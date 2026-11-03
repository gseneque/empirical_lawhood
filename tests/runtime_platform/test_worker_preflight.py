# SPDX-License-Identifier: MPL-2.0
"""Exposed worker mechanics; no native science, signers or qualification."""

from dataclasses import replace
from hashlib import sha256
import os
from pathlib import Path

import pytest

from empirical_lawhood.adapters.composition.discovery import manifest
from empirical_lawhood.adapters.methods.native_subwork_conformance import ExposedNativeSubworkRunner
from empirical_lawhood.infrastructure.artifact_stream_primitives import (
    _anonymous_input_descriptor, _PreopenedBoundedReader, _seal_anonymous_input,
)
from empirical_lawhood.infrastructure.execution import (
    LocalProcessExecutor, TaskProcessError, WorkerPreflightError, prepare_worker_invocation,
)
from empirical_lawhood.infrastructure import execution as execution_owner
from empirical_lawhood.infrastructure.numerical_provenance import capture_numerical_provenance
from empirical_lawhood.infrastructure.prepared_native_invocation import NativeInputPublication, prepare_native_invocation
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.adjudication import ScientificAdjudicationContext
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityKind, CapabilityPermission, CapabilityRequirement
from empirical_lawhood.runtime.execution import DependencyReceiptBinding, RunnerResult, TaskContext, TaskOutputPayload, WorkerInputKind, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.native_subwork import NativeSubworkOutput, NativeSubworkRoster, NativeSubworkState
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec, ProtocolExecutionTask, ScientificInputRole, ScientificInputSpec, ScientificStage
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract, PreparedNativeWork
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
from tests.runtime_platform.test_native_subwork import ExposedInput, _plane, _store


ROOT = Path(__file__).resolve().parents[2]
BUDGET = ResourceBudget(1, None, 0, None, None, None)
ACCESS = OutcomeAccess.DEVELOPMENT_VISIBLE
VISIBILITY = VisibilityCeiling.DEVELOPMENT_ONLY


class ExposedReadRunner:
    """Disclosed fixture: echo original input bytes through ordinary transport."""

    def __init__(self, *, native=False, definitions=(), rosters=(), fail=None):
        self.manifest = manifest("preflight", ExposedInput, CapabilityKind.ANALYSIS,
            tuple(sorted((ExposedInput.SCHEMA, NumericalProducingProvenance.SCHEMA))),
            (ExposedInput.SCHEMA,), EvidenceCeiling.NON_PROMOTABLE, ACCESS, None,
            namespace="exposed-worker-conformance", resources=BUDGET,
            read_permission=CapabilityPermission.READ_DEVELOPMENT,
            implementation_id="exposed-conformance-only",
            conformance_ids=("actual-worker-mechanics-no-science",))
        self.selected_definitions = definitions
        self.selected_rosters = rosters
        self.fail = fail

    def preflight(self, context):
        for port in context.input_ports:
            if port.artifact_id == context.config.artifact_id:
                raw = port.read()
                decode_canonical_bytes(raw, ExposedInput, maximum_bytes=len(raw))

    def execute(self, context):
        raw = next(port for port in context.input_ports if port.artifact_id == context.config.artifact_id).read()
        return RunnerResult((TaskOutputPayload("echo", raw),), (ReceiptCheck("exposed-echo", True, ()),))


class ExposedNativeRunner(ExposedReadRunner):
    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        failure_point = None if self.fail == "after-completion" else self.fail
        result = ExposedNativeSubworkRunner(self.selected_definitions, (b"FALSIFIED",),
            failure_point, self.selected_definitions).execute_with_native_subwork(context, native_subwork, progress)
        if self.fail == "after-completion":
            raise RuntimeError("exposed refusal after completed child before ordinary parent return")
        return result


class ExposedPidRunner(ExposedReadRunner):
    def preflight(self, context):
        super().preflight(context)
        self.preflight_pid = os.getpid()

    def execute(self, context):
        record = ExposedInput("exposed.config", str(self.preflight_pid) + ":" + str(os.getpid()))
        return RunnerResult((TaskOutputPayload("echo", record.canonical_bytes()),), (ReceiptCheck("same-worker", True, ()),))


class ExposedGroupPidRunner(ExposedPidRunner):
    worker_chunk_limit = 2

    def execute(self, context):
        raw = next(port for port in context.input_ports if port.artifact_id == context.config.artifact_id).read()
        original = decode_canonical_bytes(raw, ExposedInput, maximum_bytes=len(raw))
        record = ExposedInput(original.selected_id,
            str(self.preflight_pid) + ":" + str(os.getpid()) + ":" + original.value)
        return RunnerResult((TaskOutputPayload("echo", record.canonical_bytes()),),
            (ReceiptCheck("same-worker-fresh-input", True, ()),))


def _native_work(*, runner, context, expected_parent):
    # Disclosed transport fixture, not a domain scientific projection. Reading
    # each independent cursor proves preparation leaves execution ports intact.
    for port in context.input_ports:
        port.read()
    return PreparedNativeWork(expected_parent, ("exposed.unit",), ("exposed.slot",),
        runner.selected_definitions, runner.selected_rosters)


