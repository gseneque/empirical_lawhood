# SPDX-License-Identifier: MPL-2.0
"""Closed full-factor metadata and fresh access controls, not real authority.

The existing exposed typed fixture supplies original locator values only.
Actual configured-E3/native-DEV/structural acquisition has its own lifecycle
control; no constructor or spy in this module establishes scientific custody.
"""
from dataclasses import replace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import full_factor_bindings as owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_followup_records import scope_reference
from empirical_lawhood.api import matrix_full_factor_access as access_owner
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactManifest, ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input
from tests.test_matrix_e4_full_factor_public import _development_access_seam, _real_plane, selected  # noqa: F401
from tests.test_matrix_e4_full_factor_values import scopes  # noqa: F401
from tests.test_matrix_selected_e4_bank_recipe import literal_recipe_source_inputs  # noqa: F401


@pytest.mark.parametrize('carrier',('source','reference','reducer'))
def test_current_carriers_refuse_omitted_original_parent_census(selected,carrier):  # noqa: F811
    reference=scope_reference(selected.scope)
    value={'source':selected.scope.sources[0],'reference':reference,
        'reducer':owner.ScheduledFullFactorReduceConfig('config.'+owner.node(reference,'reduce'),
            reference,selected.resources,reference.produced_input_parents)}[carrier]
    with pytest.raises(ValueError,match='produced-parent census'):
        replace(value,produced_input_parents=())


def test_config_parent_projection_requires_actual_shared_reducer_and_case_join(selected):  # noqa: F811
    draft=owner.lower(scope_reference(selected.scope),selected.resources,draft_id='draft.access-control',campaign=selected.campaign)
    declarations={row.capability_key:row.registration() for row in owner.operation_declarations()}
    rows=tuple((row.node_id,decode_recursive_config_input(row,declarations[row.selection.capability_key]).record)
        for row in draft.operations)
    reducer=rows[-1][1]
    case=rows[0][1]
    assert owner.config_input_parents(case,rows) is reducer.produced_input_parents
    assert owner.config_input_parents(reducer,rows) is reducer.produced_input_parents
    with pytest.raises(ValueError,match='omits.*reducer'):
        owner.config_input_parents(case,rows[:-1])
    foreign=replace(case,source=replace(case.source,group_id='group.foreign'))
    with pytest.raises(ValueError,match='source, lifecycle or selected phase budget'):
        owner.config_input_parents(foreign,rows)
    changed=replace(reducer,scope=replace(reducer.scope,record_id='reference.foreign'))
    with pytest.raises(ValueError,match='exact reducer'):
        owner.config_input_parents(reducer,(*rows[:-1],(rows[-1][0],changed)))


def test_selected_bootstrap_reads_only_exact_locator_then_returns_fresh_guard(selected,monkeypatch):  # noqa: F811
    events=[];current={'allowed':True}
    class DisclosedAccess:
        def require_current(self):
            events.append('current')
            if not current['allowed']:raise PermissionError('disclosed current grant expired')
    access=DisclosedAccess()
    def original(**kwargs):
        assert kwargs['request'] is selected.request
        events.append('actual-original-packet')
        access.require_current()
        return access,selected.evidence
    monkeypatch.setattr(access_owner,'development_original_access',original)
    def locator(key,pin,kind):
        assert key=='request' and pin==selected.specification.request and kind is type(selected.request)
        events.append('request-locator')
        return selected.request
    from empirical_lawhood.planning.experiment_inputs import ExperimentInputBinding,ExperimentInputSelection
    selection=ExperimentInputSelection('inputs.disclosed-access',
        'matrix.e4.selected-full-factor-followup.development',(ExperimentInputBinding('request',
            selected.request.identity,'request.json',len(selected.request.canonical_bytes())),))
    guard=access_owner.bootstrap_selected_input_access(specification=selected.specification,selection=selection,
        read_locator=locator,artifact_writer=object())
    assert events==['request-locator','actual-original-packet','current']
    current['allowed']=False
    with pytest.raises(PermissionError,match='expired'):guard()
    assert events[-1]=='current'


