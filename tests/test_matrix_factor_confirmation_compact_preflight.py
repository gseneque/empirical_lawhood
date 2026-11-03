# SPDX-License-Identifier: MPL-2.0
"""Declared E1 graph through strict native readiness, using exposed test roots.

The dependency receipt binding is an explicit software fixture. No issue,
qualification, native entry or fresh scientific evidence is created here.
"""
from dataclasses import replace
from pathlib import Path

import pytest

from threadpoolctl import threadpool_limits

from empirical_lawhood.adapters.methods.matrix_factor_confirmation import (
    compact_bindings as owner, compact_preparation as domain, compact_records as records,
)
from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.api.recursive_authoring import implementation_binding
from empirical_lawhood.infrastructure import execution as lifecycle
from empirical_lawhood.infrastructure.numerical_provenance import selected_worker_environment
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.compiler import compile_run_plan, lower_run_plan
from empirical_lawhood.runtime.execution import (
    DependencyReceiptBinding, TaskContext, VerifiedArtifactInput, WorkerInputBinding,
    ParentPreparedTaskRunner, WorkerInputKind, WorkerIsolationProfile, WorkerOutputPort,
)
from empirical_lawhood.runtime.plans import ScientificInputRole
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.test_matrix_factor_confirmation_compact_declarative import _case
from tests.test_matrix_factor_confirmation_eligibility import provenance, stock  # noqa: F401
from tests.test_matrix_factor_confirmation_history import e1  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]


