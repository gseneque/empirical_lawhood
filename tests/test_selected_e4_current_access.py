# SPDX-License-Identifier: MPL-2.0
"""Replacement reveal over immutable original data; software custody controls.

Literal locators test only selection joins. Authority controls reuse the existing
actual issued software-control custody and its explicitly disclosed test grants;
they supply no scientific qualification, acquisition or real outcome authority.
"""
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_records import SelectedE4WaveLocator
from empirical_lawhood.api import matrix_full_factor_read as full_read
from empirical_lawhood.api import selected_e4_access as access
from empirical_lawhood.api import selected_e4_native_read as native_read
from empirical_lawhood.api import recursive_qualified_parents as authority
from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.study_issue import StudyOperationAuthority
from empirical_lawhood.runtime.plans import ExecutionPlan
from tests.test_current_result_custody import actual_issued_current_task_controls  # noqa: F401
from tests.test_current_result_historical_access import later_reveal
from tests.test_matrix_selected_e3_e4_bridge import selected_bridge, transfer  # noqa: F401
from tests.matrix_e4_structure_support import published_secondary


def _pin(name,kind):
    return ObjectIdentity(name,kind.SCHEMA,kind.VERSION,'a'*64)


def _literal_locator(wave='wave.a'):
    return SelectedE4WaveLocator(wave,'run.'+wave,
        ObjectIdentity('package.'+wave,'empirical-lawhood/api/experiment-package','1.0.0','b'*64),
        ObjectIdentity('issue.'+wave,'empirical-lawhood/runtime/issued-executable-study-manifest','1.0.0','c'*64),
        _pin('execution.'+wave,StudyOperationAuthority),_pin('reveal.'+wave,StudyOperationAuthority),
        _pin('plan.'+wave,ExecutionPlan))


def test_replacement_reveal_selection_changes_no_original_locator_bytes_or_identity():
    original=_literal_locator()
    before=original.canonical_bytes()
    selected=replace(original,reveal_authority=replace(original.reveal_authority,object_id='reveal.replacement'))
    current=access.SelectedE4CurrentAccess((selected,))
    current.require_originals((original,))
    binding=current.authority_binding(original)
    assert binding.reveal_authority==selected.reveal_authority
    assert (binding.issued_study,binding.execution_authority)==(original.issued_study,original.execution_authority)
    assert original.canonical_bytes()==before
    assert not hasattr(current,'canonical_bytes') and not hasattr(current,'identity')


@pytest.mark.parametrize('field',('wave_id','run_id','package','issued_study','execution_authority','execution_plan'))
def test_current_access_cannot_substitute_any_original_data_or_execution_identity(field):
    original=_literal_locator()
    previous=getattr(original,field)
    changed=previous+'.foreign' if type(previous) is str else replace(previous,object_id=previous.object_id+'.foreign')
    current=access.SelectedE4CurrentAccess((replace(original,**{field:changed}),))
    with pytest.raises(PermissionError,match='original wave|original data'):
        current.require_originals((original,))


@pytest.mark.parametrize('roster',('missing','extra','duplicate','reordered'))
def test_current_access_requires_the_complete_exact_original_wave_roster(roster):
    originals=(_literal_locator('wave.a'),_literal_locator('wave.b'))
    rows=originals[:1] if roster=='missing' else (*originals,_literal_locator('wave.c')) if roster=='extra' else \
        (originals[0],originals[0]) if roster=='duplicate' else originals[::-1]
    with pytest.raises((ValueError,PermissionError),match='original wave|per original wave'):
        access.SelectedE4CurrentAccess(rows).require_originals(originals)


def test_wave_read_threads_current_access_but_returns_original_data_after_final_guard(monkeypatch):
    original=_literal_locator()
    selected=replace(original,reveal_authority=replace(original.reveal_authority,object_id='reveal.replacement'))
    current=access.SelectedE4CurrentAccess((selected,))
    events=[]
    class Plane:
        @contextmanager
        def read_context(self):
            events.append('scope-enter')
            yield self
            events.append('scope-exit')
        def require_verification_snapshot(self):
            events.append('physical-guard')
    retained={'original-data':'unchanged'}
    def replay(**kwargs):
        assert kwargs['locator'] is original and kwargs['current_access'] is current
        events.append('original-replay')
        return retained
    def final(**kwargs):
        kwargs['current_access'].require_originals(kwargs['originals'])
        assert kwargs['originals']==(original,)
        events.append('current-access')
    monkeypatch.setattr(native_read,'_read_selected_e4_wave',replay)
    monkeypatch.setattr(access,'require_current_e4_access',final)
    assert native_read.read_selected_e4_wave(writer=Plane(),declaration=object(),locator=original,
        codecs={},current_access=current) is retained
    assert events==['scope-enter','original-replay','physical-guard','scope-exit','current-access']


