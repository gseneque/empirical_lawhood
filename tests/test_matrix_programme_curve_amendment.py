# SPDX-License-Identifier: MPL-2.0
"""Prospective amendment controls; every operand here is exposed software data."""
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_researcher_programme import curve_amendment as domain
from empirical_lawhood.adapters.methods.matrix_researcher_programme.curve_amendment_design import (
    CURVE_MECHANISM_AMENDMENT, amend_curve_design,
)
from empirical_lawhood.adapters.methods.matrix_researcher_programme.scientific_design import MatrixProgrammeScientificDesign
from empirical_lawhood.api.matrix_amendment_evidence import evidence_snapshots, validate_evidence
from empirical_lawhood.api.matrix_amendment_withdrawals import _future_absences
from empirical_lawhood.kernel.decoding import decode_canonical_bytes

ROOT = Path(__file__).parents[1]


def predecessor_design():
    return decode_canonical_bytes((ROOT / 'tests/fixtures/matrix-programme-paired58-k-predecessor.json').read_bytes(),
        MatrixProgrammeScientificDesign, maximum_bytes=None)


def test_fixed_amendment_changes_only_authorized_future_claim_and_shared_features():
    original = predecessor_design()
    current = amend_curve_design(original, record_id='design.disclosed-curve-amendment')
    assert current.e3.is_curve_primary and current.e4_revision.matched_selection.is_curve_primary
    assert current.e4_nomination.is_curve_primary and current.e6.criterion.is_curve_primary
    assert current.e3.measurement == original.e3.measurement
    assert current.e3.populations == original.e3.populations
    for field in ('e1_criterion', 'e2', 'training_protocol', 'training_assay', 'e3_calibration_criterion',
            'e4_development', 'e4_calibration', 'e4_confirmation', 'e4_calibration_criterion',
            'e4_preparation_coordinates', 'e4_factorial', 'prepared_assay', 'panel_choices', 'recipe_interpretations'):
        before, after = getattr(original, field), getattr(current, field)
        assert before == after
        if hasattr(before, 'canonical_bytes'):
            assert before.canonical_bytes() == after.canonical_bytes()
    assert current.e5_development.arms == original.e5_development.arms
    assert current.e3.calibration_alpha == original.e3.calibration_alpha
    assert current.e3.assessment.comparison_ids == original.e3.assessment.comparison_ids
    assert current.e3.assessment.alpha == original.e3.assessment.alpha
    assert decode_canonical_bytes(current.canonical_bytes(), type(current), maximum_bytes=None) == current
    assert decode_canonical_bytes(CURVE_MECHANISM_AMENDMENT.canonical_bytes(), type(CURVE_MECHANISM_AMENDMENT),
        maximum_bytes=None) == CURVE_MECHANISM_AMENDMENT
    with pytest.raises(ValueError, match='exactly once'):
        amend_curve_design(current, record_id='design.second-amendment')
    with pytest.raises(ValueError, match='selected version'):
        replace(CURVE_MECHANISM_AMENDMENT, median_K='CHOOSE_FROM_CONFIRMATION')


