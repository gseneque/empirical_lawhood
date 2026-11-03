# SPDX-License-Identifier: MPL-2.0
"""Seedless current E3 feature declaration and prepared worker.

The current scientific root/API authenticates original allocation, reservation,
numerical-profile and public-source custody. This PURE worker accepts only
seedless physical metadata, current prefix products and their actual sealed
array ports. It grants no source qualification, issue, execution or reveal.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterNumericalDesign
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole, MatrixProgrammeRoot
from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseProtocol
from empirical_lawhood.adapters.methods.matrix_scheduled_history.operation_bindings import _dependency, _raw_input
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity as scheduled_identity
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.input_access import validated_scientific_input_edges
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskContext, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.plans import ExecutionTask, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationDeclaration, RecursiveScientificHooks

from .configured_protected_specification import ConfiguredProtectedE3Specification as MatrixResponseErrorSpecification
from .configured_protected_feature_records import ConfiguredProtectedE3CausalFeature
from .configured_protected_feature_science import project_configured_protected_e3_feature as project_protected_e3_feature
from .configured_protected_prefix_records import ConfiguredProtectedE3CausalPrefix, ConfiguredProtectedE3FrameAssessment, ConfiguredProtectedE3NumericalAssessment, ConfiguredProtectedE3PrefixWitness
from .configured_protected_prefix_workers import _read
from .protected_input_custody import matches_protected_e3_producer
from .configured_protected_tasks import feature_task_id
from .configured_protected_source_records import NAMESPACE, ProtectedE3SourcePhase, _reference, identity, source_task_id
from .configured_protected_response_records import ConfiguredProtectedE3PhysicalForecast

BUDGET = ResourceBudget(1, None, 0, None, None, None)



@dataclass(frozen=True, slots=True)
class ConfiguredProtectedE3FeatureConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/configured-protected-feature-config"
    record_id: str
    specification: ObjectIdentity
    allocation: ObjectIdentity
    public_source: ObjectIdentity
    numerical_design: ObjectIdentity
    root: MatrixProgrammeRoot

    def __post_init__(self):
        for value, kind in ((self.specification, MatrixResponseErrorSpecification), (self.allocation, UnitAllocation),
                (self.public_source, ScheduledPublicSource), (self.numerical_design, MatrixParameterNumericalDesign)):
            _reference(value, kind)
        if type(self.root) is not MatrixProgrammeRoot:
            raise TypeError("protected E3 feature configuration needs its exact seedless original root")
        self.root.__post_init__()
        if (self.root.role not in (MatrixProgrammeRole.CALIBRATION, MatrixProgrammeRole.CONFIRMATION)
                or self.record_id != "config." + feature_task_id(self.root.root_id)):
            raise ValueError("protected E3 feature configuration changes its current whole root/role/task")


FEATURE_RECORD_INPUTS = (
    ("specification", MatrixResponseErrorSpecification, None),
    ("public-source", ScheduledPublicSource, None),
    ('protocol', ScheduledResponseProtocol, None),
    ("numerical-design", MatrixParameterNumericalDesign, None),
    ("numerical", ConfiguredProtectedE3NumericalAssessment, ProtectedE3SourcePhase.NUMERICAL),
    ("witness", ConfiguredProtectedE3PrefixWitness, ProtectedE3SourcePhase.MEASURE),
    ("assessment", ConfiguredProtectedE3FrameAssessment, ProtectedE3SourcePhase.CHECK),
    ("causal", ConfiguredProtectedE3CausalPrefix, ProtectedE3SourcePhase.PROJECT),
    ('physical', ConfiguredProtectedE3PhysicalForecast, 'physical-forecast'),
)
FEATURE_ARRAY_INPUTS = (("causal-arrays", ProtectedE3SourcePhase.PROJECT),
    ("diagnostic-arrays", ProtectedE3SourcePhase.MEASURE), ('physical-arrays', 'physical-forecast'))


def feature_producer_task(root_id, phase):
    if phase == 'physical-forecast':
        from .configured_protected_response_preparation import response_task_id
        return response_task_id(root_id, phase)
    return source_task_id(root_id, phase)


def _config(config):
    from .configured_continued_response import ConfiguredE3ContinuedFeatureConfig
    if type(config) not in (ConfiguredProtectedE3FeatureConfig, ConfiguredE3ContinuedFeatureConfig):
        raise TypeError("protected E3 feature declaration requires its exact seedless configuration")
    config.__post_init__()


def _units(config):
    _config(config)
    return (config.root.independent_group_id,)


def _operands(config):
    _config(config)
    refs = (config.specification, config.allocation, config.public_source, config.numerical_design)
    if hasattr(config, 'continuation'):
        refs += (config.continuation,)
    return tuple(sorted({row.object_fingerprint for row in refs}))


def feature_declaration(*, continued=False) -> RecursiveOperationDeclaration:
    from .configured_continued_response import ConfiguredE3ContinuedFeatureConfig
    from .configured_retained_execution import ConfiguredE3RetainedExecution
    config_kind = ConfiguredE3ContinuedFeatureConfig if continued else ConfiguredProtectedE3FeatureConfig
    records = FEATURE_RECORD_INPUTS + ((('retention', ConfiguredE3RetainedExecution, None),) if continued else ())
    codecs = {kind.SCHEMA: kind for kind in (config_kind, ConfiguredProtectedE3CausalFeature,
        *(kind for _, kind, _ in records))}
    inputs = tuple(sorted((*(RecursivePortContract(name, kind.SCHEMA, "application/json", None)
        for name, kind, _ in records), *(RecursivePortContract(name, MATRIX_ARRAY_SCHEMA,
        "application/x-npz", MAXIMUM_MATRIX_ARRAY_BYTES) for name, _ in FEATURE_ARRAY_INPUTS)), key=lambda row: row.port_id))
    key = NAMESPACE + ('.continued-feature' if continued else '.feature')
    return RecursiveOperationDeclaration(key, "2.0.0", key + ".mechanical-parent-and-matched-values-v3",
        CapabilityKind.TRANSFORM, config_kind, ScientificStage.TRANSFORM, inputs,
        (OutputTemplate("product", ConfiguredProtectedE3CausalFeature.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),),
        tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
            CapabilityPermission.READ_FROZEN_MODELS))), EvidenceCeiling.RESPONSE, OutcomeAccess.OUTCOME_BLIND,
        VisibilityCeiling.PROSPECTIVE, BUDGET, tuple(sorted(("seedless-current-prefix-and-numerical-profile", "exact-prepared-receipt-edges-and-array-ports"))),
        lambda: ConfiguredProtectedE3FeatureRunner(continued=continued), codecs, scientific_hooks=RecursiveScientificHooks(
            scientific_unit_ids=_units, scientific_operand_sha256s=_operands),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,), storage_codecs=MATRIX_STORAGE_CODECS)


def _received(context, manifest):
    from .configured_continued_response import ConfiguredE3ContinuedFeatureConfig, retained_array_port
    from .configured_retained_execution import ConfiguredE3RetainedExecution, source_binding
    continued = manifest.config_schema == ConfiguredE3ContinuedFeatureConfig.SCHEMA
    config_kind = ConfiguredE3ContinuedFeatureConfig if continued else ConfiguredProtectedE3FeatureConfig
    if type(context) is not TaskContext:
        raise TypeError("protected E3 feature needs its exact current worker context")
    context.__post_init__()
    prepared = context.prepared_invocation
    if (type(prepared) is not PreparedInvocationContract or type(prepared.execution_task_record) is not ExecutionTask
            or prepared.manifest != manifest or prepared.native_effect
            or prepared.execution_task_record.stage is not ScientificStage.TRANSFORM
            or context.permissions != manifest.permissions or context.outcome_access is not OutcomeAccess.OUTCOME_BLIND
            or not manifest.resource_ceiling.contains(context.resource_budget)
            or any(output.outcome_access is not OutcomeAccess.OUTCOME_BLIND
                or output.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE for output in prepared.execution_task_record.outputs)):
        raise ValueError("protected E3 feature changes its actual prepared context or blind scope")
    if (len(context.output_ports) != 1 or context.output_ports[0].output_id.rsplit(".", 1)[-1] != "product"
            or (context.output_ports[0].payload_schema, context.output_ports[0].profile, context.output_ports[0].media_type) !=
               (ConfiguredProtectedE3CausalFeature.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json")
            or context.output_ports[0].logical_artifact_id is None):
        raise ValueError("protected E3 feature changes its exact canonical output contract")
    ports = {port.artifact_id: port for port in context.input_ports}
    contracts = {row.artifact_id: row for row in prepared.inputs}
    config_port = ports.get(context.config.artifact_id)
    if (config_port is None or config_port.payload_schema != config_kind.SCHEMA
            or config_port.media_type != "application/json" or config_port.kind is not WorkerInputKind.EXTERNAL
            or any(port.outcome_access is not OutcomeAccess.OUTCOME_BLIND
                or port.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE for port in context.input_ports)):
        raise ValueError("protected E3 feature substitutes a seedless configuration or received input scope")
    config = _read(config_port, contracts[config_port.artifact_id], config_kind)
    if (context.task_id != feature_task_id(config.root.root_id) or context.config.config_id != config.record_id
            or context.config.content_sha256 != config.fingerprint()):
        raise ValueError("protected E3 feature substitutes its actual immutable current task/configuration")
    expected = {name: (kind, producer, "product") for name, kind, producer in FEATURE_RECORD_INPUTS}
    if continued:
        expected['retention'] = ConfiguredE3RetainedExecution, None, 'product'
    expected.update((name, (None, producer, "arrays")) for name, producer in FEATURE_ARRAY_INPUTS)
    edges = validated_scientific_input_edges(context, config_port=config_port)
    if (len(edges) != len(expected) or {row.consumer_input_id for row in edges} != set(expected)
            or {row.operational_logical_artifact_id for row in edges} != set(ports) - {config_port.artifact_id}):
        raise ValueError("protected E3 feature loses exact seedless input and receipt edge census")
    records, arrays = {}, {}
    for edge in edges:
        kind, producer, output = expected[edge.consumer_input_id]
        port = ports[edge.operational_logical_artifact_id]
        if ((port.payload_schema, port.media_type) != ((kind.SCHEMA, "application/json") if kind else (MATRIX_ARRAY_SCHEMA, "application/x-npz"))
                or producer is None and (port.kind is not WorkerInputKind.EXTERNAL or edge.producer_task_id is not None)
                or producer is not None and not matches_protected_e3_producer(
                    edge, feature_producer_task(config.root.root_id, producer), output)):
            raise ValueError("protected E3 feature substitutes exact current producer task/port or input type")
        if producer is not None:
            _dependency(context, port, config.root.root_id, getattr(producer, 'value', producer), namespace=NAMESPACE)
        if kind:
            records[edge.consumer_input_id] = _read(port, contracts[port.artifact_id], kind)
        else:
            if contracts[port.artifact_id].logical.profile is not ArtifactProfile.MATRIX_ARRAY_NPZ:
                raise ValueError("protected E3 feature changes original physical array codec")
            arrays[edge.consumer_input_id] = port
    public, specification, design, numerical = (records[name] for name in ("public-source", "specification", "numerical-design", "numerical"))
    causal, witness, assessment = (records[name] for name in ("causal", "witness", "assessment"))
    protocol, physical = records['protocol'], records['physical']
    if (specification.identity != config.specification or public.root != config.root
            or ObjectIdentity.from_record(config.public_source.object_id, public) != config.public_source
            or scheduled_identity(design) != config.numerical_design or numerical.numerical_design != config.numerical_design
            or numerical.source != public.source or numerical.history != causal.history or identity(numerical) != causal.numerical
            or numerical.source != witness.source or witness.numerical != causal.numerical
            or protocol.public_source != public or physical.source != public.source
            or physical.causal_prefix != identity(causal)
            or physical.protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)):
        raise ValueError("protected E3 feature changes original public source/profile or current numerical evidence")
    tick = public.policy.cutoff_tick
    if (tuple((control.denominator_steps, control.denominator_real_coordinates, control.tolerance) for control in numerical.controls) !=
            ((tick, 192, design.trajectory_tolerance), (2*tick, 192, design.trajectory_tolerance),
             (tick, 192, design.bridge_tolerance), (tick, 96, design.trajectory_tolerance))
            or (causal.reason == "PREFIX_NUMERICAL_CONTROLS_NOT_SATISFIED") !=
               (not numerical.numerical_pass or not assessment.numerical_pass)):
        raise ValueError("protected E3 feature changes complete original native controls, cutoff or numerical nonuse")
    retention = records.get('retention')
    if retention is not None:
        if (retention.identity != config.continuation or retention.specification != config.specification
                or retention.allocation != config.allocation or context.run_id != retention.continued_run_id
                or prepared.implementation != source_binding(retention.response_provenance)):
            raise ValueError('continued E3 feature changes original science or its continued source')
    else:
        _raw_input(context, ports, causal.arrays, config.root.root_id, "project", namespace=NAMESPACE)
        _raw_input(context, ports, witness.arrays, config.root.root_id, "measure", namespace=NAMESPACE)
        _raw_input(context, ports, physical.arrays, config.root.root_id, 'physical-forecast', namespace=NAMESPACE)
    for name, original in (("causal-arrays", causal.arrays), ("diagnostic-arrays", witness.arrays), ('physical-arrays', physical.arrays)):
        port = arrays[name]
        if retention is not None:
            producer = dict(FEATURE_ARRAY_INPUTS)[name]
            arrays[name] = retained_array_port(port, original, producer=feature_producer_task(config.root.root_id, producer),
                retention=retention, context=context)
            continue
        selected = contracts[port.artifact_id]
        if (port.artifact_id != original.array_artifact.artifact_id
                or (selected.logical.content_sha256, selected.physical_sha256) !=
                   (original.array_artifact.sha256, original.array_artifact.sha256)):
            raise ValueError("protected E3 feature substitutes actual ordinary array publication")
    return config, public, specification, causal, witness, assessment, arrays, protocol, physical


class ConfiguredProtectedE3FeatureRunner:
    def __init__(self, *, continued=False):
        self.manifest = feature_declaration(continued=continued).manifest()

    def execute(self, context: TaskContext) -> RunnerResult:
        try:
            _, public, specification, causal, witness, assessment, arrays, protocol, physical = _received(context, self.manifest)
            result = project_protected_e3_feature(specification, public, causal, witness, assessment,
                arrays["causal-arrays"], arrays["diagnostic-arrays"], protocol=protocol, physical=physical,
                physical_raw=arrays['physical-arrays'])
            return RunnerResult((TaskOutputPayload(context.output_ports[0].output_id, result.canonical_bytes()),),
                (ReceiptCheck("protected-e3-feature-seedless-current-profile-and-dataset-custody", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()
