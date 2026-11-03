# SPDX-License-Identifier: MPL-2.0
"""Exact original sequence required by new selected prepared acquisition.

These locators carry no successful-check flag, independent exclusion list or
scientific authority. Existing publication/receipt owners authenticate them.
Current entry retains the exact original scientific and publication joins.
"""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_finite_dt_source_records import MatrixFiniteDtTrainingLocator
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import physical_key
from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammeInputCommitments, MatrixProgrammePublishedInput
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent
from .selected_produced_inputs import validate_produced_input_parents
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id

from .preparation_experiment import MatrixPreparationSourceBank
from .protected_preparation_records import MatrixConfirmationSources, MatrixReservedTransferSources
from .prepared_assay_method import MatrixPreparedAssayMethod
from .prepared_response_science import MatrixPreparedResponsePanel

MISSING_ORIGINAL_COMMITMENTS = (
    "Original commitment evidence is missing: derivation, authoring or acquisition requires MatrixPreparedOriginalCommitments "
    "with the actual native TRAIN locator, whole C publication and explicit source byte budget."
)


@dataclass(frozen=True, slots=True)
class MatrixPreparedOriginalCommitments(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-original-commitments"
    VERSION: ClassVar[str] = "2.0.0"
    record_id: str
    native_training_locator: MatrixFiniteDtTrainingLocator
    input_commitments: MatrixProgrammePublishedInput
    maximum_source_bytes: int

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.native_training_locator) is not MatrixFiniteDtTrainingLocator
                or type(self.input_commitments) is not MatrixProgrammePublishedInput):
            raise TypeError("prepared commitments require actual original native and whole C publication locators")
        self.native_training_locator.__post_init__()
        self.input_commitments.__post_init__()
        self.input_commitments.require_kind(MatrixProgrammeInputCommitments)
        if type(self.maximum_source_bytes) is not int or self.maximum_source_bytes < 1:
            raise ValueError("prepared commitments require an explicit positive complete C source byte budget")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


def require_original_commitments(value):
    if type(value) is not MatrixPreparedOriginalCommitments:
        raise ValueError(MISSING_ORIGINAL_COMMITMENTS)
    value.__post_init__()
    return value


def prepared_original_panel(panel):
    """Project the exact original declared panel into the prepared method owner."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponsePanel
    if type(panel) is not ScheduledResponsePanel:
        raise TypeError("prepared response commitment requires its actual original panel")
    panel.__post_init__()
    return MatrixPreparedResponsePanel(panel.panel_id, panel.independent_group_id, panel.role, panel.streams)


def validate_committed_prepared_sources(*, phase, sources, phases, producing_provenance):
    """Keep C's exact physical roots and streams across additive audit metadata."""
    roles = {"E5_OPPORTUNITY": ("e5.development",), "E5_CONFIRMATION": ("e5.confirmation",),
        "E6_TRANSFER": ("e6.nearby", "e6.shifted")}
    if phase not in roles:
        raise ValueError("prepared sources require an exact current C phase")
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.input_records import ResolvedMatrixProgrammePhaseInputs
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledReservation
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledResponseSelection
    selected = dict(phases)
    expected = {}
    for role in roles[phase]:
        selected_phase = selected[role]
        if (type(selected_phase) is not ResolvedMatrixProgrammePhaseInputs or selected_phase.role != role
                or type(selected_phase.reservation) is not ScheduledReservation
                or type(selected_phase.responses) is not ScheduledResponseSelection):
            raise TypeError("prepared sources require their exact existing resolved phase/reservation/response owners")
        response, allocation = selected_phase.responses, selected_phase.reservation.allocation
        response.validate_allocation(allocation)
        for protocol in response.protocols:
            root_id = protocol.public_source.root.root_id
            root, = (value for value in allocation.roots if value.root.root_id == root_id)
            if root_id in expected:
                raise ValueError("prepared C repeats an original phase root")
            expected[root_id] = root, protocol.public_source
    rows = tuple(sources.sources) if phase == "E5_OPPORTUNITY" else tuple(value for _, value in sources.source_arms())
    if {value.original.root.root_id for value in rows} != set(expected):
        raise PermissionError("prepared sources change C's complete original phase root census")
    for value in rows:
        root, public = expected[value.original.root.root_id]
        if (value.root != root or value.coordinate != public.coordinate or value.original.policy != public.policy
                or value.original.source.object_id != public.source.object_id or value.provenance != producing_provenance):
            raise PermissionError("prepared sources change C's original groups, streams, numerical policy or producing source")


