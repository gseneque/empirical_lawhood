# SPDX-License-Identifier: MPL-2.0
"""Authentic retained fixture closure reuse; software only, no qualification."""

import json
import sys

import pytest

from empirical_lawhood.api import recursive_qualified_parents as owner
from empirical_lawhood.kernel import decoding
from empirical_lawhood.api.current_result_custody import CurrentResultPlanReader
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.test_issued_base_verification_scope import _case
from tests.runtime_platform.test_artifact_verification_scope import _publication
from tests.runtime_platform.test_recursive_prospective_parents import _parent_inputs, parent_fixture as parent_fixture
from tests.test_artifact_read_context import _work


@pytest.mark.parametrize('consumers', (1, 2))
def test_actual_retained_parent_census_is_shared_without_repeat_body_or_path_work(parent_fixture, tmp_path, consumers):
    fixture = parent_fixture
    _, _, binding = _parent_inputs(fixture)
    prefixes = tuple(sorted(row.capability_key for row in fixture.package.registry.capabilities))
    semantic = owner._semantic_writer(fixture.package, fixture.execution_plan, fixture.plane,
        fixture.handoff.compilation.output_codecs)
    with semantic.read_context() as reading:
        reader = CurrentResultPlanReader(reading)
        package = owner._actual_package(reading, binding.run_id, control_reader=reader)
        issued, reveal = owner._replay_parent_authority(binding, package, reading)
        plan = reader.authenticate_execution_plan(package=package, issued=issued, run_id=binding.run_id)
        output_writer = reader.output_artifact_plane(package=package, execution_plan=plan,
            output_codecs=fixture.handoff.compilation.output_codecs)
        assert reader.output_artifact_plane(package=package, execution_plan=plan,
            output_codecs=fixture.handoff.compilation.output_codecs) is output_writer
        scope = owner._ParentReadScope(reading, plan_reader=reader)
        closure = scope.receipt_closure(package, plan, reading, reveal, prefixes)
        assert len(closure.by_task) == len(plan.tasks) == 5
        assert len(closure.manifests) == len({row.materialization.relative_path for row in closure.manifests})
        observed = []
        with _work() as work:
            for _ in range(consumers):
                assert scope.receipt_closure(package, plan, reading, reveal, prefixes) is closure
                assert owner._verify_receipt_closure(reading, closure) is closure.by_task
                observed.append(dict(work))
        assert observed[-1] == observed[0]
        assert work['payloads'] > 0
        reading.require_verification_snapshot()
        owner._require_parent_authorities_current(((binding, package),), reading)
    assert fixture.executor.invocations == 5
    (tmp_path / 'retained-read-context-work.json').write_text(json.dumps({
        'tasks': len(plan.tasks), 'consumers': consumers, 'work_after_each_consumer': observed,
        'receipt_count': len(closure.by_task), 'unique_manifests': len(closure.manifests),
        'native_reexecution': False,
        'claim': 'Actual synthetic issued-parent custody only; no real scientific qualification',
    }, sort_keys=True) + '\n')


def test_more_than_eight_immutable_controls_decode_once_per_operation(tmp_path):
    plane, manifests = _publication(tmp_path, 12)
    decoded = []
    def observe(frame, event, arg):
        if event == 'call' and frame.f_code is decoding._decode_canonical_bytes.__code__:
            if frame.f_locals['record_type'] is ObjectIdentity:
                decoded.append(ObjectIdentity)
    previous = sys.getprofile()
    sys.setprofile(observe)
    try:
        with plane.read_context() as reading:
            reader = CurrentResultPlanReader(reading)
            first = tuple(reader.read_control(row, ObjectIdentity, row.materialization.size_bytes) for row in manifests)
            assert len(decoded) == len(manifests)
            repeated = tuple(reader.read_control(row, ObjectIdentity, row.materialization.size_bytes) for row in manifests)
            assert all(left is right for left, right in zip(first, repeated, strict=True))
            assert len(decoded) == len(manifests)
    finally:
        sys.setprofile(previous)


@pytest.mark.parametrize('members', (8, 16))
def test_issued_read_context_reuses_the_complete_source_census_without_issue_authority(tmp_path, members):
    case = _case(tmp_path / 'issued-read-context', members)
    with _work() as work:
        with case.publisher.read_context() as reading:
            original = reading.load_study(case.manifest.issue_id)
            first = dict(work)
            for _ in range(members):
                assert reading.load_study(case.manifest.issue_id) is original
            assert dict(work) == first
            with pytest.raises(PermissionError, match='no issue validation'):
                reading.validate(case.preparation, at_utc='2026-07-24T20:32:00Z')
    # Original member batch + manifest, then its separate publication receipt.
    assert work['payloads'] == members + 2
    assert work['snapshot_calls'] <= 8
    assert work['snapshot_paths'] <= 5 * (2 * (members + 2) + 2)
    (tmp_path / 'issued-read-context-work.json').write_text(json.dumps({
        'members': members, 'consumers': members + 1, 'work': dict(work),
        'issue_authority_granted': False, 'complete_original_facts_equal': original.manifest == case.manifest,
    }, sort_keys=True) + '\n')
