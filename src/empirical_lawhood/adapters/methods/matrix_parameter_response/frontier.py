# SPDX-License-Identifier: MPL-2.0
"""Parameter-specific finite-dt response frontiers and whole matched groups.

The actuator scales and 24+24 receiver norms are the existing response task
mathematics. New joins retain each coordinate and clock; matched coordinates
are never promoted to additional independent roots or an iid coverage claim.
"""

from dataclasses import dataclass
from decimal import Decimal, localcontext
import math
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_response.records import ACTION_ROLES, PREDICTORS, SIGNS
from empirical_lawhood.adapters.methods.matrix_factor_response.response_frontier import (
    MatrixResponseActionScale, MatrixResponseFrontierCell, MatrixResponseHorizonLoss,
    assess_receiver_metric,
)
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_stable_id

from .records import (
    MatrixParameterResponseAllocation, MatrixParameterResponseAssessment,
    MatrixParameterResponseOrigin, MatrixParameterResponseSource, identity,
)


@dataclass(frozen=True, slots=True)
class MatrixParameterFrontierProtocol(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-response/frontier-protocol'
    protocol_id: str
    coordinate: ObjectIdentity
    factor_rule: ObjectIdentity
    history_view: ObjectIdentity
    future_view: ObjectIdentity
    primary_timestep: Decimal
    horizon_steps: tuple[int, ...]
    action_scales: tuple[MatrixResponseActionScale, ...]
    action_census: tuple[tuple[str, str], ...]
    receiver_gram_tolerance: Decimal
    estimand: str = 'FINITE_DT_ODD_RESPONSE_HALF_PLUS_MINUS'
    metric: str = 'MAX_POSITION_MOMENTUM_HS24_ERROR_OVER_NOMINAL_ACTUATOR_SCALE'
    inference: str = 'EXPOSED_MATCHED_GROUP_DESCRIPTION_NO_IID_COVERAGE_OR_QUALIFICATION'

    def __post_init__(self):
        validate_stable_id(self.protocol_id)
        for name in ('primary_timestep', 'receiver_gram_tolerance'):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
            if getattr(self, name) == 0:
                raise ValueError('parameter frontier clock/metric tolerances must be positive')
        if (not self.horizon_steps or self.horizon_steps != tuple(sorted(set(self.horizon_steps)))
                or any(type(h) is not int or h < 1 for h in self.horizon_steps)
                or tuple(a.role for a in self.action_scales) != ACTION_ROLES
                or self.action_census != tuple(sorted(set(self.action_census)))
                or len({a for a, _ in self.action_census}) != 4
                or tuple(sorted(role for _, role in self.action_census)) != ACTION_ROLES
                or self.estimand != 'FINITE_DT_ODD_RESPONSE_HALF_PLUS_MINUS'
                or self.metric != 'MAX_POSITION_MOMENTUM_HS24_ERROR_OVER_NOMINAL_ACTUATOR_SCALE'
                or self.inference != 'EXPOSED_MATCHED_GROUP_DESCRIPTION_NO_IID_COVERAGE_OR_QUALIFICATION'):
            raise ValueError('parameter frontier changes its physical task or descriptive standing')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.protocol_id, self)

    @property
    def physical_horizons(self):
        return tuple(self.primary_timestep * h for h in self.horizon_steps)

    def validate_design(self, design):
        c = design.coordinate
        scales = tuple(sorted((MatrixResponseActionScale(a.role, a.amplitude, a.force_norm, a.pulse_steps)
                               for a in design.actions), key=lambda a: a.role))
        if (coordinate_identity(c) != self.coordinate or design.rule.identity != self.factor_rule
                or ObjectIdentity.from_record(c.primary_view.view_id, c.primary_view) != self.history_view
                or ObjectIdentity.from_record(design.view.view_id, design.view) != self.future_view
                or design.view.timestep != self.primary_timestep or design.horizon_steps != self.horizon_steps
                or scales != self.action_scales or design.receiver_count != 48):
            raise ValueError('parameter frontier substitutes exact coordinate/rule/native views/task')
        if tuple(sorted((a.action_id, a.role) for a in design.actions)) != self.action_census:
            raise ValueError('parameter frontier substitutes literal native action IDs')


