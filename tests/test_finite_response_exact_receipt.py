# SPDX-License-Identifier: MPL-2.0
"""Exact receipt custody in disposable stores, without execution or retry grants."""

from dataclasses import dataclass, replace
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import ClassVar

import pytest

from tests.test_doctor_profile import _profile
from empirical_lawhood.domains.matrix.finite_response_law.assigned_native_records import FiniteResponseLawAssignedEvaluationInterface
from empirical_lawhood.domains.matrix.finite_response_law.evaluation_native_records import FiniteResponseLawEvaluationInterface
from empirical_lawhood.domains.matrix.finite_response_law.instruments import REFERENCE_INSTRUMENT
from empirical_lawhood.domains.matrix.finite_response_law.runtime_ports import FiniteResponseLawControlRuntimeBinding, FiniteResponseLawPreparedStorePort, RetainedPreparedStorePort
from empirical_lawhood.execution.controller_evaluation_nested import PreparedCommonStartBinding
from empirical_lawhood.design.nested_controller_evaluation import CommonStartControllerEvaluationPlan
from empirical_lawhood.storage.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.storage.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.design.study_issue import StudyOperationAuthority
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt
from empirical_lawhood.execution.execution import DependencyReceiptBinding
from empirical_lawhood.execution.operator_profile import resolve_external_root_contract


RUN = "synthetic-run"
TASK = "synthetic.pure-projection"


