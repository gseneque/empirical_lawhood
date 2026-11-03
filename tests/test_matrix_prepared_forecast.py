# SPDX-License-Identifier: MPL-2.0
"""Literal prepared-state mechanical methods and independent cold controls."""

from dataclasses import replace
from hashlib import sha256

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import preparation_science, prepared_prefix
from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_forecast as method
from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_forecast as shared_forecast
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays, encode_matrix_arrays
from tests import test_matrix_prepared_response_method as response_fixture


@pytest.fixture
def case(tmp_path):
    source, _, _, _, protocol, _, _, _, _ = response_fixture.case.__wrapped__(tmp_path)
    # Exact shared Pauli factor is a literal deterministic equation control.
    # Every innovation is supplied zero; no native lifecycle or RNG is entered.
    pauli = np.asarray(([[0, 1], [1, 0]], [[0, -1j], [1j, 0]], [[1, 0], [0, -1]]), dtype="<c16")
    factor = np.asarray([np.kron(row, np.eye(2)) / 2 for row in pauli], dtype="<c16")
    positions = np.stack((factor, factor)).astype("<c16")
    initial, members = encode_matrix_arrays({"positions": positions, "momenta": np.zeros_like(positions)})
    state = replace(source.initial, array_artifact=replace(source.initial.array_artifact,
        artifact_id="array.literal-pauli-prepared-initial", sha256=sha256(initial).hexdigest(), size_bytes=len(initial)), members=members)
    source = replace(source, initial=state)
    innovations = np.zeros((source.total_ticks, 2, 3, 4, 4), dtype="<c16")
    arrays = preparation_science.propagate_preparation(source, initial, coarse_innovations=innovations, bridge_innovations=innovations)
    raw, preparation = preparation_science.preparation_array_product(source, initial, arrays, artifact_id="array.literal-pauli-preparation")
    numerical = preparation_science.assess_preparation_arrays(source, initial, preparation, arrays, assessment_id="assessment.literal-pauli-preparation")
    diagnostic_raw, witness = prepared_prefix.measure_prepared_prefix(source, initial, preparation, numerical, raw,
        artifact_id="array.literal-pauli-prepared-diagnostics")
    frames = prepared_prefix.check_prepared_frames(source, initial, preparation, numerical, witness, raw, diagnostic_raw)
    causal_raw, causal = prepared_prefix.project_prepared_prefix(source, initial, preparation, numerical, witness, frames, raw,
        diagnostic_raw, artifact_id="array.literal-pauli-prepared-causal")
    templates = {"generic_basis": factor,
        "force_coefficients": np.stack((np.eye(3), np.eye(3))).astype("<f8") / np.sqrt(6),
        "trace_coefficients": np.ones((2, 3), dtype="<f8") / np.sqrt(6),
        "receiver_coefficients": np.eye(48, dtype="<f8").reshape(48, 2, 2, 3, 4)}
    template_raw, template_members = encode_matrix_arrays(templates)
    protocol = replace(protocol, templates=replace(protocol.templates, members=template_members,
        array_artifact=replace(protocol.templates.array_artifact, sha256=sha256(template_raw).hexdigest(), size_bytes=len(template_raw))))
    return source, protocol, causal, causal_raw, template_raw


def test_prepared_mechanical_forecast_preserves_five_methods_and_cold_independent_derivatives(case, monkeypatch):
    source, protocol, causal, *_ = case
    assert causal.disposition == "AVAILABLE"
    raw, forecast = method.forecast(*case, artifact_id="array.literal-prepared-mechanical")
    retained = decode_matrix_arrays(raw, forecast.arrays)
    assert forecast.source == source.identity and forecast.disposition == "AVAILABLE"
    assert len(forecast.predictor_dispositions) == 10
    assert retained["receivers"].shape == (48, 2, 2, 3, 4, 4)
    assert all(retained[view + "_hessian"].shape == (96, 96) for view in ("primary", "fine"))

    def forbidden(*args, **kwargs):
        raise AssertionError("prepared cold mechanical reader entered producer, RNG or eigensolve")

    monkeypatch.setattr(shared_forecast, "_hessian", forbidden)
    monkeypatch.setattr(np.linalg, "eigh", forbidden)
    monkeypatch.setattr(np.random, "Generator", forbidden)
    monkeypatch.setattr(preparation_science, "acquire_preparation", forbidden)
    reloaded_raw, reloaded = method.forecast(*case, artifact_id=forecast.arrays.array_artifact.artifact_id, retained=retained, raw=raw)
    assert reloaded == forecast and reloaded_raw == raw
    changed = {name: value.copy() for name, value in retained.items()}
    changed["fine_hessian"][0, 0] += .1
    with pytest.raises(ValueError, match="literal potential derivative"):
        method.forecast(*case, artifact_id="array.forbidden-prepared-Hessian", retained=changed)


