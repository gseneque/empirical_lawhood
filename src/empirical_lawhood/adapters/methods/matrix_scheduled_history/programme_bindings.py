# SPDX-License-Identifier: MPL-2.0
"""Actual admission and sealed collection around unchanged v2 numerical state.

New capability identities describe the additional programme controls. Native
contacts retain the actual execution task and admission materialization; the
v2 numerical configuration, mathematical operation and source bytes are never
rewritten. These providers require ordinary issue and outcome authority.
"""

from empirical_lawhood.runtime.recursive_provider import (
    RecursiveOperationDeclaration, RecursiveScientificHooks, RecursiveExecutionProperties,
)

from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS

from dataclasses import dataclass, replace
from typing import ClassVar

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteResult, CanonicalTaskReceipt
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import TaskContext, WorkerInputKind
from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract

from . import compact_bindings as compact, operation_bindings as core, response_bindings as response
from .compact_records import ScheduledCompactBank, compact_identity
from .programme_composition import NATIVE_PHASES, expected_global_commitment, phase_roles
from .programme_global import GLOBAL_CONFIG_ID, ScheduledProgrammeGlobalCommit, ScheduledProgrammeGlobalCommitConfig, global_committed
from .programme_parent import ScheduledProgrammeGlobalParentBinding
from .programme_records import MODES, NAMESPACE, ScheduledProgramme, ScheduledProgrammeWave, validate_programme_bank
from .programme_reduction import (
    ScheduledProgrammeCaseResult, ScheduledProgrammeNativeDisposition,
    ScheduledProgrammeReceiptReference, ScheduledProgrammeWaveResult, programme_numerical_disposition,
)
from .commitment import ScheduledCommitment
from .records import identity

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT

MAXIMUM_RECORD_BYTES = 16*1024**2
BLIND, PROSP = OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeWaveAdmissionConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/wave-admission-config'
    config_id: str
    programme: ScheduledProgramme
    bank: ObjectIdentity
    wave: ScheduledProgrammeWave
    required_global_parent: ObjectIdentity
    required_global_commitment: ObjectIdentity
    global_parent_publication: ArtifactWriteResult
    global_parent_receipt: ObjectIdentity
    global_parent_binding: ScheduledProgrammeGlobalParentBinding

    def __post_init__(self):
        if (type(self.programme) is not ScheduledProgramme or self.bank != self.programme.bank
                or self.wave not in self.programme.waves or self.config_id != 'config.'+self.wave.wave_id+'.open'
                or self.required_global_parent.object_schema != ScheduledProgrammeGlobalCommit.SCHEMA
                or (self.required_global_commitment.object_schema, self.required_global_commitment.object_version)
                    != (ScheduledCommitment.SCHEMA, ScheduledCommitment.VERSION)
                or self.global_parent_receipt.object_schema != CanonicalTaskReceipt.SCHEMA
                or self.global_parent_publication.logical.payload_schema != ScheduledProgrammeGlobalCommit.SCHEMA
                or self.global_parent_publication.logical.content_sha256 != self.required_global_parent.object_fingerprint
                or self.global_parent_publication.materialization.physical_sha256 != self.required_global_parent.object_fingerprint
                or type(self.global_parent_binding) is not ScheduledProgrammeGlobalParentBinding
                or self.global_parent_binding.parent.identity != self.required_global_parent
                or self.global_parent_binding.publication != self.global_parent_publication
                or ObjectIdentity.from_record(self.global_parent_binding.receipt.receipt_id, self.global_parent_binding.receipt)
                    != self.global_parent_receipt):
            raise ValueError('wave admission substitutes global scope, bank, partition or actual/semantic parent type')


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeWaveAdmission(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/wave-admission'
    admission_id: str
    configuration: ObjectIdentity
    programme: ScheduledProgramme
    bank: ObjectIdentity
    wave: ScheduledProgrammeWave
    global_parent: ScheduledProgrammeGlobalCommit
    global_parent_publication: ArtifactWriteResult
    global_parent_receipt: CanonicalTaskReceipt
    global_parent_binding: ScheduledProgrammeGlobalParentBinding

    def __post_init__(self):
        config = ScheduledProgrammeWaveAdmissionConfig('config.'+self.wave.wave_id+'.open', self.programme,
            self.bank, self.wave, self.global_parent.identity, compact_identity(self.global_parent.semantic_commitment),
            self.global_parent_publication, ObjectIdentity.from_record(self.global_parent_receipt.receipt_id, self.global_parent_receipt),
            self.global_parent_binding)
        if (self.admission_id != 'admission.'+self.wave.wave_id
                or self.configuration != ObjectIdentity.from_record(config.config_id, config)
                or self.global_parent.programme != self.programme.identity or self.global_parent.bank != self.bank):
            raise ValueError('wave admission changes actual configuration or frozen global commitment scope')
        _authenticate_global_receipt(self.global_parent, self.global_parent_publication, self.global_parent_receipt)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.admission_id, self)

    @property
    def semantic_commitment(self):
        return self.global_parent.semantic_commitment


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeWaveCollectorConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/wave-collector-config'
    config_id: str
    programme: ObjectIdentity
    bank: ObjectIdentity
    wave: ScheduledProgrammeWave
    admission: ObjectIdentity
    mode: str

    def __post_init__(self):
        if (self.config_id != 'config.'+self.wave.wave_id+'.collect' or self.mode not in MODES
                or self.programme.object_schema != ScheduledProgramme.SCHEMA
                or self.bank.object_schema != ScheduledCompactBank.SCHEMA
                or self.admission.object_schema != ScheduledProgrammeWaveAdmission.SCHEMA):
            raise ValueError('wave collector changes exact global scope, admitted partition or declared mode')

    @property
    def operation(self):
        return 'collect-development' if self.mode == 'E4_DEVELOPMENT' else 'collect'




