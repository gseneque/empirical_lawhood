# SPDX-License-Identifier: MPL-2.0
"""Hypothetical E1 software contracts; no real issue, qualification or campaign.

Tiny deterministic trajectories use explicitly supplied zero innovations.
Receipts and protected selections below are software custody controls only.
They are never imported as scientific confirmation or eligibility evidence.
"""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_confirmation import records as r, science
from empirical_lawhood.adapters.methods.matrix_factor_confirmation.operation_bindings import (
    NAMESPACE, E1NativeRunner, E1OperationConfig, operation_factories,
)
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import ScalarClosureSpec
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import MatrixParameterFactorNumericalDesign, MatrixParameterScalarDefinition
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterNativeHistory, coordinate_identity, expected_members
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole, MatrixProgrammeRoot
from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import advance_parameter_pair, initial_parameter_state
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.native_subwork import NativeSubworkCompletion, NativeSubworkContact, NativeSubworkDefinition, NativeSubworkOutput
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from tests.test_matrix_factor_confirmation_eligibility import publish
from tests.test_matrix_factor_confirmation_eligibility import provenance as provenance
from tests.test_matrix_factor_confirmation_eligibility import stock as stock
from tests.test_matrix_factor_confirmation_refined import retained
from tests.test_matrix_parameter_history import source as parameter_source
from tests.native_completion_fixtures import publish_completion


@pytest.fixture
def e1(stock):
    plane, exposed = stock
    template = parameter_source()
    coordinates, roots = [], []
    for n, family in enumerate(FOUR_FAMILY_PREPARATION_IDS):
        coordinate = replace(template.coordinate, coordinate_id=f'coordinate.software.e1.{n}',
            clock_id=f'clock.software.e1.{n}', family_id=family, observation_ticks=tuple(range(9)))
        coordinates.append(coordinate)
        root = MatrixProgrammeRoot(f'root.software.e1.{n}', f'group.software.e1.{n}', f'regime.software.e1.{n}',
            coordinate.coordinate_id, MatrixProgrammeRole.CONFIRMATION, coordinate.clock_id)
        streams = tuple(MatrixHistorySeed(p, sha256(f'EXPOSED-SOFTWARE-E1-CONTROL-{n}-{p}'.encode()).hexdigest()) for p in HISTORY_PURPOSES)
        roots.append(r.E1HistoryRoot(root, coordinate_identity(coordinate), streams))
    allocation = r.E1HistoryAllocation('allocation.software.e1', tuple(coordinates), tuple(roots), exposed.allocation.exposure)
    reservation = r.E1AllocationReservation('reservation.software.e1', allocation, publish(plane, allocation, 'e1.allocation'))
    definition = MatrixParameterScalarDefinition('definition.software.e1.scalar')
    scalar_artifact = ArtifactIdentity(definition.definition_id, 'e1-software-normalization', definition.SCHEMA,
        definition.fingerprint(), 'application/json', len(definition.canonical_bytes()))
    rule = r.E1FactorRule('rule.software.e1', ('X', 'Y'), tuple(range(9)), D('.001'), 4, 0,
        D('.05'), D('.05'), D(15), D(15), D(30), D('1e-10'), D('1e-20'), D('.5'),
        ScalarClosureSpec('scalar-rule.software.e1', scalar_artifact, D('.30')))
    criterion = r.E1ConfirmationCriterion('criterion.software.e1', r.identity(allocation), rule.identity,
        'system.software.e1', 'world.software.e1', ObjectIdentity('relation.software.e1', 'empirical-lawhood/testing/e1-relation', '1.0.0', 'a'*64),
        'unit.whole-root', tuple(sorted((r.E1FamilyRequirement(f, 1, 1, D('.0001'), D('.0001')) for f in FOUR_FAMILY_PREPARATION_IDS), key=lambda f: f.family_id)),
        ('PRIMARY', 'FINE'), ('MOVING', 'ORIGIN_FIXED'), 'EVER_CAUSALLY_ADMITTED_IN_RISK_WINDOW', 8, 2, D('.5'),
        'EXACT_ONE_SIDED_BINOMIAL_LOWER_BOUND', 'BONFERRONI_FROZEN_FAMILY_VIEW_SECTOR_ENDPOINT_MENU')
    selection = r.E1ScientificSelection('selection.software.e1', r.identity(reservation), rule, criterion, template.numerical_design,
        MatrixParameterFactorNumericalDesign('design.software.e1.factor', *(D('1e-9') for _ in range(6))))
    frozen = r.E1FrozenSpecification('freeze.software.e1', selection, publish(plane, selection, 'e1.selection'))
    sources = tuple(r.E1HistorySource('source.'+row.root.root_id, reservation, frozen, row.root.root_id, template.provenance) for row in roots)
    return plane, sources, definition


