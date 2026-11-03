"""Causal factor admission and tracking over one complete common lattice.

Only existing matrix algebra equations are used. Native trajectories are never
created here. Spectral identification, algebra admission and frame availability
are separate observations; unknown samples cannot become physical exits.
"""

from dataclasses import dataclass, replace
from decimal import Decimal

import numpy as np

from empirical_lawhood.adapters.methods.matrix_history_analysis import algebra

from .records import FactorLifetime, FactorObservation, FactorTrace


def decimal_measurement(value):
    """Retain the finite binary result's shortest round-trip decimal spelling."""
    value = float(value)
    if not np.isfinite(value):
        raise ValueError("factor measurement is nonfinite")
    return Decimal(repr(value))


@dataclass(frozen=True)
class SectorMeasurement:
    identifiable: bool
    spectrum: np.ndarray
    projector: np.ndarray
    basis: np.ndarray
    factor: np.ndarray | None
    associative_leakage: Decimal | None
    lie_leakage: Decimal | None
    factor_fit_angle_degrees: Decimal | None


def measure_sector(triplet, spec):
    """Own the selected admission gap without changing the historical gap rule."""
    measured = algebra.sector(triplet)
    spectrum, low = measured["spectrum"], measured["low"]
    identifiable = bool(spectrum[3] - spectrum[2] > float(spec.identifiability_relative_gap) * spectrum[-1]
                        and spectrum[3] > float(spec.identifiability_absolute_fourth))
    if not identifiable:
        return SectorMeasurement(False, spectrum, low @ low.T, low, None, None, None, None)
    metrics, fields = algebra.algebra(low)
    factor = algebra.exact_factor(fields)
    return SectorMeasurement(True, spectrum, low @ low.T, low, factor,
        decimal_measurement(metrics["associative_leakage"]),
        decimal_measurement(metrics["lie_leakage"]),
        decimal_measurement(algebra.principal_angle(low, algebra.coords(factor).T)))


def align_factor(previous, current, minimum_overlap):
    """Align the current component frame to the adjacent past frame only.

    The principal subspace angle is invariant to signs and degenerate slow
    bases. The component alignment is an orientation-preserving Procrustes
    map; singular overlap remains explicitly ambiguous.
    """
    old, new = algebra.coords(previous).T, algebra.coords(current).T
    u, singular, vh = np.linalg.svd(new.T @ old)
    signs = np.eye(3)
    handedness = np.linalg.det(u @ vh)
    signs[-1, -1] = handedness
    rotation = u @ signs @ vh
    aligned = np.einsum("ia,ijk->ajk", new @ rotation, algebra.BASIS)
    return aligned, bool(singular.min() < float(minimum_overlap) or handedness < 0), decimal_measurement(algebra.principal_angle(old, new))


def _raw_admitted(measured, spec):
    return (measured.associative_leakage <= spec.associative_leakage_maximum
            and measured.lie_leakage <= spec.lie_leakage_maximum
            and measured.factor_fit_angle_degrees <= spec.factor_fit_angle_maximum_degrees)


def _moving_state(observation, spec):
    if observation.raw_admitted is None:
        return None
    return observation.raw_admitted and (observation.adjacent_angle_degrees is None
                or observation.adjacent_angle_degrees <= spec.adjacent_angle_maximum_degrees)


