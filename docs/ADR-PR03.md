# ADR PR-03 — Ontology and Explainable Graph Kernel

**Status:** Candidate; independent review required. **Base:** merged PR-02; schema version `cora-graph/1`.

## Decision

Maintain distinct entities for repository (Git commit), product (owner-declared capability boundary), software (declared implementation), and file (committed blob). The presence of a folder or filename is never sufficient to infer a product. Ontology must be a committed `cora-ontology/1` document read from the same Git commit as the PR-02 evidence ledger; editing it in the working tree does not change a graph for a fixed commit.

Provenance of `contains_file` references the PR-02 evidence record digest. Provenance of product/software memberships and declared entrypoints references the hashed committed ontology. Provenance of `static_import_candidate` references the importer blob digest and AST line. Every node and edge has a typed identity, and the graph is canonically sorted and domain-hashed.

Explainability: `cora explain` produces a deterministic shortest path of typed edges; reachability is **within this incomplete graph only**. No claim of runtime execution or safe deletion. Python AST parsing is partial; unknown dynamic, relative, ambiguous and external imports are explicit findings. No automatic mutation of target repositories.

## DoD and evidence

| Local DoD | Obligation | Proof |
|---|---|---|
| O03-01 | Reject invalid/duplicate ontological identities | strict validator tests |
| O03-02 | Bind ontology and software identities to immutable commit | Git fixture + dirty working tree invariance |
| O03-03 | Provenance for every node/edge and graph hash | deterministic evidence-linked record graph |
| O03-04 | Distinguish supported import candidates from unknowns | static AST and dynamic import fixture |
| O03-05 | Independent oracle for relationships | hand-authored expected edges for two-product/one-shared-software fixture |
| O03-06 | Independent algorithm for reachability | fixed-point oracle vs BFS, 24 mutation families |
| O03-07 | Repeat seeded 1M graph mutations byte-identically | seed 883, stream digest in CI |
| O03-08 | Preserve PR-01 and PR-02 interfaces and regression tests | GitHub CI |
| O03-09 | No deletion, runtime or complete multi-language assertions | scope and coverage fields |

The synthetic 1,000,000 cases mutate **in-memory topology**; they do not constitute 1,000,000 physical Git repositories or independent real-world software samples. The fixed-point oracle is a distinct algorithm but uses the same synthetic edge model: it tests graph reachability, not correctness of real import resolution.

## Known limitations

A Python static import is only a `static_import_candidate`; direct file mapping via `src/` and module names is intentionally incomplete and can be ambiguous when import roots overlap. Dynamic/relative imports are findings, not confirmed edges. Calls, dataflow, build/deploy, feature flags, package registries, external consumers and runtime observations remain unsupported. Follow-up PR-04 must define adapter contracts and coverage; PR-05 must prove closure before any scoped certificate.

## Release policy

Do not merge while CI, independent review or the DoD are unresolved. The merged source on `main`, not the experimental seed ZIPs, is authoritative.
