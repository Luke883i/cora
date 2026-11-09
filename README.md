# CORA — Continuous Ontological Repository Assurance

**CORA (Continuous Ontological Repository Assurance)** — **Engineering evidence for AI-assisted software changes.**

CORA is a local, offline-first Python 3.11+ framework. It helps developers and AI coding assistants inspect a Git repository, turn goals into falsifiable obligations and **produce reproducible pre/post-merge review reports**. It links **the proposed change**, **the source evidence**, **tests or counterexamples** and **the work still needed**. Agents edit with authorized tools; CORA evaluates evidence. CORA is **not a coding agent** or an approver.

**Why it matters:** a plausible AI-generated patch is not evidence that the product works. CORA makes *intent, modification, observation and uncertainty* separately inspectable. For a CTO this means reviewable decisions; for a developer, a reproducible next test; for a reviewer, explicit counterexamples and unresolved risk.

```text
Intent → acceptance graph → reversible code slice → adversarial tests
             ↑                          ↓
       open obligations ← exact Git SHA + evidence dossier
```

**Product** = the engineering-assurance experience; **software** = the `cora` Python CLI and verifiers; **repository** = their Git source, contracts, tests, docs and CI. None by itself demonstrates target-product readiness.

**Recommended use:** inspect an authorized checkout or review one bounded change. **Audience and conditions:** CTOs, developers, reviewers and coding agents; Python 3.11+, Git and authorized execution tools. **Open source license:** [MIT](LICENSE).

**Current status:** experimental `cora-audit 1.0.0a5`, **not a stable API or verified public release**. **merged PR41** and PR46 establish source milestones; the earlier `v1.0.0a4` was a draft. Independent user/host qualification is open.

## First five minutes — Quickstart

On an authorized local checkout of CORA:

```sh
python -m pip install -e .
cora --help
cora snapshot . --revision HEAD --output /tmp/cora-ledger.json
cora verify-ledger /tmp/cora-ledger.json --repo .
```

