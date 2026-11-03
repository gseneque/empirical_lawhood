# SPDX-License-Identifier: MPL-2.0
"""Cold declarations for E1 on the existing prospective runtime contracts.

Registration alone creates no source qualification or authority. The caller
must provide a genuine StudyDraft, ordinary source qualifications and issue,
execution and separate reveal authority through the existing platform.
"""

from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS

from dataclasses import dataclass, replace
from decimal import Decimal
from hashlib import sha256
import resource
import time
from typing import ClassVar

from empirical_lawhood.adapters.composition.discovery import bundle
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import MatrixParameterScalarDefinition
from empirical_lawhood.adapters.methods.matrix_parameter_history.operation_bindings import _retained_values
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterNativeHistory, coordinate_identity
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.status import AdmissionStatus, OperationalStatus, ScientificStatus
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.study_authoring import StudyDraft
from empirical_lawhood.runtime.adjudication import AdjudicationEvaluability, ScientificAdjudicationRecord
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import ParentPreparedTaskRunner, RunnerResult, TaskContext, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.input_access import validated_scientific_input_edges
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract
from empirical_lawhood.runtime.extension_bundles import ExtensionContributionKind
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkOutput, NativeSubworkRoster, NativeSubworkState, invoke_native_subwork
from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import (
    RecursivePortContract, RegisteredPublicationRequirement,
)
from empirical_lawhood.runtime.recursive_provider import (RecursiveExecutionProperties,
    RecursiveInquiryHooks, RecursiveOperationDeclaration, RecursiveScientificHooks)

from . import science
from .commitment import COMMIT_KEY, E1Commitment, E1CommitmentConfig, E1Committer, require_publication_copy
from .records import (
    E1FactorAssessment, E1FactorProduct, E1HistoryAllocation, E1HistorySource,
    E1NativeHistory, E1NumericalAssessment, E1PopulationResult, E1ScientificSelection, identity,
)

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT

NAMESPACE = 'matrix-factor-confirmation'
KEY = NAMESPACE+'.adjudicate'
BUDGET = ResourceBudget(1, None, 0, None, None, None)
PHASES = (
    ('history', (('allocation', E1HistoryAllocation), ('commitment', E1Commitment), ('coordinate', MatrixParameterCoordinate),
        ('provenance', NumericalProducingProvenance), ('selection', E1ScientificSelection),
        ('source', E1HistorySource), ('streams', MatrixHistorySeed)), E1NativeHistory, ScientificStage.ACQUIRE),
    ('numerical', (('history', E1NativeHistory), ('history-arrays', None), ('source', E1HistorySource)),
        E1NumericalAssessment, ScientificStage.FALSIFY),
    ('measure', (('history', E1NativeHistory), ('history-arrays', None), ('numerical', E1NumericalAssessment),
        ('scalar-definition', MatrixParameterScalarDefinition), ('source', E1HistorySource)), E1FactorProduct, ScientificStage.TRANSFORM),
    ('check', (('history', E1NativeHistory), ('history-arrays', None), ('measure', E1FactorProduct),
        ('measure-arrays', None), ('numerical', E1NumericalAssessment), ('scalar-definition', MatrixParameterScalarDefinition), ('source', E1HistorySource)),
        E1FactorAssessment, ScientificStage.FALSIFY),
)


@dataclass(frozen=True, slots=True)
class E1OperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/operation-config'
    config_id: str
    operation: str
    source: E1HistorySource

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if (type(self.source) is not E1HistorySource or self.operation not in {p[0] for p in PHASES}
                or self.config_id != 'config.'+NAMESPACE+'.'+self.source.root_id+'.'+self.operation):
            raise ValueError('E1 configuration cannot accept exposed source or change exact operation')


@dataclass(frozen=True, slots=True)
class E1AdjudicationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/adjudication-config'
    config_id: str
    sources: tuple[E1HistorySource, ...]

    def __post_init__(self):
        if (self.config_id != 'config.'+KEY or not self.sources or any(type(s) is not E1HistorySource for s in self.sources)
                or tuple(s.root_id for s in self.sources) != tuple(r.root.root_id for r in self.sources[0].allocation.roots)
                or any(s.reservation != self.sources[0].reservation or s.specification != self.sources[0].specification for s in self.sources)):
            raise ValueError('E1 adjudication omits or substitutes exact whole-root protected sources')


def source_operands(source):
    return tuple(sorted((identity(source), identity(source.reservation), identity(source.allocation),
        identity(source.specification), identity(source.specification.selection), identity(source.rule),
        identity(source.criterion), identity(source.numerical_design), identity(source.specification.selection.factor_numerical_design),
        coordinate_identity(source.coordinate), source.provenance.identity), key=lambda x: x.object_id))


def cutoffs(config):
    sources = config.sources if type(config) is E1AdjudicationConfig else (config.source,)
    return tuple(sorted((InformationCutoff('cutoff.'+s.root_id, s.root.root.clock_id, CausalPhase.PRE_ACTION,
        s.rule.primary_dt*s.rule.risk_start_tick) for s in sources), key=lambda c: c.cutoff_id))