class CurrentClock(datetime):
    @classmethod
    def now(cls,tz=None):
        return datetime(2030,1,1,tzinfo=UTC)


def _actual_access(f):
    package=f.control.package
    original=SelectedE4WaveLocator('wave.disclosed',package.run_plan_id,
        ObjectIdentity.from_record(package.package_id,package),
        ObjectIdentity.from_record(package.issued_study.issue_id,package.issued_study),
        ObjectIdentity.from_record(package.execution_authority.authority_id,package.execution_authority),
        ObjectIdentity.from_record(f.control.reveal.authority_id,f.control.reveal),
        ObjectIdentity.from_record(f.plan.execution_plan_id,f.plan))
    reveal=later_reveal(f)
    selected=replace(original,reveal_authority=ObjectIdentity.from_record(reveal.authority_id,reveal))
    return original,access.SelectedE4CurrentAccess((selected,)),reveal


def test_actual_stored_replacement_grant_allows_access_after_original_reveal_expiry(
        actual_issued_current_task_controls,monkeypatch):  # noqa: F811
    f=actual_issued_current_task_controls
    original,current,reveal=_actual_access(f)
    plane=f.control.service.artifact_plane
    before=original.canonical_bytes()
    monkeypatch.setattr(authority,'datetime',CurrentClock)
    with pytest.raises(PermissionError,match='expired'):
        access.require_current_e4_access(writer=plane,originals=(original,))
    loaded=[]
    load=ExternalStudyOperationAuthorityStore.load
    def observed(self,authority_id):
        loaded.append(authority_id)
        return load(self,authority_id)
    monkeypatch.setattr(ExternalStudyOperationAuthorityStore,'load',observed)
    access.require_current_e4_access(writer=plane,originals=(original,),current_access=current)
    assert reveal.authority_id in loaded and f.control.reveal.authority_id not in loaded
    assert original.canonical_bytes()==before and not f.control.executor.invocations


@pytest.mark.parametrize('failure',('expired','revoked','wrong-subject'))
def test_actual_replacement_grant_still_requires_current_valid_access(
        actual_issued_current_task_controls,monkeypatch,failure):  # noqa: F811
    f=actual_issued_current_task_controls
    original,current,reveal=_actual_access(f)
    plane=f.control.service.artifact_plane
    monkeypatch.setattr(authority,'datetime',CurrentClock)
    if failure=='revoked':
        load=ExternalStudyOperationAuthorityStore.load
        def revoked(self,authority_id):
            if authority_id==reveal.authority_id:
                raise PermissionError('stored current reveal revoked')
            return load(self,authority_id)
        monkeypatch.setattr(ExternalStudyOperationAuthorityStore,'load',revoked)
    else:
        changed=replace(reveal,authority_id=reveal.authority_id+'.refused',
            **({'expires_at_utc':'2029-01-01T00:00:00Z'} if failure=='expired' else
                {'subject':replace(reveal.subject,object_id='issued.foreign.disclosed')}))
        ExternalStudyOperationAuthorityStore(plane).persist(changed)
        current=access.SelectedE4CurrentAccess((replace(original,
            reveal_authority=ObjectIdentity.from_record(changed.authority_id,changed)),))
    with pytest.raises(PermissionError,match='expired|revoked|subject'):
        access.require_current_e4_access(writer=plane,originals=(original,),current_access=current)
    assert not f.control.executor.invocations


def test_replacement_access_is_refreshed_after_replay_and_final_physical_guard(monkeypatch):
    from empirical_lawhood.api import matrix_full_factor_runtime as runtime
    original=_literal_locator()
    current=access.SelectedE4CurrentAccess((replace(original,
        reveal_authority=replace(original.reveal_authority,object_id='reveal.replacement')),))
    events=[]
    class Plane:
        @contextmanager
        def read_context(self):
            yield self
            events.append('read-scope-closed')
        @contextmanager
        def verification_scope(self):
            yield self
        def require_verification_snapshot(self):
            events.append('physical-guard')
    def replay(**kwargs):
        assert kwargs['current_access'] is current
        events.append('replay')
        return {'retained':'original'}
    def refused(writer,scope,**kwargs):
        assert kwargs['current_access'] is current
        events.append('current-reveal-refused')
        raise PermissionError('current reveal expired during replay')
    monkeypatch.setattr(full_read,'_replay_values',replay)
    monkeypatch.setattr(runtime,'_original_grants',refused)
    with pytest.raises(PermissionError,match='expired during replay'):
        full_read._replay(writer=Plane(),specification=object(),inputs=SimpleNamespace(
            reference=SimpleNamespace(protected=True,waves=(original,))),draft=object(),plan=object(),
            receipts={},codecs={},current_access=current)
    assert events==['replay','physical-guard','read-scope-closed','current-reveal-refused']


