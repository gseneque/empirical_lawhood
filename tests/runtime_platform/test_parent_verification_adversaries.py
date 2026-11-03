# SPDX-License-Identifier: MPL-2.0
"""Scoped custody and live authority refusals; no scientific qualification.

The small batch has actual exposed canonical bytes and no authority records.
The parent replay case reuses the existing explicitly synthetic issued fixture;
it supplies no real signer, source eligibility or scientific outcome authority.
"""

from dataclasses import replace
from datetime import UTC, datetime
import os

import pytest

from empirical_lawhood.api.current_result_custody import CurrentResultPlanReader
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ExternalRootUnavailable
from empirical_lawhood.runtime.artifacts import (
    ArtifactSemanticValidation, ArtifactSemanticValidationRegistration, ArtifactSemanticValidationRegistry,
)
from empirical_lawhood.runtime.execution import VerifiedArtifactInput
from tests.numerical_provenance_fixtures import numerical_plane
from tests.test_unrestricted_artifact_custody import SoftwarePayload, manifest, request
from tests.runtime_platform.test_recursive_prospective_parents import (
    _assess_synthetic_parent, _parent_inputs, parent_fixture as parent_fixture,
)


@pytest.fixture
def actual_batch(tmp_path):
    plane = numerical_plane(tmp_path / "custody")
    records = (SoftwarePayload("software.first", "first original full bytes"),
        SoftwarePayload("software.last", "last original full bytes"))
    results = plane.write_batch(tuple(request(record) for record in records))
    manifests = tuple(manifest(plane, result) for result in results)
    assert len(manifests[0].publication.members) == 2
    return plane, records, manifests


def _target(plane, manifests, member):
    if member == "sibling-payload":
        relative = manifests[-1].materialization.relative_path
    elif member == "sibling-sidecar":
        relative = manifests[-1].materialization.relative_path + ".manifest.json"
    else:
        relative = manifests[0].publication.commit_marker_relative_path
    return plane.root.resolve(relative, for_write=False)


def _change_actual_file(path, mutation):
    raw, before = path.read_bytes(), path.stat()
    if mutation == "same-size-restored-mtime":
        altered = bytes((raw[0] ^ 1,)) + raw[1:]
        assert len(altered) == len(raw) and altered != raw
        path.write_bytes(altered)
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        assert path.stat().st_mtime_ns == before.st_mtime_ns
    elif mutation == "missing":
        path.unlink()
    elif mutation == "same-bytes-new-inode":
        replacement = path.with_name(path.name + ".exposed-replacement")
        replacement.write_bytes(raw)
        replacement.replace(path)
        assert path.read_bytes() == raw and path.stat().st_ino != before.st_ino
    else:
        target = path.with_name(path.name + ".exposed-link-target")
        path.rename(target)
        path.symlink_to(target)


@pytest.mark.parametrize("member", ("sibling-payload", "sibling-sidecar", "commit-marker"))
@pytest.mark.parametrize("mutation", ("same-size-restored-mtime", "missing", "same-bytes-new-inode", "symlink"))
@pytest.mark.parametrize("boundary", ("reuse", "successful-exit"))
def test_every_committed_member_is_guarded_before_reuse_and_successful_exit(actual_batch, member, mutation, boundary):
    plane, _, manifests = actual_batch
    with pytest.raises((ArtifactIdentityConflict, ExternalRootUnavailable, ValueError, OSError)):
        with plane.verification_scope() as scoped:
            scoped.verify_manifest(manifests[0])
            _change_actual_file(_target(plane, manifests, member), mutation)
            if boundary == "reuse":
                # Asking for the first original member still guards its sibling
                # and the whole commit marker. No fresh view hides the mutation.
                scoped.verify_manifest(manifests[0])


