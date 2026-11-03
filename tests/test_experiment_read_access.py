# SPDX-License-Identifier: MPL-2.0
"""Closed locator decoding only: literal pins establish no actual permission."""
from dataclasses import replace
import json
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import experiment_read_access as owner
from empirical_lawhood.api import generated_experiment_runtime_bindings as registry
from empirical_lawhood.api import selected_e3_access, selected_e4_access
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_records import SelectedE4WaveLocator
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding
from tests.test_selected_e3_current_access import literal_originals
from tests.test_selected_e4_current_access import _literal_locator


def _forbidden(*_args, **_kwargs):
    raise AssertionError('locator decoding attempted scientific or authority access')


def install_locator_codecs(monkeypatch, *, callbacks=None, duplicate=False):
    callbacks = callbacks or (selected_e3_access.select_current_e3_access, selected_e4_access.select_current_e4_access)
    rows = tuple(ExperimentRuntimeBinding('protocol.disclosed.access.' + str(index), None,
        derive_inputs=_forbidden, read_access_record_types=(kind,), select_read_access=callback)
        for index, (kind, callback) in enumerate(zip(
            (MatrixSelectedOriginalProduct, SelectedE4WaveLocator), callbacks, strict=True)))
    if duplicate:
        rows += (replace(rows[0], protocol_id='protocol.disclosed.access.same-owner'),)
    monkeypatch.setattr(registry, 'EXPERIMENT_RUNTIME_BINDINGS', rows)
    return rows


def locator_files(directory, *, family='e3'):
    directory.mkdir(parents=True, exist_ok=True)
    records = literal_originals() if family == 'e3' else (_literal_locator('wave.a'), _literal_locator('wave.b'))
    paths = tuple(directory / (str(index) + '.json') for index in range(len(records)))
    for path, record in zip(paths, records, strict=True):
        path.write_bytes(record.canonical_bytes())
    return records, paths


@pytest.mark.parametrize('family', ('e3', 'e4'))
def test_locator_decoding_reuses_existing_types_without_permission_or_scientific_bytes(
        tmp_path, monkeypatch, family):
    install_locator_codecs(monkeypatch, duplicate=True)
    monkeypatch.setattr(selected_e3_access, 'original_input_access', _forbidden)
    monkeypatch.setattr(selected_e4_access, 'require_current_e4_access', _forbidden)
    records, paths = locator_files(tmp_path, family=family)
    before = tuple(path.read_bytes() for path in paths)
    current = owner.load_experiment_read_access(tuple(reversed(paths)),
        protocol_id='protocol.disclosed.access.' + ('0' if family == 'e3' else '1'))
    if family == 'e3':
        assert type(current) is selected_e3_access.SelectedE3CurrentAccess
        assert current.effective_originals(records) == records
    else:
        assert type(current) is selected_e4_access.SelectedE4CurrentAccess
        current.require_originals(records)
        assert current.waves == records
    assert not hasattr(current, 'canonical_bytes') and not hasattr(current, 'identity')
    assert tuple(path.read_bytes() for path in paths) == before


def test_a_later_selection_decodes_new_reveal_pins_without_rewriting_originals(tmp_path, monkeypatch):
    install_locator_codecs(monkeypatch)
    originals, paths = locator_files(tmp_path)
    previous = owner.load_experiment_read_access(paths, protocol_id='protocol.disclosed.access.0')
    changed = replace(originals[0], reveal_authority=replace(originals[0].reveal_authority,
        object_id='reveal.disclosed.replacement'))
    paths[0].write_bytes(changed.canonical_bytes())
    current = owner.load_experiment_read_access(paths, protocol_id='protocol.disclosed.access.0')
    assert previous.originals == originals
    assert current.effective_originals(originals) == (changed, *originals[1:])


@pytest.mark.parametrize('damage', ('version', 'schema', 'extra-field'))
def test_unknown_revision_schema_or_fields_refuse_before_projection(tmp_path, monkeypatch, damage):
    calls = []
    install_locator_codecs(monkeypatch, callbacks=(lambda records: calls.append(records),
        selected_e4_access.select_current_e4_access))
    _, paths = locator_files(tmp_path)
    document = json.loads(paths[0].read_bytes())
    if damage == 'version':
        document['version'] = '99.0.0'
    elif damage == 'schema':
        document['schema'] = 'empirical-lawhood/planning/study-operation-authority'
    else:
        document['value']['permission'] = True
    paths[0].write_text(json.dumps(document))
    with pytest.raises(ValueError):
        owner.load_experiment_read_access(paths, protocol_id='protocol.disclosed.access.0')
    assert calls == []


