# SPDX-License-Identifier: MPL-2.0
"""Prepared-subject functional criteria and exact original source joins.

Future outcomes are ports, not pre-known evidence fingerprints in a selection.
No prepared response is converted into an old scheduled score or forecast.
Original sampling and applicability premises retain their separate standing.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseProtocol
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id

from .prepared_assay_composition import MatrixPreparedAssayProgramme
from .prepared_assay_method import MatrixPreparedAssayMethod
from .prepared_point import MatrixPreparedPointSeal
from .prepared_forecast import MatrixPreparedMechanicalForecast
from .prepared_response_science import MatrixPreparedResponsePanel, MatrixPreparedResponseReadout, validate_prepared_panels
from .preparation_records import MatrixPreparationSource
from .records import PHASES, MatrixFrozenConsumerPackage, MatrixFunctionalCriterion, MatrixProgrammeCase, MatrixProgrammeRoster
from .science import MatrixFunctionalCaseResult
from .selection_metadata import validate_phase_metadata
from .source_selection_metadata import _validate_source_metadata


@dataclass(frozen=True, slots=True)
class MatrixPreparedFunctionalSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-functional-specification"
    record_id: str
    phase: str
    assay: ObjectIdentity
    assay_method: ObjectIdentity
    roster: ObjectIdentity
    package: ObjectIdentity
    case_sources: tuple[tuple[str, ObjectIdentity], ...]
    criterion: MatrixFunctionalCriterion
    expected_groups: int
    arm_ids: tuple[str, ...]
    hold_arm_id: str
    nomination: ObjectIdentity | None
    minimum_recoverable_groups: int
    tie_policy: str
    transfer_regime_ids: tuple[str, ...]
    transfer_domain_claims: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.assay, MatrixPreparedAssayProgramme), (self.assay_method, MatrixPreparedAssayMethod),
                (self.roster, MatrixProgrammeRoster), (self.package, MatrixFrozenConsumerPackage)):
            if type(value) is not ObjectIdentity or value.object_schema != kind.SCHEMA or value.object_version != kind.VERSION:
                raise ValueError("prepared functional specification substitutes its exact original programme/roster/package")
        if (self.phase not in PHASES or type(self.criterion) is not MatrixFunctionalCriterion
                or type(self.expected_groups) is not int or self.expected_groups < 1
                or type(self.arm_ids) is not tuple or not self.arm_ids or self.arm_ids != tuple(sorted(set(self.arm_ids)))
                or self.hold_arm_id not in self.arm_ids or type(self.minimum_recoverable_groups) is not int or self.minimum_recoverable_groups < 1
                or self.tie_policy not in ("LEXICAL_ARM_ID", "MINIMUM_TOTAL_EFFORT_THEN_LEXICAL")
                or type(self.case_sources) is not tuple or not self.case_sources
                or tuple(key for key, _ in self.case_sources) != tuple(sorted({key for key, _ in self.case_sources}))
                or any(type(value) is not ObjectIdentity or value.object_schema != MatrixPreparationSource.SCHEMA for _, value in self.case_sources)
                or type(self.transfer_regime_ids) is not tuple or type(self.transfer_domain_claims) is not tuple):
            raise ValueError("prepared functional specification omits complete cases, explicit criteria or frozen selection rules")
        self.criterion.__post_init__()
        for value in (*self.arm_ids, *self.transfer_regime_ids, *(key for key, _ in self.case_sources)):
            validate_stable_id(value)
        if self.phase != "E5_OPPORTUNITY" and (self.criterion.minimum_usable_groups > self.expected_groups or self.criterion.minimum_admitted_groups > self.expected_groups):
            raise ValueError("prepared functional coverage exceeds the complete assigned population")
        if self.phase == "E5_OPPORTUNITY":
            if len(self.arm_ids) != 3 or self.nomination is not None or self.transfer_regime_ids or self.transfer_domain_claims:
                raise ValueError("prepared opportunity requires HOLD and two fixed recipes before nomination")
        elif self.phase == "E5_CONFIRMATION":
            if (len(self.arm_ids) != 2 or type(self.nomination) is not ObjectIdentity or self.transfer_regime_ids or self.transfer_domain_claims
                    or self.nomination.object_schema != "empirical-lawhood/matrix-experimental-programme/preparation-nomination"):
                raise ValueError("prepared confirmation requires its actual frozen original nomination")
        elif (len(self.arm_ids) != 1 or self.nomination is not None or len(self.transfer_regime_ids) != 2
                or len(set(self.transfer_regime_ids)) != 2 or len(self.transfer_domain_claims) != 2
                or any(value not in ("INTERPOLATION_WITHIN_ASSESSED_DOMAIN", "EXTRAPOLATION_WITHIN_ASSESSED_DOMAIN") for value in self.transfer_domain_claims)):
            raise ValueError("prepared transfer requires both distinct untouched complete regimes")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


def _validate_matched_future_panels(rows):
    """One complete original pair of future definitions per matched group."""
    selected = {}
    for unit_id, panels in rows:
        validate_stable_id(unit_id)
        if (type(panels) is not tuple or len(panels) != 2 or any(type(row) is not MatrixPreparedResponsePanel for row in panels)
                or tuple(row.panel_id for row in panels) != tuple(sorted({row.panel_id for row in panels}))
                or tuple(sorted(row.role for row in panels)) != ("COMMON_NOISE_PANEL", "INDEPENDENT_FUTURE")
                or any(row.independent_group_id != unit_id for row in panels)):
            raise ValueError("prepared functional matching omits its exact two whole-group future definitions")
        for panel in panels:
            panel.__post_init__()
        if selected.setdefault(unit_id, panels) != panels:
            raise ValueError("prepared functional matching changes the complete common/independent future panel definitions across arms")


def validate_prepared_functional_selection(specification, roster, package, programme, *, assay_method, nomination=None):
    """Metadata only; the exact original matching/freshness consumer is reused."""
    if (type(specification) is not MatrixPreparedFunctionalSpecification or type(roster) is not MatrixProgrammeRoster
            or type(package) is not MatrixFrozenConsumerPackage or type(programme) is not MatrixPreparedAssayProgramme
            or type(assay_method) is not MatrixPreparedAssayMethod):
        raise TypeError("prepared functional selection requires its own exact specification and original record owners")
    for value in (specification, roster, package, programme, assay_method):
        value.__post_init__()
    if (specification.assay != programme.identity or specification.assay_method != assay_method.identity
            or programme.prediction.point_design.package != package
            or tuple(key for key, _ in specification.case_sources) != tuple(case.case_id for case in roster.cases)):
        raise ValueError("prepared functional selection changes original complete programme/package/case census")
    sources = {source.identity: source for source in programme.prediction.sources.sources}
    if {value for _, value in specification.case_sources} != set(sources) or len(specification.case_sources) != len(sources):
        raise ValueError("prepared functional selection drops, duplicates or substitutes an actual prepared source")
    matched_panels = []
    for case in roster.cases:
        source = sources[dict(specification.case_sources)[case.case_id]]
        protocol = dict(programme.prediction.protocols)[source.source_id]
        assay_method.validate_protocol(protocol)
        panels = dict(programme.panels)[source.source_id]
        matched_panels.append((case.unit_id, panels))
        if (case.public_source != source.original or case.recipe != source.recipe.identity or case.initial_state != source.initial.array_artifact
                or case.preparation_duration != source.duration or case.preparation_effort != source.recipe.effort
                or specification.criterion.effort_unit != source.recipe.effort_unit
                or case.assay != assay_method.identity):
            raise ValueError("prepared functional selection crosses actual source, shared initial state, recipe, effort, duration or fixed assay")
    _validate_matched_future_panels(tuple(matched_panels))
    allocation, design = _validate_source_metadata(phase=specification.phase, roster_reference=specification.roster,
        package_reference=specification.package, expected_groups=specification.expected_groups, arm_ids=specification.arm_ids,
        transfer_regime_ids=specification.transfer_regime_ids, selection_sha256=specification.fingerprint(), roster=roster, package=package)
    validate_phase_metadata(specification, roster, package, allocation, nomination)
    return allocation, design


@dataclass(frozen=True, slots=True)
class MatrixPreparedFunctionalObservation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-functional-observation"
    case_id: str
    point: MatrixPreparedPointSeal
    mechanical: MatrixPreparedMechanicalForecast
    readout: MatrixPreparedResponseReadout
    comparator: MatrixPreparedPointSeal | None

    def __post_init__(self):
        validate_stable_id(self.case_id)
        if (type(self.point) is not MatrixPreparedPointSeal or type(self.mechanical) is not MatrixPreparedMechanicalForecast
                or type(self.readout) is not MatrixPreparedResponseReadout
                or self.comparator is not None and type(self.comparator) is not MatrixPreparedPointSeal):
            raise TypeError("prepared functional observation requires actual separate prepared numerical subjects")


@dataclass(frozen=True, slots=True)
class MatrixPreparedFunctionalManifest(CanonicalRecord):
    """Exact received numerical identities, including every assigned missing case."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-functional-manifest"
    record_id: str
    specification: ObjectIdentity
    roster: ObjectIdentity
    package: ObjectIdentity
    rows: tuple[tuple[str, ObjectIdentity | None, ObjectIdentity | None, ObjectIdentity | None, ObjectIdentity | None], ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.rows) is not tuple or not self.rows or any(type(row) is not tuple or len(row) != 5 for row in self.rows)
                or tuple(row[0] for row in self.rows) != tuple(sorted({row[0] for row in self.rows}))):
            raise ValueError("prepared functional manifest omits its complete assigned case census")
        for value, kind in ((self.specification, MatrixPreparedFunctionalSpecification), (self.roster, MatrixProgrammeRoster), (self.package, MatrixFrozenConsumerPackage)):
            if type(value) is not ObjectIdentity or value.object_schema != kind.SCHEMA or value.object_version != kind.VERSION:
                raise ValueError("prepared functional manifest substitutes its exact selected scientific owner")
        for row in self.rows:
            if type(row) is not tuple or len(row) != 5:
                raise ValueError("prepared functional manifest changes its complete pre-future/readout identity fields")
            validate_stable_id(row[0])
            if row[1] is None:
                if row[2:] != (None, None, None):
                    raise ValueError("prepared functional manifest invents a partially received observation")
                continue
            for index, (value, kind) in enumerate(zip(row[1:], (MatrixPreparedPointSeal, MatrixPreparedMechanicalForecast, MatrixPreparedResponseReadout, MatrixPreparedPointSeal), strict=True)):
                if value is None and index == 3:
                    continue
                if type(value) is not ObjectIdentity or value.object_schema != kind.SCHEMA or value.object_version != kind.VERSION:
                    raise ValueError("prepared functional manifest crosses original prepared numerical subjects")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


