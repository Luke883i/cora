# CORA operational universality — finite, closed and falsifiable

**DoD abstract A0.** Operational universality is the universal quantifier over an **explicit, versioned and closed set of observations**, *not* all possible behaviors or inputs. It must be impossible for a command, observation or negative control to disappear without refuting the claim. Source-byte parity, synthetic models and independently executed native behavior have different epistemic status.

**DoD global (scoped) G-OP.** Two **distinct** ancestrally related original-Git commits are equivalent on the precisely declared `B_OP` if and only if (I1) the observable universe is complete under the registered atlas and probe contract, (I2) every observation executes in equivalent pinned runner conditions, (I3) exact return code/stdout/stderr are equal for *every* case, and (I4) the report independently replays from the exact same commit pair and mutations fail closed. `G-OP = I1 AND I2 AND I3 AND I4`. An observed bounded G-OP PASS **never** promotes the separate product-level E1 runtime-completeness, E2 external systems/side effects, or E3 independently authenticated reviewer and host governance leaves.

**Denominator.** `B_OP = (all 71 declared CLI commands × --help) UNION {version, process-list, snapshot-pinned, graph-pinned, dod-plan-pinned, stress-128}`. The declared command list is read independently from each pinned commit's `.cora/assurance/capability-atlas.json` and must match both versions and the pinned 71-command expectation. The six native probes are fixed in this contract; no success is inferred for an omitted or unexecuted case. Source repository and baseline input Git revision are pinned, Python interpreter and seed/local environment shared. Only the specified **read-only** operations are executed; never execute all CLI commands indiscriminately.

**Intermediate → local gates and metrics.**

| Gate | Local obligations | Refutation |
| --- | --- | --- |
| I1 · universe | L1 original Git base/head distinct, ancestral; L2 dual atlas equality; L3 71/71 command closure + six non-optional native probes | missing, added, renamed or unregistered command, path or probe |
| I2 · execution | L4 same Python interpreter, environment, pinned Git input; L5 exactly one captured receipt per version/case | timeout, nonzero exit, empty/missing output, unobserved case |
| I3 · behavior | L6 return code + full stdout and stderr byte-for-byte equality on **77/77** cases | positive-control parser mutant or output divergence |
| I4 · replay | L7 recompute report on BASE/HEAD; L8 altered receipt or pruned row rejected; L9 physical original-Git mutant must fail | false PASS, different commits, mutated command help |
| E1–E3 · global product | Independent full runtime observability, effects/environment boundary and authenticated governance | **BLOCKED_EXTERNAL** until independently evidenced |

**Evidence scope.** `G-OP` can be truly PASS *within B_OP* while `G_PRODUCT_UNIVERSAL` remains `BLOCKED_EXTERNAL`. CI success on a specific HEAD is an execution observation, not proof of protected host enforcement. Full source identity shown by PR #69 is not itself an I3 native-behavior receipt. As soon as the CLI atlas grows or changes, the denominator must be requalified rather than silently accepted. The host's merge-base is provenance information, not a self-issued independent signature.

**Execution (opt-in).** `python tools/verify_operational_equivalence.py --repo . --base BASE_SHA --head HEAD_SHA --execute-pinned-native --output /tmp/cora-operational.json`; independently re-execute `--verify-report /tmp/cora-operational.json --execute-pinned-native`. Run only on trusted CORA commits in an isolated CI runner; the process deliberately executes CORA CLI code from both commits. Exact final-HEAD CI, retained receipt, negative mutants and a non-author reviewer are separate gates. This command is an assurance probe, not an autonomous agent, a runtime emulator, or a new CORA product. 
