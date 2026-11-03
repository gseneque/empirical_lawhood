# SPDX-License-Identifier: MPL-2.0
"""Issued, parent-prepared selected CONF/transfer workers over original science.

The parent supplier authenticates source and original upstream custody. These
workers independently retain the actual issued contract, exact input bytes and
current dependency receipts before entering numerical or native methods.
"""

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import MatrixHistorySeed
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.status import AdmissionStatus, ScientificStatus
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.adjudication import AdjudicationEvaluability, ScientificAdjudicationContext, ScientificAdjudicationRecord
from empirical_lawhood.runtime.execution import TaskContext, WorkerInputKind
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract

from . import preparation_bindings as preparation
from .selected_native_execution import _read, _outputs, _native_inputs
from .selected_original_commitments import MatrixSelectedEntryEvidenceV3
from . import preparation_science
from . import prepared_prefix
from . import selected_future as future
from . import selected_protected_bindings as owner
from .prepared_forecast import forecast_public
from .prepared_point import MatrixPreparedPublicSource
from .selected_entry import validate_selected_entry_evidence
from .selected_point import forecast_selected_point, measure_selected_point
from .selected_public import package_identity
from .selected_protected_results import assess_selected_programme, entry_seal
from .e6_transport_science import assess_e6_transport, decide_e6_transport, validate_e6_public_calibration_projection
from .selected_e6_transport_config import (MatrixSelectedTransportRootConfig, MatrixSelectedTransportPointConfig,
    MatrixSelectedTransportFutureConfig, MatrixSelectedTransportScoreConfig)


