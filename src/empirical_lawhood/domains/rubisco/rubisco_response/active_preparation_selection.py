# SPDX-License-Identifier: MPL-2.0
"""Explicit paired preparation purchases within the original four-material plan."""

from dataclasses import dataclass, replace
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_selection import ConditionalActiveRelaxationSelection, MatchedActiveRelaxationPlan, validate_conditional_relaxation_selection
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact


@dataclass(frozen=True, slots=True)
class ActivePreparationPrefixSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/active-preparation-prefix-selection'
    selection_id: str
    plan: ObjectIdentity
    conditional: ConditionalActiveRelaxationSelection
    model_allowances: tuple[tuple[str, int], ...]
    checkpoint_rule: str = 'LAST_ACCEPTED_STATE_WITHIN_SELECTED_COMPLETE_RETURN_ALLOWANCE'
    initial_rule: str = 'ORIGINAL_SELECTED_SEED_WITH_COMPLETE_NATIVE_FORCE'
    continuation_rule: str = 'AUTHENTICATED_OPTIMIZER_STATE_AND_ALL_COMPLETED_EVALUATIONS_NO_UNKNOWN_CONTACT'
    scope: str = 'ONE_MATCHED_M1_CASE_FOUR_NESTED_STATE_POSITIONS_NOT_A_PREPARED_POPULATION'

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        exact(self.plan, ObjectIdentity)
        exact(self.conditional, ConditionalActiveRelaxationSelection)
        if (self.plan.object_schema != MatchedActiveRelaxationPlan.SCHEMA
                or self.conditional.plan != self.plan or len(self.conditional.state_census) != 1
                or type(self.model_allowances) is not tuple
                or any(type(row) is not tuple or len(row) != 2 for row in self.model_allowances)
                or tuple(row[0] for row in self.model_allowances) != ('m1-i95m', 'm1-wt')
                or any(type(row[1]) is not int or not 2 <= row[1] <= 8 for row in self.model_allowances)
                or sum(row[1] for row in self.model_allowances) > 10):
            raise ValueError('paired prefix changes its one-case denominator or ten-return purchase')
        if (self.checkpoint_rule != 'LAST_ACCEPTED_STATE_WITHIN_SELECTED_COMPLETE_RETURN_ALLOWANCE'
                or self.initial_rule != 'ORIGINAL_SELECTED_SEED_WITH_COMPLETE_NATIVE_FORCE'
                or self.continuation_rule != 'AUTHENTICATED_OPTIMIZER_STATE_AND_ALL_COMPLETED_EVALUATIONS_NO_UNKNOWN_CONTACT'
                or self.scope != 'ONE_MATCHED_M1_CASE_FOUR_NESTED_STATE_POSITIONS_NOT_A_PREPARED_POPULATION'):
            raise ValueError('paired prefix changes its safe handoff, continuation or evidence scope')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.selection_id, self)

    def allowance_for(self, model_name):
        for name, count in self.model_allowances:
            if name == model_name:
                return count
        raise ValueError('preparation prefix requests an unselected material')


def prepare_active_preparation_prefix(*, plan, conditional_selection,
                                      model_allowances=(('m1-i95m', 5), ('m1-wt', 5))):
    exact(plan, MatchedActiveRelaxationPlan)
    validate_conditional_relaxation_selection(plan, conditional_selection)
    provisional = ActivePreparationPrefixSelection('selection.active-prefix.pending', plan.identity,
        conditional_selection, model_allowances)
    return replace(provisional, selection_id='selection.active-prefix.' + provisional.fingerprint())


def validate_prefix_member(*, prefix, plan, model_name, conditional_selection):
    exact(prefix, ActivePreparationPrefixSelection)
    if (prepare_active_preparation_prefix(plan=plan, conditional_selection=conditional_selection,
            model_allowances=prefix.model_allowances) != prefix):
        raise ValueError('preparation prefix substitutes its original complete plan or selected state')
    return prefix.allowance_for(model_name)
