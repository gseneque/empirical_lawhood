# SPDX-License-Identifier: MPL-2.0
"""Native parent/callback/projection ordering with no process, files or BEGIN."""

from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from types import SimpleNamespace

import pytest

from empirical_lawhood.infrastructure import execution as owner
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactGenericValidation, ArtifactProfile, LogicalArtifactIdentity
from empirical_lawhood.runtime.execution import ParentPreparedTaskRunner, WorkerInputBinding, WorkerInputKind, WorkerInputPort
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkOutput, NativeSubworkRoster
from empirical_lawhood.runtime.plans import ExternalInputSpec
from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeInputContract, PreparedNativeWork
from tests.runtime_platform.test_native_parent_preparation_contract import NativeRunner, native_context


class MemoryInput:
    def __init__(self, payload):
        self.payload, self.stream = payload, BytesIO(payload)
        self.bytes_read = 0

    def read(self, size=-1):
        result = self.stream.read(size)
        self.bytes_read += len(result)
        return result

    def cursor(self):
        return MemoryInput(self.payload)

    def close(self):
        self.stream.close()


def staged_context(fixture):
    manifest, base = native_context(fixture)
    original = base.prepared_invocation
    raw = b"exposed-in-memory-control"
    digest = sha256(raw).hexdigest()
    logical_id, schema = base.config.artifact_id, base.config.config_schema
    validation = ArtifactGenericValidation("exposed.metadata", "1.0.0", "5" * 64, schema, ArtifactProfile.CANONICAL_JSON)
    logical = LogicalArtifactIdentity(logical_id, digest, schema, ArtifactProfile.CANONICAL_JSON, "application/json",
        owner.VisibilityCeiling.PROSPECTIVE, (), owner.OutcomeAccess.OUTCOME_BLIND, validation)
    binding = WorkerInputBinding(logical_id, "materialization.exposed.control", schema, "application/json", len(raw),
        logical.visibility_ceiling, logical.outcome_access, WorkerInputKind.EXTERNAL)
    source = PreparedNativeInputContract(logical, binding, digest)
    config = replace(base.config, content_sha256=digest)
    task = replace(original.execution_task_record, capability=replace(original.execution_task_record.capability, config=config),
        external_inputs=(ExternalInputSpec("config", logical_id, digest, schema, "application/json", len(raw),
            logical.visibility_ceiling, logical.outcome_access, None),))
    contract = replace(original, inputs=(source,), config=config, required_input_artifact_ids=(logical_id,),
        execution_task_record=task, execution_task=ObjectIdentity.from_record(task.task_id, task))
    context = replace(base, config=config, input_bindings=(binding,), input_ports=(WorkerInputPort(binding, MemoryInput(raw)),),
        prepared_invocation=contract)
    return manifest, replace(context, prepared_invocation=None), contract


def projected_work(context, parent):
    implementation = context.prepared_invocation.implementation
    definition = NativeSubworkDefinition("work.exposed", "operation.exposed", parent,
        ObjectIdentity(context.config.config_id, context.config.config_schema, "1.0.0", context.config.content_sha256), (),
        implementation.code_sources_sha256, implementation.dependency_lock_sha256, context.input_materialization_ids, (),
        (NativeSubworkOutput("product", "empirical-lawhood/source/checksummed-uninterpreted-public-bytes",
            ArtifactProfile.RAW_SOURCE_BYTES, "application/octet-stream"),))
    roster = NativeSubworkRoster("selected.native-subwork", parent, (definition.identity,))
    return PreparedNativeWork(parent, ("unit.exposed",), ("slot.exposed",), (definition,), (roster,))


def test_initializer_does_not_project_native_work_on_unprepared_parent(protocol_fixture, monkeypatch):
    manifest, bound = native_context(protocol_fixture)
    initial = bound.prepared_invocation
    context = replace(bound, prepared_invocation=None)
    wrapper = ParentPreparedTaskRunner(manifest, lambda value: pytest.fail("initializer called custody callback"), native_effect=True)
    monkeypatch.setattr(owner, "observe_worker_environment", lambda: SimpleNamespace(interpreter_path="/exposed/python",
        interpreter_sha256="4" * 64, prefix="/exposed"))
    monkeypatch.setattr(owner, "_select_worker_environment", lambda selector: ())
    result = owner.prepare_worker_invocation(wrapper, context, (), implementation=initial.implementation,
        execution_plan=initial.execution_plan, execution_task=initial.execution_task,
        execution_task_record=initial.execution_task_record, native_effect=True,
        native_work_preparer=lambda **kwargs: pytest.fail("unprepared parent reached original native decoder"))
    assert result.native_work is None and result.native_preparation_error is None
    result.require_complete()


