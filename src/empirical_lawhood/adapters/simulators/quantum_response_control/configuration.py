# SPDX-License-Identifier: MPL-2.0
"""Read explicitly selected quantum configuration files for the domain decoder."""

from pathlib import Path
import json
from typing import Mapping
from empirical_lawhood.domains.quantum.response_control.contracts import QuantumResponseControlConfig, decode_config, MAXIMUM_JSON_BYTES


def load_config(path: Path) -> tuple[QuantumResponseControlConfig, bytes]:
    payload = path.read_bytes()
    if len(payload) > MAXIMUM_JSON_BYTES:
        raise ValueError("quantum response control config exceeds the bounded JSON limit")
    document = json.loads(payload)
    if not isinstance(document, Mapping):
        raise TypeError("quantum response control config root must be an object")
    config = decode_config(document)
    return config, payload

