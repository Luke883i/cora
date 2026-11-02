# ADR PR-06 - Scoped transformation and local guard

Status: experimental; requires independent review. Base: PR-05 merged.

## Decision
PR-06 implements only exact tracked-document path renames (.md, .txt, .rst), not general code/module/workflow deletion or renaming. Every proposal is a deterministic plan over a clean Git HEAD, including SHA-256 preimage/postimage hashes and a domain-separated plan digest. All Git-tracked files up to 2 MiB are searched for exact old path references. A match in an unsupported file type, or a symlink, oversized, nonregular or otherwise unanalysable tracked artifact, BLOCKS the plan. External consumers and implicit nonliteral references are not covered.

Applying requires an exact approval digest, fresh source-plan recomputation, clean worktree, and an explicit argv-based test command without shell wrapping. The verifier is not sandboxed. Its return code and the owned files' final hashes are checked. On failure, compensating rollback restores the owned document files; side effects created by the verifier or external systems are NOT rolled back. This is not atomic, distributed or generally equivalent refactoring.

The installer produces a local guard: .cora/policy.json, .cora/verify.py (standalone Python stdlib script), and .github/workflows/cora-architecture-guard.yml. The guard compares an explicit Git base to HEAD, rejects changes to its own files after bootstrap, cross-product Git renames, and explicit cross-product Python AST imports; unknown dynamic and relative imports in changed Python files block. It is not secure against a malicious PR changing the guard or workflow unless an independent required CI check and protected branch/rulesets are configured.

## Backward-derived DoD

| ID | Obligation | Evidence |
| --- | --- | --- |
| T06-L1 | Read-only canonical plan and source SHA | actual Git doc fixture |
| T06-L2 | Approval, fresh recomputation, no forged/stale plans | tamper, dirty, stale commit tests |
| T06-L3 | Supported exact text consumers only; unsupported consumers block | binary, source-code, symlink fixture |
| T06-L4 | Explicit tests, postimage hashes, compensating rollback | success, failing verifier and verifier-side-effect fixtures |
| G06-L1 | Installable, versioned standalone local verifier | install and execute .cora/verify.py |
| G06-L2 | Git change provenance, protected paths and product boundaries | cross-move, import, self-change tests |
| G06-L3 | Unknown dynamic/relative imports fail closed | AST tests |
| I06-T | Independent real Git tests for localized transformation | 16 local fixture cases |
| I06-G | Independent real Git guard tests | 12 local fixture cases |
| I06-F | One million distinct seeded contract risk vectors | 24 family-specific contexts, oracle and witnesses |
| G06 | Regression tests, wheel installation, CI complete, independent review | release gate |

## Falsification boundaries
The million mutations are synthetic 20-axis vectors under 24 family-specific scopes. They are NOT a million real Git repositories or one million successful transformations, and their policy oracle draws on the same declared finite contract. PR-05 safe-deletion remains non-authoritative. The PR-06 tool does not certify complete reachability, code equivalence, external references, runtime, build/deploy or anti-tamper enforcement without protected CI.

## Next step
PR-07 should test a pinned wheel/sdist in independent clean environments and on unrelated repositories, then add trust-boundary verification and supply-chain attestations. General source-code renaming requires dedicated language/CI/runtime closure and codemod recipes.
