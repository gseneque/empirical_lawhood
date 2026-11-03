# SPDX-License-Identifier: MPL-2.0
"""Shared cold stage/kind contracts for distinct scientific lifecycles."""

from types import MappingProxyType

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from .capabilities import CapabilityKind
from .plans import PlanLane, ScientificStage

PROSPECTIVE_STAGE_KINDS: dict[ScientificStage, frozenset[CapabilityKind]] = {
    ScientificStage.PREPARE: frozenset({CapabilityKind.SOURCE, CapabilityKind.SIMULATOR}),
    ScientificStage.ACQUIRE: frozenset(
        {
            CapabilityKind.SOURCE,
            CapabilityKind.SIMULATOR,
            CapabilityKind.ACTUATOR,
            CapabilityKind.OBSERVATION_OPERATOR,
        }
    ),
    ScientificStage.TRANSFORM: frozenset({CapabilityKind.TRANSFORM}),
    ScientificStage.DEVELOP: frozenset(
        {
            CapabilityKind.ANALYSIS,
            CapabilityKind.PROSPECTIVE_NOMINATOR,
            # A prospective method may issue its frozen, development-visible
            # prediction roster here and adjudicate only in a later EVALUATE
            # task. Outcome-access and graph chronology remain independently
            # checked; this does not authorize target evidence in development.
            CapabilityKind.HYPOTHESIS_ADJUDICATOR,
            CapabilityKind.LAW_IDENTIFIER,
            CapabilityKind.RESPONSE_ALGEBRA_IDENTIFIER,
            CapabilityKind.CONTROLLER_SYNTHESIZER,
        }
    ),
    ScientificStage.FALSIFY: frozenset(
        {
            CapabilityKind.FALSIFIER,
            CapabilityKind.TRANSPORT_TESTER,
            CapabilityKind.DISCREPANCY_ESTIMATOR,
        }
    ),
    ScientificStage.QUALIFY: frozenset(
        {
            CapabilityKind.LAW_IDENTIFIER,
            CapabilityKind.NUMERICAL_QUALIFIER,
            CapabilityKind.OBSERVATION_OPERATOR,
            CapabilityKind.DISCREPANCY_ESTIMATOR,
        }
    ),
    ScientificStage.FREEZE: frozenset(
        {
            CapabilityKind.EVALUATOR,
            CapabilityKind.EXPERIMENT_DESIGNER,
            CapabilityKind.TRANSFORM,
            CapabilityKind.REPORTER,
        }
    ),
    ScientificStage.EVALUATE: frozenset(
        {CapabilityKind.EVALUATOR, CapabilityKind.HYPOTHESIS_ADJUDICATOR}
    ),
    ScientificStage.REVEAL: frozenset({CapabilityKind.EVALUATOR}),
    ScientificStage.SYNTHESIZE: frozenset(
        {
            CapabilityKind.ANALYSIS,
            CapabilityKind.ATLAS_ASSEMBLER,
            CapabilityKind.HYPOTHESIS_SYNTHESIZER,
            CapabilityKind.REPORTER,
        }
    ),
    ScientificStage.ADMISSION: frozenset(
        {CapabilityKind.ADMISSION_EVALUATOR, CapabilityKind.ONLINE_GATE_EVALUATOR}
    ),
    ScientificStage.CONTROLLER: frozenset(
        {CapabilityKind.CONTROLLER_SYNTHESIZER, CapabilityKind.ONLINE_GATE_EVALUATOR}
    ),
    ScientificStage.REPORT: frozenset({CapabilityKind.REPORTER}),
    ScientificStage.EXPLORE: frozenset(
        {
            CapabilityKind.ANALYSIS,
            CapabilityKind.ANOMALY_DETECTOR,
            CapabilityKind.PORTFOLIO_PLANNER,
        }
    ),
}

PROSPECTIVE_STAGE_KINDS = MappingProxyType(PROSPECTIVE_STAGE_KINDS)


def operation_lifecycle(*, outcome_access, visibility_ceiling):
    """The registered access pair states whether an operation is development-only.

    Outcome-visible adjudication and summaries still belong to prospective plans;
    they do not grant a development operation prospective support.
    """
    if type(outcome_access) is not OutcomeAccess or type(visibility_ceiling) is not VisibilityCeiling:
        raise TypeError("operation lifecycle requires typed access and provenance visibility")
    # Visibility records provenance, not permission to inspect outcomes. Blind
    # metadata and sealed/revealed prospective tasks can inherit development
    # provenance without becoming development executions or gaining its stage
    # exceptions. Only this exact pair denotes the development-only route.
    if (outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE
            and visibility_ceiling is VisibilityCeiling.DEVELOPMENT_ONLY):
        return PlanLane.DEVELOPMENT
    return PlanLane.PROSPECTIVE


def stage_kind_allowed(stage, kind, *, lifecycle=PlanLane.PROSPECTIVE):
    if type(stage) is not ScientificStage or type(kind) is not CapabilityKind:
        raise TypeError("scientific stage/kind require exact typed contracts")
    if type(lifecycle) is not PlanLane or lifecycle not in (PlanLane.DEVELOPMENT, PlanLane.PROSPECTIVE):
        raise TypeError("operation requires its explicit development or prospective lifecycle")
    if kind is CapabilityKind.APPROVAL_GATE:
        return False
    if lifecycle is PlanLane.DEVELOPMENT:
        # Development retains its existing non-revealing method stages. A stage
        # label here never creates prospective compatibility or reveal authority.
        return stage not in (ScientificStage.EVALUATE, ScientificStage.REVEAL)
    return kind in PROSPECTIVE_STAGE_KINDS[stage]


def validate_operation_stage_kind(stage, kind, *, outcome_access, visibility_ceiling):
    lifecycle = operation_lifecycle(outcome_access=outcome_access, visibility_ceiling=visibility_ceiling)
    if not stage_kind_allowed(stage, kind, lifecycle=lifecycle):
        raise ValueError("capability kind is forbidden for the registered scientific stage/lifecycle")
    return lifecycle
