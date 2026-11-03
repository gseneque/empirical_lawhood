# SPDX-License-Identifier: MPL-2.0
"""Actual compiled TRAIN CONFIG and science census, with no native contact.

The maintained copied public preparation supplies its complete one-root TEST
allocation and actual compiler tasks. The entry dependency is the existing
explicit disclosed metadata premise, not a successful scientific/native receipt.
These controls prepare immutable work only; no Ready, execution or qualification
is established. Run on the actual clean implementing source candidate.
"""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_acquisition as acquisition
from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_bindings as owner
from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as records
from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.infrastructure import execution as lifecycle
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.execution import (
    ParentPreparedTaskRunner, TaskContext, VerifiedArtifactInput, WorkerInputBinding,
    WorkerInputKind, WorkerInputPort, WorkerIsolationProfile, WorkerOutputPort,
)
from empirical_lawhood.runtime.plans import ScientificInputRole
from tests.test_matrix_native_training_parent_preflight import prefix_context
from tests.test_matrix_native_training_public_lifecycle import _actual_case, _copied_preparation


@pytest.fixture(scope="module")
def compiled_training(tmp_path_factory):
    directory = tmp_path_factory.mktemp("native-training-config")
    with pytest.MonkeyPatch.context() as patch:
        def forbidden(*args, **kwargs):
            pytest.fail("CONFIG/science custody control entered native acquisition")
        patch.setattr(owner, "execute_parameter_native_work", forbidden)
        patch.setattr(owner, "execute_paired_response_native_work", forbidden)
        patch.setattr(owner.NativeTrainingNativeRunner, "execute_with_native_subwork", forbidden)
        case = _actual_case(directory, patch)
        preparation = _copied_preparation(case, directory / "copied")
        compiled, task, declaration, context, verified, implementation = prefix_context(case, preparation)
        runner = declaration.runner_factory()
        assert type(runner) is ParentPreparedTaskRunner and runner.native_effect
        initial = lifecycle.prepare_worker_invocation(runner, context, verified, implementation=implementation,
            execution_plan=ObjectIdentity.from_record(compiled.execution_plan.execution_plan_id, compiled.execution_plan),
            execution_task=ObjectIdentity.from_record(task.task_id, task), execution_task_record=task,
            native_effect=True, provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,),
            native_work_preparer=owner.prepare_native_work)
        assert initial.native_work is None and initial.native_preparation_error is None
        try:
            yield SimpleNamespace(case=case, compiled=compiled, task=task, declaration=declaration,
                context=context, runner=runner, initial=initial, implementation=implementation)
        finally:
            for port in context.input_ports:
                port.close()


def _prefix_context(control, *, task=None):
    task = control.task if task is None else task
    prepared = replace(control.initial, execution_task_record=task,
        execution_task=ObjectIdentity.from_record(task.task_id, task))
    return replace(control.context, prepared_invocation=prepared,
        input_ports=tuple(port.cursor() for port in control.context.input_ports))


def _close(context):
    for port in context.input_ports:
        port.close()


def _science_body_guard(monkeypatch, context):
    original, reads = WorkerInputPort.read, []
    def read(port, size=-1):
        if size != 0:
            reads.append(port.artifact_id)
            if port.artifact_id != context.config.artifact_id:
                pytest.fail("unvalidated CONFIG or science census opened a science operand")
        return original(port, size)
    monkeypatch.setattr(WorkerInputPort, "read", read)
    return reads


def _entry_context(control):
    plan = control.compiled.execution_plan
    task, = (value for value in plan.tasks if value.task_id == acquisition.entry_task_id(control.case.specification))
    row, = (value for value in control.compiled.config_inputs if value.node_id == task.task_id)
    publication = control.case.plane.write(ArtifactWriteRequest(row.config_id,
        "native-config-controls/entry.json", row.record.SCHEMA, ArtifactProfile.CANONICAL_JSON,
        "application/json", "control.native-config-entry", "native-config-controls",
        row.record.canonical_bytes(), owner.EXPOSED, (), owner.DEV))
    verified = (VerifiedArtifactInput(publication.logical, publication.materialization),)
    bindings = tuple(WorkerInputBinding.from_verified(value, kind=WorkerInputKind.EXTERNAL) for value in verified)
    ports = control.case.plane.open_many(verified, bindings=bindings, maximum_bytes=None)
    outputs = tuple(WorkerOutputPort(value.output_id, value.payload_schema, value.profile,
        value.media_type, value.logical_artifact_id) for value in task.outputs)
    context = TaskContext(plan.source_plan.object_id, task.task_id, "attempt.disclosed.native-config-entry",
        task.capability.config, bindings, ports, outputs, task.capability.required_permissions,
        task.capability.requested_outcome_access, task.capability.requested_resources,
        WorkerIsolationProfile.TRUSTED_LOCAL)
    declaration, = (value for value in owner.operation_declarations()
        if value.capability_key == records.NAMESPACE + ".entry")
    runner = declaration.runner_factory()
    prepared = lifecycle.prepare_worker_invocation(runner, context, verified, implementation=control.implementation,
        execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
        execution_task=ObjectIdentity.from_record(task.task_id, task), execution_task_record=task)
    return runner, replace(context, prepared_invocation=prepared)


