"""Deterministic, read-only CORA maturity and capability atlas.

The HTML is a view of pinned source assertions, never an independent witness.
The canonical owners remain synergy, integrated_service and reticulum.
"""
from __future__ import annotations

import html
import json
import re
import tomllib
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

from .evidence import domain_hash
from .git_snapshot import git
from .reticulum import EXTERNAL, MODEL, BLOCKED, assess_cut, ordered_cut

SCHEMA = "cora-maturity-atlas/1"
UNIFIED = "cora-five-synergies-unified/1"
DOD_PATH = ".cora/contracts/dod/maturity-dod.json"
CATALOG_PATH = ".cora/assurance/capability-atlas.json"
SOURCE_STATE = "GIT_SOURCE_MODEL_NOT_INDEPENDENT_BEHAVIOR"
HTML_MARKER = "CORA ATLAS | SOURCE-BOUNDED"
REPO_ID = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
GIT_SHA = re.compile(r"^[a-f0-9]{40}(?:[a-f0-9]{24})?$")


def _object(repo: Path, sha: str, path: str) -> dict:
    result = json.loads(git(repo, "show", sha + ":" + path, max_output=2_000_000))
    if not isinstance(result, dict):
        raise ValueError("expected Git-bound object at " + path)
    return result


def _tree(repo: Path, sha: str) -> dict[str, str]:
    """One bounded Git tree read, not a subprocess for every listed capability."""
    data = git(repo, "ls-tree", "-r", "-z", sha, max_output=8_000_000)
    result = {}
    for item in data.split(b"\x00"):
        if not item:
            continue
        metadata, path = item.split(b"\t", 1)
        mode, typ, oid = metadata.split(b" ")
        if typ != b"blob":
            continue
        result[path.decode("utf-8")] = oid.decode("ascii")
    return result


def _validate_nodes(contract: dict, tree: dict[str, str]) -> tuple[dict, dict]:
    if (contract.get("schema") != "cora-maturity-dod/1"
            or contract.get("authority") != "NONE"
            or contract.get("global_goal") != "G_MATURITY"):
        raise ValueError("maturity DoD identity or authority drift")
    nodes = contract.get("nodes", [])
    order = ordered_cut(nodes, "G_MATURITY")
    if len(order) != len(nodes):
        raise ValueError("maturity DoD contains unreachable/orphaned obligations")
    by = {x["id"]: x for x in nodes}
    gates = contract.get("gates")
    if (not isinstance(gates, list) or len(gates) != 6
            or len(set(gates)) != 6
            or by["G_MATURITY"]["depends_on"] != gates):
        raise ValueError("six mandatory noncompensatory gates changed")
    for x in nodes:
        if x.get("scope") not in ("SOURCE", "EXTERNAL"):
            raise ValueError("invalid maturity scope")
        if x["scope"] == "EXTERNAL" and not x["depends_on"] and x.get("witness_paths"):
            raise ValueError("source files cannot attest external acceptance")
    observations = {}
    missing = []
    for node in nodes:
        if node["depends_on"] or node["scope"] == "EXTERNAL":
            continue
        paths = node.get("witness_paths")
        if not isinstance(paths, list) or not paths or len(set(paths)) != len(paths):
            raise ValueError("source obligation without unique witness paths")
        if any(not isinstance(p, str) or p not in tree for p in paths):
            observations[node["id"]] = BLOCKED
            missing.append(node["id"])
        else:
            observations[node["id"]] = MODEL
    assessment = assess_cut(nodes, "G_MATURITY", observations)
    if assessment["status"] != EXTERNAL:
        raise ValueError("maturity source model incorrectly promoted to product approval")
    return assessment, {"missing_source_obligations": missing,
                        "gate_states": {g: assessment["states"][g] for g in gates}}


