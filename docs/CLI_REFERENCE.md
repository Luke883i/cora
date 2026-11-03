# CORA CLI reference — current parser inventory

This is the complete inventory of the single `cora` CLI from `src/cora/cli.py`, maintained against its real `argparse` parser. Use `cora COMMAND --help` for exact flags and inputs; this is not evidence of test execution or a guarantee of behavioral correctness. Start with [Getting started](GETTING_STARTED.md) or [Agent adoption](AGENT_ADOPTION.md).

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

Contextual premerge: `cora dev-premerge TARGET --base BASE_SHA --head HEAD_SHA --contextual --intent "The bounded change and acceptance criteria" --convergence-contract /path/to/cora/cora.convergence-dod.json --output REPORT`.

Replay with **the same intent**: `cora verify-contextual-gate REPORT --repo TARGET --intent "The bounded change and acceptance criteria" --convergence-contract /path/to/cora/cora.convergence-dod.json`.

A target must have its own committed ontology and BASE-committed continuous policy for a complete contextual review. An absent intent is debt-blocked. Real tests, security scanners, reviewers and hosting controls remain independently governed. The README intentionally explains product value, rather than listing every command.
