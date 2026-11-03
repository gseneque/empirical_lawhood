# SPDX-License-Identifier: MPL-2.0
"""Literal prepared PURE workers; no native entry or scientific qualification.

The fixture explicitly authors its native metadata/control publication and
ordinary dependency receipts. Guarded byte ports are real; no signer, issue,
genuine source qualification or actual native contact is created.
"""

from collections import defaultdict
from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import protected_prefix_bindings as declarations
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_prefix_science as science
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_prefix_workers as owner
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_source_records import ProtectedE3SourcePhase as Phase, source_task_id
from empirical_lawhood.infrastructure.execution import prepare_worker_invocation
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays, encode_matrix_arrays
from empirical_lawhood.infrastructure.prepared_native_invocation import NativeInputPublication, prepare_native_invocation
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
from empirical_lawhood.runtime.execution import DependencyReceiptBinding, TaskContext, WorkerInputKind, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec, ScientificInputRole, ScientificInputSpec
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
from tests.worker_configuration_support import freeze_worker_configuration
from tests.test_matrix_e3_protected_prefix_science import blocked, case as original_case, forbid_native as forbid_native  # noqa: F401
from tests.test_matrix_factor_confirmation_eligibility import _matrix_plane


def array_alias(phase):
    return "ordinary.worker." + phase.value + ".arrays"


@pytest.fixture(scope="module")
def case(original_case):  # noqa: F811
    source = original_case
    native = source.history.native
    # literal_history already publishes and joins this exact completion.
    assert any(row.logical_artifact_id == native.receipt.task_id + ".completion"
        and row.content_sha256 == native.completion.fingerprint() for row in native.receipt.output_logical_artifacts)
    receipt = replace(native.receipt, receipt_id="receipt." + native.receipt.attempt_id)
    history = replace(source.history, native=replace(native, receipt=receipt), arrays=replace(source.history.arrays,
        array_artifact=replace(source.history.arrays.array_artifact, artifact_id=array_alias(Phase.PREFIX))))
    arguments = dict(prefix_config=source.config, manifest=source.manifest, specification=source.specification)
    numerical = science.assess_prefix(history, source.native_raw, **arguments)
    diagnostic_raw, witness = science.measure_prefix(history, numerical, source.native_raw,
        artifact_id=array_alias(Phase.MEASURE), **arguments)
    assessment = science.check_frames(history, numerical, witness, source.native_raw, diagnostic_raw, **arguments)
    causal_raw, causal = science.causal_delivery(history, numerical, witness, assessment, source.native_raw, diagnostic_raw,
        artifact_id=array_alias(Phase.PROJECT), **arguments)
    return SimpleNamespace(**{**vars(source), "history": history, "numerical": numerical, "witness": witness,
        "assessment": assessment, "causal": causal, "diagnostic_raw": diagnostic_raw, "causal_raw": causal_raw})


def _manifest(plane, result):
    return decode_artifact_manifest(plane.root.resolve(result.materialization.relative_path + ".manifest.json",
        for_write=False).read_bytes())


