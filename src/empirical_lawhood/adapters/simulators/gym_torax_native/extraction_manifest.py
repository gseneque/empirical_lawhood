"""Native acquisition, external-format translation and custody integration."""

from __future__ import annotations
from hashlib import sha256
from pathlib import Path
from empirical_lawhood.adapters._bounded_files import read_bounded_contained
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import validate_relative_locator

from empirical_lawhood.domains.fusion.gym_torax_native.extraction_manifest import (
    GymToraxBoundedExtractionEntry as _science_GymToraxBoundedExtractionEntry,
    GymToraxBoundedExtractionManifest as _science_GymToraxBoundedExtractionManifest,
)

from empirical_lawhood.domains.fusion.gym_torax_native.extraction_manifest import GYM_TORAX_SURGICAL_EXTRACTION_MANIFEST_ID as _science_GYM_TORAX_SURGICAL_EXTRACTION_MANIFEST_ID, _ENTRY_PATHS


_MAX_SOURCE_FILE_BYTES = 2 * 1024 * 1024


def _read_exact_regular_file(repository_root: Path, relative_path: str) -> bytes:
    root = repository_root.resolve(strict=True)
    validate_relative_locator(relative_path)
    payload = read_bounded_contained(
        root, root / relative_path, maximum_bytes=_MAX_SOURCE_FILE_BYTES
    )
    if not payload:
        raise ValueError("target source entry exceeds its exact byte bound")
    return payload

def gym_torax_current_implementation_sha256() -> str:
    """Bind listed package bytes in both source and installed distributions."""
    package_root = Path(__file__).resolve(strict=True).parents[3]
    digest = sha256()
    for source_path in sorted(_ENTRY_PATHS):
        relative_path = source_path.removeprefix("src/empirical_lawhood/")
        if relative_path == source_path:
            raise ValueError("implementation source path is outside the installed package")
        name = relative_path.encode("utf-8")
        payload = _read_exact_regular_file(package_root, relative_path)
        digest.update(len(name).to_bytes(8, "big"))
        digest.update(name)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()

def build_gym_torax_extraction_manifest(
    repository_root: Path,
) -> _science_GymToraxBoundedExtractionManifest:
    """Fingerprint the explicit source roster in the inspected target checkout."""
    entries = tuple(
        sorted(
            (
                _science_GymToraxBoundedExtractionEntry(
                    entry_id='source.tokamak-control.target.' + path.replace("/", "-").replace("_", "-").replace(".", "-"),
                    target_relative_path=path,
                    target_file_sha256=sha256(_read_exact_regular_file(repository_root, path)).hexdigest(),
                )
                for path in _ENTRY_PATHS
            ),
            key=lambda entry: entry.entry_id,
        )
    )
    return _science_GymToraxBoundedExtractionManifest(
        manifest_id=_science_GYM_TORAX_SURGICAL_EXTRACTION_MANIFEST_ID,
        entries=entries,
        outcome_access=OutcomeAccess.OUTCOME_BLIND,
        visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        grants_source_access=False,
        grants_execution_authority=False,
        grants_scientific_promotion=False,
    )

def verify_gym_torax_extraction_manifest(
    manifest: _science_GymToraxBoundedExtractionManifest,
    *,
    expected_identity: ObjectIdentity,
    repository_root: Path,
) -> None:
    if expected_identity != ObjectIdentity.from_record(manifest.manifest_id, manifest):
        raise ValueError("target source manifest identity diverged")
    observed = build_gym_torax_extraction_manifest(repository_root)
    if observed != manifest:
        raise ValueError("target source bytes diverged")
