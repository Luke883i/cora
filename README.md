# CORA — software architecture evidence and forensic maintenance

**CORA** is an offline-first, Python 3.11+ command-line **product** for investigating heterogeneous repositories, explaining evidence about software and files, and planning *strictly bounded* changes. **v1.experimental (`1.0.0a1`) is a prerelease candidate, not stable 1.0.0 or a public release.** CORA is **not** a universal dead-code detector, runtime-equivalence prover, or automatic code deleter.

| Identity | What it is | Where its truth lives |
| --- | --- | --- |
| **Product `cora`** | Capability to audit, explain and conservatively maintain architecture | [Product/software ontology](cora.ontology.json), [governance](GOVERNANCE.md) and [DoD](docs/DOD_V1_EXPERIMENTAL.md) |
| **Software `cora-engine`** | `cora-audit` Python distribution with **one** entrypoint, `cora`, and evidence/forensic modules | [`src/cora/`](src/cora/), [`pyproject.toml`](pyproject.toml) |
| **Software `cora-release-verification`** | Non-runtime candidate build, provenance and fixture tools | [`tools/`](tools/) |
| **Repository `Luke883i/cora`** | Git source/change boundary: code, tests, contracts, CI, policies and ADRs | This root, [`tests/`](tests/), [workflows](.github/workflows/) |

A repository is not the product, a directory is not automatically a software system, and a name such as `test_contract.py` does **not** determine whether something is implementation, a test, a contract, or all three. CORA uses [committed, overlapping artifact-role declarations](cora.artifact-roles.json), never name-based usage assertions. Role declarations are **not behavioral proof**.

## First five minutes

```bash
python -m venv .venv
. .venv/bin/activate                    # Windows: .venv\Scripts\activate
python -m pip install .
cora --help
cora version
cora audit . --output /tmp/cora-inventory.json
cora snapshot . --revision HEAD --output /tmp/cora-ledger.json
cora verify-ledger /tmp/cora-ledger.json --repo .
```

Keep output files **outside** the repository. `audit` reads the working tree, while `snapshot` reads a **pinned Git commit**. The first does not substitute for the second. For a new repository, commit an explicit [`cora.ontology.json`](cora.ontology.json) describing its *own* product and software boundaries before running the graph.

## What works — one canonical software, bounded capabilities

| Capability | Command(s) | Proven scope and limit |
| --- | --- | --- |
| Working-tree inventory (PR-01) | `audit` | File hashes, declared ownership; no inferred business identity |
| Git evidence (PR-02) | `snapshot`, `verify-ledger` | Committed Git blobs; symlinks, submodules, LFS/oversized objects can be unknown |
| Ontology and graph (PR-03) | `graph`, `explain` | Owner-declared product/software; partial Python AST candidate edges, **not** runtime calls |
| Manifest adapters (PR-04) | `adapter-audit`, `verify-adapters` | Partial Python/Node/Rust/Go/Maven declarations; not installed or executed dependencies |
| Closure (PR-05) | `closure`, `verify-certificate` | Git-revalidated observational `PASS_SCOPED`, `BLOCKED`, `REFUTED`; no deletion permission |
| Document rename/guard (PR-06) | `plan-rename-doc`, `apply-rename-doc`, `guard-install`, `guard-check` | Only exact `.md/.txt/.rst` path references with tests and owned-file rollback; partial Git/Python guard |
| Candidate packaging (PR-07) | `tools/build_candidate.py`, `tools/release_verify.py`, `tools/external_validate.py` | Wheel/sdist, local reproducibility, synthetic Git fixture installs; no signed/published release |
| Per-file forensic lab (PR-09) | `file-lab`, `verify-file-lab`, `file-decision` | Source/ontology/graph + untrusted AI/runtime annotations; human intent, **not** execution |
| Multi-role artifact evidence (v1) | `artifact-audit`, `verify-artifacts` | Explicitly declared **overlapping** software/test/contract/workflow roles at a commit; unknowns remain unknown |
| Conservative selection (v1.experimental) | `select-file`, `verify-selection` | Git-verified `RETAIN_EVIDENCED`, `INVESTIGATE` or `DEBT_BLOCKED`; **no automatic deletion** |

The CLI also offers `stress`, `stress-evidence`, `stress-graph`, `stress-adapters`, `stress-closure`, `stress-transform`, `stress-file-lab`, `stress-artifact-semantics`, and `stress-selection`. Large numbers refer to **synthetic fixtures or finite policy states**, never independent validation on a million actual repositories.

