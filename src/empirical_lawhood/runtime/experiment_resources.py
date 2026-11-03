# SPDX-License-Identifier: MPL-2.0
"""Operational resource choices awaiting the actual candidate projection.

This selection contains no candidate or issued-extension identity. Binding it
copies its operational choices into the existing strict resource envelope; it
does not issue a study or establish scientific or execution authority.
"""

from dataclasses import dataclass, fields
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings,
    validate_sha256, validate_stable_id,
)
from empirical_lawhood.runtime.execution_envelope import (
    ChildResourceTokenLimit, ExecutionResourceEnvelopeSpec, ExecutionResourceTaskCellSpec,
    NonTimeResourceBudget, ProgressLivenessContract, RosterCapacityBranchSpec,
)
from empirical_lawhood.runtime.study_issue import IssuedExtensionSet


@dataclass(frozen=True, slots=True)
class ExecutionResourceSelection(CanonicalRecord):
    """Exact resource choices awaiting the actual compiler extension projection.

    Components and their closed types are checked here. Binding must still pass
    the existing envelope owner's cross-field topology, token, JIT and aggregate
    rules. The existing preissue compiler owns compatibility with actual tasks.
    """

    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/execution-resource-selection"

    envelope_spec_id: str
    task_cells: tuple[ExecutionResourceTaskCellSpec, ...]
    child_token_limits: tuple[ChildResourceTokenLimit, ...]
    roster_capacity_branches: tuple[RosterCapacityBranchSpec, ...]
    allowlisted_retry_reason_codes: tuple[str, ...]
    allowlisted_resource_stop_reason_codes: tuple[str, ...]
    predevelopment_jit_signature_census: ObjectIdentity | None
    jit_graph_signature_manifest: ObjectIdentity | None
    maximum_parallel_tasks: int
    aggregate_memory_ceiling_bytes: int
    resource_lock_ids: tuple[str, ...]
    non_gating_forecast_records: tuple[ObjectIdentity, ...]
    resource_contract_sha256: str
    nonrefundable_reservations: bool
    first_valid_success_wins: bool
    unknown_completion_requires_new_disposition: bool
    elapsed_time_has_no_control_effect: bool

    def __post_init__(self):
        validate_stable_id(self.envelope_spec_id, field_name="envelope_spec_id")
        for name, kind, attribute in (
                ("task_cells", ExecutionResourceTaskCellSpec, "cell_id"),
                ("child_token_limits", ChildResourceTokenLimit, "child_id"),
                ("roster_capacity_branches", RosterCapacityBranchSpec, "branch_id"),
                ("non_gating_forecast_records", ObjectIdentity, "object_id")):
            rows = getattr(self, name)
            if type(rows) is not tuple or any(type(row) is not kind for row in rows):
                raise TypeError("protected resource selection requires exact typed " + name)
            require_sorted_unique_ids(rows, attribute=attribute, field_name=name)
            for row in rows:
                row.__post_init__()
        for cell in self.task_cells:
            if type(cell.resource_budget) is not NonTimeResourceBudget:
                raise TypeError("protected resource cells require exact existing non-time budgets")
            cell.resource_budget.__post_init__()
            if cell.progress_liveness is not None:
                if type(cell.progress_liveness) is not ProgressLivenessContract:
                    raise TypeError("protected resource progress requires its existing typed contract")
                cell.progress_liveness.__post_init__()
        for name in ("allowlisted_retry_reason_codes", "allowlisted_resource_stop_reason_codes", "resource_lock_ids"):
            values = getattr(self, name)
            if type(values) is not tuple:
                raise TypeError("protected resource selection requires exact tuple " + name)
            require_sorted_unique_strings(values, field_name=name)
        for name in ("predevelopment_jit_signature_census", "jit_graph_signature_manifest"):
            value = getattr(self, name)
            if value is not None:
                if type(value) is not ObjectIdentity:
                    raise TypeError("protected resource JIT references require exact identities")
                value.__post_init__()
        for name in ("maximum_parallel_tasks", "aggregate_memory_ceiling_bytes"):
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise ValueError("protected resource selection requires positive integer " + name)
        for name in ("nonrefundable_reservations", "first_valid_success_wins",
                "unknown_completion_requires_new_disposition", "elapsed_time_has_no_control_effect"):
            if getattr(self, name) is not True:
                raise ValueError("protected resource selection weakens its exact durability rule: " + name)
        validate_sha256(self.resource_contract_sha256, field_name="resource_contract_sha256")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.envelope_spec_id, self)


def bind_execution_resources(selection: ExecutionResourceSelection, *,
        issued_extensions: IssuedExtensionSet) -> ExecutionResourceEnvelopeSpec:
    """Bind the caller's actual owning projection, preserving every resource choice.

    The API must supply the extension record from its actual candidate compiler
    projection and enforce source/candidate equality. This pure function neither
    authenticates custody nor confers issue, qualification or execution authority.
    """
    if type(selection) is not ExecutionResourceSelection or type(issued_extensions) is not IssuedExtensionSet:
        raise TypeError("execution resources require the exact unbound selection and actual typed extension set")
    selection.__post_init__()
    issued_extensions.__post_init__()
    values = {field.name: getattr(selection, field.name) for field in fields(ExecutionResourceSelection)}
    return ExecutionResourceEnvelopeSpec(**values, issued_study_extensions=ObjectIdentity.from_record(
        issued_extensions.issued_extension_set_id, issued_extensions))
