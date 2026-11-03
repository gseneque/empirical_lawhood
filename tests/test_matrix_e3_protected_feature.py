# SPDX-License-Identifier: MPL-2.0
"""Disclosed feature arithmetic and adverse joins, without qualification.

The finite fixture explicitly authors observations, frame controls and arrays.
It is a mathematical consumer control, never authentic native/source evidence.
The unchanged literal-prefix fixture retains its actual UNEVALUABLE result.
"""

from dataclasses import fields, replace
from decimal import Decimal as D, localcontext
from hashlib import sha256
from inspect import signature
import json
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_lifetime.science import lifetime
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_feature_science as owner
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_prefix_records as current
from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import FEATURES
from empirical_lawhood.adapters.methods.matrix_scheduled_history import forecast, records as scheduled, science
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from tests.test_matrix_e3_protected_prefix_science import blocked, case as case, forbid_native as forbid_native  # noqa: F401
from tests.test_matrix_response_error_prediction import observation


def project(case, *, public=None, causal=None, witness=None, assessment=None, causal_raw=None, diagnostic_raw=None):
    return owner.project_protected_e3_feature(case.specification,
        forecast.ScheduledPublicSource.from_source(case.source) if public is None else public,
        case.causal if causal is None else causal, case.witness if witness is None else witness,
        case.frames if assessment is None else assessment, case.causal_raw if causal_raw is None else causal_raw,
        case.diagnostic_raw if diagnostic_raw is None else diagnostic_raw)


def encoded(case, arrays, *, role, producers, nonfinite=()):
    return science._array_product(case.source, arrays, role=role, artifact_id="exposed.feature-v2." + role.lower(),
        producers=producers, nonfinite=nonfinite)


def finite_case(case):
    """Complete typed, explicitly authored mathematical operands only."""
    rule = case.source.policy.factor_rule
    observations = tuple(replace(observation(tick, angle=D(2)),
        causal_admitted=tick >= rule.trailing_persistence_ticks, origin_angle_degrees=D(0)) for tick in rule.lattice)
    traces = tuple(replace(trace, observations=observations, moving_lifetime=lifetime(observations, rule),
        origin_fixed_lifetime=lifetime(observations, rule, origin_fixed=True)) for trace in case.witness.traces)
    diagnostics = {name: value.copy() for name, value in decode_matrix_arrays(case.diagnostic_raw, case.witness.arrays).items()}
    spectrum = np.arange(15, dtype="<f8") / 8
    diagnostics["primary_y_spectrum"][:] = spectrum
    diagnostic_raw, diagnostic_operand = encoded(case, diagnostics, role="PREFIX_DIAGNOSTICS",
        producers=(case.witness.source, case.witness.history, case.witness.numerical),
        nonfinite=tuple(name for name in diagnostics if not name.endswith(("_ticks", "_available", "_identifiable"))))
    witness = replace(case.witness, traces=traces, arrays=diagnostic_operand)
    controls = tuple(replace(control, measured_errors=(D(0),) * len(control.measured_errors),
        applicable=(True,) * len(control.measured_errors), disposition="SATISFIED") for control in case.frames.controls)
    frames = replace(case.frames, witness=current.identity(witness), controls=controls, numerical_pass=True)
    arrays = {name: value.copy() for name, value in decode_matrix_arrays(case.causal_raw, case.causal.arrays).items()}
    arrays["frame"][:] = 0
    arrays["frame"][:, 0, 0] = (1, 2, 3)
    for name, amplitudes in (("positions", (3, 4)), ("momenta", (12, 5))):
        arrays["primary_" + name][-1] = 0
        arrays["primary_" + name][-1, :, 0, 0, 0] = amplitudes
    causal_raw, causal_operand = encoded(case, arrays, role="CAUSAL_STATE",
        producers=(case.causal.source, case.causal.history, current.identity(witness), current.identity(frames)))
    causal = replace(case.causal, witness=current.identity(witness), frame_assessment=current.identity(frames),
        disposition="AVAILABLE", reason=None, frame_sha256=sha256(arrays["frame"].tobytes()).hexdigest(), arrays=causal_operand)
    return SimpleNamespace(**{**vars(case), "witness": witness, "frames": frames, "causal": causal,
        "causal_raw": causal_raw, "diagnostic_raw": diagnostic_raw, "values": arrays, "diagnostics": diagnostics})


@pytest.fixture(scope="module")
def finite(case):
    return finite_case(case)


