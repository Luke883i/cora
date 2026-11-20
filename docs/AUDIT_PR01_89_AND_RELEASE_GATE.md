# CORA PR #1–#89 — audit and release gate

**Baseline:** merged PR #89 and main SHA 298997878c449e72f9bfca0a05e40c00af922953 (20 November 2026). This is a GitHub metadata/source audit, NOT an independent runtime or human usability study. Machine-readable contract: ../.cora/contracts/dod/reader-cockpit-release-dod.json.

## Historical census

The GitHub PR list includes **89 PRs: 86 merged and 3 closed without merge** (#34, #80 and #85). Titles classify intent; they do not attest behavior, implementation quality or external authority. Subsequent implementation belongs in PR #90.

| PRs | Source-level trajectory | Unresolved limitation |
| --- | --- | --- |
| #1–#20 | Installable CLI, Git receipts and provenance, ontology, graph, guards, adaptors, bounded fuzzing | Partial consumer discovery, source is not product behavior |
| #21–#42 | README, claim evidence, CI, source DoDs, One-Run, offline dossier, release semantics | Proof vocabulary and review complexity increased |
| #43–#67 | Consolidation, ChatGPT handoff ZIP, cross-repo profiles, pilots, packaging and SBOM | Handoffs not executed code, reviewer decisions or external user trials |
| #68–#86 | Target portability, dependency/consumer graph, physical Git counterfactuals and contraction | Dynamic callers and side effects remain partially unknown |
| #87–#89 | JSON cockpit decisions, beginner README, capability-named tests, CI workflow naming | JSON choices lacked a real navigable cockpit; usability unmeasured |

**Current code inventory:** 71 declared CLI commands; 14 workflows; exact Git receipts, bounded semantic models, one-run source dossier, portable iteration ZIP, code and documentation tests. This is inventory and bounded evidence, not 71 independently certified product functions.

## Gap register — closure is noncompensatory

| Gap | Negative oracle | Corrective contract | State |
| --- | --- | --- | --- |
| First-time reader confuses ChatGPT method and installed engine | Source ZIP mistaken for runner | Product definition before commands, side-by-side table, recommended beginner METHOD_ONLY path | Source candidate |
| README overload | Critical authorization detail missed | Progressive disclosure, lists and short action table | Source candidate, external comprehension unmeasured |
| Cockpit has JSON choices but no navigable HTML | Click unavailable, no DoD-to-gap navigation | Render verified offline HTML through existing verify-process, local anchors and three non-executing choices | Source candidate |
| Archive spoofing and HTML injection | Forged ZIP or untrusted prose becomes executable markup | Reverify source receipt, escape text, strict CSP and no scripts | Tests and real CLI required |
| Stale session artifacts | Earlier ZIP read as current commit | Exact source SHA, latest verified round and fail-closed mismatch | Runtime tests required |
| Superficial scenario counting | A million IDs mistaken for semantic coverage | 12 interacting dimensions, seeded unique tuples, distinct expected-result oracle, repeat | Finite model, not target runtime |
| Product usability unknown | Static anchor PASS promoted to browser success | Independent novice/CTO click-and-task study | BLOCKED_EXTERNAL |
| Product and recovery unobserved | Git evidence promoted to target acceptance | Maintained target native tests, auth-denial, persistence and rollback | BLOCKED_EXTERNAL |
| Release authority assumed from CI | Author self-approves | Authenticated host controls, reviewer, signed artifact, rollback and publish decision | BLOCKED_EXTERNAL |

This table lists **identified** release-relevant gaps, not all possible unknown bugs or organizational risks. New evidence may add blocking leaves.

## Architectural options and decision

| Candidate | Advantage | Refutation |
| --- | --- | --- |
| README only | Minimal edit | Does not repair JSON-only cockpit navigation |
| New hosted cockpit | Rich UI | New server, trust, deployment, attack and maintenance boundaries |
| Native ChatGPT plugin | Seamless-looking | No evidence of an installed live runner or such user interface |
| **Offline verified HTML** | Minimal existing owner, clickable internal sections, no executable controls | Must survive hostile ZIPs, script injection, actual CLI replay and novice tasks |

Chosen: README first-screen editorial simplification; a **verified local offline HTML navigator** generated after One-Run ZIP replay; no new service, no new command family, no automatic replan or merge.

## Decision gates

- **G_SOURCE_CANDIDATE = R0 AND R1 AND R2 AND R3 AND R4.** History, reader front door, navigation, 1M reproducible typed model outcomes and all 14 workflows on the same final HEAD.
- **G_PUBLIC_RELEASE = G_SOURCE_CANDIDATE AND R5 AND R6 AND R7.** External novice/CTO usability, target-runtime and rollback evidence, authenticated host and independent release decision. The release gate is BLOCKED_EXTERNAL.
- One million refers to **1,000,000 distinct modeled combinations**, with 12 semantic dimensions, seed 883, two byte-identical replay reports and an independent deterministic oracle. It is not one million physical source mutations, a human trial or a general proof.
- A failure in any dependency, an unsafe HTML projection, stale SHA or missing external witness cannot be compensated by unrelated green tests. Do not infer permission from a source receipt.

## Release actions for beginners

1. Choose ChatGPT Project (method-only) unless an actual authorized Python/Git runner exists.
2. Create a real target repository and record its Git commit. The CORA source ZIP is only a reference snapshot.
3. Explain your desired outcome; derive AND obligations, negative tests and one reversible change. Execute only with separate authorization.
4. Produce a temporary session ZIP only from real local One-Run; verify the exact receipt and produce the optional offline cockpit HTML.
5. Open the HTML in a browser and navigate its anchors, DoD, gaps and next checks. Copy the proposed question to ChatGPT; links do not execute actions.
6. Require independent target observations, non-author review, authenticated host protection and a responsible release decision before public publication.

**Proof limits:** this document does not itself execute any step or attest reader comprehension. Keep scope differences between product, software and repository explicit.
