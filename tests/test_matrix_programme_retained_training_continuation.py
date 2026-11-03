# SPDX-License-Identifier: MPL-2.0
"""Exposed source-lineage and custody controls; no completed TRAIN or authority."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_researcher_programme import retained_training_continuation as domain
from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammePublishedInput
from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import (
    MatrixContinuedProgrammeSpecification, MatrixProgrammePhaseBinding, MatrixResearchProgrammeSpecification,
    prepare,
)
from empirical_lawhood.api import matrix_programme_retained_training_continuation as owner
from empirical_lawhood.api.experiment_preparation import load_experiment_inputs
from empirical_lawhood.api.matrix_researcher_programme import _publish
from empirical_lawhood.api.recursive_authoring import implementation_binding
from empirical_lawhood.infrastructure.matrix_programme_inputs import authenticated_programme_inputs
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.test_matrix_programme_source_continuation import metadata_case  # noqa: F401

ROOT = Path(__file__).parents[1]


@pytest.fixture(scope='module')
def retained_case(metadata_case):  # noqa: F811
    from empirical_lawhood.adapters.methods.matrix_finite_dt_source_records import MatrixFiniteDtTrainingLocator
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import coordinate_identity
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
    from empirical_lawhood.runtime.native_training_export import NativeTrainingExportAdoptionSelection
    from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan
    from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave
    from empirical_lawhood.runtime.recovery import RunRecoveryTerminalEvent, DevelopmentRunRecoveryTerminalEvent
    case, original = metadata_case.case, metadata_case.original
    root = Path(case.writer.root.contract.canonical_path)
    original_commitment = load_experiment_inputs(case.specification, case.output_selection_path).method_inputs.input_commitments
    specification = decode_canonical_bytes((ROOT / 'programmes/foundations/emergent-structure/workflows/matrix-programme/specification.example.json').read_bytes(),
        MatrixResearchProgrammeSpecification, maximum_bytes=None)
    nominal, = (value for value in original.scientific_design.training_protocol.coordinates
        if coordinate_identity(value) == dict(original.scientific_design.e3.role_coordinates)['CALIBRATION'])
    e3 = specification.operations.e3
    e3 = replace(e3, computability_evidence=replace(e3.computability_evidence,
        numerical_view_ids=tuple(sorted((nominal.primary_view.view_id, nominal.fine_view.view_id)))))
    specification = replace(specification, directory='retained-original', input_commitments=original_commitment,
        operations=replace(specification.operations, e3=e3))
    plan = prepare(specification, execution=case.execution).programme
    predecessor = MatrixProgrammePublishedInput(plan.identity,
        _publish(case.writer, root / 'retained-original/matrix-programme.json', plan))
    request = domain.MatrixProgrammeRetainedTrainingContinuationSpecification('request.exposed-retained-training',
        predecessor, 'retained-target')
    # These literal pins are only untrusted software selections. No execution
    # report or adoption owner accepts them as completed scientific evidence.
    def pin(kind, name):
        return ObjectIdentity(name, kind.SCHEMA, kind.VERSION, 'a' * 64)
    locator = MatrixFiniteDtTrainingLocator('retained-original/children/train', 'run.exposed-retained-training',
        pin(AuthoredRecursiveWave, 'packet.exposed-training'), pin(DevelopmentExecutionPlan, 'plan.exposed-training'))
    banks = tuple(case.writer.write(ArtifactWriteRequest('exposed.bank.' + name,
        'exposed-bank-locators/' + name + '.json', locator.SCHEMA, ArtifactProfile.CANONICAL_JSON,
        'application/json', 'exposed.banks', 'exposed-bank-locators', locator.canonical_bytes(),
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
        for name in ('allocation', 'features', 'outcomes'))
    adoption = NativeTrainingExportAdoptionSelection('adoption.exposed-training', locator.authored_directory,
        locator.run_id, locator.packet, locator.execution_plan, implementation_binding(ROOT),
        original.scientific_design.e3.identity, original_commitment.record, 'export.exposed.train', banks)
    lineage = domain.MatrixRetainedTrainingSource('lineage.exposed-training', predecessor, original_commitment,
        locator, adoption, metadata_case.continued.producing_provenance.identity, request.identity)
    support = case.writer.write(ArtifactWriteRequest(lineage.record_id, 'retained-target/lineage.json', lineage.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', lineage.record_id, 'retained-target',
        lineage.canonical_bytes(), VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    def publish(key, record, *, identity=None):
        publication = _publish(case.writer, root / 'retained-target/inputs' / (key + '.json'), record)
        return MatrixProgrammePublishedInput(record.identity if identity is None else identity, publication)
    commitment = owner._publish_inputs(original, metadata_case.continued.producing_provenance,
        lineage, support, publish, record_id='commitments.exposed-retained-training')
    with authenticated_programme_inputs(writer=case.writer, commitment=commitment,
            maximum_source_bytes=case.request.metadata_budget.source_scan_bytes) as continued:
        domain.validate_retained_inputs(original, continued, lineage)
    target = MatrixContinuedProgrammeSpecification('specification.exposed-retained-training', request.directory,
        commitment, specification.operations, predecessor, request.identity)
    target_plan = prepare(target, execution=case.execution).programme
    bindings = tuple((phase, pin(MatrixProgrammePhaseBinding, 'binding.exposed.' + phase)) for phase in domain.RETAINED_PHASES)
    terminals = tuple((phase, pin(kind, 'terminal.exposed.' + phase)) for phase, kind in zip(domain.RETAINED_PHASES,
        (RunRecoveryTerminalEvent, DevelopmentRunRecoveryTerminalEvent, DevelopmentRunRecoveryTerminalEvent), strict=True))
    record = domain.MatrixProgrammeRetainedTrainingContinuation('continuation.exposed-training', request,
        target_plan, bindings, terminals, lineage)
    return SimpleNamespace(case=case, original=original, continued=continued, request=request, record=record,
        lineage=lineage, support=support, commitment=commitment, target=target, target_plan=target_plan)


def test_new_handoff_is_explicit_and_preserves_all_original_science(retained_case):
    value = retained_case
    for record in (value.request, value.lineage, value.record, value.target_plan):
        assert decode_canonical_bytes(record.canonical_bytes(), type(record), maximum_bytes=None) == record
    domain.validate_retained_inputs(value.original, value.continued, value.lineage)
    assert value.original.scientific_design.canonical_bytes() == value.continued.scientific_design.canonical_bytes()
    assert value.original.commitments.revision_folds == value.continued.commitments.revision_folds
    for before, after in zip(value.original.phases, value.continued.phases, strict=True):
        assert before.reservation.canonical_bytes() == after.reservation.canonical_bytes()
        assert before.native_specification == after.native_specification
    assert not domain.prepare(value.request, execution=value.case.execution).executable


def test_e3_projection_publishes_and_reopens_the_complete_handoff_handle(retained_case, monkeypatch):
    """Exercise actual input publication/binding; stop before untrusted TRAIN use."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_assembly import (
        ConfiguredProtectedE3AssemblySpecification,
    )
    from empirical_lawhood.api.matrix_programme_initial_phases import project_initial_phase
    from empirical_lawhood.api.matrix_programme_projection import MatrixProgrammeProjectionContext
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection

    value = retained_case
    plane = value.case.writer
    root = Path(plane.root.contract.canonical_path)
    directory = root / 'retained-e3-projection-seam'
    publication = _publish(plane, directory / domain.CONTINUATION_FILENAME, value.record)
    handle = MatrixProgrammePublishedInput(value.record.identity, replace(publication, created=False))
    observed = []

    class AssemblyBoundary(Exception):
        pass

    def derive_inputs(*, specification_path, source_selection_path, **_kwargs):
        specification = decode_canonical_bytes(specification_path.read_bytes(),
            ConfiguredProtectedE3AssemblySpecification, maximum_bytes=None)
        selector = decode_canonical_bytes(source_selection_path.read_bytes(),
            ExperimentFileInputSelection, maximum_bytes=None)
        selected, = (row for row in selector.bindings if row.key == 'retained-training-continuation')
        assert selected.identity == handle.identity
        assert selected.identity.object_schema == MatrixProgrammePublishedInput.SCHEMA
        assert selected.identity != handle.record
        inputs = load_experiment_inputs(specification, source_selection_path, artifact_writer=plane).method_inputs
        assert inputs.retained_training_continuation == handle
        assert inputs.retained_training_continuation.record == value.record.identity
        assert inputs.export_adoption == value.lineage.export_adoption
        assert inputs.request.native_training_locator == value.lineage.training_locator
        observed.append(inputs)
        raise AssemblyBoundary

    # The missing original TRAIN source/locator are disclosed software seams.
    # Publication and the installed binder are real; no acquisition is attempted.
    service = SimpleNamespace(artifact_writer=plane, derive_inputs=derive_inputs)
    train = SimpleNamespace(sources=SimpleNamespace(
        relative_path=value.case.output_selection_path.relative_to(root).as_posix()))
    context = MatrixProgrammeProjectionContext(service, value.target_plan, value.continued,
        directory, {'train': train}, {}, continuation_records=[value.record])
    monkeypatch.setattr(MatrixProgrammeProjectionContext, 'native_training_locator',
        lambda selected: value.lineage.training_locator if selected is context else None)
    with pytest.raises(AssemblyBoundary):
        project_initial_phase(context, 'e3')
    assert len(observed) == 1


