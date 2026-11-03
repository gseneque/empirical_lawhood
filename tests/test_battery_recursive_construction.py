"""Independent falsifiers for exposed SPMe construction, never qualification evidence."""

from dataclasses import replace
from decimal import Decimal, localcontext
import json
import struct
import subprocess
import sys

import pytest

from empirical_lawhood.adapters.methods.battery_recursive_construction import science
from empirical_lawhood.adapters.methods.battery_recursive_construction.contracts import (
    BatteryCheckpoint, BatteryOperation, BatteryOperationConfig, BatterySourceContract, BatteryTrace,
)
from empirical_lawhood.adapters.methods.battery_recursive_construction.examples import (
    _pair, battery_wave_a_draft, battery_wave_b_draft,
)
from empirical_lawhood.adapters.methods.battery_recursive_construction.executable_binding import (
    operation_declarations, operation_manifests, operation_registrations, output_codecs,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as State, AssessmentPhase, ContributionRole
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.scientific_contributions import ContributionManifest, ContributionProduct
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave

D = Decimal


def _checkpoint(wave="A", history="early"):
    return BatteryCheckpoint(f"test.{wave.lower()}.{history}.checkpoint", BatterySourceContract(),
                             f"battery-preparation-{wave.lower()}", history, D("0.60") if wave == "A" else D("0.70"),
                             D(300), D("0.041666666666666666666666666666666666666666666666667"), D("293.15"),
                             D(0) if history == "early" else D(1),
                             (("Ambient temperature [K]", D("293.15")), ("Current function [A]", D(0) if history == "early" else D(1))),
                             "a" * 64, "b" * 64, struct.pack("<d", 1.0).hex(), 2)


def _config(operation, wave="A", history="early", word="hold", manifest=None):
    node = f"test.{wave.lower()}.{history}.{word}.{operation.value.lower()}"
    pair = _pair(f"{node}.requirement", node, f"{node}.supplier", "checkpoint", node, wave,
                 "Actual declared supply retains its exact state, clocks and channels.", "Missing or substituted channels or failed frozen numerical criterion.")
    return BatteryOperationConfig(f"{node}.config", operation, wave, history, word,
                                   requirement=pair[0], connection=pair[1], contribution_sha256=None if manifest is None else manifest.fingerprint())


def _trace(checkpoint, route, word="hold", *, voltages=None):
    clocks = tuple(D(t) for t in range(300, 601, 10))
    currents = {"hold": (0, 0), "early1": (1, 0), "late1": (0, 1), "early3": (3, 0)}[word]
    # Independently integrate the declared piecewise constant current; do not
    # mirror the production expected_capacity helper in this falsifier.
    with localcontext() as context:
        context.prec = 50
        capacity = tuple(checkpoint.capacity_Ah + (D(currents[0]) * D(max(0, min(int(t), 420) - 300)) +
                         D(currents[1]) * D(max(0, min(int(t), 540) - 420))) / D(3600) for t in clocks)
    return BatteryTrace(f"{checkpoint.checkpoint_id}.{word}.{route.lower()}", science.identity(checkpoint),
                        checkpoint.unit_id, checkpoint.history, word, route, "tighter" if route == "TIGHTER" else "coarse",
                        clocks, tuple(D(4) for _ in clocks) if voltages is None else tuple(voltages), capacity,
                        tuple(D("293.15") for _ in clocks), route != "SOC", True, (), 5 if route == "REFERENCE" else 3, checkpoint.source)


def _a_products():
    checkpoints, assessments = [], []
    for history in ("early", "late"):
        checkpoint = _checkpoint(history=history)
        traces = [_trace(checkpoint, route) for route in ("REFERENCE", "FULL", "SOC")]
        checkpoints.append(checkpoint)
        assessments.append(science.assess_restart(_config(BatteryOperation.ASSESS, history=history), checkpoint, *traces))
    procedure = science.construct_procedure(_config(BatteryOperation.PROCEDURE), tuple(checkpoints), tuple(assessments))
    return checkpoints, assessments, procedure


def _test_manifest(procedure):
    # This exposed test reference has no signer or authority and is never used
    # by the public contribution import service as authenticated evidence.
    product = ContributionProduct("test.procedure-product", science.identity(procedure),
                                  ArtifactIdentity("test.procedure-artifact", "test-fixture", procedure.SCHEMA,
                                                   procedure.fingerprint(), "application/json", len(procedure.canonical_bytes())),
                                  ObjectIdentity("test.unissued-receipt", "empirical-lawhood/runtime/canonical-task-receipt", "1.0.0", "c" * 64),
                                  ContributionRole.DESIGN_OPERAND, EvidenceCeiling.NON_PROMOTABLE,
                                  OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)
    return ContributionManifest("test.unissued-contribution", "Exposed test procedure.", procedure.finding,
                                procedure.scope, (product,), procedure.assessments, ())


def _b_products(*, null=False):
    _, _, procedure = _a_products()
    manifest = _test_manifest(procedure)
    checkpoint = _checkpoint("B")
    summary = science.project_checkpoint(checkpoint)
    c1 = science.admit_procedure(_config(BatteryOperation.ADMIT_C1, "B", manifest=manifest), manifest, procedure, summary)
    c2 = science.admit_procedure(_config(BatteryOperation.ADMIT_C2, "B", manifest=manifest), manifest, procedure, summary)
    traces, assessments = [], []
    for word in ("early1", "early3", "hold", "late1"):
        volts = [D(4)] * 31
        if not null:
            if word == "early1":
                volts[11], volts[-1] = D("3.95"), D("3.990")
            elif word == "late1":
                volts[-1] = D("3.996")
            elif word == "early3":
                volts[11] = D("3.70")
        reference, full, tighter = [_trace(checkpoint, route, word, voltages=volts) for route in ("REFERENCE", "FULL", "TIGHTER")]
        traces.extend((reference, full, tighter))
        assessments.append(science.assess_restart(_config(BatteryOperation.ASSESS, "B", word=word), checkpoint, reference, full))
    config = _config(BatteryOperation.VOLTAGE, "B", manifest=manifest)
    return config, checkpoint, c1, c2, tuple(traces), tuple(assessments)


def test_static_catalog_and_compilation_do_not_import_or_contact_pybamm():
    script = "from empirical_lawhood.adapters.methods.battery_recursive_construction.examples import battery_wave_a_draft; import sys; battery_wave_a_draft(); print('pybamm' in sys.modules)"
    assert subprocess.check_output([sys.executable, "-c", script], text=True).strip() == "False"
    manifests = operation_manifests()
    assert tuple(row.registry_id for row in manifests) == tuple(sorted(row.registry_id for row in manifests))
    assert manifests == tuple(sorted((row.manifest() for row in operation_declarations()), key=lambda row: row.registry_id))
    registry = CapabilityRegistry("test.battery", manifests)
    result = compile_recursive_wave(draft=battery_wave_a_draft(), registrations=operation_registrations(), registry=registry,
                                    implementation_commit="a" * 40, output_codecs=output_codecs())
    assert result.proof is not None
    assert len(result.execution_plan.tasks) == 11
    assert all(task.maximum_attempts == 1 for task in result.execution_plan.tasks)


def test_actual_parent_binding_compiles_new_checkpoint_and_changed_words():
    _, _, procedure = _a_products()
    manifest = _test_manifest(procedure)
    draft = battery_wave_b_draft(manifest, procedure)
    result = compile_recursive_wave(draft=draft, registrations=operation_registrations(),
                                    registry=CapabilityRegistry("test.battery", operation_manifests()),
                                    implementation_commit="a" * 40, output_codecs=output_codecs())
    assert result.proof is not None
    assert len(result.execution_plan.tasks) == 21
    assert draft.development_study.assigned_unit_ids == ("battery-preparation-b",)
    assert {i.expected_content_sha256 for i in draft.external_inputs} == {manifest.fingerprint(), procedure.fingerprint()}
    assert sum(op.selection.capability_key == "battery-recursive.checkpoint" for op in draft.operations) == 1


@pytest.mark.parametrize("change", [dict(mesh_points=21), dict(coarse_rtol=D("0.001")), dict(integrator_max_steps=0), dict(pybamm_version="other")])
def test_source_and_integrator_operands_are_frozen(change):
    with pytest.raises(ValueError, match="frozen protocol"):
        replace(BatterySourceContract(), **change)


def test_state_encoding_and_native_clock_census_refuse_nonfinite_or_missing_data():
    with pytest.raises(ValueError, match="nonfinite"):
        replace(_checkpoint(), state_hex=struct.pack("<d", float("nan")).hex())
    with pytest.raises(ValueError, match="missing assigned clocks"):
        trace = _trace(_checkpoint(), "FULL")
        replace(trace, clocks_seconds=trace.clocks_seconds[:-1], voltage_V=trace.voltage_V[:-1],
                capacity_Ah=trace.capacity_Ah[:-1], temperature_K=trace.temperature_K[:-1])


def test_source_input_vector_order_and_units_cannot_be_silently_swapped():
    checkpoint = _checkpoint()
    with pytest.raises(ValueError, match="exact sorted names, units and values"):
        replace(checkpoint, source_input_ledger=tuple(reversed(checkpoint.source_input_ledger)))
    with pytest.raises(ValueError, match="exact sorted names, units and values"):
        replace(checkpoint, source_input_ledger=(("Ambient temperature [K]", D(0)), ("Current function [A]", D("293.15"))))


def test_substituted_instance_or_capacity_is_refused_before_native_build(monkeypatch):
    monkeypatch.setattr(science, "_runtime", lambda *a, **k: pytest.fail("native build contacted"))
    config = _config(BatteryOperation.FULL)
    for changed in (replace(_checkpoint(), unit_id="other-instance"), replace(_checkpoint(), capacity_Ah=D(0))):
        with pytest.raises(ValueError, match="before contact"):
            science.continue_checkpoint(config, changed)


def test_full_fidelity_and_soc_voltage_adequacy_are_distinct_claims():
    cp = _checkpoint()
    reference, full, soc = [_trace(cp, route) for route in ("REFERENCE", "FULL", "SOC")]
    adequate = science.assess_restart(_config(BatteryOperation.ASSESS), cp, reference, full, soc)
    assert adequate.supply.disposition is State.SATISFIED
    assert adequate.soc_disposition == "ADEQUATE_WITHIN_TESTED_SCOPE"
    soc = replace(soc, voltage_V=(D(4), *(D("4.002") for _ in range(30))))
    inadequate = science.assess_restart(_config(BatteryOperation.ASSESS), cp, reference, full, soc)
    assert inadequate.supply.disposition is State.SATISFIED
    assert inadequate.soc_disposition == "INADEQUATE"
    bad_full = replace(full, voltage_V=(D(4), *(D("4.000002") for _ in range(30))))
    failed = science.assess_restart(_config(BatteryOperation.ASSESS), cp, reference, bad_full, soc)
    assert failed.supply.disposition is State.FALSIFIED
    assert "FULL_RESTART_VOLTAGE_DEFECT" in failed.supply.reason_codes


def test_current_integral_control_cannot_be_replaced_by_equal_voltage():
    cp = _checkpoint()
    reference, full = [_trace(cp, route) for route in ("REFERENCE", "FULL")]
    full = replace(full, capacity_Ah=tuple(D(0) for _ in full.capacity_Ah))
    result = science.assess_restart(_config(BatteryOperation.ASSESS), cp, reference, full)
    assert result.maximum_voltage_error_V == 0
    assert result.supply.disposition is State.FALSIFIED
    assert not result.capacity_control_passed


def test_failed_soc_alternative_does_not_falsify_a_faithful_full_procedure():
    cp = _checkpoint()
    reference, full, soc = [_trace(cp, route) for route in ("REFERENCE", "FULL", "SOC")]
    soc = replace(soc, capacity_Ah=tuple(D(0) for _ in soc.capacity_Ah))
    result = science.assess_restart(_config(BatteryOperation.ASSESS), cp, reference, full, soc)
    assert result.supply.disposition is State.SATISFIED
    assert result.soc_disposition == "UNEVALUABLE"
    assert result.soc_capacity_control_passed is False


def test_nonfinite_native_output_retains_the_returned_finite_prefix(monkeypatch):
    cp = _checkpoint()
    config = _config(BatteryOperation.FULL)
    class NativeSolution:
        t = [300, 600]
    def scalar(solution, variable, time):
        if time >= D(330):
            raise ValueError("nonfinite native quantity")
        return {"Terminal voltage [V]": D(4), "Discharge capacity [A.h]": cp.capacity_Ah,
                "Volume-averaged cell temperature [K]": D("293.15")}[variable]
    monkeypatch.setattr(science, "_scalar", scalar)
    result = science._trace(config, cp, NativeSolution(), True, True, (), 3)
    assert result.clocks_seconds == (D(300), D(310), D(320))
    assert not result.completed and result.reason_codes == ("NATIVE_INVALID_QUANTITY",)


def test_both_assigned_histories_are_required_for_procedure():
    checkpoints, assessments, _ = _a_products()
    with pytest.raises(ValueError, match="actual assigned checkpoints"):
        science.construct_procedure(_config(BatteryOperation.PROCEDURE), tuple(checkpoints), (assessments[0], assessments[0]))


def test_shared_supplier_admission_is_consumer_specific_and_state_free(monkeypatch):
    _, cp, c1, c2, _, _ = _b_products()
    summary = science.project_checkpoint(cp)
    assert not hasattr(summary, "state_hex")
    assert c1.supply.phase is AssessmentPhase.ADMISSION and c1.supply.disposition is State.SATISFIED
    assert c2.supply.disposition is State.REFUSED
    assert c2.supply.reason_codes == ("REQUIRED_LATENT_CHANNEL_FORBIDDEN",)
    monkeypatch.setattr(science, "source_preflight", lambda *a: pytest.fail("source/native contact after refusal"))
    declined = science.continue_checkpoint(_config(BatteryOperation.FULL, "B"), cp, c2)
    assert not declined.completed and declined.native_phase_calls == 0


def test_distinct_further_voltage_product_preserves_actual_contrasts_and_denominators():
    config, _, c1, c2, traces, assessments = _b_products()
    result = science.assess_voltage(config, c1, c2, traces, assessments)
    assert result.c1_path_disposition is State.SATISFIED
    assert result.c1_c2_joint_disposition is State.REFUSED
    assert result.assigned_unit_ids == ("battery-preparation-b",)
    assert len(result.trace_census) == 12 and len(result.restart_assessment_census) == 4
    values = {r.contrast_id: r for r in result.contrast_results}
    assert values["current-proportionality"].coarse_V == D("-0.15")
    assert values["equal-charge-history"].coarse_V == D("-0.006")
    assert all(r.finding == "RESOLVED_NEGATIVE" for r in result.contrast_results)


def test_null_voltage_findings_are_successful_assessed_development_products():
    config, _, c1, c2, traces, assessments = _b_products(null=True)
    result = science.assess_voltage(config, c1, c2, traces, assessments)
    assert result.c1_path_disposition is State.SATISFIED
    assert all(r.finding == "BOUNDED_NULL_OR_NONDISCRIMINATING" for r in result.contrast_results)


def test_missing_nested_control_and_tighter_capacity_failure_are_preserved():
    config, _, c1, c2, traces, assessments = _b_products()
    with pytest.raises(ValueError, match="missing or duplicates"):
        science.assess_voltage(config, c1, c2, traces[:-1], assessments)
    traces = tuple(replace(t, capacity_Ah=tuple(D(0) for _ in t.capacity_Ah)) if t.route == "TIGHTER" else t for t in traces)
    result = science.assess_voltage(config, c1, c2, traces, assessments)
    assert result.c1_path_disposition is State.FALSIFIED
    assert "FORWARD_CURRENT_INTEGRAL_CONTROL_FAILED" in result.reason_codes
    assert all(r.finding == "UNEVALUABLE" for r in result.contrast_results)


def test_unavailable_contrast_is_absent_rather_than_a_fabricated_zero():
    config, _, c1, c2, traces, assessments = _b_products()
    traces = tuple(replace(t, clocks_seconds=(), voltage_V=(), capacity_Ah=(), temperature_K=(), completed=False,
                           reason_codes=("NATIVE_STOP",), native_phase_calls=0) if t.route == "TIGHTER" else t for t in traces)
    result = science.assess_voltage(config, c1, c2, traces, assessments)
    assert result.c1_path_disposition is State.UNEVALUABLE
    assert all(r.tighter_V is None and r.coarse_V is not None and r.finding == "UNEVALUABLE" for r in result.contrast_results)


def test_decimal_context_does_not_change_the_scientific_reducer():
    config, _, c1, c2, traces, assessments = _b_products()
    expected = science.assess_voltage(config, c1, c2, traces, assessments)
    with localcontext() as ctx:
        ctx.prec = 3
        actual = science.assess_voltage(config, c1, c2, traces, assessments)
    assert actual == expected
    assert decode_canonical_bytes(actual.canonical_bytes(), type(actual), maximum_bytes=4 * 1024**2) == actual


@pytest.mark.native("pybamm")
def test_native_checkpoint_full_state_restart_and_soc_bookkeeping():
    """Actual simulator conformance with no fabricated qualification product."""
    cp = science.capture_checkpoint(_config(BatteryOperation.CHECKPOINT))
    reference = science.continue_checkpoint(_config(BatteryOperation.REFERENCE), cp)
    full = science.continue_checkpoint(_config(BatteryOperation.FULL), cp)
    soc = science.continue_checkpoint(_config(BatteryOperation.SOC), cp)
    result = science.assess_restart(_config(BatteryOperation.ASSESS), cp, reference, full, soc)
    print(json.dumps({"scientific_disposition": result.supply.disposition.value,
                      "reason_codes": result.supply.reason_codes,
                      "full_voltage_error_V": str(result.maximum_voltage_error_V),
                      "full_capacity_error_Ah": str(result.maximum_capacity_error_Ah),
                      "full_temperature_error_K": str(result.maximum_temperature_error_K),
                      "routes": [{"route": t.route, "temperature_range_K": [str(min(t.temperature_K)), str(max(t.temperature_K))],
                                  "voltage_boundary_V": [str(t.voltage_V[0]), str(t.voltage_V[-1])],
                                  "capacity_boundary_Ah": [str(t.capacity_Ah[0]), str(t.capacity_Ah[-1])]} for t in (reference, full, soc) if t.completed]}, sort_keys=True))
    assert reference.completed and full.completed and soc.completed, json.dumps([t.reason_codes for t in (reference, full, soc)])
    assert full.exact_state_roundtrip
    assert result.supply.disposition is State.SATISFIED
    assert result.capacity_control_passed and result.temperature_control_passed
    # Preserve either scientifically possible SOC-only outcome; do not force a
    # negative result merely to meet an architectural example acceptance gate.
    assert result.soc_disposition in {"INADEQUATE", "ADEQUATE_WITHIN_TESTED_SCOPE"}
    print(json.dumps({"development_conformance_only": True, "assigned_preparation": cp.unit_id,
                      "checkpoint_sha256": cp.fingerprint(), "assessment_sha256": result.fingerprint(),
                      "full_voltage_error_V": str(result.maximum_voltage_error_V),
                      "full_capacity_error_Ah": str(result.maximum_capacity_error_Ah),
                      "full_temperature_error_K": str(result.maximum_temperature_error_K),
                      "soc_voltage_error_V": str(result.soc_maximum_voltage_error_V),
                      "soc_disposition": result.soc_disposition,
                      "native_phase_calls": cp.native_phase_calls + sum(t.native_phase_calls for t in (reference, full, soc))}, sort_keys=True))
