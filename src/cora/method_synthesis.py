"""Read-only source-bound synthesis, not a new scanner or AI authority."""
from __future__ import annotations

import ast
import json
from pathlib import Path
from .artifact_roles import artifact_audit, verify_artifact_report
from .workflow_rationalization import audit_workflows, verify_workflows
from .process_suite import process_catalog, verify_suite
from .ontology import committed_ontology, members
from .git_snapshot import git
from .reticulum import MODEL, BLOCKED, REFUTED, assess_cut, ordered_cut
from .evidence import domain_hash

SCHEMA = 'cora-method-synthesis/1'
HYPOTHESES = 'cora-method-hypotheses/1'


def _committed_json(repo, sha, path):
    data = json.loads(git(repo, 'show', sha + ':' + path,
                          max_output=128 * 1024).decode('utf-8'))
    if not isinstance(data, dict):
        raise ValueError('invalid synthesis contract')
    return data


def _validate_atlas(repo, sha, paths):
    atlas = _committed_json(repo, sha, '.cora/contracts/profiles/method-atlas.json')
    if (set(atlas) != {'schema','product','software','references','procedures','authority'}
            or atlas['schema'] != 'cora-method-atlas/1' or atlas['authority'] != 'NONE'):
        raise ValueError('method atlas contract invalid')
    ontology = committed_ontology(repo, sha)['document']
    if atlas['product'] not in {p['id'] for p in ontology['products']} or (
        set(atlas['software']) != {s['id'] for s in ontology['software']}):
        raise ValueError('product/software identity mismatch')
    if (not isinstance(atlas['references'], list) or len(atlas['references']) != 9
            or len(set(atlas['references'])) != 9):
        raise ValueError('nine method references required')
    if not isinstance(atlas['procedures'], list) or not 10 <= len(atlas['procedures']) <= 64:
        raise ValueError('procedure inventory invalid')
    cli = ast.parse(git(repo, 'show', sha + ':src/cora/cli.py',
                        max_output=512 * 1024).decode('utf-8'))
    commands = {x.args[0].value for x in ast.walk(cli)
                if isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute)
                and x.func.attr == 'add_parser' and x.args
                and isinstance(x.args[0], ast.Constant)
                and isinstance(x.args[0].value, str)}
    seen, mapped = set(), set()
    for p in atlas['procedures']:
        if (not isinstance(p, dict)
                or set(p) != {'id','cli','source','scope','standards'}
                or not isinstance(p['id'], str) or not p['id'] or p['id'] in seen
                or p['source'] not in paths
                or p['scope'] != 'CANDIDATE_PROCEDURE_NOT_ATTESTATION'):
            raise ValueError('method binding invalid')
        if (not isinstance(p['standards'], list) or not p['standards']
                or len(p['standards']) != len(set(p['standards']))
                or any(x not in atlas['references'] for x in p['standards'])):
            raise ValueError('method reference binding invalid')
        mapped.update(p['standards'])
        if p['cli'] is not None and p['cli'] not in commands:
            raise ValueError('method command missing from committed CLI')
        seen.add(p['id'])
    if mapped != set(atlas['references']):
        raise ValueError('unmapped reference method')
    dod = _committed_json(repo, sha, '.cora/contracts/dod/method-synthesis-dod.json')
    if (set(dod) != {'schema','nodes','authority','external_status'}
            or dod['schema'] != 'cora-method-synthesis-dod/1'
            or dod['authority'] != 'NONE'
            or dod['external_status'] != 'BLOCKED_EXTERNAL'):
        raise ValueError('method DoD contract invalid')
    if len(ordered_cut(dod['nodes'], 'G_GOVERNED')) != 16:
        raise ValueError('method DoD closure invalid')
    if any(n['scope'] != 'EXTERNAL' for n in dod['nodes']
           if n['id'].startswith('E0')):
        raise ValueError('external DoD promoted')
    return atlas, dod, ontology


