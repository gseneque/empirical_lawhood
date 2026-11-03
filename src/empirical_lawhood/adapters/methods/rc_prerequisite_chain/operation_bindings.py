# SPDX-License-Identifier: MPL-2.0
"""Cold, explicit RC phase registration and stateless runner construction."""

from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition, AssessmentPhase, RequirementSupplyAssessment
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_provider import (
    RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks,
)

from . import operation_contracts as records
from .contracts import RCChainSummary, RCChainUnitResult
from . import operations

NAMESPACE = "rc-prerequisite-chain.phases"
MEDIA_TYPE = "application/json"
MAX_BYTES = 16 * 1024**2
BUDGET = ResourceBudget(1, 1024**3, 0, 600, MAX_BYTES, MAX_BYTES)

# Each row declares configuration, input ports, product ports and executable owner.
# No factory retains a scientific fixture or looks up graph state.
PHASES = (
    ("source", records.RCSourceOperationConfig, (),
     (("evidence", records.RCSourceEvidence), ("observer", records.RCObserverExport)),
     operations.acquire_source, CapabilityKind.SIMULATOR, ScientificStage.ACQUIRE, True),
    ("observations", records.RCObservationOperationConfig, (("observer", records.RCObserverExport),),
     (("reports", records.RCObservationSet),), operations.construct_observations,
     CapabilityKind.OBSERVATION_OPERATOR, ScientificStage.TRANSFORM, False),
    ("admit", records.RCAdmissionOperationConfig, (("reports", records.RCObservationSet),),
     (("admissions", records.RCAdmissionSet),), operations.admit_observations,
     CapabilityKind.ADMISSION_EVALUATOR, ScientificStage.ADMISSION, False),
    ("commit", records.RCCommitmentOperationConfig,
     (("admissions", records.RCAdmissionSet), ("reports", records.RCObservationSet)),
     (("commitments", records.RCCommitmentSet),), operations.commit_preparations,
     CapabilityKind.TRANSFORM, ScientificStage.FREEZE, False),
    ("deliver", records.RCDeliveryOperationConfig, (("commitments", records.RCCommitmentSet),),
     (("native", records.RCNativeDeliverySet),), operations.deliver_phases,
     CapabilityKind.NATIVE_DELIVERY, ScientificStage.PREPARE, True),
    ("measure", records.RCMeasurementOperationConfig,
     (("commitments", records.RCCommitmentSet), ("reports", records.RCObservationSet), ("source", records.RCSourceEvidence)),
     (("measurements", records.RCMeasurementAssessmentSet),), operations.assess_measurement,
     CapabilityKind.FALSIFIER, ScientificStage.FALSIFY, False),
    ("support", records.RCSupportOperationConfig,
     (("commitments", records.RCCommitmentSet), ("measurements", records.RCMeasurementAssessmentSet), ("native", records.RCNativeDeliverySet)),
     (("support", records.RCSupportAssessmentSet),), operations.assess_support,
     CapabilityKind.FALSIFIER, ScientificStage.FALSIFY, False),
    ("joined", records.RCJoinedOperationConfig,
     (("commitments", records.RCCommitmentSet), ("measurements", records.RCMeasurementAssessmentSet),
      ("native", records.RCNativeDeliverySet), ("support", records.RCSupportAssessmentSet)),
     (("joined", records.RCJoinedAssessmentSet),), operations.assess_joined,
     CapabilityKind.FALSIFIER, ScientificStage.FALSIFY, False),
    ("reduce", records.RCUnitReductionConfig,
     (("commitments", records.RCCommitmentSet), ("joined", records.RCJoinedAssessmentSet),
      ("measurements", records.RCMeasurementAssessmentSet), ("reports", records.RCObservationSet),
      ("source", records.RCSourceEvidence), ("support", records.RCSupportAssessmentSet)),
     (("unit", RCChainUnitResult),), operations.reduce_unit,
     CapabilityKind.REPORTER, ScientificStage.REPORT, False),
    ("summary", records.RCSummaryOperationConfig, (("units", RCChainUnitResult),),
     (("summary", RCChainSummary),), operations.summarize_units,
     CapabilityKind.REPORTER, ScientificStage.REPORT, False),
)

