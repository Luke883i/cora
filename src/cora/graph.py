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

# P2: Git-source projection over the original graph and canonical AND engine.
# No second engine or dependency scanner with runtime authority is created.
def unified_consumer_hypergraph(repo: Path, revision: str = 'HEAD', *,
                                parse_js: bool = False) -> dict:
    """Read a pinned source tree; expose typed consumer candidates and unknowns.

    This is a bounded, opt-in source projection. A missing candidate is never
    evidence of no runtime or external consumer, and no retirement is allowed.
    """
    from .reticulum import assess_cut, MODEL, BLOCKED
    from .workflow_rationalization import audit_workflows

    repo = Path(repo).resolve(strict=True)
    ledger = snapshot(repo, revision)
    validate_ledger(ledger)
    commit = ledger['commit']
    records = {r['path']: r for r in ledger['records']}
    if len(records) > 4096:
        raise ValueError('P2 bounded source census exceeded')
    paths = sorted(records)
    aliases: dict[str, set[str]] = {}
    for path in paths:
        if path.endswith('.py'):
            for alias in modules_for(path):
                aliases.setdefault(alias, set()).add(path)

    edges: dict[tuple[str, str, str], dict] = {}
    unknowns: set[tuple[str, str]] = set()
    generated: set[str] = set()
    source_bytes = 0
    parsed_python = 0
    parsed_workflows = 0
    source_suffix = ('.py', '.js', '.mjs', '.cjs', '.ts', '.tsx',
                     '.yml', '.yaml', '.json', '.toml', '.sh')

    def unknown(path: str, kind: str) -> None:
        unknowns.add((path, kind))

    def add(consumer: str, dependency: str, kind: str) -> None:
        if consumer not in records or dependency not in records:
            unknown(consumer, 'UNRESOLVED_SOURCE_REFERENCE')
            return
        key = (consumer, dependency, kind)
        edges[key] = {'consumer': 'file:' + consumer,
                      'dependency': 'file:' + dependency,
                      'kind': kind, 'evidence_path': consumer,
                      'evidence_blob_oid': records[consumer]['git_oid'],
                      'status': 'SOURCE_CANDIDATE_NOT_RUNTIME_EDGE'}
        if len(edges) > 16384:
            raise ValueError('P2 consumer edge budget exceeded')

    def resolve(path: str, name: str, role: str) -> None:
        matches = aliases.get(name, set())
        if len(matches) == 1:
            add(path, next(iter(matches)), role)
        elif len(matches) > 1:
            unknown(path, 'AMBIGUOUS_PYTHON_MODULE')
        else:
            unknown(path, 'UNRESOLVED_OR_EXTERNAL_PYTHON_MODULE')

    for path in paths:
        record = records[path]
        if (path.startswith(('generated/', 'gen/', 'dist/', 'build/')) or
                '/generated/' in path or '/gen/' in path):
            generated.add(path)
            unknown(path, 'GENERATED_PRODUCER_NOT_ATTESTED')
        if not path.endswith(source_suffix):
            continue
        size = record.get('size')
        if (record['status'] != 'observed_git_blob' or
                not isinstance(size, int) or size > 256 * 1024 or
                source_bytes + size > 16 * 1024 * 1024):
            unknown(path, 'SOURCE_READBACK_SKIPPED_OR_UNAVAILABLE')
            continue
        raw = git(repo, 'cat-file', 'blob', record['git_oid'],
                  max_output=256 * 1024 + 1)
        source_bytes += len(raw)
        try:
            content = raw.decode('utf-8')
        except UnicodeDecodeError:
            unknown(path, 'SOURCE_ENCODING_UNKNOWN')
            continue
        if not path.endswith('.py'):
            if path.endswith(('.js', '.mjs', '.cjs', '.ts', '.tsx')) and (
                    not parse_js or not path.endswith(('.js', '.mjs'))):
                unknown(path, 'NON_PYTHON_CONSUMERS_REQUIRE_ORIGINAL_PARSER')
            continue
        try:
            syntax = ast.parse(content, filename=path)
        except SyntaxError:
            unknown(path, 'PYTHON_PARSE_FAILED')
            continue
        parsed_python += 1
        role = ('GENERATED_STATIC_IMPORT_CANDIDATE' if path in generated else
                'TEST_STATIC_IMPORT_CANDIDATE' if path.startswith('tests/') else
                'PYTHON_STATIC_IMPORT_CANDIDATE')
        for expr in ast.walk(syntax):
            if isinstance(expr, ast.Call) and (
                isinstance(expr.func, ast.Name) and expr.func.id == '__import__' or
                isinstance(expr.func, ast.Attribute) and expr.func.attr == 'import_module'):
                unknown(path, 'DYNAMIC_PYTHON_IMPORT_UNKNOWN')
            if isinstance(expr, ast.Import):
                for item in expr.names:
                    resolve(path, item.name, role)
            elif isinstance(expr, ast.ImportFrom):
                if expr.level:
                    unknown(path, 'RELATIVE_PYTHON_IMPORT_UNKNOWN')
                    continue
                if expr.module:
                    resolve(path, expr.module, role)
                    for item in expr.names:
                        if item.name != '*' and expr.module + '.' + item.name in aliases:
                            resolve(path, expr.module + '.' + item.name, role)
                else:
                    unknown(path, 'IMPORT_TARGET_UNKNOWN')

    # The original Node parser may be requested explicitly, never executed by default.
    if parse_js:
        js = original_js_source_candidates(repo, commit)
        for row in js['candidateEdges']:
            if row['status'] == 'RESOLVED_EXACT_COMMITTED_GIT_PATH':
                add(row['path'], row['candidate'], 'STATIC_ESM_IMPORT_CANDIDATE')
            else:
                unknown(row['path'], 'ESM_' + row['status'])
        for row in js['unknown']:
            unknown(row['path'], 'ESM_' + row['kind'])
        for row in js['syntaxErrors']:
            unknown(row['path'], 'ESM_PARSE_FAILED')

    # Reuse the original partial YAML/source workflow owner, not a second parser.
    try:
        workflows = audit_workflows(repo, commit)
    except (ValueError, KeyError, TypeError) as exc:
        workflows = None
        unknown('.github/workflows', 'ORIGINAL_WORKFLOW_ANALYSIS_' + type(exc).__name__.upper())
    if workflows is not None:
        parsed_workflows = workflows['workflow_count']
        for workflow in workflows['workflows']:
            target = workflow['path']
            for source in workflow['in_repo_callers']:
                add(source, target, 'WORKFLOW_REUSABLE_CALL_CANDIDATE')
            for source in workflow['other_literal_references']:
                add(source, target, 'WORKFLOW_LITERAL_REFERENCE_CANDIDATE')
            if workflow['flags']:
                unknown(target, 'PARTIAL_WORKFLOW_YAML_OR_DYNAMIC_CONSUMER')
        if not workflows['source_scan_complete']:
            unknown('.github/workflows', 'INCOMPLETE_WORKFLOW_SOURCE_SCAN')

    incoming: dict[str, list[dict]] = {}
    for edge in edges.values():
        incoming.setdefault(edge['dependency'][5:], []).append(edge)
    hyperedges = [
        {'dependency': 'file:' + path, 'operator': 'AND',
         'source_consumers': sorted(e['consumer'] for e in incoming[path]),
         'candidate_kinds': sorted({e['kind'] for e in incoming[path]}),
         'external_consumer_closure': 'UNKNOWN_NOT_ABSENT',
         'safe_to_delete': False}
        for path in sorted(incoming)
    ]
    nodes = [
        {'id': 'P2_G0', 'scope': 'EXTERNAL',
         'depends_on': ['P2_G1', 'P2_G2', 'P2_G3', 'P2_G4']},
    ]
    leaves = [
        ('P2_G1', ('L_GIT_SHA', 'L_GIT_CENSUS', 'L_BOUNDED_SOURCE')),
        ('P2_G2', ('L_PYTHON', 'L_TESTS', 'L_WORKFLOWS')),
        ('P2_G3', ('L_GENERATED', 'L_DYNAMIC_UNKNOWN', 'L_TYPED_HYPEREDGES')),
        ('P2_G4', ('L_REPLAY', 'L_EXTERNAL_CONSUMERS', 'L_INDEPENDENT_REVIEW')),
    ]
    for gate, deps in leaves:
        nodes.append({'id': gate, 'scope': 'EXTERNAL' if gate == 'P2_G4' else 'SOURCE',
                      'depends_on': list(deps)})
        for item in deps:
            nodes.append({'id': item,
                          'scope': ('EXTERNAL' if item in
                                    ('L_EXTERNAL_CONSUMERS', 'L_INDEPENDENT_REVIEW')
                                    else 'SOURCE'), 'depends_on': []})
    observations = {n['id']: MODEL for n in nodes
                    if not n['depends_on'] and n['scope'] != 'EXTERNAL'}
    if any(kind in ('PYTHON_PARSE_FAILED', 'SOURCE_READBACK_SKIPPED_OR_UNAVAILABLE',
                    'SOURCE_ENCODING_UNKNOWN') for _, kind in unknowns):
        observations['L_PYTHON'] = BLOCKED
        observations['L_BOUNDED_SOURCE'] = BLOCKED
    if workflows is None or not workflows['source_scan_complete']:
        observations['L_WORKFLOWS'] = BLOCKED
    if any(kind in ('DYNAMIC_PYTHON_IMPORT_UNKNOWN',
                     'ESM_DYNAMIC_IMPORT_CANDIDATE',
                     'ESM_COMMONJS_REQUIRE_CANDIDATE') for _, kind in unknowns):
        observations['L_DYNAMIC_UNKNOWN'] = BLOCKED
    # A constructed report has not replayed itself; only a separate verifier can.
    observations['L_REPLAY'] = BLOCKED
    if len(unknowns) > 8192:
        raise ValueError('P2 unknown ledger budget exceeded')
    # No runtime observation, even when every bounded source scan was successful.
    cut = assess_cut(nodes, 'P2_G0', observations)
    result = {'schema': 'cora-unified-consumer-hypergraph/1',
              'commit': commit, 'ledger_digest': ledger['ledger_digest'],
              'file_count': len(paths), 'python_sources_parsed': parsed_python,
              'workflow_sources_seen': parsed_workflows,
              'source_bytes_read': source_bytes,
              'edges': sorted(edges.values(), key=lambda e: (
                  e['dependency'], e['consumer'], e['kind'])),
              'hyperedges': hyperedges,
              'generated_path_candidates': sorted(generated),
              'unknowns': [{'path': p, 'kind': k} for p, k in sorted(unknowns)],
              'coverage': {'python': 'GIT_STATIC_AST_CANDIDATES',
                           'tests': 'GIT_STATIC_AST_CANDIDATES',
                           'workflows': 'REUSED_ORIGINAL_PARTIAL_YAML_ANALYZER',
                           'generated': 'PATH_CANDIDATE_NOT_GENERATOR_PROOF',
                           'non_python': 'PARSER_REQUIRED_UNKNOWN',
                           'dynamic': 'UNKNOWN_NOT_ABSENT',
                           'external': 'BLOCKED_EXTERNAL',
                           'runtime': 'NOT_ATTESTED'},
              'and_assessment': cut,
              'global_status': cut['status'],
              'authority': 'NONE', 'safe_deletion_proven': False}
    result['graph_digest'] = domain_hash('CORA:unified-consumer-hypergraph:1', result)
    return result


