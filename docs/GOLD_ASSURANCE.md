# CORA contextual gold assurance — user and coding-agent method

**Document status:** CURRENT
**Current scope:** Current contextual Gold contracts and bounded native pilot observations.
**Operational use:** Join sourced Gold/DoD claims with explicitly authorized native tests.
**Evidence:** Gold source paths, pinned repositories and original runner receipts.
**Limits:** Teddy/ICTC observations do not imply browser, remote or universal acceptance.


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

<a id="pr-19-receipt-and-image-pinning-hardening"></a>
## Pilot-source validation and image-pinning constraints

A supplied `--pilot-report` is a claim, **never** authenticated source observation. `gold-plan --ictc-root ... --ikant-root ... --aosp1-root ...` performs a fresh Git-object readback in the same operation and marks owner semantics still unverified. Explicit Docker execution requires a **preloaded digest-pinned image** of form `python@sha256:HEX64` or `node@sha256:HEX64`, with no image pull, network or privileged capabilities. This reduces source/image substitution risk but does not provide independently certified sandbox isolation.

## Private-source access is a separate authority

The current source-only Gold probe validates **real frozen ICTC Git object bytes (1/3)** and refuses to claim evidence from the private ikant/aosp1 targets: missing authorized checkouts are `NOT_OBSERVED` / `BLOCKED_INCOMPLETE` and the `gold-pilot` exit is 2. Do not give PR-controlled workflows broad private tokens. An authorized independent operator may supply local pinned checkouts; until then 3/3 verification remains unproven.

## Docker optional oracle and filesystem permissions

Optional Docker execution requires a non-root host user and reuses that UID/GID inside the disposable container, without making private source directories world-readable. The image remains digest-pinned and no network or image pull is allowed. Tests falsify root-host execution, missing opt-in and unpinned images using mocked Docker calls; actual sandbox security and host portability are not attested.



<a id="pr51--native-gold-bridge-in-the-existing-portable-one-run"></a>
## Portable Gold claim-to-oracle linkage

**Intent and status:** link a *target-owned* product/source claim to its actual
committed source owner, original native oracle source, named native witness
and exact Git revision, then expose the bounded proof/debt in the same offline
One-Run HTML and JSON. This extends Gold R1–R4 source traceability; **it does
not execute a foreign test, certify an independent issuer, or close S4**.

Use the *existing* `cora process-run TARGET --one-run --portable-profile
/path/target-v2.json --portable-evidence-dir /outside/target/artifacts --output
/out/receipt.json --atlas-html /out/atlas.html`. Omit
`--portable-evidence-dir` to document absent bytes honestly. Replay with
`cora verify-process /out/receipt.json --repo TARGET --one-run
--portable-profile /path/target-v2.json --portable-evidence-dir
/outside/target/artifacts --atlas-html /out/atlas.html`.
The original v1 profiles still work unchanged.

A v2 target-owned profile adds exactly `schema: cora-portable-target/2`,
`goal` and `claims` to the existing v1 keys. Each claim specifies
`id, claim, scope, owner_id, source_path, oracle_id, oracle_path,
oracle_sha256, witness_ids, depends_on`; every path/owner/oracle/witness must
be rooted in the original Git/profile and each retained witness is consumed
by exactly one claim. Scopes are SOURCE, BEHAVIOR and EXTERNAL. Native
witnesses retain portable-profile fields including `reported_outcome`:
`PASS_REPORTED_UNATTESTED`, `FAIL_REPORTED_UNATTESTED`,
`SKIPPED_REPORTED_UNATTESTED`, or `NOT_RUN_REPORTED_UNATTESTED`.
These are caller reports, never independent test verdicts.

**Machine conditions:**

1. **R1 original context:** a tracked regular owner file exists in the exact
   target commit; `oracle_path` is another tracked regular original Git
   blob, and its SHA-256 matches `oracle_sha256`.
2. **R2 falsifier identity:** a noncompensatory, cycle-free and orphan-free
   DAG has a single named goal. An original oracle's *presence* is **not
   execution**; no artificial executed-oracle status is issued.
3. **R3 bounded native witness:** each profile witness is bound to one
   claim, its declared `oracle_id` and Git revision; provided bytes are
   hashed and checked outside the target. Counterevidence, skipped tests,
   missing bytes and tampering have separate failure outcomes.
4. **R4 no authority promotion:** all claim rows carry
   `claim_proven: false`; independent issuer, browser comprehension,
   production deployment, reviewer and release still
   `BLOCKED_EXTERNAL`. `goal_status` is always
   `BLOCKED_INDEPENDENT_ORACLE_EXECUTION_AND_REVIEW`.
5. **Replay and falsification:** same profile, original Git objects,
   retained witness bytes and optional HTML must reproduce exactly.
   The native regression executes two distinct Git fixture targets,
   twenty independent contract mutations, a physical oracle-source
   change, HTML/script injection, byte tamper, FAIL, SKIPPED and NOT_RUN.
