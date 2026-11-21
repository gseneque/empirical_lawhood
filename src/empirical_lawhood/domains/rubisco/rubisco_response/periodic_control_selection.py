# SPDX-License-Identifier: MPL-2.0
"""Prospective finite-difference and numerical-refinement points for a full enzyme.

Every point retains the original physical atom order, topology and cell. These
numerical views are nested in one assembly; they are not biological replicates,
active-state samples or evidence of chemical applicability.
"""
from dataclasses import dataclass, fields, replace
from decimal import Decimal, ROUND_FLOOR, localcontext
from hashlib import sha256, shake_256
import math
from typing import ClassVar

from empirical_lawhood.science.models.datasets import ArrayDatasetManifest
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_nonempty, validate_sha256, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import PeriodicProbeSelection
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_physical_direction import PeriodicPhysicalDirection
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import PeriodicForceSettings, ConstrainedPeriodicForceSettings, PeriodicMMSettingsRecord, validate_periodic_force_settings, validate_periodic_mm_settings


BOHR_ANGSTROM = Decimal('0.52917721092')
CONTROL_SCOPE = 'NESTED_PERIODIC_NUMERICAL_CONTROLS_WITHOUT_ENSEMBLE_CHEMICAL_OR_RATE_ADMISSION'
ACTION_SCOPE = 'NESTED_COMPLETE_FORCE_ACTIONS_WITHOUT_ENSEMBLE_CHEMICAL_RATE_OR_INVERSE_ADMISSION'
REFINEMENT_KINDS = frozenset({'SCF', 'GRID', 'BASIS', 'EWALD', 'DIRECT_EMBEDDING', 'MOLECULAR_EWALD'})


def _positive(value, name):
    validate_decimal(value, field_name=name, minimum=Decimal(0))
    if value == 0 or not math.isfinite(float(value)) or float(value) == 0:
        raise ValueError(name+' requires a positive representable finite value')


@dataclass(frozen=True, slots=True)
class PeriodicDerivativeDirection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/periodic-derivative-direction'
    direction_id: str
    mode: str
    atom_index: int | None = None
    axis: int | None = None
    sign_seed_sha256: str | None = None

    def __post_init__(self):
        validate_stable_id(self.direction_id)
        if self.mode == 'CARTESIAN_COMPONENT':
            if (type(self.atom_index) is not int or self.atom_index < 0
                    or type(self.axis) is not int or not 0 <= self.axis < 3 or self.sign_seed_sha256 is not None):
                raise ValueError('Cartesian direction needs one exact physical atom and axis')
        elif self.mode == 'ALL_PHYSICAL_CARTESIAN_SIGNS':
            if self.atom_index is not None or self.axis is not None or type(self.sign_seed_sha256) is not str:
                raise ValueError('complete sign direction requires its prospective deterministic seed')
            validate_sha256(self.sign_seed_sha256)
        else:
            raise ValueError('unsupported periodic derivative direction')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.direction_id, self)


