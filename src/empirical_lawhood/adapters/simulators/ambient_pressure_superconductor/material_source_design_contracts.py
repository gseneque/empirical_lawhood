"""Native acquisition and external-format binding for the domain science."""

from __future__ import annotations
from pathlib import Path

from empirical_lawhood.domains.materials.superconductivity.material_source_design_contracts import (
    MATERIAL_SOURCE_DESIGN_MAXIMUM_CONFIG_BYTES as _science_MATERIAL_SOURCE_DESIGN_MAXIMUM_CONFIG_BYTES,
    MaterialSourceDesignConfig as _science_MaterialSourceDesignConfig,
    decode_material_source_design_config_bytes as _science_decode_material_source_design_config_bytes,
)

def load_material_source_design_config(path: Path) -> tuple[_science_MaterialSourceDesignConfig, bytes]:
    observed = path.lstat()
    if path.is_symlink() or not path.is_file() or observed.st_size > _science_MATERIAL_SOURCE_DESIGN_MAXIMUM_CONFIG_BYTES:
        raise ValueError('material source design config must be a bounded regular non-symlink file')
    payload = path.read_bytes()
    return _science_decode_material_source_design_config_bytes(payload), payload
