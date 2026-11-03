# SPDX-License-Identifier: MPL-2.0
"""Actual local acquisition providers with explicit new admission contracts.

Unchanged v2 mathematical configurations and native task IDs remain literal.
The new local controls cannot qualify a global law or replace original parent
custody. All workers consume their actual typed ports and issued contexts.
"""

from empirical_lawhood.runtime.recursive_provider import (
    RecursiveOperationDeclaration, RecursiveScientificHooks, RecursiveExecutionProperties,
)

from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from dataclasses import replace

from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.runtime.artifacts import ArtifactProfile, CanonicalTaskReceipt
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import TaskContext, WorkerInputKind
from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract

from .commitment import ScheduledCommitment
from . import compact_bindings as compact, operation_bindings as core, response_bindings as response
from .compact_records import ScheduledCompactBank, compact_identity
from .programme_acquisition import (NAMESPACE, ScheduledProgrammeAcquisitionAdmission,
    ScheduledProgrammeAcquisitionAdmissionConfig, ScheduledProgrammeAcquisitionCollectorConfig)
from .programme_bindings import _collect_case, _dependency, _record
from .programme_composition import NATIVE_PHASES, expected_global_commitment, phase_roles
from .programme_global import ScheduledProgrammeGlobalCommit, global_committed
from .programme_confirmation import ScheduledProgrammeConfirmationGlobalCommit
from .programme_records import validate_programme_bank
from .programme_reduction import ScheduledProgrammeWaveResult

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT

MAXIMUM_RECORD_BYTES = 16*1024**2
BLIND, PROSP = OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE




def operation_manifests():
    return tuple(row.manifest() for row in operation_declarations())


def operation_registrations():
    return tuple(row.registration() for row in operation_declarations())


def _authenticate_admission(admission, bank):
    validate_programme_bank(admission.programme, bank)
    if (admission.bank != compact_identity(bank)
            or admission.semantic_commitment != expected_global_commitment(bank)):
        raise ValueError('acquisition admission changes original full programme or exact semantic commitment')
    binding = admission.global_parent_binding
    binding.__post_init__()
    if admission.programme.mode == 'E4_CONFIRMATION':
        from .programme_qualified_parent import validate_qualified_parent_declaration
        validate_qualified_parent_declaration(bank, admission.scope.qualified_parent)
        if (binding.configuration.qualified_parent != admission.scope.qualified_parent
                or binding.parent.qualified_parent != admission.scope.qualified_parent.identity):
            raise ValueError('confirmation acquisition substitutes its actual genuine parent declaration')
    elif binding.parent != global_committed(binding.configuration, bank):
        raise ValueError('acquisition admission substitutes actual original global preparation')


