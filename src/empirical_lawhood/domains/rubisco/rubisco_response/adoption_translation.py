# SPDX-License-Identifier: MPL-2.0
"""Current-use contributions and inquiry semantics on the shared runtime."""

from hashlib import sha256

from empirical_lawhood.science.identity.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import ScientificInquiryWork
from empirical_lawhood.science.inquiry.recursive_requirements import ContributionRole, DevelopmentStudySpec
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.science.inquiry.scientific_contributions import ContributionManifest, ContributionProduct
from empirical_lawhood.science.records.status import LifecycleStatus, OperationalStatus
from empirical_lawhood.science.models.worlds import WorldKind
from empirical_lawhood.design.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.design.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.design.recursive_input_origins import RecursiveInputOrigin, RecursiveInputOriginKind, RecursiveInputOrigins, contribution_graph_role
from empirical_lawhood.execution.plans import ScientificStage
from empirical_lawhood.execution.recursive_inquiry import InquiryEvidenceBinding
from empirical_lawhood.domains.rubisco.rubisco_response.adoption import CAPABILITY, CurrentResponseUse, ResponseAdoptionConfig, adoption_connection, adoption_scope, assess_retained_response, identity
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.operation_bindings import BUDGET, MAX_INPUT_BYTES, MEDIA
from empirical_lawhood.domains.rubisco.rubisco_response.paired_prediction import source_union
from empirical_lawhood.domains.rubisco.rubisco_response.study_science import ResponseAssessment, ResponsePredictions


def scientific_operands(config):
    return source_union((identity(config, "config_id"), config.original_science.identity, config.current_science.identity,
        identity(config.parent, "contribution_id"), config.current_science.cases.identity,
        config.current_science.allocation.identity),
        tuple(value for product in (config.prediction, config.assessment) for value in (
            ObjectIdentity(product.artifact.artifact_id, product.record.object_schema,
                           product.record.object_version, product.record.object_fingerprint), product.producing_receipt)))


def scientific_unit_ids(config):
    return config.current_science.allocation.unit_ids()


def native_effect_slot_ids(config):
    exact(config, ResponseAdoptionConfig)
    return ()


def graph_contracts(config):
    requirement, connection = adoption_connection(config)
    external, links = [], []
    for name, product in (("assessment", config.assessment), ("prediction", config.prediction)):
        input_id = "external." + CAPABILITY + "." + name
        role = contribution_graph_role(product.role)
        external.append(RecursiveExternalInput(input_id, product.artifact.artifact_id, product.record.object_schema,
            MEDIA, product.artifact.size_bytes, product.outcome_access, product.visibility_ceiling,
            product.record.object_fingerprint, role))
        links.append(RecursiveInputLink("edge." + CAPABILITY + "." + name, CAPABILITY, name,
            external_input_id=input_id, scientific_role=role,
            requirement_id=requirement.requirement_id if name == "prediction" else None,
            connection_id=connection.connection_id if name == "prediction" else None))
    return (requirement,), (connection,), tuple(external), tuple(links)


def development_root(config, *, study_id):
    exact(config, ResponseAdoptionConfig)
    _, connection = adoption_connection(config)
    views = tuple(sorted({view for unit in config.current_science.allocation.units for view in unit.numerical_view_ids}))
    claim = ClaimSpec(connection.claim_id, adoption_scope(config).world_id,
        "population.rubisco-response.exposed-analytical",
        "Are complete original paired predictions adequate for the explicitly selected current conditional decision?",
        "Original exposure groups retain all nested cases, scenarios and numerical points; no fresh biological units.",
        "unit.original-exposure-group", None, EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        "Current-use assessment preserves original receipts and exposure; prediction validity and computational benefit remain open.",
        ("assumption.rubisco-response.conditional-four-state",), numerical_view_ids=views)
    return DevelopmentStudySpec(study_id, claim.proposition, config.current_science.cases.identity,
        claim.world_id, WorldKind.ANALYTIC_REFERENCE, scientific_unit_ids(config), views, (claim,), scientific_operands(config))


