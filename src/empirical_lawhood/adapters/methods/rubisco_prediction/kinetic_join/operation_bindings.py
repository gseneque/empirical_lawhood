# SPDX-License-Identifier: MPL-2.0
"""Cold typed W1 join; no predictor calibration or second execution engine."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec, ScientificConditionScope
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_provider import (
    RecursiveInquiryHooks, RecursiveOperationDeclaration, RecursiveScientificHooks,
)

from ..kinetic_assay_bridge import (
    KineticAssayBridgeResult, KineticJointTargetAssessment, assess_joint_kinetic_target,
    execute_kinetic_assay_bridge,
)
from ..kinetic_supply import JointKineticSupply, KineticSupplyContext, KineticTargetComparison
from empirical_lawhood.adapters.simulators.rubisco_assay.records import AssayQuery
from .numerical_runtime import KINETIC_PROVENANCE_REQUIREMENT

NAMESPACE = "rubisco-kinetic-join"
MEDIA = "application/json"
BUDGET = ResourceBudget(1, None, 0, None, None, None)
UNIT = NAMESPACE + ".exposed-analytical-unit"
PHASES = (
    ("assay", (("query", AssayQuery), ("supply", JointKineticSupply)),
     KineticAssayBridgeResult, ScientificStage.TRANSFORM),
    ("assess", (("bridge", KineticAssayBridgeResult), ("comparison", KineticTargetComparison)),
     KineticJointTargetAssessment, ScientificStage.FALSIFY),
)


@dataclass(frozen=True, slots=True)
class KineticJoinDesign(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/kinetic-supply/join-design"
    design_id: str
    context: KineticSupplyContext
    supply: ObjectIdentity
    query: ObjectIdentity
    comparison: ObjectIdentity
    numerical_relative_tolerance: Decimal
    evidence_role: str = "EXPOSED_CONDITIONAL_NUMERICAL_DEVELOPMENT_NONPROMOTABLE"

    def __post_init__(self):
        validate_stable_id(self.design_id)
        if type(self.context) is not KineticSupplyContext:
            raise ValueError("kinetic join requires its exact material/assay context")
        self.context.__post_init__()
        for value, schema in ((self.supply, JointKineticSupply.SCHEMA),
                              (self.query, AssayQuery.SCHEMA), (self.comparison, KineticTargetComparison.SCHEMA)):
            if type(value) is not ObjectIdentity or value.object_schema != schema:
                raise ValueError("kinetic join substitutes a typed scientific operand")
        validate_decimal(self.numerical_relative_tolerance, field_name="numerical_relative_tolerance", minimum=Decimal(0))
        if (self.numerical_relative_tolerance == 0 or self.context.temperature_k != Decimal("298.15")
                or self.evidence_role != "EXPOSED_CONDITIONAL_NUMERICAL_DEVELOPMENT_NONPROMOTABLE"):
            raise ValueError("kinetic join changes numerical protocol or conditional evidence ceiling")


@dataclass(frozen=True, slots=True)
class KineticJoinConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/kinetic-supply/join-config"
    config_id: str
    operation: str
    science: KineticJoinDesign

    def __post_init__(self):
        if (self.operation not in {row[0] for row in PHASES}
                or self.config_id != f"config.{NAMESPACE}.{self.operation}"
                or type(self.science) is not KineticJoinDesign):
            raise ValueError("kinetic join changes its selected operation/design")
        self.science.__post_init__()


def design(supply, query, comparison, *, design_id, relative_tolerance):
    supply.__post_init__()
    query.__post_init__()
    comparison.__post_init__()
    if comparison.candidate_context != ObjectIdentity.from_record(supply.context.context_id, supply.context):
        raise ValueError("kinetic design substitutes the candidate context")
    return KineticJoinDesign(design_id, supply.context, ObjectIdentity.from_record(supply.supply_id, supply),
        ObjectIdentity.from_record(design_id + ".query", query),
        ObjectIdentity.from_record(comparison.comparison_id, comparison), relative_tolerance)


def scope(science):
    return ScientificConditionScope(science.context.material.object_id, "world." + NAMESPACE,
        science.supply.object_id, ("specificity", "turnover"), ("dimensionless", "s^-1"),
        NAMESPACE + ".assess", "clock.stationary-supplied-kinetics",
        "Complete jointly supported apparent-rate members, exact material/assay context; no calibrated biological probabilities.",
        science.fingerprint(), instance_id=science.context.material.object_id)


def development_root(science, *, study_id):
    source = ObjectIdentity.from_record(science.design_id, science)
    view = NAMESPACE + ".complete-supported-member-roster"
    claim = ClaimSpec("claim." + NAMESPACE, "world." + NAMESPACE,
        "population." + NAMESPACE, "Do the complete supplied joint kinetics survive independent product/flux checks and both conditional reference bounds?",
        "One exposed analytical calculation, with complete nested supported/adverse members; zero fresh biological units.",
        UNIT, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY, "Supplied kinetic arithmetic does not predict unseen mutants, calibrate biological uncertainty or establish nomination/challenge success.",
        ("assumption.supplied-apparent-kinetics",), numerical_view_ids=(view,))
    return DevelopmentStudySpec(study_id, claim.proposition, source, "world." + NAMESPACE,
        WorldKind.ANALYTIC_REFERENCE, (UNIT,), (view,), (claim,),
        tuple(sorted((source, science.supply, science.query, science.comparison), key=lambda row: row.object_id)))


def scientific_operand_sha256s(config):
    science = config.science
    return tuple(sorted({science.fingerprint(), science.supply.object_fingerprint,
                         science.query.object_fingerprint, science.comparison.object_fingerprint}))


def scientific_unit_ids(config):
    return (UNIT,)


def scientific_root_validator(config, context):
    if (type(context.root) is not DevelopmentStudySpec
            or context.root != development_root(config.science, study_id=context.root.study_id)):
        raise ValueError("kinetic join changes its source-bound analytical root")
    phase = next(row for row in PHASES if row[0] == config.operation)
    if (context.node_id != f"{NAMESPACE}.{config.operation}" or context.stage is not phase[3]
            or context.unit_ids != (UNIT,) or context.selected_unit_ids != (UNIT,)
            or context.complete_unit_census or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise ValueError("kinetic join changes its scientific stage/access/unit")
    expected_configs = {f"{NAMESPACE}.{role}": KineticJoinConfig(f"config.{NAMESPACE}.{role}", role, config.science)
                        for role, *_ in PHASES}
    if (len(context.config_inputs) != 2
            or {row.node_id: row.record for row in context.config_inputs} != expected_configs):
        raise ValueError("kinetic join changes its complete two-stage selected design")
    expected = ({"supply": (None, None, f"external.{NAMESPACE}.supply", "MODEL"),
                 "query": (None, None, f"external.{NAMESPACE}.query", "ACTION")}
                if config.operation == "assay" else
                {"bridge": (f"{NAMESPACE}.assay", "product", None, "MODEL"),
                 "comparison": (None, None, f"external.{NAMESPACE}.comparison", "SOURCE")})
    incoming = tuple(row for row in context.links if row.consumer_node_id == context.node_id)
    if (len(incoming) != len(expected) or {row.consumer_input_id for row in incoming} != set(expected)
            or any((row.producer_node_id, row.producer_output_id, row.external_input_id, row.scientific_role)
                   != expected[row.consumer_input_id] for row in incoming)):
        raise ValueError("kinetic join substitutes its source/action/assessment dependencies")


def operation_manifests():
    return tuple(declaration.manifest() for declaration in operation_declarations())


def operation_registrations():
    return tuple(declaration.registration() for declaration in operation_declarations())


def output_codecs():
    return {record.SCHEMA: record for record in (KineticJoinConfig, KineticJoinDesign,
        JointKineticSupply, AssayQuery, KineticTargetComparison, KineticAssayBridgeResult, KineticJointTargetAssessment)}


class KineticJoinRunner:
    def __init__(self, role):
        self.phase = next(row for row in PHASES if row[0] == role)
        self.role = role
        self.manifest = next(m for m in operation_manifests() if m.capability_key == f"{NAMESPACE}.{role}")

    def execute(self, context):
        try:
            _, inputs, output_type, _ = self.phase
            types = {KineticJoinConfig.SCHEMA: KineticJoinConfig, **{t.SCHEMA: t for _, t in inputs}}
            if (context.task_id != f"{NAMESPACE}.{self.role}" or context.permissions != self.manifest.permissions
                    or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE or context.resource_budget != BUDGET
                    or len(context.input_ports) != len(types) or {p.payload_schema for p in context.input_ports} != set(types)):
                raise ValueError("kinetic worker changes its declared typed input/access census")
            ports = {p.payload_schema: p for p in context.input_ports}
            for schema, port in ports.items():
                kind = WorkerInputKind.DEPENDENCY if schema == KineticAssayBridgeResult.SCHEMA else WorkerInputKind.EXTERNAL
                if (port.kind is not kind or port.media_type != MEDIA
                        or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE):
                    raise ValueError("kinetic worker substitutes external/receipt-bound predecessor roles")
                if kind is WorkerInputKind.DEPENDENCY:
                    receipts = tuple(r for r in context.dependency_receipts if port.materialization_id in r.output_materialization_ids)
                    if len(receipts) != 1 or receipts[0].task_id != f"{NAMESPACE}.assay":
                        raise ValueError("kinetic assessment lacks its exact producing assay receipt")

            def read(record_type):
                port = ports[record_type.SCHEMA]
                payload = port.read()
                if len(payload) != port.size_bytes:
                    raise ValueError("kinetic worker source size differs from authenticated materialization")
                return decode_canonical_bytes(payload, record_type, maximum_bytes=None)

            config = read(KineticJoinConfig)
            if (config.operation != self.role or config.config_id != context.config.config_id
                    or config.fingerprint() != context.config.content_sha256
                    or ports[KineticJoinConfig.SCHEMA].artifact_id != context.config.artifact_id):
                raise ValueError("kinetic worker changes its selected immutable configuration")
            science = config.science
            if self.role == "assay":
                source, query = read(JointKineticSupply), read(AssayQuery)
                if (ObjectIdentity.from_record(source.supply_id, source) != science.supply or source.context != science.context
                        or ObjectIdentity.from_record(science.query.object_id, query) != science.query):
                    raise ValueError("kinetic assay substitutes its exact supplied material/query")
                product = execute_kinetic_assay_bridge(source, query, result_id=f"{NAMESPACE}.assay.result",
                    relative_tolerance=science.numerical_relative_tolerance)
            else:
                numerical = read(KineticAssayBridgeResult)
                if (ObjectIdentity.from_record(numerical.supply.supply_id, numerical.supply) != science.supply
                        or numerical.supply.context != science.context
                        or ObjectIdentity.from_record(science.query.object_id, numerical.query) != science.query
                        or numerical.numerical_relative_tolerance != science.numerical_relative_tolerance):
                    raise ValueError("kinetic assessment substitutes its actual precursor/query/protocol")
                target = read(KineticTargetComparison)
                if ObjectIdentity.from_record(target.comparison_id, target) != science.comparison:
                    raise ValueError("kinetic assessment substitutes its exact reference comparison")
                product = assess_joint_kinetic_target(numerical.supply, target,
                    assessment_id=f"{NAMESPACE}.assess.result", assay_bridge=numerical)
            outputs = context.output_ports
            if (len(outputs) != 1 or outputs[0].output_id != f"{context.task_id}.product"
                    or outputs[0].payload_schema != output_type.SCHEMA or outputs[0].profile is not ArtifactProfile.CANONICAL_JSON
                    or outputs[0].media_type != MEDIA):
                raise ValueError("kinetic worker changes its complete output contract")
            return RunnerResult((TaskOutputPayload(outputs[0].output_id, product.canonical_bytes()),),
                (ReceiptCheck("complete-conditional-kinetic-product", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_declarations():
    """Own the conditional join and contrast, deriving installed projections."""
    from .recursive_translation import scientific_work
    from .gas_contrast import operation_declaration as gas_contrast_declaration
    from .gas_contrast_translation import describe_kinetic_contribution

    joins = tuple(RecursiveOperationDeclaration(
        capability_key=f"{NAMESPACE}.{role}", capability_version="1.0.0",
        implementation_id=f"{NAMESPACE}.{role}.independent-complete-supported-kinetics-v1",
        kind=CapabilityKind.ANALYSIS if role == "assay" else CapabilityKind.FALSIFIER,
        config_record_type=KineticJoinConfig, stage=stage,
        input_ports=tuple(RecursivePortContract(name, record.SCHEMA, MEDIA, None)
            for name, record in inputs),
        outputs=(OutputTemplate("product", output.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA, ".json"),),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=BUDGET,
        conformance_check_ids=("complete-adverse-and-partial-denominator",
            "independent-product-flux-check", "no-biological-calibration"),
        runner_factory=lambda phase=role: KineticJoinRunner(phase), record_codecs=output_codecs(),
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=scientific_operand_sha256s,
            scientific_unit_ids=scientific_unit_ids, scientific_root_validator=scientific_root_validator),
        provenance_requirements=(KINETIC_PROVENANCE_REQUIREMENT,),
        inquiry_hooks=RecursiveInquiryHooks(inquiry_work_projector=scientific_work,
            contribution_describer=describe_kinetic_contribution))
        for role, inputs, output, stage in PHASES)
    return (*joins, gas_contrast_declaration())