def _root(config, context):
    configs = tuple(i.record for i in context.config_inputs)
    adjudicators = tuple(c for c in configs if type(c) is E1AdjudicationConfig)
    commitments = tuple(c for c in configs if type(c) is E1CommitmentConfig)
    phases = tuple(c for c in configs if type(c) is E1OperationConfig)
    if len(adjudicators) != 1 or len(commitments) != 1 or len(phases)+2 != len(configs):
        raise ValueError('E1 scientific route requires its complete four-phase population and genuine reveal evaluator')
    selected = adjudicators[0]
    if commitments[0].sources != selected.sources:
        raise ValueError('E1 commitment changes the complete current source population')
    roots = tuple(s.root_id for s in selected.sources)
    if (len(phases) != 4*len(roots) or {c.source.root_id for c in phases} != set(roots)
            or any({c.operation for c in phases if c.source.root_id == root} != {p[0] for p in PHASES} for root in roots)
            or any(c.source not in selected.sources for c in phases)):
        raise ValueError('E1 route thins or changes actual native/numerical/factor/independent phases')
    source, root = selected.sources[0], context.root
    criterion = source.criterion
    groups = tuple(sorted({s.root.root.independent_group_id for s in selected.sources}))
    if (type(root) is not StudyDraft or root.system is None or root.experiment is None
            or root.unresolved_decisions or root.system.system_id != criterion.system_id
            or root.system.world.world_id != criterion.world_id or root.system.world.kind is not WorldKind.NUMERICAL_SIMULATOR
            or root.evaluation_unit_ids != groups or root.experiment.independent_unit_id != criterion.independent_unit_id
            or identity_relation(root.experiment.relation) != criterion.relation
            or root.experiment.information_cutoffs != cutoffs(selected)
            or not {operand for s in selected.sources for operand in source_operands(s)}
               <= {i.object_identity for i in root.design_inputs}):
        raise ValueError('E1 requires genuine prospective system/relation/source/qualification design and complete causal units')
    return selected, groups


def identity_relation(relation):
    return ObjectIdentity.from_record(relation.relation_id, relation)


def scientific_root_validator(config, context):
    selected, groups = _root(config, context)
    if type(config) is E1CommitmentConfig:
        if (config.sources != selected.sources or context.node_id != COMMIT_KEY or context.stage is not ScientificStage.FREEZE
                or context.outcome_access is not OutcomeAccess.OUTCOME_BLIND
                or context.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
                or context.unit_ids != groups or context.selected_unit_ids != groups or context.complete_unit_census):
            raise ValueError('E1 commitment changes exact protected freeze/source/unit scope')
        expected = {'allocation', 'selection'} | {'source.'+s.root_id for s in selected.sources}
    elif type(config) is E1AdjudicationConfig:
        if (config != selected or context.node_id != KEY or context.stage is not ScientificStage.REVEAL
                or context.outcome_access is not OutcomeAccess.EVALUATOR_REVEAL
                or context.visibility_ceiling is not VisibilityCeiling.OUTCOME_VISIBLE
                or context.unit_ids != groups or context.selected_unit_ids != groups or context.complete_unit_census):
            raise ValueError('E1 evaluator changes genuine separate reveal or independent-root scope')
        expected = {'measure.'+s.root_id for s in selected.sources} | {'check.'+s.root_id for s in selected.sources}
    else:
        if config.operation == 'history':
            from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_ou_domain import validate_parameter_ou_domain
            validate_parameter_ou_domain(config.source.coordinate)
        phase = next(p for p in PHASES if p[0] == config.operation)
        if (context.node_id != NAMESPACE+'.'+config.source.root_id+'.'+config.operation
                or context.stage is not phase[3] or context.unit_ids != (config.source.root.root.independent_group_id,)
                or context.selected_unit_ids != groups or context.complete_unit_census != (config.operation == 'history')
                or context.outcome_access is not OutcomeAccess.EVALUATION_SEALED
                or context.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE):
            raise ValueError('E1 phase changes prospective native/stage/unit/sealed scope')
        expected = {n for n, _ in phase[1] if n != 'streams'}
        if config.operation == 'history':
            expected |= {'streams.'+s.purpose for s in config.source.root.streams}
    incoming = tuple(l for l in context.links if l.consumer_node_id == context.node_id)
    if len(incoming) != len(expected) or {l.consumer_input_id for l in incoming} != expected:
        raise ValueError('E1 operation omits its complete scientific operand census')
    for link in incoming:
        name = link.consumer_input_id
        if name in {'allocation', 'coordinate', 'provenance', 'selection', 'source', 'scalar-definition'} or name.startswith(('streams.', 'source.')):
            if link.external_input_id is None or link.producer_node_id is not None or link.scientific_role != 'SOURCE':
                raise ValueError('E1 source is not a qualified explicit ordinary prospective operand')
        else:
            if name == 'commitment':
                if (link.producer_node_id != COMMIT_KEY or link.producer_output_id != 'product'
                        or link.external_input_id is not None or link.scientific_role != 'SOURCE'):
                    raise ValueError('E1 native history lacks its actual pure prior commitment dependency')
                continue
            if type(config) is E1AdjudicationConfig:
                owner, root = name.split('.', 1)
                output = 'product'
            else:
                owner, root = name.removesuffix('-arrays'), config.source.root_id
                output = 'arrays' if name.endswith('-arrays') else 'product'
            if (link.producer_node_id != NAMESPACE+'.'+root+'.'+owner or link.producer_output_id != output
                    or link.external_input_id is not None or link.scientific_role != ('HISTORY' if owner == 'history' else 'OUTCOME')):
                raise ValueError('E1 causal input substitutes actual native history or independent check dependency')


