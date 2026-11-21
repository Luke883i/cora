"""Finite, original CLI behavioral probes for twenty previously unobserved routes.

Only disposable Git and ZIP fixtures are changed. No external agent, scanner,
Docker, human identity or release is authorized by these tests. Their PASS is
source-scoped behavior, not acceptance of a maintained target or host.
"""
from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from cora.cli import main
from cora.evidence import domain_hash

ROOT = Path(__file__).resolve().parents[1]


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.STDOUT).decode().strip()


class RemainingTwentyCLI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cora-remaining20-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root/'target'
        self.repo.mkdir()
        git(self.repo, 'init', '-q')
        git(self.repo, 'config', 'user.name', 'Fixture')
        git(self.repo, 'config', 'user.email', 'fixture@example.invalid')
        (self.repo/'docs').mkdir()
        (self.repo/'docs/old.md').write_text('# Original\nlink docs/old.md\n')
        (self.repo/'README.md').write_text('link docs/old.md\n')
        (self.repo/'src').mkdir()
        (self.repo/'src/app.py').write_text('VALUE = 1\n')
        git(self.repo,'add','.');git(self.repo,'commit','-qm','base')
        self.base = git(self.repo,'rev-parse','HEAD')
        (self.repo/'src/app.py').write_text('VALUE = 2\n')
        git(self.repo,'add','.');git(self.repo,'commit','-qm','change')
        self.head = git(self.repo,'rev-parse','HEAD')
        self.n=0

    def call(self,command,*args,expected=0):
        self.n+=1
        result=self.root/f'observation-{self.n}.json'
        stdout,stderr=io.StringIO(),io.StringIO()
        with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
            exit_code=main([command,*map(str,args),'--output',str(result)])
        self.assertEqual(exit_code,expected,f'{command}: stdout={stdout.getvalue()[:700]} stderr={stderr.getvalue()[:700]}')
        self.assertTrue(result.exists(),f'{command} produced no JSON receipt')
        obj=json.loads(result.read_text())
        self.assertIsInstance(obj,dict)
        return result,obj

    def test_01_audit_real_worktree(self):
        p,result=self.call('audit',self.repo)
        self.assertEqual(result['schema'],'cora-pr01-inventory/1')
        self.assertEqual(result['coverage']['runtime'],'unsupported')
        self.assertTrue(any(row['path']=='src/app.py' for row in result['files']))

    def test_02_explain_pinned_graph(self):
        from cora.graph import graph_from_commit
        ontology={'schema':'cora-ontology/1','products':[{'id':'sample','roots':['src'],'entrypoints':['src/app.py']}],
                  'software':[{'id':'pkg','roots':['src'],'product_ids':['sample']}]}
        (self.repo/'cora.ontology.json').write_text(json.dumps(ontology))
        git(self.repo,'add','.');git(self.repo,'commit','-qm','ontology')
        graph=graph_from_commit(self.repo,'HEAD')
        path=self.root/'graph.json';path.write_text(json.dumps(graph))
        # Explain existing node to itself with a valid, Git-replayed graph.
        node='file:src/app.py'
        p,report=self.call('explain',path,'--repo',self.repo,'--source',node,'--target',node)
        self.assertIsInstance(report,dict)

    def test_03_file_decision_no_target_mutation(self):
        lab=self.root/'lab.json'
        self.assertEqual(main(['file-lab',str(self.repo),'--path','src/app.py','--output',str(lab)]),0)
        before=git(self.repo,'status','--porcelain')
        p,report=self.call('file-decision',lab,'--actor','maintainer','--role','MAINTAINER','--action','INVESTIGATE','--rationale','Unknown external consumers')
        self.assertEqual(report['effect'],'RECORD_ONLY_NO_REPO_CHANGES')
        self.assertEqual(git(self.repo,'status','--porcelain'),before)

    def test_04_annotate_groups_untrusted_hypothesis(self):
        report_path=self.root/'holistic.json'
        self.assertEqual(main(['holistic-audit',str(self.repo),'--max-commits','4','--output',str(report_path)]),0)
        report=json.loads(report_path.read_text())
        h={'schema':'cora-group-hypotheses/1','report_digest':report['report_digest'],'hypotheses':[]}
        hp=self.root/'hypotheses.json';hp.write_text(json.dumps(h))
        p,overlay=self.call('annotate-groups',report_path,'--repo',self.repo,'--hypotheses',hp)
        self.assertEqual(overlay['effect'],'ANNOTATION_ONLY_NO_ARCHIVE_QUARANTINE_RENAME_OR_DELETE')

    def test_05_debt_diff_revisions(self):
        p,report=self.call('debt-diff',self.repo,'--base',self.base,'--head',self.head,'--max-commits','4')
        self.assertIsInstance(report,dict)
        self.assertNotEqual(self.base,self.head)

    def test_06_07_doc_plan_and_apply_on_disposable_checkout(self):
        # This is an authorized local fixture mutation, never a user repository.
        # No untracked data in the target worktree.
        planpath,plan=self.call('plan-rename-doc',self.repo,'--old','docs/old.md','--new','docs/new.md')
        self.assertEqual(plan['plan_digest'],domain_hash('CORA:transform-plan:1',
            {k:v for k,v in plan.items() if k!='plan_digest'}))
        p,applied=self.call('apply-rename-doc',self.repo,'--plan',planpath,
                            '--approve',plan['plan_digest'],'--test-command',
                            f'{sys.executable} -c "assert True"')
        self.assertEqual(applied['status'],'SCOPED_APPLIED_TESTS_PASSED')
        self.assertTrue((self.repo/'docs/new.md').exists())
        self.assertFalse((self.repo/'docs/old.md').exists())

    def test_08_09_guard_install_check_disposable_git(self):
        p,installed=self.call('guard-install',self.repo,'--product','app=src=src')
        self.assertEqual(installed['status'],'CREATED_UNCOMMITTED')
        git(self.repo,'add','.');git(self.repo,'commit','-qm','install local guard')
        p,checked=self.call('guard-check',self.repo,'--base',git(self.repo,'rev-parse','HEAD'))
        self.assertEqual(checked['status'],'PASS_SCOPED')

    def test_10_agent_check_source_bound(self):
        doc={'schema':'cora-agent-proposal/1','agent_id':'fixture-agent-001',
             'base_commit':self.base,'head_commit':self.head,
             'intent':'audit only source change','changed_paths':['src/app.py'],
             'test_claims':['unit passing by claim'], 'unknowns':['runtime'], 'authorized_action':'NONE'}
        f=self.root/'proposal.json';f.write_text(json.dumps(doc))
        p,r=self.call('agent-check',f,'--repo',self.repo)
        self.assertEqual(r['test_trust'],'UNVERIFIED_AGENT_ASSERTIONS')
        self.assertEqual(r['authorization'],'NONE')

    def test_11_12_dod_assess_and_replay(self):
        claims={'schema':'cora-agent-claims/1','head_sha':self.head,'locals':{}}
        f=self.root/'claims.json';f.write_text(json.dumps(claims))
        c=ROOT/'.cora/contracts/dod/agent-dod.json'
        receipt,r=self.call('dod-assess',f,'--contract',c,expected=2)
        self.assertNotEqual(r['goal_status'],'PASS')
        _,v=self.call('verify-dod',receipt,'--observations',f,'--contract',c)
        self.assertEqual(v['authorization'],'NONE')

    def test_13_verify_contextual_gate(self):
        c=ROOT/'.cora/contracts/dod/convergence-dod.json'
        fp=self.root/'contextual.json'
        # A source-only producer and exact-Git verifier; external approval remains absent.
        code=main(['dev-premerge',str(self.repo),'--contextual','--base',self.base,
                    '--head',self.head,'--convergence-contract',str(c),'--output',str(fp)])
        self.assertEqual(code,0)
        _,v=self.call('verify-contextual-gate',fp,'--repo',self.repo,'--convergence-contract',c)
        self.assertEqual(v['authorization'],'NONE')

    def test_14_gold_pilot_blocks_missing_external_repositories(self):
        # Correct local behavior is an attributable BLOCK, not fabricated 3/3 pass.
        path=self.root/'gold-pilot.json'
        ret=main(['gold-pilot','--contract',str(ROOT/'.cora/contracts/dod/gold-assurance.json'),
                  '--output',str(path)])
        self.assertEqual(ret,2)
        r=json.loads(path.read_text())
        self.assertEqual(r['state'],'BLOCKED_INCOMPLETE')
        self.assertEqual(r['source_readbacks_verified'],0)

    def test_15_gold_mutate_physical_ast_only(self):
        src=self.root/'mutants';src.mkdir()
        (src/'main.py').write_text('FLAG = True\n')
        plan={'schema':'cora-physical-mutants/1','oracle':{'kind':'PYTHON_AST','path':'main.py'},
              'mutants':[{'id':'syntax-break','path':'main.py','old':'FLAG = True','new':'def broken(:'}]}
        f=self.root/'plan.json';f.write_text(json.dumps(plan))
        _,r=self.call('gold-mutate',src,f)
        self.assertEqual(r['status'],'SCOPED_ORACLE_KILLED_ALL')
        self.assertFalse(r['sandbox_attested'])
        self.assertFalse(r['runtime_executed'])
        self.assertEqual((src/'main.py').read_text(),'FLAG = True\n')

    def test_16_runtime_observe_nonexecuting_path(self):
        archive=self.root/'bundle.zip';work=self.root/'work';work.mkdir()
        (work/'README.md').write_text('fixture\n')
        with zipfile.ZipFile(archive,'w') as z:z.write(work/'README.md','bundle/README.md')
        _,r=self.call('runtime-observe',archive,'--workspace',work)
        self.assertEqual(r['execution_status'],'NOT_REQUESTED')
        self.assertEqual(r['sandbox_assurance'],'NOT_INDEPENDENTLY_ATTESTED')

    def test_17_18_19_20_small_finite_models(self):
        cases=[
          ('stress-artifact-semantics',['--minimum-cases','1','--no-novelty','1'],0),
          ('stress-agent-dod',['--contract',str(ROOT/'.cora/contracts/dod/agent-dod.json'),
                               '--sessions','1','--cases-per-session','400'],0),
          ('stress-gold',['--contract',str(ROOT/'.cora/contracts/dod/gold-assurance.json'),
                          '--sessions','1','--cases-per-session','300'],0),
          ('stress-convergence',['--contract',str(ROOT/'.cora/contracts/dod/convergence-dod.json'),
                                 '--sessions','1','--cases-per-session','4000'],0)]
        for cmd,args,expected in cases:
            with self.subTest(command=cmd):
                _,report=self.call(cmd,*args,expected=expected)
                self.assertEqual(report.get('authorization','NONE'),'NONE')
                self.assertIn(report.get('status'), (None,'PASS_SCOPED_FINITE_MODEL','PARTIAL_NOT_10M'))

    def test_negative_approval_and_oracle_forgery(self):
        planpath,plan=self.call('plan-rename-doc',self.repo,'--old','docs/old.md','--new','docs/new.md')
        before=git(self.repo,'status','--porcelain')
        code=main(['apply-rename-doc',str(self.repo),'--plan',str(planpath),
                   '--approve','forged','--test-command',f'{sys.executable} -c "assert True"'])
        self.assertEqual(code,3)
        self.assertEqual(git(self.repo,'status','--porcelain'),before)
        self.assertTrue((self.repo/'docs/old.md').exists())
        code=main(['gold-pilot','--contract',str(ROOT/'.cora/contracts/dod/gold-assurance.json')])
        self.assertEqual(code,2)

    def test_negative_untrusted_hypothesis_does_not_override_git(self):
        hp=self.root/'holistic.json'
        self.assertEqual(main(['holistic-audit',str(self.repo),'--max-commits','4',
                               '--output',str(hp)]),0)
        forged={'schema':'cora-group-hypotheses/1','report_digest':'0'*64,
                'hypotheses':[]}
        path=self.root/'fake-hypotheses.json';path.write_text(json.dumps(forged))
        before=git(self.repo,'status','--porcelain')
        self.assertEqual(main(['annotate-groups',str(hp),'--repo',str(self.repo),
                               '--hypotheses',str(path)]),3)
        self.assertEqual(git(self.repo,'status','--porcelain'),before)

    def test_negative_agent_cannot_self_authorize(self):
        p={'schema':'cora-agent-proposal/1','agent_id':'agent-001','base_commit':self.base,
           'head_commit':self.head,'intent':'delete unreviewed code',
           'changed_paths':['src/app.py'],'test_claims':['green'],
           'unknowns':['external'],'authorized_action':'DELETE'}
        f=self.root/'agent.json';f.write_text(json.dumps(p))
        self.assertEqual(main(['agent-check',str(f),'--repo',str(self.repo)]),3)

    def test_negative_guard_second_install_fails_without_overwrite(self):
        self.call('guard-install',self.repo,'--product','app=src=src')
        b=(self.repo/'.cora/policy.json').read_bytes()
        self.assertEqual(main(['guard-install',str(self.repo),'--product','app=src=src']),3)
        self.assertEqual((self.repo/'.cora/policy.json').read_bytes(),b)

    def test_negative_dod_claim_with_forged_report_does_not_replay(self):
        c=ROOT/'.cora/contracts/dod/agent-dod.json'
        f=self.root/'claim.json';f.write_text(json.dumps({'schema':'cora-agent-claims/1',
               'head_sha':self.head,'locals':{}}))
        report,r=self.call('dod-assess',f,'--contract',c,expected=2)
        r['report_digest']='0'*64;report.write_text(json.dumps(r))
        self.assertEqual(main(['verify-dod',str(report),'--observations',str(f),
                               '--contract',str(c)]),3)

    def test_negative_gold_mutation_survivor_does_not_pass(self):
        source=self.root/'source';source.mkdir()
        (source/'f.py').write_text('VALUE = 3\n')
        plan={'schema':'cora-physical-mutants/1',
              'oracle':{'kind':'PYTHON_AST','path':'f.py'},
              'mutants':[{'id':'survivor','path':'f.py','old':'VALUE = 3','new':'VALUE = 4'}]}
        f=self.root/'mutants.json';f.write_text(json.dumps(plan))
        _,r=self.call('gold-mutate',source,f,expected=2)
        self.assertEqual(r['status'],'BLOCKED_MUTANT_SURVIVOR_OR_UNKNOWN')
        self.assertEqual(r['counts']['survived'],1)
        self.assertEqual((source/'f.py').read_text(),'VALUE = 3\n')


