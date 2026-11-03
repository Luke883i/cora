"""The single supported CORA console entrypoint."""
from __future__ import annotations
import argparse
import json
import sys
import subprocess
from pathlib import Path
from . import __version__
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
from .continuous import evaluate as development_gate, verify_gate, agent_check
from .continuous_stress import stress_continuous
import shlex


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog='cora', description='Scoped, read-only repository evidence')
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('version')
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
    pv = sub.add_parser('verify-process',help='Source revalidation of process receipt')
    pv.add_argument('report',type=Path)
    pv.add_argument('--repo',required=True,type=Path)
    pv.add_argument('--output',type=Path)
    dsx = sub.add_parser('stress-debt',help='1M seeded debt-policy model mutations')
    dsx.add_argument('--seed',type=int,default=883)
    dsx.add_argument('--cases',type=int,default=1000000)
    dsx.add_argument('--output',type=Path)
    gp = sub.add_parser('dev-premerge', help='Git-bound pre-merge risk and reviewer obligations')
    gp.add_argument('repo',type=Path)
    gp.add_argument('--base',required=True)
    gp.add_argument('--head',default='HEAD')
    gp.add_argument('--strict',action='store_true',help='Exit 2 on missing base policy or blockers')
    gp.add_argument('--output',type=Path)
    gm = sub.add_parser('dev-postmerge', help='Post-merge drift and bounded regression obligations')
    gm.add_argument('repo',type=Path)
    gm.add_argument('--previous',required=True)
    gm.add_argument('--head',default='HEAD')
    gm.add_argument('--with-debt',action='store_true')
    gm.add_argument('--strict',action='store_true')
    gm.add_argument('--output',type=Path)
    gv = sub.add_parser('verify-dev-gate', help='Recompute lifecycle evidence from original Git commits')
    gv.add_argument('report',type=Path)
    gv.add_argument('--repo',type=Path,required=True)
    gv.add_argument('--output',type=Path)
    ga = sub.add_parser('agent-check', help='Check coding agent proposal against Git; never approve')
    ga.add_argument('proposal',type=Path)
    ga.add_argument('--repo',type=Path,required=True)
    ga.add_argument('--output',type=Path)
    gs = sub.add_parser('stress-continuous', help='Finite deterministic CI governance model replay')
    gs.add_argument('--seed',type=int,default=883)
    gs.add_argument('--cases',type=int,default=1000000)
    gs.add_argument('--output',type=Path)
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
        if args.cmd == 'version':
            print(__version__)
            return 0
        if args.cmd == 'audit':
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
            result = run_suite(args.repo,args.revision,process=args.process,
                               max_commits=args.max_commits,focus=args.focus)
            code = 0 if result['status']!='DEBT_BLOCKED' else 2
        elif args.cmd == 'verify-process':
            item = json.loads(args.report.read_text(encoding='utf-8'))
            verify_suite(args.repo,item)
            result = {'schema':'cora-process-verification/1','status':'SOURCE_REPLAY_VERIFIED',
                      'run_digest':item['run_digest'],'commit':item['commit']}
            code = 0
        elif args.cmd == 'stress-debt':
            result = stress_debt(seed=args.seed,cases=args.cases)
            code = 2 if result['mismatches'] else 0
        elif args.cmd == 'dev-premerge':
            result = development_gate(args.repo,args.base,args.head,phase='premerge')
            code = 2 if args.strict and result['status'] != 'OBSERVED_REVIEW_REQUIRED' else 0
        elif args.cmd == 'dev-postmerge':
            result = development_gate(args.repo,args.previous,args.head,phase='postmerge',with_debt=args.with_debt)
            code = 2 if args.strict and (result['status'] != 'OBSERVED_REVIEW_REQUIRED' or 'DEBT_COMPARISON_UNAVAILABLE' in result['blockers']) else 0
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
    except (ValueError, OSError, json.JSONDecodeError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        print(f'CORA error: {exc}', file=sys.stderr)
        return 3

if __name__ == '__main__':
    raise SystemExit(main())
