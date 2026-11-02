# Contributing to CORA

Start with [README](README.md) (what/why/how), [architecture](docs/ARCHITECTURE.md) (components and evidence flow), and [DoD](docs/DOD.md) (acceptance). CORA is a **single Python distribution**; avoid copying experimental R1–R7 ZIP trees or creating a second CLI.

Use Python 3.11+, install the current checkout (`python -m pip install -e .`), run `python -m unittest discover -s tests -v`, then `python tools/verify_repository_contract.py`. Keep smoke outputs in `/tmp` (or another directory outside this Git tree). Add explicit independent expected results for new language adapters, graph relations, or transformation behaviors; never treat zero model-oracle mismatches as production proof.

For each PR, state: claim and affected objects (product/software/repo), source commit, new and unresolved evidence, regressions and adverse fixtures, trust boundary, and a rollback or recovery plan. Link tests to local DoD identifiers. Keep the README current when a capability is introduced or removed; historical ADRs must not be used as substitutes for current product documentation. Never introduce destructive transforms, network dependencies, or auto-publishing without separate security design and explicit review.

PR review is not a substitute for independently required GitHub checks or protections. Any mutation of `.cora/`, `.github/workflows/`, verification scripts or publication controls requires human security review. See [SECURITY.md](SECURITY.md) for reporting.


## Forensic and AI contributions

Any new dependency relation or runtime adapter must define a bounded claim schema, provenance, explicit unknowns, independent Git-fixture oracles and privacy/threat tests. AI text must remain a hypothesis, not an authenticated fact. High-risk changes require the human roles in [GOVERNANCE.md](GOVERNANCE.md) and independently protected review; source-controlled CODEOWNERS alone does not enforce separation of duties.
