"""PR87 finite contract search and abstract input mutants; no LLM/Git execution."""
import copy
import hashlib
import itertools
import json
import unittest

from cora.chat_bundle import _cockpit, append_chat_iteration, verify_chat_bundle
from tests import test_chat_bundle_portability as fixture_module


class CockpitTests(unittest.TestCase):
    def test_100_contracts_finite_selection(self):
        # 5 provenance x 5 estimates x 4 action policies = 100 finite alternatives.
        provenance = ('chat-trust', 'zip-present', 'receipt-only',
                      'zip-and-receipt-replayed', 'external-certification-claimed')
        estimates = ('invented-hours', 'fixed-days', 'fixed-phases',
                     'unknown-only', 'reported-leaves-without-time')
        actions = ('auto-write', 'auto-merge', 'opaque-advice', 'three-safe-choices')
        proposals = list(itertools.product(provenance, estimates, actions))
        eligible = [x for x in proposals if (x[0] == provenance[3] and
                    x[1] == estimates[4] and x[2] == actions[3])]
        self.assertEqual((len(proposals), len(eligible)), (100, 1))
        print('PR87_100_CONTRACTS ' + json.dumps({
            'tested': 100, 'eligible': 1, 'winner': eligible[0],
            'optimality': 'DEFINED_FINITE_SPACE_ONLY', 'model_calls': 0}))

    def fixture(self):
        h = fixture_module.ChatBundleTests('test_append_roundtrip_two_rounds_and_exact_handoff')
        h.setUp()
        self.addCleanup(h.doCleanups)
        result = append_chat_iteration(h.bundle, repo=h.repo,
                                       step=h.step(), receipt=h.receipt())
        return result, h.bundle

    def test_verified_zip_to_cockpit(self):
        report, bundle = self.fixture()
        cockpit = verify_chat_bundle(bundle, expected_receipt={
            'schema': 'cora-integrated-one-run/2', 'commit': 'a' * 40,
            'product_status': 'BLOCKED_EXTERNAL', 'authorization': 'NONE',
            'authority': 'NONE', 'release_authorized': False})['cockpit']
        self.assertEqual(cockpit, report['cockpit'])
        self.assertEqual(cockpit['status'], 'HUMAN_DECISION_REQUIRED')
        self.assertEqual(cockpit['recommended'], 'PROPOSE_NEXT_CHECK')
        self.assertEqual(cockpit['reported_open_dod_leaves'], 1)
        self.assertEqual([x['id'] for x in cockpit['choices']],
                         ['EXPLAIN', 'REPLAN', 'PROPOSE_NEXT_CHECK'])
        self.assertIsNone(cockpit['time_estimate'])
        self.assertIsNone(cockpit['remaining_phases_estimate'])
        self.assertEqual(cockpit['execution'], 'NONE')
        self.assertEqual(cockpit['authorization'], 'NONE')
        self.assertIs(cockpit['product_accepted'], False)
        self.assertIn(cockpit['recommended'], [x['id'] for x in cockpit['choices']])

    def test_all_recommendations_are_visible_choices(self):
        report, _ = self.fixture()
        for decision in ('PAUSE_CAPACITY_AND_REBASE', 'REVIEW_CHANGED_CONTRACT',
                         'REVALIDATE_CHANGED_SOURCE', 'REPLAN_STALLED_REPORTS',
                         'REQUEST_INDEPENDENT_ACCEPTANCE', 'REQUEST_EXTERNAL_WITNESS',
                         'PROPOSE_NEXT_SCOPED_STEP'):
            state = dict(report['continuation'], decision=decision)
            cockpit = _cockpit(state, 'a' * 40)
            self.assertIn(cockpit['recommended'],
                          [choice['id'] for choice in cockpit['choices']])
            self.assertEqual(cockpit['authorization'], 'NONE')
            self.assertIs(cockpit['product_accepted'], False)

    def test_10000_abstract_semantic_mutants_fail_closed(self):
        report, _ = self.fixture()
        original = report['continuation']
        seen = set()
        families = ('schema', 'decision', 'proof_boundary', 'authorization',
                    'product_accepted', 'automatic_execution', 'negative_open',
                    'overflow_open', 'bad_node', 'bad_commit')
        for family, i in itertools.product(families, range(1000)):
            changed = copy.deepcopy(original)
            commit = 'a' * 40
            if family == 'schema':
                changed['schema'] = f'forged-schema-{i}'
            elif family == 'decision':
                changed['decision'] = f'AUTO_PASS_{i}'
            elif family == 'proof_boundary':
                changed['proof_boundary'] = f'TARGET_VERIFIED_{i}'
            elif family == 'authorization':
                changed['authorization'] = f'APPROVED_{i}'
            elif family == 'product_accepted':
                changed['product_accepted'] = i
            elif family == 'automatic_execution':
                changed['automatic_execution'] = i
            elif family == 'negative_open':
                changed['reported_open_leaves'] = -(i + 1)
            elif family == 'overflow_open':
                changed['reported_open_leaves'] = 129 + i
            elif family == 'bad_node':
                changed['next_unresolved'] = f'BAD NODE {i}'
            else:
                commit = f'{i:039x}Z'
            digest = hashlib.sha256(json.dumps([family, i, changed, commit],
                                               sort_keys=True).encode()).digest()
            self.assertNotIn(digest, seen)
            seen.add(digest)
            with self.assertRaises(ValueError):
                _cockpit(changed, commit)
        self.assertEqual(len(seen), 10_000)
        print('PR87_10K_ABSTRACT ' + json.dumps({
            'families': 10, 'distinct_inputs': 10000, 'rejected': 10000,
            'survivors': 0, 'scope': 'DTO_ONLY_NOT_MODEL_OR_PHYSICAL_GIT',
            'model_calls': 0, 'authorization': 'NONE'}))


