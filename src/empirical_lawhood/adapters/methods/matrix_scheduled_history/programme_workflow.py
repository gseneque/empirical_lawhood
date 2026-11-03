# SPDX-License-Identifier: MPL-2.0
"""Bounded E4 phase joins and downstream nomination over original products.

There is no new scheduler or phase journal here. Phase readiness follows from
actual immutable selection, calibration and complete confirmation products.
All numerical decisions remain conditional until their domain sampling,
numerical, source and authority owners admit the applicable premises.
"""

from dataclasses import dataclass, replace
from decimal import Decimal
from fractions import Fraction
from itertools import combinations
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.runtime.experimental_factorial import holm_adjustment
from empirical_lawhood.runtime.experimental_statistics import PairedMeanTAlternative, paired_mean_t
from empirical_lawhood.runtime.experiment_preparation import DependencyKind, ExperimentDependency

from .programme_factorial import (
    ASSUMPTION_STATUS, E4_COMPARISONS, FAMILY_IDS, MISSING_COMPARISON, declared_family,
    ScheduledFactorialAssessment, ScheduledFactorialFamilySlot, _ratio, assess_programme_factorial,
)
from .programme_records import ScheduledProgramme
from .programme_selection import (
    ScheduledRevisionFrozenPackage, ScheduledRevisionNomination, _exact_decimal,
    freeze_programme_revision, validate_programme_paired_data,
)
from .revision_calibration import ScheduledRevisionCalibration, forecast_revision_cases, validate_revision_phase

STANDING = "CONDITIONAL_COMPLETE_E4_PROGRAMME_NO_QUALIFICATION_OR_DOWNSTREAM_AUTHORITY"
REVISION_COMPARISON = "e4.revision-baseline"
ENDPOINT = "WHOLE_GROUP_MAX_ABSOLUTE_PAIRED_LOG_PREDICTION_LOSS_NINE_COORDINATES_ALL30"


def _identity(record, name):
    return ObjectIdentity.from_record(getattr(record, name), record)


def _pin(value, kind):
    if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
        raise ValueError("E4 workflow substitutes its exact versioned scientific input")


