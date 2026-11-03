# SPDX-License-Identifier: MPL-2.0
"""Exposed software stocks and PURE reductions; no native acquisition/qualification."""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
from io import BytesIO
import json
import subprocess
import sys
from types import SimpleNamespace as N

import pytest

from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic import science as diagnosis
from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic.contracts import DiagnosticResult
from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import scope as original_scope
from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c, native, science
from empirical_lawhood.adapters.methods.battery_refined_inquiry import operation_bindings as owner
from empirical_lawhood.adapters.methods.battery_refined_inquiry.executable_binding import EXECUTABLE_BINDING_FACTORIES
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A, ContributionRole
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.scientific_contributions import ContributionManifest, ContributionProduct
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityRegistry
from empirical_lawhood.runtime.execution import DependencyReceiptBinding, RunnerResult, TaskOutputPayload, WorkerInputKind, WorkerOutputPort
from tests.test_battery_dfn_precision_diagnostic import config_rows, exposed as diagnostic_trace
from tests.test_battery_refined_inquiry import selected as selected, table


@pytest.fixture
def stock(selected):
    traces = tuple(diagnostic_trace(config) for config in config_rows())
    traces = (replace(traces[0], disposition="TECHNICAL_FAILURE", error_type="ExposedFailure",
                      error_message="exposed software fixture"), *traces[1:])
    diagnostic = DiagnosticResult("product.battery-dfn-precision-diagnostic", traces[0].config.source,
        traces[0].config.prior_supply, traces, tuple(diagnosis.check_trace(t) for t in traces),
        diagnosis.comparisons(traces), A.UNEVALUABLE)
    source, policy = selected
    selection = replace(policy.selection, diagnostic=c.identity(diagnostic))
    policy = replace(policy, diagnostic=selection.diagnostic, protocol_sha256=selection.fingerprint())
    source = replace(source, diagnostic=selection.diagnostic, policy=c.identity(policy), protocol_sha256=policy.protocol_sha256)
    return N(source=source, policy=policy, selection=selection, diagnostic=diagnostic)


def with_tolerance(stock):
    tighter = replace(next(v for v in stock.policy.views if v.view_id == "dfn-refined"),
        view_id="dfn-tolerance", rtol=D("1e-10"), atol=D("1e-11"))
    selection = replace(stock.selection, views=tuple(sorted((*stock.selection.views, tighter), key=lambda v: v.view_id)), tolerance_probe=True)
    policy = c.NumericalPolicy(selection.policy_id, selection.diagnostic, selection.fingerprint(), selection.views,
        selection.development_preparations, selection.later_preparations, True)
    source = replace(stock.source, policy=c.identity(policy), protocol_sha256=policy.protocol_sha256)
    return N(source=source, policy=policy, selection=selection, diagnostic=stock.diagnostic)


def config(stock, operation):
    return owner.RefinedOperationConfig("config." + owner.NAMESPACE + "." + operation, operation,
        stock.source, stock.policy, stock.selection, c.identity(stock.diagnostic))


def parent(diagnostic):
    """Unsigned exposed parent metadata; never real scientific admission evidence."""
    receipt = ObjectIdentity("receipt.exposed-diagnostic", "empirical-lawhood/runtime/task-receipt", "1.0.0", "b" * 64)
    product = ContributionProduct("product.exposed-diagnostic.analysis", c.identity(diagnostic),
        ArtifactIdentity("artifact.exposed-diagnostic", "scientific-product", diagnostic.SCHEMA, diagnostic.fingerprint(),
                         owner.MEDIA, len(diagnostic.canonical_bytes())), receipt, ContributionRole.RETAINED_ANALYSIS_INPUT,
        EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)
    return ContributionManifest("contribution.exposed-diagnostic", owner.QUESTION, "Exposed software metadata only.",
        original_scope(diagnostic.source.original),
        (product,), (c.identity(diagnostic),), (), ())


