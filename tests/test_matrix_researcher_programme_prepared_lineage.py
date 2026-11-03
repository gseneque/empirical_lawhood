# SPDX-License-Identifier: MPL-2.0
"""Exact current source/run/plan joins after ordinary readers.

Literal transport descriptors isolate correspondence and never authenticate a
synthetic locator as a completed producer or supply execution/reveal authority.
"""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.api.matrix_researcher_programme_lineage import programme_original_product
from empirical_lawhood.api.matrix_programme_projection import MatrixProgrammeProjectionContext
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.test_matrix_sampling_follow_on import prior_product


def _record(pin, field):
    return SimpleNamespace(**{field: pin.object_id}, SCHEMA=pin.object_schema, VERSION=pin.object_version,
        fingerprint=lambda: pin.object_fingerprint)


def _source_context(prior, *, observed=None):
    source = ObjectIdentity('specification.disclosed-source', 'empirical-lawhood/testing/current-source-specification', '1.0.0', 'c' * 64)
    selected = SimpleNamespace(instance=SimpleNamespace(specification=source))
    package = _record(prior.package, 'package_id')
    plan = _record(prior.execution_plan, 'execution_plan_id')
    context = SimpleNamespace(report=lambda phase: {'scientific_result': {'prior_executions': (
        (prior if observed is None else observed).to_document(),)}},
        authority=lambda phase: (selected, None, None, package, SimpleNamespace(run_plan_id=prior.run_id), plan),
        binding=lambda phase: SimpleNamespace(specification=SimpleNamespace(identity=source)))
    return context


@pytest.mark.parametrize('damage', ('run', 'plan', 'package'))
def test_e6_original_source_cannot_be_replaced_by_the_conf_source_or_another_run(damage):
    prior = prior_product(ObjectIdentity('result.disclosed-source',
        'empirical-lawhood/planning/scientific-source-qualification-result', '1.0.0', 'd' * 64)).prior_execution
    context = _source_context(prior)
    assert programme_original_product(context, 'e6.source', prior.record.object_schema) == prior
    changed = replace(prior, run_id=prior.run_id + '.foreign') if damage == 'run' else replace(prior,
        **{'execution_plan' if damage == 'plan' else 'package': replace(
            prior.execution_plan if damage == 'plan' else prior.package, object_fingerprint='e' * 64)})
    with pytest.raises(PermissionError, match='actual selected source phase/run/plan'):
        programme_original_product(_source_context(prior, observed=changed), 'e6.source', prior.record.object_schema)


def test_missing_or_ambiguous_original_source_product_never_supplies_a_locator():
    pin = ObjectIdentity('result.disclosed-source', 'empirical-lawhood/planning/scientific-source-qualification-result', '1.0.0', 'd' * 64)
    prior = prior_product(pin).prior_execution
    context = _source_context(prior)
    context.report = lambda phase: {'scientific_result': {'prior_executions': ()}}
    with pytest.raises(ValueError, match='unique original authenticated producer'):
        programme_original_product(context, 'e6.source', pin.object_schema)
    context.report = lambda phase: {'scientific_result': {'prior_executions': (prior.to_document(), prior.to_document())}}
    with pytest.raises(ValueError, match='unique original authenticated producer'):
        programme_original_product(context, 'e6.source', pin.object_schema)


@pytest.mark.parametrize('damage', ('packet-kind', 'plan-kind', 'different-c'))
def test_train_locator_keeps_original_retained_packet_plan_and_exact_c(tmp_path, monkeypatch, damage):
    from empirical_lawhood.api import native_training_banks, recursive_authoring, recursive_execution
    from empirical_lawhood.adapters.methods.matrix_finite_dt_source_records import MatrixFiniteDtTrainingLocator
    from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan
    from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave
    from tests.test_recursive_public_service import _plane
    plane = _plane(tmp_path / 'actual-guarded-plane')
    packet_pin = ObjectIdentity('packet.literal-original', AuthoredRecursiveWave.SCHEMA, AuthoredRecursiveWave.VERSION, 'a' * 64)
    plan_pin = ObjectIdentity('plan.literal-original', DevelopmentExecutionPlan.SCHEMA, DevelopmentExecutionPlan.VERSION, 'b' * 64)
    packet = _record(packet_pin, 'packet_id')
    plan = _record(plan_pin, 'execution_plan_id')
    c = object()
    request = SimpleNamespace(input_commitments=c)
    monkeypatch.setattr(recursive_authoring, 'load_authored_wave', lambda **_: (packet, object(), object(), object()))
    monkeypatch.setattr(recursive_execution, '_retained_plans', lambda *_: (SimpleNamespace(run_plan_id='run.literal-original'), plan, object()))
    monkeypatch.setattr(native_training_banks, '_read_instance', lambda *_: (None, request, None))
    directory = plane.root.resolve('children/train', for_write=False)
    context = SimpleNamespace(writer=plane, child_directory=lambda phase: directory, phase_origins={},
        plan=SimpleNamespace(specification=SimpleNamespace(input_commitments=c)))
    from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_operation
    def locate():
        with scientific_reconstruction_operation('full'):
            return MatrixProgrammeProjectionContext.native_training_locator(context)
    actual = locate()
    assert type(actual) is MatrixFiniteDtTrainingLocator
    assert (actual.packet, actual.execution_plan, actual.run_id) == (packet_pin, plan_pin, 'run.literal-original')
    if damage == 'different-c':
        request.input_commitments = object()
        with pytest.raises(PermissionError, match='original C publication'):
            locate()
    else:
        original = packet if damage == 'packet-kind' else plan
        original.SCHEMA = 'empirical-lawhood/testing/wrong-retained-header'
        with pytest.raises((ValueError, TypeError)):
            locate()
