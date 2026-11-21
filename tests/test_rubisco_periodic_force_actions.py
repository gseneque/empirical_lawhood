# SPDX-License-Identifier: MPL-2.0
"""Exposed analytic action controls; these supply no enzyme evidence."""
from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import periodic_control_operation as operation
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_control_native as native
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_control_selection as selection
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_force_action_read as reader
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_physical_direction import PeriodicPhysicalDirection
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.records.status import OperationalStatus
from tests import test_rubisco_periodic_controls as controls
from tests import test_rubisco_periodic_control_operation as lifecycle
from tests import test_rubisco_periodic_probe_operation as probe

fixture = probe.fixture


def selected(fixture):
    _, _, raw = controls.selected(fixture)
    prototype = fixture.selection
    direction = PeriodicPhysicalDirection('direction.exposed.physical', prototype.representation,
        prototype.coordinates, fixture.model.material.sources[0], prototype.physical_atom_count,
        ((0, 0, D('.6')), (1, 1, D('.8'))))
    protocol, points = selection.prepare_periodic_force_actions(prototype=prototype, coordinate_bytes=raw,
        directions=(direction,), steps_bohr=(D('.01'), D('.005')))
    configs = tuple(operation.PeriodicForceActionConfig('config.'+p.point_id, fixture.config, protocol, p) for p in points)
    return protocol, points, configs, raw


def test_formation_direction_matches_independent_periodic_coordinate_differences(fixture):
    from empirical_lawhood.domains.rubisco.rubisco_response.formation_coordinate import PreparedFormationCoordinate
    from empirical_lawhood.api.domain_composition.rubisco_response.periodic_controls import prepare_formation_response_direction

    _, _, original = controls.selected(fixture)
    xyz = np.frombuffer(original, dtype='<f8').reshape((-1, 3)).copy()
    # Exposed arithmetic coordinates cross one periodic image. The middle atom
    # participates in both distances, so its two contributions must be joined.
    xyz[:3] = ((19.6, 1., 2.), (.4, 1.3, 2.2), (1.1, 2., 1.8))
    raw = xyz.tobytes()
    manifest = fixture.selection.coordinates
    coordinates = replace(manifest,
        members=(replace(manifest.members[0], sha256=sha256(raw).hexdigest()),))
    prototype = replace(fixture.selection, coordinates=coordinates,
        sources=tuple(sorted((coordinates.identity if pin == manifest.identity else pin
            for pin in fixture.selection.sources), key=lambda pin: pin.object_id)))
    source = fixture.model.material.sources[0]
    coordinate = PreparedFormationCoordinate('coordinate.exposed.periodic-gradient', prototype.representation,
        source, source, 'site.exposed', (source, source), ('ligand.C3', 'ligand.HC3', 'protein.1.OQ2'),
        (0, 1, 2), ('atom.exposed.c', 'atom.exposed.h', 'atom.exposed.o'), (D(12), D(1), D(16)),
        'a'*64, len(xyz))
    selected_direction = prepare_formation_response_direction(coordinate=coordinate,
        prototype=prototype, coordinate_bytes=raw)
    lengths = np.array(tuple(float(v) for v in prototype.cell.lengths_angstrom))
    def value(points):
        bonds = np.diff(points[:3], axis=0)
        bonds -= lengths*np.floor(bonds/lengths+.5)
        return np.linalg.norm(bonds[0])-np.linalg.norm(bonds[1])
    numerical = np.zeros_like(xyz)
    for atom in range(3):
        for axis in range(3):
            plus, minus = xyz.copy(), xyz.copy()
            plus[atom, axis] += 1e-5
            minus[atom, axis] -= 1e-5
            numerical[atom, axis] = (value(plus)-value(minus))/(2e-5)
    numerical /= np.linalg.norm(numerical)
    actual = reader.direction_values(selected_direction, len(xyz))
    np.testing.assert_allclose(actual, numerical, atol=1e-10, rtol=1e-9)
    np.testing.assert_allclose(actual.sum(axis=0), 0, atol=1e-15)
    assert selected_direction.source == coordinate.identity
    with pytest.raises(ValueError, match='original atoms, coordinates'):
        prepare_formation_response_direction(coordinate=coordinate, prototype=prototype,
            coordinate_bytes=original)


