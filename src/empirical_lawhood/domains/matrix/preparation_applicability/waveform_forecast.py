# SPDX-License-Identifier: MPL-2.0
"""The pre-parent waveform forecasts and their development-only training operands."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

import numpy as np

from empirical_lawhood.methods.statistics.experimental_statistics import (
    StandardizedRidgeParameters,
    fit_standardized_ridge,
    predict_standardized_ridge,
)
from empirical_lawhood.science.records.serialization import (
    CanonicalRecord,
    validate_sha256,
)
from .records import finite, numbers
from .waveform_population import observe_waveform_history


DESCRIPTIONS = (
    "snapshot",
    "snapshot-margin",
    "full-prefix",
    "drive",
    "drive-history",
    "drive-margin",
    "drive-history-margin",
)
TARGETS = ("validity", "covered-service", "signed-port-two")


@dataclass(frozen=True, slots=True)
class WaveformFeatures(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/waveform-preparation/features"
    root_id: str
    prefix_sha256: str
    lower_sha256: str
    refinement: int
    full_prefix: tuple[Decimal, ...]
    drive: tuple[Decimal, ...]
    earlier_port_two: tuple[Decimal, ...]
    margin: Decimal | None

    def __post_init__(self):
        validate_sha256(self.prefix_sha256)
        validate_sha256(self.lower_sha256)
        if self.refinement not in (1, 2):
            raise ValueError("Waveform features require a declared numerical view")
        available = self.margin is not None
        finite(() if self.margin is None else (self.margin,), int(available))
        for values, count in (
            (self.full_prefix, 24),
            (self.drive, 18),
            (self.earlier_port_two, 8),
        ):
            finite(values, count if available else 0)

    def row(self, description):
        if description not in DESCRIPTIONS:
            raise ValueError("Unknown waveform description")
        if self.margin is None:
            return None
        if description == "full-prefix":
            return self.full_prefix
        values = self.full_prefix[:8]
        if description.startswith("drive"):
            values += self.drive
        if "history" in description:
            values += self.earlier_port_two
        if description.endswith("margin"):
            values += (self.margin,)
        return values


def features_at_cutoff(prefix, lower, *, refinement):
    history = observe_waveform_history(prefix, refinement=refinement)
    identity = (prefix.root_id, prefix.fingerprint(), lower.fingerprint(), refinement)
    if history is None:
        return WaveformFeatures(*identity, (), (), (), None)
    feature = history["full_prefix"]
    margin = lower.center[17] + 6 * lower.scale[17] - feature[17]
    return WaveformFeatures(
        *identity, feature, history["drive"], history["earlier_port_two"], margin
    )


@dataclass(frozen=True, slots=True)
class WaveformRidge(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/waveform-preparation/ridge"
    description: str
    arm: int
    target: str
    parameters: StandardizedRidgeParameters

    def __post_init__(self):
        if (
            self.description not in DESCRIPTIONS
            or self.arm not in range(3)
            or self.target not in TARGETS
        ):
            raise ValueError(
                "Waveform ridge must identify its information, parent and receiver"
            )


@dataclass(frozen=True, slots=True)
class WaveformFits(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/waveform-preparation/frozen-fits"
    development_root_ids: tuple[str, ...]
    development_source_sha256s: tuple[str, ...]
    margins: tuple[Decimal, ...]
    fits: tuple[WaveformRidge, ...]

    def __post_init__(self):
        if (
            len(set(self.development_root_ids)) != 32
            or len(self.development_root_ids) != 32
        ):
            raise ValueError(
                "Waveform fitting requires the 32 independent development roots"
            )
        if len(self.development_source_sha256s) != 32:
            raise ValueError("Training must identify each original measurement")
        for fingerprint in self.development_source_sha256s:
            validate_sha256(fingerprint)
        finite(self.margins, 5)
        if self.margins != tuple(sorted(self.margins)):
            raise ValueError("Development margin limits and quartiles are out of order")
        if tuple((f.description, f.arm, f.target) for f in self.fits) != tuple(
            (d, a, t) for d in DESCRIPTIONS for a in range(3) for t in TARGETS
        ):
            raise ValueError("Incomplete waveform model roster")


def fit_development(measurements):
    """Train once on the assigned development roster. Each arm has its own intercept."""
    if len(measurements) != 32 or any(
        m.draw.allocation.split_role != "DEVELOPMENT"
        or m.primary.margin is None
        or not m.complete
        for m in measurements
    ):
        raise ValueError(
            "A complete, predeclared development screen must precede fitting"
        )
    ordered = sorted(measurements, key=lambda m: m.draw.allocation.root_id)
    fits = []
    for description in DESCRIPTIONS:
        features = tuple(m.primary.row(description) for m in ordered)
        for arm in range(3):
            for target in TARGETS:
                targets = tuple(m.training_target(target, arm) for m in ordered)
                fits.append(
                    WaveformRidge(
                        description,
                        arm,
                        target,
                        fit_standardized_ridge(features, targets, penalty=Decimal(10)),
                    )
                )
    margins = np.asarray([float(m.primary.margin) for m in ordered])
    return WaveformFits(
        tuple(m.draw.allocation.root_id for m in ordered),
        tuple(m.fingerprint() for m in ordered),
        numbers(np.quantile(margins, (0, 0.25, 0.5, 0.75, 1))),
        tuple(fits),
    )


def frozen_predictions(features, fits):
    if features.refinement != 1 or features.root_id in fits.development_root_ids:
        raise ValueError(
            "Held-out forecasts require a separate root and its primary prefix"
        )
    predictions = []
    for fit in fits.fits:
        row = features.row(fit.description)
        prediction = (
            None if row is None else predict_standardized_ridge(fit.parameters, row)
        )
        if prediction is not None and fit.target != "signed-port-two":
            prediction = max(Decimal(0), min(Decimal(1), prediction))
        predictions.append(prediction)
    return tuple(predictions)
