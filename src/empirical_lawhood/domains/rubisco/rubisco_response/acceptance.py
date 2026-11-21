# SPDX-License-Identifier: MPL-2.0
"""Frozen prediction, accuracy, service and finite-action selections.

Declared criteria are separate from evidence that they are scientifically
appropriate or that a candidate meets them.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_decimal, validate_nonempty, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import RubiscoPairedCase, exact, identities


@dataclass(frozen=True, slots=True)
class NominatedPrediction(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/nominated-prediction"
    prediction_id: str
    case: ObjectIdentity
    turnover_direction: str
    specificity_direction: str
    nominated_turnover_log_ratio_interval: tuple[Decimal, Decimal] | None
    sources: tuple[ObjectIdentity, ...]
    exposure_group: str
    meaning: str = "NOMINATED_PREDICTION_DISTINCT_FROM_DECISION_AND_DONOR_EFFECT"

    def __post_init__(self):
        validate_stable_id(self.prediction_id)
        validate_stable_id(self.exposure_group)
        exact(self.case, ObjectIdentity)
        if self.case.object_schema != RubiscoPairedCase.SCHEMA or self.case.object_version != RubiscoPairedCase.VERSION:
            raise ValueError("nominated prediction substitutes its exact paired case")
        if self.turnover_direction not in {"INCREASE", "DECREASE", "UNCHANGED", "UNSPECIFIED"}:
            raise ValueError("nominated turnover direction is not explicit")
        if self.specificity_direction not in {"PRESERVE_OR_INCREASE", "INCREASE", "DECREASE", "UNSPECIFIED"}:
            raise ValueError("nominated specificity direction is not explicit")
        interval = self.nominated_turnover_log_ratio_interval
        if interval is not None:
            if type(interval) is not tuple or len(interval) != 2:
                raise ValueError("nominated effect needs a complete sourced log-ratio interval")
            for value in interval:
                validate_decimal(value, field_name="nominated_log_ratio")
            if interval[0] > interval[1]:
                raise ValueError("nominated log-ratio interval is reversed")
        identities(self.sources)
        if self.meaning != "NOMINATED_PREDICTION_DISTINCT_FROM_DECISION_AND_DONOR_EFFECT":
            raise ValueError("donor effects or favorable witnesses cannot replace the nominated prediction")


@dataclass(frozen=True, slots=True)
class ResponseAcceptance(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/acceptance"
    acceptance_id: str
    absolute_log_endpoint_tolerances: tuple[Decimal, Decimal]
    paired_log_endpoint_tolerances: tuple[Decimal, Decimal]
    uncertainty_interpretation: str
    joint_coverage_level: Decimal | None
    uncertainty_procedure: ObjectIdentity
    minimum_useful_service: Decimal
    maximum_false_admission: Decimal
    reference_method: ObjectIdentity
    conventional_baseline: ObjectIdentity
    cost_metric: str
    cost_unit: str
    planned_reuse_count: int
    permitted_refinement_ids: tuple[str, ...]
    maximum_refinements: int
    maximum_native_acquisitions: int
    checkpoint_rule: str
    stopping_conditions: tuple[str, ...]
    reference_fallback: ObjectIdentity | None
    predictive_evidence_requirement_ids: tuple[str, ...]
    gp_applicability_requirement_id: str
    matrix_handoff_requirement_id: str
    criterion_admission_requirement_ids: tuple[str, ...]
    sources: tuple[ObjectIdentity, ...]
    interpretation: str = "FROZEN_SELECTIONS_NOT_VALIDATION_OR_EXECUTION_AUTHORITY"

    def __post_init__(self):
        validate_stable_id(self.acceptance_id)
        for name in ("absolute_log_endpoint_tolerances", "paired_log_endpoint_tolerances"):
            values = getattr(self, name)
            if type(values) is not tuple or len(values) != 2:
                raise ValueError("accuracy must retain turnover and specificity jointly")
            for value in values:
                validate_decimal(value, field_name=name, minimum=Decimal(0))
                if value == 0:
                    raise ValueError("joint endpoint tolerances must be positive")
        if self.uncertainty_interpretation not in {"FINITE_JOINT_SUPPORT", "CONSERVATIVE_ERROR_SET", "DECLARED_PROBABILISTIC_JOINT_REGION"}:
            raise ValueError("joint uncertainty meaning must be frozen")
        probabilistic = self.uncertainty_interpretation == "DECLARED_PROBABILISTIC_JOINT_REGION"
        if probabilistic != (self.joint_coverage_level is not None):
            raise ValueError("probabilistic uncertainty needs its declared joint coverage")
        if self.joint_coverage_level is not None:
            validate_decimal(self.joint_coverage_level, field_name="joint_coverage_level")
            if not 0 < self.joint_coverage_level <= 1:
                raise ValueError("joint coverage must lie in (0, 1]")
        for name in ("minimum_useful_service", "maximum_false_admission"):
            value = getattr(self, name)
            validate_decimal(value, field_name=name, minimum=Decimal(0))
            if value > 1:
                raise ValueError("service and false-admission criteria must lie within [0, 1]")
        if self.minimum_useful_service == 0:
            raise ValueError("always abstaining cannot meet a useful-service criterion")
        for value in (self.uncertainty_procedure, self.reference_method, self.conventional_baseline):
            exact(value, ObjectIdentity)
        if self.reference_method == self.conventional_baseline:
            raise ValueError("the reference and conventional baseline must be distinct selections")
        if self.reference_fallback is not None:
            exact(self.reference_fallback, ObjectIdentity)
        for name in ("cost_metric", "cost_unit", "checkpoint_rule"):
            validate_nonempty(getattr(self, name), field_name=name)
        if type(self.planned_reuse_count) is not int or self.planned_reuse_count <= 0:
            raise ValueError("cost comparison requires a positive declared reuse count")
        for name in ("maximum_refinements", "maximum_native_acquisitions"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError("finite policy ceilings must be nonnegative integers")
        for name in ("permitted_refinement_ids", "predictive_evidence_requirement_ids",
                     "criterion_admission_requirement_ids", "stopping_conditions"):
            require_sorted_unique_strings(getattr(self, name), field_name=name,
                allow_empty=name in {"permitted_refinement_ids", "criterion_admission_requirement_ids"})
        if bool(self.permitted_refinement_ids) != bool(self.maximum_refinements):
            raise ValueError("finite refinements require both a menu and a positive ceiling")
        for name in ("gp_applicability_requirement_id", "matrix_handoff_requirement_id"):
            validate_stable_id(getattr(self, name))
        for name in self.permitted_refinement_ids + self.predictive_evidence_requirement_ids + self.criterion_admission_requirement_ids:
            validate_stable_id(name)
        identities(self.sources)
        if self.interpretation != "FROZEN_SELECTIONS_NOT_VALIDATION_OR_EXECUTION_AUTHORITY":
            raise ValueError("declared acceptance cannot supply biological validation or native authority")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.acceptance_id, self)
