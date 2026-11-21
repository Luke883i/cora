"""Stream one opted-in child process into a finite memory budget.

No sandbox or caller authorization is provided by this helper. The process
inherits the caller's execution privileges. POSIX descendants in the same
process group are killed on interruption; Windows descendants are not attested.
"""
from __future__ import annotations

import os
import signal
import subprocess
import threading
from pathlib import Path
from time import monotonic


READ_SIZE = 64 * 1024


def run_bounded(argv: list[str], *, cwd: Path, timeout: int,
                max_output: int, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    """Run argv without a shell, refusing output growth before it is stored.

    A background reader drains only up to max_output + READ_SIZE. On overflow
    or timeout the child is terminated, never returned as a successful probe.
    """
    if (not isinstance(argv, (list, tuple)) or not argv
            or any(not isinstance(item, str) or not item for item in argv)):
        raise ValueError('invalid bounded subprocess argv')
    if type(timeout) is not int or not 1 <= timeout <= 600:
        raise ValueError('invalid bounded subprocess timeout')
    if type(max_output) is not int or not 1 <= max_output <= 64 * 1024 * 1024:
        raise ValueError('invalid bounded subprocess output budget')
    process = subprocess.Popen(
        list(argv), cwd=cwd, env=env,
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        start_new_session=(os.name == 'posix'),
    )
    chunks: list[bytes] = []
    over_budget = threading.Event()
    reader_errors: list[BaseException] = []

    def _consume() -> None:
        total = 0
        assert process.stdout is not None
        try:
            while True:
                chunk = process.stdout.read(READ_SIZE)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_output:
                    over_budget.set()
                    break
                chunks.append(chunk)
        except BaseException as exc:
            reader_errors.append(exc)
        finally:
            process.stdout.close()

    reader = threading.Thread(target=_consume, daemon=True)
    reader.start()
    deadline = monotonic() + timeout
    completed = False
    try:
        while reader.is_alive() or process.poll() is None:
            if over_budget.is_set():
                raise ValueError('subprocess output exceeded byte budget during execution')
            remaining = deadline - monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired(list(argv), timeout)
            reader.join(min(0.05, remaining))
        if over_budget.is_set():
            raise ValueError('subprocess output exceeded byte budget during execution')
        if reader_errors:
            raise OSError('subprocess output reader failed') from reader_errors[0]
        exit_code = process.wait(timeout=0.1)
        completed = True
        return subprocess.CompletedProcess(list(argv), exit_code, b''.join(chunks), None)
    finally:
        if not completed:
            if os.name == 'posix':
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            elif process.poll() is None:
                process.kill()
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=1)
            reader.join(timeout=1)
