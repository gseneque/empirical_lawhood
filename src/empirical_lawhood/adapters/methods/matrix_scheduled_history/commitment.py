# SPDX-License-Identifier: MPL-2.0
"""Pure pre-access source commitment; publication and qualification differ.

The actual audit and prior corpus enter as qualified source materializations.
Matching bytes does not establish their truth or completeness. This operation
creates no allocation, credentials, source qualification or native contact.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import MatrixFactorExposureCensus
from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import MatrixResponseErrorModel, MatrixResponseErrorPredictionSpec
from empirical_lawhood.adapters.methods.matrix_factor_response.response_frontier import MatrixResponseFrontierProtocol
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteResult, ReceiptCheck
from empirical_lawhood.runtime.execution import RunnerResult, TaskContext, TaskOutputPayload, WorkerInputKind

from .records import (
    NAMESPACE, ScheduledAllocation, ScheduledReservation, ScheduledSelection, ScheduledSource,
    ScheduledSpecification, _publication, identity,
)
from .forecast import ScheduledForecastDesign
from .response_selection import ScheduledResponseSelection

COMMIT_KEY = NAMESPACE+'.commit'


@dataclass(frozen=True, slots=True)
class ScheduledExposureAudit(CanonicalRecord):
    """Exact current exposure declaration with actual immutable publications."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/exposure-audit'
    audit_id: str
    census: MatrixFactorExposureCensus
    prior_scheduled_coordinates: tuple[MatrixParameterCoordinate, ...]
    prior_corpus: tuple[ArtifactWriteResult, ...]

    def __post_init__(self):
        validate_stable_id(self.audit_id)
        require_sorted_unique_ids(self.prior_scheduled_coordinates, attribute='coordinate_id', field_name='prior_scheduled_coordinates')
        ids = tuple(p.logical.logical_artifact_id for p in self.prior_corpus)
        if (type(self.census) is not MatrixFactorExposureCensus or not self.prior_corpus
                or ids != tuple(sorted(set(ids))) or any(type(p) is not ArtifactWriteResult for p in self.prior_corpus)
                or any(p.logical.outcome_access is not OutcomeAccess.OUTCOME_BLIND
                    or p.logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE for p in self.prior_corpus)):
            raise ValueError('scheduled audit omits exact current blind census/coordinate publications')
        records = (self.census, *self.prior_scheduled_coordinates)
        if ({(p.logical.payload_schema, p.logical.content_sha256) for p in self.prior_corpus} !=
                {(r.SCHEMA, r.fingerprint()) for r in records} or len(self.prior_corpus) != len(records)):
            raise ValueError('scheduled audit requires complete original exposure census and coordinate metadata corpus')
        for record in records:
            publication = next(p for p in self.prior_corpus if (p.logical.payload_schema, p.logical.content_sha256) ==
                (record.SCHEMA, record.fingerprint()))
            _publication(publication, record)

    def validate_source(self, source):
        declared = source.allocation.exposure
        if (self.census != declared.census or self.prior_scheduled_coordinates != declared.prior_scheduled_coordinates
                or declared.scheduled_audit.payload_schema != self.SCHEMA
                or declared.scheduled_audit.sha256 != self.fingerprint()
                or declared.scheduled_audit.size_bytes != self.canonical_size_bytes()):
            raise ValueError('scheduled source substitutes actual audit/corpus bytes or full declared exposures')
        for coordinate in self.prior_scheduled_coordinates:
            matches = tuple(p for p in self.prior_corpus if p.logical.payload_schema == coordinate.SCHEMA
                and p.logical.content_sha256 == coordinate.fingerprint())
            if len(matches) != 1:
                raise ValueError('scheduled audit omits actual original prior coordinate corpus publication')
            _publication(matches[0], coordinate)


def corpus_artifact(publication):
    return ArtifactIdentity(publication.logical.logical_artifact_id, 'scheduled-qualified-prior-corpus',
        publication.logical.payload_schema, publication.logical.content_sha256, publication.logical.media_type,
        publication.materialization.size_bytes)


