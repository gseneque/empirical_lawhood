# SPDX-License-Identifier: MPL-2.0
"""An earlier E4 prediction publication gates unchanged native future work.

This additive capability keeps the original mathematical configuration, task and
native subwork identities. Prior publications are external inputs with actual
custody; they are never represented as same-wave dependency receipts. Public
entry must replay their original issue/source/publication custody before issue.
"""


from dataclasses import dataclass, replace
from typing import ClassVar

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveStudyDraft
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult, CanonicalTaskReceipt
from empirical_lawhood.runtime.execution import TaskContext, WorkerInputKind
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract
from empirical_lawhood.runtime.plans import ExecutionTask
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding

from . import operation_bindings as core, programme_acquisition_bindings as acquisition, response_bindings as response
from .commitment import require_publication_copy
from .compact_records import NAMESPACE as COMPACT_NAMESPACE
from .programme_records import ScheduledProgramme
from .programme_selection import ScheduledRevisionFrozenPackage, ScheduledRevisionNomination
from .programme_workflow import ScheduledE4NominationRule
from .records import _publication
from .revision_calibration import ScheduledRevisionForecastSeal, _forecast_pins, _forecast_revision_case, validate_revision_phase
from .revision_public import ScheduledRevisionPublicCalibration, validate_public_revision_calibration

NAMESPACE = "matrix-scheduled-revision-future"
ROLES = ("continue", "responses")
MAXIMUM_RECORD_BYTES = 16 * 1024**2
SEAL_CHECK = "e4-revision-frozen-prediction-before-future"
BLIND, PROSPECTIVE = OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE
_SCOPE_PINS = {}


def forecast_task_id(case_id):
    validate_stable_id(case_id)
    return NAMESPACE + "." + case_id + ".seal"


@dataclass(frozen=True, slots=True)
class ScheduledRevisionFutureScope(CanonicalRecord):
    """One shared immutable scientific scope, not repeated in per-case configs."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/revision-future-scope"
    record_id: str
    development: ScheduledProgramme
    nomination: ScheduledRevisionNomination
    frozen: ScheduledRevisionFrozenPackage
    programme: ScheduledProgramme
    calibration_programme: ScheduledProgramme | None = None
    calibration: ScheduledRevisionPublicCalibration | None = None
    nomination_rule: ScheduledE4NominationRule | None = None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        phase = "CALIBRATION" if self.programme.mode == "E4_REVISION_CALIBRATION" else "CONFIRMATION"
        validate_revision_phase(self.development, self.nomination, self.frozen, self.programme, phase=phase)
        if phase == "CONFIRMATION":
            from .programme_workflow import validate_e4_populations
            if type(self.nomination_rule) is not ScheduledE4NominationRule:
                raise ValueError("SCIENTIFIC_CHOICE: confirmation futures require the frozen explicit downstream nomination rule")
            self.nomination_rule.__post_init__()
            validate_e4_populations(self.development, self.calibration_programme, self.programme)
            validate_public_revision_calibration(self.calibration, self.development, self.nomination, self.frozen, self.calibration_programme)
        elif self.calibration_programme is not None or self.calibration is not None:
            raise ValueError("revision calibration forecast cannot import future confirmation or invented calibration products")
        if len(self.canonical_bytes()) > MAXIMUM_RECORD_BYTES:
            raise ValueError("revision future scope exceeds its closed canonical member bound")

    @property
    def identity(self):
        return _scope_pins(self)[0]

    def forecast(self, case_id, *, record_id):
        _, pins, cases = _scope_pins(self)
        case = cases.get(case_id)
        if case is None:
            raise ValueError("revision seal names a case outside its complete assigned programme")
        return _forecast_revision_case(self.nomination, self.programme, case, record_id=record_id, pins=pins)


def _scope_pins(scope):
    """Bound pure identities for the exact immutable object, never custody."""
    cached = _SCOPE_PINS.get(id(scope))
    if cached is not None and cached[0] is scope:
        return cached[1]
    result = (ObjectIdentity.from_record(scope.record_id, scope), _forecast_pins(scope.nomination, scope.frozen, scope.programme),
        {row.root_id: row for row in scope.programme.cases})
    if len(_SCOPE_PINS) == 4:
        _SCOPE_PINS.pop(next(iter(_SCOPE_PINS)))
    _SCOPE_PINS[id(scope)] = scope, result
    return result


@dataclass(frozen=True, slots=True)
class ScheduledRevisionSealCustody(CanonicalRecord):
    """Exact prior seal/receipt publications; their existence grants no authority."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/revision-seal-custody"
    record_id: str
    forecast: ScheduledRevisionForecastSeal
    publication: ArtifactWriteResult
    receipt: CanonicalTaskReceipt
    receipt_publication: ArtifactWriteResult
    prior_execution: RecursivePriorExecutionBinding

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.forecast) is not ScheduledRevisionForecastSeal
                or type(self.receipt) is not CanonicalTaskReceipt):
            raise TypeError("revision future requires exact actual seal and original producer receipt")
        self.forecast.__post_init__()
        self.receipt.__post_init__()
        prior = self.prior_execution
        if (type(prior) is not RecursivePriorExecutionBinding or prior.run_id != self.receipt.run_id
                or prior.task_id != self.receipt.task_id or prior.record != self.forecast.identity
                or prior.receipt != ObjectIdentity.from_record(self.receipt.receipt_id, self.receipt)
                or prior.logical_artifact_id != self.publication.logical.logical_artifact_id
                or prior.additional_output_schema_ids or prior.scope_output_schema_ids or prior.native_subwork):
            raise ValueError("revision future requires the exact original issued pure producer locator")
        _publication(self.publication, self.forecast)
        _publication(self.receipt_publication, self.receipt)
        if (self.receipt.task_id != forecast_task_id(self.forecast.case_id)
                or self.receipt.operational_status is not OperationalStatus.SUCCEEDED
                or self.receipt.output_logical_artifacts != (self.publication.logical,)
                or self.receipt.output_materializations != (self.publication.materialization,)
                or not any(row.check_id == SEAL_CHECK and row.passed for row in self.receipt.checks)
                or any(publication.logical.outcome_access is not BLIND
                    or publication.logical.visibility_ceiling is not PROSPECTIVE
                    for publication in (self.publication, self.receipt_publication))):
            raise ValueError("revision future substitutes the actual blind successful pre-future seal publication")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


