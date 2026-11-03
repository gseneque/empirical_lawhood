# SPDX-License-Identifier: MPL-2.0
"""Seedless E5/E6 point consumers for the actual selected E3 products.

These new contracts keep complete matched arms and original transfer reserves.
They do not promote the historical scheduled model or apply its uncertainty.
Source eligibility, original exposure, prepared-task receipts, forecast-before-
future custody and protected entry remain with their existing owning services.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

import numpy as np

from empirical_lawhood.adapters.methods.matrix_factor_lifetime.products import validate_diagnostics
from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_methods import METHODS
from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import FEATURES
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import causal_feature_values
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity as original_identity
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_sha256, validate_stable_id

from .preparation_records import MatrixCouplingRecipe, MatrixOriginalScheduleRecipe, coupling_recipe_types, is_baseline_recipe, validate_original_schedule_recipe
from .prepared_point import MatrixPreparedPublicSource, MatrixPreparedRecipeInterpretation
from .prepared_prefix import MatrixPreparedCausalPrefix, MatrixPreparedFactorWitness, MatrixPreparedFrameAssessment, identity
from .selected_package import (DOWNSTREAM_PHASES, POINT_ONLY, MatrixSelectedFrozenPackage,
    selected_frozen_package_types, validate_selected_package_calibration)
from .configured_selected_package import ConfiguredMatrixSelectedFrozenPackage


@dataclass(frozen=True, slots=True)
class MatrixSelectedPointDesign(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-point-design"
    record_id: str
    package: MatrixSelectedFrozenPackage | ConfiguredMatrixSelectedFrozenPackage
    phase: str
    expected_groups: int
    arms: tuple[tuple[str, MatrixCouplingRecipe | MatrixOriginalScheduleRecipe], ...]
    sources: tuple[tuple[str, MatrixPreparedPublicSource], ...]
    interpretations: tuple[MatrixPreparedRecipeInterpretation, ...]

    def __post_init__(self):
        self._validate(selected_frozen_package_types())

    def _validate(self, package_type):
        validate_stable_id(self.record_id)
        if (type(self.package) not in (package_type if type(package_type) is tuple else (package_type,)) or self.phase not in DOWNSTREAM_PHASES
                or type(self.expected_groups) is not int or self.expected_groups < 1
                or type(self.arms) is not tuple or tuple(arm for arm, _ in self.arms) != tuple(sorted({arm for arm, _ in self.arms}))
                or any(type(recipe) not in coupling_recipe_types() for _, recipe in self.arms)
                or type(self.sources) is not tuple or not self.sources
                or any(type(public) is not MatrixPreparedPublicSource for _, public in self.sources)
                or tuple(public.source.object_id for _, public in self.sources) != tuple(sorted({public.source.object_id for _, public in self.sources}))
                or type(self.interpretations) is not tuple or any(type(row) is not MatrixPreparedRecipeInterpretation for row in self.interpretations)):
            raise TypeError("selected point design requires its exact package and complete sorted seedless source/arm owners")
        self.package.__post_init__()
        recipes = dict(self.arms)
        expected_arms = {"E5_OPPORTUNITY": 3, "E5_CONFIRMATION": 2, "E6_TRANSFER": 1}[self.phase]
        if len(recipes) != expected_arms or sum(is_baseline_recipe(recipe) for recipe in recipes.values()) != 1:
            raise ValueError("selected point design changes the complete HOLD/fixed-recipe arm census")
        for arm, recipe in self.arms:
            validate_stable_id(arm)
            recipe.__post_init__()
        if len({recipe.identity for recipe in recipes.values()}) != len(recipes):
            raise ValueError("selected point design aliases different preparation arms")
        expected_interpretations = tuple(sorted((recipe.identity for recipe in recipes.values()), key=lambda row: row.object_id))
        if tuple(row.recipe for row in self.interpretations) != expected_interpretations:
            raise ValueError("selected point design omits exact explicit recipe feature interpretations")
        for interpretation in self.interpretations:
            interpretation.__post_init__()
        by_group, regimes = {}, {}
        role = {"E5_OPPORTUNITY": MatrixProgrammeRole.DEVELOPMENT, "E5_CONFIRMATION": MatrixProgrammeRole.CONFIRMATION,
            "E6_TRANSFER": MatrixProgrammeRole.WITHHELD_TRANSFER}[self.phase]
        measurement = self.package.specification.measurement
        for arm, public in self.sources:
            public.__post_init__()
            source, policy, coordinate = public.original, public.original.policy, public.original.coordinate
            source.root.__post_init__()
            coordinate.__post_init__()
            policy.__post_init__()
            if (arm not in recipes or public.recipe != recipes[arm].identity or source.root.role is not role
                    or policy.origin_sector != "Y" or policy.cutoff_tick != measurement.origin_tick
                    or recipes[arm].primary_steps != measurement.origin_tick
                    or coordinate.primary_view.timestep != measurement.primary_timestep
                    or coordinate.fine_view.timestep != measurement.fine_timestep):
                raise ValueError("selected point design changes source role, actual recipe, paired clocks or causal feature rule")
            validate_original_schedule_recipe(recipes[arm], coordinate, policy.cutoff_tick)
            group = source.root.independent_group_id
            if arm in by_group.setdefault(group, {}):
                raise ValueError("selected point design duplicates a nested arm of one whole group")
            by_group[group][arm] = public
            if regimes.setdefault(source.root.regime_id, {}).setdefault(group, source.coordinate) != source.coordinate:
                raise ValueError("selected point design reuses a whole group across physical coordinates")
        groups = tuple(sorted(by_group))
        self.package.require_unused_groups(groups)
        if any(set(rows) != set(recipes) for rows in by_group.values()):
            raise ValueError("selected point design thins the complete matched-arm denominator")
        for rows in by_group.values():
            first = next(iter(rows.values()))
            if any(public.original != first.original or public.initial != first.initial for public in rows.values()):
                raise ValueError("selected point design changes matched original starts, clocks or source between arms")
        if self.phase == "E6_TRANSFER":
            if (len(regimes) != 2 or any(len(rows) != self.expected_groups for rows in regimes.values())
                    or len(groups) != 2 * self.expected_groups
                    or any(public.original.reservation != self.package.prefit.reservation
                        or public.original.allocation != self.package.prefit.original_allocation for _, public in self.sources)):
                raise ValueError("selected point design changes its two separately retained original reserve regimes")
            self.package.require_reserved_transfer_groups(groups, reservation=self.package.prefit.reservation)
        elif len(groups) != self.expected_groups:
            raise ValueError("selected point design drops an assigned complete preparation group")

    @property
    def identity(self):
        return identity(self)

    def family(self, public):
        if public not in tuple(row for _, row in self.sources):
            raise ValueError("selected point design substitutes an unselected prepared source")
        return next(row.family_id for row in self.interpretations if row.recipe == public.recipe)


@dataclass(frozen=True, slots=True)
class MatrixSelectedPreparedFeature(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-prepared-feature"
    record_id: str
    design: ObjectIdentity
    public_source: MatrixPreparedPublicSource
    prefix: ObjectIdentity
    frame_sha256: str | None
    disposition: str
    values: tuple[tuple[str, Decimal], ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.design) is not ObjectIdentity or self.design.object_schema not in (MatrixSelectedPointDesign.SCHEMA,
                "empirical-lawhood/matrix-experimental-programme/selected-point-payload")
                or type(self.public_source) is not MatrixPreparedPublicSource or type(self.prefix) is not ObjectIdentity
                or (self.prefix.object_schema, self.prefix.object_version) != (MatrixPreparedCausalPrefix.SCHEMA, MatrixPreparedCausalPrefix.VERSION)
                or self.disposition not in ("AVAILABLE", "NO_CAUSAL_ORIGIN", "UNAVAILABLE", "REFUSED")
                or type(self.values) is not tuple
                or (tuple(name for name, _ in self.values) != FEATURES if self.disposition == "AVAILABLE" else bool(self.values))):
            raise ValueError("selected prepared feature changes its exact seedless source, prefix or full feature grammar")
        self.public_source.__post_init__()
        if self.frame_sha256 is not None:
            validate_sha256(self.frame_sha256)
        if self.disposition == "AVAILABLE" and (self.frame_sha256 is None
                or dict(self.values)["cutoff"] != self.public_source.original.coordinate.physical_time(self.public_source.original.policy.cutoff_tick)):
            raise ValueError("selected prepared feature loses actual admitted frame or physical cutoff")
        for _, value in self.values:
            validate_decimal(value, field_name="selected prepared seedless feature", minimum=Decimal(0))


def measure_selected_point(design, public, causal, witness, frames, causal_raw, diagnostic_raw, *, record_id):
    """Original scheduled feature equations on separately prepared prefix bytes."""
    from .selected_public import MatrixSelectedPointPayload
    if type(design) not in (MatrixSelectedPointDesign, MatrixSelectedPointPayload):
        raise TypeError("selected measurement requires its actual selected point design")
    design.__post_init__()
    family = design.family(public)
    policy = public.original.policy
    if (type(causal) is not MatrixPreparedCausalPrefix or type(witness) is not MatrixPreparedFactorWitness
            or type(frames) is not MatrixPreparedFrameAssessment or causal.source != public.source
            or witness.source != public.source or frames.source != public.source or causal.witness != identity(witness)
            or causal.frame_assessment != identity(frames) or frames.witness != identity(witness)
            or causal.policy != original_identity(policy) or witness.policy != original_identity(policy)
            or causal.cutoff_tick != policy.cutoff_tick or causal.preparation != witness.preparation or causal.numerical != witness.numerical
            or frames.numerical_design != original_identity(policy.factor_numerical_design)
            or causal.arrays.producers != tuple(sorted((public.source, causal.preparation, identity(witness), identity(frames)), key=lambda row: row.object_id))):
        raise ValueError("selected measurement substitutes actual prepared source/frame/policy ancestry")
    for record in (causal, witness, frames):
        record.__post_init__()
    arrays, diagnostics = decode_matrix_arrays(causal_raw, causal.arrays), decode_matrix_arrays(diagnostic_raw, witness.arrays)
    if any(name.endswith("innovations") for name in arrays):
        raise ValueError("selected prepared measurement receives forbidden future innovations")
    for trace in witness.traces:
        validate_diagnostics({name: diagnostics[trace.view.lower() + "_" + trace.sector.lower() + "_" + name]
            for name in ("ticks", "available", "identifiable", "spectrum", "projector", "basis", "factor", "aligned_factor")}, trace, policy.factor_rule)
    if not np.array_equal(arrays["fine_alpha_tilde"][-1], np.asarray(public.original.coordinate.couplings(2 * causal.cutoff_tick, refinement=2), dtype="<f8")):
        raise ValueError("selected measurement changes the actual restored FINE coupling")
    measurement = design.package.specification.measurement
    disposition, values = causal_feature_values(public.original.coordinate, policy,
        prefix_disposition=causal.disposition, prefix_frame_sha256=causal.frame_sha256, traces=witness.traces,
        causal_arrays=arrays, diagnostics=diagnostics, feature_window_ticks=measurement.feature_window_ticks,
        feature_cadence_ticks=measurement.feature_cadence_ticks)
    if disposition == "AVAILABLE" and not frames.numerical_pass:
        disposition, values = "REFUSED", ()
    if disposition == "AVAILABLE":
        # Recipe interpretations are explicit original premises. Changing an
        # interpretation changes this design; the source is never relabelled.
        values = tuple((name, Decimal(family.endswith("." + name.removeprefix("family-"))))
            if name.startswith("family-") else (name, value) for name, value in values)
    return MatrixSelectedPreparedFeature(record_id, design.identity, public, identity(causal), causal.frame_sha256, disposition, values)


@dataclass(frozen=True, slots=True)
class MatrixSelectedPointForecast(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-point-forecast"
    record_id: str
    design: ObjectIdentity
    feature: MatrixSelectedPreparedFeature
    package: ObjectIdentity
    original_calibration: ObjectIdentity
    log_points: tuple[tuple[str, tuple[Decimal | None, ...]], ...]
    uncertainty_status: str = POINT_ONLY

    def __post_init__(self):
        validate_stable_id(self.record_id)
        validate_selected_package_calibration(self.package, self.original_calibration)
        if (type(self.feature) is not MatrixSelectedPreparedFeature or self.design != self.feature.design
                or tuple(method for method, _ in self.log_points) != METHODS or self.uncertainty_status != POINT_ONLY):
            raise ValueError("selected point forecast changes original selected model or uncertainty scope")
        self.feature.__post_init__()
        for _, values in self.log_points:
            if len(values) != 15 or self.feature.disposition != "AVAILABLE" and values != (None,) * 15:
                raise ValueError("selected point forecast drops endpoints or invents finite nonuse predictions")
            for index, value in enumerate(values):
                if value is not None:
                    validate_decimal(value, field_name="selected cumulative log point", minimum=Decimal(0))
                    if index % 3 and (values[index - 1] is None or value < values[index - 1]):
                        raise ValueError("selected point forecast reverses within-description cumulative horizons")


def forecast_selected_point(design, feature, *, record_id):
    from .selected_public import MatrixSelectedPointPayload, calibration_identity, package_identity, point_values
    if type(design) not in (MatrixSelectedPointDesign, MatrixSelectedPointPayload) or type(feature) is not MatrixSelectedPreparedFeature:
        raise TypeError("selected point forecast requires its exact current design and measured feature")
    design.__post_init__()
    feature.__post_init__()
    family = design.family(feature.public_source)
    if feature.design != design.identity or feature.disposition == "AVAILABLE" and any(
            value != Decimal(family.endswith("." + name.removeprefix("family-"))) for name, value in feature.values if name.startswith("family-")):
        raise ValueError("selected point forecast substitutes its actual design or recipe feature interpretation")
    points = point_values(design.package, values=feature.values, disposition=feature.disposition)
    return MatrixSelectedPointForecast(record_id, design.identity, feature, package_identity(design.package),
        calibration_identity(design.package), points)
