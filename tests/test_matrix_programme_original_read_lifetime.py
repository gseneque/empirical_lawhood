# SPDX-License-Identifier: MPL-2.0
"""Operation-local reuse retains live custody; disclosed reader seam only."""
from contextlib import ExitStack, contextmanager
from dataclasses import replace
from types import SimpleNamespace
import sys

import pytest

from empirical_lawhood.api.matrix_programme_projection import MatrixProgrammeProjectionContext
from empirical_lawhood.api.domain_composition.matrix_configured_protected_response import scientific_read
from empirical_lawhood.api.prospective_experiment import RetainedProspectiveExperiment
from empirical_lawhood.kernel.provenance import ObjectIdentity


def _case(monkeypatch, lifetime):
    state = {'opens': 0, 'closes': 0, 'checks': 0, 'active': False, 'refusal': None}

    def current():
        state['checks'] += 1
        if not state['active']:
            raise PermissionError('original read expired')
        if state['refusal']:
            raise PermissionError(state['refusal'])

    products = SimpleNamespace(require_current=current)

    @contextmanager
    def reader(**options):
        state['opens'] += 1
        state['active'] = True
        try:
            current()
            yield products
            current()
        finally:
            state['active'] = False
            state['closes'] += 1

    monkeypatch.setattr(scientific_read, 'read_protected_e3_original_products', reader)
    context = MatrixProgrammeProjectionContext(SimpleNamespace(artifact_writer=object()),
        None, None, None, {}, {}, _read_lifetime=lifetime)
    arguments = dict(selected=object(), package=object(), run_id='run.original', reveal_authority_id='reveal.original')
    return context, arguments, products, state


@pytest.mark.parametrize('uses', [2, 4])
def test_one_original_read_per_operation_checks_each_use_and_expires(monkeypatch, uses):
    with ExitStack() as lifetime:
        context, arguments, products, state = _case(monkeypatch, lifetime)
        for _ in range(uses):
            with context.original_e3_products(**arguments) as actual:
                assert actual is products
        assert state['opens'] == 1 and state['closes'] == 0
        assert state['checks'] >= 1 + 2 * uses
    assert state['closes'] == 1
    with pytest.raises(PermissionError, match='expired'):
        products.require_current()
    with pytest.raises(PermissionError, match='expired'):
        with context.original_e3_products(**arguments):
            pytest.fail('a closed operation reused its products')


@pytest.mark.parametrize('refusal', ['current reveal revoked', 'original member changed', 'current reveal expired'])
def test_cached_originals_recheck_custody_and_access_before_reuse(monkeypatch, refusal):
    with ExitStack() as lifetime:
        context, arguments, _, state = _case(monkeypatch, lifetime)
        with context.original_e3_products(**arguments):
            pass
        state['refusal'] = refusal
        try:
            with pytest.raises(PermissionError, match=refusal):
                with context.original_e3_products(**arguments):
                    pytest.fail('stale custody or permission entered protected consumer')
        finally:
            state['refusal'] = None
        assert state['opens'] == 1


def test_originals_recheck_after_consumer_before_return(monkeypatch):
    with ExitStack() as lifetime:
        context, arguments, _, state = _case(monkeypatch, lifetime)
        try:
            with pytest.raises(PermissionError, match='original member changed'):
                with context.original_e3_products(**arguments):
                    state['refusal'] = 'original member changed'
        finally:
            state['refusal'] = None


@pytest.mark.parametrize('field', ['selected', 'package', 'run_id', 'reveal_authority_id'])
def test_original_read_cannot_change_its_source_or_authority(monkeypatch, field):
    with ExitStack() as lifetime:
        context, arguments, _, state = _case(monkeypatch, lifetime)
        with context.original_e3_products(**arguments):
            pass
        changed = {**arguments, field: object() if field in ('selected', 'package') else 'foreign'}
        with pytest.raises(PermissionError, match='original E3 read binding'):
            with context.original_e3_products(**changed):
                pytest.fail('substitution entered cached original read')
        assert state['opens'] == 1


def test_standalone_projection_uses_separate_original_lifetimes(monkeypatch):
    context, arguments, _, state = _case(monkeypatch, None)
    for _ in range(2):
        with context.original_e3_products(**arguments):
            assert state['active']
        assert not state['active']
    assert state['opens'] == state['closes'] == 2


def test_outer_operation_exit_rechecks_retained_originals(monkeypatch):
    with pytest.raises(PermissionError, match='original member changed'):
        with ExitStack() as lifetime:
            context, arguments, _, state = _case(monkeypatch, lifetime)
            with context.original_e3_products(**arguments):
                pass
            state['refusal'] = 'original member changed'
    assert state['closes'] == 1 and not state['active']


def _literal_retained():
    """Canonical literal fields isolate binding ownership, not source admission."""
    pin = ObjectIdentity('literal.original', 'empirical-lawhood/testing/read-lifetime', '1.0.0', 'a' * 64)
    return RetainedProspectiveExperiment(pin, pin, pin, pin, pin, pin,
        {'literal.json': b'{"literal":true}\n'})


def test_live_binding_does_not_keep_completed_authoring_body(monkeypatch):
    with ExitStack() as lifetime:
        context, arguments, products, state = _case(monkeypatch, lifetime)
        selected = _literal_retained()
        # This reader consumes its argument before yielding. The programme's
        # binding must not retain another full immutable authoring packet.
        @contextmanager
        def reader(**options):
            assert options.pop('selected') is selected
            state['active'] = True
            try:
                yield products
            finally:
                state['active'] = False
        monkeypatch.setattr(scientific_read, 'read_protected_e3_original_products', reader)
        arguments.pop('selected')
        with context.original_e3_products(selected=selected, **arguments):
            references = sys.getrefcount(selected)
            assert references == 2
        with context.original_e3_products(selected=replace(selected), **arguments):
            pass


@pytest.mark.parametrize('field', ('association', 'instance', 'candidate', 'projection', 'implementation',
    'draft', 'payloads', 'payload-bytes', 'original_input_access'))
def test_compact_original_binding_preserves_every_retained_field(monkeypatch, field):
    with ExitStack() as lifetime:
        context, arguments, _, state = _case(monkeypatch, lifetime)
        selected = _literal_retained()
        arguments['selected'] = selected
        with context.original_e3_products(**arguments):
            pass
        changed = ({name: b'changed' for name in selected.payloads} if field == 'payload-bytes' else
            dict(selected.payloads, extra=b'changed') if field == 'payloads' else
            object() if field == 'original_input_access' else replace(getattr(selected, field), object_id='literal.changed'))
        arguments['selected'] = replace(selected, **{'payloads' if field == 'payload-bytes' else field: changed})
        with pytest.raises(PermissionError, match='original E3 read binding'):
            with context.original_e3_products(**arguments):
                pytest.fail('changed retained field entered the same scientific read')
        assert state['opens'] == 1
