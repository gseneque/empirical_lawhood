# SPDX-License-Identifier: MPL-2.0
"""Separate paired CONF and reserved E6 selections and numerical consumers.

Original protected sources, package/nomination custody and prior reservation
remain independent prerequisites. These calculations neither confer issue/reveal
authority nor change the original conditional assessment qualification standing.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledForecastDesign
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseArrays, ScheduledResponseProtocol
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteResult, CanonicalTaskReceipt

from .functional_case_reduction import _prepared_endpoint
from .functional_outcome_reduction import _confirmation_comparisons, _transfer_comparisons
from .prepared_assay_method import MatrixPreparedAssayMethod, TOLERANCES
from .prepared_functional import MatrixPreparedFunctionalObservation, MatrixPreparedFunctionalSpecification, _validate_matched_future_panels
from .prepared_forecast import MatrixPreparedMechanicalForecast
from .prepared_point import MatrixPreparedPointDesign, MatrixPreparedPointSeal, MatrixPreparedPublicSource, MatrixPreparedRecipeInterpretation
from .prepared_response_science import MatrixPreparedResponseReadout
from .prepared_response_science import MatrixPreparedResponsePanel, validate_prepared_panels
from .protected_point import MatrixPreparedComparatorMethod
from .protected_preparation_records import MatrixConfirmationSources, MatrixReservedTransferSources
from .records import MatrixFrozenConsumerPackage, MatrixFunctionalCriterion, MatrixProgrammeCase, MatrixProgrammeRoster
from .science import MatrixFunctionalAssessment, MatrixFunctionalCaseResult, MatrixPreparationNomination
from .selection_metadata import validate_phase_metadata
from .source_selection_metadata import _validate_source_metadata


def _reference(value, kind):
    if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
        raise ValueError("protected selection substitutes an exact scientific owner or revision")
    value.__post_init__()


def _criterion(criterion, expected_groups):
    if type(criterion) is not MatrixFunctionalCriterion or type(expected_groups) is not int or expected_groups < 1:
        raise TypeError("protected selection requires its explicit functional criterion and whole-group denominator")
    criterion.__post_init__()
    if max(criterion.minimum_usable_groups, criterion.minimum_admitted_groups) > expected_groups:
        raise ValueError("protected functional criterion exceeds its complete assigned population")


@dataclass(frozen=True, slots=True)
class MatrixPreparationConfirmationSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/preparation-confirmation-specification"
    record_id: str
    question: str
    sources: ObjectIdentity
    package: ObjectIdentity
    comparator: ObjectIdentity
    assay_method: ObjectIdentity
    criterion: MatrixFunctionalCriterion
    expected_groups: int
    hold_arm_id: str
    selected_arm_id: str
    nomination: ObjectIdentity
    tie_policy: str

    def __post_init__(self):
        for value in (self.record_id, self.hold_arm_id, self.selected_arm_id):
            validate_stable_id(value)
        for value, kind in ((self.sources, MatrixConfirmationSources), (self.package, MatrixFrozenConsumerPackage),
                (self.comparator, MatrixPreparedComparatorMethod), (self.assay_method, MatrixPreparedAssayMethod), (self.nomination, MatrixPreparationNomination)):
            _reference(value, kind)
        _criterion(self.criterion, self.expected_groups)
        if (not isinstance(self.question, str) or not self.question.strip() or self.hold_arm_id == self.selected_arm_id
                or self.tie_policy not in ("LEXICAL_ARM_ID", "MINIMUM_TOTAL_EFFORT_THEN_LEXICAL")):
            raise ValueError("paired confirmation omits its selected recipe/HOLD and original frozen rule")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    @property
    def phase(self):
        return "E5_CONFIRMATION"

    @property
    def arm_ids(self):
        return tuple(sorted((self.hold_arm_id, self.selected_arm_id)))

    @property
    def transfer_regime_ids(self):
        return ()

    @property
    def transfer_domain_claims(self):
        return ()


@dataclass(frozen=True, slots=True)
class MatrixReservedTransferSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/reserved-transfer-specification"
    record_id: str
    question: str
    sources: ObjectIdentity
    package: ObjectIdentity
    comparator: ObjectIdentity
    assay_method: ObjectIdentity
    criterion: MatrixFunctionalCriterion
    expected_groups: int
    hold_arm_id: str
    transfer_regime_ids: tuple[str, ...]
    transfer_domain_claims: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        validate_stable_id(self.hold_arm_id)
        for value, kind in ((self.sources, MatrixReservedTransferSources), (self.package, MatrixFrozenConsumerPackage),
                (self.comparator, MatrixPreparedComparatorMethod), (self.assay_method, MatrixPreparedAssayMethod)):
            _reference(value, kind)
        _criterion(self.criterion, self.expected_groups)
        if (not isinstance(self.question, str) or not self.question.strip()
                or type(self.transfer_regime_ids) is not tuple or len(self.transfer_regime_ids) != 2 or len(set(self.transfer_regime_ids)) != 2
                or type(self.transfer_domain_claims) is not tuple or len(self.transfer_domain_claims) != 2
                or any(value not in ("INTERPOLATION_WITHIN_ASSESSED_DOMAIN", "EXTRAPOLATION_WITHIN_ASSESSED_DOMAIN") for value in self.transfer_domain_claims)):
            raise ValueError("transfer requires its two separately classified whole reserved regimes")
        for value in self.transfer_regime_ids:
            validate_stable_id(value)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    @property
    def phase(self):
        return "E6_TRANSFER"

    @property
    def arm_ids(self):
        return (self.hold_arm_id,)

    @property
    def nomination(self):
        return None


@dataclass(frozen=True, slots=True)
class MatrixProtectedFunctionalSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/protected-functional-selection"
    record_id: str
    specification: MatrixPreparationConfirmationSpecification | MatrixReservedTransferSpecification
    sources: MatrixConfirmationSources | MatrixReservedTransferSources
    package: MatrixFrozenConsumerPackage
    original_point_method: ScheduledForecastDesign
    interpretations: tuple[MatrixPreparedRecipeInterpretation, ...]
    comparator: MatrixPreparedComparatorMethod
    assay_method: MatrixPreparedAssayMethod
    future_panels: tuple[tuple[str, tuple[MatrixPreparedResponsePanel, ...]], ...]
    nomination: MatrixPreparationNomination | None
    nomination_publication: ArtifactWriteResult | None
    nomination_receipt: CanonicalTaskReceipt | None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        confirmation = type(self.specification) is MatrixPreparationConfirmationSpecification
        if (type(self.specification) not in (MatrixPreparationConfirmationSpecification, MatrixReservedTransferSpecification)
                or type(self.sources) is not (MatrixConfirmationSources if confirmation else MatrixReservedTransferSources)
                or type(self.package) is not MatrixFrozenConsumerPackage or type(self.original_point_method) is not ScheduledForecastDesign
                or type(self.comparator) is not MatrixPreparedComparatorMethod or type(self.assay_method) is not MatrixPreparedAssayMethod
                or type(self.interpretations) is not tuple or any(type(row) is not MatrixPreparedRecipeInterpretation for row in self.interpretations)):
            raise TypeError("protected functional selection requires its separate exact phase/source/method owners")
        for value in (self.specification, self.sources, self.package, self.original_point_method, self.comparator, self.assay_method):
            value.__post_init__()
        selected = self.specification
        if (selected.sources != self.sources.identity or selected.package != self.package.identity or selected.comparator != self.comparator.identity
                or selected.assay_method != self.assay_method.identity or selected.hold_arm_id != self.sources.hold_arm_id
                or selected.criterion.effort_unit != self.sources.source_arms()[0][1].recipe.effort_unit):
            raise ValueError("protected selection substitutes its original source/package/method/criterion/effort choices")
        self.comparator.validate_package(self.package)
        training_groups = {row[1] for row in self.original_point_method.training_record.roles.rows if row[3] == "TRAIN"}
        if not training_groups <= set(self.package.training_unit_ids):
            raise ValueError("protected package omits known original main-model fitted whole groups")
        original_criterion = self.original_point_method.criterion_record
        if (self.assay_method.criterion != self.package.component("criterion")
                or self.assay_method.horizon_steps != original_criterion.horizon_steps
                or self.assay_method.receiver_gram_tolerance != original_criterion.receiver_gram_tolerance
                or tuple(sorted((a.role, a.amplitude, a.force_norm, a.pulse_steps) for a in self.assay_method.actions)) !=
                    tuple(sorted((a.role, a.amplitude, a.force_norm, a.pulse_steps) for a in original_criterion.action_scales))):
            raise ValueError("protected assay changes the unchanged frozen response criterion")
        sources = tuple(row for _, row in self.sources.source_arms())
        groups = tuple(sorted({row.root.root.independent_group_id for row in sources}))
        if (type(self.future_panels) is not tuple or tuple(group for group, _ in self.future_panels) != groups
                or any(row.recipe.effort_unit != selected.criterion.effort_unit for row in sources)):
            raise ValueError("protected future selection omits complete whole groups or original effort units")
        _validate_matched_future_panels(self.future_panels)
        allocation = self.sources.closure.reservation.allocation
        known_seeds = set(allocation.exposure.census.effective_seed_exclusions)
        known_seeds.update(stream.effective_seed for root in allocation.roots for stream in root.streams)
        for _, panels in self.future_panels:
            for panel in panels:
                if panel.role == "INDEPENDENT_FUTURE":
                    for stream in panel.streams:
                        if stream.effective_seed in known_seeds:
                            raise ValueError("protected independent future reuses an exposed, original allocated or other future stream")
                        known_seeds.add(stream.effective_seed)
        for source in sources:
            validate_prepared_panels(source, dict(self.future_panels)[source.root.root.independent_group_id])
            self._protocol(source).__post_init__()
        # Constructors reprove original immutable model/reservation/feature scope.
        self.point_design.__post_init__()
        roster = self.roster
        allocation, _ = _validate_source_metadata(phase=selected.phase, roster_reference=roster.identity,
            package_reference=selected.package, expected_groups=selected.expected_groups, arm_ids=selected.arm_ids,
            transfer_regime_ids=selected.transfer_regime_ids, selection_sha256=selected.fingerprint(), roster=roster, package=self.package)
        validate_phase_metadata(selected, roster, self.package, allocation, self.nomination)
        if confirmation:
            if self.nomination.selected_arm_id != selected.selected_arm_id:
                raise ValueError("confirmation changes the actual development-selected unchanged arm")
            self._nomination_custody()
        elif (self.nomination, self.nomination_publication, self.nomination_receipt) != (None, None, None):
            raise ValueError("reserved transfer cannot depend on E5 preparation selection or its outcomes")

    def _nomination_custody(self):
        if (type(self.nomination) is not MatrixPreparationNomination or type(self.nomination_publication) is not ArtifactWriteResult
                or type(self.nomination_receipt) is not CanonicalTaskReceipt):
            raise TypeError("confirmation needs its actual original development nomination publication and ordinary receipt")
        publication, receipt = self.nomination_publication, self.nomination_receipt
        for value in (self.nomination, publication, receipt):
            value.__post_init__()
        _reference(self.nomination.specification, MatrixPreparedFunctionalSpecification)
        raw = self.nomination.canonical_bytes()
        if (receipt.operational_status is not OperationalStatus.SUCCEEDED
                or publication.logical not in receipt.output_logical_artifacts or publication.materialization not in receipt.output_materializations
                or publication.logical.payload_schema != self.nomination.SCHEMA
                or publication.logical.media_type != "application/json"
                or publication.logical.profile is not ArtifactProfile.CANONICAL_JSON
                or publication.logical.content_sha256 != self.nomination.fingerprint()
                or publication.materialization.physical_sha256 != self.nomination.fingerprint()
                or publication.materialization.size_bytes != len(raw)
                or publication.logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or publication.logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
            raise ValueError("confirmation substitutes its exact original nonpromotable nomination bytes/receipt")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    @property
    def point_design(self):
        sources = tuple(sorted((MatrixPreparedPublicSource.from_source(row) for _, row in self.sources.source_arms()), key=lambda row: row.source.object_id))
        return MatrixPreparedPointDesign("point-design.protected." + self.specification.fingerprint(), self.package,
            self.original_point_method, sources, self.interpretations)

    @property
    def roster(self):
        closure = self.sources.closure
        cases = tuple(sorted((MatrixProgrammeCase("case." + source.source_id, arm, source.recipe.identity, source.original,
            source.initial.array_artifact, source.duration, source.recipe.effort,
            ObjectIdentity.from_record(source.coordinate.coordinate_id, source.coordinate), self.assay_method.identity, ())
            for arm, source in self.sources.source_arms()), key=lambda row: row.case_id))
        return MatrixProgrammeRoster("roster.protected." + self.specification.fingerprint(), self.specification.phase,
            (closure.reservation.allocation,), closure.reservation, cases)

    def protocol(self, source):
        if source not in tuple(row for _, row in self.sources.source_arms()):
            raise ValueError("protected assay requests an unselected actual prepared subject")
        return self._protocol(source)

    def _protocol(self, source):
        method = self.assay_method
        templates = ScheduledResponseArrays("templates.protected." + source.identity.object_fingerprint, "TEMPLATES", source.original.source,
            method.template_artifact, method.template_members, (source.original.source,), OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
        return ScheduledResponseProtocol("protocol.protected." + source.identity.object_fingerprint, source.original, method.criterion,
            method.mechanical_model, method.actions, method.horizon_steps, method.receiver_count, templates,
            *(getattr(method, name) for name in TOLERANCES), method.origin_rule)


@dataclass(frozen=True, slots=True)
class MatrixProtectedFunctionalManifest(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/protected-functional-manifest"
    record_id: str
    selection: ObjectIdentity
    rows: tuple[tuple[str, ObjectIdentity | None, ObjectIdentity | None, ObjectIdentity | None, ObjectIdentity | None], ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        _reference(self.selection, MatrixProtectedFunctionalSelection)
        if (type(self.rows) is not tuple or not self.rows
                or any(type(row) is not tuple or len(row) != 5 for row in self.rows)):
            raise ValueError("protected manifest requires its exact complete assigned observation rows")
        if (tuple(row[0] for row in self.rows) != tuple(sorted({row[0] for row in self.rows}))
                or any(row[1] is None and row[2:] != (None, None, None) for row in self.rows)):
            raise ValueError("protected manifest omits complete assigned cases or invents partial received observations")
        kinds = (MatrixPreparedPointSeal, MatrixPreparedMechanicalForecast, MatrixPreparedResponseReadout, MatrixPreparedPointSeal)
        for case_id, *products in self.rows:
            validate_stable_id(case_id)
            if products[0] is not None:
                for value, kind in zip(products, kinds, strict=True):
                    _reference(value, kind)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


def protected_case_result(selection, case, source, observation):
    """Own protected guards, followed by the unchanged original endpoint math."""
    if type(selection) is not MatrixProtectedFunctionalSelection or type(case) is not MatrixProgrammeCase:
        raise TypeError("protected endpoint requires its exact separate selected owner")
    selection.__post_init__()
    if case not in selection.roster.cases or source not in tuple(row for _, row in selection.sources.source_arms()):
        raise ValueError("protected endpoint receives an unassigned original source/case")
    return _case_result(selection, case, source, observation, point_design=selection.point_design, protocol=selection._protocol(source))


def _case_result(selection, case, source, observation, *, point_design, protocol):
    package, criterion = selection.package, selection.specification.criterion
    if (case.case_id != "case." + source.source_id or case.public_source != source.original
            or case.recipe != source.recipe.identity or case.initial_state != source.initial.array_artifact):
        raise ValueError("protected endpoint changes original matched source, recipe or initial state")
    if observation is None:
        return MatrixFunctionalCaseResult(case.case_id, case.unit_id, case.arm_id, "MISSING", None, None, None,
            False, False, None, False, case.preparation_effort, ("MISSING_ORIGINAL_PREPARED_FORECAST_OR_READOUT",))
    if type(observation) is not MatrixPreparedFunctionalObservation or observation.case_id != case.case_id or observation.comparator is None:
        raise TypeError("protected endpoint requires its actual assigned point/comparator/mechanical/readout products")
    point, mechanical, score = observation.point, observation.mechanical, observation.readout
    observation.__post_init__()
    for value in (point, mechanical, score, observation.comparator):
        value.__post_init__()
    comparator = observation.comparator
    if (comparator.feature != point.feature or comparator.package != package.identity
            or comparator.model != package.component("comparator") or comparator.criterion != package.component("criterion")):
        raise ValueError("protected comparator changes its frozen original model/package or identical actual causal feature")
    panels = dict(selection.future_panels)[case.unit_id]
    if (point.package != package.identity or point.model != package.component("model") or point.criterion != package.component("criterion")
            or point.feature.design != point_design.identity or point.feature.source != source.identity
            or mechanical.source != source.identity or score.source != source.identity or point.feature.prefix != mechanical.causal
            or score.preparation != mechanical.arrays.preparation or score.original_protocol != mechanical.original_protocol
            or score.original_protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
            or mechanical.mechanical_model != ObjectIdentity.from_record(protocol.mechanical_model.model_id, protocol.mechanical_model)
            or score.panels != tuple(panel.identity for panel in panels)
            or score.forecast is not None and score.forecast != mechanical.arrays.identity
            or (point.feature.root_id, point.feature.independent_group_id, point.feature.clock_id) !=
                (source.root.root.root_id, case.unit_id, source.root.root.clock_id)
            or point.feature.cutoff != source.coordinate.physical_time(source.total_ticks)):
        raise ValueError("protected endpoint substitutes actual frozen model/source/cutoff or original complete assay")
    return _prepared_endpoint(criterion, package, case, source, observation, protocol=protocol, panels=panels)


def assess_protected_functional(selection, observations, *, result_id):
    if type(selection) is not MatrixProtectedFunctionalSelection or not isinstance(observations, Mapping):
        raise TypeError("protected assessment requires its exact selected owner and received observation mapping")
    selection.__post_init__()
    roster, specification = selection.roster, selection.specification
    if set(observations) - {case.case_id for case in roster.cases}:
        raise ValueError("protected assessment receives an unassigned case outside the complete original census")
    sources = {"case." + source.source_id: source for _, source in selection.sources.source_arms()}
    point_design = selection.point_design
    cases = tuple(_case_result(selection, case, sources[case.case_id], observations.get(case.case_id), point_design=point_design,
        protocol=selection._protocol(sources[case.case_id])) for case in roster.cases)
    rows = []
    for case in roster.cases:
        observed = observations.get(case.case_id)
        rows.append((case.case_id, None, None, None, None) if observed is None else (case.case_id,
            *(ObjectIdentity.from_record(value.record_id, value) for value in (observed.point, observed.mechanical, observed.readout, observed.comparator))))
    manifest = MatrixProtectedFunctionalManifest(result_id + ".received", selection.identity, tuple(rows))
    if type(specification) is MatrixPreparationConfirmationSpecification:
        groups = tuple(sorted({case.unit_id for case in roster.cases}))
        comparisons = _confirmation_comparisons(specification.criterion, groups, specification.selected_arm_id, specification.hold_arm_id, cases)
    else:
        regimes = tuple((regime, tuple(sorted({case.unit_id for case in roster.cases if case.public_source.root.regime_id == regime})))
            for regime in specification.transfer_regime_ids)
        comparisons = _transfer_comparisons(specification.criterion, regimes, specification.transfer_domain_claims, specification.hold_arm_id, cases)
    used = {row.comparison_id for row in comparisons}
    result = MatrixFunctionalAssessment(result_id, specification.identity, selection.package.identity, roster.identity, manifest.identity,
        None if selection.nomination is None else selection.nomination.identity, comparisons, cases,
        tuple(slot for slot in specification.criterion.family_slots if slot not in used))
    return manifest, result
