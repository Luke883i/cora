# CORA instructions for coding agents

CORA is the independent **engineering evidence and governance framework**, not the AI coding assistant that implements features. The agent may plan, write, test and propose a PR; it may not certify its own source claims as runtime truth, authenticate reviewers, grant its own authorization, merge, deploy, publish or delete source under CORA authority.

Start at the [README](README.md), [agent adoption tutorial](docs/AGENT_ADOPTION.md), [continuous method](docs/CONTINUOUS_DEVELOPMENT.md), [convergent assurance](docs/CONVERGENT_ASSURANCE.md), and [governance](GOVERNANCE.md). Existing historic PR-level DoDs and audits remain source-context records, not parallel engines.

## Mandatory current workflow

1. **Intent** — obtain the user's material product outcome, acceptance criteria, target owner, impact and independent test oracle. Treat caller-supplied intent as a claim, not authenticated approval.
2. **Observe** — inspect actual target main and committed product/software ontology, source roles, Git history and baseline policy. Pin exact BASE and candidate HEAD; never substitute a working-tree observation for committed Git source.
3. **Retrograde qualification** — derive the global/intermediate/local DoD with `cora convergence-plan` and relevant specialized policies. Select the first unresolved *real* obligation, not the highest synthetic coverage count. Reuse canonical modules; do not introduce another competing compiler.
4. **Bounded implementation** — materialize a reversible semantic slice, include independent positive and negative oracles, and preserve actual owner/consumer unknowns. No missing static import edge can certify non-use.
5. **Premerge source verification** — use the existing gate with `--contextual --intent "Specific change with acceptance criteria" --convergence-contract PATH` when the target has a committed ontology and BASE policy. Replay via `verify-contextual-gate` with the **same** intent. Legacy `dev-premerge`, `verify-dev-gate`, `agent-check` and `dod-assess` remain supported; their source claims never self-authorize.
6. **Actual tests and evidence** — run suitable target tests and, with explicit consent, physical mutations or isolated runtime checks. Capture SHA, environment, commands, outcomes, survivors, inconclusives and missing coverage. A source replay, model receipt or confidence range is not independent behavior.
7. **Governed PR** — link exact final-HEAD CI, changed-path blast radius, unresolved obligations and rollback; require independent reviewer and protected hosting controls for high-risk policy, security, CI, guard, release or retention changes.
8. **Postmerge** — inspect actual merged main SHA using `dev-postmerge --contextual --intent SAME_INTENT`; rerun relevant regression and invalidated witnesses, never reuse former PR-head evidence without revalidation.

**PR38 feature-change discipline:** Before adding a source module, CLI command, test, DoD or workflow, inspect the [37-PR genealogy](.cora/assurance/history/pr01-37-commit-diff-audit.json), reuse the original owner and prove that capability, role, DoD and CI catalogs still cover the exact HEAD. Historical workflow totals are baseline minimums, not current counts. New or moved paths must have reversible mappings; absent static imports cannot authorize deletion. Generate and replay the single comprehensive One-Run dossier, then obtain independent runtime/review evidence where required.

For documentation changes, also run the Git-bound S01–S18 proof verifier against the candidate HEAD and replay the receipt with the same exact Git revision. The profile is a source proposition register, not a substitute for review or the independent E01–E03 acceptance gates. See [documentation DoD](docs/DOCUMENTATION_DOD.md).

## Stop and boundary rules

- Missing/ambiguous owner, ontology, baseline policy, SHA, change intent, independent behavioral oracle, protected reviewer identity or required host controls remain **BLOCKED** or **BLOCKED_EXTERNAL**. Bootstrap cannot approve itself.
- A changed source invalidates dependent evidence; a not-invalidated witness still requires revalidation. Partial Python imports and product roles are *candidates/declarations*, not exhaustive runtime truth.
- Untrusted ZIP files and unknown repository scripts are not safe to execute by implication. Optional Docker test or caller verifier command needs explicit authorization; Docker flags are not independently attested host confinement.
- `gold-mutate` changes staged disposable bytes; AST-only checks are syntax checks. A survivor is not a kill. `gold-effects` identifies potential CI writes, not authenticated target readback.
- No private cross-repository token belongs in PR-editable workflows. A public ICTC 1/3 source check does not establish private ikant/aosp1 source or runtime outcomes.
- Ten-million-case campaigns are finite **synthetic fault-model evaluations**, not independent maintained-repository mutations or calibrated software quality measurements.
- AI hypotheses and user-provided runtime annotations remain untrusted until separately validated. Source hashes are not digital signatures; a green workflow does not show GitHub-required checks are enforced.

## Technical and historical references

Use [AI agent method](docs/AI_CODE_ASSURANCE.md), [PR-17 scoped DoD](docs/archive/dod/DOD_PR17_AGENT.md), [PR-18 counterexample](docs/archive/audits/AUDIT_PR18_MAIN.md), [Gold method](docs/GOLD_ASSURANCE.md), [PR-19 DoD](docs/DOD_PR19_GOLD.md), [PR-19 closure audit](docs/archive/audits/AUDIT_PR19_CLOSURE.md), [PR-16 ZIP/runtime DoD](docs/DOD_PR16_SEMANTIC_LATTICE.md) and [R1–R4 convergence DoD](docs/DOD_PR20_CONVERGENCE.md) for domain-specific responsibilities. [Documentation DoD](docs/DOCUMENTATION_DOD.md) governs the separation between current product information and historical source records.

## PR40 knowledge-convergence gate (merged source, independent gates outstanding)

Before claiming current CI success, inspect the exact candidate SHA's GitHub Actions, including failed diagnostics and skipped jobs. Treat GitHub required-check rules, reviewer identities and ruleset read failures as separate external observations. Run `python tools/verify_engineering_closure.py --repo . --revision HEAD --output /tmp/ekc.json` and its Git-bound `--verify-report`; pass `--stress-10m` only when the bounded 10-million-case finite campaign is intended. The report scans static AST callsites but does not execute runtime targets or independently validate behavior. PR25 clone failures must preserve their original stderr without retry or invented RCA. Use the original `process-run --one-run --profile comprehensive` for the integrated activity dossier; new tools must not grant merge, deletion or release authority.

## PR41 — final experimental release freeze is not permission

The final experimental source baseline must be pinned to the actual post-PR40 main ancestry and the [noncompensatory final DoD](.cora/contracts/dod/final-experimental-dod.json). Run `python tools/verify_final_experimental.py --repo . --revision HEAD --run-behavior --output /tmp/cora-final-source.json`, replay it, then separately run the 1M finite model. Actual independent maintained-target oracles, 8-person usability study, isolated hostile-code host, effective protected-branch checks, a distinct human reviewer and authenticated release manager are outside the source test. Until all seven EXTERNAL obligations and SHA-matched wheel/sdist/tag/rollback are witnessed by qualified operators, **do not approve, merge on the verifier's authority, tag, publish, rename to stable, or deprecate components**. A source-local report is never an administrator or human signature.