def test_pure_runtime_refreshes_original_access_before_any_task_input_contact(monkeypatch):
    from empirical_lawhood.api import matrix_full_factor_runtime as runtime
    original=_literal_locator()
    current=access.SelectedE4CurrentAccess((original,))
    @contextmanager
    def scope():
        yield object(),SimpleNamespace(plan_reader=object())
    def forbidden(*_args,**_kwargs):
        pytest.fail('expired original access contacted protected task inputs')
    # Ordering seam only; actual stored grants are exercised above. The
    # supplier must refresh its original-input bootstrap before wave access.
    events=[]
    bound=SimpleNamespace(scope=SimpleNamespace(protected=True,waves=(original,)),current_access=current,
        configs={'task.disclosed':object()},original_custody=SimpleNamespace(original_read_scope=scope),
        original_input_access=SimpleNamespace(require_current=lambda:events.append('original-input-access')),
        custody=SimpleNamespace(current_task=forbidden))
    def refused(writer,scope,source=None,**kwargs):
        assert kwargs['current_access'] is current
        assert events==['original-input-access']
        events.append('current-reveal-refused')
        raise PermissionError('current original reveal expired before inputs')
    monkeypatch.setattr(runtime,'_original_grants',refused)
    with pytest.raises(PermissionError,match='expired before inputs'):
        runtime.ScheduledFullFactorRuntimeSupplier._prepare(bound,
            SimpleNamespace(task_id='task.disclosed'),SimpleNamespace(phase='reduce'))
    assert events==['original-input-access','current-reveal-refused']


@pytest.mark.parametrize('status',('SUCCEEDED','PARTIAL'))
def test_retained_structure_reuses_original_request_without_source_capture_or_reauthoring(tmp_path,monkeypatch,status,selected_bridge):  # noqa: F811
    """Control routing only; the stored-grant tests above own authority checks."""
    from empirical_lawhood.api import selected_e4_structure as structure
    from empirical_lawhood.api import recursive_authoring
    from empirical_lawhood.api import matrix_full_factor_derivation
    from empirical_lawhood.api import experiment_programme
    original=_literal_locator()
    before=original.canonical_bytes()
    selected=replace(original,reveal_authority=replace(original.reveal_authority,object_id='reveal.replacement'))
    target,secondary,plane=published_secondary(selected_bridge.bank,tmp_path/'early-target-custody')
    directory=Path(plane.root.contract.canonical_path)/'structure'
    (directory/'analysis').mkdir(parents=True)
    measurement=object()
    retained={'scientific_completion':'COMPLETE_ORIGINAL_FULL_FACTOR_CENSUS','new_native_contact_count':0}
    events=[]
    class Service:
        def __init__(self,**kwargs):pass
        def read(self,**kwargs):
            kwargs['read_access'].require_originals((original,))
            assert kwargs['allow_partial'] is True
            events.append('retained-status')
            return {'status':status}
        def run(self,**kwargs):
            if status=='SUCCEEDED':
                pytest.fail('completed structural stage executed')
            kwargs['read_access'].require_originals((original,))
            events.append('ordinary-pure-resume')
            return {'status':'SUCCEEDED','scientific_result':retained}
        def author(self,**kwargs):pytest.fail('completed structural stage was reauthored')
    def forbidden(*_args,**_kwargs):
        pytest.fail('completed structural stage recaptured source or rewrote original inputs')
    def companion(**kwargs):
        kwargs['current_access'].require_originals((original,))
        return None,None,SimpleNamespace(request=SimpleNamespace(waves=(original,)))
    def current(**kwargs):
        kwargs['current_access'].require_originals(kwargs['originals'])
        assert kwargs['originals']==(original,)
        events.append('current-access')
    def read(**kwargs):
        assert kwargs['waves']==(selected,)
        events.append('independent-retained-read')
        return retained
    monkeypatch.setattr(structure,'structural_measurement',lambda **kwargs:measurement)
    monkeypatch.setattr(structure,'_directory',lambda writer,path:directory)
    monkeypatch.setattr(structure,'_structural_companion',companion)
    monkeypatch.setattr(access,'require_current_e4_access',current)
    monkeypatch.setattr(recursive_authoring,'load_authored_wave',lambda **kwargs:(None,None,None,{}))
    monkeypatch.setattr(recursive_authoring,'implementation_binding',forbidden)
    monkeypatch.setattr(matrix_full_factor_derivation,'_derive_observed_input_selection',forbidden)
    monkeypatch.setattr(experiment_programme,'ExperimentProgrammeService',Service)
    monkeypatch.setattr(structure,'read_selected_e4_structure',read)
    assert structure.produce_selected_e4_structure(directory=tmp_path,artifact_writer=plane,project_root=tmp_path,
        maximum_parallel_tasks=4,programme=object(),bank=selected_bridge.bank,
        choices=SimpleNamespace(secondary_target=target),secondary_readout=secondary,
        resources=SimpleNamespace(__post_init__=lambda:None),campaign=object(),declaration=object(),
        waves=(selected,)) is retained
    assert original.canonical_bytes()==before
    assert events==['current-access','retained-status',
        'independent-retained-read' if status=='SUCCEEDED' else 'ordinary-pure-resume']


