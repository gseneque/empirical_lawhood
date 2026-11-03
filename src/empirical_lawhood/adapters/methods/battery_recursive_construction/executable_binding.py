"""Static allowlisted battery operations and bounded path-free task runners."""

from empirical_lawhood.runtime.recursive_provider import (RecursiveOperationDeclaration,RecursiveExecutionProperties,RecursiveInquiryHooks,RecursiveScientificHooks)

from dataclasses import dataclass, replace
from functools import partial
from hashlib import sha256

from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.scientific_contributions import ContributionManifest
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract

from .contracts import (
    BatteryAdmission, BatteryCheckpoint, BatteryCheckpointSummary, BatteryFurtherProduct,
    BatteryOperation, BatteryOperationConfig, BatteryProcedureContribution,
    BatteryRestartAssessment, BatteryTrace, MAX_PRODUCT_BYTES,
)

RESOURCE = ResourceBudget(1, 2 * 1024**3, 0, 3600, 64 * 1024**2, MAX_PRODUCT_BYTES)
PERMISSIONS = tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT,
                            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS), key=lambda value: value.value))
MEDIA = "application/json"


@dataclass(frozen=True, slots=True)
class OperationDefinition:
    name: str
    operation: BatteryOperation
    wave: str | None
    inputs: tuple[tuple[str, type], ...]
    output_type: type
    stage: ScientificStage
    native: bool = False


def _definition(name, operation, wave, inputs, output, stage, native=False):
    return OperationDefinition(name, operation, wave, tuple(sorted(inputs)), output, stage, native)


DEFINITIONS = (
    _definition("checkpoint", BatteryOperation.CHECKPOINT, None, (), BatteryCheckpoint, ScientificStage.ACQUIRE, True),
    _definition("projection", BatteryOperation.PROJECT, None, (("checkpoint", BatteryCheckpoint),), BatteryCheckpointSummary, ScientificStage.TRANSFORM),
    *tuple(_definition(f"a-{name}", operation, "A", (("checkpoint", BatteryCheckpoint),), BatteryTrace, ScientificStage.ACQUIRE, True)
           for name, operation in (("reference", BatteryOperation.REFERENCE), ("full", BatteryOperation.FULL), ("soc", BatteryOperation.SOC))),
    *tuple(_definition(f"b-{name}", operation, "B", (("admission", BatteryAdmission), ("checkpoint", BatteryCheckpoint)), BatteryTrace, ScientificStage.ACQUIRE, True)
           for name, operation in (("reference", BatteryOperation.REFERENCE), ("full", BatteryOperation.FULL), ("tighter", BatteryOperation.TIGHTER))),
    _definition("a-assess", BatteryOperation.ASSESS, "A", (("checkpoint", BatteryCheckpoint), ("full", BatteryTrace), ("reference", BatteryTrace), ("soc", BatteryTrace)), BatteryRestartAssessment, ScientificStage.FALSIFY),
    _definition("b-assess", BatteryOperation.ASSESS, "B", (("checkpoint", BatteryCheckpoint), ("full", BatteryTrace), ("reference", BatteryTrace)), BatteryRestartAssessment, ScientificStage.FALSIFY),
    _definition("procedure", BatteryOperation.PROCEDURE, "A", (("assessment-early", BatteryRestartAssessment), ("assessment-late", BatteryRestartAssessment), ("checkpoint-early", BatteryCheckpoint), ("checkpoint-late", BatteryCheckpoint)), BatteryProcedureContribution, ScientificStage.SYNTHESIZE),
    _definition("procedure-import", BatteryOperation.IMPORT, "B", (("manifest", ContributionManifest), ("procedure", BatteryProcedureContribution)), BatteryProcedureContribution, ScientificStage.TRANSFORM),
    *tuple(_definition(f"admit-{consumer.lower()}", operation, "B", (("manifest", ContributionManifest), ("procedure", BatteryProcedureContribution), ("summary", BatteryCheckpointSummary)), BatteryAdmission, ScientificStage.ADMISSION)
           for consumer, operation in (("C1", BatteryOperation.ADMIT_C1), ("C2", BatteryOperation.ADMIT_C2))),
    _definition("voltage", BatteryOperation.VOLTAGE, "B",
                (("c1", BatteryAdmission), ("c2", BatteryAdmission),
                 *((f"assessment-{word}", BatteryRestartAssessment) for word in ("early1", "early3", "hold", "late1")),
                 *((f"{word}-{route}", BatteryTrace) for word in ("early1", "early3", "hold", "late1") for route in ("full", "reference", "tighter"))),
                BatteryFurtherProduct, ScientificStage.SYNTHESIZE),
)


