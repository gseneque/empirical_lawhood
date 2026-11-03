# SPDX-License-Identifier: MPL-2.0
"""Public recipe editions over exposed example locators, without real custody."""
from dataclasses import fields, replace
from pathlib import Path

import pytest

from empirical_lawhood.adapters.methods import matrix_finite_dt_source_assembly as finite
from empirical_lawhood.adapters.methods import matrix_prepared_source_assembly as prepared
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_preparation import ConfiguredE3ContinuedPreparationSelection
from empirical_lawhood.api.experiment_preparation import load_experiment_inputs, load_experiment_specification
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding


@pytest.mark.parametrize('family', ('finite', 'prepared'))
def test_retained_e3_recipes_preserve_closed_original_editions_and_public_binding(tmp_path, family):
    root = Path(__file__).parents[1] / 'programmes/foundations/emergent-structure/workflows/matrix-response-experiment'
    source = decode_canonical_bytes((root / 'prepared-source-assembly-request.example.json').read_bytes(),
        prepared.MatrixPreparedSourceAssemblyRequest, maximum_bytes=None)
    if family == 'finite':
        owner = finite
        old_request, new_request = finite.MatrixFiniteDtSourceAssemblyRequest, finite.MatrixFiniteDtRetainedE3AssemblyRequest
        old_spec, new_spec = finite.MatrixFiniteDtSourceAssemblySpecification, finite.MatrixFiniteDtRetainedE3AssemblySpecification
    else:
        owner = prepared
        old_request, new_request = prepared.MatrixPreparedSourceAssemblyRequest, prepared.MatrixPreparedRetainedE3AssemblyRequest
        old_spec, new_spec = prepared.MatrixPreparedSourceAssemblySpecification, prepared.MatrixPreparedRetainedE3AssemblySpecification
    values = {field.name: getattr(source, field.name) for field in fields(old_request) if field.name != 'phase'}
    if family == 'finite':
        values['phase'] = 'CALIBRATION'
    original = old_request(**values)
    handle = original.original_preparation
    # These are untrusted copied example locators only, never authenticated
    # retained products. The new schema must still be selected explicitly.
    continued = replace(handle, record=replace(handle.record,
        object_schema=ConfiguredE3ContinuedPreparationSelection.SCHEMA,
        object_version=ConfiguredE3ContinuedPreparationSelection.VERSION),
        publication=replace(handle.publication, logical=replace(handle.publication.logical,
            payload_schema=ConfiguredE3ContinuedPreparationSelection.SCHEMA,
            generic_validation=replace(handle.publication.logical.generic_validation,
                payload_schema=ConfiguredE3ContinuedPreparationSelection.SCHEMA))))
    with pytest.raises((ValueError, TypeError)):
        replace(original, original_preparation=continued)
    with pytest.raises((ValueError, TypeError)):
        new_request(**values)
    request = new_request(**(values | {'original_preparation': continued}))
    specification = new_spec('specification.disclosed-retained-e3', request.identity)
    with pytest.raises((ValueError, TypeError)):
        old_spec(specification.specification_id, request.identity)
    with pytest.raises((ValueError, TypeError)):
        new_spec(specification.specification_id, original.identity)
    raw = request.canonical_bytes()
    (tmp_path / 'request.json').write_bytes(raw)
    (tmp_path / 'specification.json').write_bytes(specification.canonical_bytes())
    selector = ExperimentFileInputSelection('sources.disclosed-retained-e3', owner.CONTINUED_PROTOCOL_ID,
        (ExperimentInputBinding('request', request.identity, 'request.json', len(raw)),), ())
    (tmp_path / 'sources.json').write_bytes(selector.canonical_bytes())
    loaded = load_experiment_specification(tmp_path / 'specification.json')
    bound = load_experiment_inputs(loaded, tmp_path / 'sources.json').method_inputs
    assert loaded == specification
    assert (bound if family == 'finite' else bound.request) == request
    assert decode_canonical_bytes(raw, new_request, maximum_bytes=None) == request
