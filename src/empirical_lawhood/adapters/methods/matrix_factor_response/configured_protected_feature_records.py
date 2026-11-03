# SPDX-License-Identifier: MPL-2.0
"""Seedless configured causal feature with versioned current prefix ancestry."""
from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledAllocation, ScheduledSource, ScheduledReservation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_sha256, validate_stable_id
from .protected_source_records import _reference
from .response_error_prediction import FEATURES
from .matched_response_prediction import validate_matched_features
from .configured_protected_prefix_records import ConfiguredProtectedE3CausalPrefix, ConfiguredProtectedE3NumericalAssessment, ConfiguredProtectedE3PrefixWitness, ConfiguredProtectedE3FrameAssessment

@dataclass(frozen=True, slots=True)
class ConfiguredProtectedE3CausalFeature(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/configured-protected-causal-feature"
    VERSION: ClassVar[str] = "3.0.0"
    record_id: str
    source_manifest: ObjectIdentity
    public_source: ScheduledPublicSource
    prefix: ObjectIdentity
    frame_sha256: str | None
    disposition: str
    values: tuple[tuple[str, Decimal], ...]
    evidence: tuple[ObjectIdentity, ...]
    physical_forecast: ObjectIdentity | None = None
    fine_response_defect: Decimal | None = None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.public_source) is not ScheduledPublicSource or type(self.evidence) is not tuple
                or len(self.evidence) != (4 if self.physical_forecast is None else 5)
                or any(type(row) is not ObjectIdentity for row in self.evidence)):
            raise TypeError("source-bound E3 feature requires its exact seedless source and current products")
        self.public_source.__post_init__()
        _reference(self.source_manifest, ScheduledAllocation)
        _reference(self.public_source.source, ScheduledSource)
        _reference(self.public_source.reservation, ScheduledReservation)
        _reference(self.prefix, ConfiguredProtectedE3CausalPrefix)
        kinds = (ConfiguredProtectedE3CausalPrefix, ConfiguredProtectedE3NumericalAssessment, ConfiguredProtectedE3PrefixWitness, ConfiguredProtectedE3FrameAssessment)
        expected = {(kind.SCHEMA, kind.VERSION) for kind in kinds}
        if self.physical_forecast is not None:
            from .configured_protected_response_records import ConfiguredProtectedE3PhysicalForecast
            _reference(self.physical_forecast, ConfiguredProtectedE3PhysicalForecast)
            expected.add((ConfiguredProtectedE3PhysicalForecast.SCHEMA, ConfiguredProtectedE3PhysicalForecast.VERSION))
            if self.physical_forecast not in self.evidence:
                raise ValueError('matched E3 feature drops its actual pre-future mechanical parent')
        if (self.source_manifest != self.public_source.allocation
                or tuple(row.object_id for row in self.evidence) != tuple(sorted({row.object_id for row in self.evidence}))
                or {(row.object_schema, row.object_version) for row in self.evidence} != expected
                or self.prefix not in self.evidence):
            raise ValueError("source-bound E3 feature changes original allocation or complete current evidence")
        if (self.disposition not in ("AVAILABLE", "NO_CAUSAL_ORIGIN", "UNAVAILABLE", "REFUSED")
                or type(self.values) is not tuple
                or self.physical_forecast is None and (tuple(name for name, _ in self.values) != FEATURES
                    if self.disposition == "AVAILABLE" else bool(self.values))
                or self.disposition == "AVAILABLE" and (self.frame_sha256 is None or dict(self.values)["cutoff"] != self.cutoff)):
            raise ValueError("source-bound E3 feature changes original values, frame, cutoff or nonuse")
        if self.frame_sha256 is not None:
            validate_sha256(self.frame_sha256)
        if self.physical_forecast is None:
            if self.fine_response_defect is not None:
                raise ValueError('causal defect diagnostic lacks its original mechanical parent')
            for _, value in self.values:
                validate_decimal(value, field_name="source-bound causal feature", minimum=Decimal(0))
        else:
            validate_matched_features(self.values, self.disposition)
            if self.fine_response_defect is not None:
                validate_decimal(self.fine_response_defect, field_name='FINE causal response defect', minimum=Decimal(0))
        for row in self.evidence:
            row.__post_init__()

    @property
    def unit_id(self):
        return self.public_source.root.independent_group_id

    @property
    def native_source(self):
        return self.public_source.source

    @property
    def origin(self):
        return self.prefix

    @property
    def clock_id(self):
        return self.public_source.root.clock_id

    @property
    def cutoff(self):
        return self.public_source.coordinate.physical_time(self.public_source.policy.cutoff_tick)
