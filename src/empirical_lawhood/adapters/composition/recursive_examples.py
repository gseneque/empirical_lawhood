# SPDX-License-Identifier: MPL-2.0
"""Exposed authoring examples and the deliberately unresolved materials case."""

from dataclasses import replace
from decimal import Decimal

from empirical_lawhood.kernel.authority import AuthorityAction, AuthorityPolicy, ResourceBudget, SourceAccessClass
from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import ConditionRole, ContributionRole, ScientificConditionScope, ScientificRequirementSpec
from empirical_lawhood.kernel.status import LifecycleStatus
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft, SupplierProposal
from empirical_lawhood.planning.study_authoring import UnresolvedDecision


def rc_scientific_examples():
    """Reconstruct the three frozen historical designs without private paths."""
    from empirical_lawhood.adapters.methods.rc_prerequisite_chain.science import default_chain_config
    original = default_chain_config()
    menu_protocol = replace(original.protocol, protocol_id="rc-prerequisite-chain.dc1-menu-v2",
        preparation_durations_seconds=(*original.protocol.preparation_durations_seconds, Decimal("2")),
        maximum_elapsed_seconds=Decimal("3600"), maximum_native_steps=4_000_000)
    menu = replace(original, config_id=menu_protocol.protocol_id, protocol=menu_protocol)
    budget_protocol = replace(menu_protocol, protocol_id="rc-prerequisite-chain.dc1-budget-v3",
                              completion_deadline_seconds=Decimal("3.10"))
    budget = replace(original, config_id=budget_protocol.protocol_id, protocol=budget_protocol)
    values = {"original": original, "menu-v2": menu, "budget-v3": budget}
    expected = {"original": "e74a55ba0f3118e0d6f0d2a7dfe0580b07530b6e024912320339adce3da3ecab",
        "menu-v2": "ac6116b555fdc096351e6cfe8da95ed34ac1c175023c51083e4af32aa8012613",
        "budget-v3": "a343c067c6bea41e63865532808eb27e9cab720fc30d0b6931c9af0217ada21c"}
    if any(value.fingerprint() != expected[name] for name, value in values.items()):
        raise ValueError("supplied RC scientific design changed its original canonical bytes")
    return values


