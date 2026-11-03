# SPDX-License-Identifier: MPL-2.0
"""Exact current and historical E4 native contracts over disclosed metadata.

These controls perform no native work and confer no scientific authority.
"""
from dataclasses import replace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as dev
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_bindings as protected
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as records
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_programme as programme
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_native_source import bind_selected_native_source
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.test_matrix_selected_e4_methods import selected_revision, selected_e4_populations, selected_bridge, transfer  # noqa: F401


def test_actual_development_graph_versions_cover_root_and_future_streams(selected_bridge):  # noqa: F811
    f = selected_bridge
    current = dev.contracts(f.programme, f.bank, f.evidence.identity, len(f.evidence.canonical_bytes()), secondary_readout=f.secondary_readout, produced_input_parents=f.evidence.produced_input_parents)
    historical = dev.contracts(f.programme, f.bank, f.evidence.identity, len(f.evidence.canonical_bytes()), direct_operands=False, secondary_readout=f.secondary_readout, produced_input_parents=f.evidence.produced_input_parents)
    assert current[0] == historical[0]  # Native capability selections carry the graph revision.
    source = f.bank.sources[0]
    node = dev.local_node(source.root_id, "responses")
    selected = {row.consumer_input_id: row for row in current[2] if row.consumer_node_id == node}
    old = {row.consumer_input_id: row for row in historical[2] if row.consumer_node_id == node}
    assert set(selected) - set(old) == {"checkpoint", *("streams." + str(index) for index in range(4, 8))}
    assert old.keys() <= selected.keys()
    assert selected["checkpoint"].producer_node_id == dev.local_node(source.root_id, "prefix")
    assert selected["checkpoint"].producer_output_id == "checkpoint"
    configs = dict(current[0])
    config = configs[node]
    direct_records = dict(current[3])
    streams = tuple(direct_records[selected["streams." + str(index)].external_input_id] for index in range(8))
    independent, = (panel for panel in config.panels if panel.role == "INDEPENDENT_FUTURE")
    assert streams == (*config.source.root.streams, *independent.streams)
    assert len({row.effective_seed for row in streams}) == 8
    for phase in dev.NATIVE:
        declaration, = (row for row in dev.operation_declarations() if row.capability_key == dev.NAMESPACE + "." + phase)
        assert declaration.capability_version == "3.0.0"
        stream_port, = (row for row in declaration.input_ports if row.port_id == "streams")
        assert (stream_port.minimum_count, stream_port.maximum_count) == ((8, 8) if phase == "responses" else (4, 4))


@pytest.mark.parametrize("phase", dev.NATIVE)
def test_native_direct_carriers_and_historical_rosters_are_explicit(selected_revision, phase):  # noqa: F811
    f = selected_revision
    decision = programme.SelectedE4PublicRevisionDecision.from_products(f.programme, f.nomination, f.frozen, record_id="decision.direct-control")
    models = programme.SelectedE4PublicModels.from_products(f.programme, f.nomination, f.frozen, record_id="models.direct-control")
    summary = programme.SelectedE4OriginalCalibrationSummary.from_package(f.populations.selected.package, record_id="summary.direct-control")
    selected, bank = f.populations.calibration, f.populations.calibration_bank
    source = records.SelectedE4ProtectedNativeSourceReference.from_bank(selected, bank, bank.sources[0],index=bank.source_index())
    protocol, panels = bank.response_selection.validate_source(bank.source(source.root_id,index=bank.source_index()))
    config = protected.SelectedE4ProtectedCompactConfig("config." + protected.local_node(source.root_id, phase), selected.identity,
        source, protocol, panels, bank.response_selection.identity, phase, "CALIBRATION", decision, models, None, summary)
    provenance, = (row for row in bank.provenances if row.identity == source.provenance)
    bound = bind_selected_native_source(source, provenance)
    raw = config.canonical_bytes()
    current = protected.native_contract(config, bound)
    assert current[0] == ObjectIdentity.from_record(config.config_id, config)
    assert set(current[3]) == {source.identity, provenance.identity}
    assert current[2].endswith(".direct-operands.v2")
    stem = current[2].removesuffix(".direct-operands.v2")
    with pytest.raises(ValueError,match="operation revision"):
        protected.native_contract(config,bound,recorded_operation=stem+".v1")
    assert config.canonical_bytes() == raw == decode_canonical_bytes(raw, type(config), maximum_bytes=len(raw)).canonical_bytes()
    with pytest.raises(ValueError, match="operation revision"):
        protected.native_contract(config, bound, recorded_operation=stem + ".unknown-v99")
    changed = replace(source, record_id="source.foreign-carrier")
    with pytest.raises(ValueError, match="current local configuration"):
        protected.native_contract(config, bind_selected_native_source(changed, provenance))
    for declaration in protected.operation_declarations():
        if declaration.capability_key.rsplit(".", 1)[-1] == phase:
            assert declaration.capability_version == "3.0.0"
            if phase == "responses":
                assert "checkpoint" in {row.port_id for row in declaration.input_ports}
                port, = (row for row in declaration.input_ports if row.port_id == "streams")
                assert (port.minimum_count, port.maximum_count) == (8, 8)
