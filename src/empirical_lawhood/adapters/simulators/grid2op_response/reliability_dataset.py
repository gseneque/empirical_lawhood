# SPDX-License-Identifier: MPL-2.0
"""One reliability consumer over authenticated named arrays in bounded slices.

Integer coefficients and explicit positive Decimal quanta preserve exact energy
and runtime values across physical codecs. Quanta are encoding choices, never
scientific tolerances. Missing observations have a separate validity member.
"""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.kernel.datasets import ArrayDatasetManifest
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal
from empirical_lawhood.runtime.array_datasets import ArrayDatasetReader

from .contracts import Grid2OpNativeStep
from .reliability import assess_grid_episode_intervals, exact_decimal, validate_reliability_inputs
from .reliability_contracts import GridOperatingEpisodeContext, GridServiceInterval, _identity


ENERGY_MEMBERS = ("curtailed-energy-mwh", "delivered-energy-mwh", "demanded-energy-mwh", "redispatch-magnitude-mwh")
VALUE_MEMBERS = (*ENERGY_MEMBERS, "runtime-seconds")
EVENT_MEMBERS = ("fallback-used", "forecast-available", "supplier-refused")
DATASET_MEMBERS = tuple(sorted((*VALUE_MEMBERS, *(name + ".valid" for name in VALUE_MEMBERS), *EVENT_MEMBERS)))


@dataclass(frozen=True, slots=True)
class GridServiceDatasetSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/simulators/grid2op-response/service-dataset-selection"
    context: GridOperatingEpisodeContext
    dataset: ObjectIdentity
    native_steps: tuple[Grid2OpNativeStep, ...]
    energy_quantum_mwh: Decimal
    runtime_quantum_seconds: Decimal

    def __post_init__(self):
        if type(self.context) is not GridOperatingEpisodeContext:
            raise TypeError("grid dataset requires its original complete-unit context")
        self.context.__post_init__()
        _identity(self.dataset, ArrayDatasetManifest)
        if (type(self.native_steps) is not tuple
                or any(type(step) is not Grid2OpNativeStep for step in self.native_steps)):
            raise TypeError("grid dataset must preserve its unchanged actual native observations")
        for step in self.native_steps:
            step.__post_init__()
        for name in ("energy_quantum_mwh", "runtime_quantum_seconds"):
            value = getattr(self, name)
            validate_decimal(value, field_name=name, minimum=Decimal(0))
            if value == 0:
                raise ValueError("grid exact-value encoding quantum must be positive")


def iter_grid_service_dataset(reader, selection, *, source, receiver, requirement, block_rows):
    """Decode one exact logical schema without selecting a physical codec."""
    validate_reliability_inputs(source, receiver, requirement)
    if type(selection) is not GridServiceDatasetSelection or not isinstance(reader, ArrayDatasetReader):
        raise TypeError("grid dataset assessment needs its exact typed reader and selection")
    selection.__post_init__()
    if type(block_rows) is not int or block_rows < 1:
        raise ValueError("grid dataset needs an explicit positive operational slice bound")
    manifest = reader.manifest
    count = len(selection.native_steps)
    references = {row.object_id: row for row in manifest.scientific_references}
    if (manifest.identity != selection.dataset
            or tuple(row.name for row in manifest.members) != DATASET_MEMBERS
            or any(row.shape != (count,) or row.dtype not in (
                ("<i8", ">i8") if row.name in VALUE_MEMBERS else ("|u1",)) for row in manifest.members)
            or any(references.get(row.object_id) != row for row in (
                selection.context.identity, selection.context.source_binding, receiver.identity))):
        raise ValueError("grid dataset changes its exact named values, clock extent or original scientific references")
    chronic = next((row for row in source.chronic_bindings
        if ObjectIdentity.from_record(row.chronic_id, row) == selection.context.chronic), None)
    if chronic is None:
        raise ValueError("grid dataset source lacks its original chronic")
    largest_item = max(row.itemsize for row in manifest.members)
    rows_per_slice = min(block_rows, reader.maximum_slice_bytes // largest_item)
    if rows_per_slice < 1:
        raise ValueError("grid dataset selected slice allowance cannot hold one exact value")
    # The existing reader authenticates the complete logical stream inside the
    # session. Scientific reduction still consumes every original selected row.
    with reader.verified_session(block_size_bytes=reader.maximum_chunk_bytes) as verified:
        for start in range(0, count, rows_per_slice):
            stop = min(count, start + rows_per_slice)
            arrays = {name: verified.read_array_slice(name, start, stop) for name in DATASET_MEMBERS}
            if any(len(value) != stop - start for value in arrays.values()):
                raise ValueError("grid dataset reader omitted part of its selected exact slice")
            for offset, native_step in enumerate(selection.native_steps[start:stop]):
                values = {}
                for name in VALUE_MEMBERS:
                    coefficient, valid = int(arrays[name][offset]), int(arrays[name + ".valid"][offset])
                    if valid not in (0, 1) or not valid and coefficient:
                        raise ValueError("grid dataset validity masks or missing coefficients differ")
                    quantum = selection.runtime_quantum_seconds if name == "runtime-seconds" else selection.energy_quantum_mwh
                    values[name] = exact_decimal(Fraction(coefficient) * Fraction(quantum)) if valid else None
                events = {name: int(arrays[name][offset]) for name in EVENT_MEMBERS}
                if any(value not in (0, 1) for value in events.values()):
                    raise ValueError("grid dataset event mask differs from an exact native boolean")
                yield GridServiceInterval(native_step, chronic.timestep_seconds, values["demanded-energy-mwh"],
                    values["delivered-energy-mwh"], values["redispatch-magnitude-mwh"], values["curtailed-energy-mwh"],
                    values["runtime-seconds"], bool(events["forecast-available"]), bool(events["supplier-refused"]),
                    bool(events["fallback-used"]))


def assess_grid_service_dataset(reader, selection, *, source, receiver, requirement, block_rows):
    """Run the identical whole-episode reducer used for canonical saved records."""
    intervals = iter_grid_service_dataset(reader, selection, source=source, receiver=receiver,
        requirement=requirement, block_rows=block_rows)
    try:
        return assess_grid_episode_intervals(source=source, receiver=receiver, requirement=requirement,
            context=selection.context, intervals=intervals)
    finally:
        intervals.close()