@pytest.mark.parametrize('change', ('lineage-source', 'lineage-request', 'missing-train-terminal', 'namespace', 'folds', 'panel'))
def test_handoff_refuses_source_graph_and_science_substitution(retained_case, change):
    value = retained_case
    with pytest.raises((ValueError, PermissionError)):
        if change == 'lineage-source':
            lineage = replace(value.lineage, target_provenance=value.original.producing_provenance.identity)
            domain.validate_retained_inputs(value.original, value.continued, lineage)
        elif change == 'lineage-request':
            replace(value.record, retained_training=replace(value.lineage,
                continuation_request=replace(value.request.identity, object_id='request.changed')))
        elif change == 'missing-train-terminal':
            replace(value.record, predecessor_terminals=value.record.predecessor_terminals[:-1])
        else:
            continued = value.continued
            if change == 'namespace':
                continued = replace(continued, commitments=replace(continued.commitments, namespace='different'))
            elif change == 'folds':
                group, fold = continued.commitments.revision_folds[0]
                continued = replace(continued, commitments=replace(continued.commitments,
                    revision_folds=((group, fold + 1), *continued.commitments.revision_folds[1:])))
            else:
                continued = replace(continued, phases=tuple(replace(phase,
                    responses=value.original.phase(phase.role).responses) if phase.role == 'e3.calibration' else phase
                    for phase in continued.phases))
            domain.validate_retained_inputs(value.original, continued, value.lineage)


