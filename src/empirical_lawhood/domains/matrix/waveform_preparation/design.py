# SPDX-License-Identifier: MPL-2.0
"""Derive one causal graph for a complete split of independently drawn waveforms."""

from empirical_lawhood.design.campaigns import (
    CampaignLane,
    CampaignNode,
    CampaignNodeKind,
    CampaignSpec,
    DecisionRight,
)
from empirical_lawhood.design.recursive_authoring import (
    RecursiveExternalInput,
    RecursiveInputLink,
    RecursiveOperationSpec,
    RecursiveStudyDraft,
)
from empirical_lawhood.execution.capabilities import CapabilityPermission
from empirical_lawhood.execution.plans import ScientificStage
from empirical_lawhood.science.evidence.evidence import (
    ClaimSpec,
    EvidenceCeiling,
    OutcomeAccess,
    VisibilityCeiling,
)
from empirical_lawhood.science.identity.authority import (
    AuthorityAction,
    AuthorityPolicy,
    ResourceBudget,
    SourceAccessClass,
)
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import (
    ConditionRole,
    ContributionRole,
    DevelopmentStudySpec,
    ScientificConditionScope,
    ScientificConnectionSpec,
    ScientificRequirementSpec,
)
from empirical_lawhood.science.models.worlds import WorldKind
from empirical_lawhood.science.records.status import LifecycleStatus

from .records import LOWER_USERS, NATIVE, PHASES, PROTOCOL_ID, WaveformOperation

QUESTION = "How much covered service does fixed preparation gain across bath waveforms, and can the prefix identify the gains and harms?"
WORLD = "world.matrix.six-hermitian-four.classical-baoab"
ACCESS, VISIBILITY = (
    OutcomeAccess.DEVELOPMENT_VISIBLE,
    VisibilityCeiling.DEVELOPMENT_ONLY,
)
PERMISSIONS = tuple(
    sorted(
        (
            CapabilityPermission.READ_DEVELOPMENT,
            CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
        )
    )
)
BUDGET = ResourceBudget(1, None, 0, None, None, None)
STAGES = {
    **dict.fromkeys(NATIVE, ScientificStage.ACQUIRE),
    "forecast": ScientificStage.TRANSFORM,
    "lower": ScientificStage.TRANSFORM,
    "measure": ScientificStage.FALSIFY,
    "cohort": ScientificStage.SYNTHESIZE,
}


def configurations(spec):
    rows = (
        WaveformOperation(spec, phase, n)
        for n in range(spec.count)
        for phase in PHASES[:-1]
    )
    return tuple(
        sorted(
            (*rows, WaveformOperation(spec, "cohort", None)), key=lambda c: c.node_id
        )
    )


def scientific_root(spec):
    study = "study." + spec.specification_id
    claim = ClaimSpec(
        "claim." + study,
        WORLD,
        "population." + spec.fingerprint(),
        QUESTION,
        "One independent waveform and perturbation. Three preparations share two views, two futures and 256 request pairs.",
        "unit.independent-bath-waveform",
        None,
        EvidenceCeiling.NON_PROMOTABLE,
        ACCESS,
        VISIBILITY,
        "Empirical decision for the specified numerical population and the unchanged original F.",
        ("assumption.independent-waveforms", "assumption.shared-native-requests"),
    )
    inputs = (spec.identity, spec.lower, spec.exposure) + (
        (spec.development,) if spec.development else ()
    )
    system = ObjectIdentity(
        "system." + spec.specification_id, spec.SCHEMA, spec.VERSION, spec.fingerprint()
    )
    return DevelopmentStudySpec(
        study,
        QUESTION,
        system,
        WORLD,
        WorldKind.NUMERICAL_SIMULATOR,
        spec.unit_ids,
        ("view.primary", "view.refined"),
        (claim,),
        tuple(sorted(inputs, key=lambda r: r.object_id)),
    )


def campaign(root, configs):
    budget = ResourceBudget.aggregate(BUDGET for _ in configs)
    policy = AuthorityPolicy(
        root.study_id + ".policy",
        "human.selected-operator",
        "researcher.matrix-development",
        (PROTOCOL_ID,),
        frozenset({WorldKind.NUMERICAL_SIMULATOR}),
        frozenset({AuthorityAction.SIMULATION_EXECUTION}),
        frozenset({SourceAccessClass.NONE}),
        ("source-bound-waveform-population",),
        frozenset(),
        budget,
        ACCESS,
    )
    node = CampaignNode(
        root.study_id + ".proposal",
        CampaignNodeKind.ANALYSIS_PROPOSAL,
        CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id, root),
        (),
        LifecycleStatus.ACTIVE,
    )
    return CampaignSpec(
        root.study_id + ".campaign",
        QUESTION,
        (root.system.object_id,),
        (WORLD,),
        (root.claims[0].claim_id,),
        budget,
        ObjectIdentity.from_record(policy.policy_id, policy),
        (
            DecisionRight(
                root.study_id + ".right",
                AuthorityAction.SIMULATION_EXECUTION,
                policy.delegate_id,
                policy.policy_id,
                True,
            ),
        ),
        (node,),
        (node.node_id,),
        (node.node_id,),
        (),
        LifecycleStatus.ACTIVE,
    )


