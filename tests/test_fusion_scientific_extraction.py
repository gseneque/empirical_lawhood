"""Independent reference controls for reusable fusion and reactor calculations.

No native engine, external input acquisition, CI profile or remote GPU execution.
"""
from decimal import Decimal as D
from math import pi
import subprocess
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.domains.fusion.numerical_denominator import evaluate_common_density_gauge
from empirical_lawhood.domains.fusion.prepared_base import _binomial_interval, _one_sided_lower, complete_radiation_receiver
from empirical_lawhood.domains.fusion.preparation_path_sensitivity import _log_ratio
from empirical_lawhood.domains.reactor.reactor_causal_response.actuator_statements import project_stages
from empirical_lawhood.science.identity.references import NamedDecimal


def test_foundation_and_fusion_scientific_imports_do_not_contact_adapters():
    script = '''
import importlib.abc
import sys
class NoEffects(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith("empirical_lawhood.adapters") or fullname.split(".")[0] in {"gymtorax", "torax", "jax", "freegsnke", "pybamm", "h5py"}:
            raise AssertionError("scientific import crossed effect boundary: " + fullname)
sys.meta_path.insert(0, NoEffects())
from empirical_lawhood.domains.fusion.prepared_base import development_cells, paired_views
from empirical_lawhood.domains.fusion.numerical_denominator import all_views
from empirical_lawhood.domains.fusion.preparation_path_sensitivity import evaluation_cells
from empirical_lawhood.domains.fusion.torax_flagship.evaluation import evaluate_torax_panel
from empirical_lawhood.domains.fusion.mast_archive.endpoints import reduce_mast_endpoint
from empirical_lawhood.domains.fusion.mast_torax_state_transport.contracts.support_projection import project_mapped_action_support
from empirical_lawhood.domains.fusion.mast_freegsnke_static_transport.assessment import face_point_estimates
from empirical_lawhood.domains.fusion.mastu_freegsnke_response.canary_assessment import select_canary
from empirical_lawhood.domains.fusion.mastu_release_qualification.conversion import audit_voltage_source
from empirical_lawhood.domains.reactor.reactor_causal_response.actuator import Actuator, measured_labels
from empirical_lawhood.domains.reactor.reactor_prefix_response.reference_forecast import ReferenceObserverReactorForecast
from empirical_lawhood.domains.fusion.gym_torax_native.native_episode import finalize_gym_torax_episode
from empirical_lawhood.domains.fusion.gym_torax_native.projection import project_gym_torax_episode
assert Actuator().project_stages
assert development_cells() and paired_views() and all_views() and evaluation_cells()
'''
    subprocess.run([sys.executable, '-c', script], check=True)


@pytest.mark.numerical(oracle='For a uniform density of 2e19 and unit minor radius at current pi*1e6 A, the Greenwald limit is 1e20, so both common density ratios are 0.2 regardless of interpolation grid.')
@pytest.mark.parametrize('cells', [5, 9, 17])
def test_common_density_gauge_uniform_field(cells):
    result = evaluate_common_density_gauge(
        receiver_clock_s=1, common_grid_cells=cells,
        rho=np.array([.1, .3, .5, .7, .9]),
        density=np.full(5, 2e19), vpr=np.array([1., 2., 3., 4., 5.]),
        current=pi*1e6, minor_radius=1.,
        source_volume_density=D('2e19'), source_line_density=D('2e19'),
        source_volume_fgw=D('.2'), source_line_fgw=D('.2'),
    )
    assert float(result.common_volume_density_m3) == pytest.approx(2e19, rel=2e-15)
    assert float(result.common_line_density_m3) == pytest.approx(2e19, rel=2e-15)
    assert float(result.common_volume_fgw) == pytest.approx(.2, abs=2e-15)
    assert float(result.common_line_fgw) == pytest.approx(.2, abs=2e-15)
    assert result.source_volume_identity_residual < D('1e-15')
    assert result.source_line_identity_residual < D('1e-15')


