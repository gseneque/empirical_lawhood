# SPDX-License-Identifier: MPL-2.0
"""Portable independent quadratic and refusal controls; no molecular claims."""

from dataclasses import replace
from decimal import Decimal, localcontext
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_environment import MODELS, PreparationResponseEnvironment, _environmental_candidate, _product, environment_coordinate_discrepancy
from empirical_lawhood.science.identity.provenance import ObjectIdentity


def _environment():
    def pin(name):
        return ObjectIdentity(name, 'empirical-lawhood/exposed-numerical-source', '1.0.0', '1' * 64)
    return PreparationResponseEnvironment('environment.exposed.quadratic', 'SELECTED_COMMON_PROTEIN_RESIDUES',
        (('chain.environment', 7),), tuple((m, pin('representation.' + m)) for m in MODELS),
        tuple((m, pin('preparation.' + m)) for m in MODELS), tuple((m, 6) for m in MODELS),
        tuple((m, (0, 1, 2)) for m in MODELS),
        (('chain.environment', 7, 'CA', 6, 5, 3), ('chain.environment', 7, 'CB', 6, 3, 4),
         ('chain.environment', 7, 'CG', 6, 4, 5)),
        (Decimal(20),) * 3, Decimal('0.000001'))


def _quadratic_operands():
    """Two symmetric K operators with opposite receiver/environment coupling."""
    environment = _environment()
    coordinates = {m: np.zeros((6, 3), dtype='<f8') for m in MODELS}
    for ordinal, pair in enumerate(environment.atom_pairs):
        coordinates['m1-wt'][pair[5], ordinal] = ordinal + 1
        coordinates['m1-i95m'][pair[4], ordinal] = ordinal + 1
    matrices = {m: 10 * np.eye(18, dtype='<f8') for m in MODELS}
    for model, couplings in (('m1-wt', ((3, 0, 3.), (4, 1, 4.))),
                             ('m1-i95m', ((5, 0, -3.), (3, 1, -4.)))):
        for atom, axis, value in couplings:
            index = 3 * atom + axis
            matrices[model][0, index] = matrices[model][index, 0] = value
    u = np.eye(18)[0]
    actions = {m: (matrix @ u).reshape((6, 3)) for m, matrix in matrices.items()}
    return environment, coordinates, matrices, actions


def _candidate(environment, coordinates, fine, coarse=None):
    return _environmental_candidate(environment=environment, coordinates=coordinates,
        fine_actions=fine, coarse_actions=fine if coarse is None else coarse,
        amplitude=Decimal('.2'), allowance=Decimal('.00005'))


@pytest.mark.numerical(oracle='Direct multiplication of independent opposite-coupling quadratic matrices gives signed receiver changes -1 and +1')
def test_common_direction_preserves_mutant_sign_and_receiver_atom_exclusion():
    environment, coordinates, matrices, actions = _quadratic_operands()
    status, norm, mismatch, discrepancies, components = _candidate(environment, coordinates, actions)
    assert status == 'AVAILABLE' and norm == 5 and mismatch == 0
    assert discrepancies == tuple((m, Decimal(0)) for m in MODELS)
    directions = {}
    for model, selected in components:
        d = np.zeros((6, 3), dtype='<f8')
        for atom, axis, value in selected:
            d[atom, axis] = float(value)
        assert np.array_equal(d[:3], np.zeros((3, 3)))
        assert np.linalg.norm(d) == pytest.approx(1)
        directions[model] = d
    assert directions['m1-wt'][3, 0] == directions['m1-i95m'][5, 0] == pytest.approx(.6)
    assert directions['m1-wt'][4, 1] == directions['m1-i95m'][3, 1] == pytest.approx(.8)
    for model, expected in (('m1-wt', -1.), ('m1-i95m', 1.)):
        d = directions[model]
        # Independent direct finite quadratic response: -(K * alpha*d)[0].
        direct = -(matrices[model] @ (.2 * d.ravel()))[0]
        predicted = -.2 * np.vdot(d, actions[model])
        assert direct == pytest.approx(expected)
        assert predicted == pytest.approx(direct)


def test_zero_signal_invalid_mapping_and_both_arm_scale_failures_are_retained():
    environment, coordinates, _, actions = _quadratic_operands()
    zero = {m: np.zeros_like(action) for m, action in actions.items()}
    status, _, _, _, components = _candidate(environment, coordinates, zero)
    assert status == 'NEGLIGIBLE_PROJECTED_RESPONSE' and components == ()
    changed = {m: xyz.copy() for m, xyz in coordinates.items()}
    changed['m1-i95m'][5, 0] += .001
    status, norm, mismatch, _, components = _candidate(environment, changed, actions)
    assert status == 'INVALID_COORDINATE_CORRESPONDENCE' and norm is None and mismatch > 0
    assert components == ()
    for model, atom, axis in (('m1-wt', 3, 0), ('m1-i95m', 5, 0)):
        coarse = {m: action.copy() for m, action in actions.items()}
        coarse[model][atom, axis] += .01
        status, _, _, discrepancies, components = _candidate(environment, coordinates, actions, coarse)
        assert status == 'NUMERICALLY_UNRESOLVED'
        assert dict(discrepancies)[model] == pytest.approx(Decimal('.0012'))
        assert components  # Retained evidence, never an acquisition fallback.


