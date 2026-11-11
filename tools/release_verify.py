"""CORA PR07 release-candidate verifier: wheel/sdist and original-source parity.

Does not authenticate authorship, sign artifacts, execute unknown wheels or prove
that arbitrary build backends are safe. Both artifacts are treated as untrusted.
"""
from __future__ import annotations
import argparse
import base64
import csv
import hashlib
import io
import json
import re
import subprocess
import tarfile
import uuid
import tomllib
import zipfile
from pathlib import Path

MAX_FILE = 8 * 1024 * 1024
MAX_TOTAL = 64 * 1024 * 1024
MAX_ENTRIES = 5000
# Deliberate non-executable package resource; no generic JS/wheel payload allowance.
JS_PACKAGE_RESOURCE = 'portable_js_imports.mjs'
JS_WHEEL_PATH = 'cora/' + JS_PACKAGE_RESOURCE
JS_SDIST_PATH = 'src/cora/' + JS_PACKAGE_RESOURCE


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe(name: str) -> bool:
    return bool(name and not name.startswith('/') and '\\' not in name and '\x00' not in name and all(seg not in ('', '.', '..') for seg in name.rstrip('/').split('/')))


def read_wheel(path: Path) -> dict[str, bytes]:
    result = {}
    total = 0
    with zipfile.ZipFile(path) as z:
        items = z.infolist()
        if len(items) > MAX_ENTRIES:
            raise ValueError('too many wheel entries')
        for info in items:
            name = info.filename
            if not safe(name) or name in result:
                raise ValueError('unsafe or duplicate wheel path')
            if info.is_dir():
                continue
            unix_type = (info.external_attr >> 16) & 0o170000
            if unix_type == 0o120000:
                raise ValueError('wheel symlink disallowed')
            if info.file_size > MAX_FILE:
                raise ValueError('oversized wheel entry')
            total += info.file_size
            if total > MAX_TOTAL:
                raise ValueError('oversized wheel')
            result[name] = z.read(info)
    return result


def read_sdist(path: Path, project: str, version: str) -> dict[str, bytes]:
    result = {}
    total = 0
    root = f'{project}-{version}/'
    with tarfile.open(path, mode='r:gz') as t:
        members = t.getmembers()
        if len(members) > MAX_ENTRIES:
            raise ValueError('too many sdist entries')
        for item in members:
            name = item.name
            if not safe(name):
                raise ValueError('unsafe sdist path')
            if name == root.rstrip('/') and item.isdir():
                continue
            if not name.startswith(root):
                raise ValueError('sdist wrong root')
            if item.issym() or item.islnk() or item.isdev() or item.isfifo():
                raise ValueError('sdist link or device forbidden')
            if item.isdir():
                continue
            if not item.isfile() or item.size > MAX_FILE:
                raise ValueError('unexpected or oversized sdist entry')
            rel = name[len(root):]
            if not rel or rel in result:
                raise ValueError('duplicate sdist file')
            total += item.size
            if total > MAX_TOTAL:
                raise ValueError('oversized sdist')
            stream = t.extractfile(item)
            if stream is None:
                raise ValueError('missing sdist content')
            result[rel] = stream.read()
    return result


def get_metadata(data: bytes) -> dict[str, str]:
    # Metadata fields used here must be exact and un-folded.
    lines = data.decode('utf-8').splitlines()
    parsed = {}
    for line in lines:
        if line and not line[0].isspace() and ':' in line:
            k,v=line.split(':',1);k=k.strip()
            if k in ('Name','Version','Requires-Python') and k in parsed:
                raise ValueError('duplicate metadata identity field')
            parsed[k]=v.strip()
    return parsed


