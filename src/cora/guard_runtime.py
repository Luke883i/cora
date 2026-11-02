"""Standalone stdlib-only deterministic CORA local PR guard.

This file is copied unchanged into .cora/verify.py by 'cora guard-install'.
No network, subprocess shell, or target code execution. Git is invoked read-only.
"""
from __future__ import annotations
import argparse
import ast
import json
import subprocess
import sys
from pathlib import Path

POLICY = 'cora-local-guard/1'
PROTECTED = ('.cora/', '.github/workflows/cora-architecture-guard.yml')


def _git(repo: Path,*args: str) -> bytes:
    p=subprocess.run(['git','-C',str(repo),*args],capture_output=True,timeout=45,check=False)
    if p.returncode:
        raise ValueError('git guard query failed: '+p.stderr.decode('utf-8','replace')[:160])
    return p.stdout


def _changes(repo:Path,base:str) -> list[tuple[str,str,str]]:
    # Name-status is NUL separated. Rename records have two paths.
    data=_git(repo,'diff','--no-ext-diff','--find-renames','--name-status','-z',base,'HEAD').split(b'\0')
    result=[];i=0
    while i<len(data):
        status=data[i].decode('ascii','strict');i+=1
        if not status:break
        if status[0] not in ('M','A','D','R','C','T'):
            raise ValueError('unsupported Git change status '+status)
        if i>=len(data):raise ValueError('malformed Git diff output')
        old=data[i].decode('utf-8');i+=1
        new=old
        if status[0] in ('R','C'):
            if i>=len(data):raise ValueError('malformed rename entry')
            new=data[i].decode('utf-8');i+=1
        result.append((status,old,new))
    return result


def _owner(path:str,products:list[dict]) -> list[str]:
    return [p['id'] for p in products if path==p['root'] or path.startswith(p['root']+'/')]


def verify(repo:Path,base:str|None=None) -> dict:
    repo=repo.resolve(strict=True)
    if _git(repo,'status','--porcelain=v1','-z','--untracked-files=all'):
        raise ValueError('guard refuses dirty working tree: commit changes before verification')
    path=repo/'.cora/policy.json'
    if path.is_symlink() or not path.is_file():raise ValueError('local guard policy missing')
    doc=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(doc,dict) or set(doc)!={'schema','baseline_commit','products','exceptions'} or doc['schema']!=POLICY:
        raise ValueError('invalid guard policy schema')
    products=doc['products']
    if not isinstance(products,list) or not isinstance(doc['exceptions'],list):raise ValueError('invalid policy collections')
    for p in products:
        if set(p)!={'id','root','module_prefix'} or not all(isinstance(v,str) and v for v in p.values()):
            raise ValueError('invalid product policy entry')
        if p['root'].startswith('/') or '..' in p['root'].split('/') or '\\' in p['root']:
            raise ValueError('unsafe product path')
    if doc['exceptions']:
        raise ValueError('exceptions require independent protection and are unsupported in PR-06')
    if len(set(p['id'] for p in products))!=len(products) or len(set(p['module_prefix'] for p in products))!=len(products):
        raise ValueError('duplicate product identity/prefix')
    for i,a in enumerate(products):
        for b in products[i+1:]:
            if a['root']==b['root'] or a['root'].startswith(b['root']+'/') or b['root'].startswith(a['root']+'/'):
                raise ValueError('overlapping product roots')
    base=base or doc['baseline_commit']
    # Validate commit exists before interpreting any changes.
    _git(repo,'rev-parse','--verify','--end-of-options',base+'^{commit}')
    changes=_changes(repo,base)
    # Bootstrap exception only when policy did not exist at the trusted base.
    p=subprocess.run(['git','-C',str(repo),'cat-file','-e',base+':.cora/policy.json'],capture_output=True,check=False)
    bootstrap=p.returncode!=0
    violations=[]
    def add(kind,source,detail):violations.append({'kind':kind,'path':source,'detail':detail})
    # The verifier can never prove that its own initial installation is trusted:
    # a PR targeting a pre-installation base could replace BOTH the verifier and
    # its workflow. The first installation requires independent reviewer/check.
    if bootstrap:
        add('guard_bootstrap_requires_independent_review', '.cora/policy.json',
            'base_has_no_guard_policy; local verifier cannot approve its own installation')
    for status,old,new in changes:
        if old.startswith(PROTECTED) or new.startswith(PROTECTED):
            add('guard_or_workflow_changed',new,status)
        a=_owner(old,products);b=_owner(new,products)
        if status[0] in ('R','C') and a!=b:
            add('cross_product_move',new,old)
        if len(a)>1 or len(b)>1:
            add('ambiguous_product_ownership',new,'overlapping roots')
        if status[0] not in ('M','A','R','C') or not new.endswith('.py') or not b:
            continue
        file=repo/new
        if file.is_symlink() or not file.is_file():
            add('nonregular_python_source',new,'missing or symlink')
            continue
        if file.stat().st_size>2*1024*1024:
            add('oversized_python_source',new,'2MiB ceiling')
            continue
        try:
            tree=ast.parse(file.read_text(encoding='utf-8'))
        except (UnicodeDecodeError,SyntaxError,ValueError):
            add('unparseable_python_source',new,'syntax/encoding');continue
        for node in ast.walk(tree):
            if isinstance(node,ast.Call) and ((isinstance(node.func,ast.Name) and node.func.id=='__import__') or (isinstance(node.func,ast.Attribute) and node.func.attr=='import_module')):
                add('dynamic_import_unknown',new,str(node.lineno))
            mods=[]
            if isinstance(node,ast.Import):mods=[n.name for n in node.names]
            elif isinstance(node,ast.ImportFrom):
                if node.level:
                    add('relative_import_unknown',new,str(node.lineno))
                elif node.module:mods=[node.module]
            for mod in mods:
                for p in products:
                    if p['id'] not in b and (mod==p['module_prefix'] or mod.startswith(p['module_prefix']+'.')):
                        add('cross_product_import',new,mod+' -> '+p['id'])
    violations.sort(key=lambda x:(x['kind'],x['path'],x['detail']))
    return {'schema':'cora-local-guard-result/1','base':base,'head':_git(repo,'rev-parse','HEAD').decode().strip(),
            'changed_paths':len(changes),'bootstrap':bootstrap,'status':'PASS_SCOPED' if not violations else 'BLOCKED',
            'violations':violations, 'coverage':'Git-tracked changed paths and Python explicit/dynamic import expressions only; external consumers unsupported'}


def main(argv=None)->int:
    p=argparse.ArgumentParser(prog='cora-local-guard')
    p.add_argument('--repo',type=Path,default=Path('.'))
    p.add_argument('--base',default=None)
    args=p.parse_args(argv)
    try:
        result=verify(args.repo,args.base)
        print(json.dumps(result,indent=2,sort_keys=True))
        return 0 if result['status']=='PASS_SCOPED' else 2
    except (OSError,ValueError,subprocess.TimeoutExpired,json.JSONDecodeError) as exc:
        print('CORA LOCAL GUARD: '+str(exc),file=sys.stderr)
        return 3

if __name__=='__main__':raise SystemExit(main())
