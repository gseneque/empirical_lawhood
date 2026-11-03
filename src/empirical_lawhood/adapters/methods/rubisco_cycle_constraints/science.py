# SPDX-License-Identifier: MPL-2.0
"""A declared gas-branch countermodel; no inferred biochemical microscopic rates.

Gas-ready X binds gas to C, C reversibly forms P, and P releases product to X:
X + gas <-> C <-> P -> X + product. RuBP/enolization, activation and product
concentrations are held fixed. This coarse-grained topology investigates when
downstream-release cancellation holds; it is not the full Witzel/Cummins model.
The source papers retain their own enolization, reverse and inhibitor steps.
"""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from typing import ClassVar

from empirical_lawhood.kernel.serialization import CanonicalRecord

D = Decimal


def _positive(value: Decimal, field: str, *, zero_allowed: bool = False) -> None:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError(f'{field} must be an exact finite Decimal')
    if value < 0 or (value == 0 and not zero_allowed):
        raise ValueError(f'{field} must be positive' if not zero_allowed else f'{field} must be nonnegative')


@dataclass(frozen=True, slots=True)
class BranchRates(CanonicalRecord):
    """Hypothetical conditional rates; association in uM^-1 s^-1, others s^-1."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-cycle-constraints/branch-rates'
    association_um_inv_s_inv: Decimal
    gas_dissociation_s_inv: Decimal
    forward_product_s_inv: Decimal
    reverse_product_s_inv: Decimal
    release_s_inv: Decimal

    def __post_init__(self) -> None:
        _positive(self.association_um_inv_s_inv, 'association')
        _positive(self.gas_dissociation_s_inv, 'gas dissociation', zero_allowed=True)
        _positive(self.forward_product_s_inv, 'forward product formation')
        _positive(self.reverse_product_s_inv, 'reverse product formation', zero_allowed=True)
        _positive(self.release_s_inv, 'release')


@dataclass(frozen=True, slots=True)
class BranchObservables(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-cycle-constraints/branch-observables'
    saturated_turnover_s_inv: Decimal
    gas_michaelis_um: Decimal
    catalytic_efficiency_um_inv_s_inv: Decimal
    reverse_capture_ratio: Decimal
    formation_release_ratio: Decimal


def branch_observables(rates: BranchRates) -> BranchObservables:
    """Derive observables by eliminating C/P under the stated steady state."""
    BranchRates(*(
        rates.association_um_inv_s_inv, rates.gas_dissociation_s_inv,
        rates.forward_product_s_inv, rates.reverse_product_s_inv, rates.release_s_inv,
    ))
    kon, off, a, b, r = (
        rates.association_um_inv_s_inv, rates.gas_dissociation_s_inv,
        rates.forward_product_s_inv, rates.reverse_product_s_inv, rates.release_s_inv,
    )
    with localcontext() as ctx:
        ctx.prec = 50
        denominator = a + b + r
        turnover = a * r / denominator
        affinity = (off * (b + r) + a * r) / (kon * denominator)
        efficiency = kon * a * r / (off * (b + r) + a * r)
        u = off * b / (r * (off + a))
        v = (a + b) / r
    return BranchObservables(turnover, affinity, efficiency, u, v)


def finite_gas_flux(rates: BranchRates, gas_um: Decimal) -> Decimal:
    """Product-forming events per site; carboxylation stoichiometry is not doubled."""
    _positive(gas_um, 'gas concentration', zero_allowed=True)
    observable = branch_observables(rates)
    with localcontext() as ctx:
        ctx.prec = 50
        return observable.saturated_turnover_s_inv * gas_um / (observable.gas_michaelis_um + gas_um)


def realize_conditional_branch(
    *, turnover: Decimal, catalytic_efficiency: Decimal,
    formation_release_ratio: Decimal, reverse_capture_ratio: Decimal,
) -> BranchRates:
    """Construct one mathematical witness for a declared latent scenario.

    The construction proves compatibility of this topology with supplied macro
    observables; it does not estimate an enzyme's microscopic rates. Infinitely
    many other witnesses exist. Zero reverse capture uses zero gas dissociation,
    an allowed boundary of the declared model rather than a measured process.
    """
    for value, name in (
        (turnover, 'turnover'), (catalytic_efficiency, 'catalytic efficiency'),
        (formation_release_ratio, 'formation/release ratio'),
    ):
        _positive(value, name)
    _positive(reverse_capture_ratio, 'reverse-capture ratio', zero_allowed=True)
    v, u = formation_release_ratio, reverse_capture_ratio
    if u >= v:
        raise ValueError('reverse capture must be strictly below formation/release')
    with localcontext() as ctx:
        ctx.prec = 50
        a = turnover * (1 + v)
        r = 2 * a / (v - u)
        b = v * r - a
        off = u * r * a / (b - u * r)
        association = catalytic_efficiency * (off * (b + r) + a * r) / (a * r)
    return BranchRates(association, off, a, b, r)


@dataclass(frozen=True, slots=True)
class CommonReleaseResponse(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-cycle-constraints/common-release-response'
    release_multiplier: Decimal
    turnover_multiplier: Decimal
    specificity_multiplier: Decimal
    carbon_efficiency_multiplier: Decimal
    oxygen_efficiency_multiplier: Decimal


def common_release_response(
    *, carbon_v: Decimal, carbon_u: Decimal, oxygen_u: Decimal, release_multiplier: Decimal,
) -> CommonReleaseResponse:
    """Scale both release rates, preserving binding and chemistry in each branch.

