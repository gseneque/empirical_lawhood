# SPDX-License-Identifier: MPL-2.0
"""Read-only source20 pairing of authentic completed forecast observations.

The caller owns receipt recovery, read-only stream opening and durable retention
of each yielded complete assessment. This module neither enters native work nor
publishes products. All 108 selected uses retain their 96 distinct original
comparisons and twelve explicit equal-condition derivations. A completed census
does not admit a model or close event, suffix or clock uncertainty.
"""

from dataclasses import dataclass

from empirical_lawhood.kernel.provenance import ObjectIdentity

from . import durable_roster as roster
from . import forecast_state_census as census
from . import forecast_state_control as state
from . import forecast_step_control as step
from . import lossless_segment_consumer as consumer
from . import segmented_evidence as evidence
from . import segmented_contracts as contracts
from . import segmented_fidelity_stream as paired
from . import segmented_qualification as qualification


@dataclass(frozen=True, slots=True)
class ForecastObservationReference:
    """Exact compact identities, excluding scalar traces and full boundary vectors."""

    configuration: ObjectIdentity
    trace: ObjectIdentity
    evidence: ObjectIdentity
    assignment: ObjectIdentity
    summary: ObjectIdentity

    def __post_init__(self):
        for row, schema in ((self.configuration, contracts.SegmentedNativeConfig.SCHEMA),
                (self.trace, contracts.SegmentedTrace.SCHEMA), (self.evidence, evidence.SegmentedNativeEvidence.SCHEMA),
                (self.assignment, step.ForecastStepEvidence.SCHEMA), (self.summary, qualification.SegmentedTraceSummary.SCHEMA)):
            if type(row) is not ObjectIdentity or row.object_schema != schema:
                raise ValueError("forecast observation reference changes complete original scientific identities")
            row.__post_init__()


@dataclass(frozen=True, slots=True, weakref_slot=True)
class ForecastObservation:
    """Original completed operands; equal-condition uses are not observations."""

    evidence: evidence.SegmentedNativeEvidence
    assignment: step.ForecastStepEvidence
    summary: qualification.SegmentedTraceSummary

    def __post_init__(self):
        if (type(self.evidence) is not evidence.SegmentedNativeEvidence
                or type(self.assignment) is not step.ForecastStepEvidence
                or type(self.summary) is not qualification.SegmentedTraceSummary):
            raise ValueError("forecast observation requires exact typed completed original operands")
        for record in (self.evidence, self.assignment, self.summary):
            record.__post_init__()
        trace = self.evidence.trace
        if (self.summary.condition_reuse is not None or self.summary.configuration != trace.config
                or self.summary.trace != step.identity(trace, "trace_id")
                or self.assignment.original_native_receipt != self.evidence.native_receipt):
            raise ValueError("forecast observation changes its original trace, assignment receipt or derived-use status")
        preparation = evidence.assess_preparation_evidence(trace.config, self.evidence)
        if self.summary != qualification.summarize_trace(trace, preparation, self.summary.segment_assessments):
            raise ValueError("forecast observation changes independently recomputed preparation, receiver or actual cost")

    @property
    def configuration(self):
        return step.identity(self.evidence.trace.config, "config_id")

    @property
    def reference(self):
        return ForecastObservationReference(self.configuration, self.summary.trace,
            step.identity(self.evidence, "evidence_id"), step.identity(self.assignment, "evidence_id"),
            step.identity(self.summary, "summary_id"))


def _require_observation(control, selected, observation):
    if type(observation) is not ForecastObservation:
        raise ValueError("forecast pairing requires its complete original observation")
    observation.__post_init__()
    state.require_forecast_assignment(control, selected, observation.assignment, observation.evidence)


def assess_pair(control, selected, left, right, left_port, right_port, *, temporary_file):
    """Exhaust two authentic original streams and check their independent summaries.

    Every raw knot, state component, returned derivative and call is consumed.
    The supplied summaries are checked against preparation and segment products
    independently recomputed from those exact streams, including failed traces.
    """
    state.require_algorithm_sources(control)
    for observation in (left, right):
        _require_observation(control, selected, observation)
    metadata = left.assignment, right.assignment
    assignments = tuple(row.assignment for row in metadata if row.assignment is not None)
    with consumer.numerical_consumer_scope(temporary_file=temporary_file, assignments=assignments):
        result = state.assess_streams(control, selected,
            paired.FullStateStreamOperand(left.evidence, left_port),
            paired.FullStateStreamOperand(right.evidence, right_port), metadata)
    for observation, preparation, segments in zip((left, right), result.preparations, result.segment_assessments, strict=True):
        if observation.summary != qualification.summarize_trace(observation.evidence.trace, preparation, segments):
            raise ValueError("forecast pair disagrees with the independently assessed complete original summary")
    return result


