# SPDX-License-Identifier: MPL-2.0
"""Exact raw response actions, separate from historical absolute-mean tables.

The byte form is the existing donor build-receipt array digest preimage: ASCII
shape followed by contiguous little-endian float64 values. Shape is bound by
complete target/gene registries in the corrected freeze record.
"""

from hashlib import sha256

from .contracts import VirtualCellContractError


def encode_raw_prediction_deltas_v2(*, values, target_ids, gene_ids):
    import numpy as np

    data = np.ascontiguousarray(values, dtype="<f8")
    if data.shape != (len(target_ids), len(gene_ids)) or not np.all(np.isfinite(data)):
        raise VirtualCellContractError(
            "corrected raw actions change target/gene shape or contain nonfinite values"
        )
    if (
        not target_ids
        or tuple(sorted(set(target_ids))) != target_ids
        or not gene_ids
        or len(set(gene_ids)) != len(gene_ids)
    ):
        raise VirtualCellContractError(
            "corrected raw actions require complete unique ordered registries"
        )
    return str(data.shape).encode("ascii") + data.tobytes()


def decode_raw_prediction_deltas_v2(
    *, payload, target_ids, gene_ids, expected_sha256, maximum_bytes
):
    shape = len(target_ids), len(gene_ids)
    prefix = str(shape).encode("ascii")
    expected_size = len(prefix) + shape[0] * shape[1] * 8
    if (
        type(payload) is not bytes
        or type(maximum_bytes) is not int
        or maximum_bytes < expected_size
        or len(payload) != expected_size
        or not payload.startswith(prefix)
        or sha256(payload).hexdigest() != expected_sha256
    ):
        raise VirtualCellContractError(
            "corrected raw actions fail exact frozen shape, byte limit or digest"
        )
    import numpy as np

    values = np.frombuffer(payload, dtype="<f8", offset=len(prefix)).reshape(shape)
    if (
        encode_raw_prediction_deltas_v2(
            values=values, target_ids=target_ids, gene_ids=gene_ids
        )
        != payload
    ):
        raise VirtualCellContractError(
            "corrected raw actions fail exact canonical round trip"
        )
    return values
