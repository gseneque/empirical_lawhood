# SPDX-License-Identifier: MPL-2.0
"""Portable exposed graph controls; zero scientific native entry."""

from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace as N
import pytest

from empirical_lawhood.adapters.methods.battery_durable_inquiry import operation_bindings as ob, recursive_translation as rt
from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c, durable_roster as dr, prepared_qualification as pq, preparation_science as ps
from empirical_lawhood.adapters.methods.battery_refined_inquiry.preparation_contracts import PreparationProtocol
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.execution import DependencyReceiptBinding, WorkerInputKind, WorkerOutputPort
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.battery_obstruction_fixtures import load_retained_obstruction_source
from tests.test_battery_diagnostic_obstruction import projected
from tests.test_battery_durable_roster import selected54 as exposed_selection, uncertain
from tests.test_battery_refined_inquiry import exposed
from tests.test_battery_refined_inquiry_binding import parent, Port

@pytest.fixture(scope="module")
def stock():
    source, policy = exposed_selection.__wrapped__()
    history = projected(load_retained_obstruction_source())
    selection = replace(policy.selection, diagnostic=c.identity(history))
    policy = replace(policy, diagnostic=selection.diagnostic, protocol_sha256=selection.fingerprint())
    source = replace(source, diagnostic=selection.diagnostic, policy=c.identity(policy), protocol_sha256=selection.fingerprint())
    old_provenance = next(member for member in history.source.complete_custody if member.relative_path.endswith("/inputs/producing-provenance.json"))
    old = replace(uncertain(), original_contact=history.native_contact,
        original_producing_source=ObjectIdentity("numerical.producing-provenance", NumericalProducingProvenance.SCHEMA, "1.0.0", old_provenance.sha256))
    package_sources = (("src/exposed-graph.py", "a" * 64),)
    provenance = NumericalProducingProvenance('{"python":"exposed","numpy":"exposed","scipy":"exposed","system":"Linux","machine":"exposed","threadpools":[]}',
        "b" * 64, package_sources, sha256(canonical_json_bytes(package_sources)).hexdigest(), "c" * 40, False)
    roster = dr.freeze_forecast_roster(source, policy)
    protocols = tuple(PreparationProtocol("protocol.exposed." + group[0].config_id, c.identity(group[0]), c.identity(source), provenance.identity,
        "Chen2020" if group[0].model_view == "chen-spme" else "ORegan2022", "DFN" if "dfn" in group[0].model_view else "SPMe",
        group[0].numerical_view.electrode_points, group[0].numerical_view.particle_points, group[0].initial_temperature_k,
        ps.PREPARATION_SOURCE_MEMBERS) for group in dr.distinct_forecast_groups(roster))
    retained_parent = parent(history)
    draft = rt.qualification_draft(source, policy, old, provenance, protocols, parent=retained_parent)
    configs = {operation.node_id: decode_canonical_bytes(operation.config_payload.encode(), ob.DurableOperationConfig, maximum_bytes=None)
        for operation in draft.operations}
    return N(source=source, policy=policy, history=history, uncertain=old, provenance=provenance, roster=roster,
        protocols=protocols, parent=retained_parent, draft=draft, configs=configs)


def compile_stock(stock, draft=None):
    registry = CapabilityRegistry("registry.exposed-durable", tuple(sorted(ob.operation_manifests(), key=lambda row: row.registry_id)))
    return compile_recursive_wave(draft=draft or stock.draft, registrations=ob.operation_registrations(), registry=registry,
        implementation_commit="1" * 40, output_codecs=ob.output_codecs())


