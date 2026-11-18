"""Portable source manifest path binding: original Git receipts, no root fakes."""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from cora.portable_assurance import run_portable, verify_portable

def git(root,*argv):
    return subprocess.check_output(['git','-C',str(root),*argv],text=True).strip()

class TestPortableNonRootManifests(unittest.TestCase):
    def test_source_roles_and_graph_are_executed_not_skipped(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);target=root/'target';target.mkdir()
            (target/'contracts').mkdir();(target/'host').mkdir()
            (target/'host'/'edu.mjs').write_text('export const start=()=>1;\n')
            (target/'contracts'/'roles.json').write_text(json.dumps({
                'schema':'cora-artifact-roles/1','rules':[{
                'pattern':'host/*','roles':['SOFTWARE_SOURCE'],
                'rationale':'Git-versioned execution ownership declaration'}]}))
            (target/'contracts'/'ontology.json').write_text(json.dumps({
                'schema':'cora-ontology/1',
                'products':[{'id':'project_edu','roots':['host'],
                             'entrypoints':['host/edu.mjs']}],
                'software':[{'id':'edu','roots':['host'],
                            'product_ids':['project_edu']}]}))
            git(target,'init','-q');git(target,'config','user.name','Audit')
            git(target,'config','user.email','audit@example.invalid')
            git(target,'add','.');git(target,'commit','-qm','source objects')
            rev=git(target,'rev-parse','HEAD')
            profile=root/'profile.json'
            base={'schema':'cora-portable-target/3','target_repo':'example/edu',
                  'revision':rev,'owners':[{'id':'edu-owner','path':'host/edu.mjs'}],
                  'witnesses':[],'method_links':[],
                  'source_manifests':{'artifact_roles':'contracts/roles.json',
                                      'ontology':'contracts/ontology.json'}}
            profile.write_text(json.dumps(base))
            receipt=run_portable(target,rev,profile)
            methods={x['method']:x for x in receipt['source_process']['results']}
            self.assertEqual(receipt['source_process']['status'],'PASS_SCOPED_WITH_UNVERIFIED_GAPS')
            self.assertEqual(receipt['source_status'],'PASS_SCOPED_GIT_SOURCE_ONLY')
            for m in ('artifact_roles','python_candidate_graph'):
                self.assertEqual(methods[m]['status'],'REUSED_SCOPED_FROM_HOLISTIC')
                self.assertTrue(methods[m]['source_digest'])
            self.assertTrue(verify_portable(target,receipt,profile))
            self.assertEqual(receipt['authorization'],'NONE')
            self.assertEqual(receipt['behavior_status'],'BLOCKED_EXTERNAL')
            broken=json.loads(json.dumps(base));broken['source_manifests']['ontology']='contracts/missing.json'
            profile.write_text(json.dumps(broken))
            missing=run_portable(target,rev,profile)
            self.assertEqual(missing['source_process']['status'],'SOURCE_PARTIAL_NOT_CONFIGURED')
            self.assertEqual(next(x['status'] for x in missing['source_process']['results']
                                 if x['method']=='python_candidate_graph'),'NOT_CONFIGURED')
            with self.assertRaises(ValueError):verify_portable(target,receipt,profile)
            broken['source_manifests']['ontology']='../escape.json'
            profile.write_text(json.dumps(broken))
            with self.assertRaises(ValueError):run_portable(target,rev,profile)
            profile.write_text(json.dumps(base))
            (target/'contracts'/'roles.json').write_text('{"tampered":true}')
            self.assertTrue(verify_portable(target,receipt,profile))  # Git, not worktree
            old=dict(base,schema='cora-portable-target/1')
            old.pop('source_manifests');profile.write_text(json.dumps(old))
            legacy=run_portable(target,rev,profile)
            self.assertEqual(legacy['source_process']['status'],'SOURCE_PARTIAL_NOT_CONFIGURED')

if __name__=='__main__':
    unittest.main()