def test_v2_is_exact_seedless_current_record_and_roundtrips(case):
    result = project(case)
    assert result.VERSION == "2.0.0" and result.disposition == "UNAVAILABLE" and result.values == ()
    assert tuple(field.name for field in fields(result)) == (
        "record_id", "source_manifest", "public_source", "prefix", "frame_sha256", "disposition", "values", "evidence")
    assert result.source_manifest == scheduled.identity(case.source.allocation)
    assert (result.unit_id, result.native_source, result.origin, result.clock_id, result.cutoff) == (
        case.source.root.root.independent_group_id, scheduled.identity(case.source), current.identity(case.causal),
        case.source.coordinate.clock_id, D(".256"))
    assert result.record_id == "feature.matrix-e3-protected." + case.source.root_id
    assert set(result.evidence) == {current.identity(case.causal), case.causal.numerical,
        current.identity(case.witness), current.identity(case.frames)}
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result
    def keys(value):
        if type(value) is dict:
            return set(value).union(*(keys(item) for item in value.values()))
        return set().union(*(keys(item) for item in value)) if type(value) is list else set()

    assert not keys(json.loads(result.canonical_bytes())) & {"effective_seed", "checkpoint", "streams", "innovations", "original"}
    assert tuple(signature(owner.project_protected_e3_feature).parameters) == (
        "specification", "public_source", "causal", "witness", "assessment", "causal_raw", "diagnostic_raw")


def test_complete21_values_match_original_wrapper_and_literal_calculation(finite):
    case = finite
    result = project(case)
    assert result.disposition == "AVAILABLE" and tuple(name for name, _ in result.values) == FEATURES
    values = dict(result.values)
    assert values["largest-y-rate"] == D("1.75") and values["slow-y-mean"] == D(".125")
    assert values["third-fourth-y-gap"] == D(".125") and values["trailing-angle"] == 2
    assert (values["associative-leakage"], values["lie-leakage"], values["factor-fit-angle"]) == (D(".01"), D(".02"), D(2))
    assert values["cutoff"] == D(".256")
    with localcontext() as context:
        context.prec = 50
        assert tuple(values[name] for name in ("position-x-norm", "position-y-norm", "momentum-x-norm", "momentum-y-norm")) == (
            D(4).ln(), D(5).ln(), D(13).ln(), D(6).ln())
    _, old_diagnostics = encoded(case, case.diagnostics, role="PREFIX_DIAGNOSTICS", producers=case.old_witness.arrays.producers,
        nonfinite=tuple(name for name in case.diagnostics if not name.endswith(("_ticks", "_available", "_identifiable"))))
    old_witness = replace(case.old_witness, traces=case.witness.traces, arrays=old_diagnostics)
    _, old_arrays = encoded(case, case.values, role="CAUSAL_STATE", producers=case.old_causal.arrays.producers)
    old_causal = replace(case.old_causal, disposition="AVAILABLE", reason=None, frame_sha256=case.causal.frame_sha256, arrays=old_arrays)
    original = forecast.causal_feature_from_prefix(case.source, old_causal, old_witness, case.values, case.diagnostics,
        feature_id="feature.exposed.original-comparison", feature_window_ticks=32, feature_cadence_ticks=16)
    assert canonical_json_bytes((result.disposition, result.values, result.frame_sha256)) == canonical_json_bytes((
        original.disposition, original.values, original.frame_sha256))


def test_original_no_origin_keeps_empty_feature_and_unavailable_frame(finite):
    case, rule = finite, finite.source.policy.factor_rule
    observations = tuple(replace(row, associative_leakage=rule.associative_leakage_maximum + 1,
        raw_admitted=False, causal_admitted=False) for row in case.witness.traces[0].observations)
    traces = tuple(replace(trace, observations=observations, moving_lifetime=lifetime(observations, rule),
        origin_fixed_lifetime=lifetime(observations, rule, origin_fixed=True)) for trace in case.witness.traces)
    witness = replace(case.witness, traces=traces)
    frames = replace(case.frames, witness=current.identity(witness))
    arrays = {name: value.copy() for name, value in case.values.items()}
    arrays["frame"][:] = np.nan
    raw, operand = encoded(case, arrays, role="CAUSAL_STATE", nonfinite=("frame",),
        producers=(case.causal.source, case.causal.history, current.identity(witness), current.identity(frames)))
    causal = replace(case.causal, witness=current.identity(witness), frame_assessment=current.identity(frames),
        arrays=operand, frame_sha256=None, disposition="NO_ORIGIN", reason="DECLARED_CUTOFF_NOT_CAUSALLY_ADMITTED")
    result = project(case, causal=causal, witness=witness, assessment=frames, causal_raw=raw)
    assert (result.disposition, result.values, result.frame_sha256) == ("NO_CAUSAL_ORIGIN", (), None)
    arrays["frame"][:] = 0
    raw, operand = encoded(case, arrays, role="CAUSAL_STATE", nonfinite=("frame",), producers=operand.producers)
    with pytest.raises(ValueError, match="nonuse frame"):
        project(case, causal=replace(causal, arrays=operand), witness=witness, assessment=frames, causal_raw=raw)


