"""Deterministic independent oracle for Git batch savings (fixture, not production speed)."""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

from cora import git_snapshot as gs


def run(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(['git','-C',str(repo),*args], stderr=subprocess.PIPE)


def benchmark(count: int = 160) -> dict:
    if type(count) is not int or not 40 <= count <= 1000:
        raise ValueError('fixture count out of bounds')
    with tempfile.TemporaryDirectory(prefix='cora-batch-bench-') as tmp:
        root=Path(tmp)
        run(root,'init','-q')
        run(root,'config','user.name','CORA Fixture')
        run(root,'config','user.email','fixture@invalid.example')
        for i in range(count):
            (root/('blob-%04d.bin'%i)).write_bytes((str(i)+'\0').encode() * (i%31+1))
        run(root,'add','-A')
        run(root,'commit','-qm','deterministic independent Git object oracle')
        sha=run(root,'rev-parse','HEAD').decode().strip()
        listed=run(root,'ls-tree','-rz','--full-tree',sha)
        expected={}
        reference_reads=1
        for entry in listed.split(b'\0'):
            if not entry: continue
            header,path=entry.split(b'\t',1)
            oid=header.split(b' ')[2].decode()
            raw=run(root,'cat-file','blob',oid)
            reference_reads+=1
            expected[path.decode()] = hashlib.sha256(raw).hexdigest()
        original=gs.subprocess.run
        requests=[]
        def track(*args,**kwargs):
            cmd=args[0] if args else kwargs.get('args',[])
            if cmd and cmd[0]=='git':requests.append(cmd)
            return original(*args,**kwargs)
        with patch.object(gs.subprocess,'run',side_effect=track):
            ledger=gs.snapshot(root,sha)
        actual={row['path']:row['sha256'] for row in ledger['records']}
        ok=(expected==actual and len(actual)==count and len(requests)<=5 and
            len([cmd for cmd in requests if 'cat-file' in cmd])<=2)
        return {'schema':'cora-git-batch-benchmark/1','status':'PASS_SCOPED' if ok else 'REFUTED',
                'fixture_files':count,'commit':sha,'oracle_object_reads':reference_reads,
                'batch_git_subprocesses':len(requests),
                'batch_cat_file_processes':len([cmd for cmd in requests if 'cat-file' in cmd]),
                'oracle_matches_batch':expected==actual,
                'scope':'SYNTHETIC_GIT_FIXTURE_ONLY','authorization':'NONE'}


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument('--files',type=int,default=160)
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    result=benchmark(a.files)
    data=json.dumps(result,indent=2,sort_keys=True)+'\n'
    if a.output:a.output.write_text(data,encoding='utf-8')
    else:print(data)
    return 0 if result['status']=='PASS_SCOPED' else 2

if __name__=='__main__':raise SystemExit(main())
