<a id="pr-15-definition-of-done--product-software-repository-and-governed-release"></a>
# Governed release Definition of Done — product, software and repository

**Document status:** CURRENT
**Current scope:** Noncompensatory candidate build and release-governance requirements.
**Operational use:** Verify package artifacts and separately demand real host/reviewer approvals.
**Evidence:** pyproject.toml, release workflow and exact-artifact hashes.
**Limits:** Candidate CI cannot sign provenance or authorize publication.


## Global DoD (AND, no averaging)
**G-source:** I1 AND I2 AND I3 AND I4 AND I5. Supported source/CI checks can produce `PASS_SCOPED`, never authority. **G-release:** G-source AND I6 AND I7. G-release remains `BLOCKED_EXTERNAL` unless independently authenticated GitHub/human and external validation witnesses are supplied. A false PASS from unknown evidence violates the DoD.

| Intermediate DoD | Local obligations | Witness and acceptance |
| --- | --- | --- |
| I1 Identity | L1 expanded name; L2 product/software/repo non-equivalence; L3 single CLI; L4 alpha version | README, ADR, ontology, pyproject, package-init, source-contract tests. |
| I2 Discoverability | L5 README first screen; L6 quickstart; L7 all commands linked; L8 complete architecture incl. continuous and debt | `verify_repository_contract`, novice task sheet (human remains independent). |
| I3 Evidence truth | L9 source-contract digest per input; L10 drift detected; L11 never authenticate reviewers; L12 source observations separated from behavior | `verify_release_readiness`, `verify-artifacts`, `verify-process`; external unknowns remain unknown. |
| I4 Falsification | L13 independent negative mutation fixtures; L14 Python 3.11/3.13 tests; L15 CI fails for source drift; L16 existing regression suites | `test_pr15_release_readiness.py` and all required GitHub CI on final SHA. |
| I5 Packaging | L17 PEP 440 alpha; L18 source/wheel/sdist parity; L19 independent installed fixture; L20 no stable release claim | `ci-release-candidate.yml`, version verifier and artifact checks, no publishing. |
| I6 Hosting governance | L21 branch protection enabled; L22 independent non-author approval; L23 required trusted checks; L24 immutable commit/SHA review | GitHub admin/settings/check-runs/reviews on exact candidate. **OPEN** on baseline; not supplied by local code. |
| I7 Release operations | L25 independent release manager; L26 reviewed annotated tag and GitHub Release; L27 signed provenance as applicable; L28 external real-repo pilot/consumer and rollback assessment | Human sign-off and authoritative GitHub Release/build evidence. **OPEN**. |

## Three-boundary closeout interpretation (one existing release DoD)

Do not invent another approval engine or treat a source-complete repository as enterprise-ready. **Product `cora`** is evaluated under I1 identity and I2 reader/consumer discovery; **software `cora-engine` and `cora-release-verification`** under I3 evidence truth, I4 falsification and I5 build/packaging; **repository `Luke883i/cora`** contributes to I1–I5 through pinned Git, CODEOWNERS, workflow source and CI observations, but requires I6 for effective host governance. **I7** separately governs actual release, external target, signed provenance and human operations.

**Source-closure checklist:** exact Git SHA; all current declared software IDs reconciled to `cora.ontology.json`, `pyproject.toml` and tests; canonical README/architecture/roles; source and installed-code parity where tested; all required final-SHA checks actually successful; falsifying mutations rejected. A PR-head check is not a merged-main check. **External-closure checklist:** effective branch protection, independent non-author reviewer, actual maintained-target behavior and usability, execution isolation, attributable support/rollback and signed release supply chain. `BLOCKED_EXTERNAL` persists if any applicable external obligation is missing.

**Result types:** `SOURCE_SCOPE_DEFINED` (product), `IMPLEMENTED_SOURCE_SCOPED` (engine), `CANDIDATE_VERIFICATION_ONLY` (release software) and `SOURCE_CONTROLS_DECLARED` (repository) are *classifications*, not independent approvals. Their aggregation never changes `release_status=BLOCKED_EXTERNAL`, `release_authorized=false` or `authorization=NONE` emitted by the original release verifier. [Accountable decision rights](../GOVERNANCE.md#product-software-and-repository--bounded-closeout).

## Test-oracle rule
`tools/verify_release_readiness.py` emits `source_status=PASS_SCOPED` only after validating a strictly bounded set of source declarations. It always emits `release_status=BLOCKED_EXTERNAL`, `release_authorized=false` and `authorization=NONE`: it cannot inspect GitHub branch permissions, authenticate reviewers, sign tags, run real deployment tests or approve a release. `--require-release-approval` exits nonzero even when source passes. A CI green check for source truth must not be named 'release approved'.

## Independently observable release checklist
1. Source and CI SHA identical; branch diff reviewed and all required checks successful.
2. Administrator demonstrates active non-bypassable branch protection/required checks and independent non-author review.
3. Authorized release manager reviews exact wheel, sdist, hashes, provenance and install tests.
4. Independent engineer completes novice-reader task and unrelated maintained-repo pilot with recorded deviations.
5. Tag, GitHub Release, assets, immutable checksums and release notes are produced only after 1–4; publication is not inferred from merged source.
