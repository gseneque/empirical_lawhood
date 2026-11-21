"""Native acquisition and external-format binding for the domain science."""

from __future__ import annotations
import hashlib
from pathlib import Path
import numpy as np
from empirical_lawhood.domains.optics.fine_steering_mirror.contracts import FineSteeringMirrorObservationOperatorSpec

from empirical_lawhood.domains.optics.fine_steering_mirror.observation import (
    FineSteeringMirrorObservationError as _science_FineSteeringMirrorObservationError,
    FloatArray as _science_FloatArray,
)

def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_safe_array(
    path: Path,
    *,
    expected_realizations: int,
    operator: FineSteeringMirrorObservationOperatorSpec,
) -> _science_FloatArray:
    """Load one exact numeric source array without executable deserialization."""

    loaded = np.load(path, allow_pickle=False)
    if loaded.dtype != np.dtype(np.float64):
        raise _science_FineSteeringMirrorObservationError(f"{path.name} must have exact float64 dtype")
    expected_shape = (
        operator.sample_count,
        operator.input_channels,
        expected_realizations,
        operator.periods_per_realization,
    )
    if loaded.shape != expected_shape:
        raise _science_FineSteeringMirrorObservationError(
            f"{path.name} shape {loaded.shape!r} differs from {expected_shape!r}"
        )
    if not np.isfinite(loaded).all():
        raise _science_FineSteeringMirrorObservationError(f"{path.name} contains non-finite values")
    return np.asarray(loaded, dtype=np.float64)
