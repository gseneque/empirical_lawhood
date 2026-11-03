# SPDX-License-Identifier: MPL-2.0
"""Additive independently checked observed mapping; no preparation/kinetics."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id


@dataclass(frozen=True, slots=True)
class StructuralIntegrityAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-structure/independent-integrity-assessment"
    VERSION: ClassVar[str] = "1.0.0"
    product_id: str
    source: ObjectIdentity
    inventory: ObjectIdentity
    coordinates: ObjectIdentity | None
    assessor_source: ObjectIdentity
    chain_coverage: tuple[tuple[str, int, int, tuple[int, ...]], ...]
    atom_census: tuple[tuple[str, int], ...]
    # Source-operator Gram/determinant residuals are observations, not an
    # invented physical preparation/force-field admission tolerance.
    rigid_operator_residuals: tuple[tuple[str, str, Decimal, Decimal], ...]
    maximum_distance_residual_angstrom: Decimal
    distance_comparison_tolerance_angstrom: Decimal
    shell_boundary_ambiguities: tuple[tuple[str, str, Decimal], ...]
    observed_mapping_disposition: A
    neighborhood_disposition: A
    mutant_comparison_disposition: A = A.UNEVALUABLE
    preparation_disposition: A = A.NOT_ATTEMPTED
    kinetic_disposition: A = A.UNEVALUABLE
    physical_independent_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.product_id)
        for value in (self.source, self.inventory, self.assessor_source):
            if type(value) is not ObjectIdentity:
                raise ValueError("structural integrity requires actual typed identities")
            value.__post_init__()
        if self.coordinates is not None:
            if type(self.coordinates) is not ObjectIdentity:
                raise ValueError("structural export integrity requires typed identity")
            self.coordinates.__post_init__()
        if (
            self.observed_mapping_disposition is not A.SATISFIED
            or self.neighborhood_disposition is not (A.UNEVALUABLE if self.shell_boundary_ambiguities else A.SATISFIED)
            or self.mutant_comparison_disposition is not A.UNEVALUABLE
            or self.preparation_disposition is not A.NOT_ATTEMPTED
            or self.kinetic_disposition is not A.UNEVALUABLE
            or type(self.physical_independent_units) is not int
            or self.physical_independent_units != 0
            or self.distance_comparison_tolerance_angstrom != Decimal("1e-10")
            or not self.maximum_distance_residual_angstrom.is_finite()
            or not 0 <= self.maximum_distance_residual_angstrom <= self.distance_comparison_tolerance_angstrom
            or len(self.chain_coverage) != 32
            or tuple(name for name, _ in self.atom_census) != ("1BWV", "3ZXW")
            or any(type(count) is not int or count <= 0 for _, count in self.atom_census)
        ):
            raise ValueError("structural integrity drops denominator or promotes unresolved science")
