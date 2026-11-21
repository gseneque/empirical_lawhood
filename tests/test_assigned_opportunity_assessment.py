# SPDX-License-Identifier: MPL-2.0
"""Bounded disclosed author/assessor controls; no native or scientific acquisition."""

from dataclasses import dataclass, replace
from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import product
from types import SimpleNamespace
from typing import ClassVar

import pytest

from empirical_lawhood.methods.assigned_opportunity_assessment import bindings, design, science
from empirical_lawhood.methods.assigned_opportunity_assessment.examples import CASES, example_inputs
from empirical_lawhood.methods.assigned_opportunity_assessment.records import MAX_BYTES, NAMESPACE, OpportunityAssessment, OpportunityAuthorInput, OpportunityOutcomes
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess
from empirical_lawhood.science.experiments.experimental_design import UnitRoleAssignment
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.science.models.time import CausalPhase
from empirical_lawhood.design.inquiry_methods import InquiryAuthoringMode, InquiryEvidenceRole, MissingOpportunityRule
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave


def operands(case="positive", *, count=4):
    actor, outcomes = example_inputs(case, count=count)
    config = design.make_config(actor, outcomes)
    procedure = science.author(design.author_config(config), actor)
    return actor, outcomes, config, procedure


@pytest.mark.parametrize("case,expected", tuple(zip(CASES, ("SATISFIED", "FALSIFIED", "UNEVALUABLE", "UNEVALUABLE", "UNEVALUABLE"))))
def test_five_cases_keep_complete_dependent_census_and_independent_mathematical_extrema(case, expected):
    _, outcomes, config, procedure = operands(case)
    with localcontext() as context:
        context.prec = 2
        result = science.assess(config, procedure, outcomes)
    # Independent control: enumerate every endpoint completion of the missing
    # coordinates. No implementation reduction or population inference is used.
    options = tuple((Fraction(row.views[0].value),) if row.status == "OBSERVED" and len({v.value for v in row.views}) == 1
                    else (Fraction(0), Fraction(1)) for row in outcomes.rows)
    means = [sum(completion, Fraction(0)) / len(completion) for completion in product(*options)]
    assert Fraction(*result.lower_ratio) == min(means)
    assert Fraction(*result.upper_ratio) == max(means)
    assert result.disposition == expected
    assert len(result.outcomes.rows) == 4
    assert config.assessment.allocation.unit_ids() == (outcomes.source.independent_unit_id,)
    assert len({r.dependence_root for r in result.outcomes.rows}) == 1
    assert decode_canonical_bytes(result.canonical_bytes(), OpportunityAssessment, maximum_bytes=MAX_BYTES) == result
    phases = bindings.assessment_projector(result, *design.scientific_contract(config.source))
    assert {p.phase.value: p.disposition.value for p in phases} == {
        "PROCEDURE": "SATISFIED", "INSTANCE": "SATISFIED", "ADMISSION": "SATISFIED", "JOINED": expected}
    assert all(p.evidence_ceiling.value == "NON_PROMOTABLE" for p in phases)
    if expected != "SATISFIED":
        assert result.reason_codes


def test_exact_nonterminating_ratio_and_enclosure_edge_decisions():
    actor, outcomes = example_inputs(count=3)
    outcomes = replace(outcomes, rows=(outcomes.rows[0], *(replace(row,
        views=tuple(replace(v, value=Decimal(0)) for v in row.views)) for row in outcomes.rows[1:])))
    config = design.make_config(actor, outcomes)
    result = science.assess(config, science.author(design.author_config(config), actor), outcomes)
    assert result.lower_ratio == result.upper_ratio == (1, 3)
    assert result.disposition == "FALSIFIED"
    # A missing outcome does not force an invented failure. Its sharp interval
    # can decide a predicate whose threshold is reached by every completion.
    actor, outcomes = example_inputs("insufficient")
    actor = replace(actor, requested_threshold=Decimal("0.25"))
    config = design.make_config(actor, outcomes)
    result = science.assess(config, science.author(design.author_config(config), actor), outcomes)
    assert result.disposition == "SATISFIED" and "MISSING_OPPORTUNITIES_RETAINED" in result.reason_codes
    config = design.make_config(actor, outcomes, missingness=MissingOpportunityRule.UNEVALUABLE)
    assert science.assess(config, science.author(design.author_config(config), actor), outcomes).disposition == "UNEVALUABLE"


