# CORA — Continuous Ontological Repository Assurance

**CORA (Continuous Ontological Repository Assurance)** — **Engineering evidence for AI-assisted software changes.**

CORA is an offline-first **Python 3.11+ command-line product** that helps developers and AI coding assistants inspect Git repositories, derive source-bound Definitions of Done, challenge claims with counterexamples and produce reproducible pre/post-merge review reports. The assistant writes code; CORA helps structure **what must be demonstrated** before someone can responsibly accept a change.

**Why it matters:** a successful code edit, a green test and a confident AI explanation are not the same as product correctness, operational readback or independent approval. CORA makes supported claims, evidence gaps and required next checks explicit. It is **not** a coding agent, general runtime-equivalence prover, universal dead-code detector, automatic code deleter or merge authority.

**Current status:** `v1.experimental` / Python package `1.0.0a4`, alpha **source candidate**, not a stable API or verified public release. See [release status](docs/RELEASE.md) and [product DoD](docs/DOD_V1_EXPERIMENTAL.md).

## How CORA works

```text
Human engineering intent + exact BASE / HEAD
    |
    v
Git source --> declared product/software --> candidate dependencies
    |
    v
Reverse-derived DoD --> smallest justified change --> falsifiers
    |
    v
Real tests / reports --> replay & invalidation --> unresolved evidence
    |
    v
Independent reviewer / host controls (outside CORA)
    |
    v
Actual merged SHA --> postmerge source/regression reassessment
```

CORA distinguishes **provenance**, **inference**, **runtime observation** and **authorization**. A hash can identify committed bytes; it cannot authenticate a human reviewer or demonstrate target behavior.

## First five minutes

From an authorized local checkout of CORA, with Python 3.11+ and Git:

```sh
python -m pip install -e .
cora --help
cora version
cora audit . --output /tmp/cora-worktree.json
cora snapshot . --revision HEAD --output /tmp/cora-ledger.json
cora verify-ledger /tmp/cora-ledger.json --repo .
```

Keep reports outside the source checkout; `/tmp` is a Unix example. `audit` reads the working tree, while `snapshot` reads a **pinned Git commit**; their evidence is not interchangeable. Explore the full [new-user tutorial](docs/GETTING_STARTED.md) and [CLI reference](docs/CLI_REFERENCE.md).

## What works today

| Engineering goal | Relevant CORA capabilities | Evidence boundary |
| --- | --- | --- |
| **Understand a repository** | Git snapshot, declared ontology, partial import graph, manifest adapters, artifact roles | Candidate dependencies and owner declarations, not complete runtime usage |
| **Investigate files and debt** | File Lab, source archaeology, holistic analysis, debt signals and selection triage | No universal safe-deletion certificate or measured defect rate |
| **Constrain an AI coding assistant** | Intent-to-proof DoD, finite falsifiers, contextual source assurance | Source model or synthetic scenarios never certify product behavior |
| **Review changes and follow merges** | BASE-pinned premerge and postmerge, dependency-based invalidation, effect-capability analysis | Report is not reviewer authentication, effective CI permissions or deployment evidence |
| **Run separately authorized experiments** | Controlled document rename, optional staged source mutations and runtime observation | Explicit authorization, independent oracles and external isolation checks remain necessary |

All current command names, scope details and parameters are in the [parser-checked CLI reference](docs/CLI_REFERENCE.md). For methods and domain-specific DoD, use the [complete documentation index](docs/INDEX.md).

## Use CORA with an AI coding assistant

Give your assistant an authorized checkout of CORA and a **separate target repository**; a GitHub link alone does not install or enforce anything. The target needs its **own** committed `cora.ontology.json` and a continuous policy `.cora/continuous-policy.json` present in the BASE revision for contextual review. Record a real engineering intent and acceptance oracle, then run:

```sh
cora convergence-plan --contract /path/to/cora/cora.convergence-dod.json
cora dev-premerge /path/to/target --base BASE_SHA --head PR_HEAD_SHA \
  --contextual --intent "Ship the bounded change with its acceptance tests" \
  --convergence-contract /path/to/cora/cora.convergence-dod.json \
  --output /tmp/cora-premerge.json
cora verify-contextual-gate /tmp/cora-premerge.json --repo /path/to/target \
  --intent "Ship the bounded change with its acceptance tests" \
  --convergence-contract /path/to/cora/cora.convergence-dod.json
```

The same intent is required for replay. Without it the contextual gate is **DEBT_BLOCKED**. These commands do **not** implicitly run the target tests or prove runtime correctness. Run real tests and obtain independent review separately. See [step-by-step agent adoption](docs/AGENT_ADOPTION.md), [current engineering method](docs/CONVERGENT_ASSURANCE.md) and the [R1–R4 DoD](docs/DOD_PR20_CONVERGENCE.md).

## Read a CORA result correctly

- **PASS_SCOPED:** the named bounded source obligation passed; not blanket product certification.
- **BLOCKED / DEBT_BLOCKED:** evidence is missing or cannot be reconciled; not proof of a defect.
- **REFUTED:** an observed counterexample rejects a particular claim.
- **BLOCKED_EXTERNAL:** required independent owner, host, reviewer, runtime or pilot evidence is not present.
- **Authorization:** source and replay reports do not confer merge, deployment, release or deletion permission.

The exact vocabulary depends on the report's schema. Ten-million-case campaigns are **finite synthetic model evaluations**, not ten million actual source mutants, users or runtime tests.

## Documentation by goal

- **First-time user:** [Getting started](docs/GETTING_STARTED.md) · [Architecture](docs/ARCHITECTURE.md)
- **Coding assistant or reviewer:** [Agent adoption](docs/AGENT_ADOPTION.md) · [Agent rules](AGENTS.md) · [Continuous development](docs/CONTINUOUS_DEVELOPMENT.md)
- **Forensic investigator:** [File Lab](docs/FILE_LAB.md) · [Holistic forensics](docs/HOLISTIC_FORENSICS.md) · [Engineering debt](docs/ENGINEERING_DEBT.md)
- **Product or release owner:** [Governance](GOVERNANCE.md) · [Security](SECURITY.md) · [Release](docs/RELEASE.md)
- **Full documentation, history and contracts:** [Documentation index](docs/INDEX.md) · [Documentation DoD](docs/DOCUMENTATION_DOD.md)

## Operating boundaries

CORA's first-party source analysis is not a hostile-code sandbox. Optional Docker execution and user-specified verifier commands require separate opt-in and must not be treated as independently attested isolation. The static Python graph is incomplete for dynamic, external and non-Python consumers. GitHub workflow files alone do not prove required checks, protected branches or independent approvals. No automatic code deletion or general code rewrite is supported. Read the [security policy](SECURITY.md) before running unfamiliar sources or transformations.

## Engineering map

**Product:** `cora` — the assurance capability. **Software:** `cora-engine` (`src/cora/`, Python distribution `cora-audit`, single CLI `cora`) plus `cora-release-verification` (`tools/`). **Repository:** `Luke883i/cora` — source, tests, schemas, policies, CI and historical ADRs. These are different entities; a role declaration is not execution evidence. See the [committed ontology](cora.ontology.json), [artifact role registry](cora.artifact-roles.json) and [architecture](docs/ARCHITECTURE.md).

Contribute through [CONTRIBUTING](CONTRIBUTING.md); use the [changelog](CHANGELOG.md) to distinguish merged source from publication. [License](LICENSE) · [Security reporting](SECURITY.md). An unfamiliar engineer's first-read test and real external product pilots remain open acceptance obligations.