def _context(case, *, compact=True, input_access_changes=()):
    plane = case[0]
    if compact:
        selected_owner = owner
        spec, selected, _ = _case(case)
        policy = selected.root.system.authority_policy
        selected = replace(selected, root=replace(selected.root, campaign=replace(selected.root.campaign,
            authority_policy=ObjectIdentity.from_record(policy.policy_id, policy))))
        spec = replace(spec, selection=selected.identity)
        draft, _, input_records = domain._derive(spec, selected)
        qualifications = selected.qualifications
    else:
        from empirical_lawhood.adapters.methods.matrix_factor_confirmation import operation_bindings
        from tests.test_matrix_factor_confirmation_adjudication import prospective
        from tests.test_matrix_factor_confirmation_default_integration import _selected_records
        selected_owner = operation_bindings
        draft, qualifications = prospective(case)
        root = draft.prospective_draft
        campaign = replace(root.campaign,
            budget=ResourceBudget.aggregate(row.resource_budget for row in draft.operations),
            authority_policy=ObjectIdentity.from_record(root.system.authority_policy.policy_id,
                root.system.authority_policy))
        draft = replace(draft, campaign=campaign, prospective_draft=replace(root, campaign=campaign))
        by_fingerprint = _selected_records(draft, case[2])
        input_records = tuple((external.input_id,
            by_fingerprint[external.payload_schema, external.expected_content_sha256])
            for external in draft.external_inputs)
    declarations = selected_owner.operation_declarations()
    registry = CapabilityRegistry('registry.disclosed.e1-preflight', tuple(sorted(
        (value.manifest() for value in declarations), key=lambda value: value.registry_id)))
    implementation = implementation_binding(ROOT)
    compiled = compile_recursive_wave(draft=draft,
        registrations=tuple(value.registration() for value in declarations), registry=registry,
        implementation_commit=implementation.observed_git_head, qualifications=qualifications,
        known_design_inputs=draft.prospective_draft.design_inputs,
        output_codecs={key: value for declaration in declarations for key, value in declaration.record_codecs.items()})
    # Prospective compilation deliberately stops at an authority-pending
    # candidate. The existing compiler's preissue branch lowers its graph for
    # this PURE readiness control without creating an issued study or grants.
    candidate = compiled.candidate_report.candidate
    assert candidate is not None, compiled.candidate_report.diagnostics
    run = compile_run_plan(run_plan_id='run.disclosed.e1-preflight', campaign=candidate.campaign,
        system=candidate.system, experiment=candidate.experiment, template=candidate.protocol,
        scientific_graph=candidate.scientific_graph,
        candidate=ObjectIdentity.from_record(candidate.candidate_id, candidate), registry=registry,
        implementation_commit=implementation.observed_git_head, frozen_proposal=None, authorization=None,
        approval_service=None, preissue_candidate=candidate)
    compiled = replace(compiled, run_plan=run, execution_plan=lower_run_plan(run, registry))
    task = next(value for value in compiled.execution_plan.tasks if value.task_id.endswith('.history'))
    if input_access_changes:
        changes = dict(input_access_changes)
        task = replace(task,
            external_inputs=tuple(replace(row, expected_outcome_access=changes[row.input_id])
                if row.input_id in changes else row for row in task.external_inputs),
            scientific_inputs=tuple(replace(row, outcome_access=changes[row.consumer_input_id])
                if row.consumer_input_id in changes else row for row in task.scientific_inputs))
        compiled = replace(compiled, execution_plan=replace(compiled.execution_plan,
            tasks=tuple(task if row.task_id == task.task_id else row for row in compiled.execution_plan.tasks)))
    values = dict(input_records)
    by_id = {external.logical_artifact_id: values[external.input_id] for external in draft.external_inputs}
    configuration = next(value.record for value in compiled.config_inputs if value.node_id == task.task_id)
    by_id[task.capability.config.artifact_id] = configuration
    dependency, = (edge for edge in task.scientific_inputs if edge.external_input_id is None)
    if compact:
        commitment = records.commitment_for(selected.manifest, records.sources_for_manifest(selected.manifest))
    else:
        from empirical_lawhood.adapters.methods.matrix_factor_confirmation.commitment import committed
        commitment_config = next(row.record for row in compiled.config_inputs
            if row.node_id == selected_owner.COMMIT_KEY)
        commitment = committed(commitment_config)
    by_id[dependency.operational_logical_artifact_id] = commitment
    external_ids = {value.logical_artifact_id for value in task.external_inputs}
    selected_ids = external_ids | {value.operational_logical_artifact_id for value in task.scientific_inputs}
    specifications = {row.logical_artifact_id: row for row in task.external_inputs}
    verified = []
    for index, logical_id in enumerate(sorted(selected_ids)):
        value = by_id[logical_id]
        access = (specifications[logical_id].expected_outcome_access if logical_id in specifications
            else OutcomeAccess.OUTCOME_BLIND)
        published = plane.write(ArtifactWriteRequest(logical_id, f'e1-preflight/{index:03}.json', value.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', 'control.disclosed.e1-preflight',
            'e1-preflight', value.canonical_bytes(), VisibilityCeiling.PROSPECTIVE, (), access))
        verified.append(VerifiedArtifactInput(published.logical, published.materialization))
    verified = tuple(sorted(verified, key=lambda value: value.artifact_id))
    bindings = tuple(WorkerInputBinding.from_verified(value, kind=WorkerInputKind.EXTERNAL
        if value.artifact_id in external_ids else WorkerInputKind.DEPENDENCY) for value in verified)
    ports = plane.open_many(verified, bindings=bindings, maximum_bytes=None)
    commit, = (value for value in bindings if value.kind is WorkerInputKind.DEPENDENCY)
    dependencies = (DependencyReceiptBinding('receipt.disclosed.e1-commit', selected_owner.COMMIT_KEY,
        (commit.materialization_id,)),)
    context = TaskContext(compiled.execution_plan.source_plan.object_id, task.task_id, 'attempt.disclosed.e1-history',
        task.capability.config, bindings, ports, tuple(WorkerOutputPort(value.output_id, value.payload_schema,
            value.profile, value.media_type, value.logical_artifact_id) for value in task.outputs),
        task.capability.required_permissions, task.capability.requested_outcome_access,
        task.capability.requested_resources, WorkerIsolationProfile.TRUSTED_LOCAL, dependencies)
    return compiled, task, context, verified, implementation, configuration.source


def _prepare(compiled, task, context, verified, implementation, selected_owner):
    staged = selected_owner.native_runner()
    assert type(staged) is ParentPreparedTaskRunner
    initial = lifecycle.prepare_worker_invocation(staged, context, verified, implementation=implementation,
        execution_plan=ObjectIdentity.from_record(compiled.execution_plan.execution_plan_id, compiled.execution_plan),
        execution_task=ObjectIdentity.from_record(task.task_id, task), execution_task_record=task,
        native_effect=True, provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,),
        native_work_preparer=selected_owner.prepare_native_work)
    assert initial.native_work is None and initial.native_preparation_error is None
    runner, bound, prepared = lifecycle._prepare_parent_native_runner(staged, context, initial,
        selected_owner.prepare_native_work)
    return runner, bound, prepared


