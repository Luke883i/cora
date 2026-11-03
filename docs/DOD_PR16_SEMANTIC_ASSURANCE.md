# PR-16 — Challenging semantic DoD: C5 to C9

Baseline: `main@078a794504aab549458b5940d780e2e50c21926e`. Scope: experimental PR-16 branch, no signed release or independent sandbox assurance. Every PASS requires a witness on the exact final SHA. Commit stages implement requirements; they do not automatically prove them.

## Global gate lattice (AND; never average)

`G_source = C5 AND C6_source AND C7_source AND C8_source AND C9_source`.
`G_observed = G_source AND C6_runtime AND C7_runtime`.
`G_governed = G_observed AND C9_independent`.

Missing evidence is BLOCKED, a counterexample is REFUTED, and verified narrowly scoped behavior is PASS_SCOPED. NOT_EXECUTED is not a PASS. No local receipt, CI check or AI confidence yields merge/deletion/release authority. The runtime branch is optional for source-only assurance, mandatory for any observed-runtime claim.

| Gate | Local requirements | Falsification oracle | Pending external proof |
| --- | --- | --- | --- |
| C5 Contracts | All new CLI commands documented; architecture matches code; roles cover added artifacts; distinct product/software/repo/executor | repository-contract and role verifiers, README/CLI mutation | independent novice walkthrough |
| C6_source | ZIP bounds, traversal/symlink/collision/bomb rejection, exact tree digest, no implicit execution and no invented Git ancestry | hostile ZIP fixtures, altered receipt tests | author authenticated Git object provenance |
| C6_runtime | explicit opt-in; pinned image; no arbitrary shell; network off; read-only source; non-root, bounded logs and timeout cleanup; execution identified | runtime test fixtures, bounded output/timeout failures | sandbox and Docker host independently attested |
| C7_source | typed DAG obligations, dependencies, source/observation distinctions, unknown propagation, no forged digest escalation | mutation, missing proof, cycles, wrong source, fake approval | independent oracle validity |
| C7_runtime | ZIP/tree and runtime receipt identity match; no unsupported fusion of Git history | cross-source mismatch fixture, read-only replay | real external runtime witness |
| C8 Regression | differential Git blob oracle, bounded Git process count, full tests on Python 3.11/3.13, recorded baseline and measured coverage | regression, mutation and benchmark with workload identity | independent maintained-repository pilot |
| C9_source | coherent PR with semantic commits, source/CI checks against exact final HEAD, all blockers recorded | GitHub check runs and PR changed file audit | none needed to observe CI result |
| C9_independent | protected main, required checks, non-author review, incident/recovery and rollback evidence | authenticated hosting and reviewer identity | **OPEN** |

## Counterexample constraints

1. A source receipt digest can be recomputed but cannot authenticate a claimed real-world event.
2. ZIP identity does not confer Git commit history or author verification.
3. `RUN_REPORTED_UNATTESTED` and Docker exit code 0 cannot attest isolation, coverage, or independent execution.
4. Source and runtime inputs with different archive/tree identities are not composable.
5. A missing node, expired/wrong-revision witness, dependency cycle, or unsupported status must fail closed.
6. A premerge green workflow or policy changed by the PR cannot elevate to authorization.
7. Earlier experiment metrics (244 tests, ~85% coverage, 3,245 subprocess) are historical, not fresh measurements.

## Acceptance and prohibition

A PR is *mechanically reviewable* when C5, C6_source, C7_source, C8 and C9_source have reproducible final-head witnesses, and C6_runtime/C7_runtime remain correctly BLOCKED without trusted external observations. `G_governed` is **BLOCKED_EXTERNAL** until platform protection and independent evidence are attached. No automatic deletion, code release, or sandbox safety conclusion is permitted.
