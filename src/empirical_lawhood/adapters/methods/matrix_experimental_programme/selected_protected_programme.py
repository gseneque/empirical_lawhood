# SPDX-License-Identifier: MPL-2.0
"""Complete selected protected source rosters and pre-outcome phase contracts.

Original source/exposure records remain required. Neither this composition nor
a compiled graph authenticates their publication, numerical warrant or authority.
"""

from .preparation_records import is_baseline_recipe

from dataclasses import dataclass, replace
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseArrays, ScheduledResponseProtocol
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling, inherited_visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteResult, CanonicalTaskReceipt, derived_outcome_access

from .prepared_assay_method import MatrixPreparedAssayMethod, TOLERANCES
from .prepared_functional import _validate_matched_future_panels
from .prepared_point import MatrixPreparedPublicSource
from .prepared_response_science import MatrixPreparedResponsePanel, validate_prepared_panels
from .protected_preparation_records import MatrixConfirmationSources, MatrixReservedTransferSources
from .records import MatrixFunctionalCriterion, MatrixProgrammeCase, MatrixProgrammeRoster
from .science import MatrixPreparationNomination
from .selected_future import PROGRAMME_SCHEMA, NAMESPACE
from .selected_point import MatrixSelectedPointDesign
from .selected_public import MatrixSelectedNominationSelection, MatrixSelectedPointPayload, package_identity