def operation_manifests():
    return tuple(row.manifest() for row in operation_declarations())


def operation_registrations():
    return tuple(row.registration() for row in operation_declarations())


def _record(port, cls):
    raw = port.read()
    value = decode_canonical_bytes(raw, cls, maximum_bytes=MAXIMUM_RECORD_BYTES)
    if port.media_type != 'application/json' or len(raw) != port.size_bytes or value.canonical_bytes() != raw:
        raise ValueError('programme worker substitutes exact canonical input bytes or media type')
    return value


def _dependency(context, port, task, *, access=BLIND, visibility=PROSP):
    receipts = tuple(r for r in context.dependency_receipts if port.materialization_id in r.output_materialization_ids)
    if (port.kind is not WorkerInputKind.DEPENDENCY or port.outcome_access is not access
            or port.visibility_ceiling is not visibility or len(receipts) != 1 or receipts[0].task_id != task):
        raise ValueError('programme worker loses exact actual admission/product dependency receipt')
    return receipts[0]


def _authenticate_admission(admission, bank):
    validate_programme_bank(admission.programme, bank)
    global_config = ScheduledProgrammeGlobalCommitConfig(GLOBAL_CONFIG_ID, admission.programme, compact_identity(bank))
    if (admission.bank != compact_identity(bank) or admission.semantic_commitment != expected_global_commitment(bank)
            or admission.global_parent != global_committed(global_config, bank)):
        raise ValueError('wave admission changes actual global parent or original semantic commitment')
    _authenticate_global_receipt(admission.global_parent, admission.global_parent_publication, admission.global_parent_receipt)


def _authenticate_global_receipt(parent, publication, receipt):
    from .records import _publication
    _publication(publication, parent)
    if (type(receipt) is not CanonicalTaskReceipt or receipt.task_id != compact.NAMESPACE+'.commit'
            or receipt.operational_status is not OperationalStatus.SUCCEEDED
            or publication.logical not in receipt.output_logical_artifacts
            or publication.materialization not in receipt.output_materializations
            or len(receipt.output_logical_artifacts) != 1 or len(receipt.output_materializations) != 1
            or not any(c.check_id == 'programme-global-original-published-whole-bank-freeze' and c.passed for c in receipt.checks)):
        raise ValueError('wave admission requires the actual successful global wrapper receipt and exact publication')


