# SPDX-License-Identifier: MPL-2.0
"""Complete synthetic issued-parent joins; retained bytes are software evidence."""

from dataclasses import replace
import json

import pytest

from empirical_lawhood.api import current_result_custody, recursive_qualified_parents as owner
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from tests.runtime_platform.test_recursive_prospective_parents import (
    _parent_inputs, parent_fixture as parent_fixture,
)


def _many_consumers(fixture, count):
    draft, registrations, binding = _parent_inputs(fixture)
    original_requirement, = draft.requirements
    original_connection, = draft.connections
    original_external = next(value for value in draft.external_inputs if value.input_id == binding.external_input_id)
    original_link = next(value for value in draft.links if value.external_input_id == binding.external_input_id)
    requirements, connections, externals, links, bindings = [], [], [], [], []
    for index in range(count):
        suffix = f'.consumer-{index:03}'
        requirement = replace(original_requirement, requirement_id=original_requirement.requirement_id + suffix)
        connection = replace(original_connection, connection_id=original_connection.connection_id + suffix,
            requirement_id=requirement.requirement_id, consumer_input_id=original_connection.consumer_input_id + suffix,
            external_input_id=original_connection.external_input_id + suffix)
        external = replace(original_external, input_id=connection.external_input_id,
            logical_artifact_id=original_external.logical_artifact_id + suffix)
        link = replace(original_link, edge_id=original_link.edge_id + suffix,
            external_input_id=external.input_id, consumer_input_id=connection.consumer_input_id,
            requirement_id=requirement.requirement_id, connection_id=connection.connection_id)
        requirements.append(requirement)
        connections.append(connection)
        externals.append(external)
        links.append(link)
        bindings.append(replace(binding, binding_id=binding.binding_id + suffix, external_input_id=external.input_id))
    draft = replace(draft, requirements=tuple(requirements), connections=tuple(connections),
        external_inputs=tuple(sorted((*tuple(value for value in draft.external_inputs if value != original_external),
            *externals), key=lambda value: value.input_id)),
        links=tuple(sorted((*tuple(value for value in draft.links if value != original_link), *links),
            key=lambda value: value.edge_id)))
    registrations = tuple(replace(value, input_ports=tuple(sorted((
        *tuple(port for port in value.input_ports if port.port_id != original_connection.consumer_input_id),
        *(RecursivePortContract(connection.consumer_input_id, original_external.payload_schema,
            original_external.media_type, original_external.maximum_size_bytes) for connection in connections)),
        key=lambda port: port.port_id))) if value.qualified_parent_assessor else value for value in registrations)
    return draft, registrations, tuple(bindings)


@pytest.mark.parametrize('consumers', (2, 8))
def test_shared_parent_recompiles_and_traverses_complete_closure_once(parent_fixture, tmp_path, monkeypatch, consumers):
    fixture = parent_fixture
    draft, registrations, bindings = _many_consumers(fixture, consumers)
    calls = {'plan_recompilations': 0, 'complete_closure_traversals': 0, 'live_authority_replays': 0,
        'task_index_builds': 0, 'original_index_builds': 0}

    def counted(key, original):
        def observed(*args, **kwargs):
            calls[key] += 1
            return original(*args, **kwargs)
        return observed

    monkeypatch.setattr(current_result_custody, 'authenticate_current_execution_plan',
        counted('plan_recompilations', current_result_custody.authenticate_current_execution_plan))
    monkeypatch.setattr(owner, '_collect_receipt_closure',
        counted('complete_closure_traversals', owner._collect_receipt_closure))
    monkeypatch.setattr(owner, '_replay_parent_authority',
        counted('live_authority_replays', owner._replay_parent_authority))
    monkeypatch.setattr(current_result_custody, '_index_execution_tasks',
        counted('task_index_builds', current_result_custody._index_execution_tasks))
    from empirical_lawhood.runtime import recovery
    monkeypatch.setattr(recovery, 'build_run_recovery_index',
        counted('original_index_builds', recovery.build_run_recovery_index))
    evidence = owner.authenticate_recursive_qualified_parents(spec_bindings=bindings, draft=draft,
        artifact_writer=fixture.plane, registrations=registrations,
        output_codecs=fixture.handoff.compilation.output_codecs)
    assert len(evidence) == consumers
    assert calls == {'plan_recompilations': 1, 'complete_closure_traversals': 1,
                     'live_authority_replays': consumers, 'task_index_builds': 1, 'original_index_builds': 1}
    assert all(value.product_payload == fixture.adjudication.canonical_bytes() for value in evidence)
    assert all(value.execution_plan == fixture.execution_plan for value in evidence)
    assert fixture.executor.invocations == 5
    (tmp_path / 'complete-parent-read-scaling.json').write_text(json.dumps({
        'consumers': consumers, 'original_complete_parent_task_count': len(fixture.execution_plan.tasks),
        **calls, 'retained_product_bytes_per_consumer': len(fixture.adjudication.canonical_bytes()),
        'new_native_invocations': 0, 'qualification': 'SOFTWARE_SYNTHETIC_ONLY',
    }, sort_keys=True) + '\n')
