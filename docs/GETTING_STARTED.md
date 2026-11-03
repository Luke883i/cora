# Getting started with CORA

CORA is a local source-assurance command-line tool. It is not a coding agent or a merge authority. This tutorial uses the CORA repository itself, which has a committed ontology. For other projects, [adopt CORA](AGENT_ADOPTION.md).

## Prerequisites

Python 3.11+, Git, an authorized local checkout, and an output directory outside the analyzed repository. The repository may be private: merely having the URL is not access.

## Install and inspect

Run from the CORA checkout:

```sh
python -m pip install -e .
cora --help
cora version
cora audit . --output /tmp/cora-worktree.json
cora snapshot . --revision HEAD --output /tmp/cora-ledger.json
cora verify-ledger /tmp/cora-ledger.json --repo .
```

`audit` reads the working tree. `snapshot` reads pinned committed Git objects; `verify-ledger` recomputes that bounded source observation.

## Examine architecture

```sh
cora graph . --revision HEAD --output /tmp/cora-graph.json
cora artifact-audit . --revision HEAD --output /tmp/cora-roles.json
cora verify-artifacts /tmp/cora-roles.json --repo .
```

The product/software map comes from a maintained declaration. Static imports are incomplete candidates, never an exhaustive consumer list.

## Understand the report

- `PASS_SCOPED`: this named source check passed, not a global correctness or release guarantee.
- `BLOCKED` / `DEBT_BLOCKED`: required information or source evidence is unavailable.
- `REFUTED`: a named claim has a counterexample.
- `BLOCKED_EXTERNAL`: independent host, runtime or reviewer evidence is not supplied.
- A matching Git hash or report digest is not a publisher signature or proof of behavioral execution.

For the next steps, choose [agent adoption](AGENT_ADOPTION.md), the [CLI reference](CLI_REFERENCE.md) or the [architecture](ARCHITECTURE.md). Outputs here use Unix `/tmp`; on other platforms choose a suitable directory outside the checkout.

No independent newcomer usability test is claimed by this tutorial.