def _read_phase(context, role, state):
    if type(context) is not TaskContext or context.outcome_access is not core.phase_access(role):
        raise ValueError('programme phase refuses unsupported issued access before input reads')
    phase = next(p for p in compact.PHASES if p[0] == role)
    cls = compact.config_type(role)
    types = {cls.SCHEMA: cls, **{(ScheduledProgrammeWaveAdmission if t is ScheduledCommitment else t).SCHEMA:
        ScheduledProgrammeWaveAdmission if t is ScheduledCommitment else t for _, t in phase[1]
        if t is not None and t is not compact.MatrixHistorySeed}}
    values, ports, streams = {}, {}, []
    shared = {t.SCHEMA for _, t in phase[1] if t is not None and t not in
        (ScheduledCommitment, compact.ScheduledPrefixHistory, core.ScheduledNumericalAssessment,
         core.ScheduledPrefixWitness, core.ScheduledFrameAssessment, compact.ScheduledCausalPrefix,
         compact.ScheduledForecastFeature, compact.ScheduledForecastSeal, core.ScheduledFullHistory,
         compact.ScheduledFullAssessment, compact.ScheduledResponseForecast, compact.ScheduledResponseNative,
         compact.ScheduledResponseScore, compact.ScheduledCalibration)}
    for port in context.input_ports:
        if port.payload_schema in shared and (port.kind is not WorkerInputKind.EXTERNAL
                or port.outcome_access is not BLIND or port.visibility_ceiling is not PROSP):
            raise ValueError('programme phase changes original blind shared-source boundary')
        if port.payload_schema == compact.MatrixHistorySeed.SCHEMA and any(t is compact.MatrixHistorySeed for _, t in phase[1]):
            streams.append((_record(port, compact.MatrixHistorySeed), port))
        elif port.payload_schema in types:
            if port.payload_schema in values:
                raise ValueError('programme phase duplicates a single scientific input')
            value = _record(port, types[port.payload_schema])
            values[port.payload_schema] = [(value, port)]
            ports[port.payload_schema] = port
        elif port.payload_schema == MATRIX_ARRAY_SCHEMA and port.artifact_id not in ports:
            ports[port.artifact_id] = port
        else:
            raise ValueError('programme phase receives an undeclared input schema')
    optional = {compact.ScheduledResponseForecast.SCHEMA} if role.startswith('continue') else set()
    if (not set(types)-optional <= set(values) <= set(types)
            or sum(p.payload_schema == MATRIX_ARRAY_SCHEMA for p in context.input_ports) != sum(t is None for _, t in phase[1])):
        raise ValueError('programme phase omits the complete typed/raw port census')
    config, config_port = values[cls.SCHEMA][0]
    m = next(m for m in operation_manifests() if m.capability_key == NAMESPACE+'.'+role)
    if (context.task_id != compact.NAMESPACE+'.'+config.root_id+'.'+role or context.config.config_id != config.config_id
            or context.config.config_schema != config.SCHEMA or context.config.content_sha256 != config.fingerprint()
            or context.config.artifact_id != config_port.artifact_id or context.permissions != m.permissions
            or not core.BUDGET.contains(context.resource_budget)):
        raise ValueError('programme phase changes actual v2 config bytes/task or new capability permissions')
    if role in NATIVE_PHASES:
        admission, port = values[ScheduledProgrammeWaveAdmission.SCHEMA][0]
        bank = values[ScheduledCompactBank.SCHEMA][0][0]
        _authenticate_admission(admission, bank)
        _dependency(context, port, admission.wave.wave_id+'.open')
        if config.root_id not in admission.wave.root_ids:
            raise ValueError('native phase enters a source outside its actual admitted whole-group wave')
        state.update(admission=admission, admission_port=port)
        # Derived scientific state from an explicit new typed product. The
        # port remains the real admission port with its real schema/binding.
        values[ScheduledCommitment.SCHEMA] = [(admission.semantic_commitment, port)]
        ports[ScheduledCommitment.SCHEMA] = port
    return config, values, ports, streams


def _decode(context, role, *, response_phase=False):
    state = {}

    def check(ctx, port, root_id, owner, **kwargs):
        if owner == 'commit':
            if (port is not state.get('admission_port') or port.payload_schema != ScheduledProgrammeWaveAdmission.SCHEMA
                    or root_id not in state['admission'].wave.root_ids):
                raise ValueError('native phase loses its explicit actual admission dependency')
            return _dependency(ctx, port, state['admission'].wave.wave_id+'.open', **kwargs)
        return compact.dependency(ctx, port, root_id, owner, **kwargs)

    decoder = compact.decode_response if response_phase else compact.decode_core
    return decoder(context, role, reader=lambda ctx, phase: _read_phase(ctx, phase, state), dependency_checker=check)


def decode_core(context, role):
    return _decode(context, role)


def decode_response(context, role):
    return _decode(context, role, response_phase=True)


