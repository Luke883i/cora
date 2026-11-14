# CORA holistic forensic archaeology

**Document status:** CURRENT
**Current scope:** Cross-scale Git archaeology without changing target source.
**Operational use:** Inventory original history, declared roles and source dependency candidates.
**Evidence:** Git SHA, commit episodes and bounded AST/manifest adapters.
**Limits:** Historical cochange does not prove present runtime usage.
**Applicable current DoD:** [holistic-forensics](DOD_HOLISTIC_FORENSICS.md) specifies scoped obligations and open evidence; its existence is not proof that any gate passed.


**Experimental, read-only.** A pinned Git commit is source truth; PR identity is not reconstructible from Git alone after squash/rebase and the optional `--pr-index` is an *unverified operator assertion*. Development groups are not business product identities, and co-change is **not** a runtime edge.

## Top-down multiscale inference

Product → software → repository Git history → PR/commit episodes → temporally coupled development groups → file/role/manifest/partial AST candidate dependencies → optional file-lab selection → AI counter-hypotheses → human decision.

**All-in-one `holistic-audit`** invokes only safe read-only methods. It pins a commit, runs the Git snapshot, owner-declared ontology/graph, manifest adapter, overlapping artifact roles and bounded history, then derives groups. A commit records exact path changes and rename-similarity hints, not symbol equivalence. Merge commits are excluded from cochange counts. A group requires at least 2 observed joint commits, Jaccard ≥ 0.5, no known cross-product ownership conflict and ≤ 24 paths. The full report is source-revalidated via `verify-holistic`.

**Possible scaffold waste** = undeclared role + no observed static import candidate + ≤1 touch in the sampled history. **Possible disconnected gold** = protected declared role + no observed static import. These labels mean investigate or retain, **never delete**. Truncated commit history, external consumers, runtime/build/deploy, copied symbols and missing PR mappings remain unknown.

AI group hypotheses are typed annotations (existing `file:` / `commit:` refs, counterevidence, self-reported ranges). Citation existence is not inference correctness. `annotate-groups` cannot move, archive, quarantine, rename or delete a file. The orchestrator does not invoke LLMs, run target code, execute tests, alter Git or scan remote registries. These have separate explicit workflows and proof contracts.

## Commands

```bash
cora holistic-audit . --revision HEAD --max-commits 256 \
  --focus src/cora/graph.py --output /tmp/cora-holistic.json \
  --ai-request-output /tmp/group-ai-request.json
cora verify-holistic /tmp/cora-holistic.json --repo .
cora archaeology . --max-commits 256 --output /tmp/cora-history.json
cora verify-archaeology /tmp/cora-history.json --repo .
cora annotate-groups /tmp/cora-holistic.json --repo . \
  --hypotheses /tmp/ai-reply.json --output /tmp/overlay.json
cora stress-archaeology --seed 883 --cases 1000000
```

External PR association input: `{"schema":"cora-pr-index/1","commits":{"<sha>":12}}` — **unverified without independent GitHub reconciliation**.

## Method adapters and sources

| Evidence layer | Implemented | Next stronger integration |
| --- | --- | --- |
| Git archaeology | bounded commit diffs, rename hints, topics | `git blame -L`, PR-commit verification, copy/split lineage |
| Behavioral change coupling | co-change frequencies and Jaccard | CodeScene-style historical hotspots, bulk-edit noise filtering |
| Static/semantic software graph | current CORA Python AST candidates | Joern/CodeQL CPG + cross-language symbol/dataflow |
| Refactoring history | Git rename similarity | RefactoringMiner AST-level transformations |
| Runtime | existing file-lab supplied observations, unverified | signed service/version/environment-specific OpenTelemetry |
| AI abductive inference | typed grounded/ungrounded refs; no authority | labeled gold/scaffold corpus, calibrated abstention |
| Outside repository | UNKNOWN | deploy/registry/API/external consumer verified graph |

Method references: [Git log](https://git-scm.com/docs/git-log), [PyDriller](https://github.com/ishepard/pydriller), [RefactoringMiner](https://github.com/tsantalis/RefactoringMiner), [CodeScene](https://helpcenter.codescene.com/help/articles/1844075-how-to-assess-coupling-health-in-codescene), [Joern CPG](https://docs.joern.io/code-property-graph/), [CodeQL dataflow](https://codeql.github.com/docs/writing-codeql-queries/about-data-flow-analysis/), [OpenTelemetry](https://opentelemetry.io/docs/concepts/resources/), [NIST SSDF](https://csrc.nist.gov/pubs/sp/800/218/final), [OpenSSF OSPS](https://baseline.openssf.org/). These are reference methods, **not proof of existing integrations or standards certification**.

**Additional falsification gate:** a complete ownership set is carried through transitive cohort unions, so an unowned bridge cannot join two declared different products. Truncated Git history disqualifies the short-lived scaffold heuristic; the report instead emits `HISTORY_WINDOW_TRUNCATED_UNKNOWN_LINEAGE`.

## H-FORGE optional experimental profile

For bounded before/after change analysis, `src/cora/hforge_profile.py` composes
existing Git evidence and the opt-in finite operational-equivalence verifier.
It reconciles the fixed 77-case declared universe against the original Git atlases,
provides tracked-tree measurements and can replay the existing source One-Run.
It is **not** an additional engine or default CLI command. Static omissions,
dynamic/external consumers, persisted effects, independent review and governed
product acceptance remain open unless separately observed. The committed
`.cora/contracts/profiles/hforge-profile-v1.json` and
`.cora/contracts/dod/hforge-transplant-dod.json` are declaration/DoD inputs,
not attestations that these prerequisites have been satisfied.
