# SPDX-License-Identifier: MPL-2.0
"""Pure, receipt-bound copies of completed E3 products into a new execution."""
from dataclasses import dataclass, replace
from functools import partial
from hashlib import sha256

from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind
from empirical_lawhood.runtime.execution import ParentPreparedTaskRunner, RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.input_access import validated_scientific_input_edges, validated_task_scientific_input_edges
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract
from empirical_lawhood.runtime.plans import ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_provider import RecursiveExecutionProperties, RecursiveScientificHooks

from .configured_protected_prefix_workers import _read
from .configured_protected_source_records import NAMESPACE
from .configured_retained_execution import ConfiguredE3RetainedExecution, ConfiguredE3RetainedTaskConfig, RETAINED_PHASES, source_binding


def retained_output_record_types(declarations):
    """Project only retained canonical output owners for public FILE inputs."""
    return tuple(sorted({declaration.record_codecs[output.payload_schema]
        for declaration in declarations
        if declaration.capability_key.startswith(NAMESPACE + '.retained-')
        for output in declaration.outputs if output.profile is ArtifactProfile.CANONICAL_JSON},
        key=lambda kind: (kind.SCHEMA, kind.VERSION)))


def retained_input_id(logical):
    return 'input.retained-e3.' + sha256(canonical_json_bytes((logical.logical_artifact_id,
        logical.content_sha256))).hexdigest()


def retained_phase(config):
    from .configured_protected_lowering import operation_class
    if type(config) is not ConfiguredE3RetainedTaskConfig:
        raise TypeError('retained E3 requires its exact custody-adoption configuration')
    config.__post_init__()
    return operation_class(config.original_config)


@dataclass(frozen=True, slots=True)
class _Hooks:
    original: object

    def units(self, config):
        retained_phase(config)
        return self.original.scientific_hooks.scientific_unit_ids(config.original_config)

    def operands(self, config):
        retained_phase(config)
        return tuple(sorted({config.continuation.object_fingerprint,
            config.original_receipt.fingerprint(), config.original_task.fingerprint(),
            *self.original.scientific_hooks.scientific_operand_sha256s(config.original_config)}))


def _prepare_retained_task(supplier, runner, context):
    method = getattr(supplier, 'prepare_configured_e3_retained_task', None)
    if not callable(method):
        raise PermissionError('retained E3 adoption needs its actual issued original-custody owner')
    return method(context, runner)


def _prepare(supplier, runner):
    return ParentPreparedTaskRunner(runner.manifest, partial(_prepare_retained_task, supplier, runner))


def retained_declaration(original, *, scientific_root_validator):
    """Keep original scientific edges/outputs, with an explicit PURE capability."""
    phase = original.capability_key.removeprefix(NAMESPACE + '.')
    if phase == 'native-fit':
        phase = 'fit'
    if phase not in RETAINED_PHASES:
        raise ValueError('retained E3 cannot adopt future responses or assessment')
    ports = (*original.input_ports,
        RecursivePortContract('retention', ConfiguredE3RetainedExecution.SCHEMA, 'application/json', None),
        *(RecursivePortContract('retained-' + output.output_id, output.payload_schema, output.media_type, None)
            for output in original.outputs))
    codecs = {**original.record_codecs, ConfiguredE3RetainedTaskConfig.SCHEMA: ConfiguredE3RetainedTaskConfig,
        ConfiguredE3RetainedExecution.SCHEMA: ConfiguredE3RetainedExecution}
    hooks = _Hooks(original)
    declaration = replace(original, capability_key=NAMESPACE + '.retained-' + phase,
        capability_version='1.0.0', implementation_id=NAMESPACE + '.retained-' + phase + '.exact-receipt-bytes.v1',
        kind=CapabilityKind.TRANSFORM if phase == 'prefix' else original.kind,
        stage=ScientificStage.TRANSFORM if phase == 'prefix' else original.stage,
        config_record_type=ConfiguredE3RetainedTaskConfig,
        input_ports=tuple(sorted(ports, key=lambda port: port.port_id)), record_codecs=codecs,
        conformance_check_ids=('exact-original-receipt-bytes-and-source-continuation', 'no-native-work-or-refit'),
        scientific_hooks=RecursiveScientificHooks(scientific_unit_ids=hooks.units,
            scientific_operand_sha256s=hooks.operands, scientific_root_validator=scientific_root_validator),
        execution_properties=RecursiveExecutionProperties(barrier=original.execution_properties.barrier,
            runner_preparation_factory=_prepare),
        runner_factory=partial(_runner, phase, original, scientific_root_validator),
        provenance_requirements=(), runtime_id=None, implementation_sha256=None)
    return declaration


