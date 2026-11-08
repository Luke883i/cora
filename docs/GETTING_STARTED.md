# Getting started with CORA

CORA is a local, read-only-by-default **source assurance** framework, not an autonomous
coding agent, a sandbox attestation, a merge approver or a product certificate.
Start from an authorized checkout with Python 3.11+ and Git. Use an output
directory outside the repository (`/tmp` below is a Unix example).

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

## What to check before accepting any claim

1. **Conclusion:** What is actually observed, reused, blocked or not run?
   A `PASS_SCOPED` is bounded; `BLOCKED` and `DEBT_BLOCKED` mean evidence
   or necessary context is missing; `REFUTED` requires a counterexample.
2. **Evidence:** Find the pinned commit, relevant activity, source paths and
   retained artifact. A digest establishes a scoped byte relationship,
   not human approval or universal correctness.
3. **Challenge:** Inspect the unresolved gaps and external qualification.
   `BLOCKED_EXTERNAL` means independent operator, target, isolation, host
   or user evidence remains unavailable; no source result grants release.

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

A **conversation is not a CORA runtime**. A chat can draft a plan or read a ZIP, but a source observation only exists after the Python CLI runs against a repository the operator may access.

- Start with a local checkout of CORA and a target repository you are authorized to inspect. Keep outputs outside the repository. No credentials, entire private chat transcripts, or private source files belong in the portable ZIP by default.
- Copy `examples/chat-step.example.json` to `/tmp/chat-step.json`; edit `session_id`, `intent`, `actions`, `falsifiers`, `roadmap`, `dod` and `gaps`. The sample is intentionally blocked pending an independent runtime/reviewer oracle.
- From CORA's checkout, run:

```sh
cora process-run . --revision HEAD --one-run --profile comprehensive \
  --output /tmp/round.json --atlas-html /tmp/round.html \
  --chat-step /tmp/chat-step.json --chat-bundle /tmp/cora-session.zip
cora verify-process /tmp/round.json --repo . --one-run \
  --atlas-html /tmp/round.html --chat-bundle /tmp/cora-session.zip
```

Open `/tmp/round.html` for review, then attach `/tmp/cora-session.zip` to your next ChatGPT turn. Request a reading of the **latest** `rounds/NNNNNN/handoff.md`, the DoD and the missing evidence. For round 2 set `iteration: 2` in a new input JSON and run again with the *same* ZIP. The command rejects skipped, repeated or different-session rounds; prior records remain logically intact. The ZIP can be moved to another machine and verified there, but independent Git replay needs the original authorized checkout and exact revision.

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
