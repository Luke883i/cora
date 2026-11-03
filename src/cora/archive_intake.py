"""No-execution ZIP intake. File evidence is not Git history or runtime safety."""
from __future__ import annotations

import hashlib
import re
import stat
import unicodedata
import zipfile
from pathlib import Path

from .evidence import domain_hash

MAX_ARCHIVE = 32 * 1024 * 1024
MAX_TOTAL = 64 * 1024 * 1024
MAX_FILE = 8 * 1024 * 1024
MAX_ENTRIES = 5000
MAX_RATIO = 200
SHA = re.compile(r'^[0-9a-f]{40}$')


def _object(kind: str, content: bytes) -> bytes:
    return hashlib.sha1(kind.encode('ascii') + b' ' + str(len(content)).encode() + b'\0' + content).digest()


def _tree_digest(contents: dict[str, tuple[bytes, str]]) -> str:
    """Git SHA-1 content tree for regular files; no Git revision or provenance claim."""
    nodes: dict[str, object] = {}
    for path, (raw, mode) in contents.items():
        node = nodes
        parts = path.split('/')
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = (raw, mode)

    def materialize(node: dict) -> bytes:
        entries = []
        for name, child in node.items():
            if isinstance(child, dict):
                mode, oid = '40000', materialize(child)
                sort_name = (name + '/').encode('utf-8')
            else:
                raw, mode = child
                oid = _object('blob', raw)
                sort_name = name.encode('utf-8')
            entries.append((sort_name, mode.encode('ascii') + b' ' + name.encode('utf-8') + b'\0' + oid))
        return _object('tree', b''.join(x[1] for x in sorted(entries)))
    return materialize(nodes).hex()


def inspect_zip(archive: Path, *, expected_tree: str | None = None,
                extract_to: Path | None = None) -> dict:
    """Fail-closed bounds and ZIP slip/symlink/collision rejection; never execute members."""
    archive = Path(archive).resolve(strict=True)
    if not archive.is_file() or archive.stat().st_size > MAX_ARCHIVE:
        raise ValueError('archive absent or oversized')
    if expected_tree is not None and not SHA.fullmatch(expected_tree):
        raise ValueError('expected tree must be a 40-digit Git SHA1')
    files = {}
    names = set()
    total = 0
    with zipfile.ZipFile(archive) as z:
        infos = z.infolist()
        if not infos or len(infos) > MAX_ENTRIES:
            raise ValueError('invalid ZIP entry count')
        root = None
        for info in infos:
            path = info.filename
            if (not path or '\\' in path or path.startswith('/') or ':' in path or '\0' in path or
                unicodedata.normalize('NFC', path) != path or
                any(ord(c) < 32 or ord(c) == 127 for c in path)):
                raise ValueError('unsafe ZIP member name')
            parts = path.rstrip('/').split('/')
            if len(parts) == 0 or any(p in ('', '.', '..') for p in parts):
                raise ValueError('ZIP traversal or empty segment')
            if root is None:
                root = parts[0]
            if len(parts) < 2 and not info.is_dir():
                raise ValueError('ZIP must have single source directory root')
            if parts[0] != root or any(p.casefold() == '.git' for p in parts):
                raise ValueError('multiple roots or embedded Git control directory')
            normal = '/'.join(parts[1:])
            if not normal and info.is_dir():
                continue
            key = normal.casefold()
            if key in names:
                raise ValueError('duplicate or case-fold colliding ZIP member')
            names.add(key)
            unix_type = (info.external_attr >> 16) & 0o170000
            if unix_type not in (0, stat.S_IFREG, stat.S_IFDIR) or bool(info.flag_bits & 1):
                raise ValueError('symlink, special file or encrypted ZIP member')
            if info.is_dir():
                continue
            if (info.file_size > MAX_FILE or
                info.file_size > MAX_RATIO * max(info.compress_size, 1)):
                raise ValueError('oversized or high-ratio ZIP member')
            total += info.file_size
            if total > MAX_TOTAL:
                raise ValueError('ZIP uncompressed budget exceeded')
            content = z.read(info)  # zipfile checks CRC; output bounded by metadata above
            if len(content) != info.file_size:
                raise ValueError('ZIP object size changed')
            mode = '100755' if (info.external_attr >> 16) & 0o111 else '100644'
            files[normal] = (content, mode)
    if not files:
        raise ValueError('empty source archive')
    # Reject ambiguous case-insensitive directory trees and file-as-parent conflicts.
    hierarchy = {}
    file_keys = {name.casefold() for name in files}
    for path in files:
        parts = path.split('/')
        for i, part in enumerate(parts):
            prefix = '/'.join(parts[:i+1]).casefold()
            actual = '/'.join(parts[:i+1])
            if prefix in hierarchy and hierarchy[prefix] != actual:
                raise ValueError('case-colliding ZIP directory hierarchy')
            hierarchy[prefix] = actual
        if any('/'.join(parts[:i]).casefold() in file_keys
               for i in range(1,len(parts))):
            raise ValueError('ZIP file cannot also be a directory')
    tree = _tree_digest(files)
    if expected_tree is not None and tree != expected_tree:
        raise ValueError('source tree differs from caller-provided expected identity')
    if extract_to is not None:
        dest = Path(extract_to).absolute()
        # Never overwrite or merge with an existing workspace.
        dest.mkdir(parents=False, exist_ok=False, mode=0o700)
        for rel, (content, mode) in sorted(files.items()):
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with target.open('xb') as file:
                file.write(content)
            target.chmod(0o700 if mode == '100755' else 0o600)
    report = {
        'schema':'cora-zip-intake/1',
        'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
        'git_tree_sha1':tree,
        'git_history':'UNAVAILABLE_NOT_IN_ZIP',
        'source_identity':'CONTENT_TREE_ONLY_NO_AUTHOR_AUTHENTICATION',
        'expected_tree_origin':'UNVERIFIED_CALLER_ASSERTION' if expected_tree else 'NOT_SUPPLIED',
        'tracked_files':len(files),
        'total_uncompressed_bytes':total,
        'execution':'NOT_EXECUTED',
        'workspace':'CREATED_NO_EXECUTION' if extract_to is not None else 'NOT_EXTRACTED',
        'runtime_coverage':'UNOBSERVED',
        'authorization':'NONE',
        'unknowns':['GIT_COMMIT_HISTORY', 'CI_ATTESTATION', 'RUNTIME_BEHAVIOR', 'EXTERNAL_CONSUMERS'],
    }
    report['receipt_digest'] = domain_hash('CORA:zip-intake:1', report)
    return report


