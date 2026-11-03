# SPDX-License-Identifier: MPL-2.0
"""Complete corrected custody at revision 2.1; original records remain references.

The uninstalled 2.0 header checkpoint is retained in its exact review packet.
These records describe custody; resolving actual evidence belongs to the typed
views and the eventual owning input ports, never a label or a cached verdict.
"""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord,
    require_sorted_unique_ids,
    require_sorted_unique_strings,
    validate_decimal,
    validate_sha256,
    validate_stable_id,
)
from .config_v2 import VirtualCellPipelineSelectionV2
from .contracts import (
    MetricContract,
    PredictionCommitment,
    VirtualCellSourceManifest,
    VirtualCellSourceObject,
)
from .correction_records_v2 import (
    OfficialMetricSetV2,
    SharedTemplateShiftV2BuildReceipt,
)

RAW_PREDICTION_DELTAS_SCHEMA = (
    "empirical-lawhood/physical/virtual-cell/predicted-response-deltas-v2"
)
MODEL_SCHEMA = "empirical-lawhood/physical/virtual-cell/linear-model-safetensors"
ENVELOPE_SCHEMA = "empirical-lawhood/physical/virtual-cell/prediction-h5ad-envelope"
ROSTER_SCHEMA = "empirical-lawhood/physical/virtual-cell/test-roster-csv"
FIT_SCHEMA = "empirical-lawhood/physical/virtual-cell/model-fit-record"
BINDING_SCHEMA = "empirical-lawhood/physical/virtual-cell/model-artifact-binding"
SCORE_SCHEMA = "empirical-lawhood/physical/virtual-cell/official-aggregate-score"
TOURNAMENT_SCHEMA = "empirical-lawhood/physical/virtual-cell/tournament-record"
SUMMARY_SCHEMA = "empirical-lawhood/physical/virtual-cell/response-summary-record"
PANEL_SCHEMA = "empirical-lawhood/physical/virtual-cell/falsifier-panel"


def _reference(value, schema, version="1.0.0"):
    if type(value) is not ObjectIdentity or (
        value.object_schema,
        value.object_version,
    ) != (schema, version):
        raise ValueError(
            "corrected custody reference changes its exact schema or revision"
        )
    value.__post_init__()


def _selection(value):
    _reference(
        value,
        VirtualCellPipelineSelectionV2.SCHEMA,
        VirtualCellPipelineSelectionV2.VERSION,
    )


def _artifact(value, schema, media_type):
    if (
        type(value) is not ArtifactIdentity
        or (value.payload_schema, value.media_type) != (schema, media_type)
        or type(value.size_bytes) is not int
        or value.size_bytes <= 0
    ):
        raise ValueError(
            "corrected custody changes exact artifact schema, media or positive size"
        )
    value.__post_init__()


def _ids(values, name):
    if type(values) is not tuple:
        raise TypeError("corrected custody requires an immutable complete census")
    require_sorted_unique_strings(values, field_name=name, allow_empty=False)


def registry_sha256(values):
    digest = sha256()
    for value in values:
        raw = value.encode("utf-8")
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class CandidateValidationRecordV2(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/physical/virtual-cell/corrected-candidate-validation"
    )
    VERSION: ClassVar[str] = "2.1.0"
    candidate_id: str
    selection: ObjectIdentity
    model_fit: ObjectIdentity
    prediction_build: ObjectIdentity
    metrics: ObjectIdentity
    aggregate_score: ObjectIdentity
    metrics_artifact: ArtifactIdentity
    target_ids: tuple[str, ...]
    metric_contract: ObjectIdentity
    score_standard_error: Decimal
    outcome_access: OutcomeAccess

    def __post_init__(self):
        validate_stable_id(self.candidate_id)
        _selection(self.selection)
        for value, schema, version in (
            (self.model_fit, FIT_SCHEMA, "1.0.0"),
            (
                self.prediction_build,
                SharedTemplateShiftV2BuildReceipt.SCHEMA,
                SharedTemplateShiftV2BuildReceipt.VERSION,
            ),
            (self.metrics, OfficialMetricSetV2.SCHEMA, OfficialMetricSetV2.VERSION),
            (self.aggregate_score, SCORE_SCHEMA, "1.0.0"),
            (self.metric_contract, MetricContract.SCHEMA, MetricContract.VERSION),
        ):
            _reference(value, schema, version)
        _artifact(self.metrics_artifact, OfficialMetricSetV2.SCHEMA, "application/json")
        _ids(self.target_ids, "target_ids")
        validate_decimal(
            self.score_standard_error,
            field_name="score_standard_error",
            minimum=Decimal(0),
        )
        if (
            self.metrics_artifact.sha256 != self.metrics.object_fingerprint
            or self.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
        ):
            raise ValueError(
                "corrected validation changes actual metric bytes or development-only access"
            )


