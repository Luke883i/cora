# CORA documentation semantic DoD

The [machine contract](../.cora/contracts/dod/documentation-dod.json) defines 28 nodes: 18 source obligations, three independent external obligations, five intermediate cuts, and two global roots.

**G_DOC_SOURCE** requires all of I_VALUE, I_ACCESS, I_CONSISTENCY, I_OPERATION, and I_EVIDENCE. **G_DOC_ACCEPTED** requires G_DOC_SOURCE and E01, E02, and E03. Every dependency is AND-composed.

## Source obligations

- **I_VALUE:** README explains the product promise before the internal implementation history, distinguishes product/software/repository, and never inflates its proof claims (S01, S02, S03, S06).
- **I_ACCESS:** Complete inventory and navigable links from README; newcomer walkthrough and AI agent adoption; each Markdown gets exactly one registry record (S04, S05, S07, S08, S18).
- **I_CONSISTENCY:** Correct DoD precedence, historical material preserved, contextual intent included in procedures, alpha/merge/publication separated, all 43 baseline Markdown present (S09, S10, S12, S16, S17).
- **I_OPERATION:** CLI reference covers the real parser; repository checks and operational documents agree with the current methods (S11, S13, S14).
- **I_EVIDENCE:** Negative tests, source regression and CI run at the final revision (S15).

The registry provides original Git blob references for the 43 baseline Markdown files. Historical ADRs and audits are historical records, not current acceptance authority. Current guides may be revised without changing the conclusions that the historical documents reached.

## External obligations

- **E01:** A truly unfamiliar engineer completes the first-read task without prior chat guidance.
- **E02:** An independent coding-agent operator completes adoption on a different maintained repository with a real oracle and PR review.
- **E03:** An administrator demonstrates effective required checks and independent reviewer access.

A passing static document verifier is a source-contract observation, **not** proof that I_EVIDENCE has completed final-head CI or that external obligations exist. G_DOC_ACCEPTED stays BLOCKED_EXTERNAL until real outside witnesses have been collected.

## Falsification requirements

Negative fixtures must reject missing files, duplicated identities, broken links, wrong history classification, missing CLI references, incomplete contextual intent, altered DoD prerequisites and claims of release authorization from source checks alone. The test results must be bound to the exact final Git SHA. Synthetic model coverage and local fixtures are not human usability tests.

## Revision-bound claim-to-evidence profile (merged PR-22)

The separate [claim/proof profile](../.cora/assurance/documentation-proofs.json) binds each S01–S18 leaf to one README proposition in its actual section, a named implementation/contract file, an existing test source and a concrete falsifier. The [source verifier](../tools/verify_claim_evidence.py) reads each witness as a Git blob from the **same pinned commit**, checks fixed semantic boundary oracles (including CLI parser, intent digest, declaration IDs, legacy blob identity, source-vs-external DoD and cross-document contradiction patterns), and emits a replayable SHA- and blob-attributed receipt.

From an authorized checkout, with full Git history including the PR-21 baseline, run:

```sh
python tools/verify_claim_evidence.py --repo . --revision HEAD --output /tmp/cora-doc-proofs.json
python tools/verify_claim_evidence.py --repo . --revision HEAD --verify-report /tmp/cora-doc-proofs.json
```

A source receipt means **PASS_SCOPED_SOURCE** for the implemented *finite* predicates and Git provenance only. The checker cannot prove all meanings in natural language or any real runtime behavior. Test-file paths are source-role witnesses, not attestations that the tests executed. The exact final-HEAD GitHub check-runs and independent E01 (novice), E02 (real agent/target pilot), E03 (effective host and non-author reviewer) must be observed separately; `G_DOC_ACCEPTED` remains `BLOCKED_EXTERNAL` and `authorization=NONE`.

Adversarial Git fixtures physically commit contradicting current-doc claims, detached intent wiring, parser drift, DoD edge changes, historical blob rewrites, CI proof omissions and stale receipt forgeries. They exercise falsifier sensitivity rather than assert exhaustive semantic proof. The source-oracle code and its profile are PR-editable and cannot approve changes to themselves.

## Progressive navigation micro-DoD — PR-23 source (merged)

No parallel documentation engine is introduced. Reuse the PR-21 source leaves **S01–S18**, the PR-22 revision-bound claim profile and the existing `verify_documentation.py` entrypoint. The following **editorial DoD is a proposed non-compensatory cut**, not a new certificate of human understanding:

| Local cut | Necessary property and source evidence | Falsifier / user |
| --- | --- | --- |
| **N1 Identity** | CORA is one evidence-first product, one Python CLI distribution with two declared software identities, and a distinct repository; first-screen README and ontology | Rename one identity while keeping links syntactically valid; newcomer |
| **N2 Useful first screen** | Value proposition, recommended workflow, concrete user audience, alpha/limitations and existing MIT license are visible before disclosure | Hide license or safety limits in collapsed material; evaluator |
| **N3 Progressive routes** | Five uniquely identifiable, closed, expandable lenses map product, software, repository, governance and evidence; no JS or competing catalogs | Remove or duplicate a lens, break a closing tag; reader |
| **N4 Audience path** | Getting started, coding agent, forensics, human product/security/release owner and full index are directly accessible without expanding | Misroute one persona to a wrong/absent task; newcomer/agent |
| **N5 Evidence and authority** | DoD, actual CLI/source verifiers, revision-bound proof profile, Git/CI and independent decision rights remain distinct | Promote model PASS to approval, claim real runtime or publication; reviewer |
| **N6 History and semantic minimalism** | The 48-item index and 17 historical blobs remain intact; the 18 README claim/proof leaves, complete parser, first-use task routes and bounded truth predicates must remain green. Line count is tracked as a diagnostic, **never a release gate** | Remove a claim, stale Git status, misleading runtime authority, break a user route or a link; maintainer |

