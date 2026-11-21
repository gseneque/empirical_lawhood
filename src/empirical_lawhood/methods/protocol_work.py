# SPDX-License-Identifier: MPL-2.0
"""Signed parameter work at a declared fixed-configuration protocol jump.

The caller supplies the actual potential and the configuration at the native
parameter-update boundary. Heat, driving-force work and integration error are
different quantities. Failed evaluations retain the completed work prefix.
"""
from dataclasses import dataclass
import math


@dataclass(slots=True)
class ProtocolWorkAccount:
    units: str
    convention: str
    signed_work: float = 0.
    absolute_jump_work: float = 0.
    completed_jumps: int = 0
    potential_evaluations_attempted: int = 0
    potential_evaluations_completed: int = 0

    def __post_init__(self):
        if not self.units or not self.convention:
            raise ValueError('Physical work requires explicit units and update convention')

    def record_jump(self, potential, configuration, previous_parameters, next_parameters):
        energies = []
        for parameters in (previous_parameters, next_parameters):
            self.potential_evaluations_attempted += 1
            energy = float(potential(configuration, parameters))
            if not math.isfinite(energy):
                raise FloatingPointError('Protocol work potential evaluation is nonfinite')
            self.potential_evaluations_completed += 1
            energies.append(energy)
        work = energies[1] - energies[0]
        total = math.fsum((self.signed_work, work))
        absolute = math.fsum((self.absolute_jump_work, abs(work)))
        if not math.isfinite(total) or not math.isfinite(absolute):
            raise FloatingPointError('Protocol work accumulation is nonfinite')
        self.signed_work, self.absolute_jump_work = total, absolute
        self.completed_jumps += 1
        return work

    def summary(self, *, complete=True):
        return {'signed_work': self.signed_work, 'absolute_jump_work': self.absolute_jump_work,
            'completed_parameter_jumps': self.completed_jumps,
            'potential_evaluations_attempted': self.potential_evaluations_attempted,
            'potential_evaluations_completed': self.potential_evaluations_completed,
            'units': self.units, 'convention': self.convention,
            'scope': 'PARAMETER_WORK_ONLY; THERMOSTAT_HEAT_FORCE_WORK_AND_DISCRETIZATION_ERROR_EXCLUDED',
            'complete': bool(complete), 'completed_prefix_retained': True}