def test_authoring_guard_reloads_actual_replacement_grant_and_refuses_later_revocation(
        actual_issued_current_task_controls,monkeypatch):  # noqa: F811
    from empirical_lawhood.api.experiment_preparation import _authoring_access_guard
    f=actual_issued_current_task_controls
    original,current,reveal=_actual_access(f)
    plane=f.control.service.artifact_plane
    monkeypatch.setattr(authority,'datetime',CurrentClock)
    before=original.canonical_bytes()
    def validate(**values):
        assert values['read_access'] is current
        access.require_current_e4_access(writer=values['artifact_writer'],
            originals=(original,),current_access=values['read_access'])
    guard=_authoring_access_guard(preparation=SimpleNamespace(prospective_spec=None),
        binding=SimpleNamespace(validate_authoring_read_access=validate,
            bootstrap_prospective_input_access=None),
        artifact_writer=plane,read_access=current)
    guard()
    load=ExternalStudyOperationAuthorityStore.load
    def revoked(self,authority_id):
        if authority_id==reveal.authority_id:
            raise PermissionError('current original reveal revoked after authoring preflight')
        return load(self,authority_id)
    monkeypatch.setattr(ExternalStudyOperationAuthorityStore,'load',revoked)
    with pytest.raises(PermissionError,match='after authoring preflight'):
        guard()
    assert original.canonical_bytes()==before and not f.control.executor.invocations


