# SPDX-License-Identifier: MPL-2.0
"""Installed parent preparation controls; synthetic software authority only."""

from dataclasses import dataclass, replace
from decimal import Decimal
import os

import pytest

from empirical_lawhood.infrastructure.execution import LocalProcessExecutor, ResourceAdmissionError
from empirical_lawhood.runtime.artifacts import ReceiptCheck
from empirical_lawhood.runtime.execution import (
    ParentPreparedTaskRunner, RunnerResult, TaskContext, WorkerIsolationProfile, prepare_task_runner,
)
from tests.numerical_provenance_fixtures import numerical_plane


@dataclass(frozen=True)
class _PreparedRunner:
    manifest: object
    task_id: str
    parent_pid: int

    def execute(self, context):
        assert context.task_id == self.task_id
        assert os.getpid() != self.parent_pid
        return RunnerResult((), (ReceiptCheck('software.parent-prepared-child', True, ()),))


@pytest.fixture
def task_context(protocol_fixture):
    task = next(value for value in protocol_fixture.execution_plan.tasks if value.task_id == 'prepare')
    manifest = protocol_fixture.registry.resolve(task.capability.capability_key, task.capability.capability_version)
    context = TaskContext(protocol_fixture.run_plan.run_plan_id, task.task_id,
        protocol_fixture.run_plan.run_plan_id+'.prepare.attempt-001', task.capability.config, (), (), (),
        task.capability.required_permissions, task.capability.requested_outcome_access,
        replace(task.capability.requested_resources, memory_bytes=512*1024**2, output_bytes=1024, wall_time_seconds=5),
        WorkerIsolationProfile.TRUSTED_LOCAL)
    return manifest, context


@pytest.mark.parametrize('mode', ('deadline', 'deadline-free', 'campaign-deadline-free'))
def test_preparation_runs_in_parent_and_only_plain_runner_reaches_child(task_context, tmp_path, mode):
    manifest, context = task_context
    prepared_contexts = []

    def prepare(actual):
        prepared_contexts.append(actual)
        return _PreparedRunner(manifest, actual.task_id, os.getpid())

    # The local closure cannot be pickled. A successful spawn therefore proves
    # that the wrapper, supplier/authority callback and its parent state stayed
    # out of the worker, while its exact task identity was retained.
    wrapper = ParentPreparedTaskRunner(manifest, prepare)
    executor = LocalProcessExecutor(scratch_root=numerical_plane(tmp_path/'scratch').root)
    if mode == 'deadline':
        result = executor.execute(wrapper, context, timeout_seconds=5)
    elif mode == 'deadline-free':
        result = executor.execute_deadline_free(wrapper, context, progress_contract=None,
            progress_callback=lambda counter: None)
    else:
        result = executor.execute_deadline_free_until(wrapper, context, progress_contract=None,
            progress_callback=lambda counter: None, hard_remaining_seconds=Decimal(5))
    assert prepared_contexts == [context]
    assert result.checks == (ReceiptCheck('software.parent-prepared-child', True, ()),)


@pytest.mark.parametrize('mode', ('deadline', 'deadline-free', 'campaign-deadline-free'))
def test_preparation_refusal_creates_no_scratch_pipe_or_process(task_context, tmp_path, monkeypatch, mode):
    manifest, context = task_context
    plane = numerical_plane(tmp_path/'scratch')
    executor = LocalProcessExecutor(scratch_root=plane.root)

    def refuse(actual):
        assert actual == context
        raise PermissionError('software.current-issued-authority-required')

    def forbidden(*args, **kwargs):
        pytest.fail('refused preparation reached process or pipe creation')

    monkeypatch.setattr(executor._context, 'Process', forbidden)
    monkeypatch.setattr(executor._context, 'Pipe', forbidden)
    wrapper = ParentPreparedTaskRunner(manifest, refuse)
    with pytest.raises(PermissionError, match='current-issued-authority-required'):
        if mode == 'deadline':
            executor.execute(wrapper, context, timeout_seconds=5)
        elif mode == 'deadline-free':
            executor.execute_deadline_free(wrapper, context, progress_contract=None, progress_callback=lambda counter: None)
        else:
            executor.execute_deadline_free_until(wrapper, context, progress_contract=None,
                progress_callback=lambda counter: None, hard_remaining_seconds=Decimal(5))
    assert not (tmp_path/'scratch'/'scratch').exists()


def test_unprepared_or_recursive_wrapper_cannot_execute(task_context):
    manifest, context = task_context
    wrapper = ParentPreparedTaskRunner(manifest, lambda actual: wrapper)
    with pytest.raises(PermissionError, match='PREPARATION_REQUIRED'):
        wrapper.execute(context)
    with pytest.raises(ValueError, match='remains unprepared'):
        prepare_task_runner(wrapper, context)


def test_changed_prepared_manifest_is_refused(task_context):
    manifest, context = task_context
    changed = replace(manifest, implementation_sha256='b'*64)
    wrapper = ParentPreparedTaskRunner(manifest, lambda actual: _PreparedRunner(changed, actual.task_id, os.getpid()))
    with pytest.raises(ValueError, match='installed manifest'):
        prepare_task_runner(wrapper, context)


