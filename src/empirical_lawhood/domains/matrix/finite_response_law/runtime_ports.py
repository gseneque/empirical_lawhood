"Finite response-law evaluation worker configuration over existing guarded authority/receipt/control stores.\n\nNo scientific execution, authority creation or filesystem access occurs on import\nor construction. Each operation reconstructs the existing store in its worker.\n"

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Any

from empirical_lawhood.domains.matrix.finite_response_law.assigned_native_records import FiniteResponseLawAssignedEvaluationInterface
from empirical_lawhood.domains.matrix.finite_response_law.consumer import FiniteResponseLawNativeUnitReadoutMap
from empirical_lawhood.domains.matrix.finite_response_law.control_services import FiniteResponseLawControllerBindingConfig
from empirical_lawhood.domains.matrix.finite_response_law.evaluation_native_records import FiniteResponseLawEvaluationInterface
from empirical_lawhood.storage.artifacts import ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.execution.local.prepared_execution_events import ExternalPreparedExecutionEventStore
from empirical_lawhood.storage.study_issue import ExternalStudyOperationAuthorityStore
from empirical_lawhood.storage.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_relative_locator, validate_stable_id
from empirical_lawhood.design.nested_controller_evaluation import PreparedFutureSlot
from empirical_lawhood.design.source_qualification import ProspectiveRetainedContinuation
from empirical_lawhood.design.study_issue import StudyAuthorityKind, StudyOperationAuthority, require_study_authority
from empirical_lawhood.storage.contracts.artifacts import CanonicalTaskReceipt
from empirical_lawhood.execution.controller_compiler import CompiledLeastMagnitudeControllerStudy
from empirical_lawhood.execution.controller_evaluation_nested import PreparedCommonStartBinding, PreparedDesignBindingReceipt, PreparedExecutionCensus, PreparedExecutionEventPrefix, PreparedForecastParentCommitment, PreparedFutureCompletion, PreparedInstanceBindingReceipt, PreparedParentReturn
from empirical_lawhood.execution.controller_runtime import DeliveryControllerDecisionCommitment, DeliveryControllerTickReceipt
from empirical_lawhood.execution.execution import DependencyReceiptBinding

PREPARED_SCHEMAS = tuple(
    sorted(
        cls.SCHEMA
        for cls in (
            CompiledLeastMagnitudeControllerStudy,
            DeliveryControllerDecisionCommitment,
            DeliveryControllerTickReceipt,
            PreparedCommonStartBinding,
            PreparedDesignBindingReceipt,
            PreparedForecastParentCommitment,
            PreparedInstanceBindingReceipt,
            PreparedParentReturn,
            PreparedFutureSlot,
            PreparedFutureCompletion,
            PreparedExecutionCensus,
            FiniteResponseLawEvaluationInterface,
            FiniteResponseLawAssignedEvaluationInterface,
            FiniteResponseLawNativeUnitReadoutMap,
            FiniteResponseLawControllerBindingConfig,
            StudyOperationAuthority,
        )
    )
)


@dataclass(frozen=True)
class FiniteResponseLawPreparedStorePort:
    root: GuardedExternalRoot
    relative_root: str
    minimum_free_bytes: int

    def __post_init__(self) -> None:
        validate_relative_locator(self.relative_root)
        if self.minimum_free_bytes < 0:
            raise ValueError("Finite response-law evaluation prepared storage has a negative free-space floor")

    def _store(self) -> ExternalPreparedExecutionEventStore:
        return ExternalPreparedExecutionEventStore(
            ExternalArtifactPlane(self.root),
            state_root_relative_path=self.relative_root,
            record_schemas=PREPARED_SCHEMAS,
            minimum_free_bytes=self.minimum_free_bytes,
            maximum_record_bytes=16 * 1024**2,
        )

    def publish_prepared_record(
        self, *, prefix_id: str, object_id: str, record: CanonicalRecord
    ) -> ArtifactIdentity:
        return self._store().publish_prepared_record(
            prefix_id=prefix_id, object_id=object_id, record=record
        )

    def read_prepared_record(
        self, *, prefix_id: str, subject: ObjectIdentity, artifact: ArtifactIdentity
    ) -> bytes:
        return self._store().read_prepared_record(
            prefix_id=prefix_id, subject=subject, artifact=artifact
        )

    def verify_prepared_subject(
        self, *, prefix_id: str, subject: ObjectIdentity, artifact: ArtifactIdentity
    ) -> None:
        self._store().verify_prepared_subject(
            prefix_id=prefix_id, subject=subject, artifact=artifact
        )

    def load_prepared(self, prefix_id: str) -> PreparedExecutionEventPrefix:
        return self._store().load_prepared(prefix_id)

    def create_prepared(self, prefix: PreparedExecutionEventPrefix) -> None:
        self._store().create_prepared(prefix)

    def compare_and_append_prepared(
        self, *, expected_prefix_sha256: str, updated: PreparedExecutionEventPrefix
    ) -> None:
        self._store().compare_and_append_prepared(
            expected_prefix_sha256=expected_prefix_sha256, updated=updated
        )


