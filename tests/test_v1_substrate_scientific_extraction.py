"""Independent numerical controls for explicit supplied-data scientific components.

No native engine, external campaign, remote GPU or scientific qualification runs.
"""
from decimal import Decimal
import math
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.domains.chemistry.chemical_reactor.design import cantera_design
from empirical_lawhood.domains.chemistry.chemical_reactor.response_assessment import assess_cantera_state
from empirical_lawhood.domains.energy.grid2op.topology import connected_substation_components
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.methionine_geometry import rotate_methionine_chi1
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_density_seed import density_electron_populations
from empirical_lawhood.methods.selective_dependence_response.contracts import SelectiveDependenceResponseDisposition


@pytest.mark.numerical(oracle='A quarter-turn about the z axis maps (x,y,z) to (-y,x,z), fixes the bond frame and preserves all rotated-atom pair distances.')
def test_methionine_rotation_preserves_frame_distances_and_known_quarter_turn():
    coordinates = np.array([[1., 0., 0.], [0., 0., 0.], [0., 0., 1.],
                            [1., 0., 1.], [2., 0., 1.], [2., 1., 1.]])
    original = coordinates.copy()
    rotated, angle = rotate_methionine_chi1(coordinates, math.pi / 2)
    assert angle == 0
    np.testing.assert_array_equal(coordinates, original)
    np.testing.assert_array_equal(rotated[:3], coordinates[:3])
    np.testing.assert_allclose(rotated[3:], [[0., 1., 1.], [0., 2., 1.], [-1., 2., 1.]], atol=1e-15)
    before = np.linalg.norm(original[:, None] - original[None], axis=-1)
    after = np.linalg.norm(rotated[:, None] - rotated[None], axis=-1)
    np.testing.assert_allclose(after[3:, 3:], before[3:, 3:], atol=1e-15)


@pytest.mark.parametrize('status,expected', [([True, False, True], 3), ([True, True, True], 2), ([False, False, False], 5)])
@pytest.mark.numerical(oracle='Explicit five-vertex graph has three, two or five connected components when the supplied three edges are partly, fully or not active.')
def test_grid_component_receiver_counts_isolated_vertices_and_disconnected_lines(status, expected):
    assert connected_substation_components(5, status, [0, 1, 3], [1, 2, 4]) == expected


@pytest.mark.numerical(oracle='Methane fraction 0.002/0.1 gives conversion 0.98; unit elemental mass and temperatures 1820/2500 give the five independently stated scalar margins.')
def test_cantera_supplied_state_has_literal_conversion_and_noncompensating_margins():
    values, margins = assess_cantera_state(cantera_design(), inlet_ch4=.1,
        final_methane_mole_fraction=.002, carbon_monoxide_mole_fraction=.0002,
        elemental_mass_fractions=(.1, .2, .7), peak_temperature=2500., temperature=1820.)
    assert values['methane-conversion'] == .98
    assert values['element-error'] == 0
    assert margins == (Decimal('.0003'), Decimal('.000001'), Decimal('.03'), Decimal(200), Decimal(10))


def test_cantera_native_failure_keeps_full_invalid_receiver_census_without_invented_margins(monkeypatch):
    from empirical_lawhood.adapters.simulators.cantera_reaction_response.runtime import _condition

    class Gas:
        def __init__(self, *_):
            self.TPX = (600., 1., '')
        def equilibrate(self, _):
            pass
    class Reactor:
        def __init__(self, initial, **_):
            self.T = initial.TPX[0]
            self.mass = 1.
    class Network:
        def __init__(self, _):
            self.time = 0.
        def step(self):
            raise RuntimeError('literal simulated native failure')
    fake = SimpleNamespace(Solution=Gas, one_atm=1., Reservoir=lambda *a, **k: object(),
        IdealGasReactor=Reactor, MassFlowController=lambda *a, **k: object(),
        PressureController=lambda *a, **k: None, Wall=lambda *a, **k: None, ReactorNet=Network)
    monkeypatch.setitem(sys.modules, 'cantera', fake)
    preparation = {'bath-temperature':300., 'cold-checkpoint-temperature':600.,
        'equivalence-ratio':.8, 'heat-transfer-scale':1., 'hot-checkpoint-seed-temperature':1500.,
        'inlet-temperature':300., 'reactor-volume':.001}
    condition, margins = _condition(cantera_design(), preparation, denominator_id='heat-loss-low',
        history_id='cold-checkpoint', action_id='flow-hold', horizon_id='short')
    assert condition.stopped and condition.stop_code == 'cantera-runtimeerror'
    assert condition.disposition is SelectiveDependenceResponseDisposition.UNEVALUABLE
    assert condition.fibre_admitted is None
    assert margins == condition.gate_margins == ()
    assert tuple(value.receiver_id for value in condition.receivers) == cantera_design().receiver_ids
    assert all(not value.valid for value in condition.receivers)


@pytest.mark.numerical(oracle='Diagonal overlap (2,0.5) and the two diagonal density matrices give traces 2 and 1 independently by scalar multiplication.')
def test_density_populations_use_overlap_metric_and_preserve_both_spins():
    overlap = np.diag([2., .5])
    density = np.array([np.diag([.5, 2.]), np.diag([.25, 1.])])
    assert density_electron_populations(density, overlap, np.array([2., 1.])) == [2., 1.]
    with pytest.raises(ValueError, match='electron or spin population'):
        density_electron_populations(density, overlap, np.array([2., 2.]))


