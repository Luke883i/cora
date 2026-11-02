"""Artifact semantics: owner declarations, multi-role lattice and Git evidence.

A filename is never itself a proof that an artifact is a test, contract, executable
or unused. Rules are explicitly reviewed declarations. The same artifact may hold
multiple roles. No role implies runtime observation or safe-to-delete authority.
"""
from __future__ import annotations
import fnmatch
import json
import re
from pathlib import Path
from .evidence import valid_path, domain_hash
from .git_snapshot import snapshot, git

SCHEMA = 'cora-artifact-roles/1'
REPORT = 'cora-artifact-report/1'
ROLES = frozenset({
    'PRODUCT_CONTRACT', 'SOFTWARE_SOURCE', 'ENTRYPOINT', 'TEST', 'CONTRACT_VERIFIER',
    'CONTRACT_SCHEMA', 'FIXTURE', 'WORKFLOW', 'POLICY', 'DOCUMENTATION', 'GOVERNANCE',
    'RELEASE_TOOL', 'BUILD_METADATA', 'ARTIFACT_INDEX', 'LICENSE', 'OBSERVABILITY',
})
MAX_MANIFEST = 256 * 1024


def validate_declarations(doc: object) -> dict:
    if not isinstance(doc, dict) or set(doc) != {'schema', 'rules'} or doc.get('schema') != SCHEMA:
        raise ValueError('artifact role manifest schema mismatch')
    rules = doc['rules']
    if not isinstance(rules, list) or not rules or len(rules) > 256:
        raise ValueError('artifact role rules count invalid')
    seen = set()
    for rule in rules:
        if not isinstance(rule, dict) or set(rule) != {'pattern', 'roles', 'rationale'}:
            raise ValueError('invalid role rule shape')
        p, roles, reason = rule['pattern'], rule['roles'], rule['rationale']
        if not isinstance(p, str) or not valid_path(p) or p.startswith('.git/') or '**' in p or '[' in p or ']' in p:
            raise ValueError('unsafe or nonportable glob rule')
        if not isinstance(roles, list) or not roles or roles != sorted(set(roles)) or any(r not in ROLES for r in roles):
            raise ValueError('invalid or duplicated declared role')
        if not isinstance(reason, str) or not 8 <= len(reason) <= 240:
            raise ValueError('role rationale required')
        if p in seen:
            raise ValueError('duplicate artifact rule pattern')
        seen.add(p)
    return doc


def committed_rules(repo: Path, commit: str, path: str = 'cora.artifact-roles.json') -> dict:
    if not valid_path(path):
        raise ValueError('unsafe role manifest path')
    raw = git(repo, 'show', f'{commit}:{path}', max_output=MAX_MANIFEST)
    if len(raw) > MAX_MANIFEST:
        raise ValueError('role manifest oversized')
    doc = json.loads(raw.decode('utf-8'))
    validate_declarations(doc)
    return {'document': doc, 'source': commit + ':' + path,
            'digest': domain_hash('CORA:artifact-roles:1', doc)}


def roles_for(path: str, rules: list[dict]) -> dict:
    matched = [r for r in rules if fnmatch.fnmatchcase(path, r['pattern'])]
    return {'roles': sorted({role for rule in matched for role in rule['roles']}),
            'rules': sorted(rule['pattern'] for rule in matched),
            'status': 'DECLARED_NOT_BEHAVIORALLY_ATTESTED' if matched else 'UNCLASSIFIED'}


def artifact_audit(repo: Path, revision: str = 'HEAD', manifest: str = 'cora.artifact-roles.json') -> dict:
    ledger = snapshot(repo, revision)
    commit = ledger['commit']
    declarations = committed_rules(repo, commit, manifest)
    doc = declarations['document']
    rows = []
    counts: dict[str, int] = {}
    for record in ledger['records']:
        assigned = roles_for(record['path'], doc['rules'])
        for role in assigned['roles']:
            counts[role] = counts.get(role, 0) + 1
        rows.append({'path': record['path'], 'git_record_digest': record['digest'],
                     'git_status': record['status'], **assigned})
    used_rules = {pattern for row in rows for pattern in row['rules']}
    stale_rules = sorted({r['pattern'] for r in doc['rules']} - used_rules)
    uncategorized = sorted(row['path'] for row in rows if not row['roles'])
    summary = {'total_tracked_artifacts':len(rows),
               'declared_artifacts':len(rows)-len(uncategorized),
               'unclassified':len(uncategorized), 'role_counts':dict(sorted(counts.items())),
               'stale_rules':stale_rules,
               'coverage': 'Git-tracked artifact declarations only; runtime, behavioral test truth and external consumers not attested'}
    result = {'schema': REPORT, 'commit':commit, 'ledger_digest':ledger['ledger_digest'],
              'manifest_digest':declarations['digest'], 'manifest_source':declarations['source'],
              'artifacts':rows, 'summary':summary,
              'decision_authority':'HUMAN_ONLY_NO_AUTOMATIC_DELETION'}
    result['report_digest'] = domain_hash('CORA:artifact-report:1', result)
    return result


def verify_artifact_report(repo: Path, report: object) -> bool:
    if not isinstance(report,dict) or report.get('schema') != REPORT:
        raise ValueError('invalid artifact report')
    if report.get('report_digest') != domain_hash('CORA:artifact-report:1', {k:v for k,v in report.items() if k!='report_digest'}):
        raise ValueError('artifact report digest altered')
    commit = report.get('commit')
    source = report.get('manifest_source')
    if not isinstance(commit,str) or not isinstance(source,str) or not source.startswith(commit + ':'):
        raise ValueError('invalid manifest provenance')
    if artifact_audit(repo,commit,source[len(commit)+1:]) != report:
        raise ValueError('artifact report differs from committed Git evidence')
    return True
