# SPDX-License-Identifier: MPL-2.0
"""Selected development opportunity futures through the original native child body.

No protected context or old point record is coerced into this development route. The
owning prepared worker must authenticate issued inputs and dependency receipts
before calling these numerical/native lifecycle primitives.
"""

from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

import numpy as np

from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterNativeHistory
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseProtocol, branch_census
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkOutput, NativeSubworkRoster, require_native_completion_receipt
from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork

from . import prepared_response_science as science
from .preparation_records import MatrixPreparationHistory, MatrixPreparationSource, preparation_identity
from .prepared_forecast import MatrixPreparedMechanicalForecast
from .prepared_future_custody import MatrixPreparedFutureArrays, array_product as array_product, stream_id
from .prepared_prefix import MatrixPreparedCausalPrefix, identity
from .selected_package import selected_frozen_package_types
from .selected_point import MatrixSelectedPointForecast
from .selected_future import check_handoff as check_handoff
from .selected_public import MatrixSelectedPointPayload


NAMESPACE = "matrix-selected-opportunity"
PROGRAMME_SCHEMA = "empirical-lawhood/matrix-experimental-programme/selected-opportunity-programme"
STANDING = "SELECTED_OPPORTUNITY_NATIVE_CUSTODY_NO_PROTECTED_ENTRY_OR_APPLICABILITY_WARRANT"


def node_id(source, phase):
    return NAMESPACE + "." + source.source_id + "." + phase


@dataclass(frozen=True, slots=True)
class MatrixSelectedOpportunityFutureConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-opportunity-future-config"
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
                or self.source.root.root.role is not MatrixProgrammeRole.DEVELOPMENT
                or self.protocol.public_source != self.source.original or self.protocol.horizon_steps != (16, 64, 128)
                or self.protocol.receiver_count != 48 or self.point_design.object_schema != MatrixSelectedPointPayload.SCHEMA
                or self.programme.object_schema != "empirical-lawhood/matrix-experimental-programme/selected-opportunity-public-programme"
                or (self.frozen_package.object_schema, self.frozen_package.object_version) not in tuple((kind.SCHEMA, kind.VERSION) for kind in selected_frozen_package_types())):
            raise ValueError("selected future changes its actual development source, complete assay or selected predictor")
        self.source.__post_init__()
        self.protocol.__post_init__()
        science.validate_prepared_panels(self.source, self.panels)