def causal_observations(spec, measurements, *, unavailable=None, scalar_closure=None, initial_presence=False):
    """Admission at t reads only observations on the declared lattice through t."""
    if type(initial_presence) is not bool or initial_presence and spec.risk_start_tick != 0:
        raise ValueError("initial-presence admission requires an explicit time-zero risk rule")
    if set(measurements) != set(spec.lattice):
        raise ValueError("factor measurements must retain every requested lattice role")
    unavailable = {} if unavailable is None else unavailable
    scalar_closure = {} if scalar_closure is None else scalar_closure
    if set(unavailable) - set(spec.lattice) or set(scalar_closure) - set(spec.lattice):
        raise ValueError("factor availability/scalar receiver changes its observation lattice")
    if scalar_closure and spec.scalar_closure is None:
        raise ValueError("scalar closure comparison requires its independent normalization/threshold contract")
    observations, aligned_frames = [], {}
    previous = None
    for tick in spec.lattice:
        measured = measurements[tick]
        ratio = scalar_closure.get(tick)
        scalar_pass = None if ratio is None else ratio <= spec.scalar_closure.threshold
        if tick in unavailable or measured is None:
            status = unavailable.get(tick, "UNAVAILABLE")
            if status not in ("UNAVAILABLE", "NUMERICAL_INVALID"):
                raise ValueError("factor unavailable status differs")
            observations.append(FactorObservation(tick, status, None, None, None,
                scalar_pass, None, None, None, None, None, False, status, scalar_closure_ratio=ratio))
            previous = None
            continue
        if not measured.identifiable:
            observations.append(FactorObservation(tick, "UNIDENTIFIABLE", False, None, None,
                scalar_pass, None, None, None, None, None, False, "SLOW_SECTOR_NOT_IDENTIFIABLE", scalar_closure_ratio=ratio))
            previous = None
            continue
        frame = measured.factor
        ambiguous, angle = False, None
        if previous is not None:
            old_measurement, old_frame, prior_ambiguity = previous
            frame, ambiguous, _ = align_factor(old_frame, frame, spec.frame_alignment_minimum_overlap)
            ambiguous = ambiguous or prior_ambiguity
            angle = decimal_measurement(algebra.principal_angle(old_measurement.basis, measured.basis))
        raw = _raw_admitted(measured, spec)
        observation = FactorObservation(tick, "AVAILABLE", True, bool(raw), False,
            scalar_pass, measured.associative_leakage, measured.lie_leakage,
            measured.factor_fit_angle_degrees, angle, None, ambiguous, None, scalar_closure_ratio=ratio)
        history = (*observations, observation)
        start = tick - spec.trailing_persistence_ticks
        eligible = start >= spec.lattice[0]
        trailing = tuple(o for o in history if o.tick >= start)
        eligible = eligible and bool(trailing) and trailing[0].tick == start
        eligible = eligible and all(_moving_state(o, spec) is True for o in trailing)
        if initial_presence and tick == 0:
            eligible = raw
        observations.append(replace(observation, causal_admitted=bool(eligible)))
        aligned_frames[tick] = frame
        # A failed algebra/continuity criterion ends this component track. A
        # later factor starts a new causal frame; unstable pre-admission frames
        # must not disqualify every subsequent, independently admitted spell.
        previous = (measured, frame, ambiguous) if _moving_state(observation, spec) else None
    origin = next((o.tick for o in observations if o.tick >= spec.risk_start_tick and o.causal_admitted is True), None)
    if origin is not None:
        reference = measurements[origin].basis
        observations = [replace(o, origin_angle_degrees=decimal_measurement(algebra.principal_angle(reference, measurements[o.tick].basis)))
            if o.tick >= origin and o.identifiable is True else o for o in observations]
    return tuple(observations), aligned_frames


