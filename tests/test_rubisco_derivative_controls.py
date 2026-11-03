# SPDX-License-Identifier: MPL-2.0
"""Exposed total-Hamiltonian derivatives; no molecular task or native engine."""
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
import gzip
import io
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_free_energy import (
    derivative_controls as d, derivative_native as seam, prospective_xtb as x, raw_coupled_return as raw,
)
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.runtime.artifacts import ArtifactWriteRequest
from tests.runtime_platform.test_native_subwork import _plane
from tests.test_rubisco_rr_qmmm_xtb import native_capture, original_inputs

D = Decimal


def identity(name):
    schema = "empirical-lawhood/kernel/numerical-producing-provenance" if name.startswith("producing.") else "empirical-lawhood/tests/exposed-derivative-input"
    return ObjectIdentity(name, schema, "1.0.0", "a"*64)


@pytest.fixture
def protocol():
    profile = d.PointFieldHamiltonian("profile.exposed.point-field", (identity("source.exposed"),),
        identity("stock.exposed"), identity("terms.exposed"), "SYNTHETIC_ETHANE_CONTROL")
    baseline = d.CartesianPoint("point.exposed.baseline", ("amber:1", "amber:2"),
        tuple(tuple(value.hex() for value in row) for row in ((0.5, 0.0, -0.0), (1.0, -0.5, 0.25))))
    return d.DerivativeProtocol("derivatives.exposed", profile, identity("material.exposed"), baseline,
        ("BOUNDARY_QM", "BOUNDARY_MM"), D("0.01"), D("1e-10"), D("1e-10"), D("1e-10"), D("1e-10"), identity("producing.exposed"), identity("retained.c4"))


