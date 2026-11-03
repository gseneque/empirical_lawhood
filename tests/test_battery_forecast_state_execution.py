# SPDX-License-Identifier: MPL-2.0
"""Exposed complete arrays through shared preparation and ordinary consumers.

The solver products are explicitly exposed fixtures. No native engine is
contacted, and this does not establish the later TP2 native canary acceptance.
"""

from dataclasses import replace
from hashlib import sha256

import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts
from empirical_lawhood.adapters.methods.battery_refined_inquiry import forecast_state_execution as execution
from empirical_lawhood.adapters.methods.battery_refined_inquiry import forecast_state_census as census
from empirical_lawhood.adapters.methods.battery_refined_inquiry import forecast_state_control as state
from empirical_lawhood.adapters.methods.battery_refined_inquiry import forecast_state_orchestration as orchestration
from empirical_lawhood.adapters.methods.battery_refined_inquiry import forecast_step_control as step
from empirical_lawhood.adapters.methods.battery_refined_inquiry import lossless_evidence_stream as stream
from empirical_lawhood.adapters.methods.battery_refined_inquiry.recursive_translation import _campaign
from empirical_lawhood.infrastructure.prepared_native_invocation import NativeInputPublication, prepare_native_invocation
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A, DevelopmentStudySpec
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactStreamWriteRequest
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRegistry
from empirical_lawhood.runtime.execution import TaskContext, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.runtime_platform.test_native_subwork import _plane
from tests.test_battery_forecast_state_control import selected as selected_fixture
from tests.test_battery_forecast_state_orchestration import complete_failed as complete_failed_fixture, observed_stream, port as exposed_port
from tests.test_battery_lossless_segment_integration import selected_preparation
from tests.test_battery_segmented_fidelity import prepared as prepared_fixture

complete_failed = complete_failed_fixture


@pytest.fixture(scope="module")
def original_pairs(tmp_path_factory):
    selected, prepared = selected_fixture.__wrapped__(), prepared_fixture.__wrapped__()
    prepared = selected_preparation(prepared, (selected[0], selected[1], selected[2].native_policy))
    directory = tmp_path_factory.mktemp("forecast-state-execution-originals")
    temporary_file = stream.selected_temporary_files(directory)
    left, left_payload = observed_stream(prepared, selected, directory / "left", temporary_file, horizon=60)
    results = []
    for label, damage in (("unchanged", None), ("rhs", (0, .01)), ("algebraic", (173, .01))):
        right, right_payload = observed_stream(prepared, selected, directory / label, temporary_file,
            horizon=30, changed_state=damage)
        results.append((label, left, right, left_payload, right_payload))
    return selected, tuple(results)


