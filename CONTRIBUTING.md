# Contributing to CORA

**Document status:** CURRENT
**Current scope:** The active source/test/documentation contribution process.
**Operational use:** Submit a bounded PR with tests, risk and rollback obligations.
**Evidence:** Committed test cases, original Git source and CI results.
**Limits:** Instructions cannot enforce hosting permissions.


Start with [README](README.md) (what/why/how), [architecture](docs/ARCHITECTURE.md) (components and evidence flow), and [current product DoD](docs/DOD_V1_EXPERIMENTAL.md) (acceptance). The earlier [DoD](docs/DOD.md) is a historical source record, not current approval. CORA is a **single Python distribution**; avoid copying experimental R1–R7 ZIP trees or creating a second CLI.

Use Python 3.11+, install the current checkout (`python -m pip install -e .`), run `python -m unittest discover -s tests -v`, then `python tools/verify_repository_contract.py`. Keep smoke outputs in `/tmp` (or another directory outside this Git tree). Add explicit independent expected results for new language adapters, graph relations, or transformation behaviors; never treat zero model-oracle mismatches as production proof.

For each PR, state: claim and affected objects (product/software/repo), source commit, new and unresolved evidence, regressions and adverse fixtures, trust boundary, and a rollback or recovery plan. Link tests to local DoD identifiers. Keep the README current when a capability is introduced or removed; historical ADRs must not be used as substitutes for current product documentation. Never introduce destructive transforms, network dependencies, or auto-publishing without separate security design and explicit review.

PR review is not a substitute for independently required GitHub checks or protections. Any mutation of `.cora/`, `.github/workflows/`, verification scripts or publication controls requires human security review. See [SECURITY.md](SECURITY.md) for reporting.


## Self-assurance regression: bounded CORA -> CORA

For source changes to chat continuity, authorization, reticular DoD or selection,
run the *native* Git-bound suite with `python -m unittest discover -s tests -v`.
The optional `python -m pytest -q` collection excludes the third-party fixture
under `tests/fixtures/third_party`; it does not replace the original Git-native
suite. Work on an authentic checkout, not a Git-less ZIP or synthesized commit.

Run `python tests/cora_self_mutations.py --repo . --output /tmp/cora-self-mutations.json`.
The six **physical, disposable** mutations are expected to be KILLED by named
native assertions: chat-session identity, receipt authority, aggregate DoD
self-report, external AND leaf, writer-lock cleanup/rollback and no-delete
selection. Missing anchors, timeouts, import errors or unrelated failures
must not count as kills. Keep the JSON outside the checkout; review survivors,
source SHA and exact CI on the final branch HEAD. This test-only harness uses
existing CORA modules and native tests, not another assurance engine.

**DoD:** M1 identity mutant KILLED; M2 canonical full unit suite on original
Git ancestry plus clean pytest collection; M3 six bounded semantic guards
KILLED with negative control and no write to source; M4 final-HEAD CI and
independent review. A green source CI is not evidence of protected-host checks,
independent behavior, release or approval. Revert the two semantic commits for
rollback; do not merge automatically.

## Forensic and AI contributions

Any new dependency relation or runtime adapter must define a bounded claim schema, provenance, explicit unknowns, independent Git-fixture oracles and privacy/threat tests. AI text must remain a hypothesis, not an authenticated fact. High-risk changes require the human roles in [GOVERNANCE.md](GOVERNANCE.md) and independently protected review; source-controlled CODEOWNERS alone does not enforce separation of duties.

## v1.experimental artifact-role discipline

When adding or changing files, update `cora.artifact-roles.json` to preserve all independently justified roles, including combinations of software, test, contract, fixture or workflow. Use `cora artifact-audit`, `cora verify-artifacts` and `python tools/verify_artifact_roles.py` on the committed branch. Role declaration means accountable intent, **not** demonstrated test execution or absence of consumers. Cite [v1 experimental DoD](docs/DOD_V1_EXPERIMENTAL.md) and require an independent reviewer for governance, release, security, retention, destructive workflows or contract changes.

## Debt and process DoD

Run `python -m unittest discover -s tests -q`, `python tools/verify_repository_contract.py --repo .`, and the dedicated `test_debt_governance.py` fixture suite before requesting review. For a new debt rule, document its AST/Git/third-party provenance, uncertainty, false-positive counterexamples, review category, owner role and a non-destructive remediation hypothesis. The `full` process must never execute repository scripts, AI models, or automatically remediate findings. CI must pass on the exact reviewed commit; branch protection must be separately configured and verified.

## Continuous PR and coding-agent contract

After committing a proposed change, use `cora dev-premerge . --base BASE --head HEAD --output /tmp/pre.json` and `cora verify-dev-gate /tmp/pre.json --repo .`. Every PR must distinguish source-bound facts, tests independently executed, agent assertions, unresolved runtime/consumer questions and human reviewers. An agent may submit a `cora-agent-proposal/1` record for `cora agent-check`; the result is **never** approval or verified test execution. After integration, `cora dev-postmerge` records source drift and optionally compares debt signals. Consult [AGENTS.md](AGENTS.md) and [continuous DoD](docs/DOD_CONTINUOUS.md). Do not assume branch protections exist merely because CI files are present.

## Current documentation and contextual PR requirements

Use the [README](README.md), [documentation index](docs/INDEX.md), [documentation DoD](docs/DOCUMENTATION_DOD.md) and [parser-complete CLI reference](docs/CLI_REFERENCE.md). Register every Markdown in `docs/documentation-registry.json`; preserve historical ADRs and audit text. Run `python tools/verify_documentation.py --repo .` and the regression suite. The README explains product value and is no longer the exhaustive command catalog.

An AI coding PR needs actual BASE/HEAD, a declared `--intent`, a committed target ontology and trusted BASE policy before `dev-premerge --contextual`; replay with `verify-contextual-gate` using the same intent. Independent target tests and protected reviewer decisions remain outside the CORA source receipt. See [agent adoption](docs/AGENT_ADOPTION.md).