@dataclass(frozen=True, slots=True)
class MatrixSelectedOpportunityFutureConfigV2(MatrixSelectedOpportunityFutureConfig):
    """Direct authenticated provenance and actually used future RNG operands."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-opportunity-future-config-v2"

    def __post_init__(self):
        MatrixSelectedOpportunityFutureConfig.__post_init__(self)
        if self.phase != "responses":
            raise ValueError("direct native future config selects only response acquisition")


@dataclass(frozen=True, slots=True)
class MatrixSelectedOpportunityFutureHistory(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-opportunity-future-history"
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
        if (self.standing != STANDING or type(self.arrays) is not MatrixPreparedFutureArrays or self.source != self.arrays.source
                or self.source.object_schema != MatrixPreparationSource.SCHEMA or len(self.branch_ids) != 48
                or self.branch_ids != tuple(sorted(set(self.branch_ids))) or len(self.panels) != 2
                or self.disposition not in ("COMPLETED", "NO_ORIGIN", "UNEVALUABLE", "INSTRUMENT_UNRESOLVED")
                or len(self.native) != (1 if self.disposition == "COMPLETED" else 0)
                or any(type(row) is not MatrixParameterNativeHistory for row in self.native)
                or self.preparation.object_schema != MatrixPreparationHistory.SCHEMA
                or self.causal.object_schema != MatrixPreparedCausalPrefix.SCHEMA
                or self.point.object_schema != MatrixSelectedPointForecast.SCHEMA
                or self.mechanical.object_schema != MatrixPreparedMechanicalForecast.SCHEMA
                or self.protocol.object_schema != ScheduledResponseProtocol.SCHEMA):
            raise ValueError("selected future loses actual selected seals, full branch census or known native disposition")


def initial_native_work(context, config, history, causal, point, mechanical, expected_parent):
    if type(config) is not MatrixSelectedOpportunityFutureConfigV2:
        raise TypeError("selected native future requires its current direct-input contract")
    check_handoff(config, history, causal, point, mechanical)
    source = config.source
    if (expected_parent.run_id, expected_parent.task_id, expected_parent.attempt_id, expected_parent.input_materialization_ids,
            expected_parent.implementation_commit) != (context.run_id, context.task_id, context.attempt_id,
            context.input_materialization_ids, source.provenance.observed_git_head):
        raise ValueError("selected future changes its actual issued native parent/source identity")
    from .preparation_bindings import native_input_records
    sources = tuple(sorted((source.identity, source.provenance.identity, preparation_identity(history),
        identity(causal), identity(point), identity(mechanical), ObjectIdentity.from_record(config.protocol.protocol_id, config.protocol)),
        key=lambda row: row.object_id))
    streams = tuple(sorted((pin for name, pin, _ in native_input_records(source, panels=config.panels)
        if name.startswith("native-stream.")), key=lambda row: row.object_id))
    definition = NativeSubworkDefinition("responses." + source.source_id, NAMESPACE + ".paired-pulse.direct-inputs.v2", expected_parent,
        ObjectIdentity.from_record(config.config_id, config), sources, source.provenance.code_sources_sha256,
        source.provenance.dependency_lock_sha256, context.input_materialization_ids, streams,
        (NativeSubworkOutput("arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz"),))
    roster = NativeSubworkRoster("selected.native-subwork", expected_parent, (definition.identity,))
    return PreparedNativeWork(expected_parent, (source.root.root.independent_group_id,), ("responses." + source.source_id,), (definition,), (roster,))


def validate_future_history(config, history, causal, point, mechanical, product):
    check_handoff(config, history, causal, point, mechanical)
    source, protocol = config.source, config.protocol
    if (type(product) is not MatrixSelectedOpportunityFutureHistory or product.source != source.identity
            or product.preparation != preparation_identity(history) or product.causal != identity(causal)
            or product.point != identity(point) or product.mechanical != identity(mechanical)
            or product.protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
            or product.panels != tuple(row.identity for row in config.panels)
            or product.branch_ids != tuple(row[0] for row in branch_census(protocol, config.panels))):
        raise ValueError("selected future changes actual source, selected point seals, panels or complete branches")
    product.__post_init__()
    if not product.native:
        expected = "NO_ORIGIN" if causal.disposition == "NO_ORIGIN" else "INSTRUMENT_UNRESOLVED" if mechanical.disposition == "INSTRUMENT_UNRESOLVED" else "UNEVALUABLE"
        if (causal.disposition == mechanical.disposition == "AVAILABLE" or product.disposition != expected
                or tuple((row.name, row.dtype, row.shape) for row in product.arrays.members) != (("unentered_branches", "<i8", (48,)),)):
            raise ValueError("selected future invents nonentry or thins the full unentered branch marker")
        return
    native, = product.native
    definition, completion, receipt = native.definition, native.completion, native.receipt
    from dataclasses import fields
    if definition.operation_id != NAMESPACE + ".paired-pulse.direct-inputs.v2":
        raise ValueError("selected future uses an unsupported native acquisition contract")
    response_config = MatrixSelectedOpportunityFutureConfigV2(**{field.name: getattr(config, field.name) for field in fields(MatrixSelectedOpportunityFutureConfig)
        if field.name not in ("phase", "config_id")}, phase="responses", config_id="config." + node_id(source, "responses"))
    from .preparation_bindings import native_input_records
    expected_sources = tuple(sorted((source.identity, source.provenance.identity, preparation_identity(history),
        identity(causal), identity(point), identity(mechanical), ObjectIdentity.from_record(protocol.protocol_id, protocol)),
        key=lambda row: row.object_id))
    streams = tuple(sorted((pin for name, pin, _ in native_input_records(source, panels=config.panels)
        if name.startswith("native-stream.")), key=lambda row: row.object_id))
    consumed = tuple(sorted((stream_id(config, panel, row) for panel in config.panels for row in panel.streams
        if row.purpose.startswith("autonomous")), key=lambda row: row.object_id))
    task = "native-subwork." + sha256((definition.parent_contact.task_id + ":" + definition.subwork_id).encode()).hexdigest()
    attempt = definition.parent_contact.run_id + "." + task + ".attempt-001"
    expected_ids = {task + ".output.arrays", task + ".completion"}
    if (causal.disposition != "AVAILABLE" or mechanical.disposition != "AVAILABLE"
            or definition.subwork_id != "responses." + source.source_id
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
        raise ValueError("selected future substitutes native configuration, source origin, purpose census or actual child receipt")
    logical, = tuple(row for row in receipt.output_logical_artifacts if row.payload_schema == MATRIX_ARRAY_SCHEMA)
    require_native_completion_receipt(completion, receipt, outcome_access=logical.outcome_access,
        visibility_ceiling=logical.visibility_ceiling)
    physical, = tuple(row for row in receipt.output_materializations if row.logical_artifact_id == logical.logical_artifact_id)
    artifact = product.arrays.array_artifact
    if (logical.profile is not ArtifactProfile.MATRIX_ARRAY_NPZ or logical.media_type != artifact.media_type
            or logical.content_sha256 != artifact.sha256 or physical.physical_sha256 != artifact.sha256 or physical.size_bytes != artifact.size_bytes):
        raise ValueError("selected future changes exact original receipted array bytes")


def execute_native_future(context, config, history, causal, point, mechanical, initial_raw, preparation_raw, frozen_raw,
        native_subwork, *, allocation, progress=None, prepared_arrays=None):
    history.validate_source(config.source, allocation)
    work = initial_native_work(context, config, history, causal, point, mechanical, native_subwork.parent_contact)
    from .prepared_native_body import _execute_future_native, _close_future_arrays
    output = next(row for row in context.output_ports if row.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
    result = _execute_future_native(config, history, causal, mechanical,
        initial_raw, preparation_raw, frozen_raw, native_subwork, work,
        **({"progress": progress} if progress is not None else {}),
        **({"prepared_arrays": prepared_arrays} if prepared_arrays is not None else {}),
        array_artifact_id=output.logical_artifact_id)
    _, _, native, disposition = result
    raw, operand = _close_future_arrays(result, config.source, artifact_id=output.logical_artifact_id)
    product = MatrixSelectedOpportunityFutureHistory("responses." + config.source.source_id, config.source.identity, preparation_identity(history), identity(causal),
        identity(point), identity(mechanical), ObjectIdentity.from_record(config.protocol.protocol_id, config.protocol),
        tuple(row.identity for row in config.panels), tuple(row[0] for row in branch_census(config.protocol, config.panels)), operand, native, disposition)
    validate_future_history(config, history, causal, point, mechanical, product)
    return raw, product


def assess_future(config, history, causal, point, mechanical, product, initial_raw, preparation_raw, frozen_raw, future_raw, *, record_id, frozen_input=None):
    validate_future_history(config, history, causal, point, mechanical, product)
    arrays = decode_matrix_arrays(future_raw, product.arrays)
    if product.disposition != "COMPLETED":
        if not np.array_equal(arrays["unentered_branches"], np.arange(48, dtype="<i8")):
            raise ValueError("selected future changes the complete actual unentered branch marker")
        return science.unentered_prepared_responses(config.source, history.arrays, config.protocol, config.panels,
            record_id=record_id, disposition=product.disposition)
    return science.assess_prepared_responses(config.source, initial_raw, history.arrays, preparation_raw, config.protocol,
        config.panels, mechanical.arrays, frozen_raw, arrays, record_id=record_id, frozen_input=frozen_input)
