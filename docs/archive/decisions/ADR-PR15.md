# ADR-PR15 — Identity and governed release boundary

Status: Proposed in PR-15 (not historically attributable to PR-01).

## Decision
Adopt **CORA = Continuous Ontological Repository Assurance** as the present expanded product name. C = Continuous (pre/post merge and continuous investigation), O = Ontological (explicit product/software/repository/artifact distinctions), R = Repository (Git provenance and bounded source scope), A = Assurance (falsifiable, scoped evidence, not permission). No prior etymology is asserted. The project may retain its package name `cora-audit`, product id `cora`, software ids `cora-engine` and `cora-release-verification`, and single CLI `cora`. Renaming a package/import would introduce avoidable compatibility debt.

## Release decision
Bump only the alpha candidate from 1.0.0a3 to **1.0.0a4** and preserve prerelease semantics. A published stable 1.0.0, GitHub Release, tag or signed attestation is **not** claimed. The release proceeds only through a protected PR, verified CI on the exact commit, an independent human approval, reviewed build artifacts, a versioned tag and GitHub Release object. If any gate is unknown, report **BLOCKED_EXTERNAL**, not a virtual PASS.

## Trade-offs
Use a stdlib static source-contract verifier to detect drift with deterministic negative tests. It cannot authenticate GitHub controls or production evidence. Reuse CORA's existing Git-backed provenance, process, debt and packaging tools rather than building a second analyzer or accepting self-reported AI approval.

## Follow-up
After the PR merges and hosting controls exist: obtain an external novice-engineer first-read assessment, at least one independently maintained real repository pilot, trusted runtime/test/coverage observations and a release-manager sign-off. No automatic deletion or general refactor authority is introduced.
