# SPDX-License-Identifier: MPL-2.0
"""Exposed software fixtures; no native forecast, physical or issue qualification."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.battery_thermal_inquiry import native, science
from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import (
    BatteryInquiryDelivery,
    BatteryInquiryChargingAttempt,
    BatteryInquiryInitializerAttempt,
    BatteryInquirySource,
    BatteryInquiryTrace,
    BatteryInquiryTransition,
    BACKEND_SOLVE_SCOPE,
    CONTROL_RULE,
    DEVELOPMENT_TEMPERATURES,
    MODEL_VIEWS,
    PROTOCOL_SHA256,
    RECIPES,
    TIER_TEMPERATURE,
    TIER_EVENT,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition

D = Decimal


def _mock_charging_attempt(
    config,
    index,
    regime,
    start,
    stop,
    termination,
    requested=(),
    *,
    first=None,
    last=None,
    state=None,
    technical=False,
):
    first = first or (-D("1.3"), D("4.2"), config.initial_temperature_k, D(0))
    last = last or (-D("1.3"), D("4.2"), first[2], -D("2.5"))
    state = state or (D(0), D(1))
    return BatteryInquiryChargingAttempt(
        index,
        regime,
        config.localization_epsilon_k,
        start,
        '{"type":"ExposedSolver"}',
        "0" * 64,
        "exposed-applied-control",
        tuple(sorted(native.hybrid_inputs(config, regime).items())),
        requested,
        "TECHNICAL_FAILURE" if technical else "RETURNED",
        termination,
        "ExposedFailure" if technical else None,
        "retained exposed failure" if technical else None,
        D("0.1"),
        D("0.2"),
        () if technical else (start, stop),
        () if technical else state,
        () if technical else (last[3], D(1)),
        () if technical else first,
        () if technical else last,
    )


def _two_segment_trace():
    config = science.native_config(
        BatteryInquirySource(), "use", D("293.15"), "chamber-35c", "oregan-spme"
    )
    base = _exposed_trace(config)
    crossing, right, end = D(100), D("100.00000000000001"), base.times_s[-1]
    temperature = TIER_TEMPERATURE + config.localization_epsilon_k
    capacity = -D("1.3") * crossing / D(3600)
    first = _mock_charging_attempt(
        config,
        1,
        "LOW",
        D(0),
        crossing,
        TIER_EVENT,
        last=(-D("1.3"), D("4.2"), temperature, capacity),
    )
    second = _mock_charging_attempt(
        config,
        2,
        "HIGH",
        right,
        end,
        native.TARGET_EVENT,
        first.end_differential_state,
        first=(-D("1.3"), D("4.2"), temperature, capacity),
        last=(-D("1.3"), D("4.2"), temperature, -D("2.5")),
        state=first.end_differential_state,
    )
    second = replace(second, requested_start_clock_s=crossing)
    transition = BatteryInquiryTransition(
        1,
        1,
        2,
        "LOW",
        "HIGH",
        TIER_EVENT,
        temperature,
        crossing,
        first.end_receivers,
        first.end_differential_state,
        right,
        second.start_receivers,
        second.start_differential_state,
    )
    return replace(
        base,
        times_s=(D(0), crossing, right, end),
        current_a=(-D("1.3"),) * 4,
        voltage_v=(D("4.2"),) * 4,
        capacity_ah=(D(0), capacity, capacity, -D("2.5")),
        mean_temperature_k=(
            config.initial_temperature_k,
            temperature,
            temperature,
            temperature,
        ),
        ambient_temperature_k=(config.chamber_temperature_k,) * 4,
        control_modes=("CV",) * 4,
        backend_solve_calls=2,
        charging_attempts=(first, second),
        transitions=(transition,),
        temperature_regimes=("LOW", "LOW", "HIGH", "HIGH"),
    )


def test_hybrid_subsolve_ledger_full_state_and_separate_native_boundaries():
    trace = _two_segment_trace()
    assert science.check_trace(trace).disposition is AssessmentDisposition.SATISFIED
    assert trace.backend_solve_calls == 2 and len(trace.transitions) == 1
    before, after = trace.charging_attempts
    assert after.requested_state_sha256 == before.realized_end_state_sha256
    assert after.realized_start_state_sha256 == before.realized_end_state_sha256
    assert trace.transitions[0].right_clock_s > trace.transitions[0].root_clock_s
    assert (
        decode_canonical_bytes(
            trace.canonical_bytes(), BatteryInquiryTrace, maximum_bytes=None
        )
        == trace
    )
    with pytest.raises(ValueError, match="census"):
        replace(trace, backend_solve_calls=1)
    hidden = replace(
        _exposed_trace(trace.config), charging_attempts=(), backend_solve_calls=0
    )
    assert science.check_trace(hidden).disposition is AssessmentDisposition.UNEVALUABLE


def test_hybrid_actual_state_roundoff_and_corrupted_state_are_distinguished():
    trace = _two_segment_trace()
    before, after = trace.charging_attempts
    for difference, expected in (
        (D("1e-12"), AssessmentDisposition.SATISFIED),
        (D(1), AssessmentDisposition.UNEVALUABLE),
    ):
        state = (
            after.start_differential_state[0] + difference,
            *after.start_differential_state[1:],
        )
        changed = replace(
            after, start_differential_state=state, realized_start_state_sha256=""
        )
        transition = replace(trace.transitions[0], right_differential_state=state)
        actual = replace(
            trace, charging_attempts=(before, changed), transitions=(transition,)
        )
        assert changed.requested_state_sha256 != changed.realized_start_state_sha256
        assert science.check_trace(actual).disposition is expected


def test_hybrid_dispatch_retains_up_down_roots_and_every_subsolve():
    config = science.native_config(
        BatteryInquirySource(), "use", D("293.15"), "chamber-35c", "oregan-spme"
    )
    calls = []

    def execute(index, regime, start, previous):
        calls.append((index, regime, start, previous))
        requested = () if previous is None else previous.end_differential_state
        temperature = native.hybrid_inputs(config, regime)[native.TIER_THRESHOLD_INPUT]
        first = None if previous is None else previous.end_receivers
        row = _mock_charging_attempt(
            config,
            index,
            regime,
            start if previous is None else start + D("1e-10"),
            D(index * 100),
            TIER_EVENT if index < 3 else native.TARGET_EVENT,
            requested,
            first=first,
            last=(-D("1.3"), D("4.2"), temperature, -D(index) / D(10)),
            state=requested or None,
        )
        return row, row

    attempts, transitions = [], []
    assert native.run_hybrid_segments(config, execute, attempts, transitions) is None
    assert [row.regime for row in attempts] == ["LOW", "HIGH", "LOW"]
    assert len(attempts) == 3 and len(transitions) == 2
    assert all(
        after.requested_differential_state == before.end_differential_state
        for before, after in zip(attempts, attempts[1:])
    )
    assert calls[1][3] is attempts[0] and calls[2][3] is attempts[1]
    refined = replace(config, model_view="oregan-dfn-refined")
    assert config.localization_epsilon_k == D(
        "0.001"
    ) and refined.localization_epsilon_k == D("0.0001")
    assert (
        native.hybrid_inputs(refined, "LOW")[native.TIER_THRESHOLD_INPUT]
        < native.hybrid_inputs(config, "LOW")[native.TIER_THRESHOLD_INPUT]
    )


def test_hybrid_failed_continuation_and_zero_progress_are_retained_without_retry():
    config = science.native_config(
        BatteryInquirySource(), "use", D("293.15"), "chamber-35c", "oregan-spme"
    )

    def execute(index, regime, start, previous):
        row = _mock_charging_attempt(
            config,
            index,
            regime,
            start,
            D(100),
            TIER_EVENT if index == 1 else "ExposedFailure",
            () if previous is None else previous.end_differential_state,
            last=(
                -D("1.3"),
                D("4.2"),
                TIER_TEMPERATURE + config.localization_epsilon_k,
                -D("0.1"),
            ),
            technical=index == 2,
        )
        return row, row

    attempts, transitions = [], []
    assert (
        native.run_hybrid_segments(config, execute, attempts, transitions)[0]
        == "ExposedFailure"
    )
    assert (
        len(attempts) == 2
        and len(transitions) == 1
        and transitions[0].right_clock_s is None
    )

    def no_progress(index, regime, start, previous):
        row = _mock_charging_attempt(
            config, index, regime, D(0), D(1), native.TARGET_EVENT
        )
        return replace(row, native_times_s=(D(0),)), row

    attempts, transitions = [], []
    assert (
        native.run_hybrid_segments(config, no_progress, attempts, transitions)[0]
        == "NativeNumericalNoProgress"
    )
    assert len(attempts) == 1


def test_first_charging_subcall_failure_projection_keeps_actual_cause_and_no_delivery():
    config = science.native_config(
        BatteryInquirySource(), "use", D("293.15"), "chamber-35c", "oregan-spme"
    )
    row = _mock_charging_attempt(
        config, 1, "LOW", D(0), D(100), "ExposedFailure", technical=True
    )
    attempts, transitions = [], []
    failure = native.run_hybrid_segments(
        config, lambda *_: (row, None), attempts, transitions
    )
    (
        clocks,
        columns,
        modes,
        regimes,
        termination,
        disposition,
        error_type,
        error_message,
    ) = native.project_hybrid_run(attempts, [], failure)
    assert attempts == [row] and not transitions
    assert not clocks and columns == ((), (), (), (), ()) and not modes and not regimes
    assert termination == "ExposedFailure" and disposition == "TECHNICAL_FAILURE"
    assert (
        error_type == "ExposedFailure" and error_message == "retained exposed failure"
    )


def _exposed_trace(
    config,
    *,
    duration=None,
    voltage=D("4.2"),
    magnitude=None,
    cpu=D(1),
    technical=False,
):
    # Synthetic canonical receivers exercise reductions only. They are never
    # used in actual launch configuration or supplied as scientific evidence.
    magnitude = (
        magnitude
        or {"original-ambient": D("1.1"), "chamber-35c": D("1.3"), "chamber-40c": D(1)}[
            config.recipe
        ]
    )
    duration = duration or D(9000) / magnitude
    delivery = BatteryInquiryDelivery(
        CONTROL_RULE,
        D("4.2"),
        D("4.2"),
        config.chamber_temperature_k,
        config.chamber_temperature_k,
        D(0),
        D(0),
        "exposed-control",
        "exposed-applied-control",
        "exposed-current",
        "exposed-voltage",
        "exposed-chamber",
        -magnitude,
        voltage,
        config.chamber_temperature_k,
    )
    regime = (
        "HIGH"
        if config.initial_temperature_k
        >= TIER_TEMPERATURE + config.localization_epsilon_k
        else "LOW"
    )
    attempt = BatteryInquiryChargingAttempt(
        1,
        regime,
        config.localization_epsilon_k,
        D(0),
        '{"type":"ExposedSolver"}',
        "0" * 64,
        "exposed-applied-control",
        tuple(sorted(native.hybrid_inputs(config, regime).items())),
        (),
        "RETURNED",
        native.TARGET_EVENT,
        None,
        None,
        cpu,
        D(1),
        (D(0), duration),
        (D(0), D(1)),
        (D("-2.5"), D(1)),
        (-magnitude, voltage, config.initial_temperature_k, D(0)),
        (-magnitude, voltage, config.initial_temperature_k, D("-2.5")),
    )
    return BatteryInquiryTrace(
        "trace." + config.config_id,
        config,
        "0" * 64,
        "TECHNICAL_FAILURE" if technical else "TARGET_REACHED",
        "ExposedError" if technical else native.TARGET_EVENT,
        "ExposedError" if technical else None,
        "software fixture" if technical else None,
        delivery,
        (D(0), duration),
        (-magnitude, -magnitude),
        (voltage, voltage),
        (D(0), D("-2.5")),
        (config.initial_temperature_k, config.initial_temperature_k),
        (config.chamber_temperature_k, config.chamber_temperature_k),
        ("CV", "CV"),
        native.EVENT_NAMES,
        tuple("exposed-expression" for _ in native.EVENT_NAMES),
        1,
        0 if technical else 1,
        D(1),
        cpu,
        1,
        (
            BatteryInquiryInitializerAttempt(
                1,
                "ExposedSolver",
                "exposed initializer",
                '{"type":"ExposedSolver"}',
                "exposed SOH model",
                "0" * 64,
                "RETURNED",
                None,
                None,
                D(0),
                D(0),
            ),
        ),
        charging_attempts=() if technical else (attempt,),
        temperature_regimes=(regime, regime),
    )


def _table(*, altered=None):
    source = BatteryInquirySource()
    rows = tuple(
        _exposed_trace(
            science.native_config(source, "supply", t, r, m),
            cpu=D(1) if m == "chen-spme" else D(2),
        )
        for t in DEVELOPMENT_TEMPERATURES
        for r in RECIPES
        for m in MODEL_VIEWS
    )
    return tuple(altered(v) if altered else v for v in rows)


def test_protocol_and_sources_roundtrip_without_native_import():
    raw = Path("programmes/energy/battery-charging/records/battery-thermal-inquiry-selection.json").read_bytes()
    assert sha256(raw).hexdigest() == PROTOCOL_SHA256
    source = BatteryInquirySource()
    assert (
        decode_canonical_bytes(
            source.canonical_bytes(), BatteryInquirySource, maximum_bytes=None
        )
        == source
    )
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; from empirical_lawhood.adapters.methods.battery_thermal_inquiry import contracts,native,science; assert 'pybamm' not in sys.modules",
        ],
        check=True,
    )
    with pytest.raises(ValueError, match="separately frozen"):
        replace(source, protocol_sha256="0" * 64)


def test_current_integral_and_cv_realization_are_independent_of_request():
    config = science.native_config(
        BatteryInquirySource(), "use", D("293.15"), "chamber-35c", "oregan-spme"
    )
    trace = _exposed_trace(config)
    check = science.check_trace(trace)
    assert check.realized_charge_ah == D("2.5")
    assert check.disposition is AssessmentDisposition.SATISFIED
    assert trace.delivery.requested_voltage_v == D("4.2")
    assert trace.delivery.applied_current_a == -D("1.3")
    assert not check.whole_time_certified
    corrupted = replace(trace, capacity_ah=(D(0), D("-2.4")))
    assert (
        science.check_trace(corrupted).disposition is AssessmentDisposition.UNEVALUABLE
    )


def test_high_current_at_exact_temperature_boundary_is_refused():
    config = science.native_config(
        BatteryInquirySource(), "supply", D("298.15"), "original-ambient", "chen-spme"
    )
    trace = _exposed_trace(config, magnitude=D("3.395"))
    assert science.check_trace(trace).disposition is AssessmentDisposition.FALSIFIED
    assert (
        "sampled-source-envelope-violation" in science.check_trace(trace).reason_codes
    )
    low = _exposed_trace(config, magnitude=D("1.455"))
    assert science.check_trace(low).disposition is AssessmentDisposition.SATISFIED


def test_missing_protective_event_or_processed_expression_is_unevaluable():
    config = science.native_config(
        BatteryInquirySource(), "use", D("293.15"), "chamber-35c", "oregan-spme"
    )
    trace = _exposed_trace(config)
    for changed in (
        replace(trace, initializer_attempts=()),
        replace(trace, event_names=(), processed_event_expressions=()),
        replace(
            trace,
            event_names=trace.event_names[:-1],
            processed_event_expressions=trace.processed_event_expressions[:-1],
        ),
        replace(
            trace,
            processed_event_expressions=("", *trace.processed_event_expressions[1:]),
        ),
    ):
        check = science.check_trace(changed)
        assert check.disposition is AssessmentDisposition.UNEVALUABLE
        assert not check.native_control_checked
        assert "native-control-or-chamber-delivery-unresolved" in check.reason_codes


def test_complete_procedure_chooses_admitted_actual_cpu_cost():
    table = _table()
    procedure = science.assess_procedure(table)
    assert procedure.disposition is AssessmentDisposition.SATISFIED
    assert procedure.admitted_models == ("chen-spme", "oregan-spme")
    assert procedure.selected_model == "chen-spme"
    with pytest.raises(ValueError, match="complete development"):
        science.assess_procedure(table[:-1])


def test_wrong_fastest_choice_falsifies_model_without_erasing_reference():
    def change(trace):
        if (
            trace.config.model_view == "chen-spme"
            and trace.config.recipe == "original-ambient"
        ):
            return _exposed_trace(trace.config, magnitude=D("1.4"))
        return trace

    procedure = science.assess_procedure(_table(altered=change))
    assert procedure.selected_model == "oregan-spme"
    assert (
        "unique-fastest-recipe-disagrees-outside-tie"
        in dict(procedure.model_reasons)["chen-spme"]
    )


def test_all_reduced_models_refused_uses_explicit_direct_dfn_fallback():
    def change(trace):
        if trace.config.model_view.endswith("spme"):
            return _exposed_trace(trace.config, magnitude=D("0.8"))
        return trace

    procedure = science.assess_procedure(_table(altered=change))
    assert procedure.selected_model == "oregan-dfn"
    assert not procedure.admitted_models
    assert procedure.reason_codes == ("reduced-models-refused-direct-dfn-fallback",)


def test_missing_reference_native_observation_is_unevaluable_not_model_failure():
    def change(trace):
        return (
            _exposed_trace(trace.config, technical=True)
            if trace.config.model_view == "oregan-dfn-refined"
            else trace
        )

    procedure = science.assess_procedure(_table(altered=change))
    assert procedure.disposition is AssessmentDisposition.UNEVALUABLE
    assert procedure.selected_model is None


def test_unavailable_native_library_retains_typed_zero_solve_attempt(monkeypatch):
    # Block the very first runtime library import: no native package, model,
    # provider or solve is contacted by this exposed software failure test.
    monkeypatch.setitem(sys.modules, "numpy", None)
    config = science.native_config(
        BatteryInquirySource(), "use", D("293.15"), "original-ambient", "chen-spme"
    )
    trace = native.acquire(config)
    assert trace.disposition == "TECHNICAL_FAILURE"
    assert trace.error_type == "ModuleNotFoundError" and trace.error_message
    assert trace.native_provider_attempts == 1 and trace.backend_solve_calls == 0
    assert not trace.times_s
    assert trace.delivery.accepted_voltage_v is trace.delivery.applied_current_a is None
    assert trace.wall_seconds >= 0 and trace.cpu_seconds >= 0
    assert not trace.initializer_attempts
    assert trace.backend_solve_scope == BACKEND_SOLVE_SCOPE
    assert science.check_trace(trace).disposition is AssessmentDisposition.UNEVALUABLE


def test_initializer_observer_retains_actual_fallback_attempts_and_restores_method():
    class ExposedSolver:
        def __init__(self, name, *, fail=False):
            self.name, self.fail = name, fail

        def to_config(self):
            return {"type": "ExposedSolver", "name": self.name}

        def solve(self, model):
            if self.fail:
                raise ArithmeticError("exposed initial-state failure")
            return model.name

    original = ExposedSolver.solve
    attempts = []
    full = SimpleNamespace(
        name="exposed full SOH",
        algebraic={"x": "full"},
        initial_conditions={"x": "guess"},
    )
    split = SimpleNamespace(
        name="exposed split SOH",
        algebraic={"x": "split"},
        initial_conditions={"x": "guess"},
    )
    with native.observe_initial_solver_calls(ExposedSolver, attempts):
        for solver in (
            ExposedSolver("first", fail=True),
            ExposedSolver("fallback", fail=True),
        ):
            with pytest.raises(ArithmeticError, match="initial-state"):
                solver.solve(full)
        assert ExposedSolver("split fallback").solve(split) == split.name
    assert ExposedSolver.solve is original
    assert [a.attempt_index for a in attempts] == [1, 2, 3]
    assert [a.disposition for a in attempts] == [
        "TECHNICAL_FAILURE",
        "TECHNICAL_FAILURE",
        "RETURNED",
    ]
    assert all(a.error_type == "ArithmeticError" for a in attempts[:2])
    assert attempts[0].model_expression_sha256 != attempts[2].model_expression_sha256
    assert all(a.cpu_seconds >= 0 and a.wall_seconds >= 0 for a in attempts)
    with pytest.raises(ArithmeticError, match="initial-state"):
        with native.observe_initial_solver_calls(ExposedSolver, attempts):
            ExposedSolver("uncaught", fail=True).solve(full)
    assert ExposedSolver.solve is original and len(attempts) == 4
    ExposedSolver("outside observed preparation").solve(full)
    assert len(attempts) == 4


def test_unselected_false_admission_falsifies_transfer_while_joined_use_passes(
    monkeypatch,
):
    def exposed_acquire(config):
        if (
            config.phase == "use"
            and config.model_view == "chen-spme"
            and config.recipe == "original-ambient"
        ):
            return _exposed_trace(config, magnitude=D("0.8"), cpu=D(1))
        return _exposed_trace(
            config, cpu=D(1) if config.model_view == "chen-spme" else D(2)
        )

    monkeypatch.setattr(native, "acquire", exposed_acquire)
    supplier = science.supply(BatteryInquirySource())
    result = science.assess(supplier, science.compatible_instance(supplier))
    assert result.selected_recipe == "chamber-35c"
    assert result.joined_disposition is AssessmentDisposition.SATISFIED
    assert result.admission_disposition is AssessmentDisposition.FALSIFIED
    assert result.disposition is AssessmentDisposition.FALSIFIED


def test_all_supplied_forecast_failures_remain_unevaluable_with_resolved_reference(
    monkeypatch,
):
    def exposed_acquire(config):
        return _exposed_trace(
            config,
            cpu=D(1) if config.model_view == "chen-spme" else D(2),
            technical=config.phase == "use" and config.model_view == "chen-spme",
        )

    monkeypatch.setattr(native, "acquire", exposed_acquire)
    supplier = science.supply(BatteryInquirySource())
    result = science.assess(supplier, science.compatible_instance(supplier))
    assert result.selected_recipe is None
    assert all(
        ref.disposition is AssessmentDisposition.SATISFIED
        for ref in result.reference_checks
    )
    assert result.instance_disposition is AssessmentDisposition.SATISFIED
    assert (
        result.admission_disposition
        is result.joined_disposition
        is result.disposition
        is AssessmentDisposition.UNEVALUABLE
    )
    assert result.reason_codes == ("supplied-model-native-forecast-unresolved",)
    science.validate_assessment(supplier, result)


def test_false_forecast_infeasibility_is_not_hidden_by_no_recipe_choice(monkeypatch):
    def exposed_acquire(config):
        trace = _exposed_trace(
            config, cpu=D(1) if config.model_view == "chen-spme" else D(2)
        )
        if config.phase == "use" and config.model_view == "chen-spme":
            return replace(
                trace,
                disposition="SERVICE_TERMINATED",
                termination="Inquiry source minimum charging magnitude [A]",
            )
        return trace

    monkeypatch.setattr(native, "acquire", exposed_acquire)
    supplier = science.supply(BatteryInquirySource())
    result = science.assess(supplier, science.compatible_instance(supplier))
    assert result.selected_recipe is None
    assert result.reference_best_recipes == ("chamber-35c",)
    assert result.joined_disposition is AssessmentDisposition.REFUSED
    assert (
        result.admission_disposition
        is result.disposition
        is AssessmentDisposition.FALSIFIED
    )
    science.validate_assessment(supplier, result)


def test_singleton_supply_and_separate_recipients_have_complete_attempts(monkeypatch):
    actual = []

    def exposed_acquire(config):
        actual.append(config)
        return _exposed_trace(
            config, cpu=D(1) if config.model_view == "chen-spme" else D(2)
        )

    monkeypatch.setattr(native, "acquire", exposed_acquire)
    supplier = science.supply(BatteryInquirySource())
    assert len(actual) == 36
    science.validate_supply(supplier)
    assert supplier.disposition is AssessmentDisposition.SATISFIED
    later = science.assess(supplier, science.compatible_instance(supplier))
    reuse = science.assess(
        supplier,
        science.compatible_instance(supplier, phase="reuse", prior_use=later),
        prior_use=later,
    )
    assert len(actual) == 60
    for result in (later, reuse):
        science.validate_assessment(
            supplier,
            result,
            prior_use=later if result.instance.phase == "reuse" else None,
        )
        assert result.native_provider_attempts == result.backend_solve_calls == 12
        assert result.selected_recipe == "chamber-35c"
        assert (
            result.instance_disposition
            is result.admission_disposition
            is result.joined_disposition
            is AssessmentDisposition.SATISFIED
        )
        assert (
            result.physical_independent_units == 0
            and result.simulated_parameter_families == 1
        )
        assert len(result.cache_hits) == 3
    allocations = science.cost_allocations(supplier, (later, reuse))
    assert [a.native_provider_attempts for a in allocations] == [60, 60, 30]
    assert [a.initializer_solver_attempts for a in allocations] == [60, 60, 30]
    assert allocations[0].charged_traces == allocations[1].charged_traces
    assert all(
        a.shared_computations and a.complete_total_cost_superiority == "UNEVALUABLE"
        for a in allocations
    )
    with pytest.raises(ValueError, match="duplicates a recipient"):
        science.cost_allocations(supplier, (later, later))
    assert later.instance != reuse.instance
    assert reuse.instance.prior_use == science.identity(later)
    assert later.instance.prior_use is None
    with pytest.raises(ValueError, match="actual prior-use"):
        science.compatible_instance(supplier, phase="reuse")
    with pytest.raises(ValueError, match="actual prior-use"):
        science.assess(supplier, reuse.instance)
    with pytest.raises(ValueError, match="actual prior-use"):
        science.validate_assessment(supplier, reuse)
    with pytest.raises(ValueError, match="completed attempted later use"):
        science.compatible_instance(supplier, phase="reuse", prior_use=reuse)
    with pytest.raises(ValueError, match="independently derived"):
        science.compatible_instance(
            supplier,
            phase="reuse",
            prior_use=replace(later, selected_recipe="original-ambient"),
        )
    assert len(actual) == 60  # Failed pure lineage guards cannot add native contacts.
    with pytest.raises(ValueError, match="exact later/reuse"):
        replace(later.instance, initial_temperature_k=D("300.15"))
