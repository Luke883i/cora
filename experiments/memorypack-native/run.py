#!/usr/bin/env python3
"""Fail-closed native C# baseline/repair experiment; never writes to upstream."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

PIN = '239ffa0df2f7ccad63d276457557b49e88acae4b'
ORIGINAL_SHA256 = 'bc41adf2ea96e6328f7277a9c7eb2de3c8b4f3e82ea12a7fe54142253ff4efe9'
OLD = 'case VarIntCodes.UInt16:\n                return checked((byte)ReadUnmanaged<byte>());'
NEW = 'case VarIntCodes.UInt16:\n                return checked((byte)ReadUnmanaged<ushort>());'
TARGET_TESTS = {
    'UInt16PayloadConsumesAllBytes': ('Failed', 'Passed'),
    'UInt16ValueOverflowIsRejected': ('Failed', 'Passed'),
    'DirectByteWireMarkerRegressionControl': ('Passed', 'Passed'),
}

def sha256(contents):
    return hashlib.sha256(contents).hexdigest()

def read_trx(path):
    root = ET.parse(path).getroot()
    results = {}
    for element in root.iter():
        if element.tag.split('}')[-1] == 'UnitTestResult':
            results[element.attrib.get('testName', '')] = element.attrib.get('outcome', '')
    return results

def require_results(results, phase):
    expected_index = 0 if phase == 'original' else 1
    for name, expected in TARGET_TESTS.items():
        actuals = [v for k, v in results.items() if k == name or k.endswith('.' + name)]
        if actuals != [expected[expected_index]]:
            raise RuntimeError(f'{phase}: expected exactly one {name}={expected[expected_index]}; got {actuals}; all={results}')
    if len(results) != len(TARGET_TESTS):
        raise RuntimeError(f'{phase}: expected exactly three filtered test results, got {results}')

def run_command(args, *, log, cwd):
    result = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=900, check=False)
    log.write_text(result.stdout, encoding='utf-8')
    return result.returncode

def test_phase(source, out, phase, *, no_restore=False, full_suite=False):
    results = out / phase
    results.mkdir(parents=True, exist_ok=True)
    suite = source / 'tests' / 'MemoryPack.Tests' / 'MemoryPack.Tests.csproj'
    args = ['dotnet', 'test', str(suite), '-c', 'Release', '-f', 'net8.0',
            '--results-directory', str(results),
            '--logger', f'trx;LogFileName={phase}.trx']
    if no_restore:
        args.append('--no-restore')
    if not full_suite:
        args.extend(['--filter', 'FullyQualifiedName~NativeVarIntByteContract'])
    code = run_command(args, log=results / 'console.log', cwd=source)
    trx = results / f'{phase}.trx'
    if not trx.exists():
        raise RuntimeError(f'{phase}: dotnet test produced no TRX; code={code}, see {results / "console.log"}')
    return {'returncode': code, 'tests': read_trx(trx), 'trx': str(trx), 'log': str(results / 'console.log')}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    source = a.source.resolve()
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    receipt = {'schema': 'cora-memorypack-native-f4/v1', 'target_repo': 'Cysharp/MemoryPack',
               'pin': PIN, 'status': 'HOLD', 'native_executed': False,
               'authority': 'NONE', 'upstream_mutation': False}
    try:
        revision = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
        if revision != PIN:
            raise RuntimeError(f'unexpected MemoryPack git commit: {revision}')
        src = source / 'src' / 'MemoryPack.Core' / 'MemoryPackReaderWriter.VarInt.cs'
        original = src.read_bytes()
        receipt['source_original_sha256'] = sha256(original)
        if sha256(original) != ORIGINAL_SHA256:
            raise RuntimeError('source file digest mismatch; fail closed')
        original_text = original.decode('utf-8-sig')
        if original_text.count(OLD) != 1:
            raise RuntimeError('expected original VarInt branch exactly once')
        target_test = source / 'tests' / 'MemoryPack.Tests' / 'NativeVarIntByteContract.cs'
        harness = Path(__file__).with_name('NativeVarIntByteContract.cs')
        shutil.copyfile(harness, target_test)
        receipt['harness_sha256'] = sha256(harness.read_bytes())
        receipt['runtime'] = run_command(['dotnet', '--info'], log=out / 'dotnet-info.log', cwd=source)
        baseline = test_phase(source, out, 'original')
        receipt['original'] = baseline
        if baseline['returncode'] == 0:
            raise RuntimeError('baseline unexpectedly passed; hypothesis not reproduced')
        require_results(baseline['tests'], 'original')
        patched_text = original_text.replace(OLD, NEW)
        encoded = ('\ufeff' if original.startswith(b'\xef\xbb\xbf') else '') + patched_text
        src.write_bytes(encoded.encode('utf-8'))
        receipt['source_patched_sha256'] = sha256(src.read_bytes())
        receipt['patch_single_match'] = True
        repaired = test_phase(source, out, 'repaired', no_restore=True)
        receipt['repaired'] = repaired
        if repaired['returncode'] != 0:
            raise RuntimeError('patched regression failed')
        require_results(repaired['tests'], 'repaired')
        full_suite = test_phase(source, out, 'full-suite', no_restore=True, full_suite=True)
        receipt['full_suite'] = full_suite
        if full_suite['returncode'] != 0 or any(x != 'Passed' for x in full_suite['tests'].values()):
            raise RuntimeError('full .NET test suite failed after repair')
        receipt['native_executed'] = True
        receipt['status'] = 'PASS_SCOPED_NATIVE_NET8'
    except Exception as e:
        receipt['error'] = f'{type(e).__name__}: {e}'
        print(receipt['error'], file=sys.stderr)
    finally:
        (out / 'native-receipt.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': receipt['status'], 'source': receipt.get('source_original_sha256'),
                      'error': receipt.get('error')}, sort_keys=True))
    return 0 if receipt['status'] == 'PASS_SCOPED_NATIVE_NET8' else 1

if __name__ == '__main__':
    raise SystemExit(main())
