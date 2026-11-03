# PR-19 retrograde R1–R4 / P01–P12 semantic DoD

Global human contract: `potenzia cora con gold mining; aggiorna prodotto, repository e software`. Preserve one CORA product, two canonical software IDs, one CLI, explicit evidence classes and non-authorizing change governance.

**R1 source**: G_GOLD_SOURCE = I_CONTEXT AND I_PHYSICAL AND I_EFFECT AND I_PILOT. **Governed**: G_GOLD_GOVERNED = G_GOLD_SOURCE AND I_EXTERNAL. The versioned graph has 16 local leaves L01–L16, five intermediate cuts and two global roots, 23 nodes total; L01–L12 are source obligations; L13–L16 require external host/human/runtime/rollback authority. Each local node has a named falsifier; P01–P12 are mapped to specific rails. No score averaging or self-issued waiver.

| Cut | Local failure modes and required falsifier | Scope |
| --- | --- | --- |
| I_CONTEXT (L01–03) | absent intent; ambiguous owner; missing dependency. Deterministic reverse cut, source owner marker and exact Git | source; ownership semantics unverified |
| I_PHYSICAL (L04–06) | simulated-only mutant; missing outcome classes; implicit execution. Real staged byte changes, positive baseline, syntax mutant and survived behavioral mutant; no automatic Docker | physical-source, not target behavior |
| I_EFFECT (L07–09) | hidden write; absent readback; self-approval. Workflow capability scan, host claim non-promotion | potential-effect, no observed effect |
| I_PILOT (L10–12) | single-repo overfit; stale SHA/blob; scope inflation. Three real Git checkout source-readback pairs, tampered/missing pin tests | six committed bytes, not runtime |
| I_EXTERNAL (L13–16) | absent protected branch; independent review; target runtime; rollback. Authenticated outside witnesses | BLOCKED_EXTERNAL |

Mechanical candidate gates: **D1** contract schema and 23 nodes, 12 patterns, 10 seeds, three pins; reject 16 family JSON mutations and 9 structural ones. **D2** reverse-derive 12 source / 16 governed leaves, preserve dependencies. **D3** FULL goal: exact Git commit/blob on all three separate pinned source checkout roots. **D3a** candidate CI: actual ICTC public readback (1/3). **D3b** private ikant and aosp1: **BLOCKED_ACCESS / NOT_OBSERVED**. No pass inflation from correct handling of missing access. Local Git fixtures test the mechanism, not actual private GitHub CI. **D4** physical source modification and independent oracle states killed/survived/timeout/inconclusive, baseline and no implicit target execution. **D5** potential effects cannot self-certify. **D6** two byte-identical 10M model streams with 12 singles+66 pairs per session, zero mismatches/unsafe promotions, zero novel tail signatures and zero physical mutants counted as model events. **D7** Python 3.11/3.13 new tests, cumulative regression and all final-HEAD CI checks plus README, roles, architecture and CLI contracts. **D8** actual target behavior/host reviewers/recovery are external and must remain BLOCKED.

D1–D2 and D4–D7 are eligible for **source CI PASS_SCOPED** only on exact final GitHub HEAD; full D3 remains **BLOCKED_ACCESS** until separately authorized private source readbacks. A green CI job for correct blocker detection is not a full D3 pass and cannot close G_GOLD_SOURCE. D8 cannot be closed by this PR. R2 genuine behavioral qualification, R3 authenticated CI side effects and R4 operational cross-repo pre/postmerge remain to be independently demonstrated. No Enterprise/production/release claim.

## Historical failure and constrained closure

At PR-19 prior candidate `c0af25a8`, 24 check runs passed and one failed: `gold-three-repo-source` stopped at the private ikant checkout (GitHub run 41674419549). No source mismatch was shown because the private source never arrived. Hardening replaces implicit cross-repository privileges with public ICTC replay and machine-checked 1-of-3 blockers. It also fixes a Linux permission mismatch between Docker user 65534 and private mode-0700 staging. R4 full is still external; positive source CI cannot compensate for source not observed.
