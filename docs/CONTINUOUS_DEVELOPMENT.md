# CORA continuous development — pre-merge, post-merge, agent constraints

**Status:** v1.experimental, evidence and review framework, **not** a coding assistant or a GitHub administrator. The supported package remains `cora-audit` with one CLI, `cora`. The source of truth is a Git commit; CI and review attestations require separately trusted GitHub controls.

## Operating model

1. **Plan and change:** Human product/technical owners define desired behavior and blast radius. A coding agent may propose a patch but must read [AGENTS.md](../AGENTS.md) and may not approve it.
2. **Pre-merge:** `cora dev-premerge REPO --base BASE --head HEAD` inspects committed Git changes and the continuous policy read **from BASE**. It classifies review paths conservatively and issues an immutable, re-playable receipt. Even `OBSERVED_REVIEW_REQUIRED` **does not mean approved**. Bootstrap without a policy in BASE remains `BOOTSTRAP_REVIEW_REQUIRED`.
3. **Independent checks:** Run repository tests, security tools, self-audits, and CORA `process-run --process full` as separate checks with source SHA; human reviewers inspect results and deployment/data-retention obligations. Workflow files in an untrusted PR cannot themselves confer independence. An actual admin must configure mandatory branch rules/reviews and trusted checks outside PR-controlled code.
4. **Post-merge:** `cora dev-postmerge REPO --previous PREVIOUS --head HEAD --with-debt` records ancestry, changed paths, trusted-policy status and a source-bound change in **debt signals**. The delta is not an assertion that a defect was introduced, fixed, or that runtime is healthy. Deploy/runtime rollback, incident response, SLOs and telemetry require separately authenticated systems.
5. **Continuous improvement:** Track unresolved source, build, security, governance, data and runtime evidence, run periodic trend reviews, record remediation owners and verify after closure. Recalibrate thresholds from independent outcomes, not model fixture counts.

### Commands

```bash
cora dev-premerge . --base HEAD~1 --head HEAD --output /tmp/premerge.json
cora verify-dev-gate /tmp/premerge.json --repo .
cora dev-postmerge . --previous HEAD~1 --head HEAD --with-debt --output /tmp/postmerge.json
cora verify-dev-gate /tmp/postmerge.json --repo .
cora agent-check /tmp/agent-proposal.json --repo . --output /tmp/agent-review.json
cora stress-continuous --seed 883 --cases 1000000
```

Save receipts **outside** the target working tree. `--strict` on pre/post commands emits exit code 2 for **every outstanding blocker** (including bootstrap and high-risk paths needing independent review), not just a blocked status label; it **never upgrades** a report to authorized. This PR introduces the policy for the first time, so its own BASE does not contain it and the bootstrap cannot be declared independently approved.

### Agent proposal contract

`cora-agent-proposal/1` example (use actual Git SHAs and exact old/new changed-path set):

```json
{
  "schema": "cora-agent-proposal/1",
  "agent_id": "ikant-code-agent-identifier",
  "base_commit": "<BASE_SHA>",
  "head_commit": "<HEAD_SHA>",
  "intent": "Explain the smallest expected functional change",
  "changed_paths": ["src/cora/module.py"],
  "test_claims": ["UNVERIFIED: python -m unittest ..."],
  "unknowns": ["external consumers and runtime behavior"],
  "authorized_action": "NONE"
}
```

No direct GitHub identity authentication, independent reviewer proof, test execution attestation, production deploy evidence or signed SLSA provenance is implemented by `agent-check`. Test statements remain *agent assertions* even if a referenced source path exists. **An AI must never self-attest that an independent reviewer approved.**

## Normative crosswalk (inspiration, not certification)

- **NIST SSDF SP 800-218**: PO (prepare), PS (protect), PW (secure implementation), RV (response/learning): map to explicit human ownership, immutable evidence, tests/review, post-merge follow-up.
- **OpenSSF OSPS Baseline v2026.08.28**: branch/protected change/review controls; local workflow checks are insufficient to claim enforcement.
- **SLSA 1.2 Source and Build Tracks**: source provenance/authorized revisions distinct from build attestation; CORA only stores Git-bound local receipts, not signed SLSA source/build attestations.
- **DORA**: trend observability and post-deployment quality metrics; CORA does not infer change failure rate, lead time or deployment frequency from commit history alone.
- **GitHub Actions security**: use read-only `pull_request` workflows; **never** run untrusted PR code under `pull_request_target` with privileged secrets.