def _read_control(context, role):
    if type(context) is not TaskContext:
        raise ValueError('programme control requires its actual issued TaskContext')
    cls = ScheduledProgrammeWaveAdmissionConfig if role == 'open' else ScheduledProgrammeWaveCollectorConfig
    types = {cls.SCHEMA: cls, ScheduledCompactBank.SCHEMA: ScheduledCompactBank}
    if role == 'open':
        types[ScheduledProgrammeGlobalCommit.SCHEMA] = ScheduledProgrammeGlobalCommit
        types[CanonicalTaskReceipt.SCHEMA] = CanonicalTaskReceipt
    else:
        types[ScheduledProgrammeWaveAdmission.SCHEMA] = ScheduledProgrammeWaveAdmission
        types.update({p[2].SCHEMA: p[2] for p in compact.PHASES if p[0] not in ('commit', 'calibrate', 'calibration-qualify')})
    values = {}
    for port in context.input_ports:
        if port.payload_schema not in types:
            raise ValueError('programme control receives an undeclared scientific/custody input')
        value = _record(port, types[port.payload_schema])
        values.setdefault(value.SCHEMA, []).append((value, port))
    for schema in (cls.SCHEMA, ScheduledCompactBank.SCHEMA,
            ScheduledProgrammeGlobalCommit.SCHEMA if role == 'open' else ScheduledProgrammeWaveAdmission.SCHEMA):
        if len(values.get(schema, ())) != 1:
            raise ValueError('programme control omits an exact single configuration/bank/parent')
    if role == 'open' and len(values.get(CanonicalTaskReceipt.SCHEMA, ())) != 1:
        raise ValueError('wave opener omits its actual global parent receipt')
    config, config_port = values[cls.SCHEMA][0]
    expected_role = 'open' if role == 'open' else config.operation
    m = next(m for m in operation_manifests() if m.capability_key == NAMESPACE+'.'+expected_role)
    task = config.wave.wave_id+('.open' if role == 'open' else '.collect')
    if (context.task_id != task or context.config.config_id != config.config_id
            or context.config.config_schema != cls.SCHEMA or context.config.content_sha256 != config.fingerprint()
            or context.config.artifact_id != config_port.artifact_id or context.permissions != m.permissions
            or context.outcome_access is not m.maximum_outcome_access or not core.BUDGET.contains(context.resource_budget)):
        raise ValueError('programme control changes its actual configuration/task/access/capability contract')
    bank, bank_port = values[ScheduledCompactBank.SCHEMA][0]
    if (config.bank != compact_identity(bank) or bank_port.kind is not WorkerInputKind.EXTERNAL
            or bank_port.outcome_access is not BLIND or bank_port.visibility_ceiling is not PROSP):
        raise ValueError('programme control substitutes original blind global bank custody')
    return config, bank, values


class ProgrammeWaveOpener:
    def __init__(self, manifest=None):
        self.manifest = manifest or next(m for m in operation_manifests() if m.capability_key == NAMESPACE+'.open')

    def execute(self, context):
        try:
            config, bank, values = _read_control(context, 'open')
            validate_programme_bank(config.programme, bank)
            parent, port = values[ScheduledProgrammeGlobalCommit.SCHEMA][0]
            receipt, receipt_port = values[CanonicalTaskReceipt.SCHEMA][0]
            global_config = ScheduledProgrammeGlobalCommitConfig(GLOBAL_CONFIG_ID, config.programme, compact_identity(bank))
            if (parent != global_committed(global_config, bank) or parent.identity != config.required_global_parent
                    or compact_identity(parent.semantic_commitment) != config.required_global_commitment
                    or port.outcome_access is not BLIND or port.visibility_ceiling is not PROSP):
                raise ValueError('wave opener substitutes actual global wrapper or exact original semantic state')
            if (ObjectIdentity.from_record(receipt.receipt_id, receipt) != config.global_parent_receipt
                    or receipt_port.kind is not WorkerInputKind.EXTERNAL or receipt_port.outcome_access is not BLIND
                    or receipt_port.visibility_ceiling is not PROSP):
                raise ValueError('wave opener substitutes its actual globally qualified receipt publication')
            _authenticate_global_receipt(parent, config.global_parent_publication, receipt)
            from .commitment import require_publication_copy
            require_publication_copy(parent, port, config.global_parent_publication)
            # A same-run producer is authenticated directly by the actual
            # ordinary dependency header. External parents require the public
            # source/receipt custody hook before issue; this worker does not
            # manufacture a canonical receipt from an external port.
            if port.kind is WorkerInputKind.DEPENDENCY:
                _dependency(context, port, compact.NAMESPACE+'.commit')
            elif port.kind is not WorkerInputKind.EXTERNAL:
                raise ValueError('wave opener has no actual global commitment input boundary')
            admission = ScheduledProgrammeWaveAdmission('admission.'+config.wave.wave_id,
                ObjectIdentity.from_record(config.config_id, config), config.programme, config.bank, config.wave, parent,
                config.global_parent_publication, receipt, config.global_parent_binding)
            return core._outputs(context, admission)
        finally:
            for port in context.input_ports:
                port.close()


