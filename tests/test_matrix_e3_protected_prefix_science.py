# SPDX-License-Identifier: MPL-2.0
"""Pure readers of exposed literal256 paths; no native/source qualification.

The fixture explicitly authors metadata and constant phase arrays with zero
innovations. It retains their numerical failures; no RNG or native runner runs.
"""

from dataclasses import replace
from decimal import Decimal
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import protected_prefix_science as owner
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_source_records as sources
from empirical_lawhood.adapters.methods.matrix_scheduled_history import science
from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history, parameter_history_segments, parameter_source
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from tests.test_matrix_e3_prefix_records import current_case
from tests.test_matrix_factor_confirmation_eligibility import stock
from tests.test_matrix_parameter_history import source as parameter_template
from tests.test_matrix_scheduled_history import scheduled


def blocked(*args, **kwargs):
    raise AssertionError("pure protected prefix reader entered a forbidden producer")


@pytest.fixture(scope="module")
def case(tmp_path_factory):
    temporary = tmp_path_factory.mktemp("literal-protected-prefix")
    exposed = stock.__wrapped__(temporary, parameter_template().provenance)
    with pytest.MonkeyPatch.context() as patch:
        result = current_case(scheduled.__wrapped__(exposed), patch)
        patch.setattr(parameter_history_segments, "acquire_parameter_segment", blocked)
        patch.setattr(parameter_source, "acquire_parameter_history", blocked)
        patch.setattr(parameter_history, "advance_parameter_pair", blocked)
        patch.setattr(np.random, "Generator", blocked)
        patch.setattr(np.random, "PCG64DXSM", blocked)
        patch.setattr(np.random, "default_rng", blocked)
        yield result


@pytest.fixture(autouse=True)
def forbid_native(monkeypatch):
    monkeypatch.setattr(parameter_history_segments, "acquire_parameter_segment", blocked)
    monkeypatch.setattr(parameter_source, "acquire_parameter_history", blocked)
    monkeypatch.setattr(parameter_history, "advance_parameter_pair", blocked)
    monkeypatch.setattr(np.random, "Generator", blocked)
    monkeypatch.setattr(np.random, "PCG64DXSM", blocked)
    monkeypatch.setattr(np.random, "default_rng", blocked)


def context(case):
    return dict(prefix_config=case.config, manifest=case.manifest, specification=case.specification)


@pytest.fixture(scope="module")
def products(case):
    arguments = context(case)
    numerical = owner.assess_prefix(case.history, case.native_raw, **arguments)
    diagnostic_raw, witness = owner.measure_prefix(case.history, numerical, case.native_raw,
        artifact_id="literal.protected-prefix.diagnostics", **arguments)
    frames = owner.check_frames(case.history, numerical, witness, case.native_raw, diagnostic_raw, **arguments)
    causal_raw, causal = owner.causal_delivery(case.history, numerical, witness, frames, case.native_raw, diagnostic_raw,
        artifact_id="literal.protected-prefix.causal", **arguments)
    return SimpleNamespace(numerical=numerical, diagnostic_raw=diagnostic_raw, witness=witness, frames=frames,
        causal_raw=causal_raw, causal=causal)


def test_selected256_complete_original_controls_traces_and_archives_are_preserved(case, products):
    assert case.source.policy.cutoff_tick == case.specification.measurement.origin_tick == 256
    assert canonical_json_bytes(products.numerical.controls) == canonical_json_bytes(case.old_numerical.controls)
    assert canonical_json_bytes(products.witness.traces) == canonical_json_bytes(case.old_witness.traces)
    assert canonical_json_bytes(products.frames.controls) == canonical_json_bytes(case.old_frames.controls)
    assert products.diagnostic_raw == case.diagnostic_raw
    assert products.causal_raw == case.causal_raw
    assert (products.causal.frame_sha256, products.causal.disposition, products.causal.reason) == (
        case.old_causal.frame_sha256, case.old_causal.disposition, case.old_causal.reason)
    assert not products.numerical.numerical_pass  # The literal constant de-anneal path is adverse.
    assert products.causal.disposition == "UNEVALUABLE"
    assert products.causal.reason == "PREFIX_NUMERICAL_CONTROLS_NOT_SATISFIED"
    assert tuple((c.denominator_steps, c.denominator_real_coordinates) for c in products.numerical.controls) == (
        (256, 192), (512, 192), (256, 192), (256, 96))
    assert tuple(len(c.measured_errors) for c in products.frames.controls) == (68, 1020, 68, 68, 68, 68)
    for record in (products.numerical, products.witness, products.frames, products.causal):
        assert decode_canonical_bytes(record.canonical_bytes(), type(record), maximum_bytes=None) == record
    decoded = decode_matrix_arrays(products.causal_raw, products.causal.arrays)
    assert not any(name.endswith("innovations") for name in decoded)
    assert np.isnan(decoded["frame"]).all()
    assert decoded["primary_ticks"].tolist() == list(range(257))
    assert decoded["fine_ticks"].tolist() == list(range(513))
    assert products.numerical.record_id == "numerical.matrix-e3-protected." + case.source.root_id
    assert products.witness.record_id == "witness.matrix-e3-protected." + case.source.root_id
    assert products.frames.record_id == "frames.matrix-e3-protected." + case.source.root_id
    assert products.causal.record_id == "causal.matrix-e3-protected." + case.source.root_id


