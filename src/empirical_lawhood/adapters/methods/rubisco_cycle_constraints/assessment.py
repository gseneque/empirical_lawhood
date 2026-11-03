# SPDX-License-Identifier: MPL-2.0
"""Independent normalized state balances, separate from closed-form eliminations."""
from decimal import Decimal, localcontext
from dataclasses import replace

from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition
from .contracts import (BalanceResult, CycleProcedureAssessment, CycleSupply, CycleUseProduct, CycleAnchorResult,
                        CycleScenarioResult, ScenarioSample, ReleaseBalanceResult, DEFAULT_SCENARIOS, RELEASE_MULTIPLIERS,
                        design_from_source, scope, selected_probes, identity, finite_release_interval)
from .science import BranchRates, branch_observables, finite_gas_flux, common_release_response, joint_necessities, realize_conditional_branch

D = Decimal


def _solve(matrix):
    n = len(matrix)
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(matrix[row][col]))
        matrix[col], matrix[pivot] = matrix[pivot], matrix[col]
        if matrix[col][col] == 0:
            raise ValueError('independent cycle state-balance matrix is singular')
        denominator = matrix[col][col]
        matrix[col] = [value / denominator for value in matrix[col]]
        for row in range(n):
            if row != col:
                scale = matrix[row][col]
                matrix[row] = [value - scale * basis for value, basis in zip(matrix[row], matrix[col], strict=True)]
    return tuple(row[-1] for row in matrix)


def independent_state_balance(rates, gas_um):
    """Solve the original three-state equations with pivoted Decimal elimination."""
    association = rates.association_um_inv_s_inv * gas_um
    off, a, b, release = rates.gas_dissociation_s_inv, rates.forward_product_s_inv, rates.reverse_product_s_inv, rates.release_s_inv
    with localcontext() as ctx:
        ctx.prec = 60
        matrix = [[-association, off, release, D(0)], [association, -(off + a), b, D(0)], [D(1), D(1), D(1), D(1)]]
        x, c, p = _solve(matrix)
        residual = max(abs(-association*x + off*c + release*p), abs(association*x - (off+a)*c + b*p), abs(a*c - (b+release)*p))
        return x, c, p, release*p, residual


def independent_competing_specificity(carbon, oxygen):
    """Both gas branches share X; specificity comes from actual competing fluxes."""
    c, o = carbon, oxygen
    gas_c, gas_o = D(1), D(10)
    kc, ko = c.association_um_inv_s_inv*gas_c, o.association_um_inv_s_inv*gas_o
    with localcontext() as ctx:
        ctx.prec = 60
        z = D(0)
        matrix = [[-(kc+ko), c.gas_dissociation_s_inv, c.release_s_inv, o.gas_dissociation_s_inv, o.release_s_inv, z],
                  [kc, -(c.gas_dissociation_s_inv+c.forward_product_s_inv), c.reverse_product_s_inv, z, z, z],
                  [z, c.forward_product_s_inv, -(c.reverse_product_s_inv+c.release_s_inv), z, z, z],
                  [ko, z, z, -(o.gas_dissociation_s_inv+o.forward_product_s_inv), o.reverse_product_s_inv, z],
                  [D(1), D(1), D(1), D(1), D(1), D(1)]]
        occupancy = _solve(matrix)
        if min(occupancy) < -D('1e-12') or abs(sum(occupancy)-1) > D('1e-12'):
            raise ValueError('conditional competing-state witness violates independent enzyme census')
        return (c.release_s_inv*occupancy[2]) / (o.release_s_inv*occupancy[4]) * gas_o/gas_c


def assess_release_scenarios():
    checks = []
    for sc in DEFAULT_SCENARIOS:
        carbon = realize_conditional_branch(turnover=D(2), catalytic_efficiency=D('.2'),
                    formation_release_ratio=sc.carbon_v, reverse_capture_ratio=sc.carbon_u)
        oxygen = realize_conditional_branch(turnover=D(1), catalytic_efficiency=D('.01'),
                    formation_release_ratio=sc.oxygen_u+1, reverse_capture_ratio=sc.oxygen_u)
        base_k = independent_state_balance(carbon, D('1e30'))[3]
        base_c = independent_state_balance(carbon, D('1e-20'))[3]
        base_o = independent_state_balance(oxygen, D('1e-20'))[3]
        base_s = independent_competing_specificity(carbon, oxygen)
        for multiplier in RELEASE_MULTIPLIERS:
            c, o = replace(carbon, release_s_inv=carbon.release_s_inv*multiplier), replace(oxygen, release_s_inv=oxygen.release_s_inv*multiplier)
            response = common_release_response(carbon_v=sc.carbon_v, carbon_u=sc.carbon_u, oxygen_u=sc.oxygen_u, release_multiplier=multiplier)
            actual = (independent_state_balance(c, D('1e30'))[3]/base_k,
                      independent_state_balance(c, D('1e-20'))[3]/base_c,
                      independent_state_balance(o, D('1e-20'))[3]/base_o,
                      independent_competing_specificity(c, o)/base_s)
            expected = (response.turnover_multiplier, response.carbon_efficiency_multiplier, response.oxygen_efficiency_multiplier, response.specificity_multiplier)
            discrepancy = max(abs(a-b)/max(D(1), abs(b)) for a, b in zip(actual, expected, strict=True))
            checks.append(ReleaseBalanceResult(sc, multiplier, discrepancy, discrepancy <= D('1e-12')))
    return tuple(checks)


