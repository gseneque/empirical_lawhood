# SPDX-License-Identifier: MPL-2.0
"""Owning ordinary ports for complete prepared pulse futures and cold readout."""

from dataclasses import replace
from functools import partial

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.adapters.methods.matrix_scheduled_history.operation_bindings import _dependency
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledAllocation
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseProtocol
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.infrastructure.matrix_array_io import DecodedMatrixArrayInput
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_provider import RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks

from . import preparation_science, prepared_forecast, prepared_future_custody as custody, prepared_prediction_bindings as prediction
from .preparation_records import MatrixPreparationHistory, MatrixPreparationSource
from .prepared_point import MatrixPreparedPointSeal, MatrixPreparedPublicSource
from .prepared_prefix import MatrixPreparedCausalPrefix
from .prepared_response_science import MatrixPreparedResponseReadout


BASE_INPUTS = ("source", "allocation", "initial-state", "protocol", "history", "history-arrays", "causal", "point", "mechanical", "mechanical-arrays")
INPUTS = {"responses": BASE_INPUTS, "response-score": (*BASE_INPUTS, "causal-arrays", "templates", "responses", "response-arrays")}
RECORDS = {"source": MatrixPreparationSource, "allocation": ScheduledAllocation, "protocol": ScheduledResponseProtocol,
    "history": MatrixPreparationHistory, "causal": MatrixPreparedCausalPrefix, "point": MatrixPreparedPointSeal,
    "mechanical": prepared_forecast.MatrixPreparedMechanicalForecast, "responses": custody.MatrixPreparedFutureHistory}


def units(config):
    return config.source.root.root.independent_group_id,


def slots(config):
    return "responses." + config.source.source_id,


def digests(config):
    return tuple(sorted({config.programme.object_fingerprint, config.source.fingerprint(), config.protocol.fingerprint()}))


def _decode(context, phase):
    kinds = {custody.MatrixPreparedFutureConfig.SCHEMA: custody.MatrixPreparedFutureConfig,
        **{RECORDS[name].SCHEMA: RECORDS[name] for name in INPUTS[phase] if name in RECORDS}}
    records, ports, raw_ports = {}, {}, {}
    for port in context.input_ports:
        if port.payload_schema in kinds and port.payload_schema not in records:
            records[port.payload_schema] = decode_canonical_bytes(port.read(), kinds[port.payload_schema], maximum_bytes=port.size_bytes)
            ports[port.payload_schema] = port
        elif port.payload_schema == MATRIX_ARRAY_SCHEMA and port.artifact_id not in raw_ports:
            raw_ports[port.artifact_id] = port
        else:
            raise ValueError("prepared future worker receives an extra or repeated exact input")
    if set(records) != set(kinds):
        raise ValueError("prepared future worker lacks its complete original typed scientific record census")
    config = records.pop(custody.MatrixPreparedFutureConfig.SCHEMA)
    by_name = {name: records[kind.SCHEMA] for name, kind in RECORDS.items() if name in INPUTS[phase]}
    bound = {name: ports[kind.SCHEMA] for name, kind in RECORDS.items() if name in INPUTS[phase]}
    source = config.source
    if (config.phase != phase or context.task_id != custody.node_id(source, phase)
            or context.config.config_id != config.config_id or context.config.config_schema != config.SCHEMA
            or context.config.content_sha256 != config.fingerprint() or context.resource_budget != prediction.source_owner.BUDGET
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.permissions != prediction.source_owner.operation_declarations()[0].permissions
            or by_name["source"] != source or by_name["protocol"] != config.protocol):
        raise ValueError("prepared future worker changes its exact issued configuration/resources/access/source/protocol")
    history, causal, point, mechanical = (by_name[name] for name in ("history", "causal", "point", "mechanical"))
    history.validate_source(source, by_name["allocation"])
    custody.check_handoff(config, history, causal, point, mechanical)
    expected = {"initial-state": source.initial.array_artifact, "history-arrays": history.arrays.array_artifact,
        "mechanical-arrays": mechanical.arrays.array_artifact}
    if phase == "response-score":
        expected.update({"causal-arrays": causal.arrays.array_artifact, "templates": config.protocol.templates.array_artifact,
            "response-arrays": by_name["responses"].arrays.array_artifact})
    for name, artifact in expected.items():
        matches = tuple(port for port in raw_ports.values() if (port.artifact_id, port.payload_schema, port.media_type, port.size_bytes) ==
            (artifact.artifact_id, artifact.payload_schema, artifact.media_type, artifact.size_bytes))
        if len(matches) != 1:
            raise ValueError("prepared future worker substitutes exact original array identity/size/schema")
        port, = matches
        bound[name] = port
        del raw_ports[port.artifact_id]
    if raw_ports or len(context.input_ports) != 1 + len(INPUTS[phase]):
        raise ValueError("prepared future worker changes its complete original record/array input census")
    custody.authenticate_handoff_receipts(context, config, bound)
    if phase == "response-score":
        for name in ("responses", "response-arrays"):
            _dependency(context, bound[name], source.source_id, "responses", namespace=custody.NAMESPACE,
                access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility=VisibilityCeiling.DEVELOPMENT_ONLY)
    return config, by_name, bound


