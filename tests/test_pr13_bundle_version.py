"""Review bundle must follow canonical prerelease metadata, not a hardcoded name."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from tools.make_experimental_bundle import bundle

class BundleVersionTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name)
        self.source=self.base/'source';self.source.mkdir()
        self.dist=self.base/'dist';self.dist.mkdir()
        for rel in ('README.md','GOVERNANCE.md','docs/DOD_V1_EXPERIMENTAL.md',
            'docs/ARTIFACT_SEMANTICS.md','cora.ontology.json',
            'cora.artifact-roles.json','docs/verification/V1_EXPERIMENTAL_SATURATION.json'):
            target=self.source/rel;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text('review input\n')
        (self.source/'pyproject.toml').write_text('[project]\nname="cora-audit"\nversion="1.0.0a2"\n')
        (self.dist/'cora_audit-1.0.0a2-py3-none-any.whl').write_bytes(b'fixture wheel')
        (self.dist/'cora_audit-1.0.0a2.tar.gz').write_bytes(b'fixture sdist')
    def tearDown(self):self.temp.cleanup()
    def test_uses_current_source_version(self):
        report=bundle(self.source,self.dist,self.base/'bundle.zip')
        import zipfile
        with zipfile.ZipFile(self.base/'bundle.zip') as z:
            receipt=json.loads(z.read('MANIFEST.sha256.json'))
        self.assertEqual(report['status'],'REVIEW_ONLY_NOT_RELEASE')
        self.assertEqual(receipt['package_version'],'1.0.0a2')
        self.assertIn('dist/cora_audit-1.0.0a2.tar.gz',receipt['files'])
    def test_rejects_stale_version_artifacts(self):
        (self.dist/'cora_audit-1.0.0a2-py3-none-any.whl').rename(self.dist/'cora_audit-1.0.0a1-py3-none-any.whl')
        with self.assertRaises(ValueError):bundle(self.source,self.dist,self.base/'bundle.zip')
    def test_rejects_stable_release(self):
        (self.source/'pyproject.toml').write_text('[project]\nname="cora-audit"\nversion="1.0.0"\n')
        with self.assertRaises(ValueError):bundle(self.source,self.dist,self.base/'bundle.zip')

if __name__=='__main__':unittest.main()
