# SPDX-License-Identifier: MPL-2.0
"""Explicit source gate, complete native trace roster and independent PURE reducer."""

from functools import partial
from empirical_lawhood.runtime.recursive_provider import (RecursiveOperationDeclaration,RecursiveExecutionProperties,RecursiveInquiryHooks,RecursiveScientificHooks)

from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic.contracts import DiagnosticResult
from empirical_lawhood.adapters.methods.battery_diagnostic_obstruction.contracts import ObstructionAssessment
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition, AssessmentPhase, DevelopmentStudySpec, RequirementSupplyAssessment
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, validate_stable_id
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from . import contracts as c, science

NAMESPACE = "battery-refined-inquiry"
QUESTION = "Does the explicitly selected full-roster numerical policy supply adequate conditional forecasts for separate later preparation choices?"
UNIT = c.UNIT
VIEW = "view.battery-refined-inquiry.complete-numerical-family"
MEDIA = "application/json"
MAX_BYTES = None
BUDGET = ResourceBudget(1, None, 0, None, None, None)
OPERATIONS = tuple(sorted(("acquire-45", "acquire-54", "qualify-45", "qualify-54", "validate-policy",
    "acquire-obstruction-45", "acquire-obstruction-54", "qualify-obstruction-45", "qualify-obstruction-54", "validate-obstruction-policy")))

def is_gate(operation):
    return operation in ("validate-policy", "validate-obstruction-policy")

def history_type(history):
    return ObstructionAssessment if history.object_schema == ObstructionAssessment.SCHEMA else DiagnosticResult

def gate_operation(history):
    return "validate-obstruction-policy" if history.object_schema == ObstructionAssessment.SCHEMA else "validate-policy"

def acquire_operation(history,count):
    return ("acquire-obstruction-" if history.object_schema == ObstructionAssessment.SCHEMA else "acquire-")+str(count)

def qualify_operation(history,count):
    return ("qualify-obstruction-" if history.object_schema == ObstructionAssessment.SCHEMA else "qualify-")+str(count)

COMMON_INPUTS = (("diagnostic", DiagnosticResult), ("policy", c.NumericalPolicy),
                 ("selection", c.NumericalSelection), ("source", c.RefinedSource))


def common_inputs(operation):
    return tuple((name,ObstructionAssessment if name == "diagnostic" and "obstruction" in operation else record) for name,record in COMMON_INPUTS)


def record_identity(record):
    if type(record) is c.NumericalSelection:
        return ObjectIdentity.from_record("selection." + record.policy_id, record)
    if type(record) is SourcePolicyAdmission:
        return ObjectIdentity.from_record(record.admission_id, record)
    return c.identity(record)


