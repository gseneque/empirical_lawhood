# SPDX-License-Identifier: MPL-2.0
"""OU boundaries refuse before compiling/contacting a new numerical source."""

from dataclasses import replace
from decimal import Decimal as D
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_ou_domain import validate_parameter_ou_domain
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import split_parameter_innovations
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.adapters.methods.matrix_parameter_history.operation_bindings import development_draft, operation_factories, operation_registrations, output_codecs
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.test_matrix_parameter_history import source


def changed(gamma):
    s = source()
    c = s.coordinate
    c = replace(c, primary_view=replace(c.primary_view, friction_gamma=D(gamma)),
                fine_view=replace(c.fine_view, friction_gamma=D(gamma)))
    a = replace(s.allocation, coordinates=(c,), roots=(replace(s.root, coordinate=__import__(
        'empirical_lawhood.adapters.methods.matrix_parameter_history.records', fromlist=['coordinate_identity']).coordinate_identity(c)),))
    return replace(s, allocation=a)


@pytest.mark.parametrize('gamma', ('1e-18', '1e308'))
def test_unsupported_decay_refuses_before_native_compilation_or_rng(gamma, monkeypatch):
    s = changed(gamma)
    def blocked(*args, **kwargs):
        raise AssertionError('unsupported OU source entered RNG')
    monkeypatch.setattr(np.random, 'Generator', blocked)
    with pytest.raises(ValueError, match='unsupported numerical OU domain v1'):
        validate_parameter_ou_domain(s.coordinate)
    factories = operation_factories()
    registry = CapabilityRegistry('registry.ou-boundary', tuple(sorted((f.manifest for f in factories), key=lambda m: m.registry_id)))
    with pytest.raises(ValueError, match='unsupported numerical OU domain v1'):
        compile_recursive_wave(draft=development_draft((s,), draft_id='software.ou-boundary'),
            registrations=operation_registrations(), registry=registry, implementation_commit=s.provenance.observed_git_head,
            output_codecs=output_codecs())


@pytest.mark.parametrize('gamma', ('1e-10', '1.3', '600000'))
def test_supported_small_and_large_decay_keep_bath_and_weighted_bridge(gamma):
    c = changed(gamma).coordinate
    admitted = validate_parameter_ou_domain(c)
    values = {name: float.fromhex(value) for name, value in admitted.coefficient_hex}
    assert 0 < values['bridge-half-decay'] < 1
    assert values['primary-noise-scale'] > 0 and values['fine-noise-scale'] > 0
    assert values['fine-decay'] == values['bridge-half-decay']
    coarse = np.zeros((2, 3, 4, 4), dtype='<c16')
    bridge = np.broadcast_to(np.eye(4, dtype='<c16'), coarse.shape).copy()
    first, second = split_parameter_innovations(c, coarse, bridge)
    reconstructed = (values['bridge-half-decay'] * first + second) / values['bridge-denominator']
    np.testing.assert_allclose(reconstructed, coarse, rtol=0, atol=1e-15)
    assert decode_canonical_bytes(admitted.canonical_bytes(), type(admitted), maximum_bytes=None) == admitted


@pytest.mark.parametrize('gamma', ('1e-18', '1e308'))
def test_legacy_native_entry_refuses_without_begin_contact_or_draws(gamma, tmp_path, monkeypatch):
    from tests.test_matrix_parameter_history import context, provider, object_id
    from tests.runtime_platform.test_native_subwork import _plane
    from empirical_lawhood.runtime.native_effects import NativeEffectContact
    from empirical_lawhood.runtime.native_subwork import NativeSubworkState
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    s = changed(gamma)
    _, ctx, manifests, factory = context(_plane(tmp_path / 'unsupported'), s, 'history')
    counts = {'begin': 0, 'contact': 0, 'draws': 0}
    def forbidden(name):
        def call(*args, **kwargs):
            counts[name] += 1
            raise AssertionError('unsupported source entered ' + name)
        return call
    monkeypatch.setattr(np.random, 'Generator', forbidden('draws'))
    parent = NativeEffectContact('test.ou.run', ctx.task_id, 'test.ou.run.' + ctx.task_id + '.attempt-001',
        object_id('test.ou.plan'), ObjectIdentity(ctx.task_id, 'empirical-lawhood/runtime/execution-task', '1.0.0', 'a' * 64), s.provenance.observed_git_head,
        tuple(sorted(m.materialization.materialization_id for m in manifests)), ())
    progress = SimpleNamespace(parent_contact=parent, recover=lambda d: None,
        inspect=lambda d: SimpleNamespace(state=NativeSubworkState.NOT_ENTERED),
        freeze_roster=forbidden('begin'), begin=forbidden('begin'), contact=forbidden('contact'))
    with pytest.raises(ValueError, match='unsupported numerical OU domain v1'):
        provider(factory).execute_with_native_subwork(ctx, progress)
    assert counts == {'begin': 0, 'contact': 0, 'draws': 0}
