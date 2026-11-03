# SPDX-License-Identifier: MPL-2.0
"""Actual exposed lossless pairing and complete adverse census; no native work."""

from contextlib import contextmanager
from dataclasses import replace
from decimal import Decimal as D
from io import BytesIO
from types import SimpleNamespace as N
import weakref

import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as contracts
from empirical_lawhood.adapters.methods.battery_refined_inquiry import forecast_state_orchestration as orchestration
from empirical_lawhood.adapters.methods.battery_refined_inquiry import forecast_step_control as step
from empirical_lawhood.adapters.methods.battery_refined_inquiry import lossless_evidence_stream as stream
from empirical_lawhood.adapters.methods.battery_refined_inquiry import lossless_segment_consumer as consumer
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_contracts as sc
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_evidence as evidence
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_qualification as qualification
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_roster as segmented
from empirical_lawhood.adapters.methods.battery_refined_inquiry import source_derived_preparation as roots
from empirical_lawhood.adapters.methods.battery_segmented_inquiry.evidence_stream import SegmentStreamHeader
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.status import OperationalStatus
from tests.test_battery_forecast_state_control import selected as selected_fixture
from tests.test_battery_forecast_step_control import failed_assignment_evidence
from tests.test_battery_lossless_segment_integration import selected_preparation, selected_stream
from tests.test_battery_segmented_fidelity import _receipt, prepared as prepared_fixture
from tests.test_battery_segmented_qualification import failed_trace, uncertain

selected, prepared = selected_fixture, prepared_fixture


def port(payload):
    return N(size_bytes=len(payload), read=BytesIO(payload).read)


def observed_stream(prepared, selected, directory, temporary_file, *, horizon, changed_state=None):
    original, selected_roster, control = selected
    selected_step = original, selected_roster, control.native_policy
    operand, assignment = selected_stream(prepared, selected_step, directory, temporary_file,
        horizon=horizon, changed_state=changed_state)
    payload = operand.port.read()
    original_evidence = operand.evidence
    template = failed_assignment_evidence(selected_step, original_evidence.trace.config, directory / 'template')
    definition = template.original_native_definition
    completion = replace(template.original_native_completion, operational_status=OperationalStatus.SUCCEEDED,
        output_ids=('forecast-step-assignment', 'forecast-step-policy'), omitted_output_ids=(), reason_codes=())
    records = (original_evidence.trace, original_evidence.protocol, original_evidence.source_assignment,
        original_evidence.layout, original_evidence.requested_initial, original_evidence.actual_initial,
        original_evidence.initial_derivative, original_evidence.actual_terminal, original_evidence.terminal_derivative)
    receipt = _receipt(directory / 'assigned-main', (*records, control.native_policy, assignment, completion),
        inputs=definition.input_materialization_ids, definition=definition)
    observed = replace(original_evidence, native_receipt=receipt)
    metadata = step.ForecastStepEvidence('evidence.assigned.' + observed.trace.config.config_id,
        control.native_policy, assignment, definition, completion, receipt)
    summary = consumer.assess_trace(observed.trace.config, observed, port(payload), temporary_file=temporary_file)
    return orchestration.ForecastObservation(observed, metadata, summary), payload


@pytest.mark.parametrize('changed_state', (None, (0, .01), (173, .01)))
def test_complete_actual_arrays_keep_negative_suffix_and_fixed_comparison_budget(selected, prepared, tmp_path, changed_state):
    selected_step = selected[0], selected[1], selected[2].native_policy
    prepared = selected_preparation(prepared, selected_step)
    temporary_file = stream.selected_temporary_files(tmp_path)
    left, left_payload = observed_stream(prepared, selected, tmp_path / 'left', temporary_file, horizon=60)
    right, right_payload = observed_stream(prepared, selected, tmp_path / 'right', temporary_file,
        horizon=30, changed_state=changed_state)
    previous = consumer.paired._Cursor, consumer.local._assess_operand, consumer.local._residual, consumer.local.assess_interval
    result = orchestration.assess_pair(selected[2], selected[1], left, right,
        port(left_payload), port(right_payload), temporary_file=temporary_file)
    assert result.declared_segment_counts == (1, 1) and result.original_retained_native_knots == (2, 2)
    assert result.compared_rhs_components == 173 * 31 and result.compared_algebraic_components == 31
    assert result.compared_derivative_components == 174 * 31
    assert result.scientific_control.native_policy.comparison_budget.rtol == D('1e-7')
    assert result.scientific_control.native_policy.comparison_budget.atol == D('1e-8')
    assert left.assignment.assignment.numerical_view.rtol == D('1e-9')
    assert result.disposition is (A.UNEVALUABLE if changed_state is None else A.FALSIFIED)
    assert {'unpaired-actual-terminal-suffix', 'actual-terminal-clocks-differ'}.issubset(result.reason_codes)
    assert previous == (consumer.paired._Cursor, consumer.local._assess_operand, consumer.local._residual, consumer.local.assess_interval)
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result


