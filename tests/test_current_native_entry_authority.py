# SPDX-License-Identifier: MPL-2.0
"""Actual stored grant controls at Ready; disclosed invocation, no worker entry."""

from dataclasses import replace
from datetime import UTC, datetime
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import current_task_custody as owner
from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract, PreparedWorkerEnvironment
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
from empirical_lawhood.runtime.execution import WorkerOutputPort
from empirical_lawhood.runtime.plans import BarrierKind
from tests.test_current_result_custody import actual_issued_current_task_controls as actual_issued_current_task_controls


class FutureClock(datetime):
    @classmethod
    def now(cls, tz=None):
        return datetime(2030, 1, 1, tzinfo=UTC)


def disclosed_contract(f):
    # The general control fixture deliberately supplies no dependency receipts.
    # Select its actual root task instead of manufacturing parent completion.
    task = next(row for row in f.plan.tasks if not row.dependency_task_ids and row.barrier is not BarrierKind.REVEAL)
    f.runner = SimpleNamespace(manifest=f.control.package.registry.resolve(
        task.capability.capability_key, task.capability.capability_version))
    f.context = replace(f.context, task_id=task.task_id, config=task.capability.config,
        output_ports=tuple(WorkerOutputPort(row.output_id, row.payload_schema, row.profile, row.media_type,
            row.logical_artifact_id) for row in task.outputs), permissions=task.capability.required_permissions,
        outcome_access=task.capability.requested_outcome_access, resource_budget=task.capability.requested_resources)
    sources = (('src/disclosed-ready-control.py', 'a' * 64),)
    implementation = RecursiveImplementationBinding(sources, sha256(canonical_json_bytes(sources)).hexdigest(),
        'b' * 64, f.plan.implementation_commit, False)
    # Literal environment/invocation metadata is never sent to an executor.
    # The actual issued package/grant/plan store remains the production owner.
    return PreparedInvocationContract('invocation.disclosed-ready', f.runner.manifest, implementation,
        PreparedWorkerEnvironment('/disclosed/python', 'c' * 64, '/disclosed/env', ()),
        f.context.run_id, f.context.task_id, f.context.attempt_id, f.context.config, (), f.context.output_ports,
        f.context.permissions, f.context.outcome_access, f.context.resource_budget, f.context.isolation_profile,
        dependency_receipts=f.context.dependency_receipts, execution_plan=ObjectIdentity.from_record(f.plan.execution_plan_id, f.plan),
        execution_task=ObjectIdentity.from_record(task.task_id, task), execution_task_record=task,
        required_input_artifact_ids=tuple(sorted(set(task.external_input_artifact_ids) |
            {row.operational_logical_artifact_id for row in task.scientific_inputs})), native_effect=True)


def test_ready_rechecks_actual_current_effect_authority_after_preparation(actual_issued_current_task_controls, monkeypatch):
    f = actual_issued_current_task_controls
    contract = disclosed_contract(f)
    assert f.custody.current_task(f.context, f.runner)[1] == f.plan
    f.custody.require_native_entry(f.context, f.runner, prepared_contract=contract)
    monkeypatch.setattr(owner, 'datetime', FutureClock)
    # Exact stored original controls remain readable after expiry; a new native
    # effect still refuses at the actual Ready boundary's fresh clock.
    assert f.custody.current_task(f.context, f.runner)[1] == f.plan
    with pytest.raises(PermissionError, match='expired'):
        f.custody.require_native_entry(f.context, f.runner, prepared_contract=contract)
    assert not f.control.executor.invocations


@pytest.mark.parametrize('damage', ('source', 'stored-grant-refusal'))
def test_ready_refuses_substituted_source_or_current_permission_store(actual_issued_current_task_controls, monkeypatch, damage):
    f = actual_issued_current_task_controls
    contract = disclosed_contract(f)
    if damage == 'source':
        contract = replace(contract, implementation=replace(contract.implementation, observed_git_head='f' * 40))
    else:
        load = ExternalStudyOperationAuthorityStore.load
        def refused(self, authority_id):
            if authority_id == f.control.package.execution_authority.authority_id:
                raise PermissionError('actual current execution authority access refused')
            return load(self, authority_id)
        monkeypatch.setattr(ExternalStudyOperationAuthorityStore, 'load', refused)
    with pytest.raises(PermissionError, match='substitutes|access refused'):
        f.custody.require_native_entry(f.context, f.runner, prepared_contract=contract)
    assert not f.control.executor.invocations
