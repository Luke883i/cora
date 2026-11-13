"""Documentation source contract: inventory, reachability, roles, CLI and DoD.

Static reports are NOT independent acceptance, host authority or user comprehension.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import posixpath
import re
from pathlib import Path
from urllib.parse import unquote

BASELINE_SHA = "ee6da7625dae1e4101e06eb979a348610f39093b"
BASELINE_MD = 43
EXPECTED_MD = 48
EXTERNAL = {"E01", "E02", "E03"}
SOURCE = {f"S{i:02d}" for i in range(1, 19)}
CUTS = {
    "I_VALUE": ["S01", "S02", "S03", "S06"],
    "I_ACCESS": ["S04", "S05", "S07", "S08", "S18"],
    "I_CONSISTENCY": ["S09", "S10", "S12", "S16", "S17"],
    "I_OPERATION": ["S11", "S13", "S14"],
    "I_EVIDENCE": ["S15"],
    "G_DOC_SOURCE": ["I_VALUE", "I_ACCESS", "I_CONSISTENCY", "I_OPERATION", "I_EVIDENCE"],
    "G_DOC_ACCEPTED": ["G_DOC_SOURCE", "E01", "E02", "E03"],
}
KNOWN_HISTORICAL = {
    "docs/DOD.md", "docs/archive/dod/DOD_PR17_AGENT.md",
    "docs/archive/dod/DOD_PR16_SEMANTIC_ASSURANCE.md",
    "docs/STANDARDS_MAINTENANCE_AUDIT.md",
    "docs/archive/audits/FORENSIC_SELF_AUDIT.md",
}
LINK = re.compile(r"(?<!!)\[[^\]]+\]\((<[^>]+>|[^)\s]+)")
CODE_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
COMMAND = re.compile(r"^- `([a-z][a-z0-9-]+)` —", re.M)
STATUS = {"CURRENT", "SCOPED_CURRENT", "HISTORICAL"}
KINDS = {"LANDING", "INDEX", "ADR", "AUDIT", "DOD", "CHANGELOG",
         "GOVERNANCE", "ARCHITECTURE", "REFERENCE", "METHOD"}
VALID_GROUP = {"00", "01", "02", "03", "04", "05", "06", "07"}


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def markdown_links(content: str) -> list[str]:
    output, inside, marker = [], False, ""
    for line in content.splitlines():
        m = CODE_FENCE.match(line)
        if m:
            kind = m.group(1)[0]
            if not inside:
                inside, marker = True, kind
            elif kind == marker:
                inside, marker = False, ""
            continue
        if not inside:
            output.extend(m.group(1).strip("<>") for m in LINK.finditer(line))
    return output


def resolve(base: str, href: str) -> tuple[str, str] | None:
    if href.startswith(("#", "https://", "http://", "mailto:", "tel:")):
        return None
    raw, _, anchor = unquote(href).partition("#")
    if not raw or "://" in raw or raw.startswith("/") or "\\" in raw:
        return None
    target = posixpath.normpath(posixpath.join(posixpath.dirname(base), raw))
    if target.startswith("../") or target in (".", ".."):
        return None
    return target, anchor


def heading_slugs(text: str) -> set[str]:
    slugs, counts = set(), {}
    for line in text.splitlines():
        m = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not m:
            continue
        slug = re.sub(r"[^\w\- ]", "", m.group(1).lower()).strip().replace(" ", "-")
        n = counts.get(slug, 0)
        counts[slug] = n + 1
        slugs.add(slug + (f"-{n}" if n else ""))
    # A historical deep link may survive as a bounded, explicit HTML anchor
    # without forcing the visible current heading to report PR chronology.
    for m in re.finditer(r'(?m)^<a id="([a-z0-9][a-z0-9-]{1,120})"></a>$', text):
        slugs.add(m.group(1))
    return slugs


def validate_dod(root: Path, errors: list[str]) -> None:
    try:
        d = json.loads((root / ".cora/contracts/dod/documentation-dod.json").read_text("utf-8"))
        if (d.get("schema") != "cora-documentation-dod/1" or
            d.get("baseline_markdown_count") != BASELINE_MD or
            d.get("baseline_sha") != BASELINE_SHA or
            d.get("authority") != "NONE" or
            d.get("external_status") != "BLOCKED_EXTERNAL" or
            d.get("goals") != {"source": "G_DOC_SOURCE", "accepted": "G_DOC_ACCEPTED"}):
            raise ValueError("DoD status or authority altered")
        if d.get("readme_refactor") != README_SEMANTIC_DOD:
            raise ValueError("PR42 README semantic and authority thresholds drift")
        nodes = d["nodes"]
        if not isinstance(nodes, list) or len(nodes) != 28:
            raise ValueError("expected 28 DoD nodes")
        ids = [n["id"] for n in nodes]
        if len(set(ids)) != len(ids) or set(ids) != SOURCE | EXTERNAL | set(CUTS):
            raise ValueError("DoD identities inconsistent")
        for n in nodes:
            key = n["id"]
            if key in CUTS:
                if (n["depends_on"] != CUTS[key] or
                    n["kind"] != ("GLOBAL" if key.startswith("G_") else "INTERMEDIATE") or
                    n["scope"] != ("EXTERNAL" if key == "G_DOC_ACCEPTED" else "SOURCE")):
                    raise ValueError("DoD edge/scope drift")
            elif n["depends_on"] or n["kind"] != "LOCAL" or n["scope"] != (
                "EXTERNAL" if key in EXTERNAL else "SOURCE"
            ):
                raise ValueError("DoD leaf changed")
        from cora.reticulum import ordered_cut
        if len(ordered_cut(nodes, "G_DOC_ACCEPTED")) != 28:
            raise ValueError("DoD global not connected")
    except (OSError, ValueError, TypeError, KeyError, ImportError) as exc:
        errors.append("documentation-dod-invalid:" + type(exc).__name__)


# PR42: exactly-scoped semantic editorial DoD, not an independent reader certificate.
README_SEMANTIC_DOD = json.loads(r'''{"schema":"cora-readme-semantic-refactor-dod/1","status":"SOURCE_CANDIDATE_NEEDS_EXACT_HEAD_CI","authority":"NONE","accepted":"BLOCKED_EXTERNAL","legacy_line_cap":"NON_NORMATIVE_EDITORIAL_OBSERVATION","source_gates":["S01_S18_CLAIMS_IN_SECTIONS","LIVE_GIT_PR41_AND_RELEASE_TRUTH","PROGRESSION_AND_FIRST_USE","FIVE_READER_ROUTES","FIVE_DECLARED_LENSES","ACTUAL_71_COMMAND_IDENTITY","ONE_RUN_AND_AFFECTED_STATUS","RELATIVE_LINKS_TO_TRACKED_PATHS","EXTERNAL_NONPROMOTION","SEMANTIC_POSITIVE_AND_NEGATIVE_FALSIFIERS"],"metrics":{"required_claim_leaves":18,"declared_cli_count":71,"reader_routes":5,"disclosure_lenses":5,"scenarios":10000,"seed":883,"meaning_preserving":4000,"adversarial":6000,"max_wrong_verdicts":0,"expected_rejected_negative":6000,"expected_accepted_equivalent":4000,"required_replay":true,"independent_user_trials_required":true},"external_obligations":["E01_FIRST_READ_HUMAN","E02_AGENT_ON_EXTERNAL_MAINTAINED_TARGET","E03_ENFORCED_HOST_AND_NON_AUTHOR_REVIEW"],"no_auto_publish":true,"no_auto_merge":true,"nonclaims":["NO_SEMANTIC_COMPLETENESS_PROOF","NO_INDEPENDENT_HUMAN_USABILITY_CLAIM","NO_RELEASE_AUTHORITY_FROM_README","NO_180_LINE_HARD_GATE"]}''')

README_SECTION_ORDER = (
    r"^## First five minutes\b",
    r"^## What works today\b",
    r"^## One-Run\b",
    r"^## How CORA works\b",
    r"^## Use CORA with an AI coding assistant\b",
    r"^## (?:Interpret a CORA result|Understanding CORA results)\b",
    r"^## Final Experimental Baseline\b",
    r"^## Documentation by goal\b",
    r"^## Operating boundaries\b",
    r"^## Engineering map\b",
)

README_SPECIFIC_TRUTHS = (
    "cora snapshot . --revision HEAD",
    "cora process-run . --revision HEAD --process full --one-run --profile comprehensive",
    "The default does not execute arbitrary target tests",
    "External acceptance remains `BLOCKED_EXTERNAL`",
    "15 SOURCE leaves, 7 EXTERNAL leaves, and 8 aggregate AND gates",
    "16 realistic fault families",
    "2,517 preregistered zero-to-fourway masks",
    "not one million independent source mutations",
    "Current source is this Git revision",
    "two controlled physical Git repositories",
    "GitHub workflow files alone do not prove",
    "A hash can identify committed bytes; it cannot authenticate a human reviewer",
)
README_FALSE_PROMOTIONS = (
    r"\bverified public release and stable API\b",
    r"\bCORA is an autonomous coding agent\b",
    r"\bThe default (?:automatically )?executes (?:untrusted|arbitrary) target tests\b",
    r"\bA hash alone authenticates a human reviewer\b",
    r"\bCI green is independent review\b",
    r"\bExternal acceptance has been approved\b",
    r"\bCurrent source is from an unmerged draft\b",
    r"\b\d{5,} independently executed source mutations\b",
    r"\bPASS_SCOPED certificate alone grants merge and release authority\b",
    r"\bCORA automatically approves merges\b",
)


def verify_readme_semantics(readme: str, *, root: Path | None = None) -> list[str]:
    """Finite editorial claims and navigation; not open-world language understanding.

    Formatting-equivalent edits do not fail on physical line count. The
    assertion catalog is deliberately source-only, independently falsified
    by positive/negative preseeded tests. The real newcomer study remains E01.
    """
    errors: list[str] = []
    positions = []
    for marker in README_SECTION_ORDER:
        m = re.search(marker, readme, flags=re.MULTILINE)
        if not m:
            errors.append("readme-semantic-section-missing:" + marker)
        else:
            positions.append(m.start())
    if len(positions) != len(README_SECTION_ORDER) or positions != sorted(positions):
        errors.append("readme-semantic-progression")
    if len(re.findall(r"^\x60\x60\x60", readme, flags=re.MULTILINE)) % 2:
        errors.append("readme-semantic-unclosed-code-fence")
    if not re.search(r"(?<!\d)71 declared CLI commands(?!\d)", readme):
        errors.append("readme-semantic-cli-count")
    if len(readme.split()) > 1800:
        errors.append("cto-readme-overlong")
    if "CORA is not an eleventh engineering method" not in readme:
        errors.append("cto-method-positioning-missing")
    for marker in README_SPECIFIC_TRUTHS:
        if marker not in readme:
            errors.append("readme-semantic-required-truth:" + marker[:70])
    for pattern in README_FALSE_PROMOTIONS:
        if re.search(pattern, readme, flags=re.IGNORECASE):
            errors.append("readme-semantic-false-promotion:" + pattern)
    if root is not None:
        for href in markdown_links(readme):
            target = resolve("README.md", href)
            if target is not None and not (root / target[0]).exists():
                errors.append("readme-semantic-broken-link:" + target[0])
    return sorted(set(errors))


# PR-23: bounded editorial/navigation predicates, not a second authority.
# All paths remain checked for existence and reachability by verify().
NAVIGATION_LENSES = {
    "Product": ("docs/GETTING_STARTED.md", "docs/DOD_V1_EXPERIMENTAL.md", "docs/RELEASE.md"),
    "Software": ("src/cora/", "tools/", "docs/ARCHITECTURE.md", "docs/CLI_REFERENCE.md"),
    "Repository": ("tests/", ".github/workflows/", "cora.ontology.json",
                   "docs/INDEX.md", "CHANGELOG.md"),
    "Governance": ("GOVERNANCE.md", "SECURITY.md", "CONTRIBUTING.md",
                   ".github/PULL_REQUEST_TEMPLATE.md", "LICENSE"),
    "Evidence and DoD": ("docs/CONTINUOUS_DEVELOPMENT.md",
                         "docs/CONVERGENT_ASSURANCE.md", "docs/DOCUMENTATION_DOD.md",
                         ".cora/assurance/documentation-proofs.json", "tools/verify_claim_evidence.py"),
}
NAVIGATION_READERS = {
    "First-time user": ("docs/GETTING_STARTED.md", "docs/ARCHITECTURE.md"),
    "Coding assistant or reviewer": ("docs/AGENT_ADOPTION.md",
                                     "AGENTS.md", "docs/CONTINUOUS_DEVELOPMENT.md"),
    "Forensic investigator": ("docs/FILE_LAB.md", "docs/HOLISTIC_FORENSICS.md",
                              "docs/ENGINEERING_DEBT.md"),
    "Product or release owner": ("GOVERNANCE.md", "SECURITY.md", "docs/RELEASE.md"),
    "Full documentation, history and contracts": ("docs/INDEX.md",
                                                 "docs/DOCUMENTATION_DOD.md"),
}




def verify_development_method_readme(readme: str) -> list[str]:
    """Scoped engineering-fidelity checks, not independent semantic understanding."""
    part = readme.split("## How CORA works\n", 1)
    section = part[1].split("\n## Use CORA with an AI coding assistant", 1)[0] if len(part) == 2 else ""
    if not section:
        return ["cto-method-absent"]
    errors = []
    blocks = (
        ("outcome", ("**1. Specify the outcome.**", "natural-language intent",
                     "AND-dependency graph", "backward", "unknown prerequisite")),
        ("slice", ("**2. Change one coherent unit.**", "authorized tools",
                   "content-addressed blobs", "directory trees", "New source SHA")),
        ("falsification", ("**3. Try to disprove it, then stop intelligently.**",
                           "seeded combinations", "separate expected-result rule",
                           "physical mutation testing", "surviving and inconclusive")),
        ("saturation", ("fixed scenario catalog and final window",
                        "bounded convergence", "not proof of complete correctness",
                        "no-progress rounds", "does not predict N")),
        ("target-examples", ("[ICTC](https://github.com/Luke883i/ictc)",
                             "[Teddy](https://github.com/Luke883i/teddy)",
                             "[iKant_EDU](https://github.com/Luke883i/iKant_EDU)",
                             "HTTP/SQLite", "source/UX verification",
                             "unknown consumers", "reversible repository contraction")),
        ("evidence-ownership", ("Source histories and native pilot evidence have distinct owners",
                                "CORA did not independently certify these products")),
        ("glossary", ("Terminology, only after the engineering method:",
                      "intent mining", "reticular DoD", "semantic slices",
                      "blobbing/materialization", "semantic mutations",
                      "semantic saturation")),
    )
    for label, terms in blocks:
        if any(t not in section for t in terms):
            errors.append("cto-method-lost:" + label)
    order = [section.find(m) for m in (
        "**1. Specify the outcome.**", "**2. Change one coherent unit.**",
        "**3. Try to disprove it, then stop intelligently.**",
        "**Target examples, not universal validation:**",
        "**Terminology, only after the engineering method:")]
    if min(order) < 0 or order != sorted(order):
        errors.append("cto-method-progressive-order")
    if any(x in section.lower() for x in (
            "certifies consciousness", "proves ictc compliance",
            "saturation proves complete correctness",
            "a million physical source mutants")):
        errors.append("cto-method-unearned-promotion")
    return sorted(set(errors))


def verify_contract_to_application_readme(readme: str) -> list[str]:
    """Short route to application contract and runtime boundaries."""
    parts = readme.split("## Use CORA with an AI coding assistant\n", 1)
    body = parts[1].split("\n## Interpret a CORA result", 1)[0] if len(parts) == 2 else ""
    required = ("[agent adoption](docs/AGENT_ADOPTION.md)",
                "[R1–R4 DoD](docs/DOD_PR20_CONVERGENCE.md)",
                "--contextual --intent", "The same intent is required for replay",
                "Run real tests and obtain independent review separately.",
                "does not independently write a feature",
                "LEVEL / NILO experiment", "genuine browser tests",
                "not an already delivered game",
                "docs/CONTINUOUS_DEVELOPMENT.md#level-demonstration-local-evidence-verifiable-engineering-lifecycle")
    return [] if body and all(x in body for x in required) else [
        "cto-contract-to-application-or-source-link-lost"]


def verify_multichannel_intro(readme: str) -> list[str]:
    """CTO first-read contract: compressed and bounded, not reader-tested."""
    intro = readme.split("## First five minutes", 1)[0]
    errors = []
    if not 115 <= len(intro.split()) <= 310:
        errors.append("cto-intro-compression-budget")
    groups = {
        "identity": ("# CORA — Continuous Ontological Repository Assurance",
                     "**CORA (Continuous Ontological Repository Assurance)**",
                     "**Engineering evidence for AI-assisted software changes.**"),
        "chain": ("the proposed change", "the source evidence", "tests or counterexamples",
                  "the work still needed", "exact Git SHA + evidence dossier"),
        "boundaries": ("**Product**", "**software**", "**repository**", "not a coding agent"),
        "audience": ("**Recommended use:**", "**Audience and conditions:**",
                     "**Open source license:**", "[MIT](LICENSE)", "Python 3.11+"),
        "release": ("1.0.0a5", "Current source is this Git revision", "v1.0.0a4", "draft",
                    "not a stable API or verified public release"),
    }
    for label, terms in groups.items():
        if any(x not in intro for x in terms):
            errors.append("cto-intro-missing:" + label)
    fence = chr(96) * 3
    if intro.count(fence + "text\n") != 1 or intro.count(fence + "\n") != 1:
        errors.append("cto-diagram-structure")
    if "--chat-step" not in readme or "--chat-bundle" not in readme:
        errors.append("cto-chat-path-lost")
    return sorted(set(errors))


def verify_project_first_readme(readme: str) -> list[str]:
    """Source-only Project onboarding guard; no plan or connector attestation."""
    parts = readme.split("## Use CORA in a ChatGPT Project — beginner walkthrough\n", 1)
    section = parts[1].split("\n## What works today", 1)[0] if len(parts) == 2 else ""
    required = (
        "ChatGPT Plus or Edu", "Projects are available on other plans",
        "**New project**", "**Project settings**", "**Project instructions**",
        "docs/AGENT_ADOPTION.md#chatgpt-project-beta-adapter",
        "**read access**", "Luke883i/cora", "**target repository**",
        "read-only", "write-capable coding tool", "such as Codex",
        "CORA-METHOD", "without** executing CORA-ENGINE",
        "separate Python runner", "METHOD_ONLY", "NOT_RUN",
        "--chat-step", "--chat-bundle", "iterations/000001/handoff.md",
        "neither automatic chat capture nor authenticated review",
    )
    errors = []
    if not section or any(token not in section for token in required):
        errors.append("project-onboarding-missing-source-boundary")
    if len(re.findall(r"(?m)^[1-5]\. \*\*[^\n]+", section)) != 5:
        errors.append("project-onboarding-five-steps-required")
    if re.search(r"(?i)github app (?:automatically|directly) (?:commits|pushes|merges)", section):
        errors.append("project-onboarding-false-write-authority")
    return errors


def verify_compact_document_bridge(guide: str, index: str, architecture: str) -> list[str]:
    """Reversible documentation assertion, not independent product acceptance."""
    errors = []
    contract_anchor = "## Example contract and evidence ladder"
    contract_sections = guide.split(contract_anchor, 1)
    contract = contract_sections[1] if len(contract_sections) == 2 else ""
    contract_facts = (
        "SQLite with versioned schema migrations",
        "reporters create actions", "reviewers may verify closure",
        "actual test receipts on the final PR",
        "REPLAN_STALLED_REPORTS", "not a universal",
        "independent reviewer",
    )
    if (not contract or "## LEVEL: contract-to-product" not in guide
            or any(term not in contract for term in contract_facts)):
        errors.append("cto-deep-guide-proof-loss")
    index_facts = ("compressed public front door",
                   "Implementation and historical detail",
                   "docs/")
    if any(t not in index for t in index_facts):
        errors.append("cto-navigation-hierarchy-drift")
    if "implemented in src/cora/chat_bundle.py" not in architecture:
        errors.append("cto-chat-owner-drift")
    return sorted(set(errors))



def verify_method_crosswalk(readme: str, crosswalk: str, index: str) -> list[str]:
    """Finite source-only methodology/claim bridge; not method conformance."""
    errors = []
    anchor = "docs/CONVERGENT_ASSURANCE.md#method-crosswalk--borrowed-perspectives-not-full-implementations"
    if f"[method crosswalk]({anchor})" not in readme:
        errors.append("cto-method-crosswalk-unreachable")
    if "[Method crosswalk](CONVERGENT_ASSURANCE.md#method-crosswalk--borrowed-perspectives-not-full-implementations)" not in index:
        errors.append("cto-method-index-route-missing")
    if "## Method crosswalk — borrowed perspectives, not full implementations" not in crosswalk:
        errors.append("cto-method-crosswalk-heading-missing")
    methods = ("C4 / arc42", "Domain-Driven Design", "Static dependency analysis",
               "Graph theory / SCC", "Event/data lineage",
               "Formal methods / contracts", "Mutation / metamorphic testing",
               "Software archaeology", "Threat modeling / assurance",
               "Architecture fitness functions")
    for name in methods:
        if f"| {name} |" not in crosswalk:
            errors.append("cto-method-crosswalk-entry-missing:" + name)
    boundaries = ("not a replacement", "not demonstrate", "No claim of biological equivalence",
                  "not an independently reproduced ChatGPT-container session")
    if any(term not in crosswalk for term in boundaries):
        errors.append("cto-method-crosswalk-boundary-lost")
    projects = (
        "ictc/blob/e641526114a508e24f86e8554c027d8cd6bbe715/v3/browser-onto-compliance-v1.py",
        "ictc/blob/e641526114a508e24f86e8554c027d8cd6bbe715/v3/s4-a6-ux4-uiux-mount-audit.md",
        "ictc/blob/e641526114a508e24f86e8554c027d8cd6bbe715/v3/uiux-656-absorption-contract.json",
        "ictc/blob/e641526114a508e24f86e8554c027d8cd6bbe715/v3/release-readiness-e2-product-mutants.mjs",
        "iKant_EDU/blob/73842c1d71ea1b1faa3903b255d00cd09b1b6cb6/docs/IKANT_COGNITIVE_SUBSTRATE.md",
        "iKant_EDU/blob/73842c1d71ea1b1faa3903b255d00cd09b1b6cb6/docs/CORA_PR_A_BACKLOG.md",
        "656-to-12 contract", "Actual source mutants")

    if any(term not in crosswalk for term in projects):
        errors.append("cto-method-real-project-bridge-lost")
    if re.search(r"\bCORA (?:fully implements|certifies) (?:C4|DDD|formal methods|consciousness)\b",
                 readme + "\n" + crosswalk, flags=re.I):
        errors.append("cto-method-overclaim")
    return sorted(set(errors))


def verify_progressive_readme(readme: str) -> list[str]:
    """Verify finite source navigation; not human usability or semantic completeness."""
    errors: list[str] = []
    front = readme.split("## How CORA works", 1)[0]
    for visible in ("**Current status:**", "**Recommended use:**",
                    "**Audience and conditions:**", "**Open source license:**",
                    "[MIT](LICENSE)", "Python 3.11+", "1.0.0a5", "not a stable API"):
        if visible not in front:
            errors.append("navigation-first-screen:" + visible)
    if "not a coding agent" not in front.lower().replace("*", ""):
        errors.append("navigation-first-screen:agent-boundary")
    try:
        section = readme.split("## Documentation by goal\n", 1)[1].split(
            "\n## Operating boundaries", 1)[0]
    except IndexError:
        return sorted(set(errors + ["navigation-section-missing"]))
    prefix = section.split("<details>", 1)[0]
    for reader, destinations in NAVIGATION_READERS.items():
        label = "**" + reader + ":**"
        candidate = next((line for line in prefix.splitlines() if label in line), "")
        if not candidate or any(dest not in candidate for dest in destinations):
            errors.append("navigation-reader-route:" + reader)
    blocks = re.findall(r"<details>\s*<summary>([^<\n]+)</summary>(.*?)</details>",
                        section, flags=re.DOTALL)
    if (section.count("<details>") != len(NAVIGATION_LENSES) or
        section.count("</details>") != len(NAVIGATION_LENSES) or
        section.count("<summary>") != len(NAVIGATION_LENSES) or
        len(blocks) != len(NAVIGATION_LENSES) or "<details open" in section):
        errors.append("navigation-disclosure-unbalanced")
    names = [m[0].split(" | ", 1)[0] for m in blocks]
    if names != list(NAVIGATION_LENSES):
        errors.append("navigation-lenses-duplicated-or-reordered")
    for (name, body), expected in zip(blocks, NAVIGATION_LENSES):
        if name.split(" | ", 1)[0] != expected:
            continue
        for target in NAVIGATION_LENSES[expected]:
            if target not in body:
                errors.append("navigation-lens-target:" + expected + ":" + target)
    for term in ("**Decision rights are external:**", "**Source of record:**",
                 "**Why:**", "**Runtime:**", "**Read in order:**"):
        if term not in section:
            errors.append("navigation-critical-boundary:" + term)
    if re.search(r"\bCORA (?:automatically approves merges|publishes releases automatically"
                 r"|independently certifies reviewers)\b", readme, re.I):
        errors.append("navigation-authority-promotion")
    if re.search(r"<(?:script|iframe|object|embed)\b", section, re.I):
        errors.append("navigation-unsupported-interaction")
    errors.extend(verify_readme_semantics(readme))
    errors.extend(verify_multichannel_intro(readme))
    errors.extend(verify_project_first_readme(readme))
    errors.extend(verify_development_method_readme(readme))
    errors.extend(verify_contract_to_application_readme(readme))
    return sorted(set(errors))


def verify(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    try:
        registry = json.loads((root / "docs/documentation-registry.json").read_text("utf-8"))
        records = registry["documents"]
        if (registry["schema"] != "cora-documentation-registry/1" or
            registry["baseline_markdown_count"] != BASELINE_MD or
            registry["baseline_sha"] != BASELINE_SHA or
            registry["files_expected"] != EXPECTED_MD or
            registry["authority"] != "MAINTAINER_DECLARATION_NOT_INDEPENDENT_ATTESTATION"):
            raise ValueError("registry contract altered")
    except (OSError, ValueError, KeyError, TypeError):
        return ["invalid-documentation-registry"]
    actual = set()
    for p in root.rglob("*.md"):
        rel = p.relative_to(root)
        if any(part.startswith(".") and part not in (".github",) for part in rel.parts):
            continue
        if any(part in ("build", "dist", "site-packages") for part in rel.parts):
            continue
        actual.add(rel.as_posix())
    declared = [r.get("path") for r in records if isinstance(r, dict)]
    if len(declared) != EXPECTED_MD or len(set(declared)) != len(declared):
        errors.append("duplicate-or-wrong-document-count")
    if set(declared) != actual:
        errors.extend("unregistered:" + p for p in sorted(actual - set(declared)))
        errors.extend("missing:" + p for p in sorted(set(declared) - actual))
    if sum(bool(r.get("baseline_blob")) for r in records if isinstance(r, dict)) != BASELINE_MD:
        errors.append("baseline-43-markdown-count-drift")
    original = set()
    for r in records:
        if not isinstance(r, dict):
            errors.append("invalid-registry-entry")
            continue
        path = r.get("path")
        if not isinstance(path, str) or path.startswith("/") or ".." in path.split("/"):
            errors.append("invalid-path")
            continue
        historical = (path.startswith("docs/archive/") or path.startswith("docs/ADR-") or path.startswith("docs/AUDIT_")
                      or path in KNOWN_HISTORICAL)
        if r.get("status") not in STATUS or r.get("kind") not in KINDS or r.get("group") not in VALID_GROUP:
            errors.append("invalid-classification:" + path)
        if historical and (r.get("status") != "HISTORICAL" or
                           r.get("authority") != "HISTORICAL_RECORD"):
            errors.append("historical-authority-promoted:" + path)
        if r.get("baseline_blob"):
            original.add(path)
            if historical and (root / path).is_file() and git_blob_sha(
                (root / path).read_bytes()) != r["baseline_blob"]:
                errors.append("historical-content-changed:" + path)
    if len(original) != BASELINE_MD:
        errors.append("historical-baseline-incomplete")
    graph = {p: set() for p in actual}
    for path in sorted(actual):
        content = (root / path).read_text("utf-8")
        for href in markdown_links(content):
            target = resolve(path, href)
            if target is None:
                continue
            name, anchor = target
            dest = root / name
            if not dest.exists():
                errors.append("broken-link:" + path + ":" + name)
            elif anchor and dest.is_file() and dest.suffix == ".md" and (
                anchor not in heading_slugs(dest.read_text("utf-8"))):
                errors.append("broken-anchor:" + path + ":" + name + "#" + anchor)
            if name in graph:
                graph[path].add(name)
    reached, queue = {"README.md"}, ["README.md"]
    while queue:
        for linked in sorted(graph.get(queue.pop(0), ())):
            if linked not in reached:
                reached.add(linked)
                queue.append(linked)
    errors.extend("unreachable:" + p for p in sorted(actual - reached))
    for path in actual - {"docs/INDEX.md"}:
        if path not in graph.get("docs/INDEX.md", set()):
            errors.append("not-indexed:" + path)
    try:
        cli = ast.parse((root / "src/cora/cli.py").read_text("utf-8"))
        parsers = [n.args[0].value for n in ast.walk(cli)
                   if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                   and n.func.attr == "add_parser" and n.args
                   and isinstance(n.args[0], ast.Constant)
                   and isinstance(n.args[0].value, str)]
        reference = COMMAND.findall((root / "docs/CLI_REFERENCE.md").read_text("utf-8"))
        if len(parsers) != len(set(parsers)) or sorted(reference) != sorted(parsers):
            errors.append("cli-reference-parser-drift")
    except (OSError, SyntaxError):
        errors.append("cli-reference-unreadable")
    readme = (root / "README.md").read_text("utf-8")
    errors.extend(verify_progressive_readme(readme))
    if not (root / "LICENSE").is_file() or not (root / "LICENSE").read_text("utf-8").startswith("MIT License"):
        errors.append("navigation-mit-license-file-drift")
    required = ("# CORA — Continuous Ontological Repository Assurance",
                "**CORA (Continuous Ontological Repository Assurance)**",
                "## First five minutes", "## What works today",
                "## Use CORA with an AI coding assistant", "## Operating boundaries",
                "## Engineering map", "1.0.0a5", "cora --help", "cora snapshot",
                "docs/INDEX.md", "BLOCKED_EXTERNAL", "--intent")
    if any(token not in readme for token in required):
        errors.append("readme-contract-regression")
    # Physical line count is diagnostic, not evidence of usability or accuracy.
    # PR42 replaces the former 180-line hard gate with source-bound predicates.
    errors.extend(verify_readme_semantics(readme, root=root))
    errors.extend(verify_compact_document_bridge(
        (root / "docs/CONTINUOUS_DEVELOPMENT.md").read_text("utf-8"),
        (root / "docs/INDEX.md").read_text("utf-8"),
        (root / "docs/ARCHITECTURE.md").read_text("utf-8")))
    errors.extend(verify_method_crosswalk(
        readme, (root / "docs/CONVERGENT_ASSURANCE.md").read_text("utf-8"),
        (root / "docs/INDEX.md").read_text("utf-8")))
    for path in ("README.md", "docs/AGENT_ADOPTION.md", "docs/CONVERGENT_ASSURANCE.md"):
        if not (root / path).is_file():
            errors.append("missing-procedure:" + path)
        elif "--intent" not in (root / path).read_text("utf-8"):
            errors.append("contextual-intent-omitted:" + path)
    if "not a stable" not in readme.lower() and "not a stable api" not in readme.lower():
        errors.append("release-claim-regression")
    validate_dod(root, errors)
    try:
        errors.extend(census_markdown(root)["errors"])
    except (OSError, ValueError, KeyError) as exc:
        errors.append("markdown-census-unavailable:" + type(exc).__name__)
    return sorted(set(errors))



def check_current_contract(path: str, content: str, *,
                           expected_status: str = "CURRENT") -> list[str]:
    """Finite textual checks. They do not certify clarity, truth or a reader."""
    errors: list[str] = []
    intro = content.split("\n## ", 1)[0][:3000]
    if not re.search(r"(?m)^# [^\n]{8,}", content[:550]):
        errors.append("standalone-title:" + path)
    required = ("**Document status:**", "**Current scope:**",
                "**Operational use:**", "**Evidence:**", "**Limits:**")
    for field in required:
        if intro.count(field) != 1:
            errors.append("standalone-field:" + path + ":" + field)
        else:
            line = next((s for s in intro.splitlines() if field in s), "")
            tail = line.split(field, 1)[1].strip(" |.*")
            if len(tail) < 5:
                errors.append("standalone-empty-field:" + path + ":" + field)
    match = re.search(r"\*\*Document status:\*\*\s*(CURRENT|SCOPED_CURRENT)\b", intro)
    if not match or match.group(1) != expected_status:
        errors.append("standalone-scope-promotion:" + path)
    if re.search(r"\bCORA (?:automatically approves merges|certifies reviewers|"
                 r"is independently enterprise[- ]ready|automatically deletes source code)\b",
                 content, re.I):
        errors.append("standalone-false-authority:" + path)
    return errors


def census_markdown(root: Path, *, revision: str = "HEAD",
                    overrides: dict[str, str] | None = None) -> dict:
    """Exhaustive current Markdown graph from real Git, not a self-issued DoD.

    A worktree override is exclusively a falsification input. It must fail
    Git blob parity and therefore can never become an observed original blob.
    Links and headings are local observations; external HTTP is NOT_PROBED.
    """
    import subprocess

    root = Path(root).resolve(strict=True)
    def git(*args: str) -> bytes:
        proc = subprocess.run(("git", "-C", str(root), *args),
                              capture_output=True, timeout=45, check=False)
        if proc.returncode:
            raise ValueError("census-original-git-unavailable")
        return proc.stdout

    sha = git("rev-parse", "--verify", revision + "^{commit}").decode().strip()
    raw = git("ls-tree", "-rz", sha)
    tree: dict[str, str] = {}
    for item in raw.split(b"\0"):
        if item:
            header, filename = item.split(b"\t", 1)
            mode, kind, oid = header.decode().split(" ")
            if kind == "blob":
                tree[filename.decode("utf-8")] = oid
    reg = json.loads((root / "docs/documentation-registry.json").read_text("utf-8"))
    registered = {entry["path"]: entry for entry in reg["documents"]}
    tracked = sorted(path for path in tree if path.lower().endswith(".md"))
    errors: list[str] = []
    if set(tracked) != set(registered):
        errors.append("census-registry-tree-drift")
    bodies: dict[str, str] = {}
    rows: list[dict] = []
    references: dict[str, list[tuple[str, str]]] = {}
    overrides = overrides or {}
    for path in tracked:
        data = (root / path).read_bytes()
        content = overrides.get(path, data.decode("utf-8"))
        original_oid = tree[path]
        parity = git_blob_sha(content.encode("utf-8")) == original_oid
        if not parity:
            errors.append("worktree-git-parity:" + path)
        bodies[path] = content
        entry = registered.get(path, {})
        status = entry.get("status", "UNCLASSIFIED")
        lifecycle = ("ARCHIVAL_NON_NORMATIVE" if status == "HISTORICAL"
                     else "ACTIVE_SCOPED" if status == "SCOPED_CURRENT"
                     else "ACTIVE" if status == "CURRENT" else "UNKNOWN")
        if lifecycle == "UNKNOWN":
            errors.append("census-unclassified:" + path)
        if status != "HISTORICAL":
            errors.extend(check_current_contract(path, content, expected_status=status))
        heads = [m.group(1).strip() for m in
                 re.finditer(r"(?m)^#{1,6}\s+(.+)$", content)]
        local, remote, anchors = [], [], []
        for link in markdown_links(content):
            target = resolve(path, link)
            if target is None:
                if link.startswith(("https://", "http://")):
                    remote.append(link)
                continue
            location, fragment = target
            local.append((location, fragment))
            if fragment:
                anchors.append(location + "#" + fragment)
            if not (root / location).exists():
                errors.append("broken-link:" + path + ":" + location)
            elif fragment and location in tracked and (
                    fragment not in heading_slugs(
                        overrides.get(location, (root / location).read_text("utf-8")))):
                errors.append("broken-anchor:" + path + ":" + location + "#" + fragment)
        references[path] = local
        rows.append({
            "path": path, "status": status, "kind": entry.get("kind"),
            "lifecycle": lifecycle, "original_git_blob": original_oid,
            "source_parity": parity, "bytes": len(content.encode("utf-8")),
            "words": len(content.split()), "title": heads[0] if heads else "",
            "heading_count": len(heads), "inbound": 0,
            "outbound_local": len(local), "outbound_external_unprobed": len(remote),
            "local_target_paths": sorted({p for p, _ in local}),
            "local_anchors": sorted(set(anchors)),
            "history_headings": [h for h in heads if
                                 re.search(r"\bPR[- ]?\d+\b|historical|candidate|"
                                           r"earlier version", h, re.I)],
            "standalone_contract": "NOT_APPLICABLE_ARCHIVE" if status == "HISTORICAL"
                                    else "SOURCE_CHECKED",
            "interpretation": "MACHINE_SOURCE_HEURISTIC_NOT_HUMAN_COMPREHENSION",
        })
    for row in rows:
        row["inbound"] = sum(sum(1 for dest, _ in edges if dest == row["path"])
                             for edges in references.values())
        # An index entry is discoverability, not proof of operational use.
        row["inbound_active_nonindex"] = sum(
            sum(1 for dest, _ in edges if dest == row["path"])
            for source, edges in references.items()
            if source != "docs/INDEX.md" and
            registered.get(source, {}).get("status") in ("CURRENT", "SCOPED_CURRENT"))
        row["evaluation_route"] = (
            "ARCHIVAL_NON_NORMATIVE" if row["status"] == "HISTORICAL" else
            "ACTIVE_REFERENCED" if row["inbound_active_nonindex"] else
            "INDEX_ONLY_REVIEW")
        row["pr_history_mentions"] = len(re.findall(
            r"\bPR[- #]?\d+\b", bodies[row["path"]], flags=re.I))
    # Readback may execute from an uncommitted mutation. Never promote it to
    # source truth; zero errors and Git parity are jointly necessary.
    return {
        "schema": "cora-markdown-census/1", "source_commit": sha,
        "source": "ORIGINAL_GIT_TREE_AND_WORKTREE_PARITY",
        "authority": "NONE", "external_acceptance": "BLOCKED_EXTERNAL",
        "external_links": "NOT_PROBED",
        "counts": {
            "markdown": len(tracked),
            "active": sum(x["status"] in ("CURRENT", "SCOPED_CURRENT") for x in rows),
            "historical": sum(x["status"] == "HISTORICAL" for x in rows),
            "broken_local_links": sum(x.startswith(("broken-link:", "broken-anchor:"))
                                      for x in errors),
            "missing_current_contracts": sum(x.startswith("standalone-") for x in errors),
            "original_git_parity": sum(x["source_parity"] for x in rows),
            "edges": sum(x["outbound_local"] for x in rows),
            "active_index_only": sum(x["evaluation_route"] == "INDEX_ONLY_REVIEW" for x in rows),
            "active_history_mentions": sum(x["pr_history_mentions"] for x in rows if x["status"] != "HISTORICAL"),
        },
        "documents": rows,
        "errors": sorted(set(errors)),
        "status": "PASS_SCOPED" if not errors else "REFUTED",
    }



# Enterprise-evaluable means eligible for an external decision, never approved.
# This 20-bit finite model does not execute third-party targets.
ENTERPRISE_SOURCE_LEAVES = (
    "exact_git_revision", "markdown_inventory", "original_blob_parity",
    "standalone_active_docs", "local_links", "reader_routes",
    "current_product_identity", "readme_minimality", "method_nonpromotion",
    "candidate_sbom_scope", "bounded_sca_scope", "exact_head_release",
)
ENTERPRISE_EXTERNAL_LEAVES = (
    "first_read_user_study", "maintained_target_experiment",
    "independent_human_review", "enforced_host_controls",
    "verified_signed_provenance", "security_owner_acceptance",
    "release_manager_decision", "independent_operational_review",
)


def assess_enterprise_cut(mask: int) -> str:
    """Noncompensatory finite DoD model: never grants product or release authority."""
    if isinstance(mask, bool) or not isinstance(mask, int) or not 0 <= mask < (1 << 20):
        raise ValueError("enterprise-mask-invalid")
    source_required = (1 << len(ENTERPRISE_SOURCE_LEAVES)) - 1
    external_required = ((1 << len(ENTERPRISE_EXTERNAL_LEAVES)) - 1) << len(ENTERPRISE_SOURCE_LEAVES)
    if mask & source_required != source_required:
        return "REFUTED_SOURCE"
    if mask & external_required != external_required:
        return "BLOCKED_EXTERNAL"
    return "EVALUATION_ELIGIBLE"



def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--census-output", type=Path, help="write exhaustive Git-bound Markdown graph receipt")
    args = parser.parse_args()
    errors = verify(args.repo)
    if args.census_output:
        report = census_markdown(args.repo)
        args.census_output.parent.mkdir(parents=True, exist_ok=True)
        args.census_output.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps({"schema": "cora-documentation-verification/1",
                      "status": "PASS_SCOPED_STATIC" if not errors else "FAIL",
                      "source_ci": "NOT_ATTESTED_BY_THIS_PROCESS",
                      "governed": "BLOCKED_EXTERNAL", "authorization": "NONE",
                      "errors": errors}, indent=2, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