def _bind(repo, sha, artifacts, workflows, process):
    if artifacts is None:
        artifacts = artifact_audit(repo, sha)
    else:
        verify_artifact_report(repo, artifacts)
    if workflows is None:
        workflows = audit_workflows(repo, sha)
    else:
        verify_workflows(repo, workflows)
    if process is not None:
        verify_suite(repo, process)
    if (artifacts['commit'] != sha or workflows['commit'] != sha
            or process is not None and process['commit'] != sha):
        raise ValueError('cross-commit receipt rejected')
    return artifacts, workflows, process


def _ground_hypotheses(data, sha, valid):
    if data is None:
        return []
    if (not isinstance(data, dict)
            or set(data) != {'schema','commit','items'}
            or data['schema'] != HYPOTHESES or data['commit'] != sha
            or not isinstance(data['items'], list) or len(data['items']) > 32):
        raise ValueError('invalid AI hypothesis envelope')
    result, ids = [], set()
    for h in data['items']:
        if not isinstance(h, dict) or set(h) != {
                'id','statement','evidence_refs','counter_refs','action'}:
            raise ValueError('invalid AI hypothesis')
        if (not isinstance(h['id'], str) or not h['id'].isascii()
                or not h['id'].isalnum() or h['id'] in ids
                or not isinstance(h['statement'], str)
                or not 8 <= len(h['statement']) <= 800
                or h['action'] not in ('INVESTIGATE','RETAIN','REVIEW_ADJUST')
                or any(not isinstance(h[k], list) or len(h[k]) > 32
                       or any(not isinstance(x, str) for x in h[k])
                       or len(h[k]) != len(set(h[k]))
                       for k in ('evidence_refs','counter_refs'))):
            raise ValueError('unsafe or unbounded AI claim')
        if (not h['evidence_refs'] or
                any(x not in valid for x in h['evidence_refs'] + h['counter_refs'])):
            raise ValueError('ungrounded AI claim or counterevidence')
        ids.add(h['id'])
        result.append({'id':h['id'],'claim':h['statement'],'action':h['action'],
                       'evidence_refs':h['evidence_refs'],
                       'counter_refs':h['counter_refs'],
                       'state':'UNVERIFIED_AI_HYPOTHESIS','authority':'NONE'})
    return result


