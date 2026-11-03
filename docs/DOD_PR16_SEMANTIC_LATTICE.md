# PR-16 semantic assurance lattice — falsifiable DoD

**Scope:** candidate branch only; source assurance is not independent sandbox, merge, or release permission. Every status is SHA-scoped and may be invalidated by a changed input or implementation.

## Global obligations, non-compensatory

`G_SOURCE := C5 AND C6 AND C7 AND C8 AND C9_SOURCE_CI`, where each term must have a reproducible witness on the **same final HEAD**. `G_GOVERNED := G_SOURCE AND EXTERNAL_HOSTING AND INDEPENDENT_REVIEW AND REAL_PILOT`; absent authentic external witnesses, `G_GOVERNED = BLOCKED_EXTERNAL` regardless of a green CI.

| Gate | Intermediate DoD | Local witness and negative oracle | Forbidden promotion |
| --- | --- | --- | --- |
| C5 contract closure | Document new CLI; map source roles, architecture and agent boundary | README command check; repository/role verifier | New CLI must not be undocumented |
| C6 hostile input and runtime | ZIP traversal/collision/symlink/bombs rejected; opt-in execution; runtime receipts bounded and fail-closed | `test_pr16_zip_intake.py`; `test_pr16_runtime_fusion.py` | Docker flags are not sandbox proof |
| C7 lattice semantics | Cross-receipt equality, status distinction, machine-replay, dependency failure and no authorization escalation | Independent adversarial `test_pr16_lattice.py` and typed `semantic_lattice.py` | Digest is not signature; mocked success is not actual execution |
| C8 bounded performance and regression | Git objects batch-read with ≤5 Git subprocesses for 104-path fixture; differential oracle and entire regression on CI | `test_pr16_git_batch.py`, main unit suite, deterministic measured counters | Synthetic ratio not general performance guarantee |
| C9 CI and PR closure | Source checks on head in Python 3.11 and 3.13; real GitHub PR and per-job conclusions independently inspected | `ci-semantic-lattice.yml` on PR and push; GitHub check-runs on exact SHA | Existence of workflow ≠ required check; PR ≠ reviewer approval |

## Evidence classification and dependencies

`G0 = INPUT_ADMISSIBLE` needs matching archive bytes and verified content-tree claim; a caller-provided tree is not an authenticated commit. `G1 = RUNTIME_OBSERVED_UNATTESTED` requires explicit execution and consistent source identity; a missing executor remains BLOCKED, not PASS. `G2 = RECEIPTS_RECONCILED` requires matching source hashes and replay, preserving `runtime_coverage=NOT_ATTESTED` and `authorization=NONE`. `G3 = BLOCKED_EXTERNAL` until independently protected GitHub controls, a non-author reviewer, externally verified sandbox and a real maintained-repository pilot exist. An optional runtime request is **not** a prerequisite for safe source-only audit.

DoD proof objects must record method, input commitment, status, unknowns, contradictory observations, witness and invalidation scope. Report verification by recomputation is not independent semantic correctness. Forbidden: claims of SLSA compliance, CI required-check enforcement, universal dead-code detection, safe auto-deletion, sandbox confinement, CI attestation from self-reported fields or authorized release.

## Acceptance and falsification

A candidate source-DoD PASS is justified only when complete GitHub actions (not just their YAML), exact commit SHAs, full regression, negative fixtures, role and source contracts, a bounded Git performance oracle and receipt-lattice tests are observed. Record each run URL, job conclusion and skipped conditions; skipped is not passing a required check. All claims of independent host enforcement, real-world operational performance and governed release remain **DEBT_BLOCKED** unless proven separately.
