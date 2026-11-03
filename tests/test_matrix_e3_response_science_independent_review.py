# SPDX-License-Identifier: MPL-2.0
"""Independent response-consumer falsifiers over disclosed literal metadata.

The reused prefix is numerically negative. Finite target cells below are
authored arithmetic operands, not received paths or qualifying observations.
Physical transforms use the existing admitted codec and fresh reader leases.
"""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
import os

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import protected_experiment_methods as methods
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_response_records as records
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_response_science as owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_forecast, science
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from tests.test_matrix_e3_response_records import case as _producer_case, publication, qualification
from tests.test_matrix_e3_response_science import (
    LIMITS, blocked, byte_fetch, context, literal_score, no_native, public_context, score_config, store,
)
from tests.test_matrix_e3_scheduled_datasets import physical_dataset

case = _producer_case
no_native = no_native  # Reuse the disclosed no-contact/RNG/eigensolver guards.


def causal_operand(case, values, *, available=False):
    raw, arrays = science._array_product(case.source, values, role="CAUSAL_STATE",
        artifact_id=case.causal.arrays.array_artifact.artifact_id, producers=case.causal.arrays.producers,
        nonfinite=() if available else ("frame",))
    causal = replace(case.causal, arrays=arrays,
        **({"frame_sha256": sha256(values["frame"].tobytes()).hexdigest(), "disposition": "AVAILABLE", "reason": None}
           if available else {}))
    return raw, causal


@pytest.mark.parametrize("damage", ("fine-clock", "primary-coupling", "frame"))
def test_seedless_forecast_authenticates_actual_clock_coupling_and_frame_before_math(case, monkeypatch, damage):
    values = {name: array.copy() for name, array in decode_matrix_arrays(case.causal_raw, case.causal.arrays).items()}
    available = damage == "frame"
    if available:
        values["frame"][:] = 0
        _, original = causal_operand(case, values, available=True)
        values["frame"][0, 0, 0] = 1
    elif damage == "fine-clock":
        values["fine_ticks"][-1] -= 1
    else:
        values["primary_alpha_tilde"][-1, 1] += .125
    raw, causal = causal_operand(case, values, available=available)
    if available:
        # Keep the frame's declared member identity consistent with the current
        # record; only the actual supplied bytes contradict that identity.
        arrays = replace(causal.arrays, members=tuple(replace(member, sha256=original.frame_sha256)
            if member.name == "frame" else member for member in causal.arrays.members))
        causal = replace(causal, frame_sha256=original.frame_sha256, arrays=arrays)
    payloads = store(case)
    payloads[causal.arrays.array_artifact.artifact_id] = raw
    monkeypatch.setattr(owner, "forecast_response_arrays", blocked)
    expected = "complete member size or value hash verification failed" if available else "paired cutoff clocks"
    with pytest.raises(ValueError, match=expected):
        owner.forecast_physical(case.physical_config, causal, **public_context(case), fetch=byte_fetch(payloads),
            **LIMITS, artifact_id="literal.independent.refused.forecast", forecast_id="literal.independent.refused",
            outcome_access=case.physical.arrays.outcome_access, visibility_ceiling=case.physical.arrays.visibility_ceiling)


@pytest.mark.parametrize("field", ("source", "policy"))
def test_seedless_forecast_refuses_changed_public_reference_without_fetch(case, field):
    changed = replace(getattr(case.causal, field), object_fingerprint="e" * 64)
    arrays = case.causal.arrays
    if field == "source":
        arrays = replace(arrays, source=changed,
            producers=tuple(changed if row == case.causal.source else row for row in arrays.producers))
    causal = replace(case.causal, **{field: changed, "arrays": arrays})
    with pytest.raises(ValueError):
        owner.forecast_physical(case.physical_config, causal, **public_context(case), fetch=blocked,
            **LIMITS, artifact_id="literal.independent.refused.forecast", forecast_id="literal.independent.refused",
            outcome_access=case.physical.arrays.outcome_access, visibility_ceiling=case.physical.arrays.visibility_ceiling)


@pytest.mark.parametrize("member", ("fine_ticks", "fine_positions"))
def test_forecast_final_seal_covers_previously_used_and_unused_physical_members(case, tmp_path, monkeypatch, member):
    payloads, calculated = store(case), []
    original = owner.forecast_response_arrays
    directory = tmp_path / "causal"
    with physical_dataset(case.causal.arrays, case.causal_raw, directory) as reader:
        def calculate_then_mutate(*args, **kwargs):
            result = original(*args, **kwargs)
            assert result[1] == "UNEVALUABLE" and len(result[0]) == 10
            path = directory / (member + ".values")
            with path.open("r+b", buffering=0) as handle:
                offset = path.stat().st_size - 1
                before = os.pread(handle.fileno(), 1, offset)
                assert os.pwrite(handle.fileno(), bytes((before[0] ^ 1,)), offset) == 1
            calculated.append(result)
            return result

        monkeypatch.setattr(owner, "forecast_response_arrays", calculate_then_mutate)
        fetch = lambda artifact: reader if artifact == case.causal.arrays.array_artifact else payloads[artifact.artifact_id]
        with pytest.raises(ValueError, match="physical array final whole seal"):
            owner.forecast_physical(case.physical_config, case.causal, **public_context(case), fetch=fetch,
                **LIMITS, artifact_id="literal.independent.sealed.forecast", forecast_id="literal.independent.sealed",
                outcome_access=case.physical.arrays.outcome_access, visibility_ceiling=case.physical.arrays.visibility_ceiling)
    assert len(calculated) == 1