def test_independent_frame_and_cutoff_readers_do_not_measure_or_compute_a_spectrum(case, products, monkeypatch):
    monkeypatch.setattr(science, "measure_prefix_values", blocked)
    monkeypatch.setattr(np.linalg, "eigh", blocked)
    monkeypatch.setattr(np.linalg, "eigvalsh", blocked)
    original = tuple(member.sha256 for member in case.history.arrays.members)
    frames = owner.check_frames(case.history, products.numerical, products.witness,
        case.native_raw, products.diagnostic_raw, **context(case))
    raw, causal = owner.causal_delivery(case.history, products.numerical, products.witness, frames,
        case.native_raw, products.diagnostic_raw, artifact_id="literal.cold.causal", **context(case))
    assert frames == products.frames and raw == products.causal_raw
    assert causal.disposition == "UNEVALUABLE"
    assert original == tuple(member.sha256 for member in case.history.arrays.members)


def test_causal_archive_replay_validates_original_complete_bytes(case, products):
    raw, value = owner.causal_delivery(case.history, products.numerical, products.witness, products.frames,
        case.native_raw, products.diagnostic_raw, artifact_id="literal.replay.causal", raw=case.causal_raw, **context(case))
    assert raw == case.causal_raw and value.arrays.array_artifact.sha256 == products.causal.arrays.array_artifact.sha256
    with pytest.raises(ValueError):
        owner.causal_delivery(case.history, products.numerical, products.witness, products.frames,
            case.native_raw, products.diagnostic_raw, artifact_id="literal.bad-replay.causal", raw=case.causal_raw[:-1], **context(case))


@pytest.mark.parametrize("damage", ("history-type", "numerical-type", "witness-type", "prefix-config-phase", "manifest"))
def test_current_source_and_exact_record_guards_precede_arithmetic(case, products, monkeypatch, damage):
    monkeypatch.setattr(science, "assess_prefix_values", blocked)
    monkeypatch.setattr(science, "measure_prefix_values", blocked)
    monkeypatch.setattr(science, "check_prefix_frame_values", blocked)
    with pytest.raises((TypeError, ValueError)):
        if damage == "history-type":
            owner.assess_prefix(case.old_history, case.native_raw, **context(case))
        elif damage == "numerical-type":
            owner.measure_prefix(case.history, case.old_numerical, case.native_raw, artifact_id="literal.bad", **context(case))
        elif damage == "witness-type":
            owner.check_frames(case.history, products.numerical, case.old_witness, case.native_raw, products.diagnostic_raw, **context(case))
        elif damage == "prefix-config-phase":
            phase = sources.ProtectedE3SourcePhase.NUMERICAL
            config = replace(case.config, phase=phase, record_id="config." + sources.source_task_id(case.source.root_id, phase))
            owner.assess_prefix(case.history, case.native_raw, **{**context(case), "prefix_config": config})
        else:
            manifest = replace(case.manifest, record_id="manifest.literal.foreign")
            owner.assess_prefix(case.history, case.native_raw, **{**context(case), "manifest": manifest})


@pytest.mark.parametrize("damage", ("tolerance", "cutoff-denominator", "witness-policy", "producers", "view-census", "future-arrays"))
def test_numerical_witness_policy_producer_and_denominator_joins(case, products, monkeypatch, damage):
    monkeypatch.setattr(science, "measure_prefix_values", blocked)
    monkeypatch.setattr(science, "check_prefix_frame_values", blocked)
    with pytest.raises((TypeError, ValueError)):
        if damage == "tolerance":
            original = products.numerical.controls[0]
            tolerance = original.tolerance + Decimal("0.001")
            failed = tuple(i + 1 for i, error in enumerate(original.measured_errors) if error > tolerance)
            changed = replace(original, tolerance=tolerance, failed_steps=failed,
                disposition="VIOLATED" if failed else "SATISFIED")
            controls = (changed, *products.numerical.controls[1:])
            numerical = replace(products.numerical, controls=controls,
                numerical_pass=all(control.disposition == "SATISFIED" for control in controls))
            owner.measure_prefix(case.history, numerical, case.native_raw, artifact_id="literal.bad", **context(case))
        elif damage == "cutoff-denominator":
            changed = replace(products.numerical.controls[0], denominator_steps=128)
            numerical = replace(products.numerical, controls=(changed, *products.numerical.controls[1:]))
            owner.measure_prefix(case.history, numerical, case.native_raw, artifact_id="literal.bad", **context(case))
        elif damage == "witness-policy":
            policy = replace(products.witness.policy, object_fingerprint="f" * 64)
            witness = replace(products.witness, policy=policy)
            owner.check_frames(case.history, products.numerical, witness, case.native_raw, products.diagnostic_raw, **context(case))
        elif damage == "producers":
            arrays = replace(products.witness.arrays, producers=products.witness.arrays.producers[:-1])
            witness = replace(products.witness, arrays=arrays)
            owner.check_frames(case.history, products.numerical, witness, case.native_raw, products.diagnostic_raw, **context(case))
        elif damage == "view-census":
            witness = replace(products.witness, traces=products.witness.traces[:-1])
            owner.check_frames(case.history, products.numerical, witness, case.native_raw, products.diagnostic_raw, **context(case))
        else:
            history = replace(case.history, arrays=replace(case.history.arrays, role="FULL_HISTORY"))
            owner.assess_prefix(history, case.native_raw, **context(case))