def normalized_wheel_distribution(path: Path) -> dict:
    name = path.name
    if not re.fullmatch(r'cora_audit-[0-9A-Za-z.]+-py3-none-any\.whl', name):
        raise ValueError('unexpected wheel name or platform tag')
    wheel = read_wheel(path)
    metadata = [x for x in wheel if x.endswith('.dist-info/METADATA')]
    if len(metadata) != 1:
        raise ValueError('wheel metadata not unique')
    info = metadata[0].removesuffix('METADATA')
    record = info+'RECORD'
    ep = info+'entry_points.txt'
    if record not in wheel or ep not in wheel or info+'WHEEL' not in wheel:
        raise ValueError('wheel metadata incomplete')
    if any(not (n.startswith('cora/') and n.endswith('.py') or n == JS_WHEEL_PATH or n.startswith(info)) for n in wheel):
        raise ValueError('unknown install payload')
    if b'Tag: py3-none-any' not in wheel[info+'WHEEL']:
        raise ValueError('unsupported wheel compatibility tag')
    reader = csv.reader(io.StringIO(wheel[record].decode('utf-8')))
    seen = set()
    for row in reader:
        if len(row) != 3 or row[0] in seen or row[0] not in wheel:
            raise ValueError('incomplete wheel RECORD')
        seen.add(row[0]); filename, digest, size = row
        if filename == record:
            if digest or size:
                raise ValueError('RECORD must not hash itself')
            continue
        encoded = base64.urlsafe_b64encode(hashlib.sha256(wheel[filename]).digest()).rstrip(b'=').decode('ascii')
        if digest != 'sha256='+encoded or size != str(len(wheel[filename])):
            raise ValueError('wheel RECORD mismatch')
    if seen != set(wheel):
        raise ValueError('wheel RECORD missing entries')
    entries = wheel[ep].decode('utf-8')
    if not re.search(r'^cora\s*=\s*cora\.cli:main\s*$', entries, flags=re.M) or entries.count('=') != 1:
        raise ValueError('multiple or wrong entrypoints')
    py = {n.removeprefix('cora/'): raw for n, raw in wheel.items() if n.startswith('cora/') and n.endswith('.py')}
    if not py or any(n.startswith('cora/') and not n.endswith('.py') and n != JS_WHEEL_PATH for n in wheel):
        raise ValueError('unexpected installed CORA payload')
    resources = {JS_PACKAGE_RESOURCE: wheel[JS_WHEEL_PATH]} if JS_WHEEL_PATH in wheel else {}
    return {'files': py, 'resources': resources,
            'metadata': get_metadata(wheel[metadata[0]]), 'wheel': wheel}


def verify_release(wheel_path: Path, sdist_path: Path, source: Path) -> dict:
    source = source.resolve(strict=True)
    project = tomllib.loads((source/'pyproject.toml').read_text('utf-8'))['project']
    if project['name'] != 'cora-audit' or project.get('dependencies') != []:
        raise ValueError('unexpected release name or runtime dependencies')
    version = project['version']
    if not re.fullmatch(r'(?:0\.[0-9]+\.0|1\.0\.0)a[0-9]+', version):
        raise ValueError('not an authorized CORA alpha candidate')
    if '>=3.11' != project['requires-python']:
        raise ValueError('python version contract changed')
    a = normalized_wheel_distribution(wheel_path)
    s = read_sdist(sdist_path, 'cora_audit', version)
    if 'setup.py' in s or any(p.endswith(('.sh','.exe','.so','.dll')) for p in s):
        raise ValueError('unexpected executable build input in sdist')
    if 'src/cora/__init__.py' not in s or 'pyproject.toml' not in s or 'PKG-INFO' not in s or 'LICENSE' not in s:
        raise ValueError('sdist essential sources missing')
    m = a['metadata']
    n = get_metadata(s['PKG-INFO'])
    if (m.get('Name'),m.get('Version'),m.get('Requires-Python')) != ('cora-audit',version,'>=3.11'):
        raise ValueError('wheel project metadata differs')
    if (n.get('Name'),n.get('Version'),n.get('Requires-Python')) != ('cora-audit',version,'>=3.11'):
        raise ValueError('sdist project metadata differs')
    src_files = {p.name:p.read_bytes() for p in (source/'src/cora').glob('*.py')}
    sdist_files = {p.removeprefix('src/cora/'): v for p,v in s.items() if p.startswith('src/cora/') and p.endswith('.py')}
    if not src_files or a['files'] != src_files or sdist_files != src_files:
        raise ValueError('sdist/wheel/source Python payload divergence')
    # Source, installed wheel and source distribution must carry *identical*
    # reviewed ESM parser bytes, beyond RECORD integrity (which an attacker can
    # rewrite). Do not widen this whitelist to arbitrary scripts/asset files.
    resource_path = source / JS_SDIST_PATH
    if not resource_path.is_file() or resource_path.is_symlink():
        raise ValueError('packaged JS source resource missing or symbolic link')
    resource_bytes = resource_path.read_bytes()
    expected_resource = {JS_PACKAGE_RESOURCE: resource_bytes}
    sdist_resource = {JS_PACKAGE_RESOURCE: s[JS_SDIST_PATH]} if JS_SDIST_PATH in s else {}
    if (a['resources'] != expected_resource or sdist_resource != expected_resource
            or any(p.startswith('src/cora/') and p.endswith(('.js', '.mjs'))
                   and p != JS_SDIST_PATH for p in s)
            or any(p.name.endswith(('.js', '.mjs')) and p.name != JS_PACKAGE_RESOURCE
                   for p in (source / 'src/cora').iterdir())):
        raise ValueError('sdist/wheel/source packaged JS resource divergence')
    if s['pyproject.toml'] != (source/'pyproject.toml').read_bytes():
        raise ValueError('source build contract divergence')
    if s['LICENSE'] != (source/'LICENSE').read_bytes() or not any(n.endswith('.dist-info/licenses/LICENSE') and v == s['LICENSE'] for n,v in a['wheel'].items()):
        raise ValueError('license mismatch')
    result = {'schema':'cora-release-verification/1', 'status':'VERIFIED_SCOPED',
         'distribution':'cora-audit','version':version,'wheel_sha256':sha(wheel_path.read_bytes()),
         'sdist_sha256':sha(sdist_path.read_bytes()),'wheel_files':len(a['wheel']),
         'source_modules':len(src_files),'python_payload_sha256':sha(json.dumps({n:sha(v) for n,v in sorted(src_files.items())},sort_keys=True).encode()),
         'source_modules_sha256':{n:sha(v) for n,v in sorted(src_files.items())},
         'packaged_js_resource_sha256':sha(resource_bytes),
         'entrypoint':'cora=cora.cli:main',
         'limitations':['no artifact signing or remote provenance attestation',
             'source/wheel/sdist parity does not prove runtime behavioral correctness',
             'non-Python integrations and external consumers not closed']}
    return result