def prepare_native_work(*, runner, context, expected_parent):
    if type(runner) is not MatrixPreparedFutureNativeRunner:
        raise ValueError("prepared future work requires its actual owning native runner")
    config, records, ports = _decode(context, "responses")
    preparation_science.initial_state(config.source.initial, ports["initial-state"].read())
    return custody.prepare_native_future(context, config, *(records[name] for name in ("history", "causal", "point", "mechanical")),
        allocation=records["allocation"], handoff_ports=ports, expected_parent=expected_parent)


def _outputs(context, product, raw=None):
    payloads = {context.task_id + ".product": product.canonical_bytes()}
    if raw is not None:
        payloads[context.task_id + ".arrays"] = raw
    if set(payloads) != {row.output_id for row in context.output_ports}:
        raise ValueError("prepared future worker changes exact compiler-derived output census")
    return RunnerResult(tuple(TaskOutputPayload(key, value) for key, value in sorted(payloads.items())),
        (ReceiptCheck("complete-prepared-paired-future-custody-and-original-independent-readout", True, ()),))


class MatrixPreparedFutureNativeRunner:
    def __init__(self, *, manifest):
        self.manifest = manifest

    def execute(self, context):
        raise ValueError("prepared future acquisition requires its actual selected native lifecycle authority")

    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        try:
            config, records, ports = _decode(context, "responses")
            raw, product = custody.execute_native_future(context, config, *(records[name] for name in ("history", "causal", "point", "mechanical")),
                *(ports[name].read() for name in ("initial-state", "history-arrays", "mechanical-arrays")), native_subwork,
                allocation=records["allocation"], handoff_ports=ports, progress=progress)
            return _outputs(context, product, raw)
        finally:
            for port in context.input_ports:
                port.close()


class MatrixPreparedFutureAssessor:
    def __init__(self, *, manifest):
        self.manifest = manifest

    def execute(self, context):
        try:
            config, records, ports = _decode(context, "response-score")
            mechanical = records["mechanical"]
            frozen_raw = ports["mechanical-arrays"].read()
            frozen_input = DecodedMatrixArrayInput(frozen_raw, mechanical.arrays)
            # The independent physical reproof occurs only in this scientific
            # worker. Preparation/instance authentication never enters it.
            checked_raw, checked = prepared_forecast.forecast_public(MatrixPreparedPublicSource.from_source(config.source), config.protocol,
                records["causal"], ports["causal-arrays"].read(), ports["templates"].read(),
                artifact_id=mechanical.arrays.array_artifact.artifact_id, retained_input=frozen_input, raw=frozen_raw)
            if checked != mechanical or checked_raw != frozen_raw:
                raise ValueError("prepared future assessor changes original pre-future mechanical publication")
            product = custody.assess_future(config, *(records[name] for name in ("history", "causal", "point", "mechanical", "responses")),
                ports["initial-state"].read(), ports["history-arrays"].read(), frozen_raw, ports["response-arrays"].read(),
                record_id="score." + config.source.source_id, frozen_input=frozen_input)
            return _outputs(context, product)
        finally:
            for port in context.input_ports:
                port.close()


def operation_declarations():
    from .prepared_assay_composition import scientific_root_validator

    codecs = {kind.SCHEMA: kind for kind in (*RECORDS.values(), custody.MatrixPreparedFutureConfig, custody.MatrixPreparedFutureArrays,
        MatrixPreparedResponseReadout)}
    permissions = prediction.source_owner.operation_declarations()[0].permissions
    declarations = tuple(RecursiveOperationDeclaration(capability_key=custody.NAMESPACE + "." + phase, capability_version="1.0.0",
        implementation_id=custody.NAMESPACE + "." + phase + ".v1", kind=CapabilityKind.SIMULATOR if phase == "responses" else CapabilityKind.FALSIFIER,
        config_record_type=custody.MatrixPreparedFutureConfig, stage=ScientificStage.ACQUIRE if phase == "responses" else ScientificStage.FALSIFY,
        input_ports=tuple(sorted((RecursivePortContract(name, RECORDS[name].SCHEMA if name in RECORDS else MATRIX_ARRAY_SCHEMA,
            "application/json" if name in RECORDS else "application/x-npz", None if name in RECORDS else MAXIMUM_MATRIX_ARRAY_BYTES)
            for name in INPUTS[phase]), key=lambda row: row.port_id)),
        outputs=tuple(sorted((OutputTemplate("product", custody.MatrixPreparedFutureHistory.SCHEMA if phase == "responses" else MatrixPreparedResponseReadout.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),
            *((OutputTemplate("arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", ".npz"),) if phase == "responses" else ())), key=lambda row: row.output_id)),
        permissions=permissions, evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=prediction.source_owner.BUDGET,
        conformance_check_ids=("complete48-native-branch-and-purpose-census", "original-independent-full192-and-ou-readout"),
        runner_factory=MatrixPreparedFutureNativeRunner if phase == "responses" else MatrixPreparedFutureAssessor, record_codecs=codecs,
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=digests, scientific_unit_ids=units,
            native_effect_slot_ids=slots if phase == "responses" else None, scientific_root_validator=scientific_root_validator),
        execution_properties=RecursiveExecutionProperties(native_effect=phase == "responses", complete_unit_census=phase == "responses",
            native_work_preparer=prepare_native_work if phase == "responses" else None),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,), storage_codecs=MATRIX_STORAGE_CODECS) for phase in ("responses", "response-score"))
    return tuple(replace(row, runner_factory=partial(row.runner_factory, manifest=row.manifest()))
        for row in declarations)
