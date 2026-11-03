# SPDX-License-Identifier: MPL-2.0
"""Disclosed incomplete-read controls; no science, issue or qualification.

Literal control stubs isolate the public selection/authority boundary. Existing
ordinary native-store controls supply the real unknown-contact scalar math.
No manufactured completion, successful task or derivative publication is used.
"""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import configured_e3_incomplete_read as owner
from empirical_lawhood.api.domain_composition.matrix_configured_protected_response import scientific_read as reader
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.experimental_statistics import binomial_upper_tail, split_upper_calibration
from tests.test_matrix_configured_unknown_response import (
    case as case, configured_prefix_case as configured_prefix_case,
    legacy_case as legacy_case, no_science as no_science, original_case as original_case,
)
from tests.test_current_result_custody import actual_issued_current_task_controls as actual_issued_current_task_controls


def empty_rows(case):
    return {unit: {'state': 'UNENTERED', 'forecast': None, 'outcome': None}
        for role in ('calibration', 'evaluation') for unit in case.allocation.unit_ids(role)}


@pytest.mark.parametrize('changed_bytes', (False, True))
def test_external_input_projection_uses_frozen_artifact_order_and_checks_identity(monkeypatch, changed_bytes):
    """Disclosed metadata isolates ordering; it supplies no publication authority."""
    from empirical_lawhood.kernel.evidence import OutcomeAccess
    from empirical_lawhood.infrastructure.execution import SchedulerConsistencyError

    ids = ('z.config', 'a.operand')  # Declaration order differs from artifact order.
    manifests, specs, checks = {}, [], []
    for artifact_id in ids:
        logical = SimpleNamespace(logical_artifact_id=artifact_id, content_sha256='a' * 64,
            payload_schema='synthetic.config', media_type='application/json',
            outcome_access=OutcomeAccess.OUTCOME_BLIND, visibility_ceiling=owner.VisibilityCeiling.PROSPECTIVE)
        physical = SimpleNamespace(relative_path=artifact_id, storage_root_id='synthetic.store',
            compression='none', partition_selector=None, size_bytes=13)
        manifests[artifact_id] = SimpleNamespace(logical=logical, materialization=physical, publication=object())
        specs.append(SimpleNamespace(logical_artifact_id=artifact_id, expected_content_sha256='a' * 64,
            expected_payload_schema=logical.payload_schema, expected_size_bytes=13,
            expected_media_type=logical.media_type, expected_outcome_access=logical.outcome_access,
            expected_visibility_ceiling=logical.visibility_ceiling, identity_scope_sha256=None))
    task = SimpleNamespace(external_inputs=tuple(specs), external_input_artifact_ids=tuple(sorted(ids)),
        capability=SimpleNamespace(config=SimpleNamespace(artifact_id='z.config',
            content_sha256='a' * 64, config_schema='synthetic.config')))
    if changed_bytes:
        manifests['a.operand'].logical.content_sha256 = 'b' * 64
    writer = SimpleNamespace(root=SimpleNamespace(contract=SimpleNamespace(storage_root_id='synthetic.store')),
        read_manifest=manifests.__getitem__, verify_manifest=lambda value: checks.append(value.logical.logical_artifact_id))
    monkeypatch.setattr(owner, 'provider_input_location', lambda writer, run, artifact: (artifact, None, None))
    monkeypatch.setattr(owner, 'VerifiedArtifactInput', lambda logical, physical:
        SimpleNamespace(logical=logical, materialization=physical, artifact_id=logical.logical_artifact_id))
    if changed_bytes:
        with pytest.raises(SchedulerConsistencyError, match='content identity differs'):
            owner._external_inputs(writer, task, 'run.synthetic')
    else:
        result = owner._external_inputs(writer, task, 'run.synthetic')
        assert tuple(value.artifact_id for value in result) == task.external_input_artifact_ids
    assert checks == list(ids) and task.external_inputs == tuple(specs)


