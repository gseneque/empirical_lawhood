# SPDX-License-Identifier: MPL-2.0
"""Exposed tiny metadata/array software controls; no physical source or grant."""
from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.adapters.physical.virtual_cell import analysis, custody_views_v2 as views, development, runtime
from empirical_lawhood.adapters.physical.virtual_cell.contracts import PredictionCommitment, SplitCardinality, VirtualCellSourceManifest, VirtualCellSourceObject, VirtualCellSourcePart, VirtualCellSplit
from empirical_lawhood.adapters.physical.virtual_cell.correction_records_v2 import OfficialMetricGaugeV2, OfficialMetricSetV2, MetricSourceSemantics
from empirical_lawhood.adapters.physical.virtual_cell.metric_correction_v2 import score_corrected_metrics
from empirical_lawhood.adapters.physical.virtual_cell.prediction import PredictionRoster, PredictionTargetAllocation
from empirical_lawhood.adapters.physical.virtual_cell.prediction_payload_v2 import encode_raw_prediction_deltas_v2, decode_raw_prediction_deltas_v2
from empirical_lawhood.adapters.physical.virtual_cell.receiver_observation_v2 import ReceiverObservation, CandidateValidationObservationV2
from empirical_lawhood.adapters.physical.virtual_cell.records import ResponseSummaryRecord, ModelArtifactBinding, FalsifierPanel
from empirical_lawhood.adapters.physical.virtual_cell.records_v2 import CandidateValidationRecordV2, ModelDevelopmentRecordV2, ModelSelectionRecordV2, PredictionFreezeRecordV2, OfficialEvaluationRecordV2, RAW_PREDICTION_DELTAS_SCHEMA, MODEL_SCHEMA, ROSTER_SCHEMA, ENVELOPE_SCHEMA, registry_sha256
from tests.test_virtual_cell_runtime_v2 import _original_config, _selection, _build_receipt


def _identity(name, record):
    return ObjectIdentity.from_record(name, record)


def _artifact(name, schema, media, digest, size):
    return ArtifactIdentity(name, "exposed-software", schema, digest, media, size)


