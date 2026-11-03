# SPDX-License-Identifier: MPL-2.0
"""Versioned deterministic OU representability admission before effects.

This preserves the historical native arithmetic at supported points. It does
not coerce a positive bath/friction into a noiseless or degenerate bridge and
does not assess timestep adequacy or scientific qualification.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

import numpy as np

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord

METHOD = 'Q2_BINARY64_ORIGINAL_OU_AND_WEIGHTED_BRIDGE_REPRESENTABILITY_V1'


@dataclass(frozen=True, slots=True)
class MatrixParameterOUAdmission(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/six-matrix-response/parameter-ou-admission'
    coordinate: ObjectIdentity
    primary_timestep: Decimal
    fine_timestep: Decimal
    friction: Decimal
    bath_temperature: Decimal
    coefficient_hex: tuple[tuple[str, str], ...]
    method: str = METHOD
    scope: str = 'DETERMINISTIC_REPRESENTABILITY_NO_NUMERICAL_ADEQUACY_OR_QUALIFICATION'

    def __post_init__(self):
        if self.method != METHOD or self.scope != 'DETERMINISTIC_REPRESENTABILITY_NO_NUMERICAL_ADEQUACY_OR_QUALIFICATION':
            raise ValueError('OU admission changes its numerical method or invents qualification')


def validate_parameter_ou_domain(coordinate):
    """No RNG, native state, I/O, BEGIN or contact enters this validator."""
    primary, fine = coordinate.primary_view, coordinate.fine_view
    dt, fine_dt = float(primary.timestep), float(fine.timestep)
    gamma, temperature = float(primary.friction_gamma), float(primary.bath_temperature)
    if (not np.isfinite((dt, fine_dt, gamma, temperature)).all() or min(dt, fine_dt, gamma, temperature) <= 0
            or fine_dt * 2 != dt or primary.friction_gamma != fine.friction_gamma
            or primary.bath_temperature != fine.bath_temperature):
        raise ValueError('unsupported numerical OU domain v1: physical operands are not representable')
    product = gamma * dt
    if not np.isfinite(product) or product <= 0:
        raise ValueError('unsupported numerical OU domain v1: damping product is not representable')
    half = float(np.exp(-product / 2))
    primary_decay = float(np.exp(-product))
    fine_decay = float(np.exp(-gamma * fine_dt))
    primary_variance = temperature * (1 - primary_decay**2)
    fine_variance = temperature * (1 - fine_decay**2)
    if (not 0 < half < 1 or not 0 <= primary_decay < 1 or fine_decay != half
            or not np.isfinite((primary_variance, fine_variance)).all()
            or min(primary_variance, fine_variance) <= 0):
        raise ValueError('unsupported numerical OU domain v1: rounded decay/bath/bridge degeneracy')
    coefficients = {'primary-decay': primary_decay, 'fine-decay': fine_decay, 'bridge-half-decay': half,
        'primary-noise-scale': float(np.sqrt(primary_variance)), 'fine-noise-scale': float(np.sqrt(fine_variance)),
        'bridge-denominator': float(np.sqrt(1 + half**2))}
    if not np.isfinite(tuple(coefficients.values())).all() or min(coefficients.values()) < 0:
        raise ValueError('unsupported numerical OU domain v1: coefficient overflow')
    return MatrixParameterOUAdmission(ObjectIdentity.from_record(coordinate.coordinate_id, coordinate),
        primary.timestep, fine.timestep, primary.friction_gamma, primary.bath_temperature,
        tuple((name, value.hex()) for name, value in sorted(coefficients.items())))
