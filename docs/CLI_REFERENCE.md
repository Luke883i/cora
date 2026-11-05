# CORA CLI reference — current parser inventory

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
