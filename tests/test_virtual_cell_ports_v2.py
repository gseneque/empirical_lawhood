# SPDX-License-Identifier: MPL-2.0
"""Shared template/compiler/provider checks over exposed metadata only."""

from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.compiler import _compile_step, _template_order
from empirical_lawhood.runtime.plans import ExecutionTask, PlanLane, ProtocolExecutionPlan

from empirical_lawhood.adapters.physical.virtual_cell import protocol, system
from empirical_lawhood.adapters.physical.virtual_cell.contracts import (
    LeaderboardSnapshot,
    VirtualCellSourceManifest,
    VirtualCellSourceObject,
    VirtualCellSourcePart,
    VirtualCellSplit,
)
from empirical_lawhood.adapters.physical.virtual_cell.custody_transport_v2 import CanonicalEvidenceV2
from empirical_lawhood.adapters.physical.virtual_cell.ports_v2 import (
    ORIGINAL_CONFIG_INPUT_ID_V2,
    project_template_v2,
    virtual_cell_capability_registry_v2,
)
from empirical_lawhood.adapters.physical.virtual_cell.provider_v2 import VirtualCellCampaignRuntimeProviderV2
from empirical_lawhood.adapters.physical.virtual_cell.registry import virtual_cell_capability_keys, virtual_cell_capability_registry
from tests.test_virtual_cell_custody_v2 import fixture
from tests.test_virtual_cell_runtime_v2 import _selection


class _NoContact:
    def __getattr__(self, name):
        raise AssertionError("metadata preparation contacted source/scratch: " + name)


def _metadata():
    case = fixture()
    manifest = next(value for value in case.records.values() if type(value) is VirtualCellSourceManifest)
    features = b"exposed feature metadata; never decoded as scientific arrays"
    roster = b"target_gene,n_cells\ntest.a,2\n"
    digest = sha256(roster).hexdigest()
    source = VirtualCellSourceObject("source.test-roster.exposed", VirtualCellSplit.TEST,
        "prefix/target-roster", "roster.exposed.csv", "generation.exposed", len(roster), digest,
        "AAAAAA==", "text/csv", (VirtualCellSourcePart("part.roster.exposed", "roster.csv", len(roster), digest),), False)
    manifest = replace(manifest, manifest_id=protocol.SOURCE_MANIFEST_INPUT_ID,
        objects=tuple(sorted((*manifest.objects, source), key=lambda row: row.object_id)), expected_object_count=5)
    leaderboard = LeaderboardSnapshot(protocol.LEADERBOARD_SNAPSHOT_INPUT_ID, "https://example.invalid/exposed",
        "2026-01-01T00:00:00Z", 1, 1, (), False, False, "EXPOSED_SOFTWARE", "d" * 64)
    original = replace(case.original, source_manifest_sha256=manifest.fingerprint(),
        target_feature_artifact_id=protocol.TARGET_FEATURE_INPUT_ID, target_feature_sha256=sha256(features).hexdigest(),
        leaderboard_snapshot_sha256=leaderboard.fingerprint())
    selected = _selection(original)
    digests = {key: "1" * 64 for key in virtual_cell_capability_keys()}
    return SimpleNamespace(original=original, selection=selected, manifest=manifest,
        test=next(value for value in manifest.objects if value.sealed), features=features, roster=roster,
        leaderboard=leaderboard, old_registry=virtual_cell_capability_registry(digests),
        registry=virtual_cell_capability_registry_v2(digests))


def _template(values, development):
    full = protocol.virtual_cell_protocol(registry=values.old_registry, config=values.original)
    experiment = system.virtual_cell_2025_experiment(system.virtual_cell_2025_system(), values.original, test_source=values.test)
    kwargs = dict(experiment=experiment, registry=values.old_registry,
        source_manifest=values.manifest, test_source=values.test,
        target_feature_sha256=sha256(values.features).hexdigest(), target_feature_size_bytes=len(values.features),
        test_roster_sha256=sha256(values.roster).hexdigest(), test_roster_size_bytes=len(values.roster),
        leaderboard_snapshot_sha256=values.leaderboard.fingerprint(),
        leaderboard_snapshot_size_bytes=len(values.leaderboard.canonical_bytes()))
    if development:
        old = protocol.virtual_cell_development_template(
            protocol=protocol.virtual_cell_development_protocol(registry=values.old_registry, config=values.original),
            full_protocol=full, **kwargs)
    else:
        old = protocol.virtual_cell_template(protocol=full, **kwargs)
    selected = project_template_v2(old, registry=values.registry, original_config=values.original, selection=values.selection)
    selected.__post_init__()
    return selected, experiment


