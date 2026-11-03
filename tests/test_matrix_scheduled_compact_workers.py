# SPDX-License-Identifier: MPL-2.0
"""Tiny exposed compact worker custody controls, never scientific authority."""

from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import compact_bindings as cb
from empirical_lawhood.adapters.methods.matrix_scheduled_history import compact_records as cr
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex, ScheduledNativeSourceContext
from empirical_lawhood.adapters.methods.matrix_scheduled_history import operation_bindings as b, records as r, retained
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef
from empirical_lawhood.runtime.execution import DependencyReceiptBinding, TaskContext, VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.plans import BarrierKind, ScientificInputRole, ScientificInputSpec
from tests.matrix_native_invocation_support import literal_native_task, prepared_native_store
from tests.test_matrix_scheduled_history_bindings import (
    TEST_BUDGET, bank as bank, provenance as provenance, scheduled as scheduled, stock as stock,
    commitment_inputs, finish, write,
)
from tests.test_matrix_scheduled_response_bindings import response_bank as response_bank


def compact_context(plane, config, role, inputs, dependencies=()):
    registration = next(registration for registration in cb.operation_registrations()
        if registration.selection.capability_key == cr.NAMESPACE+'.'+role)
    manifest = next(manifest for manifest in cb.operation_manifests() if manifest.capability_key == cr.NAMESPACE+'.'+role)
    task = cr.NAMESPACE+'.'+role if role in ('commit', 'calibrate', 'calibration-qualify') else cr.NAMESPACE+'.'+config.root_id+'.'+role
    config_manifest = write(plane, config.config_id, config.canonical_bytes(), config.SCHEMA, phase=role,
        access=Access.OUTCOME_BLIND, visibility=Visibility.PROSPECTIVE)
    inputs = (config_manifest, *inputs)
    dependency_ids = {material.materialization_id for receipt in dependencies for material in receipt.output_materializations}
    ports = tuple(sorted((plane.open(VerifiedArtifactInput(value.logical, value.materialization),
        binding=WorkerInputBinding.from_verified(VerifiedArtifactInput(value.logical, value.materialization),
            kind=WorkerInputKind.DEPENDENCY if value.materialization.materialization_id in dependency_ids else WorkerInputKind.EXTERNAL),
        maximum_bytes=value.materialization.size_bytes) for value in inputs),
        key=lambda port: port.artifact_id))
    outputs = tuple(WorkerOutputPort(task+'.'+output.output_id, output.payload_schema, output.profile, output.media_type,
        'ordinary.'+task+'.'+output.output_id) for output in registration.outputs)
    config_ref = CapabilityConfigRef(config.config_id, config.SCHEMA, manifest.config_schema_sha256, config.fingerprint(), config.config_id)
    bindings = tuple(sorted((DependencyReceiptBinding(receipt.receipt_id, receipt.task_id,
        tuple(material.materialization_id for material in receipt.output_materializations if material.materialization_id in
            {value.materialization.materialization_id for value in inputs})) for receipt in dependencies), key=lambda value: value.receipt_id))
    context = TaskContext('run.software.compact', task, 'run.software.compact.'+task+'.attempt-001', config_ref,
        tuple(port.binding for port in ports), ports, outputs, manifest.permissions, b.phase_access(role), TEST_BUDGET,
        WorkerIsolationProfile.TRUSTED_LOCAL, bindings)
    return context, inputs


