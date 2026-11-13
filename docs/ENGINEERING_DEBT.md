# CORA engineering debt: a multiscale, evidence-bounded operating model

**Document status:** CURRENT
**Current scope:** Multi-scale debt discovery and bounded mitigation decisions.
**Operational use:** Inspect debt-signals, compare revisions and prioritize explicit unknowns.
**Evidence:** Original Git, optional input analyzers and the process suite.
**Limits:** Findings are not certified defect counts or verified remediation.
**Applicable current DoD:** [engineering-debt](DOD_ENGINEERING_DEBT.md) specifies scoped obligations and open evidence; its existence is not proof that any gate passed.


**Status: experimental.** An inventory of observations, *not* a certified defect register, a measured financial liability, a runtime dependency graph, or a license to modify software.

## Purpose, inputs and boundaries

CORA joins **committed Git object provenance**, bounded commit/change archaeology, declared product/software/ownership and multi-role contracts, partial Python AST structure, and optional externally produced **SARIF 2.1.0**. It computes source-replayable candidate technical-debt signals with: category, rule, evidence strength, versioned Git SHA, review priority, human owner role and a suggested validation/remediation method. The evidence boundary is explicit: historical co-change is not a runtime dependency; absent imports do not prove dead code; AST decision-node count is not a standardized cyclomatic-complexity measure; source static scanners cannot establish exploitability or business impact. SARIF can come from CodeQL/Semgrep/other standards-compliant producers, but **this PR does not install, execute or attest any of them**.

## Type taxonomy and bounded remediation policy

| Label | Current signals | Recommended human workflow | Why no automatic fix |
| --- | --- | --- | --- |
| CODE_COMPLEXITY | Python AST decision count/nesting or file size | Characterization tests, divide responsibilities, check behavior | Structure alone does not prove defects |
| CHANGE_PRESSURE | ≥5 observed touches in bounded Git history | Validate hotspot with ownership, faults and module health | Frequent changes may indicate valuable code |
| TEST_EVIDENCE | Coverage *not attested* (global unknown) | Run instrumented tests, link coverage to target revision | Presence of tests is not evidence of execution |
| ARCHITECTURE_COUPLING | Multiple declared product owners; ≥2 cross-product cochanges | Inspect interfaces and change coordination | Cochange is not an import or data flow |
| DEPENDENCY_RESOLUTION | Partial adapter unknowns, not audited transitively | Inspect lockfiles, build provenance and SBOM | Manifest declarations are not resolved installations |
| DOCUMENTATION_CONTRACT | Ownership/role drift and missing declarations | Reconcile policy with maintainers | Missing metadata is not dead software |
| BUILD_RELEASE | Not attested in read-only scan | Pinned reproducible build and signed provenance | Repo checkout is not an executed release |
| SECURITY_FINDING | Optional untrusted SARIF rule assertion | Security owner reproduces and independently triages | SARIF does not authenticate source or exploitability |
| GOVERNANCE_PROCESS | Required independent checks not attested | Repository ruleset and human approval review | A workflow file does not prove enforcement |
| EVIDENCE_COVERAGE | Git/AST/ontology/report gaps | Collect evidence and rescan, do not infer absence | Unknown cannot be reclassified as zero debt |

The taxonomy is a **local policy**, informed by multi-category technical-debt surveys; not an official ISO debt classification. The 
`P1_REVIEW`/`P2_INVESTIGATE`/`P3_MONITOR` bands are *ordinal review queues*, not probabilities or money. A finding **never authorizes remediation**.

## Processes and reproducibility

| Process | Read-only methods | Typical use |
| --- | --- | --- |
| `source` | Git snapshot, role declarations, manifest adapters | Intake and provenance |
| `history` | Bounded Git archaeology | Change trend and coupling review |
| `architecture` | Owner-declared graph and adapters | Architecture/design review |
| `forensics` | Holistic history, role, graph and groups; optional one-file selection | Human investigation |
| `debt` | Multi-scale categorized debt signals | Backlog intake and triage |
| `verification` | Re-run selected source/provenance analyzers | Source-local acceptance |
| `full` | Union of **safe read-only** source processes | Whole-repo observation |

All commands pin a Git commit and can be rechecked. `full` **does not** call third-party scanners, external network services, LLMs, target-code test runners, transformations, releases or security scanning tools. To run such activities, an authorized operator must invoke their existing separate workflows. `debt-scan --sarif` reads *caller-provided* bytes (≤4 MiB), validates a bounded SARIF subset, rejects path traversal/external URLs, marks each result `EXTERNAL_UNVERIFIED`, and requires the same bytes at `verify-debt`. Even replay does not establish scanner authenticity.

```bash
cora process-list
cora process-run . --process full --revision HEAD --max-commits 64 --output /tmp/process.json
cora verify-process /tmp/process.json --repo .
cora debt-scan . --revision HEAD --max-commits 64 --output /tmp/debt.json
cora verify-debt /tmp/debt.json --repo .
cora debt-diff . --base HEAD~1 --head HEAD --output /tmp/diff.json
cora debt-scan . --sarif /tmp/external.sarif --output /tmp/debt-external.json
cora verify-debt /tmp/debt-external.json --repo . --sarif /tmp/external.sarif
cora stress-debt --seed 883 --cases 1000000
```

**Trend semantics:** new/persisting/not-observed finding IDs are review signals; “not observed” does **not** mean resolved. Counts depend on historical sampling and AST/adapter coverage. Compare process/coverage gates before interpreting a change; financial interest, hours-to-remediate, expected ROI, false-positive rates, precision/recall, calibrated confidence and actual behavior require independent labeled/operational measurements.

