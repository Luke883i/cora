# Instructions for coding agents (including iKant)

CORA is **the independent development evidence and governance framework**, not a coding assistant. An agent may propose, write and test changes, but cannot certify itself, approve review, merge, release or delete code under CORA authority.

1. Start with `README.md`, `GOVERNANCE.md`, `docs/CONTINUOUS_DEVELOPMENT.md`, and `docs/DOD_CONTINUOUS.md`.
2. Pin `base` and proposed `head` Git SHAs. Work on a branch; never push to or rewrite protected `main` for the purpose of satisfying a gate.
3. Run `cora dev-premerge REPO --base BASE --head HEAD`, `cora verify-dev-gate` and relevant `cora process-run` modes. Record blockers and unknowns, not just passing tests.
4. Use `cora agent-check` to reconcile an optional versioned proposal with exact Git paths. Agent test claims, confidence estimates and reviewer labels are untrusted assertions until independently verified.
5. For high-risk modifications to `.github/workflows/`, `.cora/`, `src/cora/guard_runtime.py`, security and release controls, require a separate human security reviewer **and independently protected hosting rules**. The source file cannot enforce those permissions.
6. New functionality requires code, a regression/negative fixture, README/DoD updates and an explicit trust boundary. Keep the single Python package and `cora` entrypoint; do not duplicate engine components.
7. Never infer absence of consumers or safe deletion from missing static imports or model confidence. No code deletion is authorized by the continuous gate.
8. Before requesting merge, show exact CI execution SHA, deterministic receipts and unresolved coverage. After merge, produce a post-merge report and investigate new debt signals without treating them as proven defects.

**A CI job controlled by the PR is not an independent approver.** Policy bootstrap, external platform protections and real operational outcomes remain human/external gates.
