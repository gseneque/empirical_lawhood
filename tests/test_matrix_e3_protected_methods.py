# SPDX-License-Identifier: MPL-2.0
"""Literal exposed numerical adversaries; these fixtures confer no evidence."""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from fractions import Fraction
from hashlib import sha256
from math import comb

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import experiment_methods as old
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_experiment_methods as protected
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_prefix_records as prefix
from empirical_lawhood.adapters.methods.matrix_factor_response.records import MatrixFactorAction, MatrixFactorResponseModel
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_scheduled_history import forecast as sf, records as sr, response_records as rr, response_selection as rs
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_native import ScheduledResponseTransitionControl
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from tests.test_matrix_e3_protected_inputs import (
    build_source_inputs, join, source_inputs as source_inputs, scheduled as scheduled, stock as stock, provenance as provenance,
)


def reference(name, kind):
    return ObjectIdentity("literal." + name, kind.SCHEMA, kind.VERSION, sha256(("EXPOSED." + name).encode()).hexdigest())


def fitted(case, *, constants=False):
    features, outcomes = case.train_features, case.train_outcomes
    if constants:
        features = replace(features, rows=tuple(replace(row, values=features.rows[0].values) for row in features.rows))
        outcomes = replace(outcomes, rows=tuple(replace(row, views=tuple(replace(view,
            errors=(D(0 if i % 2 == 0 else 3),) * 15) for view in row.views)) for i, row in enumerate(outcomes.rows)))
    models = protected.fit_protected_e3_models(case.inputs, join(case), features, outcomes, record_id="model.literal.protected")
    frozen = protected.freeze_protected_e3(case.inputs.specification, case.allocation, models, record_id="freeze.literal.models")
    return models, frozen


def causal(case, unit, *, source_index=None):
    row = next(row for row in case.inputs.reservation.allocation.roots if row.root.independent_group_id == unit)
    index = source_index if source_index is not None else ScheduledSourceIndex.from_shared(
        reservation=case.inputs.reservation, specification=case.inputs.native_specification, provenances=(case.provenance,))
    source = index.resolve(index.reference(source_id="source.literal." + unit,
        root_id=row.root.root_id, provenance=case.provenance.identity))
    public = sf.ScheduledPublicSource.from_source(source)
    origin = reference("prefix." + unit, prefix.ProtectedE3CausalPrefix)
    evidence = tuple(sorted((origin, reference("numerical." + unit, prefix.ProtectedE3NumericalAssessment),
        reference("witness." + unit, prefix.ProtectedE3PrefixWitness), reference("frames." + unit, prefix.ProtectedE3FrameAssessment)),
        key=lambda row: row.object_id))
    feature = protected.ProtectedE3CausalFeature("protected-feature." + unit, sr.identity(source.allocation), public,
        origin, "a" * 64, "AVAILABLE", case.train_features.rows[0].values, evidence)
    return source, feature


def forecasts(case, models, frozen, role, *, calibration=None):
    source_index = ScheduledSourceIndex.from_shared(reservation=case.inputs.reservation,
        specification=case.inputs.native_specification, provenances=(case.provenance,))
    return tuple(protected.forecast_protected_e3(case.inputs.specification, case.allocation, models, frozen, causal(case, unit, source_index=source_index)[1],
        role=role, record_id="forecast.literal." + unit, calibration=calibration) for unit in case.allocation.unit_ids(role))


def outcome(forecast, *, values=None, missing=False, numerical="SATISFIED"):
    values = (D("0.05"),) * 15 if values is None else values
    views = tuple(old.MatrixE3ViewOutcome(view, (None,) * 15 if missing else values,
        ("UNKNOWN_CONTACT" if missing else "FINITE",) * 15) for view in ("fine", "primary"))
    return protected.ProtectedE3PairedOutcome("outcome.literal." + forecast.feature.unit_id, forecast.feature,
        protected.identity(forecast), reference("score." + forecast.feature.unit_id, rr.ScheduledResponseScore), "b" * 64,
        reference("protocol." + forecast.feature.unit_id, rr.ScheduledResponseProtocol),
        (reference("panel.common." + forecast.feature.unit_id, rr.ScheduledResponsePanel),
         reference("panel.independent." + forecast.feature.unit_id, rr.ScheduledResponsePanel)), views, numerical)


def calibrated(case, models, frozen, *, missing_count=0):
    fs = forecasts(case, models, frozen, "calibration")
    ys = tuple(outcome(f, missing=i < missing_count) for i, f in enumerate(fs))
    cal = protected.calibrate_protected_e3(case.inputs.specification, case.allocation, models, frozen, fs, ys,
        record_id="calibration.literal.protected")
    sealed = protected.freeze_protected_e3(case.inputs.specification, case.allocation, models,
        record_id="freeze.literal.calibrated", model_freeze=frozen, calibration=cal)
    return fs, ys, cal, sealed


