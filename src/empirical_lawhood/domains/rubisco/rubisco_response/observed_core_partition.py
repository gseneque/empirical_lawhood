# SPDX-License-Identifier: MPL-2.0
"""Selected physical atoms and covalent boundaries of a source-observed Val1 core."""

from dataclasses import dataclass
from math import isfinite

from empirical_lawhood.science.records.serialization import validate_sha256


@dataclass(frozen=True)
class ObservedCorePartition:
    material: str
    gas: str | None
    source_digests: tuple[tuple[str, str], ...]
    atomic_numbers: tuple[int, ...]
    masses_dalton: tuple[float, ...]
    charges_electron: tuple[float, ...]
    qm_atom_indices: tuple[int, ...]
    bonds: tuple[tuple[int, int], ...]
    links: tuple[tuple[int, int, float], ...]
    lengths_angstrom: tuple[float, float, float]
    qm_formal_charge: int
    spin_multiplicity: int

    def __post_init__(self):
        if self.material not in ("V1-WT", "V1-I95M") or self.gas not in (
            None,
            "O2",
            "CO2",
        ):
            raise ValueError(
                "observed periodic core requires its selected material and gas"
            )
        required = {
            "manifest",
            "states",
            "topology",
            "material",
            "construction",
            "thermal",
            "completion",
            "thermal-series",
        }
        if self.gas is not None:
            required.update(("gas-prepi", "gas-frcmod"))
        if (
            self.source_digests != tuple(sorted(set(self.source_digests)))
            or len(self.source_digests) != len(required)
            or {k for k, _ in self.source_digests} != required
        ):
            raise ValueError("observed core omits an original parent identity")
        for _, digest in self.source_digests:
            validate_sha256(digest, field_name="observed core original source")
        count = len(self.atomic_numbers)
        if (
            not isinstance(self.atomic_numbers, tuple)
            or not isinstance(self.masses_dalton, tuple)
            or not isinstance(self.charges_electron, tuple)
            or not count == len(self.masses_dalton) == len(self.charges_electron)
            or any(type(z) is not int or z <= 0 for z in self.atomic_numbers)
            or any(
                isinstance(m, bool) or not isfinite(m) or m <= 0
                for m in self.masses_dalton
            )
            or any(
                isinstance(q, bool) or not isfinite(q) for q in self.charges_electron
            )
        ):
            raise ValueError(
                "observed core changes the complete original atom population"
            )
        gas_numbers = {None: (), "CO2": (6, 8, 8), "O2": (8, 8)}[self.gas]
        qm = self.qm_atom_indices
        if (
            len(qm) != 121 + len(gas_numbers)
            or count <= len(qm)
            or qm != tuple(sorted(set(qm)))
            or any(type(i) is not int or not 0 <= i < count for i in qm)
            or gas_numbers
            and (
                self.atomic_numbers[-len(gas_numbers) :] != gas_numbers
                or qm[-len(gas_numbers) :]
                != tuple(range(count - len(gas_numbers), count))
            )
        ):
            raise ValueError(
                "observed core changes its quantum region or added gas atoms"
            )
        if (
            type(self.lengths_angstrom) is not tuple
            or len(self.lengths_angstrom) != 3
            or any(
                isinstance(v, bool) or not isfinite(v) or v <= 0
                for v in self.lengths_angstrom
            )
            or type(self.qm_formal_charge) is not int
            or self.qm_formal_charge != -2
            or type(self.spin_multiplicity) is not int
            or self.spin_multiplicity not in (1, 3)
        ):
            raise ValueError(
                "observed core substitutes its cell, electronic charge or spin"
            )
        region = set(qm)
        cuts = set()
        if self.bonds != tuple(sorted(set(self.bonds))):
            raise ValueError("observed core requires ordered, distinct native bonds")
        for a, b in self.bonds:
            if type(a) is not int or type(b) is not int or not 0 <= a < b < count:
                raise ValueError("observed core contains an invalid native bond")
            if (a in region) != (b in region):
                cuts.add((a, b) if a in region else (b, a))
        if (
            len(cuts) != 7
            or len(self.links) != len(cuts)
            or self.links != tuple((a, b, 1.09) for a, b in sorted(cuts))
        ):
            raise ValueError("observed core changes the seven native covalent cuts")
        electrons = (
            sum(self.atomic_numbers[i] for i in qm) + len(cuts) - self.qm_formal_charge
        )
        if (electrons - (self.spin_multiplicity - 1)) % 2:
            raise ValueError(
                "observed core electron count and spin multiplicity disagree"
            )
