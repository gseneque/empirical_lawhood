# SPDX-License-Identifier: MPL-2.0
"""Current C-backed source metadata controls; disclosed TEST inputs, no science.

The whole-C fixture retains the original configured TRAIN/future populations.
Its new E4 metadata uses four complete matched groups per phase, as the former
positive wrapper control did. Selected scientific populations are unchanged.
Original E3 producer reads below are explicit stubs, never eligibility proof.
"""
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods import matrix_finite_dt_source_assembly as domain
from empirical_lawhood.adapters.methods import matrix_finite_dt_source_records as source
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_operational_resources import SelectedE4OperationalResources
from empirical_lawhood.api.experiment_preparation import derive_experiment_inputs,load_experiment_inputs,prepare_experiment
from empirical_lawhood.api.recursive_authoring import implementation_binding
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import ReadinessStatus
from empirical_lawhood.planning.dataset_authority import DatasetWorkEnvelope,DatasetFileLimits,DatasetControlLimits
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection,ExperimentInputBinding
from empirical_lawhood.runtime.execution_envelope import ChildResourceTokenLimit,ProgressHeartbeat,ProgressLivenessContract
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
from empirical_lawhood.runtime.experiment_resources import ExecutionResourceSelection
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan
from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave

ROOT=Path(__file__).parents[1]


