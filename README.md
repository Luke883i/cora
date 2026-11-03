# CORA — Continuous Ontological Repository Assurance

**CORA (Continuous Ontological Repository Assurance)** is an offline-first, Python 3.11+ command-line **product** for investigating heterogeneous repositories, explaining evidence about software and files, and planning *strictly bounded* changes. **v1.experimental (`1.0.0a4`) is a prerelease candidate, not stable 1.0.0 or a public release.** CORA is **not** a universal dead-code detector, runtime-equivalence prover, or automatic code deleter.

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

## All-in-one holistic archaeology (experimental)

`holistic-audit` combines the safe read-only methods: Git provenance and bounded commit history, product/software ontology, partial import graph, manifest adapters, overlapping roles and development groups. `--focus` uses the per-file selector. A possible scaffold or disconnected gold flag means **human investigation**, not dead-code proof.

```bash
cora holistic-audit . --max-commits 256 --focus src/cora/graph.py --output /tmp/whole.json
cora verify-holistic /tmp/whole.json --repo .
cora archaeology . --output /tmp/history.json
cora verify-archaeology /tmp/history.json --repo .
cora annotate-groups /tmp/whole.json --repo . --hypotheses /tmp/ai.json
cora stress-archaeology --seed 883 --cases 1000000
```

AI observations are untrusted and uncalibrated; `--pr-index` declarations remain externally unverified. No transformations, remote scans or model calls are executed here. See the [holistic method](docs/HOLISTIC_FORENSICS.md), [DoD lattice](docs/DOD_HOLISTIC_FORENSICS.md), and [self-audit](docs/FORENSIC_SELF_AUDIT.md).

## Engineering debt and process modes (experimental)

`debt-scan` derives source-bound **debt signals** from bounded Git change pressure,
partial Python AST structure, declared product/role boundaries and optional
**untrusted** SARIF 2.1.0. Findings carry a finite debt category, evidence,
review priority, suggested validation/remediation strategy and human owner role.
They are neither proved defects nor measured costs, and **no command authorizes
remediation or deletion**. Missing scanner/runtime/test/CI provenance remains
explicit unknown, never a zero-debt assertion.

```bash
cora process-list
cora process-run . --process source --output /tmp/cora-source.json
cora process-run . --process debt --max-commits 12 --output /tmp/cora-debt-process.json
cora process-run . --process full --max-commits 12 --focus src/cora/graph.py --output /tmp/cora-full.json
cora verify-process /tmp/cora-full.json --repo .
cora debt-scan . --max-commits 12 --output /tmp/cora-debt.json
cora verify-debt /tmp/cora-debt.json --repo .
cora debt-diff . --base HEAD~1 --head HEAD --output /tmp/cora-trend.json
cora stress-debt --seed 883 --cases 1000000
```

`process-run` supports `source`, `history`, `architecture`, `forensics`, `debt`,
`verification`, `full`. **`full` is only the union of safe read-only Git-backed
methods**, not LLM invocation, third-party scanner execution, target tests,
archiving or transformations. External SARIF requires the original input bytes
again for `verify-debt`. A trend shows newly detected vs no-longer-detected
signals; it does **not** prove a debt was remediated. See [methods](docs/ENGINEERING_DEBT.md)
and [backward DoD](docs/DOD_ENGINEERING_DEBT.md).

## ZIP intake and optional runtime observation (PR-16 integrated)

`zip-intake` rejects malformed or hostile ZIP paths and classifies a content tree, **not** Git history. `verify-zip-intake` replays that source receipt. `runtime-observe` is separate, explicit opt-in: it requests restrictive Docker flags but does **not** independently attest host isolation or arbitrary target test coverage. `fuse-evidence` reconciles report digests without turning them into authenticated runtime proof; `verify-fusion` replays the reconciliation. `lattice-audit` builds the typed DoD obligation DAG, and `verify-lattice` recomputes it from the original ZIP; neither authorizes release.

```bash
cora zip-intake source.zip --output /tmp/cora-zip.json
cora verify-zip-intake /tmp/cora-zip.json --archive source.zip
cora fuse-evidence /tmp/cora-zip.json --output /tmp/cora-fusion.json
cora verify-fusion /tmp/cora-fusion.json --zip-report /tmp/cora-zip.json
cora lattice-audit source.zip --zip-report /tmp/cora-zip.json --output /tmp/cora-lattice.json
cora verify-lattice /tmp/cora-lattice.json --archive source.zip --zip-report /tmp/cora-zip.json
```