def test_original_primary_ridge_and_raw_median_have_independent_constant_design_values(source_inputs):
    models, frozen = fitted(source_inputs, constants=True)
    with localcontext() as context:
        context.prec = 50
        expected_intercept = D(4).ln() / 2
    for model in models.models:
        assert model.training_unit_ids == source_inputs.allocation.unit_ids("train")
        assert model.finite_counts == (12,) * 15
        if model.method_key == "RAW_TRAIN_MEDIAN":
            assert model.raw_constants == (D("1.5"),) * 15
        else:
            assert len(model.feature_names) == (13 if model.method_key == "SPECTRAL_RIDGE" else 21)
            for parameter in model.ridge_parameters:
                assert abs(parameter.coefficients[0] - expected_intercept) < D("1e-14")
                assert all(abs(value) < D("1e-14") for value in parameter.coefficients[1:])
            selection = next(s for s in source_inputs.inputs.specification.methods if s.method_key == model.method_key)
            assert selection.ridge_lambda == 1 and not selection.penalize_intercept
    assert frozen.calibration is None and not hasattr(models, "standing") and not hasattr(models, "qualified")
    assert decode_canonical_bytes(models.canonical_bytes(), type(models), maximum_bytes=None) == models


def test_calibration_uses_independent_max_both_views_then_max15_and_infinite_missing(source_inputs):
    case = source_inputs
    models, frozen = fitted(case)
    fs = forecasts(case, models, frozen, "calibration")
    ys = []
    for i, f in enumerate(fs):
        base = tuple(D(i + endpoint + 1) / 1000 for endpoint in range(15))
        y = outcome(f, values=base)
        ys.append(replace(y, views=(replace(y.views[0], errors=tuple(v + D("0.00005") for v in base)), y.views[1])))
    cal = protected.calibrate_protected_e3(case.inputs.specification, case.allocation, models, frozen, fs, tuple(ys),
        record_id="calibration.literal.max15")
    with localcontext() as context:
        context.prec = 50
        literal = tuple(max(max(D(0), (1 + max(y.views[0].errors[k], y.views[1].errors[k])).ln()
            - dict(f.log_points)["SPECTRAL_RIDGE"][k]) for k in range(15)) for f, y in zip(fs, ys, strict=True))
    assert tuple(v for _, v, _ in cal.scores) == literal
    assert cal.rank == 20 and cal.radius == max(literal)
    unavailable = tuple(outcome(f, missing=i == 0) for i, f in enumerate(fs))
    infinite = protected.calibrate_protected_e3(case.inputs.specification, case.allocation, models, frozen, fs, unavailable,
        record_id="calibration.literal.infinity")
    assert len(infinite.scores) == 20 and infinite.scores[0][1] is None and infinite.radius is None
    assert "UNKNOWN_CONTACT" in infinite.scores[0][2]


def test_point_transform_clips_then_retains_cumulative_maximum_and_missingness(source_inputs):
    case = source_inputs
    models, _ = fitted(case)
    edited = []
    for model in models.models:
        if model.method_key == "RAW_TRAIN_MEDIAN":
            edited.append(replace(model, raw_constants=(D(0), D(3), D(1)) * 5))
        else:
            parameters = tuple(replace(p, coefficients=(D((-1, 2, 1)[i % 3]), *((D(0),) * len(p.means))))
                for i, p in enumerate(model.ridge_parameters))
            edited.append(replace(model, ridge_parameters=parameters))
    models = replace(models, models=tuple(edited))
    frozen = protected.freeze_protected_e3(case.inputs.specification, case.allocation, models, record_id="freeze.literal.cumulative")
    f = forecasts(case, models, frozen, "calibration")[0]
    for method, values in f.log_points:
        if method == "RAW_TRAIN_MEDIAN":
            with localcontext() as context:
                context.prec = 50
                expected = (D(0), D(4).ln(), D(4).ln()) * 5
        else:
            expected = (D(0), D(2), D(2)) * 5
        assert values == expected
    changed = []
    for model in models.models:
        if model.method_key == "RAW_TRAIN_MEDIAN":
            changed.append(replace(model, raw_constants=(D(0), None, D(1)) * 5, finite_counts=(12, 0, 12) * 5))
        else:
            changed.append(model)
    models = replace(models, models=tuple(changed))
    frozen = protected.freeze_protected_e3(case.inputs.specification, case.allocation, models, record_id="freeze.literal.missing")
    assert dict(forecasts(case, models, frozen, "calibration")[0].log_points)["RAW_TRAIN_MEDIAN"] == (D(0), None, None) * 5