@dataclass(frozen=True)
class RetainedPreparedStorePort(FiniteResponseLawPreparedStorePort):
    original: FiniteResponseLawPreparedStorePort

    def import_locked_prefixes(self, lock) -> None:
        from empirical_lawhood.domains.matrix.finite_response_law.control_locking import execution_prefix_id
        from empirical_lawhood.domains.matrix.finite_response_law.control_parent import authenticate_parent_reservations

        authenticate_parent_reservations(lock, self.original, before_parent=True)
        for design, parent in zip(lock.designs, lock.parents, strict=True):
            key = execution_prefix_id(design.root_id, design.policy_id)
            prefix = self.original.load_prepared(key)
            for event, record in zip(prefix.events, (design, parent), strict=True):
                artifact = self.publish_prepared_record(prefix_id=key, object_id=event.subject.object_id, record=record)
                if artifact != event.subject_artifact:
                    raise ValueError("Retained choice changes an original prepared subject")
            initial = replace(prefix, events=prefix.events[:1])
            self.create_prepared(initial)
            current = self.load_prepared(key)
            if current == initial:
                self.compare_and_append_prepared(expected_prefix_sha256=initial.fingerprint(), updated=prefix)
            elif current.events[:2] != prefix.events:
                raise ValueError("Retained choice conflicts with the published prepared prefix")

    def publish_prepared_record(
        self, *, prefix_id: str, object_id: str, record: CanonicalRecord
    ) -> ArtifactIdentity:
        if isinstance(record, CompiledLeastMagnitudeControllerStudy):
            # Late binding republishes this exact pre-parent controller.
            # Its original guarded store already owns the complete bytes.
            raw = record.canonical_bytes()
            subject = ObjectIdentity.from_record(object_id, record)
            artifact = ArtifactIdentity(object_id, "prepared-control-record", record.SCHEMA,
                                        subject.object_fingerprint, "application/json", len(raw))
            if self.original.read_prepared_record(prefix_id=prefix_id, subject=subject, artifact=artifact) != raw:
                raise ValueError("Retained compiled controller differs from its original prepared record")
            return artifact
        return super().publish_prepared_record(prefix_id=prefix_id, object_id=object_id, record=record)

    def read_prepared_record(
        self, *, prefix_id: str, subject: ObjectIdentity, artifact: ArtifactIdentity
    ) -> bytes:
        if subject.object_schema in (PreparedCommonStartBinding.SCHEMA, CompiledLeastMagnitudeControllerStudy.SCHEMA):
            return self.original.read_prepared_record(prefix_id=prefix_id, subject=subject, artifact=artifact)
        return super().read_prepared_record(prefix_id=prefix_id, subject=subject, artifact=artifact)

    def verify_prepared_subject(
        self, *, prefix_id: str, subject: ObjectIdentity, artifact: ArtifactIdentity
    ) -> None:
        self.read_prepared_record(prefix_id=prefix_id, subject=subject, artifact=artifact)


@dataclass(frozen=True)
class FiniteResponseLawControlRuntimeBinding:
    root: GuardedExternalRoot
    run_id: str
    prepared_store: FiniteResponseLawPreparedStorePort
    issued_study: ObjectIdentity
    prerequisite_authority: ObjectIdentity
    authority: ObjectIdentity
    grantee_id: str
    compiler_release_id: str
    reveal_authority_id: str | None = None

    def __post_init__(self) -> None:
        for value in (self.run_id, self.grantee_id, self.compiler_release_id):
            validate_stable_id(value, field_name="prospective evaluation runtime identity")
        if self.prepared_store.root != self.root:
            raise ValueError("Finite response-law evaluation runtime substitutes its prepared-store root")
        if self.authority.object_schema != StudyOperationAuthority.SCHEMA:
            raise ValueError(
                "Finite response-law evaluation runtime requires an actual operation authority identity"
            )

    def execution_authority(self) -> StudyOperationAuthority:
        record = ExternalStudyOperationAuthorityStore(
            ExternalArtifactPlane(self.root)
        ).load(self.authority.object_id)
        if ObjectIdentity.from_record(record.authority_id, record) != self.authority:
            raise ValueError(
                "Finite response-law evaluation execution authority differs from its frozen runtime identity"
            )
        return record

    def outcome_authority(self) -> StudyOperationAuthority:
        from empirical_lawhood.storage.study_issue import PROGRAMME_REVEAL_GRANTEE_ID

        if self.reveal_authority_id is None:
            raise PermissionError(
                "Finite response-law evaluation outcomes remain sealed without a reveal authority binding"
            )
        record = ExternalStudyOperationAuthorityStore(
            ExternalArtifactPlane(self.root)
        ).load(self.reveal_authority_id)
        require_study_authority(
            record,
            kind=StudyAuthorityKind.OUTCOME_REVEAL,
            subject=self.issued_study,
            prerequisite_authority=self.authority,
            grantee_id=PROGRAMME_REVEAL_GRANTEE_ID,
            at_utc=self.now(),
        )
        return record

    def dependency_receipt(
        self, run_id: str, binding: DependencyReceiptBinding
    ) -> CanonicalTaskReceipt:
        if run_id != self.run_id:
            raise ValueError("Finite response-law evaluation control cannot read receipts from a different run")
        receipt = ExternalTaskReceiptStore(
            ExternalArtifactPlane(self.root)
        ).read_by_receipt_id(run_id, binding.task_id, binding.receipt_id)
        if (
            receipt is None
            or receipt.receipt_id != binding.receipt_id
            or receipt.run_id != run_id
            or receipt.task_id != binding.task_id
            or not set(binding.output_materialization_ids).issubset(
                {m.materialization_id for m in receipt.output_materializations}
            )
        ):
            raise ValueError(
                "Finite response-law evaluation dependency differs from its exact committed task receipt"
            )
        return receipt

    def now(self) -> str:
        return (
            datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
        )


