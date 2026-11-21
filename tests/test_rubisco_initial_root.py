# SPDX-License-Identifier: MPL-2.0
"""Disclosed exact controls for the separate joint root, never molecular evidence."""

from dataclasses import replace
from decimal import Decimal
from fractions import Fraction as F
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact as E
from empirical_lawhood.domains.rubisco.rubisco_response import initial_root as method
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_records import InitialRootDomainLimit
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.storage.artifacts import ArtifactIdentityConflict
from empirical_lawhood.api.domain_composition.rubisco_response import initial_root as public
from tests import test_rubisco_initial_model as controls
from tests.test_recursive_public_service import _plane


def evaluate(operands, **policies):
    selected, evidence, records, reviews = operands
    request = method.prepare_initial_root(model=selected, **policies)
    arguments = dict(request=request, selection=selected, evidence=evidence, reviews=reviews,
        joint_reviews=tuple(row for row in records if type(row) is controls.public.InitialJointSupportReview))
    result = method.calculate_initial_root(**arguments)
    checked = method.assess_initial_root(result=result, **arguments)
    assert checked.numerical_disposition is A.SATISFIED
    assert checked.joint_outcome == result.joint_outcome
    for record in (request, result, checked):
        assert decode_canonical_bytes(record.canonical_bytes(), type(record), maximum_bytes=2**20) == record
    return request, result, arguments


@pytest.mark.parametrize('values,expected,decisive', [
    ((2, 3, 1, 1), 'SUPPORTED', ()),
    ((1, 1, 1, 1), 'CONTRADICTED', ('turnover',)),
    ((2, 3, F(9, 10), 1), 'CONTRADICTED', ('specificity',)),
    ((1, 1, None, None), 'CONTRADICTED', ('turnover',)),
    ((None, None, F(9, 10), 1), 'CONTRADICTED', ('specificity',)),
    ((None, None, 1, 1), 'UNRESOLVED', ()),
    ((2, 3, None, None), 'UNRESOLVED', ()),
    ((F(6, 5), F(4, 5), 1, 1), 'UNRESOLVED', ()),
])
def test_joint_decision_and_partial_adversity_precede_cross_alternative_aggregation(values, expected, decisive):
    _, result, _ = evaluate(controls.support(values))
    row = result.cases[0].alternatives[0].realizations[0]
    assert result.joint_outcome == expected
    assert row.decisive_endpoints == decisive
    assert bool(result.decision_requirement_ids) == (expected == 'UNRESOLVED')
    assert result.biological_predictive_validity == 'UNEVALUABLE'
    assert result.new_native_calls == result.independent_biological_units == 0
    if decisive and None in values:
        assert result.original_remaining_requirement_ids
        assert row.omitted_operands
        # The old reader keeps its original endpoint-first interpretation.
        assert controls.read(controls.support(values))[1]['joint_owner_criterion'] == 'UNEVALUABLE'


def test_strict_waiting_threshold_and_unchanged_decimal_independent_bounds():
    _, result, _ = evaluate(controls.support((F(6, 5), F(4, 5), 1, 1)))
    row = result.cases[0].alternatives[0].realizations[0]
    assert (row.support_waiting_condition.equivalent_relation, row.support_waiting_condition.threshold) == ('GT', E.of(F(3, 5)))
    assert (row.contradiction_waiting_condition.equivalent_relation, row.contradiction_waiting_condition.threshold) == ('LE', E.of(F(3, 5)))
    for w in (F(0), F(1, 2), F(3, 5), F(7, 10), F(1)):
        turnover = 1 / (w/F(6, 5) + (1-w)/F(4, 5))
        assert (turnover > 1) == (w > row.support_waiting_condition.threshold.fraction)
    _, eliminated, _ = evaluate(controls.support((F(11, 10), F(6, 5), 1, 1)))
    assert 'wild-type-waiting-fraction' in eliminated.cases[0].alternatives[0].realizations[0].omitted_operands


@pytest.mark.parametrize('kind', ['FIXED_JOINT_REALIZATION', 'JOINT_ENCLOSURE', 'JOINT_SAMPLE'])
def test_samples_and_unreviewed_bounds_do_not_become_joint_physical_support(kind):
    selected, evidence, records, reviews = controls.support(kind=kind)
    _, result, _ = evaluate((selected, evidence, records, reviews))
    assert result.joint_outcome == ('UNRESOLVED' if kind == 'JOINT_SAMPLE' else 'SUPPORTED')
    _, without_reviews, _ = evaluate((selected, evidence, records[:-1], ()))
    assert without_reviews.joint_outcome == 'UNRESOLVED'


