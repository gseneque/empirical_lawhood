# SPDX-License-Identifier: MPL-2.0
"""Coherent scientific-claim mutations; software conformance, no native evidence."""

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from empirical_lawhood.adapters.methods.battery_recursive_construction import science
from empirical_lawhood.adapters.methods.battery_recursive_construction.contracts import BatteryOperationConfig
from empirical_lawhood.adapters.methods.battery_recursive_construction.examples import (
    battery_wave_a_draft, battery_wave_b_draft,
)
from empirical_lawhood.adapters.methods.battery_recursive_construction.executable_binding import (
    operation_manifests, operation_registrations, output_codecs, project_battery_assessment,
)
from empirical_lawhood.api.recursive_authoring import author_recursive_wave
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import ConditionRole, ContributionRole
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.test_battery_recursive_construction import _a_products, _b_products, _test_manifest
from tests.test_recursive_public_service import _plane


D = Decimal


def _draft(wave):
    if wave == "A":
        return battery_wave_a_draft()
    _, _, procedure = _a_products()  # Exposed synthetic software operands only.
    return battery_wave_b_draft(_test_manifest(procedure), procedure)


def _compile(draft):
    return compile_recursive_wave(
        draft=draft, registrations=operation_registrations(),
        registry=CapabilityRegistry("test.battery-scope", operation_manifests()),
        implementation_commit="a" * 40, output_codecs=output_codecs(),
    )


def _edit(draft, requirement_id, *, scope=None, requirement=None, connection=None):
    """Edit both the committed config and authored declaration consistently.

    These mutations deliberately preserve IDs/edges and do not merely mismatch
    a checksum. The fixed native assessment cannot assess the new meaning.
    """
    original = next(row for row in draft.requirements if row.requirement_id == requirement_id)
    changed = replace(original, scope=replace(original.scope, **(scope or {})), **(requirement or {}))
    original_connection = next(row for row in draft.connections if row.requirement_id == requirement_id)
    changed_connection = replace(original_connection, **(connection or {}))
    operations = []
    for operation in draft.operations:
        config = decode_canonical_bytes(operation.config_payload.encode(), BatteryOperationConfig,
                                        maximum_bytes=4 * 1024**2)
        if config.requirement is not None and config.requirement.requirement_id == requirement_id:
            config = replace(config, requirement=changed, connection=changed_connection)
            operation = replace(operation, config_payload=config.canonical_bytes().decode())
        operations.append(operation)
    return replace(draft, operations=tuple(operations),
                   requirements=tuple(changed if row == original else row for row in draft.requirements),
                   connections=tuple(changed_connection if row == original_connection else row for row in draft.connections))


