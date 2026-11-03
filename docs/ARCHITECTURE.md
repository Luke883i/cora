# Architecture — CORA as product, software and repository

**Scope:** CORA — Continuous Ontological Repository Assurance, v1.experimental (`1.0.0a4` prerelease candidate), current source integrated through merged PR-20. This document describes the current architecture; historical ADRs preserve earlier milestone decisions. The [README](../README.md) is the front door; this document is the engineering explanation. The [committed ontology](../cora.ontology.json) is a *declaration* by project maintainers, not an inference from folder names.

## Three non-equivalent boundaries

- **Product `cora`:** externally usable capability and observable contract of a local evidence-first CLI. Its ownership may encompass multiple software components and repositories in the future; its *current* canonical source is this Git repository.
- **Software `cora-engine`:** Python modules under `src/cora/`, served by the single `cora.cli:main` entrypoint. It implements only the bounded features listed below. **Software `cora-release-verification`** is tooling under `tools/` for building/checking artifacts; it is not a production backend.
- **Repository `Luke883i/cora`:** one Git source and change-provenance boundary containing product declarations, Python software, tests, contracts, ADRs, CI and release-candidate workflow. A repository is neither a deployed instance nor proof of complete product boundaries.

Deployables: **wheel** and **sdist**, presently review-only, not public releases. Runtime: on-demand CLI process in a user's environment. Artifact: content-addressed file/record/certificate associated with a commit. No daemon, SaaS backend, central registry, dashboard or scheduled runtime is provided.

## Component map (what each module really does)

| Module | Role | Evidence or safety boundary |
| --- | --- | --- |
| `cli.py`, `__init__.py` | One package entrypoint and version | No alternative API/daemon claimed |
| `audit.py` | Working-tree filesystem inventory, declared ownership | No runtime or dynamic dependency closure |
| `git_snapshot.py`, `evidence.py` | Committed Git blobs, canonical records, ledger and domain-separated digests | Git provenance is not independent signing |
| `ontology.py`, `graph.py` | Validated declared products/software, typed graph, partial Python AST candidate imports, path explanations | No proof of complete imports, reachability or execution |
| `adapters.py` | Partial manifest readers for Node, Python, Rust, Go and Maven | Declared dependencies, not installed/used dependencies |
| `closure.py` | Fixed narrow observational obligations and counterexamples; Git-revalidated certificates | `PASS_SCOPED` is **not** authorization to delete |
| `file_lab.py`, `artifact_roles.py`, `file_lab_stress.py` | Multi-scale read-only per-file dependency dossier, untrusted AI/runtime annotations, human triage intents, synthetic falsifier | No automatic dead-code proof, calibrated probability, external runtime attestation or deletion |
| `archaeology.py`, `holistic.py`, `group_hypotheses.py` | Commit-bounded development archaeology, co-change groups and AI hypotheses | Historical association is not a runtime dependency or PR-authenticated event |
| `debt.py`, `process_suite.py` | Multi-scale debt signals and seven bounded read-only process modes | Heuristic debt signals; no calibrated defect rate or executed target test/scanner |
| `continuous.py`, `continuous_stress.py` | Base-anchored pre/post-merge receipts, agent-claim reconciliation and finite policy falsification | Review routing is not hosting enforcement, verified reviewer identity or deployment truth |
| `transform.py` | Exact tracked-document path plan, approval, check, owned-file compensating rollback | Not syntax-aware source refactor; user verifier is untrusted/unsandboxed |
| `guard.py`, `guard_runtime.py` | Vendored local Git/AST boundary check and workflow | Cannot self-enforce against modification; depends on trusted required checks |
| `mutations.py`, `mutation_evidence.py`, `graph_stress.py`, `adapter_stress.py`, `closure_stress.py`, `transform_stress.py` | Deterministic synthetic oracles | Independent real-world source truth *not* established by large case count |
| `tools/build_candidate.py`, `release_verify.py`, `external_validate.py`, `release_stress.py` | Reproducible candidate packaging, archive checks, isolated installs and fixture tests | Not signed provenance, published release or external production validation |

## Evidence flow, from immutable source to scoped answer

```text
Git commit -> snapshot/ledger -> declared ontology + partial adapters
                              -> typed graph / unresolved findings
                              -> closure with mandatory obligations
                              -> PASS_SCOPED | BLOCKED | REFUTED
```

A single recorded evidence digest *traces a claim*, not a cryptographic attestation of an external reality. Graph edges are typed as declarations/candidates, not generic "usage". `REFUTED` is relative to a claim and a named commit. An empty graph path is not a deletion certificate.

The **continuous lifecycle** path is a distinct observational route: committed BASE policy -> proposed HEAD changed paths -> replayed pre-merge receipt -> independently protected CI and human review outside CORA -> committed merge -> post-merge source/debt delta. The receipts always carry `authorization=NONE`. A green workflow can mean correct detection of an unapproved bootstrap; it cannot authenticate an approver. See [continuous development](CONTINUOUS_DEVELOPMENT.md), [release DoD](DOD_RELEASE_READINESS.md) and [standard release procedure](RELEASE.md).

The optional **maintenance** path is deliberately separate: clean Git worktree -> read-only document rename plan -> explicit digest approval -> controlled owned-file changes -> user-specified test command -> owned-file hash validation -> receipt or compensating rollback. The local guard monitors selected Git/AST changes and must be protected by an independent required check in the hosting platform.

## Repo navigation / novice engineer challenge

