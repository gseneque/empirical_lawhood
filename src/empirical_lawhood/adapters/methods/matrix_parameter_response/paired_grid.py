# SPDX-License-Identifier: MPL-2.0
"""Declared nine-setting matched design; no acquisition or role authority.

The three factors and true center are explicit operands. Future populations,
criteria, E3 payload and conditional revision remain separately frozen science.
"""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_parameter_history.records import (
    MatrixParameterAllocation, coordinate_identity, identity as history_identity,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.experimental_matching import (
    MatchedArmDesign, MatchedCoordinate, ParameterAxisScale, ParameterGrid, ParameterGridAxis, ParameterGridSetting,
)
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, validate_decimal, validate_stable_id
from empirical_lawhood.runtime.experimental_matching import validate_matched_arms, validate_parameter_grid

from .paired_records import MatrixPairedGridCell, VIEWS, grid_census

FACTORS = ('bath_temperature', 'friction_gamma', 'cross_coupling_gamma')
PHASE_GROUPS = {'DEVELOPMENT':32, 'REVISION_CALIBRATION':64, 'CONFIRMATION':64}


def _fixed(coordinate):
    c, m, p, f = coordinate, coordinate.member, coordinate.primary_view, coordinate.fine_view
    return (c.q, m.mass_x, m.mass_y, m.beta_rule, p.timestep, f.timestep,
        p.integrator, p.precision, p.time_unit, p.rng_algorithm, p.rng_version, p.stream_derivation_rule_id,
        c.clock_id, c.family_id, c.target_x, c.target_y, c.decreasing_start, c.ramp_ticks,
        c.autonomous_ticks, c.observation_ticks, c.initial_state_rule_id, c.preparation_rule_id)


def _physical(coordinate):
    return (coordinate.primary_view.bath_temperature, coordinate.primary_view.friction_gamma,
            coordinate.member.cross_coupling_gamma)


def parameter_grid_projection(grid):
    """Derive reusable grid metadata without changing historical grid bytes."""
    if type(grid) is not MatrixPairedFactorialGrid:
        raise TypeError('parameter projection requires the original typed Matrix grid')
    return ParameterGrid(grid.grid_id + '.parameter-grid',
        tuple(ParameterGridAxis(name, levels, ParameterAxisScale(scale))
            for name, levels, scale in zip(FACTORS, grid.levels, grid.axis_scales, strict=True)),
        tuple(ParameterGridSetting(identity.object_id, tuple(values)) for identity, *values in grid.coordinates))


def matched_design_projection(grid, allocation):
    """Project original complete groups; exposed source meaning remains exposed.

    The fixed-contract digest is derived from the exact existing domain tuple,
    not supplied as a proof label. Physical/start/noise checks remain owned by
    this domain and its independent history assessors. Views remain nested.
    """
    if type(grid) is not MatrixPairedFactorialGrid or type(allocation) is not MatrixParameterAllocation:
        raise TypeError('matched projection requires the original typed Matrix grid/allocation')
    allocation.__post_init__()
    if history_identity(allocation) != grid.allocation:
        raise ValueError('matched projection substitutes its original source allocation')
    by_coordinate = {coordinate_identity(c): c for c in allocation.coordinates}
    by_group = {}
    for row in allocation.roots:
        by_group.setdefault(row.root.independent_group_id, []).append(row)
    original = history_identity(allocation)
    units, roles, observations = [], [], []
    for group_id, roots in sorted(by_group.items()):
        for row in roots:
            row.__post_init__()
        coordinates = tuple(by_coordinate[row.coordinate] for row in roots)
        families = {c.family_id for c in coordinates}
        source_roles = {row.root.role for row in roots}
        if len(families) != 1 or len(source_roles) != 1:
            raise ValueError('matched whole group mixes original preparation families or source roles')
        units.append(IndependentUnit(group_id, original.object_id, next(iter(families)),
            tuple(sorted({view.view_id for c in coordinates for view in (c.primary_view, c.fine_view)})),
            allocation.exposure == 'EXPOSED_DEVELOPMENT_NONPROMOTABLE'))
        # A declared future phase cannot relabel the actual source's roles or
        # make this exposed development allocation into fresh confirmation.
        roles.append(UnitRoleAssignment(group_id, next(iter(source_roles)).value.lower()))
        for row in roots:
            coordinate = by_coordinate[row.coordinate]
            values = tuple(sorted((('fixed.physical-contract', sha256(canonical_json_bytes(_fixed(coordinate))).hexdigest()),
                *zip(FACTORS, _physical(coordinate), strict=True),
                *(('stream.' + stream.purpose, stream.effective_seed) for stream in row.streams))))
            observations.append(MatchedCoordinate(group_id, row.coordinate.object_id,
                ObjectIdentity.from_record(row.root.root_id, row), values))
    units = UnitAllocation(grid.grid_id + '.independent-units', (original,), tuple(units), tuple(roles))
    observations = tuple(sorted(observations, key=lambda row: (row.unit_id, row.arm_id)))
    design = MatchedArmDesign(grid.grid_id + '.matched-design', units.identity,
        tuple(identity.object_id for identity, *_ in grid.coordinates),
        tuple(name for name, _ in observations[0].values), tuple(sorted(FACTORS)), observations)
    return units, design


@dataclass(frozen=True, slots=True)
class MatrixPairedFactorialGrid(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-paired/nine-setting-grid'
    grid_id: str
    allocation: ObjectIdentity
    phase: str
    levels: tuple[tuple[Decimal,Decimal,Decimal], ...]
    axis_scales: tuple[str,str,str]
    coordinates: tuple[tuple[ObjectIdentity,Decimal,Decimal,Decimal], ...]
    matched_groups: tuple[tuple[str,tuple[str, ...]], ...]
    standing: str = 'UNENTERED_DECLARED_DESIGN_NO_FRESHNESS_OR_ENTRY_AUTHORITY'

    def __post_init__(self):
        validate_stable_id(self.grid_id)
        if (self.allocation.object_schema != MatrixParameterAllocation.SCHEMA
                or self.phase not in (*PHASE_GROUPS, 'EXPOSED_SOFTWARE')
                or len(self.levels) != 3 or len(self.axis_scales) != 3
                or len(self.coordinates) != 9 or not self.matched_groups
                or self.standing != 'UNENTERED_DECLARED_DESIGN_NO_FRESHNESS_OR_ENTRY_AUTHORITY'):
            raise ValueError('nine-setting grid changes complete factors, center or unentered standing')
        for levels, scale in zip(self.levels,self.axis_scales,strict=True):
            if len(levels) != 3 or scale not in ('LINEAR','LOG'):
                raise ValueError('each factor requires its prespecified linear/log axis')
            for value in levels:
                validate_decimal(value,field_name='positive factor level',minimum=Decimal(0))
                if value <= 0:
                    raise ValueError('factorial levels must be strictly positive')
        ids = tuple(row[0].object_id for row in self.coordinates)
        if (ids != tuple(sorted(set(ids))) or any(i.object_schema != 'empirical-lawhood/simulators/six-matrix-response/parameter-coordinate' for i,*_ in self.coordinates)):
            raise ValueError('grid must contain all eight corners and exactly the true center')
        validate_parameter_grid(parameter_grid_projection(self))
        groups = tuple(group for group,_ in self.matched_groups)
        roots = tuple(root for _, rows in self.matched_groups for root in rows)
        if (groups != tuple(sorted(set(groups))) or any(len(rows) != 9 or rows != tuple(sorted(set(rows))) for _,rows in self.matched_groups)
                or len(roots) != len(set(roots)) or self.phase in PHASE_GROUPS and len(groups) != PHASE_GROUPS[self.phase]):
            raise ValueError('complete matched independent groups cannot be inflated by coordinates or views')

    @property
    def requested_independent_groups(self):
        return len(self.matched_groups)

    @property
    def requested_coordinate_cases(self):
        return 9*len(self.matched_groups)

    @property
    def requested_nested_view_cells(self):
        return 2*self.requested_coordinate_cases

    def validate_allocation(self,allocation):
        if history_identity(allocation) != self.allocation:
            raise ValueError('grid substitutes actual full allocation')
        declared = tuple(sorted(((coordinate_identity(c),*_physical(c)) for c in allocation.coordinates),key=lambda row:row[0].object_id))
        groups = tuple((g,tuple(sorted(r.root.root_id for r in allocation.roots if r.root.independent_group_id == g)))
            for g in sorted({r.root.independent_group_id for r in allocation.roots}))
        if self.coordinates != declared or self.matched_groups != groups or len({_fixed(c) for c in allocation.coordinates}) != 1:
            raise ValueError('nine-setting grid changes fixed preparation, remaining physics, clock or group census')
        units, design = matched_design_projection(self, allocation)
        validate_matched_arms(design, units)
        for group,_ in groups:
            roots = tuple(r for r in allocation.roots if r.root.independent_group_id == group)
            if len({tuple((s.purpose,s.effective_seed) for s in r.streams) for r in roots}) != 1:
                raise ValueError('every group requires all nine coordinates with identical declared purpose streams')

    def validate_transfer_reserve(self,allocation,reservation):
        """A prospective caller must supply the actual untouched E6 reservation."""
        self.validate_allocation(allocation)
        protected = {r.physical_parameters for r in reservation.regimes}
        for c in allocation.coordinates:
            m,p = c.member,c.primary_view
            physical = (m.mass_x,m.mass_y,m.cross_coupling_gamma,m.beta_rule,p.bath_temperature,
                p.friction_gamma,c.target_x,c.target_y)
            if physical in protected:
                raise ValueError('E4 grid consumes an actual protected transfer regime')

    def unentered_census(self,allocation):
        self.validate_allocation(allocation)
        cells = tuple(MatrixPairedGridCell('cell.'+r.root.root_id+'.'+view.lower(),r.root.root_id,
            r.root.independent_group_id,r.coordinate,view,'UNENTERED') for r in allocation.roots for view in VIEWS)
        return grid_census(allocation,cells,grid_id=self.grid_id+'.census')


def declare_grid(allocation,*,grid_id,phase,levels,axis_scales):
    groups = tuple((g,tuple(sorted(r.root.root_id for r in allocation.roots if r.root.independent_group_id == g)))
        for g in sorted({r.root.independent_group_id for r in allocation.roots}))
    result = MatrixPairedFactorialGrid(grid_id,history_identity(allocation),phase,levels,axis_scales,
        tuple(sorted(((coordinate_identity(c),*_physical(c)) for c in allocation.coordinates),key=lambda row:row[0].object_id)),groups)
    result.validate_allocation(allocation)
    return result
