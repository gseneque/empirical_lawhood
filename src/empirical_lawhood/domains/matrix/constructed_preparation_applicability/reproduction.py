# SPDX-License-Identifier: MPL-2.0
"""Re-evaluate the disclosed Q and E selections and the matched native contrasts."""

import numpy as np

from . import diagnostics
from .measurement import measure_sealed_observations, requests
from .qualification import constructor_crossing
from .readout import report


def replay_boundary_phase(stage, lower, assignments, expected, diagnostic_seed):
    measured, crossings, diagnostic_rows, native, forces = [], [], [], [], []
    for allocation, (original, seal, row) in zip(stage.allocation.roots, assignments, strict=True):
        if (
            allocation.root_id != original.root_id
            or row["root"] != original.root_id
            or row["measurement_sha256"] != original.fingerprint()
            or not original.complete
        ):
            raise ValueError("Disclosed boundary measurement differs from its assigned root")
        z = np.asarray(original.handoff, dtype=float).reshape(3, 24, 2)
        y = np.asarray([arm["matched_native"] for arm in row["arms"]], dtype=float)
        work = np.asarray([arm["work_by_view"] for arm in row["arms"]])
        if y.shape != (3, 4, 8, 2, 2) or work.shape != (3, 2):
            raise ValueError("Incomplete boundary assay panel")
        identity = (row["root"], row["prefix_sha256"], row["panel_sha256"], row["lower_sha256"])
        seed = allocation.seed_for("requests")
        actual = measure_sealed_observations(identity, (z, y, work), lower, stage.phase, seed, seal)
        if actual != original:
            raise ValueError("Recomputed boundary measurement differs from the original")
        measured.append(actual)
        crossings.append(constructor_crossing(actual, lower))
        direction, requirement = requests(seed)
        diagnostic, _ = diagnostics.diagnose_root(
            lower=lower,
            z=z,
            y=y,
            work=work,
            direction=direction,
            requirement=requirement,
            choices=np.asarray(seal.choices).reshape(3, 256, 2),
        )
        diagnostic_rows.append(dict(diagnostic, root=row["root"]))
        native.append(y)
        forces.append([arm["force_observations"] for arm in row["arms"]])
    result = report(stage, measured, crossings)
    if result != expected:
        raise ValueError("Recomputed constructor or evaluation report differs from the issued decision")
    native = np.asarray(native)
    contrasts = {}
    for arm, label in ((1, "N-H"), (2, "P-H")):
        difference = native[:, arm] - native[:, 0]
        for pair, (magnitude, direction) in enumerate(row["force_pairs"]):
            for axis, quantity in enumerate(lower.chart.output_ids):
                nested = difference[:, pair, axis]
                root_means = nested.mean(axis=(1, 2))
                contrasts[f"{label}:{magnitude},{direction}:{quantity}"] = {
                    "unit": lower.chart.output_units[axis],
                    "mean_by_future_and_view": nested.mean(axis=0).tolist(),
                    "mean_whole_root": float(root_means.mean()),
                    "range_of_root_means": [float(root_means.min()), float(root_means.max())],
                    "positive_roots": int((root_means > 0).sum()),
                    "negative_roots": int((root_means < 0).sum()),
                }
    return {
        "report_sha256": result.fingerprint(),
        "report": result.to_document(),
        "constructor_crossings": sum(crossings),
        "paired_native_contrasts": contrasts,
        "arms": {
            label: {
                "force_means": {
                    field: np.mean(
                        [[root[i][view][field] for view in (0, 1)] for root in forces], axis=0
                    ).tolist()
                    for field in ("at_4464", "at_4496", "backward_rate", "inward_margin")
                },
                "validity_pass_by_conjunct": np.sum(
                    [m.conjuncts[i * 7 : i * 7 + 7] for m in measured], axis=0
                ).tolist(),
            }
            for i, label in enumerate(("H", "N", "P"))
        },
        "root_probability_bounds": {"status": "QUALIFICATION_EXCLUDED_FROM_CONFIRMATION"}
        if stage.phase == "Q"
        else diagnostics.root_probability_bounds(
            assigned=len(measured),
            complete=sum(m.complete for m in measured),
            false_admission_roots=sum(m.false_admissions[1] > 0 for m in measured),
            full_valid_roots=result.full_valid_counts[1],
        ),
        "diagnostics": diagnostics.aggregate_rows(diagnostic_rows, bootstrap_seed=diagnostic_seed),
        "roots": diagnostic_rows,
    }


def historical_boundary(rows):
    """Tabulate the disclosed preprint E32 separately from the independent replication."""
    if len(rows) != 32 or len({r["unit"] for r in rows}) != 32:
        raise ValueError("Expected all original preprint boundary roots")
    native = np.asarray([[a["matched_native"] for a in r["arms"]] for r in rows])
    if native.shape != (32, 3, 4, 8, 2, 2):
        raise ValueError("Incomplete preprint boundary native panel")
    return {
        "roots": [r["unit"] for r in rows],
        "constructor_crossings": sum(r["constructor_margin_pass"] for r in rows),
        "covered_pairs": [sum(r["arms"][i]["covered"] for r in rows) for i in range(3)],
        "bypassed_pairs": [sum(r["arms"][i]["support_bypassed_joint"] for r in rows) for i in range(3)],
        "paired_native_means_by_force_quantity_future_view": {
            label: (native[:, i] - native[:, 0]).mean(axis=0).tolist()
            for i, label in ((1, "N-H"), (2, "P-H"))
        },
    }