def test_invalid_observed_value_retains_original_value_and_is_unevaluable():
    actor, outcomes = example_inputs()
    changed = replace(outcomes.rows[0], views=tuple(replace(v, value=Decimal(2)) for v in outcomes.rows[0].views))
    outcomes = replace(outcomes, rows=(changed, *outcomes.rows[1:]))
    config = design.make_config(actor, outcomes)
    result = science.assess(config, science.author(design.author_config(config), actor), outcomes)
    assert result.disposition == "UNEVALUABLE" and result.outcomes.rows[0].views[0].value == 2
    assert "UNEVALUABLE_OPPORTUNITIES_RETAINED" in result.reason_codes


@pytest.mark.parametrize("change", ("duplicate-unit", "root-alias"))
def test_shared_root_cannot_become_independent_opportunities_through_labels(change):
    _, _, config, _ = operands()
    contract = config.assessment
    unit = replace(contract.allocation.units[0], unit_id="unit.other")
    allocation = replace(contract.allocation, units=tuple(sorted((*contract.allocation.units, unit), key=lambda u: u.unit_id)),
        roles=tuple(sorted((*contract.allocation.roles, UnitRoleAssignment(unit.unit_id, "development")), key=lambda u: u.unit_id)))
    first = contract.opportunities[0]
    root = replace(first.dependence_root, object_id="source.renamed") if change == "root-alias" else first.dependence_root
    changed = replace(first, independent_unit_id=unit.unit_id, dependence_root=root)
    with pytest.raises(ValueError, match="dependence root"):
        replace(contract, allocation=allocation, opportunities=(changed, *contract.opportunities[1:]))


@pytest.mark.parametrize("change", ("root", "unit", "view", "cutoff", "denominator"))
def test_original_source_joins_reject_relabeling_and_omission(change):
    _, outcomes, _, _ = operands()
    first = outcomes.rows[0]
    with pytest.raises(ValueError):
        if change == "root":
            replace(outcomes, rows=(replace(first, dependence_root=replace(first.dependence_root, object_id="other.root")), *outcomes.rows[1:]))
        elif change == "unit":
            replace(outcomes, rows=(replace(first, independent_unit_id="unit.renamed-opportunity"), *outcomes.rows[1:]))
        elif change == "view":
            replace(outcomes, rows=(replace(first, views=tuple(replace(v, value_id="other." + v.value_id) for v in first.views)), *outcomes.rows[1:]))
        elif change == "cutoff":
            replace(outcomes, rows=(replace(first, availability=replace(first.availability, available_at=Decimal(999))), *outcomes.rows[1:]))
        else:
            replace(outcomes, rows=outcomes.rows[:-1])


@pytest.mark.parametrize("change", ("diagnostics", "future", "sealed", "activation", "release"))
def test_author_role_actual_time_and_activation_refuse_before_calculation(change, monkeypatch):
    _, _, config, _ = operands()
    entry = config.author.inputs[0]
    monkeypatch.setattr(science, "author", lambda *a: pytest.fail("author calculation entered"))
    with pytest.raises((ValueError, TypeError)):
        if change == "diagnostics":
            replace(config.author, inputs=(replace(entry, role=InquiryEvidenceRole.EVALUATOR_DIAGNOSTIC),))
        elif change == "future":
            replace(config.author, inputs=(replace(entry, availability=replace(entry.availability,
                phase=CausalPhase.PREPARATION, available_at=Decimal(100))),))
        elif change == "sealed":
            replace(config.author, inputs=(replace(entry, availability=replace(entry.availability,
                outcome_access=OutcomeAccess.EVALUATION_SEALED)),))
        elif change == "activation":
            replace(config.author, activation=replace(config.author.activation, coordinate=Decimal(-1)))
        else:
            replace(entry, role=InquiryEvidenceRole.AUTHORIZED_LATER_RELEASE)


@pytest.mark.parametrize("change", ("consumer", "rule", "threshold", "method", "mode", "revision"))
def test_frozen_consumer_and_permitted_author_contract_refuse_substitutions(change):
    _, outcomes, config, procedure = operands()
    with pytest.raises((ValueError, TypeError)):
        if change in ("consumer", "rule"):
            frozen = procedure.author_contract.frozen_consumer
            field = "consumer" if change == "consumer" else "parameter_rule"
            frozen = replace(frozen, **{field: replace(getattr(frozen, field), object_id="other." + field)})
            changed = replace(procedure, author_contract=replace(procedure.author_contract, frozen_consumer=frozen))
            science.assess(config, changed, outcomes)
        elif change == "threshold":
            science.assess(config, replace(procedure, parameters=(replace(procedure.parameters[0], value=Decimal("0.6")),)), outcomes)
        elif change == "method":
            replace(procedure, selected_methods=(replace(procedure.selected_methods[0], implementation_sha256="f" * 64),))
        elif change == "mode":
            replace(config, author=replace(config.author, mode=InquiryAuthoringMode.PROCEDURE_CONSTRUCTION))
        else:
            replace(config, assessment=replace(config.assessment, method=replace(config.assessment.method, capability_version="2.0.0")))


