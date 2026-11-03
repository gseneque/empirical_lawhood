# SPDX-License-Identifier: MPL-2.0
"""Source-bound native singleton operations and exact current trace custody."""
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition, AssessmentPhase, DevelopmentStudySpec, RequirementSupplyAssessment
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_decimal, validate_sha256, validate_stable_id
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_provider import (
    RecursiveExecutionProperties, RecursiveInquiryHooks, RecursiveOperationDeclaration, RecursiveScientificHooks,
)
from . import science
from .contracts import (BatteryInquirySource, BatteryInquirySupply, BatteryInquiryInstance, BatteryInquiryAssessment,
                        BatteryInquiryInitializerAttempt, BatteryInquiryChargingAttempt, BatteryInquiryTransition, BACKEND_SOLVE_SCOPE,
                        DEVELOPMENT_TEMPERATURES, LATER_TEMPERATURES, RECIPES, MODEL_VIEWS, QUESTION, UNIT, scope)

NAMESPACE = 'battery-thermal-inquiry'
MAX_BYTES = None
MEDIA = 'application/json'
BUDGET = ResourceBudget(1, None, 0, None, None, None)
VIEW = 'view.battery-thermal-inquiry.nested-model-recipe-preparations'


@dataclass(frozen=True, slots=True)
class BatteryInquiryAssessedInstance(CanonicalRecord):
    """Original assessed supplier carried with the actual later instance result."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/battery-thermal-inquiry/assessed-instance'
    VERSION: ClassVar[str] = '1.1.0'
    product_id: str
    supplier: BatteryInquirySupply
    assessment: BatteryInquiryAssessment
    prior_use: BatteryInquiryAssessment | None = None

    def __post_init__(self):
        if (type(self.supplier) is not BatteryInquirySupply or type(self.assessment) is not BatteryInquiryAssessment
                or self.product_id != 'product.battery-thermal-inquiry.' + self.assessment.instance.phase
                or self.assessment.supplier != science.identity(self.supplier)
                or self.assessment.scope != self.supplier.scope):
            raise ValueError('thermal carried instance changes original supplier, source, scope or actual phase')
        if self.assessment.instance.phase == 'use':
            if self.prior_use is not None:
                raise ValueError('thermal first use cannot disguise prior instance evidence')
            science.validate_assessment(self.supplier, self.assessment)
        else:
            if self.prior_use is None or self.prior_use.instance.phase != 'use':
                raise ValueError('thermal reuse must retain its exact actual prior use')
            science.validate_assessment(self.supplier, self.assessment, prior_use=self.prior_use)

    @property
    def source(self):
        return self.supplier.source

    @property
    def scope(self):
        return self.assessment.scope

    @property
    def disposition(self):
        return self.assessment.disposition


@dataclass(frozen=True, slots=True)
class BatteryInquiryOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/battery-thermal-inquiry/operation-config'
    VERSION: ClassVar[str] = '1.1.0'
    config_id: str
    operation: str
    source: BatteryInquirySource
    operands: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        science.validate_source(self.source)
        if self.operation not in {'supply', 'use', 'reuse'} or self.config_id != f'config.{NAMESPACE}.{self.operation}':
            raise ValueError('thermal operation/config identity substitution')
        require_sorted_unique_ids(self.operands, attribute='object_id', field_name='operands')
        schemas = ((BatteryInquirySource.SCHEMA,) if self.operation == 'supply' else
                   (BatteryInquiryInstance.SCHEMA, BatteryInquirySupply.SCHEMA if self.operation == 'use' else BatteryInquiryAssessedInstance.SCHEMA))
        if (len(self.operands) != len(schemas) or sorted(row.object_schema for row in self.operands) != sorted(schemas)
                or self.operation == 'supply' and self.operands != (science.identity(self.source),)):
            raise ValueError('thermal config changes complete typed scientific operand census')


@dataclass(frozen=True, slots=True)
class BatteryInquiryNativeTraceBinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/battery-thermal-inquiry/native-trace-binding'
    VERSION: ClassVar[str] = '1.1.0'
    trace: ObjectIdentity
    configuration: ObjectIdentity
    implementation_sha256: str
    disposition: str
    native_provider_attempts: int
    backend_solve_calls: int
    cpu_seconds: Decimal
    wall_seconds: Decimal
    process_peak_rss_bytes: int
    initializer_attempts: tuple[BatteryInquiryInitializerAttempt, ...] = ()
    backend_solve_scope: str = BACKEND_SOLVE_SCOPE
    charging_attempts: tuple[BatteryInquiryChargingAttempt, ...] = ()
    transitions: tuple[BatteryInquiryTransition, ...] = ()

    def __post_init__(self):
        from .contracts import BatteryInquiryTrace, BatteryInquiryNativeConfig
        if (self.trace.object_schema != BatteryInquiryTrace.SCHEMA or self.configuration.object_schema != BatteryInquiryNativeConfig.SCHEMA
                or self.trace.object_version != BatteryInquiryTrace.VERSION or self.configuration.object_version != BatteryInquiryNativeConfig.VERSION):
            raise ValueError('thermal census changes native trace/config types')
        validate_sha256(self.implementation_sha256)
        if self.native_provider_attempts != 1 or self.backend_solve_calls != len(self.charging_attempts) or self.process_peak_rss_bytes < 0:
            raise ValueError('thermal census hides or invents native attempts')
        if (tuple(row.attempt_index for row in self.charging_attempts) != tuple(range(1, len(self.charging_attempts) + 1))
                or tuple(row.transition_index for row in self.transitions) != tuple(range(1, len(self.transitions) + 1))):
            raise ValueError('thermal census omits or reorders actual charging subsolves/transitions')
        if self.backend_solve_scope != BACKEND_SOLVE_SCOPE or tuple(row.attempt_index for row in self.initializer_attempts) != tuple(range(1, len(self.initializer_attempts) + 1)):
            raise ValueError('thermal census disguises charging scope or initializer fallback attempts')
        for name in ('cpu_seconds', 'wall_seconds'):
            validate_decimal(getattr(self, name), field_name=name)
            if getattr(self, name) < 0:
                raise ValueError('thermal census cannot invent negative expense')


@dataclass(frozen=True, slots=True)
class BatteryInquiryNativeCensus(CanonicalRecord):
    """Current native attempts only; ancestor traces remain historical stock."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/battery-thermal-inquiry/native-census'
    VERSION: ClassVar[str] = '1.1.0'
    census_id: str
    source: ObjectIdentity
    phase: str
    traces: tuple[BatteryInquiryNativeTraceBinding, ...]
    native_provider_attempts: int
    backend_solve_calls: int
    initializer_solver_attempts: int = 0
    backend_solve_scope: str = BACKEND_SOLVE_SCOPE

    def __post_init__(self):
        validate_stable_id(self.census_id)
        if self.census_id != f'native-census.{NAMESPACE}.{self.phase}' or self.phase not in {'supply', 'use', 'reuse'}:
            raise ValueError('thermal census changes selected phase identity')
        science.source_scope(self.source)
        ids = tuple(row.trace.object_id for row in self.traces)
        require_sorted_unique_strings(ids, field_name='native_trace_ids')
        count = 36 if self.phase == 'supply' else 12
        if len(self.traces) != count and not (self.phase != 'supply' and not self.traces):
            raise ValueError('thermal census omits selected current trace denominator')
        if (self.native_provider_attempts != sum(row.native_provider_attempts for row in self.traces)
                or self.backend_solve_calls != sum(row.backend_solve_calls for row in self.traces)
                or self.initializer_solver_attempts != sum(len(row.initializer_attempts) for row in self.traces)
                or self.backend_solve_scope != BACKEND_SOLVE_SCOPE):
            raise ValueError('thermal census contradicts exact current native attempt totals')


