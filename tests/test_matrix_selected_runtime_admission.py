# SPDX-License-Identifier: MPL-2.0
"""In-memory refusal ordering; no authority, storage or native operation."""

from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_bindings import ENTRY_ORIGINAL_COMMITMENTS_KEY, operation_declarations
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_workers import SelectedProtectedWorker
from empirical_lawhood.api import matrix_selected_runtime as owner


def test_current_grant_refusal_precedes_selected_original_or_scientific_reads(monkeypatch):
    calls = []
    class Current:
        def __init__(self, **kwargs):
            pass
        def current_task(self, context, runner):
            calls.append('actual-current-issue-and-grant')
            raise PermissionError('genuine current grant absent')
        def task_inputs(self, context, task):
            pytest.fail('selected scientific input read before actual authority')
    monkeypatch.setattr(owner, 'CurrentIssuedTaskCustody', Current)
    manifest = next(row for row in operation_declarations() if row.capability_key == ENTRY_ORIGINAL_COMMITMENTS_KEY).manifest()
    runner = SelectedProtectedWorker('entry', manifest)
    with pytest.raises(PermissionError, match='genuine current grant absent'):
        owner.prepare_selected_matrix(SimpleNamespace(writer=object(), reveal_authority_id=None), SimpleNamespace(), runner)
    assert calls == ['actual-current-issue-and-grant']


def test_prepared_or_foreign_runner_cannot_reuse_parent_admission():
    manifest = next(row for row in operation_declarations() if row.capability_key == ENTRY_ORIGINAL_COMMITMENTS_KEY).manifest()
    runner = SelectedProtectedWorker('entry', manifest, prepared_scope=('exposed',))
    for changed in (runner, SimpleNamespace(prepared_scope=None, manifest=manifest)):
        with pytest.raises(PermissionError, match='installed unprepared worker'):
            owner.prepare_selected_matrix(SimpleNamespace(), SimpleNamespace(), changed)


def test_source_qualification_distinguishes_authenticated_compiler_config_from_scientific_sources():
    draft = SimpleNamespace(source_materializations=())
    package = SimpleNamespace(issued_study=SimpleNamespace(materialization_qualifications=(),
        candidate=SimpleNamespace(authoring_package=SimpleNamespace(base=SimpleNamespace(draft=draft)))))
    task = SimpleNamespace(capability=SimpleNamespace(config=SimpleNamespace(artifact_id='automatic.config')),
        external_inputs=(SimpleNamespace(logical_artifact_id='automatic.config'),))
    owner._current_source_qualifications(package, task)
    task.external_inputs += (SimpleNamespace(logical_artifact_id='scientific.source'),)
    with pytest.raises(PermissionError, match='actual issued source materialization'):
        owner._current_source_qualifications(package, task)


def test_registered_api_binding_validates_original_instance_before_binding_ports(monkeypatch):
    from empirical_lawhood.api.domain_composition.matrix_selected_declarative import experiment_binding as binding
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_declarative_preparation as domain
    calls = []
    def refuse(**kwargs):
        calls.append('exact-retained-instance')
        raise ValueError('foreign actual selected source/graph')
    monkeypatch.setattr(domain, 'validate_instance', refuse)
    monkeypatch.setattr(owner, 'bind_selected_matrix_handoff', lambda *args, **kwargs: pytest.fail('foreign instance bound runtime ports'))
    handoff = SimpleNamespace(compilation=SimpleNamespace(draft=object()))
    with pytest.raises(ValueError, match='foreign actual selected'):
        binding.EXPERIMENT_RUNTIME_BINDING.bind_handoff(handoff, specification=object(), allocation=object(),
            source_records=(), artifact_writer=object())
    assert calls == ['exact-retained-instance']
