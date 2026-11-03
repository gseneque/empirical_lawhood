# SPDX-License-Identifier: MPL-2.0
"""Unexecuted metadata controls for the unfinished-only public E3 selection.

These fixtures confer no real receipt, source or scientific authority.
"""
from dataclasses import fields, replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_composition as composition
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_lowering import lower_protected_matrix_response_error, selected_configs, task_id, operation_class
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_execution import source_binding
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_preparation import ConfiguredE3UnfinishedPreparationSelection, retained_file_versions
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_unfinished_execution import ConfiguredE3CompletedOutput, ConfiguredE3UnfinishedExecution
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.execution_envelope import RunExecutionResourceEnvelope
from tests.test_matrix_e3_retained_continuation import continuation_case, public_case, _changed_source, _unexecuted_receipt, _pin  # noqa: F401


@pytest.fixture(scope='module')
def unfinished_case(continuation_case):  # noqa: F811
    case = continuation_case
    configs = selected_configs(case.original.specification, case.original.allocation, case.selection)
    complete = [row for row in configs if operation_class(row) in ('prefix', 'numerical', 'measure', 'check',
        'project', 'feature', 'physical-forecast', 'fit', 'model-freeze') or
        operation_class(row) == 'forecast' and getattr(getattr(row, 'original_config', row), 'mode', None) == 'calibration']
    declarations = {row.capability_key: row for row in composition.operation_declarations()}
    previous = source_binding(case.retention.response_provenance)
    all_rows = {task_id(row): _unexecuted_receipt(row, declarations[composition._declaration_key(row)],
        previous, case.retention.continued_run_id) for row in configs}
    rows = {task_id(row): all_rows[task_id(row)] for row in complete}
    remaining = {task_id(row) for row in configs} - set(rows)
    boundary = {(edge.producer_node_id, edge.producer_output_id.rsplit('.', 1)[-1]) for edge in case.lowered.draft.links
        if edge.consumer_node_id in remaining and edge.producer_node_id in rows}
    imports = []
    for node, port in sorted(boundary):
        task, receipt, _ = rows[node]
        output, = (row for row in task.outputs if row.output_id.rsplit('.', 1)[-1] == port)
        logical, = (row for row in receipt.output_logical_artifacts if row.logical_artifact_id == output.logical_artifact_id)
        materialization, = (row for row in receipt.output_materializations if row.logical_artifact_id == output.logical_artifact_id)
        imports.append(ConfiguredE3CompletedOutput(node, output.output_id,
            ObjectIdentity.from_record(receipt.receipt_id, receipt), logical, materialization))
    retention = replace(case.retention, record_id='retention.unexecuted.unfinished',
        continued_run_id='run.unexecuted.unfinished', response_provenance=replace(
            _changed_source(case.retention.response_provenance), observed_git_head='c' * 40))
    scope = ConfiguredE3UnfinishedExecution('unfinished.unexecuted', 'unexecuted/continued', case.retention.continued_run_id,
        case.retention.original_package, case.retention.original_plan, case.retention.original_terminal,
        _pin('resources.unexecuted', RunExecutionResourceEnvelope), case.retention.original_reveal_authority,
        previous, retention, tuple((node, ObjectIdentity.from_record(row[1].receipt_id, row[1])) for node, row in sorted(rows.items())),
        tuple(sorted(remaining)), tuple(imports))
    selection = ConfiguredE3UnfinishedPreparationSelection(**{field.name: getattr(case.selection, field.name)
        for field in fields(case.selection) if field.name not in ('retention', 'retained_tasks')},
        retention=retention, retained_tasks=tuple(replace(row, continuation=retention.identity) for row in case.retained), unfinished=scope)
    lowered = lower_protected_matrix_response_error(case.original.specification, case.original.allocation, selection)
    return SimpleNamespace(previous=case, selection=selection, lowered=lowered, scope=scope,
        predecessor_tasks=tuple(row[0] for _, row in sorted(all_rows.items())),
        predecessor_receipts={key: row[1] for key, row in rows.items()})


