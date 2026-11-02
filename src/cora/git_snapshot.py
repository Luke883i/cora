"""Read committed Git object bytes; never conflate worktree with commit state."""
from __future__ import annotations
import hashlib
from pathlib import Path
import subprocess
from .evidence import make_record, make_ledger, validate_ledger

MAX_BLOB = 8 * 1024 * 1024


def git(repo: Path, *args: str, max_output: int = 32 * 1024 * 1024) -> bytes:
    cmd = ['git', '-C', str(repo), *args]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=120)
    if proc.returncode != 0:
        raise ValueError('Git operation failed: ' + proc.stderr.decode('utf-8', 'replace')[:300])
    if len(proc.stdout) > max_output:
        raise ValueError('Git response exceeds local bound')
    return proc.stdout


def snapshot(repo: Path, revision: str = 'HEAD', max_blob: int = MAX_BLOB) -> dict:
    repo = repo.resolve(strict=True)
    if not repo.is_dir() or not isinstance(revision, str) or not revision or revision.startswith('-') or '\0' in revision:
        raise ValueError('invalid repository or revision')
    if type(max_blob) is not int or not 1 <= max_blob <= 256 * 1024 * 1024:
        raise ValueError('invalid blob bound')
    commit = git(repo, 'rev-parse', '--verify', '--end-of-options', revision + '^{commit}').decode('ascii').strip()
    listing = git(repo, 'ls-tree', '-rz', '--full-tree', commit, max_output=256 * 1024 * 1024)
    records = []
    for raw in listing.split(b'\0'):
        if not raw:
            continue
        header, encoded_path = raw.split(b'\t', 1)
        mode, kind, oid_bytes = header.split(b' ', 2)
        path = encoded_path.decode('utf-8', 'surrogateescape')
        # Non-UTF8 paths cannot be represented in the JSON evidence contract.
        try:
            path.encode('utf-8', 'strict')
        except UnicodeEncodeError:
            raise ValueError('non-UTF8 path unsupported')
        mode, kind, oid = mode.decode(), kind.decode(), oid_bytes.decode('ascii')
        if mode == '120000':
            record = make_record(commit=commit, path=path, git_oid=oid, mode=mode, size=None, sha256=None, status='symlink_unresolved')
        elif mode == '160000':
            record = make_record(commit=commit, path=path, git_oid=oid, mode=mode, size=None, sha256=None, status='gitlink_unresolved')
        elif mode in ('100644', '100755') and kind == 'blob':
            size = int(git(repo, 'cat-file', '-s', oid).strip())
            if size > max_blob:
                record = make_record(commit=commit, path=path, git_oid=oid, mode=mode, size=None, sha256=None, status='blob_too_large')
            else:
                contents = git(repo, 'cat-file', 'blob', oid, max_output=max_blob)
                if len(contents) != size:
                    raise ValueError('inconsistent Git blob size')
                if contents.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
                    record = make_record(commit=commit, path=path, git_oid=oid, mode=mode, size=None, sha256=None, status='lfs_pointer_unresolved')
                else:
                    record = make_record(commit=commit, path=path, git_oid=oid, mode=mode, size=size, sha256=hashlib.sha256(contents).hexdigest(), status='observed_git_blob')
        else:
            raise ValueError('unsupported Git object')
        records.append(record)
    ledger = make_ledger(commit, records)
    validate_ledger(ledger)
    return ledger