def build_atlas(repo: Path, unified: dict) -> dict:
    """Join original same-commit claims and catalog into one non-authoritative view."""
    if (not isinstance(unified, dict) or unified.get("schema") != UNIFIED
            or unified.get("authorization") != "NONE"):
        raise ValueError("original synergic source report is required")
    sha = unified.get("commit")
    if not isinstance(sha, str) or not GIT_SHA.fullmatch(sha):
        raise ValueError("source commit must be full Git object identity")
    repo = Path(repo).resolve(strict=True)
    if git(repo, "rev-parse", "--verify", sha + "^{commit}").decode().strip() != sha:
        raise ValueError("report commit cannot be resolved unchanged")
    tree = _tree(repo, sha)
    catalog = _object(repo, sha, CATALOG_PATH)
    contract = _object(repo, sha, DOD_PATH)
    ontology = _object(repo, sha, "cora.ontology.json")
    methods = _object(repo, sha, ".cora/contracts/profiles/method-atlas.json")
    route = _object(repo, sha, ".cora/contracts/index.json")
    package = tomllib.loads(git(repo, "show", sha + ":pyproject.toml").decode("utf-8"))
    identity = catalog.get("origin", {})
    repo_name = identity.get("repository", "")
    if not isinstance(repo_name, str) or not REPO_ID.fullmatch(repo_name):
        raise ValueError("invalid canonical repository identity")
    if (ontology.get("schema") != "cora-ontology/1"
            or {p["id"] for p in ontology["products"]} != {"cora"}
            or {x["id"] for x in ontology["software"]} !=
            {"cora-engine", "cora-release-verification"}
            or identity.get("product") != "cora"
            or sorted(identity.get("software", [])) !=
            ["cora-engine", "cora-release-verification"]):
        raise ValueError("product/software/repository identity contradiction")
    if (package.get("project", {}).get("scripts", {}).get("cora") != "cora.cli:main"
            or package["project"]["name"] != "cora-audit"):
        raise ValueError("distribution/CLI contract contradiction")
    entries = catalog.get("commands", [])
    families = catalog.get("families", [])
    if (len(entries) != 71 or len({x["command"] for x in entries}) != len(entries)
            or len(families) != 8
            or unified.get("method_counts", {}).get("commands") != 71
            or unified["method_counts"].get("original_methods") != len(methods["procedures"])):
        raise ValueError("source catalog does not match original unified service")
    fam_map = {x["id"]: x for x in families}
    if len(fam_map) != len(families):
        raise ValueError("duplicate source method family")
    unique_origin = defaultdict(set)
    capabilities = []
    for item in entries:
        fam, src, test = item["family"], item["method_source"], item["test_source"]
        if fam not in fam_map or src not in tree or test not in tree:
            raise ValueError("unbound capability source or test")
        if not isinstance(item.get("interaction"), str):
            raise ValueError("capability with unspecified interaction")
        unique_origin[(src, tree[src])].add(item["command"])
        unique_origin[(test, tree[test])].add(item["command"])
        capabilities.append({"command": item["command"], "family": fam,
                             "activity": item["interaction"],
                             "source": {"path": src, "oid": tree[src]},
                             "test": {"path": test, "oid": tree[test]},
                             "proof": "DECLARED_SOURCE_AND_TEST_PATH_NOT_EXECUTED"})
    capabilities.sort(key=lambda x: (x["family"], x["command"]))
    procedures = []
    for x in methods["procedures"]:
        path = x["source"]
        if path not in tree:
            raise ValueError("method owner not present at original commit")
        procedures.append({"id": x["id"], "source": path, "oid": tree[path],
                           "proof": "ORIGINAL_SOURCE_OWNER_NOT_RUNTIME_PROOF"})
    procedures.sort(key=lambda x: x["id"])
    assessment, diagnostic = _validate_nodes(contract, tree)
    if (DOD_PATH not in tree or not any(
            x["canonical"] == DOD_PATH for x in route.get("bindings", []))):
        raise ValueError("maturity DoD is not routed by canonical contract index")
    artifacts = {
        "source_modules": sorted(x for x in tree if x.startswith("src/cora/") and x.endswith(".py")),
        "release_tools": sorted(x for x in tree if x.startswith("tools/") and x.endswith(".py")),
        "workflow_files": sorted(x for x in tree if x.startswith(".github/workflows/") and x.endswith(".yml")),
        "test_files": sorted(x for x in tree if x.startswith("tests/") and x.endswith(".py")),
        "documentation_files": sorted(x for x in tree if x.startswith("docs/") and x.endswith(".md")),
        "contracts": sorted(x for x in tree if x.startswith(".cora/contracts/") and x.endswith(".json"))
    }
    shared = [{"path": p, "oid": oid, "referenced_by": sorted(commands)}
              for (p, oid), commands in sorted(unique_origin.items())
              if len(commands) > 1]
    result = {
        "schema": SCHEMA, "commit": sha, "source_schema": UNIFIED,
        "source_receipt_digest": unified["receipt_digest"],
        "identity": {
            "product": "cora", "software": sorted(x["id"] for x in ontology["software"]),
            "repository": repo_name, "distribution": package["project"]["name"],
            "distribution_version": package["project"]["version"],
            "entrypoint": package["project"]["scripts"]["cora"],
            "release": "ALPHA_SOURCE_CANDIDATE_NOT_PUBLISHED_OR_APPROVED"},
        "capability_families": families,
        "capabilities": capabilities, "procedures": procedures,
        "artifacts": artifacts,
        "maturity": {"goal": "G_MATURITY", "nodes": contract["nodes"],
                     "gates": contract["gates"], "assessment": assessment,
                     **diagnostic, "authority": "NONE"},
        "lineage": {"unique_git_origins": len(unique_origin),
                    "shared_git_origins": shared,
                    "independent_corroborations": 0,
                    "rule": "SAME_GIT_BLOB_NEVER_COUNTS_AS_INDEPENDENT_CORROBORATION"},
        "view_scope": SOURCE_STATE,
        "host_controls": "NOT_ATTESTED_BY_GIT",
        "behavioral_validity": "BLOCKED_EXTERNAL",
        "novice_acceptance": "BLOCKED_EXTERNAL",
        "model_provider_invoked": False, "authorization": "NONE"
    }
    result["atlas_digest"] = domain_hash("CORA:maturity-atlas:1", result)
    return result


