"""Evaluator readout of the measured force boundary and matched receiver panels."""


from empirical_lawhood.domains.matrix.finite_response_law.instruments import REFERENCE_INSTRUMENT, reference_sketch
from empirical_lawhood.domains.matrix.finite_response_law.original_f import OriginalFiniteResponseLaw
from empirical_lawhood.domains.matrix.prepared_response.instruments import PreparedPortFrame
from empirical_lawhood.domains.matrix.six_matrix_response.response_observer import _decode

from .measurement import reduce_panel
from .phase_records import PreparationApplicabilityPanel, PreparationApplicabilityPrefix
from .records import MENU, PreparationApplicabilityMeasuredRoot, numbers
from .science import HANDOFF_TICK, SELECTION_TICK


def measured_boundary_observations(
    *, prefix: PreparationApplicabilityPrefix, panel: PreparationApplicabilityPanel,
    measured: PreparationApplicabilityMeasuredRoot, lower: OriginalFiniteResponseLaw,
) -> dict:
    """Recover the two actual port-2 forces and retain the same child assay across H/N/P.

    The caller authenticates outcome access. Every quantity is measured on a retained
    parent or signed/matched-HOLD panel. Reapplying the original lower requires its
    full frozen operand and the same prefix, panel and measurement.
    """
    if (
        not isinstance(lower, OriginalFiniteResponseLaw)
        or (measured.root_id, panel.root_id) != (prefix.root_id, prefix.root_id)
        or measured.lower_sha256 != lower.fingerprint()
        or measured.prefix_sha256 != prefix.fingerprint()
        or panel.prefix_sha256 != measured.prefix_sha256
        or measured.panel_sha256 != panel.fingerprint()
    ):
        raise ValueError("Boundary observations require the measured root's exact prefix, panel and lower law")
    result = {
        "root": measured.root_id, "complete": measured.complete,
        "measurement_sha256": measured.fingerprint(), "prefix_sha256": measured.prefix_sha256,
        "panel_sha256": measured.panel_sha256, "lower_sha256": measured.lower_sha256,
    }
    if not measured.complete:
        return dict(result, failed_phases=[
            (phase.phase, phase.schedule_index, phase.future_index, phase.word_index,
             phase.refinement, phase.disposition)
            for phase in (*prefix.phases, *panel.phases) if phase.disposition != "COMPLETE"
        ], arms=None)
    operands = reduce_panel(prefix, panel)
    if operands is None or not measured.covered_counts:
        raise ValueError("Complete boundary readout requires both native views and the assigned request census")
    handoffs, native, work = operands
    if numbers(handoffs) != measured.handoff or numbers(work) != measured.work:
        raise ValueError("The retained native handoff or work differs from the scored measurement")
    frame = PreparedPortFrame(SELECTION_TICK, _decode(prefix.frame_base64, (2, 3, 4, 4)))
    parents = {(p.schedule_index, p.refinement): p for p in panel.phases if p.phase == "parent"}
    instrument = REFERENCE_INSTRUMENT
    feature = instrument.feature_ids.index("backward-rate-force-2")
    elapsed = float(instrument.reference_tick_duration * instrument.backward_ticks)
    upper = lower.center[feature] + 6 * lower.scale[feature]
    result.update(
        upper_face=upper, force_unit="native-hs-force", rate_unit=instrument.feature_units[feature],
        validity_checks=("support", "numerical-agreement", "point-error", "interval-width",
                         "branch-preservation", "parent-work", "realised-coverage"),
        receiver_axes=("force-pair", "quantity", "future", "view"),
        force_pairs=((8, 0), (8, 1), (16, 0), (16, 1)),
        quantities=lower.chart.output_ids, units=lower.chart.output_units,
        futures=("future-1", "future-2"), refinements=(1, 2), arms=[],
    )
    for arm, schedule in enumerate(MENU):
        forces = []
        for view in (1, 2):
            parent = parents[arm, view]
            ticks = parent.history_ticks
            positions = _decode(parent.history_positions_base64, (len(ticks), 2, 3, 4, 4))
            before, after = (float(reference_sketch(positions[ticks.index(tick)], frame)[1])
                             for tick in (HANDOFF_TICK - instrument.backward_ticks, HANDOFF_TICK))
            rate = (after - before) / elapsed
            if rate != handoffs[arm, feature, view - 1]:
                raise ValueError("Measured reference forces do not recover the scored backward rate")
            forces.append(dict(refinement=view, at_4464=before, at_4496=after,
                               backward_rate=rate, inward_margin=float(upper) - rate))
        result["arms"].append(dict(
            schedule=schedule, force_observations=forces,
            validity_conjuncts=measured.conjuncts[7 * arm:7 * (arm + 1)],
            validity_maxima=measured.maxima[7 * arm:7 * (arm + 1)],
            joint_count=measured.joint_counts[arm], covered_count=measured.covered_counts[arm],
            attempted_choices=measured.attempts[arm], false_admissions=measured.false_admissions[arm],
            work_by_view=work[arm].tolist(), matched_native=native[arm].tolist(),
        ))
    return result