## Investigate one file — and run CORA on CORA

```bash
cora graph . --revision HEAD --output /tmp/cora-graph.json
cora artifact-audit . --revision HEAD --output /tmp/cora-roles.json
cora verify-artifacts /tmp/cora-roles.json --repo .
cora file-lab . --path src/cora/graph.py --revision HEAD \
  --output /tmp/file-lab.json --prompt-output /tmp/ai-request.json
cora verify-file-lab /tmp/file-lab.json --repo .
cora select-file . --path src/cora/graph.py --revision HEAD --output /tmp/selection.json
cora verify-selection /tmp/selection.json --repo .
python tools/verify_repository_contract.py --repo .
python tools/verify_artifact_roles.py --repo .
```

Artifact roles are multi-valued: the **same** file may be a test, executable source, contract verifier and fixture. The lab shows incoming/outgoing candidate imports, declared software and products, evidence gaps, treatment hypotheses and optional caller-supplied runtime/AI assertions. It **cannot** conclude that no external, dynamic, migration, deployment or runtime consumer exists. An AI confidence range is **uncalibrated**, not a probability. For contracts and examples: [file lab](docs/FILE_LAB.md), [artifact semantics](docs/ARTIFACT_SEMANTICS.md).

**Selection states:** `RETAIN_EVIDENCED` means a positive static/declaration reason to keep; `INVESTIGATE` means no positive usage observed but unknowns remain; `DEBT_BLOCKED` means required Git/ontology/role evidence is missing. All three have `authorized_action=NONE`. See the [selection DoD and its impossibility boundary](docs/DOD_SELECTION.md) for the global vs scoped distinction. The million-case selector corpus is finite and synthetic.

Human triage can record `RETAIN`, `INVESTIGATE`, `QUARANTINE_CANDIDATE`, `ARCHIVE_CANDIDATE`, `RENAME_CANDIDATE`, or `DELETE_BLOCKED`, but **never applies a change**. A safe-deletion claim cannot be certified by v1.experimental.

## Operating boundaries

- **Evidence, inference and authorization are distinct.** Neither a missing static edge nor a role name proves dead code, executed contracts, or safe deletion. `PASS_SCOPED` is scoped observation, not permission.
- **No general code, folder or workflow rename.** Only a clean-Git, reviewed, digest-approved document-path operation is supported. Verification commands run with operator privileges, **not in a sandbox**; rollback covers owned files, not external side effects.
- **Guard is not independent enforcement.** GitHub required reviews/checks and branch protection need separate administrator setup; workflow presence does not establish enforcement. Hosting plan restrictions may make some controls unavailable.
- **No built-in AI provider, autonomous action, remote execution or telemetry attestation.** External annotations remain untrusted. Do not upload private source without a separate decision.
- **Reproducibility is scoped.** Two matching local builds and deterministic fixture tests do not establish external production fitness or signed provenance.

## Engineering map and human governance

`src/cora/` holds the **single** Python package; `tests/` includes unit/negative Git fixtures; `schemas/` contains companion contracts; `tools/` handles candidate packaging and self-audit; `.github/workflows/` runs tests but does not publish. `docs/` stores versioned architecture, ADRs, hardening and DoDs. Start from [architecture](docs/ARCHITECTURE.md), [global/intermediate/local DoD](docs/DOD_V1_EXPERIMENTAL.md), [contribution rules](CONTRIBUTING.md), [security](SECURITY.md) and [human governance](GOVERNANCE.md).

Before any PR: `python -m unittest discover -s tests -v`, then the repository and artifact self-checks above. Changes to product boundaries, schemas, guard, security or release workflows require owner review and independent approver; the local record cannot authenticate those persons. **Do not merge** a release claim until CI and real external pilot gates are met.

## Status and release identity

**CORA v1.experimental = package `1.0.0a1`**, a PEP 440/SemVer-style *pre-release identity*, not a stable API promise. The PR candidate is reviewed with checksums and GitHub CI artifacts; no public PyPI package, signed SLSA provenance or GitHub Release is implied. The [DoD](docs/DOD_V1_EXPERIMENTAL.md) distinguishes automated scoped PASS from still-open human and external validation gates.

[License](LICENSE) · [Security reporting](SECURITY.md) · [Source/decision history](docs/ARCHITECTURE.md).