def operation_declarations():
    """Single owner for the six existing E1 capability contracts."""
    from .commitment import authenticate_prior_publications

    codecs = {t.SCHEMA: t for t in (E1Commitment, E1NativeHistory, E1NumericalAssessment,
        E1FactorProduct, E1FactorAssessment, E1PopulationResult, ScientificAdjudicationRecord)}
    base_permissions = (CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                        CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS)
    inquiry = RecursiveInquiryHooks(inquiry_record_identity=identity)
    values = []
    for role, inputs, output, stage in PHASES:
        values.append(RecursiveOperationDeclaration(
            capability_key=NAMESPACE+'.'+role, capability_version='1.0.0',
            implementation_id=NAMESPACE+'.full-paired-history-'+role+'.v1',
            kind=CapabilityKind.SIMULATOR if role == 'history' else
                CapabilityKind.TRANSFORM if role == 'measure' else CapabilityKind.FALSIFIER,
            config_record_type=E1OperationConfig, stage=stage,
            input_ports=tuple(RecursivePortContract(n, t.SCHEMA if t else MATRIX_ARRAY_SCHEMA,
                'application/json' if t else 'application/x-npz', None if t else MAXIMUM_MATRIX_ARRAY_BYTES,
                minimum_count=4 if n == 'streams' else 1, maximum_count=None if n == 'streams' else 1)
                for n, t in inputs),
            outputs=tuple(sorted((OutputTemplate('product', output.SCHEMA, ArtifactProfile.CANONICAL_JSON,
                'application/json', '.json'), *((OutputTemplate('arrays', MATRIX_ARRAY_SCHEMA,
                ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz', '.npz'),)
                if role in ('history', 'measure') else ())), key=lambda x: x.output_id)),
            permissions=tuple(sorted((*base_permissions, CapabilityPermission.READ_SEALED_OUTCOMES))),
            evidence_ceiling=EvidenceCeiling.RESPONSE, outcome_access=OutcomeAccess.EVALUATION_SEALED,
            visibility_ceiling=VisibilityCeiling.PROSPECTIVE, resources=BUDGET,
            conformance_check_ids=('complete-four-family-clock-census', 'independent-full-numerical-witness',
                                   'prospective-issued-context-required'),
            runner_factory=lambda role=role: native_runner() if role == 'history' else E1Runner(role),
            record_codecs=codecs, inquiry_hooks=inquiry,
            scientific_hooks=RecursiveScientificHooks(
                scientific_operand_sha256s=lambda c: tuple(sorted(o.object_fingerprint for o in source_operands(c.source))),
                scientific_unit_ids=lambda c: (c.source.root.root.independent_group_id,),
                native_effect_slot_ids=(lambda c: ('paired-history.'+c.source.root_id,)) if role == 'history' else None,
                scientific_root_validator=scientific_root_validator),
            execution_properties=RecursiveExecutionProperties(native_effect=role == 'history',
                complete_unit_census=role == 'history',
                native_work_preparer=prepare_native_work if role == 'history' else None),
            provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,), storage_codecs=MATRIX_STORAGE_CODECS,
            input_record_types=tuple(sorted({t for _, t in inputs if t is not None},
                                             key=lambda t: (t.SCHEMA, t.VERSION)))))
    common_hooks = dict(
        scientific_operand_sha256s=lambda c: tuple(sorted({o.object_fingerprint for s in c.sources for o in source_operands(s)})),
        scientific_unit_ids=lambda c: tuple(sorted({s.root.root.independent_group_id for s in c.sources})),
        scientific_root_validator=scientific_root_validator)
    values.append(RecursiveOperationDeclaration(
        capability_key=KEY, capability_version='1.0.0',
        implementation_id=NAMESPACE+'.frozen-full-family-recurrence-survival.v1', kind=CapabilityKind.EVALUATOR,
        config_record_type=E1AdjudicationConfig, stage=ScientificStage.REVEAL,
        input_ports=(RecursivePortContract('check', E1FactorAssessment.SCHEMA, 'application/json', None,
            minimum_count=1, maximum_count=None), RecursivePortContract('measure', E1FactorProduct.SCHEMA,
            'application/json', None, minimum_count=1, maximum_count=None)),
        outputs=(OutputTemplate('adjudication', ScientificAdjudicationRecord.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'),
            OutputTemplate('product', E1PopulationResult.SCHEMA, ArtifactProfile.CANONICAL_JSON,
                           'application/json', '.json')),
        permissions=tuple(sorted((*base_permissions, CapabilityPermission.READ_SEALED_OUTCOMES,
                                  CapabilityPermission.REVEAL_OUTCOMES))),
        evidence_ceiling=EvidenceCeiling.RESPONSE, outcome_access=OutcomeAccess.EVALUATOR_REVEAL,
        visibility_ceiling=VisibilityCeiling.OUTCOME_VISIBLE, resources=BUDGET,
        conformance_check_ids=('complete-risk-censoring-denominators', 'explicit-frozen-estimand-endpoints',
                               'issued-separate-reveal-required'),
        runner_factory=E1Adjudicator, record_codecs=codecs, inquiry_hooks=inquiry,
        scientific_hooks=RecursiveScientificHooks(adjudication_output_id='adjudication', **common_hooks),
        execution_properties=RecursiveExecutionProperties(barrier=BarrierKind.REVEAL),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,), storage_codecs=MATRIX_STORAGE_CODECS,
        input_record_types=tuple(sorted((E1FactorAssessment, E1FactorProduct), key=lambda t: (t.SCHEMA, t.VERSION)))))
    values.append(RecursiveOperationDeclaration(
        capability_key=COMMIT_KEY, capability_version='1.0.0',
        implementation_id=NAMESPACE+'.prior-protected-source-commitment.v1', kind=CapabilityKind.TRANSFORM,
        config_record_type=E1CommitmentConfig, stage=ScientificStage.FREEZE,
        input_ports=(RecursivePortContract('allocation', E1HistoryAllocation.SCHEMA, 'application/json', None),
            RecursivePortContract('selection', E1ScientificSelection.SCHEMA, 'application/json', None),
            RecursivePortContract('source', E1HistorySource.SCHEMA, 'application/json', None,
                                  minimum_count=1, maximum_count=None)),
        outputs=(OutputTemplate('product', E1Commitment.SCHEMA, ArtifactProfile.CANONICAL_JSON,
                                'application/json', '.json'),),
        permissions=tuple(sorted((*base_permissions, CapabilityPermission.READ_FROZEN_MODELS))),
        evidence_ceiling=EvidenceCeiling.RESPONSE, outcome_access=OutcomeAccess.OUTCOME_BLIND,
        visibility_ceiling=VisibilityCeiling.PROSPECTIVE, resources=BUDGET,
        conformance_check_ids=('complete-protected-source-census', 'prior-publication-identity-joins',
                               'pure-pre-native-freeze'),
        runner_factory=lambda: E1Committer(operation_manifests()[-1], BUDGET), record_codecs=codecs,
        inquiry_hooks=inquiry, scientific_hooks=RecursiveScientificHooks(**common_hooks),
        execution_properties=RecursiveExecutionProperties(barrier=BarrierKind.FREEZE),
        publication_requirements=(RegisteredPublicationRequirement(
            NAMESPACE+'.prior-publications.v1', authenticate_prior_publications),),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,), storage_codecs=MATRIX_STORAGE_CODECS,
        input_record_types=tuple(sorted((E1HistoryAllocation, E1HistorySource, E1ScientificSelection),
                                       key=lambda t: (t.SCHEMA, t.VERSION)))))
    return tuple(values)


