# SPDX-License-Identifier: MPL-2.0
"""Pure joins between RC design bytes, scientific meaning and explicit ports.

The complete configuration is compiler/reader metadata only. Policy workers
retain their truth-free protocol and opaque identities; this validator never
acquires a native view, assesses an oracle or chooses a preparation.
"""

from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Mapping

from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.inquiry.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.recursive_compiler import RecursiveScientificRootPreparationContext

from empirical_lawhood.domains.circuits.rc_prerequisite_chain import operation_contracts as records


_ROLES = {
    records.RCSourceOperationConfig: "source",
    records.RCObservationOperationConfig: "observations",
    records.RCAdmissionOperationConfig: "admit",
    records.RCCommitmentOperationConfig: "commit",
    records.RCDeliveryOperationConfig: "deliver",
    records.RCMeasurementOperationConfig: "measure",
    records.RCSupportOperationConfig: "support",
    records.RCJoinedOperationConfig: "joined",
    records.RCUnitReductionConfig: "reduce",
    records.RCSummaryOperationConfig: "summary",
}
_REQUIREMENT_ROLES = {"commit": "m", "joined": "p", "reduce": "j"}


def _equal(actual, expected, meaning):
    if actual.canonical_bytes() != expected.canonical_bytes():
        raise ValueError(f"RC scientific binding changes its frozen {meaning}")


@dataclass(frozen=True, slots=True, eq=False)
class RCScientificPreparation:
    """Whole-census proof owned by one compiler/reader invocation."""

    batch: RecursiveScientificRootPreparationContext
    node_configs: Mapping[str, CanonicalRecord]


