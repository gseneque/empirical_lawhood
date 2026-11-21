# SPDX-License-Identifier: MPL-2.0
"""Rubisco periodic cell and force conventions, independent of native solvers.

Parsing consumes supplied original bytes only; it neither opens native files nor
constructs an engine. Schema IDs and canonical records retain their original
versions and scientific meanings after the ownership extraction.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from hashlib import sha256
from io import StringIO
import math
from typing import ClassVar

from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.domains.rubisco.rubisco_response.electronic_states import ConstrainedElectronicState
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_quality import MolecularGeometryPolicy


# OpenMM 8.3.1 reference/SimTKOpenMMRealType.h, CODATA 2018 definitions.
# https://github.com/openmm/openmm/blob/8.3.1/platforms/reference/include/SimTKOpenMMRealType.h
COULOMB_KJ_NM_PER_MOL_E2 = 1/(4*math.pi*(1e-6*8.8541878128e-12/(1.602176634e-19**2*6.02214076e23)))
PYSCF_BOHR_ANGSTROM = .52917721092
REFERENCE_HARTREE_KJ_MOL = COULOMB_KJ_NM_PER_MOL_E2 / (PYSCF_BOHR_ANGSTROM / 10)
GRADIENT_UNIT = "Eh/PySCF-Bohr-0.52917721092-A"


def reference_force_units(returned):
    """Bind the native energy and Cartesian energy derivative to the selected periodic convention."""
    units = float(returned["bohr_angstrom"]), float(returned["hartree_kj_mol"])
    if returned["gradient_unit"] != GRADIENT_UNIT or units != (PYSCF_BOHR_ANGSTROM, REFERENCE_HARTREE_KJ_MOL):
        raise ValueError("reference force changed physical units")
    return units


@dataclass(frozen=True, slots=True)
class AmberPeriodicCell(CanonicalRecord):
    """The original fixed orthorhombic cell, not a free numerical tuning knob."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/amber-periodic-cell"
    cell_id: str
    raw_topology: ObjectIdentity
    raw_coordinates: ObjectIdentity
    physical_atom_count: int
    lengths_angstrom: tuple[Decimal, Decimal, Decimal]
    angles_degrees: tuple[Decimal, Decimal, Decimal]

    def __post_init__(self):
        from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
        validate_stable_id(self.cell_id)
        exact(self.raw_topology, ObjectIdentity)
        exact(self.raw_coordinates, ObjectIdentity)
        if type(self.physical_atom_count) is not int or self.physical_atom_count <= 0:
            raise ValueError("periodic cell requires the complete physical atom denominator")
        if (type(self.lengths_angstrom) is not tuple or len(self.lengths_angstrom) != 3
                or type(self.angles_degrees) is not tuple or len(self.angles_degrees) != 3):
            raise ValueError("periodic cell requires three exact lengths and angles")
        for value in (*self.lengths_angstrom, *self.angles_degrees):
            validate_decimal(value, field_name="periodic_cell_component", minimum=Decimal(0))
            if value == 0 or not math.isfinite(float(value)):
                raise ValueError("periodic cell components must be finite and positive")
        if self.angles_degrees != (Decimal(90),)*3:
            raise ValueError("this periodic operator requires the original orthorhombic cell")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.cell_id, self)


def read_amber_periodic_cell(representation, raw_topology, raw_coordinates):
    """Bind the exact source bytes and independently compare both box records."""
    from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.amber_parameters import read_prmtop_lines
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_assessment import read_initial_coordinates
    from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation
    exact(representation, MolecularRepresentation)
    for raw, selected in ((raw_topology, representation.raw_topology), (raw_coordinates, representation.raw_coordinates)):
        if type(raw) is not bytes or sha256(raw).hexdigest() != selected.object_fingerprint:
            raise ValueError("periodic cell substitutes its complete original molecular source bytes")
    box = read_initial_coordinates(raw_coordinates.decode('ascii'), len(representation.atoms), periodic=True)[1]
    topology = read_prmtop_lines(StringIO(raw_topology.decode('ascii')), selected_flags=('POINTERS', 'BOX_DIMENSIONS'))
    original = topology.get('BOX_DIMENSIONS', ())
    if (topology['POINTERS'][0] != len(representation.atoms) or len(original) != 4
            or any(abs(a-b) > Decimal('0.00001') for a, b in zip(original, (Decimal(90), *box[:3]), strict=True))):
        raise ValueError("periodic cell disagrees between complete native topology and coordinate records")
    digest = sha256((representation.raw_topology.object_fingerprint+representation.raw_coordinates.object_fingerprint).encode()).hexdigest()
    return AmberPeriodicCell('cell.gp-amber.'+digest, representation.raw_topology,
        representation.raw_coordinates, len(representation.atoms), box[:3], box[3:])


