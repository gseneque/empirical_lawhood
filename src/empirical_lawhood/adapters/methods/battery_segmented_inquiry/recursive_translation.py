# SPDX-License-Identifier: MPL-2.0
"""Complete durable graph and exact target-directed scientific work operands."""

from dataclasses import dataclass, replace
from hashlib import sha256
from functools import lru_cache
from typing import ClassVar

from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c, preparation_contracts as pc
from empirical_lawhood.adapters.methods.battery_refined_inquiry.recursive_translation import _campaign
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry_policy import ScientificInquiryWork
from empirical_lawhood.kernel.recursive_requirements import ConditionRole, ContributionRole, ScientificConnectionSpec, ScientificRequirementSpec
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from . import operation_bindings as ob


def configs(config):
    return _configs(replace(config, operation="validate", index=None, config_id="config." + ob.node_id("validate")))


@lru_cache(maxsize=8)
def _configs(config):
    roster = ob.roster_for(config)
    rows = []
    for operation, index in (("validate", None), ("qualify", None),
            *(("forecast", i) for i in range(54) if ob.representative_index(roster, i) == i),
            *(("assess" if ob.representative_index(roster, i) == i else "reuse", i) for i in range(54)),
            *(("compare", i) for i in range(36))):
        rows.append(replace(config, operation=operation, index=index, config_id="config." + ob.node_id(operation, index)))
    return tuple(sorted(rows, key=lambda row: row.config_id))


def protocol_for(config, native_index):
    roster = ob.roster_for(config)
    representatives = tuple(i for i in range(54) if ob.representative_index(roster, i) == i)
    return config.preparation_protocols[representatives.index(native_index)]


@lru_cache(maxsize=256)
def input_sources(config):
    """Port-name to exact immutable external or ordinary dependency identity."""
    roster = ob.roster_for(config)
    common = {"source": c.identity(config.source), "policy": c.identity(config.policy),
        "selection": ObjectIdentity.from_record("selection." + config.policy.policy_id, config.policy.selection),
        "history": config.source.diagnostic, "roster": config.roster, "uncertain-work": config.uncertain_work,
        "producing-provenance": config.producing_provenance,
        "method": ObjectIdentity.from_record(config.method.method_id, config.method)}
    for stock, (preparation, assessment) in zip(("chen", "oregan"), config.supplies, strict=True):
        common["preparation-" + stock] = ObjectIdentity.from_record(preparation.preparation_id, preparation)
        common["source-assessment-" + stock] = ObjectIdentity.from_record(assessment.assessment_id, assessment)
    result = {name: ("EXTERNAL", value.object_id) for name, value in common.items()}
    result["history"] = ("EXTERNAL", config.history_artifact_id)
    gate = ob.node_id("validate")
    if config.operation == "forecast":
        result.update({"admission": ("DEPENDENCY", gate + ".admission"), "entry": ("DEPENDENCY", gate + ".entry-" + f"{config.index:03d}"),
            "native-config": ("EXTERNAL", roster.configurations[config.index].config_id),
            "selected-protocol": ("EXTERNAL", protocol_for(config, config.index).object_id)})
    elif config.operation == "assess":
        producer = ob.node_id("forecast", config.index)
        result.update((name, ("DEPENDENCY", producer + "." + name)) for name, _ in ob.FORECAST_OUTPUTS)
    elif config.operation == "reuse":
        result["summary"] = ("DEPENDENCY", ob.node_id("assess", ob.representative_index(roster, config.index)) + ".summary")
    elif config.operation == "compare":
        left_id, right_id = roster.comparison_config_pairs[config.index]
        indexes = {native.config_id: i for i, native in enumerate(roster.configurations)}
        for name, value in (("left", left_id), ("right", right_id)):
            i = indexes[value]
            result[name + "-summary"] = ("DEPENDENCY", ob.summary_node(roster, i) + ".summary")
            result[name + "-evidence"] = ("DEPENDENCY", ob.node_id("forecast", ob.representative_index(roster, i)) + ".evidence")
    elif config.operation == "qualify":
        result.update(("summary-" + f"{i:03d}", ("DEPENDENCY", ob.summary_node(roster, i) + ".summary")) for i in range(54))
        result.update(("comparison-" + f"{i:03d}", ("DEPENDENCY", ob.node_id("compare", i) + ".comparison")) for i in range(36))
    return result


