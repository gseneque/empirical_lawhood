# SPDX-License-Identifier: MPL-2.0
"""A prospective initial-window observation, separate from the full forecast.

One complete coarse source-method window is the scientific observation unit.
Half/quarter methods retain their genuine continuation calls. A tier can move
the actual stopping clock; neither clocks nor scientific data are truncated to
force a matched result. Historical uncertain work and its HOLDs stay unchanged.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition
from . import durable_roster as dr
from . import segmented_contracts as sc
from . import segmented_evidence as se
from . import segmented_science as ss
from .source_derived_preparation import require_assessed_source_roots

D = Decimal
METHODS = (D(60), D(30), D(15))
STOP = "FIRST_COMPLETE_SOURCE_METHOD_RETURN_AT_OR_AFTER_60S;PHYSICAL_TERMINATION_RETAINED"
SCOPE = "INITIAL_TRANSIENT_PREPARATION_NUMERICAL_AND_RESOURCE_OBSERVATION;NOT_FULL_FORECAST_QUALIFICATION"
RAW_SOURCE_SCHEMA = "empirical-lawhood/source/checksummed-uninterpreted-public-bytes"


@dataclass(frozen=True, slots=True)
class PreparationObservationProtocol(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/initial-window-observation-protocol"
    observation_id: str
    original_selection: dr.FrozenForecastRoster
    uncertain_work: dr.UnknownDiagnosticWork
    selected_qualification_slot: int
    configurations: tuple[sc.SegmentedNativeConfig, ...]
    minimum_observation_clock_s: Decimal = D(60)
    stopping_semantics: str = STOP
    scope: str = SCOPE
    native_output: str = "ALL_ORIGINAL_NATIVE_ARRAYS_KNOTS_DERIVATIVES;EVERY_INTEGER_SECOND;NO_THINNING"
    prior_uncertainty: str = "UNCHANGED;NO_OLD_OUTPUTS_RECONSTRUCTED;NO_UNKNOWN_REPLAY"
    physical_qualification: bool = False
    full_forecast_completed: bool = False
    fresh_physical_units: int = 0
    scientific_entry_authority: str = "NONE;ACTUAL_ENTRY_REQUIRES_ITS_SEPARATE_DECLARATION_CUSTODY_ENVIRONMENT_AND_RESOURCE_OPERANDS"

    def __post_init__(self):
        validate_stable_id(self.observation_id)
        if type(self.original_selection) is not dr.FrozenForecastRoster or type(self.uncertain_work) is not dr.UnknownDiagnosticWork:
            raise ValueError("observation substitutes original selected and uncertain scientific work")
        self.original_selection.__post_init__()
        self.uncertain_work.__post_init__()
        if type(self.selected_qualification_slot) is not int or not 0 <= self.selected_qualification_slot < 54:
            raise ValueError("observation loses its declared original condition/mesh selection")
        native = self.original_selection.configurations[self.selected_qualification_slot]
        if (type(self.configurations) is not tuple or len(self.configurations) != 3
                or any(type(row) is not sc.SegmentedNativeConfig for row in self.configurations)
                or tuple(row.method.maximum_segment_horizon_s for row in self.configurations) != METHODS
                or any(row.native != native for row in self.configurations)
                or len({row.config_id for row in self.configurations}) != 3):
            raise ValueError("observation changes its isolated complete 60/30/15 denominator or native condition")
        for config in self.configurations:
            config.__post_init__()
            require_assessed_source_roots(config.preparation, config.preparation_assessment)
        if any((row.preparation, row.preparation_assessment) !=
               (self.configurations[0].preparation, self.configurations[0].preparation_assessment) for row in self.configurations):
            raise ValueError("observation changes source preparation between its numerical controls")
        if (type(self.minimum_observation_clock_s) is not D or self.minimum_observation_clock_s != 60
                or self.stopping_semantics != STOP or self.scope != SCOPE
                or self.native_output != "ALL_ORIGINAL_NATIVE_ARRAYS_KNOTS_DERIVATIVES;EVERY_INTEGER_SECOND;NO_THINNING"
                or self.prior_uncertainty != "UNCHANGED;NO_OLD_OUTPUTS_RECONSTRUCTED;NO_UNKNOWN_REPLAY"
                or any(type(getattr(self, name)) is not bool or getattr(self, name)
                       for name in ("physical_qualification", "full_forecast_completed"))
                or type(self.fresh_physical_units) is not int or self.fresh_physical_units != 0
                or self.scientific_entry_authority != "NONE;ACTUAL_ENTRY_REQUIRES_ITS_SEPARATE_DECLARATION_CUSTODY_ENVIRONMENT_AND_RESOURCE_OPERANDS"):
            raise ValueError("observation changes scientific stopping operands or invents forecast/entry/physical authority")

    @property
    def original_entry_disposition(self):
        """Recompute the retained old HOLD; no observation can clear it."""
        return dr.entry_dispositions(self.original_selection, self.uncertain_work)[self.selected_qualification_slot]


def freeze_observation(original_selection, uncertain_work, selected_slot, preparation, assessment):
    """Freeze one selected condition with three genuinely changed method operands."""
    if type(selected_slot) is not int or not 0 <= selected_slot < 54:
        raise ValueError("observation requires an exact selected qualification slot")
    require_assessed_source_roots(preparation, assessment)
    native = original_selection.configurations[selected_slot]
    configs = tuple(sc.SegmentedNativeConfig("config.observation." + str(horizon) + "." + native.config_id.removeprefix("config."),
        native, preparation, assessment, sc.SegmentedMethodProtocol("method.observation." + str(horizon), horizon)) for horizon in METHODS)
    return PreparationObservationProtocol("observation.initial-window." + native.config_id, original_selection,
        uncertain_work, selected_slot, configs)


@dataclass(frozen=True, slots=True)
class ObservationResourceSnapshot(CanonicalRecord):
    """Measured availability, not an operational ceiling or future guarantee."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/observation-resource-snapshot"
    snapshot_id: str
    observed_utc: str
    declared_storage_root: ObjectIdentity
    storage_available_bytes: int
    memory_available_bytes: int
    evidence: ObjectIdentity
    scope: str = "ACTUAL_HOST_AVAILABLE_RESOURCES;NO_UNIVERSAL_PEAK_OR_TOTAL_STORAGE_BOUND"

    def __post_init__(self):
        from datetime import datetime
        validate_stable_id(self.snapshot_id)
        observed = datetime.fromisoformat(self.observed_utc)
        if (observed.tzinfo is None or type(self.declared_storage_root) is not ObjectIdentity or type(self.evidence) is not ObjectIdentity
                or self.evidence.object_schema != RAW_SOURCE_SCHEMA
                or any(type(getattr(self, name)) is not int or getattr(self, name) <= 0
                       for name in ("storage_available_bytes", "memory_available_bytes"))
                or self.scope != "ACTUAL_HOST_AVAILABLE_RESOURCES;NO_UNIVERSAL_PEAK_OR_TOTAL_STORAGE_BOUND"):
            raise ValueError("observation requires measured positive physical availability, without invented bounds")


