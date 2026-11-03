# SPDX-License-Identifier: MPL-2.0
"""Original segmented evidence stream's explicit physical contract."""

from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.recursive_storage_codecs import RecursiveStorageCodec


def validate_segment_stream(source, request, *, size):
    from empirical_lawhood.infrastructure.artifact_validation import validate_jsonl_stream
    return validate_jsonl_stream(source, request, size=size)


SEGMENT_STREAM_CODEC = RecursiveStorageCodec(
    "battery.segments.evidence-stream",
    "empirical-lawhood/battery-segmented-inquiry/segment-evidence-stream", "1.0.0",
    ArtifactProfile.JSONL_CHUNKS, "application/x-ndjson", ".jsonl", validate_segment_stream,
)
SEGMENT_STORAGE_CODECS = (SEGMENT_STREAM_CODEC,)


def validate_observation_raw_source(source, request, *, size):
    from empirical_lawhood.infrastructure.artifact_stream_primitives import ArtifactIdentityConflict
    if size <= 0 or request.semantic_validation is not None:
        raise ArtifactIdentityConflict("observation source requires its original uninterpreted byte custody")


OBSERVATION_RAW_SOURCE_CODEC = RecursiveStorageCodec(
    "battery.observation.raw-source", "empirical-lawhood/source/checksummed-uninterpreted-public-bytes",
    "1.0.0", ArtifactProfile.RAW_SOURCE_BYTES, "text/plain", ".txt", validate_observation_raw_source,
)
OBSERVATION_STORAGE_CODECS = (OBSERVATION_RAW_SOURCE_CODEC, SEGMENT_STREAM_CODEC)
