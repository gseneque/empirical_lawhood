# SPDX-License-Identifier: MPL-2.0
"""Canonical control reads preserve issued access labels; no custody is created."""

from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import current_task_custody as owner
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from tests.runtime_platform.test_recursive_compiler import Config


@pytest.mark.parametrize('access,visibility', (
    (OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE),
    (OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.PROSPECTIVE),
    (OutcomeAccess.EVALUATOR_REVEAL, VisibilityCeiling.OUTCOME_VISIBLE),
))
def test_exact_control_lane_preserves_default_refusal_and_canonical_byte_checks(monkeypatch, access, visibility):
    record = Config('config.synthetic.control-lane', 3)
    raw, reads = record.canonical_bytes(), []
    manifest = SimpleNamespace(logical=SimpleNamespace(outcome_access=access, visibility_ceiling=visibility,
        content_sha256=sha256(raw).hexdigest()), materialization=SimpleNamespace(relative_path='unpublished/control.json',
            size_bytes=len(raw), physical_sha256=sha256(raw).hexdigest()))
    writer = SimpleNamespace(root=SimpleNamespace(resolve=lambda *args, **kwargs: 'unpublished/control.json'),
        verify_manifest=lambda value: reads.append('manifest'))
    monkeypatch.setattr(owner, 'read_bounded_bytes', lambda *args, **kwargs: reads.append('canonical-bytes') or raw)
    hashes = []
    def observed_hash(payload):
        hashes.append(payload)
        return sha256(payload)
    monkeypatch.setattr(owner, 'sha256', observed_hash)
    custody = owner.CurrentIssuedTaskCustody(writer=writer)
    if access is not OutcomeAccess.OUTCOME_BLIND:
        with pytest.raises(PermissionError, match='exact issued access'):
            custody.control_record(manifest, Config, len(raw))
        assert reads == []
    assert custody.control_record(manifest, Config, len(raw), expected_outcome_access=access,
        expected_visibility_ceiling=visibility) == record
    assert reads == ['manifest', 'canonical-bytes']
    assert hashes == [raw]
    manifest.materialization.physical_sha256 = 'f' * 64
    with pytest.raises(PermissionError, match='exact canonical'):
        custody.control_record(manifest, Config, len(raw), expected_outcome_access=access,
            expected_visibility_ceiling=visibility)
    assert hashes == [raw, raw]
    manifest.materialization.physical_sha256 = sha256(raw).hexdigest()
    manifest.logical.content_sha256 = 'f' * 64
    with pytest.raises(PermissionError, match='exact canonical'):
        custody.control_record(manifest, Config, len(raw), expected_outcome_access=access,
            expected_visibility_ceiling=visibility)
    assert hashes == [raw, raw, raw]


@pytest.mark.parametrize('access,visibility', ((None, VisibilityCeiling.PROSPECTIVE),
    (OutcomeAccess.OUTCOME_BLIND, None), (OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.PROSPECTIVE)))
def test_unspecified_or_substituted_lane_refuses_before_any_read(access, visibility):
    manifest = SimpleNamespace(logical=SimpleNamespace(outcome_access=OutcomeAccess.OUTCOME_BLIND,
        visibility_ceiling=VisibilityCeiling.PROSPECTIVE))
    custody = owner.CurrentIssuedTaskCustody(writer=SimpleNamespace())
    with pytest.raises(PermissionError, match='exact issued access'):
        custody.control_record(manifest, Config, 4096, expected_outcome_access=access,
            expected_visibility_ceiling=visibility)


