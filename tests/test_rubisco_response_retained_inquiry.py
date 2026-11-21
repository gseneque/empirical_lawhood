# SPDX-License-Identifier: MPL-2.0
"""Retained inquiry keeps full scientific requirements and exposed work scope."""

from dataclasses import replace
from decimal import Decimal

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.adoption_translation import response_adoption_draft
from empirical_lawhood.domains.rubisco.rubisco_response.disclosed_examples import disclosed_study
from empirical_lawhood.domains.rubisco.rubisco_response.retained_inquiry import retained_inquiry_specification
from empirical_lawhood.domains.rubisco.rubisco_response.requirements import response_requirement_graph
from empirical_lawhood.domains.rubisco.rubisco_response.recursive_translation import selected_configs
from empirical_lawhood.api.domain_composition.rubisco_response.inquiry import project_retained_response_inquiry
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import RobustInquirySpecification, ScientificOutcomeKind
from empirical_lawhood.science.models.time import CausalPhase, InformationCutoff
from tests.test_rubisco_response_adoption import arithmetic_fixture
from tests.test_rubisco_response_public import _prepare
from empirical_lawhood.domains.rubisco.rubisco_response.experiment_specification import response_experiment_specification


@pytest.mark.parametrize("adopted", [False, True])
def test_retained_question_preserves_every_combined_prerequisite(adopted, tmp_path):
    if adopted:
        config, *_ = arithmetic_fixture()
        draft = response_adoption_draft(config)
        study = config.current_science
    else:
        study = disclosed_study()
        draft = _prepare(response_experiment_specification(study), study, tmp_path).draft
        study = selected_configs(draft)["assess"].science
    specification = retained_inquiry_specification(draft)
    graph = response_requirement_graph(study)
    assert set(graph.requirements) <= set(specification.requirements)
    assert set(graph.connections) <= set(specification.connections)
    assert graph.root_requirement_id in specification.target.required_requirement_ids
    assert set(specification.required_requirement_closure) == {row.requirement_id for row in specification.requirements}
    assert {row.kind for row in specification.outcomes} == set(ScientificOutcomeKind)
    assert decode_canonical_bytes(specification.canonical_bytes(), RobustInquirySpecification,
                                  maximum_bytes=2_000_000) == specification
    with pytest.raises(ValueError, match="prerequisite"):
        replace(specification, requirements=tuple(row for row in specification.requirements
            if row.requirement_id != study.acceptance.matrix_handoff_requirement_id))


def test_retained_outcome_cannot_be_declared_pre_outcome_without_reading():
    cutoff = InformationCutoff("cutoff.invalid-retained", "clock.rubisco.physical-seconds",
                               CausalPhase.PRE_ACTION, Decimal(0))
    with pytest.raises(ValueError, match="post-outcome"):
        project_retained_response_inquiry(directory="does-not-exist", information_cutoff=cutoff, artifact_writer=None)


def assert_actual_retained_projection(directory, plane, *, expected_attempts):
    from empirical_lawhood.science.inquiry.recursive_inquiry import InquiryCost
    from empirical_lawhood.science.inquiry.recursive_inquiry_policy import WorkBoundInquiryState
    from empirical_lawhood.science.inquiry.recursive_requirements import RequirementSupplyAssessment

    cutoff = InformationCutoff("cutoff.response-retained-outcome", "clock.rubisco.physical-seconds",
                               CausalPhase.POST_OUTCOME, None)
    projected = project_retained_response_inquiry(directory=directory, information_cutoff=cutoff, artifact_writer=plane)
    state, spec = projected.state, projected.specification
    assert type(state) is WorkBoundInquiryState
    assert len(state.operational_census) == len(state.attempt_work_bindings) == expected_attempts
    assert all(attempt.status.value == "COMPLETED" for attempt in state.operational_census)
    assert all(binding.work is not None and binding.witness is not None for binding in state.attempt_work_bindings)
    assert all(event.cost == InquiryCost(None, None, None) for event in state.cost_events)
    assert all(not item.independent_unit_ids for item in state.stock)
    assert sum(item.product.object_schema == RequirementSupplyAssessment.SCHEMA for item in state.stock) == 4
    assert any("combined-milestone" in name for name in spec.target.required_requirement_ids)
    assert spec.question_requirement_id in {row.requirement_id for row in spec.requirements}
    return projected
