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
import tarfile
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


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Verify CORA PR07 wheel/sdist payload and metadata')
    parser.add_argument('--wheel',type=Path,required=True)
    parser.add_argument('--sdist',type=Path,required=True)
    parser.add_argument('--source',type=Path,default=Path('.'))
    parser.add_argument('--output',type=Path)
    args=parser.parse_args(argv)
    try:
        x=verify_release(args.wheel,args.sdist,args.source)
    except (ValueError,OSError,KeyError,tarfile.TarError,zipfile.BadZipFile) as e:
        parser.exit(2, f'RELEASE FAIL: {e}\n')
    result=json.dumps(x,sort_keys=True,indent=2)+'\n'
    if args.output:args.output.write_text(result)
    else:print(result,end='')
    return 0

if __name__=='__main__':raise SystemExit(main())