@dataclass(frozen=True, slots=True)
class ObservationEntryDeclaration(CanonicalRecord):
    """An exact scope consumed by the already-authorised native task boundary.

    This record is no issuer or permission mechanism. NativeSubworkProgress owns
    actual parent/contact/roster/custody authentication; the caller must provide
    these original input materializations and the selected resource/ABI products.
    """
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/observation-entry-declaration"
    declaration_id: str
    observation: ObjectIdentity
    configured_method_index: int
    producing_provenance: NumericalProducingProvenance
    abi_import_report: ObjectIdentity
    resources: ObservationResourceSnapshot
    authorised_scope: str = "INITIAL_WINDOW_SOURCE_DERIVED_CONTROL_ONLY;NO_UNKNOWN_RECOVERY_OR_FULL_FORECAST"

    def __post_init__(self):
        validate_stable_id(self.declaration_id)
        if (type(self.observation) is not ObjectIdentity or self.observation.object_schema != PreparationObservationProtocol.SCHEMA
                or type(self.configured_method_index) is not int or not 0 <= self.configured_method_index < 3
                or type(self.producing_provenance) is not NumericalProducingProvenance
                or type(self.abi_import_report) is not ObjectIdentity
                or self.abi_import_report.object_schema != RAW_SOURCE_SCHEMA
                or type(self.resources) is not ObservationResourceSnapshot
                or self.authorised_scope != "INITIAL_WINDOW_SOURCE_DERIVED_CONTROL_ONLY;NO_UNKNOWN_RECOVERY_OR_FULL_FORECAST"):
            raise ValueError("observation entry changes declared effect scope, actual environment or physical resources")
        self.producing_provenance.__post_init__()
        self.resources.__post_init__()


