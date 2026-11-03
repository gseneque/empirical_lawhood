# SPDX-License-Identifier: MPL-2.0
"""Current DEV workers; existing prepared invocation and native services own effects."""

from .response_array_preparation import selected_record_array_mappings as _values

from hashlib import sha256

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.runtime.execution import TaskContext, WorkerInputKind
from empirical_lawhood.runtime.input_access import validated_scientific_input_edges
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract

from . import selected_e3_e4_bindings as owner, selected_e3_e4_records as r, selected_e3_e4_science as method
from . import science, response_science, response_forecast
from .records import identity
from .selected_native_source import bind_selected_native_source, selected_stream_operands
from .response_array_preparation import NativeResponseArrayPreparation
from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history_segments as segments
from .selected_e3_e4_native import phase_config, initial_native_work, execute_native

from .response_array_preparation import selected_worker_outputs as _outputs

from .response_array_preparation import read_selected_native_archive as _raw

def _read(port, contract):
    cursor = port.cursor()
    try:
        raw = cursor.read()
    finally:
        cursor.close()
    if (len(raw) != port.size_bytes or sha256(raw).hexdigest() != contract.physical_sha256
            or sha256(raw).hexdigest() != contract.logical.content_sha256):
        raise ValueError("selected worker changes exact development physical/canonical bytes")
    return raw


