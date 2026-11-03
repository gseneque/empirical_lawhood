# SPDX-License-Identifier: MPL-2.0
"""Exposed software/scientific conformance of explicit RC phase boundaries."""

from dataclasses import fields, replace
from decimal import Decimal

import pytest

from empirical_lawhood.adapters.methods.rc_prerequisite_chain import operations, science
from empirical_lawhood.adapters.methods.rc_prerequisite_chain import operation_contracts as records
from empirical_lawhood.adapters.methods.rc_prerequisite_chain.operation_bindings import assessment_projector, operation_manifests, operation_registrations, output_codecs
from empirical_lawhood.adapters.methods.rc_prerequisite_chain.recursive_translation import rc_recursive_draft
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan, DevelopmentRunPlan
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave


def phases(config, unit_id):
    source, export = operations.acquire_source(records.RCSourceOperationConfig("config.source", config, unit_id))
    policy = (config.fingerprint(), unit_id, config.protocol)
    reports = operations.construct_observations(records.RCObservationOperationConfig("config.reports", *policy), export)
    admitted = operations.admit_observations(records.RCAdmissionOperationConfig("config.admit", *policy), reports)
    committed = operations.commit_preparations(records.RCCommitmentOperationConfig("config.commit", *policy), reports, admitted)
    native = operations.deliver_phases(records.RCDeliveryOperationConfig("config.deliver", config, unit_id), committed)
    measured = operations.assess_measurement(records.RCMeasurementOperationConfig("config.measure", config, unit_id), source, reports, committed)
    support = operations.assess_support(records.RCSupportOperationConfig("config.support", config, unit_id), measured, committed, native)
    joined = operations.assess_joined(records.RCJoinedOperationConfig("config.joined", config, unit_id), measured, committed, native, support)
    result = operations.reduce_unit(records.RCUnitReductionConfig("config.reduce", config, unit_id), source, reports, committed, measured, support, joined)
    return result, committed, native, measured, support


def test_explicit_phases_preserve_exact_original_unit_bytes_and_negative_assurances(monkeypatch):
    config = science.default_chain_config()
    unit = next(value for value in config.units if value.initial_voltage_volts == Decimal("0.4"))
    original = science.evaluate_unit(config, unit.unit_id)
    monkeypatch.setattr(science, "evaluate_unit", lambda *_: (_ for _ in ()).throw(AssertionError("whole-unit evaluator called")))
    result, committed, native, measured, support = phases(config, unit.unit_id)
    assert result.canonical_bytes() == original.canonical_bytes()
    assert len(committed.decisions) == 10 and len(native.arms) == 13
    biased = next(value for value in measured.assessments if value.variant_id == "biased")
    assert biased.state == "FAILED"
    insufficient = next(value for value in support.assessments if (value.variant_id, value.arm_id) == ("adequate", "insufficient"))
    arm = next(case for case in result.cases if case.variant_id == "adequate").arms[0]
    assert insufficient.actual_support is False and arm.endpoint_within_task is True and arm.joined_state != "PASSED"


def test_policy_has_truth_free_inputs_and_all_choices_precede_oracle(monkeypatch):
    config = science.default_chain_config()
    unit = config.units[0]
    committed_count = []
    original_decide, original_oracle = science.decide_preparation, science._scalar_state
    def decide(*args):
        value = original_decide(*args)
        committed_count.append(value)
        return value
    first_oracle = []
    def oracle(*args):
        if not first_oracle:
            assert len(committed_count) == 10
            first_oracle.append(True)
        assert len(committed_count) >= 10
        return original_oracle(*args)
    monkeypatch.setattr(science, "decide_preparation", decide)
    monkeypatch.setattr(science, "_scalar_state", oracle)
    result, *_ = phases(config, unit.unit_id)
    assert len(result.cases) == 10
    assert tuple(field.name for field in fields(records.RCCommitmentOperationConfig)) == (
        "config_id", "scientific_config_sha256", "unit_id", "protocol")
    registration = next(value for value in operation_registrations() if value.config_record_type is records.RCCommitmentOperationConfig)
    assert {value.payload_schema for value in registration.input_ports} == {records.RCAdmissionSet.SCHEMA, records.RCObservationSet.SCHEMA}