def deterministic_arrays(source):
    c, n = source.coordinate, source.coordinate.total_ticks
    arrays = {name: np.zeros(shape, dtype=dtype) for name, (dtype, shape) in expected_members(c).items()}
    primary = fine = initial_parameter_state(c)
    for view, multiplier in (('primary', 1), ('fine', 2)):
        arrays[view+'_ticks'][:] = np.arange(multiplier*n+1)
        arrays[view+'_alpha_tilde'][:] = [c.couplings(t, refinement=multiplier) for t in range(multiplier*n+1)]
        arrays[view+'_positions'][0], arrays[view+'_momenta'][0] = primary.positions, primary.momenta
    noise = np.zeros((2, 3, 4, 4), dtype='<c16')
    for tick in range(1, n+1):
        primary, first, fine = advance_parameter_pair(primary, fine, coordinate=c, coarse_step=tick,
            coarse_noise=noise, bridge_noise=noise)
        for view, at, state in (('primary', tick, primary), ('fine', 2*tick-1, first), ('fine', 2*tick, fine)):
            arrays[view+'_positions'][at], arrays[view+'_momenta'][at] = state.positions, state.momenta
    return arrays


def complete_history(plane, source, *, parent=None):
    arrays = deterministic_arrays(source)
    raw, operand = science.array_product(source, arrays, artifact_id='native.arrays.'+source.root_id)
    task = NAMESPACE+'.'+source.root_id+'.history'
    parent = parent or NativeEffectContact('run.software.e1', task, 'attempt.'+task,
        ObjectIdentity('plan.software.e1', 'empirical-lawhood/runtime/execution-plan', '1.0.0', 'a'*64),
        ObjectIdentity(task, 'empirical-lawhood/runtime/execution-task', '1.0.0', 'b'*64), source.provenance.observed_git_head, ('input.software.e1',), ())
    config = E1OperationConfig('config.'+task, 'history', source)
    definition = NativeSubworkDefinition('paired-history.'+source.root_id, 'matrix-e1.full-paired-history', parent,
        r.identity(config), tuple(sorted((r.identity(source), r.identity(source.allocation), coordinate_identity(source.coordinate), source.provenance.identity), key=lambda x: x.object_id)),
        source.provenance.code_sources_sha256, source.provenance.dependency_lock_sha256, parent.input_materialization_ids,
        tuple(sorted((source.root.stream_identity(s) for s in source.root.streams), key=lambda x: x.object_id)),
        (NativeSubworkOutput('arrays', operand.array_artifact.payload_schema, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz'),))
    contact = NativeSubworkContact(ObjectIdentity('begin.software.e1', 'empirical-lawhood/runtime/native-subwork-begin', '1.0.0', 'c'*64))
    completion = NativeSubworkCompletion(definition.identity, ObjectIdentity.from_record('contact.software.e1', contact),
        OperationalStatus.SUCCEEDED, ('arrays',), (), definition.streams, (), (), InquiryCost(None, None, None),
        'hypothetical software receipt only, zero supplied innovation controls', None, ())
    native_task = 'native-subwork.'+sha256((parent.task_id+':'+definition.subwork_id).encode()).hexdigest()
    native_attempt = parent.run_id+'.'+native_task+'.attempt-001'
    published = retained(plane, native_task+'.output.arrays', operand.array_artifact.payload_schema, raw, Access.EVALUATION_SEALED)
    receipt = CanonicalTaskReceipt('receipt.'+native_attempt, parent.run_id, native_task, native_attempt,
        parent.implementation_commit, parent.input_materialization_ids, (published.materialization,), (published.logical,), (), OperationalStatus.SUCCEEDED, ())
    receipt = publish_completion(plane, receipt, completion, visibility=published.logical.visibility_ceiling,
        access=Access.EVALUATION_SEALED)
    history = r.E1NativeHistory('history.'+source.root_id, r.identity(source), coordinate_identity(source.coordinate), source.root_id,
        source.root.root.independent_group_id, source.coordinate.clock_id, operand, MatrixParameterNativeHistory(definition, completion, receipt),
        source.coordinate.total_ticks, 2*source.coordinate.total_ticks)
    numerical = science.assess_history(source, history, arrays)
    return history, numerical, arrays, raw


def ordinary_receipt(plane, source, role, record, array_raw=None):
    outputs = [retained(plane, 'ordinary.'+role+'.'+source.root_id, record.SCHEMA, record.canonical_bytes(), Access.EVALUATION_SEALED)]
    if array_raw is not None:
        outputs.append(retained(plane, record.arrays.array_artifact.artifact_id, record.arrays.array_artifact.payload_schema, array_raw, Access.EVALUATION_SEALED))
    outputs.sort(key=lambda m: m.logical.logical_artifact_id)
    task = NAMESPACE+'.'+source.root_id+'.'+role
    return CanonicalTaskReceipt('receipt.ordinary.'+role+'.'+source.root_id, 'run.software.e1', task, 'attempt.'+task,
        source.provenance.observed_git_head, record.native.definition.parent_contact.input_materialization_ids if role == 'history' else (),
        tuple(m.materialization for m in outputs), tuple(m.logical for m in outputs), (), OperationalStatus.SUCCEEDED, ())


def test_additive_source_roundtrip_and_exact_four_family_clocks(e1):
    _, sources, _ = e1
    for source in sources:
        assert decode_canonical_bytes(source.canonical_bytes(), r.E1HistorySource, maximum_bytes=None) == source
        assert source.coordinate.total_ticks == 8
        assert source.coordinate.physical_time(8) == source.coordinate.physical_time(16, refinement=2)
    assert len(operation_factories()) == 6
    assert {f.registration.native_effect for f in operation_factories()} == {True, False}


@pytest.mark.parametrize('defect', ('exposed-role', 'exposed-group', 'seed-collision', 'family-missing', 'clock-change', 'changed-publication'))
def test_full_history_eligibility_refuses_before_effects(e1, defect):
    _, sources, _ = e1
    allocation = sources[0].allocation
    with pytest.raises(ValueError):
        if defect == 'exposed-role':
            replace(allocation.roots[0], root=replace(allocation.roots[0].root, role=MatrixProgrammeRole.DEVELOPMENT))
        elif defect == 'exposed-group':
            row = allocation.roots[0]
            row = replace(row, root=replace(row.root, independent_group_id=allocation.exposure.exposed_independent_groups[0]))
            replace(allocation, roots=(row, *allocation.roots[1:]))
        elif defect == 'seed-collision':
            row = replace(allocation.roots[1], streams=allocation.roots[0].streams)
            replace(allocation, roots=(allocation.roots[0], row, *allocation.roots[2:]))
        elif defect == 'family-missing':
            replace(allocation, roots=allocation.roots[:-1], coordinates=allocation.coordinates[:-1])
        elif defect == 'clock-change':
            replace(allocation, coordinates=(replace(allocation.coordinates[0], target_x=D('2')), *allocation.coordinates[1:]))
        else:
            replace(sources[0].reservation, allocation=replace(allocation, allocation_id='changed.allocation'))


def test_worker_refuses_unprotected_context_before_read_or_native_contact():
    def blocked(*args, **kwargs):
        raise AssertionError('unauthorized operand or native contact was reached')
    context = SimpleNamespace(input_ports=(SimpleNamespace(read=blocked, close=lambda: None),))
    with pytest.raises(ValueError, match='protected runtime context'):
        E1NativeRunner('history').execute_with_native_subwork(context, SimpleNamespace(parent_contact=blocked))


def test_full_numerical_and_factor_cold_reproof_without_producer_rng_or_eigh(e1, monkeypatch):
    plane, sources, _ = e1
    source = sources[1]
    history, numerical, arrays, native_raw = complete_history(plane, source)
    assert numerical.numerical_pass
    assert tuple((c.denominator_steps, c.denominator_real_coordinates) for c in numerical.controls) == ((8, 192), (16, 192), (8, 192), (8, 96))
    diagnostic_raw, product = science.measure(source, history, numerical, arrays, artifact_id='factor.arrays.'+source.root_id)
    assessment = science.assess_factor(source, history, numerical, product, native_raw, diagnostic_raw)
    n = 2*2*9
    assert tuple(len(c.measured_errors) for c in assessment.controls) == (n, 15*n, n, n, n, n)
    receipts = (ordinary_receipt(plane, source, 'history', history, native_raw), ordinary_receipt(plane, source, 'numerical', numerical),
        ordinary_receipt(plane, source, 'measure', product, diagnostic_raw), ordinary_receipt(plane, source, 'check', assessment))
    def blocked(*args, **kwargs):
        raise AssertionError('cold reader entered producer, RNG or eigensolver')
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_source as native
    monkeypatch.setattr(native, 'acquire_parameter_history', blocked)
    monkeypatch.setattr(science, 'measure', blocked)
    monkeypatch.setattr(science.factor_science, 'measure_sector', blocked)
    monkeypatch.setattr(np.linalg, 'eigh', blocked)
    monkeypatch.setattr(np.linalg, 'eigvalsh', blocked)
    monkeypatch.setattr(np.random, 'Generator', blocked)
    monkeypatch.setattr(np.random, 'PCG64DXSM', blocked)
    assert science.read_retained(source, history, numerical, product, assessment, native_raw, diagnostic_raw, receipts=receipts) == (product, assessment)
    with pytest.raises(ValueError, match='receipt'):
        science.read_retained(source, history, numerical, product, assessment, native_raw, diagnostic_raw, receipts=receipts[:-1])
    changed = {name: value.copy() for name, value in arrays.items()}
    changed['fine_positions'][7, 0, 0, 0, 0] += .1
    from empirical_lawhood.adapters.methods.matrix_parameter_history import independent
    controls = independent.assess_arrays(source.coordinate, changed, trajectory_tolerance=D('1e-8'), bridge_tolerance=D('1e-11'))
    assert controls[1]['disposition'] == 'VIOLATED'


@pytest.mark.parametrize('family', range(4))
def test_each_full_family_uses_independent_complete_paired_history_equations(e1, family):
    plane, sources, _ = e1
    history, numerical, arrays, _ = complete_history(plane, sources[family])
    assert numerical.numerical_pass
    assert arrays['primary_positions'].shape == (9, 2, 3, 4, 4)
    assert arrays['fine_positions'].shape == (17, 2, 3, 4, 4)
    history.validate_source(sources[family])


def test_mutually_forged_operator_and_spectrum_fail_literal_native_state_join(e1):
    plane, sources, _ = e1
    source = sources[1]
    history, numerical, arrays, native_raw = complete_history(plane, source)
    raw, product = science.measure(source, history, numerical, arrays, artifact_id='factor.original.'+source.root_id)
    from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays, encode_matrix_arrays
    values = {n: a.copy() for n, a in decode_matrix_arrays(raw, product.arrays).items()}
    values['primary_x_operator'][4] += np.eye(15)
    values['primary_x_spectrum'][4] += 1
    forged, members = encode_matrix_arrays(values,
        nonfinite_members=tuple(n for n in values if not n.endswith(('_ticks', '_available', '_identifiable'))))
    artifact = replace(product.arrays.array_artifact, sha256=sha256(forged).hexdigest(), size_bytes=len(forged))
    operand = replace(product.arrays, array_artifact=artifact, members=members)
    product = replace(product, arrays=operand,
        traces=tuple(replace(t, diagnostics=artifact, diagnostic_members=members) for t in product.traces))
    measured = science.assess_factor(source, history, numerical, product, native_raw, forged)
    assert not measured.numerical_pass
    assert measured.controls[0].method == 'raw-operator' and measured.controls[0].disposition == 'VIOLATED'
    assert measured.controls[1].method == 'all-eigenpairs' and measured.controls[1].disposition == 'VIOLATED'


def test_long_schedule_contract_preserves_every_1024_2048_step_without_acquisition(e1):
    plane, sources, _ = e1
    original = sources[0]
    lattice = tuple(range(0, 1025, 16))
    coordinates = tuple(replace(c, ramp_ticks=256, autonomous_ticks=768, observation_ticks=lattice) for c in original.allocation.coordinates)
    roots = tuple(replace(row, coordinate=coordinate_identity(c)) for row, c in zip(original.allocation.roots, coordinates, strict=True))
    allocation = replace(original.allocation, coordinates=coordinates, roots=roots)
    reservation = replace(original.reservation, allocation=allocation, publication=publish(plane, allocation, 'e1.long.allocation'))
    rule = replace(original.rule, lattice=lattice, risk_start_tick=256, trailing_persistence_ticks=32)
    criterion = replace(original.criterion, allocation=r.identity(allocation), factor_rule=rule.identity,
        recurrence_end_tick=1024, survival_duration_ticks=128)
    selected = replace(original.specification.selection, reservation=r.identity(reservation), factor_rule=rule, criterion=criterion)
    frozen = replace(original.specification, selection=selected, publication=publish(plane, selected, 'e1.long.selection'))
    for source in sources:
        source = replace(source, reservation=reservation, specification=frozen)
        members = expected_members(source.coordinate)
        assert members['primary_positions'][1][0] == 1025
        assert members['fine_positions'][1][0] == 2049
        assert members['primary_innovations'][1][0] == 1024
        assert members['fine_innovations'][1][0] == 2048
        assert source.coordinate.physical_time(1024) == source.coordinate.physical_time(2048, refinement=2)


@pytest.mark.parametrize('defect', ('foreign-run', 'history-attempt', 'nested-locator', 'ordinary-native-id', 'exposed-native-array'))
def test_cold_reader_refuses_changed_original_run_attempt_native_locator_or_scope(e1, defect):
    plane, sources, _ = e1
    source = sources[1]
    history, numerical, arrays, native_raw = complete_history(plane, source)
    raw, product = science.measure(source, history, numerical, arrays, artifact_id='factor.arrays.'+source.root_id)
    assessment = science.assess_factor(source, history, numerical, product, native_raw, raw)
    receipts = [ordinary_receipt(plane, source, 'history', history, native_raw), ordinary_receipt(plane, source, 'numerical', numerical),
        ordinary_receipt(plane, source, 'measure', product, raw), ordinary_receipt(plane, source, 'check', assessment)]
    if defect == 'nested-locator':
        wrong = replace(history.native.receipt, task_id=history.native.definition.parent_contact.task_id)
        with pytest.raises(ValueError, match='lineage|completion'):
            history = replace(history, native=replace(history.native, receipt=wrong))
            history.validate_source(source)
        return
    if defect == 'foreign-run':
        receipts[1] = replace(receipts[1], run_id='foreign.run')
    elif defect == 'history-attempt':
        receipts[0] = replace(receipts[0], attempt_id='foreign.attempt')
    else:
        from empirical_lawhood.kernel.evidence import VisibilityCeiling
        original = history.arrays.array_artifact.artifact_id
        new_id = 'native.changed.arrays.'+source.root_id
        receipt = receipts[0]
        if defect == 'ordinary-native-id':
            logical = tuple(replace(a, logical_artifact_id=new_id) if a.logical_artifact_id == original else a for a in receipt.output_logical_artifacts)
        else:
            logical = tuple(replace(a, outcome_access=Access.DEVELOPMENT_VISIBLE, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY)
                if a.logical_artifact_id == original else a for a in receipt.output_logical_artifacts)
        physical = tuple(replace(p, logical_artifact_id=new_id) if defect == 'ordinary-native-id' and p.logical_artifact_id == original else p
            for p in receipt.output_materializations)
        receipts[0] = replace(receipt, output_logical_artifacts=logical, output_materializations=physical)
    with pytest.raises(ValueError, match='custody|receipt'):
        science.read_retained(source, history, numerical, product, assessment, native_raw, raw, receipts=tuple(receipts))
