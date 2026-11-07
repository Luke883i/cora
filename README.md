# CORA — Continuous Ontological Repository Assurance

**CORA (Continuous Ontological Repository Assurance)** — **Engineering evidence for AI-assisted software changes.**

CORA is an **offline-first, Python 3.11+ command-line assurance framework** that helps developers and AI coding assistants inspect a Git repository, derive source-bound Definitions of Done (DoD), challenge claims with counterexamples, and produce reproducible pre/post-merge review reports. An AI assistant can propose or write code; CORA helps establish **what the change must demonstrate** before an accountable person accepts it. CORA is **not a coding agent**, a general runtime-equivalence prover, a universal dead-code detector, an automatic code deleter, or a merge authority.

**Why it matters:** a successful edit, a green test, a Git hash, and a convincing AI explanation are **different kinds of evidence**. None, alone, demonstrates product correctness, independent operational behavior, or permission to deploy. CORA makes the supported claims, missing evidence, falsifiers, and next review obligations visible.

**Current status:** `v1.experimental`; Python distribution **`cora-audit 1.0.0a4`**; source includes **merged PR41** and its *Final Experimental Baseline* contract. This is an integrated experimental **source** baseline, **not a stable API or verified public release**, independently qualified product, production service, or release authorization. The `v1.0.0a4` GitHub pre-release was observed as an **unpublished Draft without assets on 7 November 2026**; that dated observation is not a continuously verified host status. Consult [Release status](docs/RELEASE.md) and the [final experimental DoD](.cora/contracts/dod/final-experimental-dod.json) before making a release claim.

**Recommended use:** start with an authorized, read-only inspection of an exact Git `BASE` and `HEAD`; use CORA to organize the repository facts, candidate dependencies, counterexamples, source evidence, and unsatisfied verification obligations. Run real target tests and obtain independent review separately. Do not infer automatic remediation, approval, or safe deletion from a report.

**Audience and conditions:** software engineers, coding-agent operators, reviewers, maintainers, and assurance teams with legitimate repository access. The quickstart requires **Python 3.11+ and Git**. Optional target-side execution, ZIP/runtime/Docker experiments, network access, and user-supplied verifiers require distinct authorization and appropriate isolation. CORA does not provide a hosted service or production SLA.

**Open source license:** [MIT](LICENSE). The license permits reuse of CORA's code and documentation; it does not grant access to third-party repositories or authenticate a report. See [Security](SECURITY.md) and [Contributing](CONTRIBUTING.md).

## First five minutes — Quickstart

From an **authorized local checkout of CORA**, install its Python distribution and run a read-only inspection:

```sh
python -m pip install -e .
cora --help
cora version
cora audit . --output /tmp/cora-worktree.json
cora snapshot . --revision HEAD --output /tmp/cora-ledger.json
cora verify-ledger /tmp/cora-ledger.json --repo .
```

**Expected artifacts and meaning:**

- `cora-worktree.json`: a bounded inspection of the working tree; uncommitted material can affect this view.
- `cora-ledger.json`: the original-Git source inventory of the **pinned commit** `HEAD` resolved at execution time.
- `verify-ledger`: a consistency/replay check of that scoped Git observation, **not** certification of runtime behavior or reviewer identity.

Keep reports outside the source checkout; `/tmp` is a Unix example—choose an appropriate output directory on Windows. Use [`cora COMMAND --help`](docs/CLI_REFERENCE.md) for precise arguments and [Getting started](docs/GETTING_STARTED.md) for the full newcomer walkthrough.

## What works today

CORA's [capability atlas](.cora/assurance/capability-atlas.json) lists **71 declared CLI commands across eight method families**, with implementation and test-source witnesses. This is **not** a claim that 71 product behaviors have been independently executed or certified. The [parser-checked CLI reference](docs/CLI_REFERENCE.md), [capability DoD](.cora/contracts/dod/capability-dod.json), and [complete documentation index](docs/INDEX.md) distinguish available interfaces from qualified outcomes.

