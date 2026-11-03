# SPDX-License-Identifier: MPL-2.0
"""Valid public-worker instrument inputs; no native acquisition or authority.

The existing AVAILABLE response operand is authored software data. The complete
future below is another disclosed literal negative, never acquired evidence.
"""

from hashlib import sha256
import json

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_forecast import instrument
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_science import receiver_metric
from empirical_lawhood.infrastructure.execution import _prepare_native_work
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.runtime.execution import VerifiedArtifactInput
from tests.test_matrix_e3_protected_encoding_acceptance import assess, received_negative
from tests.test_matrix_e3_public_programme import _selected_case
from tests.test_matrix_e3_response_lifecycle_available import available as available
from tests.test_matrix_e3_response_preparation import case as case, original_case as original_case, prepared
from tests.test_matrix_e3_response_science import blocked, byte_fetch, no_native as no_native, store


@pytest.fixture(autouse=True)
def no_native_contact(monkeypatch, no_native):  # noqa: F811
    for owner, names in ((ExternalNativeEffectContactStore, ("begin",)), (ExternalNativeSubworkStore, ("begin", "contact"))):
        for name in names:
            monkeypatch.setattr(owner, name, blocked)


def test_public_original_instrument_matches_existing_available_owner_before_lowering(available, tmp_path):
    from tests import test_matrix_e3_protected_source_records as originals

    historical_encoder = originals.encode_matrix_arrays
    selected = _selected_case(tmp_path / "public", "small")
    assert originals.encode_matrix_arrays is historical_encoder
    publication, = selected.response_selection.template_publications
    port = selected.plane.open(VerifiedArtifactInput(publication.logical, publication.materialization), maximum_bytes=None)
    try:
        raw = port.read()
    finally:
        port.close()
    values = decode_matrix_arrays(raw, selected.protocols[0].templates)
    original_raw = store(available)[available.protocol.templates.array_artifact.artifact_id]
    expected = decode_matrix_arrays(original_raw, available.protocol.templates)
    assert raw == original_raw
    assert set(values) == {"generic_basis", "force_coefficients", "trace_coefficients", "receiver_coefficients"}
    for name in values:
        assert values[name].dtype == expected[name].dtype and values[name].shape == expected[name].shape
        assert np.array_equal(values[name], expected[name])
    frame = decode_matrix_arrays(available.causal_raw, available.causal.arrays)["frame"]
    frozen = decode_matrix_arrays(available.physical_raw, available.physical.arrays)
    forces, receivers, (spectrum, _) = instrument(selected.protocols[0], frame, values,
        witnesses=(frozen["complement_spectrum"], frozen["complement_eigenvectors"]))
    assert forces.shape == (4, 2, 3, 4, 4) and receivers.shape == (48, 2, 2, 3, 4, 4)
    assert np.allclose(np.linalg.norm(forces.reshape(4, -1), axis=1), [float(row.force_norm) for row in selected.protocols[0].actions])
    assert spectrum[0] > float(selected.protocols[0].complement_gram_minimum)
    assert max(receiver_metric(selected.protocols[0], receivers)) < selected.protocols[0].receiver_gram_tolerance
    assert all(protocol.templates.array_artifact.sha256 == sha256(raw).hexdigest() for protocol in selected.protocols)
    assert len(selected.lowered.draft.operations) == 96
    (tmp_path / "public-instrument.json").write_text(json.dumps({
        "scope": "Disclosed software instrument only; no acquisition, qualification or complete public execution claim",
        "template_sha256": sha256(raw).hexdigest(), "template_size_bytes": len(raw),
        "member_count": len(values), "protocols": len(selected.protocols), "derived_tasks": 96,
        "matches_existing_available_instrument_bytes": True, "historical_encoder_restored": True,
    }, indent=2) + "\n")


def test_available_instrument_enters_current_native_preparer_and_complete_negative_reader_without_acquisition(available, tmp_path):
    from empirical_lawhood.adapters.methods.matrix_factor_response import protected_response_bindings

    selected = prepared(available)
    try:
        work = _prepare_native_work(protected_response_bindings.prepare_native_work,
            selected.runner, selected.bound, selected.parent)
        assert work == selected.contract.native_work
        definition, = work.definitions
        assert len(definition.streams) == 8 and len(definition.sources) == 15
        assert tuple(row.output_id for row in definition.outputs) == ("arrays",)
        assert all(port.bytes_read == 0 for port in selected.bound.input_ports if port.media_type == "application/x-npz")
    finally:
        for port in selected.bound.input_ports:
            port.close()
    received = received_negative(available)
    score, outcome = assess(received, byte_fetch(store(received)))
    assert score.disposition == "NATIVE_CROSSCHECK_FAILED" and not score.numerical_pass
    assert len(received.response.arrays.members) == 246 and len(score.cells) == 240 and len(score.controls) == 48
    assert sum(row.denominator_steps for row in score.controls) == 24 * (128 + 256)
    assert all(row.denominator_real_coordinates == 192 for row in score.controls)
    assert all(view.errors == (None,) * 15 for view in outcome.views)
    (tmp_path / "native-preparation-and-negative-score.json").write_text(json.dumps({
        "scope": "Current guarded native metadata preparation and original literal negative reader; no native execution",
        "native_definition": definition.fingerprint(), "native_direct_inputs": len(definition.sources),
        "streams": len(definition.streams), "response_members": len(received.response.arrays.members),
        "score_cells": len(score.cells), "controls": len(score.controls),
        "transition_steps": sum(row.denominator_steps for row in score.controls),
        "score_disposition": score.disposition, "score_sha256": score.fingerprint(), "outcome_sha256": outcome.fingerprint(),
    }, indent=2) + "\n")
