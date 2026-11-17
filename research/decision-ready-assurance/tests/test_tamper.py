#!/usr/bin/env python3
"""Physical adversarial research-bundle mutations, never to canonical inputs."""
import tempfile,shutil,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from verify_release import problems
R=Path(__file__).resolve().parents[1]
variants=[
 ('human','real_human_participants',1),
 ('pretest','actual_skill_pretests',1),
 ('posttest','actual_skill_posttests',1),
 ('savings','billed_compute_savings_observed',True),
 ('sample','public_pr_events',12),
 ('unobserved','dossier_unobserved_slots',0),
 ('fixtures','matched_fixture_equal',15),
 ('briefings','briefings',48),
 ('units','local_si11a_unit_tests',1000),
 ('synthetic','synthetic_full_card_points',0),
 ('workflows','github_workflow_file_inventory',{'cora':100000}),
 ('contraction','ikant_pr249_added_lines',100),
 ('negative','ictc_local_unknown_required_grade_counterexample',False)
]
with tempfile.TemporaryDirectory() as td:
 q=Path(td)/'research';q.mkdir()
 files=['MANUSCRIPT.markdown','ROADMAP.markdown','CLAIM_LEDGER.json','evidence/FACTS.json','evidence/RETROSPECTIVE_11_CASES.json','evidence/REFERENCES.json','evidence/ARCHIVE_REGISTER.json']
 for f in files:
  p=q/f;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/f,p)
 assert not problems(q),'baseline integrity failed'
 caught=0
 for name,key,value in variants:
  p=q/'evidence/FACTS.json';x=json.loads(p.read_text());x['observations'][key]=value;p.write_text(json.dumps(x,indent=2))
  found=bool(problems(q));caught+=found
  if not found:print('SURVIVOR',name)
  shutil.copy2(R/'evidence/FACTS.json',p)
 p=q/'CLAIM_LEDGER.json';x=json.loads(p.read_text());x['claims'][9]['status']='SUPPORTED';p.write_text(json.dumps(x));caught+=bool(problems(q));shutil.copy2(R/'CLAIM_LEDGER.json',p)
 p=q/'MANUSCRIPT.markdown';s=p.read_text();p.write_text(s.replace('70 unobserved','70 proven failures'));caught+=bool(problems(q));shutil.copy2(R/'MANUSCRIPT.markdown',p)
 p=q/'evidence/RETROSPECTIVE_11_CASES.json';p.unlink();caught+=bool(problems(q))
 expected=len(variants)+3;print(json.dumps({'physical_mutations':expected,'detected':caught,'survivors':expected-caught}))
 sys.exit(caught!=expected)