def protocol_for_source(source, *, protocol_id):
    """Make an exposed task projection; caller freezes it before later outcomes."""
    if type(source) is not MatrixParameterResponseSource:
        raise ValueError('parameter frontier protocol requires its actual typed source')
    d = source.design
    return MatrixParameterFrontierProtocol(protocol_id, coordinate_identity(d.coordinate), d.rule.identity,
        ObjectIdentity.from_record(d.coordinate.primary_view.view_id, d.coordinate.primary_view),
        ObjectIdentity.from_record(d.view.view_id, d.view), d.view.timestep, d.horizon_steps,
        tuple(sorted((MatrixResponseActionScale(a.role, a.amplitude, a.force_norm, a.pulse_steps)
                      for a in d.actions), key=lambda a: a.role)),
        tuple(sorted((a.action_id, a.role) for a in d.actions)), d.instrument_reference_tolerance)


@dataclass(frozen=True, slots=True)
class MatrixParameterRootFrontier(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-response/root-frontier'
    frontier_id: str
    protocol: ObjectIdentity
    coordinate: ObjectIdentity
    history_view: ObjectIdentity
    future_view: ObjectIdentity
    root_id: str
    independent_group_id: str
    stratum_id: str
    source: ObjectIdentity
    origin: ObjectIdentity
    assessment: ObjectIdentity
    metric: ObjectIdentity
    origin_tick: int
    cutoff: Decimal
    primary_timestep: Decimal
    horizon_steps: tuple[int, ...]
    physical_horizons: tuple[Decimal, ...]
    panel_census: tuple[tuple[str, str], ...]
    action_census: tuple[tuple[str, str], ...]
    cells: tuple[MatrixResponseFrontierCell, ...]
    horizon_losses: tuple[MatrixResponseHorizonLoss, ...]
    native_reference_pass: bool
    numerical_convergence: str = 'UNASSESSED'
    admission: str = 'UNASSESSED_NO_CONSUMER_TOLERANCE_OR_NUMERICAL_ENCLOSURE'

    def __post_init__(self):
        for name in ('frontier_id', 'root_id', 'independent_group_id', 'stratum_id'):
            validate_stable_id(getattr(self, name))
        for name in ('cutoff', 'primary_timestep'):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
        if self.primary_timestep == 0:
            raise ValueError('parameter frontier physical timestep is not positive')
        if (self.protocol.object_schema != MatrixParameterFrontierProtocol.SCHEMA
                or self.source.object_schema != MatrixParameterResponseSource.SCHEMA
                or type(self.origin_tick) is not int or self.origin_tick < 0
                or self.cutoff != self.primary_timestep * self.origin_tick
                or self.physical_horizons != tuple(self.primary_timestep * h for h in self.horizon_steps)
                or self.panel_census != tuple(sorted(set(self.panel_census))) or len(self.panel_census) != 2
                or tuple(sorted(role for _, role in self.panel_census)) != ('COMMON_NOISE_PANEL', 'INDEPENDENT_FUTURE')
                or self.action_census != tuple(sorted(set(self.action_census))) or len(self.action_census) != 4
                or tuple(sorted(role for _, role in self.action_census)) != ACTION_ROLES
                or self.horizon_steps != tuple(sorted(set(self.horizon_steps))) or not self.horizon_steps
                or any(type(h) is not int or h < 1 for h in self.horizon_steps)
                or tuple(c.key for c in self.cells) != tuple(sorted({c.key for c in self.cells}))
                or type(self.native_reference_pass) is not bool or self.numerical_convergence != 'UNASSESSED'
                or self.admission != 'UNASSESSED_NO_CONSUMER_TOLERANCE_OR_NUMERICAL_ENCLOSURE'):
            raise ValueError('parameter frontier loses exact coordinate/clocks/negative scientific standing')
        expected = {(p, a, h, m) for p, _ in self.panel_census for a, _ in self.action_census
                    for h in self.horizon_steps for m in PREDICTORS}
        if ({c.key for c in self.cells} != expected
                or tuple((v.predictor, v.horizon_step) for v in self.horizon_losses) !=
                   tuple((m, h) for m in PREDICTORS for h in self.horizon_steps)):
            raise ValueError('parameter frontier omits complete cell/model/horizon denominator')
        panels, actions = dict(self.panel_census), dict(self.action_census)
        if any(c.panel_role != panels[c.panel_id] or c.action_role != actions[c.action_id] for c in self.cells):
            raise ValueError('parameter frontier changes physical action or panel labels')
        for value in self.horizon_losses:
            losses = [c.scaled_loss for c in self.cells if c.predictor == value.predictor and c.horizon_step <= value.horizon_step]
            expected_loss = None if any(v is None for v in losses) else max(losses)
            if value.cumulative_loss != expected_loss:
                raise ValueError('parameter frontier hides unresolved or earlier larger response loss')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.frontier_id, self)


