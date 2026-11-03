# SPDX-License-Identifier: MPL-2.0
"""Current PURE prefix workers over exact prepared ports and receipt edges.

This module owns only the four source-side numerical readers. Its manifest and
native source operands are ineligible for a seedless predictor. Declarations,
scientific roots, current issue/authority and source qualification remain with
their existing owners; a prepared invocation supplies no such qualification.
"""

from .protected_input_custody import read_protected_e3_worker_input as _read

from dataclasses import dataclass, replace

from empirical_lawhood.adapters.methods.matrix_scheduled_history.operation_bindings import (
    _dependency, _raw_input, validate_original_prefix_receipt,
)
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.input_access import validated_scientific_input_edges
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityManifest
from empirical_lawhood.runtime.execution import RunnerResult, TaskContext, WorkerInputKind, WorkerInputPort, WorkerOutputPort
from empirical_lawhood.runtime.plans import ExecutionTask, ScientificStage
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract

from . import configured_protected_prefix_science as science
from .configured_protected_specification import ConfiguredProtectedE3Specification as MatrixResponseErrorSpecification
from .protected_input_custody import matches_protected_e3_producer
from .configured_protected_prefix_records import (
    ConfiguredProtectedE3CausalPrefix, ConfiguredProtectedE3FrameAssessment, ConfiguredProtectedE3NumericalAssessment,
    ConfiguredProtectedE3PrefixHistory, ConfiguredProtectedE3PrefixWitness,
)
from .configured_protected_source_records import NAMESPACE, ProtectedE3NativeSourceManifest, ConfiguredProtectedE3SourceConfig, ProtectedE3SourcePhase, source_task_id


from .protected_input_custody import validate_protected_e3_pure_outputs as _outputs

@dataclass(frozen=True, slots=True)
class ProtectedE3PrefixPhase:
    phase: ProtectedE3SourcePhase
    stage: ScientificStage
    records: tuple[tuple[str, type[CanonicalRecord], ProtectedE3SourcePhase | None], ...]
    arrays: tuple[tuple[str, ProtectedE3SourcePhase], ...]
    product_type: type[CanonicalRecord]
    array_output: bool


_COMMON = (("prefix-config", ConfiguredProtectedE3SourceConfig, None), ("manifest", ProtectedE3NativeSourceManifest, None),
    ("specification", MatrixResponseErrorSpecification, None), ("history", ConfiguredProtectedE3PrefixHistory, ProtectedE3SourcePhase.PREFIX))
_NUMERICAL = (*_COMMON, ("numerical", ConfiguredProtectedE3NumericalAssessment, ProtectedE3SourcePhase.NUMERICAL))
_WITNESS = (*_NUMERICAL, ("witness", ConfiguredProtectedE3PrefixWitness, ProtectedE3SourcePhase.MEASURE))
_PREFIX_ARRAYS = (("prefix-arrays", ProtectedE3SourcePhase.PREFIX),)
_DIAGNOSTIC_ARRAYS = (*_PREFIX_ARRAYS, ("diagnostic-arrays", ProtectedE3SourcePhase.MEASURE))
PURE_PREFIX_PHASES = (
    ProtectedE3PrefixPhase(ProtectedE3SourcePhase.NUMERICAL, ScientificStage.FALSIFY, _COMMON, _PREFIX_ARRAYS, ConfiguredProtectedE3NumericalAssessment, False),
    ProtectedE3PrefixPhase(ProtectedE3SourcePhase.MEASURE, ScientificStage.TRANSFORM, _NUMERICAL, _PREFIX_ARRAYS, ConfiguredProtectedE3PrefixWitness, True),
    ProtectedE3PrefixPhase(ProtectedE3SourcePhase.CHECK, ScientificStage.FALSIFY, _WITNESS, _DIAGNOSTIC_ARRAYS, ConfiguredProtectedE3FrameAssessment, False),
    ProtectedE3PrefixPhase(ProtectedE3SourcePhase.PROJECT, ScientificStage.TRANSFORM,
        (*_WITNESS, ("assessment", ConfiguredProtectedE3FrameAssessment, ProtectedE3SourcePhase.CHECK)),
        _DIAGNOSTIC_ARRAYS, ConfiguredProtectedE3CausalPrefix, True),
)


