# CORA scientific research — decision-ready assurance (MS-10)

**Current main baseline:** `4ed58534022345e58d17207ab472a306d06d2925` (16 Nov 2026). This folder is a research artefact, not a runtime engine, proof of user outcomes or authorization surface.

**Research object:** typed evidence boundaries and actionable acquisition frontiers in AI-assisted software engineering. The operating question is which revision-bound evidence, *actually measured* task-specific human comprehension and attributable permission are needed for a justified engineering decision, with explicit verification cost. **No incremental accuracy gain or human comprehension gain has been shown.**

## Reading order

1. `MANUSCRIPT.markdown`: full paper source; `MANUSCRIPT.docx` is committed in this folder as an actual two-column Word document; the separate archival companion also includes the styled authoring version. Neither is the official IEEE Access template.
2. `CLAIM_LEDGER.json`: supported, bounded, unsupported and contradicted scientific claims. An unsupported claim does not become evidence by appearing in the paper.
3. `evidence/RETROSPECTIVE_11_CASES.json`: public PR identities, pins and source limits.
4. `evidence/FACTS.json`: observations versus unobserved user outcomes and costs.
5. `evidence/REFERENCES.json` and `evidence/ARCHIVE_REGISTER.json`: prior art and original archive digests.
6. `ROADMAP.markdown`: author-closeable DoD versus external empirical and editorial obligations.
7. `verify_release.py`: read-only claim and provenance tests, fail-closed.

## What the study demonstrates

11 purposively selected PRs across five repositories contain 92 applicable evidence slots and 70 **unobserved within the retrieved dossier**. On the finite 16-fixture comparator, EC-03 and a strong checklist tie. Forty-four model-generated briefings are not observed human comprehension. The 211 workflow-file census is not a count of running pipelines or agent-authored decisions. All results are author-controlled and scoped.

## Archival complement and portability

**This Git repository folder contains a compact, human-readable and directly testable scientific dossier.** The five historical original ZIP bundles (52.6 MB altogether) are delivered separately in the downloadable research ZIP, preserving byte hashes declared in the archive register. The heavy archives are **not committed to GitHub**. Consequently source-only verification and complete archival verification are different results, and no claim of full remote byte archival is made.

This avoids putting historical experimental binaries on the runtime-critical CORA tree. The independent archive can be placed under `evidence/archive/` to run full verification. None of this modifies CORA runtime authority.

```bash
python research/decision-ready-assurance/verify_release.py
# On the unpacked complete archival companion:
python research/decision-ready-assurance/verify_release.py --archival
```

No online GitHub check, independent human experiment, peer review, release approval or product certification is executed by this folder.

## AOSP R1 executive brief (17 November 2026)

A standalone, two-page A4 CTO/beginner document is available at [AOSP_R1_CTO_STANDALONE.docx](AOSP_R1_CTO_STANDALONE.docx). It distinguishes AOSP programme membership from shared runtime and gives four concrete source-bounded examples. Its original source is [AOSP_R1_BRIEF_CONTENT.json](AOSP_R1_BRIEF_CONTENT.json); see [scientific freeze](AOSP_R1_SCIENCE_FREEZE.markdown), [nine public source pins](AOSP_R1_PUBLIC_SCOPE.json), [reflection/AND DoD](AOSP_R1_PROJECT_AND_DOD.markdown), [falsification report](AOSP_R1_FALSIFICATION.markdown), and [deterministic builder](tools/build_aosp_r1.py). This communications artifact does not extend MS-10 scientific claims, provide a human study or authorize a release.

## English R2 field guide and 100 selected adversarial cases (17 November 2026)

The R1 Italian brief remains preserved. The revised reader-first artifact is the [English four-page Word guide](aosp-r2/ENGLISH_FIELD_GUIDE_R2.docx), built around backward AND derivation, source-bound Git blobs, physical-vs-modeled falsifiers, bounded semantic saturation, and a real ICTC screenshot-ledger → DOM issue case without pretending to possess the original image bytes. Read the [R2 authorial source](aosp-r2/BRIEF_SOURCE.json), [pinned public evidence atlas](aosp-r2/EVIDENCE_PINS.json), [strong editorial DoD](aosp-r2/EDITORIAL_DOD.json) and [adversarial report](aosp-r2/ADVERSARIAL_AUDIT.markdown). The [100-case catalog](aosp-r2/MUTATION_CATALOG_100.json) preserves 99/100 initial failure and 100/100 corrected scoped replay with ten benign controls; none is an independent reader experiment or product certification.