def requirement_pair(config, parent, product):
    gate = ob.node_id("validate")
    scope = c.scope(config.source)
    requirement = ScientificRequirementSpec("requirement." + gate + ".actual-unknown-history", gate, ConditionRole.EVIDENTIAL,
        ob.QUESTION, "Authentic original negative36/9 and actual UNKNOWN twelve-forecast diagnostic contact remain adverse HISTORY; changed source-derived preparation and short-step operands neither infer old counts nor clear old completion.",
        scope, gate, "Changed primary custody/source/contact or invented diagnostic completion refuses; current independent preparation and numerical adequacy remain separate.",
        (ContributionRole.RETAINED_ANALYSIS_INPUT,))
    connection = ScientificConnectionSpec("connection." + gate + ".actual-unknown-history", requirement.requirement_id,
        None, None, "history", gate, "claim." + ob.NAMESPACE, ContributionRole.RETAINED_ANALYSIS_INPUT,
        requirement.falsifier, ObjectIdentity.from_record(parent.contribution_id, parent), product.product_id,
        "external." + gate + ".history")
    return requirement, connection


def qualification_draft(roster, uncertain, provenance, protocols, *, parent,
                        draft_id="draft.battery-segmented-inquiry.qualification"):
    """Freeze an honest full54/36 graph without contacting native science."""
    roster.__post_init__()
    source, policy = roster.original_selection.source, roster.original_selection.policy
    representatives = tuple(i for i in range(54) if ob.representative_index(roster, i) == i)
    if len(protocols) != len(representatives) or any(type(protocol) is not pc.PreparationProtocol
            or protocol.configuration != c.identity(roster.configurations[i]) or protocol.source != c.identity(source)
            or protocol.producing_provenance != provenance.identity for protocol, i in zip(protocols, representatives, strict=True)):
        raise ValueError("durable graph requires exact prospective contracts for all distinct native forecasts")
    if roster.uncertain_work != ObjectIdentity.from_record(uncertain.record_id, uncertain):
        raise ValueError("segmented graph changes its actual retained uncertain-work source")
    products = tuple(product for product in parent.products if product.record == source.diagnostic and product.role is ContributionRole.RETAINED_ANALYSIS_INPUT)
    if len(products) != 1:
        raise ValueError("durable graph requires its actual portable adverse history product")
    product = products[0]
    seed = ob.SegmentedOperationConfig("config." + ob.node_id("validate"), "validate", None, source, policy,
        ObjectIdentity.from_record(roster.roster_id, roster), ObjectIdentity.from_record(uncertain.record_id, uncertain), provenance.identity,
        tuple(pc.identity(protocol, protocol.protocol_id) for protocol in protocols), product.artifact.artifact_id,
        roster.method, ob.supplies_for(roster))
    requirement, connection = requirement_pair(seed, parent, product)
    registrations = {row.selection.capability_key: row for row in ob.operation_registrations()}
    values = {value.object_id: value for value in seed.operands}
    values[product.artifact.artifact_id] = source.diagnostic
    values.update((c.identity(native).object_id, c.identity(native)) for native in roster.configurations)
    operations, links, external = [], [], []
    for config in configs(seed):
        node = ob.node_id(config.operation, config.index)
        operations.append(RecursiveOperationSpec.from_config(node_id=node,
            selection=registrations[ob.NAMESPACE + "." + config.operation].selection, config_id=config.config_id, config=config,
            obligation_ids=("obligation." + node + ".complete-source-and-evidence",), resource_budget=ob.BUDGET,
            resource_lock_ids=("battery-native-single-worker",) if config.operation == "forecast" else (), maximum_attempts=1))
        for name, (kind, origin) in input_sources(config).items():
            if kind == "EXTERNAL":
                value = values[origin]
                input_id = "external." + node + "." + name
                history = name in {"history", "uncertain-work"}
                external.append(RecursiveExternalInput(input_id, product.artifact.artifact_id if name == "history" else origin,
                    value.object_schema, ob.MEDIA, None, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
                    value.object_fingerprint, "HISTORY" if history else "SOURCE"))
                joined = name == "history" and config.operation == "validate"
                links.append(RecursiveInputLink("edge." + node + "." + name, node, name, external_input_id=input_id,
                    scientific_role="HISTORY" if history else "SOURCE", requirement_id=requirement.requirement_id if joined else None,
                    connection_id=connection.connection_id if joined else None))
            else:
                producer, output = origin.rsplit(".", 1)
                links.append(RecursiveInputLink("edge." + node + "." + name, node, name, producer_node_id=producer,
                    producer_output_id=output, scientific_role="MODEL" if name == "admission" else "OUTCOME"))
    root = ob.development_root(seed, study_id="study." + draft_id)
    campaign = _campaign(root, draft_id)
    return RecursiveStudyDraft(draft_id, ob.QUESTION, campaign, (requirement,), (connection,), (),
        tuple(sorted(operations, key=lambda row: row.node_id)), tuple(sorted(external, key=lambda row: row.input_id)),
        tuple(sorted(links, key=lambda row: row.edge_id)), tuple(sorted(row.node_id for row in operations)),
        development_study=root, contribution_parents=(parent,))


