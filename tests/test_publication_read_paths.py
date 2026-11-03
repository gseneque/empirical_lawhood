# SPDX-License-Identifier: MPL-2.0
"""Complete publication reads share paths, never byte or access verdicts."""
from collections import Counter
from dataclasses import replace
from pathlib import Path
import sys

import pytest

from empirical_lawhood.infrastructure import artifacts
from empirical_lawhood.infrastructure.artifact_validation import ArtifactProfileValidatorRegistry
from empirical_lawhood.runtime.artifacts import ArtifactWriteRequest
from tests.runtime_platform.test_artifact_verification_scope import _publication


def _case(tmp_path, count, singletons):
    plane, manifests = _publication(tmp_path, 1 if singletons else count)
    if singletons:
        first = manifests[0]
        logical = first.logical
        body = (Path(plane.root.contract.canonical_path) / first.materialization.relative_path).read_bytes()
        rest = []
        for index in range(1, count):
            result = plane.write(ArtifactWriteRequest(
                'exposed.independent.' + str(index), 'independent/member-' + str(index) + '.json',
                logical.payload_schema, logical.profile, logical.media_type,
                'exposed.independent-batch.' + str(index), 'independent', body,
                logical.visibility_ceiling, logical.parent_visibility_ceilings, logical.outcome_access))
            rest.append(plane.read_manifest(result.materialization.relative_path))
        manifests = (*manifests, *rest)
    return plane, manifests


@pytest.mark.parametrize('count', (4, 32))
@pytest.mark.parametrize('singletons', (False, True))
def test_complete_publication_census_has_constant_root_checks(tmp_path, count, singletons, record_property):
    plane, manifests = _case(tmp_path, count, singletons)
    work, accesses = Counter(), Counter()
    root_check = artifacts.GuardedExternalRoot._verify.__code__
    validation = ArtifactProfileValidatorRegistry.validate_file.__code__

    def observe(frame, event, arg):
        if event == 'call' and frame.f_code is root_check:
            work['root_checks'] += 1
        elif event == 'call' and frame.f_code is validation:
            work['physical_validations'] += 1

    previous = sys.getprofile()
    sys.setprofile(observe)
    try:
        # One selected member still requires every atomic sibling.
        result = plane.verify_manifests_members(manifests if singletons else manifests[:1],
            before_member=lambda row: accesses.update((row.materialization.relative_path,)),
            validate_members=lambda members: tuple(sorted(members)))
    finally:
        sys.setprofile(previous)
    expected = {row.materialization.relative_path for row in manifests}
    assert set(result) == set(accesses) == expected
    assert work == {'root_checks': 6, 'physical_validations': count}
    assert all(value >= 3 for value in accesses.values())
    record_property('complete_publication_read_work', dict(work))


@pytest.mark.parametrize('change', ('parent-link', 'parent-replacement', 'mount'))
def test_path_census_closes_before_the_consumer(tmp_path, monkeypatch, change):
    plane, manifests = _publication(tmp_path, 3)
    root = Path(plane.root.contract.canonical_path)
    changed, consumed = False, False
    final = manifests[-1].materialization.relative_path

    def access(manifest):
        nonlocal changed
        if changed or manifest.materialization.relative_path != final:
            return
        changed = True
        if change == 'mount':
            monkeypatch.setattr(artifacts.os.path, 'ismount', lambda path: False)
        else:
            original = root / 'outputs'
            held = root / 'original-outputs'
            original.rename(held)
            if change == 'parent-link':
                original.symlink_to(held, target_is_directory=True)
            else:
                original.mkdir()
                for path in held.iterdir():
                    if path.is_file():
                        (original / path.name).write_bytes(path.read_bytes())

    def consume(members):
        nonlocal consumed
        consumed = True

    with pytest.raises((artifacts.ExternalRootUnavailable, artifacts.ArtifactIdentityConflict)):
        plane.verify_manifests_members(manifests[:1], before_member=access, validate_members=consume)
    assert changed and not consumed


def test_new_invocation_checks_missing_atomic_sibling_and_fresh_access(tmp_path):
    plane, manifests = _publication(tmp_path, 3)
    allowed = True

    def access(_manifest):
        if not allowed:
            raise PermissionError('current access revoked')

    plane.verify_manifests(manifests[:1], before_member=access)
    allowed = False
    with pytest.raises(PermissionError, match='revoked'):
        plane.verify_manifests(manifests[:1], before_member=access)
    allowed = True
    (Path(plane.root.contract.canonical_path) / manifests[-1].materialization.relative_path).unlink()
    with pytest.raises(artifacts.ArtifactIdentityConflict):
        plane.verify_manifests(manifests[:1], before_member=access)


@pytest.mark.parametrize('custom', ('resolver', 'inspector', 'read-paths'))
def test_custom_path_owners_keep_individual_resolves(tmp_path, monkeypatch, custom):
    plane, manifests = _publication(tmp_path, 3)
    calls = []
    if custom == 'resolver':
        original = plane.root.resolve

        def resolve(relative, **kwargs):
            calls.append(relative)
            return original(relative, **kwargs)

        monkeypatch.setattr(plane.root, 'resolve', resolve)
    elif custom == 'inspector':
        class Inspector(artifacts.LocalFilesystemInspector):
            def inspect_bound(self, contract):
                calls.append(contract.storage_root_id)
                return super().inspect_bound(contract)
        plane.root.inspector = Inspector()
    else:
        original = plane.root.read_paths
        monkeypatch.setattr(plane.root, 'read_paths', lambda paths: original(paths))
        original_resolve = plane.root.resolve

        def resolve(relative, **kwargs):
            calls.append(relative)
            return original_resolve(relative, **kwargs)

        monkeypatch.setattr(plane.root, 'resolve', resolve)
    plane.verify_manifests(manifests[:1])
    assert len(calls) > 3 * len(manifests)


def test_foreign_selected_member_cannot_escape_the_publication_census(tmp_path):
    plane, manifests = _publication(tmp_path, 2)
    forged = replace(manifests[0], materialization=replace(manifests[0].materialization,
        relative_path='foreign/unselected.json'), publication=None)
    with pytest.raises(artifacts.ArtifactIdentityConflict):
        plane.verify_manifest(forged)
