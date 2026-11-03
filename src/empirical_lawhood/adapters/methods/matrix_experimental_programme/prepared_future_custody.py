# SPDX-License-Identifier: MPL-2.0
"""Genuine native lifecycle primitives for a prepared development pulse assay.

The complete programme caller must authenticate its frozen handoff and ordinary
dependency receipts before invoking this owner. All numerical science is the
original paired pulse method. Protected entry and applicability are separate.
"""

from dataclasses import dataclass, replace
from hashlib import sha256
from typing import ClassVar

import numpy as np

from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterNativeHistory
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.adapters.methods.matrix_scheduled_history.operation_bindings import _dependency
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseProtocol, branch_census
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import split_parameter_innovations
from empirical_lawhood.adapters.simulators.six_matrix_response.simulation import hermitian_noise
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays, encode_matrix_arrays, matrix_array_members
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES, MatrixArrayMember
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkOutput, NativeSubworkRoster, require_native_completion_receipt
from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork

from . import prepared_prediction_bindings as prediction
from . import prepared_response_science as science
from .preparation_records import MatrixPreparationHistory, MatrixPreparationSource, preparation_identity
from .prepared_forecast import MatrixPreparedMechanicalForecast
from .prepared_point import MatrixPreparedPointDesign, MatrixPreparedPointSeal
from .prepared_prefix import MatrixPreparedCausalPrefix, identity


NAMESPACE = "matrix-prepared-future"
STANDING = "EXPOSED_PREPARED_ASSAY_NATIVE_CUSTODY_NO_PROSPECTIVE_ENTRY_OR_APPLICABILITY_BOUND"


@dataclass(frozen=True, slots=True)
class MatrixPreparedFutureConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-future-config"
    config_id: str
    programme: ObjectIdentity
    source: MatrixPreparationSource
    protocol: ScheduledResponseProtocol
    panels: tuple[science.MatrixPreparedResponsePanel, ...]
    point_design: ObjectIdentity
    frozen_package: ObjectIdentity
    phase: str

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if (type(self.source) is not MatrixPreparationSource or type(self.protocol) is not ScheduledResponseProtocol
                or self.phase not in ("responses", "response-score") or self.config_id != "config." + node_id(self.source, self.phase)
                or self.source.root.root.role is not MatrixProgrammeRole.DEVELOPMENT or self.protocol.public_source != self.source.original
                or self.protocol.horizon_steps != (16, 64, 128) or self.protocol.receiver_count != 48
                or self.point_design.object_schema != MatrixPreparedPointDesign.SCHEMA
                or self.programme.object_schema != "empirical-lawhood/matrix-experimental-programme/prepared-assay-programme"
                or self.frozen_package.object_schema != "empirical-lawhood/matrix-experimental-programme/frozen-consumer-package"
                or type(self.panels) is not tuple or len(self.panels) != 2
                or any(type(row) is not science.MatrixPreparedResponsePanel for row in self.panels)
                or tuple(row.panel_id for row in self.panels) != tuple(sorted({row.panel_id for row in self.panels}))):
            raise ValueError("prepared future configuration changes its exact development source, full assay, frozen predictor or panels")
        self.source.__post_init__()
        self.protocol.__post_init__()
        science.validate_prepared_panels(self.source, self.panels)


