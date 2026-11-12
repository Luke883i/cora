"""Read-only, explicitly scoped CORA process registry and source-bound replay.

'full' runs all *safe read-only source methods*, not external scanners,
LLMs, target test commands, transforms, publication or runtime probes.
"""
from __future__ import annotations
from pathlib import Path
from time import monotonic
from .evidence import domain_hash, valid_path
from .git_snapshot import snapshot
from .artifact_roles import artifact_audit
from .adapters import adapter_audit
from .archaeology import mine_history
from .graph import graph_from_commit
from .holistic import holistic_audit
from .selection import select_file
from .debt import debt_scan
from .practice_contract import project as practice_project

PROCESSES = ('source', 'history', 'architecture', 'forensics', 'debt', 'verification', 'full')
IMPLEMENTED = {
 'source': ('git_snapshot', 'artifact_roles', 'manifest_adapters'),
 'history': ('git_archaeology',),
 'architecture': ('python_candidate_graph', 'manifest_adapters'),
 'forensics': ('holistic_archaeology', 'file_selection_if_focus'),
 'debt': ('debt_signals',),
 'verification': ('git_snapshot', 'artifact_roles', 'manifest_adapters', 'git_archaeology'),
 'full': ('git_snapshot', 'artifact_roles', 'manifest_adapters', 'git_archaeology',
          'python_candidate_graph', 'holistic_archaeology', 'debt_signals',
          'file_selection_if_focus'),
}


def process_catalog() -> dict:
    return {'schema':'cora-process-catalog/1', 'processes':[
      {'id':p,'methods':list(IMPLEMENTED[p]),'mode':'READ_ONLY_PINNED_GIT'} for p in PROCESSES],
      'excluded_unsafe_methods':['target_test_execution', 'arbitrary_LLM_calls',
         'SARIF_scanner_execution', 'external_network_calls',
         'rename_archive_quarantine_delete_transform', 'release_publication'],
      'test_process_policy':'verification means source revalidation, not executing target tests'}


