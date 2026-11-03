"""Untrusted AI/human group hypotheses as a strictly separate forensic overlay."""
from __future__ import annotations
from pathlib import Path
from .evidence import domain_hash
from .holistic import verify_holistic

SCHEMA = 'cora-group-hypotheses/1'
ACTIONS = frozenset({'RETAIN','INVESTIGATE','POSSIBLE_SCAFFOLD','POSSIBLE_GOLD','PROPOSE_ARCHIVE','PROPOSE_QUARANTINE','PROPOSE_RENAME'})


def annotate_groups(repo: Path, report:dict, hypothesis:dict) -> dict:
    """Check grounded references, NEVER establish that the AI inference is correct."""
    verify_holistic(repo,report)
    if not isinstance(hypothesis,dict) or set(hypothesis) != {'schema','report_digest','hypotheses'} or hypothesis.get('schema') != SCHEMA or hypothesis.get('report_digest') != report['report_digest']:
        raise ValueError('AI hypothesis subject/schema mismatch')
    if not isinstance(hypothesis['hypotheses'],list) or len(hypothesis['hypotheses'])>64:
        raise ValueError('AI hypothesis count invalid')
    groups={g['id']:g for g in report['development_groups']}
    commits={e['commit'] for e in report['history']['events']}
    files={f['path'] for f in report['files']}
    valid_refs={'file:'+p for p in files} | {'commit:'+c for c in commits}
    results=[]
    for h in hypothesis['hypotheses']:
        if not isinstance(h,dict) or set(h)!={'group_id','hypothesis','action','evidence_refs','counterevidence','confidence_range'}:
            raise ValueError('invalid group hypothesis fields')
        if h['group_id'] not in groups or h['action'] not in ACTIONS or not isinstance(h['hypothesis'],str) or not 8 <= len(h['hypothesis']) <= 1200:
            raise ValueError('invalid group hypothesis subject/action')
        if not isinstance(h['evidence_refs'],list) or not isinstance(h['counterevidence'],list) or len(h['evidence_refs'])>64 or len(h['counterevidence'])>32 or any(not isinstance(x,str) for x in h['evidence_refs']+h['counterevidence']):
            raise ValueError('invalid group evidence/counterevidence')
        if not isinstance(h['confidence_range'],list) or len(h['confidence_range'])!=2 or any(type(x) not in (int,float) or not 0<=x<=1 for x in h['confidence_range']) or h['confidence_range'][0]>h['confidence_range'][1]:
            raise ValueError('invalid uncalibrated range')
        grounded=sorted(set(h['evidence_refs']) & valid_refs)
        missing=sorted(set(h['evidence_refs']) - valid_refs)
        results.append({'group_id':h['group_id'],'hypothesis':h['hypothesis'],'proposed_action':h['action'],
                        'grounded_reference_ids':grounded,'missing_reference_ids':missing,
                        'counterevidence':h['counterevidence'],'confidence_range':h['confidence_range'],
                        'state':'UNVERIFIED_AI_HYPOTHESIS',
                        'confidence_status':'UNVALIDATED_SELF_REPORTED_NOT_STATISTICAL_CONFIDENCE',
                        'grounding_status':'REFERENCES_EXIST_NOT_CONCLUSIONS_VERIFIED' if grounded and not missing else 'INSUFFICIENT_REFERENCES',
                        'authorized_action':'NONE'})
    result={'schema':'cora-group-hypothesis-overlay/1','commit':report['commit'],
            'report_digest':report['report_digest'],'hypotheses':results,
            'effect':'ANNOTATION_ONLY_NO_ARCHIVE_QUARANTINE_RENAME_OR_DELETE'}
    result['overlay_digest']=domain_hash('CORA:group-ai:1',result)
    return result


def group_ai_request(report:dict) -> dict:
    """Portable prompt data; not a model call and not an authority grant."""
    return {'schema':'cora-group-ai-request/1','commit':report['commit'],
            'report_digest':report['report_digest'],
            'instruction':'For each development group, infer several *falsifiable* explanations. Cite existing file:/commit: ids; state unknown consumers, evidence for retention, and next counterexample probe. Never authorize deletion.',
            'groups':[{'id':g['id'],'paths':g['paths'],'roles':g['declared_roles'],'review_flags':g['review_flags']} for g in report['development_groups']],
            'confidence_range':'self_reported_uncalibrated; never interpreted as a statistical probability'}
