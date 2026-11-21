# SPDX-License-Identifier: MPL-2.0
"""Bind original phase space to explicit equilibrium sampling and bias records.

The existing trajectory selection supplies only authenticated phase transport,
physical masses and the fixed reference operator. Its NVE criteria must be
absent. The equilibrium settings alone select the new sampling algorithm and
schedule; no historical Metropolis window schedule is executed implicitly.
"""

from dataclasses import dataclass, fields, replace
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.contracts import UmbrellaWindow
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.electronic_observations import ElectronicObservationSet
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_bias import ReferenceBiasConvention, evaluate_reference_umbrella_bias
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium import ReferenceEquilibriumSettings
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium_assessment import ReferenceEquilibriumCriteria
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_selection import ReferenceTrajectorySelection, prepare_reference_trajectory, read_phase_space, validate_trajectory_prototype


@dataclass(frozen=True, slots=True)
class ReferenceEquilibriumSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/reference-equilibrium-selection'
    selection_id: str
    phase: ReferenceTrajectorySelection
    settings: ReferenceEquilibriumSettings
    criteria: ReferenceEquilibriumCriteria | None
    window: UmbrellaWindow | None
    convention: ReferenceBiasConvention | None
    scope: str = 'REFERENCE_EQUILIBRIUM_SAMPLING_WITHOUT_ENSEMBLE_OR_RATE_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        exact(self.phase, ReferenceTrajectorySelection)
        exact(self.settings, ReferenceEquilibriumSettings)
        if self.criteria is not None:
            exact(self.criteria, ReferenceEquilibriumCriteria)
        if (self.phase.criteria is not None or self.phase.settings != self.settings.dynamics
                or (self.window is None) != (self.convention is None)
                or (self.window is None) != (self.settings.bias_window is None)
                or self.scope != 'REFERENCE_EQUILIBRIUM_SAMPLING_WITHOUT_ENSEMBLE_OR_RATE_ADMISSION'):
            raise ValueError('equilibrium selection substitutes its sampling schedule, bias or scientific scope')
        if self.window is not None:
            exact(self.window, UmbrellaWindow)
            exact(self.convention, ReferenceBiasConvention)
            pin = ObjectIdentity.from_record(self.window.window_id, self.window)
            if (self.settings.bias_window != pin or self.convention.window != pin
                    or self.settings.bias_convention != self.convention.identity
                    or self.window.model_id != self.phase.representation.object_id):
                raise ValueError('equilibrium selection changes its exact original bias or represented material')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.selection_id, self)

    @property
    def arrays(self):
        return self.phase.arrays

    @property
    def representation(self):
        return self.phase.representation

    @property
    def phase_source(self):
        return self.phase.phase_source

    @property
    def phase_bytes(self):
        return self.phase.phase_bytes

    @property
    def physical_atom_count(self):
        return self.phase.physical_atom_count

    @property
    def mass_sha256(self):
        return self.phase.mass_sha256

    @property
    def density_guess_policy(self):
        return self.phase.density_guess_policy


@dataclass(frozen=True, slots=True, kw_only=True)
class ObservedElectronicEquilibriumSelection(ReferenceEquilibriumSelection):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/observed-electronic-equilibrium-selection'
    observations: ElectronicObservationSet

    def __post_init__(self):
        ReferenceEquilibriumSelection.__post_init__(self)
        exact(self.observations, ElectronicObservationSet)
        if self.phase.prototype not in {p.identity for p in self.observations.prototypes}:
            raise ValueError('observed equilibrium omits its actual sampled electronic state')


def equilibrium_selection_type(selection):
    if type(selection) not in (ReferenceEquilibriumSelection, ObservedElectronicEquilibriumSelection):
        raise TypeError('equilibrium requires its exact selected ordinary or electronic-observation record')
    return type(selection)


def prepare_electronic_observations(selection, observations):
    exact(selection, ReferenceEquilibriumSelection)
    exact(observations, ElectronicObservationSet)
    candidate = ObservedElectronicEquilibriumSelection(
        **{field.name:getattr(selection, field.name) for field in fields(selection)}, observations=observations)
    return replace(candidate, selection_id='selection.electronic-equilibrium.'+candidate.fingerprint())


def validate_equilibrium_prototype(selection, prototype):
    equilibrium_selection_type(selection)
    validate_trajectory_prototype(selection.phase, prototype)


def read_equilibrium_phase_space(selection, representation, raw):
    equilibrium_selection_type(selection)
    values = read_phase_space(selection.phase, representation, raw)
    if selection.settings.temperature_kelvin != representation.temperature_k:
        raise ValueError('equilibrium sampling substitutes the represented physical temperature')
    return values


def selected_bias(selection, prototype, representation, coordinates):
    """Evaluate the selected pure bias using authenticated material and atom order."""
    validate_equilibrium_prototype(selection, prototype)
    if representation.identity != selection.representation:
        raise ValueError('equilibrium bias substitutes its represented atom table')
    if selection.window is None:
        return None
    cell = tuple(tuple(float(prototype.cell.lengths_angstrom[i]) if i == j else 0.
        for j in range(3)) for i in range(3))
    return evaluate_reference_umbrella_bias(window=selection.window, convention=selection.convention,
        physical_model_id=representation.representation_id,
        physical_atom_ids=tuple(atom.atom_id for atom in representation.atoms),
        coordinates_angstrom=coordinates, cell_vectors_angstrom=cell)


def prepare_reference_equilibrium(*, prototype, representation, phase_source, initial_angstrom,
        initial_velocity_nm_per_ps, settings, criteria, density_guess_policy, window, convention):
    """Freeze supplied initial arrays, explicit bath and optional original bias."""
    import numpy as np
    exact(settings, ReferenceEquilibriumSettings)
    if any(np.iscomplexobj(value) for value in (initial_angstrom, initial_velocity_nm_per_ps)):
        raise ValueError('equilibrium preparation requires real original phase space')
    phase, raw = prepare_reference_trajectory(prototype=prototype, representation=representation,
        phase_source=phase_source, initial_angstrom=initial_angstrom,
        initial_velocity_nm_per_ps=initial_velocity_nm_per_ps, settings=settings.dynamics,
        criteria=None, density_guess_policy=density_guess_policy)
    digest = sha256((phase.fingerprint()+settings.fingerprint()
        +(criteria.fingerprint() if criteria is not None else 'NONE')
        +(window.fingerprint() if window is not None else 'NONE')
        +(convention.fingerprint() if convention is not None else 'NONE')).encode('ascii')).hexdigest()
    selection = ReferenceEquilibriumSelection('selection.reference-equilibrium.'+digest,
        phase, settings, criteria, window, convention)
    xyz, _, _ = read_equilibrium_phase_space(selection, representation, raw)
    selected_bias(selection, prototype, representation, xyz)
    return selection, raw
