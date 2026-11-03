# SPDX-License-Identifier: MPL-2.0
"""Authentic diagnostic history, complete native custody and assessed supply."""

from dataclasses import replace
from hashlib import sha256

from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import BatteryInquirySource, scope as original_scope
from empirical_lawhood.kernel.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition, ConditionRole, ContributionRole, ScientificConnectionSpec, ScientificRequirementSpec
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.scientific_contributions import ContributionManifest, ContributionProduct
from empirical_lawhood.kernel.status import LifecycleStatus, OperationalStatus
from empirical_lawhood.planning.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.runtime.recursive_inquiry import InquiryEvidenceBinding

from . import contracts as c, science
from .operation_bindings import BUDGET, acquire_operation,qualify_operation,gate_operation,is_gate,common_inputs, MAX_BYTES, MEDIA, NAMESPACE, QUESTION, RefinedOperationConfig, SourcePolicyAdmission, development_root, operation_outputs, operation_registrations, record_identity, source_policy_admission, trace_ports

CONDITION = "Exact authentic twelve-forecast/nine-comparison diagnostic history informs an explicitly selected new numerical policy; source consistency grants no numerical adequacy. Complete new nine-preparation qualification remains independent."
FALSIFIER = "Changed diagnostic identity, original source, selected protocol, scientific gates or complete preparation/view rosters defeats source consistency; missing or disagreeing new reference traces defeats numerical adequacy."


OBSTRUCTION_CONDITION = "Exact authentic original1.1 negative36/9 procedure plus one entered diagnostic Native contact and BLOCKED unknown-completion terminal provide adverse operational HISTORY only. No DiagnosticResult or returned trace exists; actual forecast/charging/SOH counts remain unknown. The new complete45/54 qualification independently tests numerical adequacy."
OBSTRUCTION_FALSIFIER = "Changed original negative supplier, hidden/substituted contact/plan/terminal/input/census, invented completion or zero underlying counts, or treating obstruction documentation as numerical adequacy defeats source consistency; unchanged complete new raw numerical comparison gates remain required."


def _requirement_pair(scope, parent_identity, product_id, history=None):
    gate = "validate-policy" if history is None else gate_operation(history)
    node = NAMESPACE + "." + gate
    condition = CONDITION if gate == "validate-policy" else OBSTRUCTION_CONDITION
    falsifier = FALSIFIER if gate == "validate-policy" else OBSTRUCTION_FALSIFIER
    requirement = ScientificRequirementSpec(
        "requirement." + node + ".diagnostic-history", node, ConditionRole.EVIDENTIAL,
        QUESTION, condition, scope, node, falsifier, (ContributionRole.RETAINED_ANALYSIS_INPUT,),
    )
    connection = ScientificConnectionSpec(
        "connection." + node + ".diagnostic-history", requirement.requirement_id,
        None, None, "diagnostic", node, "claim." + NAMESPACE,
        ContributionRole.RETAINED_ANALYSIS_INPUT, falsifier, parent_identity, product_id,
        "external." + node + ".diagnostic",
    )
    return requirement, connection


def requirement_pair(source, parent_identity, product_id):
    """The parent retains the original diagnostic scope, including its negatives."""
    source.__post_init__()
    return _requirement_pair(original_scope(source.original), parent_identity, product_id,source.diagnostic)


def validate_requirement_config(config, requirement, connection):
    config.__post_init__()
    if (not is_gate(config.operation) or connection.supplier_contribution is None
            or connection.supplier_product_id is None):
        raise ValueError("refined policy requires its actual portable diagnostic history")
    expected = requirement_pair(config.source, connection.supplier_contribution, connection.supplier_product_id)
    if (requirement, connection) != expected:
        raise ValueError("refined policy changes the original diagnostic scope, history role or condition")


def validate_requirement_admission(admission, requirement, connection):
    if type(admission) is not SourcePolicyAdmission:
        raise ValueError("refined source assessment requires its actual source-policy admission")
    admission.__post_init__()
    if connection.supplier_contribution is None or connection.supplier_product_id is None:
        raise ValueError("refined source assessment omits actual diagnostic ownership")
    expected = _requirement_pair(original_scope(BatteryInquirySource()), connection.supplier_contribution,
                                 connection.supplier_product_id,admission.diagnostic)
    if (requirement, connection) != expected:
        raise ValueError("source consistency cannot substitute numerical qualification or a changed history condition")


def _campaign(root, draft_id):
    policy = AuthorityPolicy(
        "policy." + draft_id, "owner.local-researcher", "operator.local-development",
        (root.study_id,), frozenset((root.world_kind,)),
        frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION, AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)), ("gate.local-nonactuating-development",),
        frozenset(), BUDGET, OutcomeAccess.DEVELOPMENT_VISIBLE,
    )
    root_id = "design." + draft_id
    return CampaignSpec(
        "campaign." + draft_id, QUESTION, (root.system.object_id,), (root.world_id,),
        tuple(row.claim_id for row in root.claims), BUDGET, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight("decision-right." + draft_id, AuthorityAction.SIMULATION_EXECUTION,
                       "owner.local-researcher", policy.policy_id, False),),
        (CampaignNode(root_id, CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
                      ObjectIdentity.from_record(root.study_id, root), (), LifecycleStatus.ACTIVE),),
        (root_id,), (root_id,), (), LifecycleStatus.ACTIVE,
    )


