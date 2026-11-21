# Post-PR94 CLI behavioral closure — scoped evidence, not product acceptance

Baseline: `Luke883i/cora` merged main `dbff5f12ba996cfcdaef35c3016c47c6ec3805d1`.
Canonical contract: [post94-cli-behavior-dod.json](../.cora/contracts/dod/post94-cli-behavior-dod.json).
Native owner fixtures: [test_post94_remaining20.py](../tests/test_post94_remaining20.py).

## Abstract DoD and backward chain

A capability is complete iff an intended result is observed on an identified source and target,
a separately specified expected counterexample is detected, effects are bounded and permitted,
and all required source/runtime/external AND leaves are closed. A successful parser help
is not a product test. A finite model is not a physical target mutation. A version probe of
a third-party binary is not a scanner or an autonomous coding agent run.

`G_71_CAPABILITY_ACCEPTED = AND(G_20_SCOPED_CHARACTERIZED, I_PRIOR_51,
I_PROCESS_INTEGRATION, E_TARGET_HOST, E_REVIEW_RELEASE)`.

`G_20_SCOPED_CHARACTERIZED = AND(I_NEW_20, I_SOURCE_IDENTITY)`,
where `I_NEW_20` requires each of the 20 command-specific local leaves.
The prior 51 are not promoted merely by the new 20 reaching local source scope.
An externally accepted release is neither implied nor authorized by either goal.

## Execute the finite native slice on the exact source

```sh
PYTHONPATH=src python -m pytest -q tests/test_post94_remaining20.py
PYTHONPATH=src python -m cora.cli process-list --intent 'source analysis'
```

Tests use fresh, disposable Git repositories and ZIP files. They run 20 CLI routes
with positive results, explicitly typed refusals and replay. No external network,
third-party scanner, arbitrary LLM, host approval or Docker target code is invoked.
`gold-pilot` must remain `BLOCKED_INCOMPLETE` without three independent pinned
checkouts; `runtime-observe` returns `NOT_REQUESTED` without operator execution consent.
`dod-assess` with missing claims returns a nonzero blocker and `verify-dod`
must still reproduce that source claim accurately. Source-only `gold-mutate` uses
a Python AST falsifier on a fresh staged copy. The target source remains unchanged.

The stress cases are deliberately short and must return `PARTIAL_NOT_10M` or
another explicit finite result, never claim 10M cases, real repositories or
cross-host safety from a small sample.

## Separate acceptance leaves

- **SOURCE:** Git parent/tree/blob readback, 71 CLI catalog identities, exact native test owner.
- **TARGET_RUNTIME:** positive/negative owner-native behavior on an authorized maintained target; source fixtures do not satisfy this globally.
- **EXTERNAL:** independent reviewer, release operator, private access and host/environment assurance remain external decisions.
- **ROLLOUT:** rollback by reverting three semantic commits in reverse order. No deletion or source replacement based solely on static-use signals.

A green source CI means `PASS_SCOPED` for the tested SHA, never `G_71_CAPABILITY_ACCEPTED`.
