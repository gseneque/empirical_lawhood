# SPDX-License-Identifier: MPL-2.0
"""Explicit umbrella energies and analytic Cartesian gradients.

This numerical component interprets the CVs in an existing window only after
the caller selects units and geometry conventions. It does not execute that
window's historical Metropolis schedule, change a reference operator, prepare
an equilibrium ensemble or infer a free energy or physical rate. The native
caller owns authenticated atom order, material, cell and original custody.
"""

from dataclasses import dataclass
import math
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.contracts import UmbrellaWindow
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id

from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact


_UNITS = {
    'DISTANCE': ('ANGSTROM', 'KJ_PER_MOL_PER_ANGSTROM_SQUARED'),
    'DISTANCE_DIFFERENCE': ('ANGSTROM', 'KJ_PER_MOL_PER_ANGSTROM_SQUARED'),
    'IMPROPER_DIHEDRAL': ('RADIAN', 'KJ_PER_MOL_PER_RADIAN_SQUARED'),
}


@dataclass(frozen=True, slots=True)
class ReferenceBiasConvention(CanonicalRecord):
    """Additional, explicit interpretation of an unchanged historical window."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/reference-bias-convention'
    VERSION: ClassVar[str] = '1.0.0'

    convention_id: str
    window: ObjectIdentity
    center_units: tuple[str, ...]
    force_constant_units: tuple[str, ...]
    distance_difference: str
    dihedral: str
    periodic_images: str

    def __post_init__(self):
        validate_stable_id(self.convention_id)
        exact(self.window, ObjectIdentity)
        if self.window.object_schema != UmbrellaWindow.SCHEMA or self.window.object_version != UmbrellaWindow.VERSION:
            raise ValueError('bias convention requires an exact umbrella-window identity')
        if (type(self.center_units) is not tuple or type(self.force_constant_units) is not tuple
                or not self.center_units or len(self.center_units) != len(self.force_constant_units)
                or any(pair not in _UNITS.values()
                    for pair in zip(self.center_units, self.force_constant_units, strict=True))):
            raise ValueError('bias convention requires explicit matching length or angle units')
        if (self.distance_difference != 'DISTANCE_12_MINUS_DISTANCE_23'
                or self.dihedral != 'SIGNED_ORDERED_TORSION_SHORTEST_ANGULAR_RESTRAINT'
                or self.periodic_images != 'ORTHORHOMBIC_MINIMUM_IMAGE_EACH_CONSECUTIVE_BOND'):
            raise ValueError('unsupported explicit bias geometry convention')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.convention_id, self)


def _bond(first, second, lengths):
    import numpy as np

    # Refuse a numerically unresolved image rather than silently select a
    # derivative at a nearest-image boundary. The guard is numerical, not a
    # molecular contact cutoff. A large translation also increases its ULP.
    delta = first - second
    imaged = delta - lengths * np.rint(delta / lengths)
    resolution = 32 * np.finfo(float).eps * np.maximum(lengths, np.maximum(abs(first), abs(second)))
    if np.any(lengths / 2 - abs(imaged) <= resolution):
        raise ValueError('bias bond lies on an unresolved periodic-image boundary')
    length = float(np.linalg.norm(imaged))
    if not math.isfinite(length) or length <= float(np.linalg.norm(resolution)):
        raise ValueError('bias bond has a coincident or numerically unresolved direction')
    return imaged, length, imaged / length


def _torsion(bonds):
    """Reverse analytic chain rule through normalized bonds and atan2."""
    import numpy as np

    a, b, c = (bond[2] for bond in bonds)
    n1, n2 = np.cross(a, b), np.cross(b, c)
    if min(np.linalg.norm(n1), np.linalg.norm(n2)) <= 64 * np.finfo(float).eps:
        raise ValueError('bias torsion is singular at a collinear plane')
    x = float(np.dot(n1, n2))
    cross = np.cross(n1, n2)
    y = float(np.dot(b, cross))
    denominator = x*x + y*y
    dx, dy = -y / denominator, x / denominator
    dn1 = dx*n2 + dy*np.cross(n2, b)
    dn2 = dx*n1 + dy*np.cross(b, n1)
    da = np.cross(b, dn1)
    db = np.cross(dn1, a) + np.cross(c, dn2) + dy*cross
    dc = np.cross(dn2, b)
    derivatives = [(g - u*np.dot(u, g)) / bond[1]
        for g, u, bond in zip((da, db, dc), (a, b, c), bonds, strict=True)]
    ga, gb, gc = derivatives
    return math.atan2(y, x), np.array((-ga, ga-gb, gb-gc, gc))


def evaluate_reference_umbrella_bias(*, window, convention, physical_model_id,
                                     physical_atom_ids, coordinates_angstrom,
                                     cell_vectors_angstrom):
    """Return only the bias, with energy in kJ/mol and gradient in kJ/mol/A.

    DISTANCE uses atoms (1, 2). DISTANCE_DIFFERENCE is r12-r23. The four
    ordered torsion atoms define consecutive bonds 1->2->3->4, without any
    inferred connectivity or central-atom reordering. Each bond uses the
    orthorhombic minimum image. Torsion restraint displacement is the shortest
    signed angular difference; its antipodal cusp is refused. Each energy is
    k*(q-q0)**2/2, including the wrapped torsion displacement.

    Every physical atom receives a gradient row, including exact zeros for
    unrestrained atoms. Local CV derivatives are returned separately. The
    caller must retain reference and bias components separately and must not
    pass a biased force to the unbiased diagnostic trajectory operation.
    """
    import numpy as np

    exact(window, UmbrellaWindow)
    exact(convention, ReferenceBiasConvention)
    window_identity = ObjectIdentity.from_record(window.window_id, window)
    if convention.window != window_identity or physical_model_id != window.model_id:
        raise ValueError('bias substitutes the selected window or physical model')
    units = tuple(_UNITS[kind] for kind in window.cv_kinds)
    if tuple(zip(convention.center_units, convention.force_constant_units, strict=True)) != units:
        raise ValueError('bias units do not match the complete selected CV census')
    if (type(physical_atom_ids) is not tuple or not physical_atom_ids
            or any(type(atom) is not str or not atom for atom in physical_atom_ids)
            or len(set(physical_atom_ids)) != len(physical_atom_ids)):
        raise ValueError('bias requires a complete unique ordered physical atom census')
    indices = {atom: i for i, atom in enumerate(physical_atom_ids)}
    if any(atom not in indices for atoms in window.cv_atom_ids for atom in atoms):
        raise ValueError('bias CV names a nonphysical or absent atom')
    if np.iscomplexobj(coordinates_angstrom) or np.iscomplexobj(cell_vectors_angstrom):
        raise ValueError('bias coordinates and cell must be real')
    xyz = np.asarray(coordinates_angstrom, dtype='<f8')
    cell = np.asarray(cell_vectors_angstrom, dtype='<f8')
    if (xyz.shape != (len(physical_atom_ids), 3) or not np.isfinite(xyz).all()
            or cell.shape != (3, 3) or not np.isfinite(cell).all()
            or not np.array_equal(cell, np.diag(np.diag(cell))) or np.any(np.diag(cell) <= 0)):
        raise ValueError('bias requires all finite physical coordinates and a positive orthorhombic cell')
    centers = np.array([float(x) for x in window.centers])
    constants = np.array([float(x) for x in window.force_constants])
    if (not np.isfinite(centers).all() or not np.isfinite(constants).all() or np.any(constants <= 0)
            or any(exact_value != 0 and value == 0 for exact_value, value in zip(window.centers, centers, strict=True))
            or any(abs(center) > math.pi for center, kind in zip(centers, window.cv_kinds, strict=True)
                if kind == 'IMPROPER_DIHEDRAL')):
        raise ValueError('bias parameters must be representable, with torsion centers in [-pi, pi]')
    gradient = np.zeros_like(xyz)
    values, displacements, energies, local_derivatives, atom_rows = [], [], [], [], []
    lengths = np.diag(cell)
    with np.errstate(over='raise', invalid='raise', divide='raise'):
        for atoms, kind, center, constant in zip(window.cv_atom_ids, window.cv_kinds,
                                                centers, constants, strict=True):
            selected = tuple(indices[atom] for atom in atoms)
            positions = xyz[list(selected)]
            if kind == 'DISTANCE':
                _, value, direction = _bond(positions[0], positions[1], lengths)
                derivative = np.array((direction, -direction))
            elif kind == 'DISTANCE_DIFFERENCE':
                _, r12, d12 = _bond(positions[0], positions[1], lengths)
                _, r23, d23 = _bond(positions[1], positions[2], lengths)
                value, derivative = r12-r23, np.array((d12, -d12-d23, d23))
            else:
                bonds = tuple(_bond(positions[i+1], positions[i], lengths) for i in range(3))
                value, derivative = _torsion(bonds)
            displacement = value-center
            if kind == 'IMPROPER_DIHEDRAL':
                displacement = math.atan2(math.sin(displacement), math.cos(displacement))
                if math.pi-abs(displacement) <= 64*np.finfo(float).eps:
                    raise ValueError('bias torsion restraint lies at an antipodal cusp')
            energy = .5*constant*displacement*displacement
            contribution = constant*displacement*derivative
            gradient[list(selected)] += contribution
            if not (math.isfinite(energy) and np.isfinite(derivative).all() and np.isfinite(gradient).all()):
                raise ValueError('bias produced a nonfinite value or Cartesian gradient')
            values.append(value)
            displacements.append(displacement)
            energies.append(energy)
            local_derivatives.append(derivative)
            atom_rows.append(selected)
    total = math.fsum(energies)
    if not math.isfinite(total):
        raise ValueError('bias total energy is not finite')
    return dict(window=window_identity.to_document(), convention=convention.identity.to_document(),
        physical_model_id=physical_model_id, physical_atoms=len(xyz),
        cv_values=tuple(values), cv_units=convention.center_units, cv_displacements=tuple(displacements),
        cv_atom_indices=tuple(atom_rows), cv_cartesian_derivatives=tuple(local_derivatives),
        term_energies_kj_mol=tuple(energies), energy_kj_mol=total,
        gradient_kj_mol_per_angstrom=gradient, gradient_kind='ENERGY_DERIVATIVE_NOT_FORCE',
        reference_energy_included=False, equilibrium_admission='UNEVALUABLE', rate_admission='UNEVALUABLE')
