"""Build distribution pair via the declared PEP 517 backend without publishing."""
from __future__ import annotations
import argparse
import gzip
import io
import tarfile
import os
import subprocess
import sys
from pathlib import Path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,default=Path('.'))
    parser.add_argument('--outdir',type=Path,required=True)
    args=parser.parse_args()
    src=args.source.resolve(strict=True)
    out=args.outdir.resolve()
    out.mkdir(parents=True,exist_ok=True)
    if (src/'pyproject.toml').is_file() is False:raise SystemExit('no pyproject')
    # Fresh subprocess keeps setuptools build backend isolated from importer state.
    script='import os,setuptools.build_meta as b; b.build_sdist(os.environ["CORA_DIST"]); b.build_wheel(os.environ["CORA_DIST"])'
    env={**os.environ, 'CORA_DIST':str(out), 'SOURCE_DATE_EPOCH':'1735689600', 'PYTHONDONTWRITEBYTECODE':'1'}
    subprocess.run([sys.executable,'-c',script],cwd=src,env=env,check=True)
    # Setuptools may embed wall-clock mtimes in the sdist even with SOURCE_DATE_EPOCH.
    # Repackage only tar headers and gzip metadata; preserve payload bytes unchanged.
    for path in out.glob('*.tar.gz'):
        tmp=path.with_suffix('.normalized.tmp')
        with tarfile.open(path,'r:gz') as input_tar:
            entries=[(m,input_tar.extractfile(m).read() if m.isfile() else None) for m in input_tar.getmembers()]
        with tmp.open('wb') as file:
            with gzip.GzipFile(filename='',fileobj=file,mode='wb',mtime=0,compresslevel=9) as gz:
                with tarfile.open(fileobj=gz,mode='w',format=tarfile.PAX_FORMAT) as output_tar:
                    for old,contents in sorted(entries,key=lambda v:v[0].name):
                        new=tarfile.TarInfo(old.name)
                        new.type=old.type
                        new.size=len(contents) if contents is not None else 0
                        new.mtime=1735689600
                        new.mode=0o755 if old.isdir() else 0o644
                        new.uid=new.gid=0
                        new.uname=new.gname=''
                        new.linkname=old.linkname
                        output_tar.addfile(new,io.BytesIO(contents) if contents is not None else None)
        tmp.replace(path)
    print('\n'.join(str(x) for x in sorted(out.iterdir())))

if __name__=='__main__':main()