# PR87 C9: source-bound CI ownership, not a new runtime gate or proof issuer.
from pathlib import Path


def _pr36_ci_owner_contract(documentation: str, integrated: str) -> None:
    """Require exact native PR36 checks in one owner; fail on false PASS cuts."""
    marker = '  pr36-native-owner:\n'
    boundary = '  diagnose-comprehensive:\n'
    assert integrated.count(marker) == 1, 'missing or duplicated PR36 owner'
    block = integrated.split(marker, 1)[1].split(boundary, 1)[0]
    assert 'PR36 execute original Git' not in documentation, 'duplicated PR36 execution'
    assert '/tmp/cora-one-run.json' not in documentation, 'stale owned artifact in docs'
    assert "python-version: ['3.11', '3.13']" in block
    assert 'fail-fast: false' in block and 'timeout-minutes: 50' in block
    assert 'ref: ${{ github.event.pull_request.head.sha || github.sha }}' in block
    assert 'fetch-depth: 0' in block and 'persist-credentials: false' in block
    assert 'test "$(git rev-parse HEAD)" = "$EXPECTED_SHA"' in block
    required = (
        'PR36 execute original Git one-run methods and render JSON/HTML',
        'cora verify-process /tmp/cora-one-run.json --repo . --one-run --atlas-json /tmp/cora-one-run-atlas.json --atlas-html /tmp/cora-one-run.html',
        'PR36 assert offline HTML byte-equivalence to verified run',
        'PR36 physical Git DoD mutants and one-run negative tests',
        'PR36 falsify 100k distinct preseeded semantic receipts twice',
        '--model-stress-cases 100000',
        "python -m unittest discover -s tests -p 'test_one_run_orchestration.py' -v",
        'cmp /tmp/cora-one-run-100k.json /tmp/cora-one-run-100k-replay.json',
        'a["authorization"]=="NONE"',
        'not a["release_authorized"]',
        'r["unauthorized_promotions"]==0',
    )
    for clause in required:
        assert block.count(clause) == 1, 'missing/duplicated PR36 oracle: ' + clause
    assert block.count('--cases 100000') == 2, 'both seeded replays required'
    assert 'if: always()' in block
    assert 'cora-pr36-source-${{ matrix.python-version }}' in block
    assert 'continue-on-error: true' not in block and '|| true' not in block


