# SPDX-License-Identifier: MPL-2.0
"""A new human-directed inquiry consumes one authentic historic negative MODEL parent."""

from hashlib import sha256
from dataclasses import replace
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
from .contracts import ObstructionOperationConfig, ObstructionAssessment, identity
from .operation_bindings import (
    BUDGET,
    CONDITION,
    FALSIFIER,
    MEDIA,
    NODE,
    PORTS,
    QUESTION,
    development_root,
    operation_registrations,
)


def obstruction_draft(
    source,
    prior,
    *,
    parent,
    draft_id="draft.battery-diagnostic-obstruction.assess",
):
    science.assess(source, prior)
    return obstruction_draft_from_parent(source, parent=parent, draft_id=draft_id)


def obstruction_draft_from_parent(
    source,
    *,
    parent,
    draft_id="draft.battery-diagnostic-obstruction.assess",
    config=None,
    registration=None,
    node_id=NODE,
):
    """Lower exact parent references without loading its large supplied record.

    This metadata projection establishes no publication or assessment. The
    shared author authenticates the complete parent custody; the existing
    worker reads and independently assesses the actual original prior supply.
    """
    science.validate_source(source)
    matching = tuple(
        p
        for p in parent.products
        if p.record == source.prior_supply and p.role is ContributionRole.DESIGN_OPERAND
    )
    if len(matching) != 1 or parent.scope != science.scope(source):
        raise ValueError(
            "prior parent substitutes original actual conditional outcome or scientific scope"
        )
    pp = matching[0]
    config = ObstructionOperationConfig("config." + NODE, source) if config is None else config
    reg = operation_registrations()[0] if registration is None else registration
    if type(config) is not reg.config_record_type or config.source != source:
        raise ValueError("obstruction lowering changes its exact declared config or original scientific source")
    root = obstruction_development_root(config, study_id="study." + draft_id, node_id=node_id)
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
    operation = RecursiveOperationSpec.from_config(
        node_id=node_id,
        selection=reg.selection,
        config_id=config.config_id,
        config=config,
        obligation_ids=("obligation." + node_id + ".source-bound-exploratory-source",),
        resource_budget=BUDGET,
    )
    requirement = ScientificRequirementSpec(
        "requirement." + node_id + ".prior-conditional-outcome",
        node_id,
        ConditionRole.EVIDENTIAL,
        QUESTION,
        CONDITION,
        science.scope(source),
        node_id,
        FALSIFIER,
        (ContributionRole.DESIGN_OPERAND,),
    )
    connection = ScientificConnectionSpec(
        "connection." + node_id + ".prior-conditional-outcome",
        requirement.requirement_id,
        None,
        None,
        "prior",
        node_id,
        "claim." + node_id,
        ContributionRole.DESIGN_OPERAND,
        FALSIFIER,
        ObjectIdentity.from_record(parent.contribution_id, parent),
        pp.product_id,
        "external." + node_id + ".prior",
    )
    inputs = (
        ("obstruction-source", identity(source)),
        ("prior", source.prior_supply),
    )
    external = []
    links = []
    for name, obj in inputs:
        is_parent = name == "prior"
        role = "MODEL" if is_parent else "SOURCE"
        eid = "external." + node_id + "." + name
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
                "edge." + node_id + "." + name,
                node_id,
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
        (node_id,),
        development_study=root,
        contribution_parents=(parent,),
    )


def obstruction_development_root(config, *, study_id, node_id=NODE):
    """One scientific projection, retaining the selected operation's claim ID."""
    root = development_root(config, study_id=study_id)
    if node_id == NODE:
        return root
    return replace(root, claims=(replace(root.claims[0], claim_id="claim." + node_id),))


def _config(draft, *, node_id=NODE, config_type=ObstructionOperationConfig, registration=None):
    if len(draft.operations) != 1 or draft.selected_operation_ids != (node_id,):
        raise ValueError("prior substitutes singleton selected source")
    operation = draft.operations[0]
    config = decode_canonical_bytes(
        operation.config_payload.encode(),
        config_type,
        maximum_bytes=None,
    )
    if (
        operation.selection != (operation_registrations()[0] if registration is None else registration).selection
        or operation.node_id != node_id
        or operation.config_id != config.config_id
        or draft.development_study
        != obstruction_development_root(config, study_id=draft.development_study.study_id, node_id=node_id)
    ):
        raise ValueError("prior changes exact registration/config/root")
    return operation, config


def validate_requirement(record, requirement, connection, *, node_id=NODE):
    if (
        type(record) is not ObstructionAssessment
        or requirement.requirement_id
        != "requirement." + node_id + ".prior-conditional-outcome"
        or requirement.consumer_operation_id != node_id
        or requirement.condition_role is not ConditionRole.EVIDENTIAL
        or requirement.scope
        != science.original_scope(record.source.diagnostic_source.original)
        or requirement.purpose != QUESTION
        or requirement.condition != CONDITION
        or requirement.assessment_operation_id != node_id
        or requirement.falsifier != FALSIFIER
        or requirement.permitted_roles != (ContributionRole.DESIGN_OPERAND,)
        or connection.connection_id
        != "connection." + node_id + ".prior-conditional-outcome"
        or connection.consumer_input_id != "prior"
        or connection.assessment_operation_id != node_id
        or connection.claim_id != "claim." + node_id
        or connection.evidence_role is not ContributionRole.DESIGN_OPERAND
        or connection.falsifier != FALSIFIER
        or connection.requirement_id != requirement.requirement_id
        or connection.external_input_id != "external." + node_id + ".prior"
    ):
        raise ValueError(
            "prior changes exact admitted prior-outcome requirement/connection"
        )
    record.__post_init__()


