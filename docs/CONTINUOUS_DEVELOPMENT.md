# CORA continuous development — pre-merge, post-merge, agent constraints

**Status:** v1.experimental, evidence and review framework, **not** a coding assistant or a GitHub administrator. The supported package remains `cora-audit` with one CLI, `cora`. The source of truth is a Git commit; CI and review attestations require separately trusted GitHub controls.

## Operating model

1. **Plan and change:** Human product/technical owners define desired behavior and blast radius. A coding agent may propose a patch but must read [AGENTS.md](../AGENTS.md) and may not approve it.
2. **Pre-merge:** `cora dev-premerge REPO --base BASE --head HEAD` inspects committed Git changes and the continuous policy read **from BASE**. It classifies review paths conservatively and issues an immutable, re-playable receipt. Even `OBSERVED_REVIEW_REQUIRED` **does not mean approved**. Bootstrap without a policy in BASE remains `BOOTSTRAP_REVIEW_REQUIRED`.
3. **Independent checks:** Run repository tests, security tools, self-audits, and CORA `process-run --process full` as separate checks with source SHA; human reviewers inspect results and deployment/data-retention obligations. Workflow files in an untrusted PR cannot themselves confer independence. An actual admin must configure mandatory branch rules/reviews and trusted checks outside PR-controlled code.
4. **Post-merge:** `cora dev-postmerge REPO --previous PREVIOUS --head HEAD --with-debt` records ancestry, changed paths, trusted-policy status and a source-bound change in **debt signals**. The delta is not an assertion that a defect was introduced, fixed, or that runtime is healthy. Deploy/runtime rollback, incident response, SLOs and telemetry require separately authenticated systems.
5. **Continuous improvement:** Track unresolved source, build, security, governance, data and runtime evidence, run periodic trend reviews, record remediation owners and verify after closure. Recalibrate thresholds from independent outcomes, not model fixture counts.

### Commands

```bash
cora dev-premerge . --base HEAD~1 --head HEAD --output /tmp/premerge.json
cora verify-dev-gate /tmp/premerge.json --repo .
cora dev-postmerge . --previous HEAD~1 --head HEAD --with-debt --output /tmp/postmerge.json
cora verify-dev-gate /tmp/postmerge.json --repo .
cora agent-check /tmp/agent-proposal.json --repo . --output /tmp/agent-review.json
cora stress-continuous --seed 883 --cases 1000000
```

Save receipts **outside** the target working tree. `--strict` on pre/post commands emits exit code 2 for **every outstanding blocker** (including bootstrap and high-risk paths needing independent review), not just a blocked status label; it **never upgrades** a report to authorized. This PR introduces the policy for the first time, so its own BASE does not contain it and the bootstrap cannot be declared independently approved.

### Agent proposal contract

`cora-agent-proposal/1` example (use actual Git SHAs and exact old/new changed-path set):

```json
{
  "schema": "cora-agent-proposal/1",
  "agent_id": "ikant-code-agent-identifier",
  "base_commit": "<BASE_SHA>",
  "head_commit": "<HEAD_SHA>",
  "intent": "Explain the smallest expected functional change",
  "changed_paths": ["src/cora/module.py"],
  "test_claims": ["UNVERIFIED: python -m unittest ..."],
  "unknowns": ["external consumers and runtime behavior"],
  "authorized_action": "NONE"
}
```

No direct GitHub identity authentication, independent reviewer proof, test execution attestation, production deploy evidence or signed SLSA provenance is implemented by `agent-check`. Test statements remain *agent assertions* even if a referenced source path exists. **An AI must never self-attest that an independent reviewer approved.**

## Normative crosswalk (inspiration, not certification)

- **NIST SSDF SP 800-218**: PO (prepare), PS (protect), PW (secure implementation), RV (response/learning): map to explicit human ownership, immutable evidence, tests/review, post-merge follow-up.
- **OpenSSF OSPS Baseline v2026.08.28**: branch/protected change/review controls; local workflow checks are insufficient to claim enforcement.
- **SLSA 1.2 Source and Build Tracks**: source provenance/authorized revisions distinct from build attestation; CORA only stores Git-bound local receipts, not signed SLSA source/build attestations.
- **DORA**: trend observability and post-deployment quality metrics; CORA does not infer change failure rate, lead time or deployment frequency from commit history alone.
- **GitHub Actions security**: use read-only `pull_request` workflows; **never** run untrusted PR code under `pull_request_target` with privileged secrets.

