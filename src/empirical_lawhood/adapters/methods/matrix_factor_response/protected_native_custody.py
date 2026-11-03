# SPDX-License-Identifier: MPL-2.0
"""Shared native custody checks behind exact version-specific contracts."""
from hashlib import sha256
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.native_subwork import require_native_completion_receipt
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import response_consumed_streams


def validate_current_native(response, config, *, native_contract, expected_run_id=None, producing_provenance=None, **operands):
    reference, configuration, task, operation, sources, streams, outputs = native_contract(config, **operands)
    event, = response.native
    definition, completion, receipt = event.definition, event.completion, event.receipt
    source, history, protocol = operands["source"], operands["history"], operands["protocol"]
    if (expected_run_id is None) != (producing_provenance is None):
        raise ValueError('response native origin requires both its actual run and producing provenance')
    run_id = history.native.definition.parent_contact.run_id if expected_run_id is None else expected_run_id
    provenance = source.provenance if producing_provenance is None else producing_provenance
    consumed = response_consumed_streams(source, protocol, streams)
    if (response.source != reference or definition.configuration != configuration or definition.parent_contact.task_id != task
            or definition.parent_contact.run_id != run_id
            or definition.parent_contact.implementation_commit != provenance.observed_git_head
            or definition.subwork_id != "responses." + config.source.root_id or definition.operation_id != operation
            or definition.sources != sources or definition.streams != streams or definition.outputs != outputs
            or definition.code_sources_sha256 != provenance.code_sources_sha256
            or definition.dependency_lock_sha256 != provenance.dependency_lock_sha256
            or completion.consumed_streams != consumed or completion.unconsumed_streams != tuple(row for row in streams if row not in consumed)):
        raise ValueError("protected E3 native response changes its current direct-input/configuration/stream contract")
    native_task = "native-subwork." + sha256((task + ":" + definition.subwork_id).encode()).hexdigest()
    expected_ids = {native_task + ".output.arrays", native_task + ".completion"}
    attempt = definition.parent_contact.run_id + "." + native_task + ".attempt-001"
    if ((receipt.run_id, receipt.task_id, receipt.attempt_id, receipt.receipt_id) != (
            definition.parent_contact.run_id, native_task, attempt, "receipt." + attempt)
            or len(receipt.output_logical_artifacts) != 2 or len(receipt.output_materializations) != 2
            or {row.logical_artifact_id for row in receipt.output_logical_artifacts} != expected_ids
            or {row.logical_artifact_id for row in receipt.output_materializations} != expected_ids):
        raise ValueError("protected E3 native response changes its original nested task/attempt receipt")
    logical = tuple(row for row in receipt.output_logical_artifacts if row.logical_artifact_id == native_task + ".output.arrays")
    physical = tuple(row for row in receipt.output_materializations if row.logical_artifact_id == native_task + ".output.arrays")
    saved = response.arrays.array_artifact
    if (len(logical) != 1 or len(physical) != 1 or
            (logical[0].payload_schema, logical[0].profile, logical[0].media_type, logical[0].content_sha256,
             logical[0].outcome_access, logical[0].visibility_ceiling, physical[0].physical_sha256, physical[0].size_bytes) !=
            (saved.payload_schema, ArtifactProfile.MATRIX_ARRAY_NPZ, saved.media_type, saved.sha256,
             response.arrays.outcome_access, response.arrays.visibility_ceiling, saved.sha256, saved.size_bytes)):
        raise ValueError("protected E3 response archive differs from exact original nested native bytes")
    require_native_completion_receipt(completion, receipt, outcome_access=response.arrays.outcome_access,
        visibility_ceiling=response.arrays.visibility_ceiling)

