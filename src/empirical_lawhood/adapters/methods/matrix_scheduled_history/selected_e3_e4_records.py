# SPDX-License-Identifier: MPL-2.0
"""Selected E3 account and truthful exposed E4 acquisition contracts.

These distinct schemas preserve historical scheduled records. The original
physical source, streams, clock, response instrument and fitted E3 parameters
remain their existing typed records. No original calibration scores occur here.
"""

from empirical_lawhood.kernel.decoding import validate_record_fields
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_public import MatrixSelectedPublicPackage
from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_public import ConfiguredMatrixSelectedPublicPackage
from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_methods import METHODS
from empirical_lawhood.adapters.methods.matrix_factor_response.response_frontier import MatrixResponseFrontierProtocol
from empirical_lawhood.adapters.methods.matrix_factor_response.origin_mechanics import model_predictors
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import METHODS as FACTOR_METHODS
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import METHODS as HISTORY_METHODS, MatrixParameterHistoryControl, MatrixParameterNumericalDesign
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, require_sorted_unique_ids, validate_decimal, validate_stable_id
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactWriteResult

from .commitment import ScheduledExposureAudit
from .continuation import ScheduledFullArrays, ScheduledFullHistory, validate_full_native_evidence
from .forecast import ScheduledForecastFeature, ScheduledPublicSource
from .programme_reduction import ScheduledProgrammeNativeDisposition, ScheduledProgrammeReceiptReference
from .programme_records import ScheduledProgramme, ScheduledProgrammeCase, ScheduledProgrammeFactor, ScheduledProgrammeWave
from .programme_roster import validate_programme_roster
from .records import (ScheduledArrays, ScheduledCheckpoint, ScheduledCausalPrefix, ScheduledFrameAssessment, ScheduledNativeEvidence,
    ScheduledPrefixHistory, ScheduledPrefixPolicy, ScheduledPrefixTrace, ScheduledPrefixWitness, ScheduledReservation, ScheduledSource, ScheduledSpecification,
    _validate_prefix_native_evidence, identity)
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import (
    MatrixE4SecondaryReadoutSelection,
)

from .response_records import ScheduledResponseArrays, ScheduledResponseForecast, ScheduledResponseNative, ScheduledResponseScore, branch_census
from .response_selection import ScheduledResponseSelection

NAMESPACE = "matrix-selected-e3-e4-development"
POINT_ONLY = "PRIMARY_FIT_POINT_ONLY_NO_E4_CALIBRATION_OR_TRANSPORT_WARRANT"
DEV, EXPOSED = OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY


def pin(record, field="record_id"):
    return ObjectIdentity.from_record(getattr(record, field), record)


def exact_pin(value, kind):
    if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
        raise ValueError("selected E3/E4 substitutes an exact versioned scientific operand")
    validate_record_fields(value)


def selected_e3_fit_target(package):
    return ('PAIRED_CUMULATIVE_LOG1P_FACTOR58' if getattr(package.specification.measurement, 'is_matched', False)
        else 'PRIMARY_CUMULATIVE_LOG1P_ALL15')


@dataclass(frozen=True, slots=True)
class SelectedE3E4ForecastDesign(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/forecast-design"
    VERSION: ClassVar[str] = "2.0.0"
    record_id: str
    package: MatrixSelectedPublicPackage | ConfiguredMatrixSelectedPublicPackage
    allocation: ObjectIdentity
    criterion_record: MatrixResponseFrontierProtocol
    criterion_publication: ArtifactWriteResult
    fit_target: str = "PRIMARY_CUMULATIVE_LOG1P_ALL15"
    uncertainty_status: str = POINT_ONLY

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.package) not in (MatrixSelectedPublicPackage, ConfiguredMatrixSelectedPublicPackage) or type(self.criterion_record) is not MatrixResponseFrontierProtocol
                or self.fit_target != selected_e3_fit_target(self.package) or self.uncertainty_status != POINT_ONLY):
            raise TypeError("selected E4 account requires actual public E3 parameters and explicit original point meaning")
        from .records import ScheduledAllocation, _publication
        exact_pin(self.allocation, ScheduledAllocation)
        validate_record_fields(self.criterion_record)
        _publication(self.criterion_publication, self.criterion_record)
        validate_record_fields(self.package)
        measurement, criterion = self.package.specification.measurement, self.criterion_record
        if (criterion.primary_timestep != measurement.primary_timestep or criterion.horizon_steps != measurement.horizons
                or any(getattr(criterion, name) != getattr(measurement, name) for name in ("panel_roles", "estimand", "metric", "aggregation"))
                or tuple((value.role, value.amplitude, value.pulse_steps) for value in criterion.action_scales) !=
                    tuple((role, measurement.action_amplitude, measurement.pulse_ticks) for role in measurement.actions)):
            raise ValueError("selected E4 criterion substitutes the frozen E3 response measurement")

        if self.package.specification.calibration_target_view != "MAX_PAIRED_VIEWS":
            raise ValueError("selected E4 cannot change the original paired-view calibration scope")

    @property
    def identity(self):
        return pin(self)

    @property
    def criterion(self):
        return self.criterion_record.identity


def selected_original_factor_rule(criterion):
    """Exact full rule already retained in the original mathematical protocol."""
    from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import FactorEventSpec
    matches = {value.target.canonical_bytes(): value.target for value in criterion.factor_rule_compatibilities
        if value.target.identity == criterion.factor_rule and type(value.target) is FactorEventSpec}
    if len(matches) != 1:
        raise ValueError("selected E4 lacks its exact original full factor-rule operand")
    return next(iter(matches.values()))