@dataclass(frozen=True, slots=True)
class ModelDevelopmentRecordV2(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/physical/virtual-cell/corrected-model-development"
    )
    VERSION: ClassVar[str] = "2.1.0"
    record_id: str
    selection: ObjectIdentity
    source_manifest: ObjectIdentity
    training_summary: ObjectIdentity
    validation_summary: ObjectIdentity
    feature_provenance_sha256: str
    models: tuple[ObjectIdentity, ...]
    validations: tuple[CandidateValidationRecordV2, ...]
    tournament: ObjectIdentity
    training_target_ids: tuple[str, ...]
    validation_target_ids: tuple[str, ...]
    final_outcome_parent_ids: tuple[str, ...]
    leaderboard_parent_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        _selection(self.selection)
        _reference(
            self.source_manifest,
            VirtualCellSourceManifest.SCHEMA,
            VirtualCellSourceManifest.VERSION,
        )
        for value in (self.training_summary, self.validation_summary):
            _reference(value, SUMMARY_SCHEMA)
        validate_sha256(self.feature_provenance_sha256)
        if type(self.models) is not tuple or not self.models:
            raise TypeError(
                "corrected development requires its complete original model-binding census"
            )
        require_sorted_unique_ids(
            self.models, attribute="object_id", field_name="models"
        )
        for value in self.models:
            _reference(value, BINDING_SCHEMA)
        if (
            type(self.validations) is not tuple
            or not self.validations
            or any(
                type(value) is not CandidateValidationRecordV2
                for value in self.validations
            )
        ):
            raise TypeError(
                "corrected development requires its typed complete validation census"
            )
        require_sorted_unique_ids(
            self.validations, attribute="candidate_id", field_name="validations"
        )
        for value in self.validations:
            value.__post_init__()
        _reference(self.tournament, TOURNAMENT_SCHEMA)
        _ids(self.training_target_ids, "training_target_ids")
        _ids(self.validation_target_ids, "validation_target_ids")
        if (
            set(self.training_target_ids) & set(self.validation_target_ids)
            or any(
                value.selection != self.selection
                or value.target_ids != self.validation_target_ids
                for value in self.validations
            )
            or type(self.final_outcome_parent_ids) is not tuple
            or type(self.leaderboard_parent_ids) is not tuple
            or self.final_outcome_parent_ids
            or self.leaderboard_parent_ids
        ):
            raise ValueError(
                "corrected development changes complete disjoint targets, selection or outcome-blind lineage"
            )


@dataclass(frozen=True, slots=True)
class ModelSelectionRecordV2(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/physical/virtual-cell/corrected-model-selection"
    )
    VERSION: ClassVar[str] = "2.1.0"
    record_id: str
    selection: ObjectIdentity
    development: ObjectIdentity
    tournament: ObjectIdentity
    falsifier_panel: ObjectIdentity
    selected_model: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.record_id)
        _selection(self.selection)
        for value, schema, version in (
            (
                self.development,
                ModelDevelopmentRecordV2.SCHEMA,
                ModelDevelopmentRecordV2.VERSION,
            ),
            (self.tournament, TOURNAMENT_SCHEMA, "1.0.0"),
            (self.falsifier_panel, PANEL_SCHEMA, "1.0.0"),
            (self.selected_model, BINDING_SCHEMA, "1.0.0"),
        ):
            _reference(value, schema, version)


