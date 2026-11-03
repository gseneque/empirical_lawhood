# SPDX-License-Identifier: MPL-2.0
"""Actual native preparation/readiness over disclosed metadata, with no contact.

Source exposure/reservation support is the existing software fixture. Direct
ports, declared task/configuration, parent/bound preparation and worker preflight
are actual owners. This creates no qualification or fresh scientific evidence.
"""
from dataclasses import replace
from decimal import localcontext
from pathlib import Path
from threading import local

import pytest
from threadpoolctl import threadpool_limits

from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_acquisition as acquisition
from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_bindings as owner
from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as records
from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.api.recursive_authoring import implementation_binding
from empirical_lawhood.api.recursive_operations import development_output_contracts, operation_catalog
from empirical_lawhood.api.selected_e4_native_runtime import development_output_plane
from empirical_lawhood.infrastructure import execution as lifecycle
from empirical_lawhood.infrastructure.numerical_provenance import selected_worker_environment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.execution import (
    DependencyReceiptBinding, ParentPreparedTaskRunner, TaskContext, VerifiedArtifactInput,
    WorkerInputBinding, WorkerInputKind, WorkerIsolationProfile, WorkerOutputPort)
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.test_matrix_native_training_public_lifecycle import _actual_case, _copied_preparation

ROOT = Path(__file__).resolve().parents[1]


def observe_native_preflight_controls(monkeypatch, native_owner):
    """Check both actual public native phases before their existing fixture entry.

    Called by the exposed public lifecycle controls. It reuses their real
    prepared ports and dependencies rather than constructing future records.
    """
    # This test also observes worker readiness in the parent. Select the same
    # environment for that software probe; actual children sanitize and verify
    # their own settings independently before any native contact.
    for name, value in selected_worker_environment():
        monkeypatch.setenv(name, value)
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_array_preparation as array_owner
    original = lifecycle._prepare_parent_native_runner
    observed = []
    probes = local()
    original_prefix = native_owner.scheduled_science.consume_prefix
    original_values = native_owner._values
    original_array_decode = array_owner.decode_matrix_arrays
    def prefix_values(*args, **kwargs):
        if hasattr(probes, 'events'):
            probes.events.append('prefix')
        return original_prefix(*args, **kwargs)
    def physical_values(ports, name, owner):
        if name == 'physical-arrays' and hasattr(probes, 'events'):
            probes.events.append('physical')
        return original_values(ports, name, owner)
    def frozen_values(*args, **kwargs):
        if hasattr(probes, 'events'):
            probes.events.append('physical')
        return original_array_decode(*args, **kwargs)
    monkeypatch.setattr(native_owner.scheduled_science, 'consume_prefix', prefix_values)
    monkeypatch.setattr(array_owner, 'consume_prefix', prefix_values)
    monkeypatch.setattr(native_owner, '_values', physical_values)
    monkeypatch.setattr(array_owner, 'decode_matrix_arrays', frozen_values)
    runner_type = (native_owner.NativeTrainingNativeRunner if hasattr(native_owner, 'NativeTrainingNativeRunner')
        else native_owner.NativeUtilityNativeRunner)
    def prepare(runner, context, contract, native_work_preparer):
        if not isinstance(runner, ParentPreparedTaskRunner) or not runner.native_effect:
            return original(runner, context, contract, native_work_preparer)
        probes.events = []
        plain, bound, final = original(runner, context, contract, native_work_preparer)
        if type(plain) is not runner_type:
            del probes.events
            return plain, bound, final
        assert final.native_preparation_error is None
        assert probes.events == []  # Both parent work projections stay metadata only.
        assert len(final.native_definitions) == 1
        definition, = final.native_definitions
        assert all(sum((row.logical.payload_schema, row.logical.content_sha256) ==
            (pin.object_schema, pin.object_fingerprint) for row in final.inputs) == 1
            for pin in (definition.configuration, *definition.sources, *definition.streams))
        actual = lifecycle._worker_preflight(plain, bound, final, (MATRIX_PROVENANCE_REQUIREMENT,),
            native_work_preparer=native_owner.prepare_native_work)
        assert actual.ready, tuple((value.operand_id, value.reason) for value in actual.mismatches)
        if plain.operation == 'responses':
            assert probes.events == ['prefix', 'physical']
            arrays = plain._response_arrays(bound)
            repeated = lifecycle._worker_preflight(plain, bound, final, (MATRIX_PROVENANCE_REQUIREMENT,),
                native_work_preparer=native_owner.prepare_native_work)
            assert repeated.ready, repeated.mismatches
            assert probes.events == ['prefix', 'physical']
            assert all(left is right for left, right in zip(arrays, plain._response_arrays(bound), strict=True))
            assert plain._response_array_preparation.__getstate__() == {'_prepared': None}
            with localcontext() as decimal:
                decimal.prec += 1
                with pytest.raises(ValueError, match='actual preflight array inputs'):
                    plain._response_arrays(bound)
        removed = next(value for value in bound.input_ports if value.payload_schema == native_owner.MatrixParameterCoordinate.SCHEMA)
        missing = replace(bound, prepared_invocation=None,
            input_ports=tuple(value for value in bound.input_ports if value is not removed),
            input_bindings=tuple(value for value in bound.input_bindings if value.artifact_id != removed.artifact_id))
        stopped = lifecycle._worker_preflight(plain, missing, final, (MATRIX_PROVENANCE_REQUIREMENT,),
            native_work_preparer=native_owner.prepare_native_work)
        assert not stopped.ready and any(value.operand_id == removed.artifact_id for value in stopped.mismatches)
        for changed in (replace(definition, sources=tuple(sorted((replace(definition.sources[0],
                object_fingerprint='e'*64), *definition.sources[1:]), key=lambda value: value.object_id))),
                replace(definition, code_sources_sha256='e'*64)):
            work = replace(final.native_work, definitions=(changed,),
                rosters=(replace(final.native_work.rosters[0], subworks=(changed.identity,)),))
            mutated = replace(final, native_work=work)
            stopped = lifecycle._worker_preflight(plain, replace(bound, prepared_invocation=mutated),
                mutated, (MATRIX_PROVENANCE_REQUIREMENT,), native_work_preparer=native_owner.prepare_native_work)
            assert not stopped.ready
            assert any('unique authenticated worker input' in value.reason if changed.sources != definition.sources
                else 'selected implementation/environment' in value.reason for value in stopped.mismatches)
        observed.append(plain.operation)
        # These are parent-side software controls. The actual spawned worker
        # must materialize its own independently authenticated arrays.
        plain._response_array_preparation.clear()
        del probes.events
        return plain, bound, final
    monkeypatch.setattr(lifecycle, '_prepare_parent_native_runner', prepare)
    return observed


