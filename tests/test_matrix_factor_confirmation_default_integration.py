# SPDX-License-Identifier: MPL-2.0
"""Default E1 application-route software proof, with no scientific execution.

The four-root selections, qualifications and selected-source inspector below are
hypothetical test controls. Only source inspection is replaced; the installed
catalog, authoring API, content-addressed custody, loader and provider proof are
the actual application owners. No issue, signer, native producer or fit runs.
"""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_confirmation import records as records, science
from empirical_lawhood.adapters.methods.matrix_factor_confirmation.commitment import COMMIT_KEY, E1Commitment, E1CommitmentConfig, committed
from empirical_lawhood.adapters.methods.matrix_factor_confirmation.operation_bindings import (
    KEY, NAMESPACE, E1AdjudicationConfig, E1NativeRunner, E1OperationConfig,
    _decode,
)
from empirical_lawhood.api import recursive_prospective_authoring as author
from empirical_lawhood.api.authoring_handoff import create_authoring_api
from empirical_lawhood.api.execution import CampaignExecutionService
from empirical_lawhood.api.recursive_operations import operation_catalog, operation_factories
from empirical_lawhood.api.results import CompileCandidateRequest
from empirical_lawhood.infrastructure.candidate_sources import ExternalCandidateInputPublisher, ExternalContentAddressedInputResolver
from empirical_lawhood.infrastructure.artifacts import ArtifactPlaneError
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.execution_envelope import (
    ChildResourceTokenLimit, ExecutionResourceEnvelopeSpec, ExecutionResourceTaskCellSpec,
    NonTimeResourceBudget, ProgressHeartbeat, ProgressLivenessContract,
)
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactWriteRequest, lineage_parent_sort_key
from empirical_lawhood.runtime.execution import DependencyReceiptBinding, TaskContext, VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind, WorkerInputPort, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.executable_bindings import LayeredCampaignRuntimeProviderResolver
from empirical_lawhood.runtime.providers import CampaignRuntimeProviderRegistry
from empirical_lawhood.runtime.capabilities import CapabilityConformanceError
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveAuthoringSpec, RecursiveProspectiveOperand
from empirical_lawhood.runtime.source_resolution import ContentAddressedResolutionError, SourceMaterializationConfig, SourceReadMode
from empirical_lawhood.runtime.study_issue import project_standard_study_extensions
from tests.experiment_entry_support import standard_authoring_for_draft
from tests.prospective_source_capture_fixture import SyntheticSourceInspector, synthetic_capture
from tests.test_matrix_factor_confirmation_adjudication import prospective
from tests.test_matrix_factor_confirmation_adjudication import context as evaluator_context, products as evaluator_products
from tests.test_matrix_factor_confirmation_eligibility import provenance as provenance
from tests.test_matrix_factor_confirmation_eligibility import stock as stock
from tests.test_matrix_factor_confirmation_history import e1 as e1
from tests.test_matrix_factor_response import Reader


# Explicit operational test selection, not a scientific parameter or estimate.
TEST_BUDGET = ResourceBudget(1, 1024**3, 0, None, 64*1024**2, 64*1024**2)


def _blocked(*args, **kwargs):
    raise AssertionError('application proof entered native, producer, assessment, RNG or eigensolve')


def _block_science(monkeypatch):
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_source
    monkeypatch.setattr(E1NativeRunner, 'execute_with_native_subwork', _blocked)
    monkeypatch.setattr(parameter_source, 'acquire_parameter_history', _blocked)
    monkeypatch.setattr(science, 'measure', _blocked)
    monkeypatch.setattr(science, 'assess_history', _blocked)
    monkeypatch.setattr(science, 'assess_factor', _blocked)
    monkeypatch.setattr(np.random, 'Generator', _blocked)
    monkeypatch.setattr(np.random, 'PCG64DXSM', _blocked)
    monkeypatch.setattr(np.linalg, 'eigh', _blocked)
    monkeypatch.setattr(np.linalg, 'eigvalsh', _blocked)


