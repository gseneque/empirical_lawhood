# SPDX-License-Identifier: MPL-2.0
"""Explicit NVE nested chemical revisions, with unchanged numerical contracts."""

from dataclasses import dataclass
import json
from typing import ClassVar

from empirical_lawhood.kernel.decoding import decode_canonical_bytes

from . import nve_contracts
from .control_preparation_admission import (
    ReusedGeometryChemicalForcePlan, SerializedDurableChemicalForcePlan,
)


@dataclass(frozen=True, slots=True)
class SerializedPreparationNVEControlPlan(nve_contracts.NVEControlPlan):
    """Select an admitted named chemical route; full 96/48 science is unchanged."""

    VERSION: ClassVar[str] = "1.1.0"
    chemical_controls: ReusedGeometryChemicalForcePlan | SerializedDurableChemicalForcePlan

    def __post_init__(self):
        if type(self.chemical_controls) not in (ReusedGeometryChemicalForcePlan,
                SerializedDurableChemicalForcePlan):
            raise ValueError("serialized NVE plan requires its explicit admitted chemical revision")
        nve_contracts.NVEControlPlan.__post_init__(self)


def decode_plan(value):
    raw = value.encode()
    version = json.loads(raw).get("version")
    kind = {"1.0.0": nve_contracts.NVEControlPlan,
        "1.1.0": SerializedPreparationNVEControlPlan}.get(version)
    if version == "1.2.0":
        from .serialized_nve_custody import SerializedCustodyNVEControlPlan
        kind = SerializedCustodyNVEControlPlan
    if kind is None:
        raise ValueError("unsupported selected NVE preparation plan revision")
    return decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))
