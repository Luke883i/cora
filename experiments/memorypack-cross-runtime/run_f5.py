#!/usr/bin/env python3
"""Independent Python oracle + 12 isolated real .NET processes; fail closed."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
from datetime import datetime, timedelta

PIN = "239ffa0df2f7ccad63d276457557b49e88acae4b"
VARINT_SOURCE_SHA256 = "bc41adf2ea96e6328f7277a9c7eb2de3c8b4f3e82ea12a7fe54142253ff4efe9"
MAJORS = (8, 9, 10)
SAMPLES = (
    ("negative-five", 2026, 11, 30, 16, 48, 36, -300),
    ("positive-nine", 2026, 11, 30, 16, 48, 36, 540),
    ("positive-odd", 2026, 11, 30, 16, 48, 36, 345),
    ("zero", 2026, 11, 30, 16, 48, 36, 0),
    ("max-offset", 2000, 1, 1, 12, 0, 0, 840),
    ("min-offset", 2000, 1, 1, 12, 0, 0, -840),
    ("before-epoch", 1969, 12, 31, 23, 59, 59, 60),
    ("post-epoch", 1970, 1, 1, 0, 0, 0, 0),
    ("leap-day", 2000, 2, 29, 9, 6, 7, 75),
    ("century-date", 1900, 2, 28, 21, 3, 2, -30),
)

def hash_bytes(data):
    return hashlib.sha256(data).hexdigest()

def generate_oracle():
    cases = []
    for case in SAMPLES:
        identity, year, month, day, hour, minute, second, offset = case
        local = datetime(year, month, day, hour, minute, second)
        utc = local - timedelta(minutes=offset)
        epoch = datetime(1, 1, 1)
        delta = utc - epoch
        ticks = (delta.days * 86400 + delta.seconds) * 10000000 + delta.microseconds * 10
        net10 = struct.pack("<i", offset) + bytes(4) + struct.pack("<q", ticks)
        net9 = struct.pack("<h", offset) + bytes(6) + struct.pack("<q", ticks)
        unity = struct.pack("<q", ticks) + struct.pack("<h", offset) + bytes(6)
        cases.append(dict(id=identity, utcTicks=ticks, offsetMinutes=offset,
                          net10Hex=net10.hex().upper(),
                          net9Hex=net9.hex().upper(), unityHex=unity.hex().upper()))
    assert cases[0]["net10Hex"] == "D4FEFFFF000000000092B5AF2B4FDF08"
    assert cases[0]["net9Hex"] == "D4FE0000000000000092B5AF2B4FDF08"
    assert cases[0]["net10Hex"] != cases[0]["net9Hex"]
    return {"schema": "cora-f5-independent-python-layout/v1",
            "oracle": "Python stdlib Gregorian / struct, NOT MemoryPack native",
            "cases": cases}

def invoke(args, directory, *, logs, env=None, expected_success=True, expected_runtime=None):
    logs.parent.mkdir(parents=True, exist_ok=True)
    child = subprocess.Popen(args, cwd=directory, env=env,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True)
    try:
        output, _ = child.communicate(timeout=900)
    except subprocess.TimeoutExpired:
        child.kill()
        output, _ = child.communicate()
        logs.write_text(output, encoding="utf-8")
        raise RuntimeError(f"Subprocess timeout: {args}")
    logs.write_text(output, encoding="utf-8")
    if expected_success and child.returncode != 0:
        raise RuntimeError(f"Native process FAIL code={child.returncode}; log={logs}")
    if not expected_success and child.returncode == 0:
        raise RuntimeError(f"Negative control escaped: {args}")
    return {"pid": child.pid, "exit_code": child.returncode, "log": str(logs)}

def verified_dotnet(inv, expected_runtime):
    data = json.loads(Path(inv["receipt_file"]).read_text())
    if data.get("status") != "PASS" or data.get("runtime_major") != expected_runtime or data.get("cases") != 10 or data.get("assertions", 0) < 30:
        raise RuntimeError(f"Invalid native process evidence: {data}")
    return data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    a = parser.parse_args()
    source = a.target.resolve()
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    receipt = {"schema": "cora-memorypack-cross-runtime-f5/v1", "target": "Cysharp/MemoryPack",
               "target_sha": PIN, "status": "HOLD", "external_authority": "NONE",
               "cross_pairs": 0, "verified_wire_files": 0, "native_processes": 0,
               "negative_controls": {}, "supported_runtime_majors": []}
    try:
        sha = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
        if sha != PIN:
            raise RuntimeError(f"Unexpected source revision {sha}")
        source_file = source / "src/MemoryPack.Core/MemoryPackReaderWriter.VarInt.cs"
        if hash_bytes(source_file.read_bytes()) != VARINT_SOURCE_SHA256:
            raise RuntimeError("Original pinned source bytes changed")
        oracle = generate_oracle()
        oracle_file = out / "goldens.json"
        oracle_file.write_text(json.dumps(oracle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        receipt["oracle_sha256"] = hash_bytes(oracle_file.read_bytes())
        available = subprocess.check_output(["dotnet", "--list-runtimes"], text=True)
        (out / "dotnet-runtimes.txt").write_text(available, encoding="utf-8")
        for major in MAJORS:
            if not re.search(rf"^Microsoft\.NETCore\.App {major}\.", available, re.MULTILINE):
                raise RuntimeError(f".NET runtime major {major} not installed")
        project = Path(__file__).with_name("CORA.MemoryPack.CrossRuntime.csproj").resolve()
        env = dict(os.environ, MemoryPackRoot=str(source))
        invoke(["dotnet", "build", str(project), "-c", "Release", "--nologo"],
               source, logs=out / "build.log", env=env)
        assembly_dir = project.parent / "bin/Release"
        dlls = {}
        for major in MAJORS:
            dll = assembly_dir / f"net{major}.0" / "CORA.MemoryPack.CrossRuntime.dll"
            if not dll.exists():
                raise RuntimeError(f"Missing framework-specific compiled target {dll}")
            dlls[major] = dll
        recorded_pids = set()
        for major in MAJORS:
            directory = out / f"emitted-by-net{major}"
            process_receipt = out / f"emit-net{major}.json"
            inv = invoke(["dotnet", str(dlls[major]), "emit", str(oracle_file),
                          str(directory), str(major), str(process_receipt)],
                         source, logs=out / f"emit-net{major}.log", env=env)
            inv["receipt_file"] = str(process_receipt)
            verified_dotnet(inv, major)
            if inv["pid"] in recorded_pids:
                raise RuntimeError("Process independence not established")
            recorded_pids.add(inv["pid"])
            for case in oracle["cases"]:
                for suffix in ("net10", "unity"):
                    actual = (directory / f'{case["id"]}.{suffix}.bin').read_bytes()
                    expected = bytes.fromhex(case["net10Hex" if suffix == "net10" else "unityHex"])
                    if actual != expected:
                        raise RuntimeError(f"Python independent oracle rejected net{major}/{case['id']}/{suffix}")
                    receipt["verified_wire_files"] += 1
                if not (directory / f'{case["id"]}.native-local-only.bin').exists():
                    raise RuntimeError("Native DateTimeOffset control missing")
            receipt["supported_runtime_majors"].append(major)
            receipt["native_processes"] += 1
        # 3 producers x 3 physically distinct consumer processes = 9 directed links.
        pairs = []
        for producer in MAJORS:
            for consumer in MAJORS:
                process_receipt = out / f"consume-net{consumer}-from-net{producer}.json"
                inv = invoke(["dotnet", str(dlls[consumer]), "consume", str(oracle_file),
                              str(out / f"emitted-by-net{producer}"), str(consumer),
                              str(process_receipt)], source,
                             logs=out / f"consume-net{consumer}-from-net{producer}.log", env=env)
                inv["receipt_file"] = str(process_receipt)
                verified_dotnet(inv, consumer)
                if inv["pid"] in recorded_pids:
                    raise RuntimeError("Consumer process PID coincides with another process")
                recorded_pids.add(inv["pid"])
                receipt["native_processes"] += 1
                receipt["cross_pairs"] += 1
                pairs.append(f"net{producer}->net{consumer}")
        receipt["pairs"] = pairs
        # Adversarial witness: one flipped data byte must be rejected by an actual native consumer.
        base = out / "emitted-by-net8"
        for label in ("bit_flip", "missing_file"):
            mutated = out / f"negative-{label}"
            shutil.copytree(base, mutated)
            file = mutated / "negative-five.net10.bin"
            if label == "bit_flip":
                content = bytearray(file.read_bytes())
                content[0] ^= 1
                file.write_bytes(content)
            else:
                file.unlink()
            inv = invoke(["dotnet", str(dlls[10]), "consume", str(oracle_file),
                          str(mutated), "10", str(out / f"{label}.json")],
                         source, logs=out / f"negative-{label}.log",
                         env=env, expected_success=False)
            log = Path(inv["log"]).read_text(encoding="utf-8")
            if label == "bit_flip" and "F5 native contract violation" not in log:
                raise RuntimeError("Bit flip did not trigger the specific binary-contract guard")
            if label == "missing_file" and "FileNotFoundException" not in log:
                raise RuntimeError("Missing-file control did not fail on missing evidence")
            receipt["negative_controls"][label] = "KILLED_NATIVE"
        # Tracked checkout source bytes untouched: external target never pushed/committed.
        if hash_bytes(source_file.read_bytes()) != VARINT_SOURCE_SHA256:
            raise RuntimeError("Target C# source mutated unexpectedly")
        receipt["status"] = "PASS_SCOPED_DOTNET_8_9_10_CROSS_PROCESS"
    except Exception as exc:
        receipt["error"] = f"{type(exc).__name__}: {exc}"
        print(receipt["error"], file=sys.stderr)
    finally:
        (out / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": receipt["status"], "pairs": receipt["cross_pairs"],
                      "native_processes": receipt["native_processes"],
                      "error": receipt.get("error")}, sort_keys=True))
    return 0 if receipt["status"] == "PASS_SCOPED_DOTNET_8_9_10_CROSS_PROCESS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
