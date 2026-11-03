# SPDX-License-Identifier: MPL-2.0
"""One native forecast or two-trace comparison per ordinary scheduled task.

The scientific roster is unchanged. Equal physical recipe conditions have
explicit DERIVED reuse products rather than repeated native effect slots.
Unknown historical primitive contact always refuses before native entry.
"""

from functools import partial
from empirical_lawhood.runtime.recursive_provider import (RecursiveOperationDeclaration,RecursiveExecutionProperties,RecursiveInquiryHooks,RecursiveScientificHooks)

from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c, science
from empirical_lawhood.adapters.methods.battery_refined_inquiry import preparation_contracts as pc, preparation_science as ps
from empirical_lawhood.adapters.methods.battery_refined_inquiry import prepared_qualification as pq, durable_roster as dr
from empirical_lawhood.adapters.methods.battery_refined_inquiry.operation_bindings import SourcePolicyAdmission, source_policy_admission, history_type
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile, CanonicalTaskReceipt, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract

NAMESPACE = "battery-durable-inquiry"
QUESTION = "Do complete source-bound, independently assessed preparations and numerical comparisons supply a dependable conditional charging description?"
OPERATIONS = ("assess", "compare", "forecast", "qualify", "reuse", "validate")
MEDIA = "application/json"
BUDGET = ResourceBudget(1, None, 0, None, None, None)
NATIVE_OUTPUTS = tuple(sorted((
    ("trace", c.Trace), ("protocol", pc.PreparationProtocol),
    ("witness", pc.InitialElectrodePreparationWitness), ("layout", pc.ProcessedInitialStateLayout),
    *((name, pc.StateObservation) for name in ("requested-initial", "actual-initial", "initial-derivative", "actual-terminal", "terminal-derivative")),
    ("native-receipt", CanonicalTaskReceipt),
)))


@dataclass(frozen=True, slots=True)
class DurableOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-durable-inquiry/operation-config"
    config_id: str
    operation: str
    index: int | None
    source: c.RefinedSource
    policy: c.NumericalPolicy
    roster: ObjectIdentity
    uncertain_work: ObjectIdentity
    producing_provenance: ObjectIdentity
    preparation_protocols: tuple[ObjectIdentity, ...]
    history_artifact_id: str

    def __post_init__(self):
        validate_stable_id(self.config_id)
        validate_stable_id(self.history_artifact_id)
        if self.operation not in OPERATIONS or self.config_id != "config." + node_id(self.operation, self.index):
            raise ValueError("durable operation changes its exact task identity")
        if self.source.policy != c.identity(self.policy) or not self.policy.tolerance_probe:
            raise ValueError("durable operation changes its selected complete54 source/policy")
        if self.source.diagnostic.object_schema != "empirical-lawhood/battery-diagnostic-obstruction/assessment":
            raise ValueError("durable successor requires explicit authentic unknown-completion history")
        expected = dr.freeze_forecast_roster(self.source, self.policy)
        if self.roster != ObjectIdentity.from_record(expected.roster_id, expected):
            raise ValueError("durable operation changes its actual complete frozen roster")
        if (self.uncertain_work.object_schema != dr.UnknownDiagnosticWork.SCHEMA
                or self.producing_provenance.object_schema != NumericalProducingProvenance.SCHEMA
                or len(self.preparation_protocols) != len(dr.distinct_forecast_groups(expected))
                or any(row.object_schema != pc.PreparationProtocol.SCHEMA for row in self.preparation_protocols)
                or len(set(row.object_id for row in self.preparation_protocols)) != len(self.preparation_protocols)):
            raise ValueError("durable operation omits its authentic history/provenance/protocol operands")
        if self.operation in {"validate", "qualify"}:
            if self.index is not None:
                raise ValueError("aggregate operation has no forecast/pair ordinal")
        elif type(self.index) is not int or not 0 <= self.index < (36 if self.operation == "compare" else 54):
            raise ValueError("durable operation changes its scientific ordinal")
        elif self.operation != "compare":
            representative = representative_index(expected, self.index)
            if (self.operation == "reuse") != (representative != self.index):
                raise ValueError("durable operation disguises an equal-condition reuse as native contact")

    @property
    def operands(self):
        roster = dr.freeze_forecast_roster(self.source, self.policy)
        return tuple(sorted((c.identity(self.source), c.identity(self.policy),
            ObjectIdentity.from_record("selection." + self.policy.policy_id, self.policy.selection),
            self.source.diagnostic, self.roster, self.uncertain_work, self.producing_provenance,
            *self.preparation_protocols, *(c.identity(native) for native in roster.configurations)), key=lambda row: row.object_id))


