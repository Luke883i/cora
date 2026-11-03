"""Read committed Git objects with bounded batch IO; never conflate worktree with commit."""
from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

from .evidence import make_record, make_ledger, validate_ledger

MAX_BLOB = 8 * 1024 * 1024
BATCH_BYTES = 16 * 1024 * 1024
OID = re.compile(rb'^[0-9a-f]{40}(?:[0-9a-f]{24})?$')


def git(repo: Path, *args: str, max_output: int = 32 * 1024 * 1024) -> bytes:
    cmd = ['git', '-C', str(repo), *args]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=120)
    if proc.returncode != 0:
        raise ValueError('Git operation failed: ' + proc.stderr.decode('utf-8', 'replace')[:300])
    if len(proc.stdout) > max_output:
        raise ValueError('Git response exceeds local bound')
    return proc.stdout


def _batch(repo: Path, mode: str, ids: list[str], limit: int) -> bytes:
    if not ids:
        return b''
    if any(not OID.fullmatch(x.encode('ascii')) for x in ids):
        raise ValueError('invalid batch oid')
    proc = subprocess.run(['git', '-C', str(repo), 'cat-file', mode],
                          input=('\n'.join(ids)+'\n').encode('ascii'),
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          check=False, timeout=120)
    if proc.returncode:
        raise ValueError('Git batch failed: ' + proc.stderr.decode('utf-8', 'replace')[:240])
    if len(proc.stdout) > limit:
        raise ValueError('Git batch response exceeds source-derived budget')
    return proc.stdout


def _sizes(repo: Path, ids: list[str]) -> dict[str, int]:
    raw = _batch(repo, '--batch-check', ids, len(ids)*130+512)
    lines = raw.splitlines()
    if len(lines) != len(ids):
        raise ValueError('Git batch-check row count mismatch')
    sizes = {}
    for requested, line in zip(ids, lines):
        fields = line.split(b' ')
        if len(fields) != 3 or fields[0].decode('ascii') != requested or fields[1] != b'blob':
            raise ValueError('Git object type or identity mismatch')
        try:
            value = int(fields[2])
        except ValueError as exc:
            raise ValueError('invalid Git blob size') from exc
        if value < 0:
            raise ValueError('negative Git blob size')
        sizes[requested] = value
    return sizes


def _read_objects(repo: Path, ids: list[str], sizes: dict[str, int]) -> dict[str, bytes]:
    """Batch by measured blob sizes, not count; no unbounded whole-tree buffering."""
    result = {}
    batch = []
    budget = 0

    def flush() -> None:
        nonlocal batch, budget
        if not batch:
            return
        raw = _batch(repo, '--batch', batch, budget + len(batch)*128 + 512)
        offset = 0
        for oid in batch:
            end = raw.find(b'\n', offset)
            if end < 0:
                raise ValueError('truncated Git batch header')
            header = raw[offset:end].split(b' ')
            if len(header) != 3 or header[0] != oid.encode('ascii') or header[1] != b'blob':
                raise ValueError('Git batch identity/type mismatch')
            try:
                actual = int(header[2])
            except ValueError as exc:
                raise ValueError('invalid Git batch object length') from exc
            if actual != sizes[oid] or end + 1 + actual >= len(raw):
                raise ValueError('Git batch length mismatch')
            start = end + 1
            if raw[start+actual:start+actual+1] != b'\n':
                raise ValueError('Git batch framing mismatch')
            result[oid] = raw[start:start+actual]
            offset = start+actual+1
        if offset != len(raw):
            raise ValueError('Git batch trailing bytes')
        batch = []
        budget = 0

    for oid in ids:
        size = sizes[oid]
        if batch and budget + size > BATCH_BYTES:
            flush()
        batch.append(oid)
        budget += size
    flush()
    return result


def snapshot(repo: Path, revision: str = 'HEAD', max_blob: int = MAX_BLOB) -> dict:
    repo = repo.resolve(strict=True)
    if not repo.is_dir() or not isinstance(revision, str) or not revision or revision.startswith('-') or '\0' in revision:
        raise ValueError('invalid repository or revision')
    if type(max_blob) is not int or not 1 <= max_blob <= 256 * 1024 * 1024:
        raise ValueError('invalid blob bound')
    commit = git(repo, 'rev-parse', '--verify', '--end-of-options', revision + '^{commit}').decode('ascii').strip()
    listing = git(repo, 'ls-tree', '-rz', '--full-tree', commit, max_output=256 * 1024 * 1024)
    items = []
    for raw in listing.split(b'\0'):
        if not raw:
            continue
        header, encoded_path = raw.split(b'\t', 1)
        mode, kind, oid_bytes = header.split(b' ', 2)
        path = encoded_path.decode('utf-8', 'surrogateescape')
        try:
            path.encode('utf-8', 'strict')
        except UnicodeEncodeError as exc:
            raise ValueError('non-UTF8 path unsupported') from exc
        mode, kind, oid = mode.decode(), kind.decode(), oid_bytes.decode('ascii')
        if mode not in ('120000', '160000', '100644', '100755') or (mode in ('100644', '100755') and kind != 'blob'):
            raise ValueError('unsupported Git object')
        items.append((mode, kind, oid, path))
    regular_ids = sorted({oid for mode, _, oid, _ in items if mode in ('100644', '100755')})
    sizes = _sizes(repo, regular_ids)
    content_ids = [oid for oid in regular_ids if sizes[oid] <= max_blob]
    blobs = _read_objects(repo, content_ids, sizes)
    records = []
    for mode, kind, oid, path in items:
        if mode == '120000':
            state, size, digest = 'symlink_unresolved', None, None
        elif mode == '160000':
            state, size, digest = 'gitlink_unresolved', None, None
        elif sizes[oid] > max_blob:
            state, size, digest = 'blob_too_large', None, None
        else:
            data = blobs[oid]
            if len(data) != sizes[oid]:
                raise ValueError('inconsistent Git blob size')
            if data.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
                state, size, digest = 'lfs_pointer_unresolved', None, None
            else:
                state, size, digest = 'observed_git_blob', sizes[oid], hashlib.sha256(data).hexdigest()
        records.append(make_record(commit=commit, path=path, git_oid=oid, mode=mode,
                                   size=size, sha256=digest, status=state))
    ledger = make_ledger(commit, records)
    validate_ledger(ledger)
    return ledger