@dataclass(frozen=True, slots=True)
class PeriodicForceSettings(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/periodic-force-settings"
    settings_id: str
    functional: str
    basis: str
    ks_flavour: str
    grid_level: int
    energy_tolerance_hartree: Decimal
    orbital_gradient_tolerance: Decimal
    maximum_scf_cycles: int | None
    memory_megabytes: int
    real_cutoff_angstrom: Decimal
    direct_field_cutoff_angstrom: Decimal
    ewald_eta_inverse_bohr: Decimal
    reciprocal_mesh: tuple[int, int, int]
    ewald_precision: Decimal

    def __post_init__(self):
        validate_stable_id(self.settings_id)
        if self.functional != "wb97x" or self.basis not in {"def2-svpd", "def2-tzvpd"}:
            raise ValueError("the reference requires its selected functional and paired basis choices")
        if self.ks_flavour not in {"RKS", "UKS"}:
            raise ValueError("the electronic spin treatment must be selected explicitly")
        if type(self.grid_level) is not int or not 0 <= self.grid_level <= 9:
            raise ValueError("the numerical integration grid requires an explicit supported level")
        if (self.maximum_scf_cycles is not None
                and (type(self.maximum_scf_cycles) is not int or self.maximum_scf_cycles <= 0)):
            raise ValueError("SCF iterations require an explicit positive integer or no count ceiling")
        if type(self.memory_megabytes) is not int or self.memory_megabytes <= 0:
            raise ValueError("SCF memory requires an explicit positive integer selection")
        for name in ("energy_tolerance_hartree", "orbital_gradient_tolerance", "real_cutoff_angstrom",
                     "direct_field_cutoff_angstrom", "ewald_eta_inverse_bohr", "ewald_precision"):
            value = getattr(self, name)
            validate_decimal(value, field_name=name, minimum=Decimal(0))
            if value == 0 or not math.isfinite(float(value)):
                raise ValueError("electronic tolerances, cutoffs and Ewald exponent must be finite and positive")
        if (type(self.reciprocal_mesh) is not tuple or len(self.reciprocal_mesh) != 3
                or any(type(n) is not int or n < 3 or n % 2 != 1 for n in self.reciprocal_mesh)):
            raise ValueError("the periodic reciprocal mesh requires three explicit positive odd counts")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.settings_id, self)


@dataclass(frozen=True, slots=True)
class ConstrainedPeriodicForceSettings(PeriodicForceSettings):
    """Additive constrained-surface record; original unconstrained bytes persist."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/constrained-periodic-force-settings'
    state: ConstrainedElectronicState

    def __post_init__(self):
        from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
        PeriodicForceSettings.__post_init__(self)
        exact(self.state, ConstrainedElectronicState)
        if self.ks_flavour != 'UKS':
            raise ValueError('the selected charge/spin constrained solver requires UKS')


def validate_periodic_force_settings(settings):
    if type(settings) not in (PeriodicForceSettings, ConstrainedPeriodicForceSettings):
        raise TypeError('periodic force requires its exact unconstrained or constrained settings record')


@dataclass(frozen=True, slots=True)
class OriginalPeriodicMMSettings(CanonicalRecord):
    """Exact historical revision one; it declares no whole-molecule policy."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/periodic-mm-settings"
    settings_id: str
    nonbonded_method: str
    cutoff_angstrom: Decimal
    ewald_relative_tolerance: Decimal
    constraints: str = "NONE_NATURAL_MASSES"
    dispersion_tail: bool = False
    vdw_switch: bool = False
    remove_center_of_mass: bool = False

    def __post_init__(self):
        validate_stable_id(self.settings_id)
        if (self.nonbonded_method not in {"PME", "Ewald"} or self.constraints != "NONE_NATURAL_MASSES"
                or self.dispersion_tail is not False or self.vdw_switch is not False
                or self.remove_center_of_mass is not False):
            raise ValueError("periodic MM requires its explicit unconstrained, unswitched, no-tail convention")
        for name in ("cutoff_angstrom", "ewald_relative_tolerance"):
            value = getattr(self, name)
            validate_decimal(value, field_name=name, minimum=Decimal(0))
            if value == 0 or not math.isfinite(float(value)):
                raise ValueError("periodic MM cutoff and reciprocal tolerance must be finite positive decimals")
        if self.ewald_relative_tolerance >= 1:
            raise ValueError("periodic MM reciprocal tolerance must be below unity")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.settings_id, self)


@dataclass(frozen=True, slots=True)
class UnversionedGeometryPeriodicMMSettings(OriginalPeriodicMMSettings):
    """Retain the interim revision-one shape exactly, for historical reads only.

    That producer added a policy without advancing the revision. Both closed
    revision-one shapes remain distinct types; no missing policy is defaulted
    while decoding, and neither type is eligible for new native work.
    """
    geometry_quality: MolecularGeometryPolicy = field(default_factory=MolecularGeometryPolicy)

    def __post_init__(self):
        OriginalPeriodicMMSettings.__post_init__(self)
        if type(self.geometry_quality) is not MolecularGeometryPolicy:
            raise ValueError('periodic MM requires its authored whole-molecule geometry policy')


@dataclass(frozen=True, slots=True)
class PeriodicMMSettings(UnversionedGeometryPeriodicMMSettings):
    """Current native selection with an explicitly authored geometry policy."""
    VERSION: ClassVar[str] = "2.0.0"


PeriodicMMSettingsRecord = PeriodicMMSettings | OriginalPeriodicMMSettings | UnversionedGeometryPeriodicMMSettings


def validate_periodic_mm_settings(settings):
    """Accept only the exact current or retained scientific record types."""
    if type(settings) not in (PeriodicMMSettings, OriginalPeriodicMMSettings, UnversionedGeometryPeriodicMMSettings):
        raise TypeError('periodic MM requires an exact supported settings record')


def require_current_periodic_mm_settings(settings):
    """Metadata compatibility grants no permission to enter a changed method."""
    if type(settings) is not PeriodicMMSettings:
        raise ValueError('new native work requires periodic MM settings revision 2.0.0; retain historical work with its compatible original installation')


def periodic_geometry_policy(settings):
    """Return only a policy actually present in the selected original record."""
    validate_periodic_mm_settings(settings)
    if type(settings) is OriginalPeriodicMMSettings:
        raise ValueError('historical periodic MM settings declare no geometry policy; use the compatible original reader without assigning a later policy')
    return settings.geometry_quality