def synthesize(repo: Path, revision='HEAD', *, artifacts=None, workflows=None,
               process=None, hypotheses=None):
    repo = Path(repo).resolve(strict=True)
    if not isinstance(revision, str) or not revision or revision.startswith('-') or '\0' in revision:
        raise ValueError('invalid revision')
    sha = git(repo, 'rev-parse', '--verify', '--end-of-options',
              revision + '^{commit}', max_output=128).decode('ascii').strip()
    artifacts, workflows, process = _bind(repo, sha, artifacts, workflows, process)
    rows = {x['path']:x for x in artifacts['artifacts']}
    if len(rows) != len(artifacts['artifacts']):
        raise ValueError('duplicate artifact')
    atlas, dod, ontology = _validate_atlas(repo, sha, set(rows))
    assigned = {x['id']:[] for x in ontology['software']}
    for method in atlas['procedures']:
        for s in ontology['software']:
            if members(method['source'], s['roots']):
                assigned[s['id']].append(method['id'])
    if any(not any(p['id'] in v for v in assigned.values())
           for p in atlas['procedures']):
        raise ValueError('method unbound to software source')
    findings = []
    refs = {'procedure:' + x['id'] for x in atlas['procedures']}
    for wf in workflows['workflows']:
        path = wf['path']
        refs.add('workflow:' + path)
        if path not in rows or 'WORKFLOW' not in rows[path]['roles']:
            findings.append({'id':'ROLE_MISMATCH','subject':path,
                             'state':'SOURCE_CONTRADICTION'})
        if wf['in_repo_callers'] or wf['other_literal_references']:
            findings.append({'id':'WORKFLOW_CONSUMER','subject':path,
                             'state':'OBSERVED_SOURCE_RELATION'})
        if wf['disposition'] != 'RETAIN_UNTIL_CONSUMER_REVIEW':
            findings.append({'id':'WORKFLOW_REVIEW_CANDIDATE','subject':path,
                             'state':'INFERRED_REVIEW_ONLY'})
    for p in atlas['procedures']:
        path = p['source']
        if path.startswith('src/') and 'SOFTWARE_SOURCE' not in rows[path]['roles']:
            findings.append({'id':'PROCEDURE_ROLE_GAP','subject':path,
                             'state':'SOURCE_CONTRADICTION'})
    if process is not None:
        for item in process['results']:
            if item['status'] in ('DEBT_BLOCKED','NOT_RUN_REQUIRES_FOCUS'):
                findings.append({'id':'PROCESS_EVIDENCE_GAP','subject':item['method'],
                                 'state':'OBSERVED_SOURCE_GAP'})
    valid = refs | {'artifact:' + x for x in rows}
    ai = _ground_hypotheses(hypotheses, sha, valid)
    # These are finite source predicates, NOT test execution receipts.
    # L7 always needs independently observed test results. Contradiction
    # propagates through the canonical AND lattice rather than being hidden.
    model = {'L'+str(n):MODEL for n in range(1,7)}
    model['L7'] = BLOCKED
    if any(row['state'] == 'SOURCE_CONTRADICTION' for row in findings):
        model['L4'] = REFUTED
    elif workflows['source_status'] != 'PASS_SCOPED_SOURCE':
        model['L4'] = BLOCKED
    if process is not None and process['status'] == 'DEBT_BLOCKED':
        model['L5'] = BLOCKED
    assessment = assess_cut(dod['nodes'], 'G_GOVERNED', model)
    report = {'schema':SCHEMA,'commit':sha,'source_status':'SOURCE_JOIN_REPLAYED_NARROW',
              'product_id':atlas['product'],'software_methods':assigned,
              'reference_count':len(atlas['references']),
              'method_reference_edges':sorted([{'procedure':p['id'],'method':ref}
                   for p in atlas['procedures'] for ref in p['standards']],
                   key=lambda x:(x['procedure'],x['method'])),
              'procedure_count':len(atlas['procedures']),
              'workflow_count':workflows['workflow_count'],
              'method_catalog':process_catalog()['processes'],
              'receipt_sources':{'artifact':artifacts['report_digest'],
                                 'workflow':workflows['receipt_sha256'],
                                 'process':process['run_digest'] if process else None},
              'process_state':process['status'] if process else 'NOT_SUPPLIED',
              'findings':sorted(findings,key=lambda x:(x['id'],x['subject'])),
              'ai_hypotheses':ai,
              'external_gaps':['HUMAN_USABILITY_UNKNOWN','REAL_TARGET_RUNTIME_UNKNOWN',
                               'HOST_REVIEW_POLICY_UNKNOWN','POSTMERGE_OUTCOME_UNKNOWN'],
              'source_model':assessment['states']['G_SOURCE'],
              'governed_model':assessment['status'],
              'interpretation':'CORRELATION_NOT_CAUSALITY_OR_CORRECTNESS',
              'authorization':'NONE'}
    report['receipt_digest'] = domain_hash('CORA:method-synthesis:1',report)
    return report


def verify_synthesis(repo, report, *, artifacts=None, workflows=None,
                     process=None, hypotheses=None):
    if not isinstance(report,dict) or report.get('schema') != SCHEMA:
        raise ValueError('invalid synthesis report')
    rebuilt = synthesize(repo,report['commit'],artifacts=artifacts,
                         workflows=workflows,process=process,hypotheses=hypotheses)
    if rebuilt != report:
        raise ValueError('synthesis proof replay mismatch')
    return True


def analyst_request(report):
    if not isinstance(report,dict) or report.get('schema') != SCHEMA:
        raise ValueError('invalid case')
    return {'schema':'cora-method-analyst-request/1',
            'source_commit':report['commit'],'receipt_digest':report['receipt_digest'],
            'questions':['Which claims are source-supported?',
                         'What counterexample could invalidate each proposed relation?',
                         'Which method overlaps are shared inputs rather than equivalent outcomes?',
                         'Which unknowns require actual independent operator evidence?'],
            'evidence_counts':{'findings':len(report['findings']),
                               'hypotheses':len(report['ai_hypotheses'])},
            'source_bytes_embedded':False,'output_authority':'NONE'}