def _resources(compilation, *, native_task_ids=None):
    cells = []
    for step in compilation.template.protocol.steps:
        native = step.step_id.endswith('.history') if native_task_ids is None else step.step_id in native_task_ids
        cells.append(ExecutionResourceTaskCellSpec('cell.'+step.step_id, step.step_id, 'child.software-e1',
            'unit.'+step.step_id if native else None, 'preparation.'+step.step_id if native else None,
            1, int(native), int(native), native,
            NonTimeResourceBudget('budget.'+step.step_id, TEST_BUDGET.cpu_cores, TEST_BUDGET.memory_bytes,
                TEST_BUDGET.output_bytes, 0, TEST_BUDGET.source_scan_bytes),
            ProgressLivenessContract('liveness.'+step.step_id, ProgressHeartbeat.SCHEMA, 'software-only-work',
                Decimal(10), True, True) if native else None, None, None))
    return ExecutionResourceEnvelopeSpec('resources.software-default-e1',
        ObjectIdentity('extensions.software-default-e1', 'empirical-lawhood/runtime/issued-extension-set', '1.0.0', 'e'*64),
        tuple(sorted(cells, key=lambda c: c.cell_id)),
        (ChildResourceTokenLimit('child.software-e1', 4 if native_task_ids is None else len(native_task_ids), 0),),
        (), (), (), None, None, 1, TEST_BUDGET.memory_bytes, (), (), 'f'*64, True, True, True, True)


def _selected_records(draft, definition):
    records_by_hash = {(definition.SCHEMA, definition.fingerprint()): definition}
    for operation in draft.operations:
        cls = E1AdjudicationConfig if operation.node_id == KEY else E1CommitmentConfig if operation.node_id == NAMESPACE+'.commit' else E1OperationConfig
        config = decode_canonical_bytes(operation.config_payload.encode(), cls, maximum_bytes=None)
        sources = config.sources if cls in (E1AdjudicationConfig, E1CommitmentConfig) else (config.source,)
        for source in sources:
            for record in (source, source.allocation, source.specification.selection, source.coordinate,
                           source.provenance, *source.root.streams):
                records_by_hash[record.SCHEMA, record.fingerprint()] = record
    return records_by_hash


