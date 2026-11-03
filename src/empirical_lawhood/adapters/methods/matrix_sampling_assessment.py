# SPDX-License-Identifier: MPL-2.0
"""Scoped Matrix sampling admission from independently produced source gates.

These pure predicates check scientific applicability, not publication custody.
The caller must obtain the exact qualification records and their transitive
evidence through the existing source/publication owner. Neither a statistical
diagnostic nor distinct seed labels proves an IID or common-normal model.
Historical conditional calculations remain unchanged.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_stable_id,
)
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.planning.metatheory import (
    MetatheoryAggregateDisposition, MetatheoryApplicability, MetatheoryCellDisposition, MetatheoryMethodSelection,
)
from empirical_lawhood.planning.scientific_source_qualification import (
    ScientificSourceGateKind, ScientificSourceGateResult, ScientificSourceQualificationResult,
    ScientificSourceQualificationSpec,
)


E3_COMPARISON = "E3_FIXED_MAP_IID_WHOLE_ROOT_COMPARISON"
E3_CALIBRATION = "E3_EXCHANGEABLE_CALIBRATION_AND_SINGLE_QUERY"
E4_FACTORIAL = "E4_IID_COMMON_NORMAL_WHOLE_GROUP_CONTRASTS"
CHECKS = {
    E3_COMPARISON: (
        "fixed-map-before-confirmation", "identical-whole-root-distribution",
        "independent-whole-root-draws", "no-outcome-dependent-unit-selection",
    ),
    E3_CALIBRATION: (
        "exchangeable-calibration-and-query-scores", "fixed-map-before-calibration",
        "no-outcome-dependent-unit-selection", "single-query-marginal-scope",
    ),
    E4_FACTORIAL: (
        "common-normal-whole-group-contrasts", "fixed-endpoints-and-tests-before-confirmation",
        "independent-whole-group-draws", "no-outcome-dependent-unit-selection",
    ),
}


def identity(record):
    return ObjectIdentity.from_record(record.record_id, record)


@dataclass(frozen=True, slots=True)
class MatrixSamplingScope(CanonicalRecord):
    """One scientific premise at its complete fixed-map/population/query scope."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix/sampling-scope"
    record_id: str
    premise: str
    specification: ObjectIdentity
    population: ObjectIdentity
    source: ObjectIdentity
    fixed_map: ObjectIdentity
    freeze_cutoff: InformationCutoff
    first_sample_cutoff: InformationCutoff
    unit_ids: tuple[str, ...]
    calibration_unit_ids: tuple[str, ...]
    query_unit_ids: tuple[str, ...]
    endpoint_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if self.premise not in CHECKS:
            raise ValueError("Matrix sampling requires one code-owned scientific premise")
        for value in (self.specification, self.population, self.source, self.fixed_map):
            if type(value) is not ObjectIdentity:
                raise TypeError("Matrix sampling requires exact immutable scientific references")
            value.__post_init__()
        for value in (self.freeze_cutoff, self.first_sample_cutoff):
            if type(value) is not InformationCutoff:
                raise TypeError("Matrix sampling requires original typed information cutoffs")
            value.__post_init__()
        freeze, sample = self.freeze_cutoff, self.first_sample_cutoff
        if (freeze.clock_id != sample.clock_id or freeze.coordinate is None or sample.coordinate is None
                or freeze.coordinate > sample.coordinate
                or freeze.coordinate == sample.coordinate and not freeze.phase.precedes_or_equals(sample.phase)
                or freeze.phase is CausalPhase.POST_OUTCOME):
            raise ValueError("Matrix sampling cannot establish a fixed map after its dependent sampling")
        for name in ("unit_ids", "calibration_unit_ids", "query_unit_ids", "endpoint_ids"):
            require_sorted_unique_strings(getattr(self, name), field_name=name,
                allow_empty=name in ("calibration_unit_ids", "query_unit_ids"))
        if self.premise == E3_CALIBRATION:
            if (not self.calibration_unit_ids or len(self.query_unit_ids) != 1
                    or set(self.calibration_unit_ids) & set(self.query_unit_ids)
                    or self.unit_ids != tuple(sorted((*self.calibration_unit_ids, *self.query_unit_ids)))):
                raise ValueError("Matrix calibration sampling covers all CAL roots and exactly one separate marginal query")
        elif self.calibration_unit_ids or self.query_unit_ids:
            raise ValueError("comparison sampling cannot silently acquire calibration or query scope")

    @property
    def identity(self):
        return identity(self)

    @property
    def operands(self):
        refs = (self.identity, self.specification, self.population, self.source, self.fixed_map,
            ObjectIdentity.from_record(self.freeze_cutoff.cutoff_id, self.freeze_cutoff),
            ObjectIdentity.from_record(self.first_sample_cutoff.cutoff_id, self.first_sample_cutoff))
        by_id = {}
        for value in refs:
            if value.object_id in by_id and by_id[value.object_id] != value:
                raise ValueError("Matrix sampling scope aliases different immutable scientific operands")
            by_id[value.object_id] = value
        return tuple(by_id[key] for key in sorted(by_id))


