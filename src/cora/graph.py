"""Versioned evidence-linked graph; conservative imports, no runtime claims."""
from __future__ import annotations
import ast
from collections import deque
from pathlib import Path
from .evidence import domain_hash, validate_ledger
from .git_snapshot import snapshot, git
from .ontology import committed_ontology, members


def modules_for(path: str) -> set[str]:
    if not path.endswith('.py'):
        return set()
    names = set()
    for base in (path, path.removeprefix('src/')):
        s = base[:-3]
        if s.endswith('/__init__'):
            s = s[:-9]
        if s:
            names.add(s.replace('/', '.'))
    return names


def graph_from_commit(repo: Path, revision='HEAD', ontology_path='cora.ontology.json') -> dict:
    ledger = snapshot(repo, revision)
    validate_ledger(ledger)
    commit = ledger['commit']
    ont = committed_ontology(repo, commit, ontology_path)
    doc = ont['document']
    files = {r['path']:r for r in ledger['records']}
    nodes: dict[str,dict] = {}
    edges: dict[tuple[str,str,str,str],dict] = {}
    findings: list[dict] = []
    def node(key, kind, evidence):
        if key not in nodes:
            nodes[key] = {'id':key,'kind':kind,'evidence':evidence}
    def edge(source, target, kind, evidence):
        k=(source,target,kind,evidence)
        if k not in edges:
            edges[k]={'source':source,'target':target,'kind':kind,'evidence':evidence}
    def finding(kind, source, detail):
        findings.append({'kind':kind,'source':source,'detail':detail})
    root = 'repository:'+commit
    node(root,'repository',ledger['ledger_digest'])
    for path,r in sorted(files.items()):
        key = 'file:'+path
        node(key,'file',r['digest'])
        edge(root,key,'contains_file',r['digest'])
        if r['status'] != 'observed_git_blob':
            finding('unresolved_git_object',key,r['status'])
    for p in doc['products']:
        key='product:'+p['id'];node(key,'product',ont['digest'])
        edge(root,key,'declares_product',ont['digest'])
        for path in sorted(files):
            if members(path,p['roots']):
                edge(key,'file:'+path,'declared_product_membership',ont['digest'])
        for e in p['entrypoints']:
            if e in files:
                edge(key,'file:'+e,'declared_entrypoint',ont['digest'])
            else:
                finding('missing_entrypoint',key,e)
    for s in doc['software']:
        key='software:'+s['id'];node(key,'software',ont['digest'])
        edge(root,key,'declares_software',ont['digest'])
        for pid in s['product_ids']:
            edge(key,'product:'+pid,'declared_implements_product',ont['digest'])
        for path in sorted(files):
            if members(path,s['roots']):
                edge(key,'file:'+path,'declared_software_membership',ont['digest'])
    for path,r in sorted(files.items()):
        owners=[p['id'] for p in doc['products'] if members(path,p['roots'])]
        if len(owners)>1: finding('ambiguous_product_membership','file:'+path,','.join(sorted(owners)))
    mod: dict[str,set[str]]={}
    for path,r in files.items():
        if r['status']=='observed_git_blob':
            for alias in modules_for(path): mod.setdefault(alias,set()).add(path)
    for path,r in sorted(files.items()):
        if r['status']!='observed_git_blob' or not path.endswith('.py'):
            continue
        if r['size'] is None or r['size']>1024*1024:
            finding('python_parse_skipped','file:'+path,'size_bound');continue
        blob=git(repo,'cat-file','blob',r['git_oid'],max_output=1024*1024)
        try:
            syntax=ast.parse(blob.decode('utf-8'),filename=path)
        except (SyntaxError,UnicodeDecodeError):
            finding('python_parse_failed','file:'+path,'syntax_or_encoding');continue
        for expr in ast.walk(syntax):
            if isinstance(expr,ast.Call) and ((isinstance(expr.func,ast.Name) and expr.func.id=='__import__') or (isinstance(expr.func,ast.Attribute) and expr.func.attr=='import_module')):
                finding('dynamic_import_unknown','file:'+path,str(expr.lineno))
            if not isinstance(expr,(ast.Import,ast.ImportFrom)):
                continue
            if isinstance(expr,ast.ImportFrom) and expr.level:
                finding('relative_import_unresolved','file:'+path,str(expr.lineno));continue
            imports=[a.name for a in expr.names] if isinstance(expr,ast.Import) else [expr.module or '']
            for name in imports:
                if not name:
                    finding('import_unresolved','file:'+path,str(expr.lineno));continue
                matches=mod.get(name,set())
                if len(matches)==1:
                    target=next(iter(matches))
                    edge('file:'+path,'file:'+target,'static_import_candidate',r['digest']+':'+str(expr.lineno))
                elif len(matches)>1:
                    finding('ambiguous_import','file:'+path,name+':'+str(expr.lineno))
                else:
                    finding('import_unresolved','file:'+path,name+':'+str(expr.lineno))
                if isinstance(expr,ast.ImportFrom) and expr.names:
                    # Imported names may denote attributes or submodules; never silently assert either.
                    for alias in expr.names:
                        if mod.get(name+'.'+alias.name):
                            finding('from_import_submodule_ambiguous','file:'+path,name+'.'+alias.name+':'+str(expr.lineno))
    payload={'schema':'cora-graph/1','commit':commit,'ledger_digest':ledger['ledger_digest'],'ontology_digest':ont['digest'],'ontology_source':ont['source'], 'nodes':sorted(nodes.values(),key=lambda x:x['id']),'edges':sorted(edges.values(),key=lambda x:(x['source'],x['target'],x['kind'],x['evidence'])),'findings':sorted(findings,key=lambda x:(x['kind'],x['source'],x['detail'])),'coverage':{'repository_files':'from_git_ledger','product_and_software':'explicit_declarations','python_imports':'partial_candidate_only','dynamic_imports':'unknown','runtime':'unsupported','external_consumers':'unsupported','non_python_imports':'unsupported'}}
    payload['graph_digest']=domain_hash('CORA:graph:1',payload)
    return payload


