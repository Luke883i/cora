"""P2 source-only hypergraph: original Git, typed consumers, nonpromotion, replay."""
import copy
import subprocess
import tempfile
import unittest
from pathlib import Path

from cora.graph import unified_consumer_hypergraph, verify_unified_consumer_hypergraph
from cora.evidence import domain_hash


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args],
                                   stderr=subprocess.PIPE).decode().strip()


class UnifiedHypergraphTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.repo = Path(self.folder.name)
        git(self.repo, 'init', '-q')
        git(self.repo, 'config', 'user.name', 'P2 fixture')
        git(self.repo, 'config', 'user.email', 'p2@example.invalid')
        files = {
            'src/pkg/__init__.py': '',
            'src/pkg/lib.py': 'VALUE = 7\n',
            'src/pkg/dynamic.py': 'import importlib\nimportlib.import_module("pkg.lib")\n',
            'tests/test_consumer.py': 'import pkg.lib\n',
            'generated/client.py': 'import pkg.lib\n',
            '.github/workflows/base.yml': 'on: [workflow_call]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo ok\n',
            '.github/workflows/call.yml': 'on: [push]\njobs:\n  call:\n    uses: ./.github/workflows/base.yml\n',
            'docs/evidence.md': 'ref: .github/workflows/base.yml\n',
            'src/client.mjs': 'import "./uncompiled.mjs";\n',
        }
        for name, content in files.items():
            file = self.repo / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(content)
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'original Git target')
        self.sha = git(self.repo, 'rev-parse', 'HEAD')

    def report(self):
        return unified_consumer_hypergraph(self.repo, self.sha)

    def test_global_and_intermediate_dods_with_explicit_unknown(self):
        r = self.report()
        self.assertEqual(r['schema'], 'cora-unified-consumer-hypergraph/1')
        self.assertEqual(r['file_count'], 9)
        self.assertEqual(r['global_status'], 'BLOCKED_EXTERNAL')
        self.assertEqual(r['and_assessment']['states']['P2_G4'], 'BLOCKED_EXTERNAL')
        self.assertEqual(r['and_assessment']['states']['P2_G0'], 'BLOCKED_EXTERNAL')
        self.assertEqual(len(r['and_assessment']['ordered_cut']), 17)
        self.assertFalse(r['safe_deletion_proven'])
        self.assertEqual(r['authority'], 'NONE')
        self.assertTrue(verify_unified_consumer_hypergraph(self.repo, r))

    def test_typed_test_generated_workflow_and_unknown_consumer(self):
        r = self.report()
        rows = {(x['consumer'], x['dependency'], x['kind']) for x in r['edges']}
        self.assertIn(('file:tests/test_consumer.py', 'file:src/pkg/lib.py',
                       'TEST_STATIC_IMPORT_CANDIDATE'), rows)
        self.assertIn(('file:generated/client.py', 'file:src/pkg/lib.py',
                       'GENERATED_STATIC_IMPORT_CANDIDATE'), rows)
        self.assertIn(('file:.github/workflows/call.yml',
                       'file:.github/workflows/base.yml',
                       'WORKFLOW_REUSABLE_CALL_CANDIDATE'), rows)
        self.assertIn('generated/client.py', r['generated_path_candidates'])
        unknown = {(x['path'], x['kind']) for x in r['unknowns']}
        self.assertIn(('src/pkg/dynamic.py', 'DYNAMIC_PYTHON_IMPORT_UNKNOWN'), unknown)
        self.assertIn(('src/client.mjs', 'NON_PYTHON_CONSUMERS_REQUIRE_ORIGINAL_PARSER'), unknown)
        group = next(x for x in r['hyperedges'] if x['dependency'] == 'file:src/pkg/lib.py')
        self.assertEqual(group['operator'], 'AND')
        self.assertEqual(group['external_consumer_closure'], 'UNKNOWN_NOT_ABSENT')
        self.assertFalse(group['safe_to_delete'])

    def test_original_opt_in_js_parser_edges_and_unknowns(self):
        # Use the previously installed Node ESM parser; do not evaluate JS.
        source = self.repo / 'src/client.mjs'
        source.write_text('import "./exact.mjs"; import("./dynamic.mjs");\n')
        (self.repo / 'src/exact.mjs').write_text('export const safe = true;\n')
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'committed ESM source and dynamic import')
        sha = git(self.repo, 'rev-parse', 'HEAD')
        js = unified_consumer_hypergraph(self.repo, sha, parse_js=True)
        self.assertIn(('file:src/client.mjs', 'file:src/exact.mjs',
                       'STATIC_ESM_IMPORT_CANDIDATE'),
                      {(e['consumer'], e['dependency'], e['kind']) for e in js['edges']})
        self.assertIn(('src/client.mjs', 'ESM_DYNAMIC_IMPORT_CANDIDATE'),
                      {(u['path'], u['kind']) for u in js['unknowns']})
        self.assertEqual(js['global_status'], 'BLOCKED_EXTERNAL')
        self.assertTrue(verify_unified_consumer_hypergraph(self.repo, js, parse_js=True))
        with self.assertRaisesRegex(ValueError, 'differs'):
            verify_unified_consumer_hypergraph(self.repo, js, parse_js=False)
        self.assertFalse((self.repo / 'src/dynamic.mjs').exists())
        import json
        from cora.portable_assurance import run_portable, verify_portable
        with tempfile.TemporaryDirectory() as external:
            profile = Path(external) / 'target.json'
            profile.write_text(json.dumps({
                "schema":"cora-portable-target/1", "target_repo":"Fixture/javascript",
                "revision":sha,
                "owners":[{"id":"js-owner", "path":"src/client.mjs"}],
                "witnesses":[], "method_links":[]
            }))
            receipt = run_portable(self.repo, sha, profile,
                                   parse_js=True, include_consumers=True)
            self.assertEqual(receipt['consumer_hypergraph']['graph_digest'],
                             js['graph_digest'])
            self.assertEqual(receipt['governed_status'], 'BLOCKED_EXTERNAL')
            self.assertTrue(verify_portable(self.repo, receipt, profile,
                                            parse_js=True, include_consumers=True))
            with self.assertRaisesRegex(ValueError, 'replay mismatch'):
                verify_portable(self.repo, receipt, profile,
                                parse_js=False, include_consumers=True)

    def test_readback_not_dirty_worktree_and_physical_import_mutation(self):
        original = self.report()
        p = self.repo / 'tests/test_consumer.py'
        p.write_text('import forged.dirty_worktree\n')
        self.assertEqual(self.report(), original)
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'physical import change')
        candidate = unified_consumer_hypergraph(self.repo, 'HEAD')
        self.assertNotEqual(candidate['graph_digest'], original['graph_digest'])
        self.assertNotEqual(candidate['commit'], original['commit'])
        self.assertFalse(any(x['consumer']=='file:tests/test_consumer.py'
                             and x['dependency']=='file:src/pkg/lib.py' for x in candidate['edges']))
        self.assertTrue(verify_unified_consumer_hypergraph(self.repo, original))
        with self.assertRaisesRegex(ValueError, 'integrity mismatch|differs'):
            forged = copy.deepcopy(original)
            forged['commit'] = candidate['commit']
            verify_unified_consumer_hypergraph(self.repo, forged)

    def test_source_report_tampering_and_authority(self):
        r = self.report()
        changes = [
            ('global_status', 'MODEL_ELIGIBLE_UNATTESTED'),
            ('authority', 'RELEASE_MANAGER'),
            ('safe_deletion_proven', True),
            ('graph_digest', 'f' * 64),
        ]
        for name, value in changes:
            mutated = copy.deepcopy(r)
            mutated[name] = value
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'integrity mismatch'):
                verify_unified_consumer_hypergraph(self.repo, mutated)
        mutated = copy.deepcopy(r)
        mutated['edges'].pop()
        with self.assertRaisesRegex(ValueError, 'integrity mismatch|differs'):
            verify_unified_consumer_hypergraph(self.repo, mutated)
        mutated = copy.deepcopy(r)
        mutated['unknowns'] = []
        with self.assertRaisesRegex(ValueError, 'integrity mismatch|differs'):
            verify_unified_consumer_hypergraph(self.repo, mutated)

    def test_portable_one_run_opt_in_reuses_graph_and_replays(self):
        import json
        from cora.portable_assurance import run_portable, verify_portable
        profile = {"schema": "cora-portable-target/1", "target_repo": "Fixture/target",
                   "revision": self.sha,
                   "owners": [{"id": "original-owner", "path": "src/pkg/lib.py"}],
                   "witnesses": [], "method_links": []}
        with tempfile.TemporaryDirectory() as outside:
            path = Path(outside) / 'profile.json'
            path.write_text(json.dumps(profile))
            report = run_portable(self.repo, self.sha, path, include_consumers=True)
            self.assertEqual(report['source_status'], 'SOURCE_PARTIAL_NOT_CONFIGURED')
            self.assertEqual(report['consumer_hypergraph']['graph_digest'],
                             self.report()['graph_digest'])
            self.assertEqual(report['consumer_hypergraph']['global_status'],
                             'BLOCKED_EXTERNAL')
            self.assertEqual(report['authorization'], 'NONE')
            self.assertTrue(verify_portable(self.repo, report, path, include_consumers=True))
            with self.assertRaisesRegex(ValueError, 'replay mismatch'):
                verify_portable(self.repo, report, path, include_consumers=False)
            forged = copy.deepcopy(report)
            forged['consumer_hypergraph']['global_status'] = 'PASS'
            with self.assertRaisesRegex(ValueError, 'replay mismatch'):
                verify_portable(self.repo, forged, path, include_consumers=True)
            self.assertFalse((self.repo / 'cora.ontology.json').exists())
            self.assertFalse((self.repo / 'cora.artifact-roles.json').exists())

    def test_10k_finite_receipt_faults_and_rehashed_forgery(self):
        # 10,000 bounded receipt-model faults, NOT 10,000 physical source edits.
        r = self.report()
        for i in range(10000):
            bad = copy.deepcopy(r)
            family = i % 10
            if family == 0:
                bad['authority'] = 'FORGED_%05d' % i
            elif family == 1:
                bad['global_status'] = 'MODEL_ELIGIBLE_%05d' % i
            elif family == 2:
                bad['safe_deletion_proven'] = True
            elif family == 3:
                bad['file_count'] += i + 1
            elif family == 4:
                bad['unknowns'] = []
            elif family == 5:
                bad['generated_path_candidates'] = ['fake_%d.py' % i]
            elif family == 6:
                bad['edges'] = []
            elif family == 7:
                bad['hyperedges'] = []
            elif family == 8:
                bad['coverage']['external'] = 'PASS_%05d' % i
            else:
                bad['and_assessment']['authorization'] = 'SELF_APPROVED_%05d' % i
            with self.assertRaisesRegex(ValueError, 'integrity mismatch'):
                verify_unified_consumer_hypergraph(self.repo, bad)
        # An adversary can rehash a local JSON report, not rewrite original Git.
        bad = copy.deepcopy(r)
        bad['authority'] = 'RELEASE_APPROVED'
        bad['graph_digest'] = domain_hash('CORA:unified-consumer-hypergraph:1',
                                          {k:v for k,v in bad.items() if k!='graph_digest'})
        with self.assertRaisesRegex(ValueError, 'differs'):
            verify_unified_consumer_hypergraph(self.repo, bad)
        self.assertEqual(self.report(), r)


class OriginalCoraSourceSelfApplication(unittest.TestCase):
    def test_original_git_checkout_consumer_projection_and_replay(self):
        # CI must use a real Git checkout; no ZIP comment substitutes for HEAD.
        root = Path(__file__).resolve().parents[1]
        self.assertTrue((root / '.git').exists(), 'exact original Git checkout required')
        head = git(root, 'rev-parse', 'HEAD')
        result = unified_consumer_hypergraph(root, head)
        self.assertEqual(result['commit'], head)
        self.assertGreaterEqual(result['file_count'], 300)
        self.assertEqual(result['global_status'], 'BLOCKED_EXTERNAL')
        self.assertEqual(result['and_assessment']['states']['L_EXTERNAL_CONSUMERS'],
                         'BLOCKED_EXTERNAL')
        self.assertFalse(result['safe_deletion_proven'])
        self.assertGreater(len(result['edges']), 0)
        self.assertTrue(verify_unified_consumer_hypergraph(root, result))


if __name__ == '__main__':
    unittest.main()
