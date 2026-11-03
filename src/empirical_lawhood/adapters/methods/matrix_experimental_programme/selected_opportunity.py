# SPDX-License-Identifier: MPL-2.0
"""Selected E3 opportunity operands and the unchanged functional nomination.

The complete development comparison owns its original selected predictor and
all three matched arms. Original calibration is parent-only; neither this
development route nor a nomination establishes downstream applicability.
"""

from collections.abc import Mapping
from .preparation_records import is_baseline_recipe

from dataclasses import dataclass, replace
from types import SimpleNamespace
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledReservation, identity as original_identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseArrays, ScheduledResponseProtocol
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id

from .functional_case_reduction import _prepared_endpoint
from .functional_outcome_reduction import _nominate_functional_cases
from .preparation_experiment import MatrixPreparationSourceBank
from .prepared_assay_method import MatrixPreparedAssayMethod, TOLERANCES
from .prepared_forecast import MatrixPreparedMechanicalForecast
from .prepared_functional import _validate_matched_future_panels
from .prepared_point import MatrixPreparedPublicSource
from .prepared_prefix import identity
from .prepared_response_science import MatrixPreparedResponsePanel, MatrixPreparedResponseReadout, validate_prepared_panels
from .records import MatrixFunctionalCriterion, MatrixProgrammeCase, MatrixProgrammeRoster
from .science import MatrixFunctionalCaseResult
from .selected_entry import MatrixSelectedOriginalProduct
from .selected_point import MatrixSelectedPointDesign, MatrixSelectedPointForecast, forecast_selected_point
from .selected_public import MatrixSelectedPointPayload, package_identity, calibration_identity


NAMESPACE = "matrix-selected-opportunity"
SCOPE = "SELECTED_E3_EXPOSED_MATCHED_OPPORTUNITY_NO_PROTECTED_ENTRY_OR_DOWNSTREAM_APPLICABILITY"


