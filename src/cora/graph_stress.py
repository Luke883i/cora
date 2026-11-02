"""Seeded model-graph mutations with independent fixed-point reachability oracle.

Mutates in-memory topology, not one million physical Git repositories.
"""
from __future__ import annotations
import hashlib
from .mutations import mix64, MASK
from .graph import explain_path

FAMILIES = (
    'remove_core_import', 'add_worker_import', 'rename_module', 'move_across_boundary',
    'add_optional_plugin', 'remove_deploy_edge', 'add_build_edge', 'cycle_imports',
    'duplicate_registry', 'shadowed_module', 'dynamic_import', 'external_consumer',
    'unknown_feature_flag', 'shared_library', 'orphaned_code', 'change_entrypoint',
    'fallback_backend', 'migration_only', 'test_only', 'release_only',
    'cross_repo_reference', 'generated_source', 'root_overlap', 'workflow_only',
)


def model_mutation(family: str, salt: int) -> tuple[list[tuple[str,str]], bool]:
    """Curated realistic topology mutation operators on six abstract entities."""
    edges=[('product','entrypoint'), ('entrypoint','service'), ('service','store')]
    uncertain=False
    if family in ('remove_core_import','orphaned_code'):
        edges.remove(('entrypoint','service'))
    elif family in ('add_worker_import','add_build_edge','shared_library'):
        edges.append(('worker','store'))
    elif family in ('rename_module','move_across_boundary'):
        edges[1]=('entrypoint','worker')
    elif family in ('cycle_imports','fallback_backend'):
        edges.append(('store','entrypoint'))
    elif family in ('duplicate_registry','shadowed_module'):
        edges.append(('entrypoint','worker'))
    elif family in ('remove_deploy_edge','change_entrypoint'):
        edges.remove(('product','entrypoint'))
    elif family in ('migration_only','test_only','release_only','workflow_only'):
        edges.append(('worker','service'))
    else:
        uncertain=True
    # Per-case variations in a secondary graph edge; fixed oracle is independent.
    if salt & 1:
        edges.append(('store','worker'))
    if salt & 2:
        edges.append(('worker','entrypoint'))
    if salt & 4:
        edges.append(('entrypoint','store'))
    return sorted(set(edges)), uncertain


def oracle_fixed_point(edges:list[tuple[str,str]], src:str, dst:str) -> bool:
    """Independent repeated-set expansion, deliberately not using explain_path/BFS."""
    reached={src}
    for _ in range(6):
        updated=reached | {b for a,b in edges if a in reached}
        if updated==reached:
            break
        reached=updated
    return dst in reached


def stress_graph(seed:int=883,cases:int=1_000_000) -> dict:
    if type(seed) is not int or type(cases) is not int or not 1<=cases<=10_000_000:
        raise ValueError('invalid stress inputs')
    digest=hashlib.sha256()
    mismatch=0
    counts={f:0 for f in FAMILIES}
    for i in range(cases):
        salt=mix64((seed^i)&MASK)
        family=FAMILIES[salt % len(FAMILIES)]
        edges,unknown=model_mutation(family,salt)
        edge_records=[{'source':a,'target':b,'kind':'synthetic_relation','evidence':f'{i:x}'} for a,b in edges]
        graph={'edges':edge_records}
        target=('worker' if (salt>>5)&1 else 'store')
        actual=explain_path(graph,'product',target)
        expected=oracle_fixed_point(edges,'product',target)
        witness=actual['edges']
        witness_valid=not actual['reachable_in_declared_graph'] or (all(x['source']==('product' if j==0 else witness[j-1]['target']) for j,x in enumerate(witness)) and (not witness or witness[-1]['target']==target) and (bool(witness) or target=='product'))
        if actual['reachable_in_declared_graph']!=expected or not witness_valid:
            mismatch+=1
        counts[family]+=1
        digest.update(i.to_bytes(8,'little')+salt.to_bytes(8,'little')+bytes([int(actual['reachable_in_declared_graph']),int(expected),int(unknown)]) + '|'.join(a+'>'+b for a,b in edges).encode()+b'\0')
    return {'schema':'cora-graph-stress/1','cases':cases,'seed':seed,'families':len(FAMILIES),'mismatches':mismatch,'distribution':counts,'stream_sha256':digest.hexdigest(),'oracle':'independent_fixed_point_topology','limits':['In-memory graph topology mutations; not one million physical repositories','No runtime semantics or static analysis completeness proof','Fixture-independent graph algorithm, but model edges are synthetic']}
