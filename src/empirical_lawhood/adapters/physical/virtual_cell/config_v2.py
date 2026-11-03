# SPDX-License-Identifier: MPL-2.0
"""Explicit corrected selections referring to unchanged original contracts."""

from dataclasses import dataclass, replace
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from .contracts import (
    PredictionCompilerContract,
    ProvenanceBoundVirtualCellPipelineConfig,
)
from .correction_records_v2 import (
    OfficialMetricGaugeV2,
    SharedTemplateShiftV2Selection,
    require_metric_contract_gauge,
)


@dataclass(frozen=True, slots=True)
class VirtualCellPipelineSelectionV2(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/physical/virtual-cell/corrected-pipeline-selection"
    )
    VERSION: ClassVar[str] = "2.0.0"

    selection_id: str
    original_config: ObjectIdentity
    compiler: SharedTemplateShiftV2Selection
    metric_gauge: OfficialMetricGaugeV2
    compiler_contract: PredictionCompilerContract

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        if type(self.original_config) is not ObjectIdentity or (
            self.original_config.object_schema,
            self.original_config.object_version,
        ) != (
            ProvenanceBoundVirtualCellPipelineConfig.SCHEMA,
            ProvenanceBoundVirtualCellPipelineConfig.VERSION,
        ):
            raise ValueError(
                "v2 selection requires the exact original pipeline schema and revision"
            )
        self.original_config.__post_init__()
        for value, kind in (
            (self.compiler, SharedTemplateShiftV2Selection),
            (self.metric_gauge, OfficialMetricGaugeV2),
            (self.compiler_contract, PredictionCompilerContract),
        ):
            if type(value) is not kind:
                raise TypeError(
                    "v2 pipeline selection requires its exact scientific contracts"
                )
            value.__post_init__()
        if (
            self.compiler_contract.contract_id,
            self.compiler_contract.mean_tolerance,
            self.compiler_contract.maximum_value,
        ) != (
            self.compiler.compiler_id,
            self.compiler.mean_tolerance,
            self.compiler.maximum_value,
        ):
            raise ValueError(
                "v2 prediction budget substitutes the selected compiler or numerical bounds"
            )

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.selection_id, self)

    def validate_original(self, original):
        if type(original) is not ProvenanceBoundVirtualCellPipelineConfig:
            raise TypeError("v2 runtime requires its actual original pipeline record")
        original.__post_init__()
        if (
            ObjectIdentity.from_record(original.config_id, original)
            != self.original_config
        ):
            raise ValueError(
                "v2 runtime changes its original pipeline identity or bytes"
            )
        expected = replace(
            original.prediction_compiler,
            contract_id=self.compiler.compiler_id,
            mean_tolerance=self.compiler.mean_tolerance,
            maximum_value=self.compiler.maximum_value,
        )
        if self.compiler_contract != expected:
            raise ValueError(
                "v2 runtime changes original row allocation, seed, cutoff or artifact bound"
            )
        for contract in (
            original.metric_contract,
            original.model_selection.validation_metric_contract,
        ):
            require_metric_contract_gauge(
                gauge=self.metric_gauge, metric_contract=contract
            )


def derive_pipeline_selection_v2(
    *, selection_id, original_config, compiler, metric_gauge
):
    """Derive the explicit compiler successor, retaining original budgets."""
    if type(original_config) is not ProvenanceBoundVirtualCellPipelineConfig:
        raise TypeError(
            "v2 selection requires its original typed pipeline configuration"
        )
    if (
        type(compiler) is not SharedTemplateShiftV2Selection
        or type(metric_gauge) is not OfficialMetricGaugeV2
    ):
        raise TypeError("v2 selection requires explicit compiler and metric selections")
    selected = VirtualCellPipelineSelectionV2(
        selection_id,
        ObjectIdentity.from_record(original_config.config_id, original_config),
        compiler,
        metric_gauge,
        replace(
            original_config.prediction_compiler,
            contract_id=compiler.compiler_id,
            mean_tolerance=compiler.mean_tolerance,
            maximum_value=compiler.maximum_value,
        ),
    )
    selected.validate_original(original_config)
    return selected
