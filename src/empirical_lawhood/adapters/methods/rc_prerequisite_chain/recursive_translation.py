# SPDX-License-Identifier: MPL-2.0
"""Translate frozen RC operands into explicit shared operations and requirements."""

from empirical_lawhood.kernel.authority import AuthorityAction, AuthorityPolicy, ResourceBudget, SourceAccessClass
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import (
    ConditionRole, ContributionRole, DevelopmentStudySpec, ScientificConditionScope,
    ScientificConnectionSpec, ScientificRequirementSpec,
)
from empirical_lawhood.kernel.status import LifecycleStatus
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.planning.recursive_authoring import RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft, SupplierProposal

from . import operation_contracts as records
from .operation_bindings import BUDGET, PHASES, operation_registrations
from .science import prove_chain

QUESTION = "Does a causally available state interval supply a committed preparation that enables the frozen response task?"
WORLD_ID = "world.rc-chain.numerical"
SYSTEM_ID = "system.rc-chain.one-cell"
CLAIM_IDS = ("claim.rc-chain.rc-j", "claim.rc-chain.rc-m", "claim.rc-chain.rc-p")

# consumer phase/input -> supplier phase/output. No shared executor interprets RC phases.
DEPENDENCIES = {
    "source": (),
    "observations": (("observer", "source", "observer"),),
    "admit": (("reports", "observations", "reports"),),
    "commit": (("admissions", "admit", "admissions"), ("reports", "observations", "reports")),
    "deliver": (("commitments", "commit", "commitments"),),
    "measure": (("commitments", "commit", "commitments"), ("reports", "observations", "reports"), ("source", "source", "evidence")),
    "support": (("commitments", "commit", "commitments"), ("measurements", "measure", "measurements"), ("native", "deliver", "native")),
    "joined": (("commitments", "commit", "commitments"), ("measurements", "measure", "measurements"),
               ("native", "deliver", "native"), ("support", "support", "support")),
    "reduce": (("commitments", "commit", "commitments"), ("joined", "joined", "joined"),
               ("measurements", "measure", "measurements"), ("reports", "observations", "reports"),
               ("source", "source", "evidence"), ("support", "support", "support")),
}


