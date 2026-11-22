"""Independent committed-Git debt sources, adverse SARIF and safe process tests."""
from __future__ import annotations
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from cora.debt import debt_scan, verify_debt, compare_debt, parse_sarif
from cora.process_suite import run_suite, verify_suite, process_catalog
from cora.debt_stress import stress_debt, model_triage, oracle_spec
from cora.evidence import domain_hash
from cora.cli import main


def g(root,*args):
    return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.STDOUT).decode().strip()


class GitDebtFixture(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        g(self.root,'init','-q');g(self.root,'config','user.email','fixture@invalid.example')
        g(self.root,'config','user.name','Independent Fixture')
        for p in ('src/a','src/b','docs'):(self.root/p).mkdir(parents=True)
        (self.root/'src/a/main.py').write_text('from . import massive\n')
        (self.root/'src/a/massive.py').write_text(self.heavy(1))
        (self.root/'src/b/worker.py').write_text('pass\n')
        (self.root/'docs/contract.md').write_text('Business contract must remain available.\n')
        (self.root/'cora.ontology.json').write_text(json.dumps({'schema':'cora-ontology/1','products':[
          {'id':'a','roots':['src/a'],'entrypoints':['src/a/main.py']},
          {'id':'b','roots':['src/b'],'entrypoints':['src/b/worker.py']}],
          'software':[{'id':'engine','roots':['src/a'],'product_ids':['a']}]}))
        (self.root/'cora.artifact-roles.json').write_text(json.dumps({'schema':'cora-artifact-roles/1','rules':[
          {'pattern':'src/a/main.py','roles':['ENTRYPOINT','SOFTWARE_SOURCE'],'rationale':'Explicit committed application entrypoint.'},
          {'pattern':'src/b/worker.py','roles':['SOFTWARE_SOURCE'],'rationale':'Explicit second product implementation.'},
          {'pattern':'docs/*','roles':['PRODUCT_CONTRACT'],'rationale':'Important normative product specifications.'}]}))
        g(self.root,'add','.');g(self.root,'commit','-qm','feat: fixture baseline')
        self.base=g(self.root,'rev-parse','HEAD')
        for i in range(2,8):
            (self.root/'src/a/massive.py').write_text(self.heavy(i))
            g(self.root,'add','.');g(self.root,'commit','-qm',f'feat: exercise hotspot {i}')
        self.head=g(self.root,'rev-parse','HEAD')
    @staticmethod
    def heavy(counter):
        return 'def f(n):\n'+''.join('    if n == %d: return %d\n'%(n,n) for n in range(24))+f'    return {counter}\n'
    def tearDown(self):self.tmp.cleanup()
    def sarif(self,uri='src/a/massive.py',level='error'):
        return json.dumps({'version':'2.1.0','runs':[{'tool':{'driver':{'name':'CheckTool'}},'results':[
          {'ruleId':'security/CWE-79','level':level,'message':{'text':'Claim, not verified'},
           'locations':[{'physicalLocation':{'artifactLocation':{'uri':uri},'region':{'startLine':4}}}]}]}]}).encode()

    def test_structural_signal_with_source_proof(self):
        r=debt_scan(self.root,max_commits=16)
        self.assertTrue(any(f['kind']=='CODE_COMPLEXITY' and f['path']=='src/a/massive.py' for f in r['findings']))
        self.assertTrue(any(f['kind']=='CHANGE_PRESSURE' for f in r['findings']))
        self.assertTrue(verify_debt(self.root,r))
    def test_role_missing_is_coverage_not_dead_code(self):
        r=debt_scan(self.root,max_commits=16)
        hits=[f for f in r['findings'] if f['path']=='src/a/massive.py' and f['kind']=='EVIDENCE_COVERAGE']
        self.assertTrue(hits)
        self.assertTrue(all(f['authorized_action']=='NONE' for f in r['findings']))
    def test_dirty_tree_does_not_affect_pinned_report(self):
        r=debt_scan(self.root,max_commits=8)
        (self.root/'src/a/massive.py').write_text('raise RuntimeError("should not run")\n')
        self.assertEqual(r,debt_scan(self.root,max_commits=8))
    def test_reforged_self_digest_rejected(self):
        r=debt_scan(self.root,max_commits=4)
        r['findings'][0]['authorized_action']='DELETE'
        r['report_digest']=domain_hash('CORA:debt-ledger:1',{k:v for k,v in r.items() if k!='report_digest'})
        with self.assertRaises(ValueError): verify_debt(self.root,r)
    def test_external_sarif_never_authorizes(self):
        raw=self.sarif()
        r=debt_scan(self.root,max_commits=5,sarif_bytes=raw)
        found=[x for x in r['findings'] if x['evidence_strength']=='EXTERNAL_UNVERIFIED']
        self.assertEqual(len(found),1)
        self.assertEqual(found[0]['kind'],'SECURITY_FINDING')
        self.assertEqual(found[0]['authorized_action'],'NONE')
        self.assertTrue(verify_debt(self.root,r,sarif_bytes=raw))
    def test_sarif_missing_replay_rejected(self):
        r=debt_scan(self.root,max_commits=3,sarif_bytes=self.sarif())
        with self.assertRaises(ValueError):verify_debt(self.root,r)
    def test_sarif_foreign_input_rejected(self):
        r=debt_scan(self.root,max_commits=3,sarif_bytes=self.sarif())
        with self.assertRaises(ValueError):verify_debt(self.root,r,sarif_bytes=self.sarif(level='note'))
    def test_malformed_sarif_objects_fail_closed(self):
        raw=self.sarif()
        doc=json.loads(raw)
        examples=[]
        v=json.loads(raw);v['runs'][0]['tool']=[];examples.append(v)
        v=json.loads(raw);v['runs'][0]['results'][0]['message']=[];examples.append(v)
        v=json.loads(raw);v['runs'][0]['results'][0]['locations'][0]['physicalLocation']['region']=[];examples.append(v)
        for instance in examples:
            with self.subTest(instance=instance['runs'][0]),self.assertRaises(ValueError):
                parse_sarif(json.dumps(instance).encode(),{'src/a/massive.py'})
    def test_full_process_reuses_same_commit_evidence(self):
        suite=run_suite(self.root,process='full',max_commits=3,focus='src/a/main.py')
        reused=[r for r in suite['results'] if r['status']=='REUSED_SCOPED_FROM_HOLISTIC']
        self.assertGreaterEqual(len(reused),4)
        self.assertTrue(verify_suite(self.root,suite))

    def test_sarif_path_escape_rejected(self):
        for p in ('../etc/passwd','/tmp/secret.py','https://bad.invalid/x.py','src/%2e%2e/x.py'):
            with self.subTest(p=p),self.assertRaises(ValueError):parse_sarif(self.sarif(uri=p),{'src/a/massive.py'})
    def test_unknown_sarif_path_visible(self):
        r=parse_sarif(self.sarif(uri='src/a/not-tracked.py'),{'src/a/massive.py'})
        self.assertEqual(r['rows'],[])
        self.assertIn('SARIF_PATH_NOT_IN_COMMIT:src/a/not-tracked.py',r['unknown'])
    def test_diff_is_detection_not_resolution_proof(self):
        r=compare_debt(self.root,self.base,self.head,max_commits=4)
        self.assertEqual(r['resolution_claim'],'NOT_PROVEN_ONLY_DETECTION_DELTA')
        self.assertEqual(r['authorized_action'],'NONE')
    def test_process_names_and_safe_exclusions(self):
        cat=process_catalog()
        self.assertEqual(len(cat['processes']),7)
        self.assertIn('target_test_execution',cat['excluded_unsafe_methods'])
    def test_independent_single_source_process(self):
        r=run_suite(self.root,process='source',max_commits=4)
        self.assertEqual(r['status'],'PASS_SCOPED_WITH_UNVERIFIED_GAPS')
        self.assertTrue(verify_suite(self.root,r))
        self.assertNotIn('debt_signals',[x['method'] for x in r['results']])
    def test_all_in_one_no_execution(self):
        r=run_suite(self.root,process='full',max_commits=3,focus='src/a/main.py')
        self.assertIn(r['status'],('PASS_SCOPED_WITH_UNVERIFIED_GAPS','DEBT_BLOCKED'))
        self.assertEqual(r['authorized_action'],'NONE')
        self.assertIn('debt_signals',[x['method'] for x in r['results']])
        self.assertNotIn('target_test_execution',[x['method'] for x in r['results']])
        self.assertTrue(verify_suite(self.root,r))
    def test_fake_process_status_fails_replay(self):
        r=run_suite(self.root,process='history',max_commits=3)
        r['results'][0]['status']='FABRICATED_PASS'
        r['run_digest']=domain_hash('CORA:process-run:1',{k:v for k,v in r.items() if k!='run_digest'})
        with self.assertRaises(ValueError):verify_suite(self.root,r)
    def test_cli_debt_full_and_verify(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'report.json'
            self.assertEqual(main(['debt-scan',str(self.root),'--max-commits','3','--output',str(out)]),0)
            self.assertEqual(main(['verify-debt',str(out),'--repo',str(self.root)]),0)
    def test_cli_suite_and_verify(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'run.json'
            self.assertEqual(main(['process-run',str(self.root),'--process','history','--max-commits','3','--output',str(out)]),0)
            self.assertEqual(main(['verify-process',str(out),'--repo',str(self.root)]),0)
    def test_code_file_not_run_during_scanning(self):
        (self.root/'src/a/main.py').write_text('raise RuntimeError("never execute me")\n')
        g(self.root,'add','.');g(self.root,'commit','-qm','adversarial code')
        self.assertEqual(debt_scan(self.root,max_commits=3)['commit'],g(self.root,'rev-parse','HEAD'))


class ModelFalsification(unittest.TestCase):
    def test_4096_oracle_cases(self):
        for family in range(24):
            for bits in range(4096):
                self.assertEqual(model_triage(bits,family),oracle_spec(bits,family))
    def test_reproducible_4096(self):
        a=stress_debt(seed=883,cases=4096)
        self.assertEqual(a,stress_debt(seed=883,cases=4096))
        self.assertEqual((a['cases'],a['distinct_input_masks'],a['mismatches']),(4096,4096,0))
    def test_invalid_case_counts(self):
        with self.assertRaises(ValueError):stress_debt(cases=1_000_001)


class ExternalToolOptimalContract(unittest.TestCase):
    """Contract tests: discovery is not execution or an approval boundary."""
    def test_all_candidates_are_unexecuted_and_owned_upstream(self):
        c = process_catalog(intent='')
        self.assertEqual(len(c['processes']), 7)
        self.assertNotIn('external_tools', process_catalog())
        self.assertEqual(len(c['external_tools']), 10)
        self.assertEqual(c['authorized_action'], 'NONE')
        self.assertEqual(c['inference'], [])
        self.assertTrue(all(t['owner'] == 'UPSTREAM_EXTERNAL' and
                            t['approval'] == 'NONE' and t['installation'] == 'NOT_CHECKED' and
                            t['execution'].startswith('NOT_RUN') for t in c['external_tools']))

    def test_intent_inference_is_bounded_deterministic_and_not_execution(self):
        i = 'Please do a security scan and produce SARIF'
        a = process_catalog(intent=i)
        self.assertEqual(a, process_catalog(intent=i))
        self.assertEqual(a['inference'][0]['id'], 'semgrep')
        self.assertNotIn('explicit_version_probe', a)
        self.assertEqual(process_catalog(intent='some unrelated sentence')['inference'], [])
        with self.assertRaises(ValueError): process_catalog(intent='a' * 1025)
        with self.assertRaises(ValueError): process_catalog(intent=123)

    def test_probe_needs_exact_opt_in_and_closed_identity(self):
        with self.assertRaises(ValueError): process_catalog(probe_tool='semgrep')
        with self.assertRaises(ValueError): process_catalog(authorize_probe=True)
        with self.assertRaises(ValueError): process_catalog(probe_tool='bash', authorize_probe=True)
        with self.assertRaises(ValueError): process_catalog(probe_tool='../semgrep', authorize_probe=True)
        with self.assertRaises(ValueError): process_catalog(probe_tool='semgrep;id', authorize_probe=True)

    def test_probe_no_binary_does_not_execute_or_promote(self):
        from unittest.mock import patch
        with patch('cora.process_suite.shutil.which', return_value=None):
            r = process_catalog(probe_tool='semgrep', authorize_probe=True)
        self.assertEqual(r['explicit_version_probe']['status'], 'NOT_INSTALLED')
        self.assertEqual(r['explicit_version_probe']['target_execution'], 'NOT_RUN')
        r = process_catalog(probe_tool='hypothesis', authorize_probe=True)
        self.assertEqual(r['explicit_version_probe']['status'], 'NO_SAFE_STANDALONE_PROBE')

    def test_probed_executable_uses_bounded_upstream_runner(self):
        from unittest.mock import patch
        from types import ModuleType
        import subprocess as sp
        import sys
        fake = ModuleType('cora.process_bounds')
        called = []
        def bounded(argv, **kw):
            called.append((argv, kw))
            return sp.CompletedProcess(argv, 0, b'0.9.1\n', None)
        fake.run_bounded = bounded
        with patch('cora.process_suite.shutil.which', return_value='/tmp/fake-semgrep'), \
             patch.dict(sys.modules, {'cora.process_bounds': fake}):
            r = process_catalog(probe_tool='semgrep', authorize_probe=True)
        self.assertEqual(r['explicit_version_probe']['status'], 'VERSION_PROBE_EXECUTED_UNTRUSTED')
        self.assertEqual(r['explicit_version_probe']['target_execution'], 'NOT_RUN')
        self.assertEqual(called[0][0], ['/tmp/fake-semgrep', '--version'])
        self.assertLessEqual(called[0][1]['max_output'], 8192)

    def test_cli_inference_and_deny_probe_no_side_effects(self):
        from contextlib import redirect_stdout
        from io import StringIO
        out=StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(['process-list','--intent','signature verification']), 0)
        parsed=json.loads(out.getvalue())
        self.assertEqual(parsed['inference'][0]['id'], 'cosign')
        self.assertNotIn('explicit_version_probe', parsed)
        with redirect_stdout(StringIO()):
            self.assertNotEqual(main(['process-list','--probe-tool','cosign']), 0)

    def test_optimal_contract_and_falsifier_presence(self):
        r = Path(__file__).resolve().parents[1]
        doc=json.loads((r/'.cora/contracts/dod/optimal-tool-acquisition.json').read_text())
        self.assertEqual(doc['authority'], 'NONE')
        nodes={x['id']: x for x in doc['nodes']}
        self.assertEqual(nodes['G_TOOLS_ACCEPTED']['depends_on'],
                         ['I_PRODUCT','I_SOFTWARE','I_REPOSITORY','E_EXTERNAL'])
        self.assertEqual(nodes['E_EXTERNAL']['status'], 'BLOCKED_EXTERNAL')
        self.assertEqual(nodes['G_TOOLS_ACCEPTED']['status'], 'BLOCKED_EXTERNAL')
        self.assertEqual(doc['global_status'], 'NOT_ACCEPTED')
        self.assertTrue(all(nodes[k]['status'] == 'NOT_ACCEPTED'
                            for k in ('I_PRODUCT','I_SOFTWARE','I_REPOSITORY')))
        self.assertEqual(set(nodes), {'G_TOOLS_ACCEPTED','I_PRODUCT','I_SOFTWARE',
                         'I_REPOSITORY','E_EXTERNAL','L_DISCOVER','L_INFER',
                         'L_PROBE','L_NO_AUTHORITY','L_PACKAGING','L_CI'})
        self.assertTrue(all(x.get('falsifier') for x in doc['nodes'] if x['id'].startswith('L_')))
        self.assertEqual(doc['global_status'], 'NOT_ACCEPTED')

if __name__=='__main__':unittest.main()



class OperationalCapabilityTests(unittest.TestCase):
    """Actual disposable target Git/tests; mocked scanner envelopes are separate from the real CE pilot."""

    def setUp(self):
        import tempfile
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.repo = self.home / "target"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        (self.repo / "tests").mkdir()
        (self.repo / "calc.py").write_text("def double(x):\n    return x * 2\ndef parse(s):\n    return eval(s)\n")
        (self.repo / "tests/test_calc.py").write_text(
            "import unittest\nfrom calc import double\nclass CalcTests(unittest.TestCase):\n"
            "    def test_double(self):\n        self.assertEqual(double(3), 6)\n")
        self.commit()

    def git(self, *args):
        import subprocess
        return subprocess.check_output(["git", "-C", str(self.repo), *args], stderr=subprocess.PIPE).decode().strip()

    def commit(self):
        from cora.process_suite import run_suite, universal_capability_plan
        self.git("add", "-A")
        self.git("commit", "-qm", "fixture source")
        sha = self.git("rev-parse", "HEAD")
        native = json.loads((Path(__file__).resolve().parents[1] / ".cora/assurance/capability-atlas.json").read_text())["commands"]
        process = run_suite(self.repo, sha, process="history")
        self.base = {"commit": sha, "source_process": process,
                     "universal_capability_plan": universal_capability_plan(
                         native, commit=sha, source_methods=process["results"], source_process="history")}
        self.request = {"schema": "cora-capability-request/1", "commit": sha,
                        "tree": self.git("rev-parse", "HEAD^{tree}"),
                        "decisions": [{"id": "cora:archaeology", "reason": "Check real source history",
                                       "obligation": "HISTORY", "test_ids": ["test_calc.CalcTests.test_double"]}],
                        "tests": [{"path": "tests/test_calc.py", "ids": ["test_calc.CalcTests.test_double"]}],
                        "semgrep": None, "timeout": 30}

    def scan_request(self):
        self.request["decisions"].append({"id": "external:semgrep", "reason": "Detect eval in committed input",
                                         "obligation": "NO_EVAL", "test_ids": ["test_calc.CalcTests.test_double"]})
        self.request["semgrep"] = {"rules": {"rules": [{"id": "no-eval", "pattern": "eval(...)",
            "message": "Do not evaluate input", "languages": ["python"], "severity": "ERROR"}]}, "targets": ["calc.py"]}

    def run_operation(self, name="evidence", execute=True):
        from cora.integrated_run import run_capability_operation
        return run_capability_operation(self.repo, self.base, self.request,
                                        execute=execute, evidence_dir=self.home / name)

    def test_existing_analysis_is_reused(self):
        from unittest.mock import patch
        from cora.integrated_run import verify_capability_operation
        with patch("cora.process_suite.run_suite", side_effect=AssertionError("duplicate analysis")):
            report = self.run_operation()
        row = next(r for r in report["rows"] if r["id"] == "cora:archaeology")
        self.assertEqual(row["state"], "REUSED_SOURCE_METHOD_SCOPED")
        self.assertEqual(row["source_digest"], self.base["source_process"]["results"][0]["source_digest"])
        self.assertEqual(report["duplicate_source_executions"], 0)
        self.assertEqual(report["scoped_runtime_goal"], "PASS_SCOPED_LOCAL_UNATTESTED")
        self.assertEqual(report["product_status"], "BLOCKED_EXTERNAL")
        with patch("cora.integrated_run.run_bounded", side_effect=AssertionError("replay executed code")):
            self.assertTrue(verify_capability_operation(self.repo, self.base, report, self.home / "evidence"))

    def test_agent_decisions_override_lexical_ranking(self):
        from cora.process_suite import operational_selection
        row = next(r for r in operational_selection(self.base, self.request) if r["id"] == "cora:archaeology")
        self.assertTrue(row["selected"])
        self.assertFalse(next(r for r in self.base["universal_capability_plan"]["rows"] if r["id"] == "cora:archaeology")["selected"])
        self.assertEqual(len(operational_selection(self.base, self.request)), 81)
        for changed in ("external:invented", "cora:archaeology; rm -rf /"):
            self.request["decisions"][0]["id"] = changed
            with self.assertRaises(ValueError):
                self.run_operation(execute=False)

    def test_unsupported_selected_capability_stays_blocked(self):
        self.request["decisions"][0]["id"] = "external:openhands"
        report = self.run_operation()
        self.assertEqual(report["scoped_runtime_goal"], "DEBT_BLOCKED")
        self.assertEqual(report["agent_handoff"]["next_unresolved"]["id"], "external:openhands")
        self.assertEqual(report["agent_handoff"]["next_unresolved"]["reason"], "BLOCKED_NO_QUALIFIED_ADAPTER")

    def test_real_target_tests_and_mutation(self):
        self.assertEqual(self.run_operation()["scoped_runtime_goal"], "PASS_SCOPED_LOCAL_UNATTESTED")
        (self.repo / "calc.py").write_text("def double(x):\n    return x * 3\n")
        self.commit()
        bad = self.run_operation("mutant-evidence")
        self.assertEqual(bad["scoped_runtime_goal"], "DEBT_BLOCKED")
        self.assertNotEqual(bad["observations"][0]["returncode"], 0)
        self.assertFalse(bad["tests"]["test_calc.CalcTests.test_double"]["successful_run"])

    def test_zero_skipped_and_failed_tests_are_not_pass(self):
        sources = ["import unittest\n", "import unittest\nclass CalcTests(unittest.TestCase):\n    @unittest.skip('not observed')\n    def test_double(self): pass\n",
                   "import unittest\nclass CalcTests(unittest.TestCase):\n    def test_double(self): self.fail('known failure')\n"]
        for i, source in enumerate(sources):
            with self.subTest(source=i):
                (self.repo / "tests/test_calc.py").write_text(source)
                self.commit()
                self.assertEqual(self.run_operation("bad-" + str(i))["scoped_runtime_goal"], "DEBT_BLOCKED")

    def test_denial_bounds_and_stale_source(self):
        from unittest.mock import patch
        from cora.integrated_run import run_capability_operation
        import subprocess
        with patch("cora.integrated_run.run_bounded", side_effect=AssertionError("unconsented effect")):
            report = self.run_operation(execute=False)
            self.assertEqual(report["observations"], [])
            self.assertEqual(report["scoped_runtime_goal"], "DEBT_BLOCKED")
            self.request["commit"] = "a" * 40
            with self.assertRaises(ValueError):
                self.run_operation()
        self.request["commit"] = self.base["commit"]
        for i, error in enumerate((ValueError("output bound"), subprocess.TimeoutExpired(["fixture"], 1), OSError("missing"))):
            with patch("cora.integrated_run.run_bounded", side_effect=error):
                self.assertEqual(self.run_operation("bounded-" + str(i))["scoped_runtime_goal"], "DEBT_BLOCKED")
        with self.assertRaises(ValueError):
            run_capability_operation(self.repo, self.base, self.request, execute=True, evidence_dir=None)
        self.request["tests"][0]["path"] = "../escape.py"
        with self.assertRaises(ValueError):
            self.run_operation(execute=False)

    def test_retained_artifact_tamper_and_test_lineage(self):
        import copy
        from cora.integrated_run import verify_capability_operation
        report = self.run_operation()
        for mutate in (lambda x: x.update(authority="APPROVED"),
                       lambda x: x["tests"].clear(),
                       lambda x: x["rows"].pop(),
                       lambda x: x["request"]["decisions"][0].update(test_ids=["test_calc.CalcTests.nonexistent"])):
            bad = copy.deepcopy(report)
            mutate(bad)
            with self.assertRaises(ValueError):
                verify_capability_operation(self.repo, self.base, bad, self.home / "evidence")
        log = self.home / "evidence" / report["artifacts"][0]["path"]
        log.write_bytes(log.read_bytes() + b"altered\n")
        with self.assertRaises(ValueError):
            verify_capability_operation(self.repo, self.base, report, self.home / "evidence")

    def test_findings_and_errors_block_runtime_goal(self):
        from cora.integrated_run import _operation_projection
        self.scan_request()
        sarif = {"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "Semgrep"}}, "results": [
            {"ruleId": "no-eval", "message": {"text": "eval"}, "locations": [{"physicalLocation": {
                "artifactLocation": {"uri": "calc.py"}, "region": {"startLine": 4}}}]}]}]}
        # Unit envelope tests do not stand in for the separately required real scanner.
        artifacts = {"capability-00.log": b"1.186.0\n", "capability-01.log": b"",
                     "capability-01.sarif": json.dumps(sarif).encode(), "capability-02.log": b"",
                     "capability-01.json": json.dumps({"errors": [], "paths": {"scanned": ["calc.py"]},
                         "results": [{"path": "calc.py", "start": {"line": 4}}]}).encode()}
        obs = [{"id": key, "returncode": 0, "reason": "EXIT_REPORTED", "duration_ms": 1,
                "log": "capability-%02d.log" % i, "sarif": "capability-01.sarif" if i == 1 else None,
                "json": "capability-01.json" if i == 1 else None}
               for i, key in enumerate(("semgrep-version", "external:semgrep", "test:tests/test_calc.py"))]
        p = _operation_projection(self.base, self.request, obs, artifacts)
        self.assertEqual(next(r for r in p["rows"] if r["id"] == "external:semgrep")["state"], "FINDINGS")
        artifacts["capability-01.json"] = b'{"errors": [], "paths": {"scanned": []}, "results": []}'
        p = _operation_projection(self.base, self.request, obs, artifacts)
        self.assertEqual(next(r for r in p["rows"] if r["id"] == "external:semgrep")["state"], "FAIL")
        artifacts["capability-01.sarif"] = b"invalid"
        p = _operation_projection(self.base, self.request, obs, artifacts)
        self.assertEqual(next(r for r in p["rows"] if r["id"] == "external:semgrep")["state"], "FAIL")

    def test_real_semgrep_and_physical_counterexample(self):
        import os, shutil
        from cora.integrated_run import verify_capability_operation
        if not shutil.which("semgrep"):
            if os.environ.get("CORA_REQUIRE_SEMGREP") == "1":
                self.fail("real Semgrep is mandatory in the hosted operational pilot")
            self.skipTest("real Semgrep not installed; native tests run separately")
        self.scan_request()
        vulnerable = self.run_operation("scanner-vulnerable")
        row = next(r for r in vulnerable["rows"] if r["id"] == "external:semgrep")
        self.assertEqual(row["state"], "FINDINGS", vulnerable["observations"])
        self.assertEqual(vulnerable["scoped_runtime_goal"], "DEBT_BLOCKED")
        self.assertTrue(verify_capability_operation(self.repo, self.base, vulnerable, self.home / "scanner-vulnerable"))
        self.retain_pilot("vulnerable", vulnerable, self.home / "scanner-vulnerable")
        (self.repo / "calc.py").write_text("def double(x):\n    return x * 2\ndef parse(s):\n    return int(s)\n")
        self.commit()
        self.scan_request()
        repaired = self.run_operation("scanner-repaired")
        self.assertEqual(repaired["scoped_runtime_goal"], "PASS_SCOPED_LOCAL_UNATTESTED", repaired["observations"])
        self.assertTrue(verify_capability_operation(self.repo, self.base, repaired, self.home / "scanner-repaired"))
        self.retain_pilot("repaired", repaired, self.home / "scanner-repaired")

    def retain_pilot(self, label, report, evidence):
        import os, shutil, subprocess
        destination = os.environ.get("CORA_OPERATIONAL_EVIDENCE_DIR")
        if not destination:
            return
        out = Path(destination) / label
        out.mkdir(parents=True, exist_ok=True)
        shutil.copytree(evidence, out / "evidence", dirs_exist_ok=True)
        subprocess.run(["git", "-C", str(self.repo), "bundle", "create", str(out / "target.bundle"), "--all"], check=True)
        (out / "operation.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
        root = Path(__file__).resolve().parents[1]
        engine = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"]).decode().strip()
        (out / "engine-head.txt").write_text(engine + "\n")

    def test_no_request_preserves_original_dossier(self):
        from unittest.mock import patch
        from cora.cli import main
        with patch("cora.cli.run_integrated") as run:
            run.return_value = {"baseline_pr36": {"source_status": "PASS_SCOPED", "model_stress": {"status": "NOT_RUN"}}, "tests": {"state": "NOT_RUN"}}
            self.assertEqual(main(["process-run", ".", "--one-run", "--profile", "comprehensive"]), 0)
            self.assertNotIn("capability_request", run.call_args.kwargs)
        with patch("cora.cli.run_integrated") as run:
            self.assertEqual(main(["process-run", ".", "--execute-capabilities"]), 3)
            run.assert_not_called()

    def test_declared_dod_has_real_oracles_and_and_dependencies(self):
        from cora.reticulum import ordered_cut
        path = Path(__file__).resolve().parents[1] / ".cora/contracts/dod/optimal-tool-acquisition.json"
        contract = json.loads(path.read_text())["operational_contract"]
        order = ordered_cut(contract["nodes"], contract["goals"]["complete"])
        self.assertEqual(len(order), 22)
        self.assertEqual(set(order), {n["id"] for n in contract["nodes"]})
        for node in contract["nodes"]:
            if node["kind"] == "LOCAL" and node["scope"] != "EXTERNAL":
                self.assertTrue(callable(getattr(self, node["oracle"].split(".")[-1])))
            if node["scope"] == "EXTERNAL" and node["kind"] == "LOCAL":
                self.assertEqual(node["status"], "BLOCKED_EXTERNAL")


class Universal81CapabilityTests(unittest.TestCase):
    """The 81 owners are typed, fail-closed and not 81 launched programs."""

    @staticmethod
    def native():
        names = ["version", "process-list", "snapshot"] + [
            f"fixture-{i:02d}" for i in range(68)]
        return [{"command": n, "family": "git-evidence"} for n in names]

    def test_exact_census_and_nonpromotion(self):
        from cora.process_suite import universal_capability_plan, verify_universal_capability_plan
        names = self.native()
        result = universal_capability_plan(names, commit="a" * 40)
        self.assertEqual(result["counts"], {
            "native": 71, "external": 10, "total": 81,
            "selected": 3, "run_reported": 0, "source_reused": 0, "blocked": 3,
            "not_selected": 78})
        self.assertTrue(verify_universal_capability_plan(names, result))
        self.assertEqual(result["authority"], "NONE")
        self.assertEqual(result["product_status"], "BLOCKED_EXTERNAL")
        self.assertTrue(all(r["state"] == "NOT_SELECTED" for r in result["rows"]
                            if r["kind"] == "UPSTREAM_CANDIDATE"))

    def test_security_intent_uses_upstream_as_blocked_handoff(self):
        from cora.process_suite import universal_capability_plan
        r = universal_capability_plan(self.native(), commit="a" * 40,
                                      intent="security scan sarif")
        semgrep = next(x for x in r["rows"] if x["id"] == "external:semgrep")
        self.assertTrue(semgrep["selected"])
        self.assertEqual(semgrep["state"], "BLOCKED")
        self.assertEqual(semgrep["owner"], "UPSTREAM_EXTERNAL")
        self.assertIsNone(semgrep["output_sha256"])
        self.assertIn("external:semgrep", r["agent_handoff"]["selected"])

    def test_forged_receipts_and_wrong_source_sha_rejected(self):
        from cora.process_suite import universal_capability_plan
        names = self.native()
        sha = "a" * 40
        rows = [{"command": x["command"], "commit": sha, "authority": "NONE",
                 "state": "BLOCKED", "stdout_sha256": None} for x in names]
        ok = universal_capability_plan(names, commit=sha, native_observations=rows)
        self.assertEqual(ok["counts"]["total"], 81)
        for mutate in (
                lambda rows: rows[0].update(commit="b" * 40),
                lambda rows: rows[0].update(stdout_sha256="c" * 64),
                lambda rows: rows[4].update(state="RUN_REPORTED_UNATTESTED"),
                lambda rows: rows[0].update(authority="AI_AGENT")):
            bad = [dict(x) for x in rows]
            mutate(bad)
            with self.subTest(mutation=mutate):
                with self.assertRaises(ValueError):
                    universal_capability_plan(names, commit=sha, native_observations=bad)

    def test_forged_output_replay_rejected(self):
        import copy
        from cora.process_suite import universal_capability_plan, verify_universal_capability_plan
        names = self.native()
        a = universal_capability_plan(names, commit="a" * 40, intent="history")
        for mutator in (
                lambda x: x["counts"].update(total=80),
                lambda x: x["rows"].pop(),
                lambda x: x["rows"][0].update(state="RUN_REPORTED_UNATTESTED"),
                lambda x: x["agent_handoff"].update(human_review_required=False),
                lambda x: x.update(authority="AI_AGENT")):
            altered = copy.deepcopy(a)
            mutator(altered)
            with self.subTest(mutation=mutator):
                with self.assertRaises(ValueError):
                    verify_universal_capability_plan(names, altered)

    def test_backward_reticular_and_contract_not_accepted(self):
        from cora.process_suite import EXTERNAL_TOOLS
        root = Path(__file__).resolve().parents[1]
        data = json.loads((root / ".cora/contracts/dod/post94-cli-behavior-dod.json").read_text())
        cut = data["universal_orchestration"]
        nodes = {n["id"]: n for n in cut["nodes"]}
        self.assertEqual(len(nodes), 19)
        self.assertEqual(len(cut["nodes"]), len(nodes))
        self.assertEqual(cut["source_counts"]["addressable_capabilities"], 81)
        self.assertEqual(cut["source_counts"]["native_cli_declarations"], 71)
        self.assertEqual(cut["source_counts"]["external_candidates"], len(EXTERNAL_TOOLS))
        self.assertEqual(cut["global_status"], "BLOCKED_EXTERNAL")
        self.assertEqual(cut["authority"], "NONE")
        for node in nodes.values():
            self.assertTrue(set(node["depends_on"]) <= set(nodes))
        self.assertTrue(any(n["scope"] == "EXTERNAL" and n["status"] == "BLOCKED_EXTERNAL"
                            for n in nodes.values()))
        self.assertIn("NOT_81_EXECUTED", cut["nonclaims"])

    def test_existing_source_method_is_reused_not_duplicated_cli_execution(self):
        from cora.process_suite import (
            IMPLEMENTED, universal_capability_plan, verify_universal_capability_plan)
        names = self.native()
        names[3]["command"] = "graph"
        names[3]["family"] = "architecture"
        sha = "a" * 40
        methods = [
            {"method": m, "status": "EXECUTED_SCOPED", "source_digest": "f" * 64}
            if m == "python_candidate_graph" else
            {"method": m, "status": "DEBT_BLOCKED"} for m in IMPLEMENTED["full"]]
        report = universal_capability_plan(
            names, commit=sha, intent="architecture imports", source_methods=methods)
        graph = next(x for x in report["rows"] if x["id"] == "cora:graph")
        self.assertEqual(graph["state"], "REUSED_SOURCE_METHOD_SCOPED")
        self.assertEqual(graph["reason"], "SOURCE_METHOD_REUSED_NOT_INDIVIDUAL_CLI_EXECUTION")
        self.assertEqual(graph["source_digest_sha256"], "f" * 64)
        self.assertIsNone(graph["output_sha256"])
        self.assertEqual(report["counts"]["source_reused"], 1)
        self.assertEqual(report["counts"]["run_reported"], 0)
        self.assertTrue(verify_universal_capability_plan(
            names, report, source_methods=methods))
        for changed in ("source_digest_sha256", "state", "reason"):
            forged = json.loads(json.dumps(report))
            wrong = next(x for x in forged["rows"] if x["id"] == "cora:graph")
            wrong[changed] = "FORGED"
            with self.subTest(mutated=changed):
                with self.assertRaises(ValueError):
                    verify_universal_capability_plan(names, forged, source_methods=methods)
        with self.assertRaises(ValueError):
            universal_capability_plan(names, commit=sha, intent="architecture",
                                      source_methods=methods[:-1])
        wrong_methods = [dict(x) for x in methods]
        wrong_methods[0]["source_digest"] = "f" * 64
        with self.assertRaises(ValueError):
            universal_capability_plan(names, commit=sha, source_methods=wrong_methods)

    def test_history_profile_exact_methods_and_unrequested_full_methods(self):
        from cora.process_suite import (
            IMPLEMENTED, universal_capability_plan, verify_universal_capability_plan)
        names = self.native()
        names[3]["command"] = "archaeology"
        sha = "a" * 40
        methods = [{"method": "git_archaeology", "status": "EXECUTED_SCOPED",
                    "source_digest": "d" * 64}]
        result = universal_capability_plan(
            names, commit=sha, intent="history commits",
            source_methods=methods, source_process="history")
        target = next(x for x in result["rows"] if x["id"] == "cora:archaeology")
        self.assertEqual(target["state"], "REUSED_SOURCE_METHOD_SCOPED")
        self.assertEqual(result["counts"]["source_reused"], 1)
        self.assertTrue(verify_universal_capability_plan(
            names, result, source_methods=methods, source_process="history"))
        with self.assertRaises(ValueError):
            universal_capability_plan(
                names, commit=sha, intent="history",
                source_methods=methods, source_process="full")
        with self.assertRaises(ValueError):
            universal_capability_plan(
                names, commit=sha, source_methods=[], source_process="history")
        self.assertEqual(IMPLEMENTED["history"], ("git_archaeology",))

    def test_invalid_inputs_and_duplicate_native_rejected(self):
        from cora.process_suite import universal_capability_plan
        names = self.native()
        for malformed in (names[:-1], names + [names[0]], names[:-1] + [names[0]]):
            with self.assertRaises(ValueError):
                universal_capability_plan(malformed, commit="a" * 40)
        with self.assertRaises(ValueError):
            universal_capability_plan(names, commit="a" * 40, intent="x" * 1025)