def _runner(phase, original, validator):
    return ConfiguredE3RetainedTaskRunner(phase, retained_declaration(original,
        scientific_root_validator=validator).manifest())


@dataclass(frozen=True, slots=True)
class ConfiguredE3RetainedTaskRunner:
    phase: str
    manifest: object

    def execute(self, context):
        try:
            prepared = context.prepared_invocation
            if (type(prepared) is not PreparedInvocationContract or prepared.native_effect
                    or prepared.manifest != self.manifest or context.permissions != self.manifest.permissions):
                raise ValueError('retained E3 adoption changes its exact pure prepared invocation')
            ports = {port.artifact_id: port for port in context.input_ports}
            contracts = {row.artifact_id: row for row in prepared.inputs}
            config_port = ports[context.config.artifact_id]
            config = _read(config_port, contracts[config_port.artifact_id], ConfiguredE3RetainedTaskConfig)
            if (retained_phase(config) != self.phase or config.original_task.task_id != context.task_id
                    or context.config.content_sha256 != config.fingerprint()
                    or context.config.config_id != config.record_id):
                raise ValueError('retained E3 adoption changes its current task/configuration')
            edges = {edge.consumer_input_id: edge for edge in validated_scientific_input_edges(context,
                config_port=config_port)}
            originals = {edge.consumer_input_id: edge for edge in validated_task_scientific_input_edges(config.original_task)}
            expected = {*originals, 'retention', *('retained-' + output.output_id.rsplit('.', 1)[-1]
                for output in config.original_task.outputs)}
            if set(edges) != expected:
                raise ValueError('retained E3 adoption changes the complete original input and custody census')
            for name, edge in originals.items():
                actual = edges[name]
                if ((actual.producer_task_id, actual.producer_output_id, actual.scientific_role) !=
                        (edge.producer_task_id, edge.producer_output_id, edge.scientific_role)):
                    raise ValueError('retained E3 adoption bypasses an original scientific dependency')
            pin_port = ports[edges['retention'].operational_logical_artifact_id]
            retention = _read(pin_port, contracts[pin_port.artifact_id], ConfiguredE3RetainedExecution)
            config.validate_retention(retention)
            if (prepared.implementation != source_binding(retention.response_provenance)
                    or context.run_id != retention.continued_run_id):
                raise ValueError('retained E3 adoption must execute under its distinct continued producer')
            originals = {row.logical_artifact_id: row for row in config.original_receipt.output_logical_artifacts}
            physicals = {row.logical_artifact_id: row for row in config.original_receipt.output_materializations}
            outputs = {port.output_id.rsplit('.', 1)[-1]: port for port in context.output_ports}
            if set(outputs) != {row.output_id.rsplit('.', 1)[-1] for row in config.original_task.outputs}:
                raise ValueError('retained E3 adoption drops an original output port')
            payloads = []
            for old_output in config.original_task.outputs:
                name = old_output.output_id.rsplit('.', 1)[-1]
                old, physical = originals[old_output.logical_artifact_id], physicals[old_output.logical_artifact_id]
                edge = edges['retained-' + name]
                port = ports[edge.operational_logical_artifact_id]
                contract, output = contracts[port.artifact_id], outputs[name]
                if (edge.producer_task_id is not None or port.kind is not WorkerInputKind.EXTERNAL
                        or port.artifact_id != retained_input_id(old)
                        or (port.payload_schema, port.media_type, port.size_bytes, port.outcome_access, port.visibility_ceiling,
                            contract.logical.content_sha256, contract.physical_sha256) !=
                            (old.payload_schema, old.media_type, physical.size_bytes, old.outcome_access, old.visibility_ceiling,
                                old.content_sha256, physical.physical_sha256)
                        or (output.payload_schema, output.profile, output.media_type) !=
                            (old.payload_schema, old.profile, old.media_type)):
                    raise ValueError('retained E3 adoption substitutes original output bytes or access')
                raw = port.read()
                if len(raw) != physical.size_bytes or sha256(raw).hexdigest() != physical.physical_sha256:
                    raise ValueError('retained E3 original output changed during its bounded copy')
                payloads.append(TaskOutputPayload(output.output_id, raw))
            return RunnerResult(tuple(payloads), (ReceiptCheck('retained-e3-exact-original-receipt-bytes', True, ()),))
        finally:
            for port in context.input_ports:
                port.close()
