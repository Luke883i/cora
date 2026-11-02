# ADR PR-04 — Adaptive adapter contracts with explicit coverage

**Status:** proposed; PR-03 merged baseline. **Principle:** parsers must never silently promote absence of extracted declarations to absence of dependencies.

## Decision

CORA introduces a language-agnostic evidence contract `cora-adapter-report/1`, with adapter name + version, Git commit, PR-02 ledger digest, source record digest, extracted dependency declarations, machine-readable unresolved causes, declared capability coverage and a domain-separated SHA-256. A `verify-adapters` operation recomputes the output from source Git objects and rejects forged reports even if a self-hash has been recomputed.

Use only standard-library, bounded parsers: Python JSON/TOML, exact requirements line handling, simplified go.mod require extraction, Maven XML with DTD/ENTITY rejected. Runtime resolution, dynamic package registries, Docker and workflows are explicitly unsupported. A parser may be partial; it must declare its limitations. No execution of target repository code, scripts or build tools.

## Backward-derived DoD

| Local contract | Condition | Witness |
|---|---|---|
| A04-L1 | Versioned adapter registry with declared coverage | `SUPPORTED` + report catalog |
| A04-L2 | Immutable evidence provenance | Git snapshot commit + record digest |
| A04-L3 | Unsupported technologies are not ignored | Workflow/Docker/.csproj fixture |
| A04-L4 | Malformed or indirect forms cannot be marked resolved | parse-error, workspace, source and pip include fixtures |
| A04-L5 | Dependency extraction claims are bounded | `claim=declared_only` |
| A04-L6 | Re-signed forged reports are rejected | recompute report from Git contents |
| A04-I1 | End-to-end multi-ecosystem oracles | 9-file independently authored Git fixture |
| A04-I2 | 1M pre-seeded, serialized distinct synthetic inputs | 24 families; independent template expectations |
| A04-I3 | Reproducibility and regression | repeat byte-identical runs + PR-01..03 suite |

## Disqualifiers

Claims of runtime consumption, dependency lock resolution, executed CI workflow, completeness of ecosystem code graph or safe deletion are prohibited. The million-case synthetic oracle shares fixture-generation assumptions; it is not independent validation on a million live repositories. Distinctness is measured on serialized manifest bytes, not computational paths. The results do not imply that unknown dependencies are absent.

## Follow-on

PR-05 closure engine must account for source uncertainty; PR-06 guard/transformations cannot promote adapter results into destructive authorization. Later PRs may extend the registry with pinned, sandboxed scanner integrations that return the same contract.
