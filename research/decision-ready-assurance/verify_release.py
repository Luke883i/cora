#!/usr/bin/env python3
"""CORA MS-10 research integrity verification, read-only; never authorizes anything."""
import argparse,hashlib,json,re,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def problems(root=ROOT,archival=False):
    errors=[]
    def need(expr,code):
        if not expr: errors.append(code)
    try:
        claims=json.loads((root/'CLAIM_LEDGER.json').read_text(encoding='utf-8'))['claims']
        facts=json.loads((root/'evidence/FACTS.json').read_text(encoding='utf-8'))
        events=json.loads((root/'evidence/RETROSPECTIVE_11_CASES.json').read_text(encoding='utf-8'))['events']
        refs=json.loads((root/'evidence/REFERENCES.json').read_text(encoding='utf-8'))['refs']
        archive=json.loads((root/'evidence/ARCHIVE_REGISTER.json').read_text(encoding='utf-8'))['snapshots']
        paper=(root/'MANUSCRIPT.markdown').read_text(encoding='utf-8')
        roadmap=(root/'ROADMAP.markdown').read_text(encoding='utf-8')
    except (FileNotFoundError,ValueError,KeyError) as e:return ['MISSING_OR_MALFORMED_RESEARCH_SOURCE:'+str(e)]
    m=facts['observations'];lim=facts['measurement_limits']
    need(m['public_pr_events']==11 and len(events)==11,'RETROSPECTIVE_DENOMINATOR')
    need(len(set(x['pr_url'] for x in events))==11,'PR_DUPLICATE')
    need(len(set(x['repository'] for x in events))==5,'REPOSITORY_DENOMINATOR')
    need(all(re.fullmatch('[0-9a-f]{40}',e['pr_head_sha']) and re.fullmatch('[0-9a-f]{40}',e['pr_base_sha']) and re.fullmatch('[0-9a-f]{40}',e['merge_commit_sha']) for e in events),'PR_SHA_MISSING')
    need(all(e['test_execution']=='NOT_OBSERVED_BY_THIS_STUDY' and e['recap_dossier_limit']=='NOT_OBSERVED_DOES_NOT_MEAN_ABSENT' for e in events),'EVIDENCE_PROMOTION')
    need(m['evidence_obligation_slots']==92 and m['dossier_unobserved_slots']==70,'OBLIGATION_NUMBERS')
    need(m['matched_fixture_decisions']==16 and m['matched_fixture_equal']==16 and m['paired_compared_oracle_fields_per_evaluator']==82,'STRONG_COMPARATOR_NULL')
    need(m['strong_checklist_pr_verdict_ties']==11,'RETRO_CHECKLIST_TIE')
    need(m['briefing_formats']==4 and m['briefings']==44 and m['comprehension_questions_per_briefing']==7,'BRIEFING_COVERAGE')
    need(m['local_si11a_unit_tests']==37 and m['si11a_physical_source_mutants_detected']==17,'INSTRUMENT_FROZEN_RECEIPT')
    need(m['synthetic_briefing_cost_points_min']==52 and m['synthetic_briefing_cost_points_max']==59 and m['synthetic_full_card_points']==76,'SYNTHETIC_MODEL_NUMBERS')
    need(m['real_human_participants']==0 and m['actual_skill_pretests']==0 and m['actual_skill_posttests']==0,'FABRICATED_HUMAN_STUDY')
    need(m['billed_compute_savings_observed'] is False,'FABRICATED_COST_SAVING')
    need(sum(m['github_workflow_file_inventory'].values())==211 and len(m['github_workflow_file_inventory'])==5,'WORKFLOW_CENSUS')
    need(m['ikant_pr249_added_lines']-m['ikant_pr249_deleted_lines']==2761,'FALSE_REPOSITORY_COMPRESSION')
    need(m['teddy_v21_predates_public_cora'] is True and m['ictc_local_unknown_required_grade_counterexample'] is True,'NEGATIVE_CASE_ERASURE')
    need('NOT_MEASURED' in str(lim.get('human_understanding')) and 'NO_CAUSAL' in lim.get('CORA_effectiveness',''),'CLAIM_CEILING_LOST')
    C={c['id']:c for c in claims};need(len(C)==len(claims) and len(C)>=16,'CLAIM_REGISTER_INCOMPLETE')
    for id_ in ('C10','C11','C14','C15','C16'):
        need(id_ in C and C[id_]['status'] in ('NOT_MEASURED','NOT_DONE','UNSUPPORTED'),'CLAIM_FALSE_PROMOTION_'+id_)
    need(C['C12']['status']=='CONTRADICTED_IN_FINITE_FIXTURES' and C['C13']['status']=='FORBIDDEN','NEGATIVE_COMPARATOR_OR_AUTHORITY')
    need(len(refs)>=10 and any('3807966' in a['uri'] for a in refs),'PRIOR_ART_INCOMPLETE')
    must_have=('92','70','16','44','Storey','Soei','Git','human comprehension','rather than a claim','no human','cost')
    for term in must_have:need(term.lower() in paper.lower(),'MANUSCRIPT_MISSING_'+term.replace(' ','_'))
    need('NOT_DONE' in str(claims) and 'OPEN_EXTERNAL' in roadmap,'ROADMAP_FALSE_CLOSE')
    need(('peer review' in paper.lower() or 'peer reviewed' in paper.lower()) and 'ai-use disclosure' in paper.lower(),'EDITORIAL_DISCLOSURE_MISSING')
    need('70 proven failures' not in paper.lower() and '100 independent human participants' not in paper.lower(),'MANUSCRIPT_FALSE_PROMOTION')
    need(len(archive)==5 and len(set(x['id'] for x in archive))==5,'ARCHIVE_REGISTER_INCOMPLETE')
    for row in archive:
        need(bool(re.fullmatch('[0-9a-f]{64}',row['sha256'])) and row['bytes']>10000,'ARCHIVE_IDENTITY_MISSING')
        p=root/row['file']
        if archival:
            need(p.is_file(),'ARCHIVE_BYTES_NOT_PRESENT_'+row['id'])
            if p.is_file():
                need(p.stat().st_size==row['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],'ARCHIVE_HASH_FAIL_'+row['id'])
                try:
                    with zipfile.ZipFile(p) as z:need(z.testzip() is None,'ARCHIVE_ZIP_CORRUPT_'+row['id'])
                except (ValueError,zipfile.BadZipFile):errors.append('ARCHIVE_ZIP_INVALID_'+row['id'])
    if archival:
        doc=root/'MANUSCRIPT.docx';need(doc.is_file(),'MANUSCRIPT_DOCX_MISSING')
        if doc.is_file():
            try:
                with zipfile.ZipFile(doc) as z:
                    xml=z.read('word/document.xml').decode('utf-8')
                    need('Decision-Ready Assurance' in xml and 'AI-USE DISCLOSURE' in xml,'DOCX_CONTENT_IDENTITY')
            except (ValueError,zipfile.BadZipFile,KeyError):errors.append('DOCX_INVALID')
    return errors

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--archival',action='store_true');args=a.parse_args()
    er=problems(archival=args.archival)
    print(json.dumps({'verdict':'PASS_AUTHOR_SCOPED' if not er else 'FAIL','archival_bytes_checked':args.archival,'errors':er,'human_study':'NOT_DONE','peer_review':'NOT_DONE'},indent=2))
    sys.exit(bool(er))
