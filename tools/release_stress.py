"""CORA PR07 deterministic finite-model release-risk adversarial mutations.

One million DIFFERENT 20-axis states, NOT one million rebuilt/published artifacts.
24 contextual mutation families; separate finite contract oracle.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from dataclasses import dataclass

FAMILIES = (
 'metadata_name_substitution','metadata_version_drift','sdist_source_omission',
 'wheel_payload_swap','record_digest_tampering','entrypoint_duplicate',
 'unsafe_wheel_traversal','sdist_symlink_escape','license_omitted',
 'source_payload_divergence','cross_commit_replay','tag_mismatch',
 'unreproducible_rebuild','unsigned_artifact','isolated_wheel_install_failure',
 'independent_oracle_mismatch','unknown_non_python_runtime','unmapped_external_consumer',
 'untrusted_release_source','premature_publication','different_backend_version',
 'toolchain_changed','disconnected_build_attestation','matching_release_candidate'
)
# Each variant has 20 axes: 0..12,14,15,18,19 fatal; 13,16,17 uncertain.
CONTRACT = {
 'fatal': (0,1,2,3,4,5,6,7,8,9,10,11,12,14,15,18,19),
 'uncertain': (13,16,17)
}
ACTIVE = (
 (0,2,9,15), (1,11,12), (2,9,10), (3,4,9), (4,3,8), (5,3,14),
 (6,3,14), (7,2,14), (8,9,11), (9,2,3), (10,1,18), (11,12,18),
 (12,9,13), (13,14,16), (14,15,9), (15,16,17),
 (16,17,13), (17,16,13), (18,19,15), (19,18,14),
 (12,13,9), (12,14,13), (13,18,17), (0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19)
)
MASK=(1<<20)-1

def mix64(x: int) -> int:
    x=(x+0x9E3779B97F4A7C15)&((1<<64)-1)
    x=((x^(x>>30))*0xBF58476D1CE4E5B9)&((1<<64)-1)
    x=((x^(x>>27))*0x94D049BB133111EB)&((1<<64)-1)
    return x^(x>>31)


def classify_model(mask: int, family: int) -> tuple[str,list[str]]:
    if not 0<=mask<=MASK or not 0<=family<24:raise ValueError('invalid state')
    hazards=[i for i in ACTIVE[family] if mask & (1<<i)]
    fatal = [i for i in hazards if i in CONTRACT['fatal']]
    uncertain = [i for i in hazards if i in CONTRACT['uncertain']]
    if fatal:return 'REJECTED', [f'gate:{i:02d}' for i in fatal]
    if uncertain:return 'HELD', [f'gate:{i:02d}' for i in uncertain]
    return 'CANDIDATE_SCOPED', []


def independent_oracle(mask: int, family:int) -> str:
    # Mask arithmetic (not using classify_model, hazards or output objects).
    active=0
    for bit in ACTIVE[family]:active |= 1<<bit
    bad=0
    for bit in CONTRACT['fatal']:bad |= 1<<bit
    unknown=0
    for bit in CONTRACT['uncertain']:unknown |= 1<<bit
    return ('REJECTED' if mask & active & bad else
            'HELD' if mask & active & unknown else 'CANDIDATE_SCOPED')


def stress(seed:int=883,cases:int=1_000_000) -> dict:
    if type(seed) is not int or type(cases) is not int or not 1<=cases<=1_000_000:
        raise ValueError('bad stress params')
    stream=hashlib.sha256()
    counts={x:0 for x in ('REJECTED','HELD','CANDIDATE_SCOPED')}
    families={x:0 for x in FAMILIES}
    mismatches=0
    for i in range(cases):
        mask=(i ^ (seed & MASK))
        family=mix64(i+seed)%len(FAMILIES)
        observed,proof=classify_model(mask,family)
        expected=independent_oracle(mask,family)
        if observed!=expected:mismatches+=1
        if observed=='CANDIDATE_SCOPED' and proof:mismatches+=1
        if observed!='CANDIDATE_SCOPED' and not proof:mismatches+=1
        counts[observed]+=1
        families[FAMILIES[family]]+=1
        stream.update(i.to_bytes(4,'little')+mask.to_bytes(4,'little')+bytes([family])+observed.encode()+b'|'+','.join(proof).encode()+b'\n')
    return {'schema':'cora-pr07-release-stress/1','seed':seed,'cases':cases,
            'distinct_risk_vectors':cases,'families':len(FAMILIES),'mismatches':mismatches,
            'outcomes':counts,'distribution':families,'stream_sha256':stream.hexdigest(),
            'oracle':'separate-bitwise-contract','scope':'synthetic finite release risk vectors, not real-world artifact or repository mutations'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int,default=883)
    p.add_argument('--cases',type=int,default=1_000_000);p.add_argument('--output',type=str)
    args=p.parse_args();result=json.dumps(stress(args.seed,args.cases),sort_keys=True,indent=2)+'\n'
    if args.output:open(args.output,'w').write(result)
    else:print(result,end='')
if __name__=='__main__':main()
