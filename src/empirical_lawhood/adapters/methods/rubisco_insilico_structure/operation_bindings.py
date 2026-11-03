# SPDX-License-Identifier: MPL-2.0
"""Cold PURE observed-source mapping registrations; no modeling engine imports."""

from empirical_lawhood.adapters.methods.rubisco_nomination_preparation.contracts import (
    NominationDossier,
)
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import (
    ClaimSpec,
    EvidenceCeiling,
    OutcomeAccess,
    VisibilityCeiling,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import (
    AssessmentPhase,
    DevelopmentStudySpec,
    RequirementSupplyAssessment,
)
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import (
    RunnerResult,
    TaskOutputPayload,
    WorkerInputKind,
)
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import (
    RecursivePortContract,
)
from empirical_lawhood.runtime.recursive_provider import (
    RecursiveInquiryHooks, RecursiveOperationDeclaration, RecursiveScientificHooks,
)
from . import contracts as c, science

MEDIA = "application/json"
BUDGET = ResourceBudget(1, None, 0, None, None, None)


def operation_inputs(operation):
    if operation not in ("analyze", "assess"):
        raise ValueError("unknown structural operation")
    return tuple(
        sorted(
            (("source", c.StructuralSource), ("nomination", NominationDossier))
            + ((("inventory", c.StructuralInventory),) if operation == "assess" else ())
        )
    )


def operation_outputs(operation):
    return (
        (("coordinates", c.AssemblyCoordinates), ("inventory", c.StructuralInventory))
        if operation == "analyze"
        else (("assessment", c.StructuralAssessment),)
    )


def development_root(config, *, study_id):
    # The assessed prerequisite is the actual nomination OUTCOME: compiler
    # claims must use its world/system. The new mapping endpoint remains the
    # separately registered c.scope(source), without transporting qualification.
    world = config.nomination_scope.world_id
    view = "view." + c.NAMESPACE + ".observed-source-assembly"
    claim = ClaimSpec(
        "claim." + c.NAMESPACE + ".observed-mapping",
        world,
        "population.exposed-original-structures",
        c.QUESTION,
        "Exact observed activated/inhibited source assemblies and missing-coordinate census; derived mutant comparison pending.",
        c.UNIT,
        None,
        EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY,
        "No kinetic, preparation or fresh biological qualification.",
        ("mutant-comparison-pending", "observed-source-only"),
        numerical_view_ids=(view,),
    )
    return DevelopmentStudySpec(
        study_id,
        c.QUESTION,
        ObjectIdentity.from_record(config.nomination_scope.system_id, config.source),
        world,
        WorldKind.ANALYTIC_REFERENCE,
        (c.UNIT,),
        (view,),
        (claim,),
        config.operands,
    )


def scientific_root_validator(config, context):
    config.__post_init__()
    node = c.NAMESPACE + "." + config.operation
    configs = {row.node_id: row.record for row in context.config_inputs}
    if (
        type(context.root) is not DevelopmentStudySpec
        or context.root != development_root(config, study_id=context.root.study_id)
        or context.node_id != node
        or context.stage is not ScientificStage.FALSIFY
        or context.unit_ids != (c.UNIT,)
        or context.selected_unit_ids != (c.UNIT,)
        or context.complete_unit_census
        or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
        or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
        or len(context.config_inputs) != 2
        or set(configs) != {c.NAMESPACE + ".analyze", c.NAMESPACE + ".assess"}
        or configs.get(node) != config
        or any(
            type(value) is not c.StructureOperationConfig
            or value.source != config.source
            or value.nomination_scope != config.nomination_scope
            or value.operands != config.operands
            for value in configs.values()
        )
    ):
        raise ValueError(
            "structure mapping changes exact scientific root/config/exposure"
        )
    from .recursive_translation import validate_requirement_config

    if len(context.requirements) != 1 or len(context.connections) != 1:
        raise ValueError("structure mapping changes requirement/connection census")
    validate_requirement_config(config, context.requirements[0], context.connections[0])
    links = [r for r in context.links if r.consumer_node_id == node]
    roles = {"source": "SOURCE", "nomination": "OUTCOME"}
    if config.operation == "assess":
        roles["inventory"] = "HISTORY"
    if (
        len(links) != len(roles)
        or {r.consumer_input_id for r in links} != set(roles)
        or any(r.scientific_role != roles[r.consumer_input_id] for r in links)
        or any(
            r.external_input_id is None
            for r in links
            if r.consumer_input_id != "inventory"
        )
        or len(context.requirements) != 1
        or context.requirements[0].scope != config.nomination_scope
    ):
        raise ValueError("structure mapping changes authentic nomination/operand roles")


def scientific_operand_sha256s(config):
    return tuple(sorted(r.object_fingerprint for r in config.operands))


def scientific_unit_ids(config):
    return (c.UNIT,)


def output_codecs():
    return {
        r.SCHEMA: r
        for r in (
            c.StructureOperationConfig,
            c.StructuralSource,
            NominationDossier,
            c.StructuralInventory,
            c.AssemblyCoordinates,
            c.StructuralAssessment,
        )
    }


class StructureRunner:
    def __init__(self, operation):
        self.operation = operation
        self.manifest = dict(
            zip(("analyze", "assess"), operation_manifests(), strict=True)
        )[operation]

    def execute(self, context):
        try:
            expected = {r.SCHEMA: r for _, r in operation_inputs(self.operation)}
            expected[c.StructureOperationConfig.SCHEMA] = c.StructureOperationConfig
            node = c.NAMESPACE + "." + self.operation
            if (
                context.task_id != node
                or context.permissions != self.manifest.permissions
                or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or context.resource_budget != BUDGET
                or len(context.input_ports) != len(expected)
                or {p.payload_schema for p in context.input_ports} != set(expected)
            ):
                raise ValueError("structure worker changes exact PURE census/access")
            records = {}
            for port in context.input_ports:
                if (
                    port.media_type != MEDIA
                    or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                ):
                    raise ValueError(
                        "structure worker changes canonical development input"
                    )
                if (
                    port.payload_schema != c.StructuralInventory.SCHEMA
                    and port.kind is not WorkerInputKind.EXTERNAL
                ):
                    raise ValueError(
                        "structure worker changes authentic external source/nomination"
                    )
                raw = port.read()
                if len(raw) != port.size_bytes:
                    raise ValueError(
                        "structure worker truncates canonical materialization"
                    )
                records[port.payload_schema] = decode_canonical_bytes(
                    raw, expected[port.payload_schema], maximum_bytes=None
                )
            config = records[c.StructureOperationConfig.SCHEMA]
            source = records[c.StructuralSource.SCHEMA]
            dossier = records[NominationDossier.SCHEMA]
            if (
                config.operation != self.operation
                or config.config_id != context.config.config_id
                or config.fingerprint() != context.config.content_sha256
                or source != config.source
                or dossier.scope != config.nomination_scope
                or tuple(
                    sorted(
                        (c.identity(source), c.identity(dossier)),
                        key=lambda r: r.object_id,
                    )
                )
                != config.operands
            ):
                raise ValueError(
                    "structure worker substitutes selected source/nomination/config"
                )
            if self.operation == "analyze":
                inventory = science.analyze(source, dossier)
                outputs = (science.assembly_coordinates(source, inventory), inventory)
            else:
                outputs = (
                    science.assess(
                        source, dossier, records[c.StructuralInventory.SCHEMA]
                    ),
                )
            declared = operation_outputs(self.operation)
            if tuple(
                (p.output_id, p.payload_schema, p.profile, p.media_type)
                for p in context.output_ports
            ) != tuple(
                (
                    node + "." + name,
                    record.SCHEMA,
                    ArtifactProfile.CANONICAL_JSON,
                    MEDIA,
                )
                for name, record in declared
            ):
                raise ValueError("structure worker changes complete output census")
            return RunnerResult(
                tuple(
                    TaskOutputPayload(node + "." + name, record.canonical_bytes())
                    for (name, _), record in zip(declared, outputs, strict=True)
                ),
                (
                    ReceiptCheck(
                        "observed-original-source-mapping-not-mutant-or-kinetics",
                        True,
                        (),
                    ),
                ),
            )
        finally:
            for port in context.input_ports:
                port.close()


def project_assessments(record, requirement, connection):
    from .recursive_translation import validate_requirement_assessment

    validate_requirement_assessment(record, requirement, connection)
    from empirical_lawhood.kernel.provenance import ObjectIdentity

    return tuple(
        RequirementSupplyAssessment(
            "assessment." + record.product_id + "." + phase.value.lower(),
            ObjectIdentity.from_record(requirement.requirement_id, requirement),
            ObjectIdentity.from_record(connection.connection_id, connection),
            phase,
            record.source_disposition,
            record.prior_nomination_scope.instance_id,
            (c.identity(record),),
            tuple(sorted(record.reason_codes)),
        )
        for phase in AssessmentPhase
    )


def operation_manifests():
    return tuple(declaration.manifest() for declaration in operation_declarations())


def operation_declarations():
    """Own analyze/assess ordering and the assess-only independent projector."""
    from .recursive_translation import (
        describe_contributions, inquiry_endpoint_validator, inquiry_evidence_projector,
        inquiry_outcome_projector, next_wave_builder,
    )

    return tuple(RecursiveOperationDeclaration(
        capability_key=c.NAMESPACE + "." + operation, capability_version="1.0.0",
        implementation_id=c.NAMESPACE + ".observed-" + operation + "-v1",
        kind=CapabilityKind.ANALYSIS, config_record_type=c.StructureOperationConfig,
        stage=ScientificStage.FALSIFY,
        input_ports=tuple(RecursivePortContract(name, record.SCHEMA, MEDIA, None)
            for name, record in operation_inputs(operation)),
        outputs=tuple(OutputTemplate(name, record.SCHEMA, ArtifactProfile.CANONICAL_JSON,
            MEDIA, ".json") for name, record in operation_outputs(operation)),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=BUDGET,
        conformance_check_ids=("exact-nomination-and-original-sequences",
            "full-l8s8-original-assembly", "no-built-mutant-or-kinetic-promotion"),
        runner_factory=lambda operation=operation: StructureRunner(operation),
        record_codecs=output_codecs(),
        scientific_hooks=RecursiveScientificHooks(
            assessment_projector=project_assessments if operation == "assess" else None,
            scientific_operand_sha256s=scientific_operand_sha256s,
            scientific_unit_ids=scientific_unit_ids, scientific_root_validator=scientific_root_validator),
        inquiry_hooks=RecursiveInquiryHooks(contribution_describer=describe_contributions,
                next_wave_builder=next_wave_builder, inquiry_outcome_projector=inquiry_outcome_projector,
                inquiry_evidence_projector=inquiry_evidence_projector,
                inquiry_endpoint_validator=inquiry_endpoint_validator))
        for operation in ("analyze", "assess"))