def test_projection_readers_and_semantic_views_share_the_same_finite_lifetime(actual_batch):
    plane, _, manifests = actual_batch
    with pytest.raises(ArtifactIdentityConflict, match="active verification scope"):
        CurrentResultPlanReader(plane)
    with plane.verification_scope() as scoped:
        scoped.verify_manifest(manifests[0])
        projected = scoped.with_semantic_validation_registry(ArtifactSemanticValidationRegistry("exposed.same-semantics", ()))
        projected.verify_manifest(manifests[0])
        reader = CurrentResultPlanReader(projected)
        assert reader.writer is projected
    for view in (scoped, projected):
        with pytest.raises(ArtifactIdentityConflict, match="scope has ended"):
            view.verify_manifest(manifests[0])
        with pytest.raises(ArtifactIdentityConflict, match="scope has ended"):
            CurrentResultPlanReader(view)


def test_cached_generic_bytes_cannot_supply_a_different_semantic_contract(actual_batch):
    plane, _, manifests = actual_batch
    original = manifests[0]
    altered = ArtifactSemanticValidation("exposed.changed-validator", "1.0.0", "e" * 64,
        original.logical.payload_schema, original.logical.profile, ("schema", "value", "version"),
        ("record_id", "text"), (("schema", original.logical.payload_schema), ("version", "1.0.0")))
    registry = ArtifactSemanticValidationRegistry("exposed.changed-semantics", (
        ArtifactSemanticValidationRegistration(original.logical.logical_artifact_id, altered),))
    with plane.verification_scope() as scoped:
        scoped.verify_manifest(original)
        with pytest.raises(ArtifactIdentityConflict):
            scoped.with_semantic_validation_registry(registry).verify_manifest(original)


def test_worker_transport_authenticates_actual_bytes_and_keeps_the_delivered_snapshot(actual_batch):
    plane, records, manifests = actual_batch
    first = manifests[0]
    value = VerifiedArtifactInput(first.logical, first.materialization)
    with plane.verification_scope() as scoped:
        scoped.verify_manifest(first)
        port = scoped.open(value, maximum_bytes=None)
    try:
        assert port.read() == records[0].canonical_bytes()
        port.seek(0)
        path = plane.root.resolve(first.materialization.relative_path, for_write=False)
        _change_actual_file(path, "same-size-restored-mtime")
        # The worker retains the actual originally sealed descriptor. A new
        # delivery must independently reject the changed source publication.
        assert port.read() == records[0].canonical_bytes()
        with pytest.raises(ArtifactIdentityConflict):
            plane.open(value, maximum_bytes=None)
    finally:
        port.close()


def _two_consumers(fixture, assessor):
    draft, registrations, binding = _parent_inputs(fixture)
    requirement, = draft.requirements
    connection, = draft.connections
    second_requirement = replace(requirement, requirement_id=requirement.requirement_id + ".second")
    second_connection = replace(connection, connection_id=connection.connection_id + ".second",
        requirement_id=second_requirement.requirement_id)
    draft = replace(draft, requirements=(requirement, second_requirement), connections=(connection, second_connection))
    registrations = tuple(replace(value, qualified_parent_assessor=assessor) if value.qualified_parent_assessor else value
        for value in registrations)
    return draft, registrations, binding


def test_second_consumer_replays_live_authority_after_first_read_even_when_all_files_are_unchanged(parent_fixture, monkeypatch):
    from empirical_lawhood.api import recursive_qualified_parents as owner

    fixture, observed = parent_fixture, []
    original_invocations = fixture.executor.invocations
    expiry = fixture.package.execution_authority.expires_at_utc
    assert expiry is not None

    class SelectedClock:
        current = datetime(2026, 10, 15, tzinfo=UTC)

        @classmethod
        def now(cls, timezone):
            assert timezone is UTC
            return cls.current

    def assess(**kwargs):
        _assess_synthetic_parent(**kwargs)
        observed.append(kwargs["requirement"].requirement_id)
        SelectedClock.current = datetime(2028, 10, 15, tzinfo=UTC)

    draft, registrations, binding = _two_consumers(fixture, assess)
    monkeypatch.setattr(owner, "datetime", SelectedClock)
    with pytest.raises(PermissionError, match="authority has expired"):
        owner.authenticate_recursive_qualified_parents(spec_bindings=(binding,), draft=draft,
            artifact_writer=fixture.plane, registrations=registrations,
            output_codecs=fixture.handoff.compilation.output_codecs)
    assert observed == [draft.requirements[0].requirement_id]
    assert fixture.executor.invocations == original_invocations
