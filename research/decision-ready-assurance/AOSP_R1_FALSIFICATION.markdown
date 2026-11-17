# AOSP R1 — falsification, reproduction and claim ceiling

**Date:** 2026-11-17. **Verdict:** `PASS_AUTHOR_SCOPED` for the bounded editorial/structural tests only. R1 is not an independent reader test, an enterprise certification, a scientific replication by a third party or a release approval.

## Pinned inputs and the new output

- Scientific baseline: PR73 before R1 `6695923c1689bc440fa26969d32eb32356c8df76`; CORA main `4ed58534022345e58d17207ab472a306d06d2925`. Original MS-10 manuscript, claim and factual registries remain unchanged.
- Public programme scope: nine `Luke883i` GitHub repositories pinned by main-commit and README blob in `AOSP_R1_PUBLIC_SCOPE.json`. Programme membership is not shared runtime.
- Standalone Word: `AOSP_R1_CTO_STANDALONE.docx`; Git blob `a0a79384dd3cfa22dd9b534e6d5ee25bb554d7df`; SHA-256 `60c25adf681f170f5298bcba7409869872479a7d62d9ac68f7328aabb16b05d3`; 36,494 bytes.

## Tested, locally and author-controlled

- Deterministic builder from `AOSP_R1_BRIEF_CONTENT.json` reconstructed the **exact Git blob SHA**, not merely visually similar content.
- LibreOffice-based visual review of **two A4 pages**: no clipping or overlap observed. Accessibility inspection: **0 high, 0 medium, 0 low** findings (semantic tests cannot measure actual comprehension).
- Read-only verifier: source schema, public owner/repository set, pinned SHA formats, six sequential method steps, four concrete cases, 11/92/70/16/44 claim ceilings, nondelegable authorization, XML/ZIP integrity and source-to-DOCX consistency.
- Physical copied-file mutation campaign: **15/15 detected, 0 survivors**, using source, scope, freeze, authority, denominator, DOCX absence/corruption and comparative-advantage falsifiers. Inputs are restored between cases.

## Reproduction from this PR branch

```bash
python research/decision-ready-assurance/tools/build_aosp_r1.py /tmp/aosp-r1.docx
git hash-object /tmp/aosp-r1.docx
# expected a0a79384dd3cfa22dd9b534e6d5ee25bb554d7df
python research/decision-ready-assurance/tools/verify_aosp_r1.py
python research/decision-ready-assurance/tests/test_aosp_r1_mutations.py
```

The builder has only Python standard-library dependencies. GitHub Actions and exact-HEAD required checks are **separate host observations**; this report does not claim their success before a current readback. More tests cannot turn the original MS-10 null comparator into a positive finding.

## External gates left open

Independent nontechnical and CTO readers have not been studied. Comprehension time, decision quality, false closure, actual compute/CI/human cost, external target runtime and approval/peer review remain `NOT_MEASURED` or `OPEN_EXTERNAL`. The document is a decision-aid candidate, not proof of a successful decision. R2 requires novel reader evidence, source change or a material counterexample; there is no automatic N.
