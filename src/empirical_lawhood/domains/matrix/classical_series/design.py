# SPDX-License-Identifier: MPL-2.0
"""Lower one authored series to the existing recursive execution graph."""
from hashlib import sha256

from empirical_lawhood.science.identity.authority import AuthorityAction, AuthorityPolicy, ResourceBudget, SourceAccessClass
from empirical_lawhood.science.evidence.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import ConditionRole, ContributionRole, DevelopmentStudySpec, ScientificConditionScope, ScientificConnectionSpec, ScientificRequirementSpec
from empirical_lawhood.science.records.status import LifecycleStatus
from empirical_lawhood.science.models.worlds import WorldKind
from empirical_lawhood.design.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.design.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.execution.capabilities import CapabilityPermission
from empirical_lawhood.execution.plans import ScientificStage

from .records import NAMESPACE, SeriesOperationConfig

# One numerical thread per independently recoverable root. Byte/time/memory
# limits are optional operational selections, not arbitrary scientific limits.
BUDGET = ResourceBudget(1, None, 0, None, None, None)
ACCESS, VISIBILITY = OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY
PERMISSIONS = tuple(sorted((CapabilityPermission.READ_DEVELOPMENT, CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS)))
WORLD = "world.matrix.six-hermitian-four.classical-baoab"
QUESTION = "Which prepared and adapted response descriptions preserve the quantities required by later matrix questions?"


def stage(phase):
    return {"acquire": ScientificStage.ACQUIRE, "calibrate": ScientificStage.DEVELOP, "analyse": ScientificStage.FALSIFY, "summarise": ScientificStage.TRANSFORM, "synthesise": ScientificStage.SYNTHESIZE}[phase]


def budget_for(config):
    """Conservative working-memory allowance derived from the selected array census.

    This is placement/enforcement, not an estimated physical or scientific cost.
    Changing root count never silently truncates the authored population.
    """
    c = config.settings
    cases = len(c["coordinates"]) * len(c["preparation_arms"])
    if config.phase in ("acquire", "analyse", "summarise"):
        numerical_values = cases * (2 * 96 * 96 * (1 + c["panels"]) +
            2 * 8 * 96 * max(48, c["joint_rank"]) +
            2 * c["panels"] * len(c["actions"]) * (c["horizon_ticks"] + 1) * 48)
        # The shared executor enforces virtual address space, not only RSS.
        # Reserve the imported numerical runtime, authenticated output encoding
        # and Python object copies, then scale the complete array census.
        memory = 2 * 1024**3 + 256 * numerical_values
    else:
        # Compact root summaries only; calibration does not retain native arrays.
        memory = 2 * 1024**3 + 128 * len(config.assignments) * cases * 2048
    return ResourceBudget(1, memory, 0, None, None, None)


def configs_for(specification):
    def make(phase, assignments):
        selection = specification.fingerprint() + ":" + phase + ":" + ",".join(str(r.seed) for r in assignments)
        node = "mcs." + sha256(selection.encode()).hexdigest() + "." + phase
        return SeriesOperationConfig("config." + node, phase, specification.identity,
            specification.settings_json, assignments, specification.evidence_scope)
    rows = []
    if specification.mode == "new-development":
        for root in specification.assignments:
            rows.append(make("acquire", (root,)))
            if root.role != "confirmation":
                rows.append(make("summarise", (root,)))
        rows.append(make("calibrate", tuple(r for r in specification.assignments if r.role != "confirmation")))
    for root in specification.assignments:
        if root.role == "confirmation":
            rows.append(make("analyse", (root,)))
    rows.append(make("synthesise", tuple(r for r in specification.assignments if r.role == "confirmation")))
    return tuple(sorted(rows, key=lambda c: c.node_id))


