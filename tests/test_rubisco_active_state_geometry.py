# SPDX-License-Identifier: MPL-2.0
"""Independent conservation and geometric falsifiers; no enzyme qualification."""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import SourceMember
from empirical_lawhood.domains.rubisco.rubisco_response.active_model_preparation import ActivePreparationProtocol, read_catalytic_core_graphs
from empirical_lawhood.domains.rubisco.rubisco_response.active_state_geometry import ActiveCoordinateChange, CatalyticStateSeed, _hydrogen_position, _water_geometry, expand_state_coordinates
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity


FIXTURE = Path(__file__).parent/'fixtures/rubisco/active-states/catalytic-core-graphs.json'


def source(raw=None):
    raw = FIXTURE.read_bytes() if raw is None else raw
    return SourceMember('source.exposed.catalytic-graph-control', 'exposed-software-fixture', sha256(raw).hexdigest(), raw.decode())


def protocol():
    return ActivePreparationProtocol('protocol.exposed.active-geometry', read_catalytic_core_graphs(source()))


def pin(name):
    return ObjectIdentity(name, 'empirical-lawhood/exposed/control', '1.0.0', 'a'*64)


def test_all_nine_hypotheses_preserve_atoms_charge_and_electrons():
    value = protocol()
    populations = []
    for graph in value.graphs:
        populations.append([(a.label, a.atomic_number, a.cap) for a in graph.atoms])
        assert len(graph.atoms) == 125 and sum(a.cap for a in graph.atoms) == 7
        assert sum(a.formal_charge for a in graph.atoms) == -2
        assert sum(a.atomic_number for a in graph.atoms)+2 == 476
        assert sum(a.atomic_number == 1 and not a.cap for a in graph.atoms) == 61
    assert all(p == populations[0] for p in populations)
    assert decode_canonical_bytes(value.canonical_bytes(), ActivePreparationProtocol, maximum_bytes=2**20) == value


@pytest.mark.parametrize('change', ('missing-state', 'duplicate-state', 'missing-atom', 'wrong-charge', 'wrong-bond'))
def test_changed_complete_chemical_census_is_refused(change):
    document = json.loads(FIXTURE.read_text())
    rows = document['core_chemical_hypotheses']
    if change == 'missing-state':
        rows.pop()
    elif change == 'duplicate-state':
        rows[-1] = rows[0]
    elif change == 'missing-atom':
        rows[0]['atoms'].pop('ligand.HC3')
    elif change == 'wrong-charge':
        rows[0]['atoms']['ligand.O2']['formal_charge'] += 1
    else:
        rows[0]['bonds'][0]['order'] = 3
    with pytest.raises((ValueError, KeyError)):
        read_catalytic_core_graphs(source(json.dumps(document).encode()))


def test_coordinate_overlay_requires_the_original_full_array_and_exact_successor():
    before = np.asarray(((0., 0., 0.), (1., 0., 0.), (9., 8., 7.)), dtype='<f8')
    after = before.copy()
    after[1] = (0., 1., 0.)
    changes = (ActiveCoordinateChange(1, (D(1), D(0), D(0)), (D(0), D(1), D(0))),)
    seed = CatalyticStateSeed('seed.exposed', pin('site.exposed'), pin('protocol.exposed'), pin('graph.exposed'),
        'keto-hid', 'AS_CONSTRUCTED', 3, sha256(before.tobytes()).hexdigest(), changes,
        sha256(after.tobytes()).hexdigest(), ())
    assert np.array_equal(expand_state_coordinates(seed, before.tobytes()), after)
    assert decode_canonical_bytes(seed.canonical_bytes(), CatalyticStateSeed, maximum_bytes=2**20) == seed
    tampered = before.copy()
    tampered[-1, 0] += 1e-10
    with pytest.raises(ValueError, match='original full'):
        expand_state_coordinates(seed, tampered.tobytes())
    with pytest.raises(ValueError, match='successor'):
        expand_state_coordinates(replace(seed, expanded_coordinate_sha256='b'*64), before.tobytes())
    with pytest.raises(ValueError, match='original atom'):
        expand_state_coordinates(replace(seed, coordinate_changes=(replace(changes[0], before_angstrom=(D(0),)*3),)), before.tobytes())
    with pytest.raises(ValueError, match='repeated'):
        replace(seed, coordinate_changes=(changes[0], changes[0]))
    with pytest.raises(ValueError, match='cannot admit'):
        replace(seed, scope='RELAXED_ACTIVE_ENZYME')


