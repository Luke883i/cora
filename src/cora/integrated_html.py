"""Single self-contained, escaped, searchable CORA forensic HTML dossier."""
from __future__ import annotations

import hashlib
import html
import json

SCHEMA = "cora-integrated-one-run/2"
SCRIPT = r"""(function(){
"use strict";
const q=document.getElementById("search");
const kinds=document.getElementById("kind-filter");
const states=document.getElementById("state-filter");
const cards=[...document.querySelectorAll("article.activity")];
const tally=document.getElementById("visible-count");
const historyFilter=document.getElementById("history-filter");
if(historyFilter){
 const units=[...document.querySelectorAll("article.commit-unit")];
 const groups=[...document.querySelectorAll("details.pr-record")];
 const count=document.getElementById("history-filter-count");
 function updateHistory(){
  const term=historyFilter.value.trim().toLowerCase();let shown=0;
  for(const u of units){const match=!term||u.dataset.search.includes(term);u.hidden=!match;if(match)shown++;}
  for(const g of groups)g.hidden=![...g.querySelectorAll("article.commit-unit")].some(u=>!u.hidden);
  count.textContent=shown+" / "+units.length+" commits";
 }
 historyFilter.addEventListener("input",updateHistory);updateHistory();
}
function apply(){
 const term=q.value.trim().toLowerCase(), kind=kinds.value, state=states.value;
 let shown=0;
 for(const el of cards){
  const yes=(!term || el.dataset.search.includes(term)) &&
            (!kind || el.dataset.kind===kind) &&
            (!state || el.dataset.state===state);
  el.hidden=!yes;if(yes)shown++;
 }
 tally.textContent=shown+" / "+cards.length+" activities visible";
}
for(const el of [q,kinds,states]) el.addEventListener("input",apply);
apply();
})();"""
CSP = ("default-src 'none'; base-uri 'none'; form-action 'none'; "
       "connect-src 'none'; img-src 'none'; object-src 'none'; "
       "style-src 'unsafe-inline'; script-src 'sha256-" +
       __import__("base64").b64encode(hashlib.sha256(SCRIPT.encode()).digest()).decode() + "'")
STYLE = """
:root{color-scheme:light;font-family:system-ui,-apple-system,sans-serif;color:#17263c;background:#f6f3ed}
*{box-sizing:border-box}body{max-width:1500px;margin:0 auto;padding:18px 24px 80px}
header{background:#10243c;color:white;padding:27px;border-radius:12px}h1{font-size:28px;margin:0 0 10px}
h2{font-size:23px;margin:32px 0 12px}h3{font-size:17px}a{color:#195a8c}header a{color:#d4e9ff}
nav{display:flex;flex-wrap:wrap;gap:12px;margin-top:15px}nav a{color:#e4edfa}
.muted{color:#5b6979}.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}
.tile,section.panel,article.activity{background:white;border:1px solid #ddd8ce;border-radius:10px;padding:13px}
.tile strong{display:block;font-size:27px;margin:4px 0}.note{border-left:4px solid #b97730;padding:10px 15px;background:#fff7e9}
.controls{display:flex;flex-wrap:wrap;gap:15px;padding:14px 0;align-items:end}label{display:flex;gap:5px;flex-direction:column;font-weight:600}
input,select{padding:9px;border:1px solid #969da8;border-radius:7px;font-size:14px;min-width:210px}
article.activity{margin:5px 0}article.activity[hidden]{display:none}
details.pr-record{border:1px solid #ccd5dd;background:#fff;border-radius:9px;padding:12px;margin:9px 0}
details.pr-record>summary{font-size:15px}article.commit-unit{border-left:3px solid #2d5a7b;background:#f6f9fc;padding:7px 12px;margin:8px 0 8px 12px}
article.commit-unit[hidden],details.pr-record[hidden]{display:none}
.trace-pill{background:#ebf1f5;border-radius:4px;padding:2px 6px;font-size:12px}
.note-trust{background:#fff7e7;border-left:4px solid #b08944;padding:12px}

summary{cursor:pointer;font-weight:650;overflow-wrap:anywhere}small,code{overflow-wrap:anywhere}
pre{white-space:pre-wrap;word-break:break-word;background:#f4f6f8;padding:12px}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{text-align:left;padding:7px;border-bottom:1px solid #e3e7eb;vertical-align:top;overflow-wrap:anywhere}
th{background:#e6edf4}details{margin:7px 0}details[open]{border-color:#6082a9}
.status{border-radius:4px;padding:2px 6px;background:#e6ecf2;font-size:12px}
.FAIL,.BLOCKED,.DEBT_BLOCKED{background:#fce7df}.EXECUTED_SCOPED{background:#e4f1eb}.REUSED_SCOPED{background:#e8eef9}
footer{margin-top:42px;padding:12px;border-top:1px solid #d1d7dc;font-size:13px}
:focus-visible{outline:3px solid #195a8c;outline-offset:2px}
@media(max-width:650px){body{padding:10px}header{padding:18px}.controls>*{width:100%}input,select{width:100%}table{display:block;overflow-x:auto}}
"""


