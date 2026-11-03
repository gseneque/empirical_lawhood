# SPDX-License-Identifier: MPL-2.0
"""Exposed tiny software controls; no scientific bank, issue or qualification.

Candidate protected-role labels below exercise records only. Explicit toy
streams and trajectories are exposed by these tests and cannot be used fresh.
"""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_confirmation.records import E1FactorRule
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import ScalarClosureSpec
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import MatrixParameterFactorNumericalDesign, MatrixParameterScalarDefinition
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole as Role, MatrixProgrammeRoot
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as r, retained, science
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import expected_members as diagnostic_members
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_source, parameter_history_segments as segments
from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, CanonicalTaskReceipt
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.native_subwork import NativeSubworkCompletion, NativeSubworkContact, NativeSubworkDefinition, NativeSubworkOutput
from tests.test_matrix_factor_confirmation_eligibility import artifact, publish
from tests.test_matrix_factor_confirmation_eligibility import provenance as provenance
from tests.test_matrix_factor_confirmation_eligibility import stock as stock
from tests.test_matrix_parameter_history import source as parameter_template


CONSTRUCTION = 'COMMON_DECLARED_INITIAL_STATE_AND_FOUR_PURPOSE_PCG64DXSM_NOISE_COORDINATE_SPECIFIC_OU'


@pytest.fixture
def scheduled(stock, *, producing_provenance=None):
    plane, old = stock
    template = parameter_template()
    provenance = template.provenance if producing_provenance is None else producing_provenance
    coordinates, roots, scopes = [], [], []
    for i, role in enumerate(Role):
        # Two coordinate cases of one group, not two independent groups.
        ids = []
        streams = tuple(MatrixHistorySeed(p, sha256(f'EXPOSED-SOFTWARE-SCHEDULED-{i}-{p}'.encode()).hexdigest()) for p in HISTORY_PURPOSES)
        for j in range(2):
            c = replace(template.coordinate, coordinate_id=f'coordinate.software.scheduled.{i}.{j}',
                family_id=FOUR_FAMILY_PREPARATION_IDS[1], clock_id='clock.software.scheduled', observation_ticks=tuple(range(9)),
                member=replace(template.coordinate.member, member_id=f'member.software.scheduled.{i}.{j}', cross_coupling_gamma=D(1+j)),
                primary_view=replace(template.coordinate.primary_view, view_id=f'primary.software.scheduled.{i}.{j}', bath_temperature=D(1+i)),
                fine_view=replace(template.coordinate.fine_view, view_id=f'fine.software.scheduled.{i}.{j}', bath_temperature=D(1+i)))
            coordinates.append(c); ids.append(coordinate_identity(c))
            root = MatrixProgrammeRoot(f'root.software.scheduled.{i}.{j}', f'group.software.scheduled.{i}',
                f'regime.software.scheduled.{i}.{j}', c.coordinate_id, role, c.clock_id)
            roots.append(r.ScheduledRoot(root, coordinate_identity(c), streams))
        scopes.append(r.ScheduledMatchedScope(f'scope.software.scheduled.{i}', role, (f'group.software.scheduled.{i}',), tuple(ids), CONSTRUCTION))
    exposure = r.ScheduledExposure('exposure.software.scheduled', old.allocation.exposure, (), artifact('audit.software.scheduled'))
    allocation = r.ScheduledAllocation('allocation.software.scheduled', tuple(coordinates), tuple(roots), tuple(scopes), exposure)
    reservation = r.ScheduledReservation('reservation.software.scheduled', allocation, publish(plane, allocation, 'scheduled.allocation'))
    definition = MatrixParameterScalarDefinition('scalar.software.scheduled')
    scalar = ArtifactIdentity(definition.definition_id, 'software-only-normalization', definition.SCHEMA, definition.fingerprint(), 'application/json', len(definition.canonical_bytes()))
    rule = E1FactorRule('rule.software.scheduled.prefix', ('X', 'Y'), tuple(range(7)), D('.001'), 4, 0,
        D('.05'), D('.05'), D(15), D(15), D(30), D('1e-10'), D('1e-20'), D('.5'), ScalarClosureSpec('scalar-rule.software.scheduled', scalar, D('.30')))
    policy = r.ScheduledPrefixPolicy('policy.software.scheduled', 6, rule,
        MatrixParameterFactorNumericalDesign('design.software.scheduled.factor', *(D('1e-9') for _ in range(6))),
        'X', 'FIXED_DECLARED_CUTOFF_CAUSALLY_ADMITTED_PRIMARY_FRAME')
    selection = r.ScheduledSelection('selection.software.scheduled', r.identity(reservation), template.numerical_design,
        (policy,), tuple((coordinate_identity(c), r.identity(policy)) for c in coordinates))
    specification = r.ScheduledSpecification('specification.software.scheduled', selection, publish(plane, selection, 'scheduled.selection'))
    index = ScheduledSourceIndex.from_shared(reservation=reservation, specification=specification, provenances=(provenance,))
    sources = tuple(index.resolve(index.reference(source_id='source.'+row.root.root_id, root_id=row.root.root_id, provenance=provenance.identity)) for row in roots)
    return plane, sources



