# SPDX-License-Identifier: MPL-2.0
"""Derive M0–M7 acquisitions and assessments through the shared recursive graph."""
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
from .records import MODULES, NAMESPACE, PREREQUISITES, OperationConfig, selection_key

BUDGET = ResourceBudget(1, None, 0, None, None, None)
ACCESS, VISIBILITY = OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY
PERMISSIONS = tuple(sorted((CapabilityPermission.READ_DEVELOPMENT, CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS)))
WORLD = "world.matrix.six-hermitian-four.classical-baoab"
QUESTION = "Which physical information supplies the specified receiver at useful accuracy and complete cost without compulsory learned fitting?"


def stage(phase):
    return {"acquire": ScientificStage.ACQUIRE, "analyse": ScientificStage.FALSIFY, "synthesise": ScientificStage.SYNTHESIZE}[phase]


def budget_for(config):
    # Operational selection never changes the record length or root census.
    limits = config.settings.get("resources", {})
    return ResourceBudget(1, limits.get("memory_bytes"), 0, limits.get("wall_time_seconds"), None, limits.get("output_bytes"))


def configs_for(specification):
    def make(phase, module, assignments):
        key = specification.fingerprint() + ":" + phase + ":" + module + ":" + ",".join(str(r.seed) for r in assignments)
        node = "mfm." + sha256(key.encode()).hexdigest() + "." + phase
        return OperationConfig("config." + node, phase, module, specification.identity, specification.settings_json, assignments, specification.evidence_scope)
    rows = []
    for assignment in specification.assignments:
        for module in assignment.modules:
            if specification.mode == "new-development":
                rows.append(make("acquire", module, (assignment,)))
            rows.append(make("analyse", module, (assignment,)))
    for module in MODULES:
        assigned = tuple(r for r in specification.assignments if module in r.modules)
        if assigned:
            rows.append(make("synthesise", module, assigned))
    return tuple(sorted(rows, key=lambda c: c.node_id))


def scientific_root(specification):
    prefix = "study." + NAMESPACE + "." + specification.fingerprint()
    digest = sha256(specification.settings_json.encode()).hexdigest()
    system = ObjectIdentity("system.matrix.model-free." + digest, PREFIX_SYSTEM, "1.0.0", digest)
    claim = ClaimSpec("claim." + prefix, WORLD, "population." + specification.fingerprint(), QUESTION,
        "Six Hermitian 4x4 matrices; observations, recipes, ports and time origins remain nested within roots.",
        "unit.independent-matrix-root", None, EvidenceCeiling.NON_PROMOTABLE, ACCESS, VISIBILITY,
        "Numerical development with declared direct/certified/statistical scope. No molecular or protected qualification.",
        ("assumption.declared-physical-measure", "assumption.independent-root-population"))
    operands = (specification.identity,) + tuple(r.identity for r in specification.retained_inputs)
    return DevelopmentStudySpec(prefix, QUESTION, system, WORLD, WorldKind.NUMERICAL_SIMULATOR,
        specification.independent_unit_ids, ("view.primary",), (claim,), tuple(sorted(operands, key=lambda p: p.object_id)))