_EXTRA_PORTS = (
    ("revision-scope", ScheduledRevisionFutureScope),
    ("revision-seal", ScheduledRevisionForecastSeal),
    ("revision-custody", ScheduledRevisionSealCustody),
    ("revision-seal-receipt", CanonicalTaskReceipt),
)
_EXTRA_SCHEMAS = frozenset(kind.SCHEMA for _, kind in _EXTRA_PORTS)


@dataclass(frozen=True, slots=True)
class AuthenticatedRevisionFuture:
    """Current parent-side replay result; never a canonical grant or authority."""

    run_id: str
    task_id: str
    input_materialization_ids: tuple[str, ...]
    execution_plan: ObjectIdentity
    scope: ObjectIdentity
    forecast: ObjectIdentity
    prior_execution: ObjectIdentity


def operation_manifests():
    return tuple(row.manifest() for row in operation_declarations())


def scientific_root_validator(config, context):
    """Require real named external prerequisites, then replay original admission."""
    from .compact_qualification import _qualification
    from .programme_acquisition_qualification import scientific_root_validator as original

    extra = tuple(link for link in context.links if link.consumer_node_id == context.node_id
        and link.consumer_input_id in {name for name, _ in _EXTRA_PORTS})
    if (len(extra) != len(_EXTRA_PORTS) or {row.consumer_input_id for row in extra} != {name for name, _ in _EXTRA_PORTS}
            or any(row.producer_node_id is not None or row.external_input_id is None for row in extra)):
        raise ValueError("revision future requires named actual earlier-wave seal, scope and custody inputs")
    for name, kind in _EXTRA_PORTS:
        link, = (row for row in extra if row.consumer_input_id == name)
        external = tuple(row for row in context.external_inputs if row.input_id == link.external_input_id)
        qualified = tuple(row for row in context.qualifications if row.source_id == link.external_input_id)
        if (len(external) != 1 or external[0].payload_schema != kind.SCHEMA
                or external[0].expected_content_sha256 is None or len(qualified) != 1):
            raise ValueError("revision future loses its exact prior scientific/custody input qualification")
        _qualification(context.root, context, qualified[0].materialization.object_id, kind.SCHEMA,
            external[0].expected_content_sha256, BLIND, PROSPECTIVE, kind.VERSION)
    original(config, replace(context, links=tuple(row for row in context.links if row not in extra)))


