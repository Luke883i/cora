"""Physical *file* mutation in disposable private staging, never implicit execution.

A syntax oracle is not a behavioral oracle. Real code execution requires explicit
caller consent and a preinstalled Docker image; Docker confinement is not
independently attested by this module. Any unknown result is inconclusive.
"""
from __future__ import annotations
import ast
import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path, PurePosixPath

SCHEMA = "cora-physical-mutants/1"
MAX_BYTES = 8 * 1024 * 1024
MAX_FILES = 512
IMAGES = {"python:3.11-slim": "python", "node:22-bookworm-slim": "node"}

def _path(rel):
    return isinstance(rel,str) and 0 < len(rel) <= 240 and not rel.startswith(("/", "-")) and "\\" not in rel and "\x00" not in rel and all(v not in ("", ".", "..") for v in rel.split("/")) and str(PurePosixPath(rel)) == rel

def _stage(source: Path, stage: Path) -> None:
    total = count = 0
    if not source.is_dir():
        raise ValueError("source directory required")
    for directory, dirs, files in os.walk(source, followlinks=False):
        dirs[:] = sorted(x for x in dirs if x not in (".git",".venv","node_modules","__pycache__"))
        folder = Path(directory)
        if folder.is_symlink() or any((folder/x).is_symlink() for x in dirs):
            raise ValueError("symlink stage prohibited")
        for name in sorted(files):
            p = folder / name
            if p.is_symlink() or not p.is_file():
                raise ValueError("only regular files supported")
            sz = p.stat().st_size
            total += sz
            count += 1
            if count > MAX_FILES or total > MAX_BYTES:
                raise ValueError("staged source exceeds bounded size")
            dest = stage / p.relative_to(source)
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(p,dest)

def _oracle(stage: Path, oracle: dict, *, authorized: bool) -> str:
    """PASS, FAIL, TIMEOUT or INCONCLUSIVE, never inferred from claim text."""
    if oracle.get("kind") == "PYTHON_AST":
        if not _path(oracle.get("path")) or not oracle["path"].endswith(".py"):
            raise ValueError("invalid source AST target")
        try:
            ast.parse((stage/oracle["path"]).read_text("utf-8"))
            return "PASS"
        except (SyntaxError,UnicodeDecodeError):
            return "FAIL"
    if oracle.get("kind") != "DOCKER_TEST":
        raise ValueError("unknown oracle kind")
    if not authorized:
        return "INCONCLUSIVE"
    image=oracle.get("image")
    command=oracle.get("command")
    if (image not in IMAGES or not isinstance(command,list) or not 2 <= len(command) <= 12
        or command[0] != IMAGES[image] or
        any(not isinstance(x,str) or not 1 <= len(x) <= 160 or "\x00" in x for x in command)):
        raise ValueError("sandbox command not allowlisted")
    # This is an explicit, local, bounded test execution, NOT a proof of
    # independently audited container confinement. No inherited host secrets.
    args = ["docker","run","--rm","--pull=never","--network=none","--read-only",
            "--cap-drop=ALL","--security-opt=no-new-privileges",
            "--pids-limit=64","--memory=512m","--cpus=1","--user=65534:65534",
            "--tmpfs=/tmp:rw,noexec,nosuid,size=32m",
            "-v",str(stage.resolve())+":/workspace:ro","-w","/workspace",
            "-e","PYTHONDONTWRITEBYTECODE=1",image,*command]
    try:
        p=subprocess.run(args,capture_output=True,timeout=25,check=False)
        if p.returncode==0:
            return "PASS"
        if p.returncode in (125,126,127):
            return "INCONCLUSIVE"
        return "FAIL"
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except OSError:
        return "INCONCLUSIVE"

def physical_mutants(source: str | Path, plan: dict, *, authorize_docker=False) -> dict:
    """One mutant per fresh staged copy; baseline must first succeed."""
    source=Path(source).resolve()
    if not isinstance(plan,dict) or plan.get("schema") != SCHEMA:
        raise ValueError("versioned mutation plan required")
    spec=plan.get("oracle")
    variants=plan.get("mutants")
    if (not isinstance(spec,dict) or not isinstance(variants,list)
        or not 1 <= len(variants) <= 64):
        raise ValueError("bounded oracle and mutant set required")
    ids=[x.get("id") for x in variants if isinstance(x,dict)]
    if len(ids)!=len(variants) or len(set(ids))!=len(ids) or any(not isinstance(x,str) or not x for x in ids):
        raise ValueError("mutant ids invalid")
    with tempfile.TemporaryDirectory(prefix="cora-physical-") as root:
        baseline=Path(root)/"baseline"
        baseline.mkdir()
        _stage(source,baseline)
        baseline_result=_oracle(baseline,spec,authorized=authorize_docker)
        if baseline_result != "PASS":
            return {"schema":SCHEMA,"status":"BLOCKED_BASELINE_NOT_PROVEN",
                    "baseline":baseline_result,"counts":{"killed":0,"survived":0,"timeout":0,"inconclusive":len(variants)},
                    "cases":[],"sandbox_attested":False,"authorization":"NONE"}
        cases=[]
        for i,item in enumerate(variants):
            rel=item.get("path")
            old=item.get("old")
            new=item.get("new")
            if (not _path(rel) or not isinstance(old,str) or not old or
                not isinstance(new,str) or new==old or
                len(old)>512 or len(new)>512):
                raise ValueError("invalid source mutation")
            stage=Path(root)/str(i)
            stage.mkdir()
            _stage(source,stage)
            target=stage/rel
            if not target.is_file() or target.is_symlink():
                raise ValueError("mutated target not a staged regular file")
            original=target.read_text("utf-8")
            if original.count(old) != 1:
                raise ValueError("stale/nonunique mutation anchor")
            changed=original.replace(old,new,1)
            target.write_text(changed,encoding="utf-8")
            if target.read_text("utf-8")!=changed:
                raise ValueError("mutant staged readback mismatch")
            outcome=_oracle(stage,spec,authorized=authorize_docker)
            classification={"FAIL":"killed","PASS":"survived","TIMEOUT":"timeout",
                            "INCONCLUSIVE":"inconclusive"}[outcome]
            cases.append({"id":item["id"],"path":rel,"mutated_sha256":hashlib.sha256(changed.encode()).hexdigest(),
                          "source_byte_delta":True,"oracle":outcome,"classification":classification})
    counts={k:sum(x["classification"]==k for x in cases) for k in
            ("killed","survived","timeout","inconclusive")}
    result={"schema":SCHEMA,
            "status":"SCOPED_ORACLE_KILLED_ALL" if counts["killed"]==len(cases) else "BLOCKED_MUTANT_SURVIVOR_OR_UNKNOWN",
            "baseline":"PASS","cases":cases,"counts":counts,
            "scope":"SOURCE_BYTES_CHANGED_ORACLE_SPECIFIC_NOT_GENERAL_CORRECTNESS",
            "sandbox_attested":False,"runtime_executed":spec.get("kind")=="DOCKER_TEST" and authorize_docker,
            "authorization":"NONE"}
    return result
