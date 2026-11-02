# Audit of merged PR-01–07 and controlled hardening backlog

**Review baseline:** `Luke883i/cora` main `2d513155155cfd4ef805a8b86b3e05d00023e02f`, reviewed 2026-11-02. All PR-01–07 are merged. The code and local CI evidence, not previous conversation or PR marketing, determine supported claims. This audit does **not** claim a complete independent security assessment.

## Genealogy and observed evidence

| PR | Verified implemented object | Validation boundary / unresolved part |
| --- | --- | --- |
| 01 | One installable Python package, working-tree inventory, product-root declarations, 1M synthetic model checks | Repo != product; no dead-code oracle |
| 02 | Git snapshot, per-record/ledger hashes, source revalidation, uncertain blobs | Commit bytes are not trusted runtime behavior or publisher identity |
| 03 | Committed ontology, typed graph, Python AST import candidates and explanations | Partial static resolution only; not complete dependency graph |
| 04 | Versioned partial parsers for six manifest types, unresolved/unsupported reporting | Declared != resolved, installed or executed dependency |
| 05 | Fixed bounded evidence closure, `PASS_SCOPED`/`BLOCKED`/`REFUTED` and Git certificate revalidation | No certificate for safe deletion |
| 06 | Exact tracked-document-path rename with test/rollback, vendored Git/AST local guard | Only owned file rollback; verifier unsandboxed; local guard must not self-trust |
| 07 | Wheel/sdist candidate build, local source parity, two synthetic Git fixture installations, 24 actual archive mutants | Not a signed/published or independently production-tested release |

Tests to date include increasingly large **synthetic** mutation corpora with explicit seeds and independent real Git *fixtures*. Millions of model vectors do not increase external validity by themselves. No evidence establishes correctness on a representative sample of third-party production repositories. Do not report synthetic zero mismatch as zero real-world false-positive probability.

## Actual hardening findings and disposition

| Finding | Severity / proof | Action and required acceptance | Status |
| --- | --- | --- | --- |
| **H-01 Guard bootstrap bypass** | **High, reproduced:** selecting a base commit without `.cora/policy.json` and modifying `.cora/verify.py` produced `PASS_SCOPED` with empty violations | Fail closed on bootstrap and protected control changes, with actual Git regression fixture | Addressed by this PR if CI succeeds |
| **H-02 Self-authored guard lacks independent enforcement** | **High, architectural:** change to `.cora/verify.py` or workflow can alter its own verdict | Require protected status checks/ruleset and non-author review externally; do not claim it is configured | **BLOCKED** — host administration/plan not verified |
| **H-03 README misleading chronology** | **Medium, observed:** README began with PR-01, repeated synthetic 1M results, and referred to superseded Draft states | Replace with current product/software/repo contract and concise capability, quickstart and caveat map | Addressed by this PR |
| **H-04 CORA lacked committed self-ontology** | **Medium, observed:** `cora graph .` required a manually supplied `cora.ontology.json` | Add self-ontology, test graph against commit and verify product/software distinct | Addressed by this PR |
| **H-05 Missing first-read and reproducible doc contract** | **Medium, observed:** no CI proof that README can orient new engineer | Static README/link/CLI contract gate + independent human 5-minute test | Automatic part addressed; human **PENDING** |
| **H-06 Repository security/disclosure and contributor guidance absent** | **Medium, observed:** no SECURITY.md or CONTRIBUTING.md | Add scope-conscious policy, support caveats and contributor checks | Addressed by this PR |
| **H-07 Signed provenance, branch protection and external pilots absent** | **High, evidence debt:** source hashes/release archives are unsigned local claims; ruleset read returned GitHub 403 for private repo tier | Do not promote to production / universal. Require independent review, release controls and real maintainer-owned pilot repositories | **BLOCKED** |
| **H-08 Tool invocation and untrusted repository semantics** | **Residual design risk:** user verifier may execute arbitrary code; Git/manifest scanning and adapter parsers intentionally partial | Sandbox or isolate execution in future, harden Git data limits, add external-consumer evidence and threat-model tests | **OPEN** |

The ruleset endpoint returned a GitHub 403 referring to plan/public visibility. This is **not evidence that protections are enabled or disabled**: verification is inaccessible from this connection. The PR must not claim the guard cannot be bypassed at hosting level. A private vulnerability-reporting channel was likewise not verified.

## Standards crosswalk — guidance, not certifications

| Standard/guidance | Relevant control | Here and remaining gap |
| --- | --- | --- |
| OpenSSF OSPS Baseline **v2026.08.28** | Primary branch protections, vulnerability-handling, traceable releases | CI and disclosure guidance added; independent branch protection and reporting channel not evidenced |
| GitHub Actions security best practices | Full commit SHA pinning, least-privilege token, trusted required checks | Actions in current workflows SHA-pinned and `contents: read`; protections/check immutability external |
| Python Packaging User Guide (PyPA) | `pyproject.toml`, wheel/sdist, reproducible installs | PR-07 builds and compares local archives; signed attestations and controlled publishing remain open |
| Diátaxis + Read the Docs documentation guidance | Short orientation and paths to explanation/reference/how-to | README is entry point; architecture, DoD, contribution and security docs separated; human first-read still necessary |

References: https://baseline.openssf.org/ ; https://docs.github.com/en/actions/reference/security/secure-use ; https://packaging.python.org/en/latest/flow/ ; https://diataxis.fr/ . These standards are used as **falsification criteria**; passing local tests is not a statement of compliance, OSPS certification or official external assessment.