@pytest.fixture
def evidence_case(tmp_path):
    roots = tuple('root.exposed-software.' + str(index).zfill(3) for index in range(96))
    protocols = {root: {'path': '/disclosed/' + root + '.json', 'sha256': 'a' * 64} for root in roots}
    exposure = SimpleNamespace(exposed_roots=(('e2', roots),), e2_protocols=tuple(
        (root, SimpleNamespace(object_fingerprint='a' * 64)) for root in roots))
    provenance = SimpleNamespace(observed_git_head='c' * 40)
    selections, prior = [], {}
    for analysis in domain.ANALYSES:
        home = tmp_path / analysis
        home.mkdir()
        first = analysis == domain.ANALYSES[0]
        spec_name = 'analysis-specification.json' if first else 'followup-specification.json'
        spec = dict(root_ids=roots, protocols=protocols, new_native_acquisitions=0)
        spec.update(dict(producing_commit=provenance.observed_git_head) if first else
            dict(root_denominator=96, prior_pins=prior))
        (home / spec_name).write_text(json.dumps(spec))
        (home / 'report.md').write_text('Exposed software report. No qualification.\n')
        members = [dict(path=name, sha256=sha256((home / name).read_bytes()).hexdigest(),
            **{('size_bytes' if first else 'bytes'): (home / name).stat().st_size}) for name in (spec_name, 'report.md')]
        manifest = {('files' if first else 'members'): members}
        (home / 'artifacts-manifest.json').write_text(json.dumps(manifest))
        manifest_sha = sha256((home / 'artifacts-manifest.json').read_bytes()).hexdigest()
        completion = (dict(status='COMPLETED_ALL_AVAILABLE_REQUIRED_STAGES', root_count=96, view_count=192,
            original_endpoints_unchanged=True, artifact_manifest_sha256=manifest_sha) if first else
            dict(status='COMPLETE_ALL_96_ROOTS_BOTH_VIEWS', original_scientific_disposition='UNCHANGED',
                manifest_sha256=manifest_sha, report_sha256=members[1]['sha256']))
        completion['new_native_acquisitions'] = 0
        (home / 'analysis-completion.json').write_text(json.dumps(completion))
        names = ('analysis-completion.json', 'artifacts-manifest.json', 'report.md', spec_name)
        files = tuple((member, domain.MatrixAmendmentEvidenceFile(str(home / name),
            sha256((home / name).read_bytes()).hexdigest(), (home / name).stat().st_size))
            for member, name in zip(domain.EVIDENCE_MEMBERS, names, strict=True))
        selections.append(domain.MatrixAmendmentAnalysisSelection(analysis, files))
        if first:
            prior = {Path(value.path).name: value.sha256 for name, value in files if name != 'report'}
    request = SimpleNamespace(specification_id='amendment.disclosed-software',
        analyses=tuple(selections), fingerprint=lambda: 'disclosed-software')
    return SimpleNamespace(request=request, exposure=exposure, provenance=provenance,
        snapshots=evidence_snapshots(request))


def test_exposed_analysis_snapshots_keep_exact_bytes_and_complete_original_protocols(evidence_case):
    case = evidence_case
    validate_evidence(case.request, case.snapshots, case.exposure, case.provenance)
    for snapshot in case.snapshots:
        assert snapshot.utf8_text.encode() == Path(snapshot.original.path).read_bytes()
        assert decode_canonical_bytes(snapshot.canonical_bytes(), type(snapshot), maximum_bytes=None) == snapshot
    changed = SimpleNamespace(observed_git_head='d' * 40)
    with pytest.raises(PermissionError, match='source or scientific standing'):
        validate_evidence(case.request, case.snapshots, case.exposure, changed)
    with pytest.raises(PermissionError, match='complete exact exposed evidence census'):
        validate_evidence(case.request, case.snapshots[:-1], case.exposure, case.provenance)
    foreign = SimpleNamespace(exposed_roots=case.exposure.exposed_roots, e2_protocols=tuple(
        (root, SimpleNamespace(object_fingerprint='b' * 64)) for root, _ in case.exposure.e2_protocols))
    with pytest.raises(PermissionError, match='original E2 root/protocol'):
        validate_evidence(case.request, case.snapshots, foreign, case.provenance)


def test_changed_original_analysis_file_refuses_before_publication(evidence_case):
    path = Path(evidence_case.snapshots[0].original.path)
    path.write_bytes(path.read_bytes().replace(b'96', b'95'))
    with pytest.raises(PermissionError, match='selected original bytes'):
        evidence_snapshots(evidence_case.request)


