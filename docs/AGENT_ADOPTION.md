# Adopt CORA in an AI coding workflow

CORA **governs evidence and review** for a coding assistant; it does not write product code or authorize merging. A GitHub URL is a reading location, not an installation or a protected policy. Start with the [product README](../README.md), [agent rules](../AGENTS.md) and [method](AI_CODE_ASSURANCE.md).

## 1. Prepare the two repositories

Give the assistant access to a local CORA installation and a separate **target** checkout. Install CORA from an authorized clone using Python 3.11+:

```sh
python -m pip install -e /path/to/cora
cora --help
```

In the target, establish its *own* committed `cora.ontology.json`. Contextual pre/postmerge additionally requires a `.cora/continuous-policy.json` present in the trusted **BASE** revision. Its absence requires a separate human bootstrap decision; a candidate PR cannot approve its own policy. Review the [architecture](ARCHITECTURE.md) and [continuous method](CONTINUOUS_DEVELOPMENT.md). Do not overwrite the target's product and software identities with CORA's self-ontology.

## 2. Record the real engineering intent

The agent identifies the product outcome, independent acceptance oracle, impacted owners and consumers, and real BASE/HEAD commits. The exact change intent is supplied as text; CORA binds it to the source revision but does **not** authenticate its human author. Run the source/complete DoD plan:

```sh
cora convergence-plan --contract /path/to/cora/.cora/contracts/dod/convergence-dod.json
```

## 3. Execute an opt-in contextual source gate

After the target change is committed, replace the placeholders with real revisions. This is a source-only review workflow, not an implicit test runner or CI endorsement.

```sh
cora dev-premerge /path/to/target --base BASE_SHA --head PR_HEAD_SHA \
  --contextual --intent "Ship the stated change with its named acceptance tests" \
  --convergence-contract /path/to/cora/.cora/contracts/dod/convergence-dod.json \
  --output /tmp/cora-premerge.json

cora verify-contextual-gate /tmp/cora-premerge.json --repo /path/to/target \
  --intent "Ship the stated change with its named acceptance tests" \
  --convergence-contract /path/to/cora/.cora/contracts/dod/convergence-dod.json
```

The same intent is required at replay. Missing intent produces `DEBT_BLOCKED`. A valid source report may still require review; dynamic consumers, behavioral tests and trusted side-effect readback remain separate obligations. `--strict` intentionally rejects unresolved conditions rather than turning them into approvals.

## 4. Complete real tests and review outside the receipt

Run the target project's real unit/integration tests and, only when authorized, concrete source mutators and relevant isolated runtime tests with independent oracles. Record SHA, environment, commands, coverage gaps, failed and surviving mutants. Do not present a deterministic 10-million-case finite model as 10 million source mutations or product behavioral passes.

Open the PR with the reports and unresolved blockers. Hosting administrators must independently enforce required checks and non-author approval. CORA does not configure those permissions.

## 5. Observe the actual merged revision

After a separately authorized merge, run `cora dev-postmerge TARGET --previous REAL_PREMERGE_MAIN --head ACTUAL_MERGED_MAIN --contextual --intent SAME_INTENT --convergence-contract PATH` and replay its receipt with `verify-contextual-gate`. A former PR-head green result is not a postmerge witness.

## Stopping conditions

Stop claims of acceptance when the target ontology is missing, ownership is ambiguous, the Git source or change intent cannot be reproduced, tests have no independent oracle, or effective permissions and reviewers are not attested. The full R1–R4 and governed roots remain blocked until real external witnesses converge. See [full R1–R4 DoD](DOD_PR20_CONVERGENCE.md) and [documentation DoD](DOCUMENTATION_DOD.md).

## Portable ChatGPT handoff (opt-in)

When using CORA in a chat-assisted workflow, distinguish the conversation's proposed actions from actual source evidence. Prepare a strict iteration JSON from `examples/chat-step.example.json`, execute **the same** `cora process-run --one-run --profile comprehensive` with `--chat-step` and `--chat-bundle`, then verify with `cora verify-process --one-run --chat-bundle`. Upload or transfer the ZIP to the next chat, read the latest `handoff.md`, and repeat with the next sequence number. Never claim automatic per-turn capture, external authorization, a genuine test execution, or chat-history completeness. See [Getting started](GETTING_STARTED.md).

