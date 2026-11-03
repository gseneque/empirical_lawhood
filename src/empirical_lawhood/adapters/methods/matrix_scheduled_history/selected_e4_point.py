# SPDX-License-Identifier: MPL-2.0
"""Bounded E4 revision points for prepared E5/E6 sources.

Both unchanged paired model outputs are retained. Unsupported grid coordinates
produce explicit nonuse endpoints; they neither select an E3 substitute nor
prevent an independently eligible functional assay. Carried calibration pins
retain their original scope and supply no downstream uncertainty warrant.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_point import MatrixPreparedMatchedFeature, MatrixPreparedPublicSource
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_prefix import MatrixPreparedCausalPrefix, identity
from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_records import coupling_recipe_identity
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.runtime.experimental_statistics import StandardizedRidgeParameters, predict_standardized_ridge

from .programme_records import ScheduledProgrammeFactor
from .records import identity as original_identity
from .programme_selection import ScheduledRevisionTarget, ScheduledRevisionTuning, physical_grid_features
from .selected_e4_programme import SelectedE4PublicCalibration, SelectedE4PublicModels, _pin
from .e4_structural_prediction import E4MatchedRelationFit, E4MatchedRelationTarget, RELATION_METHODS, relation_point_values
from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_prediction import (
    MatchedForecastPolicy, matched_forecast_policy, postprocess_log_points,
)

POINT_ONLY = "POINT_ONLY_DOWNSTREAM_UNCERTAINTY_UNEVALUABLE"
TRANSPORT = "EMPIRICAL_FROZEN_E4_TRANSPORT_NO_CALIBRATION_GUARANTEE"


@dataclass(frozen=True, slots=True)
class SelectedE4PointModels(CanonicalRecord):
    """Actual coefficients/transforms and original pins, without source rosters."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/point-models"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    original: ObjectIdentity
    development_nomination: ObjectIdentity
    frozen: ObjectIdentity
    revision_model: ObjectIdentity
    baseline_model: ObjectIdentity
    target: ScheduledRevisionTarget | E4MatchedRelationTarget
    factors: tuple[ScheduledProgrammeFactor, ...]
    revision_tuning: ScheduledRevisionTuning | None
    baseline_tuning: ScheduledRevisionTuning | None
    revision_parameters: tuple[StandardizedRidgeParameters, ...]
    baseline_parameters: tuple[StandardizedRidgeParameters, ...]
    relation_fit: E4MatchedRelationFit | None = None

    def __post_init__(self):
        from .programme_selection import ScheduledRevisionFittedModel
        from .selected_e4_methods import SelectedE4RevisionNomination, SelectedE4FrozenRevision
        validate_stable_id(self.record_id)
        _pin(self.original, SelectedE4PublicModels.SCHEMA, SelectedE4PublicModels.VERSION)
        _pin(self.development_nomination, SelectedE4RevisionNomination.SCHEMA, SelectedE4RevisionNomination.VERSION)
        _pin(self.frozen, SelectedE4FrozenRevision.SCHEMA, SelectedE4FrozenRevision.VERSION)
        if self.relation_fit is not None:
            if (type(self.relation_fit) is not E4MatchedRelationFit or type(self.target) is not E4MatchedRelationTarget
                    or self.revision_tuning is not None or self.baseline_tuning is not None
                    or self.revision_parameters or self.baseline_parameters):
                raise ValueError('matched downstream models require their complete original relation without substituted parameters')
            self.relation_fit.__post_init__()
            self.target.__post_init__()
            models = {model.method_key: model for model in self.relation_fit.models}
            selected = self.relation_fit.selection
            if ((self.revision_model, self.baseline_model) != (models['SR'].identity, models['BR'].identity)
                    or any(models[method].parameters is None for method in ('SR', 'BR'))
                    or tuple(axis.factor_id for axis in self.factors) != ('temperature', 'friction', 'coupling')
                    or tuple(axis.center for axis in self.factors) !=
                        (selected.nominal_temperature, selected.nominal_friction, selected.nominal_coupling)
                    or any(type(axis) is not ScheduledProgrammeFactor or axis.scale != 'LOG'
                        or axis.low * 2 != axis.center or axis.high != axis.center * 2 for axis in self.factors)):
                raise ValueError('matched downstream models change the frozen SR/BR coefficients or physical feature scales')
            for axis in self.factors:
                axis.__post_init__()
            return
        for pin in (self.revision_model, self.baseline_model):
            _pin(pin, ScheduledRevisionFittedModel.SCHEMA)
        if (type(self.target) is not ScheduledRevisionTarget or type(self.factors) is not tuple
                or tuple(axis.factor_id for axis in self.factors) != ("temperature", "friction", "coupling")
                or any(type(axis) is not ScheduledProgrammeFactor for axis in self.factors)):
            raise ValueError("selected downstream point changes its actual frozen target or physical grid")
        for record in (self.target, *self.factors):
            record.__post_init__()
        for tuning, parameters in ((self.revision_tuning, self.revision_parameters), (self.baseline_tuning, self.baseline_parameters)):
            if (type(tuning) is not ScheduledRevisionTuning or type(parameters) is not tuple or len(parameters) != 30
                    or any(type(value) is not StandardizedRidgeParameters or value.coefficients is None
                        or len(value.coefficients) != len(tuning.feature_names) + 1 or value.fitted_rows != value.training_rows for value in parameters)):
                raise ValueError("selected downstream point changes actual complete paired fitted parameters")
            tuning.__post_init__()
            for value in parameters:
                value.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    @classmethod
    def from_models(cls, models, *, record_id):
        if type(models) is not SelectedE4PublicModels:
            raise TypeError("selected point payload derives from actual authenticated public E4 models")
        models.__post_init__()
        if models.relation_fit is not None:
            return cls(record_id, models.identity, models.nomination, models.frozen, models.revision_model.identity,
                models.baseline_model.identity, models.target, models.development_design.factors,
                None, None, (), (), models.relation_fit)
        return cls(record_id, models.identity, models.nomination, models.frozen, models.revision_model.identity,
            models.baseline_model.identity, models.target, models.development_design.factors,
            models.revision_model.tuning, models.baseline_model.tuning,
            models.revision_model.parameters, models.baseline_model.parameters)

    def grid_features(self, coordinate):
        if type(coordinate) is not MatrixParameterCoordinate:
            raise TypeError("selected point requires its exact typed physical coordinate")
        coordinate.__post_init__()
        values = (coordinate.primary_view.bath_temperature, coordinate.primary_view.friction_gamma,
            coordinate.member.cross_coupling_gamma)
        corners = all(value in (axis.low, axis.high) for axis, value in zip(self.factors, values, strict=True))
        center = all(value == axis.center for axis, value in zip(self.factors, values, strict=True))
        return physical_grid_features(self.factors, values) if corners or center else None

    def predict(self, coordinate, *, feature=None):
        self.__post_init__()
        if self.relation_fit is not None:
            if type(coordinate) is not MatrixParameterCoordinate or feature is None:
                raise TypeError('matched downstream predictions require the actual single-case coordinate and causal features')
            coordinate.__post_init__()
            points = dict(relation_point_values(self.relation_fit, feature.values, feature.disposition,
                factor_values=(coordinate.primary_view.bath_temperature, coordinate.primary_view.friction_gamma,
                    coordinate.member.cross_coupling_gamma), family_id=coordinate.family_id))
            return ('PREDICTED' if all(value is not None for method in ('SR', 'BR') for value in points[method]) else 'UNEVALUABLE',
                points['SR'], points['BR'])
        features = self.grid_features(coordinate)
        if features is None:
            return ("UNSUPPORTED_DECLARED_GRID", (None,) * 30, (None,) * 30)
        results = tuple(tuple(predict_standardized_ridge(value, tuple(features[name] for name in tuning.feature_names))
            for value in parameters) for tuning, parameters in ((self.revision_tuning, self.revision_parameters),
                (self.baseline_tuning, self.baseline_parameters)))
        return ("PREDICTED", *results)