def assess_procedure():
    tolerance = D('1e-12')
    results = []
    for probe in selected_probes():
        x, c, p, flux, residual = independent_state_balance(probe.rates, probe.gas_um)
        predicted = finite_gas_flux(probe.rates, probe.gas_um)
        discrepancy = abs(predicted - flux)
        passed = (min(x, c, p) >= -tolerance and abs(x+c+p-1) <= tolerance
                  and residual <= tolerance and discrepancy <= tolerance)
        results.append(BalanceResult(probe, branch_observables(probe.rates), x, c, p, flux, predicted, residual, discrepancy, passed))
    # These contrasts use the independently solved low-gas flux, not the same
    # catalytic-efficiency formula being falsified.
    gas = D('1e-20')
    def efficiency(reverse, release):
        return independent_state_balance(BranchRates(D('.2'), D(2), D(3), reverse, release), gas)[3] / gas
    cancellation = abs(efficiency(D(0), D(7)) - efficiency(D(0), D(70))) <= tolerance
    exception = efficiency(D(5), D(70)) > efficiency(D(5), D(7))
    release_checks = assess_release_scenarios()
    passed = all(row.passed for row in results) and all(row.passed for row in release_checks) and cancellation and exception
    return CycleProcedureAssessment('check.rubisco-cycle.normalized-state-balance', tuple(results), cancellation, exception, tolerance,
                                    AssessmentDisposition.SATISFIED if passed else AssessmentDisposition.FALSIFIED, release_checks)


def supply(source):
    design = design_from_source(source)
    check = assess_procedure()
    return CycleSupply('product.rubisco-cycle.assessed-conditional-model', design, check, scope(design), check.disposition)


def validate_supplier(supplier):
    if type(supplier) is not CycleSupply or supplier.check != assess_procedure():
        raise ValueError('cycle supplier differs from actual independent complete state-balance assessment')
    CycleSupply(supplier.product_id, supplier.design, supplier.check, supplier.scope, supplier.disposition)


def validate_instance(source, instance):
    from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry.science import selected_candidates
    if identity(source) != instance.macro_source:
        raise ValueError('cycle instance substitutes actual macro source bytes')
    available = {row.candidate_id: row for row in selected_candidates(source)}
    if not set(instance.candidate_ids) <= set(available):
        raise ValueError('cycle instance selects a macro anchor outside authenticated candidate roster')
    selected = tuple(available[key] for key in instance.candidate_ids)
    if any(row.turnover_s_inv is None or row.specificity_dimensionless is None for row in selected):
        raise ValueError('cycle instance has unknown macro endpoints; no microscopic calibration permitted')
    return selected


def assess_use(supplier, source, instance):
    from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry.science import REFERENCES
    model = supplier if type(supplier) is CycleSupply else supplier.model
    validate_supplier(model)
    candidates = validate_instance(source, instance)
    refs = {row[0]: row for row in REFERENCES}
    anchors = []
    for candidate in candidates:
        for name in instance.reference_ids:
            reference = refs[name]
            rows = []
            for sc in instance.scenarios:
                needed = joint_necessities(parent_turnover=candidate.turnover_s_inv, parent_specificity=candidate.specificity_dimensionless,
                    target_turnover=reference[1], target_specificity=reference[2], carbon_v=sc.carbon_v, carbon_u=sc.carbon_u, oxygen_u=sc.oxygen_u)
                samples = []
                for multiplier in instance.release_multipliers:
                    response = common_release_response(carbon_v=sc.carbon_v, carbon_u=sc.carbon_u, oxygen_u=sc.oxygen_u, release_multiplier=multiplier)
                    samples.append(ScenarioSample(response, response.turnover_multiplier >= needed.minimum_turnover_multiplier
                                                  and response.specificity_multiplier >= needed.minimum_specificity_multiplier))
                rows.append(CycleScenarioResult(sc, needed, sc.carbon_u == 0 and sc.oxygen_u == 0
                                                and needed.minimum_specificity_multiplier > 1, tuple(samples),
                                                *finite_release_interval(sc, needed.minimum_turnover_multiplier, needed.minimum_specificity_multiplier)))
            anchors.append(CycleAnchorResult(candidate, reference, tuple(rows)))
    return CycleUseProduct('product.rubisco-cycle.' + instance.instance_id, identity(supplier), model, instance,
                           tuple(anchors), model.scope, model.disposition)