@dataclass(frozen=True, slots=True)
class SourcePolicyAdmission(CanonicalRecord):
    """Only source/protocol/history consistency; no numerical adequacy or authority."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-refined-inquiry/source-policy-admission"
    admission_id: str
    source: ObjectIdentity
    policy: ObjectIdentity
    selection: ObjectIdentity
    diagnostic: ObjectIdentity
    numerical_adequacy: str = "NOT_ASSESSED"
    scientific_authority: str = "NONE"

    def __post_init__(self):
        if self.admission_id != "admission." + NAMESPACE + ".source-policy":
            raise ValueError("source-policy gate changes its record identity")
        schemas = (c.RefinedSource.SCHEMA, c.NumericalPolicy.SCHEMA, c.NumericalSelection.SCHEMA, self.diagnostic.object_schema)
        if self.diagnostic.object_schema not in c.HISTORY_SCHEMAS or tuple(x.object_schema for x in (self.source, self.policy, self.selection, self.diagnostic)) != schemas:
            raise ValueError("source-policy gate substitutes its typed operands")
        if self.numerical_adequacy != "NOT_ASSESSED" or self.scientific_authority != "NONE":
            raise ValueError("source consistency cannot grant numerical adequacy or scientific authority")


@dataclass(frozen=True, slots=True)
class RefinedOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-refined-inquiry/operation-config"
    config_id: str
    operation: str
    source: c.RefinedSource
    policy: c.NumericalPolicy
    selection: c.NumericalSelection
    diagnostic: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if self.operation not in OPERATIONS or self.config_id != "config." + NAMESPACE + "." + self.operation:
            raise ValueError("refined operation identity differs")
        if type(self.source) is not c.RefinedSource or type(self.policy) is not c.NumericalPolicy or type(self.selection) is not c.NumericalSelection:
            raise ValueError("refined operation substitutes selected source/policy/protocol types")
        self.source.__post_init__()
        self.policy.__post_init__()
        self.selection.__post_init__()
        if (self.source.policy != c.identity(self.policy) or self.selection != self.policy.selection
                or self.source.diagnostic != self.diagnostic or self.policy.diagnostic != self.diagnostic
                or self.source.protocol_sha256 != self.policy.protocol_sha256):
            raise ValueError("refined operation changes exact source/policy/selection/history join")
        if ("obstruction" in self.operation) != (self.diagnostic.object_schema == ObstructionAssessment.SCHEMA):
            raise ValueError("refined operation cannot substitute an absent result or disguise adverse history")
        if not is_gate(self.operation) and self.operation.endswith("54") != self.policy.tolerance_probe:
            raise ValueError("refined operation changes its complete45/54 scientific roster")

    @property
    def operands(self):
        return tuple(sorted((record_identity(self.source), record_identity(self.policy),
                             record_identity(self.selection), self.diagnostic), key=lambda x: x.object_id))


def source_policy_admission(source, policy, selection, diagnostic):
    if type(selection) is not c.NumericalSelection or selection != policy.selection:
        raise ValueError("source-policy gate changes the actual selected protocol")
    science.validate_source_policy(source, policy, diagnostic=diagnostic, protocol_bytes=selection.canonical_bytes())
    return SourcePolicyAdmission("admission." + NAMESPACE + ".source-policy", record_identity(source),
        record_identity(policy), record_identity(selection), record_identity(diagnostic))


def scope(config):
    return c.scope(config.source)


def scientific_operand_sha256s(config):
    return tuple(sorted({x.object_fingerprint for x in config.operands}))


def scientific_unit_ids(config):
    return (UNIT,)


def native_effect_slot_ids(config):
    """Scientific effects exclude editable labels and historical view names."""
    if not config.operation.startswith("acquire-"):
        return ()
    values = []
    for native in science.configurations(config.source, config.policy):
        view = native.numerical_view
        operand = {"original_physics": config.source.original, "native_source_members": config.source.source_members,
            "phase": native.phase, "initial_temperature_k": native.initial_temperature_k,
            "recipe": native.recipe, "chamber_temperature_k": native.chamber_temperature_k,
            "model_view": native.model_view, "electrode_points": view.electrode_points,
            "particle_points": view.particle_points, "localization_epsilon_k": view.localization_epsilon_k,
            "rtol": view.rtol, "atol": view.atol}
        values.append("native." + NAMESPACE + "." + sha256(canonical_json_bytes(operand)).hexdigest())
    return tuple(sorted(values))


def development_root(config, *, study_id):
    selected_scope = scope(config)
    claim = ClaimSpec("claim." + NAMESPACE, selected_scope.world_id,
        "population.battery-thermal-inquiry.exposed-lgm50", QUESTION,
        "Complete nine preparations, two reduced models and independent DFN band/mesh/combined comparisons; all views nested in one exposed numerical family.",
        UNIT, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        "Conditional finite-path numerical adequacy grants zero physical units, no whole-time certificate, physical qualification or controller authority.",
        ("assumption.exposed-lgm50-model-family",), numerical_view_ids=(VIEW,))
    return DevelopmentStudySpec(study_id, QUESTION,
        ObjectIdentity.from_record(selected_scope.system_id, config.source.original), selected_scope.world_id,
        WorldKind.NUMERICAL_SIMULATOR, (UNIT,), (VIEW,), (claim,), config.operands)


def trace_ports(count):
    if count not in (45, 54):
        raise ValueError("refined trace roster is45 or54")
    return tuple("trace-" + f"{n:03d}" for n in range(count))


def operation_inputs(operation):
    result = list(common_inputs(operation))
    if not is_gate(operation):
        result.append(("admission", SourcePolicyAdmission))
    if operation.startswith("qualify-"):
        result.extend((name, c.Trace) for name in trace_ports(int(operation.rsplit("-", 1)[1])))
    return tuple(sorted(result))


def operation_outputs(operation):
    if is_gate(operation):
        return (("admission", SourcePolicyAdmission),)
    if operation.startswith("acquire-"):
        return tuple((name, c.Trace) for name in trace_ports(int(operation.rsplit("-", 1)[1])))
    return (("qualification", c.Qualification), ("supply", c.Supply))


def operation_stage(operation):
    return ScientificStage.ADMISSION if is_gate(operation) else (
        ScientificStage.ACQUIRE if operation.startswith("acquire-") else ScientificStage.QUALIFY)


def scientific_root_validator(config, context):
    native = config.operation.startswith("acquire-")
    if (context.root != development_root(config, study_id=context.root.study_id)
            or context.node_id != NAMESPACE + "." + config.operation or context.stage is not operation_stage(config.operation)
            or context.unit_ids != (UNIT,) or context.selected_unit_ids != (UNIT,) or context.complete_unit_census != native
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise ValueError("refined operation changes exact scientific root/config/stage/units/access")
    incoming = tuple(x for x in context.links if x.consumer_node_id == context.node_id)
    expected = dict(operation_inputs(config.operation))
    if len(incoming) != len(expected) or {x.consumer_input_id for x in incoming} != set(expected):
        raise ValueError("refined operation omits or duplicates exact scientific input ports")
    for link in incoming:
        name = link.consumer_input_id
        if name in dict(common_inputs(config.operation)):
            if link.external_input_id is None or link.scientific_role != ("HISTORY" if name == "diagnostic" else "SOURCE"):
                raise ValueError("refined operation changes source/history scientific roles")
        else:
            producer = NAMESPACE + ("." + gate_operation(config.diagnostic) if name == "admission" else "." + acquire_operation(config.diagnostic,config.operation.rsplit("-", 1)[1]))
            if (link.external_input_id is not None or link.producer_node_id != producer or link.producer_output_id != name
                    or link.scientific_role != ("MODEL" if name == "admission" else "OUTCOME")):
                raise ValueError("refined operation requires exact internal gate/trace dependencies")
    configs = {x.node_id: x.record for x in context.config_inputs}
    if (configs.get(context.node_id) != config or any(type(row) is not RefinedOperationConfig
            or node != NAMESPACE + "." + row.operation or row.operands != config.operands for node, row in configs.items())):
        raise ValueError("refined graph substitutes selected source/policy/configuration")
    gate = configs.get(NAMESPACE + "." + gate_operation(config.diagnostic))
    if gate is None or (config.operation.startswith("qualify-")
            and NAMESPACE + "." + acquire_operation(config.diagnostic,config.operation.rsplit("-", 1)[1]) not in configs):
        raise ValueError("refined operation omits its selected internal source gate/acquisition")
    if len(context.requirements) != 1 or len(context.connections) != 1:
        raise ValueError("refined graph requires its exact shared evidential history connection")
    from .recursive_translation import validate_requirement_config
    validate_requirement_config(gate, context.requirements[0], context.connections[0])


def project_source_policy_assessments(record, requirement, connection):
    from .recursive_translation import validate_requirement_admission
    validate_requirement_admission(record, requirement, connection)
    return tuple(RequirementSupplyAssessment("assessment." + NAMESPACE + ".source-policy." + phase.value.lower(),
        ObjectIdentity.from_record(requirement.requirement_id, requirement), ObjectIdentity.from_record(connection.connection_id, connection),
        phase, AssessmentDisposition.SATISFIED, record.admission_id, (record_identity(record),), ()) for phase in AssessmentPhase)


def describe_contributions(draft, products):
    from .recursive_translation import describe_contributions as callback
    return callback(draft, products)

def next_wave_builder(draft, manifest, products):
    from .recursive_translation import next_wave_builder as callback
    return callback(draft, manifest, products)

def inquiry_endpoint_validator(draft, endpoint):
    from .recursive_translation import inquiry_endpoint_validator as callback
    return callback(draft, endpoint)

def inquiry_outcome_projector(draft, specification, products):
    from .recursive_translation import inquiry_outcome_projector as callback
    return callback(draft, specification, products)

def inquiry_evidence_projector(draft, payloads, products=None):
    from .recursive_translation import inquiry_evidence_projector as callback
    return callback(draft, payloads, products)


def operation_declarations():
    return tuple((RecursiveOperationDeclaration(
        capability_key=NAMESPACE + '.' + operation, capability_version='1.0.0',
        implementation_id=NAMESPACE + '.source-gated-complete-roster-v1.' + operation,
        kind=CapabilityKind.SIMULATOR if operation.startswith('acquire-') else CapabilityKind.ANALYSIS,
        config_record_type=RefinedOperationConfig, stage=operation_stage(operation),
        input_ports=tuple((RecursivePortContract(name, record.SCHEMA, MEDIA, MAX_BYTES) for name, record in operation_inputs(operation))),
        outputs=tuple((OutputTemplate(name, record.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA, '.json') for name, record in operation_outputs(operation))),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=BUDGET,
        conformance_check_ids=('authentic-history-protocol-before-native', 'complete-separate-trace-custody', 'independent-full-roster-reduction'),
        runner_factory=partial(RefinedRunner, operation), record_codecs=output_codecs(),
        scientific_hooks=RecursiveScientificHooks(
            assessment_projector=project_source_policy_assessments if is_gate(operation) else None,
            scientific_operand_sha256s=scientific_operand_sha256s, scientific_unit_ids=scientific_unit_ids,
            native_effect_slot_ids=native_effect_slot_ids if operation.startswith('acquire-') else None,
            scientific_root_validator=scientific_root_validator,
        ),
        execution_properties=RecursiveExecutionProperties(
            native_effect=operation.startswith('acquire-'), complete_unit_census=operation.startswith('acquire-'),
        ),
        inquiry_hooks=RecursiveInquiryHooks(
            contribution_describer=describe_contributions, next_wave_builder=next_wave_builder,
            inquiry_endpoint_validator=inquiry_endpoint_validator, inquiry_outcome_projector=inquiry_outcome_projector,
            inquiry_evidence_projector=inquiry_evidence_projector,
        ),
    ) for operation in OPERATIONS))

def operation_manifests():
    return tuple(row.manifest() for row in operation_declarations())


def operation_registrations():
    return tuple(row.registration() for row in operation_declarations())


def output_codecs():
    codecs = {record.SCHEMA: record for record in (RefinedOperationConfig, SourcePolicyAdmission, DiagnosticResult, ObstructionAssessment,
        c.RefinedSource, c.NumericalPolicy, c.NumericalSelection, c.Trace, c.Qualification, c.Supply)}
    from . import recipient_bindings
    for schema, record in recipient_bindings.output_codecs().items():
        if schema in codecs and codecs[schema] is not record:
            raise ValueError("refined operation codecs disagree on canonical schema owner")
        codecs[schema] = record
    return codecs


class RefinedRunner:
    def __init__(self, operation):
        if operation not in OPERATIONS:
            raise ValueError("unknown refined operation")
        self.operation = operation
        self.manifest = next(m for m in operation_manifests() if m.capability_key == NAMESPACE + "." + operation)

    def execute(self, context):
        try:
            node = NAMESPACE + "." + self.operation
            expected = operation_inputs(self.operation)
            schemas = {record.SCHEMA: record for _, record in expected} | {RefinedOperationConfig.SCHEMA: RefinedOperationConfig}
            if (context.task_id != node or context.permissions != self.manifest.permissions or context.resource_budget != BUDGET
                    or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE or len(context.input_ports) != len(expected) + 1):
                raise ValueError("refined worker changes exact task/input/access/resource contract")
            decoded = {}
            for port in context.input_ports:
                if (port.payload_schema not in schemas or port.media_type != MEDIA
                        or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                        or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
                    raise ValueError("refined worker receives undeclared or protected inputs")
                raw = port.read()
                if len(raw) != port.size_bytes:
                    raise ValueError("refined worker input materialization size differs")
                record = decode_canonical_bytes(raw, schemas[port.payload_schema], maximum_bytes=None)
                decoded.setdefault(port.payload_schema, []).append((port, record))
            if set(decoded) != set(schemas) or any(len(rows) != (len(trace_ports(int(self.operation.rsplit('-', 1)[1])))
                    if schema == c.Trace.SCHEMA else 1) for schema, rows in decoded.items()):
                raise ValueError("refined worker duplicates or omits exact typed input census")
            config_port, config = decoded[RefinedOperationConfig.SCHEMA][0]
            if (config_port.kind is not WorkerInputKind.EXTERNAL or config_port.artifact_id != context.config.artifact_id
                    or config.config_id != context.config.config_id or config.fingerprint() != context.config.content_sha256
                    or config.operation != self.operation):
                raise ValueError("refined worker substitutes immutable selected config")
            common = {name: decoded[record.SCHEMA][0] for name, record in common_inputs(self.operation)}
            if any(port.kind is not WorkerInputKind.EXTERNAL for port, _ in common.values()):
                raise ValueError("refined worker substitutes source/history input origin")
            if (common["source"][1] != config.source or common["policy"][1] != config.policy
                    or common["selection"][1] != config.selection or record_identity(common["diagnostic"][1]) != config.diagnostic):
                raise ValueError("refined worker substitutes actual source/policy/selection/history")
            admission = source_policy_admission(*(common[name][1] for name in ("source", "policy", "selection", "diagnostic")))
            outputs = operation_outputs(self.operation)
            if (tuple((p.output_id, p.payload_schema) for p in context.output_ports) != tuple((node + "." + name, record.SCHEMA) for name, record in outputs)
                    or any(p.profile is not ArtifactProfile.CANONICAL_JSON or p.media_type != MEDIA for p in context.output_ports)):
                raise ValueError("refined worker changes complete canonical output contract")
            if is_gate(self.operation):
                if context.dependency_receipts:
                    raise ValueError("source consistency gate has undeclared dependencies")
                records = (admission,)
            else:
                port, retained = decoded[SourcePolicyAdmission.SCHEMA][0]
                producer = NAMESPACE + "." + gate_operation(config.diagnostic)
                if (port.kind is not WorkerInputKind.DEPENDENCY or retained != admission
                        or port.artifact_id != f"artifact.{context.run_id}.{producer}.admission"
                        or not any(r.task_id == producer and port.materialization_id in r.output_materialization_ids for r in context.dependency_receipts)):
                    raise ValueError("native/reducer requires its actual exact receipt-backed internal source gate")
                configs = science.configurations(config.source, config.policy)
                if self.operation.startswith("acquire-"):
                    if len(context.dependency_receipts) != 1:
                        raise ValueError("native acquisition has undeclared dependencies")
                    from .native import acquire
                    records = tuple(acquire(native) for native in configs)
                    if any(type(record) is not c.Trace or record.config != native for record, native in zip(records, configs, strict=True)):
                        raise ValueError("native provider substitutes exact configured trace census")
                else:
                    producer = NAMESPACE + "." + acquire_operation(config.diagnostic,self.operation.rsplit("-", 1)[1])
                    ports = {p.artifact_id: (p, record) for p, record in decoded[c.Trace.SCHEMA]}
                    traces = []
                    for name, native in zip(trace_ports(len(configs)), configs, strict=True):
                        key = f"artifact.{context.run_id}.{producer}.{name}"
                        if key not in ports:
                            raise ValueError("reducer trace port mapping omits actual acquisition output")
                        p, trace = ports[key]
                        if (p.kind is not WorkerInputKind.DEPENDENCY or trace.config != native
                                or not any(r.task_id == producer and p.materialization_id in r.output_materialization_ids for r in context.dependency_receipts)):
                            raise ValueError("reducer substitutes trace config/ordinal/producing receipt")
                        traces.append(trace)
                    if len(context.dependency_receipts) != 2:
                        raise ValueError("reducer has undeclared dependency receipts")
                    qualification = science.qualify(config.source, config.policy, tuple(traces))
                    records = (qualification, science.construct_supply(config.source, config.policy, qualification, tuple(traces)))
            return RunnerResult(tuple(TaskOutputPayload(p.output_id, record.canonical_bytes()) for p, record in zip(context.output_ports, records, strict=True)),
                                (ReceiptCheck("source-gated-complete-refined-operation", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()
