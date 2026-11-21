#!/usr/bin/env python3
"""A bounded CORA gate: observations do not imply a third-party release."""
import argparse
import json
from pathlib import Path
from cora.reticulum import MODEL, BLOCKED, assess_cut

PIN = "239ffa0df2f7ccad63d276457557b49e88acae4b"
PASS = "PASS_SCOPED_DOTNET_8_9_10_CROSS_PROCESS"
PAIRS = [f"net{p}->net{c}" for p in (8, 9, 10) for c in (8, 9, 10)]

def evaluate(record):
    identity = record.get("target_sha") == PIN and record.get("target") == "Cysharp/MemoryPack"
    execution = record.get("status") == PASS and record.get("native_processes") == 12 and record.get("cross_pairs") == 9
    matrix = (record.get("pairs") == PAIRS and record.get("supported_runtime_majors") == [8, 9, 10])
    bytes_verified = record.get("verified_wire_files") == 60 and len(record.get("oracle_sha256", "")) == 64
    negatives = record.get("negative_controls") == {
        "bit_flip": "KILLED_NATIVE", "missing_file": "KILLED_NATIVE"}
    observed = {
        "L_TARGET_PIN": MODEL if identity else BLOCKED,
        "L_NATIVE_EXECUTIONS": MODEL if execution else BLOCKED,
        "L_DIRECTED_RUNTIME_MATRIX": MODEL if matrix else BLOCKED,
        "L_INDEPENDENT_WIRE_ORACLE": MODEL if bytes_verified else BLOCKED,
        "L_NEGATIVE_NATIVE_PROBES": MODEL if negatives else BLOCKED,
    }
    nodes = [{"id": "G_F5_FIXED_LAYOUT_CROSS_RUNTIME", "depends_on": list(observed)}] + [
        {"id": k, "depends_on": []} for k in observed]
    scoped = assess_cut(nodes, "G_F5_FIXED_LAYOUT_CROSS_RUNTIME", observed)
    release_nodes = [{"id":"G_EXTERNAL_PRODUCT_RELEASE", "depends_on":
                     ["L_SCOPED_F5", "L_UNITY_NATIVE", "L_NET_NATIVE_DATETIME_ABI", "L_SECURITY_SCOPE", "L_MAINTAINER_AUTHORITY"]}] + [
        {"id": n, "depends_on": [], "scope": "EXTERNAL"} for n in (
            "L_SCOPED_F5", "L_UNITY_NATIVE", "L_NET_NATIVE_DATETIME_ABI",
            "L_SECURITY_SCOPE", "L_MAINTAINER_AUTHORITY")]
    release = assess_cut(release_nodes, "G_EXTERNAL_PRODUCT_RELEASE", {
        "L_SCOPED_F5": MODEL if scoped["status"] == MODEL else BLOCKED})
    return {"schema":"cora-memorypack-f5-reticulum/v1", "scoped":scoped,
            "release":release,"observation_class":"CI_RECORDED_INDEPENDENT_PROCESS_AND_PYTHON_ORACLE",
            "authorization":"NONE","maintainer_approved":False}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args=parser.parse_args()
    record = json.loads(args.receipt.read_text()) if args.receipt.exists() else {}
    assessment = evaluate(record)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(assessment, indent=2, sort_keys=True) + "\n")
    print(f'CORA scoped={assessment["scoped"]["status"]}; global={assessment["release"]["status"]}')
    if record.get("status") == PASS and assessment["scoped"]["status"] != MODEL:
        raise RuntimeError("CORA rejects unauthenticated F5 PASS")
    if assessment["release"]["status"] == MODEL:
        raise RuntimeError("Unexpected product-release elevation")

if __name__ == "__main__":
    main()
