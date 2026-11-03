# SPDX-License-Identifier: MPL-2.0
"""Fresh DEVELOPMENT/TRAIN acquisition and truthful complete native banks.

These immutable operands create no issue, freshness, sampling qualification or
outcome authority. Existing publication and native receipt owners establish
custody. Acquisition never needs a fitted response-error predictor.
"""
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import exposure_support as current_exposure_support
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import (
    MatrixProgrammeInputCommitments, MatrixProgrammePublishedInput,
)
from bisect import bisect_left
from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity as scheduled_identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponsePanel, ScheduledResponseProtocol
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import validate_record_fields
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding
from empirical_lawhood.kernel.serialization import (CanonicalRecord, require_sorted_unique_ids,
    require_sorted_unique_strings, validate_decimal, validate_sha256, validate_stable_id)
from empirical_lawhood.planning.campaigns import CampaignSpec
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
from .configured_protected_specification import ConfiguredProtectedE3Specification
from .configured_specification import ConfiguredE3Measurement
from .experiment_methods import MatrixE3ViewOutcome, STANDING
from .protected_source_records import ProtectedE3NativeSourceManifest
from .response_error_prediction import FEATURES, FEATURE_DISPOSITIONS
from .response_frontier import MatrixResponseFrontierProtocol
from .matched_response_prediction import MatchedResponseViewOutcome, validate_matched_features
from .origin_mechanics import MatrixOriginResponseModel

PHASES = ("prefix", "numerical", "measure", "check", "project", "physical-forecast", "feature", "responses", "response-score")
ALL_PHASES = tuple(sorted((*PHASES, "entry", "terminal")))
NAMESPACE = "matrix-native-training-v1"


def identity(record):
    for name in ("record_id", "specification_id", "protocol_id", "panel_id"):
        if hasattr(record, name):
            return ObjectIdentity.from_record(getattr(record, name), record)
    return scheduled_identity(record)


class _Identity:
    __slots__ = ()

    @property
    def identity(self):
        return identity(self)


def native_source_pins(source):
    """Exact compact direct operands; never a per-root full allocation copy."""
    return (source.reference.identity,
        coordinate_identity(source.coordinate), source.provenance.identity)


def exact_reference(value, kind):
    if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
        raise ValueError("native TRAIN substitutes an exact immutable type or revision")
    validate_record_fields(value)


@dataclass(frozen=True, slots=True)
class NativeTrainingAcquisitionSpecification(_Identity, CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/native-training-acquisition-specification"
    specification_id: str
    measurement: ConfiguredE3Measurement
    root_ids: tuple[str, ...]
    future_reservation: ObjectIdentity
    candidate: ObjectIdentity

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledReservation
        validate_stable_id(self.specification_id)
        if type(self.measurement) is not ConfiguredE3Measurement:
            raise TypeError("native TRAIN requires its explicitly selected existing measurement")
        validate_record_fields(self.measurement)
        require_sorted_unique_strings(self.root_ids, field_name="all assigned native TRAIN roots", allow_empty=False)
        exact_reference(self.future_reservation, ScheduledReservation)
        exact_reference(self.candidate, ConfiguredProtectedE3Specification)


@dataclass(frozen=True, slots=True)
class NativeTrainingResources(_Identity, CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/native-training-resources"
    record_id: str
    budgets: tuple[tuple[str, ResourceBudget], ...]
    maximum_parallel_tasks: int

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.budgets) is not tuple or tuple(name for name, _ in self.budgets) != ALL_PHASES
                or any(type(budget) is not ResourceBudget for _, budget in self.budgets)
                or type(self.maximum_parallel_tasks) is not int or self.maximum_parallel_tasks < 1):
            raise ValueError("native TRAIN needs exact explicit phase budgets and parallel placement")
        for _, budget in self.budgets:
            validate_record_fields(budget)
            if budget.cpu_cores != 1 or budget.gpu_devices != 0:
                raise ValueError("native TRAIN task budgets require one numerical worker per task")

    def for_operation(self, operation):
        return dict(self.budgets)[operation]


@dataclass(frozen=True, slots=True)
class NativeTrainingAcquisitionRequest(_Identity, CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/native-training-acquisition-request"
    VERSION: ClassVar[str] = '3.0.0'
    record_id: str
    train_manifest: ProtectedE3NativeSourceManifest
    future_manifest: ProtectedE3NativeSourceManifest
    candidate_specification: ConfiguredProtectedE3Specification
    sources: tuple[ScheduledSource, ...]
    protocols: tuple[ScheduledResponseProtocol, ...]
    panels: tuple[ScheduledResponsePanel, ...]
    mathematical_protocol: MatrixResponseFrontierProtocol
    template_publications: tuple[ArtifactWriteResult, ...]
    exposure_support: tuple[tuple[ArtifactIdentity, ArtifactWriteResult | ExperimentFileInputBinding], ...]
    campaign: CampaignSpec
    resources: NativeTrainingResources
    input_commitments: MatrixProgrammePublishedInput

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.input_commitments) is not MatrixProgrammePublishedInput:
            raise TypeError("native TRAIN requires its actual complete pre-acquisition programme commitment")
        validate_record_fields(self.input_commitments)
        self.input_commitments.require_kind(MatrixProgrammeInputCommitments)
        for value, kind in ((self.train_manifest, ProtectedE3NativeSourceManifest),
                (self.future_manifest, ProtectedE3NativeSourceManifest),
                (self.candidate_specification, ConfiguredProtectedE3Specification),
                (self.mathematical_protocol, MatrixResponseFrontierProtocol), (self.campaign, CampaignSpec),
                (self.resources, NativeTrainingResources)):
            if type(value) is not kind:
                raise TypeError("native TRAIN request changes its exact explicit scientific operands")
            validate_record_fields(value)
        for values, kind, key in ((self.sources, ScheduledSource, "root_id"),
                (self.protocols, ScheduledResponseProtocol, None), (self.panels, ScheduledResponsePanel, "panel_id")):
            if type(values) is not tuple or not values or any(type(value) is not kind for value in values):
                raise TypeError("native TRAIN request requires complete typed source/protocol/panel tuples")
            for value in values:
                validate_record_fields(value)
            names = tuple(getattr(value, key) if key else value.public_source.root.root_id for value in values)
            if names != tuple(sorted(set(names))):
                raise ValueError("native TRAIN request duplicates or reorders original roots/panels")
        if (type(self.template_publications) is not tuple or not self.template_publications
                or any(type(value) is not ArtifactWriteResult for value in self.template_publications)
                or tuple(value.logical.logical_artifact_id for value in self.template_publications) !=
                   tuple(sorted({value.logical.logical_artifact_id for value in self.template_publications}))):
            raise ValueError("native TRAIN requires exact unique original template publications")



