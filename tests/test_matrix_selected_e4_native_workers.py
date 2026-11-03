# SPDX-License-Identifier: MPL-2.0
"""Actual PURE protected worker transport; synthetic receipt pins confer no grant."""
from dataclasses import replace
from hashlib import sha256

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_bindings as owner,selected_e4_native_records as r
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_protected_workers import SelectedE4ProtectedWorker
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_programme as p
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.artifacts import ArtifactGenericValidation,ArtifactProfile,LogicalArtifactIdentity
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef,CapabilityRequirement
from empirical_lawhood.runtime.execution import DependencyReceiptBinding,TaskContext,WorkerInputBinding,WorkerInputKind,WorkerInputPort,WorkerIsolationProfile,WorkerOutputPort
from empirical_lawhood.runtime.plans import ArtifactOutputSpec,BarrierKind,ExecutionTask,ExternalInputSpec,ScientificInputRole,ScientificInputSpec
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract,PreparedNativeInputContract,PreparedWorkerEnvironment
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
from tests.test_matrix_selected_protected_worker import MemoryReader
from tests.worker_configuration_support import freeze_worker_configuration
from tests.test_matrix_selected_e4_fixtures import selected_e4_populations,selected_bridge,transfer  # noqa: F401
from tests.test_matrix_selected_e4_methods import selected_revision,fixture_observations  # noqa: F401

def _invocation(config, values, producers):
    declaration = next(row for row in owner.operation_declarations() if row.capability_key == owner.NAMESPACE + "." + config.phase)
    manifest, task_id = declaration.manifest(), config.config_id.removeprefix("config.")
    ports, contracts, external, edges, receipts = [], [], [], [], {}
    for name, value in sorted({"automatic": config, **values}.items()):
        raw = value if type(value) is bytes else value.canonical_bytes()
        arrays = type(value) is bytes
        schema, media, profile = (MATRIX_ARRAY_SCHEMA, "application/x-npz", ArtifactProfile.MATRIX_ARRAY_NPZ) if arrays else (value.SCHEMA, "application/json", ArtifactProfile.CANONICAL_JSON)
        digest = sha256(raw).hexdigest()
        producer = producers.get(name)
        lane=owner.access(config.phase) if name=="automatic" else owner.input_access(name)
        logical = LogicalArtifactIdentity(config.config_id if name == "automatic" else "artifact." + name, digest, schema, profile, media, Visibility.PROSPECTIVE, (), lane,
            ArtifactGenericValidation("validator.disclosed-protected-e4-control", "1.0.0", "1" * 64, schema, profile))
        binding = WorkerInputBinding(logical.logical_artifact_id, "material." + name, schema, media, len(raw), Visibility.PROSPECTIVE,
            lane, WorkerInputKind.DEPENDENCY if producer else WorkerInputKind.EXTERNAL)
        ports.append(WorkerInputPort(binding, MemoryReader(raw)))
        contracts.append(PreparedNativeInputContract(logical, binding, digest))
        output = None if producer is None else producer + (".arrays" if arrays else ".product")
        if producer:
            receipts.setdefault(producer, []).append(binding.materialization_id)
        else:
            external.append(ExternalInputSpec("external." + name, logical.logical_artifact_id, digest, schema, media,
                len(raw), Visibility.PROSPECTIVE, lane, None))
        if name != "automatic":
            edges.append(ScientificInputSpec("edge." + name, name, ScientificInputRole.HISTORY if producer else ScientificInputRole.SOURCE,
                producer, output, None if producer else "external." + name, "scientific." + name, logical.logical_artifact_id,
                schema, media, len(raw), lane, Visibility.PROSPECTIVE, BarrierKind.NONE))
    ports.sort(key=lambda row: row.artifact_id)
    contracts.sort(key=lambda row: row.artifact_id)
    dependencies = tuple(DependencyReceiptBinding("receipt." + task, task, tuple(sorted(materials))) for task, materials in sorted(receipts.items()))
    config_ref = CapabilityConfigRef(config.config_id, config.SCHEMA, manifest.config_schema_sha256, config.fingerprint(), config.config_id)
    outputs = tuple(WorkerOutputPort(task_id + "." + row.output_id, row.payload_schema, row.profile, row.media_type,
        "output.disclosed-protected-e4-control." + row.output_id) for row in declaration.outputs)
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind, config_ref,
        manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions, EvidenceCeiling.NON_PROMOTABLE, owner.access(config.phase), owner.BUDGET)
    task = ExecutionTask(task_id, owner.stage(config.phase), requirement, manifest.implementation_sha256, tuple(sorted(receipts)), tuple(external),
        tuple(ArtifactOutputSpec(output.output_id, output.logical_artifact_id, "unpublished/" + output.output_id + ".json", output.payload_schema, output.profile,
            output.media_type, Visibility.PROSPECTIVE, (Visibility.PROSPECTIVE,), owner.access(config.phase)) for output in outputs),
        (), BarrierKind.NONE, 1, ("obligation.disclosed-protected-e4-control",), scientific_inputs=tuple(edges))
    task = freeze_worker_configuration(task)
    plan = ObjectIdentity("plan.disclosed-protected-e4-control", "empirical-lawhood/runtime/execution-plan", "1.0.0", "a" * 64)
    packages = (("synthetic/control.py", "1" * 64),)
    implementation = RecursiveImplementationBinding(packages, sha256(canonical_json_bytes(packages)).hexdigest(), "2" * 64, "3" * 40, False)
    context = TaskContext("run.disclosed-protected-e4-control", task_id, "attempt.disclosed-protected-e4-control", config_ref, tuple(row.binding for row in ports), tuple(ports),
        outputs, manifest.permissions, owner.access(config.phase), owner.BUDGET, WorkerIsolationProfile.TRUSTED_LOCAL, dependencies)
    prepared = PreparedInvocationContract("prepared.disclosed-protected-e4-control", manifest, implementation,
        PreparedWorkerEnvironment("/synthetic/python", "4" * 64, "/synthetic", ()), context.run_id, task_id, context.attempt_id,
        config_ref, tuple(contracts), outputs, manifest.permissions, owner.access(config.phase), owner.BUDGET,
        WorkerIsolationProfile.TRUSTED_LOCAL, dependencies, execution_plan=plan, execution_task=ObjectIdentity.from_record(task_id, task),
        execution_task_record=task, required_input_artifact_ids=tuple(row.artifact_id for row in ports))
    context = replace(context, prepared_invocation=prepared)
    runner = SelectedE4ProtectedWorker(config.phase, manifest).with_prepared_scope((context.run_id, task_id, context.input_materialization_ids, plan))
    return runner, context