def test_rc_graph_is_explicit_bounded_and_early_slice_retains_original_config():
    config = science.default_chain_config()
    registry = CapabilityRegistry("registry.rc-phases", tuple(sorted(operation_manifests(), key=lambda value: value.registry_id)))
    draft = rc_recursive_draft(config)
    compiled = compile_recursive_wave(draft=draft, registrations=operation_registrations(), registry=registry,
        implementation_commit="a" * 40, output_codecs=output_codecs())
    assert len(draft.operations) == len(compiled.execution_plan.tasks) == 100
    assert len(draft.requirements) == len(draft.connections) == 33
    assert isinstance(compiled.run_plan, DevelopmentRunPlan) and isinstance(compiled.execution_plan, DevelopmentExecutionPlan)
    assert not hasattr(compiled.run_plan, "authorization")
    for task in compiled.execution_plan.tasks:
        assert task.maximum_attempts == 1
        assert "evaluate_unit" not in task.capability.capability_key
    early = rc_recursive_draft(config, unit_ids=(config.units[0].unit_id,), include_summary=False)
    assert len(early.operations) == 9 and early.development_study.assigned_unit_ids == (config.units[0].unit_id,)
    source = next(value for value in early.operations if value.node_id.endswith(".source"))
    restored = decode_canonical_bytes(source.config_payload.encode(), records.RCSourceOperationConfig, maximum_bytes=16*1024**2)
    assert restored.scientific_config.canonical_bytes() == config.canonical_bytes()
    with pytest.raises(ValueError, match="complete original"):
        rc_recursive_draft(config, unit_ids=(config.units[0].unit_id,))


def test_retained_phase_tampering_cannot_rewrite_committed_scientific_projection():
    config = science.default_chain_config()
    result, committed, native, measured, support = phases(config, config.units[1].unit_id)
    changed = replace(support, commitment_sha256="0" * 64)
    with pytest.raises(ValueError, match="substituted support"):
        operations.assess_joined(records.RCJoinedOperationConfig("config.joined", config, result.unit_id), measured, committed, native, changed)


def test_precontact_compiler_refuses_a_coherent_scientific_root_substitution(monkeypatch):
    config = science.default_chain_config()
    draft = rc_recursive_draft(config, unit_ids=(config.units[0].unit_id,), include_summary=False)
    source = next(value for value in draft.operations if value.node_id.endswith(".source"))
    old = decode_canonical_bytes(source.config_payload.encode(), records.RCSourceOperationConfig, maximum_bytes=16*1024**2)
    changed_config = replace(config, config_id="changed.scientific-design")
    replacement = replace(old, scientific_config=changed_config)
    changed_op = replace(source, config_payload=replacement.canonical_bytes().decode())
    changed = replace(draft, operations=tuple(changed_op if value.node_id == source.node_id else value for value in draft.operations))
    monkeypatch.setattr(science, "_execute", lambda *_: (_ for _ in ()).throw(AssertionError("native contact")))
    registry = CapabilityRegistry("registry.rc-phases", tuple(sorted(operation_manifests(), key=lambda value: value.registry_id)))
    with pytest.raises(ValueError, match="scientific operand"):
        compile_recursive_wave(draft=changed, registrations=operation_registrations(), registry=registry,
            implementation_commit="a" * 40, output_codecs=output_codecs())


