# SPDX-License-Identifier: MPL-2.0
"""Receipt-bound evaluator controls with explicit exposed software originals.

Prepared invocation contracts, guarded inputs and predecessor receipts are real.
All literals, source qualifications and reveal context are synthetic controls;
none supplies an authenticated sampling warrant or genuine authority.
"""

from dataclasses import fields, replace
from decimal import Decimal
from fractions import Fraction
import pickle
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import protected_adjudication as owner
from empirical_lawhood.infrastructure.execution import prepare_worker_invocation
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess as Access, VisibilityCeiling as Visibility, inherited_visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import AdmissionStatus, ScientificStatus
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.adjudication import AdjudicationEvaluability, ScientificAdjudicationContext, ScientificAdjudicationRecord
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityPermission, CapabilityRequirement
from empirical_lawhood.runtime.execution import DependencyReceiptBinding, TaskContext, VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec, ScientificInputRole, ScientificInputSpec, ScientificStage
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
from tests.worker_configuration_support import freeze_worker_configuration
from tests.test_matrix_e3_statistical_bindings import case as case, fitted as fitted, stored
from tests.test_matrix_e3_statistical_bindings_independent_review import sequence as sequence


def scientific_root(config, context):
    config.__post_init__()
    if context.node_id != owner.adjudication_task_id(config.specification, config.allocation):
        raise ValueError('synthetic root changes selected adjudication')


def prepared(case, fitted, assessment, *, producer_output='product', external_assessment=False,
        authority_kind=WorldKind.NUMERICAL_SIMULATOR, authority_plan=None, no_authority=False, qualified_outputs=True):
    declaration = owner.adjudication_declaration(scientific_root_validator=scientific_root)
    runner, manifest = declaration.runner_factory(), declaration.manifest()
    task_id = owner.adjudication_task_id(case.inputs.specification.identity, case.allocation.identity)
    config = owner.ProtectedE3AdjudicationConfig('config.' + task_id, case.inputs.specification.identity, case.allocation.identity)
    case.counter += 1
    prefix = 'adjudication.' + str(case.counter)
    automatic = stored(case, config, prefix + '.config', logical_id=config.record_id,
        access=Access.EVALUATOR_REVEAL, ceiling=Visibility.OUTCOME_VISIBLE)
    operands = {'specification': fitted.common['specification'], 'allocation': fitted.common['allocation'], 'assessment': assessment}
    rows = {'automatic': automatic, **operands}
    verified = tuple(sorted((VerifiedArtifactInput(value.publication.logical, value.publication.materialization)
        for value in rows.values()), key=lambda row: row.artifact_id))
    by_id = {value.publication.logical.logical_artifact_id: (name, value) for name, value in rows.items()}
    bindings = tuple(WorkerInputBinding.from_verified(value, kind=WorkerInputKind.DEPENDENCY
        if by_id[value.artifact_id][0] == 'assessment' and not external_assessment else WorkerInputKind.EXTERNAL)
        for value in verified)
    ports = case.plane.open_many(verified, bindings=bindings, maximum_bytes=None)
    deps = (() if external_assessment else (DependencyReceiptBinding(assessment.receipt.receipt_id,
        assessment.receipt.task_id, (assessment.publication.materialization.materialization_id,)),))
    config_ref = CapabilityConfigRef(config.record_id, config.SCHEMA, manifest.config_schema_sha256,
        config.fingerprint(), automatic.publication.logical.logical_artifact_id)
    output = WorkerOutputPort(task_id + '.adjudication', ScientificAdjudicationRecord.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'ordinary.' + prefix)
    plan = ObjectIdentity('plan.literal.e3-adjudication', 'empirical-lawhood/runtime/execution-plan', '1.0.0', 'e' * 64)
    authority = None if no_authority else ScientificAdjudicationContext(authority_plan or plan,
        'world.literal.e3-adjudication', authority_kind,
        ObjectIdentity('relation.literal.e3', 'empirical-lawhood/testing/e3-relation', '1.0.0', 'a' * 64),
        'unit.whole-root', (ObjectIdentity.from_record(case.fit_cutoff.cutoff_id, case.fit_cutoff),),
        Visibility.OUTCOME_VISIBLE, Access.EVALUATION_REVEALED)
    context = TaskContext('run.literal.e3-adjudication', task_id, 'attempt.' + prefix, config_ref,
        bindings, ports, (output,), manifest.permissions, Access.EVALUATOR_REVEAL, owner.BUDGET,
        WorkerIsolationProfile.TRUSTED_LOCAL, deps, scientific_adjudication_context=authority)
    incoming, external = [], []
    for value, binding in zip(verified, bindings, strict=True):
        name, selected = by_id[value.artifact_id]
        dependency = binding.kind is WorkerInputKind.DEPENDENCY
        if not dependency:
            external.append(ExternalInputSpec('input.' + value.artifact_id, value.artifact_id,
                value.logical.content_sha256, value.logical.payload_schema, value.logical.media_type,
                value.materialization.size_bytes, value.logical.visibility_ceiling, value.logical.outcome_access, None))
        if name == 'automatic':
            continue
        incoming.append(ScientificInputSpec('edge.' + prefix + '.' + name, name,
            ScientificInputRole.OUTCOME if dependency else ScientificInputRole.SOURCE,
            selected.receipt.task_id if dependency else None,
            (selected.receipt.task_id + '.' + producer_output if qualified_outputs else producer_output) if dependency else None,
            None if dependency else 'external.' + name, 'scientific.' + prefix + '.' + name,
            binding.artifact_id, binding.payload_schema, binding.media_type, binding.size_bytes,
            binding.outcome_access, binding.visibility_ceiling, BarrierKind.NONE))
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind,
        config_ref, manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions,
        EvidenceCeiling.RESPONSE, Access.EVALUATOR_REVEAL, owner.BUDGET)
    task = ExecutionTask(task_id, ScientificStage.EVALUATE, requirement, manifest.implementation_sha256,
        tuple(row.task_id for row in deps), tuple(external),
        (ArtifactOutputSpec(output.output_id, output.logical_artifact_id, 'adjudication/' + prefix + '.json',
            output.payload_schema, output.profile, output.media_type,
            inherited_visibility(tuple(binding.visibility_ceiling for binding in bindings), Access.EVALUATION_REVEALED),
            tuple(binding.visibility_ceiling for binding in bindings), Access.EVALUATION_REVEALED),),
        (), BarrierKind.REVEAL, 1, ('obligation.literal.adjudicate',),
        scientific_inputs=tuple(sorted(incoming, key=lambda row: row.edge_id)))
    task = freeze_worker_configuration(task)
    provenance = case.provenance
    implementation = RecursiveImplementationBinding(provenance.package_sources, provenance.code_sources_sha256,
        provenance.dependency_lock_sha256, provenance.observed_git_head, provenance.observed_checkout_clean)
    try:
        contract = prepare_worker_invocation(runner, context, verified, implementation=implementation,
            execution_plan=plan, execution_task=ObjectIdentity.from_record(task_id, task), execution_task_record=task)
    except Exception:
        for port in ports:
            port.close()
        raise
    return SimpleNamespace(runner=runner, context=replace(context, prepared_invocation=contract), declaration=declaration)