def fixture():
    """Real typed records with synthetic metadata; no represented physical bytes."""
    genes = ("gene.a", "gene.b")
    train_ids, validation_ids, test_ids = ("train.a",), ("validation.a",), ("test.a",)
    gene_hash = registry_sha256(genes)
    objects = []
    for split, role in ((VirtualCellSplit.SHARED, "registry/genes"), (VirtualCellSplit.TRAIN, "response/development"),
            (VirtualCellSplit.VALIDATION, "response/development"), (VirtualCellSplit.TEST, "response/sealed")):
        name = "source." + split.value.lower()
        objects.append(VirtualCellSourceObject(name, split, role, name, "generation.exposed", 1, "d" * 64,
            "AAAAAA==", "application/octet-stream", (VirtualCellSourcePart("part." + name, name + ".bin", 1, "d" * 64),), split is VirtualCellSplit.TEST))
    manifest = VirtualCellSourceManifest("manifest.exposed", "release.exposed", "https://example.invalid/exposed", "storage.exposed", "terms.exposed",
        "receipt.exposed", "d" * 64, 2, gene_hash, tuple(SplitCardinality(split, 1, 1) for split in
            (VirtualCellSplit.TEST, VirtualCellSplit.TRAIN, VirtualCellSplit.VALIDATION)), tuple(sorted(objects, key=lambda value: value.object_id)), 4, True)
    original = _original_config()
    original = replace(original, source_manifest_sha256=manifest.fingerprint(), prediction_compiler=replace(original.prediction_compiler,
        total_cell_limit=3, control_cells=1, minimum_cells_per_target=1, control_reservoir_cells=4))
    selected = _selection(original)
    records = {}
    def retain(name, record):
        identity = _identity(name, record)
        records[identity] = record
        return identity
    source_ref = retain(manifest.manifest_id, manifest)
    def summary(split):
        record = ResponseSummaryRecord("summary." + split.value.lower(), split, "d" * 64, original.response_summary.fingerprint(),
            "table." + split.value.lower(), "d" * 64, 2, 2, 1, 2, genes, gene_hash, original.response_summary.normalization,
            original.response_summary.normalization_target_sum, "non-targeting", original.response_summary.aggregation_unit, OutcomeAccess.DEVELOPMENT_VISIBLE)
        return retain(record.record_id, record)
    train, validation = summary(VirtualCellSplit.TRAIN), summary(VirtualCellSplit.VALIDATION)
    metric_contract = original.model_selection.validation_metric_contract
    validation_contract = retain(metric_contract.contract_id, metric_contract)
    raw = encode_raw_prediction_deltas_v2(values=np.asarray([[-.4, 1.2]]), target_ids=test_ids, gene_ids=genes)
    roster = PredictionRoster("roster.exposed", "d" * 64, (PredictionTargetAllocation("test.a", 2, D(100), 2),), "non-targeting", 1, 3, "EXPOSED_SOFTWARE")
    build = replace(_build_receipt(), gene_order_sha256=gene_hash, seed=selected.compiler_contract.compiler_seed,
        roster_sha256=roster.fingerprint(), predicted_delta_sha256=sha256(raw).hexdigest())
    models, validations, entries = [], [], []
    by_model = {}
    for candidate_id in original.model_selection.candidate_ids:
        for model_id, target_ids in ((candidate_id, train_ids), (candidate_id + "-development-refit", tuple(sorted((*train_ids, *validation_ids))))):
            fit = analysis.ModelFitRecord("fit." + model_id, model_id, analysis.ModelFamily.NO_CHANGE_BASELINE,
                registry_sha256(target_ids), original.target_feature_provenance_sha256, "d" * 64, D(0), None, 1, D(0), D(1), True)
            retain(fit.fit_id, fit)
            binding = ModelArtifactBinding(model_id, "artifact." + model_id, "d" * 64, fit)
            models.append(retain("model-binding." + model_id, binding))
            by_model[model_id] = binding
        metrics = OfficialMetricSetV2(OfficialMetricGaugeV2(), MetricSourceSemantics.OFFICIAL_SOURCE_COLUMNS, None,
            validation_ids, (D('.2'),), (D('.8'),), (D('.01'),))
        metric_ref = retain("metrics.validation." + candidate_id, metrics)
        score = score_corrected_metrics(metrics, metric_contract=metric_contract)
        score_ref = retain("score.validation." + candidate_id, score)
        validations.append(CandidateValidationRecordV2(candidate_id, selected.identity,
            _identity(by_model[candidate_id].fit.fit_id, by_model[candidate_id].fit), retain("prediction-build.validation." + candidate_id, build),
            metric_ref, score_ref, _artifact("artifact.metrics." + candidate_id, metrics.SCHEMA, "application/json", metrics.fingerprint(), len(metrics.canonical_bytes())),
            validation_ids, validation_contract, D(0), OutcomeAccess.DEVELOPMENT_VISIBLE))
        entries.append(analysis.TournamentEntry(candidate_id, score.des, score.pds, score.mae, score.average_score, D(0), 1, True, ()))
    tournament = analysis.select_tournament(tournament_id="tournament.exposed", entries=tuple(entries))
    tournament_ref = retain(tournament.tournament_id, tournament)
    development_record = ModelDevelopmentRecordV2("development.exposed", selected.identity, source_ref, train, validation,
        original.target_feature_provenance_sha256, tuple(sorted(models, key=lambda row: row.object_id)), tuple(validations), tournament_ref,
        train_ids, validation_ids, (), ())
    development_ref = retain(development_record.record_id, development_record)
    sentinels = tuple(sorted(development.COMPETITION_SELECTION_INTEGRITY_FALSIFIER_IDS))
    panel = FalsifierPanel("panel.exposed", tuple(analysis.FalsifierResult(name, True, D(1), D(0), "GE", ()) for name in sentinels), sentinels, True)
    binding = by_model[tournament.selected_candidate_id + "-development-refit"]
    selection_record = ModelSelectionRecordV2("selection.exposed", selected.identity, development_ref, tournament_ref,
        retain(panel.panel_id, panel), _identity("model-binding." + binding.model_id, binding))
    selection_ref = retain(selection_record.record_id, selection_record)
    final_contract = retain(original.metric_contract.contract_id, original.metric_contract)
    commitment = PredictionCommitment("commitment.exposed", "lane.exposed", binding.model_id, binding.artifact_sha256, selected.fingerprint(),
        manifest.fingerprint(), "d" * 64, original.metric_contract.fingerprint(), build.h5ad_sha256, "d" * 64, "d" * 64, gene_hash,
        selected.compiler_contract.freeze_timestamp_utc, (), ())
    freeze = PredictionFreezeRecordV2("freeze.exposed", selected.identity, selection_ref, source_ref, final_contract,
        _identity(binding.fit.fit_id, binding.fit), binding.model_id,
        _artifact(binding.artifact_id, MODEL_SCHEMA, "application/x-safetensors", binding.artifact_sha256, 1), commitment, build,
        test_ids, genes, retain(roster.roster_id, roster), _artifact("roster.source", ROSTER_SCHEMA, "text/csv", "d" * 64, 1),
        _artifact("deltas.exposed", RAW_PREDICTION_DELTAS_SCHEMA, "application/octet-stream", sha256(raw).hexdigest(), len(raw)),
        _artifact("envelope.exposed", ENVELOPE_SCHEMA, "application/x-hdf5", "d" * 64, 1))
    freeze_ref = retain(freeze.record_id, freeze)
    metrics = replace(metrics, target_ids=test_ids)
    metric_ref = retain("metrics.final.evaluation.exposed", metrics)
    final_score = score_corrected_metrics(metrics, metric_contract=original.metric_contract)
    score_ref = retain("score.final.evaluation.exposed", final_score)
    test_source = next(row for row in manifest.objects if row.split is VirtualCellSplit.TEST)
    evaluation = OfficialEvaluationRecordV2("evaluation.exposed", selected.identity, freeze_ref, commitment.fingerprint(),
        retain(test_source.object_id, test_source), final_contract, metric_ref,
        _artifact("metrics.final", metrics.SCHEMA, "application/json", metrics.fingerprint(), len(metrics.canonical_bytes())), score_ref,
        test_ids, "0.6.6", "0.1.26", OutcomeAccess.EVALUATOR_REVEAL)
    retain(evaluation.evaluation_id, evaluation)
    return SimpleNamespace(original=original, selection=selected, records=records, evidence=views.ActualRecordsV2(records.items()),
        development=development_record, model_selection=selection_record, freeze=freeze, evaluation=evaluation, raw=raw)