@dataclass(frozen=True, slots=True)
class PreparationObservationResult(CanonicalRecord):
    """Actual original prefix outputs, never a relabelled completed forecast."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/initial-window-observation-result"
    result_id: str
    observation: PreparationObservationProtocol
    configured_method_index: int
    evidence: se.SegmentedNativeEvidence
    native_definition: NativeSubworkDefinition
    entry_declaration: ObservationEntryDeclaration
    disposition: str
    actual_last_model_clock_s: Decimal | None
    observed_native_calls: int
    original_entry_disposition: dr.ForecastEntryDisposition
    scope: str = SCOPE
    full_forecast_completed: bool = False
    physical_qualification: bool = False
    fresh_physical_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.result_id)
        if type(self.observation) is not PreparationObservationProtocol or type(self.evidence) is not se.SegmentedNativeEvidence:
            raise ValueError("observation result substitutes its actual declaration or scientific outputs")
        self.observation.__post_init__()
        self.evidence.__post_init__()
        if (type(self.configured_method_index) is not int or not 0 <= self.configured_method_index < 3
                or self.evidence.trace.config != self.observation.configurations[self.configured_method_index]
                or type(self.native_definition) is not NativeSubworkDefinition
                or type(self.entry_declaration) is not ObservationEntryDeclaration
                or self.entry_declaration.observation != ss.identity(self.observation, "observation_id")
                or self.entry_declaration.configured_method_index != self.configured_method_index
                or self.entry_declaration.producing_provenance.identity != self.evidence.protocol.producing_provenance
                or self.observed_native_calls != len(self.evidence.trace.segments)
                or type(self.observed_native_calls) is not int
                or self.original_entry_disposition != self.observation.original_entry_disposition):
            raise ValueError("observation result changes actual selected method, calls, custody or old HOLD")
        definition = self.native_definition
        self.entry_declaration.__post_init__()
        ss.authenticate_payloads(self.evidence.native_receipt, (self.observation, self.entry_declaration))
        if (definition.operation_id != "battery.segmented-observation.initial-window"
                or definition.configuration != ss.identity(self.evidence.trace.config, "config_id")
                or not {ss.identity(self.observation, "observation_id"),
                        ss.identity(self.observation.original_selection, "roster_id"),
                        ss.identity(self.observation.uncertain_work, "record_id"),
                        ss.identity(self.entry_declaration, "declaration_id")}.issubset(definition.sources)
                or not set(definition.input_materialization_ids).issubset(self.evidence.native_receipt.input_materialization_ids)
                or any(sum(parent.identity == definition.identity for parent in row.lineage_parents) != 1
                       for row in self.evidence.native_receipt.output_logical_artifacts)):
            raise ValueError("observation result loses its distinct source declaration and actual producing custody")
        clocks = tuple(row.native_times_s[-1] for row in self.evidence.trace.segments if row.native_times_s)
        last = clocks[-1] if clocks else None
        if any(clock >= self.observation.minimum_observation_clock_s for clock in clocks[:-1]):
            raise ValueError("observation continues beyond its declared first complete native return")
        expected = ("TECHNICAL_FAILURE" if self.evidence.trace.disposition == "TECHNICAL_FAILURE" else
                    "OBSERVATION_WINDOW_COMPLETED" if last is not None and last >= self.observation.minimum_observation_clock_s else
                    "PHYSICAL_TERMINATION_BEFORE_OBSERVATION_WINDOW")
        if self.disposition != expected or self.actual_last_model_clock_s != last:
            raise ValueError("observation result invents an unobserved stopping clock or favourable completion")
        if (self.scope != SCOPE or any(type(getattr(self, name)) is not bool or getattr(self, name)
                for name in ("full_forecast_completed", "physical_qualification"))
                or type(self.fresh_physical_units) is not int or self.fresh_physical_units != 0):
            raise ValueError("an observed initial window cannot become full forecast or physical qualification")


@dataclass(frozen=True, slots=True)
class ObservationPreparationAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/initial-window-preparation-assessment"
    assessment_id: str
    observation_result: ObjectIdentity
    configuration: ObjectIdentity
    preparation: ss.DerivedPreparationAssessment | ss.UnavailableDerivedPreparationAssessment
    disposition: A
    reason_codes: tuple[str, ...]
    scope: str = "OBSERVED_INITIAL_PREPARATION_ONLY;WINDOW_FIDELITY_RESOURCE_AND_FULL_QUALIFICATION_REMAIN_SEPARATE"
    full_forecast_completed: bool = False
    physical_qualification: bool = False

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if (self.observation_result.object_schema != PreparationObservationResult.SCHEMA
                or self.configuration.object_schema != sc.SegmentedNativeConfig.SCHEMA
                or type(self.preparation) not in {ss.DerivedPreparationAssessment, ss.UnavailableDerivedPreparationAssessment}
                or self.preparation.configuration != self.configuration or self.disposition is not self.preparation.disposition
                or self.reason_codes != self.preparation.reason_codes
                or self.scope != "OBSERVED_INITIAL_PREPARATION_ONLY;WINDOW_FIDELITY_RESOURCE_AND_FULL_QUALIFICATION_REMAIN_SEPARATE"
                or any(type(getattr(self, name)) is not bool or getattr(self, name)
                       for name in ("full_forecast_completed", "physical_qualification"))):
            raise ValueError("observation assessment invents preparation, full forecast or physical success")


def assess_observation_preparation(result):
    if type(result) is not PreparationObservationResult:
        raise ValueError("preparation observation assessment requires its exact actual result")
    result.__post_init__()
    config = result.evidence.trace.config
    assessment = se.assess_preparation_evidence(config, result.evidence)
    return ObservationPreparationAssessment("assessment." + result.result_id, ss.identity(result, "result_id"),
        ss.identity(config, "config_id"), assessment, assessment.disposition, assessment.reason_codes)
