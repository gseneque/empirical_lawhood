# SPDX-License-Identifier: MPL-2.0
"""E1 actual compiler facade and E2 all-unentered descriptive lifecycle controls."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_confirmation import experiment_preparation as e1_owner
from empirical_lawhood.adapters.methods.matrix_factor_confirmation import operation_bindings as e1_bindings
from empirical_lawhood.adapters.methods.matrix_history_analysis import experiment_preparation as e2_owner
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import MatrixHistoryAllocation,MatrixHistoryAnalysisConfig
from empirical_lawhood.api.experiment_preparation import load_experiment_specification,load_experiment_inputs,prepare_experiment
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.recursive_authoring import implementation_binding
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.test_matrix_factor_confirmation_adjudication import prospective
from tests.test_matrix_factor_confirmation_eligibility import provenance as provenance,stock as stock
from tests.test_matrix_factor_confirmation_history import e1 as e1
from tests.test_recursive_public_service import _plane

ROOT=Path(__file__).parents[1]


def _e1_selection(e1):
    draft,qualifications=prospective(e1)
    operation=next(value for value in draft.operations if value.node_id==e1_bindings.KEY)
    config=decode_canonical_bytes(operation.config_payload.encode(),e1_bindings.E1AdjudicationConfig,maximum_bytes=None)
    owners=tuple(sorted((obligation,value.node_id) for value in draft.operations for obligation in value.obligation_ids))
    selection=e1_owner.E1ConfirmationSelection('selection.disclosed-e1-facade',draft.prospective_draft,config.sources,e1[2],
        owners,tuple((value.node_id,value.resource_budget) for value in draft.operations),qualifications,
        draft.prospective_draft.design_inputs,(),None,None,(),None)
    specification=e1_owner.E1ConfirmationSpecification('experiment.disclosed-e1-facade',selection.root.question,
        tuple(value.root_id for value in selection.sources),selection.identity)
    return specification,selection


def test_e1_copied_selection_derives_real_complete_prospective_graph_without_native(e1):
    specification,selection=_e1_selection(e1)
    assert decode_canonical_bytes(selection.canonical_bytes(),type(selection),maximum_bytes=None)==selection
    prepared=prepare_experiment(specification,method_inputs=selection,execution=ExecutionSelection(4))
    assert not prepared.executable
    assert {value.code for value in prepared.dependencies}>={'e1.entry','e1.resources','e1.source-configs',
        'e1.execution.source-snapshot','e1.execution.output-root'}
    assert prepared.census.native_effect_count==4
    assert len(prepared.draft.operations)==18
    factories=e1_bindings.operation_factories()
    registry=CapabilityRegistry('registry.disclosed-e1-facade',tuple(sorted((value.manifest for value in factories),key=lambda value:value.registry_id)))
    compiled=compile_recursive_wave(draft=prepared.draft,registrations=tuple(value.registration for value in factories),
        registry=registry,implementation_commit='a'*40,qualifications=selection.qualifications,
        known_design_inputs=selection.known_design_inputs,
        output_codecs={key:value for factory in factories for key,value in factory.output_codecs.items()})
    assert compiled.candidate_report.candidate is not None,compiled.candidate_report.diagnostics
    assert prepared.allocation.unit_ids()==tuple(sorted(source.root.root.independent_group_id for source in selection.sources))
    with pytest.raises(ValueError,match='budgets omit'):
        changed=replace(selection,task_budgets=selection.task_budgets[:-1])
        e1_owner.prepare(replace(specification,selection=changed.identity),method_inputs=changed,execution=ExecutionSelection(4))


def test_e2_actual_public_analyze_read_and_recovery_retain_all_256_unentered(tmp_path,monkeypatch):
    from empirical_lawhood.api import matrix_history_analysis as history
    plane=_plane(tmp_path/'selected')
    allocation=decode_canonical_bytes((ROOT/'programmes/foundations/emergent-structure/workflows/matrix-history-analysis/allocation.json').read_bytes(),MatrixHistoryAllocation,maximum_bytes=None)
    source=history.prepare_matrix_history_source_configuration(config_id='source.disclosed-e2-facade',allocation=allocation,repo_root=ROOT)
    config=MatrixHistoryAnalysisConfig('analysis.disclosed-e2-facade','ALGEBRA',source)
    spec=e2_owner.MatrixHistoryProgrammeSpecification('experiment.disclosed-e2-facade',allocation.identity,config.identity,(),
        'history-control/descriptive-result')
    service=ExperimentProgrammeService(ROOT,plane,storage_profile=SimpleNamespace(maximum_parallel_tasks=4))
    execution=ExecutionSelection(4,'environment.disclosed-e2-facade',ObjectIdentity.from_record('recursive-member.implementation',
        implementation_binding(ROOT)),plane.root.contract.canonical_path)
    prepared=service.prepare(spec,method_inputs=e2_owner.MatrixHistoryProgrammeInputs(allocation,config),execution=execution)
    assert prepared.executable and prepared.census.native_effect_count==0
    copied_spec=load_experiment_specification(ROOT/'programmes/foundations/emergent-structure/workflows/matrix-history-analysis/programme.json')
    copied=load_experiment_inputs(copied_spec,ROOT/'programmes/foundations/emergent-structure/workflows/matrix-history-analysis/programme-sources.json')
    assert copied.method_inputs.allocation.identity==copied_spec.allocation
    assert copied.method_inputs.analysis.identity==copied_spec.analysis
    assert prepared.allocation.role_counts==(('descriptive',256),)
    assert all(unit.numerical_view_ids==('fine','primary') for unit in prepared.allocation.units)
    assert all(unit.source_id==allocation.allocation_id for unit in prepared.allocation.units)
    destination=Path(plane.root.contract.canonical_path)/'history-control/programme'
    service.author(preparation=prepared,output_dir=destination)
    assert service.read(directory=destination,allow_partial=True)['state']=='AWAITING_DESCRIPTIVE_RESULT'
    actual=service.run(directory=destination,maximum_parallel_tasks=4)
    assert actual['result']['requested_histories']==256 and actual['result']['unentered_histories']==256
    assert actual['result']['scientific_qualification_granted'] is False
    monkeypatch.setattr(history,'analyze_matrix_histories',lambda **_kwargs:pytest.fail('completed recovery recalculated E2'))
    monkeypatch.setattr(history,'produce_matrix_histories',lambda **_kwargs:pytest.fail('descriptive facade acquired native history'))
    assert service.recover(directory=destination,maximum_parallel_tasks=4)==actual
    assert service.read(directory=destination)==actual
    assert service.author(preparation=prepared,output_dir=destination)['state']=='DESCRIPTIVE_PLAN_RETAINED'
    stopped=service.prepare(replace(spec,mode='ACQUIRE_AND_ANALYZE'),
        method_inputs=e2_owner.MatrixHistoryProgrammeInputs(allocation,config),execution=execution)
    assert not stopped.executable and {value.code for value in stopped.dependencies}=={'e2.parallel-native-entry'}


def test_registered_facade_examples_load_without_native_or_qualification():
    for relative in ('programmes/foundations/emergent-structure/workflows/matrix-factor-confirmation/specification.json','programmes/foundations/emergent-structure/workflows/matrix-history-analysis/programme.json'):
        specification=load_experiment_specification(ROOT/relative)
        prepared=prepare_experiment(specification)
        assert not prepared.executable