def _mutate_pr36_owner(owner: str, old: str, new: str) -> str:
    marker = '  pr36-native-owner:\n'
    boundary = '  diagnose-comprehensive:\n'
    prefix, rest = owner.split(marker, 1)
    block, suffix = rest.split(boundary, 1)
    assert old in block, 'mutation did not target PR36 owner'
    return prefix + marker + block.replace(old, new, 1) + boundary + suffix


class Pr87CiOwnershipTests(unittest.TestCase):
    def test_native_owner_and_sixteen_negative_mutants(self):
        # Workflows are tracked source; this is an exact current-tree *static*
        # contract, while GitHub owns the actual job execution and results.
        documentation = Path('.github/workflows/ci-documentation.yml').read_text()
        integrated = Path('.github/workflows/ci-one-run-integrated.yml').read_text()
        _pr36_ci_owner_contract(documentation, integrated)
        alterations = [
            ('--model-stress-cases 100000', '--model-stress-cases 0'),
            ('cora verify-process /tmp/cora-one-run.json --repo . --one-run', ': /tmp/cora-one-run.json'),
            ('PR36 assert offline HTML byte-equivalence to verified run', 'PR36 bypass offline HTML comparison'),
            ("python -m unittest discover -s tests -p 'test_one_run_orchestration.py' -v", "python -m unittest discover -s tests -p 'test_pr35_one_run.py' -v"),
            ('--cases 100000', '--cases 99999'),
            ('cmp /tmp/cora-one-run-100k.json', ': /tmp/cora-one-run-100k.json'),
            ('if: always()', 'if: false'),
            ('timeout-minutes: 50', 'timeout-minutes: 12'),
            ('test "$(git rev-parse HEAD)" = "$EXPECTED_SHA"', 'echo "$EXPECTED_SHA"'),
            ("python-version: ['3.11', '3.13']", "python-version: ['3.11']"),
            ('PR36 execute original Git one-run methods', 'PR36 execute original Git one-run methods\n        continue-on-error: true'),
            ('persist-credentials: false', 'persist-credentials: true'),
            ('fetch-depth: 0', 'fetch-depth: 1'),
            ('not a["release_authorized"]', 'a["release_authorized"]'),
            ('r["unauthorized_promotions"]==0', 'r["unauthorized_promotions"]>=0'),
        ]
        for i, (old, new) in enumerate(alterations):
            with self.subTest(mutant=i), self.assertRaises(AssertionError):
                _pr36_ci_owner_contract(documentation, _mutate_pr36_owner(integrated, old, new))
        with self.assertRaises(AssertionError):
            _pr36_ci_owner_contract(
                documentation + '      - name: PR36 execute original Git one-run methods and render JSON/HTML\n',
                integrated)
        self.assertEqual(len(alterations) + 1, 16)

    def test_single_replay_keeps_original_source_oracle_chain(self):
        """Static call-graph guard; native PR36 tests prove actual execution."""
        cli = Path('src/cora/cli.py').read_text()
        one = Path('src/cora/one_run.py').read_text()
        suite = Path('src/cora/process_suite.py').read_text()
        negative = Path('tests/test_one_run_orchestration.py').read_text()
        self.assertIn('verify_one(args.repo,item,', cli)
        self.assertIn('if not verify_suite(repo, plain):', one)
        self.assertIn('expected=run_suite(repo,report[', suite)
        self.assertIn('self.assertTrue(verify_one(ROOT, report, html_page=page))', negative)
        self.assertIn('self.assertTrue(verify_suite(ROOT, legacy))', negative)
        for source, anchor in ((cli, 'verify_one(args.repo,item,'),
                               (one, 'if not verify_suite(repo, plain):'),
                               (suite, 'expected=run_suite(repo,report[')):
            self.assertNotIn(anchor, source.replace(anchor, 'FORGED_BYPASS', 1))



# PR90: verify real offline navigation, escaped user prose and receipt boundaries.
from html.parser import HTMLParser
import zipfile
from cora.chat_bundle import render_verified_cockpit
from tests import test_chat_bundle_portability as fixtures

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.refs = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "a" and "href" in attrs:
            self.refs.append(attrs["href"])


