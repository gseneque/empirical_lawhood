# SPDX-License-Identifier: MPL-2.0
"""Exposed mathematical/compilation fixtures; no provider or scientific launch."""
from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
from types import SimpleNamespace as N

import pytest

from empirical_lawhood.adapters.methods.rubisco_cycle_constraints import assessment, contracts, operation_bindings as owner, recursive_translation as drafts
from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry import science as portfolio
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition, AssessmentPhase
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.recursive_compiler import project_recursive_assessments
from tests.test_inquiry_successor_compilation import compile_complete_draft, portable_parent
from tests.rubisco_nomination_fixture import sources as exposed_sources


@pytest.fixture(scope='module')
def sources():
    return exposed_sources()


@pytest.fixture(scope='module')
def model(sources):
    return assessment.supply(sources[0])


@pytest.fixture(scope='module')
def queries(sources):
    first = drafts.instance_from_source(sources[1], instance_id='instance.cycle.first', candidate_ids=('gp.wt', 'wilson2017-row17'))
    second = drafts.instance_from_source(sources[1], instance_id='instance.cycle.second', candidate_ids=('nt.a369.t391i', 'potato.ps3', 'potato.pst'))
    return first, second


@pytest.fixture(scope='module')
def uses(sources, model, queries):
    first = assessment.assess_use(model, sources[1], queries[0])
    return first, assessment.assess_use(first, sources[1], queries[1])


def _metadata_products(draft, record):
    """Caller-authenticated metadata stub, only for callback contract conformance."""
    node = draft.operations[0].node_id
    logical = N(logical_artifact_id='artifact.exposed-cycle.' + node, payload_schema=record.SCHEMA,
        content_sha256=record.fingerprint(), media_type='application/json', outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY)
    receipt = N(receipt_id='receipt.exposed-cycle.' + node, SCHEMA='empirical-lawhood/testing/exposed-cycle-receipt', VERSION='1.0.0',
                fingerprint=lambda: 'a' * 64, operational_status=OperationalStatus.SUCCEEDED, output_logical_artifacts=(logical,))
    artifact = N(logical=logical, materialization=N(size_bytes=len(record.canonical_bytes())))
    return {'records': {node: {node + '.product': record}}, 'receipts': {node: receipt}, 'outputs': {logical.logical_artifact_id: artifact}}


def _payloads(draft, records):
    by_hash = {row.fingerprint(): row.canonical_bytes() for row in records}
    return {'external-' + sha256(row.input_id.encode()).hexdigest()[:24] + '.json': by_hash[row.expected_content_sha256] for row in draft.external_inputs}


def test_exact_original_source_census_and_cutoff(sources):
    mechanism, _ = sources
    with pytest.raises(ValueError, match='source bytes'):
        replace(mechanism.sources[0], raw_utf8=mechanism.sources[0].raw_utf8 + ' ')
    with pytest.raises(ValueError, match='census'):
        replace(mechanism, sources=mechanism.sources[:-1])
    with pytest.raises(ValueError, match='cutoff'):
        replace(mechanism, cutoff='claimed-fresh')


def test_independent_balance_full_census_and_countermodel(model):
    assert model.disposition is AssessmentDisposition.SATISFIED
    assert len(model.check.results) == 16 and len(model.check.release_checks) == 216
    assert all(row.passed for row in model.check.release_checks)
    assert model.check.irreversible_release_cancellation and model.check.reverse_capture_release_dependence
    assert max(row.maximum_relative_discrepancy for row in model.check.release_checks) < D('1e-12')
    assert len(contracts.DEFAULT_SCENARIOS) == 36
    assert len(model.canonical_bytes()) < 200_000  # compact witness, not copies of primary papers
    assert decode_canonical_bytes(model.canonical_bytes(), contracts.CycleSupply, maximum_bytes=None) == model


def test_independent_balance_falsifies_corrupted_closed_form(monkeypatch):
    original = assessment.finite_gas_flux
    monkeypatch.setattr(assessment, 'finite_gas_flux', lambda rates, gas: original(rates, gas) * D('1.02'))
    check = assessment.assess_procedure()
    assert check.disposition is AssessmentDisposition.FALSIFIED
    assert any(not row.passed for row in check.results)


@pytest.mark.parametrize('v,c,o,k,s,expected', [
    ('1', '0', '0', '2', '1', (None, None)),
    ('10', '5', '0', '1', '6', (None, None)),
    ('4', '0', '3', '1.1', '.5', (D('4.4')/D('3.9'), D(3))),
    ('10', '5', '0', '1', '4', (D(10), None)),
])
def test_independent_finite_release_interval_handles_strict_limits_and_specificity_headroom(v, c, o, k, s, expected):
    scenario = contracts.LatentScenario('scenario.exposed-interval', D(v), D(c), D(o))
    actual = contracts.finite_release_interval(scenario, D(k), D(s))
    if expected[0] is None:
        assert actual == expected
    else:
        assert abs(actual[0] - expected[0]) < D('1e-25') and actual[1] == expected[1]


