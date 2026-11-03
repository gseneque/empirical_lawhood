# SPDX-License-Identifier: MPL-2.0
"""Actual global sealed calibration and one separately authorized reveal."""

from empirical_lawhood.runtime.recursive_provider import (
    RecursiveOperationDeclaration, RecursiveScientificHooks, RecursiveExecutionProperties,
)


from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import AdmissionStatus, ScientificStatus
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.adjudication import AdjudicationEvaluability, ScientificAdjudicationRecord
from empirical_lawhood.runtime.artifacts import ArtifactProfile, CanonicalTaskReceipt, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskContext, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract

from .compact_records import ScheduledCompactBank
from .forecast import ScheduledCalibration
from .operation_bindings import BUDGET
from .programme_bindings import ScheduledProgrammeWaveCollectorConfig
from .programme_acquisition import ScheduledProgrammeAcquisitionCollectorConfig
from .programme_acquisition_custody import ScheduledProgrammeAcquisitionWaveCustody
from .programme_calibration import (
    CALIBRATE_TASK_ID, MAXIMUM_CALIBRATION_BYTES, MAXIMUM_CONFIG_BYTES, QUALIFY_TASK_ID,
    ScheduledProgrammeCalibrationConfig, ScheduledProgrammeCalibrationEvidence, ScheduledProgrammeWaveCustody,
    calibrate_programme, construction_supported,
)
from .programme_global import validate_programme_root
from .programme_records import NAMESPACE, validate_programme_bank
from .programme_reduction import ScheduledProgrammeWaveResult
from .programme_tail_freeze import ScheduledProgrammeFrozenTailCustody, ScheduledProgrammeTailFreezeConfig, TASK_ID as TAIL_FREEZE_TASK_ID

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT

SEALED, REVEAL = OutcomeAccess.EVALUATION_SEALED, OutcomeAccess.EVALUATOR_REVEAL
BLIND, PROSP = OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE
ROLES = ('calibrate', 'calibration-qualify')


def access(role):
    return SEALED if role == 'calibrate' else REVEAL


def visibility(role):
    return PROSP if role == 'calibrate' else VisibilityCeiling.OUTCOME_VISIBLE


def _classes(role):
    return (ScheduledProgrammeCalibrationConfig, ScheduledCompactBank, *(
        (ScheduledProgrammeFrozenTailCustody, ScheduledProgrammeWaveResult, ScheduledProgrammeWaveCustody, ScheduledProgrammeAcquisitionWaveCustody,
         CanonicalTaskReceipt, ScheduledProgrammeWaveCollectorConfig, ScheduledProgrammeAcquisitionCollectorConfig) if role == 'calibrate' else
        (ScheduledCalibration, ScheduledProgrammeCalibrationEvidence)))


def calibration_manifests():
    return tuple(row.manifest() for row in calibration_declarations())


def scientific_root_validator(config, context):
    task = CALIBRATE_TASK_ID if config.operation == 'calibrate' else QUALIFY_TASK_ID
    stage = ScientificStage.TRANSFORM if config.operation == 'calibrate' else ScientificStage.REVEAL
    if (type(config) is not ScheduledProgrammeCalibrationConfig or context.node_id != task
            or context.stage is not stage or context.outcome_access is not access(config.operation)
            or context.visibility_ceiling is not visibility(config.operation)
            or context.unit_ids != config.programme.group_ids or context.selected_unit_ids != config.programme.group_ids
            or not context.config_inputs):
        raise ValueError('programme global calibration changes exact original full64 study/task/stage/access')
    configs = tuple(v.record for v in context.config_inputs if type(v.record) is ScheduledProgrammeCalibrationConfig)
    freezes = tuple(v for v in context.config_inputs if type(v.record) is ScheduledProgrammeTailFreezeConfig)
    if (len(context.config_inputs) != 3 or len(configs) != 2 or config not in configs
            or any(type(c) is not ScheduledProgrammeCalibrationConfig or c.programme != config.programme
                or c.bank != config.bank or c.calibration_id != config.calibration_id or c.wave_custody != config.wave_custody
                for c in configs) or {c.operation for c in configs} != set(ROLES)
            or len(freezes) != 1 or freezes[0].node_id != TAIL_FREEZE_TASK_ID
            or freezes[0].record.programme != config.programme or freezes[0].record.bank != config.bank
            or freezes[0].record.wave_custody != config.wave_custody):
        raise ValueError('programme calibration root changes its closed global transform/reveal pair')
    validate_programme_root(config.programme, context)