Official references: https://csrc.nist.gov/pubs/sp/800/218/final · https://baseline.openssf.org/ · https://slsa.dev/spec/v1.2/ · https://dora.dev/ · https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target

## Trust boundary and known debt

The policy and code live in the same repository that an agent can edit. Until protected GitHub branch rules, independent reviewer permissions and required trusted checks are configured by an administrator, **CORA cannot guarantee** a user or agent cannot bypass them. GitHub ruleset inspection on this private repository currently returns HTTP 403 due to account/plan restrictions, which is an **unverified control**, not proof of enforcement or non-enforcement. This first PR is a **bootstrap** and needs human administrator acceptance.

Post-merge without real CI/deployment telemetry is not an end-to-end operational health gate. Any result that says `OBSERVED_REVIEW_REQUIRED` is an audit signal, not a merge authorization. No automated deletion, code rewrite, release or deployment is performed by these new tools.

### Review artifact retention

The PR workflow uploads only JSON review receipts and deterministic model reports for **14 days**; the post-merge job uploads its JSON drift receipt for **30 days**. These are expiring review artefacts, not authoritative durable records, signatures, SLSA attestations or a replacement for an approved record system. Output paths and CI artifacts can still disclose repository metadata, so use repository-appropriate access controls. The workflow never includes source files in these uploads.

## Current PR-20 opt-in contextual workflow

When the target has its own committed ontology and a trusted BASE-committed `.cora/continuous-policy.json`, pass a bounded `--intent` to `cora dev-premerge TARGET --base BASE --head HEAD --contextual --intent "Specific change with acceptance tests" --convergence-contract PATH --output REPORT`. Verify with `cora verify-contextual-gate REPORT --repo TARGET --intent "Specific change with acceptance tests" --convergence-contract PATH`. Run the equivalent `dev-postmerge --contextual` against the **actual merged** revision, not the former PR SHA. The legacy gate remains available without `--contextual`.

Source candidates and witness invalidations are not authenticated consumer, host or runtime observations. Missing intent yields DEBT_BLOCKED, even if deterministic local source checks can otherwise run. See [agent adoption](AGENT_ADOPTION.md) and [convergent assurance](CONVERGENT_ASSURANCE.md).

## CI workflow rationalization (PR-24 proposal)

CORA adapts the iKant_EDU PR-201/202 inventory, PR-205 historical preservation, and draft PR-215 consolidation proposals. Those observations are engineering precedents, not an authorization to delete workflows.

Run `cora workflow-audit . --revision HEAD --output /tmp/workflows.json` and `cora verify-workflows /tmp/workflows.json --repo .`. Compare with `--base BASE_SHA` to inspect additions, modifications and removals. This read-only analysis identifies partial trigger/job syntax, local workflow callers, source references and duplicate checks; it cannot prove absent external consumers or equivalent runs.

`cora.workflow-dod.json` specifies `G_WORKFLOW_SOURCE` and `G_WORKFLOW_GOVERNED` with external E01-E04 evidence open. A reviewer must establish replacement behavior and actual platform controls before separately approving retirement. A source receipt never executes or modifies target workflows.

## Method synthesis and governed AI hypotheses (PR-25)

`cora method-synthesize . --revision HEAD --output /tmp/cora-case.json --analyst-request /tmp/cora-questions.json` reuses the original Git-bound artifact and workflow auditors, software ontology, process catalog and reticulum. `cora verify-method-synthesis /tmp/cora-case.json --repo .` replays the exact committed source. Optional `--artifacts`, `--workflows` and `--process` inputs must be independently reverified and share one commit; optional `--hypotheses` claims are never execution evidence.

The [method atlas](../cora.method-atlas.json) connects fourteen CORA procedures to nine industry methods as inspiration, **not standards certification**. The [AND DoD](../cora.method-synthesis-dod.json) keeps seven source obligations distinct from four external requirements. A workflow role disagreement is `SOURCE_CONTRADICTION`; a shared caller is `OBSERVED_SOURCE_RELATION`; a proposed workflow adjustment is `INFERRED_REVIEW_ONLY`; unavailable process evidence is `OBSERVED_SOURCE_GAP`. The analyst request embeds bounded questions rather than source code or a purported LLM conclusion.

Do not interpret shared inputs as equivalent executions, source proofs as release attestation, or typed AI suggestions as authenticated facts. Real usability, maintained-target behavior, independent host/reviewer authority and postmerge effects remain outside this source-only case.
