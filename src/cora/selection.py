"""Read-only, Git-verified, conservative per-file *selection for investigation*.

Never calls a transformer. 'Selected' means an investigation queue item, not
'proven dead' or 'eligible for deletion'. Both AI and runtime annotations are
excluded from the source-verifiable decision.
"""
from __future__ import annotations

from pathlib import Path
from .evidence import domain_hash, valid_path
from .file_lab import examine_file

SCHEMA = 'cora-file-selection/1'
POLICY = 'cora-selection-policy/1'
PROTECTED_ROLES = frozenset({
    'PRODUCT_CONTRACT', 'ENTRYPOINT', 'TEST', 'CONTRACT_VERIFIER',
    'CONTRACT_SCHEMA', 'FIXTURE', 'WORKFLOW', 'POLICY',
    'GOVERNANCE', 'RELEASE_TOOL', 'BUILD_METADATA',
    'ARTIFACT_INDEX', 'LICENSE', 'OBSERVABILITY',
})
# Known absence claims are never constructed, even when no references are found.
UNPROVEN_GLOBAL = (
    'cross_repository_and_external_consumers',
    'dynamic_dispatch_and_plugin_resolution',
    'build_deploy_registry_configuration_closure',
    'all_runtime_paths_and_traffic',
    'data_retention_and_historical_migrations',
    'behavior_equivalence_and_recovery',
    'independent_human_approval_and_enforced_checks',
)


def selection_from_dossier(lab: dict) -> dict:
    """Conservative projection of one immutable, unannotated CORA dossier.

    Pure policy used solely after source-bound verification; the input is not a
    self-sufficient provenance certificate. No destructive authority is present.
    """
    if (not isinstance(lab, dict) or lab.get('schema') != 'cora-file-lab/1'
            or lab.get('ai', {}).get('status') != 'NOT_SUPPLIED'
            or lab.get('levels', {}).get('L5_operational', {}).get('runtime') != 'NOT_SUPPLIED'):
        raise ValueError('selection requires unannotated committed-Git lab evidence')
    record = lab['blob_record']
    roles = lab['artifact_roles']
    incoming = lab['levels']['L1_code']['incoming_python_import_candidates']
    entrypoint = lab['levels']['L3_product']['entrypoint']
    triggers: list[str] = []
    if entrypoint:
        triggers.append('declared_entrypoint')
    if incoming:
        triggers.append('static_import_candidate_inbound')
    protected = sorted(PROTECTED_ROLES.intersection(roles['roles']))
    triggers.extend('declared_role:' + role for role in protected)
    unknown = sorted({o['id'] for o in lab['unresolved_obligations']} | set(UNPROVEN_GLOBAL))
    if record['status'] != 'observed_git_blob':
        state = 'DEBT_BLOCKED'
        reason = 'committed Git object is unresolved'
    elif lab['graph_digest'] is None or roles['status'] in ('UNDECLARED','UNCLASSIFIED'):
        state = 'DEBT_BLOCKED'
        reason = 'minimum ontology, graph or committed artifact-role declaration missing'
    elif any(f['kind'] == 'ambiguous_product_membership' for f in lab['levels']['L1_code']['unresolved']):
        state = 'DEBT_BLOCKED'
        reason = 'conflicting product ownership declarations'
    elif triggers:
        state = 'RETAIN_EVIDENCED'
        reason = 'positive reference, entrypoint or protected *declared* role requires retention review'
    elif not lab['levels']['L3_product']['owner_declarations']:
        state = 'DEBT_BLOCKED'
        reason = 'no declared product ownership for the file'
    else:
        state = 'INVESTIGATE'
        reason = 'no positive reference observed in a partial model; this is NOT dead-code proof'
    if roles['status'] in ('UNDECLARED','UNCLASSIFIED'):
        unknown = sorted(set(unknown) | {'artifact_role_declaration_missing'})
    return {
        'state': state,
        'positive_triggers': sorted(set(triggers)),
        'unclosed_obligations': unknown,
        'selected_for_investigation': state == 'INVESTIGATE',
        'dead_code_proven': False,
        'safe_deletion_proven': False,
        'authorized_action': 'NONE',
        'reason': reason,
    }


def select_file(repo: Path, path: str, *, revision: str = 'HEAD',
                ontology_path: str = 'cora.ontology.json') -> dict:
    """Select one Git-tracked file for *review*, not for removal."""
    if not valid_path(path):
        raise ValueError('invalid relative subject path')
    lab = examine_file(repo, path, revision=revision, ontology_path=ontology_path)
    decision = selection_from_dossier(lab)
    result = {
        'schema': SCHEMA,
        'policy': POLICY,
        'commit': lab['commit'],
        'path': path,
        'ontology_path': ontology_path,
        'lab_digest': lab['lab_digest'],
        'ledger_digest': lab['ledger_digest'],
        'graph_digest': lab['graph_digest'],
        'blob_record_digest': lab['blob_record']['digest'],
        'artifact_role_manifest_digest': lab['artifact_roles']['manifest_digest'],
        'selection': decision,
        'effect': 'READ_ONLY_HUMAN_REVIEW_QUEUE',
        'epistemic_boundary': 'absence_in_partial_graph_is_not_proof_of_nonuse',
    }
    result['selection_digest'] = domain_hash('CORA:selection:1', result)
    return result


def verify_selection(repo: Path, selection: dict) -> bool:
    """Refuse self-resigned forgeries by reproducing the result from Git."""
    if not isinstance(selection, dict) or selection.get('schema') != SCHEMA:
        raise ValueError('invalid selection contract')
    digest = selection.get('selection_digest')
    if digest != domain_hash('CORA:selection:1', {k:v for k,v in selection.items() if k != 'selection_digest'}):
        raise ValueError('selection digest mismatch')
    expected = select_file(repo, selection['path'], revision=selection['commit'],
                           ontology_path=selection['ontology_path'])
    if selection != expected:
        raise ValueError('selection is not reproducible from committed Git evidence')
    return True