def native_census(record, phase):
    source = record.source
    if type(record) is BatteryInquirySupply:
        science.validate_supply(record)
        if phase != 'supply':
            raise ValueError('thermal census substitutes supplier acquisition phase')
        traces = record.traces
    else:
        record.__post_init__()
        if record.assessment.instance.phase != phase:
            raise ValueError('thermal census substitutes actual recipient phase')
        traces = record.assessment.traces
    rows = tuple(sorted((BatteryInquiryNativeTraceBinding(science.identity(trace), science.identity(trace.config),
        trace.implementation_sha256, trace.disposition, trace.native_provider_attempts, trace.backend_solve_calls,
        trace.cpu_seconds, trace.wall_seconds, trace.process_peak_rss_bytes, trace.initializer_attempts,
        trace.backend_solve_scope, trace.charging_attempts, trace.transitions) for trace in traces), key=lambda row: row.trace.object_id))
    return BatteryInquiryNativeCensus(f'native-census.{NAMESPACE}.{phase}', science.identity(source), phase, rows,
                                    sum(row.native_provider_attempts for row in rows), sum(row.backend_solve_calls for row in rows),
                                    sum(len(row.initializer_attempts) for row in rows))


PHASES = (
    ('reuse', (('instance', BatteryInquiryInstance), ('supplier', BatteryInquiryAssessedInstance)), BatteryInquiryAssessedInstance),
    ('supply', (('source', BatteryInquirySource),), BatteryInquirySupply),
    ('use', (('instance', BatteryInquiryInstance), ('supplier', BatteryInquirySupply)), BatteryInquiryAssessedInstance),
)


