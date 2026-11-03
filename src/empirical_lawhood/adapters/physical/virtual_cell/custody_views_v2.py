# SPDX-License-Identifier: MPL-2.0
"""Typed joins of actual canonical evidence; views never impersonate old records.

The future owning ports must authenticate ordinary artifacts and receipts before
supplying these records. No view creates an access grant or scientific warrant.
"""

from dataclasses import dataclass
from types import MappingProxyType

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from .contracts import (
    MetricContract,
    VirtualCellSourceManifest,
    VirtualCellSourceObject,
    VirtualCellSplit,
)
from .correction_records_v2 import (
    MetricSourceSemantics,
    OfficialMetricSetV2,
    SharedTemplateShiftV2BuildReceipt,
)
from .records_v2 import (
    ModelDevelopmentRecordV2,
    ModelSelectionRecordV2,
    PredictionFreezeRecordV2,
    OfficialEvaluationRecordV2,
    registry_sha256,
)


class ActualRecordsV2:
    """An in-memory byte-identity join, not artifact or receipt authentication."""

    def __init__(self, records):
        retained = {}
        for reference, record in records:
            if (
                type(reference) is not ObjectIdentity
                or not isinstance(record, CanonicalRecord)
                or ObjectIdentity.from_record(reference.object_id, record) != reference
                or reference in retained
            ):
                raise ValueError(
                    "actual record set changes or repeats an original canonical identity"
                )
            record.__post_init__()
            retained[reference] = record
        self.records = MappingProxyType(retained)

    def resolve(self, reference, kind):
        value = self.records.get(reference)
        if (
            type(value) is not kind
            or ObjectIdentity.from_record(reference.object_id, value) != reference
        ):
            raise ValueError(
                "custody view lacks the exact original canonical object, revision or bytes"
            )
        value.__post_init__()
        return value


def _selected(record, selection, original):
    selection.__post_init__()
    selection.validate_original(original)
    record.__post_init__()
    if record.selection != selection.identity:
        raise ValueError(
            "custody view changes its actual selected corrected configuration"
        )


def _metrics(candidate, evidence, selection, contract):
    from .analysis import OfficialAggregateScore
    from .metric_correction_v2 import score_corrected_metrics

    metric = evidence.resolve(candidate.metrics, OfficialMetricSetV2)
    score = evidence.resolve(candidate.aggregate_score, OfficialAggregateScore)
    role = ("validation." + candidate.candidate_id if hasattr(candidate, "candidate_id")
            else "final." + candidate.evaluation_id)
    if (
        candidate.metrics.object_id != "metrics." + role
        or candidate.aggregate_score.object_id != "score." + role
        or
        candidate.metric_contract
        != ObjectIdentity.from_record(contract.contract_id, contract)
        or metric.gauge != selection.metric_gauge
        or metric.target_ids != candidate.target_ids
        or metric.source_semantics is not MetricSourceSemantics.OFFICIAL_SOURCE_COLUMNS
        or metric.original_artifact_sha256 is not None
        or candidate.metrics_artifact.size_bytes != len(metric.canonical_bytes())
        or score != score_corrected_metrics(metric, metric_contract=contract)
    ):
        raise ValueError(
            "custody view changes the actual corrected receiver, complete metrics or original baseline score"
        )
    return metric, score


@dataclass(frozen=True, slots=True)
class DevelopmentViewV2:
    record: ModelDevelopmentRecordV2
    models: tuple
    tournament: CanonicalRecord

    def fingerprint(self):
        return self.record.fingerprint()

    @property
    def final_outcome_parent_ids(self):
        return self.record.final_outcome_parent_ids

    @property
    def leaderboard_parent_ids(self):
        return self.record.leaderboard_parent_ids


