# SPDX-License-Identifier: MPL-2.0
"""Unissued PURE worker controls over real guarded UNKNOWN-contact bytes.

The surrounding graph/receipt pins are disclosed software premises. The real
native store contains BEGIN/contact only, and these tests never run science.
"""
from dataclasses import fields, replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_composition as composition
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_closeout_execution import (
    ConfiguredE3CALRootCloseout, ConfiguredE3MissingOutcomeConfig, ConfiguredE3MissingOutcomeProducts,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_continued_response import ConfiguredE3ContinuedResponseConfig
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_unknown_response import score_unknown_response
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_execution import source_binding
from empirical_lawhood.infrastructure.execution import prepare_worker_invocation
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
from empirical_lawhood.runtime.execution import TaskContext, VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, ExecutionPlan, ExecutionTask, ExternalInputSpec, ScientificInputRole, ScientificInputSpec
from tests.test_matrix_configured_unknown_response import (
    case as unknown_case, configured_prefix_case, legacy_case, original_case, no_science, _pin,  # noqa: F401
)
from tests.test_matrix_e3_cal_closeout import closeout_case, unfinished_case, continuation_case, public_case  # noqa: F401
from tests.test_matrix_factor_confirmation_eligibility import _matrix_plane
from tests.worker_configuration_support import freeze_worker_configuration


@pytest.fixture(scope='module')
def worker_premises(closeout_case, unknown_case):  # noqa: F811
    """One literal prepared worker, separate from the full compiler control."""
    old = closeout_case.scope
    original_retention = replace(old.original_boundary.retention,
        specification=unknown_case.specification.identity, allocation=unknown_case.allocation.identity)
    boundary = replace(old.original_boundary, retention=original_retention)
    retention = replace(old.retention, specification=original_retention.specification, allocation=original_retention.allocation)
    original = unknown_case.operands.config
    config = ConfiguredE3ContinuedResponseConfig(**{field.name: getattr(original, field.name) for field in fields(original)},
        continuation=original_retention.identity)
    score, outcome = score_unknown_response(unknown_case.availability, unknown_case.operands,
        score_id='score.disclosed.closeout', outcome_id='outcome.disclosed.closeout')
    products = ConfiguredE3MissingOutcomeProducts('products.disclosed.closeout', retention.response_provenance,
        config, unknown_case.availability, score, outcome, Visibility.DEVELOPMENT_ONLY)
    root = config.source.root.root
    row = ConfiguredE3CALRootCloseout(root.root_id, root.independent_group_id,
        ObjectIdentity.from_record(config.config_id, config), ObjectIdentity.from_record(
            'native-contact.' + unknown_case.availability.parent_contact.task_id, unknown_case.availability.parent_contact),
        None, None, products.identity, len(products.canonical_bytes()), products.visibility_ceiling)
    scope = replace(old, original_boundary=boundary, retention=retention,
        calibration_units=(row.unit_id,), calibration_roots=(row,),
        imported_outputs=tuple(value for value in old.imported_outputs
            if value.task_id not in (row.native_task_id, row.outcome_task_id)),
        completed_receipts=tuple((node, receipt) for node, receipt in old.completed_receipts
            if node not in (row.native_task_id, row.outcome_task_id)),
        unfinished_task_ids=tuple(sorted((set(old.unfinished_task_ids) | {row.outcome_task_id}) - {row.native_task_id})))
    config = ConfiguredE3MissingOutcomeConfig(**{**{field.name: getattr(config, field.name) for field in fields(config)},
        'operation': 'response-score', 'config_id': 'config.' + row.outcome_task_id, 'continuation': retention.identity},
        closeout=scope.identity, products=products.identity)
    return SimpleNamespace(scope=scope, config=config, products=products, row=row)


def prepared_worker(premises, directory, *, damage=None):
    plane = _matrix_plane(directory / 'closeout-worker')
    declaration, = (row for row in composition.operation_declarations() if row.capability_key.endswith('.missing-response-score'))
    runner, manifest = declaration.runner_factory(), declaration.manifest()
    records = {'closeout': premises.scope, 'products': premises.products, 'config': premises.config}
    verified, edges = [], []
    for name, record in records.items():
        key = premises.config.config_id if name == 'config' else 'disclosed.closeout.' + name
        visibility = premises.products.visibility_ceiling if name == 'products' else Visibility.PROSPECTIVE
        access = Access.EVALUATION_SEALED if name == 'products' else Access.OUTCOME_BLIND
        if damage == 'visibility' and name == 'products':
            visibility = Visibility.PROSPECTIVE
        publication = plane.write(ArtifactWriteRequest(key, 'inputs/' + name + '.json', record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', 'publication.disclosed.closeout', 'inputs',
            record.canonical_bytes(), visibility, (), access))
        verified.append(VerifiedArtifactInput(publication.logical, publication.materialization))
        if name != 'config':
            edges.append(ScientificInputSpec('edge.closeout.' + name, name,
                ScientificInputRole.HISTORY if name == 'products' else ScientificInputRole.SOURCE,
                None, None, 'external.' + name, key, key, record.SCHEMA, 'application/json',
                publication.materialization.size_bytes, access, visibility, BarrierKind.NONE))
    verified = tuple(sorted(verified, key=lambda row: row.artifact_id))
    bindings = tuple(WorkerInputBinding.from_verified(row, kind=WorkerInputKind.EXTERNAL) for row in verified)
    ports = plane.open_many(verified, bindings=bindings, maximum_bytes=None)
    task_id = premises.row.outcome_task_id
    outputs = tuple(WorkerOutputPort(task_id + '.' + row.output_id, row.payload_schema, row.profile,
        row.media_type, 'artifact.disclosed.' + row.output_id) for row in declaration.outputs)
    config = premises.config
    reference = CapabilityConfigRef(config.config_id, config.SCHEMA, manifest.config_schema_sha256,
        config.fingerprint(), config.config_id)
    context = TaskContext(premises.scope.retention.continued_run_id, task_id, 'attempt.disclosed.closeout',
        reference, bindings, ports, outputs, manifest.permissions, Access.EVALUATION_SEALED,
        manifest.resource_ceiling, WorkerIsolationProfile.TRUSTED_LOCAL)
    external = tuple(sorted((ExternalInputSpec('input.' + row.artifact_id, row.artifact_id,
        row.logical.content_sha256, row.logical.payload_schema, row.logical.media_type, row.materialization.size_bytes,
        row.logical.visibility_ceiling, row.logical.outcome_access, None) for row in verified), key=lambda row: row.input_id))
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind,
        reference, manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions,
        manifest.maximum_evidence_ceiling, Access.EVALUATION_SEALED, manifest.resource_ceiling)
    ceiling = Visibility.PROSPECTIVE if damage == 'visibility' else Visibility.DEVELOPMENT_ONLY
    task = freeze_worker_configuration(ExecutionTask(task_id, declaration.stage, requirement,
        manifest.implementation_sha256, (), external,
        tuple(ArtifactOutputSpec(row.output_id, row.logical_artifact_id, 'outputs/' + row.output_id,
            row.payload_schema, row.profile, row.media_type, ceiling, (), Access.EVALUATION_SEALED) for row in outputs),
        (), BarrierKind.NONE, 1, ('obligation.disclosed.closeout',), scientific_inputs=tuple(edges)))
    implementation = source_binding(premises.scope.retention.response_provenance)
    if damage == 'source':
        implementation = premises.scope.predecessor_source
    prepared = prepare_worker_invocation(runner, context, verified, implementation=implementation,
        execution_plan=_pin('plan.disclosed.closeout', ExecutionPlan),
        execution_task=ObjectIdentity.from_record(task.task_id, task), execution_task_record=task)
    return runner, replace(context, prepared_invocation=prepared), plane