def scientific_operand_sha256s(config):
    return tuple(sorted({config.source.fingerprint(), *(row.object_fingerprint for row in config.operands)}))


def scientific_unit_ids(config):
    return (UNIT,)


def native_effect_slot_ids(config):
    temperatures = DEVELOPMENT_TEMPERATURES if config.operation == 'supply' else (LATER_TEMPERATURES[config.operation],)
    return tuple(sorted('native.' + NAMESPACE + '.' + sha256(science.native_config(config.source, config.operation, temperature, recipe, model).canonical_bytes()).hexdigest()
                        for temperature in temperatures for recipe in RECIPES for model in MODEL_VIEWS))


def development_root(config, *, study_id):
    original_scope = scope(config.source)
    claim = ClaimSpec(f'claim.{NAMESPACE}.{config.operation}', original_scope.world_id, 'population.battery-thermal-inquiry.exposed-lgm50',
        QUESTION, 'Conservative hybrid native charge, sampled constraints and least-time choice within the complete declared chamber/model menu and localization bands; all views/preparations nested.',
        UNIT, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        'Conditional conservative hybrid numerical procedure adequacy and use do not confer exact pointwise ideal CCCV, physical safety, whole-time certification or EL comparative advantage.',
        ('assumption.exposed-lgm50-model-family',), numerical_view_ids=(VIEW,))
    return DevelopmentStudySpec(study_id, QUESTION, ObjectIdentity.from_record(original_scope.system_id, config.source), original_scope.world_id,
        WorldKind.NUMERICAL_SIMULATOR, (UNIT,), (VIEW,), (claim,),
        tuple(sorted({science.identity(config.source), *config.operands}, key=lambda row: row.object_id)))


def scientific_root_validator(config, context):
    phase = next(row for row in PHASES if row[0] == config.operation)
    if (type(context.root) is not DevelopmentStudySpec or context.root != development_root(config, study_id=context.root.study_id)
            or context.node_id != f'{NAMESPACE}.{config.operation}' or context.stage is not ScientificStage.ACQUIRE
            or context.unit_ids != (UNIT,) or context.selected_unit_ids != (UNIT,) or not context.complete_unit_census
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or len(context.config_inputs) != 1 or context.config_inputs[0].record != config):
        raise ValueError('thermal operation changes exact source/question/units/views/configuration or access')
    links = tuple(row for row in context.links if row.consumer_node_id == context.node_id)
    roles = {name: ('OUTCOME' if config.operation == 'reuse' else 'MODEL') if name == 'supplier' else 'SOURCE' for name, _ in phase[1]}
    if (len(links) != len(roles) or {row.consumer_input_id for row in links} != set(roles)
            or any(row.external_input_id is None or row.scientific_role != roles[row.consumer_input_id] for row in links)):
        raise ValueError('thermal operation changes exact original source or parent input roles')
    from .recursive_translation import validate_requirement_config
    for requirement in context.requirements:
        matches = tuple(row for row in context.connections if row.requirement_id == requirement.requirement_id)
        if len(matches) != 1:
            raise ValueError('thermal prerequisite needs its unique exact scientific connection')
        validate_requirement_config(config, requirement, matches[0])


