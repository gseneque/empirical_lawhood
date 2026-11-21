# SPDX-License-Identifier: MPL-2.0
"""Authenticated engine-only successors of complete retained active preparations."""

from contextlib import ExitStack

from empirical_lawhood.domains.rubisco.rubisco_response.active_model_packet import ActiveModelPreparation
from empirical_lawhood.domains.rubisco.rubisco_response.active_model_rebinding import ActiveModelEngineRebinding, assess_engine_rebinding, rebind_prepared_engine
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.records.serialization import validate_relative_locator
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactStreamWriteRequest
from empirical_lawhood.api.domain_composition.rubisco_response.active_models import MAXIMUM_PREPARATION_BYTES


def _read(reader, path, kind):
    manifest = reader.read_manifest(path)
    if (manifest.logical.payload_schema != kind.SCHEMA
            or manifest.logical.profile is not ArtifactProfile.CANONICAL_JSON
            or manifest.logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or manifest.logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE):
        raise ValueError('engine rebinding requires the original exposed canonical publication')
    reader.verify_manifests((manifest,))
    raw = read_bounded_bytes(reader.root.resolve(path, for_write=False), maximum_bytes=MAXIMUM_PREPARATION_BYTES)
    record = decode_canonical_bytes(raw, kind, maximum_bytes=MAXIMUM_PREPARATION_BYTES)
    if record.fingerprint() != manifest.logical.content_sha256:
        raise ValueError('engine rebinding changes original canonical preparation bytes')
    return record


def _publish(writer, record, path):
    validate_relative_locator(path)
    if writer.root.resolve(path, for_write=True).exists():
        raise ValueError('engine rebinding requires fresh successor custody')
    size = record.canonical_size_bytes()
    if size > MAXIMUM_PREPARATION_BYTES:
        raise ValueError('engine rebinding exceeds its preparation publication bound')
    chunks = (chunk[offset:offset+2**20] for chunk in record.canonical_chunks()
        for offset in range(0, len(chunk), 2**20))
    writer.write_stream(ArtifactStreamWriteRequest(record.identity.object_id, path, record.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', record.identity.object_id,
        path.rsplit('/', 1)[0], chunks, maximum_bytes=size, maximum_chunk_bytes=min(size, 2**20),
        expected_size_bytes=size, expected_physical_sha256=record.fingerprint(),
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE))


def rebind_active_model_engine(*, original_relative_path, original_writer, original_prototype,
                              updated_prototype, representation, output_relative_path, artifact_writer):
    """Retain immutable seeds and assessments while selecting another numerical engine."""
    validate_relative_locator(output_relative_path)
    binding_path = output_relative_path+'.engine-binding.json'
    with original_writer.read_context() as reading:
        original = _read(reading, original_relative_path, ActiveModelPreparation)
        rebound, binding = rebind_prepared_engine(prepared=original, original_prototype=original_prototype,
            updated_prototype=updated_prototype, representation=representation)
        assessment = assess_engine_rebinding(binding=binding, original=original, rebound=rebound,
            original_prototype=original_prototype, updated_prototype=updated_prototype, representation=representation)
        _publish(artifact_writer, rebound, output_relative_path)
        _publish(artifact_writer, binding, binding_path)
    return dict(preparation=rebound, binding=binding, assessment=assessment,
        preparation_relative_path=output_relative_path, binding_relative_path=binding_path)


def read_active_model_engine_rebinding(*, original_relative_path, original_writer, original_prototype,
                                     updated_prototype, representation, preparation_relative_path,
                                     binding_relative_path, artifact_writer):
    """Authenticate both publications and compare originals through their final checks."""
    with ExitStack() as stack:
        original_reading = stack.enter_context(original_writer.read_context())
        updated_reading = stack.enter_context(artifact_writer.read_context())
        original = _read(original_reading, original_relative_path, ActiveModelPreparation)
        rebound = _read(updated_reading, preparation_relative_path, ActiveModelPreparation)
        binding = _read(updated_reading, binding_relative_path, ActiveModelEngineRebinding)
        assessment = assess_engine_rebinding(binding=binding, original=original, rebound=rebound,
            original_prototype=original_prototype, updated_prototype=updated_prototype, representation=representation)
    return dict(preparation=rebound, binding=binding, assessment=assessment)