def test_missing_forecasts_keep_full_denominators_without_inventing_observations(case):
    rows = empty_rows(case)
    math = owner._denominator_math(case.specification, case.allocation, rows, {})
    # The owning read returns this through the strict canonical projection.
    # Mutable intermediate lists must not escape into that final boundary.
    encoded = owner.canonical_value(math)
    assert encoded['assessment']['assigned_units'] == len(case.allocation.unit_ids('evaluation'))
    cal, conf = math['calibration'], math['assessment']
    expected_cal = case.allocation.unit_ids('calibration')
    expected_conf = case.allocation.unit_ids('evaluation')
    assert tuple(row[0] for row in cal['scores']) == expected_cal
    assert all(row[1] is None and row[2] == ('UNENTERED',) for row in cal['scores'])
    assert cal['rank'] == split_upper_calibration((None,) * len(expected_cal), case.specification.calibration_alpha).rank
    assert cal['radius'] is None and cal['radius_kind'] == 'INFINITE'
    assert conf['assigned_units'] == len(expected_conf) and conf['usable_units'] == conf['successes'] == 0
    tail = binomial_upper_tail(len(expected_conf), 0, case.specification.assessment.null_probability)
    assert (conf['binomial_tail_numerator'], conf['binomial_tail_denominator']) == (tail.numerator, tail.denominator)
    assert not conf['criterion_met']
    assert all(len(row.comparisons) == 4 and all(value is None for _, _, value in row.comparisons)
        for row in conf['decisions'])
    assert all(row['forecast'] is row['outcome'] is None for row in rows.values())


def test_real_unknown_contact_is_none_in_full_census_and_other_states_remain_distinct(case):
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_unknown_response import score_unknown_response
    score, outcome = score_unknown_response(case.availability, case.operands,
        score_id='read-score.disclosed', outcome_id='read-outcome.disclosed')
    rows = empty_rows(case)
    unit = case.error.feature.unit_id
    rows[unit] = {'state': 'UNKNOWN_CONTACT', 'forecast': case.error, 'outcome': outcome}
    confirmation = case.allocation.unit_ids('evaluation')
    rows[confirmation[0]]['state'] = 'KNOWN_FAILED_NATIVE_RETURN'
    rows[confirmation[-1]]['state'] = 'UNENTERED'
    math = owner._denominator_math(case.specification, case.allocation, rows,
        {owner.methods.identity(case.frozen): case.frozen})
    assert score.reason_codes == ('UNKNOWN_CONTACT',) and score.cumulative_log_errors == (None,) * 15
    assert len(math['calibration']['scores']) == len(case.allocation.unit_ids('calibration'))
    assert next(row for row in math['calibration']['scores'] if row[0] == unit)[1] is None
    decisions = math['assessment']['decisions']
    assert decisions[0].reasons == ('KNOWN_FAILED_NATIVE_RETURN',)
    assert decisions[-1].reasons == ('UNENTERED',)
    assert all(not row.usable and not row.success for row in decisions)
    assert case.native.inspect(case.availability.definition).receipt is None


