# SPDX-License-Identifier: MPL-2.0
"""Actual retained PURE receipts; execution observation never opens products."""
from pathlib import Path

import pytest

from empirical_lawhood.api import experiment_execution_read as owner
from empirical_lawhood.api import recursive_execution as execution
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.runtime.artifacts import artifact_publication_commit_relative_path
from tests.test_recursive_report_projection import wave  # noqa: F401
from tests.test_recursive_report_projection import ROOT

pytestmark = pytest.mark.parametrize('wave', [2], indirect=True)


def _roots(wave):  # noqa: F811
    _, draft, _, payloads = execution.load_authored_wave(directory=wave.directory,
        artifact_writer=wave.plane, lazy_payloads=True)
    return execution._retained_plans(payloads, draft)


def test_execution_records_keep_actual_census_without_body_replay_or_dispatch(wave, monkeypatch):  # noqa: F811
    from empirical_lawhood.infrastructure import recursive_custody
    monkeypatch.setattr(recursive_custody, 'read_recursive_products',
        lambda **kwargs: pytest.fail('execution observation opened scientific products'))
    controls = []
    report = owner.read_development_execution(directory=wave.directory, artifact_writer=wave.plane,
        observe_controls=lambda index, pins: controls.append((index, pins)))
    _, plan, index = _roots(wave)
    terminal = ExternalRunRecoveryStore(wave.plane).read_terminal(index)
    assert report['execution_complete'] and report['status'] == 'SUCCEEDED'
    assert report['task_count'] == len(plan.tasks)
    assert len(report['operational_census']) == len(terminal.attempts)
    assert report['read_scope'] == 'EXECUTION_RECORDS'
    assert report['scientific_completion'] == 'DEFERRED_TO_FULL_READ'
    assert report['new_native_contact_count'] == 0
    assert len(controls) == 1 and controls[0][0] == index
    assert controls[0][1] == execution._custody_control_pins(wave.plane, index)


def test_continuation_reuses_exact_authored_controls_and_retains_final_mutation_refusal(wave):  # noqa: F811
    from empirical_lawhood.api.retained_e3_evidence import retained_e3_evidence_context
    path = wave.directory / 'execution-plan.json'
    before = path.read_bytes()
    try:
        with pytest.raises((ValueError, RuntimeError, OSError)):
            with retained_e3_evidence_context(wave.plane):
                with wave.plane.read_context() as first:
                    original = owner.load_development_execution_controls(directory=wave.directory, artifact_writer=first)
                with wave.plane.read_context() as second:
                    repeated = owner.load_development_execution_controls(directory=wave.directory, artifact_writer=second)
                    assert repeated[1] is original[1] and repeated[2] is original[2]
                    path.write_bytes(bytes([before[0] ^ 1]) + before[1:])
    finally:
        path.write_bytes(before)


def test_partial_input_namespace_is_unentered_without_changing_or_erasing_it(wave):  # noqa: F811
    from dataclasses import replace
    from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryIndex
    _, original, _ = _roots(wave)
    run_id = 'run.partial-input-control'
    plan = replace(original, source_plan=replace(original.source_plan, object_id=run_id))
    index = DevelopmentRunRecoveryIndex.from_execution_plan(plan, run_id=run_id,
        wave_id='wave.development', authority_identities=())
    path = wave.plane.root.resolve('runs/' + run_id + '/inputs/input-incomplete.json', for_write=True)
    path.parent.mkdir(parents=True)
    path.write_bytes(b'original incomplete input')
    before = path.read_bytes()
    report = owner.read_execution_records(writer=wave.plane, plan=plan, index=index)
    assert report['status'] == 'INPUTS_PARTIAL' and not report['execution_complete']
    assert report['new_native_contact_count'] == 0 and report['terminal'] is None
    assert path.read_bytes() == before
    for name in ('native-contacts', 'receipts', 'recovery'):
        foreign = path.parent.parent / name
        foreign.mkdir()
        try:
            with pytest.raises(PermissionError, match='input-only'):
                owner.read_execution_records(writer=wave.plane, plan=plan, index=index)
        finally:
            foreign.rmdir()


