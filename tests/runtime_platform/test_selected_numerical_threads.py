# SPDX-License-Identifier: MPL-2.0
"""Actual worker thread selection, independent of scientific engine results."""

from dataclasses import replace
import json
import os

import pytest

from empirical_lawhood.execution.local.execution import LocalProcessExecutor, _select_worker_environment, prepare_worker_invocation
from empirical_lawhood.storage.numerical_provenance import worker_numerical_threads
from empirical_lawhood.execution.local.worker_bootstrap import NUMERICAL_THREAD_ENV_VARS, numerical_spawn_environment
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.storage.contracts.artifacts import ReceiptCheck
from empirical_lawhood.execution.execution import RunnerResult, TaskOutputPayload
from tests.runtime_platform.test_native_subwork import ExposedInput
from tests.runtime_platform.test_worker_preflight import ExposedReadRunner, _case, _original_task, _second_attempt


IMPORT_THREAD_SETTINGS = {name: os.environ.get(name) for name in NUMERICAL_THREAD_ENV_VARS}


def select_two_threads(environment):
    return {**environment, **dict.fromkeys(NUMERICAL_THREAD_ENV_VARS, "2")}


class ExposedThreadRunner(ExposedReadRunner):
    worker_chunk_limit = 2

    def __init__(self):
        super().__init__()
        self.manifest = replace(self.manifest,
            resource_ceiling=replace(self.manifest.resource_ceiling, cpu_cores=2))

    def execute(self, context):
        import numpy as np
        from threadpoolctl import threadpool_info

        assert np.eye(4).dot(np.ones(4)).tolist() == [1.0]*4
        observed = dict(before_worker_sanitization=IMPORT_THREAD_SETTINGS,
            environment={name: os.environ.get(name) for name in NUMERICAL_THREAD_ENV_VARS},
            pools=[dict(api=p["user_api"], threads=p["num_threads"]) for p in threadpool_info()],
            pid=os.getpid())
        value = ExposedInput("exposed.config", json.dumps(observed, sort_keys=True))
        return RunnerResult((TaskOutputPayload("echo", value.canonical_bytes()),),
            (ReceiptCheck("exposed-actual-thread-observation", True, ()),))


@pytest.mark.parametrize("mode", ("ordinary", "deadline-free", "group"))
def test_actual_spawn_and_loaded_pools_honor_selected_task_threads(tmp_path, mode):
    plane, bundle, _, original_context, original, _ = _case(tmp_path, actual=True)
    runner = ExposedThreadRunner()
    context = replace(original_context, resource_budget=replace(original_context.resource_budget, cpu_cores=2))
    task = _original_task(runner, context, bundle)
    contract = prepare_worker_invocation(runner, context, bundle.verified_inputs,
        implementation=original.implementation, execution_plan=original.execution_plan,
        execution_task=ObjectIdentity.from_record(task.task_id, task), execution_task_record=task,
        worker_environment_selector=select_two_threads)
    executor = LocalProcessExecutor(scratch_root=plane.root)
    before = dict(os.environ)
    try:
        attempts = ((context, contract), _second_attempt(context, contract)) if mode == "group" else ((context, contract),)
        observations = []
        for selected_context, selected_contract in attempts:
            if mode == "ordinary":
                result = executor.execute(runner, selected_context, timeout_seconds=None, prepared_contract=selected_contract)
            else:
                args = dict(progress_contract=None, progress_callback=lambda value: pytest.fail("unexpected progress"),
                    prepared_contract=selected_contract)
                if mode == "group":
                    result = executor.execute_deadline_free_in_group(runner, selected_context,
                        execution_group_id="exposed.selected-threads", **args)
                else:
                    result = executor.execute_deadline_free(runner, selected_context, **args)
            raw = result.outputs[0].payload
            record = decode_canonical_bytes(raw, ExposedInput, maximum_bytes=len(raw))
            observed = json.loads(record.value)
            assert observed["before_worker_sanitization"] == dict.fromkeys(NUMERICAL_THREAD_ENV_VARS, "2")
            assert observed["environment"] == dict.fromkeys(NUMERICAL_THREAD_ENV_VARS, "2")
            assert observed["pools"] and {p["threads"] for p in observed["pools"]} == {2}
            observations.append(observed)
        if mode == "group":
            assert observations[0]["pid"] == observations[1]["pid"] != os.getpid()
        assert dict(os.environ) == before
        assert all(port.bytes_read == 0 for port in context.input_ports)
    finally:
        executor.close_run_workers()
        bundle.close()


@pytest.mark.parametrize("count", ("0", "-1", "1.5", "02", "9", "", "٢"))
def test_invalid_or_excess_thread_selection_refuses_before_spawn(count):
    def select(environment):
        return {**environment, **dict.fromkeys(NUMERICAL_THREAD_ENV_VARS, count)}

    with pytest.raises(ValueError, match="thread setting"):
        _select_worker_environment(select, cpu_cores=8)


def test_thread_count_is_bound_to_task_allocation_and_cannot_remove_required_settings():
    with pytest.raises(ValueError, match="CPU allocation"):
        _select_worker_environment(select_two_threads, cpu_cores=1)
    selected = _select_worker_environment(select_two_threads, cpu_cores=2)
    assert worker_numerical_threads(selected, cpu_cores=2) == 2
    changed = dict(selected)
    changed.pop("OMP_NUM_THREADS")
    with pytest.raises(ValueError, match="thread setting"):
        worker_numerical_threads(changed, cpu_cores=2)
    changed = dict(selected, OPENMM_CPU_THREADS="3")
    with pytest.raises(ValueError, match="CPU allocation"):
        worker_numerical_threads(changed, cpu_cores=2)


def test_spawn_restores_parent_environment_after_failure(monkeypatch):
    monkeypatch.setenv("OMP_NUM_THREADS", "7")
    monkeypatch.delenv("MKL_NUM_THREADS", raising=False)
    before = dict(os.environ)
    with pytest.raises(RuntimeError, match="exposed launch failure"):
        with numerical_spawn_environment(numerical_threads=2):
            assert all(os.environ[name] == "2" for name in NUMERICAL_THREAD_ENV_VARS)
            raise RuntimeError("exposed launch failure")
    assert dict(os.environ) == before