def test_cold_reproof_rejects_changed_retained_nonuse_prediction_before_receiver_assessment(case, monkeypatch):
    values = {name: array.copy() for name, array in decode_matrix_arrays(case.physical_raw, case.physical.arrays).items()}
    values["fine_factor"][3, 2, 47] = .25
    raw, arrays = response_forecast.array_product(case.protocol, values, role="FORECAST",
        artifact_id=case.physical.arrays.array_artifact.artifact_id, producers=case.physical.arrays.producers,
        access=case.physical.arrays.outcome_access, visibility=case.physical.arrays.visibility_ceiling,
        nonfinite=tuple(values))
    physical = replace(case.physical, arrays=arrays)
    old_ref, new_ref = owner._object(case.physical), owner._object(physical)
    response = replace(case.response, physical_forecast=new_ref, arrays=replace(case.response.arrays,
        producers=tuple(new_ref if row == old_ref else row for row in case.response.arrays.producers)))
    payloads = store(case)
    payloads[arrays.array_artifact.artifact_id] = raw
    monkeypatch.setattr(owner, "assess_paired_response_arrays", blocked)
    with pytest.raises(ValueError, match="cold forecast substitutes actual frozen"):
        owner.assess_responses(score_config(case), case.native_config, response, **context(case, physical=physical),
            fetch=byte_fetch(payloads), **LIMITS, score_id="literal.independent.changed.retained")


def test_actual_prefix_native_source_closure_refuses_before_any_array_fetch(case):
    event = case.history.native
    definition = replace(event.definition, sources=event.definition.sources[:-1])
    with pytest.raises(ValueError):
        history = replace(case.history, native=replace(event, definition=definition,
            completion=replace(event.completion, definition=definition.identity)))
        owner.assess_responses(score_config(case), case.native_config, case.response, **context(case, history=history),
            fetch=blocked, **LIMITS, score_id="literal.independent.native.source.refused")


def target_operands(case):
    literal = literal_score(case)
    predictors = case.specification.measurement.descriptions
    panels = tuple(panel.panel_id for panel in case.panels)
    actions = tuple(action.action_id for action in case.protocol.actions)
    horizons = case.protocol.horizon_steps
    cells = []
    for cell in literal.score.cells:
        value = ((D(100) if cell.view == "FINE" else D(0)) + 10 * predictors.index(cell.predictor)
            + horizons.index(cell.horizon_tick) + D(panels.index(cell.panel_id)) / 10 + D(actions.index(cell.action_id)) / 100)
        signed = tuple(value + D(receiver) / 1000 for receiver in range(48))
        cells.append(replace(cell, actual_odd_responses=tuple(D(receiver + 1) for receiver in range(48)),
            signed_errors=signed, absolute_errors=signed, relative_errors=tuple(value / (receiver + 1) for receiver in range(48)),
            normalized_error=value))
    literal.score = replace(literal.score, cells=tuple(cells), cumulative_log_errors=(D(9999),) * 15)
    return literal


def project(case, literal, *, score=None):
    return owner.project_outcome(score_config(case), case.native_config, literal.response,
        literal.score if score is None else score, **literal.args, record_id="literal.independent.paired.outcome")


def test_independent_ordered_cell_oracle_keeps240_cells48_receiver_vectors48_controls_and_both_views(case):
    literal = target_operands(case)
    result = project(case, literal)
    assert len(literal.score.cells) == 240 and len(literal.score.controls) == 48
    assert all(len(cell.actual_odd_responses) == len(cell.signed_errors) == 48 for cell in literal.score.cells)
    assert sum(control.denominator_steps for control in literal.score.controls) == 24 * (128 + 256)
    for view in result.views:
        offset = D(100) if view.view_id == "fine" else D(0)
        assert view.errors == tuple(offset + 10 * predictor + horizon + D(".13")
            for predictor in range(5) for horizon in range(3))
        assert view.dispositions == ("FINITE",) * 15
    assert result.original_cells_sha256 == sha256(methods.canonical_json_bytes(literal.score.cells)).hexdigest()


