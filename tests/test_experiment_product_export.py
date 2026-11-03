# SPDX-License-Identifier: MPL-2.0
"""Postprocessing composition controls; no source freshness or native authority."""
from dataclasses import replace
import json
from pathlib import Path

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.extension_bundle import EXPERIMENT_PROTOCOL_DECLARATIONS
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_acquisition import PROTOCOL_ID
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_exports import NativeTrainingBankExportSelection
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_records import NativeTrainingAcquisitionSpecification
from empirical_lawhood.api.experiment_runtime_bindings import experiment_runtime_binding, validate_experiment_runtime_binding
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.serialization import canonical_json_document_bytes


def protocol():
    return next(row for row in EXPERIMENT_PROTOCOL_DECLARATIONS if row.protocol_id == PROTOCOL_ID)


def test_typed_export_selection_preserves_intent_and_refuses_path_traversal():
    selected = NativeTrainingBankExportSelection('export.disclosed-training',
        'banks.disclosed-training', 'exports/disclosed-training')
    assert decode_canonical_bytes(selected.canonical_bytes(), type(selected), maximum_bytes=None) == selected
    for path in ('../escape', '/absolute', '.', 'exports/../escape'):
        with pytest.raises(ValueError):
            replace(selected, output_relative_path=path)
    assert set(json.loads(selected.canonical_bytes())['value']) == {
        'record_id', 'bank_record_id', 'output_relative_path'}


@pytest.mark.parametrize('defect', ('old-edition', 'caller-locator'))
def test_public_export_refuses_retired_or_caller_authored_source_metadata(defect):
    selected = NativeTrainingBankExportSelection('export.disclosed-training',
        'banks.disclosed-training', 'exports/disclosed-training')
    document = json.loads(selected.canonical_bytes())
    if defect == 'old-edition':
        document['version'] = '1.0.0'
    else:
        document['value']['locator'] = {'run_id': 'run.unexecuted-substitution'}
    with pytest.raises((ValueError, TypeError)):
        decode_canonical_bytes(canonical_json_document_bytes(document), type(selected), maximum_bytes=None)


def test_installed_export_only_composition_keeps_common_development_lifecycle():
    selected = protocol()
    binding = experiment_runtime_binding(selected)
    assert callable(binding.export_products)
    assert binding.bind_handoff is None and binding.bind_development_runtime is None
    assert selected.requires_prospective_runtime_binding is False
    assert selected.requires_development_runtime_binding is False
    assert validate_experiment_runtime_binding(selected, binding) is binding
    for keyword in ('bind_handoff', 'bind_development_runtime', 'prepare_authoring', 'programme_service_factory'):
        with pytest.raises((ValueError, TypeError)):
            validate_experiment_runtime_binding(selected, replace(binding, **{keyword: lambda **kwargs: None}))
    for keyword in ('requires_prospective_runtime_binding', 'requires_development_runtime_binding'):
        with pytest.raises(ValueError, match='declared lifecycle'):
            validate_experiment_runtime_binding(replace(selected, **{keyword: True}), binding)


def test_installed_binding_index_validates_each_exact_tuple_once_and_keeps_context_checks(monkeypatch):
    from empirical_lawhood.api import experiment_runtime_bindings as owner
    from empirical_lawhood.api import generated_experiment_runtime_bindings as installed
    from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding

    selected = protocol()
    rows = installed.EXPERIMENT_RUNTIME_BINDINGS
    calls = []
    original = ExperimentRuntimeBinding.__post_init__

    def observed(self):
        calls.append(self.protocol_id)
        original(self)

    monkeypatch.setattr(ExperimentRuntimeBinding, '__post_init__', observed)
    monkeypatch.setattr(owner, '_installed_bindings_index', None)
    for _ in range(4):
        assert experiment_runtime_binding(selected).protocol_id == selected.protocol_id
    assert len(calls) == len(rows)
    with pytest.raises(ValueError, match='declared lifecycle'):
        experiment_runtime_binding(replace(selected, requires_prospective_runtime_binding=True))
    assert len(calls) == len(rows)
    monkeypatch.setattr(installed, 'EXPERIMENT_RUNTIME_BINDINGS', tuple(list(rows)))
    experiment_runtime_binding(selected)
    assert len(calls) == 2 * len(rows)
    monkeypatch.setattr(installed, 'EXPERIMENT_RUNTIME_BINDINGS', (*rows, rows[0]))
    with pytest.raises(ValueError, match='inconsistent owning declarations'):
        experiment_runtime_binding(selected)


def test_public_export_selection_is_registered_configuration_without_task_lowering():
    selected = protocol()
    role, = (row for row in selected.configuration_inputs if row.consumer_id == 'matrix-native-training-bank-export')
    assert role.record_type is NativeTrainingBankExportSelection
    assert NativeTrainingAcquisitionSpecification is selected.specification_type
    assert NativeTrainingBankExportSelection in selected.input_record_types
    example = Path(__file__).parents[1] / 'programmes/foundations/emergent-structure/workflows/matrix-response-experiment/native-training-export.example.json'
    selection = decode_canonical_bytes(example.read_bytes(), NativeTrainingBankExportSelection,
        maximum_bytes=role.maximum_config_bytes)
    assert selection == NativeTrainingBankExportSelection('export.disclosed-training',
        'banks.disclosed-training', 'exports/disclosed-training')


def test_export_shape_cannot_be_used_as_an_acquisition_request():
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_acquisition import bind_inputs
    selected=NativeTrainingBankExportSelection('export.disclosed-training','banks.disclosed-training','exports/disclosed-training')
    with pytest.raises(TypeError,match='exact acquisition request'):
        bind_inputs(object(),{'request':selected})
