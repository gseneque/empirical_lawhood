# SPDX-License-Identifier: MPL-2.0
"""Config-bound custody for exposed development effects, without scientific authority.

Use existing guarded artifact manifests and task receipts. Completed effects are
immutable; interrupted contact never supplies permission to acquire them again.
"""

from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore, decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import artifact_custody_limits
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactManifest, ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt, ReceiptCheck


def read_development_native_payload(writer: ExternalArtifactPlane, manifest: ArtifactManifest, *, maximum_bytes: int | None) -> bytes:
    if (manifest.logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
        or manifest.logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
        or (maximum_bytes is not None and manifest.materialization.size_bytes > maximum_bytes)):
        raise ValueError("Development native input has another access role or exceeds its bound")
    writer.verify_manifest(manifest)
    raw = read_bounded_bytes(writer.root.resolve(manifest.materialization.relative_path, for_write=False),
                             maximum_bytes=manifest.materialization.size_bytes)
    if (len(raw) != manifest.materialization.size_bytes
        or sha256(raw).hexdigest() != manifest.materialization.physical_sha256
        or sha256(raw).hexdigest() != manifest.logical.content_sha256):
        raise ValueError("Development native bytes changed after exact publication authentication")
    return raw


def preflight_development_native_store(writer: ExternalArtifactPlane, *, minimum_free_bytes: int) -> None:
    if not isinstance(writer, ExternalArtifactPlane):
        raise TypeError("Development native operations require an actual guarded ExternalArtifactPlane")
    writer.root.verify(for_write=True, operation_minimum_free_bytes=minimum_free_bytes)


