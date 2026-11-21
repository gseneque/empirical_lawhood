# SPDX-License-Identifier: MPL-2.0
"""Read explicitly selected quantum configuration files for the domain decoder."""

from pathlib import Path
import json
from typing import Mapping, cast
from empirical_lawhood.domains.quantum.trajectory_reference_validation.schemas import QuantumTrajectoryReferenceValidationConfig, decode_config, stable_json_bytes


def load_config(path: Path) -> tuple[QuantumTrajectoryReferenceValidationConfig, bytes]:
    payload = path.read_bytes()
    document = json.loads(payload)
    if not isinstance(document, Mapping):
        raise ValueError("quantum trajectory reference validation config root must be an object")
    config = decode_config(cast(Mapping[str, object], document))
    if stable_json_bytes(document) != payload:
        raise ValueError("quantum trajectory reference validation repository config must use canonical JSON bytes")
    return config, payload

