# SPDX-License-Identifier: MPL-2.0
"""Paired use, numerical error and native cost on an exposed evaluation cohort."""

from collections import Counter, defaultdict
from decimal import Decimal
import json
from math import fsum, sqrt

from .handoff_error import _signed_differences, observed_handoff_errors
from .law_binding import NATIVE_WORDS


def native_prices(views, events, *, use_allowed, handoff_available):
    costs = Counter()
    for view in views:
        costs.update({task: updates for task, updates, _ in view.accounting})
    common = {task for task in costs if task.endswith((".prefix.native", ".parent.native"))}
    words = {w.invocation.task_id: w.invocation.word for w in views[0].words}
    if len(common) != 2 or len(words) != 18 or set(costs) != common | words.keys():
        raise ValueError("Native price requires the complete assigned prefix, parent and futures")

    def price(selected):
        pairs = {
            (NATIVE_WORDS[e.selected_word].magnitude, NATIVE_WORDS[e.selected_word].direction_index)
            for e in selected
            if use_allowed and e.selected_word >= 0
        }
        required = common | {
            task
            for task, word in words.items()
            if (handoff_available if word.sign == 0 else (word.magnitude, word.direction_index) in pairs)
        }
        return sum(costs[task] for task in required)

    return {
        "shared_full_panel": sum(costs.values()),
        "common_prefix_and_assigned_parent": sum(costs[task] for task in common),
        "per_policy_admitted_signed_pairs_and_matched_hold": {
            b: price([e for e in events if e.policy_id.startswith(b + ".")])
            for b in ("composed", "cached", "direct")
        },
        "per_consumer_admitted_signed_pair_and_matched_hold": {e.policy_id: price([e]) for e in events},
    }


def _sealed_means(row, chart):
    values = {}
    for cell in row["rows"]:
        key = (cell["magnitude"], cell["direction_index"], cell["quantity"])
        mean = cell["sealed_prediction"]
        if key in values and values[key] != mean:
            raise ValueError("Sealed forecast changed between nested futures or numerical views")
        values[key] = mean
    ordered = [
        values[int(word.magnitude), word.direction_index, quantity]
        for word in NATIVE_WORDS[1::2]
        for quantity in chart.output_ids
    ]
    return tuple(None if value is None else Decimal(value) for value in ordered)


