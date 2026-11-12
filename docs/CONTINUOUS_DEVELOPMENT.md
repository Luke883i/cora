# CORA continuous development — pre-merge, post-merge, agent constraints

**Status:** v1.experimental, evidence and review framework, **not** a coding assistant or a GitHub administrator. The supported package remains `cora-audit` with one CLI, `cora`. The source of truth is a Git commit; CI and review attestations require separately trusted GitHub controls.

## Current change-range discipline (PR59)

Record explicit original-Git BASE and HEAD for a multi-commit change, then run the **existing** `process-run --change-base BASE_SHA --one-run --profile comprehensive` and replay the receipt. Do not infer complete PR coverage from a single-commit diff; a supplied base is not authenticated GitHub metadata. Review obligations are path-triggered hypotheses and may require semantic/editorial evaluation, runtime oracles and human decisions. Historical v1 receipts stay source-bounded; no execution or release approval is implicit.

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

## Current supporting operations (original owners, no parallel runner)

The following operations supplement the primary `process-run` / `verify-process` review path. They do not retire checks, execute unknown target code without consent, or certify enterprise readiness.

| Goal | Original command / source | Boundary |
| --- | --- | --- |
| Inspect workflow consumers | `cora workflow-audit . --revision HEAD --output /tmp/workflows.json` then `cora verify-workflows /tmp/workflows.json --repo .` | A duplicate-looking workflow is not safe to delete; callers and actual hosted enforcement must be reviewed. |
| Correlate method/agent hypotheses | `cora method-synthesize . --revision HEAD --output /tmp/cora-case.json` and `cora verify-method-synthesis /tmp/cora-case.json --repo .` | Typed observations remain separate from unauthenticated AI hypotheses and target runtime. |
| Diagnose repeatability | `python -m cora.ci_repro --repo . --sha "$(git rev-parse HEAD)" --repetitions 3 --output /tmp/cora-ci-repro.json` | All PR25/PR26 failures and timeouts count; a green repeat cannot prove root cause or eliminate flakiness. |
| Execute One-Run | `cora process-run . --revision HEAD --process full --one-run --profile comprehensive --output /tmp/one.json` | The 71-command atlas is a catalog; at most eight safe methods run, without automatic target tests or release authority. |

**Scope and iteration:** preserve original Git/test witnesses for every method, negative mutant, and new feature; record exact BASE/HEAD, actual execution or `NOT_RUN`, blockers and postmerge rechecks. The [method atlas](../.cora/contracts/profiles/method-atlas.json), [workflow DoD](../.cora/contracts/dod/workflow-dod.json) and [postmerge DoD](../.cora/contracts/dod/postmerge-repro-dod.json) retain formal owners. PR24/25/33/36/39 development details remain in the [changelog](../CHANGELOG.md), their source commits and associated DoDs; these are not alternate instructions or proof of independent hosting.

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


## Cross-repository source/evidence convergence (PR50 — candidate)

**Abstract goal:** on two independently owned maintained codebases, an engineer
must be able to reconstruct intent -> accountable owner -> bounded source change
-> falsifier -> observed outcome -> unresolved blocker -> decision, from exact
Git objects, with *less combined work* than a controlled alternative. This is
a product hypothesis, not an established efficiency or usability result.

The canonical machine-readable reticulum is
[\`crossrepo-convergence-dod.json\`](../.cora/contracts/dod/crossrepo-convergence-dod.json):
18 typed local obligations, five intermediate AND cuts and two globals.
\`G_SOURCE_CANDIDATE = I_S0 AND I_S1 AND I_S2 AND I_S3\`;
\`G_GOVERNED_PORTABILITY = G_SOURCE_CANDIDATE AND I_S4\`.
The \`I_S2\` and \`I_S3\` cuts include external obligations, so all-source CI
cannot silently declare \`G_SOURCE_CANDIDATE\` accepted. The current
target-repository/source-method observations remain independent of user or
provider validity; the source reticulum and an acceptance receipt are
different types of artifact.

| Cut | Minimal observable obligation | Metric / falsifier |
| --- | --- | --- |
| S0, CI repair | Existing source and claims tests recognize current README and preserve negative mutants | Original exact-head 11-run baseline reconciled; 0 weakened checks; post-merge separately rerun |
| S1, portable source | Own profile/owner/path identities; source methods on distinct real Git targets; replay | >=2 target Git fixtures, 0 forged SHA/owner/replay acceptance; JS/dynamic UNKNOWN |
| S2, evidence | Bytes, SHA and named oracle; no caller JSON promoted to execution | 0 tamper/path/false-PASS acceptance; real behavior independently observed later |
| S3, transfer | Typed method links, original source and target SHAs, provenance and invalidation | 0 stale-source reuse; actual upstream object and adoption readback external |
| S4, qualification | Independent maintained-target behavior, novice tasks, guarded release, measured efficiency | >=2 live maintained targets; >=8 new-user sessions, >=80% task success, 0 critical false promotions; preregistered time comparison |

**Permitted source-side result:** source paths, Git SHA, declared profile and
byte-digest replay can be checked locally. Imported HTTP/browser/log evidence
proves only byte integrity unless the original executor is independently
attested. No target tests, models or remote URLs execute implicitly. Missing
source, incomplete dependencies, mismatched SHA, blocked external review or
insufficient usability data remain explicit blockers.

**Cross-repository roles:** \`teddy\` and \`NILO\` are candidate target
examples, not CORA-owned products. A repository-local ontology or existing
consumer map outranks a CORA convenience default. \`LUMEN -> Teddy\` is a
candidate documented transfer of Render deployment method, while
\`CORA -> NILO\` is a candidate transfer of engineering discipline;
both require separate source/adaptation readback for an execution claim.
Neither relation proves shared runtime or authority.

**Staging / checklist:** first preserve repository and documentation checks;
then run portable source profiles in a clean, committed checkout; challenge
paths, owner, SHA, negative-oracle and source mutations; compare exact source
receipts with independent readback; finally obtain independent studies,
governed host review and real evidence of effort reduction. If a source gate
fails, stop and correct that owner. If an external gate is absent, retain
\`BLOCKED_EXTERNAL\`, not an invented PASS. Recompute after actual merge SHA.