def test_scoped_immutable_control_parse_reuse_keeps_real_custody_and_decimal_policy(tmp_path, monkeypatch):
    from decimal import localcontext
    from empirical_lawhood.infrastructure import canonical_record_read
    from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, GuardedExternalRoot
    from empirical_lawhood.infrastructure.bounded_io import BoundedFileIOError
    from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, ExternalRootContract
    from empirical_lawhood.runtime.operator_profile import OperatorStorageProfile

    plane=ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract(
        'synthetic.static-control-store','disclosed static parse reuse',str(tmp_path),
        str(next(parent for parent in tmp_path.parents if parent.is_mount())),
        OperatorStorageProfile.SCHEMA,1,None,None,())))
    record=Config('config.synthetic.static-control',3)
    publication=plane.write(ArtifactWriteRequest(
        logical_artifact_id=record.config_id,relative_path='controls/config.json',payload_schema=record.SCHEMA,
        profile=ArtifactProfile.CANONICAL_JSON,media_type='application/json',
        publication_scope_id='synthetic.static-controls',publication_scope_relative_root='controls',
        payload=record.canonical_bytes(),visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
        parent_visibility_ceilings=(),outcome_access=OutcomeAccess.OUTCOME_BLIND,minimum_free_bytes=1))
    manifest=plane.read_manifest(publication.materialization.relative_path)
    parses=[];payloads=[];decode=canonical_record_read._SelectedCanonicalRecordRead.decode
    def observed(selection,raw):
        if selection.record_type is Config:
            parses.append(Config);payloads.append(raw)
        return decode(selection,raw)
    # Static controls now use the typed publication owner. Observe that owner
    # without changing its eligibility hooks or forcing the fallback reader.
    monkeypatch.setattr(canonical_record_read._SelectedCanonicalRecordRead,'decode',observed)
    custody=owner.CurrentIssuedTaskCustody(writer=plane)
    with custody.verification_scope():
        reader=custody._control_reader
        assert custody.writer is plane and reader.writer is not plane
        first=custody.immutable_control_record(manifest,Config,len(record.canonical_bytes()))
        assert custody.immutable_control_record(manifest,Config,len(record.canonical_bytes())) is first
        assert parses==[Config] and payloads==[record.canonical_bytes()]
        with localcontext() as context:
            context.prec+=1
            assert custody.immutable_control_record(manifest,Config,len(record.canonical_bytes()))==record
        assert parses==[Config,Config] and payloads==[record.canonical_bytes()]*2
        # Ordinary per-task controls deliberately do not join the persistent snapshot.
        assert custody.control_record(manifest,Config,len(record.canonical_bytes()))==record
        assert parses==[Config,Config]
        with pytest.raises(PermissionError,match='exact issued access'):
            custody.immutable_control_record(manifest,Config,len(record.canonical_bytes()),
                expected_outcome_access=OutcomeAccess.EVALUATION_SEALED)
        with pytest.raises(BoundedFileIOError):
            custody.immutable_control_record(manifest,Config,1)
    assert custody._control_reader is None
    with pytest.raises(RuntimeError):
        reader.read_control(manifest,Config,len(record.canonical_bytes()))


def test_current_issued_control_scope_ignores_routes_without_custody_ports():
    with owner.current_issued_task_control_scope(SimpleNamespace()):
        pass


@pytest.mark.parametrize('custom',('subclass','write-hook'))
def test_current_task_scope_preserves_custom_writer_hooks(custom):
    from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane
    if custom=='subclass':
        class CustomPlane(ExternalArtifactPlane):
            def verification_scope(self):
                raise AssertionError('custom writer must keep its independent reads')
        writer=object.__new__(CustomPlane)
    else:
        writer=object.__new__(ExternalArtifactPlane)
        writer.write=lambda *_args,**_kwargs: None
    custody=owner.CurrentIssuedTaskCustody(writer=writer)
    with custody.verification_scope():
        assert custody._control_reader is None and custody._issued_reader is None


@pytest.mark.parametrize('fail', (False, True))
def test_original_control_lifetime_opens_once_and_closes_on_every_exit(tmp_path, fail):
    from contextlib import contextmanager
    from tests.test_matrix_factor_confirmation_eligibility import _matrix_plane

    events = []

    @contextmanager
    def original():
        events.append('open')
        try:
            yield
        finally:
            events.append('close')

    custody = owner.CurrentIssuedTaskCustody(writer=_matrix_plane(tmp_path / 'scope'), original_control_scopes=(original,))
    try:
        with custody.verification_scope():
            reader = custody._control_reader
            with custody.verification_scope():
                assert events == ['open'] and custody._control_reader is reader
            assert events == ['open']
            if fail:
                raise RuntimeError('disclosed scope failure')
    except RuntimeError as error:
        assert fail and str(error) == 'disclosed scope failure'
    assert events == ['open', 'close']
    assert custody._control_reader is custody._issued_reader is None
    with pytest.raises(RuntimeError):
        reader.writer.require_verification_context()


def test_original_control_lifetime_refuses_custom_writer_before_entry():
    entered = []
    custody = owner.CurrentIssuedTaskCustody(writer=SimpleNamespace(),
        original_control_scopes=(lambda: entered.append(True),))
    with pytest.raises(PermissionError, match='ordinary guarded custody'):
        with custody.verification_scope():
            pytest.fail('custom writer reached an original custody lifetime')
    assert entered == []
