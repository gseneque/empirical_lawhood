# SPDX-License-Identifier: MPL-2.0
"""Copied current E3 metadata controls; producer stubs are disclosed TEST inputs.

These controls create no native trajectories, genuine TRAIN custody, scientific
qualification, human proposal, issue or reveal. Production admission continues
to require the actual exporter and all four original pre-TRAIN commitments.
"""
from dataclasses import fields,replace
from hashlib import sha256
from pathlib import Path
import shutil

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_assembly as domain
from empirical_lawhood.api.configuration import validate_configuration
from empirical_lawhood.api.experiment_preparation import derive_experiment_inputs,load_experiment_inputs,load_experiment_specification,prepare_experiment
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection,ExperimentInputBinding
from tests.test_matrix_native_training_assembly import assembly_case

ROOT=Path(__file__).parents[1]
EXAMPLES=ROOT/'programmes/foundations/emergent-structure/workflows/matrix-response-experiment'


def test_copied_configured_assembly_examples_validate_and_report_real_missing_inputs(tmp_path):
    paths={}
    for role,name,consumer in (
            ('spec','configured-scientific-assembly.example.json','matrix-configured-protected-input-assembly'),
            ('request','configured-scientific-assembly.request.example.json','matrix-configured-protected-assembly-request'),
            ('sources','configured-scientific-assembly.sources.example.json','matrix-configured-protected-assembly-sources')):
        path=tmp_path/name;shutil.copyfile(EXAMPLES/name,path);paths[role]=path
        report=validate_configuration(path,consumer=consumer)
        assert report['status']=='VALIDATED' and report['authority_granted'] is False
    specification=load_experiment_specification(paths['spec'])
    inputs=load_experiment_inputs(specification,paths['sources'])
    from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
    prepared=prepare_experiment(specification,method_inputs=inputs.method_inputs,execution=ExecutionSelection(workers=4))
    assert not prepared.executable and prepared.census.native_effect_count==0
    assert 'configured-assembly.scientific-protocol' in {value.code for value in prepared.dependencies}
    assert not {'blueprint','source_profile','entry_package','formal_methods'} & {field.name for field in fields(inputs.method_inputs.request)}
    with pytest.raises(TypeError,match='exact scientific operand'):
        replace(inputs.method_inputs.request,scientific_protocol=inputs.method_inputs.request.native_training_locator.packet)
    with pytest.raises(ValueError):replace(inputs.method_inputs.request,pretrain_inputs_relative_directory='../escape')