def source_metadata_case(tmp_path):
    """Actual C/publications around disclosed arithmetic original E3 records.

    TRAIN metadata here has the same declared count and scientific operands as
    the original configured package. No claim is made that those arithmetic
    fit inputs were produced by this unexecuted native request; the positive
    wrapper control explicitly substitutes that original-producer I/O boundary.
    """
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_public import ConfiguredMatrixSelectedPublicPackage
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as native
    from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES,MatrixHistorySeed
    from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole,MatrixProgrammeRoot
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammePublishedInput, MatrixProgrammeProducedInput
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as scheduled
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponsePanel
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
    from empirical_lawhood.api.codecs import load_authoring
    from empirical_lawhood.api.recursive_operations import operation_storage_codecs
    from empirical_lawhood.infrastructure.artifact_validation import ArtifactProfileValidatorRegistry
    from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.kernel.references import ArtifactIdentity
    from empirical_lawhood.runtime.experiment_preparation import PreparedExperimentFile
    from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
    from tests.test_matrix_configured_protected_public_preparation import prepared_case
    from tests.test_matrix_configured_protected_statistical import config as fit_config
    from tests.test_matrix_configured_selected_package import configured_package
    from tests.test_matrix_factor_confirmation_eligibility import publish
    from tests.test_matrix_native_training_acquisition import _whole_training_commitment
    from tests.test_matrix_scheduled_history import CONSTRUCTION
    from tests.test_matrix_selected_e4_bank_recipe import original_locators

    case=prepared_case(tmp_path/'configured-original')
    case.plane.validators=ArtifactProfileValidatorRegistry(binary_codecs=operation_storage_codecs())
    case.fit_cutoff=case.fit_config.fit_cutoff
    full,bank_context=configured_package(case,return_context=True)
    public=ConfiguredMatrixSelectedPublicPackage.from_package(full)
    def artifact(record):
        return ArtifactIdentity(record.record_id,'disclosed-arithmetic-control-bank',record.SCHEMA,
            record.fingerprint(),'application/json',len(record.canonical_bytes()))
    root=replace(case.selection.root,system=replace(case.selection.root.system,
        world=replace(case.selection.root.system.world,label='Disclosed source-wrapper metadata control',maximum_evidence=EvidenceCeiling.LOCAL_LAW)))
    preparation=replace(case.selection,root=root,fit_config=fit_config(bank_context,'fit'),
        training_allocation=bank_context.inputs.training_allocation,
        training_features=artifact(bank_context.train_features),training_outcomes=artifact(bank_context.train_outcomes))
    assay=preparation.protocols[0]
    future=preparation.manifest
    coordinate=assay.public_source.coordinate
    policy=assay.public_source.policy
    count=public.specification.population('TRAIN').expected_units
    roots,scopes=[],[]
    for number in range(count):
        group='group.disclosed-c-backed-source.train.'+str(number).zfill(3)
        root_id='root.disclosed-c-backed-source.train.'+str(number).zfill(3)
        roots.append(scheduled.ScheduledRoot(MatrixProgrammeRoot(root_id,group,'regime.disclosed-c-backed-source.train',
            coordinate.coordinate_id,MatrixProgrammeRole.DEVELOPMENT,coordinate.clock_id),
            scheduled.coordinate_identity(coordinate),tuple(MatrixHistorySeed(purpose,
                sha256(('EXPOSED.C.BACKED.SOURCE.TRAIN.'+group+purpose).encode()).hexdigest()) for purpose in HISTORY_PURPOSES)))
        scopes.append(scheduled.ScheduledMatchedScope('scope.disclosed-c-backed-source.train.'+str(number).zfill(3),
            MatrixProgrammeRole.DEVELOPMENT,(group,),(scheduled.coordinate_identity(coordinate),),CONSTRUCTION))
    allocation=scheduled.ScheduledAllocation('allocation.disclosed-c-backed-source.train',(coordinate,),tuple(roots),tuple(scopes),
        future.reservation.allocation.exposure)
    reservation=scheduled.ScheduledReservation('reservation.disclosed-c-backed-source.train',allocation,
        publish(case.plane,allocation,'c-backed-source.train-allocation'))
    selection=replace(future.native_specification.selection,selection_id='selection.disclosed-c-backed-source.train',
        reservation=scheduled.identity(reservation),prefix_policies=(policy,),
        coordinate_policies=((scheduled.coordinate_identity(coordinate),scheduled.identity(policy)),))
    specification=scheduled.ScheduledSpecification('specification.disclosed-c-backed-source.train',selection,
        publish(case.plane,selection,'c-backed-source.train-selection'))
    train=replace(future,record_id='manifest.disclosed-c-backed-source.train',reservation=reservation,native_specification=specification,
        reservation_publication=publish(case.plane,reservation,'c-backed-source.train-reservation'))
    index=ScheduledSourceIndex.from_shared(reservation=reservation,specification=specification,provenances=train.provenances)
    protocols,panels=[],[]
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
    for row in roots:
        resolved=index.resolve(index.reference(source_id='source.'+row.root.root_id,root_id=row.root.root_id,
            provenance=train.provenances[0].identity))
        protocols.append(replace(assay,protocol_id='protocol.'+row.root.root_id,public_source=ScheduledPublicSource.from_source(resolved),
            templates=replace(assay.templates,operand_id='templates.'+row.root.root_id,source=scheduled.identity(resolved),
                producers=(scheduled.identity(resolved),))))
        group=row.root.independent_group_id
        panels.extend((ScheduledResponsePanel('panel.common.'+group,group,'COMMON_NOISE_PANEL',
            'ORIGINAL_COMPLETED_PREFIX_GENERATOR_STATES',row.streams),
            ScheduledResponsePanel('panel.independent.'+group,group,'INDEPENDENT_FUTURE','FRESH_DECLARED_FUTURE_START_AT_CUTOFF',
                tuple(MatrixHistorySeed(purpose,sha256(('EXPOSED.C.BACKED.SOURCE.FUTURE.'+group+purpose).encode()).hexdigest())
                    for purpose in HISTORY_PURPOSES))))
    commitment,committed=_whole_training_commitment(plane=case.plane,train=train,future=future,candidate=public.specification,
        mathematical=preparation.mathematical_protocol,protocols=tuple(protocols),panels=tuple(panels),
        template_publications=preparation.response_selection.template_publications)
    budget=ResourceBudget(1,2*1024**3,0,None,128*1024**2,64*1024**2)
    resources=native.NativeTrainingResources('resources.disclosed-c-backed-source.train',tuple((phase,budget) for phase in native.ALL_PHASES),4)
    campaign=load_authoring(ROOT/'tests/fixtures/reference-campaign.json').campaign
    acquisition_spec=native.NativeTrainingAcquisitionSpecification('experiment.disclosed-c-backed-source.train',public.specification.measurement,
        tuple(value.public_source.root.root_id for value in protocols),scheduled.identity(future.reservation),public.specification.identity)
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_acquisition as acquisition
    request_id='request.disclosed-c-backed-source.train'
    campaign=replace(campaign,objective=acquisition.QUESTION,system_ids=(request_id,),world_ids=(acquisition.WORLD,),
        target_claim_ids=('claim.study.'+acquisition_spec.specification_id,),
        budget=ResourceBudget.aggregate((budget,)*(len(native.PHASES)*count+2)))
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import exposure_support,corpus_artifact
    mandatory=(commitment,committed.commitments.availability,committed.commitments.e6_policy,
        *(committed.commitments.phase(role).responses for role in ('e3.calibration','e3.confirmation','e6.nearby','e6.shifted')))
    campaign=replace(campaign,evidence_state=tuple(sorted((row.record for row in mandatory),key=lambda row:row.object_id)))
    support=tuple(sorted((*exposure_support(committed.exposure_audit),
        *((corpus_artifact(row.publication),row.publication) for row in mandatory)),key=lambda row:row[0].artifact_id))
    native_request=native.NativeTrainingAcquisitionRequest(request_id,train,future,public.specification,
        tuple(index.reference(source_id='source.'+row.root.root_id,root_id=row.root.root_id,provenance=train.provenances[0].identity) for row in roots),
        tuple(protocols),tuple(sorted(panels,key=lambda value:value.panel_id)),preparation.mathematical_protocol,
        preparation.response_selection.template_publications,support,campaign,resources,commitment)
    native.validate_request(acquisition_spec,native_request)
    def published(record,name,pin):
        return MatrixProgrammePublishedInput(pin,publish(case.plane,record,name))
    # These arithmetic inputs are already exposed. Their ordinary publication
    # is not a successful original producer, issue or qualification receipt.
    public_publication=case.plane.write(ArtifactWriteRequest('c-backed-source.original-e3',
        'inputs/c-backed-source.original-e3.json',public.SCHEMA,ArtifactProfile.CANONICAL_JSON,
        'application/json','publication.c-backed-source.original-e3','inputs',public.canonical_bytes(),
        VisibilityCeiling.DEVELOPMENT_ONLY,(),OutcomeAccess.DEVELOPMENT_VISIBLE))
    public_handle=MatrixProgrammeProducedInput(public.identity,public_publication)
    preparation_handle=published(preparation,'c-backed-source.original-preparation',ObjectIdentity.from_record(preparation.selection_id,preparation))
    assay_handle=published(assay,'c-backed-source.original-assay',ObjectIdentity.from_record(assay.protocol_id,assay))
    criterion_publication=publish(case.plane,preparation.mathematical_protocol,'c-backed-source.original-criterion')
    template=assay.templates.array_artifact
    template_publication,=(row for row in preparation.response_selection.template_publications if row.logical.logical_artifact_id==template.artifact_id)
    training=SimpleNamespace(plane=case.plane,request=native_request,specification=acquisition_spec,source=index.resolve(native_request.sources[0]),
        acquisition=native.acquisition_seal(acquisition_spec,native_request),template_files={template.artifact_id:PreparedExperimentFile(
            template,'1.0.0',case.plane.root.resolve(template_publication.materialization.relative_path,for_write=False),template.size_bytes)})
    return SimpleNamespace(plane=case.plane,preparation=preparation,public=public,assay=assay,commitment=commitment,committed=committed,
        original_e3=public_handle,original_preparation=preparation_handle,original_assay=assay_handle,
        original_products=original_locators(public),criterion_publication=criterion_publication,training=training)