| Engineering task | Implemented mechanisms | Boundary of the result |
| --- | --- | --- |
| **Understand a repository** | Original-Git `snapshot`, ontology, partial Python import graph, manifest adapters, artifact-role classification | Candidate dependencies and ownership declarations; not exhaustive dynamic usage |
| **Investigate files and debt** | File Lab, archaeology, holistic forensics, debt signals, conservative selection | No universal safe-deletion proof or independently measured defect rate |
| **Constrain AI-assisted changes** | Intent-bound reticular DoD, contextual guards, negative controls, finite mutant models | Source obligations are not runtime certification or autonomous coding |
| **Review PRs and merges** | Exact `BASE`/`HEAD`, pre/post-merge checks, effect-capability analysis, evidence invalidation | Source receipts do not authenticate human approval, host enforcement, or deployment |
| **Audit CI/CD** | Workflow inventory, local caller/duplicate checks, conservative `BASE → HEAD` rationalization | External consumers and equivalent runtime behavior remain unverified; no automatic retirement |
| **Correlate assurance methods** | Ontology, source witnesses, Git replay, bounded hypotheses and convergence graphs | Correlation is not independent behavioral proof or causality |
| **Run separately authorized experiments** | Controlled document/file transformations, staged mutations, optional runtime/ZIP intake | Explicit opt-in, real oracles, and externally verified containment are required |

**Five convergent assurance goals:** Semantic Truth, AI Reasoning, Behavioral Proof, Continuous Semantic Evolution, and Unified Assurance. `method-synthesize --synergic` correlates their bounded source routes; `--integrated` joins documentation, **18 README claim traces**, and the **71 declared interfaces**. It does **not** invoke an AI provider by default or replace One-Run:

```sh
cora method-synthesize . --synergic --base-sha BASE_SHA \
  --execute-source-probes --output REPORT --ai-request-output AI_PLAN
```

Use [Convergent assurance](docs/CONVERGENT_ASSURANCE.md) to interpret the generated plan and its DoD. AI hypotheses remain untrusted until checked against original sources and independent observations.

**Historical and engineering-knowledge capabilities:** merged PR38 supplied an original-Git register of **37 PRs and 305 commit deltas**, including the **unmerged PR34** exception; **28 former paths** are classified as relocated or historical, not automatically removable. It supports PR/commit drill-down, historical path reconciliation, and future-change obligations. That frozen PR01–37 ledger does **not** cover every later PR. Merged PR40 added static/dynamic-boundary knowledge and debt checks: dynamic callsites are **not executed runtime coverage**, and its **10 million** finite scenario evaluations are **not 10 million distinct code mutations**. See the [historical register](.cora/assurance/history/pr01-37-commit-diff-audit.json), [history DoD](.cora/contracts/dod/history-convergence-dod.json), [engineering knowledge DoD](.cora/contracts/dod/engineering-knowledge-dod.json), and [engineering debt guide](docs/ENGINEERING_DEBT.md).

**Independent product qualification framework:** merged PR39 introduced four distinct gates—**behavior, usability, isolation, and effective governance**. The [native-Git reference](tools/independent_git_oracle.py) and [read-only host readback](tools/governance_readback.py) can test bounded properties, but cannot authenticate independent operators, demonstrate maintained-target performance, or approve release. See the [qualification DoD](.cora/contracts/dod/independent-qualification-dod.json).

## One-Run — one command, one evidence dossier

CORA's primary integrated assurance entry point is the **existing** `process-run --one-run --profile comprehensive`. It inventories known methods, parser/dispatch commands, tests, verifier tools, workflows, DoDs, and genealogy. On its default safe profile, **only eligible PR36 source-analysis methods actually run**; all other registered activities receive explicit `NOT_RUN` or `BLOCKED` reasons. A catalog of 71 commands is not an execution log of 71 commands.

```sh
cora process-run . --revision HEAD --process full --one-run --profile comprehensive \
  --output /tmp/cora-run.json --atlas-json /tmp/cora-run-machine.json \
  --atlas-html /tmp/cora-run.html --evidence-dir /tmp/cora-evidence

cora verify-process /tmp/cora-run.json --repo . --one-run \
  --atlas-json /tmp/cora-run-machine.json --atlas-html /tmp/cora-run.html \
  --evidence-dir /tmp/cora-evidence
```

**How to read the result:** open `/tmp/cora-run.html`; start with **Review in three questions** (conclusion, evidence, falsifier), then inspect which activities were **executed, reused, blocked, or not run**; trace a claimed outcome to its Git SHA, receipt and remaining DoD. The files have distinct purposes:

- `cora-run.json` — execution receipt and contextual outcome.
- `cora-run-machine.json` — machine-readable integrated Atlas.
- `cora-run.html` — browsable human/AI Atlas and drill-down.
- `cora-evidence/` — optional local content-addressed artifacts.

`verify-process` checks bounded JSON/HTML/Git replay; matching output does **not** imply external attestation. The smaller original One-Run view can be used without `--profile comprehensive`. CORA-only unit tests require opt-in with `--execute-self-tests`; the comprehensive authorization flow additionally uses `--authorization-file CONSENT.json` tied to the exact commit, tree, and checkout. This is not a hostile-code sandbox or permission to execute untrusted target tests.

References: [One-Run DoD](.cora/contracts/dod/one-run-dod.json), [55-node integrated DoD](.cora/contracts/dod/integrated-one-run-dod.json), [complete CLI syntax](docs/CLI_REFERENCE.md), and [Getting started](docs/GETTING_STARTED.md). The integrated DoD does not become externally accepted merely because its source checks pass.

## How CORA works

```text
Human engineering intent + exact Git BASE / HEAD
    ↓
Git inventory + declared product / software / ownership
    ↓
Reverse-derived DoD + bounded intended change + falsifiers
    ↓
Actual authorized tests, source outcomes, receipts and replay
    ↓
Outstanding runtime, user and governance obligations
    ↓
Independent reviewer / host authorization (outside CORA)
    ↓
Actual merged SHA + post-merge invalidation / reassessment
```

CORA distinguishes **provenance, inference, runtime observation, and authorization**. A hash can identify committed bytes; it cannot authenticate a human reviewer or demonstrate target behavior. A test source file is not evidence that its tests ran. Source replay is not truth, and a pass within a finite model is not a general product certificate.

## Use CORA with an AI coding assistant

Give your assistant an **authorized CORA checkout** and a **separate target repository**. A GitHub URL alone does not install CORA or enforce governance. For contextual source review, the target must include its **own committed** `cora.ontology.json` and `.cora/continuous-policy.json` in the `BASE` revision. Define the engineering intent and the acceptance oracle, then run:

```sh
cora convergence-plan --contract /path/to/cora/.cora/contracts/dod/convergence-dod.json

cora dev-premerge /path/to/target --base BASE_SHA --head PR_HEAD_SHA \
  --contextual --intent "Ship the bounded change with its acceptance tests" \
  --convergence-contract /path/to/cora/.cora/contracts/dod/convergence-dod.json \
  --output /tmp/cora-premerge.json

cora verify-contextual-gate /tmp/cora-premerge.json --repo /path/to/target \
  --intent "Ship the bounded change with its acceptance tests" \
  --convergence-contract /path/to/cora/.cora/contracts/dod/convergence-dod.json
```

**The same intent is required for replay**. Without the matching `--intent`, the contextual gate is `DEBT_BLOCKED`. These source checks do not implicitly execute tests from the target repository or prove that its runtime is correct. Run real tests and obtain independent review separately. Evaluate the **actual merged commit** again rather than reusing the PR-head receipt.

Follow [Agent adoption](docs/AGENT_ADOPTION.md), [Agent instructions](AGENTS.md), [Continuous development](docs/CONTINUOUS_DEVELOPMENT.md), and the [R1–R4 DoD](docs/DOD_PR20_CONVERGENCE.md).

## Interpret a CORA result

| Status | What it means | What it does **not** mean |
| --- | --- | --- |
| `PASS_SCOPED` / `EXECUTED_SCOPED` | A named bounded obligation passed or an eligible activity actually ran | Entire-product correctness or independent runtime validation |
| `REUSED_SCOPED` | A source-scoped, lineage-compatible receipt was reused | A new execution or universally portable evidence |
| `NOT_RUN` | An activity is inventoried but has not executed | PASS or failure |
| `BLOCKED` / `DEBT_BLOCKED` | Necessary context or proof is unavailable or inconsistent | A defect has necessarily occurred |
| `REFUTED` | A specific claim conflicts with an observed counterexample | All methods or other claims are invalid |
| `BLOCKED_EXTERNAL` | Independent target, host, reviewer, isolation, or user evidence is missing | Authorization to merge, deploy, delete, or publish |

**Example of interpretation (illustrative, not a generated CI receipt):** a report that inventories a target test as `NOT_RUN` has proved the **test was identified**, not that it passed. A matching Git replay can establish continuity of the reported source observation, not who approved it. Only independently obtained evidence can close the applicable external gate. The exact status vocabulary depends on the report schema.