def verify_review_note(path: Path, version: str, commit: str) -> bool:
    """Verify emitted PR54 review-note bytes, not just workflow source text."""
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("review note needs an exact Git revision")
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 8192:
        raise ValueError("missing, linked or oversized review note")
    raw = path.read_bytes()
    if (chr(92) * 2 + "n").encode() in raw or (chr(92) + "n").encode() in raw:
        raise ValueError("review note retains literal backslash-newline escapes")
    lines = raw.decode("utf-8").splitlines()
    if (len(lines) != 4 or lines[0] != f"CORA {version} (alpha) — REVIEW CANDIDATE ONLY"
            or lines[1] != f"Exact commit: {commit}"
            or lines[2] != "Unsigned, unpublished; not approved for release."
            or not lines[3].startswith("Required before publish: green final main CI;")
            or not lines[3].endswith("real pilot and rollback.")
            or not raw.endswith(bytes((10,)))):
        raise ValueError("review note version, commit, boundaries or line encoding drift")
    return True



# PR55: artifact SBOM is a distribution inventory, never a signed certification.
# Build dependency constraints are NOT resolved versions and remain unscanned until
# a separate scanner records actual installed build-tool pins.

def read_build_pins(path: Path) -> dict[str, str]:
    """Real installed CI tooling versions, distinct from declared minimum ranges."""
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 4096:
        raise ValueError("build tool pin record missing, linked or oversized")
    x = json.loads(path.read_text("utf-8"))
    if not isinstance(x, dict) or set(x) != {"schema", "scope", "setuptools", "wheel"} or (
            x["schema"] != "cora-build-tool-pins/1"
            or x["scope"] != "INSTALLED_BUILD_RUNNER_VERSIONS"):
        raise ValueError("invalid build pin provenance envelope")
    pins = {k: x[k] for k in ("setuptools", "wheel")}
    for name, version in pins.items():
        if not isinstance(version, str) or not re.fullmatch(
                r"[0-9]+(?:[.][0-9]+){1,3}(?:(?:a|b|rc)[0-9]+)?", version):
            raise ValueError("build tool has no exact PEP440-style version: " + name)
    if int(pins["setuptools"].split(".")[0]) < 77:
        raise ValueError("setuptools lower than declared build floor")
    v = [int(n) for n in pins["wheel"].split(".")[:2]]
    if v < [0, 45]:
        raise ValueError("wheel lower than CI build floor")
    return pins


