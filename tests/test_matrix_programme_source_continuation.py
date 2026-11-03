# SPDX-License-Identifier: MPL-2.0
"""Source-only metadata joins, never scientific acquisition or qualification."""
from dataclasses import replace
from decimal import localcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_researcher_programme import source_continuation as domain
from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammePublishedInput
from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import (
    MatrixContinuedProgrammeSpecification, MatrixResearchProgrammePlan, MatrixResearchProgrammeSpecification,
    prepare, programme_protocol,
)
from empirical_lawhood.api import matrix_programme_source_continuation as owner
from empirical_lawhood.api.matrix_researcher_programme import _publish
from empirical_lawhood.infrastructure.matrix_programme_inputs import authenticate_programme_inputs, _input_record_scope
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.api.experiment_preparation import load_experiment_inputs
from tests.test_matrix_programme_input_assembly import build_public_file_case, _derive, _inventory, _forbid_acquisition

ROOT = Path(__file__).parents[1]


@pytest.fixture(scope='module')
def metadata_case(tmp_path_factory):
    from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import MatrixFactorExposureCensus
    census = decode_canonical_bytes((ROOT / 'programmes/foundations/emergent-structure/workflows/matrix-response-experiment/exposure-census.example.json').read_bytes(),
        MatrixFactorExposureCensus, maximum_bytes=None)
    case = build_public_file_case(tmp_path_factory.mktemp('source-continuation-metadata'), census)
    result = _derive(case)
    rebound = load_experiment_inputs(case.specification, result.source_selection_path).method_inputs
    original = authenticate_programme_inputs(writer=case.writer,
        commitment=rebound.input_commitments,
        maximum_source_bytes=case.request.metadata_budget.source_scan_bytes)
    # This literal source identity exercises pure joins only. It never passes
    # current-source admission, creates a real continuation or executes work.
    provenance = replace(original.producing_provenance, observed_git_head='f' * 40)
    published = []
    def publish(key, record, *, identity=None):
        pin = record.identity if identity is None else identity
        publication = _publish(case.writer, Path(case.writer.root.contract.canonical_path) / 'disclosed-rebound' / (key + '.json'), record)
        published.append(publication)
        return MatrixProgrammePublishedInput(pin, publication)
    before = _inventory(case.directory)
    with pytest.MonkeyPatch.context() as patch:
        _forbid_acquisition(patch)
        commitment = owner._publish_inputs(original, provenance, publish, record_id='commitments.disclosed-rebound')
    assert _inventory(case.directory) == before
    continued = authenticate_programme_inputs(writer=case.writer, commitment=commitment,
        maximum_source_bytes=case.request.metadata_budget.source_scan_bytes)
    return SimpleNamespace(case=case, original=original, continued=continued, published=published, commitment=commitment)


def test_source_rebinding_keeps_all_original_d_allocations_native_settings_streams_and_support(metadata_case):
    original, continued = metadata_case.original, metadata_case.continued
    domain.validate_continued_inputs(original, continued)
    assert original.scientific_design.canonical_bytes() == continued.scientific_design.canonical_bytes()
    assert original.producing_provenance != continued.producing_provenance
    for previous, current in zip(original.phases, continued.phases, strict=True):
        assert previous.reservation.canonical_bytes() == current.reservation.canonical_bytes()
        assert previous.native_specification == current.native_specification
        if previous.responses is not None:
            assert previous.responses != current.responses
            assert [row.protocol_id for row in previous.responses.protocols] == [row.protocol_id for row in current.responses.protocols]
    assert original.commitments.support_files == continued.commitments.support_files


@pytest.mark.parametrize('field', ('namespace', 'revision_folds', 'e4_streams'))
def test_continuation_refuses_changes_outside_source_bindings(metadata_case, field):
    original, continued = metadata_case.original, metadata_case.continued
    value = getattr(continued.commitments, field)
    if field == 'namespace':
        changed = value + '.changed'
    elif field == 'revision_folds':
        changed = ((value[0][0], value[0][1] + 1), *value[1:])
    else:
        changed = replace(value, record_id=value.record_id + '.changed')
    with _input_record_scope(metadata_case.case.request.metadata_budget.source_scan_bytes):
        domain.validate_continued_inputs(original, continued)
        with pytest.raises((ValueError, PermissionError)):
            altered = replace(continued, commitments=replace(continued.commitments, **{field: changed}))
            domain.validate_continued_inputs(original, altered)