def test_actual_retained_runner_can_return_execution_records_without_full_read_or_dispatch(wave, monkeypatch):  # noqa: F811
    monkeypatch.setattr(execution, 'read_recursive_wave',
        lambda **kwargs: pytest.fail('execution-record runner requested a duplicate full read'))
    report = execution.run_recursive_wave(directory=wave.directory, project_root=ROOT,
        artifact_writer=wave.plane, result_read_scope='EXECUTION_RECORDS')
    assert report['execution_complete'] and report['read_scope'] == 'EXECUTION_RECORDS'
    assert report['new_native_contact_count'] == 0 and report['native_contact'] == 'none'


@pytest.mark.parametrize('damage', ('receipt', 'sidecar', 'commit', 'terminal', 'event', 'late-attempt'))
def test_changed_original_control_or_unused_attempt_refuses(wave, damage):  # noqa: F811
    _, _, index = _roots(wave)
    binding = index.tasks[0]
    candidate = binding.attempts[0]
    relative = candidate.receipt_relative_path
    if damage == 'sidecar':
        relative += '.manifest.json'
    elif damage == 'commit':
        publication = wave.plane.read_manifest(relative).publication
        relative = artifact_publication_commit_relative_path(publication.publication_scope, publication.publication_batch_id)
    elif damage == 'terminal':
        relative = index.terminal_event_relative_path
    elif damage == 'event':
        relative = candidate.event_relative_path
    elif damage == 'late-attempt':
        assert len(binding.attempts) > 1
        relative = binding.attempts[-1].receipt_relative_path
    path = wave.plane.root.resolve(relative, for_write=True)
    before = path.read_bytes() if path.exists() else None
    try:
        if before is None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'uncertified late attempt')
        else:
            path.write_bytes(bytes([before[0] ^ 1]) + before[1:])
        with pytest.raises((ValueError, RuntimeError, OSError)):
            owner.read_development_execution(directory=wave.directory, artifact_writer=wave.plane)
    finally:
        if before is None:
            path.unlink()
        else:
            path.write_bytes(before)


def test_execution_observation_does_not_hide_payload_damage_from_the_full_reader(wave):  # noqa: F811
    _, _, index = _roots(wave)
    binding = index.tasks[0]
    receipt = ExternalTaskReceiptStore(wave.plane).read(index.run_id, binding.task_id, binding.attempts[0].attempt_id)
    path = Path(wave.plane.root.contract.canonical_path) / receipt.output_materializations[0].relative_path
    before = path.read_bytes()
    try:
        path.write_bytes(bytes([before[0] ^ 1]) + before[1:])
        report = owner.read_development_execution(directory=wave.directory, artifact_writer=wave.plane)
        assert report['execution_complete'] and report['typed_product_validation'] == 'DEFERRED'
        with pytest.raises((ValueError, RuntimeError, OSError)):
            execution.read_recursive_wave(directory=wave.directory, artifact_writer=wave.plane)
    finally:
        path.write_bytes(before)


def test_changed_control_during_observation_refuses_before_return(wave, monkeypatch):  # noqa: F811
    _, _, index = _roots(wave)
    path = wave.plane.root.resolve(index.terminal_event_relative_path, for_write=False)
    before = path.read_bytes()
    original = owner._execution_operational_census
    def change(**kwargs):
        result = original(**kwargs)
        path.write_bytes(bytes([before[0] ^ 1]) + before[1:])
        return result
    monkeypatch.setattr(owner, '_execution_operational_census', change)
    try:
        with pytest.raises((ValueError, RuntimeError, OSError)):
            owner.read_development_execution(directory=wave.directory, artifact_writer=wave.plane)
    finally:
        path.write_bytes(before)
