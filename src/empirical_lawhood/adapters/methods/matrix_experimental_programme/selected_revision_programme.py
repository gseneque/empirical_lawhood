# SPDX-License-Identifier: MPL-2.0
"""Actual E4 revision selections and complete prepared downstream sources.

All source records are supplied originals. This composition grants no source
qualification, issue, protected access, sampling or downstream uncertainty.
"""
from dataclasses import dataclass
from typing import ClassVar
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_point import SelectedE4PointModels
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_programme import SelectedE4PublicCalibration
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledReservation, identity as original_identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseArrays, ScheduledResponseProtocol
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from .preparation_experiment import MatrixPreparationSourceBank
from .protected_preparation_records import MatrixConfirmationSources, MatrixReservedTransferSources
from .preparation_records import MatrixCouplingRecipe, MatrixOriginalScheduleRecipe, coupling_recipe_types, is_baseline_recipe, validate_matched_preparation_menu
from .prepared_point import MatrixPreparedPublicSource
from .prepared_assay_method import MatrixPreparedAssayMethod, TOLERANCES
from .prepared_functional import _validate_matched_future_panels
from .prepared_response_science import MatrixPreparedResponsePanel, validate_prepared_panels
from .records import MatrixFunctionalCriterion, MatrixProgrammeCase, MatrixProgrammeRoster
from .configured_selected_public import ConfiguredMatrixSelectedPublicPackage


NAMESPACE = "matrix-selected-revision-prepared"
PHASES = ("E5_OPPORTUNITY", "E5_CONFIRMATION", "E6_TRANSFER")


@dataclass(frozen=True, slots=True)
class MatrixRevisionSelectedPackage(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/revision-selected-package"
    VERSION: ClassVar[str] = '3.0.0'
    record_id: str
    models: SelectedE4PointModels
    nomination: ObjectIdentity
    original_calibration: ObjectIdentity
    frozen_calibration: SelectedE4PublicCalibration | None = None
    reference_package: ConfiguredMatrixSelectedPublicPackage | None = None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.models) is not SelectedE4PointModels or type(self.nomination) is not ObjectIdentity
                or type(self.original_calibration) is not ObjectIdentity
                or self.nomination.object_schema != "empirical-lawhood/matrix-selected-e4/downstream-nomination"
                or self.original_calibration.object_schema != "empirical-lawhood/matrix-selected-e4/calibration"):
            raise TypeError("revision selection needs actual bounded coefficients and original CONF/CAL pins")
        for value in (self.models, self.nomination, self.original_calibration):
            value.__post_init__()
        if self.models.relation_fit is not None:
            from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_methods import SelectedE4DownstreamNomination
            if (type(self.frozen_calibration) is not SelectedE4PublicCalibration
                    or type(self.reference_package) is not ConfiguredMatrixSelectedPublicPackage):
                raise TypeError('matched downstream package requires the original E4 calibration radii and E3 reference models')
            self.frozen_calibration.__post_init__()
            self.reference_package.__post_init__()
            from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_fitting import MatchedEstimatorModel, MatchedCurveEstimatorModel
            if (not {'S0', 'B0'} <= {model.method_key for model in self.reference_package.models.models}
                    or any(type(model) is not (MatchedCurveEstimatorModel if self.reference_package.specification.is_curve_primary
                        else MatchedEstimatorModel) for model in self.reference_package.models.models)
                    or self.models.relation_fit.selection.is_curve_primary != self.reference_package.specification.is_curve_primary):
                raise ValueError('matched downstream package requires the unchanged paired58 S0/B0 reference accounts')
            calibration = self.frozen_calibration
            if ((calibration.original, calibration.specification.frozen_models, calibration.specification.nomination,
                    calibration.relation_fit, calibration.target, calibration.revision_model, calibration.baseline_model) !=
                    (self.original_calibration, self.models.frozen, self.models.development_nomination,
                     self.models.relation_fit.identity, self.models.target.identity, self.models.revision_model, self.models.baseline_model)
                    or self.nomination.object_version != SelectedE4DownstreamNomination.VERSION):
                raise ValueError('matched downstream package substitutes the original SR/BR fit or separate CAL')
        elif self.frozen_calibration is not None or self.reference_package is not None:
            raise ValueError('closed point-only package cannot acquire an amended downstream bound')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


