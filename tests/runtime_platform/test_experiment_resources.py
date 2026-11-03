# SPDX-License-Identifier: MPL-2.0
"""Actual candidate resource parity and closed-component/envelope refusals."""

from dataclasses import fields, replace
from hashlib import sha256
import inspect

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_resources import (
    ProtectedFactorialResourceSelection, bind_protected_factorial_resources,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes, decode_canonical_record
from empirical_lawhood.runtime.compiler import ProtocolCompilationError
from empirical_lawhood.runtime.experiment_resources import ExecutionResourceSelection, bind_execution_resources
from tests import test_matrix_protected_factorial_resources as fixtures


projected = fixtures.projected


RESOURCE_FIELDS = (
    "envelope_spec_id", "task_cells", "child_token_limits", "roster_capacity_branches",
    "allowlisted_retry_reason_codes", "allowlisted_resource_stop_reason_codes",
    "predevelopment_jit_signature_census", "jit_graph_signature_manifest", "maximum_parallel_tasks",
    "aggregate_memory_ceiling_bytes", "resource_lock_ids", "non_gating_forecast_records",
    "resource_contract_sha256", "nonrefundable_reservations", "first_valid_success_wins",
    "unknown_completion_requires_new_disposition", "elapsed_time_has_no_control_effect",
)


def shared(selection):
    return ExecutionResourceSelection(**{name: getattr(selection, name) for name in RESOURCE_FIELDS})


def test_preserved_e4_schema_constructor_bytes_and_closed_decoder(projected):
    original = projected.selection
    assert type(original) is ProtectedFactorialResourceSelection
    assert original.__class__.__module__ == "empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_resources"
    assert tuple(row.name for row in fields(original)) == RESOURCE_FIELDS
    assert tuple(inspect.signature(ProtectedFactorialResourceSelection).parameters) == RESOURCE_FIELDS
    assert original.VERSION == "1.0.0"
    assert sha256(original.canonical_bytes()).hexdigest() == "98548058c4f51891a5afc8fabdccac337ff4ad942943135e0872063bef226644"
    assert decode_canonical_bytes(original.canonical_bytes(), ProtectedFactorialResourceSelection, maximum_bytes=16384) == original
    document = original.to_document()
    document["value"]["caller_bypass"] = True
    with pytest.raises(ValueError):
        decode_canonical_record(document, ProtectedFactorialResourceSelection)
    with pytest.raises((AttributeError, TypeError)):
        original.caller_bypass = True


def test_shared_owner_binds_same_actual_candidate_envelope_and_preissue_plan(projected):
    selection = shared(projected.selection)
    assert tuple(row.name for row in fields(selection)) == RESOURCE_FIELDS
    assert selection.SCHEMA == "empirical-lawhood/runtime/execution-resource-selection"
    assert selection.identity != projected.selection.identity
    assert decode_canonical_bytes(selection.canonical_bytes(), ExecutionResourceSelection, maximum_bytes=16384) == selection
    generic = bind_execution_resources(selection, issued_extensions=projected.extensions)
    original = bind_protected_factorial_resources(projected.selection, issued_extensions=projected.extensions)
    assert generic.canonical_bytes() == original.canonical_bytes()
    assert sha256(generic.canonical_bytes()).hexdigest() == "fc966a69126bf04e9f5b7f10f7cbc006e2e37270e6eef34fb4950c15e56d45a3"
    assert fixtures._preissue(projected, generic).canonical_bytes() == fixtures._preissue(projected, original).canonical_bytes()


@pytest.mark.parametrize("selection_kind", ("generic", "e4"))
def test_binding_keeps_exact_owning_selection_types(projected, selection_kind):
    supplied = projected.selection if selection_kind == "e4" else shared(projected.selection)
    binding = bind_execution_resources if selection_kind == "e4" else bind_protected_factorial_resources
    with pytest.raises(TypeError, match="exact unbound selection"):
        binding(supplied, issued_extensions=projected.extensions)


@pytest.mark.parametrize("supplied", (None, {}, "identity"))
def test_generic_binding_refuses_placeholder_extension_records(projected, supplied):
    if supplied == "identity":
        from empirical_lawhood.kernel.provenance import ObjectIdentity

        supplied = ObjectIdentity.from_record(projected.extensions.issued_extension_set_id, projected.extensions)
    with pytest.raises(TypeError, match="actual typed extension set"):
        bind_execution_resources(shared(projected.selection), issued_extensions=supplied)


@pytest.mark.parametrize("damage", ("cell-type", "parallel-bool", "durability-int", "duplicate-cell"))
def test_generic_component_checks_remain_strict_before_binding(projected, damage):
    selection = shared(projected.selection)
    with pytest.raises((ValueError, TypeError)):
        if damage == "cell-type":
            replace(selection, task_cells=list(selection.task_cells))
        elif damage == "parallel-bool":
            replace(selection, maximum_parallel_tasks=True)
        elif damage == "durability-int":
            replace(selection, first_valid_success_wins=1)
        else:
            replace(selection, task_cells=(*selection.task_cells, selection.task_cells[-1]))


@pytest.mark.parametrize("damage", ("tokens", "branch", "aggregate", "jit"))
def test_generic_binding_still_exercises_existing_complete_envelope_rules(projected, damage):
    selection = shared(projected.selection)
    if damage == "tokens":
        selection = replace(selection, child_token_limits=(replace(selection.child_token_limits[0], physical_execution_token_limit=1),))
    elif damage == "branch":
        first, *rest = selection.roster_capacity_branches
        selection = replace(selection, roster_capacity_branches=(replace(first, cell_ids=("cell.absent-generic",)), *rest))
    elif damage == "aggregate":
        selection = replace(selection, aggregate_memory_ceiling_bytes=1)
    else:
        selection = replace(selection, jit_graph_signature_manifest=selection.non_gating_forecast_records[0])
    with pytest.raises(ValueError):
        bind_execution_resources(selection, issued_extensions=projected.extensions)


def test_generic_envelope_cannot_bind_another_actual_extension_projection(projected):
    envelope = bind_execution_resources(shared(projected.selection), issued_extensions=projected.extensions)
    changed = replace(projected.extensions, issued_extension_set_id="issued-extensions.foreign-generic")
    with pytest.raises(ProtocolCompilationError, match="another issued extension set"):
        fixtures._preissue(projected, envelope, extensions=changed)
