"""Continuous CORA development controls: pinned source, bounded claims, human-only approval.

No invocation of repository code, LLMs, tests, network, transformations, or CI APIs.
The policy used to classify PR changes comes from the BASE commit, NEVER from HEAD.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from .evidence import domain_hash, valid_path

SCHEMA = 'cora-continuous-gate/1'
POLICY_SCHEMA = 'cora-continuous-policy/1'
PROPOSAL_SCHEMA = 'cora-agent-proposal/1'
POLICY_PATH = '.cora/continuous-policy.json'
MAX_CHANGES = 2048
SHA = re.compile(r'^[0-9a-f]{40}(?:[0-9a-f]{24})?$')
ROLES = frozenset({'PRODUCT_OWNER', 'MAINTAINER', 'INDEPENDENT_SECURITY_REVIEWER',
                   'RUNTIME_OWNER', 'RELEASE_MANAGER', 'DATA_RETENTION_OWNER'})
STATUS = ('OBSERVED_REVIEW_REQUIRED', 'BOOTSTRAP_REVIEW_REQUIRED', 'BLOCKED')


def _git(repo: Path, *args: str, limit: int=8 * 1024 * 1024) -> bytes:
    p = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, check=False, timeout=45)
    if p.returncode:
        raise ValueError('Git verification failed: ' + p.stderr.decode('utf-8','replace')[:240])
    if len(p.stdout)>limit:
        raise ValueError('Git verification exceeds output budget')
    return p.stdout


def _commit(repo: Path, name: str) -> str:
    return _git(repo,'rev-parse','--verify','--end-of-options',name+'^{commit}',limit=256).decode().strip()


def _is_ancestor(repo: Path, base: str, head: str) -> bool:
    p=subprocess.run(['git','-C',str(repo),'merge-base','--is-ancestor',base,head],capture_output=True,timeout=45)
    if p.returncode not in (0,1):
        raise ValueError('Git ancestry check failed')
    return p.returncode==0


def _source_policy(repo: Path, commit: str) -> dict | None:
    p=subprocess.run(['git','-C',str(repo),'show',commit+':'+POLICY_PATH],capture_output=True,timeout=45)
    if p.returncode:
        # Distinguish an absent file from a damaged/missing committed object.
        existing=_git(repo,'ls-tree','--name-only',commit,'--',POLICY_PATH,limit=1024).decode().strip()
        if existing:
            raise ValueError('committed policy cannot be read')
        return None
    if len(p.stdout)>128 * 1024:
        raise ValueError('committed policy too large')
    try:
        document=json.loads(p.stdout.decode('utf-8'))
    except (UnicodeDecodeError,json.JSONDecodeError) as exc:
        raise ValueError('invalid committed policy encoding') from exc
    _validate_policy(document)
    return document


def _validate_policy(data:dict)->None:
    if not isinstance(data,dict) or set(data)!= {'schema','version','max_changed_paths','high_risk_prefixes','high_risk_paths','required_human_roles','review_processes'}:
        raise ValueError('policy fields missing or extra')
    if data['schema']!=POLICY_SCHEMA or data['version']!=1 or type(data['max_changed_paths']) is not int or not 1<=data['max_changed_paths']<=MAX_CHANGES:
        raise ValueError('invalid continuous policy version/budget')
    for name in ('high_risk_prefixes','high_risk_paths','required_human_roles','review_processes'):
        if not isinstance(data[name],list) or len(data[name])>64 or any(not isinstance(x,str) or not x for x in data[name]) or len(data[name])!=len(set(data[name])):
            raise ValueError('invalid policy list: '+name)
    if not data['high_risk_prefixes'] or not data['required_human_roles']:
        raise ValueError('empty mandatory risk/review policy')
    if any(not valid_path(x) for x in data['high_risk_prefixes'] + data['high_risk_paths']):
        raise ValueError('unsafe policy path')
    if any(x not in ROLES for x in data['required_human_roles']):
        raise ValueError('unknown reviewer role')
    if not set(data['review_processes']).issubset({'source','history','architecture','forensics','debt','verification','full'}):
        raise ValueError('unknown analysis process')


def _changes(repo:Path,base:str,head:str)->list[dict]:
    raw=_git(repo,'diff','--no-ext-diff','--find-renames','--name-status','-z',base,head,'--')
    chunks=raw.split(b'\0');rows=[];i=0
    while i<len(chunks) and chunks[i]:
        try:status=chunks[i].decode('ascii');i+=1
        except UnicodeDecodeError as exc:raise ValueError('nonascii Git status') from exc
        if not status or status[0] not in ('A','M','D','R','C','T','U'):
            raise ValueError('unexpected Git change type')
        if i>=len(chunks) or not chunks[i]:raise ValueError('truncated Git name-status')
        try:old=chunks[i].decode('utf-8');i+=1
        except UnicodeDecodeError as exc:raise ValueError('non-UTF8 Git path') from exc
        new=old
        if status[0] in ('R','C'):
            if i>=len(chunks) or not chunks[i]:raise ValueError('truncated Git rename')
            try:new=chunks[i].decode('utf-8');i+=1
            except UnicodeDecodeError as exc:raise ValueError('non-UTF8 Git rename') from exc
        if not valid_path(old) or not valid_path(new):raise ValueError('unsafe Git changed path')
        rows.append({'status':status,'old_path':old,'new_path':new})
        if len(rows)>MAX_CHANGES:raise ValueError('changed-paths scan budget exceeded')
    return sorted(rows,key=lambda x:(x['old_path'],x['new_path'],x['status']))


def _risk(path:str, policy:dict)->bool:
    return path in policy['high_risk_paths'] or any(path==x or path.startswith(x.rstrip('/')+'/') for x in policy['high_risk_prefixes'])


def evaluate(repo:Path,base:str,head:str,*,phase:str='premerge',with_debt:bool=False)->dict:
    """Compute source-bound receipt. Labels are review routes, not security proof.

    First policy installation is a bootstrap request, never self-attested approval.
    """
    if phase not in ('premerge','postmerge') or type(with_debt) is not bool:
        raise ValueError('invalid lifecycle phase')
    repo=Path(repo).resolve(strict=True)
    before=_commit(repo,base);after=_commit(repo,head)
    ancestry=_is_ancestor(repo,before,after)
    rows=_changes(repo,before,after)
    previous=_source_policy(repo,before)
    next_policy=_source_policy(repo,after)
    bootstrap=previous is None
    active=previous or next_policy
    if active is None:
        policy_state='MISSING_POLICY'; policy_digest=None
    else:
        policy_state='BASE_COMMITTED' if previous is not None else 'UNTRUSTED_BOOTSTRAP'
        policy_digest=domain_hash('CORA:continuous-policy:1',active)
    policy_changed=previous!=next_policy
    budget=active['max_changed_paths'] if active else 0
    high=[]
    if active:
        for row in rows:
            if any(_risk(p,active) for p in {row['old_path'],row['new_path']}):
                high.append(row['new_path'])
    if not ancestry or active is None or len(rows)>budget:
        state='BLOCKED'
    elif bootstrap:
        state='BOOTSTRAP_REVIEW_REQUIRED'
    else:
        state='OBSERVED_REVIEW_REQUIRED'
    if policy_changed or high:
        required=sorted(set(active['required_human_roles'] if active else []) | {'INDEPENDENT_SECURITY_REVIEWER','MAINTAINER'})
    else:
        required=['MAINTAINER']
    blockers=[]
    if not ancestry:blockers.append('BASE_NOT_ANCESTOR_OF_HEAD')
    if active is None:blockers.append('NO_COMMITTED_POLICY')
    if len(rows)>budget:blockers.append('CHANGED_PATH_BUDGET_EXCEEDED')
    if bootstrap:blockers.append('TRUSTED_BASE_POLICY_NOT_YET_ESTABLISHED')
    if policy_changed:blockers.append('POLICY_CHANGED_REQUIRES_INDEPENDENT_REVIEW')
    if high:blockers.append('PROTECTED_PATHS_REQUIRE_INDEPENDENT_REVIEW')
    debt=None
    if phase=='postmerge' and with_debt:
        from .debt import compare_debt
        try:
            debt=compare_debt(repo,before,after,max_commits=12)
        except (ValueError,KeyError,TypeError,subprocess.TimeoutExpired) as exc:
            debt={'state':'DEBT_NOT_REPRODUCED','reason':type(exc).__name__}
            blockers.append('DEBT_COMPARISON_UNAVAILABLE')
    result={'schema':SCHEMA,'phase':phase,'base_commit':before,'head_commit':after,
            'base_is_ancestor':ancestry,'changed_paths':rows,'changed_count':len(rows),
            'high_risk_paths':sorted(set(high)),'policy_state':policy_state,
            'base_policy_digest':domain_hash('CORA:continuous-policy:1',previous) if previous else None,
            'effective_policy_digest':policy_digest,'policy_modified':policy_changed,
            'status':state,'required_human_roles':required,'required_processes':active['review_processes'] if active else [],
            'blockers':sorted(set(blockers)),'debt_delta':debt,
            'ci_review_attestation':'NOT_VERIFIED_BY_OFFLINE_CORA',
            'runtime_deployment_attestation':'NOT_VERIFIED',
            'authorization':'NONE','trust_boundary':'PR_CODE_CANNOT_ATTEST_PROTECTED_HOST_CHECKS'}
    result['receipt_digest']=domain_hash('CORA:continuous-gate:1',result)
    return result


def verify_gate(repo:Path,report:dict)->bool:
    if not isinstance(report,dict) or report.get('schema')!=SCHEMA:
        raise ValueError('invalid lifecycle receipt')
    if report.get('receipt_digest')!=domain_hash('CORA:continuous-gate:1',{k:v for k,v in report.items() if k!='receipt_digest'}):
        raise ValueError('invalid lifecycle digest')
    expected=evaluate(repo,report['base_commit'],report['head_commit'],phase=report['phase'],with_debt=report['debt_delta'] is not None)
    if report!=expected:raise ValueError('lifecycle receipt does not match Git and committed policy')
    return True


def agent_check(repo:Path,proposal:dict)->dict:
    """Reconcile an untrusted agent's change claim with Git; never authenticate its author/tests."""
    if not isinstance(proposal,dict) or set(proposal)!={'schema','agent_id','base_commit','head_commit','intent','changed_paths','test_claims','unknowns','authorized_action'}:
        raise ValueError('invalid agent proposal fields')
    if proposal['schema']!=PROPOSAL_SCHEMA or proposal['authorized_action']!='NONE':
        raise ValueError('agent cannot self-authorize changes')
    for name in ('agent_id','intent'):
        if not isinstance(proposal[name],str) or not 4<=len(proposal[name])<=1000:
            raise ValueError('invalid agent identity or intent')
    for field in ('changed_paths','test_claims','unknowns'):
        if not isinstance(proposal[field],list) or len(proposal[field])>MAX_CHANGES or any(not isinstance(x,str) for x in proposal[field]):
            raise ValueError('invalid agent proposal collection')
    gate=evaluate(repo,proposal['base_commit'],proposal['head_commit'])
    actual=sorted({x['new_path'] for x in gate['changed_paths']}|{x['old_path'] for x in gate['changed_paths']})
    if sorted(proposal['changed_paths'])!=actual or len(proposal['changed_paths'])!=len(set(proposal['changed_paths'])):
        raise ValueError('agent claims do not match Git source changes')
    result={'schema':'cora-agent-check/1','base_commit':gate['base_commit'],'head_commit':gate['head_commit'],
            'source_gate_digest':gate['receipt_digest'],'agent_id':proposal['agent_id'],
            'claimed_tests':proposal['test_claims'],'test_trust':'UNVERIFIED_AGENT_ASSERTIONS',
            'status':'SOURCE_BOUND_PROPOSAL_REVIEW_REQUIRED','required_human_roles':gate['required_human_roles'],
            'authorization':'NONE'}
    result['check_digest']=domain_hash('CORA:agent-check:1',result)
    return result
