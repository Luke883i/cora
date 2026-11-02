"""Preseeded, realistic evidence-contract mutations; synthetic, not physical PRs.

Expected outcomes are explicitly assigned per fixture family. This does not
constitute independent proof of runtime semantics or protection against a
malicious actor able to re-sign altered self-hashes.
"""
from __future__ import annotations
import hashlib
from .audit import canonical
from .evidence import make_record, make_ledger, validate_record, validate_ledger, domain_hash
from .mutations import mix64, MASK

FAMILIES = (
    ('untouched_blob', True), ('valid_path_rename', True),
    ('blob_sha256_tamper', False), ('git_oid_rewrite', False),
    ('cross_commit_replay', False), ('path_parent_escape', False),
    ('path_absolute', False), ('path_backslash', False),
    ('record_digest_corrupt', False), ('unknown_field', False),
    ('missing_digest', False), ('status_forgery', False),
    ('symlink_as_regular', False), ('fake_size', False),
    ('schema_version_drift', False), ('oid_invalid', False),
    ('ledger_record_reorder', False), ('ledger_duplicate_path', False),
    ('ledger_coverage_forgery', False), ('ledger_cross_commit', False),
    ('ledger_digest_corrupt', False), ('ledger_duplicate_exclusion', False),
    ('unknown_promoted_to_observed', False), ('record_subject_swap', False),
)


def seeded_case(family: str, v: int) -> tuple[dict, bool]:
    """Return mutation and whether ledger-level validation is required."""
    digest = hashlib.sha256(v.to_bytes(8, 'big')).hexdigest()
    oid = hashlib.sha1(v.to_bytes(8, 'little')).hexdigest()
    commit = hashlib.sha1(b'commit' + v.to_bytes(8, 'little')).hexdigest()
    path = f'src/{v & 4095:03x}/module_{(v >> 12) & 65535:04x}.py'
    a = make_record(commit=commit, path=path, git_oid=oid, mode='100644', size=v & 65535, sha256=digest, status='observed_git_blob')
    b = make_record(commit=commit, path=f'tests/test_{v & 65535:04x}.py', git_oid=oid, mode='100644', size=1, sha256=digest, status='observed_git_blob')
    if family == 'valid_path_rename':
        a = make_record(commit=commit, path=f'app/{v & 65535:04x}.py', git_oid=oid, mode='100644', size=v & 65535, sha256=digest, status='observed_git_blob')
    elif family == 'blob_sha256_tamper': a['sha256'] = 'a' * 64
    elif family == 'git_oid_rewrite': a['git_oid'] = 'a' * 40
    elif family == 'cross_commit_replay': a['commit'] = 'a' * 40
    elif family == 'path_parent_escape': a['path'] = '../' + path
    elif family == 'path_absolute': a['path'] = '/' + path
    elif family == 'path_backslash': a['path'] = path.replace('/', '\\')
    elif family == 'record_digest_corrupt': a['digest'] = 'f' * 64
    elif family == 'unknown_field': a['runtime_executed'] = True
    elif family == 'missing_digest': del a['digest']
    elif family == 'status_forgery': a['status'] = 'runtime_verified'
    elif family == 'symlink_as_regular': a['mode'] = '120000'
    elif family == 'fake_size': a['size'] += 1
    elif family == 'schema_version_drift': a['schema'] = 'cora-evidence/999'
    elif family == 'oid_invalid': a['git_oid'] = 'Z' * 40
    elif family == 'unknown_promoted_to_observed':
        a = make_record(commit=commit, path=path, git_oid=oid, mode='120000', size=None, sha256=None, status='symlink_unresolved')
        a['status'] = 'observed_git_blob'
    elif family == 'record_subject_swap': a['path'] = b['path']
    if family.startswith('ledger_'):
        ledger = make_ledger(commit, [a,b])
        if family == 'ledger_record_reorder': ledger['records'].reverse()
        elif family == 'ledger_duplicate_path': ledger['records'][0]['path'] = ledger['records'][1]['path']
        elif family == 'ledger_coverage_forgery': ledger['coverage']['runtime'] = 'verified'
        elif family == 'ledger_cross_commit': ledger['records'][0]['commit'] = 'a' * 40
        elif family == 'ledger_digest_corrupt': ledger['ledger_digest'] = 'a' * 64
        elif family == 'ledger_duplicate_exclusion': ledger['excluded'] = ['vendor','vendor']
        return ledger, True
    return a, False


def stress_evidence(*, seed: int = 883, cases: int = 1_000_000) -> dict:
    if type(cases) is not int or not 1 <= cases <= 10_000_000 or type(seed) is not int:
        raise ValueError('invalid stress parameters')
    counter = hashlib.sha256()
    counts = {name: 0 for name,_ in FAMILIES}
    mismatches = 0
    for i in range(cases):
        v = mix64((seed ^ i) & MASK)
        family, expected = FAMILIES[v % len(FAMILIES)]
        modified, is_ledger = seeded_case(family, v)
        try:
            (validate_ledger if is_ledger else validate_record)(modified)
            actual = True
        except ValueError:
            actual = False
        mismatches += (actual != expected)
        counts[family] += 1
        counter.update(i.to_bytes(8, 'little') + canonical(modified) + b'\0')
    return {'schema':'cora-evidence-stress/1', 'seed':seed, 'cases':cases, 'fixture_families':len(FAMILIES), 'mismatches':mismatches, 'distribution':counts, 'stream_sha256':counter.hexdigest(), 'scope':'in-memory provenance/contract mutations, independent expected fixture labels, no runtime or deletion proof'}
