# Artifact roles — overlapping declarations, not filename classification

**Document status:** CURRENT
**Current scope:** Current multi-role source classification for Git-tracked artifacts.
**Operational use:** Inspect role overlap and unresolved coverage without inferring unused code.
**Evidence:** cora.artifact-roles.json, audit command and original Git paths.
**Limits:** A declared role or absence of imports never authorizes deletion.


**v1 experimental contract:** `cora.artifact-roles/1`, source-traced to a committed Git revision. Repository, product, software, deployable, artifact, test and contract are distinct ontology dimensions. Roles can **overlap**, and a path can be source **and** test **and** contract verifier **and** fixture. Conversely, a file called `test_*.py` need not be a working test or even imported by CI. `*.json` does not imply contract semantics, and a file named `legacy` is not evidence that it is obsolete.

## Operational interface

```bash
cora artifact-audit . --revision HEAD --output /tmp/roles.json
cora verify-artifacts /tmp/roles.json --repo .
cora file-lab . --path tests/test_pr10_artifact_roles.py --output /tmp/lab.json
python tools/verify_artifact_roles.py --repo .
```

The result includes every Git-tracked artifact, declared roles (possibly more than one), exact matching rules, source record digest, declaration digest, unclassified artifacts and unmatched rules. A report altered and rehashed by an attacker must **not** verify against committed Git source. `artifact-audit` returns exit code 2 for a nonempty unclassified list or stale rules; it does **not** assert that declared roles have been behaviorally demonstrated. A missing role manifest on an unrelated repository remains an explicit unknown in `file-lab`, not an inference based on spelling.

### Engineering rules

1. Role assignments are **maintainer assertions** bound to a Git commit, not observations of execution, contract enforcement or consumer completeness.
2. No filename, directory, extension, negative static-import finding or LLM hypothesis may establish unused status. Positive runtime observations from the operator are still untrusted unless independently validated.
3. Multi-role annotations **accumulate**; no rule silently overrides another. Add exact overrides only when authoritatively justified. Check `stale_rules` and `unclassified` on every PR.
4. `TEST`, `CONTRACT_VERIFIER`, `WORKFLOW`, `POLICY`, `GOVERNANCE` and `LICENSE` are explicit review obligations, not deletion permissions.
5. Artifacts may only change state via documented investigation, independent review, reversible controlled experiment and actual verification. `QUARANTINE_CANDIDATE`, `ARCHIVE_CANDIDATE` and `RENAME_CANDIDATE` are **proposal states**; `DELETE_BLOCKED` is not executable.

## Independent falsifiers

A temporary real Git repo contains `src/test_contract.py` as an explicit **three-role** source/test/verifier; `src/contract_test.py` is source **only**, even though the name is suggestive. Other counterexamples include spoofed artifact reports with recomputed self-digest, untracked additions, malformed or escaping glob paths, unknown artifacts, a dirty working tree, and a changed committed manifest.

## Semantic novelty saturation

The repeatable finite corpus consists of 24 realistic scenario *labels* × 16 role subsets × 32 uncertainty subsets = **12,288 defined semantic categories**. Starting at seed `883`, enumerate **M = 1,000,000 evaluations**, then another **10,000,000** with no new category relative to M. The tool reports the actual last discovery index and stream SHA-256. **The additional 10M evaluations are repeats of a closed, predefined model; they do not show the real-world semantic space is exhausted**, do not represent 11M unique repositories/files and do not validate semantics of arbitrary runtimes. An independently expressed finite policy oracle checks each decision, but shares the fixture specification.
