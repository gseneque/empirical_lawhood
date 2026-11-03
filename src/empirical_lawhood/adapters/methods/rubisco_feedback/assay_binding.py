# SPDX-License-Identifier: MPL-2.0
"""Cold binding of the conditional assay to shared execution and custody."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.simulators.rubisco_assay.records import (
    AssayConfig, AssayEvaluation, AssayProjection,
)
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_strings
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_provider import (
    RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks,
)

NAMESPACE = "rubisco-feedback"
MAX_BYTES = 1024**2
BUDGET = ResourceBudget(1, 1024**3, 0, 600, MAX_BYTES, MAX_BYTES)
WORLD_ID = "world.rubisco.conditional-numerical"
SYSTEM_ID = "system.rubisco.supplied-kinetics"
CLAIM_ID = "claim.rubisco.conditional-agreement"
PROPOSITION = ("The complete declared supplied-kinetics query census passes the frozen branch-rate, stationary-balance "
               "and specificity-reconstruction tolerances, and the frozen initial probe design has rank-four local log sensitivity "
               "for the four supplied kinetic variables.")


@dataclass(frozen=True, slots=True)
class AssayRunProduct(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/conditional-run-product"
    config: ObjectIdentity
    projections: tuple[AssayProjection, ...]
    evaluation: AssayEvaluation
    numerical_query_count: int
    independent_biological_unit_count: int = 0
    biological_prediction_established: bool = False

    def __post_init__(self):
        if not isinstance(self.config, ObjectIdentity) or self.config.object_schema != AssayConfig.SCHEMA:
            raise ValueError("Rubisco assay product changes its configuration schema")
        if not isinstance(self.projections, tuple) or not 1 <= len(self.projections) <= 16:
            raise ValueError("Rubisco assay product changes its complete projection census")
        if any(not isinstance(value, AssayProjection) for value in self.projections):
            raise ValueError("Rubisco assay product contains an untyped projection")
        if not isinstance(self.evaluation, AssayEvaluation):
            raise ValueError("Rubisco assay product lacks its typed evaluation")
        if (type(self.independent_biological_unit_count) is not int
            or self.independent_biological_unit_count != 0 or self.biological_prediction_established is not False):
            raise ValueError("Supplied kinetics cannot establish biological prediction or replication")
        if type(self.numerical_query_count) is not int or not 1 <= self.numerical_query_count <= 256:
            raise ValueError("Rubisco numerical query count exceeds its contract")
        require_sorted_unique_strings(tuple(value.case_id for value in self.projections), field_name="case_ids")
        expected_reports = tuple(sorted((ObjectIdentity.from_record(value.report_id, value)
                                        for value in self.projections), key=lambda value: value.object_id))
        if (self.evaluation.config != self.config or self.evaluation.source_reports != expected_reports
            or any(value.config != self.config for value in self.projections)):
            raise ValueError("Rubisco assay product substitutes its exact source/configuration joins")
        results = tuple(result for value in self.projections for result in value.source_results)
        if len(results) != self.numerical_query_count or len({result.result_id for result in results}) != len(results):
            raise ValueError("Rubisco assay product changes its numerical query census")
        if len({len(value.source_results) for value in self.projections}) != 1:
            raise ValueError("Rubisco assay product changes its common declared round census")
        for projection in self.projections:
            previous = self.config
            previous_query = None
            case = projection.source_results[0].case
            if case.object_id != projection.case_id:
                raise ValueError("Rubisco assay product substitutes its declared case")
            for index, result in enumerate(projection.source_results):
                if (result.config != self.config or result.case != case or result.round_index != index
                    or result.prior_commitment != previous
                    or (index > 0 and result.realized_query != previous_query)
                    or (result.committed_next_query is None) != (index == len(projection.source_results) - 1)):
                    raise ValueError("Rubisco assay product loses its complete committed round history")
                previous = ObjectIdentity.from_record(result.result_id, result)
                previous_query = result.committed_next_query


def assay_claim():
    """The exact conditional claim; supplied rates confer no protein prediction."""
    return ClaimSpec(CLAIM_ID, WORLD_ID, "relation.rubisco.stationary-rates", PROPOSITION,
        "Complete supplied-case/query census; two branch-rate views nested within each numerical case",
        "units.rubisco.numerical-configurations", None, EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        "Exposed supplied-kinetics arithmetic cannot qualify or predict an unseen protein",
        ("assumption.rubisco.activated-saturating-clamped-stationary",),
        numerical_view_ids=("linear-stationary-occupancy", "stationary-branch-rate-reference"))


def assay_units(config):
    return tuple(case.case_id for case in config.cases)


def assay_effects(config):
    return tuple(sorted(f"native.rubisco.assay.{config.fingerprint()}.{case.case_id}.round-{i:02d}"
                        for case in config.cases for i in range(config.rounds_per_case)))


def validate_assay_root(config, context):
    root = context.root
    expected = ObjectIdentity.from_record(config.config_id, config)
    if (root.world_id != WORLD_ID or root.world_kind is not WorldKind.NUMERICAL_SIMULATOR
        or root.system != ObjectIdentity.from_record(SYSTEM_ID, config)
        or root.scientific_operands != (expected,)
        or root.assigned_unit_ids != assay_units(config)
        or root.claims != (assay_claim(),)
        or root.numerical_view_ids != assay_claim().numerical_view_ids
        or context.unit_ids != assay_units(config)):
        raise ValueError("Rubisco conditional operation changes its exact source/root/claim/unit scope")


class AssayRunner:
    def __init__(self):
        self.manifest = assay_manifest()

    def execute(self, context):
        try:
            if context.config.config_schema != AssayConfig.SCHEMA or len(context.input_ports) != 1:
                raise ValueError("Rubisco assay receives an undeclared input or configuration")
            port = context.input_ports[0]
            if (port.payload_schema != AssayConfig.SCHEMA or port.media_type != "application/json"
                or port.kind is not WorkerInputKind.EXTERNAL or port.size_bytes > MAX_BYTES
                or port.artifact_id != context.config.artifact_id):
                raise ValueError("Rubisco assay receives an undeclared input contract")
            payload = port.read(MAX_BYTES + 1)
            if len(payload) != port.size_bytes:
                raise ValueError("Rubisco assay substitutes its bounded materialization")
            config = decode_canonical_bytes(payload, AssayConfig, maximum_bytes=MAX_BYTES)
            if config.fingerprint() != context.config.content_sha256 or config.config_id != context.config.config_id:
                raise ValueError("Rubisco assay substitutes its frozen configuration")
            if (len(context.output_ports) != 1 or context.output_ports[0].payload_schema != AssayRunProduct.SCHEMA
                or context.output_ports[0].output_id != f"{context.task_id}.assay"
                or context.output_ports[0].profile is not ArtifactProfile.CANONICAL_JSON
                or context.output_ports[0].media_type != "application/json"):
                raise ValueError("Rubisco assay changes its declared output census")
            from empirical_lawhood.adapters.simulators.rubisco_assay.science import run_assay
            projections, evaluation = run_assay(config)
            if (tuple(projection.case_id for projection in projections) != assay_units(config)
                or any(len(projection.source_results) != config.rounds_per_case for projection in projections)):
                raise ValueError("Rubisco assay omits a declared case or query")
            product = AssayRunProduct(ObjectIdentity.from_record(config.config_id, config),
                                      projections, evaluation, config.maximum_native_calls)
            payload = product.canonical_bytes()
            if len(payload) > min(MAX_BYTES, context.resource_budget.output_bytes):
                raise ValueError("Rubisco assay exceeds its frozen output byte budget")
            return RunnerResult((TaskOutputPayload(context.output_ports[0].output_id, payload),),
                                (ReceiptCheck("complete-conditional-rubisco-history", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def assay_manifest():
    return assay_declaration().manifest()


def assay_declaration():
    """Own the complete supplied-case/query operation and native-effect census."""
    return RecursiveOperationDeclaration(
        capability_key=NAMESPACE + ".conditional-assay", capability_version="1.0.0",
        implementation_id="conditional-assay-successor-v1", kind=CapabilityKind.SIMULATOR,
        config_record_type=AssayConfig, stage=ScientificStage.ACQUIRE, input_ports=(),
        outputs=(OutputTemplate("assay", AssayRunProduct.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=BUDGET,
        conformance_check_ids=("complete-query-history", "independent-branch-rate-reference",
            "zero-biological-units"), runner_factory=AssayRunner,
        record_codecs={AssayRunProduct.SCHEMA: AssayRunProduct},
        scientific_hooks=RecursiveScientificHooks(
            scientific_operand_sha256s=lambda config: (config.fingerprint(),),
            scientific_unit_ids=assay_units, native_effect_slot_ids=assay_effects,
            scientific_root_validator=validate_assay_root),
        execution_properties=RecursiveExecutionProperties(native_effect=True, complete_unit_census=True))
