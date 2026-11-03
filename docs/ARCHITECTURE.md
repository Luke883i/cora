# Architecture — CORA as product, software and repository

**Scope:** CORA v1.experimental (1.0.0a1 prerelease), built through PR-01–07. The [README](../README.md) is the front door; this document is the engineering explanation. The [committed ontology](../cora.ontology.json) is a *declaration* by project maintainers, not an inference from folder names.

## Three non-equivalent boundaries

- **Product `cora`:** externally usable capability and observable contract of a local evidence-first CLI. Its ownership may encompass multiple software components and repositories in the future; its *current* canonical source is this Git repository.
- **Software `cora-engine`:** Python modules under `src/cora/`, served by the single `cora.cli:main` entrypoint. It implements only the bounded features listed below. **Software `cora-release-verification`** is tooling under `tools/` for building/checking artifacts; it is not a production backend.
- **Repository `Luke883i/cora`:** one Git source and change-provenance boundary containing product declarations, Python software, tests, contracts, ADRs, CI and release-candidate workflow. A repository is neither a deployed instance nor proof of complete product boundaries.

Deployables: **wheel** and **sdist**, presently review-only, not public releases. Runtime: on-demand CLI process in a user's environment. Artifact: content-addressed file/record/certificate associated with a commit. No daemon, SaaS backend, central registry, dashboard or scheduled runtime is provided.

## Component map (what each module really does)

| Module | Role | Evidence or safety boundary |
| --- | --- | --- |
| `cli.py`, `__init__.py` | One package entrypoint and version | No alternative API/daemon claimed |
| `audit.py` | Working-tree filesystem inventory, declared ownership | No runtime or dynamic dependency closure |
| `git_snapshot.py`, `evidence.py` | Committed Git blobs, canonical records, ledger and domain-separated digests | Git provenance is not independent signing |
| `ontology.py`, `graph.py` | Validated declared products/software, typed graph, partial Python AST candidate imports, path explanations | No proof of complete imports, reachability or execution |
| `adapters.py` | Partial manifest readers for Node, Python, Rust, Go and Maven | Declared dependencies, not installed/used dependencies |
| `closure.py` | Fixed narrow observational obligations and counterexamples; Git-revalidated certificates | `PASS_SCOPED` is **not** authorization to delete |
| `file_lab.py`, `artifact_roles.py`, `file_lab_stress.py` | Multi-scale read-only per-file dependency dossier, untrusted AI/runtime annotations, human triage intents, synthetic falsifier | No automatic dead-code proof, calibrated probability, external runtime attestation or deletion |
| `transform.py` | Exact tracked-document path plan, approval, check, owned-file compensating rollback | Not syntax-aware source refactor; user verifier is untrusted/unsandboxed |
| `guard.py`, `guard_runtime.py` | Vendored local Git/AST boundary check and workflow | Cannot self-enforce against modification; depends on trusted required checks |
| `mutations.py`, `mutation_evidence.py`, `graph_stress.py`, `adapter_stress.py`, `closure_stress.py`, `transform_stress.py` | Deterministic synthetic oracles | Independent real-world source truth *not* established by large case count |
| `tools/build_candidate.py`, `release_verify.py`, `external_validate.py`, `release_stress.py` | Reproducible candidate packaging, archive checks, isolated installs and fixture tests | Not signed provenance, published release or external production validation |

## Evidence flow, from immutable source to scoped answer

```text
Git commit -> snapshot/ledger -> declared ontology + partial adapters
                              -> typed graph / unresolved findings
                              -> closure with mandatory obligations
                              -> PASS_SCOPED | BLOCKED | REFUTED
```

A single recorded evidence digest *traces a claim*, not a cryptographic attestation of an external reality. Graph edges are typed as declarations/candidates, not generic "usage". `REFUTED` is relative to a claim and a named commit. An empty graph path is not a deletion certificate.

The optional **maintenance** path is deliberately separate: clean Git worktree -> read-only document rename plan -> explicit digest approval -> controlled owned-file changes -> user-specified test command -> owned-file hash validation -> receipt or compensating rollback. The local guard monitors selected Git/AST changes and must be protected by an independent required check in the hosting platform.

## Repo navigation / novice engineer challenge

Starting at the root, an engineer should find answers without prior PR history: What is CORA? What is deliberately not supported? How do I install and audit a repo? Which source modules implement the capabilities? What evidence proves the last revision? Where do I run tests and report security issues? The [README](../README.md) answers the first three; this map and `src/cora/` answer the next; [DoD](DOD.md), `tests/`, `.github/workflows/` and [security](../SECURITY.md) answer the rest. Automatic checks validate links and commands; genuine human comprehension requires the independent first-read review described in [DoD](DOD.md).

## Artifact roles are not file name inference

`cora.artifact-roles.json` declares overlapping artifact roles for the immutable Git tree. A file may simultaneously be implementation, executable test, contract verifier, fixture and governance mechanism. The role declaration is not proof that the test passes, that a contract is enforced in CI, or that runtime consumers have been observed. The `artifact-audit` command reports unclassified files and unused rules; `verify-artifacts` independently recomputes the report from Git. An incomplete role registry is **not** a deletion oracle.