def validate_graph(context, config):
    expected_configs = {ob.node_id(row.operation, row.index): row for row in configs(config)}
    actual_configs = {row.node_id: row.record for row in context.config_inputs}
    if actual_configs != expected_configs:
        raise ValueError("durable graph omits/substitutes its full forecast/assessment/comparison/aggregate census")
    incoming = tuple(link for link in context.links if link.consumer_node_id == context.node_id)
    sources = input_sources(config)
    if len(incoming) != len(sources) or {link.consumer_input_id for link in incoming} != set(sources):
        raise ValueError("durable graph changes exact scientific input census")
    for link in incoming:
        kind, origin = sources[link.consumer_input_id]
        if kind == "EXTERNAL":
            expected_role = "HISTORY" if link.consumer_input_id in {"history", "uncertain-work"} else "SOURCE"
            if link.external_input_id != "external." + context.node_id + "." + link.consumer_input_id or link.scientific_role != expected_role:
                raise ValueError("durable graph changes source/history scientific roles")
        elif (link.producer_node_id + "." + link.producer_output_id != origin
                or link.external_input_id is not None or link.scientific_role != ("MODEL" if link.consumer_input_id == "admission" else "OUTCOME")):
            raise ValueError("durable graph changes its actual ordinary task dependency")
    if len(context.requirements) != 1 or len(context.connections) != 1:
        raise ValueError("durable graph omits its actual adverse-history connection")


@dataclass(frozen=True, slots=True)
class SegmentedScientificMethod(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented-inquiry/scientific-method"
    operation: str
    implementation_sha256: str
    source: ObjectIdentity
    roster: ObjectIdentity
    native_primitive_sha256: str | None
    selected_operand: ObjectIdentity | None
    preparation_protocol: ObjectIdentity | None


@dataclass(frozen=True, slots=True)
class SelectedComparisonOperands(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented-inquiry/selected-comparison-operands"
    left: ObjectIdentity
    right: ObjectIdentity


def scientific_work(draft, operation_id):
    """Same actual request is the same work across editable task/draft labels."""
    selected = tuple(operation for operation in draft.operations if operation.node_id == operation_id and operation.node_id in draft.selected_operation_ids)
    if len(selected) != 1:
        raise ValueError("battery scientific work requires its exact selected ordinary operation")
    operation = selected[0]
    config = decode_canonical_bytes(operation.config_payload.encode(), ob.SegmentedOperationConfig, maximum_bytes=None)
    if (operation.config_identity != ObjectIdentity.from_record(config.config_id, config)
            or operation.node_id != ob.node_id(config.operation, config.index)
            or not any(registration.selection == operation.selection for registration in ob.operation_registrations())
            or draft.development_study != ob.development_root(config, study_id=draft.development_study.study_id)):
        raise ValueError("battery scientific work changes exact code/source/root")
    roster = ob.roster_for(config)
    native = roster.configurations[config.index] if config.operation in {"forecast", "assess", "reuse"} else None
    selected_operand = c.identity(native) if native is not None else None
    if config.operation == "compare":
        pair_ids = roster.comparison_config_pairs[config.index]
        rows = {row.config_id: row for row in roster.configurations}
        pair = SelectedComparisonOperands(*(c.identity(rows[name]) for name in pair_ids))
        selected_operand = ObjectIdentity.from_record("pair.battery-selected-comparison", pair)
    primitive = sha256(ob.forecast_primitive(native)).hexdigest() if native is not None else None
    protocol = protocol_for(config, ob.representative_index(roster, config.index)) if native is not None else None
    method = SegmentedScientificMethod(config.operation, operation.selection.implementation_sha256, c.identity(config.source), config.roster,
        primitive, selected_operand, protocol)
    method_identity = ObjectIdentity.from_record("method." + ob.NAMESPACE + "." + config.operation, method)
    return ScientificInquiryWork(method_identity, config.operands, c.scope(config.source),
        ObjectIdentity.from_record("observation." + ob.NAMESPACE + "." + config.operation, method))
