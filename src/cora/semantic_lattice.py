"""Machine-replayable PR-16 obligation DAG. Never certifies sandbox or release."""
from __future__ import annotations

from pathlib import Path
from .archive_intake import verify_intake
from .observation_fusion import fuse_evidence
from .evidence import domain_hash


def lattice_from_evidence(archive: Path, zip_report: dict, *,
                          runtime_report: dict | None = None,
                          source_process: dict | None = None,
                          workspace: Path | None = None) -> dict:
    """A source witness proves ZIP equivalence, not external truth or review."""
    verify_intake(archive, zip_report, workspace=workspace)
    fusion = fuse_evidence(zip_report, runtime_report, source_process)
    status = runtime_report['execution_status'] if runtime_report else 'NOT_SUPPLIED'
    if status == 'RUN_REPORTED_UNATTESTED':
        runtime = 'EXECUTION_REPORTED_UNATTESTED'
    elif status in ('NOT_SUPPLIED', 'NOT_REQUESTED'):
        runtime = 'NOT_OBSERVED'
    else:
        runtime = 'DEBT_BLOCKED'
    nodes = [
      {'id':'G0','depends_on':[],'status':'SOURCE_REPLAY_SCOPED',
       'witness':zip_report['receipt_digest'],
       'unknowns':['COMMIT_HISTORY','ARCHIVE_AUTHOR_AUTHENTICATION']},
      {'id':'G1','depends_on':['G0'],'status':runtime,
       'witness':runtime_report['receipt_digest'] if runtime_report else None,
       'unknowns':['HOST_SANDBOX_ATTESTATION','RUNTIME_COVERAGE','EXTERNAL_SIDE_EFFECTS']},
      {'id':'G2','depends_on':['G0'] + (['G1'] if runtime_report is not None else []),
       'status':'RECONCILED_SCOPED_UNAUTHENTICATED',
       'witness':fusion['fusion_digest'],
       'unknowns':['INDEPENDENT_EXECUTION_PROVENANCE','SOURCE_PROCESS_GIT_LINKAGE']},
      {'id':'G3','depends_on':['G2'],'status':'BLOCKED_EXTERNAL',
       'witness':None,
       'unknowns':['PROTECTED_HOST_REVIEW','INDEPENDENT_REVIEWER','REAL_WORLD_PILOT','ROLLBACK']},
    ]
    gates = [
      {'id':'C5','status':'REQUIRES_HEAD_CI','witness':'verify_repository_contract+verify_artifact_roles'},
      {'id':'C6','status':'REQUIRES_HEAD_CI_AND_RUNTIME_EXTERNAL','witness':'PR16_negative_fixtures'},
      {'id':'C7','status':'REQUIRES_HEAD_CI','witness':'lattice_negative_replay'},
      {'id':'C8','status':'REQUIRES_HEAD_CI','witness':'git_batch_budget+full_regression'},
      {'id':'C9','status':'REQUIRES_GITHUB_PR_CHECKS','witness':'GitHub_checks_same_HEAD'},
    ]
    report = {'schema':'cora-semantic-lattice/1',
              'archive_sha256':zip_report['archive_sha256'],
              'git_tree_sha1':zip_report['git_tree_sha1'],
              'nodes':nodes, 'implementation_gates':gates,
              'fusion_digest':fusion['fusion_digest'],
              'scope':'SOURCE_REPLAY_WITH_OPTIONAL_UNATTESTED_RUNTIME',
              'source_DoD':'PENDING_INDEPENDENT_HEAD_CI',
              'governed_DoD':'BLOCKED_EXTERNAL',
              'runtime_coverage':'NOT_ATTESTED',
              'authorization':'NONE',
              'release_authorized':False,
              'invalidation':'INPUT_ARCHIVE_OR_WITNESS_OR_CODE_CHANGED'}
    report['lattice_digest'] = domain_hash('CORA:semantic-lattice:1', report)
    return report


def verify_lattice(archive: Path, report: dict, *, zip_report: dict,
                   runtime_report: dict | None = None,
                   source_process: dict | None = None,
                   workspace: Path | None = None) -> bool:
    if not isinstance(report,dict) or report.get('schema') != 'cora-semantic-lattice/1':
        raise ValueError('invalid lattice report')
    actual = lattice_from_evidence(archive, zip_report, runtime_report=runtime_report,
                                   source_process=source_process, workspace=workspace)
    if actual != report:
        raise ValueError('semantic lattice differs from original evidence')
    return True
