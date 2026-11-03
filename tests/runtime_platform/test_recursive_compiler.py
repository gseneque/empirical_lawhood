# SPDX-License-Identifier: MPL-2.0
"""Synthetic shared compiler conformance; these checks do not qualify science."""
from dataclasses import dataclass, replace
from pathlib import Path
from typing import ClassVar

import pytest

from empirical_lawhood.api import load_authoring
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import (
    AssessmentDisposition, AssessmentPhase, ConditionRole, ContributionRole,
    DevelopmentStudySpec, RequirementSupplyAssessment, ScientificConditionScope,
    ScientificConnectionSpec, ScientificRequirementSpec,
)
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.planning.recursive_authoring import (
    RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft, SupplierProposal,
)
from empirical_lawhood.planning.study_authoring import CapabilitySelection
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityManifest, CapabilityPermission, CapabilityRegistry
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan, DevelopmentRunPlan, OutputTemplate, PlanLane, ScientificInputRole, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursiveOperationRegistration, RecursivePortContract, compile_recursive_wave
from empirical_lawhood.runtime.scientific_graph_preservation import prove_development_graph_parity


@dataclass(frozen=True, slots=True)
class Config(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/recursive-config"
    config_id: str
    scalar: int


class SourceConfig(Config):
    SCHEMA = "empirical-lawhood/testing/recursive-source-config"


class UseConfig(Config):
    SCHEMA = "empirical-lawhood/testing/recursive-use-config"


BUDGET = ResourceBudget(1, 1_000_000, 0, 10, 10_000, 10_000)
PERMISSIONS = (CapabilityPermission.READ_DEVELOPMENT, CapabilityPermission.READ_EXTERNAL_ARTIFACTS)


def fixture():
    package = load_authoring(Path(__file__).resolve().parents[1] / "fixtures/reference-campaign.json")
    system = package.system
    claim = replace(package.frozen_proposal.proposal.candidate_experiment.claims[0],
                    requested_rung=None, evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
                    outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
                    visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY)
    study = DevelopmentStudySpec("study.generic", "Can an assessed operand satisfy a downstream condition?",
             ObjectIdentity.from_record(system.system_id, system), system.world.world_id, system.world.kind,
             ("unit.one",), ("view.one",), (claim,), ())
    campaign = replace(package.campaign, system_ids=(system.system_id,), world_ids=(system.world.world_id,),
                       target_claim_ids=(claim.claim_id,))
    output = OutputTemplate("result", Config.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json")
    registrations = []
    manifests = []
    operations = []
    for node, ports in (("source", ()), ("use", (RecursivePortContract("operand", Config.SCHEMA, "application/json", 10_000),))):
        config_type = SourceConfig if node == "source" else UseConfig
        key = f"generic.{node}"
        selection = CapabilitySelection(key, "1.0.0", "a" * 64)
        registrations.append(RecursiveOperationRegistration(selection, ScientificStage.TRANSFORM, config_type, ports,
                             (output,), PERMISSIONS, OutcomeAccess.DEVELOPMENT_VISIBLE,
                             VisibilityCeiling.DEVELOPMENT_ONLY, BUDGET))
        manifests.append(CapabilityManifest(key, "1.0.0", CapabilityKind.TRANSFORM, config_type.SCHEMA, "b" * 64,
                         tuple(sorted({Config.SCHEMA, config_type.SCHEMA})), (Config.SCHEMA,), PERMISSIONS, EvidenceCeiling.NON_PROMOTABLE,
                         OutcomeAccess.DEVELOPMENT_VISIBLE, BUDGET, True, False, "python", "python", False,
                         False, False, ("check.generic",), "a" * 64))
        operations.append(RecursiveOperationSpec.from_config(node_id=node, selection=selection, config_id=f"config.{node}",
                          config=config_type(f"config.{node}", 3), obligation_ids=(f"obligation.{node}",), resource_budget=BUDGET))
    scope = ScientificConditionScope(system.system_id, system.world.world_id, "source.generic", ("quantity.voltage",),
                                    ("V",), "receiver.generic", "clock.generic", "same receiver and clock")
    requirement = ScientificRequirementSpec("requirement.operand", "use", ConditionRole.INFORMATIONAL,
                  "Use a retained assessed operand", "operand exists with the declared scope", scope, "use",
                  "changed source or clock fails", (ContributionRole.INSTANCE_PRODUCT,))
    connection = ScientificConnectionSpec("connection.operand", requirement.requirement_id, "source", "result",
                 "operand", "use", claim.claim_id, ContributionRole.INSTANCE_PRODUCT, "changed source fails")
    link = RecursiveInputLink("edge.operand", "use", "operand", "source", "result", None, "HISTORY",
                              requirement.requirement_id, connection.connection_id)
    unavailable = SupplierProposal("alternative.unavailable", requirement.requirement_id, (), (), False,
                                  "A later substrate is unavailable", ("NO_REGISTERED_SUPPLIER",))
    draft = RecursiveStudyDraft("draft.generic", study.question, campaign, (requirement,), (connection,),
            (unavailable,), tuple(operations), (), (link,), ("source", "use"), development_study=study)
    registry = CapabilityRegistry("registry.generic", tuple(manifests))
    return draft, tuple(registrations), registry


def compile_fixture(**changes):
    draft, registrations, registry = fixture()
    draft = replace(draft, **changes)
    return compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
                implementation_commit="1" * 40, output_codecs={Config.SCHEMA: Config})


@pytest.mark.parametrize("output_limit", [None, 4096, 128 * 1024**2])
def test_closed_matrix_array_port_derives_scientific_bound_without_operational_ceiling(output_limit):
    from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
    from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS

    draft, registrations, registry = fixture()
    source_budget = replace(BUDGET, output_bytes=output_limit)
    unlimited_budget = replace(BUDGET, output_bytes=None)
    draft = replace(draft, operations=(replace(draft.operations[0], resource_budget=source_budget),
                                      replace(draft.operations[1], resource_budget=unlimited_budget)))
    source = replace(registrations[0], resource_ceiling=unlimited_budget, storage_codecs=MATRIX_STORAGE_CODECS,
        outputs=(OutputTemplate("result", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ,
                                "application/x-npz", ".npz"),))
    consumer = replace(registrations[1], resource_ceiling=unlimited_budget, storage_codecs=MATRIX_STORAGE_CODECS,
        input_ports=(RecursivePortContract("operand", MATRIX_ARRAY_SCHEMA, "application/x-npz",
                                          MAXIMUM_MATRIX_ARRAY_BYTES),))
    registry = replace(registry, capabilities=(
        replace(registry.capabilities[0], resource_ceiling=unlimited_budget,
                output_schema_ids=(MATRIX_ARRAY_SCHEMA,)),
        replace(registry.capabilities[1], resource_ceiling=unlimited_budget,
                input_schema_ids=tuple(sorted({MATRIX_ARRAY_SCHEMA, UseConfig.SCHEMA}))),
    ))
    compiled = compile_recursive_wave(draft=draft, registrations=(source, consumer), registry=registry,
        implementation_commit="1" * 40, output_codecs={Config.SCHEMA: Config})
    expected = MAXIMUM_MATRIX_ARRAY_BYTES if output_limit is None else min(output_limit, MAXIMUM_MATRIX_ARRAY_BYTES)
    operand, = (edge for edge in compiled.template.graph.edges
        if edge.consumer_node_id == "use" and edge.consumer_input_id == "operand")
    assert operand.scientific_role is ScientificInputRole.HISTORY
    assert operand.maximum_size_bytes == expected
    assert compiled.template.protocol.steps[0].resource_budget.output_bytes == output_limit
    consumer = next(task for task in compiled.execution_plan.tasks if task.task_id == "use")
    selected, = (edge for edge in consumer.scientific_inputs if edge.consumer_input_id == "operand")
    assert selected.scientific_role is ScientificInputRole.HISTORY
    assert selected.maximum_size_bytes == expected


@pytest.mark.parametrize("changed", ["canonical", "schema", "media", "profile", "smaller-port"])
def test_closed_array_bound_does_not_exempt_other_transports_or_tighter_consumer(changed):
    from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
    from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS

    draft, registrations, registry = fixture()
    unlimited_budget = replace(BUDGET, output_bytes=None)
    draft = replace(draft, operations=tuple(replace(value, resource_budget=unlimited_budget)
                                            for value in draft.operations))
    schema = Config.SCHEMA if changed in ("canonical", "schema") else MATRIX_ARRAY_SCHEMA
    media = "application/json" if changed in ("canonical", "media") else "application/x-npz"
    profile = ArtifactProfile.CANONICAL_JSON if changed == "canonical" else (
        ArtifactProfile.NUMPY_NO_PICKLE if changed == "profile" else ArtifactProfile.MATRIX_ARRAY_NPZ)
    source = replace(registrations[0], resource_ceiling=unlimited_budget, storage_codecs=MATRIX_STORAGE_CODECS,
        outputs=(OutputTemplate("result", schema, profile, media, ".npz"),))
    consumer = replace(registrations[1], resource_ceiling=unlimited_budget, storage_codecs=MATRIX_STORAGE_CODECS,
        input_ports=(RecursivePortContract("operand", schema, media,
            MAXIMUM_MATRIX_ARRAY_BYTES - 1 if changed == "smaller-port" else MAXIMUM_MATRIX_ARRAY_BYTES),))
    registry = replace(registry, capabilities=(
        replace(registry.capabilities[0], resource_ceiling=unlimited_budget, output_schema_ids=(schema,)),
        replace(registry.capabilities[1], resource_ceiling=unlimited_budget,
                input_schema_ids=tuple(sorted({schema, UseConfig.SCHEMA}))),
    ))
    with pytest.raises(ValueError, match="incompatible with registered port|registered storage codec"):
        compile_recursive_wave(draft=draft, registrations=(source, consumer), registry=registry,
                               implementation_commit="1" * 40)


@pytest.mark.parametrize('names', [('result', 'result-secondary'), ('result', 'result.0')])
def test_output_names_incompatible_with_legacy_receipt_order_are_refused_before_effects(names):
    draft, registrations, registry = fixture()
    values = tuple(replace(registration,
                   outputs=tuple(replace(registration.outputs[0], output_id=name) for name in names))
                   if registration.selection.capability_key == 'generic.use' else registration
                   for registration in registrations)
    with pytest.raises(ValueError, match='receipt materialization order'):
        compile_recursive_wave(draft=draft, registrations=values, registry=registry,
                implementation_commit='1' * 40, output_codecs={Config.SCHEMA: Config})


@pytest.mark.parametrize('names', [('primary', 'secondary'), ('result', 'result.z')])
def test_multiple_outputs_keep_complete_census_and_actual_materialization_order(tmp_path, names):
    from empirical_lawhood.runtime.artifacts import ArtifactWriteRequest
    from tests.test_recursive_public_service import _plane

    draft, registrations, registry = fixture()
    values = tuple(replace(registration,
                   outputs=tuple(replace(registration.outputs[0], output_id=name) for name in names))
                   if registration.selection.capability_key == 'generic.use' else registration
                   for registration in registrations)
    compiled = compile_recursive_wave(draft=draft, registrations=values, registry=registry,
                 implementation_commit='1' * 40, output_codecs={Config.SCHEMA: Config})
    task = next(task for task in compiled.execution_plan.tasks if task.task_id == 'use')
    assert tuple(output.output_id for output in task.outputs) == tuple('use.' + name for name in names)
    plane = _plane(tmp_path / 'selected-output-order')
    artifacts = tuple(plane.write(ArtifactWriteRequest(output.logical_artifact_id, output.relative_path,
        Config.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', compiled.run_plan.run_plan_id,
        'runs/' + compiled.run_plan.run_plan_id, Config('product.' + names[index], index).canonical_bytes(),
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
        for index, output in enumerate(task.outputs))
    logical = tuple(item.logical.logical_artifact_id for item in artifacts)
    physical = tuple(item.materialization.materialization_id for item in artifacts)
    assert logical == tuple(sorted(logical)) and physical == tuple(sorted(physical))
    assert tuple(item.materialization.logical_artifact_id for item in artifacts) == logical


def test_closed_wave_has_real_authority_free_root_and_exact_scientific_edges():
    compiled = compile_fixture()
    assert isinstance(compiled.run_plan, DevelopmentRunPlan)
    assert isinstance(compiled.execution_plan, DevelopmentExecutionPlan)
    assert compiled.execution_plan.lane is PlanLane.DEVELOPMENT
    assert not hasattr(compiled.run_plan, "authorization")
    assert compiled.proof.node_count == 2 and compiled.proof.requirement_count == 1
    assert compiled.draft.suppliers[0].unavailable_reason_codes
    task = next(task for task in compiled.execution_plan.tasks if task.task_id == "use")
    operand, = (edge for edge in task.scientific_inputs
        if edge.scientific_role is ScientificInputRole.HISTORY and edge.consumer_input_id == "operand")
    assert operand.producer_output_id == "source.result"
    assert operand.operational_logical_artifact_id == "artifact.recursive.draft.generic.source.result"
    configuration, = (edge for edge in task.scientific_inputs
        if edge.scientific_role is ScientificInputRole.CONFIGURATION)
    assert configuration.consumer_input_id == "config"
    assert configuration.external_input_id is not None and configuration.producer_task_id is None
    assert len(task.scientific_inputs) == 2
    assert task.external_inputs[0].input_id == "config"
    assert task.external_inputs[0].expected_size_bytes == len(compiled.config_inputs[1].payload)
    assert decode_canonical_bytes(compiled.run_plan.canonical_bytes(), DevelopmentRunPlan,
                                 maximum_bytes=1_000_000) == compiled.run_plan
    assert decode_canonical_bytes(compiled.execution_plan.canonical_bytes(), DevelopmentExecutionPlan,
                                 maximum_bytes=1_000_000) == compiled.execution_plan


@pytest.mark.parametrize('changed_digest', (False, True))
def test_scientific_validators_receive_selected_external_contracts_at_compile_and_assessment(changed_digest):
    from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput
    from empirical_lawhood.runtime.recursive_compiler import project_recursive_assessments

    draft, registrations, registry = fixture()
    source = Config('original.source', 7)
    original = RecursiveExternalInput('external.origin', source.config_id, source.SCHEMA,
        'application/json', len(source.canonical_bytes()), OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY, source.fingerprint(), 'SOURCE')
    selected = replace(original, expected_content_sha256='b' * 64) if changed_digest else original
    unselected = replace(original, input_id='external.unselected', logical_artifact_id='unselected.source')
    draft = replace(draft, external_inputs=(selected, unselected),
        links=tuple(sorted((*draft.links, RecursiveInputLink('edge.origin', 'source', 'origin',
            external_input_id=selected.input_id, scientific_role='SOURCE')), key=lambda row: row.edge_id)))
    observed = []

    def validate(config, context):
        observed.append(context.external_inputs)
        if context.external_inputs != (original,):
            raise ValueError('scientific source identity was substituted')

    registrations = (replace(registrations[0],
        input_ports=(RecursivePortContract('origin', Config.SCHEMA, 'application/json', 10_000),),
        scientific_root_validator=validate), registrations[1])
    calls = (
        lambda: compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
            implementation_commit='1' * 40, output_codecs={Config.SCHEMA: Config}),
        lambda: project_recursive_assessments(draft=draft, registrations=registrations, outputs={}),
    )
    for call in calls:
        if changed_digest:
            with pytest.raises(ValueError, match='scientific source identity was substituted'):
                call()
        else:
            call()
    assert observed == [(selected,), (selected,)]


def test_unselected_unknown_alternative_is_kept_but_cannot_fill_missing_selected_input():
    draft, _, _ = fixture()
    with pytest.raises(ValueError, match="unselected supplier"):
        compile_fixture(selected_operation_ids=("use",))
    with pytest.raises(ValueError, match="incomplete port census"):
        compile_fixture(requirements=(), connections=(), links=())
    assert draft.suppliers[0].selected is False


@pytest.mark.parametrize("change", [
    lambda draft: replace(draft, requirements=(replace(draft.requirements[0], scope=None),)),
    lambda draft: replace(draft, connections=(replace(draft.connections[0], consumer_input_id="wrong"),)),
    lambda draft: replace(draft, suppliers=(replace(draft.suppliers[0], selected=True),)),
])
def test_selected_requirement_requires_scope_exact_supplier_and_available_capability(change):
    draft, registrations, registry = fixture()
    with pytest.raises(ValueError):
        compile_recursive_wave(draft=change(draft), registrations=registrations, registry=registry,
                               implementation_commit="1" * 40)


def test_configuration_rejects_deep_noncanonical_revision_extra_fields_and_duplicate_keys():
    draft, registrations, registry = fixture()
    operation = draft.operations[0]
    for payload in ('{"a":' * 65 + '0' + '}' * 65,
                    operation.config_payload.replace('"scalar":3', '"scalar":3.0'),
                    operation.config_payload.replace('"scalar":3', '"scalar":3,"scalar":3')):
        with pytest.raises(ValueError):
            replace(operation, config_payload=payload)
    for payload in (operation.config_payload.replace('"version":"1.0.0"', '"version":"2.0.0"'),
                    operation.config_payload.replace('"scalar":3', '"extra":1,"scalar":3')):
        bad = replace(draft, operations=(replace(operation, config_payload=payload), *draft.operations[1:]))
        with pytest.raises(ValueError):
            compile_recursive_wave(draft=bad, registrations=registrations, registry=registry, implementation_commit="1" * 40)


def test_parity_compares_actual_task_fields_and_selected_scientific_contracts():
    compiled = compile_fixture()
    task = compiled.execution_plan.tasks[-1]
    changed = replace(compiled.execution_plan, tasks=(*compiled.execution_plan.tasks[:-1], replace(task, maximum_attempts=2)))
    with pytest.raises(ValueError, match="drifted"):
        prove_development_graph_parity(draft=compiled.draft, selection=compiled.selected_scientific_projection,
                    template=compiled.template, run_plan=compiled.run_plan, execution_plan=changed, registry=compiled.registry)
    changed_selection = replace(compiled.selected_scientific_projection,
                                requirements=(replace(compiled.draft.requirements[0], falsifier="altered falsifier"),))
    with pytest.raises(ValueError, match="drifted"):
        prove_development_graph_parity(draft=compiled.draft, selection=changed_selection,
                    template=compiled.template, run_plan=compiled.run_plan, execution_plan=compiled.execution_plan, registry=compiled.registry)


def test_variadic_port_requires_distinct_named_exact_producers_and_closed_count():
    draft, registrations, registry = fixture()
    registration = replace(registrations[1], input_ports=(RecursivePortContract("operand", Config.SCHEMA, "application/json", 10_000, 2, 2),))
    links = (replace(draft.links[0], edge_id="edge.a", consumer_input_id="operand.a", requirement_id=None, connection_id=None),
             replace(draft.links[0], edge_id="edge.b", consumer_input_id="operand.b", requirement_id=None, connection_id=None))
    draft = replace(draft, requirements=(), connections=(), suppliers=(), links=links)
    result = compile_recursive_wave(draft=draft, registrations=(registrations[0], registration), registry=registry,
                                  implementation_commit="1" * 40)
    consumer = next(task for task in result.execution_plan.tasks if task.task_id == "use")
    operands = tuple(edge for edge in consumer.scientific_inputs
        if edge.scientific_role is ScientificInputRole.HISTORY)
    assert tuple(edge.consumer_input_id for edge in operands) == ("operand.a", "operand.b")
    configuration, = (edge for edge in consumer.scientific_inputs
        if edge.scientific_role is ScientificInputRole.CONFIGURATION)
    assert configuration.consumer_input_id == "config"
    assert len(consumer.scientific_inputs) == len(operands) + 1
    with pytest.raises(ValueError, match="incomplete port census"):
        compile_recursive_wave(draft=replace(draft, links=links[:1]), registrations=(registrations[0], registration),
                               registry=registry, implementation_commit="1" * 40)


def multiplicity_fixture(count, *, minimum_count, maximum_count):
    """Distinct declared supplier outputs; compilation creates no native effects."""
    draft, registrations, registry = fixture()
    source = replace(registrations[0], outputs=tuple(
        replace(registrations[0].outputs[0], output_id=f"stream-{index:04d}")
        for index in range(count)))
    consumer = replace(registrations[1], input_ports=(RecursivePortContract(
        "streams", Config.SCHEMA, "application/json", 10_000,
        minimum_count=minimum_count, maximum_count=maximum_count),))
    links = tuple(replace(draft.links[0], edge_id=f"edge.stream.{index:04d}",
        consumer_input_id=f"streams.{index:04d}", producer_output_id=f"stream-{index:04d}",
        requirement_id=None, connection_id=None) for index in range(count))
    return replace(draft, requirements=(), connections=(), suppliers=(), links=links), (source, consumer), registry


def test_unbounded_registered_multiplicity_preserves_complete_4097_linked_stream_census():
    draft, registrations, registry = multiplicity_fixture(4097, minimum_count=4097, maximum_count=None)
    compiled = compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
        implementation_commit="1" * 40, output_codecs={Config.SCHEMA: Config})
    assert compiled.proof is not None
    assert compiled.selected_scientific_projection.links == draft.links
    scientific_edges = tuple(edge for edge in compiled.template.graph.edges
        if edge.scientific_role is ScientificInputRole.HISTORY)
    configuration_edges = tuple(edge for edge in compiled.template.graph.edges
        if edge.scientific_role is ScientificInputRole.CONFIGURATION)
    assert len(scientific_edges) == 4097
    assert len(compiled.template.graph.edges) == len(scientific_edges) + len(configuration_edges)
    assert tuple((edge.consumer_node_id, edge.consumer_input_id) for edge in configuration_edges) == (
        ("source", "config"), ("use", "config"))
    assert all(edge.producer_node_id is None and edge.external_input_id is not None
        for edge in configuration_edges)
    supplier = next(task for task in compiled.execution_plan.tasks if task.task_id == "source")
    consumer = next(task for task in compiled.execution_plan.tasks if task.task_id == "use")
    scientific_inputs = tuple(edge for edge in consumer.scientific_inputs
        if edge.scientific_role is ScientificInputRole.HISTORY)
    assert len(supplier.outputs) == len(scientific_inputs) == 4097
    assert len(consumer.scientific_inputs) == len(scientific_inputs) + 1
    for task in compiled.execution_plan.tasks:
        configuration, = (edge for edge in task.scientific_inputs
            if edge.scientific_role is ScientificInputRole.CONFIGURATION)
        assert configuration.consumer_input_id == "config"
    expected = {(link.consumer_input_id, "source." + link.producer_output_id) for link in draft.links}
    assert {(link.consumer_input_id, link.producer_output_id) for link in scientific_inputs} == expected
    assert {output.output_id for output in supplier.outputs} == {producer for _, producer in expected}
    assert consumer.dependency_task_ids == ("source",)
    assert compiled.draft.development_study.assigned_unit_ids == ("unit.one",)


@pytest.mark.parametrize("count,minimum,maximum", [(3, 1, 2), (1, 2, None), (1, 2, 2)])
def test_declared_finite_maximum_and_unbounded_minimum_still_refuse_incomplete_census(count, minimum, maximum):
    draft, registrations, registry = multiplicity_fixture(count, minimum_count=minimum, maximum_count=maximum)
    with pytest.raises(ValueError, match="incomplete port census"):
        compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
            implementation_commit="1" * 40, output_codecs={Config.SCHEMA: Config})