@dataclass(frozen=True, slots=True)
class DevelopmentNativeEffectInput(CanonicalRecord):
    """A persisted contact boundary, never completion or retry permission."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/development-native/effect-input"
    run_id: str
    task_id: str
    configuration: ObjectIdentity


class DevelopmentNativeCustody:
    """Existing artifact/receipt contracts with exact config-bound locators."""

    effect_input_type = DevelopmentNativeEffectInput

    def __init__(self, *, writer: ExternalArtifactPlane, config: CanonicalRecord,
                 run_id: str, implementation_commit: str | None, minimum_free_bytes: int,
                 maximum_output_bytes: int | None, read_only: bool = False):
        if not isinstance(writer, ExternalArtifactPlane):
            raise TypeError("Development native operations require an actual guarded ExternalArtifactPlane")
        if type(read_only) is not bool:
            raise TypeError("Development native custody requires an exact read-only selection")
        if implementation_commit is None:
            if not read_only:
                raise ValueError("Development native execution requires its selected producing commit")
        elif (type(implementation_commit) is not str or len(implementation_commit) != 40
                or any(c not in "0123456789abcdef" for c in implementation_commit)):
            raise ValueError("Development native operation requires an exact lowercase producing Git commit")
        self.read_only = read_only
        self.writer, self.config, self.run_id = writer, config, run_id
        self.implementation_commit = implementation_commit
        self.minimum_free_bytes, self.maximum_output_bytes = minimum_free_bytes, maximum_output_bytes
        self.store = ExternalTaskReceiptStore(writer, minimum_free_bytes=minimum_free_bytes)
        self.parent = ArtifactLineageParent(ObjectIdentity.from_record(config.config_id, config),
            VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE)
        relative = f"runs/{run_id}/inputs/config.json"
        raw = config.canonical_bytes()
        existing = self._manifest(relative)
        if existing is None:
            if read_only:
                raise ValueError("Development native result lacks its retained exact input")
            published = writer.write(ArtifactWriteRequest(
                f"{run_id}.config", relative, config.SCHEMA, ArtifactProfile.CANONICAL_JSON,
                "application/json", f"{run_id}.inputs", f"runs/{run_id}/inputs", raw,
                VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE,
                minimum_free_bytes=minimum_free_bytes))
            existing = self._manifest(relative)
            if existing is None or existing.materialization != published.materialization:
                raise ValueError("Development native input publication is incomplete")
        if (existing.logical.payload_schema != config.SCHEMA or existing.logical.content_sha256 != config.fingerprint()
            or read_development_native_payload(writer, existing, maximum_bytes=len(raw)) != raw):
            raise ValueError("Development native retained input differs from its selected allocation/config")
        self.input_manifest = existing

    def _manifest(self, relative: str) -> ArtifactManifest | None:
        path = self.writer.root.resolve(relative, for_write=False)
        manifest_path = self.writer.root.resolve(relative + ".manifest.json", for_write=False)
        if not path.exists() and not manifest_path.exists():
            return None
        if not path.is_file() or not manifest_path.is_file():
            raise ValueError("Development native artifact publication is partial")
        manifest = decode_artifact_manifest(read_bounded_bytes(manifest_path, maximum_bytes=artifact_custody_limits(self.writer).manifest_bytes), maximum_bytes=artifact_custody_limits(self.writer).manifest_bytes)
        if manifest.materialization.relative_path != relative:
            raise ValueError("Development native manifest changes its exact selected path")
        return manifest

    def load(self, task_id: str, record_type: type[CanonicalRecord], *, in_progress: bool = False):
        # Native scientific rollout IDs remain unchanged in their records.
        # Compact operational locators keep receipt staging below NAME_MAX.
        task_id = self.task_locator(task_id)
        attempt_id = f"{self.run_id}.{task_id}.attempt-001"
        receipt = self.store.read_by_receipt_id(self.run_id, task_id, f"receipt.{attempt_id}")
        relative = f"runs/{self.run_id}/outputs/{task_id}.json"
        manifest = self._manifest(relative)
        if receipt is None:
            if manifest is not None:
                raise ValueError("Development native unreceipted effect requires inspection; it cannot be repeated")
            if not in_progress and self._manifest(f"runs/{self.run_id}/inputs/effects/{task_id}.json") is not None:
                raise ValueError("Development native interrupted contact lacks a completion receipt; uncertain effects cannot be repeated")
            return None
        if manifest is None or (self.implementation_commit is not None
                and receipt.implementation_commit != self.implementation_commit):
            raise ValueError("Development native recovery changes source or omits its exact output")
        logical = manifest.logical
        if (receipt.operational_status is not OperationalStatus.SUCCEEDED
            or receipt.input_materialization_ids != (self.input_manifest.materialization.materialization_id,)
            or receipt.output_materializations != (manifest.materialization,)
            or receipt.output_logical_artifacts != (logical,)
            or logical.logical_artifact_id != f"{self.run_id}.{task_id}.output"
            or logical.payload_schema != record_type.SCHEMA or logical.profile is not ArtifactProfile.CANONICAL_JSON
            or logical.media_type != "application/json"
            or logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or logical.lineage_parents != (self.parent,)
            or (self.maximum_output_bytes is not None and manifest.materialization.size_bytes > self.maximum_output_bytes)):
            raise ValueError("Development native receipt/output changes its frozen census, role or configuration")
        record = decode_canonical_bytes(read_development_native_payload(self.writer, manifest, maximum_bytes=self.maximum_output_bytes), record_type,
            maximum_bytes=self.maximum_output_bytes)
        # A completed-data reader learns the producer from authenticated custody.
        # All later members must retain that same producer; execution never infers it.
        if self.implementation_commit is None:
            self.implementation_commit = receipt.implementation_commit
        return record

    def retain(self, task_id: str, record: CanonicalRecord) -> CanonicalRecord:
        if self.read_only:
            raise ValueError("Development native read-only custody is immutable")
        task_id = self.task_locator(task_id)
        if self.load(task_id, type(record), in_progress=True) is not None:
            raise ValueError("Development native completed effect is immutable")
        raw = record.canonical_bytes()
        if self.maximum_output_bytes is not None and len(raw) > self.maximum_output_bytes:
            raise ValueError("Development native output exceeds its declared work contract")
        written = self.writer.write(ArtifactWriteRequest(
            f"{self.run_id}.{task_id}.output", f"runs/{self.run_id}/outputs/{task_id}.json",
            record.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json",
            f"{self.run_id}.outputs", f"runs/{self.run_id}/outputs", raw,
            VisibilityCeiling.DEVELOPMENT_ONLY, (VisibilityCeiling.DEVELOPMENT_ONLY,),
            OutcomeAccess.DEVELOPMENT_VISIBLE, lineage_parents=(self.parent,),
            minimum_free_bytes=self.minimum_free_bytes))
        attempt = f"{self.run_id}.{task_id}.attempt-001"
        receipt = CanonicalTaskReceipt(f"receipt.{attempt}", self.run_id, task_id, attempt,
            self.implementation_commit, (self.input_manifest.materialization.materialization_id,),
            (written.materialization,), (written.logical,),
            (ReceiptCheck("complete-typed-native-product", True, ()),), OperationalStatus.SUCCEEDED, ())
        self.store.commit(receipt, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
            outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
        return record

    def begin_native_effect(self, task_id: str) -> None:
        if self.read_only:
            raise ValueError("Development native read-only custody cannot enter an effect")
        task_id = self.task_locator(task_id)
        marker = self.effect_input_type(self.run_id, task_id, self.parent.identity)
        relative = f"runs/{self.run_id}/inputs/effects/{task_id}.json"
        if self._manifest(relative) is not None:
            raise ValueError("Development native contact is already recorded; absence of a receipt grants no retry")
        raw = marker.canonical_bytes()
        publication = self.writer.write(ArtifactWriteRequest(f"{self.run_id}.{task_id}.effect-input", relative,
            marker.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json",
            f"{self.run_id}.effect-inputs", f"runs/{self.run_id}/inputs/effects", raw,
            VisibilityCeiling.DEVELOPMENT_ONLY, (VisibilityCeiling.DEVELOPMENT_ONLY,), OutcomeAccess.DEVELOPMENT_VISIBLE,
            lineage_parents=(self.parent,), minimum_free_bytes=self.minimum_free_bytes))
        if publication.created is not True:
            raise ValueError("Development native contact publication was reused; only its creating launch may enter the worker")
        retained = self._manifest(relative)
        if (retained is None or retained.logical != publication.logical
            or retained.materialization != publication.materialization
            or read_development_native_payload(self.writer, retained, maximum_bytes=len(raw)) != raw):
            raise ValueError("Development native contact did not survive exact custody verification")

    @staticmethod
    def task_locator(scientific_id: str) -> str:
        return scientific_id if len(scientific_id) < 80 else f"cell-{sha256(scientific_id.encode()).hexdigest()[:32]}"