@dataclass(frozen=True, slots=True)
class MatrixSelectedProtectedProgramme(CanonicalRecord):
    SCHEMA: ClassVar[str] = PROGRAMME_SCHEMA
    record_id: str
    sources: MatrixConfirmationSources | MatrixReservedTransferSources
    point_design: MatrixSelectedPointDesign
    assay: MatrixPreparedAssayMethod
    panels: tuple[tuple[str, tuple[MatrixPreparedResponsePanel, ...]], ...]
    criterion: MatrixFunctionalCriterion
    transfer_domain_claims: tuple[str, ...]
    nomination: MatrixPreparationNomination | None
    nomination_publication: ArtifactWriteResult | None
    nomination_receipt: CanonicalTaskReceipt | None

    def __post_init__(self):
        self._validate(MatrixSelectedPointDesign)

    def _validate(self, design_type):
        validate_stable_id(self.record_id)
        confirmation = type(self.sources) is MatrixConfirmationSources
        if (type(self.sources) not in (MatrixConfirmationSources, MatrixReservedTransferSources)
                or type(self.point_design) is not design_type or type(self.assay) is not MatrixPreparedAssayMethod
                or type(self.criterion) is not MatrixFunctionalCriterion
                or self.point_design.phase != ("E5_CONFIRMATION" if confirmation else "E6_TRANSFER")):
            raise TypeError("selected protected programme requires its exact separately reserved source, design, assay and criterion owners")
        for value in (self.sources, self.point_design, self.assay, self.criterion):
            value.__post_init__()
        raw_sources = self.sources.source_arms()
        public = tuple(sorted(((arm, MatrixPreparedPublicSource.from_source(source)) for arm, source in raw_sources),
            key=lambda row: row[1].source.object_id))
        if self.point_design.sources != public:
            raise ValueError("selected protected programme changes complete original prepared source identities")
        actual_arms = {arm: source.recipe for arm, source in raw_sources}
        if self.point_design.arms != tuple(sorted(actual_arms.items())):
            raise ValueError("selected protected programme changes actual matched recipes")
        groups = tuple(sorted({source.root.root.independent_group_id for _, source in raw_sources}))
        if (type(self.panels) is not tuple or tuple(group for group, _ in self.panels) != groups
                or max(self.criterion.minimum_usable_groups, self.criterion.minimum_admitted_groups) > self.point_design.expected_groups
                or any(source.recipe.effort_unit != self.criterion.effort_unit for _, source in raw_sources)):
            raise ValueError("selected protected programme omits whole groups, panels or actual effort convention")
        _validate_matched_future_panels(self.panels)
        known = set(self.sources.closure.reservation.allocation.exposure.census.effective_seed_exclusions)
        known.update(stream.effective_seed for root in self.sources.closure.reservation.allocation.roots for stream in root.streams)
        for _, panels in self.panels:
            for panel in panels:
                if panel.role == "INDEPENDENT_FUTURE":
                    for stream in panel.streams:
                        if stream.effective_seed in known:
                            raise ValueError("selected protected future reuses an exposed or allocated independent stream")
                        known.add(stream.effective_seed)
        measurement = self.point_design.package.specification.measurement
        if (self.assay.horizon_steps != measurement.horizons or self.assay.receiver_count != measurement.receiver_count
                or tuple(sorted((action.role, action.amplitude, action.pulse_steps) for action in self.assay.actions)) !=
                    tuple((role, measurement.action_amplitude, measurement.pulse_ticks) for role in measurement.actions)):
            raise ValueError("selected protected assay changes the exact selected response measurement")
        for _, source in raw_sources:
            validate_prepared_panels(source, dict(self.panels)[source.root.root.independent_group_id])
            self.protocol(source).__post_init__()
        if confirmation:
            self._require_nomination()
            if self.transfer_domain_claims:
                raise ValueError("confirmation cannot select or assess transfer regimes")
        elif ((self.nomination, self.nomination_publication, self.nomination_receipt) != (None, None, None)
                or len(self.transfer_domain_claims) != 2 or any(claim not in (
                    "INTERPOLATION_WITHIN_ASSESSED_DOMAIN", "EXTRAPOLATION_WITHIN_ASSESSED_DOMAIN") for claim in self.transfer_domain_claims)):
            raise ValueError("transfer requires two declared regime interpretations and cannot depend on E5 nomination")

    def _require_nomination(self, nomination_type=MatrixPreparationNomination):
        if (type(self.nomination) is not nomination_type or type(self.nomination_publication) is not ArtifactWriteResult
                or type(self.nomination_receipt) is not CanonicalTaskReceipt):
            raise TypeError("selected confirmation requires actual original nomination publication and receipt")
        nomination, publication, receipt = self.nomination, self.nomination_publication, self.nomination_receipt
        for record in (nomination, publication, receipt):
            record.__post_init__()
        parents = publication.logical.lineage_parents
        expected_access = derived_outcome_access(OutcomeAccess.DEVELOPMENT_VISIBLE,
            *(value.outcome_access for value in parents))
        expected_visibility = inherited_visibility((VisibilityCeiling.DEVELOPMENT_ONLY,
            *(value.visibility_ceiling for value in parents)), expected_access)
        nomination_pin = nomination.original_nomination if type(nomination) is MatrixSelectedNominationSelection else nomination.identity
        selected = tuple((arm, recipe) for arm, recipe in self.point_design.arms if not is_baseline_recipe(recipe))
        if (nomination.disposition != "NOMINATED" or len(selected) != 1
                or (nomination.selected_arm_id, nomination.selected_recipe) != (selected[0][0], selected[0][1].identity)
                or nomination.hold_recipe != dict(self.point_design.arms)[self.sources.hold_arm_id].identity
                or nomination.package != package_identity(self.point_design.package) or nomination.functional_criterion != self.criterion
                or set(nomination.development_unit_ids).intersection(source.root.root.independent_group_id for _, source in self.sources.source_arms())
                or receipt.operational_status is not OperationalStatus.SUCCEEDED
                or publication.logical not in receipt.output_logical_artifacts or publication.materialization not in receipt.output_materializations
                or publication.logical.profile is not ArtifactProfile.CANONICAL_JSON or publication.logical.payload_schema != nomination_pin.object_schema
                or publication.logical.content_sha256 != nomination_pin.object_fingerprint
                or publication.materialization.physical_sha256 != nomination_pin.object_fingerprint
                or (type(nomination) is MatrixPreparationNomination and publication.materialization.size_bytes != len(nomination.canonical_bytes()))
                or publication.logical.outcome_access is not expected_access
                or publication.logical.visibility_ceiling is not expected_visibility):
            raise ValueError("selected confirmation substitutes actual nomination, complete development census or publication custody")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    @property
    def phase(self):
        return self.point_design.phase

    @property
    def roster(self):
        cases = tuple(sorted((MatrixProgrammeCase("case." + source.source_id, arm, source.recipe.identity, source.original,
            source.initial.array_artifact, source.duration, source.recipe.effort,
            ObjectIdentity.from_record(source.coordinate.coordinate_id, source.coordinate), self.assay.identity, ())
            for arm, source in self.sources.source_arms()), key=lambda row: row.case_id))
        return MatrixProgrammeRoster("roster.selected." + self.fingerprint(), self.phase,
            (self.sources.closure.reservation.allocation,), self.sources.closure.reservation, cases)

    def protocol(self, source):
        method = self.assay
        templates = ScheduledResponseArrays("templates.selected." + source.identity.object_fingerprint, "TEMPLATES", source.original.source,
            method.template_artifact, method.template_members, (source.original.source,), OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
        return ScheduledResponseProtocol("protocol.selected." + source.identity.object_fingerprint, source.original, method.criterion,
            method.mechanical_model, method.actions, method.horizon_steps, method.receiver_count, templates,
            *(getattr(method, name) for name in TOLERANCES), method.origin_rule)


@dataclass(frozen=True, slots=True)
class MatrixSelectedPublicProgramme(CanonicalRecord):
    """The actual worker programme, without the parent-only calibration bank."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-public-programme"
    record_id: str
    original_programme: ObjectIdentity
    sources: MatrixConfirmationSources | MatrixReservedTransferSources
    point_design: MatrixSelectedPointPayload
    assay: MatrixPreparedAssayMethod
    panels: tuple[tuple[str, tuple[MatrixPreparedResponsePanel, ...]], ...]
    criterion: MatrixFunctionalCriterion
    transfer_domain_claims: tuple[str, ...]
    nomination: MatrixSelectedNominationSelection | None
    nomination_publication: ArtifactWriteResult | None
    nomination_receipt: CanonicalTaskReceipt | None

    def __post_init__(self):
        if type(self.original_programme) is not ObjectIdentity or self.original_programme.object_schema != PROGRAMME_SCHEMA:
            raise TypeError("selected public programme requires its exact full original programme reference")
        MatrixSelectedProtectedProgramme._validate(self, MatrixSelectedPointPayload)

    @classmethod
    def from_programme(cls, programme):
        if type(programme) is not MatrixSelectedProtectedProgramme:
            raise TypeError("selected public programme projects its actual complete original programme")
        programme.__post_init__()
        return cls("public." + programme.record_id, programme.identity, programme.sources, MatrixSelectedPointPayload.from_design(programme.point_design),
            programme.assay, programme.panels, programme.criterion, programme.transfer_domain_claims,
            None if programme.nomination is None else MatrixSelectedNominationSelection.from_nomination(programme.nomination),
            programme.nomination_publication, programme.nomination_receipt)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    @property
    def phase(self):
        return self.point_design.phase

    @property
    def roster(self):
        roster = MatrixSelectedProtectedProgramme.roster.fget(self)
        return replace(roster, roster_id="roster.selected." + self.original_programme.object_fingerprint)

    def protocol(self, source):
        return MatrixSelectedProtectedProgramme.protocol(self, source)

    def _require_nomination(self):
        MatrixSelectedProtectedProgramme._require_nomination(self, MatrixSelectedNominationSelection)


@dataclass(frozen=True, slots=True)
class MatrixSelectedProtectedRootConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-protected-root-config"
    config_id: str
    programme: MatrixSelectedPublicProgramme
    phase: str
    entry_evidence: ObjectIdentity | None = None
    entry_evidence_size_bytes: int | None = None

    def __post_init__(self):
        if (type(self.programme) is not MatrixSelectedPublicProgramme or self.phase != "assess-programme"
                or self.config_id != "config." + global_node(self.programme, self.phase)):
            raise ValueError("selected protected root changes its exact complete phase configuration")
        if self.entry_evidence is not None or self.entry_evidence_size_bytes is not None:
            raise ValueError("selected assessment cannot replace or reselect source-entry evidence")
        self.programme.__post_init__()


@dataclass(frozen=True, slots=True)
class MatrixSelectedPreparedConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-prepared-config"
    config_id: str
    programme: ObjectIdentity
    public_source: MatrixPreparedPublicSource
    phase: str

    def __post_init__(self):
        if (type(self.programme) is not ObjectIdentity or self.programme.object_schema != MatrixSelectedPublicProgramme.SCHEMA
                or type(self.public_source) is not MatrixPreparedPublicSource
                or self.phase not in ("measure", "frames", "project", "point", "mechanical")
                or self.config_id != "config." + node_id_from_public(self.public_source, self.phase)):
            raise ValueError("selected prepared configuration substitutes its exact seedless phase/source")


def global_node(programme, phase):
    if type(programme) is MatrixSelectedProtectedProgramme:
        programme = MatrixSelectedPublicProgramme.from_programme(programme)
    return NAMESPACE + "." + phase + "." + programme.fingerprint()


def node_id_from_public(public, phase):
    return NAMESPACE + "." + public.source.object_id + "." + phase