def lifetime(observations, spec, *, origin_fixed=False):
    """First causal admission and first observed exit; no hidden reentry scoring."""
    if tuple(o.tick for o in observations) != spec.lattice:
        raise ValueError("factor lifetime requires the entire common observation lattice")
    risk = tuple(o for o in observations if o.tick >= spec.risk_start_tick)
    origin = next((o for o in risk if o.causal_admitted is True), None)
    unknown = tuple(o.tick for o in risk if o.raw_admitted is None)
    if origin is None:
        if unknown:
            return FactorLifetime(None, "UNKNOWN", "UNKNOWN", None, None, unknown)
        return FactorLifetime(None, "NEVER_ADMITTED", "NOT_AT_RISK", None, None, ())
    preceding = tuple(o for o in risk if o.tick < origin.tick)
    onset = "LEFT_PRESENT" if origin.tick == spec.risk_start_tick else "UNRESOLVED_ADMISSION" if any(o.raw_admitted is None for o in preceding) else "OBSERVED_ADMISSION"
    last = origin.tick
    for o in risk:
        if o.tick <= origin.tick:
            continue
        state = _moving_state(o, spec)
        if origin_fixed and state is not None:
            if o.origin_angle_degrees is None:
                raise ValueError("origin-fixed lifetime lacks its causal origin projector comparison")
            state = state and o.origin_angle_degrees <= spec.origin_angle_maximum_degrees
        if state is None:
            # Even if a factor is observed again, persistence across this gap is
            # unknown; do not turn the missing sample into an exit or censor.
            missing = tuple(x.tick for x in risk if x.tick >= o.tick and x.raw_admitted is None)
            return FactorLifetime(origin.tick, onset, "UNKNOWN", last, None, missing)
        if state is False:
            return FactorLifetime(origin.tick, onset, "EXIT_INTERVAL", last, o.tick, ())
        last = o.tick
    return FactorLifetime(origin.tick, onset, "RIGHT_CENSORED", last, None, ())


def trace(spec, root, view, sector, measurements, *, diagnostics=None, diagnostic_members=(), unavailable=None, scalar_closure=None):
    observations, frames = causal_observations(spec, measurements, unavailable=unavailable, scalar_closure=scalar_closure)
    return FactorTrace(root, spec.identity, view, sector, observations,
        lifetime(observations, spec), lifetime(observations, spec, origin_fixed=True), diagnostics, diagnostic_members), frames


def scalar_closure_ratios(spec, arrays, view):
    """Original producer geometry samples; the independent scalar oracle is separate."""
    if spec.scalar_closure is None:
        return None
    from empirical_lawhood.adapters.simulators.six_matrix_response.history_source import history_native_parameters
    from empirical_lawhood.adapters.simulators.six_matrix_response.model import SixMatrixState
    from empirical_lawhood.adapters.simulators.six_matrix_response.response_observer import geometry_sample
    member, _ = history_native_parameters()
    multiplier = 1 if view == "PRIMARY" else 2
    prefix = view.lower()
    rows = {"X": {}, "Y": {}}
    for tick in spec.lattice:
        i = multiplier*tick
        x, y = arrays[f"{prefix}_alpha_tilde"][i]
        state = SixMatrixState(2, arrays[f"{prefix}_positions"][i], arrays[f"{prefix}_momenta"][i], i, float(x), float(y))
        measured = geometry_sample(state=state, member=member, refinement=multiplier)
        rows["X"][tick], rows["Y"][tick] = measured.x.closure_ratio, measured.y.closure_ratio
    return rows


def measure_trace(spec, root, view, sector, positions, *, scalar_closure=None):
    """Preserve the historical exposed trace over the shared root-free mathematics."""
    values, diagnostics = measure_trace_values(spec, view, sector, positions, scalar_closure=scalar_closure)
    return FactorTrace(root, spec.identity, view, sector, *values, None), diagnostics


