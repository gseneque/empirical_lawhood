# SPDX-License-Identifier: MPL-2.0
"""Independent coordinate and two-step numerical derivative checks for bias returns.

The scalar angle uses projected vectors, independently of the producer's
reverse chain rule. No producer, force engine or random generator is called.
The caller authenticates original arrays and supplies explicit numerical
criteria. A successful check admits neither a reaction coordinate nor an
equilibrium ensemble, free energy or physical rate.
"""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
import math
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.contracts import UmbrellaWindow
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_bias import ReferenceBiasConvention


@dataclass(frozen=True, slots=True)
class ReferenceBiasGeometryCriteria(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/reference-bias-geometry-criteria'
    VERSION: ClassVar[str] = '1.0.0'

    criteria_id: str
    convention: ObjectIdentity
    derivative_step_angstrom: Decimal
    maximum_cv_value_errors: tuple[Decimal, ...]
    maximum_cv_derivative_errors_per_angstrom: tuple[Decimal, ...]
    maximum_cv_derivative_refinement_errors_per_angstrom: tuple[Decimal, ...]
    maximum_energy_error_kj_mol: Decimal
    maximum_gradient_error_kj_mol_per_angstrom: Decimal
    maximum_gradient_refinement_error_kj_mol_per_angstrom: Decimal

    def __post_init__(self):
        validate_stable_id(self.criteria_id)
        exact(self.convention, ObjectIdentity)
        if (self.convention.object_schema != ReferenceBiasConvention.SCHEMA
                or self.convention.object_version != ReferenceBiasConvention.VERSION):
            raise ValueError('bias geometry criteria require the exact selected convention')
        tuples = (self.maximum_cv_value_errors, self.maximum_cv_derivative_errors_per_angstrom,
            self.maximum_cv_derivative_refinement_errors_per_angstrom)
        if any(type(values) is not tuple or not values or len(values) != len(tuples[0]) for values in tuples):
            raise ValueError('bias geometry criteria require complete per-CV numerical limits')
        values = (self.derivative_step_angstrom, self.maximum_energy_error_kj_mol,
            self.maximum_gradient_error_kj_mol_per_angstrom,
            self.maximum_gradient_refinement_error_kj_mol_per_angstrom,
            *(value for group in tuples for value in group))
        for value in values:
            validate_decimal(value, field_name='bias geometry numerical selection', minimum=Decimal(0))
            if not math.isfinite(float(value)) or value != 0 and float(value) == 0:
                raise ValueError('bias geometry criteria must be representable finite numerical selections')
        if self.derivative_step_angstrom <= 0 or float(self.derivative_step_angstrom)/2 == 0:
            raise ValueError('bias geometry derivative step and its half must be positive and representable')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.criteria_id, self)


class _UnresolvedGeometry(ValueError):
    """A finite-difference stencil cannot resolve a smooth local geometry."""


def validate_bias_geometry_criteria(criteria, window, convention):
    exact(criteria, ReferenceBiasGeometryCriteria)
    exact(window, UmbrellaWindow)
    exact(convention, ReferenceBiasConvention)
    if (criteria.convention != convention.identity
            or convention.window != ObjectIdentity.from_record(window.window_id, window)
            or len(criteria.maximum_cv_value_errors) != len(window.cv_kinds)):
        raise ValueError('bias geometry assessment substitutes its selected convention or complete CV census')


def _angle_delta(value):
    return math.atan2(math.sin(value), math.cos(value))


def _scalar_geometry(points, lengths, kind):
    import numpy as np

    bonds = np.diff(points, axis=0)
    images = np.floor(bonds/lengths + .5)
    bonds -= images*lengths
    resolution = 32*np.finfo(float).eps*np.maximum(lengths, np.max(abs(points), axis=0))
    if np.any(lengths/2-abs(bonds) <= resolution):
        raise _UnresolvedGeometry('periodic_image_boundary')
    norms = np.linalg.norm(bonds, axis=1)
    if not np.isfinite(norms).all() or np.any(norms <= np.linalg.norm(resolution)):
        raise _UnresolvedGeometry('unresolved_bond')
    if kind == 'DISTANCE':
        value = float(norms[0])
    elif kind == 'DISTANCE_DIFFERENCE':
        value = float(norms[0]-norms[1])
    else:
        axis = bonds[1]/norms[1]
        left = -bonds[0]+axis*np.dot(axis, bonds[0])
        right = bonds[2]-axis*np.dot(axis, bonds[2])
        left_norm, right_norm = np.linalg.norm(left), np.linalg.norm(right)
        if min(left_norm/norms[0], right_norm/norms[2]) <= 64*np.finfo(float).eps:
            raise _UnresolvedGeometry('collinear_torsion_plane')
        left, right = left/left_norm, right/right_norm
        value = math.atan2(float(np.dot(np.cross(axis, left), right)), float(np.dot(left, right)))
    return value, images