def validate_committed_prepared_panels(*, phase, assay, panels, selections):
    """Recipe arms retain the same actual pre-TRAIN assay and future panels."""
    roles = {"E5_OPPORTUNITY": ("e5.development",), "E5_CONFIRMATION": ("e5.confirmation",),
        "E6_TRANSFER": ("e6.nearby", "e6.shifted")}
    selected, expected = dict(selections), {}
    for role in roles[phase]:
        response = selected[role]
        for protocol in response.protocols:
            if MatrixPreparedAssayMethod.from_protocol(assay.record_id, protocol) != assay:
                raise PermissionError("prepared sources change C's immutable numerical assay")
        for group, values in response.panels:
            if group in expected:
                raise ValueError("prepared C repeats an original phase panel group")
            expected[group] = tuple(sorted((prepared_original_panel(value) for value in values), key=lambda value: value.panel_id))
    if tuple(panels) != tuple((group, expected[group]) for group in sorted(expected)):
        raise PermissionError("prepared sources change C's exact original common and independent future panels")


def validate_original_prepared_scope(*, phase, sources, assay, panels, request, future_selections, e4_phases):
    """Pure exact consumption/exclusion join; callers authenticate every owner."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_records import NativeTrainingAcquisitionRequest
    from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
    from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
    expected_type = {"E5_OPPORTUNITY": MatrixPreparationSourceBank,
        "E5_CONFIRMATION": MatrixConfirmationSources, "E6_TRANSFER": MatrixReservedTransferSources}
    if (phase not in expected_type or type(sources) is not expected_type[phase]
            or type(assay) is not MatrixPreparedAssayMethod or type(request) is not NativeTrainingAcquisitionRequest):
        raise TypeError("prepared commitment join changes its exact declared source phase or original request")
    sources.__post_init__(); assay.__post_init__(); request.__post_init__()
    roles = dict(future_selections)
    if tuple(sorted(roles)) != ("CALIBRATION", "EVALUATION", "TRANSFER_NEARBY", "TRANSFER_SHIFTED") or len(future_selections) != 4:
        raise ValueError("prepared acquisition requires all four authenticated pre-TRAIN response commitments")
    actual = tuple(sources.sources) if phase == "E5_OPPORTUNITY" else tuple(value for _, value in sources.source_arms())
    if phase == "E6_TRANSFER":
        original = request.future_manifest
        closure = sources.closure
        if (closure.reservation != original.reservation or closure.specification != original.native_specification
                or closure.audit != original.audit or closure.audit_publication != original.audit_publication):
            raise ValueError("prepared E6 changes its exact original pre-TRAIN reserve, source selection or audit")
        expected_sources, expected_panels = {}, {}
        for role in ("TRANSFER_NEARBY", "TRANSFER_SHIFTED"):
            selected = roles[role]
            for protocol in selected.protocols:
                root_id = protocol.public_source.root.root_id
                if root_id in expected_sources:
                    raise ValueError("prepared E6 repeats an original reserved root")
                expected_sources[root_id] = protocol
            for group, values in selected.panels:
                if group in expected_panels:
                    raise ValueError("prepared E6 repeats an original reserved independent group")
                expected_panels[group] = tuple(sorted((prepared_original_panel(value) for value in values), key=lambda value: value.panel_id))
        if (len(actual) != len(expected_sources) or {value.original.root.root_id for value in actual} != set(expected_sources)
                or tuple(group for group, _ in panels) != tuple(sorted(expected_panels))):
            raise ValueError("prepared E6 thins or substitutes its complete original reserved root/panel census")
        index = closure.source_index()
        for source in actual:
            protocol = expected_sources[source.original.root.root_id]
            descriptor = next(value for value in closure.descriptors if value.root_id == source.original.root.root_id)
            original_source = closure.original(descriptor, index=index)
            if (source.original != protocol.public_source or ScheduledPublicSource.from_source(original_source) != protocol.public_source
                    or MatrixPreparedAssayMethod.from_protocol(assay.record_id, protocol) != assay):
                raise ValueError("prepared E6 substitutes an original source or committed numerical assay")
        if any(tuple(sorted(values, key=lambda value: value.panel_id)) != expected_panels[group] for group, values in panels):
            raise ValueError("prepared E6 substitutes exact pre-TRAIN panel identities, common-noise bindings or effective streams")
        return
    reserved = request.future_manifest.reservation.allocation
    withheld = {value.coordinate for value in reserved.roots if value.root.role is MatrixProgrammeRole.WITHHELD_TRANSFER}
    forbidden_physics = {physical_key(value) for value in reserved.coordinates if coordinate_identity(value) in withheld}
    forbidden_groups, forbidden_seeds = set(), set()
    for manifest in (request.train_manifest, request.future_manifest):
        forbidden_seeds.update(manifest.audit.census.effective_seed_exclusions)
        forbidden_groups.update(manifest.audit.census.exposed_independent_groups)
        for root in manifest.reservation.allocation.roots:
            forbidden_groups.add(root.root.independent_group_id)
            forbidden_seeds.update(value.effective_seed for value in root.streams)
    forbidden_seeds.update(value.effective_seed for panel in request.panels for value in panel.streams)
    forbidden_seeds.update(value.effective_seed for selected in roles.values()
        for _, values in selected.panels for panel in values for value in panel.streams)
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledResponseSelection
    if tuple(name for name, _ in e4_phases) != ("CALIBRATION", "CONFIRMATION", "DEVELOPMENT"):
        raise ValueError("prepared acquisition omits a complete committed original E4 phase")
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.input_records import ResolvedMatrixProgrammePhaseInputs
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledReservation
    for label, selected in e4_phases:
        if (type(selected) is not ResolvedMatrixProgrammePhaseInputs or selected.role != "e4." + label.lower()
                or type(selected.reservation) is not ScheduledReservation
                or type(selected.responses) is not ScheduledResponseSelection):
            raise TypeError("prepared E4 exposure requires its exact existing resolved reservation/response owners")
        selection, allocation = selected.responses, selected.reservation.allocation
        selection.validate_allocation(allocation)
        forbidden_groups.update(value.root.independent_group_id for value in allocation.roots)
        forbidden_seeds.update(value.effective_seed for root in allocation.roots for value in root.streams)
        forbidden_seeds.update(value.effective_seed for _, values in selection.panels for panel in values for value in panel.streams)
    if (any(value.root.root.independent_group_id in forbidden_groups or physical_key(value.coordinate) in forbidden_physics for value in actual)
            or any(value.effective_seed in forbidden_seeds for source in actual for value in source.root.streams)
            or any(value.effective_seed in forbidden_seeds for _, values in panels for panel in values for value in panel.streams)):
        raise ValueError("prepared E5 consumes original TRAIN/E3/E4/reserved groups, effective streams or full E6 physical keys")


# Entry evidence binds its actual original scientific and custody operands.
from .selected_opportunity import MatrixSelectedOpportunityEvidence, MatrixSelectedOpportunityPublicProgramme
from .selected_entry import MatrixSelectedEntryEvidence
from .selected_development_product import MatrixSelectedDevelopmentProduct
from .selected_revision_entry import MatrixRevisionEntryEvidence
from .selected_protected_programme import MatrixSelectedPublicProgramme
from .selected_revision_programme import MatrixRevisionPreparedProgramme


@dataclass(frozen=True, slots=True)
class MatrixSelectedOpportunityEvidenceV2(MatrixSelectedOpportunityEvidence):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-opportunity-evidence-v2"
    original_commitments: MatrixPreparedOriginalCommitments

    def __post_init__(self):
        MatrixSelectedOpportunityEvidence.__post_init__(self)
        require_original_commitments(self.original_commitments)


@dataclass(frozen=True, slots=True)
class MatrixSelectedEntryEvidenceV3(MatrixSelectedEntryEvidence):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-entry-evidence-v3"
    original_commitments: MatrixPreparedOriginalCommitments
    development_nomination: MatrixSelectedDevelopmentProduct | None

    def __post_init__(self):
        MatrixSelectedEntryEvidence.__post_init__(self)
        require_original_commitments(self.original_commitments)
        if len(self.upstream_products) != 4:
            raise ValueError("selected committed entry separates the exact four original E3 producers")
        if self.development_nomination is not None:
            if type(self.development_nomination) is not MatrixSelectedDevelopmentProduct:
                raise TypeError("selected committed CONF requires its actual original development nomination")
            self.development_nomination.__post_init__()


@dataclass(frozen=True, slots=True)
class MatrixRevisionEntryEvidenceV2(MatrixRevisionEntryEvidence):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/revision-entry-evidence-v2"
    original_commitments: MatrixPreparedOriginalCommitments

    def __post_init__(self):
        MatrixRevisionEntryEvidence.__post_init__(self)
        require_original_commitments(self.original_commitments)


def committed_entry_evidence(evidence, commitments):
    """Build the new edition from unchanged scientific/custody fields."""
    from dataclasses import fields
    require_original_commitments(commitments)
    if type(evidence) in (MatrixSelectedOpportunityEvidenceV2, MatrixSelectedEntryEvidenceV3, MatrixRevisionEntryEvidenceV2):
        if evidence.original_commitments != commitments:
            raise ValueError("selected input substitutes an already bound original commitment")
        return evidence
    if type(evidence) is MatrixSelectedOpportunityEvidence:
        kind = MatrixSelectedOpportunityEvidenceV2
        extra = {}
    elif type(evidence) is MatrixRevisionEntryEvidence:
        kind = MatrixRevisionEntryEvidenceV2
        extra = {}
    else:
        from .selected_entry_v2 import MatrixSelectedEntryEvidenceV2
        if type(evidence) not in (MatrixSelectedEntryEvidence, MatrixSelectedEntryEvidenceV2):
            raise TypeError("selected committed entry requires its exact original evidence family")
        kind = MatrixSelectedEntryEvidenceV3
        extra = {"development_nomination": getattr(evidence, "development_nomination", None)}
    original = {value.name: getattr(evidence, value.name) for value in fields(MatrixSelectedEntryEvidence if kind is MatrixSelectedEntryEvidenceV3 else type(evidence))}
    return kind(**original, original_commitments=commitments, **extra)


@dataclass(frozen=True, slots=True)
class MatrixSelectedOpportunityRootConfigV2(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-opportunity-root-config-v2"
    VERSION: ClassVar[str] = '2.0.0'
    config_id: str
    programme: "MatrixSelectedOpportunityPublicProgramme"
    phase: str
    evidence: ObjectIdentity
    evidence_size_bytes: int
    produced_input_parents: tuple[ArtifactLineageParent, ...]

    def __post_init__(self):
        validate_produced_input_parents(self.produced_input_parents)
        from .selected_opportunity import MatrixSelectedOpportunityPublicProgramme
        from .selected_opportunity_bindings import global_node
        if (type(self.programme) is not MatrixSelectedOpportunityPublicProgramme or self.phase != "design"
                or self.config_id != "config." + global_node(self.programme, self.phase)
                or type(self.evidence) is not ObjectIdentity or self.evidence.object_schema != MatrixSelectedOpportunityEvidenceV2.SCHEMA
                or type(self.evidence_size_bytes) is not int or self.evidence_size_bytes < 1):
            raise ValueError("selected committed opportunity requires its exact original evidence/byte census")
        self.programme.__post_init__()


@dataclass(frozen=True, slots=True)
class MatrixSelectedProtectedRootConfigV3(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-protected-root-config-v3"
    VERSION: ClassVar[str] = '2.0.0'
    config_id: str
    programme: "MatrixSelectedPublicProgramme"
    phase: str
    entry_evidence: ObjectIdentity
    entry_evidence_size_bytes: int
    produced_input_parents: tuple[ArtifactLineageParent, ...]

    def __post_init__(self):
        validate_produced_input_parents(self.produced_input_parents)
        from .selected_protected_programme import MatrixSelectedPublicProgramme, global_node
        if (type(self.programme) is not MatrixSelectedPublicProgramme or self.phase != "entry"
                or self.config_id != "config." + global_node(self.programme, self.phase)
                or type(self.entry_evidence) is not ObjectIdentity or self.entry_evidence.object_schema != MatrixSelectedEntryEvidenceV3.SCHEMA
                or type(self.entry_evidence_size_bytes) is not int or self.entry_evidence_size_bytes < 1):
            raise ValueError("selected committed protected entry requires its exact original evidence/byte census")
        self.programme.__post_init__()


@dataclass(frozen=True, slots=True)
class MatrixRevisionRootConfigV2(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/revision-root-config-v2"
    VERSION: ClassVar[str] = '2.0.0'
    config_id: str
    programme: "MatrixRevisionPreparedProgramme"
    phase: str
    entry_evidence: ObjectIdentity
    entry_evidence_size_bytes: int
    produced_input_parents: tuple[ArtifactLineageParent, ...]

    def __post_init__(self):
        validate_produced_input_parents(self.produced_input_parents)
        from .selected_revision_programme import MatrixRevisionPreparedProgramme, global_node
        if (type(self.programme) is not MatrixRevisionPreparedProgramme or self.phase != "entry"
                or self.config_id != "config." + global_node(self.programme, self.phase)
                or type(self.entry_evidence) is not ObjectIdentity or self.entry_evidence.object_schema != MatrixRevisionEntryEvidenceV2.SCHEMA
                or type(self.entry_evidence_size_bytes) is not int or self.entry_evidence_size_bytes < 1):
            raise ValueError("selected committed revision entry requires its exact original evidence/byte census")
        self.programme.__post_init__()
