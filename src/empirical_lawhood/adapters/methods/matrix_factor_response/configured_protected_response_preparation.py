# SPDX-License-Identifier: MPL-2.0
"""Current response operands and effect-free native work projection.

The API owns current authority and original publication authentication. This
decoder checks the actual delivered records, producer receipts and prepared
edges. It grants no source qualification or native entry authority.
"""

from .protected_input_custody import read_protected_e3_response_input as _read

from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledSource
from dataclasses import dataclass

from empirical_lawhood.adapters.methods.matrix_history_analysis.records import MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledCheckpoint
from empirical_lawhood.adapters.methods.matrix_scheduled_history.operation_bindings import validate_original_prefix_receipt
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponsePanel, ScheduledResponseProtocol
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling, inherited_visibility
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.serialization import validate_stable_id
from empirical_lawhood.runtime.input_access import validated_scientific_input_edges
from empirical_lawhood.runtime.artifacts import ArtifactProfile, derived_outcome_access
from empirical_lawhood.runtime.capabilities import CapabilityManifest
from empirical_lawhood.runtime.execution import TaskContext, WorkerInputKind, WorkerInputPort
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkRoster
from empirical_lawhood.runtime.plans import ExecutionTask, ScientificStage
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract, PreparedNativeWork

from .configured_protected_specification import ConfiguredProtectedE3Specification as MatrixResponseErrorSpecification
from .protected_input_custody import matches_protected_e3_producer
from .configured_protected_methods import ConfiguredProtectedE3Calibration, ConfiguredProtectedE3Forecast, ConfiguredProtectedE3FrozenProducts, ConfiguredProtectedE3ModelSet
from .configured_protected_prefix_records import ConfiguredProtectedE3CausalPrefix, ConfiguredProtectedE3PrefixHistory
from .configured_protected_protocol import ConfiguredProtectedE3ProtocolProjection
from .configured_protected_response_records import (
    ConfiguredProtectedE3NativeResponse, ConfiguredProtectedE3PhysicalForecast, ConfiguredProtectedE3PhysicalForecastConfig, ConfiguredProtectedE3ResponseConfig,
    ConfiguredProtectedE3ResponseNumericalProfile, _bound_source, _error_forecast, _object, _panels, _selected_protocol,
    protected_e3_response_native_contract,
)
from .configured_protected_source_records import NAMESPACE, ProtectedE3NativeSourceManifest, ConfiguredProtectedE3ResponseSelection, ConfiguredProtectedE3SourceConfig, ProtectedE3SourcePhase, identity, source_task_id
from .response_frontier import MatrixResponseFrontierProtocol


from .protected_input_custody import validate_protected_e3_response_dependency as _dependency

from .protected_input_custody import validate_protected_e3_response_array as _array

def response_task_id(root_id: str, operation: str) -> str:
    validate_stable_id(root_id)
    if operation not in ("physical-forecast", "responses", "response-score"):
        raise ValueError("protected E3 response task needs its exact current operation")
    return NAMESPACE + "." + root_id + "." + operation


PUBLIC_RECORDS = (("specification", MatrixResponseErrorSpecification), ("protocol", ScheduledResponseProtocol),
    ("numerical-profile", ConfiguredProtectedE3ResponseNumericalProfile), ("mathematical-protocol", MatrixResponseFrontierProtocol),
    ("projection", ConfiguredProtectedE3ProtocolProjection), ("causal", ConfiguredProtectedE3CausalPrefix))
RESPONSE_RECORDS = (*PUBLIC_RECORDS, ("manifest", ProtectedE3NativeSourceManifest), ("source", ScheduledSource),
    ("coordinate", MatrixParameterCoordinate), ("provenance", NumericalProducingProvenance),
    ("selection", ConfiguredProtectedE3ResponseSelection),
    ("prefix-config", ConfiguredProtectedE3SourceConfig), ("history", ConfiguredProtectedE3PrefixHistory), ("checkpoint", ScheduledCheckpoint),
    ("physical-config", ConfiguredProtectedE3PhysicalForecastConfig), ("physical", ConfiguredProtectedE3PhysicalForecast),
    ("error", ConfiguredProtectedE3Forecast), ("allocation", UnitAllocation), ("models", ConfiguredProtectedE3ModelSet))