def test_complete_graph_has48_contacts54_summaries36_pairs_and_compact_aggregate(stock):
    compiled = compile_stock(stock)
    tasks = {task.task_id: task for task in compiled.execution_plan.tasks}
    assert len(tasks) == 140
    assert sum(".forecast." in node for node in tasks) == 48
    assert sum(".assess." in node for node in tasks) == 48
    assert sum(".reuse." in node for node in tasks) == 6
    assert sum(".compare." in node for node in tasks) == 36
    slots = tuple(slot for config in stock.configs.values() if config.operation == "forecast" for slot in ob.native_effect_slot_ids(config))
    assert len(slots) == len(set(slots)) == 48
    assert all(task.maximum_attempts == 1 for task in tasks.values())
    aggregate = tasks[ob.node_id("qualify")]
    assert len(aggregate.dependency_task_ids) == 90
    assert not any(value.payload_schema == c.Trace.SCHEMA for value in aggregate.scientific_inputs)
    assert all(len(task.dependency_task_ids) <= 4 for node, task in tasks.items() if ".compare." in node)


@pytest.mark.parametrize("damage", ("missing-forecast", "changed-pair", "source-disguised-history"))
def test_incomplete_or_misjoined_graph_refuses(stock, damage):
    draft = stock.draft
    if damage == "missing-forecast":
        removed = next(operation.node_id for operation in draft.operations if ".forecast." in operation.node_id)
        draft = replace(draft, selected_operation_ids=tuple(node for node in draft.selected_operation_ids if node != removed))
    else:
        link = next(link for link in draft.links if link.consumer_node_id == ob.node_id("compare", 0) and link.consumer_input_id == "left-trace") if damage == "changed-pair" else next(link for link in draft.links if link.consumer_input_id == "history")
        altered = replace(link, producer_output_id="actual-initial") if damage == "changed-pair" else replace(link, scientific_role="SOURCE")
        draft = replace(draft, links=tuple(altered if row == link else row for row in draft.links))
    with pytest.raises(ValueError):
        compile_stock(stock, draft)


def test_condition_reuse_preserves_original_trace_and_counts_actual_cost_once(stock):
    original = {}
    for group in dr.distinct_forecast_groups(stock.roster):
        trace = exposed(group[0])
        original[group[0].config_id] = (trace, pq.summarize_trace(trace, ps.assess_initial_preparation(trace)))
    summaries = tuple(original[stock.roster.configurations[ob.representative_index(stock.roster, i)].config_id][1]
        if ob.representative_index(stock.roster, i) == i else pq.reuse_summary(native,
            original[stock.roster.configurations[ob.representative_index(stock.roster, i)].config_id][1])
        for i, native in enumerate(stock.roster.configurations))
    rows = {c.identity(summary.configuration): summary for summary in summaries}
    comparisons = []
    from empirical_lawhood.adapters.methods.battery_refined_inquiry import science
    for left, right in stock.roster.comparison_config_pairs:
        left_trace = original[(rows[left].condition_reuse.observed_configuration if rows[left].condition_reuse else rows[left].configuration).config_id][0]
        right_trace = original[(rows[right].condition_reuse.observed_configuration if rows[right].condition_reuse else rows[right].configuration).config_id][0]
        comparisons.append(pq.comparison_summary(rows[left], rows[right], science.compare_reference(left_trace, right_trace)))
    qualification = pq.qualify_summaries(stock.source, stock.policy, summaries, tuple(comparisons))
    assert len(qualification.summaries) == 54 and len(qualification.comparisons) == 36
    assert sum(summary.native_provider_attempts for summary in summaries) == 48
    assert sum(summary.condition_reuse is not None for summary in summaries) == 6
    assert qualification.disposition is A.UNEVALUABLE and qualification.selected_model is None
    alias = next(summary for summary in summaries if summary.condition_reuse is not None)
    assert alias.trace == alias.condition_reuse.original_trace and alias.cpu_seconds == 0
    with pytest.raises(ValueError, match="double-counts"):
        replace(alias, cpu_seconds=type(alias.cpu_seconds)(1))