def _actual_product(draft, products, *, node_id=NODE, config_type=ObstructionOperationConfig, registration=None):
    operation, config = _config(draft, node_id=node_id, config_type=config_type, registration=registration)
    outputs = products["records"].get(node_id, {})
    if not outputs:
        return operation, config, None
    if (
        set(outputs) != {node_id + ".product"}
        or type(outputs[node_id + ".product"]) is not ObstructionAssessment
    ):
        raise ValueError("prior changes actual output census/type")
    record = outputs[node_id + ".product"]
    science.validate_assessment(record)
    receipt = products["receipts"][node_id]
    matches = tuple(
        r
        for r in receipt.output_logical_artifacts
        if r.content_sha256 == record.fingerprint()
        and r.payload_schema == record.SCHEMA
    )
    if (
        receipt.operational_status is not OperationalStatus.SUCCEEDED
        or len(matches) != 1
        or receipt.task_id != node_id
        or len(receipt.output_logical_artifacts) != 1
        or len(receipt.output_materializations) != 1
        or science.original_scope(record.source.diagnostic_source.original)
        != science.original_scope(config.source.diagnostic_source.original)
        or record.source != config.source
    ):
        raise ValueError(
            "prior product changes actual source/config or successful receipt"
        )
    return operation, config, record


def describe_contributions(draft, products, *, node_id=NODE, config_type=ObstructionOperationConfig, registration=None):
    _, _, record = _actual_product(draft, products, node_id=node_id, config_type=config_type, registration=registration)
    if record is None:
        return ()
    receipt = products["receipts"][node_id]
    logical = next(
        r
        for r in receipt.output_logical_artifacts
        if r.content_sha256 == record.fingerprint()
    )
    artifact = products["outputs"][logical.logical_artifact_id]
    if (
        artifact.logical != logical
        or artifact.materialization not in receipt.output_materializations
        or logical.logical_artifact_id
        != "artifact." + receipt.run_id + "." + node_id + ".product"
        or artifact.materialization.physical_sha256 != record.fingerprint()
        or artifact.materialization.size_bytes != len(record.canonical_bytes())
    ):
        raise ValueError("prior contribution substitutes actual artifact")
    p = ContributionProduct(
        "product." + node_id + ".adverse-history",
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
        ContributionRole.RETAINED_ANALYSIS_INPUT,
        EvidenceCeiling.NON_PROMOTABLE,
        logical.outcome_access,
        logical.visibility_ceiling,
    )
    return (
        ContributionManifest(
            "contribution." + draft.draft_id,
            QUESTION,
            "Retained operational unknown-completion history; no diagnostic result or numerical adequacy.",
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
        raise ValueError("prior successor changes exact retained dossier")
    return None


def inquiry_endpoint_validator(draft, endpoint, **projection):
    _, config = _config(draft, **projection)
    if endpoint != science.scope(config.source):
        raise ValueError("prior inquiry changes exact original scientific source scope")


def inquiry_outcome_projector(draft, specification, products, **projection):
    inquiry_endpoint_validator(draft, specification.endpoint, **projection)
    op, _, record = _actual_product(draft, products, **projection)
    if specification.distinguishing_assessment != op.config_identity:
        raise ValueError("prior inquiry changes designated assessment")
    return "unresolved" if record is None else "useful-supply"


def inquiry_evidence_projector(draft, payloads, products=None, **projection):
    op, config = _config(draft, **projection)
    external = {r.input_id: r for r in draft.external_inputs}
    links = tuple(r for r in draft.links if r.consumer_node_id == op.node_id)
    if len(links) != 2 or {r.consumer_input_id for r in links} != {n for n, _ in PORTS}:
        raise ValueError("prior evidence omits source/outcome operand")
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
        wanted = "MODEL" if link.consumer_input_id == "prior" else "SOURCE"
        if (
            ext.scientific_role != wanted
            or ext.expected_content_sha256 != r.fingerprint()
        ):
            raise ValueError(
                "prior evidence changes original source/outcome role or bytes"
            )
        inputs[link.consumer_input_id] = r
        original = r.scope if wanted == "MODEL" else science.scope(r)
        role = (
            ContributionRole.DESIGN_OPERAND
            if wanted == "MODEL"
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
        raise ValueError("prior evidence substitutes exact configured operands")
    science.assess(inputs["obstruction-source"], inputs["prior"])
    if products is not None:
        _, _, actual = _actual_product(draft, products, **projection)
        if actual is not None:
            if actual != science.assess(inputs["obstruction-source"], inputs["prior"]):
                raise ValueError(
                    "obstruction assessment differs from exact original history and negative MODEL"
                )
            bindings.append(
                InquiryEvidenceBinding(
                    op.node_id + ".product",
                    actual.fingerprint(),
                    actual.scope,
                    ContributionRole.RETAINED_ANALYSIS_INPUT,
                    (),
                    draft.development_study.numerical_view_ids,
                )
            )
    return tuple(sorted(bindings, key=lambda r: r.binding_id))
