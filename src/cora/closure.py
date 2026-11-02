"""PR-05: versioned, Git-backed scoped evidence closure. No destructive authorization.

PASS_SCOPED is confined to four observational claims and NEVER means safe deletion.
Unknown evidence cannot be silently converted into proof. Certificates are locally
recomputed against the original Git objects; self-hashes are not authentication.
"""
from __future__ import annotations

from pathlib import Path
from .evidence import domain_hash, valid_path
from .git_snapshot import snapshot
from .graph import graph_from_commit
from .adapters import adapter_audit

SCHEMA = 'cora-closure-certificate/1'
CLAIMS = ('committed_blob', 'declared_product_membership', 'declared_manifest_dependency',
          'static_import_candidate', 'safe_deletion')
STATES = ('VERIFIED', 'COUNTEREXAMPLE', 'UNKNOWN', 'UNSUPPORTED')


def decide(obligations: list[dict]) -> tuple[str, list[str]]:
    """Deterministic policy, requires uniquely identified obligations and known states."""
    if not isinstance(obligations, list) or not obligations:
        raise ValueError('missing obligations')
    ids = set()
    for o in obligations:
        if (not isinstance(o, dict) or set(o) != {'id', 'state', 'evidence'}
                or not isinstance(o['id'], str) or not o['id'] or o['id'] in ids
                or o['state'] not in STATES or not isinstance(o['evidence'], str)
                or not o['evidence']):
            raise ValueError('invalid or duplicate obligation')
        ids.add(o['id'])
    counter = sorted(o['id'] for o in obligations if o['state'] == 'COUNTEREXAMPLE')
    unknown = sorted(o['id'] for o in obligations if o['state'] in ('UNKNOWN', 'UNSUPPORTED'))
    if counter:
        return 'REFUTED', counter
    if unknown:
        return 'BLOCKED', unknown
    return 'PASS_SCOPED', []


def make_certificate(claim: str, commit: str, path: str, selector: str,
                     ledger_digest: str, obligations: list[dict], evidence_sources: dict) -> dict:
    if claim not in CLAIMS or not valid_path(path) or not isinstance(selector, str):
        raise ValueError('invalid claim or subject')
    status, blocking = decide(obligations)
    if claim == 'safe_deletion' and status == 'PASS_SCOPED':
        raise ValueError('unsafe policy escalation attempted')
    data = {'schema': SCHEMA, 'claim': claim, 'commit': commit, 'path': path,
            'selector': selector, 'ledger_digest': ledger_digest,
            'sources': evidence_sources, 'obligations': sorted(obligations, key=lambda x:x['id']),
            'status': status, 'blocking': blocking,
            'effect': 'OBSERVATIONAL_ONLY',
            'caveat': 'PASS_SCOPED is NOT runtime proof or permission to delete or transform.'}
    data['certificate_digest'] = domain_hash('CORA:closure-certificate:1', data)
    return data


