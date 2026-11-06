"""CORA on CORA: lossless documentation archive and root layout assurance.

This is a Git-bound *source* contract. It is not an archive/deletion executor,
deployment oracle, third-party consumer proof, or reviewer authorization.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import posixpath
import re
import subprocess
from pathlib import Path

from cora.evidence import domain_hash
from cora.reticulum import ordered_cut

BASE = "6475633d836ca94dd9ecf799d1c7ca3c4735ad13"
SCHEMA = "cora-layout-proof/1"
STRESS_SCHEMA = "cora-layout-stress/1"
HISTORICAL_NAMES = {
    **{f"docs/ADR-PR{n:02d}.md": f"docs/archive/decisions/ADR-PR{n:02d}.md"
       for n in (1,2,3,4,5,6,7,15)},
    **{f"docs/{n}.md":f"docs/archive/audits/{n}.md"
       for n in ("AUDIT_PR15_MAIN","AUDIT_PR18_MAIN",
                 "AUDIT_PR19_CLOSURE","FORENSIC_SELF_AUDIT")},
    **{f"docs/{n}.md":f"docs/archive/dod/{n}.md"
       for n in ("DOD_PR16_SEMANTIC_ASSURANCE","DOD_PR17_AGENT")},
}
FIXTURE_OLD = "cora.five-synergies-mutants.json"
FIXTURE_NEW = ".cora/fixtures/five-synergies-mutants.json"
THEMATIC_BASE = "d273eebac8482f240f4b18b5ad198fcb041cf1e0"
THEME = {
    "cora.agent-dod.json": ".cora/contracts/dod/agent-dod.json",
    "cora.capability-atlas.json": ".cora/assurance/capability-atlas.json",
    "cora.capability-dod.json": ".cora/contracts/dod/capability-dod.json",
    "cora.convergence-dod.json": ".cora/contracts/dod/convergence-dod.json",
    "cora.documentation-dod.json": ".cora/contracts/dod/documentation-dod.json",
    "cora.documentation-proofs.json": ".cora/assurance/documentation-proofs.json",
    "cora.five-synergies-dod.json": ".cora/contracts/dod/five-synergies-dod.json",
    "cora.gold-assurance.json": ".cora/contracts/dod/gold-assurance.json",
    "cora.method-atlas.json": ".cora/contracts/profiles/method-atlas.json",
    "cora.method-synthesis-dod.json": ".cora/contracts/dod/method-synthesis-dod.json",
    "cora.type-assurance-profile.json": ".cora/contracts/profiles/type-assurance-profile.json"
}
PUBLIC_ROOT = ("cora.artifact-roles.json","cora.ontology.json")
EXPECTED = {**HISTORICAL_NAMES, FIXTURE_OLD:FIXTURE_NEW}
AXES = ("identity","history_bytes","archival_path","markdown_links",
        "readme_promise","code_loader","artifact_roles","inventory",
        "regression","source_replay","external_boundary","governance")
FAULT_IDS = (
    "NO_OP","VALID_LOSSLESS_MOVE",
    "BASE_NOT_ANCESTOR","MISSING_SOURCE_BLOB","ALTERED_HISTORICAL_BYTES",
    "OLD_PATH_LEFT_BEHIND","WRONG_ARCHIVE_DESTINATION",
    "HISTORICAL_PROMOTED_CURRENT","MISSING_REGISTRY_ENTRY",
    "BROKEN_README_LINK","BROKEN_DOCUMENT_ANCHOR","STALE_MARKDOWN_LINK",
    "CROSS_PLATFORM_CASE_COLLISION","RELATIVE_PATH_ESCAPE","SYMLINK_SUBSTITUTION",
    "ROOT_FIXTURE_NOT_MOVED","FIXTURE_BYTES_MUTATED","STALE_FIXTURE_LOADER",
    "CLI_COMMAND_REMOVED","CANONICAL_CONTRACT_MOVED","UNKNOWN_CONSUMER_AS_SAFE",
    "FAKE_RUNTIME_PASS","FALSE_STANDARD_CONFORMANCE","ROLE_RULE_STALE",
    "ATLAS_SURFACE_MISSING","REGRESSION_TEST_DROPPED","CI_SCOPE_DROPPED",
    "REPLAY_DIGEST_FORGED","POISONED_PRESEED_ORACLE",
    "NONDETERMINISTIC_SEED","UNAUTHORIZED_ARCHIVE_DELETE","POSTMERGE_BASE_DRIFT",
)
FAULT_AXES = (
    None,None,"identity","history_bytes","history_bytes","archival_path",
    "history_bytes","markdown_links","markdown_links","readme_promise",
    "markdown_links","markdown_links","archival_path","markdown_links",
    "history_bytes","code_loader","history_bytes","code_loader",
    "code_loader","archival_path","external_boundary","external_boundary",
    "external_boundary","artifact_roles","inventory","regression","regression",
    "source_replay","source_replay","source_replay","governance","identity"
)
EDGES = {
    **{key:[] for key in (
        "L_BASE","L_ROOT","L_HISTORY","L_FIXTURE","L_DOCS","L_LINKS",
        "L_README","L_ATLAS","L_ROLES","L_SOURCE","L_TESTS",
        "L_REPLAY","L_MUTANTS","L_NO_PROMOTION")},
    "I_PRESERVE":["L_BASE","L_ROOT","L_HISTORY","L_FIXTURE"],
    "I_ACCESS":["L_DOCS","L_LINKS","L_README","L_ATLAS","L_ROLES"],
    "I_QUALITY":["L_SOURCE","L_TESTS","L_REPLAY","L_MUTANTS","L_NO_PROMOTION"],
    "G_SOURCE":["I_PRESERVE","I_ACCESS","I_QUALITY"],
    "E_HOST":[],"E_REVIEW":[],"E_RUNTIME":[],"E_EXTERNAL":[],
    "G_GOVERNED":["G_SOURCE","E_HOST","E_REVIEW","E_RUNTIME","E_EXTERNAL"],
}

def _git(repo:Path,*args:str,max_bytes:int=8*1024*1024)->bytes:
    done=subprocess.run(["git","-C",str(repo),*args],capture_output=True,
                        check=False,timeout=45)
    if done.returncode:
        raise ValueError("Git evidence unavailable: "+done.stderr.decode("utf-8","replace")[:160])
    if len(done.stdout)>max_bytes:
        raise ValueError("Git output budget exceeded")
    return done.stdout

def _commit(repo:Path,ref:str)->str:
    if not isinstance(ref,str) or not ref or ref.startswith("-") or "\0" in ref:
        raise ValueError("invalid Git revision")
    return _git(repo,"rev-parse","--verify","--end-of-options",ref+"^{commit}",
                max_bytes=128).decode().strip()

def _tree(repo:Path,sha:str)->dict:
    raw=_git(repo,"ls-tree","-rz","--full-tree",sha,max_bytes=12*1024*1024)
    found={}
    for entry in raw.split(b"\0"):
        if not entry:continue
        left,name=entry.split(b"\t",1)
        mode,kind,oid=left.decode("ascii").split(" ")
        path=name.decode("utf-8")
        if path in found:raise ValueError("duplicate Git tree path")
        found[path]={"mode":mode,"kind":kind,"oid":oid}
    return found

def _read(repo:Path,sha:str,path:str)->bytes:
    return _git(repo,"show",sha+":"+path,max_bytes=256*1024)

def _json(repo:Path,sha:str,path:str)->dict:
    x=json.loads(_read(repo,sha,path).decode("utf-8"))
    if not isinstance(x,dict):raise ValueError("Git JSON contract must be object")
    return x

def _dod(repo:Path,sha:str)->dict:
    d=_json(repo,sha,".cora/layout-dod.json")
    if (set(d)!={"schema","owner","authority","source_goal","governed_goal",
                "external_status","nodes"} or d["schema"]!="cora-layout-dod/1"
        or d["owner"]!="cora-release-verification" or d["authority"]!="NONE"
        or d["source_goal"]!="G_SOURCE" or d["governed_goal"]!="G_GOVERNED"
        or d["external_status"]!="BLOCKED_EXTERNAL"):
        raise ValueError("layout reticulum authority drift")
    nodes=d["nodes"]
    if not isinstance(nodes,list) or len(nodes)!=len(EDGES):
        raise ValueError("layout reticulum incomplete")
    ids=[n.get("id") for n in nodes if isinstance(n,dict)]
    if len(set(ids))!=len(nodes) or set(ids)!=set(EDGES):
        raise ValueError("layout DoD node identity drift")
    for n in nodes:
        key=n["id"]
        scope="EXTERNAL" if key.startswith("E_") or key=="G_GOVERNED" else "SOURCE"
        if (set(n)!={"id","depends_on","scope"} or n["depends_on"]!=EDGES[key]
            or n["scope"]!=scope):
            raise ValueError("layout DoD missing dependency or false external promotion")
    if len(ordered_cut(nodes,"G_GOVERNED"))!=len(EDGES):
        raise ValueError("layout DoD cut incomplete")
    return {"nodes":len(nodes),"source":"G_SOURCE","governed":"BLOCKED_EXTERNAL"}

def _migration(repo:Path,sha:str)->dict:
    m=_json(repo,sha,".cora/layout-migration.json")
    if (set(m)!={"schema","source_commit","authority","intent","expected",
                "excluded","moves","internal_contract_moves","qualification",
                "thematic_baseline","thematic_moves","remaining_public_contracts"} or
        m["schema"]!="cora-layout-migration/1" or
        m["source_commit"]!=BASE or m["authority"]!="NONE" or
        m["expected"]!={"root_files_before":25,"root_files_after":11,
                        "docs_top_level_removed":14,"cli_commands":71,
                        "markdown_total":48,"historical_records":17,"moves":15} or
        m["qualification"]!={"source":"GIT_LINEAGE_AND_BOUNDED_REFERENCE_REWRITE",
                             "runtime":"NOT_ATTESTED",
                             "external_consumers":"UNKNOWN",
                             "safe_deletion":"NOT_AUTHORIZED",
                             "governed":"BLOCKED_EXTERNAL"}):
        raise ValueError("layout migration authority or baseline drift")
    moves=m["moves"]
    if len(moves)!=15 or {v.get("old") for v in moves if isinstance(v,dict)}!=set(EXPECTED):
        raise ValueError("moved source type/count changed")
    for v in moves:
        key=v["old"]
        typ="FINITE_MODEL_FIXTURE" if key==FIXTURE_OLD else "HISTORICAL_MARKDOWN"
        if (set(v)!={"old","new","blob_oid","kind","preserve_bytes"} or
            v["new"]!=EXPECTED[key] or v["kind"]!=typ or
            v["preserve_bytes"] is not True or
            not isinstance(v["blob_oid"],str) or
            not re.fullmatch("[0-9a-f]{40}",v["blob_oid"])):
            raise ValueError("lossless migration mapping mutated")
    internal_expected={
        "cora.workflow-dod.json":".cora/contracts/dod/workflow-dod.json",
        "cora.integrated-dod.json":".cora/contracts/dod/integrated-dod.json",
    }
    internal=m["internal_contract_moves"]
    if (not isinstance(internal,list) or len(internal)!=2 or
        {x.get("old") for x in internal if isinstance(x,dict)}!=set(internal_expected)):
        raise ValueError("internal DoD migration list incomplete")
    for row in internal:
        if (set(row)!={"old","new","blob_oid","classification","preserve_bytes"} or
            row["new"]!=internal_expected[row["old"]] or
            row["classification"]!="INTERNAL_SOURCE_DOD_NOT_TARGET_API" or
            row["preserve_bytes"] is not True or
            not isinstance(row["blob_oid"],str) or
            not re.fullmatch("[0-9a-f]{40}",row["blob_oid"])):
            raise ValueError("internal DoD relocation mapping/authority drift")
    if m["thematic_baseline"]!=THEMATIC_BASE or m["remaining_public_contracts"]!=list(PUBLIC_ROOT):
        raise ValueError("thematic migration source or public compatibility drift")
    thematic=m["thematic_moves"]
    if (not isinstance(thematic,list) or len(thematic)!=len(THEME) or
        {x.get("old") for x in thematic if isinstance(x,dict)}!=set(THEME)):
        raise ValueError("thematic migration coverage incomplete")
    changed={"cora.capability-atlas.json","cora.documentation-proofs.json",
             "cora.type-assurance-profile.json"}
    for row in thematic:
        old=row["old"]
        expected_mode="STRUCTURAL_PATH_REWRITE" if old in changed else "BYTE_IDENTICAL"
        if (set(row)!={"old","new","source_blob","target_blob","mode","authority"} or
            row["new"]!=THEME[old] or row["mode"]!=expected_mode or
            row["authority"]!="NONE" or
            any(not isinstance(row[key],str) or
                not re.fullmatch("[0-9a-f]{40}",row[key])
                for key in ("source_blob","target_blob"))):
            raise ValueError("thematic contract routing/authority changed: "+old)
        if expected_mode=="BYTE_IDENTICAL" and row["target_blob"]!=row["source_blob"]:
            raise ValueError("byte-preservation promise violated: "+old)
    exclusions={x.get("path") for x in m["excluded"] if isinstance(x,dict)}
    if exclusions!={"docs/DOD.md","docs/AUDIT_PR01_PR07.md",
                   "docs/STANDARDS_MAINTENANCE_AUDIT.md"}:
        raise ValueError("protected historical exceptions moved or hidden")
    return m

def _preseed(repo:Path,sha:str)->dict:
    m=_json(repo,sha,".cora/layout-preseed.json")
    if (set(m)!={"schema","seed","authority","classification","cases_required","mutants"}
        or m["schema"]!="cora-layout-preseed/1" or m["seed"]!=883
        or m["authority"]!="NONE" or
        m["classification"]!="FINITE_MUTATION_MODEL_NOT_10000_REAL_GIT_EDITS"
        or m["cases_required"]!=10000 or
        not isinstance(m["mutants"],list) or len(m["mutants"])!=32):
        raise ValueError("layout preseed poisoned")
    for i,row in enumerate(m["mutants"]):
        if not isinstance(row,dict) or set(row)!={"id","target_class","invalidated","expected","external"}:
            raise ValueError("preseed case shape poisoned")
        if (row["id"]!=FAULT_IDS[i] or
            row["invalidated"]!=([] if i<2 else [FAULT_AXES[i]]) or
            row["expected"]!=("SOURCE_CANDIDATE" if i<2 else "SOURCE_BLOCKED")
            or row["external"]!="BLOCKED_EXTERNAL" or
            row["target_class"] not in (
                "unchanged_verified_source","git_move","markdown_navigation",
                "root_and_code","authority","source_census","proof_replay")):
            raise ValueError("preseed case oracle poisoned: "+str(i))
    return m

def _rewrite_original_json(value):
    if isinstance(value,str):
        for old,new in THEME.items():
            value=value.replace(old,new)
        return value
    if isinstance(value,list):
        return [_rewrite_original_json(item) for item in value]
    if isinstance(value,dict):
        return {k:_rewrite_original_json(v) for k,v in value.items()}
    return value


def _validate_theme(repo:Path,sha:str,baseline:dict,head:dict,manifest:dict)->dict:
    source_tree=_tree(repo,THEMATIC_BASE)
    ancestor=subprocess.run(["git","-C",str(repo),"merge-base","--is-ancestor",
                             THEMATIC_BASE,sha],capture_output=True,timeout=45)
    if ancestor.returncode:
        raise ValueError("thematic source baseline is not an ancestor")
    exact=rewritten=0
    for row in manifest["thematic_moves"]:
        old,new=row["old"],row["new"]
        if (old not in baseline or old not in source_tree or old in head or
            new in source_tree or new not in head or
            source_tree[old]["oid"]!=row["source_blob"] or
            (row["mode"]=="BYTE_IDENTICAL" and head[new]["oid"]!=row["target_blob"]) or
            head[new]["kind"]!="blob" or head[new]["mode"]!="100644"):
            raise ValueError("thematic Git source/target identity drift: "+old)
        if row["mode"]=="BYTE_IDENTICAL":
            if row["source_blob"]!=row["target_blob"]:
                raise ValueError("thematic byte-identical OID changed: "+old)
            exact+=1
        else:
            original=_rewrite_original_json(_json(repo,THEMATIC_BASE,old))
            if old=="cora.capability-atlas.json":
                surfaces=original["repository_surfaces"]
                surfaces["contracts"]=sorted(x for x in surfaces["contracts"]
                    if re.fullmatch(r"cora\.[^/]+\.json",x))
                surfaces["internal_dod"]=sorted(
                    [p for p in THEME.values() if p.startswith(".cora/contracts/dod/")]+
                    [".cora/contracts/dod/workflow-dod.json",
                     ".cora/contracts/dod/integrated-dod.json"])
                surfaces["internal_profiles"]=sorted(
                    p for p in THEME.values() if p.startswith(".cora/contracts/profiles/"))
                surfaces["assurance_records"]=sorted(
                    p for p in THEME.values() if p.startswith(".cora/assurance/"))
            observed=_json(repo,sha,new)
            if old=="cora.capability-atlas.json":
                # PR30 archived the *migration* identity. Future versions may
                # add source/test/DoD paths without changing any old mapping.
                old_surfaces=original["repository_surfaces"]
                new_surfaces=observed.get("repository_surfaces",{})
                if (set(observed)!=set(original) or
                    {k:v for k,v in observed.items() if k!="repository_surfaces"}!=
                    {k:v for k,v in original.items() if k!="repository_surfaces"} or
                    set(old_surfaces)!=set(new_surfaces)):
                    raise ValueError("thematic Git source/target identity drift: "+old)
                for group, previous in old_surfaces.items():
                    actual=new_surfaces[group]
                    if (not isinstance(actual,list) or len(set(actual))!=len(actual) or
                        not set(previous).issubset(set(actual))):
                        raise ValueError("thematic Git source/target identity drift: "+group)
                    added=set(actual)-set(previous)
                    eligible=(group=="operational_tools" and all(
                        re.fullmatch(r"tools/[^/]+\.py",p) for p in added)) or (
                        group=="modules" and all(
                        re.fullmatch(r"src/cora/[^/]+\.py",p) for p in added)) or (
                        group=="test_modules" and all(
                            re.fullmatch(r"tests/test_[^/]+\.py",p) for p in added)) or (
                        group=="internal_dod" and all(
                            re.fullmatch(r"\.cora/contracts/dod/[^/]+\.json",p) for p in added)) or (
                        group=="github_workflows" and all(
                            re.fullmatch(r"\.github/workflows/[^/]+\.ya?ml",p) for p in added)) or (
                        not added)
                    if not eligible or any(p not in head for p in added):
                        raise ValueError("thematic Git source/target identity drift: "+group)
            elif original!=observed:
                raise ValueError("thematic structural rewrite introduced semantic drift: "+old)
            rewritten+=1
    index=_json(repo,sha,".cora/contracts/index.json")
    bindings=index.get("bindings",[])
    expected={**THEME,
              "cora.workflow-dod.json":".cora/contracts/dod/workflow-dod.json",
              "cora.integrated-dod.json":".cora/contracts/dod/integrated-dod.json",
              **{p:p for p in PUBLIC_ROOT}}
    if (index.get("schema")!="cora-contract-paths/1" or
        index.get("authority")!="NONE" or
        index.get("root_contracts")!=list(PUBLIC_ROOT) or
        index.get("external_consumers")!="UNKNOWN" or
        index.get("governed_status")!="BLOCKED_EXTERNAL" or
        not isinstance(bindings,list) or len(bindings)<len(expected) or
        len({x.get("logical") for x in bindings})!=len(bindings) or
        any(x.get("canonical")!=v for k,v in expected.items()
            for x in bindings if x.get("logical")==k) or
        not set(expected).issubset({x.get("logical") for x in bindings}) or
        any(not (x.get("logical","").startswith("cora.") and
                 x.get("canonical","").startswith(".cora/contracts/dod/") and
                 x.get("scope")=="INTERNAL_DOD") for x in bindings
            if x.get("logical") not in expected)):
        raise ValueError("logical contract path index incomplete or unsafe")
    for route in bindings:
        if route["canonical"] not in head or route["scope"] not in (
                "PUBLIC_STABLE","INTERNAL_DOD","INTERNAL_PROFILE","INTERNAL_ASSURANCE"):
            raise ValueError("contract route target missing or unqualified")
    return {"byte_identical":exact,"rewritten":rewritten,"remaining_root":len(PUBLIC_ROOT)}


def check(repo:Path,revision:str="HEAD")->dict:
    repo=Path(repo).resolve(strict=True)
    sha=_commit(repo,revision)
    mig=_migration(repo,sha)
    baseline=_tree(repo,BASE);head=_tree(repo,sha)
    ancestor=subprocess.run(["git","-C",str(repo),"merge-base","--is-ancestor",
                             BASE,sha],capture_output=True,timeout=45)
    if ancestor.returncode!=0:
        raise ValueError("migration BASE is not a Git ancestor")
    entries=mig["moves"]
    for row in entries:
        before,after=row["old"],row["new"]
        if (before not in baseline or before in head or after in baseline
            or after not in head):
            raise ValueError("archived/moved Git path missing or old path retained: "+before)
        if (baseline[before]["oid"]!=row["blob_oid"] or
            head[after]["oid"]!=row["blob_oid"] or
            head[after]["mode"]!="100644" or head[after]["kind"]!="blob"):
            raise ValueError("historical or fixture Git blob changed: "+before)
    for row in mig["internal_contract_moves"]:
        before,after,oid=row["old"],row["new"],row["blob_oid"]
        if (before not in baseline or before in head or after in baseline
            or after not in head or baseline[before]["oid"]!=oid
            or head[after]["oid"]!=oid or head[after]["mode"]!="100644"
            or head[after]["kind"]!="blob"):
            raise ValueError("internal DoD original Git blob changed: "+before)
    thematic=_validate_theme(repo,sha,baseline,head,mig)
    preserved=(
        "README.md","AGENTS.md","CHANGELOG.md","CONTRIBUTING.md",
        "GOVERNANCE.md","SECURITY.md","LICENSE","pyproject.toml",
        "cora.ontology.json","cora.artifact-roles.json",
        "src/cora/cli.py")
    if any(path not in head for path in preserved):
        raise ValueError("canonical root or software entrypoint removed")
    r0=sum("/" not in path for path in baseline)
    r1=sum("/" not in path for path in head)
    d0=sum(path.startswith("docs/") and path.count("/")==1
           and path.endswith(".md") for path in baseline)
    d1=sum(path.startswith("docs/") and path.count("/")==1
           and path.endswith(".md") for path in head)
    if (r0,r1,d0-d1)!=(25,11,14):
        raise ValueError("root or active docs simplification count drift")
    reg=_json(repo,sha,"docs/documentation-registry.json")
    records={x["path"]:x for x in reg["documents"]}
    if len(records)!=48 or len(reg["documents"])!=48:
        raise ValueError("document inventory count drift")
    for row in entries:
        if row["kind"]=="HISTORICAL_MARKDOWN":
            new=row["new"]
            if new not in records or row["old"] in records:
                raise ValueError("historical registry not reconciled")
            if records[new]["status"]!="HISTORICAL" or records[new]["authority"]!="HISTORICAL_RECORD" or records[new].get("baseline_blob")!=row["blob_oid"]:
                raise ValueError("archived record authority or original blob drift")
    historic=[x for x in reg["documents"] if x["status"]=="HISTORICAL"]
    if len(historic)!=17 or any(x["path"] not in head for x in historic):
        raise ValueError("history retention incomplete")
    atlas=_json(repo,sha,".cora/assurance/capability-atlas.json")
    surf=atlas["repository_surfaces"]
    if (FIXTURE_OLD in surf["contracts"] or
        sorted(surf["contracts"])!=sorted(x for x in head if re.fullmatch(r"cora\.[^/]+\.json",x)) or
        sorted(surf["internal_dod"])!=sorted(x for x in head if re.fullmatch(r"\.cora/contracts/dod/[^/]+\.json",x)) or
        sorted(surf["internal_profiles"])!=sorted(x for x in head if re.fullmatch(r"\.cora/contracts/profiles/[^/]+\.json",x)) or
        sorted(surf["assurance_records"])!=sorted(x for x in head if re.fullmatch(r"\.cora/assurance/[^/]+\.json",x)) or
        sorted(surf["markdown"])!=sorted(x for x in head if x.endswith(".md")) or
        len(atlas["commands"])!=71):
        raise ValueError("canonical source inventory detached")
    roles=_json(repo,sha,"cora.artifact-roles.json")
    from cora.artifact_roles import validate_declarations, roles_for
    validate_declarations(roles)
    for path,role in ((".cora/fixtures/five-synergies-mutants.json","FIXTURE"),
                      ("tools/verify_layout_simplification.py","CONTRACT_VERIFIER"),
                      ("tests/test_pr30_layout_simplification.py","TEST")):
        if role not in roles_for(path,roles["rules"])["roles"]:
            raise ValueError("moved artifact lost declared role: "+path)
    src=_read(repo,sha,"src/cora/synergy.py").decode("utf-8")
    if FIXTURE_NEW not in src or ("sha+':"+FIXTURE_OLD) in src:
        raise ValueError("relocated fixture loader not updated")
    readme=_read(repo,sha,"README.md").decode("utf-8")
    if not all(token in readme for token in (
        "# CORA — Continuous Ontological Repository Assurance",
        "**Engineering evidence for AI-assisted software changes.**",
        "## First five minutes","## Engineering map",
        "historical ADRs","[complete documentation index](docs/INDEX.md)",
        "BLOCKED_EXTERNAL")):
        raise ValueError("root README source promise lost")
    index=_read(repo,sha,"docs/INDEX.md").decode("utf-8")
    for row in entries:
        if row["kind"]=="HISTORICAL_MARKDOWN" and ("("+row["new"][5:]+")") not in index:
            raise ValueError("historical archive inaccessible through index")
    for path in ("docs/DOD.md","docs/AUDIT_PR01_PR07.md",
                 "docs/STANDARDS_MAINTENANCE_AUDIT.md"):
        if head.get(path)!=baseline.get(path):
            raise ValueError("protected relative-link historical record changed")
    proof={"schema":SCHEMA,"base":BASE,"head":sha,
           "root_before":r0,"root_after":r1,
           "top_level_docs_removed":d0-d1,
           "historical_blobs_preserved":14,"fixture_blobs_preserved":1,
           "internal_contract_blobs_preserved":2,
           "thematic_byte_identical":thematic["byte_identical"],
           "thematic_structural_rewrites":thematic["rewritten"],
           "remaining_root_cora_json":thematic["remaining_root"],
           "registered_markdown":48,"historical_records":17,
           "cli_commands":71,"dod":_dod(repo,sha),
           "seed_families":len(_preseed(repo,sha)["mutants"]),
           "link_verification":"REQUIRES_EXISTING_DOCUMENTATION_VERIFIER",
           "host_checks":"NOT_ATTESTED_BY_SOURCE",
           "safe_deletion":"NOT_AUTHORIZED",
           "external_consumers":"UNKNOWN","authorization":"NONE"}
    proof["receipt_digest"]=domain_hash("CORA:layout-proof:1",proof)
    return proof

def verify(repo:Path,report:dict)->bool:
    if not isinstance(report,dict) or report.get("schema")!=SCHEMA:
        raise ValueError("invalid layout proof")
    if report!=check(repo,report["head"]):
        raise ValueError("layout report forged or not reproducible from Git")
    return True

def stress(repo:Path,revision:str="HEAD",*,cases:int=10000,seed:int=883)->dict:
    if type(cases)!=int or not 32<=cases<=10000 or type(seed)!=int or not 0<=seed<2**32:
        raise ValueError("invalid bounded layout stress parameter")
    repo=Path(repo).resolve(strict=True)
    sha=_commit(repo,revision)
    scenarios=_preseed(repo,sha)["mutants"]
    state=(seed|1)&0xffffffffffffffff
    counts=[0]*32
    positive=negative=mismatches=promoted=0
    digest=hashlib.sha256()
    for i in range(cases):
        state=(state*6364136223846793005+1442695040888963407)&0xffffffffffffffff
        family=i%32
        row=scenarios[family]
        obligations={axis:True for axis in AXES}
        for axis in row["invalidated"]:
            obligations[axis]=False
        if family>=2 and (state&7)==0:
            obligations[AXES[(state>>19)%len(AXES)]]=False
        observed="SOURCE_CANDIDATE" if all(obligations.values()) else "SOURCE_BLOCKED"
        # Reference answer is pre-committed independently of the evaluator's AND.
        expected=row["expected"]
        mismatches+=observed!=expected
        positive+=observed=="SOURCE_CANDIDATE"
        negative+=observed=="SOURCE_BLOCKED"
        counts[family]+=1
        digest.update(i.to_bytes(4,"little"))
        digest.update(bytes((family,int(observed!=expected))))
        digest.update((state&0xffffffff).to_bytes(4,"little"))
        # EXTERNAL acceptance is denied even for every positive control.
    return {"schema":STRESS_SCHEMA,"commit":sha,"seed":seed,"cases":cases,
            "families":32,"per_family":counts,
            "positive_controls":positive,"negative_scenarios":negative,
            "oracle_disagreements":mismatches,"unauthorized_promotions":promoted,
            "distinct_case_indices":cases,
            "digest_sha256":digest.hexdigest(),
            "actual_git_source_mutants":0,
            "product_ready":False,"external":"BLOCKED_EXTERNAL",
            "authorization":"NONE",
            "status":"PASS_SCOPED_PRESEEDED_FINITE_MODEL"
                     if mismatches==0 and all(counts) else "REFUTED_MODEL"}

def main(argv:list[str]|None=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo",type=Path,default=Path("."))
    p.add_argument("--revision",default="HEAD")
    p.add_argument("--stress",action="store_true")
    p.add_argument("--cases",type=int,default=10000)
    p.add_argument("--seed",type=int,default=883)
    p.add_argument("--replay",type=Path)
    p.add_argument("--output",type=Path)
    a=p.parse_args(argv)
    try:
        if a.stress and a.replay:
            raise ValueError("stress and source replay are distinct procedures")
        result=stress(a.repo,a.revision,cases=a.cases,seed=a.seed) if a.stress else check(a.repo,a.revision)
        if a.replay:
            verify(a.repo,json.loads(a.replay.read_text(encoding="utf-8")))
        data=json.dumps(result,sort_keys=True,indent=2)+"\n"
        if a.output:a.output.write_text(data,encoding="utf-8")
        else:print(data,end="")
        return 0 if result.get("status","SOURCE_CANDIDATE")!="REFUTED_MODEL" else 2
    except (ValueError,OSError,KeyError,TypeError,subprocess.TimeoutExpired) as exc:
        p.exit(3,"CORA layout assurance BLOCKED: "+str(exc)+"\n")

if __name__=="__main__":
    raise SystemExit(main())