def operation_declaration(definition):
    from .scientific_binding import resolve_battery_scientific_claim
    return RecursiveOperationDeclaration(
        capability_key='battery-recursive.' + definition.name, capability_version='1.0.0',
        implementation_id='battery-recursive-v1', runtime_id='cpython-3.11-battery-recursive',
        implementation_sha256=sha256(f'battery-recursive-v1:{definition.name}:frozen-spme-state-and-voltage-operations'.encode()).hexdigest(),
        kind=CapabilityKind.SIMULATOR if definition.native else CapabilityKind.ANALYSIS,
        config_record_type=BatteryOperationConfig, stage=definition.stage,
        input_ports=tuple((RecursivePortContract(name, record.SCHEMA, MEDIA, MAX_PRODUCT_BYTES) for name, record in definition.inputs)),
        outputs=(OutputTemplate('product', definition.output_type.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA, '.json'),),
        permissions=PERMISSIONS, evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
        resources=RESOURCE,
        conformance_check_ids=('closed-protocol-and-port-census', 'nonpromotable-development', 'separate-instance-assessment'),
        runner_factory=lambda d=definition: BatteryOperationRunner(d), record_codecs=output_codecs(),
        execution_properties=RecursiveExecutionProperties(
            native_effect=definition.native, complete_unit_census=definition.native, requires_clean_commit=False,
            requires_active_mount=False,
        ),
        scientific_hooks=RecursiveScientificHooks(
            assessment_projector=project_battery_assessment if definition.operation in {BatteryOperation.ASSESS, BatteryOperation.ADMIT_C1, BatteryOperation.ADMIT_C2, BatteryOperation.VOLTAGE} else None,
            scientific_operand_sha256s=partial(scientific_operand_sha256s, definition),
            scientific_unit_ids=scientific_unit_ids,
            native_effect_slot_ids=native_effect_slot_ids if definition.native else None,
            scientific_root_validator=partial(scientific_root_validator, definition),
            scientific_claim_resolver=resolve_battery_scientific_claim,
        ),
        inquiry_hooks=RecursiveInquiryHooks(
            contribution_describer=describe_contributions if definition.operation in {BatteryOperation.PROCEDURE, BatteryOperation.VOLTAGE} else None,
            next_wave_builder=next_wave_builder if definition.operation in {BatteryOperation.PROCEDURE, BatteryOperation.VOLTAGE} else None,
        ),
    )


def operation_declarations():
    return tuple((operation_declaration(row) for row in sorted(DEFINITIONS, key=lambda row: row.name)))


def _manifest(definition):
    return operation_declaration(definition).manifest()


def operation_manifests():
    return tuple(sorted((row.manifest() for row in operation_declarations()), key=lambda row: row.registry_id))


def scientific_operand_sha256s(definition, config):
    """Bind the actual source contract to the selected scientific root."""
    from .scientific_binding import validate_battery_scientific_binding
    validate_battery_scientific_binding(definition, config)
    return (config.source.fingerprint(),)


def scientific_unit_ids(config):
    return (config.unit_id,)


def native_effect_slot_ids(config):
    """Identify actual acquisition operands, excluding editable labels."""
    components = (config.operation.value.lower(), config.source.fingerprint(),
                  config.protocol_sha256, config.wave.lower(), config.unit_id, config.history)
    if config.operation is not BatteryOperation.CHECKPOINT:
        components += (config.future_word,)
    return ("native.battery." + ".".join(components),)