@dataclass(frozen=True, slots=True)
class ScheduledE4NominationRule(CanonicalRecord):
    """Scientific choices supplied explicitly before confirmation, without defaults."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/downstream-nomination-rule"
    rule_id: str
    priority: tuple[str, ...]
    revision_baseline_null: Decimal
    minimum_original_covered_groups: int
    minimum_revision_covered_groups: int
    maximum_revision_radius: Decimal
    required_rejected_comparisons: tuple[str, ...]
    endpoint: str

    def __post_init__(self):
        self._validate_operands(maximum_groups=64)

    def _validate_operands(self, *, maximum_groups):
        validate_stable_id(self.rule_id)
        if (type(self.priority) is not tuple or len(self.priority) != 2 or set(self.priority) != {"ORIGINAL_E3", "REVISION"}
                or type(self.revision_baseline_null) is not Decimal or not self.revision_baseline_null.is_finite()
                or type(self.maximum_revision_radius) is not Decimal or not self.maximum_revision_radius.is_finite()
                or self.maximum_revision_radius < 0 or self.endpoint != ENDPOINT
                or type(self.required_rejected_comparisons) is not tuple
                or self.required_rejected_comparisons != tuple(sorted(set(self.required_rejected_comparisons)))
                or not set(self.required_rejected_comparisons) <= set((*E4_COMPARISONS, REVISION_COMPARISON))
                or any(type(value) is not int or not 0 <= value <= maximum_groups for value in
                    (self.minimum_original_covered_groups, self.minimum_revision_covered_groups))):
            raise ValueError("E4 nomination requires explicit endpoint, priority, margins, coverage and complete-family criteria")

    @property
    def identity(self):
        return _identity(self, "rule_id")


def validate_e4_populations(development, calibration, confirmation):
    """Retain all32/64/64 groups and disjoint group/root/source/noise identities."""
    phases = (development, calibration, confirmation)
    for programme, mode in zip(phases, ("E4_DEVELOPMENT", "E4_REVISION_CALIBRATION", "E4_CONFIRMATION"), strict=True):
        if type(programme) is not ScheduledProgramme or programme.mode != mode:
            raise ValueError("E4 workflow requires its actual32DEV/64CAL/64CONF programmes")
        programme.__post_init__()
        if (programme.reservation, programme.specification, programme.criterion, programme.factors, programme.confidence) != (
                development.reservation, development.specification, development.criterion, development.factors, development.confidence):
            raise ValueError("E4 phases change their frozen physical grid, original criterion or reservation")
    selectors = (lambda p: set(p.group_ids), lambda p: {row.root_id for row in p.cases},
        lambda p: {row.source for row in p.cases}, lambda p: {row.streams_sha256 for row in p.cases})
    for first, second in combinations(phases, 2):
        if any(select(first) & select(second) for select in selectors):
            raise ValueError("E4 phases reuse independent groups, roots, source identities or start/noise streams")


@dataclass(frozen=True, slots=True)
class ScheduledE4ProgrammeSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/e4-programme-specification"
    specification_id: str
    original_e3_package: ObjectIdentity
    original_e3_model: ObjectIdentity
    development: ObjectIdentity
    calibration: ObjectIdentity
    confirmation: ObjectIdentity
    nomination_rule: ScheduledE4NominationRule | None
    family_ids: tuple[str, ...] = FAMILY_IDS

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        for value in (self.original_e3_package, self.original_e3_model):
            if type(value) is not ObjectIdentity:
                raise TypeError("E4 workflow retains original E3 package and actual model identities")
            value.__post_init__()
        for value in (self.development, self.calibration, self.confirmation):
            _pin(value, ScheduledProgramme)
        if (len({self.development, self.calibration, self.confirmation}) != 3 or self.family_ids != FAMILY_IDS
                or self.nomination_rule is not None and type(self.nomination_rule) is not ScheduledE4NominationRule):
            raise ValueError("E4 workflow changes separate phases, twelve testing slots or its typed scientific nomination rule")
        if self.nomination_rule is not None:
            self.nomination_rule.__post_init__()

    @property
    def identity(self):
        return _identity(self, "specification_id")

    def validate(self, development, calibration, confirmation, *, banks=None):
        self.__post_init__()
        validate_e4_populations(development, calibration, confirmation)
        if (development.identity, calibration.identity, confirmation.identity) != (self.development, self.calibration, self.confirmation):
            raise ValueError("E4 workflow substitutes an actual assigned phase")
        if banks is not None:
            from .programme_records import validate_programme_bank
            if type(banks) is not tuple or len(banks) != 3:
                raise ValueError("E4 lowering requires all three actual native bank owners")
            for programme, bank in zip((development, calibration, confirmation), banks, strict=True):
                validate_programme_bank(programme, bank)
                if bank.forecast_design.model != self.original_e3_model:
                    raise ValueError("E4 lowering substitutes the unchanged original E3 model")

    @property
    def scientific_dependencies(self):
        if self.nomination_rule is not None:
            return ()
        return (ExperimentDependency("e4.nomination.scientific-choice", DependencyKind.SCIENTIFIC_EVIDENCE,
            "SCIENTIFIC_CHOICE: supply the frozen downstream nomination priority, endpoint, margin, coverage and radius criteria before confirmation."),)


@dataclass(frozen=True, slots=True)
class ScheduledE4PhaseReadiness:
    next_phase: str
    calibration_disposition: str
    revision_disposition: str
    dependencies: tuple[ExperimentDependency, ...]


def e4_phase_readiness(specification, development, calibration_programme, confirmation_programme,
        *, nomination=None, frozen=None, calibration=None, confirmation=None):
    specification.validate(development, calibration_programme, confirmation_programme)
    dependencies = specification.scientific_dependencies
    if confirmation is not None and (type(confirmation) is not ScheduledE4Confirmation
            or confirmation.specification != specification.identity):
        raise ValueError("E4 readiness requires its actual typed complete confirmation product")
    if nomination is None:
        if any(value is not None for value in (frozen, calibration, confirmation)):
            raise ValueError("E4 future products cannot precede their actual development nomination")
        return ScheduledE4PhaseReadiness("DEVELOPMENT", "UNENTERED", "UNENTERED", dependencies)
    if type(nomination) is not ScheduledRevisionNomination:
        raise TypeError("E4 phase readiness requires its actual immutable development nomination")
    if frozen is not None and type(frozen) is not ScheduledRevisionFrozenPackage:
        raise TypeError("E4 readiness requires its actual immutable joint model freeze")
    expected = freeze_programme_revision(development, nomination, freeze_id=frozen.package_id if frozen is not None else "freeze.required")
    if frozen is None:
        if calibration is not None or confirmation is not None:
            raise ValueError("E4 future products cannot precede the actual joint model freeze")
        return ScheduledE4PhaseReadiness("FREEZE", "UNENTERED", nomination.trigger_disposition, dependencies)
    if type(frozen) is not ScheduledRevisionFrozenPackage or frozen != expected:
        raise ValueError("E4 workflow substitutes the frozen original development selection")
    if nomination.trigger_disposition != "TRIGGERED":
        if calibration is not None:
            raise ValueError("an untriggered revision cannot enter its separate calibration branch")
        return ScheduledE4PhaseReadiness("NOMINATION" if confirmation is not None else "CONFIRMATION", "UNENTERED",
            nomination.trigger_disposition, dependencies)
    validate_revision_phase(development, nomination, frozen, calibration_programme, phase="CALIBRATION")
    validate_revision_phase(development, nomination, frozen, confirmation_programme, phase="CONFIRMATION")
    if calibration is None:
        if confirmation is not None:
            raise ValueError("E4 revision confirmation cannot precede separate actual calibration")
        return ScheduledE4PhaseReadiness("CALIBRATION", "UNENTERED", "FROZEN", dependencies)
    _validate_calibration(calibration, development, nomination, frozen, calibration_programme)
    return ScheduledE4PhaseReadiness("NOMINATION" if confirmation is not None else "CONFIRMATION", "COMPLETED", "FROZEN", dependencies)


def _validate_calibration(calibration, development, nomination, frozen, programme):
    if type(calibration) is not ScheduledRevisionCalibration:
        raise TypeError("E4 revision confirmation requires its actual separate calibration product")
    calibration.__post_init__()
    if ((calibration.specification.development_programme, calibration.specification.calibration_programme,
            calibration.specification.nomination, calibration.specification.frozen_models) !=
            (development.identity, programme.identity, nomination.identity, frozen.identity)
            or calibration.group_ids != programme.group_ids or calibration.revision_model != nomination.revision_model
            or calibration.baseline_model != nomination.baseline_model):
        raise ValueError("E4 confirmation substitutes calibration population, frozen model or original nomination")


@dataclass(frozen=True, slots=True)
class ScheduledE4ConfirmationGroup(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/e4-confirmation-group"
    independent_group_id: str
    original_covered: bool | None
    revision_covered: bool | None
    revision_loss: Decimal | None
    baseline_loss: Decimal | None

    def __post_init__(self):
        validate_stable_id(self.independent_group_id)
        for value in (self.original_covered, self.revision_covered):
            if value is not None and type(value) is not bool:
                raise TypeError("E4 confirmation retains exact whole-group coverage or missingness")
        if (self.revision_loss is None) != (self.baseline_loss is None):
            raise ValueError("E4 confirmation cannot thin its paired prediction-loss denominator")
        for value in (self.revision_loss, self.baseline_loss):
            if value is not None and (type(value) is not Decimal or not value.is_finite() or value < 0):
                raise ValueError("E4 confirmation retains finite nonnegative exact paired losses")


@dataclass(frozen=True, slots=True)
class ScheduledE4Confirmation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/e4-confirmation"
    record_id: str
    specification: ObjectIdentity
    factorial: ObjectIdentity
    calibration: ObjectIdentity | None
    groups: tuple[ScheduledE4ConfirmationGroup, ...]
    family_slots: tuple[ScheduledFactorialFamilySlot, ...]
    factorial_assessment: ScheduledFactorialAssessment
    nomination_rule: ScheduledE4NominationRule
    assumption_status: str = ASSUMPTION_STATUS
    standing: str = STANDING

    def __post_init__(self):
        validate_stable_id(self.record_id)
        _pin(self.specification, ScheduledE4ProgrammeSpecification)
        _pin(self.factorial, ScheduledFactorialAssessment)
        if self.calibration is not None:
            _pin(self.calibration, ScheduledRevisionCalibration)
        if (type(self.factorial_assessment) is not ScheduledFactorialAssessment
                or self.factorial != _identity(self.factorial_assessment, "assessment_id")
                or self.factorial_assessment.mode != "E4_CONFIRMATION"
                or type(self.nomination_rule) is not ScheduledE4NominationRule):
            raise ValueError("E4 confirmation substitutes actual original factorial or frozen nomination operands")
        if (type(self.groups) is not tuple or len(self.groups) != 64
                or any(type(row) is not ScheduledE4ConfirmationGroup for row in self.groups)
                or tuple(row.independent_group_id for row in self.groups) != tuple(sorted({row.independent_group_id for row in self.groups}))
                or type(self.family_slots) is not tuple or tuple(row.comparison_id for row in self.family_slots) != FAMILY_IDS
                or any(type(row) is not ScheduledFactorialFamilySlot for row in self.family_slots)
                or self.assumption_status != ASSUMPTION_STATUS or self.standing != STANDING):
            raise ValueError("E4 confirmation drops assigned whole groups, complete twelve-slot family or conditional standing")
        for row in (*self.groups, *self.family_slots):
            row.__post_init__()
        self.factorial_assessment.__post_init__()
        self.nomination_rule.__post_init__()
        if (tuple(row.independent_group_id for row in self.groups) != tuple(row.group_id for row in self.factorial_assessment.groups)
                or self.calibration is None and any(row.revision_covered is not None or row.revision_loss is not None for row in self.groups)
                or self.family_slots != _confirmation_family(self.groups, self.factorial_assessment, self.nomination_rule)):
            raise ValueError("E4 confirmation changes assigned groups or exact complete-family conditional arithmetic")

    @property
    def identity(self):
        return _identity(self, "record_id")


def _confirmation_family(groups, factorial, rule, *, alternative=PairedMeanTAlternative.LESS):
    values = tuple(None if row.revision_loss is None else Fraction(row.revision_loss) - Fraction(row.baseline_loss) for row in groups)
    contrast = paired_mean_t(tuple(row.independent_group_id for row in groups), values,
        null_value=rule.revision_baseline_null, alternative=alternative)
    p_values = {row.comparison.comparison_id: row.p_value for row in factorial.tests}
    p_values[REVISION_COMPARISON] = contrast.p_value
    family_ids = declared_family(factorial.specification)
    adjusted = holm_adjustment(family_ids, tuple((name, p_values.get(name)) for name in family_ids), alpha=factorial.specification.alpha)
    return tuple(ScheduledFactorialFamilySlot(row.comparison_id, p_values.get(row.comparison_id), _ratio(row.adjusted_p_value),
        row.disposition.value, () if row.p_value is not None else contrast.reason_codes if row.comparison_id == REVISION_COMPARISON
            else next((test.reason_codes for test in factorial.tests if test.comparison.comparison_id == row.comparison_id), (MISSING_COMPARISON,)))
        for row in adjusted.comparisons)


def assess_e4_confirmation(specification, development, calibration_programme, programme, nomination, frozen,
        calibration, reduction, data, forecasts, factorial, *, record_id):
    """Recompute whole-group losses and all12 Holm slots from actual products."""
    specification.validate(development, calibration_programme, programme)
    if specification.nomination_rule is None:
        raise ValueError("SCIENTIFIC_CHOICE: E4 confirmation lacks its frozen downstream nomination rule")
    readiness = e4_phase_readiness(specification, development, calibration_programme, programme,
        nomination=nomination, frozen=frozen, calibration=calibration)
    if readiness.next_phase != "CONFIRMATION":
        raise ValueError("E4 confirmation lacks actual predecessor selection, freeze or calibration products")
    if (type(factorial) is not ScheduledFactorialAssessment or factorial.mode != "E4_CONFIRMATION"
            or factorial != assess_programme_factorial(factorial.specification, programme, reduction, data,
                assessment_id=factorial.assessment_id)):
        raise ValueError("E4 confirmation substitutes the seven original factorial comparisons")
    targets, missing = validate_programme_paired_data(programme, reduction, data, nomination.specification.target,
        mode="E4_CONFIRMATION", missing_record_policy="ALLOW_ABSENT_DECLARED_ROWS")
    revision_entered = nomination.trigger_disposition == "TRIGGERED"
    if revision_entered:
        expected = forecast_revision_cases(development, nomination, frozen, programme, record_prefix="forecast.expected")
        if (type(forecasts) is not tuple or len(forecasts) != len(expected)
                or any(type(actual) is not type(wanted) or actual != replace(wanted, record_id=actual.record_id)
                    for actual, wanted in zip(forecasts, expected, strict=True))):
            raise ValueError("E4 confirmation changes frozen pre-outcome revision/baseline predictions")
    elif forecasts != ():
        raise ValueError("untriggered E4 revision forecasts remain explicitly unentered")
    by_result = {row.root_id: row for row in reduction.cases}
    by_forecast = {row.case_id: row for row in forecasts}
    groups = []
    for group in programme.group_ids:
        cases = tuple(row for row in programme.cases if row.independent_group_id == group)
        original = None if group in missing or any(upper is None for case in cases
            for upper in by_result[case.root_id].upper_log_errors) else all(
            upper is not None and Fraction(actual) <= Fraction(upper)
            for case in cases for actual, upper in zip(targets[case.root_id], by_result[case.root_id].upper_log_errors * 2, strict=True))
        revision_loss, baseline_loss, covered = None, None, None
        if revision_entered and group not in missing:
            losses = []
            for name in ("revision_predictions", "baseline_predictions"):
                losses.append(max(abs(Fraction(actual) - Fraction(point)) for case in cases
                    for actual, point in zip(targets[case.root_id], getattr(by_forecast[case.root_id], name), strict=True)))
            revision_loss, baseline_loss = (_exact_decimal(value) for value in losses)
            covered = all(calibration.revision_radius is None or Fraction(actual) - Fraction(point) <= Fraction(calibration.revision_radius)
                for case in cases for actual, point in zip(targets[case.root_id], by_forecast[case.root_id].revision_predictions, strict=True))
        groups.append(ScheduledE4ConfirmationGroup(group, original, covered, revision_loss, baseline_loss))
    slots = _confirmation_family(tuple(groups), factorial, specification.nomination_rule)
    return ScheduledE4Confirmation(record_id, specification.identity, _identity(factorial, "assessment_id"),
        calibration.identity if calibration is not None else None, tuple(groups), slots, factorial, specification.nomination_rule)


@dataclass(frozen=True, slots=True)
class ScheduledE4DownstreamNomination(CanonicalRecord):
    """Retained outcome evidence for one original package/optional revision.

    This record includes confirmation and calibration outcomes. A future
    consumer needs an authenticated public model projection; this complete
    decision record must never be relabeled as a blind future input.
    """

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/downstream-nomination"
    record_id: str
    specification: ObjectIdentity
    rule: ObjectIdentity
    confirmation: ObjectIdentity
    original_e3_package: ObjectIdentity
    frozen_revision: ObjectIdentity | None
    calibration: ObjectIdentity | None
    selected: str | None
    dispositions: tuple[tuple[str, str], ...]
    rule_product: ScheduledE4NominationRule
    confirmation_product: ScheduledE4Confirmation
    frozen_product: ScheduledRevisionFrozenPackage
    calibration_product: ScheduledRevisionCalibration | None
    standing: str = STANDING

    def __post_init__(self):
        validate_stable_id(self.record_id)
        _pin(self.specification, ScheduledE4ProgrammeSpecification)
        _pin(self.rule, ScheduledE4NominationRule)
        _pin(self.confirmation, ScheduledE4Confirmation)
        if (type(self.rule_product) is not ScheduledE4NominationRule
                or type(self.confirmation_product) is not ScheduledE4Confirmation
                or type(self.frozen_product) is not ScheduledRevisionFrozenPackage
                or self.rule != self.rule_product.identity or self.confirmation != self.confirmation_product.identity
                or self.confirmation_product.specification != self.specification
                or self.confirmation_product.nomination_rule != self.rule_product
                or self.calibration_product is not None and type(self.calibration_product) is not ScheduledRevisionCalibration):
            raise ValueError("E4 downstream nomination substitutes its actual retained immutable decision operands")
        if (self.selected not in (None, "ORIGINAL_E3", "REVISION") or type(self.dispositions) is not tuple
                or tuple(name for name, _ in self.dispositions) != ("ORIGINAL_E3", "REVISION")
                or any(value not in ("ELIGIBLE", "NOT_ELIGIBLE", "UNEVALUABLE", "UNENTERED") for _, value in self.dispositions)
                or self.selected is not None and dict(self.dispositions)[self.selected] != "ELIGIBLE"
                or (self.frozen_revision is None) != (self.calibration is None) or self.standing != STANDING):
            raise ValueError("E4 downstream nomination loses alternatives or invents an eligible calibrated revision")
        if self.frozen_revision is not None:
            _pin(self.frozen_revision, ScheduledRevisionFrozenPackage)
            _pin(self.calibration, ScheduledRevisionCalibration)
        self.rule_product.__post_init__()
        self.confirmation_product.__post_init__()
        self.frozen_product.__post_init__()
        product = self.calibration_product
        if product is not None:
            product.__post_init__()
        if (self.calibration != (product.identity if product is not None else None)
                or self.confirmation_product.calibration != self.calibration
                or self.frozen_revision != (self.frozen_product.identity if product is not None else None)
                or product is not None and product.specification.frozen_models != self.frozen_product.identity
                or (product is None) != (self.frozen_product.disposition == "UNENTERED")):
            raise ValueError("E4 downstream nomination invents entry or substitutes the actual calibrated joint freeze")
        expected = _nomination_dispositions(self.rule_product, self.confirmation_product, product)
        chosen = next((name for name in self.rule_product.priority if dict(expected)[name] == "ELIGIBLE"), None)
        if self.dispositions != expected or self.selected != chosen:
            raise ValueError("E4 downstream nomination changes the frozen rule evaluation or hides an alternative")


def _nomination_dispositions(rule, confirmation, calibration):
    original = "UNEVALUABLE" if any(row.original_covered is None for row in confirmation.groups) else "ELIGIBLE" if sum(
        row.original_covered is True for row in confirmation.groups) >= rule.minimum_original_covered_groups else "NOT_ELIGIBLE"
    revision = "UNENTERED"
    if calibration is not None:
        slots = {row.comparison_id: row for row in confirmation.family_slots}
        missing = any(row.revision_covered is None for row in confirmation.groups) or any(
            slots[name].conditional_disposition == "UNEVALUABLE" for name in rule.required_rejected_comparisons)
        revision = "UNEVALUABLE" if missing else "ELIGIBLE" if (
            sum(row.revision_covered is True for row in confirmation.groups) >= rule.minimum_revision_covered_groups
            and calibration.revision_radius is not None and calibration.revision_radius <= rule.maximum_revision_radius
            and all(slots[name].conditional_disposition == "REJECTED" for name in rule.required_rejected_comparisons)) else "NOT_ELIGIBLE"
    return (("ORIGINAL_E3", original), ("REVISION", revision))


def nominate_e4_downstream(specification, confirmation, frozen, calibration, *, record_id):
    if type(specification) is not ScheduledE4ProgrammeSpecification or specification.nomination_rule is None:
        raise ValueError("SCIENTIFIC_CHOICE: E4 downstream nomination needs its frozen explicit rule")
    if type(confirmation) is not ScheduledE4Confirmation or confirmation.specification != specification.identity:
        raise ValueError("E4 downstream nomination substitutes actual complete confirmation products")
    specification.__post_init__()
    confirmation.__post_init__()
    rule = specification.nomination_rule
    if (confirmation.nomination_rule != rule or confirmation.factorial_assessment.programme != specification.confirmation):
        raise ValueError("E4 downstream nomination substitutes its frozen rule or actual confirmation programme")
    if (confirmation.calibration != (calibration.identity if calibration is not None else None)
            or type(frozen) is not ScheduledRevisionFrozenPackage
            or frozen.programme != specification.development):
        raise ValueError("E4 downstream nomination substitutes frozen models or actual calibration")
    if calibration is not None:
        calibration.__post_init__()
        if calibration.specification.frozen_models != frozen.identity:
            raise ValueError("E4 downstream nomination substitutes its pre-confirmation frozen revision")
    dispositions = _nomination_dispositions(rule, confirmation, calibration)
    selected = next((name for name in rule.priority if dict(dispositions)[name] == "ELIGIBLE"), None)
    return ScheduledE4DownstreamNomination(record_id, specification.identity, rule.identity, confirmation.identity,
        specification.original_e3_package, frozen.identity if calibration is not None else None,
        calibration.identity if calibration is not None else None, selected, dispositions, rule, confirmation, frozen, calibration)


def e4_acquisition_draft(*, specification, development, calibration_programme, confirmation_programme,
        banks, scope, global_parent_binding, proof_owners, operational_budgets, template_bytes, draft_id,
        nomination=None, frozen=None, calibration=None, revision_custody=(), calibration_payload=None,
        revision_calibration_custody=None):
    """Project the selected next phase through the actual native acquisition owner.

    Real global/qualified parents and prior seal publications are supplied by
    their existing custody services. Triggered confirmation retains the actual
    original sealed calibration producer as an explicit public custody input;
    its native parent still authenticates issue, reveal and the complete
    original producer/scientific input closure. This join grants no entry.
    """
    from .programme_acquisition import ScheduledProgrammeAcquisitionScope
    from .programme_acquisition_composition import programme_acquisition_draft
    from .revision_calibrated_future_bindings import add_calibrated_revision_future_dependencies
    from .revision_calibration_custody import ScheduledRevisionCalibrationCustody
    from .revision_future_bindings import ScheduledRevisionFutureScope, add_revision_future_dependencies
    from .revision_public import ScheduledRevisionPublicCalibration

    specification.validate(development, calibration_programme, confirmation_programme, banks=banks)
    readiness = e4_phase_readiness(specification, development, calibration_programme, confirmation_programme,
        nomination=nomination, frozen=frozen, calibration=calibration)
    if type(scope) is not ScheduledProgrammeAcquisitionScope:
        raise TypeError("E4 lowering needs the actual original acquisition scope and global scientific root")
    phases = {"DEVELOPMENT": development, "CALIBRATION": calibration_programme, "CONFIRMATION": confirmation_programme}
    programme = phases.get(readiness.next_phase)
    if programme is None or scope.programme != programme:
        raise ValueError("E4 lowering cannot enter a future phase before its actual immutable prerequisites")
    if readiness.next_phase == "CONFIRMATION" and readiness.dependencies:
        raise ValueError("SCIENTIFIC_CHOICE: E4 confirmation requires its frozen explicit downstream nomination rule")
    revision_entered = readiness.next_phase != "DEVELOPMENT" and nomination.trigger_disposition == "TRIGGERED"
    calibrated_confirmation = revision_entered and readiness.next_phase == "CONFIRMATION"
    if calibrated_confirmation:
        if type(revision_calibration_custody) is not ScheduledRevisionCalibrationCustody:
            raise TypeError("triggered E4 confirmation requires actual original revision calibration producer custody")
        revision_calibration_custody.__post_init__()
        if revision_calibration_custody.calibration != ScheduledRevisionPublicCalibration.from_calibration(calibration):
            raise ValueError("E4 confirmation substitutes its actual original complete calibration projection or producer")
    elif revision_calibration_custody is not None:
        raise ValueError("only triggered E4 confirmation may consume original revision calibration producer custody")
    bank = banks[(development, calibration_programme, confirmation_programme).index(programme)]
    draft, operands = programme_acquisition_draft(scope=scope, bank=bank, global_parent_binding=global_parent_binding,
        proof_owners=proof_owners, operational_budgets=operational_budgets, template_bytes=template_bytes,
        draft_id=draft_id, calibration_payload=calibration_payload)
    if revision_entered:
        future = ScheduledRevisionFutureScope("revision-scope." + programme.programme_id,
            development, nomination, frozen, programme,
            calibration_programme if readiness.next_phase == "CONFIRMATION" else None,
            ScheduledRevisionPublicCalibration.from_calibration(calibration) if readiness.next_phase == "CONFIRMATION" else None,
            specification.nomination_rule if readiness.next_phase == "CONFIRMATION" else None)
        if calibrated_confirmation:
            draft, additions = add_calibrated_revision_future_dependencies(
                draft, future, revision_custody, revision_calibration_custody)
        else:
            draft, additions = add_revision_future_dependencies(draft, future, revision_custody)
        for name, record in additions.items():
            if operands.setdefault(name, record) != record:
                raise ValueError("E4 lowering aliases actual immutable scientific source bytes")
    elif revision_custody:
        raise ValueError("an unentered E4 revision cannot gain future seal custody or native dependencies")
    return draft, operands