@pytest.mark.parametrize("damage", ("duck-spec", "origin-sector", "selected-cutoff", "paired-dt"))
def test_selected_measurement_boundary_precedes_original_arithmetic(finite, monkeypatch, damage):
    monkeypatch.setattr(forecast, "causal_feature_values", blocked)
    case = finite
    public = forecast.ScheduledPublicSource.from_source(case.source)
    specification = case.specification
    if damage == "duck-spec":
        specification = SimpleNamespace(measurement=specification.measurement)
    elif damage == "origin-sector":
        public = replace(public, policy=replace(public.policy, origin_sector="X"))
    elif damage == "selected-cutoff":
        rule = replace(public.policy.factor_rule, lattice=tuple(tick for tick in public.policy.factor_rule.lattice if tick <= 128),
            risk_start_tick=128)
        public = replace(public, policy=replace(public.policy, cutoff_tick=128, factor_rule=rule))
    else:
        coordinate = public.coordinate
        public = replace(public, coordinate=replace(coordinate,
            primary_view=replace(coordinate.primary_view, timestep=D(".002")),
            fine_view=replace(coordinate.fine_view, timestep=D(".001"))))
    with pytest.raises((TypeError, ValueError)):
        owner.project_protected_e3_feature(specification, public, case.causal, case.witness, case.frames,
            case.causal_raw, case.diagnostic_raw)


@pytest.mark.parametrize("damage", ("realized-coupling", "primary-clock", "fine-clock", "negative-spectrum"))
def test_original_feature_math_refusal_is_retained_with_selfconsistent_actual_bytes(finite, damage):
    case = finite
    arrays, diagnostics = ({name: value.copy() for name, value in source.items()} for source in (case.values, case.diagnostics))
    if damage == "realized-coupling":
        arrays["primary_alpha_tilde"][-1, 0] += 1
    elif damage.endswith("clock"):
        arrays[damage.split("-")[0] + "_ticks"][-1] -= 1
    else:
        diagnostics["primary_y_spectrum"][-1, -1] = -1
    causal_raw, operand = encoded(case, arrays, role="CAUSAL_STATE", producers=case.causal.arrays.producers)
    diagnostic_raw, diagnostic_operand = encoded(case, diagnostics, role="PREFIX_DIAGNOSTICS", producers=case.witness.arrays.producers,
        nonfinite=tuple(name for name in diagnostics if not name.endswith(("_ticks", "_available", "_identifiable"))))
    witness = replace(case.witness, arrays=diagnostic_operand)
    frames = replace(case.frames, witness=current.identity(witness))
    # Update every immutable downstream join; refusal must come from values.
    operand = replace(operand, producers=tuple(sorted((case.causal.source, case.causal.history,
        current.identity(witness), current.identity(frames)), key=lambda row: row.object_id)))
    causal = replace(case.causal, witness=current.identity(witness), frame_assessment=current.identity(frames), arrays=operand)
    result = project(case, causal=causal, witness=witness, assessment=frames, causal_raw=causal_raw, diagnostic_raw=diagnostic_raw)
    expected = forecast.causal_feature_values(case.source.coordinate, case.source.policy,
        prefix_disposition="AVAILABLE", prefix_frame_sha256=case.causal.frame_sha256, traces=witness.traces,
        causal_arrays=arrays, diagnostics=diagnostics, feature_window_ticks=32, feature_cadence_ticks=16)
    assert (result.disposition, result.values) == expected == ("REFUSED", ())


