# SPDX-License-Identifier: MPL-2.0
"""Public handoff composition over exposed, nonqualifying recursive custody."""

from dataclasses import fields
from pathlib import Path

import pytest

from empirical_lawhood.api import integration_handoffs, recursive_prospective_authoring as owner
from empirical_lawhood.runtime import recursive_prospective_envelope as envelopes
from empirical_lawhood.runtime.experiment_resources import ExecutionResourceSelection, bind_execution_resources
from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveDesignInputs
from tests import test_prospective_experiment as fixtures
from tests.test_recursive_prospective_bounded_capacity import _publish_decoder_bootstrap_case
from tests.test_recursive_prospective_resource_preview import _arguments


selected = fixtures.selected


def _select_fixture_composition(selected, monkeypatch):
    from empirical_lawhood.adapters.composition import generated_extension_bundles

    # Select the existing disclosed fixture's mount and static operation roster.
    # The public dispatcher, closed member reader and compiler remain actual.
    monkeypatch.setattr(integration_handoffs, 'resolve_authoring_directory',
        lambda directory, **_kwargs: (directory.resolve(), selected.plane.root.contract))
    monkeypatch.setattr(generated_extension_bundles, 'GENERATED_EXTENSION_BUNDLE_AGGREGATE',
        selected.original_parts[2])


@pytest.mark.parametrize('carrier', (None, envelopes.RecursiveProspectiveAuthoringEnvelope,
    envelopes.RecursiveProspectiveAuthoringEnvelopeV3, envelopes.RecursiveProspectiveAuthoringEnvelopeV4),
    ids=('semantic-v1', 'envelope-v2', 'envelope-v3', 'envelope-v4'))
def test_generic_handoff_reopens_every_installed_recursive_carrier(selected, monkeypatch, carrier):
    _select_fixture_composition(selected, monkeypatch)
    original = selected.prospective_spec
    if carrier is None:
        directory = selected.original.directory
    else:
        # Select a supported larger profile around honest tiny records, then
        # retain the requested installed wrapper. Scientific bytes stay fixed.
        monkeypatch.setattr(owner, 'MAXIMUM_SPEC_BYTES', len(original.draft.canonical_bytes()) - 1)
        monkeypatch.setattr(owner, '_stored_prospective_spec',
            lambda spec, *, decoder_registration: carrier.from_spec(spec))
        design = RecursiveProspectiveDesignInputs.from_spec(original)
        preview = owner.preview_recursive_prospective_candidate(design_inputs=design, **_arguments(selected))
        controls = ExecutionResourceSelection(**{field.name: getattr(original.resources, field.name)
            for field in fields(ExecutionResourceSelection)})
        spec = design.bind_resources(bind_execution_resources(controls, issued_extensions=preview.issued_extensions))
        directory = Path(selected.plane.root.contract.canonical_path) / ('generic-carrier-' + carrier.VERSION)
        report = owner.author_recursive_prospective(spec=spec, output_dir=directory,
            expected_preview=preview, **_arguments(selected))
        assert report['native_contact'] == 'none' and report['scientific_authority'] == 'NONE'
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