def test_unbounded_multiplicity_does_not_accept_an_undeclared_or_bare_port():
    draft, registrations, registry = multiplicity_fixture(2, minimum_count=1, maximum_count=None)
    for name in ("undeclared.extra", "streams"):
        links = (replace(draft.links[0], consumer_input_id=name), draft.links[1])
        with pytest.raises(ValueError, match="undeclared scientific input port"):
            compile_recursive_wave(draft=replace(draft, links=links), registrations=registrations, registry=registry,
                implementation_commit="1" * 40, output_codecs={Config.SCHEMA: Config})


@pytest.mark.parametrize("maximum", [True, False, 0, -1, 1.0, "2", (), {}])
def test_optional_maximum_retains_strict_invalid_type_and_value_refusal(maximum):
    with pytest.raises(ValueError, match="multiplicity is invalid"):
        RecursivePortContract("streams", Config.SCHEMA, "application/json", None,
            minimum_count=0, maximum_count=maximum)


def test_negative_assessment_is_a_retained_scientific_product_and_positive_requires_evidence():
    draft, _, _ = fixture()
    requirement = ObjectIdentity.from_record(draft.requirements[0].requirement_id, draft.requirements[0])
    connection = ObjectIdentity.from_record(draft.connections[0].connection_id, draft.connections[0])
    refused = RequirementSupplyAssessment("assessment.refused", requirement, connection, AssessmentPhase.ADMISSION,
               AssessmentDisposition.REFUSED, "unit.one", (), ("SOURCE_MISMATCH",))
    assert refused.evidence_ceiling is EvidenceCeiling.NON_PROMOTABLE
    with pytest.raises(ValueError, match="actual evidence"):
        replace(refused, disposition=AssessmentDisposition.SATISFIED, reason_codes=())


