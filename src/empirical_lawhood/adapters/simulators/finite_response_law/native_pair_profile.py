# SPDX-License-Identifier: MPL-2.0
"""The finite-response native pair's closed array layout and storage contract."""

from math import prod

from empirical_lawhood.storage.artifact_validation import (
    HDF5AttributeContract,
    HDF5AttributeKind,
    HDF5InventoryContract,
    HDF5ObjectContract,
    HDF5ObjectKind,
)


PREFIX_REFERENCE_TICKS = 4096
MAXIMUM_SAMPLED_ROWS = PREFIX_REFERENCE_TICKS // 16 + 1


def native_pair_array_layout(rows: int, intervals: int) -> dict[str, tuple[tuple[int, ...], str]]:
    """Return the exact array shapes and dtypes for one numerical view."""
    return {
        "ticks": ((rows,), "<i8"),
        "positions": ((rows, 2, 3, 4, 4), "<c16"),
        "momenta": ((rows, 2, 3, 4, 4), "<c16"),
        "couplings": ((rows, 2), "<f8"),
        "transfer": ((rows, 15, 15), "<f8"),
        "transfer_known": ((rows,), "bool"),
        "realized_trace": ((intervals, 9), "<f8"),
    }


def finite_response_pair_contract() -> HDF5InventoryContract:
    """Bind both views, causal clocks and checkpoint bounds before decoding."""
    from empirical_lawhood.adapters.simulators.finite_response_law.native_artifact import (
        MAXIMUM_CHECKPOINT_BYTES, MAXIMUM_PAIR_BYTES, METADATA, NATIVE_PAIR_SCHEMA,
    )

    attributes = tuple(
        HDF5AttributeContract(key, HDF5AttributeKind.UTF8, value) for key, value in sorted(METADATA.items())
    )
    objects = [HDF5ObjectContract("/", HDF5ObjectKind.GROUP, None, None, attributes)]
    element_counts = []
    lower = native_pair_array_layout(1, 0)
    lower["checkpoint"] = ((0,), "uint8")
    for name, refinement in (("primary", 1), ("half", 2)):
        objects.append(HDF5ObjectContract(f"/{name}", HDF5ObjectKind.GROUP, None, None))
        upper = native_pair_array_layout(MAXIMUM_SAMPLED_ROWS, PREFIX_REFERENCE_TICKS * refinement)
        upper["checkpoint"] = ((MAXIMUM_CHECKPOINT_BYTES,), "uint8")
        for key, (shape, dtype) in lower.items():
            maximum = upper[key][0]
            objects.append(HDF5ObjectContract(
                f"/{name}/{key}", HDF5ObjectKind.DATASET, dtype, shape, maximum_shape=maximum,
            ))
            element_counts.append(prod(maximum))
    return HDF5InventoryContract(
        payload_schema=NATIVE_PAIR_SCHEMA,
        objects=tuple(sorted(objects, key=lambda item: item.path)),
        maximum_objects=len(objects),
        maximum_dataset_elements=max(element_counts),
        maximum_total_elements=sum(element_counts),
        maximum_decoded_bytes=MAXIMUM_PAIR_BYTES,
        maximum_name_bytes=sum(len(item.path.encode()) for item in objects if item.path != "/"),
        maximum_attribute_bytes=sum(len(key.encode()) + len(value.encode()) for key, value in METADATA.items()),
    )
