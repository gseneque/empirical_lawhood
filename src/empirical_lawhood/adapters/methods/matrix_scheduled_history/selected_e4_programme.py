# SPDX-License-Identifier: MPL-2.0
"""Selected E4 phase and bounded public scientific contracts.

Original E3 coefficients and typed source owners are preserved. These records
describe arithmetic and original scientific pins; source/receipt authority is
authenticated by the owning lifecycle, never inferred from record presence.
"""

from empirical_lawhood.kernel.decoding import validate_record_fields
from dataclasses import dataclass
from decimal import Decimal, getcontext, localcontext
from functools import lru_cache, wraps
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole, MatrixProgrammeRoot
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.kernel.time import InformationCutoff
from empirical_lawhood.runtime.experimental_statistics import predict_standardized_ridge

from . import selected_e3_e4_records as r
from .programme_records import ScheduledProgramme, ScheduledProgrammeCase
from .programme_roster import validate_programme_roster
from .programme_selection import ScheduledRevisionFittedModel, ScheduledRevisionTarget, physical_grid_features
from .records import ScheduledCausalPrefix, identity
from .response_records import ScheduledResponseScore
from .revision_calibration import SCORE_RULE
from .e4_structural_prediction import (
    E4MatchedRelationTarget, E4MatchedRelationFit, RELATION_METHODS, RELATION_SCORE_RULE, relation_point_values,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_fitting import (
    MatchedEstimatorModel, MatchedCurveEstimatorModel, require_matched_model_reference,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_prediction import (
    MatchedForecastPolicy, matched_forecast_policy, postprocess_log_points, validate_matched_features,
)

NAMESPACE = "matrix-selected-e4"
PHASES = {"CALIBRATION": ("E4_REVISION_CALIBRATION", MatrixProgrammeRole.CALIBRATION),
    "CONFIRMATION": ("E4_CONFIRMATION", MatrixProgrammeRole.CONFIRMATION)}
NATIVE_REDUCTION_SCHEMA = "empirical-lawhood/matrix-selected-e4/native-reduction"



def _decimal_context_cache(function):
    """Reuse two immutable projections only within their current Decimal policy."""
    @lru_cache(maxsize=2)
    def cached(signature,*args,**kwargs):
        return function(*args,**kwargs)

    @wraps(function)
    def selected(*args,**kwargs):
        context=getcontext()
        signature=(context.prec,context.rounding,context.Emin,context.Emax,context.clamp,context.capitals,
            tuple(sorted((signal.__name__,enabled) for signal,enabled in context.traps.items())))
        return cached(signature,*args,**kwargs)

    selected.cache_clear=cached.cache_clear
    selected.cache_info=cached.cache_info
    selected.cache_parameters=cached.cache_parameters
    return selected


def _pin(value, schema, version="1.0.0"):
    if type(value) is not ObjectIdentity or value.object_schema != schema or value.object_version != version:
        raise ValueError("selected E4 substitutes an exact original scientific operand")
    validate_record_fields(value)


def _record_pin(record, field="record_id"):
    return ObjectIdentity.from_record(getattr(record, field), record)


@dataclass(frozen=True, slots=True)
class SelectedE4PhaseBank(r.SelectedE3E4DevelopmentBank):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/phase-bank"
    phase: str

    def __post_init__(self):
        if self.phase not in PHASES:
            raise ValueError("selected E4 protected bank requires its explicit CAL or CONF role")
        self._validate_role(PHASES[self.phase][1])


@dataclass(frozen=True, slots=True)
class SelectedE4PhaseProgramme(ScheduledProgramme):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/phase-programme"
    design: r.SelectedE3E4Design

    def __post_init__(self):
        if type(self.design) is not r.SelectedE3E4Design or self.factors != self.design.factors:
            raise TypeError("selected protected programme requires its declared matched factorial design")
        validate_record_fields(self.design)
        validate_programme_roster(self, bank_schema=SelectedE4PhaseBank.SCHEMA,
            declared_group_count=self.design.group_count, declared_confidence=self.design.confidence,
            family_sampling_rule=self.design.family_sampling_rule)
        if self.mode not in tuple(mode for mode, _ in PHASES.values()):
            raise ValueError("selected E4 protected programme changes its declared phase")
        r.exact_pin(self.forecast_design, r.SelectedE3E4ForecastDesign)

    @classmethod
    def from_bank(cls, bank, *, programme_id):
        if type(bank) is not SelectedE4PhaseBank:
            raise TypeError("selected E4 phase programme requires its actual original bank")
        validate_record_fields(bank)
        return cls(*r.selected_programme_fields(bank, programme_id=programme_id, mode=PHASES[bank.phase][0]))


@_decimal_context_cache
def validate_selected_phase_bank(programme, bank):
    """Reuse only immutable scientific joins; callers authenticate live custody."""
    if (type(programme) is not SelectedE4PhaseProgramme or type(bank) is not SelectedE4PhaseBank
            or programme.bank != bank.identity
            or programme != SelectedE4PhaseProgramme.from_bank(bank, programme_id=programme.programme_id)):
        raise ValueError("selected E4 phase changes original complete source/group/grid/stream/cutoff joins")


def validate_phase_separation(development, programme):
    if (type(development) is not r.SelectedE3E4DevelopmentProgramme or type(programme) is not SelectedE4PhaseProgramme):
        raise TypeError("selected E4 use retains its truthful DEV and protected phase records")
    validate_record_fields(development)
    validate_record_fields(programme)
    if (development.reservation != programme.reservation or development.specification != programme.specification
            or development.criterion != programme.criterion or development.factors != programme.factors
            or development.forecast_design != programme.forecast_design
            or set(development.group_ids) & set(programme.group_ids)
            or {case.root_id for case in development.cases} & {case.root_id for case in programme.cases}
            or {case.source for case in development.cases} & {case.source for case in programme.cases}
            or {case.streams_sha256 for case in development.cases} & {case.streams_sha256 for case in programme.cases}):
        raise ValueError("selected E4 phase changes original target/information or reuses development units")


@dataclass(frozen=True, slots=True)
class SelectedE4PublicRevisionDecision(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/public-revision-decision"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    development: ObjectIdentity
    nomination: ObjectIdentity
    frozen: ObjectIdentity
    trigger_disposition: str
    frozen_disposition: str
    revision_model: ObjectIdentity | None
    baseline_model: ObjectIdentity | None
    relation_fit: ObjectIdentity | None = None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        _pin(self.development,r.SelectedE3E4DevelopmentProgramme.SCHEMA,r.SelectedE3E4DevelopmentProgramme.VERSION)
        from .selected_e4_methods import SelectedE4RevisionNomination, SelectedE4FrozenRevision
        r.exact_pin(self.nomination, SelectedE4RevisionNomination)
        r.exact_pin(self.frozen, SelectedE4FrozenRevision)
        if self.relation_fit is not None:
            r.exact_pin(self.relation_fit, E4MatchedRelationFit)
            available = self.trigger_disposition == 'FIT_AVAILABLE'
            if (self.trigger_disposition not in ('FIT_AVAILABLE', 'FIT_UNAVAILABLE')
                    or self.frozen_disposition != ('FROZEN_MATCHED_RELATION' if available else 'UNCONSTRUCTIBLE_MATCHED_RELATION')
                    or available != (self.revision_model is not None and self.baseline_model is not None)
                    or not available and (self.revision_model is not None or self.baseline_model is not None)):
                raise ValueError('matched E4 decision changes fit prerequisites or selects a model from confirmation outcomes')
            for model in (self.revision_model, self.baseline_model):
                if model is not None:
                    require_matched_model_reference(model)
            return
        if self.trigger_disposition not in ("TRIGGERED", "NOT_TRIGGERED", "UNEVALUABLE"):
            raise ValueError("selected E4 public decision retains the actual development branch")
        triggered = self.trigger_disposition == "TRIGGERED"
        if ((self.frozen_disposition == "FROZEN_DEVELOPMENT_NOMINATION") != triggered
                or self.frozen_disposition not in ("FROZEN_DEVELOPMENT_NOMINATION", "UNENTERED")
                or triggered != (self.revision_model is not None and self.baseline_model is not None)
                or not triggered and (self.revision_model is not None or self.baseline_model is not None)):
            raise ValueError("selected E4 public decision cannot invent fitted models on an unentered branch")
        for model in (self.revision_model, self.baseline_model):
            if model is not None:
                _pin(model, ScheduledRevisionFittedModel.SCHEMA)

    @property
    def identity(self):
        return _record_pin(self)

    @property
    def fit_available(self):
        return self.trigger_disposition in ('TRIGGERED', 'FIT_AVAILABLE')

    @classmethod
    def from_products(cls, development, nomination, frozen, *, record_id):
        from .selected_e4_methods import validate_frozen_revision
        validate_frozen_revision(development, nomination, frozen)
        return cls(record_id, development.identity, nomination.identity, frozen.identity, nomination.trigger_disposition,
            frozen.disposition, None if nomination.revision_model is None else nomination.revision_model.identity,
            None if nomination.baseline_model is None else nomination.baseline_model.identity,
            None if nomination.relation_fit is None else nomination.relation_fit.identity)


@dataclass(frozen=True, slots=True)
class SelectedE4PublicModels(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/public-models"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    development: ObjectIdentity
    development_design: r.SelectedE3E4Design
    nomination: ObjectIdentity
    frozen: ObjectIdentity
    target: ScheduledRevisionTarget | E4MatchedRelationTarget
    revision_model: ScheduledRevisionFittedModel | MatchedEstimatorModel | MatchedCurveEstimatorModel
    baseline_model: ScheduledRevisionFittedModel | MatchedEstimatorModel | MatchedCurveEstimatorModel
    relation_fit: E4MatchedRelationFit | None = None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        _pin(self.development,r.SelectedE3E4DevelopmentProgramme.SCHEMA,r.SelectedE3E4DevelopmentProgramme.VERSION)
        from .selected_e4_methods import SelectedE4RevisionNomination, SelectedE4FrozenRevision
        r.exact_pin(self.nomination, SelectedE4RevisionNomination)
        r.exact_pin(self.frozen, SelectedE4FrozenRevision)
        if self.relation_fit is not None:
            if (type(self.development_design) is not r.SelectedE3E4Design
                    or type(self.target) is not E4MatchedRelationTarget or type(self.relation_fit) is not E4MatchedRelationFit):
                raise TypeError('matched E4 public models require their actual complete DEV fit and declared geometry')
            for record in (self.development_design, self.target, self.relation_fit):
                validate_record_fields(record)
            models = {row.method_key: row for row in self.relation_fit.models}
            selection = self.relation_fit.selection
            factors = self.development_design.factors
            if ((self.revision_model, self.baseline_model) != (models['SR'], models['BR'])
                    or any(model.parameters is None for model in (self.revision_model, self.baseline_model))
                    or self.relation_fit.development != self.development
                    or len(self.training_groups) != self.development_design.group_count
                    or tuple(factor.factor_id for factor in factors) != ('temperature', 'friction', 'coupling')
                    or tuple(factor.center for factor in factors) !=
                        (selection.nominal_temperature, selection.nominal_friction, selection.nominal_coupling)
                    or any(factor.scale != 'LOG' or factor.low * 2 != factor.center or factor.high != factor.center * 2 for factor in factors)):
                raise ValueError('matched E4 public models change the original SR/BR pair, nominal scales or assigned DEV census')
            return
        if (type(self.development_design) is not r.SelectedE3E4Design or type(self.target) is not ScheduledRevisionTarget
                or any(type(model) is not ScheduledRevisionFittedModel for model in (self.revision_model, self.baseline_model))):
            raise TypeError("selected E4 public models retain actual declared transforms and paired coefficients")
        for record in (self.development_design, self.target, self.revision_model, self.baseline_model):
            validate_record_fields(record)
        if (self.revision_model.training_groups != self.baseline_model.training_groups
                or len(self.revision_model.training_groups) != self.development_design.group_count):
            raise ValueError("selected E4 public coefficients drop their exact whole development census")

    @property
    def identity(self):
        return _record_pin(self)

    @property
    def training_groups(self):
        return self.revision_model.training_unit_ids if self.relation_fit is not None else self.revision_model.training_groups

    @classmethod
    def from_products(cls, development, nomination, frozen, *, record_id):
        from .selected_e4_methods import validate_frozen_revision
        validate_frozen_revision(development, nomination, frozen)
        if nomination.trigger_disposition not in ('TRIGGERED', 'FIT_AVAILABLE'):
            raise ValueError("unentered selected E4 revision has no public fitted model")
        return cls(record_id, development.identity, development.design, nomination.identity, frozen.identity,
            nomination.specification.target, nomination.revision_model, nomination.baseline_model, nomination.relation_fit)

    def predict_coordinate(self, coordinate, *, feature=None):
        if type(coordinate) is not MatrixParameterCoordinate:
            raise TypeError("selected revision point requires its actual typed physical coordinate")
        self.__post_init__()
        validate_record_fields(coordinate)
        values = (coordinate.primary_view.bath_temperature, coordinate.primary_view.friction_gamma,
            coordinate.member.cross_coupling_gamma)
        if self.relation_fit is not None:
            if feature is None:
                raise ValueError('matched E4 predictions require the actual sealed causal features of this case')
            return relation_point_values(self.relation_fit, feature.values, feature.disposition,
                factor_values=values, family_id=coordinate.family_id)
        factors = self.development_design.factors
        if not (all(value in (axis.low, axis.high) for axis, value in zip(factors, values, strict=True))
                or all(value == axis.center for axis, value in zip(factors, values, strict=True))):
            raise ValueError("selected E4 revision has no declared non-grid or transfer feature rule")
        features = physical_grid_features(factors, values)
        return tuple((role, tuple(predict_standardized_ridge(parameters,
            tuple(features[key] for key in model.tuning.feature_names)) for parameters in model.parameters))
            for role, model in (("REVISION", self.revision_model), ("BASELINE", self.baseline_model)))

    def forecast_case(self, programme, case, *, record_id, feature=None, calibration=None, phase=None):
        self.__post_init__()
        _pin(programme,SelectedE4PhaseProgramme.SCHEMA,SelectedE4PhaseProgramme.VERSION)
        if type(case) is not ScheduledProgrammeCase:
            raise TypeError("selected E4 forecast requires the original typed pre-action case")
        validate_record_fields(case)
        if self.relation_fit is not None:
            return self.forecast_matched(programme, root_id=case.root_id, group_id=case.independent_group_id,
                source=case.source, coordinate=case.coordinate, cutoff=case.information_cutoff,
                factor_values=case.factor_values, family_id=case.family_id, feature=feature,
                calibration=calibration, phase=phase, record_id=record_id)
        factors = self.development_design.factors
        corners = all(value in (axis.low, axis.high) for axis, value in zip(factors, case.factor_values, strict=True))
        center = all(value == axis.center for axis, value in zip(factors, case.factor_values, strict=True))
        if not (corners or center):
            raise ValueError("selected E4 grid model has no declared non-grid or transfer feature rule")
        features = physical_grid_features(factors, case.factor_values)
        predictions = []
        for model in (self.revision_model, self.baseline_model):
            values = tuple(features[key] for key in model.tuning.feature_names)
            predictions.append(tuple(predict_standardized_ridge(parameters, values) for parameters in model.parameters))
        return SelectedE4ForecastSeal(record_id, programme, case.root_id, case.independent_group_id, case.source,
            case.coordinate, case.information_cutoff, self.frozen, self.revision_model.identity, self.baseline_model.identity,
            self.target.identity, *predictions)

    def forecast(self, programme, case, *, record_id, feature=None, calibration=None):
        if type(programme) is not SelectedE4PhaseProgramme or case not in programme.cases:
            raise ValueError("selected E4 forecast requires an assigned protected phase case")
        if programme.factors != self.development_design.factors or programme.criterion != self.target.criterion:
            raise ValueError("selected E4 forecast changes frozen grid or scientific target")
        return self.forecast_case(programme.identity, case, record_id=record_id, feature=feature, calibration=calibration,
            phase='CALIBRATION' if programme.mode == PHASES['CALIBRATION'][0] else 'CONFIRMATION')

    def forecast_matched(self, programme, *, root_id, group_id, source, coordinate, cutoff, factor_values, family_id,
            feature, calibration, phase, record_id):
        """Seal one genuine causal case, after mechanics and before assay futures."""
        from .selected_e4_native_records import SelectedE4ProtectedFeature
        self.__post_init__()
        if self.relation_fit is None or type(feature) not in (SelectedE4ProtectedFeature, SelectedE4CausalFeatureProjection):
            raise TypeError('matched E4 forecast requires its original fitted relation and actual protected causal feature')
        validate_record_fields(feature)
        feature_pin = feature.original_feature if type(feature) is SelectedE4CausalFeatureProjection else ObjectIdentity.from_record(feature.feature_id, feature)
        if ((feature.root_id, feature.independent_group_id, feature.source, feature.clock_id, feature.cutoff) !=
                (root_id, group_id, source, cutoff.clock_id, cutoff.coordinate)
                or feature.physical_forecast is None or group_id in self.training_groups
                or phase not in ('CALIBRATION', 'CONFIRMATION')):
            raise ValueError('matched E4 forecast substitutes a causal case, reuses DEV or omits its mechanical dependency')
        if phase == 'CALIBRATION':
            if calibration is not None:
                raise ValueError('matched E4 CAL cannot require its own future radius')
            radii, calibration_pin = (), None
        else:
            if type(calibration) is not SelectedE4PublicCalibration:
                raise TypeError('matched E4 confirmation requires its actual separate frozen calibration')
            validate_record_fields(calibration)
            if ((calibration.specification.frozen_models, calibration.target, calibration.revision_model, calibration.baseline_model,
                    calibration.relation_fit) != (self.frozen, self.target.identity, self.revision_model.identity,
                    self.baseline_model.identity, self.relation_fit.identity)
                    or group_id in calibration.group_ids):
                raise ValueError('matched E4 forecast substitutes original CAL/model identities or reuses calibration groups')
            radii = (('BR', calibration.baseline_radius), ('SR', calibration.revision_radius))
            calibration_pin = calibration.identity
        points = relation_point_values(self.relation_fit, feature.values, feature.disposition,
            factor_values=factor_values, family_id=family_id)
        by_method = dict(points)
        policies = tuple(matched_forecast_policy(method, by_method[method], dict(radii).get(method),
            calibrated=calibration is not None) for method in ('BR', 'SR'))
        return SelectedE4ForecastSeal(record_id, programme, root_id, group_id, source, coordinate, cutoff,
            self.frozen, self.revision_model.identity, self.baseline_model.identity, self.target.identity,
            by_method['SR'], by_method['BR'], feature_pin, feature.physical_forecast, points,
            policies, calibration_pin, radii, phase, 'SR')


@dataclass(frozen=True, slots=True)
class SelectedE4ForecastSeal(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/forecast-seal"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    programme: ObjectIdentity
    case_id: str
    independent_group_id: str
    source: ObjectIdentity
    coordinate: ObjectIdentity
    cutoff: InformationCutoff
    frozen_models: ObjectIdentity
    revision_model: ObjectIdentity
    baseline_model: ObjectIdentity
    target: ObjectIdentity
    revision_predictions: tuple[Decimal | None, ...]
    baseline_predictions: tuple[Decimal | None, ...]
    causal_feature: ObjectIdentity | None = None
    physical_forecast: ObjectIdentity | None = None
    relation_points: tuple[tuple[str, tuple[Decimal | None, ...]], ...] = ()
    policies: tuple[MatchedForecastPolicy, ...] = ()
    calibration: ObjectIdentity | None = None
    model_radii: tuple[tuple[str, Decimal | None], ...] = ()
    phase: str | None = None
    admission_owner: str | None = None

    def __post_init__(self):
        from .selected_e4_methods import SelectedE4FrozenRevision
        from .records import ScheduledSource
        from empirical_lawhood.kernel.time import CausalPhase
        for value in (self.record_id, self.case_id, self.independent_group_id):
            validate_stable_id(value)
        r.exact_pin(self.programme, SelectedE4PhaseProgramme)
        r.exact_pin(self.frozen_models, SelectedE4FrozenRevision)
        r.exact_pin(self.source, ScheduledSource)
        r.exact_pin(self.coordinate, MatrixParameterCoordinate)
        matched = self.target.object_schema == E4MatchedRelationTarget.SCHEMA
        r.exact_pin(self.target, E4MatchedRelationTarget if matched else ScheduledRevisionTarget)
        for value in (self.revision_model, self.baseline_model):
            if matched:
                require_matched_model_reference(value)
            else:
                r.exact_pin(value, ScheduledRevisionFittedModel)
        if self.revision_model.object_schema != self.baseline_model.object_schema:
            raise ValueError('selected E4 forecast mixes old-K and curve model contracts')
        if (type(self.cutoff) is not InformationCutoff or self.cutoff.phase is not CausalPhase.PRE_ACTION
                or self.cutoff.cutoff_id != 'cutoff.' + self.case_id):
            raise ValueError('selected E4 forecast changes its actual pre-action physical cutoff')
        validate_record_fields(self.cutoff)
        if matched:
            from .selected_e4_native_records import SelectedE4ProtectedFeature, SelectedE4ProtectedMechanicalForecast
            r.exact_pin(self.causal_feature, SelectedE4ProtectedFeature)
            r.exact_pin(self.physical_forecast, SelectedE4ProtectedMechanicalForecast)
            calibrated = self.phase == 'CONFIRMATION'
            if (self.phase not in ('CALIBRATION', 'CONFIRMATION') or self.admission_owner != 'SR'
                    or (self.calibration is not None) != calibrated
                    or tuple(method for method, _ in self.model_radii) != (('BR', 'SR') if calibrated else ())
                    or tuple(method for method, _ in self.relation_points) != RELATION_METHODS
                    or tuple(policy.method_key for policy in self.policies) != ('BR', 'SR')):
                raise ValueError('matched E4 forecast changes its fixed accounts, separate CAL or SR decision owner')
            if calibrated:
                r.exact_pin(self.calibration, SelectedE4PublicCalibration)
            for _, radius in self.model_radii:
                if radius is not None:
                    validate_decimal(radius, field_name='original E4 calibration radius', minimum=Decimal(0))
            for _, points in self.relation_points:
                if postprocess_log_points(points) != points:
                    raise ValueError('matched E4 forecast changes its nonnegative cumulative point curves')
            points = dict(self.relation_points)
            expected = tuple(matched_forecast_policy(method, points[method], dict(self.model_radii).get(method), calibrated=calibrated)
                for method in ('BR', 'SR'))
            if ((self.revision_predictions, self.baseline_predictions) != (points['SR'], points['BR']) or self.policies != expected):
                raise ValueError('matched E4 forecast substitutes the consumed SR/BR points or their upper curves')
            return
        if any((self.causal_feature, self.physical_forecast, self.relation_points, self.policies, self.calibration,
                self.model_radii, self.phase, self.admission_owner)):
            raise ValueError('closed E4 forecast invents an amended causal account or bound')
        for values in (self.revision_predictions, self.baseline_predictions):
            if type(values) is not tuple or len(values) != 30 or any(type(value) is not Decimal or not value.is_finite() for value in values):
                raise ValueError('selected closed E4 forecast drops its original paired thirty endpoints')

    @property
    def identity(self):
        return _record_pin(self)


@dataclass(frozen=True, slots=True)
class SelectedE4CalibrationSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/calibration-specification"
    VERSION: ClassVar[str] = '2.0.0'
    specification_id: str
    development_programme: ObjectIdentity
    calibration_programme: ObjectIdentity
    nomination: ObjectIdentity
    frozen_models: ObjectIdentity
    alpha: Decimal
    score_rule: str

    def __post_init__(self):
        from .selected_e4_methods import SelectedE4RevisionNomination, SelectedE4FrozenRevision
        validate_stable_id(self.specification_id)
        for value, schema, version in ((self.development_programme,r.SelectedE3E4DevelopmentProgramme.SCHEMA,r.SelectedE3E4DevelopmentProgramme.VERSION),
                (self.calibration_programme,SelectedE4PhaseProgramme.SCHEMA,SelectedE4PhaseProgramme.VERSION),
                (self.nomination,SelectedE4RevisionNomination.SCHEMA,SelectedE4RevisionNomination.VERSION),
                (self.frozen_models,SelectedE4FrozenRevision.SCHEMA,SelectedE4FrozenRevision.VERSION)):
            _pin(value,schema,version)
        if (type(self.alpha) is not Decimal or not self.alpha.is_finite() or not 0 < self.alpha < 1
                or self.score_rule not in (SCORE_RULE, RELATION_SCORE_RULE)
                or self.score_rule == RELATION_SCORE_RULE and self.alpha != Decimal('.05')):
            raise ValueError("selected E4 calibration changes its explicit whole-group score or coverage level")

    @property
    def identity(self):
        return _record_pin(self, "specification_id")


@dataclass(frozen=True, slots=True)
class SelectedE4PublicCalibration(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/public-calibration"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    original: ObjectIdentity
    specification: SelectedE4CalibrationSpecification
    target: ObjectIdentity
    revision_model: ObjectIdentity
    baseline_model: ObjectIdentity
    group_ids: tuple[str, ...]
    rank: int
    revision_radius: Decimal | None
    baseline_radius: Decimal | None
    relation_fit: ObjectIdentity | None = None

    def __post_init__(self):
        from empirical_lawhood.runtime.experimental_statistics import calibration_rank
        from .selected_e4_methods import SelectedE4Calibration
        validate_stable_id(self.record_id)
        r.exact_pin(self.original, SelectedE4Calibration)
        if type(self.specification) is not SelectedE4CalibrationSpecification:
            raise TypeError("selected public calibration retains the actual frozen method specification")
        validate_record_fields(self.specification)
        matched = self.specification.score_rule == RELATION_SCORE_RULE
        r.exact_pin(self.target, E4MatchedRelationTarget if matched else ScheduledRevisionTarget)
        for model in (self.revision_model, self.baseline_model):
            if matched:
                require_matched_model_reference(model)
            else:
                r.exact_pin(model, ScheduledRevisionFittedModel)
        if self.revision_model.object_schema != self.baseline_model.object_schema:
            raise ValueError('selected E4 calibration mixes old-K and curve model contracts')
        if matched:
            r.exact_pin(self.relation_fit, E4MatchedRelationFit)
        elif self.relation_fit is not None:
            raise ValueError('closed E4 calibration cannot acquire a matched relation fit')
        if (type(self.group_ids) is not tuple or not self.group_ids or self.group_ids != tuple(sorted(set(self.group_ids)))
                or type(self.rank) is not int or self.rank != calibration_rank(len(self.group_ids), self.specification.alpha)):
            raise ValueError("selected calibration summary changes complete original calibration groups or rank")
        for group in self.group_ids:
            validate_stable_id(group)
        for radius in (self.revision_radius, self.baseline_radius):
            if radius is not None and (type(radius) is not Decimal or not radius.is_finite() or radius < 0):
                raise ValueError("selected calibration summary changes its exact finite or unbounded radius")

    @property
    def identity(self):
        return _record_pin(self)

    @classmethod
    def from_calibration(cls, calibration, *, record_id):
        from .selected_e4_methods import SelectedE4Calibration
        if type(calibration) is not SelectedE4Calibration:
            raise TypeError("selected calibration public projection requires its actual original record")
        validate_record_fields(calibration)
        return cls(record_id, calibration.identity, calibration.specification, calibration.target,
            calibration.revision_model.identity, calibration.baseline_model.identity, calibration.group_ids,
            calibration.rank, calibration.revision_radius, calibration.baseline_radius, calibration.relation_fit)


@dataclass(frozen=True, slots=True)
class SelectedE4PrefixProjection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/prefix-projection"
    record_id: str
    original: ObjectIdentity
    source: ObjectIdentity
    root: MatrixProgrammeRoot
    cutoff_tick: int
    frame_sha256: str | None
    disposition: str

    def __post_init__(self):
        from .records import ScheduledSource
        validate_stable_id(self.record_id)
        if (type(self.original) is not ObjectIdentity or type(self.root) is not MatrixProgrammeRoot
                or type(self.cutoff_tick) is not int or self.cutoff_tick < 0
                or self.disposition not in ("AVAILABLE", "NO_ORIGIN", "UNEVALUABLE")
                or (self.disposition == "AVAILABLE") != (self.frame_sha256 is not None)):
            raise ValueError("selected observed prefix changes actual pre-cutoff projection")
        _pin(self.source,ScheduledSource.SCHEMA,ScheduledSource.VERSION)
        validate_record_fields(self.root)
        if self.frame_sha256 is not None and (len(self.frame_sha256) != 64 or any(value not in "0123456789abcdef" for value in self.frame_sha256)):
            raise ValueError("selected observed prefix changes exact original frame digest")

    @property
    def identity(self):
        return _record_pin(self)

    @classmethod
    def from_record(cls, prefix, *, record_id):
        if not isinstance(prefix, ScheduledCausalPrefix):
            raise TypeError("selected observed prefix projects an actual typed native causal record")
        validate_record_fields(prefix)
        return cls(record_id, identity(prefix), prefix.source, prefix.root, prefix.cutoff_tick, prefix.frame_sha256, prefix.disposition)


@dataclass(frozen=True, slots=True)
class SelectedE4ScoreProjection(CanonicalRecord):
    """Bounded paired endpoints derived once from an actual response score."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/score-projection"
    VERSION: ClassVar[str] = "3.0.0"
    record_id: str
    original: ObjectIdentity
    source: ObjectIdentity
    root_id: str
    independent_group_id: str
    role: str
    criterion: ObjectIdentity
    causal_prefix: ObjectIdentity
    error_forecast: ObjectIdentity
    disposition: str
    numerical_pass: bool
    paired_log_targets: tuple[Decimal | None, ...]
    target_contract: str = "PAIRED15"
    paired_errors: tuple[Decimal | None, ...] = ()

    def __post_init__(self):
        from .selected_e3_e4_records import selected_target_shape
        _, _, target_count = selected_target_shape(self.target_contract)
        for value in (self.record_id, self.root_id, self.independent_group_id):
            validate_stable_id(value)
        _pin(self.original, ScheduledResponseScore.SCHEMA, ScheduledResponseScore.VERSION)
        for value in (self.original, self.source, self.criterion, self.causal_prefix, self.error_forecast):
            if type(value) is not ObjectIdentity:
                raise TypeError("selected score projection retains exact original scientific pins")
            validate_record_fields(value)
        if (self.role not in tuple(value.value for value in MatrixProgrammeRole)
                or self.disposition not in ("FINITE", "PARTIAL", "NO_ORIGIN", "UNEVALUABLE", "NATIVE_CROSSCHECK_FAILED", "INSTRUMENT_UNRESOLVED")
                or type(self.numerical_pass) is not bool
                or self.disposition in ("FINITE", "PARTIAL") and not self.numerical_pass
                or self.disposition == "FINITE" and any(value is None for value in self.paired_log_targets)
                or self.disposition not in ("FINITE", "PARTIAL") and any(value is not None for value in self.paired_log_targets)
                or type(self.paired_log_targets) is not tuple
                or len(self.paired_log_targets) != target_count
                or any(value is not None and (type(value) is not Decimal or not value.is_finite() or value < 0)
                    for value in self.paired_log_targets)):
            raise ValueError("selected score projection changes paired30 targets or actual adverse outcome")
        block = 29 if self.target_contract == "MATCHED_FACTOR58" else 3
        if self.target_contract == 'MATCHED_FACTOR58':
            if type(self.paired_errors) is not tuple or len(self.paired_errors) != 58:
                raise ValueError('matched E4 score projection drops original-unit paired58 errors')
            for value in self.paired_errors:
                if value is not None:
                    validate_decimal(value, field_name='actual paired FACTOR error', minimum=Decimal(0))
            with localcontext() as context:
                context.prec = 60
                expected = tuple(None if value is None else (Decimal(1) + value).ln() for value in self.paired_errors)
            if expected != self.paired_log_targets:
                raise ValueError('matched E4 score projection changes original errors or their fixed log transform')
        elif self.paired_errors:
            raise ValueError('closed E4 score projection invents amended paired FACTOR errors')
        for start in (0, target_count // 2):
            for offset in range(0, target_count // 2, block):
                values = self.paired_log_targets[start + offset:start + offset + block]
                if any(value is not None and (values[index - 1] is None or value < values[index - 1])
                        for index, value in enumerate(values) if index):
                    raise ValueError("selected score projection loses cumulative-horizon missingness")

    @property
    def identity(self):
        return _record_pin(self)

    @classmethod
    def from_record(cls, score, protocol, panels, *, record_id):
        from .paired_target_reduction import paired_targets, target_contract, paired_factor_errors
        if not isinstance(score, ScheduledResponseScore):
            raise TypeError("selected score projection requires an actual typed original response score")
        validate_record_fields(score)
        if (score.source != protocol.public_source.source or score.root_id != protocol.public_source.root.root_id
                or score.independent_group_id != protocol.public_source.root.independent_group_id
                or score.criterion != protocol.criterion):
            raise ValueError("selected score projection changes original source, group or actual assay protocol")
        return cls(record_id, identity(score), score.source, score.root_id, score.independent_group_id, score.role,
            score.criterion, score.causal_prefix, score.error_forecast, score.disposition, score.numerical_pass,
            paired_targets(score, protocol, panels), target_contract(protocol),
            paired_factor_errors(score, protocol, panels) if target_contract(protocol) == 'MATCHED_FACTOR58' else ())


@dataclass(frozen=True, slots=True)
class SelectedE4CausalFeatureProjection(CanonicalRecord):
    """The original sealed matched features, with no outcome or authority claim."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-selected-e4/causal-feature-projection'
    record_id: str
    original_account: ObjectIdentity
    original_feature: ObjectIdentity
    source: ObjectIdentity
    prefix: ObjectIdentity
    root_id: str
    independent_group_id: str
    clock_id: str
    cutoff: Decimal
    disposition: str
    values: tuple[tuple[str, Decimal], ...]
    physical_forecast: ObjectIdentity
    fine_response_defect: Decimal | None

    def __post_init__(self):
        from .selected_e4_native_records import SelectedE4ProtectedAccountSeal, SelectedE4ProtectedFeature, SelectedE4ProtectedCausalPrefix, SelectedE4ProtectedMechanicalForecast
        for value in (self.record_id, self.root_id, self.independent_group_id, self.clock_id):
            validate_stable_id(value)
        kinds = ((r.SelectedE3E4AccountSeal, r.SelectedE3E4Feature, r.SelectedE3E4CausalPrefix, r.SelectedE3E4MechanicalForecast)
            if self.original_account.object_schema == r.SelectedE3E4AccountSeal.SCHEMA else
            (SelectedE4ProtectedAccountSeal, SelectedE4ProtectedFeature, SelectedE4ProtectedCausalPrefix, SelectedE4ProtectedMechanicalForecast))
        for value, kind in zip((self.original_account, self.original_feature, self.prefix, self.physical_forecast), kinds, strict=True):
            r.exact_pin(value, kind)
        from .records import ScheduledSource
        r.exact_pin(self.source, ScheduledSource)
        validate_decimal(self.cutoff, field_name='original causal cutoff', minimum=Decimal(0))
        if self.disposition not in ('AVAILABLE', 'NO_CAUSAL_ORIGIN', 'UNAVAILABLE', 'REFUSED'):
            raise ValueError('matched E4 feature projection changes original availability')
        validate_matched_features(self.values, self.disposition)
        if self.fine_response_defect is not None:
            validate_decimal(self.fine_response_defect, field_name='diagnostic FINE origin response defect', minimum=Decimal(0))

    @classmethod
    def from_account(cls, account):
        from .selected_e4_native_records import SelectedE4ProtectedAccountSeal
        if type(account) not in (r.SelectedE3E4AccountSeal, SelectedE4ProtectedAccountSeal):
            raise TypeError('matched E4 causal projection requires the actual original typed account')
        validate_record_fields(account)
        feature = account.feature
        if feature.physical_forecast is None:
            raise ValueError('matched E4 causal projection requires its actual pre-future mechanical dependency')
        return cls('causal-projection.' + feature.root_id, account.identity,
            ObjectIdentity.from_record(feature.feature_id, feature), feature.source, feature.prefix,
            feature.root_id, feature.independent_group_id, feature.clock_id, feature.cutoff, feature.disposition,
            feature.values, feature.physical_forecast, feature.fine_response_defect)


@dataclass(frozen=True, slots=True)
class SelectedE4ObservedCase(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/observed-case"
    VERSION: ClassVar[str] = "3.0.0"
    root_id: str
    source: ObjectIdentity
    group_id: str
    coordinate: MatrixParameterCoordinate
    causal_prefix: SelectedE4PrefixProjection | None
    score: SelectedE4ScoreProjection | None
    disposition: str
    numerical_disposition: str
    forecast: ObjectIdentity | None
    revision_forecast: ObjectIdentity | None
    original_log_points: tuple[tuple[str, tuple[Decimal | None, ...]], ...]
    target_contract: str = "PAIRED15"
    causal_feature: SelectedE4CausalFeatureProjection | None = None

    def __post_init__(self):
        from .selected_e3_e4_records import selected_target_shape
        methods, point_count, _ = selected_target_shape(self.target_contract)
        for value in (self.root_id, self.group_id):
            validate_stable_id(value)
        if (type(self.coordinate) is not MatrixParameterCoordinate
                or self.causal_prefix is not None and type(self.causal_prefix) is not SelectedE4PrefixProjection
                or self.score is not None and type(self.score) is not SelectedE4ScoreProjection
                or self.disposition not in ("COMPLETED", "FAILED", "UNENTERED", "UNKNOWN")
                or self.numerical_disposition not in ("SATISFIED", "VIOLATED", "UNEVALUABLE", "UNENTERED", "UNKNOWN")
                or tuple(method for method, _ in self.original_log_points) != methods):
            raise ValueError("selected observed case retains actual whole-unit adverse and three-account records")
        validate_record_fields(self.coordinate)
        for record in (self.causal_prefix, self.score):
            if record is not None:
                validate_record_fields(record)
        for _, points in self.original_log_points:
            if len(points) != point_count or any(value is not None and (type(value) is not Decimal or not value.is_finite()) for value in points):
                raise ValueError("selected observed case changes original three PRIMARY fifteen-point accounts")
        if self.score is not None and self.score.target_contract != self.target_contract:
            raise ValueError("selected E4 observed case changes its original paired target contract")
        if self.revision_forecast is not None:
            _pin(self.revision_forecast, SelectedE4ForecastSeal.SCHEMA, SelectedE4ForecastSeal.VERSION)
        if self.target_contract == 'MATCHED_FACTOR58':
            if (self.forecast is None) != (self.causal_feature is None):
                raise ValueError('matched E4 observation omits its actual sealed causal features')
            if self.causal_feature is not None:
                if type(self.causal_feature) is not SelectedE4CausalFeatureProjection:
                    raise TypeError('matched E4 observation requires its typed original feature projection')
                validate_record_fields(self.causal_feature)
                feature = self.causal_feature
                if ((feature.original_account, feature.source, feature.root_id, feature.independent_group_id,
                        feature.clock_id) != (self.forecast, self.source, self.root_id, self.group_id, self.coordinate.clock_id)
                        or self.causal_prefix is None or feature.prefix != self.causal_prefix.original
                        or feature.cutoff != self.coordinate.physical_time(self.causal_prefix.cutoff_tick)):
                    raise ValueError('matched E4 observation substitutes original account, feature source or causal cutoff')
        elif self.causal_feature is not None:
            raise ValueError('closed E4 observation cannot acquire amended causal features')


@dataclass(frozen=True, slots=True)
class SelectedE4ObservedData(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/observed-data"
    VERSION: ClassVar[str] = "2.0.0"
    record_id: str
    programme: ObjectIdentity
    reduction: ObjectIdentity
    cases: tuple[SelectedE4ObservedCase, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.programme) is not ObjectIdentity or self.programme.object_schema not in
                (r.SelectedE3E4DevelopmentProgramme.SCHEMA, SelectedE4PhaseProgramme.SCHEMA)
                or type(self.reduction) is not ObjectIdentity or self.reduction.object_schema not in
                (r.SelectedE3E4DevelopmentReduction.SCHEMA, NATIVE_REDUCTION_SCHEMA)
                or type(self.cases) is not tuple or any(type(value) is not SelectedE4ObservedCase for value in self.cases)
                or tuple(value.root_id for value in self.cases) != tuple(sorted({value.root_id for value in self.cases}))):
            raise ValueError("selected observed data changes original programme/reduction and assigned case ordering")
        for value in self.cases:
            validate_record_fields(value)

    @property
    def identity(self):
        return _record_pin(self)

    @classmethod
    def from_products(cls, programme, bank, reduction, prefixes, scores, *, record_id, accounts=()):
        if type(programme) is r.SelectedE3E4DevelopmentProgramme:
            r.validate_development_bank(programme, bank)
        else:
            validate_selected_phase_bank(programme, bank)
        if (reduction.programme != programme.identity or reduction.bank != bank.identity
                or tuple(value.root_id for value in reduction.cases) != tuple(value.root_id for value in programme.cases)):
            raise ValueError("selected observed data requires complete actual reducer products")
        prefixes, scores, accounts = dict(prefixes), dict(scores), dict(accounts)
        declared = {value.root_id for value in programme.cases}
        if set(prefixes) - declared or set(scores) - declared or set(accounts) - declared:
            raise ValueError("selected observed data adds unassigned source outcomes")
        cases = []
        index=bank.source_index()
        for case, result in zip(programme.cases, reduction.cases, strict=True):
            prefix = prefixes.get(case.root_id)
            source = bank.source(case.root_id,index=index)
            protocol, panels = bank.response_selection.validate_source(source)
            score = scores.get(case.root_id)
            score = None if score is None else SelectedE4ScoreProjection.from_record(
                score, protocol, panels, record_id="score-projection." + case.root_id)
            cases.append(SelectedE4ObservedCase(case.root_id, case.source, case.independent_group_id,
                source.coordinate, None if prefix is None else SelectedE4PrefixProjection.from_record(
                    prefix, record_id="projection." + case.root_id), score, result.disposition,
                result.numerical_disposition, result.forecast, getattr(result, "revision_forecast", None), result.original_log_points, result.target_contract,
                None if case.root_id not in accounts or result.target_contract != 'MATCHED_FACTOR58'
                else SelectedE4CausalFeatureProjection.from_account(accounts[case.root_id])))
        return cls(record_id, programme.identity, _record_pin(reduction), tuple(cases))


@dataclass(frozen=True, slots=True)
class SelectedE4ForecastBank(CanonicalRecord):
    """Complete compact pre-future seals, with original per-case identities."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/forecast-bank"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    programme: ObjectIdentity
    forecasts: tuple[SelectedE4ForecastSeal, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        _pin(self.programme,SelectedE4PhaseProgramme.SCHEMA,SelectedE4PhaseProgramme.VERSION)
        if (type(self.forecasts) is not tuple or any(type(value) is not SelectedE4ForecastSeal for value in self.forecasts)
                or tuple(value.case_id for value in self.forecasts) != tuple(sorted({value.case_id for value in self.forecasts}))
                or any(value.programme != self.programme for value in self.forecasts)):
            raise ValueError("selected forecast bank changes actual original pre-future seals")
        for value in self.forecasts:
            validate_record_fields(value)

    @property
    def identity(self):
        return _record_pin(self)


@dataclass(frozen=True, slots=True)
class SelectedE4RevisionExport(CanonicalRecord):
    """Bounded projection of the authentic DEV procedure and fitted values."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/revision-export"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    decision: SelectedE4PublicRevisionDecision
    models: SelectedE4PublicModels | None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.decision) is not SelectedE4PublicRevisionDecision:
            raise TypeError("selected revision export needs its actual public frozen branch")
        validate_record_fields(self.decision)
        if self.decision.fit_available != (self.models is not None):
            raise ValueError("selected revision export cannot invent models on an unentered branch")
        if self.models is not None:
            if type(self.models) is not SelectedE4PublicModels:
                raise TypeError("selected revision export needs actual typed fitted coefficients")
            validate_record_fields(self.models)
            if ((self.models.development, self.models.nomination, self.models.frozen,
                    self.models.revision_model.identity, self.models.baseline_model.identity) !=
                    (self.decision.development, self.decision.nomination, self.decision.frozen,
                    self.decision.revision_model, self.decision.baseline_model)):
                raise ValueError("selected revision export substitutes original frozen fitted products")
            if self.decision.relation_fit != (None if self.models.relation_fit is None else self.models.relation_fit.identity):
                raise ValueError('selected E4 export changes the exact original matched fit')

    @property
    def identity(self):
        return _record_pin(self)

    @classmethod
    def from_products(cls, development, nomination, frozen, *, record_id):
        decision = SelectedE4PublicRevisionDecision.from_products(development, nomination, frozen, record_id=record_id + ".decision")
        models = None if not decision.fit_available else SelectedE4PublicModels.from_products(
            development, nomination, frozen, record_id=record_id + ".models")
        return cls(record_id, decision, models)


@dataclass(frozen=True, slots=True)
class SelectedE4OriginalCalibrationSummary(CanonicalRecord):
    """Original E3 radius and scope, without asserting applicability to E4."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/original-e3-calibration-summary"
    record_id: str
    original_package: ObjectIdentity
    calibration: ObjectIdentity
    specification: ObjectIdentity
    allocation: ObjectIdentity
    models: ObjectIdentity
    model_freeze: ObjectIdentity
    calibrated_freeze: ObjectIdentity
    group_ids: tuple[str, ...]
    alpha: Decimal
    rank: int
    radius: Decimal | None
    applicability: str = "ORIGINAL_E3_SCOPE_ONLY_E4_APPLICABILITY_UNEVALUABLE"

    def __post_init__(self):
        from empirical_lawhood.runtime.experimental_statistics import calibration_rank
        validate_stable_id(self.record_id)
        for value in (self.original_package, self.calibration, self.specification, self.allocation,
                self.models, self.model_freeze, self.calibrated_freeze):
            if type(value) is not ObjectIdentity:
                raise TypeError("original E3 summary retains exact original scientific identities")
            validate_record_fields(value)
        if (type(self.group_ids) is not tuple or not self.group_ids or self.group_ids != tuple(sorted(set(self.group_ids)))
                or type(self.alpha) is not Decimal or not self.alpha.is_finite() or not 0 < self.alpha < 1
                or type(self.rank) is not int or self.rank != calibration_rank(len(self.group_ids), self.alpha)
                or self.radius is not None and (type(self.radius) is not Decimal or not self.radius.is_finite() or self.radius < 0)
                or self.applicability != "ORIGINAL_E3_SCOPE_ONLY_E4_APPLICABILITY_UNEVALUABLE"):
            raise ValueError("original E3 summary changes complete original rank/scope or invents an E4 calibration warrant")

    @property
    def identity(self):
        return _record_pin(self)

    @classmethod
    def from_package(cls, package, *, record_id):
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_package import selected_frozen_package_types
        if type(package) not in selected_frozen_package_types():
            raise TypeError("original E3 summary requires the authentic full original package")
        validate_record_fields(package)
        calibration = package.calibration
        return cls(record_id, package.identity, identity(calibration), package.specification.identity,
            package.allocation.identity, identity(package.models), identity(package.model_freeze), identity(package.calibrated_freeze),
            tuple(group for group, _, _ in calibration.scores), package.specification.calibration_alpha,
            calibration.rank, calibration.radius)