def with_parents(source, *, reservation=None, specification=None):
    """Author a current reference against explicitly changed scientific parents."""
    index = ScheduledSourceIndex.from_shared(reservation=reservation or source.reservation,
        specification=specification or source.specification, provenances=source.index.provenances)
    return index.resolve(index.reference(source_id=source.source_id, root_id=source.root_id,
        provenance=source.reference.provenance))


def pure_assess_prefix(source, history, values):
    """Independent value reduction; no generic native proof or future bank."""
    science.validate_prefix_arrays(source, values)
    controls = science.assess_prefix_values(source, values)
    return r.ScheduledNumericalAssessment('numerical.'+source.root_id, r.identity(source), r.identity(history),
        r.identity(source.numerical_design), controls, all(c.disposition == 'SATISFIED' for c in controls))


def pure_measure_prefix(source, history, numerical, values, *, artifact_id):
    if pure_assess_prefix(source, history, values) != numerical:
        raise ValueError('pure prefix control changes the independent numerical assessment')
    diagnostics, traces = science.measure_prefix_values(source, values)
    raw, operand = science._array_product(source, diagnostics, role='PREFIX_DIAGNOSTICS', artifact_id=artifact_id,
        producers=(r.identity(source), r.identity(history), r.identity(numerical)),
        nonfinite=tuple(n for n in diagnostics if not n.endswith(('_ticks', '_available', '_identifiable'))))
    witness = r.ScheduledPrefixWitness('witness.'+source.root_id, r.identity(source), r.identity(history), r.identity(numerical),
        r.identity(source.policy), traces, operand)
    return raw, witness


def pure_check_frames(source, history, numerical, witness, native_raw, diagnostic_raw):
    native = science.consume_prefix(source, history.arrays, native_raw)
    if (pure_assess_prefix(source, history, native) != numerical or witness.source != r.identity(source)
            or witness.history != r.identity(history) or witness.numerical != r.identity(numerical)
            or witness.policy != r.identity(source.policy)
            or tuple((t.view, t.sector) for t in witness.traces) != tuple((v, sector) for v in ('PRIMARY', 'FINE') for sector in source.policy.factor_rule.sectors)
            or witness.arrays.producers != tuple(sorted((r.identity(source), r.identity(history), r.identity(numerical)), key=lambda x: x.object_id))
            or {m.name: (m.dtype, m.shape) for m in witness.arrays.members} != diagnostic_members(source.policy.factor_rule)):
        raise ValueError('pure prefix frame control changes complete mathematical inputs')
    diagnostics = decode_matrix_arrays(diagnostic_raw, witness.arrays)
    controls = science.check_prefix_frame_values(source, witness.traces, native, diagnostics)
    return r.ScheduledFrameAssessment('frames.'+source.root_id, r.identity(source), r.identity(witness),
        r.identity(source.policy.factor_numerical_design), controls, all(c.disposition in ('SATISFIED', 'NOT_APPLICABLE') for c in controls))


