# SPDX-License-Identifier: MPL-2.0
"""Typed ordinary Matrix array access; scientific eligibility stays separate."""
from io import BytesIO
from dataclasses import dataclass

from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_NPZ_CODEC, MATRIX_STORAGE_CODECS
from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_records import MatrixPreparationInitialStateV2, initial_state_types
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_assay_method import MatrixPreparedAssayMethod
from empirical_lawhood.api.derived_metadata_access import (
    _semantic_access, validate_derived_metadata_access, _require_canonical_metadata_binding,
    _read_canonical_metadata_binding,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseArrays
from empirical_lawhood.adapters.methods.matrix_scheduled_history.continuation import ScheduledFullArrays
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays, NPZMemberSelection
from empirical_lawhood.infrastructure.publication_metadata import (
    authenticate_published_materialization, consume_published_materializations, supports_closed_publication_access,
)
from empirical_lawhood.kernel.matrix_inputs import SavedMatrixArrays
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, ArtifactWriteResult
from empirical_lawhood.runtime.recursive_storage_codecs import resolve_storage_codec


def _selection(arrays, external):
    if type(arrays) is MatrixPreparedAssayMethod:
        arrays.__post_init__()
        artifact, members = arrays.template_artifact, arrays.template_members
    elif type(arrays) is ScheduledResponseArrays:
        arrays.__post_init__()
        if arrays.role != "TEMPLATES":
            raise TypeError("array access accepts only scheduled response template operands")
        artifact, members = arrays.array_artifact, arrays.members
    elif type(arrays) in (SavedMatrixArrays, ScheduledFullArrays, *initial_state_types()):
        arrays.__post_init__()
        artifact, members = arrays.array_artifact, arrays.members
    else:
        raise TypeError("array access requires its exact original saved-array, full-history, initial-state, assay or scheduled-template owner")
    selected = NPZMemberSelection(artifact, members)
    selected.__post_init__()
    codec = resolve_storage_codec(MATRIX_STORAGE_CODECS, payload_schema=external.payload_schema,
        media_type=external.media_type, record_version=MATRIX_NPZ_CODEC.record_version)
    if (codec is not MATRIX_NPZ_CODEC or (artifact.payload_schema, artifact.media_type, artifact.sha256, artifact.size_bytes)
            != (external.payload_schema, external.media_type, external.expected_content_sha256, external.maximum_size_bytes)):
        raise ValueError("array access changes original typed codec, byte identity or complete size")
    return selected, codec


def validate_derived_matrix_array_access(*, arrays, external, root, config, qualification,
        source_profile=None, observation_operator=None):
    """Cold byte/member/context selectors; original source and publication still authenticate separately."""
    _, codec = _selection(arrays, external)
    validate_derived_metadata_access(external=external, root=root, source_profile=source_profile,
        observation_operator=observation_operator, version=codec.record_version,
        config=config, qualification=qualification)


def validate_matrix_array_input_bytes(*, raw, arrays, external):
    """Safe registered physical codec plus exact original complete values."""
    selected, codec = _selection(arrays, external)
    request = ArtifactWriteRequest(external.logical_artifact_id, "validated/input.npz", external.payload_schema,
        codec.profile, external.media_type, "array-access.validation", "validated", raw,
        external.visibility_ceiling, (), external.outcome_access)
    codec.validate_stream(BytesIO(raw), request, size=len(raw))
    values = decode_matrix_arrays(raw, selected)
    if type(arrays) is MatrixPreparationInitialStateV2:
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_initialization_science import validate_initial_state
        validate_initial_state(arrays, values)


def _require_matrix_array_binding(*, publication, arrays, external):
    """Pure original typed array/publication checks."""
    _, codec = _selection(arrays, external)
    if (type(publication) is not ArtifactWriteResult
            or publication.logical.logical_artifact_id != external.logical_artifact_id
            or publication.logical.profile is not ArtifactProfile.MATRIX_ARRAY_NPZ
            or (publication.logical.payload_schema, publication.logical.media_type,
                publication.logical.content_sha256, publication.materialization.size_bytes,
                publication.logical.outcome_access, publication.logical.visibility_ceiling) !=
                (external.payload_schema, external.media_type, external.expected_content_sha256,
                    external.maximum_size_bytes, external.outcome_access, external.visibility_ceiling)):
        raise ValueError("array access publication changes logical identity, physical bytes or selected outcome scope")
    return codec


def _read_matrix_array_binding(*, writer, publication, arrays, external):
    """Validate every original member and value after complete custody access."""
    raw = read_bounded_bytes(writer.root.resolve(publication.materialization.relative_path, for_write=False),
        maximum_bytes=external.maximum_size_bytes)
    validate_matrix_array_input_bytes(raw=raw, arrays=arrays, external=external)


def derive_matrix_array_access(*, writer, publication, arrays, external, root,
        source_profile=None, observation_operator=None):
    """Verify actual published complete values before returning fresh ACCESS-only records.

    The caller authenticates the original scientific source/producer chain.
    This owner validates actual bytes and the exact original typed member,
    shape, dtype, finite and hash census; it does not infer any qualification.
    """
    codec = _require_matrix_array_binding(publication=publication, arrays=arrays, external=external)
    # Validate context before payload I/O; no receipt is returned until all
    # actual source, publication, safe codec and complete value checks pass.
    access = _semantic_access(external=external, root=root, source_profile=source_profile,
        observation_operator=observation_operator, version=codec.record_version)
    authenticate_published_materialization(writer, publication)
    _read_matrix_array_binding(writer=writer, publication=publication, arrays=arrays, external=external)
    return access


@dataclass(frozen=True, slots=True)
class DerivedInputAccess:
    """Closed operational operand, not a scientific or authority record."""
    publication: ArtifactWriteResult
    operand: CanonicalRecord
    external: RecursiveExternalInput


def derive_matrix_input_access_batch(*, writer, inputs, root,
        source_profile=None, observation_operator=None):
    """Consume a closed metadata/template roster under one guarded boundary.

    Scientific and outcome scopes remain per operand. Every publication and its
    complete sibling set is authenticated before decoding. No qualification is
    returned if a callback or final freshness guard fails. Custom writer hooks
    retain their original owning verification route.
    """
    if type(inputs) is not tuple:
        raise TypeError("derived input access requires a closed tuple")
    accesses = []
    for item in inputs:
        if (type(item) is not DerivedInputAccess
                or type(item.external) is not RecursiveExternalInput):
            raise TypeError("derived input access requires exact operational operands")
        publication, operand, external = item.publication, item.operand, item.external
        if type(publication) is not ArtifactWriteResult:
            raise TypeError("derived input access requires its original publication")
        if publication.logical.profile is ArtifactProfile.CANONICAL_JSON:
            _require_canonical_metadata_binding(publication=publication, record=operand, external=external,
                root=root, source_profile=source_profile, observation_operator=observation_operator)
            version = operand.VERSION
        elif publication.logical.profile is ArtifactProfile.MATRIX_ARRAY_NPZ:
            version = _require_matrix_array_binding(publication=publication, arrays=operand,
                external=external).record_version
        else:
            raise ValueError("derived input access requires canonical metadata or original Matrix NPZ")
        accesses.append(_semantic_access(external=external, root=root, source_profile=source_profile,
            observation_operator=observation_operator, version=version))

    def consume(members):
        for item in inputs:
            publication, operand, external = item.publication, item.operand, item.external
            actual = members.get(publication.materialization.relative_path)
            if actual is None or (actual.logical, actual.materialization) != (
                    publication.logical, publication.materialization):
                raise ValueError("derived input access changes its authenticated member")
            if publication.logical.profile is ArtifactProfile.CANONICAL_JSON:
                _read_canonical_metadata_binding(writer=writer, publication=publication,
                    record=operand, external=external)
            else:
                _read_matrix_array_binding(writer=writer, publication=publication,
                    arrays=operand, external=external)
        return tuple(accesses)

    return consume_published_materializations(writer,
        tuple(item.publication for item in inputs), consume=consume)


def supports_derived_input_access_batch(writer, input_count):
    """Keep oversized closed rosters on their original singular access route."""
    return (type(input_count) is int and input_count > 0
        and supports_closed_publication_access(writer)
        and not writer.custody_limits.exceeds("publication_members", input_count))
