# SPDX-License-Identifier: MPL-2.0
# ruff: noqa: F811
"""Exact compiler CONFIG refusal before protected scientific bodies, no effects.

The unchanged disclosed protected-prefix helper supplies real typed task/input
contracts. Adverse frozen metadata is rebound consistently to its task identity
so the strict shared CONFIGURATION owner must refuse before any science read.
No issued authority, Ready, native work, output receipt or qualification is made.
"""
from dataclasses import replace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_protected_workers as worker
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.plans import ScientificInputRole
from tests.test_matrix_e4_protected_entry_source_identity import _deny_effects, _prefix_case
from tests.test_matrix_selected_e4_fixtures import selected_e4_populations, selected_bridge, transfer  # noqa: F401
from tests.test_matrix_selected_e4_methods import selected_revision  # noqa: F401


@pytest.mark.parametrize("damage", ("missing", "edge-id", "edge-size"))
def test_protected_prefix_refuses_frozen_configuration_substitution_before_science_body(selected_revision,
        monkeypatch, damage):
    _, _, _, _, runner, context = _prefix_case(selected_revision)
    _deny_effects(monkeypatch)
    prepared = context.prepared_invocation
    task = prepared.execution_task_record
    config_edge, = (value for value in task.scientific_inputs
        if value.scientific_role is ScientificInputRole.CONFIGURATION)
    if damage == "missing":
        edges = tuple(value for value in task.scientific_inputs if value is not config_edge)
    else:
        changed = (replace(config_edge, edge_id="edge.foreign.configuration") if damage == "edge-id"
            else replace(config_edge, maximum_size_bytes=config_edge.maximum_size_bytes + 1))
        edges = tuple(sorted((changed if value is config_edge else value for value in task.scientific_inputs),
            key=lambda value: value.edge_id))
    task = replace(task, scientific_inputs=edges)
    prepared = replace(prepared, execution_task_record=task,
        execution_task=ObjectIdentity.from_record(task.task_id, task))
    context = replace(context, prepared_invocation=prepared)
    actual_read, reads = worker._read, []
    def read(port, contract):
        reads.append(port.artifact_id)
        if port.artifact_id != context.config.artifact_id:
            pytest.fail("unvalidated CONFIG metadata opened a protected scientific input")
        return actual_read(port, contract)
    monkeypatch.setattr(worker, "_read", read)
    try:
        with pytest.raises(ValueError, match="CONFIGURATION"):
            worker._decode(context, runner)
        assert reads == [context.config.artifact_id]
        assert context.prepared_invocation.native_work is None
    finally:
        for port in context.input_ports:
            port.close()
