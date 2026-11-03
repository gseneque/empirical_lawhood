# SPDX-License-Identifier: MPL-2.0
"""Real selected E4 PURE producers over original acquired source products."""

from dataclasses import dataclass, replace
from functools import partial
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import ParentPreparedTaskRunner, RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_provider import RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks

from . import selected_e3_e4_records as r, selected_e4_programme as p, selected_e4_methods as science
from .selected_e4_adjudication import require_adjudication_context, adjudication_record
from empirical_lawhood.runtime.adjudication import ScientificAdjudicationRecord

NAMESPACE = "matrix-selected-e4"
OPERATIONS = ("revision-fit", "revision-freeze", "revision-calibrate", "factorial-assess",
    "confirmation-assess", "downstream-nominate")
ADJUDICATION_OPERATIONS = ("revision-adjudicate", "downstream-adjudicate")
# Capability ceiling only. Every authored task receives an explicit selected
# reservation; None here is never converted into a finite memory assertion.
CEILING = ResourceBudget(1, None, 0, None, None, None)
DEV, SEALED, BLIND = OutcomeAccess.DEVELOPMENT_VISIBLE, OutcomeAccess.EVALUATION_SEALED, OutcomeAccess.OUTCOME_BLIND
EXPOSED, PROSPECTIVE = VisibilityCeiling.DEVELOPMENT_ONLY, VisibilityCeiling.PROSPECTIVE



