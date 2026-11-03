# SPDX-License-Identifier: MPL-2.0
"""Pure selected v2 records, with unchanged canonical meanings and bytes.

Scientific array/evaluator methods live in their existing selected helper owners.
Historical import paths re-export these exact class objects.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import ClassVar

from empirical_lawhood.kernel.serialization import (
    CanonicalRecord,
    require_sorted_unique_strings,
    validate_decimal,
    validate_sha256,
    validate_stable_id,
)
from .contracts import MetricContract

DES_SOURCE_COLUMN = "overlap_at_N"
PDS_SOURCE_COLUMN = "discrimination_score_l1"
CORRECTIVE_SOURCE_COMMIT = "96bdd9194e0a56a4d27bc6048cbc37816c06be00"


class MetricSourceSemantics(StrEnum):
    OFFICIAL_SOURCE_COLUMNS = "cell-eval-0.6.6-source-columns"
    HISTORICAL_CROSSED_V1 = "historical-crossed-des-pds-v1"


@dataclass(frozen=True, slots=True)
class OfficialMetricGaugeV2(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/physical/virtual-cell/official-metric-gauge"
    )
    VERSION: ClassVar[str] = "2.0.0"

    des_source_column: str = DES_SOURCE_COLUMN
    pds_source_column: str = PDS_SOURCE_COLUMN
    mae_source_column: str = "mae"
    scorer_version: str = "0.6.6"
    pdex_version: str = "0.1.26"

    def __post_init__(self):
        if (
            self.des_source_column,
            self.pds_source_column,
            self.mae_source_column,
            self.scorer_version,
            self.pdex_version,
        ) != (DES_SOURCE_COLUMN, PDS_SOURCE_COLUMN, "mae", "0.6.6", "0.1.26"):
            raise ValueError(
                "corrected metric gauge changes the selected source semantics"
            )


@dataclass(frozen=True, slots=True)
class OfficialMetricSetV2(CanonicalRecord):
    """A new artifact identity; never relabel an original crossed table."""

    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/physical/virtual-cell/corrected-official-metrics"
    )
    VERSION: ClassVar[str] = "2.0.0"

    gauge: OfficialMetricGaugeV2
    source_semantics: MetricSourceSemantics
    original_artifact_sha256: str | None
    target_ids: tuple[str, ...]
    des: tuple[Decimal, ...]
    pds: tuple[Decimal, ...]
    mae: tuple[Decimal, ...]

    def __post_init__(self):
        if type(self.gauge) is not OfficialMetricGaugeV2:
            raise TypeError("corrected metrics require their exact versioned gauge")
        if type(self.source_semantics) is not MetricSourceSemantics:
            raise TypeError("corrected metrics require explicit source semantics")
        require_sorted_unique_strings(
            self.target_ids, field_name="target_ids", allow_empty=False
        )
        for name in ("des", "pds", "mae"):
            values = getattr(self, name)
            if len(values) != len(self.target_ids):
                raise ValueError(
                    "corrected metric vectors change the complete target census"
                )
            for value in values:
                validate_decimal(value, field_name=name)
        if self.original_artifact_sha256 is not None:
            validate_sha256(
                self.original_artifact_sha256, field_name="original_artifact_sha256"
            )
        if (
            self.source_semantics is MetricSourceSemantics.HISTORICAL_CROSSED_V1
            and self.original_artifact_sha256 is None
        ):
            raise ValueError(
                "historical correction must retain the original byte identity"
            )


def require_metric_contract_gauge(*, gauge, metric_contract):
    """Keep final/validation baselines within the exact selected receiver gauge."""
    if (
        type(gauge) is not OfficialMetricGaugeV2
        or type(metric_contract) is not MetricContract
    ):
        raise TypeError(
            "corrected metrics require their exact gauge and metric contract"
        )
    metric_contract.__post_init__()
    if (
        metric_contract.scorer_distribution,
        metric_contract.scorer_version,
        metric_contract.pdex_version,
    ) != ("cell-eval", gauge.scorer_version, gauge.pdex_version):
        raise ValueError(
            "corrected metric contract substitutes the selected evaluator gauge"
        )


@dataclass(frozen=True, slots=True)
class SharedTemplateShiftV2Selection(CanonicalRecord):
    """The donor's selected receiver and action contract, not qualification."""

    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/physical/virtual-cell/shared-template-shift-selection"
    )
    VERSION: ClassVar[str] = "2.0.0"

    compiler_id: str = "compiler.virtual-cell-2025-shared-template-shift-v2"
    receiver_id: str = "receiver.virtual-cell-2025-pdex-marginal-wilcoxon-v1"
    donor_source_commit: str = "859ed3b1780105bdf95e8bbdf954e5cf44285665"
    mean_tolerance: Decimal = Decimal("0.000001")
    maximum_null_mean_error: Decimal = Decimal("0.01")
    maximum_value: Decimal = Decimal("14.999")

    def __post_init__(self):
        if (self.compiler_id, self.receiver_id, self.donor_source_commit) != (
            "compiler.virtual-cell-2025-shared-template-shift-v2",
            "receiver.virtual-cell-2025-pdex-marginal-wilcoxon-v1",
            "859ed3b1780105bdf95e8bbdf954e5cf44285665",
        ):
            raise ValueError(
                "v2 selection changes its selected compiler, receiver or source"
            )
        if (self.mean_tolerance, self.maximum_null_mean_error, self.maximum_value) != (
            Decimal("0.000001"),
            Decimal("0.01"),
            Decimal("14.999"),
        ):
            raise ValueError("v2 selection changes the selected donor receiver bounds")


