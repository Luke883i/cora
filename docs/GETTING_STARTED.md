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

## Un solo comando e un Atlante HTML degli esiti reali

Usa `cora process-run . --one-run --process full --revision HEAD --output /tmp/cora-run.json --atlas-html /tmp/cora-run.html`. Apri l'HTML nel browser: la sezione **00 · Esiti realmente osservati** distingue metodi eseguiti, riusi, blocchi, attività non eseguite, tempi e lineage del commit. Le 71 funzioni del catalogo sono elencate come **dichiarazioni**, non come 71 esecuzioni. Non occorre una seconda CLI. L'HTML è offline, responsive e generato dallo stesso rapporto machine-readable verificabile con `cora verify-process /tmp/cora-run.json --repo . --one-run --atlas-html /tmp/cora-run.html`.

Per impostazione predefinita i test runtime restano `NOT_RUN`. Solo con `--execute-self-tests` su un checkout CORA affidabile vengono eseguiti i test unitari locali (nessuna attestazione indipendente o approvazione). Per repository terzi senza i contratti CORA, l'atlante mostra i risultati sorgente realmente disponibili, ma non inventa un catalogo di 71 attività.

Per includere anche il benchmark semantico pre-seeded nello stesso Atlante HTML, aggiungi `--model-stress-cases 100000` al comando One-Run: è un modello finito di controesempi e non modifica i sorgenti Git.


## New independent reviewer exercise

Open the Independent qualification section of a comprehensive One-Run Atlas. Locate G_BEHAVIOR, G_USABILITY, G_ISOLATION and G_GOVERNANCE, inspect their source paths and distinguish the BLOCKED_EXTERNAL obligations. Find one actual test result, identify the corresponding Git commit, and explain why a native-Git synthetic fixture, Docker command, self-submitted study sheet and a CI badge cannot individually certify the product. The study script and externally observed threshold are described in [Release](RELEASE.md); no participant observations are asserted merely because this documentation exists.


## PR44 — Verify without CORA jargon (three-task independent challenge)

**Goal B (reviewer access) is not solved by a glossary alone.** A newcomer must
be able to challenge a claim without adopting the same producer's proof rules.

After PR43 has been merged, or in the PR44 branch which contains its commits,
choose a concrete ancestor SHA and create a source-comparison report:

```sh
python tools/verify_engineering_closure.py --repo . --closure-base BASE_SHA \
  --revision HEAD --output /tmp/cora-closure.json
python tools/independent_git_oracle.py --repo . \
  --closure-report /tmp/cora-closure.json --reader-brief /tmp/cora-reader.md \
  --output /tmp/cora-independent-check.json
```

The second command independently recalculates every closure counter from the
original Git commit objects. It does **not** import the producer, but it
does share repository maintainership and thus does **not** attest independent
human judgment or separately owned production behavior.

The generated Markdown starts with three questions: **what changed**,
**what was actually demonstrated**, and **what could disprove it**.
Reviewers need not understand the internal word *reticulum* (dependency graph
of required checks), *non-promoting* (limited evidence cannot imply stronger
authorization), *owner-pinned* (declared responsible actor; not verified
identity), or *retrograde* (requirements worked backward from acceptance).
`HOST_ENGINEERING` has no verified current canonical definition in this
review and must not be guessed at.

**Backward-derived acceptance contract B0–B7:**

- **B0**: native Git recomputes original-source inputs at exact BASE/HEAD.
- **B1**: independent implementation rejects any changed count/status/authority.
- **B2**: an explicit three-task reviewer path has plain-language explanations.
- **B3**: original-Git physical scope mutation and 32 finite receipt mutants
  are rejected or surfaced as `REFUTED`, never promoted to product acceptance.
- **B4**: no new CORA command, executor, product authority or host credentials.
- **B5**: a reviewer can identify one claim, its source, counterexample and
  missing external witness from the packet and original Git.
- **B6 (EXTERNAL, NOT SATISFIED BY CODE)**: eight unfamiliar participants,
  three tasks each, at least 80% task completion and zero critical mistaken
  evidence promotions, with observed task data and preregistered success rules.
- **B7 (EXTERNAL, NOT SATISFIED BY CODE)**: separately maintained targets,
  independent human review and actual host checks remain subject to PR39/41.

A local test PASS covers B0–B4 **only**. B5 has an executable reader route,
but cannot be declared human-validated without B6. PR44 remains Draft until
an accountable non-author reviews exact-HEAD results. Its implementation is
not permission to release, merge automatically or count external gate closures.