Official references: https://csrc.nist.gov/pubs/sp/800/218/final · https://baseline.openssf.org/ · https://slsa.dev/spec/v1.2/ · https://dora.dev/ · https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target

## Trust boundary and known debt

The policy and code live in the same repository that an agent can edit. Until protected GitHub branch rules, independent reviewer permissions and required trusted checks are configured by an administrator, **CORA cannot guarantee** a user or agent cannot bypass them. GitHub ruleset inspection on this private repository currently returns HTTP 403 due to account/plan restrictions, which is an **unverified control**, not proof of enforcement or non-enforcement. This first PR is a **bootstrap** and needs human administrator acceptance.

Post-merge without real CI/deployment telemetry is not an end-to-end operational health gate. Any result that says `OBSERVED_REVIEW_REQUIRED` is an audit signal, not a merge authorization. No automated deletion, code rewrite, release or deployment is performed by these new tools.

### Review artifact retention

The PR workflow uploads only JSON review receipts and deterministic model reports for **14 days**; the post-merge job uploads its JSON drift receipt for **30 days**. These are expiring review artefacts, not authoritative durable records, signatures, SLSA attestations or a replacement for an approved record system. Output paths and CI artifacts can still disclose repository metadata, so use repository-appropriate access controls. The workflow never includes source files in these uploads.

## Current PR-20 opt-in contextual workflow

When the target has its own committed ontology and a trusted BASE-committed `.cora/continuous-policy.json`, pass a bounded `--intent` to `cora dev-premerge TARGET --base BASE --head HEAD --contextual --intent "Specific change with acceptance tests" --convergence-contract PATH --output REPORT`. Verify with `cora verify-contextual-gate REPORT --repo TARGET --intent "Specific change with acceptance tests" --convergence-contract PATH`. Run the equivalent `dev-postmerge --contextual` against the **actual merged** revision, not the former PR SHA. The legacy gate remains available without `--contextual`.

Source candidates and witness invalidations are not authenticated consumer, host or runtime observations. Missing intent yields DEBT_BLOCKED, even if deterministic local source checks can otherwise run. See [agent adoption](AGENT_ADOPTION.md) and [convergent assurance](CONVERGENT_ASSURANCE.md).

## CI workflow rationalization (PR-24 proposal)

CORA adapts the iKant_EDU PR-201/202 inventory, PR-205 historical preservation, and draft PR-215 consolidation proposals. Those observations are engineering precedents, not an authorization to delete workflows.

Run `cora workflow-audit . --revision HEAD --output /tmp/workflows.json` and `cora verify-workflows /tmp/workflows.json --repo .`. Compare with `--base BASE_SHA` to inspect additions, modifications and removals. This read-only analysis identifies partial trigger/job syntax, local workflow callers, source references and duplicate checks; it cannot prove absent external consumers or equivalent runs.

`.cora/contracts/dod/workflow-dod.json` specifies `G_WORKFLOW_SOURCE` and `G_WORKFLOW_GOVERNED` with external E01-E04 evidence open. A reviewer must establish replacement behavior and actual platform controls before separately approving retirement. A source receipt never executes or modifies target workflows.

## Method synthesis and governed AI hypotheses (PR-25)

`cora method-synthesize . --revision HEAD --output /tmp/cora-case.json --analyst-request /tmp/cora-questions.json` reuses the original Git-bound artifact and workflow auditors, software ontology, process catalog and reticulum. `cora verify-method-synthesis /tmp/cora-case.json --repo .` replays the exact committed source. Optional `--artifacts`, `--workflows` and `--process` inputs must be independently reverified and share one commit; optional `--hypotheses` claims are never execution evidence.

The [method atlas](../.cora/contracts/profiles/method-atlas.json) connects fourteen CORA procedures to nine industry methods as inspiration, **not standards certification**. The [AND DoD](../.cora/contracts/dod/method-synthesis-dod.json) keeps seven source obligations distinct from four external requirements. A workflow role disagreement is `SOURCE_CONTRADICTION`; a shared caller is `OBSERVED_SOURCE_RELATION`; a proposed workflow adjustment is `INFERRED_REVIEW_ONLY`; unavailable process evidence is `OBSERVED_SOURCE_GAP`. The analyst request embeds bounded questions rather than source code or a purported LLM conclusion.

