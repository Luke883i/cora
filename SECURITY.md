# Security policy — CORA alpha

CORA is an experimental local repository-analysis and scoped-maintenance tool. There is **no supported production release or security-update SLA** at this time. Security claims are scoped to tests and documented code paths, not blanket guarantees.

## Report a vulnerability

For a private repository, use GitHub's private vulnerability reporting feature **if enabled**. Otherwise, contact a repository maintainer through an already established private channel; do not post exploit details or private repository content to a public issue. The project does not yet publish a dedicated security mailbox; do not assume one exists.

Please include affected revision, minimal reproduction, relevant scope, and potential impact. Avoid running unknown build scripts or verifier commands against systems or data you do not control.

## Trust boundaries

- `cora audit`, `snapshot`, `graph`, and adapters are intended as *read-only* analyzers of local content; they are not malware or adversarial repository sandboxes.
- `apply-rename-doc` runs a **user-provided verifier command** without sandboxing; rollback is limited to files managed by the transformation. Never run untrusted commands with elevated privileges.
- `.cora/verify.py` installed inside a target repository can be edited by that same repository. Bootstrap and changes to the guard require an **independently enforced GitHub required check / reviewer**; a CI file alone is not evidence of branch protection.
- Archive SHA-256, Git object hashes, and locally derived certificates are **not provenance signatures**. Independent release identity and protected publishing remain unresolved.

Tracked issues and verification expectations: [PR-01–07 audit](docs/AUDIT_PR01_PR07.md) and [DoD](docs/DOD.md).


## Forensic runtime and AI inputs

`file-lab` reads Git objects and optional bounded JSON annotations locally; source code is not sent to a model or executed. Runtime traces supplied by users are **unverified**, may contain sensitive operational identifiers and should be minimized and retained only in an approved location. AI hypotheses are untrusted text and cannot elevate certificate status, change the repository or authorize deletion. Confidence ranges are explicitly uncalibrated. GitHub CODEOWNERS and self-hosted checks are **not** adequate protection against authorized maintainer bypass without independent required reviews.

## v1.experimental declaration trust

Artifact roles are versioned owner declarations, not security labels authenticated by GitHub or an attested CI. Do not use a file name, a declared test/contract role, a self-hash or an AI hypothesis as proof of safety for quarantine, archive, rename or deletion. The current private-repository hosting configuration may lack enforceable protected-branch controls; release and merge gates require explicit administrator evidence. See [role contract](docs/ARTIFACT_SEMANTICS.md) and [v1 DoD](docs/DOD_V1_EXPERIMENTAL.md).

## External scanner evidence and process modes

SARIF inputs are untrusted caller-provided bytes, not authenticated alerts. Do not import private source paths, credentials or runtime logs from an unapproved scanner. `verify-debt` demands the same original SARIF input and source commit; this only proves deterministic replay, not tool authenticity, exploitability or closed external consumer paths. `process-run --process full` invokes safe read-only analyzers only. Findings never authorize remediation.

## ZIP, optional runtime and private-source boundary

ZIP intake checks bounded archive structure but does not certify executable archive safety or recover a trustworthy Git history. Optional Docker execution requires explicit opt-in and restrictive flags; this is **not** independent host isolation, runtime coverage or provenance attestation. Caller-provided verification commands can run under the operator's privileges. See [PR-16 source/runtime DoD](docs/DOD_PR16_SEMANTIC_LATTICE.md).

The Gold pilot requires separately authorized private-source access. Candidate PR workflows must not use broad private repository tokens; a public one-of-three frozen source readback does not validate the other repositories or their behavior. Workflow effect scanning observes **potential** effects, not trusted target-side readbacks. A source receipt, Markdown claim or Git digest cannot authenticate reviewer identity or release decisions. See [Gold method](docs/GOLD_ASSURANCE.md) and [agent adoption](docs/AGENT_ADOPTION.md).

## Supply-chain and enterprise evaluation disclosure (post-PR52)

The source declares Python 3.11+, MIT, zero mandatory runtime Python dependencies, and an unpinned lower-bound build backend (`setuptools>=77`). The candidate workflow checks wheel/sdist parity, separate installs, readback and SHA256SUMS; the PR55 candidate workflow is configured to generate a scoped CycloneDX 1.6 SBOM, perform a pinned pip-audit scan of the actual installed setuptools/wheel build-tool versions, and retain an unsigned SHA/Git-linked build record. No SPDX SBOM is claimed. This does **not** authenticate a signed release, establish SLSA/in-toto provenance, or attest complete independent SCA/CVE, transitive build dependencies, target-native runtimes, secret scanning, or release security. These are **NOT_ATTESTED** enterprise procurement controls, not proof that such attacks or vulnerabilities exist. Release remains unpublished and external authorization remains blocked. An SBOM is an inventory, not evidence of exploit absence or trustworthy execution.
