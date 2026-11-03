# CORA governed prerelease procedure (GitHub and Python distribution)

Status: **staged, not published**. Product name: CORA — Continuous Ontological Repository Assurance. Package: `cora-audit`; software: `cora-engine` and `cora-release-verification`; repository: `Luke883i/cora`. Current proposed version in PR-15: `1.0.0a4` (PEP 440 *alpha*, not a final release or `rc`).

## GitHub-native workflow
1. Create a topic branch at an exact `main` SHA. Author atomic semantic commits with source changes, independent negative tests, build/verification changes, documentation and DoD. The branch is not an approval.
2. Open a **Draft Pull Request** targeting `main`. Include exact base and head SHA, changelog, threat/compatibility impact, explicit open obligations and evidence links. Use GitHub **Checks** and Actions workflow runs from that exact HEAD, never an author-provided screenshot or unverifiable hash.
3. Run `python -m unittest discover -s tests -v`, `python tools/verify_repository_contract.py --repo .`, `python tools/verify_artifact_roles.py --repo .`, `python tools/verify_release_readiness.py --repo .` and CORA-on-CORA read-only `process-run` + `verify-process`. Build/install wheel and sdist through the existing pinned release-candidate workflow. Retain exact-artifact SHA-256 and Python 3.11/3.13 test evidence.
4. An **administrator** must separately verify that protected `main` requires trusted checks and a non-author reviewer. Check active branch rules; CODEOWNERS text and CI-green detection do not establish enforcement. Any unavailable admin evidence means **BLOCKED_EXTERNAL**.
5. After independent review and all DoD obligations, the authorized maintainer merges through GitHub. Re-run post-merge verification on exact merge SHA; confirm all required checks. An approved human **release manager** may then create a protected, version-matched tag (e.g. `v1.0.0a4`), and a GitHub **Release** marked **pre-release** with release notes, wheel/sdist, hashes and source/build provenance when verified. The tag and assets must refer to the reviewed commit. Neither the PR nor an alpha version implies publication.
6. Record post-release issues/monitoring, rollback and consumer impact in GitHub Issues/PRs and document owners. Do not infer deployment SLOs or incident-free operation without a monitored system.

## Reproducibility and downgrade path
A passing source verifier is a bounded metadata result, not an access-control assertion. A failed or unavailable check leaves the PR Draft and the release unpublished. Existing build scripts produce candidate artifacts but do not create GitHub Releases, publish to PyPI or sign provenance. This release procedure itself cannot configure GitHub branch protections; the first trusted bootstrap must be approved independently.

References: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches ; https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases ; https://packaging.python.org/en/latest/discussions/versioning/ ; https://slsa.dev/