def future_response_support(request):
    """Exact mandatory pre-TRAIN programme and future custody, not freshness."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledResponseSelection
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.e6_transport_records import MatrixE6EmpiricalTransportPolicy
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.kernel.time import AvailabilitySpec
    from empirical_lawhood.runtime.artifacts import ArtifactProfile
    required = {artifact for manifest in (request.train_manifest, request.future_manifest)
        for artifact, _ in current_exposure_support(manifest.audit)}
    if (type(request.exposure_support) is not tuple
            or tuple(value.artifact_id for value, _ in request.exposure_support) !=
                tuple(sorted({value.artifact_id for value, _ in request.exposure_support}))):
        raise ValueError("native TRAIN repeats or reorders actual supporting publication custody")
    if not required.issubset({artifact for artifact, _ in request.exposure_support}):
        raise ValueError("native TRAIN omits actual required current exposure census support")
    extras = tuple((artifact, custody) for artifact, custody in request.exposure_support if artifact not in required)
    state = request.campaign.evidence_state
    selectors = tuple(value for value in state if value.object_schema == ScheduledResponseSelection.SCHEMA)
    clocks = tuple(value for value in state if value.object_schema == AvailabilitySpec.SCHEMA)
    policies = tuple(value for value in state if value.object_schema == MatrixE6EmpiricalTransportPolicy.SCHEMA)
    commitments = tuple(value for value in state if value.object_schema == MatrixProgrammeInputCommitments.SCHEMA)
    roles = tuple(value.role for value in request.candidate_specification.populations if value.role != "TRAIN")
    if (len(selectors) != len(roles) or len(clocks) != 1 or len(policies) != 1
            or commitments != (request.input_commitments.record,)
            or len(state) != len(roles) + 3
            or len(extras) != len(state)
            or any(value.object_version != ScheduledResponseSelection.VERSION for value in selectors)
            or clocks[0].object_version != AvailabilitySpec.VERSION
            or any(value.object_version != MatrixE6EmpiricalTransportPolicy.VERSION for value in policies)):
        raise ValueError("native TRAIN must commit the whole programme, every future selection, actual availability and E6 policy exactly once")
    rows = []
    for reference in state:
        matches = tuple((artifact, custody) for artifact, custody in extras
            if (artifact.payload_schema, artifact.sha256) == (reference.object_schema, reference.object_fingerprint))
        if len(matches) != 1:
            raise ValueError("native TRAIN omits exact canonical future selection/availability custody")
        artifact, publication = matches[0]
        if (type(artifact) is not ArtifactIdentity or type(publication) is not ArtifactWriteResult
                or artifact.media_type != "application/json" or artifact.size_bytes < 1
                or publication.logical.profile is not ArtifactProfile.CANONICAL_JSON
                or publication.logical.outcome_access is not OutcomeAccess.OUTCOME_BLIND
                or publication.logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
                or publication.materialization.compression != "none"):
            raise ValueError("native TRAIN future commitments require actual blind canonical publications, not FILE copies")
        if reference.object_schema == AvailabilitySpec.SCHEMA and reference.object_id != artifact.artifact_id:
            raise ValueError("native TRAIN substitutes the exact actual availability publication identity")
        if reference == request.input_commitments.record and publication != request.input_commitments.publication:
            raise ValueError("native TRAIN substitutes its actual complete original programme commitment publication")
        rows.append((reference, artifact, publication))
    if len({artifact for _, artifact, _ in rows}) != len(rows):
        raise ValueError("native TRAIN aliases different future commitments through one artifact")
    limit = request.resources.for_operation("entry").source_scan_bytes
    if limit is not None and sum(artifact.size_bytes for _, artifact, _ in rows) > limit:
        raise ValueError("native TRAIN future commitment reads exceed the selected entry source byte budget")
    return tuple(rows)


def validate_future_response_selections(request, selections, availability):
    """Complete pre-TRAIN future role/panel partition through existing contracts."""
    from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledResponseSelection
    from empirical_lawhood.kernel.evidence import OutcomeAccess
    from empirical_lawhood.kernel.time import AvailabilitySpec, CausalPhase
    support = future_response_support(request)
    references = {reference for reference, _, _ in support if reference.object_schema == ScheduledResponseSelection.SCHEMA}
    if (type(selections) is not tuple or any(type(value) is not ScheduledResponseSelection for value in selections)
            or len(selections) != len(references) or {value.identity for value in selections} != references
            or type(availability) is not AvailabilitySpec):
        raise ValueError("native TRAIN substitutes or omits a complete actual future selection")
    validate_record_fields(availability)
    clock, = (reference for reference, _, _ in support if reference.object_schema == AvailabilitySpec.SCHEMA)
    if (ObjectIdentity.from_record(clock.object_id, availability) != clock
            or availability.phase is not CausalPhase.PREPARATION
            or availability.outcome_access is not OutcomeAccess.OUTCOME_BLIND or availability.available_at is None
            or availability.available_at < 0):
        raise ValueError("native TRAIN future commits lack their actual pinned pre-acquisition availability")
    future = request.future_manifest.reservation.allocation
    role_coordinates = dict(request.candidate_specification.role_coordinates)
    role_kinds = {"CALIBRATION": MatrixProgrammeRole.CALIBRATION, "EVALUATION": MatrixProgrammeRole.CONFIRMATION,
        "TRANSFER_NEARBY": MatrixProgrammeRole.WITHHELD_TRANSFER, "TRANSFER_SHIFTED": MatrixProgrammeRole.WITHHELD_TRANSFER}
    assigned = {role: tuple(value for value in future.roots
        if value.coordinate == role_coordinates[role] and value.root.role is kind) for role, kind in role_kinds.items()}
    if {value.root.root_id for roots in assigned.values() for value in roots} != {value.root.root_id for value in future.roots}:
        raise ValueError("native TRAIN future response commitments omit an original reserved root")
    train_groups = {value.root.independent_group_id for value in request.train_manifest.reservation.allocation.roots}
    forbidden = {stream.effective_seed for manifest in (request.train_manifest, request.future_manifest)
        for root in manifest.reservation.allocation.roots for stream in root.streams}
    forbidden.update(stream.effective_seed for panel in request.panels for stream in panel.streams)
    forbidden.update(seed for manifest in (request.train_manifest, request.future_manifest)
        for seed in manifest.audit.census.effective_seed_exclusions)
    index = ScheduledSourceIndex.from_shared(reservation=request.future_manifest.reservation,
        specification=request.future_manifest.native_specification, provenances=request.future_manifest.provenances)
    owners, selected_roles, output = {}, set(), []
    for selection in selections:
        selection.validate_allocation(future)
        roots = {value.public_source.root.root_id for value in selection.protocols}
        matches = tuple(role for role, values in assigned.items() if roots == {value.root.root_id for value in values})
        if len(matches) != 1 or matches[0] in selected_roles:
            raise ValueError("native TRAIN future response selection substitutes its exact original role/allocation")
        role, = matches
        selected_roles.add(role)
        groups = {value.root.independent_group_id for value in assigned[role]}
        population = request.candidate_specification.population(role)
        if (len(assigned[role]) != len(groups) or len(groups) != population.expected_units
                or population.unit_ids is not None and groups != set(population.unit_ids)
                or groups.intersection(train_groups) or {group for group, _ in selection.panels} != groups):
            raise ValueError("native TRAIN future response selection thins complete independent role groups")
        for protocol in selection.protocols:
            public = protocol.public_source
            sources = tuple(index.resolve(index.reference(source_id=public.source.object_id,
                root_id=public.root.root_id, provenance=provenance.identity))
                for provenance in request.future_manifest.provenances)
            matches = tuple(value for value in sources if scheduled_identity(value) == public.source)
            if len(matches) != 1 or coordinate_identity(public.coordinate) != role_coordinates[role]:
                raise ValueError("native TRAIN future response protocol substitutes original source/provenance/coordinate")
            public.validate_source(matches[0])
            from .response_frontier import MatrixResponseActionScale
            scales = tuple(sorted((MatrixResponseActionScale(value.role, value.amplitude, value.force_norm, value.pulse_steps)
                for value in protocol.actions), key=lambda value: value.role))
            measurement = request.candidate_specification.measurement
            if (protocol.criterion != request.mathematical_protocol.identity
                    or measurement.is_matched != (type(protocol.mechanical_model) is MatrixOriginResponseModel)
                    or protocol.horizon_steps != measurement.horizons or protocol.receiver_count != measurement.receiver_count
                    or scales != request.mathematical_protocol.action_scales
                    or protocol.receiver_gram_tolerance != request.mathematical_protocol.receiver_gram_tolerance
                    or public.coordinate.primary_view.timestep != measurement.primary_timestep
                    or public.coordinate.fine_view.timestep != measurement.fine_timestep
                    or public.policy.cutoff_tick != measurement.origin_tick
                    or population.family_id is not None and public.coordinate.family_id != population.family_id):
                raise ValueError("native TRAIN future response selection changes the declared scientific target/menu")
        for group, panels in selection.panels:
            for panel in panels:
                if panel.role != "INDEPENDENT_FUTURE":
                    continue
                for stream in panel.streams:
                    owner = role, group, stream.purpose
                    if stream.effective_seed in forbidden or owners.setdefault(stream.effective_seed, owner) != owner:
                        raise ValueError("native TRAIN reserved future panel overlaps TRAIN, history, prior exposure or another role")
        output.append((role, selection))
    if selected_roles != set(role_kinds):
        raise ValueError("native TRAIN future response commitments omit a configured role")
    return tuple(sorted(output))

def source_for(request, root_id, *, index):
    position = bisect_left(request.sources, root_id, key=lambda value: value.root_id)
    if position == len(request.sources) or request.sources[position].root_id != root_id:
        raise ValueError("native TRAIN selects an unassigned root")
    return index.resolve(request.sources[position])


def panels_for(request, source):
    selected = tuple(value for value in request.panels if value.independent_group_id == source.root.root.independent_group_id)
    if tuple(sorted(value.role for value in selected)) != ("COMMON_NOISE_PANEL", "INDEPENDENT_FUTURE"):
        raise ValueError("native TRAIN requires both actual future panels for every whole group")
    return selected


def validate_request(specification, request):
    if type(specification) is not NativeTrainingAcquisitionSpecification or type(request) is not NativeTrainingAcquisitionRequest:
        raise TypeError("native TRAIN requires its exact declared specification and request")
    validate_record_fields(specification); validate_record_fields(request)
    train, future = request.train_manifest.reservation, request.future_manifest.reservation
    candidate, measurement = request.candidate_specification, specification.measurement
    if (candidate.identity != specification.candidate or candidate.measurement != measurement
            or scheduled_identity(future) != specification.future_reservation
            or tuple(value.root_id for value in request.sources) != specification.root_ids
            or tuple(value.public_source.root.root_id for value in request.protocols) != specification.root_ids
            or tuple(value.root.root_id for value in train.allocation.roots) != specification.root_ids
            or any(value.root.role is not MatrixProgrammeRole.DEVELOPMENT for value in train.allocation.roots)
            or candidate.population("TRAIN").expected_units != len(specification.root_ids)):
        raise ValueError("native TRAIN substitutes candidate, complete DEVELOPMENT roots or prior future reservation")
    train_groups = {value.root.independent_group_id for value in train.allocation.roots}
    future_groups = {value.root.independent_group_id for value in future.allocation.roots}
    train_seeds = {value.effective_seed for root in train.allocation.roots for value in root.streams}
    future_seeds = {value.effective_seed for root in future.allocation.roots for value in root.streams}
    known_groups = set(train.allocation.exposure.census.exposed_independent_groups) | set(future.allocation.exposure.census.exposed_independent_groups)
    known_seeds = set(train.allocation.exposure.census.effective_seed_exclusions) | set(future.allocation.exposure.census.effective_seed_exclusions)
    if (len(train_groups) != len(specification.root_ids) or train_groups & future_groups or train_seeds & future_seeds
            or train_groups & known_groups or train_seeds & known_seeds):
        raise ValueError("native TRAIN overlaps independent future groups or effective streams")
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledResponseSelection
    ScheduledResponseSelection("response-selection." + request.record_id, ObjectIdentity.from_record(train.allocation.allocation_id, train.allocation), request.protocols,
        tuple(sorted((group, tuple(value for value in request.panels if value.independent_group_id == group))
            for group in train_groups)), request.template_publications, None).validate_allocation(train.allocation)
    required_support = {artifact for manifest in (request.train_manifest, request.future_manifest)
        for artifact, _ in current_exposure_support(manifest.audit)}
    required_support.update(artifact for _, artifact, _ in future_response_support(request))
    if (type(request.exposure_support) is not tuple
            or tuple(value.artifact_id for value, _ in request.exposure_support) !=
               tuple(sorted({value.artifact_id for value, _ in request.exposure_support}))
            or {value for value, _ in request.exposure_support} != required_support):
        raise ValueError("native TRAIN omits actual complete train/future current exposure census custody")
    for artifact, custody in request.exposure_support:
        if type(artifact) is not ArtifactIdentity or type(custody) not in (ArtifactWriteResult, ExperimentFileInputBinding):
            raise TypeError("native TRAIN exposure support requires actual exact publication or FILE custody")
        validate_record_fields(artifact); validate_record_fields(custody)
        if type(custody) is ExperimentFileInputBinding:
            if custody.identity != artifact:
                raise ValueError("native TRAIN exposure FILE substitutes original exact bytes")
        elif (custody.logical.logical_artifact_id, custody.logical.payload_schema, custody.logical.media_type,
                custody.logical.content_sha256, custody.materialization.physical_sha256, custody.materialization.size_bytes) != (
                artifact.artifact_id, artifact.payload_schema, artifact.media_type, artifact.sha256, artifact.sha256, artifact.size_bytes):
            raise ValueError("native TRAIN exposure publication substitutes actual current census bytes")
    template_rows = {value.logical.logical_artifact_id: value for value in request.template_publications}
    actual_templates = set()
    expected_panels = set()
    from .response_frontier import MatrixResponseActionScale
    from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
    index = ScheduledSourceIndex.from_shared(reservation=request.train_manifest.reservation,
        specification=request.train_manifest.native_specification, provenances=request.train_manifest.provenances)
    index.require_roster(request.sources, expected_root_ids=index.root_ids)
    excluded_panel_seeds = train_seeds | future_seeds | known_seeds
    for descriptor, protocol in zip(request.sources, request.protocols, strict=True):
        source = source_for(request, descriptor.root_id, index=index)
        protocol.public_source.validate_source(source)
        panels = panels_for(request, source)
        expected_panels.update(value.panel_id for value in panels)
        for panel in panels:
            if panel.role == "COMMON_NOISE_PANEL" and panel.streams != source.root.streams:
                raise ValueError("native TRAIN common panel differs from actual source streams")
            if panel.role == "INDEPENDENT_FUTURE" and any(stream.effective_seed in excluded_panel_seeds for stream in panel.streams):
                raise ValueError("native TRAIN future panel reuses a native source/future stream")
        scales = tuple(sorted((MatrixResponseActionScale(value.role, value.amplitude, value.force_norm, value.pulse_steps)
            for value in protocol.actions), key=lambda value: value.role))
        if (coordinate_identity(source.coordinate) != dict(candidate.role_coordinates)["TRAIN"]
                or measurement.is_matched != (type(protocol.mechanical_model) is MatrixOriginResponseModel)
                or source.policy.cutoff_tick != measurement.origin_tick or source.policy.origin_sector != "Y"
                or source.coordinate.primary_view.timestep != measurement.primary_timestep
                or source.coordinate.fine_view.timestep != measurement.fine_timestep
                or protocol.horizon_steps != measurement.horizons or protocol.receiver_count != measurement.receiver_count
                or protocol.criterion != request.mathematical_protocol.identity
                or protocol.horizon_steps != request.mathematical_protocol.horizon_steps
                or scales != request.mathematical_protocol.action_scales
                or protocol.receiver_gram_tolerance != request.mathematical_protocol.receiver_gram_tolerance):
            raise ValueError("native TRAIN changes its exact physical coordinate, cutoff, paired assay or numerical protocol")
        artifact = protocol.templates.array_artifact
        pub = template_rows.get(artifact.artifact_id)
        if (pub is None or (pub.logical.payload_schema, pub.logical.media_type, pub.logical.content_sha256,
                pub.materialization.physical_sha256, pub.materialization.size_bytes) !=
                (artifact.payload_schema, artifact.media_type, artifact.sha256, artifact.sha256, artifact.size_bytes)):
            raise ValueError("native TRAIN templates lose original exact-byte publication")
        actual_templates.add(artifact.artifact_id)
    if expected_panels != {value.panel_id for value in request.panels} or actual_templates != set(template_rows):
        raise ValueError("native TRAIN request adds or omits original panels/templates")
    seeds = tuple(stream.effective_seed for value in request.panels if value.role == "INDEPENDENT_FUTURE" for stream in value.streams)
    if len(seeds) != len(set(seeds)):
        raise ValueError("native TRAIN independent future panels reuse effective streams")
    # Reuse the existing complete protected source projection before the first
    # TRAIN acquisition, rather than discover a bad future reserve at fitting.
    from .configured_protected_inputs import ConfiguredProtectedE3SourceInputs, project_protected_e3_allocation
    from .configured_specification import ConfiguredE3CoordinateCensus
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import physical_key
    coordinates = {coordinate_identity(value): value for value in future.allocation.coordinates}
    role_coordinates = dict(candidate.role_coordinates)
    if any(role_coordinates[role] not in coordinates for role in ("CALIBRATION", "EVALUATION", "TRANSFER_NEARBY", "TRANSFER_SHIFTED")):
        raise ValueError("native TRAIN future reservation omits an actual selected physical coordinate")
    training = _training_allocation(specification, request)
    census = ConfiguredE3CoordinateCensus("coordinates." + specification.specification_id,
        tuple(sorted((value.public_source.root.independent_group_id, value.public_source.source,
            coordinate_identity(value.public_source.coordinate)) for value in request.protocols)))
    future_inputs = ConfiguredProtectedE3SourceInputs(candidate, training, future,
        request.future_manifest.native_specification, coordinates[role_coordinates["CALIBRATION"]],
        coordinates[role_coordinates["TRANSFER_NEARBY"]], coordinates[role_coordinates["TRANSFER_SHIFTED"]], census)
    project_protected_e3_allocation(future_inputs)
    train_physical = {physical_key(value) for value in train.allocation.coordinates}
    withheld = {root.root.coordinate_id for root in future.allocation.roots if root.root.role is MatrixProgrammeRole.WITHHELD_TRANSFER}
    if any(value.coordinate_id in withheld and physical_key(value) in train_physical for value in future.allocation.coordinates):
        raise ValueError("native TRAIN overlaps a withheld future physical regime under another label")


def training_allocation(specification, request):
    validate_request(specification, request)
    return _training_allocation(specification, request)


def _training_allocation(specification, request):
    units = tuple(sorted((IndependentUnit(value.public_source.root.independent_group_id, request.record_id,
        value.public_source.coordinate.family_id, ("fine", "primary"), True) for value in request.protocols),
        key=lambda value: value.unit_id))
    return UnitAllocation("allocation." + specification.specification_id, (request.identity,), units,
        tuple(UnitRoleAssignment(value.unit_id, "train") for value in units))


@dataclass(frozen=True, slots=True)
class NativeTrainingAcquisitionSeal(_Identity, CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/native-training-acquisition-seal"
    record_id: str
    specification: ObjectIdentity
    request: ObjectIdentity
    train_reservation: ObjectIdentity
    future_reservation: ObjectIdentity
    allocation: ObjectIdentity
    candidate: ObjectIdentity

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledReservation
        validate_stable_id(self.record_id)
        for value, kind in ((self.specification, NativeTrainingAcquisitionSpecification),
                (self.request, NativeTrainingAcquisitionRequest), (self.train_reservation, ScheduledReservation),
                (self.future_reservation, ScheduledReservation), (self.allocation, UnitAllocation),
                (self.candidate, ConfiguredProtectedE3Specification)):
            exact_reference(value, kind)


def acquisition_seal(specification, request):
    allocation = training_allocation(specification, request)
    return NativeTrainingAcquisitionSeal("seal." + specification.specification_id, specification.identity, request.identity,
        scheduled_identity(request.train_manifest.reservation), specification.future_reservation, allocation.identity, specification.candidate)


@dataclass(frozen=True, slots=True)
class NativeTrainingFeature(_Identity, CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/native-training-feature"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    unit_id: str
    source_manifest: ObjectIdentity
    native_source: ObjectIdentity
    origin: ObjectIdentity
    clock_id: str
    cutoff: Decimal
    frame_sha256: str | None
    disposition: str
    values: tuple[tuple[str, Decimal], ...]
    evidence: tuple[ObjectIdentity, ...]
    standing: str = STANDING
    physical_forecast: ObjectIdentity | None = None
    fine_response_defect: Decimal | None = None

    def __post_init__(self):
        for value in (self.record_id, self.unit_id, self.clock_id):
            validate_stable_id(value)
        for value, kind in ((self.source_manifest, NativeTrainingAcquisitionRequest), (self.native_source, ScheduledSource),
                (self.origin, NativeTrainingCausalPrefix)):
            exact_reference(value, kind)
        validate_decimal(self.cutoff, field_name="actual native TRAIN cutoff", minimum=Decimal(0))
        if self.frame_sha256 is not None:
            validate_sha256(self.frame_sha256)
        require_sorted_unique_ids(self.evidence, attribute="object_id", field_name="native TRAIN feature evidence")
        if (self.disposition not in FEATURE_DISPOSITIONS or not self.evidence or self.standing != STANDING
                or self.physical_forecast is None and (tuple(name for name, _ in self.values) != FEATURES
                    if self.disposition == "AVAILABLE" else bool(self.values))
                or self.disposition == "AVAILABLE" and (self.frame_sha256 is None or dict(self.values)["cutoff"] != self.cutoff)):
            raise ValueError("native TRAIN feature manufactures values/frame after original nonuse")
        if self.physical_forecast is None:
            if self.fine_response_defect is not None:
                raise ValueError('native TRAIN defect diagnostic lacks its mechanical parent')
            for _, value in self.values:
                validate_decimal(value, field_name="native causal feature", minimum=Decimal(0))
        else:
            exact_reference(self.physical_forecast, NativeTrainingPhysicalForecast)
            if self.physical_forecast not in self.evidence:
                raise ValueError('matched TRAIN feature omits its original pre-future mechanical parent')
            validate_matched_features(self.values, self.disposition)
            if self.fine_response_defect is not None:
                validate_decimal(self.fine_response_defect, field_name='FINE causal response defect', minimum=Decimal(0))


@dataclass(frozen=True, slots=True)
class NativeTrainingOutcome(_Identity, CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/native-training-outcome"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    unit_id: str
    source_manifest: ObjectIdentity
    native_source: ObjectIdentity
    origin: ObjectIdentity
    clock_id: str
    cutoff: Decimal
    frame_sha256: str | None
    views: tuple[MatrixE3ViewOutcome | MatchedResponseViewOutcome, ...]
    numerical_disposition: str
    evidence: tuple[ObjectIdentity, ...]
    standing: str = STANDING

    def __post_init__(self):
        for value in (self.record_id, self.unit_id, self.clock_id):
            validate_stable_id(value)
        for value, kind in ((self.source_manifest, NativeTrainingAcquisitionRequest), (self.native_source, ScheduledSource),
                (self.origin, NativeTrainingCausalPrefix)):
            exact_reference(value, kind)
        validate_decimal(self.cutoff, field_name="native TRAIN outcome cutoff", minimum=Decimal(0))
        if self.frame_sha256 is not None:
            validate_sha256(self.frame_sha256)
        require_sorted_unique_ids(self.evidence, attribute="object_id", field_name="native TRAIN outcome evidence")
        if (tuple(value.view_id for value in self.views) != ("fine", "primary")
                or len({type(value) for value in self.views}) != 1
                or any(type(value) not in (MatrixE3ViewOutcome, MatchedResponseViewOutcome) for value in self.views)
                or self.numerical_disposition not in ("SATISFIED", "VIOLATED", "UNEVALUABLE")
                or not self.evidence or self.standing != STANDING
                or self.frame_sha256 is None and any(value is not None for view in self.views for value in view.errors)):
            raise ValueError("native TRAIN outcome loses paired views/nonuse or invents finite frame-free labels")
        for value in self.views:
            validate_record_fields(value)

    def view(self, view_id):
        return next(value for value in self.views if value.view_id == view_id)


@dataclass(frozen=True, slots=True)
class NativeTrainingFeatureBank(_Identity, CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/native-training-feature-bank"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    allocation: ObjectIdentity
    role: str
    rows: tuple[NativeTrainingFeature, ...]
    acquisition: ObjectIdentity
    standing: str = STANDING

    def __post_init__(self):
        _validate_bank(self, NativeTrainingFeature)


@dataclass(frozen=True, slots=True)
class NativeTrainingOutcomeBank(_Identity, CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/native-training-outcome-bank"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    allocation: ObjectIdentity
    role: str
    rows: tuple[NativeTrainingOutcome, ...]
    acquisition: ObjectIdentity
    standing: str = STANDING

    def __post_init__(self):
        _validate_bank(self, NativeTrainingOutcome)


def _validate_bank(bank, kind):
    validate_stable_id(bank.record_id)
    exact_reference(bank.allocation, UnitAllocation)
    exact_reference(bank.acquisition, NativeTrainingAcquisitionSeal)
    require_sorted_unique_ids(bank.rows, attribute="unit_id", field_name="all assigned native TRAIN units")
    if (bank.role != "train" or bank.standing != STANDING or not bank.rows
            or any(type(value) is not kind for value in bank.rows)):
        raise ValueError("native TRAIN bank changes its exact whole-unit role or original nonuse rows")
    for value in bank.rows:
        validate_record_fields(value)


def native_training_bank_types():
    return NativeTrainingFeatureBank, NativeTrainingOutcomeBank


def validate_native_training_banks(specification, allocation, features, outcomes):
    if (type(allocation) is not UnitAllocation or type(features) is not NativeTrainingFeatureBank
            or type(outcomes) is not NativeTrainingOutcomeBank):
        raise TypeError("native TRAIN fit requires its exact paired native banks")
    validate_record_fields(allocation); validate_record_fields(features); validate_record_fields(outcomes)
    units = allocation.unit_ids("train")
    if (features.allocation != allocation.identity or outcomes.allocation != allocation.identity
            or features.acquisition != outcomes.acquisition
            or tuple(value.unit_id for value in features.rows) != units
            or tuple(value.unit_id for value in outcomes.rows) != units):
        raise ValueError("native TRAIN banks drop, duplicate or cross assigned whole units/acquisition")
    families = {"family-de-anneal": "matrix-history.joint-decreasing-coupling",
        "family-x-first": "matrix-history.x-first-increasing-coupling", "family-y-first": "matrix-history.y-first-increasing-coupling"}
    for feature, outcome in zip(features.rows, outcomes.rows, strict=True):
        if (specification.measurement.is_matched != (feature.physical_forecast is not None)
                or specification.measurement.is_matched != all(type(view) is MatchedResponseViewOutcome for view in outcome.views)):
            raise ValueError('native TRAIN banks substitute the selected feature or paired target contract')
        if specification.measurement.is_matched:
            validate_matched_features(feature.values, feature.disposition, curve_primary=specification.is_curve_primary)
        unit = allocation.unit(feature.unit_id)
        fields = ("unit_id", "source_manifest", "native_source", "origin", "clock_id", "cutoff", "frame_sha256")
        if (any(getattr(feature, name) != getattr(outcome, name) for name in fields)
                or not unit.exposed or feature.source_manifest not in allocation.sources
                or feature.source_manifest.object_id != unit.source_id
                or feature.cutoff != specification.measurement.origin_tick * specification.measurement.primary_timestep):
            raise ValueError("native TRAIN banks substitute actual source, causal frame, clock, cutoff or nonuse")
        if feature.disposition == "AVAILABLE" and any(dict(feature.values)[name] != Decimal(unit.family_id == family)
                for name, family in families.items()):
            raise ValueError("native TRAIN feature changes actual preparation family")


from empirical_lawhood.adapters.methods.matrix_parameter_history.records import METHODS, MatrixParameterHistoryControl, coordinate_identity
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import MatrixParameterFactorControl
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRoot
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import (
    ROLES, ScheduledCheckpoint, ScheduledNativeEvidence, ScheduledPrefixPolicy,
    ScheduledPrefixTrace, ScheduledSource, _validate_prefix_native_evidence)
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MatrixArrayMember, MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_native import ScheduledResponseTransitionControl
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseArrays, ScheduledResponseLossCell
from .origin_mechanics import model_predictors
from .response_scoring import MatrixDenseResponseCell, MatrixDenseResponseDiagnostics
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import validate_response_score


@dataclass(frozen=True, slots=True)
class NativeTrainingArrays(_Identity, CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/native-training-arrays'
    operand_id: str
    source: ObjectIdentity
    role: str
    array_artifact: ArtifactIdentity
    members: tuple[MatrixArrayMember, ...]
    producers: tuple[ObjectIdentity, ...]
    outcome_access: OutcomeAccess
    visibility_ceiling: VisibilityCeiling

    def __post_init__(self):
        validate_stable_id(self.operand_id)
        require_sorted_unique_ids(self.members, attribute='name', field_name='members')
        require_sorted_unique_ids(self.producers, attribute='object_id', field_name='producers')
        if (self.source.object_schema != ScheduledSource.SCHEMA or self.role not in ('PREFIX', 'FULL_HISTORY', 'PREFIX_DIAGNOSTICS', 'CAUSAL_STATE')
                or not self.members or not self.producers or self.array_artifact.payload_schema != MATRIX_ARRAY_SCHEMA
                or self.array_artifact.media_type != 'application/x-npz' or not 0 < self.array_artifact.size_bytes <= MAXIMUM_MATRIX_ARRAY_BYTES
                or self.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
                or self.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE):
            raise ValueError('scheduled arrays change bounded original causal/protected scope')


@dataclass(frozen=True, slots=True)
class NativeTrainingPrefixHistory(_Identity, CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/native-training-prefix-history'
    history_id: str
    source: ObjectIdentity
    arrays: NativeTrainingArrays
    checkpoint: ScheduledCheckpoint
    native: ScheduledNativeEvidence
    configuration: ObjectIdentity
    acquisition: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.history_id)
        if (type(self.arrays) is not NativeTrainingArrays or self.arrays.role != 'PREFIX' or self.source != self.arrays.source
                or type(self.checkpoint) is not ScheduledCheckpoint or self.checkpoint.source != self.source
                or type(self.native) is not ScheduledNativeEvidence):
            raise ValueError('scheduled prefix cannot accept sealed full history or exposed source')

    def validate_source(self, source):
        self.__post_init__()
        self.checkpoint.validate_source(source, self.arrays)
        exact_reference(self.acquisition, NativeTrainingAcquisitionSeal)
        _validate_prefix_native_evidence(self, source, configuration=self.configuration,
            parent_task=NAMESPACE + "." + source.root_id + ".prefix", operation=NAMESPACE + ".paired-prefix.v1",
            native_sources={*native_source_pins(source), self.acquisition},
            output_access=OutcomeAccess.DEVELOPMENT_VISIBLE, output_visibility=VisibilityCeiling.DEVELOPMENT_ONLY)


@dataclass(frozen=True, slots=True)
class NativeTrainingNumericalAssessment(_Identity, CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/native-training-numerical-assessment'
    assessment_id: str
    source: ObjectIdentity
    history: ObjectIdentity
    numerical_design: ObjectIdentity
    controls: tuple[MatrixParameterHistoryControl, ...]
    numerical_pass: bool

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        if (self.source.object_schema != ScheduledSource.SCHEMA or self.history.object_schema != NativeTrainingPrefixHistory.SCHEMA
                or tuple(c.control_id for c in self.controls) != METHODS or type(self.numerical_pass) is not bool
                or self.numerical_pass != all(c.disposition == 'SATISFIED' for c in self.controls)):
            raise ValueError('scheduled prefix assessment loses exact independent numerical controls')


@dataclass(frozen=True, slots=True)
class NativeTrainingPrefixWitness(_Identity, CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/native-training-prefix-witness'
    product_id: str
    source: ObjectIdentity
    history: ObjectIdentity
    numerical: ObjectIdentity
    policy: ObjectIdentity
    traces: tuple[ScheduledPrefixTrace, ...]
    arrays: NativeTrainingArrays

    def __post_init__(self):
        validate_stable_id(self.product_id)
        if (self.source.object_schema != ScheduledSource.SCHEMA or self.history.object_schema != NativeTrainingPrefixHistory.SCHEMA
                or self.numerical.object_schema != NativeTrainingNumericalAssessment.SCHEMA
                or self.policy.object_schema != ScheduledPrefixPolicy.SCHEMA
                or type(self.arrays) is not NativeTrainingArrays or self.arrays.role != 'PREFIX_DIAGNOSTICS'
                or self.arrays.source != self.source or not self.traces):
            raise ValueError('scheduled prefix witness cannot accept full-history E1 diagnostics')


@dataclass(frozen=True, slots=True)
class NativeTrainingFrameAssessment(_Identity, CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/native-training-frame-assessment'
    assessment_id: str
    source: ObjectIdentity
    witness: ObjectIdentity
    numerical_design: ObjectIdentity
    controls: tuple[MatrixParameterFactorControl, ...]
    numerical_pass: bool

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import METHODS as FACTOR_METHODS
        validate_stable_id(self.assessment_id)
        if (self.source.object_schema != ScheduledSource.SCHEMA or self.witness.object_schema != NativeTrainingPrefixWitness.SCHEMA
                or tuple(c.method for c in self.controls) != FACTOR_METHODS or type(self.numerical_pass) is not bool
                or self.numerical_pass != all(c.disposition in ('SATISFIED', 'NOT_APPLICABLE') for c in self.controls)):
            raise ValueError('scheduled frame assessment loses complete independent eigenpair controls')


@dataclass(frozen=True, slots=True)
class NativeTrainingCausalPrefix(_Identity, CanonicalRecord):
    """Predictor delivery: causal phase/frame only, never checkpoint/RNG state."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/native-training-causal-prefix'
    prefix_id: str
    source: ObjectIdentity
    history: ObjectIdentity
    numerical: ObjectIdentity
    witness: ObjectIdentity
    frame_assessment: ObjectIdentity
    policy: ObjectIdentity
    root: MatrixProgrammeRoot
    cutoff_tick: int
    frame_sha256: str | None
    disposition: str
    reason: str | None
    arrays: NativeTrainingArrays

    def __post_init__(self):
        from empirical_lawhood.kernel.serialization import validate_sha256
        validate_stable_id(self.prefix_id)
        if self.frame_sha256 is not None:
            validate_sha256(self.frame_sha256)
        if (self.source.object_schema != ScheduledSource.SCHEMA or self.history.object_schema != NativeTrainingPrefixHistory.SCHEMA
                or self.numerical.object_schema != NativeTrainingNumericalAssessment.SCHEMA
                or self.witness.object_schema != NativeTrainingPrefixWitness.SCHEMA
                or self.frame_assessment.object_schema != NativeTrainingFrameAssessment.SCHEMA
                or self.policy.object_schema != ScheduledPrefixPolicy.SCHEMA
                or type(self.root) is not MatrixProgrammeRoot or self.root.role not in ROLES
                or type(self.cutoff_tick) is not int or self.cutoff_tick < 1
                or self.disposition not in ('AVAILABLE', 'NO_ORIGIN', 'UNEVALUABLE')
                or (self.disposition == 'AVAILABLE') != (self.frame_sha256 is not None and self.reason is None)
                or self.disposition != 'AVAILABLE' and self.reason is None
                or type(self.arrays) is not NativeTrainingArrays or self.arrays.role != 'CAUSAL_STATE' or self.arrays.source != self.source):
            raise ValueError('causal delivery changes exact cutoff/role or manufactures available frame')


