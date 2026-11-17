**A PRACTICAL FIELD GUIDE**

# Build with AI. Verify before you trust.

From an idea to accountable software decisions, illustrated by seven public Git histories.

AI can produce a convincing patch faster than a team can assess its consequences. A better process begins with what a person needs to achieve, works backward to what must be true, changes one coherent part of the system, tests possible failure, and records who can accept the result. Neither clean code nor a green test alone is a release decision.

**The central rule**

**A claim is as strong as the observation that supports it—not as strong as the language used to describe it.**

### A repeatable engineering loop

**Define the result.** Describe the user action and every condition required for success.

**Change the software.** Implement a reversible change and identify the exact source revision.

**Challenge the change.** Run appropriate application tests and try realistic failure cases.

**Decide and learn.** Record what passed, what failed, what remains unknown and who approves the next step.

### Where the examples come from

The cases draw on 149 selected, source-identified records across ICTC, Teddy, LUMEN, NILO, iKant_EDU, CORA and the academics programme registry. The linked examples below point to specific file versions. They show recorded engineering changes, not 149 independently repeated product tests.

*Reading guide: start with the method, examine a project case close to your own work, and use the closing decision questions before accepting a change.*

## Start with the result a person must achieve

Consider a web application for reporting a problem. Someone submits a report, finds it again after the server restarts, and cannot close another person’s report. A pleasant screen is not enough: the result also requires durable storage, correct permissions, reliable retrieval and recovery.

### Work backward from success

| Required condition | A test that could disprove it |
| --- | --- |
| Report is saved | Restart the server, then retrieve the same record. |
| Only authorized people can change it | Try to close another person’s report; the action must fail. |
| The interface reflects actual data | Reload the page and compare it with persisted records. |
| Failure can be diagnosed | Introduce a controlled error and inspect the recorded cause. |
| The change can be reversed | Restore the previous version and confirm no data are lost. |

**All mandatory conditions must hold. A hundred successful interface tests cannot compensate for one failed authorization test.**

### Change the roadmap when evidence changes

For each proposed change, record the previous accepted revision, the intended user result, affected components, positive and negative tests, a recovery plan and a reviewer. Once tests reveal a new dependency or a surviving defect, revise the sequence of work. A plan is a hypothesis, not permission to ignore a failure.

## Know what the evidence can actually establish

Source code, test scripts, screenshots and decisions answer different questions. Keep their claims separate.

| Evidence | What it can—and cannot—show |
| --- | --- |
| Git revision | Identifies tracked source bytes and history; not a running product. |
| Test result | Records behavior within a named run and environment; not every situation. |
| Screenshot | Shows pixels at one instant; not the root cause of an error. |
| Dependency inventory | Lists known components; does not exclude unknown security flaws. |
| Signed build evidence | Can verify a trusted build origin; not feature correctness. |
| Human review | Records a decision by an accountable person; not infallibility. |

### Make the test capable of detecting a real mistake

An AI assistant may write the change, the tests and a confident explanation. That can create self-confirming evidence. Define the expected result separately, include a test that should fail for a deliberately broken version, and preserve failures that remain undetected. A simulated fault tests the checker; it does not mean that the live application was broken.

### Simplify without losing responsibilities

Before moving or deleting code, trace known readers and writers, dynamically loaded modules, file paths, build rules, stored records and recovery procedures. Compare the old and new behavior. Unknown consumers are unresolved work, not evidence that deletion is safe. Fewer files or lines may reduce maintenance cost; they do not, by themselves, establish functional equivalence.

## What seven projects have in common

**Visible failures.** Tests should expose the specific operation that failed, instead of turning an error into a reassuring summary.

**Correct state over time.** A snapshot may look right while a restart, page update or later step reveals a defect.

**Independent expected results.** The checks must be able to reject plausible but wrong output.

**Source identity.** A result belongs to a precise revision and cannot be silently transferred to another.

**Preserved control.** Changes to roles, access or project membership must not accidentally grant authority.

**Human decision.** A reviewer accepts known residual risk; the coding assistant cannot approve itself.

The histories provide comparable examples of source changes, not comparable measures of engineering productivity. A repaired web cache, a game level and a corrected registry link differ in difficulty and intended outcome.

## ICTC

*Compliance knowledge and procedural workflows*

**What happened.** A modal inspector obscured controls. Subsequent corrections moved its context into the normal page flow, and browser checks were added to distinguish an unfinished interaction from missing or wrong metadata.

