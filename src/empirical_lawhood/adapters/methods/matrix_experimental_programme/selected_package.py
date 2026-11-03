# SPDX-License-Identifier: MPL-2.0
"""Lossless selected E3 products for later Matrix domain consumers.

This adapter checks immutable scientific joins, not publication custody or
authority. Original calibration is retained with its original population and
estimand. Carrying it into a package supplies no preparation/transfer warrant.
The historical scheduled point design and its point-only records are unchanged.
"""

from dataclasses import dataclass
from decimal import Decimal
from types import SimpleNamespace
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_response import e3_numerical_methods as numerical
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_experiment_methods as e3
from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_specification import MatrixResponseErrorSpecification
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_experiment_inputs import ProtectedE3PreFitJoin
from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import FEATURES, FEATURE_BLOCKS
from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_prediction import MATCHED_FEATURE_BLOCKS, validate_matched_features
from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_fitting import MatchedEstimatorModel, MatchedCurveEstimatorModel
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.runtime.experimental_statistics import split_upper_calibration

DOWNSTREAM_PHASES = ("E5_OPPORTUNITY", "E5_CONFIRMATION", "E6_TRANSFER")
CALIBRATION_METHOD = "SPLIT_UPPER_MAX_POSITIVE_LOG1P_RESIDUAL_MAX_PAIRED_VIEWS_THEN_MAX15_PER_WHOLE_ROOT"
TRANSFORM = "ZERO_CLIP_THEN_CUMULATIVE_MAX_THEN_EXPM1"
POINT_ONLY = "POINT_ONLY_DOWNSTREAM_APPLICABILITY_NOT_ASSESSED"


def _units(rows, *, field):
    if type(rows) is not tuple or rows != tuple(sorted(set(rows))):
        raise ValueError(field + " requires the complete sorted unique whole-unit census")
    for row in rows:
        validate_stable_id(row)