def sca_observation(raw_report: Path, pins_path: Path, scanner_exit: int) -> dict:
    """Parse real pip-audit feed output; do not assert feed authenticity/coverage."""
    if type(scanner_exit) is not int or scanner_exit not in (0, 1):
        raise ValueError("SCA scanner failed/unavailable, never return a fabricated clean result")
    pins = read_build_pins(pins_path)
    if raw_report.is_symlink() or not raw_report.is_file() or raw_report.stat().st_size > 2 * 1024 * 1024:
        raise ValueError("SCA raw evidence unavailable or oversized")
    raw = raw_report.read_bytes()
    doc = json.loads(raw)
    if not isinstance(doc, dict) or not isinstance(doc.get("dependencies"), list):
        raise ValueError("invalid pip-audit JSON report")
    deps = doc["dependencies"]
    if len(deps) != 2 or any(not isinstance(d, dict) for d in deps):
        raise ValueError("SCA missing some direct build tools")
    counts = 0
    found = set()
    vulnerabilities = []
    for dep in deps:
        name = str(dep.get("name", "")).lower().replace("_", "-")
        if name not in pins or name in found or dep.get("version") != pins[name]:
            raise ValueError("SCA dependency does not match exact installed tool version")
        found.add(name)
        issues = dep.get("vulns")
        if not isinstance(issues, list):
            raise ValueError("SCA lacks vulnerability results for a build tool")
        for issue in issues:
            if not isinstance(issue, dict) or not isinstance(issue.get("id"), str) or not issue["id"]:
                raise ValueError("invalid vulnerability id")
            vulnerabilities.append({"package": name, "version": pins[name], "id": issue["id"]})
            counts += 1
    if found != set(pins) or (scanner_exit == 0 and counts) or (scanner_exit == 1 and not counts):
        raise ValueError("SCA status and report disagree")
    return {
        "schema": "cora-scoped-build-sca-observation/1",
        "status": ("SCANNED_FINDINGS_REVIEW_REQUIRED" if counts
                   else "SCANNED_NO_REPORTED_VULNS_IN_SCOPED_BUILD_TOOLS"),
        "scanner": "pip-audit", "scanner_version_claim": "2.10.1",
        "scanner_exit": scanner_exit,
        "scan_scope": "DIRECT_INSTALLED_CI_BUILD_TOOLS_ONLY",
        "dependency_versions": pins,
        "raw_pip_audit_sha256": sha(raw),
        "build_pins_sha256": sha(pins_path.read_bytes()),
        "vulnerabilities": sorted(vulnerabilities, key=lambda x: (x["package"], x["id"])),
        "scanner_identity": "CI_REPORTED_NOT_EXTERNALLY_AUTHENTICATED",
        "feed_freshness": "NOT_INDEPENDENTLY_ATTESTED",
        "runtime_package_scan": "NOT_APPLICABLE_NO_PUBLISHED_CORAAUDIT_PYPI_RELEASE",
        "transitive_build_dependencies": "NOT_SCANNED",
        "target_native_dependencies": "NOT_SCANNED",
        "release_authorization": "NONE",
    }


def assert_sca(path: Path, expected: dict) -> bool:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1024 * 1024:
        raise ValueError("SCA summary missing or oversized")
    if json.loads(path.read_bytes()) != expected:
        raise ValueError("SCA result, vulnerability list or input report lineage altered")
    return True