@pytest.mark.parametrize('mutation',('partial-parents','no-parents','foreign-label'))
def test_guard_refuses_foreign_member_custody_before_body_verification(selected,tmp_path,monkeypatch,mutation):  # noqa: F811
    plane=_real_plane(tmp_path/'closed-members')
    access=_development_access_seam(monkeypatch,selected,plane)
    source=selected.scope.sources[0]
    parents=source.produced_input_parents
    publication=plane.write(ArtifactWriteRequest(source.record_id,'source.json',source.SCHEMA,
        ArtifactProfile.CANONICAL_JSON,'application/json','disclosed-members','.',source.canonical_bytes(),
        source.visibility_ceiling,tuple(row.visibility_ceiling for row in parents),source.outcome_access,lineage_parents=parents))
    manifest=plane.read_manifest(publication.materialization.relative_path)
    access.require_member(manifest)
    if mutation=='partial-parents':
        changed=replace(manifest.logical,lineage_parents=parents[:-1],
            parent_visibility_ceilings=tuple(row.visibility_ceiling for row in parents[:-1]))
    elif mutation=='no-parents':
        changed=replace(manifest.logical,lineage_parents=(),parent_visibility_ceilings=(),
            outcome_access=OutcomeAccess.EVALUATION_SEALED,visibility_ceiling=VisibilityCeiling.PROSPECTIVE)
    else:
        changed=replace(manifest.logical,outcome_access=OutcomeAccess.EVALUATION_REVEALED,
            visibility_ceiling=VisibilityCeiling.OUTCOME_VISIBLE)
    # An explicitly unpublished negative envelope must reach the actual
    # member guard. The genuine publication remains immutable; retaining its
    # old member binding would reject the envelope before this access check.
    adverse=ArtifactManifest(changed,manifest.materialization)
    assert adverse.publication is None
    with pytest.raises(PermissionError,match='parent census|custody'):
        access.require_member(adverse)