v_C=(a_C+b_C)/r_C; u_g=koff_g*b_g/[r_g*(koff_g+a_g)]. An admissible
positive carbon branch requires 0 <= u_C < v_C. Oxygen v is irrelevant to
specificity and is not silently assigned; an oxygen branch can realize each
nonnegative u_O. No observed enzyme is assigned these latent combinations.
"""
    _positive(carbon_v, 'carbon formation/release ratio')
    _positive(carbon_u, 'carbon reverse-capture ratio', zero_allowed=True)
    _positive(oxygen_u, 'oxygen reverse-capture ratio', zero_allowed=True)
    _positive(release_multiplier, 'release multiplier')
    if carbon_u >= carbon_v:
        raise ValueError('carbon u must be strictly below v for positive forward formation')
    lam = release_multiplier
    with localcontext() as ctx:
        ctx.prec = 50
        turnover = lam * (1 + carbon_v) / (lam + carbon_v)
        carbon = lam * (1 + carbon_u) / (lam + carbon_u)
        oxygen = lam * (1 + oxygen_u) / (lam + oxygen_u)
        specificity = carbon / oxygen
    return CommonReleaseResponse(lam, turnover, specificity, carbon, oxygen)


@dataclass(frozen=True, slots=True)
class JointNecessities(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-cycle-constraints/joint-necessities'
    minimum_turnover_multiplier: Decimal
    minimum_specificity_multiplier: Decimal
    strict_carbon_v_lower_bound: Decimal
    specificity_at_infinite_common_release: Decimal
    turnover_at_infinite_common_release: Decimal
    finite_release_can_meet_joint_targets: bool
    reason_codes: tuple[str, ...]


def joint_necessities(
    *, parent_turnover: Decimal, parent_specificity: Decimal,
    target_turnover: Decimal, target_specificity: Decimal,
    carbon_v: Decimal, carbon_u: Decimal, oxygen_u: Decimal,
) -> JointNecessities:
    """Check existence of lambda >= 1, including unchanged and boundary cases.

For increasing specificity (u_C>u_O), the limiting specificity multiplier
must be strictly above a required gain >1 to reach it at finite lambda.
For u_C<u_O, any acceleration decreases specificity. If the parent initially
has headroom, its finite allowed interval can still overlap the turnover need.
The latter is assessed analytically rather than rejected from the limit alone.
"""
    for value, field in (
        (parent_turnover, 'parent turnover'), (parent_specificity, 'parent specificity'),
        (target_turnover, 'target turnover'), (target_specificity, 'target specificity'),
    ):
        _positive(value, field)
    common_release_response(carbon_v=carbon_v, carbon_u=carbon_u,
                            oxygen_u=oxygen_u, release_multiplier=D(1))
    with localcontext() as ctx:
        ctx.prec = 50
        required_k = target_turnover / parent_turnover
        required_s = target_specificity / parent_specificity
        lower_v = max(D(0), required_k - 1)
        limit_k = 1 + carbon_v
        limit_s = (1 + carbon_u) / (1 + oxygen_u)
        reasons = []
        if required_k <= 1:
            lam_min = D(1)
        elif limit_k <= required_k:
            lam_min = None
            reasons.append('TURNOVER_GAIN_UNREACHABLE_AT_FINITE_RELEASE')
        else:
            lam_min = required_k * carbon_v / (carbon_v - required_k + 1)
        if lam_min is not None:
            if required_s > 1:
                if carbon_u <= oxygen_u or limit_s <= required_s:
                    reasons.append('SPECIFICITY_GAIN_UNREACHABLE_AT_FINITE_COMMON_RELEASE')
                else:
                    # S(lambda) = limit_s*(lambda+u_O)/(lambda+u_C).
                    lam_min = max(lam_min, (required_s * carbon_u - limit_s * oxygen_u) / (limit_s - required_s))
            elif carbon_u < oxygen_u:
                if required_s == 1:
                    if lam_min > 1:
                        reasons.append('SPEED_ACCELERATION_LOSES_REQUIRED_SPECIFICITY')
                elif limit_s < required_s:
                    lam_max = (required_s * carbon_u - limit_s * oxygen_u) / (limit_s - required_s)
                    if lam_min > lam_max:
                        reasons.append('FINITE_SPEED_AND_SPECIFICITY_INTERVALS_DISJOINT')
        return JointNecessities(required_k, required_s, lower_v, limit_s, limit_k,
                                not reasons, tuple(reasons))
