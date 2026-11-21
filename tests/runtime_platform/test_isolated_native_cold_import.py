# SPDX-License-Identifier: MPL-2.0
"""Selected progress bootstrap must not require the coordinator environment."""

import os
from pathlib import Path
import subprocess
import sys

import pytest


def test_child_bootstrap_cold_import_without_array_catalog_authority_or_molecular_dependencies():
    script = '''
import importlib.abc
import sys

blocked = {"cryptography", "pyarrow", "h5py", "onnx", "safetensors", "sqlalchemy", "alembic", "numpy", "scipy", "openmm", "pdbfixer", "parmed"}
class RefuseCoordinatorDependencies(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in blocked:
            raise AssertionError("selected raw-progress bootstrap imported " + fullname)
sys.meta_path.insert(0, RefuseCoordinatorDependencies())
from empirical_lawhood.execution.local.isolated_native_subwork import run_isolated_native_entry
from empirical_lawhood.execution.local.native_subwork_ipc import PipeNativeSubworkProgress
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics import durable_preparation, durable_instrumentation, parameter_audit, preparation, science
from empirical_lawhood.adapters.rubisco.rubisco_insilico_dynamics import durable_native_entry
for name in ("empirical_lawhood.storage.authority", "empirical_lawhood.execution.local.execution", "empirical_lawhood.storage.native_subwork"):
    assert name not in sys.modules, name
print("COLD_IMPORT_ONLY_PASSED")
'''
    environment = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[2] / "src"), PYTHONDONTWRITEBYTECODE="1")
    returned = subprocess.run([sys.executable, "-c", script], env=environment, capture_output=True, text=True)
    assert returned.returncode == 0, returned.stderr
    assert returned.stdout.strip() == "COLD_IMPORT_ONLY_PASSED"


def test_storage_namespace_leaves_implementation_at_its_documented_owners():
    import empirical_lawhood.storage as storage
    from empirical_lawhood.storage import artifacts
    from empirical_lawhood.storage.contracts.artifacts import ArtifactManifest

    assert artifacts.ArtifactManifest is ArtifactManifest
    assert artifacts.ExternalArtifactPlane.__module__ == artifacts.__name__
    with pytest.raises(AttributeError, match="ExternalArtifactPlane"):
        getattr(storage, "ExternalArtifactPlane")
    with pytest.raises(AttributeError, match="missing_public_export"):
        getattr(storage, "missing_public_export")


def test_old_raw_transport_paths_reexport_the_same_owners():
    from empirical_lawhood.storage import artifact_stream_primitives as raw
    from empirical_lawhood.storage import artifacts, artifact_validation, native_subwork
    for name in ("ArtifactPlaneError", "ExternalRootUnavailable", "ArtifactIdentityConflict", "ArtifactInputLimitExceeded"):
        assert getattr(artifacts, name) is getattr(artifact_validation, name) is getattr(raw, name)
    for name in ("_anonymous_input_descriptor", "_seal_anonymous_input", "_PreopenedBoundedReader"):
        assert getattr(artifacts, name) is getattr(raw, name)
    for name in ("_output_chunk_bound", "_output_chunks"):
        assert getattr(native_subwork, name) is getattr(raw, name)
    assert artifacts.STREAM_CHUNK_BYTES == artifact_validation.STREAM_CHUNK_BYTES == native_subwork.STREAM_CHUNK_BYTES == raw.STREAM_CHUNK_BYTES