Do not interpret shared inputs as equivalent executions, source proofs as release attestation, or typed AI suggestions as authenticated facts. Real usability, maintained-target behavior, independent host/reviewer authority and postmerge effects remain outside this source-only case.

## PR33 — measurable post-merge forensics, not synthetic release approval

**Objective:** diagnose the recurring post-merge PR25 and PR26 original-Git falsifier failures using complete, attributable repeated observations, rather than one green rerun. Use `python -m cora.ci_repro --repo . --sha "$(git rev-parse HEAD)" --repetitions 3 --output /tmp/cora-pr33-measured.json` from a clean, authorized CORA checkout. The runner executes the two original test cohorts (PR25 and PR26) in three separate child interpreters each, without `shell=True` and without forwarding GitHub API tokens. All outcomes, including failed attempts and timeouts, are counted; later PASS cannot erase any FAIL.

### Quantitative checklist and gate ownership

| Gate | Metric or condition | Evidence / acceptance |
|---|---|---|
| R1 — Git identity | Full source `commit`, Git `tree`, exact checkout HEAD | Git original object reads; a tree match does not equate distinct commits |
| R2 — Environment parity | Python 3.11 & 3.13, Git version, coverage version, dependency SHA-256 | Per-job report and human check for parity; no environment assumptions |
| R3 — Git mutation coverage | PR25 and PR26 cohorts, >=3 invocations each per Python | Six samples per matrix job; runner reports every return code |
| R4 — No masked failures | 0 failed or timed-out attempts; sample failure rate 0 | Any nonzero or timeout => `FAIL_OBSERVED` and nonzero CI exit |
| R5 — Traceability | Failed test IDs, stderr fingerprint, elapsed min/max/p95 | Attribution to exact SHA, job and source. Original trace in Actions logs |
| R6 — Independent RCA and delivery | Reproduction + validated counterexample, reviewed final-main CI, protected main, independent reviewer | External gate; cannot be closed by a probe report |

**Limit:** `PASS_SCOPED_REPEATABILITY_SAMPLE` means only the observed cohorts passed in that finite sample; it is not statistical proof that a flaky test no longer exists or that a root cause was found. `original_contract()` rechecks the Git-committed 21-node, noncompensatory [postmerge DoD](../.cora/contracts/dod/postmerge-repro-dod.json); source/model observations remain separate from independently observed merge, human approval and real release. Report's status never grants authorization. Compare unmodified CI logs across jobs before filing an independent root-cause conclusion.

## PR36 — an operational execution atlas, not an inflated command catalog

The one-run experience deliberately extends `process-run` and `verify-process`: it does not create a second command hierarchy. The execution receipt captures original Git commit/tree, the selected read-only source methods, each method's state and measured duration or explicit reuse/unmeasured marker, and separately declared excluded activities. The existing PR31 maturity and capability atlas remains the 71-command source catalog, **not proof of 71 executions**. Optional unit tests require explicit execution consent, never produce independent runtime authority and do not automatically become per-command PASS.

**Acceptance checklist:** G_EXECUTION = commit/tree source, bounded method scope, measured or explicitly unmeasured time and status; G_PRESENTATION = complete declaration/observed-run separation, readable searchable offline HTML, one JSON receipt, escaping, test consent; G_SOURCE_REPLAY = re-run source against immutable Git objects, reject altered HTML, 100k preseeded receipt mutations (2 positive + 30 negative families, zero oracle disagreements) and physical committed Git DoD falsifiers; G_GOVERNED_ONE_RUN and G_ONE_RUN_PRODUCT remain BLOCKED_EXTERNAL pending human acceptance, independent target execution, newcomer UX, host enforcement, release and rollback.

**Metrics and thresholds:** 71 declared/0 independently invoked CLI commands per source-only run; at most eight safe process methods, classified individually; every executed activity requires a duration; shared work must not be counted twice; no false PASS for BLOCKED or NOT_RUN; 100000 unique preseeded model inputs (6250 positive, 93750 negative), 0 disagreements and 0 unauthorized promotions, byte-identical same-seed replay. The 100k cases are **finite-model mutations of reports**, not 100k real Git changes or validated target defects. Exact original-Git DoD and artifact role registries form the provenance chain. Raw execution timings and unit-test exits cannot be independently authenticated through deterministic source replay alone.