def test_original_and_lineage_bytes_remain_guarded_through_consumer(retained_case):
    value = retained_case
    path = value.case.writer.root.resolve(value.lineage.input_commitments.publication.materialization.relative_path,
        for_write=False)
    before = path.read_bytes()
    try:
        with pytest.raises((ValueError, PermissionError, RuntimeError)):
            with authenticated_programme_inputs(writer=value.case.writer, commitment=value.commitment,
                    maximum_source_bytes=value.case.request.metadata_budget.source_scan_bytes):
                path.write_bytes(bytes((before[0] ^ 1,)) + before[1:])
    finally:
        path.write_bytes(before)


@pytest.mark.parametrize('phase', ('e3', 'e4.development', 'e5.source', 'e6'))
def test_any_original_authored_future_or_binding_refuses(tmp_path, phase):
    context = SimpleNamespace(directory=tmp_path, bindings=dict.fromkeys(domain.RETAINED_PHASES), pending_bindings={},
        child_directory=lambda key: tmp_path / 'children' / key)
    child = context.child_directory(phase)
    child.mkdir(parents=True)
    with pytest.raises(PermissionError, match='authored later'):
        owner._require_future_unentered(context)


def test_failed_preparation_metadata_is_preserved_and_dangling_child_refuses(tmp_path):
    context = SimpleNamespace(directory=tmp_path, bindings=dict.fromkeys(domain.RETAINED_PHASES), pending_bindings={},
        child_directory=lambda key: tmp_path / 'children' / key)
    partial = tmp_path / 'derived/e3/retained-failure.json'
    partial.parent.mkdir(parents=True)
    partial.write_bytes(b'original failed preparation')
    owner._require_future_unentered(context)
    assert partial.read_bytes() == b'original failed preparation'
    child = context.child_directory('e3')
    child.parent.mkdir()
    child.symlink_to(tmp_path / 'missing-target', target_is_directory=True)
    with pytest.raises(PermissionError, match='authored later'):
        owner._require_future_unentered(context)


