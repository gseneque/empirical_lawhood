# SPDX-License-Identifier: MPL-2.0
"""Explicit projected charge/spin constraints for the selected periodic model.

Projected populations define computational diabats. They are not formal
fragment charges, spin-pure states, electronic couplings or physical rates.
"""

from dataclasses import dataclass
from decimal import Decimal
import math
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact


@dataclass(frozen=True, slots=True)
class SpinOrbitMeanFieldSettings(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/spin-orbit-mean-field-settings'
    settings_id: str
    memory_megabytes: int
    integral_tolerance: Decimal
    model: str = 'ALL_QM_BREIT_PAULI_SPIN_ORBIT_MEAN_FIELD'
    density: str = 'ORIGINAL_CONSTRAINED_STATE_SPIN_SUM'
    environment: str = 'QM_NUCLEI_AND_QM_ELECTRONS_WITHOUT_RELATIVISTIC_MM_FIELD'

    def __post_init__(self):
        validate_stable_id(self.settings_id)
        if type(self.memory_megabytes) is not int or self.memory_megabytes <= 0:
            raise ValueError('spin-orbit integrals require their explicit host allocation')
        validate_decimal(self.integral_tolerance, field_name='integral_tolerance')
        if not 0 < float(self.integral_tolerance) < 1:
            raise ValueError('spin-orbit integrals require a finite positive screening tolerance')
        if (self.model != 'ALL_QM_BREIT_PAULI_SPIN_ORBIT_MEAN_FIELD'
                or self.density != 'ORIGINAL_CONSTRAINED_STATE_SPIN_SUM'
                or self.environment != 'QM_NUCLEI_AND_QM_ELECTRONS_WITHOUT_RELATIVISTIC_MM_FIELD'):
            raise ValueError('spin-orbit selection changes the explicit density or relativistic model')


@dataclass(frozen=True, slots=True)
class ElectronicPopulationConstraint(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/electronic-population-constraint'
    constraint_id: str
    kind: str
    physical_atom_indices: tuple[int, ...]
    target_electrons: Decimal

    def __post_init__(self):
        validate_stable_id(self.constraint_id)
        if (self.kind not in ('ELECTRON_POPULATION', 'ALPHA_MINUS_BETA_POPULATION')
                or type(self.physical_atom_indices) is not tuple or not self.physical_atom_indices
                or any(type(i) is not int or i < 0 for i in self.physical_atom_indices)
                or tuple(sorted(set(self.physical_atom_indices))) != self.physical_atom_indices):
            raise ValueError('electronic constraints require one actual ordered physical atom group and population meaning')
        validate_decimal(self.target_electrons, field_name='target_electrons')
        if (not math.isfinite(float(self.target_electrons))
                or self.kind == 'ELECTRON_POPULATION' and self.target_electrons < 0):
            raise ValueError('projected electron populations require finite compatible targets')


@dataclass(frozen=True, slots=True)
class ConstrainedElectronicState(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/constrained-electronic-state'
    state_id: str
    representation: ObjectIdentity
    qm_atom_indices: tuple[int, ...]
    qm_formal_charge: int
    spin_multiplicity: int
    constraints: tuple[ElectronicPopulationConstraint, ...]
    population_tolerance_electrons: Decimal
    multiplier_root_tolerance: Decimal
    multiplier_micro_steps: int
    initial_multipliers_hartree: tuple[Decimal, ...]
    chemical_hypothesis: ObjectIdentity
    spin_orbit: SpinOrbitMeanFieldSettings | None = None
    projection: str = 'GPU4PYSCF_1.8.1_PROJECTED_LOWDIN_MINAO'
    state_interpretation: str = 'CONSTRAINED_COLLINEAR_UKS_DETERMINANT_NOT_SPIN_PURE'

    def __post_init__(self):
        validate_stable_id(self.state_id)
        exact(self.representation, ObjectIdentity)
        exact(self.chemical_hypothesis, ObjectIdentity)
        if self.spin_orbit is not None:
            exact(self.spin_orbit, SpinOrbitMeanFieldSettings)
        if (type(self.qm_atom_indices) is not tuple or not self.qm_atom_indices
                or any(type(i) is not int or i < 0 for i in self.qm_atom_indices)
                or tuple(sorted(set(self.qm_atom_indices))) != self.qm_atom_indices
                or type(self.qm_formal_charge) is not int
                or type(self.spin_multiplicity) is not int or self.spin_multiplicity <= 0
                or type(self.constraints) is not tuple or not 1 <= len(self.constraints) <= 32):
            raise ValueError('electronic state requires the complete fixed QM partition and selected spin')
        for row in self.constraints:
            exact(row, ElectronicPopulationConstraint)
            if not set(row.physical_atom_indices).issubset(self.qm_atom_indices):
                raise ValueError('a constrained physical group must lie inside the actual QM partition')
        ids = tuple(row.constraint_id for row in self.constraints)
        groups = tuple((row.kind, row.physical_atom_indices) for row in self.constraints)
        if ids != tuple(sorted(set(ids))) or len(set(groups)) != len(groups):
            raise ValueError('electronic state repeats or reorders a constraint')
        for name in ('population_tolerance_electrons', 'multiplier_root_tolerance'):
            value = getattr(self, name)
            validate_decimal(value, field_name=name, minimum=Decimal(0))
            if not 0 < float(value) < 1:
                raise ValueError('constraint convergence requires explicit finite positive tolerances below one')
        if (type(self.multiplier_micro_steps) is not int or self.multiplier_micro_steps <= 0
                or type(self.initial_multipliers_hartree) is not tuple
                or len(self.initial_multipliers_hartree) != len(self.constraints)):
            raise ValueError('constraint solver requires its numerical microiteration selection and every initial multiplier')
        for value in self.initial_multipliers_hartree:
            validate_decimal(value, field_name='initial_multiplier_hartree')
            if not math.isfinite(float(value)):
                raise ValueError('initial constraint multipliers must be finite')
        if (self.projection != 'GPU4PYSCF_1.8.1_PROJECTED_LOWDIN_MINAO'
                or self.state_interpretation != 'CONSTRAINED_COLLINEAR_UKS_DETERMINANT_NOT_SPIN_PURE'):
            raise ValueError('constrained state changes its selected projector or claims unsupported spin purity')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.state_id, self)

    @property
    def solver_order(self):
        # Upstream stores charge projectors before spin projectors. The original
        # canonical constraint order is preserved independently of this layout.
        return tuple(row for kind in ('ELECTRON_POPULATION', 'ALPHA_MINUS_BETA_POPULATION')
            for row in self.constraints if row.kind == kind)


def validate_electronic_state(state, *, path, representation):
    exact(state, ConstrainedElectronicState)
    if (state.representation != representation.identity or state.representation != path.representation
            or state.qm_atom_indices != path.qm_atom_indices
            or state.qm_formal_charge != path.qm_formal_charge
            or state.spin_multiplicity != path.spin_multiplicity):
        raise ValueError('constrained state substitutes its complete molecular partition, charge or spin')


def constraint_groups(state):
    """Map actual physical atoms to upstream QM indices, never to link caps."""
    exact(state, ConstrainedElectronicState)
    indices = {atom: i for i, atom in enumerate(state.qm_atom_indices)}
    result = []
    for kind in ('ELECTRON_POPULATION', 'ALPHA_MINUS_BETA_POPULATION'):
        rows = tuple(row for row in state.solver_order if row.kind == kind)
        result.append(([list(indices[i] for i in row.physical_atom_indices) for row in rows],
            [float(row.target_electrons) for row in rows]))
    return tuple(result)


@dataclass(frozen=True, slots=True)
class ElectronicStateCriteria(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/electronic-state-criteria'
    criteria_id: str
    matrix_tolerance: Decimal
    maximum_spin_square_excess: Decimal
    maximum_determinant_overlap: Decimal
    maximum_directional_defect_hartree: Decimal
    maximum_workspace_bytes: int

    def __post_init__(self):
        validate_stable_id(self.criteria_id)
        for name in ('matrix_tolerance', 'maximum_spin_square_excess',
                'maximum_determinant_overlap', 'maximum_directional_defect_hartree'):
            value = getattr(self, name)
            validate_decimal(value, field_name=name, minimum=Decimal(0))
            if not math.isfinite(float(value)):
                raise ValueError('electronic criteria require finite exact numerical limits')
        if not 0 < self.matrix_tolerance < 1 or not 0 < self.maximum_determinant_overlap < 1:
            raise ValueError('electronic matrix and overlap criteria must lie strictly between zero and one')
        if type(self.maximum_workspace_bytes) is not int or self.maximum_workspace_bytes <= 0:
            raise ValueError('electronic assessment requires its complete explicit workspace')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.criteria_id, self)