def _component_access_case(monkeypatch, target_fixture, *, interrupted=None, failure='expired', wave=False,replacement=False):
    """Actual reader/typed-codec seam; literal clock and custody are not grants.

    Existing stored-grant controls above test the authority owner itself. This
    seam isolates when the component reader must refresh that owner, including
    after a heavy replay or a dependent consumer changes the current fact.
    """
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_preparation as preparation
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as records
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_programme as programme
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as original
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledSource
    from empirical_lawhood.api import recursive_operations
    from empirical_lawhood.runtime.prospective_experiment import SPECIFICATION_FILENAME

    events=[]
    state=SimpleNamespace(now=0,revoked=False,changed=False)
    def reached(stage):
        events.append(stage)
        if stage==interrupted:
            if failure=='expired':state.now=11
            elif failure=='revoked':state.revoked=True
            else:state.changed=True
    class Plane:
        def __getattr__(self,name):
            return getattr(target_fixture.secondary_plane,name)
        @contextmanager
        def verification_scope(self):
            reached('scope-enter')
            yield self
            reached('scope-exit')
        read_context=verification_scope
        def require_verification_snapshot(self):
            reached('physical-guard')
    plane=Plane()
    def record(pin,field):
        return SimpleNamespace(**{field:pin.object_id},SCHEMA=pin.object_schema,VERSION=pin.object_version,
            fingerprint=lambda:pin.object_fingerprint)
    locator=_literal_locator()
    package=record(locator.package,'package_id')
    package.issued_study=record(locator.issued_study,'issue_id')
    package.issued_study.candidate=record(ObjectIdentity('candidate.disclosed-component',
        'empirical-lawhood/testing/component-candidate','1.0.0','d'*64),'candidate_id')
    package.issued_study.source_closure=object()
    package.execution_authority=record(locator.execution_authority,'authority_id')
    package.run_plan_id=locator.run_id
    reveal_identity=replace(locator.reveal_authority,object_id='reveal.disclosed-replacement') if replacement else locator.reveal_authority
    reveal=record(reveal_identity,'authority_id')
    declaration=_pin('declaration.disclosed-component',records.SelectedE4NativeProgrammeDeclaration)
    wave_id='wave.a' if wave else None
    specification=preparation.SelectedE4NativeComponentSpecification('specification.disclosed-component',
        declaration,wave_id or preparation.ASSESSMENT_COMPONENT_ID,wave_id,'ACQUIRE_WAVE' if wave else 'ASSESS_PHASE')
    seal=records.SelectedE4ProtectedEntrySeal('seal.disclosed-component',
        _pin('programme.disclosed-component',programme.SelectedE4PhaseProgramme),
        _pin('bank.disclosed-component',programme.SelectedE4PhaseBank),
        _pin('forecast.disclosed-component',original.SelectedE3E4ForecastDesign),
        _pin('evidence.disclosed-component',records.SelectedE4ProtectedEvidence),('group.disclosed-component',),
        tuple(_pin('source.disclosed-component.'+str(i),ScheduledSource) for i in range(9)),
        'CONFIRMATION',wave_id,None if wave else _pin('waves.disclosed-component',records.SelectedE4PhaseCollectionEvidence),
        _pin('decision.disclosed-component',programme.SelectedE4PublicRevisionDecision),None,None, secondary_readout=target_fixture.secondary_readout.identity)
    logical=SimpleNamespace(payload_schema=seal.SCHEMA,logical_artifact_id='logical.disclosed-component')
    external=SimpleNamespace(logical_artifact_id='config.disclosed-component',
        expected_payload_schema=native_read.owner.SelectedE4ProtectedEntryConfig.SCHEMA)
    bank_external=SimpleNamespace(logical_artifact_id='bank.disclosed-component',expected_payload_schema=programme.SelectedE4PhaseBank.SCHEMA)
    entry_task=SimpleNamespace(task_id='task.disclosed-component.entry',external_inputs=(external,bank_external),
        capability=SimpleNamespace(capability_key=native_read.owner.NAMESPACE+'.phase-entry',
            config=SimpleNamespace(artifact_id=external.logical_artifact_id)))
    tail=SimpleNamespace(task_id='task.disclosed-component.tail',
        capability=SimpleNamespace(capability_key='matrix-selected-e4.disclosed-tail'))
    plan=record(locator.execution_plan,'execution_plan_id')
    plan.tasks=(entry_task,tail)
    package.registry=SimpleNamespace(capabilities=(tail.capability,))
    entry=SimpleNamespace(declaration=SimpleNamespace(identity=declaration),wave_id=wave_id,
        programme=SimpleNamespace(identity=seal.programme),bank=seal.bank,
        scope_group_ids=seal.groups,scope_cases=seal.sources,secondary_readout=target_fixture.secondary_readout)
    bank=SimpleNamespace(identity=seal.bank,forecast_design=SimpleNamespace(package=target_fixture.bank.forecast_design.package,
        criterion_record=target_fixture.bank.forecast_design.criterion_record),
        response_selection=target_fixture.bank.response_selection)
    selected=SimpleNamespace(payloads={SPECIFICATION_FILENAME:specification.canonical_bytes()},
        association=SimpleNamespace(candidate=native_read.r.pin(package.issued_study.candidate,'candidate_id')),
        implementation=package.issued_study.source_closure,projection=SimpleNamespace(tasks=plan.tasks))
    monkeypatch.setattr(native_read,'_actual_package',lambda *args:package)
    monkeypatch.setattr(ExternalStudyOperationAuthorityStore,'load',lambda self,authority_id:reveal)
    def issue(*args):
        reached('issue-replay')
        return package.issued_study,reveal
    monkeypatch.setattr(native_read,'_replay_parent_authority',issue)
    monkeypatch.setattr(native_read,'authenticate_current_execution_plan',lambda **kwargs:plan)
    def current(pairs,writer):
        binding,actual= pairs[0]
        assert len(pairs)==1 and actual is package and writer is plane
        assert (binding.issued_study,binding.execution_authority,binding.reveal_authority)==(
            locator.issued_study,locator.execution_authority,reveal_identity)
        reached('current-access')
        if state.revoked:raise PermissionError('disclosed current reveal revoked')
        if state.now>=10:raise PermissionError('disclosed current reveal expired')
        value=SimpleNamespace(**{**vars(reveal),'authority_id':'reveal.disclosed-foreign'}) if state.changed else reveal
        return ((package.execution_authority,value),)
    monkeypatch.setattr(native_read,'_require_parent_authorities_current',current)
    def published(writer,run_id,spec,kind):
        if spec is external:
            reached('entry-config')
            return entry
        assert spec is bank_external
        reached('bank')
        return bank
    monkeypatch.setattr(native_read,'_published_input',published)
    monkeypatch.setattr(recursive_operations,'operation_catalog',lambda:(None,None,{seal.SCHEMA:type(seal)}))
    monkeypatch.setattr(native_read,'retained_output_artifact_plane',lambda *args:plane)
    def collect(*args):
        reached('closure')
        return object()
    receipts={entry_task.task_id:SimpleNamespace(output_logical_artifacts=()),
        tail.task_id:SimpleNamespace(output_logical_artifacts=(logical,))}
    def verify(*args):
        reached('verify-payloads')
        return receipts
    def payload(*args):
        reached('protected-output')
        return seal.canonical_bytes()
    monkeypatch.setattr(authority,'_collect_receipt_closure',collect)
    monkeypatch.setattr(authority,'_verify_receipt_closure',verify)
    monkeypatch.setattr(authority,'_output_payload',payload)
    monkeypatch.setattr(native_read,'original_comparator_training',lambda value:{'scope':'disclosed-comparator'})
    def read_wave(**kwargs):
        reached('wave-replay')
        return seal,{'scope':'disclosed-wave'}
    monkeypatch.setattr(native_read,'read_selected_e4_wave',read_wave)
    callback_result=object()
    def consume(**kwargs):
        assert kwargs['products']==((seal,receipts[tail.task_id],logical),) and kwargs['reveal'] is reveal
        reached('dependent-consumer')
        return callback_result
    def read(*,callback=True):
        return native_read._read_selected_e4_component(selected=selected,artifact_writer=plane,
            run_id=locator.run_id,reveal_authority_id=reveal.authority_id,consume_tail=consume if callback else None)
    return SimpleNamespace(read=read,events=events,callback_result=callback_result,seal=seal,
        plane=plane,package=package,reveal=reveal,locator=locator,entry=entry,plan=plan,bank=bank,
        entry_task=entry_task,external=external,bank_external=bank_external,reached=reached,record=record)


