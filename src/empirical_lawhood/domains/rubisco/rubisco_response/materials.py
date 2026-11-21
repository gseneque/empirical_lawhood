# SPDX-License-Identifier: MPL-2.0
"""Complete L8S8 sequence selections and finite paired interventions.

Logical chain names are not PDB author chains or an atom correspondence.
A sequence-defined case establishes neither assembly nor active chemistry.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.science.records.decoding import validate_record_fields
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, validate_nonempty, validate_stable_id

AMINO_ACIDS = frozenset("ACDEFGHIKLMNPQRSTVWY")


def exact(record, kind):
    if type(record) is not kind:
        raise TypeError(f"requires exact {kind.__name__}")
    validate_record_fields(record)


def identities(values, *, allow_empty=False):
    if type(values) is not tuple or (not values and not allow_empty):
        raise ValueError("exact source identities must form a nonempty immutable tuple")
    require_sorted_unique_ids(values, attribute="object_id", field_name="sources")
    for value in values:
        exact(value, ObjectIdentity)


@dataclass(frozen=True, slots=True)
class SubunitChain(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/subunit-chain"
    chain_id: str
    subunit: str
    sequence: str

    def __post_init__(self):
        validate_stable_id(self.chain_id)
        if self.subunit not in {"LSU", "SSU"}:
            raise ValueError("Rubisco chain must identify its large or small subunit")
        if (type(self.sequence) is not str or not self.sequence
                or not set(self.sequence).issubset(AMINO_ACIDS)):
            raise ValueError("chain requires its complete unambiguous amino-acid sequence")


@dataclass(frozen=True, slots=True)
class RubiscoMaterial(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/material"
    material_id: str
    organism: str
    processing_view: str
    chains: tuple[SubunitChain, ...]
    sources: tuple[ObjectIdentity, ...]
    assembly_scope: str = "SEQUENCE_DEFINED_L8S8_NOT_ASSEMBLY_ADMISSION"

    def __post_init__(self):
        validate_stable_id(self.material_id)
        validate_nonempty(self.organism, field_name="organism")
        validate_stable_id(self.processing_view)
        if type(self.chains) is not tuple or len(self.chains) != 16:
            raise ValueError("full L8S8 material must retain all sixteen chains")
        require_sorted_unique_ids(self.chains, attribute="chain_id", field_name="chains")
        for chain in self.chains:
            exact(chain, SubunitChain)
        if tuple(sum(chain.subunit == kind for chain in self.chains) for kind in ("LSU", "SSU")) != (8, 8):
            raise ValueError("full L8S8 material must retain eight chains of each subunit")
        identities(self.sources)
        if self.assembly_scope != "SEQUENCE_DEFINED_L8S8_NOT_ASSEMBLY_ADMISSION":
            raise ValueError("sequence selection cannot establish physical assembly")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.material_id, self)


@dataclass(frozen=True, slots=True)
class ResidueSubstitution(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/residue-substitution"
    chain_id: str
    position_1based: int
    before: str
    after: str

    def __post_init__(self):
        validate_stable_id(self.chain_id)
        if type(self.position_1based) is not int or self.position_1based <= 0:
            raise ValueError("sequence edits require a positive linear position")
        if (self.before not in AMINO_ACIDS or self.after not in AMINO_ACIDS
                or self.before == self.after):
            raise ValueError("finite substitution requires two distinct amino acids")


@dataclass(frozen=True, slots=True)
class RubiscoPairedCase(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/paired-case"
    case_id: str
    parent: RubiscoMaterial
    mutant: RubiscoMaterial
    substitutions: tuple[ResidueSubstitution, ...]
    case_role: str
    exposure_group: str
    sources: tuple[ObjectIdentity, ...]
    applicability: str = "SELECTED_SEQUENCE_CONTRAST_NOT_KINETIC_VALIDATION"

    def __post_init__(self):
        validate_stable_id(self.case_id)
        validate_stable_id(self.exposure_group)
        for value in (self.parent, self.mutant):
            exact(value, RubiscoMaterial)
        identities(self.sources)
        if (self.parent.organism != self.mutant.organism
                or self.parent.processing_view != self.mutant.processing_view
                or tuple((c.chain_id, c.subunit) for c in self.parent.chains)
                != tuple((c.chain_id, c.subunit) for c in self.mutant.chains)):
            raise ValueError("paired materials must share organism, processing and full chain correspondence")
        if type(self.substitutions) is not tuple:
            raise TypeError("substitution census must be immutable")
        for row in self.substitutions:
            exact(row, ResidueSubstitution)
        expected = []
        for left, right in zip(self.parent.chains, self.mutant.chains, strict=True):
            if len(left.sequence) != len(right.sequence):
                raise ValueError("this substitution contract cannot conceal insertions or deletions")
            expected.extend(ResidueSubstitution(left.chain_id, index, a, b)
                            for index, (a, b) in enumerate(zip(left.sequence, right.sequence, strict=True), 1) if a != b)
        if self.substitutions != tuple(expected):
            raise ValueError("declared edits differ from the complete finite sequence intervention")
        if self.case_role not in {"CANDIDATE", "DONOR", "ADVERSE_CONTROL", "NO_CHANGE"}:
            raise ValueError("unknown paired case role")
        if (self.case_role == "NO_CHANGE") != (not self.substitutions):
            raise ValueError("no-change controls and actual finite edits cannot alias")
        if self.applicability != "SELECTED_SEQUENCE_CONTRAST_NOT_KINETIC_VALIDATION":
            raise ValueError("sequence correspondence cannot establish kinetic applicability")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.case_id, self)


@dataclass(frozen=True, slots=True)
class RubiscoCaseSet(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/case-set"
    selection_id: str
    cases: tuple[RubiscoPairedCase, ...]
    sources: tuple[ObjectIdentity, ...]
    exposure: str = "ALREADY_EXPOSED_DESIGN"
    independent_biological_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        if type(self.cases) is not tuple or not self.cases:
            raise ValueError("case selection must retain a nonempty complete census")
        require_sorted_unique_ids(self.cases, attribute="case_id", field_name="cases")
        for case in self.cases:
            exact(case, RubiscoPairedCase)
        identities(self.sources)
        if (self.exposure not in {"ALREADY_EXPOSED_DESIGN", "DISCLOSED_SOFTWARE_CONTROL"}
                or type(self.independent_biological_units) is not int or self.independent_biological_units != 0):
            raise ValueError("case selections cannot create fresh biological units")
        material_ids = {}
        for case in self.cases:
            for material in (case.parent, case.mutant):
                previous = material_ids.setdefault(material.material_id, material)
                if previous != material:
                    raise ValueError("material identifier aliases different sequence selections")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.selection_id, self)


def homogeneous_material(*, material_id, organism, processing_view, lsu, ssu, sources):
    """Expand a stated homogeneous assembly without inventing PDB chain maps."""
    chains = tuple(SubunitChain(f"{kind.lower()}.{number:02}", kind, sequence)
                   for kind, sequence in (("LSU", lsu), ("SSU", ssu)) for number in range(1, 9))
    return RubiscoMaterial(material_id, organism, processing_view, chains, sources)


def paired_case(*, case_id, parent, mutant, case_role, exposure_group, sources):
    """Derive every finite edit from both complete source sequences."""
    if tuple(c.chain_id for c in parent.chains) != tuple(c.chain_id for c in mutant.chains):
        raise ValueError("cannot derive edits without exact paired chain correspondence")
    substitutions = tuple(ResidueSubstitution(left.chain_id, index, a, b)
        for left, right in zip(parent.chains, mutant.chains, strict=True)
        for index, (a, b) in enumerate(zip(left.sequence, right.sequence, strict=True), 1) if a != b)
    return RubiscoPairedCase(case_id, parent, mutant, substitutions, case_role, exposure_group, sources)
