# SPDX-License-Identifier: MPL-2.0
"""Exact original Matrix physical codecs; scientific array joins remain local."""

import math
import zipfile

from empirical_lawhood.infrastructure.artifact_stream_primitives import ArtifactIdentityConflict
from empirical_lawhood.kernel.serialization import validate_stable_id
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.recursive_storage_codecs import RecursiveStorageCodec

MATRIX_FRAMED_ARRAY_SCHEMA = "empirical-lawhood/matrix-chunks/framed-array-container"
MATRIX_UNINTERPRETED_SOURCE_SCHEMA = "empirical-lawhood/source/checksummed-uninterpreted-public-bytes"

def validate_matrix_npz_stream(source, request, *, size):
    """Safe structure only; the consumer joins exact SavedMatrixArrays members."""
    import numpy as np

    semantic = request.semantic_validation
    if (request.payload_schema != MATRIX_ARRAY_SCHEMA or request.media_type != "application/x-npz"
            or not 0 < size <= MAXIMUM_MATRIX_ARRAY_BYTES
            or semantic is not None and (
                semantic.payload_schema != MATRIX_ARRAY_SCHEMA
                or semantic.profile is not ArtifactProfile.MATRIX_ARRAY_NPZ
                or semantic.top_level_keys or semantic.value_keys or semantic.field_bindings)):
        raise ArtifactIdentityConflict("matrix NPZ custody changes its closed transport contract")
    try:
        with zipfile.ZipFile(source) as archive:
            infos = archive.infolist()
            if (not 0 < len(infos) <= 256
                    or len({info.filename for info in infos}) != len(infos)
                    or sum(info.file_size for info in infos) > MAXIMUM_MATRIX_ARRAY_BYTES + 256 * 10000):
                raise ArtifactIdentityConflict("matrix NPZ member or expanded byte census differs")
            total = 0
            for info in infos:
                if (not info.filename.endswith(".npy") or info.flag_bits & 1
                        or info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)):
                    raise ArtifactIdentityConflict("matrix NPZ member type or compression is unsafe")
                validate_stable_id(info.filename[:-4], field_name="matrix array member")
                with archive.open(info) as stream:
                    version = np.lib.format.read_magic(stream)
                    if version == (1, 0):
                        shape, fortran, dtype = np.lib.format.read_array_header_1_0(stream, max_header_size=10000)
                    elif version == (2, 0):
                        shape, fortran, dtype = np.lib.format.read_array_header_2_0(stream, max_header_size=10000)
                    else:
                        raise ArtifactIdentityConflict("matrix NPZ has an unsupported NPY header")
                    if (dtype.hasobject or dtype.str not in ("<f8", "<c16", "<i8", "|b1")
                            or fortran or len(shape) > 12
                            or any(type(axis) is not int or not 0 <= axis <= 1000000 for axis in shape)):
                        raise ArtifactIdentityConflict("matrix NPZ dtype, axes or layout is unsafe")
                    remaining = math.prod(shape) * dtype.itemsize
                    total += remaining
                    if (total > MAXIMUM_MATRIX_ARRAY_BYTES
                            or stream.tell() + remaining != info.file_size):
                        raise ArtifactIdentityConflict("matrix NPZ changes its exact bounded value census")
                    while remaining:
                        chunk = stream.read(min(65536, remaining))
                        if not chunk:
                            raise ArtifactIdentityConflict("matrix NPZ member is truncated")
                        remaining -= len(chunk)
                    if stream.read(1):
                        raise ArtifactIdentityConflict("matrix NPZ member has trailing bytes")
    except ArtifactIdentityConflict:
        raise
    except (OSError, ValueError, EOFError, zipfile.BadZipFile) as error:
        raise ArtifactIdentityConflict("matrix NPZ structural validation refused the payload") from error


def validate_matrix_framed_stream(source, request, *, size):
    if (request.payload_schema != MATRIX_FRAMED_ARRAY_SCHEMA
            or request.profile is not ArtifactProfile.RAW_SOURCE_BYTES
            or request.media_type != "application/octet-stream" or size <= 0):
        raise ArtifactIdentityConflict("framed array custody changes its exact raw-byte contract")
    # Custody authenticates exact physical bytes. The selected domain reader
    # authenticates the complete leaves and scientific manifest before assessment.


def validate_original_source_stream(source, request, *, size):
    """Custody of original bytes; the scientific consumer owns their parsing."""
    from empirical_lawhood.infrastructure.artifact_stream_primitives import ArtifactIdentityConflict
    if (request.payload_schema != MATRIX_UNINTERPRETED_SOURCE_SCHEMA or request.profile is not ArtifactProfile.RAW_SOURCE_BYTES
            or request.media_type not in ("application/json", "application/x-hdf5", "application/zip", "text/x-python")
            or size <= 0 or request.semantic_validation is not None):
        raise ArtifactIdentityConflict("factor lifetime source changes its original uninterpreted byte contract")


MATRIX_FRAMED_CODEC = RecursiveStorageCodec(
    "matrix.arrays.framed", MATRIX_FRAMED_ARRAY_SCHEMA, "1.0.0",
    ArtifactProfile.RAW_SOURCE_BYTES, "application/octet-stream", ".bin",
    validate_matrix_framed_stream,
)
MATRIX_NPZ_CODEC = RecursiveStorageCodec(
    "matrix.arrays.npz", MATRIX_ARRAY_SCHEMA, "1.0.0", ArtifactProfile.MATRIX_ARRAY_NPZ,
    "application/x-npz", ".npz", validate_matrix_npz_stream, MAXIMUM_MATRIX_ARRAY_BYTES,
)
MATRIX_PYTHON_SOURCE_CODEC = RecursiveStorageCodec(
    "matrix.factor-lifetime.original-python", MATRIX_UNINTERPRETED_SOURCE_SCHEMA, "1.0.0",
    ArtifactProfile.RAW_SOURCE_BYTES, "text/x-python", ".py", validate_original_source_stream,
)
MATRIX_STORAGE_CODECS = (MATRIX_FRAMED_CODEC, MATRIX_NPZ_CODEC, MATRIX_PYTHON_SOURCE_CODEC)
