# SPDX-License-Identifier: MPL-2.0
"""Current E3 prefix operands and PURE preparation for the existing lifecycle.

Every native source and stream has direct authenticated input bytes. The
compact descriptor and shared manifest reconstruct the unchanged scientific
subject without publishing a full allocation inside every root's source.
Preparation does not enter, recover, qualify or authorize native work.
"""

from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledSource
from dataclasses import dataclass
from hashlib import sha256

from empirical_lawhood.adapters.methods.matrix_history_analysis.records import MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.compact_records import (
    compact_identity,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledCheckpoint
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityManifest
from empirical_lawhood.runtime.execution import TaskContext, WorkerOutputPort
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork
from .protected_prefix_work import prepare_prefix_native_work

from .configured_protected_specification import ConfiguredProtectedE3Specification as MatrixResponseErrorSpecification
from .configured_protected_prefix_records import ConfiguredProtectedE3PrefixHistory, protected_prefix_native_contract
from .configured_protected_source_records import (
    NAMESPACE, ProtectedE3NativeSourceManifest, ConfiguredProtectedE3SourceConfig, identity,
)


@dataclass(frozen=True, slots=True)
class ProtectedE3PrefixOperands:
    """Already decoded original operands; no custody or execution authority."""

    config: ConfiguredProtectedE3SourceConfig
    manifest: ProtectedE3NativeSourceManifest
    specification: MatrixResponseErrorSpecification
    source: ScheduledSource


def _outputs(context):
    expected = {
        (ConfiguredProtectedE3PrefixHistory.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json"),
        (MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz"),
        (ScheduledCheckpoint.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json"),
    }
    if (any(type(p) is not WorkerOutputPort for p in context.output_ports)
            or len(context.output_ports) != len(expected)
            or {(p.payload_schema, p.profile, p.media_type) for p in context.output_ports} != expected
            or any(p.logical_artifact_id is None for p in context.output_ports)
            or len({p.logical_artifact_id for p in context.output_ports}) != len(expected)):
        raise ValueError("protected E3 prefix changes its complete ordinary output contract")


def decode_protected_e3_prefix_inputs(context: TaskContext, capability: CapabilityManifest) -> ProtectedE3PrefixOperands:
    """Read the exact direct operand census through the existing worker ports.

    The engine supplies independent cursors during PURE preparation. Its first
    callback precedes construction of the prepared contract; a later bound
    callback and actual execution must preserve that same work projection.
    """
    if type(context) is not TaskContext or type(capability) is not CapabilityManifest:
        raise TypeError("protected E3 prefix requires its exact worker context and installed manifest")
    context.__post_init__()
    capability.__post_init__()
    if (capability.capability_key != NAMESPACE + ".prefix"
            or context.permissions != capability.permissions
            or context.outcome_access is not OutcomeAccess.OUTCOME_BLIND
            or not capability.resource_ceiling.contains(context.resource_budget)
            or (context.config.config_schema, context.config.config_schema_sha256) !=
               (capability.config_schema, capability.config_schema_sha256)):
        raise ValueError("protected E3 prefix changes its declared worker scope")
    _outputs(context)
    kinds = {kind.SCHEMA: kind for kind in (ConfiguredProtectedE3SourceConfig, ProtectedE3NativeSourceManifest,
        MatrixResponseErrorSpecification, ScheduledSource, MatrixParameterCoordinate,
        NumericalProducingProvenance)}
    records, ports, streams, raw_hashes = {}, {}, [], {}
    prepared = context.prepared_invocation
    if prepared is not None and (prepared.manifest != capability or not prepared.native_effect):
        raise ValueError("protected E3 prefix changes its prepared capability or native effect selection")
    if prepared is not None:
        prepared.validate_context(context)
    for port in context.input_ports:
        if (port.media_type != "application/json" or port.outcome_access is not OutcomeAccess.OUTCOME_BLIND
                or port.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE):
            raise ValueError("protected E3 prefix changes a direct input's original access or media")
        if port.payload_schema not in {*kinds, MatrixHistorySeed.SCHEMA}:
            raise ValueError("protected E3 prefix receives an undeclared or full-roster source input")
        raw = port.read()
        if len(raw) != port.size_bytes:
            raise ValueError("protected E3 prefix direct input changes its declared exact size")
        record = decode_canonical_bytes(raw, kinds.get(port.payload_schema, MatrixHistorySeed), maximum_bytes=None)
        raw_hashes[port.artifact_id] = sha256(raw).hexdigest()
        if prepared is not None:
            selected = next(row for row in prepared.inputs if row.artifact_id == port.artifact_id)
            if (selected.logical.profile is not ArtifactProfile.CANONICAL_JSON
                    or selected.logical.content_sha256 != raw_hashes[port.artifact_id]
                    or selected.physical_sha256 != raw_hashes[port.artifact_id]):
                raise ValueError("protected E3 prefix direct input changes its prepared canonical bytes or codec")
        if port.payload_schema == MatrixHistorySeed.SCHEMA:
            streams.append((port, record))
        elif port.payload_schema in records:
            raise ValueError("protected E3 prefix duplicates a direct scientific operand")
        else:
            records[port.payload_schema], ports[port.payload_schema] = record, port
    if set(records) != set(kinds) or len(streams) != 4:
        raise ValueError("protected E3 prefix omits its complete direct source or four-purpose stream inputs")
    config = records[ConfiguredProtectedE3SourceConfig.SCHEMA]
    manifest = records[ProtectedE3NativeSourceManifest.SCHEMA]
    specification = records[MatrixResponseErrorSpecification.SCHEMA]
    source, configuration, task_id, _, _, _ = protected_prefix_native_contract(
        config, manifest, specification=specification)
    if ((context.config.config_id, context.config.config_schema, context.config.content_sha256,
            context.config.artifact_id, context.task_id) !=
            (config.record_id, config.SCHEMA, config.fingerprint(), ports[config.SCHEMA].artifact_id, task_id)):
        raise ValueError("protected E3 prefix substitutes its actual task or configuration")
    if (records[ScheduledSource.SCHEMA] != config.source
            or records[MatrixParameterCoordinate.SCHEMA] != source.coordinate
            or records[NumericalProducingProvenance.SCHEMA] != source.provenance
            or {(port.artifact_id, stream) for port, stream in streams} !=
               {(source.root.stream_identity(stream).object_id, stream) for stream in source.root.streams}):
        raise ValueError("protected E3 prefix substitutes a direct original source, coordinate, provenance or stream")
    if prepared is not None:
        expected_identities = {
            ports[config.SCHEMA].artifact_id: configuration,
            ports[manifest.SCHEMA].artifact_id: identity(manifest),
            ports[specification.SCHEMA].artifact_id: specification.identity,
            ports[ScheduledSource.SCHEMA].artifact_id: compact_identity(config.source),
            ports[MatrixParameterCoordinate.SCHEMA].artifact_id: coordinate_identity(source.coordinate),
            ports[NumericalProducingProvenance.SCHEMA].artifact_id: source.provenance.identity,
            **{port.artifact_id: source.root.stream_identity(stream) for port, stream in streams},
        }
        for row in prepared.inputs:
            scientific = expected_identities[row.artifact_id]
            if (scientific.object_fingerprint != row.logical.content_sha256
                    or row.scientific_identity is not None and row.scientific_identity != scientific):
                raise ValueError("protected E3 prefix substitutes a prepared scientific identity")
    return ProtectedE3PrefixOperands(config, manifest, specification, source)


def prepare_protected_e3_prefix_work(*, context: TaskContext, expected_parent: NativeEffectContact,
        capability: CapabilityManifest) -> PreparedNativeWork:
    """Derive one original prefix scope before any freeze, BEGIN or contact."""
    operands = decode_protected_e3_prefix_inputs(context, capability)
    return _prefix_native_work(operands, context=context, expected_parent=expected_parent)


def _prefix_native_work(operands: ProtectedE3PrefixOperands, *, context: TaskContext,
        expected_parent: NativeEffectContact) -> PreparedNativeWork:
    return prepare_prefix_native_work(operands, context=context, expected_parent=expected_parent,
        native_contract=protected_prefix_native_contract)
