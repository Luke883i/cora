# CORA — scoped software architecture evidence

**CORA** is an offline-first command-line tool for understanding a repository's architecture, checking *what the evidence actually supports*, and performing narrowly controlled maintenance. It aims to help engineers converge toward the **minimum justifiable architecture**, not merely the smallest apparent set of files.

**Status:** experimental Python alpha `0.8.0a1`; installable from this source tree. **Not** a universal dead-code detector, automatic repository cleaner, runtime-equivalence prover, production-certified tool, or public package release.

| Identity | What it means here |
| --- | --- |
| **Product — CORA** | The user-facing audit, evidence, explanation, limited transformation, and local-guard capability. Its contract and roadmap are broader than any one parser. |
| **Software — `cora-audit`** | One Python 3.11+ distribution providing the `cora` CLI, evidence and graph kernels, partial manifest adapters, certificate rules, a restricted document renamer, and a vendorable guard. |
| **Repository — `Luke883i/cora`** | This Git change/provenance boundary: sources, tests, release tools, CI, schemas and documentation. A repository is not itself a product or a deployed runtime. |

## First five minutes

```bash
# Python 3.11+; inside a checkout of this repository
python -m venv .venv
. .venv/bin/activate                 # Windows: .venv\Scripts\activate
python -m pip install .
cora --help
cora version
cora audit . --output /tmp/cora-inventory.json
cora snapshot . --revision HEAD --output /tmp/cora-ledger.json
cora verify-ledger /tmp/cora-ledger.json --repo .
```

`audit` examines the working tree; `snapshot` examines an **immutable Git commit**. Their claims are different. Keep generated outputs outside the target repository. For a first self-audit with an explicit committed ontology: `cora graph . --output /tmp/cora-graph.json`. For a **different** repository, commit a `cora.ontology.json` before graph analysis; without it CORA does not invent product boundaries.

## What works (PR-01–07)

| Capability | Commands | What is proven / what remains unknown |
| --- | --- | --- |
| Inventory and ownership (01) | `audit` | Working-tree file hashes and **declared** product roots; no automatic ownership inference. |
| Immutable provenance (02) | `snapshot`, `verify-ledger` | Git-commit-bound blob evidence; symlinks, LFS, gitlinks and oversized blobs can remain unresolved. |
| Ontology and graph (03) | `graph`, `explain` | Distinct product/software/file nodes and explainable **candidate** static Python edges; not runtime execution or complete reachability. |
| Partial ecosystem adapters (04) | `adapter-audit`, `verify-adapters` | Declared dependencies in `package.json`, `pyproject.toml`, `requirements.txt`, `Cargo.toml`, `go.mod`, `pom.xml`; no resolved build/runtime graph. |
| Evidence closure (05) | `closure`, `verify-certificate` | Git-revalidated `PASS_SCOPED` / `BLOCKED` / `REFUTED` for narrow observations; **no deletion authorization**. |
| Local maintenance (06) | `plan-rename-doc`, `apply-rename-doc`, `guard-install`, `guard-check` | Explicitly approved `.md/.txt/.rst` path rename with exact local references, checks and **owned-file** rollback; a partial Python/Git boundary guard. |
| Candidate packaging (07) | `tools/build_candidate.py`, `tools/release_verify.py`, `tools/external_validate.py` | Wheel/sdist parity, local reproducible build and installation on two **synthetic Git fixtures**; no signed supply-chain attestation. |

The CLI also has seeded stress commands (`stress`, `stress-evidence`, `stress-graph`, `stress-adapters`, `stress-closure`, `stress-transform`) and `tools/release_stress.py`. Their million-case tests use **synthetic model mutations**, not a million real repositories, equivalence proofs or deletion safety certificates.

## Operating boundaries

- **Observation is not obligation closure.** A file not found in an incomplete graph is not safe to delete. A manifest dependency is declared, not necessarily installed or executed.
- **No general deletion or code/workflow rename.** `safe_deletion` never receives a positive certificate; document renames are limited to exact references in supported tracked files and may be blocked by unknown consumers.
- **Rollback is scoped.** Verification commands run with the user's privileges and are **not sandboxed**; CORA can restore its transaction-owned document files, not arbitrary external side effects.
- **Local guard is not a trust boundary by itself.** Bootstrap and changes to protected files require independent approval; required CI checks and repository rules must be configured by an administrator. The tool does not manage or attest those settings.
- **Privacy and security:** no mandatory network service or LLM; repository content is processed locally, but user-supplied verifier commands may themselves have side effects. Treat untrusted repositories and tools accordingly.

## Engineering map and contribution path

| Where | Responsibility |
| --- | --- |
| `src/cora/` | Single package and CLI; see [module map](docs/ARCHITECTURE.md). |
| `cora.ontology.json` | **Committed self-description** of CORA's own product and software boundaries. |
| `schemas/` | Data contracts for selected records and policies; code-level validators can impose additional checks. |
| `tests/` | Unit, adversarial and temporary-Git fixture oracles; tests are **not** external production validation. |
| `tools/` | Unpublished reproducible candidate builds, archive checks and external **fixture** installation. |
| `.github/workflows/` | Test and candidate build CI; workflows do **not** publish releases. |
| `docs/` | Architecture, [global/intermediate/local DoD](docs/DOD.md), [PR-01–07 audit](docs/AUDIT_PR01_PR07.md) and versioned ADRs. |

Start here: [architecture and contract](docs/ARCHITECTURE.md) → [definition of done](docs/DOD.md) → [contributing](CONTRIBUTING.md) → [security and reporting](SECURITY.md). Run `python -m unittest discover -s tests -v` before proposing changes; run `python tools/verify_repository_contract.py` to check the first-read, links, CLI and ontology contracts. The exact available commands are discoverable via `cora --help`; evidence and unsupported areas are recorded alongside each output.
cora version

**Historical lineage:** PR-01–07 ADRs live in `docs/ADR-PR01.md` … `docs/ADR-PR07.md`; they document design decisions, not present-day release certification. See [hardening debt and acceptance](docs/AUDIT_PR01_PR07.md). Licensed under [MIT](LICENSE).

## Per-file forensic laboratory and human governance (experimental)

The **multi-scale bird's-eye forensic lens** (`cora file-lab`) creates a read-only dossier for **one tracked file at a pinned Git commit**: incoming/outgoing candidate imports, declared software/product ownership, manifest declarations, operational unknowns, a qualified *dead-code investigation candidate*, and explicit quarantine/archive/rename options that **do not execute**. A file with no visible static inbound edge is **not proven dead**.

```bash
cora file-lab . --path src/cora/graph.py --revision HEAD \
  --output /tmp/file-lab.json --prompt-output /tmp/ai-review-request.json
cora verify-file-lab /tmp/file-lab.json --repo .
cora file-decision /tmp/file-lab.json --actor engineer-id --role MAINTAINER \
  --action INVESTIGATE --rationale 'Verify runtime and external consumers before changes' \
  --output /tmp/human-decision.json
```

Optional `--runtime-events` imports **unverified caller-provided** commit-bound runtime observations; optional `--ai-hypotheses` imports AI suggestions as untrusted hypotheses with **uncalibrated**, non-probabilistic ranges. No repository code is executed and no AI provider is contacted automatically. For the evidence matrix and sample schemas see [file-lab](docs/FILE_LAB.md); for accountable human roles and separation of duties see [governance](GOVERNANCE.md); for the security, maintenance and standards audit see [hardening audit](docs/STANDARDS_MAINTENANCE_AUDIT.md). This feature does not enable general dead-code deletion.
