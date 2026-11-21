#!/usr/bin/env python3
"""Project independently recorded .NET results into CORA's noncompensatory reticulum."""
import argparse
import json
from pathlib import Path
from cora.reticulum import MODEL, BLOCKED, assess_cut

PIN = '239ffa0df2f7ccad63d276457557b49e88acae4b'
NAMES = ['UInt16PayloadConsumesAllBytes', 'UInt16ValueOverflowIsRejected', 'DirectByteWireMarkerRegressionControl']

def expected(results, statuses):
    return isinstance(results, dict) and len(results) == len(statuses) and all(
        results.get(n) == s for n, s in zip(NAMES, statuses))

def evaluate(receipt):
    pin = (receipt.get('pin') == PIN and receipt.get('source_original_sha256') ==
           'bc41adf2ea96e6328f7277a9c7eb2de3c8b4f3e82ea12a7fe54142253ff4efe9')
    before = receipt.get('original', {})
    after = receipt.get('repaired', {})
    full = receipt.get('full_suite', {})
    source_truth = MODEL if pin else BLOCKED
    red_truth = MODEL if before.get('returncode') not in (None, 0) and expected(
        before.get('tests'), ['Failed', 'Failed', 'Passed']) else BLOCKED
    green_truth = MODEL if after.get('returncode') == 0 and expected(
        after.get('tests'), ['Passed'] * 3) else BLOCKED
    full_tests = full.get('tests')
    full_truth = MODEL if full.get('returncode') == 0 and full_tests and all(
        s == 'Passed' for s in full_tests.values()) else BLOCKED
    obs = {'L_PINNED_SOURCE': source_truth, 'L_NATIVE_RED': red_truth,
           'L_NATIVE_GREEN': green_truth, 'L_NATIVE_FULL_SUITE': full_truth}
    nodes = [{'id': 'G_NET8_PATCH_SCOPED', 'depends_on': list(obs)}, *[
        {'id': leaf, 'depends_on': []} for leaf in obs]]
    native = assess_cut(nodes, 'G_NET8_PATCH_SCOPED', obs)
    release_nodes = [{'id': 'G_PRODUCT_RELEASE', 'depends_on': ['L_NATIVE_SCOPED', 'L_RUNTIME_CROSS', 'L_UNITY', 'L_MAINTAINER']},
        {'id': 'L_NATIVE_SCOPED', 'depends_on': []}, {'id': 'L_RUNTIME_CROSS', 'depends_on': []},
        {'id': 'L_UNITY', 'depends_on': []}, {'id': 'L_MAINTAINER', 'depends_on': [], 'scope': 'EXTERNAL'}]
    release = assess_cut(release_nodes, 'G_PRODUCT_RELEASE', {
        'L_NATIVE_SCOPED': MODEL if native['status'] == MODEL else BLOCKED,
        'L_RUNTIME_CROSS': BLOCKED, 'L_UNITY': BLOCKED})
    return {'schema':'cora-memorypack-F4-reticulum/v1','pin': PIN,
            'receipt_status':receipt.get('status','ABSENT'),
            'evidence_class':'CI_RESULT_RECORDED_NOT_CORA_ATTESTED',
            'native':native, 'release':release,
            'authorization':'NONE', 'maintainer_approved':False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--receipt',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    receipt=json.loads(a.receipt.read_text()) if a.receipt.exists() else {}
    report=evaluate(receipt)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(f'CORA native model={report["native"]["status"]} release={report["release"]["status"]}')
    if receipt.get('status') == 'PASS_SCOPED_NATIVE_NET8' and report['native']['status'] != MODEL:
        raise RuntimeError('CORA rejected claimed scoped native PASS')

if __name__=='__main__': main()
