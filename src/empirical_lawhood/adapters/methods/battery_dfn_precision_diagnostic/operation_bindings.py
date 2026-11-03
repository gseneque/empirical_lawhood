# SPDX-License-Identifier: MPL-2.0
"""Source-bound native singleton operations and exact current trace custody."""

from empirical_lawhood.runtime.recursive_provider import (RecursiveOperationDeclaration,RecursiveExecutionProperties,RecursiveInquiryHooks,RecursiveScientificHooks)

from dataclasses import dataclass
from typing import ClassVar

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
    DevelopmentStudySpec,
    AssessmentDisposition,
    AssessmentPhase,
    RequirementSupplyAssessment,
)
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord,
    require_sorted_unique_ids,
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
from .contracts import DiagnosticSource, DiagnosticResult, QUESTION
from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import (
    BatteryInquirySupply,
    UNIT,
    scope,
)

NAMESPACE = "battery-dfn-precision-diagnostic"
MAX_BYTES = None
MEDIA = "application/json"
BUDGET = ResourceBudget(1, None, 0, None, None, None)
VIEW = "view.battery-dfn-precision-diagnostic.finite-components"


@dataclass(frozen=True, slots=True)
class DiagnosticOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/battery-dfn-precision-diagnostic/operation-config"
    )
    config_id: str
    source: DiagnosticSource
    operands: tuple[ObjectIdentity, ...]
    operation: str = "diagnose"

    def __post_init__(self):
        self.source.__post_init__()
        if self.config_id != "config." + NAMESPACE or self.operation != "diagnose":
            raise ValueError("diagnostic operation identity differs")
        require_sorted_unique_ids(
            self.operands, attribute="object_id", field_name="operands"
        )
        if (
            len(self.operands) != 2
            or science.identity(self.source) not in self.operands
            or len(
                [
                    x
                    for x in self.operands
                    if x.object_schema == BatteryInquirySupply.SCHEMA
                    and x.object_version == BatteryInquirySupply.VERSION
                    and x.object_fingerprint == self.source.prior_supply_sha256
                ]
            )
            != 1
        ):
            raise ValueError(
                "diagnostic operands change exact source or actual outcome"
            )


def scientific_operand_sha256s(config):
    return tuple(sorted(x.object_fingerprint for x in config.operands))


def scientific_unit_ids(config):
    return (UNIT,)


def native_effect_slot_ids(config):
    prior = next(
        x for x in config.operands if x.object_schema == BatteryInquirySupply.SCHEMA
    )
    return tuple(
        sorted(
            "native." + NAMESPACE + "." + c.fingerprint()
            for c in science.configurations(DiagnosticSource(), prior)
        )
    )


def development_root(config, *, study_id):
    original_scope = scope(config.source.original)
    claim = ClaimSpec(
        "claim." + NAMESPACE,
        original_scope.world_id,
        "population.battery-thermal-inquiry.exposed-lgm50",
        QUESTION,
        "Finite12 native forecasts and strict component sensitivity; approximate conservative hybrid numerical models only.",
        UNIT,
        None,
        EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY,
        "Diagnostic sensitivity grants no ideal controller, whole-time, physical, OEM, supplier or use qualification.",
        ("assumption.exposed-lgm50-model-family",),
        numerical_view_ids=(VIEW,),
    )
    return DevelopmentStudySpec(
        study_id,
        QUESTION,
        ObjectIdentity.from_record(original_scope.system_id, config.source.original),
        original_scope.world_id,
        WorldKind.NUMERICAL_SIMULATOR,
        (UNIT,),
        (VIEW,),
        (claim,),
        config.operands,
    )


def scientific_root_validator(config, context):
    if (
        context.root != development_root(config, study_id=context.root.study_id)
        or context.node_id != NAMESPACE + ".diagnose"
        or context.stage is not ScientificStage.ACQUIRE
        or context.unit_ids != (UNIT,)
        or context.selected_unit_ids != (UNIT,)
        or not context.complete_unit_census
        or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
        or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
        or len(context.config_inputs) != 1
        or context.config_inputs[0].record != config
        or len(context.requirements) != 1
        or len(context.connections) != 1
    ):
        raise ValueError("diagnostic changes exact root/scientific question/access")
    from .recursive_translation import validate_requirement_config

    validate_requirement_config(config, context.requirements[0], context.connections[0])
    links = tuple(x for x in context.links if x.consumer_node_id == context.node_id)
    roles = {"source": "SOURCE", "prior": "MODEL"}
    if (
        len(links) != 2
        or {x.consumer_input_id for x in links} != set(roles)
        or any(
            x.external_input_id is None
            or x.scientific_role != roles[x.consumer_input_id]
            or (
                x.consumer_input_id == "prior"
                and (
                    x.requirement_id != context.requirements[0].requirement_id
                    or x.connection_id != context.connections[0].connection_id
                )
            )
            for x in links
        )
    ):
        raise ValueError("diagnostic cannot retype prior outcome as source")