def test_physical_action_protocol_has_exact_four_displaced_points_and_roundtrips(fixture):
    protocol, points, configs, raw = selected(fixture)
    assert len(points) == protocol.point_count == 4 and all(p.role == 'DISPLACED' for p in points)
    assert [p.signed_step_bohr for p in points] == list(map(D, ('-.01', '.01', '-.005', '.005')))
    assert decode_canonical_bytes(protocol.canonical_bytes(), selection.PeriodicForceActionProtocol,
        maximum_bytes=2**20) == protocol
    assert decode_canonical_bytes(configs[0].canonical_bytes(), operation.PeriodicForceActionConfig,
        maximum_bytes=2**20) == configs[0]
    xyz = np.frombuffer(raw, dtype='<f8').reshape((-1, 3))
    for point in points:
        displaced = selection.point_coordinates(protocol, point, raw)
        expected = reader.direction_values(protocol.directions[0], len(xyz))*float(point.signed_step_bohr*selection.BOHR_ANGSTROM)
        assert np.count_nonzero(displaced-xyz) == 2
        np.testing.assert_allclose(displaced-xyz, expected, atol=1e-15, rtol=1e-12)
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_translation import periodic_controls_draft
    draft = periodic_controls_draft(configs)
    assert len(draft.operations) == 4 and 'force-difference actions' in draft.development_study.question
    assert all(c.FORCE_ACTIONS for c in configs)


@pytest.mark.parametrize('damage', ('norm', 'duplicate', 'coordinates', 'representation', 'baseline-criterion', 'repeat-component'))
def test_physical_action_refuses_changed_population_direction_and_scope(fixture, damage):
    protocol, _, _, _ = selected(fixture)
    direction = protocol.directions[0]
    with pytest.raises((ValueError, TypeError)):
        if damage == 'norm': replace(direction, components=((0, 0, D(2)),))
        elif damage == 'duplicate': replace(protocol, directions=(direction, replace(direction, direction_id='direction.other')))
        elif damage == 'coordinates':
            changed = replace(direction.coordinates, dataset_id='arrays.other')
            replace(protocol, directions=(replace(direction, coordinates=changed),))
        elif damage == 'representation':
            replace(protocol, directions=(replace(direction, representation=replace(direction.representation, object_id='model.other')),))
        elif damage == 'baseline-criterion':
            replace(protocol, maximum_directional_error_hartree_per_bohr=D('.01'), maximum_step_change_hartree_per_bohr=D('.01'))
        else: replace(direction, components=((0, 0, D('.6')), (0, 0, D('.8'))))


@pytest.mark.parametrize('quartic,missing', ((False, False), (True, False), (False, True)))
def test_coupled_quadratic_and_quartic_actions_use_all_gradient_components(fixture, quartic, missing):
    protocol, points, _, raw = selected(fixture)
    original = np.frombuffer(raw, dtype='<f8').reshape((-1, 3))
    vector = reader.direction_values(protocol.directions[0], len(original))
    # This independent symmetric operator has a negative curvature and an
    # off-input response. No positive inverse or stability is assumed.
    matrix = np.array([[-2., .4, .7], [.4, 5., .8], [.7, .8, 3.]])
    indices = (0, 4, 8)
    expected = np.zeros_like(original)
    expected.flat[list(indices)] = matrix@vector.ravel()[list(indices)]
    values = {}
    for point in points:
        if missing and point.ordinal == 0: continue
        xyz = selection.point_coordinates(protocol, point, raw)
        x = (xyz-original)/float(selection.BOHR_ANGSTROM)
        gradient = np.zeros_like(x)
        gradient.flat[list(indices)] = matrix@x.ravel()[list(indices)]
        if quartic: gradient += 1000*float(np.vdot(x, vector))**3*vector
        values[point.point_id] = (0., gradient)
    rows, arrays = reader.compare_force_actions(protocol, raw, points, values)
    assert len(rows) == 2 and len(arrays) == (1 if missing else 2)
    for index, row in enumerate(rows):
        if missing and index == 0:
            assert row.action is None and row.input_norm is None
            continue
        actual = next(a for manifest, a in arrays if manifest == row.action)
        target = expected + (1000*float(row.step_bohr)**2*vector if quartic else 0)
        np.testing.assert_allclose(actual, target, rtol=1e-11, atol=2e-12)
        assert float(row.orthogonal_action_norm_hartree_per_bohr2) > .1
    if missing:
        assert rows[1].relative_step_change is None
    elif quartic:
        assert float(rows[1].absolute_step_change_hartree_per_bohr2) == pytest.approx(.075, abs=2e-12)
    else:
        assert float(rows[1].relative_step_change) < 1e-11
    with pytest.raises(ValueError, match='complete selected point census'):
        reader.compare_force_actions(protocol, raw, points[:-1], values)


