# SPDX-License-Identifier: MPL-2.0
"""Bounded real global freeze before programme wave admission.

The actual configuration and output have distinct identities. The shared
commitment is explicitly inner semantic data; it is never advertised as the
actual configuration/publication of this different runtime contract.
"""

from empirical_lawhood.runtime.recursive_provider import (
    RecursiveOperationDeclaration, RecursiveScientificHooks, RecursiveExecutionProperties,
)

from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS

from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.study_authoring import StudyDraft
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskContext, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract

from .commitment import ScheduledCommitment
from .commitment import require_publication_copy
from .compact_records import NAMESPACE as COMPACT_NAMESPACE, ScheduledCompactBank, compact_identity
from .operation_bindings import BUDGET
from .programme_composition import expected_global_commitment
from .programme_records import MAXIMUM_PROGRAMME_BYTES, NAMESPACE, ScheduledProgramme, validate_programme_bank

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT

GLOBAL_TASK_ID = COMPACT_NAMESPACE+'.commit'
GLOBAL_CONFIG_ID = 'config.'+NAMESPACE+'.global-commit'
MAXIMUM_CONFIG_BYTES = 4*1024**2
BLIND, PROSPECTIVE = OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeGlobalCommitConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/global-commit-config'
    config_id: str
    programme: ScheduledProgramme
    bank: ObjectIdentity

    def __post_init__(self):
        if (self.config_id != GLOBAL_CONFIG_ID or type(self.programme) is not ScheduledProgramme
                or self.bank != self.programme.bank or len(self.canonical_bytes()) > MAXIMUM_CONFIG_BYTES):
            raise ValueError('programme global freeze requires its explicit bounded actual configuration and exact bank pin')
        if self.programme.mode == 'E4_CONFIRMATION':
            raise ValueError('programme confirmation global entry requires the genuine qualified-parent bridge')


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeGlobalCommit(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/global-commit'
    commitment_id: str
    configuration: ObjectIdentity
    programme: ObjectIdentity
    bank: ObjectIdentity
    semantic_commitment: ScheduledCommitment

    def __post_init__(self):
        validate_stable_id(self.commitment_id)
        if (self.configuration.object_schema != ScheduledProgrammeGlobalCommitConfig.SCHEMA
                or self.configuration.object_id != GLOBAL_CONFIG_ID
                or self.programme.object_schema != ScheduledProgramme.SCHEMA
                or self.bank.object_schema != ScheduledCompactBank.SCHEMA
                or type(self.semantic_commitment) is not ScheduledCommitment
                or self.semantic_commitment.shared_context != self.bank
                or self.commitment_id != self.programme.object_id+'.global-commit'):
            raise ValueError('programme global product aliases actual runtime and inner semantic commitment identities')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.commitment_id, self)


def global_committed(config, bank):
    if type(config) is not ScheduledProgrammeGlobalCommitConfig:
        raise ValueError('programme global product requires its actual additive configuration')
    validate_programme_bank(config.programme, bank)
    if bank.forecast_design.calibration is not None:
        raise ValueError('programme global entry cannot consume a sealed calibration without its genuine qualified-parent bridge')
    if compact_identity(bank) != config.bank:
        raise ValueError('programme global freeze substitutes its original bank')
    return ScheduledProgrammeGlobalCommit(config.programme.programme_id+'.global-commit',
        ObjectIdentity.from_record(config.config_id, config), config.programme.identity, config.bank,
        expected_global_commitment(bank))


def validate_programme_root(programme, context, *, bank_identity=None):
    """Require the original global study, all groups and frozen cutoffs.

    Wave callbacks additionally check the explicit exhaustive subdivision and
    local phase census. They do not substitute a smaller scientific study.
    """
    from .compact_qualification import _qualification
    if type(programme) is not ScheduledProgramme:
        raise ValueError('programme root requires its closed frozen global scientific declaration')
    root = context.root
    if (type(root) is not StudyDraft or root.system is None or root.experiment is None or root.campaign is None
            or root.unresolved_decisions or root.system.world.kind is not WorldKind.NUMERICAL_SIMULATOR
            or root.experiment.system_id != root.system.system_id or root.experiment.world_id != root.system.world.world_id
            or tuple(sorted((*root.development_unit_ids, *root.evaluation_unit_ids))) != programme.group_ids
            or root.development_unit_ids != (programme.group_ids if programme.mode == 'E4_DEVELOPMENT' else ())
            or root.experiment.information_cutoffs != tuple(case.information_cutoff for case in programme.cases)):
        raise ValueError('programme root changes the genuine global study, whole-group denominator or absolute cutoffs')
    expected = {programme.identity, programme.bank, programme.reservation, programme.allocation, programme.specification,
        programme.forecast_design, programme.response_selection, programme.criterion, *programme.source_census}
    if not expected <= {item.object_identity for item in root.design_inputs}:
        raise ValueError('programme root omits original global scientific identities and full role/source census')
    bank_identity = programme.bank if bank_identity is None else bank_identity
    if bank_identity != programme.bank:
        raise ValueError('programme root substitutes its original global bank identity')
    _qualification(root, context, bank_identity.object_id, bank_identity.object_schema, bank_identity.object_fingerprint,
        BLIND, PROSPECTIVE, bank_identity.object_version)