def independent_reference_bias_coordinates(*, window, convention, physical_model_id,
        physical_atom_ids, coordinates_angstrom, cell_vectors_angstrom):
    """Project selected scalar coordinates without the producing bias evaluator.

    This geometry projection supplies no derivative or ensemble admission.
    Native custody and the selected force/geometry criteria remain separate.
    """
    import numpy as np
    exact(window, UmbrellaWindow)
    exact(convention, ReferenceBiasConvention)
    if (convention.window != ObjectIdentity.from_record(window.window_id, window)
            or physical_model_id != window.model_id or type(physical_atom_ids) is not tuple
            or not physical_atom_ids or len(set(physical_atom_ids)) != len(physical_atom_ids)):
        raise ValueError('coordinate projection changes its original model or ordered atom census')
    units = tuple('RADIAN' if kind == 'IMPROPER_DIHEDRAL' else 'ANGSTROM' for kind in window.cv_kinds)
    constants = tuple('KJ_PER_MOL_PER_RADIAN_SQUARED' if kind == 'IMPROPER_DIHEDRAL'
        else 'KJ_PER_MOL_PER_ANGSTROM_SQUARED' for kind in window.cv_kinds)
    if convention.center_units != units or convention.force_constant_units != constants:
        raise ValueError('coordinate projection changes its explicit units')
    indices = {atom: i for i, atom in enumerate(physical_atom_ids)}
    if any(atom not in indices for atoms in window.cv_atom_ids for atom in atoms):
        raise ValueError('coordinate projection names an absent physical atom')
    if np.iscomplexobj(coordinates_angstrom) or np.iscomplexobj(cell_vectors_angstrom):
        raise ValueError('coordinate projection requires real original arrays')
    xyz, cell = np.asarray(coordinates_angstrom, dtype='<f8'), np.asarray(cell_vectors_angstrom, dtype='<f8')
    if (xyz.shape != (len(indices), 3) or not np.isfinite(xyz).all()
            or cell.shape != (3, 3) or not np.isfinite(cell).all()
            or not np.array_equal(cell, np.diag(np.diag(cell))) or np.any(np.diag(cell) <= 0)):
        raise ValueError('coordinate projection requires complete finite arrays and a positive orthorhombic cell')
    return tuple(_scalar_geometry(xyz[[indices[a] for a in atoms]], np.diag(cell), kind)[0]
        for atoms, kind in zip(window.cv_atom_ids, window.cv_kinds, strict=True))


def _derivatives(points, lengths, kind, center, constant, step, value, images):
    """Two nonuniform central stencils from scalar geometry and energy only."""
    import numpy as np

    angle = kind == 'IMPROPER_DIHEDRAL'
    displacement = _angle_delta(value-center) if angle else value-center
    gradients, derivatives = [], []
    for h in (step, step/2):
        derivative, gradient = np.zeros_like(points), np.zeros_like(points)
        for atom in range(len(points)):
            for axis in range(3):
                deltas, distances = [], []
                for sign in (1, -1):
                    moved = points.copy()
                    moved[atom, axis] += sign*h
                    distance = sign*(moved[atom, axis]-points[atom, axis])
                    if not math.isfinite(distance) or distance <= 0:
                        raise _UnresolvedGeometry('unresolved_displacement')
                    shifted, shifted_images = _scalar_geometry(moved, lengths, kind)
                    if not np.array_equal(images, shifted_images):
                        raise _UnresolvedGeometry('stencil_crosses_periodic_image')
                    delta = _angle_delta(shifted-value) if angle else shifted-value
                    if angle and abs(displacement+delta) >= math.pi-64*np.finfo(float).eps:
                        raise _UnresolvedGeometry('stencil_crosses_restraint_cusp')
                    deltas.append(delta)
                    distances.append(distance)
                plus, minus = deltas
                hp, hm = distances
                # The actual representable positive/negative steps can differ.
                derivative[atom, axis] = (hm*(plus/hp)-hp*(minus/hm))/(hp+hm)
                ep = constant*plus*(displacement+.5*plus)
                em = constant*minus*(displacement+.5*minus)
                gradient[atom, axis] = (hm*(ep/hp)-hp*(em/hm))/(hp+hm)
        derivatives.append(derivative)
        gradients.append(gradient)
    return derivatives, gradients


