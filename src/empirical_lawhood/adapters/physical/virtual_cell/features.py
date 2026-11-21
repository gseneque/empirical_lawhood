"""Native acquisition and external-format binding for the domain science."""

from __future__ import annotations
from collections.abc import Iterator
import gzip
import hashlib
import math
import re
from typing import BinaryIO
import numpy as np
from empirical_lawhood.science.records.serialization import validate_sha256
from empirical_lawhood.domains.biology.virtual_cell.analysis import TargetFeatureMatrix
from empirical_lawhood.domains.biology.virtual_cell.contracts import VirtualCellContractError

from empirical_lawhood.domains.biology.virtual_cell.features import (
    TargetFeatureBuildReceipt as _science_TargetFeatureBuildReceipt,
    TargetFeatureMapping as _science_TargetFeatureMapping,
    _AMINO_ACIDS,
    _ATTRIBUTE_PATTERN,
    _GeneAnnotation,
    _MAX_FASTA_DECOMPRESSED_BYTES,
    _MAX_GTF_DECOMPRESSED_BYTES,
    _MAX_LINE_BYTES,
    _TARGET_ALIASES,
    _TRANSFORM_ID,
    _registry_digest,
    _sequence_features,
    virtual_cell_feature_ids as _science_virtual_cell_feature_ids,
)

def _bounded_text_lines(
    stream: BinaryIO,
    *,
    maximum_decompressed_bytes: int,
) -> Iterator[str]:
    observed = 0
    try:
        with gzip.GzipFile(fileobj=stream, mode="rb") as decompressed:
            for raw in decompressed:
                if not isinstance(raw, bytes) or len(raw) > _MAX_LINE_BYTES:
                    raise VirtualCellContractError("feature-source line exceeds its bound")
                observed += len(raw)
                if observed > maximum_decompressed_bytes:
                    raise VirtualCellContractError("feature source exceeds decompressed byte bound")
                try:
                    yield raw.decode("utf-8").rstrip("\r\n")
                except UnicodeDecodeError as error:
                    raise VirtualCellContractError("feature source is not UTF-8") from error
    except (EOFError, OSError) as error:
        raise VirtualCellContractError(
            "feature source is not a valid complete gzip stream"
        ) from error


def _attributes(raw: str) -> dict[str, str]:
    return {key: value for key, value in _ATTRIBUTE_PATTERN.findall(raw)}


def _read_gene_annotations(
    stream: BinaryIO,
    *,
    requested_names: frozenset[str],
) -> dict[str, tuple[_GeneAnnotation, ...]]:
    annotations: dict[str, list[_GeneAnnotation]] = {}
    for line in _bounded_text_lines(
        stream,
        maximum_decompressed_bytes=_MAX_GTF_DECOMPRESSED_BYTES,
    ):
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != 9 or fields[2] != "gene":
            continue
        attributes = _attributes(fields[8])
        gene_name = attributes.get("gene_name")
        gene_id = attributes.get("gene_id")
        if gene_name not in requested_names or gene_id is None:
            continue
        try:
            start = int(fields[3])
            end = int(fields[4])
        except ValueError as error:
            raise VirtualCellContractError("GTF gene interval is not integral") from error
        if start <= 0 or end < start:
            raise VirtualCellContractError("GTF gene interval is invalid")
        annotation = _GeneAnnotation(
            gene_id=gene_id.split(".", 1)[0],
            gene_name=gene_name,
            chromosome=fields[0],
            strand=fields[6],
            start=start,
            end=end,
            gene_biotype=attributes.get("gene_biotype", attributes.get("gene_type", "unknown")),
        )
        candidates = annotations.setdefault(gene_name, [])
        if annotation not in candidates:
            candidates.append(annotation)
    return {
        gene_name: tuple(sorted(values, key=lambda value: value.gene_id))
        for gene_name, values in annotations.items()
    }


def _fasta_gene_id(header: str) -> str | None:
    match = re.search(r"(?:^|\s)gene:([^\s]+)", header)
    return None if match is None else match.group(1).split(".", 1)[0]


def _read_longest_proteins(
    stream: BinaryIO,
    *,
    requested_gene_ids: frozenset[str],
) -> dict[str, str]:
    sequences: dict[str, str] = {}
    current_gene: str | None = None
    chunks: list[str] = []

    def finish() -> None:
        if current_gene is None:
            return
        sequence = "".join(chunks).upper()
        if not sequence or any(value not in set(_AMINO_ACIDS) | {"X", "*"} for value in sequence):
            raise VirtualCellContractError("Ensembl peptide FASTA contains invalid residues")
        sequence = sequence.rstrip("*")
        if len(sequence) > len(sequences.get(current_gene, "")):
            sequences[current_gene] = sequence

    for line in _bounded_text_lines(
        stream,
        maximum_decompressed_bytes=_MAX_FASTA_DECOMPRESSED_BYTES,
    ):
        if line.startswith(">"):
            finish()
            candidate = _fasta_gene_id(line[1:])
            current_gene = candidate if candidate in requested_gene_ids else None
            chunks = []
        elif current_gene is not None:
            chunks.append(line.strip())
    finish()
    return sequences


