# Architecture — CORA as product, software and repository

**Document status:** CURRENT
**Current scope:** Actual CORA product, two software boundaries and Git evidence topology.
**Operational use:** Locate original owners, method entrypoints and epistemic boundaries.
**Evidence:** Committed ontology, CLI source modules, tests and release-verifier code.
**Limits:** A static component map is neither complete dynamic reachability nor release approval.


**Scope:** CORA — Continuous Ontological Repository Assurance is an experimental local Git evidence tool. Package `1.0.0a5` is implemented in src/cora/chat_bundle.py for portable handoff; this source implementation does not authenticate a public release. The [README](../README.md) is the product entry and the [committed ontology](../cora.ontology.json) declares component ownership. Real maintained-target acceptance and effective host review remain `BLOCKED_EXTERNAL`. Historical decisions remain original Git evidence, not alternate current architecture.

**Final experimental qualification:** the existing source-reticulum and independent Git oracle reuse the canonical CLI, original source owners and debt/capability catalogs. The [30-node final DoD](../.cora/contracts/dod/final-experimental-dod.json) distinguishes a closed source candidate from seven externally observed conditions; no extra product, agent, or orchestrator is introduced. The actual PR merge and subsequent tag/asset checks determine immutable release identity, not document phrasing.

**Current One-Run integration:** `process_suite.run_suite` projects advisory `practice_obligations` from original Git. The opt-in `--change-base BASE_SHA` enables an explicit complete Git change range under the v2 projection; default v1 is single-commit first-parent. Both One-Run renderers display review obligations without a ninth source method or second executor. Documentation candidates for other repositories come from their own tracked Git trees, not CORA's directory assumptions. Source evidence never grants runtime or release authority.

