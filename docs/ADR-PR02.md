# ADR-PR02 — Evidence contract and immutable Git provenance

Status: implementation candidate (PR-02). Depends on merged PR-01.

## Decision

A CORA evidence record represents only the observed state of a Git object in one immutable commit. It carries: schema, 40/64-digit commit SHA, relative path, Git object ID and mode, bounded SHA-256 content digest/size for regular blobs, epistemic state and a domain-separated record digest. Records form an ordered ledger with a separately domain-separated digest. A ledger must validate both structurally and (using `cora verify-ledger --repo`) by recomputation from actual objects present in Git. This is not a signature or a trust guarantee against a party able to replace both the ledger and its authoritative Git source.

The existing `cora audit` remains a working-tree inventory, explicitly distinct from `cora snapshot` which reads committed Git objects only. Neither runs target source code. No deletion, runtime reachability, import equivalence or cross-repository closure is claimed.

## Contract

- `cora-evidence/1`: strict field set; no unknown fields; safe relative POSIX paths; mode/status consistency; commit provenance; content SHA-256 for regular-file blob up to 8 MiB (configurable internally); no positive verification for symlinks, submodules, Git LFS pointer payloads, or oversize blobs.
- `cora-ledger/1`: deterministic ordered records, unique paths, consistent commit, fixed coverage claims, SHA-256 digest over canonical JSON with domain separation.
- `cora-ledger-verification/1`: emitted only when a ledger passes structural validation and exact comparison with a newly derived ledger from the specified repository commit.

CORA rejects invalid encoding, unsafe paths, digest/commit mismatch and fabricated claim statuses. It cannot establish external consumer absence, all runtime behaviors, semantic equivalence or authenticity against maliciously modified Git sources.

## Backward-derived PR-02 DoD

| Gate | Requirement | Evidence |
| --- | --- | --- |
| E02-L1 | Stable record schema and deterministic digest | unit fixtures + canonical JSON |
| E02-L2 | Bound facts to immutable commit | Git blob/tree provenance + actual commit comparison |
| E02-L3 | Separate unresolved from observed | symlink, gitlink, LFS, large-blob coverage statuses |
| E02-L4 | Ledger provenance and integrity | tamper, duplicate, reordering, cross-commit rejection |
| E02-L5 | Working-tree isolation | uncommitted changes cannot modify frozen ledger |
| E02-I1 | Executable reproducibility | repeat seeded 1M in-memory mutations twice |
| E02-I2 | Independent local fixture | create actual Git commits and run snapshot/verify |
| E02-G | Backward compatibility | PR-01 tests pass and one CLI remains |

## Falsification limits

The preseeded corpus uses 24 mutation operator families and deterministic Mix64 with seed `883`. It generates **one million varied in-memory evidence objects**, not one million physical Git repositories or independent empirical datasets. The category expectations are predeclared, so zero mismatches demonstrate model/validator consistency within fixtures, not general semantic correctness. The per-case stream digest includes canonical mutated object bytes to detect changes in corpus content (not just test labels). PR-03 onward should introduce external graph and policy oracles.

## Scope and follow-up

PR-03 must build graph/ontology without elevating `observed_git_blob` into `used_at_runtime`. PR-04 must publish adapter coverage contracts; PR-05 may issue PASS_SCOPED only when relevant evidence closures and obligations are demonstrated. PR-06 owns deletion and verified rename—not PR-02.
