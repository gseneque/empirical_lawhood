# SPDX-License-Identifier: MPL-2.0
"""Actual NPZ custody and complete typed values; no scientific qualification."""
from dataclasses import replace
from hashlib import sha256

import numpy as np
import pytest

from empirical_lawhood.api import derived_array_access as owner
from empirical_lawhood.infrastructure.artifact_stream_primitives import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from tests.runtime_platform.test_candidate_compiler import _fixture
from tests.test_matrix_selected_opportunity import opportunity, transfer  # noqa: F401
from tests.test_matrix_source_evidence import source_case  # noqa: F401
from tests.test_recursive_public_service import _plane


@pytest.fixture
def array_access(tmp_path, opportunity, source_case):  # noqa: F811
    writer = _plane(tmp_path / "array-custody")
    root, _ = _fixture()
    profile = replace(source_case[0].pipeline_config.profile, evidence_world_id=root.system.world.world_id)
    initial = opportunity.sources.sources[0].initial
    raw, _ = encode_matrix_arrays({"positions": np.zeros((2, 3, 4, 4), dtype="<c16"),
        "momenta": np.zeros((2, 3, 4, 4), dtype="<c16")})
    assert (sha256(raw).hexdigest(), len(raw)) == (initial.array_artifact.sha256, initial.array_artifact.size_bytes)
    external = RecursiveExternalInput("source.current.array", "current.array.actual", initial.array_artifact.payload_schema,
        "application/x-npz", len(raw), OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, sha256(raw).hexdigest())
    publication = writer.write(ArtifactWriteRequest(external.logical_artifact_id, "derived/actual.npz", external.payload_schema,
        ArtifactProfile.MATRIX_ARRAY_NPZ, external.media_type, "array-access.disclosed", "derived", raw,
        external.visibility_ceiling, (), external.outcome_access))
    return writer, root, profile, initial, external, publication


def test_actual_array_access_authenticates_original_members_and_returns_only_new_contextual_access(array_access):
    writer, root, profile, initial, external, publication = array_access
    config, qualification = owner.derive_matrix_array_access(writer=writer, publication=publication, arrays=initial,
        external=external, root=root, source_profile=profile)
    owner.validate_derived_matrix_array_access(arrays=initial, external=external, root=root,
        source_profile=profile, config=config, qualification=qualification)
    assert qualification.materialization.object_id == external.logical_artifact_id != initial.array_artifact.artifact_id
    assert qualification.content_sha256 == initial.array_artifact.sha256
    from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_NPZ_CODEC
    assert qualification.materialization.object_version == MATRIX_NPZ_CODEC.record_version
    assert qualification.observation_operator == profile.observation_operator
    assert qualification.outcome_access is OutcomeAccess.OUTCOME_BLIND
    assert qualification.SCHEMA.endswith("/materialization-qualification-receipt")
    with pytest.raises(ValueError, match="exact bytes"):
        owner.validate_derived_matrix_array_access(arrays=initial, external=external, root=root, source_profile=profile,
            config=config, qualification=replace(qualification, content_sha256="f" * 64))


def test_actual_array_access_without_pipeline_keeps_original_values_and_cold_context(array_access):
    writer, root, profile, initial, external, publication = array_access
    legacy = owner.derive_matrix_array_access(writer=writer, publication=publication, arrays=initial,
        external=external, root=root, source_profile=profile)
    current = owner.derive_matrix_array_access(writer=writer, publication=publication, arrays=initial,
        external=external, root=root, observation_operator=profile.observation_operator)
    assert tuple(value.canonical_bytes() for value in current) == tuple(value.canonical_bytes() for value in legacy)
    config, qualification = current
    owner.validate_derived_matrix_array_access(arrays=initial, external=external, root=root,
        observation_operator=profile.observation_operator, config=config, qualification=qualification)
    with pytest.raises(ValueError, match="semantic scope"):
        owner.validate_derived_matrix_array_access(arrays=initial, external=external, root=root,
            observation_operator=replace(profile.observation_operator, object_fingerprint="d" * 64),
            config=config, qualification=qualification)
    writer.root.resolve(publication.materialization.relative_path, for_write=False).write_bytes(b"corrupt")
    with pytest.raises((ValueError, RuntimeError, ArtifactIdentityConflict)):
        owner.derive_matrix_array_access(writer=writer, publication=publication, arrays=initial,
            external=external, root=root, observation_operator=profile.observation_operator)