def node_id(operation, index=None):
    return NAMESPACE + "." + operation + ("." + f"{index:03d}" if index is not None else "")


def representative_index(roster, index):
    native = roster.configurations[index]
    primitive = dr.forecast_primitive(native)
    return next(i for i, row in enumerate(roster.configurations) if dr.forecast_primitive(row) == primitive)


def summary_node(roster, index):
    return node_id("assess" if representative_index(roster, index) == index else "reuse", index)


def common_inputs(config):
    return (("history", history_type(config.source.diagnostic)), ("policy", c.NumericalPolicy),
        ("producing-provenance", NumericalProducingProvenance), ("roster", dr.FrozenForecastRoster),
        ("selection", c.NumericalSelection), ("source", c.RefinedSource), ("uncertain-work", dr.UnknownDiagnosticWork))


def internal_inputs(config):
    if config.operation == "validate":
        return ()
    if config.operation == "forecast":
        return (("admission", SourcePolicyAdmission), ("entry", dr.ForecastEntryDisposition))
    if config.operation == "assess":
        return NATIVE_OUTPUTS
    if config.operation == "reuse":
        return (("summary", pq.PreparedTraceSummary),)
    if config.operation == "compare":
        return (("left-summary", pq.PreparedTraceSummary), ("left-trace", c.Trace),
            ("right-summary", pq.PreparedTraceSummary), ("right-trace", c.Trace))
    return tuple(("summary-" + f"{i:03d}", pq.PreparedTraceSummary) for i in range(54)) + tuple(
        ("comparison-" + f"{i:03d}", pq.PreparedComparisonSummary) for i in range(36))


def operation_inputs(operation):
    # Registrations carry the same port census for each operation ordinal.
    if operation == "validate":
        return ()
    if operation == "forecast":
        return (("admission", SourcePolicyAdmission), ("entry", dr.ForecastEntryDisposition), ("native-config", c.NativeConfig), ("selected-protocol", pc.PreparationProtocol))
    if operation == "assess":
        return NATIVE_OUTPUTS
    if operation == "reuse":
        return (("summary", pq.PreparedTraceSummary),)
    if operation == "compare":
        return (("left-summary", pq.PreparedTraceSummary), ("left-trace", c.Trace), ("right-summary", pq.PreparedTraceSummary), ("right-trace", c.Trace))
    return tuple(("summary-" + f"{i:03d}", pq.PreparedTraceSummary) for i in range(54)) + tuple(
        ("comparison-" + f"{i:03d}", pq.PreparedComparisonSummary) for i in range(36))


def operation_outputs(operation):
    if operation == "validate":
        return (("admission", SourcePolicyAdmission),) + tuple(("entry-" + f"{i:03d}", dr.ForecastEntryDisposition) for i in range(54))
    if operation == "forecast":
        return NATIVE_OUTPUTS
    if operation == "assess":
        return (("assessment", pc.InitialPreparationAssessment), ("join", pc.PreparedTraceJoin), ("summary", pq.PreparedTraceSummary))
    if operation == "reuse":
        return (("reuse", dr.ExactConditionReuse), ("summary", pq.PreparedTraceSummary))
    if operation == "compare":
        return (("comparison", pq.PreparedComparisonSummary),)
    return (("qualification", pq.PreparedQualification),)


def operation_stage(operation):
    return ScientificStage.ACQUIRE if operation == "forecast" else ScientificStage.ADMISSION if operation == "validate" else ScientificStage.QUALIFY


def development_root(config, *, study_id):
    scope = c.scope(config.source)
    claim = ClaimSpec("claim." + NAMESPACE, scope.world_id, "population.battery-thermal-inquiry.exposed-lgm50", QUESTION,
        "Complete54 selected conditional forecasts and36 comparisons, including six explicit equal-condition aliases;48 distinct native charging requests.",
        c.UNIT, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        "One existing numerical family; zero fresh physical units. Preparation, precision, later use and physical qualification are separate achievements.",
        ("assumption.exposed-lgm50-model-family",), numerical_view_ids=("view.battery-durable-inquiry.complete-family",))
    return DevelopmentStudySpec(study_id, QUESTION, ObjectIdentity.from_record(scope.system_id, config.source),
        scope.world_id, WorldKind.NUMERICAL_SIMULATOR, (c.UNIT,), ("view.battery-durable-inquiry.complete-family",), (claim,), config.operands)