def test_missing_one_fine_cell_propagates_only_its_predictor_and_later_horizons(case):
    literal = target_operands(case)
    cells = tuple(replace(cell, signed_errors=None, absolute_errors=None, relative_errors=None, normalized_error=None)
        if cell.view == "FINE" and cell.predictor == "FACTOR" and cell.horizon_tick == case.protocol.horizon_steps[1]
        and cell.panel_id == case.panels[0].panel_id and cell.action_id == case.protocol.actions[0].action_id else cell
        for cell in literal.score.cells)
    assert sum(cell.normalized_error is None for cell in cells) == 1
    result = project(case, literal, score=replace(literal.score, cells=cells, disposition="PARTIAL"))
    baseline = project(case, literal)
    for actual, expected in zip(result.views, baseline.views, strict=True):
        missing = (1, 2) if actual.view_id == "fine" else ()
        assert actual.errors == tuple(None if index in missing else value for index, value in enumerate(expected.errors))
        assert actual.dispositions == tuple("UNAVAILABLE" if index in missing else "FINITE" for index in range(15))


def negative_score(literal):
    controls = list(literal.score.controls)
    first = controls[0]
    residuals = (2 * first.tolerance, *first.measured_errors[1:])
    controls[0] = replace(first, error=2 * first.tolerance, measured_errors=residuals, disposition="VIOLATED", failed_steps=(1,))
    return replace(literal.score, controls=tuple(controls), numerical_pass=False,
        disposition="NATIVE_CROSSCHECK_FAILED", cumulative_log_errors=(None,) * 15,
        reason_codes=("literal-full192-native-transition-violated",))


def test_native_negative_keeps_complete_control_denominators_and_both_missing_target_vectors(case):
    literal = target_operands(case)
    score = negative_score(literal)
    result = project(case, literal, score=score)
    assert len(score.controls) == 48 and all(row.denominator_real_coordinates == 192 for row in score.controls)
    assert sum(row.denominator_steps for row in score.controls) == 24 * (128 + 256)
    assert result.numerical_disposition == "VIOLATED"
    assert all(view.errors == (None,) * 15 and view.dispositions == ("NUMERICAL_FAILURE",) * 15 for view in result.views)


@pytest.mark.parametrize("damage", ("steps", "tolerance"))
def test_native_negative_cannot_thin_branch_scope_or_change_original_tolerance(case, damage):
    literal = target_operands(case)
    score = negative_score(literal)
    first = score.controls[0]
    if damage == "steps":
        first = replace(first, denominator_steps=1, measured_errors=(first.error,))
    else:
        tolerance = first.tolerance / 2
        first = replace(first, tolerance=tolerance)
    changed = replace(score, controls=(first, *score.controls[1:]))
    with pytest.raises(ValueError):
        project(case, literal, score=changed)


def development_profile(case, suffix):
    # Actual publication bytes plus explicitly literal, non-authoritative Q
    # metadata. The scientific protocol and all numerical values stay exact.
    pub = publication(case, case.protocol, "independent.scope." + suffix,
        access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility=VisibilityCeiling.DEVELOPMENT_ONLY)
    q = qualification(case.protocol, pub, "independent.scope." + suffix)
    profile = records.project_protected_e3_response_numerics(case.protocol,
        provenance=case.protocol, publication=pub, qualification=q)
    config = replace(case.physical_config, numerical_profile=methods.identity(profile))
    return profile, config, {**public_context(case), "numerical_profile": profile}


def test_development_numerical_container_retains_scope_and_exact_original_forecast_bytes(case):
    _, config, operands = development_profile(case, "positive")
    raw, forecast = owner.forecast_physical(config, case.causal, **operands, fetch=byte_fetch(store(case)),
        **LIMITS, artifact_id="literal.independent.development.forecast", forecast_id="literal.independent.development",
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY)
    assert raw == case.physical_raw
    assert forecast.disposition == case.physical.disposition == "UNEVALUABLE"
    assert (forecast.arrays.outcome_access, forecast.arrays.visibility_ceiling) == (
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)
    forecast.validate_public_inputs(config, causal=case.causal, **operands)


def test_development_numerical_container_cannot_be_projected_to_blind_before_fetch(case):
    _, config, operands = development_profile(case, "lowered")
    with pytest.raises(ValueError, match="lowers original numerical provenance"):
        owner.forecast_physical(config, case.causal, **operands, fetch=blocked,
            **LIMITS, artifact_id="literal.independent.lowered.forecast", forecast_id="literal.independent.lowered",
            outcome_access=OutcomeAccess.OUTCOME_BLIND, visibility_ceiling=VisibilityCeiling.PROSPECTIVE)


def test_cold_physical_record_cannot_relabel_development_profile_as_blind(case):
    profile, config, operands = development_profile(case, "cold")
    old, new = case.physical.numerical_profile, methods.identity(profile)
    arrays = replace(case.physical.arrays, producers=tuple(new if ref == old else ref for ref in case.physical.arrays.producers))
    forecast = replace(case.physical, configuration=records._object(config), numerical_profile=new, arrays=arrays)
    with pytest.raises(ValueError, match="lowers original numerical provenance"):
        forecast.validate_public_inputs(config, causal=case.causal, **operands)
