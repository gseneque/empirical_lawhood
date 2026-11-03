# SPDX-License-Identifier: MPL-2.0
"""One declaration per later-phase conditional scientific calculation."""

from dataclasses import dataclass, replace
from functools import partial
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.recursive_authoring import (
    RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft,
)
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationDeclaration, RecursiveScientificHooks

from .records import MatrixFrozenConsumerPackage, MatrixLaterExperimentSpecification, MatrixProgrammeEvidence, MatrixProgrammeRoster
from .science import MatrixFunctionalAssessment, MatrixPreparationNomination, assess_later_programme, nominate_preparation


NAMESPACE = "matrix-later-programme"
BUDGET = ResourceBudget(1, None, 0, None, None, None)
QUESTION = "Assess the complete declared preparation opportunity, fresh matched contrast or two frozen-account transfer regimes from original saved products."
WORLD = "world.matrix-later-programme.conditional-saved-products"
INPUT_TYPES = {"allocation": UnitAllocation, "specification": MatrixLaterExperimentSpecification,
    "roster": MatrixProgrammeRoster, "package": MatrixFrozenConsumerPackage, "evidence": MatrixProgrammeEvidence,
    "nomination": MatrixPreparationNomination}
OPERATIONS = {"E5_OPPORTUNITY": "preparation-opportunity", "E5_CONFIRMATION": "preparation-confirmation", "E6_TRANSFER": "transfer-assess"}


@dataclass(frozen=True, slots=True)
class MatrixLaterOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/operation-config"
    config_id: str
    phase: str
    specification: ObjectIdentity
    allocation: ObjectIdentity
    roster: ObjectIdentity
    package: ObjectIdentity
    evidence: ObjectIdentity
    unit_ids: tuple[str, ...]
    nomination: ObjectIdentity | None
    input_size_bytes: tuple[tuple[str, int], ...]

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if (self.phase not in OPERATIONS or self.config_id != "config." + node_id(self.specification, self.phase)
                or type(self.unit_ids) is not tuple or not self.unit_ids or self.unit_ids != tuple(sorted(set(self.unit_ids)))):
            raise ValueError("later operation configuration changes its declared phase or complete whole-group census")
        for name in ("specification", "allocation", "roster", "package", "evidence"):
            value = getattr(self, name)
            if type(value) is not ObjectIdentity or value.object_schema != INPUT_TYPES[name].SCHEMA:
                raise ValueError("later operation substitutes a frozen original scientific operand")
        if (self.phase == "E5_CONFIRMATION") != (self.nomination is not None):
            raise ValueError("later operation loses its actual pre-confirmation nomination")
        expected = tuple(sorted(name for name in INPUT_TYPES if name != "nomination" or self.nomination is not None))
        if (type(self.input_size_bytes) is not tuple or tuple(name for name, _ in self.input_size_bytes) != expected
                or any(type(size) is not int or size < 1 for _, size in self.input_size_bytes)):
            raise ValueError("later operation loses its complete exact original input byte census")


def node_id(specification, phase):
    return NAMESPACE + "." + OPERATIONS[phase] + "." + specification.object_fingerprint


def operand_digests(config):
    return tuple(sorted({getattr(config, name).object_fingerprint for name in
        ("specification", "allocation", "roster", "package", "evidence", "nomination") if getattr(config, name) is not None}))


def scientific_units(config):
    return config.unit_ids


def development_root(config, study_id):
    operands = tuple(sorted((getattr(config, name) for name in
        ("specification", "allocation", "roster", "package", "evidence", "nomination") if getattr(config, name) is not None),
        key=lambda row: row.object_id))
    claim = ClaimSpec("claim." + study_id, WORLD, "rule.matrix-later.complete-functional-calculation", QUESTION,
        "Retain every assigned whole group, every nested arm/view, nonuse and uncertainty bound; exact frozen criteria and original scores govern the conditional calculation.",
        "unit.matrix-later.whole-independent-group", None, EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        "This saved-product calculation authenticates no original source, sampling assumption, pre-fit act, protected reveal or scientific qualification.",
        ("assumption.matrix-later.original-source-and-sampling-remain-separate",))
    return DevelopmentStudySpec(study_id, QUESTION, config.package, WORLD, WorldKind.NUMERICAL_SIMULATOR,
        config.unit_ids, (), (claim,), operands)


