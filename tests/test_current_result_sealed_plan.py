# SPDX-License-Identifier: MPL-2.0
"""Sealed prepared-plan reads over disclosed software custody, without workers.

The existing reference fixture supplies synthetic issue/authority records for
contract checks only. No scientific qualification or fresh evidence is created.
"""

from dataclasses import replace

import pytest

from empirical_lawhood.api import current_result_custody as owner
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime import compiler
from empirical_lawhood.runtime.artifacts import (
    ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest, lineage_parent_sort_key,
)
from empirical_lawhood.runtime.plans import RunPlan
from tests.runtime_platform.test_execution_scheduler import _plane
from tests.test_current_result_custody import actual_issued_current_task_controls as actual_issued_current_task_controls


def _run(fixture):
    return owner._current_control(writer=fixture.control.service.artifact_plane,
        run_id=fixture.context.run_id, name='run-plan', record_type=RunPlan, maximum_bytes=None)


def _authenticate(fixture, *, writer=None, package=None):
    package = fixture.control.package if package is None else package
    return owner.authenticate_current_execution_plan(package=package, issued=package.issued_study,
        run_id=fixture.context.run_id, writer=fixture.control.service.artifact_plane if writer is None else writer)


def _published_controls(fixture, root, *, run=None, execution=None, foreign_lineage=False):
    """Independently publish disclosed controls to exercise the reader's joins."""
    root.mkdir()
    plane = _plane(root)
    package = fixture.control.package
    run = _run(fixture) if run is None else run
    execution = fixture.plan if execution is None else execution
    parent = ArtifactLineageParent(ObjectIdentity.from_record(package.package_id, package),
        VisibilityCeiling.PROSPECTIVE, OutcomeAccess.OUTCOME_BLIND)
    if foreign_lineage:
        parent = replace(parent, identity=replace(parent.identity, object_fingerprint='f' * 64))
    source = ArtifactLineageParent(ObjectIdentity.from_record(run.run_plan_id, run),
        VisibilityCeiling.PROSPECTIVE, OutcomeAccess.OUTCOME_BLIND)
    for name, record, parents in (
            ('campaign-package', package, ()), ('run-plan', run, (parent,)),
            ('execution-plan', execution, tuple(sorted((parent, source), key=lineage_parent_sort_key)))):
        plane.write(ArtifactWriteRequest(f'{name}.{package.run_plan_id}',
            f'runs/{package.run_plan_id}/plans/{name}.json', record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', f'campaign-plans.{package.run_plan_id}',
            f'runs/{package.run_plan_id}/plans', record.canonical_bytes(), VisibilityCeiling.PROSPECTIVE,
            tuple(value.visibility_ceiling for value in parents), OutcomeAccess.OUTCOME_BLIND,
            lineage_parents=parents, minimum_free_bytes=1))
    return plane


def test_prepared_plan_read_selects_no_compiler_or_provider(actual_issued_current_task_controls, monkeypatch):
    f = actual_issued_current_task_controls

    def forbidden(*_args, **_kwargs):
        pytest.fail('routine prepared-plan read reconstructed an executable plan')

    monkeypatch.setattr(compiler, 'compile_run_plan', forbidden)
    monkeypatch.setattr(compiler, 'lower_run_plan', forbidden)
    monkeypatch.setattr(f.control.service, '_resolve_campaign_provider', forbidden)
    assert not hasattr(owner, 'compile_run_plan')
    assert not hasattr(owner, 'lower_run_plan')
    assert _authenticate(f) == f.plan
    assert not f.control.executor.invocations


def test_prepared_publisher_refuses_consistent_replacement_under_original_paths(actual_issued_current_task_controls):
    f = actual_issued_current_task_controls
    run = _run(f)
    steps = tuple(replace(step, maximum_attempts=step.maximum_attempts + 1) for step in run.steps)
    changed_run = replace(run, steps=steps)
    changed_execution = replace(f.plan, source_plan=ObjectIdentity.from_record(run.run_plan_id, changed_run),
        tasks=tuple(replace(task, maximum_attempts=task.maximum_attempts + 1) for task in f.plan.tasks))
    # Both bodies agree with each other. The actual immutable publisher must
    # refuse to replace the original preparation-time seals at the same paths.
    with pytest.raises(ArtifactIdentityConflict):
        f.control.service._persist_plans(f.control.package, changed_run, changed_execution,
            package_name='campaign-package', source_plan_name='run-plan', minimum_free_bytes=1)
    assert _authenticate(f) == f.plan


def test_foreign_package_cannot_replace_actual_prepared_package(actual_issued_current_task_controls):
    f = actual_issued_current_task_controls
    with pytest.raises(PermissionError, match='EXACT_PREPARED_PACKAGE_REQUIRED'):
        _authenticate(f, package=replace(f.control.package, package_id=f.control.package.package_id + '.foreign'))


def test_valid_publication_with_foreign_package_lineage_refuses(actual_issued_current_task_controls, tmp_path):
    f = actual_issued_current_task_controls
    plane = _published_controls(f, tmp_path / 'foreign-lineage', foreign_lineage=True)
    with pytest.raises(PermissionError, match='PREPARED_PLAN_PUBLICATION_BINDING_MISMATCH'):
        _authenticate(f, writer=plane)


@pytest.mark.parametrize('damage', ('source', 'candidate', 'output-path', 'output-lane', 'scientific-config'))
def test_consistent_resealed_pair_cannot_override_issued_contract(actual_issued_current_task_controls, tmp_path, damage):
    f = actual_issued_current_task_controls
    run, execution = _run(f), f.plan
    if damage == 'source':
        run = replace(run, implementation_commit='f' * 40)
        execution = replace(execution, implementation_commit='f' * 40)
    elif damage == 'candidate':
        candidate = replace(run.candidate, object_fingerprint='f' * 64)
        run, execution = replace(run, candidate=candidate), replace(execution, candidate=candidate)
    else:
        step = next(step for step in run.steps if step.step_id == f.context.task_id)
        task = next(task for task in execution.tasks if task.task_id == step.step_id)
        if damage in ('output-path', 'output-lane'):
            outputs = tuple(replace(output, **({'relative_path': output.relative_path + '.foreign'}
                if damage == 'output-path' else {'outcome_access': OutcomeAccess.PRIVILEGED_TRUTH,
                    'visibility_ceiling': VisibilityCeiling.PRIVILEGED_TRUTH})) for output in step.outputs)
            step, task = replace(step, outputs=outputs), replace(task, outputs=outputs)
        else:
            config = replace(step.capability.config, content_sha256='f' * 64)
            capability = replace(step.capability, config=config)
            step, task = replace(step, capability=capability), replace(task, capability=capability)
        run = replace(run, steps=tuple(step if row.step_id == step.step_id else row for row in run.steps))
        execution = replace(execution, tasks=tuple(task if row.task_id == task.task_id else row for row in execution.tasks))
    execution = replace(execution, source_plan=ObjectIdentity.from_record(run.run_plan_id, run))
    plane = _published_controls(f, tmp_path / damage, run=run, execution=execution)
    with pytest.raises(PermissionError, match='PREPARED_PLAN_(ISSUED_BINDING|CONTRACT|OUTPUT_CONTRACT)_MISMATCH'):
        _authenticate(f, writer=plane)
