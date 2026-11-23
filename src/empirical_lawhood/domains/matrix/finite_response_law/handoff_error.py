# SPDX-License-Identifier: MPL-2.0
"""Evaluator-only decomposition of a sealed Tier 1 response forecast in native units."""

from decimal import Decimal, localcontext

import numpy as np

from empirical_lawhood.science.identity.provenance import ObjectIdentity

from .control_closeout import FiniteResponseLawRootSealedControl
from .control_reveal import FiniteResponseLawProspectiveRootEvaluation
from .evaluation_native_records import FiniteResponseLawEvaluationViewObservation
from .law_payloads import FiniteResponseLawLowerPayload
from .method_records import FiniteResponseLawQualificationReport
from .paired_assay import positive_pair_readouts


def _signed_differences(
    forecast: Decimal | None, observed_handoff: Decimal | None, native: Decimal | None,
) -> tuple[Decimal | None, Decimal | None, Decimal | None]:
    """Preserve each available difference and exact addition across decimal exponents."""
    present = [d for d in (forecast, observed_handoff, native) if d is not None]
    with localcontext() as context:
        if present:
            context.prec = max(1, max(d.adjusted() for d in present) - min(d.as_tuple().exponent for d in present) + 3)
        return (
            None if forecast is None or observed_handoff is None else forecast - observed_handoff,
            None if observed_handoff is None or native is None else observed_handoff - native,
            None if forecast is None or native is None else forecast - native,
        )


def _error_rows(readouts, chart, forecast_means, observed_means):
    rows = []
    for pair, word, readout, delivered in readouts:
        for index, native in enumerate(readout.values):
            offset = len(chart.output_ids) * pair + index
            projected = None if forecast_means is None else forecast_means[offset]
            observed = None if observed_means is None else observed_means[offset]
            scoreable = native is not None and (delivered if index < 2 else readout.source_valid)
            first, second, total = _signed_differences(projected, observed, native if scoreable else None)
            rows.append({
                "magnitude": int(word.magnitude), "direction_index": word.direction_index,
                "purpose": readout.purpose, "refinement": readout.refinement,
                "quantity": chart.output_ids[index], "unit": chart.output_units[index],
                "sealed_prediction": projected, "observed_handoff_prediction": observed,
                "native_measurement": native, "native_scoreable": scoreable,
                "signed_mates_delivered": delivered, "use_valid": readout.source_valid,
                "handoff_error": first, "downstream_error": second, "total_error": total,
            })
    return rows


def revealed_handoff_errors(
    *, sealed: FiniteResponseLawRootSealedControl, revealed: FiniteResponseLawProspectiveRootEvaluation,
    views: tuple[FiniteResponseLawEvaluationViewObservation, ...],
    qualification: FiniteResponseLawQualificationReport, lower: FiniteResponseLawLowerPayload,
):
    """Trace the original composed forecast through the same F at the observed handoff.

    The caller supplies the actual revealed root, authenticated views and published
    calibrated F. Selectors and admission intervals stay sealed. The three differences
    are forecast minus observed-handoff F, observed-handoff F minus native, and
    forecast minus native. Measured values, numerical views and masks stay distinct.
    """
    if not (
        isinstance(sealed, FiniteResponseLawRootSealedControl)
        and isinstance(revealed, FiniteResponseLawProspectiveRootEvaluation)
        and isinstance(qualification, FiniteResponseLawQualificationReport)
        and type(lower) is FiniteResponseLawLowerPayload
    ):
        raise TypeError("Select the original sealed and revealed evaluation, qualification and lower payload")
    forecast = sealed.join.lock.forecast
    root = forecast.root
    if (
        revealed.sealed != ObjectIdentity.from_record(sealed.result_id, sealed)
        or any(u.root_id != root.stage_unit for u in revealed.units)
        or forecast.qualification != ObjectIdentity.from_record(qualification.report_id, qualification)
        or lower.fingerprint() != qualification.publications[0].content_sha256
        or not qualification.eligible_for_prospective_evaluation
        or tuple(v.root for v in views) != (root, root)
        or tuple(v.refinement for v in views) != (1, 2)
        or tuple(ObjectIdentity.from_record(v.report_id, v) for v in views) != sealed.views
        or views[0].handoff_interface != sealed.join.handoff
    ):
        raise ValueError("Handoff-error operands differ from the sealed views, reveal or qualified lower")
    table = next((t for t in forecast.tables if t.boundary == "composed"), None)
    point = None if table is None else table.point_mean
    actual_support, rows = observed_handoff_errors(views, lower, point)
    return {
        "root": root.stage_unit, "physical_unit": root.physical_unit_id,
        "assigned_parent": root.assigned_parent, "sealed": revealed.sealed,
        "qualification": forecast.qualification, "lower": lower.identity,
        "composed_forecast_table": None if table is None else ObjectIdentity.from_record(table.table_id, table),
        "primary_observed_handoff_in_support": actual_support,
        "rows": rows,
    }

def observed_handoff_errors(views, lower, sealed_means):
    """Reapply the lower at the observed handoff and score the matched signed assays."""
    root = views[0].root
    if tuple(view.root for view in views) != (root, root) or tuple(view.refinement for view in views) != (1, 2):
        raise ValueError("Handoff analysis requires both ordered views of the same assigned root")
    handoff = views[0].handoff_interface
    at_actual, actual_support = None, None
    if handoff is not None:
        if handoff.cutoff_tick != 4368:
            raise ValueError("The measured primary handoff must be at tick 4368")
        prediction = lower.predict(np.asarray([handoff.values], dtype=np.float64))
        at_actual = tuple(Decimal(format(float(x), ".17g")) if np.isfinite(x) else None for x in prediction.mean.ravel())
        actual_support = bool(prediction.supported[0])
    readouts = positive_pair_readouts(views, parent=root.assigned_parent)
    return actual_support, _error_rows(readouts, lower.chart, sealed_means, at_actual)
