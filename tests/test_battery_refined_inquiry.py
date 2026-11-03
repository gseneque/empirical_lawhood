# SPDX-License-Identifier: MPL-2.0
"""Exposed conformance only: policy numerics and diagnostic IDs here are fixtures."""
from dataclasses import fields, replace
from decimal import Decimal as D
import json

import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c, science, native
from empirical_lawhood.adapters.methods.battery_thermal_inquiry import science as old_science
from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import BatteryInquirySource, SOURCE_MEMBERS
from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic.contracts import ADDITIONAL_SOURCE_MEMBERS
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from tests.test_battery_thermal_inquiry import _exposed_trace


@pytest.fixture
def selected():
    diagnostic = ObjectIdentity("diagnostic.software-fixture", "empirical-lawhood/battery-dfn-precision-diagnostic/result", "1.0.0", "a" * 64)
    # These settings do NOT select the pending actual scientific policy.
    views = tuple(sorted((
        c.NumericalView("chen-spme", "chen-spme", 30, 40, D("1e-5"), D("1e-7"), D("1e-8")),
        c.NumericalView("oregan-spme", "oregan-spme", 30, 40, D("1e-5"), D("1e-7"), D("1e-8")),
        c.NumericalView("dfn-primary", "oregan-dfn", 90, 120, D("1e-6"), D("1e-9"), D("1e-10")),
        c.NumericalView("dfn-band", "oregan-dfn", 90, 120, D("1e-5"), D("1e-9"), D("1e-10")),
        c.NumericalView("dfn-refined", "oregan-dfn", 180, 240, D("1e-6"), D("1e-9"), D("1e-10")),
    ), key=lambda row: row.view_id))
    declaration = c.NumericalSelection("policy.software-fixture", diagnostic, views,
        tuple((t, r) for t in c.DEVELOPMENT_TEMPERATURES for r in c.RECIPES),
        tuple((p, c.LATER_TEMPERATURES[p], c.RECIPES) for p in ("use", "reuse")), False)
    protocol = declaration.fingerprint()
    policy = c.NumericalPolicy(declaration.policy_id, diagnostic, protocol, views, declaration.development_preparations,
        declaration.later_preparations, declaration.tolerance_probe)
    source = c.RefinedSource("source.software-fixture", BatteryInquirySource(), c.identity(policy), diagnostic,
        protocol, tuple(sorted((*SOURCE_MEMBERS, *ADDITIONAL_SOURCE_MEMBERS))))
    return source, policy


def exposed(config, *, technical=False, cpu=D(1), voltage=D("4.2")):
    old = _exposed_trace(old_science.native_config(BatteryInquirySource(), "supply" if config.phase == "qualification" else config.phase,
        config.initial_temperature_k, config.recipe, "oregan-dfn"),
        magnitude=D("3.395") if config.initial_temperature_k > D("298.15") else D("1.455"),
        technical=technical, cpu=cpu, voltage=voltage)
    attempts = tuple(c.ChargingAttempt(configuration=config, **{
        field.name: config.localization_epsilon_k if field.name == "localization_epsilon_k"
        else json.dumps({"type": "IDAKLUSolver", "rtol": float(config.rtol), "atol": float(config.atol)})
        if field.name == "solver_configuration_json" else getattr(row, field.name)
        for field in fields(row)}) for row in old.charging_attempts)
    return c.Trace(**{field.name: config if field.name == "config" else attempts if field.name == "charging_attempts"
        else "trace." + config.config_id if field.name == "trace_id" else getattr(old, field.name)
        for field in fields(old)})


def table(selected, phase="qualification"):
    source, policy = selected
    return tuple(exposed(config, cpu=D(2) if config.component_view == "oregan-spme" else D(1))
                 for config in science.configurations(source, policy, phase))


def test_policy_is_explicit_full_triangle_and_optional_tolerance(selected):
    source, policy = selected
    assert len(science.configurations(source, policy)) == 45
    assert c.scope(source).instance_id == c.UNIT
    assert c.scope(source).source_config_sha256 == source.fingerprint()
    assert policy.comparison_pairs == (("dfn-band", "dfn-primary"), ("dfn-primary", "dfn-refined"), ("dfn-band", "dfn-refined"))
    with pytest.raises(ValueError, match="nine"):
        replace(policy, development_preparations=policy.development_preparations[:-1])
    with pytest.raises(ValueError, match="full recipe"):
        replace(policy, later_preparations=(policy.later_preparations[0],))
    with pytest.raises(ValueError):
        replace(policy, views=policy.views[:-1])
    with pytest.raises(ValueError, match="band"):
        replace(policy, views=tuple(replace(v, atol=D("1e-8")) if v.view_id == "dfn-band" else v for v in policy.views))
    probe = c.NumericalView("dfn-tolerance", "oregan-dfn", 180, 240, D("1e-6"), D("1e-10"), D("1e-11"))
    changed_selection = replace(policy.selection, tolerance_probe=True, views=tuple(sorted((*policy.views, probe), key=lambda v: v.view_id)))
    changed = replace(policy, tolerance_probe=True, views=changed_selection.views, protocol_sha256=changed_selection.fingerprint())
    changed_source = replace(source, policy=c.identity(changed), protocol_sha256=changed.protocol_sha256)
    assert len(science.configurations(changed_source, changed)) == 54
    with pytest.raises(ValueError, match="join"):
        science.configurations(source, changed)