def supply_bom(wheel_path: Path, sdist_path: Path, source: Path, build_pins: dict | None = None) -> dict:
    source = Path(source).resolve(strict=True)
    checked = verify_release(wheel_path, sdist_path, source)
    data = tomllib.loads((source / "pyproject.toml").read_text("utf-8"))
    project = data["project"]
    build = data["build-system"]["requires"]
    if not isinstance(build, list) or not build or not all(
            isinstance(x, str) and re.fullmatch(r"[A-Za-z0-9_.-]+(?:[><=!~].+)?", x)
            for x in build):
        raise ValueError("unresolved or malformed build dependency declarations")
    workflow = (source / ".github/workflows/ci-release-candidate.yml").read_text("utf-8")
    if "'wheel>=0.45'" not in workflow:
        raise ValueError("candidate CI build tooling contract unknown")
    version = checked["version"]
    if build_pins is not None and set(build_pins) != {"setuptools", "wheel"}:
        raise ValueError("incomplete resolved build tool pins")
    root = "pkg:pypi/cora-audit@" + version
    artifacts = [
        ("wheel", wheel_path, checked["wheel_sha256"]),
        ("sdist", sdist_path, checked["sdist_sha256"]),
    ]
    components = []
    for kind, path, digest in artifacts:
        components.append({
            "type": "file", "name": path.name,
            "bom-ref": f"urn:cora:{kind}:sha256:{digest}",
            "hashes": [{"alg": "SHA-256", "content": digest}],
            "properties": [{"name": "cora:artifact_kind", "value": kind},
                           {"name": "cora:source_relation",
                            "value": "VERIFIED_WHEEL_SDIST_ORIGINAL_SOURCE_PARITY"}],
        })
    for item, category in [(x, "PYPROJECT_BUILD_DECLARATION") for x in build] + [
            ("wheel>=0.45", "CI_BUILD_TOOL_DECLARATION")]:
        m = re.fullmatch(r"([A-Za-z0-9_.-]+)(.*)", item)
        if m is None:
            raise ValueError("unparsed build component")
        name, constraint = m.groups()
        resolved = build_pins.get(name) if build_pins is not None else None
        purl = "pkg:pypi/" + name.lower().replace("_", "-")
        if resolved is not None:
            purl += "@" + resolved
        components.append({
            "type": "library", "name": name,
            **({"version": resolved} if resolved is not None else {}),
            "bom-ref": purl,
            "purl": purl,
            "properties": [
                {"name": "cora:phase", "value": category},
                {"name": "cora:declared_requirement", "value": item},
                {"name": "cora:resolved_version", "value": resolved or "UNKNOWN_NOT_A_PACKAGE_LOCK"}],
        })
    refs = [c["bom-ref"] for c in components]
    if len(set(refs)) != len(refs):
        raise ValueError("duplicate source or build-tool component")
    serial = uuid.uuid5(uuid.NAMESPACE_URL,
                       "cora-artifact-bom:1:" + checked["wheel_sha256"] + ":" + checked["sdist_sha256"])
    return {
        "$schema": "http://cyclonedx.org/schema/bom-1.6.schema.json",
        "bomFormat": "CycloneDX", "specVersion": "1.6",
        "serialNumber": "urn:uuid:" + str(serial), "version": 1,
        "metadata": {
            "component": {
                "type": "application", "name": "cora-audit",
                "version": version, "bom-ref": root, "purl": root,
                "licenses": [{"license": {"id": "MIT"}}],
            },
            "properties": [
                {"name": "cora:source_scope", "value": "EXACT_ARTIFACTS_AND_DECLARED_DIRECT_DEPENDENCIES"},
                {"name": "cora:runtime_dependencies_declared", "value": "ZERO"},
                {"name": "cora:build_transitive_dependencies", "value": "NOT_INVENTORIED"},
                {"name": "cora:target_native_optional_dependencies", "value": "OUT_OF_SCOPE"},
                {"name": "cora:signing", "value": "NONE"},
            ],
        },
        "components": sorted(components, key=lambda x: x["bom-ref"]),
        "dependencies": [{"ref": root, "dependsOn": []}],
        "compositions": [{"aggregate": "incomplete", "assemblies": [root]}],
    }


def canonical_bytes(value: dict) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def assert_sbom(path: Path, expected: dict) -> bool:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
        raise ValueError("missing or oversized SBOM")
    actual = json.loads(path.read_bytes())
    if actual != expected:
        raise ValueError("CycloneDX SBOM differs from original wheel/sdist/build declarations")
    return True


def build_observation(source: Path, commit: str, wheel: Path, sdist: Path, sbom: dict) -> dict:
    """Unsigned local Git and artifact observation, NOT an in-toto/SLSA attestation."""
    source = Path(source).resolve(strict=True)
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("build observation requires exact commit")
    def git(*args: str) -> bytes:
        return subprocess.check_output(["git", "-C", str(source), *args],
                                       timeout=20, stderr=subprocess.DEVNULL)
    if git("rev-parse", "HEAD").strip() != commit.encode():
        raise ValueError("source Git HEAD not at build observation revision")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("tracked build inputs modified after source checkout")
    for path in ("pyproject.toml", "LICENSE",
                 ".github/workflows/ci-release-candidate.yml"):
        if git("show", commit + ":" + path) != (source / path).read_bytes():
            raise ValueError("build material differs from original Git revision")
    report = verify_release(wheel, sdist, source)
    record = {
        "schema": "cora-unsigned-build-observation/1",
        "subject": [
            {"name": wheel.name, "sha256": report["wheel_sha256"]},
            {"name": sdist.name, "sha256": report["sdist_sha256"]}],
        "git_commit": commit,
        "git_tree": git("rev-parse", "HEAD^{tree}").decode().strip(),
        "sbom_sha256": sha(canonical_bytes(sbom)),
        "source_materials": [
            "pyproject.toml", "LICENSE", ".github/workflows/ci-release-candidate.yml"],
        "source_material_sha256": {
            path: sha(git("show", commit + ":" + path))
            for path in ("pyproject.toml", "LICENSE",
                         ".github/workflows/ci-release-candidate.yml")},
        "builder_issuer": "UNAUTHENTICATED_LOCAL_PROCESS",
        "signatures": "NONE", "slsa_attestation": "NOT_ATTESTED",
        "independent_review": "BLOCKED_EXTERNAL",
        "release_authorization": "NONE",
        "publication_authorized": False,
    }
    record["digest"] = sha(canonical_bytes(record))
    return record


