# SPDX-License-Identifier: MPL-2.0
"""Pure ordinary declarations publishing E4 predictions before native futures."""

from empirical_lawhood.runtime.recursive_provider import (
    RecursiveOperationDeclaration, RecursiveScientificHooks, RecursiveExecutionProperties,
)

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.evidence import EvidenceCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.planning.study_authoring import StudyDraft
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskContext, WorkerInputKind
from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract

from . import operation_bindings as core
from .revision_calibration import ScheduledRevisionForecastSeal
from .revision_future_bindings import (
    BLIND, MAXIMUM_RECORD_BYTES, NAMESPACE, PROSPECTIVE, SEAL_CHECK,
    ScheduledRevisionFutureScope, _read_record, forecast_task_id,
)


@dataclass(frozen=True, slots=True)
class ScheduledRevisionForecastConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/revision-forecast-config"
    config_id: str
    scope: ObjectIdentity
    case_id: str
    independent_group_id: str
    forecast_id: str

    def __post_init__(self):
        for value in (self.case_id, self.independent_group_id, self.forecast_id):
            validate_stable_id(value)
        if (self.config_id != "config." + forecast_task_id(self.case_id) or type(self.scope) is not ObjectIdentity
                or (self.scope.object_schema, self.scope.object_version) != (ScheduledRevisionFutureScope.SCHEMA, ScheduledRevisionFutureScope.VERSION)):
            raise ValueError("revision forecast substitutes its exact frozen shared scope or producer task")


def operation_manifests():
    return tuple(row.manifest() for row in operation_declarations())


def scientific_root_validator(config, context):
    if (type(config) is not ScheduledRevisionForecastConfig or context.node_id != forecast_task_id(config.case_id)
            or context.stage is not ScientificStage.FREEZE or context.outcome_access is not BLIND
            or context.visibility_ceiling is not PROSPECTIVE or context.unit_ids != (config.independent_group_id,)):
        raise ValueError("revision forecast changes its blind prediction stage or independent whole group")
    configurations = tuple(row.record for row in context.config_inputs)
    if (not configurations or any(type(row) is not ScheduledRevisionForecastConfig or row.scope != config.scope for row in configurations)
            or len({row.case_id for row in configurations}) != len(configurations)
            or any(sum(row.independent_group_id == group for row in configurations) != 9
                for group in {row.independent_group_id for row in configurations})
            or tuple(sorted({row.independent_group_id for row in configurations})) != context.selected_unit_ids):
        raise ValueError("revision forecast wave omits a full nine-coordinate matched group or changes frozen scope")
    incoming = tuple(row for row in context.links if row.consumer_node_id == context.node_id)
    if len(incoming) != 1 or incoming[0].consumer_input_id != "revision-scope" or incoming[0].external_input_id is None:
        raise ValueError("revision predictor may read only its earlier frozen scope, without future outcomes")
    from .compact_qualification import _qualification
    qualifications = tuple(row for row in context.qualifications if row.source_id == incoming[0].external_input_id)
    if len(qualifications) != 1:
        raise ValueError("revision predictor omits its actual frozen scope source qualification")
    _qualification(context.root, context, qualifications[0].materialization.object_id, config.scope.object_schema,
        config.scope.object_fingerprint, BLIND, PROSPECTIVE, config.scope.object_version)


def operation_registrations():
    return tuple(row.registration() for row in operation_declarations())


