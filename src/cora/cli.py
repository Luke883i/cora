"""The single supported CORA console entrypoint."""
from __future__ import annotations
import argparse
import json
import sys
import subprocess
from pathlib import Path
from . import __version__
from .maturity_atlas import build_atlas, render_html, verify_atlas
from .audit import audit, read_declarations
from .mutations import stress
from .mutation_evidence import stress_evidence
from .evidence import validate_ledger
from .git_snapshot import snapshot
from .graph import graph_from_commit, explain_path, verify_graph_against_git
from .graph_stress import stress_graph
from .adapters import adapter_audit, verify_adapter_report
from .adapter_stress import stress_adapters
from .closure import closure, verify_certificate
from .closure_stress import stress_closure
from .transform import plan_rename_docs, apply_rename_docs
from .transform_stress import stress_transform
from .guard import install_guard
from .guard_runtime import verify as verify_local_guard
from .file_lab import examine_file, verify_lab, ai_prompt, record_human_decision
from .file_lab_stress import stress_file_lab
from .artifact_roles import artifact_audit, verify_artifact_report
from .artifact_saturation import saturate
from .selection import select_file, verify_selection
from .selection_stress import stress_selection
from .archaeology import mine_history, verify_history
from .holistic import holistic_audit, verify_holistic
from .group_hypotheses import group_ai_request, annotate_groups
from .archaeology_stress import stress_archaeology
from .debt import debt_scan, verify_debt, compare_debt
from .debt_stress import stress_debt
from .process_suite import process_catalog, run_suite, verify_suite, PROCESSES
from .one_run import run_one, verify_one, render_one_html
from .portable_assurance import run_portable, verify_portable, render_portable_html, parse_upstream_paths
from .integrated_run import run_integrated, verify_integrated as verify_integrated_one_run
from .integrated_html import render_integrated_html
from .chat_bundle import append_chat_iteration, verify_chat_bundle, load_chat_step
from .continuous import evaluate as development_gate, verify_gate, agent_check
from .continuous_stress import stress_continuous
from .archive_intake import inspect_zip, verify_intake
from .runtime_observation import observe_runtime
from .observation_fusion import fuse_evidence, verify_fusion
from .semantic_lattice import lattice_from_evidence, verify_lattice
from .agent_assurance import load_contract, backward_plan, assess_claims, verify_assessment, STAGES
from .agent_saturation import saturate_agent_dod
from .gold_assurance import load_gold_contract, retrograde_gold, pilot_sources, contextual_gold
from .gold_mutations import physical_mutants
from .gold_effects import audit_workflow, reconcile_effect_claim
from .workflow_rationalization import audit_workflows, verify_workflows
from .method_synthesis import synthesize, verify_synthesis, analyst_request
from .integrated_service import integrated_case, verify_integrated, ai_request as integrated_ai_request, stress_integrated
from .synergy import unified_assurance, verify_unified_assurance, stress_five_synergies
from .gold_saturation import gold_saturation
from .gold_assurance import load_convergence_contract, convergent_plan
from .gold_saturation import saturate_convergence
from .continuous import evaluate_contextual, verify_contextual_gate
import zipfile
import shlex


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog='cora', description='Scoped, read-only repository evidence')
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('version')
    dp = sub.add_parser('dod-plan', help='Reverse-derive AI agent obligations, not execution or approval')
    dp.add_argument('--contract', type=Path, default=Path('.cora/contracts/dod/agent-dod.json'))
    dp.add_argument('--stage', choices=tuple(STAGES), default='premerge')
    dp.add_argument('--goal', choices=('G_SOURCE_AGENT', 'G_GOVERNED_AGENT'))
    dp.add_argument('--output', type=Path)
    da = sub.add_parser('dod-assess', help='Reconcile untrusted local agent claims without authorization')
    da.add_argument('observations', type=Path)
    da.add_argument('--contract', type=Path, default=Path('.cora/contracts/dod/agent-dod.json'))
    da.add_argument('--stage', choices=tuple(STAGES), default='premerge')
    da.add_argument('--goal', choices=('G_SOURCE_AGENT', 'G_GOVERNED_AGENT'))
    da.add_argument('--output', type=Path)
    dv = sub.add_parser('verify-dod', help='Replay a DoD assessment against original source and claims')
    dv.add_argument('report', type=Path)
    dv.add_argument('--observations', required=True, type=Path)
    dv.add_argument('--contract', type=Path, default=Path('.cora/contracts/dod/agent-dod.json'))
    dv.add_argument('--output', type=Path)
    ds = sub.add_parser('stress-agent-dod', help='10M preseeded finite semantic model tests; not 10M source mutants')
    ds.add_argument('--contract', type=Path, default=Path('.cora/contracts/dod/agent-dod.json'))
    ds.add_argument('--sessions', type=int, default=10)
    ds.add_argument('--cases-per-session', type=int, default=1_000_000)
    ds.add_argument('--require-full', action='store_true')
    ds.add_argument('--output', type=Path)
    gg = sub.add_parser('gold-plan', help='R1: reverse-derive contextual R1-R4/P01-P12 obligations')
    gg.add_argument('--contract', type=Path, default=Path('.cora/contracts/dod/gold-assurance.json'))
    gg.add_argument('--intent', required=True)
    gg.add_argument('--pilot-report', type=Path)
    gg.add_argument('--ictc-root', type=Path)
    gg.add_argument('--ikant-root', type=Path)
    gg.add_argument('--aosp1-root', type=Path)
    gg.add_argument('--output', type=Path)
    gt = sub.add_parser('gold-pilot', help='R4: source-only SHA-bound checkouts; does not run target code')
    gt.add_argument('--contract', type=Path, default=Path('.cora/contracts/dod/gold-assurance.json'))
    gt.add_argument('--ictc-root', type=Path)
    gt.add_argument('--ikant-root', type=Path)
    gt.add_argument('--aosp1-root', type=Path)
    gt.add_argument('--output', type=Path)
    gm = sub.add_parser('gold-mutate', help='R2: bounded physical source mutants; Docker opt-in')
    gm.add_argument('source', type=Path)
    gm.add_argument('plan', type=Path)
    gm.add_argument('--authorize-docker', action='store_true')
    gm.add_argument('--output', type=Path)
    ge = sub.add_parser('gold-effects', help='R3: conservative potential workflow effects')
    ge.add_argument('workflow', type=Path)
    ge.add_argument('--revision', required=True)
    ge.add_argument('--claimed-receipt', type=Path)
    ge.add_argument('--output', type=Path)
    gx = sub.add_parser('stress-gold', help='10M finite realistic fault-class scenarios, not real source mutants')
    gx.add_argument('--contract', type=Path, default=Path('.cora/contracts/dod/gold-assurance.json'))
    gx.add_argument('--sessions', type=int, default=10)
    gx.add_argument('--cases-per-session', type=int, default=1000000)
    gx.add_argument('--require-full', action='store_true')
    gx.add_argument('--output', type=Path)
    cp = sub.add_parser('convergence-plan', help='Canonical R1-R4 source/full/external reticular DoD')
    cp.add_argument('--contract', type=Path, default=Path('.cora/contracts/dod/convergence-dod.json'))
    cp.add_argument('--goal', choices=('G_SOURCE_CONVERGENCE','G_R1_R4_COMPLETE','G_GOVERNED'), default='G_R1_R4_COMPLETE')
    cp.add_argument('--output', type=Path)
    cs = sub.add_parser('stress-convergence', help='10M preseeded realistic finite fault-class model cases, not physical code mutations')
    cs.add_argument('--contract', type=Path, default=Path('.cora/contracts/dod/convergence-dod.json'))
    cs.add_argument('--sessions', type=int, default=10)
    cs.add_argument('--cases-per-session', type=int, default=1000000)
    cs.add_argument('--require-full', action='store_true')
    cs.add_argument('--integrated', action='store_true', help='10M bounded integrated semantic model, not target mutants')
    cs.add_argument('--synergic', action='store_true', help='1M preseeded five-goal semantic model cases; no target execution')
    cs.add_argument('--repo', type=Path, default=Path('.'))
    cs.add_argument('--revision', default='HEAD')
    cs.add_argument('--seed', type=int, default=883)
    cs.add_argument('--output', type=Path)
    za = sub.add_parser('zip-intake', help='Bounded untrusted ZIP preflight: no execution, history unavailable')
    za.add_argument('archive', type=Path)
    za.add_argument('--expected-tree', help='Caller-supplied expected Git SHA-1 tree (not authenticated)')
    za.add_argument('--extract-to', type=Path, help='Explicit new empty directory; never execute')
    za.add_argument('--output', type=Path)
    zv = sub.add_parser('verify-zip-intake', help='Recompute original ZIP evidence; no Git history claim')
    zv.add_argument('report', type=Path)
    zv.add_argument('--archive', required=True, type=Path)
    zv.add_argument('--workspace', type=Path, help='Existing extracted workspace to revalidate')
    zv.add_argument('--output', type=Path)
    ro = sub.add_parser('runtime-observe', help='Separate opt-in Docker observation; not an attested sandbox')
    ro.add_argument('archive', type=Path)
    ro.add_argument('--workspace', required=True, type=Path)
    ro.add_argument('--image', help='Preloaded pinned image of form NAME@sha256:DIGEST')
    ro.add_argument('--execute', action='store_true', help='Explicitly opt in to test execution in Docker')
    ro.add_argument('--output', type=Path)
    fu = sub.add_parser('fuse-evidence', help='Source/optional runtime report reconciliation without authorization')
    fu.add_argument('zip_report', type=Path)
    fu.add_argument('--runtime-report', type=Path)
    fu.add_argument('--source-process', type=Path)
    fu.add_argument('--output', type=Path)
    fv = sub.add_parser('verify-fusion', help='Rebuild fusion from original receipts')
    fv.add_argument('fusion_report', type=Path)
    fv.add_argument('--zip-report', type=Path, required=True)
    fv.add_argument('--runtime-report', type=Path)
    fv.add_argument('--source-process', type=Path)
    fv.add_argument('--output', type=Path)
    la = sub.add_parser('lattice-audit', help='Reconcile ZIP/runtime obligations; not approval')
    la.add_argument('archive', type=Path)
    la.add_argument('--zip-report', required=True, type=Path)
    la.add_argument('--runtime-report', type=Path)
    la.add_argument('--source-process', type=Path)
    la.add_argument('--workspace', type=Path)
    la.add_argument('--output', type=Path)
    lv = sub.add_parser('verify-lattice', help='Replay lattice against original ZIP')
    lv.add_argument('lattice_report', type=Path)
    lv.add_argument('--archive', required=True, type=Path)
    lv.add_argument('--zip-report', required=True, type=Path)
    lv.add_argument('--runtime-report', type=Path)
    lv.add_argument('--source-process', type=Path)
    lv.add_argument('--workspace', type=Path)
    lv.add_argument('--output', type=Path)
    a = sub.add_parser('audit')
    a.add_argument('repo', type=Path)
    a.add_argument('--declarations', default='cora.products.json')
    a.add_argument('--output', type=Path)
    s = sub.add_parser('stress')
    s.add_argument('--seed', type=int, default=883)
    s.add_argument('--cases', type=int, default=1_000_000)
    s.add_argument('--output', type=Path)
    e = sub.add_parser('stress-evidence')
    e.add_argument('--seed', type=int, default=883)
    e.add_argument('--cases', type=int, default=1_000_000)
    e.add_argument('--output', type=Path)
    gg = sub.add_parser('graph')
    gg.add_argument('repo', type=Path)
    gg.add_argument('--revision', default='HEAD')
    gg.add_argument('--ontology', default='cora.ontology.json')
    gg.add_argument('--output', type=Path)
    xx = sub.add_parser('explain')
    xx.add_argument('graph_json', type=Path)
    xx.add_argument('--repo', required=True, type=Path)
    xx.add_argument('--source', required=True)
    xx.add_argument('--target', required=True)
    xx.add_argument('--output', type=Path)
    st = sub.add_parser('stress-graph')
    st.add_argument('--seed', type=int, default=883)
    st.add_argument('--cases', type=int, default=1000000)
    st.add_argument('--output', type=Path)
    ad = sub.add_parser('adapter-audit')
    ad.add_argument('repo', type=Path)
    ad.add_argument('--revision', default='HEAD')
    ad.add_argument('--output', type=Path)
    av = sub.add_parser('verify-adapters')
    av.add_argument('report', type=Path)
    av.add_argument('--repo', required=True, type=Path)
    av.add_argument('--output', type=Path)
    asm = sub.add_parser('stress-adapters')
    asm.add_argument('--seed', type=int, default=883)
    asm.add_argument('--cases', type=int, default=1000000)
    asm.add_argument('--output', type=Path)
    cl = sub.add_parser('closure', help='Issue scoped observational certificate from Git evidence')
    cl.add_argument('repo', type=Path)
    cl.add_argument('--claim', required=True, choices=('committed_blob','declared_product_membership','declared_manifest_dependency','static_import_candidate','safe_deletion'))
    cl.add_argument('--path', required=True)
    cl.add_argument('--selector', default='')
    cl.add_argument('--revision', default='HEAD')
    cl.add_argument('--ontology', default='cora.ontology.json')
    cl.add_argument('--output', type=Path)
    cv = sub.add_parser('verify-certificate', help='Compare scoped certificate against original Git objects')
    cv.add_argument('certificate', type=Path)
    cv.add_argument('--repo', required=True, type=Path)
    cv.add_argument('--ontology', default='cora.ontology.json')
    cv.add_argument('--output', type=Path)
    cs = sub.add_parser('stress-closure')
    cs.add_argument('--seed', type=int, default=883)
    cs.add_argument('--cases', type=int, default=1000000)
    cs.add_argument('--output', type=Path)
    plan = sub.add_parser('plan-rename-doc',help='Read-only plan for exact tracked-doc path rename')
    plan.add_argument('repo',type=Path)
    plan.add_argument('--old',required=True)
    plan.add_argument('--new',required=True)
    plan.add_argument('--output',type=Path)
    apply = sub.add_parser('apply-rename-doc',help='Approved scoped doc rename with tests and compensating rollback')
    apply.add_argument('repo',type=Path)
    apply.add_argument('--plan',required=True,type=Path)
    apply.add_argument('--approve',required=True)
    apply.add_argument('--test-command',required=True)
    apply.add_argument('--output',type=Path)
    gi = sub.add_parser('guard-install',help='Materialize standalone local guard')
    gi.add_argument('repo',type=Path)
    gi.add_argument('--product',action='append',required=True,help='id=relative/root=python.module_prefix')
    gi.add_argument('--output',type=Path)
    gc = sub.add_parser('guard-check',help='Run deterministic local architecture guard')
    gc.add_argument('repo',type=Path)
    gc.add_argument('--base')
    gc.add_argument('--output',type=Path)
    ts = sub.add_parser('stress-transform')
    ts.add_argument('--seed',type=int,default=883)
    ts.add_argument('--cases',type=int,default=1000000)
    ts.add_argument('--output',type=Path)
    lab = sub.add_parser('file-lab', help='Per-file read-only multi-scale forensic evidence lab')
    lab.add_argument('repo', type=Path)
    lab.add_argument('--path', required=True)
    lab.add_argument('--revision', default='HEAD')
    lab.add_argument('--ontology', default='cora.ontology.json')
    lab.add_argument('--runtime-events', type=Path)
    lab.add_argument('--ai-hypotheses', type=Path)
    lab.add_argument('--prompt-output', type=Path, help='Optional offline AI prompt envelope, without source code')
    lab.add_argument('--output', type=Path)
    labv = sub.add_parser('verify-file-lab', help='Recompute unannotated lab against Git objects')
    labv.add_argument('lab', type=Path)
    labv.add_argument('--repo', required=True, type=Path)
    labv.add_argument('--ontology', default='cora.ontology.json')
    labv.add_argument('--output', type=Path)
    human = sub.add_parser('file-decision', help='Record human triage intent; never changes target repo')
    human.add_argument('lab', type=Path)
    human.add_argument('--actor', required=True)
    human.add_argument('--role', required=True)
    human.add_argument('--action', required=True)
    human.add_argument('--rationale', required=True)
    human.add_argument('--second-reviewer', default='')
    human.add_argument('--output', type=Path)
    fls = sub.add_parser('stress-file-lab',help='Deterministic model-level forensic triage falsification')
    fls.add_argument('--seed',type=int,default=883)
    fls.add_argument('--cases',type=int,default=1000000)
    fls.add_argument('--output',type=Path)
    ar = sub.add_parser('artifact-audit',help='Multi-role declaration audit at immutable Git commit')
    ar.add_argument('repo',type=Path)
    ar.add_argument('--revision',default='HEAD')
    ar.add_argument('--output',type=Path)
    vr = sub.add_parser('verify-artifacts',help='Recompute artifact report against committed Git')
    vr.add_argument('report',type=Path)
    vr.add_argument('--repo',required=True,type=Path)
    vr.add_argument('--output',type=Path)
    sat = sub.add_parser('stress-artifact-semantics',help='Finite-role semantics saturation; synthetic only')
    sat.add_argument('--seed',type=int,default=883)
    sat.add_argument('--minimum-cases',type=int,default=1000000)
    sat.add_argument('--no-novelty',type=int,default=10000000)
    sat.add_argument('--output',type=Path)
    sf = sub.add_parser('select-file', help='Git-backed conservative single-file investigation selection')
    sf.add_argument('repo', type=Path)
    sf.add_argument('--path', required=True)
    sf.add_argument('--revision', default='HEAD')
    sf.add_argument('--ontology', default='cora.ontology.json')
    sf.add_argument('--output', type=Path)
    sv = sub.add_parser('verify-selection', help='Reconstruct source-only selection against Git objects')
    sv.add_argument('selection_json', type=Path)
    sv.add_argument('--repo', required=True, type=Path)
    sv.add_argument('--output', type=Path)
    stsel = sub.add_parser('stress-selection', help='Replay finite synthetic semantic selection mutations')
    stsel.add_argument('--seed', type=int, default=883)
    stsel.add_argument('--cases', type=int, default=1000000)
    stsel.add_argument('--output', type=Path)
    ha = sub.add_parser('holistic-audit', help='All-in-one read-only Git history, structure and group archaeology')
    ha.add_argument('repo',type=Path)
    ha.add_argument('--revision',default='HEAD')
    ha.add_argument('--max-commits',type=int,default=256)
    ha.add_argument('--focus')
    ha.add_argument('--pr-index',type=Path,help='Optional operator-supplied UNVERIFIED PR-to-commit map')
    ha.add_argument('--output',type=Path)
    ha.add_argument('--ai-request-output',type=Path)
    hv = sub.add_parser('verify-holistic',help='Replay holistic audit from pinned Git objects')
    hv.add_argument('report',type=Path)
    hv.add_argument('--repo',type=Path,required=True)
    hv.add_argument('--output',type=Path)
    hist = sub.add_parser('archaeology',help='Bounded read-only commit archaeology and cochange')
    hist.add_argument('repo',type=Path)
    hist.add_argument('--revision',default='HEAD')
    hist.add_argument('--max-commits',type=int,default=256)
    hist.add_argument('--pr-index',type=Path)
    hist.add_argument('--output',type=Path)
    vh = sub.add_parser('verify-archaeology',help='Replay source Git commit archaeology')
    vh.add_argument('report',type=Path)
    vh.add_argument('--repo',type=Path,required=True)
    vh.add_argument('--output',type=Path)
    gh = sub.add_parser('annotate-groups',help='Ingest AI group hypotheses without decision authority')
    gh.add_argument('report',type=Path)
    gh.add_argument('--repo',type=Path,required=True)
    gh.add_argument('--hypotheses',type=Path,required=True)
    gh.add_argument('--output',type=Path)
    ah = sub.add_parser('stress-archaeology',help='1M deterministic synthetic archaeology policy cases')
    ah.add_argument('--seed',type=int,default=883)
    ah.add_argument('--cases',type=int,default=1000000)
    ah.add_argument('--output',type=Path)
    ds = sub.add_parser('debt-scan',help='Git-backed multiscale maintenance risk signals')
    ds.add_argument('repo',type=Path)
    ds.add_argument('--revision',default='HEAD')
    ds.add_argument('--max-commits',type=int,default=64)
    ds.add_argument('--sarif',type=Path,help='Optional UNTRUSTED external SARIF 2.1.0')
    ds.add_argument('--output',type=Path)
    dv = sub.add_parser('verify-debt',help='Re-run debt scan against original Git objects')
    dv.add_argument('report',type=Path)
    dv.add_argument('--repo',required=True,type=Path)
    dv.add_argument('--sarif',type=Path,help='Same original untrusted SARIF bytes')
    dv.add_argument('--output',type=Path)
    dd = sub.add_parser('debt-diff',help='Compare source-bound debt signals across two commits')
    dd.add_argument('repo',type=Path)
    dd.add_argument('--base',required=True)
    dd.add_argument('--head',default='HEAD')
    dd.add_argument('--max-commits',type=int,default=64)
    dd.add_argument('--output',type=Path)
    pc = sub.add_parser('process-list',help='List safe independent CORA processes')
    pc.add_argument('--output',type=Path)
    pr = sub.add_parser('process-run',help='Run one bounded process or full source-only suite')
    pr.add_argument('repo',type=Path)
    pr.add_argument('--revision',default='HEAD')
    pr.add_argument('--process',choices=PROCESSES,default='full')
    pr.add_argument('--max-commits',type=int,default=64)
    pr.add_argument('--focus')
    pr.add_argument('--output',type=Path)
    pr.add_argument('--one-run',action='store_true',help='Integrated source execution + measured results atlas; not all 71 commands')
    pr.add_argument('--atlas-html',type=Path,help='Offline navigable HTML with actual measured run outcomes')
    pr.add_argument('--atlas-json',type=Path,help='Full one-run JSON for human and AI inspection')
    pr.add_argument('--execute-self-tests',action='store_true',help='Explicit opt-in to locally execute CORA unittest suite; not an external oracle')
    pr.add_argument('--test-timeout',type=int,default=240)
    pr.add_argument('--model-stress-cases',type=int,choices=(0,100000),default=0,help='Opt-in bounded 100k preseeded receipt mutants, not physical code changes')
    pr.add_argument('--profile',choices=('comprehensive',),help='PR37: account for every discovered CORA activity; source-only by default')
    pr.add_argument('--portable-profile',type=Path,help='Opt-in target-owned external source profile; not the CORA self-DoD')
    pr.add_argument('--portable-evidence-dir',type=Path,help='Optional retained observation bytes, never implicit execution')
    pr.add_argument('--portable-native-probe',type=Path,help='Opt-in retained local subprocess receipt; no test execution by One-Run')
    pr.add_argument('--portable-parse-js',action='store_true',help='Explicit source-only Node VM ESM parser; dynamic consumers remain unknown')
    pr.add_argument('--portable-upstream',action='append',default=[],help='Original Git upstream checkout as owner/repo=/path; proves bytes, never method adoption')
    pr.add_argument('--evidence-dir',type=Path,help='Outside-repo directory for the integrated evidence manifest and optional test log')
    pr.add_argument('--authorization-file',type=Path,help='Explicit exact-SHA local consent for optional untrusted self-tests, not sandbox attestation')
    pr.add_argument('--chat-step',type=Path,help='Caller-authored, non-authoritative per-round JSON plan and gaps')
    pr.add_argument('--chat-bundle',type=Path,help='Outside-repo portable logically append-only session ZIP')
    pv = sub.add_parser('verify-process',help='Source revalidation of process receipt')
    pv.add_argument('report',type=Path)
    pv.add_argument('--repo',required=True,type=Path)
    pv.add_argument('--output',type=Path)
    pv.add_argument('--one-run',action='store_true',help='Verify original Git source, metrics and optional HTML')
    pv.add_argument('--atlas-json',type=Path)
    pv.add_argument('--atlas-html',type=Path)
    pv.add_argument('--portable-profile',type=Path,help='Original caller profile for exact-source replay')
    pv.add_argument('--portable-evidence-dir',type=Path,help='Original immutable observed artifact bytes')
    pv.add_argument('--portable-native-probe',type=Path,help='Replay original retained local subprocess receipt without execution')
    pv.add_argument('--portable-parse-js',action='store_true',help='Recompute exact-Git Node VM source parse')
    pv.add_argument('--portable-upstream',action='append',default=[],help='Re-read original Git upstream objects as owner/repo=/path')
    pv.add_argument('--evidence-dir',type=Path,help='Recompute byte hashes against retained integrated evidence files')
    pv.add_argument('--chat-bundle',type=Path,help='Replay ZIP chain and match latest comprehensive One-Run receipt')
    dsx = sub.add_parser('stress-debt',help='1M seeded debt-policy model mutations')
    dsx.add_argument('--seed',type=int,default=883)
    dsx.add_argument('--cases',type=int,default=1000000)
    dsx.add_argument('--output',type=Path)
    gp = sub.add_parser('dev-premerge', help='Git-bound pre-merge risk and reviewer obligations')
    gp.add_argument('repo',type=Path)
    gp.add_argument('--base',required=True)
    gp.add_argument('--head',default='HEAD')
    gp.add_argument('--strict',action='store_true',help='Exit 2 on missing base policy or blockers')
    gp.add_argument('--contextual',action='store_true',help='Compose canonical R1-R4 reticulum, static owner graph and selective witness invalidation')
    gp.add_argument('--intent',help='Change-specific human intent, claimed not authenticated')
    gp.add_argument('--convergence-contract',type=Path,default=Path('.cora/contracts/dod/convergence-dod.json'))
    gp.add_argument('--witnesses',type=Path,help='Untrusted declared dependency manifest; never authority')
    gp.add_argument('--output',type=Path)
    gm = sub.add_parser('dev-postmerge', help='Post-merge drift and bounded regression obligations')
    gm.add_argument('repo',type=Path)
    gm.add_argument('--previous',required=True)
    gm.add_argument('--head',default='HEAD')
    gm.add_argument('--with-debt',action='store_true')
    gm.add_argument('--strict',action='store_true')
    gm.add_argument('--contextual',action='store_true',help='Compose R1-R4 source obligations on actual merged HEAD')
    gm.add_argument('--intent',help='Change-specific human intent, claimed not authenticated')
    gm.add_argument('--convergence-contract',type=Path,default=Path('.cora/contracts/dod/convergence-dod.json'))
    gm.add_argument('--witnesses',type=Path,help='Caller-declared dependencies not attested')
    gm.add_argument('--output',type=Path)
    gv = sub.add_parser('verify-dev-gate', help='Recompute lifecycle evidence from original Git commits')
    gv.add_argument('report',type=Path)
    gv.add_argument('--repo',type=Path,required=True)
    gv.add_argument('--output',type=Path)
    cv = sub.add_parser('verify-contextual-gate', help='Recompute contextual receipt from exact Git objects and original witnesses')
    cv.add_argument('report',type=Path)
    cv.add_argument('--repo',required=True,type=Path)
    cv.add_argument('--convergence-contract',type=Path,default=Path('.cora/contracts/dod/convergence-dod.json'))
    cv.add_argument('--witnesses',type=Path)
    cv.add_argument('--intent',help='Same exact change intent as original report')
    cv.add_argument('--output',type=Path)
    ga = sub.add_parser('agent-check', help='Check coding agent proposal against Git; never approve')
    ga.add_argument('proposal',type=Path)
    ga.add_argument('--repo',type=Path,required=True)
    ga.add_argument('--output',type=Path)
    gs = sub.add_parser('stress-continuous', help='Finite deterministic CI governance model replay')
    gs.add_argument('--seed',type=int,default=883)
    gs.add_argument('--cases',type=int,default=1000000)
    gs.add_argument('--output',type=Path)
    wa = sub.add_parser('workflow-audit', help='Pinned CI workflow discovery and review-only minimization candidates')
    wa.add_argument('repo', type=Path)
    wa.add_argument('--revision', default='HEAD')
    wa.add_argument('--base', help='Optional original revision for added/removed/modified comparison')
    wa.add_argument('--output', type=Path)
    wv = sub.add_parser('verify-workflows', help='Replay CI workflow report from exact Git objects')
    wv.add_argument('report', type=Path)
    wv.add_argument('--repo', required=True, type=Path)
    wv.add_argument('--output', type=Path)
    ms = sub.add_parser('method-synthesize', help='Join same-commit evidence and prepare non-authoritative AI case')
    ms.add_argument('repo', type=Path)
    ms.add_argument('--revision', default='HEAD')
    ms.add_argument('--artifacts', type=Path, help='Optional original artifact-audit receipt, reverified')
    ms.add_argument('--workflows', type=Path, help='Optional original workflow-audit receipt, reverified')
    ms.add_argument('--process', type=Path, help='Optional original process-run receipt, reverified')
    ms.add_argument('--hypotheses', type=Path, help='Optional untrusted AI hypothesis envelope')
    ms.add_argument('--analyst-request', type=Path, help='Source-free bounded case questions')
    ms.add_argument('--integrated', action='store_true', help='Original method + doc/implementation case, source-only')
    ms.add_argument('--synergic', action='store_true', help='Five source-bound synergic goals through original methods')
    ms.add_argument('--base-sha', help='Original BASE for continuous semantic evolution')
    ms.add_argument('--execute-source-probes', action='store_true', help='Opt-in three safe original CORA Git source probes')
    ms.add_argument('--ai-observations', type=Path, help='Untrusted source-bound AI answer; never approval')
    ms.add_argument('--ai-request-output', type=Path, help='Export reticular AI questions; no provider call')
    ms.add_argument('--atlas-json', type=Path, help='Export deterministic source-only human/AI capability atlas')
    ms.add_argument('--atlas-html', type=Path, help='Export self-contained offline navigable HTML')
    ms.add_argument('--output', type=Path)
    mv = sub.add_parser('verify-method-synthesis', help='Exact Git replay of correlation and original inputs')
    mv.add_argument('report', type=Path)
    mv.add_argument('--repo', type=Path, required=True)
    mv.add_argument('--artifacts', type=Path)
    mv.add_argument('--workflows', type=Path)
    mv.add_argument('--process', type=Path)
    mv.add_argument('--hypotheses', type=Path)
    mv.add_argument('--integrated', action='store_true', help='Recompute integrated source case from original Git')
    mv.add_argument('--synergic', action='store_true', help='Replay five-goal source case and safe original Git probes')
    mv.add_argument('--ai-observations', type=Path, help='Original untrusted AI envelope for replay')
    mv.add_argument('--atlas-json', type=Path, help='Re-derive atlas JSON from original Git and compare')
    mv.add_argument('--atlas-html', type=Path, help='Re-derive atlas HTML from original Git and compare')
    mv.add_argument('--output', type=Path)
    g = sub.add_parser('snapshot')
    g.add_argument('repo', type=Path)
    g.add_argument('--revision', default='HEAD')
    g.add_argument('--output', type=Path)
    v = sub.add_parser('verify-ledger')
    v.add_argument('ledger', type=Path)
    v.add_argument('--repo', required=True, type=Path, help='Recheck all Git objects at the recorded commit')
    v.add_argument('--output', type=Path)
    args = p.parse_args(argv)
    try:
        if args.cmd == 'dod-plan':
            contract=load_contract(args.contract)
            result=backward_plan(contract,goal=args.goal or STAGES[args.stage])
            code=0
        elif args.cmd == 'dod-assess':
            contract=load_contract(args.contract)
            claims=json.loads(args.observations.read_text(encoding='utf-8'))
            result=assess_claims(contract,claims,goal=args.goal or STAGES[args.stage])
            code=0 if result['goal_status']=='MODEL_ELIGIBLE_UNATTESTED' else 2
        elif args.cmd == 'verify-dod':
            contract=load_contract(args.contract)
            claims=json.loads(args.observations.read_text(encoding='utf-8'))
            receipt=json.loads(args.report.read_text(encoding='utf-8'))
            verify_assessment(contract,claims,receipt)
            result={'schema':'cora-agent-dod-verification/1',
                    'status':'MODEL_REPLAY_ONLY','report_digest':receipt['report_digest'],
                    'authorization':'NONE'}
            code=0
        elif args.cmd == 'stress-agent-dod':
            contract=load_contract(args.contract)
            result=saturate_agent_dod(contract,sessions=args.sessions,
                                     cases_per_session=args.cases_per_session)
            code=2 if result['status']=='REFUTED' or (args.require_full and
                result['status']!='PASS_SCOPED_FINITE_MODEL') else 0
        elif args.cmd == 'convergence-plan':
            contract=load_convergence_contract(args.contract)
            result=convergent_plan(contract,args.goal)
            code=0
        elif args.cmd == 'stress-convergence':
            if args.synergic:
                if args.integrated:
                    raise ValueError('choose only one finite model')
                cases=args.sessions*args.cases_per_session
                if args.require_full and cases!=1000000:
                    raise ValueError('five-goal require-full means one million preseeded cases')
                result=stress_five_synergies(args.repo,args.revision,cases=cases,seed=args.seed)
                code=0 if result['state']=='PASS_SCOPED_SEEDED_MODEL' else 2
            elif args.integrated:
                cases=args.sessions*args.cases_per_session
                if args.require_full and cases!=10000000:
                    raise ValueError('integrated require-full needs exactly 10M finite cases')
                result=stress_integrated(cases=cases)
                code=2 if result['status']!='PASS_SCOPED_FINITE_MODEL' else 0
            else:
                contract=load_convergence_contract(args.contract)
                result=saturate_convergence(contract,sessions=args.sessions,
                                            cases_per_session=args.cases_per_session)
                code=2 if result['status']=='REFUTED' or (args.require_full and
                            result['status']!='PASS_SCOPED_FINITE_MODEL') else 0
        elif args.cmd == 'gold-plan':
            c=load_gold_contract(args.contract)
            pilot=json.loads(args.pilot_report.read_text('utf-8')) if args.pilot_report else None
            roots={}
            for n,pth in (('ictc',args.ictc_root),('ikant',args.ikant_root),('aosp1',args.aosp1_root)):
                if pth:
                    roots['Luke883i/'+n]=pth
            result=contextual_gold(c,args.intent,pilot,roots=roots if roots else None)
            code=0
        elif args.cmd == 'gold-pilot':
            c=load_gold_contract(args.contract)
            roots={}
            for n,pth in (('ictc',args.ictc_root),('ikant',args.ikant_root),
                          ('aosp1',args.aosp1_root)):
                if pth:
                    roots['Luke883i/'+n]=pth
            result=pilot_sources(c,roots)
            code=0 if result['state']=='SOURCE_READBACK_3_OF_3' else 2
        elif args.cmd == 'gold-mutate':
            plan=json.loads(args.plan.read_text('utf-8'))
            result=physical_mutants(args.source,plan,authorize_docker=args.authorize_docker)
            code=0 if result['status']=='SCOPED_ORACLE_KILLED_ALL' else 2
        elif args.cmd == 'gold-effects':
            actual=audit_workflow(args.workflow.read_text('utf-8'),
                path=str(args.workflow),revision=args.revision)
            if args.claimed_receipt:
                claim=json.loads(args.claimed_receipt.read_text('utf-8'))
                result={'inventory':actual,'claim_reconciliation':reconcile_effect_claim(actual,claim)}
            else:
                result=actual
            code=0
        elif args.cmd == 'stress-gold':
            c=load_gold_contract(args.contract)
            result=gold_saturation(c,sessions=args.sessions,
                                   cases_per_session=args.cases_per_session)
            code=2 if result['status']=='REFUTED' or (args.require_full and
                       result['status']!='PASS_SCOPED_FINITE_MODEL') else 0
        elif args.cmd == 'zip-intake':
            result = inspect_zip(args.archive, expected_tree=args.expected_tree,
                                 extract_to=args.extract_to)
            code = 0
        elif args.cmd == 'verify-zip-intake':
            receipt=json.loads(args.report.read_text(encoding='utf-8'))
            verify_intake(args.archive,receipt,workspace=args.workspace)
            result={'schema':'cora-zip-intake-verification/1','status':'SOURCE_REPLAY_SCOPED',
                    'receipt_digest':receipt['receipt_digest'],'authorization':'NONE'}
            code=0
        elif args.cmd == 'runtime-observe':
            result=observe_runtime(args.archive,args.workspace,execute=args.execute,image=args.image)
            code=0 if result['execution_status'] in ('NOT_REQUESTED','RUN_REPORTED_UNATTESTED') else 2
        elif args.cmd == 'fuse-evidence':
            z=json.loads(args.zip_report.read_text(encoding='utf-8'))
            r=json.loads(args.runtime_report.read_text(encoding='utf-8')) if args.runtime_report else None
            src=json.loads(args.source_process.read_text(encoding='utf-8')) if args.source_process else None
            result=fuse_evidence(z,r,src)
            code=0
        elif args.cmd == 'verify-fusion':
            z=json.loads(args.zip_report.read_text(encoding='utf-8'))
            r=json.loads(args.runtime_report.read_text(encoding='utf-8')) if args.runtime_report else None
            src=json.loads(args.source_process.read_text(encoding='utf-8')) if args.source_process else None
            f=json.loads(args.fusion_report.read_text(encoding='utf-8'))
            verify_fusion(z,f,r,src)
            result={'schema':'cora-fusion-verification/1','status':'REPLAY_SCOPED',
                    'fusion_digest':f['fusion_digest'],'authorization':'NONE'}
            code=0
        elif args.cmd in ('lattice-audit','verify-lattice'):
            z=json.loads(args.zip_report.read_text(encoding='utf-8'))
            rt=json.loads(args.runtime_report.read_text(encoding='utf-8')) if args.runtime_report else None
            src=json.loads(args.source_process.read_text(encoding='utf-8')) if args.source_process else None
            if args.cmd == 'lattice-audit':
                result=lattice_from_evidence(args.archive,z,runtime_report=rt,
                    source_process=src,workspace=args.workspace)
            else:
                receipt=json.loads(args.lattice_report.read_text(encoding='utf-8'))
                verify_lattice(args.archive,receipt,zip_report=z,runtime_report=rt,
                    source_process=src,workspace=args.workspace)
                result={'schema':'cora-lattice-verification/1','status':'SOURCE_REPLAY_SCOPED',
                        'lattice_digest':receipt['lattice_digest'],'authorization':'NONE'}
            code=0
        elif args.cmd == 'version':
            print(__version__)
            return 0
        elif args.cmd == 'audit':
            result = audit(args.repo, read_declarations(args.repo, args.declarations))
            code = 2 if result['findings'] else 0
        elif args.cmd == 'stress':
            result = stress(seed=args.seed, cases=args.cases)
            code = 2 if result['mismatches'] else 0
        elif args.cmd == 'stress-evidence':
            result = stress_evidence(seed=args.seed, cases=args.cases)
            code = 2 if result['mismatches'] else 0
        elif args.cmd == 'stress-graph':
            result = stress_graph(seed=args.seed,cases=args.cases)
            code = 2 if result['mismatches'] else 0
        elif args.cmd == 'graph':
            result = graph_from_commit(args.repo,args.revision,args.ontology)
            code = 0
        elif args.cmd == 'explain':
            gdata = json.loads(args.graph_json.read_text(encoding='utf-8'))
            verify_graph_against_git(args.repo, gdata)
            result = explain_path(gdata,args.source,args.target)
            code = 0
        elif args.cmd == 'adapter-audit':
            result = adapter_audit(args.repo, args.revision)
            code = 0
        elif args.cmd == 'verify-adapters':
            report = json.loads(args.report.read_text(encoding='utf-8'))
            verify_adapter_report(args.repo, report)
            result = {'schema':'cora-adapter-verification/1','status':'verified_against_git_objects','commit':report['commit'],'report_digest':report['report_digest']}
            code = 0
        elif args.cmd == 'stress-adapters':
            result = stress_adapters(seed=args.seed,cases=args.cases)
            code = 2 if result['mismatches'] else 0
        elif args.cmd == 'closure':
            result = closure(args.repo,args.claim,args.path,selector=args.selector,
                             revision=args.revision,ontology_path=args.ontology)
            code = 0
        elif args.cmd == 'verify-certificate':
            cert = json.loads(args.certificate.read_text(encoding='utf-8'))
            verify_certificate(args.repo,cert,ontology_path=args.ontology)
            result = {'schema':'cora-closure-verification/1','status':'verified_against_git_objects',
                      'commit':cert['commit'],'certificate_digest':cert['certificate_digest']}
            code = 0
        elif args.cmd == 'stress-closure':
            result = stress_closure(seed=args.seed,cases=args.cases)
            code = 2 if result['mismatches'] else 0
        elif args.cmd == 'plan-rename-doc':
            result = plan_rename_docs(args.repo,args.old,args.new)
            code = 0
        elif args.cmd == 'apply-rename-doc':
            result = apply_rename_docs(args.repo,json.loads(args.plan.read_text(encoding='utf-8')),
                                       approval=args.approve,test_command=shlex.split(args.test_command))
            code = 0
        elif args.cmd == 'guard-install':
            result = install_guard(args.repo,args.product)
            code = 0
        elif args.cmd == 'guard-check':
            result = verify_local_guard(args.repo,args.base)
            code = 0 if result['status']=='PASS_SCOPED' else 2
        elif args.cmd == 'stress-transform':
            result = stress_transform(seed=args.seed,cases=args.cases)
            code = 2 if result['mismatches'] else 0
        elif args.cmd == 'file-lab':
            result = examine_file(args.repo,args.path,revision=args.revision,
                                  ontology_path=args.ontology,runtime_events=args.runtime_events,
                                  ai_hypotheses=args.ai_hypotheses)
            if args.prompt_output:
                args.prompt_output.write_text(json.dumps(ai_prompt(result),indent=2,sort_keys=True)+'\n',encoding='utf-8')
            code = 0
        elif args.cmd == 'verify-file-lab':
            lab_data=json.loads(args.lab.read_text(encoding='utf-8'))
            verify_lab(args.repo,lab_data,ontology_path=args.ontology)
            result={'schema':'cora-file-lab-verification/1','status':'VERIFIED_SCOPED',
                    'lab_digest':lab_data['lab_digest'],'commit':lab_data['commit']}
            code=0
        elif args.cmd == 'file-decision':
            lab_data=json.loads(args.lab.read_text(encoding='utf-8'))
            result=record_human_decision(lab_data,actor=args.actor,role=args.role,action=args.action,
                                         rationale=args.rationale,second_reviewer=args.second_reviewer)
            code=0
        elif args.cmd == 'stress-file-lab':
            result=stress_file_lab(seed=args.seed,cases=args.cases)
            code=2 if result['mismatches'] else 0
        elif args.cmd == 'artifact-audit':
            result = artifact_audit(args.repo,args.revision)
            code = 2 if result['summary']['unclassified'] or result['summary']['stale_rules'] else 0
        elif args.cmd == 'verify-artifacts':
            report = json.loads(args.report.read_text(encoding='utf-8'))
            verify_artifact_report(args.repo,report)
            result = {'schema':'cora-artifact-verification/1','status':'VERIFIED_SCOPED',
                      'report_digest':report['report_digest'],'commit':report['commit']}
            code = 0
        elif args.cmd == 'stress-artifact-semantics':
            result = saturate(seed=args.seed,minimum_cases=args.minimum_cases,no_novelty=args.no_novelty)
            code = 2 if result['mismatches'] else 0
        elif args.cmd == 'select-file':
            result = select_file(args.repo, args.path, revision=args.revision,
                                 ontology_path=args.ontology)
            code = 0
        elif args.cmd == 'verify-selection':
            candidate = json.loads(args.selection_json.read_text(encoding='utf-8'))
            verify_selection(args.repo, candidate)
            result = {'schema':'cora-selection-verification/1',
                      'status':'VERIFIED_SCOPED', 'commit':candidate['commit'],
                      'selection_digest':candidate['selection_digest'],
                      'authorized_action':'NONE'}
            code = 0
        elif args.cmd == 'stress-selection':
            result = stress_selection(seed=args.seed,cases=args.cases)
            code = 2 if result['mismatches'] else 0
        elif args.cmd == 'holistic-audit':
            pr_index = json.loads(args.pr_index.read_text(encoding='utf-8')) if args.pr_index else None
            result = holistic_audit(args.repo,args.revision,max_commits=args.max_commits,focus=args.focus,pr_index=pr_index)
            if args.ai_request_output:
                args.ai_request_output.write_text(json.dumps(group_ai_request(result),indent=2,sort_keys=True)+'\n',encoding='utf-8')
            code = 0
        elif args.cmd == 'verify-holistic':
            item = json.loads(args.report.read_text(encoding='utf-8'))
            verify_holistic(args.repo,item)
            result = {'schema':'cora-holistic-verification/1','status':'VERIFIED_AGAINST_GIT','commit':item['commit'],'report_digest':item['report_digest']}
            code = 0
        elif args.cmd == 'archaeology':
            pr_index = json.loads(args.pr_index.read_text(encoding='utf-8')) if args.pr_index else None
            result = mine_history(args.repo,args.revision,max_commits=args.max_commits,pr_index=pr_index)
            code = 0
        elif args.cmd == 'verify-archaeology':
            item = json.loads(args.report.read_text(encoding='utf-8'))
            verify_history(args.repo,item)
            result = {'schema':'cora-archaeology-verification/1','status':'VERIFIED_AGAINST_GIT','commit':item['commit'],'digest':item['digest']}
            code = 0
        elif args.cmd == 'annotate-groups':
            report = json.loads(args.report.read_text(encoding='utf-8'))
            hypotheses = json.loads(args.hypotheses.read_text(encoding='utf-8'))
            result = annotate_groups(args.repo,report,hypotheses)
            code = 0
        elif args.cmd == 'stress-archaeology':
            result = stress_archaeology(seed=args.seed,cases=args.cases)
            code = 2 if result['mismatches'] else 0
        elif args.cmd == 'debt-scan':
            raw = args.sarif.read_bytes() if args.sarif else None
            result = debt_scan(args.repo,args.revision,max_commits=args.max_commits,sarif_bytes=raw)
            code = 0
        elif args.cmd == 'verify-debt':
            item = json.loads(args.report.read_text(encoding='utf-8'))
            raw = args.sarif.read_bytes() if args.sarif else None
            verify_debt(args.repo,item,sarif_bytes=raw)
            result = {'schema':'cora-debt-verification/1','status':'REPLAYED_FROM_GIT_WITH_OPTIONAL_UNTRUSTED_SARIF',
                      'commit':item['commit'],'report_digest':item['report_digest']}
            code = 0
        elif args.cmd == 'debt-diff':
            result = compare_debt(args.repo,args.base,args.head,max_commits=args.max_commits)
            code = 0
        elif args.cmd == 'process-list':
            result = process_catalog()
            code = 0
        elif args.cmd == 'process-run':
            if bool(args.chat_step) != bool(args.chat_bundle):
                raise ValueError('chat steps require both --chat-step and --chat-bundle')
            if args.chat_bundle and (not args.one_run or args.profile != 'comprehensive'):
                raise ValueError('chat bundle requires --one-run --profile comprehensive')
            chat_step = load_chat_step(args.chat_step) if args.chat_step else None
            if args.portable_profile and (not args.one_run or args.profile or args.chat_step
                                          or args.chat_bundle or args.execute_self_tests
                                          or args.model_stress_cases or args.authorization_file
                                          or args.evidence_dir):
                raise ValueError('portable profile requires unprivileged --one-run only')
            if (args.portable_evidence_dir or args.portable_parse_js or args.portable_upstream or args.portable_native_probe) and not args.portable_profile:
                raise ValueError('portable evidence requires portable profile')
            if args.one_run:
                if args.portable_profile:
                    result = run_portable(args.repo,args.revision,args.portable_profile,
                                          evidence_dir=args.portable_evidence_dir,
                                          parse_js=args.portable_parse_js,
                                          upstream_paths=parse_upstream_paths(args.portable_upstream),
                                          native_probe=args.portable_native_probe)
                    if args.atlas_json:
                        args.atlas_json.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
                    if args.atlas_html:
                        args.atlas_html.write_text(render_portable_html(result),encoding='utf-8')
                    code = 2 if (result['source_status']=='DEBT_BLOCKED' or
                                 result.get('native_gold',{}).get('report_status') ==
                                 'LOCAL_RUNNER_FAIL_REPORTED') else 0
                elif args.profile == 'comprehensive':
                    result = run_integrated(args.repo,args.revision,process=args.process,
                        max_commits=args.max_commits,focus=args.focus,
                        execute_self_tests=args.execute_self_tests,
                        authorization_file=args.authorization_file,
                        evidence_dir=args.evidence_dir,test_timeout=args.test_timeout,
                        model_stress_cases=args.model_stress_cases)
                    if args.atlas_json:
                        args.atlas_json.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
                    if args.atlas_html:
                        args.atlas_html.write_text(render_integrated_html(result),encoding='utf-8')
                    if args.chat_bundle:
                        append_chat_iteration(args.chat_bundle, repo=args.repo, step=chat_step, receipt=result)
                    # External blockers do not prevent generating a truthful dossier.
                    base = result['baseline_pr36']
                    code = 2 if (base['source_status']=='DEBT_BLOCKED'
                                 or base['model_stress']['status']=='REFUTED'
                                 or result['tests']['state']=='FAIL') else 0
                else:
                    if args.evidence_dir or args.authorization_file:
                        raise ValueError('integrated evidence/authorization flags require --profile comprehensive')
                    result = run_one(args.repo,args.revision,process=args.process,
                                     max_commits=args.max_commits,focus=args.focus,
                                     execute_self_tests=args.execute_self_tests,
                                     test_timeout=args.test_timeout,
                                     model_stress_cases=args.model_stress_cases)
                    if args.atlas_json:
                        args.atlas_json.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
                    if args.atlas_html:
                        args.atlas_html.write_text(render_one_html(result),encoding='utf-8')
                    code = 2 if (result['source_status']=='DEBT_BLOCKED'
                                 or result['runtime_status']=='FAIL'
                                 or result['model_stress']['status']=='REFUTED') else 0
            else:
                if (args.atlas_html or args.atlas_json or args.execute_self_tests
                        or args.model_stress_cases or args.profile or args.evidence_dir
                        or args.authorization_file):
                    raise ValueError('integrated/HTML/JSON/optional execution flags require --one-run')
                result = run_suite(args.repo,args.revision,process=args.process,
                                   max_commits=args.max_commits,focus=args.focus)
                code = 0 if result['status']!='DEBT_BLOCKED' else 2
        elif args.cmd == 'verify-process':
            item = json.loads(args.report.read_text(encoding='utf-8'))
            if args.one_run:
                if (args.portable_evidence_dir or args.portable_parse_js or args.portable_upstream or args.portable_native_probe) and not args.portable_profile:
                    raise ValueError('portable evidence requires original profile')
                if args.atlas_json and json.loads(args.atlas_json.read_text('utf-8')) != item:
                    raise ValueError('one-run JSON atlas is not the source receipt')
                if item.get('schema') == 'cora-portable-one-run/1':
                    if not args.portable_profile or args.evidence_dir or args.chat_bundle:
                        raise ValueError('portable replay requires original profile and no integrated effects')
                    verify_portable(args.repo,item,args.portable_profile,
                         evidence_dir=args.portable_evidence_dir,
                         html_page=args.atlas_html.read_text('utf-8') if args.atlas_html else None,
                         parse_js=args.portable_parse_js,
                         upstream_paths=parse_upstream_paths(args.portable_upstream),
                         native_probe=args.portable_native_probe)
                    result = {'schema':'cora-portable-one-run-replay/1',
                        'status':'GIT_SOURCE_REPLAYED_EXTERNAL_NOT_ATTESTED',
                        'receipt_digest':item['receipt_digest'],'commit':item['commit'],
                        'authorization':'NONE','product_status':'BLOCKED_EXTERNAL'}
                elif item.get('schema') == 'cora-integrated-one-run/2':
                    verify_integrated_one_run(args.repo,item,
                        html_page=args.atlas_html.read_text('utf-8') if args.atlas_html else None,
                        evidence_dir=args.evidence_dir)
                    result = {'schema':'cora-integrated-one-run-replay/2',
                              'status':'GIT_SOURCE_REPLAYED_LOCAL_TESTS_NOT_INDEPENDENTLY_ATTESTED',
                              'receipt_digest':item['receipt_digest'],'commit':item['commit'],
                              'product_status':'BLOCKED_EXTERNAL','authorization':'NONE'}
                    if args.chat_bundle:
                        result['chat_bundle'] = verify_chat_bundle(args.chat_bundle, expected_receipt=item)
                else:
                    if args.evidence_dir or args.chat_bundle:
                        raise ValueError('integrated source receipt required for evidence/chat ZIP')
                    verify_one(args.repo,item,
                               html_page=args.atlas_html.read_text('utf-8') if args.atlas_html else None)
                    result = {'schema':'cora-one-run-replay/1','status':'SOURCE_REPLAYED_RUNTIME_NOT_ATTESTED',
                              'receipt_digest':item['receipt_digest'],'commit':item['commit'],
                              'authorization':'NONE'}
            else:
                if (args.atlas_json or args.atlas_html or args.evidence_dir or args.chat_bundle
                        or args.portable_profile or args.portable_evidence_dir or args.portable_parse_js
                        or args.portable_upstream or args.portable_native_probe):
                    raise ValueError('one-run atlas/chat/portable replay requires --one-run')
                verify_suite(args.repo,item)
                result = {'schema':'cora-process-verification/1','status':'SOURCE_REPLAY_VERIFIED',
                          'run_digest':item['run_digest'],'commit':item['commit']}
            code = 0
        elif args.cmd == 'stress-debt':
            result = stress_debt(seed=args.seed,cases=args.cases)
            code = 2 if result['mismatches'] else 0
        elif args.cmd == 'dev-premerge':
            if args.contextual:
                contract=load_convergence_contract(args.convergence_contract)
                declared=json.loads(args.witnesses.read_text('utf-8')) if args.witnesses else []
                result=evaluate_contextual(args.repo,args.base,args.head,contract=contract,
                                           phase='premerge',witnesses=declared,intent=args.intent)
                code=2 if args.strict else 0  # Full R1-R4 remains externally blocked.
            else:
                result = development_gate(args.repo,args.base,args.head,phase='premerge')
                code = 2 if args.strict and (result['status'] != 'OBSERVED_REVIEW_REQUIRED' or result['blockers']) else 0
        elif args.cmd == 'dev-postmerge':
            if args.contextual:
                contract=load_convergence_contract(args.convergence_contract)
                declared=json.loads(args.witnesses.read_text('utf-8')) if args.witnesses else []
                result=evaluate_contextual(args.repo,args.previous,args.head,contract=contract,
                                           phase='postmerge',with_debt=args.with_debt,
                                           witnesses=declared,intent=args.intent)
                code=2 if args.strict else 0  # No self-attested product acceptance.
            else:
                result = development_gate(args.repo,args.previous,args.head,phase='postmerge',with_debt=args.with_debt)
                code = 2 if args.strict and (result['status'] != 'OBSERVED_REVIEW_REQUIRED' or result['blockers']) else 0
        elif args.cmd == 'verify-contextual-gate':
            contract=load_convergence_contract(args.convergence_contract)
            declared=json.loads(args.witnesses.read_text('utf-8')) if args.witnesses else []
            original=json.loads(args.report.read_text('utf-8'))
            verify_contextual_gate(args.repo,original,contract=contract,witnesses=declared,
                                   intent=args.intent)
            result={'schema':'cora-contextual-verification/1',
                    'status':'REPLAYED_FROM_GIT_NOT_HOST_ATTESTED',
                    'head_commit':original['head_commit'],
                    'digest':original['digest'],'authorization':'NONE'}
            code=0
        elif args.cmd == 'verify-dev-gate':
            item = json.loads(args.report.read_text(encoding='utf-8'))
            verify_gate(args.repo,item)
            result = {'schema':'cora-continuous-verification/1','status':'SOURCE_REPLAY_VERIFIED',
                      'base_commit':item['base_commit'],'head_commit':item['head_commit'],
                      'receipt_digest':item['receipt_digest'],'authorization':'NONE'}
            code=0
        elif args.cmd == 'agent-check':
            item=json.loads(args.proposal.read_text(encoding='utf-8'))
            result=agent_check(args.repo,item)
            code=0
        elif args.cmd == 'stress-continuous':
            result=stress_continuous(seed=args.seed,cases=args.cases)
            code=2 if result['mismatches'] else 0
        elif args.cmd == 'workflow-audit':
            result = audit_workflows(args.repo, args.revision, base=args.base)
            code = 0 if result['source_status'] == 'PASS_SCOPED_SOURCE' else 2
        elif args.cmd == 'verify-workflows':
            candidate = json.loads(args.report.read_text('utf-8'))
            verify_workflows(args.repo, candidate)
            result = {'schema': 'cora-workflow-rationalization-verification/1',
                      'commit': candidate['commit'],
                      'receipt_sha256': candidate['receipt_sha256'],
                      'status': 'REPLAYED_SOURCE_NOT_GOVERNED',
                      'authorization': 'NONE'}
            code = 0
        elif args.cmd == 'method-synthesize':
            loaded = {}
            for key in ('artifacts','workflows','process','hypotheses'):
                path = getattr(args, key)
                loaded[key] = json.loads(path.read_text('utf-8')) if path else None
            if (args.atlas_json or args.atlas_html) and not args.synergic:
                raise ValueError('integrated maturity atlas requires canonical --synergic mode')
            if args.synergic:
                if args.integrated or any(x is not None for x in loaded.values()):
                    raise ValueError('five-goal service owns original source receipts; no conflicting modes')
                ai=json.loads(args.ai_observations.read_text('utf-8')) if args.ai_observations else None
                result=unified_assurance(args.repo,args.revision,base=args.base_sha,
                                         ai=ai,execute_probes=args.execute_source_probes)
                request=result['reasoning_plan']
                if args.ai_request_output:
                    args.ai_request_output.write_text(json.dumps(request,sort_keys=True,indent=2)+'\n',encoding='utf-8')
                if args.analyst_request:
                    args.analyst_request.write_text(json.dumps(request,sort_keys=True,indent=2)+'\n',encoding='utf-8')
                if args.atlas_json or args.atlas_html:
                    atlas = build_atlas(args.repo, result)
                    if args.atlas_json:
                        args.atlas_json.write_text(json.dumps(atlas,sort_keys=True,indent=2)+'\n',encoding='utf-8')
                    if args.atlas_html:
                        args.atlas_html.write_text(render_html(atlas),encoding='utf-8')
            elif args.integrated:
                ai=json.loads(args.ai_observations.read_text('utf-8')) if args.ai_observations else None
                result=integrated_case(args.repo,args.revision,**loaded,ai=ai)
                if args.ai_request_output:
                    args.ai_request_output.write_text(json.dumps(integrated_ai_request(result),sort_keys=True,indent=2)+'\n',encoding='utf-8')
                if args.analyst_request:
                    args.analyst_request.write_text(json.dumps(integrated_ai_request(result),sort_keys=True,indent=2)+'\n',encoding='utf-8')
            else:
                if args.ai_observations or args.ai_request_output:
                    raise ValueError('AI reticular options require --integrated')
                result=synthesize(args.repo,args.revision,**loaded)
                if args.analyst_request:
                    args.analyst_request.write_text(json.dumps(analyst_request(result),sort_keys=True,indent=2)+'\n',encoding='utf-8')
            code = 0
        elif args.cmd == 'verify-method-synthesis':
            original = json.loads(args.report.read_text('utf-8'))
            loaded = {}
            for key in ('artifacts','workflows','process','hypotheses'):
                path = getattr(args, key)
                loaded[key] = json.loads(path.read_text('utf-8')) if path else None
            if (args.atlas_json or args.atlas_html) and not args.synergic:
                raise ValueError('atlas replay requires --synergic mode')
            if args.synergic:
                if args.integrated or any(x is not None for x in loaded.values()):
                    raise ValueError('five-goal replay cannot mix original report operands')
                ai=json.loads(args.ai_observations.read_text('utf-8')) if args.ai_observations else None
                verify_unified_assurance(args.repo,original,ai=ai)
                if args.atlas_json or args.atlas_html:
                    verify_atlas(args.repo,original,
                        data=json.loads(args.atlas_json.read_text('utf-8')) if args.atlas_json else None,
                        page=args.atlas_html.read_text('utf-8') if args.atlas_html else None)
                result={'schema':'cora-five-synergies-replay/1','commit':original['commit'],
                        'receipt_digest':original['receipt_digest'],
                        'status':'REPLAYED_ORIGINAL_GIT_SOURCE_NOT_PRODUCT',
                        'authorization':'NONE'}
            elif args.integrated:
                ai=json.loads(args.ai_observations.read_text('utf-8')) if args.ai_observations else None
                verify_integrated(args.repo,original,**loaded,ai=ai)
                result={'schema':'cora-integrated-case-replay/1','commit':original['commit'],
                        'report_digest':original['report_digest'],'status':'REPLAYED_SOURCE_NOT_RUNTIME',
                        'authorization':'NONE'}
            else:
                if args.ai_observations:
                    raise ValueError('AI reticular options require --integrated')
                verify_synthesis(args.repo,original,**loaded)
                result = {'schema':'cora-method-synthesis-replay/1',
                          'commit':original['commit'],'receipt_digest':original['receipt_digest'],
                          'status':'REPLAYED_GIT_SOURCE_ONLY','authorization':'NONE'}
            code = 0
        elif args.cmd == 'snapshot':
            result = snapshot(args.repo, args.revision)
            code = 0
        else:
            ledger = json.loads(args.ledger.read_text(encoding='utf-8'))
            validate_ledger(ledger)
            actual = snapshot(args.repo, ledger['commit'])
            if ledger != actual:
                raise ValueError('Git object revalidation mismatch')
            result = {'schema':'cora-ledger-verification/1', 'status':'verified_against_git_objects', 'commit':ledger['commit'], 'ledger_digest':ledger['ledger_digest']}
            code = 0
        rendered = json.dumps(result, sort_keys=True, indent=2, ensure_ascii=True) + '\n'
        if getattr(args,'output',None):
            args.output.write_text(rendered, encoding='utf-8')
        else:
            sys.stdout.write(rendered)
        return code
    except (ValueError, OSError, json.JSONDecodeError, KeyError, TypeError, subprocess.TimeoutExpired, zipfile.BadZipFile) as exc:
        print(f'CORA error: {exc}', file=sys.stderr)
        return 3

if __name__ == '__main__':
    raise SystemExit(main())