@dataclass(frozen=True, slots=True)
class SelectedE4RevisionPoint(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/revision-point"
    VERSION: ClassVar[str] = "2.0.0"
    record_id: str
    nomination: ObjectIdentity
    models: ObjectIdentity
    original_calibration: ObjectIdentity | None
    source: ObjectIdentity
    recipe: ObjectIdentity
    coordinate: ObjectIdentity
    causal_prefix: ObjectIdentity
    cutoff: InformationCutoff
    frame_sha256: str | None
    disposition: str
    revision_predictions: tuple[Decimal | None, ...]
    baseline_predictions: tuple[Decimal | None, ...]
    uncertainty_status: str = POINT_ONLY
    feature: MatrixPreparedMatchedFeature | None = None
    relation_points: tuple[tuple[str, tuple[Decimal | None, ...]], ...] = ()
    policies: tuple[MatchedForecastPolicy, ...] = ()
    frozen_calibration: ObjectIdentity | None = None
    model_radii: tuple[tuple[str, Decimal | None], ...] = ()
    reference_package: ObjectIdentity | None = None
    reference_points: tuple[tuple[str, tuple[Decimal | None, ...]], ...] = ()

    def __post_init__(self):
        from .selected_e4_methods import SelectedE4DownstreamNomination, SelectedE4Calibration
        validate_stable_id(self.record_id)
        _pin(self.nomination, SelectedE4DownstreamNomination.SCHEMA, SelectedE4DownstreamNomination.VERSION)
        _pin(self.models, SelectedE4PointModels.SCHEMA, SelectedE4PointModels.VERSION)
        if self.original_calibration is not None:
            _pin(self.original_calibration, SelectedE4Calibration.SCHEMA, SelectedE4Calibration.VERSION)
        _pin(self.source, "empirical-lawhood/matrix-experimental-programme/preparation-source")
        if not coupling_recipe_identity(self.recipe):
            raise ValueError("selected revision point requires an exact supported coupling recipe edition")
        self.recipe.__post_init__()
        _pin(self.coordinate, MatrixParameterCoordinate.SCHEMA)
        _pin(self.causal_prefix, MatrixPreparedCausalPrefix.SCHEMA)
        if (type(self.cutoff) is not InformationCutoff or self.cutoff.phase is not CausalPhase.PRE_ACTION
                or self.cutoff.cutoff_id != "cutoff." + self.source.object_id
                or self.disposition not in ("PREDICTED", "UNSUPPORTED_DECLARED_GRID", "NO_ORIGIN", "UNEVALUABLE")):
            raise ValueError("selected revision point changes actual pre-future source/nonuse or grants downstream uncertainty")
        self.cutoff.__post_init__()
        if self.frame_sha256 is not None and (len(self.frame_sha256) != 64
                or any(value not in "0123456789abcdef" for value in self.frame_sha256)):
            raise ValueError("selected revision point changes actual causal frame digest")
        if self.feature is not None:
            if (type(self.feature) is not MatrixPreparedMatchedFeature or self.uncertainty_status != TRANSPORT
                    or self.original_calibration is None or self.disposition == "UNSUPPORTED_DECLARED_GRID"
                    or tuple(method for method, _ in self.relation_points) != RELATION_METHODS
                    or tuple(policy.method_key for policy in self.policies) != ("BR", "SR")
                    or tuple(method for method, _ in self.model_radii) != ("BR", "SR")
                    or tuple(method for method, _ in self.reference_points) != ("B0", "S0")):
                raise ValueError("matched prepared point drops its original paired58 relation or transported bound policies")
            self.feature.__post_init__()
            _pin(self.frozen_calibration, SelectedE4PublicCalibration.SCHEMA, SelectedE4PublicCalibration.VERSION)
            from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_public import ConfiguredMatrixSelectedPublicPackage
            _pin(self.reference_package, ConfiguredMatrixSelectedPublicPackage.SCHEMA, ConfiguredMatrixSelectedPublicPackage.VERSION)
            if ((self.feature.source, self.feature.prefix, self.feature.clock_id, self.feature.cutoff, self.feature.frame_sha256) !=
                    (self.source, self.causal_prefix, self.cutoff.clock_id, self.cutoff.coordinate, self.frame_sha256)):
                raise ValueError("matched prepared point substitutes its actual causal handoff feature")
            for _, radius in self.model_radii:
                if radius is not None and (type(radius) is not Decimal or not radius.is_finite() or radius < 0):
                    raise ValueError("matched prepared point changes its frozen finite or vacuous E4 radius")
            points = dict(self.relation_points)
            for _, values in (*self.relation_points, *self.reference_points):
                if postprocess_log_points(values) != values:
                    raise ValueError("matched prepared point substitutes an unprocessed paired58 forecast")
            expected = tuple(matched_forecast_policy(method, points[method], dict(self.model_radii)[method], calibrated=True)
                for method in ("BR", "SR"))
            if ((self.revision_predictions, self.baseline_predictions) != (points['SR'], points['BR'])
                    or self.policies != expected or (self.disposition == "PREDICTED") !=
                        all(value is not None for method in ("SR", "BR") for value in points[method])
                    or self.feature.disposition != "AVAILABLE" and any(value is not None
                        for _, values in (*self.relation_points, *self.reference_points) for value in values)):
                raise ValueError("matched prepared point changes frozen SR/BR values, availability or model-specific admissions")
            return
        if (self.uncertainty_status != POINT_ONLY or self.relation_points or self.policies
                or self.frozen_calibration is not None or self.model_radii or self.reference_package is not None or self.reference_points):
            raise ValueError("closed point-only preparation cannot acquire a matched feature or transported bound")
        for values in (self.revision_predictions, self.baseline_predictions):
            if (type(values) is not tuple or len(values) != 30
                    or any((value is None) != (self.disposition != "PREDICTED") for value in values)
                    or any(value is not None and (type(value) is not Decimal or not value.is_finite()) for value in values)):
                raise ValueError("selected revision point changes raw paired30 model values or drops nonuse endpoints")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


def forecast_revision_prepared(models, public_source, causal, *, nomination, original_calibration, record_id,
        feature=None, calibration=None, reference_package=None):
    if (type(models) is not SelectedE4PointModels or type(public_source) is not MatrixPreparedPublicSource
            or type(causal) is not MatrixPreparedCausalPrefix):
        raise TypeError("selected downstream point needs exact prepared public source, causal record and bounded coefficients")
    for record in (models, public_source, causal):
        record.__post_init__()
    if causal.source != public_source.source or causal.policy != original_identity(public_source.original.policy):
        raise ValueError("selected revision point substitutes the original prepared source or causal policy")
    coordinate = public_source.original.coordinate
    cutoff = InformationCutoff("cutoff." + public_source.source.object_id, coordinate.clock_id, CausalPhase.PRE_ACTION,
        coordinate.physical_time(causal.cutoff_tick))
    if models.relation_fit is not None:
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_public import ConfiguredMatrixSelectedPublicPackage
        if (type(feature) is not MatrixPreparedMatchedFeature or type(calibration) is not SelectedE4PublicCalibration
                or type(reference_package) is not ConfiguredMatrixSelectedPublicPackage):
            raise TypeError("matched prepared prediction requires its actual mechanical feature, E4 calibration and original E3 references")
        feature.__post_init__()
        calibration.__post_init__()
        reference_package.__post_init__()
        reference_package.require_unused_groups((feature.independent_group_id,))
        original = public_source.original
        from .forecast import FAMILY_MAP
        if ((feature.source, feature.prefix, feature.root_id, feature.independent_group_id, feature.clock_id,
                feature.cutoff, feature.frame_sha256, feature.family_id) !=
                (public_source.source, identity(causal), original.root.root_id, original.root.independent_group_id,
                 original.root.clock_id, cutoff.coordinate, causal.frame_sha256, FAMILY_MAP[coordinate.family_id])
                or (calibration.original, calibration.specification.frozen_models, calibration.specification.nomination,
                    calibration.relation_fit, calibration.target, calibration.revision_model, calibration.baseline_model) !=
                    (original_calibration, models.frozen, models.development_nomination, models.relation_fit.identity,
                     models.target.identity, models.revision_model, models.baseline_model)
                or feature.independent_group_id in (*models.relation_fit.models[0].training_unit_ids, *calibration.group_ids)):
            raise ValueError("matched prepared prediction changes its actual handoff, frozen fit/CAL or disjoint downstream group")
        points = relation_point_values(models.relation_fit, feature.values, feature.disposition,
            factor_values=(coordinate.primary_view.bath_temperature, coordinate.primary_view.friction_gamma,
                coordinate.member.cross_coupling_gamma), family_id=coordinate.family_id)
        radii = (("BR", calibration.baseline_radius), ("SR", calibration.revision_radius))
        policies = tuple(matched_forecast_policy(method, dict(points)[method], dict(radii)[method], calibrated=True)
            for method in ("BR", "SR"))
        reference = dict(reference_package.predict(values=feature.values, disposition=feature.disposition))
        reference_points = tuple((method, reference[method]) for method in ('B0', 'S0'))
        disposition = ("PREDICTED" if all(value is not None for method in ("SR", "BR") for value in dict(points)[method])
            else "NO_ORIGIN" if causal.disposition == "NO_ORIGIN" else "UNEVALUABLE")
        return SelectedE4RevisionPoint(record_id, nomination, models.identity, original_calibration, public_source.source,
            public_source.recipe, ObjectIdentity.from_record(coordinate.coordinate_id, coordinate), identity(causal), cutoff,
            causal.frame_sha256, disposition, dict(points)['SR'], dict(points)['BR'], TRANSPORT,
            feature, points, policies, calibration.identity, radii, reference_package.identity, reference_points)
    if feature is not None or calibration is not None or reference_package is not None:
        raise ValueError("closed point-only preparation cannot substitute matched feature or calibration operands")
    if causal.disposition == "AVAILABLE":
        disposition, revision, baseline = models.predict(coordinate)
    else:
        disposition, revision, baseline = causal.disposition, (None,) * 30, (None,) * 30
    return SelectedE4RevisionPoint(record_id, nomination, models.identity, original_calibration, public_source.source,
        public_source.recipe, ObjectIdentity.from_record(coordinate.coordinate_id, coordinate), identity(causal),
        cutoff, causal.frame_sha256, disposition, revision, baseline)
