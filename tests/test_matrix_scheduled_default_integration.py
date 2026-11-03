# SPDX-License-Identifier: MPL-2.0
"""Default compact scheduled conformance over hypothetical software sources.

The catalog, compiler, public author/load, original publication checks and
provider construction are real. Source qualifications and the clean-source
inspector are explicit fixtures, never evidence of scientific eligibility.
"""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import calibration_bindings as cb
from empirical_lawhood.api import recursive_prospective_authoring as author
from empirical_lawhood.api.authoring_handoff import create_authoring_api
from empirical_lawhood.api.recursive_operations import operation_catalog, operation_factories
from empirical_lawhood.api.results import CompileCandidateRequest
from empirical_lawhood.infrastructure.candidate_sources import ExternalCandidateInputPublisher
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveAuthoringSpec, RecursiveProspectiveOperand
from empirical_lawhood.runtime.source_resolution import SourceMaterializationConfig, SourceReadMode
from empirical_lawhood.runtime.study_issue import project_standard_study_extensions
from tests.experiment_entry_support import standard_authoring_for_draft
from tests.prospective_source_capture_fixture import SyntheticSourceInspector, synthetic_capture
from tests.test_matrix_factor_confirmation_default_integration import _resources as e1_resources
from tests.test_matrix_scheduled_calibration import (
    TEST_BUDGET, bank as bank, prospective_bank, provenance as provenance,
    response_bank as response_bank, scheduled as scheduled, stock as stock,
)


def _resources(compilation):
    """Reuse the stock finite envelope fixture with the scheduled native census."""
    from empirical_lawhood.runtime.execution_envelope import (
        ChildResourceTokenLimit, ProgressHeartbeat, ProgressLivenessContract,
    )
    from decimal import Decimal

    native = {operation.node_id for operation in compilation.draft.operations
        if operation.selection.capability_key.rsplit('.', 1)[-1] in ('prefix', 'continue', 'responses')}
    budgets = {operation.node_id: operation.resource_budget for operation in compilation.draft.operations}
    envelope = e1_resources(compilation, native_task_ids=native)
    # Each software task has an explicit acquisition token. This is not a
    # scientific independent-root count or an operational sizing recommendation.
    cells = tuple(replace(cell,
        resource_budget=replace(cell.resource_budget,
            cpu_cores=budgets[cell.task_id].cpu_cores,
            memory_bytes=budgets[cell.task_id].memory_bytes,
            output_bytes=budgets[cell.task_id].output_bytes,
            source_byte_limit=budgets[cell.task_id].source_scan_bytes),
        physical_independent_unit_id='unit.'+cell.task_id if cell.task_id in native else None,
        preparation_unit_id='preparation.'+cell.task_id if cell.task_id in native else None,
        physical_execution_cost=int(cell.task_id in native),
        retry_token_cost=int(cell.task_id in native),
        native_simulator_launch=cell.task_id in native,
        progress_liveness=ProgressLivenessContract('liveness.'+cell.task_id, ProgressHeartbeat.SCHEMA,
            'software-only-work', Decimal(10), True, True) if cell.task_id in native else None)
        for cell in envelope.task_cells)
    return replace(envelope, task_cells=cells,
        child_token_limits=(ChildResourceTokenLimit('child.software-e1', len(native), 0),))


