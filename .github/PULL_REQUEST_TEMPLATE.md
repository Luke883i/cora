## Product impact and contract
Explain product, software and repository boundaries affected; cite the contract/ADR.

## Evidence and verification
Provide exact Git commit, test commands, oracles and regression results. Distinguish synthetic tests from independent observations.

## Security, AI and privacy
Declare any new untrusted inputs, runtime signals, AI providers and data transfers. Explain limitations and adversarial cases.

## Risk and rollback
List affected consumers, unknowns, migration/retention obligations and rollback. No unverified deletion authorization.

## Human approvals
Name product owner, technical maintainer, and independent security/retention/release reviewer when relevant. CODEOWNERS routes review only; GitHub branch rules must enforce it.

## Continuous review evidence (CORA)
- Base/head SHA and `dev-premerge` receipt digest:
- Independent tests/CI job + final SHA (not agent-authored assertions):
- High-risk paths and functional security/product/release reviewers:
- New unknowns, debt signals and consumer/deployment coverage gaps:
- Post-merge monitor, rollback trigger, accountable human owner:
- Required hosting rules verified by an administrator? (if not, mark BLOCKED):
