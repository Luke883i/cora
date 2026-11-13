# CORA documentation semantic DoD

**Document status:** CURRENT
**Current scope:** Source-checkable documentation graph and independently unverified reader gates.
**Operational use:** Apply source/provenance, anchor and status checks to every registered document.
**Evidence:** Markdown registry, claim-to-Git profile and negative tests.
**Limits:** Finite machine readability is not a human study or external approval.


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

<a id="revision-bound-claim-to-evidence-profile-merged-pr-22"></a>
## Revision-bound claim-to-evidence profile

The separate [claim/proof profile](../.cora/assurance/documentation-proofs.json) binds each S01–S18 leaf to one README proposition in its actual section, a named implementation/contract file, an existing test source and a concrete falsifier. The [source verifier](../tools/verify_claim_evidence.py) reads each witness as a Git blob from the **same pinned commit**, checks fixed semantic boundary oracles (including CLI parser, intent digest, declaration IDs, legacy blob identity, source-vs-external DoD and cross-document contradiction patterns), and emits a replayable SHA- and blob-attributed receipt.

From an authorized checkout, with the original documentation baseline reachable in Git, run:

```sh
python tools/verify_claim_evidence.py --repo . --revision HEAD --output /tmp/cora-doc-proofs.json
python tools/verify_claim_evidence.py --repo . --revision HEAD --verify-report /tmp/cora-doc-proofs.json
```

A source receipt means **PASS_SCOPED_SOURCE** for the implemented *finite* predicates and Git provenance only. The checker cannot prove all meanings in natural language or any real runtime behavior. Test-file paths are source-role witnesses, not attestations that the tests executed. The exact final-HEAD GitHub check-runs and independent E01 (novice), E02 (real agent/target pilot), E03 (effective host and non-author reviewer) must be observed separately; `G_DOC_ACCEPTED` remains `BLOCKED_EXTERNAL` and `authorization=NONE`.

Adversarial Git fixtures physically commit contradicting current-doc claims, detached intent wiring, parser drift, DoD edge changes, historical blob rewrites, CI proof omissions and stale receipt forgeries. They exercise falsifier sensitivity rather than assert exhaustive semantic proof. The source-oracle code and its profile are PR-editable and cannot approve changes to themselves.

<a id="progressive-navigation-micro-dod--pr-23-source-merged"></a>
## Progressive navigation and five reader paths

No parallel documentation engine is introduced. Reuse the source leaves **S01–S18** and the revision-bound claim profile and the existing `verify_documentation.py` entrypoint. The following **editorial DoD is a proposed non-compensatory cut**, not a new certificate of human understanding:

| Local cut | Necessary property and source evidence | Falsifier / user |
| --- | --- | --- |
| **N1 Identity** | CORA is one evidence-first product, one Python CLI distribution with two declared software identities, and a distinct repository; first-screen README and ontology | Rename one identity while keeping links syntactically valid; newcomer |
| **N2 Useful first screen** | Value proposition, recommended workflow, concrete user audience, alpha/limitations and existing MIT license are visible before disclosure | Hide license or safety limits in collapsed material; evaluator |
| **N3 Progressive routes** | Five uniquely identifiable, closed, expandable lenses map product, software, repository, governance and evidence; no JS or competing catalogs | Remove or duplicate a lens, break a closing tag; reader |
| **N4 Audience path** | Getting started, coding agent, forensics, human product/security/release owner and full index are directly accessible without expanding | Misroute one persona to a wrong/absent task; newcomer/agent |
| **N5 Evidence and authority** | DoD, actual CLI/source verifiers, revision-bound proof profile, Git/CI and independent decision rights remain distinct | Promote model PASS to approval, claim real runtime or publication; reviewer |
| **N6 History and semantic minimalism** | The 48-item index and 17 historical blobs remain intact; the 18 README claim/proof leaves, complete parser, first-use task routes and bounded truth predicates must remain green. Line count is tracked as a diagnostic, **never a release gate** | Remove a claim, stale Git status, misleading runtime authority, break a user route or a link; maintainer |

