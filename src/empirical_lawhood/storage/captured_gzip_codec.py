# SPDX-License-Identifier: MPL-2.0
"""Custody declaration shared by captured native arrays and whole archives.

The consumer owns decoding and its own finite input bound. The artifact writer
still enforces the selected custody policy, requested size, complete hash and
stream lifetime. A small array consumer cannot cap every producer's archive.
"""
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile
from empirical_lawhood.storage.contracts.recursive_storage_codecs import RecursiveStorageCodec


def validate_captured_gzip_custody(source, request, *, size):
    from empirical_lawhood.storage.artifact_stream_primitives import ArtifactIdentityConflict
    if (request.payload_schema != 'empirical-lawhood/source/capture-assured-uninterpreted-public-bytes'
            or request.profile is not ArtifactProfile.RAW_SOURCE_BYTES
            or request.media_type != 'application/gzip' or size <= 0
            or request.semantic_validation is not None):
        raise ArtifactIdentityConflict('captured gzip bytes change their uninterpreted custody contract')


CAPTURED_GZIP_CODEC = RecursiveStorageCodec('source.captured-gzip-custody',
    'empirical-lawhood/source/capture-assured-uninterpreted-public-bytes', '1.0.0',
    ArtifactProfile.RAW_SOURCE_BYTES, 'application/gzip', '.gz', validate_captured_gzip_custody)