def validate_root(config, context):
    requirements, connections, external, links = graph_contracts(config)
    if (type(context.root) is not DevelopmentStudySpec
            or context.root != development_root(config, study_id=context.root.study_id)
            or context.node_id != CAPABILITY or context.stage is not ScientificStage.FALSIFY
            or context.unit_ids != scientific_unit_ids(config) or context.selected_unit_ids != scientific_unit_ids(config)
            or context.complete_unit_census or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or len(context.config_inputs) != 1 or context.config_inputs[0].record is not config
            or context.config_inputs[0].node_id != CAPABILITY
            or context.requirements != requirements or context.connections != connections
            or context.external_inputs != external or context.links != links):
        raise ValueError("retained response use changes its exact original inputs, current criteria, units or connection")


def response_adoption_draft(config, *, draft_id=None):
    from empirical_lawhood.domains.rubisco.rubisco_response.adoption_operation import operation_declaration

    exact(config, ResponseAdoptionConfig)
    draft_id = "draft." + CAPABILITY + "." + config.fingerprint() if draft_id is None else draft_id
    root = development_root(config, study_id="study." + draft_id)
    policy = AuthorityPolicy("policy." + draft_id, "owner.local-researcher", "operator.local-development",
        (root.study_id,), frozenset((root.world_kind,)),
        frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION, AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)), ("gate.local-nonactuating-development",), frozenset(), BUDGET,
        OutcomeAccess.DEVELOPMENT_VISIBLE)
    node = CampaignNode("design." + draft_id, CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
        identity(root, "study_id"), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec("campaign." + draft_id, root.question, (root.system.object_id,), (root.world_id,),
        tuple(row.claim_id for row in root.claims), BUDGET, identity(policy, "policy_id"),
        (DecisionRight("decision-right." + draft_id, AuthorityAction.SIMULATION_EXECUTION,
                       "owner.local-researcher", policy.policy_id, False),),
        (node,), (node.node_id,), (node.node_id,), (), LifecycleStatus.ACTIVE)
    operation = RecursiveOperationSpec.from_config(node_id=CAPABILITY, selection=operation_declaration().registration().selection,
        config_id=config.config_id, config=config, obligation_ids=("obligation." + CAPABILITY + ".complete-retained-use",),
        resource_budget=BUDGET)
    requirements, connections, external, links = graph_contracts(config)
    return RecursiveStudyDraft(draft_id, root.question, campaign, requirements, connections, (), (operation,),
        external, links, (CAPABILITY,), development_study=root, contribution_parents=(config.parent,))


def selected_config(draft):
    from empirical_lawhood.domains.rubisco.rubisco_response.adoption_operation import operation_declaration

    if len(draft.operations) != 1 or draft.selected_operation_ids != (CAPABILITY,) or draft.development_study is None:
        raise ValueError("response adoption requires its complete single-assessor selection")
    operation = draft.operations[0]
    config = decode_canonical_bytes(operation.config_payload.encode(), ResponseAdoptionConfig, maximum_bytes=MAX_INPUT_BYTES)
    if (operation.node_id != CAPABILITY or operation.config_identity != identity(config, "config_id")
            or operation.selection != operation_declaration().registration().selection or operation.resource_budget != BUDGET
            or draft != response_adoption_draft(config, draft_id=draft.draft_id)):
        raise ValueError("response adoption changes its current criterion or complete original contribution closure")
    return config


def response_adoption_origins(draft):
    config = selected_config(draft)
    parent = identity(config.parent, "contribution_id")
    origins = RecursiveInputOrigins(tuple(RecursiveInputOrigin("external." + CAPABILITY + "." + name,
        RecursiveInputOriginKind.CONTRIBUTION, product.record.object_fingerprint, product.role.value,
        parent, product.product_id, product.producing_receipt)
        for name, product in (("assessment", config.assessment), ("prediction", config.prediction))))
    origins.validate_draft(draft)
    return origins


def scientific_work(draft, operation_id):
    config = selected_config(draft)
    if operation_id != CAPABILITY:
        raise ValueError("response adoption changes its exact selected work")
    operands = scientific_operands(config)
    return ScientificInquiryWork(identity(config, "config_id"), operands, adoption_scope(config),
        ObjectIdentity.from_record("observation." + CAPABILITY, config))


def record_identity(record):
    exact(record, CurrentResponseUse)
    return record.identity


def actual_use(draft, products):
    config = selected_config(draft)
    found = tuple(row for row in products["records"].get(CAPABILITY, {}).values() if type(row) is CurrentResponseUse)
    receipt = products["receipts"].get(CAPABILITY)
    if not found or receipt is None:
        return config, None, None, None
    if len(found) != 1 or receipt.task_id != CAPABILITY or receipt.operational_status is not OperationalStatus.SUCCEEDED:
        raise ValueError("response adoption contribution changes its actual current-use receipt")
    record, = found
    expected = assess_retained_response(config, record.original_prediction, record.original_assessment, use_id=record.use_id)
    if record != expected:
        raise ValueError("response adoption contribution fails original/current independent assessment")
    logicals = tuple(row for row in receipt.output_logical_artifacts
                     if row.payload_schema == record.SCHEMA and row.content_sha256 == record.fingerprint())
    if len(logicals) != 1 or logicals[0].logical_artifact_id not in products["outputs"]:
        raise ValueError("response adoption contribution lacks its original physical output binding")
    logical, = logicals
    artifact = products["outputs"][logical.logical_artifact_id]
    physical = artifact.materialization
    if (artifact.logical != logical or physical not in receipt.output_materializations
            or physical.size_bytes != len(record.canonical_bytes()) or physical.physical_sha256 != record.fingerprint()
            or physical.compression != "none"):
        raise ValueError("response adoption contribution changes complete retained current-use bytes")
    return config, record, receipt, artifact


def describe_contributions(draft, products):
    config, record, receipt, artifact = actual_use(draft, products)
    if record is None:
        return ()
    product = ContributionProduct("product." + CAPABILITY, record.identity,
        ArtifactIdentity(artifact.logical.logical_artifact_id, "independent-current-response-use", record.SCHEMA,
            record.fingerprint(), MEDIA, artifact.materialization.size_bytes), identity(receipt, "receipt_id"),
        ContributionRole.RETAINED_ANALYSIS_INPUT, EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)
    current = record.current_assessment
    remaining = tuple(row for row in current.graph.requirements if row.requirement_id in current.remaining_requirement_ids)
    return (ContributionManifest("contribution." + CAPABILITY + "." + record.fingerprint()[:24], draft.question,
        "Distinct current-use conditional decision " + current.conditional_candidate_action
        + "; original exposure and receipts retained; combined milestone OPEN.",
        adoption_scope(config), (product,), (record.identity,), remaining, (identity(config.parent, "contribution_id"),)),)


def next_wave_builder(draft, manifest, products):
    if describe_contributions(draft, products) != (manifest,):
        raise ValueError("current-use successor changes its actual retained contribution")
    return None


def endpoint_validator(draft, endpoint):
    if endpoint != adoption_scope(selected_config(draft)):
        raise ValueError("current-use inquiry changes its selected scientific scope")


def outcome_projector(draft, specification, products):
    endpoint_validator(draft, specification.endpoint)
    if specification.distinguishing_assessment != draft.operations[0].config_identity:
        raise ValueError("current-use inquiry substitutes its independent assessor")
    _, record, _, _ = actual_use(draft, products)
    return "unresolved" if record is None or record.current_assessment.conditional_candidate_action == "HOLD" else "useful-supply"


def evidence_projector(draft, payloads, products=None):
    config = selected_config(draft)
    views = draft.development_study.numerical_view_ids
    rows = []
    for name, product, kind in (("assessment", config.assessment, ResponseAssessment),
                                ("prediction", config.prediction, ResponsePredictions)):
        input_id = "external." + CAPABILITY + "." + name
        filename = "external-" + sha256(input_id.encode()).hexdigest()[:24] + ".json"
        record = decode_canonical_bytes(payloads[filename], kind, maximum_bytes=MAX_INPUT_BYTES)
        if record.fingerprint() != product.record.object_fingerprint:
            raise ValueError("current-use inquiry substitutes original evidence")
        rows.append(InquiryEvidenceBinding(input_id, record.fingerprint(), config.parent.scope, product.role, (), views))
    if products is not None:
        _, record, _, _ = actual_use(draft, products)
        if record is not None:
            rows.append(InquiryEvidenceBinding(CAPABILITY + ".product", record.fingerprint(), adoption_scope(config),
                ContributionRole.RETAINED_ANALYSIS_INPUT, (), views))
    return tuple(sorted(rows, key=lambda row: row.binding_id))
