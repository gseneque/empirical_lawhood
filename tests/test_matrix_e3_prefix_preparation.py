# SPDX-License-Identifier: MPL-2.0
"""Exposed direct-input and preparation controls; no worker or native entry."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.composition.discovery import manifest as capability_manifest
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_prefix_preparation as owner
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_prefix_records import ProtectedE3PrefixHistory
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_source_records import (
    NAMESPACE, ProtectedE3SourceConfig, ProtectedE3SourcePhase, identity, source_task_id,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as sr
from empirical_lawhood.adapters.methods.matrix_scheduled_history.compact_records import compact_identity
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history_segments as segments
from empirical_lawhood.infrastructure.execution import _prepare_native_work, prepare_worker_invocation
from empirical_lawhood.infrastructure.prepared_native_invocation import (
    NativeInputPublication, prepare_native_invocation, validate_prepared_native_invocation,
)
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityKind, CapabilityPermission, CapabilityRequirement
from empirical_lawhood.runtime.execution import TaskContext, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec, ScientificStage
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
from tests.test_matrix_e3_protected_source_records import case as case  # noqa: F401
from tests.test_matrix_e3_protected_source_records import scheduled as scheduled  # noqa: F401
from tests.test_matrix_factor_confirmation_eligibility import stock as stock, provenance as provenance  # noqa: F401


ACCESS = OutcomeAccess.OUTCOME_BLIND
VISIBILITY = VisibilityCeiling.PROSPECTIVE
BUDGET = ResourceBudget(1, None, 0, None, None, None)


def _callback(*, runner, context, expected_parent):
    return owner.prepare_protected_e3_prefix_work(context=context, expected_parent=expected_parent,
        capability=runner.manifest)


def _context(case, *, damage=None):
    source = next(row for row in case.sources if row.root.root.role.value == "CALIBRATION")
    descriptor = next(row for row in case.descriptors if row.root_id == source.root_id)
    config = ProtectedE3SourceConfig("config." + source_task_id(source.root_id, ProtectedE3SourcePhase.PREFIX),
        ProtectedE3SourcePhase.PREFIX, case.inputs.specification.identity, identity(case.manifest), descriptor)
    records = [(config.record_id, config), (case.manifest.record_id, case.manifest),
        (case.inputs.specification.specification_id, case.inputs.specification),
        (descriptor.source_id, descriptor), (source.coordinate.coordinate_id, source.coordinate),
        (source.provenance.identity.object_id, source.provenance),
        *((source.root.stream_identity(stream).object_id, stream) for stream in source.root.streams)]
    if damage == "missing-descriptor":
        records = [(key, row) for key, row in records if row is not descriptor]
    elif damage == "coordinate":
        records = [(key, replace(row, coordinate_id="coordinate.foreign") if row is source.coordinate else row)
            for key, row in records]
    elif damage == "provenance":
        records = [(key, replace(row, observed_git_head="b" * 40) if row is source.provenance else row)
            for key, row in records]
    elif damage == "stream":
        records[-1] = (records[-1][0], replace(records[-1][1], digest_sha256="9" * 64))
    elif damage == "missing-stream":
        records.pop()
    elif damage == "undeclared-allocation":
        # Resolved sources are operation-local views, not publishable records.
        # A second direct copy of their whole allocation is still undeclared.
        records.append((source.allocation.allocation_id, source.allocation))
    elif damage == "duplicate-descriptor":
        records.append(("descriptor.duplicate", descriptor))
    bundle = prepare_native_invocation(case.plane,
        publications=tuple(NativeInputPublication(key, record) for key, record in records),
        relative_root="exposed-prefix-work-inputs", visibility=VISIBILITY, access=ACCESS)
    capability = capability_manifest("prefix", ProtectedE3SourceConfig, CapabilityKind.SIMULATOR,
        tuple(sorted({record.SCHEMA for _, record in records})),
        tuple(sorted((ProtectedE3PrefixHistory.SCHEMA, MATRIX_ARRAY_SCHEMA, sr.ScheduledCheckpoint.SCHEMA))),
        EvidenceCeiling.RESPONSE, ACCESS, None, namespace=NAMESPACE, resources=BUDGET,
        read_permission=CapabilityPermission.READ_FROZEN_MODELS,
        implementation_id="EXPOSED-UNINSTALLED-prefix-preparation-control",
        conformance_ids=("exposed-direct-inputs-no-native-entry",))
    task_id = source_task_id(source.root_id, ProtectedE3SourcePhase.PREFIX)
    outputs = tuple(sorted((WorkerOutputPort(task_id + "." + name, schema, profile, media,
        "ordinary." + task_id + "." + name) for name, schema, profile, media in (
            ("arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz"),
            ("checkpoint", sr.ScheduledCheckpoint.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json"),
            ("product", ProtectedE3PrefixHistory.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json"))),
        key=lambda row: row.output_id))
    reference = CapabilityConfigRef(config.record_id, config.SCHEMA, capability.config_schema_sha256,
        config.fingerprint(), config.record_id)
    context = TaskContext("run.exposed.e3-prefix", task_id, "attempt.exposed.e3-prefix", reference,
        bundle.input_bindings, bundle.input_ports, outputs, capability.permissions, ACCESS, BUDGET,
        WorkerIsolationProfile.TRUSTED_LOCAL)
    requirement = CapabilityRequirement(capability.capability_key, capability.capability_version, capability.kind,
        reference, capability.input_schema_ids, capability.output_schema_ids, capability.permissions,
        EvidenceCeiling.RESPONSE, ACCESS, BUDGET)
    external = tuple(sorted((ExternalInputSpec("input." + row.artifact_id, row.artifact_id,
        row.logical.content_sha256, row.logical.payload_schema, row.logical.media_type, row.materialization.size_bytes,
        VISIBILITY, ACCESS, None) for row in bundle.verified_inputs), key=lambda row: row.input_id))
    task = ExecutionTask(task_id, ScientificStage.ACQUIRE, requirement, capability.implementation_sha256, (), external,
        tuple(ArtifactOutputSpec(port.output_id, port.logical_artifact_id, "exposed-prefix-output/" + port.output_id,
            port.payload_schema, port.profile, port.media_type, VISIBILITY, (), ACCESS) for port in outputs), (),
        BarrierKind.NONE, 1, ("exposed.prefix-input-contract",), scientific_inputs=())
    plan = ObjectIdentity("plan.exposed.e3-prefix", "empirical-lawhood/runtime/candidate-execution-plan", "1.0.0", "a" * 64)
    parent = NativeEffectContact(context.run_id, context.task_id, context.attempt_id, plan,
        ObjectIdentity.from_record(task.task_id, task), source.provenance.observed_git_head,
        context.input_materialization_ids, context.dependency_receipt_ids)
    implementation = RecursiveImplementationBinding(source.provenance.package_sources,
        source.provenance.code_sources_sha256, source.provenance.dependency_lock_sha256,
        source.provenance.observed_git_head, source.provenance.observed_checkout_clean)
    runner = SimpleNamespace(manifest=capability, execute_with_native_subwork=lambda *_: pytest.fail("native entry"))
    return SimpleNamespace(source=source, descriptor=descriptor, config=config, bundle=bundle, capability=capability,
        context=context, task=task, parent=parent, implementation=implementation, runner=runner)


def _work(selected, *, context=None, parent=None):
    return _prepare_native_work(_callback, selected.runner, context or selected.context, parent or selected.parent)


def _bound(selected):
    contract = prepare_worker_invocation(selected.runner, selected.context, selected.bundle.verified_inputs,
        implementation=selected.implementation, execution_plan=selected.parent.execution_plan,
        execution_task=selected.parent.execution_task, execution_task_record=selected.task,
        native_effect=True, native_work_preparer=_callback)
    assert contract.native_preparation_error is None
    return replace(selected.context, prepared_invocation=contract), contract


def test_compact_direct_native_closure_passes_existing_read_only_verifier(case, monkeypatch):
    selected = _context(case)
    monkeypatch.setattr(segments, "acquire_parameter_segment", lambda *_: pytest.fail("native acquisition"))
    try:
        work = _work(selected)
        definition, = work.definitions
        source = selected.source
        assert set(definition.sources) == {compact_identity(selected.descriptor), identity(case.manifest),
            case.inputs.specification.identity, coordinate_identity(source.coordinate), source.provenance.identity}
        assert definition.configuration == identity(selected.config)
        assert definition.streams == tuple(sorted((source.root.stream_identity(stream) for stream in source.root.streams),
            key=lambda row: row.object_id))
        assert work.scientific_unit_ids == (source.root.root.independent_group_id,)
        assert work.native_effect_slot_ids == ("prefix." + source.root_id,)
        assert work.rosters[0].subworks == (definition.identity,)
        assert tuple(row.output_id for row in definition.outputs) == ("arrays", "checkpoint")
        assert selected.config.source.identity == sr.identity(source)
        input_schemas = {row.logical.payload_schema for row in selected.bundle.manifests}
        assert sr.ScheduledSource.SCHEMA in input_schemas
        assert sr.ScheduledAllocation.SCHEMA not in input_schemas
        validate_prepared_native_invocation(case.plane, selected.bundle, work.definitions, visibility=VISIBILITY, access=ACCESS)
        assert all(port.bytes_read == 0 for port in selected.context.input_ports)
    finally:
        selected.bundle.close()


def test_existing_first_and_bound_preparation_preserve_exact_work_and_original_cursors(case):
    selected = _context(case)
    try:
        original = _work(selected)
        context, contract = _bound(selected)
        assert _work(selected, context=context) == original == contract.native_work
        assert contract.expected_parent_contact == selected.parent
        assert all(port.bytes_read == 0 for port in selected.context.input_ports)
    finally:
        selected.bundle.close()


@pytest.mark.parametrize("damage", ("run", "task", "attempt", "commit", "inputs", "dependencies", "plan", "task-identity"))
def test_bound_preparation_refuses_each_foreign_parent_field(case, damage):
    selected = _context(case)
    try:
        context, _ = _bound(selected)
        changes = {"run": dict(run_id="run.foreign"),
            "task": dict(task_id="task.foreign", execution_task=replace(selected.parent.execution_task, object_id="task.foreign")),
            "attempt": dict(attempt_id="attempt.foreign"), "commit": dict(implementation_commit="b" * 40),
            "inputs": dict(input_materialization_ids=("materialization.foreign",)),
            "dependencies": dict(dependency_receipt_ids=("receipt.foreign",)),
            "plan": dict(execution_plan=replace(selected.parent.execution_plan, object_fingerprint="c" * 64)),
            "task-identity": dict(execution_task=replace(selected.parent.execution_task, object_fingerprint="d" * 64))}
        with pytest.raises(ValueError, match="parent|plan or task"):
            _work(selected, context=context, parent=replace(selected.parent, **changes[damage]))
    finally:
        selected.bundle.close()


@pytest.mark.parametrize("damage", ("missing-descriptor", "coordinate", "provenance", "stream", "missing-stream", "undeclared-allocation", "duplicate-descriptor"))
def test_prefix_preparation_refuses_missing_nested_only_or_foreign_direct_operands(case, damage):
    selected = _context(case, damage=damage)
    try:
        with pytest.raises(ValueError, match="direct|undeclared|original source|duplicates"):
            _work(selected)
        assert all(port.bytes_read == 0 for port in selected.context.input_ports)
    finally:
        selected.bundle.close()


@pytest.mark.parametrize("damage", ("missing", "profile", "media", "unbound", "duplicate-logical"))
def test_prefix_preparation_refuses_changed_complete_output_contract_before_reads(case, damage):
    selected = _context(case)
    try:
        outputs = list(selected.context.output_ports)
        if damage == "missing":
            outputs.pop()
        else:
            change = {"profile": dict(profile=ArtifactProfile.RAW_SOURCE_BYTES),
                "media": dict(media_type="application/octet-stream"), "unbound": dict(logical_artifact_id=None),
                "duplicate-logical": dict(logical_artifact_id=outputs[1].logical_artifact_id)}[damage]
            outputs[0] = replace(outputs[0], **change)
        with pytest.raises(ValueError, match="ordinary output"):
            _work(selected, context=replace(selected.context, output_ports=tuple(outputs)))
        assert all(port.bytes_read == 0 for port in selected.context.input_ports)
    finally:
        selected.bundle.close()
