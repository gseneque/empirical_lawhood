"""Original parameter-history initial custody projected without native entry.

The sealed operands and unpublished anticipated contact are exposed software
fixtures. These controls establish no worker readiness or scientific authority.
"""
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_parameter_history import (
    chunked_operation_bindings as chunked,
    compact_operation_bindings as compact,
    operation_bindings as legacy,
)
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.execution import TaskContext, WorkerIsolationProfile
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef
from empirical_lawhood.infrastructure.execution import _prepare_native_work
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.runtime_platform.test_native_subwork import _plane
from tests.test_matrix_parameter_history import context as legacy_context, object_id, provider, source
from tests.test_matrix_parameter_compact_history import context as compact_context, selected
from tests.test_matrix_parameter_chunked_history import context as chunked_context, selection


def _case(tmp_path, owner):
    plane = _plane(tmp_path/'sealed-originals')
    if owner is legacy:
        config, context, manifests, factory = legacy_context(plane, source(), 'history')
    elif owner is compact:
        sources, allocation, provenance = selected()
        config, context, manifests, factory = compact_context(plane, sources[0], allocation, provenance, 'history')
    else:
        selected_source, allocation, provenance = selection()
        config, context, manifests, factory = chunked_context(plane, selected_source, allocation, provenance, 'history')
    parent = NativeEffectContact('test.parameter.prepared', context.task_id,
        'test.parameter.prepared.'+context.task_id+'.attempt-001', object_id('test.parameter.plan'),
        ObjectIdentity(context.task_id, 'empirical-lawhood/runtime/execution-task', '1.0.0', 'a'*64), 'd'*40,
        tuple(sorted(value.materialization.materialization_id for value in manifests)), ())
    ports = tuple(sorted(context.input_ports, key=lambda port: port.artifact_id))
    context = TaskContext(parent.run_id, context.task_id, parent.attempt_id,
        CapabilityConfigRef(config.config_id, config.SCHEMA, factory.manifest.config_schema_sha256,
            config.fingerprint(), config.config_id), tuple(port.binding for port in ports), ports,
        tuple(sorted(context.output_ports, key=lambda port: port.output_id)), context.permissions,
        context.outcome_access, context.resource_budget, WorkerIsolationProfile.TRUSTED_LOCAL)
    return plane, config, context, manifests, factory, parent


@pytest.mark.parametrize('owner', (legacy, compact, chunked), ids=('original', 'compact', 'chunked'))
def test_repeated_preparation_retains_exact_original_initial_definition_and_no_custody_entry(tmp_path, owner):
    plane, config, context, manifests, factory, parent = _case(tmp_path, owner)
    before = {path.relative_to(tmp_path).as_posix(): path.read_bytes() for path in tmp_path.rglob('*') if path.is_file()}
    runner = provider(factory)
    first = _prepare_native_work(owner.prepare_native_work, runner, context, parent)
    second = _prepare_native_work(owner.prepare_native_work, runner, context, parent)
    assert first == second
    assert all(port.tell() == 0 for port in context.input_ports)
    assert first.scientific_unit_ids == owner.scientific_unit_ids(config)
    assert first.native_effect_slot_ids == owner.native_effect_slot_ids(config)
    assert len(first.definitions) == len(first.rosters) == 1
    decoded = owner._decode_inputs(context, 'history')[1]
    original = owner.carrier_definition if owner is chunked else owner.native_definition
    assert first.definitions[0].canonical_bytes() == original(context, config, decoded,
        SimpleNamespace(parent_contact=parent)).canonical_bytes()
    assert first.definitions[0].input_materialization_ids == tuple(sorted(value.materialization.materialization_id for value in manifests))
    assert first.rosters[0].subworks == (first.definitions[0].identity,)
    assert {path.relative_to(tmp_path).as_posix(): path.read_bytes() for path in tmp_path.rglob('*') if path.is_file()} == before
    assert not plane.root.resolve('runs/test.parameter.prepared', for_write=False).exists()
    for port in context.input_ports:
        port.close()


@pytest.mark.parametrize('owner', (legacy, compact, chunked), ids=('original', 'compact', 'chunked'))
def test_preparation_refuses_incomplete_original_stream_census_without_entry(tmp_path, owner):
    _, _, context, _, factory, parent = _case(tmp_path, owner)
    from empirical_lawhood.adapters.methods.matrix_history_analysis.records import MatrixHistorySeed
    omitted = next(port for port in context.input_ports if port.payload_schema == MatrixHistorySeed.SCHEMA)
    from dataclasses import replace
    remaining = tuple(port for port in context.input_ports if port is not omitted)
    context = replace(context, input_bindings=tuple(port.binding for port in remaining), input_ports=remaining)
    with pytest.raises(ValueError, match='stream'):
        _prepare_native_work(owner.prepare_native_work, provider(factory), context, parent)
    for port in (*context.input_ports, omitted):
        port.close()


def test_all_five_parameter_native_operations_use_declared_preparation_and_pure_phases_do_not():
    from empirical_lawhood.adapters.methods.matrix_parameter_response import operation_bindings, paired_operation_bindings
    owners = (legacy, compact, chunked, operation_bindings, paired_operation_bindings)
    native = []
    for owner in owners:
        declarations = owner.operation_declarations()
        assert tuple(row.manifest() for row in declarations) == owner.operation_manifests()
        assert tuple(row.registration() for row in declarations) == owner.operation_registrations()
        for row in declarations:
            registration = row.registration()
            if registration.native_effect:
                assert registration.native_work_preparer is owner.prepare_native_work
                native.append(row.capability_key)
            else:
                assert registration.native_work_preparer is None
    assert len(native) == 5
