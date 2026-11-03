# SPDX-License-Identifier: MPL-2.0
"""Operator context reaches metadata derivation without changing its lifecycle."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api.experiment_preparation import load_experiment_specification, _protocol
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.experiment_runtime_bindings import experiment_runtime_binding
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection

ROOT = Path(__file__).parents[1]


def test_public_derivation_supplies_selected_operator_service_before_any_effect(tmp_path, monkeypatch):
    from empirical_lawhood.api import matrix_programme_source_continuation as owner
    specification = ROOT / 'programmes/foundations/emergent-structure/workflows/matrix-programme/source-continuation.example.json'
    binding = experiment_runtime_binding(_protocol(load_experiment_specification(specification)))
    assert binding.programme_service_factory is None
    assert binding.bind_handoff is None and binding.bind_development_runtime is None
    profile = SimpleNamespace(maximum_parallel_tasks=8)
    service = ExperimentProgrammeService(ROOT, object(), profile,
        catalog_relative_path='disclosed/catalog.sqlite3')
    calls = []

    class ObservedSelection(Exception):
        pass

    def observe(**kwargs):
        calls.append(kwargs)
        raise ObservedSelection('stop before custody or publication')

    monkeypatch.setattr(owner, 'derive_inputs', observe)
    with pytest.raises(ObservedSelection):
        service.derive_inputs(specification_path=specification,
            source_selection_path=tmp_path/'sources.json', metadata_directory=tmp_path/'metadata',
            output_selection_path=tmp_path/'derived.json', execution=ExecutionSelection(workers=8))
    selected, = calls
    assert selected['_service'] is service
    assert selected['artifact_writer'] is service.artifact_writer
    assert selected['execution'].workers == 8
    assert not tuple(tmp_path.iterdir())