def test_rigid_water_move_preserves_triangle_with_periodic_wrapping():
    # Water straddles the periodic face; its physical geometry must survive.
    xyz = np.asarray(((19.8, 0., 0.), (.7572, 0., 0.), (19.56, .9273, 0.), (7., 8., 9.)))
    box = np.asarray((20.,)*3)
    direction = np.asarray((1., 2., 3.))/np.sqrt(14)
    placed = _water_geometry(xyz, (0, 1, 2), 3, direction, 2.15, np.eye(3), box)
    for i in range(3):
        for j in range(3):
            original = xyz[i]-xyz[j]
            original -= box*np.floor(original/box+.5)
            assert np.linalg.norm(placed[i]-placed[j]) == pytest.approx(np.linalg.norm(original), abs=1e-12)
    assert np.linalg.norm(placed[0]-xyz[3]) == pytest.approx(2.15, abs=1e-12)
    dipole = placed[1]+placed[2]-2*placed[0]
    assert np.dot(dipole/np.linalg.norm(dipole), direction) == pytest.approx(1., abs=1e-12)


def test_proton_template_preserves_explicit_oh_length_and_angle():
    p = protocol()
    graph = next(g for g in p.graphs if g.label == 'reactive-enolate-kcxh-hie')
    named = {a.label: i for i, a in enumerate(graph.atoms)}
    mapping = tuple(range(len(graph.atoms)))
    xyz = np.zeros((len(graph.atoms), 3))
    host, parent, proton = (named[k] for k in ('protein.210.OQ2', 'protein.210.CX', 'ligand.HO3'))
    xyz[parent] = (1., 0., 0.)
    xyz[proton] = (0., 2., 0.)
    placed = _hydrogen_position(xyz, graph, proton, host, mapping, np.asarray((50.,)*3), np.eye(3), p)
    assert np.linalg.norm(placed) == pytest.approx(.98, abs=1e-12)
    cosine = np.dot(placed, xyz[parent]) / np.linalg.norm(placed)
    assert np.degrees(np.arccos(cosine)) == pytest.approx(109.5, abs=1e-10)


def test_overlapping_occupancy_definitions_are_refused():
    with pytest.raises(ValueError, match='overlap'):
        replace(protocol(), unoccupied_water_minimum_angstrom=D('2.5'))


@pytest.mark.numerical(oracle="One-dimensional donor and acceptor distances and a fixed spectator bond")
@pytest.mark.parametrize("separation", (2.20, 3.0, 3.50))
def test_fixed_proton_references_keep_the_selected_nucleus_and_inclusive_endpoints(separation):
    from empirical_lawhood.domains.rubisco.rubisco_response.active_state_geometry import fixed_proton_references

    xyz = np.array(((0, 0, 0), (separation, 0, 0), (1, 0, 0), (0, 1.30, 0), (0, 0, 0)))
    original = xyz.tobytes()
    results = fixed_proton_references(xyz, ("O", "O", "H", "H", "O"), donor=0, acceptor=1,
                                      proton=2, spectator_proton=3, spectator_oxygen=4)
    assert results.refusal is None and results.proton_atom_index == 2
    assert results.initial_proton_distances_angstrom == pytest.approx((1, separation - 1))
    assert tuple(k for k, _ in results.positions_angstrom) == ("donor", "midpoint", "acceptor")
    np.testing.assert_allclose(np.asarray([p for _, p in results.positions_angstrom], dtype=float),
                               ((1, 0, 0), (separation / 2, 0, 0), (separation - 1, 0, 0)), rtol=0, atol=1e-15)
    assert xyz.tobytes() == original


@pytest.mark.parametrize(("separation", "spectator"), ((2.19, 1.0), (3.51, 1.0), (2.8, 1.31)))
def test_outside_fixed_proton_support_preserves_distances_without_issuing_nodes(separation, spectator):
    from empirical_lawhood.domains.rubisco.rubisco_response.active_state_geometry import fixed_proton_references

    result = fixed_proton_references(((0, 0, 0), (separation, 0, 0), (0, 1, 0), (0, spectator, 0), (0, 0, 0)),
                                     ("O", "O", "H", "H", "O"), donor=0, acceptor=1, proton=2,
                                     spectator_proton=3, spectator_oxygen=4)
    assert result.refusal == "OUTSIDE_SELECTED_BOND_SUPPORT" and result.positions_angstrom == ()
    assert result.donor_acceptor_angstrom == separation and result.spectator_bond_angstrom == spectator


@pytest.mark.parametrize(("donor", "elements"), ((0, ("O", "O", "C", "H", "O")),
                                                 (4, ("O", "O", "H", "H", "O"))))
def test_fixed_proton_references_refuse_substituted_atom_roles(donor, elements):
    from empirical_lawhood.domains.rubisco.rubisco_response.active_state_geometry import fixed_proton_references

    with pytest.raises(ValueError, match="source-mapped"):
        fixed_proton_references(np.zeros((5, 3)), elements, donor=donor, acceptor=1, proton=2,
                                spectator_proton=3, spectator_oxygen=4)
