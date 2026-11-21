# SPDX-License-Identifier: MPL-2.0
"""M50 display and exact-record controls; no native execution or qualification."""

from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
import json
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import application_exploration as explorer
from empirical_lawhood.api.application_exploration_contracts import validate_exploration
from empirical_lawhood.api.application_presentations import PresentationData
from empirical_lawhood.api.domain_composition.rubisco_response import preparation_presentation as presentation
from empirical_lawhood.domains.rubisco.rubisco_response.formation_coordinate import prepare_formation_coordinate
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_records import InitialRootScopedAssessment
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import prepare_response_design, response_effects
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_assessment_records import LABELS, PreparationResponseAssessment, PreparationResponseCoverage, PreparationResponseFinding, PreparationResponseQuantity
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from tests import test_application_exploration as exploration_control
from tests import test_rubisco_active_preparation as preparation_control

selected = exploration_control.selected
matched = preparation_control.matched
fixture = preparation_control.fixture
prefix = preparation_control.prefix


@pytest.fixture
def design(prefix):
    coordinates = tuple((name, prepare_formation_coordinate(representation=row[0], prepared=row[2],
        site_id=prefix.config.prefix.conditional.state_census[0][0]))
        for name, row in zip(('m1-i95m', 'm1-wt'), prefix.models[:2], strict=True))
    return prepare_response_design(prefix=prefix.config.prefix,
        root_assessment=ObjectIdentity('assessment.exposed.original-root', InitialRootScopedAssessment.SCHEMA,
            InitialRootScopedAssessment.VERSION, '8' * 64), formation_coordinates=coordinates)


def display_control(design):
    """Typed exposed display operands, never substitutes for an owning assessment."""
    quantity = PreparationResponseQuantity('exposed.signed-error', 'I95M-minus-WT', 'later',
        Decimal('-0.10000000000000000001'), 'hartree/bohr')
    questions = tuple(PreparationResponseFinding('Q' + str(i), label,
        'EXPOSED_ADVERSE' if i == 5 else 'UNAVAILABLE', (quantity,) if i == 5 else (),
        n, 1 if i == 5 else 0, (design.identity,), 'Exposed display control; no molecular finding.')
        for i, (label, n) in enumerate(zip(LABELS, (6, 4, 2, 4, 2, 2), strict=True), 1))
    coverage = tuple(PreparationResponseCoverage(effect.identity, stage,
        'NOT_SELECTED' if stage == 'additional-refinement' else 'NOT_ENTERED', None, None)
        for stage in ('diagnostic', 'challenge', 'additional-refinement') for effect in response_effects(design, stage))
    assessment = PreparationResponseAssessment('assessment.exposed.display', design, design.root_assessment,
        coverage, (), (quantity,), questions, 'EXPOSED_DISPLAY_ONLY')
    summary = dict(scientific_completion='EXPOSED_ASSESSMENT_DISPLAY', execution_status='SUCCEEDED',
        question_count=6, assigned_tasks=1, qualification='NOT_ESTABLISHED', independent_biological_units=0,
        nested_state_positions=4, original_material_count=4, original_site_count=32, original_starting_hypotheses=384)
    rows = presentation.question_rows(assessment)
    view = presentation.exploration(design=design, question='Exposed local preparation display', summary=summary,
        findings=[q.to_document() for q in questions], questions=rows, coverage={'effects': [r.to_document() for r in coverage]},
        assessment=assessment)
    return assessment, view


def test_all_question_records_open_at_their_own_identity_and_recheck_current_access(design, selected):
    assessment, view = display_control(design)
    validate_exploration(view)
    _, box, entry, _ = selected
    identity = design.identity.to_document()
    entry['value']['identity'] = identity
    box['data'] = PresentationData(identity, presentation.SCOPE, view['summary'], tuple(view['question_readouts']),
        assessment.to_document(), {'design': identity}, 'Disclosed display control.', view)
    for question, node in zip(assessment.questions, view['nodes'][1:], strict=True):
        result = exploration_control.call(selected, 'exploration.record', record_id=node['id'])
        assert result.succeeded, result.errors
        assert result.payload['canonical_text'].encode() == question.canonical_bytes()
        assert result.payload['sha256'] == question.fingerprint()
        assert node['source'] != assessment.identity.to_document()
    assert box['reads'] == box['checks'] == 6
    box['refuse'] = True
    assert exploration_control.call(selected, 'exploration.record', record_id=view['nodes'][1]['id']).reason_codes == ('CURRENT_CUSTODY_REFUSED',)
    changed = deepcopy(view)
    changed['nodes'][1]['record']['value']['consequence'] = 'Changed after projection'
    with pytest.raises(PermissionError, match='original identity'):
        explorer._record({'exploration': changed, 'identity': identity, 'scope': presentation.SCOPE}, changed['nodes'][1]['id'])


