"""External array-format effects over domain-owned scientific calculations."""
from hashlib import sha256
import io
from collections.abc import Mapping
import h5py  # type: ignore[import-untyped]
import numpy as np
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.domains.matrix.matrix_preparation.native_inputs import CONTEXTS, preparation_roots
from empirical_lawhood.adapters.simulators.six_matrix_response.response_source import response_hdf5_group, response_hdf5_read_text, response_hdf5_text, response_hdf5_writer
from empirical_lawhood.domains.matrix.matrix_preparation.contracts import PreparationProjectionRecord
from empirical_lawhood.adapters.simulators.matrix_preparation.projection import _verify_hdf5, read_preparation_projection

from empirical_lawhood.domains.matrix.matrix_preparation.data import Array, METHOD_MAXIMUM_BYTES, METHOD_METADATA, ProjectedContext, stack_projected_arrays

def collect_projected_context(
    context: str, values: tuple[tuple[PreparationProjectionRecord, bytes], ...], *, role: str
) -> ProjectedContext:
    if context not in CONTEXTS or role not in ("observable", "privileged", "prospective-task"):
        raise ValueError("projection collection changes context or information role")
    roots = tuple(r for r in preparation_roots() if r.context == context)
    by_slot = {(r.root, r.refinement): (r, payload) for r, payload in values}
    if (
        len(values) != 128
        or len(by_slot) != 128
        or set(by_slot) != {(root, r) for root in roots for r in (1, 2)}
    ):
        raise ValueError("projection collection must retain all 64 roots and both numerical views")
    reports = tuple(by_slot[(root, r)][0] for root in roots for r in (1, 2))
    if len({r.projection_config for r in reports}) != 1:
        raise ValueError("projection collection mixes observer configurations")
    decoded = [
        read_preparation_projection(*by_slot[(root, r)], role=role)
        for root in roots
        for r in (1, 2)
    ]
    return stack_projected_arrays(context, roots, reports, role, decoded)


def write_method_arrays(
    schema: str, context: str, config: ObjectIdentity, groups: Mapping[str, Mapping[str, Array]]
) -> bytes:
    if context not in CONTEXTS or len(groups) > 32:
        raise ValueError("method arrays exceed their fixed context/group census")
    output = io.BytesIO()
    with response_hdf5_writer(output) as artifact:
        for key, value in {
            "schema": schema,
            "empirical_lawhood_payload_schema": schema,
            "context": context,
            "config_sha256": config.object_fingerprint,
            **METHOD_METADATA,
        }.items():
            response_hdf5_text(artifact, key, value)
        for group_name in sorted(groups):
            group = response_hdf5_group(artifact, group_name)
            for name, array in sorted(groups[group_name].items()):
                group.create_dataset(
                    name, data=np.asarray(array, dtype=np.float64), track_times=False
                )
    payload = output.getvalue()
    if len(payload) > METHOD_MAXIMUM_BYTES:
        raise ValueError("method arrays exceed the declared 16-MiB artifact bound")
    return payload


def read_method_arrays(
    payload: bytes, *, schema: str, context: str, config: ObjectIdentity, expected_sha256: str
) -> dict[str, dict[str, Array]]:
    if len(payload) > METHOD_MAXIMUM_BYTES or sha256(payload).hexdigest() != expected_sha256:
        raise ValueError("method data differs from its immutable report")
    with h5py.File(io.BytesIO(payload), "r") as artifact:
        _verify_hdf5(artifact, METHOD_MAXIMUM_BYTES)
        if (
            response_hdf5_read_text(artifact, "schema") != schema
            or response_hdf5_read_text(artifact, "context") != context
            or response_hdf5_read_text(artifact, "config_sha256") != config.object_fingerprint
        ):
            raise ValueError("method data changes its context/config/information role")
        result = {}
        for name in artifact:
            group = artifact[name]
            if not isinstance(group, h5py.Group):
                raise ValueError("method data requires the exact bounded group schema")
            arrays = {}
            for key in group:
                value = group[key]
                if not isinstance(value, h5py.Dataset) or value.dtype != np.dtype("float64"):
                    raise ValueError("method arrays must be nonexecuting float64 data")
                arrays[key] = np.asarray(value[...])
            result[name] = arrays
    return result
