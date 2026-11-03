# SPDX-License-Identifier: MPL-2.0
"""Nine ordinary tasks, with source/history/effect identities kept distinct."""

from dataclasses import dataclass, replace
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c
from empirical_lawhood.adapters.methods.battery_refined_inquiry.recursive_translation import _campaign
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry_policy import ScientificInquiryWork
from empirical_lawhood.kernel.recursive_requirements import ConditionRole, ContributionRole, ScientificConnectionSpec, ScientificRequirementSpec
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from . import operation_bindings as ob
from .contracts import identity


def configs(config):
    return tuple(sorted((replace(config, operation=operation, index=index, config_id="config." + ob.node_id(operation, index))
        for operation, index in (("summarize", None), *((operation, i) for operation in ("observe", "assess") for i in range(3)),
            *(("pair", i) for i in range(2)))), key=lambda row: row.config_id))


def external_values(config):
    observation, declaration = config.observation, config.declarations[0]
    rows = (observation, config.source, config.provenance, config.storage, config.control,
        observation.original_selection, observation.uncertain_work, declaration.resources,
        *config.protocols, *config.declarations, *observation.configurations,
        *(row.method for row in observation.configurations), observation.configurations[0].preparation,
        observation.configurations[0].preparation_assessment)
    by_fingerprint = {row.fingerprint(): row for row in rows}
    values = {operand.object_id: by_fingerprint.get(operand.object_fingerprint) for operand in config.operands}
    values[config.history_artifact_id] = None
    return values


def input_sources(config):
    declaration = config.declarations[config.index if config.operation == "observe" else 0]
    observation = config.observation
    result = {"history": ("EXTERNAL", config.history_artifact_id), "observation": ("EXTERNAL", observation.observation_id),
        "provenance": ("EXTERNAL", config.provenance.identity.object_id), "source": ("EXTERNAL", config.source.source_id),
        "storage": ("EXTERNAL", config.storage.storage_root_id)}
    if config.operation == "observe":
        native = observation.configurations[config.index]
        result.update((name, ("EXTERNAL", operand.object_id)) for name, operand in (
            ("native-config", identity(native, "config_id")), ("protocol", identity(config.protocols[config.index], "protocol_id")),
            ("entry", identity(declaration, "declaration_id")), ("abi-import-report", declaration.abi_import_report),
            ("resource-source", declaration.resources.evidence), ("resources", identity(declaration.resources, "snapshot_id")),
            ("original-roster", identity(observation.original_selection, "roster_id")), ("uncertain-work", identity(observation.uncertain_work, "record_id")),
            ("method", identity(native.method, "method_id")), ("preparation", identity(native.preparation, "preparation_id")),
            ("source-assessment", identity(native.preparation_assessment, "assessment_id"))))
    elif config.operation == "assess":
        result.update((name, ("DEPENDENCY", ob.node_id("observe", config.index) + "." + name)) for name in ("window", "segments"))
    elif config.operation == "pair":
        result["control"] = ("EXTERNAL", config.control.control_id)
        for side, i in (("left", config.index), ("right", config.index + 1)):
            result.update((side + "-" + name, ("DEPENDENCY", ob.node_id("observe", i) + "." + name)) for name in ("window", "segments"))
    else:
        result.update(("method-" + str(i), ("DEPENDENCY", ob.node_id("assess", i) + ".assessment")) for i in range(3))
        result.update(("pair-" + str(i), ("DEPENDENCY", ob.node_id("pair", i) + ".comparison")) for i in range(2))
    return result


def requirement_pair(config, parent, product):
    gate = ob.node_id("observe", 0)
    requirement = ScientificRequirementSpec("requirement." + ob.NAMESPACE + ".actual-adverse-history", gate,
        ConditionRole.EVIDENTIAL, ob.QUESTION,
        "Original negative supplier and UNKNOWN diagnostic custody remain authentic adverse history. New source-derived initial-window operands cannot reconstruct or clear old subwork.",
        c.scope(config.source), gate, "Changed actual contact/source, invented old counts, omitted adverse work or full-forecast promotion refuses.",
        (ContributionRole.RETAINED_ANALYSIS_INPUT,))
    connection = ScientificConnectionSpec("connection." + ob.NAMESPACE + ".actual-adverse-history", requirement.requirement_id,
        None, None, "history", gate, "claim." + ob.NAMESPACE, ContributionRole.RETAINED_ANALYSIS_INPUT,
        requirement.falsifier, identity(parent, "contribution_id"), product.product_id, "external." + gate + ".history")
    return requirement, connection