**G_NAV_SOURCE = N1 ∧ N2 ∧ N3 ∧ N4 ∧ N5 ∧ N6.** This is checked only by finite structural/semantic source predicates, existing provenance contracts, and actual CI on the reviewed HEAD. **G_NAV_ACCEPTED = G_NAV_SOURCE ∧ E01 ∧ E02 ∧ E03**, so an unfamiliar-human navigation trial, an independent maintained-target agent pilot and host-enforced non-author review remain **BLOCKED_EXTERNAL** without actual witnesses.

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

<a id="pr42-readme-semantic-refactor-amendment-source-bound-not-human-acceptance"></a>
## README semantic preservation and falsification

The former **≤180 physical-line** gate has been falsified: adding harmless Markdown whitespace can fail it, while compact lines can contain false claims. A numeric line budget is **not** a valid proxy for clarity, safe onboarding, correctness or semantic preservation. The rule is retired as a blocking predicate; line/word counts remain optional diagnostics. This amendment does not change the original 28-node documentation evidence DAG or promote E01–E03.

The [machine-readable README refactor DoD](../.cora/contracts/dod/documentation-dod.json) adds a separately checked, non-authorizing `readme_refactor` contract. Its **ten source cuts** cover exact S01–S18 section/claim binding, current source/release identity and dated provenance truth, first-use order, all five reader routes and five disclosure lenses, exact 71-command identity, One-Run status honesty, Git-tracked relative links, explicit independent-operator limits and finite falsifiers. All ten are AND-required: a missing source claim or incorrect disclosure defeats a source PASS regardless of other successes.

The [navigation regression](../tests/test_pr23_navigation.py) maintains the original 1,000 adversarial vectors and adds **10,000 deterministic, distinct, preregistered variants** (`seed=883`, 20 families × 500): 4,000 meaning-preserving editorial transformations that must PASS and 6,000 false-authority/claim-count/command/link/traceability changes that must FAIL. Zero incorrect classifications, original-Git 18/18 proof replay, exact-HEAD Python 3.11/3.13 CI and a proofable checksum of the mutant stream are the SOURCE thresholds. A **true unfamiliar engineer**, an external maintained-target agent study and effective protected GitHub non-author review remain separately **BLOCKED_EXTERNAL** without real operator witnesses.

The README is the current product entry; a source-document pass cannot approve a release. The current navigation regression source and `README.md` Git blob must be compared to the reviewed candidate, with commit identity invalidated by any subsequent edit. No new orchestrator, auto-merge, release, or paper-only human study is authorized.


<a id="pr48--cto-facing-multi-abstraction-front-door-dod-source-candidate"></a>
## CTO first-read clarity and source-bound front door

**Goal:** reduce the work required for a new reader to find a defensible,
source-linked product claim, rather than increasing the apparatus used to
describe it. The README now states value, an ordinary engineering
method, two authentic project histories, one practical invocation and
limits. The supporting docs keep the detailed engineering example,
architecture, role distinctions and machine contracts.

**Noncompensatory SOURCE leaves (each must pass on the same Git HEAD):**

| Leaf | Required, falsifiable observation |
| --- | --- |
| R48-A clarity | First read distinguishes observable product outcome, Python software, Git repository and agent/host roles; technical vocabulary precedes CORA's proprietary labels. |
| R48-B compression | Root README at most 1,800 whitespace words, introductory promise 115–310 words, with no competing second source-of-truth or deleted supporting contract. Word counts are **guardrails**, not human comprehension proofs. |
| R48-C source identity | All 18 S01–S18 original claims remain bound to their required README sections and original Git blob/test references; 71 commands remain inventory, not 71 demonstrated behaviors. |
| R48-D multi-abstraction evidence | ICTC browser role/viewport witness and 656 screenshot-derived issues/12 root causes are separated from synthetic UI campaigns and physical source mutants; iKant_EDU is a **computational cognitive architecture**, not biological/phenomenological cognition, and source history keeps UNKNOWN consumer and protected-workflow constraints. |
| R48-E method honesty | Backward AND-gate acceptance, bounded slices, seeded fault combinations, independent model oracle, real isolated mutants, novelty-window stopping rule, continuation advice and same-HEAD invalidation remain distinct. |
| R48-F usability/routing | Five existing readers, five optional lenses, quickstart and One-Run, clean relative links and the comprehensive 48-document index survive. The full corrective-action app contract is preserved in the existing continuous-development guide. |
| R48-G falsification | 100 additional unique local/global editorial mutations: 20 benign acceptances and 80 planted semantic faults rejected. Original 1k/10k vector campaigns retain 1,000 rejected, 4,000 accepted equivalences and 6,000 rejected dangerous changes, zero survivors. |
| R48-H integrity | No original tests, protected CI workflows, historical Git blobs, owners or product software rewritten merely to pass editorial review. CI, git diff and replay are checked against the **final candidate SHA**. |