def _read_phase(context, role, state):
    if type(context) is not TaskContext or context.outcome_access is not core.phase_access(role):
        raise ValueError('programme phase refuses unsupported issued access before input reads')
    phase = next(p for p in compact.PHASES if p[0] == role)
    cls = compact.config_type(role)
    types = {cls.SCHEMA: cls, **{(ScheduledProgrammeAcquisitionAdmission if t is ScheduledCommitment else t).SCHEMA:
        ScheduledProgrammeAcquisitionAdmission if t is ScheduledCommitment else t for _, t in phase[1]
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
        admission, port = values[ScheduledProgrammeAcquisitionAdmission.SCHEMA][0]
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
            if (port is not state.get('admission_port') or port.payload_schema != ScheduledProgrammeAcquisitionAdmission.SCHEMA
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
    cls = ScheduledProgrammeAcquisitionAdmissionConfig if role == 'open' else ScheduledProgrammeAcquisitionCollectorConfig
    types = {cls.SCHEMA: cls, ScheduledCompactBank.SCHEMA: ScheduledCompactBank}
    if role == 'open':
        types[ScheduledProgrammeGlobalCommit.SCHEMA] = ScheduledProgrammeGlobalCommit
        types[ScheduledProgrammeConfirmationGlobalCommit.SCHEMA] = ScheduledProgrammeConfirmationGlobalCommit
        types[CanonicalTaskReceipt.SCHEMA] = CanonicalTaskReceipt
    else:
        types[ScheduledProgrammeAcquisitionAdmission.SCHEMA] = ScheduledProgrammeAcquisitionAdmission
        types.update({p[2].SCHEMA: p[2] for p in compact.PHASES if p[0] not in ('commit', 'calibrate', 'calibration-qualify')})
    values = {}
    for port in context.input_ports:
        if port.payload_schema not in types:
            raise ValueError('programme control receives an undeclared scientific/custody input')
        value = _record(port, types[port.payload_schema])
        values.setdefault(value.SCHEMA, []).append((value, port))
    for schema in (cls.SCHEMA, ScheduledCompactBank.SCHEMA):
        if len(values.get(schema, ())) != 1:
            raise ValueError('programme control omits an exact single configuration/bank/parent')
    parent_rows = sum(len(values.get(schema, ())) for schema in (ScheduledProgrammeGlobalCommit.SCHEMA,
        ScheduledProgrammeConfirmationGlobalCommit.SCHEMA)) if role == 'open' else len(values.get(ScheduledProgrammeAcquisitionAdmission.SCHEMA, ()))
    if parent_rows != 1:
        raise ValueError('acquisition control omits or aliases its exact mode-specific parent')
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


class ProgrammeAcquisitionOpener:
    def __init__(self, manifest=None):
        self.manifest = manifest or next(m for m in operation_manifests() if m.capability_key == NAMESPACE+'.open')

    def execute(self, context):
        try:
            config, bank, values = _read_control(context, 'open')
            validate_programme_bank(config.programme, bank)
            binding = config.global_parent_binding
            binding.__post_init__()
            parent, port = values[binding.parent.SCHEMA][0]
            receipt, receipt_port = values[CanonicalTaskReceipt.SCHEMA][0]
            if (parent != binding.parent or receipt != binding.receipt
                    or port.outcome_access is not BLIND or port.visibility_ceiling is not PROSP
                    or receipt_port.kind is not WorkerInputKind.EXTERNAL
                    or receipt_port.outcome_access is not BLIND or receipt_port.visibility_ceiling is not PROSP):
                raise ValueError('acquisition opener substitutes its actual mode-specific global publication/receipt')
            from .commitment import require_publication_copy
            require_publication_copy(parent, port, binding.publication)
            require_publication_copy(receipt, receipt_port, binding.receipt_publication)
            if port.kind is WorkerInputKind.DEPENDENCY:
                _dependency(context, port, compact.NAMESPACE+'.commit')
            elif port.kind is not WorkerInputKind.EXTERNAL:
                raise ValueError('acquisition opener loses actual global preparation custody')
            admission = ScheduledProgrammeAcquisitionAdmission('admission.acquisition.'+config.wave.wave_id,
                config.identity, config.scope, binding, parent.semantic_commitment)
            _authenticate_admission(admission, bank)
            return core._outputs(context, admission)
        finally:
            for port in context.input_ports:
                port.close()


class ProgrammeAcquisitionCollector:
    def __init__(self, role='collect', manifest=None):
        self.role = role
        self.manifest = manifest or next(m for m in operation_manifests() if m.capability_key == NAMESPACE+'.'+role)

    def execute(self, context):
        try:
            config, bank, values = _read_control(context, self.role)
            admission, admission_port = values[ScheduledProgrammeAcquisitionAdmission.SCHEMA][0]
            _authenticate_admission(admission, bank)
            _dependency(context, admission_port, admission.wave.wave_id+'.open')
            if (config.programme != admission.programme.identity or config.wave != admission.wave
                    or config.admission != admission.identity or config.mode != admission.programme.mode or config.scope != admission.scope.identity):
                raise ValueError('programme collector substitutes its actual admitted complete wave')
            cases = tuple(c for c in admission.programme.cases if c.root_id in admission.wave.root_ids)
            by_source = {c.source: c for c in cases}
            received = {c.root_id: {} for c in cases}
            for schema, rows in values.items():
                if schema in (config.SCHEMA, ScheduledCompactBank.SCHEMA, ScheduledProgrammeAcquisitionAdmission.SCHEMA):
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
    from .programme_acquisition_qualification import scientific_root_validator
    access = BLIND if role == 'open' else OutcomeAccess.DEVELOPMENT_VISIBLE if role.endswith('-development') else OutcomeAccess.EVALUATION_SEALED
    ceiling = EvidenceCeiling.NON_PROMOTABLE
    cls = ScheduledProgrammeAcquisitionAdmissionConfig if role == 'open' else ScheduledProgrammeAcquisitionCollectorConfig
    output = ScheduledProgrammeAcquisitionAdmission if role == 'open' else ScheduledProgrammeWaveResult
    ports = [RecursivePortContract('bank', ScheduledCompactBank.SCHEMA, 'application/json', MAXIMUM_RECORD_BYTES)]
    if role == 'open':
        ports.append(RecursivePortContract('global-parent', ScheduledProgrammeGlobalCommit.SCHEMA, 'application/json', MAXIMUM_RECORD_BYTES, minimum_count=0))
        ports.append(RecursivePortContract('confirmation-global-parent', ScheduledProgrammeConfirmationGlobalCommit.SCHEMA, 'application/json', MAXIMUM_RECORD_BYTES, minimum_count=0))
        ports.append(RecursivePortContract('global-parent-receipt', CanonicalTaskReceipt.SCHEMA, 'application/json', MAXIMUM_RECORD_BYTES))
    else:
        ports.append(RecursivePortContract('admission', ScheduledProgrammeAcquisitionAdmission.SCHEMA, 'application/json', MAXIMUM_RECORD_BYTES))
        for phase, _, product, _, _ in compact.PHASES:
            if phase not in ('commit', 'calibrate', 'calibration-qualify', 'continue-development', 'full-numerical-development', 'responses-development', 'response-score-development', 'forecast-calibrated'):
                ports.append(RecursivePortContract('products.' + phase, product.SCHEMA, 'application/json', MAXIMUM_RECORD_BYTES, minimum_count=1, maximum_count=None))
    selected = RecursiveOperationDeclaration(
        capability_key=NAMESPACE + "." + role,
        capability_version="1.0.0",
        implementation_id=NAMESPACE + '.local-acquisition-original-v2-state-' + role,
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
        conformance_check_ids=tuple(sorted(('actual-admission-dependency-custody', 'local-acquisition-with-original-global-programme', 'unchanged-original-numerical-subjects'))),
        runner_factory=lambda: ProgrammeAcquisitionOpener(selected.manifest()) if role == "open" else ProgrammeAcquisitionCollector(role, selected.manifest()),
        record_codecs={**_record_codecs(), **{kind.SCHEMA: kind for kind in (ScheduledProgrammeAcquisitionAdmission, ScheduledProgrammeGlobalCommit, CanonicalTaskReceipt, ScheduledProgrammeConfirmationGlobalCommit)}},
        scientific_hooks=RecursiveScientificHooks(scientific_unit_ids=lambda c: c.wave.group_ids, scientific_operand_sha256s=lambda c: (c.bank.object_fingerprint,), scientific_root_validator=scientific_root_validator),
        execution_properties=RecursiveExecutionProperties(barrier=BarrierKind.FREEZE if role == 'open' else BarrierKind.NONE),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,),
        storage_codecs=MATRIX_STORAGE_CODECS,
    )
    return selected


def _phase_declaration(original):
    from .programme_acquisition_qualification import scientific_root_validator
    role = original.capability_key.rsplit('.', 1)[-1]
    native = original.execution_properties.native_effect
    ports = tuple(replace(port, port_id='admission', payload_schema=ScheduledProgrammeAcquisitionAdmission.SCHEMA)
        if port.payload_schema == ScheduledCommitment.SCHEMA else port for port in original.input_ports)
    hooks = replace(original.scientific_hooks, scientific_root_validator=scientific_root_validator)

    if role == 'forecast-calibrated':
        from .programme_calibration import ScheduledProgrammeCalibrationEvidence
        from .programme_qualified_parent import qualified_parent_assessor, prior_execution_bindings, prior_execution_scope_validator
        hooks = replace(hooks, qualified_parent_assessor=qualified_parent_assessor,
            qualified_parent_evidence_schema_ids=(ScheduledProgrammeCalibrationEvidence.SCHEMA,),
            qualified_parent_prior_execution_bindings=prior_execution_bindings,
            qualified_parent_prior_execution_scope_validator=prior_execution_scope_validator)
    selected = replace(original, capability_key=NAMESPACE+'.'+role,
        implementation_id=NAMESPACE+'.acquisition-original-v2-'+role,
        input_ports=tuple(sorted(ports, key=lambda port: port.port_id)),
        conformance_check_ids=tuple(sorted(('actual-admission-dependency-custody',
            'actual-original-v2-configuration-native-join', 'complete-local-whole-group-acquisition'))),
        scientific_hooks=hooks,
        record_codecs={**_record_codecs(), **original.record_codecs, ScheduledProgrammeAcquisitionAdmission.SCHEMA: ScheduledProgrammeAcquisitionAdmission},
        runner_factory=lambda: (response.ScheduledPulseNativeRunner if native else response.ScheduledResponseRunner)(
            role, decoder=decode_response, manifest=selected.manifest())
            if role == 'physical-forecast' or role.startswith('response') else
            (core.ScheduledNativeRunner if native else core.ScheduledRunner)(role, decoder=decode_core, manifest=selected.manifest()))
    return selected


def _record_codecs():
    return {**core.output_codecs(), ScheduledCompactBank.SCHEMA: ScheduledCompactBank,
        ScheduledProgrammeAcquisitionAdmission.SCHEMA: ScheduledProgrammeAcquisitionAdmission,
        ScheduledProgrammeWaveResult.SCHEMA: ScheduledProgrammeWaveResult,
        response.ScheduledResponseNative.SCHEMA: response.ScheduledResponseNative,
        response.ScheduledResponseForecast.SCHEMA: response.ScheduledResponseForecast,
        response.ScheduledResponseScore.SCHEMA: response.ScheduledResponseScore}


def operation_declarations():
    phases = (_phase_declaration(row) for row in compact.operation_declarations()
        if row.capability_key.rsplit('.', 1)[-1] not in ('commit', 'calibrate', 'calibration-qualify'))
    return tuple(sorted((*phases, *(_control_declaration(role) for role in ('open', 'collect', 'collect-development'))),
        key=lambda row: row.capability_key))
