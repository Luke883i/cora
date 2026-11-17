# R2 editorial audit — bounded evidence, actual negative result retained

Date: 17 November 2026. Object: the new English four-page guide, `ENGLISH_FIELD_GUIDE_R2.docx`. Its author-controlled source is `BRIEF_SOURCE.json`; Git-bound public evidence lives in `EVIDENCE_PINS.json`. MS-10's scientific baseline and null comparator are unchanged.

## Editorial judgment, not synthetic readership

The 15 noncompensatory editorial principles in `EDITORIAL_DOD.json` cover plain-language problem framing, defined terms, six-stage method, retrograde AND requirements, exact Git objects, negative oracles, typed statuses, finite no-novelty saturation, screenshot-to-DOM-to-runtime inferences, source pins, public-only cross-domain cases, bounded science, and a CTO decision rule.

**Compression trade-off:** four A4 pages (two pages of method/case, one of computational mechanisms, one of evidence/CTO gate) rather than forcing the full evidence ladder and causal limitations into a two-page marketing sheet. Page-specific headings, three *editable Word-native* table diagrams, a nine-project map grouped by seven rows and 18 clickable anchored source links support progressive disclosure. This does not establish that an unfamiliar reader can actually understand the prose; that needs independent testing.

**Real screenshot evidence boundary:** the ICTC public register records 15 screenshot references, 12 issue groups and 28 granular findings (22/6 owned); the original 15 image bytes were not observed in the pinned public main tree. Therefore the guide reconstructs a source-bounded example of screenshot-derived issue semantics and concrete `frame.after(rail)`/DOM parent checks, not an independently replayed pixel audit. The 1M ICTC scenario model does not run 1M browsers.

## Falsification of the field guide

- Corpus: `MUTATION_CATALOG_100.json`, 20 risk families × five distinct wrong edits to independent fields of actual `BRIEF_SOURCE.json`; the model fixes 20 required anchors and separately lists forbidden semantic promotions.
- V0 finding: **99/100 detected**, `M086` survived because the false promotion "Native EDU/MCP equivalence proven" still contained the anchor "Native EDU/MCP equivalence". The exact failure is preserved in `MUTATION_RESULT_V0_99_OF_100.json`.
- Repair: add a negative semantic entailment/prohibition gate to the independent oracle, **without changing the mutated source or the original comparator**.
- V1 replay: **100/100 killed**, zero survivors and ten benign text controls accepted in an author-controlled in-memory JSON harness. The bundled Python `tools/replay_100.py` is designed to physically materialize a separate JSON file for each selected mutation and test its extracted claims against the unchanged authored oracle. That independent local disk replay and its hash receipts must be read from actual execution; the V1 JSON report does not pretend to be that receipt.
- The tests detect selection-specific violations; they do not evaluate all possible editorial falsehoods, scientific novelty, real human comprehension, live deployment or screenshot pixels.

## Pinned decision science

MS-10: 11 purposively chosen PRs, 92 applicable obligation slots, 70 unobserved **in the dossier**, equal checklist/EC-03 decisions on 16/16 finite fixtures, 44 modeled briefings and zero human test participants. Source-only and external scope cannot compensate for each other. PR73 remains a draft; review, publication, technical qualification and successful adoption are not attested.

## Reproduction on a verified checkout

```sh
python research/decision-ready-assurance/aosp-r2/tools/replay_100.py --out /tmp/r2-replay.json
git hash-object research/decision-ready-assurance/aosp-r2/ENGLISH_FIELD_GUIDE_R2.docx
# Expected: ffa99d46c315258f3dc7cb8067e039b7c3ce3741
```

Commit identity, native CI on the final HEAD, rendered page inspection, independent editorial comprehension and external authorization are different evidence gates. The very next addition must preserve their status instead of converting this local mutation result into proof of reader benefit.
