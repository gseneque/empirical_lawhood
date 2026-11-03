# SPDX-License-Identifier: MPL-2.0
"""Installed finite-dt source predicates with mandatory current parent custody.

The certificate is a new semantic projection relative to future E4 units. No
ordinary artifact lineage/access rule is changed by these declarations.
"""
from dataclasses import dataclass
from typing import ClassVar
from functools import partial

from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterNumericalDesign
from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as scheduled
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledResponseSelection
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_programme import SelectedE4PhaseBank, SelectedE4PhaseProgramme
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling, inherited_visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.kernel.status import AdmissionStatus, ScientificStatus
from empirical_lawhood.kernel.time import InformationCutoff
from empirical_lawhood.planning.scientific_source_qualification import ScientificSourceGateEvidence, ScientificSourceQualificationResult
from empirical_lawhood.planning.source_pipelines import SourcePipelineQualificationReceipt
from empirical_lawhood.runtime.adjudication import AdjudicationEvaluability, ScientificAdjudicationRecord
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck, derived_outcome_access
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import ParentPreparedTaskRunner, RunnerResult, TaskContext, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.plans import ExecutionTask, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract, RecursiveScientificRootContext
from empirical_lawhood.runtime.recursive_provider import RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks

from . import matrix_finite_dt_source_records as r

BUDGET = ResourceBudget(1, None, 0, None, None, None)


def input_kinds():
    return {"scope": r.MatrixFiniteDtSourceScope, "programme": SelectedE4PhaseProgramme, "bank": SelectedE4PhaseBank,
        "reservation": scheduled.ScheduledReservation, "original-reservation": scheduled.ScheduledReservation,
        "assay": ScheduledResponseSelection, "numerical": MatrixParameterNumericalDesign,
        "cutoff": InformationCutoff, "certificate": r.MatrixFiniteDtInstrumentCertificate}


@dataclass(frozen=True, slots=True)
class PreparedFiniteDtGateScope:
    """Parent-authenticated exact task facts; never a serialized authority token."""
    run_id: str
    task_id: str
    configuration: ObjectIdentity
    scope: ObjectIdentity
    certificate: ObjectIdentity


def prepare_for_invocation(supplier, runner):
    if type(runner) is not MatrixFiniteDtGateWorker:
        raise TypeError("finite-dt parent preparation requires its exact installed gate worker")
    callback = getattr(supplier, "prepare_matrix_finite_dt_gate", None)
    if not callable(callback):
        raise PermissionError("finite-dt gate requires its installed current API custody owner")
    return ParentPreparedTaskRunner(runner.manifest, partial(callback, runner=runner))


def scientific_root_validator(config, context):
    if type(config) is not r.MatrixFiniteDtGateConfig or type(context) is not RecursiveScientificRootContext:
        raise TypeError("finite-dt gate requires its exact compiler scientific context")
    config.__post_init__()
    if (context.stage is not ScientificStage.QUALIFY or context.outcome_access is not r.BLIND
            or context.visibility_ceiling is not r.PROSPECTIVE or context.unit_ids != config.group_ids
            or context.selected_unit_ids != config.group_ids or context.complete_unit_census
            or context.root.evaluation_unit_ids != config.group_ids or context.root.experiment is None
            or any(value.evidence_ceiling is not EvidenceCeiling.NON_PROMOTABLE
                for value in context.root.experiment.claims)):
        raise ValueError("finite-dt source cannot change whole future units, access or nonpromotable scientific claims")