def calibration_registrations():
    return tuple(row.registration() for row in calibration_declarations())


def _read(port, cls):
    raw = port.read()
    record = decode_canonical_bytes(raw, cls, maximum_bytes=MAXIMUM_CONFIG_BYTES
        if cls is ScheduledProgrammeCalibrationConfig else MAXIMUM_CALIBRATION_BYTES)
    if port.media_type != 'application/json' or port.size_bytes != len(raw) or raw != record.canonical_bytes():
        raise ValueError('programme calibration substitutes exact closed canonical input bytes')
    return record


def _publication_port(record, port, publication):
    logical, physical = publication.logical, publication.materialization
    if (port.artifact_id != logical.logical_artifact_id
            or port.payload_schema != record.SCHEMA or port.media_type != logical.media_type
            or port.size_bytes != physical.size_bytes or port.size_bytes != len(record.canonical_bytes())
            or record.fingerprint() != logical.content_sha256 or record.fingerprint() != physical.physical_sha256
            or port.outcome_access is not logical.outcome_access or port.visibility_ceiling is not logical.visibility_ceiling):
        raise ValueError('programme calibration changes actual original publication/materialization/bytes')


def _sealed_dependency(context, port):
    headers = tuple(r for r in context.dependency_receipts if port.materialization_id in r.output_materialization_ids)
    if (port.kind is not WorkerInputKind.DEPENDENCY or port.outcome_access is not SEALED
            or port.visibility_ceiling is not PROSP or len(headers) != 1 or headers[0].task_id != CALIBRATE_TASK_ID):
        raise ValueError('programme qualification drops actual sealed global calibration producer receipt')
    return headers[0]


def make_adjudication(context, config, calibration, evidence, bank, verified_custody=None):
    from .programme_runtime_views import ScheduledProgrammeVerifiedCalibrationCustody
    from dataclasses import replace
    if (type(config) is not ScheduledProgrammeCalibrationConfig or config.operation != 'calibration-qualify'
            or type(calibration) is not ScheduledCalibration or type(evidence) is not ScheduledProgrammeCalibrationEvidence
            or type(bank) is not ScheduledCompactBank):
        raise ValueError('programme qualification requires actual closed original config/calibration/evidence/bank')
    validate_programme_bank(config.programme, bank)
    if (evidence.configuration != replace(config, config_id='config.'+NAMESPACE+'.calibrate', operation='calibrate')
            or calibration != evidence.calibration):
        raise ValueError('programme qualification changes actual global producer config/calibration/evidence')
    if (context.scientific_adjudication_context is None
            or type(verified_custody) is not ScheduledProgrammeVerifiedCalibrationCustody
            or verified_custody.configuration != ObjectIdentity.from_record(config.config_id, config)
            or verified_custody.programme != config.programme.identity or verified_custody.bank != config.bank
            or verified_custody.execution_plan != context.scientific_adjudication_context.execution_plan
            or verified_custody.execution_task.object_id != context.task_id
            or verified_custody.evidence != evidence.identity
            or verified_custody.input_materialization_ids != context.input_materialization_ids
            or verified_custody.dependency_receipt_ids != context.dependency_receipt_ids
            or verified_custody.producing_receipt.object_id not in context.dependency_receipt_ids):
        raise PermissionError('programme qualification lacks complete actual current and original-wave runtime custody replay')
    authority, criterion = context.scientific_adjudication_context, bank.response_selection.calibration_criterion
    expected_cutoffs = tuple(ObjectIdentity.from_record(c.information_cutoff.cutoff_id, c.information_cutoff)
        for c in config.programme.cases)
    if (authority is None or authority.evidence_world_kind is not WorldKind.NUMERICAL_SIMULATOR
            or authority.outcome_access is not OutcomeAccess.EVALUATION_REVEALED
            or authority.visibility_ceiling is not VisibilityCeiling.OUTCOME_VISIBLE
            or authority.independent_unit_id != criterion.independent_unit_id
            or authority.information_cutoffs != expected_cutoffs or authority.plumbing_only
            or authority.fixture_scope_id is not None
            or any(getattr(c, 'prior_execution', None) is None for c in evidence.wave_custody)
            or calibration.model != bank.forecast_design.model):
        raise ValueError('programme qualification lacks genuine full64 issue/reveal/prior-wave execution authority')
    supported = construction_supported(evidence, criterion)
    reasons = ('scheduled-programme-complete-original-global-calibration-bank-qualified',) if supported else (
        'scheduled-programme-global-calibration-construction-conditions-not-supported',)
    return ScientificAdjudicationRecord('adjudication.'+context.run_id+'.'+context.task_id, context.run_id, context.task_id,
        authority.execution_plan, context.input_materialization_ids,
        tuple(sorted(p.logical_artifact_id for p in context.output_ports)), context.dependency_receipt_ids,
        authority.evidence_world_id, authority.evidence_world_kind, authority.relation, authority.independent_unit_id,
        authority.information_cutoffs, authority.visibility_ceiling, authority.outcome_access,
        AdjudicationEvaluability.EVALUABLE, ScientificStatus.SUPPORTED if supported else ScientificStatus.NOT_SUPPORTED,
        AdmissionStatus.ADMITTED if supported else AdmissionStatus.EMPTY, reasons)


