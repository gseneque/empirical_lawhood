# SPDX-License-Identifier: MPL-2.0
"""Read-only custody of original effective-law post-hoc records.

The unregistered private execution loop has been retired. These readers retain
its existing envelope, receipt, lineage and byte checks without any path to a
scientific calculation, publication, or automatic replay.
"""
from __future__ import annotations
import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Protocol
from empirical_lawhood.science.records.serialization import CanonicalRecord, canonical_json_bytes, validate_relative_locator, validate_stable_id
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.storage.contracts.artifacts import ArtifactManifest, ArtifactMaterialization, ArtifactProfile, ArtifactSemanticValidation, ArtifactSemanticValidationRegistration, ArtifactSemanticValidationRegistry, ArtifactWriteResult, CanonicalTaskReceipt
from empirical_lawhood.execution.plans import CandidateExecutionPlan

MAXIMUM_DOCUMENT_BYTES = 16 * 1024**2


class PosthocExternalRoot(Protocol):
    def resolve(
        self,
        relative_path: str,
        *,
        for_write: bool,
        operation_minimum_free_bytes: int = 0,
    ) -> Path: ...



class PosthocArtifactPlane(Protocol):
    def verify(self, materialization: ArtifactMaterialization) -> None: ...

    def verify_manifest(self, manifest: ArtifactManifest) -> None: ...



@dataclass(frozen=True, slots=True)
class EffectiveLawPosthocReadPorts:
    """Read-only original storage and receipt verification capabilities."""

    root: PosthocExternalRoot
    plane_for_registry: Callable[
        [ArtifactSemanticValidationRegistry],
        PosthocArtifactPlane,
    ]
    decode_artifact_manifest: Callable[[bytes], ArtifactManifest]
    decode_task_receipt: Callable[[bytes], CanonicalTaskReceipt]
    run_root: str
    run_id: str

    def __post_init__(self) -> None:
        validate_relative_locator(self.run_root)
        validate_stable_id(self.run_id)



@dataclass(frozen=True, slots=True)
class RetainedPosthocTask:
    task_id: str
    document: Mapping[str, object]
    result: ArtifactWriteResult
    receipt: CanonicalTaskReceipt
    recovered: bool = False



def _stable_payload(document: Mapping[str, object] | CanonicalRecord) -> bytes:
    def canonical_container(value: object) -> object:
        if isinstance(value, list):
            return tuple(canonical_container(item) for item in value)
        if isinstance(value, Mapping):
            return {str(key): canonical_container(item) for key, item in value.items()}
        return value

    payload = canonical_json_bytes(canonical_container(document))
    if len(payload) > MAXIMUM_DOCUMENT_BYTES:
        raise ValueError("post-hoc document exceeds its byte bound")
    return payload



def _semantic_validation(
    logical_artifact_id: str,
    document: Mapping[str, object],
    implementation_sha256: str,
) -> ArtifactSemanticValidation:
    value = document.get("value")
    if set(document) != {"schema", "value", "version"} or not isinstance(value, Mapping):
        raise ValueError("published post-hoc document is not a canonical envelope")
    return ArtifactSemanticValidation(
        validator_key=f"posthoc-json.{logical_artifact_id}",
        validator_version="1.0.0",
        validator_implementation_sha256=implementation_sha256,
        payload_schema=str(document["schema"]),
        profile=ArtifactProfile.CANONICAL_JSON,
        top_level_keys=("schema", "value", "version"),
        value_keys=tuple(sorted(str(key) for key in value)),
        field_bindings=(),
    )



def _source_materialization_id(artifact_id: str, fingerprint: str) -> str:
    return f"source.{artifact_id}.{fingerprint[:16]}"



def _external_source_materialization_id(
    artifact_id: str,
    expected_content_sha256: str | None,
) -> str:
    if expected_content_sha256 is None:
        raise ValueError(f"post-hoc external source lacks a content identity: {artifact_id}")
    return _source_materialization_id(artifact_id, expected_content_sha256)