def test_terminal_declaration_is_a_separate_revealing_evaluator_with_seedless_config(case):
    declaration = owner.adjudication_declaration(scientific_root_validator=scientific_root)
    assert declaration.stage is ScientificStage.EVALUATE
    assert declaration.kind is owner.CapabilityKind.EVALUATOR
    assert declaration.execution_properties.barrier is BarrierKind.REVEAL
    assert declaration.outcome_access is Access.EVALUATOR_REVEAL
    assert declaration.scientific_hooks.adjudication_output_id == 'adjudication'
    assert CapabilityPermission.REVEAL_OUTCOMES in declaration.permissions
    assert tuple(field.name for field in fields(owner.ProtectedE3AdjudicationConfig)) == ('record_id', 'specification', 'allocation')
    assert pickle.loads(pickle.dumps(declaration.runner_factory())).manifest == declaration.manifest()


def test_actual_current_assessment_projects_unevaluable_and_retains_runtime_scope(case, fitted, sequence):
    selected = prepared(case, fitted, sequence.assessment)
    config_port, = (port for port in selected.context.input_ports if port.artifact_id == selected.context.config.artifact_id)
    assert (config_port.outcome_access, config_port.visibility_ceiling) == (Access.EVALUATOR_REVEAL, Visibility.OUTCOME_VISIBLE)
    result = selected.runner.execute(selected.context)
    record = decode_canonical_bytes(result.outputs[0].payload, ScientificAdjudicationRecord, maximum_bytes=None)
    assert record.matches_context(selected.context.scientific_adjudication_context)
    assert record.input_materialization_ids == selected.context.input_materialization_ids
    assert record.required_receipt_ids == selected.context.dependency_receipt_ids
    assert record.evaluability is AdjudicationEvaluability.UNEVALUABLE
    assert record.scientific_status is ScientificStatus.UNEVALUABLE
    assert record.admission_status is AdmissionStatus.UNEVALUABLE
    assert {'SAMPLING_ASSUMPTION_NOT_AUTHENTICATED', 'ASSIGNED_CONFIRMATION_UNITS_8',
        'USABLE_CONFIRMATION_UNITS_7', 'NONUSE_RETAINED_IN_ASSIGNED_DENOMINATOR', 'UNKNOWN_CONTACT'} <= set(record.reason_codes)


