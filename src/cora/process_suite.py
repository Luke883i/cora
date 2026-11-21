"""Read-only, explicitly scoped CORA process registry and source-bound replay.

'full' runs all *safe read-only source methods*, not external scanners,
LLMs, target test commands, transforms, publication or runtime probes.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import re
import shutil
import subprocess
from time import monotonic
from .evidence import domain_hash, valid_path
from .git_snapshot import snapshot, git
from .artifact_roles import artifact_audit
from .adapters import adapter_audit
from .archaeology import mine_history
from .graph import graph_from_commit
from .holistic import holistic_audit
from .selection import select_file
from .debt import debt_scan
from .practice_contract import project as practice_project

IMPLEMENTED = {
 'source': ('git_snapshot', 'artifact_roles', 'manifest_adapters'),
 'history': ('git_archaeology',),
 'architecture': ('python_candidate_graph', 'manifest_adapters'),
 'forensics': ('holistic_archaeology', 'file_selection_if_focus'),
 'debt': ('debt_signals',),
 'verification': ('git_snapshot', 'artifact_roles', 'manifest_adapters', 'git_archaeology'),
}
# The full method set is derived from existing process groups, not copied to a
# second list. Keep focus-sensitive selection last; it can report NOT_RUN when
# no focus is supplied without pretending an external target test ran.
IMPLEMENTED['full'] = tuple(dict.fromkeys(
    m for g in IMPLEMENTED.values() for m in g if m != 'file_selection_if_focus')) + ('file_selection_if_focus',)
PROCESSES = tuple(IMPLEMENTED)

# Declared third-party candidates, never installed or automatically executed.
# Existing CORA owners remain authoritative for source, evidence and consent.
EXTERNAL_TOOLS = (
    ('openspec', 'openspec', ('--version',), ('openspec', 'spec driven', 'specification delta', 'requirements change'), 'source', 'SPEC_DELTA'),
    ('itself', 'itself', ('--version',), ('itself', 'claim verification', 'claim evidence', 'reasoning receipt'), 'verification', 'CLAIM_LEDGER'),
    ('agent-assure', 'agent-assure', ('--version',), ('agent assure', 'process regression', 'evidence link', 'agent release'), 'verification', 'PROCESS_EVIDENCE'),
    ('agent-workflow-bench', 'awb', ('--help',), ('workflow benchmark', 'agent workflow', 'trace observer', 'workflow regression'), 'verification', 'WORKFLOW_TRACE'),
    ('semgrep', 'semgrep', ('--version',), ('semgrep', 'static analysis', 'security scan', 'sarif'), 'debt', 'SARIF'),
    ('ast-grep', 'sg', ('--version',), ('ast grep', 'structural search', 'syntax tree', 'code pattern'), 'architecture', 'STRUCTURAL_FINDINGS'),
    ('hypothesis', None, (), ('hypothesis', 'property based', 'generative test', 'shrinking'), 'verification', 'TARGET_NATIVE_TEST'),
    ('cosign', 'cosign', ('version',), ('cosign', 'artifact signing', 'signature verification', 'provenance signature'), 'verification', 'SIGNED_ATTESTATION'),
    ('in-toto', 'in-toto-verify', ('--help',), ('in toto', 'supply chain attestation', 'supply chain integrity'), 'verification', 'ATTESTATION'),
    ('openhands', None, (), ('openhands', 'coding agent execution', 'autonomous coding'), 'source', 'EXTERNAL_AGENT'),
)


def _external_tools(intent: str | None, probe_tool: str | None,
                    authorize_probe: bool) -> tuple[list[dict], list[dict], dict | None]:
    if intent is not None and (not isinstance(intent, str) or len(intent) > 1024):
        raise ValueError('intent must be a bounded string')
    if authorize_probe != (probe_tool is not None):
        raise ValueError('tool probe requires explicit matched authorization and identifier')
    allowed = {row[0] for row in EXTERNAL_TOOLS}
    if probe_tool is not None and probe_tool not in allowed:
        raise ValueError('tool not in closed CORA external catalog')
    found = []
    matches = []
    normalized = re.sub(r'[^a-z0-9]+', ' ', intent.casefold()).strip() if intent else ''
    for key, binary, args, terms, process, handoff in EXTERNAL_TOOLS:
        row = {'id': key, 'owner': 'UPSTREAM_EXTERNAL', 'cora_process': process,
               'execution': 'NOT_RUN_REQUIRES_EXPLICIT_EXTERNAL_AUTHORIZATION',
               'installation': 'NOT_CHECKED', 'executable': binary,
               'handoff': handoff, 'activation': 'EXTERNAL_OWNER_OR_AUTHORIZED_RUNNER',
               'approval': 'NONE'}
        found.append(row)
        hits = sorted({term for term in terms if re.search(
            r'(?<![a-z0-9])' + re.escape(re.sub(r'[^a-z0-9]+', ' ', term.casefold()).strip())
            + r'(?![a-z0-9])', normalized)}) if normalized else []
        if hits:
            matches.append({'id': key, 'cora_process': process,
                            'matched_terms': hits, 'status': 'CANDIDATE_NOT_EXECUTED',
                            'approval': 'NONE'})
    matches.sort(key=lambda item: (-max(map(len, item['matched_terms'])), item['id']))
    probe = None
    if probe_tool is not None:
        item = next(x for x in EXTERNAL_TOOLS if x[0] == probe_tool)
        binary = item[1]
        if binary is None:
            probe = {'id': probe_tool, 'status': 'NO_SAFE_STANDALONE_PROBE',
                     'authorization': 'EXPLICIT_VERSION_PROBE_ONLY', 'target_execution': 'NOT_RUN'}
        else:
            resolved = shutil.which(binary)
            if resolved is None:
                probe = {'id': probe_tool, 'status': 'NOT_INSTALLED',
                         'authorization': 'EXPLICIT_VERSION_PROBE_ONLY', 'target_execution': 'NOT_RUN'}
            else:
                from .process_bounds import run_bounded
                try:
                    result = run_bounded([resolved, *item[2]], cwd=Path.cwd(),
                                         timeout=5, max_output=8192)
                except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
                    probe = {'id': probe_tool, 'status': 'PROBE_FAILED',
                             'error_type': type(exc).__name__,
                             'authorization': 'EXPLICIT_VERSION_PROBE_ONLY', 'target_execution': 'NOT_RUN'}
                else:
                    probe = {'id': probe_tool,
                             'status': 'VERSION_PROBE_EXECUTED_UNTRUSTED' if result.returncode == 0 else 'PROBE_FAILED_EXIT',
                             'exit_code': result.returncode,
                             'stdout_sha256': hashlib.sha256(result.stdout).hexdigest(),
                             'authorization': 'EXPLICIT_VERSION_PROBE_ONLY', 'target_execution': 'NOT_RUN'}
    return found, matches, probe


def process_catalog(*, intent: str | None = None, probe_tool: str | None = None,
                    authorize_probe: bool = False) -> dict:

    catalog = {'schema':'cora-process-catalog/1', 'processes':[
      {'id':p,'methods':list(IMPLEMENTED[p]),'mode':'READ_ONLY_PINNED_GIT'} for p in PROCESSES],
      'excluded_unsafe_methods':['target_test_execution', 'arbitrary_LLM_calls',
         'SARIF_scanner_execution', 'external_network_calls',
         'rename_archive_quarantine_delete_transform', 'release_publication'],
      'test_process_policy':'verification means source revalidation, not executing target tests'}
    # Preserve exact historical process-list bytes and 77-operation behavioral oracle.
    # External capability discovery is a separately requested expansion.
    if intent is None and probe_tool is None and not authorize_probe:
        return catalog
    found, suggestions, probe = _external_tools(intent, probe_tool, authorize_probe)
    catalog.update({'external_tools':found, 'inference':suggestions,
                    'external_evidence':'UNTRUSTED_UNTIL_SEPARATELY_VERIFIED',
                    'authorized_action':'NONE'})
    if probe is not None:
        catalog['explicit_version_probe'] = probe
    return catalog


def run_suite(repo:Path,revision:str='HEAD',*,process:str='full',
              max_commits:int=64,focus:str|None=None,measure:bool=False,
              change_base:str|None=None,source_mode:str='strict',
              role_manifest:str='cora.artifact-roles.json',
              ontology_manifest:str='cora.ontology.json')->dict:
    if process not in PROCESSES or type(max_commits) is not int or not 1<=max_commits<=1000:
        raise ValueError('unknown CORA process or invalid history limit')
    if source_mode not in ('strict', 'target_neutral') or not valid_path(role_manifest) or not valid_path(ontology_manifest):
        raise ValueError('unknown source manifest policy or unsafe manifest path')
    if focus is not None and not valid_path(focus):
        raise ValueError('unsafe focus')
    repo=Path(repo).resolve(strict=True)
    ledger=snapshot(repo,revision)
    commit=ledger['commit']
    tracked={row['path'] for row in ledger['records']}
    absent = ({'artifact_roles': role_manifest,
               'python_candidate_graph': ontology_manifest}
              if source_mode=='target_neutral' else {})
    absent={method: path for method,path in absent.items() if path not in tracked}
    checks=[]
    started=monotonic() if measure else None
    methods=[]
    def record(name:str,fn):
        begun=monotonic() if measure else None
        if name in absent:
            item={'method':name,'status':'NOT_CONFIGURED',
                  'required_manifest':absent[name],
                  'reason':'ABSENT_IN_PINNED_GIT'}
            if measure:
                item['elapsed_ms']=None
                item['timing_basis']='NOT_INVOKED'
            checks.append(item)
            methods.append(name)
            return
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
            holistic = holistic_audit(repo,commit,max_commits=max_commits,focus=focus,
                                       manifest_mode=source_mode,role_manifest=role_manifest,
                                       ontology_manifest=ontology_manifest)
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
        'artifact_roles': lambda:artifact_audit(repo,commit,manifest=role_manifest),
        'manifest_adapters': lambda:adapter_audit(repo,commit),
        'git_archaeology': lambda:mine_history(repo,commit,max_commits=max_commits),
        'python_candidate_graph': lambda:graph_from_commit(repo,commit,ontology_path=ontology_manifest),
        'holistic_archaeology': lambda:holistic_audit(repo,commit,max_commits=max_commits,
                                                        focus=focus,manifest_mode=source_mode,
                                                        role_manifest=role_manifest,ontology_manifest=ontology_manifest),
        'debt_signals': lambda:debt_scan(repo,commit,max_commits=max_commits,_holistic_report=holistic),
        'file_selection_if_focus': lambda:select_file(repo,focus,revision=commit),
    }
    for name in IMPLEMENTED[process]:
        if name == 'file_selection_if_focus' and focus is None:
            item={'method':name,'status':'NOT_RUN_REQUIRES_FOCUS'}
            if measure:
                item['elapsed_ms']=None
                item['timing_basis']='NOT_INVOKED'
            checks.append(item)
            continue
        if name in derived and holistic is not None:
            field,ledger_field=derived[name]
            digest=holistic.get(field)
            method_status=holistic['method_ledger'].get(ledger_field)
            if name in absent:
                item={'method':name,'status':'NOT_CONFIGURED',
                      'required_manifest':absent[name],
                      'reason':'ABSENT_IN_PINNED_GIT'}
                if measure:
                    item['elapsed_ms']=None
                    item['timing_basis']='NOT_INVOKED'
                checks.append(item)
            elif digest is not None and method_status not in ('NOT_AVAILABLE','NOT_RUN', 'NOT_CONFIGURED'):
                item={'method':name,'status':('PARTIAL_SCOPED_NOT_CONFIGURED'
                      if name=='holistic_archaeology' and absent else 'REUSED_SCOPED_FROM_HOLISTIC'),
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
    if process=='full' and set(sources)-{row['method'] for row in checks}:
        raise ValueError('full incomplete')
    status=('DEBT_BLOCKED' if any(c['status']=='DEBT_BLOCKED' for c in checks)
            else 'SOURCE_PARTIAL_NOT_CONFIGURED' if any(
                c['status'] in ('NOT_CONFIGURED','PARTIAL_SCOPED_NOT_CONFIGURED') for c in checks)
            else 'PASS_SCOPED_WITH_UNVERIFIED_GAPS')
    result={'schema':'cora-process-run/1', 'commit':commit,'process':process,'history_limit':max_commits,
            'focus':focus,'results':checks,'status':status,
            'methods_not_invoked':sorted(set(IMPLEMENTED['full'])-set(methods)),
            'excluded_unsafe_methods':process_catalog()['excluded_unsafe_methods'],
            'coverage':'Selected read-only source methods only; full does not mean all real-world behavior',
            'authorized_action':'NONE',
            'practice_obligations':practice_project(repo, commit, change_base=change_base)}
    if source_mode == 'target_neutral':
        result['source_mode']=source_mode
        result['unconfigured_manifests']=dict(sorted(
            (method,path) for method,path in absent.items() if method in IMPLEMENTED[process]))
    if change_base is not None:
        result['change_base']=result['practice_obligations']['change_base']
    if measure:
        result['timing']={'wall_ms':max(0,int((monotonic()-started)*1000)),
                          'basis':'MONOTONIC_LOCAL_OBSERVATION_NOT_REPLAYABLE'}
    if (role_manifest,ontology_manifest)!=('cora.artifact-roles.json','cora.ontology.json'):
        result['manifest_paths']={'artifact_roles':role_manifest,'ontology':ontology_manifest}
    result['run_digest']=domain_hash('CORA:process-run:1',result)
    return result


# Last exact CORA main before the PR58 projection first existed.
# Only receipts from this original CORA lineage may use the historical shape.
PRE_PR58_MAIN = '0ddb9024d0d6b31dd7734793173906c9c4d38a48'


def verify_suite(repo:Path,report:dict)->bool:
    if not isinstance(report,dict) or report.get('schema')!='cora-process-run/1':
        raise ValueError('invalid process report')
    repo=Path(repo).resolve(strict=True)
    has_practices='practice_obligations' in report
    if not has_practices and 'change_base' in report:
        raise ValueError('legacy receipt cannot declare new range')
    expected=run_suite(repo,report['commit'],process=report['process'],
                       max_commits=report['history_limit'],focus=report['focus'],
                       change_base=report.get('change_base'),
                       source_mode=report.get('source_mode','strict'),
                       role_manifest=report.get('manifest_paths',{}).get('artifact_roles','cora.artifact-roles.json'),
                       ontology_manifest=report.get('manifest_paths',{}).get('ontology','cora.ontology.json'))
    if not has_practices:
        # An old, source-replayed receipt does not magically acquire the
        # implementation added after its commit; historical bytes stay intact.
        # Check the immutable Git ancestry, not a caller-supplied "legacy" flag.
        try:
            git(repo,'merge-base','--is-ancestor',
                report['commit'],PRE_PR58_MAIN,max_output=128)
        except ValueError as exc:
            raise ValueError('missing practices on non-legacy Git source') from exc
        expected.pop('practice_obligations')
        expected.pop('run_digest')
        expected['run_digest']=domain_hash('CORA:process-run:1',expected)
    if expected != report:
        raise ValueError('process report differs from immutable Git evidence')
    return True
