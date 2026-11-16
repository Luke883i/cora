# Decision-Ready Assurance for AI-Assisted Software Engineering: Typed Evidence Boundaries, Architectural Surprise, and the Cost of Human Understanding

## ABSTRACT

AI-assisted coding can materialize source structures and continuous-integration controls before a maintainer can reconstruct their rationale or the evidence needed to decide whether to retain them. This paper presents CORA, an experimental repository-assurance artifact, as a design-science case rather than a claim of algorithmic or productivity superiority. The proposed research object is decision-ready assurance: keeping revision-bound observations, inferred explanations, actual verification, task-specific human understanding and authorization distinct, while accounting for the cost of proving them. We consolidate a sequence of author-controlled studies: a typed evidence model, a matched 16-fixture comparator, an original-source public case, a retrospective sample of 11 pull requests across five repositories, and a finite briefing-selection instrument. EC-03 and a strong executable checklist tie on the selected fixtures; the retrospective dossier identifies 92 applicable evidence obligations, 70 unobserved within that dossier; and 44 role-formatted briefings retain the same evidence obligations. A local ICTC guard counterexample and repository-contraction cases expose the danger of equating favorable source indicators with product assurance. Unit and mutation tests support narrow model properties, but no human comprehension, causal effect, total-cost saving, deployment approval or longitudinal preservation has been measured. The contribution is a reproducible claim-bounded case study and an operational research protocol for the missing human and economic validation.

## I. INTRODUCTION

Autonomous code generation changes what a repository can contain without necessarily changing what a decision-maker understands. A practitioner in the AOSP/CORA programme retrospectively described delegated architectural choices and CI/CD workflows that appeared to arise almost spontaneously. That account is useful as a motivating observation, not as evidence that particular workflows were autonomous, unnecessary or unauthorized. Git records artifact identity and changes; it does not authenticate the underlying rationale or the reviewer's cognitive state.

The literature makes novelty claims difficult. The architecture-as-decisions view predates coding agents [1]. The ironies of automation already identify supervision problems [2]. Recent work directly addresses cognitive and intent debt [3], architecture shaped by agent prompts [4], design-rationale reconstruction [5], and evidence traceability for agents [6], [7]. CORA does not originate any of those individual ideas. Its narrower conjecture is that executable, revision-bound non-promotion rules and backward evidence acquisition can compose them into an inspectable boundary between what is observable and what is still required for a justified decision.

The guiding question is: What evidence, task-specific understanding and authorization are sufficient for a warranted software-engineering decision, under non-waivable safety constraints and an explicit cost of assurance? This question separates an artifact that supports reasoning from proof that reasoning has improved in humans.

## II. THEORY AND RESEARCH QUESTIONS

Consider an architectural change event c at Git revision r and a decision task t. Define O(c,r) as observations with source identity and scope; I(c,r) as inferred rationale (explicitly marked inferential); E(c,r,t) as mandatory engineering evidence; K(u,t) as human task-relevant understanding measured from a person u; A(u,c,t) as an attributable, applicable authorization; and C as a vector of compute, CI, model, reviewer-time, delay, rework and recovery costs. These variables are neither interchangeable nor necessarily observable from the same source.

A justified decision must not be inferred from O alone. For any mandatory obligation e in E, an eligible witness must exist at the correct revision and scope; any required human comprehension and authority must have independent evidence. We call these non-compensatory boundary conditions. Absent or inconsistent evidence remains OPEN or UNKNOWN, never an inferred PASS. Optimizing C is secondary to satisfying these hard constraints; heterogeneous costs should not be added into an arbitrary scalar without declared weights and sensitivity analysis.

RQ1 (observability): Which architectural facts and control-surface changes can a pinned Git and PR dossier reconstruct, and which rationale or permissions remain underdetermined? RQ2 (typed boundary): Can a finite contract consistently prevent selected promotions from source, test or document to external approval? RQ3 (strong alternative): Does the contract behave differently from an equally informed executable checklist? RQ4 (human gap): What task-specific comprehension must a decision-maker demonstrate, beyond receiving a correctly formatted briefing? RQ5 (cost): Under which risk and evidence-reuse conditions would the total marginal assurance cost justify additional verification? RQ6 (continuity): Which obligations persist, expire or must be re-observed across Git, architecture and owner changes?

RQs 1–3 are partially addressed by retrospective source and local model evidence; RQs 4–6 remain prospective questions. A formal semantic universe of all relevant decisions is not established. Information-theoretic underdetermination is a useful analogy, but this paper does not estimate entropy, prove an information bottleneck or claim a universal optimum.

## III. SYSTEM AND METHOD