@pytest.fixture(scope='module')
def c_backed_source_case(tmp_path_factory):
    return source_metadata_case(tmp_path_factory.mktemp('disclosed-c-backed-source'))


def selected_request(case):
    locator=source.MatrixFiniteDtTrainingLocator('unexecuted/native-train','run.unexecuted-native-train',
        ObjectIdentity('packet.unexecuted-native-train',AuthoredRecursiveWave.SCHEMA,AuthoredRecursiveWave.VERSION,'a'*64),
        ObjectIdentity('plan.unexecuted-native-train',DevelopmentExecutionPlan.SCHEMA,DevelopmentExecutionPlan.VERSION,'b'*64))
    budget=ResourceBudget(1,2*1024**3,0,None,128*1024**2,64*1024**2)
    controls=ExecutionResourceSelection('resources.disclosed-source-assembly',(),
        (ChildResourceTokenLimit('child.disclosed-source',0,0),),(),(),(),None,None,4,8*1024**3,(),(),'c'*64,True,True,True,True)
    phases=tuple(sorted((*tuple(value.value.lower() for value in source.GATES),'pipeline','qualification','adjudicate')))
    operational=SelectedE4OperationalResources('operational.disclosed-source-assembly',controls,tuple((phase,100) for phase in phases),
        ProgressLivenessContract('liveness.disclosed-source-assembly',ProgressHeartbeat.SCHEMA,'disclosed-no-native-source',Decimal(30),True,True),1)
    envelope=DatasetWorkEnvelope(replace(budget,wall_time_seconds=60),DatasetFileLimits(2,2,0,1024**2),DatasetControlLimits(1024**2,10000,1024**2,32))
    compute=replace(case.preparation.root.experiment.obligations.computability,
        readiness=ReadinessStatus.REQUIRES_PROTOCOL_FREEZE,unresolved_reason_codes=('DISCLOSED_UNEXECUTED_SOURCE',),evidence_link_ids=())
    cutoff=case.preparation.root.experiment.information_cutoffs[0]
    return domain.MatrixFiniteDtSourceAssemblyRequest('request.disclosed-source-assembly','source-assembly.disclosed',case.commitment,
        case.original_e3,case.original_preparation,case.original_assay,case.original_products,'CALIBRATION',locator,cutoff,compute,
        budget,envelope,operational,'issuer.disclosed-metadata','approver.disclosed-metadata','requester.disclosed-metadata',
        'owner-keys/absent-metadata.key',3600,('EXPLICIT_METADATA_ONLY_OPERATION',),'DISCLOSED_SOFTWARE_CONFORMANCE','scratch/disclosed-source-assembly')


