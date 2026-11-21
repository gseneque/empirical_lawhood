"""Source custody on the existing immutable artifact plane; no network contact."""

from __future__ import annotations
from empirical_lawhood.storage.artifact_sidecars import resolve_artifact_sidecar_bytes
from empirical_lawhood.storage.artifact_sidecars import read_artifact_sidecar

from hashlib import sha256
from typing import TypeVar

from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.design.public_source_acquisition import ChecksummedFrozenSourceAcquisitionProposal, CaptureAssuredFrozenSourceAcquisitionProposal, MAX_ACQUISITION_CONTROL_BYTES, ChecksummedPublicSourceAcquisitionPlan, ChecksummedPublicSourceMember, ChecksummedSourceAcquisitionApproval, CaptureAssuredSourceAcquisitionApproval
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.execution.public_source_acquisition import ChecksummedSourceAcquisitionAttempt, CaptureAssuredSourceAcquisitionAttempt, SourceAcquisitionFailure, ChecksummedSourceCustodyReceipt, CaptureAssuredSourceCustodyReceipt, ChecksummedSourceTransferObservation, CaptureAssuredSourceTransferObservation, acquisition_record_types, verify_public_source_bytes
from empirical_lawhood.storage.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.storage.file_locks import exclusive_file_lock



RecordT = TypeVar("RecordT", bound=CanonicalRecord)
_CONTROL_TYPES = (
    ChecksummedSourceAcquisitionAttempt,
    ChecksummedSourceTransferObservation,
    ChecksummedSourceCustodyReceipt,
    SourceAcquisitionFailure,
    CaptureAssuredSourceAcquisitionAttempt,
    CaptureAssuredSourceTransferObservation,
    CaptureAssuredSourceCustodyReceipt,
)