def _original_task(runner, context, bundle, *, task_type=ExecutionTask):
    requirement = CapabilityRequirement(runner.manifest.capability_key, runner.manifest.capability_version,
        runner.manifest.kind, context.config, runner.manifest.input_schema_ids, runner.manifest.output_schema_ids,
        context.permissions, EvidenceCeiling.NON_PROMOTABLE, context.outcome_access, context.resource_budget)
    inputs = tuple(sorted((ExternalInputSpec("input." + row.artifact_id, row.artifact_id,
        row.logical.content_sha256, row.logical.payload_schema, row.logical.media_type,
        row.materialization.size_bytes, row.logical.visibility_ceiling, row.logical.outcome_access, None)
        for row in bundle.verified_inputs), key=lambda row: row.input_id))
    outputs = tuple(ArtifactOutputSpec(port.output_id, port.logical_artifact_id, port.output_id + ".json",
        port.payload_schema, port.profile, port.media_type, VISIBILITY, (), ACCESS) for port in context.output_ports)
    arguments = dict(task_id=context.task_id, stage=ScientificStage.DEVELOP, capability=requirement,
        capability_implementation_sha256=runner.manifest.implementation_sha256, dependency_task_ids=(),
        external_inputs=inputs, outputs=outputs, resource_lock_ids=(), barrier=BarrierKind.NONE,
        maximum_attempts=1, obligation_ids=("exposed.conformance",))
    if task_type is ExecutionTask:
        arguments["scientific_inputs"] = ()
    return task_type(**arguments)