def test_pure_worker_consumes_exact_config_source_and_product_census(sources, model):
    from empirical_lawhood.runtime.artifacts import ArtifactProfile
    from empirical_lawhood.runtime.execution import WorkerInputKind
    draft = drafts.supply_draft(sources[0])
    config = decode_canonical_bytes(draft.operations[0].config_payload.encode(), contracts.CycleOperationConfig, maximum_bytes=None)
    node = draft.operations[0].node_id
    def context(selected):
        inputs = tuple(N(payload_schema=row.SCHEMA, size_bytes=len(row.canonical_bytes()), media_type='application/json',
            kind=WorkerInputKind.EXTERNAL, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
            read=row.canonical_bytes, close=lambda: None) for row in (selected, sources[0]))
        return N(task_id=node, permissions=owner.operation_manifests()[1].permissions, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
            resource_budget=owner.BUDGET, input_ports=inputs,
            config=N(config_id=config.config_id, content_sha256=config.fingerprint()),
            output_ports=(N(output_id=node+'.product', payload_schema=contracts.CycleSupply.SCHEMA,
                            profile=ArtifactProfile.CANONICAL_JSON, media_type='application/json'),))
    result = owner.CycleRunner('supply').execute(context(config))
    assert result.outputs[0].payload == model.canonical_bytes()
    with pytest.raises(ValueError, match='immutable config'):
        owner.CycleRunner('supply').execute(context(replace(config, successor=contracts.CycleInstanceInput('instance.unselected',
            ObjectIdentity('input.unselected', portfolio.SourceAudit.SCHEMA, '1.0.0', 'a'*64)))))


def test_source_only_inquiry_exposes_sources_without_running_selected_science(sources, monkeypatch):
    initial = drafts.supply_draft(sources[0])
    def refused(*args, **kwargs):
        raise AssertionError('source-only inquiry cannot evaluate the selected cycle investigation')
    monkeypatch.setattr(assessment, 'supply', refused)
    monkeypatch.setattr(assessment, 'assess_procedure', refused)
    bindings = drafts.inquiry_evidence_projector(initial, _payloads(initial, (sources[0],)), {'records': {}})
    assert len(bindings) == 1 and bindings[0].scope.quantity_ids == ('original-source-bytes',)


def test_distinct_actual_macro_uses_preserve_all_adverse_results_and_unknown_biology(uses):
    first, second = uses
    assert [row.candidate.candidate_id for row in first.anchors[::2]] == ['gp.wt', 'wilson2017-row17']
    assert [row.candidate.candidate_id for row in second.anchors[::2]] == ['nt.a369.t391i', 'potato.ps3', 'potato.pst']
    assert second.supplier == contracts.identity(first)
    assert first.scope == second.scope and first.model == second.model
    for use in uses:
        assert use.biological_disposition is AssessmentDisposition.UNEVALUABLE
        assert all(len(anchor.scenarios) == 36 for anchor in use.anchors)
        assert all(len(row.samples) == 6 for anchor in use.anchors for row in anchor.scenarios)
        assert any(not row.necessities.finite_release_can_meet_joint_targets for anchor in use.anchors for row in anchor.scenarios)
    donor = next(anchor for anchor in first.anchors if anchor.candidate.candidate_id == 'wilson2017-row17' and anchor.reference[0] == 'radiometric')
    assert all(row.irreversible_route_excluded for row in donor.scenarios if row.scenario.carbon_u == row.scenario.oxygen_u == 0)
    assert any(row.necessities.finite_release_can_meet_joint_targets for row in donor.scenarios if row.scenario.carbon_u > row.scenario.oxygen_u)
    assert decode_canonical_bytes(second.canonical_bytes(), contracts.CycleUseProduct, maximum_bytes=None) == second
    with pytest.raises(ValueError, match='biological admission'):
        replace(first, biological_disposition=AssessmentDisposition.SATISFIED)
    with pytest.raises(ValueError, match='denominator'):
        replace(first, anchors=first.anchors[:-1])


def test_source_macro_unknown_endpoint_and_freshness_substitutions_refuse(sources, model, queries, uses):
    source = sources[1]
    with pytest.raises(ValueError, match='macro source'):
        assessment.assess_use(model, replace(source, input_id='input.changed-original-source-wrapper'), queries[0])
    unknown = replace(queries[0], candidate_ids=('gp.i95m',))
    with pytest.raises(ValueError, match='unknown macro endpoints'):
        assessment.assess_use(model, source, unknown)
    with pytest.raises(ValueError, match='distinct'):
        drafts.reuse_draft(uses[0], queries[0])
    with pytest.raises(ValueError, match='census'):
        replace(queries[0], scenarios=queries[0].scenarios[:-1])