def operation_registrations():
    return tuple(row.registration() for row in operation_declarations())


def _read_record(port, kind):
    # Independent cursors preserve the original decoder/native owner's inputs.
    cursor = port.cursor()
    try:
        raw = cursor.read()
    finally:
        cursor.close()
    record = decode_canonical_bytes(raw, kind, maximum_bytes=MAXIMUM_RECORD_BYTES)
    if len(raw) != port.size_bytes or record.canonical_bytes() != raw or port.media_type != "application/json":
        raise ValueError("revision future substitutes exact canonical prerequisite bytes")
    return record


def _require_publication_contract(context, port, publication):
    matches = tuple(row for row in context.prepared_invocation.inputs if row.binding == port.binding)
    if (len(matches) != 1 or matches[0].logical != publication.logical
            or matches[0].physical_sha256 != publication.materialization.physical_sha256
            or port.size_bytes != publication.materialization.size_bytes):
        raise ValueError("revision future changes its actual preopened prior publication contract")


def require_revision_future(context, role, *, prepared=None, expected_manifest=None, additional_external_ports=()):
    """Authenticate the full actual context before any original native admission."""
    if type(context) is not TaskContext or role not in ROLES:
        raise PermissionError("revision future requires its actual supported issued TaskContext")
    contract = context.prepared_invocation
    if type(contract) is not PreparedInvocationContract:
        raise PermissionError("revision future requires its complete prepared issued invocation")
    contract.require_complete()
    contract.validate_context(context)
    if (type(prepared) is not AuthenticatedRevisionFuture
            or (prepared.run_id, prepared.task_id, prepared.input_materialization_ids, prepared.execution_plan) !=
                (context.run_id, context.task_id, context.input_materialization_ids, contract.execution_plan)):
        raise PermissionError("revision future requires fresh actual current and prior issued custody preparation")
    selected = expected_manifest or next(row for row in operation_manifests() if row.capability_key == NAMESPACE + "." + role)
    task = contract.execution_task_record
    if (contract.manifest != selected or not contract.native_effect or type(task) is not ExecutionTask
            or task.task_id != context.task_id or task.capability.capability_key != selected.capability_key):
        raise PermissionError("revision future changes its actual installed native capability/task")
    values, selected_ports = {}, []
    for name, kind in _EXTRA_PORTS:
        ports = tuple(port for port in context.input_ports if port.payload_schema == kind.SCHEMA)
        if (len(ports) != 1 or ports[0].kind is not WorkerInputKind.EXTERNAL
                or ports[0].outcome_access is not BLIND or ports[0].visibility_ceiling is not PROSPECTIVE):
            raise ValueError("revision future loses its exact blind prior-wave prerequisite census")
        values[kind] = _read_record(ports[0], kind), ports[0]
        selected_ports.append(ports[0])
        edges = tuple(row for row in task.scientific_inputs if row.consumer_input_id == name)
        if (len(edges) != 1 or edges[0].producer_task_id is not None or edges[0].external_input_id is None
                or edges[0].operational_logical_artifact_id != ports[0].artifact_id
                or (edges[0].payload_schema, edges[0].media_type, edges[0].outcome_access, edges[0].visibility_ceiling)
                    != (kind.SCHEMA, ports[0].media_type, BLIND, PROSPECTIVE)):
            raise ValueError("revision future loses its actual earlier-wave scientific input edge")
    scope, _ = values[ScheduledRevisionFutureScope]
    seal, seal_port = values[ScheduledRevisionForecastSeal]
    custody, _ = values[ScheduledRevisionSealCustody]
    receipt, receipt_port = values[CanonicalTaskReceipt]
    if (seal != custody.forecast or seal != scope.forecast(seal.case_id, record_id=seal.record_id)
            or receipt != custody.receipt
            or (scope.identity, seal.identity, ObjectIdentity.from_record(custody.prior_execution.binding_id, custody.prior_execution))
                != (prepared.scope, prepared.forecast, prepared.prior_execution)
            or context.task_id != COMPACT_NAMESPACE + "." + seal.case_id + "." + role):
        raise ValueError("revision future substitutes frozen models, predictions or actual original case")
    _require_publication_contract(context, seal_port, custody.publication)
    _require_publication_contract(context, receipt_port, custody.receipt_publication)
    require_publication_copy(seal, seal_port, custody.publication)
    require_publication_copy(receipt, receipt_port, custody.receipt_publication)
    # Filtering is a decoder view over EXTERNAL additions only. All real
    # dependency receipts survive verbatim; native preparation/execution uses
    # the original full context and complete materialization census.
    if (type(additional_external_ports) is not tuple or len({port.artifact_id for port in additional_external_ports}) != len(additional_external_ports)
            or any(port not in context.input_ports or port.kind is not WorkerInputKind.EXTERNAL or port in selected_ports
                for port in additional_external_ports)):
        raise PermissionError("revision future additional inputs must be exact separately validated external ports")
    remaining = tuple(port for port in context.input_ports if port not in (*selected_ports, *additional_external_ports))
    view = replace(context, input_ports=remaining, input_bindings=tuple(port.binding for port in remaining), prepared_invocation=None)
    return scope, view


