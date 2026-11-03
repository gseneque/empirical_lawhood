# SPDX-License-Identifier: MPL-2.0
"""Receipt-reconstruction software controls; no native or scientific acceptance.

Real atomic publications/locks/physical guards are used. The orchestration fixture
explicitly substitutes graph/native metadata boundaries and is not an actual TRAIN
run, replay, qualification, or whole historical-export adoption proof.
"""
from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace
import os

import pytest

from empirical_lawhood.api import native_training_export_resume as api
from empirical_lawhood.infrastructure.artifacts import (
    ArtifactIdentityConflict, ArtifactPlaneError, ExternalArtifactPlane, ExternalRootUnavailable, GuardedExternalRoot,
)
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.api.integration_artifact_profiles import integration_artifact_profile_validators
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt, ExternalRootContract, lineage_parent_sort_key
from empirical_lawhood.runtime.native_training_export import NativeTrainingExportAdoptionSelection
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding


def identity(name):
    return ObjectIdentity(name, 'empirical-lawhood/testing/reconstruction', '1.0.0', sha256(name.encode()).hexdigest())


def record(name):
    body = identity(name)
    return SimpleNamespace(identity=ObjectIdentity.from_record(name, body), SCHEMA=body.SCHEMA,
        canonical_bytes=body.canonical_bytes, fingerprint=body.fingerprint)


@pytest.fixture
def boundary(tmp_path):
    path = (tmp_path/'stock-plane').resolve(); path.mkdir()
    mount = next(value for value in (path, *path.parents) if os.path.ismount(value))
    plane = ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract('fixture.export-adoption',
        'Disclosed receipt reconstruction software controls', str(path), str(mount),
        'empirical-lawhood/testing/export-adoption', 1)), validators=integration_artifact_profile_validators())
    package = (('src/example.py', 'a'*64),)
    source = RecursiveImplementationBinding(package, sha256(canonical_json_bytes(package)).hexdigest(), 'b'*64, 'c'*40, True)
    authored = path/'authored'; authored.mkdir()
    lock = path/'runs/run.fixture/.native-execution.lock'; lock.parent.mkdir(parents=True); lock.touch()
    packet = SimpleNamespace(packet_id='packet.fixture', SCHEMA='empirical-lawhood/testing/packet', VERSION='1.0.0', fingerprint=lambda:'d'*64)
    receipts = tuple(CanonicalTaskReceipt('receipt.fixture.'+str(i), 'run.fixture', 'task.fixture.'+str(i),
        'attempt.fixture.'+str(i), 'c'*40, (), (), (), (), OperationalStatus.SUCCEEDED, ()) for i in range(3))
    plan = SimpleNamespace(execution_plan_id='plan.fixture', SCHEMA='empirical-lawhood/testing/plan', VERSION='1.0.0',
        fingerprint=lambda:'e'*64, tasks=tuple(SimpleNamespace(task_id=value.task_id) for value in receipts))
    specification = SimpleNamespace(specification_id='specification.fixture', object_id='specification.fixture', identity=identity('specification.fixture'), root_ids=('root.fixture',))
    request = SimpleNamespace(identity=identity('request.fixture'))
    acquisition = SimpleNamespace(identity=identity('acquisition.fixture'))
    references = (ObjectIdentity.from_record(packet.packet_id, packet), specification.identity, request.identity,
        acquisition.identity, *api._receipt_pins(receipts))
    parents = tuple(sorted((ArtifactLineageParent(value, VisibilityCeiling.DEVELOPMENT_ONLY,
        OutcomeAccess.DEVELOPMENT_VISIBLE) for value in set(references)), key=lineage_parent_sort_key))
    values = tuple(record('fixture.bank.'+name) for name in ('allocation','features','outcomes'))
    publications = plane.write_batch(tuple(ArtifactWriteRequest(value.identity.object_id, 'banks/'+name+'.json',
        value.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', 'fixture.banks', 'banks', value.canonical_bytes(),
        VisibilityCeiling.DEVELOPMENT_ONLY, tuple(value.visibility_ceiling for value in parents),
        OutcomeAccess.DEVELOPMENT_VISIBLE, lineage_parents=parents) for name,value in zip(('allocation','features','outcomes'),values,strict=True)))
    selection = NativeTrainingExportAdoptionSelection('selection.fixture', 'authored', 'run.fixture',
        ObjectIdentity.from_record(packet.packet_id, packet), ObjectIdentity.from_record(plan.execution_plan_id, plan),
        source, specification.identity, request.identity, 'bank.fixture', publications)
    return SimpleNamespace(plane=plane,path=path,authored=authored,lock=lock,source=source,packet=packet,plan=plan,
        specification=specification,request=request,acquisition=acquisition,receipts=receipts,parents=parents,
        values=values,publications=publications,selection=selection)


