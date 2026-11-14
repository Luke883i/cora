# Getting started with CORA

**Document status:** CURRENT
**Current scope:** Minimal local installation, source replay and first-read interpretation.
**Operational use:** Install from an authorized checkout and verify one exact Git snapshot.
**Evidence:** Actual cora CLI and readback reports with pinned revision.
**Limits:** A ChatGPT conversation alone is not executed CORA or target-runtime proof.


CORA is a local, read-only-by-default **source assurance** framework, not an autonomous
coding agent, a sandbox attestation, a merge approver or a product certificate.
Start from an authorized checkout with Python 3.11+ and Git. Use an output
directory outside the repository (`/tmp` below is a Unix example).

## GitHub and ChatGPT Project from zero

**1. Create the target repository.** Open [GitHub](https://github.com), sign in, choose
**New repository**, provide an application name (for example `my-issues-webapp`),
choose private or public as appropriate, and initialize with a README. Keep
secrets, personal records and API keys out of public repositories. This
repository will contain **your product**, not CORA's source code. Record the
initial commit SHA; future changes must be reproducible from real Git history.

**2. Obtain CORA's instructions.** Open [the CORA repository](https://github.com/Luke883i/cora).
Read the [single canonical ChatGPT Project prompt](AGENT_ADOPTION.md#chatgpt-project-beta-adapter).
You may download a **source ZIP of main** as a reference and attach it to
your Project; that ZIP is a snapshot, not a Git clone and does **not** contain
original `.git` history. For Git-based execution use an authorized `git clone`
of CORA and of your target. A later `--chat-bundle` ZIP is a different,
operator-produced continuation artifact, not encrypted, signed or automatic chat memory.

**3. Set up ChatGPT Project.** In ChatGPT, create a Project for your app.
Paste the canonical text fence into **Project instructions**. Attach the CORA
source ZIP if useful; connect GitHub with scoped read permission to both
repositories. Pro or Edu can be an advanced-workflow recommendation, **not**
a universal minimum for Projects or proof of connector, runner or write access.
A separate permitted coding tool and real execution environment are required
for commits and test evidence; ChatGPT instructions do not transfer themselves
to an unrelated coding agent.

**4. Express the outcome before writing code.** Example: "Build an issue
webapp: a reporter submits an item; a reviewer sees the persisted item, may
close it, and an unauthorized user cannot close it." Translate this A0
outcome into observable acceptance tests, including reload/persistence,
authorization, data integrity, failure and rollback. This is **backward
requirements decomposition** (requirements traceability and verification/
validation): derive a noncompensatory AND graph from the desired result to
necessary source, unit, integration, HTTP/browser and independently reviewed
evidence. `UNKNOWN` or `NOT_RUN` does not satisfy a necessary condition.

**5. Develop in reversible vertical slices.** On an explicitly authorized
target branch, have a separate coding agent implement one testable workflow
(e.g. create issue -> persist SQLite -> GET returns same record) with positive
and negative oracles. Record the BASE and actual HEAD before/after; materialize
a Git blob, tree, commit and PR, then read them back. Falsify the change:
duplicate submissions, invalid input, unauthorized closure and failed
persistence must not be silently treated as PASS. Use target-native tests and
real browser checks where relevant. Run CORA on the **same committed SHA**
and inspect its receipt, counters and unclosed obligations. Each new commit
invalidates the preceding SHA-bound candidate proof.

**6. Execute and replay the single CORA dossier.** From a trusted checkout
with Python 3.11+, Git and an installed CORA CLI, run the One-Run and
`verify-process` commands below. The comprehensive route automatically
records the **safe H-FORGE source stage** when its original-Git profile is
present and replays the original safe One-Run source. The 77 native comparison
cases and any target tests or effects are **not** run without distinct consent.
On other targets without the canonical H-FORGE profile, applicability and
missing prerequisites are reported; the default is not a product certificate.

**7. Close the roadmap deliberately.** For each iteration report what was
observed, what was falsified, what survived, evidence provenance, rollback,
and the first unresolved AND prerequisite. Use the opt-in
[chat-bundle continuation](#in-a-chatgpt-session-the-shortest-reproducible-path)
to carry numbered status and next steps. Do not preassign a final number of
iterations or treat a passing source CI as permission to merge or release.

**Public source examples (bounded):** [CORA #52](https://github.com/Luke883i/cora/pull/52)
documents native Teddy Node and ICTC HTTP/SQLite pilots;
[ICTC #274](https://github.com/Luke883i/ictc/pull/274) contains a
source-only intake-to-proof contract and [ICTC #275](https://github.com/Luke883i/ictc/pull/275)
adds owner/route hardening. These commits illustrate distinct types of
engineering evidence; they do not demonstrate that CORA autonomously wrote,
ran or approved a complete third-party webapp.



### Manage the temporary ZIP in ChatGPT Project

The **source ZIP** from GitHub `main` is an optional static reference for
reading CORA's method; it does not include Git history. The **temporary
`--chat-bundle` ZIP** is a different file: a real local CORA execution writes
numbered iteration records and a matching source receipt. Upload the *latest
verified copy* to a **chat inside your ChatGPT Project**; do not treat it as
automatic Project memory, a password-protected archive or an independent
approval. Keep its working copy outside the repository.

For round 1, copy `examples/chat-step.example.json` to
`/tmp/chat-step.json`, fill the actual `session_id`, `iteration: 1`,
observed actions, DoD nodes, falsifiers, open gaps and next step. Execute the
handoff commands [below](#in-a-chatgpt-session-the-shortest-reproducible-path)
from the authorized checkout; `verify-process --one-run --chat-bundle`
must accept the result before upload. Name the attached bundle's repository,
HEAD, session and iteration in the chat. Ask ChatGPT to read
`iterations/000001/handoff.md`, `dod.json`, and
`source-receipt.json`, and to propose the next falsifiable slice rather than
declare unfinished requirements PASS.

For round 2, **do not start a fresh unrelated ZIP**: keep the local
`/tmp/cora-session.zip`, set `iteration: 2` with the same session ID,
record the new exact SHA if it changed, append with the real CLI, and replay
again. Upload the new ZIP copy, identify it as the current iteration, and
avoid retaining multiple unlabelled stale attachments as competing current
truth. A missing runner means `NOT_RUN`; no file attachment can create a
Git execution or authenticate an external reviewer. Review secrets and
sharing permissions before transfer.

## One path to a reviewable conclusion

```sh
python -m pip install -e .
cora process-run . --revision HEAD --process full --one-run --profile comprehensive \
  --output /tmp/cora-run.json --atlas-html /tmp/cora-run.html
cora verify-process /tmp/cora-run.json --repo . --one-run \
  --atlas-html /tmp/cora-run.html
```

Open `/tmp/cora-run.html` and use **Review in three questions** before exploring
the existing activity inventory, gaps, tests and evidence manifest. The first
command produces a bounded dossier; the second replays it against original
Git. An exit status indicating unresolved source debt must not be reinterpreted
as a product failure or a PASS. The HTML and JSON express the same evidence
boundary; matching them does **not** authenticate an operator or certify runtime
behavior.

The safe default executes only eligible source methods. **71 declared commands
are not 71 executed commands.** Target tests are not executed implicitly.
Local CORA self-tests require explicit exact-commit consent and remain locally
reported observations. The optional `--model-stress-cases 100000` uses the
**existing** deterministic finite source model, not 100,000 physical Git
mutations or human reviews.

**Multi-commit review:** choose the intended Git ancestor BASE, then run `cora process-run . --revision HEAD --change-base BASE_SHA --one-run --profile comprehensive --output /tmp/cora-range.json --atlas-html /tmp/cora-range.html` and `cora verify-process /tmp/cora-range.json --repo . --one-run --atlas-html /tmp/cora-range.html`. Without BASE, obligations cover one commit, not necessarily the entire PR. The caller's BASE is not host-authenticated, and source inspection does not execute target tests.

## What to check before accepting any claim

1. **Conclusion:** What is actually observed, reused, blocked or not run?
   A `PASS_SCOPED` is bounded; `BLOCKED` and `DEBT_BLOCKED` mean evidence
   or necessary context is missing; `REFUTED` requires a counterexample.
2. **Evidence:** Find the pinned commit, relevant activity, source paths and
   retained artifact. A digest establishes a scoped byte relationship,
   not human approval or universal correctness.
3. **Challenge:** Separate technical gaps from optional external assurance.
   `BLOCKED_EXTERNAL` applies to **L3 external assurance**, not L1 source
   checks or L2 experimental use; no source result grants release.

For a particular PR, select its actual `BASE` and `HEAD` commits. To compare
**declared obligation occurrences** (not verified closures), use the existing
engineering-debt tool and the separate native-Git implementation:

```sh
python tools/verify_engineering_closure.py --repo . --closure-base BASE_SHA \
  --revision HEAD_SHA --output /tmp/cora-closure.json
python tools/independent_git_oracle.py --repo . \
  --closure-report /tmp/cora-closure.json --output /tmp/cora-native-check.json
```

This optional deeper comparison is not required to **read** the One-Run dossier.
The second comparator is implementation-independent, not a different human
reviewer. A removed or renamed DoD node is not a completed requirement;
equivalent wording is only a candidate for human reconciliation.


## In a ChatGPT session: the shortest reproducible path

**New to Projects?** Start with the [canonical CORA Project beta adapter and paste-ready prompt](AGENT_ADOPTION.md#chatgpt-project-beta-adapter): this recipe assumes Plus or Edu and authorized GitHub reading, but connector capabilities vary. **Read-only** access cannot push; editing or PR creation needs a separately authorized write-capable tool or write action, and source or target tests need a real runner. Do not infer permissions or execution from a subscription or connection.

A **conversation is not a CORA runtime**. A chat can draft a plan or read a ZIP, but a source observation only exists after the Python CLI runs against a repository the operator may access.

- **Chat-only / METHOD_ONLY:** connecting GitHub in read mode permits planning, evidence questions and a proposed DoD; no local checkout, write permission, installation or fictitious runtime execution is needed. Use the [Project walkthrough](../README.md#use-cora-in-a-chatgpt-project--beginner-walkthrough).
- **Engine / actual tests:** use a real, authorized local checkout of CORA and a target repository plus a Python runner. GitHub read permission alone is insufficient. Keep outputs outside the repository; no credentials, private chat transcripts or private source files belong in the portable ZIP by default.
- Copy `examples/chat-step.example.json` to `/tmp/chat-step.json`; edit `session_id`, `intent`, `actions`, `falsifiers`, `roadmap`, `dod` and `gaps`. The sample is intentionally blocked pending an independent runtime/reviewer oracle.
- From a shell with CORA-ENGINE installed, run against the **actual target checkout** (use `.` only if intentionally auditing CORA itself). This is a source dossier, not target-native test execution:

```sh
cora process-run /path/to/target --revision TARGET_HEAD --one-run --profile comprehensive \
  --output /tmp/round.json --atlas-html /tmp/round.html \
  --chat-step /tmp/chat-step.json --chat-bundle /tmp/cora-session.zip
cora verify-process /tmp/round.json --repo /path/to/target --one-run \
  --atlas-html /tmp/round.html --chat-bundle /tmp/cora-session.zip
```

Open `/tmp/round.html` for review, then attach `/tmp/cora-session.zip` to your next ChatGPT turn. Request a reading of the **latest** `iterations/000001/handoff.md` (or the highest six-digit iteration), the DoD and the missing evidence. For round 2 set `iteration: 2` in a new input JSON and run again with the *same* ZIP. The command rejects skipped, repeated or different-session rounds; prior records remain logically intact. The ZIP can be moved to another machine and verified there, but independent Git replay needs the original authorized checkout and exact revision.

**Status vocabulary:** `DONE_REPORTED` is a user's statement, not an executed test; `PASS_REPORTED` is not a certified pass; external DoD obligations cannot be self-promoted; `BLOCKED_EXTERNAL` is an honest open qualification gate. The SHA-256 chain detects inconsistent archive entries but is not a signature. There is no automatic chat capture or hosted service; each iteration requires a deliberate CORA execution or a human-assisted invocation.

## Where to go next

For a scoped architectural investigation use `cora graph` and
`cora artifact-audit`; for exact syntax see [CLI reference](CLI_REFERENCE.md).
For external adoption see [Agent adoption](AGENT_ADOPTION.md). The
[architecture](ARCHITECTURE.md) explains source, software and product boundaries;
[Release](RELEASE.md) describes the separately required independent reviewer,
maintained-target study, host controls, reproducible distribution and rollback.
**No newcomer usability success or independent release authorization is
claimed solely because this guide exists.**
