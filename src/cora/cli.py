"""The single supported CORA console entrypoint."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from . import __version__
from .audit import audit, canonical, read_declarations
from .mutations import stress

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="cora", description="Scoped read-only repository evidence")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("version")
    a = sub.add_parser("audit")
    a.add_argument("repo", type=Path)
    a.add_argument("--declarations", default="cora.products.json")
    a.add_argument("--output", type=Path)
    s = sub.add_parser("stress")
    s.add_argument("--seed", type=int, default=883)
    s.add_argument("--cases", type=int, default=1_000_000)
    s.add_argument("--output", type=Path)
    args = p.parse_args(argv)
    try:
        if args.cmd == "version":
            print(__version__)
            return 0
        if args.cmd == "audit":
            result = audit(args.repo, read_declarations(args.repo, args.declarations))
            code = 2 if result["findings"] else 0
        else:
            result = stress(seed=args.seed, cases=args.cases)
            code = 2 if result["mismatches"] else 0
        rendered = json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
        return code
    except (ValueError, OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"CORA error: {exc}", file=sys.stderr)
        return 3

if __name__ == "__main__":
    raise SystemExit(main())