def _application(e1, tmp_path, monkeypatch, *, selected_budget=TEST_BUDGET):
    _block_science(monkeypatch)
    plane, _, definition = e1
    draft, qualifications = prospective(e1)
    records_by_hash = _selected_records(draft, definition)
    payloads = {e.logical_artifact_id: records_by_hash[e.payload_schema, e.expected_content_sha256].canonical_bytes()
        for e in draft.external_inputs}
    sources = []
    externals = {e.input_id: e for e in draft.external_inputs}
    for n, source in enumerate(draft.prospective_draft.source_materializations):
        external = externals[source.source_id]
        raw = payloads[external.logical_artifact_id]
        config = SourceMaterializationConfig('source-config.software-e1.'+str(n), source.source_id, source.role,
            sha256(raw).hexdigest(), len(raw), len(raw), external.payload_schema, external.media_type,
            SourceReadMode.ORDINARY_BOUNDED, external.outcome_access, external.visibility_ceiling)
        sources.append(replace(source, source_config_sha256=config.fingerprint()))
        payloads[config.fingerprint()] = config.canonical_bytes()
    root = draft.prospective_draft
    campaign = replace(root.campaign, budget=ResourceBudget.aggregate(selected_budget for _ in draft.operations),
        authority_policy=ObjectIdentity.from_record(root.system.authority_policy.policy_id,
        root.system.authority_policy), nodes=tuple(replace(n, object_identity=ObjectIdentity.from_record(root.system.system_id, root.system))
            if n.object_identity.object_id == root.system.system_id else n for n in root.campaign.nodes))
    draft = replace(draft, campaign=campaign, prospective_draft=replace(root, campaign=campaign,
        source_materializations=tuple(sorted(sources, key=lambda s: s.source_id))),
        operations=tuple(replace(o, resource_budget=selected_budget) for o in draft.operations))
    registrations, registry, codecs = operation_catalog()
    selected = {o.selection.selection_id for o in draft.operations}
    registry = type(registry)(registry.registry_id, tuple(m for m in registry.capabilities if m.registry_id in selected))
    compilation = compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
        implementation_commit='d'*40, qualifications=qualifications,
        known_design_inputs=draft.prospective_draft.design_inputs, output_codecs=codecs)
    assert compilation.candidate_report.candidate is not None, compilation.candidate_report.diagnostics
    standard, formal = standard_authoring_for_draft(compilation.candidate_draft, compilation.candidate_context,
        formal_method_capability_key=KEY)
    operands = tuple(sorted((RecursiveProspectiveOperand(e.logical_artifact_id, e.expected_content_sha256,
        len(payloads[e.logical_artifact_id]), e.payload_schema, e.media_type, e.outcome_access, e.visibility_ceiling)
        for e in draft.external_inputs), key=lambda e: e.logical_artifact_id))
    spec = RecursiveProspectiveAuthoringSpec('authoring.software-default-e1', draft, standard.entry_package,
        formal.formal_methods, formal.source_inventories, qualifications, compilation.candidate_context.known_design_inputs,
        _resources(compilation), operands)
    captured = synthetic_capture(spec.spec_id + '.source-closure',
        compilation.candidate_context.implementation_sha256, clean=False)
    manifest = replace(captured.manifest, implementation_commit='d'*40)
    closure = replace(captured.closure, implementation_commit='d'*40, exact_source_manifest=manifest.identity)
    captured = replace(captured, closure=closure, manifest=manifest,
        source=replace(captured.source, implementation_commit='d'*40))
    # Explicit software source, including documentary dirt. No actual checkout
    # observation, clean-source claim or historical capture API is supplied.
    def selected_source(_project_root, closure_id):
        assert closure_id == captured.closure.source_closure_id
        return captured
    monkeypatch.setattr(author, 'capture_target_closure', selected_source)
    monkeypatch.setattr(author, 'GitStudySourceClosureInspector', SyntheticSourceInspector)
    compilation, executable, decoder, registrations = author._compile(spec, closure)
    assert {m.registry_id for m in compilation.registry.capabilities} == selected
    publisher = ExternalCandidateInputPublisher(plane.root)
    for payload in (*payloads.values(), *(r.payload for r in compilation.config_inputs),
                    *(q.canonical_bytes() for q in qualifications)):
        publisher.publish(payload, maximum_bytes=16*1024**2)
    context = author._context(spec, compilation, registrations, plane.root)
    project = tmp_path/'hypothetical-checkout'
    project.mkdir()
    preview = tmp_path/'preview'
    preview.mkdir()
    for name, record in (('authoring', executable), ('selection', compilation.selected_scientific_projection), ('decoder', decoder)):
        (preview/(name+'.json')).write_bytes(record.canonical_bytes())
    api = create_authoring_api(repo_root=project, candidate_context_provider=context, candidate_capability_catalog=context.catalog)
    result = api.compile_candidate(CompileCandidateRequest(preview/'authoring.json', (preview/'selection.json',), (preview/'decoder.json',)))
    assert result.succeeded, (result.reason_codes, result.errors)
    report = result.payload.report
    extensions, _, _ = project_standard_study_extensions(candidate=report.candidate,
        extension_payload_bytes=(compilation.selected_scientific_projection.canonical_bytes(),), decoder_registrations=(decoder,),
        extension_materializations=report.extension_materializations)
    spec = replace(spec, resources=replace(spec.resources,
        issued_study_extensions=ObjectIdentity.from_record(extensions.issued_extension_set_id, extensions)))
    bindings = []
    for key, raw in payloads.items():
        path = preview/('input.'+sha256(key.encode()).hexdigest()+'.json')
        path.write_bytes(raw)
        bindings.append((key, path))
    return dict(spec=spec, project_root=project, artifact_writer=plane, input_bindings=tuple(bindings)), compilation, plane


