# SPDX-License-Identifier: MPL-2.0
"""Unbound operational resources for protected factorial authoring.

This selection contains no candidate or issued-extension identity. Binding it
copies its operational choices into the existing strict resource envelope; it
does not issue a study or establish scientific or execution authority.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.runtime.execution_envelope import ExecutionResourceEnvelopeSpec
from empirical_lawhood.runtime.experiment_resources import ExecutionResourceSelection, bind_execution_resources
from empirical_lawhood.runtime.study_issue import IssuedExtensionSet


@dataclass(frozen=True, slots=True)
class ProtectedFactorialResourceSelection(ExecutionResourceSelection):
    """Exact resource choices awaiting the actual compiler extension projection.

    Components and their closed types are checked here. Binding must still pass
    the existing envelope owner's cross-field topology, token, JIT and aggregate
    rules. The existing preissue compiler owns compatibility with actual tasks.
    """

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/protected-factorial-resource-selection"


def bind_protected_factorial_resources(selection: ProtectedFactorialResourceSelection, *,
        issued_extensions: IssuedExtensionSet) -> ExecutionResourceEnvelopeSpec:
    """Bind the caller's actual owning projection, preserving every resource choice.

    The API must supply the extension record from its actual candidate compiler
    projection and enforce source/candidate equality. This pure function neither
    authenticates custody nor confers issue, qualification or execution authority.
    """
    if type(selection) is not ProtectedFactorialResourceSelection or type(issued_extensions) is not IssuedExtensionSet:
        raise TypeError("protected resources require the exact unbound selection and actual typed extension set")
    selection.__post_init__()
    issued_extensions.__post_init__()
    shared = ExecutionResourceSelection(
        envelope_spec_id=selection.envelope_spec_id,
        task_cells=selection.task_cells,
        child_token_limits=selection.child_token_limits,
        roster_capacity_branches=selection.roster_capacity_branches,
        allowlisted_retry_reason_codes=selection.allowlisted_retry_reason_codes,
        allowlisted_resource_stop_reason_codes=selection.allowlisted_resource_stop_reason_codes,
        predevelopment_jit_signature_census=selection.predevelopment_jit_signature_census,
        jit_graph_signature_manifest=selection.jit_graph_signature_manifest,
        maximum_parallel_tasks=selection.maximum_parallel_tasks,
        aggregate_memory_ceiling_bytes=selection.aggregate_memory_ceiling_bytes,
        resource_lock_ids=selection.resource_lock_ids,
        non_gating_forecast_records=selection.non_gating_forecast_records,
        resource_contract_sha256=selection.resource_contract_sha256,
        nonrefundable_reservations=selection.nonrefundable_reservations,
        first_valid_success_wins=selection.first_valid_success_wins,
        unknown_completion_requires_new_disposition=selection.unknown_completion_requires_new_disposition,
        elapsed_time_has_no_control_effect=selection.elapsed_time_has_no_control_effect)
    try:
        return bind_execution_resources(shared, issued_extensions=issued_extensions)
    except ValueError as error:
        raise ValueError("protected resource binding failed final envelope validation: " + str(error)) from error