def prefix_worker_phase(phase: ProtectedE3SourcePhase) -> ProtectedE3PrefixPhase:
    if type(phase) is not ProtectedE3SourcePhase or phase is ProtectedE3SourcePhase.PREFIX:
        raise ValueError("protected E3 PURE worker requires its closed nonnative prefix phase")
    return next(row for row in PURE_PREFIX_PHASES if row.phase is phase)


@dataclass(frozen=True, slots=True)
class ProtectedE3PrefixWorkerInputs:
    config: ConfiguredProtectedE3SourceConfig
    prefix_config: ConfiguredProtectedE3SourceConfig
    source_manifest: ProtectedE3NativeSourceManifest
    specification: MatrixResponseErrorSpecification
    history: ConfiguredProtectedE3PrefixHistory
    numerical: ConfiguredProtectedE3NumericalAssessment | None
    witness: ConfiguredProtectedE3PrefixWitness | None
    assessment: ConfiguredProtectedE3FrameAssessment | None
    prefix_raw: WorkerInputPort
    diagnostic_raw: WorkerInputPort | None
    output_ports: tuple[WorkerOutputPort, ...]






def decode_protected_e3_prefix_worker(context: TaskContext, phase: ProtectedE3SourcePhase,
        *, manifest: CapabilityManifest) -> ProtectedE3PrefixWorkerInputs:
    """Validate actual prepared task/port edges before any scientific arithmetic."""
    selected = prefix_worker_phase(phase)
    if type(context) is not TaskContext or type(manifest) is not CapabilityManifest:
        raise TypeError("protected E3 PURE worker requires exact context and declaration-owned manifest")
    context.__post_init__()
    manifest.__post_init__()
    prepared = context.prepared_invocation
    if (type(prepared) is not PreparedInvocationContract or type(prepared.execution_task_record) is not ExecutionTask
            or prepared.manifest != manifest or prepared.native_effect or prepared.execution_task_record.stage is not selected.stage
            or any(output.outcome_access is not OutcomeAccess.OUTCOME_BLIND
                or output.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE for output in prepared.execution_task_record.outputs)
            or manifest.capability_key != NAMESPACE + "." + phase.value
            or context.permissions != manifest.permissions or context.outcome_access is not OutcomeAccess.OUTCOME_BLIND
            or not manifest.resource_ceiling.contains(context.resource_budget)
            or (context.config.config_schema, context.config.config_schema_sha256) !=
               (manifest.config_schema, manifest.config_schema_sha256)):
        raise ValueError("protected E3 PURE worker changes its exact prepared phase/configuration/access/permissions")
    prepared.validate_context(context)
    _outputs(context, selected)
    contracts = {row.artifact_id: row for row in prepared.inputs}
    ports = {port.artifact_id: port for port in context.input_ports}
    config_port = ports.get(context.config.artifact_id)
    if (config_port is None or type(config_port) is not WorkerInputPort
            or config_port.payload_schema != ConfiguredProtectedE3SourceConfig.SCHEMA
            or config_port.media_type != "application/json"
            or config_port.kind is not WorkerInputKind.EXTERNAL):
        raise ValueError("protected E3 PURE worker loses its exact automatic configuration input")
    for port in context.input_ports:
        if (type(port) is not WorkerInputPort or port.outcome_access is not OutcomeAccess.OUTCOME_BLIND
                or port.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE):
            raise ValueError("protected E3 PURE worker changes a received input's original blind prospective scope")
    config = _read(config_port, contracts[config_port.artifact_id], ConfiguredProtectedE3SourceConfig)
    if (config.phase is not phase or config.record_id != context.config.config_id
            or config.fingerprint() != context.config.content_sha256
            or context.task_id != source_task_id(config.source.root_id, phase)):
        raise ValueError("protected E3 PURE worker substitutes its actual selected phase/root/configuration")
    expected = {name: (kind, producer, "product") for name, kind, producer in selected.records}
    expected.update((name, (None, producer, "arrays")) for name, producer in selected.arrays)
    edges = validated_scientific_input_edges(context, config_port=config_port)
    if (len(edges) != len(expected) or {edge.consumer_input_id for edge in edges} != set(expected)
            or {edge.operational_logical_artifact_id for edge in edges} != set(ports) - {config_port.artifact_id}):
        raise ValueError("protected E3 PURE worker loses complete selected scientific input edges")
    records, raw_ports = {}, {}
    for edge in edges:
        kind, producer, output = expected[edge.consumer_input_id]
        port = ports[edge.operational_logical_artifact_id]
        schema, media = (kind.SCHEMA, "application/json") if kind else (MATRIX_ARRAY_SCHEMA, "application/x-npz")
        if ((port.payload_schema, port.media_type) != (schema, media)
                or producer is None and (port.kind is not WorkerInputKind.EXTERNAL or edge.producer_task_id is not None)
                or producer is not None and not matches_protected_e3_producer(
                    edge, source_task_id(config.source.root_id, producer), output)):
            raise ValueError("protected E3 PURE worker substitutes the actual producer task/port or typed scientific input")
        if producer is not None:
            _dependency(context, port, config.source.root_id, producer.value, namespace=NAMESPACE)
        if kind:
            records[edge.consumer_input_id] = _read(port, contracts[port.artifact_id], kind)
        else:
            raw_ports[edge.consumer_input_id] = port
    prefix = records["prefix-config"]
    if prefix.phase is not ProtectedE3SourcePhase.PREFIX or replace(config, record_id=prefix.record_id, phase=prefix.phase) != prefix:
        raise ValueError("protected E3 PURE worker changes original PREFIX configuration/source/manifest/specification")
    history, source_manifest, specification = records["history"], records["manifest"], records["specification"]
    source = science._bound_history(history, prefix, source_manifest, specification)
    validate_original_prefix_receipt(history, context.run_id)
    numerical, witness, assessment = (records.get(name) for name in ("numerical", "witness", "assessment"))
    if numerical is not None:
        numerical.validate_source(source, history)
    if witness is not None:
        witness.validate_source(source, history, numerical)
    if assessment is not None:
        assessment.validate_source(source, witness)
    _raw_input(context, ports, history.arrays, source.root_id, "prefix", namespace=NAMESPACE)
    if witness is not None:
        _raw_input(context, ports, witness.arrays, source.root_id, "measure", namespace=NAMESPACE)
    for name, arrays in (("prefix-arrays", history.arrays), ("diagnostic-arrays", witness.arrays if witness else None)):
        if arrays is not None:
            port = raw_ports[name]
            contract = contracts[port.artifact_id]
            if (port.artifact_id != arrays.array_artifact.artifact_id
                    or contract.logical.profile is not ArtifactProfile.MATRIX_ARRAY_NPZ
                    or contract.logical.content_sha256 != arrays.array_artifact.sha256
                    or contract.physical_sha256 != arrays.array_artifact.sha256):
                raise ValueError("protected E3 PURE worker substitutes actual ordinary array publication identity")
    return ProtectedE3PrefixWorkerInputs(config, prefix, source_manifest, specification, history, numerical, witness, assessment,
        raw_ports["prefix-arrays"], raw_ports.get("diagnostic-arrays"), context.output_ports)


class ConfiguredProtectedE3PrefixPureRunner:
    def __init__(self, phase: ProtectedE3SourcePhase, *, manifest: CapabilityManifest):
        prefix_worker_phase(phase)
        self.phase, self.manifest = phase, manifest

    def execute(self, context: TaskContext) -> RunnerResult:
        from .protected_pure_execution import execute_prefix_pure
        return execute_prefix_pure(self, context, decode_inputs=decode_protected_e3_prefix_worker,
            phases=ProtectedE3SourcePhase, science=science)
