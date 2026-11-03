# SPDX-License-Identifier: MPL-2.0
"""Actual task orchestration over exposed canonical fixtures, without receivers."""

from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from types import SimpleNamespace

import numpy as np

import pytest

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.execution import TaskContext, WorkerInputBinding, WorkerInputKind, WorkerInputPort, WorkerOutputPort, WorkerIsolationProfile

from empirical_lawhood.adapters.physical.virtual_cell import protocol, runtime, task_runner_v2 as tasks
from empirical_lawhood.adapters.physical.virtual_cell.config import SELECTION_CAPABILITY_KEY, EVALUATOR_CAPABILITY_KEY, SOURCE_CAPABILITY_KEY, MODEL_CAPABILITY_KEY
from empirical_lawhood.adapters.physical.virtual_cell.custody_transport_v2 import CanonicalEvidenceEntryV2, CanonicalEvidenceV2
from empirical_lawhood.adapters.physical.virtual_cell.ports_v2 import virtual_cell_capability_registry_v2, virtual_cell_config_ref_v2, project_protocol_v2, project_graph_v2, ORIGINAL_CONFIG_INPUT_ID_V2
from empirical_lawhood.adapters.physical.virtual_cell.receiver_readiness_v2 import ReceiverEnvironmentUnavailable
from empirical_lawhood.adapters.physical.virtual_cell.records import ModelDevelopmentRecord, ModelSelectionRecord
from empirical_lawhood.adapters.physical.virtual_cell.records_v2 import ModelSelectionRecordV2
from empirical_lawhood.adapters.physical.virtual_cell.registry import virtual_cell_capability_registry, virtual_cell_capability_keys
from tests.test_virtual_cell_custody_v2 import fixture


class _Reader:
    def __init__(self, payload):
        self._stream = BytesIO(payload)
        self.bytes_read = 0

    def read(self, size=-1):
        result = self._stream.read(size)
        self.bytes_read += len(result)
        return result


def _input(name, record, access=OutcomeAccess.DEVELOPMENT_VISIBLE):
    payload = record.canonical_bytes()
    binding = WorkerInputBinding(name, "materialization." + name, record.SCHEMA, "application/json", len(payload),
        VisibilityCeiling.DEVELOPMENT_ONLY if access is OutcomeAccess.DEVELOPMENT_VISIBLE else VisibilityCeiling.PROSPECTIVE,
        access, WorkerInputKind.EXTERNAL)
    return WorkerInputPort(binding, _Reader(payload))


