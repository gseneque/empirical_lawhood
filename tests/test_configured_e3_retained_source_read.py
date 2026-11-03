# SPDX-License-Identifier: MPL-2.0
"""Actual retained configured source consumer and frozen secondary controls.

All source and authority values are disclosed software fixtures. The actual
RetainedProspectiveExperiment class intentionally has no design_records. Its
minimal companion fields below exercise the production reader's decode and
both downstream consumers; they are not a full cold/public scientific read.
No provider, compilation, native acquisition or genuine authority is supplied.
"""
from dataclasses import replace
from types import MappingProxyType, SimpleNamespace

import pytest

from empirical_lawhood.api.domain_composition.matrix_configured_protected_response import scientific_read as owner
from empirical_lawhood.api.prospective_experiment import RetainedProspectiveExperiment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.prospective_experiment import PreparedProspectiveExperimentHandoff, source_filename
from tests.test_matrix_e3_secondary_selection import originals as originals  # noqa: F401
from tests.test_matrix_e3_secondary_selection import current_selection, target_for, published
from empirical_lawhood.adapters.methods.matrix_factor_response import configured_secondary_readout as secondary


def _retained(selection):
    pin = ObjectIdentity.from_record(selection.selection_id, selection)
    name = source_filename(pin)
    value = RetainedProspectiveExperiment(SimpleNamespace(members=(SimpleNamespace(filename=name, identity=pin),)),
        SimpleNamespace(sources=(pin,)), None, None, None, None,
        MappingProxyType({name: selection.canonical_bytes()}))
    assert not hasattr(value, 'design_records')
    return value, pin, name


def test_actual_retained_companion_decodes_same_source_for_primary_and_secondary(originals):  # noqa: F811
    _, original = current_selection(originals)
    document = target_for(originals, 'retained-source-positive')
    selection = secondary.bind_secondary_selection(original, document,
        published(originals.plane, document, 'target.secondary.retained-source-positive'))
    retained, pin, name = _retained(selection)
    raw = retained.payloads[name]
    actual = owner._selected_preparation(retained)
    assert type(actual) is type(selection) and actual == selection
    assert actual.canonical_bytes() == raw and ObjectIdentity.from_record(actual.selection_id, actual) == pin
    target = owner._selected_secondary_target(actual, originals.plane)
    assert target == (document.values(), document.identity, selection.secondary_readout.lineage_scope)
    assert retained.payloads[name] == raw


def test_actual_prepared_companion_preserves_exact_same_supported_source(originals):  # noqa: F811
    _, selection = current_selection(originals)
    retained, pin, _ = _retained(selection)
    prepared = PreparedProspectiveExperimentHandoff(None, retained.association, retained.instance, None,
        None, None, ((pin.object_id, selection),))
    assert owner._selected_preparation(prepared) == selection
    assert owner._selected_secondary_target(selection, originals.plane) is None


@pytest.mark.parametrize('damage', ('missing-source', 'duplicate-source', 'foreign-digest', 'foreign-revision',
    'missing-member', 'foreign-member', 'changed-bytes', 'missing-payload'))
def test_actual_retained_source_adversaries_refuse_before_any_scientific_use(originals, damage):  # noqa: F811
    _, selection = current_selection(originals)
    retained, pin, name = _retained(selection)
    if damage == 'missing-source':
        retained = replace(retained, instance=SimpleNamespace(sources=()))
    elif damage == 'duplicate-source':
        retained = replace(retained, instance=SimpleNamespace(sources=(pin, pin)))
    elif damage == 'foreign-digest':
        changed = replace(pin, object_fingerprint='0' * 64)
        retained = replace(retained, instance=SimpleNamespace(sources=(changed,)),
            association=SimpleNamespace(members=(SimpleNamespace(filename=name, identity=changed),)))
    elif damage == 'foreign-revision':
        retained = replace(retained, instance=SimpleNamespace(sources=(replace(pin, object_version='99.0.0'),)))
    elif damage == 'missing-member':
        retained = replace(retained, association=SimpleNamespace(members=()))
    elif damage == 'foreign-member':
        retained = replace(retained, association=SimpleNamespace(members=(SimpleNamespace(filename=name,
            identity=replace(pin, object_fingerprint='0' * 64)),)))
    elif damage == 'changed-bytes':
        retained = replace(retained, payloads={name: retained.payloads[name] + b' '})
    else:
        retained = replace(retained, payloads={})
    with pytest.raises((PermissionError, ValueError, KeyError)):
        owner._selected_preparation(retained)


def test_selected_frozen_secondary_target_corruption_refuses_after_retained_decode(originals):  # noqa: F811
    _, original = current_selection(originals)
    document = target_for(originals, 'retained-source-corrupt')
    publication = published(originals.plane, document, 'target.secondary.retained-source-corrupt')
    selection = secondary.bind_secondary_selection(original, document, publication)
    retained, _, _ = _retained(selection)
    actual = owner._selected_preparation(retained)
    path = originals.plane.root.resolve(publication.materialization.relative_path, for_write=False)
    raw = path.read_bytes()
    try:
        path.write_bytes(raw + b' ')
        with pytest.raises((PermissionError, ValueError, RuntimeError)):
            owner._selected_secondary_target(actual, originals.plane)
    finally:
        path.write_bytes(raw)



def test_foreign_reader_companion_refuses_before_member_access():
    with pytest.raises(TypeError, match='actual retained or prepared companion'):
        owner._selected_preparation(object())