class ScheduledProgrammeCalibrator:
    def __init__(self, role, manifest=None, *, verified_custody=None):
        if role not in ROLES:
            raise ValueError('unknown programme calibration operation')
        self.role = role
        self.manifest = manifest or next(m for m in calibration_manifests() if m.capability_key == NAMESPACE+'.'+role)
        self.verified_custody = verified_custody

    def execute(self, context):
        try:
            if (type(context) is not TaskContext or context.outcome_access is not access(self.role)
                    or context.permissions != self.manifest.permissions or not BUDGET.contains(context.resource_budget)):
                raise ValueError('programme calibration refuses changed actual runtime authority before reads')
            if self.role == 'calibration-qualify' and self.verified_custody is None:
                raise PermissionError('programme qualification requires parent-side original custody preparation before reads')
            types = {c.SCHEMA: c for c in _classes(self.role)}
            values = {}
            for port in context.input_ports:
                cls = types.get(port.payload_schema)
                if cls is None:
                    raise ValueError('programme calibration receives an undeclared input schema')
                value = _read(port, cls)
                values.setdefault(cls, []).append((value, port))
            if any(len(values.get(cls, ())) != 1 for cls in (ScheduledProgrammeCalibrationConfig, ScheduledCompactBank)):
                raise ValueError('programme calibration omits exact actual configuration/shared bank')
            config, config_port = values[ScheduledProgrammeCalibrationConfig][0]
            bank, bank_port = values[ScheduledCompactBank][0]
            task_id = CALIBRATE_TASK_ID if self.role == 'calibrate' else QUALIFY_TASK_ID
            if (config.operation != self.role or context.task_id != task_id or context.config.config_id != config.config_id
                    or context.config.config_schema != config.SCHEMA or context.config.content_sha256 != config.fingerprint()
                    or context.config.artifact_id != config_port.artifact_id
                    or any(p.kind is not WorkerInputKind.EXTERNAL or p.outcome_access is not BLIND
                        or p.visibility_ceiling is not PROSP for p in (config_port, bank_port))
                    or bank_port.artifact_id != bank.bank_id or bank.fingerprint() != config.bank.object_fingerprint):
                raise ValueError('programme calibration substitutes its exact global config/bank/task identity')
            validate_programme_bank(config.programme, bank)
            if self.role == 'calibrate':
                frozen = values.get(ScheduledProgrammeFrozenTailCustody, ())
                if len(frozen) != 1:
                    raise ValueError('programme calibration omits actual current tail custody freeze')
                freeze, freeze_port = frozen[0]
                headers = tuple(r for r in context.dependency_receipts if freeze_port.materialization_id in r.output_materialization_ids)
                if (freeze.configuration.programme != config.programme or freeze.configuration.bank != config.bank
                        or freeze.configuration.wave_custody != config.wave_custody
                        or freeze_port.kind is not WorkerInputKind.DEPENDENCY
                        or freeze_port.outcome_access is not BLIND or freeze_port.visibility_ceiling is not PROSP
                        or len(headers) != 1 or headers[0].task_id != TAIL_FREEZE_TASK_ID):
                    raise ValueError('programme calibration substitutes actual fixed tail freeze or its successful dependency')
                custody_type = ScheduledProgrammeAcquisitionWaveCustody if config.wave_custody[0].object_schema == ScheduledProgrammeAcquisitionWaveCustody.SCHEMA else ScheduledProgrammeWaveCustody
                collector_type = ScheduledProgrammeAcquisitionCollectorConfig if custody_type is ScheduledProgrammeAcquisitionWaveCustody else ScheduledProgrammeWaveCollectorConfig
                required = (custody_type, ScheduledProgrammeWaveResult, CanonicalTaskReceipt, collector_type)
                if any(len(values.get(cls, ())) != 16 for cls in required):
                    raise ValueError('programme calibration requires complete16 actual wave custody inputs')
                if any(values.get(cls) for cls in (ScheduledProgrammeWaveCustody, ScheduledProgrammeAcquisitionWaveCustody,
                        ScheduledProgrammeWaveCollectorConfig, ScheduledProgrammeAcquisitionCollectorConfig) if cls not in required):
                    raise ValueError('programme calibration mixes old and acquisition custody contracts')
                def indexed(cls, key):
                    rows = values.get(cls, ())
                    result = {key(v): (v, p) for v, p in rows}
                    if len(result) != len(rows):
                        raise ValueError('programme calibration duplicates an actual wave custody input')
                    return result
                bindings = indexed(custody_type, lambda v: v.identity)
                results = indexed(ScheduledProgrammeWaveResult, lambda v: v.identity)
                receipts = indexed(CanonicalTaskReceipt, lambda v: v.receipt_id)
                configs = indexed(collector_type, lambda v: v.config_id)
                ordered_bindings, ordered_results = [], []
                if set(bindings) != set(config.wave_custody):
                    raise ValueError('programme calibration substitutes frozen custody pins')
                for pin in config.wave_custody:
                    binding, binding_port = bindings[pin]
                    if (binding_port.kind is not WorkerInputKind.EXTERNAL or binding_port.outcome_access is not BLIND
                            or binding_port.visibility_ceiling is not PROSP):
                        raise ValueError('programme calibration changes its frozen source custody boundary')
                    result, result_port = results[binding.result]
                    receipt, receipt_port = receipts[binding.receipt.receipt_id]
                    collector_config, collector_port = configs[binding.configuration.config_id]
                    for record, port, publication in ((result, result_port, binding.publication),
                            (receipt, receipt_port, binding.receipt_publication),
                            (collector_config, collector_port, binding.configuration_publication)):
                        _publication_port(record, port, publication)
                    if receipt != binding.receipt or collector_config != binding.configuration:
                        raise ValueError('programme calibration substitutes actual receipt/configuration values')
                    if result_port.kind is WorkerInputKind.DEPENDENCY:
                        headers = tuple(r for r in context.dependency_receipts if result_port.materialization_id in r.output_materialization_ids)
                        if len(headers) != 1 or headers[0].receipt_id != receipt.receipt_id or headers[0].task_id != receipt.task_id:
                            raise ValueError('programme calibration changes actual wave dependency custody')
                    ordered_bindings.append(binding)
                    ordered_results.append(result)
                calibration, evidence = calibrate_programme(config, bank, ordered_results, ordered_bindings)
                products = {'product': calibration, 'evidence': evidence}
            else:
                if any(len(values.get(cls, ())) != 1 for cls in (ScheduledCalibration, ScheduledProgrammeCalibrationEvidence)):
                    raise ValueError('programme qualification omits its actual semantic and evidence outputs')
                calibration, calibration_port = values[ScheduledCalibration][0]
                evidence, evidence_port = values[ScheduledProgrammeCalibrationEvidence][0]
                if _sealed_dependency(context, calibration_port) != _sealed_dependency(context, evidence_port):
                    raise ValueError('programme qualification aliases separate calibration/evidence producers')
                products = {'adjudication': make_adjudication(context, config, calibration, evidence, bank, self.verified_custody)}
            outputs = {p.output_id.rsplit('.', 1)[-1]: p for p in context.output_ports}
            if set(outputs) != set(products) or any(outputs[k].payload_schema != v.SCHEMA
                    or outputs[k].profile is not ArtifactProfile.CANONICAL_JSON
                    or outputs[k].output_id != task_id+'.'+k or len(v.canonical_bytes()) > MAXIMUM_CALIBRATION_BYTES
                    for k, v in products.items()):
                raise ValueError('programme calibration changes its exact bounded actual output census')
            return RunnerResult(tuple(sorted((TaskOutputPayload(outputs[k].output_id, v.canonical_bytes())
                for k, v in products.items()), key=lambda o: o.output_id)),
                (ReceiptCheck('scheduled-programme-original-global64-calibration-custody', True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def calibration_factories():
    return tuple(row.provider_factory() for row in calibration_declarations())


def _calibration_declaration(role):
    def port(name, cls, minimum=1, maximum=1):
        return RecursivePortContract(name, cls.SCHEMA, 'application/json', MAXIMUM_CALIBRATION_BYTES, minimum_count=minimum, maximum_count=maximum)
    inputs = [port('bank', ScheduledCompactBank)]
    if role == 'calibrate':
        inputs.extend((port('tail-freeze', ScheduledProgrammeFrozenTailCustody), port('waves', ScheduledProgrammeWaveResult, 16, 16), port('wave-custody', ScheduledProgrammeWaveCustody, 0, 16), port('acquisition-wave-custody', ScheduledProgrammeAcquisitionWaveCustody, 0, 16), port('wave-receipts', CanonicalTaskReceipt, 16, 16), port('wave-configurations', ScheduledProgrammeWaveCollectorConfig, 0, 16), port('acquisition-wave-configurations', ScheduledProgrammeAcquisitionCollectorConfig, 0, 16)))
        outputs = (OutputTemplate('evidence', ScheduledProgrammeCalibrationEvidence.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'), OutputTemplate('product', ScheduledCalibration.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'))
    else:
        inputs.extend((port('calibration', ScheduledCalibration), port('evidence', ScheduledProgrammeCalibrationEvidence)))
        outputs = (OutputTemplate('adjudication', ScientificAdjudicationRecord.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'),)
    def prepare(supplier, runner):
        from empirical_lawhood.runtime.execution import ParentPreparedTaskRunner
        return ParentPreparedTaskRunner(runner.manifest, lambda context: supplier.prepare_programme_task(context, runner))
    selected = RecursiveOperationDeclaration(
        capability_key=NAMESPACE + "." + role,
        capability_version="1.0.0",
        implementation_id='complete-global64-calibration-' + role + '.v1',
        kind=CapabilityKind.TRANSFORM if role == 'calibrate' else CapabilityKind.EVALUATOR,
        config_record_type=ScheduledProgrammeCalibrationConfig,
        stage=ScientificStage.TRANSFORM if role == 'calibrate' else ScientificStage.REVEAL,
        input_ports=tuple(sorted(inputs, key=lambda p: p.port_id)),
        outputs=outputs,
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_SEALED_OUTCOMES, *((CapabilityPermission.REVEAL_OUTCOMES,) if role == "calibration-qualify" else ())))),
        evidence_ceiling=EvidenceCeiling.RESPONSE,
        outcome_access=access(role),
        visibility_ceiling=visibility(role),
        resources=BUDGET,
        conformance_check_ids=tuple(sorted(tuple(sorted(('one-global576-max135-rank62', 'exact-original-wave-publication-receipts', 'negative-native-numerical-and-nonuse-preservation', 'separate-genuine-global-reveal'))))),
        runner_factory=lambda: ScheduledProgrammeCalibrator(role, selected.manifest()),
        record_codecs={ScheduledCalibration.SCHEMA: ScheduledCalibration, ScheduledProgrammeCalibrationEvidence.SCHEMA: ScheduledProgrammeCalibrationEvidence, ScientificAdjudicationRecord.SCHEMA: ScientificAdjudicationRecord, **{kind.SCHEMA: kind for kind in _classes(role)}},
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=lambda c: tuple(sorted({c.bank.object_fingerprint, c.programme.fingerprint()})), scientific_unit_ids=lambda c: c.programme.group_ids, scientific_root_validator=scientific_root_validator, adjudication_output_id='adjudication' if role == 'calibration-qualify' else None),
        execution_properties=RecursiveExecutionProperties(barrier=BarrierKind.REVEAL if role == 'calibration-qualify' else BarrierKind.NONE, runner_preparation_factory=prepare if role == "calibration-qualify" else None),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,),
    )
    return selected


def calibration_declarations():
    return tuple(_calibration_declaration(role) for role in ROLES)
