# SPDX-License-Identifier: MPL-2.0
"""Exposed, exact-assembly Wilson supply and conditional endpoint consumption."""
from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.adapters.methods.rubisco_combinations import analysis
from empirical_lawhood.adapters.methods.rubisco_combinations.records import CombinationEvaluationV1, CombinationForecastV1, CombinationScienceV1
from empirical_lawhood.adapters.methods.rubisco_combinations.source_binding import decode_source
from empirical_lawhood.adapters.physical.rubisco_kinetics.wilson2017 import TeProteinSpecificationV1, WilsonMutantPanelV1
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition, ScientificConditionScope
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_stable_id

D = Decimal
REFERENCE_TURNOVER = 'maize.kelvedon-glory.sharwood2016.table1.radiometric.25C'
REFERENCE_SPECIFICITY = 'galdieria-partita.uemura1997.abstract.specificity.assay-unresolved'
QUESTION = 'Does the exact exposed three-corner Wilson procedure supply a scoped two-endpoint estimate for the combined recipe?'
UNIT = 'rubisco-inquiry.exposed-quartet'


@dataclass(frozen=True, slots=True)
class RubiscoSupply(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-inquiry/supply'
    product_id: str
    science: CombinationScienceV1
    panel: WilsonMutantPanelV1
    forecast: CombinationForecastV1
    evaluation: CombinationEvaluationV1
    scope: ScientificConditionScope
    disposition: AssessmentDisposition

    def __post_init__(self):
        validate_stable_id(self.product_id, field_name='product_id')
        science, training, features, labels = analysis.prepare_roles(self.panel)
        if (self.science != science or self.forecast != analysis.predict(science, training, features)
                or self.evaluation != analysis.evaluate(science, analysis.commit(science, self.forecast), labels)
                or self.scope != scope(science) or self.disposition is not AssessmentDisposition.SATISFIED):
            raise ValueError('Rubisco supplier changes exact panel, quartet, estimate or assembly scope')


@dataclass(frozen=True, slots=True)
class RubiscoCandidate(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-inquiry/candidate'
    candidate_id: str
    assembly: TeProteinSpecificationV1
    turnover_s_inv: Decimal | None
    specificity_dimensionless: Decimal | None
    turnover_reference: str = REFERENCE_TURNOVER
    specificity_reference: str = REFERENCE_SPECIFICITY
    conditional_scenario: bool = True

    def __post_init__(self):
        validate_stable_id(self.candidate_id, field_name='candidate_id')
        for name in ('turnover_s_inv', 'specificity_dimensionless'):
            if getattr(self, name) is not None:
                validate_decimal(getattr(self, name), field_name=name, minimum=D(0))
        if type(self.conditional_scenario) is not bool:
            raise ValueError('conditional scenario flag must be boolean')


@dataclass(frozen=True, slots=True)
class RubiscoAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-inquiry/assessment'
    assessment_id: str
    supplier: ObjectIdentity
    scope: ScientificConditionScope
    candidate: RubiscoCandidate
    disposition: AssessmentDisposition
    turnover_ratio: Decimal | None
    specificity_ratio: Decimal | None
    forecast_turnover_relative_error: Decimal | None
    forecast_specificity_relative_error: Decimal | None
    reason_codes: tuple[str, ...]
    unresolved: tuple[str, ...] = ('G_PARTITA_PREPARATION_UNRESOLVED', 'PAIRED_ASSAY_COMPATIBILITY_UNRESOLVED')

    def __post_init__(self):
        validate_stable_id(self.assessment_id, field_name='assessment_id')
        if not isinstance(self.disposition, AssessmentDisposition):
            raise ValueError('assessment verdict must be typed')
        for name in ('turnover_ratio', 'specificity_ratio', 'forecast_turnover_relative_error', 'forecast_specificity_relative_error'):
            if getattr(self, name) is not None:
                validate_decimal(getattr(self, name), field_name=name, minimum=D(0))
        if self.disposition is not AssessmentDisposition.SATISFIED and not self.reason_codes:
            raise ValueError('negative assessments retain reasons')
        if self.unresolved != ('G_PARTITA_PREPARATION_UNRESOLVED', 'PAIRED_ASSAY_COMPATIBILITY_UNRESOLVED'):
            raise ValueError('conditional assessment must retain preparation and assay uncertainties')
        if self.disposition in {AssessmentDisposition.SATISFIED, AssessmentDisposition.FALSIFIED}:
            candidate = self.candidate
            if candidate.turnover_s_inv is None or candidate.specificity_dimensionless is None:
                raise ValueError('numeric assessment requires both exact endpoint operands')
            ratios = (candidate.turnover_s_inv / D('5.46'), candidate.specificity_dimensionless / D(238))
            verdict = AssessmentDisposition.SATISFIED if all(r >= 1 for r in ratios) else AssessmentDisposition.FALSIFIED
            if (self.turnover_ratio, self.specificity_ratio) != ratios or self.disposition is not verdict:
                raise ValueError('conditional endpoint ratios or noncompensating verdict differ')
        elif any(value is not None for value in (self.turnover_ratio, self.specificity_ratio,
                self.forecast_turnover_relative_error, self.forecast_specificity_relative_error)):
            raise ValueError('refused or unevaluable assessment cannot fabricate endpoint ratios')


def scope(science):
    return ScientificConditionScope('system.rubisco-inquiry.wilson', 'world.rubisco-inquiry.exposed',
        science.source_panel.object_id, ('specificity', 'turnover'), ('dimensionless', 's^-1'),
        'receiver.wilson-reported-point', 'clock.exposed-source-table',
        'Exact source-bound LSU A398T/P415A and SSU A48V recipe; three-corner zero-log-interaction point estimate, nineteen exposed rows; biological independent n unknown.',
        source_config_sha256=science.fingerprint(), instance_id=UNIT)


def supply(article, genbank):
    panel, parent = decode_source(article, genbank)
    science, training, features, labels = analysis.prepare_roles(panel, parent)
    forecast = analysis.predict(science, training, features)
    return RubiscoSupply('product.rubisco-inquiry.supply', science, panel,
                         forecast, analysis.evaluate(science, analysis.commit(science, forecast), labels),
                         scope(science), AssessmentDisposition.SATISFIED)


def authentic_candidate(supplier):
    row = next(r for r in supplier.panel.rows if r.native_table_row.ordinal_0based == 22)
    return RubiscoCandidate('candidate.wilson2017.row22', row.te_protein_specification,
                           row.endpoint('KCAT_C').mean, row.endpoint('SPECIFICITY_CO').mean)


def assess(supplier, candidate):
    # Reconstruct the typed supplier to enforce validation even for callers bypassing decoding.
    RubiscoSupply(supplier.product_id, supplier.science, supplier.panel, supplier.forecast, supplier.evaluation, supplier.scope, supplier.disposition)
    identity = ObjectIdentity.from_record(supplier.product_id, supplier)
    target = next(c for c in supplier.science.corners if c.role == 'TARGET')
    reasons = []
    if candidate.assembly != target.protein_recipe:
        reasons.append('WRONG_CANDIDATE_ASSEMBLY')
    if (candidate.turnover_reference != REFERENCE_TURNOVER or candidate.specificity_reference != REFERENCE_SPECIFICITY
            or not candidate.conditional_scenario):
        reasons.append('WRONG_REFERENCE_OR_UNCONDITIONAL_ADMISSION')
    if reasons:
        return RubiscoAssessment('assessment.rubisco-inquiry.use', identity, supplier.scope, candidate, AssessmentDisposition.REFUSED,
                                 None, None, None, None, tuple(sorted(reasons)))
    if candidate.turnover_s_inv is None or candidate.specificity_dimensionless is None:
        return RubiscoAssessment('assessment.rubisco-inquiry.use', identity, supplier.scope, candidate, AssessmentDisposition.UNEVALUABLE,
                                 None, None, None, None, ('MISSING_KINETIC_ENDPOINT',))
    turnover = candidate.turnover_s_inv / D('5.46')
    specificity = candidate.specificity_dimensionless / D(238)
    forecast = supplier.forecast.additive_point
    errors = (abs(candidate.turnover_s_inv - forecast.turnover_s_inv) / forecast.turnover_s_inv,
              abs(candidate.specificity_dimensionless - forecast.specificity_dimensionless) / forecast.specificity_dimensionless)
    passed = turnover >= 1 and specificity >= 1
    return RubiscoAssessment('assessment.rubisco-inquiry.use', identity, supplier.scope, candidate,
        AssessmentDisposition.SATISFIED if passed else AssessmentDisposition.FALSIFIED,
        turnover, specificity, *errors, () if passed else ('CONDITIONAL_JOINT_ENDPOINT_FAILED',))