def run_suite(repo:Path,revision:str='HEAD',*,process:str='full',
              max_commits:int=64,focus:str|None=None,measure:bool=False)->dict:
    if process not in PROCESSES or type(max_commits) is not int or not 1<=max_commits<=1000:
        raise ValueError('unknown CORA process or invalid history limit')
    if focus is not None and not valid_path(focus):
        raise ValueError('unsafe focus')
    repo=Path(repo).resolve(strict=True)
    commit=snapshot(repo,revision)['commit']
    checks=[]
    started=monotonic() if measure else None
    methods=[]
    requested=set(IMPLEMENTED[process])
    def record(name:str,fn):
        begun=monotonic() if measure else None
        try:
            v=fn()
            digest=next((v[k] for k in ('report_digest','ledger_digest','graph_digest','digest','selection_digest') if k in v),None)
            item={'method':name,'status':'EXECUTED_SCOPED','source_digest':digest}
        except (ValueError, KeyError, TypeError) as exc:
            item={'method':name,'status':'DEBT_BLOCKED','reason':type(exc).__name__}
        if measure:
            item['elapsed_ms']=max(0,int((monotonic()-begun)*1000))
            item['timing_basis']='DIRECT_METHOD_EXECUTION'
        checks.append(item)
        methods.append(name)
    # The full pipeline reuses *same-commit, same-history* evidence actually
    # computed by holistic_audit. This is not a global cache, and a method with
    # missing evidence is DEBT_BLOCKED rather than counted as successfully run.
    holistic = None
    holistic_duration=None
    if process == 'full':
        holistic_started=monotonic() if measure else None
        try:
            holistic = holistic_audit(repo,commit,max_commits=max_commits,focus=focus)
        except (ValueError,KeyError,TypeError):
            pass  # Explicit fallback below still records failed methods.
        if measure:
            holistic_duration=max(0,int((monotonic()-holistic_started)*1000))
    derived = {
        'git_snapshot': ('ledger_digest','git_provenance'),
        'artifact_roles': ('artifact_report_digest','artifact_roles'),
        'manifest_adapters': ('adapter_report_digest','manifest_adapters'),
        'git_archaeology': ('history_digest','git_archaeology'),
        'python_candidate_graph': ('graph_digest','python_static_graph'),
        'holistic_archaeology': ('report_digest','cochange_and_development_groups'),
    }
    sources = {
        'git_snapshot': lambda:snapshot(repo,commit),
        'artifact_roles': lambda:artifact_audit(repo,commit),
        'manifest_adapters': lambda:adapter_audit(repo,commit),
        'git_archaeology': lambda:mine_history(repo,commit,max_commits=max_commits),
        'python_candidate_graph': lambda:graph_from_commit(repo,commit),
        'holistic_archaeology': lambda:holistic_audit(repo,commit,max_commits=max_commits,focus=focus),
        'debt_signals': lambda:debt_scan(repo,commit,max_commits=max_commits,_holistic_report=holistic),
    }
    for name in IMPLEMENTED[process]:
        if name == 'file_selection_if_focus':
            continue
        if name in derived and holistic is not None:
            field,ledger_field=derived[name]
            digest=holistic.get(field)
            method_status=holistic['method_ledger'].get(ledger_field)
            if digest is not None and method_status not in ('NOT_AVAILABLE','NOT_RUN'):
                item={'method':name,'status':'REUSED_SCOPED_FROM_HOLISTIC',
                      'source_digest':digest}
                if measure:
                    item['elapsed_ms']=holistic_duration if name=='holistic_archaeology' else None
                    item['timing_basis']='SHARED_HOLISTIC_INVOCATION' if name=='holistic_archaeology' else 'REUSED_NOT_INDEPENDENTLY_TIMED'
                checks.append(item)
            else:
                item={'method':name,'status':'DEBT_BLOCKED','reason':'SOURCE_METHOD_UNAVAILABLE'}
                if measure:
                    item['elapsed_ms']=None
                    item['timing_basis']='SOURCE_METHOD_UNAVAILABLE'
                checks.append(item)
            methods.append(name)
        else:
            record(name,sources[name])
    if focus is not None and 'file_selection_if_focus' in requested:
        record('file_selection_if_focus',lambda:select_file(repo,focus,revision=commit))
    if focus is None and 'file_selection_if_focus' in requested:
        item={'method':'file_selection_if_focus','status':'NOT_RUN_REQUIRES_FOCUS'}
        if measure:
            item['elapsed_ms']=None
            item['timing_basis']='NOT_INVOKED'
        checks.append(item)
    status='DEBT_BLOCKED' if any(c['status']=='DEBT_BLOCKED' for c in checks) else 'PASS_SCOPED_WITH_UNVERIFIED_GAPS'
    result={'schema':'cora-process-run/1', 'commit':commit,'process':process,'history_limit':max_commits,
            'focus':focus,'results':checks,'status':status,
            'methods_not_invoked':sorted(set(IMPLEMENTED['full'])-set(methods)),
            'excluded_unsafe_methods':process_catalog()['excluded_unsafe_methods'],
            'coverage':'Selected read-only source methods only; full does not mean all real-world behavior',
            'authorized_action':'NONE',
            'practice_obligations':practice_project(repo, commit)}
    if measure:
        result['timing']={'wall_ms':max(0,int((monotonic()-started)*1000)),
                          'basis':'MONOTONIC_LOCAL_OBSERVATION_NOT_REPLAYABLE'}
    result['run_digest']=domain_hash('CORA:process-run:1',result)
    return result


def verify_suite(repo:Path,report:dict)->bool:
    if not isinstance(report,dict) or report.get('schema')!='cora-process-run/1':
        raise ValueError('invalid process report')
    if run_suite(repo,report['commit'],process=report['process'],
                 max_commits=report['history_limit'],focus=report['focus']) != report:
        raise ValueError('process report differs from immutable Git evidence')
    return True
