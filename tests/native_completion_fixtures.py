# SPDX-License-Identifier: MPL-2.0
"""Disclosed completion metadata for software fixtures; no native contact or authority."""
from dataclasses import replace
from hashlib import sha256

from empirical_lawhood.runtime.artifacts import (
    ArtifactGenericValidation, ArtifactLineageParent, ArtifactMaterialization,
    ArtifactProfile, ArtifactWriteRequest, ArtifactWriteResult, LogicalArtifactIdentity,
    lineage_parent_sort_key,
)


def completion_parents(completion, visibility, access):
    return tuple(sorted((ArtifactLineageParent(value, visibility, access)
        for value in (completion.definition, completion.contact)), key=lineage_parent_sort_key))


def publish_completion(plane, receipt, completion, *, visibility, access):
    """Publish actual canonical fixture bytes with the native completion lineage."""
    logical_id = receipt.task_id + '.completion'
    binding = logical_id + ':' + visibility.value + ':' + access.value
    path = 'software-native-completions/' + sha256(binding.encode()).hexdigest() + '.' + completion.fingerprint() + '.json'
    publication = plane.write(ArtifactWriteRequest(logical_id, path, completion.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'software-native-completions',
        'software-native-completions', completion.canonical_bytes(), visibility, (visibility, visibility), access,
        lineage_parents=completion_parents(completion, visibility, access)))
    return receipt_with_completion(receipt, publication)


def literal_completion(completion, task_id, *, visibility, access):
    """Type-correct, explicitly unpublished metadata for pure record controls."""
    logical_id = task_id + '.completion'
    logical = LogicalArtifactIdentity(logical_id, completion.fingerprint(), completion.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', visibility, (visibility, visibility), access,
        ArtifactGenericValidation('validator.synthetic-native-completion', '1.0.0', 'a' * 64,
            completion.SCHEMA, ArtifactProfile.CANONICAL_JSON),
        lineage_parents=completion_parents(completion, visibility, access))
    physical = ArtifactMaterialization('material.' + logical_id, logical_id,
        'storage.synthetic-unpublished', 'unpublished/' + logical_id,
        completion.fingerprint(), len(completion.canonical_bytes()), 'none')
    sidecar = replace(physical, materialization_id='sidecar.' + logical_id,
        logical_artifact_id=logical_id + '.manifest', relative_path='unpublished/' + logical_id + '.manifest.json',
        physical_sha256='b' * 64, size_bytes=1)
    return ArtifactWriteResult(logical, physical, sidecar, False)


def receipt_with_completion(receipt, publication):
    logical_id = receipt.task_id + '.completion'
    return replace(receipt,
        output_materializations=tuple(sorted((*tuple(row for row in receipt.output_materializations
            if row.logical_artifact_id != logical_id), publication.materialization), key=lambda row: row.materialization_id)),
        output_logical_artifacts=tuple(sorted((*tuple(row for row in receipt.output_logical_artifacts
            if row.logical_artifact_id != logical_id), publication.logical), key=lambda row: row.logical_artifact_id)))
