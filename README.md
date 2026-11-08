# CORA — Continuous Ontological Repository Assurance

**CORA (Continuous Ontological Repository Assurance)** — **Engineering evidence for AI-assisted software changes.**

CORA is a local, offline-first Python 3.11+ engineering-assurance framework. It helps developers and AI coding assistants inspect a Git repository, translate a product intention into testable obligations, challenge software changes and **produce reproducible pre/post-merge review reports**. It connects **the proposed change**, **the source evidence**, **tests or counterexamples** and **the work still needed**. A coding agent can implement the change with authorized tools; CORA governs its evidence. CORA is **not a coding agent** or an automatic reviewer.

**Why it matters:** AI can generate changes faster than a team can explain, verify and maintain them. CORA makes the difference between *what was requested*, *what was changed*, *what was observed* and *what remains unknown* reviewable by another engineer.

```text
Intent → acceptance graph → reversible code slice → adversarial tests
             ↑                          ↓
       open obligations ← exact Git SHA + evidence dossier
```

**Product** = the engineering-assurance experience; **software** = the `cora` Python CLI and verifiers; **repository** = their Git source, contracts, tests, docs and CI. None by itself demonstrates target-product readiness.

**Recommended use:** start with a real requirement and an authorized checkout; review an existing change or guide an agent through bounded slices. **Audience and conditions:** developers, CTOs, reviewers and coding agents; Python 3.11+, Git and independently authorized execution tools. **Open source license:** [MIT](LICENSE).

**Current status:** experimental source `cora-audit 1.0.0a5`, **not a stable API or verified public release**; **merged PR41** and PR46 are source milestones. The prior GitHub `v1.0.0a4` release was a draft, not proof of published assets. External user and host qualification remains open.

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

**71 declared CLI commands** in the [capability atlas](.cora/assurance/capability-atlas.json): a source inventory, **not a claim that 71 product behaviors have been independently executed or certified**. Capabilities include Git/file archaeology, static dependencies, bounded engineering debt, acceptance-graph evaluation, model-based fault tests, pre/post-merge checks and a portable ChatGPT iteration ZIP. Find the [parser-checked CLI reference](docs/CLI_REFERENCE.md) and [complete documentation index](docs/INDEX.md); they are not independent runtime witnesses.

## One-Run — one command, one evidence dossier

```sh
cora process-run . --revision HEAD --process full --one-run --profile comprehensive \
  --output /tmp/cora-run.json --atlas-html /tmp/cora-run.html
cora verify-process /tmp/cora-run.json --repo . --one-run --atlas-html /tmp/cora-run.html
```