def prospective_fixture(*, typed_outputs=False, reveal_terminal=False, worker_memory_bytes=None):
    """Materialize the reference topology through the general authored compiler."""
    from hashlib import sha256
    from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput
    from tests.runtime_platform.test_candidate_compiler import _fixture
    from tests.experiment_entry_support import standard_authoring_for_draft
    from empirical_lawhood.runtime.adjudication import ScientificAdjudicationRecord
    from empirical_lawhood.adapters.reference_worlds.runtime import ReferenceAdjudicationFixture

    draft, original = _fixture()
    template = original.templates[0]
    protocol = template.protocol
    if worker_memory_bytes is not None and (type(worker_memory_bytes) is not int or worker_memory_bytes < 1024**3):
        raise ValueError("actual process fixture needs an explicit feasible memory selection")

    def worker_budget(value):
        return value if worker_memory_bytes is None else replace(value, memory_bytes=worker_memory_bytes, wall_time_seconds=60)

    protocol = replace(protocol, steps=tuple(replace(step, resource_budget=worker_budget(step.resource_budget))
        for step in protocol.steps))
    if typed_outputs:
        protocol = replace(protocol, steps=tuple(replace(step,
                    capability_key='recursive-fixture.' + step.step_id,
                    stage=ScientificStage.REVEAL if reveal_terminal and step.step_id == 'evaluate' else step.stage,
                    outputs=tuple(replace(output, payload_schema=ScientificAdjudicationRecord.SCHEMA
                                          if step.stage in {ScientificStage.EVALUATE, ScientificStage.REVEAL, ScientificStage.REPORT}
                                          else ReferenceAdjudicationFixture.SCHEMA if step.stage is ScientificStage.FREEZE else Config.SCHEMA)
                                  for output in step.outputs)) for step in protocol.steps if step.stage is not ScientificStage.REPORT))
    if worker_memory_bytes is not None:
        aggregate = ResourceBudget.aggregate(step.resource_budget for step in protocol.steps)
        policy = replace(draft.system.authority_policy, budget_ceiling=aggregate)
        draft = replace(draft, resource_ceiling=aggregate, system=replace(draft.system, authority_policy=policy),
            campaign=replace(draft.campaign, budget=aggregate,
                authority_policy=ObjectIdentity.from_record(policy.policy_id, policy)))
    manifest_keys = {step.step_id: step.capability_key for step in protocol.steps}
    original_step = {step.capability_key: step.step_id for step in original.templates[0].protocol.steps}
    manifests = tuple(replace(manifest, capability_key=manifest_keys[original_step[manifest.capability_key]], config_schema=Config.SCHEMA,
                      resource_ceiling=worker_budget(manifest.resource_ceiling),
                      config_schema_sha256=sha256(Config.SCHEMA.encode()).hexdigest(),
                      input_schema_ids=tuple(sorted({*manifest.input_schema_ids, Config.SCHEMA,
                                                   *((ScientificAdjudicationRecord.SCHEMA, ReferenceAdjudicationFixture.SCHEMA) if typed_outputs else ())})),
                      output_schema_ids=tuple(sorted({output.payload_schema for step in protocol.steps
                                                     if step.capability_key == manifest_keys[original_step[manifest.capability_key]]
                                                     for output in step.outputs})))
                      for manifest in original.registry.capabilities if original_step[manifest.capability_key] in manifest_keys)
    registry = replace(original.registry, capabilities=manifests)
    registrations, operations = [], []
    coverage = {}
    for binding in template.coverage.bindings:
        coverage.setdefault('evaluate' if typed_outputs and binding.proof_owner_node_id == 'report'
                            else binding.proof_owner_node_id, set()).add(binding.obligation_id)
    for step in protocol.steps:
        manifest = registry.resolve(step.capability_key, step.capability_version)
        selection = CapabilitySelection(manifest.capability_key, manifest.capability_version, manifest.implementation_sha256)
        incoming = tuple(edge for edge in template.graph.edges if edge.consumer_node_id == step.step_id)
        ports = tuple(sorted((RecursivePortContract(edge.consumer_input_id, edge.payload_schema, edge.media_type,
                              max(edge.maximum_size_bytes, manifest.resource_ceiling.output_bytes)) for edge in incoming),
                             key=lambda value: value.port_id))
        if typed_outputs:
            ports = tuple(replace(port, payload_schema=next(parent.outputs[0].payload_schema for parent in protocol.steps
                                      if parent.step_id == edge.producer_node_id) if edge.producer_node_id is not None else edge.payload_schema)
                          for port, edge in zip(ports, sorted(incoming, key=lambda value: value.consumer_input_id), strict=True))
        registrations.append(RecursiveOperationRegistration(selection, step.stage, Config, ports, step.outputs,
                    step.required_permissions, step.requested_outcome_access, step.visibility_ceiling,
                    manifest.resource_ceiling, step.barrier,
                    adjudication_output_id=step.outputs[0].output_id if typed_outputs and step.stage in {ScientificStage.EVALUATE, ScientificStage.REVEAL} else None))
        obligations = tuple(sorted({*step.obligation_ids, *coverage.get(step.step_id, ())}))
        operations.append(RecursiveOperationSpec.from_config(node_id=step.step_id, selection=selection,
                          config_id=step.config.config_id, config=Config(step.config.config_id, 3),
                          obligation_ids=obligations, resource_budget=step.resource_budget,
                          resource_lock_ids=step.resource_lock_ids, maximum_attempts=step.maximum_attempts))
    external = tuple(RecursiveExternalInput(value.input_id, original.qualifications[0].materialization.object_id, value.payload_schema,
               value.media_type, value.maximum_size_bytes, value.outcome_access, value.visibility_ceiling,
               original.qualifications[0].content_sha256, value.scientific_role.value)
               for value in template.graph.external_inputs)
    links = tuple(RecursiveInputLink(edge.edge_id, edge.consumer_node_id, edge.consumer_input_id,
                  edge.producer_node_id, edge.producer_output_id, edge.external_input_id,
                  edge.scientific_role.value) for edge in template.graph.edges if edge.consumer_node_id in manifest_keys)
    recursive = RecursiveStudyDraft("draft.generic-prospective", draft.question, draft.campaign,
                (), (), (), tuple(operations), external, links, tuple(step.step_id for step in protocol.steps),
                prospective_draft=draft)
    compiled = compile_recursive_wave(draft=recursive, registrations=tuple(registrations), registry=registry,
               implementation_commit="a" * 40, qualifications=original.qualifications,
               known_design_inputs=original.known_design_inputs,
               output_codecs={Config.SCHEMA: Config, ScientificAdjudicationRecord.SCHEMA: ScientificAdjudicationRecord,
                              ReferenceAdjudicationFixture.SCHEMA: ReferenceAdjudicationFixture} if typed_outputs else None)
    assert compiled.candidate_report.candidate is not None, compiled.candidate_report.diagnostics
    authoring, context = standard_authoring_for_draft(compiled.candidate_draft, compiled.candidate_context,
                          formal_method_capability_key='recursive-fixture.evaluate' if typed_outputs else 'reference.evaluate')
    return compiled, authoring, context


