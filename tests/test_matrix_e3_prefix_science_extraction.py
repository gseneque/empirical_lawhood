# SPDX-License-Identifier: MPL-2.0
"""Literal prefix arrays and disclosed metadata, never native qualification.

The segment delivery below returns hand-authored constant paths and zero noise.
No native acquisition, stepping or RNG runs. Source/receipt records come from
the existing exposed fixture and confer no real custody or qualification.
"""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as r, science
from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history, parameter_history_segments as segments, parameter_source
from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from tests.test_matrix_factor_confirmation_eligibility import publish, stock as stock, provenance as provenance
from tests.test_matrix_scheduled_history import (prefix_case, scheduled as scheduled, with_parents,
    pure_assess_prefix, pure_measure_prefix, pure_check_frames, pure_causal_delivery)


def blocked(*args, **kwargs):
    raise AssertionError("literal prefix control entered native acquisition, stepping or RNG")


def coanneal_source(plane, original):
    coordinates = tuple(replace(c, family_id=FOUR_FAMILY_PREPARATION_IDS[0]) for c in original.allocation.coordinates)
    mapped = {c.coordinate_id: coordinate_identity(c) for c in coordinates}
    allocation = replace(original.allocation, coordinates=coordinates,
        roots=tuple(replace(row, coordinate=mapped[row.root.coordinate_id]) for row in original.allocation.roots),
        matched_scopes=tuple(replace(scope, coordinates=tuple(mapped[c.object_id] for c in scope.coordinates)) for scope in original.allocation.matched_scopes))
    reservation = replace(original.reservation, allocation=allocation, publication=publish(plane, allocation, "literal.prefix.allocation"))
    selection = replace(original.specification.selection, reservation=r.identity(reservation),
        coordinate_policies=tuple((mapped[c.object_id], policy) for c, policy in original.specification.selection.coordinate_policies))
    specification = replace(original.specification, selection=selection, publication=publish(plane, selection, "literal.prefix.selection"))
    return with_parents(original, reservation=reservation, specification=specification)


def literal_segment(source, *, damaged=False):
    coordinate, cutoff = source.coordinate, source.policy.cutoff_tick
    initial = parameter_history.initial_parameter_state(coordinate)
    arrays, terminal = {}, {}
    for view, multiplier in (("primary", 1), ("fine", 2)):
        count = multiplier * cutoff
        for phase in ("positions", "momenta"):
            value = getattr(initial, phase)
            arrays[view + "_" + phase] = np.repeat(value[None], count, axis=0).astype("<c16")
            terminal[view + "_" + phase] = value.copy()
        arrays[view + "_ticks"] = np.arange(count, dtype="<i8")
        arrays[view + "_alpha_tilde"] = np.asarray([coordinate.couplings(tick, refinement=multiplier) for tick in range(count)], dtype="<f8")
        arrays[view + "_innovations"] = np.zeros((count, 2, 3, 4, 4), dtype="<c16")
    arrays["bridge_innovations"] = np.zeros((cutoff, 2, 3, 4, 4), dtype="<c16")
    if damaged:
        arrays["primary_positions"][1, 0, 0, 0, 0] += .125
    states = tuple(segments.ParameterGeneratorState(stream.purpose, stream.effective_seed, 0, 1, 0, 0,
        min(cutoff, coordinate.ramp_ticks) if stream.purpose.startswith("preparation") else max(0, cutoff - coordinate.ramp_ticks)) for stream in source.root.streams)
    return segments.ParameterSegmentValues(0, cutoff, dict(sorted(arrays.items())), terminal, states)


def build_case(scheduled, monkeypatch, *, variant="zero"):
    plane, sources = scheduled
    original = next(source for source in sources if source.root.root.role.value == "CALIBRATION")
    source = original if variant == "deanneal-negative" else coanneal_source(plane, original)
    values = literal_segment(source, damaged=variant == "native-negative")
    delivered = []

    def delivery(coordinate, streams, start, stop, **kwargs):
        assert (coordinate, streams, start, stop, kwargs) == (source.coordinate, source.root.streams, 0, source.policy.cutoff_tick, {})
        delivered.append("literal-values")
        return values

    monkeypatch.setattr(segments, "acquire_parameter_segment", delivery)
    monkeypatch.setattr(parameter_source, "acquire_parameter_history", blocked)
    monkeypatch.setattr(parameter_history, "advance_parameter_pair", blocked)
    monkeypatch.setattr(np.random, "Generator", blocked)
    monkeypatch.setattr(np.random, "PCG64DXSM", blocked)
    if variant == "unavailable":
        def unavailable(*args, **kwargs):
            raise np.linalg.LinAlgError("exposed literal unavailable eigenpair control")
        monkeypatch.setattr(np.linalg, "eigh", unavailable)
    products = prefix_case(plane, source)
    assert delivered == ["literal-values"]
    monkeypatch.setattr(segments, "acquire_parameter_segment", blocked)
    history, numerical, witness, frames, causal, native_raw, diagnostic_raw, causal_raw = products
    return SimpleNamespace(source=source, history=history, numerical=numerical, witness=witness, frames=frames, causal=causal,
        native_raw=native_raw, diagnostic_raw=diagnostic_raw, causal_raw=causal_raw)