## Why these particular reference methods

- **ISO/IEC 5055:2021** and **ISO/IEC 25010** provide a structural-quality/product-quality backdrop; CORA does **not** claim conformance to their normative metrics. [ISO 5055](https://www.iso.org/standard/80623.html).
- **CodeScene-style hotspots and change coupling** suggest prioritizing high-change areas only when combined with structural health and product relevance, not counting touches as defects. [CodeScene documentation](https://codescene.io/docs/guides/technical/hotspots.html).
- **OASIS SARIF v2.1.0** enables interoperable scanner result interchange with explicit data-source trust. [OASIS specification](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html).
- **NIST SSDF** (PO, PS, PW, RV) and **OpenSSF Scorecard/OSPS** inform review and process controls, without implied certification. [NIST SSDF](https://csrc.nist.gov/projects/ssdf), [OpenSSF Scorecard](https://openssf.org/projects/scorecard/).
- **CodeQL dataflow, Semgrep, SonarQube, PyDriller, RefactoringMiner, Joern/CPG, OpenTelemetry** are potential independently governed future adapters. This change only consumes a bounded SARIF subset; it does not execute these tools.
- **2026 empirical SATD/algorithm-debt studies** demonstrate that even task-specific ML detection can have limited F1 and confuse debt subtypes; CORA therefore refuses to turn model labels into proved debt or deletion eligibility. See [Simon et al. (2026)](https://doi.org/10.1007/s10664-026-10807-5).

## Governance and monitoring cadence

The engineering owner labels/triages; product owner evaluates impact; QA validates reproducer/coverage; security owner handles SARIF; platform owner validates build and independent CI; a second reviewer approves any future transformation. Weekly: review newly introduced `P1_REVIEW` and unresolved coverage. Monthly: compare bounded hotspot/cochange baselines, record closure evidence and reprioritize. Per release: check signed provenance/reproducibility with separate release gates. No actor identity is cryptographically verified by this CLI; the repository owner must configure protected required checks outside versioned YAML.

<a id="pr40--retained-dynamicstatic-debt-and-falsification-method"></a>
## Static/dynamic debt controls and bounded falsifiers

`python tools/verify_engineering_closure.py --repo . --revision HEAD --output /tmp/ekc.json` extracts the exact committed Git source identity, parser/atlas census, Python static relative imports and executable callsite indicators. Replay with `--verify-report /tmp/ekc.json`. Callsite presence is not proof of runtime execution, and absence is not proof of safe deletion. The primary integrated execution remains `cora process-run --one-run --profile comprehensive` and its existing `verify-process` counterpart; the engineering-closure verifier is a source diagnostic, not a second orchestrator.

The [noncompensatory engineering-knowledge DoD](../.cora/contracts/dod/engineering-knowledge-dod.json) retains distinct debt observations: P0 physical Git fixture CI failure (RCA pending), P0 host-protection/reviewer enforcement (independent administrative check), P1 live/historical document chronology, P1 dynamic Python and subprocess boundaries, P1 bounded versioned Git genealogy (not complete later history), P1 maintained-target oracle gap and P2 finite mutation model extrapolation risk. A source report cannot close an external gate.

`python tools/verify_engineering_closure.py --repo . --revision HEAD --stress-10m --output /tmp/ekc-10m.json` executes ten seeds × one million bounded semantic vectors, preregistering all zero/single/pair/triple/quadruple combinations across 14 fault families. A separately worded Boolean reference detects source-state disagreements, and any synthetic reviewer/host PASS fails closed. Retained SHA-256 streams make campaigns reproducible. Exactly 1,471 distinct fault masks are preregistered and reused; ten million **case evaluations are not ten million unique source mutations**. Physical Git-committed mutants and the original Git source fixture are tested separately; no external target code is automatically executed.


<a id="post-pr44-efficiency-without-evidence-promotion"></a>
## Efficient source review without evidence promotion

**Backward DoD (source scope).** A useful review must have **one primary
entry point**, an immediately readable **claim → Git evidence → falsifier**
path, exact-commit replay, no repeated test invocation for the same purpose,
and fewer mandatory onboarding operations. The current primary route is the
existing `cora process-run --one-run --profile comprehensive` followed by
`cora verify-process --one-run`; it does not add a second executor or
claim that the 71 declared commands ran.

The **original-Git obligation delta** remains available through
`tools/verify_engineering_closure.py --closure-base BASE_SHA --revision HEAD_SHA`.
The **separately implemented comparator** remains available through
`tools/independent_git_oracle.py --closure-report RECEIPT.json`.
The two algorithms serve different trust boundaries and are optional for
the normal One-Run review. A removed node, a rewritten claim or a self-reported
PASS never counts as a verified closure. The CI comparison now uses the
actual Git merge-base (or the preceding push commit), not a fixed historical
SHA. The duplicate qualification test invocation is omitted from engineering-debt
CI; the existing One-Run workflow retains coverage.

**Efficiency proof is bounded:** inspect the exact PR diff for reduced active
onboarding text, no new CLI command, no new DoD, no new workflow, and no lost
independent negative-control coverage. The existing One-Run CI executes the
seeded 100k finite source model and checks replay, false promotions and
source/external separation. Model volume does **not** measure elapsed human
review time. The external leaves remain mandatory: unfamiliar-reader task
completion, maintained-target behavior, runtime isolation, effective protected
GitHub review and release authorization. Until they are observed, product
acceptance stays `BLOCKED_EXTERNAL`; shortening prose cannot close them.