def test_later_evidence_and_parameter_selection_create_separate_successor_without_revising_procedure():
    actor, outcomes, config, original = operands()
    before = original.canonical_bytes()
    successor_actor = replace(actor, record_id="input.successor.actor", requested_threshold=Decimal("0.75"))
    successor = design.make_config(successor_actor, outcomes)
    later = science.author(design.author_config(successor), successor_actor)
    assert later.identity != original.identity and original.canonical_bytes() == before
    assert design.scientific_root(config).claims[0] != design.scientific_root(successor).claims[0]
    with pytest.raises(ValueError, match="procedure"):
        science.assess(config, later, outcomes)


def compiler_fixture(case="positive"):
    actor, outcomes = example_inputs(case)
    draft, sources = design.lower(actor, outcomes)
    declarations = bindings.operation_declarations()
    kwargs = dict(registry=CapabilityRegistry("test.opportunity.registry", tuple(d.manifest() for d in declarations)),
        registrations=tuple(d.registration() for d in declarations), implementation_commit="a" * 40,
        output_codecs=bindings.record_codecs())
    return draft, sources, declarations, kwargs


def test_registered_compiler_keeps_one_unit_and_causal_two_operation_graph():
    draft, _, declarations, kwargs = compiler_fixture()
    compiled = compile_recursive_wave(draft=draft, **kwargs)
    tasks = {t.task_id: t for t in compiled.execution_plan.tasks}
    assert len(tasks) == 2 and len(draft.development_study.assigned_unit_ids) == 1
    assert tasks[NAMESPACE + ".assess"].dependency_task_ids == (NAMESPACE + ".author",)
    assert all(not d.execution_properties.native_effect for d in declarations)
    for changed in (replace(draft, connections=()), replace(draft, links=tuple(replace(link,
            scientific_role="OUTCOME") if link.consumer_input_id == "actor" else link for link in draft.links))):
        with pytest.raises(ValueError):
            compile_recursive_wave(draft=changed, **kwargs)


def test_worker_cannot_supply_evaluator_body_to_actor_port():
    actor, outcomes, config, _ = operands()
    config = design.author_config(config)
    closed = []
    def port(value):
        return SimpleNamespace(payload_schema=value.SCHEMA, media_type="application/json", outcome_access=design.ACCESS,
            read=value.canonical_bytes, close=lambda: closed.append(value.SCHEMA))
    context = SimpleNamespace(input_ports=(port(config), port(outcomes)), task_id=config.node_id,
        config=SimpleNamespace(config_id=config.config_id, content_sha256=config.fingerprint()),
        resource_budget=design.BUDGET, permissions=design.PERMISSIONS, outcome_access=design.ACCESS)
    declaration = next(d for d in bindings.operation_declarations() if d.capability_key.endswith(".author"))
    with pytest.raises(ValueError, match="actor/evaluator"):
        declaration.runner_factory().execute(context)
    assert len(closed) == 2
    assert type(actor) is OpportunityAuthorInput and type(outcomes) is OpportunityOutcomes