def _plan(values, template, experiment):
    # Exercise the real stage compiler without fabricating an issue or grant.
    # This locally constructed plan is an exposed software fixture only.
    steps = {row.step_id: row for row in template.protocol.steps}
    compiled = {}
    external = {row.input_id: row for row in template.graph.external_inputs}
    for name in _template_order(template.protocol):
        compiled[name] = _compile_step(run_plan_id="run.exposed-v2", template=steps[name], compiled_steps=compiled,
            experiment=experiment, registry=values.registry, dataset_bindings=(), scientific_graph=template.graph,
            incoming_edges=tuple(row for row in template.graph.edges if row.consumer_node_id == name), external_by_id=external)
    tasks = []
    for name, row in sorted(compiled.items()):
        manifest = values.registry.require(row.capability)
        tasks.append(ExecutionTask(name, row.stage, row.capability, manifest.implementation_sha256,
            row.dependency_step_ids, row.external_inputs, row.outputs, row.resource_lock_ids, row.barrier,
            row.maximum_attempts, row.obligation_ids, scientific_inputs=row.scientific_inputs))
    return ProtocolExecutionPlan("execution.exposed-v2", PlanLane.PROSPECTIVE,
        ObjectIdentity("run.exposed-v2", "empirical-lawhood/runtime/run-plan", "1.0.0", "1" * 64),
        values.registry.fingerprint(), "1" * 40, tuple(tasks), True)


@pytest.mark.parametrize("development", [False, True])
def test_projected_template_compiles_and_provider_binds_exact_ports_without_contact(development):
    values = _metadata()
    template, experiment = _template(values, development)
    assert len(template.protocol.steps) == (7 if development else 9)
    plan = _plan(values, template, experiment)
    provider = VirtualCellCampaignRuntimeProviderV2(selection=values.selection, registry=values.registry,
        config=values.original, source_manifest=values.manifest, test_source=values.test,
        target_feature_payload=values.features, test_roster_payload=values.roster,
        leaderboard_snapshot=values.leaderboard, source_port=_NoContact(), scratch_port=_NoContact())
    supplied = provider.external_inputs(plan)
    by_id = {value.logical_artifact_id: value for value in supplied}
    assert b"".join(by_id[protocol.CONFIG_ARTIFACT_ID].source.chunks(65536)) == values.selection.canonical_bytes()
    assert b"".join(by_id[ORIGINAL_CONFIG_INPUT_ID_V2].source.chunks(65536)) == values.original.canonical_bytes()
    assert by_id[protocol.CONFIG_ARTIFACT_ID].outcome_access is OutcomeAccess.OUTCOME_BLIND
    for decoder in provider.config_decoders():
        decoder.validate_config(values.selection.canonical_bytes(), expected_schema=values.selection.SCHEMA)
    runners = provider.runners(values.registry)
    assert len(runners) == 9
    contracts = provider.output_semantic_contracts(values.registry, plan)
    assert len({value.key for value in contracts}) == len(contracts)
    assert all(any(value.payload_schema == CanonicalEvidenceV2.SCHEMA
        and value.capability_key == step.capability_key for value in contracts) for step in template.protocol.steps)
    adjudication = provider.scientific_adjudication_contract(values.registry, plan)
    assert adjudication.capability_version == "2.0.0"
    assert adjudication.output_id == ("vcc-report-development.scientific-adjudication" if development
        else "vcc-evaluate-official.scientific-adjudication")
    if development:
        assert protocol.SEALED_TEST_BINDING_INPUT_ID not in by_id
        assert protocol.LEADERBOARD_SNAPSHOT_INPUT_ID not in by_id
        assert all(task.capability.requested_outcome_access is not OutcomeAccess.EVALUATOR_REVEAL for task in plan.tasks)
