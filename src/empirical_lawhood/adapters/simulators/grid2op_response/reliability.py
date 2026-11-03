# SPDX-License-Identifier: MPL-2.0
"""Complete whole-chronic saved-data reduction with explicit delivered service.

Arithmetic is descriptive and exact. It establishes neither calibrated future
risk nor source qualification. Action substitution, refusal and fallback are
reported alongside their measured service consequences; none is presumed safe.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from fractions import Fraction

from empirical_lawhood.kernel.provenance import ObjectIdentity

from .contracts import Grid2OpSourceBinding
from .reliability_contracts import (
    GridDeliveredEnergyReceiver, GridEpisodeReliability, GridEpisodeRole,
    GridEpisodeTermination, GridOperatingEpisodeContext, GridReliabilityDisposition,
    GridReliabilityPanel, GridReliabilityRequirement, GridSavedOperatingEpisode,
    GridServiceInterval, _ids,
)


def exact_decimal(value: Fraction) -> Decimal:
    """Convert sums of finite source Decimals without caller-context rounding."""
    denominator, twos, fives = value.denominator, 0, 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    if denominator != 1:
        raise ValueError("grid source arithmetic is not a terminating exact Decimal")
    scale = max(twos, fives)
    coefficient = value.numerator * 2 ** (scale - twos) * 5 ** (scale - fives)
    return Decimal((int(coefficient < 0), Decimal(abs(coefficient)).as_tuple().digits, -scale))


def validate_reliability_inputs(source, receiver, requirement):
    for record, kind in ((source, Grid2OpSourceBinding), (receiver, GridDeliveredEnergyReceiver),
            (requirement, GridReliabilityRequirement)):
        if type(record) is not kind:
            raise TypeError("grid reliability requires its exact source, actual receiver and selected criterion")
        record.__post_init__()
    identity = ObjectIdentity.from_record(source.binding_id, source)
    if (receiver.source_binding != identity or requirement.source_binding != identity
            or requirement.receiver != receiver.identity):
        raise ValueError("grid reliability source, actual service receiver and criterion differ")
    return identity


def assess_grid_episode_intervals(*, source, receiver, requirement, context, intervals):
    """Consume every original interval once, including an explicitly partial tail.

    An iterable permits the same scientific consumer to assess bounded dataset
    slices. A partial prefix never supplies a complete-episode service success.
    """
    identity = validate_reliability_inputs(source, receiver, requirement)
    if type(context) is not GridOperatingEpisodeContext:
        raise TypeError("grid reliability needs its exact original operating-episode context")
    context.__post_init__()
    chronic = next((row for row in source.chronic_bindings
        if ObjectIdentity.from_record(row.chronic_id, row) == context.chronic), None)
    if (context.source_binding != identity or context.receiver != receiver.identity or chronic is None):
        raise ValueError("grid episode changes its exact source, whole chronic or actual service receiver")
    count = thermal = illegal = ambiguous = unrealized = forecasts = refusals = fallbacks = 0
    totals = {name: Fraction(0) for name in ("demanded_energy_mwh", "delivered_energy_mwh",
        "redispatch_magnitude_mwh", "curtailed_energy_mwh", "runtime_seconds")}
    missing = set()
    reasons = set(context.reason_codes)
    incomplete_receiver = backend_error = False
    previous_done = False
    initial_time = datetime.strptime(chronic.initial_timestamp_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    for row in intervals:
        if type(row) is not GridServiceInterval:
            raise TypeError("grid reliability iterable substitutes its declared interval record")
        row.__post_init__()
        step = row.native_step
        count += 1
        expected_time = (initial_time + timedelta(seconds=count * chronic.timestep_seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")
        if (count > chronic.maximum_steps or previous_done or context.first_observation_sequence is None
                or step.branch_id != context.branch_id or step.horizon_step != count
                or step.environment_tick != count or row.duration_seconds != chronic.timestep_seconds
                or step.timestamp_utc != expected_time):
            raise ValueError("grid reliability requires the original consecutive complete-chronic clock and nested branch")
        previous_done = step.done
        reasons.update(step.reason_codes)
        if row.forecast_available and not chronic.forecasts_available:
            raise ValueError("grid interval claims forecasts absent from its selected exact source")
        for name in totals:
            value = getattr(row, name)
            if value is None:
                missing.add(name)
            else:
                totals[name] += Fraction(value)
        incomplete_receiver |= row.demanded_energy_mwh is None or step.maximum_rho is None
        thermal += step.maximum_rho is not None and step.maximum_rho > requirement.maximum_rho
        illegal += step.action_illegal
        ambiguous += step.action_ambiguous
        unrealized += not step.realization_observed
        forecasts += not row.forecast_available
        refusals += row.supplier_refused
        fallbacks += row.fallback_used
        backend_error |= step.has_error
    if context.termination is GridEpisodeTermination.COMPLETED:
        if count != chronic.maximum_steps or backend_error:
            raise ValueError("completed grid episode omits the whole chronic or retains a backend error")
    elif context.termination is GridEpisodeTermination.PREMATURE_TERMINAL:
        if not count or count >= chronic.maximum_steps or not previous_done or backend_error:
            raise ValueError("premature grid terminal semantics differ from its actual native prefix")
    elif context.termination is GridEpisodeTermination.BACKEND_DIVERGENCE:
        if not backend_error or not previous_done:
            raise ValueError("grid backend divergence lacks its actual terminal native observation")
    elif context.termination is GridEpisodeTermination.NOT_ENTERED and count:
        raise ValueError("unentered grid episode contains native observations")
    if (backend_error and context.termination is not GridEpisodeTermination.BACKEND_DIVERGENCE
            or previous_done and count < chronic.maximum_steps and context.termination not in (
                GridEpisodeTermination.BACKEND_DIVERGENCE, GridEpisodeTermination.PREMATURE_TERMINAL)):
        raise ValueError("grid episode cannot hide an observed terminal/backend event behind another stop label")
    complete = count == chronic.maximum_steps and context.termination is GridEpisodeTermination.COMPLETED
    if not complete:
        reasons.add("GRID_WHOLE_EPISODE_INCOMPLETE")
    if incomplete_receiver or not count:
        reasons.add("GRID_DELIVERED_SERVICE_OR_THERMAL_RECEIVER_MISSING")
    if backend_error:
        reasons.add("GRID_BACKEND_DIVERGENCE_RETAINED")
    if illegal:
        reasons.add("GRID_ILLEGAL_ACTION_SUBSTITUTION_RETAINED")
    if ambiguous:
        reasons.add("GRID_AMBIGUOUS_ACTION_SUBSTITUTION_RETAINED")
    if unrealized:
        reasons.add("GRID_ACTION_REALIZATION_UNOBSERVED")
    if forecasts:
        reasons.add("GRID_UNAVAILABLE_FORECAST_RETAINED")
    if refusals:
        reasons.add("GRID_SUPPLIER_REFUSAL_RETAINED")
    if fallbacks:
        reasons.add("GRID_FALLBACK_ACTUAL_CONSEQUENCES_RETAINED")
    if missing.intersection({"redispatch_magnitude_mwh", "curtailed_energy_mwh", "runtime_seconds"}):
        reasons.add("GRID_COST_OBSERVATION_INCOMPLETE")
    values = {name: None if name in missing or not count else exact_decimal(value) for name, value in totals.items()}
    unserved = (None if values["demanded_energy_mwh"] is None
        else exact_decimal(totals["demanded_energy_mwh"] - totals["delivered_energy_mwh"]))
    unserved_lower = exact_decimal(totals["demanded_energy_mwh"] - totals["delivered_energy_mwh"])
    failed = False
    if unserved_lower > requirement.maximum_unserved_energy_mwh:
        failed = True
        reasons.add("GRID_UNSERVED_ENERGY_REQUIREMENT_FAILED")
    if thermal > requirement.maximum_thermal_violation_intervals:
        failed = True
        reasons.add("GRID_THERMAL_REQUIREMENT_FAILED")
    if context.termination is GridEpisodeTermination.PREMATURE_TERMINAL and requirement.require_complete_survival:
        failed = True
        reasons.add("GRID_SURVIVAL_REQUIREMENT_FAILED")
    disposition = (GridReliabilityDisposition.FAILED if failed else
        GridReliabilityDisposition.SATISFIED if complete and not incomplete_receiver and not backend_error
        else GridReliabilityDisposition.UNEVALUABLE)
    return GridEpisodeReliability(context.identity, context.unit_id, context.branch_id, requirement.identity,
        count, chronic.maximum_steps, values["demanded_energy_mwh"], values["delivered_energy_mwh"], unserved, unserved_lower,
        values["redispatch_magnitude_mwh"], values["curtailed_energy_mwh"], values["runtime_seconds"], thermal,
        illegal, ambiguous, unrealized, forecasts, refusals, fallbacks, context.termination, disposition,
        tuple(sorted(reasons)))


def assess_grid_saved_episode(*, source, receiver, requirement, episode):
    if type(episode) is not GridSavedOperatingEpisode:
        raise TypeError("grid saved-data assessment needs its exact original episode")
    episode.__post_init__()
    return assess_grid_episode_intervals(source=source, receiver=receiver, requirement=requirement,
        context=episode.context, intervals=episode.intervals)


def assess_grid_reliability_panel(*, panel_id, source, receiver, requirement, role,
        planned_unit_ids, branch_ids, episodes):
    """Retain the full cartesian branch census within each whole chronic unit."""
    identity = validate_reliability_inputs(source, receiver, requirement)
    _ids(planned_unit_ids, "planned grid chronic units")
    _ids(branch_ids, "nested grid branches")
    if type(role) is not GridEpisodeRole or type(episodes) is not tuple:
        raise TypeError("grid panel needs an explicit original role and exact saved episode tuple")
    chronics = {row.chronic_id: row for row in source.chronic_bindings}
    if not set(planned_unit_ids) <= set(chronics):
        raise ValueError("grid panel allocates a chronic outside its selected exact source")
    original_bytes = tuple((chronics[unit].content_sha256, chronics[unit].exogenous_event_sha256)
        for unit in planned_unit_ids)
    if len(set(original_bytes)) != len(original_bytes):
        raise ValueError("grid panel relabels identical original chronic bytes as independent units")
    expected = {(unit, branch) for unit in planned_unit_ids for branch in branch_ids}
    by_cell, episode_ids = {}, set()
    for episode in episodes:
        if type(episode) is not GridSavedOperatingEpisode:
            raise TypeError("grid panel substitutes its saved episode type")
        key = (episode.context.unit_id, episode.context.branch_id)
        if (key not in expected or key in by_cell or episode.context.role is not role
                or episode.context.episode_id in episode_ids):
            raise ValueError("grid panel duplicates, crosses roles or adds a whole-chronic/nested-branch cell")
        episode_ids.add(episode.context.episode_id)
        by_cell[key] = assess_grid_saved_episode(source=source, receiver=receiver, requirement=requirement, episode=episode)
    rows, units = [], []
    for unit in planned_unit_ids:
        local = []
        for branch in branch_ids:
            row = by_cell.get((unit, branch))
            if row is None:
                row = GridEpisodeReliability(None, unit, branch, requirement.identity, 0, chronics[unit].maximum_steps,
                    None, None, None, Decimal(0), None, None, None, 0, 0, 0, 0, 0, 0, 0,
                    GridEpisodeTermination.NOT_ENTERED, GridReliabilityDisposition.UNEVALUABLE, ("GRID_PLANNED_EPISODE_MISSING",))
            rows.append(row)
            local.append(row.disposition)
        status = (GridReliabilityDisposition.FAILED if GridReliabilityDisposition.FAILED in local else
            GridReliabilityDisposition.UNEVALUABLE if GridReliabilityDisposition.UNEVALUABLE in local else
            GridReliabilityDisposition.SATISFIED)
        units.append((unit, status))
    return GridReliabilityPanel(panel_id, identity, requirement.identity, role, planned_unit_ids,
        branch_ids, tuple(rows), tuple(units))
