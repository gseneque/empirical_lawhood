# SPDX-License-Identifier: MPL-2.0
"""Issued CAL/CONF workers; existing prepared invocation and native services own effects."""

from .response_array_preparation import selected_record_array_mappings as _values

from hashlib import sha256

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.runtime.execution import TaskContext, WorkerInputKind
from empirical_lawhood.runtime.input_access import validated_scientific_input_edges
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract

from . import selected_e4_native_bindings as owner, selected_e4_native_records as r, selected_e4_native_science as method
from . import science, response_science, response_forecast
from .selected_e4_adjudication import require_adjudication_context, adjudication_record
from .records import identity
from .selected_native_source import bind_selected_native_source, selected_stream_operands
from .response_array_preparation import NativeResponseArrayPreparation
from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history_segments as segments
from .selected_e4_native_execution import phase_config, initial_native_work, execute_native

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
        raise ValueError("selected worker changes exact issued physical/canonical bytes")
    return raw


def _decode(context, runner):
    if type(context) is not TaskContext:
        raise TypeError("selected worker requires its actual issued TaskContext")
    context.__post_init__()
    scope = (context.run_id, context.task_id, context.input_materialization_ids,
        None if context.prepared_invocation is None else context.prepared_invocation.execution_plan)
    if runner.prepared_scope is None or runner.prepared_scope != scope:
        raise PermissionError("selected worker lacks exact current parent admission preparation")
    if runner.phase == "adjudicate":require_adjudication_context(context, runner.manifest)
    prepared = context.prepared_invocation
    if (type(prepared) is not PreparedInvocationContract or prepared.manifest != runner.manifest
            or runner.manifest.capability_key not in (owner.key_for_phase(runner.phase),
                *((owner.key_for_phase(runner.phase,referenced=True),owner.key_for_phase(runner.phase,referenced=True,compact_protocol=True)) if runner.phase in owner.PHASES and runner.phase not in ("entry","reduce") else ()))
            or prepared.native_effect != (runner.phase in owner.NATIVE)
            or context.permissions != runner.manifest.permissions
            or not runner.manifest.resource_ceiling.contains(context.resource_budget)
            or context.outcome_access is not owner.access(runner.phase)
            or prepared.execution_task_record.stage is not owner.stage(runner.phase)):
        raise ValueError("selected worker changes actual manifest, stage, native scope or development access")
    contracts = {row.artifact_id: row for row in prepared.inputs}
    ports = {row.artifact_id: row for row in context.input_ports}
    if (len(contracts)!=len(prepared.inputs) or len(ports)!=len(context.input_ports) or set(contracts)!=set(ports)):
        raise ValueError("protected E4 aliases or drops immutable exact input ports")
    config_port = ports.get(context.config.artifact_id)
    declarations = {(row.capability_key,row.capability_version): row for row in owner.operation_declarations()}
    declaration = declarations[(runner.manifest.capability_key,runner.manifest.capability_version)]
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
        base = name.split(".", 1)[0] if name.startswith(("cases.", "streams.","waves.")) else name
        if base not in owner.inputs_for_config(config):
            raise ValueError("selected worker receives an undeclared scientific edge")
        port = ports[edge.operational_logical_artifact_id]
        if port.outcome_access is not owner.input_access(name):
            raise ValueError("selected worker receives foreign-lane scientific inputs")
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
        record_kind = r.SelectedE4ProtectedEvidence if base == "evidence" else owner.RECORDS.get(base)
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
    expected = set(owner.inputs_for_config(config))
    actual = {name.split(".", 1)[0] if name.startswith(("cases.", "streams.","waves.")) else name for name in (*received, *raw_arrays)}
    if actual != expected:
        raise ValueError("selected E4 worker omits a required exact scientific operand")
    expected_names=set()
    for name in owner.inputs_for_config(config):
        if name=="cases":
            wave=config.programme.waves[[v.wave_id for v in config.programme.waves].index(config.wave_id)]
            expected_names.update("cases."+v for v in wave.root_ids)
        elif name=="waves":expected_names.update("waves."+v for v,_,_ in config.observations)
        elif name=="streams":expected_names.update("streams."+str(index) for index in range(8 if config.phase == "responses" else 4))
        else:expected_names.add(name)
    if set(received)|set(raw_arrays)!=expected_names:
        raise ValueError("selected E4 worker drops or adds an assigned exact scientific input")
    if owner.referenced_config(config):
        config=owner.bind_selected_e4_models(config,received["models"])
    if runner.phase in ("entry","phase-entry"):
        evidence = received["evidence"]
        if evidence.identity != config.evidence or len(evidence.canonical_bytes()) != config.evidence_size_bytes:
            raise ValueError("selected E4 entry changes original parent-authenticated evidence pin/size")
        if received["bank"].identity!=config.bank:
            raise ValueError("protected E4 entry substitutes complete original bank")
        r.validate_evidence(evidence, config.programme, received["bank"],config.decision,config.models,config.calibration)
        if runner.phase=="phase-entry":
            collection=received["wave-evidence"]
            if (collection.identity!=config.wave_evidence or len(collection.canonical_bytes())!=config.wave_evidence_size_bytes
                    or collection.declaration!=config.declaration.identity
                    or tuple(v.locator.wave_id for v in collection.waves)!=tuple(v.wave_id for v in config.programme.waves)):
                raise ValueError("selected E4 phase entry drops or substitutes its complete original wave scope")
    else:
        seal = received["entry"]
        programme_pin = config.programme.identity if type(config) in (owner.SelectedE4ProtectedReduceConfig,owner.SelectedE4PhaseCollectConfig) else config.programme
        if (seal.programme != programme_pin
                or seal.population_phase != (("CALIBRATION" if config.programme.mode=="E4_REVISION_CALIBRATION" else "CONFIRMATION") if type(config) in (owner.SelectedE4ProtectedReduceConfig,owner.SelectedE4PhaseCollectConfig) else config.population_phase)
                or type(config) not in (owner.SelectedE4ProtectedReduceConfig,owner.SelectedE4PhaseCollectConfig) and (
                    seal.decision!=config.decision.identity or seal.models!=(None if config.models is None else config.models.identity)
                    or seal.calibration!=(None if config.calibration is None else config.calibration.identity))):
            raise ValueError("selected E4 worker substitutes its actual successful source-entry seal")
        if runner.phase not in ("reduce","phase-collect","adjudicate"):
            source_pin = config.source.descriptor.identity if owner.native_config(config) else config.public_source.source
            if source_pin not in seal.sources:
                raise ValueError("selected E4 worker source was not admitted by the original whole programme")
            if "source" in received and received["source"] != config.source:
                raise ValueError("selected E4 worker changes exact local native source bytes")
        _dependencies(config, received, edges)
        if "account" in received:
            method.validate_revision_account(config,received["account"])
        if "streams" in expected:
            streams = tuple(received[name] for name in sorted(received) if name.startswith("streams."))
            expected_streams = tuple(value for _, value in selected_stream_operands(config.source, config.panels,
                include_future=config.phase == "responses"))
            if streams != expected_streams:
                raise ValueError("selected E4 worker changes the exact original root/panel stream census")
    if "secondary-target" in received:
        secondary = config.secondary_readout if runner.phase in ("entry", "phase-entry") or runner.phase == "mechanical" else received["secondary-readout"]
        secondary.validate_target(received["secondary-target"])
        if runner.phase in ("entry", "phase-entry"):
            for protocol in received["bank"].response_selection.protocols:
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
    seal=records["entry"]
    entry=owner.NAMESPACE+(".phase-entry." if seal.wave_id is None else ".entry.")+seal.programme.object_fingerprint+("" if seal.wave_id is None else ".wave."+seal.wave_id)
    owners = {"prefix": ("prefix", "product"), "prefix-arrays": ("prefix", "arrays"), "checkpoint": ("prefix", "checkpoint"),
        "numerical": ("numerical", "product"), "witness": ("measure", "product"), "diagnostic-arrays": ("measure", "arrays"),
        "frames": ("check", "product"), "causal": ("project", "product"), "causal-arrays": ("project", "arrays"),
        "account": ("account", "product"), "mechanical": ("mechanical", "product"), "mechanical-arrays": ("mechanical", "arrays"),
        "dense-mechanical": ("mechanical", "dense-product"), "dense-mechanical-arrays": ("mechanical", "dense-arrays"),
        "full": ("continue", "product"), "full-arrays": ("continue", "arrays"), "full-numerical": ("full-numerical", "product"),
        "responses": ("responses", "product"), "response-arrays": ("responses", "arrays"), "score": ("response-score", "product"),"score-projection":("response-score","projection")}
    for edge in edges:
        name = edge.consumer_input_id
        if name in ("entry","revision-forecasts"):
            task, output = entry, "forecasts" if name=="revision-forecasts" else "product"
        elif phase == "adjudicate" and name == "reduction":
            task, output = owner.global_node(config.programme,"reduce",config.wave_id), "product"
        elif name.startswith("waves."):
            if phase!="phase-collect" or edge.producer_task_id is not None or edge.producer_output_id is not None:
                raise ValueError("selected E4 collector substitutes original external wave observation")
            continue
        elif name.startswith("cases."):
            root = name.removeprefix("cases.")
            if phase != "reduce" or root not in {case.root_id for case in config.programme.cases}:
                raise ValueError("selected E4 reducer receives a foreign whole-case operand")
            task, output = owner.local_node(root, "collect"), "product"
        elif name in ("source", "design", "templates", "provenance", "models", "secondary-target", "secondary-readout") or name.startswith("streams."):
            if edge.producer_task_id is not None or edge.producer_output_id is not None:
                raise ValueError("selected E4 changes a direct original external operand")
            continue
        else:
            root = config.source.root_id if owner.native_config(config) else config.public_source.root.root_id
            tail, output = owners[name]
            task = owner.local_node(root, tail)
        if (edge.producer_task_id, edge.producer_output_id) != (task, task + "." + output):
            raise ValueError("selected E4 replaces the exact ordinary scientific producer/output")




