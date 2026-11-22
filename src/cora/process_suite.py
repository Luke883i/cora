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


# Eighty-one addressable CAPABILITIES, not 81 independently executable CLI commands.
# The canonical 71-command parser and ten upstream owners remain untouched.
UNIVERSAL_SCHEMA = "cora-universal-capability-plan/1"
_BASELINE_OWNERS = frozenset(("version", "process-list", "snapshot"))
# Reuse SOURCE METHODS that One-Run already observed; never label these as
# individually executed CLI commands or independently validated target tests.
_SOURCE_FOR_COMMAND = {
    "graph": "python_candidate_graph",
    "archaeology": "git_archaeology",
    "debt-scan": "debt_signals",
    "artifact-audit": "artifact_roles",
    "adapter-audit": "manifest_adapters",
    "holistic-audit": "holistic_archaeology",
}
_SOURCE_METHOD_PASS = frozenset(("EXECUTED_SCOPED", "REUSED_SCOPED_FROM_HOLISTIC"))
_SOURCE_METHOD_STATES = _SOURCE_METHOD_PASS | frozenset((
    "NOT_RUN_REQUIRES_FOCUS", "NOT_CONFIGURED",
    "PARTIAL_SCOPED_NOT_CONFIGURED", "DEBT_BLOCKED"))


