"""Source-only R5 register replay; no network, target runtime, or independent approval."""
from collections import Counter
from pathlib import Path
from io import StringIO
import csv
import hashlib
import json
import re
import sys

HERE = Path(__file__).resolve().parent
REGISTER = HERE / "R5_PIN_REGISTER.tsv"
EXPECTED_SHA256 = "7837686999181c43eca88ac72aa4549bedb1deceb9ec6f7aabce26b16fb0ee66"
EXPECTED_COUNTS = {
    "academics": 4, "cora": 6, "ictc": 6, "teddy": 6,
    "lumen": 6, "NILO": 6, "iKant_EDU": 6,
}
FIELDS = ["repo", "sha", "blob", "path", "level"]

def parse(raw):
    reader = csv.DictReader(StringIO(raw), delimiter="|")
    if reader.fieldnames != FIELDS:
        raise ValueError("HEADER_MISMATCH")
    return list(reader)

def structural_errors(rows):
    errors = []
    if len(rows) != 40:
        errors.append("COUNT")
    if dict(Counter(r.get("repo") for r in rows)) != EXPECTED_COUNTS:
        errors.append("REPO_DISTRIBUTION")
    if len({(r.get("repo"), r.get("sha")) for r in rows}) != len(rows):
        errors.append("DUPLICATE_COMMIT")
    for i, row in enumerate(rows):
        if any(not row.get(k) for k in FIELDS):
            errors.append(f"MISSING_FIELD_{i}")
            continue
        if not all(re.fullmatch("[0-9a-f]{40}", row[k]) for k in ("sha", "blob")):
            errors.append(f"INVALID_OID_{i}")
        path = row["path"]
        if path.startswith("/") or "\\" in path or not path.strip() or any(
            s in ("..", ".") for s in path.split("/")
        ):
            errors.append(f"UNSAFE_PATH_{i}")
        if not re.fullmatch("[A-Za-z0-9._/-]+", path):
            errors.append(f"INVALID_PATH_{i}")
        if not re.fullmatch("[a-z][a-z0-9-]*", row["level"]):
            errors.append(f"INVALID_LAYER_{i}")
    return errors

def verify(raw):
    failures = structural_errors(parse(raw))
    if hashlib.sha256(raw.encode()).hexdigest() != EXPECTED_SHA256:
        failures.append("REGISTER_BYTE_DRIFT")
    return failures

def selftest(raw):
    original = parse(raw)
    assert not structural_errors(original)
    fault_cases = [
        ("UNKNOWN_OWNER", 0, "repo", "unowned"),
        ("INVALID_SHA", 4, "sha", "bad"),
        ("INVALID_BLOB", 5, "blob", "bad"),
        ("TRAVERSAL_PATH", 7, "path", "../escape"),
        ("ABSOLUTE_PATH", 8, "path", "/unsafe"),
        ("MISSING_LAYER", 9, "level", ""),
    ]
    results = []
    for label, index, key, replacement in fault_cases:
        rows = [dict(x) for x in original]
        rows[index][key] = replacement
        results.append((label, structural_errors(rows)))
    duplicate = [dict(x) for x in original]
    duplicate[1]["sha"] = duplicate[0]["sha"]
    results.append(("DUPLICATE_COMMIT", structural_errors(duplicate)))
    absent = [dict(x) for x in original]
    absent.pop()
    results.append(("REMOVE_WITNESS", structural_errors(absent)))
    assert len(results) == 8 and all(errors for _, errors in results)

    # Plausible OID replacement is a byte-level mismatch, not semantic proof.
    plausible = raw.replace(original[0]["sha"], "f" * 40, 1)
    assert not structural_errors(parse(plausible))
    assert "REGISTER_BYTE_DRIFT" in verify(plausible)
    return results

def main():
    raw = REGISTER.read_text(encoding="utf-8")
    failures = verify(raw)
    cases = selftest(raw) if not failures else []
    report = {
        "schema": "r5-source-only-check/1",
        "pass": not failures and len(cases) == 8,
        "register_sha256": hashlib.sha256(raw.encode()).hexdigest(),
        "entries": len(parse(raw)),
        "by_repo": dict(Counter(x["repo"] for x in parse(raw))),
        "structural_falsifiers": len(cases),
        "structural_falsifiers_detected": sum(bool(x[1]) for x in cases),
        "plausible_oid_change": "HASH_DRIFT_NOT_SEMANTIC_VERDICT",
        "native_target_runtime": "NOT_RUN",
        "independent_human_review": "NOT_ATTESTED",
        "failures": failures,
    }
    print(json.dumps(report, sort_keys=True))
    return 0 if report["pass"] else 1

if __name__ == "__main__":
    sys.exit(main())