@dataclass(frozen=True, slots=True)
class MatrixSelectedOpportunityProgramme(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-opportunity-programme"
    record_id: str
    sources: MatrixPreparationSourceBank
    reservation: ScheduledReservation
    point_design: MatrixSelectedPointDesign
    assay: MatrixPreparedAssayMethod
    panels: tuple[tuple[str, tuple[MatrixPreparedResponsePanel, ...]], ...]
    criterion: MatrixFunctionalCriterion
    minimum_recoverable_groups: int
    tie_policy: str

    def __post_init__(self):
        self._validate(MatrixSelectedPointDesign)

    def _validate(self, design_type):
        validate_stable_id(self.record_id)
        if (type(self.sources) is not MatrixPreparationSourceBank or type(self.reservation) is not ScheduledReservation
                or type(self.point_design) is not design_type or self.point_design.phase != "E5_OPPORTUNITY"
                or type(self.assay) is not MatrixPreparedAssayMethod or type(self.criterion) is not MatrixFunctionalCriterion
                or type(self.minimum_recoverable_groups) is not int or self.minimum_recoverable_groups < 1
                or self.tie_policy not in ("LEXICAL_ARM_ID", "MINIMUM_TOTAL_EFFORT_THEN_LEXICAL")):
            raise TypeError("selected opportunity requires exact development sources and explicit frozen nomination choices")
        for value in (self.sources, self.reservation, self.point_design, self.assay, self.criterion):
            value.__post_init__()
        by_source = {public.source: arm for arm, public in self.point_design.sources}
        if (set(by_source) != {source.identity for source in self.sources.sources}
                or any(source.original.reservation != original_identity(self.reservation) for source in self.sources.sources)
                or self.point_design.sources != tuple((by_source[source.identity], MatrixPreparedPublicSource.from_source(source)) for source in self.sources.sources)
                or any(source.recipe != dict(self.point_design.arms)[by_source[source.identity]] for source in self.sources.sources)
                or any(source.recipe.effort_unit != self.criterion.effort_unit for source in self.sources.sources)):
            raise ValueError("selected opportunity substitutes complete original sources, reservation, matched recipe or effort")
        groups = tuple(sorted({source.root.root.independent_group_id for source in self.sources.sources}))
        reserved = {*self.point_design.package.allocation.unit_ids("transfer_nearby"), *self.point_design.package.allocation.unit_ids("transfer_shifted")}
        if reserved.intersection(groups):
            raise ValueError("selected opportunity cannot consume an original pre-fit transfer-reserved whole group")
        if type(self.panels) is not tuple or tuple(group for group, _ in self.panels) != groups:
            raise ValueError("selected opportunity omits complete whole-group future panels")
        _validate_matched_future_panels(self.panels)
        known = {seed for allocation in self.sources.allocations for seed in allocation.exposure.census.effective_seed_exclusions}
        known.update(stream.effective_seed for allocation in self.sources.allocations for root in allocation.roots for stream in root.streams)
        for _, panels in self.panels:
            for panel in panels:
                if panel.role == "INDEPENDENT_FUTURE":
                    for stream in panel.streams:
                        if stream.effective_seed in known:
                            raise ValueError("selected opportunity independent future reuses an original exposed or allocated stream")
                        known.add(stream.effective_seed)
        measurement = self.point_design.package.specification.measurement
        if (self.assay.horizon_steps != measurement.horizons or self.assay.receiver_count != measurement.receiver_count
                or tuple(sorted((action.role, action.amplitude, action.pulse_steps) for action in self.assay.actions)) !=
                    tuple((role, measurement.action_amplitude, measurement.pulse_ticks) for role in measurement.actions)):
            raise ValueError("selected opportunity changes the actual selected response measurement")
        for source in self.sources.sources:
            validate_prepared_panels(source, dict(self.panels)[source.root.root.independent_group_id])
            self.protocol(source).__post_init__()
        self.roster.__post_init__()

    @property
    def identity(self):
        return identity(self)

    @property
    def phase(self):
        return "E5_OPPORTUNITY"

    @property
    def hold_arm_id(self):
        return next(arm for arm, recipe in self.point_design.arms if is_baseline_recipe(recipe))

    @property
    def roster(self):
        arms = {public.source: arm for arm, public in self.point_design.sources}
        cases = tuple(MatrixProgrammeCase("case." + source.source_id, arms[source.identity], source.recipe.identity, source.original,
            source.initial.array_artifact, source.duration, source.recipe.effort,
            ObjectIdentity.from_record(source.coordinate.coordinate_id, source.coordinate), self.assay.identity, ())
            for source in self.sources.sources)
        return MatrixProgrammeRoster("roster.selected-opportunity." + self.fingerprint(), self.phase, self.sources.allocations, self.reservation, cases)

    def protocol(self, source):
        method = self.assay
        templates = ScheduledResponseArrays("templates.selected-opportunity." + source.identity.object_fingerprint, "TEMPLATES", source.original.source,
            method.template_artifact, method.template_members, (source.original.source,), OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
        return ScheduledResponseProtocol("protocol.selected-opportunity." + source.identity.object_fingerprint, source.original, method.criterion,
            method.mechanical_model, method.actions, method.horizon_steps, method.receiver_count, templates,
            *(getattr(method, name) for name in TOLERANCES), method.origin_rule)


@dataclass(frozen=True, slots=True)
class MatrixSelectedOpportunityPublicProgramme(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-opportunity-public-programme"
    record_id: str
    original_programme: ObjectIdentity
    sources: MatrixPreparationSourceBank
    reservation: ScheduledReservation
    point_design: MatrixSelectedPointPayload
    assay: MatrixPreparedAssayMethod
    panels: tuple[tuple[str, tuple[MatrixPreparedResponsePanel, ...]], ...]
    criterion: MatrixFunctionalCriterion
    minimum_recoverable_groups: int
    tie_policy: str

    def __post_init__(self):
        if (type(self.original_programme) is not ObjectIdentity
                or self.original_programme.object_schema != MatrixSelectedOpportunityProgramme.SCHEMA):
            raise TypeError("selected opportunity projection requires its original full scientific programme pin")
        MatrixSelectedOpportunityProgramme._validate(self, MatrixSelectedPointPayload)

    @classmethod
    def from_programme(cls, programme):
        if type(programme) is not MatrixSelectedOpportunityProgramme:
            raise TypeError("selected opportunity projects its actual full programme")
        programme.__post_init__()
        return cls("public." + programme.record_id, programme.identity, programme.sources, programme.reservation,
            MatrixSelectedPointPayload.from_design(programme.point_design), programme.assay, programme.panels, programme.criterion,
            programme.minimum_recoverable_groups, programme.tie_policy)

    @property
    def identity(self):
        return identity(self)

    @property
    def phase(self):
        return "E5_OPPORTUNITY"

    @property
    def hold_arm_id(self):
        return MatrixSelectedOpportunityProgramme.hold_arm_id.fget(self)

    @property
    def roster(self):
        return replace(MatrixSelectedOpportunityProgramme.roster.fget(self),
            roster_id="roster.selected-opportunity." + self.original_programme.object_fingerprint)

    def protocol(self, source):
        return MatrixSelectedOpportunityProgramme.protocol(self, source)


def public_programme(programme):
    if type(programme) is MatrixSelectedOpportunityProgramme:
        return MatrixSelectedOpportunityPublicProgramme.from_programme(programme)
    if type(programme) is not MatrixSelectedOpportunityPublicProgramme:
        raise TypeError("selected opportunity requires its own exact full or public programme")
    programme.__post_init__()
    return programme


@dataclass(frozen=True, slots=True)
class MatrixSelectedOpportunityEvidence(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-opportunity-evidence"
    record_id: str
    programme: ObjectIdentity
    upstream_products: tuple[MatrixSelectedOriginalProduct, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.programme) is not ObjectIdentity or self.programme.object_schema != MatrixSelectedOpportunityProgramme.SCHEMA
                or type(self.upstream_products) is not tuple or len(self.upstream_products) != 4
                or any(type(value) is not MatrixSelectedOriginalProduct for value in self.upstream_products)
                or tuple(value.record.object_id for value in self.upstream_products) != tuple(sorted({value.record.object_id for value in self.upstream_products}))):
            raise TypeError("selected opportunity requires the four original selected producer locators, not asserted custody")
        for value in self.upstream_products:
            value.__post_init__()

    @property
    def identity(self):
        return identity(self)


def validate_opportunity_evidence(evidence, programme):
    programme = public_programme(programme)
    from .selected_original_commitments import MatrixSelectedOpportunityEvidenceV2
    if type(evidence) not in (MatrixSelectedOpportunityEvidence, MatrixSelectedOpportunityEvidenceV2):
        raise TypeError("selected opportunity requires exact original-product evidence")
    evidence.__post_init__()
    package = programme.point_design.package
    expected = {identity(package.models), identity(package.model_freeze), calibration_identity(package), identity(package.calibrated_freeze)}
    if evidence.programme != programme.original_programme or {value.record for value in evidence.upstream_products} != expected:
        raise ValueError("selected opportunity substitutes original selected package ancestry or programme")


@dataclass(frozen=True, slots=True)
class MatrixSelectedOpportunitySeal(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-opportunity-seal"
    record_id: str
    programme: ObjectIdentity
    sources: ObjectIdentity
    point_design: ObjectIdentity
    package: ObjectIdentity
    source_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.programme.object_schema != MatrixSelectedOpportunityPublicProgramme.SCHEMA
                or self.sources.object_schema != MatrixPreparationSourceBank.SCHEMA
                or self.point_design.object_schema != MatrixSelectedPointPayload.SCHEMA
                or not self.source_ids or self.source_ids != tuple(sorted(set(self.source_ids)))):
            raise ValueError("selected opportunity design seal changes its complete original selection")


def opportunity_seal(programme):
    programme = public_programme(programme)
    return MatrixSelectedOpportunitySeal("design." + programme.fingerprint(), programme.identity, programme.sources.identity,
        programme.point_design.identity, package_identity(programme.point_design.package), tuple(row.source_id for row in programme.sources.sources))


@dataclass(frozen=True, slots=True)
class MatrixSelectedOpportunityManifest(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-opportunity-manifest"
    record_id: str
    programme: ObjectIdentity
    rows: tuple[tuple[str, ObjectIdentity | None, ObjectIdentity | None, ObjectIdentity | None], ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.programme.object_schema != MatrixSelectedOpportunityPublicProgramme.SCHEMA or not self.rows
                or tuple(row[0] for row in self.rows) != tuple(sorted({row[0] for row in self.rows}))):
            raise ValueError("selected opportunity manifest omits complete sorted assigned cases")
        for _, point, mechanical, readout in self.rows:
            if point is None:
                if (mechanical, readout) != (None, None):
                    raise ValueError("selected opportunity manifest invents a partial observation")
            elif (point.object_schema != MatrixSelectedPointForecast.SCHEMA or mechanical is None or readout is None
                    or mechanical.object_schema != MatrixPreparedMechanicalForecast.SCHEMA
                    or readout.object_schema != MatrixPreparedResponseReadout.SCHEMA):
                raise ValueError("selected opportunity manifest substitutes actual numerical product types")

    @property
    def identity(self):
        return identity(self)


def nominate_selected_opportunity(programme, observations, *, result_id):
    """Reduce actual selected products; caller authenticates ordinary receipts."""
    programme = public_programme(programme)
    if not isinstance(observations, Mapping) or set(observations) - {case.case_id for case in programme.roster.cases}:
        raise ValueError("selected opportunity receives a case outside its complete assigned census")
    package, cases, manifest_rows = programme.point_design.package, [], []
    model = identity(package.models)
    operands = SimpleNamespace(identity=package_identity(package), component=lambda role: model)
    sources = {"case." + source.source_id: source for source in programme.sources.sources}
    for case in programme.roster.cases:
        observation = observations.get(case.case_id)
        if observation is None:
            cases.append(MatrixFunctionalCaseResult(case.case_id, case.unit_id, case.arm_id, "MISSING", None, None, None,
                False, False, None, False, case.preparation_effort, ("MISSING_ORIGINAL_FORECAST_OR_SCORE",)))
            manifest_rows.append((case.case_id, None, None, None))
            continue
        point, mechanical, readout = observation
        source, protocol = sources[case.case_id], programme.protocol(sources[case.case_id])
        panels = dict(programme.panels)[case.unit_id]
        if (type(point) is not MatrixSelectedPointForecast or type(mechanical) is not MatrixPreparedMechanicalForecast
                or type(readout) is not MatrixPreparedResponseReadout
                or point != forecast_selected_point(programme.point_design, point.feature, record_id=point.record_id)
                or point.feature.public_source != MatrixPreparedPublicSource.from_source(source)
                or mechanical.source != source.identity or readout.source != source.identity
                or mechanical.causal != point.feature.prefix or mechanical.original_protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
                or readout.original_protocol != mechanical.original_protocol or readout.preparation != mechanical.arrays.preparation
                or readout.panels != tuple(row.identity for row in panels)
                or readout.forecast is not None and readout.forecast != mechanical.arrays.identity):
            raise ValueError("selected opportunity substitutes actual pre-future forecasts or independent original readout")
        feature = point.feature
        feature_values = SimpleNamespace(source=feature.public_source.source, prefix=feature.prefix, values=feature.values,
            cutoff=source.coordinate.physical_time(source.total_ticks), family_id=programme.point_design.family(feature.public_source),
            frame_sha256=feature.frame_sha256, disposition=feature.disposition)
        common = {"package": point.package, "criterion": protocol.criterion, "feature": feature_values, "log_error_uppers": (None,) * 15}
        points = dict(point.log_points)
        observed = SimpleNamespace(point=SimpleNamespace(**common, log_error_points=points["SPECTRAL_RIDGE"]), mechanical=mechanical,
            readout=readout, comparator=SimpleNamespace(**common, model=model, log_error_points=points["ALL_ORIGIN_RIDGE"]))
        cases.append(_prepared_endpoint(programme.criterion, operands, case, source, observed, protocol=protocol, panels=panels))
        manifest_rows.append((case.case_id, identity(point), identity(mechanical), identity(readout)))
    manifest = MatrixSelectedOpportunityManifest(result_id + ".received", programme.identity, tuple(manifest_rows))
    nomination = _nominate_functional_cases(result_id=result_id, specification_identity=programme.original_programme,
        package_identity=package_identity(package), roster_identity=programme.roster.identity, evidence_identity=manifest.identity,
        group_ids=tuple(group for group, _ in programme.panels), arm_ids=tuple(arm for arm, _ in programme.point_design.arms),
        hold_arm_id=programme.hold_arm_id, criterion=programme.criterion, minimum_recoverable_groups=programme.minimum_recoverable_groups,
        tie_policy=programme.tie_policy, recipes=tuple((arm, recipe.identity) for arm, recipe in programme.point_design.arms), cases=tuple(cases))
    return manifest, nomination