def _decode(context, runner):
    if type(context) is not TaskContext:
        raise TypeError("selected worker requires its actual development TaskContext")
    context.__post_init__()
    scope = (context.run_id, context.task_id, context.input_materialization_ids,
        None if context.prepared_invocation is None else context.prepared_invocation.execution_plan)
    if runner.prepared_scope is None or runner.prepared_scope != scope:
        raise PermissionError("selected worker lacks exact current parent admission preparation")
    prepared = context.prepared_invocation
    if (type(prepared) is not PreparedInvocationContract or prepared.manifest != runner.manifest
            or runner.manifest.capability_key != owner.NAMESPACE + "." + runner.phase
            or prepared.native_effect != (runner.phase in owner.NATIVE)
            or context.permissions != runner.manifest.permissions
            or not runner.manifest.resource_ceiling.contains(context.resource_budget)
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or prepared.execution_task_record.stage is not owner.stage(runner.phase)):
        raise ValueError("selected worker changes actual manifest, stage, native scope or development access")
    contracts = {row.artifact_id: row for row in prepared.inputs}
    ports = {row.artifact_id: row for row in context.input_ports}
    config_port = ports.get(context.config.artifact_id)
    declarations = {row.capability_key.rsplit(".", 1)[-1]: row for row in owner.operation_declarations()}
    declaration = declarations[runner.phase]
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
    edges = validated_scientific_input_edges(context, config_port=config_port)
    if ({edge.operational_logical_artifact_id for edge in edges} != set(ports) - {config_port.artifact_id}
            or len(edges) != len(ports) - 1 or len({edge.consumer_input_id for edge in edges}) != len(edges)):
        raise ValueError("selected worker drops or aliases its exact complete scientific inputs")
    received, raw_arrays = {}, {}
    for edge in edges:
        name = edge.consumer_input_id
        base = name.split(".", 1)[0] if name.startswith(("cases.", "streams.")) else name
        if base not in owner.INPUTS[runner.phase]:
            raise ValueError("selected worker receives an undeclared scientific edge")
        port = ports[edge.operational_logical_artifact_id]
        logical = contracts[port.artifact_id].logical
        if (port.outcome_access, port.visibility_ceiling) != (edge.outcome_access, edge.visibility_ceiling) or (
                port.outcome_access, port.visibility_ceiling) != (logical.outcome_access, logical.visibility_ceiling):
            raise ValueError("selected worker changes its frozen scientific input custody")
        if edge.producer_task_id is None:
            if port.kind is not WorkerInputKind.EXTERNAL:
                raise ValueError("selected worker substitutes an original external input")
        else:
            receipts = tuple(row for row in context.dependency_receipts if port.materialization_id in row.output_materialization_ids)
            if (port.kind is not WorkerInputKind.DEPENDENCY or len(receipts) != 1
                    or receipts[0].task_id != edge.producer_task_id
                    or edge.producer_output_id is None):
                raise ValueError("selected worker loses actual current producer task/output receipt custody")
        record_kind = r.SelectedE3E4Evidence if base == "evidence" else owner.RECORDS.get(base)
        if record_kind is None:
            if (port.payload_schema, port.media_type) != (MATRIX_ARRAY_SCHEMA, "application/x-npz"):
                raise ValueError("selected worker changes a complete raw array input type")
            raw_arrays[name] = port
        else:
            raw = _read(port, contracts[port.artifact_id])
            if (port.payload_schema, port.media_type) != (record_kind.SCHEMA, "application/json"):
                raise ValueError("selected worker changes an exact scientific input type")
            record = decode_canonical_bytes(raw, record_kind, maximum_bytes=port.size_bytes)
            if record.canonical_bytes() != raw:
                raise ValueError("selected worker changes original canonical scientific record bytes")
            received[name] = record
    expected = set(owner.INPUTS[runner.phase])
    actual = {name.split(".", 1)[0] if name.startswith(("cases.", "streams.")) else name for name in (*received, *raw_arrays)}
    if actual != expected:
        raise ValueError("selected E4 worker omits a required exact scientific operand")
    if runner.phase == "entry":
        evidence = received["evidence"]
        if evidence.identity != config.evidence or len(evidence.canonical_bytes()) != config.evidence_size_bytes:
            raise ValueError("selected E4 entry changes original parent-authenticated evidence pin/size")
        r.validate_evidence(evidence, config.programme, config.bank)
    else:
        seal = received["entry"]
        programme_pin = config.programme.identity if type(config) is owner.SelectedE3E4ReduceConfig else config.programme
        if seal.programme != programme_pin:
            raise ValueError("selected E4 worker substitutes its actual successful source-entry seal")
        if runner.phase != "reduce":
            source_pin = config.source.descriptor.identity if type(config) is owner.SelectedE3E4CompactConfig else config.public_source.source
            if source_pin not in seal.sources:
                raise ValueError("selected E4 worker source was not admitted by the original whole programme")
            if "source" in received and received["source"] != config.source:
                raise ValueError("selected E4 worker changes exact local native source bytes")
        _dependencies(config, received, edges)
        if "streams" in expected:
            streams = tuple(received[name] for name in sorted(received) if name.startswith("streams."))
            expected_streams = tuple(value for _, value in selected_stream_operands(config.source, config.panels,
                include_future=config.phase == "responses"))
            if streams != expected_streams:
                raise ValueError("selected E4 worker changes the exact original root/panel stream census")
    if "secondary-target" in received:
        secondary = config.secondary_readout if runner.phase in ("entry",) or runner.phase == "mechanical" else received["secondary-readout"]
        secondary.validate_target(received["secondary-target"])
        if runner.phase in ("entry",):
            for protocol in config.bank.response_selection.protocols:
                received["secondary-target"].validate_protocol(protocol)
        else:
            received["secondary-target"].validate_protocol(config.protocol)
    if runner.phase in ("account", "mechanical") and config.secondary_readout.identity != received["entry"].secondary_readout:
        raise ValueError("E4 predictor changes its actual pre-future entry-selected target")
    if runner.phase == "response-score" and received["secondary-readout"].identity != received["entry"].secondary_readout:
        raise ValueError("E4 score changes its actual pre-future entry-selected target")
    if "checkpoint" in received and received["checkpoint"] != received["prefix"].checkpoint:
        raise ValueError("selected E4 worker substitutes the exact original four-generator checkpoint")
    if "source" in received:
        bind_selected_native_source(config.source, received["provenance"])
    return config, received, raw_arrays