def verify_intake(archive: Path, report: dict, *, workspace: Path | None = None) -> bool:
    """Replay ZIP content; verify extraction only when original workspace is supplied.

    A caller-provided expected tree remains unauthenticated even when equal.
    The receipt hash is not a signature of user intent or extraction history.
    """
    if not isinstance(report, dict) or report.get('schema') != 'cora-zip-intake/1':
        raise ValueError('invalid ZIP receipt')
    if report.get('expected_tree_origin') not in ('NOT_SUPPLIED', 'UNVERIFIED_CALLER_ASSERTION'):
        raise ValueError('invalid or promoted expected-tree provenance')
    state = report.get('workspace')
    if state not in ('NOT_EXTRACTED', 'CREATED_NO_EXECUTION'):
        raise ValueError('invalid workspace claim')
    if state == 'CREATED_NO_EXECUTION':
        if workspace is None:
            raise ValueError('workspace claim requires independent workspace argument')
        from .runtime_observation import _workspace_tree
        if _workspace_tree(Path(workspace).absolute()) != report.get('git_tree_sha1'):
            raise ValueError('workspace content differs from archive')
    elif workspace is not None:
        raise ValueError('workspace supplied but receipt declares no extraction')
    recomputed = inspect_zip(archive)
    # The caller's expected-tree origin is a type-checked declaration only.
    # No comparison to a Git commit or external authentication is implied.
    recomputed['expected_tree_origin'] = report['expected_tree_origin']
    recomputed['workspace'] = state
    recomputed['receipt_digest'] = domain_hash('CORA:zip-intake:1',
        {k:v for k,v in recomputed.items() if k != 'receipt_digest'})
    if recomputed != report:
        raise ValueError('ZIP evidence cannot be replayed')
    return True
