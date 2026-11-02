"""Materialize versioned independent local guard and limited CI workflow."""
from __future__ import annotations
import json
import re
from pathlib import Path
from .evidence import valid_path
from .git_snapshot import git
from .guard_runtime import verify

WORKFLOW = '''name: CORA | Architecture guard
on:
  pull_request:
permissions:
  contents: read
jobs:
  local-guard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
        with:
          fetch-depth: 0
      - name: Check architecture boundaries
        run: python3 .cora/verify.py --repo . --base "${{ github.event.pull_request.base.sha }}"
'''


def install_guard(repo:Path, products:list[str]) -> dict:
    repo=repo.resolve(strict=True)
    if git(repo,'status','--porcelain=v1','-z','--untracked-files=all'):
        raise ValueError('guard install requires clean checkout')
    product_defs=[]
    for spec in products:
        parts=spec.split('=',2)
        if len(parts)!=3:raise ValueError('product must be id=path=python.module_prefix')
        name,root,prefix=parts
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}',name) or not valid_path(root) or not re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*',prefix):
            raise ValueError('invalid product declaration')
        product_defs.append({'id':name,'root':root,'module_prefix':prefix})
    if not product_defs:raise ValueError('at least one explicit product declaration required')
    paths=[repo/'.cora/policy.json',repo/'.cora/verify.py',repo/'.github/workflows/cora-architecture-guard.yml']
    if any(p.exists() or p.is_symlink() for p in paths):
        raise ValueError('guard already installed or path collision; no overwrite')
    # Validate all definitions before any file creation.
    from .guard_runtime import POLICY
    if len({p['id'] for p in product_defs})!=len(product_defs) or len({p['module_prefix'] for p in product_defs})!=len(product_defs):
        raise ValueError('duplicate product declarations')
    for i,a in enumerate(product_defs):
        for b in product_defs[i+1:]:
            if a['root']==b['root'] or a['root'].startswith(b['root']+'/') or b['root'].startswith(a['root']+'/'):
                raise ValueError('nested/overlapping product roots')
    commit=git(repo,'rev-parse','HEAD').decode().strip()
    doc={'schema':POLICY,'baseline_commit':commit,'products':sorted(product_defs,key=lambda p:p['id']),'exceptions':[]}
    root=Path(__file__).with_name('guard_runtime.py')
    try:
        for path in paths:path.parent.mkdir(parents=True,exist_ok=True)
        paths[0].write_text(json.dumps(doc,sort_keys=True,indent=2)+'\n',encoding='utf-8')
        paths[1].write_bytes(root.read_bytes())
        paths[2].write_text(WORKFLOW,encoding='utf-8')
    except BaseException:
        for path in paths:
            if path.exists():path.unlink()
        raise
    return {'schema':'cora-guard-install/1','status':'CREATED_UNCOMMITTED','files':[p.relative_to(repo).as_posix() for p in paths],
            'bootstrap_commit':commit,'coverage':'local diff and Python changed-file explicit imports; requires independently protected CI required checks'}
