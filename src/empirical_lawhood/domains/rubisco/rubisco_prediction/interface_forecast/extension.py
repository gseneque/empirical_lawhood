# SPDX-License-Identifier: MPL-2.0
"""Reconstruct the frozen two-endpoint fit on a single ordinary recursive worker."""

from dataclasses import dataclass
from decimal import Decimal
import json
from typing import ClassVar

from empirical_lawhood.execution.extensions import ExtensionDeclaration
from empirical_lawhood.methods import Calculation, RecordOutput
from empirical_lawhood.science import CanonicalRecord, ResourceBudget
from empirical_lawhood.science.records.serialization import validate_sha256
from ..interface_transfer import fit_predict

KEY = "rubisco.paired-ssu-interface-forecast"
BUDGET = ResourceBudget(1, 512 * 1024**2, 0, 120, 2 * 1024**2, 2 * 1024**2)


@dataclass(frozen=True, slots=True)
class InterfaceInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/ssu-interface-fit-input"
    design_sha256: str
    features_json: str

    def __post_init__(self):
        validate_sha256(self.design_sha256)
        if not isinstance(self.features_json, str) or len(self.features_json) > 65536:
            raise ValueError("Unbounded fit input")
        data = json.loads(self.features_json)
        if set(data) != {"training", "queries"} or not (
            1 <= len(data["training"]) <= 128 and 1 <= len(data["queries"]) <= 256
        ):
            raise ValueError("Labeled training and separate query rows are required")
        for i, name in enumerate(("training", "queries")):
            for row in data[name]:
                required = {"id", "background", "features"} | (
                    {"responses"} if i == 0 else set()
                )
                if set(row) != required:
                    raise ValueError(
                        "Unexpected labels or missing fields in the fitted design"
                    )


@dataclass(frozen=True, slots=True)
class InterfaceOutput(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/ssu-interface-fit-output"
    design_sha256: str
    # Case, method, log turnover, log specificity in the declared order.
    rows: tuple[tuple[str, str, Decimal, Decimal], ...]


def calculate(config, _inputs):
    data = json.loads(config.features_json)
    _, forecasts = fit_predict(data["training"], data["queries"])
    rows = tuple(
        (key, method, *(Decimal(str(x)) for x in forecasts[key][method]))
        for key in sorted(forecasts)
        for method in sorted(forecasts[key])
    )
    return {"forecast": InterfaceOutput(config.design_sha256, rows)}


FIT = Calculation(
    capability_key=KEY,
    version="1.0.0",
    implementation_id="rubisco.ssu-interface-ridge.v1",
    config_type=InterfaceInput,
    inputs=(),
    outputs=(RecordOutput("forecast", InterfaceOutput, 65536),),
    calculate=calculate,
    resources=BUDGET,
    applicability="Two paired endpoint log ratios from annotated SSU features.",
    assumptions=(
        "Independent backgrounds are held out of fitting.",
        "Transfer to a different enzyme requires external evidence.",
    ),
)
EXTENSION = ExtensionDeclaration(KEY, "1.0.0", (FIT.operation,))