def test_legacy_prepare_named_method_is_never_called(task_context):
    manifest, context = task_context

    class LegacyRunner:
        def prepare_execution(self, actual):
            pytest.fail('legacy runner gained implicit preparation effects')

    legacy = LegacyRunner()
    legacy.manifest = manifest
    assert prepare_task_runner(legacy, context) is legacy


def test_preparation_cannot_enter_grouped_worker(task_context, tmp_path, monkeypatch):
    manifest, context = task_context
    executor = LocalProcessExecutor(scratch_root=numerical_plane(tmp_path/'scratch').root)

    def forbidden(*args, **kwargs):
        pytest.fail('parent-prepared task reached grouped worker or preparation')

    monkeypatch.setattr(executor._context, 'Process', forbidden)
    wrapper = ParentPreparedTaskRunner(manifest, forbidden)
    with pytest.raises(ResourceAdmissionError, match='dedicated task process'):
        executor.execute_deadline_free_in_group(wrapper, context, execution_group_id='software.group',
            progress_contract=None, progress_callback=lambda counter: None)


@pytest.mark.parametrize('method', ('execute_with_native_subwork', 'execute_streaming_with_native_subwork',
                                 'jit_signature_projection', 'execute_with_progress'))
def test_prepared_runner_cannot_add_native_or_progress_interfaces(task_context, method):
    manifest, context = task_context

    class ChangedRunner:
        def execute(self, actual):
            pytest.fail('changed prepared runner was executed')

    changed = ChangedRunner()
    changed.manifest = manifest
    setattr(changed, method, lambda *args, **kwargs: None)
    wrapper = ParentPreparedTaskRunner(manifest, lambda actual: changed)
    with pytest.raises(ValueError, match='dedicated pure task runner'):
        prepare_task_runner(wrapper, context)


def test_recursive_factory_defaults_and_proof_do_not_prepare_authority():
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.operation_bindings import operation_factories
    from empirical_lawhood.runtime.capabilities import CapabilityRegistry
    from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort
    from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort, recursive_input_port_key

    class Supplier:
        def resolve_input(self, spec):
            pytest.fail('runner construction opened an input')

    factory = next(value for value in operation_factories() if not value.registration.native_effect)
    supplier = Supplier()
    registry = CapabilityRegistry('registry.software.parent-preparation', (factory.manifest,))
    ports = (ExecutablePlatformPort(recursive_input_port_key(factory.registration.selection),
        RecursiveOperationInputPort(supplier)),)
    ordinary = factory.build_provider(registry=registry, records=(), platform_ports=ports).runners(registry)[0]
    assert factory.runner_preparation_factory is None
    assert not isinstance(ordinary, ParentPreparedTaskRunner)
    constructed = []

    def install(actual_supplier, runner):
        assert actual_supplier is supplier
        constructed.append(runner)

        def refused_preparation(context):
            pytest.fail('provider construction or proof performed authority preparation')

        return ParentPreparedTaskRunner(runner.manifest, refused_preparation)

    prepared_factory = replace(factory, runner_preparation_factory=install)
    assert prepared_factory.binding.canonical_bytes() == factory.binding.canonical_bytes()
    wrapper = prepared_factory.build_provider(registry=registry, records=(), platform_ports=ports).runners(registry)[0]
    assert isinstance(wrapper, ParentPreparedTaskRunner) and len(constructed) == 1
    assert wrapper.manifest == ordinary.manifest


@pytest.mark.parametrize('invalid', ('not-callable', 'wrong-wrapper'))
def test_recursive_preparation_factory_rejects_invalid_installed_product(invalid):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.operation_bindings import operation_factories
    from empirical_lawhood.runtime.capabilities import CapabilityRegistry
    from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort
    from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort, recursive_input_port_key

    factory = next(value for value in operation_factories() if not value.registration.native_effect)
    if invalid == 'not-callable':
        with pytest.raises(TypeError, match='code-owned callables'):
            replace(factory, runner_preparation_factory=True)
        return

    class Supplier:
        def resolve_input(self, spec):
            pytest.fail('invalid runner factory opened an input')

    registry = CapabilityRegistry('registry.software.invalid-preparation', (factory.manifest,))
    ports = (ExecutablePlatformPort(recursive_input_port_key(factory.registration.selection),
        RecursiveOperationInputPort(Supplier())),)
    changed = replace(factory, runner_preparation_factory=lambda supplier, runner: runner)
    provider = changed.build_provider(registry=registry, records=(), platform_ports=ports)
    with pytest.raises(ValueError, match='explicit wrapper'):
        provider.runners(registry)


def test_native_parent_preparation_declaration_does_not_execute_its_callback():
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.operation_bindings import operation_factories

    factory = next(value for value in operation_factories() if value.registration.native_effect)
    def forbidden(*args, **kwargs):
        pytest.fail('native preparation reached provider, worker or native entry')

    selected = replace(factory, runner_preparation_factory=forbidden)
    assert selected.binding == factory.binding
    assert selected.registration.native_work_preparer is factory.registration.native_work_preparer


def test_pure_parent_preparation_cannot_add_native_slots():
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.operation_bindings import operation_factories

    factory = next(value for value in operation_factories() if not value.registration.native_effect)
    factory = replace(factory, registration=replace(factory.registration,
        native_effect_slot_ids=lambda config: ('software.native-slot',)))
    with pytest.raises(ValueError, match='pure parent preparation cannot introduce native effect slots'):
        replace(factory, runner_preparation_factory=lambda supplier, runner: None)
