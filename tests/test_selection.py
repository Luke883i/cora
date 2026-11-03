"""Independent Git fixture oracle for the experimental conservative selector."""
from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from cora.cli import main
from cora.evidence import domain_hash
from cora.selection import (selection_from_dossier, select_file,
                            verify_selection, PROTECTED_ROLES)
from cora.selection_stress import (stress_selection, model_selection,
                                   oracle_bit_spec, FAMILIES)


def git(repo, *args):
    return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.STDOUT).decode().strip()


class SelectionOnRealGit(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.repo = Path(self.t.name)
        git(self.repo,'init','-q')
        git(self.repo,'config','user.name','Independent Fixture')
        git(self.repo,'config','user.email','test@invalid.example')
        (self.repo/'src').mkdir()
        (self.repo/'src/main.py').write_text('import src.lib\n')
        (self.repo/'src/lib.py').write_text('VALUE=1\n')
        (self.repo/'src/dead_candidate.py').write_text('VALUE=2\n')
        (self.repo/'src/fake_test.py').write_text('VALUE=3\n')
        (self.repo/'docs').mkdir()
        (self.repo/'docs/arbitrary.txt').write_text('contract fixture\n')
        ontology={'schema':'cora-ontology/1', 'products':[
            {'id':'widget','roots':['src','docs'],'entrypoints':['src/main.py']}],
            'software':[{'id':'engine','roots':['src'],'product_ids':['widget']}]}
        # Commit role declarations separately from use; file names are irrelevant.
        roles={'schema':'cora-artifact-roles/1','rules':[
            {'pattern':'src/*.py','roles':['SOFTWARE_SOURCE'], 'rationale':'Declared software source files'},
            {'pattern':'docs/arbitrary.txt','roles':['CONTRACT_VERIFIER','FIXTURE'], 'rationale':'Declares an overlapping contract fixture and verifier role'},
        ]}
        (self.repo/'cora.ontology.json').write_text(json.dumps(ontology))
        (self.repo/'cora.artifact-roles.json').write_text(json.dumps(roles))
        git(self.repo,'add','.');git(self.repo,'commit','-qm','independent fixture')
        self.commit=git(self.repo,'rev-parse','HEAD')
    def tearDown(self):self.t.cleanup()

    def test_oracle_inbound_import_retains(self):
        x=select_file(self.repo,'src/lib.py')
        self.assertEqual(x['selection']['state'],'RETAIN_EVIDENCED')
        self.assertIn('static_import_candidate_inbound',x['selection']['positive_triggers'])
        self.assertFalse(x['selection']['safe_deletion_proven'])
        self.assertTrue(verify_selection(self.repo,x))

    def test_oracle_entrypoint_retains(self):
        x=select_file(self.repo,'src/main.py')
        self.assertEqual(x['selection']['state'],'RETAIN_EVIDENCED')
        self.assertIn('declared_entrypoint',x['selection']['positive_triggers'])

    def test_oracle_undeclared_test_filename_not_proof(self):
        x=select_file(self.repo,'src/fake_test.py')
        self.assertEqual(x['selection']['state'],'INVESTIGATE')
        self.assertEqual(x['selection']['authorized_action'],'NONE')

    def test_oracle_protected_roles_override_name(self):
        x=select_file(self.repo,'docs/arbitrary.txt')
        self.assertEqual(x['selection']['state'],'RETAIN_EVIDENCED')
        self.assertIn('declared_role:CONTRACT_VERIFIER',x['selection']['positive_triggers'])
        self.assertIn('declared_role:FIXTURE',x['selection']['positive_triggers'])

    def test_candidate_never_dead_code_claim(self):
        x=select_file(self.repo,'src/dead_candidate.py')
        self.assertTrue(x['selection']['selected_for_investigation'])
        self.assertFalse(x['selection']['dead_code_proven'])
        self.assertGreater(len(x['selection']['unclosed_obligations']),5)

    def test_dirty_tree_does_not_change_git_scope(self):
        x=select_file(self.repo,'src/dead_candidate.py')
        (self.repo/'src/dead_candidate.py').write_text('import irrelevant\n')
        self.assertEqual(x,select_file(self.repo,'src/dead_candidate.py'))
        self.assertTrue(verify_selection(self.repo,x))

    def test_signed_looking_forgery_rejected(self):
        x=select_file(self.repo,'src/dead_candidate.py')
        x['selection']['authorized_action']='DELETE'
        x['selection_digest']=domain_hash('CORA:selection:1',{k:v for k,v in x.items() if k!='selection_digest'})
        with self.assertRaises(ValueError):verify_selection(self.repo,x)

    def test_untracked_file_refused(self):
        (self.repo/'not-tracked.py').write_text('x=1')
        with self.assertRaises(ValueError):select_file(self.repo,'not-tracked.py')

    def test_missing_graph_blocks_selection(self):
        (self.repo/'cora.ontology.json').unlink()
        git(self.repo,'add','-A');git(self.repo,'commit','-qm','ontology removed')
        x=select_file(self.repo,'src/dead_candidate.py')
        self.assertEqual(x['selection']['state'],'DEBT_BLOCKED')

    def test_missing_roles_blocks_selection(self):
        (self.repo/'cora.artifact-roles.json').unlink()
        git(self.repo,'add','-A');git(self.repo,'commit','-qm','roles removed')
        x=select_file(self.repo,'src/dead_candidate.py')
        self.assertEqual(x['selection']['state'],'DEBT_BLOCKED')

    def test_undecidable_runtime_remains_unknown(self):
        x=select_file(self.repo,'src/dead_candidate.py')
        self.assertIn('all_runtime_paths_and_traffic',x['selection']['unclosed_obligations'])
        self.assertIn('cross_repository_and_external_consumers',x['selection']['unclosed_obligations'])

    def test_unresolved_symlink_blocks(self):
        (self.repo/'src/link.py').symlink_to('/etc/passwd')
        git(self.repo,'add','.');git(self.repo,'commit','-qm','symlink')
        x=select_file(self.repo,'src/link.py')
        self.assertEqual(x['selection']['state'],'DEBT_BLOCKED')
        self.assertEqual(x['selection']['authorized_action'],'NONE')

    def test_missing_product_ownership_blocks(self):
        (self.repo/'outside.py').write_text('VALUE=10\n')
        role_file=self.repo/'cora.artifact-roles.json'
        roles=json.loads(role_file.read_text())
        roles['rules'].append({'pattern':'outside.py','roles':['SOFTWARE_SOURCE'], 'rationale':'Explicit role, deliberately missing product owner'})
        role_file.write_text(json.dumps(roles))
        git(self.repo,'add','.');git(self.repo,'commit','-qm','unassigned file')
        x=select_file(self.repo,'outside.py')
        self.assertEqual(x['selection']['state'],'DEBT_BLOCKED')

    def test_declared_role_change_is_commit_scoped(self):
        original=select_file(self.repo,'src/fake_test.py')
        role_file=self.repo/'cora.artifact-roles.json'
        roles=json.loads(role_file.read_text())
        roles['rules'].append({'pattern':'src/fake_test.py','roles':['TEST'], 'rationale':'Explicit newly reviewed test role'})
        role_file.write_text(json.dumps(roles))
        git(self.repo,'add','.');git(self.repo,'commit','-qm','role change')
        changed=select_file(self.repo,'src/fake_test.py')
        self.assertEqual(changed['selection']['state'],'RETAIN_EVIDENCED')
        self.assertNotEqual(original['selection_digest'],changed['selection_digest'])
        self.assertTrue(verify_selection(self.repo,original))

    def test_invalid_subject_refused(self):
        with self.assertRaises(ValueError):select_file(self.repo,'../etc/passwd')

    def test_cli_end_to_end(self):
        with tempfile.TemporaryDirectory() as d:
            x=Path(d)/'selection.json'
            self.assertEqual(main(['select-file',str(self.repo),'--path','src/lib.py','--output',str(x)]),0)
            self.assertTrue(x.exists())
            self.assertEqual(main(['verify-selection',str(x),'--repo',str(self.repo)]),0)


class SelectionPolicyProperties(unittest.TestCase):
    def test_all_families_match_oracle_at_boundary_bits(self):
        for family in range(len(FAMILIES)):
            for flags in [0,63,127,255,511,(1<<20)-1, ((1<<20)-1) - (1<<6)]:
                self.assertEqual(model_selection(flags,family)[0],oracle_bit_spec(flags,family))

    def test_no_automatic_removal_anywhere_in_contract(self):
        x=stress_selection(seed=883,cases=10001)
        self.assertEqual((x['mismatches'],x['authorized_destructive_changes']), (0,0))

    def test_replay_is_byte_identical(self):
        self.assertEqual(stress_selection(seed=73,cases=4000),stress_selection(seed=73,cases=4000))

    def test_invalid_cases_refused(self):
        with self.assertRaises(ValueError):stress_selection(cases=1_000_001)

    def test_retain_monotonic_when_adding_positive_reference(self):
        for family in range(24):
            for mask in [63, 63|(1<<14),63|(1<<18)]:
                orig=model_selection(mask,family)[0]
                after=model_selection(mask|(1<<6),family)[0]
                if orig!='DEBT_BLOCKED':self.assertEqual(after,'RETAIN_EVIDENCED')

    def test_unknown_not_removal_authority(self):
        for role in PROTECTED_ROLES:self.assertIsInstance(role,str)
        x=stress_selection(cases=333)
        self.assertEqual(x['authorized_destructive_changes'],0)

if __name__=='__main__':unittest.main()