@dataclass(frozen=True, slots=True)
class NativeTrainingPhysicalForecast(_Identity, CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/native-training-response-forecast'
    forecast_id: str
    source: ObjectIdentity
    causal_prefix: ObjectIdentity
    protocol: ObjectIdentity
    mechanical_model: ObjectIdentity
    frame_sha256: str | None
    arrays: ScheduledResponseArrays
    disposition: str
    dispositions: tuple[tuple[str, str, str, str | None], ...]

    def __post_init__(self):
        validate_stable_id(self.forecast_id)
        expected = tuple((v, p) for v in ('PRIMARY', 'FINE') for p in model_predictors(self.mechanical_model))
        if (self.causal_prefix.object_schema != NativeTrainingCausalPrefix.SCHEMA
                or self.protocol.object_schema != ScheduledResponseProtocol.SCHEMA or self.arrays.role != 'FORECAST'
                or self.arrays.source != self.source or tuple((v, p) for v, p, _, _ in self.dispositions) != expected
                or self.disposition not in ('AVAILABLE', 'NO_ORIGIN', 'UNEVALUABLE', 'INSTRUMENT_UNRESOLVED')
                or any(s not in ('AVAILABLE', 'UNRESOLVED') or (s == 'AVAILABLE') != (reason is None)
                    for _, _, s, reason in self.dispositions)):
            raise ValueError('scheduled forecast thins full paired predictor/menu or manufactures availability')


@dataclass(frozen=True, slots=True)
class NativeTrainingResponse(_Identity, CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/native-training-native-responses'
    response_id: str
    source: ObjectIdentity
    causal_prefix: ObjectIdentity
    physical_forecast: ObjectIdentity
    acquisition_seal: ObjectIdentity
    protocol: ObjectIdentity
    arrays: ScheduledResponseArrays
    branch_ids: tuple[str, ...]
    native: tuple[ScheduledNativeEvidence, ...]
    disposition: str
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.response_id)
        if (self.arrays.source != self.source or self.arrays.role != 'RESPONSES'
                or self.branch_ids != tuple(sorted(set(self.branch_ids)))
                or self.disposition not in ('COMPLETED', 'NO_ORIGIN', 'UNEVALUABLE', 'INSTRUMENT_UNRESOLVED')
                or (self.disposition == 'COMPLETED') != bool(self.native)
                or self.native and len(self.native) != 1
                or any(type(n) is not ScheduledNativeEvidence for n in self.native)):
            raise ValueError('scheduled response changes actual branch/native/nonuse census')


    def validate_nonentry(self, causal, physical, protocol, panels):
        """Require this TRAIN family's exact unavailable response relation."""
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import validate_native_response_nonentry
        return validate_native_response_nonentry(self, causal, physical, protocol, panels)

    @property
    def error_forecast(self):
        """Local received-array interface; canonical evidence names the real acquisition seal."""
        return self.acquisition_seal


@dataclass(frozen=True, slots=True)
class NativeTrainingScore(_Identity, CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/native-training-response-score'
    VERSION: ClassVar[str] = '2.0.0'
    score_id: str
    source: ObjectIdentity
    causal_prefix: ObjectIdentity
    acquisition_seal: ObjectIdentity
    physical_forecast: ObjectIdentity
    responses: ObjectIdentity
    root_id: str
    independent_group_id: str
    role: str
    criterion: ObjectIdentity
    controls: tuple[ScheduledResponseTransitionControl, ...]
    numerical_pass: bool
    disposition: str
    cells: tuple[ScheduledResponseLossCell | MatrixDenseResponseCell, ...]
    cumulative_log_errors: tuple[Decimal | None, ...]
    reason_codes: tuple[str, ...]
    dense: MatrixDenseResponseDiagnostics | None = None

    def __post_init__(self):
        validate_response_score(self)

    @property
    def error_forecast(self):
        """Local received-array interface; canonical evidence names the real acquisition seal."""
        return self.acquisition_seal


@dataclass(frozen=True, slots=True)
class NativeTrainingSummary(_Identity, CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/native-training-summary"
    record_id: str
    specification: ObjectIdentity
    acquisition: ObjectIdentity
    unit_ids: tuple[str, ...]
    feature_dispositions: tuple[tuple[str, str], ...]
    numerical_dispositions: tuple[tuple[str, str], ...]
    qualification: str = "NOT_ESTABLISHED"

    def __post_init__(self):
        validate_stable_id(self.record_id)
        exact_reference(self.specification, NativeTrainingAcquisitionSpecification)
        exact_reference(self.acquisition, NativeTrainingAcquisitionSeal)
        require_sorted_unique_strings(self.unit_ids, field_name="complete TRAIN summary", allow_empty=False)
        if (tuple(unit for unit, _ in self.feature_dispositions) != self.unit_ids
                or tuple(unit for unit, _ in self.numerical_dispositions) != self.unit_ids
                or any(value not in FEATURE_DISPOSITIONS for _, value in self.feature_dispositions)
                or any(value not in ("SATISFIED", "VIOLATED", "UNEVALUABLE") for _, value in self.numerical_dispositions)
                or self.qualification != "NOT_ESTABLISHED"):
            raise ValueError("native TRAIN summary loses complete negative/nonuse census or promotes qualification")
