# SPDX-License-Identifier: MPL-2.0
"""Original publication custody stays distinct from current prepared copies.

These guarded literal records and stored receipts are software conformance
fixtures. They authenticate no genuine source, chronology or authority.
"""

from dataclasses import replace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.protected_experiment_inputs import (
    E3RequiredPublication, e3_prepared_publication_transports, require_e3_reserved_fit_inputs,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.execution import VerifiedArtifactInput
from tests.test_matrix_e3_statistical_bindings import (
    case as statistical_case, config, prepared, sources,
)


@pytest.fixture(scope="module")
def case(tmp_path_factory):
    value = statistical_case.__wrapped__(tmp_path_factory)
    operands = sources(value)
    mapping = {"allocation": "original-allocation", "native-selection": "native-selection",
        "reservation": "reservation", "roles": "allocation"}
    records = {"allocation": value.manifest.reservation.allocation,
        "native-selection": value.manifest.native_specification.selection,
        "reservation": value.manifest.reservation, "roles": value.allocation}
    publications = tuple(E3RequiredPublication(key, records[key], publication, availability)
        for key, publication, availability in value.publications)
    for row in publications:
        original = row.publication
        copied = value.plane.write(ArtifactWriteRequest(original.logical.logical_artifact_id,
            "current-copies/" + row.key + ".json", row.record.SCHEMA, ArtifactProfile.CANONICAL_JSON,
            "application/json", "literal-current-byte-copy", "current-copies", row.record.canonical_bytes(),
            original.logical.visibility_ceiling, (), original.logical.outcome_access))
        assert copied.logical == original.logical
        assert copied.materialization.materialization_id != original.materialization.materialization_id
        operands[mapping[row.key]].publication = copied
    selected = prepared(value, config(value, "fit"), operands)
    value.transport_publications = publications
    value.transport_context = selected.context
    return value


def current_ports(case, context=None):
    by_id = {port.artifact_id: port for port in (context or case.transport_context).input_ports}
    return {row.key: by_id[row.publication.logical.logical_artifact_id] for row in case.transport_publications}


def require(case, *, ports=None, witnesses=()):
    return require_e3_reserved_fit_inputs(case.inputs, publications=case.transport_publications,
        ports=current_ports(case) if ports is None else ports, fit_cutoff=case.fit_cutoff,
        record_id="join.literal.original-transport", publication_transports=witnesses)


def test_current_copy_requires_actual_prepared_witness_and_preserves_original_join(case):
    with pytest.raises(ValueError, match="exact original protected allocation publication"):
        require(case)
    witnesses = e3_prepared_publication_transports(case.transport_publications, case.transport_context)
    assert tuple(row.key for row in witnesses) == ("allocation", "native-selection", "reservation", "roles")
    actual = require(case, witnesses=witnesses)
    original_ports = {row.key: case.plane.open(VerifiedArtifactInput(row.publication.logical, row.publication.materialization),
        maximum_bytes=row.publication.materialization.size_bytes) for row in case.transport_publications}
    try:
        expected = require(case, ports=original_ports)
    finally:
        for port in original_ports.values():
            port.close()
    assert actual.canonical_bytes() == expected.canonical_bytes()
    assert tuple(row[2] for row in actual.publications) == tuple(
        row.publication.materialization.materialization_id for row in case.transport_publications)
    assert all(actual.publications[index][2] != witness.prepared_input.binding.materialization_id
        for index, witness in enumerate(witnesses))
    assert all(port.tell() == 0 for port in current_ports(case).values())


def test_prospective_optional_external_size_keeps_exact_original_bytes_and_complete_witness(case):
    context = case.transport_context
    prepared = context.prepared_invocation
    task = replace(prepared.execution_task_record, external_inputs=tuple(replace(row, expected_size_bytes=None)
        for row in prepared.execution_task_record.external_inputs))
    prepared = replace(prepared, execution_task_record=task, execution_task=ObjectIdentity.from_record(task.task_id, task))
    context = replace(context, prepared_invocation=prepared)
    witnesses = e3_prepared_publication_transports(case.transport_publications, context)
    expected = e3_prepared_publication_transports(case.transport_publications, case.transport_context)
    assert witnesses == expected
    assert require(case, witnesses=witnesses).canonical_bytes() == require(case, witnesses=expected).canonical_bytes()
    assert all(witness.prepared_input.binding.size_bytes == witness.original_publication.materialization.size_bytes
        == witness.scientific_edge.maximum_size_bytes for witness in witnesses)


@pytest.mark.parametrize("damage", ("explicit-size", "edge-bound", "current-binding-size"))
def test_optional_external_size_cannot_hide_a_changed_original_size(case, damage):
    context = case.transport_context
    prepared = context.prepared_invocation
    task = prepared.execution_task_record
    artifact = case.transport_publications[0].artifact.artifact_id
    changed = case.transport_publications[0].publication.materialization.size_bytes + 1
    task = replace(task, external_inputs=tuple(replace(row, expected_size_bytes=changed if damage == "explicit-size" else None)
        if row.logical_artifact_id == artifact else row for row in task.external_inputs))
    if damage == "edge-bound":
        task = replace(task, scientific_inputs=tuple(replace(row, maximum_size_bytes=changed)
            if row.operational_logical_artifact_id == artifact else row for row in task.scientific_inputs))
    with pytest.raises((ValueError, TypeError)):
        if damage == "current-binding-size":
            changed_contracts = tuple(replace(row, binding=replace(row.binding, size_bytes=changed))
                if row.artifact_id == artifact else row for row in prepared.inputs)
            prepared = replace(prepared, inputs=changed_contracts)
        prepared = replace(prepared, execution_task_record=task, execution_task=ObjectIdentity.from_record(task.task_id, task))
        context = replace(context, prepared_invocation=prepared)
        e3_prepared_publication_transports(case.transport_publications, context)


@pytest.mark.parametrize("damage", ("missing", "order", "current-port", "physical", "logical", "edge"))
def test_copy_transport_refuses_substitution_before_lazy_training(case, damage):
    witnesses = e3_prepared_publication_transports(case.transport_publications, case.transport_context)
    ports, events = current_ports(case), []
    with pytest.raises((ValueError, TypeError)):
        if damage == "missing":
            witnesses = witnesses[:-1]
        elif damage == "order":
            witnesses = tuple(reversed(witnesses))
        elif damage == "current-port":
            ports = {**ports, "reservation": ports["roles"]}
        elif damage == "physical":
            witnesses = (replace(witnesses[0], prepared_input=replace(witnesses[0].prepared_input,
                physical_sha256="c" * 64)), *witnesses[1:])
        elif damage == "logical":
            changed = replace(witnesses[0].original_publication,
                logical=replace(witnesses[0].original_publication.logical, content_sha256="d" * 64))
            witnesses = (replace(witnesses[0], original_publication=changed), *witnesses[1:])
        else:
            witnesses = (replace(witnesses[0], scientific_edge=replace(witnesses[0].scientific_edge,
                consumer_input_id="unrelated-original")), *witnesses[1:])
        require(case, ports=ports, witnesses=witnesses)
        events.append("TRAIN read")
    assert events == []


@pytest.mark.parametrize("damage", ("unprepared", "other-port", "changed-edge", "changed-external"))
def test_transport_factory_requires_the_actual_prepared_context_and_exact_current_edge(case, damage):
    context = case.transport_context
    with pytest.raises((ValueError, TypeError)):
        if damage == "unprepared":
            context = replace(context, prepared_invocation=None)
        elif damage == "other-port":
            ports = list(context.input_ports)
            target = next(index for index, port in enumerate(ports)
                if port.artifact_id == case.transport_publications[0].artifact.artifact_id)
            ports[target] = replace(ports[target], binding=replace(ports[target].binding,
                materialization_id="materialization.literal.foreign-copy"))
            context = replace(context, input_ports=tuple(ports))
        else:
            prepared = context.prepared_invocation
            task = prepared.execution_task_record
            artifact = case.transport_publications[0].artifact.artifact_id
            if damage == "changed-edge":
                task = replace(task, scientific_inputs=tuple(replace(edge, consumer_input_id="wrong-original-port")
                    if edge.operational_logical_artifact_id == artifact else edge for edge in task.scientific_inputs))
            else:
                task = replace(task, external_inputs=tuple(replace(row, expected_content_sha256="e" * 64)
                    if row.logical_artifact_id == artifact else row for row in task.external_inputs))
            prepared = replace(prepared, execution_task_record=task,
                execution_task=ObjectIdentity.from_record(task.task_id, task))
            context = replace(context, prepared_invocation=prepared)
        e3_prepared_publication_transports(case.transport_publications, context)