@dataclass(frozen=True, slots=True)
class DisclosedLogical(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/opportunity-logical"
    payload_schema: str
    content_sha256: str


@dataclass(frozen=True, slots=True)
class DisclosedReceipt(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/opportunity-receipt"
    receipt_id: str
    run_id: str
    task_id: str
    operational_status: OperationalStatus
    output_logical_artifacts: tuple[DisclosedLogical, ...]


def projection_fixture(case="positive"):
    actor, outcomes, config, procedure = operands(case)
    result = science.assess(config, procedure, outcomes)
    draft, _ = design.lower(actor, outcomes)
    products = {"records": {}, "receipts": {}}
    for phase, value in (("author", procedure), ("assess", result)):
        node = NAMESPACE + "." + phase
        products["records"][node] = {node + ".product": value}
        products["receipts"][node] = DisclosedReceipt("receipt." + node, "run.disclosed-fixture", node,
            OperationalStatus.SUCCEEDED, (DisclosedLogical(value.SCHEMA, value.fingerprint()),))
    operation = next(op for op in draft.operations if op.node_id.endswith(".assess"))
    specification = SimpleNamespace(distinguishing_assessment=operation.config_identity,
        endpoint=config.assessment.scope, target=SimpleNamespace(scope=config.assessment.scope,
        required_claims=tuple(ObjectIdentity.from_record(c.claim_id, c) for c in draft.development_study.claims)))
    return draft, products, specification


def test_registered_claim_projection_retains_exact_current_claim_and_separate_status_axes():
    draft, products, specification = projection_fixture("adverse")
    projected, = bindings.claim_assessment_projector(draft, specification, products)
    assert projected.disposition.value == "FALSIFIED"
    assert projected.independent_unit_ids == ("unit.original-dependent-sequence",)
    assert len(projected.nested_view_ids) == 2 and projected.evidence_ceiling.value == "NON_PROMOTABLE"
    assert bindings.outcome_projector(draft, specification, products) == "scoped-failure"
    wrong = SimpleNamespace(**vars(specification), unused=None)
    wrong.target = SimpleNamespace(scope=specification.target.scope,
        required_claims=(replace(specification.target.required_claims[0], object_fingerprint="f" * 64),))
    assert bindings.claim_assessment_projector(draft, wrong, products) == ()
    wrong.target = SimpleNamespace(scope=replace(specification.target.scope, receiver_id="receiver.other"),
        required_claims=specification.target.required_claims)
    with pytest.raises(ValueError, match="scope"):
        bindings.claim_assessment_projector(draft, wrong, products)
    receipt = products["receipts"][NAMESPACE + ".assess"]
    products["receipts"][NAMESPACE + ".assess"] = replace(receipt, output_logical_artifacts=(
        replace(receipt.output_logical_artifacts[0], content_sha256="f" * 64),))
    with pytest.raises(ValueError, match="receipt"):
        bindings.claim_assessment_projector(draft, specification, products)


def test_incomplete_producing_assessment_retains_unresolved_claim_without_numerical_result():
    draft, products, specification = projection_fixture()
    del products["records"][NAMESPACE + ".assess"]
    del products["receipts"][NAMESPACE + ".assess"]
    assert bindings.authenticated_assessment(draft, products) is None
    assert bindings.outcome_projector(draft, specification, products) == "unresolved"
    assert bindings.claim_assessment_projector(draft, specification, products) == ()


@pytest.mark.parametrize("status", ("PARTIAL", "SUCCEEDED"))
def test_public_partial_read_uses_compact_custody_without_inventing_science(status, monkeypatch):
    from empirical_lawhood.api import recursive_execution
    from empirical_lawhood.api.assigned_opportunity_assessment import read_assigned_opportunity_result
    draft, _, _ = projection_fixture("adverse")
    census = ({"task_id": NAMESPACE + ".author", "operational_status": "SUCCEEDED"},
              {"task_id": NAMESPACE + ".assess", "operational_status": "PENDING" if status == "PARTIAL" else "SUCCEEDED"})
    def compact(**options):
        assert options["allow_partial"] and options["terminal_product_format"] == "compact"
        return {"run_id": "run.disclosed-fixture", "status": status, "operational_census": census}, {}, draft, None
    monkeypatch.setattr(recursive_execution, "read_recursive_wave", compact)
    monkeypatch.setattr(bindings, "authenticated_assessment", lambda *a: pytest.fail("compact custody was treated as typed science"))
    report = read_assigned_opportunity_result(directory=None, artifact_writer=None, allow_partial=True)
    assert report["scientific_completion"] == "DEFERRED" and "claim_disposition" not in report
    assert report["operational_census"] == census and report["operational_status"] == status
    assert report["assigned_opportunities"] == 4 and report["independent_units"] == 1
    assert report["qualification"] == "NOT_ESTABLISHED"


def test_public_completed_read_keeps_the_actual_adverse_finding(monkeypatch):
    from empirical_lawhood.api import recursive_execution
    from empirical_lawhood.api.assigned_opportunity_assessment import read_assigned_opportunity_result
    draft, products, _ = projection_fixture("adverse")
    def complete(**options):
        assert not options["allow_partial"] and options["terminal_product_format"] == "documents"
        return {"run_id": "run.disclosed-fixture", "status": "SUCCEEDED"}, products, draft, None
    monkeypatch.setattr(recursive_execution, "read_recursive_wave", complete)
    report = read_assigned_opportunity_result(directory=None, artifact_writer=None)
    assert report["scientific_completion"] == "COMPLETED" and report["claim_disposition"] == "FALSIFIED"
    assert report["lower_ratio"] == report["upper_ratio"] == (0, 1) and len(report["opportunities"]) == 4


def test_declared_work_has_exact_scientific_identity_and_no_opportunity_unit_inflation():
    draft, _, _, _ = compiler_fixture()
    author = bindings.scientific_work(draft, NAMESPACE + ".author")
    assessor = bindings.scientific_work(draft, NAMESPACE + ".assess")
    assert author != assessor and len(author.scientific_operands) == 3 and len(assessor.scientific_operands) == 4
    assert author.scope == assessor.scope
    with pytest.raises(ValueError, match="absent"):
        bindings.scientific_work(draft, "opportunity.00")