def graph(spec, configs, root):
    scope = ScientificConditionScope(
        root.system.object_id,
        WORLD,
        "source.matrix.baoab",
        ("fixed-law-covered-service",),
        ("assigned-request-fraction",),
        "receiver.fixed-original-f",
        "clock.physical-model-time",
        "Common prefix through 4096, actual handoff at 4496, coupled native response through 4688.",
        source_config_sha256=spec.fingerprint(),
        population_id=root.claims[0].relation_id,
    )
    reqs, connections, links = [], [], []
    external_roles = {"lower": spec.lower}
    if spec.development is not None:
        external_roles["development"] = spec.development
    for config in configs:
        for name in external_roles:
            if (name == "lower" and config.phase in LOWER_USERS) or (
                name == "development" and config.phase in ("forecast", "cohort")
            ):
                links.append(
                    RecursiveInputLink(
                        "edge." + config.node_id + "." + name,
                        config.node_id,
                        name,
                        external_input_id="external." + name,
                        scientific_role="HISTORY",
                    )
                )
        for parent in config.suppliers():
            port = "parents." + parent.phase + "." + str(parent.index).zfill(3)
            key = config.node_id + "." + port
            requirement = ScientificRequirementSpec(
                "requirement." + key,
                config.node_id,
                ConditionRole.INFORMATIONAL,
                "Supply the measured " + parent.phase + " at its declared cutoff.",
                "Authenticated source, waveform, prior decisions and complete receipt identify the same operands.",
                scope,
                config.node_id,
                "A substituted root, a changed clock or a post-outcome choice invalidates supply.",
                (ContributionRole.INSTANCE_PRODUCT,),
                background_assumption_ids=("assumption.independent-waveforms",),
            )
            connection = ScientificConnectionSpec(
                "connection." + key,
                requirement.requirement_id,
                parent.node_id,
                "product",
                port,
                config.node_id,
                root.claims[0].claim_id,
                ContributionRole.INSTANCE_PRODUCT,
                requirement.falsifier,
            )
            reqs.append(requirement)
            connections.append(connection)
            links.append(
                RecursiveInputLink(
                    "edge." + key,
                    config.node_id,
                    port,
                    parent.node_id,
                    "product",
                    scientific_role="HISTORY",
                    requirement_id=requirement.requirement_id,
                    connection_id=connection.connection_id,
                )
            )
            if parent.phase in NATIVE:
                links.append(
                    RecursiveInputLink(
                        "edge." + key + ".arrays",
                        config.node_id,
                        "arrays." + port,
                        parent.node_id,
                        "arrays",
                        scientific_role="HISTORY",
                    )
                )
    externals = tuple(
        RecursiveExternalInput(
            "external." + key,
            operand.object_id,
            operand.object_schema,
            "application/json",
            None,
            ACCESS,
            VISIBILITY,
            operand.object_fingerprint,
            scientific_role="HISTORY",
        )
        for key, operand in sorted(external_roles.items())
    )
    return (
        tuple(sorted(reqs, key=lambda x: x.requirement_id)),
        tuple(sorted(connections, key=lambda x: x.connection_id)),
        tuple(sorted(links, key=lambda x: x.edge_id)),
        externals,
    )


def lower(spec, records):
    from .bindings import declarations

    configs = configurations(spec)
    operations_by_phase = {
        r.capability_key.rsplit(".", 1)[-1]: r for r in declarations()
    }
    operations = tuple(
        RecursiveOperationSpec.from_config(
            node_id=c.node_id,
            selection=operations_by_phase[c.phase].registration().selection,
            config_id=c.config_id,
            config=c,
            obligation_ids=("obligation." + c.node_id,),
            resource_budget=BUDGET,
        )
        for c in configs
    )
    root = scientific_root(spec)
    requirements, connections, links, externals = graph(spec, configs, root)
    draft = RecursiveStudyDraft(
        draft_id="draft." + spec.specification_id,
        question=QUESTION,
        campaign=campaign(root, configs),
        requirements=requirements,
        connections=connections,
        suppliers=(),
        operations=operations,
        external_inputs=externals,
        links=links,
        selected_operation_ids=tuple(c.node_id for c in configs),
        development_study=root,
    )
    return draft, tuple(
        sorted(("external." + k, v) for k, v in records.items() if k != "exposure")
    )
