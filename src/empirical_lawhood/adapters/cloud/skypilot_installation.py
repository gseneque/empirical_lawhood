# SPDX-License-Identifier: MPL-2.0
"""Inspect the selected installed SkyPilot implementation without provider contact."""

from pathlib import Path
from empirical_lawhood.storage.bounded_io import bounded_file_sha256
from empirical_lawhood.execution.remote.accelerated_controller import (
    SKYPILOT_VERSION, SKYPILOT_COMMIT, SKYPILOT_RUNPOD_FILES, SKYPILOT_RUNPOD_DETAIL_PATCH,
)


def verify_controller_installation():
    """Explicit installed-source check, without importing SkyPilot or contacting Runpod."""
    from importlib.metadata import distribution
    installed = distribution('skypilot-nightly')
    if installed.version != SKYPILOT_VERSION:
        raise ValueError('controller differs from the selected upstream build')
    observed_files = {}
    source_patch = None
    for name, digest in SKYPILOT_RUNPOD_FILES.items():
        observed = bounded_file_sha256(Path(installed.locate_file(name)), maximum_bytes=2**20)[1]
        if name == SKYPILOT_RUNPOD_DETAIL_PATCH['path'] and observed == SKYPILOT_RUNPOD_DETAIL_PATCH['sha256']:
            source_patch = dict(SKYPILOT_RUNPOD_DETAIL_PATCH)
        elif observed != digest:
            raise ValueError('controller changes a selected Runpod REST v2 source binding')
        observed_files[name] = observed
    return {'version': installed.version, 'commit': SKYPILOT_COMMIT, 'files': observed_files,
        'source_patch': source_patch,
        'provider_contact': False, 'runpod_api': 'REST_V2_ON_DEMAND'}
