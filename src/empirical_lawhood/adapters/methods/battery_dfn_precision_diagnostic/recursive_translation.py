# SPDX-License-Identifier: MPL-2.0
"""Native procedure, distinct instance use and receipt-backed subsequent reuse."""

from empirical_lawhood.kernel.authority import (
    AuthorityAction,
    AuthorityPolicy,
    SourceAccessClass,
)
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
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
from . import science
from .contracts import DiagnosticSource, DiagnosticResult, QUESTION
from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import (
    BatteryInquirySupply,
    scope,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from hashlib import sha256
from empirical_lawhood.kernel.recursive_requirements import (
    AssessmentDisposition,
    ContributionRole,
    ConditionRole,
    ScientificRequirementSpec,
    ScientificConnectionSpec,
)
from empirical_lawhood.runtime.recursive_inquiry import InquiryEvidenceBinding
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.scientific_contributions import (
    ContributionManifest,
    ContributionProduct,
)
from empirical_lawhood.kernel.evidence import EvidenceCeiling
from .operation_bindings import (
    BUDGET,
    MAX_BYTES,
    MEDIA,
    NAMESPACE,
    DiagnosticOperationConfig,
    development_root,
    operation_registrations,
)


CONDITION = "Exact authentic original1.1 procedure retains36 forecasts and9 unresolved DFN reference checks; current12 forecast/9 single-factor comparisons assess only independent numerical precision."
FALSIFIER = "Different prior bytes/source/census, changed settings/finite preparations, absent current native integrity, or failed unchanged1s/1mV/.01K comparisons defeat this numerical precision condition."


def requirement_pair(source, parent_identity, product_id):
    node = NAMESPACE + ".diagnose"
    requirement = ScientificRequirementSpec(
        "requirement." + node + ".negative-reference-context",
        node,
        ConditionRole.EVIDENTIAL,
        QUESTION,
        CONDITION,
        scope(source.original),
        node,
        FALSIFIER,
        (ContributionRole.DESIGN_OPERAND,),
    )
    connection = ScientificConnectionSpec(
        "connection." + node + ".negative-reference-context",
        requirement.requirement_id,
        None,
        None,
        "prior",
        node,
        "claim." + NAMESPACE,
        ContributionRole.DESIGN_OPERAND,
        FALSIFIER,
        parent_identity,
        product_id,
        "external." + node + ".prior",
    )
    return requirement, connection


def validate_requirement_config(config, requirement, connection):
    if (
        connection.supplier_contribution is None
        or connection.supplier_product_id is None
    ):
        raise ValueError("diagnostic requires exact portable original procedure parent")
    expected = requirement_pair(
        config.source, connection.supplier_contribution, connection.supplier_product_id
    )
    if (requirement, connection) != expected:
        raise ValueError(
            "diagnostic changes prior evidential condition or scientific connection"
        )


def diagnostic_draft(
    prior,
    source=None,
    *,
    parent=None,
    draft_id="draft.battery-dfn-precision-diagnostic",
):
    source = DiagnosticSource() if source is None else source
    science.validate_prior(source, prior)
    config = DiagnosticOperationConfig(
        "config." + NAMESPACE,
        source,
        tuple(
            sorted(
                (science.identity(source), science.identity(prior)),
                key=lambda x: x.object_id,
            )
        ),
    )
    return draft_from_config(config, parent=parent, draft_id=draft_id)


def draft_from_config(
    config, *, parent=None, draft_id="draft.battery-dfn-precision-diagnostic"
):
    """Author immutable operands; runtime still requires actual exact prior bytes."""
    config.__post_init__()
    if parent is None:
        raise ValueError(
            "diagnostic requires actual receipt-backed original procedure parent"
        )
    prior = next(
        x for x in config.operands if x.object_schema == BatteryInquirySupply.SCHEMA
    )
    matched = tuple(x for x in parent.products if x.record == prior)
    if (
        len(matched) != 1
        or parent.scope != scope(config.source.original)
        or matched[0].role is not ContributionRole.DESIGN_OPERAND
    ):
        raise ValueError("diagnostic parent changes exact original procedure product")
    requirement, connection = requirement_pair(
        config.source,
        ObjectIdentity.from_record(parent.contribution_id, parent),
        matched[0].product_id,
    )
    source = config.source
    root = development_root(config, study_id=f"study.{draft_id}")
    policy = AuthorityPolicy(
        f"policy.{draft_id}",
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
    root_id = f"design.{draft_id}"
    campaign = CampaignSpec(
        f"campaign.{draft_id}",
        QUESTION,
        (root.system.object_id,),
        (root.world_id,),
        tuple(row.claim_id for row in root.claims),
        BUDGET,
        ObjectIdentity.from_record(policy.policy_id, policy),
        (
            DecisionRight(
                f"decision-right.{draft_id}",
                AuthorityAction.SIMULATION_EXECUTION,
                "owner.local-researcher",
                policy.policy_id,
                False,
            ),
        ),
        (
            CampaignNode(
                root_id,
                CampaignNodeKind.EVIDENCE_SNAPSHOT,
                CampaignLane.EXPLORATORY,
                ObjectIdentity.from_record(root.study_id, root),
                (),
                LifecycleStatus.ACTIVE,
            ),
        ),
        (root_id,),
        (root_id,),
        (),
        LifecycleStatus.ACTIVE,
    )
    registration = next(
        row
        for row in operation_registrations()
        if row.selection.capability_key == f"{NAMESPACE}.diagnose"
    )
    node = f"{NAMESPACE}.diagnose"
    operation = RecursiveOperationSpec.from_config(
        node_id=node,
        selection=registration.selection,
        config_id=config.config_id,
        config=config,
        obligation_ids=(f"obligation.{node}.source-and-native-census",),
        resource_budget=BUDGET,
        resource_lock_ids=("battery-native-single-worker",),
    )
    external = []
    links = []
    for port, value in (
        ("source", science.identity(source)),
        (
            "prior",
            next(
                x for x in config.operands if x.object_schema != DiagnosticSource.SCHEMA
            ),
        ),
    ):
        input_id = f"external.{node}.{port}"
        graph_role = "MODEL" if port == "prior" else "SOURCE"
        logical_id = value.object_id
        if port == "prior" and parent is not None:
            matched = tuple(x for x in parent.products if x.record == value)
            if (
                len(matched) != 1
                or parent.scope != scope(source.original)
                or matched[0].role is not ContributionRole.DESIGN_OPERAND
            ):
                raise ValueError(
                    "diagnostic parent does not own exact actual prior outcome"
                )
            logical_id = matched[0].artifact.artifact_id
        external.append(
            RecursiveExternalInput(
                input_id,
                logical_id,
                value.object_schema,
                MEDIA,
                MAX_BYTES,
                OutcomeAccess.DEVELOPMENT_VISIBLE,
                VisibilityCeiling.DEVELOPMENT_ONLY,
                value.object_fingerprint,
                graph_role,
            )
        )
        links.append(
            RecursiveInputLink(
                f"edge.{node}.{port}",
                node,
                port,
                external_input_id=input_id,
                scientific_role=graph_role,
                requirement_id=requirement.requirement_id if port == "prior" else None,
                connection_id=connection.connection_id if port == "prior" else None,
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
        tuple(sorted(external, key=lambda x: x.input_id)),
        tuple(sorted(links, key=lambda x: x.edge_id)),
        (node,),
        development_study=root,
        contribution_parents=() if parent is None else (parent,),
    )


def _config(draft):
    if len(draft.operations) != 1 or draft.selected_operation_ids != (
        NAMESPACE + ".diagnose",
    ):
        raise ValueError("diagnostic changes singleton operation")
    operation = draft.operations[0]
    config = decode_canonical_bytes(
        operation.config_payload.encode(), DiagnosticOperationConfig, maximum_bytes=None
    )
    if (
        operation.selection != operation_registrations()[0].selection
        or operation.node_id != NAMESPACE + ".diagnose"
        or operation.config_id != config.config_id
        or draft.development_study
        != development_root(config, study_id=draft.development_study.study_id)
    ):
        raise ValueError("diagnostic changes registered implementation")
    return operation, config


def _actual_product(draft, products):
    operation, config = _config(draft)
    records = products.get("records", {}).get(operation.node_id, {})
    if not records:
        return operation, config, None
    record = records.get(operation.node_id + ".product")
    if type(record) is not DiagnosticResult or len(records) != 1:
        raise ValueError("diagnostic changes actual product denominator")
    receipt = products["receipts"][operation.node_id]
    if (
        receipt.operational_status is not OperationalStatus.SUCCEEDED
        or len(receipt.output_logical_artifacts) != 1
    ):
        raise ValueError("diagnostic requires successful complete producing receipt")
    if (
        sum(
            x.payload_schema == record.SCHEMA
            and x.content_sha256 == record.fingerprint()
            for x in receipt.output_logical_artifacts
        )
        != 1
    ):
        raise ValueError("diagnostic product differs from producing receipt")
    record.__post_init__()
    if record.source != config.source or record.prior_supply not in config.operands:
        raise ValueError("diagnostic actual product changes original context")
    return operation, config, record


def inquiry_endpoint_validator(draft, endpoint):
    _, config = _config(draft)
    if endpoint != scope(config.source.original):
        raise ValueError("diagnostic changes original numerical source scope")


def inquiry_outcome_projector(draft, specification, products):
    inquiry_endpoint_validator(draft, specification.endpoint)
    operation, _, record = _actual_product(draft, products)
    if specification.distinguishing_assessment != operation.config_identity:
        raise ValueError("diagnostic changes actual assessment")
    if record is None:
        return "unresolved"
    return (
        "useful-supply"
        if record.disposition is AssessmentDisposition.SATISFIED
        else "unresolved"
    )


def inquiry_evidence_projector(draft, payloads, products=None):
    operation, config = _config(draft)
    codecs = {"source": DiagnosticSource, "prior": BatteryInquirySupply}
    external = {x.input_id: x for x in draft.external_inputs}
    links = tuple(x for x in draft.links if x.consumer_node_id == operation.node_id)
    if len(links) != 2 or {x.consumer_input_id for x in links} != set(codecs):
        raise ValueError("diagnostic changes exposed evidence census")
    inputs = {}
    bindings = []
    for link in links:
        selected = external[link.external_input_id]
        record = decode_canonical_bytes(
            payloads[
                "external-"
                + sha256(selected.input_id.encode()).hexdigest()[:24]
                + ".json"
            ],
            codecs[link.consumer_input_id],
            maximum_bytes=None,
        )
        if (
            record.fingerprint() != selected.expected_content_sha256
            or selected.scientific_role
            != ("SOURCE" if link.consumer_input_id == "source" else "MODEL")
        ):
            raise ValueError("diagnostic evidence changes exact bytes/role")
        inputs[link.consumer_input_id] = record
        bindings.append(
            InquiryEvidenceBinding(
                selected.input_id,
                record.fingerprint(),
                scope(config.source.original),
                ContributionRole.DESIGN_OPERAND
                if link.consumer_input_id == "prior"
                else ContributionRole.RETAINED_ANALYSIS_INPUT,
                (),
                draft.development_study.numerical_view_ids,
            )
        )
    science.validate_prior(inputs["source"], inputs["prior"])
    if (
        tuple(
            sorted(
                (science.identity(x) for x in inputs.values()),
                key=lambda x: x.object_id,
            )
        )
        != config.operands
    ):
        raise ValueError("diagnostic evidence substitutes configured operands")
    if products is not None:
        _, _, record = _actual_product(draft, products)
        if record is not None:
            bindings.append(
                InquiryEvidenceBinding(
                    operation.node_id + ".product",
                    record.fingerprint(),
                    scope(config.source.original),
                    ContributionRole.RETAINED_ANALYSIS_INPUT,
                    (),
                    draft.development_study.numerical_view_ids,
                )
            )
    return tuple(sorted(bindings, key=lambda x: x.binding_id))


def describe_contributions(draft, products):
    operation, config, record = _actual_product(draft, products)
    if record is None:
        return ()
    receipt = products["receipts"][operation.node_id]
    logical = next(
        x
        for x in receipt.output_logical_artifacts
        if x.payload_schema == record.SCHEMA
        and x.content_sha256 == record.fingerprint()
    )
    artifact = products["outputs"][logical.logical_artifact_id]
    if artifact.logical != logical:
        raise ValueError("diagnostic changes authenticated output")
    product = ContributionProduct(
        "product." + operation.node_id + ".retained-analysis-input",
        science.identity(record),
        ArtifactIdentity(
            logical.logical_artifact_id,
            "scientific-product",
            record.SCHEMA,
            record.fingerprint(),
            artifact.logical.media_type,
            artifact.materialization.size_bytes,
        ),
        ObjectIdentity.from_record(receipt.receipt_id, receipt),
        ContributionRole.RETAINED_ANALYSIS_INPUT,
        EvidenceCeiling.NON_PROMOTABLE,
        artifact.logical.outcome_access,
        artifact.logical.visibility_ceiling,
    )
    return (
        ContributionManifest(
            "contribution." + draft.draft_id,
            QUESTION,
            "Actual finite precision diagnostic only; preserves unresolved historical supply and confers no supplier/physical qualification.",
            scope(config.source.original),
            (product,),
            tuple(
                sorted(
                    (
                        science.identity(x)
                        for x in (*record.checks, *record.comparisons)
                    ),
                    key=lambda x: x.object_id,
                )
            ),
            (),
            tuple(
                ObjectIdentity.from_record(x.contribution_id, x)
                for x in draft.contribution_parents
            ),
        ),
    )