def test_complete_successors_and_views_forward_actual_new_identity():
    case = fixture()
    for kind, record in ((views.development_view_v2, case.development), (views.selection_view_v2, case.model_selection),
            (views.freeze_view_v2, case.freeze), (views.evaluation_view_v2, case.evaluation)):
        observed = kind(record, selection=case.selection, original=case.original, evidence=case.evidence)
        assert observed.record is record and observed.fingerprint() == record.fingerprint()
        assert not isinstance(observed, type(record))
        assert record.VERSION == '2.1.0'
        assert decode_canonical_bytes(record.canonical_bytes(), type(record), maximum_bytes=65536) == record


@pytest.mark.parametrize('field', ['metrics', 'model-role', 'target-census', 'envelope', 'original-config'])
def test_complete_custody_refuses_actual_identity_and_census_substitution(field):
    case = fixture()
    if field == 'metrics':
        reference = case.development.validations[0].metrics
        changed = replace(case.records[reference], pds=(D('.1'),))
        with pytest.raises(ValueError, match='canonical identity'):
            views.ActualRecordsV2([(key, changed if key == reference else value) for key, value in case.records.items()])
    elif field == 'model-role':
        reference = case.development.models[0]
        alias = replace(reference, object_id='model-binding.unrelated')
        records = {alias if key == reference else key: value for key, value in case.records.items()}
        record = replace(case.development, models=tuple(sorted((alias if key == reference else key for key in case.development.models), key=lambda row: row.object_id)))
        with pytest.raises(ValueError, match='model-binding role'):
            views.development_view_v2(record, selection=case.selection, original=case.original, evidence=views.ActualRecordsV2(records.items()))
    elif field == 'target-census':
        with pytest.raises(ValueError, match='complete disjoint targets'):
            replace(case.development, validation_target_ids=('substituted.target',))
    elif field == 'envelope':
        record = replace(case.freeze, envelope=replace(case.freeze.envelope, size_bytes=case.selection.compiler_contract.maximum_envelope_bytes + 1))
        with pytest.raises(ValueError, match='compiler bounds'):
            views.freeze_view_v2(record, selection=case.selection, original=case.original, evidence=case.evidence)
    else:
        with pytest.raises(ValueError, match='original pipeline identity or bytes'):
            views.development_view_v2(case.development, selection=case.selection, original=replace(case.original, config_id='config.substituted'), evidence=case.evidence)