def test_cold_all_installed_plus_new_factory_runners_have_manifests_and_no_pybamm():
    probe = """
import importlib.abc,json,sys
class RefuseNative(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0]=='pybamm': raise AssertionError('cold discovery imports PyBaMM')
sys.meta_path.insert(0,RefuseNative())
from empirical_lawhood.api import recursive_operations as api
from empirical_lawhood.adapters.methods.battery_refined_inquiry.executable_binding import EXECUTABLE_BINDING_FACTORIES
from empirical_lawhood.adapters.methods.battery_refined_inquiry.extension_bundle import EXTENSION_BUNDLE_CONTRIBUTION
factories={x.binding.binding_id:x for x in api.operation_factories()}
_,registry,_=api.operation_catalog()
assert all(factories[x.binding.binding_id] is x for x in EXECUTABLE_BINDING_FACTORIES)
runners=tuple(x.runner_factory() for x in EXECUTABLE_BINDING_FACTORIES)
assert tuple(x.manifest for x in runners)==tuple(x.manifest for x in EXECUTABLE_BINDING_FACTORIES)
assert all(callable(x.execute) for x in runners)
assert len(EXECUTABLE_BINDING_FACTORIES)==30
assert tuple(x.manifest for x in EXECUTABLE_BINDING_FACTORIES)==EXTENSION_BUNDLE_CONTRIBUTION.capability_manifests
assert all(x.next_wave_builder is not None for x in EXECUTABLE_BINDING_FACTORIES)
assert 'pybamm' not in sys.modules
print(json.dumps({'count':len(registry.capabilities),'new_count':len(runners)}))
"""
    result = subprocess.run([sys.executable, "-c", probe], check=True, capture_output=True, text=True)
    census = json.loads(result.stdout)
    assert census["count"] >= census["new_count"] == 30


def test_all_factories_delegate_exact_successor_operands_to_owner(monkeypatch):
    from empirical_lawhood.adapters.methods.battery_refined_inquiry import recursive_translation as drafts
    operands = (object(), object(), object())
    result = object()
    calls = []
    def callback(*values):
        calls.append(values)
        return result
    monkeypatch.setattr(drafts, "next_wave_builder", callback)
    for factory in EXECUTABLE_BINDING_FACTORIES:
        assert factory.next_wave_builder(*operands) is result
    assert calls == [operands] * 30


def test_selection_labels_are_not_new_native_effects_and_complete_rosters_are_fixed(stock):
    original = config(stock, "acquire-45")
    slots = owner.native_effect_slot_ids(original)
    assert len(slots) == len(set(slots)) == 45
    selection = replace(stock.selection, policy_id="policy.relabelled")
    policy = replace(stock.policy, policy_id=selection.policy_id, protocol_sha256=selection.fingerprint())
    source = replace(stock.source, source_id="source.relabelled", policy=c.identity(policy), protocol_sha256=policy.protocol_sha256)
    changed = owner.RefinedOperationConfig(original.config_id, original.operation, source, policy, selection, c.identity(stock.diagnostic))
    assert owner.native_effect_slot_ids(changed) == slots
    with pytest.raises(ValueError, match="complete45/54"):
        config(stock, "acquire-54")
    expanded = config(with_tolerance(stock), "acquire-54")
    assert len(owner.native_effect_slot_ids(expanded)) == 54
    assert set(slots).issubset(owner.native_effect_slot_ids(expanded))
    assert tuple(name for name, _ in owner.operation_outputs("acquire-54")) == owner.trace_ports(54)


def test_source_gate_retains_negative_history_without_adequacy_or_authority(stock):
    gate = owner.source_policy_admission(stock.source, stock.policy, stock.selection, stock.diagnostic)
    assert stock.diagnostic.disposition is A.UNEVALUABLE
    assert gate.numerical_adequacy == "NOT_ASSESSED" and gate.scientific_authority == "NONE"
    assert gate.diagnostic == c.identity(stock.diagnostic)
    for fields in ({"numerical_adequacy": "SATISFIED"}, {"scientific_authority": "QUALIFIED"}):
        with pytest.raises(ValueError, match="cannot grant"):
            replace(gate, **fields)
    with pytest.raises(ValueError, match="actual authenticated diagnostic"):
        owner.source_policy_admission(stock.source, stock.policy, stock.selection, None)


class Port:
    def __init__(self, artifact_id, record, kind):
        self.artifact_id = artifact_id
        self.materialization_id = "materialization." + artifact_id
        self.payload_schema = record.SCHEMA
        self.media_type = owner.MEDIA
        self.outcome_access = OutcomeAccess.DEVELOPMENT_VISIBLE
        self.visibility_ceiling = VisibilityCeiling.DEVELOPMENT_ONLY
        self.kind = kind
        self.raw = record.canonical_bytes()
        self.size_bytes = len(self.raw)
        self.reader = BytesIO(self.raw)
        self.closed = False

    def read(self):
        return self.reader.read()

    def close(self):
        self.closed = True
        self.reader.close()


