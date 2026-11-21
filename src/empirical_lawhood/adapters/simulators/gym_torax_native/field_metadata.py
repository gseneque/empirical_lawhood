"""Native acquisition, external-format translation and custody integration."""

from __future__ import annotations
import hashlib
from importlib import metadata as importlib_metadata
from importlib.util import find_spec
from pathlib import Path

from empirical_lawhood.domains.fusion.gym_torax_native.field_metadata import (
    GymToraxFieldMetadataManifest as _science_GymToraxFieldMetadataManifest,
)

def verify_installed_gym_torax_metadata_sources(
    manifest: _science_GymToraxFieldMetadataManifest,
) -> None:
    """Fail closed if installed source versions or defining bytes have drifted."""

    for distribution, expected in (
        ("gymtorax", manifest.gymtorax_version),
        ("torax", manifest.torax_version),
        ("xarray", manifest.xarray_version),
    ):
        if importlib_metadata.version(distribution) != expected:
            raise RuntimeError(f"GYM_TORAX_METADATA_DISTRIBUTION_DRIFT:{distribution}")
    for source_file in manifest.source_files:
        spec = find_spec(source_file.distribution)
        if spec is None or not spec.submodule_search_locations:
            raise RuntimeError(f"GYM_TORAX_METADATA_DISTRIBUTION_UNAVAILABLE:{source_file.distribution}")
        package_root = Path(next(iter(spec.submodule_search_locations))).resolve(strict=True)
        source_path = (package_root / source_file.relative_path).resolve(strict=True)
        if not source_path.is_relative_to(package_root):
            raise RuntimeError("GYM_TORAX_METADATA_SOURCE_PATH_ESCAPE")
        digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
        if digest != source_file.sha256:
            raise RuntimeError(f"GYM_TORAX_METADATA_SOURCE_DRIFT:{source_file.source_file_id}")