def test_new_typed_factories_carry_explicit_settings_no_native(selected, monkeypatch):
    source, policy = selected
    config = science.configurations(source, policy)[0]
    calls = []
    monkeypatch.setattr(native, "acquire_with_numerics", lambda config, **kw: calls.append((config, kw)))
    native.acquire(config)
    assert calls[0][1]["electrode_points"] == config.numerical_view.electrode_points
    assert calls[0][1]["trace_factory"] is c.Trace
    assert calls[0][1]["charging_attempt_factory"].func is c.ChargingAttempt
    assert calls[0][1]["charging_attempt_factory"].keywords == {"configuration": config}
    trace = exposed(config)
    assert science.check_trace(trace).disposition is A.SATISFIED
    assert decode_canonical_bytes(trace.canonical_bytes(), c.Trace, maximum_bytes=None) == trace
    with pytest.raises(ValueError, match="digest"):
        replace(trace.charging_attempts[0], realized_end_state_sha256="b" * 64)
    with pytest.raises(ValueError, match="native clock"):
        replace(trace, times_s=(D(0), D(0)))
    with pytest.raises(ValueError, match="negative clock"):
        replace(trace.charging_attempts[0], cpu_seconds=D(-1))


def test_canonical_protocol_and_actual_diagnostic_lineage_before_native(selected, monkeypatch):
    from tests.test_battery_dfn_precision_diagnostic import config_rows, exposed as diagnostic_trace
    from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic import science as diagnostic_science
    from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic.contracts import DiagnosticResult

    traces = tuple(diagnostic_trace(config) for config in config_rows())
    # A retained unresolved diagnosis remains history; it does not assert a
    # full-roster qualification for the new numerical owner.
    traces = (replace(traces[0], disposition="TECHNICAL_FAILURE", error_type="ExposedFailure",
                      error_message="exposed fixture technical failure"), *traces[1:])
    diagnostic = DiagnosticResult("product.battery-dfn-precision-diagnostic", traces[0].config.source,
        traces[0].config.prior_supply, traces, tuple(diagnostic_science.check_trace(t) for t in traces),
        diagnostic_science.comparisons(traces), A.UNEVALUABLE)
    source, policy = selected
    declaration = replace(policy.selection, diagnostic=c.identity(diagnostic))
    policy = replace(policy, diagnostic=declaration.diagnostic, protocol_sha256=declaration.fingerprint())
    source = replace(source, diagnostic=declaration.diagnostic, policy=c.identity(policy), protocol_sha256=policy.protocol_sha256)
    science.validate_source_policy(source, policy, diagnostic=diagnostic, protocol_bytes=declaration.canonical_bytes())
    assert diagnostic.disposition is A.UNEVALUABLE
    assert decode_canonical_bytes(declaration.canonical_bytes(), c.NumericalSelection, maximum_bytes=None) == declaration
    with pytest.raises(ValueError, match="unchanged"):
        replace(declaration, scientific_gates=(D(2), *declaration.scientific_gates[1:]))
    with pytest.raises(ValueError, match="protocol"):
        replace(policy, views=tuple(replace(v, electrode_points=31) if v.view_id == "chen-spme" else v for v in policy.views))
    changed = replace(declaration, views=tuple(replace(v, electrode_points=31) if v.view_id == "chen-spme" else v for v in policy.views))
    rebuilt_policy = replace(policy, views=changed.views, protocol_sha256=changed.fingerprint())
    rebuilt_source = replace(source, policy=c.identity(rebuilt_policy), protocol_sha256=rebuilt_policy.protocol_sha256)
    with pytest.raises(ValueError, match="identity"):
        science.validate_source_policy(rebuilt_source, rebuilt_policy, diagnostic=diagnostic, protocol_bytes=declaration.canonical_bytes())
    with pytest.raises(ValueError, match="actual authenticated diagnostic"):
        science.validate_source_policy(source, policy, diagnostic=None, protocol_bytes=declaration.canonical_bytes())
    config = science.configurations(source, policy)[0]
    calls = []
    monkeypatch.setattr(native, "acquire_with_numerics", lambda *a, **kw: calls.append(a))
    with pytest.raises(ValueError, match="effect identity"):
        native.acquire(replace(config, config_id="config.apparently-fresh-copy"))
    relabelled_temperature = config.initial_temperature_k.quantize(D("0.001"))
    with pytest.raises(ValueError, match="encoding"):
        replace(config, initial_temperature_k=relabelled_temperature,
                config_id=f"config.battery-refined-inquiry.{config.phase}.{relabelled_temperature}.{config.recipe}.{config.component_view}")
    assert calls == []


