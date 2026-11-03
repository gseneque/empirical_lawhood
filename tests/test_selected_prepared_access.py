# SPDX-License-Identifier: MPL-2.0
"""Closed prepared-parent metadata controls, never actual authority or science.

Literal existing scientific fixtures supply canonical locators. Disclosed grant
spies exercise ordering only; actual public native acceptance is a separate gate.
"""
from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_declarative_preparation as domain
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_opportunity_bindings as owner
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_opportunity import MatrixSelectedOpportunityEvidence
from empirical_lawhood.api import selected_prepared_access as access_owner
from empirical_lawhood.kernel.evidence import OutcomeAccess,VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.experiment_inputs import ExperimentInputBinding,ExperimentInputSelection
from empirical_lawhood.runtime.artifacts import ArtifactManifest,ArtifactProfile,ArtifactWriteRequest
from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input
from tests.test_matrix_selected_opportunity import opportunity,transfer  # noqa: F401
from tests.test_matrix_selected_declarative_preparation import science,request,selection
from tests.test_recursive_public_service import _plane


@pytest.fixture
def literal(opportunity):  # noqa: F811
    specification=science(opportunity)
    selected_request=request(opportunity)
    selected=selection(specification,selected_request,opportunity)
    originals=selected_request.original_e3_products
    parents=selected_request.produced_input_parents
    return SimpleNamespace(specification=specification,request=selected_request,selected=selected,
        originals=originals,parents=parents,locators=domain.original_locator_records(selected_request))


def _access(literal,plane):
    return access_owner.SelectedPreparedOriginalInputAccess(plane,literal.originals,literal.originals,(),
        literal.parents,(),(),None)


def test_locator_roster_contains_only_current_locator_codecs_and_preserves_exact_request(literal):
    before=literal.request.canonical_bytes()
    assert tuple(key for key,_ in literal.locators)==tuple('original.'+str(index) for index in range(4))
    assert all(type(record) in domain.locator_record_types() for _,record in literal.locators)
    assert type(literal.request) not in domain.locator_record_types()
    assert type(literal.selected) not in domain.locator_record_types()
    domain.validate_locator_records(literal.request,literal.locators)
    assert literal.request.canonical_bytes()==before


@pytest.mark.parametrize('mutation',('missing','duplicate','fitted-body'))
def test_bootstrap_refuses_incomplete_or_model_bearing_locator_before_body_decoder(literal,mutation):
    bindings=tuple((key,ObjectIdentity.from_record(key,record)) for key,record in literal.locators)
    if mutation=='missing':bindings=bindings[:-1]
    elif mutation=='duplicate':bindings=(*bindings,bindings[-1])
    else:bindings=(('original.0',literal.request.identity),)
    reads=[]
    def read(key,pin,kind):
        reads.append((key,kind))
        return dict(literal.locators)[key]
    with pytest.raises(PermissionError,match='locator|roster'):
        access_owner._locator_rows(bindings,read)
    assert all(kind in domain.locator_record_types() for _,kind in reads)
    if mutation=='fitted-body':assert reads==[]


def test_replacement_changes_only_reveal_not_original_scientific_locator(literal):
    selected=tuple(replace(value,reveal_authority=replace(value.reveal_authority,
        object_id='authority.current.replacement',object_fingerprint='d'*64)) for value in literal.originals)
    current=access_owner.SelectedPreparedCurrentAccess(selected)
    original_bytes=tuple(value.canonical_bytes() for value in literal.originals)
    assert current.effective_originals(literal.originals)==selected
    foreign=replace(selected[0],prior_execution=replace(selected[0].prior_execution,run_id='run.foreign'))
    with pytest.raises(PermissionError,match='package/run/plan'):
        access_owner.SelectedPreparedCurrentAccess((foreign,*selected[1:])).effective_originals(literal.originals)
    assert tuple(value.canonical_bytes() for value in literal.originals)==original_bytes


