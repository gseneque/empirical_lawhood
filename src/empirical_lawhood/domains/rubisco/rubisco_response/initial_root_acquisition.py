# SPDX-License-Identifier: MPL-2.0
"""Root-to-omission mapping and explicit unexecuted workload scenarios.

The shared work-cost owner retains measurements. These records describe
conditional forecasts only; unknown preparation and correction work stay open.
"""

from dataclasses import dataclass
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_nonempty, validate_stable_id
from empirical_lawhood.execution.work_costs import WorkCostAccount
from empirical_lawhood.domains.rubisco.rubisco_response.initial_model_records import interval
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_records import InitialRootAnalysisInputs
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_requirements import initial_root_requirement_graph, reconstruct_assessment
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact, identities
from empirical_lawhood.domains.rubisco.rubisco_response.paired_receiver_bound import PairedReceiverBoundInput, PairedReceiverBound, assess_paired_receiver_bound


@dataclass(frozen=True, slots=True)
class InitialRootForceScenario(CanonicalRecord):
    """A stated workload, not a prepared native task or a performance bound."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-root-force-scenario'
    scenario_id: str
    description: str
    complete_force_calls: int | None
    historical_seconds_per_call: tuple[Exact, Exact] | None
    historical_usd_per_hour: Exact | None
    observation_sources: tuple[ObjectIdentity, ...]
    assumptions: tuple[str, ...]
    unpriced_requirement_ids: tuple[str, ...]
    scope: str = 'UNEXECUTED_WORKLOAD_SCENARIO_NOT_A_TOTAL_BUDGET_OR_PERFORMANCE_BOUND'

    def __post_init__(self):
        validate_stable_id(self.scenario_id)
        validate_nonempty(self.description, field_name='scenario description')
        if self.complete_force_calls is not None and (type(self.complete_force_calls) is not int or self.complete_force_calls < 0):
            raise ValueError('root scenario requires an explicit nonnegative force count or unknown')
        if self.historical_seconds_per_call is not None:
            interval(self.historical_seconds_per_call, positive=True)
        if self.historical_usd_per_hour is not None:
            exact(self.historical_usd_per_hour, Exact)
            if self.historical_usd_per_hour.fraction <= 0:
                raise ValueError('root scenario needs a positive explicitly historical price')
        identities(self.observation_sources)
        if type(self.assumptions) is not tuple or not self.assumptions:
            raise ValueError('root cost scenario must state its workload, sharing and extrapolation premises')
        for assumption in self.assumptions:
            validate_nonempty(assumption, field_name='scenario assumption')
        require_sorted_unique_strings(self.unpriced_requirement_ids, field_name='unpriced requirements')
        if self.scope != 'UNEXECUTED_WORKLOAD_SCENARIO_NOT_A_TOTAL_BUDGET_OR_PERFORMANCE_BOUND':
            raise ValueError('root cost scenario cannot become a measured cost or execution allowance')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.scenario_id, self)


def _rational(value):
    value = Fraction(value)
    return {'numerator': value.numerator, 'denominator': value.denominator}


def price_initial_root_force_scenario(scenario):
    exact(scenario, InitialRootForceScenario)
    seconds = None if scenario.complete_force_calls is None or scenario.historical_seconds_per_call is None else tuple(
        value.fraction * scenario.complete_force_calls for value in scenario.historical_seconds_per_call)
    dollars = None if seconds is None or scenario.historical_usd_per_hour is None else tuple(
        value * scenario.historical_usd_per_hour.fraction / 3600 for value in seconds)
    return dict(scenario=scenario.identity.to_document(), description=scenario.description,
        complete_force_calls=scenario.complete_force_calls,
        historical_regime_seconds=None if seconds is None else tuple(map(_rational, seconds)),
        historical_rate_usd=None if dollars is None else tuple(map(_rational, dollars)),
        full_delivery_cost=None, unpriced_requirement_ids=scenario.unpriced_requirement_ids,
        assumptions=scenario.assumptions, scope=scenario.scope, execution_authorized=False)


def assess_initial_root_acquisition(*, analysis, result, assessment, measured_account, scenarios=(),
        receiver_bound_input=None, receiver_bound_result=None):
    """Preserve exact decision proofs; no scenario manufactures an omitted call."""
    exact(analysis, InitialRootAnalysisInputs)
    reconstruct_assessment(analysis, result, assessment)
    if assessment.numerical_disposition is not AssessmentDisposition.SATISFIED:
        raise ValueError('acquisition assessment requires a correctly reconstructed root')
    exact(measured_account, WorkCostAccount)
    if type(scenarios) is not tuple:
        raise TypeError('root scenarios require an immutable finite selection')
    require_sorted_unique_ids(scenarios, attribute='scenario_id', field_name='scenarios')
    for scenario in scenarios:
        exact(scenario, InitialRootForceScenario)
    graph = initial_root_requirement_graph(analysis, result=result)
    requirements = {row.requirement_id for row in graph.requirements}
    sources = {measured_account.identity, *(row.identity for row in measured_account.evidence),
        *(row.record_identity for row in measured_account.evidence if row.record_identity is not None)}
    for scenario in scenarios:
        if not set(scenario.observation_sources).issubset(sources) or not set(scenario.unpriced_requirement_ids).issubset(requirements):
            raise ValueError('root scenario changes its original cost sources or named prerequisite scope')
    if (receiver_bound_input is None) != (receiver_bound_result is None):
        raise ValueError('a scalar receiver shortcut requires its complete original input and result')
    receiver = None
    if receiver_bound_input is not None:
        exact(receiver_bound_input, PairedReceiverBoundInput)
        exact(receiver_bound_result, PairedReceiverBound)
        if receiver_bound_input.paired_case not in {row.case.identity for row in analysis.model.cases}:
            raise ValueError('scalar receiver shortcut changes the actual paired material scope')
        # Its original owner retains all correction, causality, coverage and
        # complete added-cost checks, including unknown-cost refusal.
        receiver = assess_paired_receiver_bound(receiver_bound_input, receiver_bound_result)
    omissions = tuple(dict(case_id=case.case_id, alternative_id=alternative.alternative_id,
        realization_id=row.realization_id, proof_result=result.identity.to_document(),
        proof_assessment=assessment.identity.to_document(), conditional_outcome=row.joint_outcome,
        omitted_operands=row.omitted_operands, mapped_native_work=None, avoided_cost=None)
        for case in result.cases for alternative in case.alternatives for row in alternative.realizations if row.omitted_operands)
    return dict(root=result.identity.to_document(), assessment=assessment.identity.to_document(),
        requirement_graph=graph.identity.to_document(), measured_work_account=measured_account.identity.to_document(),
        joint_outcome=result.joint_outcome, remaining_requirement_ids=result.decision_requirement_ids,
        original_remaining_requirement_ids=result.original_remaining_requirement_ids,
        decision_specific_omissions=omissions, scalar_receiver_assessment=receiver,
        scenarios=tuple(price_initial_root_force_scenario(row) for row in scenarios),
        remaining_total_cost=None, demonstrated_avoided_native_calls=0, demonstrated_net_saving=None,
        next_action='RESOLVE_NAMED_SCIENTIFIC_INPUTS' if result.decision_requirement_ids else 'RETAIN_SCOPED_CONDITIONAL_DECISION',
        native_acquisition_authorized=False, biological_predictive_validity='UNEVALUABLE')