def _decode(context, runner):
    if type(context) is not TaskContext:
        raise TypeError("selected worker requires its actual issued TaskContext")
    context.__post_init__()
    scope = (context.run_id, context.task_id, context.input_materialization_ids,
        None if context.prepared_invocation is None else context.prepared_invocation.execution_plan)
    if runner.prepared_scope is None or runner.prepared_scope != scope:
        raise PermissionError("selected worker lacks exact current parent admission preparation")
    prepared = context.prepared_invocation
    if (type(prepared) is not PreparedInvocationContract or prepared.manifest != runner.manifest
            or runner.manifest.capability_key != owner.capability_key(runner.phase, runner.manifest.capability_version)
            or prepared.native_effect != (runner.phase in owner.NATIVE)
            or context.permissions != runner.manifest.permissions
            or not runner.manifest.resource_ceiling.contains(context.resource_budget)
            or context.outcome_access is not owner.access(runner.phase)
            or prepared.execution_task_record.stage is not owner.stage(runner.phase)):
        raise ValueError("selected worker changes actual manifest, stage, native scope or issued access")
    contracts = {row.artifact_id: row for row in prepared.inputs}
    ports = {row.artifact_id: row for row in context.input_ports}
    config_port = ports.get(context.config.artifact_id)
    declaration = next(row for row in owner.operation_declarations() if (row.capability_key, row.capability_version) ==
        (runner.manifest.capability_key, runner.manifest.capability_version))
    kind = declaration.config_record_type
    if (config_port is None or config_port.kind is not WorkerInputKind.EXTERNAL
            or (config_port.payload_schema, config_port.media_type) != (kind.SCHEMA, "application/json")
            or context.config.config_schema != runner.manifest.config_schema
            or context.config.config_schema_sha256 != runner.manifest.config_schema_sha256):
        raise ValueError("selected worker loses its actual automatic configuration input")
    config_raw = _read(config_port, contracts[config_port.artifact_id])
    config = decode_canonical_bytes(config_raw, kind, maximum_bytes=config_port.size_bytes)
    if (config.canonical_bytes() != config_raw or config.fingerprint() != context.config.content_sha256
            or config.config_id != context.config.config_id or owner.phase_of(config) != runner.phase
            or owner.task_id(config) != context.task_id):
        raise ValueError("selected worker substitutes its immutable current configuration")
    from empirical_lawhood.runtime.input_access import validated_scientific_input_edges
    edges = validated_scientific_input_edges(context,config_port=config_port)
    if ({edge.operational_logical_artifact_id for edge in edges} != set(ports) - {config_port.artifact_id}
            or len(edges) != len(ports) - 1 or len({edge.consumer_input_id for edge in edges}) != len(edges)):
        raise ValueError("selected worker drops or aliases its exact complete scientific inputs")
    received, raw_arrays = {}, {}
    for edge in edges:
        name = edge.consumer_input_id
        base = name.split(".", 1)[0] if (runner.phase == "assess-programme" and name != "entry" or name.startswith("native-stream.")) else name
        if base not in owner.phase_inputs(runner.phase, runner.manifest.capability_version):
            raise ValueError("selected worker receives an undeclared scientific edge")
        port = ports[edge.operational_logical_artifact_id]
        if port.outcome_access not in (OutcomeAccess.OUTCOME_BLIND, OutcomeAccess.EVALUATION_SEALED):
            raise ValueError("selected worker receives revealed or development-relabeled scientific inputs")
        if port.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE:
            raise ValueError("selected worker receives a foreign scientific visibility lane")
        if edge.producer_task_id is None:
            if port.kind is not WorkerInputKind.EXTERNAL:
                raise ValueError("selected worker substitutes an original external input")
        else:
            receipts = tuple(row for row in context.dependency_receipts if port.materialization_id in row.output_materialization_ids)
            if (port.kind is not WorkerInputKind.DEPENDENCY or len(receipts) != 1
                    or receipts[0].task_id != edge.producer_task_id
                    or edge.producer_output_id is None):
                raise ValueError("selected worker loses actual current producer task/output receipt custody")
        final_kinds = owner.TRANSPORT_FINAL_KINDS if owner.is_transport_config(config) else owner.FINAL_KINDS
        record_kind = MatrixSelectedEntryEvidenceV3 if base == "entry-evidence" else final_kinds.get(base, owner.RECORDS.get(base))
        if base in ("native-provenance", "native-stream"):
            record_kind = NumericalProducingProvenance if base == "native-provenance" else MatrixHistorySeed
        if record_kind is None:
            if (port.payload_schema, port.media_type) != (MATRIX_ARRAY_SCHEMA, "application/x-npz"):
                raise ValueError("selected worker changes a complete raw array input type")
            raw_arrays[name] = port if runner.phase in owner.NATIVE else _read(port, contracts[port.artifact_id])
        else:
            raw = _read(port, contracts[port.artifact_id])
            if (port.payload_schema, port.media_type) != (record_kind.SCHEMA, "application/json"):
                raise ValueError("selected worker changes an exact scientific input type")
            record = decode_canonical_bytes(raw, record_kind, maximum_bytes=port.size_bytes)
            if record.canonical_bytes() != raw:
                raise ValueError("selected worker changes original canonical scientific record bytes")
            received[name] = record
    expected_inputs = set(owner.INPUTS[runner.phase])
    if owner.is_direct_native_config(config):
        preparation.validate_native_input_records(config, received)
        expected_inputs.update(name for name, _, _ in preparation.native_input_records(config.source,
            panels=getattr(config, "panels", None)))
    if type(config) in (MatrixSelectedTransportFutureConfig, MatrixSelectedTransportScoreConfig):
        expected_inputs.add("decision")
    if runner.phase != "assess-programme" and set(received) | set(raw_arrays) != expected_inputs:
        raise ValueError("selected worker omits a required original numerical operand")
    if runner.phase == "entry":
        evidence = received["entry-evidence"]
        if evidence.identity != config.entry_evidence or len(evidence.canonical_bytes()) != config.entry_evidence_size_bytes:
            raise ValueError("selected entry changes actual parent-authenticated evidence pin/size")
        validate_selected_entry_evidence(evidence, config.programme)
    else:
        seal = received["entry"]
        programme_pin = config.programme.identity if type(config) in owner.ROOT_CONFIG_TYPES else getattr(config, "programme", None)
        if programme_pin is not None and seal.programme != programme_pin:
            raise ValueError("selected worker substitutes its actual successful source-entry seal")
        if runner.phase == "assess-programme":
            if seal != entry_seal(config.programme):
                raise ValueError("selected final assessment changes complete actual source-entry census")
        else:
            source_id = config.source.source_id if hasattr(config, "source") else config.public_source.source.object_id
            if source_id not in seal.source_ids:
                raise ValueError("selected worker source was not admitted by its original complete entry")
        _dependencies(context, config, received, edges)
        if type(config) in (MatrixSelectedTransportFutureConfig, MatrixSelectedTransportScoreConfig):
            decision = future.transport_decision_for(config, received["point"])
            if received["decision"] != decision:
                raise ValueError("selected E6 response substitutes its exact pre-future empirical decision")
    source = received.get("source")
    if source is not None:
        if hasattr(config, "source") and config.source != source:
            raise ValueError("selected worker substitutes the actual native source configuration")
        if hasattr(config, "public_source") and MatrixPreparedPublicSource.from_source(source) != config.public_source:
            raise ValueError("selected worker substitutes its actual seedless source projection")
        if "allocation" in received:
            source.validate_allocation(received["allocation"])
        if "history" in received:
            if "allocation" in received:
                received["history"].validate_source(source, received["allocation"])
            elif received["history"].source != source.identity:
                raise ValueError("selected worker substitutes its actual preparation history source")
    return config, received, raw_arrays


