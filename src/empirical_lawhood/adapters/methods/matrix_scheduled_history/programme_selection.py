# SPDX-License-Identifier: MPL-2.0
"""Explicit finite E4 development selection over original paired score records.

This first implemented family uses committed physical grid parameters, signed
pair terms and one aggregate center term. It does not invent causal descriptors,
choose a scientific trigger, identify separate quadratic terms, or qualify a
model. Original programme, score, prefix and reduction records remain unchanged.
"""

from bisect import bisect_left
from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft

from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.experimental_selection import DeclaredSelectionDesign, DeclaredSelectionFreeze, DeclaredSelectionResult
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.runtime.experimental_selection import (
    evaluate_declared_candidates, freeze_declared_selection, require_development_selection_phase,
    require_frozen_selection_for_phase, selection_score, validate_declared_selection_result, validate_selection_design,
    unentered_declared_selection,
)
from empirical_lawhood.runtime.experimental_statistics import StandardizedRidgeParameters, fit_standardized_ridge, predict_standardized_ridge
from empirical_lawhood.adapters.methods.matrix_factor_response.records import ACTION_ROLES, PREDICTORS
from empirical_lawhood.adapters.methods.matrix_factor_response.response_frontier import MatrixResponseFrontierProtocol
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate

from .programme_records import MODES, NAMESPACE, ScheduledProgramme
from .programme_reduction import ScheduledProgrammeReduction
from .records import ScheduledCausalPrefix, identity
from .response_records import ScheduledResponseScore

PHYSICAL = ("temperature", "friction", "coupling")
PAIR_FEATURES = ("pair.temperature-friction", "pair.temperature-coupling", "pair.friction-coupling")
FEATURES = tuple(sorted((*PHYSICAL, *PAIR_FEATURES, "aggregate-curvature")))
VIEWS = ("PRIMARY", "FINE")
FAMILY = "physical-grid-standardized-ridge"
STANDING = "EXPOSED_DEVELOPMENT_NOMINATION_NO_QUALIFICATION"


def _finite(value, *, positive=False):
    if type(value) is not Decimal or not value.is_finite() or positive and value <= 0:
        raise ValueError("selection needs finite explicit Decimal scientific operands")


@dataclass(frozen=True, slots=True)
class ScheduledRevisionTuning(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/revision-tuning"
    tuning_id: str
    family_id: str
    feature_names: tuple[str, ...]
    penalty: Decimal
    penalize_intercept: bool
    maximum_coefficients_per_endpoint: int

    def __post_init__(self):
        validate_stable_id(self.tuning_id)
        _finite(self.penalty, positive=True)
        if (self.family_id != FAMILY or type(self.feature_names) is not tuple
                or self.feature_names != tuple(sorted(set(self.feature_names)))
                or not set(PHYSICAL) <= set(self.feature_names) <= set(FEATURES)
                or type(self.penalize_intercept) is not bool
                or type(self.maximum_coefficients_per_endpoint) is not int
                or not len(self.feature_names)+1 <= self.maximum_coefficients_per_endpoint <= len(FEATURES)+1):
            raise ValueError("E4 tuning changes its explicitly declared compact physical-grid family")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.tuning_id, self)


@dataclass(frozen=True, slots=True)
class ScheduledRevisionTarget(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/revision-target"
    target_id: str
    criterion: ObjectIdentity
    horizon_ticks: tuple[int, ...]
    numerical_views: tuple[str, ...]
    definition: str

    def __post_init__(self):
        validate_stable_id(self.target_id)
        if (type(self.criterion) is not ObjectIdentity or self.criterion.object_schema != MatrixResponseFrontierProtocol.SCHEMA
                or type(self.horizon_ticks) is not tuple or len(self.horizon_ticks) != 3
                or self.horizon_ticks != tuple(sorted(set(self.horizon_ticks)))
                or any(type(tick) is not int or tick < 1 for tick in self.horizon_ticks)
                or self.numerical_views != VIEWS or self.definition != "CUMULATIVE_LOG1P_NORMALIZED_RESPONSE_ERROR_ALL15"):
            raise ValueError("E4 selection cannot revise its original paired fifteen-endpoint target or criterion")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.target_id, self)


