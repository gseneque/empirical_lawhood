# SPDX-License-Identifier: MPL-2.0
"""Current compiler configuration edges for disclosed direct-worker fixtures."""

from dataclasses import replace

from empirical_lawhood.runtime.plans import BarrierKind, ScientificInputRole, ScientificInputSpec
from empirical_lawhood.runtime.recursive_compiler import configuration_edge_id, configuration_input_id


def freeze_worker_configuration(task):
    """Bind the actual existing config publication without changing its bytes."""
    config = task.capability.config
    assert config.artifact_id == config.config_id
    actual, = (row for row in task.external_inputs if row.logical_artifact_id == config.artifact_id)
    spec = replace(actual, input_id="config")
    edge = ScientificInputSpec(configuration_edge_id(task.task_id), "config", ScientificInputRole.CONFIGURATION,
        None, None, configuration_input_id(config.config_id), config.config_id, config.artifact_id,
        spec.expected_payload_schema, spec.expected_media_type, spec.expected_size_bytes,
        spec.expected_outcome_access, spec.expected_visibility_ceiling, BarrierKind.NONE)
    assert not any(row.scientific_role is ScientificInputRole.CONFIGURATION for row in task.scientific_inputs)
    return replace(task,
        external_inputs=tuple(sorted((spec if row is actual else row for row in task.external_inputs),
            key=lambda row: row.input_id)),
        scientific_inputs=tuple(sorted((*task.scientific_inputs, edge), key=lambda row: row.edge_id)))