def verify_unified_consumer_hypergraph(repo: Path, report: dict, *,
                                       parse_js: bool = False) -> bool:
    """Recompute exact Git source, and reject stale/tampered output."""
    if not isinstance(report, dict) or report.get('schema') != 'cora-unified-consumer-hypergraph/1':
        raise ValueError('invalid unified consumer hypergraph receipt')
    digest = domain_hash('CORA:unified-consumer-hypergraph:1',
                         {k: v for k, v in report.items() if k != 'graph_digest'})
    if digest != report.get('graph_digest'):
        raise ValueError('unified consumer graph integrity mismatch')
    actual = unified_consumer_hypergraph(repo, report.get('commit', ''),
                                         parse_js=parse_js)
    if actual != report:
        raise ValueError('unified consumer graph differs from original committed source')
    return True


def original_js_source_candidates(repo: Path, commit: str) -> dict:
    """Invoke the existing packaged Node ESM parser, never target code."""
    import json
    import subprocess
    from importlib.resources import as_file, files as package_files

    resource = package_files('cora').joinpath('portable_js_imports.mjs')
    if not resource.is_file():
        raise ValueError('packaged JS source parser not available; source unknown')
    with as_file(resource) as parser:
        proc = subprocess.run(['node', '--experimental-vm-modules', str(parser),
                               str(repo), commit], capture_output=True, text=True,
                              timeout=120, check=False)
    if proc.returncode:
        raise ValueError('bounded JS parser failed: ' + proc.stderr[-160:])
    parsed = json.loads(proc.stdout)
    if (parsed.get('schema') != 'cora-js-static-source/1' or
            parsed.get('commit') != commit or parsed.get('authority') != 'NONE' or
            parsed.get('runtimeObserved') is not False or
            not isinstance(parsed.get('syntaxErrors'), list) or
            not isinstance(parsed.get('imports'), list) or
            not isinstance(parsed.get('unknown'), list) or
            parsed.get('scope') != 'PARSED_ESM_ONLY_DYNAMIC_AND_RUNTIME_UNKNOWN'):
        raise ValueError('invalid bounded JS source parser output')
    return parsed
