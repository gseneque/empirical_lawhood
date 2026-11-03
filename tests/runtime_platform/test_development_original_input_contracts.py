# SPDX-License-Identifier: MPL-2.0
"""Pure software contracts; literal parent descriptors confer no actual access.

These controls compile disclosed metadata only. No API, source capture, worker,
native effect, original grant, publication or scientific qualification is used.
"""
from dataclasses import dataclass, replace
from types import SimpleNamespace
from typing import ClassVar

import pytest

from empirical_lawhood.kernel.authority import AuthorityAction, ResourceBudget
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.kernel.status import LifecycleStatus
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.planning.recursive_authoring import RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactProfile, derived_outcome_access
from empirical_lawhood.runtime.candidate_compiler import CandidateDiagnosticCode, _source_diagnostics
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityKind, CapabilityPermission, CapabilityRegistry, input_access_allowed
from empirical_lawhood.runtime.compiler import _config_input
from empirical_lawhood.runtime.input_access import derive_original_parent_input_contracts, validate_planned_input_access
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificInputRole, ScientificStage, development_task_output_custody
from empirical_lawhood.runtime.recursive_compiler import (
    DecodedRecursiveConfigInput, RecursiveConfigInput, RecursivePortContract, compile_recursive_wave,
    configuration_graph_bindings, decode_recursive_config_input, project_recursive_config_inputs,
    validate_recursive_config_input,
)
from empirical_lawhood.runtime.recursive_provider import (
    RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks,
)
from empirical_lawhood.runtime.scientific_graph_preservation import prove_development_graph_parity


@dataclass(frozen=True, slots=True)
class Config(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/original-input-config"
    config_id: str
    value: int
    parents: tuple[ArtifactLineageParent, ...]


BUDGET = ResourceBudget(1, 10_000_000, 0, 30, 1_000_000, 1_000_000)
PERMISSIONS = (CapabilityPermission.READ_DEVELOPMENT, CapabilityPermission.READ_EXTERNAL_ARTIFACTS)
PARENTS = (
    ArtifactLineageParent(ObjectIdentity("original.disclosed.product", "empirical-lawhood/testing/original-product",
        "1.0.0", "a" * 64), VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.EVALUATION_SEALED),
    ArtifactLineageParent(ObjectIdentity("original.disclosed.receipt", "empirical-lawhood/runtime/canonical-task-receipt",
        "1.0.0", "b" * 64), VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE),
)


def _forbidden_runner():
    raise AssertionError("pure contract projection constructed a runner")


def _case(*, protected=True, seen=None):
    """Independent literal design: one prospective software effect, one consumer."""
    def parents(config, all_records):
        if seen is not None:
            seen.append(all_records)
        assert tuple(node for node, _ in all_records) == ("source", "use")
        return config.parents

    declarations = []
    operations = []
    for node in ("source", "use"):
        source = node == "source"
        declaration = RecursiveOperationDeclaration(
            capability_key="testing.original-input." + node, capability_version="1.0.0",
            implementation_id="disclosed-pure-contract", kind=CapabilityKind.SIMULATOR if source else CapabilityKind.TRANSFORM,
            config_record_type=Config, stage=ScientificStage.ACQUIRE if source else ScientificStage.TRANSFORM,
            input_ports=() if source else (RecursivePortContract("operand", Config.SCHEMA, "application/json", 1_000_000),),
            outputs=(OutputTemplate("result", Config.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),),
            permissions=PERMISSIONS, evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
            outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
            resources=BUDGET, conformance_check_ids=("check.disclosed.original-input",),
            runner_factory=_forbidden_runner, record_codecs={Config.SCHEMA: Config},
            scientific_hooks=RecursiveScientificHooks(
                scientific_unit_ids=(lambda config: ("unit.disclosed",)) if source else None,
                native_effect_slot_ids=(lambda config: ("effect.disclosed",)) if source else None),
            execution_properties=RecursiveExecutionProperties(native_effect=source, complete_unit_census=source),
            config_input_parents=parents)
        config = Config("config." + node, 7, PARENTS if protected and source else ())
        operations.append(RecursiveOperationSpec.from_config(node_id=node, selection=declaration.registration().selection,
            config_id=config.config_id, config=config, obligation_ids=("obligation." + node,), resource_budget=BUDGET))
        declarations.append(declaration)
    system = ObjectIdentity("system.disclosed", "empirical-lawhood/testing/system", "1.0.0", "c" * 64)
    claim = ClaimSpec("claim.disclosed", "world.disclosed", "relation.disclosed", "Disclosed software contract",
        "One declared software unit", "unit.disclosed", None, EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, "No scientific promotion",
        ("assumption.disclosed-software",))
    study = DevelopmentStudySpec("study.disclosed", "Can exact original input custody survive lowering?", system,
        claim.world_id, WorldKind.NUMERICAL_SIMULATOR, ("unit.disclosed",), (), (claim,), ())
    campaign = CampaignSpec("campaign.disclosed", study.question, (system.object_id,), (claim.world_id,),
        (claim.claim_id,), BUDGET, ObjectIdentity("policy.disclosed", "empirical-lawhood/testing/policy", "1.0.0", "d" * 64),
        (DecisionRight("right.disclosed", AuthorityAction.READ_ONLY_EXPLORATION, "operator.disclosed", "policy.disclosed", False),),
        (CampaignNode("node.disclosed", CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY, system, (), LifecycleStatus.ACTIVE),),
        ("node.disclosed",), ("node.disclosed",), (), LifecycleStatus.ACTIVE)
    link = RecursiveInputLink("edge.operand", "use", "operand", "source", "result", None, "MODEL")
    draft = RecursiveStudyDraft("draft.disclosed", study.question, campaign, (), (), (), tuple(operations), (),
        (link,), ("source", "use"), development_study=study)
    registrations = tuple(value.registration() for value in declarations)
    registry = CapabilityRegistry("registry.disclosed", tuple(value.manifest() for value in declarations))
    return draft, registrations, registry


def _compile(*, protected=True):
    draft, registrations, registry = _case(protected=protected)
    compiled = compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
        implementation_commit="1" * 40, output_codecs={Config.SCHEMA: Config})
    return compiled, {row.node_id: registrations[index] for index, row in enumerate(draft.operations)}


