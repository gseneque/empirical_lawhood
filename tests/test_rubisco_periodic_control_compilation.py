# SPDX-License-Identifier: MPL-2.0
"""Pure complete-graph controls; no numerical engine or physical admission."""
from dataclasses import replace

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import periodic_control_operation as owner
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_control_translation as graph
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave
from tests import test_rubisco_periodic_controls as controls

fixture = controls.fixture
selected = controls.selected


def configs_for(fixture):
    protocol, points, raw = selected(fixture)
    configs = tuple(owner.PeriodicControlConfig('config.'+p.point_id, fixture.config, protocol, p) for p in points)
    return configs, raw


def compile_selected(configs, draft=None):
    declaration = owner.operation_declaration()
    return compile_recursive_wave(draft=draft or graph.periodic_controls_draft(configs),
        registrations=(declaration.registration(),),
        registry=CapabilityRegistry('registry.exposed-periodic-controls', (declaration.manifest(),)),
        implementation_commit=configs[0].original.implementation.observed_git_head,
        output_codecs=declaration.record_codecs)


def test_complete_control_graph_uses_shared_lock_and_one_attempt_per_point(fixture):
    configs, _ = configs_for(fixture)
    draft = graph.periodic_controls_draft(configs)
    compiled = compile_selected(configs, draft)
    assert compiled.proof is not None and compiled.run_plan is not None
    assert len(compiled.execution_plan.tasks) == len(configs) == 6
    assert len(draft.external_inputs) == 6+2*len(configs)
    assert len(draft.links) == 8*len(configs)
    assert {op.resource_lock_ids for op in draft.operations} == {('gp-periodic-force-native-worker',)}
    assert all(task.maximum_attempts == 1 and task.capability.requested_resources == owner.BUDGET
        for task in compiled.execution_plan.tasks)
    assert not fixture.workdir.exists()


@pytest.mark.parametrize('change', ('missing-point', 'wrong-shared-source', 'wrong-point-link', 'changed-root', 'selected-subset'))
def test_complete_control_graph_refuses_changed_point_or_source_denominator(fixture, change):
    configs, _ = configs_for(fixture)
    draft = graph.periodic_controls_draft(configs)
    if change == 'missing-point':
        with pytest.raises(ValueError, match='complete original prospective'):
            graph.periodic_controls_draft(configs[:-1])
        return
    if change == 'wrong-shared-source':
        draft = replace(draft, external_inputs=tuple(replace(row, expected_content_sha256='0'*64)
            if row.input_id.endswith('native-source') else row for row in draft.external_inputs))
    elif change == 'wrong-point-link':
        draft = replace(draft, links=tuple(replace(row,
            external_input_id=graph.external_id(configs[1], 'native-point'))
            if row.consumer_node_id == owner.node_id(configs[0]) and row.consumer_input_id == 'native-point'
            else row for row in draft.links))
    elif change == 'changed-root':
        draft = replace(draft, development_study=replace(draft.development_study, question='An unselected turnover claim'))
    else:
        draft = replace(draft, selected_operation_ids=draft.selected_operation_ids[:-1])
    with pytest.raises(ValueError):
        compile_selected(configs, draft)
    assert not fixture.workdir.exists()
