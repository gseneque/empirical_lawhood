# SPDX-License-Identifier: MPL-2.0
"""Independent literal complete-episode falsifier for saved reliability reports.

This checker does not invoke the producing reducer or its arithmetic helpers.
It checks descriptive energy/count/status claims, not physics, provenance,
transfer, calibration, qualification or authority.
"""

from fractions import Fraction
from datetime import UTC, datetime, timedelta

from empirical_lawhood.kernel.provenance import ObjectIdentity

from .reliability_contracts import (
    GridDeliveredEnergyReceiver, GridEpisodeReliability, GridEpisodeTermination,
    GridReliabilityDisposition, GridReliabilityRequirement, GridSavedOperatingEpisode,
)
from .contracts import Grid2OpSourceBinding


def independently_check_grid_reliability(*, source, receiver, requirement, episode, report):
    """Refuse a thinned denominator, altered totals, event counts or conclusion."""
    for value, kind in ((source, Grid2OpSourceBinding), (receiver, GridDeliveredEnergyReceiver),
            (requirement, GridReliabilityRequirement), (episode, GridSavedOperatingEpisode),
            (report, GridEpisodeReliability)):
        if type(value) is not kind:
            raise TypeError("independent grid check needs exact original typed operands")
        value.__post_init__()
    context, intervals = episode.context, episode.intervals
    source_identity = ObjectIdentity.from_record(source.binding_id, source)
    chronic = next((row for row in source.chronic_bindings
        if ObjectIdentity.from_record(row.chronic_id, row) == context.chronic), None)
    if (chronic is None or context.source_binding != source_identity or receiver.source_binding != source_identity
            or requirement.source_binding != source_identity or context.receiver != receiver.identity
            or requirement.receiver != receiver.identity or report.episode != context.identity
            or report.unit_id != context.unit_id or report.branch_id != context.branch_id
            or report.requirement != requirement.identity or report.expected_intervals != chronic.maximum_steps
            or report.observed_intervals != len(intervals) or report.termination is not context.termination):
        raise ValueError("independent grid check found a changed original source or complete denominator")
    start = datetime.strptime(chronic.initial_timestamp_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    for position, row in enumerate(intervals, 1):
        timestamp = (start + timedelta(seconds=position * chronic.timestep_seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")
        if (row.native_step.horizon_step != position or row.native_step.environment_tick != position
                or row.native_step.branch_id != context.branch_id or row.duration_seconds != chronic.timestep_seconds
                or row.native_step.timestamp_utc != timestamp or len(intervals) > chronic.maximum_steps
                or position < len(intervals) and row.native_step.done):
            raise ValueError("independent grid check found an omitted interval or crossed original branch")
    totals = {}
    for name in ("demanded_energy_mwh", "delivered_energy_mwh", "redispatch_magnitude_mwh",
            "curtailed_energy_mwh", "runtime_seconds"):
        observations = tuple(getattr(row, name) for row in intervals)
        expected = None if not observations or None in observations else sum(map(Fraction, observations), Fraction(0))
        observed = getattr(report, name)
        if (observed is None) != (expected is None) or expected is not None and Fraction(observed) != expected:
            raise ValueError("independent grid check found a changed exact energy or cost total")
        totals[name] = expected
    unserved = None if totals["demanded_energy_mwh"] is None else totals["demanded_energy_mwh"] - totals["delivered_energy_mwh"]
    if ((report.unserved_energy_mwh is None) != (unserved is None)
            or unserved is not None and Fraction(report.unserved_energy_mwh) != unserved):
        raise ValueError("independent grid check found a changed actual unserved energy")
    lower_bound = sum((Fraction(row.demanded_energy_mwh) - Fraction(row.delivered_energy_mwh)
        for row in intervals if row.demanded_energy_mwh is not None), Fraction(0))
    if Fraction(report.unserved_energy_lower_bound_mwh) != lower_bound:
        raise ValueError("independent grid check found omitted known unserved energy in an incomplete receiver")
    counts = {
        "thermal_violation_intervals": sum(row.native_step.maximum_rho is not None
            and row.native_step.maximum_rho > requirement.maximum_rho for row in intervals),
        "illegal_action_intervals": sum(row.native_step.action_illegal for row in intervals),
        "ambiguous_action_intervals": sum(row.native_step.action_ambiguous for row in intervals),
        "unrealized_action_intervals": sum(not row.native_step.realization_observed for row in intervals),
        "unavailable_forecast_intervals": sum(not row.forecast_available for row in intervals),
        "supplier_refusal_intervals": sum(row.supplier_refused for row in intervals),
        "fallback_intervals": sum(row.fallback_used for row in intervals),
    }
    if any(getattr(report, name) != expected for name, expected in counts.items()):
        raise ValueError("independent grid check found an omitted adverse action/forecast/fallback event")
    failure = (lower_bound > Fraction(requirement.maximum_unserved_energy_mwh)
        or counts["thermal_violation_intervals"] > requirement.maximum_thermal_violation_intervals
        or context.termination is GridEpisodeTermination.PREMATURE_TERMINAL and requirement.require_complete_survival)
    complete = (len(intervals) == chronic.maximum_steps and context.termination is GridEpisodeTermination.COMPLETED
        and bool(intervals) and all(row.demanded_energy_mwh is not None
            and row.native_step.maximum_rho is not None and not row.native_step.has_error for row in intervals))
    expected = (GridReliabilityDisposition.FAILED if failure else
        GridReliabilityDisposition.SATISFIED if complete else GridReliabilityDisposition.UNEVALUABLE)
    if report.disposition is not expected:
        raise ValueError("independent grid check found an unsupported complete-episode reliability conclusion")
    return True