def prepared_case(case, phase, *, directory, damage=None, qualified_outputs=True):
    """Real guarded publications plus a disclosed exact prepared task graph."""
    selected = owner.prefix_worker_phase(phase)
    plane = _matrix_plane(directory / "guarded-inputs")
    declaration = declarations.prefix_pure_declaration(phase)
    runner = declaration.runner_factory()
    manifest = declaration.manifest()
    config = replace(case.config, phase=phase, record_id="config." + source_task_id(case.source.root_id, phase))
    task_id = source_task_id(case.source.root_id, phase)
    records = {"prefix-config": case.config, "manifest": case.manifest, "specification": case.specification,
        "history": case.history, "numerical": case.numerical, "witness": case.witness, "assessment": case.assessment}
    if damage == "current-phase":
        config = case.config
    elif damage == "prefix-config":
        records["prefix-config"] = replace(case.config, source_manifest=replace(case.config.source_manifest, object_fingerprint="e"*64))
    elif damage == "native-completion":
        native = case.history.native
        records["history"] = replace(case.history, native=replace(native, receipt=replace(native.receipt,
            output_logical_artifacts=tuple(row for row in native.receipt.output_logical_artifacts if not row.logical_artifact_id.endswith(".completion")),
            output_materializations=tuple(row for row in native.receipt.output_materializations if not row.logical_artifact_id.endswith(".completion")))))
    aliases = {name: "external.worker." + phase.value + "." + name + ".record" if producer is None
        else "ordinary.worker." + producer.value + ".product" for name, _, producer in selected.records}
    current_alias = config.record_id
    publications = [NativeInputPublication(config.record_id, config, current_alias)]
    publications.extend(NativeInputPublication(record.specification_id if name == "specification" else record.record_id,
        record, aliases[name]) for name, _, _ in selected.records for record in (records[name],))
    existing, raw_aliases = [], {}
    for name, producer in selected.arrays:
        raw = case.native_raw if producer is Phase.PREFIX else case.diagnostic_raw
        artifact = array_alias(producer)
        if damage == "array-alias" and producer is Phase.PREFIX:
            artifact = "ordinary.foreign.array.alias"
        if damage == "array-bytes" and producer is Phase.PREFIX:
            values = {name: value.copy() for name, value in decode_matrix_arrays(raw, case.history.arrays).items()}
            values["primary_positions"][0, 0, 0, 0, 0] += 1
            raw, _ = encode_matrix_arrays(values)
        result = plane.write(ArtifactWriteRequest(artifact, "worker-arrays/" + phase.value + "." + name + ".npz",
            MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", "literal-pure-worker", "worker-arrays",
            raw, Visibility.PROSPECTIVE, (), Access.OUTCOME_BLIND))
        existing.append((ObjectIdentity(artifact, MATRIX_ARRAY_SCHEMA, "1.0.0", sha256(raw).hexdigest()), _manifest(plane, result)))
        raw_aliases[name] = artifact
    bundle = prepare_native_invocation(plane, publications=publications, existing_inputs=existing,
        relative_root="worker-inputs-" + phase.value, visibility=Visibility.PROSPECTIVE, access=Access.OUTCOME_BLIND)
    by_id = {row.artifact_id: row for row in bundle.verified_inputs}
    producer_by_alias = {aliases[name]: producer for name, _, producer in selected.records if producer is not None}
    producer_by_alias.update((raw_aliases[name], producer) for name, producer in selected.arrays)
    bindings = tuple(replace(binding, kind=WorkerInputKind.DEPENDENCY if binding.artifact_id in producer_by_alias else WorkerInputKind.EXTERNAL)
        for binding in bundle.input_bindings)
    ports = plane.open_many(bundle.verified_inputs, bindings=bindings, maximum_bytes=None)
    dependent = defaultdict(list)
    for binding in bindings:
        if binding.kind is WorkerInputKind.DEPENDENCY:
            producer = producer_by_alias[binding.artifact_id]
            dependent[source_task_id(case.source.root_id, producer)].append(binding.materialization_id)
    receipts = tuple(sorted((DependencyReceiptBinding("receipt.worker." + task,
        task, tuple(sorted(materializations))) for task, materializations in dependent.items()), key=lambda row: row.receipt_id))
    outputs = tuple(WorkerOutputPort(task_id + "." + template.output_id, template.payload_schema, template.profile,
        template.media_type, array_alias(phase) if template.output_id == "arrays" else "ordinary.worker." + phase.value + ".product")
        for template in declaration.outputs)
    if damage == "output-profile":
        outputs = tuple(replace(port, profile=ArtifactProfile.RAW_SOURCE_BYTES) if port.profile is ArtifactProfile.CANONICAL_JSON else port for port in outputs)
    reference = CapabilityConfigRef(config.record_id, config.SCHEMA, manifest.config_schema_sha256, config.fingerprint(), current_alias)
    context = TaskContext(case.history.native.receipt.run_id, task_id, "attempt.literal.worker." + phase.value,
        reference, bindings, ports, outputs, manifest.permissions, Access.OUTCOME_BLIND, declarations.BUDGET,
        WorkerIsolationProfile.TRUSTED_LOCAL, receipts)
    edges = []
    for name, kind, producer in (*selected.records, *((name, None, producer) for name, producer in selected.arrays)):
        artifact = aliases[name] if kind else raw_aliases[name]
        incoming = by_id[artifact]
        output = "product" if kind else "arrays"
        if damage == "producer-port" and name == "history":
            output = "checkpoint"
        edges.append(ScientificInputSpec("edge." + task_id + "." + name, name, ScientificInputRole.HISTORY if producer else ScientificInputRole.SOURCE,
            source_task_id(case.source.root_id, producer) if producer else None,
            (source_task_id(case.source.root_id, producer) + "." + output if qualified_outputs else output) if producer else None,
            "external." + name if producer is None else None, "scientific.literal." + name, artifact,
            incoming.logical.payload_schema, incoming.logical.media_type, incoming.materialization.size_bytes,
            Access.OUTCOME_BLIND, Visibility.PROSPECTIVE, BarrierKind.NONE))
    external = tuple(sorted((ExternalInputSpec("external." + row.artifact_id, row.artifact_id,
        row.logical.content_sha256, row.logical.payload_schema, row.logical.media_type, row.materialization.size_bytes,
        Visibility.PROSPECTIVE, Access.OUTCOME_BLIND, None) for row in bundle.verified_inputs if row.artifact_id not in producer_by_alias), key=lambda row: row.input_id))
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind,
        reference, manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions, EvidenceCeiling.RESPONSE,
        Access.OUTCOME_BLIND, declarations.BUDGET)
    task = ExecutionTask(task_id, selected.stage, requirement, manifest.implementation_sha256,
        tuple(sorted(dependent)), external, tuple(ArtifactOutputSpec(port.output_id, port.logical_artifact_id,
            "worker-output/" + port.output_id, port.payload_schema, port.profile, port.media_type,
            Visibility.PROSPECTIVE, (), Access.OUTCOME_BLIND) for port in outputs), (), BarrierKind.NONE, 1,
        ("obligation.literal.worker",), scientific_inputs=tuple(sorted(edges, key=lambda row: row.edge_id)))
    task = freeze_worker_configuration(task)
    provenance = case.source.provenance
    implementation = RecursiveImplementationBinding(provenance.package_sources, provenance.code_sources_sha256,
        provenance.dependency_lock_sha256, provenance.observed_git_head, provenance.observed_checkout_clean)
    contract = prepare_worker_invocation(runner, context, bundle.verified_inputs, implementation=implementation,
        execution_plan=ObjectIdentity("plan.literal.pure-worker", "empirical-lawhood/runtime/execution-plan", "1.0.0", "e"*64),
        execution_task=ObjectIdentity.from_record(task.task_id, task), execution_task_record=task)
    context = replace(context, prepared_invocation=contract)
    return SimpleNamespace(runner=runner, context=context, bundle=bundle, task=task, contract=contract)