@dataclass(frozen=True, slots=True)
class PeriodicRefinementBudget(CanonicalRecord):
    """Prospective sensitivity limits, never a proof of exact-force accuracy.

    The component maximum bounds the largest absolute Cartesian component;
    the optional RMS is over all 3N components, not over atom-vector norms.
    No literature-universal tolerances exist for these receiver-specific tests.
    A receiver-derived limit uses |r dot delta_g| <= ||r||_1 ||delta_g||_inf.
    Its algebra bounds the observed refinement difference, not unknown error.
    """
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/periodic-refinement-budget'
    budget_id: str
    maximum_gradient_component_change_hartree_per_bohr: Decimal
    justification: str
    maximum_rms_gradient_component_change_hartree_per_bohr: Decimal | None = None
    maximum_absolute_energy_change_hartree: Decimal | None = None
    receiver: ObjectIdentity | None = None
    receiver_useful_error_hartree_per_bohr: Decimal | None = None
    numerical_allowance_fraction: Decimal | None = None
    receiver_l1_norm: Decimal | None = None

    def __post_init__(self):
        validate_stable_id(self.budget_id)
        validate_nonempty(self.justification, field_name='refinement_budget_justification')
        _positive(self.maximum_gradient_component_change_hartree_per_bohr, 'maximum_gradient_component_change_hartree_per_bohr')
        for value, name in ((self.maximum_rms_gradient_component_change_hartree_per_bohr, 'maximum_rms_gradient_component_change_hartree_per_bohr'),
                (self.maximum_absolute_energy_change_hartree, 'maximum_absolute_energy_change_hartree')):
            if value is not None:
                _positive(value, name)
        derived = (self.receiver, self.receiver_useful_error_hartree_per_bohr,
            self.numerical_allowance_fraction, self.receiver_l1_norm)
        if any(value is not None for value in derived):
            if any(value is None for value in derived):
                raise ValueError('receiver-derived refinement budget requires its complete derivation')
            exact(self.receiver, ObjectIdentity)
            for value, name in zip(derived[1:], ('receiver_useful_error', 'numerical_allowance_fraction', 'receiver_l1_norm'), strict=True):
                _positive(value, name)
            if self.numerical_allowance_fraction > 1:
                raise ValueError('numerical allowance cannot exceed the receiver useful-error budget')
            with localcontext() as context:
                context.prec = 80
                context.rounding = ROUND_FLOOR
                expected = self.receiver_useful_error_hartree_per_bohr*self.numerical_allowance_fraction/self.receiver_l1_norm
            if self.maximum_gradient_component_change_hartree_per_bohr != expected:
                raise ValueError('refinement budget changes its receiver L1 sensitivity derivation')


def refinement_budget_from_receiver(*, budget_id, receiver, useful_error_hartree_per_bohr,
        numerical_allowance_fraction, receiver_l1_norm, justification):
    """Allocate an authored receiver error allowance to observed force sensitivity.

    The caller supplies the dimensionless L1 norm of the actual fixed receiver
    vector. This is for one projected force difference; finite-difference action
    and multi-operand prediction budgets require their own propagation factors.
    """
    for value, name in ((useful_error_hartree_per_bohr, 'receiver_useful_error'),
            (numerical_allowance_fraction, 'numerical_allowance_fraction'), (receiver_l1_norm, 'receiver_l1_norm')):
        _positive(value, name)
    with localcontext() as context:
        context.prec = 80
        context.rounding = ROUND_FLOOR
        maximum = useful_error_hartree_per_bohr*numerical_allowance_fraction/receiver_l1_norm
    return PeriodicRefinementBudget(budget_id, maximum, justification, receiver=receiver,
        receiver_useful_error_hartree_per_bohr=useful_error_hartree_per_bohr,
        numerical_allowance_fraction=numerical_allowance_fraction, receiver_l1_norm=receiver_l1_norm)


@dataclass(frozen=True, slots=True)
class PeriodicNumericalRefinement(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/periodic-numerical-refinement'
    VERSION: ClassVar[str] = '2.0.0'
    refinement_id: str
    kind: str
    electronic: PeriodicForceSettings | ConstrainedPeriodicForceSettings
    molecular: PeriodicMMSettingsRecord
    budget: PeriodicRefinementBudget

    def __post_init__(self):
        validate_stable_id(self.refinement_id)
        validate_periodic_force_settings(self.electronic)
        validate_periodic_mm_settings(self.molecular)
        exact(self.budget, PeriodicRefinementBudget)
        if self.kind not in REFINEMENT_KINDS:
            raise ValueError('unsupported declared periodic numerical refinement')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.refinement_id, self)