**Closure owner:** [governance decision record](../GOVERNANCE.md#product-software-and-repository--bounded-closeout) and [release DoD](DOD_RELEASE_READINESS.md). Module existence does not authenticate runtime, host or support.

## Three non-equivalent boundaries

- **Product `cora`:** externally usable capability and observable contract of a local evidence-first CLI. Its ownership may encompass multiple software components and repositories in the future; its *current* canonical source is this Git repository.
- **Software `cora-engine`:** Python modules under `src/cora/`, served by the single `cora.cli:main` entrypoint. It implements only the bounded features listed below. **Software `cora-release-verification`** is tooling under `tools/` for building/checking artifacts; it is not a production backend.
- **Repository `Luke883i/cora`:** one Git source and change-provenance boundary containing product declarations, Python software, tests, contracts, ADRs, CI and release-candidate workflow. A repository is neither a deployed instance nor proof of complete product boundaries.

Deployables: **wheel** and **sdist**, presently review-only, not public releases. Runtime: on-demand CLI process in a user's environment. Artifact: content-addressed file/record/certificate associated with a commit. No daemon, SaaS backend, central registry, dashboard or scheduled runtime is provided.

<a id="product-category-target-and-evidence-boundaries-post-pr52"></a>
## Product category, target and evidence boundaries

**Category:** agent-agnostic developer tooling / engineering assurance. **Primary task:** assess a bounded software change from intent and falsifiable acceptance conditions through Git source, target-native observations and unresolved debt. **Primary readers:** developers, AI coding-agent operators, maintainers, reviewers and CTOs. The research method (CORA-METHOD) can guide an external agent without invoking this package; the executable (CORA-ENGINE) is the existing local Python CLI, not an autonomous feature writer. The repository is the versioned source and evidence boundary, not the runtime product and not an independent approval authority.

**Transfer scope:** original-Git analysis is multi-repository; partial Python AST and static JavaScript ESM are not full architecture or dynamic behavior discovery. The native Gold pilots exercise Teddy Node and ICTC HTTP/SQLite under explicit consent; original LUMEN browser and NILO remote deployment controls remain unexecuted. An arbitrary new target requires its own authoritative oracle, isolated test environment and typed evidence. Neither a Git SHA nor a native subprocess exit authenticates an independent reviewer.

**CTO assurance vocabulary:** package `cora-audit 1.0.0a5` / CLI `cora`, Python 3.11+, MIT; no mandatory runtime Python package dependencies declared. The current candidate build creates locally verified wheel/sdist and SHA256SUMS but does not publish or sign a release. Candidate CI constructs CycloneDX 1.6 for the actual wheel and sdist, records installed build-tool versions, scans only those direct build tools with pip-audit, and replays an **unsigned** Git/artifact observation. Build transitives, optional target-native environments, independent scanner/feed trust, artifact signing, SLSA/in-toto provenance, host enforcement and security/update SLA remain unqualified. See [Security](../SECURITY.md) and [Release](RELEASE.md). These statuses are explicit evaluation debt, not claims of an insecure implementation or of enterprise acceptance.

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
| `workflow_rationalization.py`, `method_synthesis.py` | Git-bound workflow candidate review and same-commit evidence correlation | Neither supplies independent consumers, behavioral equivalence or authenticated AI conclusions |
| `.cora/assurance/capability-atlas.json`, `tools/verify_capability_atlas.py` | CLI/method/test-source inventory with Git OIDs and exact revision replay | Source witness and dispatch wiring do not prove test execution or product completeness |
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

Starting at the root, an engineer should find answers without prior PR history: What is CORA? What is deliberately not supported? How do I install and audit a repo? Which source modules implement the capabilities? What evidence proves the last revision? Where do I run tests and report security issues? The [README](../README.md) answers the first three; this map and `src/cora/` answer the next; [current product DoD](DOD_V1_EXPERIMENTAL.md), `tests/`, `.github/workflows/` and [security](../SECURITY.md) answer the rest. Automatic checks validate links and commands; genuine human comprehension requires the independent first-read review described in the [documentation acceptance DoD](DOCUMENTATION_DOD.md).

## Artifact roles are not file name inference

`cora.artifact-roles.json` declares overlapping artifact roles for the immutable Git tree. A file may simultaneously be implementation, executable test, contract verifier, fixture and governance mechanism. The role declaration is not proof that the test passes, that a contract is enforced in CI, or that runtime consumers have been observed. The `artifact-audit` command reports unclassified files and unused rules; `verify-artifacts` independently recomputes the report from Git. An incomplete role registry is **not** a deletion oracle.

<a id="cross-cutting-source-owners-pr16pr20-lineage"></a>
## Shared source owners and proof boundaries

The architecture has one `cora` CLI and no second orchestrator. These are the surviving source owners, **not** competing product identities or current release decisions:

- **Source intake:** `git_snapshot.py` reads original Git blobs; `archive_intake.py` checks bounded ZIPs without recovering authentic Git history; `runtime_observation.py` requires separate consent and does not attest Docker host isolation; `observation_fusion.py` cannot elevate untrusted observations. [Lattice DoD](DOD_PR16_SEMANTIC_LATTICE.md).
- **Agent/Gold contracts:** `agent_assurance.py`, `gold_assurance.py` and finite-mutation counterparts bind claims to source and known blockers. Three pilot declarations are not three independently executed targets; private repos need authorized access. [Gold evidence](GOLD_ASSURANCE.md) · [Agent assurance](AI_CODE_ASSURANCE.md).
- **One reticulum:** `reticulum.py` supplies noncompensatory AND-gate dependencies reused by agent/Gold and BASE-to-HEAD `continuous.py`. User-supplied intent is not review approval. Missing dynamic dependencies, execution and host controls remain `BLOCKED_EXTERNAL`. [Method](CONVERGENT_ASSURANCE.md) · [DoD](DOD_PR20_CONVERGENCE.md).

Historical reasoning and original claims remain at their immutable Git revisions, not copied into this current architecture map.

<a id="current-documentation-topology-merged-pr-25-baseline"></a>
## Current documentation ownership

The [README](../README.md) is the product entry point. The [documentation index](INDEX.md) connects reader-oriented [onboarding](GETTING_STARTED.md), [AI agent adoption](AGENT_ADOPTION.md), methods, [CLI reference](CLI_REFERENCE.md), DoDs and historical ADR/audit material. The [documentation registry](documentation-registry.json) declares one role/status for every Markdown and retains the original baseline blob identity for historical source. This declaration is checked by `tools/verify_documentation.py` and the [documentation DoD](DOCUMENTATION_DOD.md); it does not establish human comprehension or authenticated reviewer approval.

The active architecture remains **one CORA product and one Python CLI**. `reticulum.py` supplies common dependency topology, `continuous.py` the BASE-pinned contextual adapter, and the original source/runtime/Gold packages preserve their domain-specific evidence boundaries. Historical implementation records do not define another product identity.

<a id="experimental-comprehensive-one-run-activity-dossier-pr37"></a>
## Comprehensive One-Run evidence dossier

The single canonical CLI and original `process_suite.run_suite` remain owners of source execution. `integrated_registry.py` discovers parser/dispatch, source methods, test cases, tools and workflows from the exact Git commit. `integrated_run.py` extends the existing source-process receipt into a typed plan, all-activity ledger, blocker register, environment statement and byte-addressed local evidence manifest. `integrated_html.py` renders one escaped offline forensic view with per-activity and per-test navigation. The `--profile comprehensive` flag is opt-in; it does not turn all 71 parser commands, external workflows or untrusted code into automatically executable work. Local self-tests require separate exact-checkout consent; without externally proven isolation their exit states remain unauthenticated. The [55-node contract](../.cora/contracts/dod/integrated-one-run-dod.json) differentiates SOURCE witnesses from EXTERNAL acceptance and remains debt-blocked while its uncovered gates are addressed.

<a id="pr38-historical-genealogy-and-future-semantic-convergence"></a>
## Git genealogy and change invalidation

`genealogy.py` validates the [versioned corpus of 305 commit deltas](../.cora/assurance/history/pr01-37-commit-diff-audit.json) against original Git commit trees and parents where reachable, preserving closed/unmerged changes as noncanonical. Former root contract names and archived documents are retained as lineage, not evidence of unused runtime code. Exact BASE/HEAD source differences trigger registration obligations for new modules, tests, workflows and DoDs; runtime/consumer gaps remain debt. `integrated_run.py` stores genealogy in the existing JSON and evidence manifest; `integrated_html.py` provides searchable PR → commit → changed file → required check navigation. The [32-node DoD](../.cora/contracts/dod/history-convergence-dod.json) separates source properties from independent review, real-target benchmarking, isolation, human comprehension, GitHub host enforcement and deletion-consumer proof.


<a id="pr39--independent-product-qualification"></a>
## Independent acceptance boundaries and assurance levels

**Current interpretation:** the heading and `cora-independent-qualification/1` are **historical contract identities**, not evidence of an independent evaluator. Assurance is separated into **L1 engineering evidence** (source checks and actually reported test execution), **L2 experimental product validation** (bounded target behavior, with a qualified oracle), and **L3 optional external assurance** (third-party evaluation and governed release). L3 is **not a prerequisite to running CORA experimentally**; it is mandatory only for independently governed acceptance. A test run does not automatically establish L2 target acceptance, and L2 does not authenticate L3. Existing JSON schemas and digests are preserved.


The versioned [four-gate product DoD](../.cora/contracts/dod/independent-qualification-dod.json) is a noncompensatory sibling of the Git history reticulum. It extends the same One-Run runner, evidence manifest, JSON and offline Atlas. It does not add a second executor or run any target or host process by default. The Git-replayed qualification receipt shows source witness paths and explicit blockers for real maintained targets, human study, runtime host attestation and branch protection. The native-Git oracle is a distinct implementation but is not a distinct human owner; the GitHub host probe is an optional read-only observation but does not authenticate an independent reviewer. External acceptance and release authority are deliberately outside the source code.

<a id="alpha5-candidate-portable-chat-session-as-an-artifact-not-a-second-product"></a>
## Portable chat session as a bounded artifact

The existing `cora-engine` owns `src/cora/chat_bundle.py`, integrated only through `process-run --one-run --profile comprehensive` and `verify-process`. The portable ZIP contains strictly ordered, caller-authored steps, the existing comprehensive One-Run receipt, a reticularly derived DoD, a reader handoff, and a SHA-256 chained manifest. The output resides outside the inspected repository; appends are checked and atomically replaced. No additional coding agent, hosted service, external reviewer, command family, or source truth is introduced. The ZIP is append-only **as a sequence of validated records**, not bit-for-bit WORM storage or a cryptographically signed attestation.

An explicit invocation is required per chat iteration. The chat itself cannot guarantee this invocation or provide a signed human approval. All unresolved independent-target, usability, isolation, host enforcement and release gates remain `BLOCKED_EXTERNAL`.