def test_decoding_does_not_claim_a_finalized_configuration_input_contract():
    draft, registrations, _ = _case()
    decoded = decode_recursive_config_input(draft.operations[0], registrations[0])
    assert type(decoded) is DecodedRecursiveConfigInput and not hasattr(decoded, "input_spec")
    with pytest.raises(ValueError, match="configuration record or bytes"):
        validate_recursive_config_input(operation=draft.operations[0], registration=registrations[0], config_input=decoded)


def test_parent_projection_shares_one_complete_records_tuple_and_preserves_default_pairs():
    seen = []
    draft, registrations, _ = _case(seen=seen)
    decoded = tuple(decode_recursive_config_input(operation, registration)
        for operation, registration in zip(draft.operations, registrations, strict=True))
    rows = project_recursive_config_inputs(decoded, dict(zip(("source", "use"), registrations, strict=True)))
    assert len(seen) == 2 and seen[0] is seen[1]
    assert rows[0].input_parents == PARENTS
    assert (rows[0].input_spec.expected_outcome_access, rows[0].input_spec.expected_visibility_ceiling) == (
        OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.DEVELOPMENT_ONLY)
    assert rows[1].input_parents == ()
    assert rows[1].input_spec.expected_outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE
    with pytest.raises(ValueError, match="complete decoded node census"):
        project_recursive_config_inputs(decoded[:1], dict(zip(("source", "use"), registrations, strict=True)))


@pytest.mark.parametrize("damage", ("list", "duplicate", "reordered", "wrong-type", "wrong-access"))
def test_parent_projection_refuses_malformed_or_ambiguous_parent_custody(damage):
    draft, registrations, _ = _case()
    selected = list(PARENTS) if damage == "list" else (*PARENTS, PARENTS[0]) if damage == "duplicate" else \
        PARENTS[::-1] if damage == "reordered" else (object(),) if damage == "wrong-type" else \
        (replace(PARENTS[0], outcome_access="evaluation-sealed"), PARENTS[1])
    registrations = tuple(replace(value, config_input_parents=lambda config, all_records: selected) for value in registrations)
    rows = tuple(decode_recursive_config_input(operation, registration)
        for operation, registration in zip(draft.operations, registrations, strict=True))
    with pytest.raises((ValueError, TypeError), match="configuration custody"):
        project_recursive_config_inputs(rows, dict(zip(("source", "use"), registrations, strict=True)))


