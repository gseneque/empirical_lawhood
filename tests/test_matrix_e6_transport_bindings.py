# SPDX-License-Identifier: MPL-2.0
"""Actual E6 worker/declaration consumers over disclosed no-acquisition inputs."""
from dataclasses import fields, replace

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_future as future
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_protected_bindings as owner
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_protected_workers as workers
from empirical_lawhood.adapters.methods.matrix_experimental_programme import e6_transport_science
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_e6_transport_config import (
    MatrixSelectedTransportFutureConfig, MatrixSelectedTransportScoreConfig,
)
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_original_commitments import MatrixSelectedEntryEvidenceV3
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from tests.test_matrix_e6_transport_assessment import fixture_case, exposed_parent_census
from tests.test_matrix_selected_opportunity_workers import _response_invocation, invocation
from tests.test_matrix_selected_package import reference


@pytest.fixture(scope="module")
def transport():
    return fixture_case()


def response_invocation(case, *, damage=None):
    old_runner, old_context = _response_invocation(case.programme, protected=True)
    try:
        original, received, arrays = workers._decode(old_context, old_runner)
        config = MatrixSelectedTransportFutureConfig(**{field.name: getattr(original, field.name)
            for field in fields(type(original))}, transport_policy=case.policy, transport_calibration=case.projection)
        values = {**received, **{name: value.read() for name, value in arrays.items()},
            "decision": future.transport_decision_for(config, received["point"])}
        producers = {edge.consumer_input_id: edge.producer_task_id
            for edge in old_context.prepared_invocation.execution_task_record.scientific_inputs if edge.producer_task_id}
        producers["decision"] = future.node_id(config.source, "point")
        if damage == "missing-decision":
            del values["decision"]
        elif damage == "decision-prefix":
            values["decision"] = replace(values["decision"], prefix=replace(values["decision"].prefix, object_fingerprint="f" * 64))
        elif damage == "decision-producer":
            producers["decision"] += ".foreign"
        return invocation(config, values, producers, selected_owner=owner)
    finally:
        for port in old_context.input_ports:
            port.close()


def test_transport_declarations_factories_and_complete_decision_graph(transport):
    for declaration in owner.operation_declarations():
        assert declaration.runner_factory().manifest == declaration.manifest()
    configs, _, edges, _, _ = owner.contracts(transport.programme,
        reference("evidence.e6.disclosed", MatrixSelectedEntryEvidenceV3), 1,
        transport_policy=transport.policy, transport_calibration=transport.projection,
        produced_input_parents=exposed_parent_census(transport.programme))
    configs = dict(configs)
    sources = transport.programme.sources.source_arms()
    for _, source in sources:
        response = configs[future.node_id(source, "responses")]
        score = configs[future.node_id(source, "response-score")]
        assert future.response_config_for(score) == response
        assert owner.config_capability_version(response) == "3.0.0"
        assert owner.config_capability_version(score) == "2.0.0"
        for phase in ("responses", "response-score"):
            edge, = (edge for edge in edges if edge.consumer_node_id == future.node_id(source, phase)
                and edge.consumer_input_id == "decision")
            assert (edge.producer_node_id, edge.producer_output_id) == (future.node_id(source, "point"), "decision")
    decisions = tuple(edge for edge in edges if edge.consumer_input_id.startswith("decisions."))
    assert len(decisions) == len(sources)


def test_transport_custody_records_roundtrip_all_root_and_censoring_fields(transport):
    manifest, assessment = e6_transport_science.assess_e6_transport(transport.programme, transport.policy,
        transport.projection, transport.observations, transport.decisions, result_id="assessment.e6.roundtrip")
    for record in (transport.policy, transport.projection, *transport.decisions.values(), manifest, assessment):
        raw = record.canonical_bytes()
        assert decode_canonical_bytes(raw, type(record), maximum_bytes=len(raw)) == record
    assert all(len(row.lifetimes) == 10 and len(row.primary_comparator_improvements) == 2 for row in assessment.cases)


def test_actual_transport_response_worker_binds_decision_before_ready_without_acquisition(transport, monkeypatch):
    monkeypatch.setattr(future, "execute_native_future", lambda *args, **kwargs: pytest.fail("software control acquired a future"))
    runner, context = response_invocation(transport)
    try:
        work = runner.prepare_native_work(context, expected_parent=context.prepared_invocation.expected_parent_contact)
        config, received, _ = workers._decode(context, runner)
        definition, = work.definitions
        assert definition.operation_id == future.TRANSPORT_OPERATION
        assert received["decision"].identity in definition.sources
        assert len(definition.streams) == 4
        assert received["decision"].admission == "ABSTAIN"
        # Abstention does not prune the actual native work roster.
        assert work.definitions and len(work.rosters) == 1
        runner.preflight(context)
        score = MatrixSelectedTransportScoreConfig(**{field.name: ("response-score" if field.name == "phase"
            else "config." + future.node_id(config.source, "response-score") if field.name == "config_id"
            else getattr(config, field.name)) for field in fields(type(config))})
        assert future.response_config_for(score, operation_id=future.TRANSPORT_OPERATION) == config
        with pytest.raises(ValueError, match="acquisition edition"):
            future.response_config_for(score, operation_id=future.NAMESPACE + ".paired-pulse.direct-inputs.v2")
    finally:
        runner._native_array_preparation.clear()
        for port in context.input_ports:
            port.close()


@pytest.mark.parametrize("damage", ("missing-decision", "decision-prefix", "decision-producer"))
def test_actual_transport_response_worker_refuses_changed_or_missing_causal_decision_before_contact(transport, damage):
    runner, context = response_invocation(transport, damage=damage)
    try:
        with pytest.raises(ValueError, match="required original numerical operand|pre-future empirical decision|ordinary producer"):
            runner.prepare_native_work(context, expected_parent=context.prepared_invocation.expected_parent_contact)
    finally:
        for port in context.input_ports:
            port.close()