def closure(repo: Path, claim: str, path: str, *, selector: str = '',
            revision: str = 'HEAD', ontology_path: str = 'cora.ontology.json') -> dict:
    """Recompute all relevant evidence from immutable Git objects; no callers supply facts."""
    if claim not in CLAIMS or not valid_path(path) or not isinstance(selector, str):
        raise ValueError('invalid claim, path or selector')
    if claim in ('declared_product_membership', 'declared_manifest_dependency', 'static_import_candidate') and not selector:
        raise ValueError('selector required for claim')
    if claim == 'static_import_candidate' and not valid_path(selector):
        raise ValueError('selector target must be safe repository path')
    ledger = snapshot(repo, revision)
    commit = ledger['commit']
    files = {r['path']: r for r in ledger['records']}
    record = files.get(path)
    sources = {'ledger': ledger['ledger_digest']}
    obligations = []

    def fact(id: str, state: str, evidence: str) -> None:
        obligations.append({'id': id, 'state': state, 'evidence': evidence})

    if record is None:
        fact('git_file_present', 'COUNTEREXAMPLE', 'git-commit:'+commit+':absent:'+path)
    elif record['status'] != 'observed_git_blob':
        fact('git_file_present', 'UNKNOWN', record['digest']+':'+record['status'])
    else:
        fact('git_file_present', 'VERIFIED', record['digest'])

    if claim == 'committed_blob':
        pass
    elif claim == 'declared_product_membership':
        graph = graph_from_commit(repo, commit, ontology_path)
        sources['graph'] = graph['graph_digest']
        product_node = 'product:'+selector
        is_product = any(n['id'] == product_node for n in graph['nodes'])
        if not is_product:
            fact('declared_product_identity', 'COUNTEREXAMPLE', 'ontology:'+graph['ontology_digest']+':missing:'+selector)
        else:
            fact('declared_product_identity', 'VERIFIED', graph['ontology_digest'])
        matching = [e for e in graph['edges'] if e['source']==product_node and e['target']=='file:'+path and e['kind']=='declared_product_membership']
        if matching:
            fact('membership_edge', 'VERIFIED', matching[0]['evidence'])
        else:
            fact('membership_edge', 'UNKNOWN', graph['graph_digest']+':not-observed')
        conflicts = [f for f in graph['findings'] if f['source']=='file:'+path and f['kind']=='ambiguous_product_membership']
        fact('product_membership_unambiguous', 'UNKNOWN' if conflicts else 'VERIFIED',
             conflicts[0]['detail'] if conflicts else graph['ontology_digest'])
    elif claim == 'declared_manifest_dependency':
        adapter = adapter_audit(repo, commit)
        sources['adapter_report'] = adapter['report_digest']
        observations = [o for o in adapter['observations'] if o['path'] == path]
        if not observations:
            fact('manifest_adapter', 'UNSUPPORTED', 'no-adapter:'+path)
            fact('dependency_declared', 'UNKNOWN', 'unobserved:'+selector)
        else:
            o=observations[0]
            fact('manifest_adapter', 'VERIFIED' if o['status']=='partial' else 'UNSUPPORTED' if o['status']=='unsupported' else 'UNKNOWN', o['source_record_digest']+':'+o['adapter'])
            found = [d for d in o['dependencies'] if d['name']==selector]
            fact('dependency_declared', 'VERIFIED' if found else 'UNKNOWN',
                 o['source_record_digest']+':'+selector+(':'+'|'.join(sorted(d['constraint'] for d in found)) if found else ':not-observed'))
    elif claim == 'static_import_candidate':
        graph = graph_from_commit(repo,commit,ontology_path)
        sources['graph'] = graph['graph_digest']
        if selector not in files:
            fact('target_git_file_present','COUNTEREXAMPLE','git-commit:'+commit+':absent:'+selector)
        elif files[selector]['status'] != 'observed_git_blob':
            fact('target_git_file_present','UNKNOWN',files[selector]['digest'])
        else:
            fact('target_git_file_present','VERIFIED',files[selector]['digest'])
        matching=[e for e in graph['edges'] if e['source']=='file:'+path and e['target']=='file:'+selector and e['kind']=='static_import_candidate']
        fact('candidate_import_edge','VERIFIED' if matching else 'UNKNOWN',
             matching[0]['evidence'] if matching else graph['graph_digest']+':not-observed')
        related=[f for f in graph['findings'] if f['source']=='file:'+path and f['kind'] in ('python_parse_failed','relative_import_unresolved','ambiguous_import','dynamic_import_unknown','import_unresolved','from_import_submodule_ambiguous')]
        fact('import_resolution_nonambiguous','UNKNOWN' if related else 'VERIFIED',
             graph['graph_digest']+':'+','.join(sorted({f['kind'] for f in related})))
    else:  # safe_deletion never passes in PR-05
        for id in ('static_dependency_closure','dynamic_dependency_closure','build_and_deploy_closure',
                   'runtime_paths_closure','external_consumer_closure','legal_and_retention_obligations',
                   'security_contract_preservation','behavioral_equivalence', 'rollback_qualification'):
            fact(id, 'UNSUPPORTED', 'PR-05:no-authoritative-proof:'+id)
    return make_certificate(claim,commit,path,selector,ledger['ledger_digest'],obligations,sources)


def verify_certificate(repo: Path, certificate: dict, *, ontology_path: str = 'cora.ontology.json') -> bool:
    if not isinstance(certificate, dict) or certificate.get('schema') != SCHEMA:
        raise ValueError('invalid certificate schema')
    if certificate.get('certificate_digest') != domain_hash('CORA:closure-certificate:1', {k:v for k,v in certificate.items() if k!='certificate_digest'}):
        raise ValueError('invalid certificate digest')
    expected = closure(repo, certificate['claim'], certificate['path'], selector=certificate['selector'],
                       revision=certificate['commit'], ontology_path=ontology_path)
    if certificate != expected:
        raise ValueError('certificate differs from committed Git evidence and mandatory obligations')
    return True
