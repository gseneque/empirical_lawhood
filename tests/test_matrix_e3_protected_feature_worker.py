# SPDX-License-Identifier: MPL-2.0
"""Disclosed seedless worker contexts and guarded dataset ports, no issue.

Current prefix metadata and negative literal paths are software fixtures.
These tests create neither native contact nor source/numerical qualification.
"""

from collections import defaultdict
from dataclasses import fields, replace
from hashlib import sha256
import json
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import protected_feature_bindings as owner
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_experiment_inputs import project_protected_e3_allocation
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_experiment_methods import ProtectedE3CausalFeature
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_feature_science import project_protected_e3_feature
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_source_records import identity, source_task_id
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity as scheduled_identity
from empirical_lawhood.infrastructure.execution import prepare_worker_invocation
from empirical_lawhood.infrastructure.prepared_native_invocation import NativeInputPublication, prepare_native_invocation
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
from empirical_lawhood.runtime.execution import DependencyReceiptBinding, TaskContext, WorkerInputKind, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec, ScientificInputRole, ScientificInputSpec, ScientificStage
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
from tests.worker_configuration_support import freeze_worker_configuration
from tests.test_matrix_e3_protected_prefix_workers import _manifest, case as case, original_case as original_case  # noqa: F401
from tests.test_matrix_e3_protected_prefix_science import blocked, forbid_native as forbid_native  # noqa: F401
from tests.test_matrix_factor_confirmation_eligibility import _matrix_plane


