# SPDX-License-Identifier: MPL-2.0
"""Actual disclosed revision mathematics feeding the current finite frontier."""
from dataclasses import replace
from contextlib import nullcontext
from decimal import Decimal
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as records
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_science as reduction_owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_methods as scientific
from empirical_lawhood.adapters.methods.matrix_researcher_programme.frontier import PHASES, MatrixProgrammeObservation, programme_frontier
from empirical_lawhood.api import matrix_researcher_programme_e4_lineage as lineage
from tests.test_matrix_selected_e4_methods import declaration
from tests.test_matrix_selected_revision_native import (  # noqa: F401
    selected_revision, selected_e4_populations, selected_bridge, transfer, campaign_fixture, _development,
    selected_calibrated, revision_case, opportunity,
)


def _decision_products(f, branch):
    data, reduction, specification = f.data, f.reduction, f.specification
    if branch == "NOT_TRIGGERED":
        specification = scientific.derive_revision_specification(declaration(f.programme, threshold=Decimal(999)), f.programme)
    elif branch == "UNEVALUABLE":
        missing = records.SelectedE3E4CaseResult.unentered(f.programme.cases[0])
        reduction = reduction_owner.reduce_cases(f.programme, (missing, *reduction.cases[1:]), record_id=reduction.record_id)
        first = data.cases[0]
        data = replace(data, reduction=reduction.identity, cases=(replace(first, causal_prefix=None, score=None,
            disposition=missing.disposition, numerical_disposition=missing.numerical_disposition,
            forecast=missing.forecast, original_log_points=missing.original_log_points), *data.cases[1:]))
    nomination = scientific.select_revision(specification, f.programme, f.bank, reduction, data,
        nomination_id="nomination.disclosed-conditional." + branch.lower())
    frozen = scientific.freeze_revision(f.programme, nomination, freeze_id="freeze.disclosed-conditional." + branch.lower())
    return nomination, frozen


@pytest.fixture(scope="module", params=("NOT_TRIGGERED", "UNEVALUABLE", "TRIGGERED"))
def actual_decision_case(selected_revision, request):  # noqa: F811
    f = selected_revision
    nomination, frozen = _decision_products(f, request.param)
    return f, nomination, frozen



def test_both_original_revision_products_determine_the_actual_conditional_frontier(actual_decision_case, monkeypatch):
    f, nomination, frozen = actual_decision_case
    fit = _development(nomination, 'task.actual-revision-fit')
    freeze = _development(frozen, 'task.actual-revision-freeze')
    from empirical_lawhood.api import matrix_researcher_programme_prepared_lineage, selected_e4_native_runtime
    calls = []
    def locators(context, phase, kinds, *, locator_type):
        assert phase == 'e4.revision'
        assert kinds == (scientific.SelectedE4RevisionNomination, scientific.SelectedE4FrozenRevision)
        return fit, freeze
    def products(writer, requests, codecs):
        assert requests == ((fit, 'revision-fit'), (freeze, 'revision-freeze'))
        calls.extend(operation for _, operation in requests)
        return (f.programme, nomination), (f.programme, frozen)
    monkeypatch.setattr(matrix_researcher_programme_prepared_lineage, 'retained_development_products', locators)
    monkeypatch.setattr(selected_e4_native_runtime, 'development_products', products)
    _, _, decision = lineage.programme_revision_products(SimpleNamespace(writer=object(), namespace='literal.current'))
    assert calls == ['revision-fit', 'revision-freeze']
    observed = {phase: MatrixProgrammeObservation(phase, {'status': 'SUCCEEDED'}, True)
        for phase in ('train', 'e3', 'e4.development')}
    observed['e4.revision'] = MatrixProgrammeObservation('e4.revision', {}, True, decision.trigger_disposition)
    frontier = programme_frontier(observed, downstream_account='ORIGINAL_E3')
    if decision.trigger_disposition == 'TRIGGERED':
        assert 'e4.source-cal' in frontier.eligible
        assert 'e4.source-conf' not in frontier.eligible
    else:
        assert 'e4.source-cal' not in frontier.eligible
        assert 'e4.source-conf' in frontier.eligible
        assert dict(frontier.unentered)['e4.calibration'] == 'UNENTERED_REVISION_' + decision.trigger_disposition