@dataclass(frozen=True)
class SyntheticOperand(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/tests/exact-receipt-operand"
    value: str


@pytest.fixture
def custody():
    with TemporaryDirectory(prefix="exact-finite-receipt-", dir="/dev/shm") as directory:
        root = Path(directory)
        (root / "artifacts").mkdir()
        profile = _profile(root)
        repo = Path(__file__).resolve().parents[1]
        guarded = GuardedExternalRoot(
            resolve_external_root_contract(profile, repo_root=repo, home_root=Path.home())
        )
        plane = ExternalArtifactPlane(guarded)
        identity = ObjectIdentity(
            "synthetic.identity", "empirical-lawhood/tests/synthetic", "1.0.0", "a" * 64
        )
        authority = replace(identity, object_schema=StudyOperationAuthority.SCHEMA)
        runtime = FiniteResponseLawControlRuntimeBinding(
            guarded,
            RUN,
            FiniteResponseLawPreparedStorePort(guarded, "synthetic/prepared", 1),
            identity,
            identity,
            authority,
            "operator.execution-service",
            "synthetic.compiler",
        )
        yield plane, ExternalTaskReceiptStore(plane), runtime


def publish_receipt(plane, store, attempt):
    writes = []
    for member in ("a", "b"):
        record = SyntheticOperand(attempt + member)
        writes.append(
            plane.write(
                ArtifactWriteRequest(
                    logical_artifact_id=f"synthetic.{attempt}.{member}",
                    relative_path=f"synthetic/{attempt}/{member}.json",
                    payload_schema=record.SCHEMA,
                    profile=ArtifactProfile.CANONICAL_JSON,
                    media_type="application/json",
                    publication_scope_id=f"synthetic.{attempt}",
                    publication_scope_relative_root=f"synthetic/{attempt}",
                    payload=record.canonical_bytes(),
                    visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
                    parent_visibility_ceilings=(),
                    outcome_access=OutcomeAccess.OUTCOME_BLIND,
                    minimum_free_bytes=1,
                )
            )
        )
    writes.sort(key=lambda item: item.materialization.materialization_id)
    receipt = CanonicalTaskReceipt(
        f"receipt.{attempt}", RUN, TASK, attempt, "0" * 40, (),
        tuple(item.materialization for item in writes),
        tuple(item.logical for item in writes), (), OperationalStatus.SUCCEEDED, (),
    )
    store.commit(
        receipt,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
        outcome_access=OutcomeAccess.OUTCOME_BLIND,
    )
    return receipt


def binding(receipt, *, subset=False):
    ids = tuple(item.materialization_id for item in receipt.output_materializations)
    return DependencyReceiptBinding(receipt.receipt_id, TASK, ids[:1] if subset else ids)


def test_exact_repair_receipt_selected_without_earlier_attempt_fallback(custody):
    plane, store, runtime = custody
    earlier = publish_receipt(plane, store, f"{RUN}.{TASK}.attempt-001")
    exact = publish_receipt(plane, store, f"{RUN}.{TASK}.repair-0123456789ab.attempt-002")
    assert runtime.dependency_receipt(RUN, binding(exact)) == exact
    assert runtime.dependency_receipt(RUN, binding(exact, subset=True)) == exact
    missing = replace(binding(earlier), receipt_id=f"receipt.{RUN}.{TASK}.attempt-003")
    with pytest.raises(ValueError, match="exact committed task receipt"):
        runtime.dependency_receipt(RUN, missing)


def test_exact_receipt_rejects_run_task_and_materialization_substitution(custody):
    plane, store, runtime = custody
    exact = publish_receipt(plane, store, f"{RUN}.{TASK}.attempt-001")
    with pytest.raises(ValueError, match="different run"):
        runtime.dependency_receipt("synthetic-other-run", binding(exact))
    with pytest.raises(ValueError, match="exact committed task receipt"):
        runtime.dependency_receipt(RUN, replace(binding(exact), task_id="synthetic.other-task"))
    with pytest.raises(ValueError, match="exact committed task receipt"):
        runtime.dependency_receipt(
            RUN, replace(binding(exact), output_materialization_ids=("synthetic.unknown",))
        )


def test_exact_receipt_requires_authenticated_original_publication(custody):
    plane, store, runtime = custody
    exact = publish_receipt(plane, store, f"{RUN}.{TASK}.attempt-001")
    path = plane.root.resolve(
        f"runs/{RUN}/receipts/{TASK}/{exact.attempt_id}.json", for_write=False
    )
    path.write_bytes(exact.canonical_bytes() + b" ")
    with pytest.raises(ArtifactIdentityConflict):
        runtime.dependency_receipt(RUN, binding(exact))


def test_continuation_authenticates_the_original_common_start(custody):
    _, _, runtime = custody
    original = runtime.prepared_store
    store = RetainedPreparedStorePort(original.root, "continued-events", original.minimum_free_bytes, original)
    checkpoint = ObjectIdentity("source.checkpoint", "empirical-lawhood/tests/checkpoint", "1.0.0", "1" * 64)
    plan = replace(checkpoint, object_id="source.plan", object_schema=CommonStartControllerEvaluationPlan.SCHEMA)
    assignment = replace(checkpoint, object_id="source.root", object_schema="empirical-lawhood/planning/prepared-root-assignment")
    anchor = PreparedCommonStartBinding("source.start", plan, assignment, checkpoint)
    subject = ObjectIdentity.from_record(anchor.binding_id, anchor)
    artifact = original.publish_prepared_record(prefix_id=anchor.binding_id, object_id=anchor.binding_id, record=anchor)
    assert store.read_prepared_record(prefix_id=anchor.binding_id, subject=subject, artifact=artifact) == anchor.canonical_bytes()
    with pytest.raises(ArtifactIdentityConflict):
        store.verify_prepared_subject(prefix_id=anchor.binding_id, subject=replace(subject, object_fingerprint="2" * 64), artifact=artifact)


@pytest.mark.parametrize(
    "interface_type",
    (FiniteResponseLawEvaluationInterface, FiniteResponseLawAssignedEvaluationInterface),
)
def test_parent_join_persists_observed_handoff_in_its_original_schema(custody, interface_type):
    _, _, runtime = custody
    checkpoint_type = interface_type.CHECKPOINT_TYPE
    checkpoint = ObjectIdentity(
        "synthetic.parent.r1.checkpoint", checkpoint_type.SCHEMA, checkpoint_type.VERSION, "0" * 64
    )
    handoff = interface_type(checkpoint, REFERENCE_INSTRUMENT.identity, 4368, (Decimal("0"),) * 24)
    subject = ObjectIdentity.from_record("synthetic.actual-handoff", handoff)
    store = runtime.prepared_store
    artifact = store.publish_prepared_record(
        prefix_id=RUN, object_id=subject.object_id, record=handoff
    )
    recovered = store.read_prepared_record(prefix_id=RUN, subject=subject, artifact=artifact)
    assert recovered == handoff.canonical_bytes()
