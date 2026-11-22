"""Local PR97 pre-PR native DoD verifier; finite falsifiers, no release authority.

Canonical reticulum lives in cora.reticulum. This tool records native test
observations and rejects replay alteration; it is not an independent runner.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from cora.reticulum import ordered_cut

CONTRACT = '.cora/contracts/dod/pr97-foreign-hardening.json'
SOURCE = 'src/cora/foreign_pilot.py'
SCHEMA = 'cora-pr97-hardening-evidence/1'
TEST_NAME = 'test_foreign_pilot.py'
MUTATIONS = [
    ('reject_wrong_tree', "request['tree'] != tree", 'False', 'test_explicit_optin_and_stale_sha'),
    ('reject_without_consent', "or (execute and not request['trusted_local_execution'])", 'or (False)', 'test_explicit_optin_and_stale_sha'),
    ('reject_false_pass', "if obs['reason'] == 'EXIT_REPORTED'\n                     and obs['exit'] == 0 and okay and\n                     set(choice['expected']).issubset(parsed) else 'DEBT_BLOCKED'", "if True else 'DEBT_BLOCKED'", 'test_physical_target_mutant_is_refuted'),
    ('reject_retained_byte_tamper', "if item != {'path': name", "if False and item != {'path': name", 'test_log_tamper_is_refuted'),
    ('reject_external_authority_promotion', "'product_acceptance': 'BLOCKED_EXTERNAL'", "'product_acceptance': 'APPROVED'", 'test_no_host_isolation_authority'),
    ('reject_failed_only_ranking', 'and success is not None and success > 0', 'and success is not None', 'test_failed_history_cannot_be_qualified_by_low_cost'),
    ('reject_process_group_cleanup', 'os.killpg(p.pid, signal.SIGKILL)', 'os.killpg(p.pid, signal.SIGCONT)', 'test_bounded_runner_cleans_orphan_after_parent_exit'),
]
PATTERN = re.compile(r'^test_\w+ \(test_foreign_pilot\.ForeignTargetHardeningTests\.([\w]+)\) \.\.\. (ok|FAIL|ERROR|skipped .+)$')


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.PIPE).decode().strip()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def source_contract(repo):
    raw = subprocess.check_output(['git', '-C', str(repo), 'show', 'HEAD:' + CONTRACT])
    data = json.loads(raw)
    nodes = data['nodes']
    ordered = ordered_cut(nodes, 'G_COMPLETE_PRODUCT_ACCEPTANCE')
    if (data['schema'] != 'cora-pr97-prepr-reticular-dod/1' or data['authority'] != 'NONE'
            or set(ordered) != {n['id'] for n in nodes} or len(ordered) != 27
            or sum(n['scope'] == 'EXTERNAL' and n['kind'] == 'LOCAL' for n in nodes) != 4):
        raise ValueError('incomplete or promoted canonical AND graph')
    return data, raw


def run_tests(repo, source: Path, specific: str | None = None):
    env = {k: os.environ[k] for k in ('PATH', 'LANG', 'SYSTEMROOT') if k in os.environ}
    env['PYTHONPATH'] = str(source)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    # Full suite uses original checkout; mutation cases use copied candidate bytes.
    cmd = [sys.executable, '-m', 'unittest', 'discover', '-s', str(repo / 'tests'), '-p', TEST_NAME, '-v']
    if specific:
        cmd += ['-k', specific]
    p = subprocess.run(cmd, cwd=repo, env=env, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=110, check=False)
    if len(p.stdout) > 200000:
        raise ValueError('unbounded native oracle output')
    return {'exit': p.returncode, 'log': p.stdout}


def parse_log(raw):
    ids = {}
    for line in raw.decode('utf-8', 'replace').splitlines():
        m = PATTERN.match(line.strip())
        if m:
            if m.group(1) in ids:
                raise ValueError('duplicate native test ID')
            ids[m.group(1)] = m.group(2)
    return ids


def projection(contract, raw, rc, mutant_records):
    ids = parse_log(raw)
    count = re.search(rb'(?m)^Ran ([0-9]+) tests?\b', raw)
    complete = (rc == 0 and count is not None and int(count.group(1)) == len(ids)
                and len(ids) > 0 and all(x == 'ok' for x in ids.values()))
    states = {}
    for n in contract['nodes']:
        if n['kind'] == 'LOCAL':
            if n['scope'] == 'EXTERNAL':
                states[n['id']] = 'BLOCKED_EXTERNAL'
            else:
                states[n['id']] = ('PASS_SCOPED_LOCAL_UNATTESTED' if complete and ids.get(n['oracle']) == 'ok'
                                   else 'NOT_ATTESTED')
    indexed = {n['id']: n for n in contract['nodes']}
    for node_id in ordered_cut(contract['nodes'], 'G_COMPLETE_PRODUCT_ACCEPTANCE'):
        n = indexed[node_id]
        if n['kind'] != 'LOCAL':
            children = [states[k] for k in n['depends_on']]
            states[n['id']] = ('BLOCKED_EXTERNAL' if 'BLOCKED_EXTERNAL' in children else
                               'PASS_SCOPED_LOCAL_UNATTESTED' if children and all(
                                   c == 'PASS_SCOPED_LOCAL_UNATTESTED' for c in children)
                               else 'NOT_ATTESTED')
    return {'nodes': states, 'test_cases': ids, 'test_count': len(ids),
            'test_reconciled': complete,
            'source_slice': states['G_SCOPED_PORTABLE_PILOT'],
            'product_acceptance': states['G_COMPLETE_PRODUCT_ACCEPTANCE'],
            'mutation_killed': sum(m['oracle_exit'] != 0 for m in mutant_records),
            'mutation_survivors': [m['name'] for m in mutant_records if m['oracle_exit'] == 0],
            'authority': 'NONE'}


def write_output(repo, output, evidence):
    repo = repo.resolve(strict=True)
    if repo == evidence.resolve() or repo in evidence.resolve().parents:
        raise ValueError('evidence must remain outside inspected source')
    if not evidence.exists():
        evidence.mkdir(parents=True)
    if any(evidence.iterdir()):
        raise ValueError('evidence must be new/empty')
    contract, contract_raw = source_contract(repo)
    commit = git(repo, 'rev-parse', 'HEAD')
    tree = git(repo, 'rev-parse', 'HEAD^{tree}')
    original = subprocess.check_output(['git', '-C', str(repo), 'show', 'HEAD:' + SOURCE])
    root_sha = sha256(original)
    main_sha = contract['base_main_merge_sha']
    ancestry = subprocess.run(['git','-C',str(repo),'merge-base','--is-ancestor',main_sha,commit],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if ancestry.returncode != 0:
        raise ValueError('authentic merged PR97 main must be an ancestor of this candidate')
    base = run_tests(repo, repo / 'src')
    logs = {'native-suite.log': base['log']}
    mutants = []
    for index, (name, before, after, oracle) in enumerate(MUTATIONS):
        with tempfile.TemporaryDirectory(prefix='cora-physical-guard-') as tmp:
            src = Path(tmp) / 'src'
            shutil.copytree(repo / 'src', src, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            file = src / 'cora' / 'foreign_pilot.py'
            original_source = file.read_text()
            if original_source.count(before) != 1:
                raise ValueError('mutation preimage missing or ambiguous: ' + name)
            file.write_text(original_source.replace(before, after, 1))
            outcome = run_tests(repo, src, oracle)
            filename = 'guard-mutant-%02d.log' % index
            logs[filename] = outcome['log']
            mutants.append({'name': name, 'oracle': oracle, 'oracle_exit': outcome['exit'],
                            'mutant_sha256': sha256(file.read_bytes()), 'log': filename,
                            'result': 'KILLED' if outcome['exit'] else 'SURVIVED'})
    if git(repo, 'rev-parse', 'HEAD') != commit or git(repo, 'rev-parse', 'HEAD^{tree}') != tree:
        raise ValueError('source changed during local falsification')
    for filename, payload in logs.items():
        (evidence / filename).write_bytes(payload)
    proj = projection(contract, base['log'], base['exit'], mutants)
    report = {'schema': SCHEMA, 'candidate_sha': commit, 'candidate_tree': tree,
              'contract_git_oid': git(repo, 'rev-parse', 'HEAD:' + CONTRACT),
              'contract_sha256': sha256(contract_raw),
              'original_module_sha256': root_sha,
              'native_exit': base['exit'], 'mutants': mutants,
              'artifacts': [{'name': k, 'sha256': sha256(v), 'bytes': len(v),
                             'trust': 'LOCAL_UNATTESTED'} for k, v in sorted(logs.items())],
              **proj, 'runner': 'LOCAL_CONTAINER_NOT_INDEPENDENTLY_ATTESTED',
              'merged_main_SHA': contract['base_main_merge_sha'],
              'merged_main_Git_object': 'AUTHENTIC_PARENT_ANCESTRY_OBSERVED',
              'target_upstream': 'pypa/sampleproject@621e4974ca25ce531773def586ba3ed8e736b3fc',
              'target_mode': 'VERBATIM_BLOBS_NOT_FULL_UPSTREAM_TREE'}
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


def replay(repo, report, evidence):
    contract, raw = source_contract(repo)
    if (report.get('schema') != SCHEMA or report.get('candidate_sha') != git(repo, 'rev-parse', 'HEAD')
            or report.get('candidate_tree') != git(repo, 'rev-parse', 'HEAD^{tree}')
            or report.get('contract_git_oid') != git(repo, 'rev-parse', 'HEAD:' + CONTRACT)
            or report.get('contract_sha256') != sha256(raw)
            or report.get('original_module_sha256') != sha256(
                 subprocess.check_output(['git', '-C', str(repo), 'show', 'HEAD:' + SOURCE]))):
        raise ValueError('wrong source Git object or DoD')
    logs = {}
    for item in report['artifacts']:
        if not re.fullmatch(r'(native-suite|guard-mutant-[0-9]{2})\.log', item['name']):
            raise ValueError('unsafe evidence filename')
        f = evidence / item['name']
        if not f.is_file() or f.is_symlink() or f.stat().st_size > 200000:
            raise ValueError('retained evidence missing or invalid')
        data = f.read_bytes()
        if item != {'name': item['name'], 'sha256': sha256(data), 'bytes': len(data),
                    'trust': 'LOCAL_UNATTESTED'}:
            raise ValueError('retained evidence was altered')
        logs[item['name']] = data
    if set(logs) != {'native-suite.log'} | {'guard-mutant-%02d.log' % i for i in range(len(MUTATIONS))}:
        raise ValueError('incomplete mutation evidence')
    if (len(report['mutants']) != len(MUTATIONS)
            or any(m['name'] != name or m['oracle'] != oracle or m['log'] != 'guard-mutant-%02d.log' % i
                   for i, (m, (name, before, after, oracle)) in enumerate(zip(report['mutants'], MUTATIONS)))):
        raise ValueError('altered mutant mapping')
    original = subprocess.check_output(['git', '-C', str(repo), 'show', 'HEAD:' + SOURCE]).decode('utf-8')
    for m, (name, before, after, oracle) in zip(report['mutants'], MUTATIONS):
        outcomes = parse_log(logs[m['log']])
        if (original.count(before) != 1 or
                m['mutant_sha256'] != sha256(original.replace(before, after, 1).encode('utf-8')) or
                m['result'] != ('KILLED' if m['oracle_exit'] != 0 else 'SURVIVED') or
                m['oracle'] not in outcomes or
                (m['oracle_exit'] == 0) != (outcomes[m['oracle']] == 'ok')):
            raise ValueError('mutant source identity or conclusion does not replay')
    native_text = logs['native-suite.log']
    if (report['native_exit'] == 0) != (b'\nOK\n' in native_text or native_text.endswith(b'\nOK\n')):
        raise ValueError('native test exit inconsistent with retained summary')
    if (report.get('runner') != 'LOCAL_CONTAINER_NOT_INDEPENDENTLY_ATTESTED'
            or report.get('target_mode') != 'VERBATIM_BLOBS_NOT_FULL_UPSTREAM_TREE'
            or report.get('merged_main_SHA') != contract['base_main_merge_sha']
            or report.get('merged_main_Git_object') != 'AUTHENTIC_PARENT_ANCESTRY_OBSERVED'
            or report.get('target_upstream') != 'pypa/sampleproject@621e4974ca25ce531773def586ba3ed8e736b3fc'):
        raise ValueError('provenance, host or target limitations altered')
    ancestry = subprocess.run(['git','-C',str(repo),'merge-base','--is-ancestor',
                              contract['base_main_merge_sha'],'HEAD'],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if ancestry.returncode != 0:
        raise ValueError('authentic merged PR97 main ancestry no longer holds')
    expected = projection(contract, native_text, report['native_exit'], report['mutants'])
    if any(report.get(k) != v for k, v in expected.items()):
        raise ValueError('DoD and real native test outcomes do not replay')
    return True


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repo', type=Path, default=Path('.'))
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--evidence-dir', type=Path, required=True)
    p.add_argument('--verify', action='store_true')
    a = p.parse_args()
    repo = a.repo.resolve(strict=True)
    if a.verify:
        result = json.loads(a.output.read_text())
        replay(repo, result, a.evidence_dir)
        print(json.dumps({'replayed': True, 'sha': result['candidate_sha'], 'status': result['source_slice']}))
    else:
        if a.output.exists():
            raise ValueError('would overwrite prior proof; use a fresh output path')
        result = write_output(repo, a.output, a.evidence_dir)
        replay(repo, result, a.evidence_dir)
        print(json.dumps({'status': result['source_slice'], 'product': result['product_acceptance'],
                          'tests': result['test_count'], 'killed': result['mutation_killed'],
                          'survivors': result['mutation_survivors']}))
    if result['source_slice'] != 'PASS_SCOPED_LOCAL_UNATTESTED' or result['mutation_survivors']:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
