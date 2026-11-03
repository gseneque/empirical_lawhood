# SPDX-License-Identifier: MPL-2.0
"""Disclosed original seams; actual public revealed PURE workflow, never authority."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import E4_LINEAGE_SCOPE as LINEAGE_SCOPE
from tests.matrix_e4_structure_support import publish_secondary
from empirical_lawhood.adapters.methods.matrix_scheduled_history import full_factor_bindings as owner,full_factor_preparation as domain,records as old,selected_e4_bank_recipe as recipe,selected_e4_native_bindings as native_owner,selected_e4_native_records as native,selected_e4_methods as revision,selected_e4_programme as phase_science
from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_followup_records import ScheduledFullFactorScope,scope_reference
from empirical_lawhood.api import matrix_full_factor_derivation as derive,matrix_full_factor_authoring as author,matrix_full_factor_runtime as runtime,matrix_full_factor_read as reader
from empirical_lawhood.api.experiment_preparation import load_experiment_inputs
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.recursive_authoring import implementation_binding,load_authored_wave,_authenticate_experiment_instance
from empirical_lawhood.api.recursive_execution import _external_inputs,_retained_plans
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling,OutcomeAccess,VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.experiment_inputs import ExperimentInputBinding,ExperimentInputSelection
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan
from tests import matrix_selected_e4_public_fixture as held
from tests.runtime_platform.test_recursive_compiler import fixture as campaign_fixture
from tests.test_matrix_e4_full_factor_protected_reference import _waves
from tests.test_matrix_e4_full_factor_public import ROOT,_real_plane
from tests.test_matrix_e4_full_factor_values import scopes,pin  # noqa: F401
from tests.test_matrix_selected_e4_bank_recipe import literal_recipe_source_inputs  # noqa: F401
from tests.test_matrix_selected_protected import unpublished


def _selected(scope_values,f,monkeypatch):
    from tests.test_matrix_selected_e3_e4_bridge import disclosed_produced_parents
    allocation=recipe.recipe_allocation(f.inputs)
    reservation=old.ScheduledReservation('reservation.full-factor.disclosed',allocation,unpublished(allocation,'allocation.full-factor.disclosed'))
    selection=recipe.recipe_selection(f.inputs,reservation)
    specification=old.ScheduledSpecification('specification.full-factor.disclosed',selection,unpublished(selection,'selection.full-factor.disclosed'))
    criterion=f.inputs.original_preparation.mathematical_protocol
    _,responses=recipe.recipe_responses(f.inputs,reservation,specification,f.case.provenance,'CONFIRMATION')
    bank=recipe.recipe_bank(f.inputs,reservation=reservation,specification=specification,provenance=f.case.provenance,
        criterion_publication=unpublished(criterion,'criterion.full-factor.disclosed'),
        response_publication=unpublished(responses,'responses.full-factor.disclosed.confirmation'),phase='CONFIRMATION')
    programme,cases,sources=scope_values['CONFIRMATION']
    assert programme.bank==bank.identity
    budget=ResourceBudget(1,1024**3,0,None,128*1024**2,64*1024**2)
    budgets=native.SelectedE4NativeBudgets('budgets.full-factor.disclosed',
        tuple((phase,budget) for phase in sorted(native_owner.PHASES)),budget)
    decision=phase_science.SelectedE4PublicRevisionDecision('decision.full-factor.disclosed',scope_values['DEVELOPMENT'][0].identity,
        pin('nomination.full-factor.disclosed',revision.SelectedE4RevisionNomination),
        pin('frozen.full-factor.disclosed',revision.SelectedE4FrozenRevision),'UNEVALUABLE','UNENTERED',None,None)
    export=phase_science.SelectedE4RevisionExport('revision.full-factor.disclosed',decision,None)
    summary=phase_science.SelectedE4OriginalCalibrationSummary.from_package(f.package,record_id='summary.full-factor.disclosed')
    evidence=SimpleNamespace(identity=pin('evidence.full-factor.disclosed',native.SelectedE4ProtectedEvidence))
    originals=SimpleNamespace()
    monkeypatch.setattr(held,'original_preparation',lambda value:f.inputs.original_preparation if value is originals else pytest.fail('foreign original'))
    root=held._phase_root(originals,programme,bank,evidence,export,summary,None,budget)
    declaration=native.SelectedE4NativeProgrammeDeclaration('declaration.full-factor.disclosed',programme,bank.identity,
        unpublished(bank,'bank.full-factor.disclosed'),root,evidence.identity,decision,None,None,budgets,4,summary,
        disclosed_produced_parents(f.inputs.original_products))
    scope=ScheduledFullFactorScope('scope.experiment.full-factor.revealed.disclosed',programme,cases,sources,None,declaration,_waves(programme))
    resources=domain.ScheduledFullFactorResources('resources.full-factor.revealed.disclosed',tuple((phase,budget) for phase in ('assess','measure','reduce')))
    study=owner.development_root(scope,study_id='study.full-factor.'+programme.programme_id)
    campaign=replace(campaign_fixture()[0].campaign,system_ids=(study.system.object_id,),world_ids=(study.world_id,),
        target_claim_ids=tuple(sorted(claim.claim_id for claim in study.claims)))
    return SimpleNamespace(programme=programme,bank=bank,scope=scope,resources=resources,campaign=campaign,study=study)


def _public_inputs(directory,plane,selected):
    target,secondary=publish_secondary(plane,selected.bank,directory/'early-secondary')
    selected.secondary_target,selected.secondary_readout=target,secondary
    request=domain.ScheduledFullFactorProtectedRequestV4('request.full-factor.revealed.disclosed',selected.programme.identity,
        selected.bank.identity,selected.resources.identity,selected.scope.declaration.identity,selected.scope.waves,
        ObjectIdentity.from_record(selected.campaign.campaign_id,selected.campaign),secondary)
    specification=domain.ScheduledFullFactorProtectedSpecification('experiment.full-factor.revealed.disclosed',request.identity,None,None,None)
    before=request.canonical_bytes()
    assert decode_canonical_bytes(before,domain.ScheduledFullFactorProtectedRequestV4,maximum_bytes=len(before)).canonical_bytes()==before
    assert b'original_utf8' not in before and b'"preparation"' not in before
    assert b'"normalized_adequacy_tolerance"' not in before
    records={'request':request,'programme':selected.programme,'bank':selected.bank,'resources':selected.resources,'campaign':selected.campaign}
    bindings=[]
    for role,record in sorted(records.items()):
        name=role+'.json';raw=record.canonical_bytes();(directory/name).write_bytes(raw)
        field={'programme':'programme_id','bank':'bank_id','campaign':'campaign_id'}.get(role,'record_id')
        bindings.append(ExperimentInputBinding(role,ObjectIdentity.from_record(getattr(record,field),record),name,len(raw)))
    path=directory/'sources.json'
    path.write_bytes(ExperimentInputSelection('inputs.full-factor.revealed.disclosed',domain.PROTECTED_PROTOCOL_ID,tuple(bindings)).canonical_bytes())
    spec=directory/'initial.json';spec.write_bytes(specification.canonical_bytes())
    return spec,path,request


def _original_seams(monkeypatch,selected):
    from empirical_lawhood.api import matrix_full_factor_access as access_owner,selected_e4_access
    events=[]
    def protected_access(*,artifact_writer,request,read_access=None):
        if (request.programme!=selected.programme.identity or request.bank!=selected.bank.identity
                or request.declaration!=selected.scope.declaration.identity or request.waves!=selected.scope.waves):
            raise PermissionError('disclosed original wave packet substitutes its exact immutable request')
        value=access_owner.ProtectedFullFactorInputAccess(artifact_writer,request.waves,
            selected.scope.declaration,read_access)
        value.require_current()
        return value
    def current(**kwargs):
        assert kwargs['originals']==selected.scope.waves
        if kwargs['current_access'] is not None:kwargs['current_access'].require_originals(selected.scope.waves)
        # No real stored-grant read is claimed by this disclosed seam.
    monkeypatch.setattr(access_owner,'protected_original_access',protected_access)
    monkeypatch.setattr(selected_e4_access,'require_current_e4_access',current)
    def original(**kwargs):
        events.append(('original',kwargs))
        if kwargs.get('_consume_original_access') is not None:
            access=access_owner.ProtectedFullFactorInputAccess(kwargs['writer'],selected.scope.waves,
                selected.scope.declaration,kwargs.get('current_access'))
            kwargs['_consume_original_access'](access,None)
        if kwargs.get('_consume_functional') is not None:
            from tests.matrix_e4_structure_support import unentered_dense_functional_rows as dense_e4_functional_rows
            for case in selected.scope.original_cases:
                kwargs['_consume_functional'](dense_e4_functional_rows(selected.bank,case,None,dense_score=None,
                    target=selected.secondary_target,secondary=selected.secondary_readout))
        if kwargs.get('_consume_programme_result') is not None:
            kwargs['_consume_programme_result'](observations=(),report={
                'state':'DISCLOSED_UNENTERED_ORIGINAL_FIXTURE','new_native_contact_count':0})
        return selected.scope,()
    monkeypatch.setattr(derive,'derive_original_full_factor_scope',original)
    monkeypatch.setattr(author,'authenticate_original_full_factor_scope',lambda **kwargs:events.append(('author-original',kwargs)) or ())
    monkeypatch.setattr(author,'validate_authoring_read_access',lambda **kwargs:events.append(('author-access',kwargs)))
    monkeypatch.setattr(runtime,'authenticate_original_full_factor_reference',original)
    monkeypatch.setattr(reader,'authenticate_original_full_factor_reference',original)
    # Explicit unissued grant seam; these events are never real authority evidence.
    monkeypatch.setattr(runtime,'_original_grants',lambda writer,scope,source=None,**kwargs:events.append(('original-grant',source)))
    return events


def _derive_public(tmp_path,scope_values,f,monkeypatch):
    selected=_selected(scope_values,f,monkeypatch)
    root=tmp_path/'revealed-public'
    assert root.is_relative_to(Path('/media/chevre/EL/empirical-lawhood'))
    plane=_real_plane(root)
    spec,sources,request=_public_inputs(root,plane,selected)
    events=_original_seams(monkeypatch,selected)
    source=implementation_binding(ROOT)
    execution=ExecutionSelection(4,'main-locked',ObjectIdentity.from_record('recursive-member.implementation',source),str(root))
    service=ExperimentProgrammeService(ROOT,plane)
    result=service.derive_inputs(specification_path=spec,source_selection_path=sources,metadata_directory=root/'derived',
        output_selection_path=root/'derived'/'sources.json',execution=execution)
    assert result.preparation.executable and result.preparation.prospective_spec is None
    assert result.preparation.draft.prospective_draft is None
    assert result.preparation.draft.development_study==selected.study
    assert all((claim.evidence_ceiling,claim.outcome_access,claim.visibility_ceiling)==(
        EvidenceCeiling.NON_PROMOTABLE,OutcomeAccess.EVALUATION_REVEALED,VisibilityCeiling.OUTCOME_VISIBLE) for claim in selected.study.claims)
    assert result.target_specification.preparation is None
    loaded=load_experiment_inputs(result.target_specification,result.source_selection_path,artifact_writer=plane)
    assert not hasattr(loaded.method_inputs,'preparation') and not hasattr(loaded.method_inputs,'template')
    assert loaded.method_inputs.scope==selected.scope
    directory=root/'authored'
    assert service.author(preparation=result.preparation,output_dir=directory)['status']=='AUTHORED'
    _,draft,_,payloads=load_authored_wave(directory=directory,artifact_writer=plane,lazy_payloads=True)
    _,plan,_=_retained_plans(payloads,draft)
    assert type(plan) is DevelopmentExecutionPlan and len(plan.tasks)==2*len(selected.programme.cases)+1
    assert all((task.capability.requested_outcome_access,output.outcome_access,output.visibility_ceiling)==(
        OutcomeAccess.EVALUATION_REVEALED,OutcomeAccess.EVALUATION_REVEALED,VisibilityCeiling.OUTCOME_VISIBLE)
        for task in plan.tasks for output in task.outputs)
    assert all(not row.registration().native_effect for row in owner.operation_declarations())
    return SimpleNamespace(selected=selected,root=root,plane=plane,request=request,events=events,service=service,
        result=result,directory=directory,draft=draft,plan=plan,payloads=payloads)


def test_actual_protected_public_derive_author_compile_and_scope_preflight_without_worker(tmp_path,scopes,literal_recipe_source_inputs,monkeypatch):  # noqa: F811
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    monkeypatch.setattr(LocalProcessExecutor,'execute',lambda *args,**kwargs:pytest.fail('compile control entered worker'))
    value=_derive_public(tmp_path,scopes,literal_recipe_source_inputs,monkeypatch)
    instance=_authenticate_experiment_instance(payloads=value.payloads,draft=value.draft)
    inputs=reader._inputs(value.result.target_specification,instance,value.payloads)
    reader._graph(value.result.target_specification,inputs,value.draft,value.plan)
    current=_external_inputs(plane=value.plane,plan=value.plan,draft=value.draft,payloads=value.payloads,read_only=False)
    access=value.payloads.original_input_access
    reference=scope_reference(value.selected.scope)
    assert access.parents==reference.produced_input_parents
    assert reader._scope_input(value.plane,value.plan,reference,current_inputs=current,
        original_input_access=access)==value.selected.scope
    assert value.events and not tuple(value.root.glob('runs/*/receipts/*'))
    def refused(*args,**kwargs):raise PermissionError('DISCLOSED_CURRENT_ORIGINAL_GRANT_REFUSAL')
    monkeypatch.setattr(runtime,'_original_grants',refused)
    monkeypatch.setattr(reader,'_scope_input',lambda *args,**kwargs:pytest.fail('original grant refusal followed value-level Scope decode'))
    with pytest.raises(PermissionError,match='CURRENT_ORIGINAL_GRANT_REFUSAL'):
        reader._replay(writer=value.plane,specification=value.result.target_specification,inputs=inputs,draft=value.draft,
            plan=value.plan,receipts=dict.fromkeys(task.task_id for task in value.plan.tasks),codecs={},
            current_inputs=current,original_input_access=access)


def test_actual_protected_public_pure_run_read_recover_keeps_revealed_custody(tmp_path,scopes,literal_recipe_source_inputs,monkeypatch):  # noqa: F811
    value=_derive_public(tmp_path,scopes,literal_recipe_source_inputs,monkeypatch)
    completed=value.service.run(directory=value.directory,maximum_parallel_tasks=4)
    assert completed['status']=='SUCCEEDED' and completed['new_native_contact_count']==0
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    monkeypatch.setattr(LocalProcessExecutor,'execute',lambda *args,**kwargs:pytest.fail('completed recovery entered worker'))
    recovered=value.service.recover(directory=value.directory,maximum_parallel_tasks=4)
    assert recovered['status']=='SUCCEEDED' and recovered['new_native_contact_count']==0
    from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_operation
    with scientific_reconstruction_operation('full'):
        science=value.service.read(directory=value.directory)['scientific_result']
    assert science['scientific_completion']=='COMPLETE_ORIGINAL_FULL_FACTOR_CENSUS' and science['scientific_qualification']=='NOT_ESTABLISHED'
    assert science['assigned_cases']==len(value.selected.scope.sources)
    assert all(row['value']['disposition']=='HISTORY_UNAVAILABLE' for row in science['assessments'])
    secondary=science['secondary_structural_functional_readout']
    assert secondary['scope']=='SECONDARY_E4_DENSE_FACTOR_STRUCTURAL_FUNCTIONAL_RETAINED_JOIN'
    assert secondary['criterion_origin']==value.request.secondary_readout.target.to_document()
    assert secondary['target_lineage_scope']==LINEAGE_SCOPE
    assert secondary['normalized_tolerance']=={'decimal':'0.01'}
    assert secondary['assigned_cases']==len(value.selected.scope.sources)
    assert len(secondary['adequacy'])==58*len(value.selected.scope.sources)
    assert len(secondary['structural_functional_horizons'])==12*len(value.selected.scope.sources)
    assert all(row['classification']=='UNRESOLVED' for row in secondary['adequacy'])
    before=len(value.events)
    partial=value.service.read(directory=value.directory,allow_partial=True)
    assert partial['scientific_result']['scientific_completion']=='NOT_ESTABLISHED' and len(value.events)==before
    assert any(event[0]=='original-grant' for event in value.events)
    # Disclosed unissued authority seam: retain a fresh final current-access
    # refusal after actual structural replay. A snapshot alone cannot detect
    # elapsed expiry when the original grant bytes have not changed.
    for reason in ('EXPIRED_DURING_REPLAY','REVOKED_DURING_REPLAY'):
        with monkeypatch.context() as late:
            replayed=[];checks=[]
            actual_read=reader.map_reconstructions
            def measure(*args,**kwargs):
                result=actual_read(*args,**kwargs)
                replayed.extend(result)
                return result
            def current_access(*args,**kwargs):
                checks.append(len(replayed))
                if replayed:raise PermissionError('DISCLOSED_'+reason)
            late.setattr(reader,'map_reconstructions',measure)
            late.setattr(runtime,'_original_grants',current_access)
            with scientific_reconstruction_operation('full'), pytest.raises(PermissionError,match=reason):
                value.service.read(directory=value.directory)
            assert checks==[0,len(value.selected.scope.sources)]
            assert len(replayed)==len(value.selected.scope.sources)


def test_actual_original_protected_grant_refusal_is_not_replaced_by_analysis_root(scopes,literal_recipe_source_inputs,monkeypatch):  # noqa: F811
    selected=_selected(scopes,literal_recipe_source_inputs,monkeypatch)
    events=[]
    def refused(*args,**kwargs):
        events.append((args,kwargs));raise PermissionError('DISCLOSED_CURRENT_ORIGINAL_GRANT_REFUSAL')
    monkeypatch.setattr(runtime,'_actual_package',refused)
    with pytest.raises(PermissionError,match='CURRENT_ORIGINAL_GRANT_REFUSAL'):
        runtime._original_grants(object(),selected.scope)
    assert len(events)==1


def test_revealed_initial_loader_remains_admitted_but_custody_only_refuses_before_catalog(tmp_path,scopes,literal_recipe_source_inputs,monkeypatch):  # noqa: F811
    value=_derive_public(tmp_path,scopes,literal_recipe_source_inputs,monkeypatch)
    _,draft,_,_=load_authored_wave(directory=value.directory,artifact_writer=value.plane,lazy_payloads=True,
        require_initial_experiment=True)
    assert draft.development_study.access_pair==(OutcomeAccess.EVALUATION_REVEALED,VisibilityCeiling.OUTCOME_VISIBLE)
    from empirical_lawhood.api import recursive_execution as execution
    import empirical_lawhood.infrastructure.sql as sql
    def forbidden(*args,**kwargs):pytest.fail('revealed custody refusal followed plan/input/catalog processing')
    monkeypatch.setattr(execution,'_retained_plans',forbidden)
    monkeypatch.setattr(execution,'_external_inputs',forbidden)
    monkeypatch.setattr(sql,'create_catalog_engine',forbidden)
    with pytest.raises(PermissionError,match='ordinary exposed DEV custody'):
        value.service.recover(directory=value.directory,custody_only=True)
