# SPDX-License-Identifier: MPL-2.0
"""Independent literal feature controls; no native or qualification evidence.

The finite fixture authors mathematical observations and assessment metadata.
It does not establish that a whole observer or physical source is available.
"""

from dataclasses import replace
from decimal import Decimal as D, localcontext

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_lifetime.science import lifetime
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_feature_science as owner
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_experiment_methods import ProtectedE3CausalFeature
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_source_records import identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history import forecast
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from tests.test_matrix_e3_protected_feature import encoded, finite_case
from tests.test_matrix_e3_protected_prefix_science import blocked
from tests.test_matrix_e3_protected_prefix_science import case as case, forbid_native as forbid_native  # noqa: F401


@pytest.fixture(scope="module")
def finite(case):
    return finite_case(case)


def project(case, *, public=None, causal=None, witness=None, assessment=None, causal_raw=None, diagnostic_raw=None):
    return owner.project_protected_e3_feature(case.specification,
        forecast.ScheduledPublicSource.from_source(case.source) if public is None else public,
        case.causal if causal is None else causal, case.witness if witness is None else witness,
        case.frames if assessment is None else assessment, case.causal_raw if causal_raw is None else causal_raw,
        case.diagnostic_raw if diagnostic_raw is None else diagnostic_raw)


def joined(case, witness, assessment=None, causal=None):
    assessment = replace(case.frames if assessment is None else assessment, witness=identity(witness))
    causal = case.causal if causal is None else causal
    causal = replace(causal, witness=identity(witness), frame_assessment=identity(assessment),
        arrays=replace(causal.arrays, producers=tuple(sorted((causal.source, causal.history,
            identity(witness), identity(assessment)), key=lambda row: row.object_id))))
    return causal, witness, assessment


def diagnostic_operand(case, diagnostics):
    return encoded(case, diagnostics, role="PREFIX_DIAGNOSTICS", producers=case.witness.arrays.producers,
        nonfinite=tuple(name for name in diagnostics if not name.endswith(("_ticks", "_available", "_identifiable"))))


def test_literal_complex_phase_norms_and_trailing_window_match_original_math(finite, monkeypatch, tmp_path):
    case = finite
    monkeypatch.setattr(np.linalg, "eigh", blocked)
    monkeypatch.setattr(np.linalg, "eigvalsh", blocked)
    rule = case.source.policy.factor_rule
    traces = []
    for trace in case.witness.traces:
        if (trace.view, trace.sector) == ("PRIMARY", "Y"):
            # The angle at the window's first point is excluded; earlier
            # history also cannot enlarge the two within-window increments.
            angles = {224: D("1.8"), 240: D(".125"), 256: D(".375")}
            observations = tuple(replace(row, adjacent_angle_degrees=angles.get(row.tick, D("1.9")))
                for row in trace.observations)
            trace = replace(trace, observations=observations, moving_lifetime=lifetime(observations, rule),
                origin_fixed_lifetime=lifetime(observations, rule, origin_fixed=True))
        traces.append(trace)
    diagnostics = {name: value.copy() for name, value in case.diagnostics.items()}
    diagnostics["primary_y_spectrum"][:] = np.asarray((0, .125, .25, .5, .75, 1, 1.5, 2, 3, 4, 5, 6, 7, 8, 10), dtype="<f8")
    diagnostic_raw, operand = diagnostic_operand(case, diagnostics)
    witness = replace(case.witness, traces=tuple(traces), arrays=operand)
    causal, witness, assessment = joined(case, witness)
    arrays = {name: value.copy() for name, value in case.values.items()}
    for phase, scales in (("positions", (1, 3)), ("momenta", (4, 6))):
        state = arrays["primary_" + phase][-1]
        state[:] = 0
        for sector, scale in enumerate(scales):
            state[sector, 2, 3, 2] = scale * (1 + 1j)
            state[sector, 2, 2, 3] = scale * (1 - 1j)
    causal_raw, operand = encoded(case, arrays, role="CAUSAL_STATE", producers=causal.arrays.producers)
    causal = replace(causal, arrays=operand)
    feature = project(case, causal=causal, witness=witness, assessment=assessment,
        causal_raw=causal_raw, diagnostic_raw=diagnostic_raw)
    values = dict(feature.values)
    assert feature.disposition == "AVAILABLE"
    assert (values["largest-y-rate"], values["slow-y-mean"], values["third-fourth-y-gap"], values["trailing-angle"]) == (
        D(10), D(".125"), D(".25"), D(".375"))
    with localcontext() as context:
        context.prec = 50
        assert tuple(values[name] for name in ("position-x-norm", "position-y-norm", "momentum-x-norm", "momentum-y-norm")) == (
            D(3).ln(), D(7).ln(), D(9).ln(), D(13).ln())
    _, old_diagnostics = encoded(case, diagnostics, role="PREFIX_DIAGNOSTICS", producers=case.old_witness.arrays.producers,
        nonfinite=tuple(name for name in diagnostics if not name.endswith(("_ticks", "_available", "_identifiable"))))
    old_witness = replace(case.old_witness, traces=tuple(traces), arrays=old_diagnostics)
    _, old_arrays = encoded(case, arrays, role="CAUSAL_STATE", producers=case.old_causal.arrays.producers)
    old_causal = replace(case.old_causal, disposition="AVAILABLE", reason=None,
        frame_sha256=causal.frame_sha256, arrays=old_arrays)
    original = forecast.causal_feature_from_prefix(case.source, old_causal, old_witness, arrays, diagnostics,
        feature_id="feature.independent.original-mathematics", feature_window_ticks=32, feature_cadence_ticks=16)
    assert canonical_json_bytes((feature.disposition, feature.values, feature.frame_sha256)) == canonical_json_bytes((
        original.disposition, original.values, original.frame_sha256))
    (tmp_path / "independent-feature.canonical").write_bytes(feature.canonical_bytes())
    (tmp_path / "original-feature.canonical").write_bytes(original.canonical_bytes())