class MatrixFiniteDtGateWorker:
    def __init__(self, kind, prepared_scope=None):
        if kind not in r.GATES:
            raise ValueError("finite-dt gate kind is not installed")
        self.kind = kind
        self.config_kind = r.MatrixFiniteDtGateConfig
        self.manifest = gate_declaration(kind).manifest()
        self.prepared_scope = prepared_scope

    def with_prepared_scope(self, scope):
        if type(scope) is not PreparedFiniteDtGateScope:
            raise PermissionError("finite-dt gate refuses unprepared original TRAIN custody")
        return MatrixFiniteDtGateWorker(self.kind, scope)

    def execute(self, context):
        from empirical_lawhood.adapters.methods.matrix_factor_response.protected_prefix_workers import _read
        if type(context) is not TaskContext:
            raise PermissionError("finite-dt gate needs its actual current issued task context")
        try:
            context.__post_init__()
            prepared, authenticated = context.prepared_invocation, self.prepared_scope
            if (type(prepared) is not PreparedInvocationContract or prepared.manifest != self.manifest
                    or type(authenticated) is not PreparedFiniteDtGateScope
                    or authenticated.run_id != context.run_id or authenticated.task_id != context.task_id
                    or prepared.native_effect or type(prepared.execution_task_record) is not ExecutionTask
                    or prepared.execution_task_record.stage is not ScientificStage.QUALIFY
                    or context.outcome_access is not r.BLIND or context.permissions != self.manifest.permissions
                    or context.dependency_receipts or not self.manifest.resource_ceiling.contains(context.resource_budget)
                    or (context.config.config_schema, context.config.config_schema_sha256) !=
                        (self.manifest.config_schema, self.manifest.config_schema_sha256)):
                raise PermissionError("finite-dt source refuses missing custody or altered issue/stage/access/resources")
            prepared.validate_context(context)
            kinds = input_kinds()
            config_ports = tuple(value for value in context.input_ports if value.artifact_id == context.config.artifact_id)
            if len(config_ports) != 1:
                raise PermissionError("finite-dt gate omits its one exact issued configuration")
            config_port, = config_ports
            if config_port.outcome_access is not r.BLIND or config_port.visibility_ceiling is not r.PROSPECTIVE:
                raise PermissionError("finite-dt gate changes its blind configuration access")
            contracts = {value.artifact_id: value for value in prepared.inputs}
            if (len(contracts) != len(prepared.inputs) or len(context.input_ports) != len(kinds) + 1
                    or {value.artifact_id for value in context.input_ports} != set(contracts)
                    or any(value.kind is not WorkerInputKind.EXTERNAL for value in context.input_ports)):
                raise PermissionError("finite-dt gate changes its complete external future-instrument input census")
            access = derived_outcome_access(r.BLIND, *(value.outcome_access for value in context.input_ports))
            visibility = inherited_visibility(tuple(value.visibility_ceiling for value in context.input_ports), access)
            if any(value.outcome_access is not access or value.visibility_ceiling is not visibility
                    for value in prepared.execution_task_record.outputs):
                raise PermissionError("finite-dt gate drops actual inherited input access from its outputs")
            config = _read(config_port, contracts[config_port.artifact_id], self.config_kind)
            if (config.gate_kind is not self.kind or config.fingerprint() != context.config.content_sha256
                    or config.identity != authenticated.configuration or config.scope != authenticated.scope
                    or config.resource_budget != context.resource_budget):
                raise PermissionError("finite-dt gate changes its actually prepared canonical configuration")
            edges = prepared.execution_task_record.scientific_inputs
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
                if name in ("bank", "programme") and port.outcome_access is r.BLIND:
                    raise PermissionError("finite-dt gate cannot treat model-bearing inputs as blind metadata")
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


def gate_declaration(kind):
    if kind not in r.GATES:
        raise ValueError("finite-dt source gate is not an installed scientific predicate")
    config_kind = r.MatrixFiniteDtGateConfig
    kinds = input_kinds()
    namespace = r.NAMESPACE
    codecs = {value.SCHEMA: value for value in (*kinds.values(), config_kind, ScientificSourceGateEvidence)}
    return RecursiveOperationDeclaration(namespace + "." + kind.value.lower(), "1.0.0",
        namespace + "." + kind.value.lower() + ".receipt-backed-instrument-v1", CapabilityKind.NUMERICAL_QUALIFIER,
        config_kind, ScientificStage.QUALIFY,
        tuple(RecursivePortContract(name, value.SCHEMA, "application/json", None)
            for name, value in sorted(kinds.items())),
        (OutputTemplate("product", ScientificSourceGateEvidence.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),),
        (CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS),
        EvidenceCeiling.NON_PROMOTABLE, r.BLIND, r.PROSPECTIVE, BUDGET,
        ("finite-dt-instrument-original-controls-and-complete-future-source",), partial(MatrixFiniteDtGateWorker, kind), codecs,
        execution_properties=RecursiveExecutionProperties(runner_preparation_factory=prepare_for_invocation),
        scientific_hooks=RecursiveScientificHooks(scientific_unit_ids=_units,
            scientific_operand_sha256s=_operands,
            scientific_root_validator=scientific_root_validator),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,))


def gate_declarations():
    return tuple(gate_declaration(kind) for kind in r.GATES)


@dataclass(frozen=True, slots=True)
class MatrixFiniteDtSourceCloseoutConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-source/finite-dt-source-closeout-config"
    config_id: str
    products: tuple[ObjectIdentity, ...]
    group_ids: tuple[str, ...]
    resource_budget: ResourceBudget
    standing: str = r.STANDING

    def __post_init__(self):
        validate_stable_id(self.config_id)
        require_sorted_unique_ids(self.products, attribute="object_id", field_name="actual source premise products")
        require_sorted_unique_strings(self.group_ids, field_name="complete source premise units", allow_empty=False)
        if (len(self.products) != len(r.GATES) + 2 or self.standing != r.STANDING
                or type(self.resource_budget) is not ResourceBudget or not BUDGET.contains(self.resource_budget)):
            raise ValueError("finite-dt source closeout changes actual complete premises or scientific ceiling")