def _application(response_bank, tmp_path, monkeypatch, *, compact=False, draft_bundle=None, formal_method_capability_key=None):
    plane = response_bank[0]
    if draft_bundle is not None:
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.compact_qualification import QUALIFY_KEY
        draft, qualifications, records, _ = draft_bundle
    elif compact:
        from tests.test_matrix_scheduled_compact_graph import compact_bank
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.compact_qualification import QUALIFY_KEY
        draft, qualifications, records, _ = compact_bank(response_bank, response=True)
    else:
        draft, qualifications, records, _ = prospective_bank(response_bank, response=True)
        QUALIFY_KEY = cb.QUALIFY_KEY
    payloads = {key: value if isinstance(value, bytes) else value.canonical_bytes() for key, value in records.items()}
    external_by_id = {value.input_id: value for value in draft.external_inputs}
    materials = []
    for index, source in enumerate(draft.prospective_draft.source_materializations):
        external = external_by_id[source.source_id]
        raw = payloads[external.logical_artifact_id]
        config = SourceMaterializationConfig('source-config.software-scheduled.'+str(index), source.source_id,
            source.role, sha256(raw).hexdigest(), len(raw), len(raw), external.payload_schema, external.media_type,
            SourceReadMode.ORDINARY_BOUNDED, external.outcome_access, external.visibility_ceiling)
        materials.append(replace(source, source_config_sha256=config.fingerprint()))
        payloads[config.fingerprint()] = config.canonical_bytes()
    root = draft.prospective_draft
    campaign = replace(root.campaign,
        budget=ResourceBudget.aggregate(operation.resource_budget for operation in draft.operations),
        authority_policy=ObjectIdentity.from_record(root.system.authority_policy.policy_id, root.system.authority_policy),
        nodes=tuple(replace(node, object_identity=ObjectIdentity.from_record(root.system.system_id, root.system))
            if node.object_identity.object_id == root.system.system_id else node for node in root.campaign.nodes))
    draft = replace(draft, campaign=campaign, prospective_draft=replace(root, campaign=campaign,
        source_materializations=tuple(sorted(materials, key=lambda value: value.source_id))))
    registrations, registry, codecs = operation_catalog()
    selected = {operation.selection.selection_id for operation in draft.operations}
    registry = replace(registry, capabilities=tuple(manifest for manifest in registry.capabilities
        if manifest.registry_id in selected))
    compilation = compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
        implementation_commit='d'*40, qualifications=qualifications,
        known_design_inputs=draft.prospective_draft.design_inputs, output_codecs=codecs)
    assert compilation.candidate_report.candidate is not None, compilation.candidate_report.diagnostics
    standard, formal = standard_authoring_for_draft(compilation.candidate_draft, compilation.candidate_context,
        formal_method_capability_key=formal_method_capability_key or QUALIFY_KEY)
    operands = tuple(sorted((RecursiveProspectiveOperand(external.logical_artifact_id,
        external.expected_content_sha256, len(payloads[external.logical_artifact_id]), external.payload_schema,
        external.media_type, external.outcome_access, external.visibility_ceiling)
        for external in draft.external_inputs), key=lambda value: value.logical_artifact_id))
    spec = RecursiveProspectiveAuthoringSpec('authoring.software-default-scheduled', draft, standard.entry_package,
        formal.formal_methods, formal.source_inventories, qualifications, compilation.candidate_context.known_design_inputs,
        _resources(compilation), operands)
    captured = synthetic_capture(spec.spec_id + '.source-closure',
        compilation.candidate_context.implementation_sha256, clean=False)
    manifest = replace(captured.manifest, implementation_commit='d'*40)
    closure = replace(captured.closure, implementation_commit='d'*40, exact_source_manifest=manifest.identity)
    captured = replace(captured, closure=closure, manifest=manifest,
        source=replace(captured.source, implementation_commit='d'*40))

    def selected_source(_project_root, closure_id):
        assert closure_id == captured.closure.source_closure_id
        return captured

    monkeypatch.setattr(author, 'capture_target_closure', selected_source)
    monkeypatch.setattr(author, 'GitStudySourceClosureInspector', SyntheticSourceInspector)
    compilation, executable, decoder, registrations = author._compile(spec, closure)
    publisher = ExternalCandidateInputPublisher(plane.root)
    for payload in (*payloads.values(), *(value.payload for value in compilation.config_inputs),
                    *(value.canonical_bytes() for value in qualifications)):
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
        path = preview/('input.'+sha256(key.encode()).hexdigest()+'.bin')
        path.write_bytes(raw)
        bindings.append((key, path))
    return dict(spec=spec, project_root=project, artifact_writer=plane, input_bindings=tuple(bindings)), compilation, plane


@pytest.fixture
def application(response_bank, tmp_path, monkeypatch):
    return _application(response_bank, tmp_path, monkeypatch, compact=True)


