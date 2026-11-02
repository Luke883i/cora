# CORA — PR-01 canonical package baseline

CORA is a tool for scoped, explainable repository evidence and architecture convergence. **This is the minimal PR-01 baseline, not a universal dead-code detector.** No automatic deletion is available. This first package intentionally has exactly one installed entrypoint (`cora`).

## Install

Python 3.11+:

```bash
python -m pip install .
cora version
cora audit . --output /tmp/cora-audit.json
cora stress --cases 1000000 --seed 883 --output /tmp/cora-stress.json
```

`audit` scans working-tree files without executing project code. Create a `cora.products.json` containing declared products with `id`, `root`, and `entrypoints`. With no declaration file, CORA inventories paths but **cannot infer the product ontology**. The inventory reports unknown runtime, dynamic imports, historical Git provenance and external consumers; it is **not** a proof that files are unused.

## PR-01 acceptance

- single CLI via packaging; installable in clean Python 3.11+ environment;
- deterministic output for a fixed, unchanged working tree and tool version;
- file inventory with positive content hashes and declared product attribution;
- fail-closed on duplicate/missing entrypoints, overlapping product roots, symlinks;
- reproducible 1,000,000-case synthetic model-level mutation stress with predeclared fixture expectation labels;
- no destructive transformations, no runtime claims, no silent claim of R5 parity.

**Compatibility:** R5 source is a prior experimental artifact; PR-01 does not yet transplant its adaptive adapters or R4 transform API. A capability register in `docs/ADR-PR01.md` tracks these as gated follow-up PRs.

## PR-02 — committed evidence ledger and provenance

The **single `cora` CLI** now also provides immutable snapshot and verification workflows:

```bash
cora snapshot . --revision HEAD --output /tmp/cora-ledger.json
cora verify-ledger /tmp/cora-ledger.json --repo .
cora stress-evidence --seed 883 --cases 1000000 --output /tmp/cora-pr02-mutations.json
```

Snapshot reads **committed Git blob content**, not the working tree. Every regular file within the configured bound carries an independent SHA-256, Git object ID, commit, mode and path. Symlinks, submodules, Git LFS pointers and out-of-bound blobs stay explicitly `unresolved`. `verify-ledger` recomputes the complete ledger from the original commit; an internally self-consistent but forged ledger does not pass merely because it has a recalculated digest. This does **not** make Git a trusted remote attestation service or prove the file is used by the product.

The new stress corpus consists of **24 named, preseeded evidence mutation families** and 1 million in-memory variations. It verifies integrity rules and traceability consistency—not independent physical repo mutations, automatic deletion or behavioral preservation. See `docs/ADR-PR02.md`.