@pytest.fixture(autouse=True)
def no_native_contact(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("scientific binding contacted the native simulator")

    for name in ("_runtime", "_phase", "capture_checkpoint", "continue_checkpoint", "source_preflight"):
        monkeypatch.setattr(science, name, forbidden)


@pytest.mark.parametrize("wave,tasks", [("A", 11), ("B", 21)])
def test_default_scientific_scopes_and_design_operand_import_compile(wave, tasks):
    compilation = _compile(_draft(wave))
    assert compilation.proof is not None
    assert len(compilation.execution_plan.tasks) == tasks


SCOPE_MUTATIONS = (
    {"native_units": ("mAh", "C", "mV")},
    {"quantity_ids": ("capacity", "pressure", "temperature"), "native_units": ("A.h", "Pa", "K")},
    {"system_id": "another-system"},
    {"world_id": "physical-cell-world"},
    {"source_id": "another-parameter-source"},
    {"source_config_sha256": "e" * 64},
    {"source_config_sha256": None},
    {"receiver_id": "another-terminal"},
    {"clock_id": "wall-clock-seconds"},
    {"instance_id": "battery-preparation-b"},
    {"population_id": "unqualified-battery-population"},
    {"available_by": D(301)},
    {"valid_from": D(299)},
    {"valid_until": D(601)},
    {"information_cutoff": InformationCutoff("wrong-cutoff", "model-seconds", CausalPhase.PRE_ACTION, D(299))},
    {"uncertainty_contract": ObjectIdentity("unqualified-uncertainty", "empirical-lawhood/test/uncertainty", "1.0.0", "f" * 64)},
)


@pytest.mark.parametrize("mutation", SCOPE_MUTATIONS)
def test_coherently_changed_scope_refuses_before_native_contact(mutation):
    draft = _draft("A")
    requirement = next(row for row in draft.requirements if "early" in row.requirement_id)
    changed = _edit(draft, requirement.requirement_id, scope=mutation)
    with pytest.raises(ValueError, match="scientific scope"):
        _compile(changed)


@pytest.mark.parametrize("field", ["condition", "falsifier", "condition_role", "permitted_roles"])
def test_coherently_changed_scientific_criterion_is_not_a_supported_claim(field):
    draft = _draft("A")
    requirement = draft.requirements[0]
    if field == "condition":
        statement = "Terminal voltage identifies a unique physical electrochemical mechanism."
        changed = _edit(draft, requirement.requirement_id,
                        scope={"coordinate_meaning": statement}, requirement={"condition": statement})
    elif field == "falsifier":
        statement = "Any operational task exit counts as an adequate procedure."
        changed = _edit(draft, requirement.requirement_id,
                        requirement={"falsifier": statement}, connection={"falsifier": statement})
    elif field == "condition_role":
        changed = _edit(draft, requirement.requirement_id, requirement={"condition_role": ConditionRole.PHYSICAL})
    else:
        role = ContributionRole.RETAINED_ANALYSIS_INPUT
        changed = _edit(draft, requirement.requirement_id,
                        requirement={"permitted_roles": (role,)}, connection={"evidence_role": role})
    with pytest.raises(ValueError, match="scientific scope|criterion|falsifier"):
        _compile(changed)


@pytest.mark.parametrize("word", ["early1", "early3", "hold", "late1"])
def test_each_further_requirement_is_checked_even_when_not_in_voltage_config(word):
    draft = _draft("B")
    changed = _edit(draft, f"requirement.battery.b.product-{word}",
                    scope={"native_units": ("mAh", "C", "mV")})
    with pytest.raises(ValueError, match="scientific scope"):
        _compile(changed)


@pytest.mark.parametrize("word", ["early1", "early3", "hold", "late1"])
def test_retained_further_projection_cannot_support_wrong_units(word):
    draft = _draft("B")
    config, _, c1, c2, traces, assessments = _b_products(null=True)
    product = science.assess_voltage(config, c1, c2, traces, assessments)
    requirement = next(row for row in draft.requirements if row.requirement_id == f"requirement.battery.b.product-{word}")
    connection = next(row for row in draft.connections if row.requirement_id == requirement.requirement_id)
    assert project_battery_assessment(product, requirement, connection)
    wrong = replace(requirement, scope=replace(requirement.scope, native_units=("mAh", "C", "mV")))
    with pytest.raises(ValueError, match="scientific scope"):
        project_battery_assessment(product, wrong, connection)


def test_authored_labels_can_change_without_changing_voltage_science():
    draft = _draft("B")
    config, _, c1, c2, traces, assessments = _b_products(null=True)
    product = science.assess_voltage(config, c1, c2, traces, assessments)
    requirement = next(row for row in draft.requirements if row.requirement_id == "requirement.battery.b.product-hold")
    connection = next(row for row in draft.connections if row.requirement_id == requirement.requirement_id)
    requirement = replace(requirement, requirement_id="authored.changed.requirement-label")
    connection = replace(connection, requirement_id=requirement.requirement_id, connection_id="authored.changed.edge-label")
    projected, = project_battery_assessment(product, requirement, connection)
    assert projected.requirement == ObjectIdentity.from_record(requirement.requirement_id, requirement)
    assert projected.connection == ObjectIdentity.from_record(connection.connection_id, connection)


def test_public_authoring_refuses_a_coherent_wrong_scope_before_publication(tmp_path):
    draft = _draft("A")
    changed = _edit(draft, draft.requirements[0].requirement_id, scope={"receiver_id": "another-terminal"})
    selected_root = tmp_path / "selected-root"
    plane = _plane(selected_root)
    destination = selected_root / "bad-scientific-scope"
    with pytest.raises(ValueError, match="scientific scope"):
        author_recursive_wave(draft=changed, project_root=Path(__file__).resolve().parents[1],
                              artifact_writer=plane, output_dir=destination)
    assert not destination.exists()


@pytest.mark.parametrize("field", ["system-id", "system-sha", "system-schema", "source-id", "world", "world-kind", "views", "claim-unit", "claim-relation", "claim-views", "question", "claim-proposition", "claim-estimand", "claim-assumptions", "claim-promotion", "claim-outcome-visible", "claim-derivation", "claim-census"])
def test_actual_scientific_root_attribution_refuses_before_native_contact(field):
    draft = _draft("A")
    root = draft.development_study
    campaign = draft.campaign
    if field == "system-id":
        root = replace(root, system=replace(root.system, object_id="different-system"))
        campaign = replace(campaign, system_ids=("different-system",))
    elif field == "system-sha":
        root = replace(root, system=replace(root.system, object_fingerprint="e" * 64))
    elif field == "system-schema":
        root = replace(root, system=replace(root.system, object_schema="empirical-lawhood/test/another-system"))
    elif field == "source-id":
        root = replace(root, scientific_operands=(replace(root.scientific_operands[0], object_id="another-source-attribution"),))
    elif field == "world":
        root = replace(root, world_id="another-numerical-world",
                       claims=tuple(replace(claim, world_id="another-numerical-world") for claim in root.claims))
        campaign = replace(campaign, world_ids=("another-numerical-world",))
    elif field == "world-kind":
        root = replace(root, world_kind=WorldKind.ANALYTIC_REFERENCE)
    elif field == "views":
        root = replace(root, numerical_view_ids=("coarse", "unacquired-view"))
    elif field == "question":
        root = replace(root, question="Which physical battery population has a uniquely identified mechanism?")
    elif field == "claim-census":
        root = replace(root, claims=tuple(sorted((*root.claims, replace(root.claims[0], claim_id="another-unsupported-claim")),
                                                key=lambda claim: claim.claim_id)))
        campaign = replace(campaign, target_claim_ids=tuple(sorted(claim.claim_id for claim in root.claims)))
    else:
        attributes = {"claim-unit": {"physical_independent_unit_id": "battery-preparation-b"},
                      "claim-relation": {"relation_id": "physical-mechanism-identification"},
                      "claim-views": {"numerical_view_ids": ("unacquired-view",)},
                      "claim-proposition": {"proposition": "This numerical result proves a unique physical mechanism."},
                      "claim-estimand": {"estimand": "Population-wide superiority over every alternative method."},
                      "claim-assumptions": {"assumption_ids": ("fresh-physical-cells",)},
                      "claim-promotion": {"promotion_rule": "Complete tasks establish fresh scientific qualification."},
                      "claim-outcome-visible": {"outcome_access": OutcomeAccess.EVALUATION_REVEALED,
                                                "visibility_ceiling": VisibilityCeiling.OUTCOME_VISIBLE},
                      "claim-derivation": {"derivation_parent_ids": ("unbound-parent",),
                                           "parent_visibility_ceilings": (VisibilityCeiling.DEVELOPMENT_ONLY,)}}[field]
        root = replace(root, claims=tuple(replace(claim, **attributes) for claim in root.claims))
    expected = ("^development registration changes its exact exposed scientific access$" if field == "claim-outcome-visible"
        else "battery scientific root|battery root claim")
    with pytest.raises(ValueError, match=expected):
        _compile(replace(draft, development_study=root, campaign=campaign))


@pytest.mark.parametrize("consumer,port,wrong_producer", [
    ("battery.a.early.reference", "checkpoint", "battery.a.late.checkpoint"),
    ("battery.a.procedure", "assessment-early", "battery.a.late.assess"),
    ("battery.b.early1.reference", "admission", "battery.b.admit-c2"),
    ("battery.b.early1.assess", "reference", "battery.b.late1.reference"),
    ("battery.b.voltage", "early1-full", "battery.b.late1.full"),
    ("battery.b.voltage", "assessment-early1", "battery.b.late1.assess"),
])
def test_same_schema_internal_supplier_cannot_change_scientific_history_or_role(consumer, port, wrong_producer):
    draft = _draft("A" if consumer.startswith("battery.a.") else "B")
    links = tuple(replace(link, producer_node_id=wrong_producer)
                  if link.consumer_node_id == consumer and link.consumer_input_id == port else link
                  for link in draft.links)
    with pytest.raises(ValueError, match="scientific supplier|actual supplier-consumer edge"):
        _compile(replace(draft, links=links))


def test_admission_cannot_coherently_keep_another_selected_parent_digest():
    draft = _draft("B")
    operations = []
    for operation in draft.operations:
        config = decode_canonical_bytes(operation.config_payload.encode(), BatteryOperationConfig,
                                        maximum_bytes=4 * 1024**2)
        if operation.node_id == "battery.b.admit-c1":
            config = replace(config, contribution_sha256="e" * 64)
            operation = replace(operation, config_payload=config.canonical_bytes().decode())
        operations.append(operation)
    with pytest.raises(ValueError, match="exact selected contribution parent"):
        _compile(replace(draft, operations=tuple(operations)))


def test_whole_operation_topology_labels_are_not_battery_science():
    draft = _draft("B")
    renamed = {operation.node_id: f"authored.node-{index:02d}" for index, operation in enumerate(draft.operations)}
    requirements = tuple(replace(requirement, consumer_operation_id=renamed[requirement.consumer_operation_id],
                                 assessment_operation_id=renamed[requirement.assessment_operation_id])
                         for requirement in draft.requirements)
    connections = tuple(replace(connection,
                                supplier_operation_id=renamed.get(connection.supplier_operation_id),
                                assessment_operation_id=renamed[connection.assessment_operation_id])
                        for connection in draft.connections)
    by_requirement = {requirement.requirement_id: requirement for requirement in requirements}
    by_connection = {connection.connection_id: connection for connection in connections}
    operations = []
    for operation in draft.operations:
        config = decode_canonical_bytes(operation.config_payload.encode(), BatteryOperationConfig,
                                        maximum_bytes=4 * 1024**2)
        config = replace(config, config_id=f"{renamed[operation.node_id]}.config",
                         requirement=None if config.requirement is None else by_requirement[config.requirement.requirement_id],
                         connection=None if config.connection is None else by_connection[config.connection.connection_id])
        operations.append(replace(operation, node_id=renamed[operation.node_id], config_id=config.config_id,
                                  config_payload=config.canonical_bytes().decode()))
    links = tuple(replace(link, consumer_node_id=renamed[link.consumer_node_id],
                          producer_node_id=renamed.get(link.producer_node_id)) for link in draft.links)
    suppliers = tuple(replace(proposal, operation_ids=tuple(sorted(renamed[node] for node in proposal.operation_ids)))
                      for proposal in draft.suppliers)
    root = replace(draft.development_study, study_id="authored.renamed-study",
                   claims=(replace(draft.development_study.claims[0], claim_id="authored.renamed-root-claim"),))
    campaign = replace(draft.campaign, target_claim_ids=(root.claims[0].claim_id,),
                       nodes=tuple(replace(node, object_identity=ObjectIdentity.from_record(root.study_id, root))
                                   for node in draft.campaign.nodes))
    changed = replace(draft, draft_id="authored.relabeled-development", requirements=requirements,
                      connections=connections, operations=tuple(sorted(operations, key=lambda row: row.node_id)),
                      links=links, suppliers=suppliers, selected_operation_ids=tuple(sorted(renamed.values())),
                      development_study=root, campaign=campaign)
    assert len(_compile(changed).execution_plan.tasks) == 21


def test_public_authoring_refuses_coherent_wrong_root_before_publication(tmp_path):
    draft = _draft("A")
    wrong = replace(draft, development_study=replace(draft.development_study,
                    system=replace(draft.development_study.system, object_fingerprint="e" * 64)))
    selected_root = tmp_path / "selected-root"
    destination = selected_root / "bad-scientific-root"
    with pytest.raises(ValueError, match="battery scientific root"):
        author_recursive_wave(draft=wrong, project_root=Path(__file__).resolve().parents[1],
                              artifact_writer=_plane(selected_root), output_dir=destination)
    assert not destination.exists()


@pytest.mark.parametrize("requirement_id,wrong_prerequisite", [
    ("requirement.battery.b.early1.instance", "requirement.battery.b.c2-procedure"),
    ("requirement.battery.b.product-early1", "requirement.battery.b.late1.instance"),
])
def test_coherent_prerequisite_label_must_name_actual_admission_or_assessed_word(requirement_id, wrong_prerequisite):
    draft = _edit(_draft("B"), requirement_id,
                  requirement={"further_requirement_ids": (wrong_prerequisite,)})
    draft = replace(draft, suppliers=tuple(
        replace(proposal, prerequisite_requirement_ids=(wrong_prerequisite,))
        if proposal.requirement_id == requirement_id else proposal for proposal in draft.suppliers))
    with pytest.raises(ValueError, match="prerequisite differs"):
        _compile(draft)


def test_coherent_full_consumer_swap_does_not_change_which_instance_was_assessed():
    draft = _draft("B")
    early, late = "requirement.battery.b.early1.instance", "requirement.battery.b.late1.instance"
    draft = _edit(draft, early, requirement={"consumer_operation_id": "battery.b.late1.full"})
    draft = _edit(draft, late, requirement={"consumer_operation_id": "battery.b.early1.full"})
    changed = {early: late, late: early}
    connections = {connection.requirement_id: connection.connection_id for connection in draft.connections}
    links = tuple(replace(link, requirement_id=changed[link.requirement_id],
                          connection_id=connections[changed[link.requirement_id]])
                  if link.requirement_id in changed else link for link in draft.links)
    with pytest.raises(ValueError, match="actual assessed consumer"):
        _compile(replace(draft, links=links))


def test_coherent_admission_consumer_swap_cannot_assess_another_consumers_channels():
    draft = _draft("B")
    c1, c2 = "requirement.battery.b.c1-procedure", "requirement.battery.b.c2-procedure"
    draft = _edit(draft, c1, requirement={"consumer_operation_id": "battery.b.admit-c2"})
    draft = _edit(draft, c2, requirement={"consumer_operation_id": "battery.b.admit-c1"})
    changed = {c1: c2, c2: c1}
    connections = {connection.requirement_id: connection.connection_id for connection in draft.connections}
    links = tuple(replace(link, requirement_id=changed[link.requirement_id],
                          connection_id=connections[changed[link.requirement_id]])
                  if link.requirement_id in changed else link for link in draft.links)
    with pytest.raises(ValueError, match="admission assessor"):
        _compile(replace(draft, links=links))


@pytest.mark.parametrize("consumer,port", [
    ("battery.a.early.reference", "checkpoint"),
    ("battery.a.procedure", "assessment-early"),
    ("battery.b.admit-c1", "procedure"),
    ("battery.b.early1.reference", "admission"),
    ("battery.b.voltage", "hold-full"),
    ("battery.b.voltage", "c1"),
])
def test_selected_role_relabel_cannot_change_actual_causal_or_outcome_use(consumer, port):
    draft = _draft("A" if consumer.startswith("battery.a.") else "B")
    links = tuple(replace(link, scientific_role="ACTION")
                  if link.consumer_node_id == consumer and link.consumer_input_id == port else link
                  for link in draft.links)
    with pytest.raises(ValueError, match="frozen evidence role"):
        _compile(replace(draft, links=links))
