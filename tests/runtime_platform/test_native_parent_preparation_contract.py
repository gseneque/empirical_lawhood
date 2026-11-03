# SPDX-License-Identifier: MPL-2.0
"""In-memory native parent admission; no native contact or worker process."""

from dataclasses import replace
from hashlib import sha256

import pytest

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.execution import ParentPreparedTaskRunner, TaskContext, WorkerIsolationProfile, WorkerOutputPort, prepare_task_runner
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract, PreparedWorkerEnvironment
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding


def native_context(fixture):
    # This control exercises admission metadata only. Scientific input-byte and
    # actual native-contact acceptance have separate owners and are not entered.
    task = replace(next(value for value in fixture.execution_plan.tasks if value.task_id == 'prepare'), external_inputs=())
    manifest = fixture.registry.resolve(task.capability.capability_key, task.capability.capability_version)
    outputs = tuple(WorkerOutputPort(row.output_id, row.payload_schema, row.profile, row.media_type, row.logical_artifact_id)
        for row in task.outputs)
    context = TaskContext(fixture.run_plan.run_plan_id, task.task_id, 'attempt.exposed.native-parent', task.capability.config,
        (), (), outputs, task.capability.required_permissions, task.capability.requested_outcome_access,
        task.capability.requested_resources, WorkerIsolationProfile.TRUSTED_LOCAL)
    sources = (('synthetic/exposed.py', '1'*64),)
    implementation = RecursiveImplementationBinding(sources, sha256(canonical_json_bytes(sources)).hexdigest(), '2'*64, '3'*40, False)
    contract = PreparedInvocationContract('invocation.exposed.native-parent', manifest, implementation,
        PreparedWorkerEnvironment('/synthetic/python', '4'*64, '/synthetic', ()), context.run_id, context.task_id,
        context.attempt_id, context.config, (), outputs, context.permissions, context.outcome_access,
        context.resource_budget, context.isolation_profile, execution_plan=ObjectIdentity.from_record(
            fixture.execution_plan.execution_plan_id, fixture.execution_plan),
        execution_task=ObjectIdentity.from_record(task.task_id, task), execution_task_record=task, native_effect=True)
    return manifest, replace(context, prepared_invocation=contract)


class NativeRunner:
    def __init__(self, manifest):
        self.manifest = manifest

    def execute(self, context):
        pytest.fail('admission control executed a worker')

    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        pytest.fail('admission control entered native work')


def test_native_parent_admission_returns_plain_runner_only_after_exact_complete_contract(protocol_fixture):
    manifest, context = native_context(protocol_fixture)
    actual, calls = NativeRunner(manifest), []
    wrapper = ParentPreparedTaskRunner(manifest, lambda value: (calls.append(value), actual)[1], native_effect=True)
    assert callable(wrapper.execute_with_native_subwork)
    with pytest.raises(PermissionError, match='PREPARATION_REQUIRED'):
        wrapper.execute_with_native_subwork(context, object())
    assert prepare_task_runner(wrapper, context) is actual
    assert calls == [context]


def test_native_parent_refuses_missing_contract_before_callback(protocol_fixture):
    manifest, context = native_context(protocol_fixture)
    def forbidden(value):
        pytest.fail('missing prepared native identity reached parent callback')
    wrapper = ParentPreparedTaskRunner(manifest, forbidden, native_effect=True)
    with pytest.raises(ValueError, match='exact prepared native invocation'):
        prepare_task_runner(wrapper, replace(context, prepared_invocation=None))


def test_native_parent_flag_cannot_admit_a_plain_or_differently_scoped_runner(protocol_fixture):
    manifest, context = native_context(protocol_fixture)
    class PureRunner:
        def execute(self, actual):
            pytest.fail('admission executed a pure worker')
    pure = PureRunner()
    pure.manifest = manifest
    with pytest.raises(ValueError, match='declared native runner'):
        prepare_task_runner(ParentPreparedTaskRunner(manifest, lambda value: pure, native_effect=True), context)
    with pytest.raises(ValueError, match='dedicated pure task runner'):
        prepare_task_runner(ParentPreparedTaskRunner(manifest, lambda value: NativeRunner(manifest)), context)


def test_native_parent_flag_is_explicit_and_type_strict(protocol_fixture):
    manifest, _ = native_context(protocol_fixture)
    with pytest.raises(TypeError, match='installed code callback'):
        ParentPreparedTaskRunner(manifest, lambda context: None, native_effect=1)
