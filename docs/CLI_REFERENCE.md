# CORA CLI reference — current parser inventory

**Document status:** CURRENT
**Current scope:** Parser-checked command interface of the single existing cora CLI.
**Operational use:** Select an implemented command and read its parameters and output contract.
**Evidence:** src/cora/cli.py parser, command atlas and CI coverage receipts.
**Limits:** 71 declared commands are not 71 independently qualified product behaviors.


This is the complete inventory of the single `cora` CLI from `src/cora/cli.py`, maintained against its real `argparse` parser. Use `cora COMMAND --help` for exact flags and inputs; this is not evidence of test execution or a guarantee of behavioral correctness. Start with [Getting started](GETTING_STARTED.md) or [Agent adoption](AGENT_ADOPTION.md).

The [complete capability atlas](../.cora/assurance/capability-atlas.json) enumerates all **71 parser commands** with eight method families, implementation and test-source paths, classified side effects and non-CLI repository surfaces. This reference explains command entrypoints; the atlas describes source witnesses. Neither proves 71 independently qualified features, executed tests or real-target behavior. See the [capability DoD](../.cora/contracts/dod/capability-dod.json) for source-versus-external obligations.

## Git identity and source evidence

- `version` — see `cora version --help` for the supported inputs and scope.
- `audit` — see `cora audit --help` for the supported inputs and scope.
- `snapshot` — see `cora snapshot --help` for the supported inputs and scope.
- `verify-ledger` — see `cora verify-ledger --help` for the supported inputs and scope.
- `graph` — see `cora graph --help` for the supported inputs and scope.
- `explain` — see `cora explain --help` for the supported inputs and scope.
- `adapter-audit` — see `cora adapter-audit --help` for the supported inputs and scope.
- `verify-adapters` — see `cora verify-adapters --help` for the supported inputs and scope.
- `artifact-audit` — see `cora artifact-audit --help` for the supported inputs and scope.
- `verify-artifacts` — see `cora verify-artifacts --help` for the supported inputs and scope.
- `closure` — see `cora closure --help` for the supported inputs and scope.
- `verify-certificate` — see `cora verify-certificate --help` for the supported inputs and scope.

## CI/CD workflow discovery and governance

- `workflow-audit` — source-bound workflow inventory, reusable callers, risks and conservative adjustment/retirement candidates; run `cora workflow-audit REPO --revision HEAD --base BASE_SHA --output /tmp/workflows.json`. Never edits workflow files or attests external consumers.
- `verify-workflows` — rederive the exact source report: `cora verify-workflows /tmp/workflows.json --repo REPO`. See [continuous development](CONTINUOUS_DEVELOPMENT.md) for the review-only DoD and the host prerequisites.

**Full Git change range:** `cora process-run . --revision HEAD --change-base BASE_SHA` also works with existing `--one-run --profile comprehensive`. BASE must be a full, original-Git ancestor of HEAD. `verify-process` replays the pinned report. Default PR58 v1 remains first-parent single-commit; explicit v2 includes rename paths and actual tracked documents. Neither provides authenticated PR metadata, runtime behavior or release authority.

## Cross-method inference and source case

- `method-synthesize` — correlate source-verifiable role, workflow and optional process receipts on one Git commit. Use `cora method-synthesize REPO --revision HEAD --output /tmp/cora-method-case.json --analyst-request /tmp/cora-questions.json`. Optional `--artifacts`, `--workflows`, `--process` and `--hypotheses` retain original provenance and are revalidated; hypotheses never authorize actions.
- `verify-method-synthesis` — recompute from source and identical optional original inputs: `cora verify-method-synthesis /tmp/cora-method-case.json --repo REPO`. Replay is a source join, not an independent security/quality certification.

## Forensic analysis and debt