def _dependencies(context, config, received, edges):
    phase = owner.phase_of(config)
    programme_pin = received["entry"].programme
    entry = future.NAMESPACE + ".entry." + programme_pin.object_fingerprint
    producer_phases = {"history": "history", "history-arrays": "history", "numerical": "assess", "witness": "measure",
        "diagnostic-arrays": "measure", "frames": "frames", "causal": "project", "causal-arrays": "project",
        "point": "point", "decision": "point", "mechanical": "mechanical", "mechanical-arrays": "mechanical", "responses": "responses", "response-arrays": "responses"}
    external_names = {"source", "allocation", "initial-state", "point-design", "protocol", "templates"}
    for edge in edges:
        name = edge.consumer_input_id
        if name == "entry":
            task, output = entry, "product"
        elif phase == "assess-programme":
            base, source_id = name.split(".", 1)
            final_kinds = owner.TRANSPORT_FINAL_KINDS if owner.is_transport_config(config) else owner.FINAL_KINDS
            if base not in final_kinds or source_id not in received["entry"].source_ids:
                raise ValueError("selected final reducer receives a foreign case source")
            tail = {"points": "point", "decisions": "point", "mechanicals": "mechanical", "readouts": "response-score"}[base]
            task, output = future.NAMESPACE + "." + source_id + "." + tail, "decision" if base == "decisions" else "product"
        elif name in external_names or name == "native-provenance" or name.startswith("native-stream."):
            if edge.producer_task_id is not None or edge.producer_output_id is not None:
                raise ValueError("selected worker replaces its exact external source operand")
            continue
        else:
            source_id = config.source.source_id if hasattr(config, "source") else config.public_source.source.object_id
            tail = producer_phases[name]
            namespace = preparation.NAMESPACE if tail in ("history", "assess") else future.NAMESPACE
            task, output = namespace + "." + source_id + "." + tail, "arrays" if name.endswith("arrays") else "decision" if name == "decision" else "product"
        if (edge.producer_task_id, edge.producer_output_id) != (task, task + "." + output):
            raise ValueError("selected worker substitutes the exact actual ordinary producer output")


