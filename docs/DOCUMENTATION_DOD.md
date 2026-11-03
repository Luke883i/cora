# CORA documentation semantic DoD

The [machine contract](../cora.documentation-dod.json) defines 28 nodes: 18 source obligations, three independent external obligations, five intermediate cuts, and two global roots.

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