def pure_causal_delivery(source, history, numerical, witness, assessment, native_raw, diagnostic_raw, *, artifact_id, raw=None):
    if pure_check_frames(source, history, numerical, witness, native_raw, diagnostic_raw) != assessment:
        raise ValueError('pure prefix delivery changes the independent frame assessment')
    native = science.consume_prefix(source, history.arrays, native_raw)
    diagnostics = decode_matrix_arrays(diagnostic_raw, witness.arrays)
    values, frame_sha, disposition, reason = science.causal_cutoff_values(source, witness.traces,
        numerical.numerical_pass, assessment.numerical_pass, native, diagnostics)
    raw, operand = science._array_product(source, values, role='CAUSAL_STATE', artifact_id=artifact_id,
        producers=(r.identity(source), r.identity(history), r.identity(witness), r.identity(assessment)),
        nonfinite=() if disposition == 'AVAILABLE' else ('frame',), raw=raw)
    return raw, r.ScheduledCausalPrefix('causal.'+source.root_id, r.identity(source), r.identity(history), r.identity(numerical),
        r.identity(witness), r.identity(assessment), r.identity(source.policy), source.root.root, source.policy.cutoff_tick,
        frame_sha, disposition, reason, operand)


def pure_continuation_entry(source, history, raw):
    history.checkpoint.validate_source(source, history.arrays)
    arrays = science.consume_prefix(source, history.arrays, raw)
    terminal = {v+'_'+p: arrays[v+'_'+p][-1].copy() for v in ('primary', 'fine') for p in ('positions', 'momenta')}
    segments.validate_segment_entry(source.coordinate, source.root.streams, source.policy.cutoff_tick, source.coordinate.total_ticks,
        terminal=terminal, generator_states=history.checkpoint.generators)
    return terminal, history.checkpoint.generators


def pure_join_continuation(source, history, raw, tail):
    pure_continuation_entry(source, history, raw)
    result, operand = science.full_from_continuation(source, history, raw, tail, artifact_id='pure.full.'+source.root_id)
    return decode_matrix_arrays(result, operand)