def _adjudication(context, programme, prepared_scope, *, transport=False):
    scope = context.scientific_adjudication_context
    if (type(scope) is not ScientificAdjudicationContext or scope.plumbing_only or scope.fixture_scope_id is not None
            or scope.evidence_world_kind is not WorldKind.NUMERICAL_SIMULATOR or scope.execution_plan != prepared_scope[3]
            or scope.outcome_access is not OutcomeAccess.EVALUATION_REVEALED or scope.visibility_ceiling is not VisibilityCeiling.OUTCOME_VISIBLE):
        raise ValueError("selected adjudication lacks actual revealed numerical evidence context")
    return ScientificAdjudicationRecord("adjudication." + context.task_id, context.run_id, context.task_id, scope.execution_plan,
        context.input_materialization_ids, tuple(sorted(row.logical_artifact_id for row in context.output_ports)),
        tuple(sorted(row.receipt_id for row in context.dependency_receipts)), scope.evidence_world_id, scope.evidence_world_kind,
        scope.relation, scope.independent_unit_id, scope.information_cutoffs, scope.visibility_ceiling, scope.outcome_access,
        AdjudicationEvaluability.UNEVALUABLE, ScientificStatus.UNEVALUABLE, AdmissionStatus.UNEVALUABLE,
        (("E6_EMPIRICAL_TRANSPORT_WITHOUT_TRANSPORTED_QUALIFICATION",) if transport else
            ("DOWNSTREAM_PREPARATION_OR_TRANSFER_CALIBRATION_APPLICABILITY_NOT_ESTABLISHED",)))