def test_common_density_gauge_refuses_nonpositive_greenwald_scale():
    with pytest.raises(ValueError, match='Greenwald denominator'):
        evaluate_common_density_gauge(
            receiver_clock_s=1, common_grid_cells=5,
            rho=np.array([.25, .75]), density=np.array([1., 1.]), vpr=np.ones(2),
            current=0., minor_radius=1., source_volume_density=D(1), source_line_density=D(1),
            source_volume_fgw=D(1), source_line_fgw=D(1),
        )


@pytest.mark.numerical(oracle='Exact Decimal receiver arithmetic: radiation 3 W divided by heat 12 W is one quarter; the source operands are unchanged.')
def test_radiation_receiver_is_exact_and_does_not_mutate_inputs():
    values = {
        'receiver.p-heat-total': NamedDecimal('receiver.p-heat-total', D(12), 'W'),
        'receiver.p-radiation-electron': NamedDecimal('receiver.p-radiation-electron', D(3), 'W'),
    }
    result, missing = complete_radiation_receiver(values)
    assert {x.value_id: x.value for x in result}['receiver.radiated-fraction'] == D('.25')
    assert not missing and len(values) == 2


@pytest.mark.parametrize('heat', [None, D(0), D(-1)])
def test_radiation_receiver_preserves_unevaluable_operand(heat):
    values = {'receiver.p-radiation-electron': NamedDecimal('receiver.p-radiation-electron', D(3), 'W')}
    if heat is not None:
        values['receiver.p-heat-total'] = NamedDecimal('receiver.p-heat-total', heat, 'W')
    result, missing = complete_radiation_receiver(values, ('upstream.missing',))
    assert missing == ('receiver.radiated-fraction', 'upstream.missing')
    assert 'receiver.radiated-fraction' not in {x.value_id for x in result}


@pytest.mark.numerical(oracle='Clopper-Pearson for one trial is [0,0.975] after zero successes and [0.025,1] after one success; an all-success n=4 one-sided lower bound is the fourth root of 0.05.')
def test_binomial_endpoints_against_closed_form():
    assert _binomial_interval(0, 1) == (D(0), D('.975'))
    assert _binomial_interval(1, 1) == (D('.025'), D(1))
    assert float(_one_sided_lower(4, 4)) == pytest.approx(.05**.25, abs=2e-15)
    assert _one_sided_lower(0, 4) == 0


@pytest.mark.numerical(oracle='The natural log of a ratio of one is zero; reciprocal positive ratios have opposite natural logs.')
def test_preparation_path_log_ratio_symmetry():
    assert _log_ratio(D(7), D(7)) == 0
    assert float(_log_ratio(D(3), D(2))) == pytest.approx(-float(_log_ratio(D(2), D(3))), abs=1e-15)


@pytest.mark.numerical(oracle='Requested feed 1 clips to 0.032 and slews from 0 by 0.002*10=0.02; jacket 350 clips to 347.6 and slews from 316 by 0.23*10=2.3.')
def test_reactor_actuator_projection_against_hand_calculation():
    params=SimpleNamespace(dose_window_s=(600.,25200.), dose_total_kg=287.3,
        sample_dt_s=10., feed_max_kg_s=.032, feed_rate_kg_s2=.002,
        tj_cmd_min_k=279.3, tj_cmd_max_k=347.6, tj_cmd_rate_k_s=.23)
    assert project_stages(params,600.,0.,0.,316.,1.,350.) == pytest.approx((.032,347.6,.02,318.3),abs=1e-12)


