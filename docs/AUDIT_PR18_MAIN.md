# PR-18: CORA-on-CORA severe historical and reticular audit of PR-17

**Canonical history:** PR-16 merged into main `4f175ccf5c3f392433ef8179e48d5c720a75134d`; PR-17 comprised nine distinct semantic commits, final head `f568db2f14b9ed1cef95fdc5a57ed2c35df0d99a`, merged as `268f10c9d8ce267f9aed85e9fd931180f58386fb`. Git parentage establishes integration, not deployed product quality or independent runtime validation.

## Historic causal sequence and what was actually built

PR-14 delivered base-pinned pre/post-merge governance; PR-16 added ZIP input, optional Docker execution, source/runtime receipts and typed lattice; PR-17 added `cora.agent-dod.json` (24 abstract fault families, four intermediates, two globals), `agent_assurance.py` (backward requirements/claim replay), `agent_saturation.py` (10×1M finite bitmask scenarios), four commands, 34 temporary mutated policy JSON fixtures, CI and documentation. This is an implemented **agent governance model**, not automated proof of business-product correctness, real maintained repositories or LLM semantic validity.

## Source-demonstrable false coverage claim

The original stress loop recorded `exposures.add(i)` and `observed_pairs.add(PAIRS[i-24])` **regardless of the actual mask returned by `_scenario`**. An injected generator returning zero would still receive the historical 24/24 and 276/276 positional coverage counters. This does not mean the original unchanged generator was faulty; it means the former verification oracle was not sensitive to that regression. PR-18 counts the actual prespecified masks, refuses sequence mismatches, verifies diversity and kills source-code mutants that bypass model checks.

## Epistemic cross-layer reticulum

| Layer | PR-17 supported capacity | PR-18 additional falsification | Remaining debt |
| --- | --- | --- | --- |
| LOCAL (L01–L06) | typed source/owner/acceptance descriptions | verified generated single faults | real per-repository owners and consumers |
| INTERMEDIATE (L07–L12) | AND prerequisite cuts and descriptions of independent tests | 276 actual 2-fault masks and mutated oracle | behavioral target-code oracles |
| GLOBAL (L13–L18) | base/head, CI, postmerge requirements | first unresolved falsifier, source mutation regression | host-specific full-lifecycle proof |
| EXTERNAL (L19–L24) | blocked independent authorities | external claims always remain BLOCKED_EXTERNAL | real authenticated branch protection/reviewer/pilot |
| SATURATION | ten deterministic 1M streams | mask-based coverage, diversity, negative source mutants | neither probability nor universal semantic completeness |
| EVIDENCE | digest/replay, untrusted agent claims | whitespace-only witness blocked, altered next-falsifier receipt rejected | digest != signature and claim != execution |

**Non-compensatory DoD:** H_SOURCE = H1 historical exact source + H2 actual-mask coverage + H3 no external/self-assurance promotion + H4 six physically modified CORA-model Python modules failing independently written gates + H5 same-final-HEAD Python 3.11/3.13 CI and two byte-equal 10M finite-model receipts in each environment. H_GOVERNED = H_SOURCE AND H_EXTERNAL, and H_EXTERNAL remains BLOCKED until independent review, enforced branch rules, genuine target pilot, sandbox and rollback evidence are observed. The six source mutants are changes to **CORA's model implementation** in temporary files, not production-target mutations; original 34 were policy JSON mutants.

## Methods mined from other repositories, with limits

ICTC PR-183 models 10-session semantic saturation and novelty tails, PR-212 supplies intent-to-proof continuity, and PR-232 insists on *real product-source* mutation gates rather than model-volume proxies. iKant_LE PR-190/200 use reverse derivation with external provider evidence left open. CORA borrows the structure, not their untransferrable test executions or empirical truth.

## Next hardening / fine tuning

Prioritize independent labeled repository benchmarks, real target-code mutation testing, source-to-runtime provenance, timeout/performance budgets, false-positive and false-negative classification, reviewer attribution and post-merge checks on **merged main** rather than former PR HEAD. Policy declarations are not the hosting ruleset. Model saturation of its finite 24-fault ontology is not global semantic completeness, an automated merge permission or a release verdict.

**Source precedence:** Git objects/current source and same-SHA run results supersede PR prose; PR prose supersedes conjecture. This document is an audit contract, not an execution record.