def measure_trace_values(spec, view, sector, positions, *, scalar_closure=None):
    """Rescore one authenticated native history on the population's common clock.

    The caller authenticates its source bytes and original lineage before this
    pure method receives values. Dense historical h082 analysis is not consumed
    or overwritten. Fine half ticks do not enter this population lattice.
    """
    if view not in ("PRIMARY", "FINE") or sector not in spec.sectors:
        raise ValueError("factor analysis substitutes its selected sector/view")
    multiplier = 1 if view == "PRIMARY" else 2
    from empirical_lawhood.adapters.methods.matrix_dataset_readers import MatrixArrayRows
    if type(positions) is not MatrixArrayRows:
        positions = np.asarray(positions)
    if positions.ndim != 5 or positions.shape[1:] != (2, 3, 4, 4) or positions.dtype.str != "<c16" or positions.shape[0] <= multiplier*spec.lattice[-1]:
        raise ValueError("factor analysis lacks the full native position/cadence operand")
    measurements, unavailable = {}, {}
    sector_index = ("X", "Y").index(sector)
    for tick in spec.lattice:
        values = positions[multiplier*tick, sector_index]
        if not np.isfinite(values).all():
            measurements[tick] = None
            unavailable[tick] = "NUMERICAL_INVALID"
            continue
        try:
            measurements[tick] = measure_sector(values, spec)
        except np.linalg.LinAlgError:
            measurements[tick] = None
            unavailable[tick] = "NUMERICAL_INVALID"
    observations, frames = causal_observations(spec, measurements,
        unavailable=unavailable, scalar_closure=scalar_closure)
    result = (observations, lifetime(observations, spec), lifetime(observations, spec, origin_fixed=True))
    count = len(spec.lattice)
    diagnostics = {"ticks": np.asarray(spec.lattice, dtype="<i8"),
        "spectrum": np.full((count, 15), np.nan, dtype="<f8"),
        "projector": np.full((count, 15, 15), np.nan, dtype="<f8"),
        "basis": np.full((count, 15, 3), np.nan, dtype="<f8"),
        "factor": np.full((count, 3, 4, 4), np.nan, dtype="<c16"),
        "aligned_factor": np.full((count, 3, 4, 4), np.nan, dtype="<c16"),
        "available": np.zeros(count, dtype="|b1"), "identifiable": np.zeros(count, dtype="|b1")}
    for i, tick in enumerate(spec.lattice):
        value = measurements[tick]
        if value is None:
            continue
        diagnostics["available"][i] = True
        diagnostics["identifiable"][i] = value.identifiable
        for k in ("spectrum", "projector", "basis"):
            diagnostics[k][i] = getattr(value, k)
        if value.identifiable:
            diagnostics["factor"][i] = value.factor
            diagnostics["aligned_factor"][i] = frames[tick]
    return result, diagnostics


def validate_trace(trace_record, spec, *, initial_presence=False):
    """Retained reading checks reductions and rule joins without new spectra."""
    if type(initial_presence) is not bool or initial_presence and spec.risk_start_tick != 0:
        raise ValueError("initial-presence admission requires an explicit time-zero risk rule")
    if trace_record.rule != spec.identity or trace_record.sector not in spec.sectors:
        raise ValueError("retained factor trace substitutes the event rule")
    observations = trace_record.observations
    if tuple(o.tick for o in observations) != spec.lattice:
        raise ValueError("retained factor trace changes its complete lattice")
    for index, o in enumerate(observations):
        if o.scalar_closure_ratio is not None:
            if spec.scalar_closure is None or o.scalar_closure_pass != (o.scalar_closure_ratio <= spec.scalar_closure.threshold):
                raise ValueError("retained scalar closure substitutes its independent detector rule")
        if o.status != "AVAILABLE":
            continue
        expected_raw = (o.associative_leakage <= spec.associative_leakage_maximum
            and o.lie_leakage <= spec.lie_leakage_maximum
            and o.factor_fit_angle_degrees <= spec.factor_fit_angle_maximum_degrees)
        start = o.tick - spec.trailing_persistence_ticks
        trailing = tuple(x for x in observations[:index+1] if x.tick >= start)
        expected_causal = (start >= spec.lattice[0] and trailing[0].tick == start
                          and all(_moving_state(x, spec) is True for x in trailing))
        if initial_presence and o.tick == 0:
            expected_causal = expected_raw
        if o.raw_admitted != expected_raw or o.causal_admitted != expected_causal:
            raise ValueError("retained factor admission differs from its frozen criterion or causal past")
    if trace_record.moving_lifetime != lifetime(trace_record.observations, spec) or trace_record.origin_fixed_lifetime != lifetime(trace_record.observations, spec, origin_fixed=True):
        raise ValueError("retained factor lifetime differs from its complete measured observations")


