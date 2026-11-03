# SPDX-License-Identifier: MPL-2.0
"""Pure frozen task metadata, without byte custody or permission claims.

The real compiler fixture uses disclosed software metadata only. No source
capture, stored receipt, worker, native effect or original grant is supplied.
"""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.input_access import validated_task_scientific_input_edges
from empirical_lawhood.runtime.plans import BarrierKind, ProtocolExecutionTask, ScientificInputRole
from tests.runtime_platform.test_recursive_graph_indexes import _compile


@pytest.fixture(scope="module")
def compiled_metadata():
    return _compile(1)


def _consumer(compiled):
    return next(task for task in compiled.execution_plan.tasks if task.task_id != "source")


def _config_rows(task):
    edge, = (value for value in task.scientific_inputs if value.scientific_role is ScientificInputRole.CONFIGURATION)
    spec, = (value for value in task.external_inputs if value.input_id == "config")
    return edge, spec


def _changed(task, *, edge=None, spec=None, extra_edges=(), missing_edge=False, missing_spec=False):
    original_edge, original_spec = _config_rows(task)
    edges = tuple(value for value in task.scientific_inputs if value is not original_edge)
    specs = tuple(value for value in task.external_inputs if value is not original_spec)
    if not missing_edge:
        edges += (original_edge if edge is None else edge,)
    if not missing_spec:
        specs += (original_spec if spec is None else spec,)
    return replace(task, scientific_inputs=tuple(sorted((*edges, *extra_edges), key=lambda value: value.edge_id)),
        external_inputs=tuple(sorted(specs, key=lambda value: value.input_id)))


@pytest.mark.parametrize("node", ("source", "use-0000"))
def test_actual_compiler_task_retains_config_custody_and_original_scientific_edge_order(compiled_metadata, node):
    task = next(task for task in compiled_metadata.execution_plan.tasks if task.task_id == node)
    raw = task.canonical_bytes()
    edge, spec = _config_rows(task)
    expected = tuple(value for value in task.scientific_inputs if value.scientific_role is not ScientificInputRole.CONFIGURATION)
    actual = validated_task_scientific_input_edges(task)
    assert all(left is right for left, right in zip(actual, expected, strict=True))
    if node == "source":
        assert actual == ()
        assert edge.outcome_access is spec.expected_outcome_access is OutcomeAccess.EVALUATION_SEALED
    else:
        assert tuple(value.consumer_input_id for value in actual) == ("operand.a", "operand.z")
        assert all(value.outcome_access is OutcomeAccess.EVALUATION_SEALED for value in actual)
        assert edge.outcome_access is spec.expected_outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE
    assert edge.visibility_ceiling is spec.expected_visibility_ceiling is VisibilityCeiling.DEVELOPMENT_ONLY
    assert task.canonical_bytes() == raw