- `file-lab` — see `cora file-lab --help` for the supported inputs and scope.
- `verify-file-lab` — see `cora verify-file-lab --help` for the supported inputs and scope.
- `file-decision` — see `cora file-decision --help` for the supported inputs and scope.
- `select-file` — see `cora select-file --help` for the supported inputs and scope.
- `verify-selection` — see `cora verify-selection --help` for the supported inputs and scope.
- `holistic-audit` — see `cora holistic-audit --help` for the supported inputs and scope.
- `verify-holistic` — see `cora verify-holistic --help` for the supported inputs and scope.
- `archaeology` — see `cora archaeology --help` for the supported inputs and scope.
- `verify-archaeology` — see `cora verify-archaeology --help` for the supported inputs and scope.
- `annotate-groups` — see `cora annotate-groups --help` for the supported inputs and scope.
- `debt-scan` — see `cora debt-scan --help` for the supported inputs and scope.
- `verify-debt` — see `cora verify-debt --help` for the supported inputs and scope.
- `debt-diff` — see `cora debt-diff --help` for the supported inputs and scope.
- `process-list` — see `cora process-list --help` for the supported inputs and scope.
- `process-run` — see `cora process-run --help` for the supported inputs and scope.
- `verify-process` — see `cora verify-process --help` for the supported inputs and scope.

## Controlled maintenance

- `plan-rename-doc` — see `cora plan-rename-doc --help` for the supported inputs and scope.
- `apply-rename-doc` — see `cora apply-rename-doc --help` for the supported inputs and scope.
- `guard-install` — see `cora guard-install --help` for the supported inputs and scope.
- `guard-check` — see `cora guard-check --help` for the supported inputs and scope.

## AI agent and contextual governance

- `dev-premerge` — see `cora dev-premerge --help` for the supported inputs and scope.
- `dev-postmerge` — see `cora dev-postmerge --help` for the supported inputs and scope.
- `verify-dev-gate` — see `cora verify-dev-gate --help` for the supported inputs and scope.
- `agent-check` — see `cora agent-check --help` for the supported inputs and scope.
- `dod-plan` — see `cora dod-plan --help` for the supported inputs and scope.
- `dod-assess` — see `cora dod-assess --help` for the supported inputs and scope.
- `verify-dod` — see `cora verify-dod --help` for the supported inputs and scope.
- `convergence-plan` — see `cora convergence-plan --help` for the supported inputs and scope.
- `verify-contextual-gate` — see `cora verify-contextual-gate --help` for the supported inputs and scope.
- `gold-plan` — see `cora gold-plan --help` for the supported inputs and scope.
- `gold-pilot` — see `cora gold-pilot --help` for the supported inputs and scope.
- `gold-mutate` — see `cora gold-mutate --help` for the supported inputs and scope.
- `gold-effects` — see `cora gold-effects --help` for the supported inputs and scope.

## ZIP and optional runtime

- `zip-intake` — see `cora zip-intake --help` for the supported inputs and scope.
- `verify-zip-intake` — see `cora verify-zip-intake --help` for the supported inputs and scope.
- `runtime-observe` — see `cora runtime-observe --help` for the supported inputs and scope.
- `fuse-evidence` — see `cora fuse-evidence --help` for the supported inputs and scope.
- `verify-fusion` — see `cora verify-fusion --help` for the supported inputs and scope.
- `lattice-audit` — see `cora lattice-audit --help` for the supported inputs and scope.
- `verify-lattice` — see `cora verify-lattice --help` for the supported inputs and scope.

## Synthetic finite models

- `stress` — see `cora stress --help` for the supported inputs and scope.
- `stress-evidence` — see `cora stress-evidence --help` for the supported inputs and scope.
- `stress-graph` — see `cora stress-graph --help` for the supported inputs and scope.
- `stress-adapters` — see `cora stress-adapters --help` for the supported inputs and scope.
- `stress-closure` — see `cora stress-closure --help` for the supported inputs and scope.
- `stress-transform` — see `cora stress-transform --help` for the supported inputs and scope.
- `stress-file-lab` — see `cora stress-file-lab --help` for the supported inputs and scope.
- `stress-artifact-semantics` — see `cora stress-artifact-semantics --help` for the supported inputs and scope.
- `stress-selection` — see `cora stress-selection --help` for the supported inputs and scope.
- `stress-archaeology` — see `cora stress-archaeology --help` for the supported inputs and scope.
- `stress-debt` — see `cora stress-debt --help` for the supported inputs and scope.
- `stress-continuous` — see `cora stress-continuous --help` for the supported inputs and scope.
- `stress-agent-dod` — see `cora stress-agent-dod --help` for the supported inputs and scope.
- `stress-gold` — see `cora stress-gold --help` for the supported inputs and scope.
- `stress-convergence` — see `cora stress-convergence --help` for the supported inputs and scope.