@pytest.mark.parametrize("damage", ("root", "policy", "history", "numerical", "witness", "frames", "producers", "tolerance", "thin-eigenpairs"))
def test_current_seedless_product_joins_refuse_before_math(finite, monkeypatch, damage):
    monkeypatch.setattr(forecast, "causal_feature_values", blocked)
    case = finite
    public, causal, witness, frames = forecast.ScheduledPublicSource.from_source(case.source), case.causal, case.witness, case.frames
    if damage == "root":
        causal = replace(causal, root=replace(causal.root, independent_group_id="group.foreign"))
    elif damage == "policy":
        public = replace(public, policy=replace(public.policy, policy_id="policy.foreign"))
    elif damage in ("history", "numerical", "witness"):
        changed = replace(getattr(causal, damage), object_fingerprint="e" * 64)
        changes = {damage: changed}
        if damage in ("history", "witness"):
            producers = tuple(changed if row == getattr(causal, damage) else row for row in causal.arrays.producers)
            changes["arrays"] = replace(causal.arrays, producers=tuple(sorted(producers, key=lambda row: row.object_id)))
        causal = replace(causal, **changes)
    elif damage == "frames":
        frames = replace(frames, record_id="frames.foreign")
    elif damage == "producers":
        witness = replace(witness, arrays=replace(witness.arrays, producers=(witness.source,)))
        frames = replace(frames, witness=current.identity(witness))
    else:
        controls = tuple(replace(control, measured_errors=control.measured_errors[:-15 if i == 1 else -1],
            applicable=control.applicable[:-15 if i == 1 else -1]) for i, control in enumerate(frames.controls)) if damage == "thin-eigenpairs" else (
                replace(frames.controls[0], tolerance=frames.controls[0].tolerance + 1), *frames.controls[1:])
        frames = replace(frames, controls=controls)
    if damage in ("producers", "tolerance", "thin-eigenpairs"):
        causal = replace(causal, witness=current.identity(witness), frame_assessment=current.identity(frames),
            arrays=replace(causal.arrays, producers=tuple(sorted((causal.source, causal.history,
                current.identity(witness), current.identity(frames)), key=lambda row: row.object_id))))
    with pytest.raises((TypeError, ValueError)):
        project(case, public=public, causal=causal, witness=witness, assessment=frames)


@pytest.mark.parametrize("damage", ("causal-bytes", "diagnostic-bytes", "diagnostic-clock", "frame-hash", "legacy-prefix", "duck-public"))
def test_bounded_actual_arrays_and_exact_types_cannot_be_substituted(finite, damage):
    case = finite
    arguments = {}
    if damage.endswith("bytes"):
        arguments[damage.replace("-bytes", "_raw")] = getattr(case, damage.replace("-bytes", "_raw"))[:-1]
    elif damage == "frame-hash":
        with pytest.raises(ValueError):
            replace(case.causal, frame_sha256="e" * 64)
        return
    elif damage == "legacy-prefix":
        arguments["causal"] = case.old_causal
    elif damage == "duck-public":
        public = forecast.ScheduledPublicSource.from_source(case.source)
        arguments["public"] = SimpleNamespace(**{field.name: getattr(public, field.name) for field in fields(public)})
    else:
        diagnostics = {name: value.copy() for name, value in case.diagnostics.items()}
        diagnostics["fine_x_ticks"][-1] -= 1
        raw, operand = encoded(case, diagnostics, role="PREFIX_DIAGNOSTICS", producers=case.witness.arrays.producers,
            nonfinite=tuple(name for name in diagnostics if not name.endswith(("_ticks", "_available", "_identifiable"))))
        witness = replace(case.witness, arrays=operand)
        frames = replace(case.frames, witness=current.identity(witness))
        causal = replace(case.causal, witness=current.identity(witness), frame_assessment=current.identity(frames),
            arrays=replace(case.causal.arrays, producers=tuple(sorted((case.causal.source, case.causal.history,
                current.identity(witness), current.identity(frames)), key=lambda row: row.object_id))))
        arguments.update(witness=witness, assessment=frames, causal=causal, diagnostic_raw=raw)
    with pytest.raises((TypeError, ValueError)):
        project(case, **arguments)


@pytest.mark.parametrize("damage", ("legacy-prefix", "omit-evidence", "duplicate-evidence", "nonuse-values", "cutoff", "negative"))
def test_v2_constructor_keeps_exact_current_evidence_and_original_value_grammar(finite, damage):
    feature = project(finite)
    change = {}
    if damage == "legacy-prefix":
        change["prefix"] = scheduled.identity(finite.old_causal)
    elif damage == "omit-evidence":
        change["evidence"] = feature.evidence[:-1]
    elif damage == "duplicate-evidence":
        change["evidence"] = (feature.evidence[0],) * 4
    elif damage == "nonuse-values":
        change["disposition"] = "UNAVAILABLE"
    else:
        values = dict(feature.values)
        values["cutoff" if damage == "cutoff" else "largest-y-rate"] = D(1) if damage == "cutoff" else D(-1)
        change["values"] = tuple(sorted(values.items()))
    with pytest.raises((TypeError, ValueError)):
        replace(feature, **change)


@pytest.mark.parametrize("reference", ("source", "reservation"))
def test_public_original_references_keep_exact_record_kind_and_revision(finite, reference):
    public = forecast.ScheduledPublicSource.from_source(finite.source)
    value = getattr(public, reference)
    # The public carrier or the consuming feature closes each exact revision.
    with pytest.raises(ValueError):
        public = replace(public, **{reference: replace(value, object_version="99.0.0")})
        project(finite, public=public)