def observation_draft(observation, protocols, declarations, provenance, storage, control, *, parent,
                      selected_storage_contract, draft_id="draft.battery-observation-inquiry.initial-window"):
    """Pure authoring; actual selected root must be supplied by outer composition."""
    source = observation.original_selection.source
    products = tuple(product for product in parent.products if product.record == source.diagnostic
        and product.role is ContributionRole.RETAINED_ANALYSIS_INPUT)
    if len(products) != 1:
        raise ValueError("observation graph requires its exact authenticated portable adverse history product")
    product = products[0]
    seed = ob.ObservationOperationConfig("config." + ob.node_id("summarize"), "summarize", None,
        observation, protocols, declarations, storage, provenance, control, product.artifact.artifact_id)
    ob.require_selected_storage(seed, selected_storage_contract)
    requirement, connection = requirement_pair(seed, parent, product)
    values = {row.object_id: row for row in seed.operands}
    values[product.artifact.artifact_id] = source.diagnostic
    registrations = {row.selection.capability_key: row for row in ob.operation_registrations()}
    operations, links, external = [], [], []
    for config in configs(seed):
        node = ob.node_id(config.operation, config.index)
        operations.append(RecursiveOperationSpec.from_config(node_id=node,
            selection=registrations[ob.NAMESPACE + "." + config.operation].selection, config_id=config.config_id, config=config,
            obligation_ids=("obligation." + node + ".complete-original-observation",), resource_budget=ob.BUDGET,
            resource_lock_ids=("battery-native-single-worker",) if config.operation == "observe" else (), maximum_attempts=1))
        for name, (kind, origin) in input_sources(config).items():
            if kind == "EXTERNAL":
                operand = values[origin]
                input_id = "external." + node + "." + name
                history = name in {"history", "uncertain-work"}
                external.append(RecursiveExternalInput(input_id, origin, operand.object_schema, ob.media_for(name), None,
                    OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, operand.object_fingerprint,
                    "HISTORY" if history else "SOURCE"))
                joined = name == "history" and config.operation == "observe" and config.index == 0
                links.append(RecursiveInputLink("edge." + node + "." + name, node, name, external_input_id=input_id,
                    scientific_role="HISTORY" if history else "SOURCE", requirement_id=requirement.requirement_id if joined else None,
                    connection_id=connection.connection_id if joined else None))
            else:
                producer, output = origin.rsplit(".", 1)
                links.append(RecursiveInputLink("edge." + node + "." + name, node, name, producer_node_id=producer,
                    producer_output_id=output, scientific_role="OUTCOME"))
    root = ob.development_root(seed, study_id="study." + draft_id)
    return RecursiveStudyDraft(draft_id, ob.QUESTION, _campaign(root, draft_id), (requirement,), (connection,), (),
        tuple(sorted(operations, key=lambda row: row.node_id)), tuple(sorted(external, key=lambda row: row.input_id)),
        tuple(sorted(links, key=lambda row: row.edge_id)), tuple(sorted(row.node_id for row in operations)),
        development_study=root, contribution_parents=(parent,))


def validate_graph(context, config):
    expected = {ob.node_id(row.operation, row.index): row for row in configs(config)}
    if {row.node_id: row.record for row in context.config_inputs} != expected:
        raise ValueError("observation graph omits/substitutes complete three-method/two-pair census")
    sources = input_sources(config)
    incoming = tuple(link for link in context.links if link.consumer_node_id == context.node_id)
    if len(incoming) != len(sources) or {row.consumer_input_id for row in incoming} != set(sources):
        raise ValueError("observation graph changes its exact scientific input census")
    for link in incoming:
        kind, origin = sources[link.consumer_input_id]
        if kind == "EXTERNAL":
            history = link.consumer_input_id in {"history", "uncertain-work"}
            if (link.external_input_id != "external." + context.node_id + "." + link.consumer_input_id
                    or link.scientific_role != ("HISTORY" if history else "SOURCE")):
                raise ValueError("observation graph changes actual source/history roles")
        elif (link.producer_node_id + "." + link.producer_output_id != origin
                or link.external_input_id is not None or link.scientific_role != "OUTCOME"):
            raise ValueError("observation graph changes actual producing dependency")
    if len(context.requirements) != 1 or len(context.connections) != 1:
        raise ValueError("observation graph omits its authentic adverse-history connection")


@dataclass(frozen=True, slots=True)
class ObservationScientificMethod(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-observation-inquiry/scientific-method"
    operation: str
    implementation_sha256: str
    observation: ObjectIdentity
    native_primitive_sha256: str | None
    selected_operands: tuple[ObjectIdentity, ...]


def scientific_work(draft, operation_id):
    rows = tuple(row for row in draft.operations if row.node_id == operation_id and row.node_id in draft.selected_operation_ids)
    if len(rows) != 1:
        raise ValueError("observation scientific work requires its actual selected ordinary operation")
    row = rows[0]
    config = decode_canonical_bytes(row.config_payload.encode(), ob.ObservationOperationConfig, maximum_bytes=None)
    if (row.config_identity != identity(config, "config_id") or row.node_id != ob.node_id(config.operation, config.index)
            or not any(registration.selection == row.selection for registration in ob.operation_registrations())
            or draft.development_study != ob.development_root(config, study_id=draft.development_study.study_id)):
        raise ValueError("observation scientific work changes actual source/root/code")
    indices = (config.index,) if config.operation in {"observe", "assess"} else (config.index, config.index + 1) if config.operation == "pair" else (0, 1, 2)
    method = ObservationScientificMethod(config.operation, row.selection.implementation_sha256, identity(config.observation, "observation_id"),
        sha256(ob.primitive(config, config.index)).hexdigest() if config.operation in {"observe", "assess"} else None,
        tuple(identity(config.observation.configurations[i], "config_id") for i in indices))
    return ScientificInquiryWork(ObjectIdentity.from_record("method." + ob.NAMESPACE + "." + config.operation, method), config.operands, c.scope(config.source),
        ObjectIdentity.from_record("observation." + ob.NAMESPACE + "." + config.operation, method))
