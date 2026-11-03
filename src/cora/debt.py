"""Read-only, multi-scale technical-debt *signals* with Git source replay.

Debt is an investigation label; not a measured cost, defect, or delete licence.
External SARIF is a caller assertion, never a trusted scanner attestation.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

from .evidence import domain_hash, valid_path
from .git_snapshot import snapshot, git
from .archaeology import mine_history
from .holistic import holistic_audit

SCHEMA = 'cora-debt-ledger/1'
MAX_SOURCE = 512 * 1024
MAX_SARIF = 4 * 1024 * 1024
TAXONOMY = {
    'CODE_COMPLEXITY': ('REFACTOR_WITH_CHARACTERIZATION_TESTS', 'ENGINEERING_OWNER'),
    'CHANGE_PRESSURE': ('INVESTIGATE_HOTSPOT_AND_CHANGE_HISTORY', 'ENGINEERING_OWNER'),
    'TEST_EVIDENCE': ('MEASURE_COVERAGE_ON_SUPPORTED_TARGETS', 'QA_OWNER'),
    'ARCHITECTURE_COUPLING': ('REVIEW_BOUNDARY_AND_CHANGE_COORDINATION', 'ARCHITECT'),
    'DEPENDENCY_RESOLUTION': ('RESOLVE_LOCKFILE_AND_BUILD_CONTEXT', 'BUILD_OWNER'),
    'DOCUMENTATION_CONTRACT': ('RECONCILE_DECLARATIONS_AND_REVIEW', 'PRODUCT_OWNER'),
    'BUILD_RELEASE': ('REPRODUCE_RELEASE_WITH_PINNED_BUILD', 'RELEASE_OWNER'),
    'SECURITY_FINDING': ('VERIFY_ALERT_WITH_TRUSTED_SCANNER_AND_TRIAGE', 'SECURITY_OWNER'),
    'GOVERNANCE_PROCESS': ('REVIEW_INDEPENDENT_CHECKS_AND_APPROVALS', 'MAINTAINER'),
    'EVIDENCE_COVERAGE': ('COLLECT_MISSING_EVIDENCE_AND_RESCAN', 'ENGINEERING_OWNER'),
}
BANDS = ('P1_REVIEW', 'P2_INVESTIGATE', 'P3_MONITOR')


def parse_sarif(raw: bytes, paths: set[str]) -> dict:
    """Strict, bounded SARIF 2.1 subset. Never execute scanner or trust results."""
    if not isinstance(raw, bytes) or len(raw) > MAX_SARIF:
        raise ValueError('SARIF must be bytes <= 4MiB')
    try:
        doc = json.loads(raw.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError('SARIF invalid JSON/UTF-8') from exc
    if not isinstance(doc, dict) or doc.get('version') != '2.1.0' or not isinstance(doc.get('runs'), list) or len(doc['runs']) > 8:
        raise ValueError('invalid or unsupported SARIF 2.1.0 runs')
    rows = []
    unknown = []
    for run_no, run in enumerate(doc['runs']):
        if not isinstance(run, dict) or not isinstance(run.get('results', []), list) or len(run['results']) > 5000:
            raise ValueError('SARIF run/results invalid or exceeds local limit')
        tool = run.get('tool')
        if not isinstance(tool,dict) or not isinstance(tool.get('driver'),dict):
            raise ValueError('SARIF tool.driver object required')
        driver = tool['driver']
        name = driver.get('name')
        if not isinstance(name, str) or not 1 <= len(name) <= 100:
            raise ValueError('SARIF tool identity required')
        for index, result in enumerate(run['results']):
            if not isinstance(result, dict) or not isinstance(result.get('message'),dict) or not isinstance(result['message'].get('text'),str):
                raise ValueError('SARIF result requires message.text')
            locations = result.get('locations', [])
            if not isinstance(locations, list) or len(locations) > 8:
                raise ValueError('SARIF result location limit')
            rules = result.get('ruleId', 'unknown')
            if not isinstance(rules, str) or len(rules) > 160:
                raise ValueError('SARIF ruleId invalid')
            level = result.get('level', 'warning')
            if level not in ('error', 'warning', 'note', 'none'):
                raise ValueError('SARIF level invalid')
            if not locations:
                unknown.append('SARIF_RESULT_WITHOUT_LOCATION:'+str(run_no)+':'+str(index))
                continue
            first = locations[0]
            try:
                uri = first['physicalLocation']['artifactLocation']['uri']
            except (KeyError, TypeError):
                unknown.append('SARIF_LOCATION_NOT_LOCAL:'+str(run_no)+':'+str(index))
                continue
            if not isinstance(uri, str) or '%' in uri:
                raise ValueError('unsafe/undecodable SARIF uri')
            u = urlsplit(uri)
            path = unquote(u.path)
            if u.scheme or u.netloc or u.query or u.fragment or not valid_path(path):
                raise ValueError('external, absolute or traversal SARIF path rejected')
            if path not in paths:
                unknown.append('SARIF_PATH_NOT_IN_COMMIT:'+path)
                continue
            physical = first.get('physicalLocation') if isinstance(first,dict) else None
            if not isinstance(physical,dict):
                raise ValueError('SARIF physicalLocation object required')
            region = physical.get('region', {})
            if not isinstance(region,dict):
                raise ValueError('SARIF region must be object')
            line = region.get('startLine', 0)
            if type(line) is not int or not 0 <= line <= 1_000_000:
                raise ValueError('invalid SARIF source location')
            rows.append({'path':path,'tool':name,'rule':rules,'line':line,'level':level,
                         'message':result['message']['text'][:200],
                         'provenance':'EXTERNAL_UNVERIFIED'})
    return {'input_sha256':hashlib.sha256(raw).hexdigest(), 'rows':sorted(rows,key=lambda v:(v['path'],v['tool'],v['rule'],v['line'],v['message'])),
            'unknown':sorted(set(unknown)), 'trust':'CALLER_SUPPLIED_SARIF_UNAUTHENTICATED'}


def _py_metrics(raw: bytes) -> dict:
    text = raw.decode('utf-8')
    tree = ast.parse(text)
    # AST points approximate decision structure, NOT McCabe standard complexity.
    branches = sum(isinstance(n,(ast.If,ast.IfExp,ast.For,ast.AsyncFor,ast.While,ast.Try,ast.ExceptHandler,ast.Match,ast.BoolOp)) for n in ast.walk(tree))
    max_depth = 0
    stack = [(tree,0)]
    while stack:
        node,depth = stack.pop()
        if isinstance(node,(ast.If,ast.For,ast.AsyncFor,ast.While,ast.Try,ast.Match)):
            depth += 1
        max_depth=max(max_depth,depth)
        if depth <= 80:
            stack.extend((x,depth) for x in ast.iter_child_nodes(node))
    return {'lines':len(text.splitlines()), 'ast_decision_nodes':branches,'max_control_nesting':max_depth}


def debt_scan(repo: Path, revision: str='HEAD', *, max_commits: int=64,
              sarif_bytes: bytes | None=None, _holistic_report: dict|None=None) -> dict:
    """Bounded Git-only signals plus optional explicitly untrusted external SARIF."""
    repo=Path(repo).resolve(strict=True)
    ledger=snapshot(repo,revision)
    sha=ledger['commit']
    if _holistic_report is not None:
        if _holistic_report.get('commit') != sha or _holistic_report.get('history',{}).get('bounded_commits') != max_commits:
            raise ValueError('cached holistic evidence is not scoped to commit/history limit')
        holistic = _holistic_report
    else:
        holistic=holistic_audit(repo,sha,max_commits=max_commits)
    history=holistic["history"]  # Reuse source-bound history; do not re-mine same Git commit.
    records={r['path']:r for r in ledger['records']}
    findings=[]
    debt_unknown=[]
    counts=Counter()
    counts['python_ast_candidates']=sum(p.endswith('.py') for p in records)
    def add(path:str, kind:str, rule:str, priority:str, evidence:str, rationale:str,
            strength:str='SOURCE_OBSERVED', location:int=0):
        if kind not in TAXONOMY or priority not in BANDS:
            raise ValueError('internal debt taxonomy violation')
        uid=domain_hash('CORA:debt-identity:1',{'path':path,'kind':kind,'rule':rule,'location':location})
        action,owner=TAXONOMY[kind]
        findings.append({'id':uid, 'path':path,'kind':kind,'rule':rule,
                         'priority':priority,'evidence_strength':strength,'evidence':evidence,
                         'rationale':rationale,'remediation':action,'human_owner_role':owner,
                         'verification_plan':'BASELINE_TEST_AND_RERUN_RELEVANT_ANALYZER',
                         'status':'HUMAN_TRIAGE_REQUIRED','authorized_action':'NONE'})
    for path, rec in records.items():
        if rec['status']!='observed_git_blob':
            debt_unknown.append('UNRESOLVED_GIT_OBJECT:'+path)
            continue
        if not path.endswith('.py') or rec['size'] is None:
            continue
        if rec['size']>MAX_SOURCE:
            debt_unknown.append('PYTHON_AST_BUDGET_EXCEEDED:'+path)
            continue
        raw=git(repo,'cat-file','blob',rec['git_oid'],max_output=MAX_SOURCE)
        try:metrics=_py_metrics(raw)
        except (SyntaxError,UnicodeDecodeError,RecursionError,ValueError):
            debt_unknown.append('PYTHON_AST_UNAVAILABLE:'+path)
            continue
        counts['python_ast_inspected']+=1
        touched=len(history['touched_commits'].get(path,[]))
        if metrics['ast_decision_nodes'] >= 20 or metrics['max_control_nesting'] >= 6:
            add(path,'CODE_COMPLEXITY','PY_AST_STRUCTURAL_COMPLEXITY','P1_REVIEW' if touched>=4 else 'P2_INVESTIGATE',
                rec['digest']+':AST:'+str(metrics),
                'AST decision/nesting heuristic above configured threshold; not proof of defects')
        if metrics['lines'] >= 500:
            add(path,'CODE_COMPLEXITY','PY_MODULE_SIZE_HEURISTIC','P2_INVESTIGATE',rec['digest']+':lines:'+str(metrics['lines']),
                'Large Python module may need decomposition, subject to contract tests')
        if touched>=5:
            add(path,'CHANGE_PRESSURE','GIT_FREQUENT_CHANGES','P2_INVESTIGATE',
                history['digest']+':touches:'+str(touched),'Observed frequent modifications; not automatically debt')
    # Multi-level: use the same pinned repository, role/ontology and temporal group
    # evidence. These are hypotheses about coordination, not proven defects.
    for entry in holistic['files']:
        path=entry['path']
        if 'ROLE_DECLARATION_MISSING' in entry['review_flags']:
            add(path,'EVIDENCE_COVERAGE','ROLE_COVERAGE_MISSING','P3_MONITOR',
                holistic['report_digest']+':'+entry['blob_record_digest'],
                'No owner-declared role; provenance exists, role and runtime not inferred')
        if 'PRODUCT_BOUNDARY_AMBIGUOUS' in entry['review_flags']:
            add(path,'ARCHITECTURE_COUPLING','MULTI_OWNER_BOUNDARY','P1_REVIEW',
                holistic['report_digest']+':'+entry['blob_record_digest'],
                'More than one declared product owns this path; requires architectural review')
    for edge in holistic['temporal_edges']:
        if edge['cross_product_boundary'] and edge['cochanged_commits']>=2:
            add(edge['a'],'ARCHITECTURE_COUPLING',
                'CROSS_PRODUCT_COCHANGE:'+edge['b'],'P2_INVESTIGATE',
                holistic['history_digest']+':'+str(edge['cochanged_commits']),
                'Temporal cochange across declared products, NOT evidence of runtime import')
    if holistic['blockers']:
        debt_unknown.extend('HOLISTIC_METHOD_UNAVAILABLE:'+e['method'] for e in holistic['blockers'])
    debt_unknown.extend(['GOVERNANCE_REQUIRED_CHECKS_NOT_ATTESTED','RUNTIME_TEST_COVERAGE_NOT_ATTESTED'])
    if history['history_truncated']:
        debt_unknown.append('TRUNCATED_GIT_HISTORY_COUNTS_ARE_LOWER_BOUNDS')
    sarif=parse_sarif(sarif_bytes,set(records)) if sarif_bytes is not None else None
    if sarif:
        debt_unknown.extend(sarif['unknown'])
        for x in sarif['rows']:
            kind='SECURITY_FINDING' if re.search(r'(security|cwe-\d+)',x['rule'],re.I) else 'CODE_COMPLEXITY'
            add(x['path'],kind,'EXTERNAL_SARIF:'+x['tool']+':'+x['rule'],
                'P1_REVIEW' if x['level']=='error' else 'P2_INVESTIGATE',
                sarif['input_sha256']+':'+x['path']+':'+str(x['line']),
                'Untrusted SARIF scanner assertion; validate scanner configuration and actual fault',
                'EXTERNAL_UNVERIFIED',x['line'])
    else:
        debt_unknown.append('NO_EXTERNAL_STATIC_SCANNER_RESULT')
    findings.sort(key=lambda r:(r['path'],r['kind'],r['rule'],r['id']))
    if len({f['id'] for f in findings})!=len(findings):
        raise ValueError('duplicate debt identity; ambiguous scanner results')
    by_kind=Counter(f['kind'] for f in findings)
    by_priority=Counter(f['priority'] for f in findings)
    coverage={'git_tree':'COMMITTED_OBSERVED','history':'BOUNDED_TRUNCATED' if history['history_truncated'] else 'BOUNDED_COMPLETE',
              'python_ast':'PARTIAL_HEURISTIC', 'sarif':'EXTERNAL_UNVERIFIED' if sarif else 'NOT_SUPPLIED',
              'runtime':'NOT_OBSERVED','cross_language_dataflow':'NOT_EXECUTED',
              'product_impact':'NOT_CALIBRATED','human_cost_estimate':'NOT_MEASURED',
              'architecture_ownership':'DECLARED_PARTIAL','artifact_roles':'DECLARED_NOT_RUNTIME_PROVEN',
              'change_coupling':'HISTORICAL_NOT_RUNTIME_EDGE'}
    report={'schema':SCHEMA,'commit':sha,'ledger_digest':ledger['ledger_digest'],
            'history_digest':history['digest'],'holistic_digest':holistic['report_digest'],'history_limit':max_commits,
            'findings':findings,'metrics':{'git_artifacts':len(records),
               'python_ast_inspected':counts['python_ast_inspected'],
               'python_ast_candidates':counts['python_ast_candidates'],
               'python_ast_coverage_fraction':round(counts['python_ast_inspected']/counts['python_ast_candidates'],4) if counts['python_ast_candidates'] else None,
               'findings':len(findings),'by_kind':dict(sorted(by_kind.items())),
               'by_priority':dict(sorted(by_priority.items())),
               'unresolved_obligations':len(set(debt_unknown))},
            'unresolved':sorted(set(debt_unknown)),'coverage':coverage,
            'external_sarif':sarif,
            'semantics':'SIGNALS_NOT_PROVEN_DEFECTS_OR_MEASURED_FINANCIAL_DEBT',
            'authorization':'HUMAN_TRIAGE_ONLY_NO_AUTOMATED_REMEDIATION'}
    report['report_digest']=domain_hash('CORA:debt-ledger:1',report)
    return report


def verify_debt(repo:Path, report:dict, *, sarif_bytes:bytes|None=None)->bool:
    if not isinstance(report,dict) or report.get('schema')!=SCHEMA:
        raise ValueError('invalid debt report')
    if report.get('report_digest')!=domain_hash('CORA:debt-ledger:1',{k:v for k,v in report.items() if k!='report_digest'}):
        raise ValueError('debt report digest altered')
    if (report.get('external_sarif') is not None) != (sarif_bytes is not None):
        raise ValueError('external SARIF bytes required for replay')
    if debt_scan(repo,report['commit'],max_commits=report['history_limit'],sarif_bytes=sarif_bytes)!=report:
        raise ValueError('debt report differs from Git and supplied external input')
    return True


def compare_debt(repo:Path, base:str, head:str, *, max_commits:int=64)->dict:
    before=debt_scan(repo,base,max_commits=max_commits)
    after=debt_scan(repo,head,max_commits=max_commits)
    old={f['id']:f for f in before['findings']}
    new={f['id']:f for f in after['findings']}
    # A baseline with different coverage/historical truncation cannot prove resolution.
    comparable=(before['coverage']==after['coverage'] and before['history_limit']==after['history_limit']
                and before['coverage']['history']=='BOUNDED_COMPLETE'
                and after['coverage']['history']=='BOUNDED_COMPLETE')
    report={'schema':'cora-debt-trend/1','base_commit':before['commit'],'head_commit':after['commit'],
      'base_report_digest':before['report_digest'],'head_report_digest':after['report_digest'],
      'new':sorted(set(new)-set(old)),'persisting':sorted(set(new)&set(old)),
      'not_observed_in_head':sorted(set(old)-set(new)),
      'resolution_claim':'NOT_PROVEN_ONLY_DETECTION_DELTA',
      'coverage_comparable_for_supported_signals':comparable,
      'external_runtime_consumer_comparable':False,
      'human_action':'REVIEW_NEW_AND_MISSING_SIGNALS_WITH_OWNERS',
      'authorized_action':'NONE'}
    report['trend_digest']=domain_hash('CORA:debt-trend:1',report)
    return report
