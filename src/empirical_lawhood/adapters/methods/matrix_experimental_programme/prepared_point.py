# SPDX-License-Identifier: MPL-2.0
"""Seedless prepared-source point predictions from an unchanged fitted model.

Recipe feature interpretations are supplied scientific premises, not inferred
from an old schedule label. Original E4 calibration never grants a bound for
these different prepared subjects. Publication chronology and applicability
remain obligations of the owning complete programme.
"""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from hashlib import sha256
from typing import ClassVar

import numpy as np

from empirical_lawhood.adapters.methods.matrix_factor_lifetime.products import validate_diagnostics
from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_joint_v2 import points
from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import FEATURES
from empirical_lawhood.adapters.methods.matrix_factor_response.response_population_statistics import STRATA
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import FAMILY_MAP, ScheduledForecastDesign, ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity as original_identity
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_sha256, validate_stable_id

from .preparation_records import MatrixPreparationSource, initial_state_identity, coupling_recipe_identity
from .prepared_prefix import MatrixPreparedCausalPrefix, MatrixPreparedFactorWitness, MatrixPreparedFrameAssessment, identity
from .records import MatrixFrozenConsumerPackage


UNBOUNDED = "POINT_ONLY_CROSS_PREPARATION_APPLICABILITY_NOT_ASSESSED"


@dataclass(frozen=True, slots=True)
class MatrixPreparedPublicSource(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-public-source"
    source: ObjectIdentity
    original: ScheduledPublicSource
    recipe: ObjectIdentity
    initial: ObjectIdentity

    def __post_init__(self):
        if (type(self.source) is not ObjectIdentity or self.source.object_schema != MatrixPreparationSource.SCHEMA
                or type(self.original) is not ScheduledPublicSource or type(self.recipe) is not ObjectIdentity
                or not coupling_recipe_identity(self.recipe) or type(self.initial) is not ObjectIdentity
                or not initial_state_identity(self.initial)):
            raise ValueError("prepared public source changes its actual recipe, shared initial state or original allocation")
        self.original.__post_init__()

    @classmethod
    def from_source(cls, source):
        if type(source) is not MatrixPreparationSource:
            raise ValueError("prepared predictor requires its own original prepared scientific subject")
        return cls(source.identity, source.original, source.recipe.identity, source.initial.identity)


@dataclass(frozen=True, slots=True)
class MatrixPreparedRecipeInterpretation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-recipe-interpretation"
    recipe: ObjectIdentity
    family_id: str
    scientific_premise: ObjectIdentity

    def __post_init__(self):
        if (type(self.recipe) is not ObjectIdentity or not coupling_recipe_identity(self.recipe)
                or self.family_id not in STRATA or type(self.scientific_premise) is not ObjectIdentity):
            raise ValueError("prepared recipe requires an explicit frozen feature interpretation and scientific premise")


@dataclass(frozen=True, slots=True)
class MatrixPreparedPointDesign(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-point-design"
    record_id: str
    package: MatrixFrozenConsumerPackage
    original_forecast: ScheduledForecastDesign
    sources: tuple[MatrixPreparedPublicSource, ...]
    interpretations: tuple[MatrixPreparedRecipeInterpretation, ...]
    standing: str = UNBOUNDED

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.package) is not MatrixFrozenConsumerPackage or type(self.original_forecast) is not ScheduledForecastDesign
                or self.standing != UNBOUNDED or type(self.sources) is not tuple or not self.sources
                or any(type(row) is not MatrixPreparedPublicSource for row in self.sources)
                or tuple(row.source.object_id for row in self.sources) != tuple(sorted({row.source.object_id for row in self.sources}))
                or type(self.interpretations) is not tuple or any(type(row) is not MatrixPreparedRecipeInterpretation for row in self.interpretations)
                or tuple(row.recipe.object_id for row in self.interpretations) != tuple(sorted({row.recipe.object_id for row in self.interpretations}))
                or {row.recipe for row in self.sources} != {row.recipe for row in self.interpretations}):
            raise ValueError("prepared point design omits exact sources or supplied recipe feature interpretations")
        self.package.__post_init__()
        self.original_forecast.__post_init__()
        frozen = self.original_forecast
        if (frozen.model != self.package.component("model") or frozen.criterion != self.package.component("criterion")
                or frozen.training_record.future_regime_reservation != self.package.reservation
                or frozen.model_record.reservation != self.package.reservation):
            raise ValueError("prepared point design changes the frozen package/model/criterion or original pre-fit reservation")
        for public in self.sources:
            public.__post_init__()
            original = public.original
            if (original.reservation != self.package.reservation or original.policy.origin_sector != "Y"
                    or original.policy.factor_rule.identity != frozen.criterion_record.factor_rule
                    or original.coordinate.primary_view.timestep != frozen.criterion_record.primary_timestep
                    or original.root.independent_group_id in self.package.training_unit_ids):
                raise ValueError("prepared point design crosses original reserved source, fitted groups, feature rule or clock")

    @property
    def identity(self):
        return identity(self)

    @property
    def model(self):
        return self.original_forecast.model

    @property
    def training_spec(self):
        return self.original_forecast.training_spec

    def family(self, public):
        if type(public) is not MatrixPreparedPublicSource or public not in self.sources:
            raise ValueError("prepared prediction substitutes its exact per-arm source and allocation scope")
        return next(row.family_id for row in self.interpretations if row.recipe == public.recipe)


