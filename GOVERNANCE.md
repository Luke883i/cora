# CORA human governance — source of decision authority

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