def project_battery_assessments(record, requirement, connection):
    if type(record) is BatteryInquiryNativeCensus:
        return ()  # accounting is authenticated alongside the scientific product
    from .recursive_translation import validate_requirement_record
    validate_requirement_record(record, requirement, connection)
    result = record.assessment
    dispositions = {AssessmentPhase.PROCEDURE: record.supplier.check.disposition,
        AssessmentPhase.INSTANCE: result.instance_disposition, AssessmentPhase.ADMISSION: result.admission_disposition,
        AssessmentPhase.JOINED: result.joined_disposition}
    values = []
    for phase, disposition in dispositions.items():
        reasons = () if disposition is AssessmentDisposition.SATISFIED else tuple(sorted(set(
            (record.supplier.check.reason_codes if phase is AssessmentPhase.PROCEDURE else result.reason_codes) or ('thermal-supply-not-satisfied',))))
        values.append(RequirementSupplyAssessment(f'assessment.{result.instance.instance_id}.{phase.value.lower()}',
            ObjectIdentity.from_record(requirement.requirement_id, requirement), ObjectIdentity.from_record(connection.connection_id, connection),
            phase, disposition, result.instance.instance_id, (science.identity(record),), reasons))
    return tuple(values)


def operation_manifests():
    return tuple(row.manifest() for row in operation_declarations())


def operation_registrations():
    return tuple(row.registration() for row in operation_declarations())


def output_codecs():
    return {record.SCHEMA: record for record in (BatteryInquiryOperationConfig, BatteryInquirySource, BatteryInquirySupply,
        BatteryInquiryInstance, BatteryInquiryAssessment, BatteryInquiryAssessedInstance, BatteryInquiryNativeCensus)}


