# SPDX-License-Identifier: MPL-2.0
"""Closed API metadata derivation dispatch; no science or storage effects."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import experiment_preparation as api
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
from tests.test_matrix_configured_e3_v2 import configured_case


def test_unregistered_derivation_refuses_before_storage_or_domain_dispatch(tmp_path):
    specification = configured_case()[0]
    path = tmp_path / "specification.json"
    path.write_bytes(specification.canonical_bytes())
    class Forbidden:
        def __getattr__(self, name):
            pytest.fail("unsupported protocol contacted storage")
    with pytest.raises(ValueError, match="no installed input derivation"):
        api.derive_experiment_inputs(specification_path=path, source_selection_path=tmp_path / "absent-inputs.json",
            project_root=Path(__file__).resolve().parents[2], artifact_writer=Forbidden(),
            metadata_directory=tmp_path / "metadata", output_selection_path=tmp_path / "output.json",
            execution=ExecutionSelection(workers=4))


def test_registered_result_type_is_closed_and_execution_is_not_silently_reselected(tmp_path, monkeypatch):
    specification = configured_case()[0]
    path = tmp_path / "specification.json"
    path.write_bytes(specification.canonical_bytes())
    seen = []
    monkeypatch.setattr(api, "experiment_runtime_binding", lambda protocol: SimpleNamespace(
        derive_inputs=lambda **kwargs: seen.append(kwargs) or object()))
    with pytest.raises(TypeError, match="another result type"):
        api.derive_experiment_inputs(specification_path=path, source_selection_path=tmp_path / "inputs.json",
            project_root=Path(__file__).resolve().parents[2], artifact_writer=object(),
            metadata_directory=tmp_path / "metadata", output_selection_path=tmp_path / "output.json",
            execution=ExecutionSelection(workers=4))
    assert len(seen) == 1 and seen[0]["execution"] == ExecutionSelection(workers=4)
    with pytest.raises(TypeError, match="typed execution"):
        api.derive_experiment_inputs(specification_path=path, source_selection_path=tmp_path / "inputs.json",
            project_root=Path(__file__).resolve().parents[2], artifact_writer=object(),
            metadata_directory=tmp_path / "metadata", output_selection_path=tmp_path / "output.json", execution=None)