def test_general_authored_topology_enters_actual_public_source_entry_and_issue_lifecycle(tmp_path):
    from empirical_lawhood.api import CompileStudyRequest
    from empirical_lawhood.api.results import OperationStatus
    from tests.runtime_platform.test_study_issue import _issue_api_fixture, _issue_request

    compiled, authoring, context = prospective_fixture()
    api, paths, _, _ = _issue_api_fixture(tmp_path, standard_fixture=lambda: (authoring, context))
    preview = api.compile_study(CompileStudyRequest(paths["authoring"]))
    assert preview.status is OperationStatus.SUCCEEDED
    issued = api.issue_study(_issue_request(paths, confirmed=True))
    assert issued.status is OperationStatus.SUCCEEDED
    assert issued.payload.manifest.candidate.base_candidate.scientific_graph == compiled.template.graph
    assert issued.payload.manifest.candidate.base_candidate.protocol == compiled.template.protocol


def test_shared_provider_builds_through_existing_factory_composite_without_config_capture():
    from empirical_lawhood.runtime.executable_bindings import (
        ExecutableBindingContribution, ExecutableCapabilityProviderFactoryRegistry,
        ExecutablePlatformPort, LayeredCampaignRuntimeProviderResolver,
        compose_executable_binding_aggregate,
    )
    from empirical_lawhood.runtime.providers import CampaignRuntimeProviderRegistry, ExternalInputPayload
    from empirical_lawhood.runtime.recursive_provider import (
        RecursiveOperationInputPort, RecursiveOperationProviderFactory,
        recursive_input_port_key, recursive_operation_binding,
    )
    compiled = compile_fixture()
    _, registrations, registry = fixture()
    configs = {row.config_id: row for row in compiled.config_inputs}
    class Supplier:
        def resolve_input(self, spec):
            row = configs[spec.logical_artifact_id]
            return ExternalInputPayload.from_bytes(logical_artifact_id=row.config_id,
                payload_schema=row.payload_schema, profile=ArtifactProfile.CANONICAL_JSON,
                media_type="application/json", payload=row.payload,
                visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
                outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, parent_visibility_ceilings=(), lineage_parents=())
    class Runner:
        def __init__(self, manifest):
            self.manifest = manifest
    factories = []
    ports = []
    for registration in registrations:
        manifest = registry.resolve(registration.selection.capability_key, registration.selection.capability_version)
        binding = recursive_operation_binding(registration=registration, manifest=manifest)
        factories.append(RecursiveOperationProviderFactory(binding, registration, manifest,
                         lambda selected=manifest: Runner(selected), {Config.SCHEMA: Config}))
        ports.append(ExecutablePlatformPort(recursive_input_port_key(registration.selection), RecursiveOperationInputPort(Supplier())))
    factories = tuple(sorted(factories, key=lambda value: value.binding.binding_id))
    contribution = ExecutableBindingContribution("contribution.generic", "1.0.0", tuple(factory.binding for factory in factories))
    from empirical_lawhood.runtime.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind, compose_extension_bundle_aggregate
    from empirical_lawhood.adapters.composition.generated_extension_bundles import EXTENSION_BUNDLE_CONTRIBUTIONS
    discovery_contribution = ExtensionBundleContribution("discovery.generic", "1.0.0", ExtensionContributionKind.METHOD,
        (), registry.capabilities, (), (), (), (), (), (), (), (), False, False)
    discovery = compose_extension_bundle_aggregate((*EXTENSION_BUNDLE_CONTRIBUTIONS, discovery_contribution))
    aggregate = compose_executable_binding_aggregate((contribution,), discovery_aggregate=discovery)
    resolver = LayeredCampaignRuntimeProviderResolver(precomposed=CampaignRuntimeProviderRegistry(()),
                factories=ExecutableCapabilityProviderFactoryRegistry(aggregate=aggregate, factories=factories))
    provider = resolver.resolve(registry, platform_ports=tuple(sorted(ports, key=lambda value: value.port_key)))
    assert len(provider.runners(registry)) == 2
    sources = provider.external_inputs(compiled.execution_plan)
    assert len(sources) == 2
    assert tuple(b"".join(source.chunks()) for source in sources) == tuple(configs[key].payload for key in sorted(configs))
    assert len(provider.output_semantic_contracts(registry, compiled.execution_plan)) == 2