**G_NAV_SOURCE = N1 ∧ N2 ∧ N3 ∧ N4 ∧ N5 ∧ N6.** This is checked only by finite structural/semantic source predicates, existing PR-21/22 provenance contracts, and actual CI on the reviewed HEAD. **G_NAV_ACCEPTED = G_NAV_SOURCE ∧ E01 ∧ E02 ∧ E03**, so an unfamiliar-human navigation trial, an independent maintained-target agent pilot and host-enforced non-author review remain **BLOCKED_EXTERNAL** without actual witnesses.

The `test_pr23_navigation.py` experiment creates **1,000 reproducible adversarial editorial/reader-target input variants** across ten prespecified mutation families. They are ten classes with 100 distinct text vectors each, *not* 1,000 independent humans, authentic user sessions or independent semantic concepts. Each variant must break an explicit current invariant while an unchanged source must pass; output reports case counts and family-specific survivors. The mutation corpus cannot measure real task completion, calibrated product quality or accessibility in every browser. Human first-read remains the falsifier for those external claims.

## Capability and method completeness — source cut

The [capability atlas](../.cora/assurance/capability-atlas.json) is the machine census for the `cora` CLI and non-CLI repository surfaces. It records **71 commands / eight method families**, per-command implementation and test-source witnesses, explicitly classified target-side effects, and all tracked modules, operational tools, CI workflows and contract/documentation records. Do not interpret 71 subcommands as 71 separately qualified user-visible product outcomes.

The companion [capability DoD](../.cora/contracts/dod/capability-dod.json) is a noncompensatory AND lattice: **C01–C07** distinguish identity, complete parser/dispatch documentation, effects, repository inventory, cross-document chronology, Git provenance/replay and actual CI attribution. The Git source verifier can check bounded parts of C01–C06; **C07 cannot become observed CI success merely because its source code or tests exist**. E01–E03 remain independent user, maintained-target and host/reviewer acceptance obligations.

Source replay, from an authorized CORA checkout:

```sh
python tools/verify_capability_atlas.py --repo . --revision HEAD --output /tmp/cora-capability.json
python tools/verify_capability_atlas.py --repo . --verify-report /tmp/cora-capability.json
```

Every generated receipt binds method and test-source Git blob OIDs to a revision. The verifier checks `argparse` entrypoints, source-import/dispatch relationships, test-file syntax/role, current method documentation, repository-surface completeness, sensitive interaction labels, DoD edges and critical README/architecture/changelog consistency. A reported test OID is a **source witness only**: no execution, branch protection, release, reviewer or functional correctness is authenticated. Actual required CI status must be observed on the exact final SHA outside the source receipt; external behavior must be tested separately.

## PR42 README semantic refactor amendment (source-bound, not human acceptance)

The former **≤180 physical-line** gate has been falsified: adding harmless Markdown whitespace can fail it, while compact lines can contain false claims. A numeric line budget is **not** a valid proxy for clarity, safe onboarding, correctness or semantic preservation. The rule is retired as a blocking predicate; line/word counts remain optional diagnostics. This amendment does not change the original 28-node documentation evidence DAG or promote E01–E03.

The [machine-readable README refactor DoD](../.cora/contracts/dod/documentation-dod.json) adds a separately checked, non-authorizing `readme_refactor` contract. Its **ten source cuts** cover exact S01–S18 section/claim binding, live merged PR41/current release truth, first-use order, all five reader routes and five disclosure lenses, exact 71-command identity, One-Run status honesty, Git-tracked relative links, explicit independent-operator limits and finite falsifiers. All ten are AND-required: a missing source claim or incorrect disclosure defeats a source PASS regardless of other successes.

The [PR42 navigation regression](../tests/test_pr23_navigation.py) maintains the original 1,000 adversarial vectors and adds **10,000 deterministic, distinct, preregistered variants** (`seed=883`, 20 families × 500): 4,000 meaning-preserving editorial transformations that must PASS and 6,000 false-authority/claim-count/command/link/traceability changes that must FAIL. Zero incorrect classifications, original-Git 18/18 proof replay, exact-HEAD Python 3.11/3.13 CI and a proofable checksum of the mutant stream are the SOURCE thresholds. A **true unfamiliar engineer**, an external maintained-target agent study and effective protected GitHub non-author review remain separately **BLOCKED_EXTERNAL** without real operator witnesses.

The newest README is a current front door, not a new release or migration of historical truth. The PR42 test source and `README.md` Git blob must be compared to the reviewed candidate, with commit identity invalidated by any subsequent edit. No new orchestrator, auto-merge, release, or paper-only human study is authorized.
