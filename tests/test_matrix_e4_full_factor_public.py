# SPDX-License-Identifier: MPL-2.0
"""Disclosed PURE public lifecycle controls, never original native qualification.

Only the original producer reader is replaced by an explicitly disclosed I/O
seam. All copied FILE loading, public derivation, compilation, authoring, PURE
execution, receipt custody and retained independent replay remain real.
"""
from dataclasses import replace
from decimal import Decimal
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import E4_LINEAGE_SCOPE as LINEAGE_SCOPE
from tests.matrix_e4_structure_support import publish_secondary, disclosed_secondary_target
from empirical_lawhood.runtime.artifacts import ArtifactProfile,ArtifactWriteRequest
from empirical_lawhood.kernel.evidence import OutcomeAccess,VisibilityCeiling
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import full_factor_preparation as domain,full_factor_bindings as owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_followup_records import ScheduledFullFactorScope,scope_reference
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_bank_recipe as recipe,records as old
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_method_bindings import SelectedE4DevelopmentAcquisition
from empirical_lawhood.api.experiment_preparation import load_experiment_inputs
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.integration_artifact_profiles import integration_artifact_profile_validators
from empirical_lawhood.api.recursive_authoring import implementation_binding,load_authored_wave
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_document_bytes
from empirical_lawhood.planning.experiment_inputs import ExperimentInputBinding,ExperimentInputSelection
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan
from tests.runtime_platform.test_recursive_compiler import fixture as campaign_fixture
from tests.test_matrix_e4_full_factor_values import scopes,pin  # noqa: F401
from tests.test_matrix_selected_e4_bank_recipe import literal_recipe_source_inputs  # noqa: F401
from tests.test_matrix_selected_protected import unpublished
from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.infrastructure.bounded_io import BoundedFileIOError
from empirical_lawhood.runtime.artifacts import ExternalRootContract


def _real_plane(path):
    path.mkdir()
    contract = ExternalRootContract("matrix-full-factor-disclosed", "Disclosed E4 public control",
        str(path.resolve()), "/media/chevre/EL", "empirical-lawhood/testing/matrix-full-factor", 1)
    plane = ExternalArtifactPlane(GuardedExternalRoot(contract), integration_artifact_profile_validators())
    assert plane.root.diagnostic().write_ready
    return plane

ROOT=Path(__file__).resolve().parents[1]




def _published_secondary(selected, plane):
    """Publish before the public PURE readout, using the actual owning API."""
    document, secondary = publish_secondary(plane, selected.bank,
        Path(plane.root.contract.canonical_path) / "early-secondary")
    request = replace(selected.request, secondary_readout=secondary)
    return SimpleNamespace(**{**vars(selected), "request": request,
        "secondary_target": document, "secondary_readout": secondary,
        "specification": replace(selected.specification, request=request.identity)}), document, secondary.publication