def _case(tmp_path, *, training_count=1):
    from empirical_lawhood.adapters.methods.matrix_finite_dt_source_records import MatrixFiniteDtTrainingLocator
    from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan
    from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave
    old,native_assembly,native_request,native_spec_path,native_sources,execution=assembly_case(tmp_path, training_count=training_count)
    plane=old.plane;root=Path(plane.root.contract.canonical_path);pretrain=root/'native-derived'
    predecessor=derive_experiment_inputs(specification_path=native_spec_path,source_selection_path=native_sources,
        project_root=ROOT,artifact_writer=plane,metadata_directory=pretrain,
        output_selection_path=pretrain/'inputs/sources.json',execution=execution)
    actual=load_experiment_inputs(predecessor.target_specification,predecessor.source_selection_path).method_inputs.request
    copied=root/'configured-copied';copied.mkdir()
    declared=decode_canonical_bytes((EXAMPLES/'configured-scientific-assembly.request.example.json').read_bytes(),
        domain.ConfiguredProtectedE3AssemblyRequest,maximum_bytes=None)
    envelope=declared.computability_envelope
    coordinate=actual.protocols[0].public_source.coordinate
    compute=replace(declared.computability_evidence,
        envelope_id=envelope.envelope_id,numerical_view_ids=tuple(sorted((coordinate.primary_view.view_id,coordinate.fine_view.view_id))))
    scientific=old.programme_inputs.scientific_design.training_protocol
    mathematical=scientific.mathematical_protocol
    rule=next(value.target for value in mathematical.factor_rule_compatibilities if value.target.identity==mathematical.factor_rule)
    normalization=rule.scalar_closure.normalization_owner
    member=copied/'normalization.original.py'
    shutil.copyfile(ROOT/'src/empirical_lawhood/adapters/simulators/six_matrix_response/response_observer.py',member)
    assert (member.stat().st_size,sha256(member.read_bytes()).hexdigest())==(normalization.size_bytes,normalization.sha256)
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding
    locator=MatrixFiniteDtTrainingLocator('unexecuted/disclosed-training','run.disclosed-unexecuted-training',
        ObjectIdentity('packet.disclosed-unexecuted-training',AuthoredRecursiveWave.SCHEMA,AuthoredRecursiveWave.VERSION,'a'*64),
        ObjectIdentity('plan.disclosed-unexecuted-training',DevelopmentExecutionPlan.SCHEMA,DevelopmentExecutionPlan.VERSION,'b'*64))
    request=domain.ConfiguredProtectedE3AssemblyRequest('request.disclosed-configured-assembly','disclosed-configured-assembly',
        scientific.identity,pretrain.relative_to(root).as_posix()+'/inputs',
        locator,declared.resources,declared.authority_policy,envelope,compute,
        'operator.disclosed-assembly','banks.disclosed-configured-assembly',
        'exports/disclosed-configured-assembly',ExperimentFileInputBinding('normalization',normalization,'1.0.0',member.name,normalization.size_bytes))
    specification=domain.ConfiguredProtectedE3AssemblySpecification('assembly.disclosed-configured-assembly',request.identity)
    records=(('request',request,request.identity),('scientific-protocol',scientific,scientific.identity))
    bindings=[]
    for key,record,pin in records:
        path=copied/(key+'.json');path.write_bytes(record.canonical_bytes())
        bindings.append(ExperimentInputBinding(key,pin,path.name,path.stat().st_size))
    selected=ExperimentFileInputSelection('sources.disclosed-configured-assembly',domain.PROTOCOL_ID,tuple(bindings),())
    source_path=copied/'sources.json';source_path.write_bytes(selected.canonical_bytes())
    spec_path=copied/'specification.json';spec_path.write_bytes(specification.canonical_bytes())
    target=root/'configured-derived'
    kwargs=dict(specification_path=spec_path,source_selection_path=source_path,project_root=ROOT,artifact_writer=plane,
        metadata_directory=target,output_selection_path=target/'inputs/sources.json',execution=execution)
    return old,predecessor,actual,request,specification,kwargs


