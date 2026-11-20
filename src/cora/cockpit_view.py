"""Read-only offline navigation over an already verified ChatGPT handoff ZIP."""
from __future__ import annotations

from html import escape
from pathlib import Path
from zipfile import ZipFile

from .chat_bundle import _strict_json, verify_chat_bundle


def render_verified_cockpit(bundle: Path, *, expected_receipt: dict | None = None) -> str:
    """Replay bytes before projecting HTML. No JavaScript, network, or execution."""
    bundle = Path(bundle)
    report = verify_chat_bundle(bundle, expected_receipt=expected_receipt)
    prefix = f'iterations/{report["iterations"]:06d}/'
    with ZipFile(bundle) as z:
        step = _strict_json(z.read(prefix + "step.json"))
        trace = _strict_json(z.read(prefix + "dod.json"))
        receipt = _strict_json(z.read(prefix + "source-receipt.json"))
    cockpit = report["cockpit"]
    continuation = report["continuation"]

    def h(value: object) -> str:
        return escape(str(value), quote=True)

    anchors = {n["id"]: f'dod-{i + 1}' for i, n in enumerate(step["dod"]["nodes"])}
    rows = []
    for node in step["dod"]["nodes"]:
        rows.append(
            f'<tr id="{anchors[node["id"]]}"><th>{h(node["id"])}</th>'
            f'<td>{h(node["acceptance"])}</td><td>{h(node["scope"])}</td>'
            f'<td>{h(trace["states"][node["id"]])}</td>'
            f'<td>{h(", ".join(node["depends_on"]) or "none")}</td></tr>')
    roads = []
    for item in step["roadmap"]:
        links = " ".join(f'<a href="#{anchors[ref]}">{h(ref)}</a>'
                         for ref in item["dod_refs"] if ref in anchors)
        roads.append(f'<li><strong>{h(item["id"])}</strong>: {h(item["action"])} '
                     f'[{h(item["status"])}] {links}</li>')
    gaps = []
    for item in step["gaps"]:
        links = " ".join(f'<a href="#{anchors[ref]}">{h(ref)}</a>'
                         for ref in item["blocks"] if ref in anchors)
        gaps.append(f'<li><strong>{h(item["id"])}</strong>: {h(item["description"])} '
                    f'({links}). Next: {h(item["next_action"])}</li>')
    nav = "".join(f'<a href="#{key}">{label}</a>' for key, label in (
        ("overview", "Overview"), ("dod", "DoD & evidence"),
        ("roadmap", "Roadmap"), ("gaps", "Blockers"), ("actions", "Choices")))
    choices = (
        ("explain", "EXPLAIN", "Explain blockers, evidence boundaries and the first unresolved AND obligation."),
        ("replan", "REPLAN", "Recalculate the roadmap from unresolved obligations. Do not execute."),
        ("propose", "PROPOSE_NEXT_CHECK", "Propose one reversible negative test. Do not execute or approve."),
    )
    actions = "".join(f'<a class="choice" href="#{key}">{label}</a>'
                      for key, label, _ in choices)
    instructions = "".join(
        f'<section id="{key}"><h3>{label}</h3><p>Copy this into your authorized chat:</p>'
        f'<blockquote>{h(instruction)}</blockquote></section>'
        for key, label, instruction in choices)
    next_checks = ", ".join(
        f'{a["action_id"]}: {", ".join(a["falsifier_ids"])}'
        for a in continuation["next_falsification_actions"]) or "No source-backed check; request independent acceptance."
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>CORA verified ZIP navigator</title>
<style>
body{{font:16px/1.5 system-ui,sans-serif;color:#1f2937;background:#f7f6f3;max-width:1000px;margin:auto;padding:1rem 1.5rem}}
nav{{display:flex;gap:1rem;flex-wrap:wrap;margin:1rem 0}}a{{color:#155e75}}
section{{background:white;border:1px solid #d6d3d1;border-radius:.5rem;margin:1rem 0;padding:1rem}}
table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #d6d3d1;text-align:left;padding:.5rem;vertical-align:top}}
th{{background:#f2f4f7}}.choice{{display:inline-block;border:1px solid #475569;padding:.5rem;margin:.3rem;border-radius:.4rem}}
code{{overflow-wrap:anywhere}}blockquote{{border-left:3px solid #334155;padding:.5rem 1rem}}:target{{outline:2px solid #0e7490}}
</style></head><body>
<header><h1>CORA — verified ZIP decision navigator</h1>
<p><strong>Read-only, offline and non-executing.</strong> Not a live ChatGPT plugin. Links navigate only within this document.</p>
<nav aria-label="Decision navigation">{nav}</nav></header><main>
<section id="overview"><h2>Current decision</h2>
<p><strong>Status:</strong> {h(cockpit["status"])} |
<strong>Recommended:</strong> {h(cockpit["recommended"])} |
<strong>Reported open leaves:</strong> {h(cockpit["reported_open_dod_leaves"])}</p>
<p><strong>Why:</strong> {h(cockpit["what_changed"])}</p>
<p><strong>Next unresolved:</strong> {h(cockpit["next_unresolved"])}</p>
<p><strong>Git SHA:</strong> <code>{h(receipt["commit"])}</code> |
<strong>Session:</strong> {h(report["session_id"])} |
<strong>Round:</strong> {h(report["iterations"])}</p>
<p><strong>Unknown:</strong> remaining time, remaining phases, product acceptance, reviewer and host authority.</p></section>
<section id="dod"><h2>AND obligations and evidence</h2>
<p>States are derived from caller reports in a verified ZIP, not independently witnessed target behavior.</p>
<table><thead><tr><th>ID</th><th>Acceptance</th><th>Scope</th><th>State</th><th>Depends on</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></section>
<section id="roadmap"><h2>Reported roadmap</h2><ol>{''.join(roads)}</ol></section>
<section id="gaps"><h2>Unresolved gaps</h2><ul>{''.join(gaps)}</ul></section>
<section id="actions"><h2>Human choices — none executes</h2>{actions}
<p><strong>Suggested check:</strong> {h(next_checks)}</p></section>
{instructions}
<section id="boundary"><h2>Proof boundary</h2><p>{h(report["status"])}</p>
<p>Authorization: NONE. Product: BLOCKED_EXTERNAL. No link writes Git, runs tests, approves a release or automatically replans. Reverify and reopen the latest ZIP after each iteration.</p></section>
</main></body></html>
"""