def test_current_source_request_separates_produced_e3_from_blind_known_inputs(c_backed_source_case):
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammeProducedInput,MatrixProgrammePublishedInput
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.serialization import canonical_json_document_bytes
    request=selected_request(c_backed_source_case)
    assert type(request.original_e3) is MatrixProgrammeProducedInput
    assert all(type(value) is MatrixProgrammePublishedInput for value in
        (request.input_commitments,request.original_preparation,request.original_assay))
    raw=request.canonical_bytes()
    assert decode_canonical_bytes(raw,type(request),maximum_bytes=len(raw)).canonical_bytes()==raw
    document=request.to_document()
    document['value']['original_e3']['schema']=MatrixProgrammePublishedInput.SCHEMA
    with pytest.raises((ValueError,TypeError)):
        decode_canonical_bytes(canonical_json_document_bytes(document),type(request),maximum_bytes=None)
    with pytest.raises(TypeError,match='publication handles'):
        replace(request,input_commitments=request.original_e3)


def test_public_source_assembly_accepts_copied_science_and_stops_before_absent_real_machine_key(c_backed_source_case):
    case=c_backed_source_case;request=selected_request(case)
    specification=domain.MatrixFiniteDtSourceAssemblySpecification('assembly.disclosed-source',request.identity)
    plane=case.plane
    copied=Path(plane.root.contract.canonical_path)/'copied-source-assembly';copied.mkdir()
    request_path=copied/'request.json';request_path.write_bytes(request.canonical_bytes())
    spec_path=copied/'specification.json';spec_path.write_bytes(specification.canonical_bytes())
    selected=ExperimentFileInputSelection('sources.disclosed-source-assembly',domain.PROTOCOL_ID,
        (ExperimentInputBinding('request',request.identity,'request.json',request_path.stat().st_size),),())
    selected_path=copied/'sources.json';selected_path.write_bytes(selected.canonical_bytes())
    execution=ExecutionSelection(4,'environment.disclosed-source-assembly',
        ObjectIdentity.from_record('recursive-member.implementation',implementation_binding(ROOT)),plane.root.contract.canonical_path)
    inputs=load_experiment_inputs(specification,selected_path)
    prepared=prepare_experiment(specification,method_inputs=inputs.method_inputs,execution=execution)
    assert not prepared.executable and prepared.census.native_effect_count==0
    assert 'finite-dt-assembly.derive' in {value.code for value in prepared.dependencies}
    target=Path(plane.root.contract.canonical_path)/'unpublished-source-assembly'
    with pytest.raises(PermissionError,match='actual metadata key is absent'):
        derive_experiment_inputs(specification_path=spec_path,source_selection_path=selected_path,project_root=ROOT,artifact_writer=plane,
            metadata_directory=target,output_selection_path=target/'sources.json',execution=execution)
    assert not target.exists()
    assert not plane.root.resolve(request.metadata_private_key_relative_path,for_write=False).exists()
    assert request.source_computability_evidence.readiness is ReadinessStatus.REQUIRES_PROTOCOL_FREEZE


