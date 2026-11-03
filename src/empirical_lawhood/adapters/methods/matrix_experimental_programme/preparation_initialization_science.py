# SPDX-License-Identifier: MPL-2.0
"""Deterministic declared tick-zero state, independently checked Q2 geometry.

The producer uses the original initializer. The independent check uses literal
Pauli entries and Kronecker indices, with no call to that initializer or RNG.
This constructs a numerical configuration, not a trajectory or an observation.
"""
from decimal import Decimal
from hashlib import sha256

import numpy as np

from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import (
    FOUR_FAMILY_PREPARATION_IDS, initial_parameter_state,
)
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from .preparation_records import MatrixPreparationInitialStateV2


def _literal_initial(coordinate):
    """Original Q2 rule, independently expanded in a fixed public tensor basis."""
    coordinate.__post_init__()
    alpha = coordinate.decreasing_start if coordinate.family_id == FOUR_FAMILY_PREPARATION_IDS[1] else Decimal(0)
    positions = np.zeros((2, 3, 4, 4), dtype="<c16")
    if coordinate.family_id == FOUR_FAMILY_PREPARATION_IDS[1]:
        pauli = np.asarray((((0, 0.5), (0.5, 0)), ((0, -0.5j), (0.5j, 0)), ((0.5, 0), (0, -0.5))), dtype="<c16")
        scale = 2.0 * (float(alpha) / 2) / 3.0
        for axis in range(3):
            for i in range(2):
                for j in range(2):
                    for spectator in range(2):
                        positions[0, axis, 2 * i + spectator, 2 * j + spectator] = scale * pauli[axis, i, j]
                        positions[1, axis, 2 * spectator + i, 2 * spectator + j] = scale * pauli[axis, i, j]
    return {"positions": positions, "momenta": np.zeros_like(positions)}, (alpha, alpha)


def validate_initial_state(initial, arrays):
    if type(initial) is not MatrixPreparationInitialStateV2:
        raise TypeError("declared initialization proof requires its explicit V2 operand")
    initial.__post_init__()
    expected, alpha = _literal_initial(initial.original.coordinate)
    if (set(arrays) != set(expected) or initial.alpha_tilde != alpha
            or any(value.dtype.str != "<c16" or value.shape != (2, 3, 4, 4) or not np.isfinite(value).all()
                or not np.array_equal(value, expected[name]) for name, value in arrays.items())):
        raise ValueError("declared initial state differs from the independent complete original Q2 tick-zero rule")


def initialize_source(source, producing_provenance, *, state_id, artifact_id):
    """No RNG, native contact, trajectory integration or historical receipt."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
    source.__post_init__()
    coordinate = source.coordinate
    primary = initial_parameter_state(coordinate)
    fine = initial_parameter_state(coordinate)
    if (primary.step_index != 0 or fine.step_index != 0 or not primary.finite or not fine.finite
            or primary.positions.tobytes() != fine.positions.tobytes() or primary.momenta.tobytes() != fine.momenta.tobytes()
            or (primary.alpha_tilde_x, primary.alpha_tilde_y) != (fine.alpha_tilde_x, fine.alpha_tilde_y)
            or (primary.alpha_tilde_x, primary.alpha_tilde_y) != tuple(coordinate.couplings(0))):
        raise ValueError("original primary/fine declarations do not share the exact original tick-zero phase space")
    arrays = {"positions": primary.positions, "momenta": primary.momenta}
    raw, members = encode_matrix_arrays(arrays)
    _, alpha = _literal_initial(coordinate)
    artifact = ArtifactIdentity(artifact_id, "declared-matrix-tick-zero-initialization", MATRIX_ARRAY_SCHEMA,
        sha256(raw).hexdigest(), "application/x-npz", len(raw))
    initial = MatrixPreparationInitialStateV2(state_id, ScheduledPublicSource.from_source(source), source.root,
        producing_provenance, InformationCutoff("cutoff." + state_id, coordinate.clock_id, CausalPhase.PRE_ACTION,
            coordinate.physical_time(0)), artifact, members, alpha)
    validate_initial_state(initial, arrays)
    return initial, raw
