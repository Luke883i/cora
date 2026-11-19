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
from .git_snapshot import git

SCHEMA = 'cora-continuous-gate/1'
POLICY_SCHEMA = 'cora-continuous-policy/1'
PROPOSAL_SCHEMA = 'cora-agent-proposal/1'
POLICY_PATH = '.cora/continuous-policy.json'
MAX_CHANGES = 2048
SHA = re.compile(r'^[0-9a-f]{40}(?:[0-9a-f]{24})?$')
ROLES = frozenset({'PRODUCT_OWNER', 'MAINTAINER', 'INDEPENDENT_SECURITY_REVIEWER',
                   'RUNTIME_OWNER', 'RELEASE_MANAGER', 'DATA_RETENTION_OWNER'})
STATUS = ('OBSERVED_REVIEW_REQUIRED', 'BOOTSTRAP_REVIEW_REQUIRED', 'BLOCKED')


def _commit(repo: Path, name: str) -> str:
    return git(repo,'rev-parse','--verify','--end-of-options',name+'^{commit}',max_output=256,timeout=45).decode().strip()


def _is_ancestor(repo: Path, base: str, head: str) -> bool:
    p=subprocess.run(['git','-C',str(repo),'merge-base','--is-ancestor',base,head],capture_output=True,timeout=45)
    if p.returncode not in (0,1):
        raise ValueError('Git ancestry check failed')
    return p.returncode==0


def _source_policy(repo: Path, commit: str) -> dict | None:
    p=subprocess.run(['git','-C',str(repo),'show',commit+':'+POLICY_PATH],capture_output=True,timeout=45)
    if p.returncode:
        # Distinguish an absent file from a damaged/missing committed object.
        existing=git(repo,'ls-tree','--name-only',commit,'--',POLICY_PATH,max_output=1024,timeout=45).decode().strip()
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
    raw=git(repo,'diff','--no-ext-diff','--find-renames','--name-status','-z',base,head,'--',max_output=8 * 1024 * 1024,timeout=45)
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