def test_source_assembly_refuses_implicit_key_policy_self_approval_and_path_escape(c_backed_source_case):
    request=selected_request(c_backed_source_case)
    assert request.metadata_reason_codes==('EXPLICIT_METADATA_ONLY_OPERATION',)
    with pytest.raises(PermissionError,match='self-approve'):replace(request,metadata_approver_id=request.metadata_requester_id)
    with pytest.raises(ValueError):replace(request,metadata_private_key_relative_path='../unsafe')
    with pytest.raises(ValueError):replace(request,metadata_validity_seconds=0)
    with pytest.raises(ValueError):replace(request,metadata_reason_codes=list(request.metadata_reason_codes))
    with pytest.raises(ValueError,match='oversized reason code'):replace(request,metadata_reason_codes=('x'*129,))
    with pytest.raises(ValueError,match='work-envelope reason-code limit'):
        replace(request,metadata_reason_codes=tuple('reason.'+str(index).zfill(3) for index in range(33)))


def test_public_source_assembly_real_metadata_materializer_target_reopen_and_exact_retry(tmp_path,monkeypatch):
    """Actual whole-C/metadata owners; disclosed producer I/O, never native."""
    from empirical_lawhood.api import matrix_programme_e4_inputs as inputs_api
    from empirical_lawhood.api.experiment_preparation import author_prepared_experiment
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    from empirical_lawhood.api.recursive_execution import _retained_plans
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as scheduled
    from empirical_lawhood.kernel.time import CausalPhase,InformationCutoff
    from tests.test_matrix_finite_dt_source import _certificate,_control
    from tests.test_matrix_native_training_public_lifecycle import _copied_preparation

    case=source_metadata_case(tmp_path)
    prototype=case.assay.public_source.coordinate
    selected=replace(selected_request(case),allow_metadata_key_creation=True,
        metadata_private_key_relative_path='owner-keys/disclosed-source-wrapper.key',
        physical_cutoff=InformationCutoff('cutoff.disclosed-source-wrapper',prototype.clock_id,CausalPhase.PREPARATION,Decimal(0)))
    training=case.training
    preparation=_copied_preparation(training,tmp_path/'copied-native')
    authored_directory=Path(case.plane.root.contract.canonical_path)/'authored-only'
    author_prepared_experiment(preparation=preparation,project_root=ROOT,artifact_writer=case.plane,output_dir=authored_directory)
    packet,draft,_,payloads=load_authored_wave(directory=authored_directory,artifact_writer=case.plane,lazy_payloads=True)
    run,plan,_=_retained_plans(payloads,draft)
    locator=source.MatrixFiniteDtTrainingLocator(authored_directory.relative_to(case.plane.root.contract.canonical_path).as_posix(),run.run_plan_id,
        ObjectIdentity.from_record(packet.packet_id,packet),ObjectIdentity.from_record(plan.execution_plan_id,plan))
    selected=replace(selected,native_training_locator=locator)
    certificate=_certificate(training,tuple(_control(training,index,available=False) for index in range(len(training.specification.root_ids))))
    assert not certificate.instrument_checks_pass
    # These four stubs supply no issued E3 or successful native-fit custody.
    # Actual whole-C authentication, allocation-free banks, source capture,
    # metadata authorization, materialization, compilation and reopening run.
    monkeypatch.setattr(inputs_api,'authenticate_selected_e3_public_package',lambda **kw:None)
    monkeypatch.setattr(inputs_api,'authenticate_selected_e3_training_banks',lambda **kw:None)
    monkeypatch.setattr(inputs_api,'authenticate_selected_e3_assay',lambda **kw:case.criterion_publication)
    # Disclosed upstream producer I/O only; actual provider joins have separate owning controls.
    monkeypatch.setattr(inputs_api,'_original_assay_provider_publications',lambda **kw:(
        case.original_assay.publication,case.preparation.response_selection.template_publications[0]))
    monkeypatch.setattr(inputs_api,'_require_original_e3_access',lambda **kw:None)
    import empirical_lawhood.api.matrix_finite_dt_source_runtime as instrument_reader
    def disclosed_certificate(**kwargs):
        bank=kwargs['bank'];protocol=bank.response_selection.protocols[0]
        return replace(certificate,record_id=kwargs['record_id'],locator=locator,request=training.request.identity,
            original_future_reservation=scheduled.identity(case.preparation.manifest.reservation),
            numerical=scheduled.identity(bank.specification.selection.numerical_design),
            factor_numerical=scheduled.identity(protocol.public_source.policy.factor_numerical_design),
            instrument_sha256=source.instrument_signature(protocol),criterion=case.preparation.mathematical_protocol.identity,
            provenances=tuple(value.identity for value in bank.provenances),
            templates=tuple(sorted({value.templates.array_artifact for value in bank.response_selection.protocols},key=lambda value:value.artifact_id)),
            reserved_future_effective_seeds=tuple(sorted({stream.effective_seed for value in case.preparation.manifest.reservation.allocation.roots for stream in value.streams})),
            future_bank=bank.identity,future_group_ids=kwargs['programme'].group_ids,cutoff=kwargs['cutoff'])
    monkeypatch.setattr(instrument_reader,'certify_native_training_instrument',disclosed_certificate)
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_bindings as workers
    monkeypatch.setattr(workers,'execute_parameter_native_work',lambda *a,**kw:pytest.fail('source metadata entered native'))
    monkeypatch.setattr(workers,'execute_paired_response_native_work',lambda *a,**kw:pytest.fail('source metadata entered native panels'))
    execution=ExecutionSelection(4,'environment.disclosed-positive-source',
        ObjectIdentity.from_record('recursive-member.implementation',implementation_binding(ROOT)),case.plane.root.contract.canonical_path)
    specification=domain.MatrixFiniteDtSourceAssemblySpecification('assembly.disclosed-positive-source',selected.identity)
    copied=Path(case.plane.root.contract.canonical_path)/'copied-positive-source';copied.mkdir()
    spec_path=copied/'specification.json';spec_path.write_bytes(specification.canonical_bytes())
    request_path=copied/'request.json';request_path.write_bytes(selected.canonical_bytes())
    selector=ExperimentFileInputSelection('sources.disclosed-positive-source',domain.PROTOCOL_ID,
        (ExperimentInputBinding('request',selected.identity,'request.json',len(selected.canonical_bytes())),),())
    selector_path=copied/'sources.json';selector_path.write_bytes(selector.canonical_bytes())
    target=Path(case.plane.root.contract.canonical_path)/'positive-source-derived'
    kwargs=dict(specification_path=spec_path,source_selection_path=selector_path,project_root=ROOT,artifact_writer=case.plane,
        metadata_directory=target,output_selection_path=target/'sources.json',execution=execution)
    first=derive_experiment_inputs(**kwargs)
    assert first.preparation.executable and first.preparation.census.native_effect_count==0
    qualifications=first.preparation.prospective_spec.qualifications
    receipt_ids=tuple(value.receipt_id for value in qualifications)
    assert receipt_ids==tuple(sorted(set(receipt_ids)))
    assert len(qualifications)==len(first.preparation.draft.external_inputs)
    from empirical_lawhood.kernel.evidence import OutcomeAccess,VisibilityCeiling
    # Direct metadata controls stay blind; full model-bearing inputs retain
    # the disclosed original's actual irreversible exposure.
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_programme import SelectedE4PhaseBank,SelectedE4PhaseProgramme
    model_inputs=tuple(value for value in first.preparation.draft.external_inputs
        if value.payload_schema in (SelectedE4PhaseBank.SCHEMA,SelectedE4PhaseProgramme.SCHEMA))
    assert len(model_inputs)==2
    assert all((value.outcome_access,value.visibility_ceiling)==
        (OutcomeAccess.DEVELOPMENT_VISIBLE,VisibilityCeiling.DEVELOPMENT_ONLY) for value in model_inputs)
    for name in ('selection.json','authoring-base.json'):
        manifest=case.plane.read_manifest((target/name).relative_to(case.plane.root.contract.canonical_path).as_posix())
        assert manifest.logical.outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE
        assert manifest.logical.visibility_ceiling is VisibilityCeiling.DEVELOPMENT_ONLY
        assert case.original_e3.record in {value.identity for value in manifest.logical.lineage_parents}
    assert first.requirements_publication.logical.outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE
    assert first.requirements_publication.logical.visibility_ceiling is VisibilityCeiling.DEVELOPMENT_ONLY
    assert case.original_e3.record in {value.identity for value in first.requirements_publication.logical.lineage_parents}
    assert {value.source_id for value in qualifications}=={value.input_id for value in first.preparation.draft.external_inputs}
    reopened=load_experiment_inputs(first.target_specification,first.source_selection_path)
    from empirical_lawhood.adapters.methods import matrix_finite_dt_source_experiment as target_domain
    assert type(reopened.method_inputs) is target_domain.MatrixFiniteDtSourceQualificationSelection
    assert set(reopened.method_inputs.certificate.provenances)=={value.identity for value in reopened.method_inputs.bank.provenances}
    assert reopened.method_inputs.bank.reservation==case.committed.phase('e4.calibration').reservation
    assert reopened.method_inputs.bank.response_selection==case.committed.phase('e4.calibration').responses
    source.require_checked_implementation(reopened.method_inputs.certificate,reopened.method_inputs.bank)
    assert not reopened.method_inputs.certificate.instrument_checks_pass
    assert reopened.method_inputs.pipeline.assess().disposition.value=='QUALIFIED'
    assert selected.source_computability_evidence.readiness is ReadinessStatus.REQUIRES_PROTOCOL_FREEZE
    second=derive_experiment_inputs(**kwargs)
    assert second.target_specification==first.target_specification
    assert second.source_selection==first.source_selection and second.preparation==first.preparation
    from empirical_lawhood.infrastructure import authority as keys
    actual_key=case.plane.root.resolve(selected.metadata_private_key_relative_path,for_write=False)
    assert keys.Ed25519DatasetAuthorizationSigner.from_private_key_file(actual_key).verification_key_hex
