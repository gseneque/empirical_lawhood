# SPDX-License-Identifier: MPL-2.0
"""Actual selected point worker over complete typed in-memory transport.

Synthetic issued descriptors exercise software only. No authority is created,
no publication/native acquisition runs and no scientific standing is inferred.
"""

from dataclasses import replace
from hashlib import sha256
from io import BytesIO

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_protected_bindings as owner
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_point import MatrixSelectedPointForecast
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_programme import MatrixSelectedPreparedConfig, MatrixSelectedPublicProgramme
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_public import MatrixSelectedPointPayload, package_identity
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_results import MatrixSelectedProtectedEntrySeal
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_workers import SelectedProtectedWorker
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.artifacts import ArtifactGenericValidation, ArtifactProfile, LogicalArtifactIdentity
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
from empirical_lawhood.runtime.execution import DependencyReceiptBinding, TaskContext, WorkerInputBinding, WorkerInputKind, WorkerInputPort, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec, ScientificInputRole, ScientificInputSpec, ScientificStage
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract, PreparedNativeInputContract, PreparedWorkerEnvironment
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
from tests.test_matrix_selected_package import reference
from tests.worker_configuration_support import freeze_worker_configuration
from tests.test_matrix_selected_point import literal_unavailable_measurement


class MemoryReader:
    def __init__(self, raw):
        self.raw, self.stream, self.bytes_read = raw, BytesIO(raw), 0
    def read(self, size=-1):
        result = self.stream.read(size)
        self.bytes_read += len(result)
        return result
    def close(self):
        self.stream.close()
    def cursor(self):
        return type(self)(self.raw)
    def seek(self, offset, whence=0):
        return self.stream.seek(offset, whence)
    def tell(self):
        return self.stream.tell()


def invocation():
    design, public, causal, witness, frames, causal_raw, diagnostic_raw = literal_unavailable_measurement("E5_CONFIRMATION")
    design = MatrixSelectedPointPayload.from_design(design)
    programme = reference("programme.synthetic-point", MatrixSelectedPublicProgramme)
    config = MatrixSelectedPreparedConfig("config." + owner.NAMESPACE + "." + public.source.object_id + ".point", programme, public, "point")
    seal = MatrixSelectedProtectedEntrySeal("entry.synthetic-point", programme,
        ObjectIdentity("closure.synthetic-point", "empirical-lawhood/matrix-experimental-programme/protected-source-closure", "1.0.0", "a" * 64),
        design.identity, package_identity(design.package), tuple(sorted(row.source.object_id for _, row in design.sources)))
    values = {"automatic": config, "point-design": design, "entry": seal, "witness": witness, "frames": frames,
        "causal": causal, "causal-arrays": causal_raw, "diagnostic-arrays": diagnostic_raw}
    declaration = next(row for row in owner.operation_declarations() if row.capability_key.endswith(".point"))
    manifest, task_id = declaration.manifest(), owner.task_id(config)
    ports, contracts, external, edges, receipts = [], [], [], [], {}
    for name, value in sorted(values.items()):
        raw = value if type(value) is bytes else value.canonical_bytes()
        arrays = type(value) is bytes
        schema, media, profile = (MATRIX_ARRAY_SCHEMA, "application/x-npz", ArtifactProfile.MATRIX_ARRAY_NPZ) if arrays else (value.SCHEMA, "application/json", ArtifactProfile.CANONICAL_JSON)
        digest = sha256(raw).hexdigest()
        dependency = name not in ("automatic", "point-design")
        artifact_id = config.config_id if name == "automatic" else "artifact." + name
        logical = LogicalArtifactIdentity(artifact_id, digest, schema, profile, media, Visibility.PROSPECTIVE, (), Access.OUTCOME_BLIND,
            ArtifactGenericValidation("validator.synthetic-point", "1.0.0", "1" * 64, schema, profile))
        binding = WorkerInputBinding(logical.logical_artifact_id, "material." + name, schema, media, len(raw), Visibility.PROSPECTIVE,
            Access.OUTCOME_BLIND, WorkerInputKind.DEPENDENCY if dependency else WorkerInputKind.EXTERNAL)
        ports.append(WorkerInputPort(binding, MemoryReader(raw)))
        contracts.append(PreparedNativeInputContract(logical, binding, digest))
        producer = None
        output = None
        if dependency:
            tail = {"witness": "measure", "diagnostic-arrays": "measure", "frames": "frames", "causal": "project", "causal-arrays": "project"}.get(name)
            producer = owner.NAMESPACE + ".entry." + programme.object_fingerprint if name == "entry" else owner.NAMESPACE + "." + public.source.object_id + "." + tail
            output = producer + (".arrays" if arrays else ".product")
            receipts.setdefault(producer, []).append(binding.materialization_id)
        else:
            external.append(ExternalInputSpec("external." + name, logical.logical_artifact_id, digest, schema, media,
                len(raw), Visibility.PROSPECTIVE, Access.OUTCOME_BLIND, None))
        if name != "automatic":
            edges.append(ScientificInputSpec("edge." + name, name, ScientificInputRole.HISTORY if dependency else ScientificInputRole.SOURCE,
                producer, output, None if dependency else "external." + name, "scientific." + name, logical.logical_artifact_id,
                schema, media, len(raw), Access.OUTCOME_BLIND, Visibility.PROSPECTIVE, BarrierKind.NONE))
    ports.sort(key=lambda row: row.artifact_id)
    contracts.sort(key=lambda row: row.artifact_id)
    dependencies = tuple(DependencyReceiptBinding("receipt." + task, task, tuple(sorted(materials))) for task, materials in sorted(receipts.items()))
    config_ref = CapabilityConfigRef(config.config_id, config.SCHEMA, manifest.config_schema_sha256, config.fingerprint(), config.config_id)
    output = WorkerOutputPort(task_id + ".product", MatrixSelectedPointForecast.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", "output.synthetic-point")
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind, config_ref,
        manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions, EvidenceCeiling.RESPONSE, Access.OUTCOME_BLIND, owner.preparation.BUDGET)
    task = ExecutionTask(task_id, ScientificStage.FREEZE, requirement, manifest.implementation_sha256, tuple(sorted(receipts)), tuple(external),
        (ArtifactOutputSpec(output.output_id, output.logical_artifact_id, "unpublished/point.json", output.payload_schema, output.profile,
            output.media_type, Visibility.PROSPECTIVE, (Visibility.PROSPECTIVE,), Access.OUTCOME_BLIND),), (), BarrierKind.FREEZE, 1,
        ("obligation.synthetic-point",), scientific_inputs=tuple(edges))
    task = freeze_worker_configuration(task)
    plan = ObjectIdentity("plan.synthetic-point", "empirical-lawhood/runtime/execution-plan", "1.0.0", "a" * 64)
    packages = (("synthetic/control.py", "1" * 64),)
    implementation = RecursiveImplementationBinding(packages, sha256(canonical_json_bytes(packages)).hexdigest(), "2" * 64, "3" * 40, False)
    context = TaskContext("run.synthetic-point", task_id, "attempt.synthetic-point", config_ref, tuple(row.binding for row in ports), tuple(ports),
        (output,), manifest.permissions, Access.OUTCOME_BLIND, owner.preparation.BUDGET, WorkerIsolationProfile.TRUSTED_LOCAL, dependencies)
    prepared = PreparedInvocationContract("prepared.synthetic-point", manifest, implementation,
        PreparedWorkerEnvironment("/synthetic/python", "4" * 64, "/synthetic", ()), context.run_id, task_id, context.attempt_id,
        config_ref, tuple(contracts), (output,), manifest.permissions, Access.OUTCOME_BLIND, owner.preparation.BUDGET,
        WorkerIsolationProfile.TRUSTED_LOCAL, dependencies, execution_plan=plan, execution_task=ObjectIdentity.from_record(task_id, task),
        execution_task_record=task, required_input_artifact_ids=tuple(row.artifact_id for row in ports))
    context = replace(context, prepared_invocation=prepared)
    runner = SelectedProtectedWorker("point", manifest).with_prepared_scope((context.run_id, task_id, context.input_materialization_ids, plan))
    return runner, context


