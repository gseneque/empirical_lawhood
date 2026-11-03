# SPDX-License-Identifier: MPL-2.0
"""Real typed worker boundaries over exposed software declarations, no contact."""

from dataclasses import replace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import (
    compact_records as compact, programme_bindings as bindings, programme_global as global_owner,
    programme_records as records,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import ScheduledCommitment
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef
from empirical_lawhood.runtime.execution import (
    DependencyReceiptBinding, TaskContext, VerifiedArtifactInput, WorkerInputBinding,
    WorkerInputKind, WorkerInputPort, WorkerIsolationProfile, WorkerOutputPort,
)
from tests.test_matrix_factor_response import Reader
from tests.test_matrix_scheduled_compact_graph import (
    bank as bank, provenance as provenance, response_bank as response_bank, scheduled as scheduled, stock as stock,
)
from tests.test_matrix_scheduled_history_bindings import TEST_BUDGET, finish, write
from tests.test_matrix_scheduled_programme_graph import programme576_bank


def programme_context(plane, config, role, task, inputs, dependencies=()):
    owner = global_owner if role == 'global-commit' else bindings
    factory = next(f for f in owner.operation_factories() if f.registration.selection.capability_key == records.NAMESPACE+'.'+role)
    registration, manifest = factory.registration, factory.manifest
    config_input = write(plane, config.config_id, config.canonical_bytes(), config.SCHEMA, phase=role)
    inputs = (config_input, *inputs)
    material_ids = {value.materialization.materialization_id for value in inputs}
    dependency_ids = {m.materialization_id for r in dependencies for m in r.output_materializations}
    ports = tuple(sorted((WorkerInputPort(WorkerInputBinding.from_verified(VerifiedArtifactInput(v.logical, v.materialization),
        kind=WorkerInputKind.DEPENDENCY if v.materialization.materialization_id in dependency_ids else WorkerInputKind.EXTERNAL),
        Reader(plane.root.resolve(v.materialization.relative_path, for_write=False).read_bytes())) for v in inputs), key=lambda p: p.artifact_id))
    receipts = tuple(sorted((DependencyReceiptBinding(r.receipt_id, r.task_id,
        tuple(m.materialization_id for m in r.output_materializations if m.materialization_id in material_ids))
        for r in dependencies), key=lambda r: r.receipt_id))
    context = TaskContext('run.software.programme', task, 'run.software.programme.'+task+'.attempt-001',
        CapabilityConfigRef(config.config_id, config.SCHEMA, manifest.config_schema_sha256, config.fingerprint(), config.config_id),
        tuple(p.binding for p in ports), ports,
        tuple(WorkerOutputPort(task+'.'+o.output_id, o.payload_schema, o.profile, o.media_type,
            'ordinary.'+task+'.'+o.output_id) for o in registration.outputs), manifest.permissions,
        registration.outcome_access, TEST_BUDGET, WorkerIsolationProfile.TRUSTED_LOCAL, receipts)
    return context


def test_programme_factories_have_explicit_new_control_and_real_unchanged_v2_configuration_contracts(monkeypatch):
    def blocked(*args, **kwargs):
        pytest.fail('static programme discovery entered numerical science')
    monkeypatch.setattr(np.random, 'Generator', blocked)
    monkeypatch.setattr(np.linalg, 'eigh', blocked)
    factories = bindings.operation_factories()
    assert len(factories) == 19
    assert sum(f.registration.native_effect for f in factories) == 5
    for factory in factories:
        assert factory.runner_factory().manifest == factory.manifest
        assert factory.registration.selection.capability_key.startswith(records.NAMESPACE+'.')
        if factory.registration.native_effect:
            assert factory.registration.config_record_type in (compact.ScheduledCompactConfig, compact.ScheduledCompactResponseConfig)
            assert any(p.payload_schema == bindings.ScheduledProgrammeWaveAdmission.SCHEMA for p in factory.registration.input_ports)
            assert not any(p.payload_schema == ScheduledCommitment.SCHEMA for p in factory.registration.input_ports)
        if factory.manifest.capability_key.endswith('.collect'):
            assert len(factory.registration.input_ports) == 13


def test_actual_programme_admission_and_decoder_refuse_unreceipted_or_outside_wave_before_contact(response_bank, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_factor_response import response_error_prediction
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_science
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history_segments
    def blocked(*args, **kwargs):
        pytest.fail('programme worker admission/decoder entered native science or fitting')
    monkeypatch.setattr(np.random, 'Generator', blocked)
    monkeypatch.setattr(np.linalg, 'eigh', blocked)
    monkeypatch.setattr(parameter_history_segments, 'acquire_parameter_segment', blocked)
    monkeypatch.setattr(response_science, 'native_responses', blocked)
    monkeypatch.setattr(response_error_prediction, 'fit_error_model', blocked)
    monkeypatch.setattr(response_error_prediction, 'fit_scheduled_error_model', blocked)
    plane = response_bank[0]
    programme, bank, _ = programme576_bank(response_bank)
    global_config = global_owner.ScheduledProgrammeGlobalCommitConfig(global_owner.GLOBAL_CONFIG_ID, programme, programme.bank)
    # The actual new metadata worker produces the parent and an ordinary
    # stored receipt. This exposed software run establishes no scientific
    # source qualification or genuine issue/native authority.
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.retained import _manifest
    global_inputs = tuple(_manifest(plane, p.materialization.relative_path) for _, p in global_owner.source_publications(bank))
    global_inputs += tuple(_manifest(plane, p.materialization.relative_path) for p in bank.response_selection.template_publications)
    global_inputs += (write(plane, bank.bank_id, bank.canonical_bytes(), bank.SCHEMA),)
    global_context = programme_context(plane, global_config, 'global-commit', global_owner.GLOBAL_TASK_ID, global_inputs)
    global_factory, = global_owner.operation_factories()
    global_result = global_factory.runner_factory().execute(global_context)
    parent = decode_canonical_bytes(global_result.outputs[0].payload, global_owner.ScheduledProgrammeGlobalCommit,
        maximum_bytes=bindings.MAXIMUM_RECORD_BYTES)
    parent_receipt, parent_outputs = finish(plane, global_context, global_result, response_bank[1][0])
    from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
    parent_manifest, = parent_outputs
    parent_publication = ArtifactWriteResult(parent_manifest.logical, parent_manifest.materialization,
        plane._manifest_materialization(logical_artifact_id=parent_manifest.logical.logical_artifact_id,
            relative_path=parent_manifest.materialization.relative_path+'.manifest.json',
            payload=(plane.root.resolve(parent_manifest.materialization.relative_path+'.manifest.json', for_write=False)).read_bytes()), True)
    from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, CandidateExecutionPlan, ExecutionTask, ExternalInputSpec, PlanLane, ScientificStage
    from empirical_lawhood.runtime.capabilities import CapabilityRequirement
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_parent import ScheduledProgrammeGlobalParentBinding
    from tests.test_matrix_factor_confirmation_eligibility import publish
    factory, = global_owner.operation_factories()
    m = factory.manifest
    req = CapabilityRequirement(m.capability_key, m.capability_version, m.kind, global_context.config,
        m.input_schema_ids, m.output_schema_ids, m.permissions, m.maximum_evidence_ceiling, m.maximum_outcome_access, TEST_BUDGET)
    specs = tuple(ExternalInputSpec('external.'+p.artifact_id, p.artifact_id,
        global_config.fingerprint() if p.artifact_id == global_config.config_id else next(v.logical.content_sha256 for v in global_inputs if v.logical.logical_artifact_id == p.artifact_id),
        p.payload_schema, p.media_type, p.size_bytes, p.visibility_ceiling, p.outcome_access, None) for p in global_context.input_ports)
    out = parent_manifest
    task = ExecutionTask(global_owner.GLOBAL_TASK_ID, ScientificStage.FREEZE, req, m.implementation_sha256, (), specs,
        (ArtifactOutputSpec(global_owner.GLOBAL_TASK_ID+'.product', out.logical.logical_artifact_id, out.materialization.relative_path,
            out.logical.payload_schema, out.logical.profile, out.logical.media_type, out.logical.visibility_ceiling, (), out.logical.outcome_access),),
        (), BarrierKind.FREEZE, 1, ('obligation.software.programme-global',), scientific_inputs=())
    plan = CandidateExecutionPlan('plan.software.programme-global', PlanLane.PROSPECTIVE,
        ObjectIdentity('run.software.programme', 'empirical-lawhood/runtime/candidate-run-plan', '1.0.0', '1'*64), '2'*64,
        parent_receipt.implementation_commit, (task,), True,
        candidate=ObjectIdentity('candidate.software.programme-global', 'empirical-lawhood/planning/draft-study-candidate', '1.0.0', '3'*64))
    config_manifest = next(p for p in global_context.input_ports if p.artifact_id == global_config.config_id)
    published_config = _manifest(plane, next(v.materialization.relative_path for v in
        (write(plane, global_config.config_id, global_config.canonical_bytes(), global_config.SCHEMA, phase='global-commit'),)))
    assert published_config.materialization.materialization_id == config_manifest.materialization_id
    config_publication = ArtifactWriteResult(published_config.logical, published_config.materialization,
        plane._manifest_materialization(logical_artifact_id=published_config.logical.logical_artifact_id,
            relative_path=published_config.materialization.relative_path+'.manifest.json',
            payload=(plane.root.resolve(published_config.materialization.relative_path+'.manifest.json', for_write=False)).read_bytes()), True)
    binding = ScheduledProgrammeGlobalParentBinding('binding.software.programme-global', parent, parent_publication,
        parent_receipt, publish(plane, parent_receipt, 'software.programme.actual-global-receipt'), plan,
        publish(plane, plan, 'software.programme.actual-global-plan'), global_config, config_publication)
    wave = programme.waves[0]
    config = bindings.ScheduledProgrammeWaveAdmissionConfig('config.'+wave.wave_id+'.open', programme,
        programme.bank, wave, parent.identity, compact.compact_identity(parent.semantic_commitment),
        parent_publication, ObjectIdentity.from_record(parent_receipt.receipt_id, parent_receipt), binding)
    inputs = (write(plane, bank.bank_id, bank.canonical_bytes(), bank.SCHEMA), parent_manifest,
        write(plane, parent_receipt.receipt_id, parent_receipt.canonical_bytes(), parent_receipt.SCHEMA))
    context = programme_context(plane, config, 'open', wave.wave_id+'.open', inputs)
    result = bindings.ProgrammeWaveOpener().execute(context)
    admission = decode_canonical_bytes(result.outputs[0].payload, bindings.ScheduledProgrammeWaveAdmission,
        maximum_bytes=bindings.MAXIMUM_RECORD_BYTES)
    assert admission.global_parent == parent
    assert admission.semantic_commitment == parent.semantic_commitment
    assert admission.configuration.object_schema == config.SCHEMA
    receipt, outputs = finish(plane, context, result, response_bank[1][0])

    source_index = ScheduledSourceIndex.from_shared(reservation=bank.reservation,
        specification=bank.specification, provenances=bank.provenances)
    def prefix_context(root_id, *, receipted=True):
        descriptor = next(d for d in bank.sources if d.root_id == root_id)
        source = source_index.resolve(descriptor)
        config = compact.ScheduledCompactConfig('config.'+compact.NAMESPACE+'.'+root_id+'.prefix', 'prefix', descriptor, programme.bank)
        shared = ((bank.bank_id, bank), (descriptor.source_id, descriptor),
            (source.coordinate.coordinate_id, source.coordinate), (source.provenance.identity.object_id, source.provenance),
            *((source.root.stream_identity(stream).object_id, stream) for stream in source.root.streams))
        values = tuple(write(plane, name, value.canonical_bytes(), value.SCHEMA) for name, value in shared)
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.retained import _manifest
        values += tuple(_manifest(plane, p.materialization.relative_path) for p in
            (source.reservation.publication, source.specification.publication))
        return programme_context(plane, config, 'prefix', compact.NAMESPACE+'.'+root_id+'.prefix',
            (*values, *outputs), (receipt,) if receipted else ())
    context = prefix_context(wave.root_ids[0])
    parsed, source, _, _ = bindings.decode_core(context, 'prefix')
    assert parsed.record.SCHEMA == compact.ScheduledCompactConfig.SCHEMA
    assert parsed.record.fingerprint() == context.config.content_sha256
    assert source.reference.identity == next(c.source for c in programme.cases if c.root_id == wave.root_ids[0])
    for p in context.input_ports:
        p.close()
    for root, receipted in ((wave.root_ids[0], False), (programme.waves[1].root_ids[0], True)):
        context = prefix_context(root, receipted=receipted)
        with pytest.raises(ValueError, match='dependency receipt|outside its actual admitted'):
            bindings.decode_core(context, 'prefix')
        for p in context.input_ports:
            p.close()
    with pytest.raises(ValueError, match='actual configuration'):
        replace(admission, configuration=replace(admission.configuration, object_fingerprint='f'*64))

    # Use the actual recursive compiler and a complete global study. The
    # supplied qualifications are explicitly hypothetical software fixtures.
    from tests.programme_entry_support import programme_scientific_root, qualify_programme_draft
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_composition as composition
    from empirical_lawhood.runtime.capabilities import CapabilityRegistry
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
    root, reference = programme_scientific_root(response_bank, programme, bank)
    tasks = composition.programme_wave_runtime_task_ids(programme, bank, wave.wave_id)
    from tests.runtime_platform.test_candidate_compiler import _fixture
    _, compatibility = _fixture()
    owners = [(f'obligation.software.programme-runtime.{i:03}', task) for i, task in enumerate(tasks)]
    # Admission checks the complete frozen declaration, including unacquired
    # cases. Its ordinary metadata output supplies preparation coverage only.
    # Actual selected cutoff acquisition belongs to each original prefix;
    # scientific global support remains the separate later qualification.
    metadata = {row.obligation_id for row in compatibility.templates[0].coverage.bindings
        if row.obligation_id.startswith(root.experiment.experiment_id+'.')}
    metadata.update(('freeze-complete-protocol', 'prepare-independent-units'))
    owners.extend((key, wave.wave_id+'.open') for key in sorted(metadata))
    owners.append(('report-without-promotion', wave.wave_id+'.collect'))
    owners.extend((case.information_cutoff.cutoff_id,
        compact.NAMESPACE+'.'+case.root_id+'.prefix' if case.root_id in wave.root_ids else wave.wave_id+'.open')
        for case in programme.cases)
    owners = tuple(sorted(set(owners)))
    draft, operands = composition.programme_wave_draft(root=root, programme=programme, bank=bank, wave_id=wave.wave_id,
        global_parent=parent, global_parent_publication=parent_publication, global_parent_receipt=parent_receipt,
        global_parent_receipt_publication=binding.receipt_publication, global_parent_binding=binding,
        proof_owners=owners, operational_budgets=dict.fromkeys(tasks, replace(TEST_BUDGET, output_bytes=16*1024**2)),
        template_bytes={bank.response_selection.protocols[0].templates.array_artifact.artifact_id: response_bank[3]},
        draft_id='draft.software.actual-programme-wave')
    draft, qualifications = qualify_programme_draft(draft, operands, reference)
    factories = bindings.operation_factories()
    registry = CapabilityRegistry('registry.software.programme-wave', tuple(sorted((f.manifest for f in factories), key=lambda m: m.registry_id)))
    compiled = compile_recursive_wave(draft=draft, registrations=tuple(f.registration for f in factories), registry=registry,
        implementation_commit=bank.provenances[0].observed_git_head, qualifications=qualifications,
        known_design_inputs=draft.prospective_draft.design_inputs,
        output_codecs={schema: cls for f in factories for schema, cls in f.output_codecs.items()})
    # The ordinary bounded wave cannot own full64 evidential support. Keep
    # the stock candidate compiler's exact refusal instead of assigning
    # global observation, convergence, uncertainty or reveal to admission.
    from empirical_lawhood.runtime.candidate_compiler import CandidateDiagnosticCode
    assert compiled.candidate_report.candidate is None
    diagnostics = compiled.candidate_report.diagnostics
    assert all(d.code is CandidateDiagnosticCode.SCIENTIFIC_OBLIGATION_UNCOVERED for d in diagnostics), diagnostics
    missing = {d.field_path.removeprefix('obligation_coverage.') for d in diagnostics}
    assert {'synthetic-reference-support', 'synthetic-reference-uncertainty', 'synthetic-reference-convergence',
        'synthetic-reference-precision', 'synthetic-reference-reveal'} <= missing
    assert not {case.information_cutoff.cutoff_id for case in programme.cases} & missing
    assert len(compiled.template.protocol.steps) == 398
    assert len(compiled.selected_scientific_projection.canonical_bytes()) <= 16*1024**2
    print({'programme_wave_software_preparation': {'task_count': len(compiled.template.protocol.steps),
        'scientific_projection_bytes': len(compiled.selected_scientific_projection.canonical_bytes()),
        'draft_bytes': len(draft.canonical_bytes()), 'scientific_authority': 'NONE',
        'stock_candidate_disposition': 'INVALID', 'deferred_global_evidence_obligations': tuple(sorted(missing))}})

    # A public coordinate retains its ID while changing physical bytes.
    # The actual compiler must refuse it at the frozen source boundary.
    target = next(o for o in draft.operations if o.node_id.endswith('.forecast'))
    config = decode_canonical_bytes(target.config_payload.encode(), compact.ScheduledCompactForecastConfig, maximum_bytes=4*1024**2)
    public = config.public_source
    coordinate = replace(public.coordinate, primary_view=replace(public.coordinate.primary_view,
        bath_temperature=public.coordinate.primary_view.bath_temperature*2), fine_view=replace(public.coordinate.fine_view,
        bath_temperature=public.coordinate.fine_view.bath_temperature*2))
    changed = replace(config, public_source=replace(public, coordinate=coordinate))
    operation = replace(target, config_payload=changed.canonical_bytes().decode())
    corrupted = replace(draft, operations=tuple(operation if o == target else o for o in draft.operations))
    with pytest.raises(ValueError, match='original public scientific source|scientific operands'):
        compile_recursive_wave(draft=corrupted, registrations=tuple(f.registration for f in factories), registry=registry,
            implementation_commit=bank.provenances[0].observed_git_head, qualifications=qualifications,
            known_design_inputs=draft.prospective_draft.design_inputs,
            output_codecs={schema: cls for f in factories for schema, cls in f.output_codecs.items()})