@dataclass(frozen=True, slots=True)
class MatrixRevisionPreparedProgramme(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/revision-prepared-programme"
    VERSION: ClassVar[str] = "2.0.0"
    record_id: str
    phase: str
    selected_package: MatrixRevisionSelectedPackage
    sources: MatrixPreparationSourceBank | MatrixConfirmationSources | MatrixReservedTransferSources
    reservation: ScheduledReservation
    arms: tuple[tuple[str, MatrixCouplingRecipe | MatrixOriginalScheduleRecipe], ...]
    expected_groups: int
    assay: MatrixPreparedAssayMethod
    panels: tuple[tuple[str, tuple[MatrixPreparedResponsePanel, ...]], ...]
    criterion: MatrixFunctionalCriterion
    excluded_group_ids: tuple[str, ...]
    minimum_recoverable_groups: int
    tie_policy: str
    transfer_domain_claims: tuple[str, ...]
    preparation_nomination: ObjectIdentity | None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        expected_kind = {"E5_OPPORTUNITY": MatrixPreparationSourceBank,
            "E5_CONFIRMATION": MatrixConfirmationSources, "E6_TRANSFER": MatrixReservedTransferSources}
        if (self.phase not in expected_kind or type(self.sources) is not expected_kind[self.phase]
                or type(self.selected_package) is not MatrixRevisionSelectedPackage
                or type(self.reservation) is not ScheduledReservation or type(self.assay) is not MatrixPreparedAssayMethod
                or type(self.criterion) is not MatrixFunctionalCriterion or type(self.expected_groups) is not int or self.expected_groups < 1
                or type(self.arms) is not tuple or tuple(arm for arm, _ in self.arms) != tuple(sorted({arm for arm, _ in self.arms}))
                or any(type(recipe) not in coupling_recipe_types() for _, recipe in self.arms)
                or len(self.arms) != {"E5_OPPORTUNITY": 3, "E5_CONFIRMATION": 2, "E6_TRANSFER": 1}[self.phase]
                or sum(is_baseline_recipe(recipe) for _, recipe in self.arms) != 1
                or type(self.excluded_group_ids) is not tuple or self.excluded_group_ids != tuple(sorted(set(self.excluded_group_ids)))
                or type(self.minimum_recoverable_groups) is not int or self.minimum_recoverable_groups < 1
                or self.tie_policy not in ("LEXICAL_ARM_ID", "MINIMUM_TOTAL_EFFORT_THEN_LEXICAL")):
            raise ValueError("revision programme needs explicit complete source/arm/group and scientific decision selections")
        for value in (self.selected_package, self.sources, self.reservation, self.assay, self.criterion, *(recipe for _, recipe in self.arms)):
            value.__post_init__()
        matched = self.selected_package.models.relation_fit is not None
        if (self.criterion.is_matched != matched or matched and self.criterion.is_curve_primary !=
                self.selected_package.models.relation_fit.selection.is_curve_primary):
            raise ValueError("revision programme cannot mix closed functional criteria with the amended matched relation")
        if matched:
            validate_matched_preparation_menu(self.arms)
            from empirical_lawhood.adapters.methods.matrix_factor_response.origin_mechanics import MatrixOriginResponseModel
            if (type(self.assay.mechanical_model) is not MatrixOriginResponseModel
                    or self.expected_groups != {"E5_OPPORTUNITY": 16, "E5_CONFIRMATION": 80, "E6_TRANSFER": 64}[self.phase]
                    or self.minimum_recoverable_groups != 2 or self.tie_policy != "MINIMUM_TOTAL_EFFORT_THEN_LEXICAL"):
                raise ValueError("matched preparation changes its dense assay, DEV16/CONF80/transfer64 census or frozen nomination rule")
        for name in (*self.excluded_group_ids, *(arm for arm, _ in self.arms)):
            validate_stable_id(name)
        rows = self.source_arms()
        role = {"E5_OPPORTUNITY": MatrixProgrammeRole.DEVELOPMENT,
            "E5_CONFIRMATION": MatrixProgrammeRole.CONFIRMATION, "E6_TRANSFER": MatrixProgrammeRole.WITHHELD_TRANSFER}[self.phase]
        grouped = {}
        for arm, source in rows:
            source.__post_init__()
            unit = source.root.root.independent_group_id
            if (source.original.reservation != original_identity(self.reservation) or source.root.root.role is not role
                    or source.recipe != dict(self.arms)[arm] or source.recipe.effort_unit != self.criterion.effort_unit
                    or unit in self.excluded_group_ids or arm in grouped.setdefault(unit, {})):
                raise ValueError("revision programme substitutes original source/role/recipe or overlaps previously used groups")
            grouped[unit][arm] = source
        if any(set(values) != set(dict(self.arms)) for values in grouped.values()):
            raise ValueError("revision programme drops an assigned matched preparation arm")
        for values in grouped.values():
            first = next(iter(values.values()))
            if any(source.original != first.original or source.initial != first.initial for source in values.values()):
                raise ValueError("revision programme changes actual matched original starts or source")
        groups = tuple(sorted(grouped))
        if self.phase == "E6_TRANSFER":
            regimes = {}
            for _, source in rows:
                regimes.setdefault(source.root.root.regime_id, set()).add(source.root.root.independent_group_id)
            if len(regimes) != 2 or any(len(value) != self.expected_groups for value in regimes.values()):
                raise ValueError("revision transfer drops one separately declared complete original regime")
        if len(groups) != self.expected_groups * (2 if self.phase == "E6_TRANSFER" else 1):
            raise ValueError("revision programme changes its declared complete whole-group census")
        if type(self.panels) is not tuple or tuple(group for group, _ in self.panels) != groups:
            raise ValueError("revision programme omits actual future panels for an assigned group")
        _validate_matched_future_panels(self.panels)
        known = {seed for allocation in self.allocations for seed in allocation.exposure.census.effective_seed_exclusions}
        known.update(stream.effective_seed for allocation in self.allocations for root in allocation.roots for stream in root.streams)
        for _, panels in self.panels:
            for panel in panels:
                if panel.role == "INDEPENDENT_FUTURE":
                    for stream in panel.streams:
                        if stream.effective_seed in known:
                            raise ValueError("revision future reuses original exposed/allocated or another group's independent stream")
                        known.add(stream.effective_seed)
        target = self.selected_package.models.target
        if (self.assay.horizon_steps != target.horizon_ticks or self.assay.receiver_count != 48
                or tuple(target.numerical_views) != ("PRIMARY", "FINE")):
            raise ValueError("revision native assay changes the actual complete paired model endpoint geometry")
        for _, source in rows:
            validate_prepared_panels(source, dict(self.panels)[source.root.root.independent_group_id])
            self.protocol(source).__post_init__()
        if self.phase == "E5_CONFIRMATION":
            if type(self.preparation_nomination) is not ObjectIdentity or self.preparation_nomination.object_schema != "empirical-lawhood/matrix-experimental-programme/revision-programme-assessment":
                raise ValueError("revision CONF requires the actual original DEV recipe nomination")
        elif self.preparation_nomination is not None:
            raise ValueError("revision opportunity/transfer cannot invent a prior recipe nomination")
        if self.phase == "E6_TRANSFER":
            if (len(self.transfer_domain_claims) != 2 or any(value not in (
                    "INTERPOLATION_WITHIN_ASSESSED_DOMAIN", "EXTRAPOLATION_WITHIN_ASSESSED_DOMAIN") for value in self.transfer_domain_claims)):
                raise ValueError("revision transfer retains two explicit separate regime claims")
        elif self.transfer_domain_claims:
            raise ValueError("revision preparation cannot claim transfer regimes")
        self.roster.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    @property
    def allocations(self):
        return self.sources.allocations if type(self.sources) is MatrixPreparationSourceBank else (self.sources.closure.reservation.allocation,)

    @property
    def hold_arm_id(self):
        return next(arm for arm, recipe in self.arms if is_baseline_recipe(recipe))

    def source_arms(self):
        if type(self.sources) is MatrixPreparationSourceBank:
            arms = {recipe.identity: arm for arm, recipe in self.arms}
            if len(arms) != len(self.arms) or any(source.recipe.identity not in arms for source in self.sources.sources):
                raise ValueError("revision opportunity source uses an undeclared or aliased actual recipe")
            return tuple((arms[source.recipe.identity], source) for source in self.sources.sources)
        return self.sources.source_arms()

    @property
    def roster(self):
        cases = tuple(sorted((MatrixProgrammeCase("case." + source.source_id, arm, source.recipe.identity, source.original,
            source.initial.array_artifact, source.duration, source.recipe.effort,
            ObjectIdentity.from_record(source.coordinate.coordinate_id, source.coordinate), self.assay.identity, ())
            for arm, source in self.source_arms()), key=lambda row: row.case_id))
        return MatrixProgrammeRoster("roster.revision." + self.fingerprint(), self.phase, self.allocations, self.reservation, cases)

    def protocol(self, source):
        method = self.assay
        templates = ScheduledResponseArrays("templates.revision." + source.identity.object_fingerprint, "TEMPLATES", source.original.source,
            method.template_artifact, method.template_members, (source.original.source,), OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
        return ScheduledResponseProtocol("protocol.revision." + source.identity.object_fingerprint, source.original, method.criterion,
            method.mechanical_model, method.actions, method.horizon_steps, method.receiver_count, templates,
            *(getattr(method, name) for name in TOLERANCES), method.origin_rule)


@dataclass(frozen=True, slots=True)
class MatrixRevisionEntrySeal(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/revision-entry-seal"
    record_id: str
    programme: ObjectIdentity
    selected_package: ObjectIdentity
    source_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.programme) is not ObjectIdentity or self.programme.object_schema != MatrixRevisionPreparedProgramme.SCHEMA
                or type(self.selected_package) is not ObjectIdentity or self.selected_package.object_schema != MatrixRevisionSelectedPackage.SCHEMA
                or type(self.source_ids) is not tuple or not self.source_ids or self.source_ids != tuple(sorted(set(self.source_ids)))):
            raise ValueError("revision entry seal changes its exact complete programme/source/model census")
        for value in (self.programme, self.selected_package):
            value.__post_init__()
        for source in self.source_ids:
            validate_stable_id(source)


def entry_seal(programme):
    if type(programme) is not MatrixRevisionPreparedProgramme:
        raise TypeError("revision entry requires its exact declared programme")
    programme.__post_init__()
    return MatrixRevisionEntrySeal("entry." + programme.fingerprint(), programme.identity, programme.selected_package.identity,
        tuple(sorted(source.source_id for _, source in programme.source_arms())))


def global_node(programme, phase):
    return NAMESPACE + "." + phase + "." + programme.fingerprint()


@dataclass(frozen=True, slots=True)
class MatrixRevisionRootConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/revision-root-config"
    config_id: str
    programme: MatrixRevisionPreparedProgramme
    phase: str
    entry_evidence: ObjectIdentity | None = None
    entry_evidence_size_bytes: int | None = None

    def __post_init__(self):
        if (type(self.programme) is not MatrixRevisionPreparedProgramme or self.phase != "assess-programme"
                or self.config_id != "config." + global_node(self.programme, self.phase)):
            raise ValueError("revision root substitutes its actual programme or code-owned phase identity")
        self.programme.__post_init__()
        if self.entry_evidence is not None or self.entry_evidence_size_bytes is not None:
            raise ValueError("revision final reducer cannot reselect entry evidence")


@dataclass(frozen=True, slots=True)
class MatrixRevisionPreparedConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/revision-prepared-config"
    config_id: str
    programme: ObjectIdentity
    public_source: MatrixPreparedPublicSource
    phase: str
    selected_package: ObjectIdentity

    def __post_init__(self):
        if (type(self.programme) is not ObjectIdentity or self.programme.object_schema != MatrixRevisionPreparedProgramme.SCHEMA
                or type(self.public_source) is not MatrixPreparedPublicSource
                or self.phase not in ("measure", "frames", "project", "point", "mechanical")
                or self.config_id != "config." + NAMESPACE + "." + self.public_source.source.object_id + "." + self.phase
                or type(self.selected_package) is not ObjectIdentity or self.selected_package.object_schema != MatrixRevisionSelectedPackage.SCHEMA):
            raise ValueError("revision prepared phase changes its exact seedless source/model/programme selection")
        self.public_source.__post_init__()