## Evidence-oriented examples

Source-bound source snapshot: `cora snapshot TARGET --revision HEAD --output REPORT`, then `cora verify-ledger REPORT --repo TARGET`.

Contextual premerge: `cora dev-premerge TARGET --base BASE_SHA --head HEAD_SHA --contextual --intent "The bounded change and acceptance criteria" --convergence-contract /path/to/cora/.cora/contracts/dod/convergence-dod.json --output REPORT`.

Replay with **the same intent**: `cora verify-contextual-gate REPORT --repo TARGET --intent "The bounded change and acceptance criteria" --convergence-contract /path/to/cora/.cora/contracts/dod/convergence-dod.json`.

A target must have its own committed ontology and BASE-committed continuous policy for a complete contextual review. An absent intent is debt-blocked. Real tests, security scanners, reviewers and hosting controls remain independently governed. The README intentionally explains product value, rather than listing every command.

## Integrated semantic service (same 71 CLI commands)

`cora method-synthesize . --integrated --revision HEAD --output /tmp/cora-case.json --ai-request-output /tmp/cora-ai-request.json` correlates the **original method-synthesis receipts** with the committed documentation registry, 18 claim/evidence traces, the typed atlas and the reticular source/external gate. Replay using `cora verify-method-synthesis /tmp/cora-case.json --repo . --integrated`. To re-ingest an external AI response, pass `--ai-observations /tmp/response.json` to both synthesis and replay; observations must match the original source commit and case digest and always remain UNVERIFIED. The command does not contact an LLM or export repository bytes to one. Passing `--integrated` does not execute 71 target behaviors.

`cora stress-convergence --integrated --require-full --output /tmp/cora-stress.json` exercises **10 million seeded finite semantic cases** spanning 32 explicitly bounded scenario families and positive controls. It performs zero physical target mutations. The unmodified `stress-convergence` behavior and all existing CLI commands remain available.


## Five synergic goals — one existing CORA service

No new CLI command is required. From a full CORA Git checkout:

```sh
BASE=$(git rev-parse HEAD^)
cora method-synthesize . --synergic --revision HEAD --base-sha "$BASE" --execute-source-probes --output /tmp/cora-five.json --ai-request-output /tmp/cora-five-ai.json
cora verify-method-synthesis /tmp/cora-five.json --repo . --synergic
cora stress-convergence --synergic --repo . --revision HEAD --sessions 10 --cases-per-session 100000 --require-full --output /tmp/cora-five-mutations.json
```

The five-goal report binds the original 18 README claim/source/test traces, opt-in no-target-execution Git source probes, a safe AI case with support/counterexample rules, BASE-policy premerge document/change impact, and the exact 29-node reticulum. No provider connection is made. A model can be invoked explicitly only through a caller-owned `invoke_reasoner(case, truth, provider_callback, authorize=True)` adapter; tests use a fake provider and never attest a live LLM. The model answer must carry the original commit/case digest, cited source refs, disjoint support/counterexample refs, adversarial scenario, positive control and an allowed review-only action. The operator remains responsible for outbound provider security.

`--execute-source-probes` runs **three safe CORA source operations** (Git snapshot, original method-synthesis replay and integrated report replay). It does not execute arbitrary target code, attest a deployed application or test all 71 behaviors. Without the flag, behavior remains NOT_RUN. The preseeded million-case stress suite is a deterministic **finite semantic model** (two positive controls and thirty negative fault classes repeated); **zero physical code mutations** are performed by that stress command. Original physical Git mutants are in the separate source test suite. `G_GOVERNED` is always `BLOCKED_EXTERNAL` until independently observed.

<a id="unified-maturity-and-html-atlas-pr31"></a>
## Unified maturity and HTML atlas

The canonical original-owner command is `cora method-synthesize REPO --synergic`, not a new parallel scanner. Use `--base-sha SHA` to include source-diff context; `--atlas-html PATH` writes a self-contained responsive offline HTML atlas and `--atlas-json PATH` writes the exact-commit machine-readable version. `--ai-request-output PATH` remains a source-grounded AI question plan, **not a provider invocation**. Supply `--output PATH` for the original unified source report, then replay with `cora verify-method-synthesis REPORT --repo REPO --synergic --atlas-json PATH --atlas-html PATH`.