@pytest.mark.parametrize("change", ("foreign", "logical", "outcome", "world", "hash", "codec"))
def test_array_access_refuses_foreign_or_relabelled_selectors_before_writer_contact(array_access, change):
    _, root, profile, initial, external, publication = array_access
    if change == "foreign": initial = object()
    elif change == "logical": external = replace(external, logical_artifact_id="other.logical")
    elif change == "outcome": external = replace(external, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    elif change == "world": profile = replace(profile, evidence_world_id="world.foreign")
    elif change == "hash": external = replace(external, expected_content_sha256="f" * 64)
    else: external = replace(external, payload_schema="empirical-lawhood/testing/foreign-array")
    class Forbidden:
        def __getattr__(self, name): pytest.fail("refused selector contacted writer: " + name)
    with pytest.raises((TypeError, ValueError)):
        owner.derive_matrix_array_access(writer=Forbidden(), publication=publication, arrays=initial,
            external=external, root=root, source_profile=profile)


def test_corrupt_published_array_refuses_before_returning_access(array_access):
    writer, root, profile, initial, external, publication = array_access
    path = writer.root.resolve(publication.materialization.relative_path, for_write=False)
    path.write_bytes(b"corrupt")
    with pytest.raises((ValueError, RuntimeError, ArtifactIdentityConflict)):
        owner.derive_matrix_array_access(writer=writer, publication=publication, arrays=initial,
            external=external, root=root, source_profile=profile)


@pytest.mark.parametrize("change", ("members", "shape", "values"))
def test_actual_published_structure_must_match_original_complete_owned_array_contract(array_access, change):
    writer, root, profile, initial, external, _ = array_access
    positions = np.zeros((2, 3, 4, 3) if change == "shape" else (2, 3, 4, 4), dtype="<c16")
    if change == "values": positions.flat[0] = 1
    values = {"positions": positions, "momenta": np.zeros((2, 3, 4, 4), dtype="<c16")}
    if change == "members": values["undeclared"] = np.zeros((1,), dtype="<f8")
    raw, _ = encode_matrix_arrays(values)
    artifact = replace(initial.array_artifact, sha256=sha256(raw).hexdigest(), size_bytes=len(raw))
    arrays = replace(initial, array_artifact=artifact)  # original typed member/shape/hash census retained
    external = replace(external, expected_content_sha256=artifact.sha256, maximum_size_bytes=artifact.size_bytes)
    publication = writer.write(ArtifactWriteRequest(external.logical_artifact_id, "changed/" + change + ".npz",
        external.payload_schema, ArtifactProfile.MATRIX_ARRAY_NPZ, external.media_type, "array-access." + change,
        "changed", raw, external.visibility_ceiling, (), external.outcome_access))
    with pytest.raises(ValueError, match="members|axes|values|census"):
        owner.derive_matrix_array_access(writer=writer, publication=publication, arrays=arrays,
            external=external, root=root, source_profile=profile)


@pytest.fixture
def scheduled_template_access(array_access):
    """Disclosed coefficient bytes, actual publication; no source eligibility claim."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseArrays
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledSource
    from empirical_lawhood.kernel.provenance import ObjectIdentity

    writer, root, profile, initial, _, _ = array_access
    values = {
        "force_coefficients": np.arange(18, dtype="<f8").reshape(2, 3, 3),
        "generic_basis": np.ones((3, 4, 4), dtype="<c16"),
        "receiver_coefficients": np.ones((48, 2, 2, 3, 4), dtype="<f8"),
        "trace_coefficients": np.ones((2, 3), dtype="<f8"),
    }
    raw, members = encode_matrix_arrays(values)
    artifact = replace(initial.array_artifact, artifact_id="scheduled.disclosed.templates",
        sha256=sha256(raw).hexdigest(), size_bytes=len(raw))
    source = ObjectIdentity("source.scheduled.disclosed", ScheduledSource.SCHEMA, ScheduledSource.VERSION, "a" * 64)
    arrays = ScheduledResponseArrays("templates.scheduled.disclosed", "TEMPLATES", source, artifact,
        members, (source,), OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
    external = RecursiveExternalInput("source.scheduled.templates", artifact.artifact_id, artifact.payload_schema,
        artifact.media_type, artifact.size_bytes, arrays.outcome_access, arrays.visibility_ceiling, artifact.sha256)
    publication = writer.write(ArtifactWriteRequest(external.logical_artifact_id, "scheduled/templates.npz",
        external.payload_schema, ArtifactProfile.MATRIX_ARRAY_NPZ, external.media_type, "scheduled-template.disclosed",
        "scheduled", raw, external.visibility_ceiling, (), external.outcome_access))
    return writer, root, profile, arrays, external, publication, values


def test_actual_scheduled_template_owner_retains_source_members_and_access(scheduled_template_access):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseArrays

    writer, root, profile, arrays, external, publication, _ = scheduled_template_access
    original_bytes = arrays.canonical_bytes()
    config, qualification = owner.derive_matrix_array_access(writer=writer, publication=publication, arrays=arrays,
        external=external, root=root, source_profile=profile)
    owner.validate_derived_matrix_array_access(arrays=arrays, external=external, root=root,
        source_profile=profile, config=config, qualification=qualification)
    assert type(arrays) is ScheduledResponseArrays and arrays.canonical_bytes() == original_bytes
    assert arrays.producers == (arrays.source,)
    assert qualification.materialization.object_id == arrays.array_artifact.artifact_id
    assert qualification.content_sha256 == arrays.array_artifact.sha256
    assert qualification.outcome_access is OutcomeAccess.OUTCOME_BLIND
    assert qualification.visibility_ceiling is VisibilityCeiling.PROSPECTIVE


@pytest.mark.parametrize("role", ("FORECAST", "RESPONSES"))
def test_scheduled_template_access_does_not_admit_other_response_roles(scheduled_template_access, role):
    _, root, profile, arrays, external, publication, _ = scheduled_template_access
    arrays = replace(arrays, role=role, outcome_access=(OutcomeAccess.EVALUATION_SEALED
        if role == "RESPONSES" else OutcomeAccess.OUTCOME_BLIND))
    class Forbidden:
        def __getattr__(self, name): pytest.fail("refused scheduled role contacted writer: " + name)
    with pytest.raises(TypeError, match="template"):
        owner.derive_matrix_array_access(writer=Forbidden(), publication=publication, arrays=arrays,
            external=external, root=root, source_profile=profile)


@pytest.mark.parametrize("change", ("member", "shape", "values"))
def test_actual_scheduled_template_bytes_require_complete_original_contract(scheduled_template_access, change):
    writer, root, profile, arrays, external, _, original = scheduled_template_access
    values = {name: value.copy() for name, value in original.items()}
    if change == "member": values["undeclared"] = np.ones((1,), dtype="<f8")
    elif change == "shape": values["trace_coefficients"] = np.ones((2, 4), dtype="<f8")
    else: values["force_coefficients"].flat[0] = -1
    raw, _ = encode_matrix_arrays(values)
    artifact = replace(arrays.array_artifact, sha256=sha256(raw).hexdigest(), size_bytes=len(raw))
    arrays = replace(arrays, array_artifact=artifact)  # Keep original complete member/shape/value hashes.
    external = replace(external, expected_content_sha256=artifact.sha256, maximum_size_bytes=artifact.size_bytes)
    publication = writer.write(ArtifactWriteRequest(external.logical_artifact_id, "scheduled/changed-" + change + ".npz",
        external.payload_schema, ArtifactProfile.MATRIX_ARRAY_NPZ, external.media_type, "scheduled-template." + change,
        "scheduled", raw, external.visibility_ceiling, (), external.outcome_access))
    with pytest.raises(ValueError, match="members|axes|values|census"):
        owner.derive_matrix_array_access(writer=writer, publication=publication, arrays=arrays,
            external=external, root=root, source_profile=profile)