def validate_refinement(refinement, electronic, molecular):
    """Refine one numerical choice without changing the selected physical model."""
    exact(refinement, PeriodicNumericalRefinement)
    if type(refinement.electronic) is not type(electronic):
        raise ValueError('numerical refinement cannot change the selected electronic state family')
    if type(refinement.molecular) is not type(molecular):
        raise ValueError('numerical refinement cannot change the selected molecular settings revision')
    allowed = {'SCF': {'energy_tolerance_hartree', 'orbital_gradient_tolerance'},
        'GRID': {'grid_level'}, 'BASIS': {'basis'},
        'EWALD': {'real_cutoff_angstrom', 'reciprocal_mesh', 'ewald_precision'},
        'DIRECT_EMBEDDING': {'direct_field_cutoff_angstrom'}, 'MOLECULAR_EWALD': set()}[refinement.kind]
    changed = {f.name for f in fields(electronic) if f.name != 'settings_id'
        and getattr(refinement.electronic, f.name) != getattr(electronic, f.name)}
    changed_mm = {f.name for f in fields(molecular) if f.name != 'settings_id'
        and getattr(refinement.molecular, f.name) != getattr(molecular, f.name)}
    if (not changed.issubset(allowed) or changed_mm - ({'ewald_relative_tolerance'}
            if refinement.kind == 'MOLECULAR_EWALD' else set()) or not (changed or changed_mm)):
        raise ValueError('refinement changes another selected method or contains no numerical change')
    candidate = refinement.electronic
    if (candidate.energy_tolerance_hartree > electronic.energy_tolerance_hartree
            or candidate.orbital_gradient_tolerance > electronic.orbital_gradient_tolerance
            or candidate.grid_level < electronic.grid_level
            or candidate.real_cutoff_angstrom < electronic.real_cutoff_angstrom
            or candidate.direct_field_cutoff_angstrom < electronic.direct_field_cutoff_angstrom
            or candidate.ewald_precision > electronic.ewald_precision
            or any(a < b for a, b in zip(candidate.reciprocal_mesh, electronic.reciprocal_mesh, strict=True))
            or refinement.molecular.ewald_relative_tolerance > molecular.ewald_relative_tolerance
            or 'basis' in changed and (electronic.basis, candidate.basis) != ('def2-svpd', 'def2-tzvpd')):
        raise ValueError('declared refinement coarsens a selected numerical choice')


