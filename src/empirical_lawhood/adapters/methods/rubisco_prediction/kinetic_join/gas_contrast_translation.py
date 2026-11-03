# SPDX-License-Identifier: MPL-2.0
"""Existing portable contributions and recursive authoring for gas contrasts."""

from empirical_lawhood.kernel.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry_policy import ScientificInquiryWork
from empirical_lawhood.kernel.recursive_requirements import ContributionRole
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.scientific_contributions import ContributionManifest, ContributionProduct
from empirical_lawhood.kernel.status import LifecycleStatus
from empirical_lawhood.planning.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.planning.recursive_input_origins import RecursiveInputOrigin, RecursiveInputOriginKind, RecursiveInputOrigins

from ..kinetic_assay_bridge import KineticAssayBridgeResult, KineticJointTargetAssessment
from .gas_contrast import BUDGET, CAPABILITY, MEDIA, GasContrastConfig, development_root, identity, operation_declaration, require_pair, scope


def describe_kinetic_contribution(draft, products):
    """Project actual W1 outputs/receipts; the shared exporter retains custody."""
    from .operation_bindings import KineticJoinConfig, NAMESPACE, scope as join_scope
    from .recursive_translation import scientific_work as join_work

    join_work(draft, NAMESPACE + ".assay")
    selected = next(row for row in draft.operations if row.node_id == NAMESPACE + ".assay")
    config = decode_canonical_bytes(selected.config_payload.encode(), KineticJoinConfig, maximum_bytes=None)
    entries, records = [], {}
    for phase, record_type, role in (("assay", KineticAssayBridgeResult, ContributionRole.INSTANCE_PRODUCT),
            ("assess", KineticJointTargetAssessment, ContributionRole.RETAINED_ANALYSIS_INPUT)):
        task_id = NAMESPACE + "." + phase
        retained = products["records"].get(task_id, {})
        matches = tuple(row for row in retained.values() if type(row) is record_type)
        if len(matches) != 1 or task_id not in products["receipts"]:
            raise ValueError("kinetic contribution requires both actual complete products and producing receipts")
        record = matches[0]
        receipt = products["receipts"][task_id]
        logicals = tuple(row for row in receipt.output_logical_artifacts
            if row.payload_schema == record.SCHEMA and row.content_sha256 == record.fingerprint())
        if len(logicals) != 1 or logicals[0].logical_artifact_id not in products["outputs"]:
            raise ValueError("kinetic contribution substitutes the exact producing receipt product")
        logical = logicals[0]
        artifact = products["outputs"][logical.logical_artifact_id]
        if artifact.logical != logical:
            raise ValueError("kinetic contribution changes actual retained artifact ownership")
        name = "result_id" if phase == "assay" else "assessment_id"
        records[phase] = record
        entries.append(ContributionProduct("product." + task_id, identity(record, name),
            ArtifactIdentity(logical.logical_artifact_id, "rubisco-conditional-" + phase, record.SCHEMA,
                record.fingerprint(), logical.media_type, artifact.materialization.size_bytes),
            identity(receipt, "receipt_id"), role, EvidenceCeiling.NON_PROMOTABLE,
            OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY))
    if (records["assess"].assay_bridge != records["assay"]
            or identity(records["assay"].supply, "supply_id") != config.science.supply):
        raise ValueError("kinetic contribution changes its independent assay/assessment/source join")
    assessed = records["assess"]
    manifest = ContributionManifest("contribution.rubisco-kinetic-join." + assessed.fingerprint()[:24],
        draft.question, "Complete conditional numerical products; joint target " + assessed.robust_conditional_target_disposition.value
            + "; biological predictive calibration NOT_ESTABLISHED.",
        join_scope(config.science), tuple(sorted(entries, key=lambda row: row.product_id)),
        (identity(assessed, "assessment_id"),), ())
    return (manifest,)


def _bridge_product(parent, bridge):
    if type(parent) is not ContributionManifest or type(bridge) is not KineticAssayBridgeResult:
        raise ValueError("gas contrast requires typed retained parents and actual bridge products")
    parent.__post_init__()
    bridge.__post_init__()
    products = tuple(row for row in parent.products if row.record == identity(bridge, "result_id")
        and row.role is ContributionRole.INSTANCE_PRODUCT)
    if (len(products) != 1 or parent.scope.system_id != bridge.supply.context.material.object_id
            or parent.scope.source_id != bridge.supply.supply_id):
        raise ValueError("gas contrast changes its parent product or supplied material scope")
    return products[0]


