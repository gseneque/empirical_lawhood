# SPDX-License-Identifier: MPL-2.0
"""Full24-model preparation consumes authentic nomination OUTCOME and structure HISTORY."""

from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace

from empirical_lawhood.adapters.methods.rubisco_nomination_preparation.contracts import (
    NominationDossier,
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
from empirical_lawhood.kernel.recursive_requirements import (
    AssessmentDisposition,
    ConditionRole,
    ContributionRole,
    ScientificConnectionSpec,
    ScientificRequirementSpec,
)
from empirical_lawhood.kernel.references import ArtifactIdentity
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
from . import contracts as c
from empirical_lawhood.adapters.methods.rubisco_insilico_structure import (
    contracts as sc,
)
from .operation_bindings import (
    BUDGET,
    MEDIA,
    development_root,
    operation_outputs,
    operation_registrations,
)

PREPARE = c.NAMESPACE + ".prepare"
ASSESS = c.NAMESPACE + ".assess-preparation"
CONDITION = "Exact authentic Gp I95M nomination and independently authenticated observed assemblies support the selected controlled complete24-model preparation and assigned-parameter assessment; no dynamics or kinetic qualification."
FALSIFIER = "A changed nomination, original coordinate or sequence digest, assembly operator, atom/residue denominator, processing view or role defeats correspondence. Missing coordinates and inhibited chemical states cannot be interpreted as a demonstrated mutant or catalytic result."


def requirement_pair(nomination_scope, parent_identity, product_id):
    requirement = ScientificRequirementSpec(
        "requirement." + PREPARE + ".nomination",
        PREPARE,
        ConditionRole.EVIDENTIAL,
        c.QUESTION,
        CONDITION,
        nomination_scope,
        ASSESS,
        FALSIFIER,
        (ContributionRole.INSTANCE_PRODUCT,),
    )
    connection = ScientificConnectionSpec(
        "connection." + PREPARE + ".nomination",
        requirement.requirement_id,
        None,
        None,
        "nomination",
        ASSESS,
        "claim." + c.NAMESPACE + ".preparation",
        ContributionRole.INSTANCE_PRODUCT,
        FALSIFIER,
        parent_identity,
        product_id,
        "external." + PREPARE + ".nomination",
    )
    return requirement, connection


def _validate_requirement(scope, requirement, connection):
    if (
        connection.supplier_contribution is None
        or connection.supplier_product_id is None
    ):
        raise ValueError(
            "model preparation requires the actual nomination contribution"
        )
    if (requirement, connection) != requirement_pair(
        scope, connection.supplier_contribution, connection.supplier_product_id
    ):
        raise ValueError(
            "model preparation changes exact prior scope, condition, role or connection"
        )


def validate_requirement_config(config, requirement, connection):
    config.__post_init__()
    _validate_requirement(config.prior_nomination_scope, requirement, connection)


def validate_requirement_assessment(record, requirement, connection):
    if type(record) is not c.PreparationAssessment:
        raise ValueError(
            "model preparation assessment requires its actual canonical product"
        )
    record.__post_init__()
    _validate_requirement(record.prior_nomination_scope, requirement, connection)


def _campaign(root, draft_id):
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
    node = "design." + draft_id
    return CampaignSpec(
        "campaign." + draft_id,
        c.QUESTION,
        (root.system.object_id,),
        (root.world_id,),
        tuple(row.claim_id for row in root.claims),
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
                node,
                CampaignNodeKind.EVIDENCE_SNAPSHOT,
                CampaignLane.EXPLORATORY,
                ObjectIdentity.from_record(root.study_id, root),
                (),
                LifecycleStatus.ACTIVE,
            ),
        ),
        (node,),
        (node,),
        (),
        LifecycleStatus.ACTIVE,
    )


def _parent_products(source, nomination_scope, parents):
    if len(parents) != 2 or len({p.contribution_id for p in parents}) != 2:
        raise ValueError(
            "preparation requires two exact distinct authenticated parents"
        )
    result = {}
    assigned = {}
    for name, identity, role in (
        ("nomination", source.nomination, ContributionRole.INSTANCE_PRODUCT),
        (
            "inventory",
            source.structural_inventory,
            ContributionRole.RETAINED_ANALYSIS_INPUT,
        ),
        (
            "coordinates",
            source.structural_coordinates,
            ContributionRole.RETAINED_ANALYSIS_INPUT,
        ),
    ):
        matches = [
            (p, r)
            for p in parents
            for r in p.products
            if r.record == identity and r.role is role
        ]
        if len(matches) != 1:
            raise ValueError("preparation changes exact parent product identity/role")
        parent, product = matches[0]
        result[name] = product
        assigned[name] = parent
    structural = assigned["inventory"]
    if (
        assigned["nomination"] == structural
        or assigned["coordinates"] != structural
        or assigned["nomination"].scope != nomination_scope
    ):
        raise ValueError(
            "preparation changes exact separate nomination and structure custody"
        )
    expected = sc.scope(
        SimpleNamespace(
            input_id=source.structural_inventory.object_id,
            fingerprint=lambda: source.structural_inventory.object_fingerprint,
        )
    )
    # Inventory identity differs from its original source; its manifest scope
    # binds the source identity, which is checked against actual inventory below.
    if (
        structural.scope.world_id != expected.world_id
        or structural.scope.system_id != expected.system_id
    ):
        raise ValueError("preparation changes original structure world/system scope")
    return result, assigned


