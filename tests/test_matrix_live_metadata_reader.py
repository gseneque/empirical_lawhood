# SPDX-License-Identifier: MPL-2.0
"""Actual metadata custody across sibling reads; no task or native execution."""
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

import pytest

from empirical_lawhood.api import matrix_researcher_programme_lineage as lineage
from empirical_lawhood.api.retained_e3_evidence import retained_e3_evidence_context, retained_e3_reader
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane
from empirical_lawhood.infrastructure.bounded_io import BoundedFileIOError
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from tests.test_recursive_public_service import _plane


@dataclass(frozen=True)
class Control(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/live-metadata-control'
    record_id: str
    value: str


def publish(plane, count=1):
    records = tuple(Control('control.' + str(i), 'literal metadata ' + str(i)) for i in range(count))
    requests = tuple(ArtifactWriteRequest(record.record_id, 'controls/' + record.record_id + '.json',
        record.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', 'live-metadata-controls',
        'controls', record.canonical_bytes(), VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND)
        for record in records)
    plane.write_compact_batch(requests)
    return records, requests


def read(plane, request, maximum_bytes=None):
    return lineage.read_published_record(plane, request.relative_path, Control,
        len(request.payload) if maximum_bytes is None else maximum_bytes)


@pytest.mark.parametrize('count', (4, 32))
def test_sibling_reads_share_typed_controls_only_until_the_actual_owner_exits(tmp_path, monkeypatch, count):
    plane = _plane(tmp_path / 'artifacts')
    expected, requests = publish(plane, count)
    calls = []
    from empirical_lawhood.infrastructure import canonical_record_read
    from empirical_lawhood.kernel import decoding
    for module in (decoding, canonical_record_read):
        original = module.decode_canonical_bytes_with_identity
        def decode(raw, kind, *, _original=original, **kwargs):
            if kind is Control:
                calls.append(raw)
            return _original(raw, kind, **kwargs)
        monkeypatch.setattr(module, 'decode_canonical_bytes_with_identity', decode)
    with retained_e3_evidence_context(plane) as evidence:
        with retained_e3_reader(plane).read_context() as first_reader:
            first = tuple(read(first_reader, request) for request in requests)
        with retained_e3_reader(plane).read_context() as second_reader:
            second = tuple(read(second_reader, request) for request in requests)
        assert first == second == expected
        assert all(a is b for a, b in zip(first, second, strict=True))
        assert len(calls) == count
        assert first_reader is second_reader is evidence.writer
        # Sharing a reader never gives it the caller's publication capability.
        with pytest.raises(ArtifactIdentityConflict, match='cannot publish'):
            first_reader.write(requests[0])
    assert retained_e3_reader(plane) is plane
    assert tuple(read(plane, request) for request in requests) == expected
    assert len(calls) == 2 * count
    with pytest.raises(ArtifactIdentityConflict, match='ended'):
        first_reader.require_active_verification_scope()


@pytest.mark.parametrize('damage', ('body', 'sidecar', 'commit'))
def test_shared_control_keeps_every_original_byte_guard_through_outer_return(tmp_path, damage):
    plane = _plane(tmp_path / 'artifacts')
    _, requests = publish(plane)
    request, = requests
    manifest = plane.read_manifest(request.relative_path)
    relative = (request.relative_path if damage == 'body' else request.relative_path + '.manifest.json'
        if damage == 'sidecar' else manifest.publication.commit_marker_relative_path)
    path = Path(plane.root.contract.canonical_path) / relative
    with pytest.raises((ArtifactIdentityConflict, ValueError, OSError)):
        with retained_e3_evidence_context(plane):
            original = read(plane, request)
            assert read(plane, request) is original
            path.write_bytes(path.read_bytes() + b' ')


def test_shared_typed_control_cannot_bypass_a_smaller_later_read_bound(tmp_path):
    plane = _plane(tmp_path / 'artifacts')
    _, requests = publish(plane)
    request, = requests
    with retained_e3_evidence_context(plane):
        read(plane, request)
        with pytest.raises(BoundedFileIOError, match='byte limit'):
            read(plane, request, len(request.payload) - 1)


def test_sibling_scoped_access_guard_is_retained_and_refreshed(tmp_path):
    plane = _plane(tmp_path / 'artifacts')
    _, requests = publish(plane)
    allowed = [True]
    calls = []
    def current(manifest):
        calls.append(manifest.logical.logical_artifact_id)
        if not allowed[0]:
            raise PermissionError('literal current access revoked')
    with retained_e3_evidence_context(plane):
        read(plane, requests[0])
        try:
            with pytest.raises(PermissionError, match='current access revoked'):
                with plane.read_context(before_member=current) as scoped:
                    assert retained_e3_reader(scoped) is scoped
                    read(scoped, requests[0])
                    count = len(calls)
                    allowed[0] = False
                    read(scoped, requests[0])
            assert len(calls) > count
        finally:
            allowed[0] = True


@pytest.mark.parametrize('selection', ('strict', 'workers', 'custom-state', 'custom-read'))
def test_different_reader_policy_is_not_replaced_by_the_shared_owner(tmp_path, selection):
    plane = _plane(tmp_path / 'artifacts')
    expected, requests = publish(plane)
    with retained_e3_evidence_context(plane):
        read(plane, requests[0])
        other = ExternalArtifactPlane(plane.root, plane.validators, plane.semantic_validations,
            custody_limits=plane.custody_limits, maximum_parallel_verifications=plane.maximum_parallel_verifications,
            artifact_verification=plane.artifact_verification)
        calls = []
        if selection == 'strict':
            from empirical_lawhood.runtime.operational_configuration import ArtifactVerificationMode
            other.artifact_verification = ArtifactVerificationMode.STRICT
        elif selection == 'workers':
            other.maximum_parallel_verifications += 1
        elif selection == 'custom-state':
            other.custom_read_policy = object()
        else:
            original = other.read_manifest
            def observe(*args, **kwargs):
                calls.append(args[0])
                return original(*args, **kwargs)
            other.read_manifest = observe
        assert retained_e3_reader(other) is other
        assert read(other, requests[0]) == expected[0]
        if selection == 'custom-read':
            assert calls == [requests[0].relative_path]


def test_programme_read_and_transition_share_custody_without_replacing_the_publisher(tmp_path, monkeypatch):
    from contextlib import contextmanager
    from empirical_lawhood.api import matrix_programme_recorded_lineage as transitions
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
    from empirical_lawhood.api.matrix_programme_projection import MatrixProgrammeProjectionContext
    from empirical_lawhood.api.matrix_researcher_programme import MatrixResearchProgrammeService
    plane = _plane(tmp_path / 'artifacts')
    _, requests = publish(plane)
    root = Path(plane.root.contract.canonical_path)
    service = ExperimentProgrammeService(Path(__file__).parents[1], plane, None)
    selected = MatrixResearchProgrammeService(service=service)
    context = MatrixProgrammeProjectionContext(service, None, None, root, {}, {})
    values, readers = [], []
    @contextmanager
    def programme(actual_owner, plan, *, operation):
        assert plan is requests and operation is None
        readers.append(actual_owner.writer)
        values.append(read(actual_owner.writer, requests[0]))
        yield context
    @contextmanager
    def transition(actual_owner, reading, record):
        assert actual_owner is selected and record is requests
        readers.append(reading.writer)
        values.append(read(reading.writer, requests[0]))
        yield
    monkeypatch.setattr(MatrixResearchProgrammeService, '_context', programme)
    monkeypatch.setattr(transitions, '_recorded_continuation_context', transition)
    with retained_e3_evidence_context(plane) as evidence:
        with selected._read_context(requests):
            assert context.writer is plane
        with transitions.recorded_continuation_context(selected, context, requests):
            assert context.writer is plane
        assert readers == [evidence.writer, evidence.writer]
        assert values[0] is values[1]