@dataclass(frozen=True, slots=True)
class MatrixPreparedPointFeature(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-point-feature"
    record_id: str
    source: ObjectIdentity
    prefix: ObjectIdentity
    design: ObjectIdentity
    root_id: str
    independent_group_id: str
    family_id: str
    clock_id: str
    cutoff: Decimal
    frame_sha256: str | None
    disposition: str
    values: tuple[tuple[str, Decimal], ...]

    def __post_init__(self):
        for value in (self.record_id, self.root_id, self.independent_group_id, self.clock_id):
            validate_stable_id(value)
        if (self.source.object_schema != MatrixPreparationSource.SCHEMA or self.prefix.object_schema != MatrixPreparedCausalPrefix.SCHEMA
                or self.design.object_schema != MatrixPreparedPointDesign.SCHEMA or self.family_id not in STRATA
                or self.disposition not in ("AVAILABLE", "NO_CAUSAL_ORIGIN", "UNAVAILABLE", "REFUSED")
                or (tuple(name for name, _ in self.values) != FEATURES if self.disposition == "AVAILABLE" else bool(self.values))):
            raise ValueError("prepared feature changes its exact causal source or full frozen feature grammar")
        validate_decimal(self.cutoff, field_name="prepared physical cutoff", minimum=Decimal(0))
        if self.frame_sha256 is not None:
            validate_sha256(self.frame_sha256)
        for _, value in self.values:
            validate_decimal(value, field_name="actual prepared causal feature", minimum=Decimal(0))


@dataclass(frozen=True, slots=True)
class MatrixPreparedMatchedFeature(CanonicalRecord):
    """Actual arm-specific causal operands, sealed after its mechanical chart."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-matched-feature"
    record_id: str
    source: ObjectIdentity
    prefix: ObjectIdentity
    witness: ObjectIdentity
    protocol: ObjectIdentity
    mechanical: ObjectIdentity
    root_id: str
    independent_group_id: str
    family_id: str
    clock_id: str
    cutoff: Decimal
    frame_sha256: str | None
    disposition: str
    values: tuple[tuple[str, Decimal], ...]
    fine_d_lin: Decimal | None

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_prediction import validate_matched_features
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseProtocol
        from .prepared_forecast import MatrixPreparedMechanicalForecast

        for value in (self.record_id, self.root_id, self.independent_group_id, self.clock_id):
            validate_stable_id(value)
        for pin, owner in ((self.source, MatrixPreparationSource), (self.prefix, MatrixPreparedCausalPrefix),
                (self.witness, MatrixPreparedFactorWitness), (self.protocol, ScheduledResponseProtocol),
                (self.mechanical, MatrixPreparedMechanicalForecast)):
            if type(pin) is not ObjectIdentity or (pin.object_schema, pin.object_version) != (owner.SCHEMA, owner.VERSION):
                raise ValueError("matched prepared feature loses its original causal/mechanical operand edition")
            pin.__post_init__()
        if (self.family_id not in STRATA or self.disposition not in ("AVAILABLE", "NO_CAUSAL_ORIGIN", "UNAVAILABLE", "REFUSED")
                or self.disposition == "AVAILABLE" and self.frame_sha256 is None):
            raise ValueError("matched prepared feature changes its factual family, origin or availability")
        validate_matched_features(self.values, self.disposition)
        validate_decimal(self.cutoff, field_name="actual prepared physical cutoff", minimum=Decimal(0))
        if self.frame_sha256 is not None:
            validate_sha256(self.frame_sha256)
        if self.fine_d_lin is not None:
            validate_decimal(self.fine_d_lin, field_name="diagnostic fine origin defect", minimum=Decimal(0))

    @property
    def identity(self):
        return identity(self)


def matched_causal_feature(public, protocol, causal, witness, mechanical, causal_raw, diagnostic_raw, mechanical_raw, *,
        record_id, curve_primary=False):
    """Read actual received prefixes and the arm's frozen chart; no assay future."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_prediction import matched_causal_feature_values
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseProtocol
    from .prepared_forecast import MatrixPreparedMechanicalForecast

    if (type(public) is not MatrixPreparedPublicSource or type(protocol) is not ScheduledResponseProtocol
            or type(causal) is not MatrixPreparedCausalPrefix or type(witness) is not MatrixPreparedFactorWitness
            or type(mechanical) is not MatrixPreparedMechanicalForecast):
        raise TypeError("matched prepared feature requires its exact original causal and mechanical products")
    for record in (public, protocol, causal, witness, mechanical):
        record.__post_init__()
    original = public.original
    if (protocol.public_source != original or causal.source != public.source or witness.source != public.source
            or mechanical.source != public.source or mechanical.causal != identity(causal)
            or mechanical.original_protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
            or mechanical.mechanical_model != ObjectIdentity.from_record(protocol.mechanical_model.model_id, protocol.mechanical_model)
            or mechanical.arrays.preparation != causal.preparation or witness.preparation != causal.preparation
            or witness.numerical != causal.numerical or causal.witness != identity(witness)
            or causal.policy != original_identity(original.policy) or witness.policy != causal.policy
            or causal.cutoff_tick != original.policy.cutoff_tick):
        raise ValueError("matched prepared feature substitutes its actual source, handoff, witness or state-conditioned chart")
    arrays = decode_matrix_arrays(causal_raw, causal.arrays)
    diagnostics = decode_matrix_arrays(diagnostic_raw, witness.arrays)
    frozen = decode_matrix_arrays(mechanical_raw, mechanical.arrays)
    if any(name.endswith("innovations") for name in arrays):
        raise ValueError("matched prepared feature receives forbidden future noise")
    disposition, values, fine_defect = matched_causal_feature_values(protocol,
        prefix_disposition=causal.disposition, prefix_frame_sha256=causal.frame_sha256, traces=witness.traces,
        causal_arrays=arrays, diagnostics=diagnostics, frozen_arrays=frozen, curve_primary=curve_primary)
    return MatrixPreparedMatchedFeature(record_id, public.source, identity(causal), identity(witness),
        ObjectIdentity.from_record(protocol.protocol_id, protocol), identity(mechanical), original.root.root_id,
        original.root.independent_group_id, FAMILY_MAP[original.coordinate.family_id], original.root.clock_id,
        original.coordinate.physical_time(causal.cutoff_tick), causal.frame_sha256, disposition, values, fine_defect)


@dataclass(frozen=True, slots=True)
class MatrixPreparedPointSeal(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-point-seal"
    record_id: str
    feature: MatrixPreparedPointFeature
    package: ObjectIdentity
    model: ObjectIdentity
    criterion: ObjectIdentity
    raw_log_error_points: tuple[Decimal | None, ...]
    log_error_points: tuple[Decimal | None, ...]
    log_error_uppers: tuple[Decimal | None, ...]
    radius: Decimal | None
    standing: str = UNBOUNDED

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.feature) is not MatrixPreparedPointFeature or self.package.object_schema != MatrixFrozenConsumerPackage.SCHEMA
                or self.standing != UNBOUNDED or self.radius is not None or self.log_error_uppers != (None,) * 15
                or len(self.raw_log_error_points) != 15 or len(self.log_error_points) != 15):
            raise ValueError("prepared point seal imports a calibration bound or thins full15 endpoints")
        expected = []
        for start in range(0, 15, 3):
            prior, missing = Decimal(0), False
            for value in self.raw_log_error_points[start:start + 3]:
                if value is not None:
                    validate_decimal(value, field_name="raw model point")
                missing = missing or value is None
                if not missing:
                    prior = max(prior, value)
                expected.append(None if missing else prior)
        if (self.log_error_points != tuple(expected) or self.feature.disposition != "AVAILABLE"
                and any(value is not None for value in (*self.raw_log_error_points, *self.log_error_points))):
            raise ValueError("prepared point seal reverses horizons or invents finite nonuse predictions")