def test_actual_parent_receives_complete_initial_contract_then_original_work_is_sealed(protocol_fixture):
    manifest, context, initial = staged_context(protocol_fixture)
    events, plain = [], NativeRunner(manifest)

    def admission(actual):
        events.append("current-and-prior-custody")
        assert actual.prepared_invocation is initial and initial.native_work is None
        initial.validate_context(actual)
        return plain

    def project(*, runner, context, expected_parent):
        events.append("pure-native-projection")
        assert runner is plain and events[0] == "current-and-prior-custody"
        assert context.prepared_invocation is not None
        assert context.input_ports[0].read() == b"exposed-in-memory-control"
        return projected_work(context, expected_parent)

    wrapper = ParentPreparedTaskRunner(manifest, admission, native_effect=True)
    actual, final_context, final = owner._prepare_parent_native_runner(wrapper, context, initial, project)
    assert actual is plain and final.native_work is not None and final.native_preparation_error is None
    assert final_context.prepared_invocation is final and final.expected_parent_contact == initial.expected_parent_contact
    assert final.native_work.expected_parent == initial.expected_parent_contact
    assert final.identity != initial.identity
    assert events == ["current-and-prior-custody", "pure-native-projection", "pure-native-projection"]
    assert context.input_ports[0].bytes_read == 0


def test_current_grant_refusal_precedes_original_native_projection(protocol_fixture):
    manifest, context, initial = staged_context(protocol_fixture)

    def refuse(actual):
        raise PermissionError("actual current grant refused")

    wrapper = ParentPreparedTaskRunner(manifest, refuse, native_effect=True)
    with pytest.raises(PermissionError, match="current grant refused"):
        owner._prepare_parent_native_runner(wrapper, context, initial,
            lambda **kwargs: pytest.fail("refused authority reached native projection"))


def test_changed_context_or_preexisting_work_cannot_reach_parent_callback(protocol_fixture):
    manifest, context, initial = staged_context(protocol_fixture)
    wrapper = ParentPreparedTaskRunner(manifest, lambda value: pytest.fail("invalid contract reached parent"), native_effect=True)
    with pytest.raises(ValueError, match="complete worker context"):
        owner._prepare_parent_native_runner(wrapper, replace(context, attempt_id="attempt.other"), initial, lambda **kwargs: None)
    with pytest.raises(owner.ResourceAdmissionError, match="initial no-work"):
        owner._prepare_parent_native_runner(wrapper, context, replace(initial, native_preparation_error="earlier actual failure"), lambda **kwargs: None)


def test_projection_failure_is_retained_for_actual_worker_refusal_without_entry(protocol_fixture):
    manifest, context, initial = staged_context(protocol_fixture)
    plain = NativeRunner(manifest)
    wrapper = ParentPreparedTaskRunner(manifest, lambda value: plain, native_effect=True)

    def refuse(**kwargs):
        raise ValueError("actual original source was substituted")

    actual, final_context, final = owner._prepare_parent_native_runner(wrapper, context, initial, refuse)
    assert actual is plain and final_context.prepared_invocation is final
    assert final.native_work is None and final.native_preparation_error == "actual original source was substituted"


def test_changed_specialization_is_retained_for_worker_refusal(protocol_fixture):
    manifest, context, initial = staged_context(protocol_fixture)
    plain, count = NativeRunner(manifest), 0
    wrapper = ParentPreparedTaskRunner(manifest, lambda value: plain, native_effect=True)

    def project(*, runner, context, expected_parent):
        nonlocal count
        count += 1
        work = projected_work(context, expected_parent)
        return work if count == 1 else replace(work, native_effect_slot_ids=("slot.substituted",))

    _, _, final = owner._prepare_parent_native_runner(wrapper, context, initial, project)
    assert final.native_preparation_error == "native specialization changes its original scientific initial work projection"
    assert final.native_work.native_effect_slot_ids == ("slot.exposed",)


def test_existing_pure_parent_callback_keeps_original_context_and_contract(protocol_fixture):
    manifest, context, contract = staged_context(protocol_fixture)
    contract = replace(contract, native_effect=False)
    calls = []

    class PureRunner:
        def __init__(self, manifest):
            self.manifest = manifest

        def execute(self, context):
            pytest.fail("preparation control executed a worker")

    plain = PureRunner(manifest)
    wrapper = ParentPreparedTaskRunner(manifest, lambda actual: (calls.append(actual), plain)[1])
    actual, unchanged_context, unchanged_contract = owner._prepare_parent_native_runner(wrapper, context, contract,
        lambda **kwargs: pytest.fail("pure preservation projected native work"))
    assert actual is plain and calls == [context]
    assert unchanged_context is context and unchanged_contract is contract and context.prepared_invocation is None
