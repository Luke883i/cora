# CORA — Global, intermediate and local Definition of Done for selection

**Baseline:** CORA v1.experimental after merged PR-10. **Decision:** selection means **human investigation triage**, not proof of globally dead code or authority for deletion. A file is a versioned Git artifact with potentially overlapping software, test, verifier, workflow and retention roles. Absence of a parsed edge is not absence of a dependency.

## G* — requested strongest claim: IMPOSSIBLE AS A UNIVERSAL GUARANTEE

> For every possible heterogeneous repository, always identify every truly dead file and safely delete it without ever changing any externally observable behavior.

**Not achievable as a general total algorithm.** An arbitrary program may access a file iff another computation terminates; a total always-correct detector would then decide the halting problem. Whether a file is dead may also depend on unobservable future inputs, clients, deployment configurations, legal holds and secrets outside the repository. A finite number of tests, even millions of differing test vectors, cannot imply universal behavioral equivalence. **Do not create a badge, release claim or DoD mark asserting G* PASS.**

## G-selection — attainable global product contract (AND composition)

For any **supported Git-tracked single-file case**, CORA produces a deterministic, commit-scoped, explainable and source-reverifiable selection outcome, with no unsafe positive dead-file claim. It either retains a file on positive evidence, selects it for *investigation*, or blocks assessment when minimum identity/integrity evidence is missing. Every unclosed operational/consumer/retention/equivalence obligation is surfaced. No selection grants write or deletion authority. An unsupported repository must fail closed; it is not classified as safe by default.

`G-selection = I1 ∧ I2 ∧ I3 ∧ I4 ∧ I5 ∧ I6 ∧ I7`; no averaging between obligations. **Automated scoped acceptance** is possible; **independent external universal validation** is not claimed.

| Intermediate | Required local DoD | Witness | Human / external block |
| --- | --- | --- | --- |
| **I1 — Versioned identity** | L1 immutable commit; L2 Git blob status; L3 declared product/software identities; L4 multi-role artifact contract | PR-02 ledger, PR-03 graph, v1 role registry; real-Git tests | External consumer ownership not inferred |
| **I2 — Evidence graph** | L5 incoming candidate imports and declared entrypoints; L6 protected contractual roles; L7 explicit unknown layers; L8 no absence-as-proof | `file-lab`, `select-file`, exact path/role fixtures | Dynamic/build/deploy/registry/runtime closure missing |
| **I3 — Selection soundness (scoped)** | L9 `RETAIN_EVIDENCED` on observed static imports, entrypoints or declared protected roles; L10 `DEBT_BLOCKED` when graph/roles/objects unavailable; L11 `INVESTIGATE` only for a review queue; L12 zero `safe_deletion_proven` claims | `selection/1` state machine and Git fixtures | A protected declaration itself remains a claim, not behavioral proof |
| **I4 — Adversarial robustness** | L13 tampered and rehashed selection rejected; L14 dirty working tree irrelevant; L15 symlinks/absent files fail closed; L16 AI or user runtime claims never laundered into source verification | `verify-selection`, real Git negative tests | Signed external telemetry and proof-grade integration absent |
| **I5 — Independent falsification** | L17 distinct seeded model vectors; L18 count relevant semantic signatures, not just iterations; L19 independent algebra oracle, witness checks; L20 metamorphic monotonicity | 1M `stress-selection --seed 883`, twice; `tests/test_selection.py` | Fixtures are not production workload labels |
| **I6 — Governance** | L21 product owner decides risk; L22 maintainer authors rationale; L23 independent security/retention reviewer challenges; L24 Git administrator enforces status checks; L25 no automatic delete | Governance agreement, CODEOWNERS/PR routes, `authorized_action=NONE` | Protected status checks unavailable on current private hosting plan; no enforcement attestation |
| **I7 — Maintained product** | L26 README onboarding, new CLI discoverability, ADR, schema; L27 all prior tests; L28 self-selection on CORA source; L29 reviewed release identity | CI installation, regression, self-audit | Human novice-engineer pilot and independent maintained external repos still open |

### States and permissible actions

- `RETAIN_EVIDENCED`: a positive edge, entrypoint or protected **declared** role was observed. This establishes a reason to retain/review, not proof of execution.
- `INVESTIGATE`: no positive dependency emerged in the partial model; **selected for human research only**. This is not `DEAD`.
- `DEBT_BLOCKED`: the committed artifact, ontology, graph or role evidence is unavailable/incomplete for minimum classification.

In all states: `dead_code_proven=false`, `safe_deletion_proven=false`, `authorized_action=NONE`. The `cora closure --claim safe_deletion` path remains blocked/refuted as in PR-05. Neither file selection nor its source digest may authorize `apply-rename-doc` or any future destructive API.

## Falsification experiment — precise numerical contract

`cora stress-selection --seed 883 --cases 1000000` enumerates one million unique 20-bit evidence vectors using an XOR bijection with the seed, distributed over 24 contextual families. It tests a *finite modeled selector* with a separately implemented Boolean-algebra oracle plus local witnesses. The report measures `distinct_applicable_semantic_signatures`, because different vectors can become the same semantic case when irrelevant axes are removed. The two reports must compare byte-for-byte; zero differences in this corpus does **not** demonstrate universal safety in arbitrary programs. Real Git fixtures supply independent expected states for import, entrypoint, misleading filename, multi-role verifier/test, missing ontology, absent roles, path traversal and tampered receipts.

## Future threshold for a file-removal certificate

A later, explicitly different DoD would require: bounded closed-world artifact contracts; full graph-to-build/deploy/registry/runtime/cross-repository provenance per version; a reviewed machine-readable permitted change recipe; independent non-regression tests across declared configurations; restoration/rollback and data-retention approvals; externally protected CI with a second reviewer; operational rollout observation; and explicit coverage-gap handling. Even this could support only **bounded, contextual guarantees**, never the universal G* statement.

**External standards as design references, not certifications:** [OpenSSF OSPS Baseline](https://baseline.openssf.org/) (current maturity-targeted controls); [NIST SP 800-218 SSDF](https://csrc.nist.gov/pubs/sp/800/218/final) (secure software development); [GitHub ruleset guidance](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/managing-rulesets-for-a-repository) (independent platform enforcement). An unavailable private-repo ruleset cannot be represented by a repository file alone.
