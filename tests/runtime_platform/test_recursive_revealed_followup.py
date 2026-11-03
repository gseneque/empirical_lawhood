# SPDX-License-Identifier: MPL-2.0
"""Exposed software controls for revealed PURE follow-up; no scientific issue."""

from dataclasses import replace

import pytest

from empirical_lawhood.api.current_task_custody import CurrentDevelopmentTaskCustody
from empirical_lawhood.api.recursive_execution import _external_inputs
from empirical_lawhood.infrastructure.development_native_custody import read_development_native_payload
from empirical_lawhood.infrastructure.recursive_custody import read_exposed_recursive_payload
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactWriteRequest, CanonicalTaskReceipt, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityPermission
from empirical_lawhood.runtime.plans import BarrierKind, DevelopmentExecutionPlan
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryIndex, TaskRecoveryEvent
from tests.runtime_platform.test_recursive_compiler import Config, SourceConfig, fixture
from tests.test_recursive_public_service import _plane


PAIR = OutcomeAccess.EVALUATION_REVEALED, VisibilityCeiling.OUTCOME_VISIBLE


def revealed_fixture():
    draft, registrations, registry = fixture()
    study = replace(draft.development_study, claims=tuple(replace(claim,
        outcome_access=PAIR[0], visibility_ceiling=PAIR[1]) for claim in draft.development_study.claims))
    draft = replace(draft, development_study=study)
    permissions = (CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_OUTCOME_VISIBLE)
    registrations = tuple(replace(row, outcome_access=PAIR[0], visibility_ceiling=PAIR[1],
        required_permissions=permissions) for row in registrations)
    registry = replace(registry, capabilities=tuple(replace(row, maximum_outcome_access=PAIR[0],
        permissions=permissions) for row in registry.capabilities))
    return draft, registrations, registry


def compile_revealed(draft=None, registrations=None, registry=None):
    original = revealed_fixture()
    return compile_recursive_wave(draft=draft or original[0], registrations=registrations or original[1],
        registry=registry or original[2], implementation_commit="1" * 40,
        output_codecs={Config.SCHEMA: Config})


def test_revealed_pure_plan_preserves_role_in_graph_lowering_and_canonical_roundtrip():
    compiled = compile_revealed()
    assert compiled.proof.node_count == 2
    assert compiled.draft.development_study.access_pair == PAIR
    for task in compiled.execution_plan.tasks:
        assert task.capability.requested_outcome_access is PAIR[0]
        assert all((output.outcome_access, output.visibility_ceiling) == PAIR for output in task.outputs)
        assert all((item.expected_outcome_access, item.expected_visibility_ceiling) == PAIR for item in task.external_inputs)
    raw = compiled.execution_plan.canonical_bytes()
    assert decode_canonical_bytes(raw, DevelopmentExecutionPlan, maximum_bytes=len(raw)).canonical_bytes() == raw


@pytest.mark.parametrize("changed", ("native", "barrier", "registration", "claim-pair"))
def test_revealed_followup_refuses_effects_and_role_substitutions_before_lowering(changed):
    draft, registrations, registry = revealed_fixture()
    if changed == "native":
        registrations = (replace(registrations[0], native_effect=True), registrations[1])
    elif changed == "barrier":
        registrations = (replace(registrations[0], barrier=BarrierKind.FREEZE), registrations[1])
    elif changed == "registration":
        registrations = (replace(registrations[0], outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
            visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY), registrations[1])
    else:
        claim = replace(draft.development_study.claims[0], outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
        draft = replace(draft, development_study=replace(draft.development_study, claims=(claim,)))
    with pytest.raises(ValueError, match="pure operations|exposed scientific access|exact exposed claim access pair"):
        compile_revealed(draft, registrations, registry)


def test_revealed_aliases_preserve_exact_role_and_custody_control_bytes(tmp_path):
    compiled = compile_revealed()
    plane = _plane(tmp_path / "revealed-aliases")
    payloads = {row.node_id: row.payload for row in compiled.config_inputs}
    values = _external_inputs(plane=plane, plan=compiled.execution_plan, draft=compiled.draft,
        payloads=payloads, read_only=False)
    custody = CurrentDevelopmentTaskCustody.__new__(CurrentDevelopmentTaskCustody)
    custody.writer, custody.access_pair = plane, PAIR
    for value in values:
        assert (value.logical.outcome_access, value.logical.visibility_ceiling) == PAIR
        path = plane.root.resolve(value.materialization.relative_path + ".manifest.json", for_write=False)
        manifest = decode_artifact_manifest(path.read_bytes(), maximum_bytes=None)
        raw = read_exposed_recursive_payload(plane, manifest, maximum_bytes=value.materialization.size_bytes)
        codec = SourceConfig if manifest.logical.payload_schema == SourceConfig.SCHEMA else type(compiled.config_inputs[1].record)
        assert custody.control_record(manifest, codec, len(raw)).canonical_bytes() == raw
        with pytest.raises(ValueError, match="another access role"):
            read_development_native_payload(plane, manifest, maximum_bytes=len(raw))
    assert _external_inputs(plane=plane, plan=compiled.execution_plan, draft=compiled.draft,
        payloads=payloads, read_only=True) == values


def test_recovery_event_inherits_actual_revealed_receipt_without_relabeling(tmp_path):
    compiled = compile_revealed()
    plane = _plane(tmp_path / "revealed-recovery")
    plan = compiled.execution_plan
    index = DevelopmentRunRecoveryIndex.from_execution_plan(plan, run_id=compiled.run_plan.run_plan_id,
        wave_id="wave.development", authority_identities=())
    store = ExternalRunRecoveryStore(plane)
    store.freeze(index)
    task = plan.tasks[0]
    output = task.outputs[0]
    product = Config("product.disclosed-software-control", 7)
    publication = plane.write(ArtifactWriteRequest(output.logical_artifact_id, output.relative_path,
        product.SCHEMA, output.profile, output.media_type, index.run_id, "runs/" + index.run_id,
        product.canonical_bytes(), PAIR[1], (), PAIR[0]))
    attempt = index.task(task.task_id).attempts[0]
    receipt = CanonicalTaskReceipt("receipt." + attempt.attempt_id, index.run_id, task.task_id,
        attempt.attempt_id, plan.implementation_commit, (), (publication.materialization,), (publication.logical,),
        (ReceiptCheck("disclosed-software-value", product.scalar == 7, ()),), OperationalStatus.SUCCEEDED, ())
    event = TaskRecoveryEvent.from_receipt(index, receipt)
    store.append_event(index, event, receipt=receipt)
    path = plane.root.resolve(attempt.event_relative_path + ".manifest.json", for_write=False)
    manifest = decode_artifact_manifest(path.read_bytes(), maximum_bytes=None)
    assert (manifest.logical.outcome_access, manifest.logical.visibility_ceiling) == PAIR
    assert ObjectIdentity.from_record(receipt.receipt_id, receipt) in tuple(parent.identity for parent in manifest.logical.lineage_parents)
    assert store.read_event(index, attempt.event_relative_path) == event
