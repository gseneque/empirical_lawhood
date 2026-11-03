# SPDX-License-Identifier: MPL-2.0
"""Corrected receiver/compiler composition through the original nine stages.

All fitting, tournament, refit, falsifier and adjudication bodies belong to the
original runner. This subclass owns only explicit selection, actual successor
record construction, canonical dependency transport and corrected receiver I/O.
It grants no issue, execution, source access or evaluator reveal authority.
"""

from contextvars import ContextVar
from dataclasses import dataclass, field, replace
from hashlib import sha256

import numpy as np

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity

from . import runtime as original
from .config_v2 import VirtualCellPipelineSelectionV2
from .correction_records_v2 import OfficialMetricSetV2
from .custody_transport_v2 import CanonicalEvidenceV2, MAXIMUM_CUSTODY_BYTES_V2
from .custody_views_v2 import ActualRecordsV2, development_view_v2, selection_view_v2, freeze_view_v2, evaluation_view_v2
from .prediction_payload_v2 import encode_raw_prediction_deltas_v2
from .ports_v2 import CAPABILITY_VERSION_V2, virtual_cell_config_ref_v2, virtual_cell_capability_registry_v2
from .receiver_observation_v2 import CandidateValidationObservationV2, ReceiverObservation
from .receiver_readiness_v2 import require_receiver_ready_v2
from .records_v2 import CandidateValidationRecordV2, ModelDevelopmentRecordV2, ModelSelectionRecordV2, PredictionFreezeRecordV2, OfficialEvaluationRecordV2, RAW_PREDICTION_DELTAS_SCHEMA

@dataclass(slots=True)
class _StageEvidence:
    context: object
    records: dict = field(default_factory=dict)
    created: dict = field(default_factory=dict)
    inputs: dict = field(default_factory=dict)
    validations: dict = field(default_factory=dict)
    build: object = None
    roster: object = None
    gene_ids: tuple = ()
    raw_payload: bytes = b""
    selected_payload: bytes = b""
    receiver: object = None
    envelope_size: int = 0

    def retain(self, object_id, record, *, created=True):
        record.__post_init__()
        identity = ObjectIdentity.from_record(object_id, record)
        for previous in self.records:
            if (previous.object_schema, previous.object_id) == (identity.object_schema, identity.object_id) and previous != identity:
                raise ValueError("corrected task substitutes a canonical record role")
        self.records[identity] = record
        if created:
            self.created[identity] = record
        return identity

    def evidence(self):
        return ActualRecordsV2(self.records.items())


_STAGE = ContextVar("virtual_cell_v2_stage")


def _artifact(artifact_id, schema, media_type, digest, size):
    if artifact_id is None:
        raise ValueError("corrected task output lacks its logical artifact identity")
    return ArtifactIdentity(artifact_id, "virtual-cell-evidence", schema, digest, media_type, size)


