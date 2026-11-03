# SPDX-License-Identifier: MPL-2.0
"""Registered PURE preparation; original OUTCOME authority remains receipt-bound."""

from empirical_lawhood.adapters.methods.rubisco_cycle_constraints.contracts import (
    CycleUseProduct,
)
from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry.science import (
    SourceAudit,
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
    AssessmentDisposition,
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
from . import science
from .contracts import (
    NAMESPACE,
    UNIT,
    QUESTION,
    NominationOperationConfig,
    NominationPreparationSource,
    NominationDossier,
    identity,
)

MEDIA = "application/json"
MAX_BYTES = None
BUDGET = ResourceBudget(1, None, 0, None, None, None)
PORTS = (
    ("cycle-outcome", CycleUseProduct),
    ("macro-source", SourceAudit),
    ("preparation", NominationPreparationSource),
)
NODE = NAMESPACE + ".prepare"
CONDITION = "Authentic assessed conditional gas-cycle outcome may constrain an exploratory test-nomination dossier; mutation-to-microrates and biological admission remain unknown."
FALSIFIER = "Changed prior outcome/source, mismatched material, omitted adverse or unknown targets, fake assay entry or qualification."


def scientific_operand_sha256s(config):
    return tuple(sorted(r.object_fingerprint for r in config.operands))


def scientific_unit_ids(config):
    return (UNIT,)


def development_root(config, *, study_id):
    view = "view." + NAMESPACE + ".complete-source-and-target-ledger"
    claim = ClaimSpec(
        "claim." + NODE,
        config.cycle_scope.world_id,
        "population.exposed-proposed-material",
        QUESTION,
        "Proposed exact material and paired-assay preparation, with complete historical/unknown target ledger; no fresh biological units.",
        UNIT,
        None,
        EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY,
        "Preparation adequacy grants no assay, target qualification, prize success or external submission.",
        (
            "all-assays-proposed-not-entered",
            "conditional-microrates-not-measured",
            "m1-processing-unverified",
        ),
        numerical_view_ids=(view,),
    )
    return DevelopmentStudySpec(
        study_id,
        QUESTION,
        ObjectIdentity.from_record(config.cycle_scope.system_id, config.preparation),
        config.cycle_scope.world_id,
        WorldKind.ANALYTIC_REFERENCE,
        (UNIT,),
        (view,),
        (claim,),
        config.operands,
    )


def scientific_root_validator(config, context):
    if (
        type(context.root) is not DevelopmentStudySpec
        or context.root != development_root(config, study_id=context.root.study_id)
        or context.node_id != NODE
        or context.stage is not ScientificStage.FALSIFY
        or context.unit_ids != (UNIT,)
        or context.selected_unit_ids != (UNIT,)
        or context.complete_unit_census
        or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
        or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
        or len(context.config_inputs) != 1
        or context.config_inputs[0].record != config
    ):
        raise ValueError(
            "nomination changes exact scientific root, stage, preparation or access"
        )
    incoming = tuple(r for r in context.links if r.consumer_node_id == NODE)
    roles = {
        name: "OUTCOME" if name == "cycle-outcome" else "SOURCE" for name, _ in PORTS
    }
    if (
        len(incoming) != 3
        or {r.consumer_input_id for r in incoming} != set(roles)
        or any(
            r.external_input_id is None
            or r.scientific_role != roles[r.consumer_input_id]
            for r in incoming
        )
    ):
        raise ValueError(
            "nomination changes source versus actual outcome roles or complete operand census"
        )
    if (
        len(context.requirements) != 1
        or context.requirements[0].scope != config.cycle_scope
    ):
        raise ValueError("nomination changes original prior-outcome scientific scope")


def project_assessments(record, requirement, connection):
    from .recursive_translation import validate_requirement

    validate_requirement(record, requirement, connection)
    return tuple(
        RequirementSupplyAssessment(
            "assessment." + record.product_id + "." + phase.value.lower(),
            ObjectIdentity.from_record(requirement.requirement_id, requirement),
            ObjectIdentity.from_record(connection.connection_id, connection),
            phase,
            AssessmentDisposition.SATISFIED,
            record.preparation.proposed_material_id,
            (identity(record),),
            (),
        )
        for phase in AssessmentPhase
    )


def output_codecs():
    return {
        r.SCHEMA: r
        for r in (NominationOperationConfig, NominationDossier, *(r for _, r in PORTS))
    }


class NominationRunner:
    def __init__(self):
        self.manifest = operation_manifests()[0]

    def execute(self, context):
        try:
            expected = output_codecs()
            expected.pop(NominationDossier.SCHEMA)
            if (
                context.task_id != NODE
                or context.permissions != self.manifest.permissions
                or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or context.resource_budget != BUDGET
                or len(context.input_ports) != len(expected)
                or {p.payload_schema for p in context.input_ports} != set(expected)
            ):
                raise ValueError(
                    "nomination worker changes complete pure input/access census"
                )
            records = {}
            for p in context.input_ports:
                if (
                    p.kind is not WorkerInputKind.EXTERNAL
                    or p.media_type != MEDIA
                    or p.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                ):
                    raise ValueError(
                        "nomination worker changes exposed canonical input contract"
                    )
                raw = p.read()
                if len(raw) != p.size_bytes:
                    raise ValueError(
                        "nomination worker changes exact materialization bytes"
                    )
                records[p.payload_schema] = decode_canonical_bytes(
                    raw, expected[p.payload_schema], maximum_bytes=None
                )
            config = records[NominationOperationConfig.SCHEMA]
            if (
                config.config_id != context.config.config_id
                or config.fingerprint() != context.config.content_sha256
            ):
                raise ValueError(
                    "nomination worker substitutes immutable selected preparation/config"
                )
            inputs = {name: records[r.SCHEMA] for name, r in PORTS}
            if (
                tuple(
                    sorted(
                        (identity(r) for r in inputs.values()),
                        key=lambda r: r.object_id,
                    )
                )
                != config.operands
            ):
                raise ValueError(
                    "nomination worker substitutes exact source or prior outcome"
                )
            if inputs["cycle-outcome"].scope != config.cycle_scope:
                raise ValueError(
                    "nomination worker substitutes original prior scientific scope"
                )
            product = science.prepare(
                inputs["preparation"], inputs["macro-source"], inputs["cycle-outcome"]
            )
            if (
                len(context.output_ports) != 1
                or context.output_ports[0].output_id != NODE + ".product"
                or context.output_ports[0].payload_schema != NominationDossier.SCHEMA
                or context.output_ports[0].profile is not ArtifactProfile.CANONICAL_JSON
                or context.output_ports[0].media_type != MEDIA
            ):
                raise ValueError(
                    "nomination worker changes exact dossier output census"
                )
            return RunnerResult(
                (TaskOutputPayload(NODE + ".product", product.canonical_bytes()),),
                (ReceiptCheck("exact-exploratory-dossier-no-assay-entry", True, ()),),
            )
        finally:
            for port in context.input_ports:
                port.close()


def operation_manifests():
    return tuple(declaration.manifest() for declaration in operation_declarations())


def operation_declarations():
    """Own the pure scientific operation and its existing inquiry hooks."""
    from .recursive_translation import (
        describe_contributions, inquiry_endpoint_validator, inquiry_evidence_projector,
        inquiry_outcome_projector, next_wave_builder,
    )

    return (RecursiveOperationDeclaration(
        capability_key=NAMESPACE + ".prepare", capability_version="1.0.0",
        implementation_id=NAMESPACE + ".exact-exploratory-preparation-v1", kind=CapabilityKind.ANALYSIS,
        config_record_type=NominationOperationConfig, stage=ScientificStage.FALSIFY,
        input_ports=tuple(RecursivePortContract(name, record.SCHEMA, MEDIA, None)
            for name, record in PORTS),
        outputs=(OutputTemplate("product", NominationDossier.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, MEDIA, ".json"),),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=BUDGET,
        conformance_check_ids=("complete-adverse-and-unknown-targets",
            "exact-material-source-and-prior-outcome", "no-entered-assay-or-biological-qualification"),
        runner_factory=NominationRunner, record_codecs=output_codecs(),
        scientific_hooks=RecursiveScientificHooks(assessment_projector=project_assessments,
            scientific_operand_sha256s=scientific_operand_sha256s,
            scientific_unit_ids=scientific_unit_ids, scientific_root_validator=scientific_root_validator),
        inquiry_hooks=RecursiveInquiryHooks(contribution_describer=describe_contributions,
                next_wave_builder=next_wave_builder, inquiry_outcome_projector=inquiry_outcome_projector,
                inquiry_evidence_projector=inquiry_evidence_projector,
                inquiry_endpoint_validator=inquiry_endpoint_validator)),)