def test_complete_qualification_cpu_selection_and_reference_failures(selected):
    source, policy = selected
    traces = table(selected)
    q = science.qualify(source, policy, traces)
    assert len(q.traces) == 45 and len(q.comparisons) == 27
    assert q.admitted_models == c.REDUCED and q.selected_model == "chen-spme"
    with pytest.raises(ValueError, match="checks"):
        replace(q, checks=tuple(reversed(q.checks)))
    supply = science.construct_supply(source, policy, q, traces)
    assert len(supply.canonical_bytes()) < sum(len(t.canonical_bytes()) for t in traces)
    with pytest.raises(ValueError, match="census"):
        science.qualify(source, policy, traces[:-1])
    with pytest.raises(ValueError, match="comparisons"):
        replace(supply, qualification=replace(q, comparisons=q.comparisons[:-1]))
    broken = tuple(exposed(t.config, technical=True) if t.config.component_view == "dfn-refined" else t for t in traces)
    failed = science.qualify(source, policy, broken)
    assert failed.disposition is A.UNEVALUABLE and failed.selected_model is None
    with pytest.raises(ValueError, match="precision"):
        replace(failed, selected_model="dfn-primary", disposition=A.SATISFIED)
    with pytest.raises(ValueError, match="admitted"):
        science.compatible_instance(science.construct_supply(source, policy, failed, broken))


def test_agreed_service_negatives_do_not_become_positive_delivery(selected):
    source, policy = selected
    traces = tuple(exposed(config, voltage=D("4.3")) for config in science.configurations(source, policy))
    q = science.qualify(source, policy, traces)
    assert all(check.disposition is A.FALSIFIED for check in q.checks)
    assert all(comp.disposition is A.SATISFIED for comp in q.comparisons)
    supply = science.construct_supply(source, policy, q, traces)
    instance = science.compatible_instance(supply)
    later = tuple(exposed(config, voltage=D("4.3")) for config in science.configurations(source, policy, "use"))
    forecast = [t for t in later if t.config.component_view == q.selected_model]
    choice = science.commit_choice(supply, instance, forecast)
    assert choice.selected_recipe is None
    assessment = science.assess_instance(supply, instance, later, choice, c.identity(choice))
    assert assessment.disposition is A.REFUSED and assessment.joined_disposition is A.REFUSED
    assert not assessment.whole_time_certified


def test_reduced_admission_one_percent_and_two_second_tie(selected, monkeypatch):
    source, policy = selected
    traces = table(selected)
    original = science.check_trace
    def changed(trace):
        check = original(trace)
        if trace.config.component_view in c.REDUCED:
            return replace(check, completion_time_s=check.completion_time_s * D("1.02"))
        return check
    monkeypatch.setattr(science, "check_trace", changed)
    q = science.qualify(source, policy, traces)
    assert q.admitted_models == () and q.selected_model == "dfn-primary"
    assert "completion-forecast-exceeds-one-percent" in q.model_reasons[0][1]
    check = original(traces[0])
    ties = science.best_recipes({"a": replace(check, completion_time_s=D(10)),
                                "b": replace(check, completion_time_s=D(12)),
                                "c": replace(check, completion_time_s=D("12.0001"))})
    assert ties == ("a", "b")


def test_choice_persisted_before_reference_and_original_actual_reuse(selected):
    source, policy = selected
    traces = table(selected)
    supply = science.construct_supply(source, policy, science.qualify(source, policy, traces), traces)
    instance = science.compatible_instance(supply)
    order = []
    def acquire(config):
        order.append(config.component_view)
        return exposed(config)
    def persist(choice):
        order.append("PERSIST")
        return c.identity(choice)
    use, later_traces = science.run_instance(supply, instance, acquire=acquire, persist_choice=persist)
    assert order[:4] == ["chen-spme"] * 3 + ["PERSIST"]
    assert use.assessment.disposition is A.SATISFIED and len(later_traces) == 15
    assert use.assessment.cpu_seconds == sum((t.cpu_seconds for t in later_traces), D(0))
    science.validate_assessment(supply, use.assessment, later_traces)
    reuse_instance = science.compatible_instance(supply, "reuse", prior_use=use)
    reuse, reuse_traces = science.run_instance(supply, reuse_instance, acquire=acquire, persist_choice=persist, prior_use=use)
    assert reuse.prior_use == use.assessment and reuse.assessment.instance.prior_use == c.identity(use)
    assert len(reuse_traces) == 15
    with pytest.raises(ValueError, match="actual entered"):
        science.compatible_instance(supply, "reuse")
    order.clear()
    with pytest.raises(ValueError, match="not retained"):
        science.run_instance(supply, instance, acquire=acquire, persist_choice=lambda _: ObjectIdentity("wrong", c.ChoiceCommitment.SCHEMA, "1.0.0", "0" * 64))
    assert len(order) == 3
    with pytest.raises(ValueError, match="before-reveal"):
        replace(use.assessment, persisted_choice=ObjectIdentity("wrong", c.ChoiceCommitment.SCHEMA, "1.0.0", "0" * 64))