def decode_core(context, role, *, prepared=None):
    scope, view = require_revision_future(context, role, prepared=prepared)
    result = acquisition.decode_core(view, role)
    _check_original_join(scope, result)
    return result


def decode_response(context, role, *, prepared=None):
    scope, view = require_revision_future(context, role, prepared=prepared)
    result = acquisition.decode_response(view, role)
    _check_original_join(scope, result)
    return result


def _check_original_join(scope, result):
    config, source, records, _ = result
    admission = records[acquisition.ScheduledProgrammeAcquisitionAdmission.SCHEMA]
    case = next(row for row in scope.programme.cases if row.root_id == config.root_id)
    if (admission.programme != scope.programme or source.root_id != case.root_id
            or config.bank != scope.programme.bank or source.root.root.independent_group_id != case.independent_group_id):
        raise ValueError("revision future changes its actual original admitted programme/source census")


def operation_factories():
    return tuple(row.provider_factory() for row in operation_declarations())


def prepare_for_invocation(supplier, runner):
    from functools import partial
    from empirical_lawhood.runtime.execution import ParentPreparedTaskRunner
    callback = getattr(supplier, "prepare_revision_future", None)
    if not callable(callback):
        raise PermissionError("revision future requires actual current and original prior issued custody preparation")
    return ParentPreparedTaskRunner(runner.manifest, partial(callback, runner=runner), native_effect=True)


def prepared_runner(runner, prepared):
    """Keep the actual original native class; only its admission decoder changes."""
    from functools import partial
    cls, decoder = (response.ScheduledPulseNativeRunner, decode_response) if runner.role == "responses" else (core.ScheduledNativeRunner, decode_core)
    if type(runner) is not cls or runner.role not in ROLES or type(prepared) is not AuthenticatedRevisionFuture:
        raise PermissionError("revision future preparation refuses a foreign native worker or untyped custody")
    return cls(runner.role, decoder=partial(decoder, prepared=prepared), manifest=runner.manifest)