class SelectedProtectedWorker:
    def __init__(self, phase, manifest, prepared_scope=None):
        if phase not in owner.PHASES or manifest.capability_key != owner.capability_key(phase, manifest.capability_version):
            raise ValueError("selected worker changes its declared owning phase")
        self.phase, self.manifest, self.prepared_scope = phase, manifest, prepared_scope
        from .selected_native_execution import PreparedNativeArrayPreparation
        self._native_array_preparation = PreparedNativeArrayPreparation()

    def with_prepared_scope(self, scope):
        if type(scope) is not tuple or len(scope) != 4:
            raise ValueError("selected parent preparation requires exact issued run/task/input/plan scope")
        return type(self)(self.phase, self.manifest, scope)

    def prepare_native_work(self, context, *, expected_parent):
        config, records, arrays = _decode(context, self)
        if self.phase not in owner.NATIVE:
            raise ValueError("selected nonnative phase has no native effect projection")
        _native_inputs(context, config, records, arrays, expected_parent)
        if self.phase == "history":
            return preparation.initial_native_work(context, config, config.source, expected_parent)
        return future.initial_native_work(context, config, records["history"], records["causal"], records["point"], records["mechanical"], expected_parent)

    def preflight(self, context):
        if self.phase in owner.NATIVE:
            config, records, arrays = _decode(context, self)
            _native_inputs(context, config, records, arrays, context.prepared_invocation.expected_parent_contact)
            self._native_array_preparation.prepare(context, config=config, records=records, arrays=arrays)

    def execute(self, context):
        try:
            if self.phase in owner.NATIVE:
                raise PermissionError("selected native phase requires actual native lifecycle authority")
            config, records, arrays = _decode(context, self)
            if self.phase == "entry":
                product = entry_seal(config.programme)
            elif self.phase == "assess-programme":
                observations, decisions = {}, {}
                for _, source in config.programme.sources.source_arms():
                    names = tuple(name + "." + source.source_id for name in ("points", "mechanicals", "readouts"))
                    if not all(name in records for name in names):
                        raise ValueError("selected final reducer drops a complete assigned case/product denominator")
                    observations["case." + source.source_id] = tuple(records[name] for name in names)
                    if type(config) is MatrixSelectedTransportRootConfig:
                        decisions["case." + source.source_id] = records["decisions." + source.source_id]
                if len(records) != 1 + (4 if type(config) is MatrixSelectedTransportRootConfig else 3) * len(observations):
                    raise ValueError("selected final reducer duplicates original selected case products")
                manifest, product = (assess_e6_transport(config.programme, config.transport_policy, config.transport_calibration,
                    observations, decisions, result_id="result." + context.task_id) if type(config) is MatrixSelectedTransportRootConfig else
                    assess_selected_programme(config.programme, observations, result_id="result." + context.task_id))
                return _outputs(context, {"manifest": manifest, "product": product,
                    "adjudication": _adjudication(context, config.programme, self.prepared_scope,
                        transport=type(config) is MatrixSelectedTransportRootConfig)})
            elif self.phase == "point":
                design = records["point-design"]
                if design.identity != records["entry"].point_design or package_identity(design.package) != records["entry"].package:
                    raise ValueError("selected point substitutes its actual entry-selected frozen predictor")
                feature = measure_selected_point(design, config.public_source, records["causal"], records["witness"], records["frames"],
                    arrays["causal-arrays"], arrays["diagnostic-arrays"], record_id="feature." + context.task_id)
                product = forecast_selected_point(design, feature, record_id="point." + context.task_id)
                if type(config) is MatrixSelectedTransportPointConfig:
                    validate_e6_public_calibration_projection(config.transport_calibration, config.transport_policy, design.package)
                    decision = decide_e6_transport(config.transport_policy, config.transport_calibration, product,
                        source=config.public_source, record_id="decision." + context.task_id)
                    return _outputs(context, {"product": product, "decision": decision})
            elif self.phase == "mechanical":
                raw, product = forecast_public(config.public_source, records["protocol"], records["causal"], arrays["causal-arrays"],
                    arrays["templates"], artifact_id=_array_id(context))
                return _outputs(context, {"product": product}, raw)
            elif self.phase == "response-score":
                from empirical_lawhood.infrastructure.matrix_array_io import DecodedMatrixArrayInput
                mechanical = records["mechanical"]
                frozen_input = DecodedMatrixArrayInput(arrays["mechanical-arrays"], mechanical.arrays)
                product = future.assess_future(config, records["history"], records["causal"], records["point"], records["mechanical"],
                    records["responses"], arrays["initial-state"], arrays["history-arrays"], arrays["mechanical-arrays"], arrays["response-arrays"],
                    record_id="readout." + context.task_id, frozen_input=frozen_input)
                # Reprove the retained mechanical derivative from actual causal
                # and template bytes independently before using response scores.
                _, checked = forecast_public(MatrixPreparedPublicSource.from_source(config.source), records["protocol"], records["causal"],
                    arrays["causal-arrays"], arrays["templates"], artifact_id=mechanical.arrays.array_artifact.artifact_id,
                    retained_input=frozen_input, raw=arrays["mechanical-arrays"])
                if checked != mechanical:
                    raise ValueError("selected response assessor substitutes original independent mechanical prediction")
            else:
                source, history = records["source"], records["history"]
                if self.phase == "assess":
                    values = preparation_science.consume_preparation_arrays(source, arrays["initial-state"], history.arrays, arrays["history-arrays"])
                    product = preparation_science.assess_preparation_arrays(source, arrays["initial-state"], history.arrays, values,
                        assessment_id="assessment." + source.source_id)
                elif self.phase == "measure":
                    raw, product = prepared_prefix.measure_prepared_prefix(source, arrays["initial-state"], history.arrays, records["numerical"],
                        arrays["history-arrays"], artifact_id=_array_id(context))
                    return _outputs(context, {"product": product}, raw)
                elif self.phase == "frames":
                    product = prepared_prefix.check_prepared_frames(source, arrays["initial-state"], history.arrays, records["numerical"],
                        records["witness"], arrays["history-arrays"], arrays["diagnostic-arrays"])
                else:
                    raw, product = prepared_prefix.project_prepared_prefix(source, arrays["initial-state"], history.arrays, records["numerical"],
                        records["witness"], records["frames"], arrays["history-arrays"], arrays["diagnostic-arrays"], artifact_id=_array_id(context))
                    return _outputs(context, {"product": product}, raw)
            return _outputs(context, {"product": product})
        finally:
            for port in context.input_ports:
                port.close()

    @property
    def execute_with_native_subwork(self):
        return self._execute_with_native_subwork if self.phase in owner.NATIVE else None

    def _execute_with_native_subwork(self, context, native_subwork, progress=None):
        from .selected_native_execution import execute_selected_native
        return execute_selected_native(self, context, native_subwork, native_phases=owner.NATIVE,
            decode=_decode, native_inputs=_native_inputs, execute_future=future.execute_native_future, outputs=_outputs, progress=progress)


def _array_id(context):
    return next(row.logical_artifact_id for row in context.output_ports if row.payload_schema == MATRIX_ARRAY_SCHEMA)


    # PURE work freezes metadata; the actual child preflight materializes the
    # exact initial/history/forecast arrays once before Ready and native entry.