class VirtualCellTaskRunnerV2(original.VirtualCellTaskRunner):
    """An explicit v2 task runner using the original stage orchestration."""

    def __init__(self, *, selection, **kwargs):
        super().__init__(**kwargs)
        if type(selection) is not VirtualCellPipelineSelectionV2:
            raise TypeError("corrected task requires its actual frozen selection")
        selection.validate_original(self.config)
        from .registry import virtual_cell_capability_keys

        expected = virtual_cell_capability_registry_v2({key: self.manifest.implementation_sha256
            for key in virtual_cell_capability_keys()}).resolve(self.manifest.capability_key, CAPABILITY_VERSION_V2)
        if self.manifest != expected:
            raise ValueError("corrected task manifest differs from its code-owned declaration")
        if self.source_manifest.fingerprint() != self.config.source_manifest_sha256:
            raise ValueError("corrected task source differs from its original configuration")
        self.selection = selection

    def execute(self, context):
        stage = _StageEvidence(context)
        token = _STAGE.set(stage)
        try:
            result = super().execute(context)
            # Each task emits only records created here. The graph binds earlier
            # sidecars by reference, rather than copying their complete closure.
            custody = CanonicalEvidenceV2.from_records(stage.created.items())
            output = original._json_output(context, "custody-evidence", custody)
            return replace(result, outputs=tuple(sorted((*result.outputs, output), key=lambda row: row.output_id)))
        finally:
            _STAGE.reset(token)

    def _validate_context(self, context):
        if self.manifest.capability_version != CAPABILITY_VERSION_V2:
            raise ValueError("corrected task requires its explicit v2 capability revision")
        selection = original._canonical_input(context, VirtualCellPipelineSelectionV2)
        config = original._canonical_input(context, original.ProvenanceBoundVirtualCellPipelineConfig)
        if selection != self.selection or config != self.config or context.config != virtual_cell_config_ref_v2(selection):
            raise ValueError("corrected task config differs from its frozen selection and original bytes")
        stage = _STAGE.get()
        stage.retain(selection.selection_id, selection, created=False)
        stage.retain(config.config_id, config, created=False)
        stage.retain(self.source_manifest.manifest_id, self.source_manifest, created=False)
        for contract in (self.config.metric_contract, self.config.model_selection.validation_metric_contract):
            stage.retain(contract.contract_id, contract, created=False)

    def _before_stage(self, context):
        # Software admission always precedes held source, H5AD and scratch.
        require_receiver_ready_v2(selection=self.selection, original_config=self.config)
        stage = _STAGE.get()
        for port in context.input_ports:
            if port.payload_schema == CanonicalEvidenceV2.SCHEMA:
                bundle = decode_canonical_bytes(port.read(), CanonicalEvidenceV2, maximum_bytes=MAXIMUM_CUSTODY_BYTES_V2)
                for identity, value in bundle.actual_records():
                    stage.retain(identity.object_id, value, created=False)

    def _input_record(self, context, record_type):
        stage = _STAGE.get()
        if record_type in stage.inputs:
            return stage.inputs[record_type]
        successors = {
            original.ModelDevelopmentRecord: (ModelDevelopmentRecordV2, development_view_v2),
            original.ModelSelectionRecord: (ModelSelectionRecordV2, selection_view_v2),
            original.PredictionFreezeRecord: (PredictionFreezeRecordV2, freeze_view_v2),
            original.OfficialEvaluationRecord: (OfficialEvaluationRecordV2, evaluation_view_v2),
        }
        if record_type in successors:
            kind, view = successors[record_type]
            record = original._canonical_input(context, kind)
            object_id = record.evaluation_id if kind is OfficialEvaluationRecordV2 else record.record_id
            stage.retain(object_id, record, created=False)
            value = view(record, selection=self.selection, original=self.config, evidence=stage.evidence())
        else:
            value = super()._input_record(context, record_type)
            object_id = next((getattr(value, name) for name in ("record_id", "panel_id", "object_id") if hasattr(value, name)), None)
            if object_id is not None:
                stage.retain(object_id, value, created=False)
        stage.inputs[record_type] = value
        return value

    def _record_output(self, context, output_id, record):
        stage = _STAGE.get()
        object_id = next((getattr(record, name) for name in ("record_id", "panel_id", "evaluation_id") if hasattr(record, name)), None)
        if object_id is not None:
            stage.retain(object_id, record)
        return original._json_output(context, output_id, record)

    def _compiler_contract(self):
        return self.selection.compiler_contract

    def _configuration_fingerprint(self):
        return self.selection.fingerprint()

    def _prediction_output_id(self):
        return "predicted-deltas"

    def _prediction_payload_schema(self):
        return RAW_PREDICTION_DELTAS_SCHEMA

    def _metrics_payload_schema(self):
        return OfficialMetricSetV2.SCHEMA

    def _prediction_envelope_identity(self, *, size_bytes, sha256):
        _STAGE.get().envelope_size = size_bytes

    def _response_inputs(self, context, *, split_name):
        result = super()._response_inputs(context, split_name=split_name)
        _STAGE.get().retain(result[0].record_id, result[0], created=False)
        return result

    def _compile_prediction_action(self, *, target_ids, predicted_deltas, control_reservoir):
        # Raw signed deltas are the v2 donor's declared action. No old absolute
        # mean projection or clipping is admitted at this seam.
        values = np.asarray(predicted_deltas, dtype=np.float64).copy()
        encode_raw_prediction_deltas_v2(values=values, target_ids=target_ids, gene_ids=control_reservoir.gene_ids)
        values.setflags(write=False)
        return values

    def _encode_prediction_action(self, *, target_ids, prediction_action, uncertainty):
        stage = _STAGE.get()
        stage.raw_payload = encode_raw_prediction_deltas_v2(values=prediction_action, target_ids=target_ids, gene_ids=stage.gene_ids)
        return stage.raw_payload

    def _control_reservoir(self, context, *, gene_ids):
        result = super()._control_reservoir(context, gene_ids=gene_ids)
        _STAGE.get().gene_ids = gene_ids
        return result

    def _selected_model(self, context, selection):
        result = super()._selected_model(context, selection)
        _STAGE.get().selected_payload = result[1]
        return result

    def _write_prediction_file(self, *, path, roster, gene_ids, prediction_action, control_reservoir, control_reservoir_sha256):
        from .prediction_v2 import write_shared_template_shift_v2_prediction_h5ad

        receipt = write_shared_template_shift_v2_prediction_h5ad(path=path, roster=roster, gene_ids=gene_ids,
            predicted_deltas=prediction_action, control_reservoir=control_reservoir,
            control_reservoir_sha256=control_reservoir_sha256, seed=self._compiler_contract().compiler_seed,
            selection=self.selection.compiler)
        stage = _STAGE.get()
        stage.build, stage.roster, stage.gene_ids = receipt, roster, gene_ids
        return receipt

    def _evaluate_arrays(self, *, predicted, real, scratch_directory, num_threads, validation):
        from .evaluation import evaluate_official_2025_v2

        run = evaluate_official_2025_v2(predicted=predicted, real=real,
            metric_contract=(self.config.model_selection.validation_metric_contract if validation else self.config.metric_contract),
            metric_gauge=self.selection.metric_gauge, scratch_directory=scratch_directory, num_threads=num_threads,
            control_label=self.config.response_summary.comparator_label, perturbation_column=self.config.response_summary.target_field)
        observed = ReceiverObservation.from_v2_run(run)
        _STAGE.get().receiver = observed
        return observed

    def _candidate_validation(self, *, candidate_id, receiver, score_standard_error):
        result = CandidateValidationObservationV2(candidate_id, receiver, score_standard_error)
        _STAGE.get().validations[candidate_id] = (_STAGE.get().build, receiver)
        return result

    def _development_record(self, context, development, *, training_summary_sha256, validation_summary_sha256,
            feature_provenance_sha256, model_payloads, validation_metric_payloads):
        from .codecs import decode_linear_model
        from .records import ModelArtifactBinding, MODEL_SAFETENSORS_SCHEMA, ResponseSummaryRecord

        stage = _STAGE.get()
        fits = {value.candidate_id: value.fit for value in development.candidates}
        fits.update({value.model.model_id: value.fit for value in development.development_refits})
        bindings = []
        for output_id, payload in model_payloads.items():
            model = decode_linear_model(payload)
            port = original._output_port(context, output_id)
            if port.payload_schema != MODEL_SAFETENSORS_SCHEMA or port.logical_artifact_id is None:
                raise ValueError("corrected development model output changes its frozen port")
            binding = ModelArtifactBinding(model.model_id, port.logical_artifact_id, sha256(payload).hexdigest(), fits[model.model_id])
            stage.retain(binding.fit.fit_id, binding.fit)
            bindings.append(stage.retain("model-binding." + model.model_id, binding))
        contract = self.config.model_selection.validation_metric_contract
        validations = []
        for value in development.official_validations:
            build, receiver = stage.validations[value.candidate_id]
            metrics = decode_canonical_bytes(receiver.metrics_payload, OfficialMetricSetV2, maximum_bytes=MAXIMUM_CUSTODY_BYTES_V2)
            output_id = self._validation_metrics_output_name(value.candidate_id)
            payload = validation_metric_payloads[output_id]
            if payload != metrics.canonical_bytes():
                raise ValueError("corrected development changes actual receiver bytes")
            port = original._output_port(context, output_id)
            validations.append(CandidateValidationRecordV2(value.candidate_id, self.selection.identity,
                ObjectIdentity.from_record(fits[value.candidate_id].fit_id, fits[value.candidate_id]),
                stage.retain("prediction-build.validation." + value.candidate_id, build),
                stage.retain("metrics.validation." + value.candidate_id, metrics),
                stage.retain("score.validation." + value.candidate_id, value.score),
                _artifact(port.logical_artifact_id, OfficialMetricSetV2.SCHEMA, "application/json", sha256(payload).hexdigest(), len(payload)),
                value.target_ids, ObjectIdentity.from_record(contract.contract_id, contract), value.score_standard_error,
                OutcomeAccess.DEVELOPMENT_VISIBLE))
        summaries = {value.split: (reference, value) for reference, value in stage.records.items() if type(value) is ResponseSummaryRecord}
        train_ref, train = summaries[original.VirtualCellSplit.TRAIN]
        validation_ref, validation = summaries[original.VirtualCellSplit.VALIDATION]
        if (train.table_sha256, validation.table_sha256) != (training_summary_sha256, validation_summary_sha256):
            raise ValueError("corrected development changes actual summary bytes")
        record = ModelDevelopmentRecordV2("development.virtual-cell-2025-tier-l0-v2", self.selection.identity,
            ObjectIdentity.from_record(self.source_manifest.manifest_id, self.source_manifest), train_ref, validation_ref,
            feature_provenance_sha256, tuple(sorted(bindings, key=lambda row: row.object_id)), tuple(validations),
            stage.retain(development.tournament.tournament_id, development.tournament), development.train_target_ids,
            development.validation_target_ids, (), ())
        development_view_v2(record, selection=self.selection, original=self.config, evidence=stage.evidence())
        return record

    def _create_record(self, record_type, **values):
        stage = _STAGE.get()
        context = stage.context
        if record_type is original.ModelSelectionRecord:
            development = self._input_record(context, original.ModelDevelopmentRecord)
            panel = self._input_record(context, original.FalsifierPanel)
            selected = next(value for value in development.models if value.artifact_id == values["selected_model_artifact_id"])
            record = ModelSelectionRecordV2(values["record_id"] + "-v2", self.selection.identity,
                ObjectIdentity.from_record(development.record.record_id, development.record), development.record.tournament,
                ObjectIdentity.from_record(panel.panel_id, panel), ObjectIdentity.from_record("model-binding." + selected.model_id, selected))
            selection_view_v2(record, selection=self.selection, original=self.config, evidence=stage.evidence())
            return record
        if record_type is original.PredictionFreezeRecord:
            selected = self._input_record(context, original.ModelSelectionRecord)
            roster_port = original._one_input(context, payload_schema=original.TEST_ROSTER_TEXT_SCHEMA)
            delta_port = original._output_port(context, self._prediction_output_id())
            envelope_port = original._output_port(context, "prediction-envelope")
            roster = stage.roster
            record = PredictionFreezeRecordV2(values["record_id"] + "-v2", self.selection.identity,
                ObjectIdentity.from_record(selected.record.record_id, selected.record),
                ObjectIdentity.from_record(self.source_manifest.manifest_id, self.source_manifest),
                ObjectIdentity.from_record(self.config.metric_contract.contract_id, self.config.metric_contract),
                stage.retain(selected.model.fit.fit_id, selected.model.fit), selected.model.model_id,
                _artifact(selected.model.artifact_id, original.MODEL_SAFETENSORS_SCHEMA, "application/x-safetensors", selected.model.artifact_sha256, len(stage.selected_payload)),
                values["commitment"], stage.build, tuple(value.target_id for value in roster.targets), stage.gene_ids,
                stage.retain(roster.roster_id, roster),
                _artifact(roster_port.artifact_id, original.TEST_ROSTER_TEXT_SCHEMA, "text/csv", values["commitment"].target_roster_sha256, roster_port.size_bytes),
                _artifact(delta_port.logical_artifact_id, RAW_PREDICTION_DELTAS_SCHEMA, "application/octet-stream", sha256(stage.raw_payload).hexdigest(), len(stage.raw_payload)),
                _artifact(envelope_port.logical_artifact_id, original.PREDICTION_H5AD_ENVELOPE_SCHEMA, "application/x-hdf5", values["h5ad_envelope_sha256"], stage.envelope_size))
            freeze_view_v2(record, selection=self.selection, original=self.config, evidence=stage.evidence())
            return record
        if record_type is original.OfficialEvaluationRecord:
            freeze = self._input_record(context, original.PredictionFreezeRecord)
            source = self._input_record(context, original.VirtualCellSourceObject)
            receiver = stage.receiver
            metrics = decode_canonical_bytes(receiver.metrics_payload, OfficialMetricSetV2, maximum_bytes=MAXIMUM_CUSTODY_BYTES_V2)
            port = original._output_port(context, "official-metrics")
            evaluation_id = values["evaluation_id"] + "-v2"
            record = OfficialEvaluationRecordV2(evaluation_id, self.selection.identity,
                ObjectIdentity.from_record(freeze.record.record_id, freeze.record), values["prediction_commitment_sha256"],
                ObjectIdentity.from_record(source.object_id, source),
                ObjectIdentity.from_record(self.config.metric_contract.contract_id, self.config.metric_contract),
                stage.retain("metrics.final." + evaluation_id, metrics),
                _artifact(port.logical_artifact_id, OfficialMetricSetV2.SCHEMA, "application/json", sha256(receiver.metrics_payload).hexdigest(), len(receiver.metrics_payload)),
                stage.retain("score.final." + evaluation_id, receiver.score), receiver.target_ids, receiver.cell_eval_version,
                receiver.pdex_version, OutcomeAccess.EVALUATOR_REVEAL)
            evaluation_view_v2(record, selection=self.selection, original=self.config, evidence=stage.evidence())
            return record
        return super()._create_record(record_type, **values)