def operation_manifests():
    """Historical public facade; exact canonical manifests come from declarations."""
    return tuple(declaration.manifest() for declaration in operation_declarations())


def operation_registrations():
    return tuple(declaration.registration() for declaration in operation_declarations())


def _worker(context, config, role, manifest_value):
    if (type(context) is not TaskContext or context.task_id != (KEY if role == 'adjudicate' else NAMESPACE+'.'+config.source.root_id+'.'+role)
            or context.config.config_id != config.config_id or context.config.config_schema != config.SCHEMA
            or context.config.content_sha256 != config.fingerprint() or context.permissions != manifest_value.permissions
            or not BUDGET.contains(context.resource_budget) or context.outcome_access is not
                (OutcomeAccess.EVALUATOR_REVEAL if role == 'adjudicate' else OutcomeAccess.EVALUATION_SEALED)
            or any(p.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE for p in context.input_ports
                if role != 'adjudicate' or p.artifact_id != context.config.artifact_id)):
        raise ValueError('E1 worker lacks exact protected runtime configuration, inputs, permissions or access')


def _dependency(context, port, source, role):
    receipts = tuple(r for r in context.dependency_receipts if port.materialization_id in r.output_materialization_ids)
    if (port.kind is not WorkerInputKind.DEPENDENCY or port.outcome_access is not OutcomeAccess.EVALUATION_SEALED
            or len(receipts) != 1 or receipts[0].task_id != NAMESPACE+'.'+source.root_id+'.'+role):
        raise ValueError('E1 consumer loses exact protected producer receipt lineage')


def _decode(context, role):
    if (type(context) is not TaskContext or context.outcome_access is not OutcomeAccess.EVALUATION_SEALED
            or any(p.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE for p in context.input_ports)):
        raise ValueError('E1 source access requires genuine protected runtime context before reading operands')
    phase = next(p for p in PHASES if p[0] == role)
    declaration = next(value for value in operation_declarations() if value.capability_key == NAMESPACE+'.'+role)
    manifest = declaration.manifest()
    configuration_ports = tuple(port for port in context.input_ports
        if port.artifact_id == context.config.artifact_id)
    if (len(configuration_ports) != 1
            or configuration_ports[0].payload_schema != E1OperationConfig.SCHEMA
            or (configuration_ports[0].outcome_access, configuration_ports[0].visibility_ceiling) != (
                declaration.outcome_access, declaration.visibility_ceiling)):
        raise ValueError('E1 worker changes its exact declared compiler configuration custody')
    config_port, = configuration_ports
    validated_scientific_input_edges(context, config_port=config_port)
    types = {E1OperationConfig.SCHEMA: E1OperationConfig, **{t.SCHEMA: t for _, t in phase[1] if t and t is not MatrixHistorySeed}}
    records, ports, streams = {}, {}, []
    for port in context.input_ports:
        if port.payload_schema in types and port.payload_schema not in records:
            records[port.payload_schema] = decode_canonical_bytes(port.read(), types[port.payload_schema], maximum_bytes=None)
            ports[port.payload_schema] = port
        elif port.payload_schema == MatrixHistorySeed.SCHEMA and role == 'history':
            streams.append(decode_canonical_bytes(port.read(), MatrixHistorySeed, maximum_bytes=None))
        elif port.payload_schema == MATRIX_ARRAY_SCHEMA:
            if port.artifact_id in ports:
                raise ValueError('E1 worker duplicates raw arrays')
            ports[port.artifact_id] = port
        else:
            raise ValueError('E1 worker receives duplicate, exposed or undeclared records')
    if set(records) != set(types) or sum(p.payload_schema == MATRIX_ARRAY_SCHEMA for p in context.input_ports) != sum(t is None for _, t in phase[1]):
        raise ValueError('E1 worker omits complete typed/raw operands')
    config, source = records[E1OperationConfig.SCHEMA], records[E1HistorySource.SCHEMA]
    _worker(context, config, role, manifest)
    if (config.operation != role or source != config.source
            or ports[E1OperationConfig.SCHEMA] is not config_port
            or config_port.size_bytes != len(config.canonical_bytes())
            or ports[E1HistorySource.SCHEMA].outcome_access is not OutcomeAccess.OUTCOME_BLIND):
        raise ValueError('E1 worker changes current selected full-history source')
    if MatrixParameterScalarDefinition.SCHEMA in records:
        definition, port = records[MatrixParameterScalarDefinition.SCHEMA], ports[MatrixParameterScalarDefinition.SCHEMA]
        artifact = source.rule.scalar_closure.normalization_owner
        if (definition.fingerprint() != artifact.sha256 or len(definition.canonical_bytes()) != artifact.size_bytes
                or port.artifact_id != artifact.artifact_id or port.outcome_access is not OutcomeAccess.OUTCOME_BLIND):
            raise ValueError('E1 scalar comparison substitutes actual published original normalization definition')
    if role == 'history':
        commitment, port = records[E1Commitment.SCHEMA], ports[E1Commitment.SCHEMA]
        require_commitment_dependency(context, port, commitment, source)
        if (records[E1HistoryAllocation.SCHEMA] != source.allocation or records[E1ScientificSelection.SCHEMA] != source.specification.selection
                or records[MatrixParameterCoordinate.SCHEMA] != source.coordinate or records[NumericalProducingProvenance.SCHEMA] != source.provenance
                or tuple(sorted(streams, key=lambda s: s.purpose)) != source.root.streams):
            raise ValueError('E1 native worker changes exact source/coordinate/publication/stream operands')
        for schema, publication in ((E1HistoryAllocation.SCHEMA, source.reservation.publication),
                                     (E1ScientificSelection.SCHEMA, source.specification.publication)):
            port = ports[schema]
            require_publication_copy(records[schema], port, publication)
        if any(p.outcome_access is not OutcomeAccess.OUTCOME_BLIND
                for p in context.input_ports if p is not config_port):
            raise ValueError('E1 native worker refuses exposed or already accessed source operands')
    else:
        for owner, schema in (('history', E1NativeHistory.SCHEMA), ('numerical', E1NumericalAssessment.SCHEMA), ('measure', E1FactorProduct.SCHEMA)):
            if schema in records:
                _dependency(context, ports[schema], source, owner)
        for schema in (E1NativeHistory.SCHEMA, E1FactorProduct.SCHEMA):
            if schema in records:
                saved = records[schema].arrays.array_artifact
                port = ports.get(saved.artifact_id)
                if port is None or (port.payload_schema, port.media_type, port.size_bytes) != (saved.payload_schema, saved.media_type, saved.size_bytes):
                    raise ValueError('E1 raw input differs from exact receipted array artifact')
                _dependency(context, port, source, 'history' if schema == E1NativeHistory.SCHEMA else 'measure')
    return config, source, records, ports


