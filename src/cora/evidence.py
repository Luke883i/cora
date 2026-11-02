"""CORA evidence contracts v1: deterministic, scoped, content-addressed records.

An evidence record is an observation, not a deletion or runtime certificate.
"""
from __future__ import annotations
import hashlib
import json
import re
from .audit import canonical

SCHEMA = 'cora-evidence/1'
HEX = re.compile(r'^[0-9a-f]{40}(?:[0-9a-f]{24})?$')
SHA256 = re.compile(r'^[0-9a-f]{64}$')
OBSERVED = 'observed_git_blob'
UNKNOWN = {'symlink_unresolved', 'gitlink_unresolved', 'blob_too_large', 'lfs_pointer_unresolved'}
KEYS = {'schema', 'commit', 'path', 'git_oid', 'mode', 'size', 'sha256', 'status', 'digest'}


def domain_hash(domain: str, data: object) -> str:
    return hashlib.sha256(domain.encode('ascii') + b'\0' + canonical(data)).hexdigest()


def valid_path(path: str) -> bool:
    return bool(path and isinstance(path, str) and '\0' not in path and '\\' not in path and not path.startswith('/') and all(part not in ('', '.', '..') for part in path.split('/')))


def make_record(*, commit: str, path: str, git_oid: str, mode: str, size: int | None, sha256: str | None, status: str) -> dict:
    record = {'schema': SCHEMA, 'commit': commit, 'path': path, 'git_oid': git_oid, 'mode': mode, 'size': size, 'sha256': sha256, 'status': status}
    record['digest'] = domain_hash('CORA:record:1', record)
    validate_record(record)
    return record


def validate_record(record: object) -> bool:
    if not isinstance(record, dict) or set(record) != KEYS:
        raise ValueError('record shape mismatch')
    if record['schema'] != SCHEMA or not isinstance(record['commit'], str) or not HEX.fullmatch(record['commit']):
        raise ValueError('invalid commit')
    if not valid_path(record['path']):
        raise ValueError('unsafe path')
    if not isinstance(record['git_oid'], str) or not HEX.fullmatch(record['git_oid']):
        raise ValueError('invalid git oid')
    if record['mode'] not in ('100644', '100755', '120000', '160000'):
        raise ValueError('unknown git mode')
    if record['status'] == OBSERVED:
        if record['mode'] not in ('100644', '100755') or type(record['size']) is not int or record['size'] < 0 or not isinstance(record['sha256'], str) or not SHA256.fullmatch(record['sha256']):
            raise ValueError('observed blob requires size, hash and regular-file mode')
    elif record['status'] in UNKNOWN:
        if record['sha256'] is not None or record['size'] is not None:
            raise ValueError('unresolved object cannot carry verified size or hash')
        if record['status'] == 'symlink_unresolved' and record['mode'] != '120000':
            raise ValueError('symlink mode mismatch')
        if record['status'] == 'gitlink_unresolved' and record['mode'] != '160000':
            raise ValueError('gitlink mode mismatch')
        if record['status'] in ('blob_too_large', 'lfs_pointer_unresolved') and record['mode'] not in ('100644', '100755'):
            raise ValueError('regular-file mode required')
    else:
        raise ValueError('unsupported status')
    expected = domain_hash('CORA:record:1', {k: v for k, v in record.items() if k != 'digest'})
    if not isinstance(record['digest'], str) or record['digest'] != expected:
        raise ValueError('tampered record')
    return True


def make_ledger(commit: str, records: list[dict], *, excluded: list[str] | None = None) -> dict:
    if not isinstance(commit, str) or not HEX.fullmatch(commit):
        raise ValueError('invalid commit')
    if any(r['commit'] != commit for r in records):
        raise ValueError('cross-commit evidence rejected')
    for r in records:
        validate_record(r)
    ordered = sorted(records, key=lambda r: r['path'])
    if len({r['path'] for r in ordered}) != len(ordered):
        raise ValueError('duplicate paths')
    payload = {'schema': 'cora-ledger/1', 'commit': commit, 'records': ordered, 'excluded': sorted(excluded or []), 'coverage': {'git_tree': 'observed', 'runtime': 'unsupported', 'external_consumers': 'unsupported', 'dynamic_imports': 'unsupported'}}
    payload['ledger_digest'] = domain_hash('CORA:ledger:1', payload)
    return payload


def validate_ledger(ledger: object) -> bool:
    if not isinstance(ledger, dict) or set(ledger) != {'schema', 'commit', 'records', 'excluded', 'coverage', 'ledger_digest'} or ledger['schema'] != 'cora-ledger/1':
        raise ValueError('ledger schema mismatch')
    if not isinstance(ledger['records'], list) or not isinstance(ledger['excluded'], list) or any(not isinstance(x, str) for x in ledger['excluded']):
        raise ValueError('ledger payload mismatch')
    if not isinstance(ledger['coverage'], dict) or ledger['coverage'] != {'git_tree':'observed', 'runtime':'unsupported', 'external_consumers':'unsupported', 'dynamic_imports':'unsupported'}:
        raise ValueError('coverage assertion mismatch')
    if not isinstance(ledger['commit'], str) or not HEX.fullmatch(ledger['commit']):
        raise ValueError('bad ledger commit')
    if ledger['records'] != sorted(ledger['records'], key=lambda r: r['path']) or len({r['path'] for r in ledger['records']}) != len(ledger['records']):
        raise ValueError('non-canonical or duplicate paths')
    if ledger['excluded'] != sorted(set(ledger['excluded'])):
        raise ValueError('non-canonical exclusions')
    for r in ledger['records']:
        validate_record(r)
        if r['commit'] != ledger['commit']:
            raise ValueError('cross-commit record')
    if ledger['ledger_digest'] != domain_hash('CORA:ledger:1', {k: v for k, v in ledger.items() if k != 'ledger_digest'}):
        raise ValueError('ledger digest mismatch')
    return True