def explain_path(graph:dict, source:str, target:str) -> dict:
    by_source:dict[str,list[dict]]={}
    for e in graph['edges']:
        by_source.setdefault(e['source'],[]).append(e)
    todo=deque([source]);prev={source:None}
    while todo:
        cur=todo.popleft()
        if cur==target:break
        for e in sorted(by_source.get(cur,[]),key=lambda x:(x['target'],x['kind'],x['evidence'])):
            if e['target'] not in prev:
                prev[e['target']]=(cur,e)
                todo.append(e['target'])
    path=[]
    if target in prev:
        cur=target
        while cur!=source:
            prev_node,e=prev[cur]
            path.append(e)
            cur=prev_node
        path.reverse()
    return {'schema':'cora-explanation/1','source':source,'target':target,'reachable_in_declared_graph':target in prev,'edges':path,'caveat':'Graph reachability is not runtime use, non-reachability is not safe deletion.'}


def verify_graph_against_git(repo: Path, graph: dict) -> bool:
    """Require an exact reproduction from Git, not just a self-recomputed digest."""
    if not isinstance(graph, dict) or graph.get('schema') != 'cora-graph/1':
        raise ValueError('invalid graph schema')
    commit = graph.get('commit')
    source = graph.get('ontology_source')
    if not isinstance(commit, str) or not isinstance(source, str) or not source.startswith(commit+':'):
        raise ValueError('invalid graph provenance')
    digest = graph.get('graph_digest')
    if digest != domain_hash('CORA:graph:1', {k:v for k,v in graph.items() if k!='graph_digest'}):
        raise ValueError('invalid graph digest')
    actual = graph_from_commit(repo, commit, source[len(commit)+1:])
    if actual != graph:
        raise ValueError('graph differs from committed Git evidence')
    return True