**Global DoD:** R48-A ∧ R48-B ∧ R48-C ∧ R48-D ∧ R48-E ∧
R48-F ∧ R48-G ∧ R48-H ∧ E01 ∧ E02 ∧ E03. The eight SOURCE
leaves can be supported by local source and CI receipts; E01 actual
unfamiliar-reader comprehension, E02 externally maintained target
behavior and E03 enforceable host/human reviewer gates remain
**BLOCKED_EXTERNAL** until independently observed.

**Performance criteria proposed for an actual CTO study, not yet
observed:** first-read identification of value, operating model,
evidence limits and next action without historical context; shortest
path to reproduction; questions asked and interpretation errors
recorded against a deliberately competing long-form baseline. Neither
static assertions nor deterministic lexical mutants measure this.

**Source owners:** `README.md`; `tools/verify_documentation.py`;
`tests/test_pr23_navigation.py` (100 new + historical 1k/10k);
`.cora/assurance/documentation-proofs.json`; `docs/INDEX.md`;
`docs/ARCHITECTURE.md`; `docs/CONTINUOUS_DEVELOPMENT.md`.
The original machine-readable DoD is **retained**, not weakened.

<a id="pr48-migration--source-derived-claritycompression-and-external-qualification"></a>
## Source-derived clarity, compression and external acceptance

This amendment refines the existing R48-A–H AND-gate; it does **not** create a competing DoD or replace the fixed S01–S18 ledger.

