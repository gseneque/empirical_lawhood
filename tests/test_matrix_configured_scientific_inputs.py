# SPDX-License-Identifier: MPL-2.0
"""Pure direct configured assembly inputs; no API, custody or native effects."""
from dataclasses import fields, replace
from pathlib import Path

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_assembly as owner
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_protocol import NativeTrainingScientificProtocol
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.serialization import CanonicalizationError, canonical_json_document_bytes
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection

EXAMPLES = Path(__file__).parents[1] / 'programmes/foundations/emergent-structure/workflows/matrix-response-experiment'


def inputs():
    return tuple(decode_canonical_bytes((EXAMPLES / name).read_bytes(), kind, maximum_bytes=None)
        for name, kind in (
            ('configured-scientific-assembly.request.example.json', owner.ConfiguredProtectedE3AssemblyRequest),
            ('configured-scientific-assembly.example.json', owner.ConfiguredProtectedE3AssemblySpecification),
            ('native-training-scientific-protocol.example.json', NativeTrainingScientificProtocol)))


def test_current_request_binds_direct_mathematics_without_old_study_scaffolding():
    request, specification, scientific = inputs()
    assert request.VERSION == specification.VERSION == '1.0.0'
    assert not {'blueprint', 'source_profile', 'entry_package', 'formal_methods'} & {row.name for row in fields(request)}
    selected = owner.bind_inputs(specification, {'request': request, 'scientific-protocol': scientific}).method_inputs
    assert selected.scientific_protocol == scientific
    assert decode_canonical_bytes(request.canonical_bytes(), type(request), maximum_bytes=None) == request
    preparation = owner.prepare(specification, method_inputs=selected, execution=ExecutionSelection(workers=4))
    assert not preparation.executable and preparation.census.native_effect_count == 0
    assert 'configured-assembly.scientific-protocol' not in {row.code for row in preparation.dependencies}
    assert scientific.scalar_artifact != request.normalization_file.identity


@pytest.mark.parametrize('role', ('blueprint', 'source-profile', 'original', 'secondary-original'))
def test_retired_scaffold_roles_refuse_before_assembly(role):
    request, specification, _ = inputs()
    with pytest.raises(ValueError, match='direct request'):
        owner.bind_inputs(specification, {'request': request, role: object()})


@pytest.mark.parametrize('version', ('1.0.0', '2.0.0', '3.0.0'))
def test_historical_request_schemas_have_no_current_decoder_bridge(version):
    request, _, _ = inputs()
    document = request.to_document()
    document['schema'] = 'empirical-lawhood/matrix-response-experiment/configured-protected-input-assembly-request'
    document['version'] = version
    with pytest.raises(CanonicalizationError):
        decode_canonical_bytes(canonical_json_document_bytes(document), type(request), maximum_bytes=None)


def test_scientific_pin_and_original_normalization_remain_exact_and_distinct():
    request, _, scientific = inputs()
    with pytest.raises(ValueError, match='separately bound scientific protocol'):
        owner.validate_scientific_protocol(replace(request, scientific_protocol=replace(request.scientific_protocol,
            object_fingerprint='f' * 64)), scientific)
    with pytest.raises(ValueError, match='original normalization source bytes'):
        owner.validate_scientific_protocol(replace(request, normalization_file=replace(request.normalization_file,
            identity=scientific.scalar_artifact)), scientific)


def test_request_only_preparation_retains_missing_scientific_operand():
    request, specification, _ = inputs()
    selected = owner.bind_inputs(specification, {'request': request}).method_inputs
    preparation = owner.prepare(specification, method_inputs=selected, execution=ExecutionSelection(workers=4))
    assert 'configured-assembly.scientific-protocol' in {row.code for row in preparation.dependencies}
    assert not preparation.executable and preparation.census.native_effect_count == 0