@dataclass(frozen=True, slots=True)
class PeriodicControlProtocol(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/periodic-control-protocol'
    VERSION: ClassVar[str] = '2.0.0'
    SCOPE: ClassVar[str] = CONTROL_SCOPE
    INCLUDE_BASELINE: ClassVar[bool] = True
    protocol_id: str
    prototype: ObjectIdentity
    representation: ObjectIdentity
    coordinates: ArrayDatasetManifest
    physical_atom_count: int
    electronic: PeriodicForceSettings | ConstrainedPeriodicForceSettings
    molecular: PeriodicMMSettingsRecord
    directions: tuple[PeriodicDerivativeDirection, ...]
    steps_bohr: tuple[Decimal, ...]
    refinements: tuple[PeriodicNumericalRefinement, ...]
    required_refinement_kinds: tuple[str, ...]
    maximum_directional_error_hartree_per_bohr: Decimal | None = None
    maximum_step_change_hartree_per_bohr: Decimal | None = None
    scope: str = CONTROL_SCOPE

    def __post_init__(self):
        validate_stable_id(self.protocol_id)
        for value, kind in ((self.prototype, ObjectIdentity), (self.representation, ObjectIdentity),
                (self.coordinates, ArrayDatasetManifest)):
            exact(value, kind)
        validate_periodic_force_settings(self.electronic)
        validate_periodic_mm_settings(self.molecular)
        if (self.prototype.object_schema != PeriodicProbeSelection.SCHEMA
                or type(self.physical_atom_count) is not int or self.physical_atom_count < 1
                or len(self.coordinates.members) != 1 or self.coordinates.members[0].dtype != '<f8'
                or self.coordinates.members[0].shape != (self.physical_atom_count, 3)
                or not self.coordinates.members[0].finite_required or self.scope != self.SCOPE):
            raise ValueError('periodic controls change their complete original coordinate population or scope')
        direction_types = (PeriodicDerivativeDirection,) if self.INCLUDE_BASELINE else (PeriodicDerivativeDirection, PeriodicPhysicalDirection)
        for values, kind, name in ((self.directions, direction_types, 'direction_id'),
                (self.refinements, PeriodicNumericalRefinement, 'refinement_id')):
            if type(values) is not tuple:
                raise ValueError('periodic control selections require exact finite tuples')
            for value in values:
                if isinstance(kind, tuple):
                    if type(value) not in kind:
                        raise TypeError('periodic controls require an exact supported direction record')
                else:
                    exact(value, kind)
            if tuple(getattr(v, name) for v in values) != tuple(sorted({getattr(v, name) for v in values})):
                raise ValueError('periodic control selections must be complete, sorted and unique')
        physical_directions = {physical_direction_key(v) for v in self.directions}
        if len(physical_directions) != len(self.directions):
            raise ValueError('periodic directions repeat the same physical displacement under another name')
        if not self.directions and not self.refinements:
            raise ValueError('periodic controls require a declared derivative or refinement question')
        if (type(self.steps_bohr) is not tuple
                or bool(self.steps_bohr) != bool(self.directions)
                or self.directions and (len(self.steps_bohr) < 2
                    or self.steps_bohr != tuple(sorted(set(self.steps_bohr), reverse=True)))):
            raise ValueError('directional controls require at least two distinct decreasing displacement steps')
        for step in self.steps_bohr:
            _positive(step, 'displacement_bohr')
        for direction in self.directions:
            if type(direction) is PeriodicPhysicalDirection:
                if ((direction.representation, direction.coordinates, direction.physical_atom_count)
                        != (self.representation, self.coordinates, self.physical_atom_count)
                        or self.molecular.constraints != 'NONE_NATURAL_MASSES'):
                    raise ValueError('physical direction changes the original model, coordinates or constraints')
            elif direction.atom_index is not None and direction.atom_index >= self.physical_atom_count:
                raise ValueError('derivative direction escapes the full physical atom census')
        for refinement in self.refinements:
            validate_refinement(refinement, self.electronic, self.molecular)
        if (type(self.required_refinement_kinds) is not tuple
                or any(type(kind) is not str or kind not in REFINEMENT_KINDS for kind in self.required_refinement_kinds)
                or self.required_refinement_kinds != tuple(sorted(set(self.required_refinement_kinds)))
                or not set(self.required_refinement_kinds).issubset({row.kind for row in self.refinements})):
            raise ValueError('periodic controls omit or change a required prospective refinement kind')
        if (self.maximum_directional_error_hartree_per_bohr is None) != (self.maximum_step_change_hartree_per_bohr is None):
            raise ValueError('directional admission requires both prospective error and step-change tolerances')
        if not self.directions and self.maximum_directional_error_hartree_per_bohr is not None:
            raise ValueError('directional tolerances require actual prospective derivative points')
        for value in (self.maximum_directional_error_hartree_per_bohr, self.maximum_step_change_hartree_per_bohr):
            if value is not None:
                _positive(value, 'directional_tolerance')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.protocol_id, self)

    @property
    def point_count(self):
        return int(self.INCLUDE_BASELINE)+2*len(self.directions)*len(self.steps_bohr)+len(self.refinements)


@dataclass(frozen=True, slots=True)
class PeriodicForceActionProtocol(PeriodicControlProtocol):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/periodic-force-action-protocol'
    SCOPE: ClassVar[str] = ACTION_SCOPE
    INCLUDE_BASELINE: ClassVar[bool] = False
    directions: tuple[PeriodicDerivativeDirection | PeriodicPhysicalDirection, ...]
    scope: str = ACTION_SCOPE

    def __post_init__(self):
        PeriodicControlProtocol.__post_init__(self)
        if (not self.directions or self.refinements or self.required_refinement_kinds
                or self.maximum_directional_error_hartree_per_bohr is not None
                or self.maximum_step_change_hartree_per_bohr is not None):
            raise ValueError('force actions retain displaced gradients without baseline derivative criteria')


