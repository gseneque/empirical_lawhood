# SPDX-License-Identifier: MPL-2.0
"""Pure downstream E2 nonuse validation order; no native task or authority."""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_bindings as bindings
from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_records as r
from tests.test_matrix_native_utility_nonentry import metadata as original_metadata, _nonentry


@pytest.fixture
def metadata(tmp_path):
    return original_metadata.__wrapped__(tmp_path)


@pytest.mark.parametrize("defect", (None, "reason", "hash", "available-future"))
def test_actual_e2_score_consumer_checks_exact_nonentry_before_pure_scoring(metadata, monkeypatch, defect):
    causal, physical, response = _nonentry(metadata, "AVAILABLE",
        "AVAILABLE" if defect == "available-future" else "INSTRUMENT_UNRESOLVED")
    if defect == "reason":
        response = replace(response, reason_codes=("resealed-wrong-nonentry-reason",))
    elif defect == "hash":
        member, = response.arrays.members
        response = replace(response, arrays=replace(response.arrays,
            members=(replace(member, sha256="f" * 64),)))
    # All four records can be canonically resealed. The three adverse cases
    # violate the cross-record owner relation: exact unavailable reason,
    # actual complete arange marker, or availability requiring native work.
    response.canonical_bytes()
    config = SimpleNamespace(protocol=metadata.protocol, panels=metadata.panels)
    records = dict(history=SimpleNamespace(arrays=object()), causal=causal, physical=physical,
        responses=response, acquisition=metadata.case.acquisition)
    context = SimpleNamespace(input_ports=(), output_ports=())
    monkeypatch.setattr(bindings, "_decode", lambda *args, **kwargs: (
        config, metadata.case.specification, metadata.source, records, {}))
    monkeypatch.setattr(bindings, "_values", lambda *args, **kwargs: {})
    events = []
    validate = r.NativeUtilityResponse.validate_nonentry
    def checked(self, *args):
        events.append("nonentry")
        return validate(self, *args)
    monkeypatch.setattr(r.NativeUtilityResponse, "validate_nonentry", checked)
    def score(*args, **kwargs):
        if defect is not None:
            pytest.fail("invalid nonentry reached pure response scoring")
        events.append("score")
        return object(), object()
    monkeypatch.setattr(bindings.science, "score", score)
    monkeypatch.setattr(bindings, "_outputs", lambda *args, **kwargs: object())
    def forbidden(*args, **kwargs):
        pytest.fail("pure score-consumer control entered native work")
    monkeypatch.setattr(bindings, "execute_parameter_native_work", forbidden)
    monkeypatch.setattr(bindings, "execute_paired_response_native_work", forbidden)
    if defect is None:
        bindings.NativeUtilityRunner("response-score").execute(context)
        assert events == ["nonentry", "score"]
    else:
        with pytest.raises(ValueError, match="native E2 response nonentry changes"):
            bindings.NativeUtilityRunner("response-score").execute(context)
        assert events == ["nonentry"]
