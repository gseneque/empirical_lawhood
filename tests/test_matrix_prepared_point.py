# SPDX-License-Identifier: MPL-2.0
"""Prepared source scopes never acquire original E4 calibration authority."""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from hashlib import sha256

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import preparation_science, prepared_prefix
from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_point as method
from empirical_lawhood.adapters.methods.matrix_experimental_programme.records import PACKAGE_ROLES, MatrixFrozenConsumerPackage
from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import FEATURES
from empirical_lawhood.adapters.methods.matrix_factor_response.response_population_statistics import STRATA
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from tests import test_matrix_coupling_preparation as preparation_fixture
from tests import test_matrix_scheduled_history_bindings as original_fixture
from tests.test_matrix_factor_confirmation_eligibility import stock
from tests.test_matrix_later_programme import ref
from tests.test_matrix_parameter_history import source as original_parameter_source
from tests.test_matrix_scheduled_history import scheduled


def selected_scope(tmp_path):
    plane, prior = stock.__wrapped__(tmp_path, original_parameter_source().provenance)
    # Existing frozen model/publication fixture; it computes no fit or native
    # experiment. Retain its original reservation and Y-feature source grammar.
    plane, sources, config = original_fixture.bank.__wrapped__(scheduled.__wrapped__((plane, prior)))
    source, initial, coarse, bridge, _ = preparation_fixture.selected.__wrapped__((plane, sources[0]))
    package = MatrixFrozenConsumerPackage("package.literal-prepared-point", ref("freeze.literal-prepared-point"),
        tuple((role, config.forecast_design.model if role == "model" else config.forecast_design.criterion if role == "criterion"
            else ref("point-package." + role)) for role in PACKAGE_ROLES), source.original.reservation,
        ("unit.original-training",), ("unit.original-selection",), "OBSERVATION_ASSISTED_SEALED_BEFORE_FUTURE")
    public = method.MatrixPreparedPublicSource.from_source(source)
    design = method.MatrixPreparedPointDesign("design.literal-prepared-point", package, config.forecast_design, (public,),
        (method.MatrixPreparedRecipeInterpretation(source.recipe.identity, STRATA[1], ref("premise.literal-feature-interpretation")),))
    return source, initial, coarse, bridge, sources[0].allocation, design, plane


@pytest.fixture
def case(tmp_path):
    source, initial, coarse, bridge, _, design, _ = selected_scope(tmp_path)
    public = method.MatrixPreparedPublicSource.from_source(source)
    arrays = preparation_science.propagate_preparation(source, initial, coarse_innovations=coarse, bridge_innovations=bridge)
    raw, preparation = preparation_science.preparation_array_product(source, initial, arrays, artifact_id="array.literal-point-preparation")
    numerical = preparation_science.assess_preparation_arrays(source, initial, preparation, arrays, assessment_id="numerical.literal-point")
    diagnostic_raw, witness = prepared_prefix.measure_prepared_prefix(source, initial, preparation, numerical, raw,
        artifact_id="array.literal-point-diagnostics")
    frames = prepared_prefix.check_prepared_frames(source, initial, preparation, numerical, witness, raw, diagnostic_raw)
    causal_raw, causal = prepared_prefix.project_prepared_prefix(source, initial, preparation, numerical, witness, frames, raw,
        diagnostic_raw, artifact_id="array.literal-point-causal")
    return design, public, causal, witness, frames, causal_raw, diagnostic_raw


