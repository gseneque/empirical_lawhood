# SPDX-License-Identifier: MPL-2.0
"""Read explicitly selected quantum configuration files for the domain decoder."""

from pathlib import Path
import json
from typing import Mapping, cast
from empirical_lawhood.domains.quantum.trajectory_burnin_screen.schemas import QuantumTrajectoryBurninScreenConfig, decode_config, stable_json_bytes


def load_config(path: Path) -> tuple[QuantumTrajectoryBurninScreenConfig, bytes]:
    payload = path.read_bytes()
    document = json.loads(payload)
    if not isinstance(document, Mapping):
        raise ValueError("quantum trajectory burnin screen config root must be an object")
    config = decode_config(cast(Mapping[str, object], document))
    canonical = stable_json_bytes(document)
    if canonical != payload:
        raise ValueError("quantum trajectory burnin screen repository config must use canonical JSON bytes")
    return config, payload