Starting at the root, an engineer should find answers without prior PR history: What is CORA? What is deliberately not supported? How do I install and audit a repo? Which source modules implement the capabilities? What evidence proves the last revision? Where do I run tests and report security issues? The [README](../README.md) answers the first three; this map and `src/cora/` answer the next; [DoD](DOD.md), `tests/`, `.github/workflows/` and [security](../SECURITY.md) answer the rest. Automatic checks validate links and commands; genuine human comprehension requires the independent first-read review described in [DoD](DOD.md).

## Artifact roles are not file name inference

`cora.artifact-roles.json` declares overlapping artifact roles for the immutable Git tree. A file may simultaneously be implementation, executable test, contract verifier, fixture and governance mechanism. The role declaration is not proof that the test passes, that a contract is enforced in CI, or that runtime consumers have been observed. The `artifact-audit` command reports unclassified files and unused rules; `verify-artifacts` independently recomputes the report from Git. An incomplete role registry is **not** a deletion oracle.

## PR-16 integrated source archives and optional observations

The integrated PR-16 adds `archive_intake.py` (bounded ZIP inspection and source tree identity), `runtime_observation.py` (separately requested Docker unittest invocation), and `observation_fusion.py` (receipt reconciliation without authenticity elevation). The `git_snapshot.py` source reader uses bounded Git cat-file batches. These components do not add a daemon, trusted sandbox, authenticated human reviewer or release authority. A ZIP tree cannot recover Git history; an exit code is not code coverage; a digest is not a signature. `process-run full` remains read-only and does not trigger Docker.

See [semantic lattice DoD](DOD_PR16_SEMANTIC_LATTICE.md). Product/readiness documentation describes candidate source only until a PR is validated on its exact HEAD and merged by independently governed hosting controls.

## PR-17 AI coding agent semantic DoD control plane

The new cora.agent-dod.json declares 24 fault families, four intermediate cuts, two global goals and ten deterministic seeds. src/cora/agent_assurance.py compiles a reverse-derived proof plan and reconciles untrusted agent claims; src/cora/agent_saturation.py challenges its finite model with a separate oracle. Both remain subordinate to the single CORA engine and its source/runtime boundary. No delegated merge or release authority. See AI_CODE_ASSURANCE.md.

## PR-19 gold assimilation without parallel software identities

The **product** remains CORA, with one engine (`cora-engine`) and one independent release verification software identity. The existing `cora` CLI gains five bounded methods: `gold_assurance.py` (contextual R1/DoD/Git readback and R4 pilot), `gold_mutations.py` (physical temp-file mutants, optional consented Docker oracle), `gold_effects.py` (R3 potential side effects, untrusted claims), and `gold_saturation.py` (10M finite typed fault model). The **repository** registers `cora.gold-assurance.json`, 3 actual pinned source pilot pairs, CI/test/roles, the gold method and a scoped DoD. No new coding agent, writer, roadmap or release authority is created.

The PR-19 cross-repository source check is **access-scoped**: public ICTC Git blob replay can run on a normal candidate PR; private ikant and aosp1 readbacks remain blocked without independently authorized local checkouts. The CI proves that it refuses to promote 1/3 source evidence into 3/3 and produces a machine-readable blocker. The optional Docker oracle refuses root-host execution and uses the invoking UID/GID so private temporary files remain private. Neither CI-green nor these controls prove product runtime, protected hosting or human release authority.

## PR-20 reticular convergence under one product/software owner

`src/cora/reticulum.py` centralizes DAG source cut derivation, finite non-compensatory model propagation and declared path witness invalidation; `agent_assurance.py` and `gold_assurance.py` reuse the same kernel, retaining their fixed profile contracts. The existing `continuous.py` optionally composes base-pinned policy/actual Git change with committed ontology (`ontology.py`), candidate import graph (`graph.py`), invalidation (`reticulum.py`) and potential workflow effects (`gold_effects.py`). `gold_saturation.py` adds a 16-factor, 10x1M preseeded finite model. The new contract is `cora.convergence-dod.json` with source vs full R1–R4 vs governed goals; it is a PR-editable policy artifact, not hosting authority. The product is still CORA, with two existing software IDs and a single CLI; no daemon, runtime executor, deployment or new coding agent. See [method](CONVERGENT_ASSURANCE.md) and [DoD](DOD_PR20_CONVERGENCE.md).

Intent-to-proof in PR-20 is an explicitly supplied, bounded **per-change** statement digested with BASE/HEAD; it is never human approval. For delete/rename/type changes the contextual adapter replays the BASE import graph as well as HEAD, closing an avoidable false-negative on removed Python modules while keeping dynamic import edges unproven. The PR-16 archived evidence-lattice topology also uses the canonical dependency validator; its historical status labels and digests remain unchanged.

## Current documentation topology (post PR-20)

The [README](../README.md) is the product entry point. The [documentation index](INDEX.md) connects reader-oriented [onboarding](GETTING_STARTED.md), [AI agent adoption](AGENT_ADOPTION.md), methods, [CLI reference](CLI_REFERENCE.md), DoDs and historical ADR/audit material. The [documentation registry](documentation-registry.json) declares one role/status for every Markdown and retains the original baseline blob identity for historical source. This declaration is checked by `tools/verify_documentation.py` and the [documentation DoD](DOCUMENTATION_DOD.md); it does not establish human comprehension or authenticated reviewer approval.

The active architecture remains **one CORA product and one Python CLI**. `reticulum.py` supplies common dependency topology, `continuous.py` the BASE-pinned contextual adapter, and the original source/runtime/Gold packages preserve their domain-specific evidence boundaries. The prior PR-16, PR-17 and PR-19 sections above are historical implementation lineage, not alternative current product identities.
