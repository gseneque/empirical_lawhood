"""Read bounded clock and profile slices from selected FAIR-MAST Level 2 arrays.

SPDX-License-Identifier: MPL-2.0
"""

from collections.abc import Callable
from dataclasses import dataclass
import itertools
import json
import math

import numpy as np
import pyarrow


@dataclass(frozen=True)
class Level2Array:
    """A regular Zarr v3 float array with its clock on the final dimension."""

    shape: tuple[int, ...]
    chunk_shape: tuple[int, ...]
    dtype: np.dtype

    @classmethod
    def from_metadata(cls, payload: bytes, *, dimensions: tuple[str, ...], units: str):
        if len(payload) > 64 * 1024:
            raise ValueError("FAIR-MAST array metadata exceeds 64 KiB")
        value = json.loads(payload)
        codecs = value.get("codecs", [])
        if (value.get("zarr_format") != 3 or value.get("node_type") != "array"
                or value.get("data_type") not in ("float32", "float64")
                or value.get("dimension_names") != list(dimensions)
                or value.get("attributes", {}).get("units") != units
                or value.get("chunk_grid", {}).get("name") != "regular"
                or value.get("chunk_key_encoding") != {"name": "default", "configuration": {"separator": "/"}}
                or value.get("storage_transformers", []) or len(codecs) != 2
                or codecs[0] != {"name": "bytes", "configuration": {"endian": "little"}}
                or codecs[1].get("name") != "zstd"):
            raise ValueError("FAIR-MAST array differs from the selected units, dimensions or encoding")
        shape = tuple(value["shape"])
        chunk = tuple(value["chunk_grid"]["configuration"]["chunk_shape"])
        dtype = np.dtype(value["data_type"]).newbyteorder("<")
        if (not 1 <= len(shape) <= 2 or len(shape) != len(chunk) or len(shape) != len(dimensions)
                or any(type(n) is not int or n <= 0 for n in (*shape, *chunk))
                or math.prod(chunk) * dtype.itemsize > 8 * 1024**2):
            raise ValueError("FAIR-MAST array has unsupported or unbounded chunk geometry")
        return cls(shape, chunk, dtype)

    def read_interval(self, start: int, stop: int, fetch_chunk: Callable[[tuple[int, ...]], bytes]):
        """Read [start, stop) on the last axis using exact original compressed chunks."""
        if type(start) is not int or type(stop) is not int or not 0 <= start < stop <= self.shape[-1]:
            raise ValueError("FAIR-MAST interval lies outside the selected clock")
        result_shape = (*self.shape[:-1], stop - start)
        if math.prod(result_shape) * self.dtype.itemsize > 64 * 1024**2:
            raise ValueError("FAIR-MAST selected slice exceeds 64 MiB")
        result = np.empty(result_shape, dtype=self.dtype)
        lo = (0,) * (len(self.shape) - 1) + (start,)
        hi = (*self.shape[:-1], stop)
        ranges = [range(left // size, (right - 1) // size + 1)
                  for left, right, size in zip(lo, hi, self.chunk_shape, strict=True)]
        codec = pyarrow.Codec("zstd")
        chunk_bytes = math.prod(self.chunk_shape) * self.dtype.itemsize
        for index in itertools.product(*ranges):
            payload = fetch_chunk(index)
            if not isinstance(payload, bytes) or not 0 < len(payload) <= 8 * 1024**2:
                raise ValueError("FAIR-MAST compressed chunk exceeds the selected byte bounds")
            decoded = codec.decompress(payload, decompressed_size=chunk_bytes, asbytes=True)
            block = np.frombuffer(decoded, dtype=self.dtype).reshape(self.chunk_shape)
            source, target = [], []
            for tile, size, left, right in zip(index, self.chunk_shape, lo, hi, strict=True):
                origin = tile * size
                lower, upper = max(left, origin), min(right, origin + size)
                source.append(slice(lower - origin, upper - origin))
                target.append(slice(lower - left, upper - left))
            result[tuple(target)] = block[tuple(source)]
        result.setflags(write=False)
        return result
