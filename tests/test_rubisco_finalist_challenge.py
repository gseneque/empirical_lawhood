# SPDX-License-Identifier: MPL-2.0
"""Exposed original-source/math challenge checks; no workers or assay entry."""
from dataclasses import replace
from decimal import Decimal

import pytest
from tests.rubisco_inquiry_source_fixtures import finalist_source_operands

from empirical_lawhood.adapters.methods.rubisco_cycle_constraints import assessment as cycle, contracts, recursive_translation as cycle_drafts
from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry import science as portfolio
from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry.challenge import FINALIST_IDS, FinalistChallenge, challenge_finalists
from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry.source_manifest import INITIAL_CANDIDATE_IDS
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition


@pytest.fixture(scope='module')
def actual_source_products():
    macro_bytes, mechanism_bytes, yamori_bytes = finalist_source_operands()
    source = portfolio.source_audit_from_bytes(macro_bytes, candidate_ids=INITIAL_CANDIDATE_IDS)
    supplier = portfolio.supply(source)
    assessed = portfolio.assess(supplier, portfolio.authentic_candidate(supplier))
    mechanism = contracts.source_audit_from_bytes(mechanism_bytes)
    model = cycle.supply(mechanism)
    first_query = cycle_drafts.instance_from_source(source, instance_id='instance.finalist.first', candidate_ids=('gp.wt', 'wilson2017-row17'))
    second_query = cycle_drafts.instance_from_source(source, instance_id='instance.finalist.second', candidate_ids=('nt.a369.t391i', 'potato.ps3', 'potato.pst'))
    first = cycle.assess_use(model, source, first_query)
    second = cycle.assess_use(first, source, second_query)
    # Saved canonical products, not invented success receipts or worker evidence.
    saved_assessed = decode_canonical_bytes(assessed.canonical_bytes(), portfolio.PortfolioAssessment, maximum_bytes=None)
    saved_uses = tuple(decode_canonical_bytes(row.canonical_bytes(), contracts.CycleUseProduct, maximum_bytes=None) for row in (first, second))
    return supplier, saved_assessed, saved_uses, yamori_bytes


def test_saved_two_uses_preserve_five_union_primary_role_and_proposed_assays(actual_source_products):
    supplier, assessed, uses, yamori = actual_source_products
    frontier = {row.candidate_id for row in assessed.candidate_views if row.within_background_point_nondominated}
    assert frontier == {'gp.wt', 'wilson2017-row17', 'nt.a369.t391i', 'nt.a369.a369v', 'potato.ps3', 'potato.pst'}
    result = challenge_finalists(supplier, assessed, uses, yamori)
    assert tuple(row.candidate_id for row in result.cases) == FINALIST_IDS
    assert uses[1].supplier == contracts.identity(uses[0])
    assert all(len(row.conditional_margins) == 2 for row in result.cases)
    assert all(total == 36 for row in result.cases for _, _, total in row.finite_release_supporting_families)
    # Every anchor retains both admitting countermodels and adverse scenarios;
    # neither global impossibility nor an identified biological mechanism follows.
    assert all(0 < passed < total for row in result.cases for _, passed, total in row.finite_release_supporting_families)
    assert result.nominee is None and result.new_biological_units == 0
    assert result.biological_disposition is AssessmentDisposition.UNEVALUABLE
    assert result.assay_proposition.status == 'PROPOSED_NOT_ENTERED'
    assert 'IN_VIVO_COMPENSATION_POINT_INFERENCE_NOT_PAIRED_ENZYME_LABEL' in result.adverse_findings[0]
    assert result == decode_canonical_bytes(result.canonical_bytes(), FinalistChallenge, maximum_bytes=None)


def test_challenge_refuses_changed_primary_and_false_joint_endpoint(actual_source_products):
    supplier, assessed, uses, yamori = actual_source_products
    with pytest.raises(ValueError, match='source|bytes'):
        challenge_finalists(supplier, assessed, uses, yamori + b' ')
    views = (replace(assessed.candidate_views[0], point_joint_pass=True), *assessed.candidate_views[1:])
    with pytest.raises(ValueError, match='authentic|portfolio'):
        challenge_finalists(supplier, replace(assessed, candidate_views=views), uses, yamori)
    with pytest.raises(ValueError, match='five|denominator|use'):
        challenge_finalists(supplier, assessed, (uses[0], uses[0]), yamori)


def test_challenge_refuses_self_consistent_wrong_macro_source_and_reference(actual_source_products, monkeypatch):
    supplier, assessed, uses, yamori = actual_source_products
    wrong_query = replace(uses[0].instance, macro_source=replace(uses[0].instance.macro_source, object_fingerprint='a' * 64))
    wrong_source = replace(uses[0], instance=wrong_query)
    wrong_descendant = replace(uses[1], supplier=contracts.identity(wrong_source))
    with pytest.raises(ValueError, match='source|authentic|identity'):
        challenge_finalists(supplier, assessed, (wrong_source, wrong_descendant), yamori)
    # Preserve reference names and mathematical consistency while substituting
    # the scientific threshold. A name-only join would accept this false support.
    with monkeypatch.context() as patch:
        patch.setattr(portfolio, 'REFERENCES', tuple((name, Decimal('0.1'), Decimal('1')) for name, _, _ in portfolio.REFERENCES))
        wrong_reference = cycle.assess_use(uses[0].model, supplier.source, uses[0].instance)
        wrong_reuse = cycle.assess_use(wrong_reference, supplier.source, uses[1].instance)
    with pytest.raises(ValueError, match='reference|authentic|identity'):
        challenge_finalists(supplier, assessed, (wrong_reference, wrong_reuse), yamori)


def test_challenge_cannot_manufacture_nomination_or_entered_assay(actual_source_products):
    result = challenge_finalists(*actual_source_products)
    for changes in ({'nominee': 'gp.wt'}, {'new_biological_units': 1}, {'biological_disposition': AssessmentDisposition.SATISFIED}):
        with pytest.raises(ValueError):
            replace(result, **changes)
    with pytest.raises(ValueError):
        replace(result.assay_proposition, status='ENTERED')
