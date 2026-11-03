# SPDX-License-Identifier: MPL-2.0
"""Caller-frozen whole-group pulse/noise scopes, distinct from source eligibility."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.kernel.matrix_inputs import MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS

from .records import NAMESPACE, ScheduledAllocation, ScheduledSource, identity
from .response_records import ScheduledResponsePanel, ScheduledResponseProtocol


@dataclass(frozen=True, slots=True)
class ScheduledCalibrationCriterion(CanonicalRecord):
    """Explicit construction/risk denominator conditions, not usefulness claims."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/calibration-criterion'
    VERSION: ClassVar[str] = '2.0.0'
    criterion_id: str
    independent_unit_id: str
    minimum_group_count: int
    maximum_nonfinite_group_fraction: Decimal
    required_family_ids: tuple[str, ...]
    construction_estimand: str

    def __post_init__(self):
        validate_stable_id(self.criterion_id); validate_stable_id(self.independent_unit_id)
        validate_decimal(self.maximum_nonfinite_group_fraction, field_name='explicit nonuse group allowance', minimum=Decimal(0))
        matched_relation = self.construction_estimand == 'WHOLE_GROUP_MAX_POSITIVE_PAIRED_LOG_RESIDUAL_NINE_COORDINATES_FACTOR58'
        if (type(self.minimum_group_count) is not int or self.minimum_group_count < 1 or self.maximum_nonfinite_group_fraction > 1
                or self.required_family_ids != tuple(sorted(set(self.required_family_ids)))
                or (bool(self.required_family_ids) if matched_relation else not self.required_family_ids)
                or not set(self.required_family_ids) <= set(FOUR_FAMILY_PREPARATION_IDS)
                or not matched_relation and self.construction_estimand not in (
                    'COMPLETE_MATCHED_GROUP_MAX_ALL15_POSITIVE_LOG_ERROR_MINUS_PRE_FUTURE_POINT_NONUSE_INFINITY',
                    'WHOLE_ROOT_MAX_POSITIVE_PAIRED_LOG_RESIDUAL_FACTOR58_NONUSE_INFINITY')):
            raise ValueError('scheduled calibration criterion omits explicit group/family/nonuse/construction conditions')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.criterion_id, self)


