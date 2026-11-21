# SPDX-License-Identifier: MPL-2.0
"""Read explicitly selected quantum configuration files for the domain decoder."""

from pathlib import Path
import json
from typing import Mapping
from empirical_lawhood.domains.quantum.marked_record_identification.contracts import QuantumMarkedRecordIdentificationConfig, decode_config, MAXIMUM_JSON_BYTES


def load_config(path: Path) -> tuple[QuantumMarkedRecordIdentificationConfig, bytes]:
    payload = path.read_bytes()
    if len(payload) > MAXIMUM_JSON_BYTES:
        raise ValueError("quantum marked record identification config exceeds its byte bound")
    document = json.loads(payload)
    if not isinstance(document, Mapping):
        raise TypeError("quantum marked record identification config root must be an object")
    return decode_config(document), payload