def test_current_grant_is_refreshed_on_every_boundary_and_rebound_writer(literal,tmp_path,monkeypatch):
    plane=_plane(tmp_path/'actual-root');scope=_access(literal,plane)
    state={'allowed':True};calls=[]
    def current(entries,writer):
        assert entries==() and writer.root.contract==plane.root.contract
        calls.append(writer)
        if not state['allowed']:raise PermissionError('disclosed stored grant expired')
    from empirical_lawhood.api import recursive_qualified_parents
    monkeypatch.setattr(recursive_qualified_parents,'_require_parent_authorities_current',current)
    scope.require_current();scope.require_current(artifact_writer=plane)
    state['allowed']=False
    with pytest.raises(PermissionError,match='expired'):scope.require_current()
    assert len(calls)==3
    foreign=_plane(tmp_path/'foreign-root')
    with pytest.raises(PermissionError,match='root'):scope.require_current(artifact_writer=foreign)
    assert len(calls)==3


@pytest.mark.parametrize('mutation',('partial','absent','foreign-label'))
def test_original_member_guard_refuses_false_custody_without_reading_body(literal,tmp_path,monkeypatch,mutation):
    plane=_plane(tmp_path/'members');scope=_access(literal,plane)
    monkeypatch.setattr(access_owner.SelectedPreparedOriginalInputAccess,'require_current',lambda self,**kwargs:None)
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_access
    parents=literal.parents
    pair=produced_access(declared_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        declared_visibility=VisibilityCeiling.DEVELOPMENT_ONLY,parents=parents)
    pub=plane.write(ArtifactWriteRequest('input.model','input.json',literal.request.SCHEMA,
        ArtifactProfile.CANONICAL_JSON,'application/json','member-test','.',literal.request.canonical_bytes(),
        pair[1],tuple(row.visibility_ceiling for row in parents),pair[0],lineage_parents=parents))
    actual=plane.read_manifest(pub.materialization.relative_path)
    scope.require_member(actual)
    if mutation=='partial':logical=replace(actual.logical,lineage_parents=parents[:-1],parent_visibility_ceilings=tuple(row.visibility_ceiling for row in parents[:-1]))
    elif mutation=='absent':logical=replace(actual.logical,lineage_parents=(),parent_visibility_ceilings=(),outcome_access=OutcomeAccess.EVALUATION_SEALED,visibility_ceiling=VisibilityCeiling.PROSPECTIVE)
    else:logical=replace(actual.logical,outcome_access=OutcomeAccess.PRIVILEGED_TRUTH,visibility_ceiling=VisibilityCeiling.PRIVILEGED_TRUTH)
    adverse=ArtifactManifest(logical,actual.materialization)
    with pytest.raises(PermissionError,match='ancestry|custody'):scope.require_member(adverse)
    with pytest.raises(PermissionError,match='actual producing closure'):scope.require_issued_member(adverse)


def test_selected_request_manifest_preflight_precedes_model_body_hash(literal,tmp_path,monkeypatch):
    plane=_plane(tmp_path/'selected');scope=_access(literal,plane)
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_access
    parents=literal.parents[:-1]
    pair=produced_access(declared_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        declared_visibility=VisibilityCeiling.DEVELOPMENT_ONLY,parents=parents)
    raw=literal.request.canonical_bytes()
    plane.write(ArtifactWriteRequest('selected.request','request.json',literal.request.SCHEMA,
        ArtifactProfile.CANONICAL_JSON,'application/json','request-test','.',raw,pair[1],
        tuple(row.visibility_ceiling for row in parents),pair[0],lineage_parents=parents))
    for key,value in literal.locators:
        plane.write(ArtifactWriteRequest(key,key+'.json',value.SCHEMA,ArtifactProfile.CANONICAL_JSON,
            'application/json','locator-test','.',value.canonical_bytes(),VisibilityCeiling.PROSPECTIVE,(),OutcomeAccess.OUTCOME_BLIND))
    rows=tuple(sorted((ExperimentInputBinding('request',literal.request.identity,'request.json',len(raw)),
        *(ExperimentInputBinding(key,ObjectIdentity.from_record(key,value),key+'.json',len(value.canonical_bytes()))
            for key,value in literal.locators)),key=lambda row:row.key))
    selected=ExperimentInputSelection('selected.closed',domain.DEVELOPMENT_PROTOCOL_ID,rows)
    path=plane.root.resolve('sources.json',for_write=True);path.write_bytes(selected.canonical_bytes())
    monkeypatch.setattr(access_owner,'original_input_access',lambda **kwargs:scope)
    calls=[]
    monkeypatch.setattr(plane,'verify_manifest',lambda *args,**kwargs:calls.append(args))
    with pytest.raises(PermissionError,match='exact authenticated original parents'):
        access_owner.bootstrap_selected_input_access(specification=literal.specification,selection=selected,
            selection_path=path,artifact_writer=plane,read_locator=lambda key,pin,kind:dict(literal.locators)[key])
    assert calls==[]


