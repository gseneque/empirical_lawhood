"""Reusable scientific records, designs and calculations extracted from native binding.

Native acquisition and external-format effects belong to the corresponding adapter.
Original scientific schemas and numerical definitions are preserved.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from empirical_lawhood.science.evidence.evidence import OutcomeAccess
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_sha256, validate_stable_id
from empirical_lawhood.domains.biology.virtual_cell.features import TargetFeatureBuildReceipt


@dataclass(frozen=True, slots=True)
class TargetFeatureMaterializationReceipt(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        'empirical-lawhood/physical/virtual-cell/target-feature-materialization-receipt'
    )

    receipt_id: str
    source_manifest_sha256: str
    roster_source_object_ids: tuple[str, ...]
    roster_source_sha256s: tuple[str, ...]
    build_receipt_sha256: str
    arrow_sha256: str
    arrow_size_bytes: int
    target_count: int
    feature_count: int
    feature_provenance_sha256: str
    outcome_access: OutcomeAccess
    response_derived: bool
    post_cutoff: bool

    def __post_init__(self) -> None:
        validate_stable_id(self.receipt_id, field_name="receipt_id")
        for digest_name, digest_value in (
            ("source_manifest_sha256", self.source_manifest_sha256),
            ("build_receipt_sha256", self.build_receipt_sha256),
            ("arrow_sha256", self.arrow_sha256),
            ("feature_provenance_sha256", self.feature_provenance_sha256),
        ):
            validate_sha256(digest_value, field_name=digest_name)
        require_sorted_unique_strings(
            self.roster_source_object_ids,
            field_name="roster_source_object_ids",
            allow_empty=False,
        )
        require_sorted_unique_strings(
            self.roster_source_sha256s,
            field_name="roster_source_sha256s",
            allow_empty=False,
        )
        for value in self.roster_source_sha256s:
            validate_sha256(value, field_name="roster_source_sha256s")
        if (
            len(self.roster_source_object_ids) != 3
            or len(self.roster_source_sha256s) != 3
        ):
            raise ValueError(
                "target-feature materialization requires all three split rosters"
            )
        for count_name, count_value in (
            ("arrow_size_bytes", self.arrow_size_bytes),
            ("target_count", self.target_count),
            ("feature_count", self.feature_count),
        ):
            if isinstance(count_value, bool) or count_value <= 0:
                raise ValueError(f"{count_name} must be positive")
        if self.outcome_access is not OutcomeAccess.OUTCOME_BLIND:
            raise ValueError("target features must remain outcome blind")
        if self.response_derived or self.post_cutoff:
            raise ValueError("target features must be response-blind and pre-cutoff")


@dataclass(frozen=True, slots=True)
class TargetFeatureMaterialization:
    arrow_payload: bytes
    build_receipt: TargetFeatureBuildReceipt
    materialization_receipt: TargetFeatureMaterializationReceipt
