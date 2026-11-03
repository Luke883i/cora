"""PR-14 independently authored Git lifecycle and agent-adversarial oracles."""
from __future__ import annotations
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from cora.continuous import evaluate,verify_gate,agent_check,SCHEMA,POLICY_SCHEMA
from cora.continuous_stress import observed_policy,independent_truth_table,stress_continuous
from cora.evidence import domain_hash
from cora.cli import main


def git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.STDOUT).decode().strip()


POLICY={'schema':POLICY_SCHEMA,'version':1,'max_changed_paths':20,
    'high_risk_prefixes':['.github/workflows','.cora'],
    'high_risk_paths':['GOVERNANCE.md','pyproject.toml'],
    'required_human_roles':['MAINTAINER','INDEPENDENT_SECURITY_REVIEWER'],
    'review_processes':['source','history','debt','verification']}


class GitLifecycleFixtures(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.repo=Path(self.tmp.name)
        git(self.repo,'init','-q');git(self.repo,'config','user.email','git@invalid.example')
        git(self.repo,'config','user.name','Independent Fixture')
        (self.repo/'src').mkdir()
        (self.repo/'src/a.py').write_text('print(1)\n')
        git(self.repo,'add','.');git(self.repo,'commit','-qm','base')
        self.no_policy=git(self.repo,'rev-parse','HEAD')
        (self.repo/'.cora').mkdir()
        (self.repo/'.cora/continuous-policy.json').write_text(json.dumps(POLICY))
        git(self.repo,'add','.');git(self.repo,'commit','-qm','establish-policy')
        self.base=git(self.repo,'rev-parse','HEAD')
        (self.repo/'src/a.py').write_text('print(2)\n')
        git(self.repo,'add','.');git(self.repo,'commit','-qm','change')
        self.head=git(self.repo,'rev-parse','HEAD')
    def tearDown(self):self.tmp.cleanup()

    def test_regular_premerge_is_observational_only(self):
        x=evaluate(self.repo,self.base,self.head)
        self.assertEqual(x['status'],'OBSERVED_REVIEW_REQUIRED')
        self.assertEqual(x['high_risk_paths'],[])
        self.assertEqual(x['authorization'],'NONE')
        self.assertEqual(x['ci_review_attestation'],'NOT_VERIFIED_BY_OFFLINE_CORA')
        self.assertTrue(verify_gate(self.repo,x))
    def test_policy_self_change_does_not_rewrite_baseline(self):
        policy=self.repo/'.cora/continuous-policy.json'
        policy.write_text(json.dumps({**POLICY,'high_risk_prefixes':['irrelevant']}))
        git(self.repo,'add','.');git(self.repo,'commit','-qm','try-policy-bypass')
        x=evaluate(self.repo,self.base,'HEAD')
        self.assertTrue(x['policy_modified'])
        self.assertIn('.cora/continuous-policy.json',x['high_risk_paths'])
        self.assertIn('POLICY_CHANGED_REQUIRES_INDEPENDENT_REVIEW',x['blockers'])
        self.assertIn('INDEPENDENT_SECURITY_REVIEWER',x['required_human_roles'])
    def test_workflow_change_is_high_risk(self):
        p=self.repo/'.github/workflows/check.yml';p.parent.mkdir(parents=True)
        p.write_text('name: no-protection\n')
        git(self.repo,'add','.');git(self.repo,'commit','-qm','new-workflow')
        self.assertIn('.github/workflows/check.yml',evaluate(self.repo,self.base,'HEAD')['high_risk_paths'])
    def test_bootstrap_policy_not_self_attested(self):
        x=evaluate(self.repo,self.no_policy,self.base)
        self.assertEqual(x['status'],'BOOTSTRAP_REVIEW_REQUIRED')
        self.assertIn('TRUSTED_BASE_POLICY_NOT_YET_ESTABLISHED',x['blockers'])
    def test_no_policy_without_proposal_blocks(self):
        x=evaluate(self.repo,self.no_policy,self.no_policy)
        self.assertEqual(x['status'],'BLOCKED')
    def test_no_ancestry_is_blocked(self):
        x=evaluate(self.repo,self.head,self.base)
        self.assertEqual(x['status'],'BLOCKED')
    def test_renamed_workflow_checks_source_and_target(self):
        p=self.repo/'.github/workflows/main.yml';p.parent.mkdir(parents=True)
        p.write_text('name: workflow\n');git(self.repo,'add','.');git(self.repo,'commit','-qm','workflow')
        old=git(self.repo,'rev-parse','HEAD')
        p.rename(self.repo/'workflow-backup.yml')
        git(self.repo,'add','-A');git(self.repo,'commit','-qm','rename-out')
        x=evaluate(self.repo,old,'HEAD')
        self.assertIn('workflow-backup.yml',x['high_risk_paths'])
    def test_hash_reforged_fails_against_git(self):
        report=evaluate(self.repo,self.base,self.head)
        report['status']='OBSERVED_REVIEW_REQUIRED'
        report['changed_paths'][0]['new_path']='injected.py'
        report['receipt_digest']=domain_hash('CORA:continuous-gate:1',{k:v for k,v in report.items() if k!='receipt_digest'})
        with self.assertRaises(ValueError):verify_gate(self.repo,report)
    def test_dirty_worktree_does_not_change_committed_result(self):
        prev=evaluate(self.repo,self.base,self.head)
        (self.repo/'src/a.py').write_text('uncommitted\n')
        self.assertEqual(prev,evaluate(self.repo,self.base,self.head))
    def test_postmerge_debt_drift_is_replayed_not_declared_resolved(self):
        report=evaluate(self.repo,self.base,self.head,phase='postmerge',with_debt=True)
        self.assertNotIn('DEBT_COMPARISON_UNAVAILABLE',report['blockers'])
        self.assertEqual(report['debt_delta']['base_commit'],self.base)
        self.assertEqual(report['debt_delta']['head_commit'],self.head)
        self.assertEqual(report['authorization'],'NONE')
        self.assertTrue(verify_gate(self.repo,report))

    def test_postmerge_proves_only_git_delta(self):
        report=evaluate(self.repo,self.base,self.head,phase='postmerge')
        self.assertEqual(report['phase'],'postmerge')
        self.assertIsNone(report['debt_delta'])
        self.assertEqual(report['runtime_deployment_attestation'],'NOT_VERIFIED')
        self.assertTrue(verify_gate(self.repo,report))
    def test_agent_cannot_assert_fake_changes(self):
        proposal={'schema':'cora-agent-proposal/1','agent_id':'agent-ref-1234','base_commit':self.base,
                  'head_commit':self.head,'intent':'change module','changed_paths':['other.py'],
                  'test_claims':[],'unknowns':['runtime'],'authorized_action':'NONE'}
        with self.assertRaises(ValueError):agent_check(self.repo,proposal)
    def test_agent_test_claims_remain_unverified(self):
        proposal={'schema':'cora-agent-proposal/1','agent_id':'agent-ref-1234','base_commit':self.base,
                  'head_commit':self.head,'intent':'change module','changed_paths':['src/a.py'],
                  'test_claims':['all tests passed'],'unknowns':['runtime'],'authorized_action':'NONE'}
        x=agent_check(self.repo,proposal)
        self.assertEqual(x['test_trust'],'UNVERIFIED_AGENT_ASSERTIONS')
        self.assertEqual(x['authorization'],'NONE')
    def test_agent_cannot_approve(self):
        proposal={'schema':'cora-agent-proposal/1','agent_id':'agent-ref-1234','base_commit':self.base,
                  'head_commit':self.head,'intent':'remove data','changed_paths':['src/a.py'],
                  'test_claims':[],'unknowns':[],'authorized_action':'DELETE'}
        with self.assertRaises(ValueError):agent_check(self.repo,proposal)
    def test_cli_pre_and_verify_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'receipt.json'
            self.assertEqual(main(['dev-premerge',str(self.repo),'--base',self.base,'--head',self.head,'--output',str(p)]),0)
            self.assertEqual(main(['verify-dev-gate',str(p),'--repo',str(self.repo)]),0)
    def test_cli_strict_bootstrap_fails_closed(self):
        self.assertEqual(main(['dev-premerge',str(self.repo),'--base',self.no_policy,'--head',self.base,'--strict']),2)


class ContractFixtures(unittest.TestCase):
    def test_self_role_declarations_are_canonical(self):
        from cora.artifact_roles import validate_declarations
        path=Path(__file__).resolve().parents[1]/'cora.artifact-roles.json'
        rules=json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(validate_declarations(rules)['schema'],'cora-artifact-roles/1')

    def test_workflow_persists_review_receipts_without_privileged_event(self):
        workflow=(Path(__file__).resolve().parents[1]/'.github/workflows/ci-continuous-development.yml').read_text()
        self.assertNotIn('pull_request_target:',workflow)
        self.assertIn('contents: read',workflow)
        self.assertEqual(workflow.count('upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02'),2)
        self.assertIn('retention-days: 14',workflow)
        self.assertIn('retention-days: 30',workflow)

    def test_model_oracle_exhaustive_first_10000(self):
        for mask in range(10000):self.assertEqual(observed_policy(mask),independent_truth_table(mask))
    def test_small_deterministic_replay(self):
        a=stress_continuous(seed=883,cases=2000)
        self.assertEqual(a,stress_continuous(seed=883,cases=2000))
        self.assertEqual((a['distinct_input_masks'],a['mismatches']),(2000,0))

if __name__=='__main__':unittest.main()
