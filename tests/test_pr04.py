import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from cora.adapters import parse_manifest, adapter_audit, verify_adapter_report, kind_for_path
from cora.adapter_stress import stress_adapters, fixture, FAMILIES
from cora.evidence import domain_hash


def git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.STDOUT).decode().strip()


class AdapterOracleTests(unittest.TestCase):
    def test_24_independent_expected_fixture_labels(self):
        # Expectations are predeclared by the fixture generator, not derived from parser.
        for i, family in enumerate(FAMILIES):
            fmt,raw,expected,unknown,bad=fixture(i, 982739)
            with self.subTest(family=family):
                if bad:
                    with self.assertRaises(ValueError):parse_manifest(fmt,raw)
                else:
                    result=parse_manifest(fmt,raw)
                    self.assertEqual(set(result.dependencies), expected)
                    self.assertEqual(bool(result.unknown),unknown)
    def test_stress_deterministic_small(self):
        self.assertEqual(stress_adapters(seed=883,cases=2400),stress_adapters(seed=883,cases=2400))
        self.assertEqual(stress_adapters(seed=883,cases=2400)['distinct_input_fingerprints'],2400)
    def test_manifest_matching_is_exact(self):
        self.assertEqual(kind_for_path('other/package.json.bak')[1],'not_applicable')
        self.assertEqual(kind_for_path('.github/workflows/ci.yml')[1],'unsupported')
        self.assertEqual(kind_for_path('project.csproj')[1],'unsupported')
    def test_denies_xml_dtd(self):
        with self.assertRaises(ValueError):parse_manifest('pom.xml',b'<!DOCTYPE project [<!ENTITY secret SYSTEM "file:///etc/passwd">]><project>&secret;</project>')
    def test_malformed_does_not_convert_to_no_dependencies(self):
        with self.assertRaises(ValueError):parse_manifest('package.json',b'{bad-json')
    def test_unresolved_source_is_not_declared_runtime(self):
        result=parse_manifest('package.json',b'{"dependencies":{"a":"1"},"scripts":{"postinstall":"echo run"}}')
        self.assertEqual(result.dependencies,(('a','1','dependencies'),))
        self.assertIn('scripts:not-executed',result.unknown)
    def test_workspaces_are_not_claimed_resolved(self):
        result=parse_manifest('package.json',b'{"workspaces":["packages/*"]}')
        self.assertIn('workspaces:unresolved',result.unknown)


class GitAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.repo=Path(self.temp.name)
        git(self.repo,'init','-q');git(self.repo,'config','user.name','Fixture');git(self.repo,'config','user.email','fixture@invalid.example')
        artifacts={
            'js/package.json':'{"dependencies":{"lodash":"^4.17.21"},"scripts":{"start":"node app.js"}}',
            'py/pyproject.toml':'[project]\nname="test"\ndependencies=["requests>=2.30"]\n',
            'py/requirements.txt':'click==8.1.7\n',
            'rust/Cargo.toml':'[dependencies]\nserde="1.0"\n',
            'go/go.mod':'module example.com/app\nrequire example.com/lib v1.2.3\n',
            'java/pom.xml':'<project><dependencies><dependency><groupId>org.example</groupId><artifactId>lib</artifactId><version>1</version></dependency></dependencies></project>',
            'dotnet/app.csproj':'<Project><ItemGroup><PackageReference Include="X" Version="1" /></ItemGroup></Project>',
            '.github/workflows/ci.yml':'name: verify\n',
            'infra/Dockerfile':'FROM python:3.11\n',
        }
        for path,content in artifacts.items():
            p=self.repo/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content)
        git(self.repo,'add','.');git(self.repo,'commit','-qm','real-committed-polylanguage-fixture')
        self.head=git(self.repo,'rev-parse','HEAD')
    def tearDown(self):self.temp.cleanup()
    def test_independent_cross_ecosystem_oracle(self):
        report=adapter_audit(self.repo)
        self.assertTrue(verify_adapter_report(self.repo,report))
        dep={(o['path'],d['name'],d['constraint']) for o in report['observations'] for d in o['dependencies']}
        oracle={('js/package.json','lodash','^4.17.21'),('py/pyproject.toml','requests','requests>=2.30'),('py/requirements.txt','click','click==8.1.7'),('rust/Cargo.toml','serde','1.0'),('go/go.mod','example.com/lib','v1.2.3'),('java/pom.xml','org.example:lib','1')}
        self.assertEqual(dep,oracle)
        self.assertEqual(len(report['observations']),9)
        self.assertEqual(next(o for o in report['observations'] if o['path']=='dotnet/app.csproj')['status'],'unsupported')
        self.assertEqual(next(o for o in report['observations'] if o['path']=='.github/workflows/ci.yml')['status'],'unsupported')
        self.assertEqual(report['coverage']['runtime'],'unsupported')
    def test_dirty_worktree_does_not_affect_commit(self):
        a=adapter_audit(self.repo)
        (self.repo/'js/package.json').write_text('{"dependencies":{"tampered":"999"}}')
        self.assertEqual(a,adapter_audit(self.repo))
    def test_committed_change_changes_digest(self):
        a=adapter_audit(self.repo)
        (self.repo/'js/package.json').write_text('{"dependencies":{"newer":"999"}}')
        git(self.repo,'add','.');git(self.repo,'commit','-qm','newdeps')
        self.assertNotEqual(a['report_digest'],adapter_audit(self.repo)['report_digest'])
    def test_reforged_digest_is_rejected_against_git(self):
        a=adapter_audit(self.repo)
        obs=next(o for o in a['observations'] if o['path']=='js/package.json')
        obs['dependencies'][0]['name']='injected'
        a['report_digest']=domain_hash('CORA:adapter-report:1',{k:v for k,v in a.items() if k!='report_digest'})
        with self.assertRaises(ValueError):verify_adapter_report(self.repo,a)
    def test_unknown_malformed_manifest(self):
        p=self.repo/'js/package.json';p.write_text('{BROKEN')
        git(self.repo,'add','.');git(self.repo,'commit','-qm','bad-manifest')
        report=adapter_audit(self.repo)
        obs=next(o for o in report['observations'] if o['path']=='js/package.json')
        self.assertEqual(obs['status'],'unresolved')
        self.assertIn('manifest-parse-error',obs['unknown'])
    def test_unresolved_symlink_not_followed(self):
        (self.repo/'js'/'package.json').unlink();(self.repo/'js'/'package.json').symlink_to('/etc/passwd')
        git(self.repo,'add','-A');git(self.repo,'commit','-qm','symlink')
        obs=next(o for o in adapter_audit(self.repo)['observations'] if o['path']=='js/package.json')
        self.assertEqual(obs['status'],'unresolved')
        self.assertIn('git-object:symlink_unresolved',obs['unknown'])

if __name__=='__main__':unittest.main()