def compact_native_task(runner, context, inputs):
    """Exact edges for this fixture's declared ordinary.* producer outputs."""
    edges = []
    for binding in context.input_bindings:
        if binding.kind is not WorkerInputKind.DEPENDENCY:
            continue
        receipt, = tuple(row for row in context.dependency_receipts
            if binding.materialization_id in row.output_materialization_ids)
        prefix = "ordinary." + receipt.task_id + "."
        if not binding.artifact_id.startswith(prefix):
            raise ValueError("compact fixture dependency substitutes its actual producer output")
        producer_output = binding.artifact_id.removeprefix("ordinary.")
        phase = receipt.task_id.rsplit(".",1)[-1]
        edges.append(ScientificInputSpec("edge."+context.task_id+"."+binding.artifact_id,
            binding.artifact_id,ScientificInputRole.HISTORY,receipt.task_id,producer_output,None,
            binding.artifact_id,binding.artifact_id,binding.payload_schema,binding.media_type,None,
            binding.outcome_access,binding.visibility_ceiling,
            BarrierKind.FREEZE if phase in ("commit","forecast","physical-forecast") else BarrierKind.NONE))
    return literal_native_task(runner,context,inputs,visibility=b.phase_visibility(context.task_id.rsplit('.',1)[-1]),
        scientific_inputs=tuple(edges))


def run_compact_commit(bank):
    plane, sources, original = bank[:3]
    shared = cr.ScheduledCompactBank.from_commitment(original)
    config = cr.ScheduledCompactCommitmentConfig('config.'+cr.NAMESPACE+'.commit', shared)
    inputs = tuple(retained._manifest(plane, publication.materialization.relative_path)
        for _, publication in commitment_inputs(original))
    inputs += tuple(write(plane, record_id, record.canonical_bytes(), record.SCHEMA) for record_id, record in
        ((shared.bank_id, shared), (original.forecast_design.design_id, original.forecast_design),
         *((descriptor.source_id, descriptor) for descriptor in shared.sources)))
    context, _ = compact_context(plane, config, 'commit', inputs)
    result = cb.CompactCommitter().execute(context)
    receipt, outputs = finish(plane, context, result, sources[0])
    return shared, receipt, outputs


def compact_prefix_case(bank):
    """The actual exposed compact prefix shared by worker and cold-read controls."""
    plane, _, original = bank[:3]
    shared, commit_receipt, commit_outputs = run_compact_commit(bank)
    index = ScheduledSourceIndex.from_shared(reservation=shared.reservation,
        specification=shared.specification, provenances=shared.provenances)
    source = index.resolve(next(descriptor for descriptor in shared.sources
        if descriptor.root_id == original.selected_root_ids[0]))
    config = cr.ScheduledCompactConfig('config.'+cr.NAMESPACE+'.'+source.root_id+'.prefix', 'prefix', source.reference,
        cr.compact_identity(shared))
    records = ((shared.bank_id, shared), (source.reference.source_id, source.reference),
        (source.coordinate.coordinate_id, source.coordinate), (source.provenance.identity.object_id, source.provenance),
        *((source.root.stream_identity(stream).object_id, stream) for stream in source.root.streams))
    inputs = tuple(write(plane, name, record.canonical_bytes(), record.SCHEMA) for name, record in records)
    inputs += tuple(retained._manifest(plane, publication.materialization.relative_path)
        for publication in (source.reservation.publication, source.specification.publication))
    context, inputs = compact_context(plane, config, 'prefix', (*inputs, *commit_outputs), (commit_receipt,))
    plan = ObjectIdentity('plan.software.compact', 'empirical-lawhood/runtime/candidate-execution-plan', '1.0.0', 'c'*64)
    manifest = next(manifest for manifest in cb.operation_manifests() if manifest.capability_key == cr.NAMESPACE+'.prefix')
    runner = b.ScheduledNativeRunner('prefix', decoder=cb.decode_core, manifest=manifest)
    task = compact_native_task(runner, context, inputs)
    native,context,_ = prepared_native_store(plane,runner=runner,context=context,manifests=inputs,
        provenance=source.provenance,execution_plan=plan,native_work_preparer=b.prepare_native_work,
        task_record=task,visibility=Visibility.PROSPECTIVE,access=Access.OUTCOME_BLIND)
    result = runner.execute_with_native_subwork(context, native)
    return SimpleNamespace(plane=plane, source=source, shared=shared, config=config, context=context, inputs=inputs,
        plan=plan, task=task, native=native, result=result,
        commit_receipt=commit_receipt, commit_outputs=commit_outputs)


