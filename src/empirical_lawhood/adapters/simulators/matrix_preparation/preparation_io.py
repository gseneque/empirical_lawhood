"""Verified matrix array codec boundary for reusable preparation calculations."""
from empirical_lawhood.adapters.matrix_storage.matrix_array_io import decode_matrix_arrays, encode_matrix_arrays, matrix_array_members
from empirical_lawhood.domains.matrix.matrix_experimental_programme import preparation_science as calculations
import numpy as np

def initial_state(initial, raw):
    return calculations.initial_state_from_arrays(initial, decode_matrix_arrays(raw, initial))

def propagate_preparation(source, initial_raw, *, coarse_innovations, bridge_innovations, on_step=None):
    return calculations.propagate_preparation_state(source, initial_state(source.initial, initial_raw),
        coarse_innovations=coarse_innovations, bridge_innovations=bridge_innovations, on_step=on_step)

def acquire_preparation(source, initial_raw, *, on_step=None, prepared_initial=None):
    initial = initial_state(source.initial, initial_raw) if prepared_initial is None else prepared_initial
    return calculations.acquire_preparation_state(source, initial, on_step=on_step)

def preparation_array_product(source, initial_raw, arrays, *, artifact_id, raw=None):
    return _preparation_array_product(source, initial_state(source.initial, initial_raw), arrays,
        artifact_id=artifact_id, raw=raw)

def _preparation_array_product(source, initial, arrays, *, artifact_id, raw=None):
    calculations.validate_preparation_arrays(source, arrays, initial=initial)
    if raw is None:
        raw, members = encode_matrix_arrays(arrays)
    else:
        members = matrix_array_members(arrays)
    operand = calculations._preparation_array_operand(source, raw, members, artifact_id=artifact_id)
    decoded = decode_matrix_arrays(raw, operand)
    if any(not np.array_equal(decoded[name], arrays[name]) for name in arrays):
        raise ValueError("retained preparation bytes change their complete original numerical values")
    return raw, operand

def consume_preparation_arrays(source, initial_raw, operand, raw):
    operand.validate_source(source)
    arrays = decode_matrix_arrays(raw, operand)
    calculations.validate_preparation_arrays(source, arrays, initial=initial_state(source.initial, initial_raw))
    return arrays

def assess_preparation_arrays(source, initial_raw, operand, arrays, *, assessment_id):
    return calculations.assess_preparation_state(source, initial_state(source.initial, initial_raw),
        operand, arrays, assessment_id=assessment_id)


def initialize_source(source, producing_provenance, *, state_id, artifact_id):
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.preparation_initialization_science import declared_initial_source_arrays, initial_source_record
    arrays = declared_initial_source_arrays(source)
    raw, members = encode_matrix_arrays(arrays)
    initial = initial_source_record(source, producing_provenance, arrays, raw, members,
        state_id=state_id, artifact_id=artifact_id)
    return initial, raw
