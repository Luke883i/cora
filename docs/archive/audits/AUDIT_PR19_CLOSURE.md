# CORA PR-19 — Historical failure and closure audit

## Historical exact-source falsification

Base CORA `main@cfd2178c00cc88885961a0a20017cca6c178bdda` (PR-18 merged). At PR-19 candidate `c0af25a8851cb854e124498d649b94fee04b0cbe`, **24 checks succeeded, one failed, one was skipped**, none pending. The failing `gold-three-repo-source` workflow checked out CORA and public ICTC successfully, but the next checkout (private ikant) failed before its source files could be verified; the aosp1 private checkout and the `gold-pilot` verification were skipped. GitHub run: https://github.com/Luke883i/cora/actions/runs/41674419549

The source metadata distinguishes `Luke883i/ictc` (public) from `Luke883i/ikant` and `Luke883i/aosp1` (private). CORA's workflow GITHUB_TOKEN is not a cross-repository private source entitlement. Neither valid source SHA nor read access through the author's connected GitHub account means that a candidate pull request may obtain an unrestricted token to clone private repos.

## Semantic correction, no diluted DoD

The new CI `gold-public-source-boundary` checks out only public ICTC at an immutable commit; it runs the actual CORA `gold-pilot` with one local checkout, requires the expected nonzero status and validates the exact JSON receipt: **1 verified Git repository source / 3 required**, private ikant and aosp1 listed as `NOT_OBSERVED` with `NO_EXPLICIT_PINNED_CHECKOUT`, state `BLOCKED_INCOMPLETE`, runtime `NOT_EXECUTED`, external status `BLOCKED_EXTERNAL`, authorization `NONE`. A failed public readback is still a failed CI job. Its successful negative gate means **fail-closed classification only**, not full R4 validation.

The newly exposed `source_readbacks_verified`, `source_readbacks_required`, `unresolved_repositories` and `access_provenance` are user-facing engineering evidence. A test constructs **three real local Git repositories**; it first proves the 1-of-3 blocked behavior, then supplies all three and verifies the successful **fixture-only** 3-of-3 mechanism, followed by blob tampering and HEAD-drift negatives. The fixtures are not the private product repositories.

## Software portability and execution boundary

A second fault existed in the optional Docker mutator: it forced container UID 65534 to traverse a `TemporaryDirectory` owned by the calling user and normally mode 0700. The correction uses the invoking **non-root** host UID/GID and never makes the staging directory world-readable. The image remains digest pinned, the mount read-only, with network disabled and no implicit target execution. A new regression mocks Docker to check user identity, pinned image, root-host refusal and no invocation without explicit consent. No real Docker isolation or target behavior was attested by that mock.

## Product / software / repository lattice and remaining unknowns

| Perspective | Supported source outcome | Still blocked |
| --- | --- | --- |
| Product | One CORA product; contextual gold DoD and five new CLI methods; no automatic merge/release | Real target-owner semantics, user acceptance and actual cross-repo operations |
| Software R1 | 23-node global/intermediate/local reticulum; negative JSON/owner source tests | Independently qualified canonical owner/consumer graph |
| Software R2 | Byte-level temporary mutations and killed/survived/timeout/inconclusive classification | Behavioral mutants on real target systems; Docker isolation |
| Software R3 | Conservative workflow-effect inspection and non-promoting caller claims | Trusted host side-effect readback |
| Software R4 | Three frozen source anchors, readback CLI, **public ICTC CI 1/3** | Real private ikant/aosp1 readbacks **2/3**, runtime/postmerge pilot |
| Repository | Exact HEAD regression, legacy tests, model 10M twice, artifact roles and discoverability | Independent branch rules, external reviewer and runtime pilot |
| Authority | `authorization=NONE`, governed blocked | Human approval, rollback attestation, protected merge and release |

The full `G_GOLD_SOURCE = I_CONTEXT AND I_PHYSICAL AND I_EFFECT AND I_PILOT` is **not closed** merely because CI successfully handles missing private source access. `G_GOLD_GOVERNED = G_GOLD_SOURCE AND I_EXTERNAL` remains blocked separately. A correct detected blocker is not an approved waiver or a PASS for its parent. The ten million pre-seeded semantic fault scenarios are finite-model calls, not ten million physical source mutants.

## Approved follow-on needed for complete R4

A maintainer with legitimate access must run `cora gold-pilot --ictc-root ... --ikant-root ... --aosp1-root ...` in a separately trusted context using local Git checkouts on all three exact pinned commits, preserving the command, environment and receipt. For recurring automation, an administrator must first establish a protected, independently reviewed workflow or appropriately scoped GitHub App: never expose private-repository tokens in candidate PR workflows. Independent behavioral oracles, actual CI side effect readbacks, postmerge regression, sandbox tests, rollback and release authorization remain future, external requirements.

This audit describes **committed source** and observed GitHub workflow behavior on an identified previous SHA. It is not a successful check on the next candidate HEAD, a private access grant or an authentication of human reviewers.