def validate_periodic_control_protocol(protocol):
    if type(protocol) not in (PeriodicControlProtocol, PeriodicForceActionProtocol):
        raise TypeError('periodic points require an exact numerical-control or force-action protocol')


def physical_direction_key(direction):
    if type(direction) is PeriodicPhysicalDirection:
        return ('SPARSE', direction.components)
    exact(direction, PeriodicDerivativeDirection)
    if direction.mode == 'CARTESIAN_COMPONENT':
        return ('SPARSE', ((direction.atom_index, direction.axis, Decimal(1)),))
    return ('SIGNS', direction.sign_seed_sha256)


@dataclass(frozen=True, slots=True)
class PeriodicControlPoint(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/periodic-control-point'
    point_id: str
    protocol: ObjectIdentity
    ordinal: int
    role: str
    direction: ObjectIdentity | None
    signed_step_bohr: Decimal | None
    refinement: ObjectIdentity | None
    coordinate_sha256: str
    physical_atom_count: int
    electronic: PeriodicForceSettings | ConstrainedPeriodicForceSettings
    molecular: PeriodicMMSettingsRecord

    def __post_init__(self):
        validate_stable_id(self.point_id)
        exact(self.protocol, ObjectIdentity)
        validate_periodic_force_settings(self.electronic)
        validate_periodic_mm_settings(self.molecular)
        validate_sha256(self.coordinate_sha256)
        if (self.protocol.object_schema not in (PeriodicControlProtocol.SCHEMA, PeriodicForceActionProtocol.SCHEMA) or type(self.ordinal) is not int
                or self.ordinal < 0 or type(self.physical_atom_count) is not int or self.physical_atom_count < 1):
            raise ValueError('periodic point loses its declared protocol or complete physical population')
        if self.role == 'BASELINE':
            if self.ordinal != 0 or any(v is not None for v in (self.direction, self.signed_step_bohr, self.refinement)):
                raise ValueError('periodic baseline cannot contain a displacement or refinement')
        elif self.role == 'DISPLACED':
            exact(self.direction, ObjectIdentity)
            if self.direction.object_schema not in (PeriodicDerivativeDirection.SCHEMA, PeriodicPhysicalDirection.SCHEMA) or self.refinement is not None:
                raise ValueError('displaced point changes its selected direction')
            validate_decimal(self.signed_step_bohr, field_name='signed_step_bohr')
            _positive(abs(self.signed_step_bohr), 'displacement_bohr')
        elif self.role == 'REFINEMENT':
            exact(self.refinement, ObjectIdentity)
            if (self.refinement.object_schema != PeriodicNumericalRefinement.SCHEMA
                    or self.direction is not None or self.signed_step_bohr is not None):
                raise ValueError('refinement point cannot change the original coordinates')
        else:
            raise ValueError('unsupported periodic control point role')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.point_id, self)


def _coordinates(protocol, coordinate_bytes):
    import numpy as np
    if (type(coordinate_bytes) is not bytes or len(coordinate_bytes) != protocol.physical_atom_count*3*8
            or sha256(coordinate_bytes).hexdigest() != protocol.coordinates.members[0].sha256):
        raise ValueError('periodic controls substitute the complete original coordinate bytes')
    xyz = np.frombuffer(coordinate_bytes, dtype='<f8').reshape(protocol.physical_atom_count, 3)
    if not np.isfinite(xyz).all():
        raise ValueError('periodic original coordinates contain a nonfinite component')
    return xyz