@pytest.mark.parametrize('revoke_at', (None, 1, 2))
def test_unfinished_projection_refreshes_access_without_whole_history_checks(unfinished_case, monkeypatch, revoke_at):
    from empirical_lawhood.api import configured_e3_unfinished_custody as owner

    case, expected = unfinished_case, unfinished_case.scope
    values = {field.name: None for field in fields(owner.UnfinishedE3Custody)}
    pins = {}
    # Same disclosed typed task/receipt operands as the complete compiler test.
    # Surrounding source selectors are supplied pins, not claimed real custody.
    for name, field, pin in (
            ('package', 'package_id', expected.predecessor_package),
            ('plan', 'execution_plan_id', expected.predecessor_plan),
            ('terminal', 'terminal_event_id', expected.predecessor_terminal),
            ('reveal', 'authority_id', expected.predecessor_reveal_authority),
            ('envelope', 'envelope_id', expected.predecessor_resource_envelope)):
        record = SimpleNamespace(**{field: pin.object_id})
        values[name] = record
        pins[id(record)] = pin
    original_pin = owner._pin
    def supplied_pin(record, field='record_id'):
        if id(record) in pins:
            assert getattr(record, field) == pins[id(record)].object_id
            return pins[id(record)]
        return original_pin(record, field)
    monkeypatch.setattr(owner, '_pin', supplied_pin)
    values['package'].run_plan_id = expected.predecessor_run_id
    values['plan'].tasks = case.predecessor_tasks
    accesses = []
    def access():
        accesses.append(1)
        if len(accesses) == revoke_at:
            raise PermissionError('disclosed current access revoked')
    values.update(directory=expected.predecessor_authoring_directory,
        selection=case.previous.selection, specification=case.previous.original.specification,
        allocation=case.previous.original.allocation, receipts=case.predecessor_receipts,
        require_access=access, require_current=lambda: pytest.fail('pure projection rehashed the whole history'))
    custody = owner.UnfinishedE3Custody(**values)
    def project():
        return custody.unfinished(record_id=expected.record_id, retention=expected.retention)
    if revoke_at is not None:
        with pytest.raises(PermissionError, match='revoked'):
            project()
    else:
        assert project().canonical_bytes() == expected.canonical_bytes()
        assert len(accesses) == 2


def test_unfinished_compiler_keeps_completed_work_out_of_execution(unfinished_case):
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_preparation import (
        _source_projection, derive_protected_e3_design_inputs,
    )
    from empirical_lawhood.api.derived_metadata_access import _semantic_access
    from empirical_lawhood.api.recursive_operations import operation_catalog
    from empirical_lawhood.planning.experiment_entry import StudyDefinition
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
    case = unfinished_case
    scope = case.scope
    assert decode_canonical_bytes(scope.canonical_bytes(), type(scope), maximum_bytes=None) == scope
    lowered, selection = case.lowered, case.selection
    assert set(lowered.draft.selected_operation_ids) == set(scope.unfinished_task_ids)
    assert set(lowered.draft.selected_operation_ids).isdisjoint(dict(scope.completed_receipts))
    assert len(lowered.draft.operations) == len(case.previous.lowered.draft.operations)
    assert {row.task_id for row in lowered.resource_selection.task_cells} == set(scope.unfinished_task_ids)
    records = dict(lowered.input_records)
    versions = {key: value.record_version for key, value in case.previous.original.files.items()}
    versions.update(retained_file_versions(selection))
    sources, qualifications = [], []
    specification = case.previous.original.specification
    operator = ObjectIdentity.from_record(specification.specification_id + '.measurement', specification.measurement)
    for external in lowered.draft.external_inputs:
        if external.input_id in records:
            versions[external.logical_artifact_id] = records[external.input_id].VERSION
        source, qualification = _semantic_access(external=external, root=lowered.draft.prospective_draft,
            version=versions[external.logical_artifact_id], observation_operator=operator)
        sources.append(source)
        qualifications.append(qualification)
    selection = replace(selection, source_configs=tuple(sources), qualifications=tuple(sorted(qualifications, key=lambda row: row.receipt_id)))
    draft = _source_projection(lowered.draft, selection, versions)
    registrations, registry, codecs = operation_catalog()
    source = source_binding(selection.retention.response_provenance)
    result = compile_recursive_wave(draft=draft, registrations=registrations, registry=registry, output_codecs=codecs,
        implementation_commit=source.observed_git_head, implementation_sha256=source.fingerprint(),
        qualifications=selection.qualifications, known_design_inputs=draft.prospective_draft.design_inputs)
    assert result.candidate_report.candidate is not None, result.candidate_report.diagnostics
    assert result.execution_plan is None  # Prospective compilation has not been issued.
    assert {row.node_id for row in result.operations} == set(scope.unfinished_task_ids)
    assert result.candidate_draft == draft.prospective_draft, tuple(
        field.name for field in fields(result.candidate_draft)
        if getattr(result.candidate_draft, field.name) != getattr(draft.prospective_draft, field.name))
    design = derive_protected_e3_design_inputs(SimpleNamespace(
        draft=draft, design_records=((selection.selection_id, selection),)))
    # Exercise the actual prospective authoring boundary, not just lowering.
    study = StudyDefinition('study.unexecuted.unfinished', result.candidate_draft, design.entry_package)
    assert study.draft == draft.prospective_draft
    assert {row.selection_id for row in study.draft.capability_selections} == {
        row.selection.selection_id for row in result.operations}