@dataclass(frozen=True, slots=True)
class MatrixSelectedFrozenPackage(CanonicalRecord):
    """Exact original selected products, without a new fit or uncertainty claim.

    selection_unit_ids includes every known non-fit upstream use, including
    calibration, confirmation and any later model/recipe selection. Completeness
    of unreported exposure still needs the actual domain exposure assessment.
    """

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-e3-frozen-package"
    record_id: str
    specification: MatrixResponseErrorSpecification
    allocation: UnitAllocation
    prefit: ProtectedE3PreFitJoin
    models: e3.ProtectedE3ModelSet
    model_freeze: e3.ProtectedE3FrozenProducts
    calibration: e3.ProtectedE3Calibration
    calibrated_freeze: e3.ProtectedE3FrozenProducts
    selection_unit_ids: tuple[str, ...]

    def __post_init__(self):
        self._validate((MatrixResponseErrorSpecification, UnitAllocation, ProtectedE3PreFitJoin, e3.ProtectedE3ModelSet,
            e3.ProtectedE3FrozenProducts, e3.ProtectedE3Calibration, e3.ProtectedE3FrozenProducts), e3.freeze_protected_e3)

    def _validate(self, record_types, freeze):
        validate_stable_id(self.record_id)
        for value, kind in zip((self.specification, self.allocation, self.prefit, self.models,
                self.model_freeze, self.calibration, self.calibrated_freeze), record_types, strict=True):
            if type(value) is not kind:
                raise TypeError("selected package requires exact original protected E3 records")
            value.__post_init__()
        spec, allocation, models = self.specification, self.allocation, self.models
        if (spec.evidence_scope != "PROSPECTIVE_REQUIRED" or spec.calibration_target_view != "MAX_PAIRED_VIEWS"
                or tuple(sorted(allocation.role_counts)) != tuple(sorted(
                    (row.role.lower(), row.expected_units) for row in spec.populations))
                or (models.specification, models.allocation, models.reservation_join) !=
                    (spec.identity, allocation.identity, self.prefit.identity)
                or (self.prefit.specification, self.prefit.allocation) != (spec.identity, allocation.identity)
                or any(reference not in allocation.sources for reference in (
                    self.prefit.training_allocation, self.prefit.original_allocation,
                    self.prefit.reservation, self.prefit.native_specification))):
            raise ValueError("selected package changes original paired-view science, allocation or pre-fit reservation joins")
        publications = {key: artifact for key, artifact, _, _ in self.prefit.publications}
        for key, reference in (("allocation", self.prefit.original_allocation),
                ("reservation", self.prefit.reservation), ("roles", allocation.identity)):
            artifact = publications[key]
            if (artifact.payload_schema, artifact.sha256) != (reference.object_schema, reference.object_fingerprint):
                raise ValueError("selected package substitutes an original pre-fit publication")
        for model, selection in zip(models.models, spec.methods, strict=True):
            matched = getattr(spec.measurement, 'is_matched', False)
            blocks = MATCHED_FEATURE_BLOCKS if matched else FEATURE_BLOCKS
            expected_features = tuple(sorted(name for block in selection.feature_blocks for name in blocks[block]))
            if (model.method_key != selection.method_key or model.feature_names != expected_features
                    or model.training_unit_ids != allocation.unit_ids("train")):
                raise ValueError("selected package changes an actual estimator, feature mask or TRAIN census")
            if matched:
                if type(model) is not (MatchedCurveEstimatorModel if spec.is_curve_primary else MatchedEstimatorModel):
                    raise ValueError('selected matched package substitutes an original model type')
            else:
                for parameters in model.ridge_parameters:
                    if parameters is not None:
                        parameters.__post_init__()
        expected_model = freeze(spec, allocation, models, record_id=self.model_freeze.record_id)
        expected_calibrated = freeze(spec, allocation, models, record_id=self.calibrated_freeze.record_id,
            model_freeze=self.model_freeze, calibration=self.calibration)
        if self.model_freeze != expected_model or self.calibrated_freeze != expected_calibrated:
            raise ValueError("selected package substitutes its separately frozen model or calibration ancestry")
        calibration = self.calibration
        if (tuple(unit for unit, _, _ in calibration.scores) != allocation.unit_ids("calibration")
                or calibration.specification != spec.identity or calibration.allocation != allocation.identity):
            raise ValueError("selected package drops or substitutes complete original CAL roots")
        ranked = split_upper_calibration(tuple(score for _, score, _ in calibration.scores), spec.calibration_alpha)
        radius = None if ranked.radius.is_infinite() else ranked.radius
        if (calibration.rank, calibration.radius) != (ranked.rank, radius):
            raise ValueError("selected package changes the original max15 calibration rank or finite/infinite radius")
        _units(self.selection_unit_ids, field="selected package upstream use")
        required_use = set(allocation.unit_ids("calibration")) | set(allocation.unit_ids("evaluation"))
        reserves = set(allocation.unit_ids("transfer_nearby")) | set(allocation.unit_ids("transfer_shifted"))
        if not required_use <= set(self.selection_unit_ids) or reserves.intersection(self.selection_unit_ids):
            raise ValueError("selected package omits known upstream use or exposes an original transfer reserve")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    @property
    def training_unit_ids(self):
        return self.allocation.unit_ids("train")

    @property
    def calibration_method(self):
        return ('SEPARATE_S0_B0_SPLIT_UPPER_MAX_POSITIVE_LOG1P_RESIDUAL_PAIRED58_PER_WHOLE_ROOT'
            if getattr(self.specification.measurement, 'is_matched', False) else CALIBRATION_METHOD)

    @property
    def calibration_scope(self):
        """Original conditional scope; this is not a later-population warrant."""
        return self.specification.identity, self.allocation.identity, self.calibration.model_freeze

    @property
    def endpoint_order(self):
        if getattr(self.specification.measurement, 'is_matched', False):
            return tuple((view, 'FACTOR', horizon) for view in ('PRIMARY', 'FINE') for horizon in self.specification.measurement.horizons)
        return tuple((description, horizon) for description in self.specification.measurement.descriptions
            for horizon in self.specification.measurement.horizons)

    def require_unused_groups(self, group_ids):
        self.__post_init__()
        _units(group_ids, field="downstream groups")
        if not group_ids or set(group_ids).intersection((*self.training_unit_ids, *self.selection_unit_ids)):
            raise ValueError("downstream groups overlap an actual fitted or selected upstream whole unit")

    def require_reserved_transfer_groups(self, group_ids, *, reservation):
        self.require_unused_groups(group_ids)
        expected = tuple(sorted((*self.allocation.unit_ids("transfer_nearby"), *self.allocation.unit_ids("transfer_shifted"))))
        if reservation != self.prefit.reservation or group_ids != expected:
            raise ValueError("selected transfer drops or substitutes its complete original pre-fit reserve")