Then run [One-Run](#one-run--one-command-one-evidence-dossier). This identifies source and replayable assertions; it does not test an arbitrary external product. [Getting started](docs/GETTING_STARTED.md) explains setup, bounded output and failure handling.

## What works today

**71 declared CLI commands** in the [capability atlas](.cora/assurance/capability-atlas.json): a source inventory, **not 71 independently validated product behaviors**. Implemented surfaces include Git/file archaeology, partial static dependencies, typed DoD graphs, bounded debt, modeled fault tests, pre/post-merge reports and portable ChatGPT iteration ZIPs. The [parser-checked CLI reference](docs/CLI_REFERENCE.md) and [complete documentation index](docs/INDEX.md) document source surfaces, not runtime certificates.

**CORA is not an eleventh engineering method.** It correlates partial observations; no listed method is implemented in full:

| Lens | What it contributes | What CORA does *not* infer |
| --- | --- | --- |
| C4/arc42, DDD | Architectural boundaries and accountable owners | A complete architecture or true runtime ownership |
| Static dependencies, typed graphs, lineage, Git archaeology | Candidate consumers, paths, changes and provenance | Every dynamic consumer, SCC/centrality analysis or runtime causality |
| Contracts, mutation/metamorphic tests, threat modeling, fitness functions | Invariants, negative cases and change risks | Formal correctness, full security coverage or globally minimal design |

The [method crosswalk](docs/CONVERGENT_ASSURANCE.md#method-crosswalk--borrowed-perspectives-not-full-implementations) distinguishes implemented source observations, analogies and external evidence.

## One-Run — one command, one evidence dossier

```sh
cora process-run . --revision HEAD --process full --one-run --profile comprehensive \
  --output /tmp/cora-run.json --atlas-html /tmp/cora-run.html
cora verify-process /tmp/cora-run.json --repo . --one-run --atlas-html /tmp/cora-run.html
```

The dossier separates `PASS_SCOPED`, `NOT_RUN`, `REFUTED` and `BLOCKED_EXTERNAL`. **The default does not execute arbitrary target tests**. Run permitted target tests separately and keep commands, versions and observed outcomes. [Portable chat handoff](docs/AGENT_ADOPTION.md#portable-chatgpt-handoff-opt-in) uses `--chat-step` and `--chat-bundle`; its ZIP is neither automatic ChatGPT memory nor an approval.

## How CORA works

**1. Specify the outcome.** Turn natural-language intent into actors, boundaries and an **AND-dependency graph** of acceptance conditions. Work **backward** from each required observation: an unknown prerequisite remains open, never averaged away. [Worked application contract](docs/CONTINUOUS_DEVELOPMENT.md#example-contract-and-evidence-ladder--portable-corrective-action-app).

**2. Change one coherent unit.** An agent uses authorized tools to edit code and tests; CORA checks source evidence. Git records **content-addressed blobs**, **directory trees**, commits and a PR; CORA checks their lineage. **New source SHA** means revalidate. A hash can identify committed bytes; it cannot authenticate a human reviewer.

**3. Try to disprove it, then stop intelligently.** Challenge obligations with **seeded combinations** and a **separate expected-result rule**; use **physical mutation testing** on isolated real source only when authorized. Separate killed, **surviving and inconclusive** mutants. A **fixed scenario catalog and final window** with no new failure signatures establishes **bounded convergence**, **not proof of complete correctness**. After repeated **no-progress rounds**, continuation proposes replanning; it **does not predict N** or execute a next step.

**Example — delete a module?** Imports and Git history locate candidate consumers; negative tests and owners expose obligations. An unknown dynamic caller means `BLOCKED`, not safe deletion.

**Two concrete engineering histories (methods at different maturity levels, not proof that CORA CLI created these products):**

- **[ICTC](https://github.com/Luke883i/ictc) — UI/UX as observable meaning.** An authorized browser/container agent can capture screenshots across roles/viewports and compare *what the UI promises* with actual controls. The Playwright [Browser witness](https://github.com/Luke883i/ictc/blob/e641526114a508e24f86e8554c027d8cd6bbe715/v3/browser-onto-compliance-v1.py) captures screenshots; the [visual audit](https://github.com/Luke883i/ictc/blob/e641526114a508e24f86e8554c027d8cd6bbe715/v3/s4-a6-ux4-uiux-mount-audit.md) records **screenshot-derived** faults: misleading write affordances, technical-first hierarchy and hidden work. The [reconciliation contract](https://github.com/Luke883i/ictc/blob/e641526114a508e24f86e8554c027d8cd6bbe715/v3/uiux-656-absorption-contract.json) maps **656 recorded visual/UX findings to 12 root causes**; separate [physical product mutants](https://github.com/Luke883i/ictc/blob/e641526114a508e24f86e8554c027d8cd6bbe715/v3/release-readiness-e2-product-mutants.mjs) edit real source and run an E2 gate. **No fresh ChatGPT-container run or independent user study is attested here.**
- **[iKant_EDU](https://github.com/Luke883i/iKant_EDU) — experimental computational cognitive architecture.** A replaceable LLM accompanies bounded appraisal, recurrent workspace, **functional attention** and a **self/world state model**: **computational constructs**, **not a claim of a conscious biological mind**. Git archaeology retained `UNKNOWN` consumers, recovered **11 unqualified file deletions**, and [PR238](https://github.com/Luke883i/iKant_EDU/pull/238) restored a protected workflow. **Millions of finite fault vectors** challenge declared models, **not millions of real Git mutations** or host sessions. [Cognitive model](https://github.com/Luke883i/iKant_EDU/blob/73842c1d71ea1b1faa3903b255d00cd09b1b6cb6/docs/IKANT_COGNITIVE_SUBSTRATE.md) · [CORA method backlog](https://github.com/Luke883i/iKant_EDU/blob/73842c1d71ea1b1faa3903b255d00cd09b1b6cb6/docs/CORA_PR_A_BACKLOG.md).

**Terminology, only after the engineering method:** CORA calls the extraction *intent mining*, the backward graph a *reticular DoD*, coherent changes *semantic slices*, Git-object writing *blobbing/materialization*, modeled counterexamples *semantic mutations* and the bounded novelty plateau *semantic saturation*. The conventional engineering definitions and limits above govern these labels.

## Use CORA with an AI coding assistant

Follow [agent adoption](docs/AGENT_ADOPTION.md) and the [R1–R4 DoD](docs/DOD_PR20_CONVERGENCE.md). Premerge uses `--contextual --intent`; **The same intent is required for replay**. CORA **does not independently write a feature**: authorize bounded agent work. **Run real tests and obtain independent review separately.** The [LEVEL / NILO experiment](docs/CONTINUOUS_DEVELOPMENT.md#level-demonstration-local-evidence-verifiable-engineering-lifecycle) proposes a playable slice requiring genuine browser tests; it is not an already delivered game.

## Interpret a CORA result

A Git SHA identifies source bytes, not runtime or human approval. **A source digest does not authenticate a human reviewer**. Finite-model PASS is not target behavior; `NOT_RUN` and `BLOCKED_EXTERNAL` are not PASS. See [evidence boundaries](docs/CONVERGENT_ASSURANCE.md).

## Final Experimental Baseline — merged PR41

The [final experimental DoD](.cora/contracts/dod/final-experimental-dod.json) distinguishes **15 SOURCE leaves, 7 EXTERNAL leaves, and 8 aggregate AND gates**. Its **16 realistic fault families** and **2,517 preregistered zero-to-fourway masks** are finite-model cases, **not one million independent source mutations**. **two controlled physical Git repositories** supply bounded counterexamples, not independent target or user acceptance.

## Documentation by goal

**First-time user:** [Getting started](docs/GETTING_STARTED.md) · [Architecture](docs/ARCHITECTURE.md).
**Coding assistant or reviewer:** [Agent adoption](docs/AGENT_ADOPTION.md) · [AGENTS](AGENTS.md) · [Continuous development](docs/CONTINUOUS_DEVELOPMENT.md).
**Forensic investigator:** [File Lab](docs/FILE_LAB.md) · [Holistic forensics](docs/HOLISTIC_FORENSICS.md) · [Engineering debt](docs/ENGINEERING_DEBT.md).
**Product or release owner:** [Governance](GOVERNANCE.md) · [Security](SECURITY.md) · [Release](docs/RELEASE.md).
**Full documentation, history and contracts:** [Index](docs/INDEX.md) · [Documentation DoD](docs/DOCUMENTATION_DOD.md).

**Decision rights are external:** only authorized humans and trustworthy host controls can approve or release. **Source of record:** the committed Git revision, not a chat. **Why:** model tests cannot certify external behavior. **Runtime:** local Python CLI by default. **Read in order:** README → one task guide → applicable contract → exact source evidence.

<details>
<summary>Product | Outcome and limits</summary>

[Getting started](docs/GETTING_STARTED.md) · [Evidence limits](docs/DOD_V1_EXPERIMENTAL.md) · [Release](docs/RELEASE.md).
</details>
<details>
<summary>Software | Code and API</summary>

[Engine `src/cora/`](src/cora/) · [tools](tools/) · [Architecture](docs/ARCHITECTURE.md) · [CLI](docs/CLI_REFERENCE.md).
</details>
<details>
<summary>Repository | Git and tests</summary>

[Tests](tests/) · [CI](.github/workflows/) · [Ontology](cora.ontology.json) · [Index](docs/INDEX.md) · [History](CHANGELOG.md).
</details>
<details>
<summary>Governance | People and permissions</summary>

[Governance](GOVERNANCE.md) · [Security](SECURITY.md) · [Contributing](CONTRIBUTING.md) · [PR template](.github/PULL_REQUEST_TEMPLATE.md) · [MIT](LICENSE).
</details>
<details>
<summary>Evidence and DoD | Reproduce the claim</summary>

[Continuous development](docs/CONTINUOUS_DEVELOPMENT.md) · [Convergent assurance](docs/CONVERGENT_ASSURANCE.md) · [Documentation DoD](docs/DOCUMENTATION_DOD.md) · [Claim register](.cora/assurance/documentation-proofs.json) · [Verifier](tools/verify_claim_evidence.py).
</details>

## Operating boundaries

**External acceptance remains `BLOCKED_EXTERNAL`** without independent target, reviewer and host evidence. **GitHub workflow files alone do not prove** enforced rules. Absent imports do not prove `safe_deletion`; source CI does not authorize release.

## Engineering map

**Product:** reviewable assurance. **Software:** `cora-engine` CLI and `cora-release-verification` checks. **Repository:** source, contracts, tests, CI and **historical ADRs**. **merged PR38** and **merged PR39** established bounded history/qualification milestones; follow the [complete index](docs/INDEX.md) for owners.
