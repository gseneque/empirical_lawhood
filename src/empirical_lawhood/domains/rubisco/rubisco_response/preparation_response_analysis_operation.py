# SPDX-License-Identifier: MPL-2.0
"""Ordinary non-native task for retained six-question assessment and full actions."""

from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.storage.captured_gzip_codec import CAPTURED_GZIP_CODEC
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.execution.plans import OutputTemplate, ScientificStage
from empirical_lawhood.execution.recursive_compiler import RecursivePortContract
from empirical_lawhood.execution.recursive_handoff import RecursiveImplementationBinding
from empirical_lawhood.execution.recursive_provider import RecursiveOperationDeclaration, RecursiveScientificHooks, RecursiveStorageCodec
from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.raw_coupled_return import RAW_SCHEMA
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_read import ActivePreparationPrefixReadout
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_analysis import ACTION_MAGIC, ACTION_SCHEMA, PreparationResponseAnalysis, action_bytes, assess_analysis, binary_operands, read_action_bytes
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_assessment_records import PreparationResponseAssessment, EnvironmentalPreparationResponseAssessment
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import is_environmental
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_operation import CENTER_CODEC
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_read import PreparationResponsePointReadout
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_selection import CENTER_SCHEMA, MAX_CENTER_BYTES

CAPABILITY = 'rubisco-response.assess-preparation-response'
ENVIRONMENT_CAPABILITY = 'rubisco-response.assess-preparation-environment'
UNIT = 'unit.one-matched-preparation-response-investigation'
MAX_CONFIG = 64 * 2**20
BUDGET = ResourceBudget(1, 2 * 2**30, 0, 600, 256 * 2**20, 1024 * 2**20)


def validate_action_stream(source, request, *, size):
    from empirical_lawhood.storage.artifact_stream_primitives import ArtifactIdentityConflict
    if (request.payload_schema != ACTION_SCHEMA or request.profile is not ArtifactProfile.RAW_SOURCE_BYTES
            or request.media_type != 'application/octet-stream' or request.semantic_validation is not None
            or not len(ACTION_MAGIC) <= size <= BUDGET.output_bytes or (size - len(ACTION_MAGIC)) % 8):
        raise ArtifactIdentityConflict('response analysis changes its complete binary64 action transport')


# Original native gzip bytes use the shared uninterpreted-source custody
# contract. The consumer uses exact authenticated array shapes and sizes;
# registering it globally would also cap unrelated complete native archives.
ACTION_CODEC = RecursiveStorageCodec('rubisco.preparation-response-actions.f64', ACTION_SCHEMA, '1.0.0',
    ArtifactProfile.RAW_SOURCE_BYTES, 'application/octet-stream', '.bin', validate_action_stream, BUDGET.output_bytes)


@dataclass(frozen=True, slots=True)
class PreparationResponseAnalysisConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/preparation-response-analysis-config'
    ENVIRONMENTAL: ClassVar[bool] = False
    config_id: str
    analysis: PreparationResponseAnalysis
    implementation: RecursiveImplementationBinding

    def __post_init__(self):
        validate_stable_id(self.config_id)
        exact(self.analysis, PreparationResponseAnalysis)
        if is_environmental(self.analysis.design) != self.ENVIRONMENTAL:
            raise ValueError('response analysis config changes its declared experiment variant')
        exact(self.implementation, RecursiveImplementationBinding)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.config_id, self)

    @property
    def assessor_source(self):
        return ObjectIdentity.from_record('source.preparation-response-assessor.' + self.implementation.code_sources_sha256,
            self.implementation)



@dataclass(frozen=True, slots=True)
class EnvironmentalPreparationResponseAnalysisConfig(PreparationResponseAnalysisConfig):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/preparation-environment-analysis-config'
    ENVIRONMENTAL: ClassVar[bool] = True


def config_types():
    return (PreparationResponseAnalysisConfig, EnvironmentalPreparationResponseAnalysisConfig)


def config_type(design):
    return EnvironmentalPreparationResponseAnalysisConfig if is_environmental(design) else PreparationResponseAnalysisConfig


def capability_for(config):
    if type(config) not in config_types():
        raise TypeError('response analysis requires an exact selected config revision')
    return ENVIRONMENT_CAPABILITY if config.ENVIRONMENTAL else CAPABILITY


def assessment_type(config):
    capability_for(config)
    return EnvironmentalPreparationResponseAssessment if config.ENVIRONMENTAL else PreparationResponseAssessment


def input_selections(config):
    rows = []
    for record in (*config.analysis.prefixes, *config.analysis.readouts):
        _, product = config.analysis.product(record)
        kind = 'prefix' if type(record) is ActivePreparationPrefixReadout else 'point-readout'
        name = kind + '.' + record.fingerprint()
        rows.append((name, product.record, 'application/json', product.artifact.size_bytes, product.artifact.artifact_id, record))
    for name, pin, media, size in binary_operands(config.analysis):
        rows.append((name, pin, media, size, pin.object_id, None))
    return tuple(sorted(rows, key=lambda row: row[0]))


def external_id(config, name):
    return 'external.response-analysis.' + name