def nominate_prepared_opportunity(specification, roster, package, programme, observations, *, assay_method, result_id):
    """One outcome worker's complete original functional opportunity reduction.

    This executes no source or fitting method. The owning operation must first
    authenticate actual point/mechanical/readout dependency receipts. Protected
    confirmation and transfer need their separate source/entry owner.
    """
    if type(specification) is not MatrixPreparedFunctionalSpecification or specification.phase != "E5_OPPORTUNITY":
        raise ValueError("prepared opportunity nomination requires its exact exposed development specification")
    allocation, _ = validate_prepared_functional_selection(specification, roster, package, programme, assay_method=assay_method)
    if not isinstance(observations, Mapping) or set(observations) - {case.case_id for case in roster.cases}:
        raise ValueError("prepared opportunity receives an observation outside its complete assigned source census")
    sources = {source.identity: source for source in programme.prediction.sources.sources}
    protocols, panels = dict(programme.prediction.protocols), dict(programme.panels)
    cases = []
    for case in roster.cases:
        source = sources[dict(specification.case_sources)[case.case_id]]
        cases.append(prepared_case_result(specification, package, case, source, observations.get(case.case_id),
            protocol=protocols[source.source_id], panels=panels[source.source_id]))
    cases = tuple(cases)
    manifest_rows = []
    for case in roster.cases:
        observed = observations.get(case.case_id)
        manifest_rows.append((case.case_id, None, None, None, None) if observed is None else
            (case.case_id, ObjectIdentity.from_record(observed.point.record_id, observed.point),
             ObjectIdentity.from_record(observed.mechanical.record_id, observed.mechanical),
             ObjectIdentity.from_record(observed.readout.record_id, observed.readout),
             None if observed.comparator is None else ObjectIdentity.from_record(observed.comparator.record_id, observed.comparator)))
    manifest = MatrixPreparedFunctionalManifest(result_id + ".received", specification.identity, roster.identity, package.identity, tuple(manifest_rows))
    from .functional_outcome_reduction import _nominate_functional_cases

    nomination = _nominate_functional_cases(result_id=result_id, specification_identity=specification.identity,
        package_identity=package.identity, roster_identity=roster.identity, evidence_identity=manifest.identity,
        group_ids=allocation.unit_ids(), arm_ids=specification.arm_ids, hold_arm_id=specification.hold_arm_id,
        criterion=specification.criterion, minimum_recoverable_groups=specification.minimum_recoverable_groups,
        tie_policy=specification.tie_policy,
        recipes=tuple((arm, next(case.recipe for case in roster.cases if case.arm_id == arm)) for arm in specification.arm_ids), cases=cases)
    return manifest, nomination