6. **Real public pilot:** the *existing* integrated One-Run CI analyzes
   exact historical Teddy and NILO commits, independently hashes each
   repository's native test file and emits a v2 Gold trace. Their native
   test execution remains **NOT_OBSERVED** because the source pilot
   intentionally does not execute them. Separately authorized native Gold
   pilots observe Teddy Node and ICTC HTTP/SQLite; browser and remote controls remain unobserved.

**Nonclaims:** no Gold bridge entry is a valid deletion permission; no
caller-supplied PASS is native behavior proof. SHA-256 alone establishes
byte agreement, not who ran or authorized a test. This feature adds no
new command, repository-local release authority, shadow workflow, target
writer, second Gold bus or network transport. The existing source
reticulum, original process-run and existing Gold R1–R4 remain owners.

**Metrics / DoD:** 100% claims reachable from goal; 100% oracle Git hashes
replayed; 0 orphan/reused witness; 0 false positive native test/host
attestations on the declared adversarial tests; original v1 compatibility;
real pinned Teddy and NILO source readback; exact-head Python 3.11/3.13
One-Run and full CI. External product and efficiency comparisons remain open.



<a id="pr52--native-gold-pilots-and-bounded-cross-repository-result"></a>
## Native Gold pilots and negative execution controls

The portable claim-to-oracle bridge alone does not execute native target code. Explicit opt-in local subprocess execution supports only two original target tests under the existing One-Run and Gold projection, preserving missing or negative evidence as blockers.

**Pilot 1, Teddy:** actual Node24 TAP tests of original CORA JS graph
integration on pinned Git commit 05c31e986d36fb4350867d208c1e4efe7e535ece.
The fixed command is node --no-warnings --experimental-vm-modules --test-reporter=tap --test
tests/cora-adoption.test.mjs. Parse, dynamic import, physical bad import
and receipt tampering behaviors are executed by the existing target test.

**Pilot 2, ICTC:** original seven-process HTTP/SQLite runtime on pinned
Git commit d478cdd185b433f81127fa3251daebed4f84fd38.
The fixed command is node
tests/verification/e2e-cross-process-receipts-check.mjs. Exit zero
requires the native artifact to attest 12 hashed HTTP write/readback
commands over seven processes, 7 auditor requests rejected with HTTP
403, and an unchanged persisted revision after denials. This DOES NOT
execute the product browser or independently certify the local runner.

**Negative controls:** LUMEN original browser screenshot test is
read from Git, but Chromium is NOT RUN by this CORA pilot. NILO's
original conditional Render post-deploy workflow is Git-read but remote
Render is NOT PROBED. Its reported SKIPPED is a caller-declared
negative control, not authenticated remote GitHub evidence. Neither
source check becomes a product or release PASS.

**Execution and replay:** the existing Python package exposes the
allowlisted, bounded API cora.native_gold.capture_native; this API is
never called implicitly by process-run or verify-process. With explicit
operator consent and a disposable target checkout, it checks exact
HEAD, tracked source cleanliness and the original committed oracle,
executes with a subprocess argument array (no shell), scrubs inherited
tokens and captures bounded log bytes outside the target. The ICTC
native artifact is copied and validated; absence of a required artifact
is an error, never PASS. Each receipt includes SHA-256, exit code,
bounded local elapsed_ms, source commit, oracle identity and
authority NONE. replay_native rereads both the original Git blob and
the retained bytes but cannot authenticate who ran the command.

Use the original CORA CLI with additional opt-in argument:
    cora process-run TARGET --one-run --portable-profile PROFILE-v2.json --portable-native-probe OUTSIDE-TARGET/NATIVE-DIR --output RECEIPT.json --atlas-html RECEIPT.html

Replay:
    cora verify-process RECEIPT.json --repo TARGET --one-run --portable-profile PROFILE-v2.json --portable-native-probe OUTSIDE-TARGET/NATIVE-DIR --atlas-html RECEIPT.html

The native probe must identify ONE existing Gold BEHAVIOR claim with
matching source revision, original oracle path and oracle SHA. The
original claim_proven stays false; independent reviewer and
release authorization remain BLOCKED_EXTERNAL/NONE. A native exit
failure is a recorded FAIL and the One-Run returns nonzero.

**Static JS graph:** original-Git ESM source imports now distinguish
resolved exact relative paths, missing exact relative paths,
unknown extension/directory imports and unresolved package/builtin
references. Dynamic imports, CommonJS, TS/JSX, and runtime consumers
remain unknown, and safeDeletion is always NOT_PROVEN.

**Derived single dossier:** native-gold-four-repo-atlas.json is a
read-only projection of two local native receipts and two original
source-only controls, not a new authority. No extra command or
separate approval bus is introduced.

**Reticular DoD:** original Git SHA AND original native oracle AND
allowlisted explicit subprocess AND retained log AND exit and
native-artifact checks AND 12 ICTC operations AND 7 denials AND
byte replay AND one named Gold claim AND two non-promoted external
controls AND zero self-issued release claims. Original source-only
Original portable-profile and source-only behavior remains backward compatible.

**Efficiency:** local elapsed_ms is measured, but controlled
engineering-hours savings against an alternative remain NOT_MEASURED.
Independent E3/E4 user/reviewer acceptance, authentic CI identity,
LUMEN browser and NILO remote Render are BLOCKED_EXTERNAL.
