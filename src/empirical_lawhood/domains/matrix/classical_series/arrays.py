# SPDX-License-Identifier: MPL-2.0
"""Compact native operands through EL's existing authenticated framed arrays.

JSON retains scientific names and small scalar metadata. Numerical list values
are retained as exact binary arrays in bounded NPZ leaves within one streamed
container. Root population size is not a transport limit.
"""
from dataclasses import replace
from hashlib import sha256
from math import prod

import numpy as np

from empirical_lawhood.domains.matrix.matrix_array_chunks import (
    ChunkedMatrixArrays, MatrixArrayInterval, encode_chunk, whole_member,
    framed_artifact, iter_framed_bytes, iter_framed_chunk_arrays,
)
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from .records import json_text

_ARRAY = "__classical_matrix_array__"
_LEAF_ELEMENTS = 500_000  # Buffer policy; every complete array is split, never truncated.


def encode_acquisition(product, *, artifact_id, allow_empty=False):
    """Separate array bytes without changing any native numeric value or shape."""
    if product.array_manifest is not None:
        raise ValueError("acquisition arrays have already been encoded")
    values = {}

    def visit(value):
        if isinstance(value, dict):
            if _ARRAY in value:
                raise ValueError("native metadata uses a reserved physical array marker")
            return {key: visit(item) for key, item in value.items()}
        if isinstance(value, list):
            try:
                array = np.asarray(value)
            except ValueError:
                array = None
            if (array is not None and array.size >= 8 and array.dtype.kind in "fib"
                    and array.dtype.itemsize <= 8):
                kind = "|b1" if array.dtype.kind == "b" else "<i8" if array.dtype.kind == "i" else "<f8"
                array = np.asarray(array, dtype=kind, order="C")
                if np.isfinite(array).all() and json_text(array.tolist()) == json_text(value):
                    name = "array." + str(len(values)).zfill(8)
                    values[name] = array.reshape(-1)
                    return {_ARRAY: name, "shape": list(array.shape), "dtype": kind}
            return [visit(item) for item in value]
        return value

    metadata = visit(product.payload)
    if not values and not allow_empty:
        # The native system always has a physical receiver, including failed roots.
        raise ValueError("native acquisition omitted its complete physical operand census")
    producers = (product.config.specification,)
    chunks, payloads, members = [], {}, []
    for name, array in sorted(values.items()):
        members.append(whole_member(name, array))
        for start in range(0, len(array), _LEAF_ELEMENTS):
            stop = min(len(array), start + _LEAF_ELEMENTS)
            chunk_id = "chunk." + sha256(artifact_id.encode()).hexdigest() + "." + str(len(chunks)).zfill(8)
            raw, chunk = encode_chunk({name: array[start:stop]}, (MatrixArrayInterval(name, start, stop),),
                chunk_id=chunk_id, artifact_id=chunk_id + ".npz", producers=producers)
            chunks.append(chunk)
            payloads[chunk.array_artifact.artifact_id] = raw
    manifest = ChunkedMatrixArrays("arrays." + sha256(artifact_id.encode()).hexdigest(),
        product.config.specification, ObjectIdentity.from_record("assignment." + product.config.assignments[0].unit_id,
            product.config.assignments[0]), tuple(members), tuple(chunks), producers)

    def fetch(identity):
        yield payloads[identity.artifact_id]

    container = framed_artifact(manifest, fetch, artifact_id=artifact_id)
    encoded = replace(product, payload_json=json_text(metadata), array_manifest=manifest, array_artifact=container)
    return encoded, payloads


def iter_encoded_bytes(product, payloads, *, maximum_chunk_bytes=1024**2):
    def fetch(identity):
        yield payloads[identity.artifact_id]
    yield from iter_framed_bytes(product.array_manifest, fetch, maximum_chunk_bytes=maximum_chunk_bytes)


def decode_acquisition(product, reader):
    """Finish all container/member checks before returning a scientific operand."""
    if product.array_manifest is None or product.array_artifact is None:
        raise ValueError("native root requires its exact binary matrix operand companion")
    values = {member.name: np.empty(member.shape, dtype=member.dtype) for member in product.array_manifest.members}
    for chunk, arrays in iter_framed_chunk_arrays(product.array_manifest, product.array_artifact, reader.read):
        for interval in chunk.intervals:
            values[interval.name][interval.start:interval.stop] = arrays[interval.name]
    seen = set()

    def visit(value):
        if isinstance(value, dict):
            if _ARRAY in value:
                if set(value) != {_ARRAY, "shape", "dtype"}:
                    raise ValueError("native array layout adds undeclared interpretation")
                name = value[_ARRAY]
                if name not in values or name in seen:
                    raise ValueError("native array metadata omits or duplicates a scientific operand")
                seen.add(name)
                array = values[name]
                shape = value["shape"]
                if (not isinstance(shape, list) or any(type(n) is not int or n < 0 for n in shape)
                        or prod(shape) != array.size or value["dtype"] != array.dtype.str):
                    raise ValueError("native array metadata changes shape or exact numerical dtype")
                return array.reshape(tuple(shape)).tolist()
            return {key: visit(item) for key, item in value.items()}
        if isinstance(value, list):
            return [visit(item) for item in value]
        return value

    result = visit(product.metadata)
    if seen != set(values):
        raise ValueError("native metadata loses part of the complete scientific operand census")
    return result
