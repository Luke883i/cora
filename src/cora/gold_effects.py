"""Read-only, conservative workflow permissions and effect-claim classification."""
from __future__ import annotations
import hashlib
import re

SCHEMA = "cora-gold-effects/1"

def audit_workflow(content: str, *, path: str, revision: str) -> dict:
    if not isinstance(content, str) or len(content) > 256000:
        raise ValueError("invalid workflow source")
    if not path.endswith((".yml", ".yaml")) or not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise ValueError("workflow file and pinned SHA required")
    findings = []
    if not re.search(r"(?m)^jobs:\s*$", content):
        findings.append("UNPARSED_JOBS")
    if re.search(r"(?m)^\s+[a-z-]+:\s*write\s*$", content):
        findings.append("DECLARED_WRITE_CAPABILITY")
    if "write-all" in content:
        findings.append("BROAD_WRITE_CAPABILITY")
    if "permissions:" not in content:
        findings.append("IMPLICIT_HOST_PERMISSIONS")
    if "uses:" in content:
        findings.append("ACTION_EFFECT_UNCLASSIFIED")
    if "run:" in content:
        findings.append("SCRIPT_EFFECT_UNCLASSIFIED")
    if "github" in content.lower() and "script:" in content:
        findings.append("DYNAMIC_SCRIPT_UNCLASSIFIED")
    return {"schema": SCHEMA, "revision":revision, "path":path,
            "source_sha256":hashlib.sha256(content.encode()).hexdigest(),
            "potential_effects":sorted(set(findings)),
            "status":"REQUIRES_HOST_EFFECT_REVIEW" if findings else "NO_EFFECT_FOUND_NOT_CERTIFIED",
            "actual_effect":"NOT_OBSERVED",
            "readback":"NOT_OBSERVED",
            "authorization":"NONE"}

def reconcile_effect_claim(audit: dict, claim: dict | None) -> dict:
    if audit.get("schema") != SCHEMA:
        raise ValueError("wrong effect source")
    coherent = bool(isinstance(claim, dict) and
        claim.get("revision") == audit.get("revision") and
        claim.get("source_sha256") == audit.get("source_sha256") and
        claim.get("target") and claim.get("readback") is True)
    return {"schema":"cora-gold-effect-claim/1",
            "state":"COHERENT_UNTRUSTED_CLAIM" if coherent else "BLOCKED_MISSING_READBACK",
            "independent_host_attestation":False, "authorization":"NONE"}