def preparation_draft(
    source,
    dossier,
    inventory,
    coordinates,
    *,
    nomination_parent,
    structure_parent,
    draft_id="draft.rubisco-insilico-dynamics.preparation",
):
    from . import science

    science.validate_source(source, dossier, inventory, coordinates)
    parents = tuple(
        sorted((nomination_parent, structure_parent), key=lambda r: r.contribution_id)
    )
    if len({r.contribution_id for r in parents}) != 2:
        raise ValueError(
            "preparation requires two distinct authenticated original parents"
        )
    for parent in parents:
        parent.__post_init__()
    chosen = {}
    for name, record, parent, role in (
        ("nomination", dossier, nomination_parent, ContributionRole.INSTANCE_PRODUCT),
        (
            "inventory",
            inventory,
            structure_parent,
            ContributionRole.RETAINED_ANALYSIS_INPUT,
        ),
        (
            "coordinates",
            coordinates,
            structure_parent,
            ContributionRole.RETAINED_ANALYSIS_INPUT,
        ),
    ):
        matches = [
            r
            for r in parent.products
            if r.record == c.identity(record) and r.role is role
        ]
        if len(matches) != 1:
            raise ValueError("preparation changes actual parent product identity/role")
        chosen[name] = matches[0]
    if nomination_parent.scope != dossier.scope:
        raise ValueError("preparation changes original nomination scope")
    expected_scope = sc.scope(
        SimpleNamespace(
            input_id=inventory.source.object_id,
            fingerprint=lambda: inventory.source.object_fingerprint,
        )
    )
    if structure_parent.scope != expected_scope:
        raise ValueError("preparation changes exact original structure manifest scope")
    requirement, connection = requirement_pair(
        dossier.scope,
        ObjectIdentity.from_record(
            nomination_parent.contribution_id, nomination_parent
        ),
        chosen["nomination"].product_id,
    )
    base = c.PreparationOperationConfig(
        "config." + PREPARE,
        "prepare",
        source,
        dossier.scope,
        tuple(
            sorted(
                (
                    c.identity(source),
                    c.identity(dossier),
                    c.identity(inventory),
                    c.identity(coordinates),
                ),
                key=lambda r: r.object_id,
            )
        ),
    )
    registrations = {r.selection.capability_key: r for r in operation_registrations()}
    operations, external, links = [], [], []
    for operation in ("assess-preparation", "prepare"):
        node = c.NAMESPACE + "." + operation
        config = replace(base, config_id="config." + node, operation=operation)
        operations.append(
            RecursiveOperationSpec.from_config(
                node_id=node,
                selection=registrations[node].selection,
                config_id=config.config_id,
                config=config,
                obligation_ids=(
                    "obligation." + node + ".exact-complete-model-preparation",
                ),
                resource_budget=BUDGET,
            )
        )
        for name, record in (
            ("coordinates", coordinates),
            ("inventory", inventory),
            ("nomination", dossier),
            ("source", source),
        ):
            ident = c.identity(record)
            input_id = "external." + node + "." + name
            role = (
                "SOURCE"
                if name == "source"
                else "OUTCOME"
                if name == "nomination"
                else "HISTORY"
            )
            external.append(
                RecursiveExternalInput(
                    input_id,
                    ident.object_id
                    if name == "source"
                    else chosen[name].artifact.artifact_id,
                    ident.object_schema,
                    MEDIA,
                    None,
                    OutcomeAccess.DEVELOPMENT_VISIBLE,
                    VisibilityCeiling.DEVELOPMENT_ONLY,
                    ident.object_fingerprint,
                    role,
                )
            )
            connected = name == "nomination" and node == PREPARE
            links.append(
                RecursiveInputLink(
                    "edge." + node + "." + name,
                    node,
                    name,
                    external_input_id=input_id,
                    scientific_role=role,
                    requirement_id=requirement.requirement_id if connected else None,
                    connection_id=connection.connection_id if connected else None,
                )
            )
        if operation == "assess-preparation":
            for name, _ in operation_outputs("prepare"):
                links.append(
                    RecursiveInputLink(
                        "edge." + node + "." + name,
                        node,
                        name,
                        producer_node_id=PREPARE,
                        producer_output_id=name,
                        scientific_role="HISTORY",
                    )
                )
    root = development_root(base, study_id="study." + draft_id)
    return RecursiveStudyDraft(
        draft_id,
        c.QUESTION,
        _campaign(root, draft_id),
        (requirement,),
        (connection,),
        (),
        tuple(sorted(operations, key=lambda r: r.node_id)),
        tuple(sorted(external, key=lambda r: r.input_id)),
        tuple(sorted(links, key=lambda r: r.edge_id)),
        (ASSESS, PREPARE),
        development_study=root,
        contribution_parents=parents,
    )