def test_actual_selected_point_worker_consumes_literal_arrays_and_retains_all_unavailable_predictions():
    runner, context = invocation()
    result = runner.execute(context)
    point = decode_canonical_bytes(result.outputs[0].payload, MatrixSelectedPointForecast, maximum_bytes=None)
    assert point.feature.disposition == "UNAVAILABLE"
    assert all(values == (None,) * 15 for _, values in point.log_points)
    assert point.uncertainty_status == "POINT_ONLY_DOWNSTREAM_APPLICABILITY_NOT_ASSESSED"
    assert all(port._reader.stream.closed for port in context.input_ports)


@pytest.mark.parametrize("damage", ("unprepared", "run", "plan", "corrupt-array", "wrong-producer"))
def test_selected_worker_refuses_current_scope_bytes_or_actual_producer_substitution(damage):
    runner, context = invocation()
    if damage == "unprepared":
        runner = SelectedProtectedWorker("point", runner.manifest)
    elif damage == "run":
        runner = runner.with_prepared_scope(("run.foreign", *runner.prepared_scope[1:]))
    elif damage == "plan":
        runner = runner.with_prepared_scope((*runner.prepared_scope[:3], replace(runner.prepared_scope[3], object_id="plan.foreign")))
    elif damage == "corrupt-array":
        port = next(row for row in context.input_ports if row.artifact_id == "artifact.causal-arrays")
        port._reader.raw = port._reader.raw[:-1] + b"X"
    else:
        prepared = context.prepared_invocation
        task = prepared.execution_task_record
        edges = tuple(replace(edge, producer_output_id=edge.producer_task_id + ".foreign") if edge.consumer_input_id == "causal-arrays" else edge
            for edge in task.scientific_inputs)
        task = replace(task, scientific_inputs=edges)
        prepared = replace(prepared, execution_task_record=task, execution_task=ObjectIdentity.from_record(task.task_id, task))
        context = replace(context, prepared_invocation=prepared)
    with pytest.raises((ValueError, PermissionError)):
        runner.execute(context)
