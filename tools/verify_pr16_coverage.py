"""Scoped branch + line coverage floor, with named critical-module witnesses."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

CRITICAL=(
 'src/cora/cli.py','src/cora/continuous.py','src/cora/guard_runtime.py',
 'src/cora/debt.py','src/cora/git_snapshot.py','src/cora/archive_intake.py',
 'src/cora/runtime_observation.py','src/cora/observation_fusion.py',
 'src/cora/semantic_lattice.py',
)


def verify(path: Path, *, min_total: float=80.0, min_critical: float=70.0) -> dict:
    data=json.loads(path.read_text(encoding='utf-8'))
    files=data.get('files',{})
    total=data.get('totals',{}).get('percent_covered')
    missing=[]
    below=[]
    for rel in CRITICAL:
        match=next((v for k,v in files.items() if k.replace('\\','/').endswith(rel)),None)
        if match is None:missing.append(rel)
        elif match.get('summary',{}).get('percent_covered',0)<min_critical:
            below.append({'path':rel,'coverage':round(match['summary']['percent_covered'],2)})
    passed=isinstance(total,(int,float)) and total>=min_total and not missing and not below
    return {'schema':'cora-coverage-floor/1','status':'PASS_SCOPED' if passed else 'REFUTED',
            'total_coverage':round(total,2) if isinstance(total,(int,float)) else None,
            'minimum_total':min_total,'minimum_critical':min_critical,
            'critical_modules':list(CRITICAL),'missing':missing,'below_floor':below,
            'scope':'THIS_UNIT_TEST_RUN_WITH_BRANCH_COVERAGE_NOT_PRODUCTION','authorization':'NONE'}


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument('coverage_json',type=Path)
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    report=verify(a.coverage_json)
    data=json.dumps(report,indent=2,sort_keys=True)+'\n'
    if a.output:a.output.write_text(data,encoding='utf-8')
    else:print(data)
    return 0 if report['status']=='PASS_SCOPED' else 2

if __name__=='__main__':raise SystemExit(main())