def test_public_configured_assembly_refuses_uncommitted_panels_and_changed_original_publications(tmp_path,monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as native
    from empirical_lawhood.api import native_training_banks
    from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
    old,_,actual,request,_,kwargs=_case(tmp_path)
    monkeypatch.setattr(native_training_banks,'export_native_training_banks',lambda **kw:pytest.fail('refused metadata entered TRAIN export'))
    inputs=old.plane.root.resolve(request.pretrain_inputs_relative_directory,for_write=False)
    raw=(inputs/'future-manifest-publication.json').read_bytes()
    publication=decode_canonical_bytes(raw,ArtifactWriteResult,maximum_bytes=len(raw))
    manifest=old.plane.read_manifest(publication.materialization.relative_path)
    assert manifest.publication is not None
    marker=old.plane.root.resolve(manifest.publication.commit_marker_relative_path,for_write=False)
    original=marker.read_bytes()
    try:
        marker.write_bytes(b'changed disposable TEST publication')
        with pytest.raises((ValueError,PermissionError,RuntimeError)):derive_experiment_inputs(**kwargs)
    finally:marker.write_bytes(original)
    # A current request cannot lose C or any original pre-TRAIN commitment.
    omitted={native.future_response_support(actual)[index][1] for index in range(len(native.future_response_support(actual)))}
    incomplete=replace(actual,campaign=replace(actual.campaign,evidence_state=()),
        exposure_support=tuple(row for row in actual.exposure_support if row[0] not in omitted))
    alternate=inputs.parent/'incomplete-copied';shutil.copytree(inputs,alternate)
    (alternate/'request.json').write_bytes(incomplete.canonical_bytes())
    changed=replace(request,pretrain_inputs_relative_directory=alternate.relative_to(old.plane.root.contract.canonical_path).as_posix())
    source=kwargs['source_selection_path'];selector=decode_canonical_bytes(source.read_bytes(),ExperimentFileInputSelection,maximum_bytes=None)
    selector=replace(selector,bindings=tuple(replace(row,identity=changed.identity,maximum_bytes=len(changed.canonical_bytes()))
        if row.key=='request' else row for row in selector.bindings))
    source.parent.joinpath('request.json').write_bytes(changed.canonical_bytes());source.write_bytes(selector.canonical_bytes())
    kwargs['specification_path'].write_bytes(replace(load_experiment_specification(kwargs['specification_path']),request=changed.identity).canonical_bytes())
    with pytest.raises(PermissionError,match='complete original pre-acquisition programme evidence census'):derive_experiment_inputs(**kwargs)
    assert not kwargs['metadata_directory'].exists()


@pytest.mark.parametrize('amend_primary',(False,True))
@pytest.mark.parametrize('training_count',(1,12))
def test_public_configured_assembly_real_metadata_owners_target_reopen_and_exact_replay(tmp_path,monkeypatch,amend_primary,training_count):
    """Actual metadata/formal owners with disclosed unexecuted producer I/O.

    Native products below are complete adverse TEST rows. The stub supplies no
    actual native acquisition receipts and is not genuine successful custody.
    """
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as native,native_training_acquisition as acquisition
    from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_methods import MatrixE3ViewOutcome
    from empirical_lawhood.api import native_training_banks,recursive_authoring
    from empirical_lawhood.kernel.evidence import OutcomeAccess,VisibilityCeiling
    from empirical_lawhood.runtime.artifacts import ArtifactProfile,ArtifactWriteRequest,CanonicalTaskReceipt
    from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding
    from empirical_lawhood.adapters.composition import experiment_authoring
    from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_preparation
    formal_entries=[]
    formal_entry=experiment_authoring.formal_entry
    def current_formal_entry(*args,**kwargs):
        result=formal_entry(*args,**kwargs)
        formal_entries.append(result)
        return result
    monkeypatch.setattr(experiment_authoring,'formal_entry',current_formal_entry)
    original_post=configured_protected_preparation.ConfiguredProtectedE3PreparationSelection.__post_init__
    def current_entry_only(selection):
        assert formal_entries, 'configured assembly reconstructed a prior entry/formal scaffold before compilation'
        original_post(selection)
    monkeypatch.setattr(configured_protected_preparation.ConfiguredProtectedE3PreparationSelection,'__post_init__',current_entry_only)
    old,predecessor,actual,request,_,kwargs=_case(tmp_path, training_count=training_count)
    from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
    pretrain_inputs = old.plane.root.resolve(request.pretrain_inputs_relative_directory, for_write=False)
    handle_raw = (pretrain_inputs / 'train-unit-allocation-publication.json').read_bytes()
    original_training_publication = decode_canonical_bytes(handle_raw, ArtifactWriteResult, maximum_bytes=len(handle_raw))
    assert original_training_publication.logical.outcome_access is OutcomeAccess.OUTCOME_BLIND
    assert original_training_publication.logical.visibility_ceiling is VisibilityCeiling.PROSPECTIVE
    expected_counts={'TRAIN':training_count,'CALIBRATION':20,'EVALUATION':8,'TRANSFER_NEARBY':2,'TRANSFER_SHIFTED':2}
    assert len(actual.protocols)==training_count
    assert {role:actual.candidate_specification.population(role).expected_units for role in expected_counts}==expected_counts
    amendment=None
    if amend_primary:
        from empirical_lawhood.adapters.methods.matrix_factor_response.configured_primary_amendment import MatrixE3PrimaryFamilyAmendment
        family=tuple(sorted((*actual.candidate_specification.assessment.comparison_ids,'disclosed.extra-primary-one','disclosed.extra-primary-two')))
        assessment=actual.candidate_specification.assessment
        alpha=assessment.alpha*assessment.comparison_slots/len(family)
        amendment=MatrixE3PrimaryFamilyAmendment('amendment.disclosed-configured-assembly',actual.candidate_specification,
            replace(assessment,alpha_numerator=alpha.numerator,alpha_denominator=alpha.denominator,comparison_ids=family),
            actual.identity,predecessor.target_specification.identity)
        request=replace(request,primary_amendment=amendment.identity)
        source=kwargs['source_selection_path'];selector=decode_canonical_bytes(source.read_bytes(),ExperimentFileInputSelection,maximum_bytes=None)
        path=source.parent/'primary-amendment.json';path.write_bytes(amendment.canonical_bytes())
        rows=tuple(replace(row,identity=request.identity,maximum_bytes=len(request.canonical_bytes())) if row.key=='request' else row for row in selector.bindings)
        selector=replace(selector,bindings=tuple(sorted((*rows,ExperimentInputBinding('primary-amendment',amendment.identity,path.name,path.stat().st_size)),key=lambda row:row.key)))
        source.parent.joinpath('request.json').write_bytes(request.canonical_bytes());source.write_bytes(selector.canonical_bytes())
        specification=load_experiment_specification(kwargs['specification_path'])
        kwargs['specification_path'].write_bytes(replace(specification,request=request.identity).canonical_bytes())
    seal=native.acquisition_seal(predecessor.target_specification,actual)
    features=[];outcomes=[]
    for protocol in actual.protocols:
        public=protocol.public_source
        causal=ObjectIdentity('causal.disclosed.'+public.root.root_id,native.NativeTrainingCausalPrefix.SCHEMA,'1.0.0','c'*64)
        feature=native.NativeTrainingFeature('feature.disclosed.'+public.root.root_id,public.root.independent_group_id,
            actual.identity,public.source,causal,public.root.clock_id,public.coordinate.physical_time(public.policy.cutoff_tick),
            None,'NO_CAUSAL_ORIGIN',(),(seal.identity,))
        views=tuple(MatrixE3ViewOutcome(view,(None,)*15,('UNAVAILABLE',)*15) for view in ('fine','primary'))
        outcome=native.NativeTrainingOutcome('outcome.disclosed.'+public.root.root_id,feature.unit_id,feature.source_manifest,
            feature.native_source,feature.origin,feature.clock_id,feature.cutoff,None,views,'UNEVALUABLE',(seal.identity,))
        features.append(feature);outcomes.append(outcome)
    allocation,feature_bank,outcome_bank=acquisition.export_training_banks(predecessor.target_specification,actual,
        acquisition=seal,features=tuple(features),outcomes=tuple(outcomes),record_id=request.bank_export_record_id)
    disclosed_exports = []
    def export(**selected):
        assert selected['expected_locator']==request.native_training_locator
        assert selected['directory']==old.plane.root.resolve(request.native_training_locator.authored_directory,for_write=False)
        publications=[]
        for name,record in (('allocation',allocation),('features',feature_bank),('outcomes',outcome_bank)):
            publications.append(old.plane.write(ArtifactWriteRequest(record.identity.object_id,
                request.bank_export_relative_path+'/'+name+'.json',record.SCHEMA,ArtifactProfile.CANONICAL_JSON,'application/json',
                request.bank_export_record_id,request.bank_export_relative_path,record.canonical_bytes(),
                VisibilityCeiling.DEVELOPMENT_ONLY,(),OutcomeAccess.DEVELOPMENT_VISIBLE)))
        seal_publication=old.plane.write(ArtifactWriteRequest(seal.identity.object_id,
            request.bank_export_relative_path+'/entry-seal-control.json',seal.SCHEMA,ArtifactProfile.CANONICAL_JSON,'application/json',
            request.bank_export_record_id,request.bank_export_relative_path,seal.canonical_bytes(),
            VisibilityCeiling.DEVELOPMENT_ONLY,(),OutcomeAccess.DEVELOPMENT_VISIBLE))
        disclosed_exports.append(tuple(publications))
        return native_training_banks.NativeTrainingBankExport(allocation,feature_bank,outcome_bank,tuple(publications),request.native_training_locator.run_id,seal,replace(seal_publication,created=False),
            ObjectIdentity("receipt.disclosed-configured-native-entry",CanonicalTaskReceipt.SCHEMA,CanonicalTaskReceipt.VERSION,"d"*64))
    prepared=predecessor.preparation
    instance=ExperimentInstanceBinding(predecessor.target_specification.identity,allocation.identity,
        ObjectIdentity.from_record(prepared.draft.draft_id,prepared.draft),actual.identity,
        ObjectIdentity.from_record(prepared.draft.campaign.campaign_id,prepared.draft.campaign),(actual.identity,))
    monkeypatch.setattr(native_training_banks,'export_native_training_banks',export)
    if amendment is not None:
        from empirical_lawhood.api import configured_e3_primary_amendment as amendment_api
        def disclosed_entry(writer,binding):
            assert binding.native_training_locator==request.native_training_locator
            # Same explicit unexecuted TEST producer seam as the export above.
            return amendment_api._record(writer,binding.acquisition_publication,native.NativeTrainingAcquisitionSeal)
        monkeypatch.setattr(amendment_api,'_entry_product',disclosed_entry)
    monkeypatch.setattr(recursive_authoring,'load_authored_wave',lambda **kw:(None,None,None,{'experiment-instance.json':instance.canonical_bytes()}))
    first=derive_experiment_inputs(**kwargs);second=derive_experiment_inputs(**kwargs)
    assert first.target_specification==second.target_specification==(actual.candidate_specification if amendment is None else amendment.candidate)
    assert first.source_selection==second.source_selection and first.preparation==second.preparation
    assert first.target_specification_path.read_bytes()==first.target_specification.canonical_bytes()
    loaded_inputs=load_experiment_inputs(first.target_specification,first.source_selection_path)
    loaded=loaded_inputs.method_inputs.selection
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_originals import load_protected_e3_originals
    originals = loaded.fit_config.original_publications
    assert originals.training_allocation_publication == original_training_publication
    original_manifest, original_training = load_protected_e3_originals(old.plane, originals)
    assert original_manifest == actual.future_manifest and original_training == allocation
    assert disclosed_exports
    for exported_publications in disclosed_exports:
        for publication in exported_publications:
            assert publication.logical.outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE
            assert publication.logical.visibility_ceiling is VisibilityCeiling.DEVELOPMENT_ONLY
            observed = old.plane.read_manifest(publication.materialization.relative_path)
            assert (observed.logical, observed.materialization) == (publication.logical, publication.materialization)
        assert exported_publications[0] != originals.training_allocation_publication
    assert len(loaded.training_allocation.units)==len(features)==training_count
    assert {role:len(first.preparation.allocation.unit_ids(role.lower())) for role in expected_counts}==expected_counts
    assert loaded.response_selection.root_protocols==tuple((value.public_source.root.root_id,
        ObjectIdentity.from_record(value.protocol_id,value)) for value in loaded.protocols)
    panel_records={value.panel_id:value for value in loaded.panels}
    assert {reference for _,rows in loaded.response_selection.group_panels for reference in rows}=={
        ObjectIdentity.from_record(value.panel_id,value) for value in panel_records.values()}
    assert len(loaded.source_configs)>1 and len(loaded.qualifications)==len(loaded.source_configs)
    expected=ObjectIdentity.from_record(first.target_specification.specification_id+'.measurement',first.target_specification.measurement)
    assert {row.observation_operator for row in (*loaded.qualifications,*loaded.numerical_qualifications)}=={expected}
    assert 'source-profile' not in {row.key for row in decode_canonical_bytes(
        kwargs['source_selection_path'].read_bytes(),ExperimentFileInputSelection,maximum_bytes=None).bindings}
    if amendment is not None:
        from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_preparation import ConfiguredProtectedE3PreparationSelection
        from empirical_lawhood.api.configured_e3_primary_amendment import authenticate_primary_amendment
        assert type(loaded) is ConfiguredProtectedE3PreparationSelection
        assert loaded.primary_amendment.amendment==amendment
        assert first.target_specification.calibration_alpha==actual.candidate_specification.calibration_alpha
        assert first.target_specification.measurement==actual.candidate_specification.measurement
        assert authenticate_primary_amendment(writer=old.plane,selection=loaded)==loaded.primary_amendment.identity
        def selected_binding(binding):
            old_pin=loaded.primary_amendment.identity;pin=binding.identity
            design=tuple(replace(row,object_identity=pin,materialization_sha256=pin.object_fingerprint)
                if row.object_identity==old_pin else row for row in loaded.root.design_inputs)
            root=replace(loaded.root,design_inputs=design)
            entry=replace(loaded.entry_package,checklist=replace(loaded.entry_package.checklist,
                draft=ObjectIdentity.from_record(root.draft_id,root)))
            return replace(loaded,root=root,entry_package=entry,primary_amendment=binding)
        def changed_publication(record,name):
            return old.plane.write(ArtifactWriteRequest('primary-adverse.'+name,
                request.bank_export_relative_path+'/primary-adverse-'+name+'.json',record.SCHEMA,
                ArtifactProfile.CANONICAL_JSON,'application/json',request.bank_export_record_id,
                request.bank_export_relative_path,record.canonical_bytes(),VisibilityCeiling.DEVELOPMENT_ONLY,(),OutcomeAccess.DEVELOPMENT_VISIBLE))
        binding=loaded.primary_amendment
        for changed in ('seal','reservation'):
            wrong=replace(seal,**({'candidate':replace(seal.candidate,object_fingerprint='f'*64)} if changed=='seal' else
                {'future_reservation':replace(seal.future_reservation,object_fingerprint='f'*64)}))
            wrong_binding=replace(binding,acquisition=wrong.identity,acquisition_publication=changed_publication(wrong,changed))
            with pytest.raises(PermissionError,match='native seal, source, allocation or reservation'):
                authenticate_primary_amendment(writer=old.plane,selection=selected_binding(wrong_binding))
        wrong=replace(feature_bank,acquisition=replace(feature_bank.acquisition,object_fingerprint='f'*64))
        publication=changed_publication(wrong,'bank')
        changed_binding=replace(binding,native_bank_publications=(publication,binding.native_bank_publications[1]))
        artifact=replace(loaded.training_features,artifact_id=publication.logical.logical_artifact_id,sha256=wrong.fingerprint(),size_bytes=len(wrong.canonical_bytes()))
        # Construct the consistent changed bank/reference/root together; its
        # actual acquisition identity must still refuse at the cold owner.
        old_pin=binding.identity;pin=changed_binding.identity
        root=replace(loaded.root,design_inputs=tuple(replace(row,object_identity=pin,materialization_sha256=pin.object_fingerprint)
            if row.object_identity==old_pin else row for row in loaded.root.design_inputs))
        entry=replace(loaded.entry_package,checklist=replace(loaded.entry_package.checklist,draft=ObjectIdentity.from_record(root.draft_id,root)))
        changed_selection=replace(loaded,root=root,entry_package=entry,primary_amendment=changed_binding,training_features=artifact)
        with pytest.raises(PermissionError,match='native banks substitute'):
            authenticate_primary_amendment(writer=old.plane,selection=changed_selection)
    assert all(row.logical.payload_schema for row in first.publications)
    assert loaded.source_configs==tuple(next(row for row in loaded.source_configs if row.source_id==external.input_id)
        for external in first.preparation.draft.external_inputs)
    assert {row.kind.value for row in first.preparation.dependencies}<={'AUTHORITY','SCIENTIFIC_EVIDENCE','SOFTWARE'}
    assert 'matrix.e3.resource-projection' in {row.code for row in first.preparation.dependencies}
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_preparation import bind_protected_e3_experiment_inputs
    from tests.test_matrix_e3_protected_public_lowering import assert_parallel_authority_preflight
    assert_parallel_authority_preflight(specification=first.target_specification, selection=loaded,
        files=dict(loaded_inputs.method_inputs.files), execution=kwargs['execution'],
        bind_inputs=bind_protected_e3_experiment_inputs)


def test_configured_scientific_root_preserves_actual_physical_boundary_and_causal_scope(tmp_path):
    """Declare real kernel contracts over disclosed metadata, without derive/native."""
    from empirical_lawhood.api.domain_composition.matrix_configured_protected_assembly.assembly import scientific_root
    from empirical_lawhood.kernel.evidence import OutcomeAccess
    from empirical_lawhood.kernel.experiments import validate_experiment_against_system
    from empirical_lawhood.kernel.quantities import QuantityKind
    from empirical_lawhood.kernel.systems import SystemBoundaryKind
    from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
    from tests.test_matrix_configured_protected_e3 import selected
    from tests.test_matrix_e3_protected_public_lowering import original_case

    original=original_case(tmp_path/'scientific-root-originals')
    inputs,allocation=selected(original)
    coordinate=original.protocols[0].public_source.coordinate
    envelope=original.root.system.computability_envelopes[0]
    computability=replace(original.root.experiment.obligations.computability,
        envelope_id=envelope.envelope_id,
        numerical_view_ids=tuple(sorted((coordinate.primary_view.view_id,coordinate.fine_view.view_id))))
    # Bind actual declared protocol records too: more than ten inputs exposes
    # the lexical ordering contract independently of the public wrapper.
    pins=(inputs.specification.identity,allocation.identity,
        ObjectIdentity.from_record(original.manifest.record_id,original.manifest),
        *(ObjectIdentity.from_record(value.protocol_id,value) for value in original.protocols))
    assert len(pins)>10
    metadata_cutoff=original.fit_config.fit_cutoff
    policy=original.root.system.authority_policy
    root=scientific_root(namespace='disclosed-scientific-root',candidate=inputs.specification,
        manifest=original.manifest,allocation=allocation,protocols=original.protocols,
        cutoff=metadata_cutoff,policy=policy,envelope=envelope,computability=computability,
        operator_id='operator.disclosed-root-contract',scientific_pins=pins)
    validate_experiment_against_system(root.experiment,root.system)
    assert decode_canonical_bytes(root.canonical_bytes(),type(root),maximum_bytes=None)==root
    assert root.system.authority_policy==policy and root.system.computability_envelopes==(envelope,)
    assert root.experiment.obligations.computability==computability
    assert root.system.boundary_kind is SystemBoundaryKind.OPEN_DRIVEN_DISSIPATIVE
    quantities={value.kind:value for value in root.system.quantities}
    boundary=quantities[QuantityKind.BOUNDARY]
    assert 'friction gamma='+str(coordinate.primary_view.friction_gamma) in boundary.label
    assert 'temperature='+str(coordinate.primary_view.bath_temperature) in boundary.label
    assert boundary.availability==quantities[QuantityKind.HISTORY].availability
    action=quantities[QuantityKind.ACTION].availability
    assert action.phase is CausalPhase.ACTION_REQUESTED
    assert action.outcome_access is OutcomeAccess.OUTCOME_BLIND
    assert (action.clock_id,action.available_at)==(coordinate.clock_id,
        coordinate.physical_time(inputs.specification.measurement.origin_tick))
    cutoffs=tuple(sorted((InformationCutoff('cutoff.'+value.public_source.root.root_id,
        value.public_source.coordinate.clock_id,CausalPhase.PRE_ACTION,
        value.public_source.coordinate.physical_time(value.public_source.policy.cutoff_tick))
        for value in original.protocols),key=lambda value:value.cutoff_id))
    assert root.experiment.information_cutoffs==cutoffs
    assert root.experiment.obligations.support.information_cutoff_id in {value.cutoff_id for value in cutoffs}
    for cutoff in cutoffs:
        assert cutoff.allows(quantities[QuantityKind.HISTORY].availability)
        assert not cutoff.allows(action)
        assert not cutoff.allows(quantities[QuantityKind.RECEIVER].availability)
    clocks={value.clock_id:value for value in root.system.clocks}
    for value in original.manifest.reservation.allocation.coordinates:
        assert (clocks[value.clock_id].nominal_period,clocks[value.clock_id].time_unit)==(
            value.primary_view.timestep,value.primary_view.time_unit)
    assert metadata_cutoff.clock_id in clocks
    assert all(value.information_cutoff==metadata_cutoff for value in root.design_inputs)
    assert root.design_origin.declared_input_ids==tuple(sorted(value.input_id for value in root.design_inputs))
    assert {value.object_identity for value in root.design_inputs}==set(pins)


@pytest.fixture(scope="module")
def pretrain_allocation_control(tmp_path_factory):
    # Metadata only: no TRAIN authoring, acquisition, bank output or grant.
    return _case(tmp_path_factory.mktemp("pretrain-allocation-control"), training_count=12)


@pytest.mark.parametrize("damage", ("foreign-identity", "development-handle", "changed-census",
    "foreign-blind-handle", "commit-marker"))
def test_configured_assembly_refuses_changed_pretrain_allocation_before_native_export(
        pretrain_allocation_control, monkeypatch, damage):
    from empirical_lawhood.api import native_training_banks
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as native
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, ArtifactWriteResult
    old, predecessor, actual, request, specification, kwargs = pretrain_allocation_control
    plane = old.plane
    directory = plane.root.resolve(request.pretrain_inputs_relative_directory, for_write=False)
    control = directory / 'train-unit-allocation-publication.json'
    original = decode_canonical_bytes(control.read_bytes(), ArtifactWriteResult, maximum_bytes=None)
    allocation = native.training_allocation(predecessor.target_specification, actual)
    assert len(allocation.units) == 12
    source_path = kwargs['source_selection_path']
    request_path = source_path.parent / 'request.json'
    specification_path = kwargs['specification_path']
    originals = {path: path.read_bytes() for path in (control, source_path, request_path, specification_path)}
    marker = None
    saved_marker = None
    monkeypatch.setattr(native_training_banks, 'export_native_training_banks',
        lambda **_: pytest.fail('substituted preTRAIN metadata reached native bank export'))
    try:
        if damage == 'commit-marker':
            manifest = plane.read_manifest(original.materialization.relative_path)
            assert manifest.publication is not None
            marker = plane.root.resolve(manifest.publication.commit_marker_relative_path, for_write=False)
            saved_marker = marker.read_bytes()
            marker.write_bytes(b'changed disposable TEST preTRAIN publication marker')
        else:
            access, ceiling = OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE
            changed = allocation
            if damage == 'foreign-identity':
                changed = replace(allocation, allocation_id=allocation.allocation_id[:-1] + 'z')
            elif damage == 'changed-census':
                prior = allocation.units[-1]
                unit = replace(prior, unit_id=prior.unit_id[:-3] + 'zzz')
                changed = replace(allocation, units=(*allocation.units[:-1], unit),
                    roles=tuple(replace(role, unit_id=unit.unit_id) if role.unit_id == prior.unit_id else role
                        for role in allocation.roles))
            elif damage == 'development-handle':
                access, ceiling = OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY
            changed.__post_init__()
            assert len(changed.canonical_bytes()) == len(allocation.canonical_bytes())
            if damage == 'foreign-blind-handle':
                prefix = 'adverse-pretrain-allocation/' + damage
            else:
                # Select a separate prospective TEST metadata directory. Its
                # original C/request/science copies are exact. The publication
                # occupies its owning prescribed path, so access and identity
                # adversaries reach those guards rather than the path guard.
                prefix = 'adverse-pretrain-allocation/' + damage + '/publications'
                copied = plane.root.resolve('adverse-pretrain-allocation/' + damage + '/inputs', for_write=True)
                shutil.copytree(directory, copied)
                changed_request = replace(request,
                    pretrain_inputs_relative_directory=copied.relative_to(plane.root.contract.canonical_path).as_posix())
                request_path.write_bytes(changed_request.canonical_bytes())
                selected = decode_canonical_bytes(originals[source_path], ExperimentFileInputSelection, maximum_bytes=None)
                selected = replace(selected, bindings=tuple(replace(row, identity=changed_request.identity,
                    maximum_bytes=len(changed_request.canonical_bytes())) if row.key == 'request' else row
                    for row in selected.bindings))
                source_path.write_bytes(selected.canonical_bytes())
                specification_path.write_bytes(replace(specification, request=changed_request.identity).canonical_bytes())
                control = copied / 'train-unit-allocation-publication.json'
            publication = plane.write(ArtifactWriteRequest(changed.allocation_id,
                prefix + '/train-unit-allocation.json', changed.SCHEMA, ArtifactProfile.CANONICAL_JSON,
                'application/json', 'control.pretrain-allocation.' + damage, prefix,
                changed.canonical_bytes(), ceiling, (), access))
            # This is an actual valid canonical publication, never a modified
            # ArtifactManifest carrying stale publication membership facts.
            control.write_bytes(publication.canonical_bytes())
        with pytest.raises((ValueError, PermissionError, RuntimeError)):
            derive_experiment_inputs(**kwargs)
        assert not kwargs['metadata_directory'].exists()
    finally:
        for path, raw in originals.items():
            path.write_bytes(raw)
        if marker is not None:
            marker.write_bytes(saved_marker)