def test_expiry_at_publication_verify_return_refuses_direct_body_open(literal,tmp_path,monkeypatch):
    from empirical_lawhood.kernel.status import OperationalStatus
    from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
    plane=_plane(tmp_path/'body-boundary');scope=_access(literal,plane)
    raw=b'{"schema":"empirical-lawhood/tests/literal","value":{"literal":"exposed metadata"},"version":"1.0.0"}\n'
    pub=plane.write(ArtifactWriteRequest('output.literal','output.json','empirical-lawhood/tests/literal',
        ArtifactProfile.CANONICAL_JSON,'application/json','output-test','.',raw,
        VisibilityCeiling.DEVELOPMENT_ONLY,(),OutcomeAccess.DEVELOPMENT_VISIBLE))
    receipt=CanonicalTaskReceipt('receipt.literal','run.literal','task.literal','attempt.literal','c'*40,(),
        (pub.materialization,),(pub.logical,),(),OperationalStatus.SUCCEEDED,())
    state={'allowed':True};opens=[]
    def current(self,**kwargs):
        if not state['allowed']:raise PermissionError('disclosed grant revoked during verify')
    monkeypatch.setattr(access_owner.SelectedPreparedOriginalInputAccess,'require_current',current)
    original_verify=plane.verify_manifest
    def verify(*args,**kwargs):
        original_verify(*args,**kwargs)
        state['allowed']=False
    monkeypatch.setattr(plane,'verify_manifest',verify)
    from empirical_lawhood.infrastructure import bounded_io
    monkeypatch.setattr(bounded_io,'read_bounded_bytes',lambda *args,**kwargs:opens.append(args))
    with pytest.raises(PermissionError,match='revoked during verify'):
        access_owner.guarded_output_payload(plane,receipt,pub.logical,len(raw),scope)
    assert opens==[]
    assert sha256(raw).hexdigest()==pub.logical.content_sha256


def test_every_current_config_gets_the_same_exact_committed_parent_tuple(literal):
    lowered=domain.lower(literal.specification,literal.selected)
    registrations={row.registration().selection:row.registration() for row in owner.operation_declarations()}
    records=tuple((row.node_id,decode_recursive_config_input(row,registrations[row.selection]).record)
        for row in lowered.draft.operations)
    parent_tuples=tuple(owner.config_input_parents(record,records) for _,record in records)
    assert parent_tuples and all(value is parent_tuples[0] for value in parent_tuples)
    assert parent_tuples[0]==literal.parents
    root=next(row for row in records if type(row[1]) is owner.MatrixSelectedOpportunityRootConfigV2)
    with pytest.raises(ValueError,match='omits.*entry/design'):
        owner.config_input_parents(root[1],tuple(row for row in records if row is not root))
    foreign_programme=replace(root[1].programme,record_id='public.foreign')
    foreign=replace(root[1],programme=foreign_programme,config_id='config.'+owner.global_node(foreign_programme,'design'))
    with pytest.raises(ValueError,match='foreign.*census'):
        owner.config_input_parents(foreign,records)


def test_uncommitted_evidence_remains_construction_data_without_an_execution_selection(literal):
    from tests.test_matrix_selected_opportunity import campaign_fixture
    original=literal.selected.programme
    evidence=MatrixSelectedOpportunityEvidence('evidence.literal.uncommitted',original.original_programme,literal.originals)
    assert evidence.upstream_products==literal.originals
    with pytest.raises(ValueError,match='commitment-bearing evidence'):
        owner.lower_selected_opportunity(original,evidence=evidence,
            campaign=campaign_fixture()[0].campaign,draft_id='draft.literal.uncommitted')
    with pytest.raises(ValueError,match='installed phase/version'):
        owner.capability_key('design')


