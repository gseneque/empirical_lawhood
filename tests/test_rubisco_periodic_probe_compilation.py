"""Pure compiler controls for the complete periodic force probe."""
from dataclasses import replace

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import periodic_probe_operation as owner
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_probe_translation as graph
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave
from tests import test_rubisco_periodic_probe_operation as probe_controls

fixture=probe_controls.fixture


def compile_selected(config,draft=None):
    declaration=owner.operation_declaration()
    return compile_recursive_wave(draft=draft or graph.periodic_probe_draft(config),
        registrations=(declaration.registration(),),
        registry=CapabilityRegistry('registry.exposed-periodic-probe',(declaration.manifest(),)),
        implementation_commit=config.implementation.observed_git_head,
        output_codecs=declaration.record_codecs)


def test_compiler_closes_one_complete_native_force_question_without_contact(fixture):
    result=compile_selected(fixture.config)
    assert result.proof is not None and result.run_plan is not None
    assert len(result.execution_plan.tasks)==1
    task=result.execution_plan.tasks[0]
    assert task.maximum_attempts==1 and task.capability.capability_key==owner.CAPABILITY
    assert task.capability.requested_resources==owner.BUDGET
    assert len(task.outputs)==1 and task.outputs[0].payload_schema==owner.PeriodicProbeResult.SCHEMA
    assert not fixture.workdir.exists()


@pytest.mark.parametrize('change',('missing-model','source-fingerprint','unit-census','question','budget','duplicate-operation'))
def test_compiler_refuses_changes_to_complete_scientific_selection(fixture,change):
    draft=graph.periodic_probe_draft(fixture.config)
    if change=='missing-model':
        draft=replace(draft,external_inputs=tuple(row for row in draft.external_inputs
            if row.input_id!='external.periodic-force.native-model'),links=tuple(row for row in draft.links
            if row.external_input_id!='external.periodic-force.native-model'))
    elif change=='source-fingerprint':
        draft=replace(draft,external_inputs=tuple(replace(row,expected_content_sha256='0'*64)
            if row.input_id=='external.periodic-force.native-source' else row for row in draft.external_inputs))
    elif change=='unit-census':
        draft=replace(draft,development_study=replace(draft.development_study,assigned_unit_ids=('unit.substitute',)))
    elif change=='question':
        draft=replace(draft,development_study=replace(draft.development_study,question='Does I95M improve turnover?'))
    elif change=='budget':
        draft=replace(draft,operations=(replace(draft.operations[0],resource_budget=replace(owner.BUDGET,cpu_cores=owner.BUDGET.cpu_cores+1)),))
    else:
        with pytest.raises(ValueError):replace(draft,operations=draft.operations*2)
        return
    with pytest.raises(ValueError):compile_selected(fixture.config,draft)
    assert not fixture.workdir.exists()