@dataclass(frozen=True, slots=True)
class ScheduledResponseSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/response-selection'
    VERSION: ClassVar[str] = '2.0.0'
    selection_id: str
    allocation: ObjectIdentity
    protocols: tuple[ScheduledResponseProtocol, ...]
    panels: tuple[tuple[str, tuple[ScheduledResponsePanel, ...]], ...]
    template_publications: tuple[ArtifactWriteResult, ...]
    calibration_criterion: ScheduledCalibrationCriterion | None

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        if (type(self.allocation) is not ObjectIdentity
                or (self.allocation.object_schema, self.allocation.object_version) !=
                   (ScheduledAllocation.SCHEMA, ScheduledAllocation.VERSION)):
            raise TypeError('scheduled response requires its exact shared allocation identity')
        self.allocation.__post_init__()
        roots = tuple(p.public_source.root.root_id for p in self.protocols)
        if not roots or roots != tuple(sorted(set(roots))) or any(type(p) is not ScheduledResponseProtocol for p in self.protocols):
            raise ValueError('scheduled pulse selection thins/aliases complete selected source protocols')
        groups = tuple(sorted({p.public_source.root.independent_group_id for p in self.protocols}))
        if tuple(g for g, _ in self.panels) != groups:
            raise ValueError('scheduled pulse selection drops complete matched-group future panels')
        owners = {}
        for group, panels in self.panels:
            if (tuple(p.panel_id for p in panels) != tuple(sorted({p.panel_id for p in panels}))
                    or tuple(sorted(p.role for p in panels)) != ('COMMON_NOISE_PANEL', 'INDEPENDENT_FUTURE')
                    or any(p.independent_group_id != group for p in panels)):
                raise ValueError('scheduled pulse selection changes complete original group/panel census')
            for panel in panels:
                for stream in panel.streams:
                    owner = (group, panel.role, stream.purpose)
                    if owners.setdefault(stream.effective_seed, owner) != owner:
                        raise ValueError('scheduled future effective stream crosses independent group/purpose ownership')
        for protocol in self.protocols:
            if protocol.public_source.allocation != self.allocation:
                raise ValueError('scheduled response protocol changes its shared allocation identity')
            # Complete48 branch archive plus all two-panel OU witnesses.
            h = protocol.horizon_steps[-1]
            if (24*((3*h+2)*2*96*16+3*h*96*16+(3*h+2)*24)+2*4*h*96*16+260*10000) > MAXIMUM_MATRIX_ARRAY_BYTES:
                raise ValueError('scheduled complete pulse archive exceeds unchanged bounded NPZ transport')
            pubs = tuple(p for p in self.template_publications if p.logical.logical_artifact_id == protocol.templates.array_artifact.artifact_id)
            if len(pubs) != 1:
                raise ValueError('scheduled response lacks its actual original template publication')
            p, a = pubs[0], protocol.templates.array_artifact
            if (p.logical.payload_schema, p.logical.content_sha256, p.logical.media_type, p.materialization.size_bytes,
                    p.logical.outcome_access, p.logical.visibility_ceiling) != (a.payload_schema, a.sha256, a.media_type,
                    a.size_bytes, protocol.templates.outcome_access, protocol.templates.visibility_ceiling):
                raise ValueError('scheduled response template differs from original complete fixed instrument')
        ids = tuple(p.logical.logical_artifact_id for p in self.template_publications)
        if ids != tuple(sorted(set(ids))) or set(ids) != {p.templates.array_artifact.artifact_id for p in self.protocols}:
            raise ValueError('scheduled response aliases or extends original template publication census')
        calibration = {p.public_source.root.role.value == 'CALIBRATION' for p in self.protocols}
        if True in calibration and (calibration != {True} or type(self.calibration_criterion) is not ScheduledCalibrationCriterion):
            raise ValueError('scheduled calibration pulse bank lacks frozen construction criterion or mixes roles')

    def validate_allocation(self, allocation):
        """Validate the complete roster against its actual shared parent.

        Publication/access owners authenticate this allocation before scientific
        use. The selection's pin never supplies that custody or permission.
        """
        self.__post_init__()
        if type(allocation) is not ScheduledAllocation:
            raise TypeError('scheduled response needs its actual shared allocation')
        allocation.__post_init__()
        if self.allocation != identity(allocation):
            raise ValueError('scheduled response substitutes its exact shared allocation')
        allocation_roots = {r.root.root_id: r for r in allocation.roots}
        exposed = set(allocation.exposure.census.effective_seed_exclusions)
        history_seeds = {s.effective_seed for r in allocation.roots for s in r.streams}
        excluded_seeds = exposed | history_seeds
        roots_by_group, protocols_by_group = {}, {}
        for row in allocation.roots:
            roots_by_group.setdefault(row.root.independent_group_id, []).append(row)
        for protocol in self.protocols:
            protocols_by_group.setdefault(protocol.public_source.root.independent_group_id, []).append(protocol)
        coordinates_by_id = {coordinate.coordinate_id: coordinate for coordinate in allocation.coordinates}
        for group, panels in self.panels:
            rows = roots_by_group.get(group, ())
            if {r.root.root_id for r in rows} != {p.public_source.root.root_id for p in protocols_by_group.get(group, ())}:
                raise ValueError('scheduled pulse selection omits a coordinate case of one independent group')
            for panel in panels:
                if panel.role == 'COMMON_NOISE_PANEL' and any(panel.streams != r.streams for r in rows):
                    raise ValueError('scheduled common panel differs from original paired history streams')
                if panel.role == 'INDEPENDENT_FUTURE' and any(stream.effective_seed in excluded_seeds for stream in panel.streams):
                    raise ValueError('scheduled independent future reuses known exposed/history effective noise')
        for protocol in self.protocols:
            public = protocol.public_source
            row = allocation_roots.get(public.root.root_id)
            if row is None or public.root != row.root or public.coordinate != coordinates_by_id.get(row.root.coordinate_id):
                raise ValueError('scheduled response protocol changes original role/physical coordinate/allocation')
        for scope in allocation.matched_scopes:
            groups = set(scope.independent_group_ids)
            values = tuple(p for p in self.protocols if p.public_source.root.independent_group_id in groups)
            if values:
                def assay(p):
                    return (p.actions, p.horizon_steps, p.receiver_count, p.templates.array_artifact.sha256,
                        p.hessian_difference_step, p.generic_gap_minimum, p.spectral_gap_minimum, p.radial_norm_minimum,
                        p.complement_gram_minimum, p.native_reference_tolerance, p.hessian_reference_tolerance,
                        p.weak_response_minimum, p.receiver_gram_tolerance, p.origin_rule)
                if any(assay(p) != assay(values[0]) for p in values):
                    raise ValueError('matched scheduled coordinates substitute physical query/instrument/numerical policy')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.selection_id, self)

    def validate_source(self, source):
        """Local join after the owning consumer validates the shared allocation."""
        rows = tuple(p for p in self.protocols if p.public_source.root.root_id == source.root_id)
        if self.allocation != source.index.allocation_identity or len(rows) != 1:
            raise ValueError('scheduled response source is outside its exact committed selected population')
        rows[0].public_source.validate_source(source)
        return rows[0], dict(self.panels)[source.root.root.independent_group_id]


@dataclass(frozen=True, slots=True)
class ScheduledPhysicalForecastConfig(CanonicalRecord):
    """Public instrument/physical operands only; no private response selection."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/physical-forecast-config'
    config_id: str
    protocol: ScheduledResponseProtocol

    def __post_init__(self):
        if self.config_id != 'config.'+NAMESPACE+'.'+self.protocol.public_source.root.root_id+'.physical-forecast':
            raise ValueError('scheduled physical predictor changes its exact public configuration')

    @property
    def root_id(self):
        return self.protocol.public_source.root.root_id


@dataclass(frozen=True, slots=True)
class ScheduledResponseConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/response-config'
    VERSION: ClassVar[str] = '2.0.0'
    config_id: str
    operation: str
    source: ScheduledSource
    selection: ObjectIdentity
    commitment_config: ObjectIdentity

    def __post_init__(self):
        from .commitment import ScheduledCommitmentConfig
        from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
        if type(self.source) is not ScheduledSource:
            raise TypeError('scheduled response requires its current bounded source reference')
        suffix = '-development' if self.source.root.root.role is MatrixProgrammeRole.DEVELOPMENT else ''
        if (type(self.selection) is not ObjectIdentity or type(self.commitment_config) is not ObjectIdentity
                or (self.selection.object_schema, self.selection.object_version) !=
                   (ScheduledResponseSelection.SCHEMA, ScheduledResponseSelection.VERSION)
                or self.commitment_config.object_schema != ScheduledCommitmentConfig.SCHEMA
                or self.commitment_config.object_version != ScheduledCommitmentConfig.VERSION
                or self.operation not in ('responses'+suffix, 'response-score'+suffix)
                or self.config_id != 'config.'+NAMESPACE+'.'+self.source.root_id+'.'+self.operation):
            raise ValueError('scheduled response changes exact native/independent role/access configuration')
        self.source.__post_init__()
        self.selection.__post_init__()
        self.commitment_config.__post_init__()

    @property
    def root_id(self):
        return self.source.root_id