def multiple_alternatives(values):
    selected, source = controls.selection()
    alternatives, records, all_reviews = [], [source], []
    for number, value in enumerate(values):
        _, evidence, original_records, reviews = controls.support(value)
        original = evidence.cases[0].alternatives[0]
        point = original.realizations[0]
        suffix = '.alternative.' + str(number)
        revised = tuple(replace(row, review_id=row.review_id + suffix) for row in reviews)
        pins = {old.identity: new.identity for old, new in zip(reviews, revised, strict=True)}
        contrasts = tuple(replace(row, applicability_review=pins.get(row.applicability_review),
            sources=tuple(sorted((pins.get(pin, pin) for pin in row.sources), key=lambda p:p.object_id)))
            for row in point.contrasts)
        joint = replace(original_records[-1], review_id=original_records[-1].review_id + suffix,
            realization_id=point.realization_id + suffix,
            supporting_sources=tuple(sorted((pins.get(pin, pin) for pin in original_records[-1].supporting_sources), key=lambda p:p.object_id)))
        point = replace(point, realization_id=joint.realization_id, contrasts=contrasts, joint_support_source=joint.identity)
        alternatives.append(replace(original, alternative_id=original.alternative_id + suffix,
            expected_realization_ids=(point.realization_id,), realizations=(point,)))
        records.extend((*revised, joint))
        all_reviews.extend(revised)
    case = replace(selected.cases[0], expected_alternative_ids=tuple(row.alternative_id for row in alternatives))
    selected = replace(selected, cases=(case,))
    evidence = replace(evidence, selection=selected.identity,
        cases=(replace(evidence.cases[0], alternatives=tuple(alternatives)),))
    return selected, evidence, tuple(records), tuple(all_reviews)


def test_each_alternative_can_contradict_the_conjunction_through_a_different_endpoint():
    operands = multiple_alternatives(((1, 1, None, None), (None, None, F(9, 10), 1)))
    _, result, _ = evaluate(operands)
    assert result.joint_outcome == 'CONTRADICTED'
    assert tuple(a.realizations[0].decisive_endpoints for a in result.cases[0].alternatives) == (('turnover',), ('specificity',))
    assert controls.read(operands)[1]['joint_owner_criterion'] == 'UNEVALUABLE'


def test_uniform_physical_conclusion_and_robust_universal_request_have_different_quantifiers():
    operands = multiple_alternatives(((2, 3, 1, 1), (1, 1, 1, 1)))
    _, uniform, _ = evaluate(operands)
    _, robust, _ = evaluate(operands, alternative_policy=method.ROBUST)
    assert uniform.joint_outcome == 'UNRESOLVED'
    assert any('physical-alternative-resolution' in s for s in uniform.decision_requirement_ids)
    assert robust.joint_outcome == 'CONTRADICTED'


@pytest.mark.parametrize('reason', ['ZERO_MUTANT_RATE', 'ABSENT_CHANNEL', 'ZERO_WT_REFERENCE', 'UNDEFINED_EFFECTIVE_RATIO'])
def test_zero_and_undefined_domains_stay_outside_positive_ratios(reason):
    operands = controls.support((None, 1, 1, 1))
    selected = operands[0]
    limit = InitialRootDomainLimit(selected.cases[0].case_id, 'chemical.exposed', 'a', reason,
        'requirement.exposed.nonpositive-domain')
    _, result, _ = evaluate(operands, domain_limits=(limit,))
    assert result.joint_outcome == 'UNRESOLVED'
    assert limit.requirement_id in result.decision_requirement_ids
    with pytest.raises(ValueError, match='contradicts supplied positive'):
        evaluate(controls.support(), domain_limits=(limit,))
    # A domain limitation on turnover cannot erase a supported specificity failure.
    _, contradicted, _ = evaluate(controls.support((None, 1, F(9, 10), 1)), domain_limits=(limit,))
    assert contradicted.joint_outcome == 'CONTRADICTED'


def test_independent_assessor_refuses_changed_conclusion_threshold_or_consumer():
    request, result, arguments = evaluate(controls.support((F(6, 5), F(4, 5), 1, 1)))
    changed = replace(result, joint_outcome='SUPPORTED')
    assert method.assess_initial_root(result=changed, **arguments).numerical_disposition is A.FALSIFIED
    case, = result.cases
    alternative, = case.alternatives
    row, = alternative.realizations
    wrong_threshold = replace(row.support_waiting_condition, threshold=E.of(F(1, 2)))
    changed_row = replace(row, support_waiting_condition=wrong_threshold)
    changed = replace(result, cases=(replace(case, alternatives=(replace(alternative, realizations=(changed_row,)),)),))
    assert method.assess_initial_root(result=changed, **arguments).numerical_disposition is A.FALSIFIED
    with pytest.raises(ValueError, match='exact consumer'):
        method.assess_initial_root(result=result, **{**arguments, 'request': replace(request, processing_policy=method.ROBUST)})


