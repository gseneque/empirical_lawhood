# SPDX-License-Identifier: MPL-2.0
"""Actual current decoder metadata checks over disclosed guarded worker ports.

The reused fixtures contain literal source/native metadata and no new native
entry, issue, qualification or original outcome-access authority.
"""

from dataclasses import replace

import pytest

from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.input_access import validated_scientific_input_edges
from empirical_lawhood.runtime.plans import BarrierKind, ScientificInputRole
from tests.test_matrix_configured_protected_prefix_worker_routing import (
    configured_prefix_case, legacy_case, prepare_literal_case,  # noqa: F401 - actual shared fixtures
)
from tests.test_matrix_e3_protected_prefix_science import blocked, forbid_native  # noqa: F401
from tests.test_matrix_e3_protected_prefix_workers import (
    case, original_case, owner, prepared_case, Phase,  # noqa: F401 - actual shared fixtures
)


def _prepared(route, monkeypatch, tmp_path, fixed_case, configured_case):
    if route == "configured":
        return prepare_literal_case(configured_case, Phase.NUMERICAL, monkeypatch, tmp_path)
    return prepared_case(fixed_case, Phase.NUMERICAL, directory=tmp_path)


def _close(selected):
    for port in selected.context.input_ports:
        port.close()
    selected.bundle.close()


@pytest.mark.parametrize("route", ("fixed", "configured"))
def test_actual_prepared_config_authentication_preserves_scientific_edges_without_reading(
        route, monkeypatch, tmp_path, case, configured_prefix_case):  # noqa: F811 - shared fixtures
    # Declare module fixtures before the function guard. Lazy setup inside the
    # guard makes the module patch retain and later restore the blocked RNG.
    selected = _prepared(route, monkeypatch, tmp_path, case, configured_prefix_case)
    try:
        context = selected.context
        config_port, = (port for port in context.input_ports if port.artifact_id == context.config.artifact_id)
        actual = validated_scientific_input_edges(context, config_port=config_port)
        expected = tuple(edge for edge in selected.task.scientific_inputs
            if edge.scientific_role is not ScientificInputRole.CONFIGURATION)
        assert len(actual) == 5
        assert all(left is right for left, right in zip(actual, expected, strict=True))
        assert all(port.bytes_read == 0 for port in context.input_ports)
    finally:
        _close(selected)


@pytest.mark.parametrize("route", ("fixed", "configured"))
@pytest.mark.parametrize("damage", (
    "missing", "duplicate", "foreign-edge", "foreign-external", "foreign-logical", "foreign-port", "barrier",
))
def test_actual_prefix_decoder_refuses_missing_duplicate_or_substituted_config_before_math(
        route, damage, monkeypatch, tmp_path, case, configured_prefix_case):  # noqa: F811 - shared fixtures
    selected = _prepared(route, monkeypatch, tmp_path, case, configured_prefix_case)
    try:
        task = selected.task
        edge, = (row for row in task.scientific_inputs if row.scientific_role is ScientificInputRole.CONFIGURATION)
        incoming = tuple(row for row in task.scientific_inputs if row is not edge)
        if damage == "missing":
            additions = ()
        elif damage == "duplicate":
            additions = (edge, replace(edge, edge_id=edge.edge_id + ".duplicate", consumer_input_id="config.duplicate"))
        else:
            changes = {
                "foreign-edge": {"edge_id": "compiler.configuration.foreign"},
                "foreign-external": {"external_input_id": "compiler.configuration.foreign"},
                "foreign-logical": {"logical_artifact_id": "configuration.foreign"},
                "foreign-port": {"consumer_input_id": "configuration.foreign"},
                "barrier": {"barrier": BarrierKind.REVEAL},
            }[damage]
            additions = (replace(edge, **changes),)
        # Keep the original prepared context/task fingerprint join intact so
        # the actual CONFIGURATION semantic check is the refusal boundary.
        task = replace(task, scientific_inputs=tuple(sorted((*incoming, *additions), key=lambda row: row.edge_id)))
        contract = replace(selected.contract, execution_task=ObjectIdentity.from_record(task.task_id, task),
            execution_task_record=task)
        context = replace(selected.context, prepared_invocation=contract)
        callback_owner = __import__(selected.runner.__class__.__module__, fromlist=("science",))
        monkeypatch.setattr(callback_owner.science, "assess_prefix", blocked)
        with pytest.raises(ValueError, match="CONFIGURATION"):
            selected.runner.execute(context)
        assert all(port.bytes_read == 0 for port in context.input_ports if port.payload_schema == MATRIX_ARRAY_SCHEMA)
    finally:
        _close(selected)


@pytest.fixture(scope="module")
def utility_metadata(tmp_path_factory):
    from tests.test_matrix_native_utility import utility_case
    return utility_case(tmp_path_factory.mktemp("literal-e2-entry"))