def test_complete_exposed_evidence_publishes_and_reopens_through_real_custody(evidence_case, tmp_path):
    from empirical_lawhood.api.matrix_amendment_evidence import publish_evidence, read_evidence
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from tests.test_artifact_publication_admission import _plane
    case = evidence_case
    writer = _plane(tmp_path / 'publication')
    admitted = []
    directory = Path(writer.root.contract.canonical_path) / 'programme/amendment-inputs'
    publications = publish_evidence(writer, case.request, case.snapshots, directory, admit_output=admitted.append)
    assert len(publications) == len(admitted) == 8
    assert admitted == [snapshot.canonical_bytes() for snapshot in case.snapshots]
    assert len({row.publication.materialization.relative_path for row in publications}) == 8
    assert all((row.publication.logical.outcome_access, row.publication.logical.visibility_ceiling) == (
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY) for row in publications)
    record = SimpleNamespace(specification=case.request, exposure=case.exposure, evidence=publications)
    with writer.read_context() as current:
        assert read_evidence(current, record, case.provenance) == case.snapshots
        current.require_verification_snapshot()
    repeated = publish_evidence(writer, case.request, case.snapshots, directory, admit_output=lambda _: None)
    assert repeated == tuple(replace(row, publication=replace(row.publication, created=False)) for row in publications)


@pytest.mark.parametrize('relative', ('children/e3', 'derived/e6', 'bindings/e5.source.json', 'runs', 'children/train'))
def test_superseded_derivation_partial_future_namespaces_refuse(tmp_path, relative):
    context = SimpleNamespace(directory=tmp_path, bindings={}, pending_bindings={},
        child_directory=lambda phase: tmp_path / 'children' / phase,
        metadata_directory=lambda phase: tmp_path / 'derived' / phase)
    _future_absences(context, authored=False, run_id=None)
    (tmp_path / relative).mkdir(parents=True)
    with pytest.raises(PermissionError, match='superseded future execution or partial custody'):
        _future_absences(context, authored=False, run_id=None)


@pytest.fixture(scope='module')
def amended_metadata(tmp_path_factory):
    from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import MatrixFactorExposureCensus
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammePublishedInput
    from empirical_lawhood.api import matrix_programme_curve_amendment as owner
    from empirical_lawhood.api.matrix_researcher_programme import _publish
    from empirical_lawhood.api.experiment_preparation import load_experiment_inputs
    from empirical_lawhood.infrastructure.matrix_programme_inputs import authenticate_programme_inputs
    from tests.test_matrix_programme_input_assembly import build_public_file_case, _derive, _forbid_acquisition
    census = decode_canonical_bytes((ROOT / 'programmes/foundations/emergent-structure/workflows/matrix-response-experiment/exposure-census.example.json').read_bytes(),
        MatrixFactorExposureCensus, maximum_bytes=None)
    with pytest.MonkeyPatch.context() as patch:
        _forbid_acquisition(patch)
        case = build_public_file_case(tmp_path_factory.mktemp('curve-amendment-metadata'), census, design=predecessor_design())
        result = _derive(case)
        inputs = load_experiment_inputs(case.specification, result.source_selection_path).method_inputs
        original = authenticate_programme_inputs(writer=case.writer, commitment=inputs.input_commitments,
            maximum_source_bytes=case.request.metadata_budget.source_scan_bytes)
        # Literal source identity exercises pure source/claim joins only. It is
        # never admitted for native work or used as fresh scientific evidence.
        provenance = replace(original.producing_provenance, observed_git_head='f' * 40)
        def publish(key, record, *, identity=None):
            pin = record.identity if identity is None else identity
            publication = _publish(case.writer, Path(case.writer.root.contract.canonical_path) / 'disclosed-amendment' / (key + '.json'), record)
            return MatrixProgrammePublishedInput(pin, publication)
        commitment = owner._publish_inputs(original, provenance, publish, record_id='commitments.disclosed-amendment')
        amended = authenticate_programme_inputs(writer=case.writer, commitment=commitment,
            maximum_source_bytes=case.request.metadata_budget.source_scan_bytes)
    return SimpleNamespace(case=case, original=original, amended=amended, commitment=commitment)


