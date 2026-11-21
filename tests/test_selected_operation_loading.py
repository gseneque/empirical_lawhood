# SPDX-License-Identifier: MPL-2.0
"""Static selected composition, exact old census and no native prerequisite contact."""

from dataclasses import replace
import subprocess
import sys

import pytest

from empirical_lawhood.api import recursive_operations as operations


def test_generated_selection_preserves_complete_registrations_codecs_and_registry():
    from empirical_lawhood.api.recursive_operation_index import operation_registry, operation_record_codecs, operation_storage_codecs, selected_factories
    from empirical_lawhood.storage.contracts.recursive_storage_codecs import storage_codec_census
    from scripts.generate_executable_binding_aggregate import RECURSIVE_OUTPUT, discover_descriptors, render_recursive_index

    registrations, registry, codecs = operations.operation_catalog()
    selected = selected_factories(row.selection.selection_id for row in registrations)
    assert tuple(row.registration for row in selected) == registrations
    assert operation_registry().canonical_bytes() == registry.canonical_bytes()
    assert dict(operation_record_codecs()) == codecs
    assert operation_storage_codecs() == storage_codec_census(registrations)
    assert RECURSIVE_OUTPUT.read_text() == render_recursive_index(discover_descriptors())


def test_selected_battery_compilation_keeps_every_canonical_root():
    from empirical_lawhood.domains.battery.battery_recursive_construction.examples import battery_wave_a_draft
    from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave

    draft = battery_wave_a_draft()
    old = operations.operation_catalog()
    current = operations.operation_catalog_for_draft(draft)
    assert len(current[0]) < len(old[0])
    def compile(catalog):
        registrations, registry, codecs = catalog
        return compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
            implementation_commit='a' * 40, output_codecs=codecs)
    assert compile(old) == compile(current)


def test_selection_does_not_import_unrelated_factories_or_native_stacks():
    subprocess.run([sys.executable, '-c', '''
import sys
from importlib.abc import MetaPathFinder
class NoNative(MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'pyscf', 'pybamm', 'brian2', 'cantera', 'sky', 'gym_torax'}:
            raise AssertionError('static discovery attempted a native prerequisite: ' + fullname)
sys.meta_path.insert(0, NoNative())
from empirical_lawhood.domains.battery.battery_recursive_construction.examples import battery_wave_a_draft
from empirical_lawhood.api.recursive_operations import operation_catalog_for_draft, operation_record_codecs
rows, registry, codecs = operation_catalog_for_draft(battery_wave_a_draft())
assert rows and len(registry.capabilities) > len(rows)
assert codecs is operation_record_codecs()
assert 'empirical_lawhood.adapters.composition.generated_executable_bindings' not in sys.modules
assert not any(key.startswith('empirical_lawhood.domains.rubisco.rubisco_response') for key in sys.modules)
assert not any(key.startswith('empirical_lawhood.domains.matrix.matrix_scheduled_history') for key in sys.modules)
'''], check=True, timeout=60)


def test_ordinary_development_read_and_absent_repair_do_not_load_matrix_science():
    subprocess.run([sys.executable, '-c', '''
import sys
from importlib.abc import MetaPathFinder
class NoUnrelatedScience(MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if (fullname == 'empirical_lawhood.execution.generated_extension_bundles'
                or fullname.startswith('empirical_lawhood.domains.matrix.matrix_factor_response')):
            raise AssertionError('ordinary read imported unrelated science: ' + fullname)
sys.meta_path.insert(0, NoUnrelatedScience())
from empirical_lawhood.api.experiment_scientific_read import _development_runtime_context
assert _development_runtime_context(payloads={}, draft=None, callback_name='read_development_result') is None
for name in ('experiment-instance.json', 'experiment-specification.json'):
    try:
        _development_runtime_context(payloads={name: b'{}'}, draft=None, callback_name='read_development_result')
    except ValueError as error:
        assert 'omits an original experiment companion' in str(error)
    else:
        raise AssertionError('partial original companion accepted')
from empirical_lawhood.api import development_output_repair
assert development_output_repair.repair_relative_path('exposed.rc')
'''], check=True, timeout=60)


def test_recursive_cli_help_keeps_the_same_numerical_census_as_the_selected_engine():
    subprocess.run([sys.executable, '-c', '''
import sys
from importlib.abc import MetaPathFinder
class NoUnrelatedScience(MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if (fullname == 'empirical_lawhood.execution.generated_extension_bundles'
                or fullname.startswith('scipy.linalg')):
            raise AssertionError('recursive CLI changed the selected numerical census: ' + fullname)
sys.meta_path.insert(0, NoUnrelatedScience())
from empirical_lawhood.cli.entry import enforce_single_thread_environment
enforce_single_thread_environment()
from empirical_lawhood.workbench.engine import describe_engine
assert describe_engine()['operations']
from empirical_lawhood.domains.circuits.rc_prerequisite_chain.science import default_chain_config
from empirical_lawhood.domains.circuits.rc_prerequisite_chain.recursive_translation import rc_recursive_draft
from empirical_lawhood.api.recursive_operations import operation_catalog_for_draft
config = default_chain_config()
draft = rc_recursive_draft(config, unit_ids=(config.units[6].unit_id,), include_summary=False)
assert operation_catalog_for_draft(draft)[0]
from empirical_lawhood.storage.numerical_provenance import numerical_runtime_observation
before = numerical_runtime_observation()
from empirical_lawhood.cli.app import app
from typer.testing import CliRunner
result = CliRunner().invoke(app, ['campaign', 'recursive-development-run', '--help'])
assert result.exit_code == 0, result.output
assert '--authoring-dir' in result.output and '--workers' in result.output
assert numerical_runtime_observation() == before
'''], check=True, timeout=60)


