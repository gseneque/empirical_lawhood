# SPDX-License-Identifier: MPL-2.0
"""Whole-waveform inference and the fixed development headroom decision."""

from dataclasses import dataclass
from fractions import Fraction
import json
from typing import ClassVar

import numpy as np

from empirical_lawhood.methods.statistics.experimental_statistics import (
    binomial_probability_interval,
)
from empirical_lawhood.domains.matrix.classical_series.records import json_text
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from .statistics import paired_binary_test
from .waveform_forecast import DESCRIPTIONS, TARGETS, WaveformFits, fit_development
from .waveform_population import allocate_waveform
from .waveform_trial import WaveformMeasurement


@dataclass(frozen=True, slots=True)
class WaveformCohort(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/waveform-preparation/cohort"
    role: str
    master_seed: int
    bootstrap_seed: int
    rows: tuple[WaveformMeasurement, ...]
    disposition: str
    statistics_json: str
    fitted: WaveformFits | None

    @property
    def identity(self):
        return ObjectIdentity.from_record(
            f"waveform-cohort.{self.role}.{self.master_seed:032x}", self
        )

    def __post_init__(self):
        expected_count = {"development": 32, "evaluation": 128}[self.role]
        if (
            type(self.bootstrap_seed) is not int
            or not 0 <= self.bootstrap_seed < 2**128
            or len(self.rows) != expected_count
            or any(
                row.draw
                != allocate_waveform(
                    master_seed=self.master_seed, role=self.role, index=i
                )
                for i, row in enumerate(self.rows)
            )
        ):
            raise ValueError(
                "Waveform readout changes its complete independent allocation"
            )
        if self.disposition not in (
            "UNEVALUABLE",
            "HEADROOM_BELOW_THRESHOLD",
            "ENTER_CONFIRMATION",
            "SUPPORTED",
            "UNRESOLVED",
        ):
            raise ValueError("Unknown waveform scientific disposition")
        summary = json.loads(self.statistics_json)
        if (
            summary["assigned"] != expected_count
            or summary["disposition"] != self.disposition
        ):
            raise ValueError(
                "Waveform statistics changed the terminal decision or denominator"
            )
        if (self.disposition == "ENTER_CONFIRMATION") != (self.fitted is not None):
            raise ValueError("A passing development screen must freeze its estimators")
        if self.fitted and self.fitted.development_source_sha256s != tuple(
            r.fingerprint() for r in self.rows
        ):
            raise ValueError(
                "Development estimators must bind all original observations"
            )


def _bootstrap(operand, draws):
    samples = operand[draws].mean(axis=1)
    return {
        "mean": float(operand.mean()),
        "interval_95": np.quantile(samples, (0.025, 0.975)).tolist(),
        "one_sided_lower_95": float(np.quantile(samples, 0.05)),
    }


def _paired_binary_counts(first, second):
    gain, wins, harms, p = paired_binary_test(first, second)
    return {
        "gain": gain,
        "wins": wins,
        "harms": harms,
        "common_pass": int((first & second).sum()),
        "common_failure": int((~first & ~second).sum()),
        "exact_one_sided_p": p,
    }


def statistics(rows, bootstrap_seed):
    if not rows:
        raise ValueError("No independent waveform assignments")
    result = {
        "assigned": len(rows),
        "complete": sum(row.complete for row in rows),
        "incomplete": {
            row.draw.allocation.root_id: row.failures
            for row in rows
            if not row.complete
        },
        "native_view_intervals": sum(row.native_intervals for row in rows),
        "request_pairs_per_root": 256,
        "measured_port_two_counts_by_arm_future_view": np.asarray(
            [[v is not None for v in row.signed_port_two] for row in rows]
        )
        .reshape(-1, 3, 2, 2)
        .sum(axis=0)
        .tolist(),
    }
    if result["incomplete"]:
        return dict(result, disposition="UNEVALUABLE")
    rng = np.random.Generator(np.random.PCG64(bootstrap_seed))
    draws = rng.integers(0, len(rows), (20000, len(rows)))
    measurements = [r.measured for r in rows]
    validity = np.asarray([m.conjuncts for m in measurements], dtype=bool).reshape(
        -1, 3, 7
    )
    valid = validity.all(axis=2)
    covered = np.asarray([m.covered_counts for m in measurements]) / 256
    wrong = np.asarray([m.false_admissions for m in measurements])
    attempts = np.asarray([m.attempts for m in measurements])
    result.update(
        arm_order=["H", "N", "P"],
        validity_conjunct_failures=(~validity).sum(axis=0).tolist(),
        valid_roots=valid.sum(axis=0).tolist(),
        covered_pairs=np.rint(covered.sum(axis=0) * 256).astype(int).tolist(),
        attempted_consumer_choices=attempts.sum(axis=0).tolist(),
        declined_consumer_choices=(len(rows) * 512 - attempts.sum(axis=0)).tolist(),
        joint_deliveries=np.sum(
            [m.joint_counts for m in measurements], axis=0
        ).tolist(),
        false_consumer_choices=wrong.sum(axis=0).tolist(),
        false_admission_roots=(wrong > 0).sum(axis=0).tolist(),
        validity_n_h=_paired_binary_counts(valid[:, 1], valid[:, 0]),
        validity_p_h=_paired_binary_counts(valid[:, 2], valid[:, 0]),
        covered_n_h=_bootstrap(covered[:, 1] - covered[:, 0], draws),
        covered_p_h=_bootstrap(covered[:, 2] - covered[:, 0], draws),
        root_service_change_vs_hold={
            name: {
                "gains": int((covered[:, i] > covered[:, 0]).sum()),
                "harms": int((covered[:, i] < covered[:, 0]).sum()),
                "ties": int((covered[:, i] == covered[:, 0]).sum()),
            }
            for i, name in ((1, "N"), (2, "P"))
        },
        optimistic_headroom=_bootstrap(covered.max(axis=1) - covered[:, 0], draws),
        false_admission_upper_n=float(
            binomial_probability_interval(
                len(rows),
                int((wrong[:, 1] > 0).sum()),
                tail_probability=Fraction(1, 20),
            ).upper
        ),
        prefix_drive_distinct=len({r.primary.drive for r in rows}),
        prefix_sampling={
            "snapshot_channels": 8,
            "applied_drive_channels": 2,
            "recorded_drive_samples": 9,
            "additional_measured_response_samples": 8,
            "cadence_reference_ticks": 16,
        },
    )
    if rows[0].draw.allocation.split_role == "DEVELOPMENT":
        disposition = (
            "ENTER_CONFIRMATION"
            if result["optimistic_headroom"]["mean"] >= 0.05
            else "HEADROOM_BELOW_THRESHOLD"
        )
        return dict(result, disposition=disposition)
    effect = result["covered_n_h"]
    passed = (
        result["validity_n_h"]["gain"] > 0
        and result["validity_n_h"]["exact_one_sided_p"] <= 0.05
        and effect["mean"] >= 0.05
        and effect["one_sided_lower_95"] > 0
        and result["false_admission_upper_n"] <= 0.10
    )
    return dict(result, disposition="SUPPORTED" if passed else "UNRESOLVED")


def held_out_information(rows, fits, bootstrap_seed):
    """Compare the frozen rules on the very same native targets and retained assignments."""
    if any(row.forecast.fits_sha256 != fits.fingerprint() for row in rows):
        raise ValueError("Held-out forecast originated from another development freeze")
    if not all(
        row.complete and all(v is not None for v in row.forecast.predictions)
        for row in rows
    ):
        return {
            "disposition": "UNEVALUABLE",
            "assigned": len(rows),
            "complete": sum(r.complete for r in rows),
        }
    rng = np.random.Generator(np.random.PCG64(bootstrap_seed))
    draws = rng.integers(0, len(rows), (20000, len(rows)))
    predictions = np.asarray(
        [row.forecast.predictions for row in rows], dtype=float
    ).reshape(len(rows), len(DESCRIPTIONS), 3, len(TARGETS))
    truth = np.asarray(
        [
            [[r.training_target(t, arm) for t in TARGETS] for arm in range(3)]
            for r in rows
        ],
        dtype=float,
    )
    physical = np.asarray([r.signed_port_two for r in rows], dtype=float).reshape(
        -1, 3, 2, 2
    )
    margins = np.asarray([float(r.primary.margin) for r in rows])
    cuts = np.asarray(fits.margins, dtype=float)
    strata = np.searchsorted(cuts[1:-1], margins, side="right")
    result = {
        "assigned": len(rows),
        "descriptions": {},
        "incremental": {},
        "margin_quartile_counts": np.bincount(strata, minlength=4).tolist(),
        "below_development_range": int((margins < cuts[0]).sum()),
        "above_development_range": int((margins > cuts[4]).sum()),
    }

    def contrast_loss(prediction, actual, arm):
        return (
            (prediction[:, arm] - prediction[:, 0]) - (actual[:, arm] - actual[:, 0])
        ) ** 2

    for i, name in enumerate(DESCRIPTIONS):
        pred = predictions[:, i]
        estimated = (pred[:, 0, 0] < 0.5) & (pred[:, 1, 0] >= 0.5)
        observed = (truth[:, 0, 0] == 0) & (truth[:, 1, 0] == 1)
        result["descriptions"][name] = {
            "arm_losses_in_target_order": np.mean((pred - truth) ** 2, axis=0).tolist(),
            "service_contrast_loss_n_h": float(
                contrast_loss(pred[:, :, 1], truth[:, :, 1], 1).mean()
            ),
            "service_contrast_loss_p_h": float(
                contrast_loss(pred[:, :, 1], truth[:, :, 1], 2).mean()
            ),
            "physical_arm_mse_by_view": ((pred[:, :, 2, None, None] - physical) ** 2)
            .mean(axis=(0, 2))
            .tolist(),
            "physical_contrast_mse_n_h_by_view": (
                (
                    (pred[:, 1, 2] - pred[:, 0, 2])[:, None, None]
                    - (physical[:, 1] - physical[:, 0])
                )
                ** 2
            )
            .mean(axis=(0, 1))
            .tolist(),
            "predicted_rescues": {
                "true": int((estimated & observed).sum()),
                "false": int((estimated & ~observed).sum()),
                "missed": int((~estimated & observed).sum()),
                "correct_negative": int((~estimated & ~observed).sum()),
            },
        }
    for a, b in (("drive", "drive-history"), ("drive-margin", "drive-history-margin")):
        gains = contrast_loss(
            predictions[:, DESCRIPTIONS.index(a), :, 1], truth[:, :, 1], 1
        ) - contrast_loss(
            predictions[:, DESCRIPTIONS.index(b), :, 1], truth[:, :, 1], 1
        )
        result["incremental"][b] = dict(
            _bootstrap(gains, draws),
            by_margin_stratum=[
                float(gains[strata == k].mean()) if np.any(strata == k) else None
                for k in range(4)
            ],
        )
    return result


def assess_cohort(role, master, bootstrap_seed, rows, *, development=None):
    rows = tuple(sorted(rows, key=lambda row: row.draw.allocation.root_id))
    summary = statistics(rows, bootstrap_seed)
    decision = summary["disposition"]
    if role == "evaluation":
        if development is None or development.fitted is None:
            raise ValueError(
                "Evaluation requires the original development fit to score the frozen forecasts"
            )
        summary["held_out_information"] = held_out_information(
            rows, development.fitted, bootstrap_seed
        )
    fit = fit_development(rows) if decision == "ENTER_CONFIRMATION" else None
    return WaveformCohort(
        role, master, bootstrap_seed, rows, decision, json_text(summary), fit
    )
