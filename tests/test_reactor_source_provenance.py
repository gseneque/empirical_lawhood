# SPDX-License-Identifier: MPL-2.0
"""Source-custody controls; no source copies or scientific authority."""
from contextlib import nullcontext
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
import pytest
from empirical_lawhood.api import authoring_handoff as owner, reactor_authoring, recursive_prospective_authoring as prospective
from empirical_lawhood.infrastructure import publication_metadata, task_receipts, study_issue
from empirical_lawhood.infrastructure import source_closure
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.planning.study_issue import ImplementationSourceClosure, SourceClosureKind
from empirical_lawhood.runtime.artifacts import ArtifactCustodyLimits, ArtifactProfile
from tests.prospective_source_capture_fixture import synthetic_capture

ROOT = Path(__file__).resolve().parents[1]


def companion_control(monkeypatch):
    raw = b'original public companion bytes'
    logical = SimpleNamespace(payload_schema='software/companion', profile=ArtifactProfile.CANONICAL_JSON,
        media_type='application/json', outcome_access=OutcomeAccess.OUTCOME_BLIND,
        visibility_ceiling=VisibilityCeiling.PROSPECTIVE, content_sha256=sha256(raw).hexdigest())
    physical = SimpleNamespace(relative_path='authoring/provenance/selected-source-manifest.json',
        storage_root_id='software.root', compression='none', partition_selector=None, size_bytes=len(raw), physical_sha256=sha256(raw).hexdigest())
    manifest = SimpleNamespace(logical=logical, materialization=physical, publication=object())
    events = []
    writer = SimpleNamespace(root=SimpleNamespace(contract=SimpleNamespace(canonical_path='/guarded', storage_root_id='software.root'),
        resolve=lambda name, **_: Path('/guarded')/name), custody_limits=ArtifactCustodyLimits(manifest_bytes=65536),
        verify_manifest=lambda _: events.append('verified'))
    monkeypatch.setattr(task_receipts, 'decode_artifact_manifest', lambda *_args, **_kwargs: manifest)
    monkeypatch.setattr(publication_metadata, 'read_publication_metadata', lambda *_: events.append('publication'))
    monkeypatch.setattr(owner, 'read_bounded_bytes', lambda path, **_:
        b'original manifest' if path.name.endswith('.manifest.json') else events.append('payload') or raw)
    def read():
        return owner.read_authoring_source_companion(writer=writer, directory=Path('/guarded/authoring'),
            name='provenance/selected-source-manifest.json', expected_schema='software/companion')
    return read, manifest, events


def test_exact_publication_is_verified_before_original_payload(monkeypatch):
    read, _, events = companion_control(monkeypatch)
    assert read() == b'original public companion bytes'
    assert events == ['publication', 'verified', 'payload']


@pytest.mark.parametrize('damage', ('schema', 'access', 'visibility', 'path', 'size', 'publication', 'logical-hash', 'physical-hash'))
def test_companion_cannot_substitute_original_contract_or_bytes(monkeypatch, damage):
    read, manifest, events = companion_control(monkeypatch)
    if damage == 'schema': manifest.logical.payload_schema = 'software/foreign'
    elif damage == 'access': manifest.logical.outcome_access = OutcomeAccess.EVALUATION_SEALED
    elif damage == 'visibility': manifest.logical.visibility_ceiling = VisibilityCeiling.OUTCOME_VISIBLE
    elif damage == 'path': manifest.materialization.relative_path = 'elsewhere.json'
    elif damage == 'size': manifest.materialization.size_bytes = 0
    elif damage == 'publication': manifest.publication = None
    elif damage == 'logical-hash': manifest.logical.content_sha256 = 'f'*64
    else: manifest.materialization.physical_sha256 = 'f'*64
    with pytest.raises(PermissionError): read()
    if damage not in ('logical-hash', 'physical-hash'): assert events == []


def test_exact_companions_precede_reobservation_without_reconstructing_original_clean_bit(monkeypatch):
    capture = synthetic_capture('source.software.reactor', 'a'*64, clean=False)
    events = []
    monkeypatch.setattr(owner, 'read_bounded_bytes', lambda *_args, **_kwargs: capture.closure.canonical_bytes())
    monkeypatch.setattr(prospective, '_load_source_provenance', lambda **_: events.append('companions'))
    monkeypatch.setattr(study_issue, 'GitStudySourceClosureInspector', lambda _: SimpleNamespace(observe=lambda original: events.append(('observe', original))))
    writer = SimpleNamespace(require_verification_snapshot=lambda: events.append('snapshot'))
    writer.verification_scope = lambda: nullcontext(writer)
    assert owner.authenticate_authoring_source(directory=ROOT, project_root=ROOT, artifact_writer=writer) == capture.closure
    assert events == ['companions', 'snapshot', ('observe', capture.closure)] and not capture.closure.clean_worktree


def test_historical_clean_packet_keeps_no_new_companion_requirement(monkeypatch):
    old = ImplementationSourceClosure('source.historical', SourceClosureKind.CLEAN_GIT_COMMIT, 'a'*40, 'b'*64, 'c'*64, True)
    monkeypatch.setattr(owner, 'read_bounded_bytes', lambda *_args, **_kwargs: old.canonical_bytes())
    assert owner.authenticate_authoring_source(directory=ROOT, project_root=ROOT, artifact_writer=None) == old


def test_selected_source_byte_substitution_refuses_before_authoring_or_publication(tmp_path, monkeypatch):
    target = 'src/empirical_lawhood/__init__.py'
    original_bytes = (ROOT/target).read_bytes()
    original_open, original_read = source_closure._open_relative_read_only, source_closure.os.read
    selected_fds, observations = set(), []
    def selected_open(root, name):
        descriptor = original_open(root, name)
        if name == target:
            selected_fds.add(descriptor)
        return descriptor
    def substituted_read(descriptor, count):
        raw = original_read(descriptor, count)
        if descriptor in selected_fds and raw:
            selected_fds.remove(descriptor)
            observations.append(descriptor)
            return bytes((raw[0]^1,))+raw[1:]
        return raw
    monkeypatch.setattr(source_closure, '_open_relative_read_only', selected_open)
    monkeypatch.setattr(source_closure.os, 'read', substituted_read)
    writer = SimpleNamespace(root=SimpleNamespace(contract=SimpleNamespace(canonical_path=str(tmp_path)),
        verify=lambda **_: None, resolve=lambda name, **_: tmp_path/name),
        write=lambda *_: pytest.fail('changed selected source reached publication'))
    output = tmp_path/'refused-authoring'
    with pytest.raises(source_closure.SourcePolicyError, match='bytes differ'):
        reactor_authoring.author_fresh_reactor(root=ROOT, profile=SimpleNamespace(experiment_id='software.refused.reactor'),
            output_dir=output, artifact_writer=writer)
    assert observations and not output.exists()
    assert (ROOT/target).read_bytes() == original_bytes
