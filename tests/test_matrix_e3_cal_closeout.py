# SPDX-License-Identifier: MPL-2.0
"""Disclosed closeout software controls; no authentic science or authority.

The graph uses hypothetical receipts, as the existing continuation controls do.
Separate real-store controls retain literal UNKNOWN contacts without execution.
"""
from dataclasses import fields, replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_composition as composition
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_closeout_execution import (
    ConfiguredE3CALRootCloseout, ConfiguredE3ClosedExecution, ConfiguredE3MissingOutcomeProducts,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_lowering import lower_protected_matrix_response_error, selected_configs, task_id
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_execution import source_binding
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_preparation import ConfiguredE3ClosedPreparationSelection
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_unfinished_execution import ConfiguredE3CompletedOutput
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.execution_envelope import RunExecutionResourceEnvelope
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.recovery import RunRecoveryIndex
from tests.test_matrix_e3_unfinished_continuation import (
    unfinished_case, continuation_case, public_case, _changed_source, _unexecuted_receipt, _pin,  # noqa: F401
    test_unfinished_compiler_keeps_completed_work_out_of_execution as check_compiler,
)
from tests.recovery_support import case as resource_case  # noqa: F401


@pytest.fixture(scope='module')
def closeout_case(unfinished_case):  # noqa: F811
    old = unfinished_case
    original = old.previous.original
    configs = selected_configs(original.specification, original.allocation, old.selection)
    declarations = {row.capability_key: row for row in composition.operation_declarations()}
    source = source_binding(old.scope.retention.response_provenance)
    actual = {task_id(row): _unexecuted_receipt(row, declarations[composition._declaration_key(row)],
        source, old.scope.retention.continued_run_id) for row in configs}
    cal = [row for row in configs if getattr(row, 'operation', None) == 'responses'
        and row.source.root.root.role.value == 'CALIBRATION']
    assert len(cal) > 2
    completed = dict(old.predecessor_receipts)
    roots = []
    excluded = set()
    for ordinal, config in enumerate(cal):
        root = config.source.root.root
        node = task_id(config)
        score_node = node.removesuffix('.responses') + '.response-score'
        if ordinal < 2:
            completed[node], completed[score_node] = actual[node][1], actual[score_node][1]
        else:
            excluded.add(node)
        roots.append(ConfiguredE3CALRootCloseout(root.root_id, root.independent_group_id,
            ObjectIdentity.from_record(config.config_id, config), _pin('contact.' + root.root_id, NativeEffectContact),
            None if ordinal >= 2 else ObjectIdentity.from_record(completed[node].receipt_id, completed[node]),
            None if ordinal >= 2 else ObjectIdentity.from_record(completed[score_node].receipt_id, completed[score_node]),
            _pin('missing.' + root.root_id, ConfiguredE3MissingOutcomeProducts) if ordinal >= 2 else None,
            1234 if ordinal >= 2 else None, VisibilityCeiling.DEVELOPMENT_ONLY))
    pending = {task_id(row) for row in configs} - set(completed) - excluded
    missing_scores = {row.outcome_task_id for row in roots if row.missing_products is not None}
    imports = []
    boundary = {(edge.producer_node_id, edge.producer_output_id.rsplit('.', 1)[-1])
        for edge in old.previous.lowered.draft.links if edge.consumer_node_id in pending - missing_scores
        and edge.producer_node_id in completed}
    task_map = {row.task_id: row for row in old.predecessor_tasks}
    for node, port in sorted(boundary):
        receipt = completed[node]
        task = task_map[node] if node in old.predecessor_receipts else actual[node][0]
        output, = (row for row in task.outputs if row.output_id.rsplit('.', 1)[-1] == port)
        logical, = (row for row in receipt.output_logical_artifacts if row.logical_artifact_id == output.logical_artifact_id)
        materialization, = (row for row in receipt.output_materializations if row.logical_artifact_id == output.logical_artifact_id)
        imports.append(ConfiguredE3CompletedOutput(node, output.output_id,
            ObjectIdentity.from_record(receipt.receipt_id, receipt), logical, materialization))
    retention = replace(old.scope.retention, record_id='retention.unexecuted.closed', continued_run_id='run.unexecuted.closed',
        response_provenance=replace(_changed_source(old.scope.retention.response_provenance), observed_git_head='d' * 40))
    scope = ConfiguredE3ClosedExecution('closeout.unexecuted', 'unexecuted/unfinished', old.scope.retention.continued_run_id,
        old.scope.predecessor_package, old.scope.predecessor_plan, old.scope.predecessor_terminal,
        _pin('resources.unexecuted.closeout', RunExecutionResourceEnvelope), old.scope.predecessor_reveal_authority,
        source, retention, tuple((node, ObjectIdentity.from_record(receipt.receipt_id, receipt)) for node, receipt in sorted(completed.items())),
        tuple(sorted(pending)), tuple(imports), _pin('index.unexecuted.closeout', RunRecoveryIndex), 'a' * 64,
        old.scope, tuple(sorted(original.allocation.unit_ids('calibration'))),
        tuple(sorted(roots, key=lambda row: row.root_id)))
    selection = ConfiguredE3ClosedPreparationSelection(**{field.name: getattr(old.selection, field.name)
        for field in fields(old.selection) if field.name not in ('retention', 'retained_tasks', 'unfinished')},
        retention=retention, retained_tasks=tuple(replace(row, continuation=retention.identity) for row in old.selection.retained_tasks),
        closeout=scope)
    lowered = lower_protected_matrix_response_error(original.specification, original.allocation, selection)
    return SimpleNamespace(previous=old.previous, scope=scope, selection=selection, lowered=lowered)


def test_closed_cal_compiles_only_missingness_and_original_confirmation(closeout_case):
    case = closeout_case
    check_compiler(case)
    selected = {op.node_id: op for op in case.lowered.draft.operations if op.node_id in case.lowered.draft.selected_operation_ids}
    native = {node for node, op in selected.items() if op.selection.capability_key.endswith('.continued-responses')}
    roots = {row.root_id for row in case.selection.sources if row.root.root.role.value == 'CONFIRMATION'}
    assert native == {'matrix-e3-configured-protected.' + root + '.responses' for root in roots}
    assert all(row.native_task_id not in selected for row in case.scope.calibration_roots)
    assert sum(op.selection.capability_key.endswith('.missing-response-score') for op in selected.values()) == len(case.scope.excluded_native_task_ids)
    assert sum(cell.physical_execution_cost for cell in case.lowered.resource_selection.task_cells) == len(roots)
    assert decode_canonical_bytes(case.scope.canonical_bytes(), type(case.scope), maximum_bytes=None) == case.scope


def test_closed_resource_envelope_keeps_only_confirmation_demand(closeout_case):
    from empirical_lawhood.runtime.execution_envelope import ExecutionResourceEnvelopeSpec
    from empirical_lawhood.runtime.study_issue import IssuedExtensionSet

    case = closeout_case
    resources = case.lowered.resource_selection
    original = case.previous.lowered.resource_selection
    original_bytes = original.canonical_bytes()
    values = {field.name: getattr(resources, field.name) for field in fields(resources)}
    # Only the strict envelope's resource arithmetic is under test. This
    # disclosed extension identity is not an issued study or execution grant.
    envelope = ExecutionResourceEnvelopeSpec(**values,
        issued_study_extensions=_pin('extensions.unexecuted.closeout', IssuedExtensionSet))
    roots = {row.root.root.independent_group_id for row in case.selection.sources
        if row.root.root.role.value == 'CONFIRMATION'}
    capacity, = envelope.child_token_limits
    assert capacity.physical_execution_token_limit == len(roots)
    assert capacity.retry_token_limit == 0
    native = {row.physical_independent_unit_id for row in envelope.task_cells if row.native_simulator_launch}
    assert native == roots
    old_cells = {row.task_id: row for row in original.task_cells}
    assert all(row == old_cells[row.task_id] for row in envelope.task_cells)
    assert all(getattr(envelope, field.name) == getattr(original, field.name)
        for field in fields(resources) if field.name not in ('task_cells', 'child_token_limits'))
    assert original.canonical_bytes() == original_bytes
    for wrong in (capacity.physical_execution_token_limit - 1, capacity.physical_execution_token_limit + 1):
        with pytest.raises(ValueError, match='exact maximum demand'):
            replace(envelope, child_token_limits=(replace(capacity, physical_execution_token_limit=wrong),))


@pytest.mark.parametrize('damage', ('redispatch', 'drop-root', 'drop-unit', 'invent-receipt', 'change-history'))
def test_closeout_refuses_changed_missingness_and_original_denominators(closeout_case, damage):
    scope = closeout_case.scope
    unknown = next(row for row in scope.calibration_roots if row.missing_products is not None)
    with pytest.raises((TypeError, ValueError)):
        if damage == 'redispatch':
            replace(scope, unfinished_task_ids=tuple(sorted((*scope.unfinished_task_ids, unknown.native_task_id))))
        elif damage == 'drop-root':
            replace(scope, calibration_roots=tuple(row for row in scope.calibration_roots if row is not unknown))
        elif damage == 'drop-unit':
            replace(scope, calibration_units=scope.calibration_units[:-1])
        elif damage == 'invent-receipt':
            receipt = scope.completed_receipts[0][1]
            replace(unknown, response_receipt=receipt)
        else:
            replace(scope, completed_receipts=scope.completed_receipts[1:])


def test_closed_selection_cannot_enter_original_no_contact_projection(closeout_case):
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_preparation import ConfiguredE3UnfinishedPreparationSelection
    case = closeout_case
    with pytest.raises(ValueError, match='source continuation'):
        ConfiguredE3UnfinishedPreparationSelection(**{field.name: getattr(case.selection, field.name)
            for field in fields(case.selection) if field.name != 'closeout'}, unfinished=case.scope)


def test_closeout_preserves_absent_terminal_with_exact_original_controls(closeout_case):
    scope = replace(closeout_case.scope, predecessor_terminal=None)
    assert decode_canonical_bytes(scope.canonical_bytes(), type(scope), maximum_bytes=None) == scope
    assert scope.predecessor_terminal is None
    with pytest.raises(ValueError, match='custody contracts'):
        replace(scope.original_boundary, predecessor_terminal=None)
    for name in ('predecessor_plan', 'predecessor_package', 'predecessor_resource_envelope'):
        with pytest.raises(ValueError, match='custody contracts'):
            replace(scope, **{name: None})


@pytest.mark.parametrize('state', ('unknown', 'launched', 'reserved', 'wrong-root', 'hidden-attempt'))
def test_closeout_keeps_unknown_resource_cost_without_terminal_or_completion(resource_case, state):  # noqa: F811
    from empirical_lawhood.api.configured_e3_closeout_custody import _closed_resources
    from empirical_lawhood.runtime.execution_envelope import RunExecutionResourceEnvelopeMachine as Machine
    case = resource_case
    node, attempt = case.failed.task_id, case.failed_event.attempt_id
    common = dict(cell_id=case.envelope.spec.cell_for_task(node).cell_id,
        occurred_at_utc='2026-10-16T00:00:00Z')
    envelope = Machine.reserve(case.envelope, event_id='resource.disclosed.closeout.reserve', attempt_id=attempt, **common)
    if state != 'reserved':
        envelope = Machine.launch(envelope, event_id='resource.disclosed.closeout.launch', attempt_id=attempt, **common)
    if state in ('unknown', 'wrong-root', 'hidden-attempt'):
        envelope = Machine.unknown_completion(envelope, event_id='resource.disclosed.closeout.unknown',
            reason_code='disclosed-unknown-return', **common)
    raw = envelope.canonical_bytes()
    recovery = SimpleNamespace(reconstruct_execution_resource_envelope=lambda **kwargs: envelope)
    package = SimpleNamespace(execution_resource_envelope_spec=envelope.spec, jit_graph_signature_manifest=None)
    closure = SimpleNamespace(recovery_index=case.index, by_task={},
        operational_summaries={node: SimpleNamespace(attempt_id='foreign.attempt' if state == 'hidden-attempt' else attempt)})
    unknown = {} if state == 'wrong-root' else {node: object()}
    if state != 'unknown':
        with pytest.raises(PermissionError, match='resource'):
            _closed_resources(recovery, package, case.plan, closure, {node: SimpleNamespace(attempt_id=attempt)}, unknown)
    else:
        assert _closed_resources(recovery, package, case.plan, closure,
            {node: SimpleNamespace(attempt_id=attempt)}, unknown) is envelope
    assert envelope.canonical_bytes() == raw


@pytest.mark.parametrize('damage', (None, 'wrong-producer', 'overlap', 'omission', 'revoked'))
def test_closeout_read_preserves_three_disjoint_producing_plans(damage):
    """Literal plan stubs isolate provenance routing, not receipt authenticity."""
    from empirical_lawhood.api.configured_e3_closeout_custody import ClosedE3Custody
    from empirical_lawhood.api.configured_e3_incomplete_read import _receipt_sources

    def plan(*nodes):
        return SimpleNamespace(tasks=tuple(SimpleNamespace(task_id=node,
            capability=SimpleNamespace(config=SimpleNamespace(config_schema='disclosed.config')))
            for node in nodes))

    access_calls = []

    def access():
        access_calls.append('current-access')
        if damage == 'revoked':
            raise PermissionError('disclosed access revoked')

    old_receipts = {'old.prefix': object(), 'old.model': object()}
    old = SimpleNamespace(writer=object(), plan=plan(*old_receipts), receipts=old_receipts)
    recent_receipts = {'cal.finite.response': object(), 'cal.finite.score': object()}
    values = {field.name: None for field in fields(ClosedE3Custody)}
    values.update(writer=object(), plan=plan(*recent_receipts, 'cal.unknown.response'),
        receipts={**old_receipts, **recent_receipts}, predecessor=old, require_access=access)
    previous = ClosedE3Custody(**values)
    if damage == 'wrong-producer':
        old.plan = plan('foreign.prefix', 'foreign.model')
    elif damage == 'overlap':
        previous = replace(previous, plan=plan(*recent_receipts, 'old.prefix'))
    elif damage == 'omission':
        previous = replace(previous, plan=plan('cal.finite.response'))
    remaining = ('cal.unknown.score', 'conf.response')
    retained = SimpleNamespace(unfinished=SimpleNamespace(unfinished_task_ids=remaining), predecessor=previous)
    writer, current, receipts = object(), plan(*remaining), {}
    if damage:
        with pytest.raises(PermissionError, match='TASK_CENSUS|revoked'):
            _receipt_sources(writer=writer, package=None, plan=current, receipts=receipts, retained=retained)
    else:
        sources = _receipt_sources(writer=writer, package=None, plan=current, receipts=receipts, retained=retained)
        assert len(sources) == 3 and len(access_calls) == 2
        assert sources[0] == (old.writer, old.plan, old_receipts)
        assert sources[1] == (previous.writer, previous.plan, recent_receipts)
        assert sources[2] == (writer, current, receipts)