def exposure_census_publication(audit):
    """The one exact current compact census publication, without old corpus I/O."""
    if type(audit) is not ScheduledExposureAudit:
        raise TypeError('current exposure support requires its exact scheduled audit')
    matches = tuple(value for value in audit.prior_corpus if
        (value.logical.payload_schema, value.logical.content_sha256) == (audit.census.SCHEMA, audit.census.fingerprint()))
    if len(matches) != 1:
        raise ValueError('current exposure support omits or repeats its exact compact census publication')
    _publication(matches[0], audit.census)
    return matches[0]


def exposure_support(audit):
    """Current census custody; external factual provenance remains content pins."""
    publication = exposure_census_publication(audit)
    artifact = ArtifactIdentity(publication.logical.logical_artifact_id, 'matrix-current-exposure-census',
        publication.logical.payload_schema, publication.logical.content_sha256,
        publication.logical.media_type, publication.materialization.size_bytes)
    return ((artifact, publication),)


@dataclass(frozen=True, slots=True)
class ScheduledCommitmentConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/commitment-config'
    VERSION: ClassVar[str] = '2.0.0'
    config_id: str
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
        if self.config_id != 'config.' + COMMIT_KEY:
            raise ValueError('scheduled commitment changes its current configuration identity')
        validate_shared_source_bank(reservation=self.reservation, specification=self.specification,
            provenances=self.provenances, sources=self.sources, selected_root_ids=self.selected_root_ids,
            audit=self.audit, audit_publication=self.audit_publication, forecast_design=self.forecast_design,
            response_selection=self.response_selection, response_selection_publication=self.response_selection_publication)


def validate_shared_source_bank(*, reservation, specification, provenances, sources, selected_root_ids,
        audit, audit_publication, forecast_design, response_selection=None, response_selection_publication=None):
    """Complete current shared-parent and scientific scope validation, once per bank."""
    from .source_index import ScheduledSourceIndex
    require_sorted_unique_strings(selected_root_ids, field_name='selected_root_ids', allow_empty=False)
    index = ScheduledSourceIndex.from_shared(reservation=reservation, specification=specification,
        provenances=provenances)
    index.require_roster(sources, expected_root_ids=index.root_ids)
    if (not set(selected_root_ids) <= set(index.root_ids)
            or {source.provenance for source in sources} != {value.identity for value in provenances}
            or type(audit) is not ScheduledExposureAudit):
        raise ValueError('scheduled commitment omits complete sources/provenance or selected whole-bank scope')
    audit.validate_source(index.resolve(sources[0]))
    _publication(audit_publication, audit)
    if (type(forecast_design) is not ScheduledForecastDesign
            or tuple(root for root, _ in forecast_design.source_scopes) != selected_root_ids):
        raise ValueError('scheduled commitment omits actual frozen selected model/criterion/query bank')
    selected = set(selected_root_ids)
    for reference in sources:
        if reference.root_id in selected:
            forecast_design.validate_source(index.resolve(reference))
    if (response_selection is None) != (response_selection_publication is None):
        raise ValueError('scheduled response commitment omits original frozen selection publication')
    if response_selection is not None:
        if type(response_selection) is not ScheduledResponseSelection:
            raise TypeError('scheduled commitment requires its exact current response selection')
        response_selection.validate_allocation(reservation.allocation)
        _publication(response_selection_publication, response_selection)
        if tuple(p.public_source.root.root_id for p in response_selection.protocols) != selected_root_ids:
            raise ValueError('scheduled pulse commitment thins whole selected bank')
        for reference in sources:
            if reference.root_id in selected:
                protocol, _ = response_selection.validate_source(index.resolve(reference))
                protocol.validate_error_design(forecast_design)
    if audit_publication.logical.logical_artifact_id != reservation.allocation.exposure.scheduled_audit.artifact_id:
        raise ValueError('scheduled commitment substitutes actual original audit publication identity')
    groups = {}
    for reference in sources:
        groups.setdefault(reference.root.root.independent_group_id, set()).add(reference.root_id)
    for roots in groups.values():
        if roots & selected and not roots <= selected:
            raise ValueError('scheduled commitment selects only part of one matched independent group')
    return index


