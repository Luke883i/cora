"""Bounded, physical self-mutations against CORA's existing native test oracles.

Test-only runner, not a second CORA engine or independent attestation. It changes
isolated temporary package copies, never the checkout, Git references or target.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

# Every anchor is unique in the pinned original source. Failure to apply is
# INCONCLUSIVE, never a fictitious killed mutation.
MUTANTS = (
    ('session_identity', 'chat_bundle.py',
     'if not isinstance(step["session_id"], str) or not SESSION.fullmatch(step["session_id"]):',
     'if False and (not isinstance(step["session_id"], str) or not SESSION.fullmatch(step["session_id"])):',
     'test_chat_bundle_portability.py', 'test_session_id_input_constraints_and_atomic_append'),
    ('receipt_authorization', 'chat_bundle.py',
     'or receipt.get("authorization") != "NONE"',
     'or False and receipt.get("authorization") != "NONE"',
     'test_chat_bundle_portability.py', 'test_forged_receipt_and_source_promotion_refused'),
    ('dod_aggregate_self_report', 'chat_bundle.py',
     'if n["depends_on"] and n["observation"] != "UNOBSERVED":',
     'if False and n["depends_on"] and n["observation"] != "UNOBSERVED":',
     'test_chat_bundle_portability.py', 'test_aggregate_dod_claim_cannot_self_approve'),
    ('dod_external_and_cut', 'reticulum.py',
     'state = (EXTERNAL if node.get("scope") == "EXTERNAL" else',
     'state = (MODEL if node.get("scope") == "EXTERNAL" else',
     'test_chat_bundle_portability.py', 'test_derived_dod_requires_external_witness'),
    ('writer_lock_cleanup', 'chat_bundle.py',
     'lock.unlink(missing_ok=True)',
     'pass  # mutant deliberately leaks lock: cleanup/rollback must be tested',
     'test_chat_bundle_portability.py', 'test_writer_lock_cleanup_preserves_recovery'),
    ('selection_no_delete_authority', 'selection.py',
     "'authorized_action': 'NONE',", "'authorized_action': 'AUTO_DELETE',",
     'test_selection.py', 'test_oracle_undeclared_test_filename_not_proof'),
)


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(['git', '-C', str(repo), *args],
                                   stderr=subprocess.STDOUT).decode().strip()


def oracle(repo: Path, pattern: str, target: str, override: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env['PYTHONPATH'] = os.pathsep.join(str(p) for p in
        (([override] if override is not None else []) + [repo / 'src']))
    return subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests',
                           '-p', pattern, '-k', target, '-v'], cwd=repo, env=env,
                          text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          timeout=120, check=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, default=Path('.'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve(strict=True)
    sha = git(repo, 'rev-parse', '--verify', 'HEAD^{commit}')
    tree = git(repo, 'rev-parse', 'HEAD^{tree}')
    for module in {m[1] for m in MUTANTS}:
        path = f'src/cora/{module}'
        assert (repo / path).read_bytes() == subprocess.check_output(
            ['git', '-C', str(repo), 'show', f'HEAD:{path}']), f'dirty source: {path}'
    baselines = {}
    for pattern, target in sorted({(m[4], m[5]) for m in MUTANTS}):
        result = oracle(repo, pattern, target)
        if result.returncode or not re.search(r'(?m)^OK$', result.stdout):
            raise RuntimeError(f'baseline failed for {pattern}:{target}: {result.stdout[-2000:]}')
        baselines[target] = 'PASS_SCOPED'
    results = []
    for name, module, before, after, pattern, target in MUTANTS:
        raw = (repo / 'src' / 'cora' / module).read_text(encoding='utf-8')
        if raw.count(before) != 1 or after == before:
            results.append({'name': name, 'result': 'INCONCLUSIVE_ANCHOR'})
            continue
        with tempfile.TemporaryDirectory(prefix='cora-self-mut-') as directory:
            shadow = Path(directory)
            shutil.copytree(repo / 'src' / 'cora', shadow / 'cora',
                            ignore=shutil.ignore_patterns('__pycache__'))
            mutated = raw.replace(before, after, 1)
            (shadow / 'cora' / module).write_text(mutated, encoding='utf-8')
            try:
                result = oracle(repo, pattern, target, shadow)
            except subprocess.TimeoutExpired:
                results.append({'name': name, 'result': 'INCONCLUSIVE_TIMEOUT'})
                continue
            fails = re.findall(r'(?m)^FAIL: (test_[A-Za-z0-9_]+)', result.stdout)
            errors = re.findall(r'(?m)^ERROR: ', result.stdout)
            killed = result.returncode != 0 and target in fails and not errors
            results.append({'name': name, 'result': 'KILLED' if killed else 'SURVIVED_OR_INCONCLUSIVE',
                            'expected_falsifier': target, 'failing_tests': sorted(set(fails)),
                            'oracle_exit': result.returncode,
                            'mutant_sha256': hashlib.sha256(mutated.encode()).hexdigest()})
    passed = all(x['result'] == 'KILLED' for x in results)
    report = {'schema': 'cora-self-mutations/1', 'commit': sha, 'tree': tree,
              'trust': 'LOCAL_RUNNER_NOT_INDEPENDENTLY_ATTESTED',
              'source_identity': 'COMMITTED_GIT_BLOBS',
              'baseline': baselines, 'mutants': results,
              'killed': sum(x['result'] == 'KILLED' for x in results),
              'total': len(MUTANTS), 'result': 'PASS_SCOPED' if passed else 'REFUTED'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({'commit': sha, 'result': report['result'],
                      'killed': report['killed'], 'total': len(MUTANTS)}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