def context(stock, operation, *, gate_kind=WorkerInputKind.DEPENDENCY, retained_gate=None, receipt=True):
    selected = config(stock, operation)
    run_id = "run.exposed-refined"
    node = owner.NAMESPACE + "." + operation
    ports = [Port(selected.config_id, selected, WorkerInputKind.EXTERNAL)]
    ports += [Port(owner.record_identity(record).object_id, record, WorkerInputKind.EXTERNAL)
              for record in (stock.source, stock.policy, stock.selection, stock.diagnostic)]
    gate = owner.source_policy_admission(stock.source, stock.policy, stock.selection, stock.diagnostic)
    gate_port = Port(f"artifact.{run_id}.{owner.NAMESPACE}.validate-policy.admission", retained_gate or gate, gate_kind)
    ports.append(gate_port)
    dependencies = (DependencyReceiptBinding("receipt.exposed-gate", owner.NAMESPACE + ".validate-policy",
                     (gate_port.materialization_id,)),) if receipt else ()
    return N(task_id=node, run_id=run_id, input_ports=tuple(ports), permissions=owner.RefinedRunner(operation).manifest.permissions,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, resource_budget=owner.BUDGET, dependency_receipts=dependencies,
        config=N(artifact_id=selected.config_id, config_id=selected.config_id, content_sha256=selected.fingerprint()),
        output_ports=tuple(WorkerOutputPort(node + "." + name, record.SCHEMA, ArtifactProfile.CANONICAL_JSON, owner.MEDIA)
                           for name, record in owner.operation_outputs(operation)))


@pytest.mark.parametrize("damage", ("external-gate", "missing-receipt", "swapped-gate"))
def test_native_runner_refuses_unproven_gate_before_any_acquisition(stock, monkeypatch, damage):
    def forbidden(*args, **kwargs):
        raise AssertionError("refused gate entered native acquisition")
    monkeypatch.setattr(native, "acquire", forbidden)
    options = {"gate_kind": WorkerInputKind.EXTERNAL} if damage == "external-gate" else {"receipt": False} if damage == "missing-receipt" else {
        "retained_gate": replace(owner.source_policy_admission(stock.source, stock.policy, stock.selection, stock.diagnostic),
            source=replace(c.identity(stock.source), object_fingerprint="c" * 64))}
    ctx = context(stock, "acquire-45", **options)
    with pytest.raises(ValueError, match="receipt-backed internal source gate"):
        owner.RefinedRunner("acquire-45").execute(ctx)
    assert all(port.closed for port in ctx.input_ports)


def test_native_output_contract_refuses_before_provider_entry(stock, monkeypatch):
    monkeypatch.setattr(native, "acquire", lambda *_: pytest.fail("bad output census entered native"))
    ctx = context(stock, "acquire-45")
    ctx.output_ports = ctx.output_ports[:-1]
    with pytest.raises(ValueError, match="complete canonical output"):
        owner.RefinedRunner("acquire-45").execute(ctx)


@pytest.mark.parametrize("damage", ("missing-trace", "swapped-config", "wrong-producing-receipt"))
def test_pure_reducer_rejects_incomplete_or_substituted_raw_dependencies(stock, monkeypatch, damage):
    ctx = context(stock, "qualify-45")
    producer = owner.NAMESPACE + ".acquire-45"
    traces = table((stock.source, stock.policy))
    ports = [Port(f"artifact.{ctx.run_id}.{producer}.{name}", trace, WorkerInputKind.DEPENDENCY)
             for name, trace in zip(owner.trace_ports(45), traces, strict=True)]
    if damage == "missing-trace":
        ports.pop()
    elif damage == "swapped-config":
        ports[0] = Port(ports[0].artifact_id, traces[1], WorkerInputKind.DEPENDENCY)
    ctx.input_ports = (*ctx.input_ports, *ports)
    ctx.dependency_receipts = (*ctx.dependency_receipts, DependencyReceiptBinding("receipt.exposed-traces",
        producer if damage != "wrong-producing-receipt" else "different.producer",
        tuple(sorted(port.materialization_id for port in ports))))
    monkeypatch.setattr(science, "qualify", lambda *_: pytest.fail("invalid raw dependency reached independent reduction"))
    with pytest.raises(ValueError, match="input/access/resource|trace config/ordinal/producing receipt"):
        owner.RefinedRunner("qualify-45").execute(ctx)
    assert all(port.closed for port in ctx.input_ports)