def prefix_case(plane, source, *, parent=None):
    from tests.native_completion_fixtures import publish_completion
    values = segments.acquire_parameter_segment(source.coordinate, source.root.streams, 0, source.policy.cutoff_tick)
    task = r.NAMESPACE+'.'+source.root_id+'.prefix'
    parent = parent or NativeEffectContact('run.software.scheduled', task, 'attempt.'+task,
        ObjectIdentity('plan.software.scheduled', 'empirical-lawhood/runtime/execution-plan', '1.0.0', 'a'*64),
        ObjectIdentity(task, 'empirical-lawhood/runtime/execution-task', '1.0.0', 'b'*64), source.provenance.observed_git_head, ('input.software.scheduled',), ())
    # Pure mathematical fixture metadata deliberately has no authored forecast
    # bank or native configuration context. Actual native proof controls live in
    # the separately authored Y/CALIBRATION worker bank.
    definition = NativeSubworkDefinition('prefix.'+source.root_id, 'software.literal-prefix-values.v1', parent,
        source.reference.identity, tuple(sorted((r.identity(source), r.identity(source.allocation), coordinate_identity(source.coordinate), source.provenance.identity), key=lambda x: x.object_id)),
        source.provenance.code_sources_sha256, source.provenance.dependency_lock_sha256, parent.input_materialization_ids,
        tuple(sorted((source.root.stream_identity(s) for s in source.root.streams), key=lambda x: x.object_id)),
        (NativeSubworkOutput('arrays', MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz'),
         NativeSubworkOutput('checkpoint', r.ScheduledCheckpoint.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json')))
    native_task = 'native-subwork.'+sha256((task+':'+definition.subwork_id).encode()).hexdigest()
    raw, arrays, checkpoint = science.prefix_from_segment(source, values, artifact_id=native_task+'.output.arrays')
    from empirical_lawhood.runtime.artifacts import ArtifactWriteRequest
    a = plane.write(ArtifactWriteRequest(arrays.array_artifact.artifact_id, 'software/'+native_task+'.npz', MATRIX_ARRAY_SCHEMA,
        ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz', 'software-only', 'software', raw, Visibility.PROSPECTIVE, (), Access.OUTCOME_BLIND))
    c = publish(plane, checkpoint, native_task+'.output.checkpoint')
    receipt = CanonicalTaskReceipt('receipt.'+native_task, parent.run_id, native_task, parent.run_id+'.'+native_task+'.attempt-001',
        parent.implementation_commit, parent.input_materialization_ids, (a.materialization, c.materialization), (a.logical, c.logical), (), OperationalStatus.SUCCEEDED, ())
    contact = NativeSubworkContact(ObjectIdentity('begin.software.scheduled', 'empirical-lawhood/runtime/native-subwork-begin', '1.0.0', 'c'*64))
    completion = NativeSubworkCompletion(definition.identity, ObjectIdentity.from_record('contact.software.scheduled', contact),
        OperationalStatus.SUCCEEDED, ('arrays', 'checkpoint'), (), definition.streams, (), (), InquiryCost(None, None, None),
        'exposed tiny software control; no real native study/qualification', None, ())
    receipt = publish_completion(plane, receipt, completion, visibility=Visibility.PROSPECTIVE, access=Access.OUTCOME_BLIND)
    history = r.ScheduledPrefixHistory('history.'+source.root_id, r.identity(source), arrays, checkpoint, r.ScheduledNativeEvidence(definition, completion, receipt))
    numerical = pure_assess_prefix(source, history, science.consume_prefix(source, arrays, raw))
    diagnostic, witness = pure_measure_prefix(source, history, numerical, science.consume_prefix(source, arrays, raw), artifact_id='diagnostics.'+source.root_id)
    assessment = pure_check_frames(source, history, numerical, witness, raw, diagnostic)
    causal_raw, causal = pure_causal_delivery(source, history, numerical, witness, assessment, raw, diagnostic, artifact_id='causal-arrays.'+source.root_id)
    return history, numerical, witness, assessment, causal, raw, diagnostic, causal_raw


def test_complete_role_general_matched_source_roundtrip(scheduled):
    plane, sources = scheduled
    assert len(sources) == 8 and len(sources[0].allocation.independent_group_ids) == 4
    for source in sources:
        assert decode_canonical_bytes(source.reference.canonical_bytes(), r.ScheduledSource, maximum_bytes=None) == source.reference
        retained.authenticate_source_publications(plane, source)
        assert source.evidence_role == ('EXPOSED_DEVELOPMENT_NONPROMOTABLE' if source.root.root.role is Role.DEVELOPMENT else r.CANDIDATE)
    for scope in sources[0].allocation.matched_scopes:
        rows = tuple(s for s in sources if s.root.root.independent_group_id in scope.independent_group_ids)
        assert rows[0].root.streams == rows[1].root.streams
        assert len({r.matched_key(s.coordinate) for s in rows}) == 1
        assert len({r.physical_key(s.coordinate) for s in rows}) == 2


@pytest.mark.parametrize('defect', ('role', 'coordinate-missing', 'stream-purpose', 'stream-group', 'start', 'clock', 'prior-seed', 'prior-group', 'withheld-physical', 'alias'))
def test_source_refuses_false_matching_or_exposure_before_effects(scheduled, defect, monkeypatch):
    _, sources = scheduled
    allocation = sources[0].allocation
    def blocked(*args, **kwargs):
        raise AssertionError('source validation entered native/RNG')
    monkeypatch.setattr(np.random, 'Generator', blocked)
    monkeypatch.setattr(segments, 'acquire_parameter_segment', blocked)
    with pytest.raises(ValueError):
        if defect == 'coordinate-missing':
            replace(allocation, roots=allocation.roots[:-1])
        elif defect in ('role', 'stream-purpose', 'stream-group'):
            row = allocation.roots[1]
            if defect == 'role':
                row = replace(row, root=replace(row.root, role=Role.CONFIRMATION))
            else:
                row = replace(row, streams=allocation.roots[2].streams if defect == 'stream-group' else tuple(replace(s, digest_sha256=sha256(('changed'+s.purpose).encode()).hexdigest()) for s in row.streams))
            replace(allocation, roots=(allocation.roots[0], row, *allocation.roots[2:]))
        elif defect in ('start', 'clock', 'alias'):
            c = allocation.coordinates[1]
            c = replace(c, decreasing_start=D(9)) if defect == 'start' else replace(c,
                primary_view=replace(c.primary_view, timestep=D('.002')), fine_view=replace(c.fine_view, timestep=D('.001'))) if defect == 'clock' else replace(c, member=replace(c.member, member_id=allocation.coordinates[0].member.member_id))
            row = replace(allocation.roots[1], coordinate=coordinate_identity(c))
            scopes = (replace(allocation.matched_scopes[0], coordinates=(allocation.matched_scopes[0].coordinates[0], coordinate_identity(c))), *allocation.matched_scopes[1:])
            replace(allocation, coordinates=(allocation.coordinates[0], c, *allocation.coordinates[2:]), roots=(allocation.roots[0], row, *allocation.roots[2:]), matched_scopes=scopes)
        elif defect == 'withheld-physical':
            replace(allocation, exposure=replace(allocation.exposure, prior_scheduled_coordinates=(allocation.coordinates[-1],)))
        else:
            census = allocation.exposure.census
            census = replace(census, effective_seed_exclusions=tuple(sorted((*census.effective_seed_exclusions, allocation.roots[0].streams[0].effective_seed)))) if defect == 'prior-seed' else replace(census, exposed_independent_groups=tuple(sorted((*census.exposed_independent_groups, allocation.roots[0].root.independent_group_id))))
            replace(allocation, exposure=replace(allocation.exposure, census=census))


@pytest.mark.parametrize('role', tuple(Role))
def test_actual_cutoff_full_independent_controls_and_no_rng_delivery(scheduled, role):
    plane, sources = scheduled
    source = next(s for s in sources if s.root.root.role is role)
    history, numerical, witness, assessment, causal, raw, diagnostic, causal_raw = prefix_case(plane, source)
    assert numerical.numerical_pass and assessment.numerical_pass
    assert tuple(c.denominator_steps for c in numerical.controls) == (6, 12, 6, 6)
    assert tuple(len(c.measured_errors) for c in assessment.controls) == (28, 420, 28, 28, 28, 28)
    assert causal.root.role is role and causal.cutoff_tick == 6
    from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
    delivered = decode_matrix_arrays(causal_raw, causal.arrays)
    assert set(delivered) == {'primary_positions', 'primary_momenta', 'primary_ticks', 'primary_alpha_tilde',
        'fine_positions', 'fine_momenta', 'fine_ticks', 'fine_alpha_tilde', 'frame'}
    assert delivered['primary_ticks'][-1] == 6 and delivered['fine_ticks'][-1] == 12
    assert np.array_equal(delivered['primary_alpha_tilde'][-1], source.coordinate.couplings(6))
    assert r.identity(witness) == causal.witness


def test_original_checkpoint_continuation_exact_whole_reference(scheduled):
    plane, sources = scheduled
    source = sources[2]
    history, _, _, _, _, raw, _, _ = prefix_case(plane, source)
    terminal, states = pure_continuation_entry(source, history, raw)
    tail = segments.acquire_parameter_segment(source.coordinate, source.root.streams, 6, 8, terminal=terminal, generator_states=states)
    observed = pure_join_continuation(source, history, raw, tail)
    expected = parameter_source.acquire_parameter_history(source.coordinate, source.root.streams)
    assert all(np.array_equal(observed[n], expected[n]) for n in expected)
    assert observed['primary_ticks'].tolist() == list(range(9))
    assert observed['fine_ticks'].tolist() == list(range(17))


def test_cold_numerical_and_frame_controls_block_producers_rng_eigen(scheduled, monkeypatch):
    plane, sources = scheduled
    source = sources[2]
    history, numerical, witness, assessment, causal, raw, diagnostic, causal_raw = prefix_case(plane, source)
    def blocked(*args, **kwargs):
        raise AssertionError('cold check entered producer/RNG/eigen')
    monkeypatch.setattr(segments, 'acquire_parameter_segment', blocked)
    monkeypatch.setattr(parameter_source, 'acquire_parameter_history', blocked)
    monkeypatch.setattr(factor_science_module(), 'measure_sector', blocked)
    monkeypatch.setattr(np.random, 'Generator', blocked)
    monkeypatch.setattr(np.random, 'PCG64DXSM', blocked)
    monkeypatch.setattr(np.linalg, 'eigh', blocked)
    monkeypatch.setattr(np.linalg, 'eigvalsh', blocked)
    assert pure_assess_prefix(source, history, science.consume_prefix(source, history.arrays, raw)) == numerical
    assert pure_check_frames(source, history, numerical, witness, raw, diagnostic) == assessment
    assert pure_causal_delivery(source, history, numerical, witness, assessment, raw, diagnostic,
        artifact_id=causal.arrays.array_artifact.artifact_id, raw=causal_raw) == (causal_raw, causal)


def factor_science_module():
    from empirical_lawhood.adapters.methods.matrix_factor_lifetime import science as factor
    return factor


def test_mutually_forged_operator_and_spectrum_cannot_create_available_origin(scheduled):
    plane, sources = scheduled
    source = sources[2]
    history, numerical, witness, _, _, raw, diagnostic, _ = prefix_case(plane, source)
    from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
    values = {n: a.copy() for n, a in decode_matrix_arrays(diagnostic, witness.arrays).items()}
    values['primary_x_operator'] += np.eye(15)
    values['primary_x_spectrum'] += 1
    changed_raw, changed_arrays = science._array_product(source, values, role='PREFIX_DIAGNOSTICS',
        artifact_id='forged.software.diagnostics', producers=witness.arrays.producers,
        nonfinite=tuple(m.name for m in witness.arrays.members if not m.finite_required))
    changed = replace(witness, arrays=changed_arrays)
    assessed = pure_check_frames(source, history, numerical, changed, raw, changed_raw)
    assert not assessed.numerical_pass
    assert next(c for c in assessed.controls if c.method == 'raw-operator').disposition == 'VIOLATED'
    _, delivered = pure_causal_delivery(source, history, numerical, changed, assessed, raw, changed_raw, artifact_id='forged.software.delivery')
    assert delivered.disposition == 'UNEVALUABLE' and delivered.frame_sha256 is None


def test_unavailable_frame_witness_is_unevaluable_not_no_origin(scheduled, monkeypatch):
    plane, sources = scheduled
    def unavailable(*args, **kwargs):
        raise np.linalg.LinAlgError('exposed software unavailable-spectrum control')
    monkeypatch.setattr(np.linalg, 'eigh', unavailable)
    history, numerical, witness, assessed, causal, _, _, _ = prefix_case(plane, sources[2])
    assert numerical.numerical_pass and not assessed.numerical_pass
    assert causal.disposition == 'UNEVALUABLE' and causal.frame_sha256 is None
    assert all(o.status == 'NUMERICAL_INVALID' for t in witness.traces for o in t.observations)


@pytest.mark.parametrize('defect', ('cutoff', 'coupling', 'checkpoint-cursor', 'checkpoint-seed', 'rule-switch', 'publication-sidecar'))
def test_exact_prefix_and_source_substitution_controls(scheduled, defect):
    plane, sources = scheduled
    source = sources[2]
    if defect == 'rule-switch':
        selection = source.specification.selection
        changed = replace(selection.prefix_policies[0], policy_id='policy.software.changed')
        mappings = tuple((c, r.identity(changed) if c == source.root.coordinate else p) for c, p in selection.coordinate_policies)
        selected = replace(selection, prefix_policies=tuple(sorted((*selection.prefix_policies, changed), key=lambda p: p.policy_id)), coordinate_policies=mappings)
        frozen = r.ScheduledSpecification('specification.software.changed', selected, publish(plane, selected, 'scheduled.changed-selection'))
        with pytest.raises(ValueError, match='matched scheduled'):
            with_parents(source, specification=frozen)
        return
    if defect == 'publication-sidecar':
        publication = source.reservation.publication
        altered = replace(publication, manifest_materialization=replace(publication.manifest_materialization, physical_sha256='f'*64))
        reservation = replace(source.reservation, publication=altered)
        selected = replace(source.specification.selection, reservation=r.identity(reservation))
        specification = r.ScheduledSpecification('specification.software.changed-sidecar', selected,
            publish(plane, selected, 'scheduled.changed-sidecar-selection'))
        changed = with_parents(source, reservation=reservation, specification=specification)
        with pytest.raises(ValueError, match='sidecar'):
            retained.authenticate_source_publications(plane, changed)
        return
    history, _, _, _, _, raw, _, _ = prefix_case(plane, source)
    with pytest.raises(ValueError):
        if defect.startswith('checkpoint'):
            saved = history.checkpoint.generators[0]
            saved = replace(saved, completed_noise_matrices=saved.completed_noise_matrices+1) if defect == 'checkpoint-cursor' else replace(saved, effective_seed=saved.effective_seed+1)
            checkpoint = replace(history.checkpoint, generators=(saved, *history.checkpoint.generators[1:]))
            checkpoint.validate_source(source, history.arrays)
        else:
            arrays = {n: a.copy() for n, a in science.consume_prefix(source, history.arrays, raw).items()}
            if defect == 'cutoff':
                arrays['fine_ticks'][-1] += 1
            else:
                arrays['primary_alpha_tilde'][-1, 0] = 0
            science.validate_prefix_arrays(source, arrays)


def test_known_failed_admission_retains_no_origin_and_exact_native_phase(scheduled):
    plane, sources = scheduled
    source = sources[2]
    original = source.specification.selection
    policy = replace(source.policy, factor_rule=replace(source.policy.factor_rule, associative_leakage_maximum=D(0), lie_leakage_maximum=D(0)))
    selected = replace(original, selection_id='selection.software.no-origin', prefix_policies=(policy,),
        coordinate_policies=tuple((c, r.identity(policy)) for c, _ in original.coordinate_policies))
    frozen = r.ScheduledSpecification('specification.software.no-origin', selected, publish(plane, selected, 'scheduled.no-origin-selection'))
    source = with_parents(source, specification=frozen)
    history, numerical, witness, assessed, causal, raw, _, _ = prefix_case(plane, source)
    assert numerical.numerical_pass and assessed.numerical_pass
    assert causal.disposition == 'NO_ORIGIN' and causal.frame_sha256 is None
    assert len(witness.traces) == 4 and all(len(t.observations) == 7 for t in witness.traces)
    assert science.consume_prefix(source, history.arrays, raw)['primary_ticks'][-1] == 6


def test_complete_requested_census_keeps_known_refusals_unknown_and_case_group_counts(scheduled):
    _, sources = scheduled
    unavailable = []
    for i, source in enumerate(sources):
        task = r.NAMESPACE+'.'+source.root_id+'.prefix'
        if i == 0:
            contact = NativeEffectContact('run.software.unknown', task, 'attempt.software.unknown',
                ObjectIdentity('plan.software.unknown', 'empirical-lawhood/runtime/execution-plan', '1.0.0', 'a'*64),
                ObjectIdentity(task, 'empirical-lawhood/runtime/execution-task', '1.0.0', 'b'*64),
                source.provenance.observed_git_head, ('input.software.unknown',), ())
            unavailable.append(r.ScheduledUnavailable(r.identity(source), None, contact))
        else:
            receipt = CanonicalTaskReceipt('receipt.software.failed.'+str(i), 'run.software.failed', task, 'attempt.software.failed.'+str(i),
                source.provenance.observed_git_head, (), (), (), (), OperationalStatus.BLOCKED, ('software-blocked-source',))
            unavailable.append(r.ScheduledUnavailable(r.identity(source), receipt, None))
    rows, groups = science.complete_dispositions(sources, (), tuple(unavailable))
    assert len(rows) == 8 and len(groups) == 4
    assert rows[0].availability == 'UNKNOWN_CONTACT'
    assert all(r.availability == 'UNAVAILABLE' for r in rows[1:])
    with pytest.raises(ValueError, match='omits'):
        science.complete_dispositions(sources, (), tuple(unavailable[:-1]))


def test_explicit_nine_coordinate_matched_noise_keeps_one_group_and_coordinate_ou(scheduled):
    from itertools import product
    plane, sources = scheduled
    source, coordinates, roots = sources[4], [], []
    settings = (*product((D('.5'), D(2)), repeat=3), (D(1), D(1), D(1)))
    for i, (bath, friction, cross) in enumerate(settings):
        c = replace(source.coordinate, coordinate_id='coordinate.software.nine.'+str(i),
            member=replace(source.coordinate.member, member_id='member.software.nine.'+str(i), cross_coupling_gamma=cross),
            primary_view=replace(source.coordinate.primary_view, view_id='primary.software.nine.'+str(i), bath_temperature=bath, friction_gamma=friction),
            fine_view=replace(source.coordinate.fine_view, view_id='fine.software.nine.'+str(i), bath_temperature=bath, friction_gamma=friction))
        coordinates.append(c)
        root = MatrixProgrammeRoot('root.software.nine.'+str(i), 'group.software.nine', 'regime.software.nine.'+str(i),
            c.coordinate_id, Role.CONFIRMATION, c.clock_id)
        roots.append(r.ScheduledRoot(root, coordinate_identity(c), source.root.streams))
    scope = r.ScheduledMatchedScope('scope.software.nine', Role.CONFIRMATION, ('group.software.nine',),
        tuple(coordinate_identity(c) for c in coordinates), CONSTRUCTION)
    allocation = r.ScheduledAllocation('allocation.software.nine', tuple(coordinates), tuple(roots), (scope,), source.allocation.exposure)
    reservation = r.ScheduledReservation('reservation.software.nine', allocation, publish(plane, allocation, 'scheduled.nine-allocation'))
    selection = replace(source.specification.selection, selection_id='selection.software.nine', reservation=r.identity(reservation),
        coordinate_policies=tuple((coordinate_identity(c), r.identity(source.policy)) for c in coordinates))
    specification = r.ScheduledSpecification('specification.software.nine', selection, publish(plane, selection, 'scheduled.nine-selection'))
    index = ScheduledSourceIndex.from_shared(reservation=reservation, specification=specification, provenances=(source.provenance,))
    selected = tuple(index.resolve(index.reference(source_id='source.'+root.root.root_id, root_id=root.root.root_id, provenance=source.provenance.identity)) for root in roots)
    values = tuple(segments.acquire_parameter_segment(s.coordinate, s.root.streams, 0, 6) for s in selected)
    assert len(selected) == 9 and allocation.independent_group_ids == ('group.software.nine',)
    for value in values:
        assert np.array_equal(value.arrays['primary_positions'][0], values[0].arrays['primary_positions'][0])
        assert np.array_equal(value.arrays['primary_innovations'], values[0].arrays['primary_innovations'])
        assert np.array_equal(value.arrays['bridge_innovations'], values[0].arrays['bridge_innovations'])
    assert not np.array_equal(values[0].arrays['fine_innovations'], values[2].arrays['fine_innovations'])


@pytest.mark.parametrize('defect', ('half-view', 'eigenpair', 'tick'))
def test_cold_witness_rejects_missing_fine_tick_or_eigenpair(scheduled, defect):
    plane, sources = scheduled
    source = sources[2]
    history, numerical, witness, _, _, raw, diagnostic, _ = prefix_case(plane, source)
    from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
    values = {n: a.copy() for n, a in decode_matrix_arrays(diagnostic, witness.arrays).items()}
    if defect == 'half-view':
        values = {n: a for n, a in values.items() if not n.startswith('fine_')}
    elif defect == 'eigenpair':
        values['fine_y_eigenvectors'] = values['fine_y_eigenvectors'][:, :, :-1]
    else:
        values['fine_x_ticks'] = values['fine_x_ticks'][:-1]
    altered_raw, operand = science._array_product(source, values, role='PREFIX_DIAGNOSTICS', artifact_id='missing.software.'+defect,
        producers=witness.arrays.producers, nonfinite=tuple(n for n in values if not n.endswith(('_ticks', '_available', '_identifiable'))))
    with pytest.raises(ValueError):
        pure_check_frames(source, history, numerical, replace(witness, arrays=operand), raw, altered_raw)