def test_equilibrium_bridge_selection_preserves_the_complete_registry_without_native_imports():
    subprocess.run([sys.executable, '-c', '''
import sys
from importlib.abc import MetaPathFinder
class NoNative(MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'pyscf', 'pybamm', 'brian2', 'cantera', 'sky', 'gym_torax'}:
            raise AssertionError('bridge selection touched a native prerequisite: ' + fullname)
sys.meta_path.insert(0, NoNative())
from empirical_lawhood.api.recursive_operation_index import operation_registry, selected_factories
from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge.bindings import operation_declarations
before = operation_registry().canonical_bytes()
expected = tuple(row.registration() for row in operation_declarations())
actual = selected_factories(row.selection.selection_id for row in expected)
assert {row.registration.selection.selection_id: row.registration for row in actual} == {
    row.selection.selection_id: row for row in expected}
assert operation_registry().canonical_bytes() == before
assert 'empirical_lawhood.adapters.composition.generated_executable_bindings' not in sys.modules
assert not any(name.startswith('empirical_lawhood.domains.rubisco.rubisco_response') for name in sys.modules)
'''], check=True, timeout=60)


def test_unknown_keys_never_supply_import_locations(monkeypatch):
    from empirical_lawhood.api import recursive_operation_index as index
    calls = []
    monkeypatch.setattr(index, 'import_module', lambda name: calls.append(name))
    with pytest.raises(ValueError, match='installed executable'):
        index.selected_factories(('untrusted.module:runner@1.0.0',))
    assert calls == []
    with pytest.raises(KeyError):
        index.operation_record_codecs()['untrusted.module:codec']
    assert calls == []


def test_selected_factory_refuses_changed_metadata_and_duplicate_owner(monkeypatch):
    from copy import copy
    from empirical_lawhood.api import recursive_operation_index as index
    from empirical_lawhood.domains.battery.battery_recursive_construction import extension as owner
    factory = owner.EXTENSION.factories[0]
    key = factory.registration.selection.selection_id
    with monkeypatch.context() as patch:
        forged = copy(owner.EXTENSION)
        object.__setattr__(forged, 'factories', (*owner.EXTENSION.factories, factory))
        patch.setattr(owner, 'EXTENSION', forged)
        with pytest.raises(ValueError, match='factory census'):
            index.selected_factories((key,))
    changed = replace(factory, manifest=replace(factory.manifest, runtime_id='changed-static-runtime'))
    # The factory itself normally rejects changed manifests; a foreign live
    # descriptor remains independently checked by the generated selected path.
    with monkeypatch.context() as patch:
        forged = copy(owner.EXTENSION)
        object.__setattr__(forged, 'factories', (changed,))
        patch.setattr(owner, 'EXTENSION', forged)
        with pytest.raises(ValueError, match='binding and manifest'):
            index.selected_factories((key,))


def test_custom_catalog_and_factory_composition_keep_their_eager_contract(monkeypatch):
    from empirical_lawhood.domains.battery.battery_recursive_construction.examples import battery_wave_a_draft
    draft = battery_wave_a_draft()
    factory = operations.operation_factories()[0]
    marker = object()
    assert operations.operation_catalog_for_draft(draft, catalog=lambda: marker) is marker
    monkeypatch.setattr(operations, 'operation_factories', lambda: (factory,))
    assert operations.selected_operation_factories((factory.registration.selection.selection_id,)) == (factory,)
    assert operations.selected_operation_factories(('absent@1.0.0',)) == ()
    assert operations.operation_catalog_for_draft(draft) == operations.operation_catalog()


def test_generator_refuses_conflicting_output_schema_types(monkeypatch):
    from scripts import generate_executable_binding_aggregate as generator
    from empirical_lawhood.execution.recursive_provider import RecursiveOperationProviderFactory
    descriptors = generator.load_descriptors(generator.discover_descriptors())
    owner = next(row for row in descriptors if 'battery_recursive_construction' in row.module_name)
    original = next(row for row in owner.factories if isinstance(row, RecursiveOperationProviderFactory))
    schema, kind = next(iter(original.output_codecs.items()))
    changed_kind = type('ConflictingRecordMeaning', (kind,), {})
    changed = replace(original, output_codecs={**original.output_codecs, schema: changed_kind})
    replacement = replace(owner, factories=tuple(changed if row is original else row for row in owner.factories))
    monkeypatch.setattr(generator, 'load_descriptors', lambda paths: tuple(replacement if row is owner else row for row in descriptors))
    with pytest.raises(ValueError, match='strict output codec'):
        generator.render_recursive_index(())
