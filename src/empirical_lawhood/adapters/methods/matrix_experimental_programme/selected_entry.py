# SPDX-License-Identifier: MPL-2.0
"""Original source and upstream custody required by selected protected entry.

Constructing these records supplies neither a source qualification nor access.
The API replays their actual original producers and source qualification before
returning a parent-prepared worker. Nothing is signed or published here.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.planning.metatheory import MetatheoryAggregateDisposition, MetatheoryApplicability
from empirical_lawhood.planning.scientific_source_qualification import (
    ScientificSourceGateKind, ScientificSourceQualificationResult, ScientificSourceQualificationSpec,
)
from empirical_lawhood.adapters.methods.matrix_source_evidence import MatrixSourcePipelineEvidence
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding


def reference(record, field):
    return ObjectIdentity.from_record(getattr(record, field), record)


@dataclass(frozen=True, slots=True)
class MatrixSelectedOriginalProduct(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-original-product"
    prior_execution: RecursivePriorExecutionBinding
    reveal_authority: ObjectIdentity

    def __post_init__(self):
        if (type(self.prior_execution) is not RecursivePriorExecutionBinding
                or type(self.reveal_authority) is not ObjectIdentity
                or self.reveal_authority.object_schema != "empirical-lawhood/planning/study-operation-authority"):
            raise TypeError("selected upstream product requires its actual original execution and reveal locators")
        self.prior_execution.__post_init__()
        self.reveal_authority.__post_init__()

    @property
    def record(self):
        return self.prior_execution.record

    @property
    def issued_study(self):
        return self.prior_execution.issued_study

    @property
    def execution_authority(self):
        return self.prior_execution.execution_authority


@dataclass(frozen=True, slots=True)
class MatrixSelectedEntryEvidence(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-entry-evidence"
    record_id: str
    programme: ObjectIdentity
    reservation_publication: ArtifactWriteResult
    source_specification: ScientificSourceQualificationSpec
    pipeline: MatrixSourcePipelineEvidence
    source_result: ScientificSourceQualificationResult
    upstream_products: tuple[MatrixSelectedOriginalProduct, ...]
    qualification_executions: tuple[RecursivePriorExecutionBinding, ...]
    publications: tuple[tuple[ObjectIdentity, ArtifactWriteResult], ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.programme) is not ObjectIdentity
                or self.programme.object_schema != "empirical-lawhood/matrix-experimental-programme/selected-protected-programme"
                or type(self.reservation_publication) is not ArtifactWriteResult
                or type(self.source_specification) is not ScientificSourceQualificationSpec
                or type(self.pipeline) is not MatrixSourcePipelineEvidence
                or type(self.source_result) is not ScientificSourceQualificationResult
                or type(self.upstream_products) is not tuple or not self.upstream_products
                or any(type(value) is not MatrixSelectedOriginalProduct for value in self.upstream_products)
                or type(self.qualification_executions) is not tuple or not self.qualification_executions
                or any(type(value) is not RecursivePriorExecutionBinding for value in self.qualification_executions)
                or type(self.publications) is not tuple
                or any(type(row) is not tuple or len(row) != 2 or type(row[0]) is not ObjectIdentity
                    or type(row[1]) is not ArtifactWriteResult for row in self.publications)):
            raise TypeError("selected entry requires immutable original source, qualification and producer custody")
        for value in (self.programme, self.reservation_publication, self.source_specification, self.pipeline,
                self.source_result, *self.upstream_products, *self.qualification_executions):
            value.__post_init__()
        for rows in (tuple(value.record for value in self.upstream_products),
                tuple(value.record for value in self.qualification_executions), tuple(value for value, _ in self.publications)):
            if tuple(value.object_id for value in rows) != tuple(sorted({value.object_id for value in rows})):
                raise ValueError("selected entry aliases or reorders its complete original custody census")
        for pin, publication in self.publications:
            pin.__post_init__()
            publication.__post_init__()
            if (pin.object_schema, pin.object_fingerprint) != (publication.logical.payload_schema, publication.logical.content_sha256):
                raise ValueError("selected entry publication substitutes its exact original scientific bytes")

    @property
    def identity(self):
        return reference(self, "record_id")


def validate_selected_entry_evidence(evidence, programme):
    """Check applicability and complete locators; the API still owns custody."""
    from .selected_original_commitments import MatrixSelectedEntryEvidenceV3
    if type(evidence) is MatrixSelectedEntryEvidenceV3:
        if evidence.development_nomination is not None:
            from .selected_entry_v2 import validate_selected_entry_evidence_v2
            return validate_selected_entry_evidence_v2(evidence, programme)
    elif type(evidence) is not MatrixSelectedEntryEvidence:
        raise TypeError("selected protected entry requires its exact supplied source evidence")
    _validate_selected_entry_scope(evidence, programme)


def _validate_selected_entry_scope(evidence, programme, *, development_nomination=None):
    """Shared exact source gates; callers retain their distinct producer lanes."""
    from .selected_protected_programme import MatrixSelectedProtectedProgramme, MatrixSelectedPublicProgramme

    if type(programme) not in (MatrixSelectedProtectedProgramme, MatrixSelectedPublicProgramme):
        raise TypeError("selected entry requires its actual original programme or exact public projection")
    evidence.__post_init__()
    programme.__post_init__()
    closure, package = programme.sources.closure, programme.point_design.package
    spec, result = evidence.source_specification, evidence.source_result
    groups = tuple(sorted({source.root.root.independent_group_id for _, source in programme.sources.source_arms()}))
    original_programme = programme.original_programme if type(programme) is MatrixSelectedPublicProgramme else programme.identity
    if (evidence.programme != original_programme or spec.source_identity != closure.identity
            or spec.physical_unit_ids != groups or spec.expected_physical_unit_count != len(groups)
            or spec.preparation != programme.sources.identity or spec.observation_operator != programme.assay.identity
            or spec.numerical_view != closure.numerical_scope
            or spec.maximum_ordinary_evidence_ceiling is EvidenceCeiling.NON_PROMOTABLE
            or spec.outcome_access is not OutcomeAccess.OUTCOME_BLIND
            or spec.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
            or result.qualification_spec != reference(spec, "spec_id")
            or spec.source_pipeline_qualification != reference(evidence.pipeline.receipt, "receipt_id")
            or result.source_pipeline_qualification != spec.source_pipeline_qualification):
        raise ValueError("selected entry changes its actual source/preparation/assay/numerical or complete whole-group qualification scope")
    if (result.disposition is not MetatheoryAggregateDisposition.SUPPORTED
            or result.complete_physical_unit_count != len(groups)
            or result.invalid_physical_unit_count != 0 or result.eligible_physical_unit_count != len(groups)):
        raise ValueError("selected entry requires a genuinely supported complete source qualification before native contact")
    required = set(ScientificSourceGateKind) - {ScientificSourceGateKind.STATIONARITY_OR_RECURRENCE}
    gates = {gate.gate_kind: gate for gate in spec.gates}
    if any(gates[kind].applicability is not MetatheoryApplicability.REQUIRED
            or closure.identity not in gates[kind].required_operands for kind in required):
        raise ValueError("selected entry lacks independent original source, numerical, preparation, observation, completeness or cutoff assessment")
    if (programme.sources.identity not in gates[ScientificSourceGateKind.PREPARATION].required_operands
            or programme.assay.identity not in gates[ScientificSourceGateKind.OBSERVATION_OPERATOR].required_operands
            or closure.numerical_scope not in gates[ScientificSourceGateKind.NUMERICAL_OR_INSTRUMENT_VALIDITY].required_operands):
        raise ValueError("selected entry source gates do not assess the actual preparation, assay or numerical scope")
    upstream = tuple(record if type(record) is ObjectIdentity else reference(record, "record_id") for record in (
        package.models, package.model_freeze, package.calibration, package.calibrated_freeze))
    if programme.nomination is not None and development_nomination is None:
        upstream += (programme.nomination.original_nomination if type(programme) is MatrixSelectedPublicProgramme
            else reference(programme.nomination, "result_id"),)
    expected_upstream = tuple(sorted(upstream, key=lambda value: value.object_id))
    expected_qualification = tuple(sorted((reference(evidence.pipeline.receipt, "receipt_id"), reference(result, "result_id"),
        *(reference(gate, "evidence_id") for gate in result.gate_evidence)), key=lambda value: value.object_id))
    if (tuple(value.record for value in evidence.upstream_products) != expected_upstream
            or tuple(value.record for value in evidence.qualification_executions) != expected_qualification):
        raise ValueError("selected entry omits or substitutes its actual upstream freeze or independent source gate producers")
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import _publication
    _publication(evidence.reservation_publication, closure.reservation)