def test_selection_is_only_a_typed_original_custody_locator(boundary):
    s=boundary.selection
    assert decode_canonical_bytes(s.canonical_bytes(),type(s),maximum_bytes=None)==s
    assert not any('replay' in name or 'success' in name for name in s.__dataclass_fields__)


@pytest.mark.parametrize('damage',('missing-bank','duplicate-bank','foreign-source-type','absolute-authored','bad-run'))
def test_selection_rejects_incomplete_or_ill_typed_locators(boundary,damage):
    s=boundary.selection
    changes={'missing-bank':{'bank_publications':s.bank_publications[:-1]},
        'duplicate-bank':{'bank_publications':(s.bank_publications[0],)*3},
        'foreign-source-type':{'producer_implementation':identity('foreign')},
        'absolute-authored':{'authored_directory':'/authored'},'bad-run':{'run_id':'../run'}}
    with pytest.raises((TypeError,ValueError)):
        replace(s,**changes[damage])


@pytest.mark.parametrize('kind',('forged-generic','failed-final-scope'))
def test_generic_or_failed_scope_completion_never_authorizes_reuse(boundary,monkeypatch,kind):
    b=boundary
    raw=canonical_json_bytes({'schema':'empirical-lawhood/testing/untrusted-completion',
        'origin':kind,'replay_result_sha256':'f'*64,'state':'COMPLETED'})
    request=ArtifactWriteRequest('completion.'+kind,'completion/'+kind+'.json','empirical-lawhood/testing/untrusted-completion',
        ArtifactProfile.CANONICAL_JSON,'application/json','completion.fixture','completion',raw,
        VisibilityCeiling.DEVELOPMENT_ONLY,(),OutcomeAccess.DEVELOPMENT_VISIBLE)
    if kind=='failed-final-scope':
        original=(b.path/'banks/allocation.json').read_bytes()
        with pytest.raises(ArtifactIdentityConflict):
            with api._export_scope(b.plane) as writer:
                api._authenticate_reconstructed_banks(writer,b.publications,b.values,b.parents)
                # A dependent publication uses the ordinary writer while the
                # read-only source context retains its final mutation guard.
                publication=b.plane.write(request)
                (b.path/'banks/allocation.json').write_bytes(b'x'*len(original))
        (b.path/'banks/allocation.json').write_bytes(original)
    else:
        publication=b.plane.write(request)
    assert b.plane.root.resolve(publication.materialization.relative_path,for_write=False).exists()
    monkeypatch.setattr(api,'_source_now',lambda _:pytest.fail('untyped completion reached source/path admission'))
    with pytest.raises(TypeError,match='explicit typed receipt-bound'):
        api.adopt_native_training_bank_export(directory=b.authored,artifact_writer=b.plane,output_directory=b.path/'banks',
            record_id=b.selection.bank_record_id,selection=publication,expected_locator=object(),project_root=b.path)


def test_real_atomic_banks_authenticate_only_their_reconstructed_bytes_and_lineage(boundary):
    b=boundary
    with api._export_scope(b.plane) as writer:
        api._authenticate_reconstructed_banks(writer,b.publications,b.values,b.parents)