The atlas maps all **71 declared commands** to original source and test file witnesses, eight families, 14 method owners, workflow/document/test inventories and the [six-gate maturity DoD](../.cora/contracts/dod/maturity-dod.json). It is a Git source viewer: test paths are not test execution, independently demonstrated usability or an authorization decision. The release, host, human reviewer, maintained target and longitudinal gates remain `BLOCKED_EXTERNAL`. Report output must live outside the checkout. The CLI does **not** execute target tests or AI automatically.

<a id="one-run-assurance-one-existing-command-executed-results-pr36"></a>
## One-Run execution and result interpretation

From a complete authorized CORA Git checkout, generate one **actual execution dossier**, not merely the 71-command index:

```bash
cora process-run . --revision HEAD --process full --one-run \
  --output /tmp/cora-one-run.json \
  --atlas-html /tmp/cora-one-run.html --atlas-json /tmp/cora-one-run-machine.json
cora verify-process /tmp/cora-one-run.json --repo . --one-run \
  --atlas-html /tmp/cora-one-run.html --atlas-json /tmp/cora-one-run-machine.json
```

The existing `process-run` runs or reuses eight safe source methods, **not** every one of the 71 declared CLI commands. In one-run mode it records each method as `EXECUTED_SCOPED`, `REUSED_SCOPED`, `BLOCKED` or `NOT_RUN`, with a measured duration or an explicit shared-reuse/unmeasured reason; unsafe actions remain `NOT_RUN`. The original PR31 71-command catalog and six maturity gates remain available underneath the visible execution summary. JSON and HTML are derived from the same receipt and compared against original Git source; **timing and optional runtime exits are not independently attestable by source replay**.

To explicitly execute CORA's own Python unittest suite on an exact CORA checkout, add `--execute-self-tests --test-timeout 240`; this executes local code and must never be used on untrusted code or without authorization. Its result remains `RUN_REPORTED_UNATTESTED` on exit zero and requires an independent test operator. The command never starts arbitrary provider/LLM calls, external network scanners, Docker, target repository tests, transforms, merge or release.

Physical committed DoD mutants and other anti-tamper tests are in `tests/test_pr36_one_run.py`. The separate `python -m cora.one_run_stress --cases 100000 --seed 883 --output /tmp/cora-one-run-100k.json` command performs deterministic **preseeded finite-model semantic mutations of the *receipt grammar***, not 100,000 real source changes. The 32 families include 30 negative cases and 2 positive controls; CI runs the campaign twice and compares full output bytes. See [the DoD and metrics](../.cora/contracts/dod/one-run-dod.json) and [implementation guidance](CONTINUOUS_DEVELOPMENT.md).

The same **one-run** command can add `--model-stress-cases 100000` to run and display the preseeded semantic receipt benchmark inside the HTML execution results. The report and the replay then verify the 100k model digest and 32 fault-family counts. This opt-in is safe model testing, not external application testing or 100k real Git mutations.

<a id="integrated-one-run-source-candidate-pr37"></a>
## Comprehensive One-Run source dossier

`cora process-run . --revision HEAD --process full --one-run --profile comprehensive --output /tmp/cora-run.json --atlas-html /tmp/cora-run.html --evidence-dir /tmp/cora-evidence` extends the existing PR36 command; no second orchestrator or CLI entry is created. The integrated JSON/HTML reports every discovered activity, including tests, tools, workflow calls and 71 declared parser commands, but only the eight bounded source methods are eligible to run by default. It records why every other activity is NOT_RUN, BLOCKED or unobserved. Verify original-Git portions and evidence bytes with `cora verify-process /tmp/cora-run.json --repo . --one-run --atlas-html /tmp/cora-run.html --evidence-dir /tmp/cora-evidence`. Optional local unittest subprocesses require both `--execute-self-tests` and an `--authorization-file` containing schema `cora-explicit-execution-consent/1`, exact commit, tree, operation `CORA_LOCAL_SELF_TESTS`, and absolute checkout path. No self-issued consent authenticates the user, provisions a sandbox, attests the runtime or authorizes a release. The integrated [source/EXTERNAL DoD](../.cora/contracts/dod/integrated-one-run-dod.json) is a source candidate with open gates.

<a id="pr38-historical-and-adaptive-evidence-in-the-existing-one-run-atlante"></a>
## Git history and adaptive obligations in One-Run

