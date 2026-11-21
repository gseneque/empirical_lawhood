# SPDX-License-Identifier: MPL-2.0
"""Prospective numerical points on exposed atom tables; no physical admission."""
from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
import sys
import io
import json

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import periodic_control_selection as owner
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_assessment import read_initial_coordinates
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from tests import test_rubisco_periodic_probe_operation as probe

fixture = probe.fixture


@pytest.mark.parametrize('damage', ('none', 'coordinate', 'parameters', 'missing', 'trailing', 'nonfinite', 'shape'))
def test_molecular_precision_reads_complete_original_arrays_and_refuses_changed_operands(damage):
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_mm_precision import assess_molecular_precision
    request = dict(version='1.0.0', physical_atom_count=2, coordinate_sha256='a'*64,
        remainder_parameter_sha256='b'*64, cuda_properties={'Precision':'double','DeviceIndex':'0','DeterministicForces':'true'},
        scope='SAME_GEOMETRY_COMPLETE_MM_CUDA_REFERENCE', electronic_evaluations=0, matched_pme=[4.5,32,32,32])
    raw = {'mm-precision-request.json':json.dumps(request).encode()}
    completion = dict(version='1.0.0', request_sha256=sha256(raw['mm-precision-request.json']).hexdigest(),
        platforms=['CUDA','Reference'], completed_mm_evaluations=2, electronic_evaluations=0,
        original_system_unchanged=True, wall_seconds={'cuda':1.,'reference':2.})
    raw['mm-precision-completion.json'] = json.dumps(completion).encode()
    values = {'cuda-energy-kj-mol':np.array(4.), 'reference-energy-kj-mol':np.array(1.),
        'cuda-forces-kj-mol-nm':np.array([[1.,2.,0.],[0.,0.,2.]]),
        'reference-forces-kj-mol-nm':np.zeros((2,3))}
    if damage == 'nonfinite': values['cuda-forces-kj-mol-nm'][0,0] = np.nan
    if damage == 'shape': values['cuda-forces-kj-mol-nm'] = np.zeros((1,3))
    for name, value in values.items():
        stream = io.BytesIO(); np.save(stream, value, allow_pickle=False)
        raw['mm-precision-'+name+'.npy'] = stream.getvalue()
    if damage == 'missing': del raw['mm-precision-reference-energy-kj-mol.npy']
    if damage == 'trailing': raw['mm-precision-cuda-energy-kj-mol.npy'] += b'x'
    kwargs = dict(physical_atom_count=2, coordinate_sha256='c'*64 if damage == 'coordinate' else 'a'*64,
        remainder_sha256='c'*64 if damage == 'parameters' else 'b'*64)
    if damage != 'none':
        with pytest.raises(ValueError): assess_molecular_precision(raw, **kwargs)
    else:
        report = assess_molecular_precision(raw, **kwargs)
        assert report['energy_change_kj_mol'] == 3 and report['maximum_force_change_kj_mol_nm'] == 2
        assert report['rms_force_component_change_kj_mol_nm'] == pytest.approx(np.sqrt(1.5))
        assert report['chemical_model_adequacy'] == 'NOT_ESTABLISHED' and report['new_native_calls'] == 0


def selected(fixture, *, dense=False):
    xyz, _ = read_initial_coordinates(fixture.raw_xyz.decode('ascii'), len(fixture.model.atoms), periodic=True)
    raw = np.asarray(xyz, dtype='<f8').tobytes()
    direction = (owner.PeriodicDerivativeDirection('direction.full', 'ALL_PHYSICAL_CARTESIAN_SIGNS',
        sign_seed_sha256='1'*64) if dense else
        owner.PeriodicDerivativeDirection('direction.component', 'CARTESIAN_COMPONENT', 0, 1))
    refinement = owner.PeriodicNumericalRefinement('refinement.scf', 'SCF',
        replace(fixture.selection.electronic, energy_tolerance_hartree=D('1e-13')),
        fixture.selection.molecular, owner.PeriodicRefinementBudget('budget.exposed.scf', D('.01'),
            'Exposed quadratic control: independently prescribed gradient sensitivity allowance.'))
    protocol, points = owner.prepare_periodic_controls(prototype=fixture.selection, coordinate_bytes=raw,
        directions=(direction,), steps_bohr=(D('.01'), D('.005')), refinements=(refinement,),
        required_refinement_kinds=('SCF',))
    return protocol, points, raw