def test_registered_singleton_supply_use_reuse_and_four_phase_assessments(sources, model, queries, uses):
    initial = drafts.supply_draft(sources[0], successor=queries[0], reuse_successor=queries[1])
    compile_complete_draft(initial, owner)
    first_parent = portable_parent(model)
    first = drafts.use_draft(model, queries[0], parent=first_parent, successor=queries[1])
    compile_complete_draft(first, owner)
    product = uses[0]
    second_parent = drafts.describe_contributions(first, _metadata_products(first, product))[0]
    second = drafts.reuse_draft(product, queries[1], parent=second_parent)
    compile_complete_draft(second, owner)
    for draft, record in ((first, product), (second, uses[1])):
        projected = project_recursive_assessments(draft=draft, registrations=owner.operation_registrations(),
            outputs={(draft.operations[0].node_id, 'product'): record})
        assert {row.phase for row in projected} == set(AssessmentPhase)
        assert all(row.disposition is AssessmentDisposition.SATISFIED for row in projected)
        assert all(row.evidence == (contracts.identity(record),) for row in projected)
        wrong = replace(draft.requirements[0], condition='Unassessed biological improvement')
        with pytest.raises(ValueError, match='condition'):
            owner.project_cycle_assessments(record, wrong, draft.connections[0])


def test_exact_registered_successor_chain_and_receipt_substitution_refusal(sources, model, queries, uses):
    initial = drafts.supply_draft(sources[0], successor=queries[0], reuse_successor=queries[1])
    products = _metadata_products(initial, model)
    first_parent = drafts.describe_contributions(initial, products)[0]
    first = drafts.next_wave_builder(initial, first_parent, products)
    first_config = decode_canonical_bytes(first.operations[0].config_payload.encode(), contracts.CycleOperationConfig, maximum_bytes=None)
    assert first_config.successor == queries[1]
    products2 = _metadata_products(first, uses[0])
    second_parent = drafts.describe_contributions(first, products2)[0]
    second = drafts.next_wave_builder(first, second_parent, products2)
    assert second.selected_operation_ids == ('rubisco-cycle-constraints.reuse',)
    assert next(row for row in second.external_inputs if row.input_id.endswith('.supplier')).scientific_role == 'OUTCOME'
    products3 = _metadata_products(second, uses[1])
    third_parent = drafts.describe_contributions(second, products3)[0]
    assert drafts.next_wave_builder(second, third_parent, products3) is None
    products['receipts'][initial.operations[0].node_id].output_logical_artifacts[0].content_sha256 = 'b' * 64
    with pytest.raises(ValueError, match='receipt'):
        drafts.describe_contributions(initial, products)


def test_code_owned_original_scopes_full_binding_census_and_actual_outcome(sources, model, queries, uses):
    from empirical_lawhood.planning.recursive_input_origins import RecursiveInputOrigin, RecursiveInputOriginKind, RecursiveInputOrigins
    parent = portable_parent(model)
    use = drafts.use_draft(model, queries[0], parent=parent)
    product = parent.products[0]
    origins = RecursiveInputOrigins(tuple(sorted((RecursiveInputOrigin(row.input_id, RecursiveInputOriginKind.CONTRIBUTION,
        row.expected_content_sha256, product.role.value, ObjectIdentity.from_record(parent.contribution_id, parent), product.product_id, product.producing_receipt)
        if row.input_id.endswith('.supplier') else RecursiveInputOrigin(row.input_id, RecursiveInputOriginKind.SOURCE,
            row.expected_content_sha256, row.scientific_role) for row in use.external_inputs), key=lambda row: row.input_id)))
    origins.validate_draft(use)
    products = _metadata_products(use, uses[0])
    bindings = drafts.inquiry_evidence_projector(use, _payloads(use, (model, sources[1], queries[0])), products)
    assert len(bindings) == 4 and all(row.independent_unit_ids == () for row in bindings)
    supplier = next(row for row in bindings if row.binding_id.endswith('.supplier'))
    macro = next(row for row in bindings if row.binding_id.endswith('.macro-source'))
    assert supplier.scope == model.scope and macro.scope == portfolio.original_source_scope(sources[1])
    spec = N(endpoint=model.scope, distinguishing_assessment=use.operations[0].config_identity)
    assert drafts.inquiry_outcome_projector(use, spec, products) == 'useful-supply'
    assert drafts.inquiry_outcome_projector(use, spec, {'records': {}}) == 'unresolved'
    with pytest.raises(ValueError, match='endpoint'):
        drafts.inquiry_endpoint_validator(use, replace(model.scope, receiver_id='receiver.alias'))
    wrong = replace(uses[0], supplier=replace(uses[0].supplier, object_id='substituted.supplier'))
    with pytest.raises(ValueError, match='substitutes supplier'):
        drafts.inquiry_outcome_projector(use, spec, _metadata_products(use, wrong))