def development_view_v2(record, *, selection, original, evidence):
    from .analysis import ModelFitRecord, TournamentRecord, select_tournament
    from .records import ModelArtifactBinding, ResponseSummaryRecord

    if type(record) is not ModelDevelopmentRecordV2:
        raise TypeError("development view requires its actual corrected record")
    _selected(record, selection, original)
    manifest = evidence.resolve(record.source_manifest, VirtualCellSourceManifest)
    if (
        record.source_manifest.object_id != manifest.manifest_id
        or manifest.fingerprint() != original.source_manifest_sha256
        or record.feature_provenance_sha256 != original.target_feature_provenance_sha256
    ):
        raise ValueError(
            "corrected development changes original source or feature provenance"
        )
    train = evidence.resolve(record.training_summary, ResponseSummaryRecord)
    validation = evidence.resolve(record.validation_summary, ResponseSummaryRecord)
    if (record.training_summary.object_id, record.validation_summary.object_id) != (
        train.record_id,
        validation.record_id,
    ):
        raise ValueError("corrected development relabels original summary roles")
    for summary, split in (
        (train, VirtualCellSplit.TRAIN),
        (validation, VirtualCellSplit.VALIDATION),
    ):
        originals = tuple(
            row
            for row in manifest.objects
            if row.split is split and row.role.startswith("response/")
        )
        if (
            len(originals) != 1
            or summary.split is not split
            or summary.source_object_sha256 != originals[0].sha256
            or summary.summary_spec_sha256 != original.response_summary.fingerprint()
            or summary.gene_order_sha256 != manifest.gene_order_sha256
        ):
            raise ValueError(
                "corrected development changes original summary/source/gene lineage"
            )
    if train.gene_ids != validation.gene_ids:
        raise ValueError(
            "corrected development summaries disagree on the actual gene registry"
        )
    models = tuple(
        evidence.resolve(reference, ModelArtifactBinding) for reference in record.models
    )
    for reference, model in zip(record.models, models, strict=True):
        if reference.object_id != "model-binding." + model.model_id:
            raise ValueError(
                "corrected development changes the code-owned model-binding role"
            )
    candidate_ids = original.model_selection.candidate_ids
    tournament = evidence.resolve(record.tournament, TournamentRecord)
    expected_models = tuple(
        sorted(
            (*candidate_ids, *(value + "-development-refit" for value in candidate_ids))
        )
    )
    if (
        record.tournament.object_id != tournament.tournament_id
        or tuple(sorted(model.model_id for model in models)) != expected_models
        or tuple(value.candidate_id for value in record.validations) != candidate_ids
        or tuple(value.candidate_id for value in tournament.entries) != candidate_ids
    ):
        raise ValueError(
            "corrected development omits complete candidate, refit or tournament denominators"
        )
    by_model = {value.model_id: value for value in models}
    for candidate, entry in zip(record.validations, tournament.entries, strict=True):
        fit = evidence.resolve(candidate.model_fit, ModelFitRecord)
        build = evidence.resolve(
            candidate.prediction_build, SharedTemplateShiftV2BuildReceipt
        )
        _, score = _metrics(
            candidate,
            evidence,
            selection,
            original.model_selection.validation_metric_contract,
        )
        if (
            candidate.prediction_build.object_id != "prediction-build.validation." + candidate.candidate_id
            or candidate.model_fit.object_id != fit.fit_id
            or fit != by_model[candidate.candidate_id].fit
            or fit.training_target_ids_sha256
            != registry_sha256(record.training_target_ids)
            or (build.target_count, build.gene_count, build.seed)
            != (
                len(record.validation_target_ids),
                len(train.gene_ids),
                selection.compiler_contract.compiler_seed,
            )
            or build.gene_order_sha256 != manifest.gene_order_sha256
            or build.maximum_action_error > selection.compiler.mean_tolerance
            or build.maximum_null_mean_error
            > selection.compiler.maximum_null_mean_error
            or (
                entry.validation_des,
                entry.validation_pds,
                entry.validation_mae,
                entry.official_score,
                entry.official_score_standard_error,
                entry.parameter_count,
            )
            != (
                score.des,
                score.pds,
                score.mae,
                score.average_score,
                candidate.score_standard_error,
                fit.parameter_count,
            )
            or entry.eligible is not True
            or entry.reason_codes
        ):
            raise ValueError(
                "corrected development changes actual fit, compiler admission or unchanged tournament inputs"
            )
    expected_tournament = select_tournament(
        tournament_id=tournament.tournament_id, entries=tournament.entries
    )
    if tournament.canonical_bytes() != expected_tournament.canonical_bytes():
        raise ValueError(
            "corrected development tournament differs from the original selection rule or winner"
        )
    joined = registry_sha256(
        tuple(sorted((*record.training_target_ids, *record.validation_target_ids)))
    )
    if any(
        by_model[value + "-development-refit"].fit.training_target_ids_sha256 != joined
        for value in candidate_ids
    ):
        raise ValueError(
            "corrected development refits lose original all-development target lineage"
        )
    return DevelopmentViewV2(
        record, tuple(sorted(models, key=lambda value: value.model_id)), tournament
    )


