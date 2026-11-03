# SPDX-License-Identifier: MPL-2.0
"""Actual PURE producer bodies in memory; prepared tokens are disclosed controls.

No synthetic context authenticates original acquisition, issues a study or runs
a native child. Separate actual-parent refusal controls protect that boundary.
"""

from dataclasses import replace
from hashlib import sha256

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_method_bindings as owner, selected_e4_revision_preparation as public
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.artifacts import ArtifactGenericValidation, ArtifactProfile, LogicalArtifactIdentity
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
from empirical_lawhood.runtime.execution import DependencyReceiptBinding, TaskContext, WorkerInputBinding, WorkerInputKind, WorkerInputPort, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec, ScientificInputRole, ScientificInputSpec
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract, PreparedNativeInputContract, PreparedWorkerEnvironment
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
from tests.test_matrix_selected_protected_worker import MemoryReader
from tests.test_matrix_selected_e4_methods import selected_revision, selected_e4_populations, selected_bridge, transfer, pin  # noqa: F401
from tests.test_matrix_selected_e4_public import campaign_fixture
from empirical_lawhood.kernel.authority import ResourceBudget

def invocation(config, values, producers):
    declaration = next(row for row in owner.operation_declarations() if row.capability_key == owner.NAMESPACE + "." + config.operation)
    manifest, task_id = declaration.manifest(), config.config_id.removeprefix("config.")
    ports, contracts, external, edges, receipts = [], [], [], [], {}
    for name, value in sorted({"automatic": config, **values}.items()):
        raw = value if type(value) is bytes else value.canonical_bytes()
        arrays = type(value) is bytes
        schema, media, profile = (MATRIX_ARRAY_SCHEMA, "application/x-npz", ArtifactProfile.MATRIX_ARRAY_NPZ) if arrays else (value.SCHEMA, "application/json", ArtifactProfile.CANONICAL_JSON)
        digest = sha256(raw).hexdigest()
        producer = producers.get(name)
        logical = LogicalArtifactIdentity("artifact." + name, digest, schema, profile, media, Visibility.DEVELOPMENT_ONLY, (), Access.DEVELOPMENT_VISIBLE,
            ArtifactGenericValidation("validator.disclosed-e4-control", "1.0.0", "1" * 64, schema, profile))
        binding = WorkerInputBinding(logical.logical_artifact_id, "material." + name, schema, media, len(raw), Visibility.DEVELOPMENT_ONLY,
            Access.DEVELOPMENT_VISIBLE, WorkerInputKind.DEPENDENCY if producer else WorkerInputKind.EXTERNAL)
        ports.append(WorkerInputPort(binding, MemoryReader(raw)))
        contracts.append(PreparedNativeInputContract(logical, binding, digest))
        output = None if producer is None else producer + (".arrays" if arrays else ".product")
        if producer:
            receipts.setdefault(producer, []).append(binding.materialization_id)
        else:
            external.append(ExternalInputSpec("external." + name, logical.logical_artifact_id, digest, schema, media,
                len(raw), Visibility.DEVELOPMENT_ONLY, Access.DEVELOPMENT_VISIBLE, None))
        if name != "automatic":
            edges.append(ScientificInputSpec("edge." + name, name, ScientificInputRole.HISTORY if producer else ScientificInputRole.SOURCE,
                producer, output, None if producer else "external." + name, "scientific." + name, logical.logical_artifact_id,
                schema, media, len(raw), Access.DEVELOPMENT_VISIBLE, Visibility.DEVELOPMENT_ONLY, BarrierKind.NONE))
    dependencies = tuple(DependencyReceiptBinding("receipt." + task, task, tuple(sorted(materials))) for task, materials in sorted(receipts.items()))
    config_ref = CapabilityConfigRef(config.config_id, config.SCHEMA, manifest.config_schema_sha256, config.fingerprint(), "artifact.automatic")
    outputs = tuple(WorkerOutputPort(task_id + "." + row.output_id, row.payload_schema, row.profile, row.media_type,
        "output.disclosed-e4-control." + row.output_id) for row in declaration.outputs)
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind, config_ref,
        manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions, EvidenceCeiling.NON_PROMOTABLE, Access.DEVELOPMENT_VISIBLE, config.operational_budget)
    task = ExecutionTask(task_id, declaration.stage, requirement, manifest.implementation_sha256, tuple(sorted(receipts)), tuple(external),
        tuple(ArtifactOutputSpec(output.output_id, output.logical_artifact_id, "unpublished/" + output.output_id + ".json", output.payload_schema, output.profile,
            output.media_type, Visibility.DEVELOPMENT_ONLY, (Visibility.DEVELOPMENT_ONLY,), Access.DEVELOPMENT_VISIBLE) for output in outputs),
        (), declaration.execution_properties.barrier, 1, ("obligation.disclosed-e4-control",), scientific_inputs=tuple(edges))
    plan = ObjectIdentity("plan.disclosed-e4-control", "empirical-lawhood/runtime/execution-plan", "1.0.0", "a" * 64)
    packages = (("synthetic/control.py", "1" * 64),)
    implementation = RecursiveImplementationBinding(packages, sha256(canonical_json_bytes(packages)).hexdigest(), "2" * 64, "3" * 40, False)
    context = TaskContext("run.disclosed-e4-control", task_id, "attempt.disclosed-e4-control", config_ref, tuple(row.binding for row in ports), tuple(ports),
        outputs, manifest.permissions, Access.DEVELOPMENT_VISIBLE, config.operational_budget, WorkerIsolationProfile.TRUSTED_LOCAL, dependencies)
    prepared = PreparedInvocationContract("prepared.disclosed-e4-control", manifest, implementation,
        PreparedWorkerEnvironment("/synthetic/python", "4" * 64, "/synthetic", ()), context.run_id, task_id, context.attempt_id,
        config_ref, tuple(contracts), outputs, manifest.permissions, Access.DEVELOPMENT_VISIBLE, config.operational_budget,
        WorkerIsolationProfile.TRUSTED_LOCAL, dependencies, execution_plan=plan, execution_task=ObjectIdentity.from_record(task_id, task),
        execution_task_record=task, required_input_artifact_ids=tuple(row.artifact_id for row in ports))
    context = replace(context, prepared_invocation=prepared)
    runner = owner.SelectedE4MethodWorker(config.operation, manifest=manifest).with_prepared_scope((context.run_id, task_id, context.input_materialization_ids, plan))
    return runner, context