def test_prepared_point_is_seedless_frozen_and_unbounded_with_complete_nonuse(case, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("prepared point feature entered a fit, native producer, RNG or eigensolve")

    from empirical_lawhood.adapters.methods.matrix_factor_response import response_error_prediction
    monkeypatch.setattr(np.linalg, "eigh", forbidden)
    monkeypatch.setattr(np.random, "Generator", forbidden)
    monkeypatch.setattr(preparation_science, "acquire_preparation", forbidden)
    monkeypatch.setattr(response_error_prediction, "fit_error_model", forbidden)
    monkeypatch.setattr(response_error_prediction, "fit_scheduled_error_model", forbidden)
    feature = method.causal_feature(*case, record_id="feature.literal-prepared-point")
    design, public, causal, *_ = case
    seal = method.forecast(design, public, causal, feature, record_id="seal.literal-prepared-point")
    assert feature.source == public.source and feature.family_id == STRATA[1]
    assert seal.log_error_uppers == (None,) * 15 and seal.radius is None and seal.standing == method.UNBOUNDED
    assert len(seal.log_error_points) == 15
    assert not any(word in public.canonical_bytes().decode() for word in ("effective_seed", "generator_state", "streams"))
    if causal.disposition != "AVAILABLE":
        assert seal.log_error_points == (None,) * 15
    assert decode_canonical_bytes(design.canonical_bytes(), type(design), maximum_bytes=None) == design


@pytest.mark.parametrize("damage", ("recipe-interpretation", "source", "model", "reservation", "clock"))
def test_prepared_point_refuses_missing_interpretation_or_crossed_frozen_scope(case, damage):
    design, public, *_ = case
    with pytest.raises(ValueError, match="interpretation|source|package|reservation|clock|physical conditions"):
        if damage == "recipe-interpretation":
            replace(design, interpretations=())
        elif damage == "source":
            design.family(replace(public, source=replace(public.source, object_fingerprint="f" * 64)))
        elif damage == "model":
            package = replace(design.package, components=tuple((role, ref("changed.frozen-model") if role == "model" else value)
                for role, value in design.package.components))
            replace(design, package=package)
        elif damage == "reservation":
            replace(design, sources=(replace(public, original=replace(public.original,
                reservation=replace(public.original.reservation, object_fingerprint="f" * 64))),))
        else:
            changed = replace(public.original.coordinate, primary_view=replace(public.original.coordinate.primary_view,
                timestep=public.original.coordinate.primary_view.timestep * 2))
            replace(design, sources=(replace(public, original=replace(public.original, coordinate=changed)),))


def test_prepared_point_cannot_import_finite_e4_radius_or_nonuse_feature(case):
    design, public, causal, *_ = case
    feature = method.causal_feature(*case, record_id="feature.literal-point-unbounded")
    seal = method.forecast(design, public, causal, feature, record_id="seal.literal-point-unbounded")
    with pytest.raises(ValueError, match="calibration bound"):
        replace(seal, radius=D(0), log_error_uppers=(D(1),) * 15)
    if causal.disposition != "AVAILABLE":
        invented = replace(feature, disposition="AVAILABLE", values=tuple((name, D(0)) for name in FEATURES))
        with pytest.raises(ValueError, match="source/group/clock"):
            method.forecast(design, public, causal, invented, record_id="seal.forbidden-point-origin")


def test_prepared_point_authenticates_selected_causal_and_diagnostic_bytes(case):
    with pytest.raises(ValueError):
        method.causal_feature(*case[:-1], case[-1][:-1], record_id="feature.forbidden-point-bytes")
    design, public, causal, witness, frames, causal_raw, diagnostic_raw = case
    with pytest.raises(ValueError, match="boundary"):
        method.causal_feature(design, public, causal, witness, replace(frames, record_id="frames.unselected-point"),
            causal_raw, diagnostic_raw, record_id="feature.forbidden-point-frame")


def available_prepared_operands(tmp_path, *, future_ticks=128, origin_sector=None):
    """Literal supplied-noise history shared by causal and dense method controls."""
    from types import SimpleNamespace
    from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
    from tests.test_matrix_factor_confirmation_eligibility import publish

    source, _, _, _, _, design, plane = selected_scope(tmp_path)
    rule = replace(source.original.policy.factor_rule, lattice=tuple(range(33)))
    policy = replace(source.original.policy, cutoff_tick=32, factor_rule=rule,
        origin_sector=source.original.policy.origin_sector if origin_sector is None else origin_sector)
    coordinate = replace(source.coordinate, autonomous_ticks=source.coordinate.autonomous_ticks + future_ticks,
        observation_ticks=(0, 16, 32, source.coordinate.total_ticks + future_ticks))
    pauli = np.asarray(([[0, 1], [1, 0]], [[0, -1j], [1j, 0]], [[1, 0], [0, -1]]), dtype="<c16")
    frame = np.asarray([np.kron(row, np.eye(2)) / 2 for row in pauli], dtype="<c16")
    positions = np.stack((frame, frame)).astype("<c16")
    # A supplied small noncommuting perturbation resolves the exact SU(2)
    # null spectrum while preserving the original strict nonnegative feature
    # grammar. No spectral clipping or changed scientific threshold is used.
    positions[:, 0] += .001 * np.kron(np.eye(2), pauli[0])
    positions[:, 1] += .0013 * np.kron(np.eye(2), pauli[1])
    initial, members = encode_matrix_arrays({"positions": positions, "momenta": np.zeros_like(positions)})
    initial_state = replace(source.initial, array_artifact=replace(source.initial.array_artifact,
        artifact_id="array.literal-point-available-initial", sha256=sha256(initial).hexdigest(), size_bytes=len(initial)), members=members)
    recipe = replace(source.recipe, primary_steps=32, half_tick_couplings=(source.initial.alpha_tilde,) * 65, kind="HOLD")
    source = replace(source, original=replace(source.original, policy=policy, coordinate=coordinate),
        root=replace(source.root, coordinate=coordinate_identity(coordinate)), recipe=recipe, initial=initial_state)
    criterion = replace(design.original_forecast.criterion_record, factor_rule=rule.identity)
    frozen = replace(design.original_forecast, criterion_record=criterion,
        criterion_publication=publish(plane, criterion, "published.literal-point-available-criterion"))
    package = replace(design.package, components=tuple((role, frozen.criterion if role == "criterion" else value)
        for role, value in design.package.components))
    public = method.MatrixPreparedPublicSource.from_source(source)
    design = replace(design, package=package, original_forecast=frozen, sources=(public,),
        interpretations=(replace(design.interpretations[0], recipe=recipe.identity),))
    innovations = np.zeros((32, 2, 3, 4, 4), dtype="<c16")
    arrays = preparation_science.propagate_preparation(source, initial, coarse_innovations=innovations, bridge_innovations=innovations)
    raw, preparation = preparation_science.preparation_array_product(source, initial, arrays, artifact_id="array.literal-point-available-preparation")
    numerical = preparation_science.assess_preparation_arrays(source, initial, preparation, arrays, assessment_id="assessment.literal-point-available")
    diagnostic_raw, witness = prepared_prefix.measure_prepared_prefix(source, initial, preparation, numerical, raw,
        artifact_id="array.literal-point-available-diagnostics")
    frames = prepared_prefix.check_prepared_frames(source, initial, preparation, numerical, witness, raw, diagnostic_raw)
    causal_raw, causal = prepared_prefix.project_prepared_prefix(source, initial, preparation, numerical, witness, frames, raw,
        diagnostic_raw, artifact_id="array.literal-point-available-causal")
    return SimpleNamespace(source=source, initial=initial, preparation=preparation, preparation_raw=raw,
        arrays=arrays, design=design, public=public, causal=causal, witness=witness, frames=frames,
        causal_raw=causal_raw, diagnostic_raw=diagnostic_raw)


def test_available_prepared_feature_uses_original_frozen_window_actual_state_and_supplied_family(tmp_path):
    f = available_prepared_operands(tmp_path)
    design, public, causal, witness, frames = f.design, f.public, f.causal, f.witness, f.frames
    causal_raw, diagnostic_raw, arrays = f.causal_raw, f.diagnostic_raw, f.arrays
    assert causal.disposition == "AVAILABLE"
    feature = method.causal_feature(design, public, causal, witness, frames, causal_raw, diagnostic_raw, record_id="feature.literal-point-available")
    assert feature.disposition == "AVAILABLE" and tuple(name for name, _ in feature.values) == FEATURES
    assert dict(feature.values)["family-de-anneal"] == 1
    with localcontext() as context:
        context.prec = 50
        assert dict(feature.values)["position-y-norm"] == (D(1) + D(repr(float(np.linalg.norm(arrays["primary_positions"][-1, 1]))))).ln()
    seal = method.forecast(design, public, causal, feature, record_id="seal.literal-point-available")
    assert seal.raw_log_error_points == (D(".5"),) * 15 and seal.log_error_points == (D(".5"),) * 15
    assert seal.log_error_uppers == (None,) * 15 and seal.radius is None
