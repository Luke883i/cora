# CORA definition of done — a backward-derived proof lattice

**Status semantics:** `PASS` = required evidence executed and independently checked within the stated scope; `BLOCKED` = material unknown or missing proof; `FAIL` = observed counterexample; `NOT_APPLICABLE` = explicit scope exclusion. A test passing never automatically promotes a broader product claim. Gate IDs are stable, and the witness below is an acceptance *method*, not a claim that every gate has passed.

## Global DoD — G0

> A newcomer can identify CORA's product, software and Git-repository boundaries within five minutes, install one canonical CLI, audit an explicit Git revision, trace positive claims to evidence, see unresolved obligations, perform only demonstrably authorized scoped changes, and reproduce the declared tests and installation procedures; unsupported ecosystems and trust boundaries remain explicitly named.

This global DoD is **AND-composed**, not an average: `G0 := I1 AND I2 AND I3 AND I4 AND I5`. Universal safe deletion, complete multi-language semantic equivalence, independent runtime closure and public signed provenance are **separate future ambitions and currently BLOCKED**; their absence does not justify calling G0 "universal" or "production grade".

## Intermediate DoD and local tests

| Gate | Scope | Required local DoD and witness | Owner |
| --- | --- | --- | --- |
| **I1 Discoverability** | Product/repo/software | **L1.1** first 30 README lines distinguish three entities, experimental status, limits, installation; **L1.2** links/paths resolve; **L1.3** CLI commands match parser; **L1.4** a first-time engineer independently answers six questions without chat context | docs and onboarding tests + human reviewer |
| **I2 Source integrity** | Repository/software | **L2.1** single `cora` entrypoint and source package; **L2.2** committed self-ontology valid; **L2.3** executable self-graph binds to Git commit; **L2.4** schema/ADR/CI locations declared; **L2.5** no fabricated production/release claim | packaging/graph/contract CI |
| **I3 Evidence quality** | Software/product | **L3.1** working tree vs Git source kept distinct; **L3.2** graph and adapters label candidate vs supported; **L3.3** scoped certificates reject forged digest and unknowns; **L3.4** published outputs state missing coverage | PR-02–05 tests |
| **I4 Safe maintenance** | Software/repo | **L4.1** digest-approved scoped document plan; **L4.2** real Git positive and negative fixture; **L4.3** owned-file rollback and postimage check; **L4.4** guard bootstrap & protected-control modifications **BLOCK**; **L4.5** no safe-deletion promotion; **L4.6** independently protected hosting required | PR-06 tests + bootstrap adversarial tests; external admin for L4.6 |
| **I5 Distribution and reproducibility** | Product/repo | **L5.1** wheel and sdist source parity; **L5.2** isolated installs; **L5.3** corrupt archives rejected; **L5.4** deterministic seeded stress with declared denominators; **L5.5** independent release/publishing protections and actual third-party pilots separately tracked as **BLOCKED** | PR-07 CI, independent release audit |

## Human first-read acceptance — not reducible to grep

Select **one engineer who has not worked on CORA**. Give only the repository root and five minutes, without this chat. Ask them to demonstrate (not guess) where to find: (1) product purpose, (2) source package/entrypoint, (3) repository/CI boundaries, (4) first safe audit commands, (5) an explicitly unsupported destructive task, (6) tests and security contact pathway. Record task completion, time, confusion and incorrect beliefs. **Pass** requires six correct answers and no mistaken belief that CORA can safely delete arbitrary code. This human gate is **PENDING**, regardless of automated documentation checks.

## PR hardening acceptance and counterexamples

- **H01:** A malicious PR chooses a Git base preceding guard installation and edits `.cora/verify.py`. **Expected:** `BLOCKED`, not `PASS_SCOPED`.
- **H02:** An attacker edits the workflow or policy at bootstrap. **Expected:** explicit independent review required; the vendored guard cannot be its own enforcement authority.
- **H03:** Removing README's limitations, product/software/repo identity, onboarding command or a referenced doc must fail `verify_repository_contract.py`.
- **H04:** A committed ontology and a pinned Git commit must reproduce the graph; the uncommitted working tree must not silently redefine it.
- **H05:** All 108 historical regression tests, new DoD/hardening tests, and PR-07 packaging CI must pass on the **same PR head SHA**.

**G0 presently cannot be signed off solely by CI.** Human first-read and external administration/protection evidence remain necessary. Track actual outcomes in [audit](AUDIT_PR01_PR07.md); do not encode "PASS" for absent evidence.


## Extension: per-file forensic AI governance

The additional DoD lattice and unresolved hosting/runtime/AI calibration gates are in [STANDARDS_MAINTENANCE_AUDIT.md](STANDARDS_MAINTENANCE_AUDIT.md). In particular, a positive result from `file-lab` is a **narrow observation**, not a removal permit. The human decision artifact records intent but cannot authenticate its signatories or enact operations. Independent CI review, runtime provenance and external labeled accuracy remain BLOCKED.

**v1.experimental update:** the current release-candidate contract, multi-role artifact policy and expanded DoD lattice are at [DOD_V1_EXPERIMENTAL.md](DOD_V1_EXPERIMENTAL.md). The earlier G0 definition remains historical and does not substitute for the current human/hosting/independent pilot gates.