The [PR-16 source CI](.github/workflows/ci-semantic-lattice.yml) runs complete unit regression with line/branch coverage floors and an independently compared Git batch-subprocess fixture; neither is a production benchmark or sandbox attestation. These capabilities were merged in PR-16, but do not certify Docker isolation or release readiness. The Docker executor is not a safe default for hostile code: independent sandbox, resource and host authorization remain external. See [PR-16 DoD lattice](docs/DOD_PR16_SEMANTIC_LATTICE.md).

## AI coding-agent and contextual gold assurance (PR-17–PR-19)

PR-17/18 introduced `dod-plan`, `dod-assess` and `verify-dod` for generic reverse-derived DoD, plus 10M finite-model scenarios, physical CORA model mutants and non-promoting receipts. PR-19 absorbs 12 gold patterns and R1–R4 through `gold-plan` (contextual DoD), `gold-pilot` (six pinned Git blobs from ICTC/ikant/aosp1), `gold-mutate` (bounded private physical source mutants), `gold-effects` (potential CI effects) and `stress-gold` (10 preseeded × 1M *synthetic* typed faults). Candidate CI verifies **ICTC public source only (1/3)**; private ikant/aosp1 remain **BLOCKED** pending authorized readback. Green CI is not a 3/3 source pilot. No Git blob proves owner truth, no syntax mutant proves target behavior and no CI artifact authenticates release. See [closure audit](docs/AUDIT_PR19_CLOSURE.md).

Run `cora gold-plan --intent 'Deliver a testable repository change'`, `cora gold-pilot --ictc-root ../ictc --ikant-root ../ikant --aosp1-root ../aosp1` on exact pinned checkouts, and `cora stress-gold --require-full` for changed model policy. Docker target execution is never implicit. Details: [Gold method](docs/GOLD_ASSURANCE.md), [reticular DoD](docs/DOD_PR19_GOLD.md), [PR-17](docs/DOD_PR17_AGENT.md) and [PR-18](docs/AUDIT_PR18_MAIN.md).

## Continuous development: coding agents must respect CORA

CORA is a **framework the coding agent must satisfy, not an agent that writes or approves code**. Three additional source-bound checks distinguish PR changes, post-merge monitoring and untrusted agent proposals:

```bash
cora dev-premerge . --base HEAD~1 --head HEAD --output /tmp/premerge.json
cora verify-dev-gate /tmp/premerge.json --repo .
cora dev-postmerge . --previous HEAD~1 --head HEAD --with-debt --output /tmp/postmerge.json
cora verify-dev-gate /tmp/postmerge.json --repo .
cora agent-check /tmp/agent-proposal.json --repo .
cora stress-continuous --seed 883 --cases 1000000
```

The pre-merge policy is always read from the **BASE commit**; changing it in a PR cannot change the trusted-base classification. For a new target repository with no base policy, CORA returns `BOOTSTRAP_REVIEW_REQUIRED`; on CORA main the policy was introduced by PR-14. Neither state is independent approval. Review roles are proposed, **not authenticated**, and GitHub required checks/branch protections still need an administrator. A post-merge debt delta is a trend of *signals*, not proven defects or production outcome. Every report has `authorization=NONE`. See [agent instructions](AGENTS.md), [method](docs/CONTINUOUS_DEVELOPMENT.md), [DoD](docs/DOD_CONTINUOUS.md) and [governance](GOVERNANCE.md).

## Release readiness — source checks are not release authorization

Run the independent source-contract check and the CORA-on-CORA methods before preparing a GitHub Release:

```bash
python tools/verify_release_readiness.py --repo . --output /tmp/cora-release-readiness.json
cora process-run . --process full --revision HEAD --max-commits 12 --output /tmp/cora-full.json
cora verify-process /tmp/cora-full.json --repo .
```

A **source-contract PASS** confirms local metadata/documentation/policy consistency only. A governed release requires independently observed CI at the exact commit, non-author review, enforced branch protection, built and independently checked wheel/sdist, provenance and a release decision. **Current release authority is BLOCKED until external controls are attested.** Follow the [release procedure](docs/RELEASE.md), [DoD lattice](docs/DOD_RELEASE_READINESS.md) and [main self-audit](docs/AUDIT_PR15_MAIN.md). The name expansion was adopted as a present-day product definition; no earlier historical expansion is asserted.

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

**CORA v1.experimental = package `1.0.0a4`**, a PEP 440/SemVer-style *pre-release identity*, not a stable API promise. The PR candidate is reviewed with checksums and GitHub CI artifacts; no public PyPI package, signed SLSA provenance or GitHub Release is implied. The [DoD](docs/DOD_V1_EXPERIMENTAL.md) distinguishes automated scoped PASS from still-open human and external validation gates.

[License](LICENSE) · [Changelog](CHANGELOG.md) · [Security reporting](SECURITY.md) · [Source/decision history](docs/ARCHITECTURE.md).
