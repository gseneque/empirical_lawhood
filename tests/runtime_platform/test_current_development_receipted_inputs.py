# SPDX-License-Identifier: MPL-2.0
"""Canonical software custody, not native completion or scientific authority.

Exercise the first dependent publication hash before worker preparation. The
small supplied product/receipt only tests receipt and lineage admission.
"""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.api.current_task_custody import CurrentDevelopmentTaskCustody
from empirical_lawhood.api.recursive_execution import _external_inputs
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import (
    ArtifactLineageParent, ArtifactManifest, ArtifactWriteRequest, CanonicalTaskReceipt,
    ReceiptCheck, lineage_parent_sort_key,
)
from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryIndex
from tests.runtime_platform.test_recursive_compiler import Config
from tests.runtime_platform.test_recursive_revealed_followup import PAIR, compile_revealed, revealed_fixture
from tests.test_recursive_public_service import _plane


class _CurrentOriginalAccess:
    def __init__(self):
        self.current = True
        self.samples = 0

    def require_current(self):
        self.samples += 1
        if not self.current:
            raise PermissionError("actual current original grant refused")

    def require_member(self, manifest):
        raise PermissionError("unowned protected member lacks original ancestry")


def _case(tmp_path, *, retain_receipt=True, bad_lineage=False, duplicate_success=False, plane_factory=_plane):
    draft, registrations, registry = revealed_fixture()
    draft = replace(draft, operations=tuple(replace(row, maximum_attempts=2) for row in draft.operations))
    compiled = compile_revealed(draft, registrations, registry)
    plane = plane_factory(tmp_path / "receipted-inputs")
    inputs = _external_inputs(plane=plane, plan=compiled.execution_plan, draft=compiled.draft,
        payloads={row.node_id: row.payload for row in compiled.config_inputs}, read_only=False)
    task = next(row for row in compiled.execution_plan.tasks if row.task_id == "source")
    assert not task.dependency_task_ids
    selected = tuple(value for value in inputs if value.logical.logical_artifact_id in task.external_input_artifact_ids)
    parents = tuple(sorted((ArtifactLineageParent(
        ObjectIdentity.from_record(value.logical.logical_artifact_id, value.logical),
        value.logical.visibility_ceiling, value.logical.outcome_access) for value in selected), key=lineage_parent_sort_key))
    output, = task.outputs
    product = Config("product.disclosed-receipt-join", 7)
    publication = plane.write(ArtifactWriteRequest(output.logical_artifact_id, output.relative_path,
        product.SCHEMA, output.profile, output.media_type, compiled.run_plan.run_plan_id,
        "runs/" + compiled.run_plan.run_plan_id, product.canonical_bytes(), PAIR[1],
        () if bad_lineage else tuple(parent.visibility_ceiling for parent in parents), PAIR[0],
        lineage_parents=() if bad_lineage else parents))
    index = DevelopmentRunRecoveryIndex.from_execution_plan(compiled.execution_plan,
        run_id=compiled.run_plan.run_plan_id, wave_id="wave.development", authority_identities=())
    attempt = index.task(task.task_id).attempts[0]
    receipt = CanonicalTaskReceipt("receipt." + attempt.attempt_id, index.run_id, task.task_id,
        attempt.attempt_id, compiled.execution_plan.implementation_commit,
        tuple(sorted(value.materialization.materialization_id for value in selected)),
        (publication.materialization,), (publication.logical,),
        (ReceiptCheck("disclosed-software-value", True, ()),), OperationalStatus.SUCCEEDED, ())
    if retain_receipt:
        ExternalTaskReceiptStore(plane).commit(receipt, visibility_ceiling=PAIR[1], outcome_access=PAIR[0])
    if duplicate_success:
        second = index.task(task.task_id).attempts[1]
        duplicate = replace(receipt, receipt_id="receipt." + second.attempt_id, attempt_id=second.attempt_id)
        ExternalTaskReceiptStore(plane).commit(duplicate, visibility_ceiling=PAIR[1], outcome_access=PAIR[0])
    # The authenticated constructor is covered by public lifecycle checks. This
    # isolates the subsequent first-hash boundary using real canonical storage.
    custody = object.__new__(CurrentDevelopmentTaskCustody)
    custody.writer, custody.plan, custody.run, custody.index = plane, compiled.execution_plan, compiled.run_plan, index
    custody.inputs = {value.logical.logical_artifact_id: value for value in inputs}
    custody._original_member_facts = {(value.logical, value.materialization) for value in inputs}
    custody.original_input_access = _CurrentOriginalAccess()
    custody.access_pair = PAIR
    manifest = plane.read_manifest(publication.materialization.relative_path)
    return SimpleNamespace(custody=custody, plane=plane, manifest=manifest)


def test_first_dependent_body_hash_authenticates_its_actual_receipt_and_lineage(tmp_path):
    value = _case(tmp_path)
    fact = value.manifest.logical, value.manifest.materialization
    assert fact not in value.custody._original_member_facts
    value.plane.verify_manifest(value.manifest, before_member=value.custody.require_input_member)
    assert fact in value.custody._original_member_facts
    assert value.custody.original_input_access.samples >= 2


@pytest.mark.parametrize("damage", ("missing-receipt", "duplicate-success", "changed-lineage", "foreign-materialization", "unowned-output"))
def test_first_hash_refuses_missing_or_substituted_producer_custody(tmp_path, damage):
    value = _case(tmp_path, retain_receipt=damage != "missing-receipt", bad_lineage=damage == "changed-lineage",
        duplicate_success=damage == "duplicate-success")
    manifest = value.manifest
    if damage == "foreign-materialization":
        manifest = ArtifactManifest(manifest.logical,
            replace(manifest.materialization, physical_sha256="f" * 64))
    elif damage == "unowned-output":
        manifest = ArtifactManifest(replace(manifest.logical, logical_artifact_id="foreign.protected.output"),
            replace(manifest.materialization, logical_artifact_id="foreign.protected.output"))
    with pytest.raises(PermissionError, match="producer receipt|input lineage|producer publication|original ancestry"):
        value.custody.require_input_member(manifest)
    assert (manifest.logical, manifest.materialization) not in value.custody._original_member_facts


def test_retained_descendant_facts_do_not_cache_current_original_permission(tmp_path):
    value = _case(tmp_path)
    value.plane.verify_manifest(value.manifest, before_member=value.custody.require_input_member)
    value.custody.original_input_access.current = False
    with pytest.raises(PermissionError, match="current original grant refused"):
        value.plane.verify_manifest(value.manifest, before_member=value.custody.require_input_member)
