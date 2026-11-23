# SPDX-License-Identifier: MPL-2.0
"""Numerical read adapter for the issued historical Tier 2 development screen."""

from dataclasses import dataclass
from decimal import Decimal

import numpy as np

from .preparation_policy_contracts import PREPARATION_POLICY_SCHEDULE_IDS
from .preparation_policy_verification import independent


def _value(document, schema):
    if (
        document["schema"] != "icf-yolo/cc1-finite-lawhood/" + schema + "/v1"
        or document["version"] != "1.0.0"
    ):
        raise ValueError("Unrecognised historical preparation-screen operand")
    return document["value"]


def _decimal_array(values):
    if isinstance(values, list):
        return tuple(_decimal_array(x) for x in values)
    if values is None:
        return None
    if not isinstance(values, dict) or set(values) != {"decimal"}:
        raise ValueError("Expected an original canonical Decimal")
    return Decimal(values["decimal"])


@dataclass(frozen=True)
class _Root:
    cohort: str
    index: int


@dataclass(frozen=True)
class _Cell:
    schedule_id: str
    pair_index: int
    future: str
    refinement: int
    values: tuple
    valid: bool
    observed: bool


@dataclass(frozen=True)
class _Panel:
    root: _Root
    prefix_features: tuple
    handoff_features: tuple
    parent_work: tuple
    cells: tuple


def _historical_panel(document, position):
    panel = _value(document, "tier2-root-panel")
    identifier = _value(panel["root"], "tier2-root")
    cohort, index = ("q2", position) if position < 8 else ("cir1", position - 8)
    if (identifier["cohort"], identifier["index"]) != (cohort, index):
        raise ValueError("Historical 8 Q2 / 16 CIR1 preparation-screen assignment changed")
    cells = []
    for item in panel["cells"]:
        value = _value(item, "tier2-panel-cell")
        cells.append(
            _Cell(
                value["schedule_id"],
                value["pair_index"],
                value["future"],
                value["refinement"],
                _decimal_array(value["values"]),
                value["valid"],
                value["observed"],
            )
        )
    census = {(c.schedule_id, c.pair_index, c.future, c.refinement) for c in cells}
    if len(cells) != len(census) or census != {
        (s, p, f, v)
        for s in PREPARATION_POLICY_SCHEDULE_IDS
        for p in range(4)
        for f in ("future-1", "future-2")
        for v in (1, 2)
    }:
        raise ValueError("Historical screen does not contain the full nested cell census")
    current = "prepared-response" if cohort == "q2" else "information-response-prediction"
    return _Panel(
        _Root(current, index),
        _decimal_array(panel["prefix_features"]),
        _decimal_array(panel["handoff_features"]),
        _decimal_array(panel["parent_work"]),
        tuple(cells),
    )


def replay_historical_screen(panels, lower, screen, adjudication, freeze, original_audit):
    original = _value(screen, "m5-screen-result")
    fingerprints = [panel_id["value"]["object_fingerprint"] for panel_id in original["panels"]]
    if len(panels) != 24 or fingerprints != [digest for digest, _ in panels]:
        raise ValueError("The historical screen requires the exact ordered roster of 24 panels")
    if (
        original["lower_before"] != original["lower_after"]
        or original["lower_before"]["value"]["object_fingerprint"] != lower.original_payload.sha256
    ):
        raise ValueError("The original qualified lower changed")
    numerical = tuple(_historical_panel(doc, i) for i, (_, doc) in enumerate(panels))
    audit = independent(numerical, lower)
    if audit.keys() != original_audit.keys():
        raise ValueError("Historical fit audit differs in its scientific operand census")

    def compare(derived, stored):
        if isinstance(derived, dict):
            if derived.keys() != stored.keys():
                raise ValueError("Historical fit operand changed")
            for key, value in derived.items():
                compare(value, stored[key])
        elif isinstance(derived, list) and derived and isinstance(derived[0], dict):
            for value, expected in zip(derived, stored, strict=True):
                compare(value, expected)
        elif isinstance(derived, (float, list)):
            np.testing.assert_allclose(derived, stored, rtol=1e-12, atol=1e-12)
        elif derived != stored:
            raise ValueError("Historical development operand changed")

    compare(audit, original_audit)
    roots = []
    for i, record in enumerate(original["root_readouts"]):
        row = record["value"]
        selected, fixed = audit["selected"][i], audit["fixed"][i]
        checks = np.asarray(audit["conjuncts"][i], dtype=bool)
        s, f = (counts[i] for counts in audit["joint_successes"])
        if (
            row["root_id"] != f"t2-screen.r{i:03d}"
            or checks.tolist() != row["adequacy_conjuncts"]
            or row["adequacy_by_schedule"] != checks.all(axis=1).tolist()
            or (row["selected_schedule_id"], row["fixed_schedule_id"])
            != (PREPARATION_POLICY_SCHEDULE_IDS[selected], PREPARATION_POLICY_SCHEDULE_IDS[fixed])
            or (
                row["selected_joint_successes"],
                row["fixed_joint_successes"],
                row["joined_selected_successes"],
                row["joined_fixed_successes"],
            )
            != (s, f, s * bool(checks[selected].all()), f * bool(checks[fixed].all()))
        ):
            raise ValueError("Held-out choices, adequacy or service differ from the issued screen")
        ratios = np.array(
            [
                _decimal_array(row[k])
                for k in (
                    "maximum_error_ratio",
                    "maximum_width_ratio",
                    "maximum_numerical_difference",
                    "maximum_preservation_ratio",
                    "maximum_work",
                )
            ],
            dtype=float,
        ).T
        np.testing.assert_allclose(ratios, audit["ratios"][i], rtol=1e-12, atol=1e-12)
        roots.append(
            {
                "root": row["root_id"],
                "panel_sha256": fingerprints[i],
                "hold_adequate": bool(checks[0].all()),
                "selected": row["selected_schedule_id"],
                "fixed": row["fixed_schedule_id"],
                "selected_joint": s,
                "fixed_joint": f,
            }
        )
    if (
        any(audit[k] != original[k] for k in ("headroom_roots", "adequacy_net_roots", "gates_passed"))
        or abs(audit["joint_improvement"] - float(_decimal_array(original["joint_improvement"]))) > 1e-14
        or adjudication["value"]["scientific_status"] != original["scientific_status"]
        or original["m6_eligible"] != audit["gates_passed"]
    ):
        raise ValueError("Recomputed development entry decision differs from the original")
    return {
        "decision": original["scientific_status"],
        "eligible": original["m6_eligible"],
        "roots": roots,
        "independent_future_roots_opened": 0,
        "joint_successes": list(map(sum, audit["joint_successes"])),
        "original_freeze": freeze["value"],
        "folds": len(audit["fits"]),
        **{
            k: audit[k]
            for k in (
                "gates_passed",
                "headroom_roots",
                "adequacy_net_roots",
                "joint_improvement",
                "admissions",
            )
        },
    }
