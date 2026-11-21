"""Authenticate current structural-method source bytes at the storage boundary.

This is an effectful source inventory, separate from the reusable numerical
methods and their pure identity contracts. Every call checks the current files.
"""
from hashlib import sha256
from pathlib import Path
from empirical_lawhood.science.identity.structural_recurrence_source import (
    _METHOD_FILES,
    MarginStructuralRecurrenceForecastFrozenSourceFile,
    MarginStructuralRecurrenceForecastMethodSourceManifest,
)

def method_source_manifest() -> MarginStructuralRecurrenceForecastMethodSourceManifest:
    'Bind the seven method and numerical-input files as current executing target bytes.'

    method_dir = Path(__file__).resolve().parent.parent / "methods"
    values = []
    for filename in _METHOD_FILES:
        path = method_dir / filename
        if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= 2 * 1024 * 1024:
            raise ValueError('structural recurrence method source is missing or outside its byte bound')
        values.append(
            MarginStructuralRecurrenceForecastFrozenSourceFile(
                source_id=f"margin-structural-recurrence-forecast-source.{filename.removesuffix('.py').replace('_', '-')}",
                repository_path=f"src/empirical_lawhood/methods/{filename}",
                sha256=sha256(path.read_bytes()).hexdigest(),
            )
        )
    return MarginStructuralRecurrenceForecastMethodSourceManifest(
        manifest_id='independent-substrate-grounding.margin-structural-recurrence-forecast.method-source-manifest',
        source_files=tuple(sorted(values, key=lambda row: row.source_id)),
    )