def test_e1_actual_graph_has_only_direct_native_operands_and_strict_worker_refuses_mutations(
        monkeypatch, request, provenance):  # noqa: F811
    from tests import test_matrix_factor_confirmation_history as history_fixture
    original = history_fixture.parameter_source
    monkeypatch.setattr(history_fixture, 'parameter_source', lambda: replace(original(), provenance=provenance))
    for name, value in selected_worker_environment():
        monkeypatch.setenv(name, value)
    def forbidden(*args, **kwargs):
        raise AssertionError('PURE preparation/readiness entered the native producer')
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_source
    monkeypatch.setattr(parameter_source, 'acquire_parameter_history', forbidden)
    with threadpool_limits(limits=1):
        case = request.getfixturevalue('e1')
        compiled, task, context, verified, implementation, source = _context(case)
        try:
            runner, context, prepared = _prepare(compiled, task, context, verified, implementation, owner)
            assert prepared.native_preparation_error is None
            definition, = prepared.native_definitions
            assert definition.operation_id == records.NATIVE_HISTORY_OPERATION
            assert definition.sources == records.native_history_sources(source, definition.operation_id)
            assert source.manifest not in definition.sources
            assert all(sum((row.logical.payload_schema, row.logical.content_sha256) ==
                (pin.object_schema, pin.object_fingerprint) for row in prepared.inputs) == 1
                for pin in (definition.configuration, *definition.sources, *definition.streams))
            ready = lifecycle._worker_preflight(runner, context, prepared, (MATRIX_PROVENANCE_REQUIREMENT,),
                native_work_preparer=owner.prepare_native_work)
            assert ready.ready, tuple((value.operand_id, value.reason) for value in ready.mismatches)
            # Historical v1's undeclared manifest is still rejected by the
            # generic direct-input guard; the repair does not weaken it.
            legacy = replace(definition, operation_id=records.NATIVE_HISTORY_OPERATION_V1,
                sources=records.native_history_sources(source, records.NATIVE_HISTORY_OPERATION_V1))
            wrong = replace(prepared, native_work=replace(prepared.native_work, definitions=(legacy,),
                rosters=(replace(prepared.native_work.rosters[0], subworks=(legacy.identity,)),)))
            stopped = lifecycle._worker_preflight(runner, context, wrong, (MATRIX_PROVENANCE_REQUIREMENT,),
                native_work_preparer=owner.prepare_native_work)
            assert not stopped.ready and any(value.operand_id == source.manifest.object_id for value in stopped.mismatches)
            substituted = replace(definition, sources=tuple(sorted((replace(definition.sources[0],
                object_fingerprint='e'*64), *definition.sources[1:]), key=lambda value: value.object_id)))
            wrong = replace(prepared, native_work=replace(prepared.native_work, definitions=(substituted,),
                rosters=(replace(prepared.native_work.rosters[0], subworks=(substituted.identity,)),)))
            stopped = lifecycle._worker_preflight(runner, context, wrong, (MATRIX_PROVENANCE_REQUIREMENT,),
                native_work_preparer=owner.prepare_native_work)
            assert not stopped.ready and any('unique authenticated worker input' in value.reason for value in stopped.mismatches)
            # The prepared invocation rejects an incomplete worker context
            # before preflight or native entry can consume an operand.
            for removed in (source.provenance.object_schema, records.E1CompactSource.SCHEMA):
                remaining = tuple(value for value in context.input_ports if value.payload_schema != removed)
                remaining_ids = {value.artifact_id for value in remaining}
                with pytest.raises(ValueError, match='prepared invocation changes its complete worker context'):
                    replace(context, input_ports=remaining,
                        input_bindings=tuple(value for value in context.input_bindings if value.artifact_id in remaining_ids))
        finally:
            for port in context.input_ports:
                port.close()


@pytest.fixture
def actual_e1_case(monkeypatch, request, provenance):  # noqa: F811
    from tests import test_matrix_factor_confirmation_history as history_fixture
    original = history_fixture.parameter_source
    monkeypatch.setattr(history_fixture, 'parameter_source', lambda: replace(original(), provenance=provenance))
    for name, value in selected_worker_environment():
        monkeypatch.setenv(name, value)
    def forbidden(*args, **kwargs):
        raise AssertionError('configuration readiness entered native science')
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_source
    monkeypatch.setattr(parameter_source, 'acquire_parameter_history', forbidden)
    with threadpool_limits(limits=1):
        yield request.getfixturevalue('e1')


def _selected_owner(compact):
    if compact:
        return owner
    from empirical_lawhood.adapters.methods.matrix_factor_confirmation import operation_bindings
    return operation_bindings