def materials_partial_draft():
    """Author requirements for A's device capability and measurement of B.

    No specimen, instrument, qualified parent or executable physical operation
    is invented. UNSPECIFIED units record a decision, never executable scope.
    """
    budget = ResourceBudget(1, 1024**2, 0, 60, 1024**2, 1024**2)
    world_id = "world.materials.physical-unselected"
    scope_a = ScientificConditionScope("system.material-a", world_id, "source.material-a.fabrication-unavailable",
        ("quantity.material-a.microstructure",), ("UNSPECIFIED",), "receiver.material-a.characterization",
        "clock.materials.unselected", "Native microstructure coordinate and fabrication history remain unselected",
        instance_id="specimen.material-a.unassigned", population_id="population.material-a.fabrication")
    scope_device = ScientificConditionScope("system.device-material-a", world_id, "source.device-material-a.unavailable",
        ("quantity.device.response",), ("UNSPECIFIED",), "receiver.measurement-device",
        "clock.materials.unselected", "Device response, environmental range and metrology channels remain unselected",
        instance_id="device.material-a.unassigned", population_id="population.device.fabrication")
    scope_b = ScientificConditionScope("system.material-b", world_id, "source.material-b.specimen-unavailable",
        ("quantity.material-b.response",), ("UNSPECIFIED",), "receiver.material-b.measurement",
        "clock.materials.unselected", "Material B response observable, uncertainty and sampling clock require a protocol",
        instance_id="specimen.material-b.unassigned", population_id="population.material-b.preparation")
    rows = (
        ("fabrication", "investigate-material-a", "assess-fabrication", ConditionRole.PHYSICAL, scope_a,
         "Acquire authentic material A preparations", "Fabrication protocol, batch identities, preparation history and variability are measured",
         "Uncontrolled batch variation or absent authentic specimens cannot supply device premises", (), "NO_AUTHENTIC_FABRICATION_SOURCE"),
        ("microstructure", "design-device", "assess-microstructure", ConditionRole.EVIDENTIAL, scope_a,
         "Investigate whether A's microstructure supplies the desired device response", "Measured microstructure and intervention contrasts support the device design",
         "Synthetic lattice output cannot substitute for physical A microstructure or tested transfer",
         ("requirement.materials.fabrication",), "NO_PHYSICAL_MICROSTRUCTURE_EVIDENCE"),
        ("device-response", "measure-material-b", "assess-device-response", ConditionRole.PHYSICAL, scope_device,
         "Supply an instrument for the material B question", "Device response and stability hold under declared environmental and operating conditions",
         "Calibration drift, fabrication variability or unmeasured operating dependence refutes supply",
         ("requirement.materials.microstructure",), "NO_AUTHENTIC_INSTRUMENT_CALIBRATION"),
        ("resolution", "measure-material-b", "assess-resolution", ConditionRole.INFORMATIONAL, scope_b,
         "Resolve the native quantity needed for the material B question", "Instrument resolution and joint uncertainty meet the selected B measurement requirement",
         "Insufficient resolution, changed receiver or unqualified units prevents the measurement",
         ("requirement.materials.device-response",), "MEASUREMENT_QUANTITY_AND_RESOLUTION_UNSELECTED"),
        ("specimen-b", "measure-material-b", "assess-specimen-b", ConditionRole.PHYSICAL, scope_b,
         "Supply material B under an authentic preparation and source contract", "Specimen identities, native preparation, available history and variability are retained",
         "A specimen A or numerical fixture cannot supply the independent physical B subject", (), "NO_AUTHENTIC_MATERIAL_B_SOURCE"),
        ("qualification", "publish-material-b-finding", "qualify-material-b", ConditionRole.EVIDENTIAL, scope_b,
         "Assess the new physical B measurement claim", "Eligible evidence, controls, uncertainty and prospective falsifiers qualify the selected response claim",
         "Absent issue/source authority, exposed substituted outcomes or a failed measurement prevents qualification",
         ("requirement.materials.resolution", "requirement.materials.specimen-b"), "NO_ELIGIBLE_PHYSICAL_QUALIFICATION_EVIDENCE"),
    )
    requirements, suppliers = [], []
    for tag, consumer, assessor, role, scope, purpose, condition, falsifier, further, reason in rows:
        rid = f"requirement.materials.{tag}"
        requirements.append(ScientificRequirementSpec(rid, f"materials.{consumer}", role, purpose,
            condition, scope, f"materials.{assessor}", falsifier,
            (ContributionRole.INSTANCE_PRODUCT, ContributionRole.QUALIFIED_EVIDENTIAL_PARENT), tuple(sorted(further))))
        suppliers.append(SupplierProposal(f"supplier.materials.{tag}.unavailable", rid, (), tuple(sorted(further)),
            False, "No supported physical operation or evidence is supplied; preserve this scientific question", (reason,)))
    policy = AuthorityPolicy("policy.materials.authoring", "owner.local-researcher", "operator.local-development",
        ("programme.materials.unselected",), frozenset((WorldKind.PHYSICAL_EXPERIMENT,)),
        frozenset((AuthorityAction.READ_ONLY_EXPLORATION,)), frozenset((SourceAccessClass.NONE,)),
        ("gate.physical-programme-unselected",), frozenset(), budget, OutcomeAccess.DEVELOPMENT_VISIBLE)
    root_id = "design.materials.partial"
    node = CampaignNode(root_id, CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(scope_b.source_id, scope_b), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec("campaign.materials.partial", "Construct a measurement capability using material A to investigate material B",
        ("system.device-material-a", "system.material-a", "system.material-b"), (world_id,), ("claim.material-b.response",),
        budget, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight("decision-right.materials.authoring", AuthorityAction.READ_ONLY_EXPLORATION,
                       "owner.local-researcher", policy.policy_id, False),),
        (node,), (root_id,), (root_id,), (), LifecycleStatus.ACTIVE)
    decision = UnresolvedDecision("decision.materials.measurement-observable", "requirements.resolution.scope.quantity_ids",
        "Which native B response, units and resolution would test the selected scientific question?",
        ("observable.electrical-response", "observable.optical-response"))
    return RecursiveStudyDraft("draft.materials.partial", campaign.objective, campaign,
        tuple(sorted(requirements, key=lambda value: value.requirement_id)), (),
        tuple(sorted(suppliers, key=lambda value: value.proposal_id)), (), (), (), (), unresolved_decisions=(decision,))