def test_closed_wave_retains_unselected_partial_requirement_and_unknown_supplier():
    from empirical_lawhood.runtime.recursive_compiler import project_recursive_assessments
    draft, registrations, registry = fixture()
    operation = replace(draft.operations[0], node_id='future', selection=CapabilitySelection('unavailable.future', '1.0.0', 'd' * 64))
    requirement = replace(draft.requirements[0], requirement_id='requirement.future', consumer_operation_id='future',
                          scope=None, assessment_operation_id=None)
    supplier = SupplierProposal('alternative.future', requirement.requirement_id, ('future',), (), False,
                               'Threshold and substrate remain unselected', ('NO_REGISTERED_SUPPLIER',))
    partial = replace(draft, operations=tuple(sorted((*draft.operations, operation), key=lambda value: value.node_id)),
                      requirements=tuple(sorted((*draft.requirements, requirement), key=lambda value: value.requirement_id)),
                      suppliers=tuple(sorted((*draft.suppliers, supplier), key=lambda value: value.proposal_id)))
    result = compile_recursive_wave(draft=partial, registrations=registrations, registry=registry, implementation_commit='1' * 40)
    assert len(result.execution_plan.tasks) == 2
    assert result.draft.requirements[0].scope is None
    assert len(result.selected_scientific_projection.requirements) == 1
    assert result.draft == partial and operation in result.draft.operations and supplier in result.draft.suppliers
    assert project_recursive_assessments(draft=partial, registrations=registrations, outputs={}) == ()
    with pytest.raises(ValueError, match='exact code-owned registration'):
        compile_recursive_wave(draft=replace(partial, selected_operation_ids=('future', 'source', 'use'),
                requirements=draft.requirements, suppliers=draft.suppliers),
            registrations=registrations, registry=registry, implementation_commit='1' * 40)


