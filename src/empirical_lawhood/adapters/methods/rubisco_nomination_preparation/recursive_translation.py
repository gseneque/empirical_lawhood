# SPDX-License-Identifier: MPL-2.0
"""A new human-directed inquiry consumes one authentic historic OUTCOME parent."""

from hashlib import sha256
from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry import (
    science as portfolio,
)
from empirical_lawhood.kernel.authority import (
    AuthorityAction,
    AuthorityPolicy,
    SourceAccessClass,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import (
    EvidenceCeiling,
    OutcomeAccess,
    VisibilityCeiling,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.recursive_requirements import (
    ConditionRole,
    ContributionRole,
    ScientificConnectionSpec,
    ScientificRequirementSpec,
)
from empirical_lawhood.kernel.scientific_contributions import (
    ContributionManifest,
    ContributionProduct,
)
from empirical_lawhood.kernel.status import LifecycleStatus, OperationalStatus
from empirical_lawhood.planning.campaigns import (
    CampaignLane,
    CampaignNode,
    CampaignNodeKind,
    CampaignSpec,
    DecisionRight,
)
from empirical_lawhood.planning.recursive_authoring import (
    RecursiveExternalInput,
    RecursiveInputLink,
    RecursiveOperationSpec,
    RecursiveStudyDraft,
)
from empirical_lawhood.runtime.recursive_inquiry import InquiryEvidenceBinding
from . import science
from .contracts import NominationOperationConfig, NominationDossier, identity, scope
from .operation_bindings import (
    BUDGET,
    CONDITION,
    FALSIFIER,
    MEDIA,
    NODE,
    PORTS,
    QUESTION,
    development_root,
    operation_declarations,
)


def preparation_draft(
    preparation,
    macro_source,
    cycle_outcome,
    *,
    parent,
    draft_id="draft.rubisco-nomination.prepare",
):
    science.validate_inputs(preparation, macro_source, cycle_outcome)
    matching = tuple(
        p
        for p in parent.products
        if p.record == identity(cycle_outcome)
        and p.role is ContributionRole.INSTANCE_PRODUCT
    )
    if len(matching) != 1 or parent.scope != cycle_outcome.scope:
        raise ValueError(
            "nomination parent substitutes original actual conditional outcome or scientific scope"
        )
    pp = matching[0]
    config = NominationOperationConfig(
        "config." + NODE,
        preparation,
        cycle_outcome.scope,
        tuple(
            sorted(
                (identity(r) for r in (preparation, macro_source, cycle_outcome)),
                key=lambda r: r.object_id,
            )
        ),
    )
    root = development_root(config, study_id="study." + draft_id)
    policy = AuthorityPolicy(
        "policy." + draft_id,
        "owner.local-researcher",
        "operator.local-development",
        (root.study_id,),
        frozenset((root.world_kind,)),
        frozenset(
            (
                AuthorityAction.REPOSITORY_IMPLEMENTATION,
                AuthorityAction.SIMULATION_EXECUTION,
            )
        ),
        frozenset((SourceAccessClass.NONE,)),
        ("gate.local-nonactuating-development",),
        frozenset(),
        BUDGET,
        OutcomeAccess.DEVELOPMENT_VISIBLE,
    )
    rn = "design." + draft_id
    campaign = CampaignSpec(
        "campaign." + draft_id,
        QUESTION,
        (root.system.object_id,),
        (root.world_id,),
        tuple(r.claim_id for r in root.claims),
        BUDGET,
        ObjectIdentity.from_record(policy.policy_id, policy),
        (
            DecisionRight(
                "decision-right." + draft_id,
                AuthorityAction.SIMULATION_EXECUTION,
                "owner.local-researcher",
                policy.policy_id,
                False,
            ),
        ),
        (
            CampaignNode(
                rn,
                CampaignNodeKind.EVIDENCE_SNAPSHOT,
                CampaignLane.EXPLORATORY,
                ObjectIdentity.from_record(root.study_id, root),
                (),
                LifecycleStatus.ACTIVE,
            ),
        ),
        (rn,),
        (rn,),
        (),
        LifecycleStatus.ACTIVE,
    )
    reg = operation_declarations()[0].registration()
    operation = RecursiveOperationSpec.from_config(
        node_id=NODE,
        selection=reg.selection,
        config_id=config.config_id,
        config=config,
        obligation_ids=(
            "obligation." + NODE + ".source-bound-exploratory-preparation",
        ),
        resource_budget=BUDGET,
    )
    requirement = ScientificRequirementSpec(
        "requirement." + NODE + ".prior-conditional-outcome",
        NODE,
        ConditionRole.EVIDENTIAL,
        QUESTION,
        CONDITION,
        cycle_outcome.scope,
        NODE,
        FALSIFIER,
        (ContributionRole.INSTANCE_PRODUCT,),
    )
    connection = ScientificConnectionSpec(
        "connection." + NODE + ".prior-conditional-outcome",
        requirement.requirement_id,
        None,
        None,
        "cycle-outcome",
        NODE,
        "claim." + NODE,
        ContributionRole.INSTANCE_PRODUCT,
        FALSIFIER,
        ObjectIdentity.from_record(parent.contribution_id, parent),
        pp.product_id,
        "external." + NODE + ".cycle-outcome",
    )
    inputs = (
        ("preparation", preparation),
        ("macro-source", macro_source),
        ("cycle-outcome", cycle_outcome),
    )
    external = []
    links = []
    for name, r in inputs:
        obj = identity(r)
        is_parent = name == "cycle-outcome"
        role = "OUTCOME" if is_parent else "SOURCE"
        eid = "external." + NODE + "." + name
        external.append(
            RecursiveExternalInput(
                eid,
                pp.artifact.artifact_id if is_parent else obj.object_id,
                obj.object_schema,
                MEDIA,
                None,
                OutcomeAccess.DEVELOPMENT_VISIBLE,
                VisibilityCeiling.DEVELOPMENT_ONLY,
                obj.object_fingerprint,
                role,
            )
        )
        links.append(
            RecursiveInputLink(
                "edge." + NODE + "." + name,
                NODE,
                name,
                external_input_id=eid,
                scientific_role=role,
                requirement_id=requirement.requirement_id if is_parent else None,
                connection_id=connection.connection_id if is_parent else None,
            )
        )
    return RecursiveStudyDraft(
        draft_id,
        QUESTION,
        campaign,
        (requirement,),
        (connection,),
        (),
        (operation,),
        tuple(sorted(external, key=lambda r: r.input_id)),
        tuple(sorted(links, key=lambda r: r.edge_id)),
        (NODE,),
        development_study=root,
        contribution_parents=(parent,),
    )


def _config(draft):
    if len(draft.operations) != 1 or draft.selected_operation_ids != (NODE,):
        raise ValueError("nomination substitutes singleton selected preparation")
    operation = draft.operations[0]
    config = decode_canonical_bytes(
        operation.config_payload.encode(), NominationOperationConfig, maximum_bytes=None
    )
    if (
        operation.selection != operation_declarations()[0].registration().selection
        or operation.node_id != NODE
        or operation.config_id != config.config_id
        or draft.development_study
        != development_root(config, study_id=draft.development_study.study_id)
    ):
        raise ValueError("nomination changes exact registration/config/root")
    return operation, config


def validate_requirement(record, requirement, connection):
    if (
        type(record) is not NominationDossier
        or requirement.requirement_id
        != "requirement." + NODE + ".prior-conditional-outcome"
        or requirement.consumer_operation_id != NODE
        or requirement.condition_role is not ConditionRole.EVIDENTIAL
        or requirement.scope != record.prior_model_scope
        or requirement.purpose != QUESTION
        or requirement.condition != CONDITION
        or requirement.assessment_operation_id != NODE
        or requirement.falsifier != FALSIFIER
        or requirement.permitted_roles != (ContributionRole.INSTANCE_PRODUCT,)
        or connection.connection_id
        != "connection." + NODE + ".prior-conditional-outcome"
        or connection.consumer_input_id != "cycle-outcome"
        or connection.assessment_operation_id != NODE
        or connection.claim_id != "claim." + NODE
        or connection.evidence_role is not ContributionRole.INSTANCE_PRODUCT
        or connection.falsifier != FALSIFIER
        or connection.requirement_id != requirement.requirement_id
        or connection.external_input_id != "external." + NODE + ".cycle-outcome"
    ):
        raise ValueError(
            "nomination changes exact admitted prior-outcome requirement/connection"
        )
    record.__post_init__()


def _actual_product(draft, products):
    operation, config = _config(draft)
    outputs = products["records"].get(NODE, {})
    if not outputs:
        return operation, config, None
    if (
        set(outputs) != {NODE + ".product"}
        or type(outputs[NODE + ".product"]) is not NominationDossier
    ):
        raise ValueError("nomination changes actual output census/type")
    record = outputs[NODE + ".product"]
    record.__post_init__()
    receipt = products["receipts"][NODE]
    matches = tuple(
        r
        for r in receipt.output_logical_artifacts
        if r.content_sha256 == record.fingerprint()
        and r.payload_schema == record.SCHEMA
    )
    if (
        receipt.operational_status is not OperationalStatus.SUCCEEDED
        or len(matches) != 1
        or record.preparation != config.preparation
    ):
        raise ValueError(
            "nomination product changes actual source/config or successful receipt"
        )
    return operation, config, record


def describe_contributions(draft, products):
    _, _, record = _actual_product(draft, products)
    if record is None:
        return ()
    receipt = products["receipts"][NODE]
    logical = next(
        r
        for r in receipt.output_logical_artifacts
        if r.content_sha256 == record.fingerprint()
    )
    artifact = products["outputs"][logical.logical_artifact_id]
    if artifact.logical != logical:
        raise ValueError("nomination contribution substitutes actual artifact")
    p = ContributionProduct(
        "product." + NODE + ".exploratory-dossier",
        identity(record),
        ArtifactIdentity(
            logical.logical_artifact_id,
            "scientific-product",
            record.SCHEMA,
            record.fingerprint(),
            MEDIA,
            artifact.materialization.size_bytes,
        ),
        ObjectIdentity.from_record(receipt.receipt_id, receipt),
        ContributionRole.INSTANCE_PRODUCT,
        EvidenceCeiling.NON_PROMOTABLE,
        logical.outcome_access,
        logical.visibility_ceiling,
    )
    return (
        ContributionManifest(
            "contribution." + draft.draft_id,
            QUESTION,
            "Exploratory test-nominee dossier; no assay/biological qualification/external submission.",
            record.scope,
            (p,),
            (identity(record),),
            (),
            tuple(
                ObjectIdentity.from_record(r.contribution_id, r)
                for r in draft.contribution_parents
            ),
        ),
    )


def next_wave_builder(draft, manifest, products):
    if describe_contributions(draft, products) != (manifest,):
        raise ValueError("nomination successor changes exact retained dossier")
    return None


def inquiry_endpoint_validator(draft, endpoint):
    _, config = _config(draft)
    if endpoint != scope(config.preparation):
        raise ValueError(
            "nomination inquiry changes exact exploratory preparation scope"
        )


def inquiry_outcome_projector(draft, specification, products):
    inquiry_endpoint_validator(draft, specification.endpoint)
    op, _, record = _actual_product(draft, products)
    if specification.distinguishing_assessment != op.config_identity:
        raise ValueError("nomination inquiry changes designated assessment")
    return "unresolved" if record is None else "useful-supply"


def inquiry_evidence_projector(draft, payloads, products=None):
    op, config = _config(draft)
    external = {r.input_id: r for r in draft.external_inputs}
    links = tuple(r for r in draft.links if r.consumer_node_id == NODE)
    if len(links) != 3 or {r.consumer_input_id for r in links} != {n for n, _ in PORTS}:
        raise ValueError("nomination evidence omits source/outcome operand")
    codecs = dict(PORTS)
    inputs = {}
    bindings = []
    for link in links:
        ext = external[link.external_input_id]
        r = decode_canonical_bytes(
            payloads[
                "external-" + sha256(ext.input_id.encode()).hexdigest()[:24] + ".json"
            ],
            codecs[link.consumer_input_id],
            maximum_bytes=None,
        )
        wanted = "OUTCOME" if link.consumer_input_id == "cycle-outcome" else "SOURCE"
        if (
            ext.scientific_role != wanted
            or ext.expected_content_sha256 != r.fingerprint()
        ):
            raise ValueError(
                "nomination evidence changes original source/outcome role or bytes"
            )
        inputs[link.consumer_input_id] = r
        original = (
            r.scope
            if wanted == "OUTCOME"
            else portfolio.original_source_scope(r)
            if link.consumer_input_id == "macro-source"
            else scope(r)
        )
        role = (
            ContributionRole.INSTANCE_PRODUCT
            if wanted == "OUTCOME"
            else ContributionRole.RETAINED_ANALYSIS_INPUT
        )
        bindings.append(
            InquiryEvidenceBinding(
                ext.input_id,
                r.fingerprint(),
                original,
                role,
                (),
                draft.development_study.numerical_view_ids,
            )
        )
    if (
        tuple(sorted((identity(r) for r in inputs.values()), key=lambda r: r.object_id))
        != config.operands
    ):
        raise ValueError("nomination evidence substitutes exact configured operands")
    science.validate_inputs(
        inputs["preparation"], inputs["macro-source"], inputs["cycle-outcome"]
    )
    if products is not None:
        _, _, actual = _actual_product(draft, products)
        if actual is not None:
            science.validate_dossier(
                actual, inputs["macro-source"], inputs["cycle-outcome"]
            )
            bindings.append(
                InquiryEvidenceBinding(
                    op.node_id + ".product",
                    actual.fingerprint(),
                    actual.scope,
                    ContributionRole.INSTANCE_PRODUCT,
                    (),
                    draft.development_study.numerical_view_ids,
                )
            )
    return tuple(sorted(bindings, key=lambda r: r.binding_id))
