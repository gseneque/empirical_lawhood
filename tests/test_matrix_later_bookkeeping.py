# SPDX-License-Identifier: MPL-2.0
"""Later-phase bookkeeping on disclosed software custody, never qualification."""
from dataclasses import replace
import os
import sys
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import recursive_execution, selected_e4_native_read
from empirical_lawhood.api.current_result_custody import retained_output_artifact_plane
from empirical_lawhood.api.integration_artifact_profiles import INTEGRATION_ARTIFACT_PROFILE_VALIDATORS
from empirical_lawhood.infrastructure import artifacts, recursive_custody
from empirical_lawhood.runtime.recovery import build_run_recovery_index
from tests.runtime_platform.test_recursive_prospective_workflow import (
    Config, _public_issued_handoff_fixture, _run_public_handoff,
)


@pytest.fixture(scope='module')
def issued_outputs(tmp_path_factory):
    """Five actual PURE software tasks; no Matrix native work or scientific claim."""
    from empirical_lawhood.adapters.reference_worlds.runtime import ReferenceAdjudicationFixture
    from empirical_lawhood.runtime.adjudication import ScientificAdjudicationRecord
    root = tmp_path_factory.mktemp('issued-bookkeeping')
    with pytest.MonkeyPatch.context() as patch:
        parts = _public_issued_handoff_fixture(root, patch)
        fixture = _run_public_handoff(root, issued_parts=parts)
    mount = next(path for path in (root, *root.parents) if os.path.ismount(path))
    plane = artifacts.ExternalArtifactPlane(
        artifacts.GuardedExternalRoot(replace(fixture.plane.root.contract, required_mount_path=str(mount))),
        validators=INTEGRATION_ARTIFACT_PROFILE_VALIDATORS)
    codecs = {kind.SCHEMA: kind for kind in (Config, ReferenceAdjudicationFixture, ScientificAdjudicationRecord)}
    plan, package = fixture.execution_plan, fixture.package
    pin = selected_e4_native_read.r.pin
    index = build_run_recovery_index(plan, run_id=package.run_plan_id, wave_id='wave.' + package.package_id,
        authority_identities=(pin(package.scientific_approval, 'authorization_id'),
            pin(package.execution_authority, 'authority_id')))
    semantic = retained_output_artifact_plane(package, plan, plane, codecs)
    inputs = selected_e4_native_read._inputs(semantic, plan, package.run_plan_id, require_current=lambda _: None)
    return SimpleNamespace(plane=semantic, plan=plan, index=index, inputs=inputs, codecs=codecs,
        fixture=fixture)


def _issued_read(f, *, optimized, decode=True):
    with f.plane.read_context() as writer:
        options = {} if not optimized else {'_read_policy': recursive_execution._read_only_custody_policy(writer)}
        return recursive_custody.read_execution_products(plane=writer, plan=f.plan, index=f.index,
            external_inputs=f.inputs, output_codecs=f.codecs, decode_products=decode, **options)


@pytest.mark.parametrize('decode', (False, True))
def test_issued_full_and_compact_outputs_batch_once_with_exact_serial_parity(issued_outputs, decode, record_property):
    f = issued_outputs
    expected = _issued_read(f, optimized=False, decode=decode)
    paths = {row['relative_path'] for row in expected['product_index']}
    assert len(paths) > 2
    batches = []
    code = artifacts.ExternalArtifactPlane._verify_manifests.__code__
    previous = sys.getprofile()
    def observe(frame, event, _argument):
        if event == 'call' and frame.f_code is code:
            selected = {row.materialization.relative_path for row in frame.f_locals['manifests']}
            if selected == paths:
                batches.append(selected)
    sys.setprofile(observe)
    try:
        actual = _issued_read(f, optimized=True, decode=decode)
    finally:
        sys.setprofile(previous)
    assert actual == expected
    record_property('output_count',len(paths))
    record_property('complete_output_batches',len(batches))
    assert len(batches) == 1


def test_issued_output_batch_refuses_body_mutation_before_return(issued_outputs, monkeypatch):
    f = issued_outputs
    expected = _issued_read(f, optimized=False)
    selected = next(iter(expected['outputs'].values()))
    path = f.plane.root.resolve(selected.materialization.relative_path, for_write=False)
    original = path.read_bytes()
    assemble = recursive_custody._assemble_read_products
    def changed(**options):
        result = assemble(**options)
        path.write_bytes(b'X' + original[1:])
        return result
    monkeypatch.setattr(recursive_custody, '_assemble_read_products', changed)
    try:
        with pytest.raises(artifacts.ArtifactIdentityConflict):
            _issued_read(f, optimized=True)
    finally:
        path.write_bytes(original)


