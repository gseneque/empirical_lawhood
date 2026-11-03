# SPDX-License-Identifier: MPL-2.0
"""Small published controls exercise the E1 read lifetime, never science."""

from types import SimpleNamespace

import pytest

from empirical_lawhood.api import matrix_factor_confirmation_compact_read as reader
from empirical_lawhood.api.current_result_custody import CurrentResultPlanReader
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.kernel.decoding import decimal_context_key
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.runtime_platform.test_artifact_verification_scope import _publication
from tests.test_reduced_artifact_verification import _work


class _EndOfDisclosedControlCensus(Exception):
    pass


@pytest.mark.parametrize('task_count', (8, 32))
@pytest.mark.parametrize('damage', (False, True))
def test_e1_receipt_pass_has_one_final_control_census(tmp_path, monkeypatch, task_count, damage):
    plane, manifests = _publication(tmp_path, 4)
    tasks = tuple(SimpleNamespace(task_id=f'task.disclosed.{index}') for index in range(task_count))
    plan = SimpleNamespace(tasks=tasks)
    package = SimpleNamespace(issued_study=SimpleNamespace(candidate=object(), source_closure='original.source'),
        run_plan_id='run.disclosed.e1-read', execution_authority=object())
    selected = SimpleNamespace(payloads={reader.SPECIFICATION_FILENAME: b'disclosed-specification'},
        instance=SimpleNamespace(specification='specification.disclosed'),
        association=SimpleNamespace(candidate='candidate.disclosed'), implementation='original.source',
        projection=plan, draft=object())
    monkeypatch.setattr(reader, '_decode', lambda *args: SimpleNamespace(identity='specification.disclosed'))
    monkeypatch.setattr(reader, '_pin', lambda *args: 'candidate.disclosed')
    monkeypatch.setattr(reader, '_actual_package', lambda *args, **kwargs: package)

    def authenticate(self, **_):
        for manifest in manifests:
            self.read_control(manifest, ObjectIdentity, manifest.materialization.size_bytes)
        self._task_indexes[(id(plan), decimal_context_key())] = (plan, {task.task_id: task for task in tasks})
        return plan

    monkeypatch.setattr(CurrentResultPlanReader, 'authenticate_execution_plan', authenticate)
    monkeypatch.setattr(reader, 'ExternalStudyOperationAuthorityStore',
        lambda _: SimpleNamespace(load=lambda _: object()))
    monkeypatch.setattr(reader, '_replay_parent_authority', lambda *args: (None, object()))
    monkeypatch.setattr(reader, 'original_selection', lambda *args: (object(), ()))
    monkeypatch.setattr(reader, 'exact_graph', lambda *args: ({}, {reader.owner.COMMIT_KEY: object()}))
    monkeypatch.setattr(reader, 'authenticate_prior_publications', lambda *args: None)
    monkeypatch.setattr(reader, 'retained_output_artifact_plane', lambda *args: plane)
    expected = []

    def census(*args, control_reader, **kwargs):
        expected.append(len(control_reader.writer._read_verification.snapshots))
        before = work['checkpoint_hashes']
        for task in tasks:
            assert control_reader.execution_task(execution_plan=plan, task_id=task.task_id) is task
        assert work['checkpoint_hashes'] == before == 0
        if damage:
            path = plane.root.resolve(manifests[-1].materialization.relative_path, for_write=False)
            raw = path.read_bytes()
            path.write_bytes(raw.replace(b'exposed', b'changed', 1))
        raise _EndOfDisclosedControlCensus

    monkeypatch.setattr(reader, '_collect_receipt_closure', census)
    with _work() as work:
        with pytest.raises(ArtifactIdentityConflict if damage else _EndOfDisclosedControlCensus):
            reader.read_result(selected=selected, artifact_writer=plane, run_id=package.run_plan_id,
                reveal_authority_id='reveal.disclosed')
    assert 0 < work['checkpoint_hashes'] <= expected[0]
    if not damage:
        assert work['checkpoint_hashes'] == expected[0]