@dataclass(frozen=True, slots=True)
class ConfiguredProtectedE3ResponseOperands:
    config: object
    records: dict
    ports: dict
    source: object | None
    outputs: tuple
    visibility: VisibilityCeiling
    outcome_access: OutcomeAccess

    def science_arguments(self):
        names = {"prefix_config": "prefix-config", "source": None, "specification": "specification", "manifest": "manifest",
            "selection": "selection", "protocol": "protocol", "numerical_profile": "numerical-profile", "panels": "panels",
            "history": "history", "causal": "causal", "physical_config": "physical-config", "physical": "physical", "error": "error",
            "allocation": "allocation", "models": "models", "frozen": "frozen", "calibration": "calibration",
            "model_freeze": "model-freeze", "mathematical_protocol": "mathematical-protocol", "projection": "projection"}
        result = {key: self.source if name is None else self.records.get(name) for key, name in names.items()}
        if 'retention' in self.records:
            result['retention'] = self.records['retention']
        return result








def decode_response_inputs(context, *, capability, operation, statistical_task_id, record_reader=None):
    """Check first-callback metadata or the exact bound current invocation."""
    from .configured_protected_statistical_bindings import statistical_task_id as original_task_projection
    from .configured_continued_response import ConfiguredE3ContinuedResponseConfig, ConfiguredE3ContinuedNativeResponse, require_response_retention
    from .configured_retained_execution import ConfiguredE3RetainedExecution
    read_record = _read if record_reader is None else record_reader
    if not callable(read_record):
        raise TypeError('protected E3 response record reader must be callable')
    if (type(context) is not TaskContext or type(capability) is not CapabilityManifest
            or operation not in ("physical-forecast", "responses", "response-score") or statistical_task_id is not original_task_projection):
        raise TypeError("protected E3 response requires exact context/declaration and its code-owned task projection")
    context.__post_init__()
    capability.__post_init__()
    continued = capability.config_schema == ConfiguredE3ContinuedResponseConfig.SCHEMA
    expected_access = OutcomeAccess.OUTCOME_BLIND if operation == "physical-forecast" else OutcomeAccess.EVALUATION_SEALED
    if (capability.capability_key != NAMESPACE + "." + ('continued-' if continued else '') + operation or context.permissions != capability.permissions
            or context.outcome_access is not expected_access or not capability.resource_ceiling.contains(context.resource_budget)
            or (context.config.config_schema, context.config.config_schema_sha256) != (capability.config_schema, capability.config_schema_sha256)):
        raise ValueError("protected E3 response changes actual operation/permissions/configuration/access")
    prepared = context.prepared_invocation
    if prepared is not None:
        stage = ScientificStage.FREEZE if operation == "physical-forecast" else ScientificStage.ACQUIRE if operation == "responses" else ScientificStage.FALSIFY
        if (type(prepared) is not PreparedInvocationContract or type(prepared.execution_task_record) is not ExecutionTask or prepared.manifest != capability
                or prepared.native_effect != (operation == "responses") or prepared.execution_task_record.stage is not stage):
            raise ValueError("protected E3 response changes its actual prepared operation/effect")
        prepared.validate_context(context)
    elif operation != "responses":
        raise ValueError("protected E3 PURE response worker requires its actual prepared invocation")
    config_type = ConfiguredProtectedE3PhysicalForecastConfig if operation == "physical-forecast" else (
        ConfiguredE3ContinuedResponseConfig if continued else ConfiguredProtectedE3ResponseConfig)
    native_type = ConfiguredE3ContinuedNativeResponse if continued else ConfiguredProtectedE3NativeResponse
    record_inputs = PUBLIC_RECORDS if operation == 'physical-forecast' else RESPONSE_RECORDS
    if continued:
        record_inputs += (('retention', ConfiguredE3RetainedExecution),)
        from .configured_unfinished_execution import ConfiguredE3UnfinishedExecution
        if any(port.payload_schema == ConfiguredE3UnfinishedExecution.SCHEMA for port in context.input_ports):
            record_inputs += (('unfinished', ConfiguredE3UnfinishedExecution),)
        from .configured_closeout_execution import ConfiguredE3ClosedExecution
        if any(port.payload_schema == ConfiguredE3ClosedExecution.SCHEMA for port in context.input_ports):
            record_inputs += (('closeout', ConfiguredE3ClosedExecution),)
        if len({port.payload_schema for port in context.input_ports} & {
                ConfiguredE3UnfinishedExecution.SCHEMA, ConfiguredE3ClosedExecution.SCHEMA}) > 1:
            raise ValueError('continued E3 response cannot mix no-contact and closed-CAL boundaries')
    types = {kind.SCHEMA: kind for _, kind in record_inputs}
    types[config_type.SCHEMA] = config_type
    if operation != "physical-forecast":
        types.update({kind.SCHEMA: kind for kind in (ConfiguredProtectedE3FrozenProducts, ConfiguredProtectedE3Calibration, ScheduledResponsePanel, MatrixHistorySeed)})
        if operation == "response-score":
            types[native_type.SCHEMA] = native_type
    decoded, array_ports = [], {}
    for port in context.input_ports:
        if type(port) is not WorkerInputPort:
            raise TypeError("protected E3 response requires original worker input ports")
        if port.payload_schema == MATRIX_ARRAY_SCHEMA and port.media_type == "application/x-npz":
            if port.artifact_id in array_ports:
                raise ValueError("protected E3 response duplicates a direct ordinary array input")
            array_ports[port.artifact_id] = port
        elif port.payload_schema in types and port.media_type == "application/json":
            kind = types[port.payload_schema]
            record = read_record(port, prepared, kind)
            if type(record) is not kind:
                raise TypeError('protected E3 response reader changes its exact record type')
            decoded.append((record, port))
        else:
            raise ValueError("protected E3 response receives an undeclared scientific input")
    configs = tuple((record, port) for record, port in decoded if port.artifact_id == context.config.artifact_id)
    if len(configs) != 1 or type(configs[0][0]) is not config_type:
        raise ValueError("protected E3 response loses its actual configuration port")
    config, config_port = configs[0]
    root_id = config.root_id if operation == "physical-forecast" else config.source.root_id
    config_id = config.config_id
    if ((context.config.config_id, context.config.content_sha256, context.task_id) !=
            (config_id, config.fingerprint(), response_task_id(root_id, operation))
            or config_port.kind is not WorkerInputKind.EXTERNAL
            or operation != "physical-forecast" and config.operation != operation):
        raise ValueError("protected E3 response substitutes its actual immutable current task/configuration")
    remaining = [(record, port) for record, port in decoded if port is not config_port]
    records, ports = {}, {}
    for name, kind in record_inputs:
        rows = tuple((record, port) for record, port in remaining if type(record) is kind)
        if len(rows) != 1:
            raise ValueError("protected E3 response drops or duplicates an exact scientific operand: " + name)
        records[name], ports[name] = rows[0]
        remaining.remove(rows[0])
    if operation == "physical-forecast":
        from .configured_protected_response_science import _public_inputs
        _public_inputs(config, records["causal"], **{key.replace("-", "_"): records[key] for key in
            ("specification", "protocol", "numerical-profile", "mathematical-protocol", "projection")})
        source = None
    else:
        prefix, history = records["prefix-config"], records["history"]
        if (prefix.phase is not ProtectedE3SourcePhase.PREFIX or prefix.source != config.source
                or prefix.specification != config.specification or prefix.source_manifest != config.source_manifest):
            raise ValueError("protected E3 response changes original PREFIX configuration/source references")
        source = history.validate_source(prefix, records["manifest"], specification=records["specification"])
        retention = require_response_retention(config, records.get('retention'), source=source,
            run_id=context.run_id)
        unfinished = records.get('unfinished', records.get('closeout'))
        if unfinished is not None and (unfinished.retention != retention
                or context.task_id not in unfinished.unfinished_task_ids):
            raise ValueError('unfinished E3 response changes its retained science or selects completed work')
        validate_original_prefix_receipt(history, context.run_id if retention is None else retention.original_run_id)
        provenance = source.provenance if retention is None else retention.response_provenance
        if (records["source"] != config.source or records["coordinate"] != source.coordinate or records["provenance"] != provenance
                or records["checkpoint"] != history.checkpoint):
            raise ValueError("protected E3 response substitutes direct source, producing provenance or native checkpoint bytes")
        for name, kind, count in (("panels", ScheduledResponsePanel, 2), ("streams", MatrixHistorySeed, 8)):
            rows = tuple(sorted(((record, port) for record, port in remaining if type(record) is kind),
                key=lambda row: _object(row[0]).object_id if name == "panels" else row[1].artifact_id))
            if len(rows) != count:
                raise ValueError("protected E3 response changes complete direct panel/four-purpose stream census")
            records[name], ports[name] = tuple(row[0] for row in rows), tuple(row[1] for row in rows)
            for row in rows:
                remaining.remove(row)
        _selected_protocol(records["specification"], records["protocol"], records["numerical-profile"], records["projection"], records["mathematical-protocol"])
        _bound_source(source, config, records["manifest"], records["selection"], records["protocol"])
        _panels(config, records["selection"], records["protocol"], records["panels"])
        expected_streams = {(source.root.stream_identity(s).object_id, s) for s in source.root.streams}
        expected_streams.update((p.stream_identity(s).object_id, s) for p in records["panels"] if p.role == "INDEPENDENT_FUTURE" for s in p.streams)
        if {(port.artifact_id, stream) for port, stream in zip(ports["streams"], records["streams"], strict=True)} != expected_streams:
            raise ValueError("protected E3 response substitutes original eight direct stream bytes")
        frozen_rows = tuple(row for row in remaining if type(row[0]) is ConfiguredProtectedE3FrozenProducts)
        exact = tuple(row for row in frozen_rows if identity(row[0]) == records["error"].frozen_products)
        if len(exact) != 1:
            raise ValueError("protected E3 response loses its actual frozen point forecast")
        records["frozen"], ports["frozen"] = exact[0]
        remaining.remove(exact[0])
        confirmation = source.root.root.role.value == "CONFIRMATION"
        for name, kind in (("calibration", ConfiguredProtectedE3Calibration), ("model-freeze", ConfiguredProtectedE3FrozenProducts)):
            rows = tuple(row for row in remaining if type(row[0]) is kind)
            if len(rows) != int(confirmation):
                raise ValueError("protected E3 response changes actual CAL/CONF calibrated ancestry")
            records[name], ports[name] = rows[0] if rows else (None, None)
            if rows:
                remaining.remove(rows[0])
        records["physical"].validate_public_inputs(records["physical-config"], specification=records["specification"],
            protocol=records["protocol"], numerical_profile=records["numerical-profile"], causal=records["causal"],
            mathematical_protocol=records["mathematical-protocol"], projection=records["projection"])
        _error_forecast(records["specification"], records["allocation"], records["models"], records["frozen"],
            records["calibration"], records["model-freeze"], records["causal"], records["physical"],
            records["protocol"], records["error"], config.source)
    if operation == "response-score":
        for name, kind in (("native-config", config_type), ("responses", native_type)):
            rows = tuple(row for row in remaining if type(row[0]) is kind)
            if len(rows) != 1:
                raise ValueError("protected E3 score loses its actual current native acquisition operand")
            records[name], ports[name] = rows[0]
            remaining.remove(rows[0])
    if remaining:
        raise ValueError("protected E3 response includes surplus undeclared scientific operands")
    return _finish_inputs(context, capability, operation, statistical_task_id, config, config_port, records, ports, array_ports, source)