def scientific_root(specification):
    prefix = "study." + NAMESPACE + "." + specification.fingerprint()
    system = ObjectIdentity("system.matrix.six-hermitian-four." + sha256(specification.settings_json.encode()).hexdigest(),
        "empirical-lawhood/matrix-classical-series/system-settings", "1.0.0", sha256(specification.settings_json.encode()).hexdigest())
    claim = ClaimSpec("claim." + prefix, WORLD, "population." + specification.fingerprint(), QUESTION,
        "Six Hermitian 4x4 matrices, 96 position coordinates; nested views and parameter cells share independent roots.",
        "unit.independent-matrix-root", None, EvidenceCeiling.NON_PROMOTABLE, ACCESS, VISIBILITY,
        "Predeclared numerical development or exposed reanalysis; no retrospective qualification, molecular forecast or protected confirmation.",
        ("assumption.disjoint-root-seeds", "assumption.matrix-model-scope"))
    operands = (specification.identity,) + tuple(r.identity for r in specification.retained_inputs)
    return DevelopmentStudySpec(prefix, QUESTION, system, WORLD, WorldKind.NUMERICAL_SIMULATOR,
        specification.independent_unit_ids, ("view.primary", "view.refined"), (claim,),
        tuple(sorted(operands, key=lambda p: p.object_id)))


def campaign_for(root, configs):
    prefix = root.study_id
    budget = ResourceBudget.aggregate(budget_for(c) for c in configs)
    policy = AuthorityPolicy(prefix + ".policy", "human.selected-operator", "researcher.matrix-development",
        (NAMESPACE + ".development",), frozenset({WorldKind.NUMERICAL_SIMULATOR}),
        frozenset({AuthorityAction.SIMULATION_EXECUTION}), frozenset({SourceAccessClass.NONE}),
        ("source-bound-predeclared-numerical-design",), frozenset(), budget, ACCESS)
    node = CampaignNode(prefix + ".proposal", CampaignNodeKind.ANALYSIS_PROPOSAL, CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id, root), (), LifecycleStatus.ACTIVE)
    return CampaignSpec(prefix + ".campaign", QUESTION, (root.system.object_id,), (WORLD,), (root.claims[0].claim_id,),
        budget, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight(prefix + ".right", AuthorityAction.SIMULATION_EXECUTION, policy.delegate_id, policy.policy_id, True),),
        (node,), (node.node_id,), (node.node_id,), (), LifecycleStatus.ACTIVE)


