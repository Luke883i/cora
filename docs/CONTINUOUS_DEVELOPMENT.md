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

Save receipts **outside** the target working tree. `--strict` on the pre/post commands emits exit code 2 for `BLOCKED` or bootstrap; it **never upgrades** any status to authorized. This PR introduces the policy for the first time, so its own BASE does not contain it and the bootstrap cannot be declared independently approved.

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