def scientific_root_validator(definition, config, context):
    """Authenticate the actual authored claims before any native task is planned."""
    from .scientific_binding import (
        validate_battery_scientific_binding, validate_battery_scientific_requirement,
        validate_battery_scientific_root,
    )
    if not isinstance(context.root, DevelopmentStudySpec):
        raise ValueError("battery operations require their supported development scientific root")
    validate_battery_scientific_binding(definition, config)
    validate_battery_scientific_root(config, context)
    requirements = tuple(requirement for requirement in context.requirements
                         if requirement.assessment_operation_id == context.node_id)
    connections = tuple(connection for connection in context.connections
                        if connection.assessment_operation_id == context.node_id)
    if config.requirement is not None and (config.requirement not in requirements or config.connection not in connections):
        raise ValueError("battery configuration changes its actual authored requirement or connection")
    for requirement in requirements:
        selected = tuple(connection for connection in connections if connection.requirement_id == requirement.requirement_id)
        if len(selected) != 1:
            raise ValueError("battery authored requirement lacks its unique assessed connection")
        validate_battery_scientific_requirement(config, requirement, selected[0])


def operation_registrations():
    return tuple(row.registration() for row in operation_declarations())


def project_battery_assessment(record, requirement, connection):
    """Project actual supply products into the authored connection claims."""
    req = ObjectIdentity.from_record(requirement.requirement_id, requirement)
    edge = ObjectIdentity.from_record(connection.connection_id, connection)
    if isinstance(record, (BatteryRestartAssessment, BatteryAdmission)):
        if record.supply.requirement != req or record.supply.connection != edge:
            raise ValueError("battery assessment changes its committed requirement or connection")
        return (record.supply,)
    if isinstance(record, BatteryFurtherProduct):
        # Each assigned word is a declared prerequisite of the one composite
        # further inquiry. Its joined disposition is the recorded whole-census
        # result, never a newly recomputed trajectory or an outcome retuning.
        from .scientific_binding import validate_battery_further_requirement
        validate_battery_further_requirement(requirement, connection)
        return (replace(record.supply, assessment_id=f"{record.supply.assessment_id}.{requirement.requirement_id}",
                        requirement=req, connection=edge),)
    raise ValueError("battery assessor returned another scientific product type")


def output_codecs():
    return {record.SCHEMA: record for record in (BatteryCheckpoint, BatteryCheckpointSummary, BatteryTrace,
            BatteryRestartAssessment, BatteryProcedureContribution, BatteryAdmission, BatteryFurtherProduct, ContributionManifest)}


@dataclass(frozen=True, slots=True)
class BatteryOperationRunner:
    definition: OperationDefinition

    @property
    def manifest(self):
        return _manifest(self.definition)

    def execute(self, context):
        config_ports = [p for p in context.input_ports if p.payload_schema == BatteryOperationConfig.SCHEMA]
        if len(config_ports) != 1 or context.permissions != PERMISSIONS or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE:
            raise ValueError("battery task configuration or access contract differs")
        if context.resource_budget != RESOURCE or len(context.output_ports) != 1 or context.output_ports[0].output_id != f"{context.task_id}.product" or context.output_ports[0].payload_schema != self.definition.output_type.SCHEMA:
            raise ValueError("battery task output or bounded resource census differs")
        config = decode_canonical_bytes(config_ports[0].read(MAX_PRODUCT_BYTES + 1), BatteryOperationConfig, maximum_bytes=MAX_PRODUCT_BYTES)
        if config.fingerprint() != context.config.content_sha256 or config.operation is not self.definition.operation or (self.definition.wave is not None and config.wave != self.definition.wave):
            raise ValueError("battery exact selected configuration differs")
        others = [p for p in context.input_ports if p.payload_schema != BatteryOperationConfig.SCHEMA]
        expected_schemas = sorted(record.SCHEMA for _, record in self.definition.inputs)
        if sorted(p.payload_schema for p in others) != expected_schemas or any(p.size_bytes > MAX_PRODUCT_BYTES or p.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE for p in others):
            raise ValueError("battery scientific input census or exposed boundary differs")
        records = [decode_canonical_bytes(p.read(MAX_PRODUCT_BYTES + 1), output_codecs()[p.payload_schema], maximum_bytes=MAX_PRODUCT_BYTES) for p in others]
        product = _dispatch(self.definition, config, records)
        payload = product.canonical_bytes()
        if len(payload) > MAX_PRODUCT_BYTES:
            raise ValueError("battery native product exceeds its frozen byte allowance")
        return RunnerResult((TaskOutputPayload(context.output_ports[0].output_id, payload),), (ReceiptCheck("battery-typed-terminal-product", True, ()),))