def native_effect_slot_ids(config):
    if config.operation != "forecast":
        return ()
    native = dr.freeze_forecast_roster(config.source, config.policy).configurations[config.index]
    return ("native.battery-charging." + sha256(dr.forecast_primitive(native)).hexdigest(),)


def scientific_root_validator(config, context):
    if (context.root != development_root(config, study_id=context.root.study_id)
            or context.node_id != node_id(config.operation, config.index) or context.stage is not operation_stage(config.operation)
            or context.unit_ids != (c.UNIT,) or context.selected_unit_ids != (c.UNIT,)
            or context.complete_unit_census != (config.operation == "forecast")):
        raise ValueError("durable operation changes its exact scientific root/stage/unit census")
    from .recursive_translation import validate_graph
    validate_graph(context, config)


def operation_declarations():
    from .recursive_translation import scientific_work
    from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic.contracts import DiagnosticResult
    from empirical_lawhood.adapters.methods.battery_diagnostic_obstruction.contracts import ObstructionAssessment
    registrations = []
    for operation in OPERATIONS:
        inputs = operation_inputs(operation) + (('policy', c.NumericalPolicy), ('selection', c.NumericalSelection), ('source', c.RefinedSource), ('roster', dr.FrozenForecastRoster), ('uncertain-work', dr.UnknownDiagnosticWork), ('producing-provenance', NumericalProducingProvenance), ('history', ObstructionAssessment))
        registrations.append(RecursiveOperationDeclaration(
            capability_key=NAMESPACE + '.' + operation, capability_version='1.0.0',
            implementation_id='prepared-per-forecast-compact-v1.' + operation,
            kind=CapabilityKind.SIMULATOR if operation == 'forecast' else CapabilityKind.ANALYSIS,
            config_record_type=DurableOperationConfig, stage=operation_stage(operation),
            input_ports=tuple((RecursivePortContract(name, record.SCHEMA, MEDIA, None) for name, record in sorted(inputs))),
            outputs=tuple((OutputTemplate(name, record.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA, '.json') for name, record in operation_outputs(operation))),
            permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT))),
            evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
            visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=BUDGET,
            conformance_check_ids=tuple(sorted(('source-bound-complete54-census', 'actual-receipt-independent-preparation', 'uncertain-primitive-no-replay', 'compact-pair-reduction'))),
            runner_factory=partial(DurableRunner, operation), record_codecs=output_codecs(),
            scientific_hooks=RecursiveScientificHooks(
                scientific_operand_sha256s=lambda config: tuple(sorted({row.object_fingerprint for row in config.operands})),
                scientific_unit_ids=lambda config: (c.UNIT,),
                native_effect_slot_ids=native_effect_slot_ids if operation == 'forecast' else None,
                scientific_root_validator=scientific_root_validator,
            ),
            execution_properties=RecursiveExecutionProperties(
                native_effect=operation == 'forecast', complete_unit_census=operation == 'forecast',
            ),
            inquiry_hooks=RecursiveInquiryHooks(
                inquiry_work_projector=scientific_work,
            ),
            additional_input_schema_ids=(DiagnosticResult.SCHEMA,),
        ))
    return tuple(registrations)

def operation_manifests():
    return tuple(row.manifest() for row in operation_declarations())


def operation_registrations():
    return tuple(row.registration() for row in operation_declarations())


def output_codecs():
    from empirical_lawhood.adapters.methods.battery_diagnostic_obstruction.contracts import ObstructionAssessment
    records = {record for operation in OPERATIONS for _, record in (*operation_inputs(operation), *operation_outputs(operation))}
    records.update((DurableOperationConfig, ObstructionAssessment, c.RefinedSource, c.NumericalPolicy, c.NumericalSelection,
        dr.FrozenForecastRoster, dr.UnknownDiagnosticWork, NumericalProducingProvenance))
    return {record.SCHEMA: record for record in records}