def _configs(draft):
    draft.__post_init__()
    if tuple(row.node_id for row in draft.operations) != (
        ASSESS,
        PREPARE,
    ) or draft.selected_operation_ids != (ASSESS, PREPARE):
        raise ValueError("model preparation changes the exact two-operation census")
    registrations = {
        row.selection.capability_key: row for row in operation_registrations()
    }
    values = {}
    for row in draft.operations:
        config = decode_canonical_bytes(
            row.config_payload.encode(),
            c.PreparationOperationConfig,
            maximum_bytes=None,
        )
        if (
            row.config_id != config.config_id
            or row.node_id != c.NAMESPACE + "." + config.operation
            or row.selection != registrations[row.node_id].selection
        ):
            raise ValueError(
                "model preparation changes installed operation/config identities"
            )
        values[row.node_id] = config
    base = values[PREPARE]
    if (
        replace(base, operation="assess-preparation", config_id="config." + ASSESS)
        != values[ASSESS]
        or draft.development_study
        != development_root(base, study_id=draft.development_study.study_id)
        or len(draft.requirements) != 1
        or len(draft.connections) != 1
    ):
        raise ValueError(
            "model preparation changes source, actual outcome scope or common root"
        )
    validate_requirement_config(base, draft.requirements[0], draft.connections[0])
    chosen, parents = _parent_products(
        base.source, base.prior_nomination_scope, draft.contribution_parents
    )
    if (
        draft.connections[0].supplier_contribution
        != ObjectIdentity.from_record(
            parents["nomination"].contribution_id, parents["nomination"]
        )
        or draft.connections[0].supplier_product_id != chosen["nomination"].product_id
    ):
        raise ValueError("preparation requirement substitutes actual nomination parent")
    expected_external = {}
    for node in values:
        for name in ("source", "nomination", "inventory", "coordinates"):
            ident = (
                c.identity(base.source)
                if name == "source"
                else getattr(
                    base.source,
                    "structural_" + name
                    if name in ("inventory", "coordinates")
                    else name,
                )
            )
            expected_external["external." + node + "." + name] = (
                ident.object_id
                if name == "source"
                else chosen[name].artifact.artifact_id,
                ident.object_schema,
                ident.object_fingerprint,
                "SOURCE"
                if name == "source"
                else "OUTCOME"
                if name == "nomination"
                else "HISTORY",
            )
    if (
        len(draft.external_inputs) != len(expected_external)
        or {r.input_id for r in draft.external_inputs} != set(expected_external)
        or any(
            (
                r.logical_artifact_id,
                r.payload_schema,
                r.expected_content_sha256,
                r.scientific_role,
            )
            != expected_external[r.input_id]
            for r in draft.external_inputs
        )
    ):
        raise ValueError("preparation changes full exact external parent/input roster")
    return values, base