def require_commitment_dependency(context, port, commitment, source):
    commitment.validate_source(source)
    receipts = tuple(r for r in context.dependency_receipts if port.materialization_id in r.output_materialization_ids)
    if (port.kind is not WorkerInputKind.DEPENDENCY or port.outcome_access is not OutcomeAccess.OUTCOME_BLIND
            or port.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE or len(receipts) != 1
            or receipts[0].task_id != COMMIT_KEY):
        raise ValueError('E1 native history lacks its original protected prior commitment receipt')


def _outputs(context, product, raw=None):
    ports = {p.output_id.rsplit('.', 1)[-1]: p for p in context.output_ports}
    if (set(ports) != ({'product'} if raw is None else {'product', 'arrays'})
            or ports['product'].payload_schema != product.SCHEMA or ports['product'].profile is not ArtifactProfile.CANONICAL_JSON):
        raise ValueError('E1 provider changes its complete output census')
    outputs = [TaskOutputPayload(ports['product'].output_id, product.canonical_bytes())]
    if raw is not None:
        if (ports['arrays'].profile is not ArtifactProfile.MATRIX_ARRAY_NPZ
                or ports['arrays'].logical_artifact_id != product.arrays.array_artifact.artifact_id
                or sha256(raw).hexdigest() != product.arrays.array_artifact.sha256):
            raise ValueError('E1 provider changes actual array publication')
        outputs.append(TaskOutputPayload(ports['arrays'].output_id, raw))
    return RunnerResult(tuple(sorted(outputs, key=lambda x: x.output_id)), (ReceiptCheck('e1-complete-protected-scientific-census', True, ()),))