- **C / Clarity:** on first scan explain what CORA inspects, why source assurance differs from coding, the path from a falsifiable goal to a scoped decision, and the next command. Structural text checks can reject missing claims; they cannot measure comprehension.
- **K / Completeness:** preserve all S01–S18, five reader routes, five lenses, exact CLI/One-Run/replay path, and source-versus-runtime/host status. The full ten-method comparison belongs to the existing [convergence guide](CONVERGENT_ASSURANCE.md#method-crosswalk--borrowed-perspectives-not-full-implementations).
- **X / Compression:** primary README contains the value/method/usage/limits and two concrete examples without duplicating method documentation or PR archaeology. README whitespace words and first-scan bounds are guardrails; eliminate duplicate narrative while keeping verifiable anchors.
- **V / Multi-audience value:** CTO reads the decision boundary; developer obtains a testable next action; reviewer finds independent falsifiers; forensic engineer traces Git/source lineage; product owner sees external acceptance limitations. Success requires a real first-read study, not word frequency.
- **E / Evidence:** ICTC has separate (i) role/viewport browser screenshot-producing code, (ii) screenshot-derived semantic UX audit, (iii) 656/12 source contract and (iv) real E2 physical source mutants. iKant_EDU has a bounded functional computational cognitive architecture and a recoverable Git/consumer history. Neither demonstrates a fresh run by CORA, an independent ChatGPT-container test or user acceptance.
- **F / Falsification:** 100 deterministic *text/document* variations across local README and linked current docs must include 20 meaning-preserving changes accepted and 80 corrupted claims/links/gates rejected, with zero wrong outcomes; retain the original 1k/10k campaigns. One variant is not one physical software mutation or human respondent.
- **I / Integrity:** use only existing document source owners, preserve historical records, protected CI and product software; recheck on the final PR head and after each subsequent commit. Actual CI, original-Git replay and independent review are different oracles.

**Global obligation = C AND K AND X AND V AND E AND F AND I AND E01 AND E02 AND E03.** Local source tests can support bounded C/K/X/E/F/I; V as *observed human comprehension*, user/target trials and enforced host approval remain **BLOCKED_EXTERNAL** until witnessed. `PASS_SCOPED` must never substitute for them.

## Enterprise-evaluable documentation cut — non-authorizing

**Global outcome G_ENTERPRISE_EVALUABLE:** a CTO can determine product identity, run a bounded local source review, reproduce its receipt, locate each authoritative current document and distinguish source checks from independent acceptance. This is **not** enterprise certification, procurement approval, a signed release or evidence that external target behavior was validated. The evaluation is noncompensatory: an absent required source check is `REFUTED_SOURCE`; satisfied source checks with absent external evidence are `BLOCKED_EXTERNAL`; fully populated declarations yield only `EVALUATION_ELIGIBLE`, never automatic approval.

**Source obligations (S0–S11, all required):** exact Git revision; complete 48/48 Markdown census and Git parity; 31 declared active and 17 historical paths; standalone active-document contracts; zero broken relative links or anchors; five distinct reader routes; current product/CLI/agent boundary; bounded README word budget (at most 1,750 words, including a five-step Project walkthrough) with no PR-numbered headings; nonpromotional assurance method; CycloneDX candidate-CI scope without invented attestations; SCA restricted-scope disclosure; release documentation that requires exact candidate HEAD. Each obligation is owned by the existing [documentation verifier](../tools/verify_documentation.py), [claim-evidence verifier](../tools/verify_claim_evidence.py), [repository verifier](../tools/verify_repository_contract.py), or the corresponding [release workflow](../.github/workflows/ci-release-candidate.yml). They do not independently attest execution by the GitHub host.

**External obligations (E0–E7, non-inferable from Git source):** first-read human comprehension, genuine maintained-target experiments, independently identified reviewer, enforced hosting rules, verified signed provenance, security acceptance, release-manager decision and independent operational review. Each requires externally attributable evidence and remains open until that evidence is actually supplied.

**DoD-of-DoD:** each obligation must name a source, an independent oracle or concrete falsifier, the owning verifier, the exact revision invalidating prior evidence and whether the observation is SOURCE or EXTERNAL. The 20-bit AND-cut is stressed with 1,000,000 deterministic distinct finite vectors, plus physical Markdown/claim corruption controls in [enterprise documentation regression tests](../tests/test_pr62_enterprise_docs.py). The vectors exercise *contract semantics*, not a million independent repository edits, people or real product executions. The original 10,000 README counterexamples remain separately required. Failures must remain distinguishable from `NOT_RUN`; every new source revision requires fresh candidate-SHA CI.

**Live-document history metric:** zero numbered PR narratives in operational Markdown prose outside the explicitly historical CHANGELOG and index. The original verifier strips only compatibility anchor tags, Markdown link destinations and inline code identifiers before searching; paths, aliases and archival Git identities remain intact. The standalone-pr-narrative negative control rejects a fabricated current PR claim while accepting valid legacy links. This lexical gate is necessary but does not prove complete semantic de-storicization.

**Minimality rule:** prefer one existing authoritative owner over a new parallel registry, engine, framework or dashboard. Archive identity is retained; index-only visibility is not evidence of current operational use. No document may claim that Git hashes, SBOM generation or green source CI establish reviewer identity, supply-chain signing, protected hosting or enterprise readiness.

## Reader-first engineering transfer — current minimum source DoD

**Goal:** an unfamiliar CTO or engineer can locate what CORA does, reproduce a source-scoped command, challenge an overclaim, and see what remains blocked, without learning its development chronology first. This is a *source/documentation candidate* measure; no documentation unit test establishes actual human comprehension or external readiness. Reuse the original `S01–S18` documentation contract, verifier, Chat bundle source and source-tested editorial budgets. No second registry, product, software engine, approval gate or "enterprise-ready" designation.

| ID | Necessary source condition | Measurable bound / owner / falsifier |
| --- | --- | --- |
| R63-01 | Product / software / repository boundaries not conflated | README names all three; `docs/ARCHITECTURE.md` owns scope, no second engine; existing source verifier |
| R63-02 | First command, verification and verdict visible | Quickstart and One-Run both retain executable CLI invocation; `PASS_SCOPED`, `NOT_RUN`, `REFUTED`, `BLOCKED_EXTERNAL` stay discriminable |
| R63-03 | One canonical ChatGPT Project adapter | Exactly one paste-ready beta prompt under `docs/AGENT_ADOPTION.md`; README and `GETTING_STARTED.md` link it, not duplicate its instructions |
| R63-04 | Least-privilege permissions and host boundary | Plus/Edu is a *recipe baseline*, not a guaranteed entitlement; normal ChatGPT GitHub connector is read-only; write access requires a distinct authorized tool; local CLI needs real execution |
| R63-05 | Temporary handoff accurately described | `src/cora/chat_bundle.py` retains ZIP/source receipt, `iterations/000001/handoff.md`, finite limits and no signature/memory/approval claim |
| R63-06 | Evidence-backed crossrepo narrative | Seven real historical PR links across CORA, ICTC, Teddy, iKant_EDU; no assertion that CORA independently validated their products |
| R63-07 | Terms are discriminating | Blobbing, materialization, falsification, AND-DoD and finite saturation distinguish source objects, outcomes and inferential limits |
| R63-08 | Preservation and bounded complexity | 48 registered Markdown, 31 active/17 historical, historic byte identity and zero broken local links; root README **at most 1,750 words**, current navigation and documentation test bounds |
| R63-09 | Negative controls catch narrative corruption | Existing 1k, 10k and enterprise finite source falsifiers; targeted physical text mutants for read-only/write claims, prompt duplication, wrong handoff path, and invented approval |
| R63-10 | Exact-head review and no self-approval | Candidate exact Git SHA, repository/documentation/claim verification, relevant native tests and CI; effective host protection, independent review and user trials remain separate |

**Source cut:** `R63_SOURCE = R63-01 ∧ R63-02 ∧ ... ∧ R63-10`. **Governed cut:** `R63_ACCEPTED = R63_SOURCE ∧ E01_FIRST_READ_HUMAN ∧ E02_AGENT_ON_EXTERNAL_MAINTAINED_TARGET ∧ E03_ENFORCED_HOST_AND_NON_AUTHOR_REVIEW`. A missing obligation is `BLOCKED_EXTERNAL` or `REFUTED`, never averaged away.

**Current editorial budget:** cap the README at **1,750 words**. The direct reader report that Project onboarding was inadequate demonstrates why the former 1,450-word heuristic blocked a complete five-step path. This change and its source-test limit are simultaneous; neither number is an engineering standard or evidence of human comprehension. Use progressive disclosure into the single prompt owner; preserve source/external assurance boundaries.

**Checklist before PR acceptance:** snapshot exact BASE/HEAD; verify zero deleted/renamed runtime objects; read-back canonical prompt and source ZIP path; run `python tools/verify_documentation.py --repo .`, `python tools/verify_claim_evidence.py --repo . --revision HEAD --output /tmp/cora-reader-proofs.json` and `--verify-report /tmp/cora-reader-proofs.json`; execute `test_pr23_navigation.py`, `test_pr62_enterprise_docs.py` (including R63 negatives), and `test_pr46_chat_bundle.py`; inspect exact-HEAD GitHub checks and record external gates without claiming they passed.

### ChatGPT Project and timeless navigation — source acceptance

**User outcome:** a first-time reader identifies a ChatGPT Project path directly in the README; the Project adapter remains canonical in `AGENT_ADOPTION.md`, without duplicated prompt text. The five steps specify plan availability without invented entitlement, read-only GitHub access, separately authorized writing, a real runner for CORA-ENGINE and native tests, and the finite ZIP handoff path.

**Noncompensatory source gates:** README project-path presence; five readable and sequence-checked steps; zero PR-number chronology in the README; no changed archival blob; registered Markdown graph still 48/48; product/software/repository boundaries; version- and permission-truthful claims; existing 1k/10k editorial mutants; exact-HEAD CI. The README budget is **1,750 words** as a provisional lint guardrail (not a universal readability standard).

**External gates:** unfamiliar reader first-task completion, independently maintained target/runner test, protected reviewer authorization and real Project access remain **NOT_ATTESTED** until witnessed. A source checklist does not authenticate GitHub permissions or a ChatGPT Project execution.