@pytest.mark.parametrize('damage', (None, 'source', 'visibility'))
def test_missingness_worker_retains_original_unknown_and_separate_source(worker_premises, unknown_case, tmp_path, damage):  # noqa: F811
    before = unknown_case.native.inspect(unknown_case.availability.definition)
    runner, context, _ = prepared_worker(worker_premises, tmp_path, damage=damage)
    try:
        if damage:
            with pytest.raises(PermissionError, match='source|visibility'):
                runner.execute(context)
        else:
            result = runner.execute(context)
            outputs = {row.output_id.rsplit('.', 1)[-1]: row.payload for row in result.outputs}
            assert outputs == {name: getattr(worker_premises.products, name).canonical_bytes() for name in ('score', 'outcome')}
            assert not context.prepared_invocation.native_effect and all(row.passed for row in result.checks)
            assert decode_canonical_bytes(worker_premises.products.canonical_bytes(),
                ConfiguredE3MissingOutcomeProducts, maximum_bytes=worker_premises.row.missing_products_bytes) == worker_premises.products
    finally:
        for port in context.input_ports:
            port.close()
    assert unknown_case.native.inspect(unknown_case.availability.definition) == before
    assert before.completion is before.receipt is None


def test_closeout_rechecks_previously_absent_native_return(unknown_case):  # noqa: F811
    """A real new orphan witness must refuse the previously read UNKNOWN state."""
    from empirical_lawhood.api.configured_e3_closeout_custody import _require_unknown_current
    from empirical_lawhood.infrastructure.native_subwork import NativeSubworkUncertainContact

    case = unknown_case
    original = case.native.inspect(case.availability.definition)
    evidence = {case.availability.parent_contact.task_id: {'availability': case.availability,
        'call_entry': original.call_entry, 'call_return': original.call_return}}
    path = case.native.plane.root.resolve(case.native._root(case.availability.definition) + '/call-return.json', for_write=True)
    assert not path.exists()
    with case.native.plane.read_context() as writer:
        _require_unknown_current(writer, case.native.parent_contacts, evidence)
        try:
            with path.open('xb') as stream:
                stream.write(b'disclosed orphan witness; not a native return')
            with pytest.raises(NativeSubworkUncertainContact, match='partial|lost'):
                _require_unknown_current(writer, case.native.parent_contacts, evidence)
        finally:
            path.unlink()
    assert case.native.inspect(case.availability.definition) == original


def test_closeout_rechecks_previously_absent_parent_output(tmp_path):
    from empirical_lawhood.api.configured_e3_closeout_custody import _require_unpublished_outputs

    plane = _matrix_plane(tmp_path / 'unpublished')
    task = SimpleNamespace(outputs=(SimpleNamespace(relative_path='late-parent-output'),))
    _require_unpublished_outputs(plane, {'disclosed.missing': task}, {})
    path = plane.root.resolve('late-parent-output', for_write=True)
    path.write_bytes(b'disclosed late output; not a scientific completion')
    with pytest.raises(PermissionError, match='unreceipted parent outputs'):
        _require_unpublished_outputs(plane, {'disclosed.missing': task}, {})