def scientific_root_validator(config, context):
    if (type(config) is not ScheduledProgrammeGlobalCommitConfig or context.node_id != GLOBAL_TASK_ID
            or context.stage is not ScientificStage.FREEZE or context.outcome_access is not BLIND
            or context.visibility_ceiling is not PROSPECTIVE or context.unit_ids != config.programme.group_ids
            or context.selected_unit_ids != config.programme.group_ids
            or len(context.config_inputs) != 1 or context.config_inputs[0].record != config):
        raise ValueError('programme global freeze changes its exact actual node, stage or global unit scope')
    validate_programme_root(config.programme, context, bank_identity=config.bank)


def source_publications(bank):
    """All actual original blind operands, including the full prior corpus."""
    design = bank.forecast_design
    values = ((bank.reservation.allocation, bank.reservation.publication),
        (bank.specification.selection, bank.specification.publication), (bank.audit, bank.audit_publication),
        (design.model_record, design.model_publication), (design.training_record, design.training_publication),
        (design.criterion_record, design.criterion_publication), (bank.response_selection, bank.response_selection_publication))
    corpus = (bank.audit.census, *bank.audit.prior_scheduled_coordinates)
    values += tuple((next(record for record in corpus if (record.SCHEMA, record.fingerprint()) ==
        (publication.logical.payload_schema, publication.logical.content_sha256)), publication) for publication in bank.audit.prior_corpus)
    return values