def compile_stock(stock):
    from empirical_lawhood.adapters.methods.battery_refined_inquiry.recursive_translation import qualification_draft
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
    draft = qualification_draft(stock.diagnostic, stock.source, stock.policy, stock.selection, parent=parent(stock.diagnostic))
    registry = CapabilityRegistry("registry.exposed-refined", tuple(sorted(owner.operation_manifests(), key=lambda x: x.registry_id)))
    compiled = compile_recursive_wave(draft=draft, registrations=owner.operation_registrations(), registry=registry,
        implementation_commit="1" * 40, output_codecs=owner.output_codecs())
    return draft, compiled


@pytest.mark.parametrize("count", (45, 54))
def test_compiler_preserves_source_history_gate_and_all_trace_dependency_edges(stock, count):
    stock = with_tolerance(stock) if count == 54 else stock
    draft, compiled = compile_stock(stock)
    assert compiled.execution_plan is not None and compiled.proof is not None
    tasks = {task.task_id: task for task in compiled.execution_plan.tasks}
    gate, acquire, reducer = (owner.NAMESPACE + "." + role for role in ("validate-policy", f"acquire-{count}", f"qualify-{count}"))
    assert tasks[acquire].dependency_task_ids == (gate,)
    assert tasks[reducer].dependency_task_ids == tuple(sorted((gate, acquire)))
    assert len(tasks[acquire].outputs) == count
    assert len(tuple(row for row in tasks[reducer].scientific_inputs if row.consumer_input_id != "config")) == count + 5
    configuration, = (row for row in tasks[reducer].scientific_inputs if row.consumer_input_id == "config")
    assert configuration.payload_schema == owner.RefinedOperationConfig.SCHEMA
    assert {x.logical_artifact_id for x in tasks[acquire].outputs} == {
        f"artifact.{compiled.run_plan.run_plan_id}.{acquire}.{name}" for name in owner.trace_ports(count)}
    assert sum(registration.native_effect for registration in owner.operation_registrations() if "obstruction" not in registration.selection.capability_key) == 2
    assert sum(registration.native_effect for registration in owner.operation_registrations() if "obstruction" in registration.selection.capability_key) == 2
    assert len(draft.requirements) == len(draft.connections) == 1
    assert draft.connections[0].evidence_role is ContributionRole.RETAINED_ANALYSIS_INPUT


def test_compiler_refuses_source_disguised_history_and_wrong_trace_mapping(stock):
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
    draft, compiled = compile_stock(stock)
    registry = compiled.registry
    diagnostic = next(link for link in draft.links if link.consumer_node_id.endswith("validate-policy") and link.consumer_input_id == "diagnostic")
    trace = next(link for link in draft.links if link.consumer_input_id == "trace-000")
    for old, wrong in ((diagnostic, replace(diagnostic, scientific_role="SOURCE")),
                       (trace, replace(trace, producer_output_id="trace-001"))):
        changed = replace(draft, links=tuple(wrong if link == old else link for link in draft.links))
        with pytest.raises(ValueError):
            compile_recursive_wave(draft=changed, registrations=owner.operation_registrations(), registry=registry,
                implementation_commit="1" * 40, output_codecs=owner.output_codecs())


class ExposedTraceEmitter:
    """PURE software-stock producer, explicitly not the registered native runner."""
    def __init__(self, manifest, traces):
        self.manifest, self.traces = manifest, traces

    def execute(self, ctx):
        try:
            return RunnerResult(tuple(TaskOutputPayload(port.output_id, trace.canonical_bytes())
                for port, trace in zip(ctx.output_ports, self.traces, strict=True)),
                (ReceiptCheck("exposed-software-stock-only", True, ()),))
        finally:
            for port in ctx.input_ports:
                port.close()