def test_missing_alternative_is_kept_in_uniform_conclusion_and_complete_source_census():
    selected, evidence, records, reviews = multiple_alternatives(((1, 1, 1, 1), (2, 3, 1, 1)))
    case, = evidence.cases
    first, second = case.alternatives
    second = replace(second, original_state='UNKNOWN', expected_realization_ids=(), realizations=(),
        unresolved_requirement_ids=('requirement.missing.alternative',))
    evidence = replace(evidence, cases=(replace(case, alternatives=(first, second)),))
    first_reviews = tuple(row for row in reviews if row.review_id.endswith('.alternative.0'))
    first_records = tuple(row for row in records if not hasattr(row, 'review_id') or row.review_id.endswith('.alternative.0'))
    _, result, _ = evaluate((selected, evidence, first_records, first_reviews))
    assert result.joint_outcome == 'UNRESOLVED'
    assert len(result.cases[0].alternatives) == 2
    assert 'requirement.missing.alternative' in result.decision_requirement_ids


@pytest.fixture
def numerical_provenance(monkeypatch):
    package = (('src/exposed_root_control.py', '4'*64),)
    digest = sha256(canonical_json_bytes(package)).hexdigest()
    provenance = NumericalProducingProvenance(
        '{"python":"exposed","numpy":"exposed","scipy":"exposed","system":"Linux","machine":"exposed","threadpools":[]}',
        '5'*64, package, digest, '3'*40, False)
    from empirical_lawhood.api import numerical_provenance, recursive_authoring
    monkeypatch.setattr(recursive_authoring, 'implementation_binding',
        lambda _: SimpleNamespace(code_sources_sha256=digest, dependency_lock_sha256='5'*64))
    monkeypatch.setattr(numerical_provenance, 'capture_numerical_provenance', lambda **k: provenance)
    return provenance


def test_separate_export_reconstructs_original_source_and_preserves_historical_readout(tmp_path, numerical_provenance):
    selected, evidence, records, _ = controls.support((1, 1, None, None))
    writer = _plane(tmp_path/'custody')
    sources = controls.publish_sources(writer, records)
    original = controls.public.export_initial_model(selection=selected, evidence=evidence, sources=sources,
        project_root=tmp_path, artifact_writer=writer, output_relative_path='historical')
    original_bytes = {name: (tmp_path/'custody'/'historical'/name).read_bytes() for name in controls.public.MEMBERS}
    request = public.prepare_initial_root(model=selected)
    exported = public.export_initial_root(request=request, selection=selected, evidence=evidence, sources=sources,
        project_root=tmp_path, artifact_writer=writer, output_relative_path='joint')
    reread = public.read_initial_root_export(directory_relative_path='joint', sources=sources, artifact_writer=writer)
    assert reread['result'] == exported['result']
    assert reread['assessment'] == exported['assessment']
    assert reread['result'].joint_outcome == 'CONTRADICTED'
    assert reread['evidence'].cpu_seconds >= Decimal(0)
    assert reread['evidence'].provenance == numerical_provenance
    assert len(exported['paths']) == 7
    historical = controls.public.read_initial_model_export(directory_relative_path='historical', sources=sources, artifact_writer=writer)
    assert historical['report'] == original['report']
    assert original_bytes == {name: (tmp_path/'custody'/'historical'/name).read_bytes() for name in controls.public.MEMBERS}
    with pytest.raises(ValueError, match='fresh'):
        public.export_initial_root(request=request, selection=selected, evidence=evidence, sources=sources,
            project_root=tmp_path, artifact_writer=writer, output_relative_path='joint')
    path = tmp_path/'custody'/'sources'/'0.json'
    path.write_bytes(path.read_bytes() + b'\n')
    with pytest.raises(ArtifactIdentityConflict):
        public.read_initial_root_export(directory_relative_path='joint', sources=sources, artifact_writer=writer)


def test_guard_stays_live_across_new_root_analysis_and_complete_sources_are_required(tmp_path, monkeypatch):
    selected, evidence, records, _ = controls.support()
    writer = _plane(tmp_path/'custody')
    sources = controls.publish_sources(writer, records)
    request = public.prepare_initial_root(model=selected)
    with pytest.raises(ValueError, match='complete original census'):
        public.read_initial_root_sources(request=request, selection=selected, evidence=evidence, sources=sources[:-1])
    path = tmp_path/'custody'/'sources'/'0.json'
    calculate = public.calculate_initial_root
    def mutate(**kwargs):
        result = calculate(**kwargs)
        path.write_bytes(path.read_bytes() + b'\n')
        return result
    monkeypatch.setattr(public, 'calculate_initial_root', mutate)
    with pytest.raises(ArtifactIdentityConflict):
        public.read_initial_root_sources(request=request, selection=selected, evidence=evidence, sources=sources)