class ReticularDoD(unittest.TestCase):
    def setUp(self):
        self.contract=json.loads((ROOT/'.cora/contracts/dod/post94-cli-behavior-dod.json').read_text('utf-8'))

    @staticmethod
    def validate(d):
        commands=d.get('previously_missing_commands')
        if not isinstance(commands,list) or len(commands)!=20 or len(set(commands))!=20:
            return 'missing-twenty'
        nodes=d.get('nodes', [])
        idx={x.get('id'):x for x in nodes}
        if len(idx)!=len(nodes) or len(idx)!=79:
            return 'invalid-reticulum-cardinality'
        if d.get('global_status')!='NOT_ACCEPTED' or d.get('release_authorized') is not False:
            return 'unsupported-approval'
        if (d.get('goal')!='G_71_CAPABILITY_ACCEPTED' or
                d.get('slice_goal')!='G_20_SCOPED_CHARACTERIZED'):
            return 'reticular-goal-forged'
        if (d.get('original_main')!='dbff5f12ba996cfcdaef35c3016c47c6ec3805d1' or
                d.get('original_tree')!='7b9f1dfe8e932f5937f6fae81b20b6170f69bbdf'):
            return 'source-pin-forged'
        if d.get('external_tools') != {'count':10,'state':'CANDIDATE_NOT_EXECUTED_BY_DEFAULT','authority':'NONE'}:
            return 'upstream-execution-promotion'
        for x in nodes:
            if not set(x['depends_on']).issubset(idx):
                return 'unknown-dependency'
            if x['kind']=='LOCAL' and (
                    x.get('acceptance_status')!='NOT_ACCEPTED' or
                    x.get('external_authority')!='BLOCKED_EXTERNAL' or
                    not x.get('positive_oracle') or not x.get('negative_oracle')):
                return 'local-oracle-or-authority-invalid'
        target=idx.get('G_71_CAPABILITY_ACCEPTED')
        if target is None or set(target.get('depends_on',[]))!={'G_20_SCOPED_CHARACTERIZED','I_PRIOR_51','I_PROCESS_INTEGRATION','E_TARGET_HOST','E_REVIEW_RELEASE'}:
            return 'global-and-cut-changed'
        if set(idx['I_NEW_20']['depends_on']) != {'L_BEHAVIOR_'+c.upper().replace('-','_') for c in commands}:
            return 'twenty-cut-changed'
        if len(idx['I_PRIOR_51']['depends_on']) != 51:
            return 'previous-command-coverage-gap'
        test= (ROOT/'tests/test_post94_remaining20.py').read_text('utf-8')
        for c in commands:
            node=idx.get('L_BEHAVIOR_'+c.upper().replace('-','_'))
            if (not node or node['acceptance_status']!='NOT_ACCEPTED'
                or node['external_authority']!='BLOCKED_EXTERNAL'
                or not node['positive_oracle'] or not node['negative_oracle']
                or node['witness'].split('.')[-1] not in test):
                return 'local-witness-missing-or-falsely-promoted:'+c
        return None

    def test_global_intermediate_local_backward_AND_DoD(self):
        self.assertIsNone(self.validate(self.contract))

    def test_physical_counterexamples_do_not_promote_forged_acceptance(self):
        import copy
        cases=[
            ('missing-command',lambda x:x['previously_missing_commands'].pop()),
            ('lost-reticular-edge',lambda x:x['nodes'][-1]['depends_on'].pop()),
            ('fake-release',lambda x:x.update(release_authorized=True)),
            ('goal-forgery',lambda x:x.update(goal='CLAIMED_APPROVED')),
            ('source-pin-forgery',lambda x:x.update(original_main='0'*40)),
            ('external-tool-execution',lambda x:x['external_tools'].update(state='EXECUTED')),
            ('absent-local-oracle',lambda x:x['nodes'][0].update(positive_oracle='')),
            ('self-approved-node',lambda x:x['nodes'][0].update(acceptance_status='PASS')),
        ]
        for name,mutate in cases:
            with self.subTest(case=name):
                x=copy.deepcopy(self.contract)
                mutate(x)
                self.assertIsNotNone(self.validate(x),name)

