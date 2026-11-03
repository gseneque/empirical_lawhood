# SPDX-License-Identifier: MPL-2.0
"""Disclosed orchestration seams; no native work or scientific qualification."""
from contextlib import ExitStack, nullcontext
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import matrix_researcher_programme as owner
from empirical_lawhood.api.matrix_programme_projection import MatrixProgrammePrerequisite
from tests.test_matrix_programme_original_read_lifetime import _case


@pytest.mark.parametrize('phase', ('e2', 'train', 'e3', 'e4.development', 'e4.revision',
    'e4.calibration', 'e4.confirmation', 'e5.development', 'e5.confirmation', 'e6'))
@pytest.mark.parametrize('recover', (False, True))
def test_unconfirmed_programme_stops_before_any_phase_execution_or_recovery(phase, recover):
    service = owner.MatrixResearchProgrammeService(service=SimpleNamespace(artifact_writer=object()))
    # Even source/product decoding is downstream of this explicit dispatch stop.
    with pytest.raises(MatrixProgrammePrerequisite) as caught:
        service._operate_phase(SimpleNamespace(), phase, recover=recover, confirmed=False)
    assert caught.value.phase == phase and caught.value.code == 'WRITE_CONFIRMATION_REQUIRED'


@pytest.mark.parametrize('partial,succeeded', ((False, True), (False, False), (True, True)))
def test_e3_observation_and_original_consumers_share_only_a_complete_live_read(monkeypatch, partial, succeeded):
    status_calls, ordinary_reads = [], []
    with ExitStack() as lifetime:
        projection, arguments, products, state = _case(monkeypatch, lifetime)
        arguments['selected'] = SimpleNamespace(association=SimpleNamespace(candidate=object()))
        products.report = {'scientific_completion': 'RETAINED_ADJUDICATION', 'adverse': True}
        selected, package = arguments['selected'], arguments['package']
        status = SimpleNamespace(succeeded=succeeded)
        def campaign_status(request, *, expected_candidate):
            assert request.run_id == arguments['run_id']
            assert expected_candidate is selected.association.candidate
            status_calls.append(True)
            return status
        service = owner.MatrixResearchProgrammeService(service=SimpleNamespace(
            artifact_writer=SimpleNamespace(root=SimpleNamespace(resolve=lambda *args, **kwargs: 'source')),
            _prospective_report=lambda *args: {'status': 'SUCCEEDED' if succeeded else 'BLOCKED'},
            read=lambda **kwargs: ordinary_reads.append(kwargs) or {'scientific_completion': 'DEFERRED'}))
        context = SimpleNamespace(binding=lambda _: SimpleNamespace(sources=SimpleNamespace(relative_path='source')),
            bound_specification=lambda _: (None, object()), child_directory=lambda _: 'child',
            authority=lambda _: (selected, SimpleNamespace(campaign_status=campaign_status),
                SimpleNamespace(reveal_authority_id=arguments['reveal_authority_id']), package,
                SimpleNamespace(run_plan_id=arguments['run_id']), None),
            original_e3_products=projection.original_e3_products)
        monkeypatch.setattr(service, '_phase_scope', lambda *args: nullcontext())
        monkeypatch.setattr(service, '_authored', lambda *args: True)
        monkeypatch.setattr(owner, 'load_experiment_inputs', lambda *args, **kwargs: SimpleNamespace(method_inputs=None))
        monkeypatch.setattr(owner, '_protocol', lambda _: SimpleNamespace(requires_prospective_runtime_binding=True))
        report = service._read_phase(context, 'e3', allow_partial=partial)
        if partial:
            assert ordinary_reads[0]['allow_partial'] and not status_calls and not state['opens']
        elif not succeeded:
            assert report == {'status': 'BLOCKED'} and not state['opens']
        else:
            assert report['scientific_result'] == products.report
            for _ in range(3):
                with projection.original_e3_products(**arguments) as original:
                    assert original is products
            assert state['opens'] == 1 and state['active'] and not ordinary_reads
    assert state['closes'] == (1 if succeeded and not partial else 0)