def test_raw_action_encoding_is_the_exact_existing_receipt_digest_preimage():
    from empirical_lawhood.adapters.physical.virtual_cell.prediction import _array_sha256
    values = np.asarray([[-.4, 1.2]])
    payload = encode_raw_prediction_deltas_v2(values=values, target_ids=('target.a',), gene_ids=('gene.a', 'gene.b'))
    assert payload == b'(1, 2)' + values.astype('<f8').tobytes()
    assert sha256(payload).hexdigest() == _array_sha256(values)
    actual = decode_raw_prediction_deltas_v2(payload=payload, target_ids=('target.a',), gene_ids=('gene.a', 'gene.b'),
        expected_sha256=sha256(payload).hexdigest(), maximum_bytes=len(payload))
    np.testing.assert_array_equal(actual, [[-.4, 1.2]])
    assert not actual.flags.writeable
    with pytest.raises(ValueError):
        decode_raw_prediction_deltas_v2(payload=payload+b'x', target_ids=('target.a',), gene_ids=('gene.a', 'gene.b'),
            expected_sha256=sha256(payload).hexdigest(), maximum_bytes=len(payload)+1)


def test_actual_receiver_observation_and_bootstrap_preserve_unequal_score_math():
    from empirical_lawhood.adapters.physical.virtual_cell.evaluation import OfficialEvaluatorRunV2, bootstrap_official_score_standard_error
    case = fixture()
    metrics = next(value for value in case.records.values() if type(value) is OfficialMetricSetV2)
    score = score_corrected_metrics(metrics, metric_contract=case.original.model_selection.validation_metric_contract)
    run = OfficialEvaluatorRunV2(metrics, score, '0.6.6', '0.1.26', 'vcc', 'non-targeting', 'target_gene', True)
    observed = ReceiverObservation.from_v2_run(run)
    assert observed.score is score and observed.metrics_payload == metrics.canonical_bytes()
    assert observed.des == (D('.2'),) and observed.pds == (D('.8'),)
    candidate = CandidateValidationObservationV2('candidate.exposed', observed, D(0))
    assert not hasattr(candidate, 'metrics_arrow') and candidate.metrics_schema == OfficialMetricSetV2.SCHEMA
    runner = object.__new__(runtime.VirtualCellTaskRunner)
    with pytest.raises(ValueError, match='historical candidate'):
        runner._candidate_validation(candidate_id='candidate.exposed', receiver=observed, score_standard_error=D(0))
    kwargs = dict(metric_contract=case.original.model_selection.validation_metric_contract, resamples=7, seed=17)
    assert bootstrap_official_score_standard_error(des=np.asarray(observed.des, dtype=float), pds=np.asarray(observed.pds, dtype=float), mae=np.asarray(observed.mae, dtype=float), **kwargs) == bootstrap_official_score_standard_error(des=np.asarray([.2]), pds=np.asarray([.8]), mae=np.asarray([.01]), **kwargs)