def _array_id(context, output_id="arrays"):
    rows=tuple(value for value in context.output_ports if value.output_id == context.task_id + "." + output_id)
    if len(rows)!=1 or rows[0].payload_schema!=MATRIX_ARRAY_SCHEMA:
        raise ValueError("selected E4 changes an exact declared array output")
    return rows[0].logical_artifact_id






class SelectedE4ProtectedWorker:
    def __init__(self, phase, manifest, prepared_scope=None):
        if phase not in (*owner.PHASES,*owner.EXTRAS) or manifest.capability_key not in (owner.key_for_phase(phase),
                *((owner.key_for_phase(phase,referenced=True),owner.key_for_phase(phase,referenced=True,compact_protocol=True)) if phase in owner.PHASES and phase not in ("entry","reduce") else ())):
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
            physical=physical, ports=ports, protocol=owner.protocol_for_config(config) if physical is not None else None,
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
            for port in getattr(context,"input_ports",()):
                port.close()

    def execute(self, context):
        try:
            if self.phase in owner.NATIVE:
                raise PermissionError("selected E4 native phase requires genuine existing native-subwork execution")
            config, records, ports = _decode(context, self)
            if self.phase in ("entry","phase-entry"):
                products={"product":r.entry_seal(config,records["evidence"],bank=records["bank"])}
                if self.phase=="entry":
                    products["forecasts"]=method.entry_forecasts(config)
                return _outputs(context,products)
            if self.phase == "adjudicate":
                reduction = records["reduction"]
                wave = next(value for value in config.programme.waves if value.wave_id == config.wave_id)
                expected = tuple((value.root_id, value.source, value.independent_group_id)
                    for value in config.programme.cases if value.root_id in wave.root_ids)
                if (reduction.programme != config.programme.identity or reduction.bank != config.bank
                        or reduction.wave_id != config.wave_id or reduction.group_ids != wave.group_ids
                        or tuple((value.root_id, value.source, value.group_id) for value in reduction.cases) != expected
                        or records["entry"].wave_id != config.wave_id or records["entry"].groups != wave.group_ids):
                    raise ValueError("selected E4 wave adjudication changes the actual complete assigned acquisition")
                reasons = {"WAVE_ACQUISITION_RETAINED", "SCIENTIFIC_ASSESSMENT_PENDING", "SCIENTIFIC_QUALIFICATION_NOT_ESTABLISHED"}
                reasons.update("CASE_DISPOSITION_" + value.disposition for value in reduction.cases)
                return _outputs(context, {"adjudication": adjudication_record(context, self.manifest, reasons)})
            if self.phase=="phase-collect":
                observed=tuple(records["waves."+wave] for wave,_,_ in config.observations)
                for value,(_,pin,size) in zip(observed,config.observations,strict=True):
                    if value.identity!=pin or len(value.canonical_bytes())!=size:
                        raise ValueError("selected E4 phase collector changes authenticated original wave observations")
                reduction,data,forecasts=method.collect_selected_e4_programme(config.declaration,observed,
                    record_id="reduction."+config.programme.programme_id)
                return _outputs(context,{"product":reduction,"observed":data,"forecasts":forecasts})
            if self.phase == "reduce":
                wave=next(v for v in config.programme.waves if v.wave_id==config.wave_id)
                cases = tuple(records["cases." + case.root_id] for case in config.programme.cases if case.root_id in wave.root_ids)
                if len(records) != len(cases) + 1:
                    raise ValueError("selected E4 reduction adds or omits an original assigned case")
                reduction,observed,forecasts=method.reduce_cases(config.programme,config.bank,cases,
                    record_id="reduction."+config.programme.programme_id+"."+config.wave_id,wave_id=config.wave_id)
                return _outputs(context,{"product":reduction,"observed":observed,"forecasts":forecasts})
            source = bind_selected_native_source(config.source, records["provenance"]) if owner.native_config(config) else None
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
                    independent_group_id=source.root.root.independent_group_id,coordinate=source.coordinate)
                product = method.completed_case(case, config.protocol, config.panels, account_seal=records["account"], score=records["score"],
                    full_numerical=records["full-numerical"], prefix=history, causal=records["causal"],full=full, responses=response,
                    score_projection=records["score-projection"],
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
                        arrays["causal-arrays"], arrays["diagnostic-arrays"], record_id="account." + config.public_source.root.root_id,programme=config.programme,
                        decision=config.decision,models=config.models,calibration=config.calibration,original_summary=config.original_summary,
                        protocol=config.protocol,physical=records["mechanical"],frozen_arrays=arrays["mechanical-arrays"])
                    bank=records["revision-forecasts"]
                    selected=tuple(v for v in bank.forecasts if v.case_id==config.public_source.root.root_id)
                    expected = () if product.revision is None or config.models.relation_fit is not None else (product.revision,)
                    if (bank.programme!=config.programme or selected!=expected
                            or config.models is not None and config.models.relation_fit is not None and bank.forecasts):
                        raise ValueError("selected E4 account changes actual entry-produced pre-future forecast")
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
                if self.phase=="response-score":
                    from .selected_e4_programme import SelectedE4ScoreProjection
                    projection=SelectedE4ScoreProjection.from_record(product,config.protocol,config.panels,
                        record_id="score-projection."+source.root_id)
                    return _outputs(context,{"product":product,"projection":projection,"dense-score":dense_score})
                return _outputs(context, {"product": product})
        finally:
            for port in getattr(context,"input_ports",()):
                port.close()