def test_same_root_and_coordinate_cannot_rebind_original_source_fingerprint(finite, monkeypatch):
    monkeypatch.setattr(forecast, "causal_feature_values", blocked)
    public = forecast.ScheduledPublicSource.from_source(finite.source)
    public = replace(public, source=replace(public.source, object_fingerprint="e" * 64))
    with pytest.raises(ValueError, match="actual source"):
        project(finite, public=public)


def test_available_prefix_cannot_ignore_a_retained_violated_frame_control(finite, monkeypatch):
    monkeypatch.setattr(forecast, "causal_feature_values", blocked)
    control = finite.frames.controls[0]
    control = replace(control, measured_errors=(*control.measured_errors[:-1], control.tolerance + 1), disposition="VIOLATED")
    assessment = replace(finite.frames, controls=(control, *finite.frames.controls[1:]), numerical_pass=False)
    causal, witness, assessment = joined(finite, finite.witness, assessment)
    with pytest.raises(ValueError, match="independent frame assessment"):
        project(finite, causal=causal, witness=witness, assessment=assessment)


def test_available_prefix_cannot_ignore_cutoff_admission_failure(finite, monkeypatch):
    monkeypatch.setattr(forecast, "causal_feature_values", blocked)
    rule = finite.source.policy.factor_rule
    traces = []
    for trace in finite.witness.traces:
        if (trace.view, trace.sector) == ("PRIMARY", "Y"):
            last = replace(trace.observations[-1], associative_leakage=rule.associative_leakage_maximum + 1,
                raw_admitted=False, causal_admitted=False)
            observations = (*trace.observations[:-1], last)
            trace = replace(trace, observations=observations, moving_lifetime=lifetime(observations, rule),
                origin_fixed_lifetime=lifetime(observations, rule, origin_fixed=True))
        traces.append(trace)
    causal, witness, assessment = joined(finite, replace(finite.witness, traces=tuple(traces)))
    with pytest.raises(ValueError, match="cutoff admission"):
        project(finite, causal=causal, witness=witness, assessment=assessment)


def test_interior_diagnostic_clock_is_checked_even_when_endpoints_match(finite, monkeypatch):
    monkeypatch.setattr(forecast, "causal_feature_values", blocked)
    diagnostics = {name: value.copy() for name, value in finite.diagnostics.items()}
    ticks = diagnostics["primary_y_ticks"]
    ticks[5] = ticks[4]
    assert (ticks[0], ticks[-1]) == (0, 256)
    raw, operand = diagnostic_operand(finite, diagnostics)
    causal, witness, assessment = joined(finite, replace(finite.witness, arrays=operand))
    with pytest.raises(ValueError, match="complete diagnostic clock"):
        project(finite, causal=causal, witness=witness, assessment=assessment, diagnostic_raw=raw)


def test_valid_archive_cannot_omit_a_fine_view_eigenvector_member(finite, monkeypatch):
    monkeypatch.setattr(forecast, "causal_feature_values", blocked)
    diagnostics = {name: value for name, value in finite.diagnostics.items() if name != "fine_x_eigenvectors"}
    raw, operand = diagnostic_operand(finite, diagnostics)
    causal, witness, assessment = joined(finite, replace(finite.witness, arrays=operand))
    with pytest.raises(ValueError, match="complete diagnostic members"):
        project(finite, causal=causal, witness=witness, assessment=assessment, diagnostic_raw=raw)


def test_feature_v2_cannot_admit_an_unknown_numerical_evidence_revision(finite):
    feature = project(finite)
    numerical = finite.causal.numerical
    evidence = tuple(replace(row, object_version="99.0.0") if row == numerical else row for row in feature.evidence)
    with pytest.raises(ValueError, match="complete current evidence"):
        ProtectedE3CausalFeature(feature.record_id, feature.source_manifest, feature.public_source,
            feature.prefix, feature.frame_sha256, feature.disposition, feature.values, evidence)
