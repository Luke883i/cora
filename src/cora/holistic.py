"""CORA holistic, top-down, *observational* repository archaeology.

Combines Git, declared product/software roles, partial Python import graph,
manifest declarations, and longitudinal co-change. Neither co-change nor silence
in one analyzer is proof of runtime use, non-use, or safe deletion.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .evidence import domain_hash, valid_path
from .git_snapshot import snapshot
from .graph import graph_from_commit
from .artifact_roles import artifact_audit
from .adapters import adapter_audit
from .selection import select_file
from .archaeology import mine_history

SCHEMA = 'cora-holistic/1'
PROTECTED = frozenset({'PRODUCT_CONTRACT','ENTRYPOINT','TEST','CONTRACT_VERIFIER','CONTRACT_SCHEMA','FIXTURE','WORKFLOW','POLICY','GOVERNANCE','RELEASE_TOOL','BUILD_METADATA','ARTIFACT_INDEX','LICENSE','OBSERVABILITY'})


def _coupling_groups(paths:list[str], pair_rows:list[dict], by_path:dict, ownership:dict) -> tuple[list[list[str]],list[dict]]:
    """Deterministic bounded union-find; never merge cross-product owner groups."""
    parent={p:p for p in paths}
    sizes={p:1 for p in paths}
    def root(p):
        while parent[p]!=p:
            p=parent[p]
        return p
    candidates=[]
    for r in pair_rows:
        a,b,n=r['a'],r['b'],r['count']
        if a not in parent or b not in parent:
            continue
        ta=len(by_path.get(a,[]));tb=len(by_path.get(b,[]))
        if not ta or not tb:continue
        j=n/(ta+tb-n) if ta+tb>n else 0
        cross=bool(ownership.get(a) and ownership.get(b) and ownership[a]!=ownership[b])
        candidates.append({'a':a,'b':b,'cochanged_commits':n,'jaccard':round(j,3),
                           'cross_product_boundary':cross,
                           'kind':'HISTORICAL_ASSOCIATION_NOT_RUNTIME_EDGE'})
    for x in sorted(candidates,key=lambda x:(-x['jaccard'],-x['cochanged_commits'],x['a'],x['b'])):
        if x['cross_product_boundary'] or x['cochanged_commits']<2 or x['jaccard']<0.5:
            continue
        a=root(x['a']);b=root(x['b'])
        if a!=b and sizes[a]+sizes[b] <= 24:
            if a>b:a,b=b,a
            parent[b]=a;sizes[a]+=sizes[b]
    buckets:dict[str,list[str]] = defaultdict(list)
    for p in paths:buckets[root(p)].append(p)
    return sorted((sorted(v) for v in buckets.values()), key=lambda g:(g[0],len(g))), candidates


def holistic_audit(repo:Path, revision:str='HEAD', *, max_commits:int=256,
                   focus:str|None=None, pr_index:dict|None=None) -> dict:
    repo=Path(repo).resolve(strict=True)
    ledger=snapshot(repo,revision)
    sha=ledger['commit']
    history=mine_history(repo,sha,max_commits=max_commits,pr_index=pr_index)
    files={r['path']:r for r in ledger['records']}
    paths=sorted(files)
    failures=[]
    try:
        graph=graph_from_commit(repo,sha)
    except (ValueError, KeyError) as exc:
        graph=None
        failures.append({'method':'python_graph_and_ontology','status':'UNAVAILABLE','reason':type(exc).__name__})
    try:
        roles=artifact_audit(repo,sha)
    except (ValueError,KeyError) as exc:
        roles=None
        failures.append({'method':'artifact_roles','status':'UNAVAILABLE','reason':type(exc).__name__})
    adapter=adapter_audit(repo,sha)
    role_by_path={r['path']:r for r in roles['artifacts']} if roles else {}
    graph_edges=graph['edges'] if graph else []
    incoming:dict[str,int]=defaultdict(int)
    outgoing:dict[str,int]=defaultdict(int)
    owner:dict[str,set[str]]=defaultdict(set)
    for e in graph_edges:
        if e['kind']=='static_import_candidate':
            incoming[e['target'][5:]]+=1;outgoing[e['source'][5:]]+=1
        if e['kind']=='declared_product_membership':
            owner[e['target'][5:]].add(e['source'][8:])
    for p in paths:owner.setdefault(p,set())
    adapter_by_path={o['path']:o for o in adapter['observations']}
    selected=[]
    for p in paths:
        r=files[p]; declared=role_by_path.get(p,{'roles':[],'status':'UNDECLARED'})
        rs=sorted(declared['roles']); hits=len(history['touched_commits'].get(p,[]))
        flags=[]
        if r['status']!='observed_git_blob':flags.append('GIT_OBJECT_UNRESOLVED')
        if not rs:flags.append('ROLE_DECLARATION_MISSING')
        if len(owner[p])>1:flags.append('PRODUCT_BOUNDARY_AMBIGUOUS')
        if rs and PROTECTED.intersection(rs) and incoming[p]==0:
            flags.append('POSSIBLE_UNCONNECTED_GOLD_REVIEW')
        if not rs and incoming[p]==0 and hits<=1:
            flags.append('POSSIBLE_SCAFFOLD_WASTE_REVIEW')
        if hits==0:flags.append('HISTORY_WINDOW_NO_TOUCH_OBSERVED')
        if graph is None:flags.append('GRAPH_NOT_AVAILABLE')
        selected.append({'path':p,'blob_record_digest':r['digest'],'declared_roles':rs,
                         'declared_products':sorted(owner[p]),'incoming_static_import_candidates':incoming[p],
                         'outgoing_static_import_candidates':outgoing[p],
                         'observed_commit_touches':hits,
                         'manifest_adapter_state':adapter_by_path.get(p,{}).get('status','not_applicable'),
                         'review_flags':sorted(flags),'safe_to_delete':False,
                         'recommended_action':'INVESTIGATE_OR_RETAIN_ONLY'})
    groups, temporal=_coupling_groups(paths,history['cochange_pairs'],history['touched_commits'],
                                      {p:tuple(sorted(owner[p])) for p in paths})
    group_rows=[]
    rows={x['path']:x for x in selected}
    for i,group in enumerate(groups):
        pooled=sorted(set().union(*(set(rows[p]['declared_roles']) for p in group)))
        flags=sorted(set().union(*(set(rows[p]['review_flags']) for p in group)))
        kind='DOCUMENTED_OR_PROTECTED_DEVELOPMENT' if PROTECTED.intersection(pooled) else 'SOURCE_OR_UNCLASSIFIED_DEVELOPMENT'
        group_rows.append({'id':f'DEV-{i+1:04d}','paths':group,'declared_roles':pooled,
                           'kind':kind,'review_flags':flags,
                           'classification':'HYPOTHESIS_ONLY_NOT_DELETION_EVIDENCE'})
    details=None
    if focus is not None:
        if not valid_path(focus) or focus not in files:
            raise ValueError('focus must identify a tracked Git file')
        try:
            item=select_file(repo,focus,revision=sha)
            details={'path':focus,'selection_state':item['selection']['state'],
                     'selection_digest':item['selection_digest'],
                     'safe_deletion_proven':False}
        except (ValueError,KeyError) as exc:
            details={'path':focus,'selection_state':'DEBT_BLOCKED',
                     'unavailable_reason':type(exc).__name__,'safe_deletion_proven':False}
    report={
      'schema':SCHEMA,'commit':sha,'ledger_digest':ledger['ledger_digest'],
      'graph_digest':graph['graph_digest'] if graph else None,
      'artifact_report_digest':roles['report_digest'] if roles else None,
      'adapter_report_digest':adapter['report_digest'],
      'history_digest':history['digest'],'history':history,
      'files':selected,'development_groups':group_rows,
      'temporal_edges':temporal,'focused_file':details,
      'method_ledger':{
         'git_provenance':'APPLIED','git_archaeology':'APPLIED',
         'python_static_graph':'PARTIAL' if graph else 'NOT_AVAILABLE',
         'manifest_adapters':'PARTIAL',
         'artifact_roles':'DECLARATIONS_ONLY' if roles else 'NOT_AVAILABLE',
         'cochange_and_development_groups':'HEURISTIC_APPLIED',
         'per_file_selection':'APPLIED' if focus and details and 'selection_digest' in details else 'NOT_RUN',
         'runtime_telemetry':'NOT_ATTESTED',
         'AI_semantic_hypotheses':'NOT_EXECUTED_EXTERNAL_OPTION',
         'transformation_and_guard':'NOT_RUN_READ_ONLY_BOUNDARY',
         'release_and_million_case_stress':'NOT_RUN_SEPARATE_VERIFICATION'
      },
      'blockers':failures,
      'global_caveats':['cochange_does_not_imply_runtime_dependency',
                        'absence_of_observed_imports_does_not_prove_nonuse',
                        'rename_similarity_does_not_prove_symbol_identity',
                        'PR_identity_without_trusted_external_confirmation_is_unknown',
                        'incomplete_or_truncated_history_is_not_negative_evidence',
                        'external_consumers_and_dynamic_build_deploy_are_not_closed',
                        'no_deletion_or_automatic_quarantine_authority']
    }
    report['report_digest']=domain_hash('CORA:holistic:1',report)
    return report


def verify_holistic(repo:Path, report:dict) -> bool:
    if not isinstance(report,dict) or report.get('schema') != SCHEMA:
        raise ValueError('invalid holistic report')
    history=report['history']
    pr_entries={e['commit']:int(e['pr_association'][3:]) for e in history['events']
                if e.get('pr_association') and e['pr_association'].startswith('PR-')}
    pr={'schema':'cora-pr-index/1','commits':pr_entries} if pr_entries else None
    focus=report['focused_file']['path'] if report.get('focused_file') else None
    actual=holistic_audit(repo,report['commit'],max_commits=history['bounded_commits'],focus=focus,pr_index=pr)
    if actual != report:
        raise ValueError('holistic report cannot be replayed from committed Git state')
    return True