def test_global_material_decision_and_explicit_object_edge_depth_bounds():
    import json
    from empirical_lawhood.planning.study_authoring import UnresolvedDecision
    draft, registrations, registry = fixture()
    decision = UnresolvedDecision('decision.wave', 'wave.selected', 'Which selected task threshold applies?', ('first', 'second'))
    with pytest.raises(ValueError, match='unresolved scientific decisions'):
        compile_recursive_wave(draft=replace(draft, unresolved_decisions=(decision,)), registrations=registrations,
                               registry=registry, implementation_commit='1' * 40)
    with pytest.raises(ValueError, match='graph bounds'):
        replace(draft, maximum_objects=4)
    with pytest.raises(ValueError, match='depth bound'):
        compile_recursive_wave(draft=replace(draft, maximum_depth=1), registrations=registrations,
                               registry=registry, implementation_commit='1' * 40)
    document = draft.operations[0].to_document()['value']['config_payload']
    document = json.loads(document)
    document['value']['scalar'] = [0] * 200_001
    expanded = json.dumps(document, separators=(',', ':'), sort_keys=True) + '\n'
    changed = replace(draft.operations[0], config_payload=expanded)
    assert changed.config_payload == expanded
    # Removing a structural capacity guess does not relax the registered codec.
    with pytest.raises(ValueError):
        compile_recursive_wave(draft=replace(draft, operations=(changed, draft.operations[1])),
            registrations=registrations, registry=registry, implementation_commit='1' * 40)