@pytest.mark.parametrize("failure", ("tie", "one-baseline", "one-view"))
def test_strict_margin_requires_each_original_baseline_and_both_views(source_inputs, failure):
    case = source_inputs
    models, frozen = fitted(case)
    _, _, cal, sealed = calibrated(case, models, frozen)
    fs = forecasts(case, models, sealed, "evaluation", calibration=cal)
    with localcontext() as context:
        context.prec = 50
        margin, strong = (1 + D("0.0002")).ln(), (1 + D("0.001")).ln()
    fs = tuple(replace(f, log_points=(("ALL_ORIGIN_RIDGE", ((margin if failure == "tie" else D(0)
        if failure == "one-baseline" else strong),) * 15), ("RAW_TRAIN_MEDIAN", (strong,) * 15),
        ("SPECTRAL_RIDGE", (D(0),) * 15))) for f in fs)
    ys = []
    for f in fs:
        y = outcome(f, values=(D(0),) * 15)
        if failure == "one-view":
            y = replace(y, views=(replace(y.views[0], errors=(D("0.000425"),) * 15),
                replace(y.views[1], errors=(D("0.000375"),) * 15)))
        ys.append(y)
    result = protected.assess_protected_e3(case.inputs.specification, case.allocation, sealed, fs, tuple(ys),
        record_id="assessment.literal.strict")
    assert result.successes == 0 and result.usable_units == 8 and not result.criterion_met
    assert all("STRICT_PAIRED_MARGIN_NOT_MET" in row.reasons for row in result.decisions)
    if failure == "tie":
        assert all(row.comparisons[0][2] == D("0.0002") for row in result.decisions)
    elif failure == "one-view":
        assert all(row.comparisons[0][2] == D("0.00015") and row.comparisons[1][2] == D("0.00025")
            for row in result.decisions)


def test_selected64_complete_denominator_exact_binomial_and_missing_failures(scheduled):
    case = build_source_inputs(scheduled, selected64=True)
    assert dict(case.allocation.role_counts) == dict(calibration=64, evaluation=64, train=64, transfer_nearby=64, transfer_shifted=64)
    models, frozen = fitted(case)
    original_models = models.canonical_bytes()
    _, _, cal, sealed = calibrated(case, models, frozen, missing_count=3)
    assert cal.rank == 62 and cal.radius is None and len(cal.scores) == 64
    fs = forecasts(case, models, sealed, "evaluation", calibration=cal)
    # Explicit literal predictions make only the strict paired criterion vary.
    with localcontext() as context:
        context.prec = 50
        point, control = (1 + D("0.05")).ln(), (1 + D("0.051")).ln()
    fs = tuple(replace(f, log_points=tuple((name, ((point if name == "SPECTRAL_RIDGE" else control),) * 15)
        for name in old.METHODS)) for f in fs)
    ys = tuple(outcome(f, missing=i >= 58, values=(D("0.05") if i < 43 else D("0.051"),) * 15)
        for i, f in enumerate(fs))
    assessed = protected.assess_protected_e3(case.inputs.specification, case.allocation, sealed, fs, ys, record_id="assessment.literal.full64")
    exact_tail = Fraction(sum(comb(64, k) for k in range(43, 65)), 2 ** 64)
    assert assessed.successes == 43 and assessed.usable_units == 58 and len(assessed.decisions) == 64
    assert Fraction(assessed.binomial_tail_numerator, assessed.binomial_tail_denominator) == exact_tail
    assert assessed.criterion_met and exact_tail <= Fraction(1, 240)
    assert len(assessed.forecasts) == len(assessed.outcomes) == 64
    assert all(not row.success and "UNKNOWN_CONTACT" in row.reasons for row in assessed.decisions[58:])
    assert all(f.radius_kind == "INFINITE" for f in fs)
    assert all(kind in ("INFINITE", "UNAVAILABLE") for _, kind in assessed.coverage_bound_kinds)
    assert models.canonical_bytes() == original_models
    assert decode_canonical_bytes(assessed.canonical_bytes(), type(assessed), maximum_bytes=None) == assessed
    for reduced_fs, reduced_ys in ((fs[:-1], ys), (fs, ys[:-1])):
        with pytest.raises(ValueError, match="whole roots"):
            protected.assess_protected_e3(case.inputs.specification, case.allocation, sealed, reduced_fs, reduced_ys, record_id="assessment.literal.thinned")


