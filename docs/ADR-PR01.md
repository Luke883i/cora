# ADR PR-01 — Canonical package constitution

**Decision:** one Python distribution (cora-audit), one CLI (cora), one source package (src/cora); read-only by default. No AI model and no network required. No vendored old R2-R5 ZIPs in source tree. Do not describe alpha packaging as R5 feature parity.

**Identity:** repository = Git versioning boundary; product = owner-declared set of capabilities; software = implementation components; directory = a container, never a product inference by itself. PR-01 validates only owner-declared roots/entrypoints and file inventory.

**Semantic commits:** bootstrap main (necessary for initially empty GitHub repo); build(package) creates canonical package; feat(inventory) defines read-only baseline; test(stress) adds deterministic adverse mutation harness; docs(gates) records DoD and limits.

**DoD-01 pass:** installed cora resolves to cora.cli:main; no competing entrypoint; test suite green; run 1M model mutation evaluations; zero mismatches against independently curated category expectations; result digest stable on rerun.

**Not demonstrated:** complete R5 capability migration; independent 1M repository mutations; runtime reachability or deletion equivalence; full Python/JS/Go/etc dependency graphs; historical Git snapshot; production readiness.

**Follow-on:** PR-02 evidence ledger and Git snapshot; PR-03 semantic graph; PR-04 adapter coverage; PR-05 closure certificates; PR-06 verified transformations/guard; PR-07 distribution, ecosystem pilots and external validation.
