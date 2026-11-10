# CORA-Score: editorial hypothesis for engineering-assurance maturity (v0)

This is **not** a score produced by the CORA CLI, a release certificate or evidence of scientific truth. It is a two-axis *ordinal* rubric for how demonstrably a repository can be developed or remediated through CORA-like assurance. The axes must not be averaged.

- **Dev_CORA**: evidence that AI-assisted implementation can be bounded by acceptance obligations, Git revision, executable tests, adverse counterexamples and independent review.
- **Bonifica_CORA / Remediation_CORA**: evidence that previously AI-built software can be inventoried, audited, safely repaired, tested for regressions and requalified after changes.

| Band | Meaning on either axis |
| --- | --- |
| 1 | No stable acceptance, ownership or reproducible evidence |
| 2 | Some contracts and checks; major evidence, consumer or recovery gaps |
| 3 | Repeatable bounded checks; material gaps and unverified independent outcomes |
| 4 | Integrated tests, provenance and adversarial review over core paths, but qualified external acceptance still open |
| 5 | Independently reproduced relevant end-to-end, physical/host, user and recovery results with accountable reviewers. Still not a certification of correctness |

**UNRATED** is required when evidence does not support a band; it is not equivalent to 1.

### Provisional user-specified hypotheses (not measured)

| Repo | Dev_CORA | Bonifica_CORA | Qualification |
| --- | ---: | ---: | --- |
| CORA | 4/5 | 4/5 | Proposed |
| ICTC | 4/5 | 4/5 | Proposed |
| iKant_EDU | 3/5 | 2/5 | Proposed |
| LUMEN | 4/5 | 2/5 | Proposed |
| Teddy | 4/5 | 2/5 | Proposed |
| NILO | 4/5 | 2/5 | Proposed |

ROA, academics and closed Juriscribe are not rated on a software-development scale. The scale evaluates **assurance evidence**, not engineering talent, breadth of features, or market readiness.

### DoD to turn a proposed band into an assessment

Record exact repo/SHA, date, human assessor, declared scope and denominator, source-to-test trace, real runtime/host evidence, independent falsifier, surviving/inconclusive mutants, observed remediation and regression outcomes, blockers, and decision owner. Require separate acceptance gates for each axis. A modelled mutation count or a CI badge cannot replace physical outcomes.

**Adversarial counterexamples that must block an unsupported promotion:** remove SHA binding; make a test self-confirm its own oracle; substitute a simulated mutation for an observed runtime fault; remove independent reviewer evidence; turn NOT_RUN or BLOCKED_EXTERNAL into PASS; silently expand the tested scope. Scores must remain provisional until checks are independently reproduced.
