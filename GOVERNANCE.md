# CORA human governance — source of decision authority

**Document status:** CURRENT
**Current scope:** Human decision rights and actual hosting gaps.
**Operational use:** Identify accountable decision points for change, deletion and release.
**Evidence:** Source policy and separately observed GitHub settings.
**Limits:** Declared roles are not verified appointments or enforced review.


**Status:** normative proposal for the repository; roles are functions, not verified staff appointments. The GitHub repository owner currently controls the platform, but no independent reviewer, ruleset, or branch protection has been verified. This document does **not** claim that two-person approval is already technically enforced.

## Decision rights — human-in-command

| Accountability | Human role | Required decision or veto |
|---|---|---|
| Product direction, public contract, acceptance | Product owner | Accept product scope, prioritization, compatibility, and end-user risk |
| Architecture and code change | Maintainer / technical lead | Review adapters, provenance, tests, architecture and reversibility |
| Repository trust controls | Independent security reviewer | Veto unsafe tooling, model integrations, guard changes, permissions and secrets |
| Operational truth | Runtime / platform owner | Verify instrumented environment, deployment, consumer inventory, logs and recovery |
| Retention, migration, business obligation | Data / retention owner | Veto archive, quarantine or destructive actions affecting retention or legal duties |
| Distributions and releases | Release manager (not the build process) | Authorize release after supply-chain and reproducibility evidence |
| Investigation | Human analyst | Run read-only file lab, author a falsifiable hypothesis, collect counterevidence |
| Hypothesis generation | AI assistant | **Propose only**; cannot assert execution, close unknowns, approve or perform removal |

A role may be unfilled in a single-maintainer project. In that case **high-risk work remains blocked** rather than treating an AI agent or the same author as independent approver. Role names in `file-decision` are self-reported metadata, **not verified authentication**; enforcement must occur in trusted hosting and review workflows.

## State machine for a single file

`OBSERVED -> INVESTIGATE -> HUMAN_TRIAGE -> EXPERIMENT_PLAN -> INDEPENDENT_REVIEW -> VERIFIED_SCOPED -> APPROVED_ACTION -> MONITOR / REVERT`

- **Retain:** preserve established contract, entrypoint, manifest, operational observation or unclosed obligation.
- **Investigate:** no observed static inbound edge, but unknown runtime, build, reflection, API and retention still prevent a dead-file conclusion.
- **Quarantine candidate:** design a reversible isolation experiment on a segregated branch/worktree; define monitoring, exposure period and rollback. Not executable by `file-lab`.
- **Archive candidate:** specify recoverable location, hash, retention schedule, migration owner, discovery path and restore test; requires retention owner's veto review.
- **Rename candidate:** require language/format-aware codemod plus consumer, workflow and runtime impact evidence. PR-06 only implements exact tracked-document path rename under separate authorization.
- **Delete blocked:** no universal deletion authorization in CORA. A `PASS_SCOPED` observational certificate is not an approval.

Two distinct human reviewer identities are required for a quarantine, archive, broad rename or deletion exception; the implementer cannot act as sole independent reviewer. The `file-decision` CLI records a proposal only, **never applies** an action and never authenticates users. Record rationales, alternatives, counterexamples, evidence commit and reviewer identities in an external approved change record or PR; do not put sensitive runtime traces in public CI artifacts.

## Change and release controls

Require PR template, CODEOWNERS review routing, CI regression evidence, security review for trust boundary changes, risk register, backward-compatibility note and an explicit rollback/restore plan. Set required non-author approval, branch rulesets and protected required CI checks in GitHub settings. **Their availability/enforcement is outside source code and currently unverified; a private-plan feature restriction may block rulesets.** Do not use AI-produced confidence as a merge condition. Release authorization requires a human release owner, signed provenance and an external pilot before production-grade claims.

## v1.experimental: semantic artifact and transformation governance

The **product owner** is accountable for product scope and retention tradeoffs; the **software maintainer** maintains implementation and evidence contracts; the **repository steward** owns CI, workflow and protected branch settings; the **security/independent reviewer** challenges trust boundaries and high-risk changes; the **release manager** checks reproducible artifacts and publication permissions. These are functions requiring actual named accountable humans in a deployment, not automatic identities granted by CORA.

