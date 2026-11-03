# SPDX-License-Identifier: MPL-2.0
"""Current E4 routing only; controlled preflight and products are not custody."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import selected_e4_programme_service as owner
from tests.test_matrix_selected_e4_programme_status import wrapper_state
from tests.test_recursive_public_service import _plane


@pytest.mark.parametrize('retained', (('wave.a',), ('assessment',), ('wave.a', 'assessment')))
def test_run_continues_each_actual_retained_component_through_recovery(tmp_path, monkeypatch, retained):
    writer = _plane(tmp_path / 'custody')
    root = Path(writer.root.contract.canonical_path)
    (root / 'programme/components/assessment').mkdir(parents=True)
    for component in retained:
        run = 'run.wave.a' if component == 'wave.a' else 'run.assessment'
        # Deliberately invalid presence sentinel: only dispatch is under test.
        # The controlled preflight below does not admit it as real custody.
        path = root / 'runs' / run / 'plans/campaign-package.json'
        path.parent.mkdir(parents=True)
        path.write_bytes(b'disclosed routing sentinel; not a package\n')
    calls, preflight = [], []
    def run(**kwargs):
        calls.append(('run', Path(kwargs['directory']).name))
        return {'status': 'SUCCEEDED'}
    def recover(**kwargs):
        calls.append(('recover', Path(kwargs['directory']).name))
        return {'status': 'SUCCEEDED'}
    service = SimpleNamespace(artifact_writer=writer, run=run, recover=recover,
        read=lambda **kwargs: {"status": "SUCCEEDED"})
    wrapper, plan, request = wrapper_state(monkeypatch, service)
    request.collection = SimpleNamespace(evidence=SimpleNamespace(declaration=plan.declaration.identity,
        waves=(SimpleNamespace(locator='disclosed.wave.locator'),)))
    def prepare(**kwargs):
        component = kwargs['selected'].component_id
        preflight.append((component, kwargs['recover']))
        return root / 'programme/components' / component, object()
    monkeypatch.setattr(wrapper, '_preflight_component', prepare)
    monkeypatch.setattr(owner, '_locator', lambda *_args: 'disclosed.wave.locator')
    monkeypatch.setattr(wrapper, '_structure', lambda **_kwargs: ((), {'new_native_contact_count': 0}))
    monkeypatch.setattr(wrapper, '_publish_observations', lambda *_args: None)
    wrapper.run(directory=root / 'programme', maximum_parallel_tasks=4, confirmed=True)
    assert preflight == [(component, component in retained) for component in ('wave.a', 'assessment')]
    assert calls == [('recover' if component in retained else 'run', component) for component in ('wave.a', 'assessment')]