def root_validator(config, context):
    if (context.node_id != node_id(config.specification, config.phase)
            or context.root != development_root(config, context.root.study_id)
            or context.unit_ids != config.unit_ids or context.complete_unit_census
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or context.stage is not (ScientificStage.DEVELOP if config.phase == "E5_OPPORTUNITY" else ScientificStage.FALSIFY)):
        raise ValueError("later scientific operation changes its complete conditional source/phase/whole-group context")
    selected = tuple(row.record for row in context.config_inputs)
    if selected != (config,):
        raise ValueError("later saved-product assessment is one declared complete scientific operation")
    expected = {name for name in INPUT_TYPES if name != "nomination" or config.nomination is not None}
    incoming = tuple(row for row in context.links if row.consumer_node_id == context.node_id)
    if (len(incoming) != len(expected) or {row.consumer_input_id for row in incoming} != expected
            or any(row.external_input_id != "external." + row.consumer_input_id
                or row.producer_node_id is not None or row.scientific_role != "SOURCE" for row in incoming)):
        raise ValueError("later scientific operation changes its exact selected original operand census")
    external = tuple(RecursiveExternalInput("external." + name, getattr(config, name).object_id,
        INPUT_TYPES[name].SCHEMA, "application/json", size, OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY, getattr(config, name).object_fingerprint, "SOURCE")
        for name, size in config.input_size_bytes)
    if tuple(context.external_inputs) != external:
        raise ValueError("later scientific operation substitutes exact original external identity/digest/size/access contracts")