class OneRun71FrontierTests(unittest.TestCase):
    """71 attributable CLI routes, three bounded operations, 68 blocked."""

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(prefix="cora-onerun-71-")
        self.addCleanup(self._temp.cleanup)
        self.repo = Path(self._temp.name) / "target"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        (self.repo / "a.py").write_text("flag = True\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=CORA Fixture",
                        "-c", "user.email=fixture@example.invalid",
                        "commit", "-qm", "fixture"], check=True)
        self.sha = subprocess.check_output(
            ["git", "-C", str(self.repo), "rev-parse", "HEAD"], text=True).strip()
        self.catalog = json.loads(
            (ROOT / ".cora/assurance/capability-atlas.json").read_text())["commands"]

    def test_real_bounded_subprocess_three_of_seventy_one(self):
        from cora.one_run import run_cli_capabilities, verify_cli_capabilities
        rows = run_cli_capabilities(self.repo, self.sha, self.catalog)
        self.assertEqual(len(rows), 71)
        self.assertEqual({x["command"] for x in rows
                          if x["state"] == "RUN_REPORTED_UNATTESTED"},
                         {"version", "process-list", "snapshot"})
        self.assertEqual(sum(x["state"] == "BLOCKED" for x in rows), 68)
        self.assertTrue(verify_cli_capabilities(self.repo, self.sha, self.catalog, rows))
        self.assertTrue(all(x["authority"] == "NONE" for x in rows))

    def test_forged_counterfeit_success_wrong_head_and_missing_route_fail(self):
        import copy
        from cora.one_run import run_cli_capabilities, verify_cli_capabilities
        rows = run_cli_capabilities(self.repo, self.sha, self.catalog)
        candidates = [copy.deepcopy(rows) for _ in range(5)]
        candidates[0][0].update(state="RUN_REPORTED_UNATTESTED",
             reason="BOUNDED_READ_ONLY_EXIT_ZERO", returncode=0, stdout_sha256="0"*64)
        candidates[1][0]["authority"] = "APPROVED"
        candidates[2][0]["commit"] = "0"*40
        candidates[3] = candidates[3][1:]
        candidates[4][-1]["stdout_sha256"] = "f"*64
        for index, candidate in enumerate(candidates):
            with self.subTest(counterexample=index), self.assertRaises(ValueError):
                verify_cli_capabilities(self.repo, self.sha, self.catalog, candidate)

    def test_overflow_and_bad_exit_never_count_as_pass(self):
        from unittest.mock import patch
        from cora.one_run import run_cli_capabilities, verify_cli_capabilities
        with patch("cora.one_run.run_bounded", side_effect=ValueError("overflow")):
            blocked = run_cli_capabilities(self.repo, self.sha, self.catalog)
        self.assertEqual(sum(x["state"] == "BLOCKED" for x in blocked), 71)
        self.assertTrue(verify_cli_capabilities(self.repo, self.sha, self.catalog, blocked))
        with patch("cora.one_run.run_bounded",
                   return_value=subprocess.CompletedProcess([], 37, b"wrong", None)):
            failed = run_cli_capabilities(self.repo, self.sha, self.catalog)
        self.assertEqual(sum(x["state"] == "FAIL" for x in failed), 3)
        self.assertTrue(verify_cli_capabilities(self.repo, self.sha, self.catalog, failed))

    def test_extra_or_duplicate_route_is_rejected(self):
        import copy
        from cora.one_run import run_cli_capabilities
        with self.assertRaisesRegex(ValueError, "71 unique"):
            run_cli_capabilities(self.repo, self.sha, self.catalog[:-1])
        duplicate = copy.deepcopy(self.catalog)
        duplicate[-1]["command"] = duplicate[0]["command"]
        with self.assertRaisesRegex(ValueError, "71 unique"):
            run_cli_capabilities(self.repo, self.sha, duplicate)

    def test_global_intermediate_local_reticulum_remains_blocked(self):
        d = json.loads((ROOT / ".cora/contracts/dod/post94-cli-behavior-dod.json").read_text())
        f = d["orchestration_frontier"]
        self.assertEqual(f["schema"], "cora-one-run-cli-operational-frontier/1")
        self.assertEqual(f["global_status"], "BLOCKED_EXTERNAL")
        self.assertEqual(f["authority"], "NONE")
        self.assertEqual(len(f["canonical_local_node_refs"]), 71)
        self.assertEqual(len(set(f["canonical_local_node_refs"])), 71)
        self.assertEqual(set(f["canonical_local_node_refs"]),
                         {x["id"] for x in d["nodes"] if x.get("kind") == "LOCAL"})
        self.assertEqual({x["command"] for x in f["operational_adapters"]},
                         {"version", "process-list", "snapshot"})
        self.assertEqual(f["nonoperational_policy"]["count"], 68)
        self.assertEqual({x["state"] for x in f["intermediates"]
                          if x["id"].startswith("E_")}, {"BLOCKED_EXTERNAL"})
        self.assertFalse(f["observed_local_expected"]["release_approved"])

    def test_frontier_requires_pinned_original_git_contract(self):
        from cora.one_run import _cli_frontier_at_revision
        self.assertFalse(_cli_frontier_at_revision(self.repo, self.sha))
        current = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
        self.assertTrue(_cli_frontier_at_revision(ROOT, current))

    def test_integrated_dossier_attribution_is_bounded_and_non_authorizing(self):
        from cora.one_run import run_cli_capabilities
        from cora.integrated_run import _attempts, _metrics
        rows = run_cli_capabilities(self.repo, self.sha, self.catalog)
        registry = {"activities": [
            {"activity_id": "cli:" + x["command"], "kind": "CLI_COMMAND",
             "effect_class": ("READ_ONLY" if x["command"] in
                              ("version", "process-list", "snapshot")
                              else "REQUIRES_EFFECT_REVIEW"), "source_paths": []}
            for x in self.catalog], "registered_commands": 71}
        test = {"parsed_cases": [], "log_sha256": None, "state": "NOT_RUN",
                "reported_tests": None}
        attempts = _attempts(registry, {"activities": [], "cli_capability_attempts": rows}, test)
        self.assertEqual(len(attempts), 71)
        self.assertEqual(sum(x["state"] == "RUN_REPORTED_UNATTESTED"
                             for x in attempts), 3)
        self.assertEqual(_metrics(registry, attempts, test)["individually_executed_cli"], 3)
        self.assertTrue(all(x["authority"] == "NONE" for x in attempts))

