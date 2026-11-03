# SPDX-License-Identifier: MPL-2.0
"""Disclosed supplied-innovation progress controls, never scientific evidence.

The equation tests use complete toy arrays. Lifecycle seams below use explicit
metadata-only stores to isolate emitter forwarding and recovery; they create no
real contact, receipt, grant, source qualification or production result.
"""
from decimal import Decimal
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import preparation_science
from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_native_body
from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_future_custody
from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_response_science
from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_bindings, response_science
from empirical_lawhood.infrastructure.execution import _DirectProgressEmitter
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays, encode_matrix_arrays
from empirical_lawhood.runtime.native_subwork import NativeSubworkState
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.kernel.time import validate_utc_timestamp
from tests import test_matrix_coupling_preparation as preparation_fixture
from tests import test_matrix_prepared_response_method as response_fixture


@pytest.fixture
def prepared_case(tmp_path):
    return response_fixture.case.__wrapped__(tmp_path)


def exact_arrays(left, right):
    assert set(left) == set(right)
    assert all(a.dtype.str == right[name].dtype.str and a.shape == right[name].shape
        and a.tobytes() == right[name].tobytes() for name, a in left.items())
    assert encode_matrix_arrays(left)[0] == encode_matrix_arrays(right)[0]


@pytest.mark.parametrize("seeded", (False, True))
def test_preparation_actual_paired_work_preserves_every_array_and_rng_bytes(tmp_path, seeded):
    metadata = preparation_fixture.metadata.__wrapped__(tmp_path)
    source, raw, coarse, bridge, _ = preparation_fixture.selected.__wrapped__(metadata)
    counts = []
    if seeded:
        original = preparation_science.acquire_preparation(source, raw)
        observed = preparation_science.acquire_preparation(source, raw, on_step=counts.append)
    else:
        original = preparation_science.propagate_preparation(source, raw,
            coarse_innovations=coarse, bridge_innovations=bridge)
        observed = preparation_science.propagate_preparation(source, raw,
            coarse_innovations=coarse, bridge_innovations=bridge, on_step=counts.append)
    exact_arrays(original, observed)
    assert counts == [3 * step for step in range(1, source.total_ticks + 1)]


def scheduled_operands(case, monkeypatch):
    """Supply literal noise; metadata seam makes no actual source-custody claim."""
    source, _, preparation, prefix_raw, protocol, panels, forecast, frozen_raw, innovations = case
    selected = SimpleNamespace(coordinate=source.coordinate,
        policy=SimpleNamespace(cutoff_tick=source.total_ticks), root=source.root)
    instrument = SimpleNamespace(public_source=SimpleNamespace(validate_source=lambda _: None),
        horizon_steps=protocol.horizon_steps, actions=protocol.actions)
    prefix = decode_matrix_arrays(prefix_raw, preparation)
    frozen = decode_matrix_arrays(frozen_raw, forecast)
    monkeypatch.setattr(response_science, "panel_innovations", lambda _source, _history, panel, _horizon: innovations[panel.panel_id])
    return selected, None, prefix, instrument, panels, frozen


def test_scheduled_48_branches_emit_monotone_actual_steps_without_changing_bytes(prepared_case, monkeypatch):
    operands = scheduled_operands(prepared_case, monkeypatch)
    original = response_science.native_responses(*operands)
    counts = []
    observed = response_science.native_responses(*operands, on_step=counts.append)
    exact_arrays(original, observed)
    assert counts == list(range(1, 72 * operands[3].horizon_steps[-1] + 1))


def test_prepared_48_branches_emit_monotone_actual_steps_without_changing_bytes(prepared_case):
    original = prepared_response_science.propagate_prepared_responses(*prepared_case)
    counts = []
    observed = prepared_response_science.propagate_prepared_responses(*prepared_case, on_step=counts.append)
    exact_arrays(original, observed)
    assert counts == list(range(1, 72 * prepared_case[4].horizon_steps[-1] + 1))


class DisclosedStore:
    """Metadata-only lifecycle recorder; cannot publish a scientific receipt."""
    def __init__(self, raw=None):
        self.raw = raw
        self.entered = 0
        self.call_observations = []
        self.completed = SimpleNamespace(state=NativeSubworkState.COMPLETED, receipt=object(),
            completion=SimpleNamespace(operational_status=OperationalStatus.SUCCEEDED))

    def recover(self, _definition):
        return None if self.raw is None else self.completed

    def inspect(self, _definition):
        return SimpleNamespace(state=NativeSubworkState.NOT_ENTERED)

    def freeze_roster(self, *_args, **_kwargs):
        return None

    def begin(self, _definition):
        self.entered += 1
        return object()

    def contact(self, _entry):
        return None

    def call_entry(self, _entry, *, at_utc):
        self.call_observations.append(("entry", validate_utc_timestamp(at_utc), None))

    def call_return(self, _entry, *, at_utc, error_type=None):
        self.call_observations.append(("return", validate_utc_timestamp(at_utc), error_type))

    def publish_output(self, _entry, _output, chunks, **_kwargs):
        assert tuple(row[0] for row in self.call_observations) == ("entry", "return")
        assert self.call_observations[-1][2] is None
        self.raw = b"".join(chunks)

    def complete(self, _entry, **_kwargs):
        return self.completed

    def iter_completed_output(self, _definition, _output):
        return iter((self.raw,))