@pytest.mark.parametrize('dense', (False, True))
def test_complete_prospective_points_keep_original_coordinates_and_exact_units(fixture, dense):
    before = set(sys.modules)
    protocol, points, raw = selected(fixture, dense=dense)
    assert not any(n.split('.')[0] in {'pyscf', 'openmm'} for n in set(sys.modules)-before)
    assert len(points) == protocol.point_count == 6
    assert [p.role for p in points] == ['BASELINE', *(['DISPLACED']*4), 'REFINEMENT']
    assert [p.signed_step_bohr for p in points[1:5]] == list(map(D, ('-.01', '.01', '-.005', '.005')))
    assert decode_canonical_bytes(protocol.canonical_bytes(), owner.PeriodicControlProtocol, maximum_bytes=2**20) == protocol
    base = owner.point_coordinates(protocol, points[0], raw)
    for point in points:
        xyz = owner.point_coordinates(protocol, point, raw)
        assert xyz.shape == base.shape and sha256(xyz.tobytes()).hexdigest() == point.coordinate_sha256
        assert decode_canonical_bytes(point.canonical_bytes(), owner.PeriodicControlPoint, maximum_bytes=2**20) == point
        if point.role == 'DISPLACED':
            changed = xyz-base
            assert np.count_nonzero(changed) == (xyz.size if dense else 1)
            nominal = float(abs(point.signed_step_bohr)*owner.BOHR_ANGSTROM)
            roundoff = .5*np.spacing(np.maximum(np.abs(base), np.abs(xyz)))[changed != 0]+np.spacing(nominal)
            assert np.all(np.abs(np.abs(changed[changed != 0])-nominal) <= roundoff)
        else:
            assert xyz.tobytes() == raw


@pytest.mark.parametrize('change', ('ordinal', 'settings', 'point-id', 'direction', 'hash', 'refinement'))
def test_point_reconstruction_refuses_substituted_complete_selection(fixture, change):
    protocol, points, raw = selected(fixture)
    point = points[1]
    if change == 'ordinal': point = replace(point, ordinal=3)
    elif change == 'settings': point = replace(point, electronic=points[-1].electronic)
    elif change == 'point-id': point = replace(point, point_id='point.substituted')
    elif change == 'direction': point = replace(point, direction=replace(protocol.directions[0], direction_id='direction.other').identity)
    elif change == 'hash': point = replace(point, coordinate_sha256='0'*64)
    else: point = replace(points[-1], refinement=replace(protocol.refinements[0], refinement_id='refinement.other').identity)
    with pytest.raises(ValueError, match='prospective'):
        owner.point_coordinates(protocol, point, raw)


@pytest.mark.parametrize('change', ('repeated-direction', 'one-step', 'repeated-step', 'increasing-step',
    'outside-atoms', 'half-tolerance', 'no-question', 'nan-step'))
def test_protocol_refuses_incomplete_or_changed_numerical_questions(fixture, change):
    protocol, _, _ = selected(fixture)
    edits = {
        'repeated-direction': {'directions': (protocol.directions[0], replace(protocol.directions[0], direction_id='direction.other'))},
        'one-step': {'steps_bohr': (D('.01'),)},
        'repeated-step': {'steps_bohr': (D('.01'), D('.01'))},
        'increasing-step': {'steps_bohr': (D('.005'), D('.01'))},
        'outside-atoms': {'directions': (replace(protocol.directions[0], atom_index=protocol.physical_atom_count),)},
        'half-tolerance': {'maximum_directional_error_hartree_per_bohr': D('.001')},
        'no-question': {'directions': (), 'steps_bohr': (), 'refinements': ()},
        'nan-step': {'steps_bohr': (D('NaN'), D('.01'))},
    }[change]
    with pytest.raises((ValueError, ArithmeticError)):
        replace(protocol, **edits)