class ExternalPublicSourceCustody:
    """Closed source/authority records; payload publication remains artifact-owned."""

    def __init__(self, plane: ExternalArtifactPlane) -> None:
        self.plane = plane

    def _write_control(
        self,
        *,
        relative: str,
        scope: str,
        record_id: str,
        record: CanonicalRecord,
        minimum_free_bytes: int = 0,
    ) -> ObjectIdentity:
        payload = record.canonical_bytes()
        if len(payload) > MAX_ACQUISITION_CONTROL_BYTES:
            raise ValueError("source control record exceeds its byte bound")
        result = self.plane.write(
            ArtifactWriteRequest(
                logical_artifact_id=record_id,
                relative_path=relative,
                payload_schema=record.SCHEMA,
                profile=ArtifactProfile.CANONICAL_JSON,
                media_type="application/json",
                payload=payload,
                publication_scope_id="public-source-control",
                publication_scope_relative_root=scope,
                outcome_access=OutcomeAccess.OUTCOME_BLIND,
                visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
                parent_visibility_ceilings=(),
                minimum_free_bytes=minimum_free_bytes,
            )
        )
        if result.logical.content_sha256 != record.fingerprint():
            raise ArtifactIdentityConflict("source control publication changed its identity")
        return ObjectIdentity.from_record(record_id, record)

    def _read_control(self, relative: str, record_id: str, record_type: type[RecordT]) -> RecordT:
        self.plane.root.verify(for_write=False)
        path = self.plane.root.resolve(relative, for_write=False)
        manifest_path = self.plane.root.resolve(f"{relative}.manifest.json", for_write=False)
        if not path.exists() and not manifest_path.exists():
            raise KeyError(record_id)
        manifest = read_artifact_sidecar(self.plane, (manifest_path).relative_to(self.plane.root.contract.canonical_path).as_posix(), maximum_bytes=self.plane.custody_limits.manifest_bytes)
        if (
            manifest.logical.logical_artifact_id != record_id
            or manifest.logical.payload_schema != record_type.SCHEMA
            or manifest.logical.profile is not ArtifactProfile.CANONICAL_JSON
            or manifest.logical.outcome_access is not OutcomeAccess.OUTCOME_BLIND
            or manifest.logical.media_type != "application/json"
            or manifest.logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
            or manifest.materialization.relative_path != relative
            or manifest.materialization.size_bytes > MAX_ACQUISITION_CONTROL_BYTES
        ):
            raise ArtifactIdentityConflict("source control manifest changes its closed contract")
        self.plane.verify_manifest(manifest)
        payload = read_bounded_bytes(path, maximum_bytes=MAX_ACQUISITION_CONTROL_BYTES)
        record = decode_canonical_bytes(
            payload, record_type, maximum_bytes=MAX_ACQUISITION_CONTROL_BYTES
        )
        if (
            record.canonical_bytes() != payload
            or record.fingerprint() != manifest.logical.content_sha256
        ):
            raise ArtifactIdentityConflict("source control bytes changed after verification")
        return record

    def persist_source_proposal(
        self, proposal: ChecksummedFrozenSourceAcquisitionProposal
    ) -> ObjectIdentity:
        return self._write_control(
            relative=f"authority/source-acquisition-proposals/{proposal.frozen_proposal_id}.json",
            scope="authority",
            record_id=proposal.frozen_proposal_id,
            record=proposal,
        )

    def load_source_proposal(self, proposal_id: str) -> ChecksummedFrozenSourceAcquisitionProposal:
        validate_stable_id(proposal_id, field_name="proposal_id")
        return self._read_versioned_control(
            f"authority/source-acquisition-proposals/{proposal_id}.json",
            proposal_id,
            (ChecksummedFrozenSourceAcquisitionProposal, CaptureAssuredFrozenSourceAcquisitionProposal),
        )

    def persist_source_approval(self, approval: ChecksummedSourceAcquisitionApproval) -> ObjectIdentity:
        return self._write_control(
            relative=f"authority/source-acquisition-approvals/{approval.authorization_id}.json",
            scope="authority",
            record_id=approval.authorization_id,
            record=approval,
        )

    def load_source_approval(self, authorization_id: str) -> ChecksummedSourceAcquisitionApproval:
        validate_stable_id(authorization_id, field_name="authorization_id")
        return self._read_versioned_control(
            f"authority/source-acquisition-approvals/{authorization_id}.json",
            authorization_id,
            (ChecksummedSourceAcquisitionApproval, CaptureAssuredSourceAcquisitionApproval),
        )

    def _read_versioned_control(
        self, relative: str, record_id: str, record_types: tuple[type[RecordT], ...]
    ) -> RecordT:
        # Select only among code-owned schemas, then authenticate the complete
        # manifest, publication and canonical payload using the common reader.
        manifest_path = self.plane.root.resolve(f"{relative}.manifest.json", for_write=False)
        if not manifest_path.exists():
            raise KeyError(record_id)
        manifest = read_artifact_sidecar(self.plane, (manifest_path).relative_to(self.plane.root.contract.canonical_path).as_posix(), maximum_bytes=self.plane.custody_limits.manifest_bytes)
        for record_type in record_types:
            if manifest.logical.payload_schema == record_type.SCHEMA:
                return self._read_control(relative, record_id, record_type)
        raise ArtifactIdentityConflict("unregistered source authority schema")

    @staticmethod
    def _record_path(plan: ChecksummedPublicSourceAcquisitionPlan, record_id: str) -> str:
        validate_stable_id(record_id, field_name="record_id")
        return f"{plan.relative_root}/receipts/{record_id}.json"

    def preflight(self, plan: ChecksummedPublicSourceAcquisitionPlan) -> None:
        if (
            ObjectIdentity.from_record(
                self.plane.root.contract.storage_root_id, self.plane.root.contract
            )
            != plan.storage_root
        ):
            raise ValueError("source custody root differs from its frozen contract")
        self.plane.root.verify(
            for_write=True,
            operation_minimum_free_bytes=max(
                plan.minimum_free_bytes, plan.resource_budget.output_bytes
            ),
        )
        for member in plan.members:
            self.plane.root.resolve(member.relative_locator, for_write=True)
            for prefix in ("attempt", "transfer", "custody", "failure"):
                self.plane.root.resolve(
                    self._record_path(plan, f"{prefix}.{member.source_id}"), for_write=True
                )
        self.plane.validators.generic_validation(
            profile=ArtifactProfile.RAW_SOURCE_BYTES,
            payload_schema=acquisition_record_types(plan)[2].RAW_SCHEMA,
        )
        if len(plan.canonical_bytes()) > MAX_ACQUISITION_CONTROL_BYTES:
            raise ValueError("full source plan exceeds its control-record bound")

    def load_record(
        self, plan: ChecksummedPublicSourceAcquisitionPlan, record_id: str, record_type: type[RecordT]
    ) -> RecordT | None:
        if record_type not in _CONTROL_TYPES:
            raise ValueError("unregistered acquisition control record type")
        try:
            return self._read_control(self._record_path(plan, record_id), record_id, record_type)
        except KeyError:
            return None

    def publish_record(
        self, plan: ChecksummedPublicSourceAcquisitionPlan, record_id: str, record: CanonicalRecord
    ) -> None:
        if type(record) not in _CONTROL_TYPES:
            raise ValueError("unregistered acquisition control record type")
        self._write_control(
            relative=self._record_path(plan, record_id),
            scope=plan.relative_root,
            record_id=record_id,
            record=record,
            minimum_free_bytes=plan.minimum_free_bytes,
        )

    def reserve_attempt(
        self, plan: ChecksummedPublicSourceAcquisitionPlan, attempt: ChecksummedSourceAcquisitionAttempt
    ) -> None:
        lock_path = self.plane.root.resolve(
            f"{plan.relative_root}/acquisition.lock",
            for_write=True,
            operation_minimum_free_bytes=plan.minimum_free_bytes,
        )
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        # Re-resolve after mkdir; the common lock owner rejects symlink substitution.
        lock_path = self.plane.root.resolve(
            f"{plan.relative_root}/acquisition.lock", for_write=True
        )
        with exclusive_file_lock(lock_path):
            if (
                self.load_record(plan, attempt.attempt_id, acquisition_record_types(plan)[0])
                is not None
            ):
                raise RuntimeError("SOURCE_ATTEMPT_ALREADY_RESERVED_RECOVERY_REQUIRED")
            for member in plan.members:
                if member.source_id == attempt.member.object_id:
                    path = self.plane.root.resolve(member.relative_locator, for_write=False)
                    sidecar = self.plane.root.resolve(
                        f"{member.relative_locator}.manifest.json", for_write=False
                    )
                    if path.exists() or sidecar.exists():
                        raise RuntimeError("SOURCE_BYTES_ALREADY_PRESENT_WITHOUT_ATTEMPT")
            self.publish_record(plan, attempt.attempt_id, attempt)

    def publish_raw(
        self, plan: ChecksummedPublicSourceAcquisitionPlan, member: ChecksummedPublicSourceMember, payload: bytes
    ) -> tuple[ArtifactIdentity, str]:
        verify_public_source_bytes(member, payload)
        result = self.plane.write(
            ArtifactWriteRequest(
                logical_artifact_id=member.source_id,
                relative_path=member.relative_locator,
                payload_schema=acquisition_record_types(plan)[2].RAW_SCHEMA,
                profile=ArtifactProfile.RAW_SOURCE_BYTES,
                media_type=member.media_type,
                payload=payload,
                publication_scope_id=plan.scope_id,
                publication_scope_relative_root=plan.relative_root,
                outcome_access=plan.outcome_access,
                visibility_ceiling=VisibilityCeiling.OUTCOME_VISIBLE,
                parent_visibility_ceilings=(),
                minimum_free_bytes=plan.minimum_free_bytes,
            )
        )
        artifact = ArtifactIdentity(
            member.source_id,
            "raw-public-source",
            acquisition_record_types(plan)[2].RAW_SCHEMA,
            result.materialization.physical_sha256,
            member.media_type,
            result.materialization.size_bytes,
        )
        return artifact, result.manifest_materialization.physical_sha256

    def recover_raw(
        self,
        plan: ChecksummedPublicSourceAcquisitionPlan,
        member: ChecksummedPublicSourceMember,
        transfer: ChecksummedSourceTransferObservation,
    ) -> tuple[ArtifactIdentity, str]:
        path = self.plane.root.resolve(member.relative_locator, for_write=False)
        payload = read_bounded_bytes(path, maximum_bytes=member.expected_size_bytes)
        if (
            len(payload) != transfer.source_size_bytes
            or sha256(payload).hexdigest() != transfer.source_sha256
        ):
            raise ArtifactIdentityConflict(
                "recovery raw bytes differ from the transfer observation"
            )
        # Artifact publication owns reconciliation of its existing intent/commit.
        return self.publish_raw(plan, member, payload)

    def verify_raw(
        self,
        plan: ChecksummedPublicSourceAcquisitionPlan,
        member: ChecksummedPublicSourceMember,
        receipt: ChecksummedSourceCustodyReceipt,
    ) -> None:
        manifest_path = self.plane.root.resolve(
            f"{member.relative_locator}.manifest.json", for_write=False
        )
        payload = read_bounded_bytes(manifest_path, maximum_bytes=self.plane.custody_limits.manifest_bytes)
        if sha256(payload).hexdigest() != receipt.publication_manifest_sha256:
            raise ArtifactIdentityConflict("source publication manifest identity drifted")
        manifest = resolve_artifact_sidecar_bytes(self.plane, payload)
        if (
            manifest.logical.logical_artifact_id != member.source_id
            or manifest.logical.payload_schema != acquisition_record_types(plan)[2].RAW_SCHEMA
            or manifest.logical.profile is not ArtifactProfile.RAW_SOURCE_BYTES
            or manifest.logical.outcome_access is not plan.outcome_access
            or manifest.logical.media_type != member.media_type
            or manifest.logical.visibility_ceiling is not VisibilityCeiling.OUTCOME_VISIBLE
            or manifest.materialization.relative_path != member.relative_locator
            or manifest.materialization.physical_sha256 != receipt.raw_artifact.sha256
            or manifest.materialization.size_bytes != member.expected_size_bytes
            or receipt.raw_artifact.size_bytes != member.expected_size_bytes
            or receipt.raw_artifact.media_type != member.media_type
        ):
            raise ArtifactIdentityConflict("source manifest changes its custody operands")
        self.plane.verify_manifest(manifest)
