# SPDX-License-Identifier: MPL-2.0
"""Exact original structures, preparation views and unpromoted structural supply."""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import (
    AssessmentDisposition as A,
    ScientificConditionScope,
)
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord,
    validate_stable_id,
    validate_sha256,
)

NAMESPACE = "rubisco-insilico-structure"
UNIT = "rubisco.exposed-gp-te-structural-family"
QUESTION = "What does authentic full L8S8 correspondence and declared WT/I95M preparation sensitivity establish about the exact proposed Gp structural intervention?"
ORIGINALS = (
    ("1bwv.cif", "4fe0d7197062a6643568937520582a58673a91d032ed313a8c37545d22a0d6b6"),
    ("3zxw.cif", "119f966e3706442fa493134f90c21e65bc12c109e68041bf4cc7e399d9961c15"),
    (
        "gp.lsu.fasta",
        "dfd209a4a2d15f123d962b7e79e1f102a2436c702d073d07037d4c0752300baa",
    ),
    (
        "gp.ssu.i95m.m1.fasta",
        "8c0c18d140f676634e8939e698d71f57904f42a87ec6e187fa0a9ca5609005e1",
    ),
    (
        "gp.ssu.i95m.v1.fasta",
        "c535815b32647e0a05415dcfaeebd5d23cd3a30ce42d544d1ab7798d1e81bea8",
    ),
    (
        "gp.ssu.wt.m1.fasta",
        "79ac2166013376e3a5e276f1c1d610c7bae9b92ba97ef51d31dc612bc9904db3",
    ),
    (
        "gp.ssu.wt.v1.fasta",
        "dba72e8fa8ceeb679681c26349e0e59d844da6de14c84046baf931721f98ef05",
    ),
)


def identity(record):
    for name in ("input_id", "product_id", "config_id"):
        if hasattr(record, name):
            return ObjectIdentity.from_record(getattr(record, name), record)
    raise ValueError("unknown structural scientific record identity")


