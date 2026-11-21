[![ROA Research Programme](https://img.shields.io/badge/ROA-Research_Programme-1f6feb)](https://github.com/Luke883i/academics)

<!-- programme-header:v2 -->
> **ROA Research Programme · AOSP ecosystem** — [Author & programme hub](https://github.com/Luke883i/academics) · [ROA theory](https://github.com/Luke883i/ROA) · [CORA assurance](https://github.com/Luke883i/cora). Every repository is independently readable. Membership does not imply formal derivation, shared runtime, scientific validation, certification, or production readiness. Repository-local code, evidence, and governance remain authoritative.

# CORA — Continuous Ontological Repository Assurance

**Engineering evidence for AI-assisted software changes.**

**CORA helps plan software changes, verify Git evidence and expose gaps.** It combines a conversational method with a local Python 3.11+ assurance engine.

**CORA is not a coding agent**, a ChatGPT plug-in, an automatic runner or a release approver. It can **produce reproducible pre/post-merge review reports** describing **the proposed change**, **the source evidence**, **tests or counterexamples** and **the work still needed**.

**Why it matters:** patches are not proof; readers need decisions, tests and unresolved risks.

```text
TARGET Git repository = application source of truth
CORA source ZIP = optional read-only reference (no Git history)
ChatGPT Project = canonical prompt + authorized attachments, not a runner
  -> A0 goal -> backward AND acceptance tests -> proposed slice
  -> NO runner: METHOD_ONLY / NOT_RUN; explain the next choice
  -> WITH separately authorized coding agent + runner:
       target Git commit + native tests + falsifiers
       -> CORA-ENGINE -> exact Git SHA + evidence dossier
       -> opt-in verified temporary ZIP -> human review
```

**Product** = engineering assurance; **software** = the `cora` CLI and verifiers; **repository** = Git source, contracts and CI. None proves target-product readiness.

**Recommended use:** review an authorized Git change. **Audience and conditions:** CTOs, developers, reviewers and coding agents; Python 3.11+, Git and authorized execution tools. **Open source license:** [MIT](LICENSE).

**Current status:** experimental `cora-audit 1.0.0a5`, **not a stable API or verified public release**. **Document status:** CURRENT. **Current scope:** Git source. **Operational use:** inspect commits. **Evidence:** Git and scoped tests. **Limits:** `BLOCKED_EXTERNAL`. Verify the exact checked-out Git revision. **Category:** engineering assurance.

## First five minutes — choose your path

| Choose one of two modes | What you do | What CORA can actually do |
| --- | --- | --- |
| **A — CORA-METHOD in ChatGPT Project (recommended for beginners)** | Explain your desired application in normal language, ask for a falsifiable plan and choose the next small step. | Guide the conversation. **No runner = METHOD_ONLY / NOT_RUN**; the Project and a source ZIP do not execute code. |
| **B — CORA-ENGINE on a computer or with an authorized coding agent** | Use Python, Git and explicit permissions; run native tests and the local CLI at a named SHA. | Produce source-bound reports and a verified offline handoff. This does **not** approve a PR or prove the product works. |

**Remember:**
- **Beginner:** plan without Python.
- **Authorized:** agent edits; runner tests; CORA reports gaps.


**Choose A:** five ChatGPT steps; no installation. **Choose B:** Git, Python and permission. Terminal commands:

```sh
python -m pip install -e .
cora --help
cora snapshot . --revision HEAD --output /tmp/cora-ledger.json
cora verify-ledger /tmp/cora-ledger.json --repo .
```

For scoped evidence see [One-Run](#one-run--one-command-one-evidence-dossier); snapshots are Git-only, not target tests. [Getting started](docs/GETTING_STARTED.md) explains setup.

## Path A — Use CORA in a ChatGPT Project — beginner walkthrough

**Project chat and method guidance (`METHOD_ONLY` unless a runner is separately authorized).** ChatGPT proposes a contract and an agent task packet; attaching a ZIP does not install or run CORA.

**Start here:** this documented beta route assumes **ChatGPT Pro or Edu**; Projects are available on other plans, but read/write and runner permissions must be checked separately. CORA-ENGINE does not require ChatGPT.

1. **Create your GitHub repository:** on [GitHub](https://github.com) select **New repository**, name your webapp and add README. Record its Git SHA. The **target repository** holds your application, not CORA.
2. **Prepare ChatGPT:** from [Luke883i/cora](https://github.com/Luke883i/cora) select **Code → Download ZIP** on main (source reference, **no `.git` history**). Copy the [single canonical prompt](docs/AGENT_ADOPTION.md#chatgpt-project-beta-adapter). Choose **New project** → **Project settings** → **Project instructions**; paste the prompt and attach ZIP. This neither installs CORA nor runs code.
3. **Share only authorized source:** attach a verified target ZIP or grant **read access** to repositories. GitHub connector abilities vary: read-only is not permission to push or merge; write actions require verified permissions and explicit authorization. Example A0: "A reporter creates an issue; a reviewer sees it after reload; an outsider cannot close it."
4. **Plan, then authorize separately:** ask CORA-METHOD for **backward requirements decomposition**, AND tests, a falsifiable roadmap and reversible POST → SQLite → GET slice. In Project chat this is *a proposal*. A **write-capable coding tool**, such as Codex, needs authorization; a **separate Python runner** executes tests. CORA-METHOD guides you **without** executing CORA-ENGINE. Without an authorized runner, say `METHOD_ONLY` / `NOT_RUN`.
5. **Verify, then continue:** with permission, commit, run target-native tests and One-Run at the **same SHA**. With a runner create `--chat-step` and `--chat-bundle`, verify ZIP and upload its latest copy to this Project chat. Read `iterations/000001/handoff.md` and DoD. ZIP is **not** automatic chat memory and **neither automatic chat capture nor authenticated review**. [Complete guide](docs/GETTING_STARTED.md#github-and-chatgpt-project-from-zero).

**Verified offline cockpit (requires One-Run):**

```sh
cora verify-process /tmp/cora-run.json --repo . --one-run \
  --chat-bundle /tmp/cora-session.zip --chat-cockpit-html /tmp/cora-cockpit.html
```

- Open `/tmp/cora-cockpit.html`; navigate **Overview**, **DoD & evidence**, **Blockers**, **Choices**.
- **EXPLAIN**, **REPLAN**, **PROPOSE_NEXT_CHECK** link to copyable prompts; no execution or automatic replanning.
- No runner/verified ZIP? Stay METHOD_ONLY; never invent PASS.


### Repository anatomy — one minute

`README.md` explains; `docs/GETTING_STARTED.md` installs; `docs/AGENT_ADOPTION.md` owns the **single prompt**. [Architecture](docs/ARCHITECTURE.md#filesystem-anatomy-at-the-current-git-revision): `src/cora/` engine, `tests/` and `tools/` checks, `.cora/` and `schemas/` contracts, `.github/workflows/` CI, `examples/` samples. Existence is not execution.

### Humanistic, legal and organizational perspectives — noncanonical

Humanistic: people choose ends. Legal: hashes are not signatures. Organizational: owners accept risk. None is product proof.

## Path B — authorized coding agent and local CORA-ENGINE

**Executable outside ChatGPT Project, not a third chat mode.** Authorized agent edits Git; separate runner executes target-native tests. CORA-ENGINE (local Python CLI) checks the exact SHA, not reviewers or product behavior. **With no runner, this path is `NOT_RUN`.**

1. **Plan:** [agent adoption](docs/AGENT_ADOPTION.md), [R1–R4 DoD](docs/DOD_PR20_CONVERGENCE.md), negative tests and rollback.
2. **Execute:** authorize one slice, commit and test.
3. **Verify:** premerge with `--contextual --intent`; **The same intent is required for replay**.
4. **Decide:** inspect gaps. **Run real tests and obtain independent review separately.** CORA **does not independently write a feature**.

The [LEVEL / NILO experiment](docs/CONTINUOUS_DEVELOPMENT.md#level-demonstration-local-evidence-verifiable-engineering-lifecycle) proposes a slice needing genuine browser tests; it is **not an already delivered game**.

## What works today

**CTO evaluation snapshot — source-scoped, not an enterprise-readiness certificate**

| Decision question | Current answer |
| --- | --- |
| **Who / what?** | CTOs, reviewers, AI coding-agent operators: bounded software change, falsifiable DoD, unresolved obligations. |
| **Method / engine** | **CORA-METHOD** guides third-party agents; **CORA-ENGINE** is the local Python CLI. The agent edits; CORA checks evidence, not approval. |
| **Targets / runtime** | Git-bound source inspection, partial Python AST, static JavaScript ESM; **Teddy Node** and **ICTC HTTP/SQLite** pilots. |
| **Delivery / compatibility** | **MIT**, **Python 3.11+**, `cora-audit 1.0.0a5`; no declared mandatory Python runtime dependencies. |
| **Supply chain** | **SBOM (CycloneDX 1.6): GENERATION_IN_CANDIDATE_CI**; **SCA/CVE: SCAN_CI_BUILD_TOOLS_ONLY**; **artifact signing / SLSA provenance: NOT_ATTESTED**. |
| **Governance** | Execution needs authorization. **Independent reviewer, enforced branch rules, release: BLOCKED_EXTERNAL**; no production security SLA. [Security](SECURITY.md) · [Release](docs/RELEASE.md). |

**Assurance levels:** **L1** = Git/source checks; **L2** = bounded product experiments; **L3** = optional external assurance. L1/L2 may be useful without L3; CI cannot approve a release.

**71 declared CLI commands** in [capability atlas](.cora/assurance/capability-atlas.json) are inventory, not 71 independently proven features. [parser-checked CLI reference](docs/CLI_REFERENCE.md) · [complete documentation index](docs/INDEX.md).

**CORA is not an eleventh engineering method.** Source graphs and mutation tests offer partial views, not full behavioral or security proof. [Method crosswalk](docs/CONVERGENT_ASSURANCE.md#method-crosswalk--borrowed-perspectives-not-full-implementations).

## One-Run — one command, one evidence dossier

```sh
cora process-run . --revision HEAD --process full --one-run --profile comprehensive \
  --output /tmp/cora-run.json --atlas-html /tmp/cora-run.html
cora verify-process /tmp/cora-run.json --repo . --one-run --atlas-html /tmp/cora-run.html
```

The dossier distinguishes `PASS_SCOPED`, `NOT_RUN`, `REFUTED` and `BLOCKED_EXTERNAL`. **The default does not execute arbitrary target tests**. Keep native test receipts separate. [Chat handoff](docs/AGENT_ADOPTION.md#portable-chatgpt-handoff-opt-in) uses `--chat-step` / `--chat-bundle`: a temporary, operator-produced ZIP of numbered steps, evidence gaps and handoffs, **not** automatic chat memory, a signature or approval.

**Change range:** `--change-base BASE_SHA` selects BASE→HEAD; default covers one commit. Neither authenticates PR metadata.

**Native Gold pilots:** bounded, consented Teddy Node and ICTC HTTP/SQLite tests. LUMEN browser and NILO remote remain unobserved; source PASS cannot attest runner identity. [Pilot evidence](docs/GOLD_ASSURANCE.md).

**Other repos:** `--portable-profile` reads source; `--portable-parse-js` parses ESM, not execution. [Limits](docs/CONTINUOUS_DEVELOPMENT.md).

**H-FORGE:** [source stage](docs/HOLISTIC_FORENSICS.md#h-forge-optional-experimental-profile); 77 cases, dynamic consumers and P5 acceptance unverified.

## How CORA works

**Standard engineering contract:** actor, outcome, owner, negative oracle, rollback and test trace. This **does not certify compliance** with ISO/IEC/IEEE 29148, ISO/IEC 25010 or NIST SSDF. [Worked contract](docs/GETTING_STARTED.md).

**Micro-example — three evidence planes:** **Product:** an issue survives restart and outsiders cannot close it. **Software:** UI/API behavior, durable database readback and access denial require **separate real observations**. **Repository:** bind test receipts and rollback to a named Git SHA; source PASS is not product acceptance.

**Additional analytical lenses (research, not standards):** contradicted receipts and unknown consumers remain hypotheses.

**1. Specify the outcome.** Translate natural-language intent into an **AND-dependency graph**. Reason **backward**; an **unknown prerequisite** remains open. [Worked application contract](docs/CONTINUOUS_DEVELOPMENT.md#example-contract-and-evidence-ladder--portable-corrective-action-app).

**2. Change one coherent unit.** Use **authorized tools**; CORA inspects Git **content-addressed blobs**, **directory trees**, commits and PR history. **New source SHA** requires replay. A hash can identify committed bytes; it cannot authenticate a human reviewer.

**3. Try to disprove it, then stop intelligently.** Challenge **seeded combinations** with a **separate expected-result rule** and authorized **physical mutation testing**. Record killed, **surviving and inconclusive** mutations. A **fixed scenario catalog and final window** supports **bounded convergence**, **not proof of complete correctness**. After **no-progress rounds**, replan; CORA **does not predict N**.

**Target examples, not universal validation:** [ICTC](https://github.com/Luke883i/ictc) (HTTP/SQLite, source/UX verification), [Teddy](https://github.com/Luke883i/teddy) (Node) and [iKant_EDU](https://github.com/Luke883i/iKant_EDU) (unknown consumers, reversible repository contraction). Source histories and native pilot evidence have distinct owners; CORA did not independently certify these products. [Pilots](docs/GOLD_ASSURANCE.md).

**Terms:** *intent mining* extracts obligations; *reticular DoD* maps dependencies; *semantic slices* bound changes; *blobbing/materialization* writes Git objects; *semantic mutations* challenge claims; *semantic saturation* is a bounded lack of new findings. No finite test proves universal correctness.

## Interpret a CORA result

| Observed state | Meaning | Never infer |
| --- | --- | --- |
| Proposal / `METHOD_ONLY` | Roadmap only | Executed code |
| `NOT_RUN` / `UNKNOWN` | Missing observation | PASS |
| `PASS_SCOPED` on exact SHA | Named source check | Target acceptance |
| `BLOCKED_EXTERNAL` | Human/host witness outstanding | Merge authority |

**A source digest does not authenticate a human reviewer** or target runtime. `NOT_RUN` and `BLOCKED_EXTERNAL` are not PASS. See [evidence boundaries](docs/CONVERGENT_ASSURANCE.md).

## Final Experimental Baseline — bounded evidence

The [final experimental DoD](.cora/contracts/dod/final-experimental-dod.json) distinguishes **15 SOURCE leaves, 7 EXTERNAL leaves, and 8 aggregate AND gates**. Its **16 realistic fault families** and **2,517 preregistered zero-to-fourway masks** are finite-model cases, **not one million independent source mutations**. **two controlled physical Git repositories** supply bounded counterexamples, not independent target or user acceptance.

## Documentation by goal

**First-time user:** [Getting started](docs/GETTING_STARTED.md) · [Architecture](docs/ARCHITECTURE.md).
**Coding assistant or reviewer:** [Agent adoption](docs/AGENT_ADOPTION.md) · [AGENTS](AGENTS.md) · [Continuous development](docs/CONTINUOUS_DEVELOPMENT.md).
**Forensic investigator:** [File Lab](docs/FILE_LAB.md) · [Holistic forensics](docs/HOLISTIC_FORENSICS.md) · [Engineering debt](docs/ENGINEERING_DEBT.md).
**Product or release owner:** [Governance](GOVERNANCE.md) · [Security](SECURITY.md) · [Release](docs/RELEASE.md).
**Full documentation, history and contracts:** [Index](docs/INDEX.md) · [Documentation DoD](docs/DOCUMENTATION_DOD.md). [PR #1–#89 trajectory, gaps and release gate](docs/AUDIT_PR01_89_AND_RELEASE_GATE.txt).

**Decision rights are external:** people and host. **Source of record:** Git, not chat. **Why:** source is not authority. **Runtime:** local CLI. **Read in order:** README → guide → contract → evidence.

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

**Enterprise evaluation only.** Usability, target tests, rollback, host controls and review remain unqualified. [Formal three-boundary DoD](docs/DOD_RELEASE_READINESS.md) · [release](docs/RELEASE.md) · [governance](GOVERNANCE.md). `PASS_SCOPED` is not approval; `NOT_RUN` and `BLOCKED_EXTERNAL` remain open.

## Operating boundaries

**External acceptance remains `BLOCKED_EXTERNAL`** without independent target, reviewer and host evidence. **GitHub workflow files alone do not prove** enforced rules. Absent imports do not prove `safe_deletion`; source CI does not authorize release.

## Engineering map

**Product:** assurance. **Software:** `cora-engine` and `cora-release-verification`. **Repository:** source, tests, CI and **historical ADRs**. [Index](docs/INDEX.md) identifies current document owners; original Git retains decision history.
