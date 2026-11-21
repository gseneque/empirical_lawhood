"""Reusable scientific records, designs and calculations extracted from native binding.

Native acquisition and external-format effects belong to the corresponding adapter.
Original scientific schemas and numerical definitions are preserved.
"""

from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar
from empirical_lawhood.domains.history.history_budget_scientific_inputs import HistoryBudgetDescriptorScientificInput, HistoryBudgetUnitScientificInput
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.storage.contracts.artifacts import ArtifactManifest, ArtifactWriteResult
from empirical_lawhood.domains.history.simulator_morphism_challenges.contracts import SimulatorMorphismChallengeConfig, SimulatorMorphismChallengePhase
from empirical_lawhood.domains.history.simulator_morphism_challenges.numeric_inputs import (
    RCChallengeDescriptorNumericExport,
    RCChallengeNumericExport,
    RCChallengeNumericExportReceipt,
    RCChallengeNumericSource,
    original_numeric_definition,
)


def export_numeric_source(*, export_id: str, source: RCChallengeNumericSource) -> RCChallengeNumericExport:
    """Compute only outcome-blind descriptor operands and original fibre streams."""
    from empirical_lawhood.domains.history.simulator_morphism_challenges.descriptors import family_from_unit_id, generate_descriptor

    scales = (16, 32, 64) if source.phase is SimulatorMorphismChallengePhase.DEVELOPMENT else (64, 128, 256)
    rows = []
    for unit, seed in zip(source.unit_ids, source.seeds, strict=True):
        for scale in scales:
            descriptor = generate_descriptor(unit_id=unit, family=family_from_unit_id(unit), scale_cells=scale, seed=seed)
            recipe, original, seeds = original_numeric_definition(descriptor)
            rows.append(RCChallengeDescriptorNumericExport(descriptor, recipe, original, seeds))
    result = RCChallengeNumericExport(export_id, ObjectIdentity.from_record(source.source_id, source), scales, tuple(rows))
    result.require_source(source)
    return result


def publication_identity(result: ArtifactWriteResult, *, role: str) -> ArtifactIdentity:
    return ArtifactIdentity(result.logical.logical_artifact_id, role, result.logical.payload_schema,
                            result.materialization.physical_sha256, result.logical.media_type,
                            result.materialization.size_bytes)


def _require_publication(record: CanonicalRecord, result: ArtifactWriteResult) -> None:
    payload = record.canonical_bytes()
    if result.logical.payload_schema != record.SCHEMA or result.logical.content_sha256 != sha256(payload).hexdigest() or result.materialization.physical_sha256 != sha256(payload).hexdigest() or result.materialization.size_bytes != len(payload) or result.materialization.compression != "none":
        raise ValueError("numeric custody publication differs from exact current operand bytes")


@dataclass(frozen=True, slots=True)
class RCChallengeNumericInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/simulator-morphism-challenges/numeric-input"
    input_id: str
    source: RCChallengeNumericSource
    export: RCChallengeNumericExport
    receipt: RCChallengeNumericExportReceipt
    receipt_publication: ArtifactWriteResult
    receipt_manifest: ArtifactManifest

    def __post_init__(self) -> None:
        validate_stable_id(self.input_id)
        self.export.require_source(self.source)
        _require_publication(self.source, self.receipt.source_publication)
        _require_publication(self.export, self.receipt.export_publication)
        _require_publication(self.receipt, self.receipt_publication)
        if self.receipt_manifest.logical != self.receipt_publication.logical or self.receipt_manifest.materialization != self.receipt_publication.materialization or self.receipt_manifest.publication is None:
            raise ValueError("numeric input receipt requires its exact committed publication manifest")


    def scientific_inputs(self, config: SimulatorMorphismChallengeConfig) -> tuple[HistoryBudgetUnitScientificInput, ...]:
        self.source.require_config(config)
        if config.scale_cells != self.export.scale_cells:
            raise ValueError("numeric input differs from current fixed scales")
        source_id = publication_identity(self.receipt.source_publication, role="original-numeric-source")
        receipt_id = publication_identity(self.receipt_publication, role="numeric-export-receipt")
        return tuple(HistoryBudgetUnitScientificInput(0, unit, sha256(seed).hexdigest(), tuple(
            HistoryBudgetDescriptorScientificInput(0, unit, row.descriptor.scale_cells,
                row.descriptor.seed_sha256, row.original_descriptor_sha256,
                row.descriptor.fingerprint(), row.history_fibre_seed_sha256s, source_id, receipt_id)
            for row in self.export.descriptors if row.descriptor.unit_id == unit), None)
            for unit, seed in zip(self.source.unit_ids, self.source.seeds, strict=True))