@dataclass(frozen=True, slots=True)
class SelectedE4DevelopmentAcquisition(CanonicalRecord):
    """Original authored DEV acquisition locator, without issued authority."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/development-acquisition"
    record_id: str
    authored_directory: str
    run_id: str
    execution_plan: ObjectIdentity
    entry_receipt: ObjectIdentity
    allow_partial: bool

    def __post_init__(self):
        from pathlib import PurePosixPath
        from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan
        validate_stable_id(self.record_id)
        validate_stable_id(self.run_id)
        if (type(self.authored_directory) is not str or not self.authored_directory
                or PurePosixPath(self.authored_directory).is_absolute()
                or any(part in (".", "..") for part in self.authored_directory.split("/"))
                or type(self.allow_partial) is not bool):
            raise ValueError("selected revision requires an exact guarded original DEV directory and partial-read choice")
        r.exact_pin(self.execution_plan, DevelopmentExecutionPlan)
        if type(self.entry_receipt) is not ObjectIdentity:
            raise TypeError("selected revision requires its actual original successful DEV entry receipt")
        self.entry_receipt.__post_init__()

    @property
    def identity(self):
        return r.pin(self)

@dataclass(frozen=True, slots=True)
class SelectedE4ConfirmationScope(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/confirmation-scope"
    record_id: str
    specification: science.SelectedE4ProgrammeSpecification
    revision: p.SelectedE4RevisionExport
    calibration: p.SelectedE4PublicCalibration | None
    factorial: science.SelectedE4FactorialSpecification

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.specification) is not science.SelectedE4ProgrammeSpecification
                or type(self.revision) is not p.SelectedE4RevisionExport
                or type(self.factorial) is not science.SelectedE4FactorialSpecification
                or self.calibration is not None and type(self.calibration) is not p.SelectedE4PublicCalibration):
            raise TypeError("selected CONF scope requires actual frozen scientific choices and public original products")
        for value in (self.specification, self.revision, self.factorial, self.calibration):
            if value is not None:
                value.__post_init__()
        if science.factorial.declared_family(self.factorial) != self.specification.family_ids:
            raise ValueError("selected CONF scope changes the declared primary family")
        if (self.specification.development != self.revision.decision.development
                or self.factorial.programme != self.specification.confirmation
                or (self.revision.models is None) != (self.calibration is None)):
            raise ValueError("selected CONF scope changes frozen DEV branch, criteria or separate CAL ancestry")
        if self.calibration is not None and (self.calibration.specification.frozen_models != self.revision.decision.frozen
                or self.calibration.specification.nomination != self.revision.decision.nomination
                or self.calibration.specification.calibration_programme != self.specification.calibration):
            raise ValueError("selected CONF scope substitutes its actual original calibration")

    @property
    def identity(self):
        return r.pin(self)


@dataclass(frozen=True, slots=True)
class SelectedE4MethodResources(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/method-resources"
    record_id: str
    phase_budgets: tuple[tuple[str, ResourceBudget], ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.phase_budgets) is not tuple or not self.phase_budgets
                or tuple(name for name, _ in self.phase_budgets) != tuple(sorted({name for name, _ in self.phase_budgets}))
                or not {name for name, _ in self.phase_budgets} <= set(OPERATIONS)):
            raise ValueError("selected E4 methods require explicit unique installed phase reservations")
        for _, budget in self.phase_budgets:
            if type(budget) is not ResourceBudget or not CEILING.contains(budget):
                raise ValueError("selected method reservation exceeds its implemented capability")
            budget.__post_init__()

    @property
    def identity(self):
        return r.pin(self)

    def for_operations(self, operations):
        self.__post_init__()
        if tuple(sorted(operations)) != tuple(name for name, _ in self.phase_budgets):
            raise ValueError("selected method reservation selection omits or adds a required phase")
        return dict(self.phase_budgets)


@dataclass(frozen=True, slots=True)
class SelectedE4MethodConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/method-config"
    config_id: str
    operation: str
    programme: ObjectIdentity
    group_ids: tuple[str, ...]
    external_operands: tuple[tuple[str, ObjectIdentity], ...]
    links: tuple[RecursiveInputLink, ...]
    operational_budget: ResourceBudget
    entry_node_id: str | None

    def __post_init__(self):
        if (self.operation not in (*OPERATIONS, *ADJUDICATION_OPERATIONS) or self.config_id != "config." + method_node(self.programme, self.operation)
                or type(self.group_ids) is not tuple or not self.group_ids or self.group_ids != tuple(sorted(set(self.group_ids)))
                or type(self.external_operands) is not tuple
                or tuple(name for name, _ in self.external_operands) != tuple(sorted({name for name, _ in self.external_operands}))
                or type(self.links) is not tuple
                or tuple(link.consumer_input_id for link in self.links) != tuple(sorted({link.consumer_input_id for link in self.links}))
                or type(self.operational_budget) is not ResourceBudget or not CEILING.contains(self.operational_budget)):
            raise ValueError("selected E4 method changes exact task, source census, causal links or selected reservation")
        for group in self.group_ids:
            validate_stable_id(group)
        for _, value in self.external_operands:
            if type(value) is not ObjectIdentity:
                raise TypeError("selected E4 method source pins need exact canonical identities")
            value.__post_init__()
        expected = input_types(self.operation)
        if set(expected) != {link.consumer_input_id for link in self.links}:
            raise ValueError("selected method omits an exact declared scientific input")
        for link in self.links:
            link.__post_init__()
            if link.consumer_node_id != method_node(self.programme, self.operation):
                raise ValueError("selected method link points at another consumer")
        external = {link.consumer_input_id for link in self.links if link.external_input_id is not None}
        if external != {name for name, _ in self.external_operands}:
            raise ValueError("selected method pins do not bind the exact external scientific input census")
        development = self.operation in ("revision-fit", "revision-freeze")
        if development:
            r.exact_pin(self.programme, r.SelectedE3E4DevelopmentProgramme)
            if self.entry_node_id is not None:
                raise ValueError("truthful selected DEV does not manufacture issued entry authority")
        else:
            r.exact_pin(self.programme, p.SelectedE4PhaseProgramme)
            validate_stable_id(self.entry_node_id)
            entry = next(link for link in self.links if link.consumer_input_id == "entry")
            if (entry.producer_node_id, entry.producer_output_id, entry.external_input_id) != (self.entry_node_id, "product", None):
                raise ValueError("selected protected method bypasses its actual direct entry seal")


def method_node(programme, operation):
    if operation not in (*OPERATIONS, *ADJUDICATION_OPERATIONS) or type(programme) is not ObjectIdentity:
        raise ValueError("unknown selected E4 method or programme")
    return NAMESPACE + "." + operation + "." + programme.object_fingerprint


def input_types(operation):
    if operation == "revision-fit":
        return {"programme": r.SelectedE3E4DevelopmentProgramme, "bank": r.SelectedE3E4DevelopmentBank,
            "acquisition": SelectedE4DevelopmentAcquisition, "specification": science.SelectedE4RevisionSpecification, "reduction": r.SelectedE3E4DevelopmentReduction,
            "data": p.SelectedE4ObservedData}
    if operation == "revision-freeze":
        return {"programme": r.SelectedE3E4DevelopmentProgramme, "specification": science.SelectedE4RevisionSpecification,
            "nomination": science.SelectedE4RevisionNomination}
    from .selected_e4_native_records import SelectedE4NativeReduction, SelectedE4ProtectedEntrySeal
    common = {"entry": SelectedE4ProtectedEntrySeal, "programme": p.SelectedE4PhaseProgramme}
    if operation == "revision-adjudicate":
        return {**common, "calibration": science.SelectedE4Calibration}
    if operation == "downstream-adjudicate":
        return {**common, "scope": SelectedE4ConfirmationScope, "confirmation": science.SelectedE4Confirmation,
            "downstream": science.SelectedE4DownstreamNomination}
    if operation == "downstream-nominate":
        return {**common, "scope": SelectedE4ConfirmationScope, "confirmation": science.SelectedE4Confirmation}
    acquisition = {**common, "bank": p.SelectedE4PhaseBank, "reduction": SelectedE4NativeReduction, "data": p.SelectedE4ObservedData}
    if operation == "revision-calibrate":
        return {**acquisition, "specification": p.SelectedE4CalibrationSpecification, "revision": p.SelectedE4RevisionExport,
            "forecasts": p.SelectedE4ForecastBank}
    if operation == "factorial-assess":
        return {**acquisition, "specification": science.SelectedE4FactorialSpecification}
    if operation == "confirmation-assess":
        return {**acquisition, "scope": SelectedE4ConfirmationScope, "forecasts": p.SelectedE4ForecastBank,
            "factorial": science.SelectedE4FactorialAssessment}
    raise ValueError("unknown selected E4 PURE method")


def output_types(operation):
    return {"revision-fit": {"product": science.SelectedE4RevisionNomination},
        "revision-freeze": {"product": science.SelectedE4FrozenRevision, "public": p.SelectedE4RevisionExport},
        "revision-calibrate": {"product": science.SelectedE4Calibration, "public": p.SelectedE4PublicCalibration},
        "factorial-assess": {"product": science.SelectedE4FactorialAssessment},
        "confirmation-assess": {"product": science.SelectedE4Confirmation},
        "downstream-nominate": {"product": science.SelectedE4DownstreamNomination},
        "revision-adjudicate": {"adjudication": ScientificAdjudicationRecord},
        "downstream-adjudicate": {"adjudication": ScientificAdjudicationRecord}}[operation]


def scientific_root_validator(config, context):
    declaration = next(row for row in operation_declarations() if row.capability_key == NAMESPACE + "." + config.operation)
    if (context.node_id != method_node(config.programme, config.operation) or context.stage is not declaration.stage
            or context.unit_ids != config.group_ids or context.selected_unit_ids != config.group_ids):
        raise ValueError("selected method changes declared phase, complete independent units or frozen reservation")
    incoming = tuple(sorted((link for link in context.links if link.consumer_node_id == context.node_id),
        key=lambda link: link.consumer_input_id))
    if incoming != config.links:
        raise ValueError("selected method substitutes scientific dependencies or bypasses forecast/entry ordering")
    if config.entry_node_id is None:
        from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
        if (type(context.root) is not DevelopmentStudySpec or context.root.system != config.programme
                or context.root.assigned_unit_ids != config.group_ids):
            raise ValueError("selected revision fitting requires its actual truthful DEV root")
        methods = tuple(value.record for value in context.config_inputs if type(value.record) is SelectedE4MethodConfig)
        fits = tuple(value for value in methods if value.operation == "revision-fit")
        if (len(methods) != 2 or {value.operation for value in methods} != {"revision-fit", "revision-freeze"}
                or any(value.programme != config.programme or value.group_ids != config.group_ids for value in methods)
                or len(fits) != 1 or set(context.root.scientific_operands) != {pin for _, pin in fits[0].external_operands}):
            raise ValueError("selected DEV root changes its complete original acquisition/method operands")
        if (context.outcome_access is not DEV or context.visibility_ceiling is not EXPOSED or context.complete_unit_census):
            raise ValueError("selected DEV method cannot relabel outcomes or manufacture issue authority")
    else:
        from .selected_e4_native_bindings import validate_selected_e4_root_scope
        validate_selected_e4_root_scope(programme=config.programme, group_ids=config.group_ids, context=context)


def _scope(context):
    from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract
    prepared = context.prepared_invocation
    if type(prepared) is not PreparedInvocationContract:
        raise PermissionError("selected E4 method requires its complete actual prepared invocation")
    prepared.require_complete()
    prepared.validate_context(context)
    return (context.run_id, context.task_id, context.input_materialization_ids, prepared.execution_plan)


class SelectedE4MethodWorker:
    def __init__(self, operation, *, prepared_scope=None, manifest=None):
        self.operation, self.prepared_scope = operation, prepared_scope
        self.manifest = manifest or next(row.manifest() for row in operation_declarations() if row.capability_key == NAMESPACE + "." + operation)

    def with_prepared_scope(self, scope):
        return type(self)(self.operation, prepared_scope=scope, manifest=self.manifest)

    def _read(self, context):
        if self.operation in ADJUDICATION_OPERATIONS:require_adjudication_context(context, self.manifest)
        if (self.prepared_scope != _scope(context) or context.permissions != self.manifest.permissions
                or not self.manifest.resource_ceiling.contains(context.resource_budget)):
            raise PermissionError("selected E4 method lacks fresh actual parent custody preparation")
        if context.prepared_invocation.manifest != self.manifest or context.prepared_invocation.native_effect:
            raise ValueError("selected PURE method changes its actual sealed manifest or native classification")
        kinds = {"config": SelectedE4MethodConfig, **input_types(self.operation)}
        contracts = {value.artifact_id: value for value in context.prepared_invocation.inputs}
        by_schema = {}
        for name, kind in kinds.items():
            by_schema.setdefault(kind.SCHEMA, []).append((name, kind))
        records = {}
        for port in context.input_ports:
            choices = by_schema.get(port.payload_schema, ())
            if len(choices) != 1 or port.media_type != "application/json":
                raise ValueError("selected E4 method receives undeclared or ambiguous scientific record")
            name, kind = choices[0]
            if name in records:
                raise ValueError("selected E4 method repeats an input record")
            cursor = port.cursor()
            try:
                raw = cursor.read()
            finally:
                cursor.close()
            contract = contracts.get(port.artifact_id)
            if (contract is None or len(raw) != port.size_bytes
                    or sha256(raw).hexdigest() != contract.logical.content_sha256):
                raise ValueError("selected E4 method changes exact custody-bound materialized input bytes")
            record = decode_canonical_bytes(raw, kind, maximum_bytes=None)
            if name == "config" and (port.kind is not WorkerInputKind.EXTERNAL or port.artifact_id != context.config.artifact_id):
                raise ValueError("selected method substitutes its exact current external config")
            records[name] = record
        if set(records) != set(kinds):
            raise ValueError("selected method omits an exact declared source or product")
        config = records.pop("config")
        if (config.operation != self.operation or context.task_id != method_node(config.programme, self.operation)
                or context.config.config_id != config.config_id or context.config.config_schema != config.SCHEMA
                or context.config.content_sha256 != config.fingerprint() or context.resource_budget != config.operational_budget
                or records["programme"].identity != config.programme or records["programme"].group_ids != config.group_ids):
            raise ValueError("selected E4 method substitutes actual config/programme or frozen reservation")
        for name, pin in config.external_operands:
            if record_identity(records[name]) != pin:
                raise ValueError("selected method substitutes an original external scientific operand")
        if config.entry_node_id is not None:
            entry = records["entry"]
            if entry.programme != config.programme or entry.groups != config.group_ids:
                raise ValueError("selected method changes actual successful source-entry scope")
        return config, records

    def preflight(self, context):
        self._read(context)

    def execute(self, context):
        try:
            return self._execute(context)
        finally:
            for port in context.input_ports:
                port.close()

    def _execute(self, context):
        config, records = self._read(context)
        programme = records["programme"]
        product_id = "product." + context.task_id
        if self.operation == "revision-adjudicate":
            calibration = records["calibration"]
            if (calibration.specification.calibration_programme != programme.identity
                    or calibration.group_ids != programme.group_ids):
                raise ValueError("selected E4 adjudication changes the actual complete original CAL product")
            reasons = {"ORIGINAL_CALIBRATION_RETAINED", "SCIENTIFIC_QUALIFICATION_NOT_ESTABLISHED",
                "CONDITIONAL_REVISION_RADIUS_UNBOUNDED" if calibration.revision_radius is None else "CONDITIONAL_REVISION_RADIUS_FINITE"}
            products = {"adjudication": adjudication_record(context, self.manifest, reasons)}
        elif self.operation == "downstream-adjudicate":
            scope, confirmation, downstream = (records[name] for name in ("scope", "confirmation", "downstream"))
            expected = science.nominate_downstream(scope.specification, confirmation, scope.revision,
                scope.calibration, record_id=downstream.record_id)
            if (scope.specification.confirmation != programme.identity
                    or confirmation.factorial_assessment.programme != programme.identity
                    or tuple(value.independent_group_id for value in confirmation.groups) != programme.group_ids
                    or downstream != expected):
                raise ValueError("selected E4 adjudication changes actual complete CONF or downstream nomination")
            reasons = {"CONDITIONAL_E4_PROGRAMME_RETAINED", "SCIENTIFIC_QUALIFICATION_NOT_ESTABLISHED",
                confirmation.assumption_status, confirmation.standing,
                "DOWNSTREAM_SELECTED_" + (downstream.selected or "NONE")}
            reasons.update(name + "_" + disposition for name, disposition in downstream.dispositions)
            products = {"adjudication": adjudication_record(context, self.manifest, reasons)}
        elif self.operation == "revision-fit":
            products = {"product": science.select_revision(records["specification"], programme, records["bank"],
                records["reduction"], records["data"], nomination_id=product_id)}
        elif self.operation == "revision-freeze":
            if records["nomination"].specification != records["specification"]:
                raise ValueError("selected freeze substitutes its actual original fitting specification")
            frozen = science.freeze_revision(programme, records["nomination"], freeze_id=product_id)
            products = {"product": frozen, "public": p.SelectedE4RevisionExport.from_products(
                programme, records["nomination"], frozen, record_id=product_id + ".public")}
        elif self.operation == "revision-calibrate":
            calibration = science.calibrate_revision_public(records["specification"], records["revision"], programme,
                records["bank"], records["reduction"], records["data"], records["forecasts"], record_id=product_id)
            products = {"product": calibration, "public": p.SelectedE4PublicCalibration.from_calibration(
                calibration, record_id=product_id + ".public")}
        elif self.operation == "factorial-assess":
            products = {"product": science.assess_factorial(records["specification"], programme, records["bank"],
                records["reduction"], records["data"], assessment_id=product_id)}
        elif self.operation == "confirmation-assess":
            scope = records["scope"]
            if records["factorial"].specification != scope.factorial:
                raise ValueError("selected CONF calculation changes its pre-outcome factorial criterion")
            products = {"product": science.assess_confirmation_public(scope.specification, programme, records["bank"],
                scope.revision, scope.calibration, records["reduction"], records["data"], records["forecasts"],
                records["factorial"], record_id=product_id)}
        else:
            scope = records["scope"]
            products = {"product": science.nominate_downstream(scope.specification, records["confirmation"],
                scope.revision, scope.calibration, record_id=product_id)}
        expected = output_types(self.operation)
        if set(products) != set(expected) or any(type(products[name]) is not kind for name, kind in expected.items()):
            raise ValueError("selected method changes its exact scientific output family")
        expected_ports = {context.task_id + "." + name: kind for name, kind in expected.items()}
        if (len(context.output_ports) != len(expected_ports)
                or any(port.output_id not in expected_ports or port.payload_schema != expected_ports[port.output_id].SCHEMA
                    or port.profile is not ArtifactProfile.CANONICAL_JSON or port.media_type != "application/json" for port in context.output_ports)):
            raise ValueError("selected method changes its exact canonical output ports")
        return RunnerResult(tuple(TaskOutputPayload(context.task_id + "." + name, record.canonical_bytes())
            for name, record in sorted(products.items())), (ReceiptCheck("selected-e4-complete-original-scientific-products", True, ()),))


def record_identity(record):
    value = getattr(record, "identity", None)
    return value if type(value) is ObjectIdentity else ObjectIdentity.from_record(
        getattr(record, "record_id", getattr(record, "reduction_id", None)), record)


def prepare_for_invocation(supplier, runner):
    callback = getattr(supplier, "prepare_selected_e4_method", None)
    if not callable(callback):
        raise PermissionError("selected E4 PURE method requires original DEV acquisition or issued source custody preparation")
    return ParentPreparedTaskRunner(runner.manifest, partial(callback, runner=runner))


def operation_declarations():
    stages = {"revision-fit": ScientificStage.DEVELOP, "revision-freeze": ScientificStage.FREEZE,
        "revision-calibrate": ScientificStage.TRANSFORM, "factorial-assess": ScientificStage.FALSIFY,
        "confirmation-assess": ScientificStage.FALSIFY, "downstream-nominate": ScientificStage.FALSIFY,
        "revision-adjudicate": ScientificStage.EVALUATE, "downstream-adjudicate": ScientificStage.EVALUATE}
    rows = []
    for operation in (*OPERATIONS, *ADJUDICATION_OPERATIONS):
        development = operation in ("revision-fit", "revision-freeze")
        adjudicating = operation in ADJUDICATION_OPERATIONS
        inputs, outputs = input_types(operation), output_types(operation)
        permissions = [CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS]
        permissions.append(CapabilityPermission.READ_DEVELOPMENT)
        if not development:
            permissions.append(CapabilityPermission.READ_SEALED_OUTCOMES)
        if adjudicating:permissions.append(CapabilityPermission.REVEAL_OUTCOMES)
        kinds = {SelectedE4MethodConfig, *inputs.values(), *outputs.values()}
        rows.append(RecursiveOperationDeclaration(NAMESPACE + "." + operation, "1.0.0",
            NAMESPACE + "." + operation + ".actual-selected-products.v1", CapabilityKind.EVALUATOR if adjudicating else CapabilityKind.ANALYSIS if stages[operation] is ScientificStage.DEVELOP else CapabilityKind.FALSIFIER if stages[operation] is ScientificStage.FALSIFY else CapabilityKind.TRANSFORM,
            SelectedE4MethodConfig, stages[operation],
            tuple(RecursivePortContract(name, kind.SCHEMA, "application/json", None) for name, kind in sorted(inputs.items())),
            tuple(OutputTemplate(name, kind.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json")
                for name, kind in sorted(outputs.items())),
            tuple(sorted(permissions)), EvidenceCeiling.NON_PROMOTABLE if development else EvidenceCeiling.RESPONSE,
            DEV if development else OutcomeAccess.EVALUATOR_REVEAL if adjudicating else SEALED,
            EXPOSED if development else VisibilityCeiling.OUTCOME_VISIBLE if adjudicating else PROSPECTIVE, CEILING,
            ("actual-selected-e4-source-model-target-census", "whole-group-all30-complete-adverse-denominators"),
            partial(SelectedE4MethodWorker, operation), {kind.SCHEMA: kind for kind in kinds},
            scientific_hooks=RecursiveScientificHooks(scientific_unit_ids=lambda config: config.group_ids,
                scientific_root_validator=scientific_root_validator, adjudication_output_id="adjudication" if adjudicating else None),
            execution_properties=RecursiveExecutionProperties(runner_preparation_factory=prepare_for_invocation,
                barrier=BarrierKind.REVEAL if adjudicating else BarrierKind.FREEZE if operation == "revision-freeze" else BarrierKind.NONE),
            input_record_types=tuple(sorted(set(inputs.values()), key=lambda kind: (kind.SCHEMA, kind.VERSION))),
            provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,)))
    return tuple(sorted(rows, key=lambda row: row.capability_key))


def operations_for_programme(programme):
    return {"E4_DEVELOPMENT": ("revision-fit", "revision-freeze"),
        "E4_REVISION_CALIBRATION": ("revision-calibrate",),
        "E4_CONFIRMATION": ("factorial-assess", "confirmation-assess", "downstream-nominate")}[programme.mode]


def adjudication_operation(programme):
    return {"E4_REVISION_CALIBRATION": "revision-adjudicate", "E4_CONFIRMATION": "downstream-adjudicate"}.get(programme.mode)


def method_rows(programme, *, operands, connections, resources, entry_node_id):
    operations = operations_for_programme(programme)
    if type(resources) is not SelectedE4MethodResources:
        raise TypeError("selected E4 methods require explicit typed operational phase reservations")
    budgets = resources.for_operations(operations)
    terminal = adjudication_operation(programme)
    if terminal is not None:
        budgets[terminal] = budgets[operations[-1]]
        operations = (*operations, terminal)
    declarations = {row.capability_key.rsplit(".", 1)[-1]: row for row in operation_declarations()}
    records, external_inputs, links, tasks = {}, {}, [], []
    produced = {"nomination": (method_node(programme.identity, "revision-fit"), "product"),
        "factorial": (method_node(programme.identity, "factorial-assess"), "product"),
        "confirmation": (method_node(programme.identity, "confirmation-assess"), "product"),
        "calibration": (method_node(programme.identity, "revision-calibrate"), "product"),
        "downstream": (method_node(programme.identity, "downstream-nominate"), "product")}
    for operation in operations:
        node, incoming, external_pins = method_node(programme.identity, operation), [], []
        for name in input_types(operation):
            current = connections.get(name)
            if name == "entry":
                current = (entry_node_id, "product")
            elif name in produced and name not in operands:
                current = produced[name]
            if current is not None:
                producer, output = current
                link = RecursiveInputLink("edge." + node + "." + name, node, name, producer, output, None, "MODEL" if name in ("nomination", "forecasts") else "HISTORY")
            else:
                record = programme if name == "programme" else operands.get(name)
                if type(record) is not input_types(operation)[name]:
                    raise TypeError("selected E4 method needs exact original operand " + name)
                pin = record_identity(record)
                external_id = "external.selected-e4." + pin.object_fingerprint + "." + name
                if records.setdefault(external_id, record) != record:
                    raise ValueError("selected E4 source identity aliases different exact records")
                development = programme.mode == "E4_DEVELOPMENT"
                external_inputs[external_id] = RecursiveExternalInput(external_id, "input." + external_id, record.SCHEMA,
                    "application/json", len(record.canonical_bytes()), DEV if development else BLIND,
                    EXPOSED if development else PROSPECTIVE, record.fingerprint())
                external_pins.append((name, pin))
                link = RecursiveInputLink("edge." + node + "." + name, node, name, None, None, external_id, "SOURCE")
            incoming.append(link)
        config = SelectedE4MethodConfig("config." + node, operation, programme.identity, programme.group_ids,
            tuple(sorted(external_pins)), tuple(sorted(incoming, key=lambda row: row.consumer_input_id)), budgets[operation], entry_node_id)
        declaration = declarations[operation]
        tasks.append(RecursiveOperationSpec.from_config(node_id=node, selection=declaration.registration().selection,
            config_id=config.config_id, config=config, obligation_ids=("obligation." + node + ".complete-selected-science",),
            resource_budget=budgets[operation]))
        links.extend(incoming)
    return tuple(tasks), tuple(links), tuple(sorted(records.items())), tuple(sorted(external_inputs.values(), key=lambda row: row.input_id))


def lower_selected_e4_methods(draft, *, programme, operands, connections, resources, entry_node_id):
    """Append the mandatory PURE phase tail to the existing native graph."""
    if programme.mode == "E4_DEVELOPMENT" or entry_node_id not in {row.node_id for row in draft.operations}:
        raise ValueError("protected selected E4 methods require the actual native graph and direct current entry")
    tasks, links, records, external = method_rows(programme, operands=operands, connections=connections,
        resources=resources, entry_node_id=entry_node_id)
    if {row.node_id for row in tasks} & {row.node_id for row in draft.operations}:
        raise ValueError("selected E4 tail repeats an original operation")
    joined = {row.input_id: row for row in draft.external_inputs}
    for row in external:
        if joined.setdefault(row.input_id, row) != row:
            raise ValueError("selected E4 tail changes an original external source")
    return replace(draft, operations=tuple(sorted((*draft.operations, *tasks), key=lambda row: row.node_id)),
        links=tuple(sorted((*draft.links, *links), key=lambda row: row.edge_id)),
        external_inputs=tuple(sorted(joined.values(), key=lambda row: row.input_id)),
        selected_operation_ids=tuple(sorted({*draft.selected_operation_ids, *(task.node_id for task in tasks)}))), records
