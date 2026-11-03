# SPDX-License-Identifier: MPL-2.0
"""Pure acknowledgment of the already published protected E1 selections.

This phase creates no allocation, scientific selection, qualification or
authority. Its ordinary receipt is the dependency before native acquisition.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.execution import RunnerResult, TaskContext, TaskOutputPayload, WorkerInputKind

from .records import E1AllocationReservation, E1FrozenSpecification, E1HistoryAllocation, E1HistorySource, E1ScientificSelection, identity

COMMIT_KEY = 'matrix-factor-confirmation.commit'


@dataclass(frozen=True, slots=True)
class E1CommitmentConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/commitment-config'
    config_id: str
    sources: tuple[E1HistorySource, ...]

    def __post_init__(self):
        if (self.config_id != 'config.'+COMMIT_KEY or not self.sources
                or any(type(s) is not E1HistorySource for s in self.sources)
                or tuple(s.root_id for s in self.sources) != tuple(r.root.root_id for r in self.sources[0].allocation.roots)
                or any(s.reservation != self.sources[0].reservation or s.specification != self.sources[0].specification for s in self.sources)):
            raise ValueError('E1 commitment requires the complete exact protected source population')


@dataclass(frozen=True, slots=True)
class E1Commitment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/commitment'
    commitment_id: str
    reservation: E1AllocationReservation
    specification: E1FrozenSpecification
    root_ids: tuple[str, ...]
    sources: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        if (self.commitment_id != 'commitment.'+COMMIT_KEY or type(self.reservation) is not E1AllocationReservation
                or type(self.specification) is not E1FrozenSpecification
                or self.specification.selection.reservation != identity(self.reservation)
                or self.root_ids != tuple(r.root.root_id for r in self.reservation.allocation.roots)
                or len(self.sources) != len(self.reservation.allocation.roots)
                or len({s.object_id for s in self.sources}) != len(self.sources)
                or any(s.object_schema != E1HistorySource.SCHEMA for s in self.sources)):
            raise ValueError('E1 commitment changes its prior publications or complete protected source census')

    def validate_source(self, source):
        if (type(source) is not E1HistorySource or source.reservation != self.reservation
                or source.specification != self.specification
                or self.sources[self.root_ids.index(source.root_id)] != identity(source)):
            raise ValueError('E1 native source differs from its receipted prior commitment')


def committed(config):
    return E1Commitment('commitment.'+COMMIT_KEY, config.sources[0].reservation,
        config.sources[0].specification, tuple(s.root_id for s in config.sources), tuple(identity(s) for s in config.sources))


def authenticate_prior_publications(plane, config_inputs):
    """Authenticate original E1 custody before authoring or reconstruction.

    Other operation families have no E1 publication operands. This check
    creates no qualification or authority and never stages a replacement.
    """
    configs = tuple(value.record for value in config_inputs if type(value.record) is E1CommitmentConfig)
    if not configs:
        return
    if len(configs) != 1:
        raise ValueError('E1 requires one complete protected prior commitment configuration')
    _authenticate_publications(plane, configs[0])


def _authenticate_publications(plane, config):
    from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
    from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
    first = config.sources[0]
    for record, publication in ((first.allocation, first.reservation.publication),
            (first.specification.selection, first.specification.publication)):
        relative = publication.materialization.relative_path
        sidecar_relative = relative+'.manifest.json'
        raw_manifest = read_bounded_bytes(plane.root.resolve(sidecar_relative, for_write=False),
            maximum_bytes=plane.custody_limits.manifest_bytes)
        expected_sidecar = plane._manifest_materialization(logical_artifact_id=publication.logical.logical_artifact_id,
            relative_path=sidecar_relative, payload=raw_manifest)
        if publication.manifest_materialization != expected_sidecar:
            raise ValueError('E1 prior publication changes original exact sidecar materialization identity')
        plane.verify(publication.manifest_materialization)
        manifest = decode_artifact_manifest(raw_manifest)
        if manifest.logical != publication.logical or manifest.materialization != publication.materialization:
            raise ValueError('E1 prior publication differs from original protected manifest custody')
        plane.verify_manifest(manifest)
        raw = read_bounded_bytes(plane.root.resolve(relative, for_write=False), maximum_bytes=publication.materialization.size_bytes)
        if raw != record.canonical_bytes():
            raise ValueError('E1 prior publication changes its exact original canonical scientific bytes')


def require_publication_copy(record, port, publication):
    """Join the verified staged bytes to their separately authenticated origin.

    Stock staging creates a new physical materialization. Its ordinary receipt
    retains that identity; the original publication stays in the commitment.
    """
    if (port.artifact_id != publication.logical.logical_artifact_id
            or port.payload_schema != publication.logical.payload_schema or port.media_type != publication.logical.media_type
            or port.size_bytes != publication.materialization.size_bytes
            or port.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE or port.outcome_access is not OutcomeAccess.OUTCOME_BLIND
            or record.fingerprint() != publication.logical.content_sha256
            or len(record.canonical_bytes()) != port.size_bytes):
        raise ValueError('E1 commitment staged input differs from exact prior publication bytes or metadata')


class E1Committer:
    def __init__(self, manifest, budget):
        self.manifest, self.budget = manifest, budget

    def execute(self, context):
        try:
            if (type(context) is not TaskContext or context.task_id != COMMIT_KEY
                    or context.outcome_access is not OutcomeAccess.OUTCOME_BLIND
                    or context.permissions != self.manifest.permissions or not self.budget.contains(context.resource_budget)
                    or any(p.kind is not WorkerInputKind.EXTERNAL or p.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
                        or p.outcome_access is not OutcomeAccess.OUTCOME_BLIND for p in context.input_ports)):
                raise ValueError('E1 commitment requires exact protected outcome-blind runtime context')
            decoded = {t: [] for t in (E1CommitmentConfig, E1HistoryAllocation, E1ScientificSelection, E1HistorySource)}
            types = {t.SCHEMA: t for t in decoded}
            for port in context.input_ports:
                cls = types.get(port.payload_schema)
                if cls is None:
                    raise ValueError('E1 commitment receives an undeclared scientific operand')
                decoded[cls].append((decode_canonical_bytes(port.read(), cls, maximum_bytes=None), port))
            if (len(decoded[E1CommitmentConfig]) != 1 or len(decoded[E1HistoryAllocation]) != 1
                    or len(decoded[E1ScientificSelection]) != 1):
                raise ValueError('E1 commitment omits its exact selected configuration and prior publications')
            config, config_port = decoded[E1CommitmentConfig][0]
            if (context.config.config_id != config.config_id or context.config.config_schema != config.SCHEMA
                    or context.config.content_sha256 != config.fingerprint() or context.config.artifact_id != config_port.artifact_id
                    or tuple(sorted((s for s, _ in decoded[E1HistorySource]), key=lambda s: s.root_id)) != config.sources):
                raise ValueError('E1 commitment changes its complete exact current source/configuration bytes')
            first = config.sources[0]
            for cls, expected, publication in ((E1HistoryAllocation, first.allocation, first.reservation.publication),
                    (E1ScientificSelection, first.specification.selection, first.specification.publication)):
                record, port = decoded[cls][0]
                if record != expected:
                    raise ValueError('E1 commitment substitutes the actual prior allocation or selection publication')
                require_publication_copy(record, port, publication)
            value = committed(config)
            if (len(context.output_ports) != 1 or context.output_ports[0].output_id != COMMIT_KEY+'.product'
                    or context.output_ports[0].payload_schema != value.SCHEMA
                    or context.output_ports[0].profile is not ArtifactProfile.CANONICAL_JSON
                    or context.output_ports[0].media_type != 'application/json'):
                raise ValueError('E1 commitment changes its exact ordinary output contract')
            return RunnerResult((TaskOutputPayload(COMMIT_KEY+'.product', value.canonical_bytes()),),
                (ReceiptCheck('e1-prior-protected-full-population-commitment', True, ()),))
        finally:
            for port in context.input_ports:
                port.close()