@pytest.mark.numerical(oracle='For a constant normalized flux error 0.1, RMS and max error are 0.1; shifts (0.03,0.04) and (0.06,0.08) have Euclidean lengths 0.05 and 0.1.')
def test_static_transport_metrics_consume_arrays_with_closed_form_distances():
    from empirical_lawhood.domains.fusion.mast_freegsnke_static_transport.assessment import (
        COORDINATES, SLICE_TIMES_S, VIEWS, face_point_estimates, static_output_validity,
    )
    n = len(SLICE_TIMES_S)
    axis = np.tile([1., 0.], (n, 1))
    xpoints = np.tile([1., -1.], (n, 1))
    receiver = {
        'psi_total_wb': np.full((n, 2, 2), 3.),
        'psi_axis_wb': np.ones(n), 'psi_boundary_wb': np.full(n, 5.),
        'axis_rz_m': axis, 'xpoints_rz_m': xpoints[:, None, :],
        'midplane_r_m': np.zeros((n, 2)),
    }
    output = {}
    for coordinate in COORDINATES:
        for view in VIEWS:
            key = coordinate.lower() + '__' + view.replace('-', '_')
            fields = {
                'valid': np.ones(n, dtype=bool),
                'relative_change': np.full(n, .01), 'runtime_s': np.ones(n),
                'psi_normalized': np.full((n, 2, 2), .6),
                'axis_rz_m': axis + [.03, .04],
                'xpoint_rz_m': xpoints + [.06, .08],
                'xpoint_flux_mismatch': np.zeros(n),
                'topology_code': np.full(n, 'LOWER_SINGLE_NULL'),
                'midplane_r_m': np.tile([-.1, .2], (n, 1)),
            }
            output.update({key+'__'+name: value for name, value in fields.items()})
    metrics = face_point_estimates(receiver, output)
    for coordinate in COORDINATES:
        for view in VIEWS:
            row = metrics[coordinate][view]
            np.testing.assert_allclose(row['flux_rms_1'], .1, rtol=0, atol=1e-15)
            np.testing.assert_allclose(row['flux_max_abs_1'], .1, rtol=0, atol=1e-15)
            np.testing.assert_allclose(row['axis_distance_m'], .05, rtol=0, atol=1e-15)
            np.testing.assert_allclose(row['xpoint_distance_m'], .1, rtol=0, atol=1e-15)
            np.testing.assert_allclose(row['midplane_max_abs_m'], .2, rtol=0, atol=1e-15)
            assert all(row['topology_match'])
    assert all(static_output_validity(output).values())
    key = COORDINATES[0].lower() + '__baseline_65__valid'
    output[key][0] = False
    assert static_output_validity(output)[COORDINATES[0]] is False
    assert all(metrics[COORDINATES[0]]['baseline-65']['complete_cell'])


@pytest.mark.numerical(oracle='Bilinear interpolation reproduces a linear flux field exactly: normalized psi=(r+z)/4 when axis=1 and boundary=5; a valid lower X point and no wall contact give a valid static cell.')
def test_static_equilibrium_normalization_regridding_and_invalid_wall():
    from empirical_lawhood.domains.fusion.mast_freegsnke_static_transport.assessment import assess_static_equilibrium
    r = np.linspace(1., 2., 5)
    z = np.linspace(-1., 1., 7)
    rr, zz = np.meshgrid(r, z, indexing='ij')
    inputs = dict(
        psi_native=1.+rr+zz, psi_axis_native=1., psi_boundary_native=5.,
        r_coordinates=r, z_coordinates=z, grid=np.array([1.,2.,-1.,1.]),
        xpoints=np.array([[1.5,-.5,5.], [1.5,.5,5.1]]),
        midplane=np.array([1.1,1.9]), axis_rz=np.array([1.5,0.]),
        relative_change=1e-7, intersects_wall=False, is_limited=False, runtime_s=.25,
    )
    result = assess_static_equilibrium(**inputs)
    common_r, common_z = np.meshgrid(np.linspace(1.,2.,65), np.linspace(-1.,1.,65), indexing='ij')
    np.testing.assert_allclose(result['psi_normalized'], (common_r+common_z)/4, rtol=0, atol=5e-16)
    np.testing.assert_array_equal(result['xpoint_rz_m'], [1.5,-.5])
    assert result['topology_code'] == 'LOWER_SINGLE_NULL' and result['valid']
    inputs['intersects_wall'] = True
    assert assess_static_equilibrium(**inputs)['valid'] is False


