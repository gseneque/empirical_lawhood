# SPDX-License-Identifier: MPL-2.0
"""Compact wrappers over unchanged parameter-history numerical equations."""

from hashlib import sha256

from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays, encode_matrix_arrays, matrix_array_members
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.references import ArtifactIdentity

from . import independent, science
from .records import MatrixParameterHistoryControl
from .compact_records import MatrixParameterCompactArrays, MatrixParameterCompactAssessment, identity


validate_arrays = science.validate_arrays


def array_product(bound, arrays, *, artifact_id, raw=None):
    science.validate_arrays(bound, arrays)
    if raw is None:
        raw, members = encode_matrix_arrays(arrays)
    else:
        # Retained physical bytes stay unchanged. Compute value digests without
        # constructing a second complete archive in working memory.
        members = matrix_array_members(arrays)
    source = bound.source
    saved = MatrixParameterCompactArrays('operand.' + source.root_id, identity(source), source.allocation,
        source.coordinate, source.root_id, ArtifactIdentity(artifact_id, 'compact-parameter-history-arrays',
            MATRIX_ARRAY_SCHEMA, sha256(raw).hexdigest(), 'application/x-npz', len(raw)), members,
        tuple(sorted((identity(source), source.coordinate), key=lambda p: p.object_id)))
    return raw, saved


def retained_product(bound, saved, raw):
    """Exact existing receipt bytes: no redundant new archive is created."""
    saved.validate_source(bound)
    arrays = decode_matrix_arrays(raw, saved)
    science.validate_arrays(bound, arrays)
    return arrays


def assess(bound, history, arrays):
    history.validate_source(bound)
    science.validate_arrays(bound, arrays)
    design = bound.numerical_design
    rows = independent.assess_arrays(bound.coordinate, arrays, trajectory_tolerance=design.trajectory_tolerance,
                                     bridge_tolerance=design.bridge_tolerance)
    controls = tuple(MatrixParameterHistoryControl(**row) for row in rows)
    return MatrixParameterCompactAssessment('assessment.' + bound.root_id, identity(bound.source), identity(history),
        identity(design), controls, all(c.disposition == 'SATISFIED' for c in controls))


def read_retained(bound, history, retained, raw):
    if (retained.source != identity(bound.source) or retained.history != identity(history)
            or retained.numerical_design != identity(bound.numerical_design)):
        raise ValueError('compact assessment substitutes exact original source/history/design')
    arrays = retained_product(bound, history.arrays, raw)
    n, design = bound.coordinate.total_ticks, bound.numerical_design
    if tuple((c.denominator_steps,c.denominator_real_coordinates,c.tolerance) for c in retained.controls) != (
            (n,192,design.trajectory_tolerance),(2*n,192,design.trajectory_tolerance),
            (n,192,design.bridge_tolerance),(n,96,design.trajectory_tolerance)):
        raise ValueError('compact assessment loses complete numerical-control denominators')
    measured = assess(bound, history, arrays)
    if measured != retained:
        raise ValueError('compact retained independent assessment differs')
    return retained