@pytest.mark.parametrize("count", (45, 54))
def test_real_pure_reducer_shared_scheduler_full_receipts_and_no_native(stock, tmp_path, monkeypatch, count):
    """Actual gate/reducer, PURE exposed trace emitter and authentic local receipts.

    Numerical selections and all traces are explicit software fixtures. The
    emitter has its own ANALYSIS capability; it does not impersonate a native
    execution, scientific result, authentic diagnosis or qualification campaign.
    """
    from empirical_lawhood.api.recursive_execution import _external_inputs
    from empirical_lawhood.infrastructure.execution import DirectTaskExecutor, LocalScheduler
    from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
    from empirical_lawhood.infrastructure.sql import SQLiteOperationalRepository, create_catalog_engine, upgrade_catalog
    from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
    from empirical_lawhood.infrastructure.recursive_custody import read_recursive_products
    from empirical_lawhood.adapters.methods.battery_refined_inquiry import recursive_translation as drafts
    from empirical_lawhood.kernel.status import OperationalStatus
    from empirical_lawhood.runtime.execution import ExecutionAssuranceProfile, RunnerRegistry
    from empirical_lawhood.runtime.plans import PlanLane
    from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryIndex
    from tests.runtime_platform.test_execution_scheduler import StaticExternalInputResolver
    from tests.test_recursive_public_service import _plane

    monkeypatch.setattr(native, "acquire", lambda *_: pytest.fail("PURE software fixture entered native acquisition"))
    stock = with_tolerance(stock) if count == 54 else stock
    acquire_key = owner.acquire_operation(c.identity(stock.diagnostic), count)
    qualify_key = owner.qualify_operation(c.identity(stock.diagnostic), count)
    draft, compiled = compile_stock(stock)
    traces = table((stock.source, stock.policy))
    acquire = next(task for task in compiled.execution_plan.tasks if task.task_id.endswith(acquire_key))
    original = next(m for m in owner.operation_manifests() if m.capability_key.endswith(acquire_key))
    fixture_manifest = replace(original, capability_key="testing.refined.exposed-trace-stock", kind=CapabilityKind.ANALYSIS)
    registry = CapabilityRegistry("registry.exposed-pure-refined", tuple(sorted(
        (*owner.operation_manifests(), fixture_manifest), key=lambda x: x.registry_id)))
    pure_task = replace(acquire, capability=replace(acquire.capability, capability_key=fixture_manifest.capability_key,
        kind=CapabilityKind.ANALYSIS), capability_implementation_sha256=fixture_manifest.implementation_sha256)
    plan = replace(compiled.execution_plan, registry_sha256=registry.fingerprint(), tasks=tuple(
        pure_task if task == acquire else task for task in compiled.execution_plan.tasks))
    actual = tuple(factory.runner_factory() for factory in EXECUTABLE_BINDING_FACTORIES)
    runners = RunnerRegistry(tuple(sorted((*actual, ExposedTraceEmitter(fixture_manifest, traces)), key=lambda r: r.manifest.registry_id)),
        registry_sha256=registry.fingerprint())
    assert type(runners.resolve(next(t for t in plan.tasks if t.task_id.endswith(qualify_key)))) is owner.RefinedRunner
    plane = _plane(tmp_path / "pure-refined-custody")
    payloads = {row.config_id: row.payload for row in compiled.config_inputs}
    payloads.update({name: record.canonical_bytes() for name, record in (
        ("source", stock.source), ("policy", stock.policy), ("selection", stock.selection), ("diagnostic", stock.diagnostic))})
    inputs = _external_inputs(plane=plane, plan=plan, draft=draft, payloads=payloads, read_only=False)
    run_id = compiled.run_plan.run_plan_id
    index = DevelopmentRunRecoveryIndex.from_execution_plan(plan, run_id=run_id,
        wave_id="wave.exposed-pure-refined", authority_identities=())
    engine = create_catalog_engine("sqlite+pysqlite:///:memory:")
    upgrade_catalog(engine)
    repository = SQLiteOperationalRepository(engine)
    recovery, receipts = ExternalRunRecoveryStore(plane), ExternalTaskReceiptStore(plane)
    scheduler = LocalScheduler(operational_repository=repository, artifact_writer=plane, receipt_store=receipts,
        recovery_index=index, recovery_store=recovery, runner_registry=runners, implementation_commit="1" * 40,
        external_input_resolver=StaticExternalInputResolver(inputs), executor=DirectTaskExecutor(), input_port_factory=plane,
        lane=PlanLane.DEVELOPMENT, authorized_barriers=(), assurance_profile=ExecutionAssuranceProfile.TRUSTED_LOCAL)
    try:
        result = scheduler.execute(run_id, plan)
        assert result.status is OperationalStatus.SUCCEEDED
        assert len(result.receipts) == 3
        receipt = next(row for row in result.receipts if row.task_id.endswith(qualify_key))
        assert len(receipt.output_logical_artifacts) == 2
        assert len(receipt.input_materialization_ids) == count + 6  # config + four SOURCE/HISTORY + gate + complete traces
        records = {}
        for material in receipt.output_materializations:
            raw = plane.root.resolve(material.relative_path, for_write=False).read_bytes()
            logical = next(x for x in receipt.output_logical_artifacts if x.logical_artifact_id == material.logical_artifact_id)
            records[logical.payload_schema] = decode_canonical_bytes(raw, owner.output_codecs()[logical.payload_schema], maximum_bytes=None)
        qualification, supply = records[c.Qualification.SCHEMA], records[c.Supply.SCHEMA]
        science.validate_qualification(stock.source, stock.policy, qualification, traces)
        assert supply.qualification == qualification and len(qualification.traces) == count
        assert len(qualification.comparisons) == (36 if count == 54 else 27)
        assert not any(row.whole_time_certified for row in qualification.checks)
        products = read_recursive_products(plane=plane, plan=plan, index=index, external_inputs=inputs, output_codecs=owner.output_codecs())
        by_schema = {record.SCHEMA: record for record in (stock.source, stock.policy, stock.selection, stock.diagnostic)}
        meaning_payloads = {"external-" + sha256(external.input_id.encode()).hexdigest()[:24] + ".json":
            by_schema[external.payload_schema].canonical_bytes() for external in draft.external_inputs}
        contributions = drafts.describe_contributions(draft, products)
        bindings = drafts.inquiry_evidence_projector(draft, meaning_payloads, products)
        assert len(contributions) == 1 and len(contributions[0].products) == count + 3
        exported_supply = next(row for row in contributions[0].products if row.record == c.identity(supply))
        assert exported_supply.role is ContributionRole.DESIGN_OPERAND
        assert exported_supply.producing_receipt == ObjectIdentity.from_record(receipt.receipt_id, receipt)
        assert sum(row.role is ContributionRole.RETAINED_ANALYSIS_INPUT for row in contributions[0].products) == count + 2
        assert len(bindings) == len(draft.external_inputs) + count + 3
        assert all(binding.independent_unit_ids == () for binding in bindings)
        trace_output = acquire.task_id + ".trace-000"
        trace_logical = products["receipts"][acquire.task_id].output_logical_artifacts[0].logical_artifact_id
        for damage in ("omitted-trace", "omitted-receipt", "omitted-materialization", "tampered-materialization",
                       "relocated-materialization", "changed-storage-root", "swapped-trace"):
            altered = {**products, "records": {task: dict(rows) for task, rows in products["records"].items()},
                       "receipts": dict(products["receipts"]), "outputs": dict(products["outputs"])}
            if damage == "omitted-trace":
                del altered["records"][acquire.task_id][trace_output]
            elif damage == "omitted-receipt":
                del altered["receipts"][acquire.task_id]
            elif damage == "omitted-materialization":
                del altered["outputs"][trace_logical]
            elif damage == "tampered-materialization":
                manifest = altered["outputs"][trace_logical]
                altered["outputs"][trace_logical] = replace(manifest,
                    materialization=replace(manifest.materialization, physical_sha256="d" * 64))
            elif damage == "relocated-materialization":
                manifest = altered["outputs"][trace_logical]
                altered["outputs"][trace_logical] = replace(manifest,
                    materialization=replace(manifest.materialization, relative_path="unattested/trace.json"))
            elif damage == "changed-storage-root":
                manifest = altered["outputs"][trace_logical]
                altered["outputs"][trace_logical] = replace(manifest,
                    materialization=replace(manifest.materialization, storage_root_id="storage.unattested"))
            else:
                altered["records"][acquire.task_id][trace_output] = altered["records"][acquire.task_id][acquire.task_id + ".trace-001"]
            assert altered["records"][receipt.task_id] == products["records"][receipt.task_id]
            with pytest.raises(ValueError):
                drafts.describe_contributions(draft, altered)
            with pytest.raises(ValueError):
                drafts.inquiry_evidence_projector(draft, meaning_payloads, altered)
        # A raw-byte corruption also defeats the actual receipt reader, even
        # when the separately retained compact supplier remains unchanged.
        trace_path = plane.root.resolve(products["outputs"][trace_logical].materialization.relative_path, for_write=False)
        original_bytes = trace_path.read_bytes()
        try:
            trace_path.write_bytes(b"{}")
            with pytest.raises((ValueError, RuntimeError, OSError)):
                read_recursive_products(plane=plane, plan=plan, index=index, external_inputs=inputs, output_codecs=owner.output_codecs())
        finally:
            trace_path.write_bytes(original_bytes)
        monkeypatch.setattr(owner.RefinedRunner, "execute", lambda *_: pytest.fail("retained PURE result was executed again"))
        monkeypatch.setattr(ExposedTraceEmitter, "execute", lambda *_: pytest.fail("exposed stock was emitted again"))
        assert scheduler.execute(run_id, plan).receipts == result.receipts
    finally:
        engine.dispose()