def prefix_context(case, preparation):
    registrations, registry, codecs = operation_catalog()
    implementation = implementation_binding(ROOT)
    compiled = compile_recursive_wave(draft=preparation.draft, registrations=registrations, registry=registry,
        implementation_commit=implementation.observed_git_head, output_codecs=codecs)
    plan = compiled.execution_plan
    node = acquisition.task_id(case.source.root_id, "prefix")
    task, = (value for value in plan.tasks if value.task_id == node)
    entry, = (value for value in plan.tasks if value.task_id == acquisition.entry_task_id(case.specification))
    config = next(value.record for value in compiled.config_inputs if value.node_id == node)
    scientific_records = dict(preparation.input_records)
    records_by_id = {external.logical_artifact_id: scientific_records[external.input_id]
        for external in preparation.draft.external_inputs if external.input_id in scientific_records}
    records_by_id[config.record_id] = config
    acquisition_edge, = (value for value in task.scientific_inputs if value.consumer_input_id == "acquisition")
    records_by_id[acquisition_edge.operational_logical_artifact_id] = case.acquisition
    external_ids = {value.logical_artifact_id for value in task.external_inputs}
    selected_ids = external_ids | {value.operational_logical_artifact_id for value in task.scientific_inputs}
    verified = []
    for index, logical_id in enumerate(sorted(selected_ids)):
        record = records_by_id[logical_id]
        publication = case.plane.write(ArtifactWriteRequest(logical_id,
            "native-preflight/operand-" + str(index).zfill(3) + ".json", record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json", "control.native-preflight", "native-preflight",
            record.canonical_bytes(), owner.EXPOSED, (), owner.DEV))
        verified.append(VerifiedArtifactInput(publication.logical, publication.materialization))
    verified = tuple(sorted(verified, key=lambda value:value.artifact_id))
    bindings = tuple(WorkerInputBinding.from_verified(value, kind=WorkerInputKind.EXTERNAL
        if value.artifact_id in external_ids else WorkerInputKind.DEPENDENCY) for value in verified)
    ports = case.plane.open_many(verified, bindings=bindings, maximum_bytes=None)
    acquisition_binding, = (value for value in bindings if value.kind is WorkerInputKind.DEPENDENCY)
    # Explicit disclosed dependency receipt binding; no scientific completion
    # or native contact is inferred from this isolated preflight control.
    dependencies = (DependencyReceiptBinding("receipt.disclosed.native-entry", entry.task_id,
        (acquisition_binding.materialization_id,)),)
    outputs = tuple(WorkerOutputPort(value.output_id, value.payload_schema, value.profile,
        value.media_type, value.logical_artifact_id) for value in task.outputs)
    context = TaskContext(plan.source_plan.object_id,node,"attempt.disclosed.native-prefix",task.capability.config,
        bindings,ports,outputs,task.capability.required_permissions,owner.DEV,task.capability.requested_resources,
        WorkerIsolationProfile.TRUSTED_LOCAL,dependencies)
    declaration = next(value for value in owner.operation_declarations() if value.capability_key == records.NAMESPACE + ".prefix")
    return compiled, task, declaration, context, verified, implementation


