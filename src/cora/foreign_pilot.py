"""Bounded third-party target pilot attached to CORA's existing One-Run.

NOT a second analysis engine or an OS sandbox.  Run the target's original
unittest/pytest only with an explicit, exact-Git local execution request.
All product, independent-runtime, and reviewer authority stays external.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import selectors
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from .git_snapshot import git, snapshot
from .one_run import run_one, verify_one
from .evidence import domain_hash

SCHEMA = 'cora-foreign-operational-pilot/1'
REQUEST = 'cora-foreign-pilot-request/1'
ADAPTERS = ('unittest', 'pytest')
MAX_BYTES = 8 * 1024 * 1024
MAX_LOG = 512 * 1024
_ID = re.compile(r'[A-Za-z_][A-Za-z0-9_.]{2,200}\Z')
_TEST = re.compile(r'tests/test_[A-Za-z0-9_]+\.py\Z')
_OUT = re.compile(r'pilot-[0-9]{2}\.log\Z')
_SHA = re.compile(r'[0-9a-f]{40}\Z')


def _outside(repo: Path, target: Path) -> Path:
    repo = repo.resolve(strict=True)
    target = target.resolve()
    if target == repo or repo in target.parents:
        raise ValueError('evidence may not be placed inside the target')
    if target.exists() and (not target.is_dir() or target.is_symlink()):
        raise ValueError('evidence destination must be a normal directory')
    return target


def _request(repo: Path, request: dict) -> tuple[dict, list[dict]]:
    if not isinstance(request, dict) or set(request) != {
            'schema', 'commit', 'tree', 'choices', 'timeout', 'trusted_local_execution'}:
        raise ValueError('bounded request schema required')
    sha = git(repo, 'rev-parse', '--verify', 'HEAD^{commit}').decode().strip()
    tree = git(repo, 'rev-parse', 'HEAD^{tree}').decode().strip()
    if (request['schema'] != REQUEST or request['commit'] != sha or
            request['tree'] != tree or type(request['timeout']) is not int or
            not 1 <= request['timeout'] <= 30 or
            type(request['trusted_local_execution']) is not bool):
        raise ValueError('request must match exact Git HEAD/tree and bounded timeout')
    ledger = snapshot(repo, sha)
    records = {r['path']: r for r in ledger['records']}
    if len(records) > 250 or sum(r.get('size', 0) or 0 for r in records.values()) > MAX_BYTES:
        raise ValueError('pilot target exceeds declared source limits')
    if any(r['status'] != 'observed_git_blob' or r['mode'] not in ('100644', '100755') for r in records.values()):
        raise ValueError('pilot refuses symlinks, gitlinks or absent source objects')
    choices = request['choices']
    if not isinstance(choices, list) or not 1 <= len(choices) <= 4:
        raise ValueError('1-4 explicit operator selections required')
    seen = set()
    for row in choices:
        if (not isinstance(row, dict) or set(row) != {'adapter', 'path', 'expected', 'obligation', 'reason'}
                or row['adapter'] not in ADAPTERS + ('semgrep',)
                or not isinstance(row['path'], str) or not _TEST.fullmatch(row['path'])
                or row['path'] not in records
                or not isinstance(row['expected'], list) or not 1 <= len(row['expected']) <= 10
                or any(not isinstance(x, str) or not _ID.fullmatch(x) for x in row['expected'])
                or len(set(row['expected'])) != len(row['expected'])
                or not isinstance(row['obligation'], str) or not 1 <= len(row['obligation']) <= 90
                or not isinstance(row['reason'], str) or not 1 <= len(row['reason']) <= 200
                or (row['adapter'], row['path']) in seen):
            raise ValueError('invalid owner, test path, IDs, obligation or duplicated choice')
        seen.add((row['adapter'], row['path']))
    return records, choices


def _unittest_events(raw: bytes) -> tuple[set[str], bool]:
    text = raw.decode('utf-8', errors='replace')
    # Canonical verbose output: test_add_one (test_simple.TestSimple.test_add_one) ... ok
    rx = re.compile(r'^\S+ \((test_[A-Za-z0-9_]+\.[A-Za-z_][\w.]+)\) \.\.\. (ok|FAIL|ERROR|skipped .+)$')
    events = []
    for line in text.splitlines():
        m = rx.match(line.strip())
        if m:
            events.append((m.group(1), m.group(2)))
    c = re.search(r'(?m)^Ran (\d+) tests?\b', text)
    okay = bool(c and int(c.group(1)) > 0 and int(c.group(1)) == len(events)
                and len(set(e[0] for e in events)) == len(events)
                and all(e[1] == 'ok' for e in events))
    return {e[0] for e in events}, okay


def _pytest_events(raw: bytes) -> tuple[set[str], bool]:
    lines = raw.decode('utf-8', 'replace').splitlines()
    events = []
    for line in lines:
        m = re.search(r'(?m)^(tests/test_[A-Za-z0-9_]+\.py::[A-Za-z_][\w:]+) (PASSED|FAILED|SKIPPED|ERROR)(?:\s|$)', line.strip())
        if m:
            node = m.group(1)
            pieces = node.replace('tests/', '').replace('.py::', '.').replace('::', '.')
            events.append((pieces, m.group(2)))
    # Independently validate pytest's summary count against parsed events.
    summary = '\n'.join(lines[-15:])
    m = re.search(r'=+ (\d+) passed(?:, \d+ \w+)* in [\d.]+s =+', summary)
    okay = bool(m and int(m.group(1)) == len(events) and len(events) > 0
                and len(set(x[0] for x in events)) == len(events)
                and all(x[1] == 'PASSED' for x in events))
    return {e[0] for e in events}, okay


def _projection(request: dict, rows: list[dict], artifacts: dict[str, bytes]) -> dict:
    expected_rows = request['choices']
    if len(rows) not in (0, len(expected_rows)):
        raise ValueError('partial runner observation cannot be accepted')
    if len(artifacts) != len(rows):
        raise ValueError('artifact ledger and test runs disagree')
    states = []
    for i, choice in enumerate(expected_rows):
        if i >= len(rows):
            state, found = 'NOT_RUN', []
        else:
            obs = rows[i]
            name = 'pilot-%02d.log' % i
            if (set(obs) != {'adapter', 'path', 'exit', 'reason', 'log', 'elapsed_ms'}
                    or obs['adapter'] != choice['adapter'] or obs['path'] != choice['path']
                    or obs['log'] != name or name not in artifacts
                    or obs['reason'] not in ('EXIT_REPORTED', 'TIMEOUT', 'OS_ERROR', 'OUTPUT_LIMIT', 'MISSING_ADAPTER')
                    or (obs['exit'] is not None and type(obs['exit']) is not int)
                    or type(obs['elapsed_ms']) is not int or obs['elapsed_ms'] < 0):
                raise ValueError('invalid per-adapter observation')
            parsed, okay = (_unittest_events(artifacts[name]) if choice['adapter'] == 'unittest'
                            else _pytest_events(artifacts[name]) if choice['adapter'] == 'pytest'
                            else (set(), False))
            found = sorted(parsed)
            state = ('PASS_SCOPED_LOCAL_UNATTESTED' if obs['reason'] == 'EXIT_REPORTED'
                     and obs['exit'] == 0 and okay and
                     set(choice['expected']).issubset(parsed) else 'DEBT_BLOCKED')
        states.append({'adapter': choice['adapter'], 'path': choice['path'],
                       'obligation': choice['obligation'], 'expected': choice['expected'],
                       'observed': found, 'state': state})
    missing = [dict(x) for x in states if x['state'] != 'PASS_SCOPED_LOCAL_UNATTESTED']
    return {'test_linkage': states, 'selected_outcome': 'PASS_SCOPED_LOCAL_UNATTESTED' if not missing else 'DEBT_BLOCKED',
            'next_unresolved': missing[0] if missing else None, 'product_acceptance': 'BLOCKED_EXTERNAL',
            'isolation': 'PROCESS_BOUNDS_ONLY_NOT_OS_SANDBOX', 'authority': 'NONE'}


def _bounded_target_command(command: list[str], cwd: Path, env: dict, timeout: int) -> tuple[int, bytes]:
    """Bounded stdout/time with process-group cancellation; NOT an OS sandbox."""
    started = time.monotonic()
    p = subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, start_new_session=True)
    chunks: list[bytes] = []
    total = 0
    try:
        assert p.stdout is not None
        with selectors.DefaultSelector() as sel:
            sel.register(p.stdout, selectors.EVENT_READ)
            while sel.get_map():
                left = timeout - (time.monotonic() - started)
                if left <= 0:
                    raise subprocess.TimeoutExpired(command, timeout)
                events = sel.select(left)
                if not events:
                    raise subprocess.TimeoutExpired(command, timeout)
                chunk = os.read(p.stdout.fileno(), min(65536, MAX_LOG - total + 1))
                if not chunk:
                    sel.unregister(p.stdout)
                elif total + len(chunk) > MAX_LOG:
                    raise ValueError('output bound exceeded')
                else:
                    total += len(chunk)
                    chunks.append(chunk)
        left = timeout - (time.monotonic() - started)
        if left <= 0:
            raise subprocess.TimeoutExpired(command, timeout)
        return p.wait(timeout=left), b''.join(chunks)
    finally:
        # The parent may already have exited while a descendant still holds
        # stdout open. Always reap the *process group*, not just a live parent.
        # This remains process cancellation, NOT an OS sandbox.
        if os.name == 'posix':
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        elif p.poll() is None:
            p.kill()
        p.wait()
        if p.stdout is not None:
            p.stdout.close()


def run_foreign_pilot(repo: Path, request: dict, *, execute: bool, evidence_dir: Path) -> dict:
    """One-Run owns source analysis; only optional fixed adapters execute target tests."""
    repo = Path(repo).resolve(strict=True)
    out = _outside(repo, Path(evidence_dir))
    records, choices = _request(repo, request)
    if type(execute) is not bool or (execute and not request['trusted_local_execution']):
        raise ValueError('explicit trusted-local-code opt-in required')
    one = run_one(repo, request['commit'], process='history')
    rows, blobs = [], {}
    if execute:
        if out.exists() and any(out.iterdir()):
            raise ValueError('nonempty evidence directory; never overwrite')
        out.mkdir(parents=True, exist_ok=True)
        # Different from os-level isolation: arbitrary Python may still use the host's permissions.
        with tempfile.TemporaryDirectory(prefix='cora-target-', dir=out) as workname:
            work = Path(workname)
            for path, record in records.items():
                target = work / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(git(repo, 'cat-file', 'blob', record['git_oid'], max_output=MAX_BYTES))
            env = {k: os.environ[k] for k in ('PATH', 'LANG', 'SYSTEMROOT') if k in os.environ}
            env['PYTHONDONTWRITEBYTECODE'] = '1'
            env['PYTHONPATH'] = str(work / 'src') + os.pathsep + str(work)
            env['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
            env['PIP_NO_INDEX'] = '1'
            for i, choice in enumerate(choices):
                begin = time.monotonic()
                adapter = choice['adapter']
                if adapter == 'unittest':
                    command = [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', Path(choice['path']).name, '-v']
                elif adapter == 'pytest':
                    command = [sys.executable, '-m', 'pytest', '-vv', '-q', '-o', 'addopts=', '--tb=no', choice['path']]
                else:
                    command = None
                status, reason, raw = None, 'MISSING_ADAPTER', b'qualified adapter unavailable\n'
                if command is not None:
                    try:
                        status, raw = _bounded_target_command(command, work, env, request['timeout'])
                        reason = 'EXIT_REPORTED'
                    except subprocess.TimeoutExpired:
                        reason, raw = 'TIMEOUT', b'test execution timed out\n'
                    except ValueError:
                        reason, raw = 'OUTPUT_LIMIT', b'refused oversized test output\n'
                    except OSError:
                        reason, raw = 'OS_ERROR', b'test launcher OS error\n'
                name = 'pilot-%02d.log' % i
                blobs[name] = raw
                rows.append({'adapter': adapter, 'path': choice['path'], 'exit': status,
                             'reason': reason, 'log': name,
                             'elapsed_ms': max(0, int((time.monotonic()-begin)*1000))})
        for name, raw in blobs.items():
            file = out / name
            with file.open('xb') as f:
                f.write(raw)
    projection = _projection(request, rows, blobs)
    report = {'schema': SCHEMA, 'commit': request['commit'], 'tree': request['tree'],
              'source_one_run': one, 'request': request, 'executed': execute, 'observations': rows,
              'artifacts': [{'path': k, 'sha256': hashlib.sha256(v).hexdigest(), 'size': len(v), 'trust': 'LOCAL_UNATTESTED'}
                            for k, v in sorted(blobs.items())], **projection}
    report['receipt_digest'] = domain_hash('CORA:foreign-pilot:1', report)
    return report


def verify_foreign_pilot(repo: Path, report: dict, evidence_dir: Path) -> bool:
    repo = Path(repo).resolve(strict=True)
    if not isinstance(report, dict) or report.get('schema') != SCHEMA or report.get('authority') != 'NONE':
        raise ValueError('invalid pilot report')
    _request(repo, report['request'])
    if report['commit'] != report['request']['commit'] or report['tree'] != report['request']['tree']:
        raise ValueError('cross-source receipt mismatch')
    if not verify_one(repo, report['source_one_run']):
        raise ValueError('One-Run source receipt did not replay')
    if (type(report['executed']) is not bool
            or report['executed'] and not report['request']['trusted_local_execution']
            or (not report['executed'] and report['observations'])):
        raise ValueError('unconsented observations')
    out = _outside(repo, Path(evidence_dir))
    blobs = {}
    if len({a['path'] for a in report['artifacts']}) != len(report['artifacts']):
        raise ValueError('duplicate evidence')
    for item in report['artifacts']:
        name = item.get('path')
        if not isinstance(name, str) or not _OUT.fullmatch(name):
            raise ValueError('invalid evidence filename')
        file = out / name
        if not file.is_file() or file.is_symlink() or file.stat().st_size > MAX_LOG:
            raise ValueError('missing, symlink or oversized retained evidence')
        data = file.read_bytes()
        if item != {'path': name, 'sha256': hashlib.sha256(data).hexdigest(),
                    'size': len(data), 'trust': 'LOCAL_UNATTESTED'}:
            raise ValueError('evidence byte hash mismatch')
        blobs[name] = data
    expected = _projection(report['request'], report['observations'], blobs)
    for k, value in expected.items():
        if report.get(k) != value:
            raise ValueError('projection, blockers or authority altered')
    receipt = dict(report)
    digest = receipt.pop('receipt_digest')
    if domain_hash('CORA:foreign-pilot:1', receipt) != digest:
        raise ValueError('pilot receipt digest mismatch')
    return True


def prioritize_obligations(obligations: list[dict], verified_runs: list[dict], *, budget_ms: int) -> list[dict]:
    """Rank structured obligation IDs by retained, verified local observations.

    Evidence is still LOCAL_UNATTESTED: this is measured decision support,
    not inference of developer intent or independently demonstrated ROI.
    Each evidence source is replayed against exact local Git and log bytes.
    """
    if type(budget_ms) is not int or not 0 <= budget_ms <= 100000 or len(obligations) > 20:
        raise ValueError('bounded plan required')
    if not isinstance(verified_runs, list) or len(verified_runs) > 20:
        raise ValueError('bounded local history required')
    observed = {}
    for run in verified_runs:
        if not isinstance(run, dict) or set(run) != {'repo', 'report', 'evidence_dir'}:
            raise ValueError('only exact Git replay reports can contribute prior measurements')
        report = run['report']
        verify_foreign_pilot(run['repo'], report, run['evidence_dir'])
        for choice, obs, status in zip(report['request']['choices'], report['observations'], report['test_linkage']):
            if choice['adapter'] not in ADAPTERS:
                continue
            observed.setdefault((choice['obligation'], choice['adapter']), []).append({
                'elapsed_ms': obs['elapsed_ms'],
                'passed': status['state'] == 'PASS_SCOPED_LOCAL_UNATTESTED',
                'source_commit': report['commit']})
    decisions = []
    for obligation in obligations:
        if (not isinstance(obligation, dict) or set(obligation) != {'id', 'owners', 'impact'}
                or not isinstance(obligation['id'], str) or not 1 <= len(obligation['id']) <= 90
                or not isinstance(obligation['owners'], list) or not 1 <= len(obligation['owners']) <= 10
                or len(set(obligation['owners'])) != len(obligation['owners'])
                or any(not isinstance(x, str) for x in obligation['owners'])
                or type(obligation['impact']) not in (int, float)
                or not 0 < obligation['impact'] <= 100):
            raise ValueError('bounded structured obligations required; no lexical guessing')
        for adapter in obligation['owners']:
            sample = observed.get((obligation['id'], adapter), [])
            mean_ms = sum(x['elapsed_ms'] for x in sample) / len(sample) if sample else None
            success = sum(x['passed'] for x in sample) / len(sample) if sample else None
            eligible = (adapter in ADAPTERS and mean_ms is not None and
                        mean_ms <= budget_ms and success is not None and success > 0)
            decisions.append({'obligation': obligation['id'], 'adapter': adapter,
                              'state': 'QUALIFIED_CANDIDATE' if eligible else
                                       'BLOCKED_MISSING_ADAPTER' if adapter not in ADAPTERS else
                                       'BLOCKED_NO_POSITIVE_RUNTIME_EVIDENCE' if sample and success == 0 else
                                       'NOT_MEASURED_OR_OVER_BUDGET',
                              'observations': len(sample), 'mean_ms': mean_ms,
                              'observed_success_rate': success,
                              'decision_score': (float(obligation['impact']) * success / max(mean_ms, 1)
                                                 if eligible else None),
                              'authority': 'NONE'})
    return sorted(decisions, key=lambda r: (r['decision_score'] is None,
                         -(r['decision_score'] or 0), r['obligation'], r['adapter']))

# Portable capability correlation: this is a view over two *already verified*
# source owners (CORA's original run_one and this module's foreign pilot).
# It neither selects arbitrary host commands nor duplicates One-Run execution.
PORTABLE_SCHEMA = 'cora-foreign-capability-bridge/1'
_ALLOWED_OWNER_STATES = frozenset({
    'NOT_SELECTED', 'BLOCKED', 'RUN_REPORTED_UNATTESTED',
    'REUSED_SOURCE_METHOD_SCOPED',
})


def _project_portable_receipts(cora_receipt: dict, target_receipt: dict,
                               bindings: list[dict]) -> dict:
    """Internal projection: callers MUST first verify BOTH owner receipts.

    A static 81-row source catalogue is *not* evidence of 81 executions. A
    successful target test is an exact native-test observation, not independent
    proof of the related source owner's execution or of product acceptance.
    """
    if not isinstance(cora_receipt, dict) or not isinstance(target_receipt, dict):
        raise ValueError('two exact-Git original owner receipts required')
    plan = cora_receipt.get('universal_capability_plan')
    if (not isinstance(plan, dict) or plan.get('schema') != 'cora-universal-capability-plan/1'
            or plan.get('commit') != cora_receipt.get('commit')
            or plan.get('authority') != 'NONE'
            or plan.get('product_status') != 'BLOCKED_EXTERNAL'):
        raise ValueError('verified original One-Run 81-owner plan required')
    rows = plan.get('rows')
    if not isinstance(rows, list) or len(rows) != 81:
        raise ValueError('all 81 original owner rows must be present')
    owner_rows = {}
    for row in rows:
        if (not isinstance(row, dict) or not isinstance(row.get('id'), str)
                or row['id'] in owner_rows or row.get('authority') != 'NONE'
                or type(row.get('selected')) is not bool
                or row.get('state') not in _ALLOWED_OWNER_STATES
                or row.get('kind') not in ('NATIVE_CLI', 'UPSTREAM_CANDIDATE')):
            raise ValueError('duplicate or malformed original capability owner')
        if (row['kind'] == 'NATIVE_CLI') != row['id'].startswith('cora:'):
            raise ValueError('capability identity and kind disagree')
        if (row['kind'] == 'UPSTREAM_CANDIDATE') != row['id'].startswith('external:'):
            raise ValueError('upstream identity and kind disagree')
        if (row['state'] != 'NOT_SELECTED' and not row['selected']
                or row['state'] == 'NOT_SELECTED' and row['selected']):
            raise ValueError('capability selection is inconsistent')
        if (row['kind'] == 'UPSTREAM_CANDIDATE' and row['state'] not in
                ('BLOCKED', 'NOT_SELECTED')):
            raise ValueError('external tool execution was laundered into source plan')
        owner_rows[row['id']] = row
    natives = sum(x['kind'] == 'NATIVE_CLI' for x in rows)
    externals = sum(x['kind'] == 'UPSTREAM_CANDIDATE' for x in rows)
    if (natives, externals) != (71, 10) or 'cora:process-run' not in owner_rows:
        raise ValueError('original 71+10 owner universe incomplete')
    counts = plan.get('counts')
    if (not isinstance(counts, dict) or counts.get('total') != 81
            or counts.get('native') != 71 or counts.get('external') != 10
            or counts.get('selected') != sum(r['selected'] for r in rows)
            or counts.get('blocked') != sum(r['state'] == 'BLOCKED' for r in rows)
            or counts.get('not_selected') != sum(r['state'] == 'NOT_SELECTED' for r in rows)
            or counts.get('run_reported') != sum(
                r['state'] == 'RUN_REPORTED_UNATTESTED' for r in rows)
            or counts.get('source_reused') != sum(
                r['state'] == 'REUSED_SOURCE_METHOD_SCOPED' for r in rows)):
        raise ValueError('81-owner plan metric denominator was altered')
    if (target_receipt.get('authority') != 'NONE'
            or target_receipt.get('product_acceptance') != 'BLOCKED_EXTERNAL'
            or target_receipt.get('isolation') != 'PROCESS_BOUNDS_ONLY_NOT_OS_SANDBOX'
            or target_receipt.get('source_one_run', {}).get('commit') != target_receipt.get('commit')):
        raise ValueError('native target provenance or untrusted runner limit altered')
    links = target_receipt.get('test_linkage')
    if not isinstance(links, list) or len(links) > 4:
        raise ValueError('original native test ledger unavailable')
    by_key = {}
    for item in links:
        if not isinstance(item, dict):
            raise ValueError('invalid native test linkage')
        key = (item.get('obligation'), item.get('adapter'), item.get('path'))
        if (key in by_key or not isinstance(item.get('expected'), list)
                or not isinstance(item.get('observed'), list)
                or item.get('state') not in ('PASS_SCOPED_LOCAL_UNATTESTED',
                                           'NOT_RUN', 'DEBT_BLOCKED')):
            raise ValueError('ambiguous or forged native test evidence')
        by_key[key] = item
    if (not isinstance(bindings, list) or not 1 <= len(bindings) <= 12):
        raise ValueError('1-12 explicit source-to-test bindings required')
    observed_bindings, unique = [], set()
    for bind in bindings:
        if (not isinstance(bind, dict) or set(bind) !=
                {'owner_id', 'obligation', 'adapter', 'path', 'test_id'}):
            raise ValueError('structured, nonlexical binding required')
        values = (bind['owner_id'], bind['obligation'], bind['adapter'],
                  bind['path'], bind['test_id'])
        if any(not isinstance(x, str) for x in values) or values in unique:
            raise ValueError('invalid or duplicated source-to-test mapping')
        unique.add(values)
        # Only the already existing One-Run owner may hold this correlation.
        # It remains SOURCE-scoped even when linked to an executed target test.
        if bind['owner_id'] != 'cora:process-run':
            raise ValueError('unqualified capability owner cannot inherit native results')
        row = owner_rows[bind['owner_id']]
        if not row['selected']:
            raise ValueError('target evidence cannot authorize an unselected source owner')
        test = by_key.get((bind['obligation'], bind['adapter'], bind['path']))
        if test is None or bind['test_id'] not in test['expected']:
            raise ValueError('test ID must be declared by the target owner')
        passes = (test['state'] == 'PASS_SCOPED_LOCAL_UNATTESTED'
                  and bind['test_id'] in test['observed'])
        observed_bindings.append({**bind,
            'native_test_status': ('PASS_SCOPED_LOCAL_UNATTESTED' if passes
                                   else 'DEBT_BLOCKED'),
            'cora_owner_execution': 'NOT_ATTESTED_BY_TARGET_TEST'})
    passed = sum(x['native_test_status'] == 'PASS_SCOPED_LOCAL_UNATTESTED'
                 for x in observed_bindings)
    return {
        'schema': PORTABLE_SCHEMA,
        'cora_commit': cora_receipt['commit'],
        'target_commit': target_receipt['commit'],
        'target_tree': target_receipt['tree'],
        'cora_plan_digest': domain_hash('CORA:portable-owner-plan:1', plan),
        'target_pilot_digest': target_receipt.get('receipt_digest'),
        'catalog_metrics': {'total': 81, 'native': 71, 'external': 10,
                            'source_owners_executed_by_bridge': 0,
                            'selected': counts['selected']},
        'native_test_metrics': {'bound_test_ids': len(observed_bindings),
                                'passing_test_ids': passed,
                                'blocked_test_ids': len(observed_bindings) - passed},
        'bindings': observed_bindings,
        'scope_status': ('PASS_SCOPED_LOCAL_UNATTESTED' if passed == len(bindings)
                         else 'DEBT_BLOCKED'),
        'next_unresolved': next((x for x in observed_bindings
                                if x['native_test_status'] != 'PASS_SCOPED_LOCAL_UNATTESTED'),
                               {'id': 'E_INDEPENDENT_HOST_SANDBOX_AND_HUMAN_REVIEW',
                                'status': 'BLOCKED_EXTERNAL'}),
        'universal_81_execution': 'BLOCKED_EXTERNAL',
        'host_isolation': 'NOT_ATTESTED',
        'independent_acceptance': 'BLOCKED_EXTERNAL',
        'authority': 'NONE',
    }


def reconcile_portable_capabilities(cora_repo: Path, cora_receipt: dict,
                                    target_repo: Path, target_receipt: dict,
                                    evidence_dir: Path, *, bindings: list[dict]) -> dict:
    """Verify existing CORA and target receipts; correlate, never execute.

    This runs no scanner, native target test, remote fetch, or shell.  The
    independent host sandbox and authenticated owner remain external gates.
    """
    cora_repo = Path(cora_repo).resolve(strict=True)
    target_repo = Path(target_repo).resolve(strict=True)
    if cora_repo == target_repo:
        raise ValueError('independent CORA and target repositories required')
    if not verify_one(cora_repo, cora_receipt):
        raise ValueError('CORA original source One-Run receipt cannot be replayed')
    if not verify_foreign_pilot(target_repo, target_receipt, evidence_dir):
        raise ValueError('original native target receipt cannot be replayed')
    outcome = _project_portable_receipts(cora_receipt, target_receipt, bindings)
    outcome['receipt_digest'] = domain_hash('CORA:portable-capability-bridge:1', outcome)
    return outcome


def verify_portable_capabilities(cora_repo: Path, cora_receipt: dict,
                                 target_repo: Path, target_receipt: dict,
                                 evidence_dir: Path, result: dict) -> bool:
    """Recompute exactly, including dual-Git verification and retained bytes."""
    if not isinstance(result, dict) or not isinstance(result.get('bindings'), list):
        raise ValueError('missing structured portable evidence')
    bindings = [{k: row[k] for k in ('owner_id', 'obligation', 'adapter',
                                    'path', 'test_id')} for row in result['bindings']]
    expected = reconcile_portable_capabilities(
        cora_repo, cora_receipt, target_repo, target_receipt, evidence_dir,
        bindings=bindings)
    if result != expected:
        raise ValueError('portable source-target reconciliation altered')
    return True