def _h(value: object) -> str:
    return html.escape(str(value), quote=True)


def _id(i: int) -> str:
    return "activity-" + str(i)


def render_integrated_html(receipt: dict) -> str:
    """Pure deterministic rendering; verify_integrated validates original Git first."""
    if (receipt.get("schema") != SCHEMA or receipt.get("authority") != "NONE"
            or receipt.get("authorization") != "NONE"
            or receipt.get("product_status") != "BLOCKED_EXTERNAL"
            or receipt.get("release_authorized") is not False):
        raise ValueError("unqualified or unsafe integrated HTML")
    rows = receipt["registry"]["activities"]
    attempts = receipt["attempts"]
    if [x["activity_id"] for x in rows] != [x["activity_id"] for x in attempts]:
        raise ValueError("unbound registry activities")
    attempts_by_id = {x["activity_id"]: x for x in attempts}
    n_methods = sum(x["kind"] == "INTERNAL_METHOD" for x in rows)
    m = receipt["metrics"]
    links = [("overview","Overview"),("inventory","Activity inventory"),
             ("test-cases","Individual tests"),("gaps","Unresolved gaps"),
             ("dod","DoD reticulum"),("artifacts","Evidence manifest"),
             ("provenance","Provenance")]
    if "genealogy" in receipt:
        links.insert(3, ("history", "PR / commit genealogy"))
    head = [
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">",
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
        '<meta http-equiv="Content-Security-Policy" content="' + _h(CSP) + '">',
        "<title>CORA | One-Run integrated forensic atlas</title><style>" + STYLE + "</style>",
        '</head><body><header><h1>CORA | One-Run forensic atlas</h1>',
        '<p>Git commit <code>' + _h(receipt["commit"]) + '</code> &middot; ' +
        'tree <code>' + _h(receipt["tree"]) + '</code></p>',
        '<p>Source: <strong>' + _h(receipt["source_status"]) +
        '</strong> &middot; Product: <strong>' + _h(receipt["product_status"]) +
        '</strong> &middot; Authorization: NONE</p>',
        "<nav aria-label=\"Dossier sections\">" +
        " ".join('<a href="#' + anchor + '">' + _h(label) + "</a>" for anchor,label in links) +
        "</nav></header>",
        '<main id="overview"><h2>Overview</h2>',
        '<div class="note" role="note"><strong>Proof boundary:</strong> ' +
        'source Git replay is not independent execution attestation. ' +
        'Catalogued CLI commands were not individually executed. Test results, ' +
        'if supplied, remain unauthenticated local observations. No merge/release approval.</div>',
        '<div class="tiles">',
    ]
    tiles = [
        ("Registered activities", m["registered_total"]),
        ("CLI entries declared", m["registered_cli"]),
        ("CLI individually executed", m["individually_executed_cli"]),
        ("Safe source methods", n_methods),
        ("Activities accounted", m["activity_accounted"]),
        ("Unobserved / not run", m["status_counts"].get("NOT_RUN",0)),
        ("Reported tests", m["reported_tests"] if m["reported_tests"] is not None else "NOT RUN"),
        ("Test events attributed", m["identified_test_events"]),
    ]
    head.extend('<section class="tile"><span>' + _h(label) + '</span><strong>' +
                _h(value) + '</strong></section>' for label,value in tiles)
    head.append('</div><h2 id="inventory">Activity inventory and execution outcomes</h2>')
    head.append('<p class="muted">Filter by source activity, current status or text. Expand any row to inspect '
                'its call path, scope, origin and evidence references. All registered entries remain visible '
                'even when they were not run.</p>')
    kinds = sorted({row["kind"] for row in rows})
    statuses = sorted({x["state"] for x in attempts})
    head.extend([
        '<div class="controls"><label for="search">Search activities',
        '<input id="search" type="search" autocomplete="off" placeholder="Name, method, path or reason"></label>',
        '<label for="kind-filter">Activity family<select id="kind-filter"><option value="">All</option>',
        "".join('<option value="' + _h(k) + '">' + _h(k) + '</option>' for k in kinds),
        '</select></label><label for="state-filter">Execution status<select id="state-filter"><option value="">All</option>',
        "".join('<option value="' + _h(s) + '">' + _h(s) + '</option>' for s in statuses),
        '</select></label></div><p id="visible-count" aria-live="polite"></p>',
    ])
    for i, (row, attempt) in enumerate(zip(rows, attempts)):
        activity_id = row["activity_id"]
        search = " ".join([activity_id,row["kind"],row["entrypoint"],
                           row["call_path"],str(attempt["reason"]),
                           " ".join(row["source_paths"])]).lower()
        head.append(
            '<article class="activity" id="' + _id(i) +
            '" data-search="' + _h(search) + '" data-kind="' + _h(row["kind"]) +
            '" data-state="' + _h(attempt["state"]) + '"><details><summary>' +
            '<span class="status ' + _h(attempt["state"]) + '">' + _h(attempt["state"]) +
            "</span> " + _h(activity_id) + " &middot; " + _h(row["kind"]) +
            '</summary><p><strong>Explanation:</strong> ' + _h(attempt["reason"]) +
            '</p><p><strong>Provenance:</strong> <code>' +
            _h(", ".join(row["source_paths"])) +
            '</code>; Git: <code>' + _h(receipt["commit"]) +
            '</code></p><p><strong>Call path:</strong> ' + _h(row["call_path"]) +
            '<br><strong>Effect:</strong> ' + _h(row["effect_class"]) +
            '<br><strong>Policy:</strong> ' + _h(row["authorization_policy"]) +
            '<br><strong>Adapter:</strong> ' + _h(row["execution_adapter"]) +
            '<br><strong>Verifier:</strong> ' + _h(row["verifier_id"]) +
            '<br><strong>Verification state:</strong> ' + _h(attempt["verification"]) +
            '<br><strong>Elapsed ms:</strong> ' + _h(attempt["elapsed_ms"]) +
            '<br><strong>Digest:</strong> <code>' + _h(attempt["source_digest"]) +
            '</code></p><p><strong>Dependencies:</strong> ' +
            _h(", ".join(row["dependencies"]) or "None declared") +
            '<br><strong>Evidence:</strong> ' +
            _h(", ".join(attempt["evidence_refs"]) or "Not observed") +
            '</p><p><a href="#artifacts">Evidence manifest</a> · ' +
            '<a href="#dod">DoD obligations</a></p></details></article>')
    head.append('</main>')
    test = receipt["tests"]
    head.append('<section class="panel" id="test-cases"><h2>Individual test events</h2>')
    head.append('<p>Runtime: <strong>' + _h(test["state"]) + '</strong> · ' +
                _h(test["reason"]) + ' · reported ' + _h(test["reported_tests"]) +
                ' · attributed ' + _h(len(test["parsed_cases"])) + '</p>')
    head.append('<p>Local log SHA-256: <code>' + _h(test["log_sha256"]) +
                '</code> · errors and traces are retained in the evidence artifact when '
                'an authorized runner was executed. Log hashing does not attest origin.</p>')
    if test["parse_warnings"]:
        head.append('<p class="note">Per-case reconciliation incomplete: ' +
                    _h(", ".join(test["parse_warnings"])) + '</p>')
    if not test["parsed_cases"]:
        head.append("<p>No individual test execution was observed.</p>")
    else:
        head.append('<table><thead><tr><th>Test case</th><th>Status</th><th>Detail</th></tr></thead><tbody>')
        for ev in test["parsed_cases"]:
            index = next((i for i,x in enumerate(rows)
                          if x["activity_id"] == ev["activity_id"]), None)
            title = _h(ev["activity_id"])
            if index is not None:
                title = '<a href="#' + _id(index) + '">' + title + '</a>'
            head.append('<tr><td>' + title + '</td><td>' + _h(ev["state"]) +
                        '</td><td>' + _h(ev["outcome"]) + '</td></tr>')
        head.append("</tbody></table>")
    head.append('</section><section class="panel" id="gaps"><h2>Gap and blocker register</h2>')
    head.append('<p>Unknown, skipped and unauthorized activities remain visible; '
                'no blocked item is converted into PASS.</p>')
    for gap in receipt["gaps"]["issues"]:
        head.append('<details><summary>' + _h(gap["reason"]) +
                    ' — ' + _h(gap["count"]) + ' activities</summary><p>' +
                    _h(gap["remediation"]) + '</p><ul>')
        for key in gap["activity_ids"]:
            index = next((i for i,x in enumerate(rows)
                          if x["activity_id"] == key), None)
            head.append('<li>' + ('<a href="#' + _id(index) + '">' + _h(key) + "</a>"
                                  if index is not None else _h(key)) + '</li>')
        head.append("</ul></details>")
    head.append('</section><section class="panel" id="dod"><h2>DoD trace and falsifiers</h2>')
    head.append('<p><strong>Integrated source goal:</strong> ' +
                _h(receipt["dod"]["source_goal"]) + ' · <strong>Global product:</strong> ' +
                _h(receipt["dod"]["product_goal"]) + '</p>')
    head.append('<table><thead><tr><th>Node</th><th>Scope</th><th>Status</th><th>Dependencies</th></tr></thead><tbody>')
    for node in receipt["dod"]["nodes"]:
        head.append('<tr><td><code>' + _h(node["id"]) + '</code></td><td>' +
                    _h(node["scope"]) + '</td><td>' + _h(node["state"]) + '</td><td>' +
                    _h(", ".join(node["depends_on"]) or "—") + '</td></tr>')
    head.append("</tbody></table></section>")
    head.append('<section class="panel" id="artifacts"><h2>Evidence manifest</h2><p>' +
                _h(receipt["evidence_manifest"]["state"]) +
                ' · every file is a local recording, not independently signed provenance.</p>')
    head.append('<table><thead><tr><th>Relative file</th><th>Bytes</th><th>SHA-256</th></tr></thead><tbody>')
    for file in receipt["evidence_manifest"]["files"]:
        head.append('<tr><td><code>' + _h(file["path"]) + '</code></td><td>' +
                    _h(file["bytes"]) + '</td><td><code>' + _h(file["sha256"]) +
                    '</code></td></tr>')
    head.append("</tbody></table></section>")
    history = receipt.get("genealogy")
    if history and history.get("status") != "NOT_AVAILABLE_BEFORE_PR38_BASELINE":
        head.append('<section class="panel" id="history"><h2>Genealogy — PR1–PR37</h2>')
        head.append('<p class="note-trust">Git source records: ' + _h(history["pr_count"]) +
                    ' PR, ' + _h(history["commit_count"]) +
                    ' commits. PR34 closed unmerged. Changed paths and counters are not '
                    'proof of current runtime behavior, safe deletion or external approval.</p>')
        head.append('<div class="tiles"><div class="tile">Commit deltas<strong>' +
                    _h(history["commit_count"]) + '</strong></div>'
                    '<div class="tile">Historical or relocated paths<strong>' +
                    _h(history["retention"]["historical_or_relocated_count"]) + '</strong></div>'
                    '<div class="tile">Deletions authorized<strong>0</strong></div></div>')
        head.append('<label for="history-filter">Search PR, SHA, file or method'
                    '<input id="history-filter" type="search" autocomplete="off" '
                    'placeholder="PR / SHA / path / obligation"></label>'
                    '<p id="history-filter-count" aria-live="polite"></p>')
        for pr in history["prs"]:
            head.append('<details class="pr-record" id="pr-' + _h(pr["number"]) +
                        '"><summary>PR ' + _h(pr["number"]) + ' · ' + _h(pr["title"]) +
                        ' <span class="trace-pill">' + _h(pr["state"]) + ' · ' +
                        _h(pr["commit_count"]) + ' commit</span></summary>'
                        '<p><a href="' + _h(pr["pr_url"]) +
                        '" rel="noopener noreferrer">GitHub PR</a> · ' +
                        _h(pr["phase"]) + ' · ' + _h(", ".join(pr["domains"])) + '</p>')
            for u in pr["commits"]:
                search = " ".join((str(pr["number"]), pr["title"], u["sha"],
                                   u["subject"], " ".join(u["paths"]),
                                   " ".join(u["obligations"]))).lower()
                head.append('<article class="commit-unit" id="commit-' + _h(u["sha"][:12]) +
                            '" data-search="' + _h(search) + '"><details><summary>' +
                            _h(u["sha"][:12]) + ' · ' + _h(u["subject"]) +
                            '</summary><p><span class="trace-pill">' + _h(u["unit_status"]) +
                            '</span> · +' + _h(u["additions"]) + ' / -' +
                            _h(u["deletions"]) + ' · ' + _h(u["path_count"]) +
                            ' files</p><p><a href="' +
                            _h("https://github.com/Luke883i/cora/commit/" + u["sha"]) +
                            '" rel="noopener noreferrer">Open original Git commit</a></p>'
                            '<p><strong>Required checks:</strong> ' +
                            _h("; ".join(u["obligations"])) +
                            '</p><details><summary>Paths and current lineage</summary><ul>')
                for path in u["paths"]:
                    state = "PRESENT_AT_BASELINE" if path in u["currently_present_paths"] else "HISTORICAL_OR_RELOCATED"
                    head.append('<li><code>' + _h(path) + '</code> · ' + _h(state) + '</li>')
                head.append('</ul></details></details></article>')
            head.append('</details>')
        delta = history["future_delta"]
        head.append('<h3>Future feature convergence</h3><p>' + _h(delta["status"]) +
                    ' · ' + _h(delta.get("source_conclusion", "NOT_ATTESTED")) +
                    '</p><details><summary>Current branch changes and required witnesses</summary>'
                    '<p><strong>Paths:</strong> ' +
                    _h(", ".join(delta.get("affected_paths", [])) or "None") +
                    '</p><p><strong>Obligations:</strong> ' +
                    _h("; ".join(delta["required_witnesses"]) or "None") +
                    '</p></details>')
        head.append('<h3>Retention review (non-authorizing)</h3>'
                    '<p>Former paths require migration and consumer mapping, '
                    'not automatic deprecation or removal.</p><details>'
                    '<summary>Inspect historical or relocated paths</summary><ul>')
        for item in history["retention"]["candidates"]:
            head.append('<li><code>' + _h(item["old_path"]) + '</code> · ' +
                        _h(item["classification"]) + ' · ' +
                        _h(item["independent_consumer_readback"]) + '</li>')
        head.append('</ul></details></section>')
    head.append('<section class="panel" id="provenance"><h2>Source and execution provenance</h2><pre>' +
                _h(json.dumps(receipt["execution_manifest"], ensure_ascii=True, sort_keys=True, indent=2)) +
                '</pre><p>Original PR36 receipt: <code>' +
                _h(receipt["baseline_pr36"]["receipt_digest"]) +
                '</code> · Integrated receipt: <code>' +
                _h(receipt["receipt_digest"]) + '</code></p></section>')
    head.append("<footer>Machine-readable truth: integrated JSON and manifest. "
                "Source evidence is not independent runtime proof, human approval or release permission."
                "</footer><script>" + SCRIPT + "</script></body></html>\n")
    return "".join(head)