def test_component_current_access_surrounds_heavy_payload_and_dependent_consumer(monkeypatch,selected_bridge):  # noqa: F811
    case=_component_access_case(monkeypatch, target_fixture=selected_bridge)
    assert case.read() is case.callback_result
    events=case.events
    assert events.count('issue-replay')==1
    assert events[events.index('verify-payloads')-1]=='current-access'
    assert events[events.index('protected-output')-1]=='current-access'
    assert events[events.index('dependent-consumer')-1]=='current-access'
    assert events[-3:]==['physical-guard','scope-exit','current-access']


@pytest.mark.parametrize('interrupted',('closure','verify-payloads','protected-output','dependent-consumer','scope-exit'))
@pytest.mark.parametrize('failure',('expired','revoked','changed'))
def test_component_refuses_access_changes_during_replay_or_callback(monkeypatch,interrupted,failure,selected_bridge):  # noqa: F811
    case=_component_access_case(monkeypatch,interrupted=interrupted,failure=failure, target_fixture=selected_bridge)
    with pytest.raises(PermissionError,match='expired|revoked|current reveal changed'):
        case.read()
    assert case.events.count('issue-replay')==1
    if interrupted in ('closure','verify-payloads','protected-output'):
        assert 'dependent-consumer' not in case.events
    if interrupted=='closure':
        assert 'verify-payloads' not in case.events and 'protected-output' not in case.events
    if interrupted=='verify-payloads':
        assert 'protected-output' not in case.events


@pytest.mark.parametrize('route',('normal-tail','wave'))
@pytest.mark.parametrize('failure',('expired','revoked','changed'))
def test_component_normal_and_wave_returns_refresh_current_access(monkeypatch,route,failure,selected_bridge):  # noqa: F811
    case=_component_access_case(monkeypatch,interrupted='bank' if route=='normal-tail' else 'wave-replay',
        failure=failure,wave=route=='wave', target_fixture=selected_bridge)
    with pytest.raises(PermissionError,match='expired|revoked|current reveal changed'):
        case.read(callback=False)
    assert 'dependent-consumer' not in case.events and case.events.count('issue-replay')==1


