"""Focused ownership and current-byte controls for structural method provenance."""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from empirical_lawhood.science.identity.structural_recurrence_source import (
    _METHOD_FILES, MarginStructuralRecurrenceForecastMethodSourceManifest,
)
from empirical_lawhood.storage import structural_recurrence_source as source


@pytest.fixture
def selected_method_files(tmp_path, monkeypatch):
    methods = tmp_path / 'methods'
    methods.mkdir()
    for name in _METHOD_FILES:
        (methods / name).write_text('# ' + name + '\npass\n')
    storage = tmp_path / 'storage'
    storage.mkdir()
    monkeypatch.setattr(source, '__file__', str(storage / 'structural_recurrence_source.py'))
    return methods


def test_manifest_reads_exact_current_bytes_and_detects_changed_source(selected_method_files):
    before = source.method_source_manifest()
    assert len(before.source_files) == 7
    for row in before.source_files:
        assert row.sha256 == sha256((selected_method_files / Path(row.repository_path).name).read_bytes()).hexdigest()
    path = selected_method_files / _METHOD_FILES[0]
    path.write_text(path.read_text() + '# changed implementation\n')
    after = source.method_source_manifest()
    assert before.fingerprint() != after.fingerprint()
    assert sum(a != b for a, b in zip(before.source_files, after.source_files, strict=True)) == 1


@pytest.mark.parametrize('condition', ['missing', 'empty', 'symlink', 'oversized'])
def test_source_census_refuses_unusable_members(selected_method_files, condition):
    path = selected_method_files / _METHOD_FILES[0]
    if condition == 'missing':
        path.unlink()
    elif condition == 'empty':
        path.write_bytes(b'')
    elif condition == 'oversized':
        path.write_bytes(b'x' * (2 * 1024 * 1024 + 1))
    else:
        target = selected_method_files / 'other.py'
        target.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(target)
    with pytest.raises(ValueError, match='missing or outside its byte bound'):
        source.method_source_manifest()


def test_source_identity_contract_is_pure_and_preserves_schema(selected_method_files, monkeypatch):
    manifest = source.method_source_manifest()
    monkeypatch.setattr(Path, 'read_bytes', lambda *_: pytest.fail('A scientific identity read a file'))
    rebuilt = MarginStructuralRecurrenceForecastMethodSourceManifest(manifest.manifest_id, manifest.source_files)
    assert rebuilt.canonical_bytes() == manifest.canonical_bytes()
    assert rebuilt.SCHEMA == 'empirical-lawhood/methods/margin-structural-recurrence-forecast-method-source-manifest'
    with pytest.raises(ValueError, match='escapes the method package'):
        replace(manifest.source_files[0], repository_path='src/empirical_lawhood/storage/other.py')


def test_source_census_effect_has_no_retired_method_forwarder():
    from empirical_lawhood.methods import structural_recurrence_runtime
    assert not hasattr(structural_recurrence_runtime, 'method_source_manifest')


@pytest.mark.parametrize('operation_name', ['CONFORMANCE', 'PREDICT', 'MATCH', 'ADJUDICATE', 'TARGET_COMPATIBILITY_AUDIT'])
def test_registered_method_config_builder_produces_valid_stable_identity(operation_name):
    from empirical_lawhood.methods.structural_recurrence_runtime import runtime_config, MarginStructuralRecurrenceForecastRuntimeOperation
    operation = MarginStructuralRecurrenceForecastRuntimeOperation(operation_name)
    config = runtime_config(operation)
    assert config.operation is operation
    assert config.method_source_manifest_sha256 == source.method_source_manifest().fingerprint()
    assert config.config_id == 'independent-substrate-grounding.margin-structural-recurrence-forecast.' + operation_name.lower().replace('_', '-') + '.config'


def test_semantic_port_inventory_has_valid_complete_operation_identities():
    from empirical_lawhood.methods.structural_recurrence_runtime import semantic_port_inventory, MarginStructuralRecurrenceForecastRuntimeOperation
    inventory = semantic_port_inventory()
    assert {entry.operation for entry in inventory.bindings} == set(MarginStructuralRecurrenceForecastRuntimeOperation)
    assert len(inventory.bindings) == 5
    assert inventory.scientific_operators_changed is False
