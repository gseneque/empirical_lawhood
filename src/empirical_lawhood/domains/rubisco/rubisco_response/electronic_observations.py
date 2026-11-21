# SPDX-License-Identifier: MPL-2.0
"""Prospective same-geometry constrained-state observations during sampling."""

from dataclasses import dataclass, fields
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import PeriodicProbeSelection, accelerated_engine
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import ConstrainedPeriodicForceSettings


@dataclass(frozen=True, slots=True)
class ElectronicObservationSet(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/electronic-observation-set'
    observation_id: str
    prototypes: tuple[PeriodicProbeSelection, ...]
    scope: str = 'ALL_SELECTED_STATES_AT_EVERY_ORIGINAL_EQUILIBRIUM_SAMPLE'

    def __post_init__(self):
        validate_stable_id(self.observation_id)
        if type(self.prototypes) is not tuple or not 2 <= len(self.prototypes) <= 8:
            raise ValueError('electronic observations require their complete finite state roster')
        ids = []
        for prototype in self.prototypes:
            exact(prototype, PeriodicProbeSelection)
            exact(prototype.electronic, ConstrainedPeriodicForceSettings)
            if not accelerated_engine(prototype.engine):
                raise ValueError('constrained observations require their selected GPU implementation')
            ids.append(prototype.electronic.state.state_id)
        if ids != sorted(set(ids)):
            raise ValueError('electronic observations repeat or reorder a selected state')
        baseline = self.prototypes[0]
        for candidate in self.prototypes[1:]:
            for name in ('representation', 'coordinates', 'physical_atom_count', 'cell', 'molecular', 'engine'):
                if getattr(candidate, name) != getattr(baseline, name):
                    raise ValueError('electronic observations change the common geometry, embedding, MM model or engine')
            for field in fields(baseline.path):
                if field.name not in ('selection_id', 'spin_multiplicity', 'sources') and (
                        getattr(candidate.path, field.name) != getattr(baseline.path, field.name)):
                    raise ValueError('electronic observations change the physical partition, total charge or selected chemistry')
            for field in fields(baseline.electronic):
                if field.name not in ('settings_id', 'state') and (
                        getattr(candidate.electronic, field.name) != getattr(baseline.electronic, field.name)):
                    raise ValueError('electronic observations change numerical settings between diabatic states')
            if candidate.electronic.state.spin_orbit != baseline.electronic.state.spin_orbit:
                raise ValueError('electronic observations require one common explicit spin-orbit model')
        if self.scope != 'ALL_SELECTED_STATES_AT_EVERY_ORIGINAL_EQUILIBRIUM_SAMPLE':
            raise ValueError('electronic observations cannot silently select a favorable sample subset')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.observation_id, self)