def test_committed_projection_refuses_mixed_root_and_empty_census(literal):
    lowered=domain.lower(literal.specification,literal.selected)
    registrations={row.registration().selection:row.registration() for row in owner.operation_declarations()}
    records=tuple((row.node_id,decode_recursive_config_input(row,registrations[row.selection]).record)
        for row in lowered.draft.operations)
    node,root=next(row for row in records if type(row[1]) is owner.MatrixSelectedOpportunityRootConfigV2)
    foreign_programme=replace(root.programme,record_id='public.foreign')
    base=replace(root,config_id='config.'+owner.global_node(foreign_programme,'design'),programme=foreign_programme)
    mixed=tuple(sorted((*records,(owner.task_id(base),base)),key=lambda row:row[0]))
    with pytest.raises(ValueError,match='single actual committed'):
        owner.config_input_parents(root,mixed)
    with pytest.raises(ValueError,match='produced-parent census'):
        replace(root,produced_input_parents=())


def test_issued_guard_refuses_even_correct_custody_without_exact_frozen_membership(literal,tmp_path,monkeypatch):
    plane=_plane(tmp_path/'closed-issued');scope=_access(literal,plane)
    monkeypatch.setattr(access_owner.SelectedPreparedOriginalInputAccess,'require_current',lambda self,**kwargs:None)
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_access
    pair=produced_access(declared_access=OutcomeAccess.EVALUATOR_REVEAL,
        declared_visibility=VisibilityCeiling.OUTCOME_VISIBLE,parents=literal.parents)
    pub=plane.write(ArtifactWriteRequest('issued.evaluator-config','config.json',literal.request.SCHEMA,
        ArtifactProfile.CANONICAL_JSON,'application/json','closed-issued-test','.',literal.request.canonical_bytes(),
        pair[1],tuple(row.visibility_ceiling for row in literal.parents),pair[0],lineage_parents=literal.parents))
    manifest=plane.read_manifest(pub.materialization.relative_path)
    # Disclosed exact-membership seam only; actual binding is tested through the
    # prospective closed packet owner and retains every canonical pin.
    bound=replace(scope,issued_members=frozenset(((manifest.logical,manifest.materialization),)))
    bound.require_issued_member(manifest)
    foreign=ArtifactManifest(replace(manifest.logical,logical_artifact_id='foreign.same-custody'),
        replace(manifest.materialization,logical_artifact_id='foreign.same-custody'))
    with pytest.raises(PermissionError,match='actual producing closure'):bound.require_issued_member(foreign)
    with pytest.raises(PermissionError,match='actual producing closure'):scope.require_issued_member(manifest)