@dataclass(frozen=True, slots=True)
class ScheduledRevisionTrigger(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/revision-trigger"
    trigger_id: str
    metric: str
    comparison: str
    threshold: Decimal

    def __post_init__(self):
        validate_stable_id(self.trigger_id)
        _finite(self.threshold)
        if (self.metric != "MEAN_COMPLETE_GROUP_MAX_PAIRED_LOG_ERROR" or self.comparison not in ("GREATER_THAN", "AT_LEAST")
                or self.threshold < 0):
            raise ValueError("E4 inadequacy trigger must be scientifically selected explicitly")


@dataclass(frozen=True, slots=True)
class ScheduledRevisionFeatureDefinition(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/revision-feature-definition"
    feature_id: str
    programme: ObjectIdentity
    feature_names: tuple[str, ...]
    rule: str

    def __post_init__(self):
        validate_stable_id(self.feature_id)
        if (type(self.programme) is not ObjectIdentity or self.programme.object_schema != ScheduledProgramme.SCHEMA
                or self.feature_names != FEATURES or self.rule != "COMMITTED_PHYSICAL_VALUES_SIGNED_GRID_PAIRS_ONE_CENTER_INDICATOR"):
            raise ValueError("E4 feature contract cannot invent future-informed descriptors or separate quadratic terms")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.feature_id, self)


def feature_definition(programme):
    return ScheduledRevisionFeatureDefinition("features."+programme.programme_id, programme.identity, FEATURES,
        "COMMITTED_PHYSICAL_VALUES_SIGNED_GRID_PAIRS_ONE_CENTER_INDICATOR")


def programme_selection_allocation(programme):
    if type(programme) is not ScheduledProgramme or programme.mode != "E4_DEVELOPMENT":
        raise ValueError("revision fitting consumes the original complete E4 development programme only")
    programme.__post_init__()
    by_group = {group: tuple(row for row in programme.cases if row.independent_group_id == group) for group in programme.group_ids}
    return UnitAllocation("selection-allocation."+programme.programme_id, (programme.identity,),
        tuple(IndependentUnit(group, programme.programme_id, rows[0].family_id, ("fine", "primary"), True)
              for group, rows in by_group.items()),
        tuple(UnitRoleAssignment(group, "development") for group in programme.group_ids))


@dataclass(frozen=True, slots=True)
class ScheduledRevisionSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/revision-selection-specification"
    specification_id: str
    programme: ObjectIdentity
    target: ScheduledRevisionTarget
    trigger: ScheduledRevisionTrigger
    revision_design: DeclaredSelectionDesign
    baseline_design: DeclaredSelectionDesign
    tunings: tuple[ScheduledRevisionTuning, ...]

    def __post_init__(self):
        self._validate_operands(programme_schema=ScheduledProgramme.SCHEMA)

    def _validate_operands(self, *, programme_schema):
        validate_stable_id(self.specification_id)
        if (type(self.programme) is not ObjectIdentity or self.programme.object_schema != programme_schema
                or type(self.target) is not ScheduledRevisionTarget or type(self.trigger) is not ScheduledRevisionTrigger
                or type(self.revision_design) is not DeclaredSelectionDesign or type(self.baseline_design) is not DeclaredSelectionDesign
                or type(self.tunings) is not tuple or not self.tunings
                or any(type(row) is not ScheduledRevisionTuning for row in self.tunings)
                or tuple(row.tuning_id for row in self.tunings) != tuple(sorted({row.tuning_id for row in self.tunings}))):
            raise ValueError("E4 selection requires its explicit original scientific design and complete tuning records")
        for record in (self.target, self.trigger, self.revision_design, self.baseline_design, *self.tunings):
            record.__post_init__()
        revision, baseline = self.revision_design, self.baseline_design
        if ((revision.allocation, revision.development_role, revision.folds, revision.fold_count,
                revision.maximum_fit_calls, revision.target, revision.criterion, revision.features, revision.score_direction, revision.missing_policy)
                != (baseline.allocation, baseline.development_role, baseline.folds, baseline.fold_count,
                baseline.maximum_fit_calls, baseline.target, baseline.criterion, baseline.features, baseline.score_direction, baseline.missing_policy)
                or revision.development_role != "development" or revision.score_direction != "MINIMIZE"
                or revision.target != self.target.identity or revision.criterion != self.target.criterion
                or len(revision.candidates) != len(baseline.candidates)
                or {row.candidate_id for row in revision.candidates} & {row.candidate_id for row in baseline.candidates}):
            raise ValueError("revision and conventional baseline require the same information, whole folds and comparable finite fitting budget")
        by_identity = {row.identity: row for row in self.tunings}
        candidates = (*revision.candidates, *baseline.candidates)
        if (set(by_identity) != {row.tuning for row in candidates}
                or any(row.family_id != FAMILY or row.family_id != by_identity[row.tuning].family_id for row in candidates)):
            raise ValueError("E4 candidate tuning labels do not substitute their actual fitted family or penalty")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)

    def validate_programme(self, programme):
        allocation = programme_selection_allocation(programme)
        if self.programme != programme.identity or self.target.criterion != programme.criterion:
            raise ValueError("E4 selection changes its original programme or scientific target/tolerance")
        for design in (self.revision_design, self.baseline_design):
            validate_selection_design(design, allocation)
            if design.features != feature_definition(programme).identity:
                raise ValueError("E4 selection changes its actual pre-cutoff physical feature extractor")
        return allocation