def test_current_declared_method_sources_are_inspectable_without_native_entry(design, selected):
    _, view = display_control(design)
    _, box, _, _ = selected
    box['data'] = replace(box['data'], exploration=view)
    for method in view['methods']:
        for source in method['sources']:
            result = exploration_control.call(selected, 'exploration.method', method_id=method['id'], source_path=source['path'])
            assert result.succeeded, result.errors
            assert result.payload['source_scope'] == 'CURRENT_SELECTED_READER_IMPLEMENTATION'


def test_pending_and_adverse_projection_preserve_all_denominators_and_exact_signed_values(design, tmp_path):
    assessment, view = display_control(design)
    pending = presentation.pending_questions(design, 'UNENTERED')
    pending_view = presentation.exploration(design=design, question='Exposed unentered preparation',
        summary=dict(view['summary'], scientific_completion='ORIGINAL_PUBLICATION_INCOMPLETE', execution_status='UNENTERED'),
        findings=[], questions=pending, coverage={})
    for candidate in (view, pending_view):
        validate_exploration(candidate)
        assert [r['question_id'] for r in candidate['question_readouts']] == [f'Q{i}' for i in range(1, 7)]
        for row in candidate['question_readouts']:
            assert tuple(row['denominator'][key] for key in ('nested_state_positions', 'independent_biological_replicates',
                'original_material_count', 'original_site_count', 'original_starting_hypotheses')) == (4, 0, 4, 32, 384)
    assert view['question_readouts'][4]['quantity'][0]['value'] == '-0.10000000000000000001'
    assert all(row['assessment_state'] == 'NOT_YET_ASSESSED' and row['quantity'] == [] for row in pending)
    controls = dict(scope='EXPOSED_PRESENTATION_CONTROLS_ONLY', new_native_calls=0,
        unentered=pending_view, assessed=view, assessment_identity=assessment.identity.to_document())
    (tmp_path / 'presentation-controls.json').write_text(json.dumps(controls, indent=2) + '\n')


@pytest.mark.parametrize('state,expected', (('ENTRY_NOT_OBSERVED', 2), ('PARENT_CONTACT_WITHOUT_SUBWORK_ROSTER', None)))
def test_continuation_observer_distinguishes_original_ledger_from_unknown_new_contact(prefix, monkeypatch, state, expected):
    from empirical_lawhood.api.domain_composition.rubisco_response import preparation_observation as observation
    from empirical_lawhood.domains.rubisco.rubisco_response import active_preparation_continuation as continuation
    # Only presentation operands are exposed here; no source or custody admission is implied.
    original = prefix.config.identity
    assessment = SimpleNamespace(evaluations=(object(), object()), complete_native_return_ledger=True,
        continuation='EXACT_OPTIMIZER_CONTINUATION_ELECTRONIC_RESTART',
        positions=tuple(SimpleNamespace(position=name, disposition='SATISFIED', checkpoint=original) for name in ('initial', 'later')))
    readout = SimpleNamespace(assessment=assessment, original_result=SimpleNamespace(configuration=original))
    config = SimpleNamespace(original=prefix.config.original, identity=original, continuation=SimpleNamespace(readout=readout))
    monkeypatch.setattr(continuation, 'original_configuration', lambda _: original)
    progress = dict(state=state, publication='NOT_OBSERVED')
    rows, count = observation.prefix_positions(config, None, progress, None)
    assert count == expected
    assert len(rows) == 2
    assert all(row['independent_reading'] == ('ORIGINAL_CONTINUATION_INPUT_ASSESSED' if expected else 'NOT_YET_PUBLISHED') for row in rows)