def test_missing_original_decision_never_implies_unentered_calibration():
    observed = {phase: MatrixProgrammeObservation(phase, {}, True) for phase in ('train', 'e3', 'e4.development', 'e4.revision')}
    frontier = programme_frontier(observed, downstream_account='ORIGINAL_E3')
    assert not frontier.unentered
    assert 'e4.source-conf' not in frontier.eligible
    assert 'e4.revision.authenticated-decision' in dict(frontier.waiting)['e4.source-conf']


def test_e6_frontier_does_not_require_successful_e5_confirmation():
    observed = {phase: MatrixProgrammeObservation(phase, {'scientific_status': 'ADVERSE'}, True)
        for phase in ('e3', 'e4.confirmation', 'e5.development', 'e6.initialize')}
    assert 'e6.source' in programme_frontier(observed, downstream_account='ORIGINAL_E3').eligible
    observed['e6.source'] = MatrixProgrammeObservation('e6.source', {}, True)
    assert 'e6' in programme_frontier(observed, downstream_account='ORIGINAL_E3').eligible
    assert 'e5.confirmation' not in observed


@pytest.fixture(scope='module', params=('NOMINATED', 'NONDISCRIMINATING_OPPORTUNITY', 'UNEVALUABLE_OPPORTUNITY'))
def actual_e5_nomination(opportunity, request):  # noqa: F811
    from tests.test_matrix_selected_opportunity import literal_observations
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_opportunity as science
    observations = literal_observations(opportunity,
        hold_error=Decimal('.01') if request.param == 'NONDISCRIMINATING_OPPORTUNITY' else Decimal('.9'))
    if request.param == 'UNEVALUABLE_OPPORTUNITY':
        del observations[next(iter(observations))]
    _, nomination = science.nominate_selected_opportunity(opportunity, observations,
        result_id='nomination.disclosed-frontier.' + request.param.lower())
    assert nomination.disposition == request.param
    assert len(nomination.cases) == len(opportunity.roster.cases)
    return nomination


def _disclosed_read(result, account):
    """Literal read/locator seam around actual math; no publication or authority."""
    from empirical_lawhood.api import matrix_researcher_programme_prepared_lineage as prepared
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
    from tests.test_matrix_selected_e4_methods import pin
    from tests.test_matrix_selected_opportunity import unpublished
    functional = result if account == 'ORIGINAL_E3' else result.functional
    result_identity = ObjectIdentity.from_record(result.record_id, result) if account == 'REVISION' else result.identity
    locator = SimpleNamespace(record=result_identity,
        receipt=pin('receipt.disclosed-frontier', CanonicalTaskReceipt.SCHEMA, CanonicalTaskReceipt.VERSION),
        publication=unpublished(result, 'publication.disclosed-frontier'))
    science = {'scientific_completion': 'COMPLETE_ASSIGNED_E5_DEVELOPMENT_CENSUS',
        'assessment': result.to_document(), 'nomination_disposition': functional.disposition,
        'assigned_groups': len(functional.development_unit_ids), 'assigned_cases': len(functional.cases),
        'custody': {'assessment': {'receipt': locator.receipt.to_document(),
            'logical_artifact': locator.publication.logical.to_document(),
            'materialization': locator.publication.materialization.to_document()}}}
    report = {'status': 'SUCCEEDED', 'scientific_result': science}
    context = SimpleNamespace(design=SimpleNamespace(downstream_account=account,
        e5_development=SimpleNamespace(expected_groups=len(functional.development_unit_ids))),
        report=lambda phase: report)
    return prepared, context, locator, report