def test_native_parent_initial_bound_and_actual_worker_preflight_have_exact_direct_operands(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("PURE native preparation or worker readiness entered a native producer")
    monkeypatch.setattr(owner,"execute_parameter_native_work",forbidden)
    monkeypatch.setattr(owner,"execute_paired_response_native_work",forbidden)
    for name, value in selected_worker_environment():
        monkeypatch.setenv(name, value)
    with threadpool_limits(limits=1):
        case = _actual_case(tmp_path,monkeypatch)
        preparation = _copied_preparation(case,tmp_path/"copied")
        compiled,task,declaration,context,verified,implementation = prefix_context(case,preparation)
        codecs = operation_catalog()[2]
        original_semantics = case.plane.semantic_validations
        assert development_output_plane(case.plane, compiled.execution_plan, codecs) is case.plane
        assert case.plane.semantic_validations == original_semantics
        assert development_output_contracts(compiled.execution_plan, codecs)
        changed_task = replace(task, capability_implementation_sha256="e" * 64)
        changed_plan = replace(compiled.execution_plan, tasks=tuple(changed_task if value.task_id == task.task_id
            else value for value in compiled.execution_plan.tasks))
        with pytest.raises(PermissionError, match="installed producer"):
            development_output_contracts(changed_plan, codecs)
        with pytest.raises(PermissionError, match="typed codec"):
            development_output_contracts(compiled.execution_plan, {})
        manifest_decodes = []
        decode = owner.decode_canonical_bytes
        def observed_decode(raw, kind, *, maximum_bytes):
            if kind is owner.ProtectedE3NativeSourceManifest:
                manifest_decodes.append(raw)
            return decode(raw, kind, maximum_bytes=maximum_bytes)
        monkeypatch.setattr(owner, "decode_canonical_bytes", observed_decode)
        owner._decode_shared_manifest.cache_clear()
        runner = declaration.runner_factory()
        assert type(runner) is ParentPreparedTaskRunner and runner.native_effect
        try:
            initial = lifecycle.prepare_worker_invocation(runner,context,verified,implementation=implementation,
                execution_plan=ObjectIdentity.from_record(compiled.execution_plan.execution_plan_id,compiled.execution_plan),
                execution_task=ObjectIdentity.from_record(task.task_id,task),execution_task_record=task,native_effect=True,
                provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,),native_work_preparer=owner.prepare_native_work)
            assert initial.native_work is None and initial.native_preparation_error is None
            plain,bound,final = lifecycle._prepare_parent_native_runner(runner,context,initial,owner.prepare_native_work)
            assert type(plain) is owner.NativeTrainingNativeRunner
            assert final.native_work is not None and final.native_preparation_error is None
            definition, = final.native_definitions
            assert set(definition.sources) == {*records.native_source_pins(case.source),case.acquisition.identity}
            assert all(sum((row.logical.payload_schema,row.logical.content_sha256) ==
                (pin.object_schema,pin.object_fingerprint) for row in final.inputs) == 1
                for pin in (definition.configuration,*definition.sources,*definition.streams))
            readiness = lifecycle._worker_preflight(plain,bound,final,(MATRIX_PROVENANCE_REQUIREMENT,),
                native_work_preparer=owner.prepare_native_work)
            assert readiness.ready, tuple((value.operand_id,value.reason) for value in readiness.mismatches)
            assert len(manifest_decodes) == 1
            with pytest.raises(ValueError):
                owner._decode_shared_manifest(b'{"schema":"changed-foreign-manifest"}\n')
            wrong = replace(final.expected_parent_contact,execution_plan=replace(
                final.expected_parent_contact.execution_plan,object_fingerprint="e"*64))
            with pytest.raises(ValueError,match="complete prepared parent"):
                lifecycle._prepare_native_work(owner.prepare_native_work,plain,bound,wrong)
            with pytest.raises(ValueError,match="prepared invocation"):
                owner._decode(context,"prefix",plain.manifest)
        finally:
            owner._decode_shared_manifest.cache_clear()
            for port in context.input_ports:port.close()
