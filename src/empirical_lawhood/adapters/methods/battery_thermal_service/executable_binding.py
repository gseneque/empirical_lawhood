# SPDX-License-Identifier: MPL-2.0
"""Registered recursive operations retaining resource, source and custody guards."""

from empirical_lawhood.runtime.recursive_provider import (RecursiveOperationDeclaration,RecursiveExecutionProperties,RecursiveScientificHooks)

from dataclasses import dataclass
from decimal import Decimal
from functools import partial
from hashlib import sha256

from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract

from .contracts import BatteryThermalConfig, BatteryThermalTrace, BatteryThermalAssessment, MAX_PRODUCT_BYTES, QUESTION

RESOURCE = ResourceBudget(1, None, 0, None, None, None)
PERMISSIONS = tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT,
                            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS), key=lambda value: value.value))
MEDIA = "application/json"
WORLD = "battery-thermal-service-numerical-world"
SYSTEM = "chen2020-spme-lumped-arbitrary"


def operation_declaration(operation):
    if operation not in ('acquire', 'assess'):
        raise ValueError('thermal operation requires its exact acquire or assess role')
    native = operation == 'acquire'
    output = BatteryThermalTrace if native else BatteryThermalAssessment
    return RecursiveOperationDeclaration(
        capability_key='battery-thermal-service.' + operation, capability_version='1.0.0',
        implementation_id='battery-thermal-service-v1', runtime_id='cpython-3.11-battery-thermal-service',
        implementation_sha256=sha256(f'battery-thermal-service-v1:{operation}:arbitrary-geometry-realized-current'.encode()).hexdigest(),
        kind=CapabilityKind.SIMULATOR if native else CapabilityKind.ANALYSIS, config_record_type=BatteryThermalConfig,
        stage=ScientificStage.ACQUIRE if native else ScientificStage.FALSIFY,
        input_ports=() if native else (RecursivePortContract('trace', BatteryThermalTrace.SCHEMA, MEDIA, MAX_PRODUCT_BYTES),),
        outputs=(OutputTemplate('product', output.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA, '.json'),),
        permissions=PERMISSIONS, evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
        resources=RESOURCE,
        conformance_check_ids=('complete-native-receiver-census', 'nonpromotable-development', 'sampled-and-continuous-envelope-distinct'),
        runner_factory=lambda operation=operation: BatteryThermalRunner(operation), record_codecs=output_codecs(),
        execution_properties=RecursiveExecutionProperties(
            native_effect=native, complete_unit_census=native, requires_clean_commit=False, requires_active_mount=False,
        ),
        scientific_hooks=RecursiveScientificHooks(
            scientific_operand_sha256s=lambda config: (config.source.fingerprint(),),
            scientific_unit_ids=lambda config: (config.unit_id,), native_effect_slot_ids=_slots if native else None,
            scientific_root_validator=partial(scientific_root_validator, operation),
        ),
    )


def operation_declarations():
    return tuple((operation_declaration(operation) for operation in ('acquire', 'assess')))


def _manifest(operation):
    return operation_declaration(operation).manifest()


def operation_manifests():
    return tuple(row.manifest() for row in operation_declarations())


