# CORA applied to CORA: PR01–11 archaeological preliminary audit

Evidence source: GitHub PR changed-file lists, `Luke883i/cora` main `fcf7ae2bfeab81bbdbf8b0e5a777991b84ffccde` on 3 November 2026. **This is not a full native Git atomic-commit replay.** Run `cora holistic-audit` on a complete clone for that evidence.

**Product:** `cora`, forensic maintenance (not automatic deletion). **Software:** `cora-engine` plus `cora-release-verification`. **Repository:** GitHub source, contracts, tests, policies and CI.

Preliminary episodes: PR01–03 package/provenance/ontology; PR04–05 manifest adapters/closure; PR06–07 transformations/guard/release; PR08–10 documentation, file lab and multi-role contracts; PR11 selection for human investigation. Many PRs repeatedly edit README, CLI, package metadata and CI; this is historical cochange, **not proof of runtime coupling**.

**Scaffold review, no removal:** synthetic stress modules, old ADRs and verification receipts may be maintenance debt, but serve CI, lineage and test regression obligations.

**Unconnected gold:** `tools/verify_repository_contract.py` and `tools/release_verify.py` have high-value CI/release roles despite no ordinary runtime import; workflow YAML and test fixtures are operationally valuable. This falsifies naive orphan/dead-file classification.

**Blocked:** authenticated PR mapping, release/build/deploy and external consumer closure, runtime provenance, independent labels for false-positive measurement, actual source-code deletion proof. No destructive action justified.