def add_revision_future_dependencies(draft, scope, custody):
    """Augment an actual acquisition graph, preserving every original operation.

    The caller supplies prior publications and authenticates them through its
    existing public custody service. This function does not publish or issue.
    """
    if type(draft) is not RecursiveStudyDraft or type(scope) is not ScheduledRevisionFutureScope:
        raise TypeError("revision future composition requires an actual acquisition draft and shared scope")
    scope.__post_init__()
    if type(custody) is not tuple or any(type(row) is not ScheduledRevisionSealCustody for row in custody):
        raise TypeError("revision future composition requires exact immutable prior seal custody")
    from .programme_acquisition import ScheduledProgrammeAcquisitionAdmissionConfig
    declarations = tuple(decode_canonical_bytes(operation.config_payload.encode(), ScheduledProgrammeAcquisitionAdmissionConfig,
        maximum_bytes=MAXIMUM_RECORD_BYTES) for operation in draft.operations
        if operation.config_identity.object_schema == ScheduledProgrammeAcquisitionAdmissionConfig.SCHEMA)
    if len(declarations) != 1 or declarations[0].programme != scope.programme:
        raise ValueError("revision future composition substitutes its actual admitted whole programme")
    wave = declarations[0].wave
    by_case = {row.forecast.case_id: row for row in custody}
    if len(by_case) != len(custody) or tuple(sorted(by_case)) != wave.root_ids:
        raise ValueError("revision future omits an assigned wave case or duplicates prior seal custody")
    selections = {row.selection.capability_key.rsplit(".", 1)[-1]: row.selection for row in operation_registrations()}
    external = {row.input_id: row for row in draft.external_inputs}
    links, operations, operands = list(draft.links), [], {}

    def add(record, publication=None):
        logical = publication.logical.logical_artifact_id if publication else record.identity.object_id
        entry = RecursiveExternalInput("external." + logical, logical, record.SCHEMA, "application/json",
            len(record.canonical_bytes()), BLIND, PROSPECTIVE, record.fingerprint(), "SOURCE")
        if external.setdefault(entry.input_id, entry) != entry or operands.setdefault(logical, record) != record:
            raise ValueError("revision future aliases immutable prior input bytes")
        return entry.input_id

    scope_external = add(scope)
    count = 0
    for operation in draft.operations:
        role = operation.selection.capability_key.rsplit(".", 1)[-1]
        root_id = operation.node_id.removeprefix(COMPACT_NAMESPACE + ".").removesuffix("." + role)
        if role not in ROLES:
            operations.append(operation)
            continue
        if operation.selection.capability_key != acquisition.NAMESPACE + "." + role or root_id not in by_case:
            raise ValueError("revision future wrapper can only augment the actual original acquisition owner")
        prior = by_case[root_id]
        prior.__post_init__()
        if prior.forecast != scope.forecast(root_id, record_id=prior.forecast.record_id):
            raise ValueError("revision future composition substitutes pre-outcome frozen predictions")
        ports = (("revision-scope", scope_external), ("revision-seal", add(prior.forecast, prior.publication)),
            ("revision-custody", add(prior)), ("revision-seal-receipt", add(prior.receipt, prior.receipt_publication)))
        for name, external_id in ports:
            links.append(RecursiveInputLink("edge." + operation.node_id + "." + name, operation.node_id, name,
                external_input_id=external_id, scientific_role="SOURCE"))
        operations.append(replace(operation, selection=selections[role]))
        count += 1
    if count != len(ROLES) * len(wave.root_ids):
        raise ValueError("revision future omits an original continuation or response native dependency")
    return replace(draft, operations=tuple(sorted(operations, key=lambda row: row.node_id)),
        external_inputs=tuple(sorted(external.values(), key=lambda row: row.input_id)),
        links=tuple(sorted(links, key=lambda row: row.edge_id))), operands


def _operation_declaration(base):
    role = base.capability_key.rsplit('.', 1)[-1]
    cls, decoder = (response.ScheduledPulseNativeRunner, decode_response) if role == 'responses' else (core.ScheduledNativeRunner, decode_core)
    selected = replace(base, capability_key=NAMESPACE+'.'+role,
        implementation_id=NAMESPACE+'.prior-revision-seal-original-v2-'+role,
        input_ports=tuple(sorted((*base.input_ports, *(RecursivePortContract(name, kind.SCHEMA,
            'application/json', MAXIMUM_RECORD_BYTES) for name, kind in _EXTRA_PORTS)), key=lambda port: port.port_id)),
        input_record_types=tuple(sorted((*base.input_record_types, *(kind for _, kind in _EXTRA_PORTS)),
            key=lambda kind: (kind.SCHEMA, kind.VERSION))),
        conformance_check_ids=tuple(sorted(('actual-prior-revision-seal-custody',
            'complete-issued-native-input-census', 'unchanged-original-v2-native-work'))),
        scientific_hooks=replace(base.scientific_hooks, scientific_root_validator=scientific_root_validator),
        runner_factory=lambda: cls(role, decoder=decoder, manifest=selected.manifest()),
        execution_properties=replace(base.execution_properties, runner_preparation_factory=prepare_for_invocation))
    return selected


def operation_declarations():
    return tuple(sorted((_operation_declaration(base) for base in acquisition.operation_declarations()
        if base.capability_key.rsplit('.', 1)[-1] in ROLES), key=lambda row: row.capability_key))