class BatteryInquiryRunner:
    def __init__(self, role):
        self.role = role
        self.phase = next(row for row in PHASES if row[0] == role)
        self.manifest = next(row for row in operation_manifests() if row.capability_key == f'{NAMESPACE}.{role}')

    def execute(self, context):
        try:
            _, ports, output_type = self.phase
            expected = {BatteryInquiryOperationConfig.SCHEMA: BatteryInquiryOperationConfig, **{record.SCHEMA: record for _, record in ports}}
            if (context.task_id != f'{NAMESPACE}.{self.role}' or context.permissions != self.manifest.permissions
                    or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE or context.resource_budget != BUDGET
                    or len(context.input_ports) != len(expected) or {row.payload_schema for row in context.input_ports} != set(expected)):
                raise ValueError('thermal worker changes exact selected config/input/access census')
            records = {}
            for port in context.input_ports:
                if port.kind is not WorkerInputKind.EXTERNAL or port.media_type != MEDIA or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE:
                    raise ValueError('thermal worker changes exact exposed external input boundary')
                raw = port.read()
                if len(raw) != port.size_bytes:
                    raise ValueError('thermal worker changes retained input materialization')
                records[port.payload_schema] = decode_canonical_bytes(raw, expected[port.payload_schema], maximum_bytes=None)
            config = records[BatteryInquiryOperationConfig.SCHEMA]
            if config.operation != self.role or config.config_id != context.config.config_id or config.fingerprint() != context.config.content_sha256:
                raise ValueError('thermal worker substitutes exact selected immutable config')
            inputs = {name: records[record.SCHEMA] for name, record in ports}
            if tuple(sorted((science.identity(row) for row in inputs.values()), key=lambda row: row.object_id)) != config.operands:
                raise ValueError('thermal worker substitutes source or supplied operands')
            # All configuration, original-source, incoming-parent and output
            # contracts pass before the first native provider can be contacted.
            outputs = {row.output_id: row for row in context.output_ports}
            expected_outputs = {context.task_id+'.native-census': BatteryInquiryNativeCensus, context.task_id+'.product': output_type}
            if len(outputs) != 2 or set(outputs) != set(expected_outputs) or any(
                    row.payload_schema != expected_outputs[key].SCHEMA or row.profile is not ArtifactProfile.CANONICAL_JSON or row.media_type != MEDIA
                    for key, row in outputs.items()):
                raise ValueError('thermal worker substitutes exact canonical product/native census outputs')
            if self.role == 'supply':
                if inputs['source'] != config.source:
                    raise ValueError('thermal worker changes initial source stock')
                product = science.supply(inputs['source'])
            else:
                prior = inputs['supplier']
                supplier = prior if self.role == 'use' else prior.supplier
                if self.role == 'reuse':
                    prior.__post_init__()
                    if prior.assessment.instance.phase != 'use':
                        raise ValueError('thermal reuse requires the actual distinct prior use assessment')
                science.validate_supply(supplier)
                previous = prior.assessment if self.role == 'reuse' else None
                expected_instance = (science.compatible_instance(supplier, self.role, prior_use=previous) if previous is not None
                                     else science.compatible_instance(supplier, self.role))
                if supplier.source != config.source or inputs['instance'] != expected_instance:
                    raise ValueError('thermal worker changes actual source-bound later preparation')
                actual = (science.assess(supplier, inputs['instance'], prior_use=previous) if previous is not None
                          else science.assess(supplier, inputs['instance']))
                product = BatteryInquiryAssessedInstance(f'product.{NAMESPACE}.{self.role}', supplier, actual, previous)
            census = native_census(product, self.role)
            return RunnerResult((TaskOutputPayload(context.task_id+'.native-census', census.canonical_bytes()),
                                 TaskOutputPayload(context.task_id+'.product', product.canonical_bytes())),
                (ReceiptCheck('thermal-native-product-and-trace-census', True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def inquiry_record_identity(record):
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from .science import identity
    if type(record) is BatteryInquiryNativeCensus:
        return ObjectIdentity.from_record(record.census_id, record)
    return identity(record)


def _operation_declaration(role, inputs, output):
    from .recursive_translation import (
        describe_contributions, next_wave_builder, inquiry_outcome_projector,
        inquiry_evidence_projector, inquiry_endpoint_validator,
    )

    return RecursiveOperationDeclaration(
        capability_key=f'{NAMESPACE}.{role}', capability_version='1.1.0',
        implementation_id=f'{NAMESPACE}.complete-conservative-hybrid-native-{role}-v1.1',
        kind=CapabilityKind.SIMULATOR, config_record_type=BatteryInquiryOperationConfig,
        stage=ScientificStage.ACQUIRE,
        input_ports=tuple(RecursivePortContract(name, record.SCHEMA, MEDIA, MAX_BYTES)
            for name, record in inputs),
        outputs=(OutputTemplate('native-census', BatteryInquiryNativeCensus.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, MEDIA, '.json'),
            OutputTemplate('product', output.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA, '.json')),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=BUDGET,
        conformance_check_ids=('complete-native-subsolve-and-transition-census',
            'independent-source-bound-assessment', 'nonpromotable-numerical-family'),
        runner_factory=lambda: BatteryInquiryRunner(role), record_codecs=output_codecs(),
        scientific_hooks=RecursiveScientificHooks(
            assessment_projector=project_battery_assessments if role != 'supply' else None,
            scientific_operand_sha256s=scientific_operand_sha256s,
            scientific_unit_ids=scientific_unit_ids, native_effect_slot_ids=native_effect_slot_ids,
            scientific_root_validator=scientific_root_validator),
        inquiry_hooks=RecursiveInquiryHooks(contribution_describer=describe_contributions,
            next_wave_builder=next_wave_builder, inquiry_outcome_projector=inquiry_outcome_projector,
            inquiry_evidence_projector=inquiry_evidence_projector,
            inquiry_endpoint_validator=inquiry_endpoint_validator,
            inquiry_record_identity=inquiry_record_identity),
        execution_properties=RecursiveExecutionProperties(native_effect=True, complete_unit_census=True))


def operation_declarations():
    return tuple(_operation_declaration(*phase) for phase in PHASES)