@dataclass(frozen=True, slots=True)
class PredictionFreezeRecordV2(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/physical/virtual-cell/corrected-prediction-freeze"
    )
    VERSION: ClassVar[str] = "2.1.0"
    record_id: str
    selection: ObjectIdentity
    model_selection: ObjectIdentity
    source_manifest: ObjectIdentity
    metric_contract: ObjectIdentity
    model_fit: ObjectIdentity
    model_id: str
    model_artifact: ArtifactIdentity
    commitment: PredictionCommitment
    build: SharedTemplateShiftV2BuildReceipt
    target_ids: tuple[str, ...]
    gene_ids: tuple[str, ...]
    roster: ObjectIdentity
    target_roster_artifact: ArtifactIdentity
    predicted_deltas: ArtifactIdentity
    envelope: ArtifactIdentity

    def __post_init__(self):
        validate_stable_id(self.record_id)
        _selection(self.selection)
        _reference(
            self.model_selection,
            ModelSelectionRecordV2.SCHEMA,
            ModelSelectionRecordV2.VERSION,
        )
        _reference(
            self.source_manifest,
            VirtualCellSourceManifest.SCHEMA,
            VirtualCellSourceManifest.VERSION,
        )
        _reference(self.metric_contract, MetricContract.SCHEMA, MetricContract.VERSION)
        _reference(self.model_fit, FIT_SCHEMA)
        validate_stable_id(self.model_id)
        _artifact(self.model_artifact, MODEL_SCHEMA, "application/x-safetensors")
        if (
            type(self.commitment) is not PredictionCommitment
            or type(self.build) is not SharedTemplateShiftV2BuildReceipt
        ):
            raise TypeError(
                "corrected freeze requires its actual commitment and v2 compiler receipt"
            )
        self.commitment.__post_init__()
        self.build.__post_init__()
        _ids(self.target_ids, "target_ids")
        if (
            type(self.gene_ids) is not tuple
            or not self.gene_ids
            or len(set(self.gene_ids)) != len(self.gene_ids)
            or any(not value for value in self.gene_ids)
        ):
            raise ValueError(
                "corrected freeze requires its exact ordered unique gene registry"
            )
        _reference(
            self.roster, "empirical-lawhood/physical/virtual-cell/prediction-roster"
        )
        _artifact(self.target_roster_artifact, ROSTER_SCHEMA, "text/csv")
        _artifact(
            self.predicted_deltas,
            RAW_PREDICTION_DELTAS_SCHEMA,
            "application/octet-stream",
        )
        _artifact(self.envelope, ENVELOPE_SCHEMA, "application/x-hdf5")
        shape = len(self.target_ids), len(self.gene_ids)
        if (
            (
                self.commitment.config_sha256,
                self.commitment.prediction_sha256,
                self.commitment.gene_order_sha256,
                self.commitment.model_id,
                self.commitment.model_sha256,
                self.commitment.target_roster_sha256,
            )
            != (
                self.selection.object_fingerprint,
                self.build.h5ad_sha256,
                registry_sha256(self.gene_ids),
                self.model_id,
                self.model_artifact.sha256,
                self.target_roster_artifact.sha256,
            )
            or self.build.gene_order_sha256 != self.commitment.gene_order_sha256
            or self.source_manifest.object_fingerprint
            != self.commitment.source_manifest_sha256
            or self.metric_contract.object_fingerprint
            != self.commitment.metric_contract_sha256
            or self.build.roster_sha256 != self.roster.object_fingerprint
            or (self.build.target_count, self.build.gene_count) != shape
            or self.predicted_deltas.sha256 != self.build.predicted_delta_sha256
            or self.predicted_deltas.size_bytes
            != len(str(shape).encode("ascii")) + shape[0] * shape[1] * 8
        ):
            raise ValueError(
                "corrected freeze changes actual model, selection, roster, raw actions or compiler bytes"
            )


@dataclass(frozen=True, slots=True)
class OfficialEvaluationRecordV2(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/physical/virtual-cell/corrected-official-evaluation"
    )
    VERSION: ClassVar[str] = "2.1.0"
    evaluation_id: str
    selection: ObjectIdentity
    prediction_freeze: ObjectIdentity
    prediction_commitment_sha256: str
    source_binding: ObjectIdentity
    metric_contract: ObjectIdentity
    metrics: ObjectIdentity
    metrics_artifact: ArtifactIdentity
    aggregate_score: ObjectIdentity
    target_ids: tuple[str, ...]
    cell_eval_version: str
    pdex_version: str
    outcome_access: OutcomeAccess

    def __post_init__(self):
        validate_stable_id(self.evaluation_id)
        _selection(self.selection)
        for value, schema, version in (
            (
                self.prediction_freeze,
                PredictionFreezeRecordV2.SCHEMA,
                PredictionFreezeRecordV2.VERSION,
            ),
            (
                self.source_binding,
                VirtualCellSourceObject.SCHEMA,
                VirtualCellSourceObject.VERSION,
            ),
            (self.metric_contract, MetricContract.SCHEMA, MetricContract.VERSION),
            (self.metrics, OfficialMetricSetV2.SCHEMA, OfficialMetricSetV2.VERSION),
            (self.aggregate_score, SCORE_SCHEMA, "1.0.0"),
        ):
            _reference(value, schema, version)
        validate_sha256(self.prediction_commitment_sha256)
        _artifact(self.metrics_artifact, OfficialMetricSetV2.SCHEMA, "application/json")
        _ids(self.target_ids, "target_ids")
        if (
            self.metrics_artifact.sha256 != self.metrics.object_fingerprint
            or (self.cell_eval_version, self.pdex_version) != ("0.6.6", "0.1.26")
            or self.outcome_access is not OutcomeAccess.EVALUATOR_REVEAL
        ):
            raise ValueError(
                "corrected evaluation changes original receiver, actual metric bytes or exact reveal scope"
            )
