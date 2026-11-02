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
