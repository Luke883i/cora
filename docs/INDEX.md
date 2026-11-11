# CORA documentation — navigate by goal

Start at the [README](../README.md): a source-scoped product promise, a three-step engineering method, a ten-method correlation map and two source-linked project examples. This index routes readers by task, method and evidence class; it is navigation, not a release authority or an independent witness.

## How to navigate

The [README](../README.md) is the **compressed public front door**: outcome, method, concrete project histories, first use and boundaries. Implementation and historical detail belongs in the linked guides. This file remains the **exhaustive 48-document index**, not a second landing page. Read in the order: README → user task → current method → applicable DoD and source evidence → historical ADR/audit only when needed. Links and document classifications are checked by `tools/verify_documentation.py`; navigation alone does not establish user comprehension.

## Choose your path

- **New to CORA:** [Getting started](GETTING_STARTED.md) → [Architecture](ARCHITECTURE.md) → [Understanding evidence and limitations](DOD_V1_EXPERIMENTAL.md).
- **Using an AI coding assistant:** [Agent adoption](AGENT_ADOPTION.md) → [Agent method](AI_CODE_ASSURANCE.md) → [Convergent assurance](CONVERGENT_ASSURANCE.md) → [complete R1–R4 obligations](DOD_PR20_CONVERGENCE.md).
- **Auditing an existing repository:** [File Lab](FILE_LAB.md) → [Holistic forensics](HOLISTIC_FORENSICS.md) → [Engineering debt](ENGINEERING_DEBT.md).
- **Comparing CORA with established engineering methods:** [Method crosswalk](CONVERGENT_ASSURANCE.md#method-crosswalk--borrowed-perspectives-not-full-implementations) → [Architecture](ARCHITECTURE.md) → [Evidence limits](DOD_V1_EXPERIMENTAL.md).
- **Reviewing a PR or release:** [Continuous development](CONTINUOUS_DEVELOPMENT.md) → [Governance](../GOVERNANCE.md) → [Release procedure](RELEASE.md).
- **Looking for syntax and inputs:** [CLI reference](CLI_REFERENCE.md), [committed ontology](../cora.ontology.json), [role registry](../cora.artifact-roles.json).
- **Censusing all implemented command surfaces:** [Capability atlas](../.cora/assurance/capability-atlas.json) → [CLI reference](CLI_REFERENCE.md) → [architecture](ARCHITECTURE.md) → [capability DoD](../.cora/contracts/dod/capability-dod.json). These are source/test witnesses, not behavior certification.
- **Tracing the five synergic goals:** [Convergent assurance](CONVERGENT_ASSURANCE.md) → [five-goal reticulum](../.cora/contracts/dod/five-synergies-dod.json) → [preseeded semantic mutants](../.cora/fixtures/five-synergies-mutants.json). Results are source-scoped; runtime and approval remain separately governed.
- **Running integrated source-to-document convergence:** [Convergent assurance service](CONVERGENT_ASSURANCE.md) → [typed lattice](../.cora/contracts/profiles/type-assurance-profile.json) → [canonical CLI](CLI_REFERENCE.md). Original software owners remain responsible; model-supplied hypotheses are untrusted.
- **Auditing code tenuta by object type:** [Typed assurance crosswalk](../.cora/contracts/profiles/type-assurance-profile.json) → [bounded method and R3 DoD](CONVERGENT_ASSURANCE.md) → [Git-bound verifier](../tools/verify_type_assurance.py). This is a source-candidate analysis, not an ISO certificate or product-ready claim.

**PR38 history / future change source audit:** [37 PRs and 305 commit deltas](../.cora/assurance/history/pr01-37-commit-diff-audit.json) → [severe 32-node DoD](../.cora/contracts/dod/history-convergence-dod.json) → [CLI guidance](CLI_REFERENCE.md). PR34 is closed without merge, and the 28 former paths require mapping, not deletion. New modules, tests, CI and DoDs must converge with canonical inventories.

**Cross-repository portability (PR50 candidate):** [Reticular source/external DoD](../.cora/contracts/dod/crossrepo-convergence-dod.json) -> [portable One-Run method and usage](CONTINUOUS_DEVELOPMENT.md#cross-repository-sourceevidence-convergence-pr50--candidate). Neither target-owned profile nor source byte readback creates runtime or human authority.

**Integrated source dossier:** the [PR37 v2 contract](../.cora/contracts/dod/integrated-one-run-dod.json) composes the PR36 source gates with a Git-pinned activity census, typed plans, local evidence and an offline forensic atlas. Product acceptance remains external and unverified.

**Contract paths:** the only root-facing JSON contracts are `cora.ontology.json` and `cora.artifact-roles.json`. Find the eighteen internal DoDs, two profiles and two assurance records using the [contract-path index](../.cora/contracts/index.json). Git-baselined path rewrites are source-scoped: they do not attest third-party runtime compatibility or conformance.

**Archive invariant:** `docs/archive/` contains immutable historical Git blobs; [the relocation map](../.cora/layout-migration.json) records original-to-current paths and protected exceptions. Historical text is not rewritten, not product authority and not a safe-deletion signal. Read current procedures above before relying on old decisions.

## Document semantics

**CURRENT** means active source documentation; **SCOPED_CURRENT** is active only in its named domain; **HISTORICAL** records a specific earlier state and must not override current product claims. A DoD is a declared obligation, not evidence that the requirement has been satisfied. A Git SHA or a deterministic replay proves a bounded source relationship, not runtime correctness, review authority or release approval.

Machine inventory: [documentation registry](documentation-registry.json); [documentation DoD](DOCUMENTATION_DOD.md) and [machine lattice](../.cora/contracts/dod/documentation-dod.json). The [README claim/evidence profile](../.cora/assurance/documentation-proofs.json) and [Git-bound verifier](../tools/verify_claim_evidence.py) add revision-bound, falsifiable source traces for S01–S18 without promoting them to host or runtime attestation. Historical records are archived byte-for-byte under `docs/archive/`; three link-dependent historical documents remain in their original paths with documented exceptions.

## Complete Markdown inventory

### 00 — Product

- [README](../README.md) — CURRENT · LANDING

### 01 — Identity, governance, contribution, architecture

- [PULL REQUEST TEMPLATE](../.github/PULL_REQUEST_TEMPLATE.md) — CURRENT · METHOD
- [AGENTS](../AGENTS.md) — CURRENT · GOVERNANCE
- [CHANGELOG](../CHANGELOG.md) — CURRENT · CHANGELOG
- [CONTRIBUTING](../CONTRIBUTING.md) — CURRENT · METHOD
- [GOVERNANCE](../GOVERNANCE.md) — CURRENT · GOVERNANCE
- [SECURITY](../SECURITY.md) — CURRENT · GOVERNANCE
- [ARCHITECTURE](ARCHITECTURE.md) — CURRENT · ARCHITECTURE

### 02 — Product DoD and release

- [AUDIT PR15 MAIN](archive/audits/AUDIT_PR15_MAIN.md) — HISTORICAL · AUDIT
- [DOD](DOD.md) — HISTORICAL · DOD
- [DOD RELEASE READINESS](DOD_RELEASE_READINESS.md) — CURRENT · DOD
- [DOD V1 EXPERIMENTAL](DOD_V1_EXPERIMENTAL.md) — CURRENT · DOD
- [RELEASE](RELEASE.md) — CURRENT · METHOD

### 03 — Forensics, evidence, engineering debt

- [ARTIFACT SEMANTICS](ARTIFACT_SEMANTICS.md) — CURRENT · METHOD
- [AUDIT PR01 PR07](AUDIT_PR01_PR07.md) — HISTORICAL · AUDIT
- [DOD ENGINEERING DEBT](DOD_ENGINEERING_DEBT.md) — CURRENT · DOD
- [DOD HOLISTIC FORENSICS](DOD_HOLISTIC_FORENSICS.md) — CURRENT · DOD
- [DOD SELECTION](DOD_SELECTION.md) — CURRENT · DOD
- [ENGINEERING DEBT](ENGINEERING_DEBT.md) — CURRENT · METHOD
- [FILE LAB](FILE_LAB.md) — CURRENT · METHOD
- [FORENSIC SELF AUDIT](archive/audits/FORENSIC_SELF_AUDIT.md) — HISTORICAL · AUDIT
- [HOLISTIC FORENSICS](HOLISTIC_FORENSICS.md) — CURRENT · METHOD
- [STANDARDS MAINTENANCE AUDIT](STANDARDS_MAINTENANCE_AUDIT.md) — HISTORICAL · AUDIT

### 04 — AI coding assurance and continuous DevOps

- [AI CODE ASSURANCE](AI_CODE_ASSURANCE.md) — CURRENT · METHOD
- [AUDIT PR18 MAIN](archive/audits/AUDIT_PR18_MAIN.md) — HISTORICAL · AUDIT
- [CONTINUOUS DEVELOPMENT](CONTINUOUS_DEVELOPMENT.md) — CURRENT · METHOD
- [DOD CONTINUOUS](DOD_CONTINUOUS.md) — CURRENT · DOD
- [DOD PR17 AGENT](archive/dod/DOD_PR17_AGENT.md) — HISTORICAL · DOD

### 05 — Reticular gold and convergence

- [AUDIT PR19 CLOSURE](archive/audits/AUDIT_PR19_CLOSURE.md) — HISTORICAL · AUDIT
- [CONVERGENT ASSURANCE](CONVERGENT_ASSURANCE.md) — CURRENT · METHOD
- [DOD PR16 SEMANTIC ASSURANCE](archive/dod/DOD_PR16_SEMANTIC_ASSURANCE.md) — HISTORICAL · DOD
- [DOD PR16 SEMANTIC LATTICE](DOD_PR16_SEMANTIC_LATTICE.md) — SCOPED_CURRENT · DOD
- [DOD PR19 GOLD](DOD_PR19_GOLD.md) — SCOPED_CURRENT · DOD
- [DOD PR20 CONVERGENCE](DOD_PR20_CONVERGENCE.md) — SCOPED_CURRENT · DOD
- [GOLD ASSURANCE](GOLD_ASSURANCE.md) — CURRENT · METHOD

### 06 — Architectural decision records

- [ADR PR01](archive/decisions/ADR-PR01.md) — HISTORICAL · ADR
- [ADR PR02](archive/decisions/ADR-PR02.md) — HISTORICAL · ADR
- [ADR PR03](archive/decisions/ADR-PR03.md) — HISTORICAL · ADR
- [ADR PR04](archive/decisions/ADR-PR04.md) — HISTORICAL · ADR
- [ADR PR05](archive/decisions/ADR-PR05.md) — HISTORICAL · ADR
- [ADR PR06](archive/decisions/ADR-PR06.md) — HISTORICAL · ADR
- [ADR PR07](archive/decisions/ADR-PR07.md) — HISTORICAL · ADR
- [ADR PR15](archive/decisions/ADR-PR15.md) — HISTORICAL · ADR

### 07 — Documentation onboarding and reference

- [GETTING STARTED](GETTING_STARTED.md) — CURRENT · METHOD
- [AGENT ADOPTION](AGENT_ADOPTION.md) — CURRENT · METHOD
- [CLI REFERENCE](CLI_REFERENCE.md) — CURRENT · REFERENCE
- [DOCUMENTATION DOD](DOCUMENTATION_DOD.md) — CURRENT · DOD

**PR40 source knowledge convergence:** [19-node engineering DoD](../.cora/contracts/dod/engineering-knowledge-dod.json) → [existing debt method](ENGINEERING_DEBT.md) → [Git replay and 10M bounded falsifier](../tools/verify_engineering_closure.py). This records static callsite indicators and explicitly unobserved runtime; it does not certify GitHub host governance, product usability or external approval.

**Final experimental release convergence:** [30-node final source/external AND DoD](../.cora/contracts/dod/final-experimental-dod.json) → [current pre-release checklist and operator protocol](RELEASE.md) → [exact Git, physical fixture and 1M finite-model verifier](../tools/verify_final_experimental.py). A SOURCE pass is not a public release; seven independent external obligations remain noncompensatory.
