# SPDX-License-Identifier: MPL-2.0
"""Disclosed owner routing; no native work or scientific completion evidence."""
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from empirical_lawhood.api import experiment_execution_read, experiment_programme
from empirical_lawhood.api import selected_e4_structure as structure
from empirical_lawhood.api.selected_e4_revision_programme import SelectedE4RevisionAcquisitionService
from empirical_lawhood.kernel.provenance import ObjectIdentity


@pytest.mark.parametrize('mode', ('run', 'recover'))
@pytest.mark.parametrize('scope', ('EXECUTION_RECORDS', 'FULL'))
def test_revision_composite_forwards_selected_scope_through_both_public_owners(monkeypatch, mode, scope):
    calls = []
    service = experiment_programme.ExperimentProgrammeService(Path('/disclosed'), object())
    child = Path('/disclosed/revision/revision-component')
    result = {'read_scope': scope, 'status': 'SUCCEEDED'}
    def operation(**options):
        calls.append(options)
        return result
    owner = SelectedE4RevisionAcquisitionService(service=NS(run=operation, recover=operation))
    monkeypatch.setattr(owner, '_retained', lambda directory: NS(workers=8))
    monkeypatch.setattr(experiment_programme.ExperimentProgrammeService, '_composite_programme', lambda self, **_: owner)
    assert getattr(service, mode)(directory=child.parent, maximum_parallel_tasks=8, result_read_scope=scope) is result
    assert calls == [dict(directory=child, maximum_parallel_tasks=8, result_read_scope=scope)]


@pytest.mark.parametrize('scope', ('EXECUTION_RECORDS', 'FULL'))
def test_completed_revision_inspection_requires_its_exact_retained_plan(monkeypatch, scope):
    pin = ObjectIdentity('plan.disclosed', 'empirical-lawhood/testing/disclosed-plan', '1.0.0', 'a' * 64)
    calls = []
    def read(**options):
        calls.append(options)
        return {'execution_plan': pin.to_document(), 'read_scope': scope}
    programme = NS(child_plan=pin, identity=pin, specification=NS(revision=NS(canonical_bytes=lambda: b'original')))
    owner = SelectedE4RevisionAcquisitionService(service=NS(read_execution=read))
    monkeypatch.setattr(owner, '_retained', lambda directory: programme)
    result = owner.read_execution(directory=Path('/disclosed/revision'))
    assert result['execution_plan'] == pin.to_document()
    assert calls[0]['expected_specification_bytes'] == b'original'
    programme.child_plan = ObjectIdentity('plan.disclosed', 'empirical-lawhood/testing/disclosed-plan', '1.0.0', 'b' * 64)
    with pytest.raises(PermissionError, match='retained child plan'):
        owner.read_execution(directory=Path('/disclosed/revision'))


def test_explicit_development_access_reaches_execution_reader(monkeypatch):
    access = object()
    service = experiment_programme.ExperimentProgrammeService(Path('/disclosed'), object())
    monkeypatch.setattr(experiment_programme.ExperimentProgrammeService, '_composite_programme', lambda self, **_: None)
    monkeypatch.setattr(experiment_programme.ExperimentProgrammeService, '_is_prospective', lambda self, path: False)
    seen = []
    def read(**values):
        seen.append(values)
        assert values['read_access'] is access
        raise PermissionError('current original access refused')
    monkeypatch.setattr(experiment_execution_read, 'read_development_execution', read)
    with pytest.raises(PermissionError, match='current original access'):
        service.read_execution(directory=Path('/disclosed'), read_access=access)
    assert len(seen) == 1


def test_structural_execution_requires_exact_companion_before_receipt_inspection(monkeypatch, tmp_path):
    from empirical_lawhood.api import recursive_authoring
    from tests.test_recursive_public_service import _plane
    writer = _plane(tmp_path/'structural-custody')
    tmp_path = Path(writer.root.contract.canonical_path)
    (tmp_path/'analysis').mkdir()
    access, selected, observer = object(), object(), object()
    options = dict(directory=tmp_path, artifact_writer=writer, programme=object(), bank=object(),
        choices=object(), secondary_readout=object(), resources=object(), campaign=object(),
        declaration=object(), current_access=access, observe_controls=observer)
    seen = []
    monkeypatch.setattr(structure, '_directory', lambda writer, directory: tmp_path)
    monkeypatch.setattr(structure, 'structural_measurement', lambda **_: selected)
    def authored(**values):
        assert values['read_access'] is access
        return None, None, None, selected
    monkeypatch.setattr(recursive_authoring, 'load_authored_wave', authored)
    def companion(**values):
        assert values['payloads'] is selected and values['current_access'] is access
        assert values['declaration'] is options['declaration']
        seen.append('companion')
        return NS(canonical_bytes=lambda: b'original structural specification'), None, None
    monkeypatch.setattr(structure, '_structural_companion', companion)
    def read(**values):
        assert seen == ['companion']
        assert values['read_access'] is access
        assert values['expected_specification_bytes'] == b'original structural specification'
        assert values['observe_controls'] is observer
        return {'execution_complete': True}
    monkeypatch.setattr(experiment_execution_read, 'read_development_execution', read)
    assert structure.read_structural_execution(**options)['execution_complete']
    def refused(**values):
        raise PermissionError('changed original structural companion')
    monkeypatch.setattr(structure, '_structural_companion', refused)
    with pytest.raises(PermissionError, match='changed original structural'):
        structure.read_structural_execution(**options)


def test_absent_structure_never_completes_an_acquisition(monkeypatch, tmp_path):
    monkeypatch.setattr(structure, '_directory', lambda writer, directory: tmp_path)
    result = structure.read_development_structure_execution(directory=tmp_path, artifact_writer=None,
        acquisition_report={'status': 'SUCCEEDED', 'execution_complete': True})
    assert result == {'state': 'NOT_ENTERED', 'execution_complete': False}