def _published_original_history_file(selected_case,tmp_path,monkeypatch,*,extra_sealed=False):
    """Real publication custody over literal analytic arrays/typed history.

    Original locators and native metadata are disclosed software premises. The
    current-permission seam supplies no grant, native contact, producing receipt
    authentication, freshness or scientific qualification.
    """
    from types import SimpleNamespace
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as development
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as records
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as common
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.runtime.artifacts import ArtifactLineageParent
    from empirical_lawhood.runtime.experiment_preparation import PreparedExperimentFile
    from tests.test_matrix_e3_protected_response_science import literal_native_metadata
    from tests.test_matrix_e4_full_factor_values import _analytic_full,pin

    plane=_real_plane(tmp_path/'file-companion')
    access=_development_access_seam(monkeypatch,selected_case,plane)
    source,raw=_analytic_full(selected_case.scope.sources[0],None)
    index=selected_case.bank.source_index()
    descriptor=next(row for row in selected_case.bank.sources if row.root_id==source.root_id)
    native=records.SelectedE3E4NativeSource.from_bank(selected_case.programme,selected_case.bank,descriptor,index=index)
    history=records.SelectedE3E4FullHistory('full.'+source.root_id,source.source,
        pin('prefix.disclosed-file',records.SelectedE3E4PrefixHistory),pin('checkpoint.disclosed-file',common.ScheduledCheckpoint),
        pin('account.disclosed-file',records.SelectedE3E4AccountSeal),source.full_arrays,literal_native_metadata(native),
        source.coordinate.total_ticks,2*source.coordinate.total_ticks)
    parents=source.produced_input_parents
    ancestor=plane.write(ArtifactWriteRequest('fixture.original-input','inputs/parent.json',source.SCHEMA,
        ArtifactProfile.CANONICAL_JSON,'application/json','fixture.original-input','inputs',source.canonical_bytes(),
        source.visibility_ceiling,tuple(row.visibility_ceiling for row in parents),OutcomeAccess.EVALUATION_SEALED,lineage_parents=parents))
    # Match the scheduler's direct logical-input lineage, rather than flattening
    # the original E3 record/receipt pins into every downstream worker output.
    indirect=(ArtifactLineageParent(ObjectIdentity.from_record(ancestor.logical.logical_artifact_id,ancestor.logical),
        ancestor.logical.visibility_ceiling,ancestor.logical.outcome_access),)
    task=development.local_node(source.root_id,'continue')
    run='run.disclosed'
    prefix='runs/'+run+'/outputs/'+task
    scope='task-output-scope.'+run+'.'+task
    def request(logical,path,schema,profile,media,payload):
        return ArtifactWriteRequest(logical,path,schema,profile,media,scope,'runs/'+run,payload,
            source.visibility_ceiling,tuple(row.visibility_ceiling for row in indirect),OutcomeAccess.EVALUATION_SEALED,
            lineage_parents=indirect)
    array_request=request(source.full_arrays.array_artifact.artifact_id,prefix+'/arrays.npz',
        source.full_arrays.array_artifact.payload_schema,ArtifactProfile.MATRIX_ARRAY_NPZ,'application/x-npz',raw)
    history_request=request('artifact.'+run+'.'+task+'.product',prefix+'/product.json',history.SCHEMA,
        ArtifactProfile.CANONICAL_JSON,'application/json',history.canonical_bytes())
    requests=(array_request,history_request)
    if extra_sealed:
        requests+= (request('unselected.sealed-sibling',prefix+'/other.json',source.SCHEMA,
            ArtifactProfile.CANONICAL_JSON,'application/json',source.canonical_bytes()),)
    arrays,companion,*_=plane.write_batch(requests)
    history_pin=ObjectIdentity.from_record(history.history_id,history)
    source=replace(source,history=history_pin,original_products=tuple(
        replace(row,record=history_pin,task_id=task,publication=companion) if row.record==source.history else row
        for row in source.original_products))
    file=PreparedExperimentFile(replace(source.full_arrays.array_artifact,artifact_id=owner.array_logical(source)),
        '1.0.0',plane.root.resolve(arrays.materialization.relative_path,for_write=False),len(raw))
    state={'revoked':False};events=[]
    access_type=type(access)
    actual_current,actual_member=access_type.require_current,access_type.require_member
    def current(self,*,artifact_writer=None):
        actual_current(self,artifact_writer=artifact_writer)
        events.append('current')
        if state['revoked']:raise PermissionError('disclosed current grant revoked')
    def member(self,manifest):
        events.append(('strict-member',manifest.materialization.relative_path))
        return actual_member(self,manifest)
    monkeypatch.setattr(access_type,'require_current',current)
    monkeypatch.setattr(access_type,'require_member',member)
    return SimpleNamespace(plane=plane,access=access,source=source,file=file,arrays=arrays,companion=companion,
        history=history,array_request=array_request,history_request=history_request,state=state,events=events)


def test_original_file_authenticates_its_exact_indirect_history_companion(selected,tmp_path,monkeypatch):  # noqa: F811
    case=_published_original_history_file(selected,tmp_path,monkeypatch)
    target=case.plane.read_manifest(case.arrays.materialization.relative_path)
    companion=case.plane.read_manifest(case.companion.materialization.relative_path)
    assert target.publication==companion.publication and len(target.publication.members)==2
    original_pins={row.identity for row in case.access.parents}
    assert not any(row.identity in original_pins for row in companion.logical.lineage_parents)
    assert (companion.logical.outcome_access,companion.logical.visibility_ceiling)==(
        OutcomeAccess.EVALUATION_SEALED,VisibilityCeiling.DEVELOPMENT_ONLY)
    with pytest.raises(PermissionError,match='original E3 parent custody'):
        case.access.require_member(companion)
    case.events.clear()
    observed=access_owner.require_file_access(writer=case.plane,file=case.file,access=case.access,source=case.source)
    assert observed==target and case.events[-1]=='current'
    assert not any(type(event) is tuple for event in case.events)
    assert case.plane.root.resolve(target.materialization.relative_path,for_write=False).read_bytes()==case.array_request.payload
    assert case.plane.root.resolve(companion.materialization.relative_path,for_write=False).read_bytes()==case.history.canonical_bytes()


