# SPDX-License-Identifier: MPL-2.0
"""Finite metadata bounds and existing locator grouping, without execution."""

from dataclasses import replace

import pytest

from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.execution.recursive_qualified_parents import PRIOR_RECORD_ID_FIELDS, RecursivePriorExecutionBinding, inspect_prior_execution_bindings, prior_result_capacity, require_prior_execution_bindings
from scripts.examples.prior_result_capacity import disclosed_locator


def test_two_original_groups_keep_all_432_native_and_eight_companion_references():
    values = (disclosed_locator(0), disclosed_locator(1))
    report = inspect_prior_execution_bindings(values)
    assert report['prior_execution_count'] == report['distinct_run_count'] == 2
    assert report['native_reference_count'] == report['distinct_native_definition_count'] == 432
    assert report['companion_schema_reference_count'] == 8
    assert report['declared_binding_bytes'] == sum(len(value.canonical_bytes()) for value in values)
    assert len(report['binding_identities']) == 2
    assert report['independent_unit_count'] is None and report['authenticated_receipts'] is False
    for value in values:
        restored = decode_canonical_bytes(value.canonical_bytes(), RecursivePriorExecutionBinding, maximum_bytes=1024 * 1024)
        assert restored == value and restored.canonical_bytes() == value.canonical_bytes()
        assert tuple((native.definition, native.completion, native.receipt) for native in restored.native_subwork) == tuple(
            (native.definition, native.completion, native.receipt) for native in value.native_subwork)


@pytest.mark.parametrize('field', PRIOR_RECORD_ID_FIELDS)
def test_all_seven_original_identifier_fields_retain_exact_revision_one(field):
    value = replace(disclosed_locator(0, native_count=0, companion_count=0), record_id_field=field)
    restored = decode_canonical_bytes(value.canonical_bytes(), RecursivePriorExecutionBinding, maximum_bytes=16 * 1024)
    assert restored == value and value.VERSION == '1.0.0'
    assert prior_result_capacity()['record_identifier_fields'] == PRIOR_RECORD_ID_FIELDS


@pytest.mark.parametrize('change,diagnostic', (
    ({'native_count': 217}, 'bounded subwork census'),
    ({'companion_count': 5}, 'bounded exact schema census'),
))
def test_original_revision_refuses_single_binding_overflow(change, diagnostic):
    with pytest.raises(ValueError, match=diagnostic):
        disclosed_locator(0, **change)


def test_new_identifier_field_needs_a_supported_versioned_transition():
    with pytest.raises(ValueError, match='explicit installed record identifier field'):
        replace(disclosed_locator(0, native_count=0, companion_count=0), record_id_field='measurement_id')


def test_outer_census_accepts_32_original_tasks_and_refuses_33_or_duplicate_splitting():
    values = tuple(disclosed_locator(i, native_count=0, companion_count=0) for i in range(32))
    assert inspect_prior_execution_bindings(values)['prior_execution_count'] == 32
    with pytest.raises(PermissionError, match='bounded exhaustive exact locator census'):
        require_prior_execution_bindings((*values, disclosed_locator(32, native_count=0, companion_count=0)))
    # A renamed binding is not another original task or another independent unit.
    with pytest.raises(PermissionError, match='bounded exhaustive exact locator census'):
        require_prior_execution_bindings((values[0], replace(values[0], binding_id='disclosed.other-binding')))
    with pytest.raises(PermissionError, match='bounded exhaustive exact locator census'):
        require_prior_execution_bindings((values[0], replace(values[1], binding_id=values[0].binding_id)))
    with pytest.raises(PermissionError, match='bounded exhaustive exact locator census'):
        require_prior_execution_bindings(())
    with pytest.raises(PermissionError, match='bounded exhaustive exact locator census'):
        require_prior_execution_bindings(list(values))


def test_conformance_reports_actual_shared_limits_without_execution(monkeypatch):
    from empirical_lawhood.api import recursive_qualified_parents as replay
    from empirical_lawhood.execution.extension_conformance import inspect_extension_contracts
    from tests.runtime_platform.test_extension_conformance import selected
    selection, _ = selected()
    monkeypatch.setattr(replay, '_output_payload', lambda *a, **kw: pytest.fail('static capacity read payloads'))
    report = inspect_extension_contracts(selection)
    capacity = report['prior_result_capacity']
    assert capacity == prior_result_capacity() and report['executed_callbacks'] == 0
    assert capacity['maximum_prior_executions_per_parent'] == replay.MAX_PRIOR_EXECUTIONS == 32
    assert capacity['maximum_parent_bindings'] == replay.MAX_PARENT_BINDINGS == 32
    assert capacity['primary_payload_maximum_bytes'] == replay.MAX_PARENT_BYTES == 16 * 1024**2
    assert capacity['companion_aggregate_maximum_bytes'] == capacity['scope_metadata_aggregate_maximum_bytes'] == 16 * 1024**2
    assert not capacity['independent_units_inferred'] and not capacity['complete_memory_capacity_established']