@pytest.mark.parametrize('contact', ('entered', 'returned', 'uncertain'))
def test_unfinished_transition_refuses_every_native_contact(contact):
    from empirical_lawhood.api.configured_e3_unfinished_custody import _require_unentered
    store = SimpleNamespace(read=lambda run, task: contact if task == 'pending.native' else None)
    with pytest.raises(PermissionError, match='prior native contact'):
        _require_unentered(store, 'run.unexecuted', ('completed.pure', 'pending.native'))


@pytest.mark.parametrize('damage', (None, 'access', 'visibility', 'bytes', 'producer'))
def test_imported_operand_keeps_actual_receipt_bytes_and_access(unfinished_case, damage):
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_unfinished_execution import require_imported_input
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.runtime.execution import WorkerInputKind
    scope = unfinished_case.scope
    imported = scope.imported_outputs[0]
    logical, physical = imported.logical, imported.materialization
    port = SimpleNamespace(artifact_id=logical.logical_artifact_id, payload_schema=logical.payload_schema,
        media_type=logical.media_type, size_bytes=physical.size_bytes, outcome_access=logical.outcome_access,
        visibility_ceiling=logical.visibility_ceiling, kind=WorkerInputKind.EXTERNAL)
    bound = SimpleNamespace(artifact_id=port.artifact_id, logical=logical, physical_sha256=physical.physical_sha256)
    context = SimpleNamespace(prepared_invocation=SimpleNamespace(inputs=(bound,)))
    if damage == 'access':
        port.outcome_access = OutcomeAccess.PRIVILEGED_TRUTH
    elif damage == 'visibility':
        port.visibility_ceiling = VisibilityCeiling.PRIVILEGED_TRUTH
    elif damage == 'bytes':
        bound.physical_sha256 = '0' * 64
    elif damage == 'producer':
        port.kind = WorkerInputKind.DEPENDENCY
    if damage is None:
        assert require_imported_input(scope, context, port, imported.task_id, imported.output_id)
    else:
        with pytest.raises(ValueError, match='receipted input'):
            require_imported_input(scope, context, port, imported.task_id, imported.output_id)


@pytest.mark.parametrize('damage', (None, 'repeated-task', 'missing-task', 'missing-predecessor', 'revoked'))
def test_incomplete_reader_keeps_receipts_under_their_producing_plan(unfinished_case, damage):
    from empirical_lawhood.api.configured_e3_incomplete_read import _receipt_sources
    from empirical_lawhood.api.configured_e3_retained_read import RetainedE3Read

    case = unfinished_case
    current_tasks = tuple(row for row in case.predecessor_tasks if row.task_id in case.scope.unfinished_task_ids)
    original_tasks = current_tasks
    if damage == 'repeated-task':
        current_tasks += (next(row for row in case.predecessor_tasks if row.task_id in case.predecessor_receipts),)
    elif damage == 'missing-task':
        current_tasks = current_tasks[:-1]
    accesses = []
    def access():
        accesses.append('current-predecessor-access')
        if damage == 'revoked':
            raise PermissionError('predecessor access revoked')
    previous = SimpleNamespace(writer=object(), plan=SimpleNamespace(tasks=case.predecessor_tasks),
        receipts=case.predecessor_receipts, require_access=access)
    retained = RetainedE3Read(case.scope.retention, None,
        {row.original_task.task_id: row for row in case.selection.retained_tasks}, case.scope,
        None if damage == 'missing-predecessor' else previous)
    writer, plan, receipts = object(), SimpleNamespace(tasks=current_tasks), {}
    package = SimpleNamespace(run_plan_id=case.scope.retention.continued_run_id)
    if damage is not None:
        with pytest.raises(PermissionError, match='UNFINISHED_TASK_CENSUS|revoked'):
            _receipt_sources(writer=writer, package=package, plan=plan, receipts=receipts, retained=retained)
        return
    sources = _receipt_sources(writer=writer, package=package, plan=plan, receipts=receipts, retained=retained)
    assert len(sources) == 2 and accesses == ['current-predecessor-access']
    assert all(actual is expected for actual, expected in zip(sources[0],
        (previous.writer, previous.plan, previous.receipts), strict=True))
    assert all(actual is expected for actual, expected in zip(sources[1], (writer, plan, receipts), strict=True))
    assert plan.tasks == original_tasks and receipts == {}
    assert all(row.run_id == case.scope.predecessor_run_id for row in sources[0][2].values())