def test_new_plan_cannot_open_without_its_exact_handoff(retained_case, monkeypatch):
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
    from empirical_lawhood.api.matrix_researcher_programme import MatrixResearchProgrammeService
    value = retained_case
    service = MatrixResearchProgrammeService(service=ExperimentProgrammeService(ROOT, value.case.writer))
    for name in ('_project', '_author_phase', '_operate_phase'):
        monkeypatch.setattr(service, name, lambda *a, **kw: pytest.fail('missing handoff reached a child effect'))
    with pytest.raises(PermissionError, match='retained TRAIN continuation publication'):
        with service._context(value.target_plan):
            pytest.fail('new programme opened without its exact handoff')


def test_e3_future_source_rebinding_preserves_exact_original_reserves_and_panels(retained_case):
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_source_records import ProtectedE3NativeSourceManifest
    from empirical_lawhood.api.matrix_prepared_source_runtime import _future_source_selections
    value = retained_case
    inputs, commitments = value.original, value.original.commitments
    future = inputs.phase('e3.calibration')
    scalar = inputs.scientific_design.training_protocol.scalar_definition
    scalar_publication, = (row.publication for row in commitments.scalar_definitions
        if row.record == ObjectIdentity.from_record(scalar.definition_id, scalar))
    manifest = ProtectedE3NativeSourceManifest('manifest.exposed.retained-future', future.reservation,
        future.native_specification, (inputs.producing_provenance,), inputs.exposure_audit,
        commitments.exposure_audit.publication, commitments.phase('e3.calibration').reservation.publication,
        scalar, scalar_publication)
    request = SimpleNamespace(identity=value.lineage.export_adoption.request,
        input_commitments=value.lineage.input_commitments, future_manifest=manifest)
    context = SimpleNamespace(writer=value.case.writer, commitments=value.continued.commitments,
        inputs=value.continued, design=value.continued.scientific_design)
    args = dict(assembly_request=SimpleNamespace(native_training_locator=value.lineage.training_locator),
        training_request=request, scientific_protocol=context.design.training_protocol,
        candidate=context.design.e3, export_adoption=value.lineage.export_adoption)
    actual, selections, lineage = owner.continued_e3_future(context, **args)
    assert lineage == value.lineage
    assert actual.provenances == (value.continued.producing_provenance,)
    assert replace(actual, record_id=manifest.record_id, provenances=manifest.provenances) == manifest
    assert tuple(selections.items()) == _future_source_selections(value.continued)
    old = dict(_future_source_selections(value.original))
    for role, selection in selections.items():
        assert selection.panels == old[role].panels
        assert selection.template_publications == old[role].template_publications
        assert [row.public_source.root for row in selection.protocols] == [row.public_source.root for row in old[role].protocols]
    with pytest.raises(PermissionError, match='original TRAIN'):
        owner.continued_e3_future(context, **{**args, 'export_adoption': replace(value.lineage.export_adoption,
            record_id='adoption.substituted')})


def test_prepared_source_join_checks_original_c_and_exact_train_locator(retained_case, monkeypatch):
    """Only the request-body validation seam is disclosed; both C reads are real."""
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_publications
    from empirical_lawhood.api.matrix_prepared_source_runtime import _committed_e4_selections
    value, validated = retained_case, []
    request = SimpleNamespace(identity=value.lineage.export_adoption.request, input_commitments=value.lineage.input_commitments)
    monkeypatch.setattr(native_training_publications, 'validate_request_programme_inputs',
        lambda actual, original: validated.append((actual, original)))
    options = dict(maximum_source_bytes=value.case.request.metadata_budget.source_scan_bytes,
        native_training_locator=value.lineage.training_locator)
    with _committed_e4_selections(value.case.writer, value.commitment, request, **options) as current:
        assert current == value.continued
        assert validated[-1] == (request, value.original)
    for changed in (None, replace(value.lineage.training_locator, run_id='run.substituted')):
        with pytest.raises(PermissionError, match='retained TRAIN source lineage'):
            with _committed_e4_selections(value.case.writer, value.commitment, request,
                    **{**options, 'native_training_locator': changed}):
                pytest.fail('substituted TRAIN locator reached prepared source consumer')
