# SPDX-License-Identifier: MPL-2.0
"""Transitive custody is derived before generic recursive graph publication.

These are outcome-free synthetic compiler records. No runner, issue, worker,
source acquisition or scientific qualification is exercised here.
"""

from dataclasses import replace

import pytest

from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.recursive_authoring import RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.runtime.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission, CapabilityRegistry
from empirical_lawhood.runtime.compiler import compile_run_plan, lower_run_plan
from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.preexecution_contract import validate_experiment_contract_closure
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract, compile_recursive_wave
from empirical_lawhood.runtime.recursive_provider import RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks
from tests.runtime_platform.test_recursive_compiler import Config, prospective_fixture
from tests.runtime_platform.test_recursive_prospective_workflow import FixtureCanonicalSource


def _forbidden():
    raise AssertionError('custody projection invoked a runner')


@pytest.fixture(scope='module')
def compiled():
    return _compiled()


def _compiled(*, mixed_evaluator_outputs=False):
    base, _, _ = prospective_fixture(typed_outputs=True)
    external, = base.draft.external_inputs
    budget = ResourceBudget(1, 1024**2, 0, 2, 10_000, 10_000)
    output = OutputTemplate('product', Config.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json')
    previous_owners = {'prepare': 'p.blind', 'develop-a': 'z.develop', 'develop-b': 'a.reduce',
        'freeze': 'b.freeze', 'evaluate': 'm.reveal'}
    obligations = {}
    for binding in base.template.coverage.bindings:
        obligations.setdefault(previous_owners[binding.proof_owner_node_id], set()).add(binding.obligation_id)
    # Node IDs deliberately disagree with dependency order.
    selections = (
        ('z.develop', ScientificStage.DEVELOP, CapabilityKind.ANALYSIS, Access.DEVELOPMENT_VISIBLE, Visibility.DEVELOPMENT_ONLY, ('source',)),
        ('b.freeze', ScientificStage.FREEZE, CapabilityKind.EXPERIMENT_DESIGNER, Access.OUTCOME_BLIND, Visibility.PROSPECTIVE, ('model',)),
        ('y.forecast', ScientificStage.FREEZE, CapabilityKind.EXPERIMENT_DESIGNER, Access.EVALUATION_SEALED, Visibility.PROSPECTIVE, ('model',)),
        ('a.reduce', ScientificStage.TRANSFORM, CapabilityKind.TRANSFORM, Access.EVALUATION_SEALED, Visibility.PROSPECTIVE, ('forecast',)),
        ('p.blind', ScientificStage.TRANSFORM, CapabilityKind.TRANSFORM, Access.OUTCOME_BLIND, Visibility.PROSPECTIVE, ('source',)),
        ('m.reveal', ScientificStage.EVALUATE, CapabilityKind.EVALUATOR, Access.EVALUATOR_REVEAL, Visibility.OUTCOME_VISIBLE, ('blind', 'assessment')),
    )
    declarations, operations = [], []
    for node, stage, kind, access, ceiling, inputs in selections:
        permissions = [CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
            CapabilityPermission.READ_DEVELOPMENT, CapabilityPermission.READ_FROZEN_MODELS]
        if access in (Access.EVALUATION_SEALED, Access.EVALUATOR_REVEAL):
            permissions.append(CapabilityPermission.READ_SEALED_OUTCOMES)
        if access is Access.EVALUATOR_REVEAL:
            permissions.append(CapabilityPermission.REVEAL_OUTCOMES)
        protected_evaluator = mixed_evaluator_outputs and node == 'm.reveal'
        outputs = (output, OutputTemplate('verdict', ScientificAdjudicationRecord.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', '.json')) if protected_evaluator else (output,)
        declaration = RecursiveOperationDeclaration('testing.inherited.' + node, '1.0.0',
            'testing.inherited.' + node + '.v1', kind, Config, stage,
            tuple(RecursivePortContract(name, external.payload_schema if name == 'source' else Config.SCHEMA,
                'application/json', 10_000) for name in sorted(inputs)),
            outputs, tuple(sorted(permissions)), EvidenceCeiling.RESPONSE, access,
            Visibility.PROSPECTIVE if protected_evaluator else ceiling, budget,
            ('check.disclosed-transitive-custody',), _forbidden,
            {Config.SCHEMA: Config, FixtureCanonicalSource.SCHEMA: FixtureCanonicalSource,
                ScientificAdjudicationRecord.SCHEMA: ScientificAdjudicationRecord},
            scientific_hooks=RecursiveScientificHooks(adjudication_output_id='verdict' if protected_evaluator else None),
            execution_properties=RecursiveExecutionProperties(barrier=BarrierKind.REVEAL if stage is ScientificStage.EVALUATE
                else BarrierKind.FREEZE if stage is ScientificStage.FREEZE else BarrierKind.NONE))
        declarations.append(declaration)
        operations.append(RecursiveOperationSpec.from_config(node_id=node, selection=declaration.registration().selection,
            config_id='config.' + node, config=Config('config.' + node, 3),
            obligation_ids=tuple(sorted({*obligations.get(node, ()), 'obligation.' + node})), resource_budget=budget))
    aggregate = ResourceBudget.aggregate(operation.resource_budget for operation in operations)
    root = base.draft.prospective_draft
    policy = replace(root.system.authority_policy, budget_ceiling=aggregate)
    campaign = replace(root.campaign, budget=aggregate, authority_policy=ObjectIdentity.from_record(policy.policy_id, policy))
    root = replace(root, resource_ceiling=aggregate, system=replace(root.system, authority_policy=policy), campaign=campaign)
    links = [RecursiveInputLink('edge.' + node + '.source', node, 'source', external_input_id=external.input_id,
        scientific_role=external.scientific_role)
        for node in ('z.develop', 'p.blind')]
    for node, name, producer in (('b.freeze', 'model', 'z.develop'), ('y.forecast', 'model', 'b.freeze'),
            ('a.reduce', 'forecast', 'y.forecast'), ('m.reveal', 'assessment', 'a.reduce'), ('m.reveal', 'blind', 'p.blind')):
        links.append(RecursiveInputLink('edge.' + node + '.' + name, node, name, producer, 'product'))
    draft = RecursiveStudyDraft('draft.disclosed.inherited-custody', root.question, campaign, (), (), (),
        tuple(sorted(operations, key=lambda row: row.node_id)), (external,), tuple(sorted(links, key=lambda row: row.edge_id)),
        tuple(sorted(row.node_id for row in operations)), prospective_draft=root)
    registry = CapabilityRegistry('registry.disclosed.inherited-custody', tuple(sorted(
        (declaration.manifest() for declaration in declarations), key=lambda row: row.registry_id)))
    compilation = compile_recursive_wave(draft=draft, registrations=tuple(declaration.registration() for declaration in declarations),
        registry=registry, implementation_commit='a' * 40, qualifications=base.candidate_context.qualifications,
        known_design_inputs=base.candidate_context.known_design_inputs,
        output_codecs={Config.SCHEMA: Config, ScientificAdjudicationRecord.SCHEMA: ScientificAdjudicationRecord})
    assert compilation.candidate_report.candidate is not None, compilation.candidate_report.diagnostics
    candidate = compilation.candidate_report.candidate
    plan = compile_run_plan(run_plan_id='run.disclosed.inherited-custody', campaign=candidate.campaign,
        system=candidate.system, experiment=candidate.experiment, frozen_proposal=None, authorization=None,
        template=candidate.protocol, registry=registry, implementation_commit='a' * 40, approval_service=None,
        scientific_graph=candidate.scientific_graph, candidate=ObjectIdentity.from_record(candidate.candidate_id, candidate),
        preissue_candidate=candidate)
    return compilation, plan, lower_run_plan(plan, registry)


def test_reverse_lexical_recursive_chain_keeps_sealed_development_ancestry_and_blind_branch(compiled):
    compilation, plan, execution = compiled
    outputs = {step.step_id: step.outputs[0] for step in plan.steps}
    assert (outputs['z.develop'].outcome_access, outputs['b.freeze'].outcome_access) == (
        Access.DEVELOPMENT_VISIBLE, Access.DEVELOPMENT_VISIBLE)
    for node in ('z.develop', 'b.freeze', 'y.forecast', 'a.reduce'):
        assert outputs[node].visibility_ceiling is Visibility.DEVELOPMENT_ONLY
    assert outputs['y.forecast'].outcome_access is outputs['a.reduce'].outcome_access is Access.EVALUATION_SEALED
    assert (outputs['p.blind'].outcome_access, outputs['p.blind'].visibility_ceiling) == (Access.OUTCOME_BLIND, Visibility.PROSPECTIVE)
    assert (outputs['m.reveal'].outcome_access, outputs['m.reveal'].visibility_ceiling) == (Access.EVALUATION_REVEALED, Visibility.OUTCOME_VISIBLE)
    expected = {'b.freeze': Access.DEVELOPMENT_VISIBLE, 'y.forecast': Access.DEVELOPMENT_VISIBLE,
        'a.reduce': Access.EVALUATION_SEALED, 'm.reveal': Access.EVALUATION_SEALED}
    for edge in compilation.template.graph.edges:
        if edge.producer_node_id is not None and edge.producer_node_id != 'p.blind':
            assert edge.visibility_ceiling is Visibility.DEVELOPMENT_ONLY
            assert edge.outcome_access is expected[edge.consumer_node_id]
    matrix = validate_experiment_contract_closure(run_plan=plan, execution_plan=execution, capability_registry=compilation.registry)
    assert matrix.passed, matrix.reason_codes


def test_prospective_evaluator_reveals_only_its_adjudication_and_keeps_operand_lineage():
    compilation, plan, execution = _compiled(mixed_evaluator_outputs=True)
    evaluator, = (step for step in plan.steps if step.step_id == 'm.reveal')
    template, = (step for step in compilation.template.protocol.steps if step.step_id == 'm.reveal')
    assert template.visibility_ceiling is Visibility.PROSPECTIVE
    assert template.requested_outcome_access is Access.EVALUATOR_REVEAL
    task, = (task for task in execution.tasks if task.task_id == 'm.reveal')
    for outputs in (evaluator.outputs, task.outputs):
        operand, = (output for output in outputs if output.payload_schema == Config.SCHEMA)
        verdict, = (output for output in outputs if output.payload_schema == ScientificAdjudicationRecord.SCHEMA)
        assert (operand.outcome_access, operand.visibility_ceiling) == (Access.EVALUATOR_REVEAL, Visibility.DEVELOPMENT_ONLY)
        assert (verdict.outcome_access, verdict.visibility_ceiling) == (Access.EVALUATION_REVEALED, Visibility.OUTCOME_VISIBLE)
    assert Visibility.DEVELOPMENT_ONLY in next(output for output in task.outputs
        if output.payload_schema == Config.SCHEMA).parent_visibility_ceilings
    matrix = validate_experiment_contract_closure(run_plan=plan, execution_plan=execution,
        capability_registry=compilation.registry)
    assert matrix.passed, matrix.reason_codes


@pytest.mark.parametrize('target', ('edge', 'output'))
def test_strict_contract_closure_still_refuses_a_lowered_transitive_lane(compiled, target):
    compilation, plan, execution = compiled
    tasks = []
    for task in execution.tasks:
        if task.task_id == 'a.reduce':
            if target == 'edge':
                task = replace(task, scientific_inputs=tuple(replace(edge, visibility_ceiling=Visibility.PROSPECTIVE)
                    if edge.producer_task_id == 'y.forecast' else edge for edge in task.scientific_inputs))
            else:
                task = replace(task, outputs=tuple(replace(output, visibility_ceiling=Visibility.PROSPECTIVE,
                    parent_visibility_ceilings=()) for output in task.outputs))
        tasks.append(task)
    changed = replace(execution, tasks=tuple(tasks))
    matrix = validate_experiment_contract_closure(run_plan=plan, execution_plan=changed, capability_registry=compilation.registry)
    expected = 'LINEAGE_VISIBILITY_LOWERED:' if target == 'edge' else 'OUTPUT_LINEAGE_VISIBILITY_LOWERED:'
    assert not matrix.passed and any(reason.startswith(expected) for reason in matrix.reason_codes), matrix.reason_codes
