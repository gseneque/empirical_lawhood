# SPDX-License-Identifier: MPL-2.0
"""Read explicitly selected quantum configuration files for the domain decoder."""

from pathlib import Path
import json
from typing import Mapping
from empirical_lawhood.domains.quantum.finite_grammar_identification.contracts import QuantumFiniteGrammarIdentificationConfig, decode_config, MAXIMUM_JSON_BYTES


def load_config(path: Path) -> tuple[QuantumFiniteGrammarIdentificationConfig, bytes]:
    payload = path.read_bytes()
    if len(payload) > MAXIMUM_JSON_BYTES:
        raise ValueError("quantum finite grammar identification config exceeds its byte bound")
    document = json.loads(payload)
    if not isinstance(document, Mapping):
        raise TypeError("quantum finite grammar identification config root must be an object")
    return decode_config(document), payload

