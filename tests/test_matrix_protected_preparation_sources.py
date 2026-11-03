# SPDX-License-Identifier: MPL-2.0
"""Actual typed original joins over disclosed metadata, never fresh evidence."""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme.protected_preparation_records import (
    MatrixConfirmationSources, MatrixProtectedSourceClosure, MatrixReservedTransferSources,
)
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as original
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from tests import test_matrix_coupling_preparation as preparation
from tests import test_matrix_scheduled_history as scheduled
from tests import test_matrix_scheduled_history_bindings as bindings
from tests.test_matrix_factor_confirmation_eligibility import stock, publish
from tests.test_matrix_later_programme import ref
from tests.test_matrix_parameter_history import source as parameter_template


@pytest.fixture
def closure(tmp_path):
    plane, prior = stock.__wrapped__(tmp_path, parameter_template().provenance)
    plane, sources, config = bindings.bank.__wrapped__(scheduled.scheduled.__wrapped__((plane, prior)))
    selected = next(row for row in sources if row.root.root.role is MatrixProgrammeRole.CONFIRMATION)
    source, _, _, _, _ = preparation.selected.__wrapped__((plane, selected))
    result = MatrixProtectedSourceClosure("closure.exposed-confirmation-source", selected.reservation, selected.specification,
        (selected.provenance,), (selected.reference,), config.audit, config.audit_publication,
        ((selected.root_id, source.initial),), ref("numerical-scope.exposed-confirmation-source"))
    target = source.initial.alpha_tilde
    hold = replace(source.recipe, recipe_id="recipe.exposed-confirmation.hold", kind="HOLD",
        half_tick_couplings=(target,) * len(source.recipe.half_tick_couplings))
    return plane, result, hold, source.recipe


def test_confirmation_derives_two_distinct_subjects_from_one_exact_original_root_and_start(closure):
    _, original_closure, hold, recipe = closure
    selected = MatrixConfirmationSources("sources.exposed-confirmation", original_closure, (("hold", hold), ("recipe-a", recipe)), "hold")
    sources = selected.source_arms()
    assert len(sources) == 2 and len({source.identity for _, source in sources}) == 2
    assert len({source.original.source for _, source in sources}) == 1
    assert len({source.root for _, source in sources}) == len({source.initial for _, source in sources}) == 1
    assert sources[0][1].root.root.role is MatrixProgrammeRole.CONFIRMATION
    assert sources[0][1].original == original_closure.prepare_source(original_closure.descriptors[0], hold, index=original_closure.source_index()).original
    assert decode_canonical_bytes(selected.canonical_bytes(), MatrixConfirmationSources, maximum_bytes=None) == selected
    original_subject = original_closure.original(original_closure.descriptors[0], index=original_closure.source_index())
    assert original_subject.reference == original_closure.descriptors[0]


@pytest.mark.parametrize("damage", ("subject", "initial-census", "recipe-handoff", "hold-hidden-change"))
def test_protected_source_selection_refuses_original_subject_start_or_recipe_substitution(closure, damage):
    _, selected, hold, recipe = closure
    with pytest.raises(ValueError):
        if damage == "subject":
            row = selected.descriptors[0]
            replace(selected, descriptors=(replace(row, allocation=replace(row.allocation, object_fingerprint="f" * 64)),))
        elif damage == "initial-census":
            replace(selected, initial_states=())
        elif damage == "recipe-handoff":
            altered = replace(recipe, half_tick_couplings=(*recipe.half_tick_couplings[:-1], (D(9), D(9))))
            MatrixConfirmationSources("sources.refused-recipe", selected, (("hold", hold), ("recipe-a", altered)), "hold")
        else:
            replace(hold, half_tick_couplings=(hold.half_tick_couplings[0], (D(9), D(9)), *hold.half_tick_couplings[2:]))


def test_confirmation_cannot_admit_actual_development_role_by_changing_selection_name(closure):
    _, selected, hold, recipe = closure
    allocation = selected.reservation.allocation
    root = next(row for row in allocation.roots if row.root.role is MatrixProgrammeRole.DEVELOPMENT)
    index = selected.source_index()
    original_source = index.resolve(index.reference(source_id="source.exposed-original-development",
        root_id=root.root.root_id, provenance=selected.provenances[0].identity))
    source, _, _, _, _ = preparation.selected.__wrapped__((None, original_source))
    changed = replace(selected, record_id="closure.exposed-development-not-conf",
        descriptors=(original_source.reference,), initial_states=((original_source.root_id, source.initial),))
    with pytest.raises(ValueError, match="actual fresh CONF roots"):
        MatrixConfirmationSources("sources.refused-role", changed, (("hold", hold), ("recipe-a", recipe)), "hold")


