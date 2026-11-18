# Scientific editorial evidence and reproduction

**Reader artifact:** [From Intent to Evidence](From_Intent_to_Evidence.docx); SHA-256 `988b8df4d4e90b172c17d5fe199b3818360d32a883b7320ff1c80135cb7cabf0`, Git blob `77fc302848772c4d34b8c0b60df932f1f9703f48`. **Reproduction and falsification:** [source archive](Scientific_Editorial_Source_And_Audit.zip); Git blob `8ca28df0d902f83704d62916404cb2efdf7c4743`.

The paper is a reader-independent research artifact. Editorial development, mutation logs, exact Git proof and DoD remain outside it in this directory. The Word uses conventional requirements engineering, scientific modeling, test selection and provenance terminology before introducing local ROA/AOSP/CORA terms.

## Original evidence vs interpretation

Six engineering repositories (ICTC, Teddy, LUMEN, NILO, iKant_EDU and CORA) contribute 20 original historic commit/file links and three newer exact commit/file Git OID pairs each (138 references total). The 18 increments were checked against the original commit-detail file lists; historical Git references locate source, not successful runtime execution or authorship by AI. The ROA bryophyte case is a computable 20-level/42-variable simulation with a proposed blinded expert experiment; empirical indistinguishability is NOT proven.

The four architectural figures have alternative descriptions. The local manuscript was rendered to 14 A4 pages, inspected, and an automated Word accessibility check reported zero findings. These are author-scoped checks, not independent visual/accessibility certification.

## Reproduce from source

Unzip the archive in a disposable working directory. Under Python 3.11+ with `python-docx==1.2.0` (and its `lxml` dependency):

```sh
python polish_paper.py
python audit_paper.py
sha256sum From_Intent_to_Evidence.docx
```

The expected Word SHA-256 is `988b8df4d4e90b172c17d5fe199b3818360d32a883b7320ff1c80135cb7cabf0`. The audit changes 138 original Git hyperlink targets, 20 scientific-claim anchors and four figure descriptions (162 distinct physical DOCX copies); it rejects all 162 and permits 10 creator-metadata-only controls. Those are **author-defined document integrity oracles**, not original-app security exploits, performance tests or user studies.

Historical context remains reproducible from original CORA commit `c331ea2ecad080083f61f221f4991b4030a74b8c` and the pre-existing `Research_Source_And_Verification.zip` archive. This PR does not rewrite the earlier Word blob in that historical commit.

**Publication gate:** author-scoped documentary assurance only. Independent domain reviewer, empirical validation, native target executions, capacity/security audits, causal comparison and authorized publication remain outside the Word and open as noncompensatory nodes in `Scientific_Editorial_DoD.json`.
