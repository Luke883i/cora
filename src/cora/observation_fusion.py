"""Conservative evidence fusion: authenticated source identity != authenticated runtime."""
from __future__ import annotations

from .archive_intake import verify_intake
from .runtime_observation import verify_runtime_receipt
from .evidence import domain_hash


def fuse_evidence(zip_report: dict, runtime_report: dict | None = None,
                  source_process: dict | None = None) -> dict:
    if not isinstance(zip_report,dict) or zip_report.get('schema')!='cora-zip-intake/1':
        raise ValueError('invalid source intake for fusion')
    if zip_report.get('receipt_digest') != domain_hash('CORA:zip-intake:1',
           {k:v for k,v in zip_report.items() if k!='receipt_digest'}):
        raise ValueError('ZIP source receipt altered')
    if runtime_report is not None:
        verify_runtime_receipt(runtime_report)
        if (runtime_report['archive_sha256'] != zip_report['archive_sha256'] or
            runtime_report['git_tree_sha1'] != zip_report['git_tree_sha1']):
            raise ValueError('cross-archive runtime observation mismatch')
    if source_process is not None:
        if not isinstance(source_process,dict) or source_process.get('schema') != 'cora-process-run/1':
            raise ValueError('unsupported source-process receipt')
        if source_process.get('run_digest') != domain_hash('CORA:process-run:1',
                {k:v for k,v in source_process.items() if k!='run_digest'}):
            raise ValueError('source process digest tampered')
        if source_process.get('authorized_action')!='NONE':
            raise ValueError('source process cannot authorize change')
    r={
        'schema':'cora-observation-fusion/1',
        'archive_sha256':zip_report['archive_sha256'],
        'git_tree_sha1':zip_report['git_tree_sha1'],
        'archive_receipt_digest':zip_report['receipt_digest'],
        'runtime_receipt_digest':runtime_report['receipt_digest'] if runtime_report else None,
        'source_run_digest':source_process['run_digest'] if source_process else None,
        'source_git_history':'UNAVAILABLE_FROM_ZIP',
        'source_process_provenance':'INDEPENDENT_GIT_ANCESTRY_NOT_ATTESTED' if source_process else 'NOT_SUPPLIED',
        'runtime_result':runtime_report['execution_status'] if runtime_report else 'NOT_SUPPLIED',
        'observed_test_exit_code':runtime_report['exit_code'] if runtime_report else None,
        'runtime_coverage':'NOT_ATTESTED',
        'external_consumers':'NOT_ATTESTED',
        'independent_review':'NOT_ATTESTED',
        'claim':'SOURCE_AND_OPTIONAL_RUNTIME_REPORTS_RECONCILED_WITH_UNVERIFIED_GAPS',
        'authorization':'NONE',
        'release_authorized':False,
    }
    r['fusion_digest']=domain_hash('CORA:observation-fusion:1',r)
    return r


def verify_fusion(zip_report: dict, fusion: dict, runtime_report: dict | None=None,
                  source_process: dict | None=None) -> bool:
    if fusion!=fuse_evidence(zip_report,runtime_report,source_process):
        raise ValueError('fusion report cannot be reproduced from input evidence')
    return True