def universal_capability_plan(capabilities: list[dict], *, commit: str,
                              intent: str | None = None,
                              native_observations: list[dict] | None = None,
                              source_methods: list[dict] | None = None,
                              source_process: str | None = None) -> dict:
    """Select relevant owners; reuse observations, never perform new effects."""
    if (not isinstance(capabilities, list) or len(capabilities) != 71 or
            any(not isinstance(x, dict) or not isinstance(x.get("command"), str)
                or not isinstance(x.get("family"), str) for x in capabilities)):
        raise ValueError("canonical native capability census must have 71 typed rows")
    native = {x["command"]: x for x in capabilities}
    if len(native) != 71 or not _BASELINE_OWNERS.issubset(native):
        raise ValueError("duplicate, missing or forged native capability")
    if len(EXTERNAL_TOOLS) != 10 or len({x[0] for x in EXTERNAL_TOOLS}) != 10:
        raise ValueError("upstream owner census must contain exactly ten entries")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit):
        raise ValueError("unverifiable Git commit identifier")
    if intent is not None and (not isinstance(intent, str) or len(intent) > 1024):
        raise ValueError("bounded intent required")
    normalized = re.sub(r"[^a-z0-9]+", " ", (intent or "").casefold()).strip()
    tokens = {word for word in normalized.split() if len(word) >= 3}
    incoming = native_observations if native_observations is not None else []
    if not isinstance(incoming, list) or len(incoming) not in (0, 71):
        raise ValueError("only an exact complete One-Run native receipt may be reused")
    observations = {}
    for row in incoming:
        if (not isinstance(row, dict) or row.get("command") not in native or
                row.get("command") in observations or row.get("commit") != commit or
                row.get("authority") != "NONE" or
                row.get("state") not in ("RUN_REPORTED_UNATTESTED", "BLOCKED", "FAIL") or
                (row["state"] == "RUN_REPORTED_UNATTESTED" and
                 row["command"] not in _BASELINE_OWNERS) or
                (row["state"] != "RUN_REPORTED_UNATTESTED" and
                 row.get("stdout_sha256") is not None)):
            raise ValueError("non-canonical native execution receipt")
        observations[row["command"]] = row
    if observations and set(observations) != set(native):
        raise ValueError("partial native observation set")
    # These are existing run_suite() method receipts. Their behavior remains
    # source-scoped and is subsequently independently rederived by verify_one.
    source = {}
    if source_methods is not None:
        # A filtered process is complete against THAT selected group's owner
        # universe, never against eight full-profile methods not requested.
        profile = source_process if source_process is not None else "full"
        if profile not in IMPLEMENTED:
            raise ValueError("unknown original source method profile")
        if not isinstance(source_methods, list):
            raise ValueError("invalid source method ledger")
        for item in source_methods:
            if (not isinstance(item, dict) or
                    item.get("method") not in IMPLEMENTED["full"] or
                    item.get("method") in source or
                    item.get("status") not in _SOURCE_METHOD_STATES):
                raise ValueError("missing, duplicate or forged source method")
            digest = item.get("source_digest")
            if item["status"] in _SOURCE_METHOD_PASS:
                if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                    raise ValueError("source method execution lacks exact digest")
            elif digest is not None:
                raise ValueError("non-executed source method invented digest")
            source[item["method"]] = item
        if set(source) != set(IMPLEMENTED[profile]):
            raise ValueError("incomplete selected source method universe")
    rows = []
    for name, cap in sorted(native.items()):
        selected = name in _BASELINE_OWNERS
        if tokens:
            words = set(re.sub(r"[^a-z0-9]+", " ",
                               name + " " + cap["family"].lower()).split())
            selected = selected or bool(words & tokens)
            selected = selected or (
                name == "debt-scan" and bool(tokens & {"security", "sarif"}) or
                name == "graph" and bool(tokens & {"architecture", "imports"}) or
                name == "archaeology" and bool(tokens & {"history", "commits"}))
        witness = observations.get(name)
        if not selected:
            state, reason, digest = "NOT_SELECTED", "INTENT_NOT_RELEVANT", None
        elif name not in _BASELINE_OWNERS:
            state, reason, digest = "BLOCKED", "MISSING_QUALIFIED_OPERATIONAL_ADAPTER", None
        elif witness and witness["state"] == "RUN_REPORTED_UNATTESTED":
            digest = witness.get("stdout_sha256")
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ValueError("native execution without output digest")
            state, reason = "RUN_REPORTED_UNATTESTED", "REUSED_EXISTING_BOUNDED_OWNER_RECEIPT"
        else:
            state, reason, digest = "BLOCKED", "BOUNDED_NATIVE_OBSERVATION_UNAVAILABLE", None
        source_method = _SOURCE_FOR_COMMAND.get(name) if selected else None
        source_digest = None
        if (selected and name not in _BASELINE_OWNERS and source_method in source and
                source[source_method]["status"] in _SOURCE_METHOD_PASS):
            source_digest = source[source_method]["source_digest"]
            state, reason = ("REUSED_SOURCE_METHOD_SCOPED",
                             "SOURCE_METHOD_REUSED_NOT_INDIVIDUAL_CLI_EXECUTION")
        rows.append({"id": "cora:" + name, "kind": "NATIVE_CLI", "owner": "CORA",
                     "selected": selected, "state": state, "reason": reason,
                     "output_sha256": digest, "source_method": source_method,
                     "source_digest_sha256": source_digest, "authority": "NONE"})
    ranked = process_catalog(intent=intent or "")
    matches = {x["id"] for x in ranked.get("inference", [])}
    for name, binary, args, terms, process, handoff in sorted(EXTERNAL_TOOLS):
        selected = name in matches or bool(normalized and name.replace("-", " ") in normalized)
        rows.append({"id": "external:" + name, "kind": "UPSTREAM_CANDIDATE",
                     "owner": "UPSTREAM_EXTERNAL", "selected": selected,
                     "state": "BLOCKED" if selected else "NOT_SELECTED",
                     "reason": "EXTERNAL_TOOL_NOT_AUTHORIZED_OR_ATTESTED"
                     if selected else "INTENT_NOT_RELEVANT",
                     "output_sha256": None, "source_method": None,
                     "source_digest_sha256": None, "authority": "NONE"})
    rows.sort(key=lambda x: x["id"])
    counts = {"native": 71, "external": 10, "total": 81,
              "selected": sum(x["selected"] for x in rows),
              "run_reported": sum(x["state"] == "RUN_REPORTED_UNATTESTED" for x in rows),
              "source_reused": sum(x["state"] == "REUSED_SOURCE_METHOD_SCOPED" for x in rows),
              "blocked": sum(x["state"] == "BLOCKED" for x in rows),
              "not_selected": sum(x["state"] == "NOT_SELECTED" for x in rows)}
    return {"schema": UNIVERSAL_SCHEMA, "commit": commit, "intent": intent,
            "catalog": "71_CANONICAL_CLI_PLUS_10_UPSTREAM_CANDIDATES",
            "rows": rows, "counts": counts, "authority": "NONE",
            "product_status": "BLOCKED_EXTERNAL",
            "agent_handoff": {
                "selected": [r["id"] for r in rows if r["selected"]],
                "gaps": [{"id": r["id"], "reason": r["reason"]}
                         for r in rows if r["state"] == "BLOCKED"],
                "inference_scope": "DETERMINISTIC_LEXICAL_SELECTION_NOT_AI_REASONING",
                "human_review_required": True}}


def verify_universal_capability_plan(capabilities: list[dict], report: dict,
                                     native_observations: list[dict] | None = None,
                                     source_methods: list[dict] | None = None,
                                     source_process: str | None = None) -> bool:
    """Exact source replay: a digest is not independent runtime attestation."""
    if not isinstance(report, dict) or report.get("authority") != "NONE":
        raise ValueError("invalid capability report authority")
    expected = universal_capability_plan(
        capabilities, commit=report.get("commit"), intent=report.get("intent"),
        native_observations=native_observations, source_methods=source_methods,
        source_process=source_process)
    if report != expected:
        raise ValueError("capability plan, status or native receipt does not replay")
    return True
