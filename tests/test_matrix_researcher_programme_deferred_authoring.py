# SPDX-License-Identifier: MPL-2.0
"""Actual E3 authoring hooks and current runner prerequisite ordering.

The original public fixture is disclosed software metadata. These controls
stop before candidate issue, provider entry, qualification or native work.
"""
from contextlib import nullcontext
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api.experiment_preparation import load_experiment_inputs
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.matrix_programme_projection import MatrixProgrammePrerequisite
from empirical_lawhood.api.matrix_researcher_programme import MatrixResearchProgrammeService
from empirical_lawhood.runtime.experiment_preparation import DependencyKind, ExperimentDependency
from tests.test_matrix_configured_protected_public_preparation import public_case, write_public_file_selection  # noqa: F401
from tests.test_matrix_researcher_programme import ROOT, _execution


class ReachedActualPreview(RuntimeError):
    pass


def _prepare(case, service):
    sources = write_public_file_selection(case)
    inputs = load_experiment_inputs(case.specification, sources)
    prepared = service.prepare(case.specification, scientific_inputs=inputs.scientific_inputs,
        method_inputs=inputs.method_inputs, execution=_execution(case.plane))
    return sources, prepared


def test_public_configured_preparation_reaches_actual_registered_authoring_hook(public_case, monkeypatch):  # noqa: F811
    from empirical_lawhood.api import prospective_experiment
    case = public_case
    assert case.selection.manifest.provenances == (case.provenance,)
    service = ExperimentProgrammeService(ROOT, case.plane, SimpleNamespace(maximum_parallel_tasks=4))
    _, prepared = _prepare(case, service)
    observed = []
    def preview(**kwargs):
        actual = kwargs['preparation']
        assert actual.specification_record == case.specification
        assert tuple((row.code, row.kind) for row in actual.dependencies) == (
            ('matrix.e3.resource-projection', DependencyKind.SOFTWARE),)
        assert actual.draft is not None and actual.input_files
        observed.append(actual)
        raise ReachedActualPreview('actual E3 publication custody and design derivation completed')
    monkeypatch.setattr(prospective_experiment, 'preview_prepared_prospective_experiment_candidate', preview)
    destination = Path(case.plane.root.contract.canonical_path) / 'ordinary-deferred-hook'
    with pytest.raises(ReachedActualPreview, match='actual E3 publication custody'):
        service.author(preparation=prepared, output_dir=destination)
    assert len(observed) == 1 and not destination.exists()


def test_foreign_execution_source_refuses_before_prospective_provider_preview(monkeypatch):
    from empirical_lawhood.api import prospective_experiment as owner
    from empirical_lawhood.api import recursive_prospective_authoring
    captured = owner.capture_target_closure(ROOT, 'source.disclosed-programme-foreign')
    snapshot = owner.ObjectIdentity.from_record('recursive-member.implementation', captured.closure)
    foreign = replace(snapshot, object_fingerprint='0' * 64)
    monkeypatch.setattr(recursive_prospective_authoring, 'preview_recursive_prospective_candidate',
        lambda **_: pytest.fail('foreign source reached prospective provider preview'))
    with pytest.raises(ValueError, match='differs from every exact retained selected-source closure'):
        owner._selected_source_closure(captured.closure, foreign)
    assert owner._selected_source_closure(captured.closure, snapshot) == captured.closure


@pytest.mark.parametrize('kind', tuple(value for value in DependencyKind if value is not DependencyKind.SOFTWARE))
def test_current_runner_preserves_every_nonsoftware_authoring_prerequisite(public_case, monkeypatch, kind):  # noqa: F811
    case = public_case
    ordinary = ExperimentProgrammeService(ROOT, case.plane, SimpleNamespace(maximum_parallel_tasks=4))
    source_path, actual = _prepare(case, ordinary)
    dependency = ExperimentDependency('fixture.actual-prerequisite', kind, 'Disclosed unresolved entry prerequisite')
    prepared = replace(actual, dependencies=tuple(sorted((*actual.dependencies, dependency), key=lambda row: row.code)))
    monkeypatch.setattr(ExperimentProgrammeService, 'prepare', lambda *_a, **_kw: prepared)
    monkeypatch.setattr(ExperimentProgrammeService, 'author',
        lambda **_: pytest.fail('current runner bypassed a real nonsoftware prerequisite'))
    runner = MatrixResearchProgrammeService(service=ordinary)
    monkeypatch.setattr(runner, '_phase_scope', lambda *_: nullcontext())
    monkeypatch.setattr(runner, '_authored', lambda *_: False)
    context = SimpleNamespace(observations={}, binding=lambda _: SimpleNamespace(sources=SimpleNamespace(
        relative_path=source_path.relative_to(case.plane.root.contract.canonical_path).as_posix())),
        bound_specification=lambda _: (None, case.specification), execution=actual.execution,
        child_directory=lambda _: Path(case.plane.root.contract.canonical_path) / 'never-authored')
    with pytest.raises(MatrixProgrammePrerequisite, match=dependency.code) as error:
        runner._author_phase(context, 'e3')
    assert error.value.phase == 'e3' and not context.child_directory('e3').exists()
