# SPDX-License-Identifier: MPL-2.0
"""Pre-parent observations, post-parent decisions and matched native responses."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

import numpy as np

from empirical_lawhood.domains.matrix.finite_response_law.preparation_policy_instruments import (
    preparation_policy_compact_interface,
)
from empirical_lawhood.domains.matrix.prepared_response.instruments import (
    PreparedPortFrame,
)
from empirical_lawhood.domains.matrix.six_matrix_response.response_observer import (
    _decode,
)
from empirical_lawhood.science.records.serialization import (
    CanonicalRecord,
    validate_sha256,
)
from .dynamics import acquire_phase
from .measurement import (
    lower_choices,
    matched_word_response,
    reduce_panel,
    requests,
    service,
    validity,
)
from .phase_records import PreparationApplicabilityPanel
from .records import PreparationApplicabilityMeasuredRoot, numbers
from .science import DELTA
from .seals import PreparationApplicabilityLowerSeal, PreparationApplicabilityParents
from .waveform_forecast import (
    DESCRIPTIONS,
    TARGETS,
    WaveformFeatures,
    features_at_cutoff,
    frozen_predictions,
)
from .waveform_population import WaveformDraw, WaveformNativePhase
from .words import WORDS

PORT_TWO_WORDS = tuple(
    i
    for i, word in enumerate(WORDS)
    if word.direction_index == 1 and word.magnitude == 8
)
PORT_TWO_PAIR = (PORT_TWO_WORDS[0] - 1) // 2


@dataclass(frozen=True, slots=True)
class WaveformForecast(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/waveform-preparation/pre-parent-forecast"
    draw: WaveformDraw
    primary: WaveformFeatures
    refined: WaveformFeatures
    fits_sha256: str | None
    predictions: tuple[Decimal | None, ...]

    def __post_init__(self):
        if (
            (self.primary.refinement, self.refined.refinement) != (1, 2)
            or self.primary.prefix_sha256 != self.refined.prefix_sha256
            or self.primary.lower_sha256 != self.refined.lower_sha256
            or any(
                x.root_id != self.draw.allocation.root_id
                for x in (self.primary, self.refined)
            )
        ):
            raise ValueError(
                "Forecast changes its prefix, view, original law or independent waveform"
            )
        evaluation = self.draw.allocation.split_role == "EVALUATION"
        if evaluation != (self.fits_sha256 is not None) or len(self.predictions) != (
            len(DESCRIPTIONS) * 3 * len(TARGETS) if evaluation else 0
        ):
            raise ValueError(
                "Held-out forecasts need their development fits and complete prediction roster"
            )
        if evaluation:
            validate_sha256(self.fits_sha256)
        if any(p is not None and not p.is_finite() for p in self.predictions):
            raise ValueError(
                "Unavailable forecasts must retain their explicit missing value"
            )


def seal_prefix(prefix, lower, fits=None):
    primary = features_at_cutoff(prefix, lower, refinement=1)
    refined = features_at_cutoff(prefix, lower, refinement=2)
    return WaveformForecast(
        prefix.phases[0].waveform,
        primary,
        refined,
        None if fits is None else fits.fingerprint(),
        () if fits is None else frozen_predictions(primary, fits),
    )


@dataclass(frozen=True, slots=True)
class WaveformParents(PreparationApplicabilityParents):
    SCHEMA: ClassVar[str] = "empirical-lawhood/waveform-preparation/parents"
    phases: tuple[WaveformNativePhase, ...]


@dataclass(frozen=True, slots=True)
class WaveformLowerSeal(PreparationApplicabilityLowerSeal):
    SCHEMA: ClassVar[str] = "empirical-lawhood/waveform-preparation/child-decisions"


@dataclass(frozen=True, slots=True)
class WaveformPanel(PreparationApplicabilityPanel):
    SCHEMA: ClassVar[str] = "empirical-lawhood/waveform-preparation/panel"
    phases: tuple[WaveformNativePhase, ...]


def _frame(prefix):
    if prefix.frame_base64 is None:
        return None
    return PreparedPortFrame(4096, _decode(prefix.frame_base64, (2, 3, 4, 4)))


def acquire_parents(prefix, forecast):
    prefix_sha = prefix.fingerprint()
    draw = prefix.phases[0].waveform
    if forecast.primary.prefix_sha256 != prefix_sha or forecast.draw != draw:
        raise ValueError(
            "Parent acquisition requires the forecast from this waveform's measured prefix"
        )
    frame = _frame(prefix)
    phases = (
        ()
        if frame is None
        else tuple(
            acquire_phase(
                phase_name="parent",
                allocation=draw.allocation,
                waveform=draw,
                refinement=p.refinement,
                source_sha256=p.source_sha256,
                incoming=p,
                schedule_index=arm,
                frame=frame,
            )
            for arm in range(3)
            for p in prefix.phases
        )
    )
    return WaveformParents(prefix.root_id, prefix_sha, forecast.fingerprint(), phases)


def seal_lower(prefix, forecast, parents, lower):
    if (
        parents.prefix_sha256 != prefix.fingerprint()
        or parents.selection_sha256 != forecast.fingerprint()
        or forecast.primary.lower_sha256 != lower.fingerprint()
    ):
        raise ValueError(
            "Post-handoff decisions require the actual parent and original forecast"
        )
    identity = (prefix.root_id, parents.fingerprint(), lower.fingerprint())
    if len(parents.phases) != 6 or any(
        p.disposition != "COMPLETE" for p in parents.phases
    ):
        return WaveformLowerSeal(*identity, False, (), (), (), (), (), ())
    frame = _frame(prefix)
    rows = []
    for p in sorted(
        (p for p in parents.phases if p.refinement == 1), key=lambda p: p.schedule_index
    ):
        if p.incoming_sha256 != prefix.phases[0].fingerprint():
            raise ValueError("New parent does not continue the primary prefix")
        rows.append(
            preparation_policy_compact_interface(
                frame=frame,
                ticks=p.history_ticks,
                positions=_decode(p.history_positions_base64, (31, 2, 3, 4, 4)),
                momenta=_decode(p.history_momenta_base64, (31, 2, 3, 4, 4)),
            ).values
        )
    predicted = lower.predict(np.asarray(rows))
    width = float(lower.q) * predicted.sigma + np.asarray(DELTA) / 8
    directions, requirements = requests(forecast.draw.allocation.seed_for("requests"))
    choices = lower_choices(
        predicted.mean, width, predicted.supported, directions, requirements
    )
    return WaveformLowerSeal(
        *identity,
        True,
        numbers(predicted.mean),
        numbers(width),
        tuple(map(bool, predicted.supported)),
        tuple(map(int, choices.flat)),
        tuple(map(int, directions.flat)),
        numbers(requirements),
    )


def acquire_panel(prefix, parents, sealed):
    if (
        parents.prefix_sha256 != prefix.fingerprint()
        or sealed.parents_sha256 != parents.fingerprint()
    ):
        raise ValueError(
            "Assay acquisition needs its post-handoff decisions and original prefix"
        )
    frame = _frame(prefix)
    futures = (
        ()
        if not sealed.complete
        else tuple(
            acquire_phase(
                phase_name="future",
                allocation=parent.allocation,
                waveform=parent.waveform,
                refinement=parent.refinement,
                source_sha256=parent.source_sha256,
                incoming=parent,
                schedule_index=parent.schedule_index,
                future_index=future,
                word_index=word,
                frame=frame,
            )
            for parent in parents.phases
            for future in range(2)
            for word in range(len(WORDS))
        )
    )
    return WaveformPanel(
        prefix.root_id,
        parents.prefix_sha256,
        parents.selection_sha256,
        (*parents.phases, *futures),
        sealed.fingerprint(),
    )


@dataclass(frozen=True, slots=True)
class WaveformMeasurement(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/waveform-preparation/measurement"
    forecast: WaveformForecast
    measured: PreparationApplicabilityMeasuredRoot
    signed_port_two: tuple[Decimal | None, ...]
    native_intervals: int
    failures: tuple[str, ...]

    def __post_init__(self):
        if (
            self.measured.root_id != self.draw.allocation.root_id
            or self.measured.prefix_sha256 != self.primary.prefix_sha256
            or self.measured.lower_sha256 != self.primary.lower_sha256
            or self.native_intervals < 0
        ):
            raise ValueError(
                "Waveform measurement loses its original assignment or forecast"
            )
        if len(self.signed_port_two) != 12 or any(
            (
                self.complete
                if v is None
                else type(v) is not Decimal or not v.is_finite()
            )
            for v in self.signed_port_two
        ):
            raise ValueError(
                "A waveform requires one measured or missing port response per arm, future and view"
            )
        if self.complete == bool(self.failures):
            raise ValueError(
                "An unavailable waveform measurement must identify its failure"
            )

    @property
    def draw(self):
        return self.forecast.draw

    @property
    def primary(self):
        return self.forecast.primary

    @property
    def complete(self):
        return self.measured.complete

    def training_target(self, target, arm):
        if not self.complete:
            return None
        if target == "validity":
            return Decimal(int(all(self.measured.conjuncts[arm * 7 : (arm + 1) * 7])))
        if target == "covered-service":
            return Decimal(self.measured.covered_counts[arm]) / 256
        if target == "signed-port-two":
            # Stored order is parent, future, numerical view.
            return (
                self.signed_port_two[4 * arm] + self.signed_port_two[4 * arm + 2]
            ) / 2
        raise ValueError("Unknown training target")


def _available_port_two(prefix, panel):
    """Preserve individually measurable contrasts when another part of the full panel fails."""
    frame = _frame(prefix)
    if frame is None:
        return (None,) * 12
    cells = {
        (p.schedule_index, p.refinement, p.future_index, p.word_index): p
        for p in panel.phases
    }

    def observe(arm, future, view):
        parent = cells.get((arm, view, None, None))
        hold, minus, plus = (
            cells.get((arm, view, future, word)) for word in (0, *PORT_TWO_WORDS)
        )
        if any(
            p is None or p.disposition != "COMPLETE"
            for p in (parent, hold, minus, plus)
        ):
            return None
        if parent.incoming_sha256 != prefix.phases[view - 1].fingerprint():
            raise ValueError(
                "Physical measurement substitutes the preparation predecessor"
            )
        parent_sha = parent.fingerprint()
        neg, neg_known = matched_word_response(frame, parent_sha, hold, minus)
        pos, pos_known = matched_word_response(frame, parent_sha, hold, plus)
        if not (neg_known[0, 1] and pos_known[0, 1]):
            return None
        return Decimal(str(float((pos[0, 1] - neg[0, 1]) / 2)))

    return tuple(observe(a, f, v) for a in range(3) for f in range(2) for v in (1, 2))


def assess_panel(prefix, forecast, sealed, panel, lower):
    if (
        panel.selection_sha256 != forecast.fingerprint()
        or panel.lower_seal_sha256 != sealed.fingerprint()
        or sealed.lower_sha256 != lower.fingerprint()
        or forecast.primary.lower_sha256 != lower.fingerprint()
        or forecast.primary.prefix_sha256 != prefix.fingerprint()
    ):
        raise ValueError("Waveform assessment changed a pre-outcome decision")
    parents = WaveformParents(
        prefix.root_id,
        prefix.fingerprint(),
        panel.selection_sha256,
        tuple(p for p in panel.phases if p.phase == "parent"),
    )
    if sealed.parents_sha256 != parents.fingerprint():
        raise ValueError("Observed panel changed the parents used for the lower seal")
    identity = (
        prefix.root_id,
        prefix.fingerprint(),
        panel.fingerprint(),
        lower.fingerprint(),
    )
    all_phases = (*prefix.phases, *panel.phases)
    intervals = sum(p.completed_intervals for p in all_phases)
    data = None if prefix.frame_base64 is None else reduce_panel(prefix, panel)
    if data is None:
        measured = PreparationApplicabilityMeasuredRoot(
            *identity, False, (), (), (), (), (), (), (), (), ()
        )
        failures = tuple(
            f"{p.phase}.{p.schedule_index}.{p.refinement}.{p.future_index}.{p.word_index}.{p.reason}"
            for p in all_phases
            if p.disposition != "COMPLETE"
        )
        return WaveformMeasurement(
            forecast,
            measured,
            _available_port_two(prefix, panel),
            intervals,
            failures or ("UNAVAILABLE_FRAME_OR_RESPONSE",),
        )
    z, y, work = data
    maxima, checks, margins, mean, width, supported = validity(lower, z, y, work)
    directions, requirements = requests(forecast.draw.allocation.seed_for("requests"))
    selected, delivered = service(
        mean, width, supported, y, work, directions, requirements
    )
    if (
        not sealed.complete
        or sealed.mean != numbers(mean)
        or sealed.width != numbers(width)
        or sealed.support != tuple(map(bool, supported))
        or sealed.choices != tuple(map(int, selected.flat))
        or sealed.directions != tuple(map(int, directions.flat))
        or sealed.requirements != numbers(requirements)
    ):
        raise ValueError(
            "Evaluator reconstruction changes previously sealed response choices"
        )
    joint = delivered.all(axis=2)
    measured = PreparationApplicabilityMeasuredRoot(
        *identity,
        True,
        numbers(maxima),
        tuple(map(bool, checks.flat)),
        numbers(margins),
        numbers(work),
        tuple(map(int, joint.sum(axis=1))),
        tuple(map(int, (joint & checks.all(axis=1)[:, None]).sum(axis=1))),
        tuple(map(int, (selected >= 0).sum(axis=(1, 2)))),
        tuple(map(int, ((selected >= 0) & ~delivered).sum(axis=(1, 2)))),
        tuple(map(int, delivered.sum(axis=1).flat)),
        handoff=numbers(z),
    )
    return WaveformMeasurement(
        forecast, measured, numbers(y[:, PORT_TWO_PAIR, 1, :, :]), intervals, ()
    )