def assess_reference_bias_geometry(*, window, convention, criteria, physical_model_id,
        physical_atom_ids, coordinates_angstrom, cell_vectors_angstrom, returned):
    """Compare original returns to geometry and two explicit derivative steps.

    Per-CV value limits use the selected convention's length or angle units.
    Derivative limits use that CV unit per angstrom. Step refinement is a
    numerical consistency check, not a rigorous derivative-error enclosure.
    Finite violations remain falsified even when another stencil is unresolved.
    """
    import numpy as np

    validate_bias_geometry_criteria(criteria, window, convention)
    if physical_model_id != window.model_id:
        raise ValueError('bias geometry assessment changes its original physical material')
    if (type(physical_atom_ids) is not tuple or not physical_atom_ids
            or any(type(atom) is not str or not atom for atom in physical_atom_ids)
            or len(set(physical_atom_ids)) != len(physical_atom_ids)):
        raise ValueError('bias geometry assessment requires a complete unique physical atom order')
    indices = {atom:i for i, atom in enumerate(physical_atom_ids)}
    if any(atom not in indices for atoms in window.cv_atom_ids for atom in atoms):
        raise ValueError('bias geometry assessment names an absent physical atom')
    if any(np.iscomplexobj(value) for value in (coordinates_angstrom, cell_vectors_angstrom)):
        raise ValueError('bias geometry assessment requires real original coordinates and cell')
    xyz, cell = np.asarray(coordinates_angstrom, dtype='<f8'), np.asarray(cell_vectors_angstrom, dtype='<f8')
    if (xyz.shape != (len(indices), 3) or not np.isfinite(xyz).all()
            or cell.shape != (3, 3) or not np.isfinite(cell).all()
            or not np.array_equal(cell, np.diag(np.diag(cell))) or np.any(np.diag(cell) <= 0)):
        raise ValueError('bias geometry assessment requires all finite coordinates and a positive orthorhombic cell')
    units = tuple('RADIAN' if kind == 'IMPROPER_DIHEDRAL' else 'ANGSTROM' for kind in window.cv_kinds)
    constants_units = tuple('KJ_PER_MOL_PER_RADIAN_SQUARED' if kind == 'IMPROPER_DIHEDRAL'
        else 'KJ_PER_MOL_PER_ANGSTROM_SQUARED' for kind in window.cv_kinds)
    rows = tuple(tuple(indices[atom] for atom in atoms) for atoms in window.cv_atom_ids)
    expected = dict(window=convention.window.to_document(), convention=convention.identity.to_document(),
        physical_model_id=physical_model_id, physical_atoms=len(xyz), gradient_kind='ENERGY_DERIVATIVE_NOT_FORCE',
        reference_energy_included=False, equilibrium_admission='UNEVALUABLE', rate_admission='UNEVALUABLE')
    if (convention.center_units != units or convention.force_constant_units != constants_units
            or type(returned) is not dict or any(returned.get(k) != value for k, value in expected.items())
            or tuple(returned.get('cv_units', ())) != units
            or tuple(tuple(row) for row in returned.get('cv_atom_indices', ())) != rows):
        raise ValueError('bias geometry assessment changes original bias identities, units or atom rows')
    ncv = len(rows)
    def array(value, shape):
        if np.iscomplexobj(value):
            raise ValueError('bias geometry assessment requires real original returned arrays')
        a = np.asarray(value, dtype='<f8')
        if a.shape != shape or not np.isfinite(a).all():
            raise ValueError('bias geometry assessment requires complete finite original returned arrays')
        return a
    recorded_values = array(returned['cv_values'], (ncv,))
    recorded_displacements = array(returned['cv_displacements'], (ncv,))
    recorded_energies = array(returned['term_energies_kj_mol'], (ncv,))
    recorded_gradient = array(returned['gradient_kj_mol_per_angstrom'], xyz.shape)
    recorded_total = float(array(returned['energy_kj_mol'], ()))
    local = returned['cv_cartesian_derivatives']
    if len(local) != ncv:
        raise ValueError('bias geometry assessment loses original local derivative terms')
    local = tuple(array(derivative, (len(rows[i]), 3)) for i, derivative in enumerate(local))
    centers, constants = np.array([float(v) for v in window.centers]), np.array([float(v) for v in window.force_constants])
    if (not np.isfinite(centers).all() or not np.isfinite(constants).all() or np.any(constants <= 0)
            or any(original != 0 and value == 0 for original, value in zip(window.centers, centers, strict=True))
            or any(abs(centers[i]) > math.pi for i, kind in enumerate(window.cv_kinds) if kind == 'IMPROPER_DIHEDRAL')):
        raise ValueError('bias geometry parameters are not representable in their selected units')
    terms, energies, failed = [], [], False
    full = [np.zeros_like(xyz), np.zeros_like(xyz)]
    active = sorted({i for group in rows for i in group})
    spectator = recorded_gradient.copy()
    spectator[active] = 0.
    spectator_error = float(np.max(abs(spectator)))
    failed |= Fraction(spectator_error) > Fraction(criteria.maximum_gradient_error_kj_mol_per_angstrom)
    for i, (atom_rows, kind, center, constant) in enumerate(zip(rows, window.cv_kinds, centers, constants, strict=True)):
        term = dict(cv_index=i, cv_unit=units[i], value_error=None, displacement_error=None,
            energy_error_kj_mol=None, derivative_error_per_angstrom=None,
            derivative_refinement_error_per_angstrom=None, unresolved_geometry=None)
        points = xyz[list(atom_rows)]
        try:
            with np.errstate(over='raise', invalid='raise', divide='raise'):
                value, images = _scalar_geometry(points, np.diag(cell), kind)
                angle = kind == 'IMPROPER_DIHEDRAL'
                if angle and abs(recorded_values[i]) > math.pi:
                    raise ValueError('recorded torsion is not its principal signed angle')
                displacement = _angle_delta(value-center) if angle else value-center
                if angle and math.pi-abs(displacement) <= 64*np.finfo(float).eps:
                    raise _UnresolvedGeometry('restraint_cusp')
                energy = .5*constant*displacement*displacement
                if not math.isfinite(energy):
                    raise _UnresolvedGeometry('nonfinite_scalar_energy')
                energies.append(float(energy))
                term.update(value_error=abs(_angle_delta(value-recorded_values[i]) if angle else value-recorded_values[i]),
                    displacement_error=abs(displacement-recorded_displacements[i]),
                    energy_error_kj_mol=abs(energy-recorded_energies[i]))
                failed |= (Fraction(float(max(term['value_error'], term['displacement_error']))) > Fraction(criteria.maximum_cv_value_errors[i])
                    or Fraction(float(term['energy_error_kj_mol'])) > Fraction(criteria.maximum_energy_error_kj_mol))
                derivatives, gradients = _derivatives(points, np.diag(cell), kind, center, constant,
                    float(criteria.derivative_step_angstrom), value, images)
                if any(not np.isfinite(v).all() for v in (*derivatives, *gradients)):
                    raise _UnresolvedGeometry('nonfinite_numerical_derivative')
                term.update(derivative_error_per_angstrom=float(np.max(abs(derivatives[1]-local[i]))),
                    derivative_refinement_error_per_angstrom=float(np.max(abs(derivatives[1]-derivatives[0]))))
                failed |= (Fraction(term['derivative_error_per_angstrom']) > Fraction(criteria.maximum_cv_derivative_errors_per_angstrom[i])
                    or Fraction(term['derivative_refinement_error_per_angstrom']) > Fraction(criteria.maximum_cv_derivative_refinement_errors_per_angstrom[i]))
                for order in range(2):
                    full[order][list(atom_rows)] += gradients[order]
        except (_UnresolvedGeometry, FloatingPointError) as error:
            term['unresolved_geometry'] = str(error)
        terms.append(term)
    resolved = all(term['unresolved_geometry'] is None for term in terms)
    energy_error = abs(math.fsum(energies)-recorded_total) if len(energies) == ncv else None
    if energy_error is not None:
        failed |= Fraction(energy_error) > Fraction(criteria.maximum_energy_error_kj_mol)
    gradient_error = float(np.max(abs(full[1]-recorded_gradient))) if resolved else None
    refinement_error = float(np.max(abs(full[1]-full[0]))) if resolved else None
    if resolved:
        failed |= (Fraction(gradient_error) > Fraction(criteria.maximum_gradient_error_kj_mol_per_angstrom)
            or Fraction(refinement_error) > Fraction(criteria.maximum_gradient_refinement_error_kj_mol_per_angstrom))
    return dict(criteria=criteria.identity.to_document(), criteria_record=criteria.to_document(),
        convention=convention.identity.to_document(), terms=terms,
        derivative_steps_angstrom=(str(Fraction(criteria.derivative_step_angstrom)), str(Fraction(criteria.derivative_step_angstrom)/2)),
        energy_error_kj_mol=energy_error, gradient_error_kj_mol_per_angstrom=gradient_error,
        gradient_refinement_error_kj_mol_per_angstrom=refinement_error,
        spectator_gradient_error_kj_mol_per_angstrom=spectator_error,
        selected_bias_geometry_criteria='FALSIFIED' if failed else 'SATISFIED' if resolved else 'UNEVALUABLE',
        new_operator_evaluations=0, producer_bias_evaluations=0,
        equilibrium_admission='UNEVALUABLE', physical_rate_admission='UNEVALUABLE')