def test_actual_e5_nomination_and_complete_custody_determine_conf_nonentry(actual_e5_nomination, monkeypatch):
    prepared, context, locator, report = _disclosed_read(actual_e5_nomination, 'ORIGINAL_E3')
    calls = []
    def original(actual, phase):
        assert actual is context and phase == 'e5.development'
        calls.append(phase)
        return locator
    monkeypatch.setattr(prepared, 'programme_development_product', original)
    disposition = prepared.programme_development_nomination(context)
    assert calls == ['e5.development']
    from empirical_lawhood.api.matrix_researcher_programme import MatrixResearchProgrammeService
    context.bindings, context.observations = {'e5.development': object()}, {}
    service = MatrixResearchProgrammeService(service=SimpleNamespace(artifact_writer=object()))
    monkeypatch.setattr(service, '_read_phase', lambda *args, **kwargs: report)
    monkeypatch.setattr(service, '_phase_scope', lambda *args: nullcontext())
    service._observe(context)
    assert context.observations['e5.development'].nomination_disposition == disposition
    observed = {phase: MatrixProgrammeObservation(phase, {}, True)
        for phase in ('e3', 'e4.confirmation', 'e5.initialize-development', 'e6.initialize')}
    observed['e5.development'] = MatrixProgrammeObservation('e5.development', report, True,
        nomination_disposition=disposition)
    frontier = programme_frontier(observed, downstream_account='ORIGINAL_E3')
    assert 'e6.source' in frontier.eligible
    if disposition == 'NOMINATED':
        assert not frontier.unentered and 'e5.initialize-confirmation' in frontier.eligible
    else:
        assert tuple(dict(frontier.unentered)) == ('e5.initialize-confirmation', 'e5.source', 'e5.confirmation')
        assert all(reason == 'UNENTERED_E5_' + disposition for _, reason in frontier.unentered)
        assert not set(dict(frontier.unentered)).intersection(frontier.eligible)
        assert any(row.disposition == 'MISSING' for row in actual_e5_nomination.cases) == (
            disposition == 'UNEVALUABLE_OPPORTUNITY')


def test_revision_e5_negative_keeps_the_actual_assigned_census(revision_case, monkeypatch):  # noqa: F811
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_results import assess_revision_programme
    _, result = assess_revision_programme(revision_case.programme, {}, result_id='assessment.disclosed-frontier.revision-missing')
    assert result.functional.disposition == 'UNEVALUABLE_OPPORTUNITY'
    assert len(result.cases) == len(revision_case.programme.roster.cases)
    prepared, context, locator, report = _disclosed_read(result, 'REVISION')
    monkeypatch.setattr(prepared, 'programme_development_product', lambda *args: locator)
    disposition = prepared.programme_development_nomination(context)
    observed = {phase: MatrixProgrammeObservation(phase, {}, True) for phase in ('e3', 'e6.initialize')}
    observed['e4.confirmation'] = MatrixProgrammeObservation('e4.confirmation', {}, True, downstream_choice='REVISION')
    observed['e5.development'] = MatrixProgrammeObservation('e5.development', report, True,
        nomination_disposition=disposition)
    frontier = programme_frontier(observed, downstream_account='REVISION')
    assert 'e6.source' in frontier.eligible
    assert tuple(dict(frontier.unentered)) == ('e5.initialize-confirmation', 'e5.source', 'e5.confirmation')


@pytest.mark.parametrize('damage', ('partial', 'identity', 'receipt', 'groups', 'cases', 'disposition', 'custody', 'boolean-count', 'schema'))
def test_e5_report_or_census_substitution_never_establishes_nonentry(actual_e5_nomination, monkeypatch, damage):
    prepared, context, locator, report = _disclosed_read(actual_e5_nomination, 'ORIGINAL_E3')
    science = report['scientific_result']
    if damage == 'partial':
        science['scientific_completion'] = 'NOT_ESTABLISHED'
    elif damage == 'identity':
        locator.record = replace(locator.record, object_fingerprint='f' * 64)
    elif damage == 'receipt':
        locator.receipt = replace(locator.receipt, object_fingerprint='f' * 64)
    elif damage == 'groups':
        context.design.e5_development.expected_groups += 1
    elif damage == 'cases':
        science['assigned_cases'] -= 1
    elif damage == 'disposition':
        science['nomination_disposition'] = 'UNENTERED'
    elif damage == 'custody':
        del science['custody']
    elif damage == 'boolean-count':
        science['assigned_groups'] = True
    else:
        science['assessment']['schema'] = 'empirical-lawhood/testing/substituted-assessment'
    monkeypatch.setattr(prepared, 'programme_development_product', lambda *args: locator)
    with pytest.raises((PermissionError, ValueError)):
        prepared.programme_development_nomination(context)


def test_expired_or_missing_original_development_access_is_not_a_negative(actual_e5_nomination, monkeypatch):
    prepared, context, _, _ = _disclosed_read(actual_e5_nomination, 'ORIGINAL_E3')
    def refused(*args):
        raise PermissionError('literal original custody/access refusal')
    monkeypatch.setattr(prepared, 'programme_development_product', refused)
    with pytest.raises(PermissionError, match='custody/access refusal'):
        prepared.programme_development_nomination(context)


