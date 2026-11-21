# SPDX-License-Identifier: MPL-2.0
"""Reconstruct complete local force actions from authenticated original returns."""
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256, shake_256
import math
from typing import ClassVar

from empirical_lawhood.science.models.datasets import ArrayDatasetManifest, ArrayDatasetMember
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_read import ControlPointReadout, _read_point, _values
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_selection import BOHR_ANGSTROM, PeriodicForceActionProtocol, control_points, displaced_coordinates
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_translation import validate_configs
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_physical_direction import PeriodicPhysicalDirection
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import PeriodicProbeResult
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import validate_periodic_probe_model

SCOPE = 'LOCAL_CARTESIAN_ACTION_COMPARISONS_WITHOUT_DERIVATIVE_BOUND_OR_PHYSICAL_ADMISSION'


@dataclass(frozen=True, slots=True)
class PeriodicForceActionComparison(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/periodic-force-action-comparison'
    direction: ObjectIdentity
    step_bohr: Decimal
    minus_point: ObjectIdentity
    plus_point: ObjectIdentity
    previous_step_bohr: Decimal | None
    action: ArrayDatasetManifest | None
    input_norm: Decimal | None
    action_norm_hartree_per_bohr2: Decimal | None
    self_curvature_hartree_per_bohr2: Decimal | None
    orthogonal_action_norm_hartree_per_bohr2: Decimal | None
    maximum_secant_direction_error: Decimal | None
    maximum_midpoint_shift_bohr: Decimal | None
    absolute_step_change_hartree_per_bohr2: Decimal | None
    relative_step_change: Decimal | None

    def __post_init__(self):
        for pin in (self.direction, self.minus_point, self.plus_point):
            exact(pin, ObjectIdentity)
        validate_decimal(self.step_bohr, field_name='step_bohr', minimum=Decimal(0))
        if self.step_bohr == 0:
            raise ValueError('force action needs a positive original displacement')
        if self.previous_step_bohr is not None:
            validate_decimal(self.previous_step_bohr, field_name='previous_step_bohr', minimum=self.step_bohr)
            if self.previous_step_bohr == self.step_bohr:
                raise ValueError('force action repeats its comparison step')
        values = (self.input_norm, self.action_norm_hartree_per_bohr2, self.self_curvature_hartree_per_bohr2,
            self.orthogonal_action_norm_hartree_per_bohr2, self.maximum_secant_direction_error,
            self.maximum_midpoint_shift_bohr)
        if self.action is None:
            if any(v is not None for v in (*values, self.absolute_step_change_hartree_per_bohr2, self.relative_step_change)):
                raise ValueError('force action invents values for missing original gradients')
        else:
            exact(self.action, ArrayDatasetManifest)
            for index, value in enumerate(values):
                validate_decimal(value, field_name='force_action_value', minimum=None if index == 2 else Decimal(0))
            if self.input_norm == 0 or len(self.action.members) != 1:
                raise ValueError('force action loses its nonzero input or complete array')
            if self.action.scientific_references != tuple(sorted(
                    (self.direction, self.minus_point, self.plus_point), key=lambda pin:pin.object_id)):
                raise ValueError('force action substitutes its original direction or gradient sources')
        for value in (self.absolute_step_change_hartree_per_bohr2, self.relative_step_change):
            if value is not None:
                validate_decimal(value, field_name='action_step_change', minimum=Decimal(0))
                if self.previous_step_bohr is None:
                    raise ValueError('force action invents a comparison without a preceding step')


@dataclass(frozen=True, slots=True)
class PeriodicForceActionsReadout(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/periodic-force-actions-readout'
    readout_id: str
    protocol: PeriodicForceActionProtocol
    points: tuple[ControlPointReadout, ...]
    comparisons: tuple[PeriodicForceActionComparison, ...]
    scope: str = SCOPE

    def __post_init__(self):
        from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_selection import validate_control_point
        validate_stable_id(self.readout_id)
        exact(self.protocol, PeriodicForceActionProtocol)
        if type(self.points) is not tuple or type(self.comparisons) is not tuple or self.scope != SCOPE:
            raise ValueError('force-action readout changes its finite census or evidence scope')
        for point in self.points:
            exact(point, ControlPointReadout)
            validate_control_point(self.protocol, point.point)
        if tuple(p.point.ordinal for p in self.points) != tuple(range(self.protocol.point_count)):
            raise ValueError('force-action readout omits a selected point')
        expected = tuple((d.identity, step) for d in self.protocol.directions for step in self.protocol.steps_bohr)
        for row in self.comparisons:
            exact(row, PeriodicForceActionComparison)
        if tuple((r.direction, r.step_bohr) for r in self.comparisons) != expected:
            raise ValueError('force-action readout omits a selected direction or scale')
        by = {(p.point.direction, p.point.signed_step_bohr):p.point for p in self.points}
        for row in self.comparisons:
            index = self.protocol.steps_bohr.index(row.step_bohr)
            previous = self.protocol.steps_bohr[index-1] if index else None
            if (row.minus_point != by[(row.direction, -row.step_bohr)].identity
                    or row.plus_point != by[(row.direction, row.step_bohr)].identity
                    or row.previous_step_bohr != previous):
                raise ValueError('force-action comparison substitutes its original operands or step order')
            if row.action is not None:
                member, = row.action.members
                if (member.name != 'cartesian-hessian-action' or member.dtype != '<f8'
                        or member.shape != (self.protocol.physical_atom_count, 3) or not member.finite_required):
                    raise ValueError('force action changes its complete physical output array')


def direction_values(direction, physical_atom_count):
    import numpy as np
    values = np.zeros((physical_atom_count, 3), dtype='<f8')
    if type(direction) is PeriodicPhysicalDirection:
        if direction.physical_atom_count != physical_atom_count:
            raise ValueError('force-action direction changes its physical population')
        for atom, axis, coefficient in direction.components:
            values[atom, axis] = float(coefficient)
    elif direction.mode == 'CARTESIAN_COMPONENT':
        values[direction.atom_index, direction.axis] = 1
    else:
        bits = shake_256(bytes.fromhex(direction.sign_seed_sha256)).digest((values.size+7)//8)
        values[:] = (np.unpackbits(np.frombuffer(bits, dtype='u1'))[:values.size].astype('i1')*2-1).reshape(values.shape)
    return values


def compare_force_actions(protocol, coordinate_bytes, points, values):
    """Return reconstructed arrays and comparisons; missing points stay missing."""
    import numpy as np
    exact(protocol, PeriodicForceActionProtocol)
    if tuple(points) != control_points(protocol, coordinate_bytes):
        raise ValueError('force-action calculation changes its complete selected point census')
    original = np.frombuffer(coordinate_bytes, dtype='<f8').reshape((-1, 3))
    by = {(p.direction, p.signed_step_bohr):p for p in points}
    rows, arrays = [], []
    for direction in protocol.directions:
        vector = direction_values(direction, protocol.physical_atom_count)
        norm2 = float(np.vdot(vector, vector))
        previous_step, previous_action = None, None
        for step in protocol.steps_bohr:
            minus, plus = (by[(direction.identity, sign*step)] for sign in (-1, 1))
            operands = (values.get(minus.point_id), values.get(plus.point_id))
            action = manifest = None
            metrics = (None,)*8
            if all(v is not None for v in operands):
                gm, gp = (v[1] for v in operands)
                if any(g.shape != original.shape or g.dtype != np.dtype('<f8') or not np.isfinite(g).all() for g in (gm, gp)):
                    raise ValueError('force-action operand changes its complete finite binary64 gradient')
                denominator = float(2*step)
                action = np.asarray((gp-gm)/denominator, dtype='<f8')
                if not np.isfinite(action).all():
                    raise ValueError('force-action subtraction or division is nonfinite')
                curvature = float(np.vdot(vector, action))/norm2
                norm = float(np.linalg.norm(action))
                orthogonal = float(np.linalg.norm(action-curvature*vector))
                xm, xp = (displaced_coordinates(original, direction, sign*step) for sign in (-1, 1))
                secant_error = float(np.max(np.abs((xp-xm)/float(2*step*BOHR_ANGSTROM)-vector)))
                midpoint = float(np.max(np.abs((xp-original)+(xm-original))))/float(2*BOHR_ANGSTROM)
                delta = None if previous_action is None else float(np.linalg.norm(action-previous_action))
                relative = None if delta is None or norm == 0 else delta/norm
                metrics = tuple(None if value is None else Decimal.from_float(value) for value in
                    (math.sqrt(norm2), norm, curvature, orthogonal, secant_error, midpoint, delta, relative))
                references = tuple(sorted((direction.identity, minus.identity, plus.identity), key=lambda pin:pin.object_id))
                digest = sha256(action.tobytes(order='C')).hexdigest()
                manifest = ArrayDatasetManifest('arrays.force-action.'+plus.fingerprint(),
                    (ArrayDatasetMember('cartesian-hessian-action', '<f8', original.shape, digest),), references)
                arrays.append((manifest, action))
            rows.append(PeriodicForceActionComparison(direction.identity, step, minus.identity, plus.identity,
                previous_step, manifest, *metrics))
            previous_step, previous_action = step, action
    return tuple(rows), tuple(arrays)


def read_periodic_force_actions(*, configs, representation, coordinate_bytes, original_results,
        native_subwork_for_result, assessor_source, readout_id):
    base = validate_configs(configs)
    if not base.FORCE_ACTIONS:
        raise ValueError('force-action reader requires its prospectively selected action protocol')
    validate_periodic_probe_model(base.original.selection, representation)
    points = control_points(base.protocol, coordinate_bytes)
    if tuple(c.point for c in configs) != points or type(original_results) is not tuple:
        raise ValueError('force-action read changes its complete original point census')
    selected = {p.identity for p in points}
    results = {}
    for result in original_results:
        exact(result, PeriodicProbeResult)
        pin = result.returned.selection
        if pin not in selected or pin in results:
            raise ValueError('force-action read repeats or substitutes an original return')
        results[pin] = result
    reports, values = [], {}
    for config in configs:
        result = results.get(config.point.identity)
        report = None
        if result is not None:
            store = native_subwork_for_result(result)
            report = _read_point(config, result, store, assessor_source,
                readout_id+'.point.'+f'{config.point.ordinal:08d}', representation=representation)
            values[config.point.point_id] = _values(report, store, include_gradient=True)
        reports.append(ControlPointReadout(config.point, report))
    comparisons, arrays = compare_force_actions(base.protocol, coordinate_bytes, points, values)
    return {'readout':PeriodicForceActionsReadout(readout_id, base.protocol, tuple(reports), comparisons),
        'reconstructed_actions':arrays}
