"""C05: separately specified, stdlib-based oracles for source primitives.

These fixtures are not an independent maintained-target runtime or review.
They intentionally avoid CORA canonical, evidence and graph implementations
while computing expectations; source/validator shared bugs should be detectable.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cora.evidence as evidence
from cora.evidence import domain_hash, validate_record
from cora.git_snapshot import snapshot
from cora.reticulum import assess_cut, MODEL, BLOCKED, EXTERNAL, REFUTED


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(['git', '-C', str(root), *args]).decode().strip()


def reference_digest(domain: str, value: object) -> str:
    # Derivation directly from public CORA:c14n serialization contract;
    # do NOT use CORA's audit.canonical or evidence.domain_hash.
    stable = json.dumps(value, sort_keys=True, separators=(',', ':'),
                        ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(domain.encode('ascii') + b'\x00' + stable).hexdigest()


def independent_git_blob_oid(contents: bytes) -> str:
    prefix = b'blob ' + str(len(contents)).encode('ascii') + b'\x00'
    return hashlib.sha1(prefix + contents).hexdigest()


class C05IndependentOracles(unittest.TestCase):
    def test_reference_digest_covers_nonascii_and_order(self):
        value = {'z': [False, {'b': 'caffè'}], 'a': 17}
        expected = reference_digest('CORA:record:1', value)
        self.assertEqual(domain_hash('CORA:record:1', value), expected)
        self.assertEqual(domain_hash('CORA:record:1', {'a':17, 'z':[False, {'b':'caffè'}]}), expected)
        self.assertNotEqual(reference_digest('CORA:ledger:1', value), expected)
        with patch('cora.evidence.domain_hash', return_value='0'*64):
            self.assertNotEqual(evidence.domain_hash('CORA:record:1', value), expected)

    def test_git_blob_identity_matches_independent_hash(self):
        with tempfile.TemporaryDirectory(prefix='cora-independent-git-') as directory:
            root = Path(directory)
            git(root, 'init', '-q'); git(root, 'config', 'user.name', 'Fixture')
            git(root, 'config', 'user.email', 'independent@example.invalid')
            raw = b'first\x00second\xff\n'
            path = root/'bin.dat'; path.write_bytes(raw)
            path.chmod(0o755)
            git(root, 'add', '.'); git(root, 'commit', '-qm', 'source oracle')
            head = git(root, 'rev-parse', 'HEAD')
            expected_oid = independent_git_blob_oid(raw)
            self.assertEqual(git(root, 'rev-parse', head+':bin.dat'), expected_oid)
            evidence = snapshot(root, revision=head)
            row = next(x for x in evidence['records'] if x['path']=='bin.dat')
            self.assertEqual(row['git_oid'], expected_oid)
            self.assertEqual(row['sha256'], hashlib.sha256(raw).hexdigest())
            self.assertEqual(row['mode'], '100755')
            path.write_bytes(b'tampered local worktree')
            self.assertEqual(snapshot(root, revision=head), evidence)

    def test_record_validator_accepts_only_independent_digest(self):
        payload = {'schema':'cora-evidence/1','commit':'a'*40,
                   'path':'src/check.py','git_oid':'b'*40,'mode':'100644',
                   'size':4,'sha256':'c'*64,'status':'observed_git_blob'}
        expected=reference_digest('CORA:record:1', payload)
        rec={**payload, 'digest': expected}
        self.assertTrue(validate_record(rec))
        self.assertNotEqual(expected, reference_digest('CORA:ledger:1', payload))
        with self.assertRaisesRegex(ValueError, 'tampered record'):
            validate_record({**rec, 'digest': '0'*64})

    def test_noncompensatory_external_leaf_and_refutation(self):
        # Expected states preregistered explicitly, not derived using assess_cut.
        nodes=[{'id':'SRC','depends_on':[], 'scope':'SOURCE'},
               {'id':'RUN','depends_on':[], 'scope':'SOURCE'},
               {'id':'EXT','depends_on':[], 'scope':'EXTERNAL'},
               {'id':'GOAL','depends_on':['SRC','RUN','EXT'], 'scope':'SOURCE'}]
        observed={'SRC':MODEL,'RUN':MODEL,'EXT':MODEL}
        result=assess_cut(nodes,'GOAL',observed)
        self.assertEqual(result['status'],BLOCKED)
        self.assertEqual(result['states']['EXT'],EXTERNAL)
        self.assertEqual(result['blocked_leaves'],['EXT'])
        self.assertEqual(result['authorization'],'NONE')
        observed['RUN']=REFUTED
        result=assess_cut(nodes,'GOAL',observed)
        self.assertEqual(result['status'],REFUTED)
        self.assertEqual(result['blocked_leaves'],['RUN','EXT'])
        self.assertEqual(result['digest'],reference_digest('CORA:reticular-assessment:1',
            {k:v for k,v in result.items() if k!='digest'}))
        with self.assertRaisesRegex(ValueError, 'invalid model observation'):
            assess_cut(nodes,'GOAL',{'GOAL':MODEL})