def _collect_case(context, admission, bank, case, rows, *, index):
    from .compact_records import ScheduledCompactConfig
    from .source_index import ScheduledNativeSourceContext
    from .continuation import full_access, full_visibility
    source = index.resolve(next(d for d in bank.sources if d.root_id == case.root_id))
    prefix_config = ScheduledCompactConfig('config.'+compact.NAMESPACE+'.'+case.root_id+'.prefix',
        'prefix', source.reference, compact.compact_identity(bank))
    native_context = ScheduledNativeSourceContext(source, prefix_config, bank)
    roles = phase_roles(source, bank.forecast_design)
    if set(rows) != set(roles):
        raise ValueError('programme collector omits the complete eleven original products')
    products, references = {}, []
    for role in roles:
        value, port = rows[role]
        expected_type = next(p[2] for p in compact.PHASES if p[0] == role)
        if type(value) is not expected_type or value.source != case.source:
            raise ValueError('programme collector substitutes an original scientific product/source')
        binding = _dependency(context, port, compact.NAMESPACE+'.'+case.root_id+'.'+role,
            access=core.phase_access(role), visibility=core.phase_visibility(role))
        references.append(ScheduledProgrammeReceiptReference.from_binding(binding))
        products[role] = value
    prefix, causal = products['prefix'], products['project']
    suffix = '-development' if 'continue-development' in roles else ''
    forecast = products[roles[5]]
    physical, full = products['physical-forecast'], products['continue'+suffix]
    assessment, responses, score = products['full-numerical'+suffix], products['responses'+suffix], products['response-score'+suffix]
    prefix.validate_source(source, native_context=native_context)
    core.validate_original_prefix_receipt(prefix, context.run_id)
    full.validate_source(source, prefix, causal, forecast, physical, native_context=native_context)
    responses.validate_source(source, bank.response_selection, prefix, causal, physical, forecast,
        native_context=native_context)
    if (assessment.history != identity(full) or assessment.numerical_design != identity(source.numerical_design)
            or forecast.design != admission.programme.forecast_design or forecast.model != bank.forecast_design.model
            or forecast.criterion != admission.programme.criterion or score.criterion != admission.programme.criterion
            or score.error_forecast != identity(forecast) or score.responses != identity(responses)
            or score.independent_group_id != case.independent_group_id or score.role != case.role
            or full.arrays.outcome_access is not full_access(source) or full.arrays.visibility_ceiling is not full_visibility(source)):
        raise ValueError('programme collector changes actual global model, numerical or pulse lineage')
    native = []
    for phase, value in (('continue', full), ('prefix', prefix), ('responses', responses)):
        events = value.native if phase == 'responses' else (value.native,)
        if not events:
            native.append(ScheduledProgrammeNativeDisposition(phase, 'NOT_USED', None, None, None,
                tuple(sorted(set(responses.reason_codes) | {'programme-response-native-not-used'}))))
        else:
            event, = events
            if event.definition.parent_contact.run_id != context.run_id:
                raise ValueError('programme collector substitutes a foreign actual native run')
            native.append(ScheduledProgrammeNativeDisposition(phase, 'COMPLETED', event.definition.identity,
                ObjectIdentity.from_record('completion.'+event.definition.subwork_id, event.completion),
                ObjectIdentity.from_record(event.receipt.receipt_id, event.receipt), ()))
    numerical = programme_numerical_disposition(products['numerical'], assessment, score, frame_numerical=products['check'])
    reasons = set(score.reason_codes)
    if numerical != 'SATISFIED':
        reasons.add('programme-numerical-'+numerical.lower())
    return ScheduledProgrammeCaseResult(case.root_id, case.source, case.independent_group_id, 'COMPLETED', numerical,
        score.disposition, score.cumulative_log_errors, forecast.log_error_points, forecast.log_error_uppers,
        identity(forecast), identity(score), identity(assessment), tuple(sorted(references, key=lambda r: r.receipt_id)),
        tuple(native), tuple(sorted(reasons)))