@dataclass(frozen=True, slots=True)
class SelectionViewV2:
    record: ModelSelectionRecordV2
    tournament: CanonicalRecord
    model: CanonicalRecord

    def fingerprint(self):
        return self.record.fingerprint()

    @property
    def falsifier_panel_sha256(self):
        return self.record.falsifier_panel.object_fingerprint

    @property
    def selected_model_artifact_id(self):
        return self.model.artifact_id

    @property
    def selected_model_sha256(self):
        return self.model.artifact_sha256


def selection_view_v2(record, *, selection, original, evidence):
    from .analysis import TournamentRecord
    from .development import competition_selection_integrity_failures
    from .records import FalsifierPanel, ModelArtifactBinding

    if type(record) is not ModelSelectionRecordV2:
        raise TypeError("selection view requires its actual corrected record")
    _selected(record, selection, original)
    development = evidence.resolve(record.development, ModelDevelopmentRecordV2)
    development_view_v2(
        development, selection=selection, original=original, evidence=evidence
    )
    tournament = evidence.resolve(record.tournament, TournamentRecord)
    panel = evidence.resolve(record.falsifier_panel, FalsifierPanel)
    model = evidence.resolve(record.selected_model, ModelArtifactBinding)
    if (
        record.development.object_id != development.record_id
        or record.falsifier_panel.object_id != panel.panel_id
        or record.tournament.object_id != tournament.tournament_id
        or development.selection != record.selection
        or record.tournament != development.tournament
        or record.selected_model not in development.models
        or model.model_id != tournament.selected_candidate_id + "-development-refit"
        or record.selected_model.object_id != "model-binding." + model.model_id
        or competition_selection_integrity_failures(panel)
    ):
        raise ValueError(
            "corrected selection changes original tournament/integrity/selected-refit joins"
        )
    return SelectionViewV2(record, tournament, model)


@dataclass(frozen=True, slots=True)
class FreezeViewV2:
    record: PredictionFreezeRecordV2
    selected: object

    def fingerprint(self):
        return self.record.fingerprint()

    @property
    def commitment(self):
        return self.record.commitment

    @property
    def h5ad_envelope_artifact_id(self):
        return self.record.envelope.artifact_id

    @property
    def h5ad_envelope_sha256(self):
        return self.record.envelope.sha256

    @property
    def inner_h5ad_sha256(self):
        return self.record.build.h5ad_sha256

    @property
    def test_outcome_read(self):
        return self.record.build.outcome_read