def test_transfer_uses_complete_original_reserved_source_subjects_with_separate_whole_groups(closure):
    plane, selected, _, _ = closure
    allocation = selected.reservation.allocation
    old = tuple(row for row in allocation.roots if row.root.role is MatrixProgrammeRole.WITHHELD_TRANSFER)
    # A new disclosed test allocation and its own actual publication. Original
    # historical bytes are untouched; these are not real reserve/issue records.
    roots = tuple(replace(row, root=replace(row.root, root_id="root.exposed-reserve." + str(index),
        independent_group_id="group.exposed-reserve." + str(index)),
        streams=tuple(replace(stream, digest_sha256=sha256(("EXPOSED_RESERVE." + str(index) + "." + stream.purpose).encode()).hexdigest()) for stream in row.streams))
        for index, row in enumerate(old))
    scopes = tuple(original.ScheduledMatchedScope("scope.exposed-reserve." + str(index), MatrixProgrammeRole.WITHHELD_TRANSFER,
        (row.root.independent_group_id,), (row.coordinate,), scheduled.CONSTRUCTION) for index, row in enumerate(roots))
    coordinates = tuple(row for row in allocation.coordinates if original.coordinate_identity(row) in {root.coordinate for root in roots})
    allocation = replace(allocation, allocation_id="allocation.exposed-two-original-reserves", coordinates=coordinates, roots=roots, matched_scopes=scopes)
    reservation = replace(selected.reservation, reservation_id="reservation.exposed-two-original-reserves", allocation=allocation,
        publication=publish(plane, allocation, "published.exposed-two-original-reserves"))
    selection = replace(selected.specification.selection, selection_id="selection.exposed-two-original-reserves", reservation=original.identity(reservation),
        coordinate_policies=tuple((original.coordinate_identity(row), original.identity(selected.specification.selection.prefix_policies[0])) for row in coordinates))
    specification = replace(selected.specification, specification_id="specification.exposed-two-original-reserves", selection=selection,
        publication=publish(plane, selection, "published.exposed-two-original-reserve-selection"))
    source_index = ScheduledSourceIndex.from_shared(reservation=reservation, specification=specification,
        provenances=selected.provenances)
    subjects = tuple(source_index.resolve(source_index.reference(source_id="source.exposed-two-original-reserves." + str(index),
        root_id=row.root.root_id, provenance=selected.provenances[0].identity)) for index, row in enumerate(roots))
    prepared = tuple(preparation.selected.__wrapped__((None, row))[0] for row in subjects)
    reserved = MatrixProtectedSourceClosure("closure.exposed-two-original-reserves", reservation, specification, selected.provenances,
        tuple(row.reference for row in subjects), selected.audit, selected.audit_publication,
        tuple((row.root_id, source.initial) for row, source in zip(subjects, prepared, strict=True)), selected.numerical_scope)
    recipes = tuple((source.root.coordinate, replace(source.recipe, recipe_id="recipe.hold." + str(index), kind="HOLD",
        half_tick_couplings=(source.initial.alpha_tilde,) * len(source.recipe.half_tick_couplings))) for index, source in enumerate(prepared))
    transfer = MatrixReservedTransferSources("sources.exposed-two-original-reserves", reserved, recipes, "hold")
    assert len(transfer.source_arms()) == 2 and len({source.root.root.independent_group_id for _, source in transfer.source_arms()}) == 2
    assert decode_canonical_bytes(transfer.canonical_bytes(), MatrixReservedTransferSources, maximum_bytes=None) == transfer
    with pytest.raises(ValueError, match="complete original pre-fit reserve"):
        reduced = replace(reserved, descriptors=reserved.descriptors[:-1], initial_states=reserved.initial_states[:-1])
        MatrixReservedTransferSources("sources.refused-missing-reserve", reduced, recipes[:-1], "hold")
