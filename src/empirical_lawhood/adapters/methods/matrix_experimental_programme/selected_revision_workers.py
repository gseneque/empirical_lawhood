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
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import AdmissionStatus, ScientificStatus
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.adjudication import AdjudicationEvaluability, ScientificAdjudicationContext, ScientificAdjudicationRecord
from empirical_lawhood.runtime.execution import TaskContext, WorkerInputKind
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract

from . import preparation_bindings as preparation
from .selected_native_execution import _read, _outputs, _native_inputs
from .selected_original_commitments import MatrixRevisionEntryEvidenceV2, MatrixRevisionRootConfigV2
from . import preparation_science
from . import prepared_prefix
from . import selected_revision_future as future
from . import selected_revision_bindings as owner
from .prepared_forecast import forecast_public
from .prepared_point import MatrixPreparedPublicSource, matched_causal_feature
from .selected_revision_entry import validate_entry_evidence
from .selected_revision_programme import MatrixRevisionRootConfig, entry_seal
from .selected_revision_results import assess_revision_programme, revision_transfer_regimes
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_point import forecast_revision_prepared


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
            or runner.manifest.capability_key != owner.capability_key(runner.phase, runner.lane, runner.manifest.capability_version)
            or prepared.native_effect != (runner.phase in owner.NATIVE)
            or context.permissions != runner.manifest.permissions
            or not runner.manifest.resource_ceiling.contains(context.resource_budget)
            or context.outcome_access is not owner.access(runner.phase, runner.lane)
            or prepared.execution_task_record.stage is not owner.stage(runner.phase, runner.lane)):
        raise ValueError("selected worker changes actual manifest, stage, native scope or issued access")
    prepared.validate_context(context)
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
        allowed = (OutcomeAccess.DEVELOPMENT_VISIBLE,) if runner.lane == "DEVELOPMENT" else (OutcomeAccess.OUTCOME_BLIND, OutcomeAccess.EVALUATION_SEALED)
        visibility = VisibilityCeiling.DEVELOPMENT_ONLY if runner.lane == "DEVELOPMENT" else VisibilityCeiling.PROSPECTIVE
        if port.outcome_access not in allowed or port.visibility_ceiling is not visibility:
            raise ValueError("revision worker changes the original actual scientific access lane")
        if edge.producer_task_id is None:
            if port.kind is not WorkerInputKind.EXTERNAL:
                raise ValueError("selected worker substitutes an original external input")
        else:
            receipts = tuple(row for row in context.dependency_receipts if port.materialization_id in row.output_materialization_ids)
            if (port.kind is not WorkerInputKind.DEPENDENCY or len(receipts) != 1
                    or receipts[0].task_id != edge.producer_task_id
                    or edge.producer_output_id is None):
                raise ValueError("selected worker loses actual current producer task/output receipt custody")
        record_kind = (MatrixRevisionEntryEvidenceV2 if base == "entry-evidence"
            else owner.FINAL_KINDS.get(base, owner.RECORDS.get(base)))
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
    if type(config) in preparation.native_config_types():
        preparation.validate_native_input_records(config, received)
        expected_inputs.update(name for name, _, _ in preparation.native_input_records(config.source,
            panels=getattr(config, "panels", None)))
    if runner.phase != "assess-programme" and set(received) | set(raw_arrays) != expected_inputs:
        raise ValueError("selected worker omits a required original numerical operand")
    if runner.phase == "entry":
        evidence = received["entry-evidence"]
        if evidence.identity != config.entry_evidence or len(evidence.canonical_bytes()) != config.entry_evidence_size_bytes:
            raise ValueError("selected entry changes actual parent-authenticated evidence pin/size")
        validate_entry_evidence(evidence, config.programme)
    else:
        seal = received["entry"]
        programme_pin = config.programme.identity if type(config) in (MatrixRevisionRootConfig, MatrixRevisionRootConfigV2) else getattr(config, "programme", None)
        if programme_pin is not None and seal.programme != programme_pin:
            raise ValueError("selected worker substitutes its actual successful source-entry seal")
        selected_package = getattr(config, "selected_package", None)
        if selected_package is not None:
            selected_pin = selected_package if type(selected_package) is ObjectIdentity else selected_package.identity
            if selected_pin != seal.selected_package:
                raise ValueError("revision worker substitutes the selected original E4 package")
        if runner.phase == "assess-programme":
            if seal != entry_seal(config.programme):
                raise ValueError("selected final assessment changes complete actual source-entry census")
        else:
            source_id = config.source.source_id if hasattr(config, "source") else config.public_source.source.object_id
            if source_id not in seal.source_ids:
                raise ValueError("selected worker source was not admitted by its original complete entry")
        _dependencies(context, config, received, edges)
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
        "point": "point", "mechanical": "mechanical", "mechanical-arrays": "mechanical", "responses": "responses", "response-arrays": "responses"}
    external_names = {"source", "allocation", "initial-state", "point-package", "protocol", "templates"}
    for edge in edges:
        name = edge.consumer_input_id
        if name == "entry":
            task, output = entry, "product"
        elif name == "original-allocation" and phase == "assess-programme":
            task, output = entry, "original-allocation"
        elif phase == "assess-programme":
            base, source_id = name.split(".", 1)
            if base not in owner.FINAL_KINDS or source_id not in received["entry"].source_ids:
                raise ValueError("selected final reducer receives a foreign case source")
            tail = {"points": "point", "mechanicals": "mechanical", "readouts": "response-score"}[base]
            task, output = future.NAMESPACE + "." + source_id + "." + tail, "product"
        elif name in external_names or name == "native-provenance" or name.startswith("native-stream."):
            if edge.producer_task_id is not None or edge.producer_output_id is not None:
                raise ValueError("selected worker replaces its exact external source operand")
            continue
        else:
            source_id = config.source.source_id if hasattr(config, "source") else config.public_source.source.object_id
            tail = producer_phases[name]
            namespace = preparation.NAMESPACE if tail in ("history", "assess") else future.NAMESPACE
            task, output = namespace + "." + source_id + "." + tail, "arrays" if name.endswith("arrays") else "product"
        if (edge.producer_task_id, edge.producer_output_id) != (task, task + "." + output):
            raise ValueError("selected worker substitutes the exact actual ordinary producer output")


