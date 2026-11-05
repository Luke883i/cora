# CORA contextual gold assurance — user and coding-agent method

This is one **existing CORA product**, not a second AI coding assistant or authority. R1 contextual DoD, R2 physical mutation, R3 effect observation and R4 three-source pilot are distinct from external host/release validation.

## Portable origins and adaptation
| Patterns | Origin (sampled PR) | CORA adoption |
| --- | --- | --- |
| P01–P04 intent-to-proof, owner/subsumption, retrograde DoD, minimal slice | ICTC #212; ikant G1; iKant_EDU #190/#200 | R1 `gold-plan`, requirement and Git source binding; owner semantics still need review |
| P05–P07 physical mutants, adaptive saturation, same-state control | ICTC #232; ikant #193 | R2 `gold-mutate`, `stress-gold`; syntax vs target runtime explicitly distinct |
| P08–P10 persisted readback, CI side effects, execution grades | aosp1 #3816/#3865; Juriscribe #33 | R3 `gold-effects`; effect execution and host verification stay unknown |
| P11–P12 user journey and cross-repository lineage | Teddy #54; LUMEN #22; CIE #17; ROA/academics | R4 pinned readback, *not* genuine cross-repo E2E |

## Operational lifecycle
INTENT → OBSERVE → QUALIFY → SLICE → MATERIALIZE → WITNESS → CLOSE → ACT. Start with a human intent and pinned BASE. `cora gold-plan --intent 'Deliver observable scoped behavior'` shows the non-compensatory source and governed cuts. `gold-pilot --ictc-root ROOT --ikant-root ROOT --aosp1-root ROOT` requires local checkouts on exact committed SHA and compares six Git blob hashes and literal anchors. No network or target code executes. Use `dev-premerge` and `dev-postmerge` for lifecycle gates on their actual revisions, not a simulated Git clone.

`gold-mutate ROOT PLAN.json` stages only bounded regular files, checks source anchors, writes a physical byte delta and runs an independent selected oracle. A `PYTHON_AST` oracle detects **syntax only**; survivors are not kills. A `DOCKER_TEST` oracle requires explicit `--authorize-docker`, a preinstalled allowlisted image and bounded arguments; no automatic network, target code or release. Docker isolation is not independently attested. Outcome counts: killed/survived/timeout/inconclusive. An unproven baseline blocks classification.

`gold-effects workflow.yml --revision EXACT_SHA` identifies *possible* permission/action/script effects conservatively and never treats self-reported readback as authentication. Unknown YAML semantics must be reviewed by the hosting owner.

`stress-gold --require-full` runs 10 fixed seeds × 1M **synthetic typed fault scenarios**. The 12 prespecified failure families yield 12 observed singles and all 66 pairs per session, an actual-mask novelty tail, finite reference oracle and stream SHA-256. Two full runs must compare byte-for-byte. This does **not** run 10M physical source changes, LLM completions or real target oracles.

## Pilot anchors and unsupported conclusions
ICTC `56362f1b`: `docs/authority-matrix.yaml` plus `v3/release-readiness-e2-product-mutants.mjs`. ikant `43ce861a`: `CONTROL_PLANE_OWNERSHIP_CONTRACT.json` plus `ikant/control_plane_ownership.py`. aosp1 `8af1c0cc`: `authority-matrix.yaml` plus `frontend/src/apps/DataIntake/lib/d1PersistedReadback.ts`. Full 40-digit source revisions and Git blob hashes are in `.cora/contracts/dod/gold-assurance.json`. This sample is read-only source lineage, *not* an independent audit of their running products or current HEADs.

Remaining unknowns: genuine owner/consumer equivalence, real external behavioral mutators, trusted host CI effect readback, sandbox attestation, actual target runtime, reviewer identity, rollback and release authority. **All remain BLOCKED_EXTERNAL or NOT_EXECUTED, never inferred from model success.**

## PR-19 receipt and image-pinning hardening

A supplied `--pilot-report` is a claim, **never** authenticated source observation. `gold-plan --ictc-root ... --ikant-root ... --aosp1-root ...` performs a fresh Git-object readback in the same operation and marks owner semantics still unverified. Explicit Docker execution requires a **preloaded digest-pinned image** of form `python@sha256:HEX64` or `node@sha256:HEX64`, with no image pull, network or privileged capabilities. This reduces source/image substitution risk but does not provide independently certified sandbox isolation.

## Private-source access is a separate authority

PR-19 initially attempted three GitHub Actions checkouts: CORA and public ICTC succeeded, then the checkout of private ikant failed, and aosp1 was never attempted. The CORA workflow token is not a read credential for other private repositories. Never inject broad private tokens into PR-controlled workflows to change a red access gate to green. The hardened CI verifies **real frozen ICTC Git object bytes (1/3)**, runs `gold-pilot` with a deliberately missing private checkout, requires its exit status 2 and records both absent private repositories as `NOT_OBSERVED` / `BLOCKED_INCOMPLETE`. This green boundary check does **not** establish 3/3 evidence. A trusted maintainer may independently provide approved local checkouts of all three pinned commits to `gold-pilot` outside PR-controlled CI. See [closure audit](archive/audits/AUDIT_PR19_CLOSURE.md).

## Docker optional oracle and filesystem permissions

The initial Docker oracle forced user 65534 but the private temporary source root is 0700, commonly preventing traversals. The hardened implementation runs only for a non-root host user and uses that UID/GID for the container without making the temporary workspace world-readable. The image remains digest-pinned and no network or image pull is allowed. Tests falsify root-host execution, missing opt-in and unpinned images using mocked Docker calls; actual sandbox security and host portability are not attested.