class ProgrammeWaveCollector:
    def __init__(self, role='collect', manifest=None):
        self.role = role
        self.manifest = manifest or next(m for m in operation_manifests() if m.capability_key == NAMESPACE+'.'+role)

    def execute(self, context):
        try:
            config, bank, values = _read_control(context, self.role)
            admission, admission_port = values[ScheduledProgrammeWaveAdmission.SCHEMA][0]
            _authenticate_admission(admission, bank)
            _dependency(context, admission_port, admission.wave.wave_id+'.open')
            if (config.programme != admission.programme.identity or config.wave != admission.wave
                    or config.admission != admission.identity or config.mode != admission.programme.mode):
                raise ValueError('programme collector substitutes its actual admitted complete wave')
            cases = tuple(c for c in admission.programme.cases if c.root_id in admission.wave.root_ids)
            by_source = {c.source: c for c in cases}
            received = {c.root_id: {} for c in cases}
            for schema, rows in values.items():
                if schema in (config.SCHEMA, ScheduledCompactBank.SCHEMA, ScheduledProgrammeWaveAdmission.SCHEMA):
                    continue
                for value, port in rows:
                    case = by_source.get(value.source)
                    if case is None:
                        raise ValueError('programme collector receives a product outside its exact admitted source census')
                    source = next(d for d in bank.sources if d.root_id == case.root_id)
                    role = next((role for role in phase_roles(source, bank.forecast_design)
                        if next(p[2] for p in compact.PHASES if p[0] == role).SCHEMA == schema), None)
                    if role is None or role in received[case.root_id]:
                        raise ValueError('programme collector duplicates or substitutes a phase product')
                    received[case.root_id][role] = (value, port)
            from .source_index import ScheduledSourceIndex
            index = ScheduledSourceIndex.from_shared(reservation=bank.reservation,
                specification=bank.specification, provenances=bank.provenances)
            result = ScheduledProgrammeWaveResult('result.'+admission.wave.wave_id, admission.programme.identity,
                admission.wave.wave_id, admission.wave.group_ids, admission.wave.root_ids,
                tuple(_collect_case(context, admission, bank, case, received[case.root_id], index=index) for case in cases))
            return core._outputs(context, result)
        finally:
            for port in context.input_ports:
                port.close()


def operation_factories():
    return tuple(row.provider_factory() for row in operation_declarations())