def graph_for(specification, configs):
    root = scientific_root(specification)
    by_unit = {(c.phase, c.assignments[0].unit_id): c for c in configs if c.phase not in ("calibrate", "synthesise")}
    calibration = next((c for c in configs if c.phase == "calibrate"), None)
    links, requirements, connections = [], [], []
    external = {r.key: r for r in specification.retained_inputs}
    scope = ScientificConditionScope(root.system.object_id, WORLD, "source.matrix.baoab",
        ("matrix-response",), ("model-units",), "receiver.matrix.position-and-momentum", "clock.aligned-model-time",
        "Matched signed pulse responses; TRAIN/CAL complete before CONF native acquisition.",
        source_config_sha256=sha256(specification.settings_json.encode()).hexdigest(), population_id=root.claims[0].relation_id)

    def connect(consumer, port, supplier, *, key=None):
        suffix = consumer.node_id + "." + port
        if supplier is None:
            selected = external[key]
            links.append(RecursiveInputLink("edge." + suffix, consumer.node_id, port,
                external_input_id="external." + selected.key, scientific_role="HISTORY"))
            return
        requirement = ScientificRequirementSpec("requirement." + suffix, consumer.node_id, ConditionRole.INFORMATIONAL,
            "Supply the exact retained " + port + " contribution before this consumer can execute.",
            "Original producing configuration, assigned-root census, and immutable output identity agree with the authored graph.",
            scope, consumer.node_id,
            "Missing, changed, future-CONF-contaminated or wrong-root inputs invalidate this supply; claim truth is assessed separately.",
            (ContributionRole.INSTANCE_PRODUCT,), background_assumption_ids=("assumption.disjoint-root-seeds",))
        connection = ScientificConnectionSpec("connection." + suffix, requirement.requirement_id,
            supplier.node_id, "product", port, consumer.node_id, root.claims[0].claim_id,
            ContributionRole.INSTANCE_PRODUCT, requirement.falsifier)
        requirements.append(requirement)
        connections.append(connection)
        links.append(RecursiveInputLink("edge." + suffix, consumer.node_id, port,
            supplier.node_id, "product", scientific_role="HISTORY", requirement_id=requirement.requirement_id,
            connection_id=connection.connection_id))

    if calibration is not None:
        for assigned in calibration.assignments:
            connect(calibration, "summaries." + assigned.unit_id, by_unit[("summarise", assigned.unit_id)])
    synthesis = next(c for c in configs if c.phase == "synthesise")
    for assigned in synthesis.assignments:
        connect(synthesis, "analyses." + assigned.unit_id, by_unit[("analyse", assigned.unit_id)])
    for config in configs:
        if config.phase == "acquire" and config.assignments[0].role == "confirmation":
            connect(config, "calibration", calibration)
        elif config.phase == "summarise":
            supplier = by_unit[("acquire", config.assignments[0].unit_id)]
            connect(config, "acquisition", supplier)
            links.append(RecursiveInputLink("edge." + config.node_id + ".arrays", config.node_id, "arrays",
                supplier.node_id, "arrays", scientific_role="HISTORY"))
        elif config.phase == "analyse":
            connect(config, "calibration", calibration, key="calibration")
            supplier = by_unit.get(("acquire", config.assignments[0].unit_id))
            connect(config, "acquisition", supplier, key=config.assignments[0].unit_id)
            if supplier is None:
                links.append(RecursiveInputLink("edge." + config.node_id + ".arrays", config.node_id, "arrays",
                    external_input_id="external.arrays." + config.assignments[0].unit_id, scientific_role="HISTORY"))
            else:
                links.append(RecursiveInputLink("edge." + config.node_id + ".arrays", config.node_id, "arrays",
                    supplier.node_id, "arrays", scientific_role="HISTORY"))
    external_contracts = tuple(RecursiveExternalInput("external." + p.key, p.identity.object_id,
        p.identity.object_schema, "application/json", None, ACCESS, VISIBILITY, p.identity.object_fingerprint,
        scientific_role="HISTORY") for p in specification.retained_inputs)
    external_contracts += tuple(RecursiveExternalInput("external." + p.key, p.identity.artifact_id,
        p.identity.payload_schema, p.identity.media_type, p.identity.size_bytes, ACCESS, VISIBILITY, p.identity.sha256,
        scientific_role="HISTORY") for p in specification.retained_arrays)
    external_contracts = tuple(sorted(external_contracts, key=lambda p: p.input_id))
    return (tuple(sorted(requirements, key=lambda x: x.requirement_id)),
        tuple(sorted(connections, key=lambda x: x.connection_id)),
        tuple(sorted(links, key=lambda x: x.edge_id)), external_contracts)


def lower(specification, records):
    from .bindings import operation_declarations
    configs = configs_for(specification)
    declarations = {d.capability_key.rsplit(".", 1)[-1]: d for d in operation_declarations()}
    operations = tuple(RecursiveOperationSpec.from_config(node_id=c.node_id,
        selection=declarations[c.phase].registration().selection, config_id=c.config_id, config=c,
        obligation_ids=("obligation." + c.node_id,), resource_budget=budget_for(c)) for c in configs)
    root = scientific_root(specification)
    requirements, connections, links, external_inputs = graph_for(specification, configs)
    draft = RecursiveStudyDraft(draft_id="draft." + specification.specification_id, question=QUESTION,
        campaign=campaign_for(root, configs), requirements=requirements, connections=connections, suppliers=(),
        operations=operations, external_inputs=external_inputs, links=links,
        selected_operation_ids=tuple(c.node_id for c in configs), development_study=root)
    return draft, tuple(sorted(("external." + key, value) for key, value in records.items()))