CORA is an offline-first Python repository-assurance tool, not a coding agent, deployment approver or autonomous source owner. Its documented workflow binds a Git revision to inventories, source and test receipts, non-compensatory gates, exceptions and follow-up actions. Its integrated runner distinguishes executed, reused, blocked, failed and unobserved attempts. Workflow rationalization is deliberately read-only and cannot authorize workflow deletion solely from names, ages or partial dependency scans. These are implemented software affordances inspected at CORA main 4ed58534022345e58d17207ab472a306d06d2925; they are not a proof that every consumer is known.

The evidence programme evolved over locally scoped, frozen iterations SI-01 through SI-11A. We treat previous releases as provenance-bearing upstream research artefacts and independently record their boundaries rather than claiming the tests of an experimental evidence model execute the whole CORA product. The present study preserves a negative comparator and later falsifications, including malformed-grade acceptance in an ICTC control.

The retrospective sample is purposive, not representative: 11 public pull requests from CORA, ICTC, iKant_EDU, Teddy and NILO. For each event, source fields include PR numbers, creation and merge timestamps and explicitly identified base/head/merge SHA. The dossier models requirements for source, intent, tests, dynamic consumers, owner, independent review, effective host checks, rollback and, where relevant, user validation. The 92 obligations are applicable *slots* within this fixed authored scheme; the 70 non-observed actions are missing from the collected dossier and do not prove that the underlying repositories have 70 defects.

The paper also uses a controlled comparator: 16 fixed synthetic fixtures with a strong checklist encoding the same substantive rules as EC-03. Both evaluate the same declared inputs and oracles. A separate research instrument offers four presentation orders for each of the 11 PRs and a seven-question comprehension rubric; no participant attempted those questions. Nine author-defined information cards constitute a finite coverage problem. Card points are subjective illustrative weights, not real time or money.

## IV. RESULTS

R1 — Source-bound architectural surface. Across five repository revisions, 211 GitHub Actions workflow files were counted (CORA 14, ICTC 53, iKant_EDU 116, Teddy 25, NILO 3). This is an inventory, not a count of running checks, AI-created pipelines or unauthorized architectural decisions. Eight of the 11 selected PRs touched workflow paths, including 80 paths in iKant_EDU #249. Paths touched do not equal newly created workflows. The reported experience of architectural surprise remains a motivation, not a causally identified outcome.

R2 — Strong-baseline null. On the selected 16 fixtures, EC-03 and the strong executable checklist matched all 16 decisions, and 82/82 compared oracle fields per evaluator. Consequently the observed improvement in decision accuracy on this denominator is zero. No difference in human effort, maintainability or product success follows from these results.

R3 — Source and product boundaries. A public Teddy V21 source file was bound to its original Git blob and selected local helper tests; none demonstrates the complete WebGL visual experience or human visual acceptance. The geometry work preceded the public CORA repository and cannot be credited to the later CORA engine. iKant_EDU #249 exhibits seven top-level directories with PR diff statistics of +4,219/−1,458 lines, net +2,761: topological contraction does not establish less code, lower complexity or native equivalence.

R4 — A falsifiable fail-open counterexample. The original ICTC evaluateClosure function compares evidence grades through indexOf. For unknown requiredGrade such as E999, the result −1 permits a lower known observed grade to satisfy its grade inequality. Selected local tests demonstrate the counterexample; a guard on a local copy rejects two malformed-grade cases while preserving six selected regression outcomes. This does not establish a deployed exploit, a remotely exploitable vulnerability or a patch merged upstream.

R5 — Reproducible acquisition frontier. Across the fixed 11-PR sample, 92 applicable evidence obligations were classified, with 70 unobserved in the dossier. A separate executable checklist tied on the 11 resulting closure decisions. The reticular representation adds explicit, revision-bound acquisition requests, not a demonstrated improvement in decision correctness.

R6 — Authored briefing selection. The finite instrument produced 44 role-ordered briefings retaining all 92 inherited obligations across the dataset and the same seven comprehension topics. Its synthetic minimum-cover points were 52 or 59 versus a 76-point full card; zero actual users, pretests, posttests, measured reading times or provider bills exist in this study. Selected model tests (37) and physical mutant tests (17) identify contract failures, not changes in human cognition or total system economics.

## V. NOVELTY, COUNTEREXPLANATIONS AND VALUE

The observed scientific contribution is best characterized as an artifact-centred, reproducible design-science package with honest limits. The typed schema and non-promotion checks operationalize a boundary between traceability, proof, human understanding and authority; they do not invent provenance, requirements traceability, goal decomposition, assurance cases or decision records. Typed claims and agent observability are also substantial nearby work in LEDGER [6] and Soei [7]. Storey [3] explicitly warns that AI-generated explanations can create the *appearance* rather than the achievement of understanding. Therefore a persuasive briefing is not an outcome measure.