def _adjudication(context, programme, prepared_scope):
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
        (("EMPIRICAL_RESPONSE_INFERENCE_DOES_NOT_ESTABLISH_SAMPLING_QUALIFICATION_OR_TRANSPORT_GUARANTEE",)
            if programme.criterion.is_matched else ("DOWNSTREAM_PREPARATION_OR_TRANSFER_CALIBRATION_APPLICABILITY_NOT_ESTABLISHED",)))


class SelectedRevisionWorker:
    def __init__(self, phase, lane, manifest, prepared_scope=None, original_allocation=None):
        if phase not in owner.PHASES or manifest.capability_key != owner.capability_key(phase, lane, manifest.capability_version):
            raise ValueError("selected worker changes its declared owning phase")
        self.phase, self.lane, self.manifest, self.prepared_scope = phase, lane, manifest, prepared_scope
        from .selected_native_execution import PreparedNativeArrayPreparation
        self._native_array_preparation = PreparedNativeArrayPreparation()
        self.original_allocation = original_allocation

    def with_prepared_scope(self, scope, *, original_allocation=None):
        if type(scope) is not tuple or len(scope) != 4:
            raise ValueError("selected parent preparation requires exact issued run/task/input/plan scope")
        if self.phase == "entry":
            if type(original_allocation) is not UnitAllocation:
                raise ValueError("revision entry needs its parent-authenticated original allocation")
            original_allocation.__post_init__()
        elif original_allocation is not None:
            raise ValueError("revision leaf cannot carry a newly selected original allocation")
        return type(self)(self.phase, self.lane, self.manifest, scope, original_allocation)

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
                if type(self.original_allocation) is not UnitAllocation:
                    raise ValueError("revision entry loses its parent-authenticated original allocation")
                self.original_allocation.__post_init__()
                if config.programme.phase == "E6_TRANSFER":
                    revision_transfer_regimes(config.programme, self.original_allocation)
                return _outputs(context, {"product": entry_seal(config.programme), "original-allocation": self.original_allocation})
            elif self.phase == "assess-programme":
                observations = {}
                for _, source in config.programme.source_arms():
                    names = tuple(name + "." + source.source_id for name in ("points", "mechanicals", "readouts"))
                    if not all(name in records for name in names):
                        raise ValueError("selected final reducer drops a complete assigned case/product denominator")
                    observations["case." + source.source_id] = tuple(records[name] for name in names)
                if len(records) != 2 + 3 * len(observations):
                    raise ValueError("selected final reducer duplicates original selected case products")
                manifest, product = assess_revision_programme(config.programme, observations, result_id="result." + context.task_id,
                    original_allocation=records["original-allocation"])
                products = {"manifest": manifest, "product": product}
                if self.lane == "PROTECTED":
                    products["adjudication"] = _adjudication(context, config.programme, self.prepared_scope)
                return _outputs(context, products)
            elif self.phase == "point":
                package = records["point-package"]
                if package.identity != records["entry"].selected_package or package.identity != config.selected_package:
                    raise ValueError("revision point substitutes the actual admitted E4 selection")
                feature = (matched_causal_feature(config.public_source, records["protocol"], records["causal"], records["witness"],
                    records["mechanical"], arrays["causal-arrays"], arrays["diagnostic-arrays"], arrays["mechanical-arrays"],
                    record_id="feature." + context.task_id,
                    curve_primary=package.models.relation_fit.selection.is_curve_primary) if package.models.relation_fit is not None else None)
                product = forecast_revision_prepared(package.models, config.public_source, records["causal"],
                    nomination=package.nomination, original_calibration=package.original_calibration, record_id="point." + context.task_id,
                    feature=feature, calibration=package.frozen_calibration, reference_package=package.reference_package)
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
                point = records["point"]
                if point.feature is not None:
                    feature = matched_causal_feature(MatrixPreparedPublicSource.from_source(config.source), records["protocol"],
                        records["causal"], records["witness"], mechanical, arrays["causal-arrays"],
                        arrays["diagnostic-arrays"], arrays["mechanical-arrays"], record_id=point.feature.record_id,
                        curve_primary=config.selected_package.models.relation_fit.selection.is_curve_primary)
                    if feature != point.feature:
                        raise ValueError("selected response assessor changes the actual pre-future causal/mechanical feature")
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