def qualification_draft(diagnostic, source, policy, selection=None, *, parent,
                        draft_id="draft.battery-refined-inquiry.qualification"):
    """Select no defaults: bind actual history and explicit canonical policy bytes."""
    selection = policy.selection if selection is None else selection
    source_policy_admission(source, policy, selection, diagnostic)
    selected_gate = gate_operation(source.diagnostic)
    config = RefinedOperationConfig("config." + NAMESPACE + "."+selected_gate, selected_gate,
                                    source, policy, selection, record_identity(diagnostic))
    return draft_from_config(config, parent=parent, draft_id=draft_id)


def draft_from_config(config, *, parent, draft_id="draft.battery-refined-inquiry.qualification"):
    """Author selected operands; native execution still validates actual history bytes."""
    config.__post_init__()
    if not is_gate(config.operation) or type(parent) is not ContributionManifest:
        raise ValueError("refined qualification requires the source gate and actual diagnostic contribution")
    parent.__post_init__()
    matched = tuple(row for row in parent.products if row.record == config.diagnostic)
    if (len(matched) != 1 or matched[0].role is not ContributionRole.RETAINED_ANALYSIS_INPUT
            or parent.scope != original_scope(config.source.original)):
        raise ValueError("refined qualification changes exact diagnostic product, original scope or retained-history role")
    requirement, connection = requirement_pair(config.source,
        ObjectIdentity.from_record(parent.contribution_id, parent), matched[0].product_id)
    count = 54 if config.policy.tolerance_probe else 45
    selected_names = tuple(sorted((acquire_operation(config.diagnostic,count),qualify_operation(config.diagnostic,count),gate_operation(config.diagnostic))))
    registrations = {row.selection.capability_key: row for row in operation_registrations()}
    operations, external, links = [], [], []
    common = {"source": record_identity(config.source), "policy": record_identity(config.policy),
              "selection": record_identity(config.selection), "diagnostic": config.diagnostic}
    gate = NAMESPACE + "."+gate_operation(config.diagnostic)
    acquire = NAMESPACE + "."+acquire_operation(config.diagnostic,count)
    for name in selected_names:
        node = NAMESPACE + "." + name
        selected_config = replace(config, config_id="config." + node, operation=name)
        operations.append(RecursiveOperationSpec.from_config(
            node_id=node, selection=registrations[node].selection, config_id=selected_config.config_id,
            config=selected_config, obligation_ids=("obligation." + node + ".complete-source-and-evidence-census",),
            resource_budget=BUDGET,
            resource_lock_ids=("battery-native-single-worker",) if name.startswith("acquire-") else (),
        ))
        for port, _ in common_inputs(name):
            value = common[port]
            input_id = "external." + node + "." + port
            role = "HISTORY" if port == "diagnostic" else "SOURCE"
            external.append(RecursiveExternalInput(input_id,
                matched[0].artifact.artifact_id if port == "diagnostic" else value.object_id,
                value.object_schema, MEDIA, MAX_BYTES, OutcomeAccess.DEVELOPMENT_VISIBLE,
                VisibilityCeiling.DEVELOPMENT_ONLY, value.object_fingerprint, role))
            connected = port == "diagnostic" and node == gate
            links.append(RecursiveInputLink("edge." + node + "." + port, node, port,
                external_input_id=input_id, scientific_role=role,
                requirement_id=requirement.requirement_id if connected else None,
                connection_id=connection.connection_id if connected else None))
        if not is_gate(name):
            links.append(RecursiveInputLink("edge." + node + ".admission", node, "admission",
                producer_node_id=gate, producer_output_id="admission", scientific_role="MODEL"))
        if name.startswith("qualify-"):
            links.extend(RecursiveInputLink("edge." + node + "." + port, node, port,
                producer_node_id=acquire, producer_output_id=port, scientific_role="OUTCOME")
                for port in trace_ports(count))
    root = development_root(config, study_id="study." + draft_id)
    return RecursiveStudyDraft(draft_id, QUESTION, _campaign(root, draft_id), (requirement,), (connection,), (),
        tuple(sorted(operations, key=lambda row: row.node_id)), tuple(sorted(external, key=lambda row: row.input_id)),
        tuple(sorted(links, key=lambda row: row.edge_id)), tuple(sorted(row.node_id for row in operations)),
        development_study=root, contribution_parents=(parent,))


def _configs(draft):
    draft.__post_init__()
    configs = {row.node_id: decode_canonical_bytes(row.config_payload.encode(), RefinedOperationConfig,
                                                  maximum_bytes=None) for row in draft.operations}
    gate = next((row for row in configs.values() if is_gate(row.operation)),None)
    if gate is None or len(draft.contribution_parents) != 1:
        raise ValueError("refined qualification omits exact source gate or diagnostic parent")
    expected = draft_from_config(gate, parent=draft.contribution_parents[0], draft_id=draft.draft_id)
    if draft != expected:
        raise ValueError("refined qualification changes complete registered graph, scientific roles or root")
    return configs, gate