def _dependencies(config, records, edges):
    phase = config.phase
    entry = owner.NAMESPACE + ".entry." + records["entry"].programme.object_fingerprint
    owners = {"prefix": ("prefix", "product"), "prefix-arrays": ("prefix", "arrays"), "checkpoint": ("prefix", "checkpoint"),
        "numerical": ("numerical", "product"), "witness": ("measure", "product"), "diagnostic-arrays": ("measure", "arrays"),
        "frames": ("check", "product"), "causal": ("project", "product"), "causal-arrays": ("project", "arrays"),
        "account": ("account", "product"), "mechanical": ("mechanical", "product"), "mechanical-arrays": ("mechanical", "arrays"),
        "dense-mechanical": ("mechanical", "dense-product"), "dense-mechanical-arrays": ("mechanical", "dense-arrays"),
        "full": ("continue", "product"), "full-arrays": ("continue", "arrays"), "full-numerical": ("full-numerical", "product"),
        "responses": ("responses", "product"), "response-arrays": ("responses", "arrays"), "score": ("response-score", "product")}
    for edge in edges:
        name = edge.consumer_input_id
        if name == "entry":
            task, output = entry, "product"
        elif name.startswith("cases."):
            root = name.removeprefix("cases.")
            if phase != "reduce" or root not in {case.root_id for case in config.programme.cases}:
                raise ValueError("selected E4 reducer receives a foreign whole-case operand")
            task, output = owner.local_node(root, "collect"), "product"
        elif name in ("source", "design", "templates", "provenance", "secondary-target", "secondary-readout") or name.startswith("streams."):
            if edge.producer_task_id is not None or edge.producer_output_id is not None:
                raise ValueError("selected E4 changes a direct original external operand")
            continue
        else:
            root = config.source.root_id if type(config) is owner.SelectedE3E4CompactConfig else config.public_source.root.root_id
            tail, output = owners[name]
            task = owner.local_node(root, tail)
        if (edge.producer_task_id, edge.producer_output_id) != (task, task + "." + output):
            raise ValueError("selected E4 replaces the exact ordinary scientific producer/output")




def _array_id(context, output_id="arrays"):
    rows=tuple(value for value in context.output_ports if value.output_id == context.task_id + "." + output_id)
    if len(rows)!=1 or rows[0].payload_schema!=MATRIX_ARRAY_SCHEMA:
        raise ValueError("selected E4 changes an exact declared array output")
    return rows[0].logical_artifact_id