def test_issued_model_input_binds_exact_packet_members_not_an_access_pair(literal,transfer,tmp_path,monkeypatch):  # noqa: F811
    """Literal unissued metadata tests custody membership, not a valid issue."""
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_prepared_choices import SelectedPreparedProtectedSpecification
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_access
    from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave,RecursiveWaveMember,RecursiveImplementationBinding
    from empirical_lawhood.runtime.prospective_experiment import ProspectiveExperimentAssociation,instance_identity
    from empirical_lawhood.runtime.candidate_compiler import ExecutableStudyCandidate
    from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding
    from empirical_lawhood.kernel.serialization import canonical_json_bytes
    from tests.test_matrix_selected_protected import confirmation_case
    programme=confirmation_case(transfer)
    specification=SelectedPreparedProtectedSpecification('specification.literal.issued','ORIGINAL_E3','E5_CONFIRMATION',
        programme.point_design.expected_groups,programme.point_design.arms,programme.criterion,None,None,())
    config=literal.selected
    plane=_plane(tmp_path/'issued-packet');directory=plane.root.resolve('selected',for_write=True)
    directory.mkdir()
    scope=replace(_access(literal,plane),issued_specification=specification)
    monkeypatch.setattr(access_owner.SelectedPreparedOriginalInputAccess,'require_current',lambda self,**kwargs:None)
    draft=domain.lower(literal.specification,literal.selected).draft
    sources=(('empirical_lawhood/__init__.py','0'*64),)
    implementation=RecursiveImplementationBinding(sources,sha256(canonical_json_bytes(sources)).hexdigest(),'1'*64,'a'*40,True)
    records={'draft.json':draft,'implementation.json':implementation}
    members=tuple(RecursiveWaveMember(name,ObjectIdentity.from_record('literal.'+name.removesuffix('.json'),record),
        len(record.canonical_bytes())) for name,record in sorted(records.items()))
    by_name={row.filename:row.identity for row in members}
    packet=AuthoredRecursiveWave('packet.literal.unissued',by_name['draft.json'],by_name['implementation.json'],members)
    allocation=domain.allocation(literal.selected.programme)
    from empirical_lawhood.runtime.prospective_experiment import source_filename
    model_pin=ObjectIdentity.from_record('selection.literal.input',config)
    model_name=source_filename(model_pin)
    instance=ExperimentInstanceBinding(specification.identity,allocation.identity,packet.draft,
        ObjectIdentity('projection.literal',draft.SCHEMA,draft.VERSION,'b'*64),
        ObjectIdentity.from_record(draft.campaign.campaign_id,draft.campaign),(model_pin,))
    companions={'experiment-specification.json':specification,'experiment-allocation.json':allocation,'experiment-instance.json':instance,model_name:config}
    refs={'experiment-specification.json':specification.identity,'experiment-allocation.json':allocation.identity,
        'experiment-instance.json':instance_identity(instance),model_name:model_pin}
    companion_members=tuple(RecursiveWaveMember(name,refs[name],len(record.canonical_bytes())) for name,record in sorted(companions.items()))
    candidate=ObjectIdentity('candidate.literal.unissued',ExecutableStudyCandidate.SCHEMA,ExecutableStudyCandidate.VERSION,'a'*64)
    association=ProspectiveExperimentAssociation('association.literal.unissued',ObjectIdentity.from_record(packet.packet_id,packet),
        candidate,instance_identity(instance),companion_members)
    manifests=[]
    for lane,rows in (('prospective',{**records,'authored-wave.json':packet}),
            ('experiment',{**companions,'experiment-association.json':association})):
        for name,record in sorted(rows.items()):
            parents=literal.parents if name in ('draft.json',model_name) else ()
            pair=produced_access(declared_access=OutcomeAccess.DEVELOPMENT_VISIBLE if parents else OutcomeAccess.OUTCOME_BLIND,
                declared_visibility=VisibilityCeiling.DEVELOPMENT_ONLY if parents else VisibilityCeiling.PROSPECTIVE,parents=parents)
            relative='selected/'+lane+'/'+name
            publication=plane.write(ArtifactWriteRequest('literal.'+lane+'.'+name.removesuffix('.json'),relative,record.SCHEMA,
                ArtifactProfile.CANONICAL_JSON,'application/json','literal.'+lane,'selected/'+lane,record.canonical_bytes(),
                pair[1],tuple(row.visibility_ceiling for row in parents),pair[0],lineage_parents=parents))
            manifests.append(plane.read_manifest(publication.materialization.relative_path))
    for access,visibility in ((OutcomeAccess.OUTCOME_BLIND,VisibilityCeiling.PROSPECTIVE),
            (OutcomeAccess.DEVELOPMENT_VISIBLE,VisibilityCeiling.DEVELOPMENT_ONLY)):
        # Exact body pins/path/size remain fixed; falsely plain metadata must
        # refuse before either a model-input or graph-container body hash.
        for suffix in (model_name,'draft.json'):
            target=next(row for row in manifests if row.materialization.relative_path.endswith('/'+suffix))
            adverse=ArtifactManifest(replace(target.logical,lineage_parents=(),parent_visibility_ceilings=(),
                outcome_access=access,visibility_ceiling=visibility),target.materialization)
            changed=tuple(adverse if row is target else row for row in manifests)
            with pytest.raises(PermissionError,match='complete original ancestry'):
                scope.bind_issued_members(changed,packet=packet,association=association,directory=directory)
    bound=scope.bind_issued_members(tuple(manifests),packet=packet,association=association,directory=directory)
    evaluator=next(row for row in manifests if row.materialization.relative_path.endswith(model_name))
    bound.require_issued_member(evaluator)
    foreign=ArtifactManifest(replace(evaluator.logical,logical_artifact_id='foreign.same-custody'),
        replace(evaluator.materialization,logical_artifact_id='foreign.same-custody'))
    with pytest.raises(PermissionError,match='actual producing closure'):bound.require_issued_member(foreign)
    with pytest.raises(PermissionError,match='member census'):
        scope.bind_issued_members(tuple(manifests[:-1]),packet=packet,association=association,directory=directory)


