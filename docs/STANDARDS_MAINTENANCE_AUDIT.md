# CORA — product/software/repository governance and hardening audit

**Audit scope:** implementation and declared controls in merged PR-01–08; new file-lab feature proposed after PR-08. Standards are **benchmarks**, not certifications of conformance. Date: 2026-11-02.

| Standard or common operating practice | What CORA implements | Hardening / evidence gap | Required accountable human |
|---|---|---|---|
| [OpenSSF OSPS Baseline v2026.08.28](https://baseline.openssf.org/) | SECURITY, CONTRIBUTING, tests, CI, immutable Git evidence | Required independent reviews and protected main/rulesets **not proven**; private plan can limit rulesets | Repo administrator + security reviewer |
| [NIST SSDF SP 800-218](https://csrc.nist.gov/projects/ssdf) | source integrity, tests, threat-aware fail-closed evidence | formal threat model, vulnerability remediation triage, dependency management & secure release approval incomplete | Security reviewer |
| [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html) | analysability via per-file evidence dossier, defined CLI, reversible limited doc change | quality benchmarks (accuracy, testability, performance, maintainability) on real repositories absent | Product owner + test lead |
| [NIST AI RMF](https://airc.nist.gov/airmf-resources/playbook/) | AI proposals isolated from authoritative evidence; human decision recorded | empirical calibration, bias/drift measurement, provider trust/privacy approval, model provenance absent | AI-risk owner + security reviewer |
| [SLSA v1.1](https://slsa.dev/spec/v1.1/) | reproducible local candidate wheel/sdist verified in CI | attested builds, trusted identity, signed provenance, reproducible independent builder absent | Release manager |
| [GitHub governance](https://docs.github.com/en/pull-requests/reference/managing-and-standardizing-pull-requests) | PR CI, proposed CODEOWNERS and template | enforced required reviews/checks, signed commits and emergency change policy not verified | Repo administrator |
| [OpenTelemetry](https://opentelemetry.io/docs/specs/semconv/general/trace/) | bounded, typed manual import of path-level runtime observations | authenticated instrumentation, environment/trace correlation, sampling bias and non-observation proof absent | Runtime owner |

## Prioritized hardening backlog

**P0 — trust boundary:** Independent branch protection and CI required checks; no AI-supplied fact promotes certificates; runtime annotations remain caller-supplied; risky actions require separation of duties. External settings remain unverified.

**P1 — per-file forensics:** Read-only immutable per-file dossier, typed evidence links, coverage holes, incoming/outgoing static dependency candidates, product/software ownership, manifest evidence, optional runtime sample, AI hypothesis import and human decision ledger. All five evidence levels must be visible without assuming the unknown away.

**P2 — controlled experiments:** Quarantine worktree isolation, recovery checks, branch-scoped monitoring, retention approvals and code-aware rename adapters are **design only**; no universal automatic transformations are introduced by this PR. AI+runtime evaluation requires a separately governed dataset.

**P3 — evidence quality:** Measure precision/recall on independently labeled third-party repositories, false safe-deletion rate by language, calibration reliability of proposed intervals, provenance coverage and cost. Until then `confidence_range` must not be described as probabilities or verified statistical bounds.

## Global, intermediate and local DoD (backward derived)

**G-AI-FORENSICS:** An independent engineer can install CORA, inspect *one selected file* at an immutable commit, trace every **supported** relation to source evidence, see all material unsupported dimensions, import a bounded runtime claim and an AI hypothesis without elevating them to proof, register a human-only triage decision, and rerun the dossier against Git without any target-repository mutation. AND-compose the following:

| Intermediate | Local necessary conditions | Verifiable witness |
|---|---|---|
| I1 Product UX and newcomer onboarding | L1 `file-lab --help`; L2 5-minute command, limits & example; L3 product/software/repository and human responsibility explained | README, FILE_LAB, real newcomer exercise (human gate open) |
| I2 Evidence provenance | L4 commit-bound blobs; L5 typed graph relations; L6 same-commit ontology; L7 failed/unknown resolution preserved | Git fixture with stale/forged report tests |
| I3 Operational and AI boundary | L8 runtime commit checked; L9 runtime trace never proves absence; L10 AI hypothesis schema and provenance; L11 fabricated references labeled | adversarial runtime/AI tests |
| I4 Triage governance | L12 no unauthorized deletion; L13 retain/investigate vs quarantine/archive/rename proposals; L14 human role and independent reviewer; L15 no action on repo | Git fixture and decision tests |
| I5 Release and quality | L16 all PR01–08 regressions green; L17 repeatable finite model stress; L18 wheel entrypoint; L19 review/branch checks; L20 third-party real validation | CI for L16–18; human/external **BLOCKED** for L19–20 |

**Pass is scoped:** The automated subset may pass; G-AI-FORENSICS remains **BLOCKED** on independently enforced GitHub governance, real runtime evidence trust and third-party accuracy. Do not replace these with 1M synthetic cases.