def canonical_products(case):
    return canonical_json_bytes((case.history, case.numerical, case.witness, case.frames, case.causal))


def refusal_cases(case):
    altered = replace(case.numerical.controls[0], tolerance=case.numerical.controls[0].tolerance + D("0.001"))
    numerical = replace(case.numerical, controls=(altered, *case.numerical.controls[1:]))
    foreign = ObjectIdentity("literal.prefix.foreign-policy", r.ScheduledPrefixPolicy.SCHEMA, r.ScheduledPrefixPolicy.VERSION, "1" * 64)
    witness = replace(case.witness, policy=foreign)
    return (
        ("numerical-tolerance", lambda: pure_measure_prefix(case.source, case.history, numerical, {}, artifact_id="literal.refused")),
        ("witness-policy", lambda: pure_check_frames(case.source, case.history, case.numerical, witness, case.native_raw, case.diagnostic_raw)),
        ("witness-lattice", lambda: pure_check_frames(case.source, case.history, case.numerical,
            replace(case.witness, traces=tuple(reversed(case.witness.traces))), case.native_raw, case.diagnostic_raw)),
        ("native-bytes", lambda: pure_check_frames(case.source, case.history, case.numerical, case.witness, case.native_raw[:-1], case.diagnostic_raw)),
        ("frame-assessment", lambda: pure_causal_delivery(case.source, case.history, case.numerical, case.witness,
            replace(case.frames, assessment_id="literal.prefix.foreign-assessment"), case.native_raw, case.diagnostic_raw, artifact_id="literal.refused")),
    )


@pytest.mark.parametrize("variant", ("zero", "native-negative", "deanneal-negative", "unavailable"))
def test_literal_complete_prefix_keeps_all192_coordinates_eigenpairs_and_nonuse(scheduled, monkeypatch, variant):
    case = build_case(scheduled, monkeypatch, variant=variant)
    assert tuple(c.denominator_steps for c in case.numerical.controls) == (6, 12, 6, 6)
    assert tuple(c.denominator_real_coordinates for c in case.numerical.controls) == (192, 192, 192, 96)
    assert len(case.witness.traces) == 4 and all(len(trace.observations) == 7 for trace in case.witness.traces)
    assert tuple(len(control.measured_errors) for control in case.frames.controls) == (28, 420, 28, 28, 28, 28)
    assert case.causal.disposition == "UNEVALUABLE"
    assert case.causal.frame_sha256 is None
    if variant == "zero":
        assert case.numerical.numerical_pass
    elif variant in ("native-negative", "deanneal-negative"):
        assert not case.numerical.numerical_pass
    else:
        assert all(observation.status == "NUMERICAL_INVALID" for trace in case.witness.traces for observation in trace.observations)
    native = science.consume_prefix(case.source, case.history.arrays, case.native_raw)
    assert native["primary_ticks"].tolist() == list(range(7)) and native["fine_ticks"].tolist() == list(range(13))
    delivered = decode_matrix_arrays(case.causal_raw, case.causal.arrays)
    assert set(delivered) == {name for name in native if not name.endswith("innovations")} | {"frame"}
    assert np.isnan(delivered["frame"]).all()


def test_literal_prefix_cold_reader_blocks_spectrum_and_measurer(scheduled, monkeypatch):
    case = build_case(scheduled, monkeypatch)
    monkeypatch.setattr(np.linalg, "eigh", blocked)
    monkeypatch.setattr(np.linalg, "eigvalsh", blocked)
    monkeypatch.setattr(science.factor_science, "measure_sector", blocked)
    native = science.consume_prefix(case.source, case.history.arrays, case.native_raw)
    assert pure_assess_prefix(case.source, case.history, native) == case.numerical
    assert pure_check_frames(case.source, case.history, case.numerical, case.witness, case.native_raw, case.diagnostic_raw) == case.frames
    assert pure_causal_delivery(case.source, case.history, case.numerical, case.witness, case.frames,
        case.native_raw, case.diagnostic_raw, artifact_id=case.causal.arrays.array_artifact.artifact_id, raw=case.causal_raw) == (case.causal_raw, case.causal)


def test_original_prefix_refusals_keep_source_and_full_witness_boundaries(scheduled, monkeypatch):
    case = build_case(scheduled, monkeypatch)
    for _, invoke in refusal_cases(case):
        with pytest.raises(ValueError):
            invoke()