def test_private_config_and_transitive_outputs_keep_custody_while_effects_remain_dev():
    compiled, registrations = _compile()
    plan = compiled.execution_plan
    assert len(compiled.template.graph.edges) == 3
    assert sum(edge.scientific_role is ScientificInputRole.CONFIGURATION for edge in compiled.template.graph.edges) == 2
    for task in plan.tasks:
        assert task.capability.requested_outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE
        assert CapabilityPermission.READ_SEALED_OUTCOMES not in task.capability.required_permissions
        assert not input_access_allowed(task.capability, OutcomeAccess.EVALUATION_SEALED)
        assert development_task_output_custody(task) == (OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.DEVELOPMENT_ONLY)
        assert all((output.outcome_access, output.visibility_ceiling) == (
            OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.DEVELOPMENT_ONLY) for output in task.outputs)
        assert sum(value.input_id == "config" for value in task.external_inputs) == 1
    contracts = derive_original_parent_input_contracts(plan, config_inputs=compiled.config_inputs,
        registrations_for_node=registrations)
    assert tuple((value.task.object_id, value.logical_artifact_id) for value in contracts) == (
        ("source", "config.source"), ("use", plan.tasks[0].outputs[0].logical_artifact_id))
    assert all(value.input_parents == PARENTS for value in contracts)
    with pytest.raises(ValueError, match="lacks read permission"):
        validate_planned_input_access(plan)
    validate_planned_input_access(plan, original_parent_input_contracts=contracts)


def test_default_config_and_output_access_remain_development_visible():
    compiled, registrations = _compile(protected=False)
    assert all(type(row) is RecursiveConfigInput and row.input_parents == () for row in compiled.config_inputs)
    assert all(output.outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE
        and output.visibility_ceiling is VisibilityCeiling.DEVELOPMENT_ONLY
        for task in compiled.execution_plan.tasks for output in task.outputs)
    assert not derive_original_parent_input_contracts(compiled.execution_plan,
        config_inputs=compiled.config_inputs, registrations_for_node=registrations)
    validate_planned_input_access(compiled.execution_plan)


@pytest.mark.parametrize("access", (OutcomeAccess.EVALUATION_REVEALED, OutcomeAccess.PRIVILEGED_TRUTH))
def test_original_ancestry_does_not_supply_exposed_or_privileged_read_permission(access):
    draft, registrations, registry = _case()
    parents = (replace(PARENTS[0], outcome_access=access,
        visibility_ceiling=VisibilityCeiling.OUTCOME_VISIBLE if access is OutcomeAccess.EVALUATION_REVEALED
        else VisibilityCeiling.PRIVILEGED_TRUTH), PARENTS[1])
    registrations = tuple(replace(value, config_input_parents=lambda config, all_records:
        parents if config.parents else ()) for value in registrations)
    with pytest.raises(ValueError, match="lacks read permission"):
        compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
            implementation_commit="1" * 40, output_codecs={Config.SCHEMA: Config})


def test_original_input_route_refuses_a_foreign_task_or_substituted_projected_parents():
    compiled, registrations = _compile()
    contracts = derive_original_parent_input_contracts(compiled.execution_plan,
        config_inputs=compiled.config_inputs, registrations_for_node=registrations)
    foreign = replace(contracts[0], task=replace(contracts[0].task, object_id="task.foreign"))
    with pytest.raises(ValueError, match="exact task or selected input"):
        validate_planned_input_access(compiled.execution_plan, original_parent_input_contracts=(foreign, *contracts[1:]))
    damaged = (replace(compiled.config_inputs[0], input_parents=()), *compiled.config_inputs[1:])
    with pytest.raises(ValueError, match="registered configuration custody"):
        derive_original_parent_input_contracts(compiled.execution_plan,
            config_inputs=damaged, registrations_for_node=registrations)


def test_shared_exact_config_has_one_graph_external_and_two_exact_edges():
    _, registrations, _ = _case(protected=False)
    config = Config("config.shared", 3, ())
    decoded = tuple(DecodedRecursiveConfigInput(node, config.config_id, config.canonical_bytes(), config, Config)
        for node in ("source", "use"))
    rows = project_recursive_config_inputs(decoded, dict(zip(("source", "use"), registrations, strict=True)))
    external, edges = configuration_graph_bindings(rows)
    assert len(external) == 1 and len(edges) == 2
    assert {edge.external_input_id for edge in edges} == {external[0].input_id}
    assert all(edge.consumer_input_id == "config" for edge in edges)
    reference = CapabilityConfigRef(config.config_id, config.SCHEMA, "c" * 64, config.fingerprint(), config.config_id)
    frozen = _config_input(reference, graph_input=external[0])
    assert frozen.expected_outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE
    assert (frozen.expected_size_bytes, frozen.expected_media_type) == (len(config.canonical_bytes()), "application/json")
    ordinary = _config_input(reference)
    assert (ordinary.expected_size_bytes, ordinary.expected_media_type,
        ordinary.expected_outcome_access, ordinary.expected_visibility_ceiling) == (None, None, None, None)


