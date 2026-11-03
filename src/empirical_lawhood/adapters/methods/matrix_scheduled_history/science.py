# SPDX-License-Identifier: MPL-2.0
"""Scheduled prefix assembly and independently checked causal delivery.

No native producer is called here. Assembly receives an already completed
segment. Cold checks use literal numerical equations and retained eigenpairs,
without RNG, an eigensolve or a post-cutoff observation.
"""

from hashlib import sha256
from types import SimpleNamespace

import numpy as np

from empirical_lawhood.adapters.methods.matrix_factor_lifetime import science as factor_science
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.products import validate_diagnostics
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.scalar_assessment import independent_scalar_closure_ratio
from empirical_lawhood.adapters.methods.matrix_history_analysis import algebra
from empirical_lawhood.adapters.methods.matrix_parameter_factor.independent import _control, pauli_residual, raw_operator
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import DIAGNOSTICS, METHODS as FACTOR_METHODS, expected_members as diagnostic_members, prefix
from empirical_lawhood.adapters.methods.matrix_parameter_history import independent
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterHistoryControl, coordinate_identity, expected_members
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import initial_parameter_state
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history_segments import ParameterSegmentValues, validate_segment_entry
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays, encode_matrix_arrays, matrix_array_members
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.references import ArtifactIdentity

from .records import (
    NAMESPACE, ScheduledArrays, ScheduledCausalPrefix, ScheduledCheckpoint, ScheduledDisposition, ScheduledFrameAssessment,
    ScheduledNumericalAssessment, ScheduledPrefixHistory, ScheduledPrefixTrace, ScheduledPrefixWitness, ScheduledUnavailable, identity,
)


def _prefix_coordinate(source):
    c = source.coordinate
    return SimpleNamespace(q=c.q, member=c.member, primary_view=c.primary_view, fine_view=c.fine_view,
        total_ticks=source.policy.cutoff_tick)


def unpack_native(source, raw, *, prefix_only=False):
    """Decode the bounded return; retain this owner's scientific array checks."""
    from empirical_lawhood.infrastructure.matrix_array_io import decode_native_matrix_arrays
    expected = expected_members(_prefix_coordinate(source) if prefix_only else source.coordinate)
    values = decode_native_matrix_arrays(raw, expected)
    (validate_prefix_arrays if prefix_only else validate_full_arrays)(source, values)
    return values



def validate_prefix_arrays(source, arrays):
    c, n = source.coordinate, source.policy.cutoff_tick
    expected = expected_members(_prefix_coordinate(source))
    if set(arrays) != set(expected):
        raise ValueError('scheduled prefix drops complete phase/noise/coupling/clock members')
    for name, (dtype, shape) in expected.items():
        value = arrays[name]
        if value.dtype.str != dtype or value.shape != shape or not np.isfinite(value).all():
            raise ValueError('scheduled prefix changes complete exact dtype/shape/finite cutoff')
        if dtype == '<c16' and np.linalg.norm(value-value.conj().swapaxes(-1, -2)) > 1e-10*max(1, np.linalg.norm(value)):
            raise ValueError('scheduled prefix loses full Hermitian phase/noise')
    initial = initial_parameter_state(c)
    for view, multiplier in (('primary', 1), ('fine', 2)):
        count = multiplier*n+1
        if (not np.array_equal(arrays[view+'_ticks'], np.arange(count, dtype='<i8'))
                or not np.array_equal(arrays[view+'_alpha_tilde'], np.asarray([c.couplings(t, refinement=multiplier) for t in range(count)], dtype='<f8'))
                or not np.array_equal(arrays[view+'_positions'][0], initial.positions)
                or not np.array_equal(arrays[view+'_momenta'][0], initial.momenta)):
            raise ValueError('scheduled prefix changes actual initial state, absolute paired clock or realized schedule')