@pytest.mark.parametrize("damage", ("source", "freeze", "model", "calibration", "exposed", "refit"))
def test_foreign_source_freeze_refit_and_exposed_records_refuse(source_inputs, damage):
    case = source_inputs
    models, frozen = fitted(case)
    fs, ys, cal, sealed = calibrated(case, models, frozen)
    with pytest.raises((ValueError, TypeError)):
        if damage == "source":
            replace(fs[0].feature, source_manifest=reference("foreign", sr.ScheduledAllocation))
        elif damage == "freeze":
            protected.calibrate_protected_e3(case.inputs.specification, case.allocation, models,
                replace(frozen, record_id="freeze.foreign"), fs, ys, record_id="calibration.foreign")
        elif damage == "model":
            changed = (replace(fs[0], models=reference("foreign", protected.ProtectedE3ModelSet)), *fs[1:])
            protected.calibrate_protected_e3(case.inputs.specification, case.allocation, models, frozen, changed, ys, record_id="calibration.foreign")
        elif damage == "calibration":
            protected.forecast_protected_e3(case.inputs.specification, case.allocation, models, frozen,
                causal(case, case.allocation.unit_ids("evaluation")[0])[1], role="evaluation", record_id="forecast.foreign", calibration=cal)
        elif damage == "exposed":
            protected.forecast_protected_e3(replace(case.inputs.specification, evidence_scope="EXPOSED_CONFORMANCE"),
                case.allocation, models, frozen, fs[0].feature, role="calibration", record_id="forecast.foreign")
        else:
            protected.freeze_protected_e3(case.inputs.specification, case.allocation, replace(models, record_id="models.refit"),
                record_id="freeze.foreign", model_freeze=frozen, calibration=cal)
    assert sealed.models == frozen.models == protected.identity(models)


