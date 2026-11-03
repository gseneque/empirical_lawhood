# SPDX-License-Identifier: MPL-2.0
"""Withdrawal custody uses an actual exposed PURE packet, never native science."""
from dataclasses import replace

import pytest

from empirical_lawhood.api.matrix_amendment_withdrawals import _withdrawn_packet
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.recursive_custody import read_recursive_bootstrap_record
from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave
from tests.test_matrix_programme_metadata_reuse import just_authored  # noqa: F401
from tests.test_recursive_report_projection import wave  # noqa: F401


def _packet(control, writer):
    relative = (control.directory / 'authored-wave.json').relative_to(writer.root.contract.canonical_path).as_posix()
    return read_recursive_bootstrap_record(writer, relative, AuthoredRecursiveWave)


def test_withdrawn_packet_authenticates_every_member_and_original_run_without_graph_rebuild(just_authored, monkeypatch):  # noqa: F811
    from empirical_lawhood.api import recursive_authoring, recursive_execution
    monkeypatch.setattr(recursive_authoring, 'load_authored_wave',
        lambda **_: pytest.fail('withdrawal decodes the entire inactive scientific draft'))
    monkeypatch.setattr(recursive_execution, '_retained_plans',
        lambda *_: pytest.fail('withdrawal reconstructs an executable graph'))
    f = just_authored
    with f.plane.read_context() as writer:
        expected = _packet(f, writer)
        packet, run, payloads = _withdrawn_packet(writer, f.directory, expected.implementation)
        assert packet == expected and run.run_plan_id == f.report['run_id']
        assert set(payloads) == {member.filename for member in expected.members}
        assert run.draft == packet.draft
        writer.require_verification_snapshot()


@pytest.mark.parametrize('change', ('source-pin', 'member-before', 'member-after', 'run-namespace'))
def test_withdrawn_packet_refuses_foreign_source_changed_bytes_or_any_execution_namespace(just_authored, change):  # noqa: F811
    f = just_authored
    path, before = None, None
    match = ('declared original producing source' if change == 'source-pin' else
        'superseded future execution' if change == 'run-namespace' else None)
    try:
        with pytest.raises((ValueError, PermissionError, ArtifactIdentityConflict), match=match):
            with f.plane.read_context() as writer:
                expected = _packet(f, writer).implementation
                if change == 'source-pin':
                    expected = replace(expected, object_fingerprint='0' * 64)
                elif change in ('member-before', 'member-after'):
                    path = f.directory / 'draft.json'
                    before = path.read_bytes()
                    if change == 'member-before':
                        path.write_bytes(bytes([before[0] ^ 1]) + before[1:])
                else:
                    path = writer.root.resolve('runs/' + f.report['run_id'], for_write=True)
                    path.mkdir(parents=True)
                _withdrawn_packet(writer, f.directory, expected)
                if change == 'member-after':
                    path.write_bytes(bytes([before[0] ^ 1]) + before[1:])
                writer.require_verification_snapshot()
    finally:
        if before is not None:
            path.write_bytes(before)
        elif path is not None and path.exists():
            path.rmdir()


def test_withdrawn_control_reuse_keeps_nonentry_current_and_expires(just_authored, monkeypatch):  # noqa: F811
    from empirical_lawhood.kernel import decoding
    from empirical_lawhood.api.retained_e3_evidence import retained_e3_evidence_context
    from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan, DevelopmentRunPlan
    f = just_authored
    original = decoding.decode_canonical_bytes_with_identity
    calls = []
    def decode(raw, kind, **kwargs):
        if kind in (DevelopmentExecutionPlan, DevelopmentRunPlan):
            calls.append(kind)
        return original(raw, kind, **kwargs)
    monkeypatch.setattr(decoding, 'decode_canonical_bytes_with_identity', decode)
    with retained_e3_evidence_context(f.plane) as evidence:
        expected = _packet(f, evidence.writer)
        first = _withdrawn_packet(evidence.writer, f.directory, expected.implementation)
        second = _withdrawn_packet(evidence.writer, f.directory, expected.implementation)
        assert first[1] is second[1]
        assert calls == [DevelopmentRunPlan, DevelopmentExecutionPlan]
        path = f.plane.root.resolve('runs/' + first[1].run_plan_id, for_write=True)
        path.mkdir(parents=True)
        try:
            with pytest.raises(PermissionError, match='superseded future execution'):
                _withdrawn_packet(evidence.writer, f.directory, expected.implementation)
        finally:
            path.rmdir()
    with retained_e3_evidence_context(f.plane) as evidence:
        third = _withdrawn_packet(evidence.writer, f.directory, expected.implementation)
        assert third[1] == first[1] and third[1] is not first[1]
    assert calls == [DevelopmentRunPlan, DevelopmentExecutionPlan] * 2


@pytest.mark.parametrize('custom', (False, True))
def test_authored_members_keep_the_live_sidecar_owner_and_custom_fallback(just_authored, monkeypatch, custom):  # noqa: F811
    from empirical_lawhood.infrastructure import recursive_custody
    f = just_authored
    reads = []
    actual = recursive_custody.read_bounded_bytes
    def observed(path, **kwargs):
        if str(path).endswith('.manifest.json'):
            reads.append(path)
        return actual(path, **kwargs)
    monkeypatch.setattr(recursive_custody, 'read_bounded_bytes', observed)
    with f.plane.read_context() as writer:
        packet = _packet(f, writer)
        if custom:
            # Customizing the read policy deliberately retains the old route.
            original = writer.read_manifest
            monkeypatch.setattr(writer, 'read_manifest', lambda *args, **kwargs: original(*args, **kwargs))
        payloads = recursive_custody.AuthenticatedRecursivePayloads(plane=writer,
            directory=f.directory, members=packet.members)
        assert set(payloads) == {member.filename for member in packet.members}
        assert all(payloads.manifest(member.filename).logical.content_sha256 == member.identity.object_fingerprint
            for member in packet.members)
        assert bool(reads) is custom
        writer.require_verification_snapshot()