@dataclass(frozen=True, slots=True)
class SharedTemplateShiftV2BuildReceipt(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/physical/virtual-cell/shared-template-shift-v2-h5ad-build"
    )

    VERSION: ClassVar[str] = "2.0.0"

    selection_sha256: str
    receipt_id: str
    compiler_id: str
    receiver_id: str
    roster_sha256: str
    predicted_delta_sha256: str
    control_reservoir_sha256: str
    template_sha256: str
    gene_order_sha256: str
    h5ad_sha256: str
    row_count: int
    gene_count: int
    target_count: int
    control_cell_count: int
    seed: int
    maximum_null_mean_error: Decimal
    maximum_action_error: Decimal
    saturated_value_count: int
    saturated_value_fraction: Decimal
    maximum_value: Decimal
    output_dtype: str
    outcome_read: bool

    def __post_init__(self) -> None:
        selected = SharedTemplateShiftV2Selection()
        if (self.selection_sha256, self.compiler_id, self.receiver_id) != (
            selected.fingerprint(),
            selected.compiler_id,
            selected.receiver_id,
        ):
            raise ValueError("v2 receipt substitutes its selected meaning")
        validate_stable_id(self.receipt_id, field_name="receipt_id")
        validate_stable_id(self.compiler_id, field_name="compiler_id")
        validate_stable_id(self.receiver_id, field_name="receiver_id")
        for name, digest_value in (
            ("selection_sha256", self.selection_sha256),
            ("roster_sha256", self.roster_sha256),
            ("predicted_delta_sha256", self.predicted_delta_sha256),
            ("control_reservoir_sha256", self.control_reservoir_sha256),
            ("template_sha256", self.template_sha256),
            ("gene_order_sha256", self.gene_order_sha256),
            ("h5ad_sha256", self.h5ad_sha256),
        ):
            validate_sha256(digest_value, field_name=name)
        for name, count_value in (
            ("row_count", self.row_count),
            ("gene_count", self.gene_count),
            ("target_count", self.target_count),
            ("control_cell_count", self.control_cell_count),
        ):
            if isinstance(count_value, bool) or count_value <= 0:
                raise ValueError(f"{name} must be positive")
        if isinstance(self.seed, bool) or self.seed < 0:
            raise ValueError("v2 seed must be nonnegative")
        if self.saturated_value_count < 0:
            raise ValueError("v2 saturation count cannot be negative")
        validate_decimal(
            self.maximum_null_mean_error,
            field_name="maximum_null_mean_error",
            minimum=Decimal("0"),
        )
        validate_decimal(
            self.maximum_action_error,
            field_name="maximum_action_error",
            minimum=Decimal("0"),
        )
        validate_decimal(
            self.saturated_value_fraction,
            field_name="saturated_value_fraction",
            minimum=Decimal("0"),
        )
        if self.saturated_value_fraction > 1:
            raise ValueError("v2 saturation fraction cannot exceed one")
        validate_decimal(
            self.maximum_value, field_name="maximum_value", minimum=Decimal("0")
        )
        if self.output_dtype != "float32":
            raise ValueError("the v2 prediction H5AD must use float32 X")
        if self.outcome_read:
            raise ValueError("v2 prediction construction cannot read test outcomes")