@pytest.mark.parametrize('damage',('body','sidecar','marker','missing','parents','reconstructed-body','split-atomic','extra-atomic-member','ancestor'))
def test_real_bank_admission_refuses_changed_physical_or_producer_custody(boundary,damage):
    from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
    b=boundary;pubs=b.publications;values=b.values;parents=b.parents
    if damage=='body':
        p=b.path/'banks/allocation.json';p.write_bytes(b'x'*p.stat().st_size);expected=ArtifactPlaneError
    elif damage=='sidecar':
        p=b.path/pubs[0].manifest_materialization.relative_path
    elif damage=='marker':
        m=decode_artifact_manifest((b.path/pubs[0].manifest_materialization.relative_path).read_bytes())
        (b.path/m.publication.commit_marker_relative_path).write_bytes(b'{}');expected=ArtifactPlaneError
    elif damage=='missing':
        (b.path/'banks/allocation.json').unlink();expected=ArtifactPlaneError
    elif damage=='parents':
        parents=();expected=PermissionError
    elif damage=='reconstructed-body':
        values=(record('fixture.foreign'),*values[1:]);expected=PermissionError
    elif damage in ('split-atomic','extra-atomic-member'):
        requests=tuple(ArtifactWriteRequest(value.identity.object_id,'changed/'+name+'.json',value.SCHEMA,
            ArtifactProfile.CANONICAL_JSON,'application/json','fixture.changed','changed',value.canonical_bytes(),
            VisibilityCeiling.DEVELOPMENT_ONLY,tuple(x.visibility_ceiling for x in parents),OutcomeAccess.DEVELOPMENT_VISIBLE,
            lineage_parents=parents) for name,value in zip(('allocation','features','outcomes'),values,strict=True))
        if damage=='split-atomic':
            pubs=tuple(b.plane.write(value) for value in requests)
        else:
            extra=record('fixture.extra')
            fourth=ArtifactWriteRequest(extra.identity.object_id,'changed/extra.json',extra.SCHEMA,ArtifactProfile.CANONICAL_JSON,
                'application/json','fixture.changed','changed',extra.canonical_bytes(),VisibilityCeiling.DEVELOPMENT_ONLY,(),OutcomeAccess.DEVELOPMENT_VISIBLE)
            pubs=b.plane.write_batch((*requests,fourth))[:3]
        expected=PermissionError
    else:
        p=b.path/'banks';p.rename(b.path/'banks-original');p.symlink_to(b.path/'banks-original',target_is_directory=True)
        expected=ExternalRootUnavailable
    if damage=='sidecar':
        p=b.path/pubs[0].manifest_materialization.relative_path;p.write_bytes(b'{}');expected=ArtifactPlaneError
    with pytest.raises(expected):
        with api._export_scope(b.plane) as writer:
            api._authenticate_reconstructed_banks(writer,pubs,values,parents)