class ScheduledProgrammeGlobalCommitter:
    def __init__(self, manifest):
        self.manifest = manifest

    def execute(self, context):
        try:
            if (type(context) is not TaskContext or context.task_id != GLOBAL_TASK_ID
                    or context.permissions != self.manifest.permissions or context.outcome_access is not BLIND
                    or not BUDGET.contains(context.resource_budget)
                    or any(port.kind is not WorkerInputKind.EXTERNAL or port.outcome_access is not BLIND
                        or port.visibility_ceiling is not PROSPECTIVE for port in context.input_ports)):
                raise ValueError('programme global freeze refuses changed actual runtime source/access context')
            config_ports = tuple(p for p in context.input_ports if p.payload_schema == ScheduledProgrammeGlobalCommitConfig.SCHEMA)
            bank_ports = tuple(p for p in context.input_ports if p.payload_schema == ScheduledCompactBank.SCHEMA)
            if len(config_ports) != 1 or len(bank_ports) != 1:
                raise ValueError('programme global freeze requires one actual configuration and bank source')
            config_raw, bank_raw = config_ports[0].read(), bank_ports[0].read()
            config = decode_canonical_bytes(config_raw, ScheduledProgrammeGlobalCommitConfig, maximum_bytes=MAXIMUM_CONFIG_BYTES)
            bank = decode_canonical_bytes(bank_raw, ScheduledCompactBank, maximum_bytes=MAXIMUM_PROGRAMME_BYTES)
            if (config.canonical_bytes() != config_raw or bank.canonical_bytes() != bank_raw
                    or context.config.config_id != config.config_id or context.config.config_schema != config.SCHEMA
                    or context.config.content_sha256 != sha256(config_raw).hexdigest()
                    or context.config.artifact_id != config_ports[0].artifact_id
                    or bank_ports[0].artifact_id != bank.bank_id or sha256(bank_raw).hexdigest() != config.bank.object_fingerprint):
                raise ValueError('programme global freeze substitutes exact actual configuration/shared source bytes')
            validate_programme_bank(config.programme, bank)
            expected_ids = {config_ports[0].artifact_id, bank.bank_id}
            for record, publication in source_publications(bank):
                ports = tuple(p for p in context.input_ports if p.artifact_id == publication.logical.logical_artifact_id)
                if len(ports) != 1:
                    raise ValueError('programme global freeze drops an original published operand')
                actual_raw = ports[0].read()
                if (sha256(actual_raw).hexdigest() != publication.logical.content_sha256
                        or sha256(actual_raw).hexdigest() != publication.materialization.physical_sha256
                        or actual_raw != record.canonical_bytes()):
                    raise ValueError('programme global freeze substitutes original exact operand bytes')
                require_publication_copy(record, ports[0], publication)
                expected_ids.add(ports[0].artifact_id)
            for publication in bank.response_selection.template_publications:
                ports = tuple(p for p in context.input_ports if p.artifact_id == publication.logical.logical_artifact_id)
                if len(ports) != 1:
                    raise ValueError('programme global freeze drops a fixed original instrument publication')
                raw = ports[0].read()
                if (ports[0].payload_schema != MATRIX_ARRAY_SCHEMA or len(raw) != publication.materialization.size_bytes
                        or sha256(raw).hexdigest() != publication.logical.content_sha256
                        or sha256(raw).hexdigest() != publication.materialization.physical_sha256
                        or ports[0].media_type != publication.logical.media_type
                        or ports[0].size_bytes != publication.materialization.size_bytes):
                    raise ValueError('programme global freeze substitutes its original physical instrument bytes')
                expected_ids.add(ports[0].artifact_id)
            if len(context.input_ports) != len(expected_ids) or {p.artifact_id for p in context.input_ports} != expected_ids:
                raise ValueError('programme global freeze adds undeclared or repeated source/future input')
            value = global_committed(config, bank)
            if (len(context.output_ports) != 1 or context.output_ports[0].output_id != GLOBAL_TASK_ID+'.product'
                    or context.output_ports[0].payload_schema != value.SCHEMA
                    or context.output_ports[0].profile is not ArtifactProfile.CANONICAL_JSON):
                raise ValueError('programme global freeze changes its explicit actual wrapper output')
            return RunnerResult((TaskOutputPayload(GLOBAL_TASK_ID+'.product', value.canonical_bytes()),),
                (ReceiptCheck('programme-global-original-published-whole-bank-freeze', True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_factories():
    return tuple(row.provider_factory() for row in operation_declarations())


def programme_global_draft(*, root, programme, bank, proof_owners, resource_budget, template_bytes, draft_id):
    """Compose one genuine bounded global freeze; it performs no native work."""
    from empirical_lawhood.planning.recursive_authoring import (
        RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft,
    )
    validate_programme_bank(programme, bank)
    if (type(root) is not StudyDraft or tuple(sorted(set(proof_owners))) != proof_owners or not proof_owners
            or not BUDGET.contains(resource_budget)):
        raise ValueError('programme global composition requires its actual full root, explicit owners and contained budget')
    factory, = operation_factories()
    config = ScheduledProgrammeGlobalCommitConfig(GLOBAL_CONFIG_ID, programme, compact_identity(bank))
    operation = RecursiveOperationSpec.from_config(node_id=GLOBAL_TASK_ID, selection=factory.registration.selection,
        config_id=config.config_id, config=config, obligation_ids=proof_owners, resource_budget=resource_budget)
    external, records, links = {}, {}, []

    def add(port, record, logical_id, publication=None):
        raw = record if type(record) is bytes else record.canonical_bytes()
        schema = publication.logical.payload_schema if publication is not None else record.SCHEMA
        media = publication.logical.media_type if publication is not None else 'application/json'
        value = RecursiveExternalInput('external.'+logical_id, logical_id, schema, media, len(raw),
            BLIND, PROSPECTIVE, sha256(raw).hexdigest(), 'SOURCE')
        if external.setdefault(value.input_id, value) != value or records.setdefault(logical_id, record) != record:
            raise ValueError('programme global composition aliases different source bytes')
        links.append(RecursiveInputLink('edge.'+GLOBAL_TASK_ID+'.'+port, GLOBAL_TASK_ID, port,
            external_input_id=value.input_id, scientific_role='SOURCE'))

    add('bank', bank, bank.bank_id)
    source_roles = {
        'empirical-lawhood/matrix-scheduled-history/allocation': 'allocation',
        'empirical-lawhood/matrix-scheduled-history/selection': 'selection',
        'empirical-lawhood/matrix-scheduled-history/exposure-audit': 'audit',
        bank.forecast_design.model_record.SCHEMA: 'model', bank.forecast_design.training_record.SCHEMA: 'training',
        bank.forecast_design.criterion_record.SCHEMA: 'criterion', bank.response_selection.SCHEMA: 'response-selection',
        bank.audit.census.SCHEMA: 'prior-census',
    }
    for record, publication in source_publications(bank):
        role = source_roles.get(record.SCHEMA, 'prior-coordinates.'+record.coordinate_id if hasattr(record, 'coordinate_id') else None)
        if role is None:
            raise ValueError('programme global composition has an unsupported original operand')
        add(role, record, publication.logical.logical_artifact_id, publication)
    expected_templates = {p.templates.array_artifact.artifact_id: p.templates.array_artifact for p in bank.response_selection.protocols}
    if set(template_bytes) != set(expected_templates):
        raise ValueError('programme global composition drops its exact complete fixed instrument census')
    for key, artifact in sorted(expected_templates.items()):
        raw = template_bytes[key]
        publication, = (p for p in bank.response_selection.template_publications if p.logical.logical_artifact_id == key)
        if type(raw) is not bytes or len(raw) != artifact.size_bytes or sha256(raw).hexdigest() != artifact.sha256:
            raise ValueError('programme global composition substitutes actual fixed instrument bytes')
        add('templates.'+key, raw, key, publication)
    draft = RecursiveStudyDraft(draft_id, root.question, root.campaign, (), (), (), (operation,),
        tuple(sorted(external.values(), key=lambda e: e.input_id)), tuple(sorted(links, key=lambda e: e.edge_id)),
        (GLOBAL_TASK_ID,), prospective_draft=root)
    return draft, records


def operation_declarations():
    from .commitment import ScheduledExposureAudit
    from .records import ScheduledAllocation, ScheduledSelection
    from .response_selection import ScheduledResponseSelection
    from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import MatrixFactorExposureCensus
    from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import MatrixResponseErrorModel, MatrixResponseErrorPredictionSpec
    from empirical_lawhood.adapters.methods.matrix_factor_response.response_frontier import MatrixResponseFrontierProtocol
    from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
    inputs = (('bank', ScheduledCompactBank, 1, 1), ('allocation', ScheduledAllocation, 1, 1), ('selection', ScheduledSelection, 1, 1), ('audit', ScheduledExposureAudit, 1, 1), ('model', MatrixResponseErrorModel, 1, 1), ('training', MatrixResponseErrorPredictionSpec, 1, 1), ('criterion', MatrixResponseFrontierProtocol, 1, 1), ('response-selection', ScheduledResponseSelection, 1, 1), ('prior-census', MatrixFactorExposureCensus, 1, 1), ('prior-coordinates', MatrixParameterCoordinate, 0, None))
    ports = tuple(sorted((*(RecursivePortContract(name, cls.SCHEMA, 'application/json', MAXIMUM_PROGRAMME_BYTES, minimum_count=minimum, maximum_count=maximum) for name, cls, minimum, maximum in inputs), RecursivePortContract('templates', MATRIX_ARRAY_SCHEMA, 'application/x-npz', MAXIMUM_PROGRAMME_BYTES, minimum_count=1, maximum_count=None)), key=lambda p: p.port_id))
    selected = RecursiveOperationDeclaration(
        capability_key=NAMESPACE + "." + 'global-commit',
        capability_version="1.0.0",
        implementation_id='bounded-actual-global-freeze.v1',
        kind=CapabilityKind.EXPERIMENT_DESIGNER,
        config_record_type=ScheduledProgrammeGlobalCommitConfig,
        stage=ScientificStage.FREEZE,
        input_ports=ports,
        outputs=(OutputTemplate('product', ScheduledProgrammeGlobalCommit.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'),),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_FROZEN_MODELS))),
        evidence_ceiling=EvidenceCeiling.RESPONSE,
        outcome_access=BLIND,
        visibility_ceiling=PROSPECTIVE,
        resources=BUDGET,
        conformance_check_ids=tuple(sorted(('distinct-actual-and-semantic-identities', 'exact-global576-census', 'original-published-operands'))),
        runner_factory=lambda: ScheduledProgrammeGlobalCommitter(selected.manifest()),
        record_codecs={ScheduledProgrammeGlobalCommit.SCHEMA: ScheduledProgrammeGlobalCommit, **{kind.SCHEMA: kind for _, kind, _, _ in inputs}},
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=lambda c: tuple(sorted({c.programme.fingerprint(), c.bank.object_fingerprint})), scientific_unit_ids=lambda c: c.programme.group_ids, scientific_root_validator=scientific_root_validator),
        execution_properties=RecursiveExecutionProperties(barrier=BarrierKind.FREEZE),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,),
        storage_codecs=MATRIX_STORAGE_CODECS,
    )
    return (selected,)
