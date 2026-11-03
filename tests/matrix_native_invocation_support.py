# SPDX-License-Identifier: MPL-2.0
"""Exact prepared contracts for disclosed Matrix software-control fixtures.

The implementation binding comes from that fixture's own numerical provenance.
It is not installed-source qualification, a grant or an invocation from another
case. Existing typed tasks and dependency joins are retained when supplied.
"""

from dataclasses import replace

from empirical_lawhood.infrastructure.execution import prepare_worker_invocation
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.kernel.evidence import EvidenceCeiling
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
from empirical_lawhood.runtime.execution import TaskContext, VerifiedArtifactInput, WorkerInputKind, WorkerIsolationProfile
from empirical_lawhood.runtime.plans import (
    ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec, ScientificStage,
)
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding


def typed_native_context(context, *, runner, manifests, run_id=None, attempt_id=None):
    """Convert this fixture's complete live ports into the ordinary context."""
    if type(context) is TaskContext:
        return context
    selected = tuple(sorted(context.input_ports, key=lambda row: row.artifact_id))
    by_id = {row.logical.logical_artifact_id: row for row in manifests}
    if (set(by_id) != {row.artifact_id for row in selected}
            or any(by_id[row.artifact_id].materialization.materialization_id != row.materialization_id
                for row in selected)):
        raise ValueError("literal native context substitutes its actual input ports or manifests")
    configurations = tuple(row for row in manifests
        if row.logical.payload_schema == runner.manifest.config_schema
        and row.logical.content_sha256 == context.config.content_sha256)
    if len(configurations) != 1:
        raise ValueError("literal native context requires its exact selected configuration bytes")
    config, = configurations
    reference = CapabilityConfigRef(config.logical.logical_artifact_id, config.logical.payload_schema,
        runner.manifest.config_schema_sha256, config.logical.content_sha256, config.logical.logical_artifact_id)
    selected_run = getattr(context, "run_id", run_id)
    selected_attempt = getattr(context, "attempt_id", attempt_id)
    if selected_run is None or selected_attempt is None:
        raise ValueError("literal native context requires its explicit original run and attempt")
    outputs = tuple(sorted((replace(row, logical_artifact_id=row.logical_artifact_id or row.output_id)
        for row in context.output_ports), key=lambda row: row.output_id))
    return TaskContext(selected_run, context.task_id, selected_attempt, reference,
        tuple(row.binding for row in selected), selected, outputs, context.permissions,
        context.outcome_access, context.resource_budget, WorkerIsolationProfile.TRUSTED_LOCAL,
        tuple(getattr(context, "dependency_receipts", ())))


def literal_native_task(runner, context, manifests, *, visibility, scientific_inputs=()):
    """Declare exact current fixture operands; scientific edges are explicit."""
    dependencies = {row.artifact_id: row for row in context.input_bindings if row.kind is WorkerInputKind.DEPENDENCY}
    edges = {row.operational_logical_artifact_id: row for row in scientific_inputs}
    if set(edges) != set(dependencies):
        raise ValueError("dependency-bearing native fixture requires its complete explicit scientific edges")
    for artifact_id, binding in dependencies.items():
        receipts = tuple(row for row in context.dependency_receipts
            if binding.materialization_id in row.output_materialization_ids)
        if len(receipts) != 1 or receipts[0].task_id != edges[artifact_id].producer_task_id:
            raise ValueError("native fixture scientific edge changes its exact original producing receipt")
    manifest = runner.manifest
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind,
        context.config, manifest.input_schema_ids, manifest.output_schema_ids, context.permissions,
        EvidenceCeiling.NON_PROMOTABLE, context.outcome_access, context.resource_budget)
    inputs = tuple(sorted((ExternalInputSpec("fixture.input." + row.logical.logical_artifact_id,
        row.logical.logical_artifact_id, row.logical.content_sha256, row.logical.payload_schema,
        row.logical.media_type, row.materialization.size_bytes, row.logical.visibility_ceiling,
        row.logical.outcome_access, None) for row in manifests
        if row.logical.logical_artifact_id not in dependencies), key=lambda row: row.input_id))
    outputs = tuple(ArtifactOutputSpec(row.output_id, row.logical_artifact_id, "outputs/" + row.output_id,
        row.payload_schema, row.profile, row.media_type, visibility, (), context.outcome_access)
        for row in context.output_ports)
    return ExecutionTask(context.task_id, ScientificStage.DEVELOP, requirement, manifest.implementation_sha256,
        tuple(sorted({row.producer_task_id for row in scientific_inputs})), inputs, outputs, (), BarrierKind.NONE,
        1, ("disclosed.matrix-software-control",), scientific_inputs=tuple(sorted(scientific_inputs,key=lambda row: row.edge_id)))


def prepared_native_store(plane, *, runner, context, manifests, provenance, execution_plan,
                          native_work_preparer, run_id=None, attempt_id=None, task_record=None,
                          visibility, access):
    """Prepare this exact scientific-control case before publishing its parent."""
    if type(provenance) is not NumericalProducingProvenance:
        raise TypeError("native fixture requires its own exact numerical provenance")
    selected = typed_native_context(context, runner=runner, manifests=manifests,
        run_id=run_id, attempt_id=attempt_id)
    if task_record is None:
        task_record = literal_native_task(runner, selected, manifests, visibility=visibility)
    if task_record.task_id != selected.task_id:
        raise ValueError("native fixture changes its selected original task")
    implementation = RecursiveImplementationBinding(provenance.package_sources, provenance.code_sources_sha256,
        provenance.dependency_lock_sha256, provenance.observed_git_head, provenance.observed_checkout_clean)
    plane.verify_manifests(tuple(manifests))
    verified = tuple(VerifiedArtifactInput(row.logical, row.materialization) for row in manifests)
    contract = prepare_worker_invocation(runner, selected, verified, implementation=implementation,
        execution_plan=execution_plan, execution_task=ObjectIdentity.from_record(task_record.task_id, task_record),
        execution_task_record=task_record, native_effect=True, native_work_preparer=native_work_preparer)
    contract.require_complete()
    if contract.native_preparation_error is not None or contract.native_work is None:
        raise ValueError("literal native fixture preparation refused: " + str(contract.native_preparation_error))
    parent = contract.expected_parent_contact
    contacts = ExternalNativeEffectContactStore(plane=plane, execution_plan=execution_plan,
        visibility_ceiling=visibility, outcome_access=access)
    store = ExternalNativeSubworkStore(plane=plane, parent_contacts=contacts, parent_contact=parent,
        parent_inputs=tuple(manifests), prepared_invocation=contract)
    contacts.begin(parent)
    return store, replace(selected, prepared_invocation=contract), contract