def test_guarded_result_refuses_alien_same_parent_sealed_publication_sibling(literal,tmp_path,monkeypatch):
    import os
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_access
    from empirical_lawhood.kernel.status import OperationalStatus
    from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
    plane=_plane(tmp_path/'sibling-boundary')
    parents=tuple(replace(row,outcome_access=OutcomeAccess.EVALUATION_SEALED,
        visibility_ceiling=VisibilityCeiling.PROSPECTIVE) for row in literal.parents)
    scope=replace(_access(literal,plane),parents=parents)
    monkeypatch.setattr(access_owner.SelectedPreparedOriginalInputAccess,'require_current',lambda self,**kwargs:None)
    pair=produced_access(declared_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        declared_visibility=VisibilityCeiling.DEVELOPMENT_ONLY,parents=parents)
    raw=b'{"schema":"empirical-lawhood/tests/literal","value":{"disclosed":"not scientific outcomes"},"version":"1.0.0"}\n'
    def request(identifier,path):
        return ArtifactWriteRequest(identifier,path,'empirical-lawhood/tests/literal',ArtifactProfile.CANONICAL_JSON,
            'application/json','sibling-test','.',raw,pair[1],tuple(row.visibility_ceiling for row in parents),pair[0],lineage_parents=parents)
    alien,target=plane.write_batch((request('alien.same-parents','alien.json'),request('target.receipted','target.json')))
    alien_manifest=plane.read_manifest(alien.materialization.relative_path)
    scope.require_member(alien_manifest)  # Correct ancestry alone is insufficient.
    receipt=CanonicalTaskReceipt('receipt.sibling','run.sibling','task.sibling','attempt.sibling','c'*40,(),
        (target.materialization,),(target.logical,),(),OperationalStatus.SUCCEEDED,())
    opened=[];original_open=os.open
    def opened_path(path,*args,**kwargs):
        opened.append(str(path));return original_open(path,*args,**kwargs)
    monkeypatch.setattr(os,'open',opened_path)
    with pytest.raises(PermissionError,match='outside its exact receipt facts'):
        access_owner.guarded_output_payload(plane,receipt,target.logical,len(raw),scope)
    assert not any(path.endswith('/alien.json') or path=='alien.json' for path in opened)


@pytest.mark.parametrize('damage',('foreign-same-parent','owner-refuses','revoked'))
def test_original_dev_dispatch_requires_exact_real_owner_fact(literal,tmp_path,monkeypatch,damage):
    """A disclosed owner spy tests dispatch only, never actual DEV admission."""
    plane=_plane(tmp_path/'custody');scope=_access(literal,plane)
    pair=access_owner.produced_access(declared_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        declared_visibility=VisibilityCeiling.DEVELOPMENT_ONLY,parents=literal.parents)
    row=plane.write(ArtifactWriteRequest('artifact.disclosed.dev.result','dev-result.json',
        literal.request.SCHEMA,ArtifactProfile.CANONICAL_JSON,'application/json',
        'publication.disclosed.dev.result','.',literal.request.canonical_bytes(),pair[1],
        tuple(value.visibility_ceiling for value in literal.parents),pair[0],lineage_parents=literal.parents))
    member=plane.read_manifest(row.materialization.relative_path)
    calls=[];facts=set()
    def require_current(**kwargs):
        calls.append('current')
        if damage=='revoked':raise PermissionError('DISCLOSED_CURRENT_GRANT_REVOKED')
    monkeypatch.setattr(access_owner.SelectedPreparedOriginalInputAccess,'require_current',lambda self,**kwargs:require_current(**kwargs))
    def owner_guard(manifest):
        calls.append('actual-owner')
        if damage=='owner-refuses':raise PermissionError('DISCLOSED_ACTUAL_DEV_RECEIPT_REFUSED')
        facts.add((manifest.logical,manifest.materialization))
    owned_id='artifact.foreign' if damage=='foreign-same-parent' else member.logical.logical_artifact_id
    # This spy is a metadata dispatch test, not a constructed runtime custody.
    custody=SimpleNamespace(_original_member_facts=facts,
        plan=SimpleNamespace(tasks=(SimpleNamespace(outputs=(SimpleNamespace(logical_artifact_id=owned_id),)),)),
        require_input_member=owner_guard)
    scope=replace(scope,development_custodies=(custody,))
    with pytest.raises(PermissionError,match='foreign|RECEIPT_REFUSED|REVOKED'):
        scope.require_original_member(member)
    assert facts==set()
    if damage!='owner-refuses':assert 'actual-owner' not in calls
