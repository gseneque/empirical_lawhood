"""Additive parameter-coordinate and supplied-innovation paired history step.

Coordinate labels declare physical operands; they do not allocate independent
roots, admit scientific evidence or authorize acquisition. Old history records,
wrappers, RNG operation order and fixed1024/2048 contracts remain unchanged.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

import numpy as np

from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_stable_id

from .contracts import MatrixIntegratorKind, SixMatrixResponseModelFamilyMember, SixMatrixResponseNumericalView
from .history_preparation import FOUR_FAMILY_PREPARATION_IDS, four_family_preparation_couplings
from .model import ideal_state
from .parameter_derivatives import matrix, parameters
from .shooting import brownian_bridge_split
from .simulation import baoab_step_with_hermitian_noise

INITIAL_RULE_ID = 'matrix-parameter-q2.four-family-initial.v1'
PREPARATION_RULE_ID = 'matrix-parameter-q2.four-family-coupling.v1'
IMPLEMENTATION_ID = 'six-matrix-q2.parameter-paired-history.v1'


@dataclass(frozen=True, slots=True)
class MatrixParameterCoordinate(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/six-matrix-response/parameter-coordinate'
    VERSION: ClassVar[str] = '1.0.0'
    coordinate_id: str
    q: int
    member: SixMatrixResponseModelFamilyMember
    primary_view: SixMatrixResponseNumericalView
    fine_view: SixMatrixResponseNumericalView
    clock_id: str
    family_id: str
    target_x: Decimal
    target_y: Decimal
    decreasing_start: Decimal
    ramp_ticks: int
    autonomous_ticks: int
    observation_ticks: tuple[int, ...]
    initial_state_rule_id: str
    preparation_rule_id: str

    def __post_init__(self):
        for name in ('coordinate_id','clock_id'):
            validate_stable_id(getattr(self,name))
        if (type(self.q) is not int or self.q != 2 or self.family_id not in FOUR_FAMILY_PREPARATION_IDS
                or self.initial_state_rule_id != INITIAL_RULE_ID or self.preparation_rule_id != PREPARATION_RULE_ID):
            raise ValueError('parameter coordinate changes its q=2 family/initial/preparation convention')
        if (type(self.member) is not SixMatrixResponseModelFamilyMember
                or type(self.primary_view) is not SixMatrixResponseNumericalView
                or type(self.fine_view) is not SixMatrixResponseNumericalView):
            raise TypeError('parameter coordinate requires original typed positive-domain member/views')
        for name in ('target_x','target_y','decreasing_start'):
            validate_decimal(getattr(self,name),field_name=name,minimum=Decimal(0))
        if (type(self.ramp_ticks) is not int or self.ramp_ticks < 1
                or type(self.autonomous_ticks) is not int or self.autonomous_ticks < 0
                or type(self.observation_ticks) is not tuple or any(type(t) is not int for t in self.observation_ticks)
                or tuple(sorted(set(self.observation_ticks))) != self.observation_ticks
                or not self.observation_ticks or self.observation_ticks[0] != 0
                or self.observation_ticks[-1] != self.total_ticks):
            raise ValueError('parameter coordinate requires its complete declared physical observation clock')
        left,right = self.primary_view,self.fine_view
        if (left.view_id == right.view_id or left.timestep != 2*right.timestep
                or left.integrator is not MatrixIntegratorKind.BAOAB_UNDERDAMPED_LANGEVIN
                or right.integrator is not MatrixIntegratorKind.BAOAB_UNDERDAMPED_LANGEVIN
                or any(getattr(left,n) != getattr(right,n) for n in (
                    'friction_gamma','bath_temperature','time_unit','precision','rng_algorithm','rng_version','stream_derivation_rule_id'))):
            raise ValueError('parameter coordinate changes physical conditions across primary/half views')

    @property
    def total_ticks(self):
        return self.ramp_ticks+self.autonomous_ticks

    def physical_time(self, tick, *, refinement=1):
        if (type(refinement) is not int or refinement not in (1,2) or type(tick) is not int
                or not 0 <= tick <= self.total_ticks*refinement):
            raise ValueError('parameter clock is outside its declared view/source')
        return self.primary_view.timestep*Decimal(tick)/refinement

    def couplings(self, tick, *, refinement=1):
        self.physical_time(tick,refinement=refinement)
        return four_family_preparation_couplings(self.family_id,tick,ramp_steps=self.ramp_ticks,
            integrator_multiplier=refinement,target_x=float(self.target_x),target_y=float(self.target_y),
            decreasing_coupling_start=float(self.decreasing_start))


def initial_parameter_state(coordinate):
    decreasing = coordinate.family_id == FOUR_FAMILY_PREPARATION_IDS[1]
    alpha = float(coordinate.decreasing_start) if decreasing else 0.
    return ideal_state(q=2,alpha_tilde_x=alpha,alpha_tilde_y=alpha,
        constitution='11' if decreasing else '00')


def split_parameter_innovations(coordinate, coarse_noise, bridge_noise):
    """Weighted OU conditioning with actual friction and physical coarse dt."""
    matrix(coarse_noise,'coarse innovation')
    matrix(bridge_noise,'bridge innovation')
    decay = float(np.exp(-float(coordinate.primary_view.friction_gamma)*float(coordinate.primary_view.timestep)/2))
    return brownian_bridge_split(coarse_noise=coarse_noise,bridge_noise=bridge_noise,half_decay=decay)


def advance_parameter_pair(primary, fine, *, coordinate, coarse_step, coarse_noise, bridge_noise,
        primary_cache=None, fine_cache=None):
    """One paired step, no RNG or acquisition; both schedule gradient locations."""
    parameters(primary,coordinate.member)
    parameters(fine,coordinate.member)
    if (type(coarse_step) is not int or not 1 <= coarse_step <= coordinate.total_ticks
            or primary.step_index != coarse_step-1 or fine.step_index != 2*(coarse_step-1)
            or (primary.alpha_tilde_x,primary.alpha_tilde_y) != coordinate.couplings(primary.step_index)
            or (fine.alpha_tilde_x,fine.alpha_tilde_y) != coordinate.couplings(fine.step_index,refinement=2)):
        raise ValueError('parameter paired step changes physical state/source/schedule clock')
    halves = split_parameter_innovations(coordinate,coarse_noise,bridge_noise)
    def advance(state,tick,view,refinement,noise,cache):
        x,y = coordinate.couplings(tick,refinement=refinement)
        return baoab_step_with_hermitian_noise(state,member=coordinate.member,numerical_view=view,
            next_alpha_tilde_x=x,next_alpha_tilde_y=y,standardized_noise=noise,gradient_cache=cache)
    primary = advance(primary,coarse_step,coordinate.primary_view,1,coarse_noise,primary_cache)
    first = advance(fine,2*coarse_step-1,coordinate.fine_view,2,halves[0],fine_cache)
    fine = advance(first,2*coarse_step,coordinate.fine_view,2,halves[1],fine_cache)
    return primary,first,fine
