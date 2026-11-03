# SPDX-License-Identifier: MPL-2.0
"""Actual worker rejects environment changes made by a late preflight callback.

These exposed hostile callbacks test ordering only. They run no scientific
native entry and do not replace source, interpreter or producing observations.
Collect producing proof against an immutable selected checkout.
"""

import os

import pytest

from empirical_lawhood.infrastructure.execution import LocalProcessExecutor, WorkerPreflightError
from tests.runtime_platform.test_native_subwork import _store
from tests.runtime_platform.test_worker_preflight import ExposedReadRunner, _case, _native_work


class ExposedLateEnvironmentMutation(ExposedReadRunner):
    def __init__(self, name, value):
        super().__init__()
        self.name, self.value = name, value

    def preflight(self, context):
        super().preflight(context)
        os.environ[self.name] = self.value

    def execute(self, context):
        raise AssertionError("a changed final worker environment reached execution")


@pytest.mark.parametrize("name,value", (("OMP_NUM_THREADS", "2"), ("EL_EXPOSED_LATE_UNSELECTED", "unexpected")))
def test_actual_worker_stop_observes_final_callback_environment_before_ready(tmp_path, name, value):
    plane, bundle, _, context, contract, parent = _case(tmp_path, actual=True)
    runner = ExposedLateEnvironmentMutation(name, value)
    parent_value = os.environ.get(name)
    try:
        result = LocalProcessExecutor(scratch_root=plane.root).preflight(runner, context, prepared_contract=contract)
        assert not result.ready
        assert {row.operand_id for row in result.mismatches} == {"worker.environment"}
        if name == "OMP_NUM_THREADS":
            assert result.environment != contract.environment
        else:
            assert result.environment == contract.environment
            assert any(name in row.reason for row in result.mismatches)
        assert result.producing_provenance.package_sources == contract.implementation.package_sources
        assert _store(plane, parent).parent_contacts.read(context.run_id, context.task_id) is None
        assert all(port.bytes_read == 0 for port in context.input_ports)
        assert os.environ.get(name) == parent_value
    finally:
        bundle.close()


@pytest.mark.parametrize("name,value", (("OMP_NUM_THREADS", "2"), ("EL_EXPOSED_LATE_UNSELECTED", "unexpected")))
def test_actual_worker_final_environment_refusal_precedes_ordinary_native_contact(tmp_path, name, value):
    plane, bundle, _, context, contract, parent = _case(tmp_path, actual=True, native=True, nested=False)
    runner = ExposedLateEnvironmentMutation(name, value)
    calls = []
    parent_value = os.environ.get(name)

    def forbidden_entry():
        calls.append("contact")
        return parent, None

    try:
        with pytest.raises(WorkerPreflightError) as refused:
            LocalProcessExecutor(scratch_root=plane.root).execute(runner, context, timeout_seconds=None,
                prepared_contract=contract, native_entry=forbidden_entry, native_work_preparer=_native_work)
        result = refused.value.result
        assert not result.ready and result.native_work == contract.native_work
        assert {row.operand_id for row in result.mismatches} == {"worker.environment"}
        if name == "OMP_NUM_THREADS":
            assert result.environment != contract.environment
        else:
            assert result.environment == contract.environment
            assert any(name in row.reason for row in result.mismatches)
        assert result.producing_provenance.package_sources == contract.implementation.package_sources
        assert calls == []
        assert _store(plane, parent).parent_contacts.read(context.run_id, context.task_id) is None
        assert all(port.bytes_read == 0 for port in context.input_ports)
        assert os.environ.get(name) == parent_value
    finally:
        bundle.close()
