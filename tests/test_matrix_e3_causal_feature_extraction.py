# SPDX-License-Identifier: MPL-2.0
"""Literal causal feature controls; no native observations or qualification.

States, spectra and witnesses are explicit exposed operands. Source/model
fixtures create metadata only; no acquisition, fitted model or authority occurs.
"""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from hashlib import sha256
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import FactorLifetime
from empirical_lawhood.adapters.methods.matrix_scheduled_history import forecast as method, records as r, science
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.test_matrix_factor_confirmation_eligibility import publish, stock as source_stock
from tests.test_matrix_parameter_history import source as parameter_template
from tests.test_matrix_response_error_prediction import observation
from tests.test_matrix_scheduled_history import scheduled as scheduled_source, with_parents
from tests.test_matrix_scheduled_history_bindings import bank as frozen_bank


def _case(tmp_path, *, family=FOUR_FAMILY_PREPARATION_IDS[1], unequal_mass=False):
    tmp_path.mkdir(parents=True, exist_ok=True)
    plane, original = source_stock.__wrapped__(tmp_path, parameter_template().provenance)
    _, sources = scheduled_source.__wrapped__((plane, original))
    first = sources[0]
    coordinates = tuple(replace(c, family_id=family, ramp_ticks=32, autonomous_ticks=16,
        observation_ticks=tuple(range(49)), member=replace(c.member, mass_y=c.member.mass_x + 1)
        if unequal_mass else c.member) for c in first.allocation.coordinates)
    revised = {coordinate_identity(old): coordinate_identity(new)
        for old, new in zip(first.allocation.coordinates, coordinates, strict=True)}
    allocation = replace(first.allocation, coordinates=coordinates,
        roots=tuple(replace(row, coordinate=revised[row.coordinate]) for row in first.allocation.roots),
        matched_scopes=tuple(replace(scope, coordinates=tuple(revised[c] for c in scope.coordinates))
            for scope in first.allocation.matched_scopes))
    reservation = replace(first.reservation, allocation=allocation,
        publication=publish(plane, allocation, 'exposed.feature.allocation'))
    policy = replace(first.policy, cutoff_tick=32, origin_sector='Y',
        factor_rule=replace(first.policy.factor_rule, lattice=tuple(range(33))))
    selection = replace(first.specification.selection, reservation=r.identity(reservation),
        prefix_policies=(policy,), coordinate_policies=tuple((coordinate_identity(c), r.identity(policy)) for c in coordinates))
    specification = replace(first.specification, selection=selection,
        publication=publish(plane, selection, 'exposed.feature.selection'))
    sources = tuple(with_parents(source, reservation=reservation, specification=specification) for source in sources)
    _, sources, commitment = frozen_bank.__wrapped__((plane, sources))
    source = next(source for source in sources if source.root_id == commitment.selected_root_ids[0])

    frame = np.zeros((3, 4, 4), dtype='<c16')
    frame[:, 0, 0] = (1, 2, 3)
    arrays = {'frame': frame, 'primary_ticks': np.arange(33, dtype='<i8'),
        'fine_ticks': np.arange(65, dtype='<i8'),
        'primary_alpha_tilde': np.asarray([source.coordinate.couplings(t) for t in range(33)], dtype='<f8')}
    for name, amplitudes in (('positions', (3, 4)), ('momenta', (12, 5))):
        arrays['primary_' + name] = np.zeros((33, 2, 3, 4, 4), dtype='<c16')
        arrays['primary_' + name][-1, :, 0, 0, 0] = amplitudes
    spectrum = np.arange(15, dtype='<f8') / 8
    diagnostics = {'primary_y_spectrum': np.repeat(spectrum[None], 3, axis=0)}
    opaque = lambda name, kind: ObjectIdentity('exposed.feature.' + name, kind.SCHEMA, '1.0.0', 'a' * 64)
    history = opaque('history', r.ScheduledPrefixHistory)
    numerical = opaque('numerical', r.ScheduledNumericalAssessment)
    lifetime = FactorLifetime(0, 'LEFT_PRESENT', 'RIGHT_CENSORED', 32, None, ())
    trace = r.ScheduledPrefixTrace(source.policy.factor_rule.identity, 'PRIMARY', 'Y',
        (observation(0, angle=D(999)), observation(16, angle=D(2)), observation(32, angle=D(3))),
        lifetime, lifetime)
    _, diagnostic_operand = science._array_product(source, diagnostics, role='PREFIX_DIAGNOSTICS',
        artifact_id='exposed.feature.diagnostics', producers=(r.identity(source),))
    witness = r.ScheduledPrefixWitness('exposed.feature.witness', r.identity(source), history, numerical,
        r.identity(source.policy), (trace,), diagnostic_operand)
    _, causal_operand = science._array_product(source, arrays, role='CAUSAL_STATE',
        artifact_id='exposed.feature.causal-arrays', producers=(r.identity(source),))
    prefix = r.ScheduledCausalPrefix('exposed.feature.prefix', r.identity(source), history, numerical,
        r.identity(witness), opaque('assessment', r.ScheduledFrameAssessment), r.identity(source.policy),
        source.root.root, 32, sha256(frame.tobytes()).hexdigest(), 'AVAILABLE', None, causal_operand)
    return SimpleNamespace(source=source, prefix=prefix, witness=witness, arrays=arrays,
        diagnostics=diagnostics, design=commitment.forecast_design)


