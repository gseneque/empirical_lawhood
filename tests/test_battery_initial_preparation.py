# SPDX-License-Identifier: MPL-2.0
"""Independent adverse controls; exposed fixtures confer no qualification."""

from dataclasses import replace
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
import subprocess
import sys

import pytest

from empirical_lawhood.adapters.methods.battery_thermal_inquiry import science as legacy
from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import BatteryInquirySource
from empirical_lawhood.adapters.methods.battery_refined_inquiry.preparation_contracts import (
    InitialElectrodePreparationWitness, ObservationKind, PreparationProtocol,
    ProcessedInitialStateLayout, PreparedTraceJoin, StateBlock, StateObservation, identity,
)
from empirical_lawhood.adapters.methods.battery_refined_inquiry import preparation_science as science
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from tests.test_battery_thermal_inquiry import _exposed_trace

D = Decimal


def _id(name, schema="empirical-lawhood/runtime/native-subwork-completion"):
    return ObjectIdentity(name, schema, "1.0.0", "0" * 64)


def _decimal_fraction(value):
    with localcontext() as context:
        context.prec = 80
        return D(str(float(D(value.numerator) / D(value.denominator))))


def _prepared_fixture(*, family="SPMe", parameter="ORegan2022"):
    config = legacy.native_config(BatteryInquirySource(), "use", D("293.15"), "chamber-35c",
                                 "chen-spme" if parameter == "Chen2020" else "oregan-spme" if family == "SPMe" else "oregan-dfn")
    trace = _exposed_trace(config)
    protocol = PreparationProtocol("protocol.battery-preparation.fixture", legacy.identity(config), legacy.identity(config.source),
        _id("numerical.producing-provenance", "empirical-lawhood/kernel/numerical-producing-provenance"),
        parameter, family, 30, 40, config.initial_temperature_k, science.PREPARATION_SOURCE_MEMBERS)
    protocol_id = identity(protocol, protocol.protocol_id)
    roots = science.source_root_enclosures(parameter)
    x0, x100 = (_decimal_fraction((r.lower + r.upper) / 2) for r in roots)
    qn, qp, lithium = science.capacity_factors(parameter)
    y0, y100 = (_decimal_fraction((lithium - qn * Fraction.from_float(float(x))) / qp) for x in (x0, x100))
    cn, cp, stock_n, stock_p = science.source_stock(parameter)
    common = Fraction.from_float(float("96485.33212331001")) * Fraction.from_float(.065) * Fraction.from_float(1.58) / 3600
    capacities = tuple(_decimal_fraction(common * q) for q in (qn, qp, lithium))
    xinit = x0 + D(".30") * (x100 - x0)
    yinit = y0 - D(".30") * (y0 - y100)
    witness = InitialElectrodePreparationWitness("witness.battery-preparation.fixture", protocol_id,
        ("RETURNED",), (_id("completion.initializer"),), capacities[2], capacities[0], capacities[1],
        capacities[0] * (x100 - x0), D("96485.33212331001"), x0, x100, y0, y100,
        cn * xinit, cp * yinit, stock_n, stock_p, D("298.15"), D("2.5"), D("4.2"), D("1e-10"), True)
    n = 40 if family == "SPMe" else 1200
    prefix = "X-averaged " if family == "SPMe" else ""
    specifications = [
        ("discharge-capacity", "Discharge capacity [A.h]", 1, D(1)),
        ("throughput-capacity", "Throughput capacity [A.h]", 1, D(1)),
        ("negative-solid", prefix + "negative particle concentration [mol.m-3]" if prefix else "Negative particle concentration [mol.m-3]", n, cn),
        ("positive-solid", prefix + "positive particle concentration [mol.m-3]" if prefix else "Positive particle concentration [mol.m-3]", n, cp),
        ("electrolyte", "Porosity times concentration [mol.m-3]", 90, D(1000)),
        ("temperature", "Volume-averaged cell temperature [K]", 1, D("298.15")),
        ("current", "Current variable [A]", 1, D(5)),
    ]
    if family == "DFN":
        specifications.extend((("negative-potential", "Negative electrode potential [V]", 30, D(1)),
            ("positive-potential", "Positive electrode potential [V]", 30, D(1)),
            ("electrolyte-potential", "Electrolyte potential [V]", 90, D(1))))
    blocks, cursor = [], 0
    for role, name, length, scale in specifications:
        blocks.append(StateBlock(role, name, cursor, cursor + length, scale, D(0), ()))
        cursor += length
    electrolyte = blocks[4]
    rhs = blocks[5].stop
    layout = ProcessedInitialStateLayout("layout.battery-preparation.fixture", protocol_id, "0" * 64, "1" * 64,
        rhs, cursor - rhs, tuple(blocks), tuple((name, electrolyte.start + i * 30, electrolyte.start + (i + 1) * 30)
        for i, name in enumerate(("negative", "separator", "positive"))), True)
    values = (D(0), D(0)) + (xinit,) * n + (yinit,) * n + (D(".25"),) * 30 + (D(".47"),) * 30 + (D(".335"),) * 30 + (D("293.15") / D("298.15"),)
    row = trace.charging_attempts[0]
    trace = replace(trace, charging_attempts=(replace(row, start_differential_state=values,
        end_differential_state=(D("-2.5"),) + values[1:], realized_start_state_sha256="", realized_end_state_sha256=""),))
    layout_id = identity(layout, layout.layout_id)
    def observe(role, state):
        return StateObservation("observation.battery-preparation." + role, protocol_id, layout_id, role,
            ObservationKind.OBSERVED, D(0), state, tuple(float(v).hex() for v in state), (_id("completion.charging"),))
    requested = observe("requested-initial", values + (D(1),) + (D(0),) * (cursor - rhs - 1))
    actual = observe("actual-initial", values + (trace.current_a[0] / D(5),) + (D(0),) * (cursor - rhs - 1))
    join = PreparedTraceJoin("join.battery-preparation.fixture", science.trace_identity(trace), protocol_id,
        identity(witness, witness.witness_id), layout_id, identity(requested, requested.observation_id),
        identity(actual, actual.observation_id), "2" * 64)
    return trace, dict(protocol=protocol, witness=witness, layout=layout, requested_initial=requested, actual_initial=actual, join=join)


