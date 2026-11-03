# SPDX-License-Identifier: MPL-2.0
"""Declared selected E4 fitting, calibration and complete conditional decisions.

Scientific parameters are explicit input records. Mathematical bodies are shared
with their original owners, while distinct selected schemas retain true source
and programme identities. Pure calculations create no authority or applicability.
"""

from dataclasses import dataclass
from empirical_lawhood.adapters.methods.matrix_primary_family import validate_declared_primary_family
from empirical_lawhood.adapters.methods.matrix_primary_family import AMENDED_PRIMARY_FAMILY
from decimal import Decimal
from fractions import Fraction
from itertools import combinations
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_methods import METHODS
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.experimental_selection import (
    DeclaredCandidate, DeclaredSelectionDesign, DeclaredSelectionResult, DeclaredSelectionFreeze, WholeUnitFold,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.runtime.experimental_statistics import PairedMeanTAlternative, AssignedBinomialInference
from empirical_lawhood.runtime.experimental_selection import require_frozen_selection_for_phase, validate_selection_design

from . import programme_factorial as factorial, programme_selection as selection
from . import programme_workflow as workflow, revision_calibration as calibration_owner
from . import selected_e3_e4_records as r, selected_e4_programme as p
from .records import matched_key
from .selection_specification import ScheduledRevisionExperimentSpecification
from . import e4_structural_prediction as relation
from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_fitting import MatchedEstimatorModel, MatchedCurveEstimatorModel, MatchedTrainingRow
from empirical_lawhood.adapters.methods.matrix_factor_response.curve_prediction import MatchedCurveDecision, reported_loss
from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_prediction import (
    MatchedModelCalibration, MATCHED_METHODS, matched_duration_error_count,
)


def _matched_folds(folds):
    if (type(folds) is not tuple or not folds or any(type(row) is not WholeUnitFold for row in folds)
            or tuple(row.unit_id for row in folds) != tuple(sorted({row.unit_id for row in folds}))
            or {row.fold for row in folds} != {0, 1}):
        raise ValueError('matched E4 fitting requires its complete fixed two-fold whole-group assignment')
    for row in folds:
        row.__post_init__()


@dataclass(frozen=True, slots=True)
class SelectedE4FeatureDefinition(selection.ScheduledRevisionFeatureDefinition):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/feature-definition"

    def __post_init__(self):
        validate_stable_id(self.feature_id)
        r.exact_pin(self.programme, r.SelectedE3E4DevelopmentProgramme)
        if (self.feature_names != selection.FEATURES
                or self.rule != "COMMITTED_PHYSICAL_VALUES_SIGNED_GRID_PAIRS_ONE_CENTER_INDICATOR"):
            raise ValueError("selected E4 cannot invent non-grid features or separately identifiable quadratic terms")


def feature_definition(programme):
    return SelectedE4FeatureDefinition("features." + programme.programme_id, programme.identity, selection.FEATURES,
        "COMMITTED_PHYSICAL_VALUES_SIGNED_GRID_PAIRS_ONE_CENTER_INDICATOR")


def selection_allocation(programme):
    if type(programme) is not r.SelectedE3E4DevelopmentProgramme:
        raise TypeError("selected E4 fitting consumes the actual truthful development programme")
    programme.__post_init__()
    return UnitAllocation("selection-allocation." + programme.programme_id, (programme.identity,),
        tuple(IndependentUnit(group, programme.programme_id,
            next(case.family_id for case in programme.cases if case.independent_group_id == group), ("fine", "primary"), True)
            for group in programme.group_ids),
        tuple(UnitRoleAssignment(group, "development") for group in programme.group_ids))


@dataclass(frozen=True, slots=True)
class SelectedE4RevisionSpecification(selection.ScheduledRevisionSpecification):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/revision-specification"
    VERSION: ClassVar[str] = '2.0.0'
    target: selection.ScheduledRevisionTarget | relation.E4MatchedRelationTarget
    trigger: selection.ScheduledRevisionTrigger | None
    revision_design: DeclaredSelectionDesign | None
    baseline_design: DeclaredSelectionDesign | None
    matched_selection: relation.E4MatchedRelationSelection | None = None
    matched_folds: tuple[WholeUnitFold, ...] = ()

    def __post_init__(self):
        if self.matched_selection is not None:
            validate_stable_id(self.specification_id)
            r.exact_pin(self.programme, r.SelectedE3E4DevelopmentProgramme)
            if (type(self.target) is not relation.E4MatchedRelationTarget
                    or type(self.matched_selection) is not relation.E4MatchedRelationSelection
                    or self.trigger is not None or self.revision_design is not None or self.baseline_design is not None or self.tunings):
                raise ValueError('matched E4 selection cannot acquire a trigger, alternate candidate search or legacy target')
            self.target.__post_init__()
            self.matched_selection.__post_init__()
            _matched_folds(self.matched_folds)
            return
        if self.matched_folds:
            raise ValueError('closed E4 selection cannot acquire unmatched relation folds')
        self._validate_operands(programme_schema=r.SelectedE3E4DevelopmentProgramme.SCHEMA)

    def validate_programme(self, programme):
        self.__post_init__()
        allocation = selection_allocation(programme)
        if self.programme != programme.identity or self.target.criterion != programme.criterion:
            raise ValueError("selected E4 selection changes actual development programme or target")
        if self.matched_selection is not None:
            relation.validate_relation_geometry(self.matched_selection, programme)
            if tuple(row.unit_id for row in self.matched_folds) != programme.group_ids:
                raise ValueError('matched E4 selection drops original assigned DEV groups')
            return allocation
        for design in (self.revision_design, self.baseline_design):
            validate_selection_design(design, allocation)
            if design.features != feature_definition(programme).identity:
                raise ValueError("selected E4 selection changes frozen pre-cutoff physical features")
        return allocation


@dataclass(frozen=True, slots=True)
class SelectedE4RevisionExperimentSpecification(ScheduledRevisionExperimentSpecification):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/revision-experiment-specification"
    VERSION: ClassVar[str] = '2.0.0'
    target: selection.ScheduledRevisionTarget | relation.E4MatchedRelationTarget
    trigger: selection.ScheduledRevisionTrigger | None
    matched_selection: relation.E4MatchedRelationSelection | None = None

    def __post_init__(self):
        if self.matched_selection is not None:
            validate_stable_id(self.specification_id)
            r.exact_pin(self.programme, r.SelectedE3E4DevelopmentProgramme)
            if (type(self.target) is not relation.E4MatchedRelationTarget
                    or type(self.matched_selection) is not relation.E4MatchedRelationSelection
                    or self.trigger is not None or self.fold_count != 2 or self.maximum_fit_calls != 5
                    or type(self.fold_count) is not int or type(self.maximum_fit_calls) is not int
                    or any((self.revision_candidates, self.baseline_candidates, self.revision_tie_order, self.baseline_tie_order))):
                raise ValueError('matched E4 declaration changes the fixed SR/BR procedure or adds an outcome trigger')
            self.target.__post_init__()
            self.matched_selection.__post_init__()
            _matched_folds(self.folds)
            return
        self._validate_operands(programme_schema=r.SelectedE3E4DevelopmentProgramme.SCHEMA)


def derive_revision_specification(specification, programme):
    if type(specification) is not SelectedE4RevisionExperimentSpecification:
        raise TypeError("selected E4 fitting needs its explicit editable scientific declaration")
    specification.__post_init__()
    allocation = selection_allocation(programme)
    if specification.programme != programme.identity or specification.target.criterion != programme.criterion:
        raise ValueError("selected revision declaration changes its actual source programme or target")
    if specification.matched_selection is not None:
        result = SelectedE4RevisionSpecification('selection.' + specification.fingerprint(), programme.identity,
            specification.target, None, None, None, (), specification.matched_selection, specification.folds)
        result.validate_programme(programme)
        return result
    designs, tunings = [], {}
    for suffix, candidates, ties in (("revision", specification.revision_candidates, specification.revision_tie_order),
            ("baseline", specification.baseline_candidates, specification.baseline_tie_order)):
        for row in candidates:
            tunings[row.tuning.tuning_id] = row.tuning
        designs.append(DeclaredSelectionDesign("design." + specification.fingerprint() + "." + suffix,
            allocation.identity, "development",
            tuple(DeclaredCandidate(row.candidate_id, row.tuning.family_id, row.tuning.identity) for row in candidates),
            specification.folds, specification.fold_count, specification.maximum_fit_calls, ties,
            "MINIMIZE", "REQUIRE_COMPLETE", specification.target.identity, specification.target.criterion,
            feature_definition(programme).identity))
    result = SelectedE4RevisionSpecification("selection." + specification.fingerprint(), programme.identity,
        specification.target, specification.trigger, *designs, tuple(tunings[key] for key in sorted(tunings)))
    result.validate_programme(programme)
    return result


def validate_observed_data(programme, bank, reduction, data, target, *, allow_absent):
    """Rejoin all original source/cutoff/score records; missing keeps its group."""
    if type(programme) is r.SelectedE3E4DevelopmentProgramme:
        r.validate_development_bank(programme, bank)
        reduction_schema = r.SelectedE3E4DevelopmentReduction.SCHEMA
    else:
        p.validate_selected_phase_bank(programme, bank)
        reduction_schema = p.NATIVE_REDUCTION_SCHEMA
    matched = getattr(bank.forecast_design.package.specification.measurement, 'is_matched', False)
    target_count = 58 if matched else 30
    if (type(target) is not (relation.E4MatchedRelationTarget if matched else selection.ScheduledRevisionTarget)
            or target.criterion != programme.criterion
            or target.horizon_ticks != bank.forecast_design.package.specification.measurement.horizons):
        raise ValueError("selected E4 observed data changes the declared response target")
    target.__post_init__()
    if (type(data) is not p.SelectedE4ObservedData or data.programme != programme.identity
            or data.reduction != p._record_pin(reduction) or data.reduction.object_schema != reduction_schema
            or reduction.programme != programme.identity or reduction.bank != bank.identity
            or tuple(value.root_id for value in reduction.cases) != tuple(value.root_id for value in programme.cases)):
        raise ValueError("selected E4 observed data substitutes actual complete reducer/source products")
    data.__post_init__()
    reduction.__post_init__()
    by_root, missing, targets = {case.root_id: case for case in data.cases}, set(), {}
    declared = tuple(case.root_id for case in programme.cases)
    actual = tuple(case.root_id for case in data.cases)
    if set(actual) - set(declared) or not allow_absent and actual != declared:
        raise ValueError("selected E4 observed data changes assigned case census")
    index=bank.source_index()
    for case, result in zip(programme.cases, reduction.cases, strict=True):
        row = by_root.get(case.root_id)
        if row is None:
            targets[case.root_id] = (None,) * target_count
            missing.add(case.independent_group_id)
            continue
        source = bank.source(case.root_id,index=index)
        bank.response_selection.validate_source(source)
        if (r.pin(row.coordinate, "coordinate_id") != case.coordinate or row.source != case.source
                or row.group_id != case.independent_group_id or row.coordinate != source.coordinate
                or (row.disposition, row.numerical_disposition, row.forecast, row.original_log_points) !=
                (result.disposition, result.numerical_disposition, result.forecast, result.original_log_points)
                or row.revision_forecast != getattr(result, "revision_forecast", None)
                or row.target_contract != ('MATCHED_FACTOR58' if matched else 'PAIRED15')
                or row.target_contract != result.target_contract
                or matched and hasattr(result, 'causal_feature') and row.causal_feature != result.causal_feature):
            raise ValueError("selected E4 observation changes source/coordinate/group or actual reducer results")
        prefix, score = row.causal_prefix, row.score
        if prefix is not None and (prefix.source != case.source or prefix.root != source.root.root
                or source.coordinate.physical_time(prefix.cutoff_tick) != case.information_cutoff.coordinate
                or prefix.cutoff_tick != source.policy.cutoff_tick):
            raise ValueError("selected E4 observation changes the actual causal prefix or physical cutoff")
        if score is not None and (score.original != result.score or score.source != case.source
                or score.root_id != case.root_id or score.independent_group_id != case.independent_group_id
                or score.role != case.role or score.criterion != target.criterion
                or prefix is None or score.causal_prefix != prefix.original
                or score.error_forecast != row.forecast):
            raise ValueError("selected E4 target substitutes original paired score or forecast-before-response lineage")
        values = (None,) * target_count if score is None else score.paired_log_targets
        if hasattr(result, "paired_log_targets") and values != result.paired_log_targets:
            raise ValueError("selected E4 paired targets differ from their actual full original reduction")
        targets[case.root_id] = values
        if (prefix is None or prefix.disposition != "AVAILABLE" or result.disposition != "COMPLETED"
                or result.numerical_disposition != "SATISFIED" or any(value is None for value in values)):
            missing.add(case.independent_group_id)
    return targets, frozenset(missing)


@dataclass(frozen=True, slots=True)
class SelectedE4RevisionNomination(selection.ScheduledRevisionNomination):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/revision-nomination"
    VERSION: ClassVar[str] = '2.0.0'
    specification: SelectedE4RevisionSpecification
    revision_selection: DeclaredSelectionResult | None
    baseline_selection: DeclaredSelectionResult | None
    revision_model: selection.ScheduledRevisionFittedModel | MatchedEstimatorModel | MatchedCurveEstimatorModel | None
    baseline_model: selection.ScheduledRevisionFittedModel | MatchedEstimatorModel | MatchedCurveEstimatorModel | None
    relation_fit: relation.E4MatchedRelationFit | None = None

    def __post_init__(self):
        if self.relation_fit is not None:
            validate_stable_id(self.nomination_id)
            if (type(self.specification) is not SelectedE4RevisionSpecification
                    or type(self.relation_fit) is not relation.E4MatchedRelationFit
                    or self.revision_selection is not None or self.baseline_selection is not None
                    or self.standing != selection.STANDING):
                raise ValueError('matched E4 fit substitutes its fixed procedure or development standing')
            self.specification.__post_init__()
            self.relation_fit.__post_init__()
            r.exact_pin(self.data, p.SelectedE4ObservedData)
            fitted = self.relation_fit
            models = {row.method_key: row for row in fitted.models}
            available = all(models[name].parameters is not None for name in ('SR', 'BR'))
            expected = (models['SR'], models['BR']) if available else (None, None)
            if ((fitted.selection, fitted.development) != (self.specification.matched_selection, self.specification.programme)
                    or fitted.models[0].folds != tuple((row.unit_id, row.fold) for row in self.specification.matched_folds)
                    or self.trigger_disposition != ('FIT_AVAILABLE' if available else 'FIT_UNAVAILABLE')
                    or (self.revision_model, self.baseline_model) != expected
                    or type(self.endpoint_fit_calls) is not int
                    or self.endpoint_fit_calls != 58 * sum(len(model.fit_attempts) for model in fitted.models)
                    or self.missing_groups != tuple(group for group, _ in fitted.models[0].exclusions)):
                raise ValueError('matched E4 fit hides missing groups, changes its attempted fits or selects an account after outcomes')
            return
        if self.specification.matched_selection is not None:
            raise ValueError('matched E4 fitting omits its complete relation fit and prerequisite result')
        self._validate_operands(specification_type=SelectedE4RevisionSpecification, data_schema=p.SelectedE4ObservedData.SCHEMA)


def select_revision(specification, programme, bank, reduction, data, *, nomination_id):
    if type(specification) is not SelectedE4RevisionSpecification:
        raise TypeError("selected E4 fitting requires its actual derived scientific specification")
    allocation = specification.validate_programme(programme)
    targets, missing = validate_observed_data(programme, bank, reduction, data, specification.target, allow_absent=False)
    if specification.matched_selection is not None:
        rows, originals = [], []
        for case, observed in zip(programme.cases, data.cases, strict=True):
            feature = observed.causal_feature
            disposition = 'UNAVAILABLE' if feature is None else feature.disposition
            values = relation.relation_feature_values(specification.matched_selection,
                () if feature is None else feature.values, disposition, factor_values=case.factor_values, family_id=case.family_id)
            reasons = set()
            if disposition != 'AVAILABLE':
                reasons.add('CAUSAL_FEATURE_' + disposition)
            if observed.disposition != 'COMPLETED':
                reasons.add('ORIGINAL_CASE_' + observed.disposition)
            if observed.numerical_disposition != 'SATISFIED':
                reasons.add('ORIGINAL_NUMERICAL_' + observed.numerical_disposition)
            errors = (None,) * 58 if observed.score is None else observed.score.paired_errors
            if any(value is None for value in errors):
                reasons.add('INCOMPLETE_PAIRED_TARGET')
            rows.append(MatchedTrainingRow(case.root_id, case.independent_group_id, case.family_id, values, errors, tuple(sorted(reasons))))
            originals.append(ObjectIdentity.from_record(observed.root_id, observed))
        fitted = relation.fit_relation_values(specification.matched_selection, programme.identity, tuple(rows), tuple(originals),
            assigned_groups=programme.group_ids, folds=tuple((row.unit_id, row.fold) for row in specification.matched_folds),
            record_id='relation.' + nomination_id)
        models = {row.method_key: row for row in fitted.models}
        available = all(models[name].parameters is not None for name in ('SR', 'BR'))
        return SelectedE4RevisionNomination(nomination_id, specification, data.identity, None, None,
            'FIT_AVAILABLE' if available else 'FIT_UNAVAILABLE', models['SR'] if available else None, models['BR'] if available else None,
            58 * sum(len(model.fit_attempts) for model in fitted.models), tuple(group for group, _ in fitted.models[0].exclusions),
            relation_fit=fitted)
    features = {case.root_id: selection.revision_case_features(programme, case) for case in programme.cases}
    return selection._select_revision(specification, programme, data, allocation, features, targets, missing,
        nomination_id=nomination_id, nomination_type=SelectedE4RevisionNomination)


@dataclass(frozen=True, slots=True)
class SelectedE4FrozenRevision(selection.ScheduledRevisionFrozenPackage):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/frozen-revision"
    VERSION: ClassVar[str] = '2.0.0'
    revision: DeclaredSelectionFreeze | None
    baseline: DeclaredSelectionFreeze | None
    relation_fit: ObjectIdentity | None = None

    def __post_init__(self):
        if self.relation_fit is not None:
            validate_stable_id(self.package_id)
            r.exact_pin(self.programme, r.SelectedE3E4DevelopmentProgramme)
            r.exact_pin(self.nomination, SelectedE4RevisionNomination)
            r.exact_pin(self.relation_fit, relation.E4MatchedRelationFit)
            if (self.revision is not None or self.baseline is not None
                    or self.disposition not in ('FROZEN_MATCHED_RELATION', 'UNCONSTRUCTIBLE_MATCHED_RELATION')):
                raise ValueError('matched E4 freeze changes its complete DEV result or invents a legacy selection freeze')
            return
        self._validate_operands(programme_schema=r.SelectedE3E4DevelopmentProgramme.SCHEMA,
            nomination_schema=SelectedE4RevisionNomination.SCHEMA)


def freeze_revision(programme, nomination, *, freeze_id):
    if type(nomination) is not SelectedE4RevisionNomination:
        raise TypeError("selected E4 freeze cannot substitute a legacy or undeclared nomination")
    if nomination.relation_fit is not None:
        nomination.__post_init__()
        nomination.specification.validate_programme(programme)
        return SelectedE4FrozenRevision(freeze_id, programme.identity, nomination.identity, None, None,
            'FROZEN_MATCHED_RELATION' if nomination.trigger_disposition == 'FIT_AVAILABLE' else 'UNCONSTRUCTIBLE_MATCHED_RELATION',
            nomination.relation_fit.identity)
    return selection._freeze_revision(programme, nomination, freeze_id=freeze_id, package_type=SelectedE4FrozenRevision)


def validate_frozen_revision(development, nomination, frozen):
    if (type(frozen) is not SelectedE4FrozenRevision or frozen != freeze_revision(
            development, nomination, freeze_id=frozen.package_id)):
        raise ValueError("selected E4 future use substitutes actual original joint DEV freeze")


def validate_revision_phase(development, nomination, frozen, programme, *, phase):
    p.validate_phase_separation(development, programme)
    if programme.mode != p.PHASES.get(phase, (None,))[0]:
        raise ValueError("selected E4 future use changes its declared CAL or CONF phase")
    validate_frozen_revision(development, nomination, frozen)
    if nomination.relation_fit is not None:
        if nomination.trigger_disposition != 'FIT_AVAILABLE':
            raise ValueError('matched E4 future phase lacks a constructible required SR/BR pair')
        return
    if nomination.trigger_disposition != "TRIGGERED":
        raise ValueError("untriggered selected revision leaves its calibration and fitted forecasts unentered")
    allocation = nomination.specification.validate_programme(development)
    for design, result, seal, model in ((nomination.specification.revision_design, nomination.revision_selection,
            frozen.revision, nomination.revision_model), (nomination.specification.baseline_design,
            nomination.baseline_selection, frozen.baseline, nomination.baseline_model)):
        require_frozen_selection_for_phase(design, allocation, result, seal, phase=phase,
            fitted_model=model.identity, target=nomination.specification.target.identity,
            criterion=nomination.specification.target.criterion, features=design.features)


def forecast_revision_cases(development, nomination, frozen, programme, *, record_prefix):
    phase = "CALIBRATION" if programme.mode == "E4_REVISION_CALIBRATION" else "CONFIRMATION"
    validate_revision_phase(development, nomination, frozen, programme, phase=phase)
    models = p.SelectedE4PublicModels.from_products(development, nomination, frozen, record_id="public." + frozen.package_id)
    return tuple(models.forecast(programme, case, record_id=record_prefix + "." + case.root_id) for case in programme.cases)


@dataclass(frozen=True, slots=True)
class SelectedE4Calibration(calibration_owner.ScheduledRevisionCalibration):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/calibration"
    VERSION: ClassVar[str] = '2.0.0'
    specification: p.SelectedE4CalibrationSpecification
    revision_model: selection.ScheduledRevisionFittedModel | MatchedEstimatorModel | MatchedCurveEstimatorModel
    baseline_model: selection.ScheduledRevisionFittedModel | MatchedEstimatorModel | MatchedCurveEstimatorModel
    forecasts: tuple[ObjectIdentity | None, ...]
    relation_fit: ObjectIdentity | None = None
    model_calibrations: tuple[MatchedModelCalibration, ...] = ()

    def __post_init__(self):
        if self.relation_fit is not None:
            validate_stable_id(self.record_id)
            r.exact_pin(self.relation_fit, relation.E4MatchedRelationFit)
            r.exact_pin(self.target, relation.E4MatchedRelationTarget)
            r.exact_pin(self.data, p.SelectedE4ObservedData)
            if (type(self.specification) is not p.SelectedE4CalibrationSpecification
                    or self.specification.score_rule != relation.RELATION_SCORE_RULE
                    or type(self.revision_model) not in (MatchedEstimatorModel, MatchedCurveEstimatorModel) or self.revision_model.method_key != 'SR'
                    or type(self.baseline_model) is not type(self.revision_model) or self.baseline_model.method_key != 'BR'
                    or any(model.parameters is None for model in (self.revision_model, self.baseline_model))
                    or type(self.group_ids) is not tuple or not self.group_ids or self.group_ids != tuple(sorted(set(self.group_ids)))
                    or self.revision_model.training_unit_ids != self.baseline_model.training_unit_ids
                    or set(self.group_ids) & set(self.revision_model.training_unit_ids)
                    or type(self.forecasts) is not tuple or len(self.forecasts) != 9 * len(self.group_ids)
                    or len({value for value in self.forecasts if value is not None}) != sum(value is not None for value in self.forecasts)
                    or type(self.model_calibrations) is not tuple
                    or tuple(row.method_key for row in self.model_calibrations) != ('BR', 'SR')):
                raise ValueError('matched E4 calibration drops assigned groups, genuine forecasts or the original SR/BR pair')
            for record in (self.specification, self.revision_model, self.baseline_model, *self.model_calibrations):
                record.__post_init__()
            for value in self.forecasts:
                if value is not None:
                    r.exact_pin(value, p.SelectedE4ForecastSeal)
            by_method = {row.method_key: row for row in self.model_calibrations}
            for method, scores, radius in (('SR', self.revision_scores, self.revision_radius), ('BR', self.baseline_scores, self.baseline_radius)):
                row = by_method[method]
                if (tuple(group for group, _, _ in row.scores) != self.group_ids
                        or scores != tuple((group, value) for group, value, _ in row.scores)
                        or self.rank != row.rank or radius != row.radius):
                    raise ValueError('matched E4 calibration changes its complete rank or separate positive-residual radius')
            return
        if self.model_calibrations or self.specification.score_rule == relation.RELATION_SCORE_RULE:
            raise ValueError('matched E4 calibration omits its original fit or separate model scores')
        self._validate_operands(specification_type=p.SelectedE4CalibrationSpecification,
            data_schema=p.SelectedE4ObservedData.SCHEMA, forecast_schema=p.SelectedE4ForecastSeal.SCHEMA,
            group_count=len(self.group_ids), data_version=p.SelectedE4ObservedData.VERSION,
            forecast_version=p.SelectedE4ForecastSeal.VERSION)
        if not self.group_ids:
            raise ValueError("selected E4 calibration retains a nonempty declared calibration population")


def validate_forecasts(development, nomination, frozen, programme, data, forecasts):
    models = p.SelectedE4PublicModels.from_products(development, nomination, frozen, record_id="public." + frozen.package_id)
    if type(forecasts) is not tuple or tuple(seal.case_id for seal in forecasts) != tuple(case.root_id for case in programme.cases):
        raise ValueError("selected E4 future use omits a frozen pre-outcome forecast")
    rows = {row.root_id: row for row in data.cases}
    for case, seal in zip(programme.cases, forecasts, strict=True):
        if (type(seal) is not p.SelectedE4ForecastSeal
                or seal != models.forecast(programme, case, record_id=seal.record_id)
                or case.root_id in rows and rows[case.root_id].revision_forecast != seal.identity):
            raise ValueError("selected E4 future data changes original frozen predictions or pre-future seal dependency")


def calibrate_revision(specification, development, nomination, frozen, programme, bank, reduction, data, forecasts, *, record_id):
    validate_revision_phase(development, nomination, frozen, programme, phase="CALIBRATION")
    if nomination.relation_fit is not None:
        export = p.SelectedE4RevisionExport.from_products(development, nomination, frozen, record_id='export.' + frozen.package_id)
        return calibrate_revision_public(specification, export, programme, bank, reduction, data,
            p.SelectedE4ForecastBank('forecasts.' + programme.programme_id, programme.identity, forecasts), record_id=record_id)
    if (type(specification) is not p.SelectedE4CalibrationSpecification
            or (specification.development_programme, specification.calibration_programme, specification.nomination, specification.frozen_models) !=
            (development.identity, programme.identity, nomination.identity, frozen.identity)
            or Fraction(specification.alpha) != 1 - Fraction(programme.confidence)):
        raise ValueError("selected E4 calibration changes actual frozen models, complete population or declared alpha")
    specification.__post_init__()
    targets, missing = validate_observed_data(programme, bank, reduction, data, nomination.specification.target, allow_absent=True)
    validate_forecasts(development, nomination, frozen, programme, data, forecasts)
    return calibration_owner.calibration_from_targets(specification, nomination.specification.target.identity,
        nomination.revision_model, nomination.baseline_model, programme, data, forecasts, targets, missing,
        record_id=record_id, record_type=SelectedE4Calibration)


@dataclass(frozen=True, slots=True)
class SelectedE4FactorialSpecification(factorial.ScheduledFactorialSpecification):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/factorial-specification"
    VERSION: ClassVar[str] = "3.0.0"
    target: selection.ScheduledRevisionTarget | relation.E4MatchedRelationTarget
    alpha: Decimal | None
    sampling_requirement: factorial.ScientificRequirementSpec | None
    family_ids: tuple[str, ...]

    def __post_init__(self):
        if type(self.programme) is not ObjectIdentity or self.programme.object_schema not in (
                r.SelectedE3E4DevelopmentProgramme.SCHEMA, p.SelectedE4PhaseProgramme.SCHEMA):
            raise ValueError("selected factorial declaration changes its actual assigned programme")
        if type(self.target) is relation.E4MatchedRelationTarget:
            validate_stable_id(self.specification_id)
            self.programme.__post_init__()
            self.target.__post_init__()
            if (self.endpoint != 'MAX_PAIRED_LOG1P_CUMULATIVE_FACTOR_ERROR58'
                    or type(self.pair_scale) is not factorial.PairInteractionScale
                    or self.comparisons or self.alpha is not None or self.sampling_requirement is not None or self.assumption_references
                    or self.procedure != 'DESCRIPTIVE_MAIN_PAIR_AGGREGATE_CURVATURE_THREE_WAY_NO_SIGNIFICANCE_TESTS'
                    or self.missing_policy != 'REQUIRE_COMPLETE_ASSIGNED_WHOLE_GROUPS'
                    or self.family_ids != AMENDED_PRIMARY_FAMILY):
                raise ValueError('matched E4 physical contrasts cannot acquire extra primary tests, Holm adjustment or a pooled-normal premise')
            return
        self._validate_operands(programme_schema=self.programme.object_schema)
        validate_declared_primary_family(self.family_ids, required=factorial.FAMILY_IDS)


@dataclass(frozen=True, slots=True)
class SelectedE4FamilyDescription(factorial.ScheduledFactorialFamilyDescription):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/factorial-family-description"

    def __post_init__(self):
        self._validate_operands(allow_insufficient_family=True)


@dataclass(frozen=True, slots=True)
class SelectedE4FactorialAssessment(factorial.ScheduledFactorialAssessment):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/factorial-assessment"
    VERSION: ClassVar[str] = '2.0.0'
    specification: SelectedE4FactorialSpecification
    family_descriptions: tuple[SelectedE4FamilyDescription, ...]

    def __post_init__(self):
        if type(self.specification.target) is relation.E4MatchedRelationTarget:
            validate_stable_id(self.assessment_id)
            self.specification.__post_init__()
            if (type(self.specification) is not SelectedE4FactorialSpecification
                    or self.programme != self.specification.programme or self.mode not in ('E4_DEVELOPMENT', 'E4_CONFIRMATION')
                    or not self.groups or tuple(row.group_id for row in self.groups) != tuple(sorted({row.group_id for row in self.groups}))
                    or any(type(row) is not factorial.ScheduledFactorialGroup for row in self.groups)
                    or self.tests or self.family_slots or self.three_way_scope != 'DESCRIPTIVE_ONLY' or self.authority != 'NONE'
                    or self.sampling_assumption_status != 'DESCRIPTIVE_NO_POOLED_NORMAL_ASSUMPTION'
                    or self.standing != 'DESCRIPTIVE_PHYSICAL_CONTRASTS_NO_PRIMARY_SIGNIFICANCE_CLAIM'
                    or self.family_descriptions != factorial.describe_factorial_groups(self.groups, description_type=SelectedE4FamilyDescription)):
                raise ValueError('matched E4 descriptions change assigned groups or acquire undeclared significance claims')
            r.exact_pin(self.data, p.SelectedE4ObservedData)
            from .selected_e4_native_records import SelectedE4NativeReduction
            r.exact_pin(self.reduction, r.SelectedE3E4DevelopmentReduction if self.mode == 'E4_DEVELOPMENT' else SelectedE4NativeReduction)
            for record in (*self.groups, *self.family_descriptions):
                record.__post_init__()
            return
        self._validate_operands(specification_type=SelectedE4FactorialSpecification,
            reduction_schema=r.SelectedE3E4DevelopmentReduction.SCHEMA if self.mode == "E4_DEVELOPMENT" else p.NATIVE_REDUCTION_SCHEMA,
            data_schema=p.SelectedE4ObservedData.SCHEMA, group_count=len(self.groups), allow_insufficient_family=True)
        if not self.groups:
            raise ValueError("selected E4 factorial assessment preserves a nonempty declared group census")


def assess_factorial(specification, programme, bank, reduction, data, *, assessment_id):
    if type(specification) is not SelectedE4FactorialSpecification or specification.programme != programme.identity:
        raise TypeError("selected E4 factorial calculation requires its frozen explicit scientific declaration")
    specification.__post_init__()
    targets, _ = validate_observed_data(programme, bank, reduction, data, specification.target, allow_absent=True)
    by_root = {row.root_id: row for row in data.cases}
    for group in programme.group_ids:
        rows = tuple(case for case in programme.cases if case.independent_group_id == group)
        if (len({(matched_key(by_root[case.root_id].coordinate), by_root[case.root_id].coordinate.clock_id)
                for case in rows if case.root_id in by_root}) > 1
                or len({case.streams_sha256 for case in rows}) != 1):
            raise ValueError("selected factorial matched group changes fixed source/start/noise or physical clock")
    if type(specification.target) is relation.E4MatchedRelationTarget:
        # An unresolved PRIMARY/FINE discrepancy is not a physical contrast.
        for case in programme.cases:
            row = by_root.get(case.root_id)
            if row is not None and row.score is not None and relation.relation_target_reasons(row.score.paired_errors):
                targets[case.root_id] = (None,) * 58
        groups = factorial.factorial_groups_from_targets(specification, programme, reduction, data, targets)
        return SelectedE4FactorialAssessment(assessment_id, specification, programme.identity, p._record_pin(reduction), data.identity,
            programme.mode, groups, factorial.describe_factorial_groups(groups, description_type=SelectedE4FamilyDescription), (), (),
            'DESCRIPTIVE_NO_POOLED_NORMAL_ASSUMPTION', 'DESCRIPTIVE_ONLY', 'NONE',
            'DESCRIPTIVE_PHYSICAL_CONTRASTS_NO_PRIMARY_SIGNIFICANCE_CLAIM')
    return factorial.factorial_from_targets(specification, programme, reduction, data, targets, assessment_id=assessment_id,
        assessment_type=SelectedE4FactorialAssessment, description_type=SelectedE4FamilyDescription)


@dataclass(frozen=True, slots=True)
class SelectedE4NominationRule(workflow.ScheduledE4NominationRule):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/nomination-rule"
    confirmation_group_count: int
    revision_baseline_alternative: PairedMeanTAlternative

    def __post_init__(self):
        self._validate_operands(maximum_groups=self.confirmation_group_count)
        if (type(self.confirmation_group_count) is not int or self.confirmation_group_count < 1
                or type(self.revision_baseline_alternative) is not PairedMeanTAlternative):
            raise ValueError("selected E4 coverage thresholds require the explicit assigned confirmation denominator")


@dataclass(frozen=True, slots=True)
class SelectedE4MatchedRelationRule(CanonicalRecord):
    """CONF measures the fixed SR/BR pair and cannot select a downstream account."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-selected-e4/matched-relation-rule'
    rule_id: str
    confirmation_group_count: int
    account_rule: str = 'FROZEN_SR_BR_AFTER_ELIGIBLE_DEV_NO_CONFIRMATION_SELECTION'
    admission_owner: str = 'SR'
    references: tuple[str, ...] = ('B0', 'S0')
    alpha_numerator: int = 1
    alpha_denominator: int = 160
    null_numerator: int = 1
    null_denominator: int = 2
    margin_numerator: int = 1
    margin_denominator: int = 29

    def __post_init__(self):
        validate_stable_id(self.rule_id)
        if (type(self.confirmation_group_count) is not int or self.confirmation_group_count < 1
                or self.account_rule not in ('FROZEN_SR_BR_AFTER_ELIGIBLE_DEV_NO_CONFIRMATION_SELECTION',
                    'FROZEN_SR_BR_CURVE_AFTER_ELIGIBLE_DEV_NO_CONFIRMATION_SELECTION')
                or self.admission_owner != 'SR' or self.references != ('B0', 'S0')
                or any(type(value) is not int for value in (self.alpha_numerator, self.alpha_denominator, self.null_numerator,
                    self.null_denominator, self.margin_numerator, self.margin_denominator))
                or (self.alpha_numerator, self.alpha_denominator, self.null_numerator, self.null_denominator,
                    self.margin_numerator, self.margin_denominator) != (1, 160, 1, 2, 1, 10 if self.is_curve_primary else 29)):
            raise ValueError('matched E4 rule changes the fixed account, reference or assigned-group primary criterion')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.rule_id, self)

    @property
    def is_curve_primary(self):
        return self.account_rule == 'FROZEN_SR_BR_CURVE_AFTER_ELIGIBLE_DEV_NO_CONFIRMATION_SELECTION'


@dataclass(frozen=True, slots=True)
class SelectedE4ProgrammeSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/programme-specification"
    VERSION: ClassVar[str] = '2.0.0'
    specification_id: str
    original_e3_package: ObjectIdentity
    original_e3_models: ObjectIdentity
    development: ObjectIdentity
    calibration: ObjectIdentity
    confirmation: ObjectIdentity
    nomination_rule: SelectedE4NominationRule | SelectedE4MatchedRelationRule
    family_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        if (type(self.original_e3_package) is not ObjectIdentity or type(self.original_e3_models) is not ObjectIdentity
                or type(self.nomination_rule) not in (SelectedE4NominationRule, SelectedE4MatchedRelationRule)):
            raise ValueError("selected E4 programme requires explicit original three-account package and complete frozen decision rule")
        if type(self.nomination_rule) is SelectedE4MatchedRelationRule:
            if self.family_ids != AMENDED_PRIMARY_FAMILY:
                raise ValueError('matched E4 programme changes the amended eight-slot primary family')
        else:
            validate_declared_primary_family(self.family_ids, required=factorial.FAMILY_IDS)
        r.exact_pin(self.development, r.SelectedE3E4DevelopmentProgramme)
        r.exact_pin(self.calibration, p.SelectedE4PhaseProgramme)
        r.exact_pin(self.confirmation, p.SelectedE4PhaseProgramme)
        if self.calibration == self.confirmation:
            raise ValueError("selected E4 CAL and CONF must be separate declared populations")
        self.nomination_rule.__post_init__()

    @property
    def identity(self):
        return p._record_pin(self, "specification_id")

    def validate(self, development, calibration, confirmation, *, banks=None):
        self.__post_init__()
        if (development.identity, calibration.identity, confirmation.identity) != (self.development, self.calibration, self.confirmation):
            raise ValueError("selected E4 programme substitutes assigned original phase identities")
        for programme, phase in ((calibration, "CALIBRATION"), (confirmation, "CONFIRMATION")):
            p.validate_phase_separation(development, programme)
            if programme.mode != p.PHASES[phase][0]:
                raise ValueError("selected E4 programme changes explicit phase role")
        for first, second in combinations((development, calibration, confirmation), 2):
            for select in (lambda value: set(value.group_ids), lambda value: {case.root_id for case in value.cases},
                    lambda value: {case.source for case in value.cases}, lambda value: {case.streams_sha256 for case in value.cases}):
                if select(first) & select(second):
                    raise ValueError("selected E4 reuses original independent groups, roots, sources or random streams")
        if confirmation.design.group_count != self.nomination_rule.confirmation_group_count:
            raise ValueError("selected E4 rule coverage threshold changes assigned confirmation denominator")
        if banks is not None:
            if type(banks) is not tuple or len(banks) != 3:
                raise ValueError("selected E4 programme needs all original typed phase banks")
            r.validate_development_bank(development, banks[0])
            for programme, bank in zip((calibration, confirmation), banks[1:], strict=True):
                p.validate_selected_phase_bank(programme, bank)
            for bank in banks:
                package = bank.forecast_design.package
                if package.original_package != self.original_e3_package or r.pin(package.models) != self.original_e3_models:
                    raise ValueError("selected E4 phase substitutes actual three original E3 fitted accounts")


@dataclass(frozen=True, slots=True)
class SelectedE4Confirmation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/confirmation"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    specification: ObjectIdentity
    factorial: ObjectIdentity
    calibration: ObjectIdentity | None
    groups: tuple[workflow.ScheduledE4ConfirmationGroup, ...]
    family_slots: tuple[factorial.ScheduledFactorialFamilySlot, ...]
    factorial_assessment: SelectedE4FactorialAssessment
    nomination_rule: SelectedE4NominationRule | SelectedE4MatchedRelationRule
    original_point_losses: tuple[tuple[str, tuple[tuple[str, Decimal | None], ...]], ...]
    assumption_status: str = factorial.ASSUMPTION_STATUS
    standing: str = workflow.STANDING
    relation_cases: tuple[relation.E4RelationScoringCase, ...] = ()
    relation_decisions: tuple[relation.E4RelationGroupDecision | MatchedCurveDecision, ...] = ()
    model_coverage: tuple[relation.E4RelationGroupCoverage, ...] = ()
    amended_inference: AssignedBinomialInference | None = None
    original_duration_error_counts: tuple[tuple[str, tuple[tuple[str, int | None], ...]], ...] = ()

    def __post_init__(self):
        validate_stable_id(self.record_id)
        r.exact_pin(self.specification, SelectedE4ProgrammeSpecification)
        r.exact_pin(self.factorial, SelectedE4FactorialAssessment)
        if self.calibration is not None:
            r.exact_pin(self.calibration, SelectedE4Calibration)
        if type(self.nomination_rule) is SelectedE4MatchedRelationRule:
            self._validate_matched()
            return
        if any((self.relation_cases, self.relation_decisions, self.model_coverage, self.amended_inference,
                self.original_duration_error_counts)):
            raise ValueError('closed E4 confirmation cannot acquire amended relation claims')
        if (type(self.factorial_assessment) is not SelectedE4FactorialAssessment
                or self.factorial != r.pin(self.factorial_assessment, "assessment_id")
                or self.factorial_assessment.mode != "E4_CONFIRMATION"
                or type(self.nomination_rule) is not SelectedE4NominationRule
                or len(self.groups) != self.nomination_rule.confirmation_group_count
                or tuple(row.independent_group_id for row in self.groups) != tuple(row.group_id for row in self.factorial_assessment.groups)
                or tuple(row.comparison_id for row in self.family_slots) != factorial.declared_family(self.factorial_assessment.specification)
                or self.family_slots != conditional_family(self.groups, self.factorial_assessment, self.nomination_rule)
                or any(row.original_covered is not None for row in self.groups)
                or self.assumption_status != factorial.ASSUMPTION_STATUS or self.standing != workflow.STANDING):
            raise ValueError("selected E4 confirmation drops whole groups, declared family slots or invents original E3 scope applicability")
        for record in (*self.groups, *self.family_slots, self.factorial_assessment, self.nomination_rule):
            record.__post_init__()
        groups = tuple(row.independent_group_id for row in self.groups)
        if (tuple(group for group, _ in self.original_point_losses) != groups
                or any(tuple(method for method, _ in losses) != METHODS for _, losses in self.original_point_losses)):
            raise ValueError("selected E4 confirmation hides an original E3 account or whole-group point loss")
        for _, losses in self.original_point_losses:
            for _, loss in losses:
                if loss is not None and (type(loss) is not Decimal or not loss.is_finite() or loss < 0):
                    raise ValueError("selected E4 original point loss changes exact finite/adverse grammar")
        if self.calibration is None and any(row.revision_covered is not None or row.revision_loss is not None for row in self.groups):
            raise ValueError("selected unentered revision cannot invent confirmation loss or coverage")

    def _validate_matched(self):
        if (type(self.factorial_assessment) is not SelectedE4FactorialAssessment
                or type(self.factorial_assessment.specification.target) is not relation.E4MatchedRelationTarget
                or self.factorial != r.pin(self.factorial_assessment, 'assessment_id')
                or self.factorial_assessment.mode != 'E4_CONFIRMATION' or self.calibration is None
                or self.family_slots or self.assumption_status != 'INDEPENDENT_UNIFORM_FOUR_FAMILY_GROUP_SAMPLING_REQUIRED'
                or self.standing != 'FROZEN_SR_BR_CONFIRMATION_NO_ACCOUNT_SELECTION'):
            raise ValueError('matched E4 confirmation changes the frozen relation, separate CAL or descriptive contrast scope')
        self.nomination_rule.__post_init__()
        self.factorial_assessment.__post_init__()
        groups = tuple(row.group_id for row in self.factorial_assessment.groups)
        if (len(groups) != self.nomination_rule.confirmation_group_count
                or self.relation_decisions != relation.relation_group_decisions(self.relation_cases, assigned_groups=groups,
                    curve_primary=self.nomination_rule.is_curve_primary)
                or self.amended_inference != relation.relation_primary_inference(self.relation_decisions)
                or tuple((row.group_id, row.method_key) for row in self.model_coverage) !=
                    tuple((group, method) for group in groups for method in ('BR', 'SR'))
                or self.groups != _matched_confirmation_groups(self.relation_decisions, self.model_coverage)):
            raise ValueError('matched E4 confirmation changes the full assigned test, paired losses or model coverage census')
        roots = {row.group_id: row.root_ids for row in self.relation_decisions}
        for row in self.model_coverage:
            row.__post_init__()
            if tuple(case.unit_id for case in row.cases) != roots[row.group_id]:
                raise ValueError('matched E4 coverage substitutes the original nine assigned roots')
        if (tuple(group for group, _ in self.original_point_losses) != groups
                or tuple(group for group, _ in self.original_duration_error_counts) != groups
                or any(tuple(method for method, _ in losses) != MATCHED_METHODS for _, losses in self.original_point_losses)
                or any(tuple(method for method, _ in losses) != MATCHED_METHODS for _, losses in self.original_duration_error_counts)):
            raise ValueError('matched E4 confirmation drops unchanged original E3 reference accounts')
        for _, losses in self.original_point_losses:
            if any(value is not None and (type(value) is not Decimal or not value.is_finite() or value < 0) for _, value in losses):
                raise ValueError('matched E4 reference point losses change finite/adverse grammar')
        for _, losses in self.original_duration_error_counts:
            if any(value is not None and (type(value) is not int or not 0 <= value <= 522) for _, value in losses):
                raise ValueError('matched E4 reference duration losses change the paired nine-coordinate denominator')

    @property
    def identity(self):
        return p._record_pin(self)


def _validate_calibration(calibration, development, nomination, frozen, programme):
    if type(calibration) is not p.SelectedE4PublicCalibration:
        raise TypeError("selected E4 confirmation needs its authenticated public separate calibration projection")
    calibration.__post_init__()
    if ((calibration.specification.development_programme, calibration.specification.calibration_programme,
            calibration.specification.nomination, calibration.specification.frozen_models) !=
            (development.identity, programme.identity, nomination.identity, frozen.identity)
            or calibration.group_ids != programme.group_ids or calibration.revision_model != nomination.revision_model.identity
            or calibration.baseline_model != nomination.baseline_model.identity):
        raise ValueError("selected E4 confirmation substitutes actual complete CAL population or frozen coefficients")


def assess_confirmation(specification, development, calibration_programme, programme, nomination, frozen,
        calibration, bank, reduction, data, forecasts, factorial_assessment, *, record_id):
    specification.validate(development, calibration_programme, programme)
    validate_frozen_revision(development, nomination, frozen)
    export = p.SelectedE4RevisionExport.from_products(development, nomination, frozen, record_id="export." + frozen.package_id)
    if export.models is not None:
        _validate_calibration(calibration, development, nomination, frozen, calibration_programme)
    return assess_confirmation_public(specification, programme, bank, export, calibration, reduction, data,
        p.SelectedE4ForecastBank("forecasts." + programme.programme_id, programme.identity, forecasts),
        factorial_assessment, record_id=record_id)


@dataclass(frozen=True, slots=True)
class SelectedE4DownstreamNomination(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/downstream-nomination"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    specification: ObjectIdentity
    rule: ObjectIdentity
    confirmation: ObjectIdentity
    original_e3_package: ObjectIdentity
    frozen_revision: ObjectIdentity | None
    calibration: ObjectIdentity | None
    selected: str | None
    dispositions: tuple[tuple[str, str], ...]
    rule_product: SelectedE4NominationRule | SelectedE4MatchedRelationRule
    confirmation_product: SelectedE4Confirmation
    frozen_product: p.SelectedE4PublicRevisionDecision
    calibration_product: p.SelectedE4PublicCalibration | None
    standing: str = workflow.STANDING

    def __post_init__(self):
        validate_stable_id(self.record_id)
        r.exact_pin(self.specification, SelectedE4ProgrammeSpecification)
        if (type(self.rule_product) not in (SelectedE4NominationRule, SelectedE4MatchedRelationRule)
                or type(self.confirmation_product) is not SelectedE4Confirmation
                or type(self.frozen_product) is not p.SelectedE4PublicRevisionDecision
                or self.calibration_product is not None and type(self.calibration_product) is not p.SelectedE4PublicCalibration
                or self.rule != self.rule_product.identity or self.confirmation != self.confirmation_product.identity
                or self.confirmation_product.specification != self.specification
                or self.confirmation_product.nomination_rule != self.rule_product
                or self.standing != workflow.STANDING):
            raise ValueError("selected E4 downstream decision substitutes actual immutable scientific products")
        for record in (self.rule_product, self.confirmation_product, self.frozen_product, self.calibration_product):
            if record is not None:
                record.__post_init__()
        product = self.calibration_product
        if type(self.rule_product) is SelectedE4MatchedRelationRule:
            if (product is None or not self.frozen_product.fit_available or self.frozen_product.relation_fit is None
                    or self.calibration != product.original or self.confirmation_product.calibration != self.calibration
                    or self.frozen_revision != self.frozen_product.frozen
                    or (product.specification.frozen_models, product.specification.nomination, product.relation_fit,
                        product.revision_model, product.baseline_model) !=
                        (self.frozen_product.frozen, self.frozen_product.nomination, self.frozen_product.relation_fit,
                         self.frozen_product.revision_model, self.frozen_product.baseline_model)
                    or self.dispositions != _matched_downstream_dispositions() or self.selected != 'REVISION'):
                raise ValueError('matched E4 downstream account must retain the original eligible SR/BR fit and CAL after every CONF outcome')
            return
        if (self.calibration != (None if product is None else product.original)
                or self.confirmation_product.calibration != self.calibration
                or self.frozen_revision != (None if product is None else self.frozen_product.frozen)
                or product is not None and product.specification.frozen_models != self.frozen_product.frozen
                or (product is None) != (self.frozen_product.frozen_disposition == "UNENTERED")):
            raise ValueError("selected E4 downstream nomination invents entry or changes actual calibrated joint freeze")
        expected = workflow._nomination_dispositions(self.rule_product, self.confirmation_product, product)
        selected = next((name for name in self.rule_product.priority if dict(expected)[name] == "ELIGIBLE"), None)
        if self.dispositions != expected or self.selected != selected:
            raise ValueError("selected E4 downstream decision changes its frozen criteria or hides an alternative")

    @property
    def identity(self):
        return p._record_pin(self)


def nominate_downstream(specification, confirmation, export, calibration, *, record_id):
    if (type(specification) is not SelectedE4ProgrammeSpecification or type(confirmation) is not SelectedE4Confirmation
            or confirmation.specification != specification.identity or confirmation.nomination_rule != specification.nomination_rule
            or confirmation.factorial_assessment.programme != specification.confirmation
            or type(export) is not p.SelectedE4RevisionExport or export.decision.development != specification.development):
        raise ValueError("selected E4 nomination requires actual full confirmation and its predeclared rule/freeze")
    specification.__post_init__()
    confirmation.__post_init__()
    export.__post_init__()
    if type(specification.nomination_rule) is SelectedE4MatchedRelationRule:
        if export.models is None or export.models.relation_fit is None or calibration is None:
            raise ValueError('matched E4 downstream requires its actual constructible frozen SR/BR pair and separate CAL')
        dispositions, selected = _matched_downstream_dispositions(), 'REVISION'
    else:
        dispositions = workflow._nomination_dispositions(specification.nomination_rule, confirmation, calibration)
        selected = next((name for name in specification.nomination_rule.priority if dict(dispositions)[name] == "ELIGIBLE"), None)
    return SelectedE4DownstreamNomination(record_id, specification.identity, specification.nomination_rule.identity,
        confirmation.identity, specification.original_e3_package, None if calibration is None else export.decision.frozen,
        None if calibration is None else calibration.original, selected, dispositions, specification.nomination_rule,
        confirmation, export.decision, calibration)


def _matched_downstream_dispositions():
    return (('ORIGINAL_E3', 'FROZEN_REFERENCES_ONLY'), ('REVISION', 'ELIGIBLE_FROZEN_SR_BR'))


def validate_public_phase(export, programme, *, phase):
    if type(export) is not p.SelectedE4RevisionExport or type(programme) is not p.SelectedE4PhaseProgramme:
        raise TypeError("selected protected method needs exact public frozen revision and phase records")
    export.__post_init__()
    programme.__post_init__()
    if programme.mode != p.PHASES.get(phase, (None,))[0]:
        raise ValueError("selected protected method changes its actual phase role")
    if export.models is not None:
        models = export.models
        if (models.target.criterion != programme.criterion or models.development_design.factors != programme.factors
                or set(models.training_groups) & set(programme.group_ids)):
            raise ValueError("selected protected method changes model target/grid or reuses original development units")


def validate_public_forecasts(export, programme, data, bank, *, calibration=None):
    if type(bank) is not p.SelectedE4ForecastBank or bank.programme != programme.identity:
        raise TypeError("selected protected method needs its actual compact original forecast census")
    bank.__post_init__()
    if export.models is not None and export.models.relation_fit is not None:
        rows = {row.root_id: row for row in data.cases}
        expected = tuple(case.root_id for case in programme.cases
            if case.root_id in rows and rows[case.root_id].causal_feature is not None)
        if tuple(seal.case_id for seal in bank.forecasts) != expected:
            raise ValueError('matched E4 forecasts omit an original account or invent a seal for an absent causal case')
        originals = {seal.case_id: seal for seal in bank.forecasts}
        for case in programme.cases:
            row, seal = rows.get(case.root_id), originals.get(case.root_id)
            if seal is None:
                if row is not None and row.revision_forecast is not None:
                    raise ValueError('matched E4 read drops an actual original revision forecast')
                continue
            expected_seal = export.models.forecast(programme, case, record_id=seal.record_id,
                feature=row.causal_feature, calibration=calibration)
            if seal != expected_seal or row.revision_forecast != seal.identity:
                raise ValueError('matched E4 forecast replay changes original causal features, fixed models or consumed upper curves')
        return
    expected = tuple(case.root_id for case in programme.cases) if export.models is not None else ()
    if tuple(seal.case_id for seal in bank.forecasts) != expected:
        raise ValueError("selected protected method omits a pre-future forecast or invents an unentered revision")
    rows = {row.root_id: row for row in data.cases}
    for case, seal in zip(programme.cases if export.models is not None else (), bank.forecasts, strict=True):
        if (seal != export.models.forecast(programme, case, record_id=seal.record_id)
                or case.root_id in rows and rows[case.root_id].revision_forecast != seal.identity):
            raise ValueError("selected protected method changes actual pre-future model predictions or source association")


def calibrate_revision_public(specification, export, programme, bank, reduction, data, forecasts, *, record_id):
    validate_public_phase(export, programme, phase="CALIBRATION")
    if export.models is None:
        raise ValueError("an unentered selected revision cannot enter a calibration producer")
    models = export.models
    if (type(specification) is not p.SelectedE4CalibrationSpecification
            or (specification.development_programme, specification.calibration_programme, specification.nomination, specification.frozen_models) !=
            (models.development, programme.identity, models.nomination, models.frozen)
            or Fraction(specification.alpha) != 1 - Fraction(programme.confidence)):
        raise ValueError("selected calibration changes actual public frozen models, original population or explicit alpha")
    specification.__post_init__()
    targets, missing = validate_observed_data(programme, bank, reduction, data, models.target, allow_absent=True)
    validate_public_forecasts(export, programme, data, forecasts)
    if models.relation_fit is not None:
        if specification.score_rule != relation.RELATION_SCORE_RULE:
            raise ValueError('matched E4 calibration requires the original nine-coordinate paired58 maximum')
        cases = relation_scoring_cases(programme, data, forecasts)
        calibrated = relation.calibrate_relation_values(cases, assigned_groups=programme.group_ids)
        by_method = {row.method_key: row for row in calibrated}
        by_root = {seal.case_id: seal for seal in forecasts.forecasts}
        return SelectedE4Calibration(record_id, specification, models.target.identity, models.revision_model, models.baseline_model,
            programme.group_ids, tuple((group, value) for group, value, _ in by_method['SR'].scores),
            tuple((group, value) for group, value, _ in by_method['BR'].scores), by_method['SR'].rank,
            by_method['SR'].radius, by_method['BR'].radius, data.identity,
            tuple(None if case.root_id not in by_root else by_root[case.root_id].identity for case in programme.cases),
            models.relation_fit.identity, calibrated)
    return calibration_owner.calibration_from_targets(specification, models.target.identity,
        models.revision_model, models.baseline_model, programme, data, forecasts.forecasts, targets, missing,
        record_id=record_id, record_type=SelectedE4Calibration)


def _validate_public_calibration(specification, export, calibration, programme):
    if type(calibration) is not p.SelectedE4PublicCalibration:
        raise TypeError("selected confirmation needs its authenticated public separate CAL projection")
    calibration.__post_init__()
    models = export.models
    if (models is None or (calibration.specification.development_programme, calibration.specification.calibration_programme,
            calibration.specification.nomination, calibration.specification.frozen_models) !=
            (models.development, specification.calibration, models.nomination, models.frozen)
            or calibration.target != models.target.identity
            or (calibration.revision_model, calibration.baseline_model) != (models.revision_model.identity, models.baseline_model.identity)
            or calibration.relation_fit != (None if models.relation_fit is None else models.relation_fit.identity)
            or set(calibration.group_ids) & set((*models.training_groups, *programme.group_ids))):
        raise ValueError("selected confirmation substitutes original calibration/frozen models or reuses CAL groups")


def relation_scoring_cases(programme, data, forecasts):
    """Keep every assigned coordinate; missing seals and targets stay missing."""
    observed = {row.root_id: row for row in data.cases}
    sealed = {row.case_id: row for row in forecasts.forecasts}
    result = []
    for case in programme.cases:
        row, seal = observed.get(case.root_id), sealed.get(case.root_id)
        reasons = set()
        if row is None or row.disposition != 'COMPLETED':
            reasons.add('ORIGINAL_CASE_ABSENT' if row is None else 'ORIGINAL_CASE_' + row.disposition)
        if row is not None and row.numerical_disposition != 'SATISFIED':
            reasons.add('ORIGINAL_NUMERICAL_' + row.numerical_disposition)
        if row is None or row.causal_feature is None or row.causal_feature.disposition != 'AVAILABLE':
            reasons.add('CAUSAL_FEATURE_UNAVAILABLE')
        score = None if row is None else row.score
        errors = (None,) * 58 if score is None else score.paired_errors
        if score is not None and score.target_contract != 'MATCHED_FACTOR58':
            raise ValueError('matched E4 scoring substitutes a different original target')
        points = tuple((method, (None,) * 58) for method in relation.RELATION_METHODS) if seal is None else seal.relation_points
        result.append(relation.E4RelationScoringCase(case.root_id, case.independent_group_id,
            None if seal is None else seal.identity, None if score is None else score.original,
            points, errors, tuple(sorted(reasons))))
    return tuple(result)


def assess_confirmation_public(specification, programme, bank, export, calibration, reduction, data,
        forecasts, factorial_assessment, *, record_id):
    if type(specification) is not SelectedE4ProgrammeSpecification or programme.identity != specification.confirmation:
        raise TypeError("selected confirmation requires its predeclared complete scientific programme")
    specification.__post_init__()
    validate_public_phase(export, programme, phase="CONFIRMATION")
    if (export.decision.development != specification.development
            or programme.design.group_count != specification.nomination_rule.confirmation_group_count):
        raise ValueError("selected confirmation changes its original DEV selection or frozen coverage denominator")
    if factorial.declared_family(factorial_assessment.specification) != specification.family_ids:
        raise ValueError("selected confirmation changes the declared primary family")
    target = factorial_assessment.specification.target
    if export.models is not None and target != export.models.target:
        raise ValueError("selected confirmation substitutes its frozen response target")
    targets, missing = validate_observed_data(programme, bank, reduction, data, target, allow_absent=True)
    if (type(factorial_assessment) is not SelectedE4FactorialAssessment or factorial_assessment.mode != "E4_CONFIRMATION"
            or factorial_assessment != assess_factorial(factorial_assessment.specification, programme, bank, reduction, data,
                assessment_id=factorial_assessment.assessment_id)):
        raise ValueError("selected confirmation changes original seven factorial comparisons")
    if type(specification.nomination_rule) is SelectedE4MatchedRelationRule and (
            export.models is None or export.models.relation_fit is None):
        raise ValueError('unconstructible matched E4 models are a prerequisite failure; CONF cannot select an E3 fallback')
    validate_public_forecasts(export, programme, data, forecasts, calibration=calibration)
    if export.models is not None:
        _validate_public_calibration(specification, export, calibration, programme)
    elif calibration is not None:
        raise ValueError("selected unentered revision cannot gain separate calibration evidence")
    if type(specification.nomination_rule) is SelectedE4MatchedRelationRule:
        return _matched_confirmation(specification, programme, calibration, data, forecasts, factorial_assessment,
            record_id=record_id)
    return confirmation_from_targets(specification, programme, export, calibration, reduction, data, forecasts.forecasts,
        factorial_assessment, targets, missing, record_id=record_id)


def _matched_confirmation_groups(decisions, coverage):
    sr = {row.group_id: row for row in coverage if row.method_key == 'SR'}
    return tuple(workflow.ScheduledE4ConfirmationGroup(row.group_id, None, sr[row.group_id].covered,
        reported_loss(row.loss('SR') if type(row) is MatchedCurveDecision else
            Fraction(dict(row.duration_error_counts)['SR'], 522)) if row.usable else None,
        reported_loss(row.loss('BR') if type(row) is MatchedCurveDecision else
            Fraction(dict(row.duration_error_counts)['BR'], 522)) if row.usable else None)
        for row in decisions)


def _matched_confirmation(specification, programme, calibration, data, forecasts, factorial_assessment, *, record_id):
    cases = relation_scoring_cases(programme, data, forecasts)
    decisions = relation.relation_group_decisions(cases, assigned_groups=programme.group_ids,
        curve_primary=specification.nomination_rule.is_curve_primary)
    coverage = relation.relation_group_coverage(cases, forecasts.forecasts, assigned_groups=programme.group_ids)
    observed = {row.root_id: row for row in data.cases}
    point_losses, duration_losses = [], []
    for group in programme.group_ids:
        rows = tuple(row for row in cases if row.group_id == group)
        reference_losses, reference_durations = [], []
        for method in MATCHED_METHODS:
            usable = all(not row.reasons and not relation.relation_target_reasons(row.errors)
                and all(value is not None for value in row.errors) for row in rows)
            point_rows = tuple(dict(observed[row.root_id].original_log_points)[method] for row in rows) if usable else ()
            usable = usable and all(all(value is not None for value in points) for points in point_rows)
            if usable:
                loss = max(abs(Fraction(actual) - Fraction(point)) for row, points in zip(rows, point_rows, strict=True)
                    for actual, point in zip(observed[row.root_id].score.paired_log_targets, points, strict=True))
                count = sum(matched_duration_error_count(points, row.errors) for row, points in zip(rows, point_rows, strict=True))
                reference_losses.append((method, selection._exact_decimal(loss)))
                reference_durations.append((method, count))
            else:
                reference_losses.append((method, None))
                reference_durations.append((method, None))
        point_losses.append((group, tuple(reference_losses)))
        duration_losses.append((group, tuple(reference_durations)))
    return SelectedE4Confirmation(record_id, specification.identity, r.pin(factorial_assessment, 'assessment_id'),
        calibration.original, _matched_confirmation_groups(decisions, coverage), (), factorial_assessment,
        specification.nomination_rule, tuple(point_losses), 'INDEPENDENT_UNIFORM_FOUR_FAMILY_GROUP_SAMPLING_REQUIRED',
        'FROZEN_SR_BR_CONFIRMATION_NO_ACCOUNT_SELECTION', cases, decisions, coverage,
        relation.relation_primary_inference(decisions), tuple(duration_losses))


def confirmation_from_targets(specification, programme, export, calibration, reduction, data, forecasts,
        factorial_assessment, targets, missing, *, record_id):
    """Shared selected original-point and paired-model whole-group equations."""
    entered = export.models is not None
    by_forecast = {seal.case_id: seal for seal in forecasts}
    observed = {row.root_id: row for row in data.cases}
    groups, point_losses = [], []
    for group in programme.group_ids:
        cases = tuple(case for case in programme.cases if case.independent_group_id == group)
        losses = []
        for method in METHODS:
            points = tuple((target, point) for case in cases for target, point in zip(
                targets[case.root_id], dict(observed[case.root_id].original_log_points)[method] * 2, strict=True)) if group not in missing else ()
            loss = (None if not points or any(point is None for _, point in points) else
                selection._exact_decimal(max(abs(Fraction(actual)-Fraction(point)) for actual, point in points)))
            losses.append((method, loss))
        point_losses.append((group, tuple(losses)))
        revision_loss, baseline_loss, covered = None, None, None
        if entered and group not in missing:
            losses = tuple(max(abs(Fraction(actual)-Fraction(point)) for case in cases
                for actual, point in zip(targets[case.root_id], getattr(by_forecast[case.root_id], name), strict=True))
                for name in ("revision_predictions", "baseline_predictions"))
            revision_loss, baseline_loss = (selection._exact_decimal(value) for value in losses)
            covered = all(calibration.revision_radius is None or Fraction(actual)-Fraction(point) <= Fraction(calibration.revision_radius)
                for case in cases for actual, point in zip(targets[case.root_id], by_forecast[case.root_id].revision_predictions, strict=True))
        groups.append(workflow.ScheduledE4ConfirmationGroup(group, None, covered, revision_loss, baseline_loss))
    slots = conditional_family(tuple(groups), factorial_assessment, specification.nomination_rule)
    return SelectedE4Confirmation(record_id, specification.identity, r.pin(factorial_assessment, "assessment_id"),
        None if calibration is None else calibration.original, tuple(groups), slots, factorial_assessment,
        specification.nomination_rule, tuple(point_losses))


def conditional_family(groups, factorial_assessment, rule):
    return workflow._confirmation_family(groups, factorial_assessment, rule, alternative=rule.revision_baseline_alternative)