def prepared_case_result(specification, package, case, source, observation, *, protocol, panels):
    """Original complete functional endpoint over the real prepared readout.

    The owning worker authenticates ordinary readout/point dependency receipts.
    Point-only prepared forecasts stay unbounded; a reference or support label
    can never create a conditional admission here.
    """
    if (type(specification) is not MatrixPreparedFunctionalSpecification or type(package) is not MatrixFrozenConsumerPackage
            or type(source) is not MatrixPreparationSource or type(case) is not MatrixProgrammeCase or type(protocol) is not ScheduledResponseProtocol):
        raise TypeError("prepared functional result requires its own original selected scientific operands")
    for value in (specification, package, case, source):
        value.__post_init__()
    protocol.__post_init__()
    if protocol.horizon_steps != (16, 64, 128) or protocol.receiver_count != 48:
        raise ValueError("prepared functional endpoint requires the original complete fixed horizon/48-receiver scope")
    validate_prepared_panels(source, panels)
    if (specification.package != package.identity or dict(specification.case_sources).get(case.case_id) != source.identity
            or case.public_source != source.original or case.recipe != source.recipe.identity or case.assay != specification.assay_method
            or case.initial_state != source.initial.array_artifact or case.preparation_effort != source.recipe.effort
            or case.preparation_duration != source.duration or protocol.public_source != source.original):
        raise ValueError("prepared functional result changes the exact selected actual source/case/method/package")
    if observation is None:
        return MatrixFunctionalCaseResult(case.case_id, case.unit_id, case.arm_id, "MISSING", None, None, None,
            False, False, None, False, case.preparation_effort, ("MISSING_ORIGINAL_PREPARED_FORECAST_OR_READOUT",))
    if type(observation) is not MatrixPreparedFunctionalObservation or observation.case_id != case.case_id:
        raise TypeError("prepared functional result receives an unassigned or foreign observation owner")
    point, mechanical, score, criterion = observation.point, observation.mechanical, observation.readout, specification.criterion
    if (point.package != package.identity or point.model != package.component("model") or point.criterion != package.component("criterion")
            or point.feature.source != source.identity or mechanical.source != source.identity or score.source != source.identity
            or point.feature.prefix != mechanical.causal or score.preparation != mechanical.arrays.preparation
            or score.original_protocol != mechanical.original_protocol
            or score.original_protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
            or score.panels != tuple(panel.identity for panel in panels)
            or score.forecast is not None and score.forecast != mechanical.arrays.identity
            or (point.feature.root_id, point.feature.independent_group_id, point.feature.clock_id) !=
                (source.root.root.root_id, case.unit_id, source.root.root.clock_id)
            or point.feature.cutoff != source.coordinate.physical_time(source.total_ticks)):
        raise ValueError("prepared functional result substitutes actual pre-future model/source/cutoff or original complete assay")
    from .functional_case_reduction import _prepared_endpoint

    return _prepared_endpoint(criterion, package, case, source, observation, protocol=protocol, panels=panels)