def selected_pairs(control, selected, receiver):
    """Recover all distinct pair operands from the complete independent receiver."""
    state.require_algorithm_sources(control)
    if (type(selected) is not roster.FrozenForecastRoster
            or step.identity(selected, "roster_id") != control.native_policy.selected_roster
            or type(receiver) is not qualification.SegmentedFidelityQualification
            or receiver != qualification.qualify_fidelity(receiver.method_qualifications, receiver.fidelity_comparisons)
            or any(row.roster.original_selection != selected for row in receiver.method_qualifications)):
        raise ValueError("forecast pair plan changes selected source or complete independent receiver denominator")
    stock = {}
    for a, b in zip(receiver.method_qualifications, receiver.method_qualifications[1:]):
        for left, right in zip(a.summaries, b.summaries, strict=True):
            actual = tuple(row.configuration if row.condition_reuse is None else row.condition_reuse.observed_configuration
                for row in (left, right))
            for configuration in actual:
                step.require_config(control.native_policy, selected, configuration)
            key = tuple(step.identity(row, "config_id") for row in actual)
            expected = tuple(row.trace for row in (left, right))
            if key in stock and stock[key] != expected:
                raise ValueError("forecast pair plan substitutes a trace in an equal-condition use")
            stock[key] = expected
    if len(stock) != 96:
        raise ValueError("forecast pair plan omits its ninety-six distinct original comparisons")
    return tuple((key, stock[key]) for key in sorted(stock, key=lambda rows: tuple(row.object_id for row in rows)))


def assess_complete_pairs(control, selected, receiver, references, load_observation, open_stream, *, temporary_file):
    """Yield each complete product for immediate caller-owned durable retention.

    Only exact identity references and the current pair are resident. The caller
    loads each original through its retained receipts and opens both streams
    through its selected authenticated artifact plane as context managers.
    Streams close and complete packets release before each yield. A read or guard
    failure remains an exception; it cannot manufacture an assessment or a
    complete census. Successful return yields all 96 distinct comparisons;
    ``census.join_complete_state`` performs the final 108-use outcome join.
    """
    plan = selected_pairs(control, selected, receiver)
    rows = tuple(references)
    if any(type(row) is not ForecastObservationReference for row in rows):
        raise ValueError("forecast pair references substitute original typed identities")
    for row in rows:
        row.__post_init__()
    stock = {row.configuration: row for row in rows}
    required = {configuration for key, _ in plan for configuration in key}
    if len(stock) != len(rows) or set(stock) != required or len(rows) != 144:
        raise ValueError("forecast pair observations omit, duplicate or add selected original forecasts")
    summaries = {step.identity(row.configuration, "config_id"): step.identity(row, "summary_id")
        for product in receiver.method_qualifications for row in product.summaries if row.condition_reuse is None}
    if set(summaries) != required or any(row.summary != summaries[row.configuration] for row in rows):
        raise ValueError("forecast pair references change exact independently assessed original summaries")
    for key, traces in plan:
        if tuple(stock[configuration].trace for configuration in key) != traces:
            raise ValueError("forecast pair observations change actual selected trace identities")
    for key, _ in plan:
        left, right = (load_observation(stock[configuration]) for configuration in key)
        for observed, reference in zip((left, right), (stock[configuration] for configuration in key), strict=True):
            _require_observation(control, selected, observed)
            if observed.reference != reference:
                raise ValueError("loaded forecast observation substitutes its committed receipt operands")
        del observed
        with open_stream(left) as left_port, open_stream(right) as right_port:
            result = assess_pair(control, selected, left, right, left_port, right_port, temporary_file=temporary_file)
        del left, right, left_port, right_port
        yield result


def join_complete_pairs(control, selected, receiver, assessments):
    """Compact actual products only, then preserve the complete selected census."""
    selected_pairs(control, selected, receiver)
    conclusions = []
    for row in assessments:
        if type(row) is not state.ForecastStateStream or row.scientific_control != control:
            raise ValueError("completed forecast pair substitutes its committed scientific control")
        conclusions.append(census.compact_assessment(row))
    return census.join_complete_state(receiver, conclusions)
