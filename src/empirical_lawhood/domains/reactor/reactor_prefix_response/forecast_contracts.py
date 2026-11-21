"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_sha256
from empirical_lawhood.domains.reactor.reactor_prefix_response.contracts import ReactorCommand, ReactorMeasurement

REFERENCE_SHA256 = "f19d7a1ce9e70c654eefe31a4adfcf2dcb4241dfccddadbe5b6479649ed1efe8"

@dataclass(frozen=True, slots=True)
class ReactorForecastState(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/reactor-prefix-response/reactor-forecast-state'
    measurement: ReactorMeasurement
    n_a_mol: Decimal
    n_b_mol: Decimal
    volume_m3: Decimal
    t_estimate_k: Decimal
    tj_estimate_k: Decimal
    ua_estimate_w_per_k: Decimal
    kinetic_multiplier: Decimal
    previous_feed_kg_s: Decimal
    previous_jacket_k: Decimal
    reference_feed_kg_s: Decimal
    reference_jacket_k: Decimal

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            if name not in {"SCHEMA", "measurement"}:
                validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
        if self.volume_m3 == 0 or self.kinetic_multiplier == 0:
            raise ValueError("forecast requires positive volume and kinetic multiplier")

@dataclass(frozen=True, slots=True)
class ReactorPointForecast(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/reactor-prefix-response/reactor-point-forecast'
    state_sha256: str
    command: ReactorCommand
    plant_dt_s: Decimal
    peak_temperature_k: Decimal
    endpoint_temperature_k: Decimal
    endpoint_dosed_kg: Decimal
    endpoint_conversion_b: Decimal
    predicted_feed_kg_s: Decimal
    predicted_jacket_k: Decimal

    def __post_init__(self) -> None:
        validate_sha256(self.state_sha256, field_name="state_sha256")
        for name in (
            "peak_temperature_k",
            "endpoint_temperature_k",
            "endpoint_dosed_kg",
            "endpoint_conversion_b",
            "predicted_feed_kg_s",
            "predicted_jacket_k",
        ):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
        if (
            self.plant_dt_s not in (Decimal(1), Decimal("0.5"))
            or self.peak_temperature_k < self.endpoint_temperature_k
            or self.endpoint_conversion_b > 1
        ):
            raise ValueError("point forecast has invalid numerical or receiver coordinates")
