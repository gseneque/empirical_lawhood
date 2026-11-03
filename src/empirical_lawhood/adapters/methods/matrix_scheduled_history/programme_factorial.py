# SPDX-License-Identifier: MPL-2.0
"""Original E4 whole-group factorial analysis, conditional on declared science.

The public operation is exposed development FALSIFY only. It creates neither
confirmation access nor qualification. The pure arithmetic also accepts a
complete original confirmation roster, but its caller must separately establish
frozen criteria, genuine qualified parents and outcome authority. No public
confirmation factory is supplied here. All original scientific bytes survive.

The selected endpoint is explicitly the worst cumulative log1p response error
over both numerical views and all fifteen predictor/horizon outputs. Seven E4
contrasts are tested conditionally; five other slots of the complete twelve-
comparison family remain unevaluable. No comparison probability is a caller
operand. Three-way interaction and preparation-family heterogeneity are retained
descriptively. Common-normal independent whole-group differences are a named
scientific requirement, never an inference from labels or a development example.
"""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from itertools import product
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import (
    ConditionRole, ContributionRole, ScientificRequirementSpec,
)
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft
from empirical_lawhood.runtime.experimental_factorial import (
    FactorialCoordinate, FactorialGrid, FactorialObservation, PairInteractionScale,
    factorial_group_contrasts, holm_adjustment,
)
from empirical_lawhood.runtime.experimental_statistics import (
    PairedMeanTAlternative, paired_mean_t,
)

from .programme_records import MODES, NAMESPACE, ScheduledProgramme
from .programme_reduction import ScheduledProgrammeReduction
from .programme_selection import (
    ScheduledRevisionDataBank, ScheduledRevisionTarget, validate_programme_paired_data,
)
from .records import matched_key

OPERATION = NAMESPACE+".factorial-assess"
ENDPOINT = "MAX_PAIRED_CUMULATIVE_LOG1P_RESPONSE_ERROR_ALL15"
PROCEDURE = "PAIRED_GROUP_MEAN_T"
SAMPLING_REQUIREMENT = "IID_COMMON_NORMAL_WHOLE_GROUP_DIFFERENCES"
E4_COMPARISONS = (
    "e4.main.temperature", "e4.main.friction", "e4.main.coupling",
    "e4.pair.temperature-friction", "e4.pair.temperature-coupling", "e4.pair.friction-coupling",
    "e4.aggregate-curvature",
)
FAMILY_IDS = tuple(sorted(("e3.model", *E4_COMPARISONS, "e4.revision-baseline", "e5.preparation",
    "e6.nearby", "e6.shifted")))
MISSING_COMPARISON = "MISSING_AUTHENTICATED_CROSS_PHASE_COMPARISON"
ASSUMPTION_STATUS = "NOT_AUTHENTICATED_BY_THIS_CALCULATION"


def mean_t_requirement(requirement_id):
    """Code-owned necessary assumption, with no evidence/admission verdict."""
    return ScientificRequirementSpec(requirement_id, OPERATION, ConditionRole.EVIDENTIAL,
        "Interpret the conditional Student mean-tail calculations for the declared whole-group contrasts.",
        SAMPLING_REQUIREMENT, None, None,
        "Dependence between groups, unequal group means/variances, nonnormal differences, or endpoint/margin selection after outcomes invalidates this procedure.",
        (ContributionRole.RETAINED_ANALYSIS_INPUT,))