def fitting_invocation(f):
    acquisition = owner.SelectedE4DevelopmentAcquisition("acquisition.disclosed-worker", "original/unpublished", "run.unpublished",
        pin("plan.disclosed", "empirical-lawhood/runtime/development-execution-plan"),
        pin("receipt.disclosed", "empirical-lawhood/runtime/canonical-task-receipt"), False)
    resources = owner.SelectedE4MethodResources("resources.disclosed-worker", tuple(
        (phase, ResourceBudget(1, 1024**3, 0, None, None, None)) for phase in ("revision-fit", "revision-freeze")))
    inputs = public.SelectedE4RevisionInputs(campaign_fixture()[0].campaign, f.programme, f.bank, acquisition, f.reduction, f.data, resources)
    draft, _ = public.lower_development(f.editable, inputs)
    declaration = next(row for row in owner.operation_declarations() if row.capability_key.endswith(".revision-fit"))
    operation = next(row for row in draft.operations if row.selection.capability_key == declaration.capability_key)
    from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input
    config = decode_recursive_config_input(operation, declaration.registration()).record
    return invocation(config, {"programme": f.programme, "bank": f.bank, "acquisition": acquisition,
        "specification": f.specification, "reduction": f.reduction, "data": f.data}, {})


def test_actual_fitting_worker_body_matches_original_source_math_and_exact_output(selected_revision):  # noqa: F811
    runner, context = fitting_invocation(selected_revision)
    result = runner.execute(context)
    output, = result.outputs
    assert output.output_id == context.task_id + ".product"
    nomination = decode_canonical_bytes(output.payload, owner.science.SelectedE4RevisionNomination, maximum_bytes=None)
    expected = owner.science.select_revision(selected_revision.specification, selected_revision.programme, selected_revision.bank,
        selected_revision.reduction, selected_revision.data, nomination_id="product." + context.task_id)
    assert nomination == expected
    assert nomination.endpoint_fit_calls == 300


def test_actual_fitting_worker_refuses_missing_parent_admission_even_for_complete_observations(selected_revision):  # noqa: F811
    runner, context = fitting_invocation(selected_revision)
    with pytest.raises(PermissionError, match="parent custody"):
        runner.with_prepared_scope(None).execute(context)


def test_actual_fitting_worker_rejects_tampered_custody_bound_input_bytes(selected_revision):  # noqa: F811
    runner, context = fitting_invocation(selected_revision)
    port = next(value for value in context.input_ports if value.payload_schema == selected_revision.data.SCHEMA)
    replacement = WorkerInputPort(port.binding, MemoryReader(selected_revision.data.canonical_bytes().replace(
        b'"FINITE"', b'"FAKED!"', 1)))
    altered = replace(context, input_ports=tuple(replacement if value is port else value for value in context.input_ports))
    with pytest.raises(ValueError, match="custody-bound"):
        runner.execute(altered)
