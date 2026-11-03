# SPDX-License-Identifier: MPL-2.0
"""Conditional paired gas-response assessment over receipted apparent kinetics.

The numerical products and the exact Fraction stationary-flux falsifier are
independent calculations. A complete adverse roster remains part of the result;
none of these supplied-constant calculations is a biological trial.
"""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import (
    AssessmentDisposition as A, ContributionRole, DevelopmentStudySpec, ScientificConditionScope,
)
from empirical_lawhood.kernel.scientific_contributions import ContributionManifest, ContributionProduct
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile, CanonicalTaskReceipt, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_provider import (
    RecursiveInquiryHooks, RecursiveOperationDeclaration, RecursiveScientificHooks,
)

from ..kinetic_assay_bridge import KineticAssayBridgeResult
from ..kinetic_supply import JointKineticSupply, KineticSupplyContext
from empirical_lawhood.adapters.simulators.rubisco_assay.records import AssayQuery

CAPABILITY = "rubisco-kinetic-join.gas-contrast"
UNIT = CAPABILITY + ".exposed-analytical-unit"
MEDIA = "application/json"
BUDGET = ResourceBudget(1, None, 0, None, None, None)


def identity(record, name):
    return ObjectIdentity.from_record(getattr(record, name), record)


@dataclass(frozen=True, slots=True)
class GasContrastConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/kinetic-supply/gas-contrast-config"
    config_id: str
    context: KineticSupplyContext
    supply: ObjectIdentity
    left_parent: ObjectIdentity
    right_parent: ObjectIdentity
    left_product: ContributionProduct
    right_product: ContributionProduct
    left_query: ObjectIdentity
    right_query: ObjectIdentity
    numerical_relative_tolerance: Decimal
    estimand: str = "RIGHT_MINUS_LEFT_APPARENT_CARBOXYLATION_AND_OXYGENATION_FLUX"

    def __post_init__(self):
        if self.config_id != "config." + CAPABILITY or type(self.context) is not KineticSupplyContext:
            raise ValueError("gas contrast requires its exact conditional config/context")
        self.context.__post_init__()
        if self.context.temperature_k != Decimal("298.15"):
            raise ValueError("gas contrast changes the existing apparent-rate temperature")
        for value, schema in ((self.supply, JointKineticSupply.SCHEMA),
                (self.left_parent, ContributionManifest.SCHEMA), (self.right_parent, ContributionManifest.SCHEMA),
                (self.left_query, AssayQuery.SCHEMA), (self.right_query, AssayQuery.SCHEMA)):
            if type(value) is not ObjectIdentity or value.object_schema != schema:
                raise ValueError("gas contrast substitutes a typed scientific operand")
            value.__post_init__()
        if self.left_parent == self.right_parent or self.left_query.object_fingerprint == self.right_query.object_fingerprint:
            raise ValueError("gas contrast needs distinct supplied query products and parents")
        for product in (self.left_product, self.right_product):
            if (type(product) is not ContributionProduct or product.record.object_schema != KineticAssayBridgeResult.SCHEMA
                    or product.role is not ContributionRole.INSTANCE_PRODUCT
                    or product.evidence_ceiling is not EvidenceCeiling.NON_PROMOTABLE
                    or product.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                    or product.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
                raise ValueError("gas contrast requires receipted exposed apparent-kinetic instance products")
            product.__post_init__()
            if product.producing_receipt.object_schema != CanonicalTaskReceipt.SCHEMA:
                raise ValueError("gas contrast substitutes its original task completion receipt")
        if (self.left_product.record == self.right_product.record
                or self.left_product.producing_receipt == self.right_product.producing_receipt):
            raise ValueError("gas contrast cannot relabel one assay as a paired query")
        validate_decimal(self.numerical_relative_tolerance, field_name="numerical_relative_tolerance", minimum=Decimal(0))
        if (not self.numerical_relative_tolerance
                or self.estimand != "RIGHT_MINUS_LEFT_APPARENT_CARBOXYLATION_AND_OXYGENATION_FLUX"):
            raise ValueError("gas contrast changes its fixed estimand or numerical criterion")


def require_pair(config, left, right):
    config.__post_init__()
    for side, bridge, product, query in (
            ("left", left, config.left_product, config.left_query),
            ("right", right, config.right_product, config.right_query)):
        if type(bridge) is not KineticAssayBridgeResult:
            raise ValueError("gas contrast requires actual typed assay products")
        bridge.__post_init__()
        if (identity(bridge, "result_id") != product.record or bridge.supply.context != config.context
                or identity(bridge.supply, "supply_id") != config.supply
                or ObjectIdentity.from_record(CAPABILITY + "." + side + ".query", bridge.query) != query
                or bridge.numerical_relative_tolerance != config.numerical_relative_tolerance):
            raise ValueError("gas contrast substitutes its exact paired query, product or supplied material")
    if left.supply != right.supply or left.query.duration_s != right.query.duration_s:
        raise ValueError("gas contrast changes matched kinetics, context or duration")
    if (left.query.co2_um, left.query.o2_um) == (right.query.co2_um, right.query.o2_um):
        raise ValueError("gas contrast requires a declared gas intervention")


def _fraction_pair(value):
    return value.numerator, value.denominator


def _stationary_flux(constants, query):
    carbon = Fraction(query.co2_um) / Fraction(constants.kc_um)
    oxygen = Fraction(query.o2_um) / Fraction(constants.ko_um)
    denominator = 1 + carbon + oxygen
    return (Fraction(constants.kcat_c_s_inv) * carbon / denominator,
            Fraction(constants.kcat_o_s_inv) * oxygen / denominator)


@dataclass(frozen=True, slots=True)
class GasContrastMember(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/kinetic-supply/gas-contrast-member"
    member_id: str
    source_outcome: str
    observed_difference: tuple[tuple[int, int], tuple[int, int]] | None
    expected_difference: tuple[tuple[int, int], tuple[int, int]] | None
    maximum_relative_error: tuple[int, int] | None
    disposition: A
    reason: str

    def __post_init__(self):
        validate_stable_id(self.member_id)
        if (not self.source_outcome or type(self.disposition) is not A or not self.reason
                or (self.observed_difference is None) != (self.expected_difference is None)
                or (self.expected_difference is None) != (self.maximum_relative_error is None)):
            raise ValueError("gas contrast member omits complete paired arithmetic or disposition")
        values = (() if self.maximum_relative_error is None else
            (*self.observed_difference, *self.expected_difference, self.maximum_relative_error))
        for value in values:
            if (type(value) is not tuple or len(value) != 2 or any(type(atom) is not int for atom in value)
                    or value[1] <= 0 or _fraction_pair(Fraction(*value)) != value):
                raise ValueError("gas contrast member changes normalized exact rational values")
        if self.maximum_relative_error is None:
            if self.disposition is not A.UNEVALUABLE:
                raise ValueError("unidentified gas contrast cannot become an evaluated member")
        elif (len(self.observed_difference) != 2 or len(self.expected_difference) != 2
                or self.maximum_relative_error[0] < 0):
            raise ValueError("gas contrast changes its complete two-flux/error denominator")


def _assessed_members(config, left, right):
    require_pair(config, left, right)
    rows = []
    for member, first, second in zip(left.supply.members, left.member_results, right.member_results, strict=True):
        if (first.reduced_rates is None or second.reduced_rates is None or member.constants is None):
            rows.append(GasContrastMember(member.member_id, member.outcome, None, None, None,
                A.UNEVALUABLE, "retained-adverse-or-unidentified-paired-kinetics"))
            continue
        observed = tuple(Fraction(b) - Fraction(a) for a, b in zip(first.reduced_rates, second.reduced_rates, strict=True))
        expected = tuple(b - a for a, b in zip(_stationary_flux(member.constants, left.query),
            _stationary_flux(member.constants, right.query), strict=True))
        error = max(abs(a - b) / abs(b) if b else abs(a) for a, b in zip(observed, expected, strict=True))
        disposition = (A.FALSIFIED if A.FALSIFIED in (first.disposition, second.disposition)
            or error > Fraction(config.numerical_relative_tolerance)
            else A.UNEVALUABLE if A.UNEVALUABLE in (first.disposition, second.disposition) else A.SATISFIED)
        rows.append(GasContrastMember(member.member_id, member.outcome,
            tuple(map(_fraction_pair, observed)), tuple(map(_fraction_pair, expected)), _fraction_pair(error),
            disposition, "independent-rational-paired-stationary-flux"))
    return tuple(rows)


def _complete_disposition(rows):
    dispositions = tuple(row.disposition for row in rows)
    return (A.FALSIFIED if A.FALSIFIED in dispositions else A.UNEVALUABLE if A.UNEVALUABLE in dispositions
            else A.SATISFIED)


@dataclass(frozen=True, slots=True)
class GasContrastAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/kinetic-supply/gas-contrast-assessment"
    assessment_id: str
    configuration: GasContrastConfig
    left: KineticAssayBridgeResult
    right: KineticAssayBridgeResult
    members: tuple[GasContrastMember, ...]
    disposition: A
    fresh_biological_units: int = 0
    biological_predictive_calibration: str = "NOT_ESTABLISHED"

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        if type(self.configuration) is not GasContrastConfig:
            raise ValueError("gas contrast lacks its frozen scientific configuration")
        rows = _assessed_members(self.configuration, self.left, self.right)
        if (self.members != rows or self.disposition is not _complete_disposition(rows)
                or type(self.fresh_biological_units) is not int or self.fresh_biological_units != 0
                or self.biological_predictive_calibration != "NOT_ESTABLISHED"):
            raise ValueError("gas contrast changes independent arithmetic, complete adverse census or evidence ceiling")


def assess_gas_contrast(config, left, right):
    rows = _assessed_members(config, left, right)
    return GasContrastAssessment(CAPABILITY + ".assessment", config, left, right, rows, _complete_disposition(rows))


def development_root(config, *, study_id):
    config.__post_init__()
    source = identity(config, "config_id")
    claim = ClaimSpec("claim." + CAPABILITY, "world." + CAPABILITY, "population." + CAPABILITY,
        "Do paired numerical apparent-rate flux differences agree with independently derived stationary kinetics?",
        "One exposed paired analytical calculation with complete supplied/partial/rejected members; zero fresh biological units.",
        UNIT, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY,
        "Supplied gas-response arithmetic supplies no mutant prediction or calibrated biological uncertainty.",
        ("assumption.supplied-apparent-kinetics",), numerical_view_ids=(CAPABILITY + ".complete-paired-member-roster",))
    # Different W1 waves retain the same historical result_id. Their existing
    # logical artifact IDs distinguish the two exact input references without
    # rewriting either scientific record or manufacturing another unit.
    products = tuple(ObjectIdentity(product.artifact.artifact_id, product.record.object_schema,
        product.record.object_version, product.record.object_fingerprint)
        for product in (config.left_product, config.right_product))
    sources = (source, config.supply, config.left_parent, config.right_parent, config.left_query, config.right_query,
        *products, config.left_product.producing_receipt, config.right_product.producing_receipt)
    return DevelopmentStudySpec(study_id, claim.proposition, source, "world." + CAPABILITY,
        WorldKind.ANALYTIC_REFERENCE, (UNIT,), claim.numerical_view_ids, (claim,),
        tuple(sorted(sources, key=lambda row: row.object_id)))


def scope(config):
    return ScientificConditionScope(config.context.material.object_id, "world." + CAPABILITY, config.supply.object_id,
        ("carboxylation-flux-difference", "oxygenation-flux-difference"), ("s^-1", "s^-1"), CAPABILITY,
        "clock.stationary-supplied-kinetics", "Exact matched supplied kinetics; right-minus-left gas intervention; no biological units.",
        config.fingerprint(), instance_id=config.context.material.object_id)


def scientific_root_validator(config, context):
    if (type(context.root) is not DevelopmentStudySpec
            or context.root != development_root(config, study_id=context.root.study_id)
            or context.node_id != CAPABILITY or context.stage is not ScientificStage.FALSIFY
            or context.unit_ids != (UNIT,) or context.selected_unit_ids != (UNIT,) or context.complete_unit_census
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or len(context.config_inputs) != 1 or context.config_inputs[0].record != config):
        raise ValueError("gas contrast substitutes its exact paired development root or operation")
    links = tuple(row for row in context.links if row.consumer_node_id == CAPABILITY)
    if (len(links) != 2 or {row.consumer_input_id for row in links} != {"left", "right"}
            or any(row.producer_node_id is not None or row.producer_output_id is not None
                or row.external_input_id != "external." + CAPABILITY + "." + row.consumer_input_id
                or row.scientific_role != "OUTCOME" for row in links)):
        raise ValueError("gas contrast changes its two receipt-bound parent product roles")


def scientific_operand_sha256s(config):
    return tuple(sorted({config.fingerprint(), config.supply.object_fingerprint,
        config.left_parent.object_fingerprint, config.right_parent.object_fingerprint,
        config.left_product.record.object_fingerprint, config.right_product.record.object_fingerprint,
        config.left_product.producing_receipt.object_fingerprint, config.right_product.producing_receipt.object_fingerprint,
        config.left_query.object_fingerprint, config.right_query.object_fingerprint}))


def scientific_unit_ids(config):
    return (UNIT,)


class GasContrastRunner:
    def __init__(self):
        self.manifest = operation_declaration().manifest()

    def execute(self, context):
        try:
            if (context.task_id != CAPABILITY or context.permissions != self.manifest.permissions
                    or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE or context.resource_budget != BUDGET):
                raise ValueError("gas contrast changes its registered worker task/access")
            config_ports = tuple(port for port in context.input_ports if port.payload_schema == GasContrastConfig.SCHEMA)
            bridge_ports = tuple(port for port in context.input_ports if port.payload_schema == KineticAssayBridgeResult.SCHEMA)
            if len(config_ports) != 1 or len(bridge_ports) != 2 or len(context.input_ports) != 3:
                raise ValueError("gas contrast changes its complete typed worker input census")
            for port in context.input_ports:
                if (port.kind is not WorkerInputKind.EXTERNAL or port.media_type != MEDIA
                        or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                        or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
                    raise ValueError("gas contrast changes authenticated contribution input access")

            def read(port, record_type):
                raw = port.read()
                if len(raw) != port.size_bytes:
                    raise ValueError("gas contrast omits complete authenticated input bytes")
                return decode_canonical_bytes(raw, record_type, maximum_bytes=None)

            config = read(config_ports[0], GasContrastConfig)
            if (config_ports[0].artifact_id != context.config.artifact_id or config.config_id != context.config.config_id
                    or config.fingerprint() != context.config.content_sha256):
                raise ValueError("gas contrast substitutes its immutable configuration")
            bridges = {}
            ownership = {product.artifact.artifact_id: product.record
                for product in (config.left_product, config.right_product)}
            if {port.artifact_id for port in bridge_ports} != set(ownership):
                raise ValueError("gas contrast substitutes producing artifact ownership")
            for port in bridge_ports:
                product = read(port, KineticAssayBridgeResult)
                key = identity(product, "result_id")
                if key != ownership[port.artifact_id]:
                    raise ValueError("gas contrast changes the exact producing artifact/product join")
                if key in bridges:
                    raise ValueError("gas contrast duplicates a paired assay product")
                bridges[key] = product
            if set(bridges) != {config.left_product.record, config.right_product.record}:
                raise ValueError("gas contrast substitutes its original paired product identity")
            result = assess_gas_contrast(config, bridges[config.left_product.record], bridges[config.right_product.record])
            outputs = context.output_ports
            if (len(outputs) != 1 or outputs[0].output_id != CAPABILITY + ".assessment"
                    or outputs[0].payload_schema != GasContrastAssessment.SCHEMA
                    or outputs[0].profile is not ArtifactProfile.CANONICAL_JSON or outputs[0].media_type != MEDIA):
                raise ValueError("gas contrast changes its complete output contract")
            return RunnerResult((TaskOutputPayload(outputs[0].output_id, result.canonical_bytes()),),
                (ReceiptCheck("complete-independent-rational-gas-contrast", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_declaration():
    from .gas_contrast_translation import scientific_work

    return RecursiveOperationDeclaration(capability_key=CAPABILITY, capability_version="1.0.0",
        implementation_id="independent-rational-paired-apparent-flux-v1", kind=CapabilityKind.FALSIFIER,
        config_record_type=GasContrastConfig, stage=ScientificStage.FALSIFY,
        input_ports=tuple(RecursivePortContract(side, KineticAssayBridgeResult.SCHEMA, MEDIA, None) for side in ("left", "right")),
        outputs=(OutputTemplate("assessment", GasContrastAssessment.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA, ".json"),),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=BUDGET,
        conformance_check_ids=("complete-adverse-roster", "exact-paired-receipted-query-material", "independent-fraction-flux-difference"),
        runner_factory=GasContrastRunner, record_codecs={record.SCHEMA: record for record in
            (GasContrastConfig, GasContrastAssessment, GasContrastMember, KineticAssayBridgeResult)},
        scientific_hooks=RecursiveScientificHooks(
            scientific_operand_sha256s=scientific_operand_sha256s,
            scientific_unit_ids=scientific_unit_ids, scientific_root_validator=scientific_root_validator),
        inquiry_hooks=RecursiveInquiryHooks(inquiry_work_projector=scientific_work))