@dataclass(frozen=True, slots=True)
class ScheduledCommitment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/commitment'
    VERSION: ClassVar[str] = '3.0.0'
    commitment_id: str
    configuration: ObjectIdentity
    shared_context: ObjectIdentity
    sources: tuple[ObjectIdentity, ...]
    root_ids: tuple[str, ...]
    selected_root_ids: tuple[str, ...]
    allocation: ObjectIdentity
    selection: ObjectIdentity
    audit: ObjectIdentity
    prior_corpus: tuple[ArtifactIdentity, ...]
    forecast_design: ObjectIdentity
    response_selection: ObjectIdentity | None = None

    def __post_init__(self):
        from .compact_records import NAMESPACE as COMPACT_NAMESPACE, ScheduledCompactBank, ScheduledCompactCommitmentConfig
        configurations = {
            (ScheduledCommitmentConfig.SCHEMA, ScheduledCommitmentConfig.VERSION): 'commitment.' + COMMIT_KEY,
            (ScheduledCompactCommitmentConfig.SCHEMA, ScheduledCompactCommitmentConfig.VERSION):
                'commitment.' + COMPACT_NAMESPACE + '.commit',
        }
        if (type(self.configuration) is not ObjectIdentity
                or type(self.shared_context) is not ObjectIdentity
                or configurations.get((self.configuration.object_schema, self.configuration.object_version)) != self.commitment_id
                or self.configuration.object_id != 'config.' + self.commitment_id.removeprefix('commitment.')
                or not self.sources or len(self.sources) != len(self.root_ids)
                or any(type(s) is not ObjectIdentity or
                    (s.object_schema, s.object_version) != (ScheduledSource.SCHEMA, ScheduledSource.VERSION)
                    for s in self.sources)):
            raise ValueError('scheduled commitment changes exact full source/configuration closure')
        self.configuration.__post_init__()
        self.shared_context.__post_init__()
        if (self.configuration.object_schema == ScheduledCommitmentConfig.SCHEMA
                and self.shared_context != self.configuration
                or self.configuration.object_schema == ScheduledCompactCommitmentConfig.SCHEMA
                and (self.shared_context.object_schema, self.shared_context.object_version) !=
                    (ScheduledCompactBank.SCHEMA, ScheduledCompactBank.VERSION)):
            raise ValueError('scheduled commitment changes its exact current shared context owner')
        require_sorted_unique_strings(self.root_ids, field_name='root_ids', allow_empty=False)
        require_sorted_unique_strings(self.selected_root_ids, field_name='selected_root_ids', allow_empty=False)
        require_sorted_unique_ids(self.prior_corpus, attribute='artifact_id', field_name='prior_corpus')
        if (not set(self.selected_root_ids) <= set(self.root_ids)
                or self.forecast_design.object_schema != ScheduledForecastDesign.SCHEMA
                or self.allocation.object_schema != ScheduledAllocation.SCHEMA
                or self.selection.object_schema != ScheduledSelection.SCHEMA
                or self.audit.object_schema != ScheduledExposureAudit.SCHEMA):
            raise ValueError('scheduled commitment changes frozen selection/audit/forecast or selected census')

    def validate_source(self, source):
        from .source_index import ResolvedScheduledSource
        if (type(source) is not ResolvedScheduledSource or source.root_id not in self.selected_root_ids
                or self.root_ids != source.index.root_ids
                or self.sources[source.index._root_positions[source.root_id]] != source.reference.identity
                or self.allocation != source.reference.allocation or self.selection != source.reference.selection
                or self.audit.object_fingerprint != source.allocation.exposure.scheduled_audit.sha256):
            raise ValueError('scheduled prefix source differs from prior receipted whole-bank commitment')


def committed(config):
    if type(config) is not ScheduledCommitmentConfig:
        raise TypeError('scheduled commitment requires its actual current shared-parent configuration')
    configuration = ObjectIdentity.from_record(config.config_id, config)
    return ScheduledCommitment('commitment.'+COMMIT_KEY, configuration, configuration,
        tuple(source.identity for source in config.sources), tuple(s.root_id for s in config.sources), config.selected_root_ids,
        identity(config.reservation.allocation), identity(config.specification.selection),
        ObjectIdentity.from_record(config.audit.audit_id, config.audit), tuple(corpus_artifact(p) for p in config.audit.prior_corpus),
        identity(config.forecast_design), None if config.response_selection is None else config.response_selection.identity)


