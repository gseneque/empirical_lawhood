# SPDX-License-Identifier: MPL-2.0
"""Actual local source transport across processes; exposed software metadata only."""
from dataclasses import replace
import os
import pickle
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as old
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_bank_recipe as recipe
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as dev
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as protected
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_native_source import BoundSelectedNativeSource
from empirical_lawhood.api.matrix_retained_replay import bounded_e4_replay_source, map_reconstructions, replay_weight
from empirical_lawhood.infrastructure.parallel_verification import CanonicalValidationPool
from tests.test_matrix_selected_e4_bank_recipe import literal_recipe_source_inputs  # noqa: F401
from tests.test_matrix_selected_protected import unpublished


def _source_values(value):
    _, source = value
    assert type(source) is BoundSelectedNativeSource and not hasattr(source, 'index')
    source.__post_init__()
    public = ScheduledPublicSource.from_source(source)
    assert old.identity(source) == public.source
    return os.getpid(), public.canonical_bytes(), source.provenance.canonical_bytes(), source.root.streams


@pytest.mark.parametrize('phase', ('DEVELOPMENT', 'CONFIRMATION'))
def test_actual_e4_source_has_bounded_weight_and_crosses_process_without_shared_bank(
        literal_recipe_source_inputs, phase):  # noqa: F811
    f = literal_recipe_source_inputs
    allocation = recipe.recipe_allocation(f.inputs)
    reservation = old.ScheduledReservation('reservation.replay.disclosed', allocation, unpublished(allocation, 'allocation.replay.disclosed'))
    selection = recipe.recipe_selection(f.inputs, reservation)
    specification = old.ScheduledSpecification('specification.replay.disclosed', selection, unpublished(selection, 'selection.replay.disclosed'))
    _, responses = recipe.recipe_responses(f.inputs, reservation, specification, f.case.provenance, phase)
    criterion = f.inputs.original_preparation.mathematical_protocol
    bank = recipe.recipe_bank(f.inputs, reservation=reservation, specification=specification, provenance=f.case.provenance,
        criterion_publication=unpublished(criterion, 'criterion.replay.disclosed'),
        response_publication=unpublished(responses, 'responses.replay.disclosed.' + phase.lower()), phase=phase)
    programme = recipe.recipe_programme(bank, phase)
    index = bank.source_index()
    descriptor = bank.sources[0]
    resolved = index.resolve(descriptor)
    native_kind = dev.SelectedE3E4NativeSource if phase == 'DEVELOPMENT' else protected.SelectedE4ProtectedNativeSource
    native = native_kind.from_bank(programme, bank, descriptor, index=index)
    source = bounded_e4_replay_source(native)
    assert source.reference == resolved.reference
    assert source.coordinate == resolved.coordinate and source.policy == resolved.policy
    assert old.identity(source) == old.identity(resolved)
    assert len(pickle.dumps(source)) < bank.canonical_size_bytes()
    size = replay_weight(records=(source.transport, source.provenance), archives=())
    assert size > source.transport.canonical_size_bytes() + source.provenance.canonical_size_bytes()
    expected = _source_values((size, source))
    pool = CanonicalValidationPool(2)
    writer = SimpleNamespace(_read_verification=SimpleNamespace(canonical_pool=pool))
    try:
        actual, = map_reconstructions(writer, _source_values, ((size, source),))
    finally:
        pool.close()
    assert actual[0] != os.getpid() and actual[1:] == expected[1:]
    assert actual[1] == ScheduledPublicSource.from_source(resolved).canonical_bytes()
    with pytest.raises(ValueError, match='size'):
        replace(source, transport=replace(source.transport, provenance_size_bytes=source.transport.provenance_size_bytes + 1))