@pytest.mark.parametrize("which", ("prefix", "diagnostic"))
def test_changed_received_bytes_refuse_before_independent_arithmetic(case, products, monkeypatch, which):
    monkeypatch.setattr(science, "check_prefix_frame_values", blocked)
    prefix_raw = case.native_raw[:-1] if which == "prefix" else case.native_raw
    diagnostic_raw = products.diagnostic_raw[:-1] if which == "diagnostic" else products.diagnostic_raw
    with pytest.raises(ValueError):
        owner.check_frames(case.history, products.numerical, products.witness, prefix_raw, diagnostic_raw, **context(case))


@pytest.mark.parametrize("damage", ("last-eigenpair", "raw-operator", "missing-eigenpair"))
def test_independent_reader_checks_full_last_eigenpair_and_raw_operator(case, products, monkeypatch, damage):
    arrays = {name: value.copy() for name, value in decode_matrix_arrays(products.diagnostic_raw, products.witness.arrays).items()}
    if damage == "last-eigenpair":
        # A vector change inside a zero eigenspace can remain a valid pair.
        # Change the fifteenth eigenvalue to force its literal residual.
        arrays["primary_y_spectrum"][-1, 14] += 0.125
    elif damage == "raw-operator":
        arrays["primary_y_operator"][-1, 0, 0] += 0.125
    else:
        arrays["primary_y_eigenvectors"] = arrays["primary_y_eigenvectors"][:, :, :-1]
    raw, operand = science._array_product(case.source, arrays, role="PREFIX_DIAGNOSTICS", artifact_id="literal.changed." + damage,
        producers=products.witness.arrays.producers,
        nonfinite=tuple(name for name in arrays if not name.endswith(("_ticks", "_available", "_identifiable"))))
    witness = replace(products.witness, arrays=operand)
    monkeypatch.setattr(np.linalg, "eigh", blocked)
    if damage == "missing-eigenpair":
        monkeypatch.setattr(science, "check_prefix_frame_values", blocked)
        with pytest.raises(ValueError, match="complete array members"):
            owner.check_frames(case.history, products.numerical, witness, case.native_raw, raw, **context(case))
    else:
        result = owner.check_frames(case.history, products.numerical, witness, case.native_raw, raw, **context(case))
        control = next(c for c in result.controls if c.method == ("all-eigenpairs" if damage == "last-eigenpair" else "raw-operator"))
        assert control.disposition == "VIOLATED" and not result.numerical_pass
        assert len(next(c for c in result.controls if c.method == "all-eigenpairs").measured_errors) == 1020


def test_unavailable_measurements_keep_every_missing_eigenpair_and_nonuse(case, products, monkeypatch):
    def unavailable(*args, **kwargs):
        raise np.linalg.LinAlgError("explicit exposed unavailable measurement")
    monkeypatch.setattr(np.linalg, "eigh", unavailable)
    raw, witness = owner.measure_prefix(case.history, products.numerical, case.native_raw,
        artifact_id="literal.unavailable.diagnostics", **context(case))
    assert all(observation.status == "NUMERICAL_INVALID" for trace in witness.traces for observation in trace.observations)
    frames = owner.check_frames(case.history, products.numerical, witness, case.native_raw, raw, **context(case))
    eigenpairs = next(c for c in frames.controls if c.method == "all-eigenpairs")
    assert len(eigenpairs.measured_errors) == 1020 and all(value is None for value in eigenpairs.measured_errors)
    causal_raw, causal = owner.causal_delivery(case.history, products.numerical, witness, frames, case.native_raw, raw,
        artifact_id="literal.unavailable.causal", **context(case))
    assert causal.disposition == "UNEVALUABLE" and causal.frame_sha256 is None
    assert np.isnan(decode_matrix_arrays(causal_raw, causal.arrays)["frame"]).all()


@pytest.mark.parametrize("damage", ("identity", "controls"))
def test_causal_reader_recomputes_exact_retained_assessment(case, products, monkeypatch, damage):
    assessment = replace(products.frames, record_id="frames.literal.foreign") if damage == "identity" else replace(products.frames,
        controls=(replace(products.frames.controls[0], tolerance=products.frames.controls[0].tolerance + Decimal("0.001")), *products.frames.controls[1:]))
    monkeypatch.setattr(science, "causal_cutoff_values", blocked)
    with pytest.raises(ValueError, match="retained independent frame assessment"):
        owner.causal_delivery(case.history, products.numerical, products.witness, assessment,
            case.native_raw, products.diagnostic_raw, artifact_id="literal.bad.causal", **context(case))