@pytest.mark.parametrize('error_type,return_code', ((None, None), ('RuntimeError', None), (None, 17)))
def test_raw_return_without_products_stays_known_and_missing_in_the_full_census(
        case, monkeypatch, error_type, return_code):
    """Literal call facts test the reader projection; no native call or genuine issue."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_unknown_response import (
        ConfiguredProtectedE3UnknownResponseAvailability,
    )
    from empirical_lawhood.runtime.native_subwork import NativeSubworkCallEntry, NativeSubworkCallReturn
    from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract

    availability = case.availability
    parent, definition = availability.parent_contact, availability.definition
    entered = NativeSubworkCallEntry(definition.identity, availability.contact_identity,
        ObjectIdentity('invocation.disclosed.read-control', PreparedInvocationContract.SCHEMA,
            PreparedInvocationContract.VERSION, 'a' * 64), '2026-10-21T00:00:00Z')
    returned = NativeSubworkCallReturn(ObjectIdentity.from_record('entry.disclosed.read-control', entered),
        '2026-10-21T00:00:01Z', error_type, return_code)
    inspection = replace(case.native.inspect(definition), call_entry=entered, call_return=returned)
    assert inspection.completion is inspection.receipt is None and inspection.outputs == ()
    # A known raw return cannot be projected as a new UNKNOWN-contact score.
    with pytest.raises(ValueError, match='actual uncompleted native contact'):
        ConfiguredProtectedE3UnknownResponseAvailability.from_inspection('availability.disclosed.rejected',
            parent_contact=parent, roster=availability.roster, inspection=inspection,
            contact_identity=availability.contact_identity)
    contacts = SimpleNamespace(read=lambda run, task: parent)
    store = SimpleNamespace(read_roster=lambda selected: availability.roster,
        iter_roster_definitions=lambda selected: iter((definition,)), inspect=lambda selected: inspection)
    monkeypatch.setattr(owner, 'ExternalNativeEffectContactStore', lambda **kwargs: contacts)
    monkeypatch.setattr(owner, 'ExternalNativeSubworkStore', lambda **kwargs: store)
    dispatch = []
    monkeypatch.setattr(owner, 'authenticate_task_dispatch_authority', lambda **kwargs: dispatch.append(kwargs))
    work = SimpleNamespace(rosters=(availability.roster,), definitions=(definition,))
    monkeypatch.setattr(owner, '_operands', lambda *args: (case.operands, work, ()))
    monkeypatch.setattr(owner, 'score_unknown_response', lambda *args, **kwargs:
        pytest.fail('known return was relabelled as UNKNOWN-contact evidence'))
    output = SimpleNamespace(visibility_ceiling=owner.VisibilityCeiling.DEVELOPMENT_ONLY,
        outcome_access=case.operands.outcome_access)
    task = SimpleNamespace(task_id=parent.task_id, outputs=(output,),
        capability=SimpleNamespace(requested_outcome_access=case.operands.outcome_access))
    state, evidence = owner._unknown_response(None, SimpleNamespace(run_plan_id=parent.run_id),
        SimpleNamespace(execution_plan_id='plan.disclosed.read-control', fingerprint=lambda: 'b' * 64,
            SCHEMA='empirical-lawhood/runtime/execution-plan', VERSION='1.0.0'),
        task, case.operands.config, (), {}, (parent.attempt_id,))
    expected = ('KNOWN_FAILED_NATIVE_RETURN' if error_type is not None or return_code not in (None, 0)
        else 'KNOWN_NATIVE_RETURN_WITHOUT_PARENT_RESULT')
    assert state == expected and len(dispatch) == 1
    assert evidence['call_entry'] is entered and evidence['call_return'] is returned
    assert evidence['completion'] is None and 'score' not in evidence and 'outcome' not in evidence
    rows = empty_rows(case)
    unit = case.allocation.unit_ids('evaluation')[0]
    rows[unit] = {'state': state, 'forecast': None, 'outcome': None}
    math = owner._denominator_math(case.specification, case.allocation, rows, {})
    assert math['assessment']['assigned_units'] == len(case.allocation.unit_ids('evaluation'))
    assert math['assessment']['usable_units'] == math['assessment']['successes'] == 0
    assert math['assessment']['decisions'][0].reasons == (expected,)


@pytest.mark.parametrize('damage', ('missing-freeze', 'foreign-freeze', 'foreign-allocation', 'foreign-outcome'))
def test_incomplete_math_refuses_foreign_original_paired_premises(case, damage):
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_unknown_response import score_unknown_response
    _, outcome = score_unknown_response(case.availability, case.operands,
        score_id='read-score.disclosed', outcome_id='read-outcome.disclosed')
    forecast = case.error
    freezes = {owner.methods.identity(case.frozen): case.frozen}
    if damage == 'missing-freeze':
        freezes = {}
    elif damage == 'foreign-freeze':
        freezes[owner.methods.identity(case.frozen)] = replace(case.frozen,
            models=replace(case.frozen.models, object_fingerprint='f' * 64))
    elif damage == 'foreign-allocation':
        forecast = replace(forecast, allocation=replace(forecast.allocation, object_fingerprint='f' * 64))
    else:
        outcome = replace(outcome, forecast=replace(outcome.forecast, object_fingerprint='f' * 64))
    rows = empty_rows(case)
    rows[forecast.feature.unit_id] = {'state': 'UNKNOWN_CONTACT', 'forecast': forecast, 'outcome': outcome}
    with pytest.raises(PermissionError, match='ORIGINAL_FROZEN_FORECAST'):
        owner._denominator_math(case.specification, case.allocation, rows, freezes)


@pytest.fixture
def public_boundary(actual_issued_current_task_controls, case, monkeypatch):
    from empirical_lawhood.api import configured_e3_primary_amendment
    f = actual_issued_current_task_controls
    package, plan = f.control.package, f.plan
    selected = SimpleNamespace(association=SimpleNamespace(candidate=ObjectIdentity.from_record(
        package.issued_study.candidate.candidate_id, package.issued_study.candidate)),
        implementation=package.issued_study.source_closure, projection=SimpleNamespace(tasks=plan.tasks))
    selected.instance = SimpleNamespace(specification=case.specification.identity)
    selected.association.identity = selected.association.candidate
    selected.handoff = SimpleNamespace(projection=selected.projection)
    monkeypatch.setattr(reader, '_original_design', lambda selected: (case.specification, case.allocation))
    monkeypatch.setattr(reader, '_current_control', lambda **kwargs: package)
    monkeypatch.setattr(reader, 'authenticate_current_execution_plan', lambda **kwargs: plan)
    monkeypatch.setattr(reader, '_retained_scientific_writer', lambda package, plan, writer: writer)
    monkeypatch.setattr(reader, '_selected_preparation', lambda selected: SimpleNamespace(primary_amendment=None))
    accesses, reads, amendments = [], [], []
    monkeypatch.setattr(configured_e3_primary_amendment, 'authenticate_primary_amendment',
        lambda **kwargs: amendments.append('exact-primary-inputs'))

    def assessment(**kwargs):
        reads.append('protected-inputs')
        return {'scientific_completion': 'UNPUBLISHED_INCOMPLETE_ASSESSMENT',
            'adjudication': None, **owner._denominator_math(case.specification, case.allocation, empty_rows(case), {})}

    monkeypatch.setattr(owner, 'read_incomplete_assessment', assessment)

    def authorize(writer, package, reveal):
        accesses.append(tuple(reads))
        if reveal is None:
            raise PermissionError('current reveal required before protected inputs')

    monkeypatch.setattr(reader, '_authorize', authorize)
    return SimpleNamespace(selected=selected, writer=f.control.service.artifact_plane,
        run_id=package.run_plan_id, accesses=accesses, reads=reads, amendments=amendments)


def test_explicit_incomplete_read_requires_reveal_before_inputs_and_at_final_return(public_boundary):
    f = public_boundary
    with pytest.raises(PermissionError, match='before protected inputs'):
        reader.read_protected_e3_result(selected=f.selected, artifact_writer=f.writer,
            run_id=f.run_id, assess_incomplete=True)
    assert f.reads == []
    f.accesses.clear()
    report = reader.read_protected_e3_result(selected=f.selected, artifact_writer=f.writer,
        run_id=f.run_id, reveal_authority_id='reveal.disclosed', assess_incomplete=True)
    assert report['scientific_completion'] == 'UNPUBLISHED_INCOMPLETE_ASSESSMENT' and report['adjudication'] is None
    assert f.accesses == [(), ('protected-inputs',), ('protected-inputs',)]
    assert f.amendments == ['exact-primary-inputs'] and report['primary_family_amendment'] is None


def test_incomplete_public_read_enters_the_same_continuation_owner_as_completed_reads(public_boundary, monkeypatch):
    from contextlib import contextmanager
    from empirical_lawhood.api import configured_e3_retained_read

    f, entries = public_boundary, []
    @contextmanager
    def continued_scope(*, writer, plan):
        entries.append((writer, plan))
        try:
            yield None
        finally:
            entries.append('exit')
    monkeypatch.setattr(configured_e3_retained_read, 'continued_plan_read', continued_scope)
    report = reader.read_protected_e3_result(selected=f.selected, artifact_writer=f.writer,
        run_id=f.run_id, reveal_authority_id='reveal.disclosed', assess_incomplete=True)
    assert report['scientific_completion'] == 'UNPUBLISHED_INCOMPLETE_ASSESSMENT'
    assert len(entries) == 2 and entries[-1] == 'exit'
    assert entries[0][0].root is f.writer.root
    assert entries[0][1].tasks == f.selected.projection.tasks


def test_incomplete_final_reveal_refusal_prevents_return(public_boundary, monkeypatch):
    f = public_boundary
    def authorize(*args):
        if f.reads:
            raise PermissionError('current reveal expired during incomplete read')
    monkeypatch.setattr(reader, '_authorize', authorize)
    with pytest.raises(PermissionError, match='expired during incomplete read'):
        reader.read_protected_e3_result(selected=f.selected, artifact_writer=f.writer,
            run_id=f.run_id, reveal_authority_id='reveal.disclosed', assess_incomplete=True)


def test_incomplete_primary_amendment_refusal_precedes_scientific_math(public_boundary, monkeypatch):
    from empirical_lawhood.api import configured_e3_primary_amendment
    f = public_boundary
    def refuse(**kwargs):
        raise PermissionError('actual selected primary amendment provenance refused')
    monkeypatch.setattr(configured_e3_primary_amendment, 'authenticate_primary_amendment', refuse)
    with pytest.raises(PermissionError, match='primary amendment provenance refused'):
        reader.read_protected_e3_result(selected=f.selected, artifact_writer=f.writer,
            run_id=f.run_id, reveal_authority_id='reveal.disclosed', assess_incomplete=True)
    assert f.reads == []


def test_metadata_partial_stays_unassessed_without_authority_and_modes_refuse(public_boundary, monkeypatch):
    f = public_boundary
    monkeypatch.setattr(reader, '_authorize', lambda *args: pytest.fail('metadata-only read requested reveal'))
    report = reader.read_protected_e3_result(selected=f.selected, artifact_writer=f.writer,
        run_id=f.run_id, allow_partial=True)
    assert report['scientific_status'] == 'UNASSESSED' and report['assessment'] is None
    assert f.reads == []
    with pytest.raises(ValueError, match='explicit result-read selection'):
        reader.read_protected_e3_result(selected=f.selected, artifact_writer=f.writer,
            run_id=f.run_id, allow_partial=True, assess_incomplete=True)


def test_programme_dispatches_explicit_scientific_assessment_on_operationally_blocked_campaign(public_boundary, monkeypatch, tmp_path):
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
    from empirical_lawhood.api.results import ApiResult, CampaignStatusRequest, OperationStatus
    f = public_boundary
    result = ApiResult('campaign.status', OperationStatus.BLOCKED)
    monkeypatch.setattr(ExperimentProgrammeService, '_prospective_context', lambda *args, **kwargs:
        (f.selected, SimpleNamespace(campaign_status=lambda *args, **kwargs: result)))
    programme = ExperimentProgrammeService(tmp_path, f.writer)
    assert 'scientific_result' not in programme.read(directory=tmp_path, request=CampaignStatusRequest(f.run_id))
    report = programme.read(directory=tmp_path, request=CampaignStatusRequest(f.run_id),
        reveal_authority_id='reveal.disclosed', assess_incomplete=True)
    assert report['status'] == 'BLOCKED'
    assert report['scientific_result']['scientific_completion'] == 'UNPUBLISHED_INCOMPLETE_ASSESSMENT'
    assert report['scientific_result']['adjudication'] is None


def test_current_task_preparation_does_not_renew_effect_authority(actual_issued_current_task_controls, monkeypatch):
    from empirical_lawhood.api import current_task_custody
    from tests.test_current_result_historical_access import LaterClock
    f = actual_issued_current_task_controls
    monkeypatch.setattr(current_task_custody, 'datetime', LaterClock)
    package, plan, task = f.custody.current_task(f.context, f.runner)
    assert package == f.control.package and plan == f.plan and task.task_id == f.context.task_id
    assert package.execution_authority.expires_at_utc < '2030-01-01T00:00:00Z'
    with pytest.raises(PermissionError, match='exact prepared effect contract'):
        f.custody.require_native_entry(f.context, f.runner, prepared_contract=object())
    assert not f.control.executor.invocations


def test_incomplete_assessment_support_is_an_explicit_owning_declaration():
    from empirical_lawhood.api.domain_composition.matrix_configured_protected_response.experiment_binding import EXPERIMENT_RUNTIME_BINDING
    from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding
    assert EXPERIMENT_RUNTIME_BINDING.supports_incomplete_assessment is True
    with pytest.raises(TypeError, match='explicit boolean'):
        replace(EXPERIMENT_RUNTIME_BINDING, supports_incomplete_assessment=1)
    with pytest.raises(ValueError, match='code-owned scientific reader'):
        ExperimentRuntimeBinding('disclosed.no-reader', lambda: None, supports_incomplete_assessment=True)


def test_explicit_incomplete_dispatch_refuses_an_unregistered_scientific_reader(case, monkeypatch):
    from empirical_lawhood.api import generated_experiment_runtime_bindings as generated
    from empirical_lawhood.api.experiment_scientific_read import read_prepared_experiment_science
    monkeypatch.setattr(generated, 'EXPERIMENT_RUNTIME_BINDINGS', ())
    selected = SimpleNamespace(instance=SimpleNamespace(specification=case.specification.identity))
    assert read_prepared_experiment_science(selected=selected, artifact_writer=object(), run_id='run.disclosed') is None
    with pytest.raises(ValueError, match='does not support incomplete assessment'):
        read_prepared_experiment_science(selected=selected, artifact_writer=object(), run_id='run.disclosed', assess_incomplete=True)