def test_shared_supply_projection_keeps_every_nested_result_and_actual_evidence():
    from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition, AssessmentPhase
    config = science.default_chain_config()
    unit = next(value for value in config.units if value.initial_voltage_volts == Decimal("0.4"))
    result, committed, native, measured, support = phases(config, unit.unit_id)
    joined = operations.assess_joined(records.RCJoinedOperationConfig("config.joined", config, unit.unit_id), measured, committed, native, support)
    draft = rc_recursive_draft(config, unit_ids=(unit.unit_id,), include_summary=False)
    outputs = {"m": measured, "p": support, "j": joined}
    for tag, product in outputs.items():
        requirement = next(value for value in draft.requirements if value.requirement_id.endswith("."+tag))
        connection = next(value for value in draft.connections if value.requirement_id == requirement.requirement_id)
        projected = assessment_projector(product, requirement, connection)
        assert len(projected) == (10 if tag == "m" else 13)
        assert len({value.assessment_id for value in projected}) == len(projected)
        assert {value.instance_id for value in projected} == {unit.unit_id}
        assert all(value.evidence[0].object_fingerprint == product.fingerprint() for value in projected)
        assert {value.phase for value in projected} == {AssessmentPhase.JOINED if tag == "j" else AssessmentPhase.INSTANCE}
        assert any(value.disposition is AssessmentDisposition.FALSIFIED for value in projected)


def test_materials_partial_has_distinct_subjects_no_physical_supplier_and_no_native():
    from empirical_lawhood.adapters.composition.recursive_examples import materials_partial_draft, rc_scientific_examples
    from empirical_lawhood.planning.recursive_authoring import explain_recursive_draft
    draft = materials_partial_draft()
    explanation = explain_recursive_draft(draft)
    assert explanation["scientific_root"] == "UNSELECTED" and not draft.selected_operation_ids
    assert len(draft.requirements) == len(draft.suppliers) == 6
    assert all(not value.selected and value.unavailable_reason_codes for value in draft.suppliers)
    assert len({value.scope.system_id for value in draft.requirements}) == 3
    assert draft.unresolved_decisions and not draft.connections and not draft.operations
    assert tuple(rc_scientific_examples()) == ("original", "menu-v2", "budget-v3")


def test_second_view_failure_retains_first_raw_view_and_complete_unevaluable_census(monkeypatch):
    from empirical_lawhood.adapters.simulators.rc_ladder_response import campaign
    config = science.default_chain_config()
    original = campaign.run_native_view
    calls = []
    def fail_second(study, view):
        calls.append(view)
        if view == "matrix-exponential":
            raise RuntimeError("declared numerical failure")
        return original(study, view)
    monkeypatch.setattr(campaign, "run_native_view", fail_second)
    unit_id = config.units[0].unit_id
    source, exported = operations.acquire_source(records.RCSourceOperationConfig("config.source", config, unit_id))
    assert calls == ["backward-euler", "matrix-exponential"]
    assert len(source.native_panels) == 1 and source.failure_reason_codes == ("NUMERICAL_EXECUTION_FAILED",)
    assert exported.observed_sample_volts is None
    policy = (config.fingerprint(), unit_id, config.protocol)
    reports = operations.construct_observations(records.RCObservationOperationConfig("config.reports", *policy), exported)
    admissions = operations.admit_observations(records.RCAdmissionOperationConfig("config.admit", *policy), reports)
    committed = operations.commit_preparations(records.RCCommitmentOperationConfig("config.commit", *policy), reports, admissions)
    native = operations.deliver_phases(records.RCDeliveryOperationConfig("config.deliver", config, unit_id), committed)
    measured = operations.assess_measurement(records.RCMeasurementOperationConfig("config.measure", config, unit_id), source, reports, committed)
    support = operations.assess_support(records.RCSupportOperationConfig("config.support", config, unit_id), measured, committed, native)
    joined = operations.assess_joined(records.RCJoinedOperationConfig("config.joined", config, unit_id), measured, committed, native, support)
    result = operations.reduce_unit(records.RCUnitReductionConfig("config.reduce", config, unit_id), source, reports, committed, measured, support, joined)
    assert result == science.failed_unit_result(config, unit_id)
    assert len(measured.assessments) == 10 and len(support.assessments) == 13
    assert all(value.state == "UNEVALUABLE" for value in measured.assessments)
    assert calls == ["backward-euler", "matrix-exponential"]
