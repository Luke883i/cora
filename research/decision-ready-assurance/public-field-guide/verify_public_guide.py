"""Source-only editorial and original-Git-link oracle for the standalone guide.

The audit deliberately cannot certify target runtime behavior, publication approval,
human comprehension, or causal benefit from the method.
"""
from pathlib import Path
import csv
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
GUIDE = HERE / "From_Intent_to_Evidence.markdown"
SOURCE = HERE.parent / "aosp-r5" / "R5_PIN_REGISTER.tsv"
PROJECTS = ("ICTC", "Teddy", "LUMEN", "NILO", "iKant_EDU", "CORA", "academics")
MATERIAL = (
    "A claim is as strong as the observation that supports it",
    "not 149 independently repeated product tests",
    "All mandatory conditions must hold",
    "cannot approve itself",
    "not a running product",
    "does not mean that the live application was broken",
    "Unknown consumers are unresolved work",
    "not independently certify legal compliance",
    "cannot establish charm",
    "does not establish live institutional catalogue integration",
    "cannot prove successful admission",
    "does not establish superiority to a strong checklist",
    "cannot alone show that a method caused faster or better engineering",
)

def expected_links():
    with SOURCE.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="|"))
    assert len(rows) == 40 and all(len(row["sha"]) == 40 and len(row["blob"]) == 40 for row in rows)
    return [
        "https://github.com/Luke883i/{repo}/blob/{sha}/{path}".format(**row)
        for row in rows
    ]

def assess(content, links):
    problems = []
    found = re.findall(r"\]\((https://github\.com/[^)]+)\)", content)
    if sorted(found) != sorted(links):
        problems.append("EXACT_ORIGINAL_SOURCE_LINKS")
    if len(found) != 40 or len(set(found)) != 40:
        problems.append("SOURCE_LINK_COUNT_OR_DUPLICATES")
    # Remove full URL targets before judging reader-facing terminology.
    visible = re.sub(r"\]\(https://github\.com/[^)]+\)", "]", content)
    if re.search(r"\bR[1-9]\d*\b|\bPR\b|\bHEAD\b|\bDoD\b|\bA0\b", visible):
        problems.append("OPERATIVE_DOCUMENT_HISTORY_OR_SHORTHAND")
    for heading in PROJECTS:
        if not re.search(r"^## " + re.escape(heading) + r"\s*$", content, re.M):
            problems.append("MISSING_PROJECT_" + heading)
    for fragment in MATERIAL:
        if fragment not in visible:
            problems.append("MATERIAL_CLAIM_NOT_PRESERVED_" + fragment)
    return problems

def main():
    text = GUIDE.read_text(encoding="utf-8")
    links = expected_links()
    assert not assess(text, links), assess(text, links)
    attempted = []
    # 40 separate corrupted, physically different source text copies.
    for number, source in enumerate(links, 1):
        mutated = text.replace(source, source.replace("/Luke883i/", "/invented-author/"), 1)
        assert mutated != text
        attempted.append(("SOURCE_LINK_" + str(number), bool(assess(mutated, links))))
    # Seven missing/renamed reader-facing project sections.
    for heading in PROJECTS:
        mutated = text.replace("\n## " + heading + "\n", "\n## Unknown project\n", 1)
        assert mutated != text
        attempted.append(("CASE_" + heading, bool(assess(mutated, links))))
    # Thirteen material copy substitutions that should be rejected.
    for number, fragment in enumerate(MATERIAL, 1):
        mutated = text.replace(fragment, "All outcomes are independently certified", 1)
        assert mutated != text
        attempted.append(("COPY_" + str(number), bool(assess(mutated, links))))
    benign = []
    for i in range(10):
        benign.append(not assess(text + ("\n" * (i + 1)), links))
    report = {
        "schema": "public-guide-source-only/1",
        "status": "PASS_AUTHOR_SCOPED" if len(attempted) == 60 and all(x[1] for x in attempted) and all(benign) else "FAIL",
        "markdown_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "links": len(links),
        "semantic_claim_anchors": len(MATERIAL),
        "physical_modified_markdown_cases": len(attempted),
        "detected": sum(x[1] for x in attempted),
        "survivors": [name for name, killed in attempted if not killed],
        "benign_controls": len(benign),
        "benign_passed": sum(benign),
        "target_runtime": "NOT_REEXECUTED",
        "human_acceptance": "NOT_OBSERVED",
        "causal_advantage": "NOT_ESTABLISHED",
    }
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "PASS_AUTHOR_SCOPED" else 1

if __name__ == "__main__":
    raise SystemExit(main())