def _load(application, destination, monkeypatch):
    args, _, plane = application
    monkeypatch.setattr(author, 'resolve_authoring_directory', lambda directory, **kwargs: (Path(directory).resolve(), plane.root.contract))
    return author.load_recursive_prospective_handoff(directory=destination, root=args['project_root'],
        storage_profile=object(), artifact_writer=plane)


def test_default_scheduled_public_author_load_and_provider_remain_effect_free(application, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.compact_records import NAMESPACE
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history_segments

    def blocked(*args, **kwargs):
        pytest.fail('public author/load or provider proof entered numerical science')

    monkeypatch.setattr(np.random, 'Generator', blocked)
    monkeypatch.setattr(np.linalg, 'eigh', blocked)
    monkeypatch.setattr(parameter_history_segments, 'acquire_parameter_segment', blocked)
    args, _, plane = application
    factories = tuple(factory for factory in operation_factories() if factory.manifest.capability_key.startswith(NAMESPACE+'.'))
    assert len(factories) == 19
    destination = Path(plane.root.contract.canonical_path)/'default-scheduled-authoring'
    result = author.author_recursive_prospective(**args, output_dir=destination)
    assert result['task_count'] == 25 and result['native_contact'] == 'none'
    assert result['scientific_authority'] == 'NONE'
    handoff = _load(application, destination, monkeypatch)
    proof = author.prove_recursive_prospective_handoff(handoff)
    assert proof['task_count'] == 25 and proof['scientific_execution_performed'] is False
    assert {task.capability.requested_resources for task in handoff.projection.tasks} == {TEST_BUDGET}
    assert len(handoff.compilation.candidate_context.qualifications) == len(args['spec'].qualifications)


def test_original_full_scheduled_projection_preserves_operands_and_decoder_bound(response_bank):
    """The compact encoding preserves the complete original projection."""
    from empirical_lawhood.kernel.decoding import CanonicalizationError, decode_canonical_bytes

    draft, qualifications, _, _ = prospective_bank(response_bank, response=True)
    registrations, registry, codecs = operation_catalog()
    selected = {operation.selection.selection_id for operation in draft.operations}
    registry = replace(registry, capabilities=tuple(manifest for manifest in registry.capabilities
        if manifest.registry_id in selected))
    compilation = compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
        implementation_commit='d'*40, qualifications=qualifications,
        known_design_inputs=draft.prospective_draft.design_inputs, output_codecs=codecs)
    assert compilation.candidate_report.candidate is not None, compilation.candidate_report.diagnostics
    projection = compilation.selected_scientific_projection
    raw = projection.canonical_bytes()
    assert decode_canonical_bytes(raw, type(projection), maximum_bytes=author.MAXIMUM_SPEC_BYTES) == projection
    with pytest.raises(CanonicalizationError, match='exceeds its bounded contract'):
        decode_canonical_bytes(raw, type(projection), maximum_bytes=len(raw)-1)


@pytest.mark.parametrize('entry', ('author', 'load'))
def test_compact_public_entry_authenticates_original_shared_publication(application, monkeypatch, entry):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.compact_records import ScheduledCompactCommitmentConfig
    from empirical_lawhood.infrastructure.artifacts import ArtifactPlaneError

    args, compilation, plane = application
    config, = (value.record for value in compilation.config_inputs
        if type(value.record) is ScheduledCompactCommitmentConfig)
    destination = Path(plane.root.contract.canonical_path)/'compact-shared-original-authentication'
    if entry == 'load':
        author.author_recursive_prospective(**args, output_dir=destination)
    original = config.bank.reservation.publication
    path = plane.root.resolve(original.materialization.relative_path, for_write=True)
    path.write_bytes(path.read_bytes()+b'\n')
    with pytest.raises(ArtifactPlaneError):
        if entry == 'author':
            author.author_recursive_prospective(**args, output_dir=destination)
        else:
            _load(application, destination, monkeypatch)
    if entry == 'author':
        assert not destination.exists()
