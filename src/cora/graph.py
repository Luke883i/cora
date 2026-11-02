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
