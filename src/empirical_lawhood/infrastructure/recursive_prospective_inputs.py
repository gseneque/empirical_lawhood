# SPDX-License-Identifier: MPL-2.0
"""Bounded exact content-addressed inputs for common prospective providers."""
from empirical_lawhood.runtime.artifacts import ArtifactProfile, is_canonical_json_media_type
from empirical_lawhood.runtime.providers import ExternalInputPayload, MAX_EXTERNAL_INPUT_CHUNK_BYTES
from empirical_lawhood.runtime.recursive_storage_codecs import resolve_storage_codec, validate_storage_codecs
from empirical_lawhood.runtime.source_resolution import ContentAddressedInputKind, ContentAddressedInputRequirement
from .candidate_sources import ExternalContentAddressedInputResolver


class _MaterializedOperandSource:
    """Expose one already bounded materialization through existing chunk ports."""
    def __init__(self, payload):
        self.payload = payload
        self.consumed = False

    def chunks(self, maximum_chunk_bytes):
        if self.consumed or not 0 < maximum_chunk_bytes <= MAX_EXTERNAL_INPUT_CHUNK_BYTES:
            raise ValueError('prospective source is consumed or has an invalid chunk bound')
        self.consumed = True
        for offset in range(0, len(self.payload), maximum_chunk_bytes):
            yield self.payload[offset:offset + maximum_chunk_bytes]

    def close(self):
        self.payload = b''
        self.consumed = True


class RecursiveContentInputSupplier:
    def __init__(self, *, root, operands, validate_payload=None, storage_codecs=()):
        self.resolver = ExternalContentAddressedInputResolver(root)
        self.operands = {operand.logical_artifact_id: operand for operand in operands}
        if len(self.operands) != len(operands):
            raise ValueError('prospective source inventory repeats an operand')
        if validate_payload is not None and not callable(validate_payload):
            raise TypeError('prospective input validation requires a code-owned callable')
        self.validate_payload = validate_payload
        self.storage_codecs = validate_storage_codecs(storage_codecs)

    def resolve_input(self, spec):
        operand = self.operands.get(spec.logical_artifact_id)
        if operand is None:
            raise ValueError('prospective task names an unbound exact operand')
        if (spec.expected_content_sha256 is not None and spec.expected_content_sha256 != operand.content_sha256
            or spec.expected_payload_schema != operand.payload_schema
            or spec.expected_media_type is not None and spec.expected_media_type != operand.media_type
            or spec.expected_size_bytes is not None and spec.expected_size_bytes != operand.size_bytes
            or spec.expected_outcome_access is not None and spec.expected_outcome_access is not operand.outcome_access
            or spec.expected_visibility_ceiling is not None and spec.expected_visibility_ceiling is not operand.visibility_ceiling
            or spec.identity_scope_sha256 is not None and not any(parent.identity.object_fingerprint == spec.identity_scope_sha256
                                                                   for parent in operand.lineage_parents)):
            raise ValueError('prospective input changes frozen bytes, access or enclosing identity')
        codec = resolve_storage_codec(self.storage_codecs,
            payload_schema=operand.payload_schema, media_type=operand.media_type)
        if codec is not None:
            if codec.maximum_bytes is not None and operand.size_bytes > codec.maximum_bytes:
                raise ValueError('prospective input exceeds its exact registered physical codec bound')
            profile = codec.profile
        elif is_canonical_json_media_type(operand.media_type):
            profile = ArtifactProfile.CANONICAL_JSON
        else:
            raise ValueError('prospective binary input lacks an exact registered physical codec')
        requirement = ContentAddressedInputRequirement('recursive-input.' + operand.logical_artifact_id,
            ContentAddressedInputKind.SOURCE_MATERIALIZATION, operand.content_sha256, operand.payload_schema,
            operand.media_type, operand.size_bytes, operand.size_bytes, operand.outcome_access, operand.visibility_ceiling)
        resolved = self.resolver.resolve(requirement, materialize=True)
        if resolved.payload is None:
            raise ValueError('prospective input was not materialized within its exact bound')
        if self.validate_payload is not None:
            if self.validate_payload(logical_artifact_id=operand.logical_artifact_id, payload=resolved.payload) is not None:
                raise ValueError('prospective input validator must raise on refusal or return None')
        return ExternalInputPayload(logical_artifact_id=operand.logical_artifact_id,
            payload_schema=operand.payload_schema, profile=profile, media_type=operand.media_type,
            source=_MaterializedOperandSource(resolved.payload), size_bytes=operand.size_bytes,
            source_sha256=operand.content_sha256, maximum_bytes=operand.size_bytes,
            maximum_chunk_bytes=min(operand.size_bytes, MAX_EXTERNAL_INPUT_CHUNK_BYTES),
            visibility_ceiling=operand.visibility_ceiling, outcome_access=operand.outcome_access,
            parent_visibility_ceilings=tuple(sorted((parent.visibility_ceiling for parent in operand.lineage_parents), key=lambda value: value.value)),
            lineage_parents=operand.lineage_parents)