## Final Experimental Baseline — merged PR41

PR41 formalizes a **conclusive experimental source baseline**, not a published or independently qualified final product. Its [30-node noncompensatory DoD](.cora/contracts/dod/final-experimental-dod.json) contains **15 SOURCE leaves, 7 EXTERNAL leaves, and 8 aggregate AND gates**. Three pillars organize the stop point:

1. **Git-to-document truth:** the current README, docs, CLI, artifact roles, and evidence claims must agree with committed Git. Expected measurements include **48/48 indexed Markdown files**, classification of all tracked files, **71/71 CLI entries**, zero known false current-state claims, and unmodified historical ADRs/audits.
2. **Actually observed bounded behavior:** the real CORA CLI is compared with a separately implemented native-Git oracle on **two controlled physical Git repositories**, including changed commits, stale references, and negative controls. This is independent **implementation**, not independent **operator validation** or a benchmark on two maintained external targets.
3. **Effective governance:** branch restrictions, required checks, distinct non-author review, runtime isolation, and release authorization must be demonstrated **on their actual hosts by authorized independent operators**. Workflow files and source contracts alone cannot enforce these conditions.

The PR41 source campaign includes **1,000,000 deterministic finite-model evaluations**, **four seeds**, **16 realistic fault families**, and **2,517 preregistered zero-to-fourway masks**; it requires zero model/reference disagreements and zero unsafe authorization promotions, with reproducible digest replay. These are not one million independent source mutations, target executions, or user sessions.

**External acceptance remains `BLOCKED_EXTERNAL`** until at least two independently maintained target repositories are tested against preregistered oracles; host isolation is independently witnessed; **at least eight unfamiliar users** attempt **three tasks each**, with **≥80% successful completion and zero critical evidence-status misinterpretations**; GitHub actually enforces required checks and an authenticated non-author reviewer approves; and a release manager verifies the final merged SHA against the tag, wheel, sdist, provenance, and rollback drill.

**Release distinction:** `1.0.0a4` is an alpha package identity. As observed on **7 November 2026**, the existing GitHub `v1.0.0a4` pre-release remained an **unpublished Draft with zero assets** and no verified `refs/tags/v1.0.0a4` ref. This is a dated observation, not a permanent claim about the host. A Draft targeting mutable `main` is not a verified frozen artifact. Any subsequent source change invalidates earlier SHA-bound freeze receipts. CORA cannot self-approve, merge, tag, publish, destructively clean up, or authorize release.

Before a public experimental pre-release, follow the [release operator protocol](docs/RELEASE.md), [experimental product DoD](docs/DOD_V1_EXPERIMENTAL.md), and [final experimental DoD](.cora/contracts/dod/final-experimental-dod.json). A source pass and a human release decision are different events.

## Documentation by goal

Choose a path according to the task; the [48-document index](docs/INDEX.md) is exhaustive. The routes below are entry points, not competing sources of truth.

- **First-time user:** [Getting started](docs/GETTING_STARTED.md) · [Architecture](docs/ARCHITECTURE.md)
- **Coding assistant or reviewer:** [Agent adoption](docs/AGENT_ADOPTION.md) · [Agent rules](AGENTS.md) · [Continuous development](docs/CONTINUOUS_DEVELOPMENT.md)
- **Forensic investigator:** [File Lab](docs/FILE_LAB.md) · [Holistic forensics](docs/HOLISTIC_FORENSICS.md) · [Engineering debt](docs/ENGINEERING_DEBT.md)
- **Product or release owner:** [Governance](GOVERNANCE.md) · [Security](SECURITY.md) · [Release](docs/RELEASE.md)
- **Full documentation, history and contracts:** [Documentation index](docs/INDEX.md) · [Documentation DoD](docs/DOCUMENTATION_DOD.md)

<details>
<summary>Product | purpose, users, and outcomes</summary>

**Why:** make engineering claims falsifiable without transforming source findings into release authority. **For:** newcomers, engineers, coding-agent operators, reviewers, and product owners. Read [Getting started](docs/GETTING_STARTED.md), [experimental product DoD](docs/DOD_V1_EXPERIMENTAL.md), and [Release](docs/RELEASE.md). Independent real-target pilots and usability validation remain external obligations.