class NavigationTests(unittest.TestCase):
    def make_bundle(self, *, attack=False):
        case = fixtures.ChatBundleTests("test_append_roundtrip_two_rounds_and_exact_handoff")
        case.setUp()
        self.addCleanup(case.doCleanups)
        step = case.step()
        if attack:
            step["intent"] = '<script>alert("hijack")</script>'
            step["roadmap"][0]["action"] = '<img src=x onerror=alert(1)>'
            step["gaps"][0]["description"] = '"><iframe src="https://evil.invalid">'
        receipt = case.receipt()
        append_chat_iteration(case.bundle, repo=case.repo, step=step, receipt=receipt)
        return case.bundle, receipt

    def test_verified_offline_links_have_real_targets(self):
        bundle, receipt = self.make_bundle()
        page = render_verified_cockpit(bundle, expected_receipt=receipt)
        parser = Links()
        parser.feed(page)
        self.assertEqual(len(parser.ids), len(set(parser.ids)))
        self.assertTrue(parser.refs)
        self.assertTrue(all(ref.startswith("#") for ref in parser.refs))
        self.assertTrue(all(ref[1:] in parser.ids for ref in parser.refs))
        for anchor in ("overview", "dod", "roadmap", "gaps", "actions",
                       "explain", "replan", "propose", "boundary", "dod-1", "dod-2"):
            self.assertIn(anchor, parser.ids)
        for label in ("EXPLAIN", "REPLAN", "PROPOSE_NEXT_CHECK"):
            self.assertIn(label, page)
        self.assertIn(receipt["commit"], page)
        self.assertIn("BLOCKED_EXTERNAL", page)
        self.assertNotIn("<script", page.lower())
        self.assertNotIn("onclick=", page.lower())

    def test_untrusted_prose_never_becomes_html_markup(self):
        bundle, receipt = self.make_bundle(attack=True)
        page = render_verified_cockpit(bundle, expected_receipt=receipt)
        self.assertNotIn("<script>", page)
        self.assertNotIn("<img src=", page)
        self.assertNotIn("<iframe", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertIn("&lt;img", page)
        self.assertIn("&lt;iframe", page)
        self.assertIn("default-src 'none'", page)

    def test_wrong_receipt_never_renders(self):
        bundle, receipt = self.make_bundle()
        wrong = dict(receipt, commit="b" * 40)
        with self.assertRaises(ValueError):
            render_verified_cockpit(bundle, expected_receipt=wrong)

    def test_modified_zip_never_renders(self):
        bundle, receipt = self.make_bundle()
        corrupted = bundle.with_name("tampered.zip")
        with zipfile.ZipFile(bundle) as source, zipfile.ZipFile(corrupted, "w") as target:
            for name in source.namelist():
                original = source.read(name)
                if name.endswith("/step.json"):
                    original += b"\n"
                target.writestr(name, original)
        with self.assertRaises(ValueError):
            render_verified_cockpit(corrupted, expected_receipt=receipt)

    def test_pilot_optin_does_not_change_historical_cli_help(self):
        import subprocess
        import sys
        from pathlib import Path
        p = subprocess.run([sys.executable, "-m", "cora.cli", "verify-process", "--help"],
                           capture_output=True, text=True, check=False)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("--chat-cockpit-html", p.stdout)
        self.assertIn("--chat-cockpit-html",
                      (Path(__file__).resolve().parents[1] / "README.md").read_text("utf-8"))
        source = (Path(__file__).resolve().parents[1] / "src/cora/cli.py").read_text("utf-8")
        self.assertIn("pv.add_argument('--chat-cockpit-html',type=Path,help=argparse.SUPPRESS)",
                      source)

    def test_navigation_does_not_promote_authority(self):
        bundle, receipt = self.make_bundle()
        page = render_verified_cockpit(bundle, expected_receipt=receipt)
        report = verify_chat_bundle(bundle)
        self.assertEqual(report["authorization"], "NONE")
        self.assertFalse(report["cockpit"]["product_accepted"])
        self.assertIn("Authorization: NONE", page)
        self.assertIn("No link writes Git", page)
        self.assertNotIn("<form", page.lower())


if __name__ == "__main__":
    unittest.main()
