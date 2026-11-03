"""Parameter-history products and authenticated retained numerical consumers."""

from hashlib import sha256

import numpy as np

from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import initial_parameter_state
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays, encode_matrix_arrays
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.references import ArtifactIdentity

from . import independent
from .records import (
    MatrixParameterHistoryArrays, MatrixParameterHistoryAssessment, MatrixParameterHistoryControl,
    coordinate_identity, expected_members, identity,
)


def validate_arrays(source, arrays):
    """Every state/noise/coupling/clock, including all fine half steps."""
    coordinate = source.coordinate
    expected = expected_members(coordinate)
    if set(arrays) != set(expected):
        raise ValueError('parameter history omits its full state/noise/clock member census')
    for name, (dtype,shape) in expected.items():
        value = arrays[name]
        if value.dtype.str != dtype or value.shape != shape or not np.isfinite(value).all():
            raise ValueError('parameter history changes exact complete dtype/shape/finite population')
        if dtype == '<c16' and np.linalg.norm(value-value.conj().swapaxes(-1,-2)) > 1e-10*max(1,np.linalg.norm(value)):
            raise ValueError('parameter native phase space or innovations are non-Hermitian')
    initial = initial_parameter_state(coordinate)
    for view, multiplier in (('primary',1),('fine',2)):
        count = coordinate.total_ticks*multiplier+1
        if not np.array_equal(arrays[view+'_ticks'],np.arange(count,dtype='<i8')):
            raise ValueError('parameter history substitutes the physical native clock')
        coupling = np.asarray([coordinate.couplings(t,refinement=multiplier) for t in range(count)],dtype='<f8')
        if not np.array_equal(arrays[view+'_alpha_tilde'],coupling):
            raise ValueError('parameter history substitutes a native coupling schedule')
        if (not np.array_equal(arrays[view+'_positions'][0],initial.positions)
                or not np.array_equal(arrays[view+'_momenta'][0],initial.momenta)):
            raise ValueError('parameter history substitutes the declared family initial state')


def array_product(source, arrays, *, artifact_id, raw=None):
    validate_arrays(source,arrays)
    encoded,members = encode_matrix_arrays(arrays)
    if raw is None:
        raw = encoded
    artifact = ArtifactIdentity(artifact_id,'parameter-history-arrays',MATRIX_ARRAY_SCHEMA,
        sha256(raw).hexdigest(),'application/x-npz',len(raw))
    operand = MatrixParameterHistoryArrays('operand.'+source.root_id,identity(source),identity(source.allocation),
        coordinate_identity(source.coordinate),source.root_id,artifact,members,
        tuple(sorted((identity(source),coordinate_identity(source.coordinate)),key=lambda x:x.object_id)))
    # If retaining an already receipted child, authenticate its exact raw bytes
    # against the newly derived value/member manifest; never rewrite that child.
    decode_matrix_arrays(raw,operand)
    return raw,operand


def consume_arrays(source, operand, raw):
    operand.validate_source(source)
    arrays = decode_matrix_arrays(raw,operand)
    validate_arrays(source,arrays)
    return arrays


def assess(source, history, arrays):
    history.validate_source(source)
    validate_arrays(source,arrays)
    design = source.numerical_design
    rows = independent.assess_arrays(source.coordinate,arrays,
        trajectory_tolerance=design.trajectory_tolerance,bridge_tolerance=design.bridge_tolerance)
    controls = tuple(MatrixParameterHistoryControl(**row) for row in rows)
    result = MatrixParameterHistoryAssessment('assessment.'+source.root_id,identity(source),identity(history),
        identity(design),controls,all(c.disposition == 'SATISFIED' for c in controls))
    validate_assessment(source,history,result)
    return result


def validate_assessment(source, history, assessment):
    """Cold structural/census guard; does not recreate native history."""
    history.validate_source(source)
    n = source.coordinate.total_ticks
    design = source.numerical_design
    if (assessment.source != identity(source) or assessment.history != identity(history)
            or assessment.numerical_design != identity(design)
            or tuple((c.denominator_steps,c.denominator_real_coordinates,c.tolerance) for c in assessment.controls) !=
               ((n,192,design.trajectory_tolerance),(2*n,192,design.trajectory_tolerance),
                (n,192,design.bridge_tolerance),(n,96,design.trajectory_tolerance))):
        raise ValueError('parameter assessment thins source/control/real-coordinate denominator')


def read_retained(source, history, assessment, raw):
    """Independent reproof over exact retained bytes, with producer unavailable."""
    validate_assessment(source,history,assessment)
    arrays = consume_arrays(source,history.arrays,raw)
    if assess(source,history,arrays) != assessment:
        raise ValueError('parameter retained independent measurements changed')
    return assessment
