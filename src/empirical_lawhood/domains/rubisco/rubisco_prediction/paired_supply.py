# SPDX-License-Identifier: MPL-2.0
"""Joint WT/mutant support with explicit dependence and model alternatives.

A scenario census is not a probability mixture. Covariance is retained as
evidence and never supplies missing coverage, missing outcomes or independence.
"""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction as F
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact, identities
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition, AssessmentPhase, RequirementSupplyAssessment, ScientificConnectionSpec, ScientificRequirementSpec
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_decimal, validate_nonempty, validate_stable_id

RAW_LOG_AXES = ("wt.kcat_c", "wt.specificity", "mutant.kcat_c", "mutant.specificity")
ANCHORED_LOG_AXES = (*RAW_LOG_AXES, "anchor.kcat_c", "anchor.specificity")


@dataclass(frozen=True, slots=True)
class EndpointValues(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/endpoint-values"
    kcat_c_s_inv: Exact
    specificity: Exact

    def __post_init__(self):
        for value in (self.kcat_c_s_inv, self.specificity):
            exact(value, Exact)
            if value.fraction <= 0:
                raise ValueError("identified log-kinetic endpoints must be strictly positive")

    @classmethod
    def of(cls, turnover, specificity):
        return cls(Exact.of(turnover), Exact.of(specificity))


@dataclass(frozen=True, slots=True)
class PairedJointValue(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/paired-joint-value"
    value_id: str
    wild_type: EndpointValues
    mutant: EndpointValues
    anchor_wild_type: EndpointValues | None = None
    anchored_mutant: EndpointValues | None = None

    def __post_init__(self):
        validate_stable_id(self.value_id)
        for value in (self.wild_type, self.mutant):
            exact(value, EndpointValues)
        if (self.anchor_wild_type is None) != (self.anchored_mutant is None):
            raise ValueError("anchored output must retain its actual WT anchor and raw outputs")
        if self.anchor_wild_type is not None:
            exact(self.anchor_wild_type, EndpointValues)
            exact(self.anchored_mutant, EndpointValues)
            if self.anchored_mutant != EndpointValues.of(
                    self.anchor_wild_type.kcat_c_s_inv.fraction * self.turnover_ratio,
                    self.anchor_wild_type.specificity.fraction * self.specificity_ratio):
                raise ValueError("anchored mutant differs from the paired raw log contrast")

    @property
    def turnover_ratio(self):
        return self.mutant.kcat_c_s_inv.fraction / self.wild_type.kcat_c_s_inv.fraction

    @property
    def specificity_ratio(self):
        return self.mutant.specificity.fraction / self.wild_type.specificity.fraction

    @property
    def coordinates(self):
        values = (self.wild_type, self.mutant)
        if self.anchor_wild_type is not None:
            values += (self.anchor_wild_type, self.anchored_mutant)
        return tuple(q.fraction for value in values for q in (value.kcat_c_s_inv, value.specificity))


def anchor_joint_value(value, observed_wt, *, value_id=None):
    """Apply one joint realization; uncertain anchors remain joint input rows."""
    exact(value, PairedJointValue)
    exact(observed_wt, EndpointValues)
    if value.anchor_wild_type is not None:
        raise ValueError("a joint value cannot receive its WT reference twice")
    return PairedJointValue(value.value_id if value_id is None else value_id,
        value.wild_type, value.mutant, observed_wt,
        EndpointValues.of(observed_wt.kcat_c_s_inv.fraction * value.turnover_ratio,
                          observed_wt.specificity.fraction * value.specificity_ratio))


@dataclass(frozen=True, slots=True)
class JointLogCovariance(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/joint-log-covariance"
    axes: tuple[str, ...]
    matrix: tuple[tuple[Decimal, ...], ...]
    sources: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        if self.axes not in (RAW_LOG_AXES, ANCHORED_LOG_AXES):
            raise ValueError("covariance changes its complete WT/mutant/reference log axes")
        n = len(self.axes)
        if (type(self.matrix) is not tuple or len(self.matrix) != n
                or any(type(row) is not tuple or len(row) != n for row in self.matrix)):
            raise ValueError("joint covariance must retain its complete square matrix")
        identities(self.sources)
        for row in self.matrix:
            for value in row:
                validate_decimal(value, field_name="log_covariance")
        if any(self.matrix[i][j] != self.matrix[j][i] for i in range(n) for j in range(n)):
            raise ValueError("joint log covariance must be symmetric")
        # Exact LDL/Schur test, including singular shared-reference directions.
        residual = [[F(value) for value in row] for row in self.matrix]
        for pivot in range(n):
            diagonal = residual[pivot][pivot]
            if diagonal < 0 or (diagonal == 0 and any(residual[pivot][j] for j in range(pivot + 1, n))):
                raise ValueError("joint log covariance must be positive semidefinite")
            if diagonal:
                for i in range(pivot + 1, n):
                    for j in range(pivot + 1, n):
                        residual[i][j] -= residual[i][pivot] * residual[pivot][j] / diagonal


def anchored_log_covariance(covariance):
    """Retain WT/reference correlation in y_M,anchored = y_W,obs + y_M - y_W."""
    exact(covariance, JointLogCovariance)
    if covariance.axes != ANCHORED_LOG_AXES:
        raise ValueError("anchoring covariance needs the actual joint reference axes")
    transform = ((0, 0, 0, 0, 1, 0), (0, 0, 0, 0, 0, 1),
                 (-1, 0, 1, 0, 1, 0), (0, -1, 0, 1, 0, 1))
    return tuple(tuple(Exact.of(sum(F(transform[i][a]) * F(covariance.matrix[a][b]) * transform[j][b]
                    for a in range(6) for b in range(6))) for j in range(4)) for i in range(4))


@dataclass(frozen=True, slots=True)
class JointEndpointRegion(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/joint-endpoint-region"
    region_id: str
    values: tuple[PairedJointValue, ...]
    geometry: str
    uncertainty_kind: str
    sources: tuple[ObjectIdentity, ...]
    covariance: JointLogCovariance | None = None
    declared_coverage: Decimal | None = None
    coverage_source: ObjectIdentity | None = None
    anchor_source: ObjectIdentity | None = None

    def __post_init__(self):
        validate_stable_id(self.region_id)
        if type(self.values) is not tuple or len(self.values) > 256:
            raise ValueError("joint region exceeds its declared finite member capacity")
        require_sorted_unique_strings(tuple(row.value_id for row in self.values), field_name="joint_value_ids")
        for value in self.values:
            exact(value, PairedJointValue)
        if self.geometry not in {"FINITE_POINTS", "CONVEX_HULL"}:
            raise ValueError("region must distinguish a finite support from its continuous hull")
        if self.geometry == "CONVEX_HULL" and len(self.values) > 16:
            raise ValueError("exact hull assessment supports at most sixteen declared vertices")
        if self.uncertainty_kind not in {"FINITE_JOINT_SUPPORT", "CONSERVATIVE_ERROR_SET",
                                        "DECLARED_PROBABILISTIC_JOINT_REGION"}:
            raise ValueError("joint uncertainty requires its actual interpretation")
        identities(self.sources)
        anchored = self.anchor_source is not None
        if anchored:
            exact(self.anchor_source, ObjectIdentity)
        if any((row.anchor_wild_type is not None) != anchored for row in self.values):
            raise ValueError("joint region drops or adds shared reference dependence")
        if anchored and self.anchor_source not in self.sources:
            raise ValueError("reference identity is absent from the joint region source closure")
        if self.covariance is not None:
            exact(self.covariance, JointLogCovariance)
            if not set(self.covariance.sources).issubset(self.sources):
                raise ValueError("covariance source closure is absent from the joint region")
            if self.covariance.axes != (ANCHORED_LOG_AXES if anchored else RAW_LOG_AXES):
                raise ValueError("region covariance omits or invents its shared reference axes")
        probabilistic = self.uncertainty_kind == "DECLARED_PROBABILISTIC_JOINT_REGION"
        if probabilistic:
            if self.declared_coverage is None or self.coverage_source is None:
                raise ValueError("declared probabilistic coverage requires its actual source")
            validate_decimal(self.declared_coverage, field_name="declared_coverage", minimum=Decimal(0))
            if not 0 < self.declared_coverage <= 1:
                raise ValueError("declared coverage must lie in (0, 1]")
            exact(self.coverage_source, ObjectIdentity)
            if self.coverage_source not in self.sources:
                raise ValueError("coverage identity is absent from the joint region source closure")
        elif self.declared_coverage is not None or self.coverage_source is not None:
            raise ValueError("unweighted support or error sets cannot acquire a probability level")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.region_id, self)


@dataclass(frozen=True, slots=True)
class ConservativeScenarioCompletion(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/conservative-scenario-completion"
    region: JointEndpointRegion
    requirement: ScientificRequirementSpec
    connection: ScientificConnectionSpec
    assessment: RequirementSupplyAssessment
    other_phase_assessments: tuple[RequirementSupplyAssessment, ...]
    case: ObjectIdentity
    context: ObjectIdentity

    def __post_init__(self):
        for record, kind in ((self.region, JointEndpointRegion), (self.requirement, ScientificRequirementSpec),
                             (self.connection, ScientificConnectionSpec), (self.assessment, RequirementSupplyAssessment)):
            exact(record, kind)
        if (not self.region.values or self.region.uncertainty_kind != "CONSERVATIVE_ERROR_SET"
                or self.connection.requirement_id != self.requirement.requirement_id
                or self.connection.assessment_operation_id != self.requirement.assessment_operation_id
                or self.connection.evidence_role not in self.requirement.permitted_roles
                or self.assessment.requirement != ObjectIdentity.from_record(self.requirement.requirement_id, self.requirement)
                or self.assessment.connection != ObjectIdentity.from_record(self.connection.connection_id, self.connection)
                or self.assessment.phase is not AssessmentPhase.ADMISSION
                or self.assessment.disposition is not AssessmentDisposition.SATISFIED
                or self.region.identity not in self.assessment.evidence):
            raise ValueError("scenario completion needs the exact independently assessed conservative region")
        for value, schema in ((self.case, "empirical-lawhood/rubisco-response/paired-case"),
                              (self.context, "empirical-lawhood/rubisco-response/assay-context")):
            exact(value, ObjectIdentity)
            if value.object_schema != schema or value.object_version != "1.0.0":
                raise ValueError("conservative completion changes its paired case or context")
        if (type(self.other_phase_assessments) is not tuple
                or tuple(row.phase for row in self.other_phase_assessments)
                != (AssessmentPhase.PROCEDURE, AssessmentPhase.INSTANCE, AssessmentPhase.JOINED)):
            raise ValueError("conservative completion requires all four connection assessment phases")
        for row in self.other_phase_assessments:
            exact(row, RequirementSupplyAssessment)
            if (row.requirement != self.assessment.requirement or row.connection != self.assessment.connection
                    or row.instance_id != self.assessment.instance_id
                    or row.disposition is not AssessmentDisposition.SATISFIED
                    or not set(self.assessment.evidence).issubset(row.evidence)):
                raise ValueError("conservative completion changes its phased evidence or original instance")


@dataclass(frozen=True, slots=True)
class PairedScenarioSupport(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/paired-scenario-support"
    scenario_id: str
    original_state: str
    region: JointEndpointRegion | None
    sources: tuple[ObjectIdentity, ...]
    unresolved_requirement_ids: tuple[str, ...]
    completion: ConservativeScenarioCompletion | None = None

    def __post_init__(self):
        validate_stable_id(self.scenario_id)
        identities(self.sources)
        require_sorted_unique_strings(self.unresolved_requirement_ids, field_name="unresolved_requirement_ids")
        for name in self.unresolved_requirement_ids:
            validate_stable_id(name)
        if self.original_state not in {"AVAILABLE", "UNKNOWN", "FAILED"}:
            raise ValueError("scenario outcome must preserve available, unknown or failed work")
        if self.region is not None:
            exact(self.region, JointEndpointRegion)
        if self.original_state == "AVAILABLE":
            if self.region is None or self.completion is not None:
                raise ValueError("available scenario needs its original region without a replacement")
        elif self.region is not None or not self.unresolved_requirement_ids:
            raise ValueError("unknown or failed scenario needs its missing requirement, not an admitted original region")
        if self.completion is not None:
            exact(self.completion, ConservativeScenarioCompletion)
            if (self.completion.assessment.instance_id != self.scenario_id
                    or self.completion.requirement.requirement_id not in self.unresolved_requirement_ids
                    or not set(self.sources).issubset(set(self.completion.assessment.evidence))):
                raise ValueError("completion changes the unresolved scenario or its original source ancestry")

    @property
    def effective_region(self):
        return self.region if self.region is not None else (
            None if self.completion is None else self.completion.region)


@dataclass(frozen=True, slots=True)
class PairedKineticSupport(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/paired-kinetic-support"
    support_id: str
    case: ObjectIdentity
    context: ObjectIdentity
    expected_scenario_ids: tuple[str, ...]
    scenarios: tuple[PairedScenarioSupport, ...]
    shared_sources: tuple[ObjectIdentity, ...]
    prerequisite_requirement_ids: tuple[str, ...]
    interpretation: str = "UNION_OF_ALTERNATIVES_NOT_INDEPENDENT_REQUIRED_CASES"
    biological_predictive_calibration: str = "NOT_ESTABLISHED"

    def __post_init__(self):
        validate_stable_id(self.support_id)
        exact(self.case, ObjectIdentity)
        exact(self.context, ObjectIdentity)
        if (self.case.object_schema != "empirical-lawhood/rubisco-response/paired-case"
                or self.case.object_version != "1.0.0"
                or self.context.object_schema != "empirical-lawhood/rubisco-response/assay-context"
                or self.context.object_version != "1.0.0"):
            raise ValueError("paired support substitutes the exact case or assay context")
        require_sorted_unique_strings(self.expected_scenario_ids, field_name="expected_scenario_ids", allow_empty=False)
        if (type(self.scenarios) is not tuple
                or tuple(row.scenario_id for row in self.scenarios) != self.expected_scenario_ids):
            raise ValueError("paired support drops or reorders a declared alternative")
        for row in self.scenarios:
            exact(row, PairedScenarioSupport)
            if row.completion is not None and (row.completion.case, row.completion.context) != (self.case, self.context):
                raise ValueError("conservative completion substitutes the selected paired case or context")
        identities(self.shared_sources, allow_empty=True)
        require_sorted_unique_strings(self.prerequisite_requirement_ids, field_name="prerequisite_requirement_ids")
        for name in self.prerequisite_requirement_ids:
            validate_stable_id(name)
        if (self.interpretation != "UNION_OF_ALTERNATIVES_NOT_INDEPENDENT_REQUIRED_CASES"
                or self.biological_predictive_calibration != "NOT_ESTABLISHED"):
            raise ValueError("paired support cannot change its quantifier or confer biological calibration")


@dataclass(frozen=True, slots=True)
class PairedDecisionRegion(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/paired-decision-region"
    decision_id: str
    case: ObjectIdentity
    context: ObjectIdentity
    minimum_turnover_ratio: Decimal
    minimum_specificity_ratio: Decimal
    absolute_turnover_floor_s_inv: Decimal | None
    absolute_specificity_floor: Decimal | None
    endpoint_view: str
    next_action: str
    sources: tuple[ObjectIdentity, ...]
    purpose: str = "CONDITIONAL_CANDIDATE_PRIORITIZATION"
    strict_turnover_increase: bool = False
    specificity_claim: str = "PRESERVATION"

    def __post_init__(self):
        validate_stable_id(self.decision_id)
        for value, schema in ((self.case, "empirical-lawhood/rubisco-response/paired-case"),
                              (self.context, "empirical-lawhood/rubisco-response/assay-context")):
            exact(value, ObjectIdentity)
            if value.object_schema != schema or value.object_version != "1.0.0":
                raise ValueError("decision must bind its exact material and assay context")
        if self.minimum_turnover_ratio < 1:
            raise ValueError("a turnover benefit cannot permit slower turnover")
        for name in ("minimum_turnover_ratio", "minimum_specificity_ratio"):
            value = getattr(self, name)
            validate_decimal(value, field_name=name, minimum=Decimal(0))
            if value == 0:
                raise ValueError("paired decision ratios must be positive")
        for name in ("absolute_turnover_floor_s_inv", "absolute_specificity_floor"):
            value = getattr(self, name)
            if value is not None:
                validate_decimal(value, field_name=name, minimum=Decimal(0))
                if value == 0:
                    raise ValueError("selected absolute kinetic floors must be positive")
        if type(self.strict_turnover_increase) is not bool:
            raise TypeError("strict turnover comparison needs an explicit boolean")
        if self.endpoint_view not in {"RAW", "ANCHORED"}:
            raise ValueError("decision must explicitly select raw or anchored absolute endpoints")
        if (self.specificity_claim not in {"PRESERVATION", "EXPLORATORY_LOSS_ALLOWED"}
                or self.specificity_claim == "PRESERVATION" and self.minimum_specificity_ratio < 1):
            raise ValueError("a permitted specificity loss cannot be reported as preservation")
        for name in ("next_action", "purpose"):
            validate_nonempty(getattr(self, name), field_name=name)
        identities(self.sources)
