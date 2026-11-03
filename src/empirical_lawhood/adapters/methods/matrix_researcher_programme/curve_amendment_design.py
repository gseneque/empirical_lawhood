# SPDX-License-Identifier: MPL-2.0
"""The fixed prospective 2026-10-25.1 change, independent of access and I/O.

Only unentered prediction stages may consume this design. The public amendment
owner must establish the original exposure and unentered-stage custody first.
The exposed E1/E2 definitions, native roster, assay and calibration are retained.
"""
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_response.causal_hessian import CAUSAL_HESSIAN_RULE, CausalHessianRule
from empirical_lawhood.adapters.methods.matrix_factor_response.curve_contract import (
    CURVE_IMPROVEMENT_RULE, CURVE_LOSS_RULE, CURVE_RELATION_LOSS_RULE, CURVE_SELECTION_RULE, CURVE_TRANSFER_PROCEDURE,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_specification import matched_e3_estimators
from empirical_lawhood.adapters.methods.matrix_factor_response.mechanism_readout import MECHANISM_READOUT_RULE, MechanismReadoutRule
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id

from .scientific_design import MatrixProgrammeScientificDesign


@dataclass(frozen=True, slots=True)
class MatrixCurveMechanismAmendmentRule(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/curve-mechanism-amendment-rule'
    amendment: str = '2026-10-25.1'
    loss: str = CURVE_LOSS_RULE
    selection: str = CURVE_SELECTION_RULE
    margin: Decimal = Decimal('.1')
    root_numerics: str = 'DECIMAL_PRECISION60_ROUND_HALF_EVEN_LOG_SQRT_EXACT_FRACTION_GROUP_MEANS_AND_DIFFERENCES'
    median_K: str = 'PER_VIEW_LOWER_CENTRAL_INTEGER_FITTING_PARTITION_ONLY'
    causal: CausalHessianRule = CAUSAL_HESSIAN_RULE
    mechanism: MechanismReadoutRule = MECHANISM_READOUT_RULE
    scope: str = 'UNENTERED_TRAIN_E3_E4_E5_E6_ORIGINAL_E1_E2_RETAINED_AS_EXPOSED_EVIDENCE'

    def __post_init__(self):
        if (self.amendment != '2026-10-25.1' or self.loss != CURVE_LOSS_RULE or self.selection != CURVE_SELECTION_RULE
                or type(self.margin) is not Decimal or self.margin != Decimal('.1')
                or self.root_numerics != 'DECIMAL_PRECISION60_ROUND_HALF_EVEN_LOG_SQRT_EXACT_FRACTION_GROUP_MEANS_AND_DIFFERENCES'
                or self.median_K != 'PER_VIEW_LOWER_CENTRAL_INTEGER_FITTING_PARTITION_ONLY'
                or self.causal != CAUSAL_HESSIAN_RULE or self.mechanism != MECHANISM_READOUT_RULE
                or self.scope != 'UNENTERED_TRAIN_E3_E4_E5_E6_ORIGINAL_E1_E2_RETAINED_AS_EXPOSED_EVIDENCE'):
            raise ValueError('curve amendment changes its explicitly selected version, numerical owners or prospective scope')
        self.causal.__post_init__()
        self.mechanism.__post_init__()


CURVE_MECHANISM_AMENDMENT = MatrixCurveMechanismAmendmentRule()


def amend_curve_design(original, *, record_id):
    """No new allocation, margin, feature, recipe or optional attribution choice."""
    if type(original) is not MatrixProgrammeScientificDesign:
        raise TypeError('curve amendment requires the actual original complete scientific design')
    original.__post_init__()
    validate_stable_id(record_id)
    if not original.e3.measurement.is_matched or original.e3.is_curve_primary:
        raise ValueError('curve amendment requires its original paired58 K design exactly once')
    e3 = replace(original.e3, methods=matched_e3_estimators(curve_primary=True),
        assessment=replace(original.e3.assessment, improvement_rule=CURVE_IMPROVEMENT_RULE, improvement_margin=Decimal('.1')))
    relation = replace(original.e4_revision.matched_selection, loss=CURVE_RELATION_LOSS_RULE)
    criterion = replace(original.e5_development.criterion, procedure=CURVE_TRANSFER_PROCEDURE)
    return replace(original, record_id=record_id, e3=e3,
        e4_revision=replace(original.e4_revision, matched_selection=relation),
        e4_structure=replace(original.e4_structure, prediction=relation),
        e4_nomination=replace(original.e4_nomination,
            account_rule='FROZEN_SR_BR_CURVE_AFTER_ELIGIBLE_DEV_NO_CONFIRMATION_SELECTION', margin_denominator=10),
        e5_development=replace(original.e5_development, criterion=criterion),
        e5_confirmation=replace(original.e5_confirmation, criterion=criterion),
        e6=replace(original.e6, criterion=criterion), e6_policy=replace(original.e6_policy, criterion=criterion))
