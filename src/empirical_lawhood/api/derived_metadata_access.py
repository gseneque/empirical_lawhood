# SPDX-License-Identifier: MPL-2.0
"""Current exact-byte access to code-owned derived metadata.

These receipts establish decoding/access under an explicitly selected root.
They establish no scientific source gate, issue, reveal, sampling or freshness.
"""
from hashlib import sha256

from empirical_lawhood.infrastructure.publication_metadata import authenticate_published_materialization
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes
from empirical_lawhood.planning.study_authoring import (
    MaterializationQualificationReceipt, SourceAccessDisposition, SourceMaterializationRole, StudyDraft,
)
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteResult
from empirical_lawhood.runtime.source_pipelines import SourcePipelineProfile
from empirical_lawhood.runtime.source_resolution import SourceMaterializationConfig, SourceReadMode


def _require_scope(root, source_profile, observation_operator):
    if type(root) is not StudyDraft or root.system is None or root.experiment is None:
        raise TypeError("derived metadata requires its exact selected scientific root")
    if source_profile is not None:
        if type(source_profile) is not SourcePipelineProfile or observation_operator is not None:
            raise TypeError("derived metadata requires exactly one typed observation context")
        if source_profile.evidence_world_id != root.system.world.world_id:
            raise ValueError("derived metadata cannot reinterpret its original source evidence world")
        observation_operator = source_profile.observation_operator
    if type(observation_operator) is not ObjectIdentity:
        raise TypeError("derived metadata requires its exact observation operator")
    observation_operator.__post_init__()
    return observation_operator


def _semantic_access(*, external, root, version, source_profile=None, observation_operator=None):
    observation_operator = _require_scope(root, source_profile, observation_operator)
    pin = ObjectIdentity(external.logical_artifact_id, external.payload_schema, version, external.expected_content_sha256)
    semantic_scope = (root.system.world.world_id, observation_operator,
        tuple(value.view_id for value in root.system.numerical_views),
        tuple(sorted({value.native_unit for value in root.system.quantities})),
        tuple(sorted({value.coordinate_frame for value in root.system.quantities})),
        tuple(value.clock_id for value in root.system.clocks), root.system.relation.relation_id,
        root.experiment.obligations.validity.validity_id, root.experiment.obligations.uncertainty.uncertainty_id)
    suffix = sha256(canonical_json_bytes((external.input_id, pin, semantic_scope))).hexdigest()
    config_suffix = sha256(canonical_json_bytes((external.input_id, pin))).hexdigest()
    role = (SourceMaterializationRole.RETAINED_HISTORY if external.scientific_role == "HISTORY"
        else SourceMaterializationRole.CALIBRATION if external.scientific_role == "QUALIFICATION"
        else SourceMaterializationRole.OBSERVATION_STREAM)
    config = SourceMaterializationConfig("source-config.derived-metadata." + config_suffix, external.input_id,
        role, pin.object_fingerprint,
        external.maximum_size_bytes, external.maximum_size_bytes, external.payload_schema, external.media_type,
        SourceReadMode.ORDINARY_BOUNDED, external.outcome_access, external.visibility_ceiling)
    receipt = MaterializationQualificationReceipt("qualification.derived-metadata." + suffix, external.input_id,
        pin, pin.object_fingerprint, root.system.world.world_id, observation_operator,
        tuple(value.view_id for value in root.system.numerical_views),
        tuple(sorted({value.native_unit for value in root.system.quantities})),
        tuple(sorted({value.coordinate_frame for value in root.system.quantities})),
        tuple(value.clock_id for value in root.system.clocks), root.system.relation.relation_id,
        root.experiment.obligations.validity.validity_id, root.experiment.obligations.uncertainty.uncertainty_id,
        SourceAccessDisposition.VERIFIED_ACCESS, external.outcome_access, external.visibility_ceiling)
    return config, receipt


def validate_derived_metadata_access(*, external, root, version, config, qualification,
        source_profile=None, observation_operator=None):
    """Cold semantic replay; actual source access still needs the publication reader."""
    if (config, qualification) != _semantic_access(external=external, root=root,
            source_profile=source_profile, observation_operator=observation_operator, version=version):
        raise ValueError("derived metadata access changes exact bytes, source or selected semantic scope")


def _require_canonical_metadata_binding(*, publication, record, external, root,
        source_profile=None, observation_operator=None):
    """Pure exact binding/context checks, shared by singular and closed access."""
    if (not isinstance(record, CanonicalRecord) or type(publication) is not ArtifactWriteResult
            or publication.logical.profile is not ArtifactProfile.CANONICAL_JSON
            or publication.logical.media_type != "application/json"
            or external.media_type != "application/json"
            or publication.logical.logical_artifact_id != external.logical_artifact_id
            or (publication.logical.payload_schema, publication.logical.content_sha256,
                publication.materialization.size_bytes) !=
                (external.payload_schema, external.expected_content_sha256, external.maximum_size_bytes)
            or (record.SCHEMA, record.fingerprint(), len(record.canonical_bytes())) !=
                (external.payload_schema, external.expected_content_sha256, external.maximum_size_bytes)):
        raise ValueError("derived metadata publication substitutes the actual canonical input")
    if (publication.logical.outcome_access is not external.outcome_access
            or publication.logical.visibility_ceiling is not external.visibility_ceiling):
        raise ValueError("derived metadata publication cannot relabel outcome access")
    _require_scope(root, source_profile, observation_operator)


def _read_canonical_metadata_binding(*, writer, publication, record, external):
    """Strictly decode one freshly authenticated selected canonical payload."""
    raw = read_bounded_bytes(writer.root.resolve(publication.materialization.relative_path, for_write=False),
        maximum_bytes=external.maximum_size_bytes)
    decoded = decode_canonical_bytes(raw, type(record), maximum_bytes=external.maximum_size_bytes)
    if decoded.canonical_bytes() != raw or decoded != record:
        raise ValueError("derived metadata publication is not the exact decoded code-owned object")


def derive_canonical_metadata_access(*, writer, publication, record, external, root,
        source_profile=None, observation_operator=None):
    """Read and decode an actual publication before creating a new access receipt.

    The domain caller owns deterministic derivation from authenticated original
    operands. This helper proves only that the new exact canonical object was
    actually published and decoded under that caller's selected root and exact
    observation operator. A pipeline profile remains supported for callers that
    own a real pipeline; metadata access itself does not execute that pipeline.
    """
    _require_canonical_metadata_binding(publication=publication, record=record, external=external,
        root=root, source_profile=source_profile, observation_operator=observation_operator)
    authenticate_published_materialization(writer, publication)
    _read_canonical_metadata_binding(writer=writer, publication=publication, record=record, external=external)
    return _semantic_access(external=external, root=root, source_profile=source_profile,
        observation_operator=observation_operator, version=record.VERSION)