def prepare_pair(directory, selected, original):
    label, left, right, left_payload, right_payload = original
    control, roster = selected[2], selected[1]
    records = {"control": control, "selected-roster": roster}
    for side, observed in (("left", left), ("right", right)):
        records.update({side + "-evidence": observed.evidence, side + "-assignment": observed.assignment,
            side + "-summary": observed.summary})
    artifacts = tuple((name, "input.exposed." + name) for name, _ in execution.input_types("pair"))
    config = execution.ForecastStateOperationConfig("config.exposed.forecast-state." + label,
        "pair", control.identity, step.identity(roster, "roster_id"),
        (left.configuration, right.configuration), artifacts)
    publications = []
    references = {}
    for name, record in records.items():
        identifier = ("control_id" if name == "control" else "roster_id" if name == "selected-roster"
            else "summary_id" if name.endswith("-summary") else "evidence_id")
        identity = step.identity(record, identifier)
        publications.append(NativeInputPublication(identity.object_id, record, dict(artifacts)[name]))
        references[name] = identity
    publications.append(NativeInputPublication(config.config_id, config))
    plane = _plane(directory)
    original_streams = []
    for side, payload in (("left", left_payload), ("right", right_payload)):
        name = side + "-segments"
        lines = payload.splitlines(keepends=True)
        result = plane.write_stream(ArtifactStreamWriteRequest(dict(artifacts)[name], "inputs/" + name + ".jsonl",
            stream.LosslessEvidenceLine.SCHEMA, ArtifactProfile.JSONL_CHUNKS, "application/x-ndjson",
            "exposed.original-streams", "inputs", iter(lines), maximum_bytes=len(payload),
            maximum_chunk_bytes=max(map(len, lines)), visibility_ceiling=execution.VISIBILITY,
            parent_visibility_ceilings=(), outcome_access=execution.ACCESS))
        manifest = decode_artifact_manifest(plane.root.resolve(result.materialization.relative_path
            + ".manifest.json", for_write=False).read_bytes())
        identity = ObjectIdentity("original.exposed." + name, stream.LosslessEvidenceLine.SCHEMA,
            "1.0.0", manifest.logical.content_sha256)
        original_streams.append((identity, manifest))
        references[name] = identity
    prepared = prepare_native_invocation(plane, publications=tuple(publications),
        existing_inputs=tuple(original_streams), visibility=execution.VISIBILITY, access=execution.ACCESS)
    manifest = execution.operation_manifest("pair")
    context = TaskContext("exposed.forecast-state", "battery-forecast-state.pair.000", "exposed.forecast-state.attempt01",
        CapabilityConfigRef(config.config_id, config.SCHEMA, sha256(config.SCHEMA.encode()).hexdigest(),
            config.fingerprint(), config.config_id), prepared.input_bindings, prepared.input_ports,
        (WorkerOutputPort("battery-forecast-state.pair.000.assessment", state.ForecastStateStream.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json"),), manifest.permissions,
        execution.ACCESS, execution.BUDGET, WorkerIsolationProfile.TRUSTED_LOCAL)
    return config, context, prepared, references


@pytest.mark.parametrize("index", (0, 1, 2))
def test_actual_shared_prepared_ports_use_full_pair_and_keep_negative_suffix(original_pairs, tmp_path, index):
    selected, originals = original_pairs
    config, context, prepared, _ = prepare_pair(tmp_path / "prepared", selected, originals[index])
    runner = execution.ForecastStateRunner("pair", temporary_file=stream.selected_temporary_files(tmp_path))
    result = runner.execute(context)
    output = decode_canonical_bytes(result.outputs[0].payload, state.ForecastStateStream, maximum_bytes=None)
    assert output.disposition is (A.UNEVALUABLE if index == 0 else A.FALSIFIED)
    assert output.declared_segment_counts == (1, 1)
    assert output.original_retained_native_knots == (2, 2)
    assert output.compared_rhs_components == 173 * 31
    assert output.compared_algebraic_components == 31
    assert output.compared_derivative_components == 174 * 31
    assert {"unpaired-actual-terminal-suffix", "actual-terminal-clocks-differ"}.issubset(output.reason_codes)
    assert output.scientific_control.native_policy.comparison_budget.rtol.as_tuple().exponent == -7
    assert output.control == config.control
    assert result.checks[0].passed
    for port in prepared.input_ports:
        with pytest.raises(ValueError, match="closed"):
            port.read(0)


def test_complete_pair_graph_compiles_ten_real_ports_without_native_effects(original_pairs, tmp_path):
    selected, originals = original_pairs
    config, _, prepared, references = prepare_pair(tmp_path / "prepared-graph", selected, originals[0])
    try:
        node = "battery-forecast-state.pair.000"
        operation, external, links = execution.graph_fragment(config, node_id=node, references=references)
        scope = contracts.scope(selected[1].source)
        claim = ClaimSpec("claim.exposed.forecast-state", scope.world_id, "population.exposed.battery-state",
            "Does the complete exposed array consumer retain adverse outcomes?", "Exact fixed-budget readback",
            contracts.UNIT, None, EvidenceCeiling.NON_PROMOTABLE, execution.ACCESS, execution.VISIBILITY,
            "Exposed artificial products; no native result, supplier admission or physical qualification.",
            ("assumption.exposed.artificial-products",))
        study = DevelopmentStudySpec("study.exposed.forecast-state", claim.proposition,
            ObjectIdentity.from_record(scope.system_id, selected[1].source), scope.world_id,
            WorldKind.NUMERICAL_SIMULATOR, (contracts.UNIT,), (), (claim,),
            tuple(sorted(config.scientific_operands, key=lambda row: row.object_id)))
        draft = RecursiveStudyDraft("draft.exposed.forecast-state", study.question, _campaign(study, "exposed.forecast-state"),
            (), (), (), (operation,), external, links, (node,), development_study=study)
        manifest = execution.operation_manifest("pair")
        compiled = compile_recursive_wave(draft=draft, registrations=(execution.operation_registration("pair"),),
            registry=CapabilityRegistry("registry.exposed.forecast-state", (manifest,)), implementation_commit="3" * 40,
            output_codecs={state.ForecastStateStream.SCHEMA: state.ForecastStateStream})
        assert len(compiled.execution_plan.tasks) == 1
        task = compiled.execution_plan.tasks[0]
        assert len(tuple(row for row in task.scientific_inputs if row.consumer_input_id != "config")) == 10
        configuration, = (row for row in task.scientific_inputs if row.consumer_input_id == "config")
        assert configuration.payload_schema == type(config).SCHEMA and len(task.external_inputs) == 11
        assert task.capability.capability_key == "battery-forecast-state.pair"
        assert decode_canonical_bytes(config.canonical_bytes(), type(config), maximum_bytes=None) == config
    finally:
        prepared.close()


@pytest.mark.parametrize("damage", ("missing-port", "changed-config", "changed-output"))
def test_domain_guards_refuse_substituted_port_config_or_output_and_close(original_pairs, tmp_path, damage):
    selected, originals = original_pairs
    _, context, prepared, _ = prepare_pair(tmp_path / "prepared-adverse", selected, originals[0])
    if damage == "missing-port":
        context = replace(context, input_ports=context.input_ports[:-1], input_bindings=context.input_bindings[:-1])
    elif damage == "changed-config":
        context = replace(context, config=replace(context.config, content_sha256="f" * 64))
    else:
        context = replace(context, output_ports=(replace(context.output_ports[0], payload_schema="empirical-lawhood/exposed/substituted-output"),))
    with pytest.raises(ValueError):
        execution.ForecastStateRunner("pair", temporary_file=stream.selected_temporary_files(tmp_path)).execute(context)
    for port in context.input_ports:
        with pytest.raises(ValueError, match="closed"):
            port.read(0)
    prepared.close()


def test_graph_requires_complete_scientific_inputs_and_qualifies_no_model(original_pairs, tmp_path):
    selected, originals = original_pairs
    config, _, prepared, references = prepare_pair(tmp_path / "prepared-graph-adverse", selected, originals[0])
    try:
        with pytest.raises(ValueError, match="omits"):
            execution.graph_fragment(config, node_id="battery-forecast-state.pair.000", references=dict(references, extra=config.control))
        with pytest.raises(ValueError, match="transport"):
            replace(config, input_artifacts=config.input_artifacts[:-1])
        assert execution.operation_registration("pair").native_effect is False
        registered = execution.operation_registration("census")
        pair_port = next(row for row in registered.input_ports if row.port_id == "pair")
        assert (pair_port.minimum_count, pair_port.maximum_count) == (96, 96)
        assert len(execution.input_types("census")) == 99
        assert registered.native_effect is False
    finally:
        prepared.close()


def test_local_declaration_keeps_complete_census_and_existing_lossless_codec_without_runner(monkeypatch):
    from empirical_lawhood.adapters.methods.battery_refined_inquiry.controlled_operation_bindings import LOSSLESS_STORAGE_CODECS
    from empirical_lawhood.runtime.plans import ScientificStage

    def forbidden(*args, **kwargs):
        pytest.fail("cold local declarations constructed a runner or temporary resource")
    monkeypatch.setattr(execution, "ForecastStateRunner", forbidden)
    declarations=tuple(execution.operation_declaration(role) for role in ("pair", "census"))
    assert all(row.stage is ScientificStage.QUALIFY and not row.execution_properties.native_effect
        and row.storage_codecs==LOSSLESS_STORAGE_CODECS for row in declarations)
    pair,census_declaration=(row.registration() for row in declarations)
    port,=tuple(row for row in census_declaration.input_ports if row.port_id=="pair")
    assert port.minimum_count==port.maximum_count==96
    stream_ports=tuple(row for row in pair.input_ports if row.media_type=="application/x-ndjson")
    assert tuple(row.port_id for row in stream_ports)==("left-segments","right-segments")
    assert all(any(codec.payload_schema==row.payload_schema and codec.media_type==row.media_type
        for codec in pair.storage_codecs) for row in stream_ports)
    assert tuple(row.capability_key for row in declarations)==("battery-forecast-state.pair","battery-forecast-state.census")


def test_full96_product_ports_produce108_use_census_and_complete_graph(complete_failed, tmp_path):
    """A complete exposed failed panel is not a genuine DFN memory assessment."""
    selected = selected_fixture.__wrapped__()
    control, roster = selected[2], selected[1]
    receiver, observations, payloads = complete_failed
    stock = {row.configuration: row for row in observations}
    products = []
    for key, _ in orchestration.selected_pairs(control, roster, receiver):
        left, right = (stock[identity] for identity in key)
        products.append(orchestration.assess_pair(control, roster, left, right,
            exposed_port(payloads[left.configuration]), exposed_port(payloads[right.configuration]),
            temporary_file=stream.selected_temporary_files(tmp_path)))
    names = execution.input_types("census")
    artifacts = tuple((name, "input.exposed.census." + name) for name, _ in names)
    config = execution.ForecastStateOperationConfig("config.exposed.forecast-state.census", "census",
        control.identity, step.identity(roster, "roster_id"), (), artifacts)
    records = {"control": control, "selected-roster": roster, "receiver": receiver,
        **{"pair." + f"{index:03d}": record for index, record in enumerate(products)}}
    identities = {name: step.identity(record, "control_id" if name == "control" else "roster_id"
        if name == "selected-roster" else "product_id" if name == "receiver" else "assessment_id")
        for name, record in records.items()}
    publications = tuple(NativeInputPublication(identities[name].object_id, record, dict(artifacts)[name])
        for name, record in records.items()) + (NativeInputPublication(config.config_id, config),)
    prepared = prepare_native_invocation(_plane(tmp_path / "complete-census"), publications=publications,
        visibility=execution.VISIBILITY, access=execution.ACCESS)
    try:
        manifest = execution.operation_manifest("census")
        node = "battery-forecast-state.census"
        context = TaskContext("exposed.forecast-state", node, node + ".attempt01",
            CapabilityConfigRef(config.config_id, config.SCHEMA, sha256(config.SCHEMA.encode()).hexdigest(),
                config.fingerprint(), config.config_id), prepared.input_bindings, prepared.input_ports,
            (WorkerOutputPort(node + ".census", census.ForecastStateCensus.SCHEMA,
                ArtifactProfile.CANONICAL_JSON, "application/json"),), manifest.permissions,
            execution.ACCESS, execution.BUDGET, WorkerIsolationProfile.TRUSTED_LOCAL)
        output = execution.ForecastStateRunner("census", temporary_file=lambda: None).execute(context)
        result = decode_canonical_bytes(output.outputs[0].payload, census.ForecastStateCensus, maximum_bytes=None)
        assert result.disposition is A.UNEVALUABLE
        assert len(result.selected_uses) == 108 and len(result.conclusions) == 96
        assert sum(bool(row.equal_condition_derivations) for row in result.selected_uses) == 12
        assert receiver.selected_model is None and receiver.selected_forecast_slots == 162
        assert receiver.distinct_forecast_effects == 144
        operation, external, links = execution.graph_fragment(config, node_id=node, references=identities)
        assert len(external) == len(links) == 99
        pair_refs = {name: ("battery-forecast-state." + name, "assessment")
            for name in identities if name.startswith("pair.")}
        run_plan_id = "run.exposed.complete-state-panel"
        joined_config = replace(config, config_id=config.config_id + ".joined",
            input_artifacts=tuple((name, "artifact." + run_plan_id + "." + pair_refs[name][0] + ".assessment"
                if name in pair_refs else artifact) for name, artifact in config.input_artifacts))
        with pytest.raises(ValueError, match="compiler-owned"):
            execution.graph_fragment(config, node_id=node,
                references={name: row for name, row in identities.items() if name not in pair_refs},
                dependencies=tuple(pair_refs.items()), run_plan_id=run_plan_id)
        _, retained, joined = execution.graph_fragment(joined_config, node_id=node,
            references={name: row for name, row in identities.items() if name not in pair_refs},
            dependencies=tuple(pair_refs.items()), run_plan_id=run_plan_id)
        assert len(retained) == 3 and sum(row.producer_node_id is not None for row in joined) == 96
        scope = contracts.scope(roster.source)
        claim = ClaimSpec("claim.exposed.complete-state-census", scope.world_id, "population.exposed.battery-state",
            "Are all selected numerical comparisons retained?", "Complete adverse denominator", contracts.UNIT,
            None, EvidenceCeiling.NON_PROMOTABLE, execution.ACCESS, execution.VISIBILITY,
            "Exposed failed panel; no native result or model admission.", ("assumption.exposed.artificial-products",))
        study = DevelopmentStudySpec("study.exposed.complete-state-census", claim.proposition,
            ObjectIdentity.from_record(scope.system_id, roster.source), scope.world_id, WorldKind.NUMERICAL_SIMULATOR,
            (contracts.UNIT,), (), (claim,), tuple(sorted(config.scientific_operands, key=lambda row: row.object_id)))
        draft = RecursiveStudyDraft("draft.exposed.complete-state-census", study.question,
            _campaign(study, "exposed.complete-state-census"), (), (), (), (operation,), external, links,
            (node,), development_study=study)
        compiled = compile_recursive_wave(draft=draft, registrations=(execution.operation_registration("census"),),
            registry=CapabilityRegistry("registry.exposed.complete-state-census", (manifest,)),
            implementation_commit="3" * 40, output_codecs={census.ForecastStateCensus.SCHEMA: census.ForecastStateCensus})
        task = compiled.execution_plan.tasks[0]
        assert len(tuple(row for row in task.scientific_inputs if row.consumer_input_id != "config")) == 99
        configuration, = (row for row in task.scientific_inputs if row.consumer_input_id == "config")
        assert configuration.payload_schema == type(config).SCHEMA and len(task.external_inputs) == 100
        # The connected graph uses actual compiler-owned producer output IDs,
        # rather than accepting hand-written aliases that cannot reach a worker.
        operations, panel_externals, panel_links = [], [], []
        operands = {row.object_id: row for row in config.scientific_operands}
        for index, (key, _) in enumerate(orchestration.selected_pairs(control, roster, receiver)):
            left, right = (stock[identity] for identity in key)
            refs = {"control": control.identity, "selected-roster": step.identity(roster, "roster_id")}
            for side, observed in (("left", left), ("right", right)):
                refs.update({side + "-evidence": observed.reference.evidence,
                    side + "-assignment": observed.reference.assignment, side + "-summary": observed.reference.summary,
                    side + "-segments": ObjectIdentity("stream.exposed." + observed.configuration.object_id,
                        stream.LosslessEvidenceLine.SCHEMA, "1.0.0", sha256(payloads[observed.configuration]).hexdigest())})
            pair_node = "battery-forecast-state.pair." + f"{index:03d}"
            pair_config = execution.ForecastStateOperationConfig("config.exposed." + pair_node, "pair",
                control.identity, step.identity(roster, "roster_id"), (left.configuration, right.configuration),
                tuple((name, refs[name].object_id) for name, _ in execution.input_types("pair")))
            fragment = execution.graph_fragment(pair_config, node_id=pair_node, references=refs)
            operations.append(fragment[0])
            panel_externals.extend(fragment[1])
            panel_links.extend(fragment[2])
            operands.update((row.object_id, row) for row in pair_config.scientific_operands)
        fragment = execution.graph_fragment(joined_config, node_id=node,
            references={name: row for name, row in identities.items() if name not in pair_refs},
            dependencies=tuple(pair_refs.items()), run_plan_id=run_plan_id)
        operations.append(fragment[0])
        panel_externals.extend(fragment[1])
        panel_links.extend(fragment[2])
        panel_study = replace(study, scientific_operands=tuple(operands[key] for key in sorted(operands)))
        panel_draft = replace(draft, operations=tuple(sorted(operations, key=lambda row: row.node_id)),
            external_inputs=tuple(sorted(panel_externals, key=lambda row: row.input_id)),
            links=tuple(sorted(panel_links, key=lambda row: row.edge_id)),
            selected_operation_ids=tuple(sorted(row.node_id for row in operations)),
            development_study=panel_study)
        joined_wave = compile_recursive_wave(draft=panel_draft,
            registrations=(execution.operation_registration("pair"), execution.operation_registration("census")),
            registry=CapabilityRegistry("registry.exposed.connected-state-census",
                (manifest, execution.operation_manifest("pair"))), implementation_commit="3" * 40,
            run_plan_id=run_plan_id, output_codecs={state.ForecastStateStream.SCHEMA: state.ForecastStateStream,
                census.ForecastStateCensus.SCHEMA: census.ForecastStateCensus})
        assert len(joined_wave.execution_plan.tasks) == 97
        census_task = next(row for row in joined_wave.execution_plan.tasks if row.task_id == node)
        assert len(census_task.dependency_task_ids) == 96
        assert {row.operational_logical_artifact_id for row in census_task.scientific_inputs
            if row.consumer_input_id != "config"} == {
            artifact for _, artifact in joined_config.input_artifacts}
    finally:
        prepared.close()