@pytest.mark.numerical(oracle='Post-step voltages -8,-4,0 have mean -4 and exactly two supplied spikes occur at or after the boundary.')
def test_neuron_receiver_includes_boundary_samples_and_clips_current_exactly():
    from empirical_lawhood.domains.biology.neuron_current_response.numerics import accept_current, summarize_post_step
    assert [accept_current(value, 10.) for value in (-3., 0., 4., 11.)] == [0., 0., 4., 10.]
    mean, count = summarize_post_step(np.array([0., 1., 2., 3.]), np.array([-10., -8., -4., 0.]),
        np.array([0., 1., 2.5]), 1.)
    assert mean == -4. and count == 2


@pytest.mark.numerical(oracle='For identity molecular orbitals the second occupied frontier projector has one at (1,1), energy -1 and gap 1; spin-square 1 differs from the doublet reference by 0.25.')
def test_frontier_orbital_and_spin_diagnostics_have_literal_projector_and_gap():
    from empirical_lawhood.domains.rubisco.electronic.frontier_diagnostics import frontier_orbital_diagnostics
    occupations = np.array([2., 2., *([0.] * 12)])
    result = frontier_orbital_diagnostics(spin=0, occupations=occupations, coefficients=np.eye(14),
        energies=np.arange(14, dtype=float) - 2., overlap=np.eye(14), ao_atom_indices=list(range(14)))
    assert result['homo_index_zero_based'] == 1
    assert result['homo_energy_hartree'] == -1.
    assert result['adjacent_occupied_gap_hartree'] == 1.
    expected = np.zeros((14, 14)); expected[1, 1] = 1.
    np.testing.assert_array_equal(result['one_electron_homo_density_matrix'], expected)
    opened = frontier_orbital_diagnostics(spin=1, occupations=None, coefficients=None,
        energies=None, overlap=None, ao_atom_indices=None, spin_square=(1., 2.2))
    assert opened == {'s_squared': 1., 'spin_multiplicity': 2.2, 's_squared_minus_doublet_reference': .25}


@pytest.mark.numerical(oracle='The downstream two values 4 and 5 have mean 4.5; diffusivity 0.02 times terminal value 5 over half-cell width 0.1 gives outward flux 1.')
def test_construct_validation_keeps_distinct_frozen_chart_and_flux_receiver():
    from empirical_lawhood.domains.chemistry.construct_validation.response import (
        cantera_construct_parameters, fipy_construct_parameters, fipy_construct_result,
    )
    residence, temperature, _, requested, accepted = cantera_construct_parameters(
        denominator_id='denominator.residence.0p10s', history_id='history.initial.1100k',
        action_id='action.low-flow', seed=17)
    assert (residence, temperature, requested, accepted) == (.1, 1100., .75, .75)
    diffusivity, requested, accepted, rate, _, _ = fipy_construct_parameters(
        denominator_id='denominator.diffusivity.0p02', action_id='action.hold', seed=17)
    assert (diffusivity, requested, accepted) == (.02, .5, .5)
    result, version = fipy_construct_result(unit_id='unit.literal', denominator_id='denominator.literal',
        history_id='history.literal', action_id='action.hold', values=np.arange(1., 6.),
        x=np.array([.1, .3, .5, .7, .9]), diffusivity=diffusivity, length=1., nx=5,
        requested_rate=requested, accepted_rate=accepted, applied_rate=rate,
        realized_integral=.01, steps=50, source_version='literal-exposed-fixture')
    assert {row.receiver_id: row.value for row in result.receivers} == {
        'receiver.downstream-mean': Decimal('4.5'), 'receiver.right-outward-flux': Decimal('1.0')}
    assert version == 'literal-exposed-fixture'


def test_scientific_owners_import_without_any_native_engine():
    import subprocess
    modules = (
        'empirical_lawhood.domains.battery.electrothermal_hierarchy',
        'empirical_lawhood.domains.battery.exact_restart',
        'empirical_lawhood.domains.battery.reduced_coordinate_sufficiency',
        'empirical_lawhood.domains.rubisco.electronic.frontier_diagnostics',
        'empirical_lawhood.domains.rubisco.rubisco_response.periodic_density_seed',
        'empirical_lawhood.domains.chemistry.chemical_reactor.response_assessment',
        'empirical_lawhood.domains.chemistry.construct_validation.response',
        'empirical_lawhood.domains.energy.grid2op.topology',
        'empirical_lawhood.domains.biology.neuron_current_response.numerics',
        'empirical_lawhood.domains.matrix.six_matrix_response.response_dynamics',
        'empirical_lawhood.domains.matrix.matrix_preparation_analysis.preparation_dynamics',
        'empirical_lawhood.domains.quantum.response_control.compatibility_assessment',
    )
    script = '''import importlib, importlib.abc, sys
class DenyNative(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'pybamm','pyscf','gpu4pyscf','cupy','openmm','cantera','fipy','brian2','grid2op'}:
            raise AssertionError('pure scientific import contacted native engine: '+fullname)
sys.meta_path.insert(0,DenyNative())
for module in MODULES: importlib.import_module(module)
'''.replace('MODULES', repr(modules))
    subprocess.run([sys.executable, '-c', script], check=True)