@dataclass(frozen=True, slots=True)
class ScheduledRevisionCaseData(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/revision-case-data"
    root_id: str
    coordinate: MatrixParameterCoordinate
    causal_prefix: ScheduledCausalPrefix | None
    score: ScheduledResponseScore | None

    def __post_init__(self):
        validate_stable_id(self.root_id)
        if (type(self.coordinate) is not MatrixParameterCoordinate
                or self.causal_prefix is not None and type(self.causal_prefix) is not ScheduledCausalPrefix
                or self.score is not None and type(self.score) is not ScheduledResponseScore):
            raise TypeError("revision data retains actual original coordinate, causal prefix and paired score records")
        for record in (self.coordinate, self.causal_prefix, self.score):
            if record is not None:
                record.__post_init__()


@dataclass(frozen=True, slots=True)
class ScheduledRevisionDataBank(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/revision-data-bank"
    bank_id: str
    programme: ObjectIdentity
    reduction: ObjectIdentity
    cases: tuple[ScheduledRevisionCaseData, ...]

    def __post_init__(self):
        validate_stable_id(self.bank_id)
        if (type(self.programme) is not ObjectIdentity or self.programme.object_schema != ScheduledProgramme.SCHEMA
                or type(self.reduction) is not ObjectIdentity or self.reduction.object_schema != ScheduledProgrammeReduction.SCHEMA
                or type(self.cases) is not tuple or any(type(row) is not ScheduledRevisionCaseData for row in self.cases)
                or tuple(row.root_id for row in self.cases) != tuple(sorted({row.root_id for row in self.cases}))):
            raise ValueError("revision bank retains a closed complete original case census")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.bank_id, self)


def _paired_targets(target, score):
    if score is None or not score.numerical_pass or score.disposition not in ("FINITE", "PARTIAL"):
        return (None,)*30
    score.__post_init__()
    panels = {cell.panel_id for cell in score.cells if cell.view == "PRIMARY"}
    actions = {cell.action_id for cell in score.cells if cell.view == "PRIMARY"}
    expected = {(view, panel, action, predictor, horizon) for view in VIEWS for panel in panels for action in actions
                for predictor in PREDICTORS for horizon in target.horizon_ticks}
    if len(panels) != 2 or len(actions) != len(ACTION_ROLES) or {cell.key for cell in score.cells} != expected:
        return (None,)*30
    values = []
    for view in VIEWS:
        for predictor in PREDICTORS:
            for horizon in target.horizon_ticks:
                cells = tuple(cell.normalized_error for cell in score.cells
                              if cell.view == view and cell.predictor == predictor and cell.horizon_tick <= horizon)
                with localcontext() as context:
                    context.prec = 50
                    values.append(None if any(value is None for value in cells) else (Decimal(1)+max(cells)).ln())
    if tuple(values[:15]) != score.cumulative_log_errors:
        raise ValueError("original primary score differs from the unchanged paired target reduction equation")
    return tuple(values)


def validate_programme_paired_data(programme, reduction, data, target, *, mode, missing_record_policy):
    """Join original paired outcomes and pre-cutoff frames in an explicit E4 mode.

    The selected policy either requires the full evidence-row census or retains
    absent declared rows as missing targets against the unchanged assigned
    programme/reduction census. Unknown, duplicate and reordered rows refuse.
    This authenticates scientific record associations, not access authority or
    pre-outcome freezing. Protected confirmation consumers must additionally use
    their owning qualified-parent, frozen-criteria and outcome-access services.
    """
    if (mode not in ("E4_DEVELOPMENT", "E4_REVISION_CALIBRATION", "E4_CONFIRMATION") or mode not in MODES
            or type(programme) is not ScheduledProgramme or programme.mode != mode
            or type(target) is not ScheduledRevisionTarget or target.criterion != programme.criterion):
        raise ValueError("paired data changes its explicitly selected original E4 phase or target")
    programme.__post_init__()
    target.__post_init__()
    if type(missing_record_policy) is not str or missing_record_policy not in ("STRICT", "ALLOW_ABSENT_DECLARED_ROWS"):
        raise ValueError("paired data requires an explicit closed missing-record policy")
    if (type(reduction) is not ScheduledProgrammeReduction or reduction.mode != mode
            or reduction.programme != programme.identity or type(data) is not ScheduledRevisionDataBank
            or data.programme != programme.identity or data.reduction != ObjectIdentity.from_record(reduction.reduction_id, reduction)
            or tuple((row.root_id, row.source, row.independent_group_id) for row in reduction.cases)
                != tuple((row.root_id, row.source, row.independent_group_id) for row in programme.cases)):
        raise ValueError("E4 selection substitutes original development reduction, full groups or source bank")
    reduction.__post_init__()
    data.__post_init__()
    declared = tuple(case.root_id for case in programme.cases)
    actual = tuple(row.root_id for row in data.cases)
    actual_ids = set(actual)
    if (actual != tuple(root for root in declared if root in actual_ids)
            or missing_record_policy == "STRICT" and actual != declared):
        raise ValueError("E4 selection substitutes original development reduction, full groups or source bank")
    by_root = {row.root_id: row for row in data.cases}
    targets, missing = {}, set()
    for case, result in zip(programme.cases, reduction.cases, strict=True):
        row = by_root.get(case.root_id)
        if row is None:
            targets[case.root_id] = (None,)*30
            missing.add(case.independent_group_id)
            continue
        row.__post_init__()
        coordinate, prefix, score = row.coordinate, row.causal_prefix, row.score
        if (ObjectIdentity.from_record(coordinate.coordinate_id, coordinate) != case.coordinate or coordinate.clock_id != case.information_cutoff.clock_id or coordinate.family_id != case.family_id
                or (coordinate.primary_view.bath_temperature, coordinate.primary_view.friction_gamma,
                    coordinate.member.cross_coupling_gamma) != case.factor_values):
            raise ValueError("revision features substitute exact original source coordinates or physical parameters")
        if prefix is not None and (prefix.source != case.source or prefix.root.root_id != case.root_id
                or prefix.root.independent_group_id != case.independent_group_id or prefix.root.role.value != case.role
                or prefix.root.coordinate_id != case.coordinate.object_id or prefix.root.clock_id != coordinate.clock_id
                or coordinate.physical_time(prefix.cutoff_tick) != case.information_cutoff.coordinate):
            raise ValueError("revision features substitute the original causal frame, physical clock or pre-action cutoff")
        if score is not None and (identity(score) != result.score or score.source != case.source or score.root_id != case.root_id
                or score.independent_group_id != case.independent_group_id or score.role != case.role
                or score.criterion != programme.criterion or score.cumulative_log_errors != result.cumulative_log_errors
                or prefix is None or score.causal_prefix != identity(prefix)):
            raise ValueError("revision target changes original source, paired score or pre-cutoff frame lineage")
        targets[case.root_id] = _paired_targets(target, score)
        if (prefix is None or prefix.disposition != "AVAILABLE" or result.disposition != "COMPLETED"
                or result.numerical_disposition != "SATISFIED" or any(value is None for value in targets[case.root_id])):
            missing.add(case.independent_group_id)
    return targets, frozenset(missing)


def revision_case_features(programme, case):
    """The unchanged committed grid features, available before response contact."""
    index = bisect_left(programme.cases, case.root_id, key=lambda row: row.root_id)
    if index == len(programme.cases) or programme.cases[index] != case:
        raise ValueError("revision features require an actual declared programme case")
    return physical_grid_features(programme.factors, case.factor_values)


def physical_grid_features(factors, factor_values):
    """Original physical grid feature equation, without source/authority claims."""
    coded = tuple(Decimal(-1) if value == axis.low else Decimal(1) if value == axis.high else Decimal(0)
                  for value, axis in zip(factor_values, factors, strict=True))
    values = dict(zip(PHYSICAL, factor_values, strict=True))
    values.update(zip(PAIR_FEATURES, (coded[0]*coded[1], coded[0]*coded[2], coded[1]*coded[2]), strict=True))
    values["aggregate-curvature"] = Decimal(all(value == 0 for value in coded))
    return values


def _validate_data(specification, programme, reduction, data):
    allocation = specification.validate_programme(programme)
    targets, missing = validate_programme_paired_data(programme, reduction, data, specification.target,
        mode="E4_DEVELOPMENT", missing_record_policy="STRICT")
    features = {case.root_id: revision_case_features(programme, case) for case in programme.cases}
    return allocation, features, targets, set(missing)


@dataclass(frozen=True, slots=True)
class ScheduledRevisionFittedModel(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/revision-fitted-model"
    model_id: str
    candidate_id: str
    tuning: ScheduledRevisionTuning
    training_groups: tuple[str, ...]
    parameters: tuple[StandardizedRidgeParameters, ...]

    def __post_init__(self):
        validate_stable_id(self.model_id); validate_stable_id(self.candidate_id)
        if (type(self.tuning) is not ScheduledRevisionTuning or type(self.training_groups) is not tuple
                or self.training_groups != tuple(sorted(set(self.training_groups))) or not self.training_groups
                or type(self.parameters) is not tuple or len(self.parameters) != 30
                or any(type(row) is not StandardizedRidgeParameters or row.training_rows != 9*len(self.training_groups)
                    or row.fitted_rows != row.training_rows or row.coefficients is None
                    or len(row.coefficients) > self.tuning.maximum_coefficients_per_endpoint for row in self.parameters)):
            raise ValueError("E4 fit retains its exact complete paired bundle, compact parameters and whole training groups")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.model_id, self)


def _fit_bundle(tuning, groups, programme, features, targets, *, model_id, candidate_id):
    cases = tuple(case for case in programme.cases if case.independent_group_id in groups)
    x = tuple(tuple(features[case.root_id][name] for name in tuning.feature_names) for case in cases)
    fitted = tuple(fit_standardized_ridge(x, tuple(targets[case.root_id][endpoint] for case in cases),
        penalty=tuning.penalty, penalize_intercept=tuning.penalize_intercept) for endpoint in range(30))
    return ScheduledRevisionFittedModel(model_id, candidate_id, tuning, groups, fitted)


def _crossfit(specification, design, allocation, programme, features, targets, missing, *, result_id):
    tunings = {row.identity: row for row in specification.tunings}
    def fit_and_score(*, candidate, fold, training_unit_ids, heldout_unit_ids):
        if missing:
            return tuple(selection_score(candidate.candidate_id, group, fold, None) for group in heldout_unit_ids)
        tuning = tunings[candidate.tuning]
        model = _fit_bundle(tuning, training_unit_ids, programme, features, targets,
            model_id="fold-model."+candidate.candidate_id+"."+str(fold), candidate_id=candidate.candidate_id)
        scores = []
        for group in heldout_unit_ids:
            losses = []
            for case in programme.cases:
                if case.independent_group_id != group:
                    continue
                x = tuple(features[case.root_id][name] for name in tuning.feature_names)
                predictions = tuple(predict_standardized_ridge(parameters, x) for parameters in model.parameters)
                losses.extend(abs(Fraction(actual)-Fraction(predicted)) for actual, predicted
                              in zip(targets[case.root_id], predictions, strict=True))
            scores.append(selection_score(candidate.candidate_id, group, fold, _exact_decimal(max(losses))))
        return tuple(scores)
    return evaluate_declared_candidates(design, allocation, fit_and_score=fit_and_score, result_id=result_id)


def _exact_decimal(value):
    denominator, twos, fives = value.denominator, 0, 0
    while denominator % 2 == 0:
        denominator //= 2; twos += 1
    while denominator % 5 == 0:
        denominator //= 5; fives += 1
    if denominator != 1:
        raise ValueError("declared Decimal score difference unexpectedly has a nonterminating expansion")
    places = max(twos, fives)
    coefficient = value.numerator * 2**(places-twos) * 5**(places-fives)
    return Decimal((int(coefficient < 0), Decimal(abs(coefficient)).as_tuple().digits, -places))


@dataclass(frozen=True, slots=True)
class ScheduledRevisionNomination(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/revision-nomination"
    nomination_id: str
    specification: ScheduledRevisionSpecification
    data: ObjectIdentity
    revision_selection: DeclaredSelectionResult
    baseline_selection: DeclaredSelectionResult
    trigger_disposition: str
    revision_model: ScheduledRevisionFittedModel | None
    baseline_model: ScheduledRevisionFittedModel | None
    endpoint_fit_calls: int
    missing_groups: tuple[str, ...]
    standing: str = STANDING

    def __post_init__(self):
        self._validate_operands(specification_type=ScheduledRevisionSpecification, data_schema=ScheduledRevisionDataBank.SCHEMA)

    def _validate_operands(self, *, specification_type, data_schema):
        validate_stable_id(self.nomination_id)
        if (type(self.specification) is not specification_type or type(self.data) is not ObjectIdentity
                or self.data.object_schema != data_schema
                or type(self.revision_selection) is not DeclaredSelectionResult or type(self.baseline_selection) is not DeclaredSelectionResult
                or self.trigger_disposition not in ("TRIGGERED", "NOT_TRIGGERED", "UNEVALUABLE")
                or type(self.endpoint_fit_calls) is not int or self.endpoint_fit_calls < 0
                or self.missing_groups != tuple(sorted(set(self.missing_groups))) or self.standing != STANDING):
            raise ValueError("E4 nomination preserves explicit trigger, full adverse groups and development standing")
        models = (self.revision_model, self.baseline_model)
        if ((self.trigger_disposition == "TRIGGERED") != all(model is not None for model in models)
                or self.trigger_disposition != "TRIGGERED" and any(model is not None for model in models)
                or self.trigger_disposition == "UNEVALUABLE" and not self.missing_groups):
            raise ValueError("E4 unentered/unevaluable revision cannot invent a fitted model")
        if self.trigger_disposition != "UNEVALUABLE" and self.missing_groups:
            raise ValueError("E4 nomination cannot discard missing paired development groups")
        expected_calls = 30*(self.revision_selection.fit_calls+self.baseline_selection.fit_calls+2) if self.trigger_disposition == "TRIGGERED" else 0
        if self.endpoint_fit_calls != expected_calls:
            raise ValueError("E4 nomination changes actual paired endpoint-fit call accounting")
        for model, result, design in zip(models, (self.revision_selection, self.baseline_selection),
                (self.specification.revision_design, self.specification.baseline_design), strict=True):
            if result.design != design.identity or result.allocation != design.allocation:
                raise ValueError("E4 selection substitutes its declared original design/allocation")
            candidate = next((row for row in design.candidates if row.candidate_id == result.selected_candidate_id), None)
            if model is not None and (type(model) is not ScheduledRevisionFittedModel or model.candidate_id != result.selected_candidate_id
                    or candidate is None or model.tuning.identity != candidate.tuning):
                raise ValueError("E4 fitted package substitutes its declared development selection")
            if model is not None:
                model.__post_init__()
            elif result.fit_calls or result.selected_candidate_id is not None:
                raise ValueError("E4 unentered branch cannot invent fitting or recycle its reserved candidates")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.nomination_id, self)


def select_programme_revision(specification, programme, reduction, data, *, nomination_id):
    require_development_selection_phase("DEVELOPMENT" if programme.mode == "E4_DEVELOPMENT" else programme.mode)
    allocation, features, targets, missing = _validate_data(specification, programme, reduction, data)
    return _select_revision(specification, programme, data, allocation, features, targets, missing,
        nomination_id=nomination_id, nomination_type=ScheduledRevisionNomination)


def _select_revision(specification, programme, data, allocation, features, targets, missing, *, nomination_id, nomination_type):
    group_maxima = tuple(max(targets[case.root_id][endpoint] for case in programme.cases
                             if case.independent_group_id == group for endpoint in range(30))
                         for group in programme.group_ids) if not missing else ()
    mean = sum(map(Fraction, group_maxima), Fraction(0))/len(group_maxima) if group_maxima else None
    trigger = specification.trigger
    triggered = mean is not None and (mean > Fraction(trigger.threshold) if trigger.comparison == "GREATER_THAN" else mean >= Fraction(trigger.threshold))
    # A nontriggered branch performs no fitting. Its reserved candidate slots
    # remain explicit unevaluable records, never recycled tuning allowance.
    selections = []
    for suffix, design in (("revision", specification.revision_design), ("baseline", specification.baseline_design)):
        selections.append(_crossfit(specification, design, allocation, programme, features, targets, set(),
            result_id=nomination_id+"."+suffix+"-selection") if triggered else
            unentered_declared_selection(design, allocation, result_id=nomination_id+"."+suffix+"-selection",
                reason="MISSING_COMPLETE_PAIRED_GROUPS" if missing else "INADEQUACY_TRIGGER_NOT_MET"))
    revision, baseline = selections
    models = []
    for selection, design in ((revision, specification.revision_design), (baseline, specification.baseline_design)):
        candidate = next((row for row in design.candidates if row.candidate_id == selection.selected_candidate_id), None)
        tuning = next((row for row in specification.tunings if candidate is not None and row.identity == candidate.tuning), None)
        models.append(None if tuning is None else _fit_bundle(tuning, programme.group_ids, programme, features, targets,
            model_id=nomination_id+"."+candidate.candidate_id+".model", candidate_id=candidate.candidate_id))
    calls = 30*(revision.fit_calls+baseline.fit_calls+2) if triggered else 0
    return nomination_type(nomination_id, specification, data.identity, revision, baseline,
        "UNEVALUABLE" if missing else "TRIGGERED" if triggered else "NOT_TRIGGERED", *models, calls, tuple(sorted(missing)))


@dataclass(frozen=True, slots=True)
class ScheduledRevisionFrozenPackage(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/revision-frozen-package"
    package_id: str
    programme: ObjectIdentity
    nomination: ObjectIdentity
    revision: DeclaredSelectionFreeze | None
    baseline: DeclaredSelectionFreeze | None
    disposition: str

    def __post_init__(self):
        self._validate_operands(programme_schema=ScheduledProgramme.SCHEMA, nomination_schema=ScheduledRevisionNomination.SCHEMA)

    def _validate_operands(self, *, programme_schema, nomination_schema):
        validate_stable_id(self.package_id)
        if (type(self.programme) is not ObjectIdentity or self.programme.object_schema != programme_schema
                or type(self.nomination) is not ObjectIdentity or self.nomination.object_schema != nomination_schema
                or self.disposition not in ("FROZEN_DEVELOPMENT_NOMINATION", "UNENTERED")
                or (self.revision is None) != (self.baseline is None)
                or (self.revision is None) != (self.disposition == "UNENTERED")
                or self.revision is not None and (type(self.revision) is not DeclaredSelectionFreeze
                    or type(self.baseline) is not DeclaredSelectionFreeze)):
            raise ValueError("revision and same-information conventional baseline freeze together or remain unentered")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.package_id, self)


def freeze_programme_revision(programme, nomination, *, freeze_id):
    return _freeze_revision(programme, nomination, freeze_id=freeze_id, package_type=ScheduledRevisionFrozenPackage)


def _freeze_revision(programme, nomination, *, freeze_id, package_type):
    allocation = nomination.specification.validate_programme(programme)
    nomination.__post_init__()
    if nomination.trigger_disposition != "TRIGGERED":
        return package_type(freeze_id, programme.identity, nomination.identity, None, None, "UNENTERED")
    for result, design in ((nomination.revision_selection, nomination.specification.revision_design),
                           (nomination.baseline_selection, nomination.specification.baseline_design)):
        validate_declared_selection_result(design, allocation, result)
    frozen = tuple(freeze_declared_selection(design, allocation, result, fitted_model=model.identity,
        freeze_id=freeze_id+"."+suffix) for suffix, design, result, model in (
            ("revision", nomination.specification.revision_design, nomination.revision_selection, nomination.revision_model),
            ("baseline", nomination.specification.baseline_design, nomination.baseline_selection, nomination.baseline_model)))
    if any(model.training_groups != programme.group_ids for model in (nomination.revision_model, nomination.baseline_model)):
        raise ValueError("frozen revision/baseline drops original whole development groups")
    return package_type(freeze_id, programme.identity, nomination.identity, *frozen, "FROZEN_DEVELOPMENT_NOMINATION")


def require_revision_for_future_phase(programme, nomination, frozen, *, phase, model, target, criterion, features):
    allocation = nomination.specification.validate_programme(programme)
    if type(frozen) is not ScheduledRevisionFrozenPackage or frozen != freeze_programme_revision(programme, nomination, freeze_id=frozen.package_id):
        raise ValueError("future phase requires the actual unchanged joint revision/baseline freeze")
    return require_frozen_selection_for_phase(nomination.specification.revision_design, allocation, nomination.revision_selection,
        frozen.revision, phase=phase, fitted_model=model.identity, target=target, criterion=criterion, features=features)


def selection_node_id(specification, operation):
    if operation not in ("select-revision", "freeze-revision"):
        raise ValueError("unknown bounded E4 selection operation")
    return NAMESPACE+"."+operation+"."+specification.fingerprint()[:24]


@dataclass(frozen=True, slots=True)
class ScheduledRevisionOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/revision-operation-config"
    config_id: str
    operation: str
    programme: ScheduledProgramme
    specification: ScheduledRevisionSpecification
    reduction: ObjectIdentity
    data: ObjectIdentity

    def __post_init__(self):
        if type(self.programme) is not ScheduledProgramme or type(self.specification) is not ScheduledRevisionSpecification:
            raise TypeError("E4 method configuration retains its original complete programme and explicit selection")
        self.specification.validate_programme(self.programme)
        if (self.config_id != "config."+selection_node_id(self.specification, self.operation)
                or type(self.reduction) is not ObjectIdentity or self.reduction.object_schema != ScheduledProgrammeReduction.SCHEMA
                or type(self.data) is not ObjectIdentity or self.data.object_schema != ScheduledRevisionDataBank.SCHEMA):
            raise ValueError("E4 method configuration changes its derived identity or original evidence references")


def selection_development_root(config, *, study_id):
    from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
    from empirical_lawhood.kernel.worlds import WorldKind
    question = "Does the explicitly declared E4 development trigger and finite whole-group selection retain every paired target and adverse group?"
    world = "world.matrix-scheduled-programme.development-selection"
    claim = ClaimSpec("claim."+study_id, world, config.programme.programme_id, question,
        "Complete original32 groups, nine coordinates and paired fifteen-target development selection; separate conventional baseline.",
        "unit.matrix-scheduled-programme.whole-group", None, EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        "This nomination creates no source eligibility, scientific qualification, fresh units or authority.",
        ("assumption.e4.exposed-original-development-records",), numerical_view_ids=("fine", "primary"))
    operands = tuple(sorted((config.programme.identity, config.specification.identity, config.reduction, config.data), key=lambda row: row.object_id))
    return DevelopmentStudySpec(study_id, question, config.programme.identity, world, WorldKind.NUMERICAL_SIMULATOR,
        config.programme.group_ids, ("fine", "primary"), (claim,), operands)



def selection_external_id(specification, name):
    """One source-owned naming rule for the immutable method operands."""
    if name not in ("programme", "specification", "reduction", "data"):
        raise ValueError("unknown E4 declared selection operand")
    return "external."+specification.fingerprint()+"."+name


def selection_connections(config):
    """Exact scientific links shared by the domain lowerer and its validator."""
    names = ("programme", "specification", "reduction", "data") if config.operation == "select-revision" else ("programme", "specification")
    result = {name: (None, None, selection_external_id(config.specification, name), "SOURCE") for name in names}
    if config.operation == "freeze-revision":
        result["nomination"] = (selection_node_id(config.specification, "select-revision"), "product", None, "MODEL")
    return result



@dataclass(frozen=True, slots=True)
class ScheduledRevisionLoweredStudy:
    """Pure exposed lowering; source publication and execution retain their owners."""
    draft: RecursiveStudyDraft
    input_records: tuple[tuple[str, CanonicalRecord], ...]


def lower_exposed_programme_selection(specification, programme, reduction, data, *, campaign):
    """Compose the two declared development methods without fitting or custody I/O.

    This supports an exposed conformance study over an original development
    programme. It does not create the later calibration/confirmation programme,
    genuine issue, a reserved population or a scientific selection warrant.
    """
    from dataclasses import replace
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.planning.campaigns import CampaignSpec
    from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec
    if type(campaign) is not CampaignSpec:
        raise TypeError("E4 exposed lowering needs its existing typed campaign")
    _validate_data(specification, programme, reduction, data)
    configs = tuple(ScheduledRevisionOperationConfig("config."+selection_node_id(specification, operation), operation,
        programme, specification, ObjectIdentity.from_record(reduction.reduction_id, reduction), data.identity)
        for operation in ("select-revision", "freeze-revision"))
    declarations = {row.capability_key.rsplit(".", 1)[-1]: row for row in operation_declarations()}
    operations, links = [], []
    for config in configs:
        node = selection_node_id(specification, config.operation)
        declaration = declarations[config.operation]
        operations.append(RecursiveOperationSpec.from_config(node_id=node, selection=declaration.registration().selection,
            config_id=config.config_id, config=config, obligation_ids=("obligation."+node+".complete-selection",),
            resource_budget=declaration.resources))
        for name, (producer, output, external, role) in selection_connections(config).items():
            links.append(RecursiveInputLink("edge."+node+"."+name, node, name, producer, output, external, role))
    records = tuple(sorted((selection_external_id(specification, name), record) for name, record in (
        ("programme", programme), ("specification", specification), ("reduction", reduction), ("data", data))))
    external = tuple(RecursiveExternalInput(input_id, "input."+input_id, record.SCHEMA, "application/json",
        len(record.canonical_bytes()), OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, record.fingerprint())
        for input_id, record in records)
    root = selection_development_root(configs[0], study_id="study.e4.exposed-selection."+specification.fingerprint())
    selected_campaign = replace(campaign, objective=root.question, system_ids=(root.system.object_id,), world_ids=(root.world_id,),
        target_claim_ids=tuple(row.claim_id for row in root.claims))
    draft = RecursiveStudyDraft("draft.e4.exposed-selection."+specification.fingerprint(), root.question, selected_campaign,
        (), (), (), tuple(sorted(operations, key=lambda row: row.node_id)), external,
        tuple(sorted(links, key=lambda row: row.edge_id)), tuple(sorted(row.node_id for row in operations)), development_study=root)
    return ScheduledRevisionLoweredStudy(draft, records)


def scientific_root_validator(config, context):
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
    from empirical_lawhood.planning.study_authoring import StudyDraft
    from empirical_lawhood.runtime.plans import ScientificStage
    node = selection_node_id(config.specification, config.operation)
    stage = ScientificStage.DEVELOP if config.operation == "select-revision" else ScientificStage.FREEZE
    if (context.node_id != node or context.stage is not stage or context.unit_ids != config.programme.group_ids
            or context.selected_unit_ids != config.programme.group_ids or context.complete_unit_census
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise ValueError("E4 selection changes its exact development stage, original groups or access")
    if type(context.root) is DevelopmentStudySpec:
        if context.root != selection_development_root(config, study_id=context.root.study_id):
            raise ValueError("E4 selection substitutes its exposed original-data scientific root")
    elif type(context.root) is StudyDraft:
        from .programme_global import validate_programme_root
        validate_programme_root(config.programme, context)
        if not {config.specification.identity, config.reduction, config.data} <= {row.object_identity for row in context.root.design_inputs}:
            raise ValueError("E4 selection root omits its exact original method/evidence inputs")
    else:
        raise ValueError("E4 selection lacks its actual original development scientific root")
    matched = tuple(row.record for row in context.config_inputs if type(row.record) is ScheduledRevisionOperationConfig
                    and row.record.specification == config.specification)
    if (len(matched) != 2 or {row.operation for row in matched} != {"select-revision", "freeze-revision"}
            or any((row.programme, row.reduction, row.data) != (config.programme, config.reduction, config.data) for row in matched)):
        raise ValueError("E4 selection requires its single original development fit and independent freeze")
    incoming = tuple(row for row in context.links if row.consumer_node_id == node)
    expected = selection_connections(config)
    actual = {row.consumer_input_id: (row.producer_node_id, row.producer_output_id, row.external_input_id, row.scientific_role)
              for row in incoming}
    if len(incoming) != len(expected) or actual != expected:
        raise ValueError("E4 selection changes exact original source links or bypasses its actual selection-to-freeze dependency")



class ScheduledRevisionWorker:
    def __init__(self, operation, manifest=None):
        self.operation = operation
        self.manifest = manifest or next(row.manifest() for row in operation_declarations() if row.capability_key.endswith("."+operation))

    def _inputs(self, context):
        from empirical_lawhood.kernel.decoding import decode_canonical_bytes
        from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
        from empirical_lawhood.runtime.execution import WorkerInputKind
        kinds = (ScheduledRevisionOperationConfig, ScheduledProgramme, ScheduledRevisionSpecification,
            *((ScheduledProgrammeReduction, ScheduledRevisionDataBank) if self.operation == "select-revision" else (ScheduledRevisionNomination,)))
        by_schema = {kind.SCHEMA: kind for kind in kinds}
        if (context.permissions != self.manifest.permissions or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or len(context.input_ports) != len(kinds) or not self.manifest.resource_ceiling.contains(context.resource_budget)):
            raise ValueError("E4 method changes original input census, resource budget or development access")
        records = {}
        for port in context.input_ports:
            kind = by_schema.get(port.payload_schema)
            if (kind is None or kind in records or port.media_type != "application/json"
                    or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                    or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
                raise ValueError("E4 method receives duplicate, protected or undeclared input records")
            cursor = port.cursor()
            try:
                raw = cursor.read()
            finally:
                cursor.close()
            if len(raw) != port.size_bytes:
                raise ValueError("E4 method changes original complete materialized record bytes")
            records[kind] = decode_canonical_bytes(raw, kind, maximum_bytes=None)
            if kind is ScheduledRevisionOperationConfig and (port.kind is not WorkerInputKind.EXTERNAL
                    or port.artifact_id != context.config.artifact_id):
                raise ValueError("E4 method changes its complete original external configuration")
        config = records[ScheduledRevisionOperationConfig]
        if (config.operation != self.operation or context.task_id != selection_node_id(config.specification, self.operation)
                or context.config.config_id != config.config_id or context.config.config_schema != config.SCHEMA
                or context.config.content_sha256 != config.fingerprint()
                or records[ScheduledProgramme] != config.programme or records[ScheduledRevisionSpecification] != config.specification):
            raise ValueError("E4 method substitutes original config/programme/specification bindings")
        if self.operation == "select-revision":
            reduction, bank = records[ScheduledProgrammeReduction], records[ScheduledRevisionDataBank]
            if ObjectIdentity.from_record(reduction.reduction_id, reduction) != config.reduction or bank.identity != config.data:
                raise ValueError("E4 method substitutes original development evidence bytes")
            _validate_data(config.specification, config.programme, reduction, bank)
        else:
            nomination = records[ScheduledRevisionNomination]
            if nomination.specification != config.specification or nomination.data != config.data:
                raise ValueError("E4 freeze substitutes its actual original development nomination")
        return config, records

    def preflight(self, context):
        self._inputs(context)

    def execute(self, context):
        from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
        from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload
        config, records = self._inputs(context)
        node = selection_node_id(config.specification, self.operation)
        if self.operation == "select-revision":
            product = select_programme_revision(config.specification, config.programme, records[ScheduledProgrammeReduction],
                records[ScheduledRevisionDataBank], nomination_id="nomination."+config.specification.specification_id)
        else:
            product = freeze_programme_revision(config.programme, records[ScheduledRevisionNomination],
                freeze_id="frozen."+config.specification.specification_id)
        if (len(context.output_ports) != 1 or context.output_ports[0].output_id != node+".product"
                or context.output_ports[0].payload_schema != product.SCHEMA
                or context.output_ports[0].profile is not ArtifactProfile.CANONICAL_JSON
                or context.output_ports[0].media_type != "application/json"):
            raise ValueError("E4 method changes its exact original output contract")
        return RunnerResult((TaskOutputPayload(node+".product", product.canonical_bytes()),),
            (ReceiptCheck("e4-declared-whole-group-development-selection", True, ()),))


def operation_declarations():
    from functools import partial
    from empirical_lawhood.kernel.authority import ResourceBudget
    from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.runtime.artifacts import ArtifactProfile
    from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
    from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
    from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
    from empirical_lawhood.runtime.recursive_provider import RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks
    from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
    common = (("programme", ScheduledProgramme), ("specification", ScheduledRevisionSpecification))
    phases = (("select-revision", (*common, ("reduction", ScheduledProgrammeReduction), ("data", ScheduledRevisionDataBank)),
               ScheduledRevisionNomination, ScientificStage.DEVELOP),
              ("freeze-revision", (*common, ("nomination", ScheduledRevisionNomination)), ScheduledRevisionFrozenPackage, ScientificStage.FREEZE))
    kinds = {ScheduledRevisionOperationConfig, *(kind for _, inputs, output, _ in phases for kind in (*[kind for _, kind in inputs], output))}
    codecs = {kind.SCHEMA: kind for kind in kinds}
    return tuple(RecursiveOperationDeclaration(
        capability_key=NAMESPACE+"."+operation, capability_version="1.0.0",
        implementation_id="explicit-paired-original-e4-physical-grid-"+operation+"-v1",
        kind=CapabilityKind.ANALYSIS, config_record_type=ScheduledRevisionOperationConfig, stage=stage,
        input_ports=tuple(sorted((RecursivePortContract(name, kind.SCHEMA, "application/json", None) for name, kind in inputs), key=lambda port: port.port_id)),
        outputs=(OutputTemplate("product", output.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),),
        permissions=tuple(sorted((CapabilityPermission.READ_DEVELOPMENT, CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS))), evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
        resources=ResourceBudget(1, None, 0, None, None, None),
        conformance_check_ids=("complete-original-paired-whole-group-development", "finite-declared-fold-budget-and-trigger",
            "one-model-and-baseline-freeze-before-future"), runner_factory=partial(ScheduledRevisionWorker, operation),
        record_codecs=codecs, input_record_types=tuple(sorted((kind for _, kind in inputs), key=lambda kind: (kind.SCHEMA, kind.VERSION))),
        scientific_hooks=RecursiveScientificHooks(scientific_unit_ids=lambda config: config.programme.group_ids,
            scientific_root_validator=scientific_root_validator),
        execution_properties=RecursiveExecutionProperties(barrier=BarrierKind.FREEZE if operation == "freeze-revision" else BarrierKind.NONE),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,)) for operation, inputs, output, stage in phases)


def operation_factories():
    return tuple(row.provider_factory() for row in operation_declarations())


def operation_manifests():
    return tuple(row.manifest() for row in operation_declarations())
