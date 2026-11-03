# SPDX-License-Identifier: MPL-2.0
"""Standalone full-provenance transport controls; no issue or native execution.

The 3,068-file record is a disclosed release fixture sized above the observed
392,101-byte census. This tests transport capacity, never scientific freshness.
Actual selected bytes are measured separately by held workflow acceptance.
"""
from dataclasses import replace
from hashlib import sha256

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as legacy
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as dev
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as development
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as protected
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_native_source import bind_selected_native_source,source_transport
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from tests.test_matrix_selected_e3_e4_bridge import selected_bridge, transfer  # noqa: F401
from tests.test_matrix_selected_e4_fixtures import selected_e4_populations  # noqa: F401


def large_provenance(original):
    files = tuple(("src/disclosed_release_control/owner_" + str(index).zfill(4) + "/native_source_contract.py",
        sha256(("disclosed-control." + str(index)).encode()).hexdigest()) for index in range(3068))
    return replace(original, package_sources=files,
        code_sources_sha256=sha256(canonical_json_bytes(files)).hexdigest())


@pytest.mark.parametrize("phase", ("development", "calibration", "confirmation"))
def test_full_actual_sized_provenance_binds_without_entering_compact_transport(selected_e4_populations, phase):  # noqa: F811
    f = selected_e4_populations
    programme, bank = getattr(f, phase), getattr(f, phase + "_bank")
    original = bank.source(bank.sources[0].root_id,index=bank.source_index())
    provenance = large_provenance(original.provenance)
    assert len(provenance.package_sources) == 3068 and len(provenance.canonical_bytes()) >= 392101
    index=ScheduledSourceIndex.from_shared(reservation=original.reservation,
        specification=original.specification,provenances=(provenance,))
    descriptor=index.reference(source_id=original.source_id,root_id=original.root_id,provenance=provenance.identity)
    subject=index.resolve(descriptor)
    kind = dev.SelectedE3E4NativeSourceReference if phase == "development" else protected.SelectedE4ProtectedNativeSourceReference
    transport = kind("native." + subject.source_id, programme.identity, bank.identity, descriptor,
        ScheduledPublicSource.from_source(subject), subject.policy, subject.numerical_design,
        provenance.identity, len(provenance.canonical_bytes()))
    raw = transport.canonical_bytes()
    assert len(raw) <= 256 * 1024 and b'"package_sources"' not in raw
    assert decode_canonical_bytes(raw, kind, maximum_bytes=None) == transport
    bound = bind_selected_native_source(transport, provenance)
    assert bound.provenance is provenance and bound.provenance.canonical_bytes() == provenance.canonical_bytes()
    assert legacy.identity(bound) == legacy.identity(subject) == transport.reference.identity
    assert bound.identity == transport.identity != transport.reference.identity
    assert not hasattr(bound,"canonical_bytes") and not hasattr(bound,"fingerprint")
    assert source_transport(bound).canonical_bytes()==raw
    assert bound.coordinate == subject.coordinate and bound.root == subject.root
    assert ScheduledPublicSource.from_source(bound) == transport.public
    assert decode_canonical_bytes(provenance.canonical_bytes(), type(provenance), maximum_bytes=None) == provenance
    with pytest.raises(ValueError, match="provenance identity"):
        bind_selected_native_source(transport, replace(provenance, observed_checkout_clean=not provenance.observed_checkout_clean))
    with pytest.raises(ValueError, match="exact size"):
        bind_selected_native_source(replace(transport, provenance_size_bytes=transport.provenance_size_bytes + 1), provenance)
    with pytest.raises(TypeError, match="full provenance"):
        bind_selected_native_source(transport, provenance.identity)


def test_whole_dev_graph_delivers_one_original_provenance_record_with_exact_direct_leaf_ports(selected_bridge):  # noqa: F811
    f = selected_bridge
    configs, external, links, records, _ = development.contracts(f.programme, f.bank,
        f.evidence.identity, len(f.evidence.canonical_bytes()), produced_input_parents=f.evidence.produced_input_parents,
        secondary_readout=f.secondary_readout)
    references = tuple(row for row in external if row.payload_schema == f.bank.provenances[0].SCHEMA)
    assert len(references) == len(f.bank.provenances) == 1
    reference, = references
    provenance, = f.bank.provenances
    assert dict(records)[reference.input_id] == provenance
    assert (reference.logical_artifact_id, reference.expected_content_sha256, reference.maximum_size_bytes) == (
        "selected-e4.provenance." + provenance.fingerprint(), provenance.fingerprint(), len(provenance.canonical_bytes()))
    selected = {node for node, config in configs if type(config) is development.SelectedE3E4CompactConfig}
    edges = tuple(row for row in links if row.consumer_input_id == "provenance")
    assert {row.consumer_node_id for row in edges} == selected
    assert len(edges) == len(selected) and all(row.external_input_id == reference.input_id and row.producer_node_id is None for row in edges)
    assert len(f.programme.cases) == 288 and len(f.programme.group_ids) == 32
    declarations = {row.capability_key: row for row in development.operation_declarations()}
    expected_versions = {"entry": "2.0.0", "reduce": "1.0.0", "account": "3.0.0", "mechanical": "2.0.0",
        "prefix": "3.0.0", "continue": "3.0.0", "responses": "3.0.0",
        "numerical": "2.0.0", "measure": "2.0.0", "check": "2.0.0", "project": "2.0.0",
        "full-numerical": "2.0.0", "response-score": "3.0.0", "collect": "2.0.0"}
    assert {key.removeprefix(development.NAMESPACE + ".") for key in declarations} == set(expected_versions)
    assert {key.removeprefix(development.NAMESPACE + ".") for key, value in declarations.items()
        if value.execution_properties.native_effect} == {"prefix", "continue", "responses"}
    for node, config in configs:
        phase = development.phase_of(config)
        declaration = declarations[development.NAMESPACE + "." + phase]
        assert declaration.capability_version == expected_versions[phase]
        if node in selected:
            assert declaration.config_record_type is development.SelectedE3E4CompactConfig
            assert config.source.provenance == provenance.identity
    # Full-factor scientific inputs keep their current full-provenance carrier;
    # its scientific reference is the same sole bounded current source.
    old = dev.SelectedE3E4NativeSource.from_bank(f.programme,f.bank,f.bank.sources[0],index=f.bank.source_index())
    assert old.reference==f.bank.sources[0] and old.reference.VERSION=="2.0.0"
    assert decode_canonical_bytes(old.canonical_bytes(), type(old), maximum_bytes=None) == old
    assert declarations[development.NAMESPACE + ".prefix"].record_codecs[old.SCHEMA] is type(old)