def prepare_rc_scientific_binding(context):
    """Authenticate the complete selected RC science once, without effects.

    The maintained translator supplies the closed scientific semantics. Labels
    may be renamed coherently; roles come from typed records and exact joins.
    """
    from empirical_lawhood.domains.circuits.rc_prerequisite_chain.recursive_translation import DEPENDENCIES, rc_recursive_draft

    if (type(context) is not RecursiveScientificRootPreparationContext
            or not isinstance(context.root, DevelopmentStudySpec)):
        raise ValueError("RC operations require their actual exposed development scientific root")
    rows = {row.node_id: row.record for row in context.config_inputs if type(row.record) in _ROLES}
    if not rows or len(rows) != sum(type(row.record) in _ROLES for row in context.config_inputs):
        raise ValueError("RC scientific preparation requires unique actual selected configurations")
    full = {row.scientific_config.fingerprint(): row.scientific_config for row in rows.values()
            if not isinstance(row, records.RCPolicyOperationConfig)}
    if len(full) != 1:
        raise ValueError("RC selected phases require exactly one actual full scientific configuration")
    scientific = next(iter(full.values()))
    digest = scientific.fingerprint()
    nodes, keys = {}, {}
    assigned_units = set(context.root.assigned_unit_ids)
    for node_id, row in rows.items():
        role = _ROLES[type(row)]
        key = (role, None if role == "summary" else row.unit_id)
        if key in nodes:
            raise ValueError("RC selected phases duplicate an actual scientific role/unit")
        nodes[key], keys[node_id] = node_id, key
        if isinstance(row, records.RCPolicyOperationConfig):
            if row.scientific_config_sha256 != digest:
                raise ValueError("RC policy substitutes its actual scientific source identity")
            _equal(row.protocol, scientific.protocol, "whole policy protocol identity")
        else:
            _equal(row.scientific_config, scientific, "whole scientific source identity")
        if role != "summary" and row.unit_id not in assigned_units:
            raise ValueError("RC phase substitutes its root-assigned scientific unit")

    # This includes the existing pure representability/native-work proof. No
    # default config replaces the actual legitimate original or extended menu.
    reference = rc_recursive_draft(scientific, unit_ids=context.root.assigned_unit_ids,
                                   include_summary=("summary", None) in nodes)
    expected_root = reference.development_study
    claim_ids, claims = {}, []
    claims_by_meaning = {}
    for claim in context.root.claims:
        key = replace(claim, claim_id="claim.rc-normalized").canonical_bytes()
        claims_by_meaning.setdefault(key, []).append(claim)
    for expected in expected_root.claims:
        matches = claims_by_meaning.get(replace(expected, claim_id="claim.rc-normalized").canonical_bytes(), ())
        if len(matches) != 1:
            raise ValueError("RC root claim changes its actual native law, denominator, access or evidence ceiling")
        claim = matches[0]
        claim_ids[expected.claim_id] = claim.claim_id
        claims.append(claim)
    _equal(context.root, replace(expected_root, study_id=context.root.study_id,
        claims=tuple(sorted(claims, key=lambda claim: claim.claim_id))),
        "root system, world, operands, unit census and numerical views")

    # Reference labels belong solely to the maintained translator. The actual
    # authored topology is resolved through the typed role/unit map above.
    reference_keys = {f"rc.u{index:02d}.{role}": (role, unit_id)
        for index, unit_id in enumerate(context.root.assigned_unit_ids, start=1)
        for role in DEPENDENCIES}
    expected_requirements = {reference_keys[requirement.consumer_operation_id]: requirement
                             for requirement in reference.requirements}
    reference_requirements = {item.requirement_id: item for item in reference.requirements}
    reference_connections = {item.requirement_id: item for item in reference.connections}
    connections_by_requirement = {}
    for connection in context.connections:
        connections_by_requirement.setdefault(connection.requirement_id, []).append(connection)
    requirements, connections, labels = {}, {}, {}
    source_units, cutoff_units = {}, {}
    for requirement in context.requirements:
        related = (requirement.consumer_operation_id in rows or requirement.assessment_operation_id in rows
                   or any(connection.supplier_operation_id in rows
                          for connection in connections_by_requirement.get(requirement.requirement_id, ())))
        if not related:
            continue
        key = keys.get(requirement.consumer_operation_id)
        if key not in expected_requirements or key in requirements:
            raise ValueError("RC requirement has an unsupported or duplicate consumer role/unit")
        expected = expected_requirements[key]
        assessor_key = reference_keys[expected.assessment_operation_id]
        if assessor_key not in nodes:
            raise ValueError("RC requirement lacks its exact same-unit assessor phase")
        scope = requirement.scope
        if scope is None or scope.information_cutoff is None:
            raise ValueError("RC requirement lacks its frozen source/clock/cutoff scope")
        label = (scope.source_id, scope.information_cutoff.cutoff_id)
        unit_id = key[1]
        if unit_id in labels and labels[unit_id] != label:
            raise ValueError("RC M/P/J substitute their same-unit source or cutoff declaration")
        if (source_units.get(label[0], unit_id) != unit_id
                or cutoff_units.get(label[1], unit_id) != unit_id):
            raise ValueError("RC independent units alias a source or cutoff declaration")
        labels[unit_id] = label
        source_units[label[0]], cutoff_units[label[1]] = unit_id, unit_id
        expected_scope = replace(expected.scope, source_id=scope.source_id,
            information_cutoff=replace(expected.scope.information_cutoff, cutoff_id=scope.information_cutoff.cutoff_id))
        _equal(requirement, replace(expected, requirement_id=requirement.requirement_id,
            consumer_operation_id=requirement.consumer_operation_id, purpose=requirement.purpose,
            scope=expected_scope, assessment_operation_id=nodes[assessor_key],
            further_requirement_ids=requirement.further_requirement_ids), "requirement scope, criterion, falsifier and roles")
        linked = connections_by_requirement.get(requirement.requirement_id, ())
        if len(linked) != 1:
            raise ValueError("RC requirement lacks its one actual assessed internal supply")
        connection = linked[0]
        reference_connection = reference_connections[expected.requirement_id]
        supplier_key = reference_keys[reference_connection.supplier_operation_id]
        if supplier_key not in nodes:
            raise ValueError("RC connection lacks its exact same-unit supplier phase")
        _equal(connection, replace(reference_connection, connection_id=connection.connection_id,
            requirement_id=requirement.requirement_id, supplier_operation_id=nodes[supplier_key],
            assessment_operation_id=nodes[assessor_key], claim_id=claim_ids[reference_connection.claim_id]),
            "connection source, consumer, assessor, claim and contribution role")
        requirements[key], connections[key] = requirement, connection

    links_by_node = {}
    for link in context.links:
        links_by_node.setdefault(link.consumer_node_id, {}).setdefault(link.consumer_input_id, []).append(link)
    for key, node_id in nodes.items():
        role, unit_id = key
        if role in _REQUIREMENT_ROLES and key not in requirements:
            raise ValueError("RC consumer omits its mandatory frozen scientific requirement")
        if key in requirements:
            expected = expected_requirements[key]
            prerequisite_keys = [reference_keys[reference_requirements[item].consumer_operation_id]
                                 for item in expected.further_requirement_ids]
            if any(item not in requirements for item in prerequisite_keys):
                raise ValueError("RC requirement omits its actual same-unit prerequisites")
            prerequisites = tuple(sorted(requirements[item].requirement_id for item in prerequisite_keys))
            if requirements[key].further_requirement_ids != prerequisites:
                raise ValueError("RC requirement substitutes its M/P/J prerequisite closure")
        incoming = links_by_node.get(node_id, {})
        expected_ports = (tuple((f"units.{unit}", "reduce", "unit") for unit in context.root.assigned_unit_ids)
                          if role == "summary" else DEPENDENCIES[role])
        if sum(map(len, incoming.values())) != len(expected_ports):
            raise ValueError("RC phase changes its complete scientific input census")
        for port, supplier_role, output in expected_ports:
            matches = incoming.get(port, ())
            supplier_unit = port.removeprefix("units.") if role == "summary" else unit_id
            supplier = nodes.get((supplier_role, supplier_unit))
            if len(matches) != 1 or supplier is None:
                raise ValueError("RC phase lacks its exact same-unit typed dependency")
            link = matches[0]
            annotated = key in requirements and port == connections[key].consumer_input_id
            if (link.producer_node_id != supplier or link.producer_output_id != output
                or link.external_input_id is not None
                or link.scientific_role != ("ACTION" if supplier_role == "commit" else "HISTORY")
                or link.requirement_id != (requirements[key].requirement_id if annotated else None)
                or link.connection_id != (connections[key].connection_id if annotated else None)):
                raise ValueError("RC scientific dependency substitutes source/unit, phase role or assessed connection")
    return RCScientificPreparation(context, MappingProxyType(rows))


def validate_rc_scientific_binding(config, context) -> None:
    """Use only the exact preparation of this selected immutable invocation."""
    from empirical_lawhood.domains.circuits.rc_prerequisite_chain.operation_bindings import PHASES

    prepared = context.scientific_preparation
    if type(prepared) is not RCScientificPreparation or type(config) not in _ROLES:
        raise ValueError("RC scientific binding requires its invocation-local preparation")
    batch = prepared.batch
    if (prepared.node_configs.get(context.node_id) is not config or context.root is not batch.root
            or context.config_inputs is not batch.config_inputs or context.links is not batch.links
            or context.requirements is not batch.requirements or context.connections is not batch.connections
            or context.external_inputs is not batch.external_inputs
            or context.qualifications is not batch.qualifications
            or context.known_design_inputs is not batch.known_design_inputs):
        raise ValueError("RC scientific binding changes its exact prepared invocation")
    stage = next(row[6] for row in PHASES if row[1] is type(config))
    if (context.stage is not stage or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise ValueError("RC scientific phase cannot change its registered stage, access or visibility")
