"""Create an unpublished v1.experimental review bundle, reproducible on one builder.

This is not a signed release or a supplier provenance attestation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

FIXED = (1980,1,1,0,0,0)


def bundle(source: Path, dist: Path, output: Path) -> dict:
    source=source.resolve(strict=True)
    dist=dist.resolve(strict=True)
    files = [source/'README.md',source/'GOVERNANCE.md',source/'docs/DOD_V1_EXPERIMENTAL.md',
             source/'docs/ARTIFACT_SEMANTICS.md',source/'cora.ontology.json',
             source/'cora.artifact-roles.json',source/'docs/verification/V1_EXPERIMENTAL_SATURATION.json']
    wheel=sorted(dist.glob('cora_audit-1.0.0a1-*.whl'))
    sdist=sorted(dist.glob('cora_audit-1.0.0a1.tar.gz'))
    if len(wheel)!=1 or len(sdist)!=1:raise ValueError('wheel and sdist 1.0.0a1 required')
    files.extend(wheel+sdist)
    for f in files:
        if not f.is_file() or f.is_symlink():raise ValueError('bundle input missing/symlink:'+str(f))
    entries = {}
    for f in files:
        arc=('dist/'+f.name) if f.parent==dist else f.relative_to(source).as_posix()
        if arc in entries:raise ValueError('bundle collision')
        entries[arc]=f.read_bytes()
    checksums={p:hashlib.sha256(raw).hexdigest() for p,raw in sorted(entries.items())}
    report={'schema':'cora-v1-experimental-review-bundle/1','status':'UNPUBLISHED_REVIEW_ONLY',
            'files':checksums,'scope':'same-source and toolchain; no signed provenance or stable release'}
    entries['MANIFEST.sha256.json']=json.dumps(report,sort_keys=True,indent=2).encode()+b'\n'
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for path,raw in sorted(entries.items()):
            info=zipfile.ZipInfo(path,FIXED)
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=(0o100644<<16)
            z.writestr(info,raw)
    return {'path':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
            'file_count':len(entries),'status':'REVIEW_ONLY_NOT_RELEASE'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=Path('.'));p.add_argument('--dist',type=Path,default=Path('dist'))
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(bundle(a.source,a.dist,a.output),sort_keys=True))
if __name__=='__main__':main()