def _finish_inputs(context, capability, operation, statistical_task_id, config, config_port, records, ports, arrays, source):
    """Join current receipt edges, actual ordinary aliases and compiled lanes."""
    from .configured_protected_methods import ConfiguredProtectedE3PairedOutcome
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseScore

    root_id = config.root_id if source is None else source.root_id
    producers = {"causal": (source_task_id(root_id, ProtectedE3SourcePhase.PROJECT), "product")}
    if source is not None:
        common = (config.specification, records["allocation"].identity)
        confirmation = source.root.root.role.value == "CONFIRMATION"
        producers.update({
            "history": (source_task_id(root_id, ProtectedE3SourcePhase.PREFIX), "product"),
            "checkpoint": (source_task_id(root_id, ProtectedE3SourcePhase.PREFIX), "checkpoint"),
            "physical": (response_task_id(root_id, "physical-forecast"), "product"),
            "models": (statistical_task_id(*common, "fit"), "product"),
            "frozen": (statistical_task_id(*common, "freeze", mode="calibration" if confirmation else "model"), "product"),
            "error": (statistical_task_id(*common, "forecast", mode="evaluation" if confirmation else "calibration", root=source.root.root), "product"),
        })
        if confirmation:
            producers.update({"model-freeze": (statistical_task_id(*common, "freeze", mode="model"), "product"),
                "calibration": (statistical_task_id(*common, "calibrate"), "product")})
        if operation == "response-score":
            producers["responses"] = (response_task_id(root_id, "responses"), "product")
            arguments = ConfiguredProtectedE3ResponseOperands(config, records, ports, source, (),
                VisibilityCeiling.PROSPECTIVE, OutcomeAccess.EVALUATION_SEALED).science_arguments()
            records["responses"].validate_source(records["native-config"], **{key: value for key, value in arguments.items() if key != "prefix_config"})

    expected_arrays = {"causal-arrays": (records["causal"].arrays, source_task_id(root_id, ProtectedE3SourcePhase.PROJECT), "arrays"),
        "templates-arrays": (records["protocol"].templates, None, None)} if operation != "responses" else {}
    if source is not None:
        expected_arrays.update({"prefix-arrays": (records["history"].arrays, source_task_id(root_id, ProtectedE3SourcePhase.PREFIX), "arrays"),
            "physical-arrays": (records["physical"].arrays, response_task_id(root_id, "physical-forecast"), "arrays")})
        if operation == "response-score":
            expected_arrays["response-arrays"] = (records["responses"].arrays, response_task_id(root_id, "responses"), "arrays")
    retention = records.get('retention')
    unfinished = records.get('unfinished', records.get('closeout'))
    imported = set() if unfinished is None else {key for key, _ in unfinished.completed_receipts}
    retained_producers = set() if retention is None else {task for task, _ in retention.retained_arrays}
    array_ids = {name: (unfinished.imported(producer, output).logical.logical_artifact_id if producer in imported else
        'artifact.' + context.run_id + '.' + producer + '.arrays' if producer in retained_producers
        else original.array_artifact.artifact_id) for name, (original, producer, output) in expected_arrays.items()}
    if set(arrays) != set(array_ids.values()):
        raise ValueError("protected E3 response changes complete ordinary array input census")
    prepared = context.prepared_invocation
    selected_inputs = {}
    for name, port in ports.items():
        if port is None:
            continue
        actual_ports = port if type(port) is tuple else (port,)
        for actual in actual_ports:
            selected_inputs[actual.artifact_id] = (name, producers.get(name))
    aliases = {}
    for name, (original, producer, output) in expected_arrays.items():
        port = arrays[array_ids[name]]
        if producer in imported:
            from dataclasses import replace
            from .configured_unfinished_execution import require_imported_input
            require_imported_input(unfinished, context, port, producer, output)
            row = unfinished.imported(producer, output)
            if (row.logical.content_sha256, row.materialization.size_bytes) != (
                    original.array_artifact.sha256, original.array_artifact.size_bytes):
                raise ValueError('unfinished E3 changes original canonical array bytes')
            aliases[name] = replace(port, binding=replace(port.binding, artifact_id=original.array_artifact.artifact_id))
            _array(aliases[name], original, None)
        elif producer in retained_producers:
            from .configured_continued_response import retained_array_port
            aliases[name] = retained_array_port(port, original, producer=producer, retention=retention, context=context)
        else:
            _array(port, original, prepared)
        selected_inputs[port.artifact_id] = (name, None if producer is None else (producer, output))
        ports[name] = port
    for artifact_id, (_, producer) in selected_inputs.items():
        port = next(port for port in context.input_ports if port.artifact_id == artifact_id)
        if producer is not None:
            from .configured_unfinished_execution import require_imported_input
            if require_imported_input(unfinished, context, port, *producer):
                selected_inputs[artifact_id] = selected_inputs[artifact_id][0], None
            else:
                _dependency(context, port, *producer, prepared)
        elif port.kind is not WorkerInputKind.EXTERNAL or any(port.materialization_id in row.output_materialization_ids
                for row in context.dependency_receipts):
            raise ValueError("protected E3 response substitutes an original external publication with an undeclared producer")
    used_receipts = {row.receipt_id for row in context.dependency_receipts
        if any(port.materialization_id in row.output_materialization_ids and selected_inputs.get(port.artifact_id, (None, None))[1] is not None
            for port in context.input_ports)}
    if used_receipts != set(context.dependency_receipt_ids):
        raise ValueError("protected E3 response changes complete dependency receipt census")
    if prepared is not None:
        edges = validated_scientific_input_edges(context, config_port=config_port)
        if len(edges) != len(selected_inputs) or {row.operational_logical_artifact_id for row in edges} != set(selected_inputs):
            raise ValueError("protected E3 response changes complete prepared scientific edge census")
        for edge in edges:
            name, producer = selected_inputs[edge.operational_logical_artifact_id]
            repeated = name in ("panels", "streams")
            producer_matches = ((edge.producer_task_id, edge.producer_output_id) == (None, None)
                if producer is None else matches_protected_e3_producer(edge, *producer))
            if ((edge.consumer_input_id != name if not repeated else not edge.consumer_input_id.startswith(name + "."))
                    or not producer_matches):
                raise ValueError("protected E3 response changes its exact scientific role or producing port")

    expected_outputs = {"score": (ScheduledResponseScore.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json"),
        "outcome": (ConfiguredProtectedE3PairedOutcome.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json")} if operation == "response-score" else {
        "arrays": (MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz"),
        "product": ((ConfiguredProtectedE3PhysicalForecast if source is None else
            _native_response_type(retention is not None)).SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json")}
    if (len(context.output_ports) != len(expected_outputs)
            or {port.output_id.rsplit(".", 1)[-1] for port in context.output_ports} != set(expected_outputs)
            or any(not port.logical_artifact_id or (port.payload_schema, port.profile, port.media_type) !=
                expected_outputs[port.output_id.rsplit(".", 1)[-1]] for port in context.output_ports)
            or len({port.logical_artifact_id for port in context.output_ports}) != len(expected_outputs)):
        raise ValueError("protected E3 response changes its complete bound ordinary output contract")
    declared = OutcomeAccess.OUTCOME_BLIND if source is None else OutcomeAccess.EVALUATION_SEALED
    access = derived_outcome_access(declared, *(port.outcome_access for port in context.input_ports))
    visibility = inherited_visibility(tuple(port.visibility_ceiling for port in context.input_ports), access)
    allowed = ((OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE),
        (OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)) if source is None else (
            (OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.PROSPECTIVE),
            (OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.DEVELOPMENT_ONLY))
    if (access, visibility) not in allowed:
        raise ValueError("protected E3 response changes its closed inherited information lane")
    if prepared is not None and any((row.outcome_access, row.visibility_ceiling) != (access, visibility)
            for row in prepared.execution_task_record.outputs):
        raise ValueError("protected E3 response changes actual compiler-derived output access or visibility")
    ports.update(aliases)
    return ConfiguredProtectedE3ResponseOperands(config, records, ports, source, context.output_ports, visibility, access)


def _native_response_type(continued):
    if continued:
        from .configured_continued_response import ConfiguredE3ContinuedNativeResponse
        return ConfiguredE3ContinuedNativeResponse
    return ConfiguredProtectedE3NativeResponse


def prepare_response_work(*, context, expected_parent, capability, statistical_task_id):
    operands = decode_response_inputs(context, capability=capability, operation="responses", statistical_task_id=statistical_task_id)
    return response_native_work(operands, context=context, expected_parent=expected_parent)


def response_native_work(operands, *, context, expected_parent):
    """One exact initial definition, shared by both preparation callbacks."""
    if type(expected_parent) is not NativeEffectContact:
        raise TypeError("protected E3 response requires its exact anticipated ordinary parent")
    expected_parent.__post_init__()
    source = operands.source
    retention = operands.records.get('retention')
    provenance = source.provenance if retention is None else retention.response_provenance
    if ((expected_parent.run_id, expected_parent.task_id, expected_parent.attempt_id, expected_parent.implementation_commit,
            expected_parent.input_materialization_ids, expected_parent.dependency_receipt_ids) !=
            (context.run_id, context.task_id, context.attempt_id, provenance.observed_git_head,
                context.input_materialization_ids, context.dependency_receipt_ids)):
        raise ValueError("protected E3 response changes its complete anticipated parent")
    prepared = context.prepared_invocation
    if prepared is not None:
        if expected_parent != prepared.expected_parent_contact:
            raise ValueError("protected E3 response changes its exact prepared task/plan parent")
        implementation = prepared.implementation
        if ((provenance.package_sources, provenance.code_sources_sha256, provenance.dependency_lock_sha256,
                provenance.observed_git_head) != (implementation.package_sources, implementation.code_sources_sha256,
                    implementation.dependency_lock_sha256, implementation.observed_git_head)):
            raise ValueError("protected E3 response changes actual producing source or dependency lock")
    _, configuration, _, operation, sources, streams, outputs = protected_e3_response_native_contract(operands.config,
        **{key: value for key, value in operands.science_arguments().items() if key in ("source", "manifest", "specification",
            "selection", "protocol", "numerical_profile", "panels", "history", "causal", "physical", "error", 'retention')})
    definition = NativeSubworkDefinition("responses." + source.root_id, operation, expected_parent, configuration, sources,
        provenance.code_sources_sha256, provenance.dependency_lock_sha256, context.input_materialization_ids, streams, outputs)
    roster = NativeSubworkRoster("selected.native-subwork", expected_parent, (definition.identity,))
    return PreparedNativeWork(expected_parent, (source.root.root.independent_group_id,), (definition.subwork_id,), (definition,), (roster,))