@pytest.fixture(scope='module')
def guarded_pair(tmp_path_factory):
    selected, prepared = selected_fixture.__wrapped__(), prepared_fixture.__wrapped__()
    selected_step = selected[0], selected[1], selected[2].native_policy
    prepared = selected_preparation(prepared, selected_step)
    directory = tmp_path_factory.mktemp('forecast-pair-guard-controls')
    temporary_file = stream.selected_temporary_files(directory)
    left, left_payload = observed_stream(prepared, selected, directory / 'left', temporary_file, horizon=60)
    right, right_payload = observed_stream(prepared, selected, directory / 'right', temporary_file, horizon=30)
    return selected, left, right, left_payload, right_payload, temporary_file


@pytest.mark.parametrize('damage', ('hidden-knots', 'truncated-stream', 'wrong-assignment-receipt'))
def test_complete_pair_refuses_substituted_summary_bytes_or_assignment_and_restores_hooks(guarded_pair, damage):
    selected, left, right, left_payload, right_payload, temporary_file = guarded_pair
    if damage == 'hidden-knots':
        assessment = replace(right.summary.segment_assessments[0], retained_native_knots=1)
        summary = qualification.summarize_trace(right.evidence.trace, right.summary.preparation, (assessment,))
        right = replace(right, summary=summary)
    elif damage == 'truncated-stream':
        right_payload = right_payload[:-1]
    else:
        # Bypass construction to verify the consumer revalidates independently
        # decoded inputs before opening any stream, rather than trusting types.
        forged = object.__new__(orchestration.ForecastObservation)
        for name, value in (('evidence', right.evidence), ('summary', right.summary), ('assignment', left.assignment)):
            object.__setattr__(forged, name, value)
        right = forged
        left_payload = right_payload = b''
    previous = consumer.paired._Cursor, consumer.local._assess_operand, consumer.local._residual, consumer.local.assess_interval
    with pytest.raises(ValueError):
        orchestration.assess_pair(selected[2], selected[1], left, right,
            port(left_payload), port(right_payload), temporary_file=temporary_file)
    assert previous == (consumer.paired._Cursor, consumer.local._assess_operand, consumer.local._residual, consumer.local.assess_interval)


def failed_observation(selected, configuration, original_protocol, directory):
    selected_step = selected[0], selected[1], selected[2].native_policy
    template = failed_assignment_evidence(selected_step, configuration, directory / 'template')
    definition, completion = template.original_native_definition, template.original_native_completion
    trace = failed_trace(configuration)
    protocol = replace(original_protocol, configuration=step.identity(configuration, 'config_id'),
        source=configuration.preparation.source, parameter_source=configuration.preparation.parameter_source,
        model_family='DFN' if 'dfn' in configuration.model_view else 'SPMe',
        electrode_points=configuration.numerical_view.electrode_points, particle_points=configuration.numerical_view.particle_points,
        initial_temperature_k=configuration.initial_temperature_k)
    receipt = replace(_receipt(directory / 'failed-main', (trace, protocol, selected[2].native_policy, completion),
        inputs=definition.input_materialization_ids, definition=definition), operational_status=OperationalStatus.FAILED,
        reason_codes=completion.reason_codes)
    observed = evidence.SegmentedNativeEvidence('evidence.' + configuration.config_id, trace, protocol,
        None, None, None, None, None, None, None, receipt)
    metadata = step.ForecastStepEvidence('evidence.assignment.' + configuration.config_id,
        selected[2].native_policy, None, definition, completion, receipt)
    header = stream.LosslessEvidenceLine(0, 0, 'HEADER', SegmentStreamHeader(step.identity(trace, 'trace_id'),
        step.identity(protocol, 'protocol_id'), 0).canonical_bytes().decode(), None, None)
    payload = header.canonical_bytes()
    summary = consumer.assess_trace(configuration, observed, port(payload), temporary_file=lambda: None)
    return orchestration.ForecastObservation(observed, metadata, summary), payload