def _retained_outputs(node, config, products, *, output_contracts=None):
    """Join every parsed output to its complete successful producing receipt."""
    records = products.get("records", {}).get(node, {})
    if not records:
        return None
    outputs = operation_outputs(config.operation) if output_contracts is None else output_contracts
    expected = {node + "." + name: record for name, record in outputs}
    receipt = products.get("receipts", {}).get(node)
    if (records.keys() != expected.keys() or receipt is None or receipt.task_id != node
            or receipt.operational_status is not OperationalStatus.SUCCEEDED
            or len(receipt.output_logical_artifacts) != len(expected)):
        raise ValueError("refined output census differs from its complete successful producing receipt")
    logical_ids, materialization_ids = set(), set()
    expected_materialization_ids = {row.materialization_id for row in receipt.output_materializations}
    receipt_materializations = {row.materialization_id: row for row in receipt.output_materializations}
    for output_id, record_type in expected.items():
        record = records[output_id]
        if type(record) is not record_type:
            raise ValueError("refined actual output substitutes its declared typed record")
        record.__post_init__()
        matching = tuple(row for row in receipt.output_logical_artifacts
                         if row.payload_schema == record.SCHEMA and row.content_sha256 == record.fingerprint())
        if len(matching) != 1:
            raise ValueError("refined record differs from actual producing receipt bytes")
        logical = matching[0]
        if logical.logical_artifact_id != "artifact." + receipt.run_id + "." + output_id:
            raise ValueError("refined output substitutes its declared output ordinal or logical identity")
        artifact = products.get("outputs", {}).get(logical.logical_artifact_id)
        if (artifact is None or artifact.logical != logical
                or artifact.materialization.materialization_id not in expected_materialization_ids
                or artifact.materialization != receipt_materializations[artifact.materialization.materialization_id]
                or artifact.materialization.physical_sha256 != record.fingerprint()
                or artifact.materialization.size_bytes != len(record.canonical_bytes())
                or logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
            raise ValueError("refined output loses exact authenticated materialization, custody or access")
        logical_ids.add(logical.logical_artifact_id)
        materialization_ids.add(artifact.materialization.materialization_id)
    if (len(logical_ids) != len(expected) or materialization_ids != expected_materialization_ids):
        raise ValueError("refined output hides or duplicates retained materialization census")
    return records


def _actual_product(draft, products):
    configs, gate = _configs(draft)
    retained = {node: _retained_outputs(node, config, products) for node, config in configs.items()}
    count = 54 if gate.policy.tolerance_probe else 45
    gate_node = NAMESPACE + "."+gate_operation(gate.diagnostic)
    acquire_node = NAMESPACE + "."+acquire_operation(gate.diagnostic,count)
    qualify_node = NAMESPACE + "."+qualify_operation(gate.diagnostic,count)
    admission = None if retained[gate_node] is None else retained[gate_node][gate_node + ".admission"]
    if admission is not None:
        if (admission.source != record_identity(gate.source) or admission.policy != record_identity(gate.policy)
                or admission.selection != record_identity(gate.selection) or admission.diagnostic != gate.diagnostic):
            raise ValueError("actual source-policy gate substitutes the configured operands")
        validate_requirement_admission(admission, draft.requirements[0], draft.connections[0])
    if retained[qualify_node] is None:
        return gate, None, retained
    if admission is None or retained[acquire_node] is None:
        raise ValueError("qualified compact product omits actual source gate or complete native traces")
    traces = tuple(retained[acquire_node][acquire_node + "." + port] for port in trace_ports(count))
    if tuple(trace.config for trace in traces) != science.configurations(gate.source, gate.policy):
        raise ValueError("actual qualification changes exact trace configuration/ordinal census")
    qualification = retained[qualify_node][qualify_node + ".qualification"]
    supply = retained[qualify_node][qualify_node + ".supply"]
    # A compact product never establishes numerical adequacy by itself.
    science.validate_qualification(gate.source, gate.policy, qualification, traces)
    if supply != science.construct_supply(gate.source, gate.policy, qualification, traces):
        raise ValueError("actual supplier differs from complete independently reduced raw evidence")
    return gate, supply, retained


def inquiry_endpoint_validator(draft, endpoint):
    if _is_recipient(draft):
        return recipient_endpoint_validator(draft, endpoint)
    _, config = _configs(draft)
    if endpoint != c.scope(config.source):
        raise ValueError("refined inquiry changes its explicitly selected numerical source scope")


def inquiry_outcome_projector(draft, specification, products):
    if _is_recipient(draft):
        return recipient_outcome_projector(draft, specification, products)
    inquiry_endpoint_validator(draft, specification.endpoint)
    _, supply, _ = _actual_product(draft, products)
    # Canonical operation order is lexical; all three form one actual assessment.
    if specification.distinguishing_assessment != draft.operations[0].config_identity:
        raise ValueError("refined inquiry changes its designated complete assessment configuration")
    if supply is None:
        return "unresolved"
    return "useful-supply" if supply.disposition is AssessmentDisposition.SATISFIED else "unresolved"


def inquiry_evidence_projector(draft, payloads, products=None):
    if _is_recipient(draft):
        return recipient_evidence_projector(draft, payloads, products)
    configs, config = _configs(draft)
    external = {row.input_id: row for row in draft.external_inputs}
    bindings, actual = [], {}
    for node in configs:
        for port, codec in common_inputs(config.operation):
            input_id = "external." + node + "." + port
            selected = external[input_id]
            raw = payloads["external-" + sha256(input_id.encode()).hexdigest()[:24] + ".json"]
            record = decode_canonical_bytes(raw, codec, maximum_bytes=None)
            expected = config.diagnostic if port == "diagnostic" else record_identity(getattr(config, port))
            if record_identity(record) != expected or record.fingerprint() != selected.expected_content_sha256:
                raise ValueError("refined evidence substitutes actual selected external operand bytes")
            if port in actual and record != actual[port]:
                raise ValueError("refined graph exposes conflicting bytes for one scientific operand")
            actual[port] = record
            bindings.append(InquiryEvidenceBinding(input_id, record.fingerprint(),
                original_scope(config.source.original) if port == "diagnostic" else c.scope(config.source),
                ContributionRole.RETAINED_ANALYSIS_INPUT, (), draft.development_study.numerical_view_ids))
    source_policy_admission(*(actual[name] for name in ("source", "policy", "selection", "diagnostic")))
    if products is not None:
        _, supply, retained = _actual_product(draft, products)
        for records in retained.values():
            for output_id, record in ({} if records is None else records).items():
                bindings.append(InquiryEvidenceBinding(output_id, record.fingerprint(), c.scope(config.source),
                    ContributionRole.DESIGN_OPERAND if type(record) is c.Supply else ContributionRole.RETAINED_ANALYSIS_INPUT,
                    (), draft.development_study.numerical_view_ids))
        if supply is not None and supply.source != actual["source"]:
            raise ValueError("refined supplier changes authenticated original selection")
    return tuple(sorted(bindings, key=lambda row: row.binding_id))


def describe_contributions(draft, products):
    if _is_recipient(draft):
        return describe_recipient_contributions(draft, products)
    config, supply, retained = _actual_product(draft, products)
    if supply is None:
        return ()
    exported = []
    # Every raw supplier trace has an explicit authentic product origin in a
    # later wave. It must never be disguised as a fresh SOURCE input merely
    # because the supplier itself is compact.
    for node, records in retained.items():
        receipt = products["receipts"][node]
        for output_id, record in records.items():
            logical = next(row for row in receipt.output_logical_artifacts
                           if row.payload_schema == record.SCHEMA and row.content_sha256 == record.fingerprint())
            artifact = products["outputs"][logical.logical_artifact_id]
            exported.append(ContributionProduct("product." + output_id, record_identity(record),
                ArtifactIdentity(logical.logical_artifact_id, "scientific-product", record.SCHEMA, record.fingerprint(),
                                 logical.media_type, artifact.materialization.size_bytes),
                ObjectIdentity.from_record(receipt.receipt_id, receipt),
                ContributionRole.DESIGN_OPERAND if type(record) is c.Supply else ContributionRole.RETAINED_ANALYSIS_INPUT,
                EvidenceCeiling.NON_PROMOTABLE, logical.outcome_access, logical.visibility_ceiling))
    return (ContributionManifest("contribution." + draft.draft_id, QUESTION,
        "Actual full-roster finite-path conditional numerical supplier with independently reduced band/mesh/combined evidence; all traces retain custody. No physical qualification, whole-time certificate, controller authority or comparative advantage.",
        c.scope(config.source), tuple(sorted(exported, key=lambda row: row.product_id)),
        tuple(sorted((record_identity(record) for record in (supply.qualification, *supply.qualification.checks,
                                                            *supply.qualification.comparisons)), key=lambda row: row.object_id)),
        (), tuple(ObjectIdentity.from_record(parent.contribution_id, parent) for parent in draft.contribution_parents)),)


SUPPLIER_CONDITION = "Actual full-roster qualified numerical supplier supports an independently assessed distinct later preparation and forecast-only choice committed before remaining band/refined/tolerance reference acquisition."
PRIOR_USE_CONDITION = "Actual entered twenty-degree instance retains the same original supplier and its complete raw outcomes; its disposition remains historical evidence rather than a guarantee of the later thirty-degree result."
RECIPIENT_FALSIFIER = "Changed original supplier, source, policy, prior-use identity or full trace census; missing persisted choice dependency; failed recipient reference precision, model admission or delivered-service assessment defeats the declared conditional use."


def _is_recipient(draft):
    from .recipient_bindings import RecipientOperationConfig
    return bool(draft.operations) and draft.operations[0].config_identity.object_schema == RecipientOperationConfig.SCHEMA


def _recipient_pair(source, phase, count, parent_identity, product_id, *, prior=False):
    from . import recipient_bindings as rb
    consumer = rb.node_id(f"validate-{phase}-{count}" if prior else f"forecast-{phase}-{count}")
    assessor = rb.node_id(f"assess-{phase}-{count}")
    port = "prior-use" if prior else "supplier"
    condition = PRIOR_USE_CONDITION if prior else SUPPLIER_CONDITION
    role = ContributionRole.INSTANCE_PRODUCT if prior else ContributionRole.DESIGN_OPERAND
    requirement = ScientificRequirementSpec("requirement." + consumer + "." + port, consumer,
        ConditionRole.EVIDENTIAL, QUESTION, condition, c.scope(source), assessor, RECIPIENT_FALSIFIER, (role,))
    connection = ScientificConnectionSpec("connection." + consumer + "." + port, requirement.requirement_id,
        None, None, port, assessor, "claim." + NAMESPACE + ".recipient", role, RECIPIENT_FALSIFIER,
        parent_identity, product_id, "external." + consumer + "." + port)
    return requirement, connection


def validate_recipient_requirement_config(config, requirements, connections):
    from . import recipient_bindings as rb
    config.__post_init__()
    _, phase, count = rb.parts(config.operation)
    expected_count = 2 if phase == "reuse" else 1
    if len(requirements) != expected_count or len(connections) != expected_count:
        raise ValueError("recipient changes its actual original supplier/prior-use scientific conditions")
    by_requirement = {row.requirement_id: row for row in requirements}
    ports = set()
    for connection in connections:
        prior = connection.consumer_input_id == "prior-use"
        if (connection.consumer_input_id not in {"supplier", "prior-use"} or prior and phase != "reuse"
                or connection.supplier_contribution is None or connection.supplier_product_id is None):
            raise ValueError("recipient omits exact authentic parent product ownership")
        expected = _recipient_pair(config.source, phase, count, connection.supplier_contribution,
                                   connection.supplier_product_id, prior=prior)
        if (by_requirement.get(connection.requirement_id), connection) != expected:
            raise ValueError("recipient changes its original scientific scope, role, phase or falsifier")
        ports.add(connection.consumer_input_id)
    if ports != ({"supplier", "prior-use"} if phase == "reuse" else {"supplier"}):
        raise ValueError("recipient duplicates or omits original supplier/prior-use conditions")


def validate_recipient_requirement_record(record, requirement, connection):
    if type(record) is not c.AssessedInstance:
        raise ValueError("recipient requirement requires actual independently assessed instance")
    record.__post_init__()
    phase = record.assessment.instance.phase
    count = len(record.supplier.qualification.traces)
    prior = connection.consumer_input_id == "prior-use"
    if (connection.supplier_contribution is None or connection.supplier_product_id is None
            or prior and (phase != "reuse" or record.prior_use is None)):
        raise ValueError("recipient assessment omits its actual original supplier or prior use")
    expected = _recipient_pair(record.supplier.source, phase, count, connection.supplier_contribution,
                               connection.supplier_product_id, prior=prior)
    if (requirement, connection) != expected:
        raise ValueError("recipient assessment changes the original conditional use grammar")


def _source_admission_join(source, policy, selection, admission):
    if type(admission) is not SourcePolicyAdmission:
        raise ValueError("recipient requires actual prior source-policy gate")
    admission.__post_init__()
    if (admission.source != record_identity(source) or admission.policy != record_identity(policy)
            or admission.selection != record_identity(selection) or admission.diagnostic != source.diagnostic
            or selection != policy.selection or source.policy != record_identity(policy)
            or source.protocol_sha256 != selection.fingerprint()):
        raise ValueError("recipient substitutes authentic source-policy admission/protocol lineage")


def use_draft(supplier, source_admission, *, parent, draft_id="draft.battery-refined-inquiry.use"):
    from .recipient_bindings import RecipientOperationConfig, node_id
    instance = science.compatible_instance(supplier, "use")
    _source_admission_join(supplier.source, supplier.policy, supplier.policy.selection, source_admission)
    count = len(supplier.qualification.traces)
    operation = f"validate-use-{count}"
    config = RecipientOperationConfig("config." + node_id(operation), operation, supplier.source, supplier.policy,
        supplier.policy.selection, supplier.source.diagnostic, record_identity(source_admission), supplier, instance,
        supplier.qualification.traces, None, ())
    return _recipient_draft_from_config(config, parent=parent, draft_id=draft_id)


def reuse_draft(previous, source_admission, *, parent, draft_id="draft.battery-refined-inquiry.reuse"):
    from .recipient_bindings import RecipientOperationConfig, node_id
    if type(previous) is not c.AssessedInstance or previous.assessment.instance.phase != "use":
        raise ValueError("refined reuse requires actual entered distinct prior use")
    previous.__post_init__()
    supplier = previous.supplier
    instance = science.compatible_instance(supplier, "reuse", prior_use=previous)
    _source_admission_join(supplier.source, supplier.policy, supplier.policy.selection, source_admission)
    count = len(supplier.qualification.traces)
    operation = f"validate-reuse-{count}"
    config = RecipientOperationConfig("config." + node_id(operation), operation, supplier.source, supplier.policy,
        supplier.policy.selection, supplier.source.diagnostic, record_identity(source_admission), supplier, instance,
        supplier.qualification.traces, previous, previous.assessment.traces)
    return _recipient_draft_from_config(config, parent=parent, draft_id=draft_id)


def _recipient_operand(config, name):
    from . import recipient_bindings as rb
    if name == "source-admission":
        return config.source_admission
    if name.startswith("supplier-trace-"):
        return config.supplier_traces[rb.ports("supplier-trace", len(config.supplier_traces)).index(name)]
    if name.startswith("prior-trace-"):
        return config.prior_traces[rb.ports("prior-trace", len(config.prior_traces)).index(name)]
    return record_identity(config.prior_use if name == "prior-use" else getattr(config, name))


def _recipient_draft_from_config(config, *, parent, draft_id):
    from . import recipient_bindings as rb
    config.__post_init__()
    _, phase, count = rb.parts(config.operation)
    if config.operation != f"validate-{phase}-{count}" or type(parent) is not ContributionManifest:
        raise ValueError("recipient requires its exact initial validation config and actual contribution")
    parent.__post_init__()
    if parent.scope != c.scope(config.source):
        raise ValueError("recipient changes original selected numerical source scope")
    parent_identity = ObjectIdentity.from_record(parent.contribution_id, parent)
    registrations = {row.selection.capability_key: row for row in rb.operation_registrations()}
    operations, external, links, pairs = [], [], [], []
    for step in rb.STEPS:
        name = f"{step}-{phase}-{count}"
        node = rb.node_id(name)
        selected = replace(config, config_id="config." + node, operation=name)
        operations.append(RecursiveOperationSpec.from_config(node_id=node, selection=registrations[node].selection,
            config_id=selected.config_id, config=selected,
            obligation_ids=("obligation." + node + ".full-custody-and-before-reveal-choice",), resource_budget=BUDGET,
            resource_lock_ids=("battery-native-single-worker",) if step in ("forecast", "complete") else ()))
        for port, _ in rb.external_inputs(name):
            identity = _recipient_operand(config, port)
            role = ("MODEL" if port == "supplier" else "OUTCOME" if port == "prior-use" else "HISTORY"
                    if port == "source-admission" or port.startswith(("supplier-trace-", "prior-trace-")) else "SOURCE")
            contributed = role != "SOURCE"
            matched = tuple(row for row in parent.products if row.record == identity)
            expected_role = (ContributionRole.DESIGN_OPERAND if role == "MODEL" else ContributionRole.INSTANCE_PRODUCT
                             if role == "OUTCOME" else ContributionRole.RETAINED_ANALYSIS_INPUT)
            if contributed and (len(matched) != 1 or matched[0].role is not expected_role):
                raise ValueError("recipient omits exact portable supplier, source gate or full raw trace product origins")
            input_id = "external." + node + "." + port
            external.append(RecursiveExternalInput(input_id, matched[0].artifact.artifact_id if contributed else identity.object_id,
                identity.object_schema, MEDIA, MAX_BYTES, OutcomeAccess.DEVELOPMENT_VISIBLE,
                VisibilityCeiling.DEVELOPMENT_ONLY, identity.object_fingerprint, role))
            pair = None
            if port == "supplier" and step == "forecast" or port == "prior-use" and step == "validate":
                pair = _recipient_pair(config.source, phase, count, parent_identity, matched[0].product_id, prior=port == "prior-use")
                pairs.append(pair)
            links.append(RecursiveInputLink("edge." + node + "." + port, node, port, external_input_id=input_id,
                scientific_role=role, requirement_id=pair[0].requirement_id if pair else None,
                connection_id=pair[1].connection_id if pair else None))
        links.extend(RecursiveInputLink("edge." + node + "." + port, node, port,
            producer_node_id=rb.node_id(producer), producer_output_id=output,
            scientific_role="MODEL" if port == "admission" else "OUTCOME")
            for port, _, producer, output in rb.dependency_inputs(name))
    root = rb.development_root(config, study_id="study." + draft_id)
    return RecursiveStudyDraft(draft_id, QUESTION, _campaign(root, draft_id),
        tuple(sorted((row[0] for row in pairs), key=lambda row: row.requirement_id)),
        tuple(sorted((row[1] for row in pairs), key=lambda row: row.connection_id)), (),
        tuple(sorted(operations, key=lambda row: row.node_id)), tuple(sorted(external, key=lambda row: row.input_id)),
        tuple(sorted(links, key=lambda row: row.edge_id)), tuple(sorted(row.node_id for row in operations)),
        development_study=root, contribution_parents=(parent,))


def _recipient_configs(draft):
    from . import recipient_bindings as rb
    draft.__post_init__()
    configs = {row.node_id: decode_canonical_bytes(row.config_payload.encode(), rb.RecipientOperationConfig,
                                                  maximum_bytes=None) for row in draft.operations}
    gates = tuple(row for row in configs.values() if rb.parts(row.operation)[0] == "validate")
    if len(gates) != 1 or len(draft.contribution_parents) != 1:
        raise ValueError("recipient omits exact validation node or authentic immediate parent")
    expected = _recipient_draft_from_config(gates[0], parent=draft.contribution_parents[0], draft_id=draft.draft_id)
    if draft != expected:
        raise ValueError("recipient changes exact registered graph, lineage or before-reveal choice dependencies")
    return configs, gates[0]


def _recipient_actual_product(draft, products):
    from . import recipient_bindings as rb
    configs, config = _recipient_configs(draft)
    retained = {node: _retained_outputs(node, row, products, output_contracts=rb.operation_outputs(row.operation))
                for node, row in configs.items()}
    _, phase, count = rb.parts(config.operation)
    nodes = {step: rb.node_id(f"{step}-{phase}-{count}") for step in rb.STEPS}
    gate = retained[nodes["validate"]]
    if gate is not None:
        if (gate[nodes["validate"] + ".admission"] != rb.expected_admission(config)
                or gate[nodes["validate"] + ".supplier-product"] != config.supplier):
            raise ValueError("actual recipient gate changes admitted original supplier or complete custody")
        source_admission = gate[nodes["validate"] + ".source-admission"]
        if record_identity(source_admission) != config.source_admission:
            raise ValueError("actual recipient gate substitutes original source-policy receipt product")
        _source_admission_join(config.source, config.policy, config.selection, source_admission)
        supplier_traces = tuple(gate[nodes["validate"] + "." + port] for port in rb.ports("supplier-trace", count))
        if tuple(record_identity(row) for row in supplier_traces) != config.supplier_traces:
            raise ValueError("recipient supplier relay changes original trace bytes or identity")
        science.validate_qualification(config.source, config.policy, config.supplier.qualification, supplier_traces)
        if phase == "reuse":
            prior = gate[nodes["validate"] + ".prior-use"]
            prior_traces = tuple(gate[nodes["validate"] + "." + port] for port in rb.ports("prior-trace", len(config.prior_traces)))
            if prior != config.prior_use or tuple(record_identity(row) for row in prior_traces) != config.prior_traces:
                raise ValueError("recipient reuses different actual prior-use bytes or full raw census")
            science.validate_assessment(config.supplier, prior.assessment, prior_traces)
    if retained[nodes["assess"]] is None:
        return config, None, retained
    if any(retained[node] is None for node in nodes.values()):
        raise ValueError("actual recipient assessment omits entered gate, forecast, choice or reference receipt")
    # The actual complete-census receipt consumes the persisted choice output.
    # Identity equality in an Assessment alone cannot prove before-reveal order.
    choice_receipt = products["receipts"][nodes["choose"]]
    if not {row.materialization_id for row in choice_receipt.output_materializations}.issubset(
            products["receipts"][nodes["complete"]].input_materialization_ids):
        raise ValueError("reference acquisition omits an actual persisted EL/direct/Chen choice receipt dependency")
    forecasts = tuple(retained[nodes["forecast"]][nodes["forecast"] + "." + port] for port in rb.ports("forecast", 9))
    remaining = tuple(retained[nodes["complete"]][nodes["complete"] + "." + port]
                      for port in rb.ports("trace", len(rb.remaining_configs(config))))
    if (tuple(row.config for row in forecasts) != rb.forecast_configs(config)
            or tuple(row.config for row in remaining) != rb.remaining_configs(config)):
        raise ValueError("recipient substitutes exact current forecast/reference preparation/config census")
    choice = retained[nodes["choose"]][nodes["choose"] + ".choice"]
    if choice != science.commit_choice(config.supplier, config.instance, rb.selected_forecasts(config, forecasts)):
        raise ValueError("recipient persisted choice differs from forecast-only actual reduction")
    traces = tuple(sorted((*forecasts, *remaining), key=lambda row: row.trace_id))
    assessment = retained[nodes["assess"]][nodes["assess"] + ".assessment"]
    assessed = retained[nodes["assess"]][nodes["assess"] + ".assessed"]
    expected = science.assess_instance(config.supplier, config.instance, traces, choice, record_identity(choice), prior_use=config.prior_use)
    if assessment != expected or assessed != c.AssessedInstance("product." + NAMESPACE + ".assessed-" + phase,
        config.supplier, expected, config.prior_use.assessment if config.prior_use is not None else None):
        raise ValueError("actual compact recipient products differ from complete independent raw reduction")
    for arm, prefix in (("chen", "chen"), ("direct-dfn", "direct")):
        comparator_choice = retained[nodes["choose"]][nodes["choose"] + "." + prefix + "-choice"]
        if comparator_choice != rb.comparator_choice(config, forecasts, arm):
            raise ValueError("comparator persisted choice differs from its own three foreground forecasts")
        comparator_assessment = retained[nodes["assess"]][nodes["assess"] + "." + prefix + "-assessment"]
        if comparator_assessment != rb.assess_comparator(config, traces, comparator_choice):
            raise ValueError("comparator assessment differs from independently reduced complete raw reference evidence")
    return config, assessed, retained


def recipient_endpoint_validator(draft, endpoint):
    _, config = _recipient_configs(draft)
    if endpoint != c.scope(config.source):
        raise ValueError("recipient changes original qualified numerical source scope")


def recipient_outcome_projector(draft, specification, products):
    recipient_endpoint_validator(draft, specification.endpoint)
    _, record, _ = _recipient_actual_product(draft, products)
    if specification.distinguishing_assessment != draft.operations[0].config_identity:
        raise ValueError("recipient changes designated complete actual assessment")
    if record is None or record.assessment.disposition is AssessmentDisposition.UNEVALUABLE:
        return "unresolved"
    return "useful-supply" if record.assessment.disposition is AssessmentDisposition.SATISFIED else "scoped-failure"


def recipient_evidence_projector(draft, payloads, products=None):
    from . import recipient_bindings as rb
    configs, config = _recipient_configs(draft)
    external = {row.input_id: row for row in draft.external_inputs}
    bindings, originals = [], {}
    for node, selected_config in configs.items():
        for port, codec in rb.external_inputs(selected_config.operation):
            input_id = "external." + node + "." + port
            record = decode_canonical_bytes(payloads["external-" + sha256(input_id.encode()).hexdigest()[:24] + ".json"],
                                            codec, maximum_bytes=None)
            if record_identity(record) != _recipient_operand(config, port) or record.fingerprint() != external[input_id].expected_content_sha256:
                raise ValueError("recipient evidence substitutes original source or authenticated full custody operand")
            if port in originals and originals[port] != record:
                raise ValueError("recipient exposes conflicting bytes for one original scientific operand")
            originals[port] = record
            role = (ContributionRole.DESIGN_OPERAND if port == "supplier" else ContributionRole.INSTANCE_PRODUCT
                    if port == "prior-use" else ContributionRole.RETAINED_ANALYSIS_INPUT)
            bindings.append(InquiryEvidenceBinding(input_id, record.fingerprint(), c.scope(config.source), role, (),
                                                   draft.development_study.numerical_view_ids))
    _source_admission_join(config.source, config.policy, config.selection, originals["source-admission"])
    supplier_traces = tuple(originals[port] for port in rb.ports("supplier-trace", len(config.supplier_traces)))
    science.validate_qualification(config.source, config.policy, config.supplier.qualification, supplier_traces)
    if config.prior_use is not None:
        prior_traces = tuple(originals[port] for port in rb.ports("prior-trace", len(config.prior_traces)))
        science.validate_assessment(config.supplier, config.prior_use.assessment, prior_traces)
    if products is not None:
        _, _, retained = _recipient_actual_product(draft, products)
        for records in retained.values():
            for output_id, record in ({} if records is None else records).items():
                role = (ContributionRole.DESIGN_OPERAND if type(record) is c.Supply else ContributionRole.INSTANCE_PRODUCT
                        if type(record) is c.AssessedInstance else ContributionRole.RETAINED_ANALYSIS_INPUT)
                bindings.append(InquiryEvidenceBinding(output_id, record.fingerprint(), c.scope(config.source), role, (),
                                                       draft.development_study.numerical_view_ids))
    return tuple(sorted(bindings, key=lambda row: row.binding_id))


def describe_recipient_contributions(draft, products):
    from . import recipient_bindings as rb
    config, assessed, retained = _recipient_actual_product(draft, products)
    if assessed is None:
        return ()
    exported = []
    for node, records in retained.items():
        receipt = products["receipts"][node]
        for output_id, record in records.items():
            logical = next(row for row in receipt.output_logical_artifacts
                           if row.payload_schema == record.SCHEMA and row.content_sha256 == record.fingerprint())
            artifact = products["outputs"][logical.logical_artifact_id]
            identity = rb.admission_identity(record) if type(record) is rb.RecipientAdmission else record_identity(record)
            exported.append(ContributionProduct("product." + output_id, identity,
                ArtifactIdentity(logical.logical_artifact_id, "scientific-product", record.SCHEMA, record.fingerprint(),
                                 logical.media_type, artifact.materialization.size_bytes),
                ObjectIdentity.from_record(receipt.receipt_id, receipt),
                ContributionRole.DESIGN_OPERAND if type(record) is c.Supply else ContributionRole.INSTANCE_PRODUCT
                if type(record) is c.AssessedInstance else ContributionRole.RETAINED_ANALYSIS_INPUT,
                EvidenceCeiling.NON_PROMOTABLE, logical.outcome_access, logical.visibility_ceiling))
    return (ContributionManifest("contribution." + draft.draft_id, QUESTION,
        "Actual separate later preparation with receipt-backed declared three-model foreground choices before remaining band/refined/tolerance reference acquisition. Exact-byte supplier and prior-use custody relays preserve historical evidence; relays create no new scientific units, native forecasts or freshness. Complete current and historical trace censuses remain explicit; comparative benefit and physical qualification are not established.",
        c.scope(config.source), tuple(sorted(exported, key=lambda row: row.product_id)),
        (record_identity(assessed.assessment),), (),
        tuple(ObjectIdentity.from_record(parent.contribution_id, parent) for parent in draft.contribution_parents)),)


def next_wave_builder(draft, manifest, products):
    """One later use and one reuse, with actual closure; no additional uses."""
    if describe_contributions(draft, products) != (manifest,):
        raise ValueError("refined successor changes its independently checked actual contribution")
    if _is_recipient(draft):
        from . import recipient_bindings as rb
        config, assessed, retained = _recipient_actual_product(draft, products)
        _, phase, count = rb.parts(config.operation)
        if assessed is None or phase != "use":
            return None
        gate = rb.node_id(f"validate-{phase}-{count}")
        return reuse_draft(assessed, retained[gate][gate + ".source-admission"], parent=manifest)
    config, supply, retained = _actual_product(draft, products)
    if supply is None or supply.disposition is not AssessmentDisposition.SATISFIED:
        return None
    gate = NAMESPACE + "."+gate_operation(config.diagnostic)
    return use_draft(supply, retained[gate][gate + ".admission"], parent=manifest)