def test_response_panel_and_policy_substitutions_refuse(metadata_case):
    original, continued = metadata_case.original, metadata_case.continued
    with _input_record_scope(metadata_case.case.request.metadata_budget.source_scan_bytes):
        domain.validate_continued_inputs(original, continued)
        with pytest.raises(PermissionError, match='response panels'):
            phases = tuple(replace(value, responses=original.phase(value.role).responses)
                if value.role == 'train' else value for value in continued.phases)
            domain.validate_continued_inputs(original, replace(continued, phases=phases))
        with pytest.raises(PermissionError, match='E6 policy'):
            domain.validate_continued_inputs(original, replace(continued, e6_policy=original.e6_policy))


def _count_response_binds(monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseAssay
    calls, original = [], ScheduledResponseAssay.bind
    def counted(self, source, **kwargs):
        calls.append(source)
        return original(self, source, **kwargs)
    monkeypatch.setattr(ScheduledResponseAssay, 'bind', counted)
    _forbid_acquisition(monkeypatch)
    return calls


def test_nested_input_reads_construct_each_original_response_only_once(metadata_case, monkeypatch):
    phase = metadata_case.original.phase('train')
    provenance = metadata_case.continued.producing_provenance
    assay = metadata_case.original.scientific_design.training_assay
    calls = _count_response_binds(monkeypatch)
    bound = metadata_case.case.request.metadata_budget.source_scan_bytes
    with _input_record_scope(bound):
        first = domain.rebound_responses(phase, provenance, assay)
        with _input_record_scope(bound):
            # A fresh phase container and equal immutable provenance still
            # refer to the same authenticated original scientific operands.
            assert domain.rebound_responses(replace(phase), replace(provenance), assay) is first
        assert len(calls) == len(phase.responses.protocols)
        assert first.canonical_bytes() == metadata_case.continued.phase('train').responses.canonical_bytes()
    with _input_record_scope(bound):
        assert domain.rebound_responses(phase, provenance, assay) == first
    assert len(calls) == 2 * len(phase.responses.protocols)


@pytest.mark.parametrize('changed', ('source', 'assay', 'responses', 'decimal'))
def test_rebinding_reuse_tracks_every_scientific_operand(metadata_case, monkeypatch, changed):
    phase = metadata_case.original.phase('train')
    provenance = metadata_case.continued.producing_provenance
    assay = metadata_case.original.scientific_design.training_assay
    calls = _count_response_binds(monkeypatch)
    with _input_record_scope(metadata_case.case.request.metadata_budget.source_scan_bytes):
        first = domain.rebound_responses(phase, provenance, assay)
        count = len(calls)
        if changed == 'assay':
            changed_assay = replace(assay, hessian_difference_step=assay.hessian_difference_step * 2)
            with pytest.raises(PermissionError, match='response mathematics'):
                domain.rebound_responses(phase, provenance, changed_assay)
        elif changed == 'source':
            result = domain.rebound_responses(phase, replace(provenance, observed_git_head='e' * 40), assay)
            assert result != first
        elif changed == 'responses':
            changed_phase = replace(phase, responses=replace(phase.responses,
                selection_id=phase.responses.selection_id + '.changed'))
            result = domain.rebound_responses(changed_phase, provenance, assay)
            assert result.selection_id == changed_phase.responses.selection_id
            assert result != first
        else:
            with localcontext() as context:
                context.prec += 1
                assert domain.rebound_responses(phase, provenance, assay) == first
        assert len(calls) > count


def test_too_small_rebinding_budget_keeps_exact_uncached_behavior(metadata_case, monkeypatch):
    phase = metadata_case.original.phase('train')
    provenance = metadata_case.continued.producing_provenance
    assay = metadata_case.original.scientific_design.training_assay
    calls = _count_response_binds(monkeypatch)
    with _input_record_scope(1):
        first = domain.rebound_responses(phase, provenance, assay)
        second = domain.rebound_responses(phase, provenance, assay)
    assert first is not second
    assert first.canonical_bytes() == second.canonical_bytes()
    assert len(calls) == 2 * len(phase.responses.protocols)


def _plans(metadata_case):
    case = metadata_case.case
    specification = decode_canonical_bytes((ROOT / 'programmes/foundations/emergent-structure/workflows/matrix-programme/specification.example.json').read_bytes(),
        MatrixResearchProgrammeSpecification, maximum_bytes=None)
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import coordinate_identity
    design = metadata_case.original.scientific_design
    nominal, = (coordinate for coordinate in design.training_protocol.coordinates
        if coordinate_identity(coordinate) == dict(design.e3.role_coordinates)['CALIBRATION'])
    e3 = specification.operations.e3
    e3 = replace(e3, computability_evidence=replace(e3.computability_evidence,
        numerical_view_ids=tuple(sorted((nominal.primary_view.view_id, nominal.fine_view.view_id)))))
    specification = replace(specification, operations=replace(specification.operations, e3=e3))
    original = prepare(replace(specification, directory='original-programme'), execution=case.execution).programme
    publication = _publish(case.writer, Path(case.writer.root.contract.canonical_path) / 'original-programme/matrix-programme.json', original)
    predecessor = MatrixProgrammePublishedInput(original.identity, publication)
    request = domain.MatrixProgrammeSourceContinuationSpecification('request.disclosed-continuation', predecessor, 'continued-programme')
    target = MatrixContinuedProgrammeSpecification('specification.disclosed-continuation', request.directory,
        metadata_case.commitment, specification.operations, predecessor, request.identity)
    continued = prepare(target, execution=case.execution).programme
    return original, request, continued


def test_original_and_continued_plans_decode_with_required_distinct_lineage(metadata_case):
    original, request, continued = _plans(metadata_case)
    for record in (original, continued):
        assert decode_canonical_bytes(record.canonical_bytes(), MatrixResearchProgrammePlan, maximum_bytes=None) == record
    assert type(continued.specification) is MatrixContinuedProgrammeSpecification
    assert programme_protocol(continued.specification) == 'matrix.researcher-programme.continued.v1'
    assert type(original.specification) is MatrixResearchProgrammeSpecification
    document = continued.specification.to_document()
    del document['value']['continuation_request']
    from empirical_lawhood.kernel.serialization import canonical_json_document_bytes
    with pytest.raises(ValueError):
        decode_canonical_bytes(canonical_json_document_bytes(document), MatrixContinuedProgrammeSpecification, maximum_bytes=None)
    assert not domain.prepare(request, execution=metadata_case.case.execution).executable


def test_missing_required_handoff_refuses_before_any_child_projection(metadata_case, monkeypatch):
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
    from empirical_lawhood.api.matrix_researcher_programme import MatrixResearchProgrammeService
    _, _, plan = _plans(metadata_case)
    service = MatrixResearchProgrammeService(service=ExperimentProgrammeService(ROOT, metadata_case.case.writer))
    for name in ('_project', '_author_phase', '_operate_phase'):
        monkeypatch.setattr(service, name, lambda *args, **kwargs: pytest.fail('missing handoff reached a child effect'))
    with pytest.raises(PermissionError, match='exact original source-continuation publication'):
        with service._context(plan):
            pytest.fail('continued programme opened without its required original custody')


@pytest.mark.parametrize('selected', ('original', 'original/child', 'original/child/grandchild'))
def test_continuation_never_uses_original_or_nested_home(selected):
    with pytest.raises(ValueError, match='disjoint'):
        domain.require_separate_home('original', selected)
    with pytest.raises(ValueError, match='disjoint'):
        domain.require_separate_home(selected, 'original')


@pytest.mark.parametrize('phase', ('e3', 'e4.development', 'e5.source', 'e6'))
def test_any_original_later_namespace_refuses_source_continuation(tmp_path, phase):
    context = SimpleNamespace(bindings={key: object() for key in ('e1', 'e2', 'train')}, pending_bindings={},
        child_directory=lambda key: tmp_path / 'children' / key,
        metadata_directory=lambda key: tmp_path / 'derived' / key)
    context.metadata_directory(phase).mkdir(parents=True)
    with pytest.raises(PermissionError, match='dependent phase namespace'):
        owner._unentered_future(context)


def test_partial_binding_cannot_be_treated_as_unentered_future():
    context = SimpleNamespace(bindings={key: object() for key in ('e1', 'e2', 'train')},
        pending_bindings={'e3': 'uncommitted original publication'})
    with pytest.raises(PermissionError, match='no later phase binding'):
        owner._unentered_future(context)


def test_completed_source_handoff_retains_all_original_phase_and_terminal_contracts(metadata_case):
    from empirical_lawhood.api.matrix_programme_completed_continuation import read_source_continuation
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import MatrixProgrammePhaseBinding
    from empirical_lawhood.runtime.recovery import RunRecoveryTerminalEvent, DevelopmentRunRecoveryTerminalEvent
    from empirical_lawhood.runtime.retained_e3_repair import RetainedE3ContinuedRepairTerminalEvent
    _, request, target = _plans(metadata_case)
    bindings = tuple((phase, ObjectIdentity('binding.disclosed.' + phase, MatrixProgrammePhaseBinding.SCHEMA,
        MatrixProgrammePhaseBinding.VERSION, 'a' * 64)) for phase in domain.COMPLETED_PHASES)
    kinds = (RunRecoveryTerminalEvent, DevelopmentRunRecoveryTerminalEvent,
        DevelopmentRunRecoveryTerminalEvent, RetainedE3ContinuedRepairTerminalEvent)
    terminals = tuple((phase, ObjectIdentity('terminal.disclosed.' + phase, kind.SCHEMA, kind.VERSION, 'b' * 64))
        for phase, kind in zip(domain.COMPLETED_PHASES, kinds, strict=True))
    record = domain.MatrixProgrammeCompletedSourceContinuation('continuation.disclosed-completed', request,
        target, bindings, terminals)
    writer = metadata_case.case.writer
    relative = 'disclosed-completed/source-continuation.json'
    _publish(writer, Path(writer.root.contract.canonical_path) / relative, record)
    assert read_source_continuation(writer, relative, 64 * 1024**2) == record
    assert decode_canonical_bytes(record.canonical_bytes(), type(record), maximum_bytes=None) == record
    with pytest.raises(ValueError, match='complete E1/E2/TRAIN/E3'):
        replace(record, predecessor_bindings=bindings[:-1])
    with pytest.raises(ValueError, match='terminal contract'):
        replace(record, predecessor_terminals=(*terminals[:-1], ('e3', bindings[-1][1])))


@pytest.mark.parametrize('phase', ('e4.development', 'e4.calibration', 'e5.development', 'e6'))
@pytest.mark.parametrize('kind', ('metadata', 'child', 'binding', 'dangling'))
def test_completed_source_handoff_refuses_every_started_successor(tmp_path, phase, kind):
    from empirical_lawhood.api.matrix_programme_completed_continuation import require_unentered_successors
    context = SimpleNamespace(directory=tmp_path, bindings=dict.fromkeys(domain.COMPLETED_PHASES),
        pending_bindings={}, child_directory=lambda phase: tmp_path / 'children' / phase,
        metadata_directory=lambda phase: tmp_path / 'derived' / phase)
    require_unentered_successors(context)
    path = (context.metadata_directory(phase) if kind == 'metadata' else context.child_directory(phase)
        if kind == 'child' else tmp_path / 'bindings' / (phase + '.json'))
    path.parent.mkdir(parents=True, exist_ok=True)
    if kind == 'dangling':
        path.symlink_to(tmp_path / 'absent')
    else:
        path.mkdir()
    with pytest.raises(PermissionError, match='entered or authored successor'):
        require_unentered_successors(context)
