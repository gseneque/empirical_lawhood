# SPDX-License-Identifier: MPL-2.0
"""Independent current-use assessment; synthetic custody below is arithmetic-only."""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.adoption import CAPABILITY, CurrentResponseUse, ResponseAdoptionConfig, adoption_assessments, adoption_connection, assess_retained_response, identity
from empirical_lawhood.domains.rubisco.rubisco_response.adoption_operation import operation_declaration
from empirical_lawhood.domains.rubisco.rubisco_response.adoption_translation import response_adoption_draft, response_adoption_origins, scientific_work
from empirical_lawhood.domains.rubisco.rubisco_response.disclosed_examples import disclosed_study
from empirical_lawhood.domains.rubisco.rubisco_response.requirements import scientific_scope
from empirical_lawhood.domains.rubisco.rubisco_response.study_science import assess_response_study, predict_response_study
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import ContributionRole
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.science.inquiry.scientific_contributions import ContributionManifest, ContributionProduct
from empirical_lawhood.storage.contracts.artifacts import CanonicalTaskReceipt
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave


def arithmetic_fixture():
    """These receipt references test mathematics only, never real adoption."""
    original = disclosed_study()
    prediction = predict_response_study(original, prediction_id="prediction.arithmetic-fixture")
    assessment = assess_response_study(original, prediction, assessment_id="assessment.arithmetic-fixture")
    products = []
    for name, record, role in (("prediction", prediction, ContributionRole.INSTANCE_PRODUCT),
                               ("assessment", assessment, ContributionRole.RETAINED_ANALYSIS_INPUT)):
        record_id = record.identity if name == "prediction" else identity(record, "assessment_id")
        products.append(ContributionProduct("product.arithmetic-fixture." + name, record_id,
            ArtifactIdentity("artifact.arithmetic-fixture." + name, "synthetic-arithmetic-only", record.SCHEMA,
                record.fingerprint(), "application/json", len(record.canonical_bytes())),
            ObjectIdentity("receipt.arithmetic-fixture." + name, CanonicalTaskReceipt.SCHEMA,
                CanonicalTaskReceipt.VERSION, sha256(name.encode()).hexdigest()),
            role, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY))
    parent = ContributionManifest("contribution.arithmetic-fixture", original.question, "Synthetic references, no primary custody",
        scientific_scope(original), tuple(sorted(products, key=lambda row: row.product_id)),
        (identity(assessment, "assessment_id"),), ())
    current = replace(original, study_id="study.current.stricter-criterion",
        decisions=tuple(replace(row, minimum_turnover_ratio=D(2))
            if row.case.object_id.endswith("candidate") else row for row in original.decisions))
    config = ResponseAdoptionConfig("config." + CAPABILITY, original, current, parent, *products)
    return config, prediction, assessment


def _compile(draft):
    declaration = operation_declaration()
    return compile_recursive_wave(draft=draft, registrations=(declaration.registration(),),
        registry=CapabilityRegistry("registry.response-adoption", (declaration.manifest(),)),
        implementation_commit="a" * 40, output_codecs=declaration.record_codecs)


def test_new_criterion_reassesses_original_points_without_producer_or_new_units(monkeypatch):
    config, prediction, assessment = arithmetic_fixture()
    raw = prediction.canonical_bytes()
    def forbidden(*args, **kwargs):
        raise AssertionError("current use called an original producer")
    monkeypatch.setattr("empirical_lawhood.domains.rubisco.rubisco_response.study_science.predict_response_study", forbidden)
    monkeypatch.setattr("empirical_lawhood.domains.rubisco.rubisco_response.paired_prediction.predict_paired_rates", forbidden)
    result = assess_retained_response(config, prediction, assessment, use_id="use.current.adverse")
    assert assessment.conditional_candidate_action == "ADVANCE"
    assert result.current_assessment.conditional_candidate_action == "DEPRIORITIZE"
    assert result.original_prediction == prediction and prediction.canonical_bytes() == raw
    assert result.current_prediction.predictions == prediction.predictions
    assert result.current_prediction.study != prediction.study
    assert result.current_assessment.combined_milestone == "OPEN"
    assert result.fresh_independent_units == result.new_native_acquisitions == 0
    assert decode_canonical_bytes(result.canonical_bytes(), CurrentResponseUse, maximum_bytes=2_000_000) == result
    phases = adoption_assessments(result, *adoption_connection(config))
    assert len(phases) == 4 and all(row.disposition.value == "SATISFIED" for row in phases)
    assert all(row.evidence == (result.identity,) for row in phases)


@pytest.mark.parametrize("change", ["supply", "exposure", "receipt", "scope", "assessment-product"])
def test_adoption_refuses_evidence_receipt_and_scope_substitution(change):
    config, prediction, assessment = arithmetic_fixture()
    with pytest.raises(ValueError):
        if change == "supply":
            altered = replace(config.current_science.supplies[0], supply_id="supply.substituted")
            replace(config, current_science=replace(config.current_science, supplies=(altered, *config.current_science.supplies[1:])))
        elif change == "exposure":
            replace(config, current_science=replace(config.current_science, evidence_scope="PROSPECTIVE_REQUIRED"))
        elif change == "receipt":
            replace(config, prediction=replace(config.prediction, producing_receipt=config.assessment.producing_receipt))
        elif change == "scope":
            replace(config, parent=replace(config.parent, scope=replace(config.parent.scope, source_id="source.substituted")))
        else:
            assess_retained_response(config, prediction, replace(assessment, conditional_candidate_action="HOLD"), use_id="use.substituted")


def test_adoption_compiles_complete_original_contribution_inputs_and_scientific_connection():
    config, *_ = arithmetic_fixture()
    draft = response_adoption_draft(config)
    assert len(_compile(draft).execution_plan.tasks) == 1
    origins = response_adoption_origins(draft)
    assert {row.producing_receipt for row in origins.inputs} == {
        config.prediction.producing_receipt, config.assessment.producing_receipt}
    assert {row.product_id for row in origins.inputs} == {config.prediction.product_id, config.assessment.product_id}
    assert scientific_work(draft, CAPABILITY).scope.receiver_id == CAPABILITY
    assert draft.contribution_parents == (config.parent,)
    with pytest.raises(ValueError):
        _compile(replace(draft, contribution_parents=()))
    with pytest.raises(ValueError):
        _compile(replace(draft, links=draft.links[:-1]))
    with pytest.raises(ValueError):
        _compile(replace(draft, development_study=replace(draft.development_study,
            scientific_operands=tuple(row for row in draft.development_study.scientific_operands
                                      if row != config.prediction.producing_receipt))))