## PR39 rule for future feature convergence

A future source engine, benchmark, runtime runner, UI, publication mechanism or governance claim must update the canonical feature atlas and artifact roles, introduce independent negative oracles, extend the existing One-Run lineage and explicit blockers, revise operator docs, and pass tests on exact HEAD. Changes to the four product proof boundaries must alter the versioned independent qualification DoD deliberately, with an independent reviewer. PR36–38 identities and earlier receipts remain immutable historical witnesses; no local green test may substitute for a missing external authority.


## LEVEL: contract-to-product development with bounded continuation (PR47 candidate)

**One promise:** convert an expressive human goal into successive, testable software
changes while preserving provenance, negative controls and an honest stopping
decision. **CORA is the local assurance/control protocol, not an autonomous
software writer, build authority or independent reviewer.** A human-authorized
coding agent and Git/build/test tools make the actual source changes and PRs.

### The minimum evidence graph, derived backward

Start at the observable goal, then ask *what evidence must exist before this
goal may be accepted?* Write prerequisites as an AND-DAG, never as a checklist
whose sum or score can compensate for a missing obligation.

| Node | Acceptance condition / evidence | Class | When absent |
| --- | --- | --- | --- |
| L0 | Expressive versioned human contract: actors, behavior, data, UX, exclusions, permitted effects, expected negative tests | SOURCE + human intent declaration | Stop for a specific missing choice |
| L1 | Existing owners/consumers and protected originals reconstructed on exact BASE and HEAD; unknown dependencies remain UNKNOWN | SOURCE | Block unsafe deletion or parallel owner |
| L2 | Dependency-ordered, atomic acceptance conditions and falsification oracles; all required children are non-compensatory | SOURCE | Next unresolved leaf is the next candidate |
| L3 | Bounded, reversible vertical slice: code + test + docs in the authorized target; Git blob/tree/commit provenance | SOURCE | Do not promote a design to executed software |
| L4 | Predeclared positive and negative tests with observed outcomes: distinguish real source mutants from finite-model perturbations | SOURCE for report; EXTERNAL for independent behavior | Surviving or not-run tests block acceptance |
| L5 | Seeded finite scenario coverage, independent reference rule, normalized-failure novelty plateau under a declared budget | FINITE_MODEL | A zero-novelty tail proves only the declared model window |
| L6 | Each explicitly executed One-Run has a portable append-only logical ZIP round, unresolved gap, next action and replay receipt | SOURCE | No invisible background work or invented round |
| L7 | Final PR source HEAD, test commands, dependencies, environment and CI outcomes attributable to one immutable revision; reverify postmerge SHA | SOURCE + external CI/host | A new commit invalidates prior final-HEAD conclusions |
| L8 | A new user can actually play and finish LEVEL's game; UX and accessibility tested on target browser | EXTERNAL | Product remains unqualified regardless of source scores |
| L9 | Independent reviewer, authority, licensing, protected branch rules, rollback and release decision | EXTERNAL | Never self-authorize merge or deployment |

