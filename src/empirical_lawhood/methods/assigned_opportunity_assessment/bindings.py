# SPDX-License-Identifier: MPL-2.0
"""Existing typed recursive seams for the finite author and independent assessor."""

from dataclasses import replace
from functools import partial

from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_claim_assessment import InquiryClaimAssessment
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import ScientificInquiryWork
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition, AssessmentPhase, RequirementSupplyAssessment
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.design.inquiry_methods import AssignedInquiryOpportunity, DependentAssessmentContract, FixedOpportunityStopping, FrozenInquiryConsumer, FrozenInquiryProcedure, InquiryAuthorContract, InquiryMethodEvidence
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.execution.capabilities import CapabilityKind
from empirical_lawhood.execution.execution import RunnerResult, TaskOutputPayload
from empirical_lawhood.execution.plans import OutputTemplate
from empirical_lawhood.execution.recursive_compiler import RecursivePortContract
from empirical_lawhood.execution.recursive_provider import RecursiveInquiryHooks, RecursiveOperationDeclaration, RecursiveScientificHooks

from empirical_lawhood.methods.assigned_opportunity_assessment import design, science
from empirical_lawhood.methods.assigned_opportunity_assessment.records import ACCESS, MAX_BYTES, NAMESPACE, OpportunityAssessment, OpportunityAuthorInput, OpportunityConsumer, OpportunityOperationConfig, OpportunityOutcome, OpportunityOutcomes, OpportunitySource, implementation, method


def record_codecs():
    return {t.SCHEMA: t for t in (OpportunitySource, OpportunityAuthorInput, OpportunityOutcome, OpportunityOutcomes,
        OpportunityConsumer, OpportunityOperationConfig, OpportunityAssessment, AssignedInquiryOpportunity,
        DependentAssessmentContract, FixedOpportunityStopping, FrozenInquiryConsumer, FrozenInquiryProcedure,
        InquiryAuthorContract, InquiryMethodEvidence)}


def record_identity(record):
    if type(record) is FrozenInquiryProcedure:
        return record.identity
    if type(record) is OpportunityOperationConfig:
        return ObjectIdentity.from_record(record.config_id, record)
    if type(record) in (OpportunitySource, OpportunityAuthorInput, OpportunityOutcomes, OpportunityConsumer, OpportunityAssessment):
        return record.identity
    raise TypeError("opportunity extension has no identity projection for this exact record revision")


def units(config):
    return (config.source.independent_unit_id,)


def operands(config):
    values = (config.source.identity, config.consumer.identity, config.author.identity)
    if config.assessment is not None:
        values = (*values, config.assessment.identity)
    return tuple(sorted({p.object_fingerprint for p in values}))


def root_validator(config, context):
    selected = tuple(v.record for v in context.config_inputs)
    assessors = tuple(c for c in selected if type(c) is OpportunityOperationConfig and c.phase == "assess")
    if len(assessors) != 1:
        raise ValueError("opportunity design requires its independent assessor")
    assessor, = assessors
    if (tuple(sorted(selected, key=lambda c: c.node_id)) != (assessor, design.author_config(assessor))
            or config not in selected or context.node_id != config.node_id
            or context.root != design.scientific_root(assessor)
            or context.requirements != (design.scientific_contract(config.source)[0],)
            or context.connections != (design.scientific_contract(config.source)[1],)
            or context.links != design.links_for(assessor) or context.external_inputs != design.external_contracts(assessor)
            or context.unit_ids != units(config) or context.selected_unit_ids != units(config)
            or context.stage is not design.stage(config.phase) or context.complete_unit_census
            or context.outcome_access is not ACCESS or context.visibility_ceiling is not design.VISIBILITY):
        raise ValueError("opportunity design changes its original dependence, complete census, scope or information roles")


def assessment_projector(record, requirement, connection):
    if type(record) is not OpportunityAssessment:
        return ()
    record.__post_init__()
    if (requirement, connection) != design.scientific_contract(record.config.source):
        raise ValueError("opportunity assessment substitutes its exact requirement or consumer connection")
    evidence = tuple(sorted((record.procedure.identity, record.identity), key=lambda p: p.object_id))
    return tuple(RequirementSupplyAssessment("assessment." + record.record_id + "." + phase.value.lower(),
        ObjectIdentity.from_record(requirement.requirement_id, requirement),
        ObjectIdentity.from_record(connection.connection_id, connection), phase,
        AssessmentDisposition(record.disposition) if phase is AssessmentPhase.JOINED else AssessmentDisposition.SATISFIED,
        record.config.node_id, evidence, record.reason_codes if phase is AssessmentPhase.JOINED else ())
        for phase in AssessmentPhase)