def authenticated_native_join(records):
    """Independently authenticate the actual completed native subwork receipt."""
    receipt = records["native-receipt"]
    if type(receipt) is not CanonicalTaskReceipt or receipt.operational_status is not OperationalStatus.SUCCEEDED:
        raise ValueError("preparation requires an actual successful native subwork receipt")
    for name, record_type in NATIVE_OUTPUTS:
        if name == "native-receipt":
            continue
        record = records[name]
        if type(record) is not record_type or sum(row.payload_schema == record.SCHEMA and row.content_sha256 == record.fingerprint()
                for row in receipt.output_logical_artifacts) != 1:
            raise ValueError("native preparation operand differs from its actual producing receipt")
    trace, protocol, witness, layout, requested, actual = (records[name] for name in ("trace", "protocol", "witness", "layout", "requested-initial", "actual-initial"))
    return pc.PreparedTraceJoin("join.prepared." + trace.trace_id, ps.trace_identity(trace), pc.identity(protocol, protocol.protocol_id),
        pc.identity(witness, witness.witness_id), pc.identity(layout, layout.layout_id), pc.identity(requested, requested.observation_id),
        pc.identity(actual, actual.observation_id), receipt.fingerprint())


class DurableRunner:
    def __init__(self, operation):
        if operation not in OPERATIONS:
            raise ValueError("unknown durable battery operation")
        self.operation = operation
        self.manifest = next(row for row in operation_manifests() if row.capability_key == NAMESPACE + "." + operation)

    def execute(self, context):
        return self._execute(context, None)

    def execute_with_native_subwork(self, context, native_subwork):
        return self._execute(context, native_subwork)

    def _execute(self, context, native_subwork):
        from .recursive_translation import input_sources
        try:
            configs = tuple(port for port in context.input_ports if port.payload_schema == DurableOperationConfig.SCHEMA)
            if len(configs) != 1:
                raise ValueError("durable worker requires exactly one immutable operation config")
            config_port = configs[0]
            config = decode_canonical_bytes(config_port.read(), DurableOperationConfig, maximum_bytes=None)
            node = node_id(config.operation, config.index)
            if (self.operation != config.operation or context.task_id != node or context.permissions != self.manifest.permissions
                    or context.resource_budget != BUDGET or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                    or config_port.kind is not WorkerInputKind.EXTERNAL or config_port.artifact_id != context.config.artifact_id
                    or config.fingerprint() != context.config.content_sha256 or config.config_id != context.config.config_id):
                raise ValueError("durable worker substitutes exact task/config/access/resources")
            expected = dict((*common_inputs(config), *operation_inputs(config.operation)))
            sources = input_sources(config)
            decoded = {}
            for name, record_type in expected.items():
                source_kind, artifact = sources[name]
                artifact_id = f"artifact.{context.run_id}.{artifact}" if source_kind == "DEPENDENCY" else artifact
                ports = tuple(port for port in context.input_ports if port.artifact_id == artifact_id)
                if len(ports) != 1:
                    raise ValueError("durable worker omits or substitutes declared input ordinal")
                port = ports[0]
                if (port.kind is not (WorkerInputKind.DEPENDENCY if source_kind == "DEPENDENCY" else WorkerInputKind.EXTERNAL)
                        or port.payload_schema != record_type.SCHEMA or port.media_type != MEDIA
                        or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                        or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
                    raise ValueError("durable worker changes declared typed input/access")
                raw = port.read()
                if len(raw) != port.size_bytes:
                    raise ValueError("durable worker input materialization size differs")
                if source_kind == "DEPENDENCY":
                    producer = artifact.rsplit(".", 1)[0]
                    if not any(receipt.task_id == producer and port.materialization_id in receipt.output_materialization_ids for receipt in context.dependency_receipts):
                        raise ValueError("durable worker loses actual producing dependency receipt")
                decoded[name] = decode_canonical_bytes(raw, record_type, maximum_bytes=None)
            if len(context.input_ports) != len(expected) + 1:
                raise ValueError("durable worker has undeclared inputs")
            expected_producers = {origin.rsplit(".", 1)[0] for kind, origin in sources.values() if kind == "DEPENDENCY"}
            if {receipt.task_id for receipt in context.dependency_receipts} != expected_producers or len(context.dependency_receipts) != len(expected_producers):
                raise ValueError("durable worker changes its exact producing receipt census")
            roster, uncertain, provenance = (decoded[name] for name in ("roster", "uncertain-work", "producing-provenance"))
            if (decoded["source"] != config.source or decoded["policy"] != config.policy or decoded["selection"] != config.policy.selection
                    or c.identity(decoded["history"]) != config.source.diagnostic
                    or ObjectIdentity.from_record(roster.roster_id, roster) != config.roster
                    or ObjectIdentity.from_record(uncertain.record_id, uncertain) != config.uncertain_work
                    or provenance.identity != config.producing_provenance):
                raise ValueError("durable worker changes actual source/history/roster/provenance")
            admission = source_policy_admission(config.source, config.policy, config.policy.selection, decoded["history"])
            history = decoded["history"]
            old_provenance = tuple(member for member in history.source.complete_custody
                if member.relative_path.endswith("/inputs/producing-provenance.json"))
            if (uncertain.original_contact != history.native_contact or not old_provenance
                    or not any(member.sha256 == uncertain.original_producing_source.object_fingerprint for member in old_provenance)):
                raise ValueError("durable unknown-work record substitutes original actual contact/source identity")
            outputs = operation_outputs(config.operation)
            if (tuple((port.output_id, port.payload_schema) for port in context.output_ports) != tuple((node + "." + name, record.SCHEMA) for name, record in outputs)
                    or any(port.profile is not ArtifactProfile.CANONICAL_JSON or port.media_type != MEDIA for port in context.output_ports)):
                raise ValueError("durable worker changes its complete output contract")
            if config.operation == "validate":
                records = (admission, *dr.entry_dispositions(roster, uncertain))
            elif config.operation == "forecast":
                native = roster.configurations[config.index]
                entries = dr.entry_dispositions(roster, uncertain)
                if decoded["admission"] != admission or decoded["entry"] != entries[config.index] or decoded["native-config"] != native:
                    raise ValueError("native forecast substitutes its actual gate/config/primitive disposition")
                dr.require_no_uncertain_primitive(decoded["entry"])
                protocol = decoded["selected-protocol"]
                if (protocol.configuration != c.identity(native) or protocol.source != c.identity(config.source)
                        or protocol.producing_provenance != provenance.identity or pc.identity(protocol, protocol.protocol_id) not in config.preparation_protocols):
                    raise ValueError("native forecast substitutes its actual prospective preparation contract")
                if native_subwork is None:
                    raise ValueError("native forecast requires durable precontact subwork custody")
                from empirical_lawhood.adapters.methods.battery_refined_inquiry import prepared_native
                materializations = tuple(sorted(port.materialization_id for port in context.input_ports))
                definition = prepared_native.build_forecast_definition(native, protocol, provenance, native_subwork, materializations)
                prepared_native.freeze_forecast_roster(native_subwork, (definition,))
                result = prepared_native.acquire_prepared(native, protocol=protocol, provenance=provenance, definition=definition,
                    native_subwork=native_subwork, inputs=None)
                returned = prepared_native.returned_records(result)
                records = tuple(returned[name] for name, _ in outputs)
                if returned["trace"].config != native:
                    raise ValueError("native forecast returns another configured trace")
            elif config.operation == "assess":
                join = authenticated_native_join(decoded)
                native = roster.configurations[config.index]
                from .recursive_translation import protocol_for
                if (decoded["trace"].config != native
                        or pc.identity(decoded["protocol"], decoded["protocol"].protocol_id) != protocol_for(config, config.index)
                        or decoded["protocol"].producing_provenance != provenance.identity):
                    raise ValueError("independent preparation receives another forecast")
                assessment = ps.assess_initial_preparation(decoded["trace"], protocol=decoded["protocol"], witness=decoded["witness"],
                    layout=decoded["layout"], requested_initial=decoded["requested-initial"], actual_initial=decoded["actual-initial"], join=join)
                records = (assessment, join, pq.summarize_trace(decoded["trace"], assessment))
            elif config.operation == "reuse":
                summary = pq.reuse_summary(roster.configurations[config.index], decoded["summary"])
                records = (summary.condition_reuse, summary)
            elif config.operation == "compare":
                left, right = decoded["left-trace"], decoded["right-trace"]
                if ps.trace_identity(left) != decoded["left-summary"].trace or ps.trace_identity(right) != decoded["right-summary"].trace:
                    raise ValueError("independent pair reducer substitutes original trace operands")
                records = (pq.comparison_summary(decoded["left-summary"], decoded["right-summary"], science.compare_reference(left, right)),)
            else:
                records = (pq.qualify_summaries(config.source, config.policy, tuple(decoded["summary-" + f"{i:03d}"] for i in range(54)),
                    tuple(decoded["comparison-" + f"{i:03d}"] for i in range(36))),)
            return RunnerResult(tuple(TaskOutputPayload(port.output_id, record.canonical_bytes()) for port, record in zip(context.output_ports, records, strict=True)),
                (ReceiptCheck("durable-battery-exact-preparation-and-complete-denominator", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()