def _safe(value: object) -> str:
    return html.escape(str(value), quote=True)


def render_html(atlas: dict) -> str:
    """Offline responsive HTML with text-only data, no external assets or network calls."""
    if not isinstance(atlas, dict) or atlas.get("schema") != SCHEMA:
        raise ValueError("invalid atlas source schema")
    if atlas.get("authorization") != "NONE":
        raise ValueError("atlas is not an authorization surface")
    commit, owner = atlas["commit"], atlas["identity"]["repository"]
    if not GIT_SHA.fullmatch(commit) or not REPO_ID.fullmatch(owner):
        raise ValueError("invalid Git hyperlink source")
    def source(path: str) -> str:
        return ("https://github.com/" + owner + "/blob/" + commit + "/" +
                quote(path, safe="/"))
    def link(path: str, label: str | None = None) -> str:
        return ('<a rel="noopener noreferrer" target="_blank" href="' +
                _safe(source(path)) + '">' + _safe(label or path) + '</a>')
    cards = []
    for family in atlas["capability_families"]:
        items = [c for c in atlas["capabilities"] if c["family"] == family["id"]]
        command_rows = []
        for c in items:
            search = " ".join([c["command"], family["label"], c["activity"], c["source"]["path"]])
            command_rows.append(
                '<article class="command searchable" data-search="' + _safe(search.lower()) + '">' +
                '<div><code>cora ' + _safe(c["command"]) + '</code><div class="muted small">' +
                _safe(c["activity"].replace("_", " ").lower()) + '</div></div>' +
                '<div class="references">' + link(c["source"]["path"], "Source") +
                '<span aria-hidden="true">·</span>' + link(c["test"]["path"], "Test source") +
                '<span class="tag">Unexecuted witness</span></div></article>')
        cards.append('<section class="family" id="family-' + _safe(family["id"]) + '">' +
                     '<h3>' + _safe(family["label"]) + '<span class="count">' +
                     str(len(items)) + ' comandi</span></h3>' +
                     '<p class="muted">' + _safe(family["method"]) + ' · ' +
                     _safe(family["scope"]) + '</p>' +
                     '<p class="small">' + link(family["guide"], "Guida metodologica") + '</p>' +
                     '<div class="commands">' + "".join(command_rows) + '</div></section>')
    gate_rows = []
    for g in atlas["maturity"]["gates"]:
        node = next(x for x in atlas["maturity"]["nodes"] if x["id"] == g)
        value = atlas["maturity"]["gate_states"][g]
        gate_rows.append('<article class="gate"><div><strong>' + _safe(g.replace("_", " ")) +
                         '</strong><p class="muted small">' + _safe(node["description"]) +
                         '</p></div><span class="state">' + _safe(value) + '</span></article>')
    methods = "".join('<li class="searchable" data-search="' +
                      _safe((p["id"] + " " + p["source"]).lower()) + '"><strong>' +
                      _safe(p["id"]) + '</strong> · ' + link(p["source"]) +
                      '</li>' for p in atlas["procedures"])
    counts = [(str(len(atlas["capabilities"])), "CLI dichiarate"),
              (str(len(atlas["procedures"])), "Metodi sorgente"),
              (str(len(atlas["artifacts"]["workflow_files"])), "Workflow"),
              (str(len(atlas["artifacts"]["documentation_files"])), "Documenti Markdown")]
    metrics = "".join('<div class="metric"><b>' + v + '</b><span>' + t + '</span></div>'
                      for v,t in counts)
    groups = [
        ("source_modules", "Moduli del motore"),
        ("release_tools", "Strumenti di qualificazione"),
        ("workflow_files", "Workflow CI"),
        ("test_files", "Sorgenti di test"),
        ("documentation_files", "Documentazione"),
        ("contracts", "Contratti")
    ]
    inventory = "".join('<details><summary>' + title + ' <span class="muted">(' +
                        str(len(atlas["artifacts"][key])) + ')</span></summary><ul class="inventory">' +
                        "".join('<li>' + link(x) + '</li>' for x in atlas["artifacts"][key]) +
                        '</ul></details>' for key,title in groups)
    share = "".join('<li><code>' + _safe(row["path"]) + '</code> — ' +
                    str(len(row["referenced_by"])) + ' comandi condividono lo stesso blob Git</li>'
                    for row in atlas["lineage"]["shared_git_origins"][:24])
    body = f"""<!DOCTYPE html>
<html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'none'; font-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; connect-src 'none'">
<title>CORA · Atlante integrato</title>
<style>
:root{{--paper:#f4eee5;--ink:#0b1f3a;--text:#243247;--muted:#5e6b7c;--gold:#c8892b;--line:#e0d7c9;--white:#fff;--teal:#2a9d8f}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--paper);color:var(--text);font:15px/1.6 system-ui,-apple-system,Segoe UI,sans-serif}}
a{{color:#175380;text-underline-offset:3px}}a:hover{{color:#0b1f3a}}a:focus-visible,input:focus-visible,summary:focus-visible{{outline:3px solid var(--gold);outline-offset:3px}}
.layout{{display:grid;grid-template-columns:240px minmax(0,1fr);min-height:100vh}}
aside{{background:var(--ink);color:#fff;padding:30px 22px;position:sticky;top:0;height:100vh;overflow:auto}}
aside a{{display:block;color:#d8e1ee;text-decoration:none;padding:9px 12px;border-radius:7px;font-size:14px}}aside a:hover{{background:#17365e;color:#fff}}
.logo{{font-weight:800;font-size:27px;letter-spacing:.1em;margin-bottom:6px}}
.sidebar-note{{color:#b9c8dd;font-size:12px;margin-bottom:26px}}
main{{max-width:1240px;width:100%;margin:0 auto;padding:34px 5vw 80px}}
.hero{{background:var(--ink);color:#fff;padding:44px;border-radius:16px}}
.kicker{{color:#e7b23c;letter-spacing:.15em;text-transform:uppercase;font-weight:700;font-size:12px}}
h1{{font-size:clamp(32px,4vw,52px);line-height:1.1;margin:12px 0}}h2{{font-size:27px;color:var(--ink);margin:44px 0 16px}}h3{{font-size:19px;color:var(--ink);margin:0 0 5px}}
.hero p{{max-width:780px;color:#dce5f1}}.status{{font-size:12px;background:#243e60;padding:6px 11px;border-radius:999px;display:inline-block}}
.metrics{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:20px 0}}
.metric{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:19px}}.metric b{{display:block;font-size:29px;color:var(--ink)}}.metric span{{font-size:13px;color:var(--muted)}}
.panel,.family{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:22px;margin:14px 0}}
.cols{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}}
.muted{{color:var(--muted)}}.small{{font-size:12px}}.family h3{{display:flex;justify-content:space-between;gap:16px;align-items:center}}
.count{{font-size:12px;font-weight:500;color:var(--muted)}}.command,.gate{{display:flex;justify-content:space-between;align-items:center;gap:15px;padding:11px 0;border-top:1px solid #eee7df}}
.command:first-child,.gate:first-child{{border-top:0}}code{{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;color:#12315c;font-size:13px}}
.references{{display:flex;flex-wrap:wrap;gap:8px;font-size:12px;align-items:center}}
.tag{{font-size:10px;padding:3px 7px;background:#f5eee4;color:#815d22;border-radius:99px}}
.state{{font-size:11px;color:#875a16;text-align:right;max-width:45%;overflow-wrap:anywhere}}
input{{background:#fff;border:1px solid #b7c2d1;padding:14px 18px;border-radius:10px;width:100%;font-size:16px}}
label{{font-weight:700;display:block;margin:10px 0}}.filter-tip{{font-size:12px;color:var(--muted)}}
.inventory{{columns:2;padding-left:23px}}.inventory li{{break-inside:avoid;font-size:12px;overflow-wrap:anywhere;margin-bottom:5px}}
details{{border-bottom:1px solid var(--line);padding:10px 0}}summary{{cursor:pointer;font-weight:600}}
.note{{border-left:3px solid var(--gold);padding:8px 18px;margin:18px 0;background:#fff}}
footer{{font-size:12px;color:var(--muted);margin-top:48px;overflow-wrap:anywhere}}
[hidden]{{display:none!important}}
@media(max-width:850px){{.layout{{display:block}}aside{{height:auto;position:static;padding:16px}}aside nav{{display:flex;flex-wrap:wrap}}aside a{{padding:5px 10px}}main{{padding:18px}}.metrics,.cols{{grid-template-columns:repeat(2,minmax(0,1fr))}}.hero{{padding:25px}}.inventory{{columns:1}}}}
@media(max-width:560px){{.metrics,.cols{{grid-template-columns:1fr}}.command,.gate{{align-items:flex-start;flex-direction:column}}.state{{max-width:none}}}}
</style></head>
<body><div class="layout">
<aside aria-label="Navigazione atlante"><div class="logo">CORA</div>
<div class="sidebar-note">Continuous Ontological<br>Repository Assurance</div>
<nav><a href="#overview">Panoramica</a><a href="#maturity">Reticolo DoD</a>
<a href="#catalog">Attività e comandi</a><a href="#methods">Metodi</a>
<a href="#inventory">Artefatti e CI</a><a href="#lineage">Lineage</a><a href="#reading">Uso responsabile</a></nav></aside>
<main><header class="hero" id="overview"><span class="kicker">ATLAS / {{_safe(atlas['identity']['distribution_version'])}}</span>
<h1>Una mappa per capire<br>e usare CORA.</h1>
<p>Superficie funzionale integrata, fonti originali, test dichiarati, obbligazioni di maturità e limiti verificabili.
Il coding agent implementa: CORA organizza quello che resta da dimostrare.</p>
<span class="status">Source candidate · non è certificazione o autorizzazione</span>
<p class="small">Commit esatto <code style="color:#fff">{{_safe(commit)}}</code></p></header>
<div class="metrics">{{metrics}}</div>
<section id="maturity"><h2>01 · Reticolo di maturità</h2>
<p>Sei condizioni necessarie. Un modello sorgente non può trasformare un controllo esterno in PASS.</p>
<div class="panel">{{''.join(gate_rows)}}<p class="small muted">Stato globale: {{_safe(atlas['maturity']['assessment']['status'])}} · Autorità: NONE · Il modello non attesta il passaggio dei test.</p></div>
<p class="small">{{link(DOD_PATH, "Contratto DoD originale e derivazione retrograda")}}</p></section>
<section id="catalog"><h2>02 · Attività e comandi</h2>
<p>Inventario esaustivo dei {{len(atlas['capabilities'])}} comandi dichiarati, non di {{len(atlas['capabilities'])}} comportamenti provati.
Ogni attività collega implementazione, test sorgente, metodo e perimetro di interazione.</p>
<label for="find">Cerca un comando, attività, modulo o metodo</label>
<input id="find" type="search" placeholder="Es. audit, replay, runtime, merge…" autocomplete="off">
<p class="filter-tip" id="visible-count" aria-live="polite">Visualizzazione completa.</p>
{{''.join(cards)}}</section>
<section id="methods"><h2>03 · Metodi canonici</h2>
<div class="panel"><p>Le 14 procedure conservano i loro owner software; l'atlante non costruisce un nuovo motore di inferenza.</p>
<ul>{{methods}}</ul></div></section>
<section id="inventory"><h2>04 · Inventario completo di sorgenti e verifiche</h2>
<div class="panel"><p>Indici Git del commit esatto: sorgenti, CI, test, contratti e documentazione. Presenza di file ≠ esecuzione.</p>{{inventory}}</div></section>
<section id="lineage"><h2>05 · Provenienza e dipendenze comuni</h2>
<div class="panel"><p><strong>{{atlas['lineage']['unique_git_origins']}}</strong> blob Git distinti nel mapping CLI/test.
<strong>0</strong> conferme indipendenti: due metodi che condividono un blob non costituiscono due osservazioni indipendenti.</p>
<details><summary>Mostra esempi di fonti condivise</summary><ul>{{share}}</ul></details></div></section>
<section id="reading"><h2>06 · Come usare CORA responsabilmente</h2>
<div class="cols"><div class="panel"><h3>Per l'utilizzatore</h3><p>Parti dalla famiglia di attività, leggi la guida e il contratto.
Esegui il comando in un checkout autorizzato; verifica il report al medesimo commit e richiedi test indipendenti.</p></div>
<div class="panel"><h3>Per l'agente AI</h3><p>Consuma il rapporto JSON e l'AI request separata.
Formula ipotesi falsificabili; non chiamare una descrizione o un hash prova comportamentale o approvazione.</p></div></div>
<p class="note">Non vengono eseguiti test target, Docker o provider AI per creare questa pagina. La release è un candidato alpha;
protezione host, adozione e validità real-world rimangono esterne.</p>
<p>{{link("docs/CONVERGENT_ASSURANCE.md","Metodo integrato")}} · {{link("AGENTS.md","Regole per agenti")}} · {{link("README.md","Presentazione del prodotto")}}</p></section>
<footer>{{_safe(HTML_MARKER)}} · source receipt {{_safe(atlas['source_receipt_digest'])}} · atlas digest {{_safe(atlas['atlas_digest'])}}
<br>HTML autocontenuto, filtri locali. I link alle fonti Git richiedono accesso autorizzato al repository.</footer>
</main></div>
<script>
(function(){{
  "use strict";
  const box=document.getElementById('find');
  const rows=Array.from(document.querySelectorAll('.searchable'));
  const groups=Array.from(document.querySelectorAll('.family'));
  const count=document.getElementById('visible-count');
  function update(){{
    const value=box.value.trim().toLocaleLowerCase();
    let shown=0;
    rows.forEach(function(row){{
      const ok=!value || (row.getAttribute('data-search')||'').includes(value);
      row.hidden=!ok;
      if(ok && row.classList.contains('command')) shown++;
    }});
    groups.forEach(function(group){{
      group.hidden=value && !Array.from(group.querySelectorAll('.command')).some(function(x){{return !x.hidden;}});
    }});
    count.textContent=value ? String(shown)+' comandi corrispondenti.' : 'Visualizzazione completa.';
  }}
  box.addEventListener('input',update);
}})();
</script></body></html>
"""
    # Fail closed on accidental unescaped Python interpolation placeholders.
    if "{{" in body or "}}" in body:
        raise ValueError("unrendered atlas template placeholders")
    return body


def verify_atlas(repo: Path, unified: dict, *, data: dict | None = None,
                 page: str | None = None) -> bool:
    """Independent re-derivation from original Git, not a self-signed digest."""
    if data is None and page is None:
        raise ValueError("one original artifact is required to verify")
    expected = build_atlas(repo, unified)
    if data is not None and data != expected:
        raise ValueError("atlas JSON differs from original Git source")
    if page is not None and page != render_html(expected):
        raise ValueError("atlas HTML differs from original Git source")
    return True