def validate_selected_prefix_projection(criterion, policy, cutoff_tick):
    """Replay original full-to-prefix mathematics; never establish its custody.

    Keep the retained E3 projection owner unchanged. This selected consumer uses
    its exact field census; authentic original projection pins are checked by
    the parent against the actual original fit/physical producer inputs.
    """
    from dataclasses import fields
    from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import FactorEventSpec
    from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import MatrixParameterScalarDefinition
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_protocol import (
        ORIGINAL_SCALAR_SOURCE_BYTES, ORIGINAL_SCALAR_SOURCE_SHA256,
    )
    full, rule = selected_original_factor_rule(criterion), policy.factor_rule
    excluded = {"spec_id", "lattice", "scalar_closure", "exposure"}
    if (policy.cutoff_tick != cutoff_tick or policy.origin_sector != "Y"
            or rule.lattice != tuple(tick for tick in full.lattice if tick <= cutoff_tick)
            or rule.lattice[-1] != cutoff_tick
            or any(getattr(rule, field.name) != getattr(full, field.name)
                for field in fields(FactorEventSpec) if field.name not in excluded)
            or full.scalar_closure is None or rule.scalar_closure is None
            or full.scalar_closure.threshold != rule.scalar_closure.threshold
            or (full.scalar_closure.normalization_owner.sha256, full.scalar_closure.normalization_owner.size_bytes) !=
                (ORIGINAL_SCALAR_SOURCE_SHA256, ORIGINAL_SCALAR_SOURCE_BYTES)
            or (rule.scalar_closure.normalization_owner.payload_schema, rule.scalar_closure.normalization_owner.media_type) !=
                (MatrixParameterScalarDefinition.SCHEMA, "application/json")):
        raise ValueError("selected E4 changes the exact original full-to-prefix factor/scalar projection")


def validate_selected_error_design(protocol, design):
    """Use the selected original projection without relaxing generic schedules."""
    criterion, public = design.criterion_record, protocol.public_source
    if criterion.factor_rule == public.policy.factor_rule.identity:
        return protocol.validate_error_design(design)
    validate_selected_prefix_projection(criterion, public.policy, design.package.specification.measurement.origin_tick)
    if (protocol.criterion != design.criterion or protocol.horizon_steps != criterion.horizon_steps
            or protocol.receiver_count != 48 or protocol.receiver_gram_tolerance != criterion.receiver_gram_tolerance
            or public.allocation != design.allocation or public.coordinate.q != 2
            or criterion.primary_timestep != public.coordinate.primary_view.timestep
            or tuple(sorted((a.role, a.amplitude, a.force_norm, a.pulse_steps) for a in protocol.actions)) !=
                tuple(sorted((a.role, a.amplitude, a.force_norm, a.pulse_steps) for a in criterion.action_scales))):
        raise ValueError("selected E4 response differs from its exact original target/menu/physical clock")