def authenticate_publication(plane, publication, record=None):
    relative = publication.materialization.relative_path
    sidecar = relative+'.manifest.json'
    raw = read_bounded_bytes(plane.root.resolve(sidecar, for_write=False), maximum_bytes=plane.custody_limits.manifest_bytes)
    expected = plane._manifest_materialization(logical_artifact_id=publication.logical.logical_artifact_id, relative_path=sidecar, payload=raw)
    if expected != publication.manifest_materialization:
        raise ValueError('scheduled prior corpus substitutes original exact sidecar materialization')
    manifest = decode_artifact_manifest(raw)
    if manifest.logical != publication.logical or manifest.materialization != publication.materialization:
        raise ValueError('scheduled prior publication differs from actual guarded manifest custody')
    # The complete publication verifier guards this exact sidecar and every
    # sibling through current member access. A sidecar is control metadata,
    # not another independently published payload with its own sidecar.
    plane.verify_manifest(manifest)
    if record is not None:
        raw = read_bounded_bytes(plane.root.resolve(relative, for_write=False), maximum_bytes=publication.materialization.size_bytes)
        if raw != record.canonical_bytes():
            raise ValueError('scheduled prior publication changes exact original canonical bytes')


def authenticate_prior_publications(plane, config_inputs):
    """ROOT composes immediately after compile in public authoring and loading."""
    configs = tuple(v.record for v in config_inputs if type(v.record) is ScheduledCommitmentConfig)
    if not configs:
        return
    if len(configs) != 1:
        raise ValueError('scheduled inquiry requires one complete pre-access commitment')
    config = configs[0]
    for record, publication in ((config.reservation.allocation, config.reservation.publication),
            (config.specification.selection, config.specification.publication), (config.audit, config.audit_publication)):
        authenticate_publication(plane, publication, record)
    for publication in config.audit.prior_corpus:
        coordinate = next((c for c in (config.audit.census, *config.audit.prior_scheduled_coordinates) if
            c.SCHEMA == publication.logical.payload_schema and c.fingerprint() == publication.logical.content_sha256), None)
        authenticate_publication(plane, publication, coordinate)
    design = config.forecast_design
    for record, publication in ((design.model_record, design.model_publication),
            (design.training_record, design.training_publication), (design.criterion_record, design.criterion_publication)):
        authenticate_publication(plane, publication, record)
    if design.calibration is not None:
        # Hash custody only. Protected score access belongs to the existing
        # qualified-parent authenticator and sealed forecast worker.
        authenticate_publication(plane, design.calibration_publication)
    if config.response_selection is not None:
        authenticate_publication(plane, config.response_selection_publication, config.response_selection)
        for pub in config.response_selection.template_publications:
            authenticate_publication(plane, pub)


def require_publication_copy(record, port, publication):
    """Staged copies have their own physical IDs; original custody is separate."""
    if (port.artifact_id != publication.logical.logical_artifact_id
            or (port.payload_schema, port.media_type, port.size_bytes, port.outcome_access, port.visibility_ceiling) !=
               (publication.logical.payload_schema, publication.logical.media_type, publication.materialization.size_bytes,
                publication.logical.outcome_access, publication.logical.visibility_ceiling)
            or record.fingerprint() != publication.logical.content_sha256 or len(record.canonical_bytes()) != port.size_bytes):
        raise ValueError('scheduled staged copy changes original publication bytes or logical metadata')