def _inner_wave_access_case(monkeypatch, target_fixture, *, interrupted=None,failure='expired'):
    """Real inner projection of nine missing cases; custody/clock remain spies."""
    from pathlib import Path
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_protocol import NativeTrainingScientificProtocol
    from empirical_lawhood.api import selected_e4_native_runtime
    from empirical_lawhood.kernel.authority import ResourceBudget

    case=_component_access_case(monkeypatch,target_fixture,interrupted=interrupted,failure=failure,wave=True,replacement=True)
    root=Path(__file__).parents[1]
    coordinate=decode_canonical_bytes((root/'programmes/foundations/emergent-structure/workflows/matrix-response-experiment/native-training-scientific-protocol.example.json').read_bytes(),
        NativeTrainingScientificProtocol,maximum_bytes=None).coordinates[0]
    roots=tuple(SimpleNamespace(root_id='root.disclosed-inner.'+str(i),source=source,
        independent_group_id=case.seal.groups[0]) for i,source in enumerate(case.seal.sources))
    wave=SimpleNamespace(root_ids=tuple(row.root_id for row in roots),group_ids=case.seal.groups)
    budget=ResourceBudget(1,None,0,None,None,None)
    entry_task=case.entry_task
    entry_task.capability.capability_key=native_read.owner.NAMESPACE+'.entry'
    entry_task.capability.capability_version='2.0.0'
    entry_task.capability.capability_implementation_sha256='a'*64
    entry_task.capability.config.config_schema=native_read.owner.SelectedE4ProtectedEntryConfig.SCHEMA
    prefix=SimpleNamespace(task_id='task.disclosed-inner.prefix',capability=SimpleNamespace(
        capability_key=native_read.owner.NAMESPACE+'.prefix',capability_version='3.0.0',
        capability_implementation_sha256='a'*64,config=SimpleNamespace(config_schema='empirical-lawhood/testing/inner-prefix-config')))
    case.plan.tasks=(entry_task,prefix)
    configs=[]
    manifests={}
    for task,phase in ((entry_task,'entry'),(prefix,'prefix')):
        task.capability_implementation_sha256='a'*64
        config=SimpleNamespace(phase=phase,SCHEMA=task.capability.config.config_schema,fingerprint=lambda:'b'*64)
        task.capability.config.config_schema_sha256='c'*64
        task.capability.config.content_sha256=config.fingerprint()
        task.capability.requested_resources=budget
        task.capability.requested_outcome_access=native_read.owner.access(phase)
        manifest=SimpleNamespace(capability_key=task.capability.capability_key,
            capability_version=task.capability.capability_version,config_schema=config.SCHEMA,
            config_schema_sha256='c'*64,implementation_sha256='a'*64)
        manifests[config.phase]=manifest
        configs.append((task.task_id,config))
    case.package.registry=SimpleNamespace(resolve=lambda key,version:next(value for value in manifests.values()
        if (value.capability_key,value.capability_version)==(key,version)))
    case.package.scientific_approval=case.record(ObjectIdentity('approval.disclosed-inner',
        'empirical-lawhood/testing/approval','1.0.0','d'*64),'authorization_id')
    declaration=SimpleNamespace(identity=case.entry.declaration.identity,bank=case.bank.identity,
        __post_init__=lambda:None,wave=lambda wave_id:wave,
        planned_task_budgets=tuple((task.task_id,budget) for task in case.plan.tasks),
        programme=SimpleNamespace(cases=roots))
    case.entry.declaration=declaration
    for name in ('programme','evidence','evidence_size_bytes','decision','models','calibration','declaration_publication'):
        if not hasattr(case.entry,name):setattr(case.entry,name,None)
    case.entry.programme.cases=roots
    source_index=object()
    case.bank.source_index=lambda:source_index
    resolved=[]
    def source(root_id,*,index):
        assert index is source_index, 'incomplete wave passed recovery metadata as its scientific source index'
        resolved.append(root_id)
        if len(resolved)==len(roots):case.reached('last-source')
        return SimpleNamespace(coordinate=coordinate)
    case.bank.source=source
    monkeypatch.setattr(selected_e4_native_runtime,'require_selected_e4_native_plan_budget',lambda **kwargs:None)
    monkeypatch.setattr(native_read.owner,'contracts',lambda *args,**kwargs:(tuple(configs),(),(),None,None))
    monkeypatch.setattr(native_read.owner,'declaration_for_config',lambda config:manifests[config.phase])
    monkeypatch.setattr(native_read,'_require_wave_graph',lambda *args:None)
    recovery=SimpleNamespace(index_relative_path='disclosed-inner/recovery.json',SCHEMA='empirical-lawhood/testing/recovery-index')
    monkeypatch.setattr(native_read,'build_run_recovery_index',lambda *args,**kwargs:recovery)
    class Recovery:
        def __init__(self,writer):assert writer is case.plane
        def read_index(self,*args,**kwargs):
            case.reached('recovery')
            return recovery
    monkeypatch.setattr(native_read,'ExternalRunRecoveryStore',Recovery)
    def plan(**kwargs):
        case.reached('plan')
        return case.plan
    monkeypatch.setattr(native_read,'authenticate_current_execution_plan',plan)
    def inputs(writer,*args,require_current,**kwargs):
        require_current(writer)
        case.reached('protected-inputs')
        return ()
    monkeypatch.setattr(native_read,'_inputs',inputs)
    terminal=case.record(ObjectIdentity('terminal.disclosed-inner',
        'empirical-lawhood/runtime/run-recovery-terminal-event','1.0.0','e'*64),'terminal_event_id')
    terminal.operational_status='FAILED'
    products={'terminal':terminal,'dispositions':tuple({'task_id':task.task_id,'operational_status':'FAILED'}
        for task in case.plan.tasks),'product_index':[],'outputs':{},'receipts':{},'recovery_events':{}}
    from empirical_lawhood.api import recursive_execution
    selected_policy=object()
    monkeypatch.setattr(recursive_execution,'_read_only_custody_policy',lambda writer:selected_policy)
    def product_pass(**kwargs):
        assert kwargs['index'] is recovery and kwargs['_read_policy'] is selected_policy
        case.reached('product-pass')
        return products
    monkeypatch.setattr(native_read,'read_execution_products',product_pass)
    def missing_record(writer,*args,require_current):
        require_current(writer)
        case.reached('typed-product')
        return None
    monkeypatch.setattr(native_read,'_record',missing_record)
    def native_products(writer,*args,require_current,**kwargs):
        require_current(writer)
        return {phase:None for phase in ('prefix','project','account','mechanical','continue','responses')}
    monkeypatch.setattr(native_read,'_native_case_products',native_products)
    current=access.SelectedE4CurrentAccess((replace(case.locator,
        reveal_authority=native_read.r.pin(case.reveal,'authority_id')),))
    def consume(**kwargs):
        assert len(kwargs['cases'])==9
        case.reached('dependent-consumer')
    def read():
        return native_read._read_selected_e4_wave(writer=case.plane,declaration=declaration,locator=case.locator,
            codecs={},current_access=current,_consume_original=consume)
    return SimpleNamespace(read=read,events=case.events,resolved=resolved,roots=roots)