class MatrixFiniteDtSourceCloseoutWorker:
    def __init__(self):
        self.manifest = closeout_declaration().manifest()

    def execute(self, context):
        from empirical_lawhood.adapters.methods.matrix_factor_response.protected_prefix_workers import _read
        if type(context) is not TaskContext:
            raise PermissionError("finite-dt closeout requires actual current issued context")
        try:
            context.__post_init__()
            prepared, adjudication = context.prepared_invocation, context.scientific_adjudication_context
            if (type(prepared) is not PreparedInvocationContract or prepared.manifest != self.manifest
                    or adjudication is None or prepared.native_effect
                    or prepared.execution_task_record.stage is not ScientificStage.REPORT
                    or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                    or context.permissions != self.manifest.permissions
                    or len(context.dependency_receipt_ids) != len(r.GATES) + 2):
                raise PermissionError("finite-dt source closeout requires all actual original source producers")
            prepared.validate_context(context)
            contracts = {value.artifact_id: value for value in prepared.inputs}
            config_port, = (value for value in context.input_ports if value.artifact_id == context.config.artifact_id)
            from empirical_lawhood.runtime.input_access import validated_scientific_input_edges
            validated_scientific_input_edges(context, config_port=config_port)
            config = _read(config_port, contracts[config_port.artifact_id], MatrixFiniteDtSourceCloseoutConfig)
            if (config.fingerprint() != context.config.content_sha256 or config.resource_budget != context.resource_budget
                    or len(context.input_ports) != len(r.GATES) + 3):
                raise PermissionError("finite-dt source closeout changes its exact scientific configuration")
            kinds = {kind.SCHEMA: (kind, field) for kind, field in (
                (ScientificSourceGateEvidence, "evidence_id"), (SourcePipelineQualificationReceipt, "receipt_id"),
                (ScientificSourceQualificationResult, "result_id"))}
            actual, qualification = [], None
            for port in context.input_ports:
                if port is config_port:
                    continue
                if port.kind is not WorkerInputKind.DEPENDENCY or port.payload_schema not in kinds:
                    raise PermissionError("finite-dt closeout substitutes an actual source premise producer")
                kind, field = kinds[port.payload_schema]
                product = _read(port, contracts[port.artifact_id], kind)
                actual.append(r.pin(product, field))
                if type(product) is ScientificSourceQualificationResult:
                    if qualification is not None:
                        raise PermissionError("finite-dt source closeout repeats qualification")
                    qualification = product
            if (tuple(sorted(actual, key=lambda value: value.object_id)) != config.products or qualification is None
                    or qualification.complete_physical_unit_count != len(config.group_ids)):
                raise PermissionError("finite-dt source closeout changes original complete source result")
            output, = context.output_ports
            if output.payload_schema != ScientificAdjudicationRecord.SCHEMA or output.output_id != context.task_id + ".product":
                raise PermissionError("finite-dt source closeout changes actual global adjudication")
            reasons = tuple(sorted(("FINITE_DT_INSTRUMENT_SOURCE_" + qualification.disposition.value,
                "FUTURE_NUMERICAL_OUTCOMES_NOT_ASSERTED", "SAMPLING_AND_TRANSPORT_NOT_ESTABLISHED")))
            record = ScientificAdjudicationRecord("adjudication." + context.run_id + "." + context.task_id,
                context.run_id, context.task_id, adjudication.execution_plan, tuple(sorted(context.input_materialization_ids)),
                (output.logical_artifact_id,), context.dependency_receipt_ids, adjudication.evidence_world_id,
                adjudication.evidence_world_kind, adjudication.relation, adjudication.independent_unit_id,
                adjudication.information_cutoffs, adjudication.visibility_ceiling, adjudication.outcome_access,
                AdjudicationEvaluability.UNEVALUABLE, ScientificStatus.UNEVALUABLE, AdmissionStatus.UNEVALUABLE, reasons)
            return RunnerResult((TaskOutputPayload(output.output_id, record.canonical_bytes()),),
                (ReceiptCheck("finite-dt-source-premises-retained-global-qualification-unestablished", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def closeout_declaration():
    ports = tuple((kind.value.lower(), ScientificSourceGateEvidence.SCHEMA) for kind in r.GATES) + (
        ("pipeline", SourcePipelineQualificationReceipt.SCHEMA), ("qualification", ScientificSourceQualificationResult.SCHEMA))
    return RecursiveOperationDeclaration(r.NAMESPACE + ".adjudicate", "1.0.0",
        r.NAMESPACE + ".source-premise-closeout.v1", CapabilityKind.REPORTER,
        MatrixFiniteDtSourceCloseoutConfig, ScientificStage.REPORT,
        tuple(RecursivePortContract(name, schema, "application/json", None) for name, schema in sorted(ports)),
        (OutputTemplate("product", ScientificAdjudicationRecord.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),),
        (CapabilityPermission.READ_DEVELOPMENT, CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
            CapabilityPermission.READ_SEALED_OUTCOMES, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS),
        EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, BUDGET,
        ("finite-dt-source-premises-retained-global-qualification-unestablished",), MatrixFiniteDtSourceCloseoutWorker,
        {kind.SCHEMA: kind for kind in (MatrixFiniteDtSourceCloseoutConfig, ScientificAdjudicationRecord,
            ScientificSourceGateEvidence, SourcePipelineQualificationReceipt, ScientificSourceQualificationResult)},
        scientific_hooks=RecursiveScientificHooks(adjudication_output_id="product"),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,))
