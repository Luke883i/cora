"""PR07 release candidate: real built artifact mutations, independent finite oracle."""
from __future__ import annotations
import base64
import csv
import hashlib
import io
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
from tools.release_verify import verify_release, normalized_wheel_distribution, read_sdist, supply_bom, assert_sbom, canonical_bytes, read_build_pins, sca_observation, assert_sca
from tools.release_stress import stress, classify_model, independent_oracle, FAMILIES

ROOT=Path(__file__).resolve().parents[1]
VERSION=__import__('tomllib').loads((ROOT/'pyproject.toml').read_text(encoding='utf-8'))['project']['version']


class RealArtifactMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix='cora-artifact-oracle-')
        cls.out=Path(cls.tmp.name)
        subprocess.run([sys.executable,str(ROOT/'tools/build_candidate.py'),'--source',str(ROOT),'--outdir',str(cls.out)],capture_output=True,check=True,timeout=90)
        cls.whl=next(cls.out.glob('*.whl'));cls.sdist=next(cls.out.glob('*.tar.gz'))
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_artifact_source_parity(self):
        result=verify_release(self.whl,self.sdist,ROOT)
        self.assertEqual(result['status'],'VERIFIED_SCOPED')
        self.assertEqual(result['version'],__import__('tomllib').loads((ROOT/'pyproject.toml').read_text())['project']['version'])
        self.assertEqual(result['entrypoint'],'cora=cora.cli:main')


    def test_pr55_sbom_generation_scope_and_components(self):
        bom = supply_bom(self.whl, self.sdist, ROOT)
        self.assertEqual((bom["bomFormat"], bom["specVersion"]), ("CycloneDX", "1.6"))
        self.assertEqual(bom["metadata"]["component"]["name"], "cora-audit")
        self.assertEqual(bom["metadata"]["component"]["version"], VERSION)
        self.assertEqual(bom["dependencies"][0]["dependsOn"], [])
        self.assertEqual(len(bom["components"]), 4)
        self.assertEqual(bom["compositions"][0]["aggregate"], "incomplete")

    def test_pr55_sbom_exact_original_artifact_replay(self):
        bom = supply_bom(self.whl, self.sdist, ROOT)
        with tempfile.TemporaryDirectory() as td:
            note = Path(td) / "bom.cdx.json"
            note.write_bytes(canonical_bytes(bom))
            self.assertTrue(assert_sbom(note, supply_bom(self.whl, self.sdist, ROOT)))

    def test_pr55_sbom_five_physical_negative_mutants(self):
        import copy
        bom = supply_bom(self.whl, self.sdist, ROOT)
        variants = []
        mutated = copy.deepcopy(bom)
        next(c for c in mutated["components"] if "hashes" in c)["hashes"][0]["content"] = "0" * 64
        variants.append(mutated)
        mutated = copy.deepcopy(bom)
        mutated["components"].pop()
        variants.append(mutated)
        mutated = copy.deepcopy(bom)
        mutated["metadata"]["properties"] = []
        variants.append(mutated)
        mutated = copy.deepcopy(bom)
        mutated["compositions"][0]["aggregate"] = "complete"
        variants.append(mutated)
        mutated = copy.deepcopy(bom)
        mutated["metadata"]["component"]["version"] = "9.9.9"
        variants.append(mutated)
        with tempfile.TemporaryDirectory() as td:
            note = Path(td) / "bom.cdx.json"
            for i, wrong in enumerate(variants):
                with self.subTest(i=i):
                    note.write_bytes(canonical_bytes(wrong))
                    with self.assertRaisesRegex(ValueError, "SBOM differs"):
                        assert_sbom(note, bom)

    def test_pr55_pinned_build_components_and_real_sca_report_grammar(self):
        import json
        pins = {"schema": "cora-build-tool-pins/1",
                "scope": "INSTALLED_BUILD_RUNNER_VERSIONS",
                "setuptools": "80.1.0", "wheel": "0.45.1"}
        report = {"dependencies": [
            {"name": "setuptools", "version": "80.1.0", "vulns": []},
            {"name": "wheel", "version": "0.45.1", "vulns": []}]}
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pin_path = root / "pins.json"
            raw_path = root / "scanner.json"
            summary = root / "summary.json"
            pin_path.write_text(json.dumps(pins), encoding="utf-8")
            raw_path.write_text(json.dumps(report), encoding="utf-8")
            self.assertEqual(read_build_pins(pin_path), {
                "setuptools": "80.1.0", "wheel": "0.45.1"})
            sbom = supply_bom(self.whl, self.sdist, ROOT, read_build_pins(pin_path))
            components = {x["name"]: x for x in sbom["components"]}
            self.assertEqual(components["setuptools"]["version"], "80.1.0")
            self.assertEqual(components["wheel"]["version"], "0.45.1")
            record = sca_observation(raw_path, pin_path, 0)
            self.assertEqual(record["scan_scope"], "DIRECT_INSTALLED_CI_BUILD_TOOLS_ONLY")
            self.assertEqual(record["transitive_build_dependencies"], "NOT_SCANNED")
            summary.write_bytes(canonical_bytes(record))
            self.assertTrue(assert_sca(summary, record))
            mutant = dict(report)
            mutant["dependencies"] = [dict(x) for x in report["dependencies"]]
            mutant["dependencies"][0]["version"] = "79.0.0"
            raw_path.write_text(json.dumps(mutant), encoding="utf-8")
            with self.assertRaises(ValueError):
                sca_observation(raw_path, pin_path, 0)
            raw_path.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaises(ValueError):
                sca_observation(raw_path, pin_path, 2)
            report["dependencies"][0]["vulns"] = [{"id": "PYSEC-TEST-000"}]
            raw_path.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaises(ValueError):
                sca_observation(raw_path, pin_path, 0)
            exposed = sca_observation(raw_path, pin_path, 1)
            self.assertEqual(exposed["status"], "SCANNED_FINDINGS_REVIEW_REQUIRED")
            summary.write_bytes(canonical_bytes(record))
            with self.assertRaises(ValueError):
                assert_sca(summary, exposed)

    def test_unrelated_sdist_has_no_false_identity(self):
        self.assertEqual(len(normalized_wheel_distribution(self.whl)['files']),len(list((ROOT/'src/cora').glob('*.py'))))
    def test_stress_oracle_at_edge_bits(self):
        for case in range(24):
            for mask in (0,1,3,7,15,63,255,1023,(1<<20)-1):
                got,proof=classify_model(mask,case)
                self.assertEqual(got,independent_oracle(mask,case))
                self.assertEqual(got=='CANDIDATE_SCOPED', not bool(proof))
    def test_seeded_stress_determinism_small(self):
        self.assertEqual(stress(seed=883,cases=5000),stress(seed=883,cases=5000))
        self.assertEqual(stress(seed=883,cases=5000)['mismatches'],0)
    def _edited_wheel(self, case, path):
        with zipfile.ZipFile(self.whl) as z:
            files={x.filename:z.read(x) for x in z.infolist() if not x.is_dir()}
        info=next(n for n in files if n.endswith('.dist-info/METADATA'))
        entry=info.removesuffix('METADATA')+'entry_points.txt'
        record=info.removesuffix('METADATA')+'RECORD'
        source='cora/__init__.py'
        mode=case%12
        salt=hashlib.sha256(f'PR07:{case}:883'.encode()).hexdigest()[:12]
        if mode==0:files[source]+=f'\n# tamper {salt}\n'.encode()
        elif mode==1:files[source]+=f'\n# re-signed {salt}\n'.encode()
        elif mode==2:files[info]=files[info].replace(('Version: '+VERSION).encode(),b'Version: 9.9.9')
        elif mode==3:files[entry]+=b'cora2 = cora.cli:main\n'
        elif mode==4:files['../escape.txt']=salt.encode()
        elif mode==5:files.pop(record)
        elif mode==6:files['malware_script.py']=salt.encode()
        elif mode==7:files['cora/hidden.py']=salt.encode()
        elif mode==8:files[info]+=b'Name: counterfeit\n'
        elif mode==9:files[source]=b''
        elif mode==10:files[info]=files[info].replace(b'Name: cora-audit',b'Name: wrong-release')
        elif mode==11:files[info.removesuffix('METADATA')+'WHEEL']=files[info.removesuffix('METADATA')+'WHEEL'].replace(b'py3-none-any',b'cp311-cp311-linux_x86_64')
        if mode in (1,2,3,8,10,11):
            # Re-signing integrity metadata must not hide semantic/source divergence.
            content=[]
            for line in csv.reader(io.StringIO(files[record].decode())):
                name=line[0]
                if name not in files:continue
                if name == record:content.append([name,'','']);continue
                digest=base64.urlsafe_b64encode(hashlib.sha256(files[name]).digest()).rstrip(b'=').decode()
                content.append([name,'sha256='+digest,str(len(files[name]))])
            out=io.StringIO();w=csv.writer(out,lineterminator='\n');w.writerows(content)
            files[record]=out.getvalue().encode()
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
            for name,raw in sorted(files.items()):z.writestr(name,raw)
        return path
    def _edited_sdist(self,case,path):
        with tarfile.open(self.sdist,'r:gz') as t:
            contents={m.name:(m,t.extractfile(m).read()) for m in t.getmembers() if m.isfile()}
        root=f'cora_audit-{VERSION}/'
        mode=case%12
        salt=hashlib.sha256(f'PR07:{case}:883'.encode()).hexdigest()[:12].encode()
        if mode==0:contents[root+'src/cora/graph.py']=(None,b'graph tampered '+salt)
        elif mode==1:contents.pop(root+'LICENSE')
        elif mode==2:contents[root+'setup.py']=(None,b'print("unapproved build hook")')
        elif mode==3:contents[root+'pyproject.toml']=(None,b'[project]\nname="other"\n')
        elif mode==4:contents[root+'src/cora/extra.py']=(None,b'INJECTED=True\n')
        elif mode==5:contents[root+'../escape']=(None,salt)
        elif mode==6:contents.pop(root+'src/cora/__init__.py')
        elif mode==7:contents[root+'LICENSE']=(None,b'BAD LICENSE '+salt)
        elif mode==8:contents[root+'PKG-INFO']=(None,('Name: wrong\nVersion: '+VERSION+'\nRequires-Python: >=3.11').encode())
        elif mode==9:contents[root+'pyproject.toml']=(None,b'malformed')
        elif mode==10:contents[root+'src/cora/__init__.py']=(None,b'__version__="9.9"\n')
        elif mode==11:contents[root+'README.md']=(None,b'changed no metadata update')
        with tarfile.open(path,'w:gz') as t:
            for name,(old,raw) in sorted(contents.items()):
                info=tarfile.TarInfo(name);info.size=len(raw);info.mode=0o644;t.addfile(info,io.BytesIO(raw))
            if mode==11:
                info=tarfile.TarInfo(root+'src/cora/linked.py');info.type=tarfile.SYMTYPE;info.linkname='/etc/passwd';t.addfile(info)
        return path
    def test_24_real_artifact_mutations_rejected(self):
        seen=set()
        for case in range(24):
            with self.subTest(case=case):
                out=self.out/('mutated-%02d.'%case+('whl' if case<12 else 'tar.gz'))
                if case<12:
                    self._edited_wheel(case,out)
                    wheel=out;sdist=self.sdist
                    # .whl filenames also encode identity; rename to genuine wheel filename in separate dir.
                    folder=self.out/f'mutant-wheel-{case}';folder.mkdir()
                    wheel=folder/self.whl.name;out.replace(wheel)
                else:
                    self._edited_sdist(case-12,out)
                    folder=self.out/f'mutant-sdist-{case}';folder.mkdir()
                    sdist=folder/self.sdist.name;out.replace(sdist);wheel=self.whl
                try:verify_release(wheel,sdist,ROOT)
                except ValueError:pass
                else:self.fail(f'Artifact mutant case {case} was accepted')
                digest=hashlib.sha256((wheel if case<12 else sdist).read_bytes()).hexdigest()
                self.assertNotIn(digest,seen);seen.add(digest)
        self.assertEqual(len(seen),24)
    def test_bundled_js_resource_tampering_with_valid_wheel_record_is_rejected(self):
        # Alter an installed ESM parser and recompute RECORD just like a hostile
        # repackager. Byte-level wheel/SDist/original-source parity must refute it.
        with zipfile.ZipFile(self.whl) as z:
            files = {f.filename: z.read(f) for f in z.infolist() if not f.is_dir()}
        resource = 'cora/portable_js_imports.mjs'
        self.assertIn(resource, files, 'reviewed JS resource absent from built wheel')
        files[resource] += b'\n// injected ESM parser mutation\n'
        rec = next(n for n in files if n.endswith('.dist-info/RECORD'))
        rows = []
        for name, _, _ in csv.reader(io.StringIO(files[rec].decode('utf-8'))):
            if name == rec:
                rows.append([name, '', ''])
            else:
                digest = base64.urlsafe_b64encode(
                    hashlib.sha256(files[name]).digest()).rstrip(b'=').decode()
                rows.append([name, 'sha256=' + digest, str(len(files[name]))])
        out = io.StringIO()
        csv.writer(out, lineterminator='\n').writerows(rows)
        files[rec] = out.getvalue().encode()
        folder = self.out / 'mutant-js-resource'
        folder.mkdir(exist_ok=True)
        wheel = folder / self.whl.name
        with zipfile.ZipFile(wheel, 'w', zipfile.ZIP_DEFLATED) as z:
            for name, content in sorted(files.items()):
                z.writestr(name, content)
        with self.assertRaisesRegex(ValueError, 'packaged JS resource divergence'):
            verify_release(wheel, self.sdist, ROOT)

    def test_release_source_mutation_detected(self):
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)
            (src/'src/cora').mkdir(parents=True)
            for x in (ROOT/'src/cora').glob('*.py'):
                (src/'src/cora'/x.name).write_bytes(x.read_bytes())
            for x in ('pyproject.toml','LICENSE'):(src/x).write_bytes((ROOT/x).read_bytes())
            (src/'src/cora/__init__.py').write_text('__version__="tampered"\n')
            with self.assertRaises(ValueError):verify_release(self.whl,self.sdist,src)

if __name__=='__main__':unittest.main()
