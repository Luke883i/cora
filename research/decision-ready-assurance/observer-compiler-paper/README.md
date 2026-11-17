# From Intent to Evidence — engineering research edition

**Reader artifact:** [From_Intent_to_Evidence.docx](From_Intent_to_Evidence.docx) (13 pages, exact Git blob `5ead919a008d6a08eb11fb774854f53cedab5037`; SHA-256 `75a5cfd30a3281877d21e0278aa9f5853eab9beb3639d1b83b85a1bdd5c68ef2`).

**Reproducibility:** [Research_Source_And_Verification.zip](Research_Source_And_Verification.zip) (Git blob `8a70abca67c4b5652d40d26d35a9601d18184431`; SHA-256 `9cab798be75852c74411efb22256328f28ab4013ffca1b129f828ab33353f8d8`).

This research paper examines whether a **non-specialist operator** can direct materially correct software development with a capable coding agent, a persistent Project prompt and source ZIP, while reserving expert acceptance. The model is a hypothesis, not an experimentally demonstrated reduction in expert labor. The distinction between **product / software / repository** is preserved throughout.

## Scientific and engineering boundaries

The [ROA Annex B](https://github.com/Luke883i/ROA/blob/519a85bb15e8a964ce2f4d2cb6fdba44ab2382e7/Operation/corpus/text/annex-b-rla-biological-case-bryophyte.md) defines a generalist bryophyte reticulum with 20 abstraction levels and 42 parameters. [Its executable laboratory](https://github.com/Luke883i/ROA/blob/b0dcda8bef8b6e34455d86907db56f29ead1c521/Reticular%20Local%20Abstraction%20RLA-CRC-ECNN/ROA%20Bryophyte%20Epistemic%20Lab/ROA_Bryophyte_Epistemic_Lab_v9.html) is pinned by original commit `b0dcda8bef8b6e34455d86907db56f29ead1c521`, Git file object `7711cf274127af04912b11162ce0d2cbb85df1ea`. The hypothesis of blind expert real-versus-synthetic indistinguishability has **not** been empirically established.

Comparing this botanical example with CORA is an analogy **of bounded observer construction and explicit epistemic debt**, not equivalence between scientific biological prediction and software assurance. ROA is a proposed theoretical framework. AOSP (Augmented Ontological-Semantic Platforms) is an ecosystem, not one individual application. No formal derivation or priority/novelty claims over established research follow automatically from this corpus.

## Reproduce on an authorized checkout

```sh
unzip -oq Research_Source_And_Verification.zip -d /tmp/observer-paper
python -m pip install 'python-docx==1.2.0' 'Pillow==12.3.0'
cd /tmp/observer-paper
python build_paper.py
python science_and_falsification.py
python audit_paper.py
sha256sum From_Intent_to_Evidence.docx
```

The build requires DejaVu Sans TrueType fonts at `/usr/share/fonts/truetype/dejavu`. The manuscript is compiled into a deterministic ZIP-packaged Word document with four editable-positioned raster diagrams, 120 selected original Git source links from six repositories, and additional scientific/standards links. The auditor enforces 147 finite source/Word negative oracles and ten harmless metadata controls. The scientific model runner constructs 10,000 deterministic, structurally edited JSON contract variants and checks their typed invariants. **No target product native runtime, domain expert assessment, field capacity benchmark, independent security audit or human effectiveness study is represented by these local tests.**

`Gold_Git_Witnesses_120.json` preserves 20 selected commit/file references per repository (five for each of four inquiry lenses) and classifies 80 adjacent examples as research questions rather than direct test evidence. The extracted archive contains `Scientific_Challenge_Nodes_100.json`, 1,000 unexecuted adversarial review questions, and the executable verifiers. The 10,000-case JSON mutation manifest is regenerated with seed `13072026` (not pre-promoted into independent proof).

**Review gate:** reproduce exact document SHA, run the author-scoped falsifiers, inspect the 13-page render and obtain a reviewer independent of the author before any publication-grade claim. GitHub check success is not evidence of real expert authorization or institution-wide compliance.