def _retained_outputs(node, config, products, *, output_contracts=None):
    """Join every parsed output to its complete successful producing receipt."""
    records = products.get("records", {}).get(node, {})
    if not records:
        return None
    outputs = (
        operation_outputs(config.operation)
        if output_contracts is None
        else output_contracts
    )
    expected = {node + "." + name: record for name, record in outputs}
    receipt = products.get("receipts", {}).get(node)
    if (
        records.keys() != expected.keys()
        or receipt is None
        or receipt.task_id != node
        or receipt.operational_status is not OperationalStatus.SUCCEEDED
        or len(receipt.output_logical_artifacts) != len(expected)
    ):
        raise ValueError(
            "preparation output census differs from its complete successful producing receipt"
        )
    logical_ids, materialization_ids = set(), set()
    expected_materialization_ids = {
        row.materialization_id for row in receipt.output_materializations
    }
    receipt_materializations = {
        row.materialization_id: row for row in receipt.output_materializations
    }
    for output_id, record_type in expected.items():
        record = records[output_id]
        if type(record) is not record_type:
            raise ValueError(
                "preparation actual output substitutes its declared typed record"
            )
        record.__post_init__()
        matching = tuple(
            row
            for row in receipt.output_logical_artifacts
            if row.payload_schema == record.SCHEMA
            and row.content_sha256 == record.fingerprint()
        )
        if len(matching) != 1:
            raise ValueError(
                "preparation record differs from actual producing receipt bytes"
            )
        logical = matching[0]
        if (
            logical.logical_artifact_id
            != "artifact." + receipt.run_id + "." + output_id
        ):
            raise ValueError(
                "preparation output substitutes its declared output ordinal or logical identity"
            )
        artifact = products.get("outputs", {}).get(logical.logical_artifact_id)
        if (
            artifact is None
            or artifact.logical != logical
            or artifact.materialization.materialization_id
            not in expected_materialization_ids
            or artifact.materialization
            != receipt_materializations[artifact.materialization.materialization_id]
            or artifact.materialization.physical_sha256 != record.fingerprint()
            or artifact.materialization.size_bytes != len(record.canonical_bytes())
            or logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
        ):
            raise ValueError(
                "preparation output loses exact authenticated materialization, custody or access"
            )
        logical_ids.add(logical.logical_artifact_id)
        materialization_ids.add(artifact.materialization.materialization_id)
    if (
        len(logical_ids) != len(expected)
        or materialization_ids != expected_materialization_ids
    ):
        raise ValueError(
            "preparation output hides or duplicates retained materialization census"
        )
    return records


def _actual_outputs(draft, products):
    configs, config = _configs(draft)
    retained = {
        node: _retained_outputs(node, selected, products)
        for node, selected in configs.items()
    }
    if retained[ASSESS] is not None:
        if retained[PREPARE] is None:
            raise ValueError(
                "preparation assessment omits complete actual native product/assets"
            )
        if not {
            r.materialization_id
            for r in products["receipts"][PREPARE].output_materializations
        }.issubset(products["receipts"][ASSESS].input_materialization_ids):
            raise ValueError(
                "preparation assessor lacks complete actual native output dependency materializations"
            )
        preparation = retained[PREPARE][PREPARE + ".preparation"]
        assets = tuple(
            retained[PREPARE][PREPARE + f".assets-{i:02d}"]
            for i in range(len(c.model_roster()))
        )
        assessment = retained[ASSESS][ASSESS + ".assessment"]
        if (
            preparation.source != c.identity(config.source)
            or preparation.nomination != config.source.nomination
            or preparation.structural_inventory != config.source.structural_inventory
            or preparation.structural_coordinates
            != config.source.structural_coordinates
            or tuple(c.identity(a) for a in assets)
            != tuple(m.assets for m in preparation.models)
            or assessment.preparation != c.identity(preparation)
            or assessment.source != c.identity(config.source)
            or assessment.nomination != config.source.nomination
            or assessment.structural_inventory != config.source.structural_inventory
            or assessment.prior_nomination_scope != config.prior_nomination_scope
        ):
            raise ValueError(
                "preparation assessment changes actual source/assets/parent joins"
            )
        validate_requirement_assessment(
            assessment, draft.requirements[0], draft.connections[0]
        )
    return config, retained


def inquiry_endpoint_validator(draft, endpoint):
    _, config = _configs(draft)
    if endpoint != c.scope(config.source):
        raise ValueError(
            "model preparation inquiry changes its exact source/mapping scope"
        )


def inquiry_outcome_projector(draft, specification, products):
    inquiry_endpoint_validator(draft, specification.endpoint)
    config, retained = _actual_outputs(draft, products)
    if specification.distinguishing_assessment != draft.operations[0].config_identity:
        raise ValueError(
            "model preparation inquiry changes its committed graph designation"
        )
    if retained[ASSESS] is None:
        return "unresolved"
    result = retained[ASSESS][ASSESS + ".assessment"]
    return (
        "useful-supply"
        if result.preparation_disposition is AssessmentDisposition.SATISFIED
        else "unresolved"
    )


