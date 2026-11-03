# SPDX-License-Identifier: MPL-2.0
"""Selected current-stage evidence; software exposure never grants qualification."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.methods.battery_thermal_service.contracts import BatteryThermalConfig, BatteryThermalSource, BatteryThermalTrace
from decimal import Decimal
from empirical_lawhood.kernel.action_contracts import OccurrenceActionWord, ObservedActionOccurrence
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.planning.controller_study import ImplementationRole
from empirical_lawhood.runtime.artifacts import ArtifactManifest, CanonicalTaskReceipt
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.planning.recursive_authoring import RecursiveOperationSpec
from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave, RecursiveImplementationBinding

PROTOCOL_SHA256 = "dca5201fbcffbf7c1955dfeacf8458b253d43fb7620ca069d16051c51cbc7d41"
EXPOSURES = ("EXPOSED_RECORDED_INPUT_CONFORMANCE", "RECEIPT_BACKED_NATIVE_OBSERVATION")


@dataclass(frozen=True, slots=True)
class BatteryCurrentRecipe(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-current-control/recipe"
    source: BatteryThermalSource
    protocol_sha256: str
    unit_id: str
    initial_temperature_k: Decimal
    initial_soc: Decimal
    view: str

    @property
    def recipe_id(self):
        return f"{self.unit_id}.{self.view}.current-recipe"

    def __post_init__(self):
        BatteryThermalConfig("battery-current-recipe.validation", "acquire", self.protocol_sha256, self.unit_id, self.initial_temperature_k, view=self.view, initial_soc=self.initial_soc, source=self.source)


def current_recipe(config: BatteryThermalConfig) -> BatteryCurrentRecipe:
    return BatteryCurrentRecipe(config.source, config.protocol_sha256, config.unit_id, config.initial_temperature_k, config.initial_soc, config.view)


@dataclass(frozen=True, slots=True)
class BatteryCurrentControlConfiguration(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-current-control/implementation-config"
    config_id: str
    role: ImplementationRole
    protocol_sha256: str = PROTOCOL_SHA256

    def __post_init__(self):
        if self.config_id != f"battery-current-control.{self.role.value.lower()}.config" or self.protocol_sha256 != PROTOCOL_SHA256:
            raise ValueError("battery current owner changes the frozen role or service selection")
        if self.role is ImplementationRole.OUTCOME_EVALUATOR:
            raise ValueError("selected battery interface grants no outcome qualification capability")


@dataclass(frozen=True, slots=True)
class BatteryCurrentDeliveryEvidence(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-current-control/delivery-evidence"
    evidence_id: str
    exposure: str
    source: BatteryThermalTrace
    producing_receipt: CanonicalTaskReceipt
    artifact: ArtifactManifest
    word: OccurrenceActionWord
    observed: ObservedActionOccurrence
    source_clock: ObjectIdentity
    native_configuration: ArtifactManifest | None = None
    native_acquisition: RecursiveOperationSpec | None = None
    native_packet: AuthoredRecursiveWave | None = None
    native_implementation: RecursiveImplementationBinding | None = None

    def __post_init__(self):
        validate_stable_id(self.evidence_id)
        if self.exposure not in EXPOSURES:
            raise ValueError("battery delivery must retain its original evidence exposure")
        if self.source.config.protocol_sha256 != PROTOCOL_SHA256:
            raise ValueError("battery delivery changes the selected configuration/preparation")
        raw = self.source.canonical_bytes()
        logical, material = self.artifact.logical, self.artifact.materialization
        if logical.content_sha256 != self.source.fingerprint() or material.physical_sha256 != self.source.fingerprint() or material.size_bytes != len(raw) or logical.payload_schema != self.source.SCHEMA:
            raise ValueError("battery delivery source bytes differ from their artifact")
        receipt = self.producing_receipt
        if receipt.operational_status is not OperationalStatus.SUCCEEDED or material not in receipt.output_materializations or logical not in receipt.output_logical_artifacts:
            raise ValueError("battery delivery lacks its exact successful producing receipt")
        if len(self.word.occurrences) != 1 or self.observed.expected_occurrence_id != self.word.occurrences[0].occurrence_id:
            raise ValueError("battery delivery changes the selected current occurrence")
        from .delivery import project_current_stages, validate_current_word
        validate_current_word(self.word, self.source.config)
        actual, clock = project_current_stages(self.source, self.word, observation_id=self.observed.observation_id)
        if self.observed != actual or self.source_clock != clock:
            raise ValueError("battery delivery stages or source clock differ from original acquisition")
        native_members = (self.native_configuration, self.native_acquisition, self.native_packet, self.native_implementation)
        if self.exposure == "EXPOSED_RECORDED_INPUT_CONFORMANCE":
            if any(member is not None for member in native_members):
                raise ValueError("exposed conformance cannot claim native custody members")
        elif any(member is None for member in native_members):
            raise ValueError("native current exposure requires its actual configuration, acquisition and authored source custody")
        else:
            from empirical_lawhood.adapters.methods.battery_thermal_service.executable_binding import operation_registrations
            config_input = self.native_configuration
            operation = self.native_acquisition
            native_owner = next(r.selection for r in operation_registrations() if r.selection.capability_key == "battery-thermal-service.acquire")
            if operation.selection != native_owner or operation.config_identity != ObjectIdentity.from_record(self.source.config.config_id, self.source.config):
                raise ValueError("native current delivery changes its registered producing acquisition")
            if config_input.logical.logical_artifact_id != self.source.config.config_id or config_input.logical.content_sha256 != self.source.config.fingerprint() or config_input.logical.payload_schema != self.source.config.SCHEMA or config_input.materialization.physical_sha256 != self.source.config.fingerprint() or config_input.materialization.size_bytes != len(self.source.config.canonical_bytes()) or config_input.materialization.materialization_id not in receipt.input_materialization_ids:
                raise ValueError("native current delivery configuration is absent from the producing receipt")
            if self.native_packet.implementation.object_fingerprint != self.native_implementation.fingerprint() or receipt.implementation_commit != self.native_implementation.observed_git_head:
                raise ValueError("native current delivery substitutes its actual producing implementation")
            source_members = dict(self.native_implementation.package_sources)
            if source_members.get("adapters/methods/battery_thermal_service/science.py") != self.source.implementation_sha256:
                raise ValueError("native current delivery source implementation differs from the authored source inventory")