def _dispatch(definition, config, records):
    from . import science

    def one(record_type, predicate=lambda value: True):
        values = [record for record in records if isinstance(record, record_type) and predicate(record)]
        if len(values) != 1:
            raise ValueError("battery fixed scientific role is missing or ambiguous")
        return values[0]

    operation = definition.operation
    if operation is BatteryOperation.CHECKPOINT:
        return science.capture_checkpoint(config)
    if operation is BatteryOperation.PROJECT:
        return science.project_checkpoint(one(BatteryCheckpoint))
    if operation in {BatteryOperation.REFERENCE, BatteryOperation.FULL, BatteryOperation.SOC, BatteryOperation.TIGHTER}:
        admission = one(BatteryAdmission) if config.wave == "B" else None
        return science.continue_checkpoint(config, one(BatteryCheckpoint), admission)
    if operation is BatteryOperation.ASSESS:
        soc = one(BatteryTrace, lambda t: t.route == "SOC") if config.wave == "A" else None
        return science.assess_restart(config, one(BatteryCheckpoint), one(BatteryTrace, lambda t: t.route == "REFERENCE"),
                                      one(BatteryTrace, lambda t: t.route == "FULL"), soc)
    if operation is BatteryOperation.PROCEDURE:
        return science.construct_procedure(config, tuple(r for r in records if isinstance(r, BatteryCheckpoint)),
                                           tuple(r for r in records if isinstance(r, BatteryRestartAssessment)))
    if operation is BatteryOperation.IMPORT:
        return science.import_procedure(config, one(ContributionManifest), one(BatteryProcedureContribution))
    if operation in {BatteryOperation.ADMIT_C1, BatteryOperation.ADMIT_C2}:
        return science.admit_procedure(config, one(ContributionManifest), one(BatteryProcedureContribution), one(BatteryCheckpointSummary))
    if operation is BatteryOperation.VOLTAGE:
        return science.assess_voltage(config, one(BatteryAdmission, lambda a: a.consumer_id == "C1"),
                                      one(BatteryAdmission, lambda a: a.consumer_id == "C2"),
                                      tuple(r for r in records if isinstance(r, BatteryTrace)),
                                      tuple(r for r in records if isinstance(r, BatteryRestartAssessment)))
    raise ValueError("unregistered battery operation")


def describe_contributions(draft, authenticated_products):
    from .examples import describe_contributions as describe
    return describe(draft, authenticated_products)


def next_wave_builder(draft, manifest, authenticated_products):
    from .examples import next_wave_builder as build
    return build(draft, manifest, authenticated_products)


from empirical_lawhood.adapters.composition.discovery import bundle as _discovery_bundle
from empirical_lawhood.runtime.executable_bindings import ExecutableBindingContribution
from empirical_lawhood.runtime.extension_bundles import ExtensionContributionKind

_DISCOVERY_BUILT = tuple(_discovery_bundle(manifest.capability_key.removeprefix('battery-recursive.'),
    ExtensionContributionKind.METHOD, manifest, (), None, namespace='battery-recursive',
    maximum_config_bytes=MAX_PRODUCT_BYTES) for manifest in operation_manifests())
_DISCOVERY_COMPONENTS = {value[0].capability_manifests[0].registry_id:
                        tuple(sorted(value[1], key=lambda component: component.registration_id))
                        for value in _DISCOVERY_BUILT}
EXECUTABLE_BINDING_FACTORIES = tuple(sorted((row.provider_factory(components=_DISCOVERY_COMPONENTS[row.manifest().registry_id])
    for row in operation_declarations()), key=lambda value: value.binding.binding_id))
EXECUTABLE_BINDING_CONTRIBUTION = ExecutableBindingContribution(
    'executable-contribution.battery-recursive.operations', '1.0.0',
    tuple(value.binding for value in EXECUTABLE_BINDING_FACTORIES))
EXECUTABLE_RECORD_TYPES = ()
