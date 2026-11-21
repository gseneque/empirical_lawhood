# SPDX-License-Identifier: MPL-2.0
"""Public handoff composition over exposed, nonqualifying recursive custody."""

from pathlib import Path

import pytest

from empirical_lawhood.api import integration_handoffs, recursive_prospective_authoring as owner
from tests import test_prospective_experiment as fixtures
from tests.test_recursive_prospective_bounded_capacity import _publish_decoder_bootstrap_case


selected = fixtures.selected


def _select_fixture_composition(selected, monkeypatch):
    import empirical_lawhood.execution.generated_extension_bundles as generated_extension_bundles

    # Select the existing disclosed fixture's mount and static operation roster.
    # The public dispatcher, closed member reader and compiler remain actual.
    monkeypatch.setattr(integration_handoffs, 'resolve_authoring_directory',
        lambda directory, **_kwargs: (directory.resolve(), selected.plane.root.contract))
    monkeypatch.setattr(generated_extension_bundles, 'GENERATED_EXTENSION_BUNDLE_AGGREGATE',
        selected.original_parts[2])


def test_generic_handoff_reopens_exact_recursive_spec(selected, monkeypatch):
    _select_fixture_composition(selected, monkeypatch)
    original = selected.prospective_spec
    directory = selected.original.directory
    handoff = integration_handoffs.load_integration_handoff(directory=directory,
        root=selected.root / 'checkout', storage_profile=object(), artifact_writer=selected.plane)
    assert handoff.family == 'recursive-inquiry'
    assert handoff.selected.compilation.draft.canonical_bytes() == original.draft.canonical_bytes()
    assert handoff.selected.projection.tasks == selected.original.projection.tasks
    assert (directory / 'draft.json').read_bytes() == original.draft.canonical_bytes()


def test_generic_recursive_dispatch_authenticates_decoder_before_large_untrusted_body(
        selected, tmp_path, monkeypatch):
    _select_fixture_composition(selected, monkeypatch)
    directory, plane = _publish_decoder_bootstrap_case(selected, tmp_path, mutate_decoder=True)
    # This deliberately invalid body is never read: the authentic small packet
    # first selects an uninstalled decoder, which must refuse at that boundary.
    (directory / 'recursive-prospective.json').write_bytes(b' ' * (16 * 1024**2 + 1))
    reads = []
    original_read = owner.read_bounded_bytes

    def observe(path, **kwargs):
        if not Path(path).name.endswith('.manifest.json'):
            reads.append(Path(path).name)
        return original_read(path, **kwargs)

    monkeypatch.setattr(owner, 'read_bounded_bytes', observe)
    with pytest.raises(ValueError, match='outside its exact installed allowlist'):
        integration_handoffs.load_integration_handoff(directory=directory,
            root=selected.root / 'checkout', storage_profile=object(), artifact_writer=plane)
    assert reads == ['authored-wave.json', 'decoder.json']


def test_recursive_marker_does_not_make_an_ambiguous_directory_selectable(selected, tmp_path, monkeypatch):
    _select_fixture_composition(selected, monkeypatch)
    directory = tmp_path / 'ambiguous'
    directory.mkdir()
    for name in ('recursive-prospective.json', 'issued-inputs.json'):
        (directory / name).write_bytes(b'not an authenticated handoff')
    monkeypatch.setattr(owner, 'load_recursive_prospective_handoff',
        lambda **_kwargs: pytest.fail('ambiguous selection reached its owning loader'))
    with pytest.raises(ValueError, match='exactly one unambiguous'):
        integration_handoffs.load_integration_handoff(directory=directory,
            root=selected.root / 'checkout', storage_profile=object(), artifact_writer=selected.plane)