The dossier separates `PASS_SCOPED`, `NOT_RUN`, `REFUTED` and `BLOCKED_EXTERNAL`. **The default does not execute arbitrary target tests**. A coding agent must execute permitted target tests separately and attach authentic commands, versions and observations. For chat continuity, [portable session instructions](docs/AGENT_ADOPTION.md#portable-chatgpt-handoff-opt-in) cover `--chat-step` and `--chat-bundle`; the ZIP is logically append-only, not automatic ChatGPT memory or approval.

## How CORA works

**1. Specify the outcome.** Turn natural-language intent into actors, boundaries, expected behavior, affected owners and an **AND-dependency graph** of acceptance conditions. Derive tests *backward*: what must be observable for each condition to count as met? An unknown prerequisite is an open obligation, not a percentage of completion. [Contract-to-product example](docs/CONTINUOUS_DEVELOPMENT.md#level-contract-to-product-development-with-bounded-continuation-pr47-candidate).

**2. Change one coherent unit.** The agent uses its authorized tools to create or modify source, tests, assets and workflow files; Git records content-addressed blobs, directory trees, commits and a proposed PR. CORA evaluates their structure and source lineage. New source SHA means **revalidate**; a new contract means **reassess**. Do not add an owner or CI workflow if the existing owner can perform the task.

**3. Try to disprove it, then stop intelligently.** Generate *seeded combinations* of relevant fault conditions; compare outcomes against a **separate expected-result rule**; change real source in an isolated checkout when physical mutation testing is authorized. Count detected, surviving and inconclusive mutations separately. Group new failure signatures and inspect a **fixed scenario catalog and final window**: no new signatures is **bounded convergence**, not proof of complete correctness. The portable round report suggests a next obligation or replanning after repeated no-progress rounds; it does not predict N or execute the next step.

**Two concrete engineering histories (methods at different maturity levels, not proof that CORA CLI created these products):**

- **<a href="https://github.com/Luke883i/ictc">ICTC</a> — visual meaning and decision-oriented UX.** A browser test covers procedure surfaces across *roles and viewport sizes*; separate screenshot-derived audits detect semantic UI failures such as an apparent write action for a read-only role, technical evidence overshadowing the user's next decision and hidden work. A source contract maps **656 recorded visual/UX findings to 12 root causes** and existing UI owners. A deterministic campaign challenges defined UI failure families; [physical product mutants](https://github.com/Luke883i/ictc/blob/e641526114a508e24f86e8554c027d8cd6bbe715/v3/release-readiness-e2-product-mutants.mjs) instead edit actual source and run an E2 gate. The screenshot-derived claims originate in recorded project audits, not a fresh human usability study. [Browser witness](https://github.com/Luke883i/ictc/blob/e641526114a508e24f86e8554c027d8cd6bbe715/v3/browser-onto-compliance-v1.py) · [visual audit](https://github.com/Luke883i/ictc/blob/e641526114a508e24f86e8554c027d8cd6bbe715/v3/s4-a6-ux4-uiux-mount-audit.md) · [reconciliation contract](https://github.com/Luke883i/ictc/blob/e641526114a508e24f86e8554c027d8cd6bbe715/v3/uiux-656-absorption-contract.json).
- **<a href="https://github.com/Luke883i/iKant_EDU">iKant_EDU</a> — experimental computational cognitive architecture.** Node/Host software around a replaceable LLM uses bounded appraisal, recurrent workspace, functional attention and a self/world state model; these are **computational constructs**, not a claim of a conscious biological mind. Source archaeology preserves unresolved dynamic consumers as `UNKNOWN`; 11 unqualified file deletions were restored before further qualification. In [PR238](https://github.com/Luke883i/iKant_EDU/pull/238), a protected workflow was restored byte-for-byte and Git readback moved to an existing CLI owner. Millions of finite fault vectors test *declared models*, not millions of real Git mutations or host sessions. [Cognitive model and limits](https://github.com/Luke883i/iKant_EDU/blob/73842c1d71ea1b1faa3903b255d00cd09b1b6cb6/docs/IKANT_COGNITIVE_SUBSTRATE.md) · [CORA method backlog](https://github.com/Luke883i/iKant_EDU/blob/73842c1d71ea1b1faa3903b255d00cd09b1b6cb6/docs/CORA_PR_A_BACKLOG.md).

**Terminology, only after the engineering method:** CORA calls the extraction *intent mining*, the backward graph a *reticular DoD*, coherent changes *semantic slices*, Git-object writing *blobbing/materialization*, modeled counterexamples *semantic mutations* and the bounded novelty plateau *semantic saturation*. The conventional engineering definitions and limits above govern these labels.

## Use CORA with an AI coding assistant

Start from [agent adoption](docs/AGENT_ADOPTION.md) and the [R1–R4 DoD](docs/DOD_PR20_CONVERGENCE.md). The existing premerge command accepts `--contextual --intent`; **The same intent is required for replay**. Authorize the assistant's next scoped stage; CORA can report an unresolved node or stagnation but **does not independently write a feature**. **Run real tests and obtain independent review separately.** The [LEVEL / NILO experiment](docs/CONTINUOUS_DEVELOPMENT.md#level-demonstration-local-evidence-verifiable-engineering-lifecycle) proposes a playable platform game whose first vertical slice must pass genuine browser tests; it is not an already delivered game.

## Interpret a CORA result

A Git SHA identifies source bytes, not the runtime, the CI host or a person's approval. **A hash can identify committed bytes; it cannot authenticate a human reviewer**. A positive result in a finite oracle is not proof of downstream behavior. `NOT_RUN` and `BLOCKED_EXTERNAL` are not PASS. [Evidence boundaries](docs/CONVERGENT_ASSURANCE.md) explain why proof context, scope and provenance matter more than a large green number.

## Final Experimental Baseline — merged PR41

The [final experimental DoD](.cora/contracts/dod/final-experimental-dod.json) declares **15 SOURCE leaves, 7 EXTERNAL leaves, and 8 aggregate AND gates**. Its **16 realistic fault families** and **2,517 preregistered zero-to-fourway masks** are finite-model cases, **not one million independent source mutations**. **Two controlled physical Git repositories** were used for bounded source counterexamples. These results cannot replace external users, maintained targets, host isolation or independent governance.

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

**External acceptance remains `BLOCKED_EXTERNAL`** until an independent target, human reviewer and governed host are observed. **GitHub workflow files alone do not prove** protected rules or independent reviewer identity. CORA cannot infer `safe_deletion` from absent imports; dynamic and external consumers require evidence. Do not treat a source-scoped CI result as release authorization.

## Engineering map

**Product:** explainable assurance and evidence-guided development. **Software:** `cora-engine` (CLI) and `cora-release-verification` (source/build checks). **Repository:** Git, machine contracts, tests, CI, documentation and **historical ADRs**. The **merged PR38** established historical source genealogy; **merged PR39** added source-level qualification gates. Use [the complete index](docs/INDEX.md) for precise ownership, not an invented second registry.
