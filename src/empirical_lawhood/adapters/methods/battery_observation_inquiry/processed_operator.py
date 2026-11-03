# SPDX-License-Identifier: MPL-2.0
"""Passive exact selected operator custody for later independent residual checks.

Capture only functions and sparse matrices already produced by the selected
native solver setup. No function evaluation, construction or model replay occurs
here. Serialization preserves actual operator operands; it does not assess them.
"""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id, validate_sha256
from . import contracts as ct


@dataclass(frozen=True, slots=True)
class ProcessedOperator(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-observation-inquiry/actual-processed-operator"
    operator_id: str
    native_configuration: ObjectIdentity
    preparation_protocol: ObjectIdentity
    actual_solver_assignment: ObjectIdentity
    model_expression_sha256: str
    rhs_serialization: str
    algebraic_serialization: str
    ordered_scalar_input_names: tuple[str, ...]
    rhs_input_shapes: tuple[tuple[int, int], ...]
    algebraic_input_shapes: tuple[tuple[int, int], ...]
    rhs_output_shape: tuple[int, int]
    algebraic_output_shape: tuple[int, int]
    mass_matrix_shape: tuple[int, int]
    mass_matrix_csc_indptr: tuple[int, ...]
    mass_matrix_csc_indices: tuple[int, ...]
    mass_matrix_csc_binary64: tuple[str, ...]
    source_standard_form_dae: bool
    scope: str = "PASSIVE_ACTUAL_PROCESSED_RHS_ALGEBRAIC_AND_MASS_MATRIX;NOT_RESIDUAL_OR_PHYSICAL_QUALIFICATION"

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.battery_refined_inquiry import preparation_contracts as pc
        validate_stable_id(self.operator_id)
        validate_sha256(self.model_expression_sha256)
        if (self.native_configuration.object_schema != "empirical-lawhood/battery-segmented/native-config"
                or self.preparation_protocol.object_schema != pc.PreparationProtocol.SCHEMA
                or self.actual_solver_assignment.object_schema != "empirical-lawhood/battery-observation-inquiry/actual-precision-level-assignment"
                or type(self.rhs_serialization) is not str or not self.rhs_serialization
                or type(self.algebraic_serialization) is not str or not self.algebraic_serialization
                or self.ordered_scalar_input_names != tuple(sorted(set(self.ordered_scalar_input_names)))
                or not self.ordered_scalar_input_names
                or self.rhs_input_shapes != ((1, 1), (174, 1), (len(self.ordered_scalar_input_names), 1))
                or self.algebraic_input_shapes != self.rhs_input_shapes
                or self.rhs_output_shape != (173, 1) or self.algebraic_output_shape != (1, 1)
                or self.mass_matrix_shape != (174, 174)
                or len(self.mass_matrix_csc_indptr) != 175 or self.mass_matrix_csc_indptr[0] != 0
                or self.mass_matrix_csc_indptr[-1] != len(self.mass_matrix_csc_indices)
                or len(self.mass_matrix_csc_indices) != len(self.mass_matrix_csc_binary64)
                or any(type(i) is not int or not 0 <= i < 174 for i in self.mass_matrix_csc_indices)
                or any(type(i) is not int or i < 0 for i in self.mass_matrix_csc_indptr)
                or any(a > b for a, b in zip(self.mass_matrix_csc_indptr, self.mass_matrix_csc_indptr[1:]))
                or type(self.source_standard_form_dae) is not bool
                or self.scope != "PASSIVE_ACTUAL_PROCESSED_RHS_ALGEBRAIC_AND_MASS_MATRIX;NOT_RESIDUAL_OR_PHYSICAL_QUALIFICATION"):
            raise ValueError("processed operator loses its exact complete selected dimensions/source/claim scope")
        import math
        for bit in self.mass_matrix_csc_binary64:
            value = float.fromhex(bit)
            if not math.isfinite(value) or value.hex() != bit:
                raise ValueError("processed mass matrix loses its original finite binary64 values")
        for left, right in zip(self.mass_matrix_csc_indptr, self.mass_matrix_csc_indptr[1:]):
            indices = self.mass_matrix_csc_indices[left:right]
            if indices != tuple(sorted(set(indices))):
                raise ValueError("processed mass matrix has reordered/duplicate sparse coordinates")


def capture_processed_operator(model, inputs_list, config, protocol, assignment):
    """Read already prepared exact functions; never evaluate or compile them."""
    from empirical_lawhood.adapters.methods.battery_refined_inquiry import prepared_native as passive
    if (model.convert_to_format != "casadi" or model.len_rhs != 173 or model.len_alg != 1
            or len(inputs_list) != 1 or tuple(inputs_list[0]) != tuple(sorted(inputs_list[0]))):
        raise ValueError("passive operator capture changes actual selected model/input preparation")
    if any(type(value) not in (float, int) for value in inputs_list[0].values()):
        raise ValueError("selected passive operator capture needs its actual scalar input layout")
    rhs, algebraic = model.rhs_eval, model.algebraic_eval
    if rhs.n_in() != 3 or algebraic.n_in() != 3 or rhs.n_out() != 1 or algebraic.n_out() != 1:
        raise ValueError("passive capture omits actual complete function input/output denominator")
    mass = model.mass_matrix.entries.tocsc(copy=True)
    mass.sort_indices()
    return ProcessedOperator("operator." + assignment.assignment_id,
        ct.identity(config, "config_id"), ct.identity(protocol, "protocol_id"), ct.identity(assignment, "assignment_id"),
        passive._model_digest(model, ("rhs", "algebraic")), rhs.serialize(), algebraic.serialize(),
        tuple(inputs_list[0]), tuple((rhs.size1_in(i), rhs.size2_in(i)) for i in range(3)),
        tuple((algebraic.size1_in(i), algebraic.size2_in(i)) for i in range(3)),
        (rhs.size1_out(0), rhs.size2_out(0)), (algebraic.size1_out(0), algebraic.size2_out(0)),
        tuple(int(value) for value in mass.shape), tuple(int(value) for value in mass.indptr),
        tuple(int(value) for value in mass.indices), tuple(float(value).hex() for value in mass.data),
        bool(model.is_standard_form_dae))


def require_operator(operator, assignment, window):
    from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_science as ss
    if type(operator) is not ProcessedOperator:
        raise ValueError("controlled observation omits its actual processed operator")
    operator.__post_init__()
    evidence = window.result.evidence
    if (operator.actual_solver_assignment != ct.identity(assignment, "assignment_id")
            or operator.native_configuration != ct.identity(evidence.trace.config, "config_id")
            or operator.preparation_protocol != ct.identity(evidence.protocol, "protocol_id")
            or operator.model_expression_sha256 != evidence.layout.model_expression_sha256):
        raise ValueError("processed operator substitutes actual assignment/model/layout source")
    ss.authenticate_payloads(evidence.native_receipt, (operator,))