@dataclass(frozen=True, slots=True)
class StructuralSourceMember(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-structure/source-member"
    filename: str
    original_url: str
    sha256: str
    raw_utf8: str

    def __post_init__(self):
        validate_sha256(self.sha256)
        if (
            not self.original_url
            or sha256(self.raw_utf8.encode()).hexdigest() != self.sha256
        ):
            raise ValueError("structural source substitutes original bytes")


@dataclass(frozen=True, slots=True)
class StructuralSource(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-structure/source"
    input_id: str
    nomination: ObjectIdentity
    source_members: tuple[StructuralSourceMember, ...]
    distance_shells_angstrom: tuple[Decimal, ...]
    assembly_ids: tuple[tuple[str, str], ...]
    alternate_policy: str
    missing_coordinate_policy: str
    mutant_coordinate_status: str

    def __post_init__(self):
        validate_stable_id(self.input_id)
        for row in self.source_members:
            row.__post_init__()
        if (
            tuple((row.filename, row.sha256) for row in self.source_members)
            != ORIGINALS
            or self.distance_shells_angstrom != (Decimal(3), Decimal(5), Decimal(8))
            or self.assembly_ids != (("1BWV", "1"), ("3ZXW", "1"))
            or self.alternate_policy
            != "RETAIN_ALL_POSITIVE_OCCUPANCY_ALTERNATES_NO_COOCCURRENCE_CLAIM"
            or self.missing_coordinate_policy
            != "RETAIN_UNKNOWN_NO_LOOP_OR_TERMINUS_BUILD"
            or self.mutant_coordinate_status != "UNMODELED_PENDING_DECLARED_COMPARISON"
        ):
            raise ValueError(
                "structural source changes its frozen source/mapping substep"
            )
        if (
            self.nomination.object_schema
            != "empirical-lawhood/rubisco-nomination-preparation/exploratory-dossier"
            or self.nomination.object_version != "1.0.0"
            or self.nomination.object_fingerprint
            != "8121b9e941cbc66d0634dbc9f3047c6e22232fb1a783f2a313a17bf5f63f35fa"
        ):
            raise ValueError(
                "structural source substitutes the actual prepared nomination"
            )


def scope(source):
    return ScientificConditionScope(
        "system.rubisco-insilico.gp-i95m",
        "world.rubisco-insilico.structure",
        source.input_id,
        ("assembly-correspondence", "mutant-geometry", "site-neighborhood"),
        ("dimensionless", "dimensionless", "angstrom"),
        "receiver.exact-source-structure-not-kinetics",
        "clock.exposed-rubisco-structural-analysis",
        "Original activated inhibited Gp and Te deposits, full biological assemblies and exact proposed full sequence views; coordinate coverage is explicit and mutant geometry/kinetics remain unresolved.",
        source_config_sha256=source.fingerprint(),
        instance_id="material.gp-i95m.m1.tag-free.v2",
    )


@dataclass(frozen=True, slots=True)
class AssemblyAtom(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-structure/assembly-atom"
    pdb_id: str
    operator_id: str
    source_atom_id: str
    label_asym_id: str
    auth_asym_id: str
    entity_id: str
    label_seq_id: str
    auth_seq_id: str
    insertion_code: str
    component_id: str
    atom_id: str
    element: str
    alternate_id: str
    occupancy: Decimal
    xyz_angstrom: tuple[Decimal, Decimal, Decimal]

    def __post_init__(self):
        if self.pdb_id not in ("1BWV", "3ZXW") or len(self.xyz_angstrom) != 3:
            raise ValueError(
                "assembly atom changes selected structure or coordinate dimensions"
            )
        if (
            not self.occupancy.is_finite()
            or self.occupancy < 0
            or any(not value.is_finite() for value in self.xyz_angstrom)
        ):
            raise ValueError("assembly atom has invalid coordinate/occupancy")

    @property
    def chain_id(self):
        return self.pdb_id + "." + self.operator_id + "." + self.label_asym_id


@dataclass(frozen=True, slots=True)
class AssemblyChain(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-insilico-structure/assembly-chain"
    )
    pdb_id: str
    operator_id: str
    label_asym_id: str
    auth_asym_id: str
    entity_id: str
    full_sequence: str
    # Every linear sequence position, original author number/insertion/component,
    # and all actually observed atom names; an empty atom list remains missing.
    residues: tuple[tuple[int, str, str, str, tuple[str, ...]], ...]

    def __post_init__(self):
        if tuple(row[0] for row in self.residues) != tuple(
            range(1, len(self.full_sequence) + 1)
        ):
            raise ValueError(
                "assembly chain omits/duplicates complete sequence positions"
            )

    @property
    def chain_id(self):
        return self.pdb_id + "." + self.operator_id + "." + self.label_asym_id


@dataclass(frozen=True, slots=True)
class SiteNeighborhood(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-insilico-structure/site-neighborhood"
    )
    chain_id: str
    linear_position: int
    author_position: str
    original_component: str
    query_atom_count: int
    # Complete per-shell nearby atom identities, including own-chain residues,
    # neighbor chains, all deposited chemicals/waters; no kinetic threshold.
    shells: tuple[tuple[Decimal, tuple[str, ...]], ...]
    # All other protein chain minima, including remote chains and missing query.
    other_chain_minima_angstrom: tuple[tuple[str, Decimal | None], ...]
    chemical_minima_angstrom: tuple[tuple[str, Decimal | None], ...]


@dataclass(frozen=True, slots=True)
class StructuralInventory(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-structure/inventory"
    product_id: str
    source: ObjectIdentity
    nomination: ObjectIdentity
    atoms: tuple[AssemblyAtom, ...]
    chains: tuple[AssemblyChain, ...]
    # Original named operators, flattened row-major matrix plus translation.
    operators: tuple[tuple[str, str, tuple[Decimal, ...], tuple[Decimal, ...]], ...]
    neighborhoods: tuple[SiteNeighborhood, ...]
    proposed_sequences: tuple[tuple[str, str], ...]
    chemical_census: tuple[tuple[str, str, str, int], ...]
    # Full M1/V1 WT/I95M views; mutations are exact sequence propositions only.
    mutant_geometry: str = "UNMODELED_PENDING_DECLARED_COMPARISON"
    biological_disposition: A = A.UNEVALUABLE

    def __post_init__(self):
        validate_stable_id(self.product_id)
        if (
            self.mutant_geometry != "UNMODELED_PENDING_DECLARED_COMPARISON"
            or self.biological_disposition is not A.UNEVALUABLE
        ):
            raise ValueError("source inventory promotes modeled mutant or biology")
        if len(
            {(a.pdb_id, a.operator_id, a.source_atom_id) for a in self.atoms}
        ) != len(self.atoms):
            raise ValueError("assembly atom opportunity duplicated")
        if len({c.chain_id for c in self.chains}) != len(self.chains):
            raise ValueError("biological protein chain duplicated")


@dataclass(frozen=True, slots=True)
class StructuralAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-structure/assessment"
    product_id: str
    source: ObjectIdentity
    inventory: ObjectIdentity
    nomination: ObjectIdentity
    prior_nomination_scope: ScientificConditionScope
    chain_coverage: tuple[tuple[str, int, int, tuple[int, ...]], ...]
    sequence_views: tuple[tuple[str, str], ...]
    source_disposition: A
    mutant_comparison_disposition: A
    kinetic_disposition: A
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        if (
            self.mutant_comparison_disposition is not A.UNEVALUABLE
            or self.kinetic_disposition is not A.UNEVALUABLE
        ):
            raise ValueError(
                "source/mapping substep pretends complete mutant comparison/kinetics"
            )


@dataclass(frozen=True, slots=True)
class StructureOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-insilico-structure/operation-config"
    )
    config_id: str
    operation: str
    source: StructuralSource
    nomination_scope: ScientificConditionScope
    operands: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        self.source.__post_init__()
        if (
            self.operation not in ("analyze", "assess")
            or self.config_id != "config." + NAMESPACE + "." + self.operation
        ):
            raise ValueError("structural config changes exact selected operation")
        expected = tuple(
            sorted(
                (identity(self.source), self.source.nomination),
                key=lambda row: row.object_id,
            )
        )
        if self.operands != expected:
            raise ValueError("structural config changes selected authentic operands")


@dataclass(frozen=True, slots=True)
class AssemblyCoordinates(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-insilico-structure/assembly-coordinates"
    )
    product_id: str
    inventory: ObjectIdentity
    # mmCIF retains original atom columns, renamed assembly chains and exact
    # transformed coordinates. It is observed WT, not prepared mutant geometry.
    files: tuple[tuple[str, str, str], ...]

    def __post_init__(self):
        if tuple(row[0] for row in self.files) != (
            "1bwv-assembly1.cif",
            "3zxw-assembly1.cif",
        ):
            raise ValueError("assembly coordinate roster changed")
        for _, digest, text in self.files:
            if sha256(text.encode()).hexdigest() != digest:
                raise ValueError("assembly coordinate bytes changed")