def test_even_a_met_conditional_criterion_cannot_create_missing_sampling_warrant(case, fitted, sequence):
    original = sequence.assessment.record
    decisions = tuple(replace(row, usable=True, success=True,
        comparisons=tuple((baseline, view, Decimal('0.001')) for baseline, view, _ in row.comparisons),
        reasons=('PAIRED_SUCCESS',)) for row in original.decisions)
    literal = replace(original, decisions=decisions, successes=8, usable_units=8,
        binomial_tail_numerator=1, binomial_tail_denominator=256, criterion_met=True)
    assert Fraction(1, 256) <= case.inputs.specification.assessment.alpha
    supplied = stored(case, literal, 'adjudication.literal-conditional-met', task=sequence.assessment.receipt.task_id,
        access=Access.EVALUATION_SEALED, ceiling=Visibility.DEVELOPMENT_ONLY)
    selected = prepared(case, fitted, supplied)
    record = decode_canonical_bytes(selected.runner.execute(selected.context).outputs[0].payload,
        ScientificAdjudicationRecord, maximum_bytes=None)
    assert 'CONDITIONAL_CRITERION_MET' in record.reason_codes
    assert 'SAMPLING_ASSUMPTION_NOT_AUTHENTICATED' in record.reason_codes
    assert record.scientific_status is ScientificStatus.UNEVALUABLE
    assert record.admission_status is AdmissionStatus.UNEVALUABLE


@pytest.mark.parametrize('damage', ('no-authority', 'analytic-world', 'foreign-plan', 'foreign-task', 'foreign-output', 'external-assessment'))
def test_authority_and_actual_producer_refusals_precede_assessment_read(case, fitted, sequence, damage):
    supplied = sequence.assessment
    arguments = {}
    if damage == 'no-authority':
        arguments['no_authority'] = True
    elif damage == 'analytic-world':
        arguments['authority_kind'] = WorldKind.ANALYTIC_REFERENCE
    elif damage == 'foreign-plan':
        arguments['authority_plan'] = ObjectIdentity('plan.foreign', 'empirical-lawhood/runtime/execution-plan', '1.0.0', 'f' * 64)
    elif damage == 'foreign-task':
        supplied = stored(case, supplied.record, 'adjudication.foreign-assessment-task', task='task.foreign',
            access=Access.EVALUATION_SEALED, ceiling=Visibility.DEVELOPMENT_ONLY)
    elif damage == 'foreign-output':
        arguments['producer_output'] = 'outcome'
    else:
        arguments['external_assessment'] = True
    if damage == 'foreign-plan':
        with pytest.raises(ValueError, match='exact adjudication execution scope'):
            prepared(case, fitted, supplied, **arguments)
        return
    selected = prepared(case, fitted, supplied, **arguments)
    assessment_port, = (port for port in selected.context.input_ports if port.payload_schema == owner.ProtectedE3Assessment.SCHEMA)
    with pytest.raises(ValueError):
        selected.runner.execute(selected.context)
    assert assessment_port.bytes_read == 0


@pytest.mark.parametrize('damage', ('missing-unit', 'wrong-binomial', 'changed-margin', 'wrong-allocation'))
def test_terminal_projection_refuses_altered_full_denominator_or_conditional_math(case, fitted, sequence, damage):
    assessment = sequence.assessment.record
    if damage == 'missing-unit':
        decisions = assessment.decisions[:-1]
        assessment = replace(assessment, decisions=decisions, forecasts=assessment.forecasts[:-1], outcomes=assessment.outcomes[:-1],
            coverage=assessment.coverage[:-1], coverage_bound_kinds=assessment.coverage_bound_kinds[:-1],
            successes=sum(row.success for row in decisions), usable_units=sum(row.usable for row in decisions))
    elif damage == 'wrong-binomial':
        assessment = replace(assessment, binomial_tail_numerator=0, binomial_tail_denominator=1)
    elif damage == 'changed-margin':
        row = assessment.decisions[0]
        row = replace(row, comparisons=tuple((baseline, view, Decimal(0)) for baseline, view, _ in row.comparisons),
            usable=True, success=True)
        decisions = (row, *assessment.decisions[1:])
        assessment = replace(assessment, decisions=decisions, successes=sum(row.success for row in decisions),
            usable_units=sum(row.usable for row in decisions))
    else:
        assessment = replace(assessment, allocation=replace(assessment.allocation, object_fingerprint='f' * 64))
    supplied = stored(case, assessment, 'adjudication.altered.' + damage,
        task=sequence.assessment.receipt.task_id, access=Access.EVALUATION_SEALED, ceiling=Visibility.DEVELOPMENT_ONLY)
    selected = prepared(case, fitted, supplied)
    with pytest.raises(ValueError):
        selected.runner.execute(selected.context)


@pytest.mark.parametrize('access', (Access.EVALUATION_REVEALED, Access.PRIVILEGED_TRUTH))
def test_revealed_or_privileged_scientific_assessment_still_refuses_before_read(case, fitted, sequence, access):
    supplied = stored(case, sequence.assessment.record, 'adjudication.foreign-scope.' + access.value,
        task=sequence.assessment.receipt.task_id, access=access,
        ceiling=Visibility.PRIVILEGED_TRUTH if access is Access.PRIVILEGED_TRUTH else Visibility.OUTCOME_VISIBLE)
    selected = prepared(case, fitted, supplied)
    assessment_port, = (port for port in selected.context.input_ports if port.payload_schema == owner.ProtectedE3Assessment.SCHEMA)
    with pytest.raises(ValueError, match='receives revealed inputs'):
        selected.runner.execute(selected.context)
    assert assessment_port.bytes_read == 0
