# SPDX-License-Identifier: MPL-2.0
"""Finite-resolution response-error frontiers, without qualification/admission.

The task uses the already committed odd response, not absolute phase-space
accuracy or a derivative divided by amplitude. Its actuator scales depend only
on the declared action and clocks. They never divide by a realised response.
All receiver coordinates, actions, panels, models and assigned roots remain in
the denominator. A frontier is descriptive development evidence; choosing a
consumer tolerance and establishing its numerical/statistical warrant are
separate operations. Original assessment/convergence records are not revised.
"""

from dataclasses import dataclass, fields
from decimal import Decimal, localcontext
import math
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import FactorEventSpec
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_strings, validate_decimal,
    validate_stable_id,
)

from .records import ACTION_ROLES, PREDICTORS, identity


@dataclass(frozen=True, slots=True)
class MatrixResponseFactorRuleCompatibility(CanonicalRecord):
    """Only admission/tracking equivalence; scalar comparison remains separate."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-frontier/factor-rule-compatibility"
    compatibility_id: str
    original: FactorEventSpec
    target: FactorEventSpec

    def __post_init__(self):
        validate_stable_id(self.compatibility_id)
        if (type(self.original) is not FactorEventSpec or type(self.target) is not FactorEventSpec
                or any(getattr(self.original, f.name) != getattr(self.target, f.name)
               for f in fields(FactorEventSpec) if f.name not in {"spec_id", "scalar_closure"})):
            raise ValueError("factor admission/tracking compatibility changes scientific criteria or clocks")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.compatibility_id, self)


@dataclass(frozen=True, slots=True)
class MatrixResponseActionScale(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-frontier/action-scale"
    role: str
    amplitude: Decimal
    force_norm: Decimal
    pulse_steps: int

    def __post_init__(self):
        if self.role not in ACTION_ROLES or type(self.pulse_steps) is not int or self.pulse_steps < 1:
            raise ValueError("response task requires its declared action role and pulse")
        for name in ("amplitude", "force_norm"):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
            if getattr(self, name) == 0:
                raise ValueError("response actuator scales must be positive")

    def scales(self, dt, horizon_steps):
        """Nominal free-actuator impulse/displacement, not a native prediction."""
        horizon = dt * horizon_steps
        pulse = dt * min(self.pulse_steps, horizon_steps)
        impulse = self.amplitude * self.force_norm * pulse
        return impulse * (horizon - pulse / 2), impulse


@dataclass(frozen=True, slots=True)
class MatrixResponseFrontierProtocol(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-frontier/protocol"
    protocol_id: str
    factor_rule: ObjectIdentity
    primary_timestep: Decimal
    horizon_steps: tuple[int, ...]
    action_scales: tuple[MatrixResponseActionScale, ...]
    receiver_gram_tolerance: Decimal
    panel_roles: tuple[str, ...] = ("COMMON_NOISE_PANEL", "INDEPENDENT_FUTURE")
    factor_rule_compatibilities: tuple[MatrixResponseFactorRuleCompatibility, ...] = ()
    estimand: str = "FINITE_DT_ODD_RESPONSE_HALF_PLUS_MINUS"
    metric: str = "MAX_POSITION_MOMENTUM_HS24_ERROR_OVER_NOMINAL_ACTUATOR_SCALE"
    aggregation: str = "MAX_ALL_PANELS_ACTIONS_AND_PRECEDING_HORIZONS_PER_WHOLE_ROOT"
    inference: str = "EXPOSED_DEVELOPMENT_FRONTIER_NO_ADMISSION_OR_QUALIFICATION"

    def __post_init__(self):
        validate_stable_id(self.protocol_id)
        for name in ("primary_timestep", "receiver_gram_tolerance"):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
            if getattr(self, name) == 0:
                raise ValueError("response frontier clocks and metric checks must be positive")
        if (not self.horizon_steps or self.horizon_steps != tuple(sorted(set(self.horizon_steps)))
                or any(type(h) is not int or h < 1 for h in self.horizon_steps)
                or tuple(a.role for a in self.action_scales) != ACTION_ROLES
                or self.panel_roles != tuple(sorted(self.panel_roles))
                or not {"COMMON_NOISE_PANEL", "INDEPENDENT_FUTURE"} <= set(self.panel_roles)
                or set(self.panel_roles) - {"COMMON_NOISE_PANEL", "INDEPENDENT_FUTURE"}
                or tuple(c.compatibility_id for c in self.factor_rule_compatibilities) !=
                   tuple(sorted({c.compatibility_id for c in self.factor_rule_compatibilities}))
                or any(c.target.identity != self.factor_rule for c in self.factor_rule_compatibilities)
                or self.estimand != "FINITE_DT_ODD_RESPONSE_HALF_PLUS_MINUS"
                or self.metric != "MAX_POSITION_MOMENTUM_HS24_ERROR_OVER_NOMINAL_ACTUATOR_SCALE"
                or self.aggregation != "MAX_ALL_PANELS_ACTIONS_AND_PRECEDING_HORIZONS_PER_WHOLE_ROOT"
                or self.inference != "EXPOSED_DEVELOPMENT_FRONTIER_NO_ADMISSION_OR_QUALIFICATION"):
            raise ValueError("response frontier changes its complete task or evidential scope")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.protocol_id, self)

    def validate_design(self, design):
        actual = tuple(sorted((MatrixResponseActionScale(a.role, a.amplitude, a.force_norm, a.pulse_steps)
                               for a in design.actions), key=lambda a: a.role))
        compatible = tuple(c for c in self.factor_rule_compatibilities if c.original == design.rule)
        if (design.rule.identity != self.factor_rule and len(compatible) != 1
                or design.view.timestep != self.primary_timestep
                or design.horizon_steps != self.horizon_steps or design.receiver_count != 48
                or actual != self.action_scales or design.normalization != "ODD_FINITE_RESPONSE_HALF_PLUS_MINUS"):
            raise ValueError("response frontier substitutes clocks, actions, receiver census or factor rule")
        return None if design.rule.identity == self.factor_rule else compatible[0].identity


@dataclass(frozen=True, slots=True)
class MatrixResponseReceiverMetric(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-frontier/receiver-metric"
    metric_id: str
    origin: ObjectIdentity
    arrays: ArtifactIdentity
    gram_error: Decimal
    phase_support_error: Decimal
    hermitian_error: Decimal

    def __post_init__(self):
        validate_stable_id(self.metric_id)
        for name in ("gram_error", "phase_support_error", "hermitian_error"):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.metric_id, self)


def assess_receiver_metric(protocol, origin, receivers):
    """Check authenticated origin arrays at the caller's bounded-array boundary.

    The caller must authenticate ``receivers`` against ``origin.arrays`` before
    invoking this numerical consumer. This is a metric check, not acquisition.
    """
    import numpy as np
    values = np.asarray(receivers)
    if values.shape != (48, 2, 2, 3, 4, 4) or values.dtype != np.dtype("complex128") or not np.isfinite(values).all():
        raise ValueError("response metric needs all48 complete finite native receivers")
    gram = np.einsum("rpsjab,tpsjab->rt", values.conj(), values)
    gram_error = float(np.linalg.norm(gram - np.eye(48)))
    phase_error = float(np.sqrt(np.linalg.norm(values[:24, 1])**2 + np.linalg.norm(values[24:, 0])**2))
    hermitian_error = float(np.linalg.norm(values - values.conj().swapaxes(-1, -2)))
    if max(gram_error, phase_error, hermitian_error) > float(protocol.receiver_gram_tolerance):
        raise ValueError("response receiver chart is not the declared orthonormal position/momentum metric")
    return MatrixResponseReceiverMetric("metric." + origin.origin_id, identity(origin),
        origin.arrays.array_artifact, Decimal(str(gram_error)), Decimal(str(phase_error)), Decimal(str(hermitian_error)))


@dataclass(frozen=True, slots=True)
class MatrixResponseFrontierCell(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-frontier/cell"
    panel_id: str
    panel_role: str
    action_id: str
    action_role: str
    horizon_step: int
    predictor: str
    position_error: Decimal | None
    momentum_error: Decimal | None
    scaled_loss: Decimal | None
    weak_receiver_count: int
    negative_receiver_count: int

    @property
    def key(self):
        return self.panel_id, self.action_id, self.horizon_step, self.predictor

    def __post_init__(self):
        for value in (self.panel_id, self.action_id):
            validate_stable_id(value)
        if (self.panel_role not in {"COMMON_NOISE_PANEL", "INDEPENDENT_FUTURE"}
                or self.action_role not in ACTION_ROLES or self.predictor not in PREDICTORS
                or type(self.horizon_step) is not int or self.horizon_step < 1
                or any(type(n) is not int or not 0 <= n <= 48 for n in
                       (self.weak_receiver_count, self.negative_receiver_count))
                or len({v is None for v in (self.position_error, self.momentum_error, self.scaled_loss)}) != 1):
            raise ValueError("response cell drops a receiver/comparator or unresolved disposition")
        for name in ("position_error", "momentum_error", "scaled_loss"):
            if getattr(self, name) is not None:
                validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))


@dataclass(frozen=True, slots=True)
class MatrixResponseHorizonLoss(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-frontier/horizon-loss"
    predictor: str
    horizon_step: int
    cumulative_loss: Decimal | None

    def __post_init__(self):
        if self.predictor not in PREDICTORS or type(self.horizon_step) is not int or self.horizon_step < 1:
            raise ValueError("response horizon loss substitutes its predictor or clock")
        if self.cumulative_loss is not None:
            validate_decimal(self.cumulative_loss, field_name="cumulative_loss", minimum=Decimal(0))


@dataclass(frozen=True, slots=True)
class MatrixResponseRootFrontier(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-frontier/root"
    frontier_id: str
    protocol: ObjectIdentity
    root_id: str
    independent_group_id: str
    stratum_id: str
    source: ObjectIdentity
    disposition: str
    origin: ObjectIdentity | None
    assessment: ObjectIdentity | None
    metric: ObjectIdentity | None
    factor_rule_compatibility: ObjectIdentity | None
    panel_census: tuple[tuple[str, str], ...]
    action_census: tuple[tuple[str, str], ...]
    horizon_steps: tuple[int, ...]
    cells: tuple[MatrixResponseFrontierCell, ...]
    horizon_losses: tuple[MatrixResponseHorizonLoss, ...]
    native_reference_pass: bool | None
    admission: str = "UNASSESSED_NO_CONSUMER_TOLERANCE_OR_NUMERICAL_ENCLOSURE"

    def __post_init__(self):
        for name in ("frontier_id", "root_id", "independent_group_id", "stratum_id"):
            validate_stable_id(getattr(self, name))
        measured = self.disposition == "MEASURED_DEVELOPMENT"
        if (self.disposition not in {"MEASURED_DEVELOPMENT", "NO_CAUSAL_ORIGIN", "OBSERVATION_UNRESOLVED", "UNKNOWN_CONTACT"}
                or self.protocol.object_schema != MatrixResponseFrontierProtocol.SCHEMA
                or self.admission != "UNASSESSED_NO_CONSUMER_TOLERANCE_OR_NUMERICAL_ENCLOSURE"
                or measured != all(v is not None for v in (self.origin, self.assessment, self.metric))
                or not measured and any(v is not None for v in (self.origin, self.assessment, self.metric))
                or measured != bool(self.cells) or measured != bool(self.horizon_losses)
                or measured != (type(self.native_reference_pass) is bool)
                or tuple(c.key for c in self.cells) != tuple(sorted({c.key for c in self.cells}))):
            raise ValueError("response frontier confuses missing origin/contact with assessed admission")
        if not measured:
            if self.panel_census or self.action_census or self.horizon_steps or self.factor_rule_compatibility is not None:
                raise ValueError("unentered response frontier invents an entered task census")
            return
        if (self.panel_census != tuple(sorted(set(self.panel_census)))
                or not {"COMMON_NOISE_PANEL", "INDEPENDENT_FUTURE"} <= {role for _, role in self.panel_census}
                or {role for _, role in self.panel_census} - {"COMMON_NOISE_PANEL", "INDEPENDENT_FUTURE"}
                or len({name for name, _ in self.panel_census}) != len(self.panel_census)
                or self.action_census != tuple(sorted(set(self.action_census)))
                or tuple(sorted(role for _, role in self.action_census)) != ACTION_ROLES
                or len({name for name, _ in self.action_census}) != 4
                or not self.horizon_steps or self.horizon_steps != tuple(sorted(set(self.horizon_steps)))
                or any(type(h) is not int or h < 1 for h in self.horizon_steps)):
            raise ValueError("response frontier changes its complete panel/action/horizon census")
        panels, actions = dict(self.panel_census), dict(self.action_census)
        expected = {(p, a, h, m) for p in panels for a in actions for h in self.horizon_steps for m in PREDICTORS}
        if ({c.key for c in self.cells} != expected
                or any(c.panel_role != panels[c.panel_id] or c.action_role != actions[c.action_id] for c in self.cells)
                or tuple((v.predictor, v.horizon_step) for v in self.horizon_losses) !=
                   tuple((m, h) for m in PREDICTORS for h in self.horizon_steps)):
            raise ValueError("response frontier omits/duplicates a complete cell or cumulative horizon loss")
        for value in self.horizon_losses:
            losses = [c.scaled_loss for c in self.cells if c.predictor == value.predictor and c.horizon_step <= value.horizon_step]
            actual = None if any(v is None for v in losses) else max(losses)
            if value.cumulative_loss != actual:
                raise ValueError("response frontier changes cumulative maximum or unresolved propagation")


def reduce_response_frontier(protocol, source, origin, assessment, metric, *, stratum_id):
    """Reduce already independently assessed scores; no producer or assessor entry."""
    compatibility = protocol.validate_design(source.design)
    if (assessment.source != identity(source) or origin.source != identity(source)
            or assessment.origin != identity(origin) or metric.origin != identity(origin)
            or metric.arrays != origin.arrays.array_artifact
            or origin.design != source.design or origin.root_id != source.root.root_id
            or origin.independent_group_id != source.root.independent_group_id or origin.clock_id != source.root.clock_id
            or max(metric.gram_error, metric.phase_support_error, metric.hermitian_error) > protocol.receiver_gram_tolerance):
        raise ValueError("response frontier substitutes its independently assessed source/origin/metric")
    panels = tuple(p for p in source.root.streams if p.role != "PREFIX")
    if tuple(sorted(p.role for p in panels)) != protocol.panel_roles:
        raise ValueError("response frontier changes its declared panel task")
    actions = {a.action_id: a for a in source.design.actions}
    expected = {(p.panel_id, p.role, a, h, r, m) for p in panels for a in actions
                for h in protocol.horizon_steps for r in range(48) for m in PREDICTORS}
    keys = {(r.panel_id, r.panel_role, r.action_id, r.horizon_step, r.receiver_index, r.predictor)
            for r in assessment.scores}
    if (len(assessment.scores) != len(expected) or keys != expected
            or assessment.requested_panels != len(panels) or assessment.requested_original_roots != 1):
        raise ValueError("response frontier lacks the complete root/panel/action/horizon/receiver/model census")
    grouped, shared = {}, {}
    for row in assessment.scores:
        shared_key = row.panel_id, row.action_id, row.horizon_step, row.receiver_index
        truth = row.actual_odd_response, row.weak_response, row.complementary_leakage
        if shared.setdefault(shared_key, truth) != truth:
            raise ValueError("response frontier changes the same native outcome across predictors")
        if row.absolute_error is not None and row.absolute_error != abs(row.signed_error):
            raise ValueError("response score changes its signed versus absolute error")
        if row.signed_error is not None:
            values = (row.predicted_odd_response, row.actual_odd_response, row.signed_error)
            if any(not math.isfinite(float(v)) for v in values):
                raise ValueError("response score exceeds its finite native arithmetic domain")
            arithmetic_margin = sum((Decimal(str(math.ulp(float(v)))) for v in values), Decimal(0)) * 2
            with localcontext() as context:
                context.prec = 60
                if abs(row.signed_error - (row.predicted_odd_response - row.actual_odd_response)) > arithmetic_margin:
                    raise ValueError("response score changes its committed prediction/native outcome difference")
        grouped.setdefault((row.panel_id, row.action_id, row.horizon_step, row.predictor), []).append(row)
    scales = {a.role: a for a in protocol.action_scales}
    cells = []
    with localcontext() as context:
        context.prec = 60
        for key, rows in sorted(grouped.items()):
            rows.sort(key=lambda r: r.receiver_index)
            action = actions[key[1]]
            if any(r.signed_error is None for r in rows):
                position = momentum = loss = None
            else:
                position = sum(r.signed_error**2 for r in rows[:24]).sqrt()
                momentum = sum(r.signed_error**2 for r in rows[24:]).sqrt()
                position_scale, momentum_scale = scales[action.role].scales(protocol.primary_timestep, key[2])
                loss = max(position / position_scale, momentum / momentum_scale)
            cells.append(MatrixResponseFrontierCell(key[0], rows[0].panel_role, key[1], action.role, key[2], key[3],
                position, momentum, loss, sum(r.weak_response for r in rows), sum(r.actual_odd_response < 0 for r in rows)))
    losses = []
    for predictor in PREDICTORS:
        for horizon in protocol.horizon_steps:
            values = [c.scaled_loss for c in cells if c.predictor == predictor and c.horizon_step <= horizon]
            losses.append(MatrixResponseHorizonLoss(predictor, horizon,
                None if any(v is None for v in values) else max(values)))
    return MatrixResponseRootFrontier("frontier." + source.root.root_id, protocol.identity,
        source.root.root_id, source.root.independent_group_id, stratum_id, identity(source), "MEASURED_DEVELOPMENT",
        identity(origin), identity(assessment), metric.identity, compatibility,
        tuple(sorted((p.panel_id, p.role) for p in panels)), tuple(sorted((a.action_id, a.role) for a in source.design.actions)),
        protocol.horizon_steps, tuple(cells), tuple(losses), assessment.native_reference_pass)


def root_frontier_census(protocol, roots, *, requested_root_ids):
    """Exact whole-root denominator and breakpoints, including unentered cases.

    Empirical crossings below report observed finite-dt loss, conditional on the
    native cross-check. They are not certified admission or population coverage.
    No asymptotic, statistical or continuum enclosure is manufactured.
    """
    require_sorted_unique_strings(requested_root_ids, field_name="requested_root_ids", allow_empty=False)
    actual = {r.root_id: r for r in roots}
    if len(actual) != len(roots) or set(actual) != set(requested_root_ids) or any(r.protocol != protocol.identity for r in roots):
        raise ValueError("response frontier census thins or substitutes its requested population")
    if len({r.independent_group_id for r in roots}) != len(roots):
        raise ValueError("nested roots cannot be counted as extra independent units")
    expected_losses = {(m, h) for m in PREDICTORS for h in protocol.horizon_steps}
    scales = {a.role: a for a in protocol.action_scales}
    allowed_compatibilities = {c.identity for c in protocol.factor_rule_compatibilities}
    for root in roots:
        if root.disposition == "MEASURED_DEVELOPMENT" and (
                root.horizon_steps != protocol.horizon_steps or len(root.horizon_losses) != len(expected_losses)
                or tuple(sorted(role for _, role in root.panel_census)) != protocol.panel_roles
                or root.factor_rule_compatibility is not None and root.factor_rule_compatibility not in allowed_compatibilities
                or {(v.predictor, v.horizon_step) for v in root.horizon_losses} != expected_losses):
            raise ValueError("response frontier omits or duplicates a whole-root model/horizon loss")
        with localcontext() as context:
            context.prec = 60
            for cell in root.cells:
                if cell.scaled_loss is not None:
                    position_scale, momentum_scale = scales[cell.action_role].scales(protocol.primary_timestep, cell.horizon_step)
                    if cell.scaled_loss != max(cell.position_error / position_scale, cell.momentum_error / momentum_scale):
                        raise ValueError("response frontier changes native metric loss or actuator units")
    findings = []
    for stratum in sorted({r.stratum_id for r in roots}):
        selected = tuple(r for r in roots if r.stratum_id == stratum)
        for predictor in PREDICTORS:
            for horizon in protocol.horizon_steps:
                values = []
                for root in selected:
                    candidates = [v.cumulative_loss for v in root.horizon_losses
                                  if v.predictor == predictor and v.horizon_step == horizon]
                    if root.disposition == "MEASURED_DEVELOPMENT" and root.native_reference_pass and len(candidates) == 1 and candidates[0] is not None:
                        values.append(candidates[0])
                findings.append({"stratum_id": stratum, "predictor": predictor, "horizon_step": horizon,
                    "requested_roots": len(selected), "crosschecked_measured_roots": len(values),
                    "no_origin_roots": sum(r.disposition == "NO_CAUSAL_ORIGIN" for r in selected),
                    "unresolved_roots": len(selected) - len(values) - sum(r.disposition == "NO_CAUSAL_ORIGIN" for r in selected),
                    "empirical_loss_breakpoints": tuple((v, sum(x <= v for x in values)) for v in sorted(set(values))),
                    "admission": "UNASSESSED", "statistical_coverage": "UNASSESSED",
                    "numerical_scope": "FINITE_DT_EMPIRICAL_CROSSCHECK_NOT_CERTIFIED_ERROR_ENCLOSURE"})
    return tuple(findings)