def test_unknown_overlap_refuses_before_provider_contact(stock, monkeypatch):
    entries = dr.entry_dispositions(stock.roster, stock.uncertain)
    index = next(i for i, entry in enumerate(entries) if entry.state == "HOLD_UNCERTAIN_PRIOR_PRIMITIVE" and ob.representative_index(stock.roster, i) == i)
    config = stock.configs[ob.node_id("forecast", index)]
    run_id = "run.exposed-durable"
    values = {"source": stock.source, "policy": stock.policy, "selection": stock.policy.selection, "history": stock.history,
        "roster": stock.roster, "uncertain-work": stock.uncertain, "producing-provenance": stock.provenance,
        "native-config": stock.roster.configurations[index], "selected-protocol": next(protocol for protocol in stock.protocols if protocol.configuration == c.identity(stock.roster.configurations[index])),
        "admission": ob.source_policy_admission(stock.source, stock.policy, stock.policy.selection, stock.history), "entry": entries[index]}
    ports = [Port(config.config_id, config, WorkerInputKind.EXTERNAL)]
    for name, (kind, artifact_id) in rt.input_sources(config).items():
        ports.append(Port(f"artifact.{run_id}.{artifact_id}" if kind == "DEPENDENCY" else artifact_id, values[name],
            WorkerInputKind.DEPENDENCY if kind == "DEPENDENCY" else WorkerInputKind.EXTERNAL))
    dependency_ports = tuple(port.materialization_id for port in ports if port.kind is WorkerInputKind.DEPENDENCY)
    runner = ob.DurableRunner("forecast")
    node = ob.node_id("forecast", index)
    context = N(run_id=run_id, task_id=node, input_ports=tuple(ports), permissions=runner.manifest.permissions,
        resource_budget=ob.BUDGET, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        config=N(artifact_id=config.config_id, config_id=config.config_id, content_sha256=config.fingerprint()),
        dependency_receipts=(DependencyReceiptBinding("receipt.exposed-gate", ob.node_id("validate"), tuple(sorted(dependency_ports))),),
        output_ports=tuple(WorkerOutputPort(node + "." + name, record.SCHEMA, ArtifactProfile.CANONICAL_JSON, ob.MEDIA)
            for name, record in ob.operation_outputs("forecast")))
    from empirical_lawhood.adapters.methods.battery_refined_inquiry import prepared_native
    calls = []
    monkeypatch.setattr(prepared_native, "acquire_prepared", lambda *args, **kwargs: calls.append(args))
    with pytest.raises(ValueError, match="automatic replay"):
        runner.execute_with_native_subwork(context, object())
    assert calls == [] and all(port.closed for port in ports)


def test_work_distinguishes_actual_reference_pairs_and_retains_complete_roster(stock):
    first, second = (rt.scientific_work(stock.draft, ob.node_id("compare", i)) for i in (0, 1))
    assert first.method != second.method and first.observation_contract != second.observation_contract
    assert stock.configs[ob.node_id("validate")].roster in first.scientific_operands


def test_cold_factory_discovery_imports_no_native_solver_or_array_library():
    import subprocess
    import sys
    probe = """
import importlib.abc,sys
class RefuseNative(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0] in {'pybamm','numpy','flint'}:
            raise AssertionError('cold descriptor imports native numerical code')
sys.meta_path.insert(0,RefuseNative())
from empirical_lawhood.adapters.methods.battery_durable_inquiry.executable_binding import EXECUTABLE_BINDING_FACTORIES
from empirical_lawhood.adapters.methods.battery_durable_inquiry.extension_bundle import EXTENSION_BUNDLE_CONTRIBUTION
assert len(EXECUTABLE_BINDING_FACTORIES)==6
assert tuple(row.manifest for row in EXECUTABLE_BINDING_FACTORIES)==EXTENSION_BUNDLE_CONTRIBUTION.capability_manifests
assert all(row.inquiry_work_projector is not None for row in EXECUTABLE_BINDING_FACTORIES)
"""
    subprocess.run([sys.executable, "-c", probe], check=True, capture_output=True, text=True)