def _context(case, manifest, records, outputs=(), *, access=OutcomeAccess.DEVELOPMENT_VISIBLE, permissions=None):
    inputs = [_input("selection.config", case.selection, OutcomeAccess.OUTCOME_BLIND),
        _input("original.config", case.original, OutcomeAccess.OUTCOME_BLIND)]
    inputs.extend(_input(name, record) for name, record in records)
    inputs = tuple(sorted(inputs, key=lambda row: row.artifact_id))
    output_ports = [WorkerOutputPort("custody-evidence", CanonicalEvidenceV2.SCHEMA, ArtifactProfile.CANONICAL_JSON,
        "application/json", "artifact.custody-evidence")]
    output_ports.extend(WorkerOutputPort(name, record.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", "artifact." + name)
        for name, record in outputs)
    return TaskContext("run.exposed", "task.exposed", "attempt.exposed", virtual_cell_config_ref_v2(case.selection),
        tuple(value.binding for value in inputs), inputs, tuple(sorted(output_ports, key=lambda row: row.output_id)),
        manifest.permissions if permissions is None else permissions, access, manifest.resource_ceiling, WorkerIsolationProfile.TRUSTED_LOCAL)


class _NoContact:
    def __getattr__(self, name):
        raise AssertionError("source/scratch contacted: " + name)


def _registry():
    digests = {key: "1" * 64 for key in virtual_cell_capability_keys()}
    return virtual_cell_capability_registry(digests), virtual_cell_capability_registry_v2(digests)


def _runner(case, key):
    registry = _registry()[1]
    manifest = registry.resolve(key, tasks.CAPABILITY_VERSION_V2)
    source_manifest = next(value for value in case.records.values() if type(value) is runtime.VirtualCellSourceManifest)
    return tasks.VirtualCellTaskRunnerV2(manifest=manifest, selection=case.selection, config=case.original,
        source_manifest=source_manifest, source_port=_NoContact(), scratch_port=_NoContact()), manifest


def test_custody_transport_exact_roundtrip_and_unknown_type_refusal():
    case = fixture()
    payload = CanonicalEvidenceV2.from_records(case.records.items())
    decoded = decode_canonical_bytes(payload.canonical_bytes(), CanonicalEvidenceV2, maximum_bytes=16 * 1024**2)
    assert dict(decoded.actual_records()) == case.records
    with pytest.raises(ValueError, match="actual canonical bytes"):
        replace(payload.entries[0], canonical_utf8=payload.entries[0].canonical_utf8 + " ")
    entry = payload.entries[0]
    unknown = replace(entry.identity, object_schema="empirical-lawhood/exposed/unregistered")
    with pytest.raises(ValueError, match="unregistered domain"):
        CanonicalEvidenceV2((CanonicalEvidenceEntryV2(unknown, entry.canonical_utf8),)).actual_records()


def test_custody_transport_bounds_its_serialized_outer_json_including_escaping(monkeypatch):
    from empirical_lawhood.adapters.physical.virtual_cell import custody_transport_v2 as transport

    identity, record = next(iter(fixture().records.items()))
    inner_size = len(record.canonical_bytes())
    monkeypatch.setattr(transport, "MAXIMUM_CUSTODY_BYTES_V2", inner_size + 1)
    with pytest.raises(ValueError, match="serialized byte bound"):
        transport.CanonicalEvidenceV2.from_records(((identity, record),))


def test_registry_protocol_and_graph_ports_derive_exact_original_stages_and_authority():
    case = fixture()
    old_registry, registry = _registry()
    old_protocol = protocol.virtual_cell_protocol(registry=old_registry, config=case.original)
    selected = project_protocol_v2(old_protocol, selection=case.selection)
    assert len(selected.steps) == 9
    for old, new in zip(old_protocol.steps, selected.steps, strict=True):
        assert (old.stage, old.required_permissions, old.requested_outcome_access, old.barrier, old.resource_budget, old.obligation_ids) == (
            new.stage, new.required_permissions, new.requested_outcome_access, new.barrier, new.resource_budget, new.obligation_ids)
        assert new.config.content_sha256 == case.selection.fingerprint()
        manifest = registry.resolve(new.capability_key, new.capability_version)
        assert set(value.payload_schema for value in new.outputs) <= set(manifest.output_schema_ids)
        assert CanonicalEvidenceV2.SCHEMA in manifest.output_schema_ids
    manifest = next(value for value in case.records.values() if type(value) is runtime.VirtualCellSourceManifest)
    source = next(value for value in manifest.objects if value.sealed)
    original_graph = protocol.virtual_cell_graph(protocol=old_protocol, registry=old_registry, source_manifest=manifest,
        test_source=source, target_feature_sha256="1" * 64, target_feature_size_bytes=1, test_roster_sha256="2" * 64,
        test_roster_size_bytes=1, leaderboard_snapshot_sha256="3" * 64, leaderboard_snapshot_size_bytes=1)
    graph = project_graph_v2(original_graph, protocol=selected, registry=registry, original_config=case.original, selection=case.selection)
    assert len(graph.nodes) == 9
    assert len([edge for edge in graph.edges if edge.external_input_id == ORIGINAL_CONFIG_INPUT_ID_V2]) == 9
    assert not any(edge.payload_schema in (ModelDevelopmentRecord.SCHEMA, ModelSelectionRecord.SCHEMA) for edge in graph.edges)
    for edge in graph.edges:
        if edge.payload_schema == CanonicalEvidenceV2.SCHEMA:
            assert edge.producer_output_id == "custody-evidence"
            assert edge.outcome_access == next(step.requested_outcome_access for step in selected.steps if step.step_id == edge.producer_node_id)


@pytest.mark.parametrize("key", [SOURCE_CAPABILITY_KEY, SELECTION_CAPABILITY_KEY, EVALUATOR_CAPABILITY_KEY])
def test_actual_execute_missing_receiver_refuses_before_any_source_or_scratch(key):
    case = fixture()
    runner, manifest = _runner(case, key)
    context = _context(case, manifest, ())
    with pytest.raises(ReceiverEnvironmentUnavailable, match="ENVIRONMENT:.*receiver unavailable"):
        runner.execute(context)


def test_inherited_selection_stage_consumes_actual_v2_custody_and_emits_only_new_records(monkeypatch):
    case = fixture()
    runner, manifest = _runner(case, SELECTION_CAPABILITY_KEY)
    panel = next(value for value in case.records.values() if type(value) is runtime.FalsifierPanel)
    custody = CanonicalEvidenceV2.from_records((key, value) for key, value in case.records.items()
        if type(value) not in (ModelSelectionRecordV2,))
    context = _context(case, manifest, (("development", case.development), ("panel", panel), ("prior.custody", custody)),
        (("model-selection", ModelSelectionRecordV2),))
    # Exposed software control: only optional software availability is doubled.
    # The actual inherited execute/select bodies, input ports and record joins run.
    monkeypatch.setattr(tasks, "require_receiver_ready_v2", lambda **kwargs: None)
    result = runner.execute(context)
    selection_payload = next(value.payload for value in result.outputs if value.output_id == "model-selection")
    selected = decode_canonical_bytes(selection_payload, ModelSelectionRecordV2, maximum_bytes=65536)
    assert selected.selected_model == case.model_selection.selected_model
    assert selected.development == ObjectIdentity.from_record(case.development.record_id, case.development)
    assert tasks.VirtualCellTaskRunnerV2._select is runtime.VirtualCellTaskRunner._select
    assert tasks.VirtualCellTaskRunnerV2._develop is runtime.VirtualCellTaskRunner._develop
    assert tasks.VirtualCellTaskRunnerV2._falsify is runtime.VirtualCellTaskRunner._falsify
    assert tasks.VirtualCellTaskRunnerV2._evaluate is runtime.VirtualCellTaskRunner._evaluate
    emitted = decode_canonical_bytes(next(value.payload for value in result.outputs if value.output_id == "custody-evidence"),
        CanonicalEvidenceV2, maximum_bytes=65536).actual_records()
    assert emitted == ((ObjectIdentity.from_record(selected.record_id, selected), selected),)
    assert sha256(selection_payload).hexdigest() == selected.fingerprint()


def test_actual_evaluator_stage_keeps_original_reveal_gate_after_software_admission(monkeypatch):
    case = fixture()
    runner, manifest = _runner(case, EVALUATOR_CAPABILITY_KEY)
    context = _context(case, manifest, (), permissions=(), access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    monkeypatch.setattr(tasks, "require_receiver_ready_v2", lambda **kwargs: None)
    with pytest.raises(PermissionError, match="exact reveal authority"):
        runner.execute(context)


def test_development_factory_binds_actual_model_and_metric_payloads_with_complete_census():
    """Saved exposed models exercise the new factory, independently of H5AD I/O."""
    from decimal import Decimal
    from empirical_lawhood.adapters.physical.virtual_cell.analysis import LinearResponseModel
    from empirical_lawhood.adapters.physical.virtual_cell.codecs import encode_linear_model
    from empirical_lawhood.adapters.physical.virtual_cell.contracts import MetricContract
    from empirical_lawhood.adapters.physical.virtual_cell.correction_records_v2 import OfficialMetricSetV2, SharedTemplateShiftV2BuildReceipt
    from empirical_lawhood.adapters.physical.virtual_cell.custody_views_v2 import development_view_v2
    from empirical_lawhood.adapters.physical.virtual_cell.receiver_observation_v2 import CandidateValidationObservationV2, ReceiverObservation
    from empirical_lawhood.adapters.physical.virtual_cell.records import ModelArtifactBinding, ResponseSummaryRecord
    from empirical_lawhood.adapters.physical.virtual_cell.records_v2 import ModelDevelopmentRecordV2

    case = fixture()
    runner, manifest = _runner(case, MODEL_CAPABILITY_KEY)
    source_manifest = runner.source_manifest
    stage = tasks._StageEvidence(None)
    for reference, value in case.records.items():
        if type(value) in (MetricContract, ResponseSummaryRecord, runtime.VirtualCellSourceManifest):
            stage.retain(reference.object_id, value, created=False)
    bindings = {value.model_id: value for value in case.records.values() if type(value) is ModelArtifactBinding}
    models = {name: LinearResponseModel(name, value.fit.family, (), ("gene.a", "gene.b"), None,
        np.empty((0, 2)), np.zeros(2), None, False, 0, None, np.ones(2)) for name, value in bindings.items()}
    candidates = tuple(SimpleNamespace(candidate_id=name, fit=bindings[name].fit) for name in case.original.model_selection.candidate_ids)
    refits = tuple(SimpleNamespace(model=models[name + "-development-refit"], fit=bindings[name + "-development-refit"].fit)
        for name in case.original.model_selection.candidate_ids)
    tournament = case.records[case.development.tournament]
    metrics = next(value for value in case.records.values() if type(value) is OfficialMetricSetV2 and value.target_ids == case.development.validation_target_ids)
    score = next(value for key, value in case.records.items() if key.object_id.startswith("score.validation."))
    receiver = ReceiverObservation(metrics.target_ids, metrics.des, metrics.pds, metrics.mae, score, metrics.canonical_bytes(),
        metrics.SCHEMA, "0.6.6", "0.1.26", True)
    build = next(value for value in case.records.values() if type(value) is SharedTemplateShiftV2BuildReceipt)
    validations = tuple(CandidateValidationObservationV2(name, receiver, Decimal(0)) for name in case.original.model_selection.candidate_ids)
    stage.validations = {name: (build, receiver) for name in case.original.model_selection.candidate_ids}
    development = SimpleNamespace(candidates=candidates, development_refits=refits, official_validations=validations,
        tournament=tournament, train_target_ids=case.development.training_target_ids, validation_target_ids=case.development.validation_target_ids)
    model_payloads = {runner._model_output_name(name): encode_linear_model(models[name]) for name in case.original.model_selection.candidate_ids}
    model_payloads.update({runner._model_refit_output_name(name): encode_linear_model(models[name + "-development-refit"])
        for name in case.original.model_selection.candidate_ids})
    metric_payloads = {runner._validation_metrics_output_name(name): metrics.canonical_bytes() for name in case.original.model_selection.candidate_ids}
    context = _context(case, manifest, ())
    context = replace(context, output_ports=tuple(sorted((*context.output_ports,
        *(WorkerOutputPort(name, runtime.MODEL_SAFETENSORS_SCHEMA, ArtifactProfile.SAFETENSORS, "application/x-safetensors", "artifact." + name) for name in model_payloads),
        *(WorkerOutputPort(name, metrics.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", "artifact." + name) for name in metric_payloads)), key=lambda row: row.output_id)))
    stage.context = context
    summaries = [value for value in stage.records.values() if type(value) is ResponseSummaryRecord]
    token = tasks._STAGE.set(stage)
    try:
        record = runner._development_record(context, development, training_summary_sha256=summaries[0].table_sha256,
            validation_summary_sha256=summaries[1].table_sha256, feature_provenance_sha256=case.original.target_feature_provenance_sha256,
            model_payloads=model_payloads, validation_metric_payloads=metric_payloads)
    finally:
        tasks._STAGE.reset(token)
    assert type(record) is ModelDevelopmentRecordV2
    view = development_view_v2(record, selection=case.selection, original=case.original, evidence=stage.evidence())
    assert len(view.models) == 10 and len(record.validations) == 5
    assert record.source_manifest == ObjectIdentity.from_record(source_manifest.manifest_id, source_manifest)
    for binding in view.models:
        output_id = (runner._model_refit_output_name(binding.model_id.removesuffix("-development-refit"))
            if binding.model_id.endswith("-development-refit") else runner._model_output_name(binding.model_id))
        assert binding.artifact_sha256 == sha256(model_payloads[output_id]).hexdigest()
    for validation in record.validations:
        assert validation.metrics_artifact.sha256 == metrics.fingerprint()
        assert validation.metrics_artifact.payload_schema == metrics.SCHEMA


def test_actual_five_family_fit_tournament_and_refit_math_preserve_observation_parity():
    """Changed payload semantics leave the existing numerical finalizer intact."""
    from decimal import Decimal as D
    from empirical_lawhood.adapters.physical.virtual_cell.analysis import TargetFeatureMatrix, TargetResponseMatrix
    from empirical_lawhood.adapters.physical.virtual_cell.codecs import encode_official_metrics
    from empirical_lawhood.adapters.physical.virtual_cell.correction_records_v2 import OfficialMetricGaugeV2, OfficialMetricSetV2, MetricSourceSemantics
    from empirical_lawhood.adapters.physical.virtual_cell.development import fit_tier_l0_candidates, finalize_tier_l0_development, CandidateOfficialValidation
    from empirical_lawhood.adapters.physical.virtual_cell.metric_correction_v2 import score_corrected_metrics
    from empirical_lawhood.adapters.physical.virtual_cell.receiver_observation_v2 import ReceiverObservation, CandidateValidationObservationV2
    from tests.test_virtual_cell_runtime_v2 import _original_config

    selected = _original_config()
    contract = replace(selected.model_selection, ridge_alphas=(D(1),), reduced_ranks=(1,), outer_target_folds=2, repeat_seeds=(7,))
    genes = tuple("gene." + str(index) for index in range(8))
    rng = np.random.default_rng(17)
    values = rng.normal(size=(8, 8))
    values[np.arange(8), np.arange(8)] = -1
    train = TargetResponseMatrix(genes[:6], genes, values[:6], np.ones(6))
    validation = TargetResponseMatrix(genes[6:], genes, values[6:], np.ones(2))
    features = TargetFeatureMatrix(genes, ("feature.a", "feature.b", "feature.c"), rng.normal(size=(8, 3)), "1" * 64)
    kwargs = dict(train=train, validation=validation, features=features, contract=contract,
        realized_admission_repression_scale=float(contract.realized_admission_repression_scale))
    candidates = fit_tier_l0_candidates(**kwargs)
    historical, corrected = [], []
    for index, candidate in enumerate(candidates):
        metrics = OfficialMetricSetV2(OfficialMetricGaugeV2(), MetricSourceSemantics.OFFICIAL_SOURCE_COLUMNS, None,
            validation.target_ids, (D('.2') + D(index) / 50, D('.3')), (D('.8'), D('.7')), (D('.01'), D('.02')))
        score = score_corrected_metrics(metrics, metric_contract=contract.validation_metric_contract)
        historical.append(CandidateOfficialValidation(candidate.candidate_id, metrics.target_ids, score, D('.01'),
            encode_official_metrics(target_ids=metrics.target_ids, des=np.asarray(metrics.des, dtype=float),
                pds=np.asarray(metrics.pds, dtype=float), mae=np.asarray(metrics.mae, dtype=float)), "0.6.6", "0.1.26", True))
        receiver = ReceiverObservation(metrics.target_ids, metrics.des, metrics.pds, metrics.mae, score,
            metrics.canonical_bytes(), metrics.SCHEMA, "0.6.6", "0.1.26", True)
        corrected.append(CandidateValidationObservationV2(candidate.candidate_id, receiver, D('.01')))
    old = finalize_tier_l0_development(**kwargs, candidates=candidates, official_validations=tuple(historical))
    new = finalize_tier_l0_development(**kwargs, candidates=candidates, official_validations=tuple(corrected))
    assert old.tournament.canonical_bytes() == new.tournament.canonical_bytes()
    assert old.development_target_ids == new.development_target_ids == genes
    for before, after in zip(old.development_refits, new.development_refits, strict=True):
        assert before.fit.canonical_bytes() == after.fit.canonical_bytes()
        for name in ("coefficients", "intercept", "residual_scale", "response_basis"):
            np.testing.assert_array_equal(getattr(before.model, name), getattr(after.model, name))
