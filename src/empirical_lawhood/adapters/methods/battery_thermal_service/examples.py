# SPDX-License-Identifier: MPL-2.0
"""Concrete declaration of a single preparation; grants no execution authority."""

from decimal import Decimal

from empirical_lawhood.kernel.authority import AuthorityAction, AuthorityPolicy, ResourceBudget, SourceAccessClass
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.status import LifecycleStatus
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.planning.recursive_authoring import RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft

from .contracts import BatteryThermalConfig, BatteryThermalSource, PROTOCOL_SHA256, QUESTION
from .executable_binding import RESOURCE, SYSTEM, WORLD, operation_registrations


def thermal_service_draft(*, initial_temperature_k=Decimal("296.15"), view="primary", word="standard-cc900"):
    """Acquire and independently assess exactly one of the selected nested views."""
    token = "23c" if initial_temperature_k == Decimal("296.15") else "27c"
    unit = f"unit.battery-thermal-service.{token}"
    prefix = f"battery-thermal-service.{token}.{word}.{view}"
    source = BatteryThermalSource()
    claim = ClaimSpec(f"{prefix}.claim", WORLD, "battery-thermal-service", QUESTION,
                      "Realized charge and numerical service envelope; whole-time certification and physical uncertainty remain distinct.",
                      unit, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE,
                      VisibilityCeiling.DEVELOPMENT_ONLY, "Never promotes development completion to scientific qualification.",
                      ("exposed-deterministic-model",), numerical_view_ids=(view,))
    scientific = DevelopmentStudySpec(f"{prefix}.study", QUESTION, ObjectIdentity.from_record(SYSTEM, source), WORLD,
                                       WorldKind.NUMERICAL_SIMULATOR, (unit,), (view,), (claim,),
                                       (ObjectIdentity.from_record("battery-thermal-service-source", source),))
    budget = ResourceBudget(1, None, 0, None, None, None)
    policy = AuthorityPolicy(f"{prefix}.development-policy", "human.project-owner", "researcher.battery-development",
                             ("battery-thermal-service.development",), frozenset({WorldKind.NUMERICAL_SIMULATOR}),
                             frozenset({AuthorityAction.SIMULATION_EXECUTION}), frozenset({SourceAccessClass.NONE}),
                             ("frozen-source-and-protocol",), frozenset(), budget, OutcomeAccess.DEVELOPMENT_VISIBLE)
    root = CampaignNode(f"{prefix}.proposal", CampaignNodeKind.ANALYSIS_PROPOSAL, CampaignLane.EXPLORATORY,
                        ObjectIdentity.from_record(scientific.study_id, scientific), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec(f"{prefix}.campaign", QUESTION, (SYSTEM,), (WORLD,), (claim.claim_id,), budget,
                            ObjectIdentity.from_record(policy.policy_id, policy),
                            (DecisionRight(f"{prefix}.development-right", AuthorityAction.SIMULATION_EXECUTION,
                                           policy.delegate_id, policy.policy_id, True),),
                            (root,), (root.node_id,), (root.node_id,), (), LifecycleStatus.ACTIVE)
    operations = []
    for registration in operation_registrations():
        operation = registration.selection.capability_key.rsplit(".", 1)[-1]
        node = f"{prefix}.{operation}"
        config = BatteryThermalConfig(f"{node}.config", operation, PROTOCOL_SHA256, unit,
                                      initial_temperature_k, word, view)
        operations.append(RecursiveOperationSpec.from_config(
            node_id=node, selection=registration.selection, config_id=config.config_id, config=config,
            obligation_ids=(f"{node}.obligation",), resource_budget=RESOURCE,
            resource_lock_ids=("battery-native-single-worker",) if operation == "acquire" else ()))
    edge = RecursiveInputLink(f"{prefix}.trace-edge", f"{prefix}.assess", "trace", f"{prefix}.acquire", "product", None, "OUTCOME", None, None)
    return RecursiveStudyDraft(prefix, QUESTION, campaign, (), (), (), tuple(operations), (), (edge,),
                               tuple(operation.node_id for operation in operations), development_study=scientific)
