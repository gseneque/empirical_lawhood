# SPDX-License-Identifier: MPL-2.0
"""Disposable guarded development storage, without scientific authority."""

import os
from pathlib import Path

from empirical_lawhood.storage.artifacts import ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.storage.contracts.artifacts import ExternalRootContract
from empirical_lawhood.storage.workspaces import containing_mount

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def selected_test_mount(directory: Path, *, external: bool = False) -> Path:
    """Observe the fixture's actual mount and enforce an explicit test selection."""
    mount = containing_mount(directory)
    selected = os.environ.get("EL_TEST_EXTERNAL_MOUNT")
    if selected is not None and Path(selected) != mount:
        raise ValueError("select pytest basetemp beneath EL_TEST_EXTERNAL_MOUNT")
    if external and mount == Path("/"):
        raise ValueError("this control requires an actual external test mount")
    return mount


def numerical_plane(directory):
    mount = selected_test_mount(directory)
    directory.mkdir(parents=True, exist_ok=True)
    resolved = directory.resolve()
    contract = ExternalRootContract("test.numerical-provenance.root", "synthetic software storage",
        str(resolved), str(mount), "empirical-lawhood/test/local-root", 1)
    return ExternalArtifactPlane(GuardedExternalRoot(contract))
