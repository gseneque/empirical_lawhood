# SPDX-License-Identifier: MPL-2.0
"""Bounded noncanonical original-custody views supplied by installed API code."""
from dataclasses import dataclass

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import require_sorted_unique_strings
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from empirical_lawhood.runtime.plans import ExecutionPlan

from .programme_calibration import ScheduledProgrammeCalibrationEvidence


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeCurrentCalibration:
    """Actual current producer custody, before its terminal qualifier exists.

    This is not QualifiedParentEvidence: it contains no invented qualification,
    reveal result or supported adjudication. The API authenticates its original
    current package/grants/plan/producer before constructing this view.
    """
    package: object
    execution_plan: ExecutionPlan
    producing_receipt: CanonicalTaskReceipt
    calibration_evidence: ScheduledProgrammeCalibrationEvidence
    prior_executions: tuple = ()
    prior_scope_products: tuple = ()


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeVerifiedCalibrationCustody:
    """Identity-only result of current authority and all original-wave replay."""
    configuration: ObjectIdentity
    programme: ObjectIdentity
    bank: ObjectIdentity
    execution_plan: ObjectIdentity
    execution_task: ObjectIdentity
    producing_receipt: ObjectIdentity
    evidence: ObjectIdentity
    input_materialization_ids: tuple[str, ...]
    dependency_receipt_ids: tuple[str, ...]
    prior_bindings: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        require_sorted_unique_strings(self.input_materialization_ids, field_name='actual qualifier inputs', allow_empty=False)
        require_sorted_unique_strings(self.dependency_receipt_ids, field_name='actual qualifier receipt dependencies', allow_empty=False)
        if len(self.prior_bindings) != 16 or len(set(self.prior_bindings)) != 16:
            raise ValueError('global qualifier custody requires all sixteen exact original acquisitions')