def prepared_feature(case, directory, *, damage=None, qualified_outputs=True):
    plane = _matrix_plane(directory / "guarded-feature")
    declaration, runner = owner.feature_declaration(), owner.feature_declaration().runner_factory()
    manifest = declaration.manifest()
    public = ScheduledPublicSource.from_source(case.source)
    source_inputs = replace(case.originals.inputs, reservation=case.manifest.reservation, native_specification=case.manifest.native_specification)
    allocation = project_protected_e3_allocation(source_inputs)
    public_identity = ObjectIdentity.from_record("public.literal." + case.source.root_id, public)
    design = case.source.numerical_design
    config = owner.ProtectedE3FeatureConfig("config." + owner.feature_task_id(public.root.root_id),
        case.specification.identity, allocation.identity, public_identity, scheduled_identity(design), public.root)
    records = {"specification": case.specification, "public-source": public, "numerical-design": design,
        "numerical": case.numerical, "witness": case.witness, "assessment": case.assessment, "causal": case.causal}
    if damage == "profile":
        records["numerical-design"] = replace(design, trajectory_tolerance=design.trajectory_tolerance + 1)
    elif damage == "public-reference":
        config = replace(config, public_source=replace(config.public_source, object_fingerprint="e" * 64))
    elif damage in ("numerical-tolerance", "numerical-denominator"):
        numerical = case.numerical
        if damage == "numerical-tolerance":
            control = numerical.controls[0]
            tolerance = control.tolerance + 1
            failed = tuple(index+1 for index, error in enumerate(control.measured_errors) if error > tolerance)
            control = replace(control, tolerance=tolerance, failed_steps=failed, disposition="VIOLATED" if failed else "SATISFIED")
            controls = (control, *numerical.controls[1:])
        else:
            controls = tuple(replace(control, denominator_steps=control.denominator_steps+ (2 if index == 1 else 1),
                measured_errors=(*control.measured_errors, *((type(control.error)(0),) * (2 if index == 1 else 1))))
                for index, control in enumerate(numerical.controls))
        numerical = replace(numerical, controls=controls, numerical_pass=all(c.disposition == "SATISFIED" for c in controls))
        witness = replace(case.witness, numerical=identity(numerical), arrays=replace(case.witness.arrays,
            producers=tuple(sorted((case.witness.source, case.witness.history, identity(numerical)), key=lambda row: row.object_id))))
        assessment = replace(case.assessment, witness=identity(witness))
        causal = replace(case.causal, numerical=identity(numerical), witness=identity(witness), frame_assessment=identity(assessment),
            arrays=replace(case.causal.arrays, producers=tuple(sorted((case.causal.source, case.causal.history,
                identity(witness), identity(assessment)), key=lambda row: row.object_id))))
        records.update(numerical=numerical, witness=witness, assessment=assessment, causal=causal)
    task_id, current_alias = owner.feature_task_id(public.root.root_id), config.record_id
    aliases = {name: "transport.feature." + name + ".record" for name, _, _ in owner.FEATURE_RECORD_INPUTS}
    publications = [NativeInputPublication(config.record_id, config, current_alias)]
    for name, _, _ in owner.FEATURE_RECORD_INPUTS:
        record = records[name]
        object_id = public_identity.object_id if name == "public-source" else scheduled_identity(record).object_id
        publications.append(NativeInputPublication(object_id, record, aliases[name]))
    existing, raw_aliases = [], {}
    for name, _ in owner.FEATURE_ARRAY_INPUTS:
        raw = case.causal_raw if name == "causal-arrays" else case.diagnostic_raw
        original = case.causal.arrays if name == "causal-arrays" else case.witness.arrays
        alias = original.array_artifact.artifact_id
        if damage == "array-alias" and name == "causal-arrays":
            alias = "ordinary.feature.foreign-causal-array"
        result = plane.write(ArtifactWriteRequest(alias, "arrays/" + name + ".npz", MATRIX_ARRAY_SCHEMA,
            ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", "literal-feature-arrays", "arrays", raw,
            Visibility.PROSPECTIVE, (), Access.OUTCOME_BLIND))
        existing.append((ObjectIdentity(alias, MATRIX_ARRAY_SCHEMA, "1.0.0", sha256(raw).hexdigest()), _manifest(plane, result)))
        raw_aliases[name] = alias
    bundle = prepare_native_invocation(plane, publications=publications, existing_inputs=existing,
        relative_root="feature-inputs", visibility=Visibility.PROSPECTIVE, access=Access.OUTCOME_BLIND)
    by_id = {row.artifact_id: row for row in bundle.verified_inputs}
    producers = {aliases[name]: producer for name, _, producer in owner.FEATURE_RECORD_INPUTS if producer is not None}
    producers.update((raw_aliases[name], producer) for name, producer in owner.FEATURE_ARRAY_INPUTS)
    bindings = tuple(replace(binding, kind=WorkerInputKind.DEPENDENCY if binding.artifact_id in producers else WorkerInputKind.EXTERNAL)
        for binding in bundle.input_bindings)
    ports = plane.open_many(bundle.verified_inputs, bindings=bindings, maximum_bytes=None)
    dependent = defaultdict(list)
    for binding in bindings:
        if binding.kind is WorkerInputKind.DEPENDENCY:
            dependent[source_task_id(public.root.root_id, producers[binding.artifact_id])].append(binding.materialization_id)
    receipts = tuple(sorted((DependencyReceiptBinding("receipt.feature." + task, task, tuple(sorted(materializations)))
        for task, materializations in dependent.items()), key=lambda row: row.receipt_id))
    outputs = (WorkerOutputPort(task_id + ".product", ProtectedE3CausalFeature.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", "ordinary.feature.output"),)
    reference = CapabilityConfigRef(config.record_id, config.SCHEMA, manifest.config_schema_sha256, config.fingerprint(), current_alias)
    context = TaskContext(case.history.native.receipt.run_id, task_id, "attempt.literal.feature-worker", reference,
        bindings, ports, outputs, manifest.permissions, Access.OUTCOME_BLIND, owner.BUDGET, WorkerIsolationProfile.TRUSTED_LOCAL, receipts)
    edges = []
    for name, kind, producer in (*owner.FEATURE_RECORD_INPUTS, *((name, None, producer) for name, producer in owner.FEATURE_ARRAY_INPUTS)):
        alias = aliases[name] if kind else raw_aliases[name]
        incoming, output = by_id[alias], "product" if kind else "arrays"
        if damage == "producer-port" and name == "numerical":
            output = "arrays"
        edges.append(ScientificInputSpec("edge.feature." + name, name, ScientificInputRole.HISTORY if producer else ScientificInputRole.SOURCE,
            source_task_id(public.root.root_id, producer) if producer else None,
            (source_task_id(public.root.root_id, producer) + "." + output if qualified_outputs else output) if producer else None,
            "external." + name if producer is None else None, "scientific.feature." + name, alias,
            incoming.logical.payload_schema, incoming.logical.media_type, incoming.materialization.size_bytes,
            Access.OUTCOME_BLIND, Visibility.PROSPECTIVE, BarrierKind.NONE))
    external = tuple(sorted((ExternalInputSpec("input." + row.artifact_id, row.artifact_id, row.logical.content_sha256,
        row.logical.payload_schema, row.logical.media_type, row.materialization.size_bytes, Visibility.PROSPECTIVE,
        Access.OUTCOME_BLIND, None) for row in bundle.verified_inputs if row.artifact_id not in producers), key=lambda row: row.input_id))
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind, reference,
        manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions, EvidenceCeiling.RESPONSE, Access.OUTCOME_BLIND, owner.BUDGET)
    task = ExecutionTask(task_id, ScientificStage.TRANSFORM, requirement, manifest.implementation_sha256, tuple(sorted(dependent)), external,
        tuple(ArtifactOutputSpec(port.output_id, port.logical_artifact_id, "feature-output/product.json", port.payload_schema,
            port.profile, port.media_type, Visibility.PROSPECTIVE, (), Access.OUTCOME_BLIND) for port in outputs), (),
        BarrierKind.NONE, 1, ("obligation.literal.feature-worker",), scientific_inputs=tuple(sorted(edges, key=lambda row: row.edge_id)))
    task = freeze_worker_configuration(task)
    provenance = case.source.provenance
    implementation = RecursiveImplementationBinding(provenance.package_sources, provenance.code_sources_sha256,
        provenance.dependency_lock_sha256, provenance.observed_git_head, provenance.observed_checkout_clean)
    contract = prepare_worker_invocation(runner, context, bundle.verified_inputs, implementation=implementation,
        execution_plan=ObjectIdentity("plan.literal.feature-worker", "empirical-lawhood/runtime/execution-plan", "1.0.0", "e"*64),
        execution_task=ObjectIdentity.from_record(task_id, task), execution_task_record=task)
    return SimpleNamespace(context=replace(context, prepared_invocation=contract), runner=runner, bundle=bundle, config=config)


def close(selected):
    for port in selected.context.input_ports:
        port.close()
    selected.bundle.close()


def test_seedless_config_and_actual_declaration_have_no_native_private_payload(case):
    declaration = owner.feature_declaration()
    assert declaration.registration().stage is ScientificStage.TRANSFORM
    assert not declaration.registration().native_effect
    assert tuple(field.name for field in fields(owner.ProtectedE3FeatureConfig)) == (
        "record_id", "specification", "allocation", "public_source", "numerical_design", "root")
    assert {row.port_id for row in declaration.input_ports} == {
        "specification", "public-source", "numerical-design", "numerical", "witness", "assessment", "causal", "causal-arrays", "diagnostic-arrays"}


@pytest.mark.parametrize("qualified_outputs", (False, True))
def test_actual_feature_factory_uses_sealed_dataset_ports_and_retains_nonuse(case, tmp_path, monkeypatch, qualified_outputs):
    selected = prepared_feature(case, tmp_path, qualified_outputs=qualified_outputs)
    supplied = []
    original = owner.project_protected_e3_feature

    def observe(*arguments):
        supplied.extend(arguments[-2:])
        assert all(type(port).__name__ == "WorkerInputPort" for port in arguments[-2:])
        return original(*arguments)

    monkeypatch.setattr(owner, "project_protected_e3_feature", observe)
    try:
        result = selected.runner.execute(selected.context)
        product = decode_canonical_bytes(result.outputs[0].payload, ProtectedE3CausalFeature, maximum_bytes=None)
        expected = project_protected_e3_feature(case.specification, ScheduledPublicSource.from_source(case.source),
            case.causal, case.witness, case.assessment, case.causal_raw, case.diagnostic_raw)
        assert product.canonical_bytes() == expected.canonical_bytes()
        assert product.disposition == "UNAVAILABLE" and product.values == ()
        assert len(supplied) == 2 and all(port.bytes_read == 0 for port in supplied)
        keys = set(json.loads(selected.config.canonical_bytes())["value"])
        assert keys == {field.name for field in fields(selected.config)}
        assert all(check.passed for check in result.checks)
    finally:
        close(selected)


@pytest.mark.parametrize("damage", ("profile", "public-reference", "numerical-tolerance", "numerical-denominator", "producer-port", "array-alias"))
def test_actual_seedless_worker_refuses_wrong_original_profile_or_received_edges_before_math(case, tmp_path, monkeypatch, damage):
    selected = prepared_feature(case, tmp_path, damage=damage)
    monkeypatch.setattr(owner, "project_protected_e3_feature", blocked)
    try:
        with pytest.raises((TypeError, ValueError)):
            selected.runner.execute(selected.context)
        assert all(port.bytes_read == 0 for port in selected.context.input_ports if port.payload_schema == MATRIX_ARRAY_SCHEMA)
    finally:
        close(selected)


@pytest.mark.parametrize("damage", ("unprepared", "missing-receipt", "permissions", "current-task"))
def test_feature_context_refuses_before_input_reads(case, tmp_path, monkeypatch, damage):
    selected = prepared_feature(case, tmp_path)
    monkeypatch.setattr(owner, "project_protected_e3_feature", blocked)
    try:
        with pytest.raises((TypeError, ValueError)):
            if damage == "unprepared":
                context = replace(selected.context, prepared_invocation=None)
            elif damage == "missing-receipt":
                context = replace(selected.context, dependency_receipts=selected.context.dependency_receipts[:-1])
            elif damage == "permissions":
                context = replace(selected.context, permissions=())
            else:
                context = replace(selected.context, task_id="task.foreign")
            selected.runner.execute(context)
        assert all(port.bytes_read == 0 for port in selected.context.input_ports)
    finally:
        close(selected)