def test_amended_full_roster_c_reopens_without_allocating_or_changing_native_selections(amended_metadata):
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.source_continuation import validate_continued_inputs
    original, amended = amended_metadata.original, amended_metadata.amended
    domain.validate_amended_inputs(original, amended)
    assert sum(dict(amended.scientific_design.phase_group_counts).values()) == 980
    for before, after in zip(original.phases, amended.phases, strict=True):
        assert before.reservation.canonical_bytes() == after.reservation.canonical_bytes()
        assert before.native_specification == after.native_specification
    assert amended.commitments.revision_folds == original.commitments.revision_folds
    assert amended.commitments.e4_streams == original.commitments.e4_streams
    assert amended.commitments.exposure_census == original.commitments.exposure_census
    with pytest.raises(PermissionError, match='original D'):
        validate_continued_inputs(original, amended)
    bindings = {role: SimpleNamespace(specification=SimpleNamespace(identity=original.scientific_design.identity))
        for role in domain.RETAINED_PHASES}
    exposure = domain.amendment_exposure(original, bindings)
    assert tuple((role, len(roots)) for role, roots in exposure.exposed_roots) == (('e1', 384), ('e2', 96))
    assert len(exposure.e2_protocols) == 96 and len(exposure.dependent_reservations) == 10


@pytest.mark.parametrize('field', ('namespace', 'revision_folds', 'e4_streams'))
def test_amendment_refuses_changes_outside_fixed_prospective_rule(amended_metadata, field):
    original, current = amended_metadata.original, amended_metadata.amended
    value = getattr(current.commitments, field)
    changed = value + '.changed' if field == 'namespace' else (
        ((value[0][0], value[0][1] + 1), *value[1:]) if field == 'revision_folds' else
        replace(value, record_id=value.record_id + '.changed'))
    with pytest.raises((ValueError, PermissionError)):
        domain.validate_amended_inputs(original, replace(current, commitments=replace(current.commitments, **{field: changed})))


def test_amended_plan_requires_selected_lineage_before_any_child_effect(amended_metadata, evidence_case, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import (
        AMENDED_PROTOCOL_ID, MatrixCurveAmendedProgrammeSpecification, MatrixResearchProgrammePlan, prepare, programme_protocol,
    )
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
    from empirical_lawhood.api.matrix_researcher_programme import MatrixResearchProgrammeService
    from tests.test_matrix_programme_source_continuation import _plans
    _, predecessor_request, previous = _plans(amended_metadata)
    request = domain.MatrixProgrammeCurveAmendmentSpecification('request.disclosed-curve-amendment',
        predecessor_request.predecessor, 'curve-amended-programme', CURVE_MECHANISM_AMENDMENT,
        evidence_case.request.analyses, ())
    # _plans has already aligned the example operations to this disclosed
    # metadata coordinate's numerical-view identities.
    operations = previous.specification.operations
    target = MatrixCurveAmendedProgrammeSpecification('specification.disclosed-curve-amendment', request.directory,
        amended_metadata.commitment, operations, request.predecessor, request.identity)
    plan = prepare(target, execution=amended_metadata.case.execution).programme
    assert programme_protocol(target) == AMENDED_PROTOCOL_ID
    assert decode_canonical_bytes(plan.canonical_bytes(), MatrixResearchProgrammePlan, maximum_bytes=None) == plan
    assert not domain.prepare(request, execution=amended_metadata.case.execution).executable
    service = MatrixResearchProgrammeService(service=ExperimentProgrammeService(ROOT, amended_metadata.case.writer))
    for name in ('_project', '_author_phase', '_operate_phase'):
        monkeypatch.setattr(service, name, lambda *args, **kwargs: pytest.fail('missing amendment reached child effect'))
    with pytest.raises(PermissionError, match='exact prospective curve-amendment publication'):
        with service._context(plan):
            pytest.fail('amended programme opened without its required lineage')