def freeze_view_v2(record, *, selection, original, evidence):
    from .analysis import ModelFitRecord
    from .prediction import PredictionRoster

    if type(record) is not PredictionFreezeRecordV2:
        raise TypeError("freeze view requires its actual corrected record")
    _selected(record, selection, original)
    selected = selection_view_v2(
        evidence.resolve(record.model_selection, ModelSelectionRecordV2),
        selection=selection,
        original=original,
        evidence=evidence,
    )
    fit = evidence.resolve(record.model_fit, ModelFitRecord)
    roster = evidence.resolve(record.roster, PredictionRoster)
    manifest = evidence.resolve(record.source_manifest, VirtualCellSourceManifest)
    contract = evidence.resolve(record.metric_contract, MetricContract)
    compiler = selection.compiler_contract
    if (
        record.model_selection.object_id != selected.record.record_id
        or record.model_fit.object_id != fit.fit_id
        or record.source_manifest.object_id != manifest.manifest_id
        or record.roster.object_id != roster.roster_id
        or record.metric_contract.object_id != contract.contract_id
        or record.model_id != selected.model.model_id
        or record.model_artifact.sha256 != selected.selected_model_sha256
        or record.model_artifact.artifact_id != selected.selected_model_artifact_id
        or fit != selected.model.fit
        or manifest.fingerprint() != original.source_manifest_sha256
        or contract != original.metric_contract
        or record.commitment.frozen_at_utc != compiler.freeze_timestamp_utc
        or roster.prefix_source_sha256 != record.target_roster_artifact.sha256
        or roster.control_label != original.response_summary.comparator_label
        or tuple(value.target_id for value in roster.targets) != record.target_ids
        or roster.total_cell_limit != compiler.total_cell_limit
        or roster.control_cells != compiler.control_cells
        or record.build.row_count != compiler.total_cell_limit
        or record.build.control_cell_count != compiler.control_cells
        or record.build.seed != compiler.compiler_seed
        or record.envelope.size_bytes > compiler.maximum_envelope_bytes
        or any(
            value.allocated_cells < compiler.minimum_cells_per_target
            for value in roster.targets
        )
        or record.build.maximum_action_error > selection.compiler.mean_tolerance
        or record.build.maximum_null_mean_error
        > selection.compiler.maximum_null_mean_error
    ):
        raise ValueError(
            "corrected freeze changes original selected model, source, final metric, allocation or compiler bounds"
        )
    return FreezeViewV2(record, selected)


@dataclass(frozen=True, slots=True)
class EvaluationViewV2:
    record: OfficialEvaluationRecordV2
    score: CanonicalRecord

    def fingerprint(self):
        return self.record.fingerprint()

    @property
    def prediction_commitment_sha256(self):
        return self.record.prediction_commitment_sha256


def evaluation_view_v2(record, *, selection, original, evidence):
    if type(record) is not OfficialEvaluationRecordV2:
        raise TypeError("evaluation view requires its actual corrected record")
    _selected(record, selection, original)
    freeze = evidence.resolve(record.prediction_freeze, PredictionFreezeRecordV2)
    freeze_view_v2(freeze, selection=selection, original=original, evidence=evidence)
    source = evidence.resolve(record.source_binding, VirtualCellSourceObject)
    _metrics(record, evidence, selection, original.metric_contract)
    from .analysis import OfficialAggregateScore

    score = evidence.resolve(record.aggregate_score, OfficialAggregateScore)
    manifest = evidence.resolve(freeze.source_manifest, VirtualCellSourceManifest)
    if (
        record.prediction_freeze.object_id != freeze.record_id
        or record.source_binding.object_id != source.object_id
        or freeze.selection != record.selection
        or record.prediction_commitment_sha256 != freeze.commitment.fingerprint()
        or record.target_ids != freeze.target_ids
        or not source.sealed
        or source.split is not VirtualCellSplit.TEST
        or source not in manifest.objects
        or manifest.fingerprint() != original.source_manifest_sha256
    ):
        raise ValueError(
            "corrected evaluation changes exact sealed test binding or frozen prediction lineage"
        )
    return EvaluationViewV2(record, score)