def test_configuration_operands_do_not_satisfy_a_missing_scientific_source():
    compiled, _ = _compile(protected=False)
    diagnostics, accepted = _source_diagnostics(SimpleNamespace(source_materializations=()),
        SimpleNamespace(qualifications=()), compiled.template)
    assert not accepted and any(value.code is CandidateDiagnosticCode.SOURCE_UNRESOLVED for value in diagnostics)


@pytest.mark.parametrize("damage", ("config-port", "config-role", "reserved-id"))
def test_authored_links_cannot_impersonate_a_compiler_owned_configuration(damage):
    draft, registrations, registry = _case(protected=False)
    link = replace(draft.links[0], **({"consumer_input_id": "config"} if damage == "config-port" else
        {"scientific_role": "CONFIGURATION"} if damage == "config-role" else {"edge_id": "compiler.configuration.use"}))
    with pytest.raises(ValueError, match="compiler.*implicit inputs"):
        compile_recursive_wave(draft=replace(draft, links=(link,)), registrations=registrations, registry=registry,
            implementation_commit="1" * 40, output_codecs={Config.SCHEMA: Config})


def test_graph_correspondence_refuses_a_missing_configuration_edge():
    compiled, _ = _compile()
    edges = tuple(edge for edge in compiled.template.graph.edges if edge.consumer_input_id != "config" or edge.consumer_node_id != "use")
    retained_ids = {edge.edge_id for edge in edges}
    coverage = replace(compiled.template.coverage, bindings=tuple(replace(binding,
        contributor_edge_ids=tuple(edge_id for edge_id in binding.contributor_edge_ids if edge_id in retained_ids))
        for binding in compiled.template.coverage.bindings))
    template = replace(compiled.template, graph=replace(compiled.template.graph, edges=edges), coverage=coverage)
    run_plan = replace(compiled.run_plan, template=ObjectIdentity.from_record(template.template_key, template))
    execution_plan = replace(compiled.execution_plan, source_plan=ObjectIdentity.from_record(run_plan.run_plan_id, run_plan))
    with pytest.raises(ValueError, match="configuration census"):
        prove_development_graph_parity(draft=compiled.draft, selection=compiled.selected_scientific_projection,
            template=template, run_plan=run_plan, execution_plan=execution_plan, registry=compiled.registry)


@pytest.mark.parametrize("declared,parents,expected", (
    (OutcomeAccess.DEVELOPMENT_VISIBLE, (OutcomeAccess.EVALUATION_SEALED,), OutcomeAccess.EVALUATION_SEALED),
    (OutcomeAccess.DEVELOPMENT_VISIBLE, (OutcomeAccess.DEVELOPMENT_VISIBLE,), OutcomeAccess.DEVELOPMENT_VISIBLE),
    (OutcomeAccess.DEVELOPMENT_VISIBLE, (OutcomeAccess.EVALUATION_SEALED, OutcomeAccess.DEVELOPMENT_VISIBLE), OutcomeAccess.EVALUATION_SEALED),
    (OutcomeAccess.DEVELOPMENT_VISIBLE, (OutcomeAccess.EVALUATION_SEALED, OutcomeAccess.EVALUATION_REVEALED), OutcomeAccess.EVALUATION_REVEALED),
    (OutcomeAccess.DEVELOPMENT_VISIBLE, (OutcomeAccess.EVALUATION_SEALED, OutcomeAccess.PRIVILEGED_TRUTH), OutcomeAccess.PRIVILEGED_TRUTH),
    (OutcomeAccess.EVALUATION_SEALED, (OutcomeAccess.DEVELOPMENT_VISIBLE,), OutcomeAccess.EVALUATION_SEALED),
))
def test_sealed_original_inheritance_preserves_existing_exposed_and_privileged_restrictions(declared, parents, expected):
    assert derived_outcome_access(declared, *parents) is expected
