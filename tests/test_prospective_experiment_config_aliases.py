# SPDX-License-Identifier: MPL-2.0
"""Selected operation-byte aliases keep the public closed binding census.

These are disclosed canonical records and immutable byte bindings, with no issue,
worker execution, source qualification or scientific authority.
"""

from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace

from empirical_lawhood.api.prospective_experiment import _input_bindings
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.planning.recursive_authoring import RecursiveOperationSpec
from empirical_lawhood.planning.study_authoring import SourceMaterializationRole
from empirical_lawhood.runtime.experiment_preparation import PreparedExperimentFile
from empirical_lawhood.runtime.input_payloads import InputBytes
from empirical_lawhood.runtime.source_resolution import SourceMaterializationConfig, SourceReadMode
from tests.runtime_platform.test_recursive_compiler import Config, SourceConfig, fixture


def _file(directory, name, raw, schema):
    path = directory / (name + '.json')
    path.write_bytes(raw)
    identity = ArtifactIdentity(name, 'disclosed-software-input', schema, sha256(raw).hexdigest(),
        'application/json', len(raw))
    return PreparedExperimentFile(identity, '1.0.0', path, len(raw))


def test_exact_selected_operation_aliases_need_no_duplicate_path_but_keep_source_configs(tmp_path):
    draft, _, _ = fixture()
    operation = draft.operations[0]
    selected = decode_canonical_bytes(operation.config_payload.encode(), SourceConfig, maximum_bytes=None)
    unused = Config('config.unselected', 17)
    unselected_operation = RecursiveOperationSpec.from_config(node_id='unselected', selection=operation.selection,
        config_id=unused.config_id, config=unused, obligation_ids=('obligation.unselected',), resource_budget=operation.resource_budget)
    draft = replace(draft, operations=tuple(sorted((*draft.operations, unselected_operation), key=lambda row: row.node_id)))
    ordinary = Config('source.ordinary', 23)
    sources = {'alias-record': selected, 'ordinary': ordinary, 'unused-config': unused}
    selected_file = _file(tmp_path, 'alias-file', selected.canonical_bytes(), selected.SCHEMA)
    ordinary_file = _file(tmp_path, 'ordinary-file', ordinary.canonical_bytes(), ordinary.SCHEMA)
    files = {'alias-file': selected_file, 'ordinary-file': ordinary_file}
    external = {key: SimpleNamespace(logical_artifact_id='logical.' + key) for key in (*sources, *files)}
    source_config = SourceMaterializationConfig('source-config.disclosed', 'source.disclosed',
        SourceMaterializationRole.OBSERVATION_STREAM, ordinary.fingerprint(), len(ordinary.canonical_bytes()),
        len(ordinary.canonical_bytes()), ordinary.SCHEMA, 'application/json', SourceReadMode.ORDINARY_BOUNDED,
        OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
    original_sources = {key: record.canonical_bytes() for key, record in sources.items()}
    before = set(tmp_path.iterdir())
    with _input_bindings(external=external, sources=sources, files=files,
            configs={source_config.fingerprint(): source_config}, custody_root=tmp_path, draft=draft) as bindings:
        supplied = dict(bindings)
        assert len(supplied) == len(bindings) == 4
        assert set(supplied) == {'logical.ordinary', 'logical.unused-config',
            'logical.ordinary-file', source_config.fingerprint()}
        assert type(supplied[source_config.fingerprint()]) is InputBytes
        assert supplied[source_config.fingerprint()].payload == source_config.canonical_bytes()
        assert supplied['logical.unused-config'].payload == unused.canonical_bytes()
        assert supplied['logical.ordinary'].payload == ordinary.canonical_bytes()
        assert supplied['logical.ordinary-file'] == ordinary_file.path
        assert set(tmp_path.iterdir()) == before
    assert set(tmp_path.iterdir()) == before
    assert selected_file.path.read_bytes() == selected.canonical_bytes()
    assert {key: record.canonical_bytes() for key, record in sources.items()} == original_sources
    assert set(external) == {'alias-record', 'alias-file', 'ordinary', 'ordinary-file', 'unused-config'}


def test_same_config_id_with_changed_bytes_remains_an_explicit_external_binding(tmp_path):
    draft, _, _ = fixture()
    selected = decode_canonical_bytes(draft.operations[0].config_payload.encode(), SourceConfig, maximum_bytes=None)
    changed = replace(selected, scalar=selected.scalar + 1)
    assert changed.config_id == selected.config_id and changed.fingerprint() != selected.fingerprint()
    external = {'changed': SimpleNamespace(logical_artifact_id='logical.changed-config')}
    with _input_bindings(external=external, sources={'changed': changed}, files={}, configs={},
            custody_root=tmp_path, draft=draft) as bindings:
        key, payload = bindings[0]
        assert key == 'logical.changed-config' and payload.payload == changed.canonical_bytes()
        assert len(bindings) == 1