def test_compiler_configuration_survives_actual_train_parent_preparation_and_prefix_decode(compiled_training):
    control = compiled_training
    config_edge, = (edge for edge in control.task.scientific_inputs
        if edge.scientific_role is ScientificInputRole.CONFIGURATION)
    plain, bound, final = lifecycle._prepare_parent_native_runner(control.runner,
        control.context, control.initial, owner.prepare_native_work)
    assert type(plain) is owner.NativeTrainingNativeRunner
    assert final.native_preparation_error is None and final.native_work is not None
    definition, = final.native_definitions
    assert set(definition.sources) == {*records.native_source_pins(control.case.source), control.case.acquisition.identity}
    context = replace(bound, input_ports=tuple(port.cursor() for port in bound.input_ports))
    try:
        config, specification, source, actual, ports = owner._decode(context, "prefix", plain.manifest)
        assert specification == control.case.specification and source == control.case.source
        assert config.source == control.case.request.sources[0]
        assert actual["acquisition"] == control.case.acquisition
        assert config_edge.consumer_input_id not in ports
        assert set(ports) == {edge.consumer_input_id for edge in control.task.scientific_inputs
            if edge.scientific_role is not ScientificInputRole.CONFIGURATION}
        assert context.prepared_invocation.native_effect
    finally:
        _close(context)


def test_compiler_entry_configuration_has_no_science_operands(compiled_training):
    runner, context = _entry_context(compiled_training)
    try:
        task = context.prepared_invocation.execution_task_record
        assert len(task.scientific_inputs) == 1
        assert task.scientific_inputs[0].scientific_role is ScientificInputRole.CONFIGURATION
        config, specification, source, actual, ports = owner._decode(context, "entry", runner.manifest)
        assert specification == compiled_training.case.specification
        assert config.request == compiled_training.case.request
        assert source is None and actual == {} and ports == {}
        assert not context.prepared_invocation.native_effect
    finally:
        _close(context)


@pytest.mark.parametrize("damage", ("missing", "edge-id", "edge-size"))
def test_train_prefix_configuration_substitution_refuses_before_science_body(compiled_training, monkeypatch, damage):
    task = compiled_training.task
    config_edge, = (edge for edge in task.scientific_inputs if edge.scientific_role is ScientificInputRole.CONFIGURATION)
    if damage == "missing":
        edges = tuple(edge for edge in task.scientific_inputs if edge is not config_edge)
    else:
        changed = (replace(config_edge, edge_id="edge.foreign.train-configuration") if damage == "edge-id"
            else replace(config_edge, maximum_size_bytes=config_edge.maximum_size_bytes + 1))
        edges = tuple(sorted((changed if edge is config_edge else edge for edge in task.scientific_inputs),
            key=lambda edge: edge.edge_id))
    context = _prefix_context(compiled_training, task=replace(task, scientific_inputs=edges))
    reads = _science_body_guard(monkeypatch, context)
    try:
        with pytest.raises(ValueError, match="CONFIGURATION"):
            owner._decode(context, "prefix", compiled_training.runner.manifest)
        assert set(reads).issubset({context.config.artifact_id})
    finally:
        _close(context)


def test_train_entry_missing_configuration_refuses_before_request_is_used(compiled_training, monkeypatch):
    runner, context = _entry_context(compiled_training)
    task = replace(context.prepared_invocation.execution_task_record, scientific_inputs=())
    prepared = replace(context.prepared_invocation, execution_task_record=task,
        execution_task=ObjectIdentity.from_record(task.task_id, task))
    context = replace(context, prepared_invocation=prepared)
    _science_body_guard(monkeypatch, context)
    try:
        with pytest.raises(ValueError, match="CONFIGURATION"):
            owner._decode(context, "entry", runner.manifest)
    finally:
        _close(context)


def test_valid_configuration_does_not_hide_missing_train_science_operand(compiled_training, monkeypatch):
    task = compiled_training.task
    removed, = (edge for edge in task.scientific_inputs if edge.consumer_input_id == "source")
    task = replace(task, scientific_inputs=tuple(edge for edge in task.scientific_inputs if edge is not removed))
    # The actual external source publication and complete prepared input census
    # remain. Only the assigned scientific relation is missing.
    context = _prefix_context(compiled_training, task=task)
    _science_body_guard(monkeypatch, context)
    try:
        with pytest.raises(ValueError, match="scientific operand census"):
            owner._decode(context, "prefix", compiled_training.runner.manifest)
    finally:
        _close(context)
