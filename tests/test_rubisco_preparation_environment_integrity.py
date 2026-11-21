# SPDX-License-Identifier: MPL-2.0
"""Disclosed original-input controls, with no molecular execution or admission.

These cases preserve internally valid canonical identities while falsifying
support and mapping claims. The original paired metadata fixture supplies the
actual logical atom tables; no native callback or response result is used.
"""

from dataclasses import replace

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.formation_coordinate import prepare_formation_coordinate
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_records import InitialRootScopedAssessment
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import prepare_response_design, review_response_initial_geometry
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_environment import MODELS, prepare_response_environment, validate_environment_model, validate_response_environment_sources
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from tests import test_rubisco_active_preparation as preparation

fixture = preparation.fixture
matched = preparation.matched
prefix = preparation.prefix


@pytest.fixture
def environment_sources(prefix):
    paired = dict(zip(MODELS, prefix.models[:2], strict=True))
    coordinates = tuple((name, prepare_formation_coordinate(representation=row[0], prepared=row[2],
        site_id=prefix.config.prefix.conditional.state_census[0][0])) for name, row in paired.items())
    return dict(models={name: row[0] for name, row in paired.items()},
        prototypes={name: row[1] for name, row in paired.items()},
        preparations={name: row[2] for name, row in paired.items()}, formation_coordinates=coordinates)


def _selected(sources):
    return prepare_response_environment(**sources, region='SELECTED_COMMON_PROTEIN_RESIDUES',
        residue_keys=(('lsu.01', 1),))


def _identified(record):
    provisional = replace(record, environment_id='environment.preparation-response.pending')
    return replace(provisional, environment_id='environment.preparation-response.' + provisional.fingerprint())


def test_complete_original_sources_refuse_an_undeclared_subset(environment_sources):
    selected = _selected(environment_sources)
    validate_response_environment_sources(environment=selected, **environment_sources)
    # This fixture's full common protein exceeds the bounded transport census.
    # Refusal is required; selecting a clipped prefix is not an allowed default.
    with pytest.raises(ValueError, match='4096'):
        prepare_response_environment(**environment_sources)
    forged = _identified(replace(selected, region='COMMON_PROTEIN_OUTSIDE_SELECTED_SITE_CORE'))
    # The same valid small map cannot claim to be the complete all-common region.
    for name in MODELS:
        validate_environment_model(forged, environment_sources['models'][name], name)
    with pytest.raises(ValueError, match='4096'):
        validate_response_environment_sources(environment=forged, **environment_sources)


def test_complete_original_sources_refuse_a_weakened_retained_core(environment_sources):
    selected = _selected(environment_sources)
    coordinates = dict(environment_sources['formation_coordinates'])
    excluded = dict(selected.excluded_atom_indices)
    model = MODELS[0]
    remove = next(index for index in excluded[model] if index not in coordinates[model].native_atom_indices)
    weakened = tuple((name, tuple(index for index in indices if name != model or index != remove))
        for name, indices in selected.excluded_atom_indices)
    forged = _identified(replace(selected, excluded_atom_indices=weakened))
    assert set(coordinates[model].native_atom_indices) <= set(dict(forged.excluded_atom_indices)[model])
    with pytest.raises(ValueError, match='full authenticated paired construction'):
        validate_response_environment_sources(environment=forged, **environment_sources)


def test_native_order_does_not_authenticate_atom_correspondence(environment_sources):
    selected = prepare_response_environment(**environment_sources, region='SELECTED_COMMON_PROTEIN_RESIDUES',
        residue_keys=(('lsu.01', 1), ('lsu.01', 2)))
    # Both selected residues contain a CA in this disclosed metadata fixture.
    # Preserve the full native-index census while swapping their logical roles.
    pairs = list(selected.atom_pairs)
    first, second = pairs[0], pairs[1]
    pairs[0], pairs[1] = (*first[:5], second[5]), (*second[:5], first[5])
    forged = _identified(replace(selected, atom_pairs=tuple(pairs)))
    assert {row[5] for row in selected.atom_pairs} == {row[5] for row in forged.atom_pairs}
    with pytest.raises(ValueError, match='unrelated native index'):
        validate_environment_model(forged, environment_sources['models']['m1-wt'], 'm1-wt')


def test_explicit_region_cannot_include_the_receiver_or_mutated_chemistry(environment_sources):
    coordinates = dict(environment_sources['formation_coordinates'])
    model = environment_sources['models']['m1-wt']
    residues = {row.residue_id: row for row in model.residues}
    receiver = residues[model.atoms[coordinates['m1-wt'].native_atom_indices[2]].residue_id]
    receiver_key = (receiver.chain_id, receiver.sequence_position_1based)
    with pytest.raises(ValueError, match='retained-core chemistry'):
        prepare_response_environment(**environment_sources, region='SELECTED_COMMON_PROTEIN_RESIDUES',
            residue_keys=(receiver_key,))
    paired = {name: {(row.chain_id, row.sequence_position_1based): row
        for row in environment_sources['models'][name].residues if row.role == 'PROTEIN'} for name in MODELS}
    mutation = next(key for key in sorted(set(paired[MODELS[0]]) & set(paired[MODELS[1]]))
        if (paired[MODELS[0]][key].component, paired[MODELS[0]][key].sequence_letter)
        != (paired[MODELS[1]][key].component, paired[MODELS[1]][key].sequence_letter))
    with pytest.raises(ValueError, match='mutated, noncommon'):
        prepare_response_environment(**environment_sources, region='SELECTED_COMMON_PROTEIN_RESIDUES',
            residue_keys=(mutation,))


def test_environmental_geometry_cannot_be_mislabeled_as_the_local_mixed_challenge(prefix, environment_sources):
    original_root = ObjectIdentity('assessment.exposed.original-root', InitialRootScopedAssessment.SCHEMA,
        InitialRootScopedAssessment.VERSION, '8' * 64)
    design = prepare_response_design(prefix=prefix.config.prefix, root_assessment=original_root,
        formation_coordinates=environment_sources['formation_coordinates'], environment=_selected(environment_sources))
    model, prototype, prepared, _, _, coordinates = prefix.models[0]
    with pytest.raises(ValueError, match='before the initial-action nomination'):
        review_response_initial_geometry(design=design, model_name=MODELS[0], representation=model,
            prepared=prepared, prototype=prototype, coordinate_bytes=coordinates)