def reduce_parameter_frontier(protocol, source, origin, assessment, receivers, *, stratum_id):
    """Reduce independently assessed scores using unchanged nominal HS24 units."""
    if (type(protocol) is not MatrixParameterFrontierProtocol or type(source) is not MatrixParameterResponseSource
            or type(origin) is not MatrixParameterResponseOrigin or type(assessment) is not MatrixParameterResponseAssessment):
        raise ValueError('parameter frontier requires its own exact typed source/assessment edition')
    protocol.validate_design(source.design)
    metric = assess_receiver_metric(protocol, origin, receivers)
    if (origin.source != identity(source.causal) or origin.design != source.design
            or assessment.source != identity(source) or assessment.origin != identity(origin)
            or origin.root_id != source.root.root_id or origin.independent_group_id != source.root.independent_group_id
            or origin.clock_id != source.root.clock_id):
        raise ValueError('parameter frontier changes independently assessed public/private source or original group')
    panels = source.root.streams
    actions = {a.action_id: a for a in source.design.actions}
    expected = {(p.panel_id, p.role, a, h, r, m) for p in panels for a in actions
                for h in protocol.horizon_steps for r in range(48) for m in PREDICTORS}
    keys = {(s.panel_id, s.panel_role, s.action_id, s.horizon_step, s.receiver_index, s.predictor)
            for s in assessment.scores}
    if len(assessment.scores) != len(expected) or keys != expected:
        raise ValueError('parameter frontier thins complete panel/action/horizon/48 receiver/model scores')
    grouped, shared = {}, {}
    for row in assessment.scores:
        shared_key = row.panel_id, row.action_id, row.horizon_step, row.receiver_index
        truth = row.actual_odd_response, row.weak_response, row.complementary_leakage
        if shared.setdefault(shared_key, truth) != truth:
            raise ValueError('parameter frontier substitutes native outcome across comparators')
        if row.absolute_error is not None and row.absolute_error != abs(row.signed_error):
            raise ValueError('parameter frontier changes signed versus absolute response error')
        if row.signed_error is not None:
            values = row.predicted_odd_response, row.actual_odd_response, row.signed_error
            if any(not math.isfinite(float(v)) for v in values):
                raise ValueError('parameter frontier scores exceed finite native arithmetic')
            margin = sum((Decimal(str(math.ulp(float(v)))) for v in values), Decimal(0)) * 2
            with localcontext() as context:
                context.prec = 60
                if abs(row.signed_error - (row.predicted_odd_response - row.actual_odd_response)) > margin:
                    raise ValueError('parameter frontier changes sealed prediction/native signed difference')
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
            losses.append(MatrixResponseHorizonLoss(predictor, horizon, None if any(v is None for v in values) else max(values)))
    return MatrixParameterRootFrontier('frontier.' + source.root.root_id, protocol.identity, protocol.coordinate,
        protocol.history_view, protocol.future_view, source.root.root_id, source.root.independent_group_id,
        stratum_id, identity(source), identity(origin), identity(assessment), metric.identity, origin.design.origin_tick,
        origin.design.cutoff, protocol.primary_timestep, protocol.horizon_steps, protocol.physical_horizons,
        tuple(sorted((p.panel_id, p.role) for p in panels)), tuple(sorted((a.action_id, a.role) for a in source.design.actions)),
        tuple(cells), tuple(losses), assessment.native_reference_pass)