def selected_values(scope_values,f,*,plane):
    allocation=recipe.recipe_allocation(f.inputs)
    reservation=old.ScheduledReservation('reservation.full-factor.disclosed',allocation,unpublished(allocation,'allocation.full-factor.disclosed'))
    selection=recipe.recipe_selection(f.inputs,reservation)
    spec=old.ScheduledSpecification('specification.full-factor.disclosed',selection,unpublished(selection,'selection.full-factor.disclosed'))
    criterion=f.inputs.original_preparation.mathematical_protocol
    _,responses=recipe.recipe_responses(f.inputs,reservation,spec,f.case.provenance,'DEVELOPMENT')
    bank=recipe.recipe_bank(f.inputs,reservation=reservation,specification=spec,provenance=f.case.provenance,
        criterion_publication=unpublished(criterion,'criterion.full-factor.disclosed'),
        response_publication=unpublished(responses,'responses.full-factor.disclosed.development'),phase='DEVELOPMENT')
    programme,cases,sources=scope_values['DEVELOPMENT']
    locator=SelectedE4DevelopmentAcquisition('acquisition.full-factor.disclosed','disclosed-original','run.disclosed',
        pin('plan.disclosed',DevelopmentExecutionPlan),pin('receipt.disclosed',CanonicalTaskReceipt),False)
    scope=ScheduledFullFactorScope('scope.experiment.full-factor.disclosed',programme,cases,sources,locator,None,())
    resources=domain.ScheduledFullFactorResources('resources.full-factor.disclosed',tuple((phase,ResourceBudget(1,1024**3,0,None,None,64*1024**2)) for phase in ('assess','measure','reduce')))
    development=owner.development_root(scope,study_id='study.full-factor.'+programme.programme_id)
    campaign=replace(campaign_fixture()[0].campaign,system_ids=(development.system.object_id,),world_ids=(development.world_id,),
        target_claim_ids=tuple(sorted(claim.claim_id for claim in development.claims)))
    request=domain.ScheduledFullFactorDevelopmentRequestV3('request.full-factor.disclosed',programme.identity,bank.identity,
        resources.identity,ObjectIdentity.from_record(campaign.campaign_id,campaign),locator,publish_secondary(plane,bank,Path(plane.root.contract.canonical_path)/"early-secondary")[1])
    specification=domain.ScheduledFullFactorDevelopmentSpecification('experiment.full-factor.disclosed',request.identity,None,None,None)
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import SelectedE3E4Evidence
    evidence=SelectedE3E4Evidence('evidence.full-factor.disclosed',programme.identity,
        f.inputs.original_products,scope.produced_input_parents)
    return SimpleNamespace(programme=programme,bank=bank,scope=scope,resources=resources,campaign=campaign,
        request=request,specification=specification,evidence=evidence,
        secondary_target=disclosed_secondary_target(bank),secondary_readout=request.secondary_readout)


@pytest.fixture
def selected(scopes,literal_recipe_source_inputs,tmp_path):  # noqa: F811
    return selected_values(scopes,literal_recipe_source_inputs,plane=_real_plane(tmp_path/"selected-early-target"))

def _copied(selected,directory):
    records={'request':selected.request,'programme':selected.programme,'bank':selected.bank,'resources':selected.resources,'campaign':selected.campaign}
    bindings=[]
    for role,record in sorted(records.items()):
        name=role+'.json';(directory/name).write_bytes(record.canonical_bytes())
        field={'programme':'programme_id','bank':'bank_id','campaign':'campaign_id'}.get(role,'record_id')
        bindings.append(ExperimentInputBinding(role,ObjectIdentity.from_record(getattr(record,field),record),name,len(record.canonical_bytes())))
    path=directory/'inputs.json'
    path.write_bytes(ExperimentInputSelection('inputs.full-factor.disclosed',domain.DEV_PROTOCOL_ID,tuple(bindings)).canonical_bytes())
    spec=directory/'initial.json';spec.write_bytes(selected.specification.canonical_bytes())
    return spec,path



def _development_access_seam(monkeypatch,selected,writer,events=None):
    """Explicit unissued original I/O seam; no grant or custody claim.

    The actual access class still validates each inherited member's exact
    parent census. Only its storage permission read and original packet reader
    are replaced; the separate C-backed lifecycle control uses real producers.
    """
    from empirical_lawhood.api import matrix_full_factor_access as access_owner
    from empirical_lawhood.api.selected_e3_access import SelectedE3OriginalInputAccess
    evidence=selected.evidence
    access=SelectedE3OriginalInputAccess(writer,evidence.upstream_products,evidence.upstream_products,
        evidence.produced_input_parents,())
    def current(self,*,artifact_writer=None):
        assert self.parents==evidence.produced_input_parents
        assert self.writer.root.contract==writer.root.contract
        if artifact_writer is not None:assert artifact_writer.root.contract==writer.root.contract
        # No real stored-grant read is claimed by this disclosed seam.
    def original(*,artifact_writer,request,evidence=None,read_access=None):
        assert artifact_writer.root.contract==writer.root.contract
        if (request.programme!=selected.programme.identity or request.bank!=selected.bank.identity
                or request.original!=selected.scope.development or evidence is not None and evidence!=selected.evidence):
            raise PermissionError('disclosed original packet substitutes its exact original request/evidence')
        access.require_current()
        return access,selected.evidence
    monkeypatch.setattr(SelectedE3OriginalInputAccess,'require_current',current)
    monkeypatch.setattr(access_owner,'development_original_access',original)
    return access