@pytest.mark.parametrize('change', ('wrong-field', 'coarsened', 'only-name', 'changed-mm', 'cell-overrun'))
def test_refinements_preserve_the_physical_model_and_declared_resolution(fixture, change):
    protocol, _, _ = selected(fixture)
    original = protocol.refinements[0]
    if change == 'wrong-field': candidate = replace(original, electronic=replace(original.electronic, memory_megabytes=512))
    elif change == 'coarsened': candidate = replace(original, electronic=replace(original.electronic, energy_tolerance_hartree=D('1e-8')))
    elif change == 'only-name': candidate = replace(original, electronic=replace(protocol.electronic, settings_id='settings.renamed'))
    elif change == 'changed-mm': candidate = replace(original, molecular=replace(protocol.molecular, cutoff_angstrom=D(8)))
    else: candidate = replace(original, kind='EWALD', electronic=replace(protocol.electronic, real_cutoff_angstrom=D(20)))
    with pytest.raises(ValueError):
        changed = replace(protocol, refinements=(candidate,))
        owner.validate_control_prototype(changed, fixture.selection)


def test_coordinate_mutation_and_unrepresentable_displacement_refuse(fixture):
    protocol, points, raw = selected(fixture)
    wrong = bytearray(raw); wrong[-1] ^= 1
    with pytest.raises(ValueError, match='original coordinate bytes'):
        owner.point_coordinates(protocol, points[0], bytes(wrong))
    direction = owner.PeriodicDerivativeDirection('direction.tiny', 'CARTESIAN_COMPONENT', 0, 0)
    with pytest.raises(ValueError, match='coordinate resolution'):
        owner.displaced_coordinates(np.ones((2, 3)), direction, D('1e-30'))
    dense = owner.PeriodicDerivativeDirection('direction.partial', 'ALL_PHYSICAL_CARTESIAN_SIGNS', sign_seed_sha256='2'*64)
    with pytest.raises(ValueError, match='coordinate resolution'):
        owner.displaced_coordinates(np.array([[1e25, 0, 0]], dtype='<f8'), dense, D('.001'))


def test_refinement_only_has_no_invented_derivative_criterion(fixture):
    protocol, _, raw = selected(fixture)
    refinement_only = replace(protocol, directions=(), steps_bohr=())
    assert len(owner.control_points(refinement_only, raw)) == 2
    assert refinement_only.maximum_directional_error_hartree_per_bohr is None
    with pytest.raises(ValueError, match='actual prospective derivative'):
        replace(refinement_only, maximum_directional_error_hartree_per_bohr=D('.01'),
            maximum_step_change_hartree_per_bohr=D('.01'))


@pytest.mark.numerical(oracle='Holder inequality with independently authored receiver (2,-3,1), L1 norm 6, and exact rational allowance 0.012*0.25/6=0.0005')
def test_receiver_budget_propagates_component_sensitivity_in_correct_norm(fixture):
    from empirical_lawhood.api.domain_composition.rubisco_response.periodic_controls import prepare_receiver_refinement_budget
    budget = prepare_receiver_refinement_budget(budget_id='budget.exposed.receiver', receiver=fixture.model.identity,
        useful_error_hartree_per_bohr=D('.012'), numerical_allowance_fraction=D('.25'), receiver_l1_norm=D(6),
        justification='Exposed linear receiver: reserve one quarter of useful error for one force refinement.')
    assert budget.maximum_gradient_component_change_hartree_per_bohr == D('.0005')
    delta = (D('.0005'), D('-.0005'), D('.0005'))
    projected = sum(r*g for r, g in zip((D(2), D(-3), D(1)), delta, strict=True))
    assert projected == D('.003') == budget.receiver_useful_error_hartree_per_bohr*budget.numerical_allowance_fraction
    assert decode_canonical_bytes(budget.canonical_bytes(), owner.PeriodicRefinementBudget, maximum_bytes=2**20) == budget
    with pytest.raises(ValueError, match='L1 sensitivity'):
        replace(budget, maximum_gradient_component_change_hartree_per_bohr=D('.0006'))