@pytest.fixture
def application(e1, tmp_path, monkeypatch):
    return _application(e1, tmp_path, monkeypatch)


def _load(application, destination, monkeypatch):
    args, _, plane = application
    # The ordinary loader's guarded directory contract is retained. Only this
    # isolated software plane's unavailable real storage-profile lookup is replaced.
    monkeypatch.setattr(author, 'resolve_authoring_directory', lambda directory, **kwargs: (Path(directory).resolve(), plane.root.contract))
    return author.load_recursive_prospective_handoff(directory=destination, root=args['project_root'],
        storage_profile=object(), artifact_writer=plane)


def _prove_stock_staging_to_pure_commitment(handoff, plane):
    from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY
    provider = LayeredCampaignRuntimeProviderResolver(precomposed=CampaignRuntimeProviderRegistry(()),
        factories=EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY).resolve(handoff.compilation.registry, platform_ports=handoff.platform_ports)
    run = handoff.projection.source_plan.object_id
    # Exercise the exact stock staging owner on the selected software plane;
    # no issue/engine/executor is constructed or invoked.
    inputs = CampaignExecutionService._persist_provider_inputs(SimpleNamespace(artifact_plane=plane), run,
        provider.external_inputs(handoff.projection), minimum_free_bytes=0)
    task = next(t for t in handoff.projection.tasks if t.task_id == COMMIT_KEY)
    selected = tuple(i for i in inputs if i.artifact_id in task.external_input_artifact_ids)
    ports = tuple(WorkerInputPort(WorkerInputBinding.from_verified(i, kind=WorkerInputKind.EXTERNAL),
        Reader(plane.root.resolve(i.materialization.relative_path, for_write=False).read_bytes())) for i in selected)
    config = next(row.record for row in handoff.compilation.config_inputs if type(row.record) is E1CommitmentConfig)
    for publication in (config.sources[0].reservation.publication, config.sources[0].specification.publication):
        staged = next(p for p in ports if p.artifact_id == publication.logical.logical_artifact_id)
        assert staged.materialization_id != publication.materialization.materialization_id
    context = TaskContext(run, COMMIT_KEY, run+'.commit.software-only', task.capability.config,
        tuple(p.binding for p in ports), ports, tuple(WorkerOutputPort(o.output_id, o.payload_schema, o.profile, o.media_type,
            o.logical_artifact_id) for o in task.outputs), task.capability.required_permissions,
        task.capability.requested_outcome_access, task.capability.requested_resources, WorkerIsolationProfile.TRUSTED_LOCAL)
    runner = next(r for r in provider.runners(handoff.compilation.registry) if r.manifest.capability_key == COMMIT_KEY)
    value = runner.execute(context)
    assert decode_canonical_bytes(value.outputs[0].payload, E1Commitment, maximum_bytes=None) == committed(config)
    output = task.outputs[0]
    parents = tuple(sorted((ArtifactLineageParent(ObjectIdentity.from_record(i.logical.logical_artifact_id, i.logical),
        i.logical.visibility_ceiling, i.logical.outcome_access) for i in selected), key=lineage_parent_sort_key))
    write = plane.write(ArtifactWriteRequest(output.logical_artifact_id, output.relative_path, output.payload_schema,
        output.profile, output.media_type, 'publication.hypothetical-default-commit', Path(output.relative_path).parent.as_posix(),
        value.outputs[0].payload, output.visibility_ceiling,
        tuple(sorted((p.visibility_ceiling for p in parents), key=lambda v: v.value)), output.outcome_access, lineage_parents=parents))
    history_task = next(t for t in handoff.projection.tasks if t.capability.capability_key == NAMESPACE+'.history')
    external = tuple(i for i in inputs if i.artifact_id in history_task.external_input_artifact_ids)
    native_ports = [WorkerInputPort(WorkerInputBinding.from_verified(i, kind=WorkerInputKind.EXTERNAL),
        Reader(plane.root.resolve(i.materialization.relative_path, for_write=False).read_bytes())) for i in external]
    native_ports.append(WorkerInputPort(WorkerInputBinding.from_verified(VerifiedArtifactInput(write.logical, write.materialization),
        kind=WorkerInputKind.DEPENDENCY), Reader(value.outputs[0].payload)))
    native_ports = tuple(sorted(native_ports, key=lambda p: p.artifact_id))
    context = TaskContext(run, history_task.task_id, run+'.history.software-only', history_task.capability.config,
        tuple(p.binding for p in native_ports), native_ports,
        tuple(WorkerOutputPort(row.output_id, row.payload_schema, row.profile, row.media_type,
            row.logical_artifact_id) for row in history_task.outputs), history_task.capability.required_permissions,
        history_task.capability.requested_outcome_access, history_task.capability.requested_resources, WorkerIsolationProfile.TRUSTED_LOCAL,
        (DependencyReceiptBinding('receipt.hypothetical-default-commit', COMMIT_KEY, (write.materialization.materialization_id,)),))
    from empirical_lawhood.infrastructure.execution import prepare_worker_invocation
    from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
    provenance = config.sources[0].provenance
    implementation = RecursiveImplementationBinding(provenance.package_sources, provenance.code_sources_sha256,
        provenance.dependency_lock_sha256, provenance.observed_git_head, provenance.observed_checkout_clean)
    verified = tuple(sorted((*external, VerifiedArtifactInput(write.logical, write.materialization)),
        key=lambda row: row.artifact_id))
    contract = prepare_worker_invocation(E1NativeRunner('history'), context, verified,
        implementation=implementation,
        execution_plan=ObjectIdentity.from_record(handoff.projection.execution_plan_id, handoff.projection),
        execution_task=ObjectIdentity.from_record(history_task.task_id, history_task), execution_task_record=history_task)
    assert not contract.native_effect and contract.native_work is None
    context = replace(context, prepared_invocation=contract)
    try:
        native_config, source, _, _ = _decode(context, 'history')
        assert native_config.source == source and source in config.sources
    finally:
        for port in native_ports:
            port.close()


