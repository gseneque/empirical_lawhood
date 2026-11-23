# SPDX-License-Identifier: MPL-2.0
"""Independent bath-waveform allocations and causal observations for fixed-law reuse."""

from dataclasses import dataclass, field
from decimal import Decimal
from hashlib import sha256
from functools import lru_cache
from typing import ClassVar

import numpy as np

from empirical_lawhood.domains.matrix.constructed_preparation_applicability.config import (
    FIXED_PROBE_SEED,
)
from empirical_lawhood.domains.matrix.constructed_preparation_applicability.phase_records import (
    ConstructedPreparationStream,
    nominal_digest,
)
from empirical_lawhood.domains.matrix.finite_response_law.instruments import (
    REFERENCE_INSTRUMENT,
)
from empirical_lawhood.domains.matrix.input_contracts import (
    MATRIX_NATIVE_PURPOSES,
    MatrixPurposeSeed,
    MatrixRootAllocation,
)
from empirical_lawhood.domains.matrix.prepared_response.instruments import (
    PreparedPortFrame,
    prepared_receiver,
)
from empirical_lawhood.domains.matrix.six_matrix_response.response_observer import (
    _decode,
)
from empirical_lawhood.science.records.serialization import (
    CanonicalRecord,
    canonical_json_bytes,
    validate_sha256,
)

from .phase_records import (
    PreparationApplicabilityNativePhase,
    PreparationApplicabilityPrefix,
)
from .records import numbers


NOMINAL_PURPOSES = ("prefix", "prefix-bridge", "parent", "parent-bridge")
SAMPLE_TICKS = tuple(range(3968, 4097, 16))