def rc_recursive_draft(config, *, draft_id="draft.rc-chain.recursive", unit_ids=None, include_summary=True):
    """Retain original scientific bytes while selecting a closed exposed wave.

    A single-unit early slice omits the complete-census summary. Its original
    configuration and unit projection remain exact, and the other units are
    explicitly outside this wave's assigned roster.
    """
    prove_chain(config)
    complete = tuple(unit.unit_id for unit in config.units)
    assigned = complete if unit_ids is None else tuple(sorted(unit_ids))
    if not assigned or len(set(assigned)) != len(assigned) or not set(assigned).issubset(complete):
        raise ValueError("RC selected wave substitutes or duplicates its assigned unit census")
    if include_summary and assigned != complete:
        raise ValueError("RC legacy summary requires the complete original configuration census")
    config_identity = ObjectIdentity.from_record(config.config_id, config)
    claims = tuple(ClaimSpec(claim, WORLD_ID, "relation.rc-chain.response", proposition,
        "Complete frozen variant and arm denominator, nested numerical views", "units.rc-chain.initial-state-configurations",
        None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY, "Exposed numerical development cannot qualify or create fresh evidence",
        ("assumption.rc-chain.one-cell-kcl",), numerical_view_ids=("backward-euler", "matrix-exponential"))
        for claim, proposition in zip(CLAIM_IDS, (
            "RC-J: the supplied measurement and preparation jointly enable the unchanged frozen response",
            "RC-M: declared intervals contain the sampled voltage with the frozen causal binding",
            "RC-P: the committed finite preparation supplies response-cutoff support"), strict=True))
    study = DevelopmentStudySpec(f"study.{draft_id}", QUESTION, ObjectIdentity.from_record(SYSTEM_ID, config), WORLD_ID,
        WorldKind.NUMERICAL_SIMULATOR, assigned, ("backward-euler", "matrix-exponential"), claims, (config_identity,))
    # Governance declarations identify the real local owner; they are neither
    # an execution authorization nor a signed issue/approval object.
    count = len(assigned) * 9 + int(include_summary)
    campaign_budget = ResourceBudget(1, BUDGET.memory_bytes, 0, BUDGET.wall_time_seconds * count,
                                     BUDGET.source_scan_bytes * count, BUDGET.output_bytes * count)
    policy = AuthorityPolicy(f"policy.{draft_id}", "owner.local-researcher", "operator.local-development",
        (study.study_id,), frozenset((WorldKind.NUMERICAL_SIMULATOR,)),
        frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION, AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)), ("gate.local-nonactuating-development",), frozenset(),
        campaign_budget, OutcomeAccess.DEVELOPMENT_VISIBLE)
    root_id = f"design.{draft_id}"
    node = CampaignNode(root_id, CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(study.study_id, study), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec(f"campaign.{draft_id}", QUESTION, (SYSTEM_ID,), (WORLD_ID,), CLAIM_IDS,
        campaign_budget, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight(f"decision-right.{draft_id}", AuthorityAction.SIMULATION_EXECUTION,
                       "owner.local-researcher", policy.policy_id, False),),
        (node,), (root_id,), (root_id,), (), LifecycleStatus.ACTIVE)
    registrations = {row.selection.capability_key.rsplit(".", 1)[-1]: row for row in operation_registrations()}
    operations, links, requirements, connections, suppliers = [], [], [], [], []
    for index, unit_id in enumerate(assigned, start=1):
        prefix = f"rc.u{index:02d}"
        nodes = {role: f"{prefix}.{role}" for role in DEPENDENCIES}
        scope = ScientificConditionScope(SYSTEM_ID, WORLD_ID, f"source.{prefix}",
            (config.protocol.quantity_id,), (config.protocol.voltage_unit,), config.protocol.receiver_id,
            "clock.rc-chain.seconds", "One capacitor voltage, simulation seconds and exact left/right boundary schedule",
            config.fingerprint(), unit_id, information_cutoff=InformationCutoff(
                f"cutoff.{prefix}", "clock.rc-chain.seconds", CausalPhase.PRE_ACTION, config.protocol.decision_seconds),
            available_by=config.protocol.decision_seconds, valid_from=config.protocol.sample_seconds,
            uncertainty_contract=ObjectIdentity.from_record(
                "protocol.rc-chain", config.protocol))
        requirement_specs = (
            ("m", "commit", "reports", "observations", "reports", "measure", ConditionRole.INFORMATIONAL,
             "A declared observation interval is available by the decision cutoff, bound to this receiver/source/unit",
             "Wrong units, source, unit, clock, late availability, excessive radius or false oracle containment refuses/falsifies supply", ()),
            ("p", "joined", "support", "support", "support", "support", ConditionRole.PHYSICAL,
             "The committed preparation prospectively covers the response support and its actual cutoff lies in that support",
             "Wrong/insufficient boundaries, unjustified intervals, false measurement or out-of-support actual cutoff fail supply", (f"requirement.{prefix}.m",)),
            ("j", "reduce", "joined", "joined", "joined", "joined", ConditionRole.TASK,
             "Supplied M and P jointly meet the unchanged frozen affine response and original completion deadline",
             "A coincidental in-band endpoint cannot supply missing support; endpoint/view/current/timing failures retain the negative result", (f"requirement.{prefix}.m", f"requirement.{prefix}.p")),
        )
        annotated = {}
        for tag, consumer, port, supplier, output, assessor, condition_role, condition, falsifier, prerequisites in requirement_specs:
            rid, cid = f"requirement.{prefix}.{tag}", f"connection.{prefix}.{tag}"
            requirement = ScientificRequirementSpec(rid, nodes[consumer], condition_role,
                f"Supply frozen RC-{tag.upper()} for unit {unit_id}", condition, scope, nodes[assessor], falsifier,
                (ContributionRole.INSTANCE_PRODUCT,), tuple(sorted(prerequisites)),
                ("assumption.rc-chain.one-cell-kcl",), BUDGET)
            connection = ScientificConnectionSpec(cid, rid, nodes[supplier], output, port, nodes[assessor],
                f"claim.rc-chain.rc-{tag}", ContributionRole.INSTANCE_PRODUCT, falsifier)
            requirements.append(requirement); connections.append(connection)
            suppliers.append(SupplierProposal(f"supplier.{prefix}.{tag}", rid, (nodes[supplier],),
                tuple(sorted(prerequisites)), True, "Explicit registered phase supplier, assessed after immutable commitment"))
            annotated[(consumer, port)] = (rid, cid)
        for role, config_type, _, _, _, _, _, _ in PHASES[:-1]:
            cid = f"config.{nodes[role]}"
            if issubclass(config_type, records.RCPolicyOperationConfig):
                operand = config_type(cid, config.fingerprint(), unit_id, config.protocol)
            else:
                operand = config_type(cid, config, unit_id)
            obligations = tuple(sorted(requirement.requirement_id for requirement in requirements
                if requirement.assessment_operation_id == nodes[role]))
            operations.append(RecursiveOperationSpec.from_config(node_id=nodes[role],
                selection=registrations[role].selection, config_id=cid, config=operand,
                obligation_ids=obligations or (f"obligation.{nodes[role]}.ports",), resource_budget=BUDGET))
            for port, supplier, output in DEPENDENCIES[role]:
                rid, connection = annotated.get((role, port), (None, None))
                links.append(RecursiveInputLink(f"edge.{nodes[role]}.{port}", nodes[role], port,
                    nodes[supplier], output, None, "ACTION" if supplier == "commit" else "HISTORY", rid, connection))
        if include_summary:
            links.append(RecursiveInputLink(f"edge.rc.summary.u{index:02d}", "rc.summary", f"units.{unit_id}", nodes["reduce"], "unit"))
    if include_summary:
        operand = records.RCSummaryOperationConfig("config.rc.summary", config)
        operations.append(RecursiveOperationSpec.from_config(node_id="rc.summary", selection=registrations["summary"].selection,
            config_id=operand.config_id, config=operand, obligation_ids=("obligation.rc.summary.complete-census",), resource_budget=BUDGET))
    return RecursiveStudyDraft(draft_id, QUESTION, campaign,
        tuple(sorted(requirements, key=lambda value: value.requirement_id)),
        tuple(sorted(connections, key=lambda value: value.connection_id)),
        tuple(sorted(suppliers, key=lambda value: value.proposal_id)),
        tuple(sorted(operations, key=lambda value: value.node_id)), (),
        tuple(sorted(links, key=lambda value: value.edge_id)), tuple(sorted(value.node_id for value in operations)),
        development_study=study)


def project_legacy_results(config, products):
    """Project retained final products only; no execution or numerical replay."""
    from .contracts import RCChainSummary, RCChainUnitResult
    from .science import summarize_chain
    units = tuple(sorted((value for value in products if isinstance(value, RCChainUnitResult)), key=lambda value: value.unit_id))
    summary = summarize_chain(config, units)
    summaries = tuple(value for value in products if isinstance(value, RCChainSummary))
    if len(summaries) != 1 or summaries[0] != summary:
        raise ValueError("RC retained summary differs from its exact original scientific projection")
    return units, summary
