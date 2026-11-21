# SPDX-License-Identifier: MPL-2.0
"""A complete temperature-domain transformation composing a reusable method.

The companion v1_method.py is contributor-owned method code, not EL internals.
This example performs no measurement and gives no sensor calibration guarantee.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from decimal import Decimal
import json
from typing import ClassVar

from empirical_lawhood.science import CanonicalRecord, ResourceBudget
from empirical_lawhood.methods import Calculation, RecordOutput
from empirical_lawhood.execution.extensions import ExtensionDeclaration
from v1_method import AFFINE, AffineConfig


@dataclass(frozen=True, slots=True)
class CelsiusReading(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/tutorial/celsius-reading"
    temperature: Decimal
    unit: str = "degC"

    def __post_init__(self) -> None:
        if self.unit != "degC":
            raise ValueError("temperature source must declare degC")
        if type(self.temperature) is not Decimal or not self.temperature.is_finite():
            raise ValueError("temperature must be a finite Decimal")
        if (self.temperature < Decimal("-273.15") or self.temperature > Decimal("1e9")
                or len(self.temperature.as_tuple().digits) > 20
                or not -20 <= self.temperature.as_tuple().exponent <= 12):
            raise ValueError("temperature lies outside the declared physical and tutorial bounds")


@dataclass(frozen=True, slots=True)
class KelvinReading(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/tutorial/kelvin-reading"
    temperature: Decimal
    unit: str = "K"

    def __post_init__(self) -> None:
        if self.unit != "K" or type(self.temperature) is not Decimal:
            raise ValueError("temperature result requires Decimal kelvin")
        if not self.temperature.is_finite() or self.temperature < 0:
            raise ValueError("temperature result must be finite and at least absolute zero")


def convert(config: CelsiusReading, inputs):
    result = AFFINE(AffineConfig(config.temperature, Decimal("1"), Decimal("273.15")))["result"]
    return {"temperature": KelvinReading(result.value)}


TEMPERATURE = Calculation(
    capability_key="tutorial.celsius-to-kelvin", version="1.0.0",
    implementation_id="tutorial.celsius-to-kelvin.v1", config_type=CelsiusReading,
    inputs=(), outputs=(RecordOutput("temperature", KelvinReading, 4096),),
    calculate=convert, resources=ResourceBudget(1, 64 * 1024**2, 0, 30, 4096, 4096),
    applicability="Conversion of supplied Celsius temperatures to kelvin.",
    assumptions=("The source declares Celsius and its own measurement uncertainty.",
                 "This transformation neither acquires nor calibrates a measurement."),
    maximum_config_bytes=4096,
)
EXTENSION = ExtensionDeclaration("tutorial.temperature", TEMPERATURE.version, (TEMPERATURE.operation,))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--celsius", type=Decimal, default=Decimal("0"))
    args = parser.parse_args()
    result = TEMPERATURE(CelsiusReading(args.celsius))["temperature"]
    print(json.dumps({"celsius": str(args.celsius), "kelvin": str(result.temperature),
        "result": result.to_document(), "declaration": TEMPERATURE.describe()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
