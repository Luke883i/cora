"""PR-06: narrow doc-path rename, fail-closed plan and compensating rollback.

No general-purpose source-code refactor and no deletion. Untrusted plan files are
recomputed from the current clean Git checkout before being accepted.
"""
from __future__ import annotations

import hashlib
import json
import os
import shlex
import subprocess
import tempfile
from pathlib import Path

from .evidence import domain_hash, valid_path
from .git_snapshot import git

MAX_EDIT = 2 * 1024 * 1024
DOC_EXT = ('.md', '.txt', '.rst')


def _run(repo: Path, *args: str) -> bytes:
    return git(repo, *args)


def _tracked(repo: Path) -> list[str]:
    names = _run(repo, 'ls-files', '-z', '--cached').split(b'\0')
    out = []
    for p in names:
        if p:
            try:
                n = p.decode('utf-8')
            except UnicodeDecodeError as e:
                raise ValueError('non-UTF8 tracked path blocks scoped transformation') from e
            if not valid_path(n):
                raise ValueError('unsafe tracked path blocks transformation')
            out.append(n)
    if len(out) != len(set(out)):
        raise ValueError('duplicate tracked path')
    return sorted(out)


def _clean(repo: Path) -> None:
    if _run(repo, 'status', '--porcelain=v1', '-z', '--untracked-files=all'):
        raise ValueError('working tree or index is dirty; transformation requires clean checkout')


def _file(repo: Path, path: str) -> Path:
    if not valid_path(path):
        raise ValueError('unsafe relative path')
    item = repo / path
    if item.is_symlink() or item.resolve().is_relative_to(repo.resolve()) is False:
        raise ValueError('symlink or path escape blocked')
    for parent in item.parents:
        if parent == repo:
            break
        if parent.is_symlink():
            raise ValueError('symlink parent blocked')
    return item


def _hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def plan_rename_docs(repo: Path, old: str, new: str) -> dict:
    repo = repo.resolve(strict=True)
    if not old.endswith(DOC_EXT) or not new.endswith(DOC_EXT) or old == new:
        raise ValueError('only nonidentity document path renames (.md/.txt/.rst) supported')
    if not valid_path(old) or not valid_path(new) or old.startswith('.cora/') or new.startswith('.cora/') or old.startswith('.github/') or new.startswith('.github/'):
        raise ValueError('protected or unsafe paths blocked')
    _clean(repo)
    head = _run(repo, 'rev-parse', '--verify', 'HEAD').decode().strip()
    tracked = _tracked(repo)
    if old not in tracked or new in tracked or (repo / new).exists() or (repo / new).is_symlink():
        raise ValueError('source must be tracked, destination must not exist')
    old_file = _file(repo, old)
    if not old_file.is_file() or old_file.stat().st_size > MAX_EDIT:
        raise ValueError('source file unsupported or too large')
    # Scan *all* tracked files for exact old path bytes; references in unknown
    # extensions MUST block rather than silently omit consumer rewrites.
    old_token = old.encode('utf-8')
    edits: list[dict] = []
    for name in tracked:
        path = _file(repo, name)
        if not path.is_file() or path.is_symlink():
            raise ValueError('nonregular tracked artifact prevents completeness claim')
        if path.stat().st_size > MAX_EDIT:
            raise ValueError('oversized tracked file prevents closed reference scan')
        raw = path.read_bytes()
        if name == old:
            try:
                raw.decode('utf-8')
            except UnicodeDecodeError as e:
                raise ValueError('source document not UTF8') from e
        count = raw.count(old_token)
        if count and not name.endswith(DOC_EXT):
            raise ValueError('non-document references require dedicated adapter: ' + name)
        if count:
            try:
                raw.decode('utf-8')
            except UnicodeDecodeError as e:
                raise ValueError('non-UTF8 reference consumer') from e
        if name == old or count:
            revised = raw.replace(old_token, new.encode('utf-8'))
            edits.append({'path': name, 'result_path': new if name == old else name,
                          'before_sha256': _hash(raw), 'after_sha256': _hash(revised),
                          'reference_occurrences': count})
    if not any(e['path'] == old for e in edits):
        raise ValueError('source vanished during inventory')
    plan = {'schema':'cora-transform-plan/1', 'kind':'rename_scoped_document',
            'commit':head, 'old':old, 'new':new, 'edits':sorted(edits,key=lambda e:e['path']),
            'scope':'all_tracked_files_scanned_up_to_2MiB_each; text-reference-exact-path; external-consumers-unknown',
            'authorization':'explicit_digest_plus_test_command_required',
            'prohibited_claim':'no runtime equivalence, external reference closure, or code rename proof'}
    plan['plan_digest'] = domain_hash('CORA:transform-plan:1', plan)
    return plan