def projection_fixture(case):
    models, frozen = fitted(case)
    source, feature = causal(case, case.allocation.unit_ids("evaluation")[0])
    _, _, cal, sealed = calibrated(case, models, frozen)
    f = protected.forecast_protected_e3(case.inputs.specification, case.allocation, models, sealed, feature,
        role="evaluation", record_id="forecast.literal.cells", calibration=cal)
    raw, members = encode_matrix_arrays({"generic_basis": np.zeros((3, 4, 4), dtype="<c16"),
        "force_coefficients": np.zeros((2, 3, 3), dtype="<f8"), "trace_coefficients": np.zeros((2, 3), dtype="<f8"),
        "receiver_coefficients": np.zeros((48, 2, 2, 3, 4), dtype="<f8")})
    pub = case.plane.write(ArtifactWriteRequest("literal.e3.templates", "literal/templates.npz", sr.MATRIX_ARRAY_SCHEMA,
        ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", "literal-e3", "literal", raw, Visibility.PROSPECTIVE, (), Access.OUTCOME_BLIND))
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import corpus_artifact
    arrays = rr.ScheduledResponseArrays("arrays.literal.templates", "TEMPLATES", sr.identity(source), corpus_artifact(pub), members,
        (sr.identity(source),), Access.OUTCOME_BLIND, Visibility.PROSPECTIVE)
    protocol = rr.ScheduledResponseProtocol("protocol.literal.cells", feature.public_source, case.inputs.specification.identity,
        MatrixFactorResponseModel("model.literal.mechanical", rr.physical_forecast_implementation()),
        tuple(MatrixFactorAction("action.literal." + role.lower(), role, D("0.01"), 16, D(1)) for role in ("COMPLEMENT", "FACTOR", "GENERIC", "TRACE")),
        (16, 64, 128), 48, arrays, D("1e-5"), D("1e-10"), D("1e-10"), D("1e-10"), D("1e-10"), D("1e-8"), D("1e-5"), D("1e-12"), D("1e-10"),
        "PRESERVED_DISTINCT_PRIMARY_FINE_CUTOFF_STATES_ORIGIN_FIXED_PRIMARY_Y_FRAME")
    panels = (rr.ScheduledResponsePanel("panel.literal.common", feature.unit_id, "COMMON_NOISE_PANEL", "ORIGINAL_COMPLETED_PREFIX_GENERATOR_STATES", source.root.streams),
        rr.ScheduledResponsePanel("panel.literal.independent", feature.unit_id, "INDEPENDENT_FUTURE", "FRESH_DECLARED_FUTURE_START_AT_CUTOFF",
            tuple(MatrixHistorySeed(p, sha256(("EXPOSED.CELLS." + p).encode()).hexdigest()) for p in HISTORY_PURPOSES)))
    selection = rs.ScheduledResponseSelection("selection.literal.cells", ObjectIdentity.from_record(source.allocation.allocation_id, source.allocation), (protocol,), ((feature.unit_id, panels),), (pub,), None)
    selection.validate_allocation(source.allocation)
    controls = tuple(ScheduledResponseTransitionControl("control.scheduled." + source.root_id + "." + branch,
        "SCHEDULED_PULSE_FULL192_LITERAL_TRACE_WORD_BAOAB_BOTH_KICKS", D(0), protocol.native_reference_tolerance, "SATISFIED",
        128 if view == "PRIMARY" else 256, 192, (D(0),) * (128 if view == "PRIMARY" else 256), ())
        for branch, view, *_ in rr.branch_census(protocol, panels))
    cells = []
    for view in ("PRIMARY", "FINE"):
        for panel_index, panel in enumerate(panels):
            for action_index, action in enumerate(protocol.actions):
                for description_index, description in enumerate(case.inputs.specification.measurement.descriptions):
                    for horizon in (16, 64, 128):
                        value = D(description_index) / 100 + D(horizon) / 10000 + D(panel_index) / 100000 + D(action_index) / 1000000 + (D("0.00005") if view == "FINE" else 0)
                        cells.append(rr.ScheduledResponseLossCell(view, panel.panel_id, action.action_id, description, horizon,
                            (D(1),) * 48, (value,) * 48, (value,) * 48, (value,) * 48, value))
    score = rr.ScheduledResponseScore("score.literal.cells", sr.identity(source), feature.origin, protected.identity(f),
        reference("physical-forecast", rr.ScheduledResponseForecast), reference("responses", rr.ScheduledResponseNative), source.root_id,
        feature.unit_id, source.root.root.role.value, protocol.criterion, controls, True, "FINITE", tuple(sorted(cells, key=lambda c: c.key)),
        (D(999),) * 15, ())
    return source, selection, f, score


def test_complete240_original_cells_project_both_views_without_primary_only_summary(source_inputs):
    case = source_inputs
    source, selection, f, score = projection_fixture(case)
    projected = protected.project_protected_e3_outcome(case.inputs.specification, source, selection, f, score, record_id="outcome.literal.cells")
    assert len(score.cells) == 240 and len(score.controls) == 48
    for view in projected.views:
        for k, (description, horizon) in enumerate(old.ENDPOINTS):
            literal = max(c.normalized_error for c in score.cells if c.view == view.view_id.upper()
                and c.predictor == description and c.horizon_tick <= horizon)
            assert view.errors[k] == literal and literal != D(999)
    damaged = replace(score, cells=score.cells[:-1])
    with pytest.raises(ValueError, match="cell denominators"):
        protected.project_protected_e3_outcome(case.inputs.specification, source, selection, f, damaged, record_id="outcome.literal.thinned")
    controls = replace(score, controls=score.controls[:-1])
    with pytest.raises(ValueError, match="full192"):
        protected.project_protected_e3_outcome(case.inputs.specification, source, selection, f, controls, record_id="outcome.literal.thinned")
    missing_cell = replace(score.cells[0], normalized_error=None)
    missing = replace(score, cells=(missing_cell, *score.cells[1:]), disposition="PARTIAL")
    partial = protected.project_protected_e3_outcome(case.inputs.specification, source, selection, f, missing, record_id="outcome.literal.partial")
    assert any(v is None for view in partial.views for v in view.errors)
    assert "UNAVAILABLE" in protected.numerical.outcome_reasons(case.inputs.specification, partial)


def test_configured_native_training_reuses_original_complete_paired_target_body(source_inputs):
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_methods import paired_response_view_values
    from tests.test_matrix_configured_e3_v2 import configured_case

    source, selection, forecast, score = projection_fixture(source_inputs)
    configured, _ = configured_case()
    protocol = selection.protocols[0]
    panels = dict(selection.panels)[source.root.root.independent_group_id]
    projected = protected.project_paired_response_cells(source_inputs.inputs.specification, source, protocol,
        panels, forecast, score, record_id="outcome.native-target-old-byte-control")
    views, numerical = paired_response_view_values(configured, source, protocol, panels, score)
    assert tuple(view.canonical_bytes() for view in views) == tuple(view.canonical_bytes() for view in projected.views)
    assert numerical == projected.numerical_disposition
    with pytest.raises(ValueError, match="cell denominators"):
        paired_response_view_values(configured, source, protocol, panels,
            replace(score, cells=score.cells[:-1]))
    with pytest.raises(ValueError, match="full192"):
        paired_response_view_values(configured, source, protocol, panels,
            replace(score, controls=score.controls[:-1]))