@pytest.fixture(scope='module', params=((), ('e4.revision-baseline',)))
def actual_downstream_case(selected_calibrated, request):  # noqa: F811
    from tests.test_matrix_selected_e4_methods import confirmation_products
    f = confirmation_products(selected_calibrated, required=request.param)
    result = scientific.nominate_downstream(f.specification, f.result, selected_calibrated.export,
        f.public_calibration, record_id='downstream.disclosed-frontier.' + ('unevaluable' if request.param else 'eligible'))
    scope = SimpleNamespace(specification=f.specification, revision=selected_calibrated.export, calibration=f.public_calibration)
    return result, scope


def test_complete_actual_conf_product_supplies_revision_package_choice(actual_downstream_case, monkeypatch):
    from empirical_lawhood.api import matrix_researcher_programme_lineage as current
    result, original_scope = actual_downstream_case
    scope = SimpleNamespace(**vars(original_scope))
    context = SimpleNamespace(method_inputs=lambda phase: SimpleNamespace(plan=SimpleNamespace(tail=SimpleNamespace(confirmation=scope))))
    calls = []
    def original(actual, phase, schema):
        assert actual is context and phase == 'e4.confirmation' and schema == scientific.SelectedE4DownstreamNomination.SCHEMA
        calls.append(phase)
        return result, object()
    monkeypatch.setattr(current, '_issued_e4_record', original)
    choice = lineage.programme_downstream_choice(context)
    assert calls == ['e4.confirmation'] and choice == ('UNSELECTED' if result.selected is None else 'REVISION')
    from empirical_lawhood.api.matrix_researcher_programme import MatrixResearchProgrammeService
    context.design = SimpleNamespace(downstream_account='REVISION')
    context.bindings, context.observations = {'e4.confirmation': object()}, {}
    report = {'scientific_completion': 'ASSESSMENT_RETAINED', 'all_wave_terminals_present': True,
        'assessment': {'status': 'SUCCEEDED', 'scientific_result': {}},
        'structure': {'scientific_completion': 'COMPLETE_ORIGINAL_FULL_FACTOR_CENSUS'}}
    service = MatrixResearchProgrammeService(service=SimpleNamespace(artifact_writer=object()))
    monkeypatch.setattr(service, '_read_phase', lambda *args, **kwargs: report)
    monkeypatch.setattr(service, '_phase_scope', lambda *args: nullcontext())
    service._observe(context)
    assert context.observations['e4.confirmation'].downstream_choice == choice
    observed = {'e3': MatrixProgrammeObservation('e3', {}, True),
        'e4.confirmation': MatrixProgrammeObservation('e4.confirmation', {}, True, downstream_choice=choice)}
    frontier = programme_frontier(observed, downstream_account='REVISION')
    if result.selected is None:
        assert tuple(dict(frontier.unentered)) == tuple(phase for phase in PHASES if phase.startswith(('e5.', 'e6')))
        assert all(reason == 'UNENTERED_REVISION_PACKAGE_UNSELECTED' for _, reason in frontier.unentered)
    else:
        assert not frontier.unentered and 'e5.initialize-development' in frontier.eligible
    scope.specification = replace(scope.specification, specification_id=scope.specification.specification_id + '.foreign')
    with pytest.raises(PermissionError, match='original CONF scope'):
        lineage.programme_downstream_choice(context)


