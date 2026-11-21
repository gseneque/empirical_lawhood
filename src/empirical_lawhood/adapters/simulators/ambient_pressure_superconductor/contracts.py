"""Native acquisition and external-format binding for the domain science."""

from __future__ import annotations
from pathlib import Path

from empirical_lawhood.domains.materials.superconductivity.solver_control_contracts import (
    ExcludedSolverControlConfig as _science_ExcludedSolverControlConfig,
    decode_config_bytes as _science_decode_config_bytes,
)

def load_config(path: Path) -> tuple[_science_ExcludedSolverControlConfig, bytes]:
    payload = path.read_bytes()
    return _science_decode_config_bytes(payload), payload