def apply_rename_docs(repo: Path, plan: dict, *, approval: str, test_command: list[str], timeout: int = 120) -> dict:
    repo = repo.resolve(strict=True)
    if not isinstance(plan, dict) or plan.get('schema') != 'cora-transform-plan/1' or plan.get('kind') != 'rename_scoped_document':
        raise ValueError('invalid plan')
    if not isinstance(approval, str) or approval != plan.get('plan_digest'):
        raise ValueError('explicit matching plan digest approval required')
    if not isinstance(test_command,list) or not test_command or any(not isinstance(s,str) or not s for s in test_command):
        raise ValueError('explicit nonempty argv-based verification command required')
    if test_command[0] in ('sh','bash','zsh','cmd','powershell'):
        raise ValueError('shell wrappers not accepted for bounded test invocation')
    if type(timeout) is not int or not 1 <= timeout <= 600:
        raise ValueError('invalid timeout')
    _clean(repo)
    actual = plan_rename_docs(repo, plan['old'], plan['new'])
    if actual != plan:
        raise ValueError('plan differs from current Git+worktree, including if self-digest re-signed')
    before: dict[str,bytes] = {}
    try:
        for entry in actual['edits']:
            item = _file(repo,entry['path'])
            raw=item.read_bytes()
            if _hash(raw)!=entry['before_sha256']:
                raise ValueError('preimage hash mismatch')
            before[entry['path']]=raw
        for entry in actual['edits']:
            source = _file(repo,entry['path'])
            target = _file(repo,entry['result_path'])
            new_contents = before[entry['path']].replace(actual['old'].encode('utf-8'),actual['new'].encode('utf-8'))
            if _hash(new_contents) != entry['after_sha256']:
                raise ValueError('postimage hash mismatch')
            target.parent.mkdir(parents=True,exist_ok=True)
            if entry['path'] == actual['old']:
                # staged rename in same filesystem; source content kept in memory for rollback
                source.rename(target)
            with tempfile.NamedTemporaryFile(dir=target.parent,delete=False) as scratch:
                temp=Path(scratch.name)
                scratch.write(new_contents)
            os.chmod(temp, target.stat().st_mode & 0o777)
            os.replace(temp,target)
        check = subprocess.run(test_command, cwd=repo, capture_output=True, timeout=timeout, check=False)
        if check.returncode != 0:
            raise ValueError('verification command failed with exit '+str(check.returncode))
        # Revalidate all owned postimages *after* the verifier ran.
        for entry in actual['edits']:
            path = _file(repo, entry['result_path'])
            if not path.is_file() or _hash(path.read_bytes()) != entry['after_sha256']:
                raise ValueError('verifier altered an owned postimage')
        if (repo / actual['old']).exists():
            raise ValueError('old path still exists after rename')
        changed = set()
        for line in _run(repo,'status','--porcelain=v1','-z','--untracked-files=all').split(b'\0'):
            if line:
                # robust rename detection via git diff --name-only may miss destination before add
                raw = line[3:]
                if raw:
                    changed.add(raw.decode('utf-8','replace'))
        allowed = {e['path'] for e in actual['edits']} | {actual['new']}
        if not changed.issubset(allowed):
            raise ValueError('verifier created unexpected workspace changes')
        receipt = {'schema':'cora-transform-receipt/1','plan_digest':actual['plan_digest'],
                   'base_commit':actual['commit'],'status':'SCOPED_APPLIED_TESTS_PASSED',
                   'test_argv':test_command,'test_returncode':check.returncode,
                   'edits':actual['edits'],
                   'scope':'local tracked document path references only; no external/runtime equivalence'}
        receipt['receipt_digest']=domain_hash('CORA:transform-receipt:1',receipt)
        return receipt
    except BaseException:
        # Compensating rollback only for the document paths owned by this transaction.
        newpath=repo / actual['new']
        if newpath.exists() and actual['new'] not in before:
            newpath.unlink()
        for name,raw in before.items():
            target=_file(repo,name)
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(raw)
        raise