def _case(tmp_path, *, actual=False, native=False, nested=True, fail=None, task_type=ExecutionTask,
        recorded_provenance=None):
    if recorded_provenance is not None:
        if not actual or not native or type(recorded_provenance) is not NumericalProducingProvenance:
            raise ValueError("recorded provenance requires an actual native fixture and its exact typed record")
        provenance = recorded_provenance
    elif actual:
        provenance = capture_numerical_provenance(project_root=ROOT)
    else:
        # Literal predicate/contract fixture, explicitly not producing evidence.
        sources = (("exposed-contract-fixture.py", sha256(b"fixture").hexdigest()),)
        provenance = NumericalProducingProvenance(
            '{"machine":"exposed","numpy":"exposed","python":"exposed","scipy":"exposed",'
            '"system":"exposed","threadpools":[]}\n', "1" * 64, sources,
            sha256(canonical_json_bytes(sources)).hexdigest(), "2" * 40, False)
    implementation = RecursiveImplementationBinding(provenance.package_sources, provenance.code_sources_sha256,
        provenance.dependency_lock_sha256, provenance.observed_git_head, provenance.observed_checkout_clean)
    plane = _plane(tmp_path / "custody")
    record = ExposedInput("exposed.config", "original exact bytes")
    publications = (NativeInputPublication(record.selected_id, record),)
    if native:
        publications += (NativeInputPublication(provenance.identity.object_id, provenance),)
    bundle = prepare_native_invocation(plane, publications=publications, visibility=VISIBILITY, access=ACCESS)
    runner = ExposedNativeRunner(fail=fail) if native and nested else ExposedReadRunner()
    config = CapabilityConfigRef(record.selected_id, record.SCHEMA, runner.manifest.config_schema_sha256,
        record.fingerprint(), record.selected_id)
    context = TaskContext("exposed.run", "exposed.task", "exposed.attempt", config,
        bundle.input_bindings, bundle.input_ports, (
            WorkerOutputPort("echo", record.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", "logical.echo"),),
        runner.manifest.permissions, ACCESS, BUDGET, WorkerIsolationProfile.TRUSTED_LOCAL)
    plan = ObjectIdentity("exposed.plan", "empirical-lawhood/runtime/development-execution-plan", "1.0.0", "3" * 64)
    task_record = _original_task(runner, context, bundle, task_type=task_type)
    task = ObjectIdentity.from_record(task_record.task_id, task_record)
    parent = NativeEffectContact(context.run_id, context.task_id, context.attempt_id, plan, task,
        provenance.observed_git_head, context.input_materialization_ids, context.dependency_receipt_ids)
    if native and nested:
        definition = bundle.definition(subwork_id="exposed.work", operation_id="exposed.no-solver",
            parent_contact=parent, configuration=ObjectIdentity.from_record(record.selected_id, record),
            sources=(), provenance=provenance, outputs=(NativeSubworkOutput("result.output.native",
                "empirical-lawhood/source/checksummed-uninterpreted-public-bytes", ArtifactProfile.RAW_SOURCE_BYTES,
                "text/plain"),))
        runner.selected_definitions = (definition,)
        runner.selected_rosters = (NativeSubworkRoster("selected.native-subwork", parent, (definition.identity,)),)
    contract = prepare_worker_invocation(runner, context, bundle.verified_inputs, implementation=implementation,
        execution_plan=plan, execution_task=task, execution_task_record=task_record, native_effect=native,
        native_work_preparer=_native_work if native else None)
    return plane, bundle, runner, context, contract, parent


@pytest.mark.parametrize("task_type", (ExecutionTask, ProtocolExecutionTask))
def test_contract_canonical_roundtrip_retains_original_task_without_input_storage_locators(tmp_path, task_type):
    _, bundle, _, context, contract, _ = _case(tmp_path, task_type=task_type)
    try:
        raw = contract.canonical_bytes()
        assert decode_canonical_bytes(raw, PreparedInvocationContract, maximum_bytes=len(raw)) == contract
        assert str(tmp_path).encode() not in raw
        assert b"_reader" not in raw
        assert contract.execution_task_record.__class__ is task_type
        for row in contract.inputs:
            assert b"relative_path" not in row.canonical_bytes()
        contract.require_complete()
        contract.validate_context(context)
        assert bundle.contract is None and bundle.complete is False
        with pytest.raises(ValueError, match="plan/task"):
            replace(contract, execution_plan=None).require_complete()
    finally:
        bundle.close()


@pytest.mark.parametrize("coordinate", ("config", "output", "permissions", "access", "resources",
    "capability-key", "capability-version", "implementation", "input-census"))
def test_original_task_projection_refuses_consistent_context_substitutions(tmp_path, coordinate):
    _, bundle, _, _, contract, _ = _case(tmp_path)
    try:
        if coordinate == "config":
            updates = {"config": replace(contract.config, content_sha256="8" * 64)}
        elif coordinate == "output":
            updates = {"output_ports": (replace(contract.output_ports[0], output_id="other"),)}
        elif coordinate == "permissions":
            updates = {"permissions": ()}
        elif coordinate == "access":
            updates = {"outcome_access": OutcomeAccess.OUTCOME_BLIND}
        elif coordinate == "resources":
            updates = {"resource_budget": replace(contract.resource_budget, source_scan_bytes=1)}
        elif coordinate == "input-census":
            updates = {"required_input_artifact_ids": ()}
        else:
            field = {"capability-key": "capability_key", "capability-version": "capability_version",
                "implementation": "implementation_sha256"}[coordinate]
            value = {"capability-key": "other.capability", "capability-version": "1.0.1",
                "implementation": "8" * 64}[coordinate]
            updates = {"manifest": replace(contract.manifest, **{field: value})}
        with pytest.raises(ValueError, match="original|complete task|unregistered capability"):
            replace(contract, **updates)
    finally:
        bundle.close()


@pytest.mark.parametrize("coordinate", ("missing-record", "task-fingerprint", "original-record"))
def test_complete_invocation_requires_the_exact_original_execution_task(tmp_path, coordinate):
    _, bundle, _, _, contract, _ = _case(tmp_path)
    try:
        if coordinate == "missing-record":
            with pytest.raises(ValueError, match="original task"):
                replace(contract, execution_task_record=None).require_complete()
        else:
            updates = {"execution_task": replace(contract.execution_task, object_fingerprint="8" * 64)}
            if coordinate == "original-record":
                updates = {"execution_task_record": replace(contract.execution_task_record, maximum_attempts=2)}
            with pytest.raises(ValueError, match="original execution task fingerprint"):
                replace(contract, **updates)
    finally:
        bundle.close()


@pytest.mark.parametrize("coordinate", ("content", "schema", "media", "size", "visibility", "access"))
def test_original_external_input_selection_is_checked_against_actual_transport(tmp_path, coordinate):
    _, bundle, _, _, contract, _ = _case(tmp_path)
    try:
        spec, = contract.execution_task_record.external_inputs
        field, value = {
            "content": ("expected_content_sha256", "8" * 64),
            "schema": ("expected_payload_schema", NumericalProducingProvenance.SCHEMA),
            "media": ("expected_media_type", "application/octet-stream"),
            "size": ("expected_size_bytes", spec.expected_size_bytes + 1),
            "visibility": ("expected_visibility_ceiling", VisibilityCeiling.OUTCOME_VISIBLE),
            "access": ("expected_outcome_access", OutcomeAccess.OUTCOME_BLIND),
        }[coordinate]
        original = replace(contract.execution_task_record, external_inputs=(replace(spec, **{field: value}),))
        with pytest.raises(ValueError, match="exact original external input"):
            replace(contract, execution_task_record=original,
                execution_task=ObjectIdentity.from_record(original.task_id, original))
    finally:
        bundle.close()


def test_external_fields_without_a_declared_exact_selection_are_not_invented(tmp_path):
    _, bundle, _, _, contract, _ = _case(tmp_path)
    try:
        spec, = contract.execution_task_record.external_inputs
        scoped = replace(spec, expected_content_sha256=None, identity_scope_sha256="8" * 64,
            expected_payload_schema=None, expected_media_type=None, expected_size_bytes=None,
            expected_visibility_ceiling=None, expected_outcome_access=None)
        original = replace(contract.execution_task_record, external_inputs=(scoped,))
        selected = replace(contract, execution_task_record=original,
            execution_task=ObjectIdentity.from_record(original.task_id, original))
        selected.require_complete()
    finally:
        bundle.close()


def _scientific_case(tmp_path):
    _, bundle, runner, context, contract, _ = _case(tmp_path, native=True, nested=False)
    bindings = tuple(replace(row, kind=WorkerInputKind.DEPENDENCY) for row in context.input_bindings)
    ports = tuple(replace(port, binding=binding) for port, binding in zip(context.input_ports, bindings, strict=True))
    receipts = tuple(DependencyReceiptBinding("receipt." + str(index), "producer." + str(index),
        (binding.materialization_id,)) for index, binding in enumerate(bindings))
    scientific = tuple(ScientificInputSpec("edge." + str(index), "operand." + str(index), ScientificInputRole.MODEL,
        receipts[index].task_id, "source.output", None, binding.artifact_id, binding.artifact_id,
        binding.payload_schema, binding.media_type, binding.size_bytes, binding.outcome_access,
        binding.visibility_ceiling, BarrierKind.NONE) for index, binding in enumerate(bindings))
    context = replace(context, input_bindings=bindings, input_ports=ports, dependency_receipts=receipts)
    original = replace(contract.execution_task_record, external_inputs=(),
        dependency_task_ids=tuple(row.task_id for row in receipts), scientific_inputs=scientific)
    selected = prepare_worker_invocation(runner, context, bundle.verified_inputs, implementation=contract.implementation,
        execution_plan=contract.execution_plan, execution_task=ObjectIdentity.from_record(original.task_id, original),
        execution_task_record=original)
    return bundle, context, selected


@pytest.mark.parametrize("coordinate", ("schema", "media", "size", "visibility", "access", "producer"))
def test_original_scientific_edge_contract_and_receipt_producer_are_preserved(tmp_path, coordinate):
    bundle, _, contract = _scientific_case(tmp_path)
    try:
        edge = contract.execution_task_record.scientific_inputs[0]
        field, value = {
            "schema": ("payload_schema", "empirical-lawhood/tests/other-scientific-schema"),
            "media": ("media_type", "application/octet-stream"),
            "size": ("maximum_size_bytes", edge.maximum_size_bytes - 1),
            "visibility": ("visibility_ceiling", VisibilityCeiling.OUTCOME_VISIBLE),
            "access": ("outcome_access", OutcomeAccess.OUTCOME_BLIND),
            "producer": ("producer_task_id", "producer.1"),
        }[coordinate]
        edges = (replace(edge, **{field: value}), *contract.execution_task_record.scientific_inputs[1:])
        # Producer substitution is a valid complete task with the same producer
        # census, by swapping the second edge as well. Its receipt association
        # remains wrong even though both task IDs and bytes are present.
        if coordinate == "producer":
            edges = (edges[0], replace(edges[1], producer_task_id="producer.0"))
        original = replace(contract.execution_task_record, scientific_inputs=edges)
        with pytest.raises(ValueError, match="scientific|producer"):
            replace(contract, execution_task_record=original,
                execution_task=ObjectIdentity.from_record(original.task_id, original))
    finally:
        bundle.close()


def test_receipt_census_is_retained_alongside_original_scientific_inputs(tmp_path):
    bundle, context, contract = _scientific_case(tmp_path)
    try:
        contract.require_complete()
        contract.validate_context(context)
        assert contract.dependency_receipts == context.dependency_receipts
        assert contract.expected_parent_contact.dependency_receipt_ids == ("receipt.0", "receipt.1")
        with pytest.raises(ValueError, match="dependency|producer receipt"):
            replace(contract, dependency_receipts=())
    finally:
        bundle.close()


def test_adjudication_denominator_and_lineage_context_is_retained_exactly(tmp_path):
    _, bundle, _, context, contract, _ = _case(tmp_path)
    try:
        identity = ObjectIdentity("exposed.relation", "empirical-lawhood/kernel/relation", "1.0.0", "8" * 64)
        cutoff = replace(identity, object_id="exposed.cutoff", object_schema="empirical-lawhood/kernel/information-cutoff")
        adjudication = ScientificAdjudicationContext(contract.execution_plan, "exposed.world",
            WorldKind.ANALYTIC_REFERENCE, identity, "exposed.unit", (cutoff,), VISIBILITY, ACCESS,
            "exposed.plumbing-only", True)
        selected = replace(contract, scientific_adjudication_context=adjudication)
        selected.validate_context(replace(context, scientific_adjudication_context=adjudication))
        with pytest.raises(ValueError, match="complete worker context"):
            selected.validate_context(replace(context,
                scientific_adjudication_context=replace(adjudication, independent_unit_id="other.unit")))
        with pytest.raises(ValueError, match="adjudication execution scope"):
            replace(selected, scientific_adjudication_context=replace(adjudication,
                execution_plan=replace(contract.execution_plan, object_fingerprint="9" * 64)))
    finally:
        bundle.close()


@pytest.mark.parametrize("coordinate", ("config", "output", "permissions", "attempt", "inputs"))
def test_exact_context_substitutions_refuse(tmp_path, coordinate):
    _, bundle, _, context, contract, _ = _case(tmp_path)
    try:
        if coordinate == "config":
            changed = replace(context, config=replace(context.config, content_sha256="8" * 64))
        elif coordinate == "output":
            changed = replace(context, output_ports=(replace(context.output_ports[0], output_id="other"),))
        elif coordinate == "permissions":
            changed = replace(context, permissions=())
        elif coordinate == "attempt":
            changed = replace(context, attempt_id="other.attempt")
        else:
            changed = replace(context, input_bindings=(), input_ports=())
        with pytest.raises(ValueError, match="complete worker context"):
            contract.validate_context(changed)
    finally:
        bundle.close()


def test_native_contract_retains_exact_roster_definition_and_parent(tmp_path):
    _, bundle, _, _, contract, _ = _case(tmp_path, native=True)
    try:
        raw = contract.canonical_bytes()
        assert decode_canonical_bytes(raw, PreparedInvocationContract, maximum_bytes=len(raw)) == contract
        with pytest.raises(ValueError, match="parent"):
            replace(contract, attempt_id="other.attempt")
        with pytest.raises(ValueError, match="roster"):
            replace(contract.native_work, definitions=())
    finally:
        bundle.close()


def _reparent_work(work, parent):
    definitions = tuple(replace(row, parent_contact=parent) for row in work.definitions)
    rosters = tuple(replace(row, parent_contact=parent, subworks=tuple(value.identity for value in definitions))
        for row in work.rosters)
    return replace(work, expected_parent=parent, definitions=definitions, rosters=rosters)


@pytest.mark.parametrize("coordinate", ("run", "task-fingerprint", "attempt", "plan", "commit", "inputs", "receipts"))
def test_native_work_requires_the_whole_anticipated_contact_not_a_partial_join(tmp_path, coordinate):
    _, bundle, _, _, contract, parent = _case(tmp_path, native=True)
    try:
        updates = {
            "run": {"run_id": "other.run"},
            "task-fingerprint": {"execution_task": replace(parent.execution_task, object_fingerprint="8" * 64)},
            "attempt": {"attempt_id": "other.attempt"},
            "plan": {"execution_plan": replace(parent.execution_plan, object_fingerprint="8" * 64)},
            "commit": {"implementation_commit": "8" * 40},
            "inputs": {"input_materialization_ids": ()},
            "receipts": {"dependency_receipt_ids": ("other.receipt",)},
        }[coordinate]
        work = _reparent_work(contract.native_work, replace(parent, **updates))
        with pytest.raises(ValueError, match="complete anticipated native parent"):
            replace(contract, native_work=work)
    finally:
        bundle.close()


@pytest.mark.parametrize("nested", (False, True))
def test_pure_native_projection_declares_ordinary_or_complete_initial_nested_scope(tmp_path, nested):
    _, bundle, _, context, contract, parent = _case(tmp_path, native=True, nested=nested)
    try:
        assert contract.native_preparation_error is None
        assert contract.native_work.expected_parent == parent
        assert contract.native_work.scientific_unit_ids == ("exposed.unit",)
        assert contract.native_work.native_effect_slot_ids == ("exposed.slot",)
        assert bool(contract.native_definitions) is nested
        assert bool(contract.native_rosters) is nested
        assert all(port.bytes_read == 0 for port in context.input_ports)
    finally:
        bundle.close()


@pytest.mark.parametrize("nested", (False, True))
def test_preparer_cannot_substitute_ordinary_and_nested_interfaces(tmp_path, nested):
    _, bundle, runner, context, contract, parent = _case(tmp_path, native=True, nested=nested)
    try:
        if nested:
            runner.selected_definitions = runner.selected_rosters = ()
        else:
            runner = ExposedNativeRunner()
        refused = prepare_worker_invocation(runner, context, bundle.verified_inputs,
            implementation=contract.implementation, execution_plan=contract.execution_plan,
            execution_task=contract.execution_task, execution_task_record=contract.execution_task_record,
            native_effect=True, native_work_preparer=_native_work)
        assert refused.native_work is None
        assert "ordinary versus initial nested" in refused.native_preparation_error
        assert parent == refused.expected_parent_contact
        assert all(port.bytes_read == 0 for port in context.input_ports)
    finally:
        bundle.close()


class _Acknowledgements:
    def __init__(self):
        self.sent = []

    def send(self, value):
        self.sent.append(value)


def _literal_readiness(contract):
    # This only probes parent dispatch with a disclosed literal contract fixture.
    # The actual-worker cases below capture unmocked source and environment.
    provenance = NumericalProducingProvenance(
        '{"machine":"exposed","numpy":"exposed","python":"exposed","scipy":"exposed",'
        '"system":"exposed","threadpools":[]}\n', contract.implementation.dependency_lock_sha256,
        contract.implementation.package_sources, contract.implementation.code_sources_sha256,
        contract.implementation.observed_git_head, contract.implementation.observed_checkout_clean)
    return execution_owner.WorkerPreflightResult(contract.identity, provenance, contract.environment, (), contract.native_work)


@pytest.mark.parametrize("coordinate", ("plan", "task-fingerprint", "commit", "inputs", "receipts"))
def test_parent_admission_refuses_any_changed_actual_contact_before_proceed(tmp_path, coordinate):
    _, bundle, _, context, contract, parent = _case(tmp_path, native=True, nested=False)
    connection = _Acknowledgements()
    calls = []
    updates = {
        "plan": {"execution_plan": replace(parent.execution_plan, object_fingerprint="8" * 64)},
        "task-fingerprint": {"execution_task": replace(parent.execution_task, object_fingerprint="8" * 64)},
        "commit": {"implementation_commit": "8" * 40},
        "inputs": {"input_materialization_ids": ()},
        "receipts": {"dependency_receipt_ids": ("other.receipt",)},
    }[coordinate]

    def enter():
        calls.append("entry")
        return replace(parent, **updates), None

    try:
        with pytest.raises(TaskProcessError, match="contact"):
            LocalProcessExecutor._admit_worker(_literal_readiness(contract), contract, connection,
                context, tmp_path, enter, None)
        assert calls == ["entry"] and connection.sent == []
    finally:
        bundle.close()


def test_parent_admission_requires_progress_only_for_initial_nested_work(tmp_path):
    _, bundle, _, context, contract, parent = _case(tmp_path, native=True)
    connection = _Acknowledgements()
    try:
        with pytest.raises(TaskProcessError, match="nested"):
            LocalProcessExecutor._admit_worker(_literal_readiness(contract), contract, connection,
                context, tmp_path, lambda: (parent, None), None)
        assert connection.sent == []
    finally:
        bundle.close()


def test_parent_admission_allows_explicit_ordinary_contact_without_nested_rosters(tmp_path):
    _, bundle, _, context, contract, parent = _case(tmp_path, native=True, nested=False)
    connection = _Acknowledgements()
    try:
        assert LocalProcessExecutor._admit_worker(_literal_readiness(contract), contract, connection,
            context, tmp_path, lambda: (parent, None), None) is None
        acknowledgement, = connection.sent
        assert acknowledgement.invocation == contract.identity and acknowledgement.proceed is True
    finally:
        bundle.close()


@pytest.mark.parametrize("path", ("ordinary", "deadline-free"))
def test_pure_contract_refuses_native_entry_before_worker_creation_or_contact(tmp_path, path):
    plane, bundle, runner, context, contract, parent = _case(tmp_path)
    calls = []
    executor = LocalProcessExecutor(scratch_root=plane.root)

    def forbidden_entry():
        calls.append("entry")
        return parent, None

    try:
        with pytest.raises(execution_owner.ResourceAdmissionError, match="pure prepared invocation cannot enter a native effect"):
            if path == "ordinary":
                executor.execute(runner, context, timeout_seconds=None,
                    prepared_contract=contract, native_entry=forbidden_entry)
            else:
                executor.execute_deadline_free(runner, context, progress_contract=None,
                    progress_callback=lambda value: pytest.fail("unexpected progress"),
                    prepared_contract=contract, native_entry=forbidden_entry)
        assert calls == []
        assert _store(plane, parent).parent_contacts.read(context.run_id, context.task_id) is None
        assert all(port.bytes_read == 0 for port in context.input_ports)
        assert not (tmp_path / "custody" / "scratch").exists()
    finally:
        bundle.close()


def test_sealed_cursors_read_independently_without_copy_or_shared_offset():
    descriptor = _anonymous_input_descriptor()
    os.write(descriptor, b"abcdef")
    os.lseek(descriptor, 0, os.SEEK_SET)
    _seal_anonymous_input(descriptor)
    reader = _PreopenedBoundedReader(descriptor, maximum_bytes=6)
    left, right = reader.cursor(), reader.cursor()
    try:
        assert left.read(2) == b"ab"
        assert right.read(3) == b"abc"
        assert reader.read(1) == b"a"
        assert left.read() == b"cdef" and right.read() == b"def"
        assert reader.read() == b"bcdef"
        assert os.lseek(descriptor, 0, os.SEEK_CUR) == 0
    finally:
        left.close()
        right.close()
        reader.close()


def test_mutable_descriptor_cannot_mint_preflight_cursor(tmp_path):
    path = tmp_path / "mutable"
    path.write_bytes(b"mutable")
    reader = _PreopenedBoundedReader(os.open(path, os.O_RDONLY), maximum_bytes=7)
    try:
        with pytest.raises(RuntimeError, match="kernel-sealed"):
            reader.cursor()
    finally:
        reader.close()


def test_actual_worker_stop_reports_source_environment_and_leaves_inputs_unconsumed(tmp_path):
    plane, bundle, runner, context, contract, parent = _case(tmp_path, actual=True)
    try:
        result = LocalProcessExecutor(scratch_root=plane.root).preflight(runner, context, prepared_contract=contract)
        assert result.ready and result.invocation == contract.identity
        assert result.environment == contract.environment
        assert result.producing_provenance.package_sources == contract.implementation.package_sources
        assert result.producing_provenance.runtime_observation_json != "exposed"
        assert _store(plane, parent).parent_contacts.read(context.run_id, context.task_id) is None
        assert context.input_ports[0].bytes_read == 0
        executed = LocalProcessExecutor(scratch_root=plane.root).execute(runner, context,
            timeout_seconds=None, prepared_contract=contract)
        assert executed.outputs[0].payload == ExposedInput("exposed.config", "original exact bytes").canonical_bytes()
    finally:
        bundle.close()


def test_actual_worker_reports_all_absent_direct_inputs_and_capability_before_contact(tmp_path):
    plane, bundle, runner, context, contract, parent = _case(tmp_path, actual=True, native=True)
    try:
        missing_specs = tuple(ExternalInputSpec("input." + name, name, None, None, None, None, None, None,
            "8" * 64) for name in ("missing.one", "missing.two"))
        original = replace(contract.execution_task_record, external_inputs=tuple(sorted(
            (*contract.execution_task_record.external_inputs, *missing_specs), key=lambda row: row.input_id)))
        missing = replace(contract, execution_task_record=original,
            execution_task=ObjectIdentity.from_record(original.task_id, original), native_work=None,
            required_input_artifact_ids=original.external_input_artifact_ids)
        missing = replace(missing, native_work=_reparent_work(contract.native_work, missing.expected_parent_contact))
        result = LocalProcessExecutor(scratch_root=plane.root).preflight(runner, context, prepared_contract=missing)
        assert not result.ready
        assert {row.operand_id for row in result.mismatches} == {"missing.one", "missing.two", "native.preparer"}
        assert _store(plane, parent).parent_contacts.read(context.run_id, context.task_id) is None
    finally:
        bundle.close()


@pytest.mark.parametrize("change", ("interpreter", "prefix", "implementation"))
def test_actual_worker_refuses_selected_drift_without_contact(tmp_path, change):
    plane, bundle, runner, context, contract, parent = _case(tmp_path, actual=True, native=True, nested=False)
    try:
        if change == "implementation":
            changed = replace(contract, implementation=replace(contract.implementation, dependency_lock_sha256="8" * 64))
        else:
            environment = replace(contract.environment, **({"interpreter_sha256": "8" * 64}
                if change == "interpreter" else {"prefix": "/exposed/wrong-prefix"}))
            changed = replace(contract, environment=environment)
        with pytest.raises(WorkerPreflightError) as refused:
            LocalProcessExecutor(scratch_root=plane.root).execute(runner, context,
                timeout_seconds=None, prepared_contract=changed, native_entry=lambda: pytest.fail("entered"),
                native_work_preparer=_native_work)
        assert not refused.value.result.ready
        assert _store(plane, parent).parent_contacts.read(context.run_id, context.task_id) is None
    finally:
        bundle.close()


@pytest.mark.parametrize("cut", ("before-contact", "after-durable-contact", "after-completion"))
def test_actual_worker_entry_and_completed_child_recovery_preserve_uncertainty(tmp_path, cut):
    plane, bundle, runner, context, contract, parent = _case(tmp_path, actual=True, native=True,
        fail="after-completion" if cut == "after-completion" else None)
    store = _store(plane, parent, bundle.manifests)
    calls = []

    def enter():
        # Closure deliberately remains parent-only; it is never pickled to child.
        calls.append(context.attempt_id)
        if cut == "before-contact":
            raise OSError("exposed refusal before contact")
        store.parent_contacts.begin(parent)
        if cut == "after-durable-contact":
            raise OSError("exposed lost acknowledgement after durable contact")
        return parent, store

    try:
        with pytest.raises((OSError, TaskProcessError)):
            LocalProcessExecutor(scratch_root=plane.root).execute(runner, context,
                timeout_seconds=None, prepared_contract=contract, native_entry=enter, native_work_preparer=_native_work)
        assert calls == [context.attempt_id]
        retained = store.parent_contacts.read(context.run_id, context.task_id)
        assert (retained is None) is (cut == "before-contact")
        if cut == "after-completion":
            recovered = store.recover(contract.native_definitions[0])
            assert recovered.state is NativeSubworkState.COMPLETED
            assert b"".join(store.iter_completed_output(contract.native_definitions[0], "result.output.native")) == b"FALSIFIED"
            assert retained == parent  # No ordinary parent completion was manufactured.
    finally:
        store.parent_contacts.retire_live_creator(parent)
        bundle.close()


@pytest.mark.parametrize("nested", (False, True))
def test_actual_worker_native_ready_then_stop_never_contacts_or_consumes_execution_inputs(tmp_path, nested):
    plane, bundle, runner, context, contract, parent = _case(tmp_path, actual=True, native=True, nested=nested)
    try:
        result = LocalProcessExecutor(scratch_root=plane.root).preflight(runner, context,
            prepared_contract=contract, native_work_preparer=_native_work)
        assert result.ready and result.native_work == contract.native_work
        assert result.environment == contract.environment
        assert result.producing_provenance.package_sources == contract.implementation.package_sources
        assert _store(plane, parent).parent_contacts.read(context.run_id, context.task_id) is None
        assert all(port.bytes_read == 0 for port in context.input_ports)
    finally:
        bundle.close()


def test_actual_worker_ready_and_proceed_execute_in_the_same_process_after_ordinary_contact(tmp_path):
    plane, bundle, _, context, contract, parent = _case(tmp_path, actual=True, native=True, nested=False)
    runner = ExposedPidRunner()
    store = _store(plane, parent)
    calls = []

    def enter():
        calls.append(os.getpid())
        store.parent_contacts.begin(parent)
        return parent, None

    try:
        executed = LocalProcessExecutor(scratch_root=plane.root).execute(runner, context,
            timeout_seconds=None, prepared_contract=contract, native_entry=enter, native_work_preparer=_native_work)
        raw = executed.outputs[0].payload
        record = decode_canonical_bytes(raw, ExposedInput, maximum_bytes=len(raw))
        ready_pid, execute_pid = map(int, record.value.split(":"))
        assert ready_pid == execute_pid and execute_pid != os.getpid()
        assert calls == [os.getpid()]
        assert store.parent_contacts.read(context.run_id, context.task_id) == parent
        assert not hasattr(runner, "preflight_pid")
        assert all(port.bytes_read == 0 for port in context.input_ports)
    finally:
        store.parent_contacts.retire_live_creator(parent)
        bundle.close()


def test_actual_worker_deadline_free_ready_and_proceed_share_process_after_exact_ordinary_contact(tmp_path):
    plane, bundle, _, context, contract, parent = _case(tmp_path, actual=True, native=True, nested=False)
    runner = ExposedPidRunner()
    store = _store(plane, parent)
    calls = []

    def enter():
        calls.append(os.getpid())
        store.parent_contacts.begin(parent)
        return parent, None

    try:
        result = LocalProcessExecutor(scratch_root=plane.root).execute_deadline_free(runner, context,
            progress_contract=None, progress_callback=lambda value: pytest.fail("unexpected progress"),
            prepared_contract=contract, native_work_preparer=_native_work, native_entry=enter)
        raw = result.outputs[0].payload
        record = decode_canonical_bytes(raw, ExposedInput, maximum_bytes=len(raw))
        ready_pid, execute_pid = map(int, record.value.split(":"))
        assert ready_pid == execute_pid and execute_pid != os.getpid()
        assert calls == [os.getpid()]
        assert store.parent_contacts.read(context.run_id, context.task_id) == parent
        assert all(port.bytes_read == 0 for port in context.input_ports)
    finally:
        store.parent_contacts.retire_live_creator(parent)
        bundle.close()


def _second_attempt(context, contract):
    context = replace(context, attempt_id="exposed.attempt.second")
    contract = replace(contract, invocation_id="prepared." + context.attempt_id, attempt_id=context.attempt_id)
    return context, contract


def test_actual_worker_group_reuses_process_with_fresh_readiness_and_original_inputs_per_attempt(tmp_path):
    plane, bundle, _, context, contract, parent = _case(tmp_path, actual=True)
    executor = LocalProcessExecutor(scratch_root=plane.root)
    runner = ExposedGroupPidRunner()
    try:
        records = []
        for selected_context, selected_contract in ((context, contract), _second_attempt(context, contract)):
            result = executor.execute_deadline_free_in_group(runner, selected_context,
                execution_group_id="exposed.two-task-group", progress_contract=None,
                progress_callback=lambda value: pytest.fail("unexpected progress"),
                prepared_contract=selected_contract)
            raw = result.outputs[0].payload
            records.append(decode_canonical_bytes(raw, ExposedInput, maximum_bytes=len(raw)))
        first_ready, first_execute, first_value = records[0].value.split(":", 2)
        second_ready, second_execute, second_value = records[1].value.split(":", 2)
        assert first_ready == first_execute == second_ready == second_execute
        assert int(first_execute) != os.getpid()
        assert first_value == second_value == "original exact bytes"
        assert _store(plane, parent).parent_contacts.read(context.run_id, context.task_id) is None
        assert all(port.bytes_read == 0 for port in context.input_ports)
    finally:
        executor.close_run_workers()
        bundle.close()


def test_actual_worker_reused_group_reauthenticates_changed_sealed_bytes_on_second_attempt(tmp_path):
    plane, bundle, _, context, contract, parent = _case(tmp_path, actual=True)
    executor = LocalProcessExecutor(scratch_root=plane.root)
    runner = ExposedGroupPidRunner()
    substituted = None
    try:
        first = executor.execute_deadline_free_in_group(runner, context,
            execution_group_id="exposed.integrity-group", progress_contract=None,
            progress_callback=lambda value: pytest.fail("unexpected progress"), prepared_contract=contract)
        assert first.outputs[0].payload
        context, contract = _second_attempt(context, contract)
        context, substituted = _changed_sealed_context(context)
        with pytest.raises(WorkerPreflightError) as refused:
            executor.execute_deadline_free_in_group(runner, context,
                execution_group_id="exposed.integrity-group", progress_contract=None,
                progress_callback=lambda value: pytest.fail("unexpected progress"), prepared_contract=contract)
        assert context.config.artifact_id in {row.operand_id for row in refused.value.result.mismatches}
        assert not refused.value.result.ready
        assert _store(plane, parent).parent_contacts.read(context.run_id, context.task_id) is None
        assert all(port.bytes_read == 0 for port in context.input_ports)
        scratch = tmp_path / "custody" / "scratch" / "task-execution" / context.run_id / context.attempt_id
        assert not any(path.is_file() for path in scratch.rglob("*"))
    finally:
        executor.close_run_workers()
        if substituted is not None:
            substituted.close()
        bundle.close()


def _changed_sealed_context(context):
    raw = ExposedInput("exposed.config", "modified exact bytes").canonical_bytes()
    original, = context.input_ports
    assert len(raw) == original.binding.size_bytes
    descriptor = _anonymous_input_descriptor()
    os.write(descriptor, raw)
    _seal_anonymous_input(descriptor)
    reader = _PreopenedBoundedReader(descriptor, maximum_bytes=len(raw))
    substituted = replace(original, _reader=reader)
    return replace(context, input_ports=(substituted,)), substituted


@pytest.mark.parametrize("path", ("deadline-free", "grouped"))
@pytest.mark.parametrize("drift", ("context", "implementation", "sealed-bytes"))
def test_actual_worker_additional_paths_refuse_context_source_or_real_byte_substitution_before_output(tmp_path, path, drift):
    plane, bundle, _, context, contract, parent = _case(tmp_path, actual=True)
    executor = LocalProcessExecutor(scratch_root=plane.root)
    runner = ExposedGroupPidRunner()
    substituted = None
    if drift == "context":
        context = replace(context, attempt_id="substituted.attempt")
        expected_operand = contract.task_id
    elif drift == "implementation":
        contract = replace(contract, implementation=replace(contract.implementation, dependency_lock_sha256="8" * 64))
        expected_operand = "worker.implementation"
    else:
        context, substituted = _changed_sealed_context(context)
        expected_operand = context.config.artifact_id
    try:
        with pytest.raises(WorkerPreflightError) as refused:
            if path == "deadline-free":
                executor.execute_deadline_free(runner, context, progress_contract=None,
                    progress_callback=lambda value: pytest.fail("unexpected progress"), prepared_contract=contract)
            else:
                executor.execute_deadline_free_in_group(runner, context,
                    execution_group_id="exposed.refused-group", progress_contract=None,
                    progress_callback=lambda value: pytest.fail("unexpected progress"), prepared_contract=contract)
        assert not refused.value.result.ready
        assert expected_operand in {row.operand_id for row in refused.value.result.mismatches}
        assert _store(plane, parent).parent_contacts.read(context.run_id, context.task_id) is None
        assert all(port.bytes_read == 0 for port in context.input_ports)
        scratch = tmp_path / "custody" / "scratch" / "task-execution" / context.run_id / context.attempt_id
        assert not any(selected.is_file() for selected in scratch.rglob("*"))
    finally:
        executor.close_run_workers()
        if substituted is not None:
            substituted.close()
        bundle.close()