@pytest.fixture(scope='module')
def complete_failed(tmp_path_factory):
    selected, prepared = selected_fixture.__wrapped__(), prepared_fixture.__wrapped__()
    tmp_path = tmp_path_factory.mktemp('forecast-pair-complete-adverse')
    selected_roster = selected[1]
    stocks = {stock: (root, roots.assess_source_roots(root)) for stock in ('Chen2020', 'ORegan2022')
        for root in (roots.supply_source_roots(contracts.identity(selected_roster.source), stock),)}
    rosters = tuple(segmented.freeze_segmented_roster(selected_roster, uncertain(),
        sc.SegmentedMethodProtocol('method.exposed.' + str(n), D(n)), stocks) for n in (60, 30, 15))
    observations, payloads, products, all_traces = [], {}, [], []
    for roster in rosters:
        summaries, traces = {}, {}
        for group in segmented.distinct_forecast_groups(roster):
            configuration = roster.configurations[group[0]]
            observation, payload = failed_observation(selected, configuration, prepared[1], tmp_path / configuration.config_id)
            observations.append(observation)
            payloads[observation.configuration] = payload
            for index in group:
                current = roster.configurations[index]
                summaries[current.config_id] = observation.summary if index == group[0] else qualification.reuse_summary(current, observation.summary)
                traces[current.config_id] = observation.evidence.trace
        comparisons = tuple(qualification.compare_traces(traces[a], traces[b], summaries[a], summaries[b])
            for a, b in roster.comparison_config_pairs)
        products.append(qualification.qualify_summaries(roster, tuple(summaries.values()), comparisons))
        all_traces.append(traces)
    fidelity = tuple(qualification.compare_traces(at[left.configuration.config_id], bt[right.configuration.config_id], left, right,
        comparison_kind='SEGMENT_FIDELITY') for (a, at), (b, bt) in zip(zip(products, all_traces), zip(products[1:], all_traces[1:]))
        for left, right in zip(a.summaries, b.summaries, strict=True))
    return qualification.qualify_fidelity(tuple(products), fidelity), tuple(observations), payloads


def test_actual144_failed_originals_yield96_complete_pairs_and108_selected_uses(selected, complete_failed, tmp_path):
    receiver, observations, payloads = complete_failed
    entered, closed, loaded = [], [], []
    stock = {row.configuration: row for row in observations}

    def load_observation(reference):
        # Each new complete packet must be released before the next result is
        # yielded, even though the exposed fixture retains its original stock.
        original = replace(stock[reference.configuration])
        loaded.append(weakref.ref(original))
        assert sum(row() is not None for row in loaded) <= 2
        return original

    @contextmanager
    def open_stream(observation):
        entered.append(observation.configuration)
        try:
            yield port(payloads[observation.configuration])
        finally:
            closed.append(observation.configuration)

    products = []
    references = tuple(row.reference for row in observations)
    for product in orchestration.assess_complete_pairs(selected[2], selected[1], receiver, reversed(references),
            load_observation, open_stream, temporary_file=stream.selected_temporary_files(tmp_path)):
        assert len(entered) == len(closed)
        assert not any(row() is not None for row in loaded)
        assert product.disposition is A.UNEVALUABLE and product.declared_segment_counts == (0, 0)
        products.append(product)
    result = orchestration.join_complete_pairs(selected[2], selected[1], receiver, reversed(products))
    assert len(products) == 96 and len(entered) == len(closed) == 192
    assert len(result.selected_uses) == 108 and len(result.conclusions) == 96
    assert sum(bool(row.equal_condition_derivations) for row in result.selected_uses) == 12
    assert result.disposition is A.UNEVALUABLE and receiver.selected_model is None
    assert receiver.selected_forecast_slots == 162 and receiver.distinct_forecast_effects == 144
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result


@pytest.mark.parametrize('damage', ('omit', 'duplicate', 'trace', 'source'))
def test_incomplete_or_substituted_panel_refuses_before_opening_any_arrays(selected, complete_failed, tmp_path, damage):
    receiver, observations, _ = complete_failed
    references = tuple(row.reference for row in observations)
    control = selected[2]
    if damage == 'omit':
        references = references[:-1]
    elif damage == 'duplicate':
        references = (*references[:-1], references[0])
    elif damage == 'source':
        control = replace(control, interval_algorithm_source_sha256='f' * 64)
    else:
        comparison = replace(receiver.fidelity_comparisons[0], left_trace=observations[-1].summary.trace)
        receiver = replace(receiver, fidelity_comparisons=(comparison, *receiver.fidelity_comparisons[1:]))

    def forbidden_open(_):
        pytest.fail('an invalid scientific panel opened arrays')

    with pytest.raises(ValueError):
        tuple(orchestration.assess_complete_pairs(control, selected[1], receiver, references,
            forbidden_open, forbidden_open, temporary_file=stream.selected_temporary_files(tmp_path)))