def config_from_draft(draft):
    operations = tuple(op for op in draft.operations if op.node_id in draft.selected_operation_ids)
    if tuple(op.node_id for op in operations) != (NAMESPACE + ".assess", NAMESPACE + ".author"):
        raise ValueError("opportunity inquiry changes its complete two-operation census")
    configs = tuple(decode_canonical_bytes(op.config_payload.encode(), OpportunityOperationConfig,
                   maximum_bytes=MAX_BYTES) for op in operations)
    config = configs[0]
    if (configs != (config, design.author_config(config))
            or any(op.selection != method(c.phase) or op.config_id != c.config_id
                   for op, c in zip(operations, configs, strict=True))
            or draft.development_study != design.scientific_root(config)
            or draft.requirements != (design.scientific_contract(config.source)[0],)
            or draft.connections != (design.scientific_contract(config.source)[1],)
            or draft.links != design.links_for(config) or draft.external_inputs != design.external_contracts(config)):
        raise ValueError("opportunity inquiry substitutes its original scientific design")
    return config, operations[0]


def endpoint_validator(draft, endpoint):
    config, _ = config_from_draft(draft)
    if endpoint != design.condition_scope(config.source):
        raise ValueError("opportunity inquiry changes its exact scope, cutoff or receiver")


def authenticated_assessment(draft, products):
    """Validate retained scientific operands and actual producing receipt joins."""
    config, operation = config_from_draft(draft)
    found = {}
    for phase, kind in (("author", FrozenInquiryProcedure), ("assess", OpportunityAssessment)):
        node = NAMESPACE + "." + phase
        outputs, receipt = products["records"].get(node, {}), products["receipts"].get(node)
        if not outputs:
            continue
        value = outputs.get(node + ".product")
        if (len(outputs) != 1 or type(value) is not kind or receipt is None
                or receipt.task_id != node or receipt.operational_status is not OperationalStatus.SUCCEEDED
                or sum(v.payload_schema == value.SCHEMA and v.content_sha256 == value.fingerprint()
                       for v in receipt.output_logical_artifacts) != 1):
            raise ValueError("opportunity result lacks its exact successful original producing receipt")
        value.__post_init__()
        found[phase] = value
    if "assess" not in found:
        return None
    record = found["assess"]
    if (record.config != config or found.get("author") != record.procedure
            or products["receipts"][NAMESPACE + ".author"].run_id != products["receipts"][operation.node_id].run_id):
        raise ValueError("opportunity result substitutes original consumer, procedure or execution")
    return record


def outcome_projector(draft, specification, products):
    config, operation = config_from_draft(draft)
    endpoint_validator(draft, specification.endpoint)
    if specification.distinguishing_assessment != operation.config_identity:
        raise ValueError("opportunity inquiry substitutes its selected assessor revision")
    record = authenticated_assessment(draft, products)
    if record is None or record.disposition == "UNEVALUABLE":
        return "unresolved"
    return "useful-supply" if record.disposition == "SATISFIED" else "scoped-failure"


def claim_assessment_projector(draft, specification, products):
    config, operation = config_from_draft(draft)
    claims = tuple(c for c in draft.development_study.claims
                   if ObjectIdentity.from_record(c.claim_id, c) in specification.target.required_claims)
    if not claims:
        return ()
    endpoint_validator(draft, specification.target.scope)
    if specification.distinguishing_assessment != operation.config_identity:
        raise ValueError("opportunity target changes its exact selected assessment contract")
    record = authenticated_assessment(draft, products)
    if record is None:
        return ()
    receipt = products["receipts"][operation.node_id]
    return tuple(InquiryClaimAssessment(claim, operation.config_identity, record.identity,
        ObjectIdentity.from_record(receipt.receipt_id, receipt), config.assessment.scope,
        AssessmentDisposition(record.disposition),
        tuple(sorted((record.identity, record.procedure.identity, record.outcomes.identity), key=lambda p: p.object_id)),
        units(config), config.source.numerical_view_ids, EvidenceCeiling.NON_PROMOTABLE, ACCESS, design.VISIBILITY)
        for claim in claims)


def scientific_work(draft, task_id):
    config, _ = config_from_draft(draft)
    phase = task_id.removeprefix(NAMESPACE + ".")
    if phase not in ("author", "assess"):
        raise ValueError("opportunity work names an absent original operation")
    selected = method(phase)
    scientific = (config.source.identity, config.consumer.identity, config.author.identity)
    if phase == "assess":
        scientific = (*scientific, config.assessment.identity)
    return ScientificInquiryWork(ObjectIdentity.from_record(selected.capability_key + ".v" + selected.capability_version, selected),
        tuple(sorted(scientific, key=lambda p: p.object_id)), design.condition_scope(config.source),
        config.author.identity if phase == "author" else config.assessment.identity)