@dataclass(frozen=True, slots=True)
class MatrixSamplingRequest(CanonicalRecord):
    """Preselected scientific assessor; its config is the exact sampling scope."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix/sampling-request"
    record_id: str
    scope: MatrixSamplingScope
    method: MetatheoryMethodSelection

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.scope) is not MatrixSamplingScope or type(self.method) is not MetatheoryMethodSelection:
            raise TypeError("Matrix sampling requires its typed scope and independently selected assessment method")
        self.scope.__post_init__()
        self.method.__post_init__()
        if self.method.config != self.scope.identity:
            raise ValueError("Matrix sampling assessor does not assess the exact named scope")

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class MatrixSamplingEvidence(CanonicalRecord):
    """Original source qualification records; no caller-supplied admission flag."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix/sampling-evidence"
    record_id: str
    request: ObjectIdentity
    qualification_specification: ScientificSourceQualificationSpec
    qualification_result: ScientificSourceQualificationResult

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.request) is not ObjectIdentity or self.request.object_schema != MatrixSamplingRequest.SCHEMA
                or type(self.qualification_specification) is not ScientificSourceQualificationSpec
                or type(self.qualification_result) is not ScientificSourceQualificationResult):
            raise TypeError("Matrix sampling evidence requires exact original source qualification records")
        self.request.__post_init__()
        self.qualification_specification.__post_init__()
        self.qualification_result.__post_init__()

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class MatrixSamplingAdmission(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix/sampling-admission"
    record_id: str
    request: ObjectIdentity
    evidence: ObjectIdentity | None
    premise: str
    disposition: str
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.request) is not ObjectIdentity or self.request.object_schema != MatrixSamplingRequest.SCHEMA
                or self.premise not in CHECKS or self.disposition not in ("SUPPORTED", "OPPOSED", "UNEVALUABLE")
                or self.disposition != "UNEVALUABLE" and self.evidence is None
                or not self.reason_codes):
            raise ValueError("Matrix sampling admission loses its exact premise or evidential disposition")
        if self.evidence is not None and (type(self.evidence) is not ObjectIdentity
                or self.evidence.object_schema != MatrixSamplingEvidence.SCHEMA):
            raise ValueError("Matrix sampling admission substitutes its original evidence")
        require_sorted_unique_strings(self.reason_codes, field_name="Matrix sampling reasons")

    @property
    def identity(self):
        return identity(self)