def gas_contrast_draft(left, right, left_parent, right_parent, *, draft_id="draft.rubisco.gas-contrast.v1"):
    """Select two authentic parent products; authoring authenticates their custody."""
    config = GasContrastConfig("config." + CAPABILITY, left.supply.context, identity(left.supply, "supply_id"),
        identity(left_parent, "contribution_id"), identity(right_parent, "contribution_id"),
        _bridge_product(left_parent, left), _bridge_product(right_parent, right),
        ObjectIdentity.from_record(CAPABILITY + ".left.query", left.query),
        ObjectIdentity.from_record(CAPABILITY + ".right.query", right.query), left.numerical_relative_tolerance)
    require_pair(config, left, right)
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
            "owner.local-researcher", policy.policy_id, False),), (node,), (node.node_id,), (node.node_id,), (), LifecycleStatus.ACTIVE)
    operation = RecursiveOperationSpec.from_config(node_id=CAPABILITY, selection=operation_declaration().registration().selection,
        config_id=config.config_id, config=config, obligation_ids=("obligation." + CAPABILITY + ".complete-paired-census",),
        resource_budget=BUDGET)
    external, links = [], []
    for side, product in (("left", config.left_product), ("right", config.right_product)):
        input_id = "external." + CAPABILITY + "." + side
        external.append(RecursiveExternalInput(input_id, product.artifact.artifact_id,
            product.record.object_schema, MEDIA, product.artifact.size_bytes, product.outcome_access,
            product.visibility_ceiling, product.record.object_fingerprint, "OUTCOME"))
        links.append(RecursiveInputLink("edge." + CAPABILITY + "." + side, CAPABILITY, side,
            external_input_id=input_id, scientific_role="OUTCOME"))
    return RecursiveStudyDraft(draft_id, root.question, campaign, (), (), (), (operation,),
        tuple(external), tuple(links), (CAPABILITY,), development_study=root,
        contribution_parents=tuple(sorted((left_parent, right_parent), key=lambda row: row.contribution_id)))


def gas_contrast_input_origins(draft):
    config = _selected_config(draft)
    origins = RecursiveInputOrigins(tuple(RecursiveInputOrigin("external." + CAPABILITY + "." + side,
        RecursiveInputOriginKind.CONTRIBUTION, product.record.object_fingerprint, product.role.value,
        parent, product.product_id, product.producing_receipt) for side, parent, product in
        (("left", config.left_parent, config.left_product), ("right", config.right_parent, config.right_product))))
    origins.validate_draft(draft)
    return origins


def _selected_config(draft):
    if (len(draft.operations) != 1 or draft.selected_operation_ids != (CAPABILITY,)
            or draft.operations[0].node_id != CAPABILITY or draft.development_study is None):
        raise ValueError("gas contrast requires its single complete selected operation")
    selected = draft.operations[0]
    config = decode_canonical_bytes(selected.config_payload.encode(), GasContrastConfig, maximum_bytes=None)
    if (selected.config_identity != identity(config, "config_id")
            or selected.selection != operation_declaration().registration().selection
            or selected.resource_budget != BUDGET
            or draft.development_study != development_root(config, study_id=draft.development_study.study_id)):
        raise ValueError("gas contrast changes its frozen configuration, capability or scientific root")
    if {identity(row, "contribution_id") for row in draft.contribution_parents} != {config.left_parent, config.right_parent}:
        raise ValueError("gas contrast substitutes its exact paired contribution parents")
    externals, links = [], []
    for side, product in (("left", config.left_product), ("right", config.right_product)):
        input_id = "external." + CAPABILITY + "." + side
        externals.append(RecursiveExternalInput(input_id, product.artifact.artifact_id,
            product.record.object_schema, MEDIA, product.artifact.size_bytes, product.outcome_access,
            product.visibility_ceiling, product.record.object_fingerprint, "OUTCOME"))
        links.append(RecursiveInputLink("edge." + CAPABILITY + "." + side, CAPABILITY, side,
            external_input_id=input_id, scientific_role="OUTCOME"))
    if draft.external_inputs != tuple(externals) or draft.links != tuple(links):
        raise ValueError("gas contrast substitutes its exact paired input ownership graph")
    return config


def scientific_work(draft, operation_id):
    config = _selected_config(draft)
    if operation_id != CAPABILITY:
        raise ValueError("gas contrast changes selected scientific work")
    sources = tuple(sorted((config.supply, config.left_parent, config.right_parent,
        config.left_query, config.right_query), key=lambda row: row.object_id))
    return ScientificInquiryWork(ObjectIdentity.from_record("method." + CAPABILITY, config), sources, scope(config),
        ObjectIdentity.from_record("observation." + CAPABILITY, config))