class PreparationResponseAnalysisRunner:
    def __init__(self, *, environmental=False):
        self.environmental = environmental
        self.manifest = operation_declaration(environmental=environmental).manifest()

    def execute(self, context):
        try:
            capability = ENVIRONMENT_CAPABILITY if self.environmental else CAPABILITY
            kind = EnvironmentalPreparationResponseAnalysisConfig if self.environmental else PreparationResponseAnalysisConfig
            if (context.task_id != capability or context.resource_budget != BUDGET
                    or context.permissions != self.manifest.permissions
                    or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE):
                raise ValueError('response assessor changes its bounded non-native task')
            config_port, = [p for p in context.input_ports if p.payload_schema == kind.SCHEMA]
            config = decode_canonical_bytes(config_port.read(MAX_CONFIG), kind, maximum_bytes=MAX_CONFIG)
            if ((config.config_id, config.fingerprint(), config_port.artifact_id) !=
                    (context.config.config_id, context.config.content_sha256, context.config.artifact_id)):
                raise ValueError('response assessor substitutes its frozen configuration')
            selected = input_selections(config)
            by_artifact = {row[4]: row for row in selected}
            if len(by_artifact) != len(selected) or len(context.input_ports) != len(selected) + 1:
                raise ValueError('response assessor changes the exact complete original input census')
            binary, seen = {}, set()
            for port in context.input_ports:
                if (port.kind is not WorkerInputKind.EXTERNAL or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                        or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
                    raise ValueError('response assessor changes original input exposure or custody')
                if port is config_port:
                    continue
                row = by_artifact.get(port.artifact_id)
                if row is None or port.artifact_id in seen:
                    raise ValueError('response assessor duplicates or substitutes an original operand')
                name, pin, media, size, _, record = row
                if (port.payload_schema, port.media_type, port.size_bytes) != (pin.object_schema, media, size):
                    raise ValueError('response assessor changes original operand schema, media or complete size')
                raw = port.read(size + 1)
                if len(raw) != size or sha256(raw).hexdigest() != pin.object_fingerprint:
                    raise ValueError('response assessor changes original complete operand bytes')
                if record is None:
                    binary[name] = raw
                elif raw != record.canonical_bytes():
                    raise ValueError('response assessor substitutes its original contribution record')
                seen.add(port.artifact_id)
            assessment, arrays = assess_analysis(config.analysis, binary, assessor_source=config.assessor_source,
                assessment_id=capability + '.assessment.' + config.analysis.fingerprint())
            raw_actions = action_bytes(arrays)
            read_action_bytes(assessment, raw_actions)
            outputs = {capability + '.assessment': (assessment_type(config).SCHEMA, assessment.canonical_bytes()),
                capability + '.actions': (ACTION_SCHEMA, raw_actions)}
            if (len(context.output_ports) != 2 or {p.output_id for p in context.output_ports} != set(outputs)
                    or any(p.payload_schema != outputs[p.output_id][0] for p in context.output_ports)):
                raise ValueError('response assessor changes its complete scientific output census')
            return RunnerResult(tuple(TaskOutputPayload(p.output_id, outputs[p.output_id][1]) for p in context.output_ports),
                (ReceiptCheck('six-questions-original-raw-operands-zero-native-calls', True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_declaration(*, environmental=False):
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_analysis_translation import validate_root
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_analysis_inquiry import inquiry_hooks
    capability = ENVIRONMENT_CAPABILITY if environmental else CAPABILITY
    kind = EnvironmentalPreparationResponseAnalysisConfig if environmental else PreparationResponseAnalysisConfig
    assessment_kind = EnvironmentalPreparationResponseAssessment if environmental else PreparationResponseAssessment
    return RecursiveOperationDeclaration(capability_key=capability, capability_version='1.0.0',
        implementation_id=('original-six-question-environment-assessment-v1' if environmental
            else 'original-six-question-response-assessment-v1'), kind=CapabilityKind.FALSIFIER,
        config_record_type=kind, stage=ScientificStage.FALSIFY,
        input_ports=(RecursivePortContract('center', CENTER_SCHEMA, 'application/octet-stream', MAX_CENTER_BYTES, 0, 4),
            RecursivePortContract('native-array', RAW_SCHEMA, 'application/gzip', None, 0, 56),
            RecursivePortContract('point-readout', PreparationResponsePointReadout.SCHEMA, 'application/json', MAX_CONFIG, 0, 28),
            RecursivePortContract('prefix', ActivePreparationPrefixReadout.SCHEMA, 'application/json', MAX_CONFIG, 2, 2)),
        outputs=(OutputTemplate('actions', ACTION_SCHEMA, ArtifactProfile.RAW_SOURCE_BYTES, 'application/octet-stream', '.bin'),
            OutputTemplate('assessment', assessment_kind.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json')),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
            CapabilityPermission.READ_DEVELOPMENT))), evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
        resources=BUDGET, conformance_check_ids=('complete-original-native-operands', 'complete-paired-and-missing-denominators',
            'frozen-prediction-before-reveal', 'six-question-scientific-decisions', 'zero-new-native-effects'),
        runner_factory=(lambda: PreparationResponseAnalysisRunner(environmental=True)) if environmental else PreparationResponseAnalysisRunner,
        record_codecs={record.SCHEMA: record for record in (kind, PreparationResponseAnalysis,
            assessment_kind, PreparationResponsePointReadout, ActivePreparationPrefixReadout)},
        storage_codecs=tuple(sorted((CENTER_CODEC, ACTION_CODEC, CAPTURED_GZIP_CODEC), key=lambda c: c.codec_id)),
        scientific_hooks=RecursiveScientificHooks(scientific_root_validator=validate_root,
            scientific_operand_sha256s=lambda c: tuple(sorted({c.analysis.fingerprint(),
                *(row[1].object_fingerprint for row in input_selections(c))})),
            scientific_unit_ids=lambda c: (UNIT,), native_effect_slot_ids=lambda c: ()),
        inquiry_hooks=inquiry_hooks())
