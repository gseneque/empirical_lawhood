# SPDX-License-Identifier: MPL-2.0
"""Actual receipted literal E6 partial products, no issue or native acquisition.

The installed graph and physical writer are real. Configuration selection is a
closed disclosed seam; separate current-authority controls cover that boundary.
"""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import matrix_selected_scientific_read as reader
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_protected_bindings as owner
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_future as future
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_original_commitments import MatrixSelectedEntryEvidenceV3
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_programme import MatrixSelectedPublicProgramme
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec, ScientificInputRole, ScientificInputSpec
from tests.worker_configuration_support import freeze_worker_configuration
from tests.test_matrix_e6_transport_assessment import fixture_case, exposed_parent_census
from tests.test_recursive_public_service import _plane


@pytest.mark.parametrize("damage", (None, "decision", "entry"))
def test_receipted_causal_admission_with_missing_future_retains_unpublished_worst_case(tmp_path, monkeypatch, damage):
    case = fixture_case()
    programme = MatrixSelectedPublicProgramme.from_programme(case.programme)
    evidence = ObjectIdentity("evidence.disclosed.e6-read", MatrixSelectedEntryEvidenceV3.SCHEMA, "1.0.0", "a" * 64)
    configurations, _, links, _, _ = owner.contracts(programme, evidence, 1,
        transport_policy=case.policy, transport_calibration=case.projection,
        produced_input_parents=exposed_parent_census(programme))
    configurations = dict(configurations)
    declarations = {(row.capability_key, row.capability_version): row for row in owner.operation_declarations()}
    tasks = {}
    for node, config in configurations.items():
        version = owner.config_capability_version(config)
        key = owner.capability_key(config.phase, version)
        declaration = declarations[key, version]
        outputs = tuple(SimpleNamespace(output_id=node + "." + output.output_id,
            logical_artifact_id="artifact." + node + "." + output.output_id, payload_schema=output.payload_schema,
            profile=output.profile, media_type=output.media_type)
            for output in declaration.outputs)
        inputs = tuple(SimpleNamespace(consumer_input_id=edge.consumer_input_id,
            producer_task_id=edge.producer_node_id,
            producer_output_id=edge.producer_node_id + "." + edge.producer_output_id,
            operational_logical_artifact_id="artifact." + edge.producer_node_id + "." + edge.producer_output_id)
            for edge in links if edge.consumer_node_id == node and edge.producer_node_id is not None)
        tasks[node] = SimpleNamespace(task_id=node, outputs=outputs, scientific_inputs=inputs,
            capability=SimpleNamespace(capability_key=key, capability_version=version))
    plane, receipts = _plane(tmp_path / "custody"), {}
    run_id = "run.disclosed.e6-partial"
    def publish(task, values):
        publications = []
        for name, record in sorted(values.items()):
            logical = next(output.logical_artifact_id for output in task.outputs if output.output_id == task.task_id + "." + name)
            publications.append(plane.write(ArtifactWriteRequest(logical,
                "partial/" + record.fingerprint() + ".json", record.SCHEMA, ArtifactProfile.CANONICAL_JSON,
                "application/json", "publication." + record.fingerprint(), "partial", record.canonical_bytes(),
                VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND)))
        receipts[task.task_id] = CanonicalTaskReceipt("receipt." + task.task_id, run_id, task.task_id,
            "attempt." + task.task_id, "c" * 40, (), tuple(value.materialization for value in publications),
            tuple(sorted((value.logical for value in publications), key=lambda row: row.logical_artifact_id)),
            (), OperationalStatus.SUCCEEDED, ())
    entry_task = tasks[owner.global_node(programme, "entry")]
    seal = reader.entry_seal(programme)
    if damage == "entry":
        seal = replace(seal, source_ids=seal.source_ids[1:])
    publish(entry_task, {"product": seal})
    _, source = programme.sources.source_arms()[0]
    point_task = tasks[future.node_id(source, "point")]
    point = case.observations["case." + source.source_id][0]
    config = configurations[future.node_id(source, "responses")]
    decision = future.transport_decision_for(config, point)
    if damage == "decision":
        decision = replace(decision, error_uppers=tuple(None if value is None else value + 1 for value in decision.error_uppers))
    publish(point_task, {"product": point, "decision": decision})
    def configuration(writer, actual_run, task, kinds):
        assert actual_run == run_id and type(configurations[task.task_id]) in kinds
        return configurations[task.task_id]
    # The final reducer has no receipt, but its complete frozen CONFIGURATION
    # and science-edge census must still be real typed metadata. Missing future
    # receipts remain absent; this creates no successful terminal or authority.
    terminal_id = owner.global_node(programme, "assess-programme")
    terminal = tasks[terminal_id]
    config = configurations[terminal_id]
    declaration = declarations[terminal.capability.capability_key, terminal.capability.capability_version]
    manifest = declaration.manifest()
    raw = config.canonical_bytes()
    config_publication = plane.write(ArtifactWriteRequest(config.config_id,
        "reader-configuration/transport-terminal.json", config.SCHEMA, ArtifactProfile.CANONICAL_JSON,
        "application/json", "publication." + config.config_id, "reader-configuration", raw,
        declaration.visibility_ceiling, (), declaration.outcome_access))
    reference = CapabilityConfigRef(config.config_id, config.SCHEMA, manifest.config_schema_sha256,
        config.fingerprint(), config.config_id)
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version,
        manifest.kind, reference, manifest.input_schema_ids, manifest.output_schema_ids,
        manifest.permissions, declaration.evidence_ceiling, declaration.outcome_access, declaration.resources)
    science = []
    for edge in terminal.scientific_inputs:
        producer = tasks[edge.producer_task_id]
        source_output = next(row for row in producer.outputs if row.output_id == edge.producer_output_id)
        source_declaration = declarations[producer.capability.capability_key, producer.capability.capability_version]
        science.append(ScientificInputSpec("edge." + terminal_id + "." + edge.consumer_input_id,
            edge.consumer_input_id, ScientificInputRole.HISTORY, producer.task_id, source_output.output_id,
            None, source_output.logical_artifact_id, source_output.logical_artifact_id, source_output.payload_schema,
            source_output.media_type, source_declaration.resources.output_bytes,
            source_declaration.outcome_access, source_declaration.visibility_ceiling, BarrierKind.NONE))
    config_input = ExternalInputSpec("config", config.config_id, config.fingerprint(), config.SCHEMA,
        "application/json", len(raw), config_publication.logical.visibility_ceiling,
        config_publication.logical.outcome_access, None)
    outputs = tuple(ArtifactOutputSpec(row.output_id, row.logical_artifact_id,
        "unentered/" + row.output_id + ".json", row.payload_schema, row.profile, row.media_type,
        declaration.visibility_ceiling, (), declaration.outcome_access) for row in terminal.outputs)
    terminal = ExecutionTask(terminal_id, declaration.stage, requirement, manifest.implementation_sha256,
        tuple(sorted({edge.producer_task_id for edge in science})), (config_input,), outputs,
        (), declaration.execution_properties.barrier, 1, ("obligation.disclosed.e6-partial-reducer",),
        scientific_inputs=tuple(sorted(science, key=lambda row: row.edge_id)))
    tasks[terminal_id] = freeze_worker_configuration(terminal)
    monkeypatch.setattr(reader, "_configuration", configuration)
    arguments = (plane, SimpleNamespace(run_plan_id=run_id), SimpleNamespace(tasks=tuple(tasks.values())),
        receipts, entry_task, configurations[entry_task.task_id])
    if damage is not None:
        with pytest.raises((ValueError, PermissionError)):
            reader._transport_science(*arguments, partial=True)
        return
    actual = reader._transport_science(*arguments, partial=True)
    assert actual["adjudication"] is None and actual["assessment_custody"] == "UNPUBLISHED_PARTIAL_REDUCTION"
    assert actual["qualification"] == "NOT_ESTABLISHED"
    assert sum(row["assigned_units"] for row in actual["denominators"].values()) == 4
    assert sum(row["false_admissions_unresolved"] for row in actual["denominators"].values()) == 1
    assert sum(row["joint_service_successes"] for row in actual["denominators"].values()) == 0
    assert len(receipts) == 2
    projected = actual["predicted_lifetimes"]
    assert projected["scope"] == "DECLARED_FINITE_HORIZON_LATTICE"
    assert len(projected["rows"]) == 4 * 5 * 3
    assert sum(row["status"] == "MISSING_POINT" for row in projected["rows"]) == 3 * 5 * 3
    assert all(row["status"] != "MISSING_POINT" for row in projected["rows"]
        if row["case_id"] == "case." + source.source_id)