Any artifact can combine implementation/test/contract/workflow roles. The committed role registry is a reviewable assertion; changing it requires a maintainer and a different reviewer. **No AI suggestion, maintainer label, self-hash or `PASS_SCOPED` is an approval.** Quarantine/archive/rename remain proposals until separate scope closure and non-regression evidence support them. Destructive deletion is unsupported. An actual administrator must protect branch settings and required checks; this repository does not attest that protection.

## Selection governance — explicit role separation

`cora select-file` selects for **investigation**, not deletion. The maintainer may propose an `INVESTIGATE` case with its source-verified receipt; the software/product owner decides whether its declared product responsibility and retention obligations permit an experiment; an independent security/data-retention reviewer challenges dynamic consumers, legal hold and rollback; a separate administrator verifies platform-level required checks; the release owner controls deployment. The same individual or AI suggestion must not serve as independent source, verifier and final approver. For this private repository, **mandatory protected checks have not been demonstrated**. A human role is an accountability assignment, not an authenticated identity in CLI arguments.

A proposed quarantine or archive requires its own non-destructive experiment record and an independently reviewed restore plan. A negative search result, an uncalibrated AI confidence interval or even a matching SHA-256 is not a substitute for evidence of absence. **Selection receipts do not unlock transformation APIs**, and v1.experimental remains incapable of certified automatic code deletion.


## Historical groups and AI governance

Development groups are **review subjects**. Maintainer validates Git history; product owner verifies capability; software/runtime owner reviews tests, deployment and consumers; independent approver controls subsequent transformation under a separate contract. Roles are functions, not confirmed personnel. Cochange, an absent import or self-reported AI confidence never authorizes archive, quarantine, rename or deletion. External operational closure and independently protected GitHub checks remain required.

## Engineering-debt triage and process governance

`debt-scan` and `process-run` are source-bound **review instruments**, not authority to repair, delete or change repository policy. The engineering owner validates structural/historical signals; the product owner evaluates capability impact; QA supplies real test/coverage evidence; security independently challenges untrusted SARIF; the platform/release owner validates build, deployment and required checks. An independent human approver reviews any future transformation. Review priority is an ordinal queue, not confidence, business impact or money. Weekly inspect P1 signals and evidence gaps; monthly compare source-bound trends without interpreting disappearance as proven resolution. No CLI field authenticates personnel or branch protection.

## Continuous development and AI agent review (PR-14)

The **coding agent is an implementer and proposer, never a reviewer of its own change**. CORA binds pre/post merge evidence to immutable commits and a policy from the base commit. The maintainer evaluates functional changes; the product owner accepts scope; an independently empowered security reviewer vetoes changes to policy, CI, guard, release or repository trust controls; the runtime owner evaluates deployment and rollback; the release manager authorizes distribution. These roles are only *required function labels*: CORA does not authenticate people or enforce GitHub permissions.

Policy bootstrap is `BOOTSTRAP_REVIEW_REQUIRED` and must be accepted under an external administrator-controlled process. Even after merge, an `OBSERVED_REVIEW_REQUIRED` receipt remains nonauthoritative. Independent branch protection, required reviews/checks, signed supply-chain provenance and incident monitoring require controls outside the source tree. See [continuous method](docs/CONTINUOUS_DEVELOPMENT.md) and [DoD](docs/DOD_CONTINUOUS.md).

## Current agent and documentation authority (PR-20 / documentation convergence)

The coding agent is an implementer and source-evidence proposer, not an independent reviewer. The current lifecycle uses the BASE policy and an explicit change-specific intent with the contextual pre/postmerge gate; caller intent is bounded and SHA-linked, never authenticated as product approval. A source-only reticular DoD cannot promote the externally blocked R1–R4 obligations or independently controlled release. See [agent rules](AGENTS.md), [convergent method](docs/CONVERGENT_ASSURANCE.md) and [full R1–R4 DoD](docs/DOD_PR20_CONVERGENCE.md).

For documentation, the README is the current product storefront; methods explain operation; [ADRs and audits](docs/INDEX.md) preserve history; [DoDs](docs/DOCUMENTATION_DOD.md) declare obligations; Git and observed independent outcomes are separate evidence authorities. Editors may clarify a current method but must not overwrite historical findings with retrospective approval. Documentation source review alone cannot close novice usability, target-pilot or protected hosting gates.
