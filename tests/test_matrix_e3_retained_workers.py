# SPDX-License-Identifier: MPL-2.0
"""Real prepared pure-copy workers over disclosed, unissued literal evidence."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_composition as composition
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_source_records import ConfiguredProtectedE3SourceConfig, ProtectedE3SourcePhase as Phase, source_task_id
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_methods import ConfiguredProtectedE3FrozenProducts
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_execution import ConfiguredE3RetainedExecution, ConfiguredE3RetainedTaskConfig, source_binding
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_bindings import retained_input_id
from empirical_lawhood.infrastructure.execution import prepare_worker_invocation
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
from empirical_lawhood.runtime.execution import DependencyReceiptBinding, TaskContext, VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.input_access import validated_task_scientific_input_edges
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, ExecutionPlan, ExecutionTask, ExternalInputSpec, ScientificInputRole, ScientificInputSpec
from empirical_lawhood.runtime.recovery import RunRecoveryTerminalEvent
from tests.test_matrix_configured_protected_prefix_worker_routing import configured_prefix_case, prepare_literal_case  # noqa: F401
from tests.test_matrix_e3_protected_prefix_workers import case as legacy_case, original_case, forbid_native, _matrix_plane  # noqa: F401
from tests.test_matrix_e3_retained_continuation import _changed_source, _pin
from tests.worker_configuration_support import freeze_worker_configuration


def prepared_copy(case, monkeypatch, directory, damage):
    (directory / 'original').mkdir()
    original = prepare_literal_case(case, Phase.NUMERICAL, monkeypatch, directory / 'original', qualified_outputs=True)
    old_inputs = {value.artifact_id: value for value in original.bundle.verified_inputs}
    payloads = {key: (directory / 'original' / 'guarded-inputs' / value.materialization.relative_path).read_bytes()
        for key, value in old_inputs.items()}
    old_config = decode_canonical_bytes(payloads[original.context.config.artifact_id], ConfiguredProtectedE3SourceConfig, maximum_bytes=None)
    result = original.runner.execute(original.context)
    original.bundle.close()
    plane = _matrix_plane(directory / 'continued')
    output_raw = {row.output_id: row.payload for row in result.outputs}
    outputs = tuple(plane.write(ArtifactWriteRequest(row.logical_artifact_id, row.relative_path, row.payload_schema,
        row.profile, row.media_type, 'disclosed.original-products', 'worker-output', output_raw[row.output_id],
        row.visibility_ceiling, (), row.outcome_access)) for row in original.task.outputs)
    original_receipt = CanonicalTaskReceipt('receipt.disclosed-original', original.context.run_id, original.task.task_id,
        original.context.attempt_id, case.source.provenance.observed_git_head,
        tuple(sorted(value.materialization.materialization_id for value in old_inputs.values())),
        tuple(value.materialization for value in outputs), tuple(value.logical for value in outputs), (), OperationalStatus.SUCCEEDED, ())
    from empirical_lawhood.api.matrix_numerical_provenance import capture_matrix_provenance
    inventory = capture_matrix_provenance(project_root=Path(__file__).parents[1])
    # The literal prefix fixture has a deliberately tiny source inventory.
    # This unissued worker premise supplies a complete byte inventory under its
    # disclosed fictional revision; only the separate original reader can
    # authenticate a real producer. No source qualification is constructed.
    provenance = replace(case.source.provenance, package_sources=inventory.package_sources,
        code_sources_sha256=inventory.code_sources_sha256)
    current = _changed_source(provenance)
    prefix_task = source_task_id(case.source.root_id, Phase.PREFIX)
    prefix_array = replace(case.history.arrays.array_artifact,
        artifact_id='artifact.' + original.context.run_id + '.' + prefix_task + '.arrays')
    retention = ConfiguredE3RetainedExecution('retention.disclosed-worker', 'disclosed/original', original.context.run_id,
        'run.disclosed-continuation', ObjectIdentity('package.disclosed', 'empirical-lawhood/api/experiment-package', '1.0.0', 'a' * 64),
        _pin('plan.disclosed', ExecutionPlan), _pin('terminal.disclosed', RunRecoveryTerminalEvent),
        ObjectIdentity('reveal.disclosed', 'empirical-lawhood/planning/study-operation-authority', '1.0.0', 'a' * 64),
        source_binding(provenance), current, case.specification.identity, _pin('allocation.disclosed', UnitAllocation),
        _pin('freeze.disclosed', ConfiguredProtectedE3FrozenProducts),
        tuple(sorted(((original.task.task_id, ObjectIdentity.from_record(original_receipt.receipt_id, original_receipt)),
            (prefix_task, _pin('receipt.disclosed-prefix-premise', CanonicalTaskReceipt))))), ((prefix_task, prefix_array),))
    config = ConfiguredE3RetainedTaskConfig('config.retained.' + original.task.task_id, retention.identity,
        old_config, original.task, original_receipt)
    declaration, = (row for row in composition.operation_declarations() if row.capability_key.endswith('.retained-numerical'))
    manifest, runner = declaration.manifest(), declaration.runner_factory()
    verified, kinds, edges = [], {}, []

    def publish(key, raw, schema, profile, media, *, dependency=False):
        value = plane.write(ArtifactWriteRequest(key, 'copy-inputs/' + key + '.json', schema, profile, media,
            'disclosed.continued-operands', 'copy-inputs', raw, VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
        verified.append(VerifiedArtifactInput(value.logical, value.materialization))
        kinds[key] = WorkerInputKind.DEPENDENCY if dependency else WorkerInputKind.EXTERNAL
        return value

    for edge in validated_task_scientific_input_edges(original.task):
        prior = old_inputs[edge.operational_logical_artifact_id]
        key = edge.operational_logical_artifact_id if edge.producer_task_id is None else (
            'artifact.' + retention.continued_run_id + '.' + edge.producer_task_id + '.' + edge.producer_output_id.rsplit('.', 1)[-1])
        publish(key, payloads[edge.operational_logical_artifact_id], prior.logical.payload_schema,
            prior.logical.profile, prior.logical.media_type, dependency=edge.producer_task_id is not None)
        edge = replace(edge, operational_logical_artifact_id=key)
        if damage == 'producer' and edge.producer_task_id is not None:
            edge = replace(edge, producer_task_id='foreign.producer', producer_output_id='foreign.producer.product')
        edges.append(edge)
    for port, key, raw, schema in (
            ('retention', retention.record_id, retention.canonical_bytes(), retention.SCHEMA),
            ('retained-product', retained_input_id(outputs[0].logical),
                (replace(case.numerical, record_id='numerical.disclosed-substitution').canonical_bytes()
                    if damage == 'copy-bytes' else output_raw[original.task.outputs[0].output_id]), outputs[0].logical.payload_schema)):
        value = publish(key, raw, schema, ArtifactProfile.CANONICAL_JSON, 'application/json')
        edges.append(ScientificInputSpec('edge.copy.' + port, port, ScientificInputRole.SOURCE, None, None,
            'external.' + port, key, key, schema, 'application/json', value.materialization.size_bytes,
            OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, BarrierKind.NONE))
    publish(config.record_id, config.canonical_bytes(), config.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json')
    verified = tuple(sorted(verified, key=lambda row: row.artifact_id))
    bindings = tuple(WorkerInputBinding.from_verified(row, kind=kinds[row.artifact_id]) for row in verified)
    dependent = {}
    for edge in edges:
        if edge.producer_task_id is not None:
            dependent.setdefault(edge.producer_task_id, []).append(next(row.materialization_id for row in bindings
                if row.artifact_id == edge.operational_logical_artifact_id))
    receipts = tuple(DependencyReceiptBinding('receipt.disclosed.' + key, key, tuple(sorted(values)))
        for key, values in sorted(dependent.items()))
    ports = plane.open_many(verified, bindings=bindings, maximum_bytes=None)
    output_ports = tuple(WorkerOutputPort(row.output_id, row.payload_schema, row.profile, row.media_type,
        'artifact.' + retention.continued_run_id + '.' + row.output_id) for row in original.task.outputs)
    reference = CapabilityConfigRef(config.record_id, config.SCHEMA, manifest.config_schema_sha256, config.fingerprint(), config.record_id)
    context = TaskContext('run.foreign' if damage == 'run' else retention.continued_run_id, original.task.task_id,
        'attempt.disclosed-copy', reference, bindings, ports, output_ports, manifest.permissions,
        OutcomeAccess.OUTCOME_BLIND, manifest.resource_ceiling, WorkerIsolationProfile.TRUSTED_LOCAL, receipts)
    external = tuple(sorted((ExternalInputSpec('input.' + row.artifact_id, row.artifact_id,
        row.logical.content_sha256, row.logical.payload_schema, row.logical.media_type, row.materialization.size_bytes,
        VisibilityCeiling.PROSPECTIVE, OutcomeAccess.OUTCOME_BLIND, None)
        for row in verified if kinds[row.artifact_id] is WorkerInputKind.EXTERNAL), key=lambda row: row.input_id))
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind, reference,
        manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions, manifest.maximum_evidence_ceiling,
        OutcomeAccess.OUTCOME_BLIND, manifest.resource_ceiling)
    task = freeze_worker_configuration(ExecutionTask(original.task.task_id, declaration.stage, requirement,
        manifest.implementation_sha256, tuple(sorted(dependent)), external,
        tuple(ArtifactOutputSpec(row.output_id, row.logical_artifact_id, 'copy-output/' + row.output_id,
            row.payload_schema, row.profile, row.media_type, VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND)
            for row in output_ports), (), BarrierKind.NONE, 1, ('obligation.disclosed-copy',),
        scientific_inputs=tuple(sorted(edges, key=lambda row: row.edge_id))))
    contract = prepare_worker_invocation(runner, context, verified,
        implementation=retention.original_source if damage == 'source' else source_binding(current),
        execution_plan=_pin('plan.disclosed-continued', ExecutionPlan),
        execution_task=ObjectIdentity.from_record(task.task_id, task), execution_task_record=task)
    return SimpleNamespace(runner=runner, context=replace(context, prepared_invocation=contract), raw=output_raw,
        config=config, task=task, retention=retention)


@pytest.mark.parametrize('damage', (None, 'producer', 'source', 'run', 'copy-bytes'))
def test_retained_worker_keeps_original_bytes_and_refuses_substitution(configured_prefix_case, monkeypatch, tmp_path, damage):  # noqa: F811
    selected = prepared_copy(configured_prefix_case, monkeypatch, tmp_path, damage)
    try:
        if damage is not None:
            with pytest.raises(ValueError, match='dependency|continued|original output'):
                selected.runner.execute(selected.context)
        else:
            result = selected.runner.execute(selected.context)
            assert {row.output_id: row.payload for row in result.outputs} == selected.raw
            assert all(row.passed for row in result.checks)
            assert not selected.context.prepared_invocation.native_effect
    finally:
        for port in selected.context.input_ports:
            port.close()
