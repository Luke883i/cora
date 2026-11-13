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

## Test-oracle rule
`tools/verify_release_readiness.py` emits `source_status=PASS_SCOPED` only after validating a strictly bounded set of source declarations. It always emits `release_status=BLOCKED_EXTERNAL`, `release_authorized=false` and `authorization=NONE`: it cannot inspect GitHub branch permissions, authenticate reviewers, sign tags, run real deployment tests or approve a release. `--require-release-approval` exits nonzero even when source passes. A CI green check for source truth must not be named 'release approved'.

## Independently observable release checklist
1. Source and CI SHA identical; branch diff reviewed and all required checks successful.
2. Administrator demonstrates active non-bypassable branch protection/required checks and independent non-author review.
3. Authorized release manager reviews exact wheel, sdist, hashes, provenance and install tests.
4. Independent engineer completes novice-reader task and unrelated maintained-repo pilot with recorded deviations.
5. Tag, GitHub Release, assets, immutable checksums and release notes are produced only after 1–4; publication is not inferred from merged source.