`cora process-run . --revision HEAD --process full --one-run --profile comprehensive --output /tmp/run.json --atlas-html /tmp/atlas.html --evidence-dir /tmp/evidence` now includes the original-Git genealogy when the inspected commit contains the [PR1–37 history corpus](../.cora/assurance/history/pr01-37-commit-diff-audit.json). It navigates 37 PRs, 305 commit deltas, the unmerged PR34 exception, 28 old/relocated paths and future feature-registration obligations. `cora verify-process /tmp/run.json --repo . --one-run --atlas-html /tmp/atlas.html --evidence-dir /tmp/evidence` rechecks the genealogy against committed Git and verifies content-addressed evidence including genealogy.json. Existing PR37 receipts at older Git revisions remain in their original provenance scope. This capability neither executes every catalogued command nor certifies a removed source module as safe to delete. See the [PR38 source/external DoD](../.cora/contracts/dod/history-convergence-dod.json).


<a id="pr39-source-reference-and-host-readback-auxiliary-tools-not-new-cli-commands"></a>
## Native Git oracle and optional host readback

The existing cora process-run . --revision HEAD --process full --one-run --profile comprehensive --output /tmp/run.json --atlas-html /tmp/atlas.html --evidence-dir /tmp/evidence attaches a read-only qualification receipt when the candidate Git commit has the PR39 contract. Verify it using cora verify-process /tmp/run.json --repo . --one-run --atlas-html /tmp/atlas.html --evidence-dir /tmp/evidence. The evidence manifest includes qualification.json with four BLOCKED_EXTERNAL product gates.

Independent-implementation source comparison: python tools/independent_git_oracle.py --output /tmp/native-reference.json. Host observation, with an optional environment-scoped read-only GITHUB_TOKEN: python tools/governance_readback.py --repo Luke883i/cora --branch main --output /tmp/host.json. Both require explicit separate invocation. Neither authenticates external witnesses or grants a release. See [product qualification acceptance](../.cora/contracts/dod/independent-qualification-dod.json) and [operator protocol](RELEASE.md).

## ChatGPT session continuity: one portable iteration per One-Run invocation

`process-run` has two optional paired flags for `--one-run --profile comprehensive`: `--chat-step STEP.json` (caller-authored, strict JSON) and `--chat-bundle PATH.zip` (outside the inspected Git checkout). It runs the existing source methods, writes the usual One-Run receipt and atomically appends an iteration to a portable ZIP. `verify-process --one-run --chat-bundle PATH.zip` checks both exact Git source replay and the ZIP's latest receipt/hash-chain agreement.

Use [the full novice walkthrough](GETTING_STARTED.md) and [the example step](../examples/chat-step.example.json). The required step keys are `schema`, `session_id`, `iteration`, `intent`, `actions`, `roadmap`, `falsifiers`, `dod`, `gaps`, `next_step`. Roadmap entries must reference falsifiers and DoD nodes; unresolved leaf obligations must have explicitly linked gaps. The DoD is topologically ordered using CORA's existing reticular kernel and conservatively assessed; caller evidence never authenticates runtime, reviewer identity, merge or release.

ZIP layout: `meta/session.json`, followed by `rounds/000001/{step.json,receipt.json,dod.json,handoff.md,manifest.json}`, `rounds/000002/...` and so on. Each manifest hashes its own round content and links the previous round's manifest SHA-256. The archive is logically append-only, with a bounded size/round count, duplicate-name and path checks, no implicit execution of its contents and an exclusive writer lock. It is **not** a WORM store or digital signature: a malicious holder can rebuild the chain unless the previous manifest digest is retained independently.

CORA cannot automatically observe every ChatGPT message. No assistant should claim that a round was recorded if the host never ran the command.


#<a id="pr52-native-gold-receipts-in-existing-one-run"></a>
## Optional native Gold receipts

With explicit permission, generate one original target native execution receipt outside the target using cora.native_gold.capture_native. Then pass --portable-native-probe PATH to the existing process-run --one-run --portable-profile PROFILE-v2.json; verify-process uses the same flag for exact Git and retained-byte replay. This is a local subprocess outcome, not authenticated host identity, independent browser/remote proof or release approval. See GOLD_ASSURANCE.md PR52.