@pytest.mark.parametrize('fixture_name', ('bank', 'response_bank'))
def test_compact_commit_and_prefix_use_actual_original_bytes_and_v2_native_custody(request, fixture_name):
    """A few deliberately exposed states exercise actual stores and decoder."""
    bank = request.getfixturevalue(fixture_name)
    case = compact_prefix_case(bank)
    plane, source, shared = case.plane, case.source, case.shared
    config = case.config
    context, inputs, result, native = case.context, case.inputs, case.result, case.native
    commit_receipt, commit_outputs, plan = case.commit_receipt, case.commit_outputs, case.plan
    product = decode_canonical_bytes(next(output.payload for output in result.outputs if output.output_id.endswith('.product')),
        r.ScheduledPrefixHistory, maximum_bytes=None)
    product.validate_source(source, native_context=ScheduledNativeSourceContext(source, config, shared))
    assert product.source == source.reference.identity
    assert product.native.definition.configuration == cr.compact_identity(config)
    assert product.native.definition.parent_contact.task_id == context.task_id
    assert set(product.native.definition.sources) == set(cr.compact_native_contract(source, 'prefix', bank=shared)[3])
    saved = native.recover(product.native.definition)
    assert saved.receipt == product.native.receipt
    raw = b''.join(native.iter_completed_output(product.native.definition, 'arrays'))
    assert sha256(raw).hexdigest() == product.arrays.array_artifact.sha256
    assert source.reference == next(reference for reference in bank[2].sources if reference.root_id == source.root_id)
    receipts, outputs, products = {'commit': commit_receipt}, {'commit': commit_outputs}, {'prefix': product}
    receipts['prefix'], outputs['prefix'] = finish(plane, context, result, source)
    shared_inputs = {schema: manifest for manifest in inputs for schema in (manifest.logical.payload_schema,)}
    roles = ('numerical', 'measure', 'check', 'project', 'forecast')
    if shared.response_selection is not None:
        roles += ('physical-forecast',)
    roles += ('continue', 'full-numerical')
    if shared.response_selection is not None:
        roles += ('responses', 'response-score')
    for role in roles:
        phase = next(phase for phase in cb.PHASES if phase[0] == role)
        if role == 'forecast':
            config = cr.ScheduledCompactForecastConfig('config.'+cr.NAMESPACE+'.'+source.root_id+'.forecast',
                ScheduledPublicSource.from_source(source), r.identity(shared.forecast_design))
        elif role == 'physical-forecast':
            config = cr.ScheduledCompactPhysicalForecastConfig('config.'+cr.NAMESPACE+'.'+source.root_id+'.'+role,
                shared.response_selection.validate_source(source)[0])
        elif role.startswith('response'):
            config = cr.ScheduledCompactResponseConfig('config.'+cr.NAMESPACE+'.'+source.root_id+'.'+role,
                role, source.reference, shared.response_selection.identity, cr.compact_identity(shared))
        else:
            config = cr.ScheduledCompactConfig(
                'config.'+cr.NAMESPACE+'.'+source.root_id+'.'+role, role, source.reference, cr.compact_identity(shared))
        incoming, dependencies = [], []
        for name, cls in phase[1]:
            if name == 'physical-forecast' and shared.response_selection is None:
                continue
            if name == 'streams':
                incoming.extend(manifest for manifest in inputs if manifest.logical.payload_schema == cb.MatrixHistorySeed.SCHEMA)
                if role.startswith('responses'):
                    _, panels = shared.response_selection.validate_source(source)
                    incoming.extend(write(plane, panel.stream_identity(stream).object_id, stream.canonical_bytes(), stream.SCHEMA)
                        for panel in panels if panel.role == 'INDEPENDENT_FUTURE' for stream in panel.streams)
            elif name in ('bank', 'source', 'allocation', 'selection', 'coordinate', 'provenance'):
                incoming.append(shared_inputs[cls.SCHEMA])
            elif name == 'forecast-design':
                incoming.append(write(plane, shared.forecast_design.design_id, shared.forecast_design.canonical_bytes(), cls.SCHEMA))
            elif name == 'response-selection':
                incoming.append(retained._manifest(plane, shared.response_selection_publication.materialization.relative_path))
            elif name == 'templates':
                incoming.append(retained._manifest(plane, shared.response_selection.template_publications[0].materialization.relative_path))
            else:
                owner = 'prefix' if name.startswith('history') or name == 'checkpoint' else 'project' if name.startswith('causal') or name == 'feature' else 'commit' if name == 'commitment' else 'forecast' if name == 'error-forecast' else name.removesuffix('-arrays')
                suffix = 'arrays' if name.endswith('-arrays') else 'feature' if name == 'feature' else 'checkpoint' if name == 'checkpoint' else 'product'
                incoming.append(next(manifest for manifest in outputs[owner] if manifest.logical.logical_artifact_id.endswith('.'+suffix)))
                if receipts[owner] not in dependencies:
                    dependencies.append(receipts[owner])
        context, actual_inputs = compact_context(plane, config, role, tuple(incoming), tuple(dependencies))
        manifest = next(manifest for manifest in cb.operation_manifests() if manifest.capability_key == cr.NAMESPACE+'.'+role)
        if role in ('continue', 'responses'):
            runner = cb.response.ScheduledPulseNativeRunner(role, decoder=cb.decode_response, manifest=manifest) if role == 'responses' else b.ScheduledNativeRunner(role, decoder=cb.decode_core, manifest=manifest)
            native,context,_ = prepared_native_store(plane,runner=runner,context=context,manifests=actual_inputs,
                provenance=source.provenance,execution_plan=plan,
                native_work_preparer=cb.response.prepare_native_work if role == 'responses' else b.prepare_native_work,
                task_record=compact_native_task(runner,context,actual_inputs),
                visibility=Visibility.PROSPECTIVE,access=Access.EVALUATION_SEALED)
            result = runner.execute_with_native_subwork(context, native)
        else:
            runner = cb.response.ScheduledResponseRunner(role, decoder=cb.decode_response, manifest=manifest) if role in ('physical-forecast', 'response-score') else b.ScheduledRunner(role, decoder=cb.decode_core, manifest=manifest)
            result = runner.execute(context)
        receipts[role], outputs[role] = finish(plane, context, result, source)
        products[role] = decode_canonical_bytes(next(output.payload for output in result.outputs if output.output_id.endswith('.product')),
            phase[2], maximum_bytes=None)
    full = products['continue']
    native_context = ScheduledNativeSourceContext(source, case.config, shared)
    full.validate_source(source, products['prefix'], products['project'], products['forecast'],
        products.get('physical-forecast'), native_context=native_context)
    assert full.native.definition.configuration.object_schema == cr.ScheduledCompactConfig.SCHEMA
    assert full.native.definition.operation_id == cr.NAMESPACE+'.exact-checkpoint-continuation.v2'
    assert products['full-numerical'].numerical_pass
    if shared.response_selection is not None:
        protocol, panels = shared.response_selection.validate_source(source)
        response_product = products['responses']
        response_product.validate_source(source, shared.response_selection, products['prefix'], products['project'],
            products['physical-forecast'], products['forecast'], native_context=native_context)
        assert len(response_product.branch_ids) == 48
        assert len(products['response-score'].cells) == 240
        assert len(products['response-score'].cumulative_log_errors) == 15
        if response_product.native:
            assert response_product.native[0].definition.operation_id == cr.NAMESPACE+'.pulse-response-v2'