@pytest.mark.parametrize('failed', (False, True))
def test_original_action_custody_reconstructs_failure_and_never_repeats_native(fixture, monkeypatch, failed):
    from tests.rubisco_exposed_geometry_fixture import install_exposed_geometry
    install_exposed_geometry(monkeypatch)
    protocol, points, configs, raw = selected(fixture)
    original = np.frombuffer(raw, dtype='<f8').reshape((-1, 3))
    stores, results, calls = {}, [], []
    # Adapt only the shared test fixture's declaration selection. Native
    # execution remains an explicitly disclosed quadratic software control.
    test_owner = SimpleNamespace(**vars(operation))
    test_owner.operation_declaration = lambda **kw:operation.operation_declaration(force_actions=True, **kw)
    monkeypatch.setattr(operation, 'authenticate_periodic_engine', lambda *a, **kw:())
    for config in configs:
        chosen = SimpleNamespace(**(vars(fixture)|{'config':config}))
        c = probe.custody(chosen, owner=test_owner, task_id=operation.node_id(config),
            runner_type=operation.PeriodicForceActionRunner, implementation=config.original.implementation,
            custody_name='action-custody.'+str(config.point.ordinal))
        def quadratic(**kwargs):
            calls.append(kwargs['point'])
            xyz = lifecycle.disclose_point(kwargs)
            if failed and kwargs['point'].ordinal == 1:
                raise RuntimeError('disclosed failed action point')
            x = (xyz-original)/float(selection.BOHR_ANGSTROM)
            return {'energy_hartree':float(np.sum(x*x)), 'gradient_hartree_per_bohr':2*x}
        monkeypatch.setattr(native, 'execute_periodic_control', quadratic)
        output = operation.PeriodicForceActionRunner().execute_with_native_subwork(c.context, c.store)
        result = decode_canonical_bytes(output.outputs[0].payload, operation.PeriodicProbeResult,
            maximum_bytes=operation.MAX_RETURN)
        results.append(result); stores[result.returned.selection] = c.store
        monkeypatch.setattr(native, 'execute_periodic_control', lambda **kw:pytest.fail('native action replay'))
        repeated = operation.PeriodicForceActionRunner().execute_with_native_subwork(c.fresh_context(), c.store)
        assert repeated.outputs[0].payload == result.canonical_bytes()
    kwargs = dict(configs=configs, representation=fixture.model, coordinate_bytes=raw, original_results=tuple(results),
        native_subwork_for_result=lambda result:stores[result.returned.selection],
        assessor_source=fixture.model.material.sources[0], readout_id='read.exposed.actions')
    result = reader.read_periodic_force_actions(**kwargs)
    report = result['readout']
    assert len(calls) == len(points) == 4 and len(report.points) == 4 and len(report.comparisons) == 2
    assert decode_canonical_bytes(report.canonical_bytes(), reader.PeriodicForceActionsReadout,
        maximum_bytes=operation.MAX_RETURN) == report
    assert report.comparisons[0].action is None if failed else report.comparisons[0].action is not None
    assert report.points[1].original.original_result.completion.operational_status is (
        OperationalStatus.FAILED if failed else OperationalStatus.SUCCEEDED)
    for _, array in result['reconstructed_actions']:
        np.testing.assert_allclose(array, 2*reader.direction_values(protocol.directions[0], len(original)), atol=1e-12)
    with pytest.raises(ValueError, match='repeats or substitutes'):
        reader.read_periodic_force_actions(**(kwargs|{'original_results':(*results,results[0])}))
    with pytest.raises(ValueError, match='original coordinate bytes'):
        reader.read_periodic_force_actions(**(kwargs|{'coordinate_bytes':raw[:-1]+bytes([raw[-1]^1])}))