def read_published_task(
    *,
    ports: EffectiveLawPosthocReadPorts,
    task_id: str,
    implementation_commit: str,
    implementation_sha256: str,
    expected_input_materialization_ids: Sequence[str],
) -> RetainedPosthocTask | None:
    """Read one exact terminal task; no computation, writing or retry is available."""

    root = ports.root
    output_relative = f"{ports.run_root}/outputs/{task_id}/result.json"
    receipt_relative = f"{ports.run_root}/receipts/{task_id}/attempt-001.json"
    required = (
        output_relative,
        f"{output_relative}.manifest.json",
        receipt_relative,
        f"{receipt_relative}.manifest.json",
    )
    paths = tuple(root.resolve(value, for_write=False) for value in required)
    present = tuple(path.is_file() for path in paths)
    if not any(present):
        return None
    if not all(present):
        raise ValueError(f"partial published state for task {task_id}")

    output_manifest = ports.decode_artifact_manifest(read_bounded_bytes(paths[1], maximum_bytes=1024 * 1024))
    verify_published_artifact(
        output_relative,
        ports=ports,
        implementation_sha256=implementation_sha256,
    )
    verify_published_artifact(
        receipt_relative,
        ports=ports,
        implementation_sha256=implementation_sha256,
    )
    receipt = ports.decode_task_receipt(read_bounded_bytes(paths[2], maximum_bytes=MAXIMUM_DOCUMENT_BYTES))
    if (
        receipt.run_id != ports.run_id
        or receipt.task_id != task_id
        or receipt.attempt_id != "attempt-001"
        or receipt.implementation_commit != implementation_commit
        or receipt.operational_status is not OperationalStatus.SUCCEEDED
        or not all(check.passed for check in receipt.checks)
    ):
        raise ValueError(f"task receipt does not authorize recovery: {task_id}")
    if receipt.input_materialization_ids != tuple(sorted(set(expected_input_materialization_ids))):
        raise ValueError(f"task receipt input closure drifted: {task_id}")
    if receipt.output_materializations != (output_manifest.materialization,):
        raise ValueError(f"task receipt output materialization drifted: {task_id}")
    if receipt.output_logical_artifacts != (output_manifest.logical,):
        raise ValueError(f"task receipt logical output drifted: {task_id}")

    payload = read_bounded_bytes(paths[0], maximum_bytes=MAXIMUM_DOCUMENT_BYTES)
    if len(payload) > MAXIMUM_DOCUMENT_BYTES:
        raise ValueError(f"recovered output exceeds its byte bound: {task_id}")
    document = json.loads(payload)
    if not isinstance(document, Mapping) or _stable_payload(document) != payload:
        raise ValueError(f"recovered output is not canonical JSON: {task_id}")
    if document.get("schema") != output_manifest.logical.payload_schema:
        raise ValueError(f"recovered output schema drifted: {task_id}")

    manifest_payload = read_bounded_bytes(paths[1], maximum_bytes=1024 * 1024)
    manifest_materialization = ArtifactMaterialization(
        materialization_id=f"{ports.run_id}.{task_id}.manifest.attempt-001",
        logical_artifact_id=f"{ports.run_id}.{task_id}.manifest",
        storage_root_id=output_manifest.materialization.storage_root_id,
        relative_path=f"{output_relative}.manifest.json",
        physical_sha256=sha256(manifest_payload).hexdigest(),
        size_bytes=len(manifest_payload),
        compression="none",
        partition_selector=None,
    )
    return RetainedPosthocTask(
        task_id=task_id,
        document=document,
        result=ArtifactWriteResult(
            logical=output_manifest.logical,
            materialization=output_manifest.materialization,
            manifest_materialization=manifest_materialization,
            created=False,
        ),
        receipt=receipt,
        recovered=True,
    )



def verify_published_artifact(
    relative_path: str,
    *,
    ports: EffectiveLawPosthocReadPorts,
    implementation_sha256: str,
) -> str:
    root = ports.root
    payload_path = root.resolve(relative_path, for_write=False)
    sidecar_path = root.resolve(f"{relative_path}.manifest.json", for_write=False)
    manifest = ports.decode_artifact_manifest(read_bounded_bytes(sidecar_path, maximum_bytes=1024 * 1024))
    document = json.loads(read_bounded_bytes(payload_path, maximum_bytes=MAXIMUM_DOCUMENT_BYTES))
    if not isinstance(document, Mapping):
        raise ValueError("published artifact is not a canonical mapping")
    expected = _semantic_validation(
        manifest.logical.logical_artifact_id,
        document,
        implementation_sha256,
    )
    if manifest.logical.semantic_validation != expected:
        raise ValueError("published artifact semantic validator identity drifted")
    registry = ArtifactSemanticValidationRegistry.from_registrations(
        registry_id=f"posthoc-recovery.{manifest.logical.logical_artifact_id}",
        registrations=(
            ArtifactSemanticValidationRegistration(
                logical_artifact_id=manifest.logical.logical_artifact_id,
                validation=expected,
            ),
        ),
    )
    plane = ports.plane_for_registry(registry)
    plane.verify(manifest.materialization)
    plane.verify_manifest(manifest)
    return manifest.materialization.physical_sha256



def verify_complete_run(
    plan: CandidateExecutionPlan,
    *,
    ports: EffectiveLawPosthocReadPorts,
    implementation_commit: str,
) -> dict[str, object]:
    output_rows = []
    published: dict[str, RetainedPosthocTask] = {}
    tasks = {task.task_id: task for task in plan.tasks}
    for task_id in plan.topological_task_ids():
        task = tasks[task_id]
        external_by_id = {value.input_id: value for value in task.external_inputs}
        expected_input_ids = []
        for edge in task.scientific_inputs:
            if edge.producer_task_id is not None:
                expected_input_ids.append(
                    published[edge.producer_task_id].result.materialization.materialization_id
                )
            else:
                assert edge.external_input_id is not None
                external = external_by_id[edge.external_input_id]
                expected_input_ids.append(
                    _external_source_materialization_id(
                        external.logical_artifact_id,
                        external.expected_content_sha256,
                    )
                )
        recovered = read_published_task(
            ports=ports,
            task_id=task_id,
            implementation_commit=implementation_commit,
            implementation_sha256=task.capability_implementation_sha256,
            expected_input_materialization_ids=expected_input_ids,
        )
        if recovered is None:
            raise ValueError(f"terminal task is absent during recovery: {task_id}")
        published[task_id] = recovered
        output_path = f"{ports.run_root}/outputs/{task_id}/result.json"
        receipt_path = f"{ports.run_root}/receipts/{task_id}/attempt-001.json"
        output_rows.append(
            {
                "output_sha256": verify_published_artifact(
                    output_path,
                    ports=ports,
                    implementation_sha256=task.capability_implementation_sha256,
                ),
                "receipt_sha256": verify_published_artifact(
                    receipt_path,
                    ports=ports,
                    implementation_sha256=task.capability_implementation_sha256,
                ),
                "task_id": task_id,
            }
        )
    return {
        "schema": 'empirical-lawhood/methods/posthoc-response-composition/recovery-verification',
        "version": "1.0.0",
        "value": {
            "execution_plan_sha256": plan.fingerprint(),
            "output_rows": output_rows,
            "recovered_from_external_artifacts_only": True,
            "receipt_input_closure_verified": True,
            "task_count": len(output_rows),
            "verified": len(output_rows) == 21,
        },
    }

