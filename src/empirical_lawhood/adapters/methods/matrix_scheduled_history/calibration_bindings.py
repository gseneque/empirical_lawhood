# SPDX-License-Identifier: MPL-2.0
"""Actual sealed score reduction and separately revealed calibration assessment."""

from empirical_lawhood.runtime.recursive_provider import (
    RecursiveOperationDeclaration, RecursiveScientificHooks, RecursiveExecutionProperties,
)

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.kernel.status import AdmissionStatus, ScientificStatus
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.adjudication import AdjudicationEvaluability, ScientificAdjudicationRecord
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskContext, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract

from .calibration import calibrate, validate_calibration_sources
from .commitment import ScheduledCommitment, ScheduledCommitmentConfig, committed
from .forecast import ScheduledCalibration, ScheduledForecastSeal
from .records import NAMESPACE, identity
from .response_records import ScheduledResponseScore
from .source_index import ResolvedScheduledSource

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT

CALIBRATE_KEY, QUALIFY_KEY = NAMESPACE+'.calibrate', NAMESPACE+'.calibration-qualify'


@dataclass(frozen=True, slots=True)
class ScheduledCalibrationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/calibration-config'
    VERSION: ClassVar[str] = '2.0.0'
    config_id: str
    operation: str
    commitment: ObjectIdentity
    calibration_id: str
    group_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.calibration_id)
        require_sorted_unique_strings(self.group_ids, field_name='complete calibration groups', allow_empty=False)
        if (self.operation not in ('calibrate', 'calibration-qualify') or self.config_id != 'config.'+NAMESPACE+'.'+self.operation
                or type(self.commitment) is not ObjectIdentity
                or (self.commitment.object_schema, self.commitment.object_version) !=
                   (ScheduledCommitmentConfig.SCHEMA, ScheduledCommitmentConfig.VERSION)):
            raise ValueError('scheduled calibration config changes frozen complete original CALIBRATION bank')


@dataclass(frozen=True, slots=True)
class BoundScheduledCalibrationConfig:
    """One actual calibration operation and its explicitly resolved denominator."""
    record: object
    commitment: ScheduledCommitmentConfig
    sources: tuple[ResolvedScheduledSource, ...]
    full_assessments: tuple = ()
    bank: object = None

    def __post_init__(self):
        from .compact_records import ScheduledCompactBank, ScheduledCompactCalibrationConfig, compact_identity
        if type(self.commitment) is not ScheduledCommitmentConfig:
            raise TypeError('scheduled calibration requires its actual shared current commitment')
        if type(self.record) is ScheduledCalibrationConfig:
            if self.bank is not None or self.record.commitment != identity(self.commitment):
                raise ValueError('scheduled calibration substitutes its shared current commitment pin')
        elif type(self.record) is ScheduledCompactCalibrationConfig:
            if type(self.bank) is not ScheduledCompactBank or self.record.bank != compact_identity(self.bank):
                raise ValueError('compact calibration substitutes its actual shared bank pin')
            for name in ('reservation', 'specification', 'provenances', 'sources', 'selected_root_ids',
                    'audit', 'audit_publication', 'forecast_design', 'response_selection', 'response_selection_publication'):
                if getattr(self.commitment, name) != getattr(self.bank, name):
                    raise ValueError('compact calibration changes its actual shared scientific operands')
        else:
            raise TypeError('scheduled calibration requires its exact current canonical configuration')
        if (type(self.sources) is not tuple or not self.sources
                or any(type(source) is not ResolvedScheduledSource for source in self.sources)
                or tuple(source.root_id for source in self.sources) != self.commitment.selected_root_ids
                or tuple(source.reference for source in self.sources) != tuple(reference for reference in
                    self.commitment.sources if reference.root_id in self.commitment.selected_root_ids)
                or tuple(sorted({source.root.root.independent_group_id for source in self.sources})) != self.record.group_ids
                or any(source.root.root.role is not MatrixProgrammeRole.CALIBRATION for source in self.sources)
                or self.commitment.response_selection is None
                or self.commitment.response_selection.calibration_criterion is None):
            raise ValueError('scheduled calibration thins or changes its exact frozen CALIBRATION denominator')

    @property
    def config_id(self): return self.record.config_id
    @property
    def operation(self): return self.record.operation
    @property
    def calibration_id(self): return self.record.calibration_id
    @property
    def group_ids(self): return self.record.group_ids
    @property
    def SCHEMA(self): return self.record.SCHEMA
    @property
    def VERSION(self): return self.record.VERSION
    def fingerprint(self): return self.record.fingerprint()
    def canonical_bytes(self): return self.record.canonical_bytes()