@dataclass(frozen=True, slots=True)
class ExactRatio(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/exact-ratio"
    numerator: int
    denominator: int

    def __post_init__(self):
        if (type(self.numerator) is not int or type(self.denominator) is not int or self.denominator < 1
                or Fraction(self.numerator, self.denominator).denominator != self.denominator):
            raise ValueError("factorial exact ratios require reduced integer numerator/positive denominator")

    @property
    def fraction(self):
        return Fraction(self.numerator, self.denominator)


def _ratio(value):
    if value is None:
        return None
    exact = Fraction(value)
    return ExactRatio(exact.numerator, exact.denominator)


@dataclass(frozen=True, slots=True)
class ScheduledFactorialComparison(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/factorial-comparison"
    comparison_id: str
    alternative: PairedMeanTAlternative
    null_value: Decimal
    practical_threshold: Decimal | None

    def __post_init__(self):
        if (self.comparison_id not in E4_COMPARISONS or type(self.alternative) is not PairedMeanTAlternative
                or type(self.null_value) is not Decimal or not self.null_value.is_finite()
                or self.practical_threshold is not None and (type(self.practical_threshold) is not Decimal
                    or not self.practical_threshold.is_finite() or self.practical_threshold < 0)):
            raise ValueError("E4 factorial comparison requires its explicit direction, null/margin and descriptive practical threshold")


@dataclass(frozen=True, slots=True)
class ScheduledFactorialSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/factorial-specification"
    specification_id: str
    programme: ObjectIdentity
    target: ScheduledRevisionTarget
    endpoint: str
    pair_scale: PairInteractionScale
    comparisons: tuple[ScheduledFactorialComparison, ...]
    alpha: Decimal
    procedure: str
    sampling_requirement: ScientificRequirementSpec
    assumption_references: tuple[ObjectIdentity, ...]
    missing_policy: str

    def __post_init__(self):
        self._validate_operands(programme_schema=ScheduledProgramme.SCHEMA)

    def _validate_operands(self, *, programme_schema):
        validate_stable_id(self.specification_id)
        if (type(self.programme) is not ObjectIdentity or self.programme.object_schema != programme_schema
                or type(self.target) is not ScheduledRevisionTarget or self.endpoint != ENDPOINT
                or type(self.pair_scale) is not PairInteractionScale or self.procedure != PROCEDURE
                or self.missing_policy != "REQUIRE_COMPLETE_ASSIGNED_WHOLE_GROUPS"
                or type(self.alpha) is not Decimal or not self.alpha.is_finite() or not 0 < self.alpha < 1
                or type(self.comparisons) is not tuple or any(type(row) is not ScheduledFactorialComparison for row in self.comparisons)
                or tuple(row.comparison_id for row in self.comparisons) != E4_COMPARISONS
                or type(self.sampling_requirement) is not ScientificRequirementSpec
                or self.sampling_requirement != mean_t_requirement(self.sampling_requirement.requirement_id)
                or type(self.assumption_references) is not tuple
                or any(type(row) is not ObjectIdentity for row in self.assumption_references)
                or tuple(row.object_id for row in self.assumption_references)
                    != tuple(sorted({row.object_id for row in self.assumption_references}))):
            raise ValueError("E4 factorial specification changes its complete explicit conditional procedure or required scientific assumption")
        self.target.__post_init__()
        self.sampling_requirement.__post_init__()
        for row in self.comparisons:
            row.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


@dataclass(frozen=True, slots=True)
class ScheduledFactorialGroup(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/factorial-group"
    group_id: str
    family_id: str
    root_endpoints: tuple[tuple[str, Decimal | None], ...]
    disposition: str
    missing_root_ids: tuple[str, ...]
    nonfinite_root_ids: tuple[str, ...]
    contrasts: tuple[ExactRatio | None, ...]
    three_way_descriptive: ExactRatio | None

    def __post_init__(self):
        validate_stable_id(self.group_id)
        validate_stable_id(self.family_id)
        if (len(self.root_endpoints) != 9 or len(self.contrasts) != 7
                or tuple(name for name, _ in self.root_endpoints) != tuple(sorted({name for name, _ in self.root_endpoints}))
                or self.disposition not in ("FINITE", "UNEVALUABLE")
                or any(value is not None and type(value) is not Decimal for _, value in self.root_endpoints)
                or self.missing_root_ids != tuple(name for name, value in self.root_endpoints if value is None)
                or self.nonfinite_root_ids != tuple(name for name, value in self.root_endpoints if value is not None and not value.is_finite())
                or (self.disposition == "FINITE") != (not self.missing_root_ids and not self.nonfinite_root_ids)
                or any(value is not None and type(value) is not ExactRatio for value in (*self.contrasts, self.three_way_descriptive))
                or any((value is not None) != (self.disposition == "FINITE") for value in (*self.contrasts, self.three_way_descriptive))):
            raise ValueError("factorial group drops a nested coordinate or invents finite whole-group contrasts")


@dataclass(frozen=True, slots=True)
class ScheduledFactorialFamilyDescription(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/factorial-family-description"
    family_id: str
    group_ids: tuple[str, ...]
    complete_groups: int
    means: tuple[ExactRatio | None, ...]
    sample_variances: tuple[ExactRatio | None, ...]
    scope: str

    def __post_init__(self):
        self._validate_operands(allow_insufficient_family=False)

    def _validate_operands(self, *, allow_insufficient_family):
        validate_stable_id(self.family_id)
        if (type(self.group_ids) is not tuple or not self.group_ids
                or self.group_ids != tuple(sorted(set(self.group_ids))) or type(self.complete_groups) is not int
                or not 0 <= self.complete_groups <= len(self.group_ids) or len(self.means) != 7 or len(self.sample_variances) != 7
                or any(value is not None and type(value) is not ExactRatio for value in (*self.means, *self.sample_variances))
                or any((value is not None) != (self.complete_groups == len(self.group_ids)) for value in self.means)
                or any((value is not None) != (self.complete_groups == len(self.group_ids)
                    and (not allow_insufficient_family or len(self.group_ids) > 1)) for value in self.sample_variances)
                or self.scope != "DESCRIPTIVE_ONLY_NO_STRATUM_TESTS"):
            raise ValueError("factorial family description changes complete-group accounting or invents stratum inference")


@dataclass(frozen=True, slots=True)
class ScheduledFactorialTestResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/factorial-test-result"
    comparison: ScheduledFactorialComparison
    assigned_groups: int
    finite_groups: int
    missing_group_ids: tuple[str, ...]
    nonfinite_group_ids: tuple[str, ...]
    mean: ExactRatio | None
    sample_variance: ExactRatio | None
    degrees_of_freedom: int
    statistic: Decimal | None
    p_value: Decimal | None
    adjusted_p_value: ExactRatio | None
    conditional_disposition: str
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        if (type(self.comparison) is not ScheduledFactorialComparison or type(self.assigned_groups) is not int
                or type(self.finite_groups) is not int or not 0 <= self.finite_groups <= self.assigned_groups
                or self.degrees_of_freedom != self.assigned_groups-1
                or self.finite_groups+len(self.missing_group_ids)+len(self.nonfinite_group_ids) != self.assigned_groups
                or len(set((*self.missing_group_ids, *self.nonfinite_group_ids))) != self.assigned_groups-self.finite_groups
                or self.conditional_disposition not in ("REJECTED", "NOT_REJECTED", "UNEVALUABLE")
                or any(value is not None and type(value) is not ExactRatio for value in (self.mean, self.sample_variance, self.adjusted_p_value))
                or any(value is not None and (type(value) is not Decimal or not value.is_finite()) for value in (self.statistic, self.p_value))
                or self.p_value is not None and not 0 < self.p_value <= 1
                or (self.conditional_disposition == "UNEVALUABLE") != (self.p_value is None)
                or (self.p_value is None) != (self.adjusted_p_value is None) or (self.p_value is None) != (self.statistic is None)
                or (self.p_value is None) != bool(self.reason_codes)
                or self.finite_groups != self.assigned_groups and (self.mean is not None or self.sample_variance is not None)):
            raise ValueError("factorial test drops assigned groups or invents finite conditional inference")


@dataclass(frozen=True, slots=True)
class ScheduledFactorialFamilySlot(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/factorial-family-slot"
    comparison_id: str
    p_value: Decimal | None
    adjusted_p_value: ExactRatio | None
    conditional_disposition: str
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.comparison_id)
        if (self.conditional_disposition not in ("REJECTED", "NOT_REJECTED", "UNEVALUABLE")
                or self.p_value is not None and (type(self.p_value) is not Decimal or not self.p_value.is_finite() or not 0 < self.p_value <= 1)
                or self.adjusted_p_value is not None and type(self.adjusted_p_value) is not ExactRatio
                or (self.p_value is None) != (self.adjusted_p_value is None)
                or (self.p_value is None) != (self.conditional_disposition == "UNEVALUABLE")
                or (self.p_value is None) != bool(self.reason_codes)):
            raise ValueError("factorial family slot invents an available comparison or hides its unevaluable reason")


@dataclass(frozen=True, slots=True)
class ScheduledFactorialAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/factorial-assessment"
    assessment_id: str
    specification: ScheduledFactorialSpecification
    programme: ObjectIdentity
    reduction: ObjectIdentity
    data: ObjectIdentity
    mode: str
    groups: tuple[ScheduledFactorialGroup, ...]
    family_descriptions: tuple[ScheduledFactorialFamilyDescription, ...]
    tests: tuple[ScheduledFactorialTestResult, ...]
    family_slots: tuple[ScheduledFactorialFamilySlot, ...]
    sampling_assumption_status: str
    three_way_scope: str
    authority: str
    standing: str

    def __post_init__(self):
        self._validate_operands(specification_type=ScheduledFactorialSpecification,
            reduction_schema=ScheduledProgrammeReduction.SCHEMA, data_schema=ScheduledRevisionDataBank.SCHEMA,
            group_count=MODES.get(self.mode, (None, None))[1], allow_insufficient_family=False)

    def _validate_operands(self, *, specification_type, reduction_schema, data_schema, group_count, allow_insufficient_family):
        validate_stable_id(self.assessment_id)
        family_ids = declared_family(self.specification)
        accepted_types = specification_type if type(specification_type) is tuple else (specification_type,)
        if (type(self.specification) not in accepted_types
                or self.mode not in ("E4_DEVELOPMENT", "E4_CONFIRMATION")
                or self.programme != self.specification.programme
                or self.reduction.object_schema != reduction_schema
                or self.data.object_schema != data_schema
                or len(self.groups) != group_count
                or tuple(row.group_id for row in self.groups) != tuple(sorted({row.group_id for row in self.groups}))
                or tuple(row.comparison for row in self.tests) != self.specification.comparisons
                or any(row.assigned_groups != len(self.groups) or row.degrees_of_freedom != len(self.groups)-1 for row in self.tests)
                or tuple(row.comparison_id for row in self.family_slots) != family_ids
                or any(row.p_value is not None or row.reason_codes != (MISSING_COMPARISON,)
                    for row in self.family_slots if row.comparison_id not in E4_COMPARISONS)
                or self.sampling_assumption_status != ASSUMPTION_STATUS or self.three_way_scope != "DESCRIPTIVE_ONLY"
                or self.authority != "NONE" or self.standing != ("EXPLORATORY_EXPOSED_DEVELOPMENT" if self.mode == "E4_DEVELOPMENT"
                    else "CONDITIONAL_CONFIRMATION_NUMBERS_NO_AUTHORITY")):
            raise ValueError("factorial assessment changes its full original group/family census or invents scientific authority")
        self.specification.__post_init__()
        for row in self.groups:
            row.__post_init__()
        descriptions = {row.family_id: row for row in self.family_descriptions}
        if (tuple(descriptions) != tuple(sorted({row.family_id for row in self.groups}))
                or len(descriptions) != len(self.family_descriptions)
                or any(row.group_ids != tuple(group.group_id for group in self.groups if group.family_id == row.family_id)
                    or row.complete_groups != sum(group.disposition == "FINITE" for group in self.groups if group.family_id == row.family_id)
                    for row in self.family_descriptions)):
            raise ValueError("factorial assessment loses preparation-family heterogeneity or complete group counts")
        for row in (*self.family_descriptions, *self.tests, *self.family_slots):
            row.__post_init__()
        for index, test in enumerate(self.tests):
            absent = tuple(row.group_id for row in self.groups if row.contrasts[index] is None)
            if (test.missing_group_ids != absent or test.nonfinite_group_ids or test.finite_groups != len(self.groups)-len(absent)):
                raise ValueError("factorial test substitutes original complete-group contrast availability")
            if not absent:
                values = tuple(row.contrasts[index].fraction for row in self.groups)
                mean = sum(values, Fraction(0))/len(values)
                variance = sum(((value-mean)**2 for value in values), Fraction(0))/(len(values)-1)
                if (test.mean, test.sample_variance) != (_ratio(mean), _ratio(variance)):
                    raise ValueError("factorial test substitutes its exact full-denominator moments")
        for description in self.family_descriptions:
            selected = tuple(row for row in self.groups if row.family_id == description.family_id)
            if description.complete_groups == len(selected):
                for index in range(7):
                    values = tuple(row.contrasts[index].fraction for row in selected)
                    mean = sum(values, Fraction(0))/len(values)
                    variance = (None if allow_insufficient_family and len(values) < 2 else
                        sum(((value-mean)**2 for value in values), Fraction(0))/(len(values)-1))
                    if (description.means[index], description.sample_variances[index]) != (_ratio(mean), _ratio(variance)):
                        raise ValueError("factorial description substitutes original preparation-family moments")
        by_test = {row.comparison.comparison_id: row for row in self.tests}
        expected = holm_adjustment(family_ids, tuple((name, by_test[name].p_value if name in by_test else None)
            for name in family_ids), alpha=self.specification.alpha)
        for row, adjusted in zip(self.family_slots, expected.comparisons, strict=True):
            if (row.adjusted_p_value != _ratio(adjusted.adjusted_p_value) or row.conditional_disposition != adjusted.disposition.value
                    or row.comparison_id in by_test and (row.p_value, row.adjusted_p_value, row.conditional_disposition, row.reason_codes)
                        != (by_test[row.comparison_id].p_value, by_test[row.comparison_id].adjusted_p_value,
                            by_test[row.comparison_id].conditional_disposition, by_test[row.comparison_id].reason_codes)):
                raise ValueError("factorial assessment changes its exact conservative full-family adjustment")


def _coded(factors, values):
    return tuple(-1 if value == axis.low else 1 if value == axis.high else 0
        for value, axis in zip(values, factors, strict=True))


def _coordinate(levels):
    return FactorialCoordinate("setting."+".".join({-1: "low", 0: "center", 1: "high"}[value] for value in levels), levels)


def validate_factorial_inputs(specification, programme, reduction, data):
    """Pure shared admission for this consumer's original paired/matched records."""
    if type(specification) is not ScheduledFactorialSpecification:
        raise TypeError("factorial assessment requires its explicit typed scientific specification")
    specification.__post_init__()
    if type(programme) is not ScheduledProgramme or specification.programme != programme.identity:
        raise ValueError("factorial assessment substitutes its original programme")
    targets, _ = validate_programme_paired_data(programme, reduction, data, specification.target, mode=programme.mode,
        missing_record_policy="ALLOW_ABSENT_DECLARED_ROWS")
    by_root = {row.root_id: row for row in data.cases}
    for group in programme.group_ids:
        rows = tuple(case for case in programme.cases if case.independent_group_id == group)
        if (len({(matched_key(by_root[case.root_id].coordinate), by_root[case.root_id].coordinate.clock_id)
                for case in rows if case.root_id in by_root}) > 1
                or len({case.streams_sha256 for case in rows}) != 1):
            raise ValueError("factorial matched group changes fixed preparation, source clock, start/noise contract or remaining physics")
    return targets


def assess_programme_factorial(specification, programme, reduction, data, *, assessment_id):
    """Compute only conditional numbers; no fit, acquisition, source or authority acts."""
    targets = validate_factorial_inputs(specification, programme, reduction, data)
    return factorial_from_targets(specification, programme, reduction, data, targets, assessment_id=assessment_id,
        assessment_type=ScheduledFactorialAssessment, description_type=ScheduledFactorialFamilyDescription)


def factorial_groups_from_targets(specification, programme, reduction, data, targets):
    """Whole-group physical contrasts, before any selected inferential procedure."""
    grid = FactorialGrid(tuple(axis.factor_id for axis in programme.factors),
        tuple(_coordinate(levels) for levels in (*product((-1, 1), repeat=3), (0, 0, 0))))
    by_root = {row.root_id: row for row in data.cases}
    endpoints = {}
    for case, result in zip(programme.cases, reduction.cases, strict=True):
        row = by_root.get(case.root_id)
        prefix = None if row is None else row.causal_prefix
        values = targets[case.root_id]
        endpoints[case.root_id] = (None if prefix is None or prefix.disposition != "AVAILABLE"
            or result.disposition != "COMPLETED" or result.numerical_disposition != "SATISFIED"
            or any(value is None for value in values) else max(values))
    observations = tuple(FactorialObservation(case.independent_group_id, _coordinate(_coded(programme.factors, case.factor_values)),
        endpoints[case.root_id]) for case in programme.cases)
    contrasts = factorial_group_contrasts(grid, programme.group_ids, observations, pair_scale=specification.pair_scale)
    groups = []
    for result in contrasts.groups:
        original = tuple(case for case in programme.cases if case.independent_group_id == result.group_id)
        values = tuple((case.root_id, endpoints[case.root_id]) for case in original)
        groups.append(ScheduledFactorialGroup(result.group_id, original[0].family_id, values, result.disposition.value,
            tuple(name for name, value in values if value is None),
            tuple(name for name, value in values if value is not None and not value.is_finite()),
            tuple(_ratio(value) for value in (*result.main_effects, *result.pair_interactions, result.curvature)), _ratio(result.three_way)))
    return tuple(groups)


def factorial_from_targets(specification, programme, reduction, data, targets, *, assessment_id, assessment_type, description_type):
    """Original factorial equation after exact source/paired-target validation."""
    groups = factorial_groups_from_targets(specification, programme, reduction, data, targets)
    conditional = tuple(paired_mean_t(programme.group_ids,
        tuple(None if row.contrasts[index] is None else row.contrasts[index].fraction for row in groups),
        null_value=comparison.null_value, alternative=comparison.alternative)
        for index, comparison in enumerate(specification.comparisons))
    probabilities = dict(zip(E4_COMPARISONS, (row.p_value for row in conditional), strict=True))
    family_ids = declared_family(specification)
    adjusted = holm_adjustment(family_ids, tuple((name, probabilities.get(name)) for name in family_ids), alpha=specification.alpha)
    by_comparison = {row.comparison_id: row for row in adjusted.comparisons}
    tests = tuple(ScheduledFactorialTestResult(comparison, result.assigned_count, result.finite_count,
        result.missing_group_ids, result.nonfinite_group_ids, _ratio(result.mean), _ratio(result.sample_variance),
        result.degrees_of_freedom, result.statistic, result.p_value, _ratio(by_comparison[comparison.comparison_id].adjusted_p_value),
        by_comparison[comparison.comparison_id].disposition.value, result.reason_codes)
        for comparison, result in zip(specification.comparisons, conditional, strict=True))
    slots = tuple(ScheduledFactorialFamilySlot(name, probabilities.get(name), _ratio(by_comparison[name].adjusted_p_value),
        by_comparison[name].disposition.value, next(row.reason_codes for row in tests if row.comparison.comparison_id == name)
            if name in E4_COMPARISONS else (MISSING_COMPARISON,)) for name in family_ids)
    descriptions = describe_factorial_groups(groups, description_type=description_type)
    return assessment_type(assessment_id, specification, programme.identity,
        ObjectIdentity.from_record(getattr(reduction, "reduction_id", getattr(reduction, "record_id", None)), reduction), data.identity, programme.mode, groups,
        descriptions, tests, slots, ASSUMPTION_STATUS, "DESCRIPTIVE_ONLY", "NONE",
        "EXPLORATORY_EXPOSED_DEVELOPMENT" if programme.mode == "E4_DEVELOPMENT" else "CONDITIONAL_CONFIRMATION_NUMBERS_NO_AUTHORITY")


def describe_factorial_groups(groups, *, description_type):
    """Exact family moments, retaining incomplete and singleton family scopes."""
    descriptions = []
    for family in sorted({row.family_id for row in groups}):
        rows = tuple(row for row in groups if row.family_id == family)
        complete = sum(row.disposition == "FINITE" for row in rows)
        means, variances = [], []
        for index in range(7):
            if complete != len(rows):
                means.append(None); variances.append(None)
            else:
                values = tuple(row.contrasts[index].fraction for row in rows)
                mean = sum(values, Fraction(0))/len(values)
                means.append(_ratio(mean))
                variances.append(None if len(values) < 2 else
                    _ratio(sum(((value-mean)**2 for value in values), Fraction(0))/(len(values)-1)))
        descriptions.append(description_type(family, tuple(row.group_id for row in rows), complete,
            tuple(means), tuple(variances), "DESCRIPTIVE_ONLY_NO_STRATUM_TESTS"))
    return tuple(descriptions)


def factorial_node_id(specification):
    return OPERATION+"."+specification.fingerprint()[:24]


@dataclass(frozen=True, slots=True)
class ScheduledFactorialOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/factorial-operation-config"
    config_id: str
    programme: ScheduledProgramme
    specification: ScheduledFactorialSpecification
    reduction: ObjectIdentity
    data: ObjectIdentity

    def __post_init__(self):
        if (type(self.programme) is not ScheduledProgramme or self.programme.mode != "E4_DEVELOPMENT"
                or type(self.specification) is not ScheduledFactorialSpecification
                or self.specification.programme != self.programme.identity
                or self.specification.target.criterion != self.programme.criterion
                or self.config_id != "config."+factorial_node_id(self.specification)
                or type(self.reduction) is not ObjectIdentity or self.reduction.object_schema != ScheduledProgrammeReduction.SCHEMA
                or type(self.data) is not ObjectIdentity or self.data.object_schema != ScheduledRevisionDataBank.SCHEMA):
            raise ValueError("public factorial analysis requires exact original exposed development inputs; no confirmation access bypass")
        self.programme.__post_init__()
        self.specification.__post_init__()


def factorial_external_id(specification, name):
    if name not in ("programme", "specification", "reduction", "data"):
        raise ValueError("unknown original factorial operand")
    return "external."+specification.fingerprint()+"."+name


def factorial_development_root(config, *, study_id):
    from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
    from empirical_lawhood.kernel.worlds import WorldKind
    question = "What exploratory whole-group E4 factorial contrasts and conditional declared-family tests do the complete original paired outcomes support?"
    world = "world.matrix-scheduled-programme.development-factorial"
    claim = ClaimSpec("claim."+study_id, world, config.programme.programme_id, question,
        "Original32 whole groups, all nine settings and both numerical views; seven conditional tests retain all twelve family slots.",
        "unit.matrix-scheduled-programme.whole-group", None, EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        "Conditional development arithmetic authenticates no sampling assumption, source eligibility, qualification or outcome authority.",
        ("assumption.e4.common-normal-independent-whole-groups",), numerical_view_ids=("fine", "primary"))
    operands = tuple(sorted((config.programme.identity, config.specification.identity, config.reduction, config.data), key=lambda row: row.object_id))
    return DevelopmentStudySpec(study_id, question, config.programme.identity, world, WorldKind.NUMERICAL_SIMULATOR,
        config.programme.group_ids, ("fine", "primary"), (claim,), operands)


@dataclass(frozen=True, slots=True)
class ScheduledFactorialLoweredStudy:
    draft: RecursiveStudyDraft
    input_records: tuple[tuple[str, CanonicalRecord], ...]


def lower_exposed_programme_factorial(specification, programme, reduction, data, *, campaign):
    """Compose one original exposed method through existing recursive authoring."""
    from dataclasses import replace
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.planning.campaigns import CampaignSpec
    from empirical_lawhood.planning.recursive_authoring import (
        RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec,
    )
    if type(campaign) is not CampaignSpec:
        raise TypeError("factorial lowering needs its existing typed campaign")
    node = factorial_node_id(specification)
    config = ScheduledFactorialOperationConfig("config."+node, programme, specification,
        ObjectIdentity.from_record(reduction.reduction_id, reduction), data.identity)
    validate_factorial_inputs(specification, programme, reduction, data)
    declaration = operation_declarations()[0]
    operation = RecursiveOperationSpec.from_config(node_id=node, selection=declaration.registration().selection,
        config_id=config.config_id, config=config, obligation_ids=("obligation."+node+".complete-factorial",), resource_budget=declaration.resources)
    records = tuple(sorted((factorial_external_id(specification, name), record) for name, record in (
        ("programme", programme), ("specification", specification), ("reduction", reduction), ("data", data))))
    external = tuple(RecursiveExternalInput(input_id, "input."+input_id, record.SCHEMA, "application/json",
        len(record.canonical_bytes()), OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, record.fingerprint())
        for input_id, record in records)
    links = tuple(sorted((RecursiveInputLink("edge."+node+"."+name, node, name, None, None,
        factorial_external_id(specification, name), "SOURCE") for name in ("programme", "specification", "reduction", "data")), key=lambda row: row.edge_id))
    root = factorial_development_root(config, study_id="study.e4.exposed-factorial."+specification.fingerprint())
    selected = replace(campaign, objective=root.question, system_ids=(root.system.object_id,), world_ids=(root.world_id,),
        target_claim_ids=tuple(row.claim_id for row in root.claims))
    draft = RecursiveStudyDraft("draft.e4.exposed-factorial."+specification.fingerprint(), root.question, selected,
        (), (), (), (operation,), external, links, (node,), development_study=root)
    return ScheduledFactorialLoweredStudy(draft, records)


def scientific_root_validator(config, context):
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
    from empirical_lawhood.runtime.plans import ScientificStage
    config.__post_init__()
    if (context.node_id != factorial_node_id(config.specification) or context.stage is not ScientificStage.FALSIFY
            or context.unit_ids != config.programme.group_ids or context.selected_unit_ids != config.programme.group_ids
            or context.complete_unit_census or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or type(context.root) is not DevelopmentStudySpec
            or context.root != factorial_development_root(config, study_id=context.root.study_id)):
        raise ValueError("factorial public operation changes its exact exposed development root, whole groups, FALSIFY stage or access")
    configs = tuple(row.record for row in context.config_inputs if type(row.record) is ScheduledFactorialOperationConfig)
    if configs != (config,):
        raise ValueError("factorial analysis requires its single exact declared development method")
    incoming = tuple(row for row in context.links if row.consumer_node_id == context.node_id)
    expected = {name: (None, None, factorial_external_id(config.specification, name), "SOURCE")
        for name in ("programme", "specification", "reduction", "data")}
    actual = {row.consumer_input_id: (row.producer_node_id, row.producer_output_id, row.external_input_id, row.scientific_role) for row in incoming}
    if len(incoming) != 4 or actual != expected:
        raise ValueError("factorial analysis substitutes its original source links or causal input roles")


class ScheduledFactorialWorker:
    def __init__(self, manifest=None):
        self.manifest = manifest or operation_declarations()[0].manifest()

    def _inputs(self, context):
        from empirical_lawhood.kernel.decoding import decode_canonical_bytes
        from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
        from empirical_lawhood.runtime.artifacts import ArtifactProfile
        from empirical_lawhood.runtime.execution import WorkerInputKind
        kinds = (ScheduledFactorialOperationConfig, ScheduledProgramme, ScheduledFactorialSpecification,
            ScheduledProgrammeReduction, ScheduledRevisionDataBank)
        by_schema = {kind.SCHEMA: kind for kind in kinds}
        if (context.permissions != self.manifest.permissions or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or len(context.input_ports) != len(kinds) or not self.manifest.resource_ceiling.contains(context.resource_budget)):
            raise ValueError("factorial analysis changes its original complete inputs, resources or exposed development access")
        records = {}
        for port in context.input_ports:
            kind = by_schema.get(port.payload_schema)
            if (kind is None or kind in records or port.media_type != "application/json"
                    or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
                raise ValueError("factorial analysis receives duplicate, protected or undeclared original input records")
            cursor = port.cursor()
            try:
                raw = cursor.read()
            finally:
                cursor.close()
            if len(raw) != port.size_bytes:
                raise ValueError("factorial analysis changes its complete original record bytes")
            records[kind] = decode_canonical_bytes(raw, kind, maximum_bytes=None)
            if kind is ScheduledFactorialOperationConfig and (port.kind is not WorkerInputKind.EXTERNAL or port.artifact_id != context.config.artifact_id):
                raise ValueError("factorial analysis changes its original external configuration")
        config = records[ScheduledFactorialOperationConfig]
        if (context.task_id != factorial_node_id(config.specification) or context.config.config_id != config.config_id
                or context.config.config_schema != config.SCHEMA or context.config.content_sha256 != config.fingerprint()
                or records[ScheduledProgramme] != config.programme or records[ScheduledFactorialSpecification] != config.specification
                or ObjectIdentity.from_record(records[ScheduledProgrammeReduction].reduction_id, records[ScheduledProgrammeReduction]) != config.reduction
                or records[ScheduledRevisionDataBank].identity != config.data):
            raise ValueError("factorial analysis substitutes its original config, programme, method or evidence bindings")
        output = factorial_node_id(config.specification)+".product"
        if (len(context.output_ports) != 1 or context.output_ports[0].output_id != output
                or context.output_ports[0].payload_schema != ScheduledFactorialAssessment.SCHEMA
                or context.output_ports[0].profile is not ArtifactProfile.CANONICAL_JSON
                or context.output_ports[0].media_type != "application/json"):
            raise ValueError("factorial analysis changes its exact original output contract")
        validate_factorial_inputs(config.specification, config.programme, records[ScheduledProgrammeReduction], records[ScheduledRevisionDataBank])
        return config, records

    def preflight(self, context):
        self._inputs(context)

    def execute(self, context):
        from empirical_lawhood.runtime.artifacts import ReceiptCheck
        from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload
        config, records = self._inputs(context)
        product = assess_programme_factorial(config.specification, config.programme, records[ScheduledProgrammeReduction],
            records[ScheduledRevisionDataBank], assessment_id="assessment."+config.specification.specification_id)
        output = factorial_node_id(config.specification)+".product"
        return RunnerResult((TaskOutputPayload(output, product.canonical_bytes()),),
            (ReceiptCheck("complete-original-whole-group-conditional-factorial", True, ()),))


def operation_declarations():
    from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
    from empirical_lawhood.kernel.authority import ResourceBudget
    from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.runtime.artifacts import ArtifactProfile
    from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
    from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
    from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
    from empirical_lawhood.runtime.recursive_provider import RecursiveOperationDeclaration, RecursiveScientificHooks
    inputs = (("data", ScheduledRevisionDataBank), ("programme", ScheduledProgramme),
        ("reduction", ScheduledProgrammeReduction), ("specification", ScheduledFactorialSpecification))
    kinds = (ScheduledFactorialOperationConfig, ScheduledFactorialAssessment, *(kind for _, kind in inputs))
    return (RecursiveOperationDeclaration(capability_key=OPERATION, capability_version="1.0.0",
        implementation_id="original-paired-e4-whole-group-conditional-factorial-v1", kind=CapabilityKind.ANALYSIS,
        config_record_type=ScheduledFactorialOperationConfig, stage=ScientificStage.FALSIFY,
        input_ports=tuple(RecursivePortContract(name, kind.SCHEMA, "application/json", None) for name, kind in inputs),
        outputs=(OutputTemplate("product", ScheduledFactorialAssessment.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),),
        permissions=tuple(sorted((CapabilityPermission.READ_DEVELOPMENT, CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS))), evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
        resources=ResourceBudget(1, None, 0, None, None, None),
        conformance_check_ids=("complete-original-paired-whole-group-factorial", "conditional-common-normal-procedure",
            "full-twelve-comparison-family-no-reallocation"), runner_factory=ScheduledFactorialWorker,
        record_codecs={kind.SCHEMA: kind for kind in kinds}, input_record_types=tuple(sorted((kind for _, kind in inputs), key=lambda kind: (kind.SCHEMA, kind.VERSION))),
        scientific_hooks=RecursiveScientificHooks(scientific_unit_ids=lambda config: config.programme.group_ids,
            scientific_root_validator=scientific_root_validator), provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,)),)


def operation_factories():
    return tuple(row.provider_factory() for row in operation_declarations())


def operation_manifests():
    return tuple(row.manifest() for row in operation_declarations())


def declared_family(specification):
    """Use an explicit successor roster; historical specifications retain twelve."""
    return getattr(specification, "family_ids", FAMILY_IDS)