@dataclass(frozen=True, slots=True)
class MatrixPreparedFutureArrays(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-future-arrays"
    record_id: str
    source: ObjectIdentity
    array_artifact: ArtifactIdentity
    members: tuple[MatrixArrayMember, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.source.object_schema != MatrixPreparationSource.SCHEMA or type(self.array_artifact) is not ArtifactIdentity
                or self.array_artifact.payload_schema != MATRIX_ARRAY_SCHEMA or self.array_artifact.media_type != "application/x-npz"
                or not 0 < self.array_artifact.size_bytes <= MAXIMUM_MATRIX_ARRAY_BYTES or type(self.members) is not tuple
                or not 1 <= len(self.members) <= 256 or any(type(row) is not MatrixArrayMember or not row.finite_required for row in self.members)
                or tuple(row.name for row in self.members) != tuple(sorted({row.name for row in self.members}))
                or sum(row.size_bytes for row in self.members) > MAXIMUM_MATRIX_ARRAY_BYTES):
            raise ValueError("prepared future arrays change bounded complete finite native geometry")


@dataclass(frozen=True, slots=True)
class MatrixPreparedFutureHistory(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-future-history"
    record_id: str
    source: ObjectIdentity
    preparation: ObjectIdentity
    causal: ObjectIdentity
    point: ObjectIdentity
    mechanical: ObjectIdentity
    protocol: ObjectIdentity
    panels: tuple[ObjectIdentity, ...]
    branch_ids: tuple[str, ...]
    arrays: MatrixPreparedFutureArrays
    native: tuple[MatrixParameterNativeHistory, ...]
    disposition: str
    standing: str = STANDING

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.standing != STANDING or self.source != self.arrays.source or len(self.branch_ids) != 48
                or self.branch_ids != tuple(sorted(set(self.branch_ids))) or len(self.panels) != 2
                or self.disposition not in ("COMPLETED", "NO_ORIGIN", "UNEVALUABLE", "INSTRUMENT_UNRESOLVED")
                or len(self.native) != (1 if self.disposition == "COMPLETED" else 0)
                or any(type(row) is not MatrixParameterNativeHistory for row in self.native)
                or self.preparation.object_schema != MatrixPreparationHistory.SCHEMA or self.causal.object_schema != MatrixPreparedCausalPrefix.SCHEMA
                or self.point.object_schema != MatrixPreparedPointSeal.SCHEMA or self.mechanical.object_schema != MatrixPreparedMechanicalForecast.SCHEMA
                or self.protocol.object_schema != ScheduledResponseProtocol.SCHEMA):
            raise ValueError("prepared future history drops complete branch/custody/nonentry denominators or invents authority")


def node_id(source, phase):
    return NAMESPACE + "." + source.source_id + "." + phase


def stream_id(config, panel, stream):
    if panel not in config.panels or stream not in panel.streams:
        raise ValueError("prepared future stream is outside its exact original panel purpose census")
    if panel.role == "COMMON_NOISE_PANEL":
        return config.source.root.stream_identity(stream)
    return ObjectIdentity.from_record("prepared-future-stream." + panel.independent_group_id + "." + panel.panel_id + "." + stream.purpose, stream)


def check_handoff(config, history, causal, point, mechanical):
    """Exact source/model/cutoff joins; no outcome, fitting or native producer."""
    source, protocol = config.source, config.protocol
    if (type(history) is not MatrixPreparationHistory or type(causal) is not MatrixPreparedCausalPrefix
            or type(point) is not MatrixPreparedPointSeal or type(mechanical) is not MatrixPreparedMechanicalForecast
            or history.source != source.identity or causal.source != source.identity or mechanical.source != source.identity
            or point.feature.source != source.identity or point.feature.prefix != identity(causal)
            or mechanical.causal != identity(causal) or mechanical.original_protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
            or mechanical.arrays.preparation != preparation_identity(history.arrays) or causal.preparation != preparation_identity(history.arrays)
            or point.feature.design != config.point_design or point.package != config.frozen_package
            or point.criterion != protocol.criterion or point.feature.cutoff != source.coordinate.physical_time(source.total_ticks)
            or point.feature.frame_sha256 != causal.frame_sha256 or causal.cutoff_tick != source.total_ticks
            or (point.feature.root_id, point.feature.independent_group_id, point.feature.clock_id) !=
                (source.root.root.root_id, source.root.root.independent_group_id, source.root.root.clock_id)):
        raise ValueError("prepared future changes its actual pre-future source, fixed physical instrument, predictor package or cutoff")
    science._public_context(source, history.arrays, protocol, config.panels)


def authenticate_handoff_receipts(context, config, ports):
    """Use original ordinary receipt custody; no label or Boolean is a seal."""
    source = config.source
    for key, namespace, phase in (("history", prediction.source_owner.NAMESPACE, "history"),
            ("history-arrays", prediction.source_owner.NAMESPACE, "history"),
            ("causal", prediction.NAMESPACE, "project"), ("point", prediction.NAMESPACE, "point"),
            ("mechanical", prediction.NAMESPACE, "mechanical"), ("mechanical-arrays", prediction.NAMESPACE, "mechanical")):
        _dependency(context, ports[key], source.source_id, phase, namespace=namespace,
            access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility=VisibilityCeiling.DEVELOPMENT_ONLY)


def initial_native_work(context, config, history, causal, point, mechanical, expected_parent):
    check_handoff(config, history, causal, point, mechanical)
    source = config.source
    if (expected_parent.run_id, expected_parent.task_id, expected_parent.attempt_id, expected_parent.input_materialization_ids,
            expected_parent.implementation_commit) != (context.run_id, context.task_id, context.attempt_id,
            context.input_materialization_ids, source.provenance.observed_git_head):
        raise ValueError("prepared future changes actual issued parent contact/source implementation")
    sources = tuple(sorted((source.identity, source.provenance.identity, preparation_identity(history), identity(causal), identity(point), identity(mechanical),
        ObjectIdentity.from_record(config.protocol.protocol_id, config.protocol)), key=lambda row: row.object_id))
    streams = tuple(sorted((stream_id(config, panel, row) for panel in config.panels for row in panel.streams), key=lambda row: row.object_id))
    definition = NativeSubworkDefinition("responses." + source.source_id, NAMESPACE + ".paired-pulse.v1", expected_parent,
        ObjectIdentity.from_record(config.config_id, config), sources, source.provenance.code_sources_sha256,
        source.provenance.dependency_lock_sha256, context.input_materialization_ids, streams,
        (NativeSubworkOutput("arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz"),))
    roster = NativeSubworkRoster("selected.native-subwork", expected_parent, (definition.identity,))
    return PreparedNativeWork(expected_parent, (source.root.root.independent_group_id,), ("responses." + source.source_id,), (definition,), (roster,))


def prepare_native_future(context, config, history, causal, point, mechanical, *, allocation, handoff_ports, expected_parent):
    if config.phase != "responses":
        raise ValueError("prepared native future requires its actual responses phase")
    history.validate_source(config.source, allocation)
    authenticate_handoff_receipts(context, config, handoff_ports)
    return initial_native_work(context, config, history, causal, point, mechanical, expected_parent)


def acquire_future(config, history, initial_raw, preparation_raw, mechanical, frozen_raw, *, on_step=None, prepared_arrays=None):
    """Entered only by the owning actual native lifecycle after BEGIN/contact.

    Preparation consumed only its two preparation streams. These original
    autonomous streams are untouched and start at the actual restored cutoff;
    this does not pretend to be an old scheduled generator checkpoint.
    """
    source, innovations = config.source, {}
    for panel in config.panels:
        selected = {row.purpose: row for row in panel.streams}
        coarse = np.random.Generator(np.random.PCG64DXSM(selected["autonomous-coarse-driver"].effective_seed))
        bridge = np.random.Generator(np.random.PCG64DXSM(selected["autonomous-fine-bridge"].effective_seed))
        primary, fine, coupling = [], [], []
        for _ in range(config.protocol.horizon_steps[-1]):
            noise, pair = hermitian_noise(rng=coarse, q=2), hermitian_noise(rng=bridge, q=2)
            primary.append(noise)
            coupling.append(pair)
            fine.extend(split_parameter_innovations(source.coordinate, noise, pair))
        innovations[panel.panel_id] = {"primary": np.asarray(primary, dtype="<c16"), "fine": np.asarray(fine, dtype="<c16"),
            "bridge": np.asarray(coupling, dtype="<c16")}
    if prepared_arrays is not None:
        prefix, frozen = prepared_arrays
        return science._propagate_prepared_response_arrays(source, config.protocol, config.panels, innovations,
            prefix=prefix, frozen=frozen, on_step=on_step)
    return science.propagate_prepared_responses(source, initial_raw, history.arrays, preparation_raw, config.protocol,
        config.panels, mechanical.arrays, frozen_raw, innovations, on_step=on_step)


def array_product(source, arrays, *, artifact_id, raw=None):
    if raw is None:
        result, members = encode_matrix_arrays(arrays)
    else:
        result, members = raw, matrix_array_members(arrays)
    operand = _array_operand(source, result, members, artifact_id=artifact_id)
    decoded = decode_matrix_arrays(result, operand)
    if any(not np.array_equal(value, decoded[name]) for name, value in arrays.items()):
        raise ValueError("prepared future retained bytes change original complete native values")
    return result, operand


def _array_operand(source, raw, members, *, artifact_id):
    """Metadata for exact native bytes whose complete values were already checked."""
    return MatrixPreparedFutureArrays("arrays." + artifact_id, source.identity, ArtifactIdentity(artifact_id, "prepared-pulse-native", MATRIX_ARRAY_SCHEMA,
        sha256(raw).hexdigest(), "application/x-npz", len(raw)), members)


def execute_native_future(context, config, history, causal, point, mechanical, initial_raw, preparation_raw, frozen_raw, native_subwork, *, allocation, handoff_ports, progress=None):
    """One authenticated child, no automatic replay after unknown contact."""
    source = config.source
    work = prepare_native_future(context, config, history, causal, point, mechanical, allocation=allocation,
        handoff_ports=handoff_ports, expected_parent=native_subwork.parent_contact)
    from .prepared_native_body import _execute_future_native

    output = next(row for row in context.output_ports if row.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
    result = _execute_future_native(config, history, causal, mechanical,
        initial_raw, preparation_raw, frozen_raw, native_subwork, work, progress=progress,
        array_artifact_id=output.logical_artifact_id)
    _, _, native, disposition = result
    from .prepared_native_body import _close_future_arrays
    raw, operand = _close_future_arrays(result, source, artifact_id=output.logical_artifact_id)
    product = MatrixPreparedFutureHistory("responses." + source.source_id, source.identity, preparation_identity(history), identity(causal), identity(point),
        identity(mechanical), ObjectIdentity.from_record(config.protocol.protocol_id, config.protocol), tuple(row.identity for row in config.panels),
        tuple(row[0] for row in branch_census(config.protocol, config.panels)), operand, native, disposition)
    validate_future_history(config, history, causal, point, mechanical, product)
    return raw, product


def validate_future_history(config, history, causal, point, mechanical, product):
    """Authenticate complete original child custody, not a supplied completion flag."""
    check_handoff(config, history, causal, point, mechanical)
    source, protocol = config.source, config.protocol
    if (type(product) is not MatrixPreparedFutureHistory or product.source != source.identity
            or product.preparation != preparation_identity(history) or product.causal != identity(causal)
            or product.point != identity(point) or product.mechanical != identity(mechanical)
            or product.protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
            or product.panels != tuple(row.identity for row in config.panels)
            or product.branch_ids != tuple(row[0] for row in branch_census(protocol, config.panels))):
        raise ValueError("prepared future changes actual source, pre-future seals, panels or complete branches")
    if not product.native:
        expected = "NO_ORIGIN" if causal.disposition == "NO_ORIGIN" else "INSTRUMENT_UNRESOLVED" if mechanical.disposition == "INSTRUMENT_UNRESOLVED" else "UNEVALUABLE"
        if (causal.disposition == mechanical.disposition == "AVAILABLE" or product.disposition != expected
                or tuple((row.name, row.dtype, row.shape) for row in product.arrays.members) != (("unentered_branches", "<i8", (48,)),)):
            raise ValueError("prepared future invents known nonentry or loses complete unentered branch marker")
        return
    native, = product.native
    definition, completion, receipt = native.definition, native.completion, native.receipt
    response_config = replace(config, phase="responses", config_id="config." + node_id(source, "responses"))
    expected_sources = tuple(sorted((source.identity, source.provenance.identity, preparation_identity(history), identity(causal), identity(point),
        identity(mechanical), ObjectIdentity.from_record(protocol.protocol_id, protocol)), key=lambda row: row.object_id))
    streams = tuple(sorted((stream_id(config, panel, row) for panel in config.panels for row in panel.streams), key=lambda row: row.object_id))
    consumed = tuple(sorted((stream_id(config, panel, row) for panel in config.panels for row in panel.streams
        if row.purpose.startswith("autonomous")), key=lambda row: row.object_id))
    task = "native-subwork." + sha256((definition.parent_contact.task_id + ":" + definition.subwork_id).encode()).hexdigest()
    attempt = definition.parent_contact.run_id + "." + task + ".attempt-001"
    expected_ids = {task + ".output.arrays", task + ".completion"}
    if (causal.disposition != "AVAILABLE" or mechanical.disposition != "AVAILABLE"
            or definition.subwork_id != "responses." + source.source_id or definition.operation_id != NAMESPACE + ".paired-pulse.v1"
            or definition.configuration != ObjectIdentity.from_record(response_config.config_id, response_config)
            or definition.parent_contact.task_id != node_id(source, "responses")
            or definition.parent_contact.implementation_commit != source.provenance.observed_git_head
            or definition.sources != expected_sources or definition.streams != streams or completion.consumed_streams != consumed
            or completion.unconsumed_streams != tuple(row for row in streams if row not in consumed)
            or definition.code_sources_sha256 != source.provenance.code_sources_sha256 or definition.dependency_lock_sha256 != source.provenance.dependency_lock_sha256
            or (receipt.run_id, receipt.task_id, receipt.attempt_id, receipt.receipt_id) != (definition.parent_contact.run_id, task, attempt, "receipt." + attempt)
            or len(receipt.output_logical_artifacts) != 2 or len(receipt.output_materializations) != 2
            or {row.logical_artifact_id for row in receipt.output_logical_artifacts} != expected_ids
            or {row.logical_artifact_id for row in receipt.output_materializations} != expected_ids):
        raise ValueError("prepared future substitutes actual native configuration, source origin, purpose census or original child receipt")
    logical, = tuple(row for row in receipt.output_logical_artifacts if row.payload_schema == MATRIX_ARRAY_SCHEMA)
    require_native_completion_receipt(completion, receipt, outcome_access=logical.outcome_access,
        visibility_ceiling=logical.visibility_ceiling)
    physical, = tuple(row for row in receipt.output_materializations if row.logical_artifact_id == logical.logical_artifact_id)
    artifact = product.arrays.array_artifact
    if (logical.profile is not ArtifactProfile.MATRIX_ARRAY_NPZ or logical.media_type != artifact.media_type
            or logical.content_sha256 != artifact.sha256 or physical.physical_sha256 != artifact.sha256 or physical.size_bytes != artifact.size_bytes):
        raise ValueError("prepared future changes exact original receipted raw array bytes")


def assess_future(config, history, causal, point, mechanical, product, initial_raw, preparation_raw, frozen_raw, future_raw, *, record_id, frozen_input=None):
    validate_future_history(config, history, causal, point, mechanical, product)
    arrays = decode_matrix_arrays(future_raw, product.arrays)
    if product.disposition != "COMPLETED":
        if not np.array_equal(arrays["unentered_branches"], np.arange(48, dtype="<i8")):
            raise ValueError("prepared future changes its actual complete unentered branch marker")
        return science.unentered_prepared_responses(config.source, history.arrays, config.protocol, config.panels,
            record_id=record_id, disposition=product.disposition)
    return science.assess_prepared_responses(config.source, initial_raw, history.arrays, preparation_raw, config.protocol,
        config.panels, mechanical.arrays, frozen_raw, arrays, record_id=record_id, frozen_input=frozen_input)