def _control_declaration(role):
    from .programme_wave_qualification import scientific_root_validator
    access = BLIND if role == 'open' else OutcomeAccess.DEVELOPMENT_VISIBLE if role.endswith('-development') else OutcomeAccess.EVALUATION_SEALED
    ceiling = EvidenceCeiling.NON_PROMOTABLE
    cls = ScheduledProgrammeWaveAdmissionConfig if role == 'open' else ScheduledProgrammeWaveCollectorConfig
    output = ScheduledProgrammeWaveAdmission if role == 'open' else ScheduledProgrammeWaveResult
    ports = [RecursivePortContract('bank', ScheduledCompactBank.SCHEMA, 'application/json', MAXIMUM_RECORD_BYTES)]
    if role == 'open':
        ports.append(RecursivePortContract('global-parent', ScheduledProgrammeGlobalCommit.SCHEMA, 'application/json', MAXIMUM_RECORD_BYTES))
        ports.append(RecursivePortContract('global-parent-receipt', CanonicalTaskReceipt.SCHEMA, 'application/json', MAXIMUM_RECORD_BYTES))
    else:
        ports.append(RecursivePortContract('admission', ScheduledProgrammeWaveAdmission.SCHEMA, 'application/json', MAXIMUM_RECORD_BYTES))
        for phase, _, product, _, _ in compact.PHASES:
            if phase not in ('commit', 'calibrate', 'calibration-qualify', 'continue-development', 'full-numerical-development', 'responses-development', 'response-score-development', 'forecast-calibrated'):
                ports.append(RecursivePortContract('products.' + phase, product.SCHEMA, 'application/json', MAXIMUM_RECORD_BYTES, minimum_count=1, maximum_count=None))
    selected = RecursiveOperationDeclaration(
        capability_key=NAMESPACE + "." + role,
        capability_version="1.0.0",
        implementation_id=NAMESPACE + '.actual-admission-original-v2-state-' + role,
        kind=CapabilityKind.EXPERIMENT_DESIGNER if role == 'open' else CapabilityKind.TRANSFORM,
        config_record_type=cls,
        stage=ScientificStage.FREEZE if role == 'open' else ScientificStage.TRANSFORM,
        input_ports=tuple(sorted(ports, key=lambda p: p.port_id)),
        outputs=(OutputTemplate('product', output.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'),),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT if role.endswith('-development') else CapabilityPermission.READ_SEALED_OUTCOMES if access is OutcomeAccess.EVALUATION_SEALED else CapabilityPermission.READ_FROZEN_MODELS))),
        evidence_ceiling=ceiling,
        outcome_access=access,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY if role.endswith('-development') else PROSP,
        resources=core.BUDGET,
        conformance_check_ids=tuple(sorted(('actual-admission-dependency-custody', 'complete-global-whole-group-scope', 'unchanged-original-numerical-subjects'))),
        runner_factory=lambda: ProgrammeWaveOpener(selected.manifest()) if role == "open" else ProgrammeWaveCollector(role, selected.manifest()),
        record_codecs={**_record_codecs(), **{kind.SCHEMA: kind for kind in (ScheduledProgrammeWaveAdmission, ScheduledProgrammeGlobalCommit, CanonicalTaskReceipt)}},
        scientific_hooks=RecursiveScientificHooks(scientific_unit_ids=lambda c: c.wave.group_ids, scientific_operand_sha256s=lambda c: (c.bank.object_fingerprint,), scientific_root_validator=scientific_root_validator),
        execution_properties=RecursiveExecutionProperties(barrier=BarrierKind.FREEZE if role == 'open' else BarrierKind.NONE),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,),
        storage_codecs=MATRIX_STORAGE_CODECS,
    )
    return selected


def _phase_declaration(original):
    from .programme_wave_qualification import scientific_root_validator
    role = original.capability_key.rsplit('.', 1)[-1]
    native = original.execution_properties.native_effect
    ports = tuple(replace(port, port_id='admission', payload_schema=ScheduledProgrammeWaveAdmission.SCHEMA)
        if port.payload_schema == ScheduledCommitment.SCHEMA else port for port in original.input_ports)
    hooks = replace(original.scientific_hooks, scientific_root_validator=scientific_root_validator)

    selected = replace(original, capability_key=NAMESPACE+'.'+role,
        implementation_id=NAMESPACE+'.admitted-original-v2-'+role,
        input_ports=tuple(sorted(ports, key=lambda port: port.port_id)),
        conformance_check_ids=tuple(sorted(('actual-admission-dependency-custody',
            'actual-original-v2-configuration-native-join', 'complete-global-programme-scoped-wave'))),
        scientific_hooks=hooks,
        record_codecs={**_record_codecs(), **original.record_codecs, ScheduledProgrammeWaveAdmission.SCHEMA: ScheduledProgrammeWaveAdmission},
        runner_factory=lambda: (response.ScheduledPulseNativeRunner if native else response.ScheduledResponseRunner)(
            role, decoder=decode_response, manifest=selected.manifest())
            if role == 'physical-forecast' or role.startswith('response') else
            (core.ScheduledNativeRunner if native else core.ScheduledRunner)(role, decoder=decode_core, manifest=selected.manifest()))
    return selected


def _record_codecs():
    return {**core.output_codecs(), ScheduledCompactBank.SCHEMA: ScheduledCompactBank,
        ScheduledProgrammeWaveAdmission.SCHEMA: ScheduledProgrammeWaveAdmission,
        ScheduledProgrammeWaveResult.SCHEMA: ScheduledProgrammeWaveResult,
        response.ScheduledResponseNative.SCHEMA: response.ScheduledResponseNative,
        response.ScheduledResponseForecast.SCHEMA: response.ScheduledResponseForecast,
        response.ScheduledResponseScore.SCHEMA: response.ScheduledResponseScore}


def operation_declarations():
    phases = (_phase_declaration(row) for row in compact.operation_declarations()
        if row.capability_key.rsplit('.', 1)[-1] not in ('commit', 'calibrate', 'calibration-qualify'))
    return tuple(sorted((*phases, *(_control_declaration(role) for role in ('open', 'collect', 'collect-development'))),
        key=lambda row: row.capability_key))
