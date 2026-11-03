# SPDX-License-Identifier: MPL-2.0
"""Exposed retained-history/software checks; zero native entry or numerical qualification."""

from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace as N
import pytest
from empirical_lawhood.adapters.methods.battery_diagnostic_obstruction import (
    contracts as c,
    science as s,
)
from empirical_lawhood.adapters.methods.battery_refined_inquiry import (
    contracts as rc,
    science as rs,
    operation_bindings as ro,
    recursive_translation as rt,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.runtime.execution import WorkerInputKind
from tests.battery_obstruction_fixtures import load_retained_obstruction_source
from tests.test_battery_refined_inquiry_binding import parent
from tests.test_battery_refined_inquiry import selected as selected


@pytest.fixture(scope="module")
def source():
    return load_retained_obstruction_source()


def projected(source):
    records = s.validate_source(source)
    return c.ObstructionAssessment(
        "product.exposed-obstruction-history",
        source,
        source.prior_supply,
        records["index"].run_id,
        ObjectIdentity.from_record(records["plan"].execution_plan_id, records["plan"]),
        ObjectIdentity.from_record(
            "native-contact."
            + records["contact"].run_id
            + "."
            + records["contact"].task_id,
            records["contact"],
        ),
        ObjectIdentity.from_record(
            records["terminal"].terminal_event_id, records["terminal"]
        ),
    )


def test_complete_primary_history_keeps_unknown_executions(source):
    records = s.validate_source(source)
    history = projected(source)
    s.validate_assessment(history)
    assert history.numerical_disposition is A.UNEVALUABLE
    assert (
        history.entered_registered_native_operations == 1
        and history.selected_forecast_roster_count == 12
    )
    assert (
        history.returned_materialized_trace_rows == 0
        and history.actual_forecast_completions is None
    )
    assert (
        history.actual_forecast_provider_entries is None
        and history.actual_charging_subcalls is None
    )
    assert len(source.complete_custody) == 475 and len(source.input_manifests) == 3
    assert records["terminal"].completed_task_ids == ()


@pytest.mark.parametrize(
    "field",
    [
        "actual_forecast_provider_entries",
        "actual_forecast_completions",
        "actual_charging_subcalls",
        "actual_initial_soc_soh_subcalls",
    ],
)
def test_unknown_cannot_be_retyped_zero_or_complete(source, field):
    with pytest.raises(ValueError, match="absent ledger"):
        replace(projected(source), **{field: 0})


def test_missing_primary_records_or_full_inputs_refuse(source):
    with pytest.raises(ValueError):
        replace(source, records=source.records[:-1])
    for change in (
        {"input_manifests": source.input_manifests[:-1]},
        {"complete_custody": source.complete_custody[1:]},
    ):
        with pytest.raises(ValueError):
            s.validate_source(replace(source, **change))


@pytest.mark.parametrize("input_index", range(3))
@pytest.mark.parametrize("damage", ("storage-root", "publication"))
def test_each_typed_native_input_keeps_exact_original_manifest_sidecar(source, input_index, damage):
    manifest = source.input_manifests[input_index]
    raw = manifest.canonical_bytes()
    sidecar = next(row for row in source.complete_custody
        if row.relative_path == manifest.materialization.relative_path + ".manifest.json")
    assert (sidecar.size_bytes, sidecar.sha256) == (len(raw), sha256(raw).hexdigest())
    assert manifest.publication is not None
    changed = (replace(manifest, publication=None) if damage == "publication" else
        replace(manifest, publication=None, materialization=replace(manifest.materialization,
            storage_root_id="storage.unselected-rebound-original")))
    assert changed.materialization.physical_sha256 == manifest.materialization.physical_sha256
    assert changed.logical == manifest.logical
    with pytest.raises(ValueError, match="original sidecar bytes"):
        s.validate_source(replace(source, input_manifests=tuple(changed if index == input_index else row
            for index, row in enumerate(source.input_manifests))))


@pytest.mark.parametrize("damage", ("missing", "size", "digest"))
def test_native_input_sidecar_must_have_exact_original_custody_identity(source, damage):
    relative = source.input_manifests[0].materialization.relative_path + ".manifest.json"
    sidecar = next(row for row in source.complete_custody if row.relative_path == relative)
    changed = replace(sidecar, **({"size_bytes": sidecar.size_bytes + 1} if damage == "size"
        else {"sha256": "f" * 64}))
    custody = tuple(changed if row == sidecar else row for row in source.complete_custody)
    if damage == "missing":
        custody = tuple(row for row in custody if row.relative_path != relative)
    with pytest.raises(ValueError, match="original sidecar bytes"):
        s.validate_source(replace(source, complete_custody=custody))


def test_substituted_plan_contact_terminal_and_cost_fail_closed(source):
    for role in ("contact", "event", "plan", "terminal"):
        row = next(r for r in source.records if r.role == role)
        changed = replace(row, raw_utf8=row.raw_utf8 + " ")
        with pytest.raises(ValueError, match="census"):
            s.validate_source(
                replace(
                    source,
                    records=tuple(changed if r == row else r for r in source.records),
                )
            )
    import json

    cost = json.loads(source.invocation_cost_raw_utf8)
    cost["native_contacts"] = 0
    with pytest.raises(ValueError, match="cost census"):
        s.validate_source(replace(source, invocation_cost_raw_utf8=json.dumps(cost)))


def test_forged_obstruction_projection_and_numerical_adequacy_refuse(source):
    history = projected(source)
    with pytest.raises(ValueError):
        replace(history, numerical_disposition=A.SATISFIED)
    with pytest.raises(ValueError):
        s.validate_assessment(replace(history, execution_plan=source.prior_supply))


@pytest.mark.parametrize("count", (45, 54))
def test_explicit_alternative_history_preserves_full_roster_and_gates(selected, source, count):
    old_source, old_policy = selected
    history = projected(source)
    selection = replace(old_policy.selection, diagnostic=c.identity(history))
    if count == 54:
        from decimal import Decimal as D
        tighter = replace(next(v for v in selection.views if v.view_id == "dfn-refined"),
                          view_id="dfn-tolerance", rtol=D("1e-10"), atol=D("1e-11"))
        selection = replace(selection, views=tuple(sorted((*selection.views, tighter), key=lambda v:v.view_id)), tolerance_probe=True)
    policy = replace(
        old_policy,
        diagnostic=selection.diagnostic,
        protocol_sha256=selection.fingerprint(),
        views=selection.views,
        tolerance_probe=selection.tolerance_probe,
    )
    new_source = replace(
        old_source,
        diagnostic=selection.diagnostic,
        policy=rc.identity(policy),
        protocol_sha256=selection.fingerprint(),
    )
    rs.validate_source_policy(
        new_source,
        policy,
        diagnostic=history,
        protocol_bytes=selection.canonical_bytes(),
    )
    admission = ro.source_policy_admission(new_source, policy, selection, history)
    assert (
        admission.numerical_adequacy == "NOT_ASSESSED"
        and admission.scientific_authority == "NONE"
    )
    draft = rt.qualification_draft(
        history, new_source, policy, selection, parent=parent(history)
    )
    assert tuple(row.node_id for row in draft.operations) == tuple(
        "battery-refined-inquiry." + r
        for r in (
            f"acquire-obstruction-{count}",
            f"qualify-obstruction-{count}",
            "validate-obstruction-policy",
        )
    )
    assert (
        "unknown" in draft.requirements[0].condition
        and "No DiagnosticResult" in draft.requirements[0].condition
    )
    from empirical_lawhood.runtime.capabilities import CapabilityRegistry
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave

    compiled = compile_recursive_wave(
        draft=draft,
        registrations=ro.operation_registrations(),
        registry=CapabilityRegistry(
            "registry.exposed-obstruction", ro.operation_manifests()
        ),
        implementation_commit="1" * 40,
        output_codecs=ro.output_codecs(),
    )
    acquire = next(
        t
        for t in compiled.execution_plan.tasks
        if t.task_id.endswith(f"acquire-obstruction-{count}")
    )
    assert len(acquire.outputs) == count
    native_config = decode_canonical_bytes(
        next(
            r.config_payload.encode()
            for r in draft.operations
            if r.node_id == acquire.task_id
        ),
        ro.RefinedOperationConfig,
        maximum_bytes=None,
    )
    assert len(ro.native_effect_slot_ids(native_config)) == count
    gate = next(
        r for r in draft.operations if r.node_id.endswith("validate-obstruction-policy")
    )
    config = decode_canonical_bytes(
        gate.config_payload.encode(), ro.RefinedOperationConfig, maximum_bytes=None
    )
    with pytest.raises(ValueError, match="absent result"):
        replace(
            config,
            config_id="config.battery-refined-inquiry.validate-policy",
            operation="validate-policy",
        )
    rows = (config, history, new_source, policy, selection)
    ports = tuple(
        N(
            payload_schema=r.SCHEMA,
            kind=WorkerInputKind.EXTERNAL,
            media_type="application/json",
            outcome_access=__import__(
                "empirical_lawhood.kernel.evidence", fromlist=["OutcomeAccess"]
            ).OutcomeAccess.DEVELOPMENT_VISIBLE,
            visibility_ceiling=__import__(
                "empirical_lawhood.kernel.evidence", fromlist=["VisibilityCeiling"]
            ).VisibilityCeiling.DEVELOPMENT_ONLY,
            size_bytes=len(r.canonical_bytes()),
            read=r.canonical_bytes,
            close=lambda: None,
            artifact_id=config.config_id
            if r is config
            else c.identity(r).object_id
            if r is history
            else ro.record_identity(r).object_id,
        )
        for r in rows
    )
    from empirical_lawhood.runtime.artifacts import ArtifactProfile

    runner = ro.RefinedRunner("validate-obstruction-policy")
    context = N(
        task_id=gate.node_id,
        permissions=runner.manifest.permissions,
        resource_budget=ro.BUDGET,
        outcome_access=ports[0].outcome_access,
        input_ports=ports,
        config=N(
            artifact_id=config.config_id,
            config_id=config.config_id,
            content_sha256=config.fingerprint(),
        ),
        dependency_receipts=(),
        output_ports=(
            N(
                output_id=gate.node_id + ".admission",
                payload_schema=ro.SourcePolicyAdmission.SCHEMA,
                profile=ArtifactProfile.CANONICAL_JSON,
                media_type="application/json",
            ),
        ),
    )
    result = runner.execute(context)
    assert (
        decode_canonical_bytes(
            result.outputs[0].payload, ro.SourcePolicyAdmission, maximum_bytes=None
        )
        == admission
    )


@pytest.mark.parametrize("damage", ("missing-receipt", "external-gate", "old-result-gate", "changed-history"))
def test_alternate_native_gate_refuses_before_acquisition(selected, source, monkeypatch, damage):
    from tests.test_battery_refined_inquiry_binding import context, Port
    from empirical_lawhood.adapters.methods.battery_refined_inquiry import native
    from empirical_lawhood.runtime.execution import DependencyReceiptBinding
    old_source, old_policy = selected
    history = projected(source)
    selection = replace(old_policy.selection, diagnostic=c.identity(history))
    policy = replace(old_policy, diagnostic=selection.diagnostic, protocol_sha256=selection.fingerprint())
    new_source = replace(old_source, diagnostic=selection.diagnostic, policy=rc.identity(policy), protocol_sha256=policy.protocol_sha256)
    stock = N(source=new_source, policy=policy, selection=selection, diagnostic=history)
    ctx = context(stock, "acquire-obstruction-45")
    gate = ro.source_policy_admission(new_source, policy, selection, history)
    if damage == "changed-history":
        gate = replace(gate, diagnostic=replace(gate.diagnostic, object_fingerprint="c"*64))
    producer = ro.NAMESPACE + (".validate-policy" if damage == "old-result-gate" else ".validate-obstruction-policy")
    port = Port(f"artifact.{ctx.run_id}.{producer}.admission", gate,
                WorkerInputKind.EXTERNAL if damage == "external-gate" else WorkerInputKind.DEPENDENCY)
    ctx.input_ports = (*ctx.input_ports[:-1], port)
    ctx.dependency_receipts = () if damage == "missing-receipt" else (DependencyReceiptBinding(
        "receipt.exposed-obstruction-gate", producer, (port.materialization_id,)),)
    monkeypatch.setattr(native, "acquire", lambda *_:pytest.fail("invalid alternate history entered native"))
    with pytest.raises(ValueError, match="receipt-backed internal source gate"):
        ro.RefinedRunner("acquire-obstruction-45").execute(ctx)
    assert all(p.closed for p in ctx.input_ports)


@pytest.mark.parametrize("count", (45, 54))
def test_alternate_history_real_gate_and_reducer_scheduler(selected, source, tmp_path, monkeypatch, count):
    """Exposed operational history+synthetic traces, actual PURE runners and receipts.

    No native attempt or numerical scientific qualification is performed here.
    """
    from tests.test_battery_refined_inquiry_binding import test_real_pure_reducer_shared_scheduler_full_receipts_and_no_native as exercise
    old_source, old_policy = selected
    history = projected(source)
    selection = replace(old_policy.selection, diagnostic=c.identity(history))
    policy = replace(old_policy, diagnostic=selection.diagnostic, protocol_sha256=selection.fingerprint())
    new_source = replace(old_source, diagnostic=selection.diagnostic, policy=rc.identity(policy), protocol_sha256=policy.protocol_sha256)
    stock = N(source=new_source, policy=policy, selection=selection, diagnostic=history)
    exercise(stock,tmp_path,monkeypatch,count)