def test_default_e1_public_author_load_and_provider_proof_with_optional_bounds(application, monkeypatch):
    args, compilation, plane = application
    assert all(e.maximum_size_bytes is None for e in args['spec'].draft.external_inputs)
    actual = author._operands(args['spec'], compilation)
    assert all(type(o.size_bytes) is int and o.size_bytes > 0 for o in actual)
    installed = tuple(f for f in operation_factories() if f.manifest.capability_key.startswith(NAMESPACE+'.'))
    assert len(installed) == 6 and len({f.registration.selection for f in installed}) == 6
    _, _, codecs = operation_catalog()
    assert all(codecs[schema] is cls for schema, cls in installed[0].output_codecs.items())
    destination = Path(plane.root.contract.canonical_path)/'default-e1-authoring'
    result = author.author_recursive_prospective(**args, output_dir=destination)
    assert result['task_count'] == 18 and result['native_contact'] == 'none' and result['scientific_authority'] == 'NONE'
    handoff = _load(application, destination, monkeypatch)
    proof = author.prove_recursive_prospective_handoff(handoff)
    assert proof['task_count'] == 18 and proof['runner_count'] == 6
    assert proof['scientific_execution_performed'] is False
    assert {t.capability.requested_resources for t in handoff.projection.tasks} == {TEST_BUDGET}
    assert len(handoff.compilation.candidate_context.qualifications) == len(args['spec'].qualifications)
    _prove_stock_staging_to_pure_commitment(_load(application, destination, monkeypatch), plane)
    selected = next(o for o in args['spec'].external_operands if sum(any(e.logical_artifact_id == o.logical_artifact_id
        for e in t.external_inputs) for t in handoff.projection.tasks) > 1)
    for defect in ('finite-oversize', 'metadata', 'changed-bytes', 'shared-sha', 'shared-size', 'shared-access', 'shared-scope'):
        fresh = _load(application, destination, monkeypatch)
        if defect.startswith('shared-'):
            matching = tuple(t for t in fresh.projection.tasks if any(e.logical_artifact_id == selected.logical_artifact_id for e in t.external_inputs))
            assert len(matching) > 1
            changes = {'shared-sha': {'expected_content_sha256': 'f'*64}, 'shared-size': {'expected_size_bytes': selected.size_bytes+1},
                'shared-access': {'expected_outcome_access': OutcomeAccess.DEVELOPMENT_VISIBLE}, 'shared-scope': {'identity_scope_sha256': 'f'*64}}
            tasks = tuple(replace(t, external_inputs=tuple(replace(e, **changes[defect])
                if e.logical_artifact_id == selected.logical_artifact_id else e for e in t.external_inputs))
                if t.task_id == matching[0].task_id else t for t in fresh.projection.tasks)
            fresh = replace(fresh, projection=replace(fresh.projection, tasks=tasks))
        elif defect == 'finite-oversize':
            tasks = tuple(replace(t, scientific_inputs=tuple(replace(edge, maximum_size_bytes=selected.size_bytes-1)
                if edge.external_input_id is not None and edge.operational_logical_artifact_id == selected.logical_artifact_id else edge
                for edge in t.scientific_inputs)) for t in fresh.projection.tasks)
            fresh = replace(fresh, projection=replace(fresh.projection, tasks=tasks))
        elif defect == 'metadata':
            tasks = tuple(replace(t, external_inputs=tuple(replace(external, expected_media_type='text/plain')
                if external.logical_artifact_id == selected.logical_artifact_id else external for external in t.external_inputs))
                for t in fresh.projection.tasks)
            fresh = replace(fresh, projection=replace(fresh.projection, tasks=tasks))
        else:
            path = ExternalContentAddressedInputResolver.install_path(Path(plane.root.contract.canonical_path), selected.content_sha256)
            original = path.read_bytes()
            mode = path.stat().st_mode & 0o777
            path.chmod(0o600)
            path.write_bytes(original[:-2]+bytes([original[-2]^1])+original[-1:])
        try:
            with pytest.raises(ContentAddressedResolutionError if defect == 'changed-bytes' else ValueError,
                    match='conflicting exact external operand descriptors' if defect.startswith('shared-') else None):
                author.prove_recursive_prospective_handoff(fresh)
        finally:
            if defect == 'changed-bytes':
                path.write_bytes(original)
                path.chmod(mode)