class ScheduledCommitter:
    def __init__(self, manifest, budget):
        self.manifest, self.budget = manifest, budget

    def execute(self, context):
        try:
            if (type(context) is not TaskContext or context.task_id != COMMIT_KEY
                    or context.outcome_access is not OutcomeAccess.OUTCOME_BLIND
                    or context.permissions != self.manifest.permissions or not self.budget.contains(context.resource_budget)
                    or any(p.kind is not WorkerInputKind.EXTERNAL or p.outcome_access is not OutcomeAccess.OUTCOME_BLIND
                        or p.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE for p in context.input_ports)):
                raise ValueError('scheduled commitment requires exact original blind pre-access runtime context')
            classes = (ScheduledCommitmentConfig, ScheduledAllocation, ScheduledSelection, ScheduledExposureAudit,
                ScheduledSource, ScheduledForecastDesign, MatrixFactorExposureCensus, MatrixParameterCoordinate,
                MatrixResponseErrorModel, MatrixResponseErrorPredictionSpec, MatrixResponseFrontierProtocol, ScheduledResponseSelection)
            types, decoded = {t.SCHEMA: t for t in classes}, {t: [] for t in classes}
            for port in context.input_ports:
                cls = types.get(port.payload_schema)
                if cls is None:
                    raise ValueError('scheduled commitment receives undeclared source/outcome operands')
                decoded[cls].append((decode_canonical_bytes(port.read(), cls, maximum_bytes=None), port))
            if any(len(decoded[t]) != 1 for t in classes if t not in (ScheduledSource, MatrixParameterCoordinate, ScheduledResponseSelection)):
                raise ValueError('scheduled commitment omits exact configuration/publication/design census')
            config, port = decoded[ScheduledCommitmentConfig][0]
            selected_responses = decoded[ScheduledResponseSelection]
            if ((config.response_selection is None and selected_responses) or
                    config.response_selection is not None and (len(selected_responses) != 1 or selected_responses[0][0] != config.response_selection)):
                raise ValueError('scheduled commitment omits/substitutes actual frozen pulse/stream selection')
            if config.response_selection is not None:
                require_publication_copy(*selected_responses[0], config.response_selection_publication)
            if (context.config.config_id != config.config_id or context.config.config_schema != config.SCHEMA
                    or context.config.content_sha256 != config.fingerprint() or context.config.artifact_id != port.artifact_id
                    or tuple(sorted((r for r, _ in decoded[ScheduledSource]), key=lambda s: s.root_id)) != config.sources
                    or decoded[MatrixFactorExposureCensus][0][0] != config.audit.census
                    or tuple(sorted((r for r, _ in decoded[MatrixParameterCoordinate]), key=lambda c: c.coordinate_id)) != config.audit.prior_scheduled_coordinates
                    or decoded[ScheduledForecastDesign][0][0] != config.forecast_design):
                raise ValueError('scheduled commitment changes actual complete source/forecast/config bytes')
            for cls, record, pub in ((ScheduledAllocation, config.reservation.allocation, config.reservation.publication),
                    (ScheduledSelection, config.specification.selection, config.specification.publication),
                    (ScheduledExposureAudit, config.audit, config.audit_publication)):
                actual, staged = decoded[cls][0]
                if actual != record:
                    raise ValueError('scheduled commitment substitutes prior allocation/selection/audit')
                require_publication_copy(actual, staged, pub)
            for actual, staged in (*decoded[MatrixFactorExposureCensus], *decoded[MatrixParameterCoordinate]):
                pub = next(p for p in config.audit.prior_corpus if
                    (p.logical.payload_schema, p.logical.content_sha256) == (actual.SCHEMA, actual.fingerprint()))
                require_publication_copy(actual, staged, pub)
            design = config.forecast_design
            for cls, record, pub in ((MatrixResponseErrorModel, design.model_record, design.model_publication),
                    (MatrixResponseErrorPredictionSpec, design.training_record, design.training_publication),
                    (MatrixResponseFrontierProtocol, design.criterion_record, design.criterion_publication)):
                actual, staged = decoded[cls][0]
                if actual != record:
                    raise ValueError('scheduled commitment changes actual original frozen forecast operands')
                require_publication_copy(actual, staged, pub)
            value = committed(config)
            if (len(context.output_ports) != 1 or context.output_ports[0].output_id != COMMIT_KEY+'.product'
                    or context.output_ports[0].payload_schema != value.SCHEMA
                    or context.output_ports[0].profile is not ArtifactProfile.CANONICAL_JSON):
                raise ValueError('scheduled commitment changes exact ordinary freeze output')
            return RunnerResult((TaskOutputPayload(COMMIT_KEY+'.product', value.canonical_bytes()),),
                (ReceiptCheck('scheduled-original-prior-whole-population-commitment', True, ()),))
        finally:
            for port in context.input_ports:
                port.close()