def test_static_leaves_and_blind_layout_exclude_original_outcome_bodies(selected):
    allocation=domain.programme_allocation(selected.programme,selected.bank)
    assert allocation.unit_ids()==selected.programme.group_ids
    assert {unit.source_id for unit in allocation.units} <= {source.object_id for source in allocation.sources}
    declarations=domain.protocol_declarations()
    assert {row.protocol_id for row in declarations}=={domain.DEV_PROTOCOL_ID,domain.PROTECTED_PROTOCOL_ID}
    assert all(row.requires_prospective_runtime_binding!=row.requires_development_runtime_binding for row in declarations)
    assert all({kind.SCHEMA for kind in row.input_file_record_types}=={ScheduledFullFactorScope.SCHEMA,domain.r.ScheduledFullFactorSource.SCHEMA} for row in declarations)
    reference=scope_reference(selected.scope)
    draft=owner.lower(reference,selected.resources,draft_id='draft.disclosed',campaign=selected.campaign)
    assert b'"original_cases"' not in draft.canonical_bytes()
    assert b'"source_state"' not in draft.canonical_bytes()
    assert b'"history_numerical_pass"' not in draft.canonical_bytes()
    assert len(draft.operations)==2*len(selected.programme.cases)+1
    assert all(any(edge.external_input_id is not None and edge.consumer_node_id==row.node_id for edge in draft.links) for row in draft.operations)
    assert {edge.consumer_node_id for edge in draft.links}=={row.node_id for row in draft.operations}
    assert all('forecast' not in row.selection.capability_key for row in draft.operations)
    assert reference.scope==selected.scope.identity


def test_current_full_factor_contract_refuses_retired_request_and_preparation_roles(selected):
    request=selected.request
    raw=request.canonical_bytes()
    assert decode_canonical_bytes(raw,type(request),maximum_bytes=len(raw)).canonical_bytes()==raw
    assert domain.request_types(False)==(domain.ScheduledFullFactorDevelopmentRequestV3,)
    assert domain.request_types(True)==(domain.ScheduledFullFactorProtectedRequestV4,)
    declarations=domain.protocol_declarations()
    for declaration in declarations:
        expected=domain.request_types(declaration.protocol_id==domain.PROTECTED_PROTOCOL_ID)[0]
        configurations=tuple(row for row in declaration.configuration_inputs if '.request' in row.consumer_id)
        assert len(configurations)==1
        assert configurations[0].consumer_id.endswith('.request') and configurations[0].record_type is expected
    document=request.to_document();document['version']='1.0.0'
    with pytest.raises(ValueError,match='unsupported canonical document version'):
        decode_canonical_bytes(canonical_json_document_bytes(document),type(request),maximum_bytes=None)
    specification=selected.specification
    assert specification.to_document()['value']['preparation'] is None
    before=specification.canonical_bytes()
    assert decode_canonical_bytes(before,type(specification),maximum_bytes=len(before)).canonical_bytes()==before
    with pytest.raises(ValueError,match='cannot invent prospective preparation'):
        replace(specification,preparation=ObjectIdentity('preparation.retired',
            'empirical-lawhood/matrix-selected-e4/full-factor-protected-preparation','1.0.0','a'*64))
    for role in ('template','preparation'):
        with pytest.raises(ValueError,match='unsupported scientific roles'):
            domain.bind_inputs(specification,{role:object()})