def displaced_coordinates(original, direction, step_bohr):
    """Construct a prospective numerical displacement; keep every other coordinate."""
    import numpy as np
    if type(direction) not in (PeriodicDerivativeDirection, PeriodicPhysicalDirection):
        raise TypeError('periodic displacement requires an exact supported direction')
    validate_decimal(step_bohr, field_name='signed_step_bohr')
    _positive(abs(step_bohr), 'displacement_bohr')
    xyz = np.array(original, dtype='<f8', copy=True)
    if xyz.ndim != 2 or xyz.shape[1] != 3 or not xyz.size or not np.isfinite(xyz).all():
        raise ValueError('periodic displacement requires a finite complete Cartesian atom array')
    if type(direction) is PeriodicPhysicalDirection:
        if direction.physical_atom_count != len(xyz):
            raise ValueError('physical direction changes the complete coordinate population')
    elif direction.atom_index is not None and direction.atom_index >= len(xyz):
        raise ValueError('periodic direction escapes the full physical coordinate census')
    step = float(step_bohr*BOHR_ANGSTROM)
    if type(direction) is PeriodicPhysicalDirection:
        for atom, axis, coefficient in direction.components:
            xyz[atom, axis] += float(coefficient)*step
        expected_changes = len(direction.components)
    elif direction.mode == 'CARTESIAN_COMPONENT':
        xyz[direction.atom_index, direction.axis] += step
        expected_changes = 1
    else:
        bits = shake_256(bytes.fromhex(direction.sign_seed_sha256)).digest((xyz.size+7)//8)
        signs = np.unpackbits(np.frombuffer(bits, dtype='u1'))[:xyz.size].astype('i1')*2-1
        xyz += signs.reshape(xyz.shape)*step
        expected_changes = xyz.size
    changed = xyz != original
    if not np.isfinite(xyz).all() or np.count_nonzero(changed) != expected_changes:
        raise ValueError('periodic displacement is nonfinite or below coordinate resolution')
    return xyz


def control_points(protocol, coordinate_bytes):
    """Derive the whole point census from the declared protocol and original array."""
    validate_periodic_control_protocol(protocol)
    original = _coordinates(protocol, coordinate_bytes)
    points = []
    def append(role, direction, step, refinement, electronic, molecular, raw):
        point = PeriodicControlPoint('point.periodic-control', protocol.identity, len(points), role,
            direction, step, refinement, sha256(raw).hexdigest(), protocol.physical_atom_count, electronic, molecular)
        points.append(replace(point, point_id='point.periodic-control.'+point.fingerprint()))
    if protocol.INCLUDE_BASELINE:
        append('BASELINE', None, None, None, protocol.electronic, protocol.molecular, coordinate_bytes)
    for direction in protocol.directions:
        for step in protocol.steps_bohr:
            for sign in (-1, 1):
                signed = step*sign
                xyz = displaced_coordinates(original, direction, signed)
                append('DISPLACED', direction.identity, signed, None, protocol.electronic, protocol.molecular,
                    xyz.tobytes(order='C'))
    for refinement in protocol.refinements:
        append('REFINEMENT', None, None, refinement.identity, refinement.electronic, refinement.molecular, coordinate_bytes)
    displacements = [p.coordinate_sha256 for p in points if p.role == 'DISPLACED']
    if len(set(displacements)) != len(displacements):
        raise ValueError('distinct declared periodic displacements collapse to the same physical coordinates')
    assert len(points) == protocol.point_count
    return tuple(points)


def validate_control_point(protocol, point):
    """Check the exact prospective ordinal and settings without reading arrays.

    Displaced byte digests are checked against actual original coordinates at
    preparation and native entry. Static discovery does not read those bytes.
    """
    validate_periodic_control_protocol(protocol)
    exact(point, PeriodicControlPoint)
    questions = [('BASELINE', None, None, None, protocol.electronic, protocol.molecular)] if protocol.INCLUDE_BASELINE else []
    questions.extend(('DISPLACED', direction.identity, step*sign, None, protocol.electronic, protocol.molecular)
        for direction in protocol.directions for step in protocol.steps_bohr for sign in (-1, 1))
    questions.extend(('REFINEMENT', None, None, row.identity, row.electronic, row.molecular)
        for row in protocol.refinements)
    if (point.protocol != protocol.identity or point.physical_atom_count != protocol.physical_atom_count
            or point.ordinal >= len(questions)
            or (point.role, point.direction, point.signed_step_bohr, point.refinement,
                point.electronic, point.molecular) != questions[point.ordinal]
            or point.role != 'DISPLACED' and point.coordinate_sha256 != protocol.coordinates.members[0].sha256):
        raise ValueError('periodic point changes its complete prospective question')
    provisional = replace(point, point_id='point.periodic-control')
    if point.point_id != 'point.periodic-control.'+provisional.fingerprint():
        raise ValueError('periodic point changes its derived prospective identity')


def point_coordinates(protocol, point, coordinate_bytes):
    """Reconstruct only the selected declared point before an original native call."""
    validate_control_point(protocol, point)
    expected = control_points(protocol, coordinate_bytes)
    if point.ordinal >= len(expected) or expected[point.ordinal] != point:
        raise ValueError('periodic point changes its complete prospective position, settings or identity')
    original = _coordinates(protocol, coordinate_bytes)
    if point.role == 'DISPLACED':
        direction = next((d for d in protocol.directions if d.identity == point.direction), None)
        if direction is None or abs(point.signed_step_bohr) not in protocol.steps_bohr:
            raise ValueError('periodic point is outside the prospective displacement selection')
        xyz = displaced_coordinates(original, direction, point.signed_step_bohr)
    else:
        xyz = original.copy()
    if sha256(xyz.tobytes(order='C')).hexdigest() != point.coordinate_sha256:
        raise ValueError('periodic point changes its exact complete prospective coordinates')
    return xyz


def prepare_periodic_controls(*, prototype, coordinate_bytes, required_refinement_kinds, directions=(), steps_bohr=(), refinements=(),
        maximum_directional_error_hartree_per_bohr=None, maximum_step_change_hartree_per_bohr=None):
    exact(prototype, PeriodicProbeSelection)
    protocol = PeriodicControlProtocol('protocol.periodic-controls', prototype.identity, prototype.representation,
        prototype.coordinates, prototype.physical_atom_count, prototype.electronic, prototype.molecular,
        directions, steps_bohr, refinements, required_refinement_kinds, maximum_directional_error_hartree_per_bohr,
        maximum_step_change_hartree_per_bohr)
    protocol = replace(protocol, protocol_id='protocol.periodic-controls.'+protocol.fingerprint())
    validate_control_prototype(protocol, prototype)
    return protocol, control_points(protocol, coordinate_bytes)


def prepare_periodic_force_actions(*, prototype, coordinate_bytes, directions, steps_bohr):
    exact(prototype, PeriodicProbeSelection)
    protocol = PeriodicForceActionProtocol('protocol.periodic-force-actions', prototype.identity,
        prototype.representation, prototype.coordinates, prototype.physical_atom_count,
        prototype.electronic, prototype.molecular, directions, steps_bohr, (), ())
    protocol = replace(protocol, protocol_id='protocol.periodic-force-actions.'+protocol.fingerprint())
    validate_control_prototype(protocol, prototype)
    return protocol, control_points(protocol, coordinate_bytes)


def validate_control_prototype(protocol, prototype):
    validate_periodic_control_protocol(protocol)
    exact(prototype, PeriodicProbeSelection)
    if (protocol.prototype, protocol.representation, protocol.coordinates, protocol.physical_atom_count,
            protocol.electronic, protocol.molecular) != (prototype.identity, prototype.representation,
                prototype.coordinates, prototype.physical_atom_count, prototype.electronic, prototype.molecular):
        raise ValueError('periodic controls substitute their original full model or numerical reference')
    for refinement in protocol.refinements:
        if (refinement.electronic.real_cutoff_angstrom >= min(prototype.cell.lengths_angstrom)
                or refinement.molecular.cutoff_angstrom >= min(prototype.cell.lengths_angstrom)/2):
            raise ValueError('periodic refinement exceeds its original periodic cell support')
