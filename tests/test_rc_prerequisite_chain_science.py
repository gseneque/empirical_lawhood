"""Frozen rule, bounded work and complete adverse RC development records."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import replace
from decimal import Decimal, Inexact, ROUND_UP, localcontext

import pytest

from empirical_lawhood.adapters.methods.rc_prerequisite_chain import science
from empirical_lawhood.adapters.methods.rc_prerequisite_chain.contracts import (
    ARM_IDS, VARIANT_IDS, RCPrerequisiteChainConfig, decay_factor,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes


def test_design_compilation_is_static_bounded_and_canonically_transportable() -> None:
    config = science.default_chain_config()
    assert decode_canonical_bytes(config.canonical_bytes(), RCPrerequisiteChainConfig, maximum_bytes=65536) == config
    proof = science.prove_chain(config)
    assert proof.unit_count == 11
    assert proof.maximum_native_steps <= config.protocol.maximum_native_steps
    assert proof.maximum_nested_view_count == 154  # Nested views, not unit count.
    script = (
        "import sys; from empirical_lawhood.adapters.methods.rc_prerequisite_chain.science "
        "import default_chain_config,prove_chain; prove_chain(default_chain_config()); "
        "assert 'numpy' not in sys.modules and 'scipy' not in sys.modules"
    )
    subprocess.run([sys.executable, "-c", script], check=True, capture_output=True, text=True)


def test_compile_refuses_work_budget_before_any_native_operation(monkeypatch) -> None:
    config = science.default_chain_config()
    config = replace(config, protocol=replace(config.protocol, maximum_native_steps=100))
    monkeypatch.setattr(science, "_execute", lambda *args: pytest.fail("Budget refusal acquired a source"))
    with pytest.raises(ValueError, match="work budget"):
        science.evaluate_unit(config, config.units[0].unit_id)


@pytest.mark.parametrize("duration", [".250000000000000000000001", ".250000000000001"])
def test_almost_coincident_action_and_grid_clocks_refuse_before_native_contact(monkeypatch, duration) -> None:
    config = science.default_chain_config()
    menu = (Decimal(0), Decimal(duration), *config.protocol.preparation_durations_seconds[2:])
    config = replace(config, protocol=replace(config.protocol, preparation_durations_seconds=menu))
    monkeypatch.setattr(science, "_execute", lambda *args: pytest.fail("Unsafe clock grid acquired a source"))
    with pytest.raises(ValueError, match="collapse|work budget"):
        science.evaluate_unit(config, config.units[0].unit_id)


def test_callers_decimal_context_cannot_change_frozen_choices_or_canonical_default() -> None:
    config = science.default_chain_config()
    unit = config.units[7]
    expectation = science._expectation(config, unit, science._source(config, unit))
    observation = science._observation(config.protocol, expectation, unit.initial_voltage_volts, "adequate")
    baseline = science.decide_preparation(config.protocol, expectation, observation)
    with localcontext() as context:
        context.prec = 6
        context.rounding = ROUND_UP
        context.traps[Inexact] = True
        changed = science.default_chain_config()
        assert changed.canonical_bytes() == config.canonical_bytes()
        assert science.prove_chain(changed) == science.prove_chain(config)
        assert science.decide_preparation(config.protocol, expectation, observation) == baseline


@pytest.mark.parametrize("capacitance,resistance,a", [
    ("1e300", "1e-320", "0"),
    ("1e-320", "1e300", "0"),
    ("1e300", "1e300", "1"),
])
def test_finite_decimal_components_refuse_unrepresentable_native_operators_before_contact(
    monkeypatch, capacitance, resistance, a,
) -> None:
    config = science.default_chain_config()
    config = replace(config, protocol=replace(config.protocol, capacitance_farads=Decimal(capacitance),
        left_source_resistance_ohms=Decimal(resistance), right_source_resistance_ohms=Decimal(resistance),
        response_coefficient_a=Decimal(a), response_coefficient_b_volts=(1 - Decimal(a)) / 2))
    monkeypatch.setattr(science, "_execute", lambda *args: pytest.fail("Unrepresentable native operator acquired a source"))
    with pytest.raises(ValueError, match="native conductance|state coefficient"):
        science.evaluate_unit(config, config.units[0].unit_id)


def test_exact_decimal_response_refuses_native_forcing_overflow_before_contact(monkeypatch) -> None:
    config = science.default_chain_config()
    protocol = config.protocol
    with localcontext() as context:
        context.prec = 50
        b = Decimal("5e308") * (1 - protocol.response_coefficient_a)
    config = replace(config, protocol=replace(protocol, response_left_voltage_volts=Decimal("1e309"),
        response_coefficient_b_volts=b))
    monkeypatch.setattr(science, "_execute", lambda *args: pytest.fail("Unrepresentable response forcing acquired a source"))
    with pytest.raises(ValueError, match="response boundaries|forcing"):
        science.evaluate_unit(config, config.units[0].unit_id)


def test_declared_arithmetic_guard_changes_boundary_choice_before_observation_outcomes() -> None:
    config = science.default_chain_config()
    unit = config.units[3]
    expected = science._expectation(config, unit, science._source(config, unit))
    upper = config.protocol.support_upper_volts / decay_factor(config.protocol.decay_rate_per_second,
        config.protocol.decision_seconds)
    observation = science._observation(config.protocol, expected, Decimal(0), "adequate")
    assert observation is not None
    observation = replace(observation, reported_voltage_volts=upper - observation.radius_volts)
    decision = science.decide_preparation(config.protocol, expected, observation)
    assert decision.disposition == "ADMITTED"
    assert decision.duration_seconds == Decimal(".25")


def test_numerical_source_failure_retains_every_assigned_terminal_row(monkeypatch) -> None:
    config = science.default_chain_config()
    config = replace(config, units=(config.units[0],))
    calls = []

    def failed(*args):
        calls.append(args)
        raise RuntimeError("native failure")

    monkeypatch.setattr(science, "_execute", failed)
    result = science.evaluate_unit(config, config.units[0].unit_id)
    assert len(calls) == 1
    assert result.source_failure_reason_codes == ("NUMERICAL_EXECUTION_FAILED",)
    assert tuple(case.variant_id for case in result.cases) == VARIANT_IDS
    assert tuple(arm.arm_id for arm in result.cases[0].arms) == ARM_IDS
    assert all(case.measurement_state == "UNEVALUABLE" for case in result.cases)
    assert all(arm.joined_state == "UNEVALUABLE" for case in result.cases for arm in case.arms)
    science.verify_unit_result(config, result)
    summary = science.summarize_chain(config, (result,))
    assert summary.unit_count == 1
    assert summary.nested_view_count == 0
    assert len(calls) == 1
    with pytest.raises(ValueError, match="complete assigned unit census"):
        science.summarize_chain(config, ())


def test_unit_relabeling_does_not_make_repeated_deterministic_state_independent() -> None:
    config = science.default_chain_config()
    repeated = replace(config.units[0], unit_id="rc-chain-unit-99")
    with pytest.raises(ValueError, match="relabelled"):
        replace(config, units=(*config.units, repeated))


def test_failed_source_conformance_keeps_completed_panels_and_has_a_cold_reader(tmp_path, monkeypatch) -> None:
    config = science.default_chain_config()
    config = replace(config, units=(config.units[0],),
        protocol=replace(config.protocol, maximum_view_defect_volts=Decimal(".00000001")))
    result = science.evaluate_unit(config, config.units[0].unit_id)
    assert result.source_failure_reason_codes == ("NUMERICAL_SOURCE_CONFORMANCE_FAILED",)
    assert len(result.source_panels) == 2
    assert all(case.measurement_state == "UNEVALUABLE" for case in result.cases)
    monkeypatch.setattr(science, "_execute", lambda *args: pytest.fail("Retained failure repeated source acquisition"))
    science.verify_unit_result(config, result)
    config_path, result_path = tmp_path / "config.json", tmp_path / "result.json"
    config_path.write_bytes(config.canonical_bytes())
    result_path.write_bytes(result.canonical_bytes())
    script = (
        "import sys; from pathlib import Path; "
        "from empirical_lawhood.kernel.decoding import decode_canonical_bytes; "
        "from empirical_lawhood.adapters.methods.rc_prerequisite_chain.contracts import RCPrerequisiteChainConfig,RCChainUnitResult; "
        "from empirical_lawhood.adapters.methods.rc_prerequisite_chain.science import verify_unit_result; "
        "c=decode_canonical_bytes(Path(sys.argv[1]).read_bytes(),RCPrerequisiteChainConfig,maximum_bytes=65536); "
        "r=decode_canonical_bytes(Path(sys.argv[2]).read_bytes(),RCChainUnitResult,maximum_bytes=16777216); "
        "verify_unit_result(c,r); assert 'numpy' not in sys.modules and 'scipy' not in sys.modules"
    )
    subprocess.run([sys.executable, "-c", script, str(config_path), str(result_path)],
        check=True, capture_output=True, text=True)


@pytest.mark.parametrize("field,value", [("capacitance_farads", 1.0), ("decision_seconds", True)])
def test_direct_protocol_constructor_rejects_inexact_numerical_operands(field, value) -> None:
    with pytest.raises(ValueError, match="finite Decimal"):
        replace(science.default_chain_config().protocol, **{field: value})


def test_failure_product_cannot_be_promoted_or_bind_another_config() -> None:
    config = science.default_chain_config()
    result = science.failed_unit_result(config, config.units[0].unit_id)
    with pytest.raises(ValueError, match="evidence role"):
        replace(result, evidence_role="SCIENTIFIC_QUALIFICATION")
    changed = replace(config, config_id="distinct-selected-design")
    with pytest.raises(ValueError, match="configuration"):
        science.verify_unit_result(changed, result)
