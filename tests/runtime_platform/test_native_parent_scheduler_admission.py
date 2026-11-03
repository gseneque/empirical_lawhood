# SPDX-License-Identifier: MPL-2.0
"""Actual scheduler fallback refuses native parent entry with missing bindings.

Synthetic metadata only: no repository, scratch, worker, native store or BEGIN.
"""

from types import SimpleNamespace

import pytest

from empirical_lawhood.infrastructure.execution import LocalScheduler, ResourceAdmissionError
from empirical_lawhood.runtime.execution import ExecutionAssuranceProfile, ParentPreparedTaskRunner
from empirical_lawhood.runtime.plans import PlanLane
from tests.runtime_platform.test_native_parent_preparation_contract import native_context


@pytest.mark.parametrize('missing', ('implementation', 'native-hook'))
def test_actual_scheduler_refuses_legacy_begin_fallback_for_unprepared_native_parent(protocol_fixture, missing):
    manifest, context = native_context(protocol_fixture)
    contract = context.prepared_invocation
    task = contract.execution_task_record

    def forbidden(*args, **kwargs):
        pytest.fail('missing native parent binding reached custody callback, worker or BEGIN')

    wrapper = ParentPreparedTaskRunner(manifest, forbidden, native_effect=True)
    scheduler = object.__new__(LocalScheduler)
    scheduler.implementation_binding = None if missing == 'implementation' else contract.implementation
    scheduler._implementation_commit_for = lambda *args: contract.implementation.observed_git_head
    scheduler.runner_registry = SimpleNamespace(resolve=lambda value: wrapper)
    scheduler._worker_inputs = lambda *args: ((), ())
    scheduler.lane = PlanLane.PROSPECTIVE
    scheduler.assurance_profile = ExecutionAssuranceProfile.TRUSTED_LOCAL
    scheduler.adjudication_task_id = None
    scheduler.execution_resource_envelope_coordinator = None
    scheduler.provenance_requirements = {}
    scheduler.native_effect_capability_keys = frozenset((manifest.capability_key,))
    scheduler.native_work_preparers = {}
    scheduler.executor = SimpleNamespace(execute=forbidden)
    scheduler._begin_native_contact = forbidden
    scheduler._native_subwork_progress = forbidden
    with pytest.raises(ResourceAdmissionError, match='native parent preparation requires'):
        scheduler._execute_runner(context.run_id, task, context.attempt_id, (), (), ())