@pytest.mark.parametrize("damage", (
    "missing-edge", "duplicate-edge", "foreign-edge", "foreign-external", "foreign-logical", "foreign-operational",
    "foreign-port", "barrier", "missing-spec", "spec-port", "spec-hash", "spec-schema", "spec-media", "spec-size",
    "absent-hash", "absent-schema", "absent-media", "absent-size", "zero-size", "boolean-size", "edge-size",
    "access", "visibility", "absent-access", "absent-visibility", "raw-access", "raw-visibility", "identity-scope",
))
def test_frozen_config_metadata_refuses_thinning_aliases_and_substituted_operands(compiled_metadata, damage):
    task = _consumer(compiled_metadata)
    edge, spec = _config_rows(task)
    options = {}
    if damage == "missing-edge":
        options["missing_edge"] = True
    elif damage == "missing-spec":
        options["missing_spec"] = True
    elif damage == "duplicate-edge":
        options["extra_edges"] = (replace(edge, edge_id=edge.edge_id + ".duplicate", consumer_input_id="config.duplicate"),)
    elif damage in ("absent-size", "zero-size", "boolean-size"):
        size = {"absent-size": None, "zero-size": 0, "boolean-size": True}[damage]
        options["spec"] = replace(spec, expected_size_bytes=size)
        # A zero edge-size is already refused by its owning record constructor.
        if size != 0 or type(size) is bool:
            options["edge"] = replace(edge, maximum_size_bytes=size)
    elif damage == "raw-access":
        options["spec"] = replace(spec, expected_outcome_access=spec.expected_outcome_access.value)
        options["edge"] = replace(edge, outcome_access=edge.outcome_access.value)
    elif damage == "raw-visibility":
        options["spec"] = replace(spec, expected_visibility_ceiling=spec.expected_visibility_ceiling.value)
        options["edge"] = replace(edge, visibility_ceiling=edge.visibility_ceiling.value)
    else:
        edge_changes = {
            "foreign-edge": {"edge_id": "compiler.configuration.foreign"},
            "foreign-external": {"external_input_id": "compiler.configuration.foreign"},
            "foreign-logical": {"logical_artifact_id": "configuration.foreign"},
            "foreign-operational": {"operational_logical_artifact_id": "configuration.foreign"},
            "foreign-port": {"consumer_input_id": "configuration.foreign"},
            "barrier": {"barrier": BarrierKind.REVEAL},
            "edge-size": {"maximum_size_bytes": edge.maximum_size_bytes + 1},
        }
        spec_changes = {
            "spec-port": {"input_id": "configuration.foreign"},
            "spec-hash": {"expected_content_sha256": "f" * 64},
            "spec-schema": {"expected_payload_schema": "empirical-lawhood/testing/foreign-configuration"},
            "spec-media": {"expected_media_type": "application/octet-stream"},
            "spec-size": {"expected_size_bytes": spec.expected_size_bytes + 1},
            "absent-hash": {"expected_content_sha256": None, "identity_scope_sha256": "e" * 64},
            "absent-schema": {"expected_payload_schema": None},
            "absent-media": {"expected_media_type": None},
            "access": {"expected_outcome_access": OutcomeAccess.OUTCOME_BLIND},
            "visibility": {"expected_visibility_ceiling": VisibilityCeiling.PROSPECTIVE},
            "absent-access": {"expected_outcome_access": None},
            "absent-visibility": {"expected_visibility_ceiling": None},
            "identity-scope": {"identity_scope_sha256": "e" * 64},
        }
        if damage in edge_changes:
            options["edge"] = replace(edge, **edge_changes[damage])
        else:
            options["spec"] = replace(spec, **spec_changes[damage])
    changed = _changed(task, **options)
    with pytest.raises(ValueError, match="CONFIGURATION"):
        validated_task_scientific_input_edges(changed)


@pytest.mark.parametrize("damage", ("logical", "operational", "external"))
def test_nonconfig_scientific_edge_cannot_impersonate_reserved_configuration(compiled_metadata, damage):
    task = _consumer(compiled_metadata)
    configuration, _ = _config_rows(task)
    original = next(value for value in task.scientific_inputs if value.consumer_input_id == "operand.a")
    changes = ({"logical_artifact_id": configuration.logical_artifact_id} if damage == "logical" else
        {"operational_logical_artifact_id": configuration.operational_logical_artifact_id} if damage == "operational" else
        {"external_input_id": configuration.external_input_id, "producer_task_id": None, "producer_output_id": None})
    changed = replace(original, **changes)
    # operand.z still supplies the original dependency, so the task remains a
    # well-formed current record and reaches the exact reserved-config guard.
    task = replace(task, scientific_inputs=tuple(changed if value is original else value for value in task.scientific_inputs))
    with pytest.raises(ValueError, match="alias.*CONFIGURATION"):
        validated_task_scientific_input_edges(task)


def test_task_config_reference_cannot_select_a_foreign_transport_alias(compiled_metadata):
    task = _consumer(compiled_metadata)
    config = replace(task.capability.config, artifact_id="configuration.foreign")
    task = replace(task, capability=replace(task.capability, config=config))
    with pytest.raises(ValueError, match="CONFIGURATION"):
        validated_task_scientific_input_edges(task)


@pytest.mark.parametrize("kind", ("object", "namespace", "protocol"))
def test_only_current_actual_execution_task_metadata_is_supported(compiled_metadata, kind):
    task = _consumer(compiled_metadata)
    if kind == "object":
        foreign = object()
    elif kind == "namespace":
        foreign = SimpleNamespace(capability=task.capability, scientific_inputs=task.scientific_inputs,
            external_inputs=task.external_inputs, task_id=task.task_id)
    else:
        foreign = ProtocolExecutionTask(**{name: getattr(task, name) for name in (
            "task_id", "stage", "capability", "capability_implementation_sha256", "dependency_task_ids", "external_inputs",
            "outputs", "resource_lock_ids", "barrier", "maximum_attempts", "obligation_ids")})
    with pytest.raises(ValueError, match="CONFIGURATION"):
        validated_task_scientific_input_edges(foreign)
