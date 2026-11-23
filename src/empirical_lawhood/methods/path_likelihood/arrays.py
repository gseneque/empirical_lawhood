# SPDX-License-Identifier: MPL-2.0
"""Typed array companions for finite observation windows."""

import io
from hashlib import sha256
import zipfile

import numpy as np

from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile
from empirical_lawhood.storage.contracts.recursive_storage_codecs import (
    RecursiveStorageCodec,
)

SCHEMA = "empirical-lawhood/path-ensemble/numerical-arrays"
MEDIA = "application/octet-stream"
LIMIT = 128 * 1024**2


def validate_stream(stream, request, *, size):
    if (
        request.payload_schema != SCHEMA
        or request.media_type != MEDIA
        or not 0 < size <= LIMIT
    ):
        raise ValueError("invalid finite path-array container")
    with zipfile.ZipFile(stream) as archive:
        entries = archive.infolist()
        if (
            not entries
            or len(entries) > 256
            or len({i.filename for i in entries}) != len(entries)
            or sum(i.file_size for i in entries) > LIMIT
            or any(
                not i.filename.endswith(".npy")
                or "/" in i.filename
                or "\\" in i.filename
                or i.flag_bits & 1
                for i in entries
            )
        ):
            raise ValueError("invalid path-array member census")


CODEC = RecursiveStorageCodec(
    "path-ensemble.arrays",
    SCHEMA,
    "1.0.0",
    ArtifactProfile.RAW_SOURCE_BYTES,
    MEDIA,
    ".bin",
    validate_stream,
    LIMIT,
)


def encode(arrays):
    manifest = {}
    for name, raw in sorted(arrays.items()):
        value = np.asarray(raw)
        if (
            not name.isidentifier()
            or value.dtype.str not in ("<c16", "<f8", "<i8", "|b1")
            or not np.isfinite(value).all()
        ):
            raise ValueError("unsupported path-array name, dtype or numerical value")
        manifest[name] = [
            value.dtype.str,
            list(value.shape),
            sha256(value.tobytes()).hexdigest(),
        ]
    buffer = io.BytesIO()
    np.savez_compressed(buffer, **arrays)
    data = buffer.getvalue()
    if (
        len(data) > LIMIT
        or sum(np.asarray(value).nbytes for value in arrays.values())
        + 256 * len(arrays)
        > LIMIT
    ):
        raise ValueError(
            "path-array batch exceeds its declared size. Select fewer roots per batch"
        )
    return data, manifest


def decode(data, manifest):
    with np.load(io.BytesIO(data), allow_pickle=False) as archive:
        if set(archive.files) != set(manifest):
            raise ValueError("path-array census differs")
        result = {}
        for name, (dtype, shape, digest) in manifest.items():
            value = archive[name]
            if (
                value.dtype.str != dtype
                or list(value.shape) != shape
                or sha256(value.tobytes()).hexdigest() != digest
            ):
                raise ValueError("path-array coordinates or original bytes differ")
            result[name] = value
    return result
