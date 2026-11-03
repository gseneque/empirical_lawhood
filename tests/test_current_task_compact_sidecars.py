# SPDX-License-Identifier: MPL-2.0
"""Current preparation reads original compact custody without executing tasks.

The input publications are actual small software fixtures. Current grant and
plan objects are disclosed unit doubles, never scientific authority.
"""
from dataclasses import replace

import pytest

from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustody
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.runtime.artifacts import ArtifactStreamWriteRequest
from tests.test_execution_input_custody_readers import Control, LOGICAL, _selected, _write
from tests.test_selected_development_owned_manifests import _case


def test_development_task_inputs_resolve_complete_compact_publication(tmp_path):
    case = _case(tmp_path, compact=True)
    context, task = _selected(case.manifest)
    receipts, controls = case.custody.task_inputs(context, task)
    assert receipts == {}
    assert controls == {case.value.artifact_id: case.manifest}
    assert len(controls[case.value.artifact_id].publication.members) == 2
    assert case.custody.control_record(case.manifest, type(case.record), 4096) == case.record
    assert all(port.bytes_read == 0 for port in context.input_ports)


@pytest.mark.parametrize('damage', ('member', 'sibling', 'sidecar', 'commit', 'missing-commit'))
def test_development_compact_custody_refuses_changed_original_members(tmp_path, damage):
    case = _case(tmp_path, compact=True)
    context, task = _selected(case.manifest)
    case.custody.task_inputs(context, task)
    relative = {
        'member': case.manifest.materialization.relative_path,
        'sibling': 'selected/sibling.json',
        'sidecar': case.manifest.materialization.relative_path + '.manifest.json',
        'commit': case.manifest.publication.commit_marker_relative_path,
        'missing-commit': case.manifest.publication.commit_marker_relative_path,
    }[damage]
    path = case.plane.root.resolve(relative, for_write=False)
    if damage == 'missing-commit':
        path.unlink()
    else:
        path.write_bytes(path.read_bytes() + b' ')
    with pytest.raises(ArtifactIdentityConflict):
        case.custody.task_inputs(context, task)


def test_development_compact_inputs_keep_exact_worker_bindings(tmp_path):
    case = _case(tmp_path, compact=True)
    context, task = _selected(case.manifest)
    context.input_bindings = (replace(context.input_bindings[0], materialization_id='materialization.foreign'),)
    with pytest.raises(PermissionError, match='complete actual input bindings'):
        case.custody.task_inputs(context, task)


def test_development_compact_sibling_keeps_its_own_access_guard(tmp_path):
    case = _case(tmp_path, compact=True)
    context, task = _selected(case.manifest)
    case.custody._original_member_facts = {(case.value.logical, case.value.materialization)}
    with pytest.raises(PermissionError, match='unowned protected software member'):
        case.custody.task_inputs(context, task)


def test_issued_task_inputs_resolve_compact_transport_before_control_read(tmp_path):
    from tests.runtime_platform.test_execution_scheduler import _plane
    plane = _plane(tmp_path)
    original = _write(plane, 'sharded', logical='input.path-selection')
    raw = Control().canonical_bytes()
    # Select the ordinary deterministic provider path for this separate input.
    from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location
    from tests.test_execution_input_custody_readers import RUN
    relative, scope, root = provider_input_location(plane, RUN, LOGICAL)
    request = ArtifactStreamWriteRequest(LOGICAL, relative, Control.SCHEMA,
        original.logical.profile, original.logical.media_type, scope, root, (raw,),
        len(raw), len(raw), len(raw), Control().fingerprint(),
        original.logical.visibility_ceiling, (), original.logical.outcome_access)
    publication, = plane.write_compact_batch((request,))
    context, task = _selected(publication)
    custody = CurrentIssuedTaskCustody(writer=plane)
    receipts, controls = custody.task_inputs(context, task)
    assert receipts == {} and controls[LOGICAL] == plane.read_manifest(relative)
    assert custody.control_record(controls[LOGICAL], Control, len(raw)) == Control()
    assert all(port.bytes_read == 0 for port in context.input_ports)


def test_compact_metadata_reads_keep_the_selected_custom_reader(tmp_path, monkeypatch):
    case = _case(tmp_path, compact=True)
    calls = []
    original = case.plane.read_manifest
    def selected(relative, **kwargs):
        calls.append(relative)
        return original(relative, **kwargs)
    monkeypatch.setattr(case.plane, 'read_manifest', selected)
    assert case.custody._manifest(case.value.materialization.relative_path,
        expected=case.manifest) == case.manifest
    assert calls == [case.value.materialization.relative_path]