def build_ensembl_target_features(
    *,
    target_ids: tuple[str, ...],
    gtf_stream: BinaryIO,
    peptide_fasta_stream: BinaryIO,
    gtf_sha256: str,
    peptide_fasta_sha256: str,
) -> tuple[TargetFeatureMatrix, _science_TargetFeatureBuildReceipt]:
    "Build the frozen Ensembl-113 gene/protein target-feature transform."

    if not target_ids or len(set(target_ids)) != len(target_ids):
        raise ValueError("target roster must be nonempty and unique")
    validate_sha256(gtf_sha256, field_name="gtf_sha256")
    validate_sha256(peptide_fasta_sha256, field_name="peptide_fasta_sha256")
    mapped_names = {target: _TARGET_ALIASES.get(target, target) for target in target_ids}
    annotation_candidates = _read_gene_annotations(
        gtf_stream,
        requested_names=frozenset(mapped_names.values()),
    )
    proteins = _read_longest_proteins(
        peptide_fasta_stream,
        requested_gene_ids=frozenset(
            value.gene_id for values in annotation_candidates.values() for value in values
        ),
    )
    annotations = {
        gene_name: max(
            values,
            key=lambda value: (
                len(proteins.get(value.gene_id, "")),
                value.gene_biotype == "protein_coding",
                value.end - value.start,
                value.gene_id,
            ),
        )
        for gene_name, values in annotation_candidates.items()
    }
    feature_ids = _science_virtual_cell_feature_ids()
    rows: list[list[float]] = []
    mappings: list[_science_TargetFeatureMapping] = []
    for target in target_ids:
        mapped_name = mapped_names[target]
        annotation = annotations.get(mapped_name)
        sequence = None if annotation is None else proteins.get(annotation.gene_id)
        reasons: tuple[str, ...]
        if annotation is None:
            gene_features = [0.0] * 7
            reasons = ("ENSEMBL_GENE_NAME_UNMAPPED",)
        else:
            chromosome = annotation.chromosome.removeprefix("chr").upper()
            gene_features = [
                math.log1p(annotation.end - annotation.start + 1),
                float(annotation.gene_biotype == "protein_coding"),
                float(annotation.strand == "+"),
                float(chromosome.isdigit() and 1 <= int(chromosome) <= 22),
                float(chromosome == "X"),
                float(chromosome == "Y"),
                float(chromosome in {"M", "MT"}),
            ]
            reasons = () if sequence is not None else ("ENSEMBL_PROTEIN_SEQUENCE_UNAVAILABLE",)
        rows.append([*gene_features, *_sequence_features(sequence), float(annotation is None)])
        mappings.append(
            _science_TargetFeatureMapping(
                target_id=target,
                mapped_gene_name=mapped_name,
                ensembl_gene_id=None if annotation is None else annotation.gene_id,
                protein_sequence_available=sequence is not None,
                alias_applied=target != mapped_name,
                reason_codes=reasons,
            )
        )
    matrix = np.asarray(rows, dtype=np.float64)
    if matrix.shape != (len(target_ids), len(feature_ids)) or not np.all(np.isfinite(matrix)):
        raise VirtualCellContractError("target feature transform produced an invalid matrix")
    provenance = hashlib.sha256()
    for value in (
        _TRANSFORM_ID,
        gtf_sha256,
        peptide_fasta_sha256,
        _registry_digest(target_ids),
        _registry_digest(feature_ids),
    ):
        provenance.update(value.encode("utf-8"))
    feature_matrix = TargetFeatureMatrix(
        target_ids=target_ids,
        feature_ids=feature_ids,
        values=matrix,
        provenance_sha256=provenance.hexdigest(),
    )
    matrix_digest = hashlib.sha256(np.ascontiguousarray(matrix, dtype="<f8").tobytes()).hexdigest()
    receipt = _science_TargetFeatureBuildReceipt(
        receipt_id="target-features.virtual-cell-2025-ensembl-113",
        transform_id=_TRANSFORM_ID,
        ensembl_release="ensembl-113",
        gtf_sha256=gtf_sha256,
        peptide_fasta_sha256=peptide_fasta_sha256,
        target_roster_sha256=_registry_digest(target_ids),
        feature_ids_sha256=_registry_digest(feature_ids),
        matrix_sha256=matrix_digest,
        mappings=tuple(sorted(mappings, key=lambda value: value.target_id)),
        mapped_gene_count=sum(value.ensembl_gene_id is not None for value in mappings),
        protein_covered_count=sum(value.protein_sequence_available for value in mappings),
        response_derived=False,
        post_cutoff=False,
    )
    return feature_matrix, receipt