@pytest.mark.numerical(oracle='The symmetric-coil rule uses the first polarity and mean magnitude: [-2,-4] maps to -3 A; a passive current 5 A times multiplier 2 is 10 A.')
def test_coil_coordinate_map_against_hand_calculation():
    from empirical_lawhood.domains.fusion.mast_freegsnke_static_transport.assessment import map_coil_currents
    machine = {'active-symmetric': {'p4': {}}, 'passive': [{'name':'shell','efitGroup':'pass','current_multiplier':2.}]}
    result = map_coil_currents(('p4',), machine, 'SYMMETRY_COLLAPSED', ['P4_U','P4_L','PASS'], np.array([-2.,-4.,5.]))
    assert result == {'p4': -3., 'shell': 10.}


@pytest.mark.numerical(oracle='For diagonal inductance and resistance equal to identity, the p4 current response to unit voltage is 1-exp(-t); 5% of 5000 A headroom divided by that response sets the rounded admission voltage.')
def test_canary_admission_voltage_against_scalar_rc_solution():
    from math import exp, floor
    from empirical_lawhood.domains.fusion.mastu_freegsnke_response.canary_assessment import _admission_limit, voltage_vector, current_extrema
    labels = ('Solenoid','px','d1','d2','d3','dp','d5','d6','d7','p4','p5','p6')
    baseline = np.zeros(12)
    baseline[9] = -5000.
    actual = _admission_limit(np.eye(12), np.ones(12), labels, baseline)
    expected = floor(250./(1.-exp(-.015))*1e6)/1e6
    assert actual == pytest.approx(expected, abs=1e-6)
    voltage, digest = voltage_vector(baseline, np.full(12,2.), labels, 3.)
    assert voltage[9] == -9997. and np.count_nonzero(voltage) == 1 and len(digest) == 64
    assert baseline[9] == -5000.
    lo, hi = current_extrema(np.array([1.,2.]), np.array([3.,4.]), np.array([0.,5.]))
    np.testing.assert_array_equal(lo, [0.,2.])
    np.testing.assert_array_equal(hi, [3.,5.])


@pytest.mark.numerical(oracle='A 12 V source over series resistors 1,2,3 ohms carries 2 A, so node voltages are 10 and 6 V; the stated 3x3 bipartite graph has matching cardinality two.')
def test_independent_circuit_and_matching_oracles():
    from empirical_lawhood.domains.circuits.reference_oracles import _analytic_equilibrium, _brute_matching_rank, _rank_audit
    descriptor=SimpleNamespace(left_source_resistance_ohms=D(1),right_termination_resistance_ohms=D(3),interior_resistances_ohms=(D(2),))
    np.testing.assert_array_equal(_analytic_equilibrium(descriptor,12.), [10.,6.])
    assert _brute_matching_rank(np.array([[1,0,0],[1,0,0],[0,1,0]], dtype=bool)) == 2
    _rank_audit(-np.eye(2), np.eye(2), lag=.1, maximum_depth=2, error_prefix='REFERENCE')
    with pytest.raises(ValueError, match='REFERENCE_DUPLICATE_PRESENT_CONTROL_FAILED'):
        _rank_audit(-np.eye(9), np.eye(9), lag=.1, maximum_depth=0, error_prefix='REFERENCE')


@pytest.mark.numerical(oracle='For one=2K, J=K, K1=2K, K2=-K, BP-SOMF two=0.5K. With c=2, factor=1/8, so the one/two contributions are K/4 and K/16, respectively.')
def test_breit_pauli_supplied_integrals_against_hand_calculation():
    from empirical_lawhood.domains.rubisco.electronic.spin_orbit import combine_breit_pauli_integrals
    k=np.tile(np.array([[0.,1.],[-1.,0.]]),(3,1,1))
    terms=combine_breit_pauli_integrals(2*k,k,2*k,-k,light_speed_atomic_units=2.)
    np.testing.assert_array_equal(terms['soc-one-electron-imaginary'],k/4)
    np.testing.assert_array_equal(terms['soc-two-electron-imaginary'],k/16)
    invalid=k.copy();invalid[0,0,0]=1.
    with pytest.raises(ValueError,match='finite antisymmetric Cartesian conventions'):
        combine_breit_pauli_integrals(2*k,invalid,2*k,-k,light_speed_atomic_units=2.)
