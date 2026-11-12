# Backward DoD lattice — continuous development framework

**Document status:** CURRENT
**Current scope:** Acceptance cuts for contextual engineering-change governance.
**Operational use:** Check pre/postmerge source invariants and identify independent review gates.
**Evidence:** Reticular DoD, contextual receipts and source regressions.
**Limits:** Human approval and actual host enforcement remain separately unverified.


**G (scoped and falsifiable):** For any two accessible commits with bounded Git changes, CORA produces an immutable/replayable source-bound pre-merge or post-merge review receipt. An agent can submit its change claims for reconciliation without acquiring authority. The framework neither silently treats missing policy as approved nor falsely attests human/CI trust, execution or runtime equivalence.

**G+ (not demonstrated):** independent GitHub rulesets/required approvals and attestation of reviewer identities; real-world scanner authenticity and patch quality; production deployment/rollback/SLO observability; universally regression-free development; SLSA compliance. These require *external* controls and evidence.

| Intermediate DoD | Local testable obligations | Witness |
| --- | --- | --- |
| I1 Provenance | L1 both SHA commits source-verified; L2 ancestry; L3 exact changed/renamed paths and 2048-path limit | real temporary Git fixture, source-bound replay |
| I2 Governance | L4 policy from BASE only; L5 policy self-edit/high-risk path routed to security; L6 first policy bootstrap cannot approve itself | adversarial policy, workflow, rename tests |
| I3 Human/agent separation | L7 named functional review roles; L8 agent cannot self-authorize; L9 agent claims reconcile to Git but tests stay unverified | fake path, fake approval, fake tests fixtures |
| I4 Lifecycle | L10 pre-merge receipt; L11 post-merge source delta; L12 debt trend optional and explicitly uncertain | positive/negative commit fixture and replay |
| I5 Architecture | L13 single `cora` entrypoint; L14 process-suite and snapshot remain independent; L15 no LLM, source execution or deletion in gate | CLI/test contracts |
| I6 Reproducibility | L16 altered/re-signed receipt rejected against Git; L17 dirty worktree invariant; L18 same-source policy pinned | forged-hash and dirty-worktree tests |
| I7 Continuous verification | L19 CI on PR and main push; L20 Python 3.11/3.13; L21 source-bound CORA-on-CORA and two 1M deterministic model replays; L22 existing suite remains green | final-head GitHub workflows |
| I8 External truth | L23 branch protection and approvals externally enforced; L24 operational incident/deployment/release evidence independently authenticated | **OPEN**, cannot be closed by code in this PR |

## Mechanical metrics

- `base_is_ancestor`: Boolean based on Git merge-base.
- `changed_count`: count of paths in SHA-scoped Git diff; budget comes from **BASE** policy.
- `high_risk_paths`: exact/rename-scoped paths crossing protected prefixes.
- `base_policy_digest`, `policy_state`: immutable base authorization anchor or explicit bootstrap/missing.
- `required_human_roles`: functional human roles; a label is **not authenticated evidence of review**.
- `debt_delta`: optional signal comparison; not a claim about incidents, outcomes or behavior.
- `source_verified`: `verify-dev-gate` replays on original Git objects and reproduces every field.
- `authorized_action`: **always `NONE`**. There is no positive transition to merge permission in this contract.

## Merge checklist (manual and outside CORA authority)

- [ ] CI passes on exact final SHA, tests and static scanner outputs retained.
- [ ] Independent reviewer, with appropriate protected permissions, validates policy/trust boundary changes.
- [ ] Repository administrator confirms required status checks and protected branch controls, or documents a blocker.
- [ ] Product and software owners accept scope, compatibility, rollout and rollback plan.
- [ ] Runtime/security/retention owners resolve applicable deployment/consumer obligations.
- [ ] Post-merge monitoring owner assigned, baseline/target SHA and evidence recorded.

**No green CI or million-case synthetic model can substitute for these external human/operational DoDs.**
