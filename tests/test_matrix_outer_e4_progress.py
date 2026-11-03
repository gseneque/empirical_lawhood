# SPDX-License-Identifier: MPL-2.0
"""Outer E4 routing checks; isolated state sentinels grant no authority."""
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import matrix_researcher_programme as outer
from empirical_lawhood.api import matrix_programme_e4_phases as projections
from empirical_lawhood.api import selected_e4_programme_service as e4
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.test_recursive_public_service import _plane


def _unexecuted_phase(tmp_path, monkeypatch, phase, authorized):
    writer = _plane(tmp_path / 'custody')
    directory = Path(writer.root.contract.canonical_path) / 'programme' / phase
    directory.mkdir(parents=True)
    identity = ObjectIdentity('plan.disclosed-outer-routing', e4.d.SelectedE4ProtectedProgrammePlan.SCHEMA,
        e4.d.SelectedE4ProtectedProgrammePlan.VERSION, 'b' * 64)
    wave = SimpleNamespace(wave_id='wave.disclosed', group_ids=('group.disclosed',))
    programme = SimpleNamespace(group_ids=wave.group_ids, cases=(), waves=(wave,))
    plan = SimpleNamespace(identity=identity, component_ids=(wave.wave_id, 'assessment'),
        declaration=SimpleNamespace(programme=programme))
    components = () if not authorized else (e4.SelectedE4ComponentRequest(wave.wave_id, 'run.disclosed-wave',
        'controls/disclosed-package.json', 'authority.disclosed-reveal', None, ()),)
    request = e4.SelectedE4ProgrammeRequest('request.disclosed-outer-routing', identity, components, None)
    service = SimpleNamespace(artifact_writer=writer)
    child = e4.SelectedE4ProgrammeService(service=service)
    service._composite_programme = lambda **_kw: child
    owner = outer.MatrixResearchProgrammeService(service=service)
    monkeypatch.setattr(child, '_state', lambda _directory: (plan, None))
    monkeypatch.setattr(child, '_unentered', lambda _plan: None)
    monkeypatch.setattr(owner, '_phase_scope', lambda *_args: nullcontext())
    monkeypatch.setattr(owner, '_authored', lambda *_args: True)
    monkeypatch.setattr(outer, '_protocol', lambda _specification: object())
    monkeypatch.setattr(outer, 'load_experiment_inputs', lambda *_a, **_kw: SimpleNamespace(method_inputs=SimpleNamespace(plan=plan)))
    monkeypatch.setattr(projections, 'programme_e4_request', lambda *_args: request)
    context = SimpleNamespace(binding=lambda _phase: SimpleNamespace(sources=SimpleNamespace(relative_path='unused-input.json')),
        bound_specification=lambda _binding: (None, object()), child_directory=lambda _phase: directory)
    return owner, context, directory


@pytest.mark.parametrize('phase', ('e4.calibration', 'e4.confirmation'))
@pytest.mark.parametrize('authorized', (False, True))
def test_authored_frontier_does_not_require_future_wave_products(tmp_path, monkeypatch, phase, authorized):
    owner, context, _ = _unexecuted_phase(tmp_path, monkeypatch, phase, authorized)
    report = owner._read_phase(context, phase)
    assert report['state'] == 'UNASSESSED'
    assert report['new_native_contact_count'] == 0
    assert report['missing_components'] == (('assessment',) if authorized else ('wave.disclosed', 'assessment'))
    assert not outer._phase_complete(phase, report)
    assert not (Path(owner.writer.root.contract.canonical_path) / 'runs').exists()


@pytest.mark.parametrize('phase', ('e4.calibration', 'e4.confirmation'))
def test_existing_structure_without_actual_wave_custody_still_refuses(tmp_path, monkeypatch, phase):
    from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
    owner, context, directory = _unexecuted_phase(tmp_path, monkeypatch, phase, True)
    (directory / 'structure' / 'analysis').mkdir(parents=True)
    with pytest.raises(ArtifactIdentityConflict, match='artifact sidecar metadata is invalid'):
        owner._read_phase(context, phase)
    assert not (Path(owner.writer.root.contract.canonical_path) / 'runs').exists()
