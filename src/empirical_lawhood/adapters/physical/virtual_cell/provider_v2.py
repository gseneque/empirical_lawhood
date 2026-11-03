# SPDX-License-Identifier: MPL-2.0
"""Explicit corrected receiver provider using existing candidate execution ports."""

from dataclasses import replace

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactProfile
from empirical_lawhood.runtime.providers import CapabilityOutputSemanticContract, ExternalInputPayload

from .config_v2 import VirtualCellPipelineSelectionV2
from .correction_records_v2 import OfficialMetricSetV2
from .custody_transport_v2 import CanonicalEvidenceV2
from .ports_v2 import CAPABILITY_VERSION_V2, ORIGINAL_CONFIG_INPUT_ID_V2, virtual_cell_capability_registry_v2
from .protocol import CONFIG_ARTIFACT_ID
from .provider import VirtualCellCampaignRuntimeProvider, _JSON_TYPES, _PROFILE_BY_SCHEMA
from .records_v2 import ModelDevelopmentRecordV2, ModelSelectionRecordV2, PredictionFreezeRecordV2, OfficialEvaluationRecordV2, RAW_PREDICTION_DELTAS_SCHEMA
from .runtime import canonical_json_record_value_keys
from .task_runner_v2 import VirtualCellTaskRunnerV2


class VirtualCellConfigDecoderV2:
    def __init__(self, manifest, selection):
        if manifest.capability_version != CAPABILITY_VERSION_V2 or manifest.config_schema != selection.SCHEMA:
            raise ValueError("corrected decoder requires its selected v2 declaration")
        self.manifest, self.selection = manifest, selection

    @property
    def provider_key(self):
        return self.manifest.capability_key

    @property
    def provider_version(self):
        return self.manifest.capability_version

    def validate_config(self, payload, *, expected_schema):
        if expected_schema != self.selection.SCHEMA or decode_canonical_bytes(payload,
                VirtualCellPipelineSelectionV2, maximum_bytes=1024**2) != self.selection:
            raise ValueError("corrected config bytes differ from their frozen selection")


class VirtualCellCampaignRuntimeProviderV2(VirtualCellCampaignRuntimeProvider):
    def __init__(self, *, selection, **kwargs):
        super().__init__(**kwargs)
        selection.validate_original(self.config)
        if any(value.capability_version != CAPABILITY_VERSION_V2 or value.config_schema != selection.SCHEMA
                for value in self.registry.capabilities):
            raise ValueError("corrected provider requires its complete v2 registry")
        expected = virtual_cell_capability_registry_v2({value.capability_key: value.implementation_sha256
            for value in self.registry.capabilities})
        if self.registry != expected:
            raise ValueError("corrected registry differs from its code-owned declarations")
        self.selection = selection

    def config_decoders(self):
        return tuple(VirtualCellConfigDecoderV2(value, self.selection) for value in self.registry.capabilities)

    def runners(self, registry, source_records=()):
        self._validate_registry(registry)
        if source_records:
            raise ValueError("corrected provider accepts no unbound issued source records")
        return tuple(VirtualCellTaskRunnerV2(manifest=value, selection=self.selection, config=self.config,
            source_manifest=self.source_manifest, source_port=self.source_port, scratch_port=self.scratch_port)
            for value in registry.capabilities)

    def external_inputs(self, plan, source_records=()):
        if source_records or plan.registry_sha256 != self.registry_sha256:
            raise ValueError("corrected external inputs differ from frozen registry or source scope")
        selected_ids = {CONFIG_ARTIFACT_ID, ORIGINAL_CONFIG_INPUT_ID_V2}
        # Reuse the ordinary source/feature/roster/leaderboard admission owner.
        ordinary_plan = replace(plan, tasks=tuple(replace(task, external_inputs=tuple(
            value for value in task.external_inputs if value.logical_artifact_id not in selected_ids)) for task in plan.tasks))
        values = list(super().external_inputs(ordinary_plan))
        specs = {value.logical_artifact_id: value for task in plan.tasks for value in task.external_inputs
            if value.logical_artifact_id in selected_ids}
        for artifact_id, record, object_id in (
                (CONFIG_ARTIFACT_ID, self.selection, self.selection.selection_id),
                (ORIGINAL_CONFIG_INPUT_ID_V2, self.config, self.config.config_id)):
            if artifact_id not in specs:
                continue
            spec = specs[artifact_id]
            payload = record.canonical_bytes()
            expected = ((spec.expected_payload_schema, record.SCHEMA), (spec.expected_content_sha256, record.fingerprint()),
                (spec.expected_size_bytes, len(payload)), (spec.expected_media_type, "application/json"),
                (spec.expected_outcome_access, OutcomeAccess.OUTCOME_BLIND),
                (spec.expected_visibility_ceiling, VisibilityCeiling.PROSPECTIVE))
            if any(actual not in (None, correct) for actual, correct in expected):
                raise ValueError("corrected external config port changes exact original or selected bytes")
            parent = ArtifactLineageParent(ObjectIdentity.from_record(object_id, record),
                VisibilityCeiling.PROSPECTIVE, OutcomeAccess.OUTCOME_BLIND)
            values.append(ExternalInputPayload.from_bytes(logical_artifact_id=artifact_id, payload_schema=record.SCHEMA,
                profile=ArtifactProfile.CANONICAL_JSON, media_type="application/json", payload=payload,
                visibility_ceiling=VisibilityCeiling.PROSPECTIVE, outcome_access=OutcomeAccess.OUTCOME_BLIND,
                parent_visibility_ceilings=(VisibilityCeiling.PROSPECTIVE,), lineage_parents=(parent,),
                logical_content_sha256=record.fingerprint()))
        return tuple(sorted(values, key=lambda value: value.logical_artifact_id))

    def output_semantic_contracts(self, registry, execution_plan=None):
        self._validate_registry(registry)
        types = {kind.SCHEMA: kind for kind in (*_JSON_TYPES, ModelDevelopmentRecordV2,
            ModelSelectionRecordV2, PredictionFreezeRecordV2, OfficialEvaluationRecordV2,
            OfficialMetricSetV2, CanonicalEvidenceV2)}
        profiles = {**_PROFILE_BY_SCHEMA, RAW_PREDICTION_DELTAS_SCHEMA: ArtifactProfile.RAW_SOURCE_BYTES}
        contracts = []
        for manifest in registry.capabilities:
            for schema in manifest.output_schema_ids:
                if schema in types:
                    contracts.append(CapabilityOutputSemanticContract.from_manifest(manifest, payload_schema=schema,
                        profile=ArtifactProfile.CANONICAL_JSON, top_level_keys=("schema", "value", "version"),
                        value_keys=canonical_json_record_value_keys(types[schema])))
                elif schema in profiles:
                    contracts.append(CapabilityOutputSemanticContract.from_manifest(manifest, payload_schema=schema,
                        profile=profiles[schema]))
                else:
                    raise ValueError("corrected declaration contains an unbound output schema")
        if execution_plan is not None:
            planned = {(task.capability.capability_key, task.capability.capability_version, output.payload_schema, output.profile)
                for task in execution_plan.tasks for output in task.outputs}
            contracts = [value for value in contracts if value.key in planned]
        return tuple(sorted(contracts, key=lambda value: value.key))

    def scientific_adjudication_contract(self, registry, execution_plan=None):
        return replace(super().scientific_adjudication_contract(registry, execution_plan), capability_version=CAPABILITY_VERSION_V2)
