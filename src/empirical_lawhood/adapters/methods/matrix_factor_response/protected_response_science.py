# SPDX-License-Identifier: MPL-2.0
"""Current E3 physical predictions and independent received-array consumers.

Every operation opens one fresh retained dataset session. Scientific arithmetic
stays with the original numerical owners. Current source/config/freeze joins
establish consistency; original publication qualification and producing task
custody remain with the owning API.
"""

from dataclasses import replace
from hashlib import sha256

import numpy as np

from empirical_lawhood.adapters.methods.matrix_dataset_readers import retained_array_mappings
from empirical_lawhood.adapters.methods.matrix_scheduled_history import science as prefix_science
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ResolvedScheduledSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_forecast import array_product, forecast_response_arrays
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_science import assess_paired_response_arrays

from .protected_experiment_methods import identity, project_paired_response_cells
from .protected_prefix_records import ProtectedE3CausalPrefix, ProtectedE3PrefixHistory
from .protected_response_records import (
    ProtectedE3NativeResponse, ProtectedE3PhysicalForecast, ProtectedE3PhysicalForecastConfig, ProtectedE3ResponseConfig,
    _exact, _object, _selected_protocol, validate_physical_information_scope,
)
from .protected_source_records import NAMESPACE, ProtectedE3SourceConfig


def _public_inputs(config, causal, *, specification, protocol, numerical_profile, mathematical_protocol, projection):
    _exact(config, ProtectedE3PhysicalForecastConfig)
    _exact(causal, ProtectedE3CausalPrefix)
    _selected_protocol(specification, protocol, numerical_profile, projection, mathematical_protocol)
    public = protocol.public_source
    if (config.root_id != public.root.root_id or config.specification != specification.identity
            or config.protocol != _object(protocol) or config.numerical_profile != identity(numerical_profile)
            or causal.source != public.source or causal.root != public.root or causal.policy != _object(public.policy)
            or causal.cutoff_tick != public.policy.cutoff_tick):
        raise ValueError("protected E3 physical inputs substitute actual public source/policy/cutoff/profile")


def _causal_clocks(protocol, causal, arrays):
    if causal.frame_sha256 is not None and sha256(arrays["frame"].tobytes()).hexdigest() != causal.frame_sha256:
        raise ValueError("protected E3 physical inputs change the actual retained origin frame")
    for view, multiplier in (("primary", 1), ("fine", 2)):
        if (arrays[view + "_ticks"][-1] != multiplier * causal.cutoff_tick
                or not np.array_equal(arrays[view + "_alpha_tilde"][-1], np.asarray(
                    protocol.public_source.coordinate.couplings(multiplier * causal.cutoff_tick, refinement=multiplier), dtype="<f8"))):
            raise ValueError("protected E3 physical inputs change actual paired cutoff clocks or realized couplings")


def forecast_physical(config, causal, *, specification, protocol, numerical_profile, mathematical_protocol, projection,
        fetch, maximum_chunk_bytes, maximum_slice_bytes, artifact_id, forecast_id, outcome_access, visibility_ceiling, raw=None):
    """Produce the original predictions using genuinely seedless operands only."""
    public_context = dict(specification=specification, protocol=protocol, numerical_profile=numerical_profile,
        mathematical_protocol=mathematical_protocol, projection=projection)
    _public_inputs(config, causal, **public_context)
    validate_physical_information_scope(numerical_profile, outcome_access=outcome_access, visibility_ceiling=visibility_ceiling)
    with retained_array_mappings((causal.arrays, protocol.templates), fetch,
            maximum_chunk_bytes=maximum_chunk_bytes, maximum_slice_bytes=maximum_slice_bytes) as values:
        causal_arrays, templates = values
        _causal_clocks(protocol, causal, causal_arrays)
        arrays, disposition, dispositions = forecast_response_arrays(protocol, causal_arrays, templates, disposition=causal.disposition)
        raw, operand = array_product(protocol, arrays, role="FORECAST", artifact_id=artifact_id,
            producers=(protocol.public_source.source, identity(causal), _object(protocol), identity(numerical_profile)),
            access=outcome_access, visibility=visibility_ceiling,
            nonfinite=tuple(name for name, array in arrays.items() if not np.isfinite(array).all()), raw=raw)
    result = ProtectedE3PhysicalForecast(forecast_id, _object(config), protocol.public_source.source, identity(causal),
        _object(protocol), identity(numerical_profile), _object(protocol.mechanical_model), causal.frame_sha256,
        operand, disposition, dispositions)
    result.validate_public_inputs(config, causal=causal, **public_context)
    return raw, result