class SelectedE3E4Worker:
    def __init__(self, phase, manifest, prepared_scope=None):
        if phase not in owner.PHASES or manifest.capability_key != owner.NAMESPACE + "." + phase:
            raise ValueError("selected E4 worker changes its installed owning phase")
        self.phase, self.manifest, self.prepared_scope = phase, manifest, prepared_scope
        self._native_array_preparation = NativeResponseArrayPreparation()

    def with_prepared_scope(self, scope):
        if type(scope) is not tuple or len(scope) != 4:
            raise ValueError("selected E4 requires exact current DEV run/task/input/plan preparation")
        return type(self)(self.phase, self.manifest, scope)

    def prepare_native_work(self, context, *, expected_parent):
        config, records, arrays = _decode(context, self)
        if self.phase not in owner.NATIVE:
            raise ValueError("selected E4 pure phase cannot prepare native work")
        # Parent projections freeze exact identities only. Actual child
        # preflight validates/materializes arrays before Ready and native BEGIN.
        return initial_native_work(context, config, records, {}, expected_parent)

    def preflight(self, context):
        if self.phase not in ("continue", "responses"):
            return
        config, records, arrays = _decode(context, self)
        source = bind_selected_native_source(config.source, records["provenance"])
        ports = {"history-arrays": arrays["prefix-arrays"]}
        physical = None
        if self.phase == "responses":
            ports["physical-arrays"] = arrays["mechanical-arrays"]
            physical = records["mechanical"].arrays
        self._native_array_preparation.prepare(context, source=source, history=records["prefix"].arrays,
            physical=physical, ports=ports, protocol=config.protocol if physical is not None else None,
            physical_disposition=records["mechanical"].disposition if physical is not None else None)
        if self.phase == "continue":
            prefix, _ = self._native_array_preparation.arrays(context)
            terminal = {view + "_" + component: prefix[view + "_" + component][-1]
                for view in ("primary", "fine") for component in ("positions", "momenta")}
            segments.validate_segment_entry(source.coordinate, source.root.streams, source.policy.cutoff_tick,
                source.coordinate.total_ticks, terminal=terminal, generator_states=records["prefix"].checkpoint.generators)

    @property
    def execute_with_native_subwork(self):
        return self._execute_with_native_subwork if self.phase in owner.NATIVE else None

    def _execute_with_native_subwork(self, context, native_subwork, progress=None):
        try:
            config, records, arrays = _decode(context, self)
            prepared = None if self.phase == "prefix" else self._native_array_preparation.arrays(context)
            original = ({"prefix-arrays": self._native_array_preparation.prefix_raw(context)}
                if self.phase == "continue" else {})
            raw, product = execute_native(context, config, records, original,
                native_subwork, artifact_id=_array_id(context), progress=progress, prepared_arrays=prepared)
            products = {"product": product}
            if self.phase == "prefix":
                products["checkpoint"] = product.checkpoint
            return _outputs(context, products, raw)
        finally:
            self._native_array_preparation.clear()
            for port in context.input_ports:
                port.close()

    def execute(self, context):
        try:
            if self.phase in owner.NATIVE:
                raise PermissionError("selected E4 native phase requires genuine existing native-subwork execution")
            config, records, ports = _decode(context, self)
            if self.phase == "entry":
                return _outputs(context, {"product": r.entry_seal(config.programme, records["evidence"], secondary_readout=config.secondary_readout)})
            if self.phase == "reduce":
                cases = tuple(records["cases." + case.root_id] for case in config.programme.cases)
                if len(records) != len(cases) + 1:
                    raise ValueError("selected E4 reduction adds or omits an original assigned case")
                return _outputs(context, {"product": method.reduce_cases(config.programme, cases,
                    record_id="reduction." + config.programme.programme_id)})
            source = bind_selected_native_source(config.source, records["provenance"]) if type(config) is owner.SelectedE3E4CompactConfig else None
            if "prefix" in records:
                records["prefix"].validate_source(source, config=phase_config(config, "prefix"))
            if self.phase == "collect":
                history, full, response = records["prefix"], records["full"], records["responses"]
                full.validate_source(source, history, records["causal"], records["account"], records["mechanical"],
                    config=phase_config(config, "continue"), prefix_config=phase_config(config, "prefix"))
                response.validate_source(source, history, records["causal"], records["mechanical"], records["account"],
                    config=phase_config(config, "responses"), prefix_config=phase_config(config, "prefix"))
                # Original case pin/geometry are taken from the successful entry
                # and exact current local source, never a smaller local study.
                from types import SimpleNamespace
                case = SimpleNamespace(root_id=source.root_id, source=identity(source),
                    independent_group_id=source.root.root.independent_group_id)
                product = method.completed_case(case, config.protocol, config.panels, account_seal=records["account"], score=records["score"],
                    full_numerical=records["full-numerical"], prefix=history, full=full, responses=response,
                    receipts=context.dependency_receipts)
                return _outputs(context, {"product": product})
            with _values(records, ports, protocol=config.protocol) as arrays:
                if self.phase == "numerical":
                    science.validate_prefix_operand(source, records["prefix"].arrays)
                    product = method.numerical(source, records["prefix"], arrays["prefix-arrays"])
                elif self.phase == "full-numerical":
                    product = method.numerical(source, records["full"], arrays["full-arrays"], full=True)
                elif self.phase == "measure":
                    raw, product = method.measure(source, records["prefix"], records["numerical"], arrays["prefix-arrays"], artifact_id=_array_id(context))
                    return _outputs(context, {"product": product}, raw)
                elif self.phase == "check":
                    method.validate_numerical(source, records["prefix"], records["numerical"], arrays["prefix-arrays"])
                    product = method.check_frames(source, records["witness"], arrays["prefix-arrays"], arrays["diagnostic-arrays"])
                elif self.phase == "project":
                    raw, product = method.project(source, records["prefix"], records["numerical"], records["witness"], records["frames"],
                        arrays["prefix-arrays"], arrays["diagnostic-arrays"], artifact_id=_array_id(context))
                    return _outputs(context, {"product": product}, raw)
                elif self.phase == "account":
                    if r.pin(records["design"]) != records["entry"].forecast_design:
                        raise ValueError("selected E4 account changes the original entry-selected model package")
                    product = method.account(records["design"], config.public_source, records["causal"], records["witness"],
                        arrays["causal-arrays"], arrays["diagnostic-arrays"], record_id="account." + config.public_source.root.root_id,
                        protocol=config.protocol, physical=records["mechanical"], frozen_arrays=arrays["mechanical-arrays"])
                elif self.phase == "mechanical":
                    raw, product = method.mechanical(config.protocol, records["causal"], arrays["causal-arrays"], arrays["templates"],
                        artifact_id=_array_id(context))
                    dense_raw, dense_product = response_forecast.forecast_e4_dense(config.protocol, records["causal"],
                        arrays["causal-arrays"], arrays["templates"], target=records["secondary-target"],
                        secondary=config.secondary_readout, original_physical=product, original_forecast_raw=raw,
                        artifact_id=_array_id(context,"dense-arrays"), forecast_id="dense-mechanical."+config.public_source.root.root_id)
                    return _outputs(context, {"product": product, "dense-product": dense_product}, raw,
                        additional_arrays=(("dense-arrays",dense_raw),))
                elif self.phase == "response-score":
                    response, mechanical = records["responses"], records["mechanical"]
                    response.validate_source(source, records["prefix"], records["causal"], mechanical, records["account"],
                        config=phase_config(config, "responses"), prefix_config=phase_config(config, "prefix"))
                    original_raw=_raw(ports["mechanical-arrays"])
                    dense_raw=_raw(ports["dense-mechanical-arrays"])
                    response_raw=_raw(ports["response-arrays"])
                    _, checked = method.mechanical(config.protocol, records["causal"], arrays["causal-arrays"], arrays["templates"],
                        artifact_id=mechanical.arrays.array_artifact.artifact_id, retained=arrays["mechanical-arrays"], raw=original_raw)
                    if checked != mechanical:
                        raise ValueError("selected E4 independent assessor replaces the original mechanical forecast")
                    dense=records["dense-mechanical"]
                    _, dense_checked=response_forecast.forecast_e4_dense(config.protocol, records["causal"],
                        arrays["causal-arrays"], arrays["templates"], target=records["secondary-target"],
                        secondary=records["secondary-readout"], original_physical=mechanical, original_forecast_raw=original_raw,
                        artifact_id=dense.arrays.array_artifact.artifact_id, forecast_id=dense.forecast_id,
                        retained=arrays["dense-mechanical-arrays"],raw=dense_raw)
                    if dense_checked!=dense:
                        raise ValueError("selected E4 independent assessor replaces the actual sealed dense mechanical forecast")
                    science.validate_prefix_arrays(source, arrays["prefix-arrays"])
                    product = response_science.assess_paired_response_arrays(source, records["causal"], records["prefix"], arrays["prefix-arrays"],
                        mechanical, arrays["mechanical-arrays"], config.protocol, config.panels, response, arrays["response-arrays"],
                        error_forecast=records["account"].identity, score_id="score." + source.root_id)
                    dense_score=response_science.score_e4_dense(source, config.protocol, config.panels,
                        target=records["secondary-target"],secondary=records["secondary-readout"],original_score=product,
                        original_physical=mechanical,dense_physical=dense,responses=response,
                        original_forecast_raw=original_raw,dense_forecast_raw=dense_raw,response_raw=response_raw,
                        score_id="dense-score."+source.root_id)
                else:
                    raise ValueError("selected E4 worker changes its closed pure phase")
                return _outputs(context, {"product": product, **({"dense-score":dense_score} if self.phase == "response-score" else {})})
        finally:
            for port in context.input_ports:
                port.close()