@pytest.mark.parametrize('compact', (True, False), ids=('compact', 'ordinary'))
def test_actual_e1_staged_history_authenticates_sealed_config_and_blind_four_streams(actual_e1_case, compact):
    selected_owner = _selected_owner(compact)
    compiled, task, context, verified, implementation, source = _context(actual_e1_case, compact=compact)
    try:
        declaration = next(row for row in selected_owner.operation_declarations()
            if row.capability_key == selected_owner.NAMESPACE+'.history')
        assert type(declaration.runner_factory()) is ParentPreparedTaskRunner
        runner, context, prepared = _prepare(compiled, task, context, verified, implementation, selected_owner)
        assert prepared.native_preparation_error is None
        configuration, = (port for port in context.input_ports if port.artifact_id == context.config.artifact_id)
        assert configuration.outcome_access is OutcomeAccess.EVALUATION_SEALED
        assert configuration.visibility_ceiling is VisibilityCeiling.PROSPECTIVE
        assert all(port.outcome_access is OutcomeAccess.OUTCOME_BLIND
            for port in context.input_ports if port is not configuration)
        config, actual, _, _ = selected_owner._decode(context, 'history')
        assert actual == source and config.source == source
        assert sum(port.payload_schema.endswith('/seed') for port in context.input_ports) == 4
        ready = lifecycle._worker_preflight(runner, context, prepared, (MATRIX_PROVENANCE_REQUIREMENT,),
            native_work_preparer=selected_owner.prepare_native_work)
        assert ready.ready, tuple((row.operand_id, row.reason) for row in ready.mismatches)
    finally:
        for port in context.input_ports:
            port.close()


@pytest.mark.parametrize('compact', (True, False), ids=('compact', 'ordinary'))
@pytest.mark.parametrize('operand,access', (
    ('config', OutcomeAccess.OUTCOME_BLIND),
    ('source', OutcomeAccess.EVALUATION_SEALED),
    ('streams.autonomous-coarse-driver', OutcomeAccess.EVALUATION_SEALED),
))
def test_actual_e1_history_refuses_mislabeled_config_or_exposed_scientific_operand(
        actual_e1_case, compact, operand, access):
    selected_owner = _selected_owner(compact)
    compiled, task, context, verified, implementation, _ = _context(actual_e1_case,
        compact=compact, input_access_changes=((operand, access),))
    try:
        runner, context, prepared = _prepare(compiled, task, context, verified, implementation, selected_owner)
        assert prepared.native_preparation_error is not None
        assert ('configuration custody' if operand == 'config' else 'source operands' if operand.startswith('streams.')
            else 'full-history source') in prepared.native_preparation_error
        stopped = lifecycle._worker_preflight(runner, context, prepared, (MATRIX_PROVENANCE_REQUIREMENT,),
            native_work_preparer=selected_owner.prepare_native_work)
        assert not stopped.ready and prepared.native_work is None
    finally:
        for port in context.input_ports:
            port.close()


@pytest.mark.parametrize('compact', (True, False), ids=('compact', 'ordinary'))
@pytest.mark.parametrize('damage', ('missing', 'foreign'))
def test_actual_e1_bound_decoder_refuses_missing_or_foreign_config_before_operand_reads(
        actual_e1_case, compact, damage):
    selected_owner = _selected_owner(compact)
    compiled, task, context, verified, implementation, _ = _context(actual_e1_case, compact=compact)
    try:
        _, context, prepared = _prepare(compiled, task, context, verified, implementation, selected_owner)
        assert prepared.native_preparation_error is None
        edge, = (row for row in task.scientific_inputs if row.scientific_role is ScientificInputRole.CONFIGURATION)
        scientific = tuple(row for row in task.scientific_inputs if row is not edge)
        additions = () if damage == 'missing' else (replace(edge, external_input_id='compiler.configuration.foreign'),)
        changed = replace(task, scientific_inputs=tuple(sorted((*scientific, *additions), key=lambda row: row.edge_id)))
        changed_contract = replace(prepared, native_work=None,
            execution_task=ObjectIdentity.from_record(changed.task_id, changed), execution_task_record=changed)
        changed_context = replace(context, prepared_invocation=changed_contract)
        before = tuple(port.bytes_read for port in context.input_ports)
        with pytest.raises(ValueError, match='CONFIGURATION'):
            selected_owner._decode(changed_context, 'history')
        assert tuple(port.bytes_read for port in context.input_ports) == before
    finally:
        for port in context.input_ports:
            port.close()
