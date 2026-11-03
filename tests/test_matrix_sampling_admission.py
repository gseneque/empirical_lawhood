# SPDX-License-Identifier: MPL-2.0
"""In-memory admission controls; synthetic gates establish no actual warrant."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256

import pytest

from empirical_lawhood.adapters.methods import matrix_sampling_assessment as owner
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.planning.metatheory import (
    MetatheoryAggregateDisposition as Aggregate, MetatheoryApplicability as Applicability,
    MetatheoryCellDisposition as Cell, MetatheoryEvidenceCeiling, MetatheoryMethodSelection,
)
from empirical_lawhood.planning.scientific_source_qualification import (
    ScientificSourceGateEvidence, ScientificSourceGateKind, ScientificSourceGateResult, ScientificSourceGateSpec,
    ScientificSourceInvalidUnitPolicy, ScientificSourceQualificationResult, ScientificSourceQualificationSpec,
)


def pin(name, schema="empirical-lawhood/testing/exposed-sampling-pin"):
    return ObjectIdentity(name, schema, "1.0.0", sha256(name.encode()).hexdigest())


def request_for(premise=owner.E3_COMPARISON, **changes):
    scope = owner.MatrixSamplingScope("scope.exposed.sampling", premise, pin("specification.original"),
        pin("population.original"), pin("source.original"), pin("map.original"),
        InformationCutoff("cutoff.freeze", "clock.original", CausalPhase.PREPARATION, Decimal(0)),
        InformationCutoff("cutoff.sample", "clock.original", CausalPhase.PRE_ACTION, Decimal(1)),
        ("unit.a", "unit.b"), ("unit.a",) if premise == owner.E3_CALIBRATION else (),
        ("unit.b",) if premise == owner.E3_CALIBRATION else (), ("endpoint.a", "endpoint.b"))
    if changes:
        scope = replace(scope, **changes)
    method = MetatheoryMethodSelection("method.exposed.independent-scientific-assessor", "testing.sampling-assessor",
        "1.0.0", scope.identity, "a"*64)
    return owner.MatrixSamplingRequest("request.exposed.sampling", scope, method)


def evidence_for(request, *, disposition=Cell.SUPPORTED, checks=None, links=True):
    """Typed exposed source-gate records without store, signers or qualification."""
    scope = request.scope
    gates = []
    for kind in ScientificSourceGateKind:
        required = kind is ScientificSourceGateKind.STATIONARITY_OR_RECURRENCE
        gates.append(ScientificSourceGateSpec("gate." + kind.value.lower(), kind,
            Applicability.REQUIRED if required else Applicability.NOT_APPLICABLE,
            request.method if required else None, scope.operands if required else (), "unit.whole-root",
            owner.sampling_operation_id(scope.premise) if required else "operation.not-applicable",
            (owner.CHECKS[scope.premise] if checks is None else checks) if required else (),
            () if required else ("EXPOSED_FIXTURE_OTHER_GATE_NOT_APPLICABLE",)))
    gates = tuple(sorted(gates, key=lambda value: value.gate_id))
    spec = ScientificSourceQualificationSpec("qualification.exposed.sampling",
        pin("pipeline.original", "empirical-lawhood/planning/source-pipeline-profile"),
        pin("pipeline-receipt.original", "empirical-lawhood/planning/source-pipeline-qualification-receipt"),
        pin("profile.original", "empirical-lawhood/planning/evidence-profile-selection"),
        scope.source, pin("source-materialization.original"), gates, scope.unit_ids, len(scope.unit_ids),
        ScientificSourceInvalidUnitPolicy.UNEVALUABLE, scope.fixed_map, pin("observation.original"),
        pin("view.original"), ObjectIdentity.from_record(scope.freeze_cutoff.cutoff_id, scope.freeze_cutoff),
        EvidenceCeiling.RESPONSE, MetatheoryEvidenceCeiling.PROSPECTIVE_TARGET_LOCAL,
        OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
    spec_ref = ObjectIdentity.from_record(spec.spec_id, spec)
    gate = next(value for value in gates if value.gate_kind is ScientificSourceGateKind.STATIONARITY_OR_RECURRENCE)
    gate_ref = ObjectIdentity.from_record(gate.gate_id, gate)
    reasons = () if disposition is Cell.SUPPORTED else ("EXPOSED_SCIENTIFIC_PREMISE_NOT_SUPPORTED",)
    original = ScientificSourceGateEvidence("evidence.exposed.sampling", spec_ref, gate_ref, scope.operands,
        request.method, scope.unit_ids, scope.unit_ids if disposition is Cell.SUPPORTED else (),
        () if disposition is Cell.SUPPORTED else scope.unit_ids, (), pin("publication.original"), pin("recovery.original"),
        (pin("scientific-derivation.original"),) if links else (), disposition, reasons)
    results = tuple(ScientificSourceGateResult("result." + value.gate_id, spec_ref,
        ObjectIdentity.from_record(value.gate_id, value), ObjectIdentity.from_record(original.evidence_id, original)
        if value == gate else None, disposition if value == gate else Cell.NOT_APPLICABLE,
        tuple(link.object_id for link in original.evidence_links) if value == gate else (),
        original.reason_codes if value == gate else value.applicability_reason_codes) for value in gates)
    result = ScientificSourceQualificationResult("result.exposed.sampling", spec_ref, spec.source_pipeline_qualification,
        (original,), results, len(scope.unit_ids), len(original.invalid_physical_unit_ids), len(original.eligible_physical_unit_ids),
        Aggregate(disposition.value), spec.maximum_ordinary_evidence_ceiling, spec.maximum_structural_evidence_ceiling,
        tuple(sorted((original.publication, original.recovery, *original.evidence_links), key=lambda value: value.object_id)),
        spec.outcome_access, spec.visibility_ceiling)
    return owner.MatrixSamplingEvidence("bundle.exposed.sampling", request.identity, spec, result)


@pytest.mark.parametrize("premise", (owner.E3_COMPARISON, owner.E4_FACTORIAL))
def test_scoped_independent_gate_semantics_and_exact_roundtrips(premise):
    request = request_for(premise)
    evidence = evidence_for(request)
    admitted = owner.assess_matrix_sampling(request, evidence)
    assert admitted.disposition == "SUPPORTED" and admitted.premise == premise
    for record in (request, evidence, admitted):
        assert decode_canonical_bytes(record.canonical_bytes(), type(record), maximum_bytes=None) == record


def test_missing_and_opposed_evidence_do_not_become_positive_admission():
    request = request_for()
    assert owner.assess_matrix_sampling(request).disposition == "UNEVALUABLE"
    assert owner.assess_matrix_sampling(request, evidence_for(request, disposition=Cell.OPPOSED)).disposition == "OPPOSED"
    assert owner.assess_matrix_sampling(request, evidence_for(request, disposition=Cell.UNEVALUABLE)).disposition == "UNEVALUABLE"


@pytest.mark.parametrize("field", ("specification", "population", "source", "fixed_map"))
def test_valid_supported_result_cannot_be_reused_for_another_scope(field):
    original = request_for()
    evidence = evidence_for(original)
    changed = request_for(**{field: pin("substituted." + field)})
    with pytest.raises(ValueError, match="substitutes"):
        owner.assess_matrix_sampling(changed, evidence)


@pytest.mark.parametrize("field,value", (
    ("unit_ids", ("unit.a",)), ("endpoint_ids", ("endpoint.a",)),
    ("freeze_cutoff", InformationCutoff("cutoff.other-freeze", "clock.original", CausalPhase.PREPARATION, Decimal(0))),
    ("first_sample_cutoff", InformationCutoff("cutoff.other-sample", "clock.original", CausalPhase.PRE_ACTION, Decimal(2))),
))
def test_complete_units_endpoints_and_timing_are_part_of_the_exact_scientific_request(field, value):
    original = request_for()
    with pytest.raises(ValueError, match="substitutes"):
        owner.assess_matrix_sampling(request_for(**{field: value}), evidence_for(original))


@pytest.mark.parametrize("checks", ((), ("distinct-seed-labels",), ("normality-diagnostic-passed",),
    ("fixed-map-before-confirmation", "independent-whole-root-draws")))
def test_finite_diagnostics_and_partial_checks_cannot_supply_the_named_sampling_warrant(checks):
    request = request_for()
    with pytest.raises(ValueError, match="every required independent check"):
        owner.assess_matrix_sampling(request, evidence_for(request, checks=checks))


def test_gate_result_supported_label_does_not_override_its_original_negative_evidence():
    request = request_for()
    evidence = evidence_for(request, disposition=Cell.OPPOSED)
    false_result = replace(evidence.qualification_result, disposition=Aggregate.SUPPORTED)
    with pytest.raises(ValueError, match="aggregate substitutes"):
        owner.assess_matrix_sampling(request, replace(evidence, qualification_result=false_result))


def test_named_scientific_gate_requires_actual_original_evidence_links():
    request = request_for()
    with pytest.raises(ValueError, match="complete evidence provenance"):
        owner.assess_matrix_sampling(request, evidence_for(request, links=False))


def test_gate_result_cannot_drop_original_scientific_evidence_links():
    request = request_for()
    evidence = evidence_for(request)
    result = replace(evidence.qualification_result,
        evidence_links=(pin("pipeline.publication"), pin("pipeline.recovery")))
    with pytest.raises(ValueError, match="scientific evidence links"):
        owner.assess_matrix_sampling(request, replace(evidence, qualification_result=result))


def test_actual_qualification_service_result_keeps_pipeline_and_gate_custody_separate():
    from empirical_lawhood.adapters.methods.backbone_structural_transport.source_free_property_transport_contracts import source_free_property_transport_capability_registry
    from empirical_lawhood.adapters.methods.backbone_structural_transport.source_free_property_transport_source_qualification_input_parts import _pipeline_receipt_for_profile
    from empirical_lawhood.runtime.capabilities import CapabilityRegistry
    from empirical_lawhood.runtime.scientific_source_qualification import ScientificSourceQualificationService

    request = request_for()
    supplied = evidence_for(request)
    pipeline = _pipeline_receipt_for_profile(supplied.qualification_specification.source_pipeline_profile)
    spec = replace(supplied.qualification_specification,
        source_pipeline_qualification=ObjectIdentity.from_record(pipeline.receipt_id, pipeline))
    gate = replace(supplied.qualification_result.gate_evidence[0],
        qualification_spec=ObjectIdentity.from_record(spec.spec_id, spec))
    installed = source_free_property_transport_capability_registry().capabilities[0]
    assessor = replace(installed, capability_key=request.method.capability_key,
        capability_version=request.method.capability_version, config_schema=request.scope.SCHEMA,
        input_schema_ids=tuple(sorted({value.object_schema for value in request.scope.operands})),
        output_schema_ids=(ScientificSourceGateEvidence.SCHEMA,),
        implementation_sha256=request.method.implementation_sha256)
    service = ScientificSourceQualificationService(CapabilityRegistry("registry.exposed.sampling", (assessor,)))
    result = service.finalize(spec=spec, pipeline_receipt=pipeline, gate_evidence=(gate,))
    assert gate.publication not in result.evidence_links and gate.recovery not in result.evidence_links
    assert pipeline.publication in result.evidence_links and pipeline.recovery in result.evidence_links
    evidence = replace(supplied, qualification_specification=spec, qualification_result=result)
    assert owner.assess_matrix_sampling(request, evidence).disposition == "SUPPORTED"


def test_calibration_is_separate_from_comparison_and_has_exactly_one_marginal_query():
    request = request_for(owner.E3_CALIBRATION, calibration_unit_ids=("unit.a",), query_unit_ids=("unit.b",))
    admitted = owner.assess_matrix_sampling(request, evidence_for(request))
    assert admitted.premise == owner.E3_CALIBRATION
    for queries in ((), ("unit.a",), ("unit.b", "unit.c")):
        with pytest.raises(ValueError, match="exactly one separate marginal query"):
            replace(request.scope, query_unit_ids=queries)
    with pytest.raises(ValueError, match="calibration or query scope"):
        replace(request.scope, premise=owner.E3_COMPARISON)


def test_future_fitted_map_and_method_scope_substitutions_are_refused():
    with pytest.raises(ValueError, match="after its dependent sampling"):
        request_for(freeze_cutoff=InformationCutoff("cutoff.late", "clock.original", CausalPhase.POST_OUTCOME, Decimal(2)))
    request = request_for()
    with pytest.raises(ValueError, match="exact named scope"):
        replace(request, method=replace(request.method, config=pin("foreign.assessor-config")))


def test_corrupted_per_gate_result_is_not_reduced_by_its_aggregate_label():
    request = request_for()
    evidence = evidence_for(request)
    result = evidence.qualification_result
    original = next(value for value in result.gate_results if value.evidence is not None)
    changed = replace(original, decisive_witness_ids=())
    result = replace(result, gate_results=tuple(changed if value == original else value for value in result.gate_results))
    with pytest.raises(ValueError, match="complete independently assessed gate evidence"):
        owner.assess_matrix_sampling(request, replace(evidence, qualification_result=result))