def adapt_e3_frozen_package(*, record_id, specification, allocation, prefit, models,
        model_freeze, calibration, calibrated_freeze, selection_unit_ids):
    return MatrixSelectedFrozenPackage(record_id, specification, allocation, prefit, models,
        model_freeze, calibration, calibrated_freeze, selection_unit_ids)


def predict_selected_points(package, *, values, disposition="AVAILABLE"):
    """Reuse exact original predictors without refitting or importing a bound."""
    if type(package) not in selected_frozen_package_types():
        raise TypeError("selected points require the exact selected protected E3 package")
    package.__post_init__()
    validate_selected_features(package.specification, values, disposition)
    return numerical.forecast_point_values(package.models.models, SimpleNamespace(values=values, disposition=disposition))


def validate_selected_features(specification, values, disposition):
    if disposition not in ('AVAILABLE', 'NO_CAUSAL_ORIGIN', 'UNAVAILABLE', 'REFUSED'):
        raise ValueError('selected prediction changes explicit causal availability')
    if getattr(specification.measurement, 'is_matched', False):
        validate_matched_features(values, disposition, curve_primary=specification.is_curve_primary)
        return
    if (disposition not in ("AVAILABLE", "NO_CAUSAL_ORIGIN", "UNAVAILABLE", "REFUSED")
            or type(values) is not tuple
            or (tuple(name for name, _ in values) != FEATURES if disposition == "AVAILABLE" else bool(values))):
        raise ValueError("selected prediction requires complete original seedless causal features or explicit nonuse")
    for _, value in values:
        validate_decimal(value, field_name="selected causal feature", minimum=Decimal(0))


def require_downstream_calibration(package, *, phase):
    """Fail closed until a domain assessor supports the new preparation/regime.

    Original calibration data remains in the package. It cannot be used as a
    downstream uncertainty bound by passing a record reference or a new label.
    """
    if type(package) not in selected_frozen_package_types():
        raise TypeError("downstream calibration requires the exact selected package")
    package.__post_init__()
    if phase not in DOWNSTREAM_PHASES:
        raise ValueError("unknown downstream Matrix phase")
    raise ValueError(POINT_ONLY + ": original max15 calibration does not establish preparation or regime applicability")


def selected_frozen_package_types():
    from .configured_selected_package import ConfiguredMatrixSelectedFrozenPackage
    return MatrixSelectedFrozenPackage, ConfiguredMatrixSelectedFrozenPackage


def validate_selected_package_calibration(package, calibration):
    """Keep exact legacy/configured package and calibration families together."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_methods import ConfiguredProtectedE3Calibration
    from .configured_selected_package import ConfiguredMatrixSelectedFrozenPackage
    families = ((MatrixSelectedFrozenPackage, e3.ProtectedE3Calibration),
        (ConfiguredMatrixSelectedFrozenPackage, ConfiguredProtectedE3Calibration))
    if type(package) is not ObjectIdentity or type(calibration) is not ObjectIdentity:
        raise TypeError("selected package/calibration require exact scientific identities")
    package.__post_init__(); calibration.__post_init__()
    if not any((package.object_schema, package.object_version, calibration.object_schema, calibration.object_version) ==
            (full.SCHEMA, full.VERSION, cal.SCHEMA, cal.VERSION) for full, cal in families):
        raise ValueError("selected package mixes original scientific record families or revisions")
