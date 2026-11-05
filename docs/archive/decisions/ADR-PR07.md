# ADR PR-07 — Release candidate packaging and external fixture validation

Status: review candidate. Prerequisite: PR-06 merged on `main`.

## Decision

CORA 0.7.0a1 remains an **experimental alpha**, not a general enterprise-safe refactoring engine. PR-07 constitutes build tools and release **verification**, but does **not** publish to PyPI, create a GitHub Release or tag, register a trusted publisher, or issue a signed attestation. The name `cora-audit` remains provisional for any future public index distribution.

Versioned artifacts: one pure-Python wheel with one installed `cora=cora.cli:main` console entrypoint, one sdist, SHA-256 digests and a machine-readable release audit. The release verifier validates metadata name/version and Python requirement, source/wheel/sdist byte equivalence for 18 Python modules, license, wheel `RECORD`, path safety, symlinks, unsupported wheel payload and missing/altered files. Both artifacts are rebuilt with normalized timestamps; same-source/same-toolchain byte identity is tested in CI. This is **not** supply-chain signing, guaranteed reproducibility across independently managed builders, or an identity proof against an adversary controlling the trusted source checkout.

`tools/external_validate.py` installs the wheel and sdist in **separate virtual environments** with PyPI index access disabled. Wheel environment is isolated; offline sdist environment exposes the builder's preinstalled `setuptools` via a local `.pth` file and is therefore not hermetic. The installed CLI then audits two Git repositories constructed from separately authored fixtures: a Python repository with two products and shared software, and a JS/Go/Docker repository. Expected dependencies, graph edges, blob counts and unresolved capabilities are declared independently of the engine. **These are synthetic independent fixtures, not external production repositories.**

The CI job is a PR-only or manually triggered **non-publishing** verifier, with `contents: read` and pinned GitHub actions. It uploads short-lived artifacts for review but has no `id-token: write`, packages, releases or publishing permissions. A separate future reviewed workflow should use GitHub's supported artifact attestation if enabled for the private repository and PyPI Trusted Publishing with a protected environment, rather than project secrets. No attestation is claimed for PR-07.

## Reverse-derived DoD

| DoD | Requirement | Proof |
| --- | --- | --- |
| R07-L1 | One Python distribution, one CLI, pinned release candidate version | wheel metadata/entry points |
| R07-L2 | Safe artifact layout and content integrity | archive traversal, tampering, RECORD verifier |
| R07-L3 | Source/wheel/sdist parity | module hash registry and license parity |
| R07-L4 | Reproducible build for fixed source/toolchain | two builds, identical wheel AND normalized sdist |
| R07-I1 | Actual isolated install from wheel | fresh venv, offline package index, CLI invocation |
| R07-I2 | Actual sdist install with disclosed offline builder | separate venv, no index, Git fixture invocation |
| R07-I3 | Independently authored expectations on two unrelated Git fixtures | Python ontology and JS/Go oracle |
| R07-I4 | Real artifact mutants must be rejected | 24 actual corrupted/re-signed wheel and sdist cases |
| R07-I5 | One million distinct pre-seeded **model** risk vectors | 24 categories; 2 deterministic replays; oracle |
| R07-G1 | No regressions PR-01 to PR-06 | complete CI unit suite |
| R07-G2 | Reproducible CI on Python 3.11 and 3.13 | release verification matrix |
| R07-G3 | Review required before any public publish | Draft PR; no publish workflow |

## Known evidence debt / release blockers

- No third-party independent production repository pilots or measured false-positive rates, despite two separately authored Git fixture repositories.
- No signed build attestation, hermetic build environment, independent builders, lockfile/pinned backend SHA or verified public package-index name.
- No semantic equivalence for arbitrary source code, no proof that unseen dynamic/external consumers are absent, no safe-deletion authority.
- Exact document rename and local guard remain the limited experimental PR-06 feature set; their safety properties must not be overstated by a successful packaging gate.
- Test coverage is bounded to Python 3.11 and 3.13 on Ubuntu hosted runners; other interpreters, operating systems and platforms remain unverified.

## Falsification scope

One million mutations are **distinct 20-axis in-memory contract states**, not one million wheel/sdist files, commits, Git repositories, builds, or runtime paths. They include realistic packaging and supply-chain hazard names across 24 families, with family-specific obligations and a separate bitmask oracle derived from the same stated contract. Only **24 actual modified distribution archives** are constructed and tested. Report both numbers, never conflate them. Zero mismatches do not prove global soundness.