def causal_feature(design, public, causal, witness, frames, causal_raw, diagnostic_raw, *, record_id):
    """Read only authenticated seedless causal operands; never refit or eigensolve."""
    family = design.family(public)
    original, policy = public.original, public.original.policy
    if (type(causal) is not MatrixPreparedCausalPrefix or type(witness) is not MatrixPreparedFactorWitness
            or type(frames) is not MatrixPreparedFrameAssessment or causal.source != public.source
            or witness.source != public.source or frames.source != public.source or causal.witness != identity(witness)
            or causal.frame_assessment != identity(frames) or frames.witness != identity(witness)
            or causal.policy != original_identity(policy) or witness.policy != original_identity(policy)
            or causal.cutoff_tick != policy.cutoff_tick or causal.preparation != witness.preparation or causal.numerical != witness.numerical
            or frames.numerical_design != original_identity(policy.factor_numerical_design)
            or causal.arrays.producers != tuple(sorted((public.source, causal.preparation, identity(witness), identity(frames)), key=lambda row: row.object_id))):
        raise ValueError("prepared point feature substitutes its exact causal source/frame/policy boundary")
    arrays, diagnostics = decode_matrix_arrays(causal_raw, causal.arrays), decode_matrix_arrays(diagnostic_raw, witness.arrays)
    if any(name.endswith("innovations") for name in arrays):
        raise ValueError("prepared public feature receives forbidden future/seed operands")
    disposition = "NO_CAUSAL_ORIGIN" if causal.disposition == "NO_ORIGIN" else "UNAVAILABLE"
    values = ()
    if causal.disposition == "AVAILABLE" and frames.numerical_pass:
        try:
            coordinate, tick = original.coordinate, causal.cutoff_tick
            if coordinate.member.mass_x != coordinate.member.mass_y:
                raise ValueError("frozen feature grammar has one potential mass")
            window, cadence = design.original_forecast.training_record.feature_window_ticks, design.original_forecast.training_record.feature_cadence_ticks
            selected = tuple(range(max(0, tick - window), tick + 1, cadence))
            if len(selected) < 2 or selected[-1] != tick:
                raise ValueError("prepared feature omits frozen trailing window or cadence")
            trace = next(row for row in witness.traces if (row.view, row.sector) == ("PRIMARY", "Y"))
            validate_diagnostics({name: diagnostics["primary_y_" + name] for name in
                ("ticks", "available", "identifiable", "spectrum", "projector", "basis", "factor", "aligned_factor")}, trace, policy.factor_rule)
            observed = {row.tick: row for row in trace.observations}
            samples = tuple(observed[at] for at in selected)
            if any(row.status != "AVAILABLE" or row.identifiable is not True or row.alignment_ambiguous for row in samples):
                raise ValueError("prepared feature loses causal identified window")
            angles = tuple(row.adjacent_angle_degrees for row in samples[1:])
            if any(type(value) is not Decimal or not value.is_finite() or value < 0 for value in angles):
                raise ValueError("prepared feature lacks actual continuity diagnostics")
            for view, multiplier in (("primary", 1), ("fine", 2)):
                if (not np.array_equal(arrays[view + "_ticks"], np.arange(multiplier * tick + 1, dtype="<i8"))
                        or not np.array_equal(arrays[view + "_alpha_tilde"][-1], np.asarray(coordinate.couplings(multiplier * tick, refinement=multiplier), dtype="<f8"))):
                    raise ValueError("prepared feature changes actual restored coupling or paired clock")
            spectrum, alpha = diagnostics["primary_y_spectrum"][-1], arrays["primary_alpha_tilde"][-1]
            if sha256(arrays["frame"].tobytes()).hexdigest() != causal.frame_sha256 or not np.isfinite(spectrum).all():
                raise ValueError("prepared feature changes actual frame or full15 spectrum")
            last = samples[-1]
            context = {"alpha-x": Decimal(repr(float(alpha[0]))), "alpha-y": Decimal(repr(float(alpha[1]))),
                "bath-temperature": coordinate.primary_view.bath_temperature, "friction": coordinate.primary_view.friction_gamma,
                "cross-gamma": coordinate.member.cross_coupling_gamma, "potential-m": coordinate.member.mass_x,
                "cutoff": coordinate.physical_time(tick),
                **{"family-" + label.rsplit(".", 1)[1]: Decimal(family == label) for label in STRATA[1:]},
                "largest-y-rate": Decimal(repr(float(spectrum[-1]))),
                "third-fourth-y-gap": Decimal(repr(float(spectrum[3] - spectrum[2]))),
                "associative-leakage": last.associative_leakage, "lie-leakage": last.lie_leakage,
                "factor-fit-angle": last.factor_fit_angle_degrees, "trailing-angle": max(angles)}
            with localcontext() as context_precision:
                context_precision.prec = 50
                context["slow-y-mean"] = sum(Decimal(repr(float(value))) for value in spectrum[:3]) / 3
                for name, label in (("positions", "position"), ("momenta", "momentum")):
                    for sector, at in (("x", 0), ("y", 1)):
                        norm = Decimal(repr(float(np.linalg.norm(arrays["primary_" + name][-1, at]))))
                        context[label + "-" + sector + "-norm"] = (Decimal(1) + norm).ln()
            for value in context.values():
                validate_decimal(value, field_name="prepared causal feature", minimum=Decimal(0))
            values, disposition = tuple(sorted(context.items())), "AVAILABLE"
        except (ValueError, TypeError, KeyError, StopIteration):
            disposition = "REFUSED"
    return MatrixPreparedPointFeature(record_id, public.source, identity(causal), design.identity, original.root.root_id,
        original.root.independent_group_id, family, original.root.clock_id, original.coordinate.physical_time(policy.cutoff_tick),
        causal.frame_sha256, disposition, values)


def forecast(design, public, causal, feature, *, record_id):
    family = design.family(public)
    original = public.original
    if (type(feature) is not MatrixPreparedPointFeature or feature.source != public.source or causal.source != public.source
            or feature.prefix != identity(causal) or feature.design != design.identity or feature.family_id != family
            or (feature.root_id, feature.independent_group_id, feature.clock_id) !=
                (original.root.root_id, original.root.independent_group_id, original.root.clock_id)
            or feature.cutoff != original.coordinate.physical_time(original.policy.cutoff_tick)
            or feature.frame_sha256 != causal.frame_sha256 or feature.disposition == "AVAILABLE" and causal.disposition != "AVAILABLE"):
        raise ValueError("prepared point forecast changes original source/group/clock or frozen recipe interpretation")
    raw, point = points(design, design.original_forecast.model_record, feature)
    return MatrixPreparedPointSeal(record_id, feature, design.package.identity, design.model, design.original_forecast.criterion,
        raw, point, (None,) * 15, None)
