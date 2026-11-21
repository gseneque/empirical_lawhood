# SPDX-License-Identifier: MPL-2.0
"""Read explicitly selected quantum configuration files for the domain decoder."""

from pathlib import Path
import json
from typing import Mapping
from empirical_lawhood.domains.quantum.receiver_response.contracts import QuantumReceiverResponseConfig, decode_config, stable_json_bytes


def load_config(path: Path) -> tuple[QuantumReceiverResponseConfig, bytes]:
    payload = path.read_bytes()
    document = json.loads(payload)
    if not isinstance(document, Mapping):
        raise ValueError("quantum receiver response config root must be an object")
    config = decode_config(document)
    canonical = stable_json_bytes(document)
    if canonical != payload:
        raise ValueError("quantum receiver response repository config must use canonical JSON bytes")
    return config, payload