@pytest.mark.parametrize('defect', ('finite-oversize', 'metadata', 'changed-bytes'))
def test_default_e1_public_author_refuses_changed_operand_before_authored_packet(application, defect):
    args, _, plane = application
    args = dict(args)
    spec = args['spec']
    selected = spec.draft.external_inputs[0]
    if defect == 'finite-oversize':
        size = next(o.size_bytes for o in spec.external_operands if o.logical_artifact_id == selected.logical_artifact_id)
        draft = replace(spec.draft, external_inputs=tuple(replace(e, maximum_size_bytes=size-1)
            if e.input_id == selected.input_id else e for e in spec.draft.external_inputs))
        spec = replace(spec, draft=draft)
    elif defect == 'metadata':
        spec = replace(spec, external_operands=tuple(replace(o, media_type='text/plain')
            if o.logical_artifact_id == selected.logical_artifact_id else o for o in spec.external_operands))
    else:
        path = dict(args['input_bindings'])[selected.logical_artifact_id]
        raw = path.read_bytes()
        path.write_bytes(raw[:-2]+bytes([raw[-2]^1])+raw[-1:])
    args['spec'] = spec
    destination = Path(plane.root.contract.canonical_path)/('refusal-'+defect)
    with pytest.raises(ValueError, match='metadata|bound|bytes|input'):
        author.author_recursive_prospective(**args, output_dir=destination)
    assert not destination.exists()