# Function argument order is independent of the canonical sorted port inventory.
ARGUMENT_SCHEMAS = {
    "source": (), "observations": (records.RCObserverExport,), "admit": (records.RCObservationSet,),
    "commit": (records.RCObservationSet, records.RCAdmissionSet),
    "deliver": (records.RCCommitmentSet,),
    "measure": (records.RCSourceEvidence, records.RCObservationSet, records.RCCommitmentSet),
    "support": (records.RCMeasurementAssessmentSet, records.RCCommitmentSet, records.RCNativeDeliverySet),
    "joined": (records.RCMeasurementAssessmentSet, records.RCCommitmentSet, records.RCNativeDeliverySet, records.RCSupportAssessmentSet),
    "reduce": (records.RCSourceEvidence, records.RCObservationSet, records.RCCommitmentSet,
               records.RCMeasurementAssessmentSet, records.RCSupportAssessmentSet, records.RCJoinedAssessmentSet),
    "summary": (RCChainUnitResult,),
}


def scientific_operand_sha256s(config):
    """Declare opaque parent binding without exposing fixture truth to policy."""
    if isinstance(config, records.RCPolicyOperationConfig):
        return (config.scientific_config_sha256,)
    return (config.scientific_config.fingerprint(),)


def scientific_unit_ids(config):
    """Bind unit-scoped phases without exposing the scientific roster to policy."""
    if isinstance(config, records.RCSummaryOperationConfig):
        return tuple(unit.unit_id for unit in config.scientific_config.units)
    return (config.unit_id,)


def native_effect_slot_ids(config):
    """Keep source and delivery distinct; editable config IDs create no new slot."""
    if isinstance(config, records.RCDeliveryOperationConfig):
        phase = "delivery"
    elif type(config) is records.RCSourceOperationConfig:
        phase = "source"
    else:
        raise ValueError("RC native slot requires a registered source or delivery configuration")
    return (f"native.rc-chain.{phase}.{config.scientific_config.fingerprint()}.{config.unit_id}",)


def scientific_root_validator(config, context):
    """Bind policy, source and scoped claims using frozen compiler metadata."""
    from .scientific_binding import validate_rc_scientific_binding
    validate_rc_scientific_binding(config, context)


def assessment_projector(product, requirement, connection):
    """Retain every nested result under its actual scientific requirement."""
    ports = {records.RCMeasurementAssessmentSet: "measurements",
             records.RCSupportAssessmentSet: "support", records.RCJoinedAssessmentSet: "joined"}
    port = ports.get(type(product))
    if port is None:
        raise ValueError("RC assessment projection requires an actual M/P/J phase product")
    if (connection.requirement_id != requirement.requirement_id or
        connection.assessment_operation_id != requirement.assessment_operation_id or
        requirement.scope is None or requirement.scope.instance_id != product.unit_id or
        requirement.scope.source_config_sha256 != product.config_sha256):
        raise ValueError("RC assessment changes its requirement, instance or scientific source scope")
    dispositions = {"PASSED": AssessmentDisposition.SATISFIED, "FAILED": AssessmentDisposition.FALSIFIED,
                    "REFUSED": AssessmentDisposition.REFUSED, "UNEVALUABLE": AssessmentDisposition.UNEVALUABLE,
                    "UNSUPPORTED": AssessmentDisposition.UNSUPPORTED}
    evidence = ObjectIdentity.from_record(f"{requirement.assessment_operation_id}.{port}", product)
    results = []
    for row in product.assessments:
        joined = isinstance(product, records.RCJoinedAssessmentSet)
        state, reasons = ((row.result.joined_state, row.result.reason_codes) if joined else (row.state, row.reason_codes))
        arm = getattr(row, "arm_id", "observation")
        results.append(RequirementSupplyAssessment(
            f"assessment.{requirement.requirement_id}.{row.variant_id}.{arm}",
            ObjectIdentity.from_record(requirement.requirement_id, requirement),
            ObjectIdentity.from_record(connection.connection_id, connection),
            AssessmentPhase.JOINED if joined else AssessmentPhase.INSTANCE, dispositions[state], product.unit_id,
            (evidence,), () if state == "PASSED" else reasons))
    return tuple(sorted(results, key=lambda value: value.assessment_id))