def assess_matrix_sampling(request, evidence=None):
    """Replay exact named gate applicability; never infer a warrant from data.

    This function does not authenticate storage. Registered consumers must first
    replay original qualification/publication custody, including the selected
    independent evaluator and its actual input/output provenance. A parsed JSON
    record is insufficient for protected use.
    """
    if type(request) is not MatrixSamplingRequest:
        raise TypeError("Matrix sampling requires its exact declared request")
    request.__post_init__()
    scope = request.scope
    record_id = "admission." + request.record_id
    if evidence is None:
        return MatrixSamplingAdmission(record_id, request.identity, None, scope.premise, "UNEVALUABLE",
            ("SAMPLING_EVIDENCE_ABSENT",))
    if type(evidence) is not MatrixSamplingEvidence:
        raise TypeError("Matrix sampling requires its original typed evidence bundle")
    evidence.__post_init__()
    spec, result = evidence.qualification_specification, evidence.qualification_result
    spec_ref = ObjectIdentity.from_record(spec.spec_id, spec)
    if (evidence.request != request.identity or result.qualification_spec != spec_ref
            or result.source_pipeline_qualification != spec.source_pipeline_qualification
            or spec.source_identity != scope.source or spec.preparation != scope.fixed_map
            or spec.causal_cutoff != ObjectIdentity.from_record(scope.freeze_cutoff.cutoff_id, scope.freeze_cutoff)
            or spec.physical_unit_ids != scope.unit_ids
            or result.complete_physical_unit_count != len(scope.unit_ids)
            or (result.outcome_access, result.visibility_ceiling) != (spec.outcome_access, spec.visibility_ceiling)
            or result.maximum_ordinary_evidence_ceiling != spec.maximum_ordinary_evidence_ceiling
            or result.maximum_structural_evidence_ceiling != spec.maximum_structural_evidence_ceiling):
        raise ValueError("Matrix sampling evidence substitutes its original source, map, cutoff or complete population")
    if (spec.outcome_access is not OutcomeAccess.OUTCOME_BLIND
            or spec.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE):
        raise ValueError("Matrix sampling evidence cannot be selected from the dependent revealed outcomes")
    gates = tuple(gate for gate in spec.gates if gate.gate_kind is ScientificSourceGateKind.STATIONARITY_OR_RECURRENCE)
    if len(gates) != 1:
        raise ValueError("Matrix sampling evidence lacks its independently assessed sampling gate")
    gate, = gates
    if (gate.applicability is not MetatheoryApplicability.REQUIRED or gate.evaluator != request.method
            or gate.required_operands != scope.operands or gate.falsifier_ids != CHECKS[scope.premise]
            or gate.uncertainty_operation_id != sampling_operation_id(scope.premise)):
        raise ValueError("Matrix sampling gate does not assess the named scientific premise and every required independent check")
    require_sorted_unique_ids(result.gate_evidence, attribute="evidence_id", field_name="sampling source evidence")
    require_sorted_unique_ids(result.gate_results, attribute="result_id", field_name="sampling source gate results")
    expected_results, admitted_evidence = [], None
    by_gate = {}
    for value in result.gate_evidence:
        value.__post_init__()
        if value.gate_spec in by_gate:
            raise ValueError("Matrix sampling source repeats evidence for one scientific gate")
        by_gate[value.gate_spec] = value
    dispositions, invalid, eligible = [], set(), set(scope.unit_ids)
    for source_gate in spec.gates:
        source_gate.__post_init__()
        gate_ref = ObjectIdentity.from_record(source_gate.gate_id, source_gate)
        original = by_gate.pop(gate_ref, None)
        if source_gate.applicability is MetatheoryApplicability.NOT_APPLICABLE:
            if original is not None:
                raise ValueError("Matrix sampling source invents evidence for an inapplicable gate")
            expected_results.append(ScientificSourceGateResult("result." + source_gate.gate_id, spec_ref, gate_ref,
                None, MetatheoryCellDisposition.NOT_APPLICABLE, (), source_gate.applicability_reason_codes))
            continue
        if (original is None or original.qualification_spec != spec_ref or original.method != source_gate.evaluator
                or original.input_operands != source_gate.required_operands
                or original.observed_physical_unit_ids != scope.unit_ids or not original.evidence_links):
            raise ValueError("Matrix sampling source loses its exact independent method, operands or complete evidence provenance")
        if not set(original.evidence_links).issubset(result.evidence_links):
            raise ValueError("Matrix sampling source omits independently assessed scientific evidence links")
        invalid.update(original.invalid_physical_unit_ids)
        eligible.intersection_update(original.eligible_physical_unit_ids)
        dispositions.append(original.disposition)
        expected_results.append(ScientificSourceGateResult("result." + source_gate.gate_id, spec_ref, gate_ref,
            ObjectIdentity.from_record(original.evidence_id, original), original.disposition,
            tuple(sorted(value.object_id for value in original.evidence_links)), original.reason_codes))
        if source_gate == gate:
            admitted_evidence = original
    if by_gate or tuple(sorted(expected_results, key=lambda value: value.result_id)) != result.gate_results:
        raise ValueError("Matrix sampling source result disagrees with its complete independently assessed gate evidence")
    aggregate = (MetatheoryAggregateDisposition.OPPOSED if MetatheoryCellDisposition.OPPOSED in dispositions
        else MetatheoryAggregateDisposition.UNEVALUABLE if MetatheoryCellDisposition.UNEVALUABLE in dispositions
        else MetatheoryAggregateDisposition.SUPPORTED)
    if (result.disposition is not aggregate or result.invalid_physical_unit_count != len(invalid)
            or result.eligible_physical_unit_count != len(eligible - invalid)):
        raise ValueError("Matrix sampling source aggregate substitutes the original complete source disposition")
    if aggregate is MetatheoryAggregateDisposition.OPPOSED:
        disposition, reasons = "OPPOSED", ("SAMPLING_OR_SOURCE_PREMISE_OPPOSED",)
    elif (aggregate is not MetatheoryAggregateDisposition.SUPPORTED or invalid
            or eligible != set(scope.unit_ids) or admitted_evidence is None
            or admitted_evidence.disposition is not MetatheoryCellDisposition.SUPPORTED):
        disposition, reasons = "UNEVALUABLE", ("SAMPLING_OR_SOURCE_PREMISE_NOT_ESTABLISHED",)
    else:
        disposition, reasons = "SUPPORTED", ("SCOPED_SAMPLING_PREMISE_SUPPORTED",)
    return MatrixSamplingAdmission(record_id, request.identity, evidence.identity, scope.premise, disposition, reasons)


def sampling_operation_id(premise):
    if premise not in CHECKS:
        raise ValueError("unknown Matrix sampling premise")
    return "matrix.sampling." + premise.lower().replace("_", "-")