def scientific_root_validator(operation, config, context):
    if config.operation != operation or context.stage is not (ScientificStage.ACQUIRE if operation == "acquire" else ScientificStage.FALSIFY):
        raise ValueError("thermal scientific operation differs from its selected registration and stage")
    root = context.root
    if (not isinstance(root, DevelopmentStudySpec) or root.question != QUESTION
            or root.world_id != WORLD or root.world_kind is not WorldKind.NUMERICAL_SIMULATOR
            or root.system != ObjectIdentity.from_record(SYSTEM, config.source)
            or root.assigned_unit_ids != (config.unit_id,) or root.numerical_view_ids != (config.view,)
            or root.scientific_operands != (ObjectIdentity.from_record("battery-thermal-service-source", config.source),)
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise ValueError("thermal scientific root changes its frozen question, source, units or views")
    from .examples import thermal_service_draft
    expected_claim = thermal_service_draft(initial_temperature_k=config.initial_temperature_k, view=config.view, word=config.word).development_study.claims[0]
    if len(root.claims) != 1 or any(getattr(root.claims[0], field) != getattr(expected_claim, field) for field in
                                  ("world_id", "relation_id", "proposition", "estimand", "physical_independent_unit_id",
                                   "requested_rung", "evidence_ceiling", "outcome_access", "visibility_ceiling", "promotion_rule",
                                   "assumption_ids", "derivation_parent_ids", "parent_visibility_ceilings", "numerical_view_ids", "extensions")):
        raise ValueError("thermal scientific claim differs from its actual scientific root")
    records = {row.node_id: row.record for row in context.config_inputs}
    if records.get(context.node_id) != config:
        raise ValueError("thermal scientific root lacks its actual config")
    for link in context.links:
        if link.consumer_node_id == context.node_id:
            supplier = records.get(link.producer_node_id)
            if (config.operation != "assess" or link.consumer_input_id != "trace"
                    or link.producer_output_id != "product" or link.scientific_role != "OUTCOME"
                    or not isinstance(supplier, BatteryThermalConfig) or supplier.operation != "acquire"
                    or any(getattr(supplier, field) != getattr(config, field) for field in
                           ("source", "protocol_sha256", "unit_id", "initial_temperature_k", "initial_soc", "word", "view"))):
                raise ValueError("thermal assessment changes its internal scientific supplier")


def _slots(config):
    semantic = {"source": config.source.fingerprint(), "protocol": config.protocol_sha256,
                "initial_temperature_k": "23c" if config.initial_temperature_k == Decimal("296.15") else "27c",
                "initial_soc": "shipping-soc-0.30",
                "word": config.word, "view": config.view}
    return ("native.battery-thermal-service." + sha256(canonical_json_bytes(semantic)).hexdigest(),)


def operation_registrations():
    return tuple(row.registration() for row in operation_declarations())


def output_codecs():
    return {record.SCHEMA: record for record in (BatteryThermalTrace, BatteryThermalAssessment)}


@dataclass(frozen=True, slots=True)
class BatteryThermalRunner:
    operation: str

    @property
    def manifest(self):
        return _manifest(self.operation)

    def execute(self, context):
        configs = [port for port in context.input_ports if port.payload_schema == BatteryThermalConfig.SCHEMA]
        if (len(configs) != 1 or context.permissions != PERMISSIONS or context.resource_budget != RESOURCE
                or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE):
            raise ValueError("thermal task resource, config or access census differs")
        config = decode_canonical_bytes(configs[0].read(), BatteryThermalConfig, maximum_bytes=MAX_PRODUCT_BYTES)
        if config.fingerprint() != context.config.content_sha256 or config.operation != self.operation:
            raise ValueError("thermal task selected config differs")
        inputs = [port for port in context.input_ports if port not in configs]
        output = BatteryThermalTrace if self.operation == "acquire" else BatteryThermalAssessment
        if len(context.output_ports) != 1 or context.output_ports[0].payload_schema != output.SCHEMA or context.output_ports[0].output_id != f"{context.task_id}.product":
            raise ValueError("thermal task output census differs")
        from .science import acquire, assess
        if self.operation == "acquire":
            if inputs:
                raise ValueError("thermal native acquisition takes no latent supplied state")
            product = acquire(config)
        else:
            if (len(inputs) != 1 or inputs[0].payload_schema != BatteryThermalTrace.SCHEMA
                    or inputs[0].outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE):
                raise ValueError("thermal assessment native input census differs")
            product = assess(config, decode_canonical_bytes(inputs[0].read(), BatteryThermalTrace, maximum_bytes=MAX_PRODUCT_BYTES))
        payload = product.canonical_bytes()
        return RunnerResult((TaskOutputPayload(context.output_ports[0].output_id, payload),), (ReceiptCheck("battery-thermal-typed-terminal", True, ()),))


from empirical_lawhood.adapters.composition.discovery import bundle as _discovery_bundle
from empirical_lawhood.runtime.extension_bundles import ExtensionContributionKind
from empirical_lawhood.runtime.executable_bindings import ExecutableBindingContribution

_DISCOVERY_BUILT = tuple(_discovery_bundle(operation, ExtensionContributionKind.METHOD, _manifest(operation), (), None,
                                         namespace="battery-thermal-service", maximum_config_bytes=MAX_PRODUCT_BYTES)
                         for operation in ("acquire", "assess"))
EXECUTABLE_BINDING_FACTORIES = tuple(row.provider_factory(
    components=tuple(sorted(components,key=lambda item:item.registration_id)))
    for row,(_,components) in zip(operation_declarations(),_DISCOVERY_BUILT,strict=True))
EXECUTABLE_BINDING_CONTRIBUTION = ExecutableBindingContribution("executable-contribution.battery-thermal-service.operations", "1.0.0",
                                                             tuple(factory.binding for factory in EXECUTABLE_BINDING_FACTORIES))
EXECUTABLE_RECORD_TYPES = ()
