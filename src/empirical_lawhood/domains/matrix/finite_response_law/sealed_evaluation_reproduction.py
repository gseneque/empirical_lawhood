# SPDX-License-Identifier: MPL-2.0
"""Recover the bounds consumed by the six policies from original sealed and revealed operands."""

from .consumer import SPEC, finite_bound_operands, response_coordinates
from .control_delivery import _force
from .evaluation_readout import root_operands
from .evaluation_reproduction import native_prices
from .handoff_error import revealed_handoff_errors
from .law_binding import NATIVE_WORDS, output_quantities
from .paired_assay import paired_native_assay
from empirical_lawhood.science.identity.provenance import ObjectIdentity


def selected_intervals(seal, revealed, operand, views):
    """Retain the bound actually consumed, its unclipped inputs and physical intersection."""
    coords = response_coordinates(ObjectIdentity.from_record("flh-science", SPEC))
    quantities = output_quantities()
    preservation = {q.quantity_id for q in quantities[2:]}
    axis = {q.quantity_id: i for i, q in enumerate(quantities)}
    tables = {t.boundary: t for t in seal.join.lock.forecast.tables}
    locks = {p.policy_id: p for p in seal.join.lock.parents}
    designs = {p.policy_id: p for p in seal.join.lock.designs}
    outcomes = {u.policy_id: u for u in revealed.units}
    rows = []
    for event in operand.events:
        unit = outcomes[event.policy_id]
        early = locks[event.policy_id]
        row = dict(
            policy=event.policy_id,
            selected_word=event.selected_word,
            admitted=unit.admitted,
            task_success=unit.task_success,
            false_admission=unit.admitted_failure,
            handoff_permitted_use=seal.join.use_allowed,
            decision=early.decision.disposition.value,
            measured_available=event.measured_available,
            numerical_agreement=event.numerical_agreement,
            gates={
                k: getattr(unit, k).value
                for k in (
                    "native_target",
                    "delivery",
                    "preservation",
                    "numerics",
                    "probe_adequacy",
                    "probe_coverage",
                    "probe_sharpness",
                )
            },
            handoff_available=unit.handoff_available,
            dispositions=[d.value for d in unit.dispositions],
            reasons=list(unit.reason_codes),
            bounds=[],
        )
        rows.append(row)
        if event.selected_word < 0:
            if unit.admitted:
                raise ValueError("An abstention cannot be an admission")
            continue
        boundary = event.policy_id.split(".")[0]
        table = tables[boundary]
        word = NATIVE_WORDS[event.selected_word]
        if _force(early.decision.action_binding.action_word) != word:
            raise ValueError("Consumed action differs from the sealed action word")
        refinements = dict(
            zip(
                designs[event.policy_id].evaluation_plan.numerical_view_ids,
                (v.refinement for v in views),
                strict=True,
            )
        )
        observations = {
            (v.purpose, v.refinement): v
            for v in paired_native_assay(
                views, parent=seal.join.lock.forecast.root.assigned_parent, word=word
            ).readouts
        }
        pairs = [
            (r, x)
            for r, x in zip(table.requests, table.results, strict=True)
            if r.action_word and _force(r.action_word) == word
        ]
        if len(pairs) != 2 or len({x.qualification_view_id for _, x in pairs}) != 2:
            raise ValueError("Selected action requires both issued qualification views")
        for request, result in pairs:
            values = finite_bound_operands(result, coords)
            widths = {
                v.quantity_id: v.value
                for v in result.uncertainty_values
                if v.value_id.startswith("halfwidth.")
            }
            means = {v.quantity_id: v.value for v in result.response_values}
            for box in values.bounds:
                key = box.coordinate.quantity_id
                mean = means[key]
                width = widths[key]
                nu = box.numerical_floor
                low, high = box.expanded_interval
                domain = [max(0, low), max(0, high)] if key in preservation else [low, high]
                measurement = observations[
                    box.coordinate.coordinate_id.split(".")[0], refinements[result.qualification_view_id]
                ]
                observed = measurement.values[axis[key]]
                scoreable = measurement.source_valid and observed is not None
                row["bounds"].append(
                    dict(
                        qualification_view=result.qualification_view_id,
                        request_sha256=request.fingerprint(),
                        result_sha256=result.fingerprint(),
                        coordinate=box.coordinate.coordinate_id,
                        quantity=key,
                        unit=box.coordinate.unit,
                        point_mean=mean,
                        calibrated_halfwidth=width,
                        numerical_allowance=nu,
                        unexpanded=[mean - width, mean + width],
                        numerically_expanded=[mean - width - nu, mean + width + nu],
                        issued_bound_before_allowance=[box.lower, box.upper],
                        issued_expanded=[low, high],
                        physical_domain_intersection=domain,
                        precision_margin=values.precision_margin,
                        observed_selected_native=observed,
                        full_assay_scoreable=scoreable,
                        in_unexpanded=(mean - width <= observed <= mean + width) if scoreable else None,
                        in_issued_expanded=(low <= observed <= high) if scoreable else None,
                        in_physical_domain=(domain[0] <= observed <= domain[1]) if scoreable else None,
                    )
                )
        if len(row["bounds"]) != 32:
            raise ValueError("Selected action requires all 32 bounds")
    if {x["policy"] for x in rows} != set(outcomes):
        raise ValueError("Consumer policy census differs from the reveal")
    return rows


def sealed_root_readout(*, seal, reveal, views, qualification, lower, inference):
    """Re-evaluate use, response loss, exact error decomposition, selected bounds and policy costs."""
    actual = root_operands(seal, views, reveal)
    if actual != inference:
        raise ValueError("Recomputed decision or response losses differ from the issued root inference")
    row = revealed_handoff_errors(
        sealed=seal, revealed=reveal, views=views, qualification=qualification, lower=lower
    )
    forecast = seal.join.lock.forecast
    for name in ("sealed", "qualification", "lower", "composed_forecast_table"):
        if row[name] is not None:
            row[name] = row[name].to_document()
    return dict(
        row,
        forecast_sha256=forecast.fingerprint(),
        consumer_requests=[r.to_document() for r in seal.join.lock.requests.requests],
        parent_work_in_both_views=list(seal.join.parent_work),
        response_losses_by_boundary=dict(actual.response_losses),
        response_numerical_agreement=actual.response_numerical_agreement,
        native_prices=native_prices(
            views,
            actual.events,
            use_allowed=seal.join.use_allowed,
            handoff_available=seal.join.handoff is not None,
        ),
        consumer_readout=selected_intervals(seal, reveal, actual, views),
    )