def operation_manifests():
    return tuple(row.manifest() for row in operation_declarations())


def operation_registrations():
    return tuple(row.registration() for row in operation_declarations())


def build_runners():
    return tuple(row.runner_factory() for row in operation_declarations())


def prepare_native_work(*, runner, context, expected_parent):
    """Declare the original ordinary RC effect scope without native calculation."""
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork

    if (type(runner) is not operations.RCPhaseRunner
            or runner.operation not in (operations.acquire_source, operations.deliver_phases)):
        raise ValueError("RC native preparation requires its installed source or delivery owner")
    allowed = {record.SCHEMA: record for record in (runner.config_type, *runner.input_types)}
    decoded = {}
    for port in context.input_ports:
        record_type = allowed.get(port.payload_schema)
        if record_type is None:
            raise ValueError("RC native preparation receives an undeclared input or oracle")
        value = decode_canonical_bytes(port.read(), record_type, maximum_bytes=operations.MAX_OPERATION_BYTES)
        decoded.setdefault(port.payload_schema, []).append(value)
    configs = decoded.pop(runner.config_type.SCHEMA, ())
    if (len(configs) != 1 or configs[0].config_id != context.config.config_id
            or configs[0].fingerprint() != context.config.content_sha256):
        raise ValueError("RC native preparation lacks its exact original configuration")
    config = configs[0]
    for record_type in runner.input_types:
        rows = decoded.get(record_type.SCHEMA, ())
        if len(rows) != 1:
            raise ValueError("RC native preparation lacks its complete direct input census")
        operations._same_unit(config, rows[0])
    return PreparedNativeWork(expected_parent, scientific_unit_ids(config), native_effect_slot_ids(config))


def output_codecs():
    return {record.SCHEMA: record for row in PHASES for _, record in row[3]}


def _operation_declaration(role, config, inputs, outputs, owner, kind, stage, native):
    selected = RecursiveOperationDeclaration(
        capability_key=f"{NAMESPACE}.{role}", capability_version="1.0.0",
        implementation_id="registered-phase-v1", kind=kind,
        config_record_type=config, stage=stage,
        input_ports=tuple(RecursivePortContract(name, record.SCHEMA, MEDIA_TYPE, MAX_BYTES,
            1, 32 if role == "summary" else 1) for name, record in inputs),
        outputs=tuple(OutputTemplate(name, record.SCHEMA, ArtifactProfile.CANONICAL_JSON,
            MEDIA_TYPE, ".json") for name, record in outputs),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=BUDGET,
        conformance_check_ids=("complete-phase-ports", "truth-isolated-policy"),
        runner_factory=lambda: operations.RCPhaseRunner(manifest=selected.manifest(),
            config_type=config, input_types=ARGUMENT_SCHEMAS[role], operation=owner,
            output_types=tuple(record for _, record in outputs)),
        record_codecs=output_codecs(),
        scientific_hooks=RecursiveScientificHooks(
            assessment_projector=assessment_projector if role in {"measure", "support", "joined"} else None,
            scientific_operand_sha256s=scientific_operand_sha256s,
            scientific_unit_ids=scientific_unit_ids,
            native_effect_slot_ids=native_effect_slot_ids if native else None,
            scientific_root_validator=scientific_root_validator),
        execution_properties=RecursiveExecutionProperties(
            barrier=BarrierKind.FREEZE if role == "commit" else BarrierKind.NONE,
            native_effect=native, native_work_preparer=prepare_native_work if native else None,
            complete_unit_census=native))
    return selected


def operation_declarations():
    return tuple(_operation_declaration(*phase) for phase in PHASES)