PREFIX_SYSTEM = "empirical-lawhood/matrix-model-free/system-settings"


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
    index = {(c.phase, c.module, c.assignments[0].seed): c for c in configs if c.phase != "synthesise"}
    links, requirements, connections = [], [], []
    retained = {r.key: r for r in specification.retained_inputs}
    scope = ScientificConditionScope(root.system.object_id, WORLD, "source.matrix.baoab",
        ("matrix-task-specific-response",), ("model-units",), "receiver.matrix.declared", "clock.physical-model-time",
        "Native inputs, preparation and root dependence retained; direct suppliers do not require a learned calibration.",
        source_config_sha256=sha256(specification.settings_json.encode()).hexdigest(), population_id=root.claims[0].relation_id)

    def connect(consumer, port, supplier, key=None):
        suffix = consumer.node_id + "." + port
        if supplier is None:
            links.append(RecursiveInputLink("edge." + suffix, consumer.node_id, port,
                external_input_id="external." + retained[key].key, scientific_role="HISTORY"))
            links.append(RecursiveInputLink("edge." + suffix + ".arrays", consumer.node_id, "arrays." + port,
                external_input_id="external.arrays." + key, scientific_role="HISTORY"))
            return
        requirement = ScientificRequirementSpec("requirement." + suffix, consumer.node_id, ConditionRole.INFORMATIONAL,
            "Supply the original " + port + " with its exact physical and assigned-root identity.",
            "Original configuration, root, module and immutable output agree with the authored dependency.",
            scope, consumer.node_id, "Changed, missing, future or incompatible physical operands refuse this supply.",
            (ContributionRole.INSTANCE_PRODUCT,), background_assumption_ids=("assumption.independent-root-population",))
        connection = ScientificConnectionSpec("connection." + suffix, requirement.requirement_id,
            supplier.node_id, "product", port, consumer.node_id, root.claims[0].claim_id,
            ContributionRole.INSTANCE_PRODUCT, requirement.falsifier)
        requirements.append(requirement)
        connections.append(connection)
        links.append(RecursiveInputLink("edge." + suffix, consumer.node_id, port, supplier.node_id, "product",
            scientific_role="HISTORY", requirement_id=requirement.requirement_id, connection_id=connection.connection_id))
        if supplier.phase == "acquire":
            links.append(RecursiveInputLink("edge." + suffix + ".arrays", consumer.node_id, "arrays." + port,
                supplier.node_id, "arrays", scientific_role="HISTORY"))

    for config in configs:
        if config.phase == "synthesise":
            for root_assignment in config.assignments:
                connect(config, "analyses." + root_assignment.unit_id, index[("analyse", config.module, root_assignment.seed)])
        elif config.phase == "analyse":
            assignment = config.assignments[0]
            connect(config, "acquisition", index.get(("acquire", config.module, assignment.seed)), selection_key(config.module, assignment))
        else:
            for module in PREREQUISITES.get(config.module, ()):
                connect(config, "prerequisites." + module.lower(), index[("acquire", module, config.assignments[0].seed)])
    external = tuple(RecursiveExternalInput("external." + r.key, r.identity.object_id, r.identity.object_schema,
        "application/json", None, ACCESS, VISIBILITY, r.identity.object_fingerprint, scientific_role="HISTORY") for r in specification.retained_inputs)
    external += tuple(RecursiveExternalInput("external." + r.key, r.identity.artifact_id, r.identity.payload_schema,
        r.identity.media_type, max(1, r.identity.size_bytes), ACCESS, VISIBILITY, r.identity.sha256, scientific_role="HISTORY") for r in specification.retained_arrays)
    return (tuple(sorted(requirements, key=lambda x: x.requirement_id)), tuple(sorted(connections, key=lambda x: x.connection_id)),
        tuple(sorted(links, key=lambda x: x.edge_id)), tuple(sorted(external, key=lambda x: x.input_id)))


def lower(specification, records):
    from .bindings import operation_declarations
    configs = configs_for(specification)
    declarations = {d.capability_key.rsplit(".", 1)[-1]: d for d in operation_declarations()}
    operations = tuple(RecursiveOperationSpec.from_config(node_id=c.node_id,
        selection=declarations[c.phase].registration().selection, config_id=c.config_id, config=c,
        obligation_ids=("obligation." + c.node_id,), resource_budget=budget_for(c)) for c in configs)
    root = scientific_root(specification)
    requirements, connections, links, external = graph_for(specification, configs)
    draft = RecursiveStudyDraft(draft_id="draft." + specification.specification_id, question=QUESTION,
        campaign=campaign_for(root, configs), requirements=requirements, connections=connections, suppliers=(), operations=operations,
        external_inputs=external, links=links, selected_operation_ids=tuple(c.node_id for c in configs), development_study=root)
    return draft, tuple(sorted(("external." + key, record) for key, record in records.items()))
