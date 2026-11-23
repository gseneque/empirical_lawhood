# SPDX-License-Identifier: MPL-2.0
"""Replay the whole-waveform development decision and paired physical contrasts."""

import json

import numpy as np

from ..preparation_applicability.waveform_evaluation import assess_cohort


def replay_waveforms(original, ordinary):
    actual = assess_cohort(original.role, original.master_seed, original.bootstrap_seed, original.rows)
    if actual != original or actual.role != "development" or len(actual.rows) != 32:
        raise ValueError("Disclosed waveforms do not reproduce the complete development decision")
    rows = actual.rows
    draw = np.random.Generator(np.random.PCG64(actual.bootstrap_seed))
    indices = draw.integers(0, len(rows), (20000, len(rows)))
    y = np.asarray([r.signed_port_two for r in rows], dtype=float).reshape(len(rows), 3, 2, 2)
    contrasts = {}
    for arm, label in ((1, "N-H"), (2, "P-H")):
        delta = y[:, arm] - y[:, 0]
        contrasts[label] = []
        for view in range(2):
            values = delta[:, :, view].mean(axis=1)
            complete = int(np.isfinite(values).sum())
            result = {"assigned": len(rows), "complete": complete}
            if complete == len(rows):
                means = values[indices].mean(axis=1)
                result.update(
                    mean=float(values.mean()),
                    interval_95=np.quantile(means, [0.025, 0.975]).tolist(),
                    gains=int((values > 0).sum()),
                    harms=int((values < 0).sum()),
                    by_future=delta[:, :, view].mean(axis=0).tolist(),
                )
            contrasts[label].append(result)
    reference = ordinary["retained_evaluation_roots"]
    if len(reference) != 64 or len({r["root"] for r in reference}) != 64:
        raise ValueError("The historical ordinary-bath comparison requires all 64 roots")
    covered = np.asarray([r["covered_pairs"] for r in reference])
    return {
        "decision": actual.disposition,
        "cohort_sha256": actual.fingerprint(),
        "master_seed": actual.master_seed,
        "bootstrap_seed": actual.bootstrap_seed,
        "statistics": json.loads(actual.statistics_json),
        "physical_port_two_contrasts": contrasts,
        "ordinary_bath": {
            "assigned": len(reference),
            "covered_pairs": covered.sum(axis=0).tolist(),
            "best_with_outcomes_minus_hold_pairs": int((covered.max(axis=1) - covered[:, 0]).sum()),
            "best_fixed_minus_hold_pairs": int(covered.sum(axis=0).max() - covered[:, 0].sum()),
        },
        "roots": [
            {
                "root": r.draw.unit_id,
                "measurement_sha256": r.fingerprint(),
                "complete": r.complete,
                "covered": list(r.measured.covered_counts),
                "false_admissions": list(r.measured.false_admissions),
                "signed_port_two": [None if x is None else str(x) for x in r.signed_port_two],
                "failures": list(r.failures),
            }
            for r in rows
        ],
    }