@pytest.mark.parametrize('defect', ('missing-manifest', 'changed-original-bytes', 'changed-sidecar-bytes', 'missing-commit'))
def test_default_author_and_loader_authenticate_original_custody_before_effects(application, monkeypatch, defect):
    args, compilation, plane = application
    root = Path(plane.root.contract.canonical_path)
    destination = root/'retained-original-control'
    author.author_recursive_prospective(**args, output_dir=destination)
    config = next(row.record for row in compilation.config_inputs if type(row.record) is E1CommitmentConfig)
    publication = config.sources[0].reservation.publication
    original_manifest = plane.root.resolve(publication.manifest_materialization.relative_path, for_write=False)
    if defect == 'missing-commit':
        manifest = decode_artifact_manifest(original_manifest.read_bytes())
        path = plane.root.resolve(manifest.publication.commit_marker_relative_path, for_write=False)
    elif defect == 'changed-original-bytes':
        path = plane.root.resolve(publication.materialization.relative_path, for_write=False)
    else:
        path = original_manifest
    if defect.startswith('missing-'):
        moved = path.with_name(path.name+'.hypothetical-control')
        path.rename(moved)
    else:
        raw = path.read_bytes()
        mode = path.stat().st_mode & 0o777
        path.chmod(0o600)
        path.write_bytes(raw[:-2]+bytes([raw[-2]^1])+raw[-1:])
    refusal = root/('prior-refusal-'+defect)
    try:
        with pytest.raises((ValueError, ArtifactPlaneError, OSError)):
            author.author_recursive_prospective(**args, output_dir=refusal)
        assert not refusal.exists()
        with pytest.raises((ValueError, ArtifactPlaneError, OSError)):
            _load(application, destination, monkeypatch)
    finally:
        if defect.startswith('missing-'):
            moved.rename(path)
        else:
            path.write_bytes(raw)
            path.chmod(mode)


def test_default_e1_unselected_memory_limit_cannot_lower_into_finite_envelope(e1, tmp_path, monkeypatch):
    # Evidence for the original mismatch: cells must be finite, while each
    # unchanged default request has no selected memory enforcement limit.
    from empirical_lawhood.adapters.methods.matrix_factor_confirmation.operation_bindings import BUDGET
    args, _, plane = _application(e1, tmp_path, monkeypatch, selected_budget=BUDGET)
    destination = Path(plane.root.contract.canonical_path)/'default-memory-refusal'
    with pytest.raises(ValueError, match='resource cell|task budget|envelope'):
        author.author_recursive_prospective(**args, output_dir=destination)
    assert not (destination/'authored-wave.json').exists()


@pytest.mark.parametrize('placement', ('finite-contained', 'cpu2', 'gpu1'))
def test_e1_worker_budget_guard_accepts_explicit_contained_request_only(e1, placement):
    from empirical_lawhood.adapters.methods.matrix_factor_confirmation.operation_bindings import _worker
    _, sources, _ = e1
    config = E1AdjudicationConfig('config.'+KEY, sources)
    p, a = evaluator_products(sources)
    budget = TEST_BUDGET if placement == 'finite-contained' else replace(TEST_BUDGET,
        cpu_cores=2 if placement == 'cpu2' else 1, gpu_devices=1 if placement == 'gpu1' else 0)
    if placement != 'finite-contained':
        with pytest.raises(CapabilityConformanceError, match='CAPABILITY_RESOURCE_EXCEEDED'):
            evaluator_context(config, p, a, plane=e1[0], resource_budget=budget)
        return
    context = evaluator_context(config, p, a, plane=e1[0], resource_budget=budget)
    manifest = next(f.manifest for f in operation_factories() if f.manifest.capability_key == KEY)
    try:
        assert _worker(context, config, 'adjudicate', manifest) is None
    finally:
        for port in context.input_ports:
            port.close()
