# SPDX-License-Identifier: MPL-2.0
"""A complete pure method contribution using only supported EL contracts."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from decimal import Decimal, localcontext
import json
from typing import ClassVar

from empirical_lawhood.science import CanonicalRecord, ResourceBudget
from empirical_lawhood.methods import Calculation, RecordOutput
from empirical_lawhood.execution.extensions import ExtensionDeclaration


def _scalar(value: Decimal) -> None:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError("affine scalar values must be finite Decimal values")
    if abs(value) > Decimal("1e12") or len(value.as_tuple().digits) > 20 or not -20 <= value.as_tuple().exponent <= 12:
        raise ValueError("affine scalar values exceed the declared tutorial bound")


@dataclass(frozen=True, slots=True)
class AffineConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/tutorial/affine-config"
    value: Decimal
    scale: Decimal
    offset: Decimal

    def __post_init__(self) -> None:
        for value in (self.value, self.scale, self.offset):
            _scalar(value)


@dataclass(frozen=True, slots=True)
class AffineResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/tutorial/affine-result"
    value: Decimal

    def __post_init__(self) -> None:
        if type(self.value) is not Decimal or not self.value.is_finite():
            raise ValueError("affine result must be a finite Decimal")


def calculate(config: AffineConfig, inputs):
    with localcontext() as context:
        context.prec = 50
        return {"result": AffineResult(config.value * config.scale + config.offset)}


AFFINE = Calculation(
    capability_key="tutorial.affine", version="1.0.0",
    implementation_id="tutorial.affine.decimal50.v1", config_type=AffineConfig,
    inputs=(), outputs=(RecordOutput("result", AffineResult, 4096),),
    calculate=calculate, resources=ResourceBudget(1, 64 * 1024**2, 0, 30, 4096, 4096),
    applicability="Finite supplied scalar affine transformations within the declared bounds.",
    assumptions=("The caller owns unit meaning and uncertainty.", "Decimal arithmetic uses precision 50."),
    maximum_config_bytes=4096,
)
EXTENSION = ExtensionDeclaration(AFFINE.capability_key, AFFINE.version, (AFFINE.operation,))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--value", type=Decimal, default=Decimal("2"))
    parser.add_argument("--scale", type=Decimal, default=Decimal("3"))
    parser.add_argument("--offset", type=Decimal, default=Decimal("0.5"))
    args = parser.parse_args()
    result = AFFINE(AffineConfig(args.value, args.scale, args.offset))["result"]
    print(json.dumps({"value": str(result.value), "result": result.to_document(),
        "declaration": AFFINE.describe(), "registered_operations": len(EXTENSION.operations)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