@pytest.fixture(scope='module')
def case(tmp_path_factory):
    return _case(tmp_path_factory.mktemp('literal-causal-feature'))


@pytest.fixture(autouse=True)
def block_producers(monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_factor_response import response_error_prediction
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history_segments, parameter_source

    def forbidden(*args, **kwargs):
        raise AssertionError('literal feature entered native acquisition, RNG, fit or eigensolve')

    for owner, names in ((parameter_history_segments, ('acquire_parameter_segment',)),
            (parameter_source, ('acquire_parameter_history',)),
            (response_error_prediction, ('fit_error_model', 'fit_scheduled_error_model')),
            (np.random, ('Generator', 'default_rng', 'PCG64', 'PCG64DXSM')),
            (np.linalg, ('eigh', 'eigvalsh'))):
        for name in names:
            monkeypatch.setattr(owner, name, forbidden)


def _extract(case, *, prefix=None, witness=None, arrays=None, diagnostics=None, window=32, cadence=16):
    return method.causal_feature_from_prefix(case.source, case.prefix if prefix is None else prefix,
        case.witness if witness is None else witness, case.arrays if arrays is None else arrays,
        case.diagnostics if diagnostics is None else diagnostics, feature_id='exposed.feature.result',
        feature_window_ticks=window, feature_cadence_ticks=cadence)


def test_original_wrapper_and_explicit_feature_have_identical_canonical_output(case):
    explicit = _extract(case)
    original = method.causal_feature(case.design, case.source, case.prefix, case.witness,
        case.arrays, case.diagnostics, feature_id=explicit.feature_id)
    assert explicit.disposition == 'AVAILABLE'
    assert original.canonical_bytes() == explicit.canonical_bytes()
    assert decode_canonical_bytes(explicit.canonical_bytes(), method.ScheduledForecastFeature,
        maximum_bytes=None) == explicit
    assert explicit.source == r.identity(case.source) and explicit.prefix == r.identity(case.prefix)
    assert (explicit.root_id, explicit.independent_group_id, explicit.clock_id, explicit.cutoff,
        explicit.frame_sha256) == (case.source.root_id, case.source.root.root.independent_group_id,
        case.source.coordinate.clock_id, D('.032'), case.prefix.frame_sha256)


def test_literal_feature_equations_keep_actual_units_spectrum_and_window(case):
    values = dict(_extract(case).values)
    # Retain the realized binary coupling, including its difference from the
    # decimal schedule target. No rounding or target substitution is allowed.
    assert (values['alpha-x'], values['alpha-y'], values['bath-temperature'], values['friction'],
        values['cross-gamma'], values['potential-m']) == (D('2.0999999999999996'), D('4.4'), D(2), D(1), D(1), D('.5'))
    assert (values['largest-y-rate'], values['slow-y-mean'], values['third-fourth-y-gap']) == (D('1.75'), D('.125'), D('.125'))
    assert (values['associative-leakage'], values['lie-leakage'], values['factor-fit-angle'], values['trailing-angle']) == (D('.01'), D('.02'), D(2), D(3))
    assert values['family-de-anneal'] == 1 and values['family-x-first'] == values['family-y-first'] == 0
    with localcontext() as context:
        context.prec = 50
        assert tuple(values[name] for name in ('position-x-norm', 'position-y-norm',
            'momentum-x-norm', 'momentum-y-norm')) == tuple(D(value).ln() for value in (4, 5, 13, 6))


@pytest.mark.parametrize('field', ('feature_window_ticks', 'feature_cadence_ticks'))
@pytest.mark.parametrize('value', (0, -1, True, False, 16.0, D(16), '16', None, np.int64(16)))
def test_explicit_window_and_cadence_require_positive_exact_integers(case, field, value):
    options = {'window': 32, 'cadence': 16}
    options['window' if field == 'feature_window_ticks' else 'cadence'] = value
    with pytest.raises(ValueError, match='positive exact integer'):
        _extract(case, **options)


def test_selected_window_is_explicit_and_does_not_read_a_historical_design(case):
    # A shorter valid window uses just the final complete interval. The helper
    # receives no model, design, seal or historical role constructor.
    assert _extract(case, window=16).canonical_bytes() == _extract(case).canonical_bytes()
    assert _extract(case, cadence=8).disposition == 'REFUSED'  # Missing actual tick 8/24 observations.
    assert _extract(case, window=16, cadence=32).disposition == 'REFUSED'  # Cutoff absent.


def test_preceding_interval_and_future_observations_do_not_enter_causal_values(case):
    trace, = case.witness.traces
    changed = replace(trace, observations=(replace(trace.observations[0], adjacent_angle_degrees=None),
        *trace.observations[1:], observation(48, angle=D(888))))
    witness = replace(case.witness, traces=(changed,))
    assert _extract(case, witness=witness).canonical_bytes() == _extract(case).canonical_bytes()


@pytest.mark.parametrize('damage', ('prefix-source', 'policy', 'root', 'cutoff',
    'witness-source', 'history', 'numerical'))
def test_original_source_prefix_and_witness_boundaries_still_raise(case, damage):
    prefix, witness = case.prefix, case.witness
    if damage in ('prefix-source', 'policy'):
        field = 'source' if damage == 'prefix-source' else 'policy'
        value = replace(getattr(prefix, field), object_fingerprint='f' * 64)
        prefix = replace(prefix, **{field: value}, arrays=replace(prefix.arrays, source=value)
            if field == 'source' else prefix.arrays)
    elif damage == 'root':
        prefix = replace(prefix, root=replace(prefix.root, independent_group_id='foreign.feature.group'))
    elif damage == 'cutoff':
        prefix = replace(prefix, cutoff_tick=31)
    else:
        field = 'source' if damage == 'witness-source' else damage
        value = replace(getattr(witness, field), object_fingerprint='f' * 64)
        witness = replace(witness, **{field: value}, arrays=replace(witness.arrays, source=value)
            if field == 'source' else witness.arrays)
    with pytest.raises(ValueError, match='prefix/source/witness/clock boundary'):
        _extract(case, prefix=prefix, witness=witness)
    with pytest.raises(ValueError, match='prefix/source/witness/clock boundary'):
        method.causal_feature(case.design, case.source, prefix, witness, case.arrays, case.diagnostics,
            feature_id='exposed.feature.result')


def _damaged(case, damage):
    arrays = {name: value.copy() for name, value in case.arrays.items()}
    diagnostics = {name: value.copy() for name, value in case.diagnostics.items()}
    witness = case.witness
    if damage in ('primary-clock', 'fine-clock', 'frame', 'couplings'):
        name = {'primary-clock': 'primary_ticks', 'fine-clock': 'fine_ticks',
            'frame': 'frame', 'couplings': 'primary_alpha_tilde'}[damage]
        arrays[name].flat[-1] += 1
    elif damage == 'missing-array':
        del arrays['primary_positions']
    elif damage == 'spectrum-shape':
        diagnostics['primary_y_spectrum'] = diagnostics['primary_y_spectrum'][:, :-1]
    elif damage in ('nonfinite-spectrum', 'negative-feature'):
        diagnostics['primary_y_spectrum'][-1, -1] = np.nan if damage == 'nonfinite-spectrum' else -1
    else:
        trace, = witness.traces
        if damage == 'missing-observation':
            trace = replace(trace, observations=(trace.observations[0], trace.observations[-1]))
        elif damage == 'missing-angle':
            trace = replace(trace, observations=(*trace.observations[:-1], replace(trace.observations[-1], adjacent_angle_degrees=None)))
        elif damage == 'ambiguous-observation':
            trace = replace(trace, observations=(*trace.observations[:-1], replace(trace.observations[-1], alignment_ambiguous=True)))
        elif damage == 'missing-primary-y':
            trace = replace(trace, sector='X')
        witness = replace(witness, traces=(trace,))
    return witness, arrays, diagnostics


@pytest.mark.parametrize('damage', ('primary-clock', 'fine-clock', 'frame', 'couplings',
    'missing-array', 'spectrum-shape', 'nonfinite-spectrum', 'negative-feature',
    'missing-observation', 'missing-angle', 'ambiguous-observation', 'missing-primary-y'))
def test_original_native_array_and_measurement_refusals_keep_identical_outputs(case, damage):
    witness, arrays, diagnostics = _damaged(case, damage)
    result = _extract(case, witness=witness, arrays=arrays, diagnostics=diagnostics)
    original = method.causal_feature(case.design, case.source, case.prefix, witness, arrays,
        diagnostics, feature_id=result.feature_id)
    assert result.disposition == 'REFUSED' and result.values == ()
    assert original.canonical_bytes() == result.canonical_bytes()


@pytest.mark.parametrize('disposition,expected', (('NO_ORIGIN', 'NO_CAUSAL_ORIGIN'), ('UNEVALUABLE', 'UNAVAILABLE')))
def test_nonuse_retains_original_disposition_without_reading_arrays(case, disposition, expected):
    class NoRead:
        def __getitem__(self, key):
            raise AssertionError('nonuse feature read numerical operands')

    prefix = replace(case.prefix, disposition=disposition, frame_sha256=None, reason='EXPOSED_NONUSE')
    result = _extract(case, prefix=prefix, arrays=NoRead(), diagnostics=NoRead())
    original = method.causal_feature(case.design, case.source, prefix, case.witness, NoRead(), NoRead(),
        feature_id=result.feature_id)
    assert result.disposition == expected and result.values == () and result.frame_sha256 is None
    assert original.canonical_bytes() == result.canonical_bytes()


def test_historical_wrapper_runs_original_design_guard_before_delegation(case, monkeypatch):
    changed = replace(case.design, source_scopes=tuple((root, method.DEVELOPMENT_POINT)
        for root, _ in case.design.source_scopes))

    def forbidden(*args, **kwargs):
        raise AssertionError('historical source guard did not run first')

    monkeypatch.setattr(method, 'causal_feature_from_prefix', forbidden)
    with pytest.raises(ValueError, match='role'):
        method.causal_feature(changed, case.source, case.prefix, case.witness, case.arrays,
            case.diagnostics, feature_id='exposed.feature.forbidden')


@pytest.mark.parametrize('family,expected,flags', (
    (FOUR_FAMILY_PREPARATION_IDS[0], 'cc1.history.co-anneal', (0, 0, 0)),
    (FOUR_FAMILY_PREPARATION_IDS[1], 'cc1.history.de-anneal', (1, 0, 0)),
    (FOUR_FAMILY_PREPARATION_IDS[2], 'cc1.history.x-first', (0, 1, 0)),
    (FOUR_FAMILY_PREPARATION_IDS[3], 'cc1.history.y-first', (0, 0, 1))))
def test_original_family_mapping_is_preserved(tmp_path, family, expected, flags):
    case = _case(tmp_path, family=family)
    result = _extract(case)
    assert result.family_id == expected
    values = dict(result.values)
    assert tuple(values[name] for name in ('family-de-anneal', 'family-x-first', 'family-y-first')) == flags


def test_original_member_contract_still_refuses_unequal_masses(tmp_path):
    with pytest.raises(ValueError, match='only symmetric mass members'):
        _case(tmp_path, unequal_mass=True)
