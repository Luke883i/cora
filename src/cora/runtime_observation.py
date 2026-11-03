"""Explicit opt-in Docker runtime observation: never self-attested isolation or approval.

This process is separate from `process-run --process full` and never executes
untrusted source without an operator's affirmative --execute and a digest-pinned,
preloaded image, a non-root host and an available Docker engine. Engine policies,
VM boundaries and host permissions require external verification.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

from .archive_intake import inspect_zip, _tree_digest, MAX_TOTAL, MAX_FILE
from .evidence import domain_hash

IMAGE = re.compile(r'^[a-z0-9][a-z0-9._:/-]*@sha256:[0-9a-f]{64}$')
TEST_COMMAND = ('python', '-m', 'unittest', 'discover', '-s', 'tests', '-q')
TIMEOUT_SEC = 180
MAX_LOG = 1024 * 1024


def _workspace_tree(root: Path) -> str:
    if root.is_symlink() or not root.is_dir():
        raise ValueError('workspace not a real source directory')
    data = {}
    total = 0
    for dirpath, dirs, files in os.walk(root, followlinks=False):
        for name in dirs:
            if (Path(dirpath)/name).is_symlink():
                raise ValueError('workspace directory symlink')
        for name in files:
            p = Path(dirpath)/name
            if p.is_symlink() or not p.is_file():
                raise ValueError('workspace special file or symlink')
            size = p.stat().st_size
            total += size
            if size > MAX_FILE or total > MAX_TOTAL:
                raise ValueError('workspace source budget exceeded')
            rel = p.relative_to(root).as_posix()
            if any(q in ('', '.', '..', '.git') for q in rel.split('/')):
                raise ValueError('unsafe workspace source path')
            mode = '100755' if p.stat().st_mode & stat.S_IXUSR else '100644'
            data[rel] = (p.read_bytes(), mode)
    return _tree_digest(data)


def observe_runtime(archive: Path, workspace: Path, *, execute: bool = False,
                    image: str | None = None, docker: str = 'docker') -> dict:
    """If execution is unavailable, return an explicit blocker without spawning code."""
    a = inspect_zip(archive)
    work = Path(workspace).absolute()
    if _workspace_tree(work) != a['git_tree_sha1']:
        raise ValueError('workspace diverges from original source archive')
    if image is not None and not IMAGE.fullmatch(image):
        raise ValueError('container image must have digest-pinned sha256 identity')
    report = {
        'schema':'cora-runtime-observation/1',
        'archive_sha256':a['archive_sha256'],
        'git_tree_sha1':a['git_tree_sha1'],
        'git_history':'UNAVAILABLE_NOT_IN_ZIP',
        'image':image,
        'command':list(TEST_COMMAND),
        'execution_requested':execute,
        'execution_status':'NOT_REQUESTED',
        'exit_code':None,
        'stdout_sha256':None,
        'stderr_sha256':None,
        'log_bytes':None,
        'runtime_coverage':'NOT_ATTESTED',
        'sandbox_assurance':'NOT_INDEPENDENTLY_ATTESTED',
        'network':'REQUESTED_NONE_IF_EXECUTED',
        'source_mount':'REQUESTED_READ_ONLY_IF_EXECUTED',
        'authorization':'NONE',
    }
    if execute:
        if not image:
            report['execution_status']='BLOCKED_NO_PINNED_IMAGE'
        elif not shutil.which(docker):
            report['execution_status']='BLOCKED_EXECUTOR_UNAVAILABLE'
        elif os.getuid() == 0:
            report['execution_status']='BLOCKED_ROOT_HOST_OPERATOR'
        else:
            # No arbitrary shell, network access, credentials or writable source mount.
            command = [docker, 'run', '--rm', '--pull', 'never', '--network', 'none',
                       '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                       '--pids-limit', '64', '--memory', '512m', '--cpus', '1',
                       '--user', str(os.getuid()) + ':' + str(os.getgid()),
                       '--tmpfs', '/tmp:rw,nosuid,nodev,size=64m',
                       '--mount', 'type=bind,src='+str(work)+',dst=/work,readonly',
                       '--workdir', '/work', '--env', 'PYTHONPATH=/work/src:/work',
                       '--env', 'PYTHONDONTWRITEBYTECODE=1', image, *TEST_COMMAND]
            with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
                try:
                    completed = subprocess.run(command, stdout=stdout, stderr=stderr,
                                               check=False, timeout=TIMEOUT_SEC)
                except subprocess.TimeoutExpired:
                    # A CLI timeout is not an authenticated container teardown.
                    report['execution_status']='BLOCKED_TIMEOUT_CONTAINER_TEARDOWN_UNVERIFIED'
                else:
                    stdout.flush();stderr.flush()
                    sizes=(stdout.seek(0,2),stderr.seek(0,2))
                    if sum(sizes) > MAX_LOG:
                        report['execution_status']='BLOCKED_EXCESSIVE_LOGS'
                    else:
                        stdout.seek(0);stderr.seek(0)
                        report['stdout_sha256']=hashlib.sha256(stdout.read()).hexdigest()
                        report['stderr_sha256']=hashlib.sha256(stderr.read()).hexdigest()
                        report['log_bytes']=list(sizes)
                        report['exit_code']=completed.returncode
                        report['execution_status']='RUN_REPORTED_UNATTESTED' if completed.returncode==0 else 'RUN_FAILED'
    report['receipt_digest']=domain_hash('CORA:runtime-observation:1', report)
    return report


def verify_runtime_receipt(report: dict) -> bool:
    if not isinstance(report,dict) or report.get('schema')!='cora-runtime-observation/1':
        raise ValueError('invalid runtime receipt')
    if report.get('authorization')!='NONE' or report.get('sandbox_assurance')!='NOT_INDEPENDENTLY_ATTESTED':
        raise ValueError('runtime cannot self-authorize or attest external isolation')
    if report.get('receipt_digest') != domain_hash('CORA:runtime-observation:1',
             {k:v for k,v in report.items() if k!='receipt_digest'}):
        raise ValueError('runtime receipt altered')
    return True