def _rejoin(trace, operands):
    operands = dict(operands)
    join = operands["join"]
    operands["join"] = replace(join, trace=science.trace_identity(trace),
        protocol=identity(operands["protocol"], operands["protocol"].protocol_id),
        witness=identity(operands["witness"], operands["witness"].witness_id),
        layout=identity(operands["layout"], operands["layout"].layout_id),
        requested_initial=identity(operands["requested_initial"], operands["requested_initial"].observation_id),
        actual_initial=identity(operands["actual_initial"], operands["actual_initial"].observation_id))
    return operands


@pytest.mark.parametrize("family,parameter,rhs", [("SPMe", "Chen2020", 173), ("SPMe", "ORegan2022", 173), ("DFN", "ORegan2022", 2493)])
def test_independent_full_preparation_checks_every_rhs_component(family, parameter, rhs):
    trace, operands = _prepared_fixture(family=family, parameter=parameter)
    result = science.assess_initial_preparation(trace, **operands)
    assert result.disposition is A.SATISFIED and result.checked_state_components == rhs
    assert not result.physical_qualification
    assert science.require_prepared_trace(trace, result) is trace
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result


@pytest.mark.parametrize("parameter", ["Chen2020", "ORegan2022"])
def test_root_proof_encloses_both_complete_unique_source_endpoints(parameter):
    roots = science.source_root_enclosures(parameter)
    assert len(roots) == 2 and roots[0].upper < roots[1].lower
    assert all(r.upper - r.lower <= Fraction(1, 10**12) for r in roots)
    assert science.monotonicity_margin() > Fraction(3, 10)
    assert all(r.observation_kind == "DERIVED_SOURCE_MATHEMATICS" for r in roots)


def test_historical_correct_receivers_do_not_supply_missing_preparation():
    trace = _exposed_trace(legacy.native_config(BatteryInquirySource(), "use", D("293.15"), "chamber-35c", "oregan-spme"))
    original = trace.canonical_bytes()
    assert legacy.check_trace(trace).disposition is A.SATISFIED
    assessment = science.assess_initial_preparation(trace)
    assert assessment.disposition is A.UNEVALUABLE
    with pytest.raises(ValueError, match="no independently satisfied"):
        science.require_prepared_trace(trace, assessment)
    assert trace.canonical_bytes() == original


def test_reproduced_wrong_initial_temperature_is_a_nonpositive_current_result():
    trace = _exposed_trace(legacy.native_config(BatteryInquirySource(), "use", D("293.15"), "chamber-35c", "oregan-spme"))
    row = trace.charging_attempts[0]
    altered = replace(trace, mean_temperature_k=(D("283.15"),) * 2,
        charging_attempts=(replace(row, start_receivers=(row.start_receivers[0], row.start_receivers[1], D("283.15"), row.start_receivers[3]),
                                  end_receivers=(row.end_receivers[0], row.end_receivers[1], D("283.15"), row.end_receivers[3])),))
    assert legacy.check_trace(altered).disposition is A.SATISFIED
    result = science.assess_initial_preparation(altered)
    assert result.disposition is A.FALSIFIED and "initial-temperature-disagrees" in result.reason_codes


