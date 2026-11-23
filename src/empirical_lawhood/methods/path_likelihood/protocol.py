# SPDX-License-Identifier: MPL-2.0
"""Bind finite path experiments to the ordinary EL recursive investigation."""

from functools import partial
from hashlib import sha256

from empirical_lawhood.design.campaigns import (
    CampaignLane,
    CampaignNode,
    CampaignNodeKind,
    CampaignSpec,
    DecisionRight,
)
from empirical_lawhood.design.evidence_profiles import ExperimentObjectiveProfile
from empirical_lawhood.design.recursive_authoring import (
    RecursiveInputLink,
    RecursiveOperationSpec,
    RecursiveStudyDraft,
)
from empirical_lawhood.execution.capabilities import CapabilityPermission
from empirical_lawhood.execution.discovery_descriptors import EnvironmentDeclaration
from empirical_lawhood.execution.experiment_preparation import (
    DependencyKind,
    ExperimentCensus,
    ExperimentDependency,
    ExperimentPreparation,
    ExperimentProtocolDeclaration,
    PreparedExperimentInputs,
)
from empirical_lawhood.execution.extension_bundles import (
    ExtensionProfileKind,
    ExtensionProfileRegistration,
)
from empirical_lawhood.execution.extensions import ExtensionDeclaration
from empirical_lawhood.execution.installation_descriptors import (
    WorkflowInstallationDeclaration,
)
from empirical_lawhood.execution.plans import ScientificStage
from empirical_lawhood.execution.workflow_descriptors import (
    Workflow,
    WorkflowDeclaration,
    WorkflowInput,
    WorkflowOperation,
)
from empirical_lawhood.science.evidence.evidence import (
    ClaimSpec,
    EvidenceCeiling,
    OutcomeAccess,
    VisibilityCeiling,
)
from empirical_lawhood.science.experiments.experimental_design import (
    IndependentUnit,
    UnitAllocation,
    UnitRoleAssignment,
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
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.science.records.status import LifecycleStatus

from . import arrays
from .records import operations, required_parents

ACCESS, VISIBILITY = (
    OutcomeAccess.DEVELOPMENT_VISIBLE,
    VisibilityCeiling.DEVELOPMENT_ONLY,
)
BUDGET = ResourceBudget(1, 2 * 1024**3, 0, None, None, None)
PERMISSIONS = tuple(
    sorted(
        (
            CapabilityPermission.READ_DEVELOPMENT,
            CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
        )
    )
)
STAGES = {
    "prefix": ScientificStage.ACQUIRE,
    "observe": ScientificStage.TRANSFORM,
    "predict": ScientificStage.FREEZE,
    "develop": ScientificStage.ACQUIRE,
    "evaluate": ScientificStage.ACQUIRE,
    "freeze": ScientificStage.DEVELOP,
    "assess": ScientificStage.FALSIFY,
}


def allocation(spec):
    blocks = [c for c in operations(spec) if c.phase in ("develop", "evaluate")]
    return UnitAllocation(
        "allocation." + spec.specification_id,
        (spec.identity,),
        tuple(
            sorted(
                (
                    IndependentUnit(
                        c.unit_id,
                        spec.specification_id,
                        "family." + spec.FAMILY,
                        (),
                        False,
                    )
                    for c in blocks
                ),
                key=lambda u: u.unit_id,
            )
        ),
        tuple(
            sorted(
                (
                    UnitRoleAssignment(
                        c.unit_id,
                        "development" if c.phase == "develop" else "confirmation",
                    )
                    for c in blocks
                ),
                key=lambda u: u.unit_id,
            )
        ),
    )


def graph(spec, configs):
    d = spec.design
    system = ObjectIdentity.from_record("system." + spec.FAMILY, d)
    world = "world." + spec.FAMILY
    claim = ClaimSpec(
        "claim." + spec.specification_id,
        world,
        "population." + d.fingerprint(),
        spec.QUESTION,
        spec.POPULATION,
        "unit.independent-path-family",
        None,
        EvidenceCeiling.NON_PROMOTABLE,
        ACCESS,
        VISIBILITY,
        "Numerical experiment on the authored population with separate held-out roots.",
        ("assumption.independent-innovation-streams",),
    )
    root = DevelopmentStudySpec(
        "study." + spec.specification_id,
        spec.QUESTION,
        system,
        world,
        WorldKind.NUMERICAL_SIMULATOR,
        tuple(sorted({c.unit_id for c in configs if c.acquires})),
        (),
        (claim,),
        (spec.identity,),
    )
    scope = ScientificConditionScope(
        system.object_id,
        world,
        "source." + spec.FAMILY,
        ("path-measurement",),
        ("model-units",),
        "receiver." + spec.FAMILY,
        "clock.model-time",
        spec.POPULATION,
        source_config_sha256=d.fingerprint(),
        population_id=claim.relation_id,
    )
    requirements, connections, links = [], [], []
    for c in configs:
        for supplier in required_parents(c, configs):
            suffix = c.node_id + "." + supplier.phase + "." + str(supplier.first)
            port = "parents." + supplier.node_id
            requirement = ScientificRequirementSpec(
                "requirement." + suffix,
                c.node_id,
                ConditionRole.INFORMATIONAL,
                "Supply the original path measurements or pre-evaluation decision.",
                "Exact root range, phase, clock and source.",
                scope,
                c.node_id,
                "Substitution of a block, decision or array invalidates this assessment.",
                (ContributionRole.INSTANCE_PRODUCT,),
            )
            connection = ScientificConnectionSpec(
                "connection." + suffix,
                requirement.requirement_id,
                supplier.node_id,
                "product",
                port,
                c.node_id,
                claim.claim_id,
                ContributionRole.INSTANCE_PRODUCT,
                requirement.falsifier,
            )
            requirements.append(requirement)
            connections.append(connection)
            links.append(
                RecursiveInputLink(
                    "edge." + suffix,
                    c.node_id,
                    port,
                    supplier.node_id,
                    "product",
                    scientific_role="HISTORY",
                    requirement_id=requirement.requirement_id,
                    connection_id=connection.connection_id,
                )
            )
            if supplier.acquires:
                links.append(
                    RecursiveInputLink(
                        "edge.arrays." + suffix,
                        c.node_id,
                        "arrays." + supplier.node_id,
                        supplier.node_id,
                        "arrays",
                        scientific_role="HISTORY",
                    )
                )
    return (
        root,
        tuple(sorted(requirements, key=lambda x: x.requirement_id)),
        tuple(sorted(connections, key=lambda x: x.connection_id)),
        tuple(sorted(links, key=lambda x: x.edge_id)),
    )


def lower(spec, declarations):
    configs = operations(spec)
    root, reqs, conns, edges = graph(spec, configs)
    budget = ResourceBudget.aggregate(BUDGET for c in configs)
    owner = root.study_id
    policy = AuthorityPolicy(
        owner + ".policy",
        "human.selected-operator",
        "researcher.path-ensembles",
        (spec.FAMILY + ".numerical",),
        frozenset({WorldKind.NUMERICAL_SIMULATOR}),
        frozenset({AuthorityAction.SIMULATION_EXECUTION}),
        frozenset({SourceAccessClass.NONE}),
        ("source-bound-numerical-design",),
        frozenset(),
        budget,
        ACCESS,
    )
    node = CampaignNode(
        owner + ".proposal",
        CampaignNodeKind.ANALYSIS_PROPOSAL,
        CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(owner, root),
        (),
        LifecycleStatus.ACTIVE,
    )
    campaign = CampaignSpec(
        owner + ".campaign",
        spec.QUESTION,
        (root.system.object_id,),
        (root.world_id,),
        (root.claims[0].claim_id,),
        budget,
        ObjectIdentity.from_record(policy.policy_id, policy),
        (
            DecisionRight(
                owner + ".right",
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
    registered = {
        v.capability_key.split(".")[-1]: v.registration().selection
        for v in declarations
    }
    selected = tuple(
        RecursiveOperationSpec.from_config(
            node_id=c.node_id,
            selection=registered[c.phase],
            config_id=c.config_id,
            config=c,
            obligation_ids=("obligation." + c.node_id,),
            resource_budget=BUDGET,
        )
        for c in configs
    )
    return RecursiveStudyDraft(
        "draft." + spec.specification_id,
        spec.QUESTION,
        campaign,
        reqs,
        conns,
        (),
        selected,
        (),
        edges,
        tuple(c.node_id for c in configs),
        development_study=root,
    )


def bind_inputs(specification, records, *, files=None):
    specification.__post_init__()
    if records or files:
        raise ValueError(
            "path ensemble has an exact native seed allocation and no external outcomes"
        )
    return PreparedExperimentInputs({"allocation": allocation(specification)}, {})


def prepare(
    specification,
    *,
    scientific_inputs,
    execution,
    method_inputs=None,
    protocol_bytes=None,
    declarations,
):
    bound = bind_inputs(specification, method_inputs or {})
    if protocol_bytes is not None or scientific_inputs != bound.scientific_inputs:
        raise ValueError("path ensemble original input selection differs")
    dependencies = tuple(
        ExperimentDependency(
            "paths.execution." + key, DependencyKind.ENVIRONMENT, "Select " + key + "."
        )
        for key in ("environment_id", "output_root", "source_snapshot", "workers")
        if getattr(execution, key) is None
        or (
            key == "environment_id" and execution.environment_id != specification.FAMILY
        )
    )
    d = specification.design
    counts = (
        ("development-roots", d.development_roots),
        ("evaluation-roots", d.evaluation_roots),
    )
    configs = operations(specification)
    return ExperimentPreparation(
        specification.identity,
        ExperimentCensus(
            counts,
            counts if not dependencies else tuple((k, 0) for k, _ in counts),
            (("operations", len(configs)),),
            (
                ("array-batches", sum(c.acquires for c in configs)),
                ("canonical-products", len(configs)),
            ),
            0,
        ),
        dependencies,
        allocation=None if dependencies else bound.scientific_inputs["allocation"],
        draft=None if dependencies else lower(specification, declarations),
        execution=execution,
        specification_record=specification,
    )


def validate_instance(
    *, specification, allocation, draft, source_records, declarations
):
    expected = bind_inputs(specification, {}).scientific_inputs["allocation"]
    if (
        source_records
        or expected != allocation
        or draft != lower(specification, declarations)
    ):
        raise ValueError("authored path allocation or original causal graph changed")


def extension(spec_type, acquire, evaluate, guide, order, *, additional_definitions=()):
    from .workers import operation_declarations

    ns = spec_type.FAMILY
    decls = operation_declarations(spec_type, acquire, evaluate)
    profile = ExtensionProfileRegistration(
        "profile-registration." + ns + ".workflow",
        ns + ".workflow",
        "1.0.0",
        ExtensionProfileKind.OBJECTIVE_TERMINAL,
        ExperimentObjectiveProfile.SCHEMA,
        sha256(ExperimentObjectiveProfile.SCHEMA.encode()).hexdigest(),
        sha256(
            canonical_json_bytes(tuple(d.manifest().fingerprint() for d in decls))
        ).hexdigest(),
    )
    directory = guide.rsplit("/", 1)[0]
    definitions = (
        ("experiment.json", "Complete numerical experiment"),
        ("smoke.json", "Small numerical control"),
        *additional_definitions,
    )
    inputs = tuple(
        WorkflowInput(f"{directory}/{filename}", role, spec_type.definition_schema_id())
        for filename, role in definitions
    )
    definition_paths = tuple(item.path for item in inputs)
    workflow = WorkflowDeclaration(
        Workflow(
            workflow_id=ns,
            title=spec_type.TITLE,
            kind="recursive numerical path experiment",
            substrates=(spec_type.POPULATION,),
            methods=(
                "Predeclared finite path ensemble with independent physical references.",
            ),
            environment=ns,
            operations=tuple(
                WorkflowOperation(
                    "campaign experiment-" + op,
                    summary,
                    definition_paths,
                )
                for op, summary in (
                    ("prepare", "Validate the original allocation"),
                    ("author", "Freeze the source and causal stages"),
                    ("run", "Acquire path families and assess their laws"),
                    ("read", "Read original receipts and scientific results"),
                    ("recover", "Recover settled original work"),
                )
            ),
            inputs=inputs,
            input_availability="Select one numerical recipe and a new external workspace.",
            scientific_ceiling="Source-bound numerical evidence under the declared observer and clock.",
            first_missing_prerequisite="Select the locked numerical environment and storage.",
            guide=guide,
            verification_owners=("tests/test_path_ensembles.py",),
        ),
        "Independent numerical benchmark and held-out path assessment",
        catalogue_order=order,
    )
    return ExtensionDeclaration(
        extension_id=ns,
        version="1.0.0",
        operations=decls,
        profiles=(profile,),
        protocols=(
            ExperimentProtocolDeclaration(
                ns + ".numerical",
                spec_type,
                partial(prepare, declarations=decls),
                ns + "-experiment",
                maximum_config_bytes=None,
                bind_inputs=bind_inputs,
                validate_instance=partial(validate_instance, declarations=decls),
                input_storage_codecs=(arrays.CODEC,),
            ),
        ),
        workflows=(workflow,),
        environments=(
            EnvironmentDeclaration(
                route_id=ns,
                python_version="3.11.14",
                distribution_versions=(("numpy", "2.4.6"), ("scipy", "1.17.1")),
                lock_path="uv.lock",
                python_implementation="CPython",
                descriptor_version="1.0.0",
                dependency_groups=(),
                supported_platforms=(("Linux", "x86_64"),),
            ),
        ),
        installations=(
            WorkflowInstallationDeclaration(
                workflow_id=ns,
                profile_id="standard",
                adapter_module=spec_type.__module__.rsplit(".", 1)[0],
                adapter_version="1.0.0",
                controller_environment=ns,
                workers=(),
                external_software=(),
                source_prerequisites=(
                    "Select the original definition and explicit storage.",
                ),
                continuing_source_prerequisites=(),
                descriptor_version="1.0.0",
            ),
        ),
    )