def _utility_entry(metadata):
    """Real current E2 entry inputs and ports; no acquisition is invoked."""
    from types import SimpleNamespace

    from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_bindings as bindings
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_utility_acquisition import entry_task_id
    from empirical_lawhood.infrastructure.execution import prepare_worker_invocation
    from empirical_lawhood.infrastructure.prepared_native_invocation import NativeInputPublication, prepare_native_invocation
    from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
    from empirical_lawhood.runtime.execution import TaskContext, WorkerIsolationProfile, WorkerOutputPort
    from empirical_lawhood.runtime.plans import ArtifactOutputSpec, ExecutionTask, ExternalInputSpec
    from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
    from tests.worker_configuration_support import freeze_worker_configuration

    declaration = next(row for row in bindings.operation_declarations() if row.capability_key.endswith(".entry"))
    runner, manifest = declaration.runner_factory(), declaration.manifest()
    task_id = entry_task_id(metadata.specification)
    config = bindings.NativeUtilityEntryConfig("config." + task_id, metadata.specification, metadata.request)
    bundle = prepare_native_invocation(metadata.plane, publications=(NativeInputPublication(config.record_id, config),),
        relative_root="literal-e2-current-entry", visibility=VisibilityCeiling.DEVELOPMENT_ONLY,
        access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    verified, = bundle.verified_inputs
    ports = metadata.plane.open_many(bundle.verified_inputs, bindings=bundle.input_bindings, maximum_bytes=None)
    reference = CapabilityConfigRef(config.record_id, config.SCHEMA, manifest.config_schema_sha256,
        config.fingerprint(), config.record_id)
    outputs = tuple(WorkerOutputPort(task_id + "." + row.output_id, row.payload_schema, row.profile, row.media_type,
        "literal.e2.entry." + row.output_id) for row in declaration.outputs)
    budget = metadata.request.resources.for_operation("entry")
    context = TaskContext("run.literal.e2.entry", task_id, "attempt.literal.e2.entry", reference,
        bundle.input_bindings, ports, outputs, manifest.permissions, OutcomeAccess.DEVELOPMENT_VISIBLE, budget,
        WorkerIsolationProfile.TRUSTED_LOCAL)
    spec = ExternalInputSpec("config", config.record_id, config.fingerprint(), config.SCHEMA, "application/json",
        verified.materialization.size_bytes, verified.logical.visibility_ceiling, verified.logical.outcome_access, None)
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind, reference,
        manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions, EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE, budget)
    task = ExecutionTask(task_id, declaration.stage, requirement, manifest.implementation_sha256, (), (spec,),
        tuple(ArtifactOutputSpec(row.output_id, row.logical_artifact_id, "literal-e2-entry/" + row.output_id + ".json",
            row.payload_schema, row.profile, row.media_type, VisibilityCeiling.DEVELOPMENT_ONLY,
            (VisibilityCeiling.DEVELOPMENT_ONLY,), OutcomeAccess.DEVELOPMENT_VISIBLE) for row in outputs), (),
        declaration.execution_properties.barrier, 1, ("obligation.literal.e2.entry",), scientific_inputs=())
    task = freeze_worker_configuration(task)
    provenance = metadata.source.provenance
    implementation = RecursiveImplementationBinding(provenance.package_sources, provenance.code_sources_sha256,
        provenance.dependency_lock_sha256, provenance.observed_git_head, provenance.observed_checkout_clean)
    contract = prepare_worker_invocation(runner, context, bundle.verified_inputs, implementation=implementation,
        execution_plan=ObjectIdentity("plan.literal.e2.entry", "empirical-lawhood/runtime/execution-plan", "1.0.0", "e" * 64),
        execution_task=ObjectIdentity.from_record(task_id, task), execution_task_record=task)
    return SimpleNamespace(context=replace(context, prepared_invocation=contract), runner=runner,
        bundle=bundle, task=task, contract=contract)


def test_actual_e2_entry_authenticates_config_then_runs_pure_seal_without_native(utility_metadata, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_bindings as bindings
    for name in ("execute_parameter_native_work", "execute_paired_response_native_work"):
        monkeypatch.setattr(bindings, name, blocked)
    selected = _utility_entry(utility_metadata)
    try:
        result = selected.runner.execute(selected.context)
        payload, = result.outputs
        assert payload.payload == utility_metadata.acquisition.canonical_bytes()
        assert not selected.contract.native_effect
    finally:
        _close(selected)


@pytest.mark.parametrize("damage", ("missing", "foreign"))
def test_actual_e2_entry_refuses_config_edge_substitution_before_seal(utility_metadata, monkeypatch, damage):
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_bindings as bindings
    selected = _utility_entry(utility_metadata)
    try:
        edge, = selected.task.scientific_inputs
        edges = () if damage == "missing" else (replace(edge, external_input_id="compiler.configuration.foreign"),)
        task = replace(selected.task, scientific_inputs=edges)
        contract = replace(selected.contract, execution_task_record=task,
            execution_task=ObjectIdentity.from_record(task.task_id, task))
        context = replace(selected.context, prepared_invocation=contract)
        monkeypatch.setattr(bindings.r, "acquisition_seal", blocked)
        with pytest.raises(ValueError, match="CONFIGURATION"):
            selected.runner.execute(context)
    finally:
        _close(selected)