def test_default_graph_capacity_is_unrestricted_and_historical_finite_values_roundtrip():
    draft, _, _ = fixture()
    assert (draft.maximum_objects, draft.maximum_links, draft.maximum_depth) == (None, None, None)
    partial = tuple(replace(draft.requirements[0], requirement_id=f'future.{index:04d}',
        consumer_operation_id='future', assessment_operation_id=None) for index in range(300))
    expanded = replace(draft, requirements=tuple(sorted((*draft.requirements, *partial),
        key=lambda value: value.requirement_id)))
    assert len(expanded.requirements) == 301
    for selected in (draft, replace(draft, maximum_objects=256, maximum_links=1024, maximum_depth=32)):
        raw = selected.canonical_bytes()
        restored = decode_canonical_bytes(raw, RecursiveStudyDraft, maximum_bytes=len(raw))
        assert restored == selected and restored.canonical_bytes() == raw
    for field in ('maximum_objects', 'maximum_links', 'maximum_depth'):
        with pytest.raises(ValueError, match='capacity'):
            replace(draft, **{field: True})


def test_config_nesting_has_no_sixty_four_level_ceiling_but_strict_numbers_and_keys_remain():
    import json
    draft, _, _ = fixture()
    document = json.loads(draft.operations[0].config_payload)
    nested = 0
    for _ in range(80):
        nested = [nested]
    document['value']['scalar'] = nested
    raw = json.dumps(document, separators=(',', ':'), sort_keys=True) + '\n'
    assert replace(draft.operations[0], config_payload=raw).config_payload == raw
    for value in ('1.5', 'NaN', 'Infinity', '{"duplicate":0,"duplicate":1}'):
        changed = draft.operations[0].config_payload.replace('"scalar":3', '"scalar":' + value)
        with pytest.raises(ValueError):
            replace(draft.operations[0], config_payload=changed)