def population_counts(result):
    """Whole-root denominators by family/view/sector, never pooled nested views."""
    counts = {}
    for t in result.traces:
        validate_trace(t, result.rule)
        key = (t.root.family_id, t.view, t.sector)
        row = counts.setdefault(key, {"requested_roots": 0, "admitted_roots": 0,
            "never_admitted_roots": 0, "unknown_roots": 0, "left_present_roots": 0,
            "exit_interval_roots": 0, "right_censored_roots": 0,
            "requested_observations": 0, "available_observations": 0,
            "unidentifiable_observations": 0, "unavailable_observations": 0,
            "raw_admitted_observations": 0, "causal_admitted_observations": 0,
            "scalar_comparable_observations": 0, "scalar_disagreement_observations": 0})
        row["requested_roots"] += 1
        life = t.moving_lifetime
        row["admitted_roots"] += life.origin_tick is not None
        row["never_admitted_roots"] += life.disposition == "NOT_AT_RISK"
        row["unknown_roots"] += life.disposition == "UNKNOWN"
        row["left_present_roots"] += life.onset == "LEFT_PRESENT"
        row["exit_interval_roots"] += life.disposition == "EXIT_INTERVAL"
        row["right_censored_roots"] += life.disposition == "RIGHT_CENSORED"
        for o in t.observations:
            row["requested_observations"] += 1
            row["available_observations"] += o.status == "AVAILABLE"
            row["unidentifiable_observations"] += o.status == "UNIDENTIFIABLE"
            row["unavailable_observations"] += o.status in ("UNAVAILABLE", "NUMERICAL_INVALID")
            row["raw_admitted_observations"] += o.raw_admitted is True
            row["causal_admitted_observations"] += o.causal_admitted is True
            if o.raw_admitted is not None and o.scalar_closure_pass is not None:
                row["scalar_comparable_observations"] += 1
                row["scalar_disagreement_observations"] += o.raw_admitted != o.scalar_closure_pass
    return counts


def risk_sets(result):
    """Complete family/root risk sets at a fixed post-preparation observation.

    First admissions after that cutoff are incidence records. Factors present
    at the cutoff have residual lifetimes, with unknown prior formation. No
    histories or adjacent observations are treated as independent units.
    """
    population_counts(result)
    output = {}
    for family in sorted({r.family_id for r in result.population.roots}):
        for view in ("PRIMARY", "FINE"):
            for sector in result.rule.sectors:
                traces = tuple(t for t in result.traces if (t.root.family_id, t.view, t.sector) == (family, view, sector))
                rows = []
                for tick in result.rule.lattice:
                    if tick < result.rule.risk_start_tick:
                        continue
                    row = {"tick": tick, "requested_roots": len(traces),
                        "first_causal_admissions": 0, "admitted_through_tick": 0,
                        "not_yet_admitted_known": 0, "uncertain_admission_through_tick": 0,
                        "left_present_roots": 0, "left_present_surviving": 0,
                        "left_present_exited": 0, "left_present_unknown": 0}
                    for trace_record in traces:
                        life = trace_record.moving_lifetime
                        origin = life.origin_tick
                        if origin is not None and origin <= tick:
                            row["admitted_through_tick"] += 1
                            row["first_causal_admissions"] += origin == tick
                        else:
                            prior = tuple(o for o in trace_record.observations if result.rule.risk_start_tick <= o.tick <= tick)
                            unknown = any(o.raw_admitted is None for o in prior)
                            row["uncertain_admission_through_tick" if unknown else "not_yet_admitted_known"] += 1
                        if life.onset == "LEFT_PRESENT":
                            row["left_present_roots"] += 1
                            if life.unavailable_ticks and life.unavailable_ticks[0] <= tick:
                                row["left_present_unknown"] += 1
                            elif life.exit_upper_tick is not None and life.exit_upper_tick <= tick:
                                row["left_present_exited"] += 1
                            else:
                                row["left_present_surviving"] += 1
                    rows.append(row)
                output[family, view, sector] = tuple(rows)
    return output


def eligible_origins(trace_record, spec):
    """Return causal usable frame cutoffs, with no future-duration selection."""
    validate_trace(trace_record, spec)
    return tuple(o.tick for o in trace_record.observations
        if o.tick >= spec.risk_start_tick and o.causal_admitted is True and not o.alignment_ambiguous)