@pytest.fixture
def publisher(tmp_path):
    plane = _plane(tmp_path / "exposed.derivatives")
    class Port:
        calls = []
        def publish_output(self, entry, output_id, chunks, **limits):
            spec = next(row for row in entry.definition.outputs if row.output_id == output_id)
            payload = b"".join(chunks)
            assert len(payload) == limits['expected_size_bytes']
            assert sha256(payload).hexdigest() == limits['expected_physical_sha256']
            artifact = entry.definition.configuration.object_id + "." + output_id
            result = plane.write(ArtifactWriteRequest(artifact, "outputs/"+artifact+".bin", spec.payload_schema,
                spec.profile, spec.media_type, "exposed.derivatives", "outputs", payload,
                VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
            self.calls.append((output_id, len(payload)))
            return decode_artifact_manifest(plane.root.resolve(result.materialization.relative_path+".manifest.json", for_write=False).read_bytes())
    def reader(manifest):
        plane.verify_manifest(manifest)
        return plane.root.resolve(manifest.materialization.relative_path, for_write=False).open("rb")
    return SimpleNamespace(port=Port(), reader=reader)


def entry_for(request):
    return SimpleNamespace(definition=SimpleNamespace(configuration=request.identity,
        sources=(request.protocol, request.prepared_material, request.physical_coordinates, request.producing_provenance),
        outputs=raw.return_outputs()))


def outcomes(protocol, publisher, *, mutate=lambda ordinal, point, energy, gradient: (energy, gradient), power=2):
    result = []
    for ordinal, point in enumerate(d.control_points(protocol)):
        coords = np.asarray([[float.fromhex(token) for token in row] for row in point.coordinates_angstrom_hex])
        energy = np.sum(coords**power)/power
        gradient = coords**(power-1)*float(d.ASH_ANGSTROM_PER_BOHR)
        energy, gradient = mutate(ordinal, point, energy, gradient)
        request = d.request_for_point(protocol, point, producing_provenance=identity("producing.exposed"))
        returned = d.evaluate_then_capture(request, lambda e=energy, g=gradient: (e, g), publisher.port, entry_for(request))
        result.append(d.DerivativeOutcome(request, "RETURNED", returned, "DISCLOSED_EXPOSED_FUNCTION_RETURN"))
    return tuple(result)


def assess(protocol, rows, publisher):
    return d.assess_derivative_control(protocol, rows, publisher.reader, assessor_source=identity("assessor.exposed"), assessment_id="assessment.exposed")


def test_complete_qm_mm_boundary_h_and_half_h_quadratic(protocol, publisher):
    rows = outcomes(protocol, publisher)
    report = assess(protocol, rows, publisher)
    assert len(rows) == 25 and len(report.components) == 6
    assert report.disposition is A.SATISFIED
    assert all(row.disposition is A.SATISFIED for row in report.components)
    assert {row.physical_role for row in report.components} == {"BOUNDARY_QM", "BOUNDARY_MM"}
    assert report.physical_reference_adequacy is report.chemical_state_adequacy is report.kinetic_prediction is A.UNEVALUABLE
    assert d.validate_derivative_assessment(report, protocol, publisher.reader) == report


def test_absolute_only_protocol_preserves_unchanged_absolute_gates_and_full_reduction(protocol, publisher):
    protocol = replace(protocol, gradient_relative_tolerance=D(0), refinement_relative_tolerance=D(0))
    assert protocol.VERSION == "1.1.0"
    assert protocol.gradient_absolute_tolerance_eh_per_angstrom == D("1e-10")
    report = assess(protocol, outcomes(protocol, publisher), publisher)
    assert report.disposition is A.SATISFIED and len(report.outcomes) == 25 and len(report.components) == 6
    assert d.validate_derivative_assessment(report, protocol, publisher.reader) == report


@pytest.mark.parametrize("field", ["gradient_relative_tolerance", "refinement_relative_tolerance"])
@pytest.mark.parametrize("value", [D("-1e-50"), D("NaN"), D("Infinity"), 0])
def test_relative_operand_requires_finite_nonnegative_exact_decimal(protocol, field, value):
    with pytest.raises(ValueError, match="nonnegative finite Decimal"):
        replace(protocol, **{field: value})


@pytest.mark.parametrize("field", ["displacement_angstrom", "gradient_absolute_tolerance_eh_per_angstrom", "refinement_absolute_tolerance_eh_per_angstrom"])
def test_absolute_only_support_keeps_absolute_and_displacement_strictly_positive(protocol, field):
    with pytest.raises(ValueError, match="positive finite Decimal"):
        replace(protocol, **{field: D(0)})


def test_wrong_mm_boundary_gradient_falsifies_independent_total_energy(protocol, publisher):
    def mutate(ordinal, point, energy, gradient):
        if ordinal == 0:
            gradient = gradient.copy(); gradient[1, 1] *= -1
        return energy, gradient
    report = assess(protocol, outcomes(protocol, publisher, mutate=mutate), publisher)
    assert report.disposition is A.FALSIFIED
    assert report.components[4].physical_role == "BOUNDARY_MM"
    assert report.components[4].gradient_scaled_error > 1


def test_quartic_displacement_refinement_can_fail_with_finite_complete_returns(protocol, publisher):
    protocol = replace(protocol, gradient_absolute_tolerance_eh_per_angstrom=D("0.1"), gradient_relative_tolerance=D("0.1"))
    report = assess(protocol, outcomes(protocol, publisher, power=4), publisher)
    assert all(state is A.SATISFIED for _, state in report.numerical_integrity)
    assert report.disposition is A.FALSIFIED
    assert any(row.refinement_scaled_error > 1 for row in report.components)


@pytest.mark.parametrize("state", ["NOT_ENTERED", "UNKNOWN", "KNOWN_FAILURE"])
def test_missing_adverse_and_unknown_rows_remain_in_complete_denominator(protocol, publisher, state):
    rows = list(outcomes(protocol, publisher))
    rows[1] = d.DerivativeOutcome(rows[1].request, state, None, "EXACT_ORIGINAL_MISSING_OUTCOME")
    report = assess(protocol, tuple(rows), publisher)
    assert len(report.outcomes) == 25 and report.outcomes[1].contact_state == state
    assert report.disposition is A.UNEVALUABLE and report.components[0].disposition is A.UNEVALUABLE
    with pytest.raises(ValueError, match="denominator"):
        assess(protocol, tuple(rows[1:]), publisher)


@pytest.mark.parametrize("dtype, expected", [(np.float32, A.UNSUPPORTED), (np.complex128, A.UNSUPPORTED)])
def test_actual_dtype_is_preserved_and_cannot_be_cast_into_positive(protocol, publisher, dtype, expected):
    report = assess(protocol, outcomes(protocol, publisher, mutate=lambda i,p,e,g: (e, g.astype(dtype))), publisher)
    assert report.disposition is A.UNEVALUABLE
    assert report.numerical_integrity[0][1] is expected
    assert all(row.disposition is A.UNEVALUABLE for row in report.components)
    if len(report.reason_codes) > 1:
        with pytest.raises(ValueError, match="reason census"):
            replace(report, reason_codes=tuple(reversed(report.reason_codes)))


def test_nonfinite_original_return_captured_then_falsified(protocol, publisher):
    rows = outcomes(protocol, publisher, mutate=lambda i,p,e,g: (float("nan") if i == 0 else e, g))
    assert rows[0].returned.energy is not None
    report = assess(protocol, rows, publisher)
    assert report.disposition is A.FALSIFIED and report.numerical_integrity[0][1] is A.FALSIFIED


@pytest.mark.parametrize("gradient_error, refinement_error, state", [
    ("-0.1", "0", A.SATISFIED), ("0", "-0.1", A.FALSIFIED),
    ("1.0000000000000000000000000000000000000001", "0", A.SATISFIED),
    ("0", "1.0000000000000000000000000000000000000001", A.SATISFIED),
    ("1", "1", A.FALSIFIED), ("NaN", "0", A.SATISFIED),
])
def test_immutable_component_forbids_negative_nonfinite_and_false_gate_dispositions(gradient_error, refinement_error, state):
    with pytest.raises(ValueError):
        d.DerivativeComponent("amber:1", 0, "BOUNDARY_QM", D(0), D(0), D(0),
            D(gradient_error), D(refinement_error), state)


@pytest.mark.parametrize("missing_state", ["NOT_ENTERED", "UNKNOWN", "KNOWN_FAILURE"])
def test_immutable_assessment_forbids_false_satisfied_missing_outcomes_and_reason_loss(protocol, publisher, missing_state):
    rows = list(outcomes(protocol, publisher))
    rows[1] = d.DerivativeOutcome(rows[1].request, missing_state, None, "EXACT_ORIGINAL_MISSING_OUTCOME")
    report = assess(protocol, tuple(rows), publisher)
    with pytest.raises(ValueError, match="disposition contradicts"):
        replace(report, disposition=A.SATISFIED)
    with pytest.raises(ValueError, match="reason census"):
        replace(report, reason_codes=())
    with pytest.raises(ValueError, match="components or evaluation rows"):
        replace(report, outcomes=report.outcomes[1:], numerical_integrity=report.numerical_integrity[1:])


def test_immutable_assessment_forbids_false_negative_or_uncertain_native_and_component_joins(protocol, publisher):
    report = assess(protocol, outcomes(protocol, publisher), publisher)
    for state in (A.FALSIFIED, A.UNEVALUABLE, A.UNSUPPORTED):
        changed = ((report.numerical_integrity[0][0], state), *report.numerical_integrity[1:])
        with pytest.raises(ValueError, match="baseline/h/h2 native integrity"):
            replace(report, numerical_integrity=changed)
    component = report.components[0]
    falsified = replace(component, gradient_scaled_error=D("1.01"), disposition=A.FALSIFIED)
    with pytest.raises(ValueError, match="complete component/native outcomes"):
        replace(report, components=(falsified, *report.components[1:]))
    with pytest.raises(ValueError, match="baseline/h/h2 native integrity"):
        replace(report, components=(d.DerivativeComponent(component.atom_id, component.axis, component.physical_role,
            None, None, None, None, None, A.UNEVALUABLE), *report.components[1:]))


def test_immutable_adverse_reason_census_requires_sorted_complete_unique_codes(protocol, publisher):
    report = assess(protocol, outcomes(protocol, publisher, mutate=lambda i,p,e,g: (float("nan") if i == 0 else e, g)), publisher)
    with pytest.raises(ValueError, match="complete component/native outcomes"):
        replace(report, disposition=A.SATISFIED)
    for reasons in ((), (*report.reason_codes, *report.reason_codes), ("INVENTED_FAVOURABLE_REASON",)):
        with pytest.raises(ValueError, match="reason census"):
            replace(report, reason_codes=reasons)
    assert report.VERSION == "1.1.0"


def test_committed_point_and_output_refusal_precede_one_native_call(protocol, publisher):
    point = next(d.control_points(protocol)); request = d.request_for_point(protocol, point, producing_provenance=identity("producing.exposed"))
    called = []
    bad = entry_for(request); bad.definition.outputs = ()
    with pytest.raises(ValueError, match="committed"):
        d.evaluate_then_capture(request, lambda: called.append(True), publisher.port, bad)
    assert called == [] and publisher.port.calls == []
    with pytest.raises(ValueError, match="source/lock"):
        d.request_for_point(protocol, point, producing_provenance=identity("producing.substituted"))
    with pytest.raises(ValueError, match="selected protocol"):
        d.request_for_point(protocol, replace(point, coordinates_angstrom_hex=((1.0.hex(), 0.0.hex(), 0.0.hex()), point.coordinates_angstrom_hex[1])), producing_provenance=identity("producing.exposed"))


def test_second_raw_read_is_authenticated_and_producer_assessment_forgery_refuses(protocol, publisher):
    rows = outcomes(protocol, publisher); report = assess(protocol, rows, publisher)
    forged = replace(report, components=(replace(report.components[0], analytic_eh_per_angstrom=D(0)), *report.components[1:]))
    with pytest.raises(ValueError, match="authentic complete raw"):
        d.validate_derivative_assessment(forged, protocol, publisher.reader)
    capture = rows[0].returned.energy
    with publisher.reader(capture.artifact_manifest) as source:
        original = gzip.decompress(source.read())
    array = np.load(io.BytesIO(original), allow_pickle=False); array[...] += 1
    changed = io.BytesIO(); np.lib.format.write_array(changed, array, version=(2, 0), allow_pickle=False)
    with pytest.raises(ValueError, match="authentic complete raw custody"):
        d._raw_operand(capture, lambda manifest: io.BytesIO(gzip.compress(changed.getvalue())))


def theory():
    events = []
    def execute(plan):
        events.append("execute")
        class ExposedCaptureView:
            execution_id = "call-0001"
            def __getattr__(self, name): return getattr(plan, name)
        old = native_capture(ExposedCaptureView())
        fields = {name: getattr(old,name) for name in old.__dataclass_fields__}
        fields['execution_id'] = plan.execution_id
        return x.XtbSinglePointCaptureV2(**fields)
    def retain(plan, capture): events.append("retain")
    return x.StrictQmmmXtbTheoryV1(executable_path="/selected/bin/xtb", parameter_path="/selected/share/param_gfn2-xtb.txt", output_root="/selected/output", executor=execute, retain_capture=retain), events


def test_prospective_callback_has_no_operational_count_ceiling_preserves_scientific_scc():
    current, events = theory()
    current.callback_reservations = 120
    current.run(**original_inputs())
    assert current.callback_reservations == 121 and events == ["execute", "retain"]
    current.callback_reservations = 9999
    current.run(**original_inputs())
    assert current.last_observation.plan.execution_id == "call-10000"
    plan = current.last_observation.plan
    assert plan.model_id == x.MODEL_ID
    assert plan.model_id != "gfn2-xtb-6.7.1-hardness99-ash-single-point-v1"
    assert "--norestart" in plan.program_argv and "--grad" in plan.program_argv
    assert plan.binary_sha256 == x.BINARY_SHA256 and plan.parameter_sha256 == x.PARAMETER_SHA256


def test_prospective_raw_capture_over_old_byte_ceiling_is_retained_before_negative_guard():
    current, events = theory()
    previous = current.executor
    def execute(plan):
        capture = previous(plan)
        return replace(capture, stdout=capture.stdout+b" "*(16*1024*1024)+b"FAILED TO CONVERGE\n")
    current.executor = execute
    with pytest.raises(ValueError): current.run(**original_inputs())
    assert events == ["execute", "retain"] and current.callback_reservations == 1


def test_prospective_complete_native_atom_and_field_denominators_exceed_old_caps():
    atoms = tuple(x.NativeAtomV1("qm-"+str(i), "H", (D(0),D(0),D(0))) for i in range(101))
    plan = x.XtbSinglePointPlanV2("call-0001", "/selected/output/call-0001", "/selected/bin/xtb", "/selected/param", atoms, (), 0, 1, False)
    assert len(plan.atoms) == 101 and len(plan.coordinates_bohr) == 101
    field = tuple(x.NativeFieldRowV1("pc-"+str(i), (D(0),D(10),D(0)), Fraction(1,100)) for i in range(14001))
    embedded = x.XtbSinglePointPlanV2("call-0002", "/selected/output/call-0002", "/selected/bin/xtb", "/selected/param", atoms, field, 0, 1, True)
    assert len(embedded.field_rows) == len(embedded.native_field_ids) == 14001
    assert embedded.pcem_bytes.splitlines()[0] == b"14001"


def test_existing_ethane_constructor_seam_full_coordinates_profile_and_pre_guard_capture(tmp_path, publisher, monkeypatch):
    from empirical_lawhood.adapters.methods.rubisco_insilico_free_energy import native_coupling
    callback, _ = theory()
    original = np.arange(24,dtype=np.float64).reshape(8,3)/10
    prmtop = b"DISCLOSED_EXPOSED_ETHANE_SOURCE;NO_NATIVE_CONSTRUCTION"
    topology = tmp_path/"ethane-control.prmtop"; topology.write_bytes(prmtop)
    audit = dict(physical_atoms=8,real_qm_atoms=4,generated_links=1,qm_charge=0,
        derived_prmtop_sha256=sha256(prmtop).hexdigest(),
        classical_charge_policy="unshifted-source-MM;QM-particle-and-exception-zero",
        quantum_field_policy="ASH-CAcharge-shift-only;no-dipole-correction",expected_nonzero_point_charge_atoms=2,
        point_field_materialized=False,verified_callback_entries=0)
    calls = []
    class ExposedTheory:
        qm_theory = callback
        mm_theory = SimpleNamespace(system=object())
        def run(self, *, current_coords, Grad):
            calls.append(current_coords.copy()); assert Grad is True
            audit['point_field_materialized'] = True; audit['verified_callback_entries'] += 1
            return float(np.sum(current_coords**2)/2), current_coords*float(d.ASH_ANGSTROM_PER_BOHR)
    session = native_coupling.CouplingSession(ExposedTheory(), SimpleNamespace(coords=original), (3,4), (0,1,2,5,6,7),audit,tmp_path)
    constructor_calls = []
    def constructor(actual_callback, **kwargs):
        constructor_calls.append((actual_callback, kwargs)); return session
    monkeypatch.setattr(native_coupling, 'build_ethane_control', constructor)
    system_xml = '<System><Particles>'+''.join('<Particle mass="1"/>' for _ in range(8))+'</Particles><Forces><Force type="DISCLOSED_EXPOSED"/></Forces></System>'
    def serialize(actual):
        assert actual is session.theory.mm_theory.system
        return system_xml
    preparation, actual = seam.prepare_ethane_derivatives(callback, preparation_id="preparation.ethane.exposed",
        source_members=(identity("source.ethane.exposed"),),native_stock=identity("stock.exposed"),scratch_directory=tmp_path,protocol_sha256="b"*64,native_system_serializer=serialize)
    assert actual is session and len(constructor_calls) == 1
    profile = seam.profile_for_preparation(preparation,profile_id="profile.ethane.exposed")
    protocol = d.DerivativeProtocol("derivatives.ethane.exposed",profile,preparation.identity,preparation.baseline,
        preparation.physical_atom_roles,D("0.01"),D("1e-8"),D("1e-8"),D("1e-8"),D("1e-8"),identity("producing.exposed"))
    points = list(d.control_points(protocol)); assert len(points) == 97
    for point in points[:2]:
        request = d.request_for_point(protocol,point,producing_provenance=identity("producing.exposed"))
        returned = seam.evaluate_ethane_point(protocol,point,preparation,session,producing_provenance=identity("producing.exposed"),progress=publisher.port,entry=entry_for(request),native_system_serializer=serialize)
        assert returned.request == request.identity and returned.scientific_admission is A.NOT_ATTEMPTED
    assert len(calls) == 2 and calls[1][0,0] != calls[0][0,0]
    with pytest.raises(ValueError,match="Hamiltonian"):
        seam.evaluate_ethane_point(protocol,points[2],preparation,session,producing_provenance=identity("producing.exposed"),progress=publisher.port,entry=entry_for(request),
            native_system_serializer=lambda actual: system_xml.replace('DISCLOSED_EXPOSED','SUBSTITUTED_SAME_ATOM_CENSUS'))
    assert len(calls) == 2
    topology.write_bytes(b"SUBSTITUTED_NATIVE_TOPOLOGY")
    with pytest.raises(ValueError,match="topology bytes"):
        seam.evaluate_ethane_point(protocol,points[2],preparation,session,producing_provenance=identity("producing.exposed"),progress=publisher.port,entry=entry_for(request),native_system_serializer=serialize)
    assert len(calls) == 2