class E1Runner:
    def __init__(self, role):
        self.role = role
        self.manifest = next(m for m in operation_manifests() if m.capability_key.endswith('.'+role))

    def execute(self, context):
        try:
            _, source, records, ports = _decode(context, self.role)
            if self.role == 'history':
                raise ValueError('E1 native history requires the genuine issued native-subwork port')
            history = records[E1NativeHistory.SCHEMA]
            native_raw = ports[history.arrays.array_artifact.artifact_id].read()
            arrays = science.consume_arrays(source, history.arrays, native_raw)
            if self.role == 'numerical':
                return _outputs(context, science.assess_history(source, history, arrays))
            numerical = records[E1NumericalAssessment.SCHEMA]
            if self.role == 'measure':
                output = next(p for p in context.output_ports if p.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
                raw, product = science.measure(source, history, numerical, arrays, artifact_id=output.logical_artifact_id)
                return _outputs(context, product, raw)
            product = records[E1FactorProduct.SCHEMA]
            diagnostics = ports[product.arrays.array_artifact.artifact_id].read()
            return _outputs(context, science.assess_factor(source, history, numerical, product, native_raw, diagnostics))
        finally:
            for port in context.input_ports:
                port.close()


def _initial_native_work(context, config, source, parent):
    """The unchanged E1 child and parent checks before preparation or entry."""
    from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork

    if (parent.run_id != context.run_id or parent.task_id != context.task_id or parent.attempt_id != context.attempt_id
            or parent.input_materialization_ids != context.input_materialization_ids
            or parent.implementation_commit != source.provenance.observed_git_head):
        raise ValueError('E1 native entry substitutes its genuine issued ordinary parent contact')
    definition = NativeSubworkDefinition('paired-history.'+source.root_id, 'matrix-e1.full-paired-history', parent,
        identity(config), tuple(sorted((identity(source), identity(source.allocation), coordinate_identity(source.coordinate), source.provenance.identity), key=lambda x: x.object_id)),
        source.provenance.code_sources_sha256, source.provenance.dependency_lock_sha256, context.input_materialization_ids,
        tuple(sorted((source.root.stream_identity(s) for s in source.root.streams), key=lambda x: x.object_id)),
        (NativeSubworkOutput('arrays', MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz'),))
    roster = NativeSubworkRoster('selected.native-subwork', parent, (definition.identity,))
    return PreparedNativeWork(parent, (source.root.root.independent_group_id,),
        ('paired-history.'+source.root_id,), (definition,), (roster,))


def prepare_native_work(*, runner, context, expected_parent):
    if type(runner) is not E1NativeRunner or runner.role != 'history':
        raise ValueError('E1 preparation requires its installed original protected history phase')
    config, source, _, _ = _decode(context, 'history')
    return _initial_native_work(context, config, source, expected_parent)


def _prepare_native_runner(context):
    """Select the unchanged history runner only after complete parent preparation."""
    runner = E1NativeRunner('history')
    prepared = context.prepared_invocation
    if (type(prepared) is not PreparedInvocationContract or not prepared.native_effect
            or prepared.manifest != runner.manifest):
        raise ValueError('E1 native parent preparation requires its complete actual native invocation')
    prepared.require_complete()
    prepared.validate_context(context)
    return runner


def native_runner():
    """Reuse ordinary parent staging before the strict history decoder runs."""
    runner = E1NativeRunner('history')
    return ParentPreparedTaskRunner(runner.manifest, _prepare_native_runner, native_effect=True)


class E1NativeRunner(E1Runner):
    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        try:
            config, source, _, _ = _decode(context, 'history')
            parent = native_subwork.parent_contact
            work = _initial_native_work(context, config, source, parent)
            definition, = work.definitions
            completed = native_subwork.recover(definition)
            if completed is not None:
                if (completed.state is not NativeSubworkState.COMPLETED or completed.completion is None
                        or completed.completion.operational_status is not OperationalStatus.SUCCEEDED or completed.receipt is None):
                    raise ValueError('E1 refuses uncertain or failed native replay')
                raw = b''.join(native_subwork.iter_completed_output(definition, 'arrays'))
                arrays = _retained_values(source, raw)
            else:
                if native_subwork.inspect(definition).state is not NativeSubworkState.NOT_ENTERED:
                    raise ValueError('E1 unreceipted or uncertain native contact cannot be repeated')
                from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_ou_domain import validate_parameter_ou_domain
                validate_parameter_ou_domain(source.coordinate)
                native_subwork.freeze_roster(work.rosters[0], definitions=work.definitions)
                entry = native_subwork.begin(definition)
                native_subwork.contact(entry)
                cpu, wall = time.process_time(), time.monotonic()
                try:
                    from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_source import acquire_parameter_history
                    # Count only the completed primary and fine BAOAB steps.
                    callback = None if progress is None else lambda primary, fine: progress.advance(Decimal(primary+fine))
                    arrays = invoke_native_subwork(native_subwork, entry,
                        acquire_parameter_history, source.coordinate, source.root.streams, progress=callback)
                except (ArithmeticError, MemoryError, ValueError):
                    native_subwork.complete(entry, operational_status=OperationalStatus.FAILED,
                        cost=InquiryCost(Decimal(str(time.process_time()-cpu)), Decimal(str(time.monotonic()-wall)), None),
                        cost_scope='E1 native complete paired history nested within ordinary task',
                        unknown_streams=definition.streams, reason_codes=('matrix-e1-native-failure',))
                    raise
                raw, _ = science.array_product(source, arrays, artifact_id='array.'+definition.subwork_id)
                native_subwork.publish_output(entry, 'arrays', (raw,), maximum_bytes=len(raw), maximum_chunk_bytes=len(raw),
                    expected_size_bytes=len(raw), expected_physical_sha256=sha256(raw).hexdigest())
                consumed = tuple(sorted((source.root.stream_identity(s) for s in source.root.streams
                    if s.purpose.startswith('preparation') or source.coordinate.autonomous_ticks), key=lambda x: x.object_id))
                completed = native_subwork.complete(entry, operational_status=OperationalStatus.SUCCEEDED,
                    cost=InquiryCost(Decimal(str(time.process_time()-cpu)), Decimal(str(time.monotonic()-wall)), Decimal(len(raw))),
                    cost_scope='E1 native complete paired history nested within ordinary task', consumed_streams=consumed,
                    unconsumed_streams=tuple(s for s in definition.streams if s not in consumed),
                    peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
            output = next(p for p in context.output_ports if p.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
            _, operand = science.array_product(source, arrays, artifact_id=output.logical_artifact_id, raw=raw)
            root = source.root.root
            product = E1NativeHistory('history.'+source.root_id, identity(source), coordinate_identity(source.coordinate),
                source.root_id, root.independent_group_id, root.clock_id, operand,
                MatrixParameterNativeHistory(definition, completed.completion, completed.receipt),
                source.coordinate.total_ticks, 2*source.coordinate.total_ticks)
            product.validate_source(source)
            return _outputs(context, product, raw)
        finally:
            for port in context.input_ports:
                port.close()


def _adjudication_configuration(context):
    """Authenticate the declared CONFIG before reading any outcome operand."""
    declaration = next(row for row in operation_declarations() if row.capability_key == KEY)
    ports = tuple(port for port in context.input_ports if port.artifact_id == context.config.artifact_id)
    if (len(ports) != 1 or ports[0].payload_schema != E1AdjudicationConfig.SCHEMA
            or (ports[0].outcome_access, ports[0].visibility_ceiling) != (
                declaration.outcome_access, declaration.visibility_ceiling)):
        raise ValueError('E1 evaluator changes its exact declared CONFIGURATION custody')
    validated_scientific_input_edges(context, config_port=ports[0])
    return ports[0]


def make_adjudication(context, config, result):
    authority, criterion = context.scientific_adjudication_context, config.sources[0].criterion
    if (authority is None or context.outcome_access is not OutcomeAccess.EVALUATOR_REVEAL
            or authority.outcome_access is not OutcomeAccess.EVALUATION_REVEALED
            or authority.visibility_ceiling is not VisibilityCeiling.OUTCOME_VISIBLE
            or authority.evidence_world_kind is not WorldKind.NUMERICAL_SIMULATOR
            or authority.evidence_world_id != criterion.world_id or authority.relation != criterion.relation
            or authority.independent_unit_id != criterion.independent_unit_id
            or authority.information_cutoffs != tuple(ObjectIdentity.from_record(c.cutoff_id, c) for c in cutoffs(config))
            or authority.plumbing_only or authority.fixture_scope_id is not None):
        raise ValueError('E1 adjudication requires exact genuine issued/revealed scientific context')
    evaluable = result.scientific_status is not ScientificStatus.UNEVALUABLE
    return ScientificAdjudicationRecord('adjudication.'+context.run_id+'.'+context.task_id,
        context.run_id, context.task_id, authority.execution_plan, context.input_materialization_ids,
        tuple(sorted(p.logical_artifact_id for p in context.output_ports if p.logical_artifact_id is not None)),
        context.dependency_receipt_ids, authority.evidence_world_id, authority.evidence_world_kind, authority.relation,
        authority.independent_unit_id, authority.information_cutoffs, authority.visibility_ceiling, authority.outcome_access,
        AdjudicationEvaluability.EVALUABLE if evaluable else AdjudicationEvaluability.UNEVALUABLE, result.scientific_status,
        AdmissionStatus.NOT_EVALUATED if evaluable else AdmissionStatus.UNEVALUABLE, result.reason_codes)


class E1Adjudicator:
    def __init__(self):
        self.manifest = next(m for m in operation_manifests() if m.capability_key == KEY)

    def execute(self, context):
        try:
            authority = getattr(context, 'scientific_adjudication_context', None)
            if (type(context) is not TaskContext or context.outcome_access is not OutcomeAccess.EVALUATOR_REVEAL
                    or authority is None or authority.outcome_access is not OutcomeAccess.EVALUATION_REVEALED
                    or authority.visibility_ceiling is not VisibilityCeiling.OUTCOME_VISIBLE
                    or authority.evidence_world_kind is not WorldKind.NUMERICAL_SIMULATOR
                    or authority.plumbing_only or authority.fixture_scope_id is not None):
                raise ValueError('E1 sealed outcome access requires genuine issued separate reveal context')
            config_port = _adjudication_configuration(context)
            configs, products, assessments, ports = [], [], [], []
            for port in context.input_ports:
                if port is config_port:
                    configs.append(decode_canonical_bytes(port.read(), E1AdjudicationConfig, maximum_bytes=None))
                elif port.payload_schema in (E1FactorProduct.SCHEMA, E1FactorAssessment.SCHEMA):
                    record_type = E1FactorProduct if port.payload_schema == E1FactorProduct.SCHEMA else E1FactorAssessment
                    record = decode_canonical_bytes(port.read(), record_type, maximum_bytes=None)
                    (products if record_type is E1FactorProduct else assessments).append(record)
                    ports.append((record, port, 'measure' if record_type is E1FactorProduct else 'check'))
                else:
                    raise ValueError('E1 evaluator receives undeclared or exposed products')
            if len(configs) != 1:
                raise ValueError('E1 evaluator requires its exact frozen configuration')
            config = configs[0]
            _worker(context, config, 'adjudicate', self.manifest)
            sources = {identity(s): s for s in config.sources}
            for record, port, role in ports:
                if record.source not in sources:
                    raise ValueError('E1 evaluator substitutes an allocated source')
                _dependency(context, port, sources[record.source], role)
            result = science.reduce_population(config.sources, tuple(products), tuple(assessments))
            adjudication = make_adjudication(context, config, result)
            outputs = {'product': result, 'adjudication': adjudication}
            if (len(context.output_ports) != 2 or {p.output_id.rsplit('.', 1)[-1] for p in context.output_ports} != set(outputs)
                    or any(p.payload_schema != outputs[p.output_id.rsplit('.', 1)[-1]].SCHEMA for p in context.output_ports)):
                raise ValueError('E1 evaluator changes exact result/adjudication outputs')
            return RunnerResult(tuple(TaskOutputPayload(p.output_id, outputs[p.output_id.rsplit('.', 1)[-1]].canonical_bytes())
                for p in context.output_ports), (ReceiptCheck('e1-full-family-risk-censoring-adjudication', True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_factories():
    factories = []
    for declaration in operation_declarations():
        selected = declaration.manifest()
        role = selected.capability_key.rsplit('.', 1)[-1]
        _, parts = bundle(role, ExtensionContributionKind.METHOD, selected, (), None,
                          namespace=NAMESPACE, maximum_config_bytes=None)
        factories.append(declaration.provider_factory(
            components=tuple(sorted(parts, key=lambda p: p.registration_id))))
    return tuple(factories)


def confirmation_draft(*, root, sources, scalar_definition, proof_owners, draft_id):
    """Compose only; stock qualifications, issue, contact and reveal stay external."""
    from empirical_lawhood.planning.recursive_authoring import (
        RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft,
    )
    sources = tuple(sorted(sources, key=lambda s: s.root_id))
    adjudication = E1AdjudicationConfig('config.'+KEY, sources)
    if (type(root) is not StudyDraft or root.campaign is None or root.experiment is None
            or type(scalar_definition) is not MatrixParameterScalarDefinition
            or tuple(sorted(set(proof_owners))) != proof_owners
            or any(s.rule.scalar_closure.normalization_owner.sha256 != scalar_definition.fingerprint() for s in sources)):
        raise ValueError('E1 authoring requires genuine prospective root and explicit proof owners')
    registrations = {r.selection.capability_key.rsplit('.', 1)[-1]: r for r in operation_registrations()}
    external, operations, links = {}, [], []
    def add(record, logical_id=None, publication=None):
        object_id = (record.coordinate_id if type(record) is MatrixParameterCoordinate else record.identity.object_id
            if type(record) is NumericalProducingProvenance else logical_id if type(record) is MatrixHistorySeed else identity(record).object_id)
        logical_id = object_id if logical_id is None else logical_id
        name = 'external.'+logical_id
        value = RecursiveExternalInput(name, logical_id, record.SCHEMA, 'application/json', None,
            OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, record.fingerprint(), 'SOURCE')
        if publication is not None:
            name = 'external.'+publication.logical.logical_artifact_id
            value = replace(value, input_id=name, logical_artifact_id=publication.logical.logical_artifact_id)
        if external.setdefault(name, value) != value:
            raise ValueError('E1 authoring substitutes shared scientific operand')
        return name
    for source in sources:
        source_port = add(source)
        for role, inputs, _, _ in PHASES:
            node = NAMESPACE+'.'+source.root_id+'.'+role
            config = E1OperationConfig('config.'+node, role, source)
            obligations = tuple(o for o, n in proof_owners if n == node)
            if not obligations:
                raise ValueError('E1 authoring omits explicit selected operation proof owners')
            operations.append(RecursiveOperationSpec.from_config(node_id=node, selection=registrations[role].selection,
                config_id=config.config_id, config=config, obligation_ids=obligations, resource_budget=BUDGET))
            for name, _ in inputs:
                if name == 'commitment':
                    links.append(RecursiveInputLink('edge.'+node+'.commitment', node, 'commitment',
                        producer_node_id=COMMIT_KEY, producer_output_id='product', scientific_role='SOURCE'))
                    continue
                values = {'source': source_port}
                if role in ('measure', 'check'):
                    values['scalar-definition'] = add(scalar_definition, source.rule.scalar_closure.normalization_owner.artifact_id)
                if role == 'history':
                    values.update(allocation=add(source.allocation, publication=source.reservation.publication),
                        selection=add(source.specification.selection, publication=source.specification.publication),
                        coordinate=add(source.coordinate, source.coordinate.coordinate_id),
                        provenance=add(source.provenance, source.provenance.identity.object_id))
                if name == 'streams':
                    for stream in source.root.streams:
                        port_name = name+'.'+stream.purpose
                        links.append(RecursiveInputLink('edge.'+node+'.'+port_name, node, port_name,
                            external_input_id=add(stream, source.root.stream_identity(stream).object_id), scientific_role='SOURCE'))
                elif name in values:
                    links.append(RecursiveInputLink('edge.'+node+'.'+name, node, name,
                        external_input_id=values[name], scientific_role='SOURCE'))
                else:
                    owner = name.removesuffix('-arrays')
                    links.append(RecursiveInputLink('edge.'+node+'.'+name, node, name,
                        producer_node_id=NAMESPACE+'.'+source.root_id+'.'+owner,
                        producer_output_id='arrays' if name.endswith('-arrays') else 'product',
                        scientific_role='HISTORY' if owner == 'history' else 'OUTCOME'))
        for owner in ('measure', 'check'):
            name = owner+'.'+source.root_id
            links.append(RecursiveInputLink('edge.'+KEY+'.'+name, KEY, name,
                producer_node_id=NAMESPACE+'.'+source.root_id+'.'+owner, producer_output_id='product', scientific_role='OUTCOME'))
    obligations = tuple(o for o, n in proof_owners if n == KEY)
    if not obligations or {n for _, n in proof_owners} - {o.node_id for o in operations} - {KEY, COMMIT_KEY}:
        raise ValueError('E1 authoring omits evaluator proof or names unavailable operation')
    operations.append(RecursiveOperationSpec.from_config(node_id=KEY, selection=registrations['adjudicate'].selection,
        config_id=adjudication.config_id, config=adjudication, obligation_ids=obligations, resource_budget=BUDGET))
    config = E1CommitmentConfig('config.'+COMMIT_KEY, sources)
    obligations = tuple(o for o, n in proof_owners if n == COMMIT_KEY)
    if not obligations:
        raise ValueError('E1 authoring omits explicit pure commitment proof owners')
    operations.append(RecursiveOperationSpec.from_config(node_id=COMMIT_KEY, selection=registrations['commit'].selection,
        config_id=config.config_id, config=config, obligation_ids=obligations, resource_budget=BUDGET))
    for name, external_id in (('allocation', add(sources[0].allocation, publication=sources[0].reservation.publication)),
            ('selection', add(sources[0].specification.selection, publication=sources[0].specification.publication)),
            *(('source.'+s.root_id, add(s)) for s in sources)):
        links.append(RecursiveInputLink('edge.'+COMMIT_KEY+'.'+name, COMMIT_KEY, name,
            external_input_id=external_id, scientific_role='SOURCE'))
    return RecursiveStudyDraft(draft_id, root.question, root.campaign, (), (), (), tuple(sorted(operations, key=lambda o: o.node_id)),
        tuple(sorted(external.values(), key=lambda x: x.input_id)), tuple(sorted(links, key=lambda x: x.edge_id)),
        tuple(sorted(o.node_id for o in operations)), prospective_draft=root)