@dataclass(frozen=True, slots=True)
class WaveformDraw(CanonicalRecord):
    """One waveform and its perturbation, shared by all three parents on a root."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/waveform-preparation/draw"
    allocation: MatrixRootAllocation
    nominal_seed_digests: tuple[str, ...]

    @property
    def unit_id(self):
        return self.allocation.root_id

    def __post_init__(self):
        root = self.allocation
        if (
            root.cohort != "constructed"
            or root.source_prefix is not None
            or root.seed_for("passive-probes") != FIXED_PROBE_SEED
            or len(self.nominal_seed_digests) != len(NOMINAL_PURPOSES)
        ):
            raise ValueError(
                "Waveform draw needs a fresh prefix, the fixed probe and four bath purposes"
            )
        for digest in self.nominal_seed_digests:
            validate_sha256(digest, field_name="nominal_seed_digest")
        nominal = {int(digest[:32], 16) for digest in self.nominal_seed_digests}
        reserved = {int(nominal_digest(name)[:32], 16) for name in NOMINAL_PURPOSES}
        if (
            len(nominal) != len(NOMINAL_PURPOSES)
            or nominal & reserved
            or nominal & {seed.effective_seed for seed in root.scientific_seeds}
        ):
            raise ValueError(
                "Waveform and perturbation streams must be independent of the D016 reference"
            )

    def stream(self, purpose):
        nominal = None
        if purpose in NOMINAL_PURPOSES:
            nominal = self.nominal_seed_digests[NOMINAL_PURPOSES.index(purpose)]
        elif purpose not in (
            "future-1",
            "future-1-bridge",
            "future-2",
            "future-2-bridge",
        ):
            raise ValueError("Unknown bath purpose for a waveform acquisition")
        return ConstructedPreparationStream(
            self.allocation.seed_for(purpose),
            nominal,
            Decimal(1) if nominal is None else Decimal("0.002"),
        )


@lru_cache(maxsize=512)
def allocate_waveform(*, master_seed, role, index):
    counts = {"development": 32, "evaluation": 128}
    if (
        role not in counts
        or type(index) is not int
        or not 0 <= index < counts[role]
        or type(master_seed) is not int
        or not 0 <= master_seed < 2**128
    ):
        raise ValueError(
            "Select a predeclared waveform split, root index and numeric master"
        )

    def digest(component, purpose):
        return sha256(
            canonical_json_bytes(
                (
                    "empirical-lawhood/waveform-preparation/allocation-v1",
                    master_seed,
                    role,
                    index,
                    component,
                    purpose,
                )
            )
        ).hexdigest()

    innovations = tuple(
        sorted(
            (
                MatrixPurposeSeed(purpose, int(digest("independent", purpose)[:32], 16))
                for purpose in MATRIX_NATIVE_PURPOSES
            ),
            key=lambda seed: seed.purpose_id,
        )
    )
    return WaveformDraw(
        MatrixRootAllocation(
            f"waveform-preparation.{master_seed:032x}.{role}.{index:03d}",
            "constructed",
            innovations,
            split_role=role.upper(),
            conditioning_seeds=(
                MatrixPurposeSeed("passive-probes", FIXED_PROBE_SEED, "PCG64DXSM"),
            ),
        ),
        tuple(digest("nominal", purpose) for purpose in NOMINAL_PURPOSES),
    )


@dataclass(frozen=True, slots=True)
class WaveformNativePhase(PreparationApplicabilityNativePhase):
    SCHEMA: ClassVar[str] = "empirical-lawhood/waveform-preparation/native-phase"
    streams: tuple[ConstructedPreparationStream, ...]
    waveform: WaveformDraw = field(kw_only=True)

    def __post_init__(self):
        PreparationApplicabilityNativePhase.__post_init__(self)
        purpose = (
            f"future-{self.future_index + 1}" if self.phase == "future" else self.phase
        )
        if self.allocation != self.waveform.allocation or self.streams != (
            self.waveform.stream(purpose),
            self.waveform.stream(purpose + "-bridge"),
        ):
            raise ValueError("Native phase changed its waveform, innovations or future")


@dataclass(frozen=True, slots=True)
class WaveformPrefix(PreparationApplicabilityPrefix):
    SCHEMA: ClassVar[str] = "empirical-lawhood/waveform-preparation/prefix"
    phases: tuple[WaveformNativePhase, ...]

    def __post_init__(self):
        PreparationApplicabilityPrefix.__post_init__(self)
        if self.phases[0].waveform != self.phases[1].waveform:
            raise ValueError("Numerical views must observe the same waveform")


def observe_waveform_history(prefix: WaveformPrefix, *, refinement=1):
    """Read the common clock and measured port from an authenticated prefix only."""
    if type(refinement) is not int or refinement not in (1, 2):
        raise ValueError("Select a declared primary or refined view")
    phase = prefix.phases[refinement - 1]
    if prefix.frame_base64 is None or phase.disposition != "COMPLETE":
        return None
    frame = PreparedPortFrame(4096, _decode(prefix.frame_base64, (2, 3, 4, 4)))
    positions = _decode(phase.history_positions_base64, (31, 2, 3, 4, 4))
    # The realized trace records interval starts. A sample at t uses the
    # applied coupling on the last substep ending at that physical tick.
    trace = _decode(phase.trace_base64, (phase.completed_intervals, 9), real=True)
    drive = trace[np.asarray(SAMPLE_TICKS) * refinement - 1, 3:5]
    feature = prefix.features[refinement - 1]
    channel = REFERENCE_INSTRUMENT.feature_ids.index("x-port-2")
    past = [
        prepared_receiver(frame, positions[phase.history_ticks.index(tick), 0])[1]
        for tick in SAMPLE_TICKS
    ]
    if not np.isclose(past[-1], float(feature[channel]), rtol=1e-12, atol=1e-12):
        raise ValueError("Past and snapshot disagree on the common port at 4096")
    return {
        "sample_ticks": SAMPLE_TICKS,
        "snapshot": feature[:8],
        "full_prefix": feature,
        "drive": numbers(drive),
        "earlier_port_two": numbers(past[:-1]),
    }