**Global acceptance = L0 AND L1 AND L2 AND L3 AND L4 AND L5 AND L6 AND
L7 AND L8 AND L9.** The graph itself is a **declared contract**, not a
measurement that all ten nodes are closed. It remains source-qualified or
\`BLOCKED_EXTERNAL\` while target, reviewer or host witnesses are absent.
The same obligations apply whether the target is a platform, a web game
or a documentation-only PR; inapplicable requirements require a human
decision and recorded justification, not silent deletion.

### Adaptive continuation, not an invented number N

The **existing** \`cora process-run --one-run --profile comprehensive
--chat-step ... --chat-bundle ...\` creates one verified-by-source-replay
portable ZIP round per explicit invocation. The additional *continuation*
projection of \`verify_chat_bundle\` reuses the existing \`ordered_cut\` and
\`assess_cut\` logic. It returns the first unresolved DoD, linked next
falsifiers, actual iteration count and a conservative next-step decision.
The ZIP schema and prior rounds are **unchanged**; the additional field
is a read-only projection, not a new agent, daemon, authority or
automatic Git operation.

| Observed bounded condition | Suggested decision | Important non-inference |
| --- | --- | --- |
| First unresolved EXTERNAL prerequisite | \`REQUEST_EXTERNAL_WITNESS\` | A caller cannot certify independence |
| New exact source revision | \`REVALIDATE_CHANGED_SOURCE\` | New Git SHA alone is not test proof |
| Contract/goal changed after a round | \`REVIEW_CHANGED_CONTRACT\` | Renaming requirements cannot launder closure |
| Three matching semantic evidence snapshots despite changed roadmap wording | \`REPLAN_STALLED_REPORTS\` | Rewording, DONE_REPORTED or a synthetic count is not progress |
| No unresolved leaf in a source-only model | \`REQUEST_INDEPENDENT_ACCEPTANCE\` | Not an enterprise/product PASS |
| An unblocked SOURCE leaf with a linked falsifier | \`PROPOSE_NEXT_SCOPED_STEP\` | Proposal is not execution permission |
| Portability bound (128 rounds) reached | \`PAUSE_CAPACITY_AND_REBASE\` | Exhaustion is not convergence |

The assistant's dynamic N is therefore the **eventual number of actually
executed rounds**, not an oracle that predicts how many future turns are
needed. No source-only heuristic can prove that the next round will work.
Do not convert any decision above into an automatic privileged action.
A new human authorization may be required at a phase edge. Keep archive
ZIPs outside the repository and retain prior manifest digests separately
if tamper-detection across untrusted transfers matters.

**Anti-entropy check:** prefer a single existing owner, existing
execution and reporting mechanisms, one portable ledger and one source
of truth for each policy. Do not build a second task orchestrator, error
bus, claims registry, source census or fake reviewer. Record unchanged
SHA, unchanged DoD and unchanged attributable evidence across three
rounds as a *replanning signal*. A pure textual paraphrase does not
create engineering progress; neither does increasing the mutation
counter without enlarging the declared fault coverage.

### Concrete three-repository method transfer (not shared runtime)

- **CORA:** \`src/cora/reticulum.py\` supplies topological AND assessment;
  \`src/cora/chat_bundle.py\` supplies strict receipt and ZIP verification;
  \`src/cora/cli.py\` owns the existing One-Run and replay path.
- **ICTC:** \`docs/PROCEDURE_INTENT_CONVERGENCE_DOD_2026-08-18.md\` uses
  seven non-collapsible process models and owner-aware negative
  requirements. Its \`v3/saturation.mjs\` explicitly *assigns* novelty
  from 12 declared primitives among 136 fixed scenarios. Its
  \`v3/release-readiness-e2-product-mutants.mjs\` instead changes real
  code in a disposable clone and runs an E2 gate. These are distinct
  levels of evidence; nothing here certifies ICTC runtime as a whole.
- **iKant_EDU:** \`docs/CORA_PR_A_BACKLOG.md\` keeps unknown dynamic or
  external consumers UNKNOWN while deriving a read-only review
  backlog. M3/PR238 commit \`34750a2b2f192758b26919235922c4002ff040c0\`
  restored the byte-identical protected workflow and moved Git
  index/TREE/worktree source readback into
  \`scripts/project-review-callsites.mjs\`. Its
  \`governance/changes/m3-source-closure-20261108.json\` retains
  \`required_checks_verified=false\` and \`human_signoffs=0\`.
  **Protected owner/workflow invariants outrank a convenient new CI job.**

The **minimum interoperable interface** is an expressive A0 goal, an
immutable target BASE/HEAD, declared owners, a dependency-ordered
acceptance graph, named negative oracles, source/behavior distinction,
open gaps, a portable round reference, and separately governed
postmerge/release decisions. It does **not** require installing CORA
in ICTC or iKant_EDU, nor does it grant CORA the original products'
authority. A cross-repository method contract is not a shared
product/runtime contract.

### LEVEL demonstration: Local Evidence, Verifiable Engineering Lifecycle

A *proposed* new repository (not yet created or executed) will contain
the original 2D platform game **NILO — La Fabbrica delle Ore**.
One natural-language contract names story, characters, six levels,
three bosses, game-state transitions, checkpoint persistence,
accessibility and asset licenses. The first functional slice is not
six levels of untested code: it is one playable section with input,
camera, collision, checkpoint, HUD and a real browser replay test.
Then each later slice carries its own source SHA, positive and negative
tests, closed and open obligations, and rollback path.

**What would impress an external CTO:** run the game, select a visible
checkpoint behavior, inspect the actual test receipt, follow it to
the specific acceptance requirement and original intent, and return
to the exact source commit. Require the same proof chain for a mutant
that intentionally breaks persistence. A screenshot or a 10M finite
mask counter alone cannot deliver that outcome.

### Enterprise-candidate engineering controls: crosswalk, not certification

| Engineering goal | Concrete CORA/source surface | Gate not automatically satisfied |
| --- | --- | --- |
| Controlled software development; NIST SSDF SP 800-218 v1.1 PO/PS/PW/RV | Agent intent and scope, pinned Git artifacts, premerge guard, negative tests and postmerge source audit | Organization-wide secure SDLC, credential isolation, actual vulnerability response |
| Web-application security; OWASP ASVS v5.0.0 | Negative access/authorization and input cases can be declared and traced for a target | Actual security test of the game's HTTP/web surface; no claim of ASVS conformity |
| Build provenance; SLSA v1.2 | Pinned Git SHA, explicit build/test receipts and replay boundaries | Authenticated provenance, ephemeral isolation and independent trusted builder |
| Quality characteristics; ISO/IEC 25010:2023 | Explicit performance, usability, reliability, compatibility and accessibility requirements in product DoD | Observed behavior with real users/devices; no ISO certification |

Official normative references: [NIST SSDF](https://csrc.nist.gov/pubs/sp/800/218/final),
[OWASP ASVS](https://asvs.owasp.org/),
[SLSA build requirements](https://slsa.dev/spec/v1.2/build-requirements),
[ISO/IEC 25010](https://www.iso.org/standard/78176.html).
All mappings are **engineering analogies/requirements inspirations**,
not scope-specific conformity assessments.

### Minimal local falsification and qualification

The paired unit tests in \`tests/test_pr46_chat_bundle.py\` reject
false progress from reworded plans, fabricated independent
acceptance, changed policy/goal, changed exact source revision and
self-reported evidence. The original ZIP duplicate/path/size/hash
tests remain in force. \`tools/verify_documentation.py\` continues
to bind reader-facing claims to source. Before promoting the PR,
require its final-HEAD CI and real source replay, not merely an
assistant-generated PASS. Original host/workflow protections remain
unaltered. Independent gameplay, accessibility, reviewers and
license review remain \`BLOCKED_EXTERNAL\`.


## Example contract and evidence ladder — portable corrective-action app

**Historical PR47 README example, retained here as a hypothetical design,
not an executed build.** The user asks for a local corrective-action
tracker where reporters create actions, owners implement them, and only
reviewers may verify closure. Progress must survive restart; concurrent
edits must not silently overwrite state; external effects require consent.

Minimum expressive contract: a local browser UI and JSON API;
authenticated reporter/owner/reviewer roles; SQLite with versioned schema migrations; record `{id, title, owner, status, evidence_ref, revision}`;
workflow `OPEN → IN_PROGRESS → VERIFIED`; optimistic concurrency and
persistent readback; no cloud or deployment; test, usage guide and rollback
included in a PR. An essential unknown is a blocking question, not
permission to guess.

**Backward engineering:** verify-only-by-reviewer → deny an unauthorized
transition → persist/reload state → reject stale versions → test restart →
inspect role permissions → require actual test receipts on the final PR
HEAD and independent reviewer decision. Each leaf is mandatory and
noncompensatory; a graph or a green simulation does not close it.

**Source/materialization:** the authorized coding agent writes app,
migrations, tests and docs → Git records exact blob bytes, directory
tree, commit and proposed PR → CI and target tests run on the same
candidate SHA → physical source mutants challenge permission/persistence
oracles → PR documents actual receipts, survivors, gaps and rollback.
New commits invalidate prior final-HEAD test conclusions; merged main
requires its own reinspection. SHA equality never authenticates a test
host or human.

**Portable round:** an explicitly executed
`cora process-run --one-run --chat-step ... --chat-bundle ...`
adds source-scoped ZIP lineage. The read-only continuation projection
suggests REVALIDATE_CHANGED_SOURCE, REVIEW_CHANGED_CONTRACT or
REPLAN_STALLED_REPORTS when three consecutive source/evidence
snapshots are unchanged. This is a replanning signal, not a universal
semantic convergence theorem, autonomous execution or a product PASS.