def inquiry_evidence_projector(draft, payloads, products=None):
    from . import science

    configs, config = _configs(draft)
    external = {r.input_id: r for r in draft.external_inputs}
    bindings = []
    actual = {}
    codecs = {
        "source": c.PreparationSelection,
        "nomination": NominationDossier,
        "inventory": sc.StructuralInventory,
        "coordinates": sc.AssemblyCoordinates,
    }
    expected = {
        "source": c.identity(config.source),
        "nomination": config.source.nomination,
        "inventory": config.source.structural_inventory,
        "coordinates": config.source.structural_coordinates,
    }
    for node in configs:
        for name, codec in codecs.items():
            input_id = "external." + node + "." + name
            item = external[input_id]
            record = decode_canonical_bytes(
                payloads[
                    "external-" + sha256(input_id.encode()).hexdigest()[:24] + ".json"
                ],
                codec,
                maximum_bytes=None,
            )
            role = (
                "SOURCE"
                if name == "source"
                else "OUTCOME"
                if name == "nomination"
                else "HISTORY"
            )
            if (
                c.identity(record) != expected[name]
                or record.fingerprint() != item.expected_content_sha256
                or item.scientific_role != role
                or (name in actual and actual[name] != record)
            ):
                raise ValueError("preparation changes actual input identity/role/bytes")
            actual[name] = record
            scope = (
                c.scope(config.source)
                if name == "source"
                else record.scope
                if name == "nomination"
                else next(
                    p.scope
                    for p in draft.contribution_parents
                    if any(r.record == c.identity(record) for r in p.products)
                )
            )
            bindings.append(
                InquiryEvidenceBinding(
                    input_id,
                    record.fingerprint(),
                    scope,
                    ContributionRole.INSTANCE_PRODUCT
                    if name == "nomination"
                    else ContributionRole.RETAINED_ANALYSIS_INPUT,
                    (),
                    draft.development_study.numerical_view_ids,
                )
            )
    science.validate_source(
        *(actual[name] for name in ("source", "nomination", "inventory", "coordinates"))
    )
    _, parents = _parent_products(
        config.source, config.prior_nomination_scope, draft.contribution_parents
    )
    if parents["inventory"].scope != sc.scope(
        SimpleNamespace(
            input_id=actual["inventory"].source.object_id,
            fingerprint=lambda: actual["inventory"].source.object_fingerprint,
        )
    ):
        raise ValueError("preparation substitutes exact original structure scope")
    if products is not None:
        _, retained = _actual_outputs(draft, products)
        if retained[ASSESS] is not None:
            prepared = retained[PREPARE][PREPARE + ".preparation"]
            assets = tuple(
                retained[PREPARE][PREPARE + f".assets-{i:02d}"]
                for i in range(len(c.model_roster()))
            )
            if (
                science.assess_preparation(
                    *(
                        actual[name]
                        for name in ("source", "nomination", "inventory", "coordinates")
                    ),
                    prepared,
                    assets,
                )
                != retained[ASSESS][ASSESS + ".assessment"]
            ):
                raise ValueError(
                    "preparation assessment fails independent raw24-asset reduction"
                )
        for records in retained.values():
            for output_id, record in ({} if records is None else records).items():
                bindings.append(
                    InquiryEvidenceBinding(
                        output_id,
                        record.fingerprint(),
                        c.scope(config.source),
                        ContributionRole.RETAINED_ANALYSIS_INPUT,
                        (),
                        draft.development_study.numerical_view_ids,
                    )
                )
    return tuple(sorted(bindings, key=lambda r: r.binding_id))


def describe_contributions(draft, products):
    config, retained = _actual_outputs(draft, products)
    if retained[ASSESS] is None:
        return ()
    exported = []
    for node, records in retained.items():
        receipt = products["receipts"][node]
        for output_id, record in records.items():
            logical = next(
                row
                for row in receipt.output_logical_artifacts
                if row.payload_schema == record.SCHEMA
                and row.content_sha256 == record.fingerprint()
            )
            artifact = products["outputs"][logical.logical_artifact_id]
            exported.append(
                ContributionProduct(
                    "product." + output_id,
                    c.identity(record),
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
            )
    return (
        ContributionManifest(
            "contribution." + draft.draft_id,
            c.QUESTION,
            "Complete controlled model preparation, raw24 assets, actual native attempt ledger and independent assigned-parameter assessment. Dynamics and kinetics remain unentered.",
            c.scope(config.source),
            tuple(sorted(exported, key=lambda row: row.product_id)),
            tuple(
                sorted(
                    (
                        c.identity(record)
                        for records in retained.values()
                        for record in records.values()
                    ),
                    key=lambda row: row.object_id,
                )
            ),
            (),
            tuple(
                ObjectIdentity.from_record(parent.contribution_id, parent)
                for parent in draft.contribution_parents
            ),
        ),
    )


def next_wave_builder(draft, manifest, products):
    if describe_contributions(draft, products) != (manifest,):
        raise ValueError(
            "model preparation successor changes actual source-bound products"
        )
    return None