class MatrixLaterRunner:
    def __init__(self, phase):
        self.phase = phase
        capability_key = NAMESPACE + "." + OPERATIONS[phase]
        self.manifest = next(row.manifest() for row in operation_declarations()
            if row.capability_key == capability_key)

    def execute(self, context):
        codecs = {kind.SCHEMA: kind for kind in (*INPUT_TYPES.values(), MatrixLaterOperationConfig)}
        records = {}
        try:
            for port in context.input_ports:
                kind = codecs.get(port.payload_schema)
                if kind is None or port.payload_schema in records:
                    raise ValueError("later worker receives an extra or repeated original record schema")
                raw = port.read()
                records[port.payload_schema] = decode_canonical_bytes(raw, kind, maximum_bytes=port.size_bytes)
            config = records.pop(MatrixLaterOperationConfig.SCHEMA)
            if (config.phase != self.phase or
                    (context.config.config_id, context.config.content_sha256) != (config.config_id, config.fingerprint())):
                raise ValueError("later worker substitutes its frozen configuration")
            selected = {name: records[kind.SCHEMA] for name, kind in INPUT_TYPES.items() if kind.SCHEMA in records}
            expected = {name for name in INPUT_TYPES if name != "nomination" or config.nomination is not None}
            if set(selected) != expected:
                raise ValueError("later worker omits or adds a scientific operand")
            for name in expected:
                record = selected[name]
                actual = record.identity if name != "allocation" else record.identity
                if actual != getattr(config, name):
                    raise ValueError("later worker replaces exact original record bytes")
            from .science import source_allocation
            if selected["allocation"] != source_allocation(selected["specification"], selected["roster"]):
                raise ValueError("later worker replaces its whole-group allocation")
            arguments = tuple(selected[name] for name in ("specification", "roster", "package", "evidence"))
            product = (nominate_preparation(*arguments, result_id="result." + context.task_id)
                if config.phase == "E5_OPPORTUNITY" else assess_later_programme(*arguments,
                    result_id="result." + context.task_id, nomination=selected.get("nomination")))
            output, = context.output_ports
            if output.payload_schema != product.SCHEMA or output.output_id != context.task_id + ".product":
                raise ValueError("later worker replaces its actual complete compiler-derived output")
            return RunnerResult((TaskOutputPayload(output.output_id, product.canonical_bytes()),),
                (ReceiptCheck("complete-later-matrix-conditional-functional-calculation", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_declarations():
    codecs = {kind.SCHEMA: kind for kind in (*INPUT_TYPES.values(), MatrixLaterOperationConfig, MatrixFunctionalAssessment)}
    return tuple(RecursiveOperationDeclaration(
        NAMESPACE + "." + operation, "1.0.0", NAMESPACE + "." + operation + ".original-products-v1",
        CapabilityKind.ANALYSIS if phase == "E5_OPPORTUNITY" else CapabilityKind.FALSIFIER,
        MatrixLaterOperationConfig, ScientificStage.DEVELOP if phase == "E5_OPPORTUNITY" else ScientificStage.FALSIFY,
        tuple(sorted((RecursivePortContract(name, kind.SCHEMA, "application/json", None,
            minimum_count=0 if name == "nomination" else 1) for name, kind in INPUT_TYPES.items()), key=lambda row: row.port_id)),
        (OutputTemplate("product", MatrixPreparationNomination.SCHEMA if phase == "E5_OPPORTUNITY" else MatrixFunctionalAssessment.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),),
        tuple(sorted((CapabilityPermission.READ_DEVELOPMENT, CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS))), EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, BUDGET,
        tuple(sorted(("whole-group-complete-functional-denominator", "unchanged-frozen-account", "conditional-sampling-no-qualification"))),
        partial(MatrixLaterRunner, phase), codecs,
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=operand_digests,
            scientific_unit_ids=scientific_units, scientific_root_validator=root_validator),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,),
        input_record_types=tuple(sorted(INPUT_TYPES.values(), key=lambda kind: kind.SCHEMA)))
        for phase, operation in sorted(OPERATIONS.items(), key=lambda row: row[1]))


@dataclass(frozen=True, slots=True)
class LoweredMatrixLaterExperiment:
    draft: RecursiveStudyDraft
    input_records: tuple[tuple[str, CanonicalRecord], ...]


def lower_later_experiment(specification, roster, package, evidence, *, allocation, campaign, nomination=None):
    references = dict(specification=specification.identity, allocation=allocation.identity,
        roster=roster.identity, package=package.identity, evidence=evidence.identity)
    node = node_id(specification.identity, specification.phase)
    records = dict(specification=specification, allocation=allocation, roster=roster, package=package, evidence=evidence)
    if nomination is not None:
        records["nomination"] = nomination
    config = MatrixLaterOperationConfig("config." + node, specification.phase, **references,
        unit_ids=allocation.unit_ids(), nomination=None if nomination is None else nomination.identity,
        input_size_bytes=tuple((name, len(record.canonical_bytes())) for name, record in sorted(records.items())))
    declaration = next(row for row in operation_declarations() if row.capability_key == NAMESPACE + "." + OPERATIONS[specification.phase])
    operation = RecursiveOperationSpec.from_config(node_id=node, selection=declaration.registration().selection,
        config_id=config.config_id, config=config, obligation_ids=("obligation." + node,), resource_budget=BUDGET)
    externals = tuple(RecursiveExternalInput("external." + key, references[key].object_id if key in references else record.identity.object_id,
        record.SCHEMA, "application/json", len(record.canonical_bytes()), OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY, record.fingerprint(), "SOURCE") for key, record in sorted(records.items()))
    links = tuple(RecursiveInputLink("edge." + node + "." + key, node, key, external_input_id="external." + key,
        scientific_role="SOURCE") for key in sorted(records))
    study = development_root(config, "study." + node)
    selected_campaign = replace(campaign, objective=QUESTION, system_ids=(study.system.object_id,), world_ids=(WORLD,),
        target_claim_ids=tuple(claim.claim_id for claim in study.claims))
    draft = RecursiveStudyDraft("draft." + node, QUESTION, selected_campaign, (), (), (), (operation,), externals,
        links, (node,), development_study=study)
    return LoweredMatrixLaterExperiment(draft, tuple(("external." + key, record) for key, record in sorted(records.items())))