def test_prospective_support_cannot_include_receiver_or_repeated_atoms():
    environment = _environment()
    changed = list(environment.atom_pairs)
    changed[0] = (*changed[0][:4], 0, changed[0][5])
    with pytest.raises(ValueError, match='retained-core or receiver'):
        replace(environment, atom_pairs=tuple(changed))
    changed[0] = (*changed[0][:4], environment.atom_pairs[1][4], changed[0][5])
    with pytest.raises(ValueError, match='duplicates or omits'):
        replace(environment, atom_pairs=tuple(changed))


def test_coordinate_preflight_needs_no_force_or_action_observation():
    environment, coordinates, _, _ = _quadratic_operands()
    assert environment_coordinate_discrepancy(environment, coordinates) == 0
    coordinates['m1-i95m'][5, 2] += .01
    assert environment_coordinate_discrepancy(environment, coordinates) > environment.coordinate_tolerance_angstrom
    with pytest.raises(ValueError, match='both original'):
        environment_coordinate_discrepancy(environment, {'m1-wt': coordinates['m1-wt']})


@pytest.mark.numerical(oracle='Exact decimal multiplication with precomputed 43-digit product')
def test_nomination_threshold_products_do_not_depend_on_decimal_context():
    left, right = Decimal('0.000472091234567890123456789012345678901234567890'), Decimal('.1')
    with localcontext() as context:
        context.prec = 6
        actual = _product(left, right)
    assert actual == Decimal('0.0000472091234567890123456789012345678901234567890')


def test_refined_reciprocity_cannot_hide_aligned_subthreshold_discrepancies():
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_assessment import PreparationResponseQuantity, _questions
    from tests.test_rubisco_preparation_response_decisions import findings
    original = findings(numerical='.09', reciprocal='.09')
    quantities = {(q.name, q.model_name, q.position): q for question in original for q in question.quantities}
    for model in MODELS:
        row = PreparationResponseQuantity('additional-receiver-scale-discrepancy', model, 'later',
            Decimal('.09'), 'hartree/bohr')
        quantities[row.name, row.model_name, row.position] = row
    design = SimpleNamespace(useful_error_hartree_per_bohr=Decimal(1), numerical_allowance_fraction=Decimal('.1'))
    assert _questions(design, tuple(quantities.values()), ())[0].disposition == 'EMPIRICALLY_CONSISTENT'
    # Coarse residual +0.09, u.Kd change +0.09, d.Ku change -0.09:
    # each constituent passes 0.1, but the observed fine residual is +0.27.
    row = PreparationResponseQuantity('fine-reciprocal-receiver-discrepancy', 'm1-wt', 'later',
        Decimal('.27'), 'hartree/bohr')
    quantities[row.name, row.model_name, row.position] = row
    reviewed = _questions(design, tuple(quantities.values()), ())
    assert reviewed[0].disposition == 'CONSEQUENTIAL_SCALE_SENSITIVITY'
    assert reviewed[1].disposition == reviewed[3].disposition == 'NUMERICALLY_UNRESOLVED'


def test_unavailable_prefix_keeps_its_original_consequence_without_admitting_partial_response(monkeypatch):
    from empirical_lawhood.domains.rubisco.rubisco_response import preparation_response_assessment as owner
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_assessment_records import PreparationResponseCoverage
    from tests.test_rubisco_preparation_response_decisions import findings
    # Isolate the consequence relation from the separately checked record and
    # molecular-custody boundaries. The rows themselves retain their typed form.
    monkeypatch.setattr(owner, 'require_response_assessment', lambda assessment: None)
    pin = ObjectIdentity('effect.exposed.unentered', 'empirical-lawhood/exposed-effect', '1.0.0', '2' * 64)
    questions = tuple(replace(row, disposition='UNAVAILABLE', assessable_comparisons=0,
        quantities=tuple(replace(value, value=None) for value in row.quantities)) for row in findings())
    coverage = (PreparationResponseCoverage(pin, 'initial-primary', 'NOT_ENTERED', None, None),
        PreparationResponseCoverage(pin, 'additional-refinement', 'NOT_SELECTED', None, None))
    report = SimpleNamespace(design=object(), nomination=None, actions=(), questions=questions, coverage=coverage)
    assert owner.response_supplier_decision(report) == (
        'REASSESS_UNAVAILABLE_PAIRED_PREPARATION_OR_JUSTIFIABLY_STOP_WITH_ORIGINAL_DENOMINATOR')
    report.coverage = (replace(coverage[0], point=pin), coverage[1])
    assert owner.response_supplier_decision(report) == owner.next_response_supplier(questions)
    report.coverage, report.actions = coverage, (object(),)
    assert owner.response_supplier_decision(report) == owner.next_response_supplier(questions)