@dataclass(frozen=True, slots=True)
class MatrixParameterFrontierCase(CanonicalRecord):
    """Every requested original case, including all24 unentered/unknown slots."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-response/frontier-case'
    root_id: str
    independent_group_id: str
    coordinate: ObjectIdentity
    history_view: ObjectIdentity
    future_view: ObjectIdentity
    source_state: str
    disposition: str
    branches: tuple[tuple[str, str], ...]
    frontier: MatrixParameterRootFrontier | None

    def __post_init__(self):
        for value in (self.root_id, self.independent_group_id):
            validate_stable_id(value)
        states = {'SUCCEEDED', 'FAILED', 'UNKNOWN', 'BEGUN', 'NOT_ENTERED'}
        if (self.disposition not in {'MEASURED_DEVELOPMENT', 'NO_CAUSAL_ORIGIN', 'REFUSED', 'UNKNOWN', 'NOT_ENTERED'}
                or self.source_state not in {'COMPLETED', 'ABSENT', 'FAILED', 'UNKNOWN', 'BEGUN', 'NOT_ENTERED'}
                or len(self.branches) != 24 or self.branches != tuple(sorted(set(self.branches)))
                or len({b for b, _ in self.branches}) != 24 or any(s not in states for _, s in self.branches)
                or (self.frontier is not None) != (self.disposition == 'MEASURED_DEVELOPMENT')):
            raise ValueError('parameter case drops source/native missing or uncertain denominator')
        if self.frontier is not None:
            f = self.frontier
            if ((self.root_id, self.independent_group_id, self.coordinate, self.history_view, self.future_view) !=
                    (f.root_id, f.independent_group_id, f.coordinate, f.history_view, f.future_view)
                    or self.source_state != 'COMPLETED' or any(s != 'SUCCEEDED' for _, s in self.branches)):
                raise ValueError('parameter case substitutes measured coordinate/group or native completion')
            expected = {f'{p}.{a}.{sign.lower()}' for p, _ in f.panel_census for a, _ in f.action_census for sign in SIGNS}
            if {b for b, _ in self.branches} != expected:
                raise ValueError('parameter case changes all24 named measured native slots')
        elif self.disposition in {'NO_CAUSAL_ORIGIN', 'NOT_ENTERED'} and any(s != 'NOT_ENTERED' for _, s in self.branches):
            raise ValueError('parameter unentered/no-origin case invents a native contact')
        if self.disposition == 'NO_CAUSAL_ORIGIN' and self.source_state != 'COMPLETED':
            raise ValueError('parameter missing source cannot supply an assessed no-origin conclusion')


@dataclass(frozen=True, slots=True)
class MatrixParameterGroupCensus(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-response/group-census'
    census_id: str
    allocation: ObjectIdentity
    requested_root_ids: tuple[str, ...]
    cases: tuple[MatrixParameterFrontierCase, ...]
    independent_groups: tuple[tuple[str, tuple[str, ...]], ...]
    physical_horizons: tuple[Decimal, ...]
    protocols: tuple[MatrixParameterFrontierProtocol, ...]
    group_losses: tuple[tuple[str, str, Decimal, Decimal | None], ...]
    inference: str = 'MATCHED_COORDINATES_ONE_ORIGINAL_GROUP_NO_IID_COVERAGE_OR_QUALIFICATION'

    def __post_init__(self):
        validate_stable_id(self.census_id)
        actual = tuple(c.root_id for c in self.cases)
        groups = tuple((g, tuple(c.root_id for c in self.cases if c.independent_group_id == g))
                       for g in sorted({c.independent_group_id for c in self.cases}))
        expected_keys = {(g, m, h) for g, _ in groups for m in PREDICTORS for h in self.physical_horizons}
        if (self.allocation.object_schema != MatrixParameterResponseAllocation.SCHEMA
                or actual != self.requested_root_ids or actual != tuple(sorted(set(actual)))
                or self.independent_groups != groups or not self.physical_horizons
                or self.physical_horizons != tuple(sorted(set(self.physical_horizons)))
                or tuple(p.protocol_id for p in self.protocols) != tuple(sorted({p.protocol_id for p in self.protocols}))
                or not self.protocols or any(p.physical_horizons != self.physical_horizons for p in self.protocols)
                or tuple((g, m, h) for g, m, h, _ in self.group_losses) != tuple(sorted(expected_keys))
                or self.inference != 'MATCHED_COORDINATES_ONE_ORIGINAL_GROUP_NO_IID_COVERAGE_OR_QUALIFICATION'):
            raise ValueError('parameter census thins original groups or invents iid coverage')
        requested = {(p.coordinate, p.history_view, p.future_view): p for p in self.protocols}
        if len(requested) != len(self.protocols) or set(requested) != {
                (c.coordinate, c.history_view, c.future_view) for c in self.cases}:
            raise ValueError('parameter census changes its complete requested coordinate/native-view task map')
        for case in self.cases:
            p = requested[(case.coordinate, case.history_view, case.future_view)]
            if case.frontier is not None and case.frontier.protocol != p.identity:
                raise ValueError('parameter census substitutes measured case task protocol')
            if case.frontier is not None:
                scales = {a.role: a for a in p.action_scales}
                with localcontext() as context:
                    context.prec = 60
                    for cell in case.frontier.cells:
                        if cell.scaled_loss is not None:
                            qscale, pscale = scales[cell.action_role].scales(p.primary_timestep, cell.horizon_step)
                            if cell.scaled_loss != max(cell.position_error / qscale, cell.momentum_error / pscale):
                                raise ValueError('parameter census changes HS24 metric loss or nominal actuator units')
        for group, predictor, physical, loss in self.group_losses:
            values = []
            for case in self.cases:
                if case.independent_group_id != group:
                    continue
                f = case.frontier
                if f is None or not f.native_reference_pass:
                    values.append(None)
                else:
                    index = f.physical_horizons.index(physical)
                    values.append(next(v.cumulative_loss for v in f.horizon_losses
                                       if v.predictor == predictor and v.horizon_step == f.horizon_steps[index]))
            if loss != (None if any(v is None for v in values) else max(values)):
                raise ValueError('parameter census hides unresolved coordinate or changes whole-group maximum')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.census_id, self)


def group_census(allocation, cases, *, census_id, physical_horizons, protocols):
    """Complete matched-group maxima; absent/unresolved cases keep a None bound."""
    if type(allocation) is not MatrixParameterResponseAllocation:
        raise ValueError('parameter group census requires exact complete future allocation')
    cases = tuple(sorted(cases, key=lambda c: c.root_id))
    expected_roots = tuple(r.root_id for r in allocation.roots)
    if tuple(c.root_id for c in cases) != expected_roots:
        raise ValueError('parameter group census loses an original requested coordinate/root')
    coordinates = {coordinate_identity(c): c for c in allocation.original_allocation.coordinates}
    protocols = tuple(sorted(protocols, key=lambda p: p.protocol_id))
    tasks = {(p.coordinate, p.history_view, p.future_view): p for p in protocols}
    for case, root in zip(cases, allocation.roots, strict=True):
        original = next(r for r in allocation.original_allocation.roots if r.root.root_id == root.root_id)
        coordinate = coordinates[original.coordinate]
        if (type(case) is not MatrixParameterFrontierCase or case.independent_group_id != root.independent_group_id
                or case.coordinate != original.coordinate
                or case.history_view != ObjectIdentity.from_record(coordinate.primary_view.view_id, coordinate.primary_view)):
            raise ValueError('parameter group census substitutes original coordinate/group/history view')
        key = case.coordinate, case.history_view, case.future_view
        if key not in tasks:
            raise ValueError('parameter group census invents an unselected future-view task')
        expected_branches = {f'{p.panel_id}.{a}.{sign.lower()}' for p in root.streams
                             for a, _ in tasks[key].action_census for sign in SIGNS}
        if {b for b, _ in case.branches} != expected_branches:
            raise ValueError('parameter group census changes allocated complete24 action/panel/sign slots')
        if case.frontier is not None and case.frontier.physical_horizons != physical_horizons:
            raise ValueError('parameter group contrast changes common physical horizon menu')
    groups = tuple((g, tuple(c.root_id for c in cases if c.independent_group_id == g))
                   for g in sorted({c.independent_group_id for c in cases}))
    losses = []
    for group, roots in groups:
        selected = tuple(c for c in cases if c.root_id in roots)
        for predictor in PREDICTORS:
            for physical in physical_horizons:
                values = []
                for case in selected:
                    frontier = case.frontier
                    if frontier is None or not frontier.native_reference_pass:
                        values.append(None)
                    else:
                        index = frontier.physical_horizons.index(physical)
                        step = frontier.horizon_steps[index]
                        values.append(next(v.cumulative_loss for v in frontier.horizon_losses
                                           if v.predictor == predictor and v.horizon_step == step))
                losses.append((group, predictor, physical, None if any(v is None for v in values) else max(values)))
    return MatrixParameterGroupCensus(census_id, identity(allocation), expected_roots, cases, groups,
                                      physical_horizons, protocols, tuple(sorted(losses, key=lambda v: v[:3])))
