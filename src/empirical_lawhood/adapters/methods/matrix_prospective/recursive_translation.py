# SPDX-License-Identifier: MPL-2.0
"""Exact full selected wave; future tasks depend on published commitments."""
from empirical_lawhood.kernel.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import LifecycleStatus
from empirical_lawhood.planning.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft

from .operation_bindings import BUDGET, MEDIA, NAMESPACE, PHASES, MatrixOperationConfig, development_root, operation_registrations
from .records import identity
from .science import branch_contract


def prospective_draft(source, provenance, *, draft_id="draft.matrix-prospective.exposed"):
    root = development_root(source.protocol, study_id="study." + draft_id,
                            scientific_operands=(identity(source), provenance.identity))
    policy = AuthorityPolicy("policy." + draft_id, "owner.local-researcher", "operator.local-development",
        (root.study_id,), frozenset((root.world_kind,)),
        frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION, AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)), ("gate.local-nonactuating-development",), frozenset(), BUDGET,
        OutcomeAccess.DEVELOPMENT_VISIBLE)
    design = CampaignNode("design." + draft_id, CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id, root), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec("campaign." + draft_id, root.question, (root.system.object_id,), (root.world_id,),
        tuple(c.claim_id for c in root.claims), BUDGET, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight("right." + draft_id, AuthorityAction.SIMULATION_EXECUTION,
            "owner.local-researcher", policy.policy_id, False),), (design,), (design.node_id,), (design.node_id,), (), LifecycleStatus.ACTIVE)
    external = tuple(sorted((
        RecursiveExternalInput("external.matrix.provenance", provenance.identity.object_id, provenance.SCHEMA,
            MEDIA, None, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
            provenance.fingerprint(), "SOURCE"),
        RecursiveExternalInput("external.matrix.source", source.source_id, source.SCHEMA, MEDIA, None,
            OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, source.fingerprint(), "SOURCE"),
        *(RecursiveExternalInput("external.matrix." + b + "-stream",
            "stream." + source.protocol.root.root_id + "." + b,
            branch_contract(source, b).stream.SCHEMA, MEDIA, None, OutcomeAccess.DEVELOPMENT_VISIBLE,
            VisibilityCeiling.DEVELOPMENT_ONLY, branch_contract(source, b).stream.fingerprint(), "SOURCE")
          for b in ("future-1", "future-2")),
    ), key=lambda value: value.input_id))
    registrations = {r.selection.capability_key: r for r in operation_registrations()}
    operations, links = [], []
    for role, ports, _, _ in PHASES:
        node = f"{NAMESPACE}.{role}"
        config = MatrixOperationConfig("config." + node, role, source.protocol,
            None if role == "forecast" else identity(source),
            provenance.identity if role in {"origin", "futures"} else None)
        operations.append(RecursiveOperationSpec.from_config(node_id=node,
            selection=registrations[node].selection, config_id=config.config_id, config=config,
            obligation_ids=("obligation." + node + ".exact-causal-scope",), resource_budget=BUDGET))
        for port, _ in ports:
            if port in {"source", "provenance", "future-1-stream", "future-2-stream"}:
                links.append(RecursiveInputLink("edge." + node + "." + port, node, port,
                    external_input_id="external.matrix." + port, scientific_role="SOURCE"))
            else:
                owner = port.removesuffix("-arrays")
                links.append(RecursiveInputLink("edge." + node + "." + port, node, port,
                    producer_node_id=f"{NAMESPACE}.{owner}",
                    producer_output_id="arrays" if port.endswith("-arrays") else "product",
                    scientific_role="MODEL" if owner == "forecast" else "OUTCOME" if owner == "futures" else "HISTORY"))
    return RecursiveStudyDraft(draft_id, root.question, campaign, (), (), (),
        tuple(sorted(operations, key=lambda o: o.node_id)), external,
        tuple(sorted(links, key=lambda e: e.edge_id)), tuple(sorted(o.node_id for o in operations)),
        development_study=root)
