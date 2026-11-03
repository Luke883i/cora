# PR-17 — AI agent semantic DoD, backward derived

## Global goal

Desired result: an agent receives an explicit human engineering intent, locates product/software/repository owners, derives necessary prerequisites backwards, proposes one minimal material implementation, falsifies it against relevant mechanisms, and presents exact-revision witnesses while refusing to self-approve. G_SOURCE_AGENT = I_LOCAL AND I_INTERMEDIATE AND I_GLOBAL. G_GOVERNED_AGENT = G_SOURCE_AGENT AND I_EXTERNAL. Both are non-compensatory AND nodes. External release authority is never concluded from this local model.

## Intermediate and local lattice

The machine-readable source of obligation IDs, edges and nearest falsifiers is cora.agent-dod.json. I_LOCAL requires L01-L06 (product/source identity and basic evidence); I_INTERMEDIATE requires L07-L12 (materiality, independent oracles, runtime and provenance discipline); I_GLOBAL requires L13-L18 (Git BASE/HEAD, policy integrity, completeness, CI, regressions and postmerge); I_EXTERNAL requires L19-L24 (protected hosting, independent reviewer, isolated execution, pilots, rollback and release). Removing, duplicating or reclassifying an obligation must fail the static validator.

| Gate | Condition | Falsification |
| --- | --- | --- |
| D1 — Source taxonomy | Exactly 24 local families, 4 intermediates, 2 global goals, ten distinct seeds, fixed authority | policy file mutant, missing edge, duplicate, changed source/external scope |
| D2 — Retrograde | G_SOURCE derives exactly 18 local leaves; G_GOVERNED 24; topological order and nearest falsifier | wrong link, changed goal, absent leaf |
| D3 — Evidence | self-reported PASS stays MODEL_ELIGIBLE_UNATTESTED; complete governed claims stay BLOCKED_EXTERNAL | missing witness, wrong SHA, tampered digest, forged authorization |
| D4 — Physical mutation | 24 family policy JSON mutants and 10 structural/authority mutants rejected | actual temporary file rewrites under unittest, not production target mutants |
| D5 — Campaign | 10 preseeded sessions x 1M calls; all 24 singles and 276 pairs per session; no oracle mismatches, no unsafe promotions, zero novel signatures in last 100k | two byte-identical full receipts; failed campaign must not PASS |
| D6 — Source DevOps | single CLI, repository contract + roles, Python 3.11/3.13, existing regressions, CI pinned to exact PR HEAD | GitHub check run and explicit HEAD equality |
| D7 — External governance | real independent review/host enforcement/runtime pilot/rollback | not self-attestable; remain BLOCKED_EXTERNAL |

Global source CI = D1 AND D2 AND D3 AND D4 AND D5 AND D6, with pass only within the tested scope and exact commit. Global governed = source CI AND D7. Machine-readable scenario coverage is not operational code coverage, a physically mutated contract is not a physically mutated product implementation, and a digest is not a signature. No automated deletion, deployment or release authorization is allowed.

## Evidence and invalidation

Evidence is invalid when commit SHA, contract, command environment, oracle, test harness or runtime source changes. A model receipt is replayable only against its pinned inputs. CI must run the full 10M in a separate job twice and require exact JSON byte equality. After merge a new main SHA requires a separate post-merge review. No model-score averaging, self-issued waiver or deployment authority.

## Accepted results

A mechanically demonstrated candidate source DoD may be PASS_SCOPED only after final-head GitHub workflows independently complete with success. Even then: protected main, non-author review, verified sandbox, real maintained-repository pilot and rollback remain external requirements. See AI_CODE_ASSURANCE.md for the DevOps moments and usage.