# P2 opt-in projection: one source graph, one workflow owner, one AND kernel.
def consumer_hypergraph(repo: Path, revision: str = 'HEAD', *,
                        ontology_path: str = 'cora.ontology.json') -> dict:
    """Inventory typed *candidates* from pinned Git; never infer safe deletion."""
    from .reticulum import assess_cut, MODEL, BLOCKED
    from .workflow_rationalization import audit_workflows
    from .evidence import valid_path

    if not valid_path(ontology_path):
        raise ValueError('unsafe P2 ontology path')
    repo = Path(repo).resolve(strict=True)
    ledger = snapshot(repo, revision)
    validate_ledger(ledger)
    commit = ledger['commit']
    files = {r['path']: r for r in ledger['records']}
    if len(files) > 8192:
        raise ValueError('P2 source census exceeded')
    seen = set()
    edges, unknown = [], set()
    def add(source, target, kind, origin):
        if source not in files or target not in files:
            unknown.add((source, 'UNRESOLVED_SOURCE_REFERENCE'))
            return
        key = (source, target, kind)
        if key in seen:
            return
        seen.add(key)
        edges.append({'consumer': 'file:' + source, 'dependency': 'file:' + target,
                      'kind': kind, 'evidence': origin,
                      'consumer_blob': files[source]['git_oid'],
                      'claim': 'STATIC_CANDIDATE_NOT_RUNTIME_DEPENDENCY'})
        if len(edges) > 16384:
            raise ValueError('P2 edge budget exceeded')

    source_graph = None
    if ontology_path not in files:
        unknown.add((ontology_path, 'ONTOLOGY_NOT_CONFIGURED_IN_COMMIT'))
    else:
        try:
            source_graph = graph_from_commit(repo, commit, ontology_path)
        except (ValueError, KeyError) as exc:
            unknown.add((ontology_path, 'ONTOLOGY_OR_GRAPH_' + type(exc).__name__.upper()))
    if source_graph:
        for edge in source_graph['edges']:
            if edge['kind'] != 'static_import_candidate':
                continue
            source, target = edge['source'][5:], edge['target'][5:]
            kind = ('GENERATED_PYTHON_CONSUMER_CANDIDATE'
                    if '/generated/' in '/' + source or source.startswith('generated/')
                    else 'TEST_PYTHON_CONSUMER_CANDIDATE'
                    if source.startswith('tests/') else 'PYTHON_CONSUMER_CANDIDATE')
            add(source, target, kind, edge['evidence'])
        for finding in source_graph['findings']:
            unknown.add((finding['source'].removeprefix('file:'),
                         'GRAPH_' + finding['kind'].upper()))
    try:
        workflows = audit_workflows(repo, commit)
    except (ValueError, KeyError) as exc:
        workflows = None
        unknown.add(('.github/workflows', 'WORKFLOW_ANALYZER_' + type(exc).__name__.upper()))
    if workflows:
        for wf in workflows['workflows']:
            for caller in wf['in_repo_callers']:
                add(caller, wf['path'], 'REUSABLE_WORKFLOW_CALL_CANDIDATE', wf['git_oid'])
            for caller in wf['other_literal_references']:
                add(caller, wf['path'], 'WORKFLOW_LITERAL_REFERENCE_CANDIDATE', wf['git_oid'])
            if wf['flags']:
                unknown.add((wf['path'], 'WORKFLOW_PARTIAL_YAML_OR_HOST_UNKNOWN'))
        if not workflows['source_scan_complete']:
            unknown.add(('.github/workflows', 'WORKFLOW_CONSUMER_SCAN_INCOMPLETE'))
    generated = sorted(p for p in files if p.startswith(('gen/', 'generated/', 'dist/', 'build/'))
                       or '/generated/' in p)
    for path in generated:
        unknown.add((path, 'GENERATED_PRODUCER_UNATTESTED'))
    for path in files:
        if path.endswith(('.js', '.mjs', '.cjs', '.ts', '.tsx')):
            unknown.add((path, 'NON_PYTHON_PARSER_NOT_INVOKED'))
    edges.sort(key=lambda e: (e['dependency'], e['consumer'], e['kind'], e['evidence']))
    incoming = {}
    for edge in edges:
        incoming.setdefault(edge['dependency'], []).append(edge)
    groups = [{'dependency': target, 'operator': 'AND',
               'candidate_consumers': sorted(set(e['consumer'] for e in inbound)),
               'candidate_kinds': sorted(set(e['kind'] for e in inbound)),
               'external_and_runtime_completeness': 'UNKNOWN', 'safe_to_delete': False}
              for target, inbound in sorted(incoming.items())]
    gates = {
        'P2_G1': ('L_GIT', 'L_OWNERS', 'L_BOUNDS'),
        'P2_G2': ('L_PYTHON', 'L_TEST', 'L_WORKFLOW'),
        'P2_G3': ('L_GENERATED', 'L_DYNAMIC', 'L_HYPEREDGES'),
        'P2_G4': ('L_REPLAY', 'L_EXTERNAL', 'L_REVIEW'),
    }
    nodes = [{'id': 'P2_G0', 'depends_on': list(gates), 'scope': 'EXTERNAL'}]
    for gate, leaves in gates.items():
        nodes.append({'id': gate, 'depends_on': list(leaves),
                      'scope': 'EXTERNAL' if gate == 'P2_G4' else 'SOURCE'})
        nodes.extend({'id': leaf, 'depends_on': [],
                      'scope': 'EXTERNAL' if leaf in ('L_EXTERNAL', 'L_REVIEW') else 'SOURCE'}
                     for leaf in leaves)
    obs = {leaf: MODEL for leaves in gates.values() for leaf in leaves}
    if source_graph is None:
        obs['L_PYTHON'] = BLOCKED
        obs['L_TEST'] = BLOCKED
    if workflows is None or not workflows['source_scan_complete']:
        obs['L_WORKFLOW'] = BLOCKED
    obs['L_REPLAY'] = BLOCKED  # cannot self-attest its later independent verification
    cut = assess_cut(nodes, 'P2_G0', {key: val for key, val in obs.items()
                                   if key not in ('L_EXTERNAL', 'L_REVIEW')})
    result = {'schema': 'cora-consumer-hypergraph/1', 'commit': commit,
              'ontology_path': ontology_path, 'ledger_digest': ledger['ledger_digest'],
              'source_graph_digest': source_graph['graph_digest'] if source_graph else None,
              'workflow_digest': workflows['receipt_sha256'] if workflows else None,
              'file_count': len(files), 'edges': edges, 'hyperedges': groups,
              'generated_path_candidates': generated,
              'unknowns': [{'path': p, 'kind': k} for p, k in sorted(unknown)],
              'assessment': cut, 'global_status': cut['status'],
              'authority': 'NONE', 'safe_to_delete': False,
              'scope': 'GIT_STATIC_CANDIDATES_UNCLOSED_RUNTIME_AND_EXTERNAL'}
    result['digest'] = domain_hash('CORA:consumer-hypergraph:1', result)
    return result


def verify_consumer_hypergraph(repo: Path, report: dict) -> bool:
    """Independent of the report digest: replay original committed Git source."""
    if not isinstance(report, dict) or report.get('schema') != 'cora-consumer-hypergraph/1':
        raise ValueError('invalid P2 consumer graph receipt')
    if report.get('digest') != domain_hash('CORA:consumer-hypergraph:1',
                                           {k: v for k, v in report.items() if k != 'digest'}):
        raise ValueError('P2 consumer receipt digest mismatch')
    expected = consumer_hypergraph(repo, report.get('commit', ''),
                                   ontology_path=report.get('ontology_path', ''))
    if expected != report:
        raise ValueError('P2 consumer graph differs from immutable Git source')
    return True