@pytest.mark.parametrize('change', ('missing-kind', 'unsorted-kind', 'unknown-kind', 'zero', 'nan', 'rationale', 'partial-derivation', 'fraction'))
def test_refinement_budget_requires_prospective_complete_selection(fixture, change):
    protocol, _, _ = selected(fixture)
    budget = protocol.refinements[0].budget
    with pytest.raises((ValueError, ArithmeticError)):
        if change == 'missing-kind': replace(protocol, required_refinement_kinds=('GRID', 'SCF'))
        elif change == 'unsorted-kind': replace(protocol, required_refinement_kinds=('SCF', 'GRID'))
        elif change == 'unknown-kind': replace(protocol, required_refinement_kinds=('UNDECLARED',))
        elif change == 'zero': replace(budget, maximum_gradient_component_change_hartree_per_bohr=D(0))
        elif change == 'nan': replace(budget, maximum_gradient_component_change_hartree_per_bohr=D('NaN'))
        elif change == 'rationale': replace(budget, justification='')
        elif change == 'partial-derivation': replace(budget, receiver=fixture.model.identity)
        else: owner.refinement_budget_from_receiver(budget_id='budget.overdrawn', receiver=fixture.model.identity,
            useful_error_hartree_per_bohr=D(1), numerical_allowance_fraction=D(2), receiver_l1_norm=D(1),
            justification='This deliberately exceeds the receiver allowance.')


def test_unbudgeted_old_refinement_cannot_be_promoted(fixture):
    protocol, _, _ = selected(fixture)
    original = protocol.refinements[0].to_document()
    original['version'] = '1.0.0'
    original['value'].pop('budget')
    with pytest.raises(ValueError):
        decode_canonical_bytes(json.dumps(original).encode(), owner.PeriodicNumericalRefinement, maximum_bytes=2**20)


@pytest.mark.numerical(oracle='Independent exact array difference (3,4,0) has maximum component 4, component RMS sqrt(25/(3N)), and energy difference -3')
def test_refinement_metrics_and_authored_limits_are_independently_assessed(fixture):
    from empirical_lawhood.domains.rubisco.rubisco_response import periodic_control_read as reader
    from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
    protocol, _, raw = selected(fixture)
    budget = replace(protocol.refinements[0].budget,
        maximum_gradient_component_change_hartree_per_bohr=D('3.5'),
        maximum_rms_gradient_component_change_hartree_per_bohr=D(1),
        maximum_absolute_energy_change_hartree=D(4))
    protocol = replace(protocol, refinements=(replace(protocol.refinements[0], budget=budget),))
    points = owner.control_points(protocol, raw)
    base = np.zeros((protocol.physical_atom_count, 3))
    perturbed = base.copy(); perturbed[0] = [3., 4., 0.]
    values = {points[0].point_id:(7., base), points[-1].point_id:(4., perturbed)}
    row, = reader._refinements(protocol, points, values)
    assert row.energy_change_hartree == -3
    assert row.maximum_gradient_component_change_hartree_per_bohr == 4
    assert float(row.rms_gradient_component_change_hartree_per_bohr) == pytest.approx((25/(3*protocol.physical_atom_count))**.5)
    assert row.rms_gradient_component_change_hartree_per_bohr < budget.maximum_rms_gradient_component_change_hartree_per_bohr
    assert row.disposition is A.FALSIFIED  # One bad component is not hidden by a small whole-enzyme RMS.
    with pytest.raises(ValueError, match='sensitivity disposition'):
        replace(row, disposition=A.SATISFIED)


@pytest.mark.parametrize('energy,maximum,rms,expected', (
    ('-2', '1', '.5', 'SATISFIED'), ('-2.00000000000000000000000000000000000000000000000001', '1', '.5', 'FALSIFIED'),
    ('2', '1.0000000000000000000001', '.5', 'FALSIFIED'), ('2', '1', '.5000000000000000000001', 'FALSIFIED'),
    (None, None, None, 'UNEVALUABLE')))
def test_refinement_criteria_are_inclusive_signed_energy_safe_and_missing_aware(energy, maximum, rms, expected):
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_read import _refinement_disposition
    budget = owner.PeriodicRefinementBudget('budget.exposed.exact', D(1), 'Exact boundary conformance control.',
        maximum_rms_gradient_component_change_hartree_per_bohr=D('.5'), maximum_absolute_energy_change_hartree=D(2))
    values = tuple(None if value is None else D(value) for value in (energy, maximum, rms))
    assert _refinement_disposition(budget, *values).value == expected