CALIBRATION_PHASES = (
    ('calibrate', (('commitment', ScheduledCommitment), ('commitment-config', ScheduledCommitmentConfig), ('forecasts', ScheduledForecastSeal), ('scores', ScheduledResponseScore)), ScheduledCalibration, ScientificStage.TRANSFORM),
    ('calibration-qualify', (('calibration', ScheduledCalibration), ('commitment', ScheduledCommitment), ('commitment-config', ScheduledCommitmentConfig)), ScientificAdjudicationRecord, ScientificStage.REVEAL),
)


def access(role):
    return OutcomeAccess.EVALUATION_SEALED if role == 'calibrate' else OutcomeAccess.EVALUATOR_REVEAL


def visibility(role):
    return VisibilityCeiling.PROSPECTIVE if role == 'calibrate' else VisibilityCeiling.OUTCOME_VISIBLE


def units(config):
    return config.group_ids


def calibration_manifests():
    return tuple(row.manifest() for row in calibration_declarations())




class ScheduledCalibrator:
    def __init__(self, role, *, decoder=None, manifest=None, namespace=NAMESPACE, dependency_checker=None):
        self.role, self.namespace = role, namespace
        self.manifest = manifest if manifest is not None else next(m for m in calibration_manifests() if m.capability_key == NAMESPACE+'.'+role)
        self._decoder, self._dependency_checker = decoder, dependency_checker

    def _decode(self, context):
        if self._decoder is not None:
            return self._decoder(context, self.role)
        classes = {ScheduledCalibrationConfig.SCHEMA: ScheduledCalibrationConfig,
            **{t.SCHEMA: t for _, t in next(p for p in CALIBRATION_PHASES if p[0] == self.role)[1]}}
        values = {t: [] for t in classes.values()}
        for port in context.input_ports:
            cls = classes.get(port.payload_schema)
            if cls is None:
                raise ValueError('scheduled calibration receives undeclared private/outcome operands')
            values[cls].append((decode_canonical_bytes(port.read(), cls, maximum_bytes=None), port))
        if (len(values[ScheduledCalibrationConfig]) != 1 or len(values[ScheduledCommitment]) != 1
                or len(values[ScheduledCommitmentConfig]) != 1):
            raise ValueError('scheduled calibration omits original config/commitment census')
        config, config_port = values[ScheduledCalibrationConfig][0]
        shared, shared_port = values[ScheduledCommitmentConfig][0]
        from .operation_bindings import require_shared_config
        from .qualification import selected_sources
        index = require_shared_config(shared, shared_port, expected=config.commitment)
        return BoundScheduledCalibrationConfig(config, shared, selected_sources(shared, index=index)), config_port, values

    def _dependency(self, context, port, root_id, owner, **kwargs):
        if self._dependency_checker is None:
            from .operation_bindings import _dependency
            return _dependency(context, port, root_id, owner, **kwargs)
        return self._dependency_checker(context, port, root_id, owner, **kwargs)

    def execute(self, context):
        from .operation_bindings import BUDGET
        try:
            if type(context) is not TaskContext or context.outcome_access is not access(self.role):
                raise ValueError('scheduled calibration refuses unsupported access before score reads')
            config, config_port, values = self._decode(context)
            if len(values[ScheduledCommitment]) != 1:
                raise ValueError('scheduled calibration omits original config/commitment census')
            if type(config) is not BoundScheduledCalibrationConfig:
                raise ValueError('scheduled calibration requires its explicit current shared scientific context')
            if type(config.record) is ScheduledCalibrationConfig:
                if self.namespace != NAMESPACE:
                    raise ValueError('scheduled calibration changes its registered namespace')
                expected_commitment = committed(config.commitment)
            else:
                from .compact_records import (NAMESPACE as COMPACT_NAMESPACE, ScheduledCompactCalibrationConfig,
                    ScheduledCompactCommitmentConfig, compact_committed)
                if self.namespace != COMPACT_NAMESPACE or type(config.record) is not ScheduledCompactCalibrationConfig:
                    raise ValueError('scheduled calibration requires its exact current compact config')
                expected_commitment = compact_committed(ScheduledCompactCommitmentConfig('config.'+self.namespace+'.commit', config.bank))
            if (config.operation != self.role or context.task_id != self.namespace+'.'+self.role or context.config.config_id != config.config_id
                    or context.config.config_schema != config.SCHEMA or context.config.content_sha256 != config.fingerprint()
                    or context.config.artifact_id != config_port.artifact_id or context.permissions != self.manifest.permissions
                    or not BUDGET.contains(context.resource_budget) or values[ScheduledCommitment][0][0] != expected_commitment):
                raise ValueError('scheduled calibration changes actual issued complete original scope')
            self._dependency(context, values[ScheduledCommitment][0][1], '', 'commit')
            if self.role == 'calibrate':
                indexed_scores = {v.root_id: (v, p) for v, p in values[ScheduledResponseScore]}
                indexed_forecasts = {v.feature.root_id: (v, p) for v, p in values[ScheduledForecastSeal]}
                roots = config.commitment.selected_root_ids
                if (tuple(sorted(indexed_scores)) != roots or tuple(sorted(indexed_forecasts)) != roots
                        or len(indexed_scores) != len(values[ScheduledResponseScore]) or len(indexed_forecasts) != len(values[ScheduledForecastSeal])):
                    raise ValueError('scheduled calibration thins/duplicates actual CALIBRATION score/point custody')
                custody = {}
                for root in roots:
                    _, score_port = indexed_scores[root]
                    _, forecast_port = indexed_forecasts[root]
                    self._dependency(context, score_port, root, 'response-score', access=OutcomeAccess.EVALUATION_SEALED)
                    self._dependency(context, forecast_port, root, 'forecast')
                    score_receipt = next(r for r in context.dependency_receipts if score_port.materialization_id in r.output_materialization_ids)
                    forecast_receipt = next(r for r in context.dependency_receipts if forecast_port.materialization_id in r.output_materialization_ids)
                    custody[root] = score_receipt.receipt_id, forecast_receipt.receipt_id, score_port.materialization_id, forecast_port.materialization_id
                product = calibrate(config.commitment, tuple(v for v, _ in indexed_scores.values()),
                    tuple(v for v, _ in indexed_forecasts.values()), custody=custody, calibration_id=config.calibration_id,
                    sources=config.sources)
            else:
                if len(values[ScheduledCalibration]) != 1:
                    raise ValueError('scheduled qualification omits actual original calibration value')
                product, port = values[ScheduledCalibration][0]
                receipts = tuple(r for r in context.dependency_receipts if port.materialization_id in r.output_materialization_ids)
                if (port.kind is not WorkerInputKind.DEPENDENCY or port.outcome_access is not OutcomeAccess.EVALUATION_SEALED
                        or len(receipts) != 1 or receipts[0].task_id != self.namespace+'.calibrate'):
                    raise ValueError('scheduled qualification substitutes original sealed calibration ordinary receipt')
                product = make_adjudication(context, config, product)
            if len(context.output_ports) != 1 or context.output_ports[0].payload_schema != product.SCHEMA:
                raise ValueError('scheduled calibration changes original selected complete output contract')
            return RunnerResult((TaskOutputPayload(context.output_ports[0].output_id, product.canonical_bytes()),),
                (ReceiptCheck('scheduled-original-whole-group-calibration-census', True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def make_adjudication(context, config, calibration):
    from .qualification import cutoffs
    if type(config) is not BoundScheduledCalibrationConfig:
        raise TypeError('scheduled qualification requires its exact current bound calibration context')
    validate_calibration_sources(config.commitment, calibration, sources=config.sources)
    authority, criterion = context.scientific_adjudication_context, config.commitment.response_selection.calibration_criterion
    if (authority is None or authority.evidence_world_kind is not WorldKind.NUMERICAL_SIMULATOR
            or authority.outcome_access is not OutcomeAccess.EVALUATION_REVEALED or authority.visibility_ceiling is not VisibilityCeiling.OUTCOME_VISIBLE
            or authority.independent_unit_id != criterion.independent_unit_id or authority.plumbing_only or authority.fixture_scope_id is not None
            or authority.information_cutoffs != tuple(ObjectIdentity.from_record(c.cutoff_id, c) for c in cutoffs(config.commitment, sources=config.sources))
            or calibration.calibration_id != config.calibration_id or calibration.qualification_criterion != criterion.identity
            or calibration.model != config.commitment.forecast_design.model or calibration.criterion != config.commitment.forecast_design.criterion
            or calibration.reservation != identity(config.commitment.reservation)
            or tuple(c.root_id for c in calibration.cases) != config.commitment.selected_root_ids):
        raise ValueError('scheduled calibration qualification lacks exact genuine issue/reveal/context/original bank')
    supported = (len(calibration.group_ids) >= criterion.minimum_group_count
        and set(criterion.required_family_ids) <= set(calibration.family_ids)
        and Decimal(sum(v is None for _, v, _ in calibration.scores))/len(calibration.group_ids) <= criterion.maximum_nonfinite_group_fraction)
    if type(config.record) is not ScheduledCalibrationConfig:
        from .compact_records import ScheduledCompactCalibrationConfig
        if type(config.record) is not ScheduledCompactCalibrationConfig:
            raise ValueError('scheduled qualification has no code-owned exact compact assessment view')
        assessments = config.full_assessments
        sources = config.sources
        if tuple(a.source for a in assessments) != tuple(identity(s) for s in sources):
            raise ValueError('compact qualification omits complete independently assessed full histories')
        supported = supported and all(a.numerical_pass for a in assessments)
    reasons = ('scheduled-complete-original-calibration-bank-qualified',) if supported else ('scheduled-calibration-frozen-construction-conditions-not-supported',)
    return ScientificAdjudicationRecord('adjudication.'+context.run_id+'.'+context.task_id, context.run_id, context.task_id,
        authority.execution_plan, context.input_materialization_ids, tuple(sorted(p.logical_artifact_id for p in context.output_ports)),
        context.dependency_receipt_ids, authority.evidence_world_id, authority.evidence_world_kind, authority.relation,
        authority.independent_unit_id, authority.information_cutoffs, authority.visibility_ceiling, authority.outcome_access,
        AdjudicationEvaluability.EVALUABLE, ScientificStatus.SUPPORTED if supported else ScientificStatus.NOT_SUPPORTED,
        AdmissionStatus.ADMITTED if supported else AdmissionStatus.EMPTY, reasons)




def _calibration_declaration(role, inputs, out, stage):
    from .operation_bindings import BUDGET
    from .qualification import scientific_root_validator
    output = 'adjudication' if role == 'calibration-qualify' else 'product'
    return RecursiveOperationDeclaration(
        capability_key=NAMESPACE + "." + role,
        capability_version="1.0.0",
        implementation_id=NAMESPACE + '.original-whole-group-' + role + '.v1',
        kind=CapabilityKind.TRANSFORM if role == 'calibrate' else CapabilityKind.EVALUATOR,
        config_record_type=ScheduledCalibrationConfig,
        stage=stage,
        input_ports=tuple((RecursivePortContract(n, t.SCHEMA, 'application/json', None, minimum_count=1, maximum_count=None if n in ('forecasts', 'scores') else 1) for n, t in inputs)),
        outputs=(OutputTemplate(output, out.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'),),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_SEALED_OUTCOMES, *((CapabilityPermission.REVEAL_OUTCOMES,) if role == "calibration-qualify" else ())))),
        evidence_ceiling=EvidenceCeiling.RESPONSE,
        outcome_access=access(role),
        visibility_ceiling=visibility(role),
        resources=BUDGET,
        conformance_check_ids=tuple(sorted(('all-original-calibration-cases-and-receipts', 'nonuse-infinite-whole-group-max15', 'separate-genuine-calibration-qualification'))),
        runner_factory=lambda: ScheduledCalibrator(role),
        record_codecs={**{ScheduledCalibration.SCHEMA: ScheduledCalibration, ScientificAdjudicationRecord.SCHEMA: ScientificAdjudicationRecord}, **{kind.SCHEMA: kind for _, kind in inputs}},
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=lambda c: (c.commitment.object_fingerprint,), scientific_unit_ids=units, scientific_root_validator=scientific_root_validator, adjudication_output_id=output if role == 'calibration-qualify' else None),
        execution_properties=RecursiveExecutionProperties(barrier=BarrierKind.REVEAL if role == 'calibration-qualify' else BarrierKind.NONE),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,),
    )


def calibration_declarations():
    return tuple(_calibration_declaration(*phase) for phase in CALIBRATION_PHASES)