def _current_inputs(config, native_config, responses, operands):
    _exact(config, ProtectedE3ResponseConfig)
    _exact(native_config, ProtectedE3ResponseConfig)
    _exact(responses, ProtectedE3NativeResponse)
    _exact(operands["prefix_config"], ProtectedE3SourceConfig)
    _exact(operands["history"], ProtectedE3PrefixHistory)
    # The history's original current configuration/native/checkpoint relation
    # is checked once at this science boundary, before any payload is opened.
    bound = operands["history"].validate_source(operands["prefix_config"], operands["manifest"],
        specification=operands["specification"])
    if type(operands["source"]) is not ResolvedScheduledSource or bound != operands["source"]:
        raise ValueError("protected E3 response science substitutes the authentic bound prefix source")
    expected = replace(native_config, operation="response-score",
        config_id="config." + NAMESPACE + "." + native_config.source.root_id + ".response-score")
    if config != expected:
        raise ValueError("protected E3 response science changes its actual current score/acquisition configuration")
    responses.validate_source(native_config, **{key: value for key, value in operands.items() if key != "prefix_config"})


def _current_score(score, native_config, responses, *, source, causal, physical, error, protocol, panels):
    from .protected_response_score_validation import validate_current_score
    return validate_current_score(score, native_config, responses, source=source, protocol=protocol, panels=panels,
        causal_identity=identity(causal), error_identity=identity(error), physical_identity=_object(physical),
        response_identity=_object(responses))


def assess_responses(config, native_config, responses, *, prefix_config, source, specification, manifest, selection, protocol,
        numerical_profile, panels, history, causal, physical_config, physical, error, allocation, models, frozen,
        calibration, model_freeze, mathematical_protocol, projection, fetch, maximum_chunk_bytes, maximum_slice_bytes, score_id):
    """Cold reproof and full paired native assessment within one dataset lease."""
    operands = dict(prefix_config=prefix_config, source=source, specification=specification, manifest=manifest, selection=selection,
        protocol=protocol, numerical_profile=numerical_profile, panels=panels, history=history, causal=causal,
        physical_config=physical_config, physical=physical, error=error, allocation=allocation, models=models, frozen=frozen,
        calibration=calibration, model_freeze=model_freeze, mathematical_protocol=mathematical_protocol, projection=projection)
    _current_inputs(config, native_config, responses, operands)
    prefix_science.validate_prefix_operand(source, history.arrays)
    with retained_array_mappings((history.arrays, causal.arrays, protocol.templates, physical.arrays, responses.arrays), fetch,
            maximum_chunk_bytes=maximum_chunk_bytes, maximum_slice_bytes=maximum_slice_bytes) as values:
        prefix_arrays, causal_arrays, templates, frozen_arrays, response_arrays = values
        prefix_science.validate_prefix_arrays(source, prefix_arrays)
        _causal_clocks(protocol, causal, causal_arrays)
        _, disposition, dispositions = forecast_response_arrays(protocol, causal_arrays, templates,
            disposition=causal.disposition, retained=frozen_arrays)
        if (disposition, dispositions) != (physical.disposition, physical.dispositions):
            raise ValueError("protected E3 response science changes original cold physical availability or predictor reasons")
        score = assess_paired_response_arrays(source, causal, history, prefix_arrays, physical, frozen_arrays, protocol,
            panels, responses, response_arrays, error_forecast=identity(error), score_id=score_id)
        _current_score(score, native_config, responses, source=source, causal=causal, physical=physical, error=error, protocol=protocol, panels=panels)
        return score


def project_outcome(config, native_config, responses, score, *, prefix_config, source, specification, manifest, selection, protocol,
        numerical_profile, panels, history, causal, physical_config, physical, error, allocation, models, frozen,
        calibration, model_freeze, mathematical_protocol, projection, record_id):
    """Project both complete15 targets from the actual current independent score."""
    operands = dict(prefix_config=prefix_config, source=source, specification=specification, manifest=manifest, selection=selection,
        protocol=protocol, numerical_profile=numerical_profile, panels=panels, history=history, causal=causal,
        physical_config=physical_config, physical=physical, error=error, allocation=allocation, models=models, frozen=frozen,
        calibration=calibration, model_freeze=model_freeze, mathematical_protocol=mathematical_protocol, projection=projection)
    _current_inputs(config, native_config, responses, operands)
    _current_score(score, native_config, responses, source=source, causal=causal, physical=physical, error=error, protocol=protocol, panels=panels)
    return project_paired_response_cells(specification, source, protocol, panels, error, score, record_id=record_id)