def evaluate_contextual(repo: Path, base: str, head: str, *,
                        contract: dict, phase: str = "premerge",
                        with_debt: bool = False,
                        witnesses: list[dict] | None = None,
                        intent: str | None = None) -> dict:
    """Source-only, generic target adapter over existing lifecycle/ontology.

    Static import edges are possible dependencies, not proven callpaths. No
    tests, Docker, network or target side effects are implicitly executed.
    """
    from collections import deque
    from .graph import graph_from_commit
    from .ontology import committed_ontology, members
    from .reticulum import invalidated_witnesses, assess_cut
    from .gold_assurance import convergent_plan
    from .gold_effects import audit_workflow

    if phase not in ("premerge", "postmerge"):
        raise ValueError("invalid lifecycle phase")
    if intent is not None and (not isinstance(intent, str) or
            not 12 <= len(intent.strip()) <= 1024 or chr(0) in intent):
        raise ValueError("bounded change-specific human intent required")
    repo = Path(repo).resolve(strict=True)
    gate = evaluate(repo, base, head, phase=phase, with_debt=with_debt)
    before, after = gate["base_commit"], gate["head_commit"]
    intent_digest = (domain_hash("CORA:intent-to-proof:1",
                     {"base": before, "head": after, "intent": intent.strip()})
                     if intent is not None else None)
    changed = sorted({p for row in gate["changed_paths"]
                      for p in (row["old_path"], row["new_path"])})
    graph = None
    declared = None
    graph_problem = None
    try:
        declared = committed_ontology(repo, after)
        graph = graph_from_commit(repo, after)
    except (ValueError, OSError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        graph_problem = type(exc).__name__
    # The HEAD graph cannot resolve imports targeting a removed/renamed file.
    # Reconstruct the BASE graph for these changes or explicitly block the
    # impact claim instead of silently dropping pre-change consumers.
    need_base_graph = any(row["status"][0] in ("D", "R", "T")
                          for row in gate["changed_paths"])
    base_graph = None
    base_graph_problem = None
    if need_base_graph:
        try:
            base_graph = graph_from_commit(repo, before)
        except (ValueError, OSError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
            base_graph_problem = type(exc).__name__
    consumers = {}
    imports_unknown = []
    product_context = []
    for candidate in (base_graph, graph):
        if candidate is None:
            continue
        for edge in candidate["edges"]:
            if (edge["kind"] == "static_import_candidate" and
                edge["source"].startswith("file:") and
                edge["target"].startswith("file:")):
                target = edge["target"][5:]
                source = edge["source"][5:]
                consumers.setdefault(target, set()).add(source)
    if graph is not None and declared is not None:
        for row in graph["findings"]:
            if row["kind"] in ("dynamic_import_unknown", "relative_import_unresolved",
                               "ambiguous_import", "import_unresolved",
                               "from_import_submodule_ambiguous"):
                imports_unknown.append(row)
        for item in changed:
            products = sorted(x["id"] for x in declared["document"]["products"]
                              if members(item, x["roots"]))
            software = sorted(x["id"] for x in declared["document"]["software"]
                              if members(item, x["roots"]))
            product_context.append({
                "path": item, "declared_products": products,
                "declared_software": software,
                "owner_status": "AMBIGUOUS_DECLARED_OWNER" if len(products) > 1 else
                ("DECLARED_CANDIDATE_NOT_ATTESTED" if products else
                 "UNASSIGNED_REPOSITORY_ARTIFACT"),
            })
    affected = set(changed)
    frontier = deque(changed)
    # Traverse only static Python candidate reverse imports, never conclude
    # that absence of an edge proves absence of a runtime consumer.
    while frontier:
        current = frontier.popleft()
        for dependent in sorted(consumers.get(current, ())):
            if dependent not in affected:
                if len(affected) >= 4096:
                    raise ValueError("candidate impact graph budget exceeded")
                affected.add(dependent)
                frontier.append(dependent)
    invalidations = invalidated_witnesses(
        witnesses if witnesses is not None else [], sorted(affected),
        source_revision=after)
    effects = []
    for item in sorted(set(changed)):
        if not item.startswith(".github/workflows/") or not item.endswith((".yml", ".yaml")):
            continue
        try:
            source = git(repo, "show", after + ":" + item, max_output=256000, timeout=45).decode("utf-8")
            effects.append(audit_workflow(source, path=item, revision=after))
        except (ValueError, OSError, UnicodeDecodeError, subprocess.TimeoutExpired):
            effects.append({"workflow": item, "status": "UNKNOWN_DELETED_OR_UNREADABLE",
                            "actual_effect": "NOT_OBSERVED", "authorization": "NONE"})
    plan = convergent_plan(contract, "G_R1_R4_COMPLETE")
    model = assess_cut(contract["nodes"], "G_R1_R4_COMPLETE", {})
    if graph is None:
        next_action = "SUPPLY_COMMITTED_ONTOLOGY_AND_REPRODUCE_GRAPH"
    elif need_base_graph and base_graph is None:
        next_action = "REPRODUCE_BASE_GRAPH_FOR_REMOVED_OR_RENAMED_SOURCE"
    elif gate["status"] == "BLOCKED":
        next_action = "REPAIR_BASE_PINNED_CONTINUOUS_POLICY"
    elif any(x["owner_status"] == "AMBIGUOUS_DECLARED_OWNER" for x in product_context):
        next_action = "QUALIFY_CONFLICTING_PRODUCT_OWNERS"
    elif intent_digest is None:
        next_action = "DECLARE_CHANGE_SPECIFIC_HUMAN_INTENT"
    elif imports_unknown:
        next_action = "INVESTIGATE_UNRESOLVED_STATIC_OR_DYNAMIC_CONSUMERS"
    elif any(x["state"] == "INVALIDATED_BY_CHANGED_SOURCE" for x in invalidations["witnesses"]):
        next_action = "REEXECUTE_AFFECTED_WITNESSES_WITH_INDEPENDENT_ORACLES"
    elif effects:
        next_action = "OBTAIN_TRUSTED_WORKFLOW_EFFECT_READBACK"
    else:
        next_action = "VALIDATE_BEHAVIORAL_MUTANTS_AND_FULL_R1_R4_PILOTS"
    result = {
        "schema": "cora-contextual-devops/1", "phase": phase,
        "base_commit": before, "head_commit": after,
        "continuous_gate": gate,
        "canonical_lattice": {"source_goal": "G_SOURCE_CONVERGENCE",
                              "complete_goal": "G_R1_R4_COMPLETE",
                              "source_cut": plan["source_locals"],
                              "external_cut": plan["external_locals"],
                              "model_complete_status": model["status"],
                              "complete_dod": "BLOCKED_EXTERNAL"},
        "contract_digest": domain_hash("CORA:convergence-policy:1", contract),
        "contract_authority": "PR_EDITABLE_PROFILE_NOT_BASE_HOST_AUTHORITY",
        "intent_digest": intent_digest,
        "intent_status": ("CALLER_SUPPLIED_UNVERIFIED_BOUND_TO_BASE_HEAD"
                          if intent_digest else "BLOCKED_MISSING_PER_CHANGE_INTENT"),
        "changed_paths": changed, "candidate_affected_paths": sorted(affected),
        "owner_candidates": product_context,
        "candidate_graph_source": graph["graph_digest"] if graph else None,
        "base_candidate_graph_source": base_graph["graph_digest"] if base_graph else None,
        "base_candidate_graph_required": need_base_graph,
        "base_graph_problem": base_graph_problem,
        "unresolved_imports": imports_unknown,
        "graph_problem": graph_problem, "invalidation": invalidations,
        "workflow_effects": effects,
        "mutations": "NOT_EXECUTED",
        "target_test_oracle": "NOT_EXECUTED",
        "private_repositories": "NOT_OBSERVED",
        "external_approval": "BLOCKED_EXTERNAL",
        "next_action": next_action,
        "status": ("DEBT_BLOCKED" if graph is None or gate["status"] == "BLOCKED"
                   or (need_base_graph and base_graph is None) or intent_digest is None
                   else "SOURCE_OBSERVED_REVIEW_REQUIRED"),
        "authorization": "NONE",
    }
    result["digest"] = domain_hash("CORA:contextual-devops:1", result)
    return result


def verify_contextual_gate(repo: Path, report: dict, *,
                           contract: dict, witnesses: list[dict] | None = None,
                           intent: str | None = None) -> bool:
    """Replay against actual committed Git objects, not a receipt hash alone."""
    if not isinstance(report, dict) or report.get("schema") != "cora-contextual-devops/1":
        raise ValueError("unknown contextual gate format")
    expected = evaluate_contextual(
        repo, report["base_commit"], report["head_commit"],
        contract=contract, phase=report["phase"],
        with_debt=report["continuous_gate"]["debt_delta"] is not None,
        witnesses=witnesses, intent=intent)
    if expected != report:
        raise ValueError("contextual report differs from actual Git/source policy")
    return True

# P0 is a source-bound development programme, not a new release or graph owner.
SELF_P0 = '.cora/contracts/dod/self-governing-portable-development-v1.json'
SELF_P0_SCHEMA = 'cora-self-governing-portable-development/1'
SELF_P0_REPORT = 'cora-self-development-plan/1'


def _validate_self_program(document: dict, tracked: set[str]) -> None:
    """Validate normative topology and negative authority claims against committed owners."""
    from .reticulum import ordered_cut, assess_cut, EXTERNAL
    if (not isinstance(document, dict) or document.get('schema') != SELF_P0_SCHEMA
            or document.get('authority') != 'NONE'
            or document.get('product_go') is not False
            or document.get('release') != 'HOLD'
            or document.get('global_status') != 'OPEN'
            or document.get('baseline', {}).get('zip_has_git') is not False
            or document.get('baseline', {}).get('target_runtime_tested') is not False):
        raise ValueError('P0 source contract or authority invalid')
    nodes = document.get('nodes')
    expected_leaves = {f'L{i:02d}' for i in range(1, 33)}
    expected = {'A0', 'G0'} | {f'G{i}' for i in range(1, 9)} | expected_leaves
    if not isinstance(nodes, list) or len(nodes) != len(expected):
        raise ValueError('P0 incomplete nodes')
    if any(not isinstance(node, dict) or not isinstance(node.get('id'), str)
           for node in nodes):
        raise ValueError('P0 malformed nodes')
    by_id = {n['id']: n for n in nodes}
    if len(by_id) != len(nodes) or set(by_id) != expected:
        raise ValueError('P0 duplicate or missing node')
    if (by_id['A0'].get('kind') != 'ABSTRACT'
            or by_id['A0'].get('scope') != 'EXTERNAL'
            or by_id['A0'].get('depends_on') != ['G0']
            or by_id['G0'].get('kind') != 'GLOBAL'
            or by_id['G0'].get('scope') != 'EXTERNAL'
            or by_id['G0'].get('depends_on') != [f'G{i}' for i in range(1, 9)]):
        raise ValueError('P0 global AND contract drift')
    external_leaves = {f'L{i:02d}' for i in (12, 16, 20, 24, 27, 28, 30, 31, 32)}
    for i in range(1, 9):
        gate = by_id[f'G{i}']
        if (gate.get('kind') != 'INTERMEDIATE'
                or gate.get('depends_on') != [f'L{j:02d}' for j in range(i * 4 - 3, i * 4 + 1)]
                or gate.get('scope') != ('EXTERNAL' if i >= 7 else 'MIXED')):
            raise ValueError('P0 local AND edge or authority drift')
    for leaf in expected_leaves:
        item = by_id[leaf]
        if (item.get('kind') != 'LOCAL' or item.get('depends_on') != []
                or item.get('status') != 'OPEN'
                or item.get('scope') != ('EXTERNAL' if leaf in external_leaves else 'SOURCE')
                or not isinstance(item.get('oracle'), str)
                or len(item['oracle']) < 20 or 'ASSUMED_PASS' in item['oracle']
                or not isinstance(item.get('owner'), str)
                or not item['owner'].startswith('src/cora/')
                or item['owner'] not in tracked):
            raise ValueError('P0 unowned leaf or false witness')
    if len(ordered_cut(nodes, 'A0')) != 42:
        raise ValueError('P0 cut not complete')
    if assess_cut(nodes, 'A0', {})['status'] != EXTERNAL:
        raise ValueError('P0 external status incorrectly closable')
    golds = document.get('golds')
    if not isinstance(golds, list) or len(golds) != 12 or {
            g.get('id') for g in golds if isinstance(g, dict)} != {
            f'GOLD{i:02d}' for i in range(1, 13)}:
        raise ValueError('P0 gold inventory drift')
    for gold in golds:
        if (gold.get('transfer') != 'SEMANTIC_NOT_CODE'
                or gold.get('state') != 'CANDIDATE_NOT_IMPLEMENTED'
                or gold.get('owner') not in tracked
                or gold.get('leaf') not in expected_leaves
                or gold.get('origin_url') !=
                f"https://github.com/Luke883i/iKant_EDU/pull/{gold.get('origin_pr')}"):
            raise ValueError('P0 unauthorized gold promotion')
    phases = document.get('phases')
    if not isinstance(phases, list) or len(phases) != 7:
        raise ValueError('P0 phase count drift')
    by_phase = {p.get('id'): p for p in phases if isinstance(p, dict)}
    if len(by_phase) != 7 or set(by_phase) != {f'P{i}' for i in range(7)}:
        raise ValueError('P0 missing phase')
    all_leaves = []
    for i in range(7):
        phase = by_phase[f'P{i}']
        if (phase.get('status') != 'OPEN'
                or phase.get('depends_on') != ([f'P{i-1}'] if i else [])
                or not isinstance(phase.get('leaves'), list)):
            raise ValueError('P0 phase dependency drift')
        all_leaves.extend(phase['leaves'])
    if len(all_leaves) != 32 or set(all_leaves) != expected_leaves:
        raise ValueError('P0 phase coverage drift')
    if (document.get('portability', {}).get('unprofiled_manifest_status') != 'NOT_CONFIGURED_NOT_PASS'
            or document.get('portability', {}).get('must_not_write_target_root') is not True
            or any(value is not False for value in document.get('nonpromotion', {}).values())
            or len(document.get('nonpromotion', {})) != 6
            or document.get('minimality', {}).get('new_parallel_graph_engine') != 'FORBIDDEN'
            or document.get('science', {}).get('status') != 'NOT_RUN'
            or document.get('science', {}).get('claimed_causal_benefit') is not False
            or document.get('mutation_campaign', {}).get('kind') != 'FINITE_CONTRACT_MODEL_NOT_RUNTIME'
            or document.get('mutation_campaign', {}).get('physical_runtime_mutants') != 0):
        raise ValueError('P0 external outcome or evidence promotion')


def self_development_plan(repo: Path, revision: str = 'HEAD') -> dict:
    """Read original committed P0 and return a non-promoting, source-only plan."""
    from .reticulum import assess_cut
    repo = Path(repo).resolve(strict=True)
    commit = _commit(repo, revision)
    tree = git(repo, 'rev-parse', commit + '^{tree}', max_output=128, timeout=45).decode().strip()
    blob = git(repo, 'rev-parse', commit + ':' + SELF_P0, max_output=128, timeout=45).decode().strip()
    source = git(repo, 'show', commit + ':' + SELF_P0, max_output=256 * 1024, timeout=45)
    try:
        data = json.loads(source.decode('utf-8'))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError('P0 committed contract cannot be parsed') from exc
    tracked = set(git(repo, 'ls-tree', '-r', '--name-only', '-z', commit,
                       max_output=8 * 1024 * 1024, timeout=45).decode('utf-8').split('\0'))
    _validate_self_program(data, tracked)
    assessment = assess_cut(data['nodes'], 'A0', {})
    result = {'schema': SELF_P0_REPORT, 'commit': commit, 'tree': tree,
              'contract_path': SELF_P0, 'contract_blob': blob,
              'contract_digest': domain_hash('CORA:self-program-contract:1', data),
              'assessment': assessment, 'first_open_phase': 'P0',
              'gold_count': len(data['golds']), 'local_obligations': 32,
              'global_dod': 'HOLD', 'product_go': False,
              'classification': 'GIT_SOURCE_MODEL_NOT_INDEPENDENT_EXECUTION',
              'evidence': 'COMMITTED_SOURCE_READBACK_ONLY',
              'authority': 'NONE', 'independent_review': 'NOT_ATTESTED'}
    result['report_digest'] = domain_hash('CORA:self-development-plan:1', result)
    return result


def verify_self_development_plan(repo: Path, report: dict, revision: str = 'HEAD') -> bool:
    """Reopen Git objects, reject stale or tampered reports; never grant approval."""
    if not isinstance(report, dict) or report.get('schema') != SELF_P0_REPORT:
        raise ValueError('invalid P0 plan receipt')
    if report.get('commit') != _commit(Path(repo).resolve(strict=True), revision):
        raise ValueError('P0 receipt is not for requested exact source revision')
    if report != self_development_plan(repo, revision):
        raise ValueError('P0 plan receipt differs from committed source')
    return True