@pytest.mark.parametrize('damage',('busy','missing','nonempty'))
def test_original_run_lock_refuses_concurrent_entry_or_absent_original_lock(boundary,damage):
    b=boundary
    if damage=='busy':
        contacts=ExternalNativeEffectContactStore(plane=b.plane,execution_plan=b.selection.execution_plan,
            visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
        with contacts.execution_lock(b.selection.run_id):
            with pytest.raises(BlockingIOError):
                with api._adoption_lock(b.plane,b.selection):
                    pytest.fail('busy original run admitted')
    else:
        if damage=='missing':b.lock.unlink()
        else:b.lock.write_bytes(b'changed')
        with pytest.raises(PermissionError,match='original existing native execution lock'):
            with api._adoption_lock(b.plane,b.selection):
                pytest.fail('invalid original lock admitted')


def test_original_lock_remains_held_through_failed_final_snapshot(boundary):
    b=boundary;events=[]
    with api._adoption_lock(b.plane,b.selection):
        with pytest.raises(ArtifactIdentityConflict):
            with api._export_scope(b.plane) as writer:
                api._authenticate_reconstructed_banks(writer,b.publications,b.values,b.parents)
                p=b.path/'banks/allocation.json';p.write_bytes(b'x'*p.stat().st_size)
        with pytest.raises(BlockingIOError):
            with api._adoption_lock(b.plane,b.selection):events.append('second-entry')
    assert events==[]


@pytest.mark.parametrize('label',('score','checkpoint'))
def test_fresh_product_decoder_uses_actual_alternate_receipt_port(tmp_path,label):
    from tests.test_native_training_bank_custody import receipted_product
    from empirical_lawhood.api.native_training_banks import _receipt_product
    plane,products,plan,task_id,expected=receipted_product.__wrapped__(tmp_path)
    old=plan.tasks[0].outputs[0]
    plan.tasks[0].outputs=(SimpleNamespace(output_id=task_id+'.'+label,
        logical_artifact_id=old.logical_artifact_id,payload_schema=old.payload_schema),)
    with pytest.raises(PermissionError,match='declared product/schema'):_receipt_product(plane,products,plan,task_id,ObjectIdentity)
    actual,receipt=_receipt_product(plane,products,plan,task_id,ObjectIdentity,label=label)
    assert actual==expected and receipt is products['receipts'][task_id]


@pytest.mark.parametrize('damage',('missing','run','task','failed','body'))
def test_actual_product_decoder_refuses_foreign_or_failed_original_receipt(tmp_path,damage):
    from tests.test_native_training_bank_custody import receipted_product
    from empirical_lawhood.api.native_training_banks import _receipt_product
    plane,products,plan,task_id,_=receipted_product.__wrapped__(tmp_path)
    receipt=products['receipts'][task_id]
    if damage=='missing':products['receipts'].clear()
    elif damage=='run':products['receipts'][task_id]=replace(receipt,run_id='run.foreign')
    elif damage=='task':products['receipts'][task_id]=replace(receipt,task_id='task.foreign')
    elif damage=='failed':products['receipts'][task_id]=replace(receipt,operational_status=OperationalStatus.FAILED,reason_codes=('disclosed-failure',))
    else:(plane.root.resolve('outputs/product.json',for_write=False)).write_bytes(b'changed')
    expected=ArtifactPlaneError if damage=='body' else PermissionError
    with pytest.raises(expected):_receipt_product(plane,products,plan,task_id,ObjectIdentity)


@pytest.fixture
def orchestration(boundary,monkeypatch):
    """Real bank/lock/final guards; disclosed compact/graph/native metadata seams."""
    from empirical_lawhood.api import native_training_banks, recursive_execution
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_acquisition
    b=boundary;draft=object();run=SimpleNamespace(run_plan_id=b.selection.run_id)
    products={'receipts':{r.task_id:r for r in b.receipts}}
    report={'status':'SUCCEEDED','run_id':b.selection.run_id,'packet_sha256':b.packet.fingerprint()}
    instance=SimpleNamespace(allocation=b.values[0].identity)
    features=(SimpleNamespace(unit_id='unit.fixture'),);outcomes=(SimpleNamespace(unit_id='unit.fixture'),)
    events=[]
    monkeypatch.setattr(api,'_source_now',lambda _:b.source)
    monkeypatch.setattr(native_training_banks,'_export_authored_preflight',lambda **_:object())
    def compact(**kw):
        assert kw['terminal_product_format']=='compact' and kw['allow_partial'] is False and kw['include_products'] is True
        events.append('complete-custody')
        return (report,products,draft,b.plan),(b.packet,draft,b.source,run,b.plan,object()),(b.specification,b.request,instance)
    monkeypatch.setattr(recursive_execution,'_read_recursive_wave_with_roots',compact)
    monkeypatch.setattr(native_training_banks,'_collect_export_records',lambda **_:(b.acquisition,b.publications[0],
        ObjectIdentity.from_record(b.receipts[0].receipt_id,b.receipts[0]),b.receipts,features,outcomes))
    def native(**kw):
        events.append('fresh-native-custody')
        return features,outcomes,lambda:events.append('final-native-custody')
    monkeypatch.setattr(api,'_authenticate_receipt_reconstruction',native)
    monkeypatch.setattr(native_training_acquisition,'export_training_banks',lambda *_,**__:b.values)
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_acquisition import entry_task_id
    def decoded_batch(*,consume,**_):
        return consume(object(),{(entry_task_id(b.specification),'product'):b.publications[0]})
    monkeypatch.setattr(api,'_consume_receipt_products',decoded_batch)
    return b,report,products,events


def adopt(b):
    return api.adopt_native_training_bank_export(directory=b.authored,artifact_writer=b.plane,
        output_directory=b.path/'banks',record_id=b.selection.bank_record_id,selection=b.selection,
        expected_locator=object(),project_root=b.path)


def test_disclosed_orchestration_has_fresh_proof_each_call_without_math(orchestration,monkeypatch):
    from empirical_lawhood.api import native_training_banks, matrix_native_acquisition_replay
    from empirical_lawhood.infrastructure import matrix_array_io
    b,_,_,events=orchestration
    def forbidden(*_,**__):pytest.fail('receipt reconstruction invoked numerical/native execution')
    monkeypatch.setattr(native_training_banks,'export_native_training_banks',forbidden)
    monkeypatch.setattr(matrix_native_acquisition_replay,'replay_root',forbidden)
    monkeypatch.setattr(matrix_array_io,'decode_matrix_arrays',forbidden)
    first=adopt(b);second=adopt(b)
    assert first.validation_origin==second.validation_origin=='RECEIPT_BOUND_BANK_RECONSTRUCTION'
    assert first.publications==b.publications and events==['complete-custody','fresh-native-custody','final-native-custody']*2
    assert not hasattr(first,'completion_publication')


@pytest.mark.parametrize('damage',('missing-winning-receipt','wrong-source','failed-census','wrong-run','wrong-terminal-packet','native-unknown','late-body','late-source'))
def test_disclosed_orchestration_refuses_before_any_value_escapes(orchestration,monkeypatch,damage):
    b,report,products,events=orchestration
    if damage=='missing-winning-receipt':products['receipts'].pop(next(iter(products['receipts'])))
    elif damage=='wrong-source':b.selection=replace(b.selection,producer_implementation=replace(b.source,observed_git_head='f'*40))
    elif damage=='failed-census':report['status']='FAILED'
    elif damage=='wrong-run':report['run_id']='run.foreign'
    elif damage=='wrong-terminal-packet':report['packet_sha256']='f'*64
    elif damage=='native-unknown':
        def refuse(**_):raise PermissionError('UNKNOWN native custody')
        monkeypatch.setattr(api,'_authenticate_receipt_reconstruction',refuse)
    elif damage=='late-body':
        original=api._authenticate_reconstructed_banks
        def late(*args):
            original(*args);p=b.path/'banks/allocation.json';p.write_bytes(b'x'*p.stat().st_size)
        monkeypatch.setattr(api,'_authenticate_reconstructed_banks',late)
    else:
        sources=iter((b.source,replace(b.source,observed_git_head='f'*40)))
        monkeypatch.setattr(api,'_source_now',lambda _:next(sources))
    expected=ArtifactIdentityConflict if damage=='late-body' else PermissionError
    escaped=[]
    with pytest.raises(expected):escaped.append(adopt(b))
    assert escaped==[]


@pytest.fixture
def batch(boundary,monkeypatch):
    """Actual receipt/product/sidecar/batch I/O; only the contract roster is literal."""
    b=boundary;tasks=[];products={'receipts':{},'outputs':{}}
    contracts=[]
    for receipt,publication in zip(b.receipts,b.publications,strict=True):
        task_id=receipt.task_id
        actual=b.plane.read_manifest(publication.materialization.relative_path)
        tasks.append(SimpleNamespace(task_id=task_id,outputs=(SimpleNamespace(output_id=task_id+'.product',
            logical_artifact_id=actual.logical.logical_artifact_id,payload_schema=ObjectIdentity.SCHEMA),)))
        products['receipts'][task_id]=replace(receipt,output_logical_artifacts=(actual.logical,),output_materializations=(actual.materialization,))
        products['outputs'][actual.logical.logical_artifact_id]=actual
        contracts.append(('literal',task_id,ObjectIdentity,'product'))
    plan=SimpleNamespace(tasks=tuple(tasks),source_plan=SimpleNamespace(object_id=b.selection.run_id))
    monkeypatch.setattr(api,'_receipt_product_contracts',lambda _:tuple(contracts))
    return b,products,plan


def test_actual_closed_product_batch_once_decodes_all_and_preserves_receipt_binding(batch,monkeypatch):
    from empirical_lawhood.infrastructure import publication_metadata
    b,products,plan=batch;seen=[];original=publication_metadata.consume_published_materializations
    def counted(plane,publications,*,consume):
        seen.append(len(publications))
        return original(plane,publications,consume=consume)
    monkeypatch.setattr(publication_metadata,'consume_published_materializations',counted)
    def consume(get,publications):
        assert len(publications)==3
        decoded=tuple(get(receipt.task_id,ObjectIdentity) for receipt in b.receipts)
        assert tuple(value[1] for value in decoded)==tuple(products['receipts'][r.task_id] for r in b.receipts)
        assert all(type(value[0]) is ObjectIdentity for value in decoded)
        return tuple(value[0] for value in decoded)
    with api._export_scope(b.plane) as writer:
        returned=api._consume_receipt_products(writer=writer,products=products,plan=plan,specification=object(),consume=consume)
    assert len(returned)==3 and seen==[3]


@pytest.mark.parametrize('damage',('missing-receipt','foreign-source-material','late-body','wrong-kind'))
def test_actual_closed_product_batch_refuses_before_callback_result_escapes(batch,damage):
    b,products,plan=batch;escaped=[];receipt=next(iter(products['receipts'].values()))
    if damage=='missing-receipt':products['receipts'].pop(receipt.task_id)
    elif damage=='foreign-source-material':
        pub=b.publications[0]
        changed=replace(pub.materialization,storage_root_id='foreign.root')
        products['receipts'][receipt.task_id]=replace(receipt,output_materializations=(changed,))
    def consume(get,publications):
        if damage=='late-body':
            p=b.path/'banks/allocation.json';p.write_bytes(b'x'*p.stat().st_size)
        elif damage=='wrong-kind':get(receipt.task_id,CanonicalTaskReceipt)
        return 'would-escape'
    expected=ArtifactIdentityConflict if damage=='late-body' else PermissionError
    with pytest.raises(expected):
        with api._export_scope(b.plane) as writer:
            value=api._consume_receipt_products(writer=writer,products=products,plan=plan,specification=object(),consume=consume)
        escaped.append(value)
    assert escaped==[]


@pytest.mark.parametrize('damage',('instance-read','registry','base-write','scoped-write','scoped-verify','scoped-stream-identity'))
def test_custom_policy_refuses_before_lock_or_path_admission(boundary,monkeypatch,damage):
    from empirical_lawhood.infrastructure.artifact_validation import ArtifactProfileValidatorRegistry
    from empirical_lawhood.infrastructure.artifacts import _ScopedArtifactPlane
    b=boundary
    if damage=='instance-read':b.plane.read_manifest=lambda *_:None
    elif damage=='registry':b.plane.validators=ArtifactProfileValidatorRegistry()
    else:
        owner=ExternalArtifactPlane if damage=='base-write' else _ScopedArtifactPlane
        method='verify' if damage=='scoped-verify' else '_stream_identity' if damage=='scoped-stream-identity' else 'write'
        monkeypatch.setattr(owner,method,lambda *_:pytest.fail('custom hook reached'))
    with pytest.raises(TypeError,match='actual stock'):
        with api._adoption_lock(b.plane,b.selection):pytest.fail('custom path admitted')


@pytest.mark.parametrize('damage',('begun','contacted'))
def test_actual_native_owner_refuses_late_nonentry_appearance_without_execution(tmp_path,damage):
    from tests.runtime_platform.test_native_subwork import _selected
    from empirical_lawhood.api.matrix_native_acquisition_replay import inspect_native
    store,definition,inputs=_selected(tmp_path)
    assert inspect_native(store=store,definition=definition,require_nonentry=True).state.value=='NOT_ENTERED'
    entry=store.begin(definition,inputs)  # Metadata control only; no runner/solver/native contact.
    if damage=='contacted':store.contact(entry)  # Exposed synthetic ledger only; no native effect.
    with pytest.raises(PermissionError,match='nonentry contradicts'):
        inspect_native(store=store,definition=definition,require_nonentry=True)


def test_final_native_inspection_refuses_late_real_store_begin_before_adoption_return(orchestration,monkeypatch,tmp_path):
    from tests.runtime_platform.test_native_subwork import _selected
    from empirical_lawhood.api.matrix_native_acquisition_replay import inspect_native
    component=tmp_path/'native-component';component.mkdir()
    store,definition,inputs=_selected(component)
    b,_,_,_=orchestration
    def native(**_):
        inspect_native(store=store,definition=definition,require_nonentry=True)
        def final():inspect_native(store=store,definition=definition,require_nonentry=True)
        # Same fixture values are required by the whole-root equality boundary.
        from empirical_lawhood.api import native_training_banks
        values=native_training_banks._collect_export_records(writer=None,products=None,plan=None,specification=None)
        return values[-2],values[-1],final
    monkeypatch.setattr(api,'_authenticate_receipt_reconstruction',native)
    original=api._authenticate_reconstructed_banks
    def late(*args):
        original(*args);store.begin(definition,inputs)
    monkeypatch.setattr(api,'_authenticate_reconstructed_banks',late)
    with pytest.raises(PermissionError,match='nonentry contradicts'):adopt(b)


@pytest.mark.parametrize('damage',('missing-root','wrong-terminal','denominator','negative-preserved'))
def test_shared_terminal_guard_preserves_whole_denominators_and_negative_states(monkeypatch,damage):
    from empirical_lawhood.api.matrix_native_training_read import _validate_complete_root_results
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as r
    spec=SimpleNamespace(specification_id='spec.fixture',identity=ObjectIdentity('spec.fixture',r.NativeTrainingAcquisitionSpecification.SCHEMA,'1.0.0','a'*64))
    seal=SimpleNamespace(identity=ObjectIdentity('seal.fixture',r.NativeTrainingAcquisitionSeal.SCHEMA,'1.0.0','b'*64))
    fs=tuple(SimpleNamespace(unit_id='unit.'+str(i),disposition='UNAVAILABLE') for i in (1,2))
    ys=tuple(SimpleNamespace(unit_id='unit.'+str(i),numerical_disposition='UNEVALUABLE') for i in (1,2))
    summary=r.NativeTrainingSummary('summary.spec.fixture',spec.identity,seal.identity,('unit.1','unit.2'),
        tuple((x.unit_id,x.disposition) for x in fs),tuple((x.unit_id,x.numerical_disposition) for x in ys))
    monkeypatch.setattr(r,'training_allocation',lambda *_:SimpleNamespace(unit_ids=lambda _:('unit.1','unit.2')))
    pairs=tuple(zip(fs,ys,strict=True));called=[]
    if damage=='missing-root':pairs=pairs[:-1]
    elif damage=='wrong-terminal':summary=replace(summary,record_id='summary.foreign')
    elif damage=='denominator':pairs=((fs[0],ys[1]),)
    def get_summary():called.append(True);return summary
    if damage=='negative-preserved':
        got=_validate_complete_root_results(spec,object(),seal,pairs,get_summary=get_summary)
        assert got==(fs,ys,summary)
    else:
        with pytest.raises(PermissionError):_validate_complete_root_results(spec,object(),seal,pairs,get_summary=get_summary)
        if damage=='denominator':assert called==[]


@pytest.mark.parametrize('root_count',(2,4))
@pytest.mark.parametrize('mutation',(False,True))
def test_existing_root_local_scopes_bound_rosters_and_guard_cross_root_mutation(boundary,root_count,mutation):
    from contextlib import ExitStack
    from empirical_lawhood.infrastructure.publication_metadata import authenticate_published_materialization
    b=boundary;publications=[]
    for i in range(root_count):
        value=record('native-control.root.'+str(i))
        publications.append(b.plane.write(ArtifactWriteRequest(value.identity.object_id,'native-controls/root.'+str(i)+'.json',
            value.SCHEMA,ArtifactProfile.CANONICAL_JSON,'application/json','native.control.root.'+str(i),'native-controls',
            value.canonical_bytes(),VisibilityCeiling.DEVELOPMENT_ONLY,(),OutcomeAccess.DEVELOPMENT_VISIBLE)))
    sizes=[];escaped=[]
    def consume():
        with api._export_scope(b.plane) as global_plane:
            api._authenticate_reconstructed_banks(global_plane,b.publications,b.values,b.parents)
            global_size=len(global_plane._read_verification.snapshots)
            with ExitStack() as scopes:
                views=[]
                for i,publication in enumerate(publications):
                    local=scopes.enter_context(global_plane.verification_scope());views.append(local)
                    authenticate_published_materialization(local,publication)
                    sizes.append(len(local._read_verification.snapshots))
                    assert len(global_plane._read_verification.snapshots)==global_size
                    if mutation and i==root_count-1:
                        path=b.path/publications[0].materialization.relative_path
                        path.write_bytes(b'x'*path.stat().st_size)
                for view in views:view.require_verification_snapshot()
            global_plane.require_verification_snapshot()
        escaped.append('complete')
    if mutation:
        with pytest.raises(ArtifactIdentityConflict):consume()
        assert escaped==[]
    else:
        consume();assert escaped==['complete']
    assert len(sizes)==root_count and len(set(sizes))==1


def test_actual_closed_batch_keeps_two_labels_from_one_producing_receipt(boundary,monkeypatch):
    b=boundary;pubs=b.publications[:2];old=b.receipts[0];task_id=old.task_id
    logicals=tuple(sorted((p.logical for p in pubs),key=lambda x:x.logical_artifact_id))
    materials=tuple(sorted((p.materialization for p in pubs),key=lambda x:x.materialization_id))
    receipt=replace(old,output_logical_artifacts=logicals,output_materializations=materials)
    labels=('checkpoint','score')
    task=SimpleNamespace(task_id=task_id,outputs=tuple(SimpleNamespace(output_id=task_id+'.'+label,
        logical_artifact_id=pub.logical.logical_artifact_id,payload_schema=ObjectIdentity.SCHEMA)
        for label,pub in zip(labels,pubs,strict=True)))
    plan=SimpleNamespace(tasks=(task,),source_plan=SimpleNamespace(object_id=old.run_id))
    products={'receipts':{task_id:receipt},'outputs':{p.logical.logical_artifact_id:b.plane.read_manifest(p.materialization.relative_path) for p in pubs}}
    monkeypatch.setattr(api,'_receipt_product_contracts',lambda _:(('literal',task_id,ObjectIdentity,'checkpoint'),('literal',task_id,ObjectIdentity,'score')))
    seen=[]
    from empirical_lawhood.kernel import decoding
    original=decoding.decode_canonical_bytes
    def counted(raw,kind,**kw):
        if kind is ObjectIdentity:seen.append(sha256(raw).hexdigest())
        return original(raw,kind,**kw)
    monkeypatch.setattr(decoding,'decode_canonical_bytes',counted)
    def consume(get,publications):
        values=tuple(get(task_id,ObjectIdentity,label) for label in labels)
        assert all(value[1] is receipt for value in values)
        assert len(publications)==2 and values[0][0]!=values[1][0]
        return tuple(value[0] for value in values)
    with api._export_scope(b.plane) as writer:
        returned=api._consume_receipt_products(writer=writer,products=products,plan=plan,specification=object(),consume=consume)
    assert len(returned)==2 and len(seen)==len(set(seen))==2


def test_actual_reconstruction_closure_reinspects_late_native_begin_with_literal_graph_seams(tmp_path,boundary,monkeypatch):
    """Actual closure+native store; domain graph/typed records are disclosed seams."""
    from contextlib import ExitStack
    from tests.runtime_platform.test_native_subwork import _selected
    from empirical_lawhood.api import matrix_native_read_custody, matrix_native_training_read, matrix_native_acquisition_replay
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as r
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_acquisition as owner
    component=tmp_path/'native-closure';component.mkdir();store,definition,inputs=_selected(component)
    spec=SimpleNamespace(root_ids=('root.fixture',),object_id='spec.fixture')
    plan=SimpleNamespace(source_plan=SimpleNamespace(object_id='run.fixture'))
    acquisition=object();feature=object();outcome=object();summary=object();events=[]
    manifest=SimpleNamespace(reservation=object(),native_specification=object(),provenances=(object(),))
    request=SimpleNamespace(train_manifest=manifest,sources=(object(),))
    source_indexes=[]
    class LiteralSourceIndex:
        def require_roster(self,sources,*,expected_root_ids):
            assert sources is request.sources and expected_root_ids==spec.root_ids
    source_index=LiteralSourceIndex()
    def build_source_index(**values):
        assert values==dict(reservation=manifest.reservation,specification=manifest.native_specification,
            provenances=manifest.provenances)
        source_indexes.append(source_index)
        return source_index
    monkeypatch.setattr(api,'ScheduledSourceIndex',SimpleNamespace(from_shared=build_source_index))
    monkeypatch.setattr(matrix_native_read_custody,'_graph',lambda *_:({},{}))
    monkeypatch.setattr(r,'acquisition_seal',lambda *_:acquisition)
    def root(*args,get,source_index,**kw):
        assert source_index is source_indexes[0]
        # Exercise the actual callback's two alternate ports as well.
        get('prefix',r.ScheduledCheckpoint,'checkpoint');get('response-score',r.NativeTrainingScore,'score')
        return object(),object(),(),{'feature':feature,'outcome':outcome}
    monkeypatch.setattr(matrix_native_training_read,'_authenticate_root_records',root)
    def reduction(*args,get_summary):
        assert get_summary() is summary
        return (feature,),(outcome,),summary
    monkeypatch.setattr(matrix_native_training_read,'_validate_complete_root_results',reduction)
    def native(**kw):
        events.append(kw['artifact_writer'])
        matrix_native_acquisition_replay.inspect_native(store=store,definition=definition,require_nonentry=True)
    monkeypatch.setattr(matrix_native_acquisition_replay,'authenticate_native_custody',native)
    reads=[]
    def get_product(task,kind,label='product'):
        reads.append((task,label))
        return (summary if task==owner.terminal_task_id(spec) else object()),object()
    with api._export_scope(boundary.plane) as writer:
        with ExitStack() as scopes:
            fs,ys,require_native=api._authenticate_receipt_reconstruction(writer=writer,specification=spec,
                request=request,draft=object(),plan=plan,products={},acquisition=acquisition,
                get_product=get_product,custody_scopes=scopes)
            assert fs==(feature,) and ys==(outcome,) and len(events)==1
            assert source_indexes==[source_index]
            assert events[0] is not writer and len(reads)==3
            store.begin(definition,inputs)
            with pytest.raises(PermissionError,match='nonentry contradicts'):require_native()
            assert len(events)==2 and events[0] is events[1]