def test_registered_multiplicity_and_identity_projection_have_no_global_count_ceiling():
    from empirical_lawhood.runtime.recursive_compiler import _registered_identity_projection
    port = RecursivePortContract('operand', Config.SCHEMA, 'application/json', None, 0, 300)
    assert port.matches('operand.299')
    values = tuple(f'unit.{index:04d}' for index in range(300))
    assert _registered_identity_projection(lambda config: values, None, field_name='units') == values
    with pytest.raises(ValueError, match='sorted and unique'):
        _registered_identity_projection(lambda config: (*values, values[0]), None, field_name='units')


def test_scientific_operand_binding_refuses_coherent_config_substitution_before_contact():
    draft, registrations, registry = fixture()
    identities = tuple(sorted((operation.config_identity for operation in draft.operations), key=lambda value: value.object_id))
    draft = replace(draft, development_study=replace(draft.development_study, scientific_operands=identities))
    registrations = tuple(replace(registration, scientific_operand_sha256s=lambda record: (record.fingerprint(),))
                          for registration in registrations)
    compile_recursive_wave(draft=draft, registrations=registrations, registry=registry, implementation_commit='1' * 40)
    changed = replace(draft.operations[0], config_payload=draft.operations[0].config_payload.replace('"scalar":3', '"scalar":4'))
    with pytest.raises(ValueError, match='scientific operand'):
        compile_recursive_wave(draft=replace(draft, operations=(changed, draft.operations[1])), registrations=registrations,
                               registry=registry, implementation_commit='1' * 40)


def test_external_config_bindings_round_trip_and_share_schema_without_constructor_capture():
    from empirical_lawhood.runtime.executable_bindings import ExecutableBindingContribution
    from empirical_lawhood.runtime.recursive_provider import recursive_operation_binding
    _, registrations, registry = fixture()
    registration = replace(registrations[1], config_record_type=SourceConfig)
    manifest = replace(registry.capabilities[1], config_schema=SourceConfig.SCHEMA,
                       input_schema_ids=tuple(sorted({Config.SCHEMA, SourceConfig.SCHEMA})))
    bindings = tuple(sorted((recursive_operation_binding(registration=registrations[0], manifest=registry.capabilities[0]),
                             recursive_operation_binding(registration=registration, manifest=manifest)), key=lambda value: value.binding_id))
    assert bindings[0].accepted_config_types == bindings[1].accepted_config_types
    assert all(not binding.construction_record_schema_ids for binding in bindings)
    contribution = ExecutableBindingContribution('external-config.test', '1.0.0', bindings)
    assert decode_canonical_bytes(contribution.canonical_bytes(), ExecutableBindingContribution, maximum_bytes=100_000) == contribution