@pytest.mark.parametrize("phase", tuple(row.phase for row in owner.PURE_PREFIX_PHASES))
@pytest.mark.parametrize("qualified_outputs", (False, True))
def test_actual_declaration_runner_preserves_complete_math_and_ordinary_array_aliases(case, phase, tmp_path, qualified_outputs):
    selected = prepared_case(case, phase, directory=tmp_path, qualified_outputs=qualified_outputs)
    try:
        result = selected.runner.execute(selected.context)
        metadata = owner.prefix_worker_phase(phase)
        outputs = {payload.output_id.rsplit(".", 1)[-1]: payload.payload for payload in result.outputs}
        product = decode_canonical_bytes(outputs["product"], metadata.product_type, maximum_bytes=None)
        expected = {Phase.NUMERICAL: case.numerical, Phase.MEASURE: case.witness, Phase.CHECK: case.assessment, Phase.PROJECT: case.causal}[phase]
        assert product.canonical_bytes() == expected.canonical_bytes()
        if metadata.array_output:
            assert outputs["arrays"] == (case.diagnostic_raw if phase is Phase.MEASURE else case.causal_raw)
            assert product.arrays.array_artifact.artifact_id == array_alias(phase)
        assert all(check.passed for check in result.checks)
        assert all(port.bytes_read == 0 for port in selected.context.input_ports if port.payload_schema == MATRIX_ARRAY_SCHEMA)
        assert case.history.arrays.array_artifact.artifact_id != case.history.checkpoint.prefix_arrays.artifact_id
        if phase is Phase.PROJECT:
            assert product.disposition == "UNEVALUABLE" and product.reason == "PREFIX_NUMERICAL_CONTROLS_NOT_SATISFIED"
    finally:
        for port in selected.context.input_ports:
            port.close()
        selected.bundle.close()


@pytest.mark.parametrize("damage", ("current-phase", "prefix-config", "native-completion", "producer-port", "array-alias", "array-bytes", "output-profile"))
def test_actual_prepared_worker_refuses_adverse_joins_before_scientific_math(case, monkeypatch, damage, tmp_path):
    if damage == "native-completion":
        # The current typed native record refuses this missing publication
        # before a prepared worker context can be constructed.
        with pytest.raises(ValueError, match="native receipt omits its exact canonical completion publication"):
            prepared_case(case, Phase.NUMERICAL, directory=tmp_path, damage=damage)
        return
    selected = prepared_case(case, Phase.NUMERICAL, directory=tmp_path, damage=damage)
    monkeypatch.setattr(science, "assess_prefix", blocked)
    try:
        with pytest.raises((TypeError, ValueError)):
            selected.runner.execute(selected.context)
        if damage == "output-profile":
            assert all(port.bytes_read == 0 for port in selected.context.input_ports)
    finally:
        for port in selected.context.input_ports:
            port.close()
        selected.bundle.close()


@pytest.mark.parametrize("damage", ("unprepared", "permissions", "task", "config-hash", "dependency-receipt", "access"))
def test_actual_complete_context_changes_refuse_before_reads(case, monkeypatch, damage, tmp_path):
    selected = prepared_case(case, Phase.CHECK, directory=tmp_path)
    monkeypatch.setattr(science, "check_frames", blocked)
    try:
        with pytest.raises((TypeError, ValueError)):
            if damage == "unprepared":
                context = replace(selected.context, prepared_invocation=None)
            elif damage == "permissions":
                context = replace(selected.context, permissions=())
            elif damage == "task":
                context = replace(selected.context, task_id="task.foreign")
            elif damage == "config-hash":
                context = replace(selected.context, config=replace(selected.context.config, content_sha256="f"*64))
            elif damage == "dependency-receipt":
                context = replace(selected.context, dependency_receipts=selected.context.dependency_receipts[:-1])
            else:
                context = replace(selected.context, outcome_access=Access.DEVELOPMENT_VISIBLE)
            selected.runner.execute(context)
        assert all(port.bytes_read == 0 for port in selected.context.input_ports)
    finally:
        for port in selected.context.input_ports:
            port.close()
        selected.bundle.close()
