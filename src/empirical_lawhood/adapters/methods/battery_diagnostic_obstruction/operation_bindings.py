# SPDX-License-Identifier: MPL-2.0
"""Registered PURE history assessment; original MODEL custody remains receipt-bound."""

from empirical_lawhood.runtime.recursive_provider import (RecursiveOperationDeclaration,RecursiveExecutionProperties,RecursiveInquiryHooks,RecursiveScientificHooks)

from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import (
    BatteryInquirySupply,
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
from . import science
from .contracts import (
    NAMESPACE,
    UNIT,
    QUESTION,
    ObstructionOperationConfig,
    ObstructionSource,
    ObstructionAssessment,
    identity,
)

MEDIA = "application/json"
MAX_BYTES = None
BUDGET = ResourceBudget(1, None, 0, None, None, None)
PORTS = (
    ("obstruction-source", ObstructionSource),
    ("prior", BatteryInquirySupply),
)
NODE = NAMESPACE + ".assess"
CONDITION = "Authentic negative original36/9 MODEL supplies context for independent operational obstruction-history assessment; missing diagnostic completion and all underlying native counts remain unknown."
FALSIFIER = "Changed actual prior MODEL, substituted plan/contact/terminal/input custody, hidden result/receipt, invented zero/completed native counts or numerical adequacy."


def scientific_operand_sha256s(config):
    return tuple(sorted(r.object_fingerprint for r in config.operands))


def scientific_unit_ids(config):
    return (UNIT,)


def development_root(config, *, study_id):
    view = "view." + NAMESPACE + ".complete-adverse-operational-ledger"
    claim = ClaimSpec(
        "claim." + NODE,
        science.original_scope(config.source.diagnostic_source.original).world_id,
        "population.battery-thermal-inquiry.exposed-lgm50",
        QUESTION,
        "Retained operational unknown-completion history and original negative36/9 numerical context; no returned diagnostic result.",
        UNIT,
        None,
        EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY,
        "Operational history conformance grants no numerical adequacy, retry, physical qualification or controller authority.",
        ("assumption.unknown-diagnostic-completion",),
        numerical_view_ids=(view,),
    )
    return DevelopmentStudySpec(
        study_id,
        QUESTION,
        ObjectIdentity.from_record(
            science.original_scope(config.source.diagnostic_source.original).system_id,
            config.source.diagnostic_source.original,
        ),
        science.original_scope(config.source.diagnostic_source.original).world_id,
        WorldKind.NUMERICAL_SIMULATOR,
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
            "obstruction changes exact scientific root, stage, preparation or access"
        )
    incoming = tuple(r for r in context.links if r.consumer_node_id == NODE)
    roles = {name: "MODEL" if name == "prior" else "SOURCE" for name, _ in PORTS}
    if (
        len(incoming) != 2
        or {r.consumer_input_id for r in incoming} != set(roles)
        or any(
            r.external_input_id is None
            or r.scientific_role != roles[r.consumer_input_id]
            for r in incoming
        )
    ):
        raise ValueError(
            "obstruction changes source versus actual outcome roles or complete operand census"
        )
    if len(context.requirements) != 1 or context.requirements[
        0
    ].scope != science.original_scope(config.source.diagnostic_source.original):
        raise ValueError("obstruction changes original prior-outcome scientific scope")


def project_assessments(record, requirement, connection, *, node_id=NODE):
    from .recursive_translation import validate_requirement

    validate_requirement(record, requirement, connection, node_id=node_id)
    return tuple(
        RequirementSupplyAssessment(
            "assessment." + record.product_id + "." + phase.value.lower(),
            ObjectIdentity.from_record(requirement.requirement_id, requirement),
            ObjectIdentity.from_record(connection.connection_id, connection),
            phase,
            AssessmentDisposition.SATISFIED,
            record.original_negative_supply.object_id,
            (identity(record),),
            (),
        )
        for phase in AssessmentPhase
    )


def operation_declarations():
    from .recursive_translation import describe_contributions, next_wave_builder, inquiry_outcome_projector, inquiry_evidence_projector, inquiry_endpoint_validator
    return (RecursiveOperationDeclaration(
        capability_key=NAMESPACE + '.' + 'assess', capability_version='1.0.0',
        implementation_id=NAMESPACE + '.exact-adverse-history-v1', kind=CapabilityKind.ANALYSIS,
        config_record_type=ObstructionOperationConfig, stage=ScientificStage.FALSIFY,
        input_ports=tuple((RecursivePortContract(name, r.SCHEMA, MEDIA, None) for name, r in PORTS)),
        outputs=(OutputTemplate('product', ObstructionAssessment.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA, '.json'),),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=BUDGET,
        conformance_check_ids=('complete-adverse-and-unknown-execution-census', 'exact-primary-history-and-negative-model', 'no-absent-result-or-numerical-qualification'),
        runner_factory=ObstructionRunner, record_codecs=output_codecs(),
        scientific_hooks=RecursiveScientificHooks(
            assessment_projector=project_assessments, scientific_operand_sha256s=scientific_operand_sha256s,
            scientific_unit_ids=scientific_unit_ids, scientific_root_validator=scientific_root_validator,
        ),
        execution_properties=RecursiveExecutionProperties(
            native_effect=False,
        ),
        inquiry_hooks=RecursiveInquiryHooks(
            contribution_describer=describe_contributions, next_wave_builder=next_wave_builder,
            inquiry_outcome_projector=inquiry_outcome_projector, inquiry_evidence_projector=inquiry_evidence_projector,
            inquiry_endpoint_validator=inquiry_endpoint_validator,
        ),
    ),)

def operation_manifests():
    return tuple(row.manifest() for row in operation_declarations())


def operation_registrations():
    return tuple(row.registration() for row in operation_declarations())


def output_codecs():
    return {
        r.SCHEMA: r
        for r in (
            ObstructionOperationConfig,
            ObstructionAssessment,
            *(r for _, r in PORTS),
        )
    }


class ObstructionRunner:
    def __init__(self):
        self.manifest = operation_manifests()[0]

    def execute(self, context):
        try:
            expected = output_codecs()
            expected.pop(ObstructionAssessment.SCHEMA)
            if (
                context.task_id != NODE
                or context.permissions != self.manifest.permissions
                or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or context.resource_budget != BUDGET
                or len(context.input_ports) != len(expected)
                or {p.payload_schema for p in context.input_ports} != set(expected)
            ):
                raise ValueError(
                    "obstruction worker changes complete pure input/access census"
                )
            records = {}
            for p in context.input_ports:
                if (
                    p.kind is not WorkerInputKind.EXTERNAL
                    or p.media_type != MEDIA
                    or p.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                ):
                    raise ValueError(
                        "obstruction worker changes exposed canonical input contract"
                    )
                raw = p.read()
                if len(raw) != p.size_bytes:
                    raise ValueError(
                        "obstruction worker changes exact materialization bytes"
                    )
                records[p.payload_schema] = decode_canonical_bytes(
                    raw, expected[p.payload_schema], maximum_bytes=None
                )
            config = records[ObstructionOperationConfig.SCHEMA]
            if (
                config.config_id != context.config.config_id
                or config.fingerprint() != context.config.content_sha256
            ):
                raise ValueError(
                    "obstruction worker substitutes immutable selected preparation/config"
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
                    "obstruction worker substitutes exact source or prior outcome"
                )
            if inputs["prior"].scope != science.original_scope(
                config.source.diagnostic_source.original
            ):
                raise ValueError(
                    "obstruction worker substitutes original prior scientific scope"
                )
            product = science.assess(inputs["obstruction-source"], inputs["prior"])
            if (
                len(context.output_ports) != 1
                or context.output_ports[0].output_id != NODE + ".product"
                or context.output_ports[0].payload_schema
                != ObstructionAssessment.SCHEMA
                or context.output_ports[0].profile is not ArtifactProfile.CANONICAL_JSON
                or context.output_ports[0].media_type != MEDIA
            ):
                raise ValueError(
                    "obstruction worker changes exact history output census"
                )
            return RunnerResult(
                (TaskOutputPayload(NODE + ".product", product.canonical_bytes()),),
                (ReceiptCheck("exact-adverse-history-no-numerical-qualification", True, ()),),
            )
        finally:
            for port in context.input_ports:
                port.close()
