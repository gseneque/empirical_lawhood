# SPDX-License-Identifier: MPL-2.0
"""Installed finite-dt source predicates with mandatory current parent custody.

The certificate is a new semantic projection relative to future E4 units. No
ordinary artifact lineage/access rule is changed by these declarations.
"""
from dataclasses import dataclass
from functools import partial

from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterNumericalDesign
from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as scheduled
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling, inherited_visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.time import InformationCutoff
from empirical_lawhood.planning.scientific_source_qualification import ScientificSourceGateEvidence
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck, derived_outcome_access
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import ParentPreparedTaskRunner, RunnerResult, TaskContext, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.plans import ExecutionTask, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract, RecursiveScientificRootContext
from empirical_lawhood.runtime.recursive_provider import RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks

from . import matrix_prepared_source_records as r
from .matrix_finite_dt_source_bindings import closeout_declaration as closeout_declaration, MatrixFiniteDtSourceCloseoutConfig as MatrixFiniteDtSourceCloseoutConfig

BUDGET = ResourceBudget(1, None, 0, None, None, None)


def input_kinds(phase):
    from .matrix_experimental_programme.protected_preparation_records import MatrixProtectedSourceClosure, MatrixConfirmationSources, MatrixReservedTransferSources
    from .matrix_experimental_programme.prepared_assay_method import MatrixPreparedAssayMethod
    if phase not in ('E5_CONFIRMATION', 'E6_TRANSFER'):
        raise ValueError('prepared source gate phase is not installed')
    return {"scope": r.MatrixPreparedSourceScope, "bank": r.MatrixPreparedSourceBank,
        "source": MatrixProtectedSourceClosure,
        "preparation": MatrixConfirmationSources if phase == 'E5_CONFIRMATION' else MatrixReservedTransferSources,
        "assay": MatrixPreparedAssayMethod, "numerical": MatrixParameterNumericalDesign,
        "original-reservation": scheduled.ScheduledReservation, "cutoff": InformationCutoff,
        "certificate": r.MatrixPreparedInstrumentCertificate}


@dataclass(frozen=True, slots=True)
class PreparedMatrixSourceGateScope:
    """Parent-authenticated exact task facts; never a serialized authority token."""
    run_id: str
    task_id: str
    configuration: ObjectIdentity
    scope: ObjectIdentity
    certificate: ObjectIdentity


def prepare_for_invocation(supplier, runner):
    if type(runner) is not MatrixPreparedSourceGateWorker:
        raise TypeError("finite-dt parent preparation requires its exact installed gate worker")
    callback = getattr(supplier, "prepare_matrix_prepared_source_gate", None)
    if not callable(callback):
        raise PermissionError("finite-dt gate requires its installed current API custody owner")
    return ParentPreparedTaskRunner(runner.manifest, partial(callback, runner=runner))


def scientific_root_validator(config, context):
    if type(config) is not r.MatrixPreparedSourceGateConfig or type(context) is not RecursiveScientificRootContext:
        raise TypeError("finite-dt gate requires its exact compiler scientific context")
    config.__post_init__()
    if (context.stage is not ScientificStage.QUALIFY or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY or context.unit_ids != config.group_ids
            or context.selected_unit_ids != config.group_ids or context.complete_unit_census
            or context.root.evaluation_unit_ids != config.group_ids or context.root.experiment is None
            or any(value.evidence_ceiling is not EvidenceCeiling.NON_PROMOTABLE
                for value in context.root.experiment.claims)):
        raise ValueError("finite-dt source cannot change whole future units, access or nonpromotable scientific claims")