def test_scheduled_owner_forwards_real_decimal_emitter_and_completed_recovery_emits_nothing(prepared_case, monkeypatch):
    source, history, prefix, protocol, panels, frozen = scheduled_operands(prepared_case, monkeypatch)
    # Only publication/identity seams are disclosed: the complete native response
    # equations and stock decoder still run over every supplied branch/member.
    monkeypatch.setattr(response_bindings, "identity", lambda _source: object())
    monkeypatch.setattr(response_bindings, "array_product", lambda _protocol, arrays, **_kwargs: (encode_matrix_arrays(arrays)[0], None))
    definition = SimpleNamespace(streams=())
    work = SimpleNamespace(definitions=(definition,), rosters=(object(),))
    counts = []
    emitter = _DirectProgressEmitter(counts.append)
    store = DisclosedStore()
    raw, arrays, _, _ = response_bindings.execute_paired_response_native_work(source, work, store,
        protocol=protocol, panels=panels, history=history, prefix=prefix, frozen=frozen,
        selection=object(), progress=emitter)
    assert store.entered == 1
    assert tuple(row[0] for row in store.call_observations) == ("entry", "return")
    assert counts == [Decimal(step) for step in range(1, 72 * protocol.horizon_steps[-1] + 1)]
    assert all(type(value) is Decimal for value in counts)
    monkeypatch.setattr(response_bindings, "native_responses", lambda *_args, **_kwargs: pytest.fail("recovery entered native math"))
    recovered_counts = []
    recovered_store = DisclosedStore(raw)
    recovered, received, _, _ = response_bindings.execute_paired_response_native_work(source, work, recovered_store,
        protocol=protocol, panels=panels, history=history, prefix=prefix, frozen=frozen,
        selection=object(), progress=_DirectProgressEmitter(recovered_counts.append))
    assert recovered == raw and recovered_store.entered == 0 and recovered_counts == []
    assert recovered_store.call_observations == []
    exact_arrays(arrays, received)


def test_prepared_owner_forwards_real_decimal_emitter_and_completed_recovery_emits_nothing(prepared_case, monkeypatch):
    source, initial, preparation, preparation_raw, protocol, panels, forecast, frozen_raw, _ = prepared_case
    config = SimpleNamespace(source=source, protocol=protocol, panels=panels)
    history = SimpleNamespace(arrays=preparation)
    causal = SimpleNamespace(disposition="AVAILABLE")
    mechanical = SimpleNamespace(disposition="AVAILABLE", arrays=forecast)
    streams = tuple(sorted((prepared_future_custody.stream_id(config, panel, stream) for panel in panels for stream in panel.streams),
        key=lambda row: row.object_id))
    definition = SimpleNamespace(streams=streams)
    work = SimpleNamespace(definitions=(definition,), rosters=(object(),))
    # Do not manufacture native custody records for this metadata-only store.
    monkeypatch.setattr(prepared_native_body, "MatrixParameterNativeHistory", lambda *_args: object())
    counts = []
    store = DisclosedStore()
    arrays, raw, _, disposition = prepared_native_body._execute_future_native(config, history, causal, mechanical,
        initial, preparation_raw, frozen_raw, store, work, progress=_DirectProgressEmitter(counts.append))
    assert disposition == "COMPLETED" and store.entered == 1
    assert tuple(row[0] for row in store.call_observations) == ("entry", "return")
    assert counts == [Decimal(step) for step in range(1, 72 * protocol.horizon_steps[-1] + 1)]
    monkeypatch.setattr(prepared_future_custody, "acquire_future", lambda *_args, **_kwargs: pytest.fail("recovery acquired future"))
    recovered_counts = []
    recovered_store = DisclosedStore(raw)
    received, recovered, _, disposition = prepared_native_body._execute_future_native(config, history, causal, mechanical,
        initial, preparation_raw, frozen_raw, recovered_store, work, progress=_DirectProgressEmitter(recovered_counts.append))
    assert recovered == raw and disposition == "COMPLETED" and recovered_store.entered == 0 and recovered_counts == []
    assert recovered_store.call_observations == []
    exact_arrays(arrays, received)