@dataclass(frozen=True)
class RetainedControlRuntimeBinding(FiniteResponseLawControlRuntimeBinding):
    original_run_id: str = ""
    retained_parents: tuple[ProspectiveRetainedContinuation, ...] = ()

    def original_parent(self, imported, artifact):
        prior = next(p for p in self.retained_parents if p.segment_id == imported.task_id)
        original = ExternalTaskReceiptStore(ExternalArtifactPlane(self.root)).read_by_receipt_id(
            self.original_run_id, imported.task_id, prior.task_receipt.artifact_id)
        if (original is None or original.fingerprint() != prior.task_receipt.sha256
                or original.run_id != self.original_run_id or imported.run_id != self.run_id
                or sorted((a.payload_schema, a.content_sha256) for a in imported.output_logical_artifacts)
                   != sorted((a.payload_schema, a.content_sha256) for a in original.output_logical_artifacts)):
            raise ValueError("Retained evaluation parent differs from its original successful receipt")
        from empirical_lawhood.execution.source_qualification import validate_retained_qualification_receipt
        validate_retained_qualification_receipt(prior, original)
        logical, = (a for a in original.output_logical_artifacts if a.payload_schema == artifact.payload_schema
                    and a.content_sha256 == artifact.sha256 and a.media_type == artifact.media_type)
        return original, replace(artifact, artifact_id=logical.logical_artifact_id)


def retain_evaluation_runtime(runtime, retention):
    from dataclasses import fields
    original = FiniteResponseLawPreparedStorePort(runtime.root,
        f"runs/{retention.donor_run_id}/prepared-execution-events", runtime.prepared_store.minimum_free_bytes)
    store = RetainedPreparedStorePort(runtime.root, runtime.prepared_store.relative_root, original.minimum_free_bytes, original)
    return RetainedControlRuntimeBinding(**{f.name: getattr(runtime, f.name)
        for f in fields(FiniteResponseLawControlRuntimeBinding) if f.name != "prepared_store"},
        prepared_store=store, original_run_id=retention.donor_run_id, retained_parents=retention.parents)


def prospective_evaluation_platform_ports(
    root: GuardedExternalRoot,
    payload_reader: Any,
    *,
    runtime: FiniteResponseLawControlRuntimeBinding,
) -> tuple[Any, ...]:
    """Distinct provider port keys, one existing authoritative store configuration."""
    from empirical_lawhood.domains.matrix.finite_response_law.control_ports import CONTROL_RUNTIME_PORT, REVEAL_CONTROL_PORT, SEALED_CONTROL_PORT, SOURCE_CONTROL_PORT
    from empirical_lawhood.domains.matrix.finite_response_law.method_provider import CANDIDATE_PAYLOAD_PORT, INPUT_RESOLVER_PORT
    from empirical_lawhood.storage.candidate_sources import ExternalContentAddressedInputResolver
    from empirical_lawhood.execution.executable_bindings import ExecutablePlatformPort

    values: dict[str, Any] = {
        k: runtime
        for k in (
            CONTROL_RUNTIME_PORT,
            SOURCE_CONTROL_PORT,
            SEALED_CONTROL_PORT,
            REVEAL_CONTROL_PORT,
        )
    }
    values[CANDIDATE_PAYLOAD_PORT] = payload_reader
    values[INPUT_RESOLVER_PORT] = ExternalContentAddressedInputResolver(root)
    return tuple(ExecutablePlatformPort(k, values[k]) for k in sorted(values))
