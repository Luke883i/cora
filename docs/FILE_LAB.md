# CORA File Lab — one artifact at a time

**Design name:** *visione a volo d'uccello multi-scala* (*multi-scale bird's-eye forensic lens*). The operator zooms from byte/Git identity to imports, software, product contract, repository history and operational consumers, then returns to a **single file** with explicit evidence and epistemic debt. This is not a model of total program semantics, and not the colloquial expression *occhio di porco*.

## Quick start

```bash
# On a repository with a committed cora.ontology.json; output outside the repo.
cora file-lab . --path src/cora/graph.py --revision HEAD \
  --output /tmp/graph-lab.json --prompt-output /tmp/graph-ai-request.json
cora verify-file-lab /tmp/graph-lab.json --repo .
cora file-decision /tmp/graph-lab.json --actor engineer-id --role MAINTAINER \
  --action INVESTIGATE --rationale 'Investigate indirect consumers before considering changes' \
  --output /tmp/graph-human-decision.json
cora stress-file-lab --seed 883 --cases 1000000 --output /tmp/lab-stress.json
```

**Read-only:** commands do not execute analyzed code or call an AI API. AI involvement is a provider-neutral, optional, manual import. Commit, path and evidence IDs are stable and derived from Git. Keep outputs outside the repository.

## The five-dimensional dependency lens

| Lens | Implemented evidence | Unknown / unsupported |
|---|---|---|
| L0 File/artifact | Git mode, blob digest, size, tracked commit | LFS payload, symlink target, untracked files |
| L1 Code | Incoming/outgoing candidate Python AST imports, local unresolved imports | Reflection, imports via configuration, call graph, arbitrary language semantics |
| L2 Software | Owner-declared software membership | Real deployment composition, runtime dynamics |
| L3 Product | Declared product root and entrypoint | External customers, business contracts and indirect consumers |
| L4 Repository | Immutable snapshot, graph digest, bounded declared edges | Complete Git history, CI policy enforcement, cross-repository references |
| L5 Runtime / environment | Imported, commit-bound **caller-supplied** observations | Instrumentation coverage, provenance attestation, environment reachability and non-use |

Manifest declarations from PR-04 are listed separately and mean *declared* dependency only. **No inbound edge in an incomplete graph does not mean dead.** Any missing dimension yields an explicit `unresolved_obligations` record. The file dossier is source-revalidated only when no external runtime/AI annotation is attached; externally supplied claims retain their own unverified status.

### Runtime observation contract (manually supplied)

```json
{
  "schema": "cora-runtime-observation/1",
  "commit": "<40-digit real Git commit>",
  "provenance": "otel-export:run-unique-id (operator-provided, not verified)",
  "observations": [
    {"path": "src/shared/util.py", "kind": "loaded", "count": 3, "source_ref": "span:abc"}
  ]
}
```

Run `cora file-lab . --path src/shared/util.py --runtime-events /tmp/runtime.json`. Missing events never imply non-use, even with a correct commit. Runtime observations are **not automatically trusted** or authenticated. The format is an *import envelope*, not a claim of full OTel conformance.

### AI hypotheses — separate epistemic channel

`--prompt-output` exports **metadata without source code**; an analyst may decide whether to send it to an AI provider. An AI-produced reply is imported with `--ai-hypotheses /tmp/ai.json`:

```json
{
  "schema": "cora-ai-hypotheses/1",
  "commit": "<same 40-digit commit>",
  "path": "src/shared/util.py",
  "hypotheses": [
    {
      "hypothesis": "May be imported by a runtime plugin not represented in the static graph",
      "suggested_treatment": "INVESTIGATE",
      "evidence_refs": ["<exact evidence ID from the lab>"],
      "counterevidence": ["No trusted plugin-registry inventory"],
      "confidence_range": [0.1, 0.4]
    }
  ]
}
```

CORA validates the schema and references. It never treats this range as a calibrated probability or statistical confidence interval. A matching evidence ID means **the reference exists**, not that the proposed conclusion follows. Wrong or invented references are marked ungrounded. AI content is untrusted data; no direct network action, tool execution, permission escalation or deletion follows from it. Calibration requires independent labeled cases, reliability curves, confidence interval estimation and monitoring for drift; none exist yet.

### Forensic decision states

`RETAIN`, `INVESTIGATE`, `QUARANTINE_CANDIDATE`, `ARCHIVE_CANDIDATE`, `RENAME_CANDIDATE`, `DELETE_BLOCKED`. The last four are **not executable permissions**. The human decision tool records a digest-linked *intent* and prompts independent review for high-risk candidates; it is not a signature or authorization. See [governance](../GOVERNANCE.md).

## Falsification and DoD

A real Git fixture with two declared products and one shared software must distinguish positive incoming/outgoing edges, product entrypoints, a genuinely unreferenced **static candidate**, dynamic imports, runtime presence/absence, invalid commit bindings, AI hallucinated refs, forged/rehashed reports and two-person gate. A separate seeded 1M-case model stress tests the *finite triage policy*, **not a million repository analyses**. Pass means no false safe-deletion; it does not prove global recall, calibrated confidence, or field accuracy. See [standards audit](STANDARDS_MAINTENANCE_AUDIT.md).

## v1.experimental artifact roles

When a committed `cora.artifact-roles.json` is present, `file-lab` also includes **all** declared roles of the examined file, the matching rule paths and the manifest source digest. A file may be both test and source or contract verifier. Missing declarations create an explicit unknown; no role grants deletion permission or demonstrates successful CI execution. The independent role ledger is built with `cora artifact-audit` and verified by `cora verify-artifacts`. See [artifact semantics](ARTIFACT_SEMANTICS.md).
