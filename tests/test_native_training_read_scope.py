# SPDX-License-Identifier: MPL-2.0
"""Disclosed control membership only; no TRAIN/qualification/native science.

Real artifact/contact/subwork/receipt stores retain literal software returns.
These controls do not claim a complete scientific TRAIN run. The public TRAIN
scope still needs its actual current retained-run integration acceptance.
"""
from dataclasses import replace
from pathlib import Path

import pytest

from empirical_lawhood.api.native_training_read_scope import (
    NativeTrainingReadScope, _Metadata, authenticated_native_training_read_scope,
)
from empirical_lawhood.infrastructure import artifacts
from empirical_lawhood.infrastructure.artifact_validation import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore, NativeSubworkMetadata
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from tests.runtime_platform.test_native_subwork import _complete, _publish, _selected
from tests.test_experiment_selected_input_bootstrap import Model


def _reader(plane, store):
    contacts=ExternalNativeEffectContactStore(plane=plane,execution_plan=store.parent_contact.execution_plan,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    return ExternalNativeSubworkStore(plane=plane,parent_contacts=contacts,parent_contact=store.parent_contact,
        parent_inputs=store.parent_inputs,completed_only=True)


def _finished(tmp_path):
    store,definition,_=_selected(tmp_path)
    entry=store.begin(definition);store.contact(entry);_publish(store,entry,b'FALSIFIED')
    observed=_complete(store,entry)
    return store,definition,observed


def _no_array_open(plane,manifests,monkeypatch):
    paths={plane.root.resolve(row.materialization.relative_path,for_write=False) for row in manifests}
    original=artifacts.os.open
    def opened(path,*args,**kwargs):
        if isinstance(path,(str,Path)) and Path(path) in paths:
            pytest.fail('metadata census opened a scientific output body')
        return original(path,*args,**kwargs)
    monkeypatch.setattr(artifacts.os,'open',opened)


def test_native_metadata_reuses_real_control_receipt_checks_without_output_hashes(tmp_path,monkeypatch):
    store,definition,completed=_finished(tmp_path)
    _no_array_open(store.plane,completed.outputs,monkeypatch)
    with store.plane.verification_scope() as plane:
        result=_reader(plane,store).inspect_metadata(definition)
        assert type(result) is NativeSubworkMetadata
        assert result.receipt==completed.receipt and result.completion==completed.completion
        assert result.outputs==completed.outputs and result.partial_outputs==()
        assert not hasattr(result,'state')  # No verified-array/completion projection.


def test_corrupt_output_is_not_promoted_by_metadata_and_full_replay_still_refuses(tmp_path):
    store,definition,completed=_finished(tmp_path)
    output,=completed.outputs
    path=store.plane.root.resolve(output.materialization.relative_path,for_write=False)
    path.write_bytes(b'X'*output.materialization.size_bytes)
    with store.plane.verification_scope() as plane:
        metadata=_reader(plane,store).inspect_metadata(definition)
        assert metadata.outputs==completed.outputs and metadata.receipt==completed.receipt
    with pytest.raises(ArtifactIdentityConflict):
        with store.plane.verification_scope() as plane:
            _reader(plane,store).inspect(definition)


def test_metadata_inspection_refuses_a_changed_child_receipt_before_any_output_hash(tmp_path,monkeypatch):
    store,definition,completed=_finished(tmp_path)
    run,task,attempt=store._receipt_locator(definition)
    relative=store.receipts._relative_path(run,task,attempt)
    path=store.plane.root.resolve(relative,for_write=False)
    raw=path.read_bytes();path.write_bytes(raw[:-1]+(b' ' if raw[-1:]!=b' ' else b'\n'))
    _no_array_open(store.plane,completed.outputs,monkeypatch)
    with pytest.raises((ValueError,ArtifactIdentityConflict)):
        with store.plane.verification_scope() as plane:
            _reader(plane,store).inspect_metadata(definition)


def test_foreign_actual_output_publication_cannot_replace_selected_metadata(tmp_path,monkeypatch):
    store,definition,completed=_finished(tmp_path)
    other=replace(definition,subwork_id='forecast.two')
    entry=store.begin(other);store.contact(entry);_publish(store,entry,b'SATISFIED')
    alien=_complete(store,entry)
    output,=completed.outputs;foreign,=alien.outputs
    _no_array_open(store.plane,(*completed.outputs,*alien.outputs),monkeypatch)
    with store.plane.verification_scope() as plane:
        actual=plane.read_manifest
        def substituted(path,**kwargs):
            return foreign if path==output.materialization.relative_path else actual(path,**kwargs)
        monkeypatch.setattr(plane,'read_manifest',substituted)
        with pytest.raises(ValueError,match='changes its exact publication metadata'):
            _reader(plane,store).inspect_metadata(definition)


def test_metadata_inspection_requires_real_readonly_finite_lifetime(tmp_path):
    store,definition,_=_finished(tmp_path)
    with pytest.raises(ValueError,match='read-only completed store'):
        store.inspect_metadata(definition)
    with store.plane.verification_scope() as plane:
        reader=_reader(plane,store)
    with pytest.raises(ArtifactIdentityConflict,match='scope has ended'):
        reader.inspect_metadata(definition)


def test_exact_scope_membership_is_immutable_rejects_foreign_and_expires(tmp_path):
    store,definition,completed=_finished(tmp_path)
    output,=completed.outputs
    # Deliberately only the pure membership container is exercised here. It is
    # not an authenticated TRAIN factory invocation or an access authority.
    with store.plane.verification_scope() as plane:
        held={output.materialization.relative_path:output}
        scope=NativeTrainingReadScope(None,plane,held)
        held.clear()
        scope.require_member(output)
        control=plane.read_manifest(store._root(definition)+'/definition.json')
        with pytest.raises(PermissionError,match='outside the exact original'):
            scope.require_member(control)
    with pytest.raises(ArtifactIdentityConflict,match='scope has ended'):
        scope.require_member(output)


@pytest.mark.parametrize('damage',('sealed','wrong-codec'))
def test_control_bootstrap_rejects_foreign_custody_or_codec_before_body(tmp_path,monkeypatch,damage):
    store,_,_=_finished(tmp_path)
    record=Model('software.train-metadata.foreign',(2,3))
    access=OutcomeAccess.EVALUATION_SEALED if damage=='sealed' else OutcomeAccess.DEVELOPMENT_VISIBLE
    visibility=VisibilityCeiling.PROSPECTIVE if damage=='sealed' else VisibilityCeiling.DEVELOPMENT_ONLY
    publication=store.plane.write(ArtifactWriteRequest(record.record_id,'foreign/control.json',record.SCHEMA,
        ArtifactProfile.CANONICAL_JSON,'application/json','software.train-metadata.foreign','foreign',
        record.canonical_bytes(),visibility,(),access))
    manifest=store.plane.read_manifest(publication.materialization.relative_path)
    _no_array_open(store.plane,(manifest,),monkeypatch)
    with store.plane.verification_scope() as plane:
        kind=Model
        if damage=='wrong-codec':
            from empirical_lawhood.runtime.native_subwork import NativeSubworkCompletion
            kind=NativeSubworkCompletion
        with pytest.raises(PermissionError,match='published bytes|codec'):
            _Metadata(plane).control(publication.materialization.relative_path,kind)


def test_public_train_scope_refuses_nonlocator_before_any_read(tmp_path,monkeypatch):
    store,_,_=_finished(tmp_path)
    monkeypatch.setattr(store.plane,'verification_scope',lambda *args,**kwargs:pytest.fail('invalid locator opened a scope'))
    with pytest.raises(TypeError,match='exact current locator'):
        with authenticated_native_training_read_scope(artifact_writer=store.plane,locator=object()):
            pytest.fail('invalid locator yielded membership')


@pytest.mark.parametrize('selected_name',('scientific-feature.json','draft.json'))
def test_packet_json_profile_and_identity_do_not_make_a_scientific_body_readable(tmp_path,monkeypatch,selected_name):
    from empirical_lawhood.api.native_training_read_scope import _Packet
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave,RecursiveWaveMember
    store,_,_=_finished(tmp_path)
    # Deliberately invalid TRAIN premises: a real canonical software body has
    # exact bytes/pins, but neither a scientific filename nor a control filename
    # changes it into the required closed control codec. No body may be opened.
    records={name:Model('software.packet.'+str(index),(index,)) for index,name in enumerate(
        ('draft.json','implementation.json','scientific-feature.json'))}
    members=[];published=[]
    for name,record in records.items():
        publication=store.plane.write(ArtifactWriteRequest(record.record_id,'closed-packet/'+name,record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON,'application/json','software.closed-packet','closed-packet',
            record.canonical_bytes(),VisibilityCeiling.DEVELOPMENT_ONLY,(),OutcomeAccess.DEVELOPMENT_VISIBLE))
        published.append(store.plane.read_manifest(publication.materialization.relative_path))
        members.append(RecursiveWaveMember(name,ObjectIdentity.from_record(record.record_id,record),len(record.canonical_bytes())))
    packet=AuthoredRecursiveWave('packet.software.closed',members[0].identity,members[1].identity,
        tuple(sorted(members,key=lambda row:row.filename)))
    _no_array_open(store.plane,published,monkeypatch)
    with store.plane.verification_scope() as plane:
        payloads=_Packet(_Metadata(plane),'closed-packet',packet)
        with pytest.raises(PermissionError,match='non-control packet body'):
            payloads[selected_name]


@pytest.mark.parametrize('training_outermost',(True,False))
def test_actual_guarded_reader_final_hash_requires_training_scope_to_enclose_it(tmp_path,training_outermost):
    from contextlib import ExitStack
    store,_,completed=_finished(tmp_path)
    output,=completed.outputs
    calls=[]
    with ExitStack() as scopes:
        if training_outermost:
            native=scopes.enter_context(store.plane.verification_scope())
            scope=NativeTrainingReadScope(None,native,{output.materialization.relative_path:output})
            def guard(member):
                calls.append(member)
                scope.require_member(member)
            with store.plane.read_context(before_member=guard) as full:
                full.verify_manifest(output)
                before_final=len(calls)
            assert len(calls)>before_final
        else:
            holder=[]
            def guard(member):
                calls.append(member)
                holder[0].require_member(member)
            with pytest.raises(ArtifactIdentityConflict,match='scope has ended'):
                with store.plane.read_context(before_member=guard) as full:
                    with store.plane.verification_scope() as native:
                        holder.append(NativeTrainingReadScope(None,native,{output.materialization.relative_path:output}))
                        full.verify_manifest(output)
                    # The ordinary reader finalizes only AFTER native lifetime
                    # ended. No previous positive member check may rescue this.
            assert calls
