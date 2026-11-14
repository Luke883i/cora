[![ROA Research Programme](https://img.shields.io/badge/ROA-Research_Programme-1f6feb)](https://github.com/Luke883i/academics)

<!-- programme-header:v2 -->
> **ROA Research Programme · AOSP ecosystem** — [Author & programme hub](https://github.com/Luke883i/academics) · [ROA theory](https://github.com/Luke883i/ROA) · [CORA assurance](https://github.com/Luke883i/cora). Every repository is independently readable. Membership does not imply formal derivation, shared runtime, scientific validation, certification, or production readiness. Repository-local code, evidence, and governance remain authoritative.

# CORA — Continuous Ontological Repository Assurance

**CORA (Continuous Ontological Repository Assurance)** — **Engineering evidence for AI-assisted software changes.**

CORA is a local, offline-first Python 3.11+ framework. It helps developers and AI coding assistants inspect a Git repository and **produce reproducible pre/post-merge review reports**. It connects **the proposed change**, **the source evidence**, **tests or counterexamples** and **the work still needed**. Authorized agents edit; CORA evaluates evidence. It is **not a coding agent** or an approver.

**Why it matters:** plausible patches are not proof. Readers need decisions, next tests and visible unresolved risks.

```text
Intent → acceptance graph → reversible code slice → adversarial tests
             ↑                          ↓
       open obligations ← exact Git SHA + evidence dossier
```

**Product** = engineering assurance; **software** = the `cora` CLI and verifiers; **repository** = Git source, contracts and CI. None proves target-product readiness.

**Recommended use:** inspect an authorized checkout or review one bounded change. **Audience and conditions:** CTOs, developers, reviewers and coding agents; Python 3.11+, Git and authorized execution tools. **Open source license:** [MIT](LICENSE).

**Current status:** experimental `cora-audit 1.0.0a5`, **not a stable API or verified public release**. **Document status:** CURRENT. **Current scope:** Git source review. **Operational use:** inspect commits. **Evidence:** Git and scoped tests. **Limits:** `BLOCKED_EXTERNAL`. Verify the exact checked-out Git revision rather than relying on an earlier prerelease candidate or a README version string. **Category:** agent-agnostic engineering assurance.

## First five minutes — Quickstart

On an authorized local checkout of CORA:

```sh
python -m pip install -e .
cora --help
cora snapshot . --revision HEAD --output /tmp/cora-ledger.json
cora verify-ledger /tmp/cora-ledger.json --repo .
```

For a scoped dossier, run [One-Run](#one-run--one-command-one-evidence-dossier). The snapshot is Git-only; neither command tests target runtime. [Getting started](docs/GETTING_STARTED.md) covers setup.

**ChatGPT Project:** see the complete, first-time setup below; the [canonical beta prompt](docs/AGENT_ADOPTION.md#chatgpt-project-beta-adapter) is optional and does not execute software.

## Use CORA in a ChatGPT Project — beginner walkthrough

**Choose this route if you want ChatGPT to help improve your own software.** The beta guide recommends **ChatGPT Plus or Edu**; Projects are available on other plans too, and specific tools depend on plan and workspace. No ChatGPT subscription is needed to run the standalone Python CLI.

1. **Create a Project:** in ChatGPT choose **New project**, name it for your work and open its **Project settings**. Copy the [single canonical CORA beta prompt](docs/AGENT_ADOPTION.md#chatgpt-project-beta-adapter) into **Project instructions**.
2. **Connect GitHub:** in Settings → Apps/Plugins authorize **read access** to [CORA](https://github.com/Luke883i/cora) and your **target repository** (your own or one you may work on). Confirm both repositories are available in this chat. GitHub connector abilities vary: **read-only** access is **not permission to push or merge**, and write actions require verified permissions and explicit authorization.
3. **Request a bounded change:** for example, “Read my target README and implementation; propose the smallest reversible fix for its broken login, with tests and a PR.” State product outcome and test oracle. CORA-METHOD can guide the discussion **without** executing CORA-ENGINE.
4. **Authorize execution separately:** use an available **write-capable coding tool**, such as Codex, or an authorized GitHub write action, with explicit permission **on your target** to create blobs, commits and a PR. A separate Python runner is needed for actual CORA-ENGINE receipts and native target tests. If unavailable, report `METHOD_ONLY` / `NOT_RUN`, never invented execution or a fictional PR.
5. **Keep evidence and continue:** after an actual `process-run`, optionally provide a `--chat-step` file and `--chat-bundle` ZIP. The [handoff guide](docs/GETTING_STARTED.md#in-a-chatgpt-session-the-shortest-reproducible-path) explains how to replay numbered `iterations/000001/handoff.md` records. The temporary ZIP is neither automatic chat capture nor authenticated review.

**Practical result:** proposed changes, commits and evidence dossiers are distinct; humans and host controls approve.

## What works today

**CTO evaluation snapshot — source-scoped, not an enterprise-readiness certificate**

| Decision question | Current answer |
| --- | --- |
| **Who / what?** | CTOs, developers, reviewers and AI coding-agent operators assess one bounded software change, its falsifiable DoD and unresolved obligations. |
| **Method / engine** | **CORA-METHOD** guides third-party agents; **CORA-ENGINE** is the local Python CLI. The agent edits; CORA checks evidence, not approval. |
| **Targets / runtime** | Git-bound source inspection, partial Python AST and static JavaScript ESM; native pilots **Teddy Node** and **ICTC HTTP/SQLite**. Browser/remote unobserved. |
| **Delivery / compatibility** | **MIT**, **Python 3.11+**, `cora-audit 1.0.0a5`, no declared mandatory Python runtime dependencies. Wheel/sdist candidates; no supported public release. |
| **Supply chain** | **SBOM (CycloneDX 1.6): GENERATION_IN_CANDIDATE_CI**; **SCA/CVE: SCAN_CI_BUILD_TOOLS_ONLY**; **artifact signing / SLSA provenance: NOT_ATTESTED**. |
| **Governance** | Execution needs authorization and isolation. **Independent reviewer, enforced branch rules, release: BLOCKED_EXTERNAL**; no production security SLA. [Security](SECURITY.md) · [Release](docs/RELEASE.md). |

**Assurance levels:** **L1** = Git/source checks; **L2** = bounded product experiments; **L3** = optional external assurance. L1/L2 may be useful without L3. CI PASS cannot approve a release.

**71 declared CLI commands** in [capability atlas](.cora/assurance/capability-atlas.json) are inventory, not 71 independently proven features. [parser-checked CLI reference](docs/CLI_REFERENCE.md) · [complete documentation index](docs/INDEX.md).

**CORA is not an eleventh engineering method.** Architecture models, source graphs, Git lineage, contracts and mutation tests offer partial perspectives—not complete runtime causality, formal correctness or security proof. The [method crosswalk](docs/CONVERGENT_ASSURANCE.md#method-crosswalk--borrowed-perspectives-not-full-implementations) separates implemented evidence and analogies.

## One-Run — one command, one evidence dossier

```sh
cora process-run . --revision HEAD --process full --one-run --profile comprehensive \
  --output /tmp/cora-run.json --atlas-html /tmp/cora-run.html
cora verify-process /tmp/cora-run.json --repo . --one-run --atlas-html /tmp/cora-run.html
```

The dossier distinguishes `PASS_SCOPED`, `NOT_RUN`, `REFUTED` and `BLOCKED_EXTERNAL`. **The default does not execute arbitrary target tests**. Keep native test receipts separate. [Chat handoff](docs/AGENT_ADOPTION.md#portable-chatgpt-handoff-opt-in) uses `--chat-step` / `--chat-bundle`: a temporary, operator-produced ZIP of numbered steps, evidence gaps and handoffs, **not** automatic chat memory, a signature or approval.

**Change range:** `--change-base BASE_SHA` compares an explicit base against HEAD; without it, the default covers one commit. Neither mode authenticates PR metadata or rewrites code.

**Native Gold pilots:** Teddy Node and ICTC HTTP/SQLite have bounded consented tests; LUMEN browser and NILO remote remain unobserved. Local PASS is not an authenticated runner or productivity claim. [Pilot evidence and linkage](docs/GOLD_ASSURANCE.md).

**Other Git repos:** `--one-run --portable-profile /path/to/target.json` enables source replay, not transplanted DoD. `--portable-parse-js` parses static ESM without execution. [Cross-repository limits](docs/CONTINUOUS_DEVELOPMENT.md).

**H-FORGE:** [Safe source stage](docs/HOLISTIC_FORENSICS.md#h-forge-optional-experimental-profile) joins comprehensive One-Run; native 77-case replay, effects, dynamic consumers and P5 acceptance remain separately unverified.

## How CORA works

**1. Specify the outcome.** Turn natural-language intent into an **AND-dependency graph** of observable conditions. Reason **backward**: an unknown prerequisite stays open. [Worked application contract](docs/CONTINUOUS_DEVELOPMENT.md#example-contract-and-evidence-ladder--portable-corrective-action-app).

**2. Change one coherent unit.** The agent uses authorized tools; CORA inspects committed evidence. Git preserves **content-addressed blobs**, **directory trees**, commits and PR lineage. **New source SHA** means revalidate. A hash can identify committed bytes; it cannot authenticate a human reviewer.

**3. Try to disprove it, then stop intelligently.** Use **seeded combinations**, a **separate expected-result rule** and authorized **physical mutation testing**. Keep killed, **surviving and inconclusive** mutants distinct. A **fixed scenario catalog and final window** can establish **bounded convergence**, **not proof of complete correctness**. After **no-progress rounds**, replan; CORA **does not predict N**.

**Delete a module?** Candidate consumers and negative tests inform review; an unknown dynamic caller means `BLOCKED`, not safe deletion.

**Target examples, not universal validation:** [ICTC](https://github.com/Luke883i/ictc) exercises HTTP/SQLite and source/UX verification; [Teddy](https://github.com/Luke883i/teddy) exercises Node; [iKant_EDU](https://github.com/Luke883i/iKant_EDU) illustrates unknown consumers and reversible repository contraction. Source histories and native pilot evidence have distinct owners; CORA did not independently certify these products. [Pilot scopes](docs/GOLD_ASSURANCE.md).

**Terminology, only after the engineering method:** *intent mining* = extracting obligations; *reticular DoD* = dependencies; *semantic slices* = bounded changes; *blobbing/materialization* = writing Git objects; *semantic mutations* = falsifiers; *semantic saturation* = bounded absence of new findings. Specifically, blobs hold bytes; trees and commits record revisions. Saturation covers finite scenarios, never universal correctness.

## Use CORA with an AI coding assistant

Follow [agent adoption](docs/AGENT_ADOPTION.md) and the [R1–R4 DoD](docs/DOD_PR20_CONVERGENCE.md). Premerge uses `--contextual --intent`; **The same intent is required for replay**. CORA **does not independently write a feature**: authorize bounded agent work. **Run real tests and obtain independent review separately.** The [LEVEL / NILO experiment](docs/CONTINUOUS_DEVELOPMENT.md#level-demonstration-local-evidence-verifiable-engineering-lifecycle) proposes a playable slice requiring genuine browser tests; it is not an already delivered game.

## Interpret a CORA result

**A source digest does not authenticate a human reviewer** or target runtime. `NOT_RUN` and `BLOCKED_EXTERNAL` are not PASS. See [evidence boundaries](docs/CONVERGENT_ASSURANCE.md).

## Final Experimental Baseline — bounded evidence

The [final experimental DoD](.cora/contracts/dod/final-experimental-dod.json) distinguishes **15 SOURCE leaves, 7 EXTERNAL leaves, and 8 aggregate AND gates**. Its **16 realistic fault families** and **2,517 preregistered zero-to-fourway masks** are finite-model cases, **not one million independent source mutations**. **two controlled physical Git repositories** supply bounded counterexamples, not independent target or user acceptance.

## Documentation by goal

**First-time user:** [Getting started](docs/GETTING_STARTED.md) · [Architecture](docs/ARCHITECTURE.md).
**Coding assistant or reviewer:** [Agent adoption](docs/AGENT_ADOPTION.md) · [AGENTS](AGENTS.md) · [Continuous development](docs/CONTINUOUS_DEVELOPMENT.md).
**Forensic investigator:** [File Lab](docs/FILE_LAB.md) · [Holistic forensics](docs/HOLISTIC_FORENSICS.md) · [Engineering debt](docs/ENGINEERING_DEBT.md).
**Product or release owner:** [Governance](GOVERNANCE.md) · [Security](SECURITY.md) · [Release](docs/RELEASE.md).
**Full documentation, history and contracts:** [Index](docs/INDEX.md) · [Documentation DoD](docs/DOCUMENTATION_DOD.md).

**Decision rights are external:** people/host controls approve. **Source of record:** committed Git, not chat. **Why:** models cannot certify external behavior. **Runtime:** local CLI. **Read in order:** README → task guide → contract → evidence.

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

## Enterprise evaluation boundary

**Enterprise evaluation candidate, not enterprise-qualified.** **Product:** `cora` scope defined; independent user acceptance open. **Software:** `cora-engine` and `cora-release-verification` source tested, without a supported release. **Repository:** Git, contracts and CI exist; effective host rules and non-author review are unverified. Adoption needs real target oracles, isolation, security/support commitments, provenance, rollback and accountable human acceptance. [Formal three-boundary DoD](docs/DOD_RELEASE_READINESS.md) · [release](docs/RELEASE.md) · [governance](GOVERNANCE.md).

**Decision rule:** `PASS_SCOPED` covers only measured scope; `NOT_RUN` and `BLOCKED_EXTERNAL` cannot be converted into approval.

## Operating boundaries

**External acceptance remains `BLOCKED_EXTERNAL`** without independent target, reviewer and host evidence. **GitHub workflow files alone do not prove** enforced rules. Absent imports do not prove `safe_deletion`; source CI does not authorize release.

## Engineering map

**Product:** assurance. **Software:** `cora-engine` and `cora-release-verification`. **Repository:** source, tests, CI and **historical ADRs**. [Index](docs/INDEX.md) identifies current document owners; original Git retains decision history.