def assert_build_observation(path: Path, expected: dict) -> bool:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1024 * 1024:
        raise ValueError("missing or oversized build record")
    if json.loads(path.read_bytes()) != expected:
        raise ValueError("unsigned build record, Git lineage or artifact digests altered")
    return True


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Verify CORA PR07 wheel/sdist payload and metadata')
    parser.add_argument('--wheel',type=Path,required=True)
    parser.add_argument('--sdist',type=Path,required=True)
    parser.add_argument('--source',type=Path,default=Path('.'))
    parser.add_argument('--output',type=Path)
    parser.add_argument('--sbom-output', type=Path)
    parser.add_argument('--verify-sbom', type=Path)
    parser.add_argument('--provenance-output', type=Path)
    parser.add_argument('--verify-provenance', type=Path)
    parser.add_argument('--git-commit')
    parser.add_argument('--review-note', type=Path)
    parser.add_argument('--build-pins', type=Path)
    parser.add_argument('--sca-raw', type=Path)
    parser.add_argument('--sca-exit', type=int)
    parser.add_argument('--sca-output', type=Path)
    parser.add_argument('--verify-sca', type=Path)
    args=parser.parse_args(argv)
    try:
        x=verify_release(args.wheel,args.sdist,args.source)
        pins = read_build_pins(args.build_pins) if args.build_pins else None
        if any((args.sbom_output, args.verify_sbom,
                args.provenance_output, args.verify_provenance, args.review_note)):
            bom = supply_bom(args.wheel, args.sdist, args.source, build_pins=pins)
            if args.sbom_output:
                args.sbom_output.write_bytes(canonical_bytes(bom))
            if args.verify_sbom:
                assert_sbom(args.verify_sbom, bom)
            x["supply_chain_bom"] = {
                "standard": "CycloneDX 1.6",
                "scope": "SOURCE_ARTIFACT_DECLARED_DIRECT_PARTIAL",
                "sha256": sha(canonical_bytes(bom)),
                "build_transitives": "NOT_INVENTORIED",
            }
            if args.provenance_output or args.verify_provenance:
                if not args.git_commit:
                    raise ValueError("provenance needs exact Git SHA")
                record = build_observation(args.source, args.git_commit,
                                           args.wheel, args.sdist, bom)
                if args.provenance_output:
                    args.provenance_output.write_bytes(canonical_bytes(record))
                if args.verify_provenance:
                    assert_build_observation(args.verify_provenance, record)
                x["build_observation"] = {
                    "digest": record["digest"], "signature": "NONE",
                    "slsa": "NOT_ATTESTED", "authority": "NONE"}
            if args.review_note:
                if not args.git_commit:
                    raise ValueError("review note needs exact Git SHA")
                verify_review_note(args.review_note, x["version"], args.git_commit)
        if any((args.sca_raw, args.sca_output, args.verify_sca)):
            if not args.sca_raw or not args.build_pins or args.sca_exit is None:
                raise ValueError("SCA must have raw scanner report, installed pins and exit")
            scan = sca_observation(args.sca_raw, args.build_pins, args.sca_exit)
            if args.sca_output:
                args.sca_output.write_bytes(canonical_bytes(scan))
            if args.verify_sca:
                assert_sca(args.verify_sca, scan)
            x["sca"] = {"status": scan["status"], "scope": scan["scan_scope"],
                        "report_digest": sha(canonical_bytes(scan)),
                        "external_authorization": "NONE"}
    except (ValueError,OSError,KeyError,tarfile.TarError,zipfile.BadZipFile) as e:
        parser.exit(2, f'RELEASE FAIL: {e}\n')
    result=json.dumps(x,sort_keys=True,indent=2)+'\n'
    if args.output:args.output.write_text(result)
    else:print(result,end='')
    return 0

if __name__=='__main__':raise SystemExit(main())