def reduce_invocation(f,*,omit=False):
    programme,bank=f.populations.calibration,f.populations.calibration_bank
    revision=p.SelectedE4RevisionExport.from_products(f.programme,f.nomination,f.frozen,record_id="revision.disclosed-protected")
    reduction,_=fixture_observations(programme,bank,revision=revision)
    wave=programme.waves[0]
    cases=tuple(v for v in reduction.cases if v.root_id in wave.root_ids)
    config=owner.SelectedE4ProtectedReduceConfig("config."+owner.global_node(programme,"reduce",wave.wave_id),programme,bank.identity,wave.wave_id)
    def pin(name,kind):return ObjectIdentity(name,kind.SCHEMA,kind.VERSION,"a"*64)
    entry=r.SelectedE4ProtectedEntrySeal("entry.disclosed-protected",programme.identity,bank.identity,programme.forecast_design,
        pin("evidence.disclosed-protected",r.SelectedE4ProtectedEvidence),wave.group_ids,tuple(v.source for v in programme.cases if v.root_id in wave.root_ids),
        "CALIBRATION",wave.wave_id,None,revision.decision.identity,revision.models.identity,None, secondary_readout=f.populations.secondary_readout.identity)
    values={"entry":entry,**{"cases."+v.root_id:v for v in (cases[:-1] if omit else cases)}}
    producers={"entry":owner.global_node(programme,"entry",wave.wave_id),
        **{"cases."+v.root_id:owner.local_node(v.root_id,"collect") for v in cases}}
    return _invocation(config,values,producers),cases


def test_actual_prepared_reduce_worker_emits_full_wave_reduction_observed_and_prefuture_forecasts(selected_revision):  # noqa: F811
    (runner,context),cases=reduce_invocation(selected_revision)
    result=runner.execute(context)
    assert len(result.outputs)==3
    payloads={v.output_id.rsplit(".",1)[1]:v.payload for v in result.outputs}
    reduction=decode_canonical_bytes(payloads["product"],r.SelectedE4NativeReduction,maximum_bytes=None)
    data=decode_canonical_bytes(payloads["observed"],p.SelectedE4ObservedData,maximum_bytes=None)
    forecasts=decode_canonical_bytes(payloads["forecasts"],p.SelectedE4ForecastBank,maximum_bytes=None)
    assert reduction.cases==cases and len(data.cases)==len(forecasts.forecasts)==36
    assert all(v.revision_forecast==s.identity for v,s in zip(data.cases,forecasts.forecasts,strict=True))
    assert all(port._reader.stream.closed for port in context.input_ports)


def test_actual_prepared_reduce_worker_refuses_missing_assigned_case_before_reduction(selected_revision):  # noqa: F811
    (runner,context),_=reduce_invocation(selected_revision,omit=True)
    with pytest.raises(ValueError,match="assigned exact"):runner.execute(context)
    assert all(port._reader.stream.closed for port in context.input_ports)
