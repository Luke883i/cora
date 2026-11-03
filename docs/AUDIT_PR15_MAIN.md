# PR-15 severe audit — CORA applied to CORA

Baseline: merged PR-14 `main@c14a5880f90d2c45d2b7961cbeb4dac0a42716d4`, 2026-11-03. Audit methods: direct GitHub source and metadata inspection; README/architecture/ontology/CLI/test/workflow/release-contract review; recent GitHub CI evidence. This document does not claim a locally executed full regression at the original Git ancestry.

## Multi-abstraction findings

| ID | Level | Severity | Observed evidence | Disposition |
| --- | --- | --- | --- | --- |
| F01 | Product language | P1 | README title has no expanded CORA name; historic origin not documented. | Adopt explicit current expansion; do not fabricate historic etymology. |
| F02 | Product onboarding | P1 | README covers the functionality but narrates PRs, repeats scope and includes first-bootstrap wording after PR-14 merge. | Consolidate the release boundary and update bootstrap semantics. |
| F03 | Architecture | P1 | `docs/ARCHITECTURE.md` starts with PR-01–07 / 1.0.0a1 scope despite merged PR-14. | Update scope and map archaeology, debt, process suite and continuous gates. |
| F04 | Metadata | P1 | Main package is 1.0.0a3; source, package and release identity need one verifier before next candidate. | Bump to 1.0.0a4; verify exact source declarations. |
| F05 | Repository controls | P0 | GitHub branch endpoint exposes `main.protected=false`; admin-independent approval not established. | EXTERNAL BLOCKER. Protected required checks, non-author review and administrator confirmation. |
| F06 | Governance | P0 | `continuous.evaluate` emits review routing and `authorization=NONE`; CI permits correct `BOOTSTRAP_REVIEW_REQUIRED` detection as green. | Preserve detection/approval separation; release must never be inferred from a green CI. |
| F07 | Assurance | P1 | Existing source replay verifies reproducibility, not algorithm correctness or runtime and scanner authenticity. | Add negative release-contract fixtures, source scan, independent human+external gates. |
| F08 | Engineering debt | P2 | AST, bounded history, change coupling, caller SARIF are partial/heuristic; no calibrated real-repo rates. | Follow-on independent pilots and measured precision/recall/coverage. |
| F09 | Supply chain | P0 | Wheel/sdist can be built and source-compared; no authenticated public tag, signed provenance or release approval established. | Publish only after downstream sign-off and release-object verification. |
| F10 | DevOps | P1 | Post-merge debt drift is source-bounded; deployment incidents/SLO/rollback not attested. | Add trusted telemetry adapters in a separate scoped PR. |

## CORA-on-CORA source analysis
Run `cora process-run . --process full --revision HEAD --max-commits 12 --output /tmp/cora-process.json`, `cora verify-process /tmp/cora-process.json --repo .`, `cora debt-scan . --max-commits 12 --output /tmp/cora-debt.json`, `cora verify-debt /tmp/cora-debt.json --repo .`. All of these report observations of the committed source; **full** excludes target test execution, LLMs, third-party scanners and runtime tracing. The new source-contract verifier adds a separate stdlib-based oracle for release documentation and metadata, not a replacement for source-bound CORA.

## Limits, falsification and acceptance
Existing million-case corpora are synthetic finite policy states and not a million independently maintained projects. PR-15 adds mutation tests for independent failure modes (wrong version, missing name, policy coverage loss, privileged workflow, missing release docs). Passing these fixtures establishes only supported contract detection. The global release gate remains **DEBT_BLOCKED / BLOCKED_EXTERNAL** until F05, F09 and human/external verification are closed with independently observable witnesses.

## Standards crosswalk (engineering references, no certification)
NIST SSDF SP 800-218: PO/PS/PW/RV; OpenSSF OSPS Baseline v2026.08.28 for protected changes and developer controls; Python Packaging User Guide/PEP 440 for alpha identities; GitHub protected branches, required checks and GitHub Releases; SLSA source/build provenance. Matching source files to standards does not establish compliance.
