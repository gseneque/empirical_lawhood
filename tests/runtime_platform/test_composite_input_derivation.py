# SPDX-License-Identifier: MPL-2.0
"""Composite derivation is one explicit input step, never a component lifecycle."""
from pathlib import Path

import pytest

from empirical_lawhood.api import experiment_preparation as api
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding, ExecutionSelection
from tests.test_matrix_configured_e3_v2 import configured_case


def test_composite_factory_and_real_deriver_dispatch_through_existing_public_api(tmp_path, monkeypatch):
    specification = configured_case()[0]
    path = tmp_path / "specification.json"
    path.write_bytes(specification.canonical_bytes())
    calls = []
    def derive(**kwargs):
        calls.append(kwargs)
        raise ValueError("actual domain prerequisite absent before publication")
    binding = ExperimentRuntimeBinding(api._protocol(specification).protocol_id, None,
        programme_service_factory=lambda **kwargs: object(), derive_inputs=derive)
    monkeypatch.setattr(api, "experiment_runtime_binding", lambda protocol: binding)
    with pytest.raises(ValueError, match="actual domain prerequisite"):
        api.derive_experiment_inputs(specification_path=path, source_selection_path=tmp_path / "inputs.json",
            project_root=Path(__file__).resolve().parents[2], artifact_writer=object(),
            metadata_directory=tmp_path / "derived", output_selection_path=tmp_path / "output.json",
            execution=ExecutionSelection(workers=4))
    assert len(calls) == 1
    assert calls[0]["specification"] == specification
    assert calls[0]["execution"] == ExecutionSelection(workers=4)
    assert not (tmp_path / "derived").exists() and not (tmp_path / "output.json").exists()


@pytest.mark.parametrize("field", ("bind_handoff", "bind_development_runtime", "prepare_authoring", "read_result",
    "specification_schema"))
def test_composite_derivation_still_refuses_an_independent_component_lifecycle(field):
    values = {"bind_handoff": None}
    values[field] = "fixture/schema" if field == "specification_schema" else lambda: None
    with pytest.raises(TypeError, match="separate code-owned"):
        ExperimentRuntimeBinding("fixture.composite", programme_service_factory=lambda **kwargs: object(),
            derive_inputs=lambda **kwargs: object(), **values)


def test_composite_derivation_requires_a_callable_owner():
    with pytest.raises(TypeError, match="input derivation"):
        ExperimentRuntimeBinding("fixture.composite", None, programme_service_factory=lambda **kwargs: object(), derive_inputs=True)
