# SPDX-License-Identifier: MPL-2.0
# ruff: noqa: F811
"""Protected native-prefix decoder membership, without native work or grants.

The existing disclosed 32/64/64 fixture supplies unchanged mathematics and
population metadata. In-memory prepared contracts and synthetic dependency
receipt bindings exercise the actual decoder only; they establish no issued
source, reveal permission, Ready proof, native contact or scientific result.
"""
from dataclasses import replace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_bindings as bindings
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as records
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_programme as programme_owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_protected_workers as worker
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_native_source import selected_stream_operands
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.test_matrix_selected_e4_fixtures import selected_e4_populations, selected_bridge, transfer  # noqa: F401
from tests.test_matrix_selected_e4_methods import selected_revision  # noqa: F401
from tests.test_matrix_selected_e4_native_workers import _invocation


def _prefix_case(fixture, *, damage=None):
    programme, bank = fixture.populations.calibration, fixture.populations.calibration_bank
    wave = programme.waves[0]
    descriptor = next(value for value in bank.sources if value.root_id == wave.root_ids[0])
    source = records.SelectedE4ProtectedNativeSourceReference.from_bank(programme, bank, descriptor,
        index=bank.source_index())
    protocol, panels = bank.response_selection.validate_source(
        bank.source(descriptor.root_id, index=bank.source_index()))
    decision = programme_owner.SelectedE4PublicRevisionDecision.from_products(fixture.programme,
        fixture.nomination, fixture.frozen, record_id="decision.disclosed-protected-prefix-membership")
    models = programme_owner.SelectedE4PublicModels.from_products(fixture.programme,
        fixture.nomination, fixture.frozen, record_id="models.disclosed-protected-prefix-membership")
    summary = programme_owner.SelectedE4OriginalCalibrationSummary.from_package(
        fixture.populations.selected.package, record_id="summary.disclosed-protected-prefix-membership")
    config = bindings.SelectedE4ProtectedCompactConfig("config." + bindings.local_node(source.root_id, "prefix"),
        programme.identity, source, protocol, panels, bank.response_selection.identity, "prefix", "CALIBRATION",
        decision, models, None, summary)
    evidence = ObjectIdentity("evidence.unissued-protected-prefix-membership", records.SelectedE4ProtectedEvidence.SCHEMA,
        records.SelectedE4ProtectedEvidence.VERSION, "a" * 64)
    seal = records.SelectedE4ProtectedEntrySeal("entry.disclosed-protected-prefix-membership", programme.identity,
        bank.identity, programme.forecast_design, evidence, wave.group_ids,
        tuple(value.source for value in programme.cases if value.root_id in wave.root_ids),
        "CALIBRATION", wave.wave_id, None, decision.identity, models.identity, None, secondary_readout=fixture.populations.secondary_readout.identity)
    selected = source.descriptor.identity
    assert selected in seal.sources and identity(source) not in seal.sources
    if damage is not None:
        foreign = (replace(selected, object_fingerprint="f" * 64)
            if damage == "descriptor-fingerprint" else identity(source))
        seal = replace(seal, sources=tuple(sorted((foreign if pin == selected else pin for pin in seal.sources),
            key=lambda pin: pin.object_id)))
    provenance = next(value for value in bank.provenances if value.identity == source.provenance)
    values = {"entry": seal, "source": source, "provenance": provenance,
        **{"streams." + str(index): value for index, (_, value) in enumerate(
            selected_stream_operands(source, panels, include_future=False))}}
    runner, context = _invocation(config, values, {"entry": bindings.global_node(programme, "entry", wave.wave_id)})
    prepared = replace(context.prepared_invocation, native_effect=True)
    return programme, config, source, seal, runner, replace(context, prepared_invocation=prepared)


def _deny_effects(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail("protected descriptor membership entered native preparation, acquisition or executor")
    monkeypatch.setattr(worker, "initial_native_work", forbidden)
    monkeypatch.setattr(worker, "execute_native", forbidden)
    monkeypatch.setattr(LocalProcessExecutor, "execute", forbidden)


def test_real_protected_prefix_decoder_uses_exact_entry_admitted_descriptor(selected_revision, monkeypatch):
    programme, config, source, seal, runner, context = _prefix_case(selected_revision)
    _deny_effects(monkeypatch)
    try:
        actual, received, arrays = worker._decode(context, runner)
        assert actual == config and received["source"] == source and received["entry"] == seal
        assert source.descriptor.identity == source.reference.identity == source.public.source
        assert arrays == {} and len(programme.group_ids) == 64 and len(programme.cases) == 576
        assert len(seal.groups) == 4 and len(seal.sources) == 36
        assert context.prepared_invocation.native_work is None
    finally:
        for port in context.input_ports:
            port.close()


@pytest.mark.parametrize("damage", ("descriptor-fingerprint", "wrapper-instead-of-descriptor"))
def test_real_protected_prefix_decoder_refuses_foreign_descriptor_or_wrapper_only_seal(selected_revision,
        monkeypatch, damage):
    _, _, _, _, runner, context = _prefix_case(selected_revision, damage=damage)
    _deny_effects(monkeypatch)
    try:
        with pytest.raises(ValueError, match="not admitted by the original whole programme"):
            worker._decode(context, runner)
        assert context.prepared_invocation.native_work is None
    finally:
        for port in context.input_ports:
            port.close()