def test_current_conf_reader_returns_record_and_locator_within_the_same_live_callback(actual_downstream_case, monkeypatch):
    """Literal authority descriptors isolate callback transport, never grant access."""
    from empirical_lawhood.api import matrix_researcher_programme_lineage as current, selected_e4_native_read
    from tests.test_matrix_sampling_follow_on import prior_product
    result, _ = actual_downstream_case
    previous = prior_product(result.identity)
    original = previous.prior_execution
    def record(pin, field):
        return SimpleNamespace(**{field: pin.object_id}, SCHEMA=pin.object_schema, VERSION=pin.object_version,
            fingerprint=lambda: pin.object_fingerprint)
    package = record(original.package, 'package_id')
    package.issued_study = record(original.issued_study, 'issue_id')
    package.execution_authority = record(original.execution_authority, 'authority_id')
    plan, receipt = record(original.execution_plan, 'execution_plan_id'), record(original.receipt, 'receipt_id')
    receipt.task_id = original.task_id
    actual_selected, writer = object(), object()
    context = SimpleNamespace(writer=writer, authority=lambda phase, component: (actual_selected, None,
        SimpleNamespace(reveal_authority_id=previous.reveal_authority.object_id), package,
        SimpleNamespace(run_plan_id=original.run_id), plan))
    calls = []
    def live_read(*, selected, artifact_writer, run_id, reveal_authority_id, consume_tail):
        assert selected is actual_selected and artifact_writer is writer and run_id == original.run_id
        assert reveal_authority_id == previous.reveal_authority.object_id
        value = consume_tail(writer=writer, package=package, plan=plan, entry=None, receipts={},
            products=((result, receipt, SimpleNamespace(logical_artifact_id=original.logical_artifact_id)),),
            reveal=record(previous.reveal_authority, 'authority_id'))
        assert value[0] is result and value[1].record == result.identity
        calls.append('live-read-closed')
        return value
    monkeypatch.setattr(selected_e4_native_read, '_read_selected_e4_component', live_read)
    actual, locator = current._issued_e4_record(context, 'e4.confirmation', type(result).SCHEMA)
    assert actual is result and calls == ['live-read-closed']
    assert locator.prior_execution == replace(original, binding_id='binding.programme.' + result.fingerprint())
    assert current._issued_e4_product(context, 'e4.confirmation', type(result).SCHEMA) == locator
    assert calls == ['live-read-closed', 'live-read-closed']
    def refused(**kwargs):
        raise PermissionError('literal current original reveal refused')
    monkeypatch.setattr(selected_e4_native_read, '_read_selected_e4_component', refused)
    with pytest.raises(PermissionError, match='current original reveal refused'):
        current._issued_e4_record(context, 'e4.confirmation', type(result).SCHEMA)


@pytest.mark.parametrize('branch', ('NOT_TRIGGERED', 'UNEVALUABLE'))
def test_revision_account_nonentry_uses_actual_original_revision_decision(selected_revision, branch):  # noqa: F811
    nomination, frozen = _decision_products(selected_revision, branch)
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_programme import SelectedE4PublicRevisionDecision
    actual = SelectedE4PublicRevisionDecision.from_products(selected_revision.programme, nomination, frozen,
        record_id='decision.disclosed-frontier.' + branch.lower())
    observed = {'e4.revision': MatrixProgrammeObservation('e4.revision', {}, True, actual.trigger_disposition)}
    frontier = programme_frontier(observed, downstream_account='REVISION')
    assert set(dict(frontier.unentered)) == {'e4.source-cal', 'e4.calibration',
        *(phase for phase in PHASES if phase.startswith(('e5.', 'e6')))}
    assert not set(dict(frontier.unentered)).intersection(frontier.eligible)


@pytest.mark.parametrize('account,disposition,choice', (
    ('ORIGINAL_E3', 'NONDISCRIMINATING_OPPORTUNITY', None),
    ('ORIGINAL_E3', 'UNEVALUABLE_OPPORTUNITY', None),
    ('REVISION', None, 'UNSELECTED'),
    ('REVISION', None, 'ORIGINAL_E3'),
))
def test_all_eligible_complete_stops_without_projecting_or_entering_skipped_phases(monkeypatch, account, disposition, choice):
    from empirical_lawhood.api.matrix_researcher_programme import MatrixResearchProgrammeService
    skipped = (('e5.initialize-confirmation', 'e5.source', 'e5.confirmation') if account == 'ORIGINAL_E3'
        else tuple(phase for phase in PHASES if phase.startswith(('e5.', 'e6'))))
    observed = {phase: MatrixProgrammeObservation(phase, {}, True) for phase in PHASES if phase not in skipped}
    observed['e4.revision'] = MatrixProgrammeObservation('e4.revision', {}, True, 'TRIGGERED')
    observed['e4.confirmation'] = MatrixProgrammeObservation('e4.confirmation', {}, True, downstream_choice=choice)
    if disposition is not None:
        observed['e5.development'] = MatrixProgrammeObservation('e5.development', {}, True, nomination_disposition=disposition)
    context = SimpleNamespace(design=SimpleNamespace(downstream_account=account), observations=observed)
    service = MatrixResearchProgrammeService(service=SimpleNamespace(artifact_writer=object()))
    monkeypatch.setattr(service, '_observe', lambda actual, **kwargs: None)
    monkeypatch.setattr(service, '_advance_report', lambda actual, dependencies: programme_frontier(actual.observations,
        downstream_account=actual.design.downstream_account))
    def forbidden(*args, **kwargs):
        pytest.fail('conditional nonentry reached derivation, authoring or native execution')
    for name in ('_project', '_retain_binding', '_author_phase', '_operate_phase'):
        monkeypatch.setattr(service, name, forbidden)
    result = service._advance(context, mode='run')
    assert result.complete and not result.eligible and not result.waiting
    assert tuple(dict(result.unentered)) == skipped