def test_issued_custom_root_keeps_serial_policy_and_exact_products(issued_outputs):
    f=issued_outputs
    expected=_issued_read(f,optimized=True)
    calls=[]
    class CustomRoot(artifacts.GuardedExternalRoot):
        def resolve(self,*args,**kwargs):
            calls.append(True)
            return super().resolve(*args,**kwargs)
    plane=artifacts.ExternalArtifactPlane(CustomRoot(f.plane.root.contract),
        validators=f.plane.validators,semantic_validations=f.plane.semantic_validations)
    selected=SimpleNamespace(**{**vars(f),'plane':plane})
    assert recursive_execution._read_only_custody_policy(plane) is None
    assert _issued_read(selected,optimized=True)==expected
    assert calls


@pytest.mark.parametrize('damage', ('none', 'late-output', 'revoked-grant'))
def test_e5_e6_common_reader_reuses_custody_and_keeps_live_guards(issued_outputs, monkeypatch, damage, record_property):
    """Real issued controls/receipts; an explicit seam stops before Matrix science."""
    from empirical_lawhood.api import matrix_selected_scientific_read as reader, recursive_operations
    from empirical_lawhood.api.selected_prepared_access import guarded_output_payload
    from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
    f=issued_outputs
    package=f.fixture.package
    selected=SimpleNamespace(association=SimpleNamespace(candidate=reader._pin(package.issued_study.candidate,'candidate_id')),
        implementation=package.issued_study.source_closure,projection=f.plan)
    monkeypatch.setattr(reader,'_design',lambda _: (SimpleNamespace(account='REVISION',criterion=SimpleNamespace(is_matched=True)),None))
    monkeypatch.setattr(recursive_operations,'operation_catalog',lambda: (None,None,f.codecs))
    guards={'controls':0,'science':0}
    current=[]
    grant_refreshes=[]
    active=[]
    code=artifacts.ExternalArtifactPlane._require_verification_snapshot_paths.__code__
    previous=sys.getprofile()
    def observe(frame,event,_argument):
        if event=='call' and frame.f_code is reader._CurrentPreparedScientificRead.require_current.__code__:
            grant_refreshes.append(True)
        if event=='call' and frame.f_code is code and active:
            phase,writer=active[-1]
            if frame.f_locals['self'] is writer:guards[phase]+=1
    entry=SimpleNamespace(phase='entry')
    def entry_seam(writer,run_id,plan,*,custody):
        active.append(('controls',custody._control_reader.writer))
        try:
            for _ in range(12):
                assert custody._control_reader.authenticate_execution_plan(package=package,
                    issued=package.issued_study,run_id=run_id)==plan
        finally:active.pop()
        return plan.tasks[0],entry,True
    monkeypatch.setattr(reader,'_entry',entry_seam)
    monkeypatch.setattr(reader,'_validate_design',lambda *args:None)
    monkeypatch.setattr(reader,'_current_source_qualifications',lambda *args:None)
    monkeypatch.setattr(reader,'_entry_evidence',lambda *args,**kwargs:None)
    monkeypatch.setattr(reader,'_original_source_operands',lambda *args,**kwargs:None)
    class ReachedScience(RuntimeError):pass
    path=f.plane.root.resolve(f.fixture.qualification_receipt.output_materializations[0].relative_path,for_write=False)
    raw=path.read_bytes()
    load=ExternalStudyOperationAuthorityStore.load
    def revoked(store,authority_id):
        if authority_id==f.fixture.reveal.authority_id:
            raise PermissionError('disclosed grant revoked inside scientific read')
        return load(store,authority_id)
    def scientific_seam(writer,package,plan,receipts,*args,original_input_access,**kwargs):
        active.append(('science',writer))
        try:
            for receipt in receipts.values():
                for logical in receipt.output_logical_artifacts:
                    original_input_access.require_current()
                    current.append(logical.logical_artifact_id)
                    for _ in range(3):
                        assert guarded_output_payload(writer,receipt,logical,1024**2,original_input_access)
        finally:active.pop()
        if damage=='late-output':path.write_bytes(b'X'+raw[1:])
        if damage=='revoked-grant':
            monkeypatch.setattr(ExternalStudyOperationAuthorityStore,'load',revoked)
            original_input_access.require_current()
        raise ReachedScience('disclosed phase seam supplies no Matrix result')
    monkeypatch.setattr(reader,'_terminal_science',scientific_seam)
    sys.setprofile(observe)
    try:
        error=ReachedScience if damage=='none' else artifacts.ArtifactIdentityConflict if damage=='late-output' else PermissionError
        with pytest.raises(error):
            reader.read_selected_protected_result(selected=selected,artifact_writer=f.plane,
                run_id=package.run_plan_id,reveal_authority_id=f.fixture.reveal.authority_id)
    finally:
        sys.setprofile(previous)
        if damage=='late-output':path.write_bytes(raw)
    record_property('repeated_control_census_guards',guards['controls'])
    record_property('repeated_scientific_census_guards',guards['science'])
    record_property('live_grant_refreshes',len(grant_refreshes))
    assert len(current)>2 and len(grant_refreshes)>3*len(current)
    assert guards=={'controls':0,'science':0},guards