def _array_product(source, arrays, *, role, artifact_id, producers, nonfinite=(), raw=None):
    supplied = raw is not None
    if raw is None:
        raw, members = encode_matrix_arrays(arrays, nonfinite_members=nonfinite)
    else:
        members = matrix_array_members(arrays, nonfinite_members=nonfinite)
    artifact = ArtifactIdentity(artifact_id, 'scheduled-'+role.lower(), MATRIX_ARRAY_SCHEMA,
        sha256(raw).hexdigest(), 'application/x-npz', len(raw))
    operand = ScheduledArrays('arrays.'+artifact_id, identity(source), role, artifact, members,
        tuple(sorted(producers, key=lambda x: x.object_id)),
        OutcomeAccess.EVALUATION_SEALED if role == 'FULL_HISTORY' else OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
    # These member hashes come from the independently generated values,
    # including when preserving a supplied original compressed archive.
    if supplied:
        decode_matrix_arrays(raw, operand)
    return raw, operand


def prefix_from_segment(source, values, *, artifact_id, return_values=False):
    """Append the retained terminal without advancing beyond the cutoff."""
    c, tick = source.coordinate, source.policy.cutoff_tick
    if type(values) is not ParameterSegmentValues or (values.start, values.stop) != (0, tick):
        raise ValueError('scheduled prefix needs its exact initial completed cutoff segment')
    validate_segment_entry(c, source.root.streams, 0, tick)
    arrays = {name: value.copy() for name, value in values.arrays.items()}
    for view, multiplier in (('primary', 1), ('fine', 2)):
        for component in ('positions', 'momenta'):
            name = view+'_'+component
            arrays[name] = np.concatenate((arrays[name], values.terminal_arrays[name][None]), axis=0)
        arrays[view+'_alpha_tilde'] = np.concatenate((arrays[view+'_alpha_tilde'],
            np.asarray([c.couplings(multiplier*tick, refinement=multiplier)], dtype='<f8')), axis=0)
        arrays[view+'_ticks'] = np.append(arrays[view+'_ticks'], np.asarray(multiplier*tick, dtype='<i8'))
    validate_prefix_arrays(source, arrays)
    raw, operand = _array_product(source, arrays, role='PREFIX', artifact_id=artifact_id,
        producers=(identity(source), coordinate_identity(c)))
    checkpoint = ScheduledCheckpoint('checkpoint.'+source.root_id, identity(source), coordinate_identity(c), tick,
        operand.array_artifact, values.generators)
    checkpoint.validate_source(source, operand)
    return (raw, operand, checkpoint, arrays) if return_values else (raw, operand, checkpoint)


def validate_prefix_operand(source, operand):
    if (operand.role != 'PREFIX' or operand.source != identity(source)
            or operand.producers != tuple(sorted((identity(source), coordinate_identity(source.coordinate)), key=lambda x: x.object_id))
            or {m.name: (m.dtype, m.shape) for m in operand.members} != expected_members(_prefix_coordinate(source))
            or any(not m.finite_required for m in operand.members)):
        raise ValueError('scheduled prefix consumer receives wrong original source/member scope')


def consume_prefix(source, operand, raw):
    validate_prefix_operand(source, operand)
    arrays = decode_matrix_arrays(raw, operand)
    validate_prefix_arrays(source, arrays)
    return arrays


def full_from_continuation(source, prefix, prefix_raw, segment, *, artifact_id, raw=None,
        prefix_values=None, return_values=False):
    """Retain each cutoff row once, and every later state/noise on original clocks."""
    if prefix_values is None:
        before = consume_prefix(source, prefix.arrays, prefix_raw)
    else:
        # Reuse only the exact original preflight values. Fingerprint them
        # against the retained member contract and authenticate the unchanged
        # original archive without expanding that archive a second time.
        validate_prefix_operand(source, prefix.arrays)
        artifact = prefix.arrays.array_artifact
        if (type(prefix_raw) is not bytes or len(prefix_raw) != artifact.size_bytes
                or sha256(prefix_raw).hexdigest() != artifact.sha256
                or matrix_array_members(prefix_values) != prefix.arrays.members):
            raise ValueError('scheduled continuation changes its exact preflight prefix values or original archive')
        validate_prefix_arrays(source, prefix_values)
        before = prefix_values
    start, stop = source.policy.cutoff_tick, source.coordinate.total_ticks
    if type(segment) is not ParameterSegmentValues or (segment.start, segment.stop) != (start, stop):
        raise ValueError('scheduled full continuation changes exact original prefix boundary or duration')
    values = {}
    for name, original in before.items():
        later = segment.arrays[name]
        if name.endswith(('positions', 'momenta', 'alpha_tilde', 'ticks')):
            if not np.array_equal(original[-1], later[0]):
                raise ValueError('scheduled continuation changes published original cutoff state/coupling/clock')
            original = original[:-1]
        values[name] = np.concatenate((original, later), axis=0)
    result = full_array_product(source, prefix, values, artifact_id=artifact_id, raw=raw)
    return (*result, values) if return_values else result


def full_array_product(source, prefix, values, *, artifact_id, raw=None):
    supplied = raw is not None
    validate_full_arrays(source, values)
    if raw is None:
        raw, members = encode_matrix_arrays(values)
    else:
        members = matrix_array_members(values)
    operand = _full_array_operand(source, prefix, raw, members, artifact_id=artifact_id)
    if supplied:
        decode_matrix_arrays(raw, operand)
    return raw, operand


def _full_array_operand(source, prefix, raw, members, *, artifact_id):
    """Alias already encoded or decoded native bytes; callers own that proof."""
    from .continuation import ScheduledFullArrays, full_access, full_visibility
    artifact = ArtifactIdentity(artifact_id, 'scheduled-original-full-history', MATRIX_ARRAY_SCHEMA,
        sha256(raw).hexdigest(), 'application/x-npz', len(raw))
    operand = ScheduledFullArrays('arrays.'+artifact_id, identity(source), artifact, members,
        tuple(sorted((identity(source), coordinate_identity(source.coordinate), identity(prefix)), key=lambda x: x.object_id)),
        full_access(source), full_visibility(source))
    return operand


def validate_full_arrays(source, arrays):
    c = source.coordinate
    if set(arrays) != set(expected_members(c)):
        raise ValueError('scheduled full history omits complete requested state/noise/paired clocks')
    for name, (dtype, shape) in expected_members(c).items():
        if arrays[name].dtype.str != dtype or arrays[name].shape != shape or not np.isfinite(arrays[name]).all():
            raise ValueError('scheduled full history substitutes original finite member geometry')
    initial = initial_parameter_state(c)
    for view, multiplier in (('primary', 1), ('fine', 2)):
        n = multiplier*c.total_ticks+1
        if (not np.array_equal(arrays[view+'_ticks'], np.arange(n, dtype='<i8'))
                or not np.array_equal(arrays[view+'_alpha_tilde'], np.asarray([c.couplings(i, refinement=multiplier) for i in range(n)], dtype='<f8'))
                or not np.array_equal(arrays[view+'_positions'][0], initial.positions)
                or not np.array_equal(arrays[view+'_momenta'][0], initial.momenta)):
            raise ValueError('scheduled full history changes preparation, absolute clock or realized schedule')


def assess_full(source, history, arrays):
    from .continuation import ScheduledFullAssessment
    validate_full_arrays(source, arrays)
    design = source.numerical_design
    controls = tuple(MatrixParameterHistoryControl(**row) for row in independent.assess_arrays(source.coordinate, arrays,
        trajectory_tolerance=design.trajectory_tolerance, bridge_tolerance=design.bridge_tolerance))
    return ScheduledFullAssessment('full-numerical.'+source.root_id, identity(source), identity(history), identity(design),
        controls, all(c.disposition == 'SATISFIED' for c in controls))


def assess_prefix(source, history, arrays, *, native_context=None):
    if type(history) is not ScheduledPrefixHistory:
        raise TypeError('scheduled prefix assessment requires its exact generic history owner')
    history.validate_source(source, native_context=native_context)
    validate_prefix_arrays(source, arrays)
    design = source.numerical_design
    controls = assess_prefix_values(source, arrays)
    return ScheduledNumericalAssessment('numerical.'+source.root_id, identity(source), identity(history), identity(design),
        controls, all(c.disposition == 'SATISFIED' for c in controls))


def assess_prefix_values(source, arrays):
    """Original full-coordinate controls over caller-validated prefix values."""
    design = source.numerical_design
    rows = independent.assess_arrays(_prefix_coordinate(source), arrays,
        trajectory_tolerance=design.trajectory_tolerance, bridge_tolerance=design.bridge_tolerance)
    controls = tuple(MatrixParameterHistoryControl(**row) for row in rows)
    return controls


def validate_numerical(source, history, numerical, *, native_context=None):
    if type(history) is not ScheduledPrefixHistory:
        raise TypeError('scheduled numerical proof requires its exact generic history owner')
    history.validate_source(source, native_context=native_context)
    n, design = source.policy.cutoff_tick, source.numerical_design
    if (numerical.source != identity(source) or numerical.history != identity(history)
            or numerical.numerical_design != identity(design)
            or tuple((c.denominator_steps, c.denominator_real_coordinates, c.tolerance) for c in numerical.controls) !=
               ((n, 192, design.trajectory_tolerance), (2*n, 192, design.trajectory_tolerance),
                (n, 192, design.bridge_tolerance), (n, 96, design.trajectory_tolerance))):
        raise ValueError('scheduled prefix numerical witness thins original complete transition denominators')


def measure_prefix(source, history, numerical, native, *, artifact_id, native_context=None):
    """Measurements end at the fixed cutoff; later histories never enter."""
    validate_numerical(source, history, numerical, native_context=native_context)
    validate_prefix_arrays(source, native)
    arrays, traces = measure_prefix_values(source, native)
    raw, operand = _array_product(source, arrays, role='PREFIX_DIAGNOSTICS', artifact_id=artifact_id,
        producers=(identity(source), identity(history), identity(numerical)),
        nonfinite=tuple(n for n in arrays if not n.endswith(('_ticks', '_available', '_identifiable'))))
    return raw, ScheduledPrefixWitness('witness.'+source.root_id, identity(source), identity(history), identity(numerical),
        identity(source.policy), tuple(traces), operand)


def measure_prefix_values(source, native_arrays):
    """Original complete lattice diagnostics and traces; no source envelope."""
    rule = source.policy.factor_rule
    arrays = {name: np.asarray(rule.lattice, dtype=dtype) if name.endswith('_ticks') else
        np.zeros(shape, dtype=dtype) if dtype == '|b1' else np.full(shape, np.nan, dtype=dtype)
        for name, (dtype, shape) in diagnostic_members(rule).items()}
    traces = []
    for view, multiplier in (('PRIMARY', 1), ('FINE', 2)):
        for sector in rule.sectors:
            base, index = prefix(view, sector), ('X', 'Y').index(sector)
            measurements, unavailable, scalar = {}, {}, {}
            for i, tick in enumerate(rule.lattice):
                fields = native_arrays[view.lower()+'_positions'][multiplier*tick, index]
                alpha = native_arrays[view.lower()+'_alpha_tilde'][multiplier*tick, index]
                try:
                    scalar[tick] = independent_scalar_closure_ratio(fields, alpha)
                except ValueError:
                    scalar[tick] = None
                try:
                    measured = factor_science.measure_sector(fields, rule)
                    operator = algebra.operator(fields)
                    spectrum, vectors = np.linalg.eigh(operator)
                    if not np.array_equal(spectrum, measured.spectrum):
                        raise ValueError('scheduled prefix measurement substitutes complete spectral witness')
                except np.linalg.LinAlgError:
                    measurements[tick], unavailable[tick] = None, 'NUMERICAL_INVALID'
                    continue
                measurements[tick] = measured
                arrays[base+'available'][i], arrays[base+'identifiable'][i] = True, measured.identifiable
                for name in ('spectrum', 'projector', 'basis'):
                    arrays[base+name][i] = getattr(measured, name)
                arrays[base+'operator'][i], arrays[base+'eigenvectors'][i] = operator, vectors
                if measured.identifiable:
                    arrays[base+'factor'][i] = measured.factor
            observations, frames = factor_science.causal_observations(rule, measurements, unavailable=unavailable, scalar_closure=scalar)
            for i, tick in enumerate(rule.lattice):
                if tick in frames:
                    arrays[base+'aligned_factor'][i] = frames[tick]
            traces.append(ScheduledPrefixTrace(identity(rule), view, sector, observations,
                factor_science.lifetime(observations, rule), factor_science.lifetime(observations, rule, origin_fixed=True)))
    return arrays, tuple(traces)


def check_frames(source, history, numerical, witness, native_raw, diagnostic_raw, *, native_context=None):
    """Independent raw-state/operator/all15-eigenpair proof; no eigensolve."""
    validate_numerical(source, history, numerical, native_context=native_context)
    rule, design = source.policy.factor_rule, source.policy.factor_numerical_design
    if (witness.source != identity(source) or witness.history != identity(history) or witness.numerical != identity(numerical)
            or witness.policy != identity(source.policy)
            or tuple((t.view, t.sector) for t in witness.traces) != tuple((v, s) for v in ('PRIMARY', 'FINE') for s in rule.sectors)
            or witness.arrays.producers != tuple(sorted((identity(source), identity(history), identity(numerical)), key=lambda x: x.object_id))
            or {m.name: (m.dtype, m.shape) for m in witness.arrays.members} != diagnostic_members(rule)):
        raise ValueError('scheduled frame witness changes original prefix/source/rule/full lattice')
    native = consume_prefix(source, history.arrays, native_raw)
    arrays = decode_matrix_arrays(diagnostic_raw, witness.arrays)
    controls = check_prefix_frame_values(source, witness.traces, native, arrays)
    return ScheduledFrameAssessment('frames.'+source.root_id, identity(source), identity(witness), identity(design), controls,
        all(c.disposition in ('SATISFIED', 'NOT_APPLICABLE') for c in controls))


def check_prefix_frame_values(source, traces, native_arrays, diagnostic_arrays):
    """Original independent raw operator/all15 eigenpair and trace checks."""
    rule, design = source.policy.factor_rule, source.policy.factor_numerical_design
    errors, applicable = {m: [] for m in FACTOR_METHODS}, []
    for trace in traces:
        factor_science.validate_trace(trace, rule)
        base = prefix(trace.view, trace.sector)
        diag = {name: diagnostic_arrays[base+name] for name in DIAGNOSTICS}
        validate_diagnostics(diag, trace, rule)
        multiplier, sector_index = 1 if trace.view == 'PRIMARY' else 2, ('X', 'Y').index(trace.sector)
        for i, observation in enumerate(trace.observations):
            fields = native_arrays[trace.view.lower()+'_positions'][multiplier*observation.tick, sector_index]
            alpha = native_arrays[trace.view.lower()+'_alpha_tilde'][multiplier*observation.tick, sector_index]
            try:
                scalar = independent_scalar_closure_ratio(fields, alpha)
            except ValueError:
                scalar = None
            if (scalar is None) != (observation.scalar_closure_ratio is None):
                raise ValueError('scheduled prefix scalar witness changes missingness')
            errors['scalar-contrast'].append(None if scalar is None else abs(float(scalar-observation.scalar_closure_ratio)))
            available, identified = bool(diag['available'][i]), bool(diag['identifiable'][i])
            applicable.append(not available or identified)
            errors['pauli-factor'].append(pauli_residual(diag['factor'][i]) if identified else None)
            op, vectors, spectrum = diagnostic_arrays[base+'operator'][i], diagnostic_arrays[base+'eigenvectors'][i], diag['spectrum'][i]
            if not available:
                if not np.isnan(op).all() or not np.isnan(vectors).all():
                    raise ValueError('unavailable scheduled prefix manufactures spectral witnesses')
                for name in ('raw-operator', 'eigenvector-orthogonality', 'slow-projector'):
                    errors[name].append(None)
                errors['all-eigenpairs'].extend([None]*15)
                continue
            if not np.isfinite(op).all() or not np.isfinite(vectors).all() or np.any(np.diff(spectrum) < 0):
                raise ValueError('scheduled prefix witness loses ordered finite eigenpairs')
            formed = raw_operator(fields)
            errors['raw-operator'].append(np.linalg.norm(op-formed))
            errors['all-eigenpairs'].extend(np.linalg.norm(formed@vectors-vectors*spectrum[None, :], axis=0))
            errors['eigenvector-orthogonality'].append(np.linalg.norm(vectors.T@vectors-np.eye(15)))
            errors['slow-projector'].append(np.linalg.norm(diag['projector'][i]-vectors[:, :3]@vectors[:, :3].T))
    tolerances = (design.operator_tolerance, design.eigenpair_tolerance, design.orthogonality_tolerance,
        design.projector_tolerance, design.factor_tolerance, design.scalar_tolerance)
    controls = tuple(_control(name, errors[name], tolerance, dimension, applicable if name == 'pauli-factor' else None)
        for name, tolerance, dimension in zip(FACTOR_METHODS, tolerances, (225, 15, 225, 225, 48, 1), strict=True))
    n = 2*len(rule.sectors)*len(rule.lattice)
    if tuple(len(c.measured_errors) for c in controls) != (n, 15*n, n, n, n, n):
        raise ValueError('scheduled prefix thins numerical view/sector/tick/eigenpair denominator')
    return controls


def causal_delivery(source, history, numerical, witness, assessment, native_raw, diagnostic_raw, *, artifact_id, raw=None, native_context=None):
    """Only phase, coupling, clock and selected cutoff frame reach consumers."""
    observed = check_frames(source, history, numerical, witness, native_raw, diagnostic_raw, native_context=native_context)
    if observed != assessment:
        raise ValueError('scheduled causal delivery substitutes retained independent frame assessment')
    native = consume_prefix(source, history.arrays, native_raw)
    diag = decode_matrix_arrays(diagnostic_raw, witness.arrays)
    values, frame_sha, disposition, reason = causal_cutoff_values(source, witness.traces,
        numerical.numerical_pass, assessment.numerical_pass, native, diag)
    raw, operand = _array_product(source, values, role='CAUSAL_STATE', artifact_id=artifact_id,
        producers=(identity(source), identity(history), identity(witness), identity(assessment)), nonfinite=() if disposition == 'AVAILABLE' else ('frame',), raw=raw)
    return raw, ScheduledCausalPrefix('causal.'+source.root_id, identity(source), identity(history), identity(numerical),
        identity(witness), identity(assessment), identity(source.policy), source.root.root, source.policy.cutoff_tick,
        frame_sha, disposition, reason, operand)


def causal_cutoff_values(source, traces, numerical_pass, frame_pass, native_arrays, diagnostic_arrays):
    """Original cutoff decision and copies, never source or issue authority."""
    trace = next(t for t in traces if t.view == 'PRIMARY' and t.sector == source.policy.origin_sector)
    observation = trace.observations[-1]
    if not numerical_pass or not frame_pass:
        disposition, reason = 'UNEVALUABLE', 'PREFIX_NUMERICAL_CONTROLS_NOT_SATISFIED'
    elif observation.raw_admitted is None:
        disposition, reason = 'UNEVALUABLE', 'CAUSAL_CUTOFF_OBSERVATION_UNAVAILABLE'
    elif observation.causal_admitted is not True or observation.alignment_ambiguous:
        disposition, reason = 'NO_ORIGIN', 'DECLARED_CUTOFF_NOT_CAUSALLY_ADMITTED'
    else:
        disposition, reason = 'AVAILABLE', None
    frame = diagnostic_arrays[prefix('PRIMARY', source.policy.origin_sector)+'aligned_factor'][-1].copy() if disposition == 'AVAILABLE' else np.full((3, 4, 4), np.nan, dtype='<c16')
    values = {n: a.copy() for n, a in native_arrays.items() if not n.endswith('innovations')}
    values['frame'] = frame
    return values, sha256(frame.tobytes()).hexdigest() if disposition == 'AVAILABLE' else None, disposition, reason


def continuation_entry(source, history, prefix_raw, *, native_context=None):
    """Exact retained checkpoint operands; calling this does not acquire."""
    if type(history) is not ScheduledPrefixHistory:
        raise TypeError('scheduled continuation requires its exact generic prefix history')
    history.validate_source(source, native_context=native_context)
    arrays = consume_prefix(source, history.arrays, prefix_raw)
    terminal = {view+'_'+part: arrays[view+'_'+part][-1].copy() for view in ('primary', 'fine') for part in ('positions', 'momenta')}
    validate_segment_entry(source.coordinate, source.root.streams, source.policy.cutoff_tick, source.coordinate.total_ticks,
        terminal=terminal, generator_states=history.checkpoint.generators)
    return terminal, history.checkpoint.generators


def join_continuation(source, history, prefix_raw, completed, *, native_context=None):
    """Assemble exact full rows without duplicating the published boundary.

The issued worker must separately authenticate the original prefix/checkpoint
ordinary/native receipts and required pre-future seal before native contact.
This mathematical helper neither enters nor recovers a native operation.
"""
    continuation_entry(source, history, prefix_raw, native_context=native_context)
    if type(completed) is not ParameterSegmentValues or (completed.start, completed.stop) != (source.policy.cutoff_tick, source.coordinate.total_ticks):
        raise ValueError('scheduled continuation changes original cutoff/full horizon')
    prefix_arrays = consume_prefix(source, history.arrays, prefix_raw)
    arrays = {}
    for name, value in prefix_arrays.items():
        if not name.endswith('innovations'):
            if not np.array_equal(value[-1], completed.arrays[name][0]):
                raise ValueError('scheduled continuation changes published cutoff state/clock/coupling')
            value = value[:-1]
        arrays[name] = np.concatenate((value, completed.arrays[name]), axis=0)
    from empirical_lawhood.adapters.methods.matrix_parameter_history.science import validate_arrays
    validate_arrays(source, arrays)
    return arrays


def complete_dispositions(sources, prefixes, unavailable):
    """Exact assigned cases; custody authenticates unavailable evidence first.

    Requested independent units are the allocation's whole group IDs. A case,
    half view or coordinate never supplies an additional independent unit.
    Missing evidence refuses; an uncertain contact remains unknown without replay.
    """
    from .source_index import ResolvedScheduledSource
    if (not sources or any(type(s) is not ResolvedScheduledSource for s in sources)
            or any(type(p) is not ScheduledCausalPrefix for p in prefixes) or any(type(u) is not ScheduledUnavailable for u in unavailable)
            or tuple(s.root_id for s in sources) != tuple(r.root.root_id for r in sources[0].allocation.roots)
            or any(s.reservation != sources[0].reservation or s.specification != sources[0].specification for s in sources)):
        raise ValueError('scheduled readout omits original complete requested source census')
    supplied = (*prefixes, *unavailable)
    rows = {}
    for value in supplied:
        if value.source in rows:
            raise ValueError('scheduled readout duplicates an assigned case')
        rows[value.source] = value
    if set(rows) != {identity(s) for s in sources}:
        raise ValueError('scheduled readout omits unavailable/no-origin/negative requested cases')
    result = []
    for source in sources:
        value = rows[identity(source)]
        if value in prefixes:
            if value.root != source.root.root or value.policy != identity(source.policy) or value.cutoff_tick != source.policy.cutoff_tick:
                raise ValueError('scheduled readout substitutes source/role/cutoff disposition')
            result.append(ScheduledDisposition(identity(source), source.root.root, value, None))
        else:
            evidence = value.receipt if value.receipt is not None else value.contact
            if (evidence.task_id != NAMESPACE+'.'+source.root_id+'.prefix'
                    or evidence.implementation_commit != source.provenance.observed_git_head):
                raise ValueError('scheduled readout substitutes original failed/uncertain attempt scope')
            result.append(ScheduledDisposition(identity(source), source.root.root, None, value))
    return tuple(result), sources[0].allocation.independent_group_ids