def test_one_original_case_measurement_uses_production_npz_codec_and_exact_reopen(selected,tmp_path):
    """Disclosed unentered original: real PURE measure/custody, no native claim."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import full_factor_records as records,full_factor_science as science
    from empirical_lawhood.infrastructure.artifact_stream_primitives import ArtifactIdentityConflict
    from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
    from empirical_lawhood.runtime.execution import VerifiedArtifactInput

    root=tmp_path/'one-original-measure'
    plane=_real_plane(root)
    source=selected.scope.sources[0]
    copied_path=root/'original-source.json'
    copied_path.write_bytes(source.canonical_bytes())
    copied=decode_canonical_bytes(copied_path.read_bytes(),records.ScheduledFullFactorSource,maximum_bytes=None)
    assert copied==source and copied.history is None
    raw,product=science.measure(copied,None,artifact_id='diagnostics.disclosed.one-original')
    request=ArtifactWriteRequest(product.arrays.array_artifact.artifact_id,'diagnostics.npz',MATRIX_ARRAY_SCHEMA,
        ArtifactProfile.MATRIX_ARRAY_NPZ,'application/x-npz','one-original-measure','.',raw,
        VisibilityCeiling.DEVELOPMENT_ONLY,(),OutcomeAccess.DEVELOPMENT_VISIBLE)
    # Reproduce the omitted-codec fixture failure before the expensive full graph.
    with pytest.raises(ArtifactIdentityConflict):
        ExternalArtifactPlane(plane.root).preflight_write(request)
    publication=plane.write(request)
    value=VerifiedArtifactInput(publication.logical,publication.materialization)
    port=plane.open(value,maximum_bytes=len(raw))
    try:
        reopened=port.read()
    finally:
        port.close()
    assert reopened==raw
    assessment=science.assess(copied,product,None,reopened)
    assert assessment.disposition=='HISTORY_UNAVAILABLE' and not assessment.witness_pass
    # Registration admits this exact closed codec, not malformed array bytes.
    with pytest.raises(ArtifactIdentityConflict):
        plane.preflight_write(replace(request,logical_artifact_id='diagnostics.disclosed.damaged',
            relative_path='damaged.npz',payload=b'not-an-npz'))


def test_public_copied_derive_author_pure_run_read_and_partial_guard(selected,tmp_path,monkeypatch):
    from empirical_lawhood.api import matrix_full_factor_derivation as derive,matrix_full_factor_authoring as author,matrix_full_factor_runtime as runtime,matrix_full_factor_read as reader
    root=tmp_path/'full-factor-public-disclosed'
    assert root.is_relative_to(Path('/media/chevre/EL/empirical-lawhood'))
    plane=_real_plane(root)
    before=selected.request.canonical_bytes()
    selected,document,target_publication=_published_secondary(selected,plane)
    request=selected.request
    raw=request.canonical_bytes()
    assert decode_canonical_bytes(raw,type(request),maximum_bytes=len(raw))==request
    assert b'original_utf8' not in raw and b'"normalized_adequacy_tolerance"' not in raw
    assert decode_canonical_bytes(before,domain.ScheduledFullFactorDevelopmentRequestV3,maximum_bytes=None).canonical_bytes()==before
    spec_path,input_path=_copied(selected,root)
    events=[]
    access=_development_access_seam(monkeypatch,selected,plane,events)
    def original(**kwargs):
        events.append(kwargs)
        if kwargs.get('_consume_original_access') is not None:
            kwargs['_consume_original_access'](access,selected.evidence)
        if kwargs.get('_consume_functional') is not None:
            from tests.matrix_e4_structure_support import unentered_dense_functional_rows as dense_e4_functional_rows
            for case in selected.scope.original_cases:
                kwargs['_consume_functional'](dense_e4_functional_rows(selected.bank,case,None, dense_score=None,
                    target=document,secondary=request.secondary_readout))
        if kwargs.get('_consume_programme_result') is not None:
            kwargs['_consume_programme_result'](observations=(),report={
                'state':'DISCLOSED_UNENTERED_ORIGINAL_FIXTURE','new_native_contact_count':0})
        return selected.scope,()
    monkeypatch.setattr(derive,'derive_original_full_factor_scope',original)
    monkeypatch.setattr(author,'authenticate_original_full_factor_scope',lambda **kwargs:events.append(kwargs) or ())
    monkeypatch.setattr(runtime,'authenticate_original_full_factor_reference',original)
    monkeypatch.setattr(reader,'authenticate_original_full_factor_reference',original)
    service=ExperimentProgrammeService(ROOT,plane)
    source=implementation_binding(ROOT)
    execution=ExecutionSelection(4,'main-locked',ObjectIdentity.from_record('recursive-member.implementation',source),str(root))
    result=service.derive_inputs(specification_path=spec_path,source_selection_path=input_path,metadata_directory=root/'derived',
        output_selection_path=root/'derived'/'sources.json',execution=execution)
    assert result.preparation.executable and result.preparation.input_records==()
    assert 'scope' not in dict(result.preparation.design_records)
    assert dict(result.preparation.design_records)['reference']==scope_reference(selected.scope)
    copied=load_experiment_inputs(result.target_specification,result.source_selection_path,artifact_writer=plane)
    assert copied.method_inputs.scope==selected.scope
    directory=root/'authored'
    report=service.author(preparation=result.preparation,output_dir=directory)
    assert report['status']=='AUTHORED'
    _,draft,_,_=load_authored_wave(directory=directory,artifact_writer=plane,lazy_payloads=True)
    assert draft==result.preparation.draft
    completed=service.run(directory=directory,maximum_parallel_tasks=4)
    assert completed['status']=='SUCCEEDED'
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    monkeypatch.setattr(LocalProcessExecutor,'execute',lambda *args,**kwargs:pytest.fail('completed full-factor recovery entered executor'))
    recovered=service.recover(directory=directory,maximum_parallel_tasks=4)
    assert recovered['status']=='SUCCEEDED' and recovered['new_native_contact_count']==0
    from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_operation
    with scientific_reconstruction_operation('full'):
        retained=service.read(directory=directory)
    science=retained['scientific_result']
    assert science['scientific_completion']=='COMPLETE_ORIGINAL_FULL_FACTOR_CENSUS'
    assert science['assigned_cases']==len(selected.programme.cases) and science['scientific_qualification']=='NOT_ESTABLISHED'
    assert all(row['value']['history_available'] is False for row in science['assessments'])
    secondary=science['secondary_structural_functional_readout']
    assert secondary['normalized_tolerance']=={'decimal':'0.01'} and document.normalized_adequacy_tolerance==Decimal('.01')
    assert secondary['criterion_origin']==document.identity.to_document()
    assert secondary['target_lineage_scope']==LINEAGE_SCOPE
    assert len(secondary['adequacy'])==len(selected.scope.sources)*58
    assert len(secondary['structural_functional_horizons'])==len(selected.scope.sources)*12
    assert all(row['classification']=='UNRESOLVED' for row in secondary['adequacy'])
    assert all(not row['structural_usable'] for row in secondary['structural_functional_horizons'])
    assert all(not row['degenerate_complete_lifetime_labels'] for row in secondary['lifetime_pattern_census'])
    actual_target=plane.root.resolve(target_publication.materialization.relative_path,for_write=False)
    raw=actual_target.read_bytes();before_original=len(events)
    try:
        actual_target.write_bytes(b'changed')
        with pytest.raises((ValueError,PermissionError,RuntimeError)):
            service.read(directory=directory)
        assert len(events)==before_original
    finally:
        actual_target.write_bytes(raw)
    before=len(events)
    partial=service.read(directory=directory,allow_partial=True)
    assert partial['scientific_result']['scientific_completion']=='NOT_ESTABLISHED' and len(events)==before
    from empirical_lawhood.api.recursive_execution import read_recursive_wave
    compact=read_recursive_wave(directory=directory,artifact_writer=plane,terminal_product_format='compact')
    assert compact['scientific_result']['scientific_completion']=='NOT_ESTABLISHED' and len(events)==before
    scope_file=dict(result.preparation.input_files)[owner.scope_input(selected.scope)].path
    scope_file.write_bytes(scope_file.read_bytes()+b'\n')
    with pytest.raises(BoundedFileIOError,match='byte limit'):
        load_experiment_inputs(result.target_specification,result.source_selection_path,artifact_writer=plane)
    # Changed original producer selection cannot be hidden behind the same
    # completed programme and an unrelated immutable scope reference.
    changed=replace(selected.request,original=replace(selected.request.original,run_id='run.substituted'))
    with pytest.raises(ValueError,match='locator|requested'):
        domain.validate_reference(replace(result.target_specification,request=changed.identity),
            replace(copied.method_inputs,request=changed))


def test_original_callbacks_refuse_partial_and_noncallable_before_io(monkeypatch):
    from empirical_lawhood.api import matrix_selected_e3_e4_read as dev,selected_e4_native_read as protected
    monkeypatch.setattr(dev,'_read_recursive_wave_with_roots',lambda **kwargs:pytest.fail('partial original consumer reached I/O'))
    with pytest.raises(ValueError,match='complete ordinary'):
        dev.read_selected_e3_e4_development(directory=None,artifact_writer=None,allow_partial=True,_consume_original=lambda **kwargs:None)
    with pytest.raises(TypeError,match='callable'):
        protected.read_selected_e4_wave(writer=None,declaration=None,locator=None,codecs=None,_consume_original=object())


@pytest.mark.parametrize('damage',(None,'programme','bank','evidence-size','evidence-pin','noncanonical-evidence',
    'evidence-programme','evidence-parents','missing-access','grant-after-products','grant-final',
    'missing-entry-receipt','run','plan'))
def test_full_factor_dev_uses_one_ordinary_reader_and_its_exact_access_evidence(selected,tmp_path,monkeypatch,damage):
    """Disclosed metadata/permission I/O seams; real reader and derivation joins.

    The source records, entry CONFIG decoding, case reduction and complete scope
    projection are real. These unissued software operands establish no producer
    custody, grant, native result, freshness or scientific qualification.
    """
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as dev_owner
    from empirical_lawhood.api import matrix_full_factor_access as access_owner,matrix_full_factor_custody as custody
    from empirical_lawhood.api import matrix_selected_e3_e4_read as original_reader
    from empirical_lawhood.api.selected_e3_access import SelectedE3OriginalInputAccess
    from empirical_lawhood.planning.recursive_authoring import RecursiveOperationSpec
    from empirical_lawhood.runtime.prospective_experiment import source_filename
    writer=_real_plane(tmp_path/'ordinary-original')
    selected,_,_=_published_secondary(selected,writer)
    (Path(writer.root.contract.canonical_path)/selected.scope.development.authored_directory).mkdir()
    evidence=selected.evidence
    if damage=='evidence-programme':
        evidence=replace(evidence,programme=replace(evidence.programme,object_fingerprint='f'*64))
    raw=evidence.canonical_bytes()
    evidence_pin=evidence.identity
    if damage=='noncanonical-evidence':
        raw+=b' '
        from hashlib import sha256
        evidence_pin=replace(evidence_pin,object_fingerprint=sha256(raw).hexdigest())
    if damage=='evidence-pin':
        evidence_pin=replace(evidence_pin,object_fingerprint='f'*64)
    task=dev_owner.global_node(selected.programme,'entry')
    entry=dev_owner.SelectedE3E4EntryConfig('config.'+task,selected.programme,selected.bank,evidence_pin,
        len(raw)+(damage=='evidence-size'),selected.evidence.produced_input_parents, secondary_readout=selected.secondary_readout)
    declaration=next(row for row in dev_owner.operation_declarations() if row.capability_key==dev_owner.NAMESPACE+'.entry')
    operation=RecursiveOperationSpec.from_config(node_id=task,selection=declaration.registration().selection,
        config_id=entry.config_id,config=entry,obligation_ids=('obligation.'+task,),
        resource_budget=dict(selected.resources.phase_budgets)['measure'])
    draft=SimpleNamespace(operations=(operation,),development_study=object(),prospective_draft=None)
    locator=selected.scope.development
    plan=SimpleNamespace(execution_plan_id=locator.execution_plan.object_id,SCHEMA=DevelopmentExecutionPlan.SCHEMA,
        VERSION=DevelopmentExecutionPlan.VERSION,fingerprint=lambda:'f'*64 if damage=='plan' else locator.execution_plan.object_fingerprint,
        tasks=())
    receipt=SimpleNamespace(receipt_id=locator.entry_receipt.object_id,SCHEMA=CanonicalTaskReceipt.SCHEMA,
        VERSION=CanonicalTaskReceipt.VERSION,fingerprint=lambda:locator.entry_receipt.object_fingerprint)
    products={'receipts':{} if damage=='missing-entry-receipt' else {task:receipt},'outputs':{},'terminal':object(),
        'product_index':()}
    packet=SimpleNamespace(fingerprint=lambda:'c'*64)
    run=SimpleNamespace(run_plan_id='run.substituted' if damage=='run' else locator.run_id)
    events=[]
    access=SelectedE3OriginalInputAccess(writer,selected.evidence.upstream_products,selected.evidence.upstream_products,
        () if damage=='evidence-parents' else selected.evidence.produced_input_parents,())
    revoked=False
    def current(self,*,artifact_writer=None):
        assert self is access
        if artifact_writer is not None:assert artifact_writer is writer
        events.append('current')
        if revoked or damage=='grant-after-products' and 'products' in events:
            raise PermissionError('actual current grant refused at later boundary')
    monkeypatch.setattr(SelectedE3OriginalInputAccess,'require_current',current)
    class Payloads(dict):
        original_input_access=None if damage=='missing-access' else access
        def __getitem__(self,name):
            events.append('evidence-body')
            return super().__getitem__(name)
    payloads=Payloads({source_filename(entry.evidence):raw})
    def ordinary(**kwargs):
        assert kwargs['include_products'] is True and kwargs['allow_partial'] is False
        assert kwargs['terminal_product_format']=='compact'
        events.append('ordinary-reader')
        kwargs['validate_authored'](packet=packet,draft=draft,source=None,payloads=payloads,run=run,plan=plan,index=None)
        events.append('products')
        report={'packet_sha256':packet.fingerprint(),'run_id':run.run_plan_id,'status':'SUCCEEDED'}
        report['scientific_result']=kwargs['scientific_consumer'](artifact_writer=writer,report=report,products=products,
            payloads=payloads,draft=draft,plan=plan)
        return (report,products,draft,plan),(packet,draft,None,run,plan,None),entry
    monkeypatch.setattr(original_reader,'_read_recursive_wave_with_roots',ordinary)
    def duplicate(**_):
        pytest.fail('full-factor projection reloaded the original DEV packet separately')
    monkeypatch.setattr(access_owner,'development_packet_access',duplicate)
    cases={dev_owner.local_node(row.root_id,'collect'):row for row in selected.scope.original_cases}
    monkeypatch.setattr(original_reader,'_record',lambda writer,products,task,kind,**_:cases.get(task))
    def absent(*args,**kwargs):
        events.append('derived-original')
        kwargs['original_input_access'].require_current()
        return None,None
    monkeypatch.setattr(custody,'_record',absent)
    actual_access=[]
    def observe_access(actual,actual_evidence):
        assert actual is access and actual_evidence==selected.evidence
        events.append('access-observer')
        actual_access.append((actual,actual_evidence))
    def observe_result(**_):
        nonlocal revoked
        events.append('programme-result')
        if damage=='grant-final':revoked=True
    programme=selected.programme
    if damage=='programme':programme=replace(programme,programme_id='programme.substituted')
    if damage=='bank':programme=replace(programme,bank=replace(programme.bank,object_fingerprint='f'*64))
    def derive():
        return custody.derive_original_full_factor_scope(writer=writer,programme=programme,
            bank=None if damage=='bank' else selected.bank,record_id=selected.scope.record_id,codecs={},
            development=locator,_consume_original_access=observe_access,_consume_programme_result=observe_result)
    if damage is None:
        scope,files=derive()
        assert scope==selected.scope and files==()
        assert actual_access==[(access,selected.evidence)]
        assert events.count('ordinary-reader')==events.count('evidence-body')==1
        assert events.count('derived-original')==3*len(selected.programme.cases)
        assert events[-1]=='current'
    else:
        with pytest.raises((PermissionError,ValueError)):
            derive()
        if damage in ('programme','bank'):
            assert 'products' not in events and 'evidence-body' not in events
        if damage!='grant-final':
            assert 'derived-original' not in events and not actual_access
        else:
            assert 'programme-result' in events and actual_access



def test_e4_early_target_publication_is_blind_reopens_exactly_and_refuses_changed_bytes(selected, tmp_path, monkeypatch):  # noqa: F811
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import MatrixE4SecondaryTarget
    from empirical_lawhood.api.matrix_full_factor_secondary import publish_e4_secondary_target, authenticate_e4_secondary_target
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor, DirectTaskExecutor
    from empirical_lawhood.infrastructure.bounded_io import BoundedFileIOError
    from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
    # These are disclosed software operands. No issue, native contact, source
    # qualification or scientific result is supplied by this target publication.
    def forbidden(*args, **kwargs):
        pytest.fail('early target publication entered an executor')
    monkeypatch.setattr(LocalProcessExecutor, 'execute', forbidden)
    monkeypatch.setattr(DirectTaskExecutor, 'execute', forbidden)
    plane = _real_plane(tmp_path / 'e4-early-target-disclosed')
    document = MatrixE4SecondaryTarget('target.e4.early.disclosed', selected.bank.forecast_design.criterion_record,
        Decimal('.01'), (Decimal('.005'), Decimal('.02'), Decimal('.05')),
        tuple(range(16, 129, 4)), Decimal('.001'))
    directory = plane.root.resolve('inputs/e4-target', for_write=True)
    secondary = publish_e4_secondary_target(writer=plane, directory=directory, target=document, bank=selected.bank)
    assert (secondary.publication.logical.outcome_access, secondary.publication.logical.visibility_ceiling) == (
        OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
    assert secondary.publication.logical.lineage_parents == ()
    assert secondary.publication.materialization.physical_sha256 == document.fingerprint()
    before = {path.relative_to(plane.root.contract.canonical_path).as_posix(): path.read_bytes()
        for path in Path(plane.root.contract.canonical_path).rglob('*') if path.is_file()}
    assert authenticate_e4_secondary_target(writer=plane, selection=secondary, bank=selected.bank) == document
    assert publish_e4_secondary_target(writer=plane, directory=directory, target=document, bank=selected.bank) == secondary
    assert before == {path.relative_to(plane.root.contract.canonical_path).as_posix(): path.read_bytes()
        for path in Path(plane.root.contract.canonical_path).rglob('*') if path.is_file()}
    path = plane.root.resolve(secondary.publication.materialization.relative_path, for_write=False)
    raw = path.read_bytes()
    path.write_bytes(raw[:-1] + (b' ' if raw[-1:] != b' ' else b'\n'))
    with pytest.raises((ArtifactIdentityConflict, PermissionError, ValueError, BoundedFileIOError)):
        authenticate_e4_secondary_target(writer=plane, selection=secondary, bank=selected.bank)


def test_e4_early_publisher_rejects_old_e3_target_before_any_publication(selected, tmp_path):  # noqa: F811
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import MatrixE3SecondaryTarget
    from empirical_lawhood.api.matrix_full_factor_secondary import publish_e4_secondary_target
    plane = _real_plane(tmp_path / 'e4-refuse-old-target-disclosed')
    before = tuple(Path(plane.root.contract.canonical_path).rglob('*'))
    old = MatrixE3SecondaryTarget('target.e3.old.disclosed', selected.bank.forecast_design.criterion_record, Decimal('.01'))
    with pytest.raises(TypeError, match='exact declared scientific target'):
        publish_e4_secondary_target(writer=plane, directory=plane.root.resolve('inputs', for_write=True), target=old, bank=selected.bank)
    assert tuple(Path(plane.root.contract.canonical_path).rglob('*')) == before