def test_inner_wave_retains_all_missing_cases_and_uses_the_scientific_source_index(monkeypatch,selected_bridge):  # noqa: F811
    case=_inner_wave_access_case(monkeypatch, target_fixture=selected_bridge)
    result,state=case.read()
    assert tuple(row.root_id for row in result.cases)==tuple(row.root_id for row in case.roots)==tuple(case.resolved)
    assert len(result.cases)==9 and state['terminal']=='FAILED'
    assert all(row.disposition=='UNKNOWN' and row.paired_log_targets==(None,)*30 and not row.ordinary_receipts
        for row in result.cases)
    assert case.events.count('issue-replay')==1
    assert case.events[case.events.index('protected-inputs')-1]=='current-access'
    assert case.events[case.events.index('dependent-consumer')-1]=='current-access'
    assert case.events[-1]=='current-access'


@pytest.mark.parametrize('interrupted',('plan','recovery','product-pass','last-source','dependent-consumer'))
@pytest.mark.parametrize('failure',('expired','revoked','changed'))
def test_inner_wave_refuses_changed_current_replacement_access_before_payload_or_consumer(monkeypatch,interrupted,failure,selected_bridge):  # noqa: F811
    case=_inner_wave_access_case(monkeypatch,interrupted=interrupted,failure=failure, target_fixture=selected_bridge)
    with pytest.raises(PermissionError,match='expired|revoked|current reveal changed'):
        case.read()
    assert case.events.count('issue-replay')==1
    if interrupted=='plan':
        assert 'entry-config' not in case.events
    if interrupted in ('plan','recovery'):
        assert 'protected-inputs' not in case.events
    if interrupted=='product-pass':
        assert 'typed-product' not in case.events
    if interrupted!='dependent-consumer':
        assert 'dependent-consumer' not in case.events
