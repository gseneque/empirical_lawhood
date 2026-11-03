# SPDX-License-Identifier: MPL-2.0
"""Disclosed preparation controls; no issued authority or native execution."""
from contextlib import nullcontext
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import configured_e3_retained_runtime as owner
from empirical_lawhood.api import current_task_custody
from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_composition
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_lowering import operation_class
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_bindings import retained_input_id
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
from empirical_lawhood.runtime.plans import BarrierKind, ExecutionTask, ExternalInputSpec, ScientificInputRole, ScientificInputSpec
from tests.worker_configuration_support import freeze_worker_configuration
from tests.test_matrix_e3_retained_continuation import (  # noqa: F401
    continuation_case, public_case,
)


@pytest.fixture(scope='module')
def controls_case(continuation_case):  # noqa: F811
    return continuation_case


def preparation_case(case, monkeypatch, phase, *, damage=None):
    plan = object()
    config = next(row for row in case.selection.retained_tasks
        if operation_class(row) == phase)
    declarations = {row.capability_key: row for row in configured_protected_composition.operation_declarations()}
    declaration = declarations['matrix-e3-configured-protected.retained-' + phase]
    runner = declaration.runner_factory()
    source = next(row.input_spec for row in case.configs if row.record == config)
    raw, events = config.canonical_bytes(), []
    logical = SimpleNamespace(outcome_access=source.expected_outcome_access,
        visibility_ceiling=source.expected_visibility_ceiling, content_sha256=config.fingerprint())
    physical = SimpleNamespace(relative_path='disclosed/retained-config.json', size_bytes=len(raw),
        physical_sha256='f' * 64 if damage == 'bytes' else config.fingerprint())
    manifest = SimpleNamespace(logical=logical, materialization=physical)
    inputs = {config.record_id: manifest}
    edges = []
    originals = {row.logical_artifact_id: row for row in config.original_receipt.output_logical_artifacts}
    physicals = {row.logical_artifact_id: row for row in config.original_receipt.output_materializations}
    for output in config.original_task.outputs:
        old, material = originals[output.logical_artifact_id], physicals[output.logical_artifact_id]
        port = 'retained-' + output.output_id.rsplit('.', 1)[-1]
        edge = ScientificInputSpec('edge.disclosed.' + port, port, ScientificInputRole.SOURCE,
            None, None, 'external.' + port, retained_input_id(old), retained_input_id(old),
            old.payload_schema, old.media_type, material.size_bytes, old.outcome_access,
            old.visibility_ceiling, BarrierKind.NONE)
        edges.append(edge)
        inputs[edge.operational_logical_artifact_id] = SimpleNamespace(logical=SimpleNamespace(
            logical_artifact_id=retained_input_id(old), payload_schema=old.payload_schema,
            profile=old.profile, media_type=old.media_type, content_sha256=old.content_sha256,
            outcome_access=old.outcome_access, visibility_ceiling=old.visibility_ceiling),
            materialization=SimpleNamespace(physical_sha256=material.physical_sha256,
                size_bytes=material.size_bytes))

    manifest_contract = declaration.manifest()
    reference = CapabilityConfigRef(config.record_id, config.SCHEMA,
        manifest_contract.config_schema_sha256, config.fingerprint(), config.record_id)
    requirement = CapabilityRequirement(manifest_contract.capability_key, manifest_contract.capability_version,
        manifest_contract.kind, reference, manifest_contract.input_schema_ids, manifest_contract.output_schema_ids,
        manifest_contract.permissions, manifest_contract.maximum_evidence_ceiling,
        declaration.outcome_access, manifest_contract.resource_ceiling)
    external = (source, *(ExternalInputSpec(edge.consumer_input_id, edge.operational_logical_artifact_id,
        inputs[edge.operational_logical_artifact_id].logical.content_sha256, edge.payload_schema,
        edge.media_type, edge.maximum_size_bytes, edge.visibility_ceiling, edge.outcome_access, None)
        for edge in edges))
    task = freeze_worker_configuration(ExecutionTask(config.original_task.task_id,
        config.original_task.stage, requirement, manifest_contract.implementation_sha256, (),
        tuple(sorted(external, key=lambda row: row.input_id)), config.original_task.outputs, (),
        BarrierKind.NONE, 1, config.original_task.obligation_ids,
        scientific_inputs=tuple(sorted(edges, key=lambda row: row.edge_id))))
    if damage in ('access', 'visibility'):
        # The frozen typed task stays intact; the persisted publication substitutes a label.
        setattr(logical, 'outcome_access' if damage == 'access' else 'visibility_ceiling', None)

    writer = SimpleNamespace(root=SimpleNamespace(resolve=lambda *args, **kwargs: physical.relative_path),
        verify_manifest=lambda *args, **kwargs: events.append('manifest'))
    custody = current_task_custody.CurrentIssuedTaskCustody(writer=writer)
    monkeypatch.setattr(current_task_custody, 'read_bounded_bytes',
        lambda *args, **kwargs: events.append('control-bytes') or raw)
    root = object()
    package = SimpleNamespace(issued_study=SimpleNamespace(candidate=SimpleNamespace(
        authoring_package=SimpleNamespace(base=SimpleNamespace(draft=root)))))
    monkeypatch.setattr(custody, 'preparation_scope', nullcontext)
    def current_task(*args):
        events.append('issued-task')
        if damage == 'current-access' and events.count('issued-task') == 2:
            raise PermissionError('disclosed current access revoked')
        return package, plan, task

    monkeypatch.setattr(custody, 'current_task', current_task)
    monkeypatch.setattr(custody, 'task_inputs', lambda *args: ({}, inputs))

    def require_task(value):
        assert value == config
        events.append('original-access')
        if damage == 'late-access' and events.count('original-access') == 2:
            raise PermissionError('disclosed original access revoked')

    supplier = SimpleNamespace(custody=custody, root=root, selection=case.selection,
        retained_e3_scope=SimpleNamespace(require_task=require_task))
    context = SimpleNamespace(config=SimpleNamespace(artifact_id=config.record_id,
        content_sha256=config.fingerprint()), run_id=case.selection.retention.continued_run_id)
    return supplier, context, runner, events


@pytest.mark.parametrize('phase', ('numerical', 'fit', 'model-freeze', 'forecast'))
def test_retained_preparation_reads_the_exact_issued_control_lane(controls_case, monkeypatch, phase):
    supplier, context, runner, events = preparation_case(controls_case, monkeypatch, phase)
    assert owner.prepare_retained_task(supplier, context, runner) is runner
    assert events == ['issued-task', 'manifest', 'control-bytes', 'original-access',
        'issued-task', 'original-access']


@pytest.mark.parametrize('damage', ('access', 'visibility', 'bytes', 'late-access', 'current-access'))
def test_retained_control_lane_keeps_missing_lane_byte_and_current_access_refusals(controls_case, monkeypatch, damage):
    supplier, context, runner, events = preparation_case(controls_case, monkeypatch, 'fit', damage=damage)
    with pytest.raises(PermissionError, match='exact issued access|exact canonical|access revoked'):
        owner.prepare_retained_task(supplier, context, runner)
    assert events[0] == 'issued-task'
    if damage in ('access', 'visibility'):
        assert events == ['issued-task']