def test_reproduced_uniform_capacity_shift_retains_the_actual_adverse_result():
    trace = _exposed_trace(legacy.native_config(BatteryInquirySource(), "use", D("293.15"), "chamber-35c", "oregan-spme"))
    row = trace.charging_attempts[0]
    altered = replace(trace, capacity_ah=(D(1), D("-1.5")),
        charging_attempts=(replace(row, start_receivers=row.start_receivers[:3] + (D(1),), end_receivers=row.end_receivers[:3] + (D("-1.5"),)),))
    assert legacy.check_trace(altered).disposition is A.SATISFIED
    result = science.assess_initial_preparation(altered)
    assert result.disposition is A.FALSIFIED and "initial-capacity-origin-nonzero" in result.reason_codes


def test_average_matching_compensated_radial_error_still_refuses():
    trace, operands = _prepared_fixture()
    actual = operands["actual_initial"]
    values = list(actual.scaled_values)
    values[2] += D(".01")
    values[3] -= D(".01")
    operands["actual_initial"] = replace(actual, scaled_values=tuple(values), binary64_hex=tuple(float(v).hex() for v in values))
    row = trace.charging_attempts[0]
    trace = replace(trace, charging_attempts=(replace(row, start_differential_state=tuple(values[:173]), realized_start_state_sha256=""),))
    result = science.assess_initial_preparation(trace, **_rejoin(trace, operands))
    assert result.disposition is A.FALSIFIED and result.checked_state_components == 173
    assert "pointwise-full-initial-state-disagrees" in result.reason_codes


@pytest.mark.parametrize("field,value", [("assigned_negative_concentration", D(10000)), ("assigned_positive_concentration", D(10000)),
    ("particle_lithium_capacity_ah", D(5)), ("negative_electrode_capacity_ah", D(5)),
    ("upper_voltage_v", D("4.4")), ("pre_soc_negative_concentration", D(10000)),
    ("x100", D(".2")), ("reference_temperature_k", D("293.15")), ("ocp_clipping_tolerance", D(".001"))])
def test_independent_preparation_rejects_changed_scientific_operands(field, value):
    trace, operands = _prepared_fixture()
    operands["witness"] = replace(operands["witness"], **{field: value})
    result = science.assess_initial_preparation(trace, **_rejoin(trace, operands))
    assert result.disposition is A.FALSIFIED and result.reason_codes


@pytest.mark.parametrize("kind", [ObservationKind.DERIVED, ObservationKind.UNAVAILABLE])
def test_unavailable_or_derived_state_cannot_satisfy_an_observed_role(kind):
    trace, operands = _prepared_fixture()
    actual = operands["actual_initial"]
    operands["actual_initial"] = replace(actual, kind=kind, derivation=_id("derivation.fixture") if kind is ObservationKind.DERIVED else None,
        scaled_values=actual.scaled_values if kind is ObservationKind.DERIVED else (),
        binary64_hex=actual.binary64_hex if kind is ObservationKind.DERIVED else (),
        model_clock_s=D(0) if kind is ObservationKind.DERIVED else None)
    result = science.assess_initial_preparation(trace, **_rejoin(trace, operands))
    assert result.disposition is A.UNEVALUABLE and "required-full-initial-state-not-observed" in result.reason_codes


def test_unknown_initializer_is_not_reclassified_as_returned():
    trace, operands = _prepared_fixture()
    operands["witness"] = replace(operands["witness"], initializer_dispositions=("UNKNOWN_COMPLETION",))
    result = science.assess_initial_preparation(trace, **_rejoin(trace, operands))
    assert result.disposition is A.UNEVALUABLE and "initializer-completion-census-unresolved" in result.reason_codes


def test_foreign_trace_join_and_binary_representation_refuse():
    trace, operands = _prepared_fixture()
    operands["join"] = replace(operands["join"], producing_receipt_sha256="3" * 64, trace=_id("foreign.trace"))
    with pytest.raises(ValueError, match="exact configuration"):
        science.assess_initial_preparation(trace, **operands)
    actual = operands["actual_initial"]
    with pytest.raises(ValueError, match="binary64"):
        replace(actual, binary64_hex=(float(1).hex(),) + actual.binary64_hex[1:])


def test_preparation_is_cold_and_calls_no_native_initializer():
    code = '''
import importlib.abc, sys
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'pybamm', 'pybammsolvers'}:
            raise AssertionError('native import attempted: ' + fullname)
sys.meta_path.insert(0, Block())
from empirical_lawhood.adapters.methods.battery_refined_inquiry.preparation_science import source_root_enclosures
assert len(source_root_enclosures('ORegan2022')) == 2
'''
    completed = subprocess.run([sys.executable, "-c", code], text=True, capture_output=True)
    assert completed.returncode == 0, completed.stderr
    assert sha256(code.encode()).hexdigest()
