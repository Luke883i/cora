# ADR PR-05 — Closure and observational evidence certificates

**Decision:** combine immutable Git blob inventory (PR-02), declared ontology / conservative Python graph (PR-03), and partial manifest adapter claims (PR-04) under a **fixed, server-derived set of obligations**, not free-form assertions supplied by a requesting AI agent. Certify *positive, scope-limited statements only*. `safe_deletion` cannot pass without a complete future PR-06+ evidence program.

## Contract and statuses

`cora-closure-certificate/1` binds exact commit, requested artifact path and selector, underlying ledger digest and evidence-source hashes, per-obligation states and trace, resulting status, and domain-separated certificate SHA-256. `PASS_SCOPED` means only all mandatory *supported observational obligations* in the claim have positive evidence. `BLOCKED` means missing/unsupported/ambiguous obligations. `REFUTED` means authoritative counterevidence within the narrow declared scope, irrespective of other uncertainties. No result authorizes destructive changes.

Certifying an observation does not imply future validity, proof of runtime use, absence of external consumers, or correctness of a software transformation. A self-hash is insufficient: `verify-certificate --repo` recomputes all claims from Git objects for the same commit. This is not a signature against compromise of the Git repository or executor.

## Retrograde local DoD

| DoD | Requirement | Test witness |
| --- | --- | --- |
| C05-L1 | Fixed claim registry and non-bypassable required obligation IDs | no caller-provided facts; injection/re-sign rejection |
| C05-L2 | Three-way `PASS_SCOPED` / `BLOCKED` / `REFUTED` | real-commit fixtures; precedence tests |
| C05-L3 | Strict provenance and revalidation | corrupted / re-signed receipt rejected against Git |
| C05-L4 | Cross-PR evidence convergence on same immutable commit | ontology / graph / adapter / ledger fixture |
| C05-L5 | Fail closed for dynamic / ambiguous / unobserved claims | dynamic import, missing dependency, symlink tests |
| C05-L6 | Safe deletion can never pass in PR-05 (existing file blocked; missing file refuted) | unconditional unsupported obligations fixture |
| C05-I1 | Independent Git oracle | real two-product Git repository with hand-authored expected outcomes |
| C05-I2 | Independent model decision oracle | bit-spec decision check + witness reconciliation |
| C05-I3 | Seeded one-million adversarial scenarios | 24 families, 20 toggled evidence axes, 1M unique vectors |
| C05-G | All PR-01–04 regressions / 0 mutation mismatches | install wheel / CI tests and double replay |

## Falsification and limitations

The synthetic corpus has 1,000,000 **distinct 20-bit evidence-state vectors**, 24 named architecture stress families (dynamic loaders, external consumers, migration, retention holds, CI links, etc.), and independently coded bit-rule oracles, replayed twice with seed `883`. The corpus does NOT contain a million different physical repositories, source trees, runtime paths or measured real-world semantics. The family/claim mapping and oracle draw on the same written fixture specification. Zero mismatches validate internal obligations but cannot prove soundness of every imported scanner. Many distinct 20-axis vectors have identical values on the smaller subset of obligations relevant to a specific claim; distinctness does not imply one million independent decisions.

The observation `declared_manifest_dependency` is not the same as installed or reachable dependency; `static_import_candidate` is not an exact call graph. Even a complete observed Git inventory is insufficient to infer safe deletion. PR-06 must introduce transactional changes, protected guard and non-regression obligations, and may only promote certificates as authorized by separate, versioned policy.
