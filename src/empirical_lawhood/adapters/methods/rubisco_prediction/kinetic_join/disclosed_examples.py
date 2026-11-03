# SPDX-License-Identifier: MPL-2.0
"""Typed disclosed source witness; never a measured enzyme or qualification."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id


@dataclass(frozen=True, slots=True)
class DisclosedAssumption(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/examples/disclosed-rubisco-kinetic-assumption"
    assumption_id: str
    description: str
    evidence_role: str = "DISCLOSED_SYNTHETIC_NOT_MEASURED"
    independent_biological_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.assumption_id)
        if (type(self.description) is not str or not self.description.strip()
                or self.evidence_role != "DISCLOSED_SYNTHETIC_NOT_MEASURED"
                or type(self.independent_biological_units) is not int
                or self.independent_biological_units != 0):
            raise ValueError("disclosed example cannot become measured biological evidence")
