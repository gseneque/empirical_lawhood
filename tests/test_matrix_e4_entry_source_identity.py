# SPDX-License-Identifier: MPL-2.0
# ruff: noqa: F811
"""Exact admitted descriptor pins through the real DEV decoder, without effects.

Existing disclosed full32x9 metadata and actual in-memory TaskContext/CONFIG
contracts are software premises only. No producer, qualification, current grant,
native RNG, integrator, executor, acquisition or physical receipt is fabricated.
"""
from dataclasses import replace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as bindings
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as records
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_workers as worker
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_native_source import selected_stream_operands
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
from tests.test_matrix_selected_e3_e4_workers import invocation
from tests.test_matrix_selected_e3_e4_bridge import selected_bridge, transfer  # noqa: F401


def _case(fixture, *, damage=None):
    index = fixture.bank.source_index()
    local = records.SelectedE3E4NativeSourceReference.from_bank(fixture.programme, fixture.bank,
        fixture.bank.sources[0], index=index)
    protocol = next(value for value in fixture.bank.response_selection.protocols
        if value.public_source.root.root_id == local.root_id)
    panels = dict(fixture.bank.response_selection.panels)[local.root.root.independent_group_id]
    config = bindings.SelectedE3E4CompactConfig("config." + bindings.local_node(local.root_id, "prefix"),
        fixture.programme.identity, local, protocol, panels, fixture.bank.response_selection.identity, "prefix")
    seal = records.entry_seal(fixture.programme, fixture.evidence, secondary_readout=fixture.secondary_readout)
    selected = local.descriptor.identity
    assert selected in seal.sources and identity(local) not in seal.sources
    if damage in ("descriptor-fingerprint", "wrapper-instead-of-descriptor"):
        foreign = (replace(selected, object_fingerprint="f" * 64)
            if damage == "descriptor-fingerprint" else identity(local))
        seal = replace(seal, sources=tuple(sorted((foreign if pin == selected else pin for pin in seal.sources),
            key=lambda pin: pin.object_id)))
    elif damage == "programme":
        seal = replace(seal, programme=replace(seal.programme, object_fingerprint="f" * 64))
    source = (records.SelectedE3E4NativeSourceReference.from_bank(fixture.programme, fixture.bank,
        fixture.bank.sources[1], index=index) if damage == "local-source-bytes" else local)
    provenance = next(value for value in fixture.bank.provenances if value.identity == local.provenance)
    values = {"entry": seal, "source": source, "provenance": provenance,
        **{"streams." + str(i): value for i, (_, value) in enumerate(
            selected_stream_operands(local, panels, include_future=False))}}
    runner, context = invocation(config, values, {"entry": bindings.global_node(fixture.programme, "entry")})
    # Honest metadata-only native preparation: complete frozen task and input
    # contracts exist, but no prepared work, contact or Ready assertion exists.
    prepared = replace(context.prepared_invocation, native_effect=True)
    return config, local, seal, runner, replace(context, prepared_invocation=prepared)


def _deny_effects(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail("descriptor membership entered a native effect or executor")
    monkeypatch.setattr(worker, "execute_native", forbidden)
    monkeypatch.setattr(LocalProcessExecutor, "execute", forbidden)


def test_real_prepared_decoder_uses_entry_admitted_descriptor_not_transport_identity(selected_bridge, monkeypatch):
    config, local, seal, runner, context = _case(selected_bridge)
    _deny_effects(monkeypatch)
    try:
        actual, received, arrays = worker._decode(context, runner)
        assert actual == config and received["source"] == local and received["entry"] == seal
        assert arrays == {} and len(seal.sources) == 288 and len(seal.groups) == 32
        assert local.descriptor.identity == local.public.source
        assert context.prepared_invocation.native_work is None
    finally:
        for port in context.input_ports:
            port.close()


@pytest.mark.parametrize("damage,reason", (("descriptor-fingerprint", "not admitted by the original whole programme"),
    ("wrapper-instead-of-descriptor", "not admitted by the original whole programme"),
    ("programme", "actual successful source-entry seal"), ("local-source-bytes", "exact local native source bytes")))
def test_real_prepared_decoder_refuses_foreign_descriptor_seal_or_local_bytes(selected_bridge, monkeypatch, damage, reason):
    _, _, _, runner, context = _case(selected_bridge, damage=damage)
    _deny_effects(monkeypatch)
    try:
        with pytest.raises(ValueError, match=reason):
            worker._decode(context, runner)
        assert context.prepared_invocation.native_work is None
    finally:
        for port in context.input_ports:
            port.close()
