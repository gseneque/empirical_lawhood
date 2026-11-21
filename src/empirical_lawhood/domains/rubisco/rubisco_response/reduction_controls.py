# SPDX-License-Identifier: MPL-2.0
"""Small exact exposed controls for driven response and finite intervention.

These dimensionless systems are bounded software falsifiers. They are not a
molecular operator, a selected Rubisco supplier, or a measured cost comparison.
No Matrix production dimensions, normalization or successful thresholds enter.
"""

from dataclasses import dataclass
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact, identities
from empirical_lawhood.domains.rubisco.rubisco_response.policy_indicator import exact_vector


def _matrix(values, rows, columns):
    if type(values) is not tuple or len(values) != rows:
        raise ValueError("control matrix changes its complete row dimension")
    for row in values:
        exact_vector(row, columns)


def _qvec(values):
    return tuple(Exact.of(value) for value in values)


def _mv(matrix, vector):
    return tuple(sum((a.fraction * b for a, b in zip(row, vector, strict=True)), Fraction(0)) for row in matrix)


def _add(*vectors):
    return tuple(sum(values, Fraction(0)) for values in zip(*vectors, strict=True))


def _block(matrix, rows, columns):
    return tuple(tuple(matrix[i][j] for j in columns) for i in rows)


@dataclass(frozen=True, slots=True)
class DrivenControlStep(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/driven-control-step"
    a: tuple[tuple[Exact, ...], ...]
    b: tuple[tuple[Exact, ...], ...]
    c: tuple[tuple[Exact, ...], ...]
    d: tuple[tuple[Exact, ...], ...]

    def __post_init__(self):
        if type(self.a) is not tuple or not 1 <= len(self.a) <= 8 or type(self.b) is not tuple or not self.b:
            raise ValueError("exposed control has one through eight state coordinates")
        n, m = len(self.a), len(self.b[0])
        if not 1 <= m <= 4:
            raise ValueError("exposed control has one through four input coordinates")
        for values, rows, columns in ((self.a, n, n), (self.b, n, m), (self.c, 2, n), (self.d, 2, m)):
            _matrix(values, rows, columns)


@dataclass(frozen=True, slots=True)
class DrivenResponseControl(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/driven-response-control"
    control_id: str
    steps: tuple[DrivenControlStep, ...]
    inputs: tuple[tuple[Exact, ...], ...]
    initial_state: tuple[Exact, ...]
    sources: tuple[ObjectIdentity, ...]
    units: str = "DIMENSIONLESS_EXPOSED_CONTROL"
    clock: str = "INDEXED_DISCRETE_STEPS_NOT_PHYSICAL_TIME"
    claim_scope: str = "BOUNDED_ANALYTIC_FALSIFIER_NOT_A_MOLECULAR_SUPPLIER"

    def __post_init__(self):
        validate_stable_id(self.control_id)
        if type(self.steps) is not tuple or not 1 <= len(self.steps) <= 32:
            raise ValueError("exposed control needs its complete horizon of one through thirty-two steps")
        for row in self.steps:
            exact(row, DrivenControlStep)
        n, m = len(self.steps[0].a), len(self.steps[0].b[0])
        if any(len(row.a) != n or len(row.b[0]) != m for row in self.steps):
            raise ValueError("changing dynamics must retain their declared state and input coordinates")
        exact_vector(self.initial_state, n)
        if type(self.inputs) is not tuple or len(self.inputs) != len(self.steps):
            raise ValueError("driven control drops an input or observation checkpoint")
        for row in self.inputs:
            exact_vector(row, m)
        identities(self.sources)
        if (self.units != "DIMENSIONLESS_EXPOSED_CONTROL" or self.clock != "INDEXED_DISCRETE_STEPS_NOT_PHYSICAL_TIME"
                or self.claim_scope != "BOUNDED_ANALYTIC_FALSIFIER_NOT_A_MOLECULAR_SUPPLIER"):
            raise ValueError("analytic controls cannot supply physical units, dynamics or target justification")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.control_id, self)


@dataclass(frozen=True, slots=True)
class ControlTrajectory(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/control-trajectory"
    trajectory_id: str
    control: ObjectIdentity
    original_state: str
    states: tuple[tuple[Exact, ...], ...]
    outputs: tuple[tuple[Exact, ...], ...]

    def __post_init__(self):
        validate_stable_id(self.trajectory_id)
        exact(self.control, ObjectIdentity)
        if self.original_state not in {"AVAILABLE", "FAILED", "UNKNOWN"}:
            raise ValueError("control trajectory loses its original completion state")
        for values in (self.states, self.outputs):
            if type(values) is not tuple:
                raise ValueError("control trajectory must retain immutable complete or partial arrays")
            for row in values:
                if not row:
                    raise ValueError("a retained state or output vector cannot be empty")
                exact_vector(row, len(row))

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.trajectory_id, self)


def propagate_control(control, *, trajectory_id):
    exact(control, DrivenResponseControl)
    x = tuple(value.fraction for value in control.initial_state)
    states, outputs = [_qvec(x)], []
    for step, raw_input in zip(control.steps, control.inputs, strict=True):
        u = tuple(value.fraction for value in raw_input)
        outputs.append(_qvec(_add(_mv(step.c, x), _mv(step.d, u))))
        x = _add(_mv(step.a, x), _mv(step.b, u))
        states.append(_qvec(x))
    return ControlTrajectory(trajectory_id, control.identity, "AVAILABLE", tuple(states), tuple(outputs))


def _control_residuals(control, trajectory):
    n, horizon = len(control.initial_state), len(control.steps)
    complete = (len(trajectory.states) == horizon + 1 and len(trajectory.outputs) == horizon
        and all(len(row) == n for row in trajectory.states) and all(len(row) == 2 for row in trajectory.outputs))
    residuals = None
    if complete:
        initial = _qvec(a.fraction - b.fraction for a, b in zip(trajectory.states[0], control.initial_state, strict=True))
        dynamics, outputs = [], []
        # Independent local balance checks on retained arrays. This never calls
        # the producer, projection, elimination or a tangent propagation routine.
        for i, step in enumerate(control.steps):
            x, next_x, u, y = trajectory.states[i], trajectory.states[i + 1], control.inputs[i], trajectory.outputs[i]
            dynamics.append(_qvec(next_x[j].fraction
                - sum(step.a[j][k].fraction * x[k].fraction for k in range(n))
                - sum(step.b[j][k].fraction * u[k].fraction for k in range(len(u))) for j in range(n)))
            outputs.append(_qvec(y[j].fraction
                - sum(step.c[j][k].fraction * x[k].fraction for k in range(n))
                - sum(step.d[j][k].fraction * u[k].fraction for k in range(len(u))) for j in range(2)))
        residuals = initial, tuple(dynamics), tuple(outputs)
    balanced = residuals is not None and not any(value.fraction for row in
        (residuals[0], *residuals[1], *residuals[2]) for value in row)
    checks = (("source", trajectory.control == control.identity), ("complete-census", complete), ("local-equations", balanced))
    disposition = A.UNEVALUABLE if trajectory.original_state != "AVAILABLE" else A.SATISFIED if all(value for _, value in checks) else A.FALSIFIED
    return checks, residuals, disposition


@dataclass(frozen=True, slots=True)
class ControlTrajectoryAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/control-trajectory-assessment"
    assessment_id: str
    control: DrivenResponseControl
    trajectory: ControlTrajectory
    checks: tuple[tuple[str, bool], ...]
    residuals: tuple[tuple[Exact, ...], tuple[tuple[Exact, ...], ...], tuple[tuple[Exact, ...], ...]] | None
    disposition: A

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        exact(self.control, DrivenResponseControl)
        exact(self.trajectory, ControlTrajectory)
        if (self.checks, self.residuals, self.disposition) != _control_residuals(self.control, self.trajectory):
            raise ValueError("control assessment substitutes the independent retained-equation checks")


def assess_control_trajectory(control, trajectory, *, assessment_id):
    exact(control, DrivenResponseControl)
    exact(trajectory, ControlTrajectory)
    return ControlTrajectoryAssessment(assessment_id, control, trajectory, *_control_residuals(control, trajectory))


def _indices(control, retained):
    if (type(retained) is not tuple or not retained or retained != tuple(sorted(set(retained)))
            or any(type(i) is not int or not 0 <= i < len(control.initial_state) for i in retained)
            or len(retained) >= len(control.initial_state)):
        raise ValueError("control partition needs a strict nonempty retained subset and the full omitted complement")
    return tuple(i for i in range(len(control.initial_state)) if i not in retained)


def projected_control(control, retained, *, control_id):
    exact(control, DrivenResponseControl)
    _indices(control, retained)
    inputs = tuple(range(len(control.inputs[0])))
    rows = tuple(DrivenControlStep(_block(step.a, retained, retained), _block(step.b, retained, inputs),
        _block(step.c, (0, 1), retained), step.d) for step in control.steps)
    return DrivenResponseControl(control_id, rows, control.inputs, tuple(control.initial_state[i] for i in retained),
        tuple(sorted({*control.sources, control.identity}, key=lambda row: row.object_id)))


def frozen_control(control, *, control_id):
    exact(control, DrivenResponseControl)
    return DrivenResponseControl(control_id, (control.steps[0],) * len(control.steps), control.inputs,
        control.initial_state, tuple(sorted({*control.sources, control.identity}, key=lambda row: row.object_id)))


@dataclass(frozen=True, slots=True)
class OmittedStateContribution(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/omitted-state-contribution"
    checkpoint: int
    initial: tuple[Exact, ...]
    drive: tuple[Exact, ...]
    returned_history: tuple[Exact, ...]

    def __post_init__(self):
        if type(self.checkpoint) is not int or self.checkpoint < 0 or not self.initial:
            raise ValueError("omitted contribution needs its exact checkpoint and nonempty complement")
        for row in (self.initial, self.drive, self.returned_history):
            exact_vector(row, len(self.initial))


def eliminate_control_memory(control, retained, *, trajectory_id):
    """Exact finite history reconstruction; this is not a fast production solver."""
    exact(control, DrivenResponseControl)
    omitted = _indices(control, retained)
    r0 = tuple(control.initial_state[i].fraction for i in omitted)
    z_history = [tuple(control.initial_state[i].fraction for i in retained)]
    states, outputs, contributions = [], [], []
    inputs = tuple(tuple(value.fraction for value in row) for row in control.inputs)
    for n in range(len(control.steps) + 1):
        initial, drive, returned = r0, (Fraction(0),) * len(omitted), (Fraction(0),) * len(omitted)
        for j in range(n):
            step = control.steps[j]
            arr = _block(step.a, omitted, omitted)
            initial = _mv(arr, initial)
            drive = _add(_mv(arr, drive), _mv(_block(step.b, omitted, tuple(range(len(inputs[j])))), inputs[j]))
            returned = _add(_mv(arr, returned), _mv(_block(step.a, omitted, retained), z_history[j]))
        r = _add(initial, drive, returned)
        full = dict(zip(retained, z_history[n], strict=True)) | dict(zip(omitted, r, strict=True))
        x = tuple(full[i] for i in range(len(control.initial_state)))
        states.append(_qvec(x))
        contributions.append(OmittedStateContribution(n, _qvec(initial), _qvec(drive), _qvec(returned)))
        if n < len(control.steps):
            step, u = control.steps[n], inputs[n]
            outputs.append(_qvec(_add(_mv(step.c, x), _mv(step.d, u))))
            z_history.append(tuple(_add(_mv(step.a, x), _mv(step.b, u))[i] for i in retained))
    return ControlTrajectory(trajectory_id, control.identity, "AVAILABLE", tuple(states), tuple(outputs)), tuple(contributions)


def _direction_join(control, direction):
    exact(control, DrivenResponseControl)
    exact(direction, DrivenResponseControl)
    if (len(control.steps), len(control.initial_state), len(control.inputs[0])) != (
            len(direction.steps), len(direction.initial_state), len(direction.inputs[0])):
        raise ValueError("finite perturbation must retain every state, input, receiver and checkpoint")


def _mix(left, right, step):
    return tuple(Exact.of(a.fraction + step * b.fraction) for a, b in zip(left, right, strict=True))


def finite_perturbed_control(control, direction, step, *, control_id):
    """Affine parameter perturbation, including driving and initial preparation."""
    _direction_join(control, direction)
    exact(step, Exact)
    rows = tuple(DrivenControlStep(*(tuple(_mix(a, b, step.fraction) for a, b in zip(getattr(left, name), getattr(right, name), strict=True))
        for name in ("a", "b", "c", "d"))) for left, right in zip(control.steps, direction.steps, strict=True))
    return DrivenResponseControl(control_id, rows,
        tuple(_mix(a, b, step.fraction) for a, b in zip(control.inputs, direction.inputs, strict=True)),
        _mix(control.initial_state, direction.initial_state, step.fraction),
        tuple(sorted({*control.sources, *direction.sources, control.identity, direction.identity}, key=lambda row: row.object_id)))


def tangent_control(control, direction, *, control_id):
    """Augment exact first-order state and retain initial, input and direct terms."""
    _direction_join(control, direction)
    n, m = len(control.initial_state), len(control.inputs[0])
    if n > 4 or m > 2:
        raise ValueError("tangent control stays within the bounded exposed-control capacity")
    zeros_n, zeros_m = (Exact.of(0),) * n, (Exact.of(0),) * m
    rows = tuple(DrivenControlStep(
        tuple((*row, *zeros_n) for row in base.a) + tuple((*da, *a) for da, a in zip(delta.a, base.a, strict=True)),
        tuple((*row, *zeros_m) for row in base.b) + tuple((*db, *b) for db, b in zip(delta.b, base.b, strict=True)),
        tuple((*dc, *c) for dc, c in zip(delta.c, base.c, strict=True)),
        tuple((*dd, *d) for dd, d in zip(delta.d, base.d, strict=True)))
        for base, delta in zip(control.steps, direction.steps, strict=True))
    return DrivenResponseControl(control_id, rows,
        tuple((*u, *du) for u, du in zip(control.inputs, direction.inputs, strict=True)),
        (*control.initial_state, *direction.initial_state),
        tuple(sorted({*control.sources, *direction.sources, control.identity, direction.identity}, key=lambda row: row.object_id)))


def finite_response_remainders(control, direction, step, original, perturbed, tangent):
    """Independently check all three retained equations before finite remainders.

    The conventional approximation here is the complete first-order response of
    the same disclosed equations. No molecular comparator or speedup is claimed.
    """
    _direction_join(control, direction)
    exact(step, Exact)
    expected_finite = finite_perturbed_control(control, direction, step, control_id=perturbed.control.object_id)
    expected_tangent = tangent_control(control, direction, control_id=tangent.control.object_id)
    for model, result in ((control, original), (expected_finite, perturbed), (expected_tangent, tangent)):
        checked = assess_control_trajectory(model, result, assessment_id="assessment.finite-control." + result.trajectory_id)
        if checked.disposition is not A.SATISFIED:
            return None
    return tuple(_qvec(b.fraction - a.fraction - step.fraction * d.fraction for a, b, d in zip(y0, y1, dy, strict=True))
        for y0, y1, dy in zip(original.outputs, perturbed.outputs, tangent.outputs, strict=True))