def test_mixed_locator_families_cannot_select_an_owner(tmp_path, monkeypatch):
    calls = []
    install_locator_codecs(monkeypatch, callbacks=(lambda records: calls.append(records),
        lambda records: calls.append(records)))
    _, e3 = locator_files(tmp_path / 'e3')
    _, e4 = locator_files(tmp_path / 'e4', family='e4')
    with pytest.raises(ValueError):
        owner.load_experiment_read_access((*e3, *e4), protocol_id='protocol.disclosed.access.0')
    assert calls == []


@pytest.mark.parametrize('selected_protocol', ('protocol.disclosed.access.0', 'protocol.disclosed.prepared'))
def test_explicit_protocol_selects_one_of_two_real_same_codec_projection_owners(
        tmp_path, monkeypatch, selected_protocol):
    calls = []
    rows = install_locator_codecs(monkeypatch)

    def project(protocol):
        def selected(records):
            calls.append(protocol)
            return SimpleNamespace(protocol_id=protocol, records=records)
        return selected

    e3 = replace(rows[0], select_read_access=project(rows[0].protocol_id))
    prepared = replace(rows[0], protocol_id='protocol.disclosed.prepared',
        select_read_access=project('protocol.disclosed.prepared'))
    monkeypatch.setattr(registry, 'EXPERIMENT_RUNTIME_BINDINGS', (e3, rows[1], prepared))
    originals, paths = locator_files(tmp_path)
    current = owner.load_experiment_read_access(paths, protocol_id=selected_protocol)
    assert current.protocol_id == selected_protocol and current.records == originals
    assert calls == [selected_protocol]


@pytest.mark.parametrize('damage', ('missing-protocol', 'unsupported-protocol', 'duplicate-protocol'))
def test_protocol_is_required_and_unambiguous_before_any_locator_open(tmp_path, monkeypatch, damage):
    from empirical_lawhood.api import codecs
    rows = install_locator_codecs(monkeypatch)
    monkeypatch.setattr(codecs, 'load_registered_authoring', _forbidden)
    paths = (tmp_path / 'unopened.json',)
    if damage == 'missing-protocol':
        with pytest.raises(TypeError, match='protocol_id'):
            owner.load_experiment_read_access(paths)
    else:
        if damage == 'duplicate-protocol':
            monkeypatch.setattr(registry, 'EXPERIMENT_RUNTIME_BINDINGS', (*rows, rows[0]))
        with pytest.raises(ValueError, match='unambiguous|no current locator projection'):
            owner.load_experiment_read_access(paths, protocol_id=(rows[0].protocol_id
                if damage == 'duplicate-protocol' else 'protocol.disclosed.unsupported'))


@pytest.mark.parametrize('damage', ('duplicate', 'symlink', 'parent'))
def test_locator_transport_refuses_aliases_symlinks_and_parent_traversal(tmp_path, monkeypatch, damage):
    install_locator_codecs(monkeypatch)
    _, paths = locator_files(tmp_path)
    if damage == 'duplicate':
        selected = (*paths, paths[0])
    elif damage == 'symlink':
        alias = tmp_path / 'alias.json'
        alias.symlink_to(paths[0])
        selected = (alias, *paths[1:])
    else:
        selected = (tmp_path / 'unused' / '..' / paths[0].name, *paths[1:])
    with pytest.raises(ValueError, match='repeats|symbolic links and parent traversal'):
        owner.load_experiment_read_access(selected, protocol_id='protocol.disclosed.access.0')


@pytest.mark.parametrize('verdict', (None, True, 'canonical-record'))
def test_projection_cannot_return_a_permission_verdict_or_new_canonical_authority(tmp_path, monkeypatch, verdict):
    def project(records):
        return records[0] if verdict == 'canonical-record' else verdict
    install_locator_codecs(monkeypatch, callbacks=(project, selected_e4_access.select_current_e4_access))
    _, paths = locator_files(tmp_path)
    with pytest.raises(TypeError, match='operation-local selection, not a permission result'):
        owner.load_experiment_read_access(paths, protocol_id='protocol.disclosed.access.0')