class Runner:
    def __init__(self, *, manifest):
        self.manifest = manifest

    def execute(self, context):
        try:
            codecs = record_codecs()
            received = {}
            for port in context.input_ports:
                kind = codecs.get(port.payload_schema)
                if (kind not in (OpportunityOperationConfig, OpportunityAuthorInput, OpportunityOutcomes, FrozenInquiryProcedure)
                        or kind in received or port.media_type != "application/json" or port.outcome_access is not ACCESS):
                    raise ValueError("opportunity worker changes its exact input role or census")
                received[kind] = decode_canonical_bytes(port.read(), kind, maximum_bytes=MAX_BYTES)
            config = received.pop(OpportunityOperationConfig)
            if (context.task_id != config.node_id or context.config.config_id != config.config_id
                    or context.config.content_sha256 != config.fingerprint()
                    or context.resource_budget != design.BUDGET or context.permissions != design.PERMISSIONS
                    or context.outcome_access is not ACCESS):
                raise ValueError("opportunity worker changes its compiled execution contract")
            if config.phase == "author" and set(received) == {OpportunityAuthorInput}:
                product = science.author(config, received[OpportunityAuthorInput])
            elif config.phase == "assess" and set(received) == {FrozenInquiryProcedure, OpportunityOutcomes}:
                product = science.assess(config, received[FrozenInquiryProcedure], received[OpportunityOutcomes])
            else:
                raise ValueError("opportunity worker crosses its actor/evaluator information boundary")
            if (len(context.output_ports) != 1 or context.output_ports[0].output_id != context.task_id + ".product"
                    or context.output_ports[0].payload_schema != product.SCHEMA
                    or context.output_ports[0].profile is not ArtifactProfile.CANONICAL_JSON):
                raise ValueError("opportunity worker substitutes its original result contract")
            payload = product.canonical_bytes()
            if len(payload) > MAX_BYTES:
                raise ValueError("opportunity result exceeds the declared canonical byte bound")
            return RunnerResult((TaskOutputPayload(context.task_id + ".product", payload),),
                (ReceiptCheck("assigned-opportunity-original-roots-and-census", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_declarations():
    from empirical_lawhood.methods.assigned_opportunity_assessment.portability import describe_contributions

    rows = []
    for phase in ("assess", "author"):
        ports = (("outcomes", OpportunityOutcomes), ("procedure", FrozenInquiryProcedure)) if phase == "assess" else (("actor", OpportunityAuthorInput),)
        output = OpportunityAssessment if phase == "assess" else FrozenInquiryProcedure
        row = RecursiveOperationDeclaration(capability_key=NAMESPACE + "." + phase, capability_version="1.0.0",
            implementation_id=NAMESPACE + ".exact-finite-census." + phase + ".v1", implementation_sha256=implementation(phase),
            kind=CapabilityKind.FALSIFIER if phase == "assess" else CapabilityKind.TRANSFORM,
            config_record_type=OpportunityOperationConfig, stage=design.stage(phase),
            input_ports=tuple(RecursivePortContract(name, kind.SCHEMA, "application/json", MAX_BYTES) for name, kind in ports),
            outputs=(OutputTemplate("product", output.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),),
            permissions=design.PERMISSIONS, evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
            outcome_access=ACCESS, visibility_ceiling=design.VISIBILITY, resources=design.BUDGET,
            conformance_check_ids=("assigned-opportunity-complete-dependent-census", "assigned-opportunity-independent-enclosure"),
            runner_factory=Runner, record_codecs=record_codecs(),
            scientific_hooks=RecursiveScientificHooks(assessment_projector=assessment_projector,
                scientific_operand_sha256s=operands, scientific_unit_ids=units, scientific_root_validator=root_validator),
            inquiry_hooks=RecursiveInquiryHooks(contribution_describer=describe_contributions if phase == "assess" else None,
                inquiry_endpoint_validator=endpoint_validator,
                inquiry_record_identity=record_identity, inquiry_work_projector=scientific_work,
                inquiry_outcome_projector=outcome_projector,
                inquiry_claim_assessment_projector=claim_assessment_projector if phase == "assess" else None))
        rows.append(replace(row, runner_factory=partial(Runner, manifest=row.manifest())))
    return tuple(rows)