@pytest.mark.parametrize('account', ('ORIGINAL_E3', 'REVISION'))
def test_complete_e5_operational_status_without_scientific_census_does_not_advance(monkeypatch, account):
    from empirical_lawhood.api.matrix_researcher_programme import MatrixResearchProgrammeService, _phase_complete
    report = {'status': 'SUCCEEDED', 'scientific_result': {'scientific_completion': 'NOT_ESTABLISHED'}}
    assert not _phase_complete('e5.development', report)
    service = MatrixResearchProgrammeService(service=SimpleNamespace(artifact_writer=object()))
    context = SimpleNamespace(bindings={'e5.development': object()}, observations={},
        design=SimpleNamespace(downstream_account=account))
    monkeypatch.setattr(service, '_read_phase', lambda *args, **kwargs: report)
    monkeypatch.setattr(service, '_phase_scope', lambda *args: nullcontext())
    service._observe(context)
    assert not context.observations['e5.development'].complete
    frontier = programme_frontier(context.observations, downstream_account=account)
    assert not frontier.unentered and 'e5.initialize-confirmation' not in frontier.eligible


@pytest.mark.parametrize('account', ('', 'original_e3', None, True))
def test_frontier_requires_exact_frozen_account(account):
    with pytest.raises(ValueError, match='frozen D'):
        programme_frontier({}, downstream_account=account)


def test_missing_actual_conditional_products_never_mean_negative_or_revision_fallback():
    observed = {phase: MatrixProgrammeObservation(phase, {}, True) for phase in ('e3', 'e4.confirmation', 'e5.development')}
    for account in ('ORIGINAL_E3', 'REVISION'):
        frontier = programme_frontier(observed, downstream_account=account)
        assert not frontier.unentered and 'e5.initialize-confirmation' not in frontier.eligible
    frontier = programme_frontier(observed, downstream_account='REVISION')
    assert 'e5.initialize-development' not in frontier.eligible and 'e6.initialize' not in frontier.eligible
    assert 'e4.confirmation.authenticated-revision-package' in dict(frontier.waiting)['e6.initialize']


@pytest.mark.parametrize('entered', ('complete', 'uncertain-contact', 'known-return', 'uncontacted-parent', 'unavailable'))
def test_negative_nomination_refuses_to_rewrite_retained_entered_or_uncertain_conf(entered):
    report = {}
    if entered == 'uncertain-contact':
        report['current_native_facts'] = ({'uncertain_contact_definition_ids': ('literal-contact-pin',)},)
    elif entered == 'known-return':
        report['current_native_facts'] = ({'native_returns': ({'native_return_status': 'SUCCEEDED'},)},)
    elif entered == 'uncontacted-parent':
        report['current_native_facts'] = ({'uncontacted_definition_ids': ('literal-definition-pin',)},)
    elif entered == 'unavailable':
        report['native_observation_unavailable'] = ({'reason': 'literal missing original custody'},)
    observed = {'e5.development': MatrixProgrammeObservation('e5.development', {}, True,
        nomination_disposition='NONDISCRIMINATING_OPPORTUNITY'),
        'e5.confirmation': MatrixProgrammeObservation('e5.confirmation', report, entered == 'complete')}
    with pytest.raises(ValueError, match='conflicts with retained phase completion or native custody'):
        programme_frontier(observed, downstream_account='ORIGINAL_E3')


@pytest.mark.parametrize('phase,fields', (
    ('e5.development', {'nomination_disposition': 'NONDISCRIMINATING_OPPORTUNITY'}),
    ('e4.confirmation', {'downstream_choice': 'UNSELECTED'}),
))
def test_incomplete_observation_cannot_claim_conditional_nonentry(phase, fields):
    with pytest.raises(ValueError, match='authenticated complete'):
        MatrixProgrammeObservation(phase, {}, False, **fields)