def test_value_helpers_reproduce_original_controls_traces_and_causal_arrays(scheduled, monkeypatch):
    case = build_case(scheduled, monkeypatch)
    native = science.consume_prefix(case.source, case.history.arrays, case.native_raw)
    diagnostics = decode_matrix_arrays(case.diagnostic_raw, case.witness.arrays)
    assert science.assess_prefix_values(case.source, native) == case.numerical.controls
    measured, traces = science.measure_prefix_values(case.source, native)
    assert traces == case.witness.traces
    assert set(measured) == set(diagnostics)
    assert all(np.array_equal(measured[name], diagnostics[name], equal_nan=True) for name in measured)
    assert science.check_prefix_frame_values(case.source, traces, native, diagnostics) == case.frames.controls
    values, frame_sha, disposition, reason = science.causal_cutoff_values(case.source, traces,
        case.numerical.numerical_pass, case.frames.numerical_pass, native, diagnostics)
    delivered = decode_matrix_arrays(case.causal_raw, case.causal.arrays)
    assert all(np.array_equal(values[name], delivered[name], equal_nan=True) for name in values)
    assert (frame_sha, disposition, reason) == (case.causal.frame_sha256, case.causal.disposition, case.causal.reason)
    assert all(not np.shares_memory(values[name], native[name]) for name in native if name in values)


@pytest.mark.parametrize("damage", ("trace-denominator", "eigenpair", "forged-operator"))
def test_cold_values_keep_full_lattice_and_independent_raw_operator(scheduled, monkeypatch, damage):
    case = build_case(scheduled, monkeypatch)
    native = science.consume_prefix(case.source, case.history.arrays, case.native_raw)
    diagnostics = {name: value.copy() for name, value in decode_matrix_arrays(case.diagnostic_raw, case.witness.arrays).items()}
    traces = case.witness.traces
    if damage == "trace-denominator":
        with pytest.raises(ValueError, match="denominator"):
            science.check_prefix_frame_values(case.source, traces[:-1], native, diagnostics)
    elif damage == "eigenpair":
        diagnostics["primary_x_eigenvectors"] = diagnostics["primary_x_eigenvectors"][..., :-1]
        with pytest.raises(ValueError):
            science.check_prefix_frame_values(case.source, traces, native, diagnostics)
    else:
        diagnostics["primary_x_operator"] += np.eye(15)
        diagnostics["primary_x_spectrum"] += 1
        controls = science.check_prefix_frame_values(case.source, traces, native, diagnostics)
        assert next(control for control in controls if control.method == "raw-operator").disposition == "VIOLATED"
        assert next(control for control in controls if control.method == "all-eigenpairs").disposition == "VIOLATED"
        assert tuple(len(control.measured_errors) for control in controls) == (28, 420, 28, 28, 28, 28)


@pytest.mark.parametrize("numerical_pass,frame_pass,raw,causal,ambiguous,expected", (
    (False, True, True, True, False, "UNEVALUABLE"), (True, False, True, True, False, "UNEVALUABLE"),
    (True, True, None, None, False, "UNEVALUABLE"), (True, True, False, False, False, "NO_ORIGIN"),
    (True, True, True, True, True, "NO_ORIGIN"), (True, True, True, True, False, "AVAILABLE"),
))
def test_bare_cutoff_conditional_values_confer_no_native_qualification(scheduled, monkeypatch,
        numerical_pass, frame_pass, raw, causal, ambiguous, expected):
    case = build_case(scheduled, monkeypatch)
    native = science.consume_prefix(case.source, case.history.arrays, case.native_raw)
    diagnostics = {name: value.copy() for name, value in decode_matrix_arrays(case.diagnostic_raw, case.witness.arrays).items()}
    key = science.prefix("PRIMARY", case.source.policy.origin_sector) + "aligned_factor"
    # Bare flags/frame test only the conditional. These are not original
    # qualified traces, and no scientific envelope is constructed from them.
    frame = np.zeros((3, 4, 4), dtype="<c16")
    diagnostics[key][-1] = frame
    observation = SimpleNamespace(raw_admitted=raw, causal_admitted=causal, alignment_ambiguous=ambiguous)
    trace = SimpleNamespace(view="PRIMARY", sector=case.source.policy.origin_sector, observations=(observation,))
    values, digest, disposition, reason = science.causal_cutoff_values(case.source, (trace,), numerical_pass,
        frame_pass, native, diagnostics)
    assert disposition == expected
    if expected == "AVAILABLE":
        assert digest == sha256(frame.tobytes()).hexdigest() and reason is None
        assert np.array_equal(values["frame"], frame) and not np.shares_memory(values["frame"], diagnostics[key])
    else:
        assert digest is None and reason is not None and np.isnan(values["frame"]).all()


def test_old_history_guards_run_before_any_value_helper(scheduled, monkeypatch):
    case = build_case(scheduled, monkeypatch)
    history = replace(case.history, checkpoint=replace(case.history.checkpoint, cutoff_tick=7))
    for name in ("assess_prefix_values", "measure_prefix_values", "check_prefix_frame_values", "causal_cutoff_values"):
        monkeypatch.setattr(science, name, blocked)
    calls = (
        lambda: pure_assess_prefix(case.source, history, {}),
        lambda: pure_measure_prefix(case.source, history, case.numerical, {}, artifact_id="literal.refused"),
        lambda: pure_check_frames(case.source, history, case.numerical, case.witness, b"", b""),
        lambda: pure_causal_delivery(case.source, history, case.numerical, case.witness, case.frames, b"", b"", artifact_id="literal.refused"),
    )
    for invoke in calls:
        with pytest.raises(ValueError):
            invoke()
