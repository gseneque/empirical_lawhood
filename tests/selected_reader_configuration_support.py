# SPDX-License-Identifier: MPL-2.0
"""Actual frozen task/config metadata for disclosed reducer-only reader controls.

The surrounding literal receipts are software premises, not acquisition or
qualification. No TaskContext, prepared invocation or permission is fabricated.
"""
from hashlib import sha256

from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
from empirical_lawhood.runtime.plans import (
    ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec,
    ScientificInputRole, ScientificInputSpec,
)
from tests.worker_configuration_support import freeze_worker_configuration


def freeze_reader_terminal(*, plane, task, config, declaration, receipts, resources=None):
    """Retain every existing science port and add the actual canonical CONFIG."""
    manifest = declaration.manifest()
    assert type(config) is declaration.config_record_type
    raw = config.canonical_bytes()
    publication = plane.write(ArtifactWriteRequest(config.config_id,
        'reader-configuration/' + sha256(task.task_id.encode()).hexdigest() + '.json',
        config.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json',
        'publication.' + config.config_id, 'reader-configuration', raw,
        declaration.visibility_ceiling, (), declaration.outcome_access))
    reference = CapabilityConfigRef(config.config_id, config.SCHEMA,
        manifest.config_schema_sha256, config.fingerprint(), config.config_id)
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version,
        manifest.kind, reference, manifest.input_schema_ids, manifest.output_schema_ids,
        manifest.permissions, declaration.evidence_ceiling, declaration.outcome_access,
        declaration.resources if resources is None else resources)
    edges = []
    for edge in task.scientific_inputs:
        receipt = receipts[edge.producer_task_id]
        logical, = (row for row in receipt.output_logical_artifacts
            if row.logical_artifact_id == edge.operational_logical_artifact_id)
        material, = (row for row in receipt.output_materializations
            if row.logical_artifact_id == logical.logical_artifact_id)
        edges.append(ScientificInputSpec('edge.' + task.task_id + '.' + edge.consumer_input_id,
            edge.consumer_input_id, ScientificInputRole.HISTORY, edge.producer_task_id,
            edge.producer_output_id, None, logical.logical_artifact_id,
            logical.logical_artifact_id, logical.payload_schema, logical.media_type,
            material.size_bytes, logical.outcome_access, logical.visibility_ceiling,
            BarrierKind.NONE))
    receipt = receipts[task.task_id]
    outputs = []
    for spec in task.outputs:
        logical, = (row for row in receipt.output_logical_artifacts
            if row.logical_artifact_id == spec.logical_artifact_id)
        material, = (row for row in receipt.output_materializations
            if row.logical_artifact_id == logical.logical_artifact_id)
        outputs.append(ArtifactOutputSpec(spec.output_id, spec.logical_artifact_id,
            material.relative_path, logical.payload_schema, logical.profile, logical.media_type,
            logical.visibility_ceiling, (), logical.outcome_access))
    config_input = ExternalInputSpec('config', config.config_id, config.fingerprint(),
        config.SCHEMA, 'application/json', len(raw), publication.logical.visibility_ceiling,
        publication.logical.outcome_access, None)
    typed = ExecutionTask(task.task_id, declaration.stage, requirement,
        manifest.implementation_sha256,
        tuple(sorted({edge.producer_task_id for edge in edges})), (config_input,),
        tuple(sorted(outputs, key=lambda row: row.output_id)), (), BarrierKind.NONE,
        1, ('obligation.disclosed.reader',),
        scientific_inputs=tuple(sorted(edges, key=lambda row: row.edge_id)))
    return freeze_worker_configuration(typed)