def project_assessments(record, requirement, connection):
    science.validate_result(record)
    config = DiagnosticOperationConfig(
        "config." + NAMESPACE,
        record.source,
        tuple(
            sorted(
                (science.identity(record.source), record.prior_supply),
                key=lambda x: x.object_id,
            )
        ),
    )
    from .recursive_translation import validate_requirement_config

    validate_requirement_config(config, requirement, connection)
    values = []
    for phase in AssessmentPhase:
        disposition = (
            AssessmentDisposition.SATISFIED
            if phase is AssessmentPhase.PROCEDURE
            else record.disposition
        )
        reasons = (
            ()
            if disposition is AssessmentDisposition.SATISFIED
            else tuple(
                sorted(
                    set(
                        reason
                        for row in (*record.checks, *record.comparisons)
                        if row.disposition is AssessmentDisposition.UNEVALUABLE
                        for reason in row.reason_codes
                    )
                )
            )
        )
        values.append(
            RequirementSupplyAssessment(
                "assessment." + NAMESPACE + "." + phase.value.lower(),
                ObjectIdentity.from_record(requirement.requirement_id, requirement),
                ObjectIdentity.from_record(connection.connection_id, connection),
                phase,
                disposition,
                record.product_id,
                (science.identity(record),),
                reasons,
            )
        )
    return tuple(values)


def operation_declarations():
    from .recursive_translation import describe_contributions, inquiry_endpoint_validator, inquiry_outcome_projector, inquiry_evidence_projector
    return (RecursiveOperationDeclaration(
        capability_key=NAMESPACE + '.' + 'diagnose', capability_version='1.0.0',
        implementation_id=NAMESPACE + '.explicit-finite-native-components', kind=CapabilityKind.SIMULATOR,
        config_record_type=DiagnosticOperationConfig, stage=ScientificStage.ACQUIRE,
        input_ports=(RecursivePortContract('prior', BatteryInquirySupply.SCHEMA, MEDIA, MAX_BYTES), RecursivePortContract('source', DiagnosticSource.SCHEMA, MEDIA, MAX_BYTES)),
        outputs=(OutputTemplate('product', DiagnosticResult.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA, '.json'),),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=BUDGET,
        conformance_check_ids=('complete-twelve-forecast-roster', 'prior-outcome-preserved', 'strict-independent-sensitivity'),
        runner_factory=DiagnosticRunner, record_codecs=output_codecs(),
        scientific_hooks=RecursiveScientificHooks(
            assessment_projector=project_assessments, scientific_operand_sha256s=scientific_operand_sha256s,
            scientific_unit_ids=scientific_unit_ids, native_effect_slot_ids=native_effect_slot_ids,
            scientific_root_validator=scientific_root_validator,
        ),
        execution_properties=RecursiveExecutionProperties(
            native_effect=True, complete_unit_census=True,
        ),
        inquiry_hooks=RecursiveInquiryHooks(
            contribution_describer=describe_contributions, inquiry_endpoint_validator=inquiry_endpoint_validator,
            inquiry_outcome_projector=inquiry_outcome_projector, inquiry_evidence_projector=inquiry_evidence_projector,
        ),
    ),)

def operation_manifests():
    return tuple(row.manifest() for row in operation_declarations())


def operation_registrations():
    return tuple(row.registration() for row in operation_declarations())


def output_codecs():
    return {
        x.SCHEMA: x
        for x in (
            DiagnosticOperationConfig,
            DiagnosticSource,
            BatteryInquirySupply,
            DiagnosticResult,
        )
    }


class DiagnosticRunner:
    def __init__(self):
        self.manifest = operation_manifests()[0]

    def execute(self, context):
        try:
            expected = {
                x.SCHEMA: x
                for x in (
                    DiagnosticOperationConfig,
                    DiagnosticSource,
                    BatteryInquirySupply,
                )
            }
            node = NAMESPACE + ".diagnose"
            if (
                context.task_id != node
                or context.permissions != self.manifest.permissions
                or context.resource_budget != BUDGET
                or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or len(context.input_ports) != 3
                or {x.payload_schema for x in context.input_ports} != set(expected)
            ):
                raise ValueError("diagnostic changes exact runtime inputs/access")
            records = {}
            for port in context.input_ports:
                if (
                    port.kind is not WorkerInputKind.EXTERNAL
                    or port.media_type != MEDIA
                    or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                ):
                    raise ValueError("diagnostic changes input boundary")
                raw = port.read()
                if len(raw) != port.size_bytes:
                    raise ValueError("diagnostic input size mismatch")
                records[port.payload_schema] = decode_canonical_bytes(
                    raw, expected[port.payload_schema], maximum_bytes=None
                )
                del raw
                port.close()
            config = records[DiagnosticOperationConfig.SCHEMA]
            source = records[DiagnosticSource.SCHEMA]
            prior = records[BatteryInquirySupply.SCHEMA]
            if (
                config.config_id != context.config.config_id
                or config.fingerprint() != context.config.content_sha256
                or config.source != source
                or config.operands
                != tuple(
                    sorted(
                        (science.identity(source), science.identity(prior)),
                        key=lambda x: x.object_id,
                    )
                )
            ):
                raise ValueError("diagnostic runtime substitutes immutable operands")
            science.validate_prior(source, prior)
            if (
                len(context.output_ports) != 1
                or context.output_ports[0].output_id != node + ".product"
                or context.output_ports[0].payload_schema != DiagnosticResult.SCHEMA
                or context.output_ports[0].profile is not ArtifactProfile.CANONICAL_JSON
                or context.output_ports[0].media_type != MEDIA
            ):
                raise ValueError("diagnostic output contract differs")
            # Full actual science/operand validation precedes releasing history.
            # Input materializations and canonical receipts retain its custody;
            # native configurations need only the exact validated identity.
            prior_identity = science.identity(prior)
            records.clear()
            del prior
            result = science._run_validated_prior(source, prior_identity)
            return RunnerResult(
                (TaskOutputPayload(node + ".product", result.canonical_bytes()),),
                (
                    ReceiptCheck(
                        "diagnostic-complete-roster-and-independent-reduction", True, ()
                    ),
                ),
            )
        finally:
            for port in context.input_ports:
                port.close()