@pytest.mark.parametrize('damage',('file-alias','file-hash','file-bound','file-path','history-companion',
    'producer','run','batch','extra-sealed','array-bytes','history-bytes','partial-parents','relabelled-parents',
    'grant-member','grant-final'))
def test_original_file_refuses_substitution_unselected_sibling_and_later_revocation(
        selected,tmp_path,monkeypatch,damage):  # noqa: F811
    from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
    case=_published_original_history_file(selected,tmp_path,monkeypatch,extra_sealed=damage=='extra-sealed')
    source,file=case.source,case.file
    history_index=next(index for index,row in enumerate(source.original_products) if row.record==source.history)
    if damage in ('partial-parents','relabelled-parents'):
        parents=source.produced_input_parents
        if damage=='partial-parents':parents=parents[:-1]
        else:parents=tuple(replace(row,outcome_access=OutcomeAccess.EVALUATION_REVEALED,
            visibility_ceiling=VisibilityCeiling.OUTCOME_VISIBLE) for row in parents)
        source=replace(source,produced_input_parents=parents)
    elif damage=='producer':
        source=replace(source,original_products=tuple(replace(row,task_id='task.foreign') if index==history_index else row
            for index,row in enumerate(source.original_products)))
    elif damage=='run':
        source=replace(source,original_products=tuple(replace(row,run_id='run.foreign') for row in source.original_products))
    elif damage=='history-companion':
        clone=case.plane.write(replace(case.history_request,relative_path=case.history_request.relative_path+'.copy'))
        source=replace(source,original_products=tuple(replace(row,publication=clone) if index==history_index else row
            for index,row in enumerate(source.original_products)))
    # Source changes also change its legitimate FILE alias. Keep that alias exact
    # so each case reaches its own producer/parent/companion refusal.
    file=replace(file,identity=replace(file.identity,artifact_id=owner.array_logical(source)))
    if damage=='file-alias':file=replace(file,identity=replace(file.identity,artifact_id='foreign.alias'))
    elif damage=='file-hash':file=replace(file,identity=replace(file.identity,sha256='f'*64))
    elif damage=='file-bound':file=replace(file,maximum_bytes=file.maximum_bytes+1)
    elif damage=='file-path':file=replace(file,path=case.plane.root.resolve(case.companion.materialization.relative_path,for_write=False))
    elif damage=='batch':
        clone=case.plane.write(replace(case.array_request,relative_path=case.array_request.relative_path+'.copy'))
        file=replace(file,path=case.plane.root.resolve(clone.materialization.relative_path,for_write=False))
    elif damage in ('array-bytes','history-bytes'):
        publication=case.arrays if damage=='array-bytes' else case.companion
        path=case.plane.root.resolve(publication.materialization.relative_path,for_write=False)
        raw=path.read_bytes();path.write_bytes(bytes((raw[0]^1,))+raw[1:])
    actual_verify=case.plane.verify_manifest
    def verify(manifest,**kwargs):
        case.events.append('full-batch')
        if damage=='grant-member':
            before=kwargs['before_member']
            def guard(member):
                if member.materialization.relative_path==case.companion.materialization.relative_path:
                    case.state['revoked']=True
                before(member)
            kwargs['before_member']=guard
        result=actual_verify(manifest,**kwargs)
        if damage=='grant-final':case.state['revoked']=True
        return result
    monkeypatch.setattr(case.plane,'verify_manifest',verify)
    with pytest.raises((PermissionError,ValueError,ArtifactIdentityConflict)):
        access_owner.require_file_access(writer=case.plane,file=file,access=case.access,source=source)
    if damage in ('file-alias','file-hash','file-bound','file-path','history-companion','producer','run','batch',
            'partial-parents','relabelled-parents'):
        assert 'full-batch' not in case.events
    if damage=='extra-sealed':
        assert ('strict-member',case.array_request.relative_path.removesuffix('/arrays.npz')+'/other.json') in case.events
    if damage in ('grant-member','grant-final'):
        assert case.state['revoked'] and case.events[-1]=='current'
