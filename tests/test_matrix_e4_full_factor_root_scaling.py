# SPDX-License-Identifier: MPL-2.0
"""Actual typed E4 population compiler controls; no original custody or science.

The two populations are rebuilt by the selected recipe owner with four/eight
whole matched groups. Disclosed unissued locators only support pure metadata;
these controls perform no issue, native acquisition, reveal or qualification.
"""
from dataclasses import replace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import (
    full_factor_bindings as owner, full_factor_science as science,
    records as old, selected_e4_bank_recipe as recipe,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_followup_records import (
    ScheduledFullFactorScope, scope_reference,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import (
    SelectedE3E4CaseResult, SelectedE3E4NativeSource,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_method_bindings import (
    SelectedE4DevelopmentAcquisition,
)
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan
from empirical_lawhood.runtime.recursive_compiler import (
    decode_recursive_config_input, project_recursive_config_inputs, validate_recursive_scientific_roots,
)
from tests.runtime_platform.test_recursive_compiler import fixture as campaign_fixture
from tests.test_matrix_e4_full_factor_values import pin
from tests.test_matrix_selected_e4_bank_recipe import literal_recipe_source_inputs  # noqa: F401
from tests.test_matrix_selected_e3_e4_bridge import disclosed_produced_parents
from tests.test_matrix_selected_protected import unpublished


def _draft(f, groups):
    selected=replace(f.inputs.recipe,population_designs=tuple(
        (phase,replace(design,group_count=groups)) for phase,design in f.inputs.recipe.population_designs))
    inputs=replace(f.inputs,recipe=selected)
    allocation=recipe.recipe_allocation(inputs)
    reservation=old.ScheduledReservation('reservation.scaling.'+str(groups),allocation,
        unpublished(allocation,'allocation.scaling.'+str(groups)))
    selection=recipe.recipe_selection(inputs,reservation)
    specification=old.ScheduledSpecification('specification.scaling.'+str(groups),selection,
        unpublished(selection,'selection.scaling.'+str(groups)))
    criterion=inputs.original_preparation.mathematical_protocol
    _,responses=recipe.recipe_responses(inputs,reservation,specification,f.case.provenance,'DEVELOPMENT')
    bank=recipe.recipe_bank(inputs,reservation=reservation,specification=specification,provenance=f.case.provenance,
        criterion_publication=unpublished(criterion,'criterion.scaling.'+str(groups)),
        response_publication=unpublished(responses,'responses.scaling.'+str(groups)),phase='DEVELOPMENT')
    programme=recipe.recipe_programme(bank,'DEVELOPMENT')
    cases=[];sources=[]
    index=bank.source_index()
    parents=disclosed_produced_parents(f.inputs.original_products)
    for declared,descriptor in zip(programme.cases,bank.sources,strict=True):
        case=SelectedE3E4CaseResult.unentered(declared)
        source=SelectedE3E4NativeSource.from_bank(programme,bank,descriptor,index=index)
        cases.append(case)
        sources.append(science.source_from_original(record_id='source.scaling.'+declared.root_id,
            source=source,criterion=criterion,case=case,original_products=(),produced_input_parents=parents))
    locator=SelectedE4DevelopmentAcquisition('acquisition.scaling','disclosed-original','run.disclosed',
        pin('plan.disclosed',DevelopmentExecutionPlan),pin('receipt.disclosed',CanonicalTaskReceipt),False)
    scope=ScheduledFullFactorScope('scope.scaling.'+str(groups),programme,tuple(cases),tuple(sources),locator,None,())
    resources=owner.ScheduledFullFactorResources('resources.scaling',tuple((phase,
        ResourceBudget(1,64*1024**2,0,None,None,64*1024**2)) for phase in ('assess','measure','reduce')))
    development=owner.development_root(scope,study_id='study.full-factor.'+programme.programme_id)
    campaign=replace(campaign_fixture()[0].campaign,system_ids=(development.system.object_id,),world_ids=(development.world_id,),
        target_claim_ids=tuple(sorted(claim.claim_id for claim in development.claims)))
    draft=owner.lower(scope_reference(scope),resources,draft_id='draft.scaling.'+str(groups),campaign=campaign)
    assert len(programme.group_ids)==groups and len(programme.cases)==9*groups
    assert tuple(row.node_id for row in draft.operations)==tuple(sorted(row.node_id for row in draft.operations))
    assert draft.operations[-1].selection.capability_key==owner.key(False,'reduce')
    return draft


@pytest.fixture(scope='module')
def populations(literal_recipe_source_inputs):  # noqa: F811
    return tuple(_draft(literal_recipe_source_inputs,groups) for groups in (4,8))


def _decoded(draft):
    registrations={row.capability_key:row.registration() for row in owner.operation_declarations()}
    by_node={row.node_id:registrations[row.selection.capability_key] for row in draft.operations}
    decoded=tuple(decode_recursive_config_input(row,by_node[row.node_id]) for row in draft.operations)
    return project_recursive_config_inputs(decoded,by_node),by_node


def _validate(draft,rows=None):
    if rows is None:
        rows,by_node=_decoded(draft)
    else:
        registrations={row.capability_key:row.registration() for row in owner.operation_declarations()}
        by_node={row.node_id:registrations[row.selection.capability_key] for row in draft.operations}
    validate_recursive_scientific_roots(root=draft.development_study,
        config_inputs=rows,registrations_for_node=by_node,
        requirements=draft.requirements,connections=draft.connections,links=draft.links,
        qualifications=(),known_design_inputs=(),external_inputs=draft.external_inputs)


def test_two_actual_populations_have_one_complete_graph_check_and_bounded_source_lookups(populations,monkeypatch):
    metrics=[]
    for draft in populations:
        decoded,_=_decoded(draft)
        count=dict(walks=0,visited=0,links=0,roots=0,lookups=0,probes=0)
        class CountedRows(tuple):
            def __iter__(self):
                count['walks']+=1
                for row in super().__iter__():
                    count['visited']+=1
                    yield row
        actual_links,actual_root,actual_bisect=owner.expected_links,owner.development_root,owner.bisect_left
        def links(scope):
            count['links']+=1
            return actual_links(scope)
        def root(scope,**kwargs):
            count['roots']+=1
            return actual_root(scope,**kwargs)
        def lookup(sequence,value,*,key):
            count['lookups']+=1
            def probe(row):
                count['probes']+=1
                return key(row)
            return actual_bisect(sequence,value,key=probe)
        with monkeypatch.context() as patch:
            patch.setattr(owner,'expected_links',links)
            patch.setattr(owner,'development_root',root)
            patch.setattr(owner,'bisect_left',lookup)
            _validate(draft,CountedRows(decoded))
        roots=(len(decoded)-1)//2
        # The common owner normalizes this complete input census once; the
        # domain still validates its full graph once and each bounded source.
        assert count['walks']==1 and count['visited']==len(decoded)
        assert count['links']==count['roots']==1
        assert count['lookups']==2*roots
        assert count['probes']<=2*roots*roots.bit_length()
        metrics.append((roots,count))
    assert metrics[1][0]==2*metrics[0][0]
    assert metrics[1][1]['visited']<2*metrics[0][1]['visited']


@pytest.mark.parametrize('population',(0,1))
@pytest.mark.parametrize('mutation',('links','source','roster','reducer','root'))
def test_complete_compiler_batch_refuses_changed_graph_source_or_roster(populations,population,mutation):
    draft=populations[population]
    if mutation=='links':
        draft=replace(draft,links=draft.links[1:])
    elif mutation=='source':
        rows,_=_decoded(draft)
        config=rows[0].record
        changed=replace(config,source=replace(config.source,group_id='group.foreign'))
        operation=replace(draft.operations[0],config_payload=changed.canonical_bytes().decode('utf-8'))
        draft=replace(draft,operations=(operation,*draft.operations[1:]))
    elif mutation in ('roster','reducer'):
        removed=draft.operations[0] if mutation=='roster' else draft.operations[-1]
        draft=replace(draft,operations=tuple(row for row in draft.operations if row.node_id!=removed.node_id),
            selected_operation_ids=tuple(row for row in draft.selected_operation_ids if row!=removed.node_id))
    else:
        draft=replace(draft,development_study=replace(draft.development_study,question='Changed original whole-group scope'))
    with pytest.raises(ValueError,match='full factor'):
        _validate(draft)