@dataclass(frozen=True, slots=True)
class SelectedE3E4Design(CanonicalRecord):
    """Declared population and original supported full factorial instrument."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/design"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    group_count: int
    confidence: Decimal
    factors: tuple[ScheduledProgrammeFactor, ...]
    wave_group_count: int
    family_sampling_rule: str = 'BALANCED_FIXED_FOUR_FAMILY_GROUPS'

    def __post_init__(self):
        from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
        validate_stable_id(self.record_id)
        families = tuple(FOUR_FAMILY_PREPARATION_IDS)
        if (self.family_sampling_rule not in ('BALANCED_FIXED_FOUR_FAMILY_GROUPS', 'IID_UNIFORM_FOUR_FAMILIES_NO_REDRAW')
                or type(self.group_count) is not int or self.group_count < 1
                or self.family_sampling_rule == 'BALANCED_FIXED_FOUR_FAMILY_GROUPS'
                    and (self.group_count < len(families) or self.group_count % len(families))
                or type(self.confidence) is not Decimal or not self.confidence.is_finite() or not 0 < self.confidence < 1
                or type(self.factors) is not tuple
                or tuple(value.factor_id for value in self.factors) != ("temperature", "friction", "coupling")
                or any(type(value) is not ScheduledProgrammeFactor for value in self.factors)
                or type(self.wave_group_count) is not int or not 1 <= self.wave_group_count <= 8):
            raise ValueError("selected E4 requires explicit groups, confidence, supported factorial axes and whole-wave subdivision")
        for value in self.factors:
            validate_record_fields(value)

    @property
    def identity(self):
        return pin(self)

    @property
    def cases_per_group(self):
        # This supported three-axis method measures every binary corner plus
        # the joint center. A different grid needs a different scientific method.
        return 2 ** len(self.factors) + 1


def require_e4_reserved_physical_exclusion(coordinates, original_reservation):
    """Compare actual full reserved regimes; names and new groups confer no separation."""
    from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
    from .records import coordinate_identity, physical_key
    if (type(original_reservation) is not ScheduledReservation or type(coordinates) is not tuple
            or any(type(value) is not MatrixParameterCoordinate for value in coordinates)):
        raise TypeError("selected E4 physical exclusion requires actual coordinates and original reservation")
    validate_record_fields(original_reservation)
    allocation = original_reservation.allocation
    reserved = {value.coordinate for value in allocation.roots
        if value.root.role is MatrixProgrammeRole.WITHHELD_TRANSFER}
    withheld_keys = {physical_key(value) for value in allocation.coordinates if coordinate_identity(value) in reserved}
    if withheld_keys.intersection(physical_key(value) for value in coordinates):
        raise ValueError("selected E4 consumes an original reserved E6 full physical key")


@dataclass(frozen=True, slots=True)
class SelectedE3E4DevelopmentBank(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/development-bank"
    bank_id: str
    reservation: ScheduledReservation
    specification: ScheduledSpecification
    provenances: tuple[NumericalProducingProvenance, ...]
    sources: tuple[ScheduledSource, ...]
    audit: ScheduledExposureAudit
    audit_publication: ArtifactWriteResult
    forecast_design: SelectedE3E4ForecastDesign
    response_selection: ScheduledResponseSelection
    response_selection_publication: ArtifactWriteResult
    design: SelectedE3E4Design

    def __post_init__(self):
        self._validate_role(MatrixProgrammeRole.DEVELOPMENT)

    def _validate_role(self, expected_role):
        validate_stable_id(self.bank_id)
        expected = ((self.reservation, ScheduledReservation), (self.specification, ScheduledSpecification),
            (self.audit, ScheduledExposureAudit), (self.forecast_design, SelectedE3E4ForecastDesign),
            (self.response_selection, ScheduledResponseSelection), (self.design, SelectedE3E4Design))
        for value, kind in expected:
            if type(value) is not kind:
                raise TypeError("selected E4 bank requires its exact original scientific source and selected forecast owners")
            validate_record_fields(value)
        require_sorted_unique_ids(self.sources, attribute="root_id", field_name="selected development source census")
        if (len(self.sources) != self.design.group_count * self.design.cases_per_group or any(type(value) is not ScheduledSource for value in self.sources)
                or type(self.provenances) is not tuple or not self.provenances
                or any(type(value) is not NumericalProducingProvenance for value in self.provenances)
                or tuple(value.fingerprint() for value in self.provenances) != tuple(sorted({value.fingerprint() for value in self.provenances}))
                or {value.provenance for value in self.sources} != {value.identity for value in self.provenances}
                or self.forecast_design.allocation != identity(self.reservation.allocation)
                or {value.public_source.root.root_id for value in self.response_selection.protocols} != {value.root_id for value in self.sources}):
            raise ValueError("selected E4 bank must retain its declared complete factorial development groups and all assay protocols")
        from .records import _publication
        _publication(self.audit_publication, self.audit)
        self.response_selection.validate_allocation(self.reservation.allocation)
        _publication(self.response_selection_publication, self.response_selection)
        groups = tuple(sorted({value.root.root.independent_group_id for value in self.sources}))
        package, measurement = self.forecast_design.package, self.forecast_design.package.specification.measurement
        if getattr(measurement, 'is_matched', False):
            expected_sampling = ('BALANCED_FIXED_FOUR_FAMILY_GROUPS' if expected_role is MatrixProgrammeRole.DEVELOPMENT
                else 'IID_UNIFORM_FOUR_FAMILIES_NO_REDRAW')
            if self.design.family_sampling_rule != expected_sampling:
                raise ValueError('matched E4 changes balanced DEV or independent uniform CAL/CONF family allocation')
            criterion = self.response_selection.calibration_criterion
            if expected_role is MatrixProgrammeRole.CALIBRATION and (
                    criterion.required_family_ids or criterion.construction_estimand !=
                    'WHOLE_GROUP_MAX_POSITIVE_PAIRED_LOG_RESIDUAL_NINE_COORDINATES_FACTOR58'):
                raise ValueError('matched E4 calibration changes its paired58 target or redraws missing families')
        package.require_unused_groups(groups)
        reserves = {*package.allocation.unit_ids("transfer_nearby"), *package.allocation.unit_ids("transfer_shifted")}
        if len(groups) != self.design.group_count or reserves.intersection(groups):
            raise ValueError("selected E4 development cannot consume original fit/selection or pre-fit transfer reserves")
        index=self.source_index()
        index.require_roster(self.sources,expected_root_ids=tuple(value.root.root_id
            for value in self.reservation.allocation.roots if value.root.role is expected_role))
        for descriptor in self.sources:
            source = self.source(descriptor.root_id,index=index)
            self.audit.validate_source(source)
            protocol, _ = self.response_selection.validate_source(source)
            validate_selected_error_design(protocol, self.forecast_design)
            if (source.root.root.role is not expected_role
                    or source.policy.cutoff_tick != measurement.origin_tick or source.policy.origin_sector != "Y"
                    or (source.coordinate.primary_view.timestep, source.coordinate.fine_view.timestep) != (measurement.primary_timestep, measurement.fine_timestep)
                    or protocol.criterion != self.forecast_design.criterion or protocol.horizon_steps != measurement.horizons
                    or protocol.receiver_count != measurement.receiver_count
                    or tuple(sorted((action.role, action.amplitude, action.pulse_steps) for action in protocol.actions)) !=
                        tuple((role, measurement.action_amplitude, measurement.pulse_ticks) for role in measurement.actions)):
                raise ValueError("selected E4 source changes actual role, selected origin, paired clocks or original four-action response measurement")

    @property
    def identity(self):
        return pin(self, "bank_id")

    def source_index(self):
        from .source_index import ScheduledSourceIndex
        return ScheduledSourceIndex.from_shared(reservation=self.reservation,
            specification=self.specification,provenances=self.provenances)

    def source(self, root_id, *, index):
        descriptor = next((value for value in self.sources if value.root_id == root_id), None)
        if descriptor is None:
            raise ValueError("selected E4 source lies outside its complete declared bank")
        if (index.reservation is not self.reservation or index.specification is not self.specification
                or index.provenances!=self.provenances):
            raise ValueError("selected E4 source index changes its actual shared bank parents")
        return index.resolve(descriptor)


@dataclass(frozen=True, slots=True)
class SelectedE3E4DevelopmentProgramme(ScheduledProgramme):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/development-programme"
    design: SelectedE3E4Design

    def __post_init__(self):
        if type(self.design) is not SelectedE3E4Design:
            raise TypeError("selected E4 programme requires its explicit original design")
        validate_record_fields(self.design)
        if self.factors != self.design.factors:
            raise ValueError("selected E4 programme changes its declared factor grid")
        validate_programme_roster(self, bank_schema=SelectedE3E4DevelopmentBank.SCHEMA,
            declared_group_count=self.design.group_count, declared_confidence=self.design.confidence,
            family_sampling_rule=self.design.family_sampling_rule)
        if self.design.family_sampling_rule != 'BALANCED_FIXED_FOUR_FAMILY_GROUPS':
            raise ValueError('E4 DEV requires its preassigned balanced four-family fitting bank')
        if self.mode != "E4_DEVELOPMENT":
            raise ValueError("selected E3/E4 development cannot relabel separate CAL or CONF populations")
        exact_pin(self.forecast_design, SelectedE3E4ForecastDesign)

    @classmethod
    def from_selected_bank(cls, bank, *, programme_id):
        if type(bank) is not SelectedE3E4DevelopmentBank:
            raise TypeError("selected E4 programme requires its actual bank and explicit bounded whole-group subdivisions")
        validate_record_fields(bank)
        return cls(*selected_programme_fields(bank, programme_id=programme_id, mode="E4_DEVELOPMENT"))

def selected_programme_fields(bank, *, programme_id, mode):
    cases = []
    index=bank.source_index()
    for descriptor in bank.sources:
        source = bank.source(descriptor.root_id,index=index)
        coordinate = source.coordinate
        cases.append(ScheduledProgrammeCase(source.root_id, source.root.root.independent_group_id, coordinate.family_id,
            source.root.root.role.value, descriptor.identity, descriptor.coordinate,
            (coordinate.primary_view.bath_temperature, coordinate.primary_view.friction_gamma, coordinate.member.cross_coupling_gamma),
            sha256(canonical_json_bytes(source.root.streams)).hexdigest(),
            InformationCutoff("cutoff." + source.root_id, coordinate.clock_id, CausalPhase.PRE_ACTION,
                coordinate.physical_time(source.policy.cutoff_tick))))
    cases = tuple(cases)
    factors, wave_group_count = bank.design.factors, bank.design.wave_group_count
    groups = tuple(sorted({value.independent_group_id for value in cases}))
    waves = tuple(ScheduledProgrammeWave(f"{programme_id}.wave.{index // wave_group_count:03}", groups[index:index + wave_group_count],
        tuple(value.root_id for value in cases if value.independent_group_id in groups[index:index + wave_group_count]))
        for index in range(0, len(groups), wave_group_count))
    criterion = bank.response_selection.calibration_criterion
    return (programme_id, mode, bank.identity, identity(bank.reservation), identity(bank.reservation.allocation),
        identity(bank.specification), bank.forecast_design.identity, bank.response_selection.identity, bank.forecast_design.criterion,
        None if criterion is None else criterion.identity, factors, cases, tuple(value.identity for value in bank.sources), waves,
        bank.design.confidence, bank.design.group_count, bank.design)


def validate_development_bank(programme, bank):
    if type(programme) is not SelectedE3E4DevelopmentProgramme or type(bank) is not SelectedE3E4DevelopmentBank or programme.bank != bank.identity:
        raise TypeError("selected E4 requires exact original programme and typed bank")
    rebuilt = SelectedE3E4DevelopmentProgramme.from_selected_bank(bank, programme_id=programme.programme_id)
    if rebuilt != programme:
        raise ValueError("selected E4 programme changes original full source/grid/stream/cutoff/forecast joins")


@dataclass(frozen=True, slots=True)
class SelectedE3E4Evidence(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/original-e3-evidence"
    VERSION: ClassVar[str] = "2.0.0"
    record_id: str
    programme: ObjectIdentity
    upstream_products: tuple[MatrixSelectedOriginalProduct, ...]
    produced_input_parents: tuple[ArtifactLineageParent, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        exact_pin(self.programme, SelectedE3E4DevelopmentProgramme)
        if (type(self.upstream_products) is not tuple or len(self.upstream_products) != 4
                or any(type(value) is not MatrixSelectedOriginalProduct for value in self.upstream_products)
                or tuple(value.record.object_id for value in self.upstream_products) != tuple(sorted({value.record.object_id for value in self.upstream_products}))):
            raise TypeError("selected E4 requires four exact original issued E3 model/freeze/calibration producer locators")
        for value in self.upstream_products:
            validate_record_fields(value)
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import validate_produced_input_parents
        validate_produced_input_parents(self.produced_input_parents)
        expected = {pin for value in self.upstream_products for pin in (value.record, value.prior_execution.receipt)}
        if {value.identity for value in self.produced_input_parents} != expected:
            raise ValueError("selected E4 DEV changes its complete original produced-parent census")

    @property
    def identity(self):
        return pin(self)


def validate_evidence(evidence, programme, bank):
    if type(evidence) is not SelectedE3E4Evidence:
        raise TypeError("selected E4 requires exact original E3 product evidence")
    validate_record_fields(evidence)
    validate_development_bank(programme, bank)
    package = bank.forecast_design.package
    expected = {identity(package.models), identity(package.model_freeze), package.calibration, identity(package.calibrated_freeze)}
    if evidence.programme != programme.identity or {value.record for value in evidence.upstream_products} != expected:
        raise ValueError("selected E4 substitutes its actual original model/calibration/freeze products")


@dataclass(frozen=True, slots=True)
class SelectedE3E4Arrays(ScheduledArrays):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/development-arrays"

    def __post_init__(self):
        from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
        validate_stable_id(self.operand_id)
        require_sorted_unique_ids(self.members, attribute="name", field_name="development array members")
        require_sorted_unique_ids(self.producers, attribute="object_id", field_name="development array producers")
        if ((self.source.object_schema,self.source.object_version) != (ScheduledSource.SCHEMA,ScheduledSource.VERSION) or self.role not in ("PREFIX", "PREFIX_DIAGNOSTICS", "CAUSAL_STATE")
                or not self.members or not self.producers or self.array_artifact.payload_schema != MATRIX_ARRAY_SCHEMA
                or self.array_artifact.media_type != "application/x-npz" or not 0 < self.array_artifact.size_bytes <= MAXIMUM_MATRIX_ARRAY_BYTES
                or sum(value.size_bytes for value in self.members) > MAXIMUM_MATRIX_ARRAY_BYTES
                or self.outcome_access is not DEV or self.visibility_ceiling is not EXPOSED):
            raise ValueError("selected E4 arrays change original complete members or exposed development classification")


@dataclass(frozen=True, slots=True)
class SelectedE3E4PrefixHistory(ScheduledPrefixHistory):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/prefix-history"
    arrays: SelectedE3E4Arrays

    def __post_init__(self):
        validate_stable_id(self.history_id)
        if (type(self.arrays) is not SelectedE3E4Arrays or self.arrays.role != "PREFIX" or self.source != self.arrays.source
                or type(self.checkpoint) is not ScheduledCheckpoint or self.checkpoint.source != self.source
                or type(self.native) is not ScheduledNativeEvidence):
            raise ValueError("selected E4 prefix loses its complete original checkpoint/native evidence")

    def validate_source(self, source, *, config=None):
        if config is None:
            raise PermissionError("selected E4 prefix validation requires its actual installed compact configuration")
        from .selected_e3_e4_bindings import native_contract
        configuration, parent_task, operation, sources = native_contract(config, source,
            recorded_operation=self.native.definition.operation_id)
        self.checkpoint.validate_source(source, self.arrays)
        _validate_prefix_native_evidence(self, source, configuration=configuration, parent_task=parent_task,
            operation=operation, native_sources=set(sources), output_access=DEV, output_visibility=EXPOSED)


@dataclass(frozen=True, slots=True)
class SelectedE3E4NumericalAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/numerical-assessment"
    assessment_id: str
    phase: str
    source: ObjectIdentity
    history: ObjectIdentity
    numerical_design: ObjectIdentity
    controls: tuple[MatrixParameterHistoryControl, ...]
    numerical_pass: bool

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        kind = SelectedE3E4PrefixHistory if self.phase == "prefix" else SelectedE3E4FullHistory if self.phase == "full" else None
        if (kind is None or self.history.object_schema != kind.SCHEMA or (self.source.object_schema,self.source.object_version) != (ScheduledSource.SCHEMA,ScheduledSource.VERSION)
                or type(self.controls) is not tuple or any(type(value) is not MatrixParameterHistoryControl for value in self.controls)
                or tuple(value.control_id for value in self.controls) != HISTORY_METHODS or type(self.numerical_pass) is not bool
                or self.numerical_pass != all(value.disposition == "SATISFIED" for value in self.controls)):
            raise ValueError("selected E4 numerical assessment loses full original paired transition controls")
        n = self.controls[0].denominator_steps
        if tuple((value.denominator_steps, value.denominator_real_coordinates) for value in self.controls) != (
                (n, 192), (2 * n, 192), (n, 192), (n, 96)):
            raise ValueError("selected E4 numerical assessment changes original complete transition denominators")


@dataclass(frozen=True, slots=True)
class SelectedE3E4Witness(ScheduledPrefixWitness):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/prefix-witness"
    arrays: SelectedE3E4Arrays

    def __post_init__(self):
        validate_stable_id(self.product_id)
        exact_pin(self.history, SelectedE3E4PrefixHistory)
        exact_pin(self.numerical, SelectedE3E4NumericalAssessment)
        if (type(self.arrays) is not SelectedE3E4Arrays or self.arrays.role != "PREFIX_DIAGNOSTICS"
                or self.arrays.source != self.source or type(self.traces) is not tuple or any(type(value) is not ScheduledPrefixTrace for value in self.traces)
                or tuple((value.view, value.sector) for value in self.traces) !=
                    (("PRIMARY", "X"), ("PRIMARY", "Y"), ("FINE", "X"), ("FINE", "Y"))):
            raise ValueError("selected E4 witness drops its actual causal lattice, complete traces or diagnostic members")


@dataclass(frozen=True, slots=True)
class SelectedE3E4Frames(ScheduledFrameAssessment):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/frame-assessment"

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        exact_pin(self.witness, SelectedE3E4Witness)
        if (tuple(value.method for value in self.controls) != FACTOR_METHODS or type(self.numerical_pass) is not bool
                or self.numerical_pass != all(value.disposition in ("SATISFIED", "NOT_APPLICABLE") for value in self.controls)):
            raise ValueError("selected E4 frame assessment loses independent original eigenpair controls")
        n = len(self.controls[0].measured_errors)
        if (tuple(len(value.measured_errors) for value in self.controls) != (n, 15 * n, n, n, n, n)
                or tuple(value.denominator_real_coordinates for value in self.controls) != (225, 15, 225, 225, 48, 1)):
            raise ValueError("selected E4 frame assessment thins original paired eigenpair denominators")


@dataclass(frozen=True, slots=True)
class SelectedE3E4CausalPrefix(ScheduledCausalPrefix):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/causal-prefix"
    arrays: SelectedE3E4Arrays

    def __post_init__(self):
        validate_stable_id(self.prefix_id)
        for value, kind in ((self.history, SelectedE3E4PrefixHistory), (self.numerical, SelectedE3E4NumericalAssessment),
                (self.witness, SelectedE3E4Witness), (self.frame_assessment, SelectedE3E4Frames)):
            exact_pin(value, kind)
        if (type(self.arrays) is not SelectedE3E4Arrays or self.arrays.role != "CAUSAL_STATE" or self.arrays.source != self.source
                or self.root.role is not MatrixProgrammeRole.DEVELOPMENT or self.disposition not in ("AVAILABLE", "NO_ORIGIN", "UNEVALUABLE")
                or (self.disposition == "AVAILABLE") != (self.frame_sha256 is not None and self.reason is None)
                or self.disposition != "AVAILABLE" and self.reason is None):
            raise ValueError("selected E4 causal delivery changes source/frame/cutoff availability")


def validate_selected_causal_feature(feature, causal_kind, mechanical_kind):
    from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import FEATURES
    from empirical_lawhood.adapters.methods.matrix_factor_response.response_population_statistics import STRATA
    from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_prediction import validate_matched_features
    from empirical_lawhood.kernel.serialization import validate_sha256
    for value in (feature.feature_id, feature.root_id, feature.independent_group_id, feature.clock_id):
        validate_stable_id(value)
    exact_pin(feature.prefix, causal_kind)
    exact_pin(feature.source, ScheduledSource)
    if (feature.family_id not in STRATA or feature.disposition not in
            ('AVAILABLE', 'NO_CAUSAL_ORIGIN', 'UNAVAILABLE', 'REFUSED')):
        raise ValueError('selected E4 feature changes the frozen causal grammar or availability')
    if feature.frame_sha256 is not None:
        validate_sha256(feature.frame_sha256)
    validate_decimal(feature.cutoff, field_name='actual causal cutoff', minimum=Decimal(0))
    if feature.physical_forecast is not None:
        exact_pin(feature.physical_forecast, mechanical_kind)
        validate_matched_features(feature.values, feature.disposition)
    else:
        if (tuple(name for name, _ in feature.values) != FEATURES
                if feature.disposition == 'AVAILABLE' else bool(feature.values)):
            raise ValueError('selected E4 feature drops its declared causal descriptor census')
        for _, value in feature.values:
            validate_decimal(value, field_name='causal selected feature', minimum=Decimal(0))
    if feature.fine_response_defect is not None:
        validate_decimal(feature.fine_response_defect, field_name='diagnostic FINE origin defect', minimum=Decimal(0))
        if feature.physical_forecast is None:
            raise ValueError('selected E4 diagnostic defect lacks its original mechanical producer')


def selected_target_shape(contract):
    if contract not in ('PAIRED15', 'MATCHED_FACTOR58'):
        raise ValueError('selected E4 changes its declared paired target contract')
    methods, points = selected_point_menu(contract == 'MATCHED_FACTOR58')
    return methods, points, 58 if contract == 'MATCHED_FACTOR58' else 30


def selected_point_menu(matched):
    from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_prediction import MATCHED_METHODS
    return (MATCHED_METHODS, 58) if matched else (METHODS, 15)


def validate_selected_point_curves(points, disposition, *, matched):
    from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_prediction import postprocess_log_points
    methods, count = selected_point_menu(matched)
    if type(points) is not tuple or tuple(method for method, _ in points) != methods:
        raise ValueError('selected E4 seal changes its frozen original account menu')
    for _, values in points:
        if (type(values) is not tuple or len(values) != count
                or disposition != 'AVAILABLE' and values != (None,) * count):
            raise ValueError('selected E4 seal drops paired targets or invents unavailable predictions')
        if matched:
            if postprocess_log_points(values) != values:
                raise ValueError('selected E4 seal changes cumulative paired58 predictions')
        else:
            for index, value in enumerate(values):
                if value is not None:
                    validate_decimal(value, field_name='selected original cumulative log point', minimum=Decimal(0))
                    if index % 3 and (values[index - 1] is None or value < values[index - 1]):
                        raise ValueError('selected E4 seal reverses original cumulative prediction transform')


@dataclass(frozen=True, slots=True)
class SelectedE3E4Feature(ScheduledForecastFeature):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/causal-feature"

    VERSION: ClassVar[str] = "2.0.0"
    physical_forecast: ObjectIdentity | None = None
    fine_response_defect: Decimal | None = None

    def __post_init__(self):
        validate_selected_causal_feature(self, SelectedE3E4CausalPrefix, SelectedE3E4MechanicalForecast)


@dataclass(frozen=True, slots=True)
class SelectedE3E4AccountSeal(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/account-seal"
    VERSION: ClassVar[str] = "2.0.0"
    record_id: str
    design: ObjectIdentity
    source: ObjectIdentity
    prefix: ObjectIdentity
    feature: SelectedE3E4Feature
    original_package: ObjectIdentity
    original_calibration: ObjectIdentity
    log_points: tuple[tuple[str, tuple[Decimal | None, ...]], ...]
    uncertainty_status: str = POINT_ONLY

    def __post_init__(self):
        validate_stable_id(self.record_id)
        exact_pin(self.design, SelectedE3E4ForecastDesign)
        exact_pin(self.prefix, SelectedE3E4CausalPrefix)
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_package import validate_selected_package_calibration
        validate_selected_package_calibration(self.original_package, self.original_calibration)
        if (type(self.feature) is not SelectedE3E4Feature or self.feature.source != self.source
                or self.feature.prefix != self.prefix or self.uncertainty_status != POINT_ONLY):
            raise ValueError('selected E4 seal changes its original causal inputs or point-only meaning')
        validate_record_fields(self.feature)
        validate_selected_point_curves(self.log_points, self.feature.disposition,
            matched=self.feature.physical_forecast is not None)

    @property
    def identity(self):
        return pin(self)


@dataclass(frozen=True, slots=True)
class SelectedE3E4FullHistory(ScheduledFullHistory):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/full-history"

    def __post_init__(self):
        validate_stable_id(self.history_id)
        exact_pin(self.prefix, SelectedE3E4PrefixHistory)
        exact_pin(self.forecast, SelectedE3E4AccountSeal)
        exact_pin(self.checkpoint, ScheduledCheckpoint)
        if self.physical_forecast is not None:
            exact_pin(self.physical_forecast, SelectedE3E4MechanicalForecast)
        if (type(self.arrays) is not ScheduledFullArrays or self.arrays.source != self.source or type(self.native) is not ScheduledNativeEvidence
                or type(self.completed_primary_steps) is not int or self.completed_primary_steps < 1
                or self.completed_fine_steps != 2 * self.completed_primary_steps
                or self.arrays.outcome_access is not DEV or self.arrays.visibility_ceiling is not EXPOSED):
            raise ValueError("selected E4 continuation changes complete original paired clock/native history")

    def validate_source(self, source, prefix, causal, seal, physical, *, config, prefix_config):
        from .selected_e3_e4_bindings import native_contract
        prefix.validate_source(source, config=prefix_config)
        configuration, parent_task, operation, sources = native_contract(config, source,
            recorded_operation=self.native.definition.operation_id)
        validate_full_native_evidence(self, source, prefix, causal, seal, physical, configuration=configuration,
            parent_task=parent_task, operation=operation, shared_sources=sources)


@dataclass(frozen=True, slots=True)
class SelectedE3E4MechanicalForecast(ScheduledResponseForecast):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/mechanical-forecast"

    def __post_init__(self):
        validate_stable_id(self.forecast_id)
        exact_pin(self.causal_prefix, SelectedE3E4CausalPrefix)
        if (type(self.arrays) is not ScheduledResponseArrays or self.arrays.role != "FORECAST" or self.arrays.source != self.source
                or self.arrays.outcome_access is not DEV or self.arrays.visibility_ceiling is not EXPOSED
                or tuple((view, predictor) for view, predictor, _, _ in self.dispositions) != tuple((view, predictor) for view in ("PRIMARY", "FINE") for predictor in model_predictors(self.mechanical_model))
                or self.disposition not in ("AVAILABLE", "NO_ORIGIN", "UNEVALUABLE", "INSTRUMENT_UNRESOLVED")):
            raise ValueError("selected E4 mechanical forecast drops complete selected paired method instrument")


@dataclass(frozen=True, slots=True)
class SelectedE3E4Responses(ScheduledResponseNative):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/native-responses"

    def validate_source(self, source, history, causal, physical, error, *, config, prefix_config):
        from .selected_e3_e4_bindings import native_contract
        from .response_records import validate_response_native_evidence
        history.validate_source(source, config=prefix_config)
        protocol, panels = config.protocol, config.panels
        protocol.public_source.validate_source(source)
        if (self.source != identity(source) or self.causal_prefix != identity(causal)
                or self.physical_forecast != identity(physical) or self.error_forecast != error.identity
                or self.protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
                or self.branch_ids != tuple(value[0] for value in branch_census(protocol, panels))
                or self.arrays.outcome_access is not DEV or self.arrays.visibility_ceiling is not EXPOSED):
            raise ValueError("selected E4 responses substitute actual source/cutoff/seals/complete48branch menu")
        if not self.native:
            if causal.disposition == "AVAILABLE" and physical.disposition == "AVAILABLE":
                raise ValueError("selected E4 cannot hide an available required native pulse collection")
            return
        configuration, parent_task, operation, sources = native_contract(config, source,
            recorded_operation=self.native[0].definition.operation_id)
        validate_response_native_evidence(self, source, config.response_selection, history, causal, physical, error,
            configuration=configuration, parent_task=parent_task, operation=operation, shared_sources=sources, panels=panels, protocol=protocol,
            native_sources=(*sources, identity(history), identity(history.checkpoint), identity(causal), identity(error), identity(physical))
                if operation.endswith(".direct-operands.v2") else None)


@dataclass(frozen=True, slots=True)
class SelectedE3E4NativeSource(CanonicalRecord):
    """Bounded native transport; its own bytes never impersonate the subject.

    Only the parent derives this record from the complete authenticated bank.
    Child arithmetic names the actual bounded reference as its scientific source.
    """
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/native-source"
    record_id: str
    programme: ObjectIdentity
    bank: ObjectIdentity
    descriptor: ScheduledSource
    public: ScheduledPublicSource
    policy: ScheduledPrefixPolicy
    numerical_design: MatrixParameterNumericalDesign
    provenance: NumericalProducingProvenance

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterNumericalDesign
        from .records import ScheduledPrefixPolicy
        validate_stable_id(self.record_id)
        exact_pin(self.programme, SelectedE3E4DevelopmentProgramme)
        exact_pin(self.bank, SelectedE3E4DevelopmentBank)
        for value, kind in ((self.descriptor, ScheduledSource), (self.public, ScheduledPublicSource),
                (self.policy, ScheduledPrefixPolicy), (self.numerical_design, MatrixParameterNumericalDesign),
                (self.provenance, NumericalProducingProvenance)):
            if type(value) is not kind:
                raise TypeError("selected E4 native transport requires exact original local operands")
            validate_record_fields(value)
        if (self.descriptor.identity != self.public.source or self.descriptor.root.root != self.public.root
                or self.descriptor.root.coordinate != ObjectIdentity.from_record(self.public.coordinate.coordinate_id, self.public.coordinate)
                or self.descriptor.provenance != self.provenance.identity or self.public.policy != self.policy
                or (self.public.allocation, self.public.reservation) != (self.descriptor.allocation, self.descriptor.reservation)
                or self.public.root.role is not MatrixProgrammeRole.DEVELOPMENT):
            raise ValueError("selected E4 local transport changes exact original root/policy/provenance")

    @classmethod
    def from_bank(cls, programme, bank, descriptor, *, index):
        if descriptor not in bank.sources or programme.bank != pin(bank, "bank_id"):
            raise ValueError("selected E4 native transport is outside its authenticated whole programme")
        source = bank.source(descriptor.root_id,index=index)
        return cls("native." + source.source_id, programme.identity, pin(bank, "bank_id"), descriptor,
            ScheduledPublicSource.from_source(source), source.policy, source.numerical_design, source.provenance)

    @property
    def identity(self):
        return pin(self)

    @property
    def reference(self):
        return self.descriptor

    @property
    def root(self):
        return self.descriptor.root

    @property
    def root_id(self):
        return self.descriptor.root_id

    @property
    def coordinate(self):
        return self.public.coordinate

    @property
    def evidence_role(self):
        return "EXPOSED_DEVELOPMENT_NONPROMOTABLE"



@dataclass(frozen=True, slots=True)
class SelectedE3E4NativeSourceReference(CanonicalRecord):
    """Bounded source reference; full provenance is a separate exact input.

    Only the parent derives this record from the complete authenticated bank.
    Child arithmetic names the actual bounded reference as its scientific source.
    """
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/native-source-reference"
    record_id: str
    programme: ObjectIdentity
    bank: ObjectIdentity
    descriptor: ScheduledSource
    public: ScheduledPublicSource
    policy: ScheduledPrefixPolicy
    numerical_design: MatrixParameterNumericalDesign
    provenance: ObjectIdentity
    provenance_size_bytes: int

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterNumericalDesign
        from .records import ScheduledPrefixPolicy
        validate_stable_id(self.record_id)
        exact_pin(self.programme, SelectedE3E4DevelopmentProgramme)
        exact_pin(self.bank, SelectedE3E4DevelopmentBank)
        for value, kind in ((self.descriptor, ScheduledSource), (self.public, ScheduledPublicSource),
                (self.policy, ScheduledPrefixPolicy), (self.numerical_design, MatrixParameterNumericalDesign),
                (self.provenance, ObjectIdentity)):
            if type(value) is not kind:
                raise TypeError("selected E4 native transport requires exact original local operands")
            validate_record_fields(value)
        exact_pin(self.provenance, NumericalProducingProvenance)
        if (type(self.provenance_size_bytes) is not int or self.provenance_size_bytes < 1
                or self.descriptor.identity != self.public.source or self.descriptor.root.root != self.public.root
                or self.descriptor.root.coordinate != ObjectIdentity.from_record(self.public.coordinate.coordinate_id, self.public.coordinate)
                or self.descriptor.provenance != self.provenance or self.public.policy != self.policy
                or (self.public.allocation, self.public.reservation) != (self.descriptor.allocation, self.descriptor.reservation)
                or self.public.root.role is not MatrixProgrammeRole.DEVELOPMENT):
            raise ValueError("selected E4 local transport changes exact original root/policy/provenance")

    @classmethod
    def from_bank(cls, programme, bank, descriptor, *, index):
        if descriptor not in bank.sources or programme.bank != pin(bank, "bank_id"):
            raise ValueError("selected E4 native transport is outside its authenticated whole programme")
        source = bank.source(descriptor.root_id,index=index)
        return cls("native." + source.source_id, programme.identity, pin(bank, "bank_id"), descriptor,
            ScheduledPublicSource.from_source(source), source.policy, source.numerical_design, source.provenance.identity, len(source.provenance.canonical_bytes()))

    @property
    def identity(self):
        return pin(self)

    @property
    def reference(self):
        return self.descriptor

    @property
    def root(self):
        return self.descriptor.root

    @property
    def root_id(self):
        return self.descriptor.root_id

    @property
    def coordinate(self):
        return self.public.coordinate

    @property
    def evidence_role(self):
        return "EXPOSED_DEVELOPMENT_NONPROMOTABLE"


@dataclass(frozen=True, slots=True)
class SelectedE3E4EntrySeal(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/development-entry-seal"
    VERSION: ClassVar[str] = "2.0.0"
    record_id: str
    programme: ObjectIdentity
    bank: ObjectIdentity
    forecast_design: ObjectIdentity
    evidence: ObjectIdentity
    groups: tuple[str, ...]
    sources: tuple[ObjectIdentity, ...]
    design: SelectedE3E4Design

    secondary_readout: ObjectIdentity

    def __post_init__(self):
        exact_pin(self.secondary_readout, MatrixE4SecondaryReadoutSelection)
        validate_stable_id(self.record_id)
        exact_pin(self.programme, SelectedE3E4DevelopmentProgramme)
        exact_pin(self.bank, SelectedE3E4DevelopmentBank)
        exact_pin(self.forecast_design, SelectedE3E4ForecastDesign)
        exact_pin(self.evidence, SelectedE3E4Evidence)
        if (type(self.design) is not SelectedE3E4Design or len(self.groups) != self.design.group_count
                or self.groups != tuple(sorted(set(self.groups))) or len(self.sources) != self.design.group_count * self.design.cases_per_group
                or tuple(value.object_id for value in self.sources) != tuple(sorted({value.object_id for value in self.sources}))):
            raise ValueError("selected E4 entry drops its declared complete whole-group factorial census")
        validate_record_fields(self.design)

    @property
    def identity(self):
        return pin(self)


def entry_seal(programme, evidence, *, secondary_readout):
    return SelectedE3E4EntrySeal("entry." + programme.programme_id, programme.identity, programme.bank,
        programme.forecast_design, evidence.identity, programme.group_ids, tuple(case.source for case in programme.cases), programme.design, secondary_readout.identity)


@dataclass(frozen=True, slots=True)
class SelectedE3E4CaseResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/development-case-result"
    VERSION: ClassVar[str] = "2.0.0"
    root_id: str
    source: ObjectIdentity
    group_id: str
    disposition: str
    numerical_disposition: str
    score_disposition: str
    paired_log_targets: tuple[Decimal | None, ...]
    original_log_points: tuple[tuple[str, tuple[Decimal | None, ...]], ...]
    forecast: ObjectIdentity | None
    score: ObjectIdentity | None
    full_assessment: ObjectIdentity | None
    ordinary_receipts: tuple[ObjectIdentity | ScheduledProgrammeReceiptReference, ...]
    native: tuple[ScheduledProgrammeNativeDisposition, ...]
    reason_codes: tuple[str, ...]
    operational_events: tuple[ObjectIdentity, ...] = ()
    target_contract: str = "PAIRED15"

    def __post_init__(self):
        from .programme_reduction import (ScheduledProgrammeNativeDisposition, ScheduledProgrammeReceiptReference,
            NATIVE_PHASES, NUMERICAL_DISPOSITIONS, DISPOSITIONS)
        validate_stable_id(self.root_id)
        validate_stable_id(self.group_id)
        exact_pin(self.source, ScheduledSource)
        methods, point_count, target_count = selected_target_shape(self.target_contract)
        if (self.disposition not in DISPOSITIONS or self.numerical_disposition not in NUMERICAL_DISPOSITIONS
                or type(self.paired_log_targets) is not tuple or len(self.paired_log_targets) != target_count
                or type(self.original_log_points) is not tuple or tuple(method for method, _ in self.original_log_points) != methods
                or any(len(values) != point_count for _, values in self.original_log_points)
                or tuple(value.phase for value in self.native) != NATIVE_PHASES
                or any(type(value) is not ScheduledProgrammeNativeDisposition for value in self.native)
                or any(type(value) not in (ObjectIdentity, ScheduledProgrammeReceiptReference) for value in self.ordinary_receipts)
                or any(type(value) is ObjectIdentity and value.object_schema != "empirical-lawhood/runtime/canonical-task-receipt" for value in self.ordinary_receipts)
                or tuple(value.object_id if type(value) is ObjectIdentity else value.receipt_id for value in self.ordinary_receipts) !=
                    tuple(sorted({value.object_id if type(value) is ObjectIdentity else value.receipt_id for value in self.ordinary_receipts}))
                or self.reason_codes != tuple(sorted(set(self.reason_codes)))):
            raise ValueError("selected E4 development case drops actual outcomes, original three methods or paired30 endpoints")
        from empirical_lawhood.runtime.recovery import TaskRecoveryEvent
        if (type(self.operational_events) is not tuple or tuple(value.object_id for value in self.operational_events) !=
                tuple(sorted({value.object_id for value in self.operational_events}))):
            raise ValueError("selected E4 case aliases original operational failure/recovery events")
        for value in self.operational_events:
            exact_pin(value, TaskRecoveryEvent)
        for value, kind in ((self.forecast, SelectedE3E4AccountSeal), (self.score, ScheduledResponseScore),
                (self.full_assessment, SelectedE3E4NumericalAssessment)):
            if value is not None:
                exact_pin(value, kind)
        for value in (*self.paired_log_targets, *(value for _, values in self.original_log_points for value in values)):
            if value is not None:
                validate_decimal(value, field_name="original cumulative log endpoint", minimum=Decimal(0))

    @classmethod
    def unentered(cls, case, *, target_contract="PAIRED15"):
        from .programme_reduction import ScheduledProgrammeNativeDisposition, NATIVE_PHASES
        methods, point_count, target_count = selected_target_shape(target_contract)
        return cls(case.root_id, case.source, case.independent_group_id, "UNENTERED", "UNENTERED", "UNENTERED",
            (None,) * target_count, tuple((method, (None,) * point_count) for method in methods), None, None, None, (),
            tuple(ScheduledProgrammeNativeDisposition(phase, "UNENTERED", None, None, None,
                ("actual-operation-unentered",)) for phase in NATIVE_PHASES), ("actual-operation-unentered",), target_contract=target_contract)


@dataclass(frozen=True, slots=True)
class SelectedE3E4DevelopmentReduction(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/development-reduction"
    record_id: str
    programme: ObjectIdentity
    bank: ObjectIdentity
    cases: tuple[SelectedE3E4CaseResult, ...]
    group_residuals: tuple[tuple[str, tuple[tuple[str, Decimal | None], ...]], ...]
    design: SelectedE3E4Design
    uncertainty_status: str = POINT_ONLY
    scientific_standing: str = "EXPOSED_DEVELOPMENT_ONLY_NO_QUALIFICATION"

    def __post_init__(self):
        validate_stable_id(self.record_id)
        exact_pin(self.programme, SelectedE3E4DevelopmentProgramme)
        exact_pin(self.bank, SelectedE3E4DevelopmentBank)
        if (type(self.design) is not SelectedE3E4Design or type(self.cases) is not tuple
                or len(self.cases) != self.design.group_count * self.design.cases_per_group
                or any(type(value) is not SelectedE3E4CaseResult for value in self.cases)
                or tuple(value.root_id for value in self.cases) != tuple(sorted({value.root_id for value in self.cases}))
                or len(self.group_residuals) != self.design.group_count or self.uncertainty_status != POINT_ONLY
                or self.scientific_standing != "EXPOSED_DEVELOPMENT_ONLY_NO_QUALIFICATION"):
            raise ValueError("selected E4 reduction changes declared complete scope or promotes exposed point evidence")
        validate_record_fields(self.design)
        from .selected_e3_e4_science import group_residuals
        if self.group_residuals != group_residuals(self.cases):
            raise ValueError("selected E4 reduction replaces complete nine-coordinate/paired-target residuals")

    @property
    def identity(self):
        return pin(self)