</details>

<details>
<summary>Software | implementation, interfaces, and runtime</summary>

**Runtime:** one local `cora-audit` Python distribution and a single `cora` CLI, with the engine [`src/cora/`](src/cora/) and release-verification [tools/](tools/). See [Architecture](docs/ARCHITECTURE.md), [CLI reference](docs/CLI_REFERENCE.md), and [Artifact semantics](docs/ARTIFACT_SEMANTICS.md). Static dependency edges do not attest dynamic execution, and optional Docker does not independently certify isolation.

</details>

<details>
<summary>Repository | versioned sources, CI, and history</summary>

**Source of record:** original Git objects bound to an exact SHA, not merely a description or uncommitted working tree. Inspect [tests](tests/), [workflows](.github/workflows/), [ontology](cora.ontology.json), [artifact roles](cora.artifact-roles.json), [changelog](CHANGELOG.md), and [Documentation index](docs/INDEX.md). Historical ADRs and audits retain their original authority; moving or archiving them is not proof of safe deletion.

</details>

<details>
<summary>Governance | responsibilities and security</summary>

**Decision rights are external:** no source report, `PASS_SCOPED`, CODEOWNERS entry, or green CI workflow authenticates an independent approval. See [Governance](GOVERNANCE.md), [Security](SECURITY.md), [Contributing](CONTRIBUTING.md), [PR template](.github/PULL_REQUEST_TEMPLATE.md), and [MIT](LICENSE). Check host-enforced rules and review identities separately.

</details>

<details>
<summary>Evidence and DoD | claims, falsifiers, and evidence lineage</summary>

**Read in order:** [Continuous development](docs/CONTINUOUS_DEVELOPMENT.md), [Convergent assurance](docs/CONVERGENT_ASSURANCE.md), [Documentation DoD](docs/DOCUMENTATION_DOD.md), [claim–evidence profile S01–S18](.cora/assurance/documentation-proofs.json), and [Git source verifier](tools/verify_claim_evidence.py). For deep investigations consult [File Lab](docs/FILE_LAB.md), [Holistic forensics](docs/HOLISTIC_FORENSICS.md), and [Engineering debt](docs/ENGINEERING_DEBT.md); archived decisions are accessible from [Documentation index](docs/INDEX.md) but are not current approval.

</details>

## Operating boundaries

CORA's default offline-first source inspection is **not a hostile-code sandbox**. The default does not execute arbitrary target tests, make network calls, or invoke AI providers. Optional runtime/ZIP/Docker and user-provided verifiers require explicit consent, appropriate containment, and separate verification of isolation; **the existence of a sandbox configuration is not execution proof**. Static Python graphs cannot resolve every dynamic, external, or non-Python dependency. GitHub workflow files alone do not prove required checks, branch protection, or independent review. CORA does not automatically delete files, rewrite arbitrary code, retire workflows, merge PRs, or publish releases.

Security-sensitive changes and unfamiliar repositories require [Security](SECURITY.md), independent recovery/rollback planning, and accountable human approval.

## Engineering map

**Product:** `cora`, the assurance capability. **Software:** `cora-engine` (Python package `cora-audit`, CLI `cora`, implementation [`src/cora/`](src/cora/)) plus `cora-release-verification` ([`tools/`](tools/)). **Repository:** `Luke883i/cora`—versioned sources, [tests](tests/), [schemas](schemas/), [workflows](.github/workflows/), governance, current guidance, and historical ADRs/audits. These identities are not interchangeable with runtime events or release approval.

The root retains package/policy files and the two adoption-facing JSON contracts [`cora.ontology.json`](cora.ontology.json) and [`cora.artifact-roles.json`](cora.artifact-roles.json). Internal DoDs, profiles, assurance reports, and fixtures reside under [`.cora/contracts/`](.cora/contracts/index.json), [`.cora/assurance/`](.cora/assurance/capability-atlas.json), and [`.cora/fixtures/`](.cora/fixtures/). The [canonical contract routing index](.cora/contracts/index.json) maps logical identities to paths. A relocated file is not automatically obsolete, safely removable, or runtime-compatible. The historical record is navigable from [Documentation index](docs/INDEX.md).

**Contribute and report:** [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md) · [Security](SECURITY.md) · [License](LICENSE). Product usability and independent real-world acceptance remain unverified until their external witnesses are recorded.
