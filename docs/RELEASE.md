# CORA — Continuous Ontological Repository Assurance: governed prerelease procedure

**Document status:** CURRENT
**Current scope:** Operator-only candidate validation and unpublished release conditions.
**Operational use:** Check candidate bytes, required reviews, hosting and rollback before any tag.
**Evidence:** Actual wheel/sdist receipts, CI, SCA limits and independently verified host state.
**Limits:** Current source is staged not published; no source verifier can authorize release.


**Status: staged, not published. Current source:** `cora-audit 1.0.0a5` (Python 3.11+, one `cora` CLI). PR59 is merged to `main@a01e0b121ac3734fd4ec1afa22781c90dbed1260`. This is a source change, **not a stable API, supported production release or independently approved distribution**. No public candidate is published. **Release = BLOCKED_EXTERNAL** pending the separately accountable operator gates below.

**Decision boundary:** L1 Git/source CI and local tests are valuable engineering evidence; bounded L2 pilots do not prove broad product acceptance; L3 external qualification, when claimed, requires real people, host controls, reproducible artifacts and accountable decisions. A source report is **not a self-issued** approval, certificate, signed provenance or permission to publish. A PASS for one level cannot complete the others.

## Release path — current operator runbook

1. **Freeze the intended commit.** Use a Draft PR with exact BASE/HEAD, source changes, code/contract tests, negative controls, risk owner and rollback plan. On an authorized checkout run `python -m unittest discover -s tests -v`, `python tools/verify_repository_contract.py --repo .`, `python tools/verify_artifact_roles.py --repo .` and `python tools/verify_release_readiness.py --repo .`. Use `cora process-run . --revision HEAD --change-base BASE_SHA --one-run --profile comprehensive --output /tmp/cora-release-run.json` and `cora verify-process /tmp/cora-release-run.json --repo . --one-run`. A caller-provided BASE is not authenticated GitHub PR metadata.
2. **Build and reconcile bytes.** The existing `CI | CORA release candidate verification` checks out the exact PR HEAD, builds wheel and sdist twice, compares builds, validates archives, installs in separate Python 3.11/3.13 test environments, computes `SHA256SUMS` and emits scoped manifests. Review the **actual artifacts intended for publication**, not an unrelated prior-SHA run. An unsuccessful or inconclusive job is a blocker.
3. **Verify host governance (G_GOVERNANCE).** An authorized GitHub administrator must demonstrate effective protected `main` branch rules, named required checks, no unauthorized bypass and an authenticated reviewer different from the author. A CODEOWNERS declaration, workflow YAML, CI success, Git hash or HTTP 403 ruleset response does **not** prove enforcement.
4. **Independently evaluate target behavior (G_BEHAVIOR).** For independently governed acceptance, assign real accountable operators to run an independent Git/source oracle against at least two actively maintained, different repositories with preregistered expected results and zero critical false PASS. Retain exact target commits, environment, failures, unknown dynamic consumers and independent review evidence. Controlled source fixtures and the Teddy/ICTC native Gold pilot are **not** independent maintained-target acceptance.
5. **Check user interpretation (G_USABILITY) and hostile execution (G_ISOLATION).** An independent usability observer should evaluate at least eight real participants (first-time developer and assurance reviewer roles), three tasks each, with at least 80% task completion and zero critical evidence-status misinterpretations. A qualified host operator must independently verify non-root isolated runtime, network/filesystem denial, resource bounds, no credentials, cleanup and actual timeout termination. Docker flags or simulated tests alone do not establish isolation. These are **external gates**: L3 remains optional for experimental use, not a prerequisite for ordinary authorized source inspection.
6. **Authorize separately.** Require accountable non-author review, release-manager acceptance, relevant vulnerability assessment, artifact/provenance verification, documented rollback/monitoring owner and CI on the **actual merged main SHA**. Only after all applicable gates may that operator create a protected version-matched tag, verify the remote ref, and publish a GitHub pre-release with matching wheel/sdist, hashes and release notes. PR creation, a draft release and a tag name are not publication. No automated CORA command may grant this authority.

**On failure:** retain original diagnostic evidence, mark the source or external gate `FAIL`, `NOT_RUN` or `BLOCKED_EXTERNAL`, and do not automatically merge, tag or publish. Restore from an authorized known-good commit and re-qualify the changed SHA. Existing build scripts do not create releases, publish to PyPI or sign statements.

## Post-PR52 CTO procurement and software supply-chain status (source-scoped)

| Item | What currently exists | What is still required |
| --- | --- | --- |
| Package | MIT, Python 3.11+, `cora-audit 1.0.0a5`, zero declared mandatory runtime Python dependencies | Installer compatibility and adopter legal review |
| Reproducibility | Candidate wheel/sdist parity, install fixtures and `SHA256SUMS` in CI | Validate final intended uploaded bytes and frozen tag |
| **SBOM** | **CONFIGURED_IN_PR55_CANDIDATE_CI**: physical CycloneDX 1.6 for built wheel/sdist; strict structural validation and original-byte replay | Transitive/optional inventory, environment coverage and external review |
| **SCA** | `pip-audit==2.10.1` on direct installed build tools, raw scanner output; no blanket clean claim | Review actual scan, feed provenance, transitives, host, target tools and remediation |
| **SLSA/in-toto** | Unsigned local source/build observation; **NOT_ATTESTED** signature/SLSA statement | Independently trusted issuer, signatures, policy and digest verification |
| Runtime/security | Source-only default; authorized native pilots; no supported production security SLA | Independently validated isolation, incident handling, threat model and support commitment |
| Hosting/review | **BLOCKED_EXTERNAL**; source declarations are not enforced permissions | Protected branch, independent reviewer and authoritative host readback |
| Product acceptance | Bounded L1 and selected L2 observations; no independent enterprise decision | Maintained target, measured usability/cost, owner acceptance and rollback |

**Scope:** `tools/release_verify.py` owns original wheel/sdist verification; the PR55 supply-chain pipeline produces `cora.cdx.json`, `cora-scoped-sca.json`, `cora-unsigned-build.json` and schema validation receipts. Their digest binding is not third-party identity, software completeness, a SOC 2/ISO 27001 certificate or authorization. Scanner failures must not be interpreted as vulnerability-free results.

## Historical source and release identity — not current operating instructions

**PR40 merged source knowledge** on 7 November 2026; PR41 established a bounded 30-node final-experimental source baseline. PR32/PR34 were procedure and candidate-build stages; PR39 merged a source-only independent acceptance protocol, not a release; PR54/PR55 added version/SBOM/SCA checks; PR56 separated L1/L2/L3 and documented the optional external study protocol. These milestones are preserved in [CHANGELOG](../CHANGELOG.md), original Git commits, [architecture](ARCHITECTURE.md) and the [independent qualification DoD](../.cora/contracts/dod/independent-qualification-dod.json), not alternative release instructions.

**Existing GitHub release draft:** `CORA v1.0.0a4 — First Alpha Release` (historical GitHub Release ID 435292303) was reported on 7 November 2026 as `draft=true`, `prerelease=true`, `published_at=null`, zero assets. A read-only request for `refs/tags/v1.0.0a4` returned 404 at that time. These are **dated host observations**, not evidence of the current tag state, public release or a signed artifact. The historical `1.0.0a4` procedure must **not** be copied to publish `1.0.0a5`. Reconcile any existing draft under the authorized release manager; do not create a duplicate.

**Current status:** publication and independently governed acceptance remain `BLOCKED_EXTERNAL`. [Governance](../GOVERNANCE.md) · [Security](../SECURITY.md) · [Documentation](INDEX.md).