def replay_evaluation(cohort, native, qualification, lower, rows):
    if (
        not qualification.eligible_for_prospective_evaluation
        or cohort.qualification.object_fingerprint != qualification.fingerprint()
        or qualification.publications[0].content_sha256 != lower.fingerprint()
    ):
        raise ValueError("Evaluation changes the qualified lower or its calibration")
    by_root = defaultdict(list)
    for view in native.views:
        by_root[view.root.stage_unit].append(view)
    if set(by_root) != {operand.root_id for operand in cohort.operands}:
        raise ValueError("Native completion and inference rosters differ")
    terms = ("handoff_error", "downstream_error", "total_error")
    root_squares, root_biases, scored = defaultdict(list), defaultdict(list), Counter()
    gate_counts, interval_counts, costs = defaultdict(Counter), defaultdict(Counter), Counter()
    pairs = []
    for operand, row in zip(cohort.operands, rows, strict=True):
        views = sorted(by_root[operand.root_id], key=lambda view: view.refinement)
        unit = views[0].root
        if (row["root"], row["physical_unit"], row["assigned_parent"]) != (
            operand.root_id,
            unit.physical_unit_id,
            unit.assigned_parent,
        ):
            raise ValueError("Paired readout substitutes an assigned physical root or parent")
        support, cells = observed_handoff_errors(views, lower, _sealed_means(row, lower.chart))
        if (
            json.loads(json.dumps(cells, default=str)) != row["rows"]
            or support != row["primary_observed_handoff_in_support"]
        ):
            raise ValueError("Recomputed native measurements or signed errors differ from the published root")
        for quantity in lower.chart.output_ids:
            for term in terms:
                values = [float(c[term]) for c in cells if c["quantity"] == quantity and c[term] is not None]
                if values:
                    key = quantity, term
                    root_squares[key].append(fsum(v * v for v in values) / len(values))
                    root_biases[key].append(fsum(values) / len(values))
                    scored[key] += len(values)
        consumers = {item["policy"]: item for item in row["consumer_readout"]}
        if set(consumers) != {e.policy_id for e in operand.events}:
            raise ValueError("Incomplete consumer decision census")
        for event in operand.events:
            c = consumers[event.policy_id]
            if (event.selected_word, event.success, event.false_admission) != (
                c["selected_word"],
                c["task_success"],
                c["false_admission"],
            ):
                raise ValueError("Published consumer choices differ from the issued scalar operands")
            method = event.policy_id.split(".")[0]
            gate_counts[method].update(f"{gate}.{value}" for gate, value in c["gates"].items())
            for bound in c["bounds"]:
                quantity = bound["quantity"]
                sample = bound["observed_selected_native"]
                for key, field in (
                    ("unexpanded", "unexpanded"),
                    ("expanded", "issued_expanded"),
                    ("physical", "physical_domain_intersection"),
                ):
                    verdict = None
                    if bound["full_assay_scoreable"]:
                        lo, hi = map(Decimal, bound[field])
                        verdict = lo <= Decimal(sample) <= hi
                    interval_counts[method][f"{quantity}.{key}.{verdict}"] += 1
        (allowed,) = {c["handoff_permitted_use"] for c in consumers.values()}
        price = native_prices(
            views,
            operand.events,
            use_allowed=allowed,
            handoff_available=views[0].handoff_interface is not None,
        )
        if price != row["native_prices"]:
            raise ValueError("Recomputed price differs from the published native accounting")
        costs.update(price["per_policy_admitted_signed_pairs_and_matched_hold"])
        costs.update(price["per_consumer_admitted_signed_pair_and_matched_hold"])
        for name in ("shared_full_panel", "common_prefix_and_assigned_parent"):
            costs[name] += price[name]
        pairs.append(
            {
                "root": unit.stage_unit,
                "physical_unit": unit.physical_unit_id,
                "parent": unit.assigned_parent,
                "loss": {k: None if v is None else str(v) for k, v in operand.response_losses},
                "handoff_supported": support,
                "methods": {
                    m: {
                        "words": [e.selected_word for e in operand.events if e.policy_id.startswith(m + ".")],
                        "joint": all(e.success for e in operand.events if e.policy_id.startswith(m + ".")),
                        "false": any(
                            e.false_admission for e in operand.events if e.policy_id.startswith(m + ".")
                        ),
                    }
                    for m in ("composed", "cached", "direct")
                },
            }
        )

    def estimates(key):
        n = len(root_squares[key])
        return {
            "independent_roots": n,
            "scored_cells": scored[key],
            "rmse": sqrt(fsum(root_squares[key]) / n) if n else None,
            "mean_signed_error": fsum(root_biases[key]) / n if n else None,
        }

    # The typed cohort constructor reruns cohort_inference, including both root bootstraps.
    return {
        "statistics": json.loads(cohort.statistics_json),
        "roots": pairs,
        "handoff_errors": {q: {t: estimates((q, t)) for t in terms} for q in lower.chart.output_ids},
        "native_prices": dict(costs),
        "gate_counts": gate_counts,
        "selected_intervals": interval_counts,
    }


def historical_handoff_errors(rows):
    """Recount the historical E64 error decomposition on its own independent roots."""
    if len(rows) != 64 or len({r["unit"] for r in rows}) != 64:
        raise ValueError("Expected all original preprint handoff roots")
    mean_squares = defaultdict(list)
    counts = Counter()
    for root in rows:
        squares = defaultdict(list)
        if len(root["rows"]) != 128:
            raise ValueError("Missing assigned historical handoff cells")
        for cell in root["rows"]:
            values = [
                None if cell[k] is None else Decimal(cell[k])
                for k in ("sealed_prediction", "observed_handoff_prediction", "native_measurement")
            ]
            if not cell["native_scoreable"]:
                values[2] = None
            for key, value in zip(
                ("handoff_error", "downstream_error", "total_error"),
                _signed_differences(*values),
                strict=True,
            ):
                original = None if cell[key] is None else Decimal(cell[key])
                if value != original:
                    raise ValueError("Historical forecast decomposition changed")
                if value is not None:
                    squares[cell["quantity"], key].append(float(value) ** 2)
        for key, values in squares.items():
            counts[key] += len(values)
            mean_squares[key].append(fsum(values) / len(values))
    return {
        "roots": [r["unit"] for r in rows],
        "nested_cells": sum(len(r["rows"]) for r in rows),
        "quantities": {
            q: {
                term: {
                    "rmse": sqrt(fsum(vals) / len(vals)),
                    "scored_cells": counts[axis, term],
                    "independent_roots": len(vals),
                }
                for (axis, term), vals in mean_squares.items()
                if axis == q
            }
            for q, _ in mean_squares
        },
    }