There are multiple competing explanations for the architecture-surprise narrative: competent authorized delegation, underspecified instructions, delayed documentation, proliferating CI scaffolds, and changes in reviewer capacity. The available Git/PR corpus cannot adjudicate among them. A mechanism that generates more verification machinery can also increase compute costs and reduce the operator's available attention. It may even substitute dependence on CORA for dependence on the coding agent.

The candidate user value is conditional: given a change that must be decided by an authorized human, the artifact can expose specific unclosed evidence requirements and preserve them when information is reformatted. The stronger propositions—that this improves real understanding, supports more appropriate reliance, and lowers risk-adjusted total cost—are untested. CORA may be valuable even when it does not save compute if it avoids unacceptable false closures; conversely, under low stakes and strong existing review, its marginal cost may exceed its benefit. We make neither sign assumption in advance.

## VI. LIMITATIONS AND REPLICATION

All fixture, card, fault-vocabulary and manuscript-variant choices were author-controlled. The 100 earlier manuscript variants were editorial alternatives, not 100 experiments or referees. The 11 public PRs are related and selectively chosen; no random sampling, blinded scorer, human comprehension data or time-aligned pre-decision mandate was collected. Git SHA identifies source content but is not testimony of authorized decision, and PR merge status does not alone prove an independent veto or effective host controls. The finite mutation campaigns cannot establish complete correctness or semantic universality.

The companion root-folder release contains the manuscript source, an evidence ledger with references and scopes, historical SHA-256 identities, a deliberately small read-only verifier and adversarial mutations. The archival ZIP supplied alongside retains historical research bundles. Exact-boundary assertions can be checked without network access against the saved corpus; upstream Git and independent external gates require separate observation. Reported original test outcomes are attributed to their prior receipts, not represented as newly executed here unless a local replay receipt explicitly says so.

Future testing, not claimed in this article, requires preregistered decision events, competent and novice participants with measured baseline task knowledge, a checklist with equal information access, independent scoring, cost meters and real host checks. Primary endpoints should include harmful false closures, ability to explain rationale and identify unknowns, and appropriate challenge/rollback; costs should be reported as vectors with uncertainty. An ethically valid outcome may be that a concise briefing does not help, or that CORA is more expensive with no quality improvement.

## VII. CONCLUSION

A repository can preserve exactly what was written without preserving why it was written, which proofs survive a change, or whether the decision-maker understands the choice. CORA implements useful local evidence boundaries and reproducible acquisition tasks but has not demonstrated stronger decisions than an equally informed checklist. The present package consolidates both positive and negative evidence into an inspectable design-science case. The remaining human and economic hypotheses require an independent prospective study and must not be backfilled with synthetic personas, CI status or author-generated prose.

## ACKNOWLEDGMENTS AND AI-USE DISCLOSURE

This manuscript, its research framing, draft text, code, and supplementary evidence organization were developed with substantial assistance from OpenAI ChatGPT (GPT-6), including source analysis, literature discovery, manuscript drafting, reference checking, test generation and adversarial review simulation. AI-generated material appears throughout the abstract, methods, results, discussion, conclusion and scripts. The human author must check all scientific claims, approve the submission and comply with the selected venue's disclosure and authorship policy. No AI system is a human author, and no independent peer review, participant validation or formal editor acceptance is claimed.

## REFERENCES

[1] A. Jansen and J. Bosch, “Software Architecture as a Set of Architectural Design Decisions,” WICSA, 2005, doi:10.1109/WICSA.2005.61.

[2] L. Bainbridge, “Ironies of Automation,” Automatica, vol. 19, no. 6, 1983, doi:10.1016/0005-1098(83)90046-8.

[3] M.-A. Storey, “From Technical Debt to Cognitive and Intent Debt,” 2026, doi:10.1145/3807966.

[4] P. M. Konrad et al., “Architecture Without Architects: How AI Coding Agents Shape Software Architecture,” arXiv:2604.04990, 2026.

[5] X. Zhou et al., “Using LLMs in Generating Design Rationale for Software Architecture Decisions,” ACM TOSEM, 2026, doi:10.1145/3785010.

[6] D. Kim et al., “LEDGER: Claim-to-Evidence Trace Graphs for Auditing LLM Agents,” arXiv:2608.18398, 2026.

[7] M. N. Khan and K. S. Kumar, “Soei: Structured Observability of Evidence and Intent for Multi-Agent AI Software Engineering,” arXiv:2610.39468, 2026.

[8] W3C, “PROV-O: The PROV Ontology,” 2013, https://www.w3.org/TR/prov-o/.

[9] SCSC, “Goal Structuring Notation (GSN) Community Standard, Version 3,” 2021, https://scsc.uk/gsn.

[10] I. Koishybayev et al., “Characterizing the Security of GitHub CI Workflows,” USENIX Security, 2022, https://www.usenix.org/conference/usenixsecurity22/presentation/koishybayev.
