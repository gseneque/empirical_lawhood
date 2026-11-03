# SPDX-License-Identifier: MPL-2.0
"""Lossless E4 revision/baseline handoff without invented transfer features.

The explicit calibration owner retains a maximum over nine coordinates and
thirty paired outputs per group. That scope is distinct from E3 max15. A new
physical coordinate outside the declared grid needs its own domain feature rule;
it cannot silently receive the old feature extractor's center code.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_response.records import PREDICTORS
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_records import ScheduledProgramme
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_selection import (
    ScheduledRevisionFrozenPackage, ScheduledRevisionNomination, revision_case_features,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_calibration import (
    SCORE_RULE, ScheduledRevisionCalibration, calibrate_revision, validate_revision_phase,
)
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.runtime.experimental_statistics import predict_standardized_ridge

from .selected_package import DOWNSTREAM_PHASES, POINT_ONLY, _units


@dataclass(frozen=True, slots=True)
class MatrixSelectedRevisionPackage(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-e4-revision-package"
    record_id: str
    development: ScheduledProgramme
    nomination: ScheduledRevisionNomination
    frozen: ScheduledRevisionFrozenPackage
    calibration_programme: ScheduledProgramme
    calibration: ScheduledRevisionCalibration
    upstream_fit_unit_ids: tuple[str, ...]
    selection_unit_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.calibration) is not ScheduledRevisionCalibration:
            raise TypeError("selected revision requires its actual typed independent paired-model calibration")
        validate_revision_phase(self.development, self.nomination, self.frozen, self.calibration_programme, phase="CALIBRATION")
        self.calibration.__post_init__()
        cal, spec = self.calibration, self.calibration.specification
        if ((spec.development_programme, spec.calibration_programme, spec.nomination, spec.frozen_models) !=
                (self.development.identity, self.calibration_programme.identity, self.nomination.identity, self.frozen.identity)
                or cal.revision_model != self.nomination.revision_model or cal.baseline_model != self.nomination.baseline_model
                or cal.target != self.nomination.specification.target.identity or cal.group_ids != self.calibration_programme.group_ids
                or spec.alpha != Decimal(1) - self.calibration_programme.confidence):
            raise ValueError("selected revision substitutes original models, joint freeze, target or complete calibration scope")
        for values in (self.upstream_fit_unit_ids, self.selection_unit_ids):
            _units(values, field="selected revision upstream use")
        if (not set(self.development.group_ids) <= set(self.upstream_fit_unit_ids)
                or not set(cal.group_ids) <= set(self.selection_unit_ids)):
            raise ValueError("selected revision omits actual fitted or calibrated whole groups")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    @property
    def calibration_method(self):
        return SCORE_RULE

    @property
    def endpoint_order(self):
        target = self.nomination.specification.target
        return tuple((view, description, tick) for view in target.numerical_views
            for description in PREDICTORS
            for tick in target.horizon_ticks)

    def require_unused_groups(self, group_ids):
        self.__post_init__()
        _units(group_ids, field="selected revision downstream groups")
        if not group_ids or set(group_ids).intersection((*self.upstream_fit_unit_ids, *self.selection_unit_ids)):
            raise ValueError("revision downstream groups overlap actual fitted or selected upstream whole units")


def adapt_e4_frozen_package(*, record_id, development, nomination, frozen, calibration_programme,
        calibration, reduction, data, forecasts, upstream_fit_unit_ids, selection_unit_ids):
    """Replay actual original scores/seals once at the domain handoff boundary.

    The resulting consumer carries frozen models, calibration and exact original
    identities. Raw calibration outcomes do not become point-predictor inputs.
    Custody/authority authentication remains with the owning API and worker.
    """
    if type(calibration) is not ScheduledRevisionCalibration:
        raise TypeError("revision handoff cannot replace actual calibration with a generic reference")
    expected = calibrate_revision(calibration.specification, development, nomination, frozen, calibration_programme,
        reduction, data, forecasts, record_id=calibration.record_id)
    if calibration != expected:
        raise ValueError("revision handoff changes original full paired calibration products")
    return MatrixSelectedRevisionPackage(record_id, development, nomination, frozen, calibration_programme,
        calibration, upstream_fit_unit_ids, selection_unit_ids)


def predict_revision_coordinate(package, coordinate):
    """Both unchanged original model outputs at an actually declared grid value.

    This is point arithmetic. It grants no new source admission, preparation or
    regime applicability and no application of the carried calibration radii.
    """
    if type(package) is not MatrixSelectedRevisionPackage or type(coordinate) is not MatrixParameterCoordinate:
        raise TypeError("selected revision prediction requires original typed package and physical coordinate")
    package.__post_init__()
    coordinate.__post_init__()
    factors = (coordinate.primary_view.bath_temperature, coordinate.primary_view.friction_gamma, coordinate.member.cross_coupling_gamma)
    case = next((row for row in package.development.cases if row.factor_values == factors), None)
    if case is None:
        raise ValueError("revision coordinate has no declared grid feature rule; a non-grid point cannot be relabelled as center")
    # Reuse the original feature owner on its original declared case. Only the
    # immutable physical feature vector is reused, not that case's observations.
    features = revision_case_features(package.development, case)
    return tuple((role, tuple(predict_standardized_ridge(parameters,
        tuple(features[name] for name in model.tuning.feature_names)) for parameters in model.parameters))
        for role, model in (("REVISION", package.calibration.revision_model), ("BASELINE", package.calibration.baseline_model)))


def require_revision_downstream_calibration(package, *, phase):
    if type(package) is not MatrixSelectedRevisionPackage:
        raise TypeError("revision calibration requires the exact selected package")
    package.__post_init__()
    if phase not in DOWNSTREAM_PHASES:
        raise ValueError("unknown downstream Matrix phase")
    raise ValueError(POINT_ONLY + ": original whole-nine-coordinate paired calibration does not establish downstream applicability")
