"""Reusable scientific records, designs and calculations extracted from native binding.

Native acquisition and external-format effects belong to the corresponding adapter.
Original scientific schemas and numerical definitions are preserved.
"""

from __future__ import annotations
from dataclasses import dataclass
import hashlib
import math
import re
from typing import ClassVar
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_nonempty, validate_sha256, validate_stable_id


_TRANSFORM_ID = "ensembl-113-gene-protein-composition"


_MAX_GTF_DECOMPRESSED_BYTES = 4 * 1024**3


_MAX_FASTA_DECOMPRESSED_BYTES = 1024**3


_MAX_LINE_BYTES = 4 * 1024**2


_AMINO_ACIDS = tuple("ACDEFGHIKLMNPQRSTVWY")


_TARGET_ALIASES: dict[str, str] = {}


_ATTRIBUTE_PATTERN = re.compile(r'(\S+) "([^"]*)"')


@dataclass(frozen=True, slots=True)
class _GeneAnnotation:
    gene_id: str
    gene_name: str
    chromosome: str
    strand: str
    start: int
    end: int
    gene_biotype: str


@dataclass(frozen=True, slots=True)
class TargetFeatureMapping(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/physical/virtual-cell/target-feature-mapping'

    target_id: str
    mapped_gene_name: str
    ensembl_gene_id: str | None
    protein_sequence_available: bool
    alias_applied: bool
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        validate_nonempty(self.target_id, field_name="target_id")
        validate_nonempty(self.mapped_gene_name, field_name="mapped_gene_name")
        if self.ensembl_gene_id is not None:
            validate_nonempty(self.ensembl_gene_id, field_name="ensembl_gene_id")
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if self.ensembl_gene_id is None and not self.reason_codes:
            raise ValueError("unmapped target feature requires a reason")
        if self.protein_sequence_available and self.ensembl_gene_id is None:
            raise ValueError("protein sequence cannot exist without a gene mapping")


@dataclass(frozen=True, slots=True)
class TargetFeatureBuildReceipt(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/physical/virtual-cell/target-feature-build-receipt'

    receipt_id: str
    transform_id: str
    ensembl_release: str
    gtf_sha256: str
    peptide_fasta_sha256: str
    target_roster_sha256: str
    feature_ids_sha256: str
    matrix_sha256: str
    mappings: tuple[TargetFeatureMapping, ...]
    mapped_gene_count: int
    protein_covered_count: int
    response_derived: bool
    post_cutoff: bool

    def __post_init__(self) -> None:
        validate_stable_id(self.receipt_id, field_name="receipt_id")
        validate_stable_id(self.transform_id, field_name="transform_id")
        validate_stable_id(self.ensembl_release, field_name="ensembl_release")
        for name, value in (
            ("gtf_sha256", self.gtf_sha256),
            ("peptide_fasta_sha256", self.peptide_fasta_sha256),
            ("target_roster_sha256", self.target_roster_sha256),
            ("feature_ids_sha256", self.feature_ids_sha256),
            ("matrix_sha256", self.matrix_sha256),
        ):
            validate_sha256(value, field_name=name)
        require_sorted_unique_ids(self.mappings, attribute="target_id", field_name="mappings")
        if self.mapped_gene_count != sum(
            value.ensembl_gene_id is not None for value in self.mappings
        ):
            raise ValueError("mapped gene count is not derived from mappings")
        if self.protein_covered_count != sum(
            value.protein_sequence_available for value in self.mappings
        ):
            raise ValueError("protein coverage count is not derived from mappings")
        if self.response_derived or self.post_cutoff:
            raise ValueError("Lane H target features must be response-blind and pre-cutoff")


def _registry_digest(values: tuple[str, ...]) -> str:
    digest = hashlib.sha256()
    for value in values:
        payload = value.encode("utf-8")
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _sequence_features(sequence: str | None) -> list[float]:
    if sequence is None or not sequence:
        return [0.0] * (len(_AMINO_ACIDS) + 9) + [1.0]
    length = len(sequence)
    counts = {acid: sequence.count(acid) / length for acid in _AMINO_ACIDS}
    entropy = -sum(value * math.log(value) for value in counts.values() if value > 0)
    grouped = (
        sum(counts[value] for value in "DE"),
        sum(counts[value] for value in "KRH"),
        sum(counts[value] for value in "AVILMFWY"),
        sum(counts[value] for value in "FWY"),
        sum(counts[value] for value in "STNQ"),
        counts["P"],
        counts["G"],
        entropy,
    )
    return [math.log1p(length), *(counts[value] for value in _AMINO_ACIDS), *grouped, 0.0]


def virtual_cell_feature_ids() -> tuple[str, ...]:
    values = (
        "gene_log1p_span_bp",
        "gene_is_protein_coding",
        "gene_strand_positive",
        "gene_chr_autosome",
        "gene_chr_x",
        "gene_chr_y",
        "gene_chr_mt",
        "protein_log1p_length",
        *(f"protein_fraction_{acid.lower()}" for acid in _AMINO_ACIDS),
        "protein_fraction_acidic",
        "protein_fraction_basic",
        "protein_fraction_hydrophobic",
        "protein_fraction_aromatic",
        "protein_fraction_polar",
        "protein_fraction_proline",
        "protein_fraction_glycine",
        "protein_composition_entropy",
        "protein_missing",
        "gene_annotation_missing",
    )
    return tuple(values)
