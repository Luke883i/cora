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

## PR-16 runtime-intake boundary (candidate)

Treat ZIP paths and source bytes as untrusted, including inside Docker. Never interpret `runtime-observe` success, an output digest, a simulated executor test or `verify-fusion` as proof of sandbox confinement, real target coverage, human approval or an authorized release. Review [the semantic lattice DoD](docs/DOD_PR16_SEMANTIC_LATTICE.md) before proposing execution. Do not run unknown ZIP code merely to satisfy an audit gate: a read-only source result is legitimate and runtime remains NOT_EXECUTED.

## PR-17 agent delivery (CORA as framework, not coding agent)

Before coding derive prerequisite cuts: `cora dod-plan --stage intake` then `cora dod-plan --stage implementation`. Before PR use `cora dod-plan --stage premerge`, `cora dod-assess`, `cora verify-dod`, and the existing `dev-premerge`. Run `cora stress-agent-dod --require-full` for model/contract changes; use real target-code mutants and executed regression separately. Postmerge: `dev-postmerge` on merged main; release: `dod-plan --stage release` with external review. Do not self-attest missing runtime/hosting witnesses or introduce a new product owner. Full rules: [AI assistant method](docs/AI_CODE_ASSURANCE.md).

## PR-18 historical anti-regression

Always derive source-model coverage from actual generated fault masks, not iteration positions. Use negative tests against physically changed CORA implementation, distinguish JSON policy mutants from source-code mutants and real third-party product tests. Explain the first unresolved prerequisite and re-pin merged main. See [severe audit](docs/AUDIT_PR18_MAIN.md).
