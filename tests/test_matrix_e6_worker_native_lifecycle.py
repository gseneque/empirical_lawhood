# SPDX-License-Identifier: MPL-2.0
"""Opt-in frozen-source E6 response-worker conformance on exposed fixture roots.

The original package, zero preparation paths, feature values and admitted Pauli
frame are disclosed software premises. Only the four complete paired futures
are actually acquired. This does not enter a public scientific programme or
establish source, prefix, calibration, transfer or issue qualification.

The actual software futures expose the declared canonical T=1.25 and T=3
physical coordinates. New group labels or RNG keys cannot restore withheld
regime standing. The authored zero prefix performs no native preparation.

The coordinator enables this file only after committing the complete tested
source and reconciling its disclosed keys with every selected reservation.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from threadpoolctl import threadpool_limits

from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_prefix
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_future as future
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_protected_bindings as owner
from empirical_lawhood.adapters.methods.matrix_experimental_programme.e6_transport_science import project_e6_frozen_calibration
from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_records import MatrixPreparationAssessment, preparation_identity
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_forecast import forecast_public
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_point import MatrixPreparedPublicSource
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_response_science import MatrixPreparedResponseReadout
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_e6_transport_config import MatrixSelectedTransportFutureConfig, MatrixSelectedTransportScoreConfig
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_point import forecast_selected_point
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_programme import MatrixSelectedPublicProgramme
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_results import entry_seal
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_workers import SelectedProtectedWorker
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_public import package_identity
from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity as scheduled_identity
from empirical_lawhood.api.recursive_authoring import implementation_binding
from empirical_lawhood.infrastructure import execution as lifecycle
from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays, encode_matrix_arrays
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.infrastructure.numerical_provenance import capture_numerical_provenance, selected_worker_environment
from empirical_lawhood.infrastructure.source_origin import require_executing_target_source
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactManifest, ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
from empirical_lawhood.runtime.execution import DependencyReceiptBinding, TaskContext, VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.native_subwork import NativeSubworkState
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec, ScientificInputRole, ScientificInputSpec
from tests.test_matrix_e6_transport_assessment import fixture_case
from tests.test_matrix_factor_confirmation_eligibility import _matrix_plane
from tests.test_matrix_selected_native_work import literal_history
from tests.test_matrix_selected_package import reference
from tests.test_matrix_selected_point import feature
from tests.test_matrix_scheduled_response_forecast import pauli


pytestmark = pytest.mark.skipif(os.environ.get("EL_RUN_E6_NATIVE_CONTROL") != "1",
    reason="coordinator must freeze source and reconcile exposed E6 software keys before this actual native control")
ROOT = Path(__file__).resolve().parents[1]


def physical_cores():
    selected = {}
    for cpu in sorted(os.sched_getaffinity(0)):
        topology = Path("/sys/devices/system/cpu") / ("cpu" + str(cpu)) / "topology"
        key = ((topology / "physical_package_id").read_text().strip(), (topology / "core_id").read_text().strip())
        selected.setdefault(key, cpu)
    assert len(selected) >= 4, "this control requires four distinct available physical cores"
    return tuple(selected[key] for key in sorted(selected)[:4])


def bind_current_source(case, provenance):
    """Retain declared roots/keys and explicitly author current software source."""
    programme, closure = case.programme, case.programme.sources.closure
    source_index = ScheduledSourceIndex.from_shared(reservation=closure.reservation,
        specification=closure.specification, provenances=(provenance,))
    descriptors = tuple(source_index.reference(source_id=row.source_id, root_id=row.root_id,
        provenance=provenance.identity) for row in closure.descriptors)
    closure = replace(closure, provenances=(provenance,),
        descriptors=descriptors)
    sources = replace(programme.sources, closure=closure)
    design = replace(programme.point_design, sources=tuple((arm, MatrixPreparedPublicSource.from_source(source))
        for arm, source in sources.source_arms()))
    frame = np.asarray([np.kron(value, np.eye(2)) / 2 for value in pauli()], dtype="<c16")
    template_raw, members = encode_matrix_arrays({
        "generic_basis": np.asarray([np.kron(np.eye(2), value) / 2 for value in pauli()], dtype="<c16"),
        "force_coefficients": np.stack((np.eye(3), np.eye(3))).astype("<f8") / np.sqrt(6),
        "trace_coefficients": np.ones((2, 3), dtype="<f8") / np.sqrt(6),
        "receiver_coefficients": np.eye(48, dtype="<f8").reshape(48, 2, 2, 3, 4)})
    assay = replace(programme.assay, template_artifact=replace(programme.assay.template_artifact,
        artifact_id="templates.e6-exposed-native-control", sha256=sha256(template_raw).hexdigest(), size_bytes=len(template_raw)),
        template_members=members)
    programme = replace(programme, sources=sources, point_design=design, assay=assay)
    roles = {row[3]: row[0] for row in case.policy.regime_roster}
    rows = tuple(sorted(((roles[source.root.root.independent_group_id], source.root.root.regime_id,
        source.root.root.root_id, source.root.root.independent_group_id, source.original.source)
        for _, source in sources.source_arms()), key=lambda row: (row[0], row[2])))
    policy = replace(case.policy, regime_roster=rows)
    projection = project_e6_frozen_calibration(policy, programme.point_design.package,
        record_id="projection.e6-exposed-native-control")
    return SimpleNamespace(programme=MatrixSelectedPublicProgramme.from_programme(programme), policy=policy, projection=projection,
        frame=frame, template_raw=template_raw, implementation=implementation_binding(ROOT))


def authored_prefix(case, source):
    """Complete zero path and explicit frame premise; never a measured admission."""
    fixture = SimpleNamespace(sources=SimpleNamespace(source_arms=lambda: (("hold", source),),
        closure=case.programme.sources.closure))
    _, history, _, initial_raw, history_raw = literal_history(fixture, native_version="2.0.0")
    arrays = decode_matrix_arrays(history_raw, history.arrays)
    values = {name: value for name, value in arrays.items() if not name.endswith("innovations")}
    values["frame"] = case.frame
    numerical = reference("authored.e6-control.numerical." + source.source_id, MatrixPreparationAssessment)
    witness = reference("authored.e6-control.witness." + source.source_id, prepared_prefix.MatrixPreparedFactorWitness)
    frames = reference("authored.e6-control.frames." + source.source_id, prepared_prefix.MatrixPreparedFrameAssessment)
    causal_raw, operand = prepared_prefix._product(source, values, role="CAUSAL_STATE",
        artifact_id="authored.e6-control.causal-arrays." + source.source_id,
        producers=(source.identity, preparation_identity(history.arrays), witness, frames))
    causal = prepared_prefix.MatrixPreparedCausalPrefix("authored.e6-control.causal." + source.source_id,
        source.identity, preparation_identity(history.arrays), numerical, witness, frames,
        scheduled_identity(source.original.policy), source.total_ticks, sha256(case.frame.tobytes()).hexdigest(),
        "AVAILABLE", None, operand)
    public = MatrixPreparedPublicSource.from_source(source)
    point = forecast_selected_point(case.programme.point_design, replace(feature(case.programme.point_design, public),
        prefix=prepared_prefix.identity(causal), frame_sha256=causal.frame_sha256),
        record_id="point." + future.node_id(source, "point"))
    protocol = case.programme.protocol(source)
    mechanical_raw, mechanical = forecast_public(public, protocol, causal, causal_raw, case.template_raw,
        artifact_id="mechanical.e6-control." + source.source_id)
    assert mechanical.disposition == "AVAILABLE", "finite actual native future must not silently become nonuse"
    config = MatrixSelectedTransportFutureConfig("config." + future.node_id(source, "responses"),
        case.programme.identity, source, protocol, dict(case.programme.panels)[source.root.root.independent_group_id],
        case.programme.point_design.identity, package_identity(case.programme.point_design.package), "responses",
        case.policy, case.projection)
    values = {"source": source, "allocation": case.programme.sources.closure.reservation.allocation,
        "initial-state": initial_raw, "history": history, "history-arrays": history_raw, "causal": causal,
        "point": point, "mechanical": mechanical, "mechanical-arrays": mechanical_raw, "protocol": protocol,
        "entry": entry_seal(case.programme), "decision": future.transport_decision_for(config, point),
        **{name: value for name, _, value in owner.preparation.native_input_records(source, panels=config.panels)}}
    return SimpleNamespace(config=config, values=values, causal_raw=causal_raw)


def invoke(case, plane, fixture, cpu, *, score=None, damage=None):
    config, values = fixture.config, dict(fixture.values)
    if score is not None:
        config = MatrixSelectedTransportScoreConfig("config." + future.node_id(config.source, "response-score"),
            config.programme, config.source, config.protocol, config.panels, config.point_design, config.frozen_package,
            "response-score", config.transport_policy, config.transport_calibration)
        values = {name: value for name, value in values.items() if name != "native-provenance" and not name.startswith("native-stream.")}
        values.update({"causal-arrays": fixture.causal_raw, "templates": case.template_raw,
            "responses": score[0], "response-arrays": score[1]})
    if damage == "history-bytes":
        arrays = dict(decode_matrix_arrays(values["history-arrays"], values["history"].arrays))
        arrays["primary_positions"] = arrays["primary_positions"].copy()
        arrays["primary_positions"][1, 0, 0, 0, 0] = 1
        values["history-arrays"], _ = encode_matrix_arrays(arrays)
    declaration = next(row for row in owner.operation_declarations() if row.capability_key ==
        owner.capability_key(config.phase, owner.config_capability_version(config)))
    manifest, task_id = declaration.manifest(), owner.task_id(config)
    outputs = tuple(WorkerOutputPort(task_id + "." + row.output_id, row.payload_schema, row.profile, row.media_type,
        "output.e6-control." + config.source.source_id + "." + config.phase + "." + row.output_id) for row in declaration.outputs)
    producers = {"entry": (owner.global_node(case.programme, "entry"), "product"),
        **{name: (owner.preparation.node_id(config.source, "history"), "arrays" if name.endswith("arrays") else "product")
            for name in ("history", "history-arrays")},
        **{name: (future.node_id(config.source, phase), output) for name, phase, output in (
            ("causal", "project", "product"), ("causal-arrays", "project", "arrays"),
            ("point", "point", "product"), ("decision", "point", "decision"),
            ("mechanical", "mechanical", "product"), ("mechanical-arrays", "mechanical", "arrays"),
            ("responses", "responses", "product"), ("response-arrays", "responses", "arrays"))}}
    verified, bindings, external, edges, dependencies = [], [], [], [], {}
    suffix = config.source.source_id + "." + config.phase + (".damaged" if damage else "")
    for index, (name, value) in enumerate(sorted({"automatic": config, **values}.items())):
        array = type(value) is bytes
        raw = value if array else value.canonical_bytes()
        artifact_id = "input.e6-control." + suffix + "." + name
        schema, media, profile = ((MATRIX_ARRAY_SCHEMA, "application/x-npz", ArtifactProfile.MATRIX_ARRAY_NPZ)
            if array else (value.SCHEMA, "application/json", ArtifactProfile.CANONICAL_JSON))
        access = Access.EVALUATION_SEALED if name in ("responses", "response-arrays") else Access.OUTCOME_BLIND
        result = plane.write(ArtifactWriteRequest(artifact_id, "inputs/" + suffix + "/" + str(index).zfill(2) +
            (".npz" if array else ".json"), schema, profile, media, "e6-exposed-worker-control", "inputs", raw,
            Visibility.PROSPECTIVE, (), access))
        selected = VerifiedArtifactInput(result.logical, result.materialization)
        producer = producers.get(name)
        binding = WorkerInputBinding.from_verified(selected,
            kind=WorkerInputKind.DEPENDENCY if producer else WorkerInputKind.EXTERNAL)
        verified.append(selected)
        bindings.append(binding)
        if producer:
            dependencies.setdefault(producer[0], []).append(binding.materialization_id)
        else:
            external.append(ExternalInputSpec("external." + name, artifact_id, result.logical.content_sha256,
                schema, media, len(raw), Visibility.PROSPECTIVE, access, None))
        if name != "automatic":
            edges.append(ScientificInputSpec("edge." + name, name,
                ScientificInputRole.HISTORY if producer else ScientificInputRole.SOURCE,
                None if producer is None else producer[0], None if producer is None else producer[0] + "." + producer[1],
                "external." + name if producer is None else None, "scientific." + name, artifact_id,
                schema, media, len(raw), access, Visibility.PROSPECTIVE, BarrierKind.NONE))
    config_input = next(row for row in verified if row.artifact_id.endswith(".automatic"))
    config_ref = CapabilityConfigRef(config.config_id, config.SCHEMA, manifest.config_schema_sha256,
        config.fingerprint(), config_input.artifact_id)
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind, config_ref,
        manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions, EvidenceCeiling.NON_PROMOTABLE,
        owner.access(config.phase), owner.preparation.BUDGET)
    task = ExecutionTask(task_id, owner.stage(config.phase), requirement, manifest.implementation_sha256,
        tuple(sorted(dependencies)), tuple(external), tuple(ArtifactOutputSpec(row.output_id, row.logical_artifact_id,
            "outputs/" + suffix + "/" + row.output_id.rsplit(".", 1)[-1], row.payload_schema, row.profile, row.media_type,
            Visibility.PROSPECTIVE, (Visibility.PROSPECTIVE,), owner.access(config.phase)) for row in outputs),
        (), BarrierKind.NONE, 1, ("obligation.e6-control." + config.phase,), scientific_inputs=tuple(edges))
    receipts = tuple(DependencyReceiptBinding("receipt.e6-control." + task, task, tuple(sorted(materials)))
        for task, materials in sorted(dependencies.items()))
    ports = plane.open_many(tuple(verified), bindings=tuple(bindings), maximum_bytes=None)
    context = TaskContext("run.e6-exposed-worker-control", task_id, "attempt.e6-control." + suffix,
        config_ref, tuple(bindings), ports, outputs, manifest.permissions, owner.access(config.phase), owner.preparation.BUDGET,
        WorkerIsolationProfile.TRUSTED_LOCAL, receipts, cpu_affinity=(cpu,))
    plan = ObjectIdentity("plan.e6-exposed-worker-control", "empirical-lawhood/runtime/development-execution-plan", "1.0.0", "a" * 64)
    runner = SelectedProtectedWorker(config.phase, manifest).with_prepared_scope(
        (context.run_id, task_id, context.input_materialization_ids, plan))
    contract = lifecycle.prepare_worker_invocation(runner, context, tuple(verified), implementation=case.implementation,
        execution_plan=plan, execution_task=ObjectIdentity.from_record(task_id, task), execution_task_record=task,
        native_effect=config.phase in owner.NATIVE, provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,))
    if config.phase in owner.NATIVE:
        contract = replace(contract, native_work=runner.prepare_native_work(replace(context, prepared_invocation=contract),
            expected_parent=contract.expected_parent_contact))
    return SimpleNamespace(runner=runner, context=replace(context, prepared_invocation=contract), contract=contract,
        verified=tuple(verified), plane=plane)


def payloads(result):
    values = {}
    for row in result.outputs:
        if hasattr(row, "payload"):
            raw = row.payload
        else:
            try:
                raw = b"".join(row.source.chunks(1024 * 1024))
            finally:
                row.source.close()
            assert len(raw) == row.size_bytes and sha256(raw).hexdigest() == row.physical_sha256
        values[row.output_id.rsplit(".", 1)[-1]] = raw
    return values


def close(selected):
    for port in selected.context.input_ports:
        port.close()


def snapshot(plane):
    root = Path(plane.root.contract.canonical_path)
    return {str(path.relative_to(root)): sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*") if path.is_file() and not path.name.endswith(".lock")}


def execute_one(case, source, cpu, path):
    plane = _matrix_plane(path / "custody")
    fixture = authored_prefix(case, source)
    selected = invoke(case, plane, fixture, cpu)
    parent = selected.contract.expected_parent_contact
    contacts = ExternalNativeEffectContactStore(plane=plane, execution_plan=parent.execution_plan,
        visibility_ceiling=Visibility.PROSPECTIVE, outcome_access=Access.EVALUATION_SEALED)
    store = ExternalNativeSubworkStore(plane=plane, parent_contacts=contacts, parent_contact=parent,
        parent_inputs=tuple(ArtifactManifest(row.logical, row.materialization) for row in selected.verified),
        prepared_invocation=selected.contract)
    executor = lifecycle.LocalProcessExecutor(scratch_root=_matrix_plane(path / "worker-scratch").root)
    try:
        ready = executor.preflight(selected.runner, selected.context, prepared_contract=selected.contract,
            provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,), native_work_preparer=owner.prepare_native_work)
        assert ready.ready, tuple((row.operand_id, row.reason) for row in ready.mismatches)
        assert contacts.read(parent.run_id, parent.task_id) is None
        entries = []

        def enter():
            entries.append(parent.identity if hasattr(parent, "identity") else parent.fingerprint())
            contacts.begin(parent)
            return parent, store

        result = executor.execute(selected.runner, selected.context, timeout_seconds=None, prepared_contract=selected.contract,
            provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,), native_work_preparer=owner.prepare_native_work,
            native_entry=enter)
        actual = payloads(result)
        product = decode_canonical_bytes(actual["product"], future.MatrixSelectedFutureHistory, maximum_bytes=None)
        assert len(entries) == 1 and product.disposition == "COMPLETED" and len(product.branch_ids) == 48
        assert len(decode_matrix_arrays(actual["arrays"], product.arrays)) == 246
        definition, = selected.contract.native_work.definitions
        completed = store.recover(definition)
        assert completed.state is NativeSubworkState.COMPLETED and completed.completion == product.native[0].completion
        assert len(completed.completion.consumed_streams) == 4 and completed.completion.unconsumed_streams == ()
        assert b"".join(store.iter_completed_output(definition, "arrays")) == actual["arrays"]
        before = snapshot(plane)
        # The worker's creating parent has retired. Cold native-store recovery
        # authenticates existing custody without reopening a live executor.
        fresh_plane = ExternalArtifactPlane(plane.root, validators=plane.validators)
        fresh_contacts = ExternalNativeEffectContactStore(plane=fresh_plane, execution_plan=parent.execution_plan,
            visibility_ceiling=Visibility.PROSPECTIVE, outcome_access=Access.EVALUATION_SEALED)
        reader = ExternalNativeSubworkStore(plane=fresh_plane, parent_contacts=fresh_contacts, parent_contact=parent)
        assert not fresh_contacts.is_live_creator(parent)
        assert reader.read_roster(parent, definition.roster_id).subworks == (definition.identity,)
        assert reader.read_definition(definition.identity) == definition
        assert reader.recover(definition) == completed
        assert b"".join(reader.iter_completed_output(definition, "arrays")) == actual["arrays"]
        assert snapshot(plane) == before
        score = invoke(case, plane, fixture, cpu, score=(product, actual["arrays"]))
        try:
            scored = lifecycle.LocalProcessExecutor(scratch_root=_matrix_plane(path / "score-scratch").root).execute(
                score.runner, score.context, timeout_seconds=None, prepared_contract=score.contract,
                provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,))
            readout = decode_canonical_bytes(payloads(scored)["product"], MatrixPreparedResponseReadout, maximum_bytes=None)
            # The authored zero origin leaves the slow-mode cutoff, radial
            # direction and native matrix spectrum unresolved. Keep that
            # negative result alongside the complete finite native census.
            assert readout.numerical_pass and readout.disposition == "PARTIAL"
            assert len(readout.controls) == 48 and len(readout.cells) == 240
            assert all(row.disposition == "SATISFIED" for row in readout.controls)
            assert all(len(row.actual_odd_responses) == 48 for row in readout.cells)
            assert sum(row.denominator_steps for row in readout.controls) == 24 * 128 + 24 * 256
        finally:
            close(score)
        adverse = invoke(case, plane, fixture, cpu, damage="history-bytes")
        try:
            refused = lifecycle.LocalProcessExecutor(scratch_root=_matrix_plane(path / "adverse-scratch").root).preflight(
                adverse.runner, adverse.context, prepared_contract=adverse.contract,
                provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,), native_work_preparer=owner.prepare_native_work)
            assert not refused.ready and refused.mismatches
            assert contacts.read(adverse.context.run_id, adverse.context.task_id) == parent
            assert snapshot(plane) != before  # adverse inputs are retained; native receipt stays exact
            assert store.recover(definition) == completed
        finally:
            close(adverse)
        used = tuple(value for panel in fixture.config.panels for value in panel.streams if value.purpose.startswith("autonomous"))
        return {"root_id": source.root.root.root_id, "independent_group_id": source.root.root.independent_group_id,
            "source_id": source.source_id, "source_sha256": source.fingerprint(), "cpu_affinity": [cpu],
            "native_definition_sha256": definition.fingerprint(), "completion_sha256": completed.completion.fingerprint(),
            "native_receipt_sha256": completed.receipt.fingerprint(), "archive_sha256": sha256(actual["arrays"]).hexdigest(),
            "response_operation": definition.operation_id, "response_version": selected.runner.manifest.capability_version,
            "score_version": score.runner.manifest.capability_version, "score_disposition": readout.disposition,
            "branch_count": len(product.branch_ids), "cell_count": len(readout.cells), "control_count": len(readout.controls),
            "ready_then_stop_without_parent_contact": True, "changed_history_child_stopped": True,
            "cold_native_store_recovery_exact_bytes_and_custody": True,
            "consumed": [{"purpose": value.purpose, "seed_sha256": value.digest_sha256,
                "effective_seed": value.effective_seed} for value in used]}
    finally:
        close(selected)


def physical_source_census(programme, sources):
    return tuple({"source_id": source.source_id, "root_id": source.root.root.root_id,
        "independent_group_id": source.root.root.independent_group_id,
        "declared_coordinate": source.original.coordinate.to_document(), "recipe": source.recipe.to_document(),
        "prefix_scope": "AUTHORED_ALL_ZERO_PHASE_SPACE_NO_NATIVE_PREPARATION_OR_PREFIX_DRAW",
        "authored_prefix_primary_interval": [0, source.total_ticks],
        "authored_prefix_fine_interval": [0, 2 * source.total_ticks],
        "native_future_primary_interval": [source.total_ticks, source.total_ticks + programme.assay.horizon_steps[-1]],
        "native_future_fine_interval": [2 * source.total_ticks, 2 * (source.total_ticks + programme.assay.horizon_steps[-1])],
        "horizons": programme.assay.horizon_steps} for source in sources)


@pytest.mark.native
def test_e6_actual_response3_four_core_ready_stop_native_score2_and_recovery(tmp_path, monkeypatch):
    assert tmp_path.is_relative_to(Path("/media/chevre/EL/empirical-lawhood")), "all control outputs must be on EL"
    for name, value in selected_worker_environment():
        monkeypatch.setenv(name, value)
    disclosed = fixture_case()
    with threadpool_limits(limits=1):
        provenance = capture_numerical_provenance(project_root=ROOT)
        require_executing_target_source(ROOT)
        case = bind_current_source(disclosed, provenance)
        cores, sources = physical_cores(), tuple(source for _, source in case.programme.sources.source_arms())
        assert len(sources) == len(cores) == 4
        paths = tuple(tmp_path / ("root-" + str(index)) for index in range(4))
        for path in paths:
            path.mkdir()
        declared = {value.effective_seed for source in sources for value in source.root.streams}
        declared.update(value.effective_seed for _, panels in case.programme.panels for panel in panels for value in panel.streams)
        physical_sources = physical_source_census(case.programme, sources)
        (tmp_path / "e6-native-control-reservations.json").write_text(json.dumps({
            "schema": "exposed-e6-planned-software-native-use.v1",
            "scope": "Conservative exclusions for every planned software operand; actual use remains in native receipts even if this control fails.",
            "observed_git_head": provenance.observed_git_head, "code_sources_sha256": provenance.code_sources_sha256,
            "physical_source_census": physical_sources,
            "reserved_or_excluded_group_ids": sorted(source.root.root.independent_group_id for source in sources),
            "reserved_or_excluded_effective_seeds": sorted(declared)}, indent=2, sort_keys=True) + "\n")
        with ThreadPoolExecutor(max_workers=4) as pool:
            events = tuple(pool.map(lambda args: execute_one(case, *args), zip(sources, cores, paths, strict=True)))
        used = {value["effective_seed"] for row in events for value in row["consumed"]}
        report = {"schema": "exposed-e6-response3-software-native-use.v1",
            "scope": "Authored disclosed original-package/prefix/frame/feature premises; actual complete futures only; no scientific qualification or public entry.",
            "observed_git_head": provenance.observed_git_head, "observed_checkout_clean": provenance.observed_checkout_clean,
            "code_sources_sha256": provenance.code_sources_sha256, "dependency_lock_sha256": provenance.dependency_lock_sha256,
            "test_source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(), "events": events,
            "physical_source_census": physical_sources,
            "actual_acquired_group_ids": sorted(row["independent_group_id"] for row in events),
            "actual_consumed_effective_seeds": sorted(used), "reserved_or_excluded_group_ids": [],
            "reserved_or_excluded_effective_seeds": sorted(declared - used)}
        (tmp_path / "e6-native-control-exposures.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