class MatrixPreparedSourceGateWorker:
    def __init__(self, kind, phase, prepared_scope=None):
        if kind not in r.GATES:
            raise ValueError("finite-dt gate kind is not installed")
        self.kind, self.phase = kind, phase
        self.manifest = gate_declaration(kind, phase).manifest()
        self.prepared_scope = prepared_scope

    def with_prepared_scope(self, scope):
        if type(scope) is not PreparedMatrixSourceGateScope:
            raise PermissionError("finite-dt gate refuses unprepared original TRAIN custody")
        return MatrixPreparedSourceGateWorker(self.kind, self.phase, scope)

    def execute(self, context):
        from empirical_lawhood.adapters.methods.matrix_factor_response.protected_prefix_workers import _read
        if type(context) is not TaskContext:
            raise PermissionError("finite-dt gate needs its actual current issued task context")
        try:
            context.__post_init__()
            prepared, authenticated = context.prepared_invocation, self.prepared_scope
            if (type(prepared) is not PreparedInvocationContract or prepared.manifest != self.manifest
                    or type(authenticated) is not PreparedMatrixSourceGateScope
                    or authenticated.run_id != context.run_id or authenticated.task_id != context.task_id
                    or prepared.native_effect or type(prepared.execution_task_record) is not ExecutionTask
                    or prepared.execution_task_record.stage is not ScientificStage.QUALIFY
                    or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE or context.permissions != self.manifest.permissions
                    or context.dependency_receipts or not self.manifest.resource_ceiling.contains(context.resource_budget)
                    or (context.config.config_schema, context.config.config_schema_sha256) !=
                        (self.manifest.config_schema, self.manifest.config_schema_sha256)):
                raise PermissionError("finite-dt source refuses missing custody or altered issue/stage/access/resources")
            prepared.validate_context(context)
            kinds = input_kinds(self.phase)
            config_ports = tuple(value for value in context.input_ports if value.artifact_id == context.config.artifact_id)
            if len(config_ports) != 1:
                raise PermissionError("finite-dt gate omits its one exact issued configuration")
            config_port, = config_ports
            contracts = {value.artifact_id: value for value in prepared.inputs}
            if (len(contracts) != len(prepared.inputs) or len(context.input_ports) != len(kinds) + 1
                    or {value.artifact_id for value in context.input_ports} != set(contracts)
                    or any(value.kind is not WorkerInputKind.EXTERNAL for value in context.input_ports)):
                raise PermissionError("finite-dt gate changes its complete external future-instrument input census")
            access = derived_outcome_access(OutcomeAccess.DEVELOPMENT_VISIBLE, *(value.outcome_access for value in context.input_ports))
            visibility = inherited_visibility(tuple(value.visibility_ceiling for value in context.input_ports), access)
            if any(value.outcome_access is not access or value.visibility_ceiling is not visibility
                    for value in prepared.execution_task_record.outputs):
                raise PermissionError("prepared source gate drops actual inherited input access from its outputs")
            from empirical_lawhood.runtime.input_access import validated_scientific_input_edges
            edges = validated_scientific_input_edges(context, config_port=config_port)
            config = _read(config_port, contracts[config_port.artifact_id], r.MatrixPreparedSourceGateConfig)
            if (config.gate_kind is not self.kind or config.phase != self.phase or config.fingerprint() != context.config.content_sha256
                    or config.identity != authenticated.configuration or config.scope != authenticated.scope
                    or config.resource_budget != context.resource_budget):
                raise PermissionError("finite-dt gate changes its actually prepared canonical configuration")
            records = {}
            for name, kind in sorted(kinds.items()):
                selected = tuple(value for value in edges if value.consumer_input_id == name)
                if len(selected) != 1 or selected[0].producer_task_id is not None:
                    raise PermissionError("finite-dt gate changes exact scientific input ownership")
                edge, = selected
                ports = tuple(value for value in context.input_ports
                    if value.artifact_id == edge.operational_logical_artifact_id)
                if len(ports) != 1 or ports[0] is config_port or ports[0].payload_schema != kind.SCHEMA:
                    raise PermissionError("finite-dt gate substitutes its exact typed scientific input")
                port, = ports
                if name in ("bank", "source", "preparation") and port.outcome_access is r.BLIND:
                    raise PermissionError("prepared source gate cannot treat model-bearing inputs as blind metadata")
                records[name] = _read(port, contracts[port.artifact_id], kind)
            if (len(edges) != len(kinds) or records["scope"].identity != authenticated.scope
                    or records["certificate"].identity != authenticated.certificate):
                raise PermissionError("finite-dt gate changes its actual original prerequisite certificate")
            product = r.validate_gate_operands(config, records["scope"], records)
            output, = context.output_ports
            if output.output_id != context.task_id + ".product" or output.payload_schema != product.SCHEMA:
                raise PermissionError("finite-dt gate changes its exact declared scientific output")
            return RunnerResult((TaskOutputPayload(output.output_id, product.canonical_bytes()),),
                (ReceiptCheck("finite-dt-instrument-original-controls-and-complete-future-source", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def _units(config):
    return config.group_ids


def _operands(config):
    return (config.scope.object_fingerprint,)


def gate_declaration(kind, phase):
    if kind not in r.GATES:
        raise ValueError("finite-dt source gate is not an installed scientific predicate")
    codecs = {value.SCHEMA: value for value in (*input_kinds(phase).values(), r.MatrixPreparedSourceGateConfig, ScientificSourceGateEvidence)}
    return RecursiveOperationDeclaration(r.NAMESPACE + "." + phase.lower() + "." + kind.value.lower(), "1.0.0",
        r.NAMESPACE + "." + phase.lower() + "." + kind.value.lower() + ".receipt-backed-instrument-v1", CapabilityKind.NUMERICAL_QUALIFIER,
        r.MatrixPreparedSourceGateConfig, ScientificStage.QUALIFY,
        tuple(RecursivePortContract(name, value.SCHEMA, "application/json", None)
            for name, value in sorted(input_kinds(phase).items())),
        (OutputTemplate("product", ScientificSourceGateEvidence.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),),
        (CapabilityPermission.READ_DEVELOPMENT, CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_SEALED_OUTCOMES,
            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS),
        EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, BUDGET,
        ("finite-dt-instrument-original-controls-and-complete-future-source",), partial(MatrixPreparedSourceGateWorker, kind, phase), codecs,
        execution_properties=RecursiveExecutionProperties(runner_preparation_factory=prepare_for_invocation),
        scientific_hooks=RecursiveScientificHooks(scientific_unit_ids=_units,
            scientific_operand_sha256s=_operands,
            scientific_root_validator=scientific_root_validator),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,))


def gate_declarations():
    return tuple(gate_declaration(kind, phase) for phase in ('E5_CONFIRMATION', 'E6_TRANSFER') for kind in r.GATES)