class ScheduledRevisionForecaster:
    def __init__(self, selected):
        self.manifest = selected

    def execute(self, context):
        try:
            if (type(context) is not TaskContext or context.permissions != self.manifest.permissions
                    or context.outcome_access is not BLIND or not core.BUDGET.contains(context.resource_budget)
                    or len(context.input_ports) != 2
                    or any(port.kind is not WorkerInputKind.EXTERNAL or port.outcome_access is not BLIND
                        or port.visibility_ceiling is not PROSPECTIVE for port in context.input_ports)):
                raise PermissionError("revision prediction requires the actual issued blind frozen-input context")
            values = {}
            for kind in (ScheduledRevisionForecastConfig, ScheduledRevisionFutureScope):
                ports = tuple(port for port in context.input_ports if port.payload_schema == kind.SCHEMA)
                if len(ports) != 1:
                    raise ValueError("revision prediction omits its exact config/shared frozen input")
                values[kind] = _read_record(ports[0], kind), ports[0]
            config, port = values[ScheduledRevisionForecastConfig]
            scope, _ = values[ScheduledRevisionFutureScope]
            case = next((row for row in scope.programme.cases if row.root_id == config.case_id), None)
            if (scope.identity != config.scope or case is None or case.independent_group_id != config.independent_group_id
                    or context.task_id != forecast_task_id(config.case_id) or context.config.artifact_id != port.artifact_id
                    or context.config.config_id != config.config_id or context.config.config_schema != config.SCHEMA
                    or context.config.content_sha256 != config.fingerprint()):
                raise ValueError("revision prediction changes frozen models, actual case, group or exact configuration")
            forecast = scope.forecast(config.case_id, record_id=config.forecast_id)
            result = core._outputs(context, forecast)
            return RunnerResult(result.outputs, (ReceiptCheck(SEAL_CHECK, True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_factories():
    return tuple(row.provider_factory() for row in operation_declarations())


def revision_forecast_draft(*, root, scope, wave_id, proof_owners, operational_budgets, draft_id, forecast_prefix):
    """Declare a complete pure seal wave before a separate native acquisition.

    The supplied root and ordinary source qualifications retain their existing
    authority requirements. Outputs of this wave become actual prior external
    publications of the later acquisition; no receipt is synthesized here.
    """
    if type(root) is not StudyDraft or type(scope) is not ScheduledRevisionFutureScope:
        raise TypeError("revision forecast composition needs its real prospective root and frozen future scope")
    scope.__post_init__()
    wave = next((row for row in scope.programme.waves if row.wave_id == wave_id), None)
    if wave is None:
        raise ValueError("revision forecast wave is outside the actual frozen programme")
    registration, = operation_registrations()
    scope_id = "external." + scope.record_id
    external = RecursiveExternalInput(scope_id, scope.record_id, scope.SCHEMA, "application/json", len(scope.canonical_bytes()),
        BLIND, PROSPECTIVE, scope.fingerprint(), "SOURCE")
    operations, links = [], []
    scope_pin = scope.identity
    for case in scope.programme.cases:
        if case.root_id not in wave.root_ids:
            continue
        task = forecast_task_id(case.root_id)
        config = ScheduledRevisionForecastConfig("config." + task, scope_pin, case.root_id,
            case.independent_group_id, forecast_prefix + "." + case.root_id)
        owners = tuple(owner for owner, node in proof_owners if node == task)
        budget = operational_budgets.get(task)
        if not owners or budget is None or not core.BUDGET.contains(budget):
            raise ValueError("revision forecast wave omits explicit proof owners or contained operational budgets")
        operations.append(RecursiveOperationSpec.from_config(node_id=task, selection=registration.selection,
            config_id=config.config_id, config=config, obligation_ids=owners, resource_budget=budget))
        links.append(RecursiveInputLink("edge." + task + ".revision-scope", task, "revision-scope",
            external_input_id=scope_id, scientific_role="SOURCE"))
    tasks = tuple(sorted(row.node_id for row in operations))
    if set(operational_budgets) != set(tasks) or {node for _, node in proof_owners} != set(tasks):
        raise ValueError("revision forecast wave changes its complete explicit task/owner/budget census")
    return RecursiveStudyDraft(draft_id, root.question, root.campaign, (), (), (),
        tuple(sorted(operations, key=lambda row: row.node_id)), (external,),
        tuple(sorted(links, key=lambda row: row.edge_id)), tasks, prospective_draft=root), {scope.record_id: scope}


def operation_declarations():
    selected = RecursiveOperationDeclaration(
        capability_key=NAMESPACE + "." + 'seal',
        capability_version="1.0.0",
        implementation_id=NAMESPACE + '.physical-grid-frozen-model-prediction',
        kind=CapabilityKind.TRANSFORM,
        config_record_type=ScheduledRevisionForecastConfig,
        stage=ScientificStage.FREEZE,
        input_ports=(RecursivePortContract('revision-scope', ScheduledRevisionFutureScope.SCHEMA, 'application/json', MAXIMUM_RECORD_BYTES),),
        outputs=(OutputTemplate('product', ScheduledRevisionForecastSeal.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'),),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_FROZEN_MODELS))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=BLIND,
        visibility_ceiling=PROSPECTIVE,
        resources=core.BUDGET,
        conformance_check_ids=tuple(sorted(('complete-assigned-whole-group-case-census', 'frozen-development-models-only', 'revision-seal-before-native-futures'))),
        runner_factory=lambda: ScheduledRevisionForecaster(selected.manifest()),
        record_codecs={ScheduledRevisionForecastSeal.SCHEMA: ScheduledRevisionForecastSeal},
        scientific_hooks=RecursiveScientificHooks(scientific_unit_ids=lambda config: (config.independent_group_id,), scientific_root_validator=scientific_root_validator),
        execution_properties=RecursiveExecutionProperties(barrier=BarrierKind.FREEZE),
        input_record_types=(ScheduledRevisionFutureScope,),
    )
    return (selected,)
