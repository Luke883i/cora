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

## PR-03: committed ontology and explainable graph (alpha)

The `cora graph` command requires a `cora.ontology.json` **committed in the same Git revision** as the source tree. Products are owner-declared capabilities; software is separately declared, and a directory name is never proof of product identity. No ontology supplied means the graph command fails, not that products are inferred.

```bash
cora graph /path/to/repo --revision HEAD --ontology cora.ontology.json --output /tmp/cora-graph.json
cora explain /tmp/cora-graph.json --repo /path/to/repo --source product:api --target file:src/shared/util.py
cora stress-graph --seed 883 --cases 1000000 --output /tmp/graph-stress.json
```

Example ontology:
```json
{"schema":"cora-ontology/1","products":[{"id":"api","roots":["apps/api"],"entrypoints":["apps/api/main.py"]}],"software":[{"id":"app","roots":["apps/api"],"product_ids":["api"]}]}
```

Evidence: typed and versioned repository/product/software/file nodes, ledger-backed declarations and candidate Python imports with graph path witnesses. Missing, dynamic, relative, ambiguous or external imports remain unresolved. **An unreachable file is NOT certified deletable.** Coverage for runtime, deployment and external consumers remains unsupported. See `docs/ADR-PR03.md`.

## PR-04 — Versioned manifest adapters and explicit coverage

Six bounded, read-only partial adapters are available for `package.json`, `pyproject.toml`, `requirements.txt`, `Cargo.toml`, `go.mod` and `pom.xml`. No scripts, build instructions, application code or third-party plugins are executed. Dockerfiles, GitHub Actions and `.csproj` are explicitly `unsupported`; malformed, symlink and oversized content are `unresolved`.

```bash
cora adapter-audit /path/to/repo --revision HEAD --output /tmp/adapters.json
cora verify-adapters /tmp/adapters.json --repo /path/to/repo
cora stress-adapters --seed 883 --cases 1000000 --output /tmp/stress-adapters.json
```

Results carry a versioned adapter identity and provenance to PR-02 Git blob evidence. Dependency entries are **declared only**, never interpreted as proven installed, imported or used at runtime. This does not complete language-wide import resolution, build pipelines or software product boundaries. See `docs/ADR-PR04.md`.

## PR-05 — Scoped Evidence Closure (alpha)

`cora closure` issues a **Git-source-rechecked, observational-only** claim with
`PASS_SCOPED`, `BLOCKED`, or `REFUTED`; it never licenses file deletion.

```bash
cora closure /path/to/repo --claim committed_blob --path src/service.py --output /tmp/cert.json
cora verify-certificate /tmp/cert.json --repo /path/to/repo
cora closure /path/to/repo --claim declared_product_membership --path apps/api/main.py --selector api
cora closure /path/to/repo --claim declared_manifest_dependency --path package.json --selector react
cora closure /path/to/repo --claim static_import_candidate --path apps/api/main.py --selector src/shared/util.py
cora closure /path/to/repo --claim safe_deletion --path legacy/file.py
cora stress-closure --seed 883 --cases 1000000 --output /tmp/cora-closure-stress.json
```

The three latter observational claims require ontologies or adapters from earlier PRs. `safe_deletion` is **always blocked** in PR-05 because runtime, build, deployment, retention and external consumer obligations have no authoritative proofs. A missing blob is `REFUTED` only *within the specified immutable Git commit*; it says nothing about untracked files or other repositories. An agent cannot supply arbitrary fact assertions to `cora closure`. The signed-looking SHA-256 digest is **not a cryptographic signature**; `verify-certificate` must independently recompute from Git. See `docs/ADR-PR05.md`.