def test_prepared_mechanical_forecast_rejects_selected_causal_bytes_and_protocol_identity(case):
    source, protocol, causal, causal_raw, template_raw = case
    with pytest.raises(ValueError):
        method.forecast(source, protocol, causal, causal_raw[:-1], template_raw, artifact_id="array.forbidden-prepared-causal")
    with pytest.raises(ValueError, match="source"):
        method.forecast(source, replace(protocol, public_source=replace(protocol.public_source,
            source=replace(protocol.public_source.source, object_fingerprint="f" * 64))), causal, causal_raw, template_raw,
            artifact_id="array.forbidden-prepared-protocol")


def test_prepared_mechanical_cold_reader_detects_changed_fine_prediction(case):
    raw, forecast = method.forecast(*case, artifact_id="array.literal-prepared-prediction")
    retained = {name: value.copy() for name, value in decode_matrix_arrays(raw, forecast.arrays).items()}
    retained["fine_full_coupled"][0, 0, 0] += .01
    with pytest.raises(ValueError, match="frozen forces/receivers/predictions/witnesses"):
        method.forecast(*case, artifact_id="array.forbidden-prepared-prediction", retained=retained)



def test_prepared_cold_forecast_reuses_only_its_exact_received_archive(case, monkeypatch):
    from empirical_lawhood.infrastructure import matrix_array_io
    raw, forecast = method.forecast(*case, artifact_id="array.literal-prepared-reuse")
    retained = decode_matrix_arrays(raw, forecast.arrays)
    expected_raw, expected = method.forecast(*case, artifact_id=forecast.arrays.array_artifact.artifact_id,
        retained=retained, raw=raw)
    calls = []
    actual_decode = matrix_array_io._decode_matrix_arrays

    def decode(received, operand):
        if received is raw:
            calls.append(operand)
        return actual_decode(received, operand)

    monkeypatch.setattr(matrix_array_io, "_decode_matrix_arrays", decode)
    selected = matrix_array_io.DecodedMatrixArrayInput(raw, forecast.arrays)
    original_decode = method.decode_matrix_arrays

    def no_repeat(received, operand):
        if received is raw:
            pytest.fail("independent cold forecast expanded its received forecast twice")
        return original_decode(received, operand)

    monkeypatch.setattr(method, "decode_matrix_arrays", no_repeat)
    monkeypatch.setattr(shared_forecast, "_hessian", lambda *_args: pytest.fail("cold reuse entered Hessian producer"))
    monkeypatch.setattr(np.linalg, "eigh", lambda *_args: pytest.fail("cold reuse entered eigensolve"))
    actual_raw, actual = method.forecast(*case, artifact_id=forecast.arrays.array_artifact.artifact_id,
        retained_input=selected, raw=raw)
    assert calls == [forecast.arrays]
    assert actual_raw == expected_raw == raw
    assert actual == expected == forecast and actual.canonical_bytes() == expected.canonical_bytes()
    with pytest.raises(ValueError, match="exact original operand"):
        method.forecast(*case, artifact_id="array.foreign-prepared-reuse", retained_input=selected, raw=raw)



def test_prepared_cold_forecast_refuses_duck_typed_decoded_holder_before_arrays(case, monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(method, "decode_matrix_arrays", lambda *_args:
        pytest.fail("forged decoded holder reached array expansion"))
    forged = SimpleNamespace(original=object(), for_operand=lambda *_args:
        pytest.fail("forged decoded holder supplied fabricated arrays"))
    with pytest.raises(TypeError, match="actual decoded retained input"):
        method.forecast(*case, artifact_id="array.forbidden-forged-reuse", retained_input=forged, raw=b"forged")
