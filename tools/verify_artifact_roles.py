"""CORA v1.experimental self-audit; evaluates actual Git committed repository."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path


def verify_self(repo: Path, revision: str='HEAD') -> dict:
    from cora.artifact_roles import artifact_audit, verify_artifact_report
    from cora.graph import graph_from_commit
    from cora.ontology import committed_ontology
    from cora.git_snapshot import snapshot
    repo=repo.resolve()
    ledger=snapshot(repo,revision)
    report=artifact_audit(repo,ledger['commit'])
    verify_artifact_report(repo,report)
    graph=graph_from_commit(repo,ledger['commit'])
    identity=committed_ontology(repo,ledger['commit'])['document']
    findings=[]
    if report['summary']['unclassified']:
        findings.append({'id':'UNCLASSIFIED','count':report['summary']['unclassified']})
    if report['summary']['stale_rules']:
        findings.append({'id':'STALE_ROLE_RULE','paths':report['summary']['stale_rules']})
    if {p['id'] for p in identity['products']}!={'cora'}:
        findings.append({'id':'PRODUCT_IDENTITY_DRIFT'})
    if {s['id'] for s in identity['software']}!={'cora-engine','cora-release-verification'}:
        findings.append({'id':'SOFTWARE_IDENTITY_DRIFT'})
    test_contract = next((a for a in report['artifacts'] if a['path']=='tests/test_pr10_artifact_roles.py'),None)
    if not test_contract or not {'TEST','CONTRACT_VERIFIER','FIXTURE'}.issubset(test_contract['roles']):
        findings.append({'id':'MULTI_ROLE_CONTRACT_NOT_DEMONSTRATED'})
    return {'schema':'cora-self-audit-v1-experimental/1', 'commit':ledger['commit'],
            'product_id':'cora','software_ids':['cora-engine','cora-release-verification'],
            'repository_scope':'Git commit, not external deployment','artifact_report_digest':report['report_digest'],
            'graph_digest':graph['graph_digest'], 'tracked_artifacts':report['summary']['total_tracked_artifacts'],
            'declared_artifacts':report['summary']['declared_artifacts'],
            'findings':findings,'status':'PASS_SCOPED' if not findings else 'BLOCKED',
            'limits':['Role declarations are not runtime proof','No independent production deployment or external consumer closure',
                      'Human novice engineer acceptance and protected branch settings require external evidence']}


def main() -> int:
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path('.'));p.add_argument('--revision',default='HEAD');p.add_argument('--output',type=Path)
    a=p.parse_args()
    try:
        data=verify_self(a.repo,a.revision)
        rendered=json.dumps(data,sort_keys=True,indent=2)+'\n'
        if a.output:a.output.write_text(rendered,encoding='utf-8')
        else:sys.stdout.write(rendered)
        return 0 if data['status']=='PASS_SCOPED' else 2
    except (ValueError,OSError,KeyError,TypeError,ImportError) as e:
        print('CORA self-audit: '+str(e),file=sys.stderr)
        return 3
if __name__=='__main__':raise SystemExit(main())
