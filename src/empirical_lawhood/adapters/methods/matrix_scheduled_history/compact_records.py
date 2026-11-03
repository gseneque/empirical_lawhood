# SPDX-License-Identifier: MPL-2.0
"""Current bounded configurations for shared scheduled scientific operands."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult

from .commitment import ScheduledCommitment, ScheduledCommitmentConfig, ScheduledExposureAudit, corpus_artifact, validate_shared_source_bank
from .forecast import ScheduledForecastDesign, ScheduledPublicSource
from .records import ScheduledReservation, ScheduledSource, ScheduledSpecification, identity
from .response_records import ScheduledResponseProtocol
from .response_selection import ScheduledResponseSelection

NAMESPACE = 'matrix-scheduled-history-compact'


def compact_identity(record):
    for field in ('bank_id', 'source_id', 'config_id', 'commitment_id'):
        if hasattr(record, field):
            return ObjectIdentity.from_record(getattr(record, field), record)
    raise ValueError('compact scheduled record lacks its declared identity')


@dataclass(frozen=True, slots=True)
class ScheduledCompactBank(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/compact-bank'
    VERSION: ClassVar[str] = '3.0.0'
    bank_id: str
    reservation: ScheduledReservation
    specification: ScheduledSpecification
    provenances: tuple[NumericalProducingProvenance, ...]
    sources: tuple[ScheduledSource, ...]
    selected_root_ids: tuple[str, ...]
    audit: ScheduledExposureAudit
    audit_publication: ArtifactWriteResult
    forecast_design: ScheduledForecastDesign
    response_selection: ScheduledResponseSelection | None = None
    response_selection_publication: ArtifactWriteResult | None = None

    def __post_init__(self):
        validate_stable_id(self.bank_id)
        validate_shared_source_bank(reservation=self.reservation, specification=self.specification,
            provenances=self.provenances, sources=self.sources, selected_root_ids=self.selected_root_ids,
            audit=self.audit, audit_publication=self.audit_publication, forecast_design=self.forecast_design,
            response_selection=self.response_selection, response_selection_publication=self.response_selection_publication)

    @classmethod
    def from_commitment(cls, config, bank_id='bank.'+NAMESPACE):
        if type(config) is not ScheduledCommitmentConfig:
            raise TypeError('compact bank requires its exact current shared commitment')
        return cls(bank_id, config.reservation, config.specification, config.provenances,
            config.sources, config.selected_root_ids, config.audit, config.audit_publication,
            config.forecast_design, config.response_selection, config.response_selection_publication)

    def commitment_config(self, config_id='config.matrix-scheduled-history.commit'):
        return ScheduledCommitmentConfig(config_id, self.reservation, self.specification,
            self.provenances, self.sources, self.selected_root_ids, self.audit, self.audit_publication,
            self.forecast_design, self.response_selection, self.response_selection_publication)


@dataclass(frozen=True, slots=True)
class ScheduledCompactConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/compact-config'
    VERSION: ClassVar[str] = '3.0.0'
    config_id: str
    operation: str
    source: ScheduledSource
    bank: ObjectIdentity

    def __post_init__(self):
        if (type(self.source) is not ScheduledSource or self.bank.object_schema != ScheduledCompactBank.SCHEMA
                or self.bank.object_version != ScheduledCompactBank.VERSION or self.operation not in
                ('prefix', 'continue', 'continue-development', 'numerical', 'measure', 'check', 'project',
                 'full-numerical', 'full-numerical-development')
                or self.config_id != 'config.'+NAMESPACE+'.'+self.root_id+'.'+self.operation):
            raise ValueError('compact native configuration changes actual source/phase')

    @property
    def root_id(self):
        return self.source.root_id


@dataclass(frozen=True, slots=True)
class ScheduledCompactCommitmentConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/compact-commitment-config'
    VERSION: ClassVar[str] = '3.0.0'
    config_id: str
    bank: ScheduledCompactBank

    def __post_init__(self):
        if self.config_id != 'config.'+NAMESPACE+'.commit' or type(self.bank) is not ScheduledCompactBank:
            raise ValueError('compact commitment omits complete actual shared scientific bank')


def compact_committed(config):
    if type(config) is not ScheduledCompactCommitmentConfig:
        raise TypeError('compact commitment requires its exact current configuration')
    bank = config.bank
    return ScheduledCommitment('commitment.'+NAMESPACE+'.commit', compact_identity(config), compact_identity(bank),
        tuple(source.identity for source in bank.sources), tuple(source.root_id for source in bank.sources),
        bank.selected_root_ids, identity(bank.reservation.allocation), identity(bank.specification.selection),
        identity(bank.audit), tuple(corpus_artifact(value) for value in bank.audit.prior_corpus),
        identity(bank.forecast_design), None if bank.response_selection is None else bank.response_selection.identity)


def authenticate_prior_publications(plane, config_inputs):
    """Authenticate original published operands of the actual compact bank."""
    from .commitment import authenticate_publication
    configs = tuple(value.record for value in config_inputs if type(value.record) is ScheduledCompactCommitmentConfig)
    if not configs:
        return
    if len(configs) != 1:
        raise ValueError('compact scheduled inquiry requires one complete pre-access commitment')
    bank = configs[0].bank
    for record, publication in ((bank.reservation.allocation, bank.reservation.publication),
            (bank.specification.selection, bank.specification.publication), (bank.audit, bank.audit_publication)):
        authenticate_publication(plane, publication, record)
    for publication in bank.audit.prior_corpus:
        record = next(record for record in (bank.audit.census, *bank.audit.prior_scheduled_coordinates)
            if record.SCHEMA == publication.logical.payload_schema and record.fingerprint() == publication.logical.content_sha256)
        authenticate_publication(plane, publication, record)
    design = bank.forecast_design
    for record, publication in ((design.model_record, design.model_publication),
            (design.training_record, design.training_publication), (design.criterion_record, design.criterion_publication)):
        authenticate_publication(plane, publication, record)
    if design.calibration is not None:
        authenticate_publication(plane, design.calibration_publication)
    if bank.response_selection is not None:
        authenticate_publication(plane, bank.response_selection_publication, bank.response_selection)
        for publication in bank.response_selection.template_publications:
            authenticate_publication(plane, publication)


@dataclass(frozen=True, slots=True)
class ScheduledCompactForecastConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/compact-forecast-config'
    VERSION: ClassVar[str] = '2.0.0'
    config_id: str
    public_source: ScheduledPublicSource
    design: ObjectIdentity
    calibrated: bool = False

    def __post_init__(self):
        if (type(self.public_source) is not ScheduledPublicSource or self.design.object_schema != ScheduledForecastDesign.SCHEMA
                or type(self.calibrated) is not bool
                or self.config_id != 'config.'+NAMESPACE+'.'+self.root_id+'.'+self.operation):
            raise ValueError('compact predictor changes exact public source/design/phase')

    @property
    def root_id(self):
        return self.public_source.root.root_id

    @property
    def operation(self):
        return 'forecast-calibrated' if self.calibrated else 'forecast'


@dataclass(frozen=True, slots=True)
class ScheduledCompactResponseConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/compact-response-config'
    VERSION: ClassVar[str] = '3.0.0'
    config_id: str
    operation: str
    source: ScheduledSource
    selection: ObjectIdentity
    bank: ObjectIdentity

    def __post_init__(self):
        if (type(self.source) is not ScheduledSource or self.selection.object_schema != ScheduledResponseSelection.SCHEMA
                or self.bank.object_schema != ScheduledCompactBank.SCHEMA or self.bank.object_version != ScheduledCompactBank.VERSION
                or self.operation not in ('responses', 'response-score', 'responses-development', 'response-score-development')
                or self.config_id != 'config.'+NAMESPACE+'.'+self.root_id+'.'+self.operation):
            raise ValueError('compact response changes exact source/selection/phase')

    @property
    def root_id(self):
        return self.source.root_id


@dataclass(frozen=True, slots=True)
class ScheduledCompactPhysicalForecastConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/compact-physical-forecast-config'
    VERSION: ClassVar[str] = '2.0.0'
    config_id: str
    protocol: ScheduledResponseProtocol

    def __post_init__(self):
        if (type(self.protocol) is not ScheduledResponseProtocol
                or self.config_id != 'config.'+NAMESPACE+'.'+self.root_id+'.physical-forecast'):
            raise ValueError('compact physical predictor changes its exact public configuration')

    @property
    def root_id(self):
        return self.protocol.public_source.root.root_id


@dataclass(frozen=True, slots=True)
class ScheduledCompactCalibrationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/compact-calibration-config'
    VERSION: ClassVar[str] = '3.0.0'
    config_id: str
    bank: ObjectIdentity
    calibration_id: str
    qualify: bool
    group_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.calibration_id)
        require_sorted_unique_strings(self.group_ids, field_name='calibration group_ids', allow_empty=False)
        if (self.bank.object_schema != ScheduledCompactBank.SCHEMA or self.bank.object_version != ScheduledCompactBank.VERSION
                or type(self.qualify) is not bool or self.config_id != 'config.'+NAMESPACE+'.'+self.operation):
            raise ValueError('compact calibration changes actual shared bank/phase/group census')

    @property
    def operation(self):
        return 'calibration-qualify' if self.qualify else 'calibrate'


def compact_native_contract(source, phase, *, bank):
    from .source_index import ResolvedScheduledSource
    if type(source) is not ResolvedScheduledSource or type(bank) is not ScheduledCompactBank:
        raise TypeError('compact native contract requires its resolved source and actual shared bank')
    reference = source.reference
    source.index.require_shared_source(reference, bank)
    suffix = '-development' if source.evidence_role == 'EXPOSED_DEVELOPMENT_NONPROMOTABLE' else ''
    if phase not in ('prefix', 'continue'+suffix, 'responses'+suffix):
        raise ValueError('compact native contract changes its actual native phase/access lane')
    task = NAMESPACE+'.'+source.root_id+'.'+phase
    if phase.startswith('responses'):
        selection = bank.response_selection
        if selection is None:
            raise ValueError('compact pulse contract omits complete selected response population')
        config = ScheduledCompactResponseConfig('config.'+task, phase, reference, selection.identity, compact_identity(bank))
        operation = NAMESPACE+'.pulse-response-v2'
    else:
        config = ScheduledCompactConfig('config.'+task, phase, reference, compact_identity(bank))
        operation = NAMESPACE+('.prefix-before-continuation.v2' if phase == 'prefix' else '.exact-checkpoint-continuation.v2')
    operands = (reference.identity, compact_identity(bank), reference.allocation, reference.selection,
        reference.coordinate, reference.provenance)
    return compact_identity(config), task, operation, tuple(sorted(operands, key=lambda value: value.object_id))