**What would make the conclusion stronger.** Examine the user’s role, the visible requirement, the persisted record after a restart and the exact browser failure. The source examples do not independently certify legal compliance or production behavior.

**Original source changes:** [Wait for the browser interaction to finish before inspecting the panel](https://github.com/Luke883i/ictc/blob/5ea589a37943697daf29d8b16e27ff1207f47955/tests/browser/browser-convergent-kernel.py)  ·  [Report the exact browser failure instead of hiding the failed check](https://github.com/Luke883i/ictc/blob/8686b01c88fa41656526400f315ddd90d64678b2/.github/workflows/convergent-kernel-dod.yml)  ·  [Repeat metadata checks after the page updates](https://github.com/Luke883i/ictc/blob/2c0a8a0f4c1bd98f9a3d5141b20f68cff773fb6e/tests/browser/browser-convergent-kernel.py)  ·  [Check the meaning of the maturity indicator on every display path](https://github.com/Luke883i/ictc/blob/72ca530d7b3df6283f4264d9173dd8c388d9dbaa/tests/verification/ux-r8-adoption-check.mjs)  ·  [Track how seven procedures produce metrics across users and revisions](https://github.com/Luke883i/ictc/blob/f35656c1b0ea5aeca7d8ae2e7a150608d6a2053e/tests/verification/ux-r8-metric-provenance-check.mjs)  ·  [Distinguish missing metadata from a wrong explanation](https://github.com/Luke883i/ictc/blob/f0e5fe7dec600bbc2028a71db5a7b062955f71a5/tests/browser/browser-convergent-kernel.py)

## Teddy

*Local conversation and animated character*

**What happened.** Character movement, the shape of animated surfaces, conversation memory and browser request security produced different failure modes. The history adds movement checks, preserves conversation chronology and separates genuine service responses from simulated ones.

**What would make the conclusion stronger.** Reproduce a gesture in an actual browser, check request identity and establish which model or service answered. An anatomical test cannot establish charm, empathy or reliable external service availability.

**Original source changes:** [Update the motion evidence when movement rules change](https://github.com/Luke883i/teddy/blob/da66653f4affa15384b58d7174ff545486619392/docs/motion-v8-mutation-report.json)  ·  [Compare newer gesture tests with previously defined movement limits](https://github.com/Luke883i/teddy/blob/ff04b6fe1c346a604db2fb0a3ddfcecfea984453/docs/MOTION_V45_LEGACY_MUTATOR_RECONCILIATION.md)  ·  [Test whether animated surfaces move consistently with the body](https://github.com/Luke883i/teddy/blob/230f13d16739d693a5ccdf5e1207c935ca64ea87/tests/motion-physical-pelt-v45.test.mjs)  ·  [Keep real service responses separate from simulated ones](https://github.com/Luke883i/teddy/blob/62af0c6d62bfaacc6afdd62eaae0678c68f03a20/tools/prove-real-text-v20.mjs)  ·  [Retain recent conversation context without scrambling its order](https://github.com/Luke883i/teddy/blob/ba9cf5e7330a834551fcd502c08a0326b1160349/server/lib/local-engines.mjs)  ·  [Keep browser graphics failures visible and clean up test sessions](https://github.com/Luke883i/teddy/blob/767e844ddba865a3bc1dab1d98182c76a10d326a/.github/workflows/motion-v8.yml)

## LUMEN

*Library services and offline web application*

**What happened.** A cache write may fail after the network has already delivered fresh content. The original work tests update behavior under storage constraints, protects a user’s unfinished form and strengthens startup and storage-path checks.

**What would make the conclusion stronger.** Verify fresh online content, offline fallback, safe updates and real process restart. Public code does not establish live institutional catalogue integration, device-wide reliability or operational recovery.

**Original source changes:** [Check that the public programme record names the right owner](https://github.com/Luke883i/lumen/blob/785eb028cb53c113175d8de25f12ee7c7b300992/test/roa-membership.test.mjs)  ·  [Reject invalid claims about participation in the programme](https://github.com/Luke883i/lumen/blob/f730cefa70e7054f05a6c64581cb311a137f3092/test/roa-membership.test.mjs)  ·  [Test cache failures and network responses across 80 modeled states](https://github.com/Luke883i/lumen/blob/1b9cea75d4cc8d84a37779b8b0b53ca1078ef438/test/pwa-cache-coherence.test.mjs)  ·  [Offer a clear update action without losing what the reader typed](https://github.com/Luke883i/lumen/blob/d37b8e4f573aa39d8decfae5e8b473f00eed7a47/browser/tests/experience.spec.mjs)  ·  [Reject unsafe characters in data-storage paths](https://github.com/Luke883i/lumen/blob/dbcd21fcd29494da7a73c1c860cd3f9625b8d0d9/src/deployment-contract.mjs)  ·  [Check database settings when the server starts](https://github.com/Luke883i/lumen/blob/591beb0a74444f23747d3b2f60344fe084929705/src/deployment-contract.mjs)

## NILO

*Narrative platform game*

**What happened.** Adding a third level changed legitimate expectations in older tests. The history preserves graphics fault checks, verifies the actual game-state rules and separates deployment constraints from player acceptance.

**What would make the conclusion stronger.** Replay movement, boss states, saved checkpoints and the delivered build in a real browser. Deterministic gameplay checks do not prove enjoyment, artistic quality or commercial completeness.

**Original source changes:** [Update an older browser expectation after adding a new level](https://github.com/Luke883i/NILO/blob/fbdf5549c05450d0b3d93e77b46d6ed84c54d742/tests/browser-e2e.py)  ·  [Keep graphics fault checks valid as the game expands](https://github.com/Luke883i/NILO/blob/b31bce89812e85b6d2841fe8eca0854af7a2f1d7/tests/art-mutation.test.mjs)  ·  [Preserve earlier physical fault checks for the new game state](https://github.com/Luke883i/NILO/blob/8e643e76d3b197fb1e91ab1ded1e7faf83fa11d2/tests/contracts.test.mjs)  ·  [Separate essential release conditions from external acceptance](https://github.com/Luke883i/NILO/blob/054d81fca36ceefcfb02753c8ff5a538ce7045c1/contracts/dod-v1.json)  ·  [Test eight deliberately broken delivery configurations](https://github.com/Luke883i/NILO/blob/b450352b2d83c0e6e09f9a7b52526ee22cabde79/tests/delivery-mutation.test.mjs)  ·  [Align the defeat state and real keys with the game rules](https://github.com/Luke883i/NILO/blob/0303002a9f4dec3d288fd0c16927b314f211e380/contracts/nilo-semantic-v1.json)

## iKant_EDU

*Experimental controller for language-model interactions*

**What happened.** Restructuring the repository moved files, changed server paths and invalidated generated evidence. Fixes rebound exact source identities and prevented a test workflow from rewriting the proposed source revision.

**What would make the conclusion stronger.** Identify active and indirect consumers, retest the original entrypoints and verify the actual host interaction. A smaller directory tree or green local check cannot prove successful admission into an external host.

**Original source changes:** [Show the exact interface failure without removing the quality gate](https://github.com/Luke883i/iKant_EDU/blob/cf454bb84361e9ab5cafd5023a9f8299bb7b9ecf/.github/workflows/mcp-standalone-assurance.yml)  ·  [Detect stale evidence after moving files and changing paths](https://github.com/Luke883i/iKant_EDU/blob/cd3632f3504711332882d1025a3f355680e25012/scripts/v5b-repository-governance-audit.mjs)  ·  [Rebuild evidence identities for the relocated source files](https://github.com/Luke883i/iKant_EDU/blob/a44a8a4e0712da1949c678c9493a1c7819fc18e3/tests/artifacts/qualification/c51-candidate-blob-manifest.json)  ·  [Prevent test automation from rewriting the proposed code revision](https://github.com/Luke883i/iKant_EDU/blob/fdedc5f8aefae4a78aa4c450abcc73d5841f0d7a/.github/workflows/c53-physical-closure-hardening.yml)  ·  [Declare allowed changes and reject unrelated byte differences](https://github.com/Luke883i/iKant_EDU/blob/93d12cf5b87c343cde60d28a702ffc530cb8c150/contracts/r7-pr249-founding-contract.json)  ·  [Use the exact proposed source revision in project-session checks](https://github.com/Luke883i/iKant_EDU/blob/71bbc9ef5bf50de357eeb7a6b625fe4a09c319a9/.github/workflows/project-session-repo-first.yml)

## CORA

*Local engineering-assurance method and software*

**What happened.** An editorial checker initially missed a false claim because the expected words were still present. The source history records stronger negative tests, explicit evidence roles and a research comparison that did not demonstrate a differential advantage.

**What would make the conclusion stronger.** Check that the expected result is independent of the proposed code, the evidence matches the exact revision and open gaps remain visible. The measured comparison on selected examples does not establish superiority to a strong checklist.

**Original source changes:** [Specify expected results separately from the software being examined](https://github.com/Luke883i/cora/blob/050ad69f57022343c135beb93b7ab90baef4bae3/research/decision-ready-assurance/aosp-r2/ORACLE_SPEC.json)  ·  [Connect visual failure hypotheses to their source records](https://github.com/Luke883i/cora/blob/3ba2d31700008734e05b9eee5a48edf709c3c78b/research/decision-ready-assurance/aosp-r3/EVIDENCE_PINS_R3.json)  ·  [Publish an editable guide with evidence-based diagrams](https://github.com/Luke883i/cora/blob/a6519d08da7a0b35e76056a2388bfde1e0d154ee/research/decision-ready-assurance/aosp-r2/ENGLISH_FIELD_GUIDE_R2.docx)  ·  [Require all fifteen stated editorial conditions to hold](https://github.com/Luke883i/cora/blob/dd0d7ea00b2ef9f6b95817469c76ae21bfb5e808/research/decision-ready-assurance/aosp-r2/EDITORIAL_DOD.json)  ·  [Preserve an inconclusive comparison against a strong checklist](https://github.com/Luke883i/cora/blob/d19e54ec776ac23ba85c0f6fc2ecb26050b7936f/research/decision-ready-assurance/AOSP_R1_SCIENCE_FREEZE.markdown)  ·  [Classify research files without treating them as runtime proof](https://github.com/Luke883i/cora/blob/435701f48e6172eeaa77c9320d44c1716840db02/cora.artifact-roles.json)

## academics

*Public research programme registry*

**What happened.** Programme membership, source references and reader navigation are maintained as a public directory. The recorded changes remove obsolete entries, update source identities and repair a link and heading.

**What would make the conclusion stronger.** Check that each stated member resolves to its intended repository and original record. Shared programme membership does not mean shared runtime, one approval authority or independent peer review.

**Original source changes:** [Rebuild source records when programme membership changes](https://github.com/Luke883i/academics/blob/490155e1649ccf73b29d78ce04cb9edbdf975431/.github/workflows/regenerate-lumen-hub.yml)  ·  [Remove programme entries no longer in scope](https://github.com/Luke883i/academics/blob/23be9d4e305ba2dd5e8da738a254ee0c4977af8b/PROGRAMME.json)  ·  [Repair a broken link in the public research directory](https://github.com/Luke883i/academics/blob/ff12a99984e7c76a575fb6211b81feda3bafab91/README.md)  ·  [Clarify the heading that guides readers to public repositories](https://github.com/Luke883i/academics/blob/12c1526041815e5dfc5344d7200fd0ff74e61565/README.md)

## Use the evidence to make a decision

Before approving a change, ask five practical questions. Each answer should identify its evidence and any remaining uncertainty.

**What must work for the user?** List the mandatory outcomes, including access and recovery.

**What was actually run?** Record the source revision, command, environment, result and surviving failures.

**What might still be affected?** Name unknown consumers, side effects, external services and rollback risks.

**Which protections are effective?** Check permissions, reviewer independence, sensitive data and release controls—not merely their configuration files.

**Who makes the decision?** Identify the accountable reviewer and the conditions for revisiting acceptance.

### Does a structured method add value beyond a strong checklist?

That is an open experimental question. A fair comparison would give equivalent tasks and information to three groups: a capable AI coding assistant with a strong persistent checklist; the same assistant following the structured method; and the same assistant using both the method and its local checking software. Independent reviewers should compare serious errors missed, human work, rework, recovery readiness and cost—not how persuasive the reports look.

One published, author-selected comparison found identical results for the structured decision rule and an informed checklist on sixteen test cases. This is a useful null result, not a general finding of equivalence or a causal advantage.

### Scope of this field guide

The 149 selected historical references identify source files and commits across seven public repositories. The forty links in the project sections open additional exact-source examples. The material was not used here to rerun all seven products, authenticate an independent reviewer, conduct usability trials or measure development-time savings. Source history can explain the sequence of corrections; it cannot alone show that a method caused faster or better engineering.

**Takeaway: use AI to propose and implement; use independently meaningful observations to challenge; keep approval with accountable people.**
