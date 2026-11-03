# SPDX-License-Identifier: MPL-2.0
"""Exposed mathematical and genuine retained-fixture response conformance.

Fixtures do not qualify scientific sources. Original history/factor byte
packages are consumed only when explicitly selected and are never recreated.
"""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
import json
import os
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS

from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import MatrixFactorStream
from empirical_lawhood.adapters.methods.matrix_factor_response.records import MatrixFactorAction, MatrixFactorResponseModel
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import (
    MatrixParameterFactorAssessment, MatrixParameterFactorProduct, MatrixParameterFactorSource,
    MatrixParameterFactorSupply, expected_members as factor_members, identity as factor_identity, prefix,
)
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import (
    MatrixParameterHistorySource, expected_members as history_members, identity as history_identity,
)
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.science import eligible_origins
from empirical_lawhood.adapters.methods.matrix_parameter_response import independent, science
from empirical_lawhood.adapters.methods.matrix_parameter_response.operation_bindings import (
    MatrixParameterResponseForecastConfig, MatrixParameterResponseRunner, NAMESPACE,
    development_draft, operation_factories, operation_registrations, output_codecs,
)
from empirical_lawhood.adapters.methods.matrix_parameter_response.records import (
    CONTINUATION, MatrixParameterResponseAllocation, MatrixParameterResponseCausalSource,
    MatrixParameterResponseDesign, MatrixParameterResponseRoot, MatrixParameterResponseSource, identity,
)
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import initial_parameter_state
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_response import native_constant_response_branch
from empirical_lawhood.adapters.simulators.six_matrix_response.shooting import hermitian_basis
from empirical_lawhood.api.matrix_numerical_provenance import capture_matrix_provenance
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.test_matrix_parameter_factor import absent_case


def obj(name):
    return ObjectIdentity('software.response.' + name, 'empirical-lawhood/tests/parameter-response', '1.0.0', sha256(name.encode()).hexdigest())


def model_record():
    return MatrixFactorResponseModel('software.parameter-response.model', obj('parameter-generalized-origin-linearized-v1'))


def design_for(parameter, rule, *, tick, model):
    c = parameter.coordinate
    view = replace(c.primary_view, view_id=c.primary_view.view_id + '.response', rng_algorithm='PCG64', rng_version='1.0.0',
                   stream_derivation_rule_id='software.future-only.v1')
    actions = tuple(MatrixFactorAction('software.action.' + r.lower(), r, D('.001'), 1, D(1))
                    for r in ('COMPLEMENT', 'FACTOR', 'GENERIC', 'TRACE'))
    return MatrixParameterResponseDesign('software.response.design', c, rule, view, tick,
        tuple(x.hex() for x in c.couplings(tick)), actions, (1, 2, 4), 48,
        D('1e-5'), D('1e-5'), D('1e-10'), D('1e-10'), D('1e-8'), D('1e-7'), D('1e-8'), D('1e-10'), D('1e-14'),
        identity(model), obj('independent-evaluator'), obj('declared-instrument'), obj('receiver'), 'Y', 'AT_RAMP_END')


def templates():
    pauli = np.asarray([[[0, 1], [1, 0]], [[0, -1j], [1j, 0]], [[1, 0], [0, -1]]], dtype='<c16')
    generic = np.asarray([np.kron(np.eye(2), p) / 2 for p in pauli], dtype='<c16')
    coefficients = np.zeros((2, 3, 3), dtype='<f8')
    for s in range(2):
        for j in range(3):
            coefficients[s, j, j] = 1 / np.sqrt(6)
    return {'generic_basis': generic, 'force_coefficients': coefficients,
            'trace_coefficients': np.ones((2, 3), dtype='<f8') / np.sqrt(6),
            'receiver_coefficients': np.eye(48, dtype='<f8').reshape(48, 2, 2, 3, 4)}


@pytest.fixture(scope='module')
def mathematical():
    _, parameter, _, rule, *_ = absent_case()
    model = model_record()
    tick = next(t for t in rule.lattice if t >= parameter.coordinate.ramp_ticks)
    d = design_for(parameter, rule, tick=tick, model=model)
    arrays = {name: np.zeros(shape, dtype=dtype) for name, (dtype, shape) in history_members(d.coordinate).items()}
    initial = initial_parameter_state(d.coordinate)
    basis = hermitian_basis(4)
    for view, multiplier in (('primary', 1), ('fine', 2)):
        count = multiplier * d.coordinate.total_ticks + 1
        arrays[view + '_positions'][0] = initial.positions
        arrays[view + '_momenta'][0] = initial.momenta
        for j in range(1, count):
            for s in range(2):
                for k in range(3):
                    arrays[view + '_positions'][j, s, k] = np.diag([-.2, .1, .4, .8]) + .03 * basis[4 + k] + .01 * (s + k) * np.eye(4)
        arrays[view + '_alpha_tilde'][:] = np.asarray([d.coordinate.couplings(j, refinement=multiplier) for j in range(count)])
        arrays[view + '_ticks'][:] = np.arange(count)
    diagnostics = {name: np.zeros(shape, dtype=dtype) for name, (dtype, shape) in factor_members(rule).items()}
    pauli = np.asarray([[[0, 1], [1, 0]], [[0, -1j], [1j, 0]], [[1, 0], [0, -1]]], dtype='<c16')
    frame = np.asarray([np.kron(p, np.eye(2)) / 2 for p in pauli], dtype='<c16')
    for view in ('PRIMARY', 'FINE'):
        for sector in rule.sectors:
            base = prefix(view, sector)
            diagnostics[base + 'ticks'][:] = rule.lattice
            diagnostics[base + 'aligned_factor'][:] = frame
            diagnostics[base + 'available'][:] = True
            diagnostics[base + 'identifiable'][:] = True
    past = science.make_origin_arrays(d, arrays, diagnostics, templates())
    origin = SimpleNamespace(design=d)
    predicted, dispositions, _ = science.forecast_values(d, past, model)
    commitment = SimpleNamespace(dispositions=dispositions)
    return parameter, d, model, arrays, diagnostics, past, origin, predicted, commitment


def test_parameter_design_preserves_actual_schedule_and_new_constant_continuation(mathematical):
    _, d, *_ = mathematical
    assert d.continuation == CONTINUATION
    assert tuple(float(v).hex() for v in (d.alpha_x, d.alpha_y)) == d.actual_alpha_hex
    assert d.end_time == d.cutoff + 4 * d.view.timestep
    for changes in ({'continuation': 'IMPLICIT_EXTENSION'}, {'actual_alpha_hex': ('0x1p+9', '0x1p+9')},
                    {'view': replace(d.view, bath_temperature=d.view.bath_temperature * 2)}, {'ramp_boundary': 'OUTCOME_SELECTED'}):
        with pytest.raises(ValueError):
            replace(d, **changes)


def test_cold_forecast_witness_all_modes_and_force_roles_without_producer_or_eigensolver(mathematical, monkeypatch):
    *_, past, origin, predicted, commitment = mathematical
    def forbidden(*args, **kwargs):
        raise AssertionError('cold reproof entered producer/eigensolver')
    monkeypatch.setattr(science, 'forecast_values', forbidden)
    monkeypatch.setattr(np.linalg, 'eigh', forbidden)
    monkeypatch.setattr(np.linalg, 'eigvalsh', forbidden)
    independent.verify_forecast(origin, past, predicted, commitment)
    modified = dict(predicted)
    modified['origin_hessian'] = predicted['origin_hessian'].copy()
    modified['origin_hessian'][-1, -1] += 1
    with pytest.raises(ValueError):
        independent.verify_forecast(origin, past, modified, commitment)
    wrong = dict(past)
    wrong['forces'] = past['forces'].copy()
    wrong['forces'][0] = past['forces'][1]
    assert np.isclose(np.linalg.norm(wrong['forces'][0]), np.linalg.norm(past['forces'][0]))
    with pytest.raises(ValueError):
        independent.verify_instruments(origin.design, wrong)


def test_supplied_innovation_branch_preserves_full192_both_kicks_and_actual_clocks(mathematical):
    _, d, _, _, _, past, *_ = mathematical
    from empirical_lawhood.adapters.simulators.six_matrix_response.model import SixMatrixState
    state = SixMatrixState(2, past['positions'][-1], past['momenta'][-1], d.origin_tick, float(d.alpha_x), float(d.alpha_y))
    noise = np.zeros((4, 2, 3, 4, 4), dtype='<c16')
    result = native_constant_response_branch(state, member=d.member, numerical_view=d.view, direction=past['forces'][1],
        amplitude=.001, pulse_steps=1, innovations=noise)
    reference = independent.reference_branch(d, past, past['forces'][1], .001, 1, noise)
    assert set(result) == {'positions', 'momenta', 'noise', 'alpha_tilde', 'ticks'}
    for name in ('positions', 'momenta'):
        assert result[name].shape == (5, 2, 3, 4, 4)
        np.testing.assert_allclose(result[name], reference[name], rtol=0, atol=1e-9)
    assert np.array_equal(result['ticks'], np.arange(d.origin_tick, d.origin_tick + 5))
    assert np.array_equal(result['alpha_tilde'], np.tile([float(d.alpha_x), float(d.alpha_y)], (5, 1)))


def test_source_free_forecast_and_only_future_native_factory(mathematical):
    parameter, d, *_ = mathematical
    r = parameter.root.root
    cfg = MatrixParameterResponseForecastConfig(f'config.{NAMESPACE}.{r.root_id}.forecast', d, r.root_id, r.independent_group_id, r.clock_id)
    raw = cfg.canonical_bytes()
    assert b'"seed"' not in raw and b'"streams"' not in raw and b'"history_source"' not in raw
    assert not hasattr(MatrixParameterResponseRunner('forecast'), 'execute_with_native_subwork')
    factories = operation_factories()
    assert len(factories) == 4 and sum(bool(f.registration.native_effect) for f in factories) == 1


@pytest.fixture(scope='module')
def retained():
    value = os.environ.get('MATRIX_PARAMETER_RESPONSE_RETAINED_FACTOR')
    if not value:
        pytest.skip('explicit original exposed factor receipt package not selected')
    root = Path(value)
    inputs = root / 'operands'
    classes = {'parameter-source': MatrixParameterHistorySource, 'supply': MatrixParameterFactorSupply,
        'source': MatrixParameterFactorSource}
    values = {name: decode_canonical_bytes((inputs / name).read_bytes(), cls, maximum_bytes=None) for name, cls in classes.items()}
    handoff = json.loads((root.parent / 'matrix-e4-parameter-factor-installed-handoff01.json').read_text())
    publications = {}
    for item in handoff['actual_new_pure_outputs']:
        path = Path(item['path'])
        if path.name in ('product.json', 'arrays.npz'):
            raw = path.read_bytes()
            assert len(raw) == item['size_bytes'] and sha256(raw).hexdigest() == item['sha256']
            if path.name == 'arrays.npz':
                publications['factor-raw'] = raw
            else:
                cls = MatrixParameterFactorProduct if path.parent.name.endswith('measure') else MatrixParameterFactorAssessment
                publications[cls.SCHEMA] = decode_canonical_bytes(raw, cls, maximum_bytes=None)
    receipts = tuple(decode_canonical_bytes(Path(p['path']).read_bytes(), CanonicalTaskReceipt, maximum_bytes=None)
                     for p in handoff['actual_new_pure_ordinary_receipts'])
    return root, values, publications, receipts


def selected_case(retained):
    _, values, publications, receipts = retained
    parameter, supply, factor = values['parameter-source'], values['supply'], values['source']
    product, assessment = publications[MatrixParameterFactorProduct.SCHEMA], publications[MatrixParameterFactorAssessment.SCHEMA]
    rule = decode_canonical_bytes((retained[0] / 'operands/rule').read_bytes(), type(absent_case()[3]), maximum_bytes=None)
    trace = next(t for t in product.traces if (t.view, t.sector) == ('PRIMARY', 'Y'))
    tick = next(t for t in eligible_origins(trace, rule) if t >= parameter.coordinate.ramp_ticks)
    model = model_record()
    d = design_for(parameter, rule, tick=tick, model=model)
    streams = (MatrixFactorStream('future.common', 'panel.common', 98712301, 'COMMON_NOISE_PANEL'),
               MatrixFactorStream('future.independent', 'panel.independent', 98712302, 'INDEPENDENT_FUTURE'))
    roots = tuple(MatrixParameterResponseRoot(r.root, streams) for r in parameter.allocation.roots)
    initial = initial_parameter_state(parameter.coordinate)
    initial_fp = sha256(np.asarray(initial.positions, dtype='<c16').tobytes()
                        + np.asarray(initial.momenta, dtype='<c16').tobytes()).hexdigest()
    allocation = MatrixParameterResponseAllocation('software.response.future-allocation', parameter.allocation, roots, (),
        tuple((r.root_id, initial_fp) for r in roots))
    causal = MatrixParameterResponseCausalSource('software.response.causal', parameter.root.root, d,
        history_identity(parameter), history_identity(supply.product), history_identity(supply.assessment),
        factor_identity(factor), factor_identity(product), factor_identity(assessment))
    _, instruments = science.array_product(templates(), producers=(d.instrument, d.receiver),
        artifact_id='software.response.instrument-arrays', operand_id='software.response.instruments')
    provenance = capture_matrix_provenance(project_root=Path(__file__).resolve().parents[1])
    source = MatrixParameterResponseSource('software.response.source', causal, allocation, factor_identity(supply),
        supply.product.arrays.array_artifact, product.arrays.array_artifact, receipts, instruments, provenance,
        'ABSENT_CONDITIONAL_DERIVED_HISTORY')
    return source, parameter, supply, factor, product, assessment, model


@pytest.mark.held
def test_actual_retained_supplier_receipts_root_compile_and_exact_source_refusals(retained):
    case = selected_case(retained)
    source, parameter, supply, factor, product, assessment, _ = case
    source.validate_operands(parameter, supply, factor, product, assessment)
    factories = operation_factories()
    registry = CapabilityRegistry('registry.software.response', tuple(sorted((f.manifest for f in factories), key=lambda m: m.registry_id)))
    draft = development_draft((case,), draft_id='software.response.retained')
    result = compile_recursive_wave(draft=draft, registrations=operation_registrations(), registry=registry,
        implementation_commit=source.provenance.observed_git_head, output_codecs=output_codecs())
    assert len(result.execution_plan.tasks) == 4
    for changes in ({'world_kind': __import__('empirical_lawhood.kernel.worlds', fromlist=['WorldKind']).WorldKind.ANALYTIC_REFERENCE},
                    {'system': obj('foreign-system')}, {'numerical_view_ids': ()}):
        altered = replace(draft.development_study, **changes)
        with pytest.raises(ValueError):
            compile_recursive_wave(draft=replace(draft, development_study=altered), registrations=operation_registrations(),
                registry=registry, implementation_commit=source.provenance.observed_git_head, output_codecs=output_codecs())
    with pytest.raises(ValueError):
        replace(source, factor_receipts=source.factor_receipts[:1])
    with pytest.raises(ValueError, match='no original'):
        replace(source, historical_enclosing_return='AUTHENTIC_ORIGINAL_ORDINARY_RETURN').validate_operands(parameter, supply, factor, product, assessment)


@pytest.mark.held
def test_actual_retained_origin_forecast_and_original_prefix_substitution(retained):
    case = selected_case(retained)
    source, parameter, supply, factor, product, assessment, model = case
    original = Path(os.environ['MATRIX_PARAMETER_RESPONSE_RETAINED_HISTORY'])
    native = next((original / 'runs/test.e4.run/native-subwork').rglob('outputs/arrays'))
    raw = native.read_bytes()
    history = decode_matrix_arrays(raw, supply.product.arrays)
    diagnostics = decode_matrix_arrays(retained[2]['factor-raw'], product.arrays)
    origin_raw, origin = science.origin_record(source, history, diagnostics, templates(), product, artifact_id='software.response.origin-arrays')
    past = decode_matrix_arrays(origin_raw, origin.arrays)
    forecast_raw, forecast = science.forecast(origin, past, model, artifact_id='software.response.forecast-arrays')
    predicted = decode_matrix_arrays(forecast_raw, forecast.arrays)
    independent.validate_original_origin(source, origin, past, parameter, supply, factor, product, assessment, history, diagnostics)
    independent.verify_forecast(origin, past, predicted, forecast)
    changed = dict(past)
    changed['positions'] = past['positions'].copy()
    changed['positions'][-1, 1, 2, 3, 3] += .0001
    with pytest.raises(ValueError):
        independent.validate_original_origin(source, origin, changed, parameter, supply, factor, product, assessment, history, diagnostics)
    assert source.historical_enclosing_return == 'ABSENT_CONDITIONAL_DERIVED_HISTORY'
    assert source.design.origin_tick == 944


@pytest.mark.held
def test_genuine_four_phase_exposed_native_receipts_cold_and_portable(retained, tmp_path, monkeypatch):
    """One newly entered software response case; no original producer replay."""
    if completed := os.environ.get('MATRIX_PARAMETER_RESPONSE_COMPLETED_FIXTURE'):
        return _completed_fixture_cold(Path(completed), tmp_path, monkeypatch)
    from empirical_lawhood.api.execution import _StaticInputResolver
    from empirical_lawhood.infrastructure.execution import DirectTaskExecutor, LocalScheduler
    from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
    from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
    from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
    from empirical_lawhood.infrastructure.sql import SQLiteOperationalRepository, create_catalog_engine, upgrade_catalog
    from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore, decode_artifact_manifest
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.kernel.status import OperationalStatus
    from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
    from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
    from empirical_lawhood.runtime.execution import ExecutionAssuranceProfile, RunnerRegistry, VerifiedArtifactInput
    from empirical_lawhood.runtime.native_subwork import NativeSubworkState
    from empirical_lawhood.runtime.plans import PlanLane
    from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryIndex
    from empirical_lawhood.adapters.methods.matrix_parameter_response.operation_bindings import operands
    from empirical_lawhood.adapters.methods.matrix_parameter_response.records import (
        MatrixParameterResponseOrigin, MatrixParameterResponseForecast, MatrixParameterNativeResponses,
        MatrixParameterResponseAssessment,
    )
    from empirical_lawhood.adapters.methods.matrix_parameter_response.frontier import (
        protocol_for_source, reduce_parameter_frontier,
    )
    from tests.runtime_platform.test_native_subwork import _plane
    import shutil

    case = selected_case(retained)
    s, parameter, supply, factor_source, factor_product, factor_assessment, _ = case
    historical = Path(os.environ['MATRIX_PARAMETER_RESPONSE_RETAINED_HISTORY'])
    preserved = {str(p.relative_to(historical)): sha256(p.read_bytes()).hexdigest()
                 for p in historical.rglob('*') if p.is_file()}
    history_raw = next((historical / 'runs/test.e4.run/native-subwork').rglob('outputs/arrays')).read_bytes()
    instrument_raw, _ = science.array_product(templates(), producers=(s.design.instrument, s.design.receiver),
        artifact_id=s.instrument_arrays.array_artifact.artifact_id, operand_id=s.instrument_arrays.operand_id)
    records = operands(*case) | {'streams.' + stream.purpose_id: stream for stream in s.root.streams}
    by_sha = {r.fingerprint(): r.canonical_bytes() for r in records.values()}
    by_sha.update({sha256(raw).hexdigest(): raw for raw in (history_raw, retained[2]['factor-raw'], instrument_raw)})
    draft = development_draft((case,), draft_id='software.response.actual-fixture')
    factories = operation_factories()
    registry = CapabilityRegistry('registry.software.response.fixture', tuple(sorted((f.manifest for f in factories), key=lambda m: m.registry_id)))
    compiled = compile_recursive_wave(draft=draft, registrations=operation_registrations(), registry=registry,
        implementation_commit=s.provenance.observed_git_head, output_codecs=output_codecs())
    by_sha.update({c.record.fingerprint(): c.payload for c in compiled.config_inputs})
    plan, run = compiled.execution_plan, compiled.run_plan
    plane = _plane(tmp_path / 'original', binary_codecs=MATRIX_STORAGE_CODECS)
    inputs = []
    specs = {v.logical_artifact_id: v for t in plan.tasks for v in t.external_inputs}
    for i, (aid, spec) in enumerate(sorted(specs.items())):
        raw = by_sha[spec.expected_content_sha256]
        array = spec.expected_payload_schema == MATRIX_ARRAY_SCHEMA
        published = plane.write(ArtifactWriteRequest(aid, f'inputs/input-{i:03d}' + ('.npz' if array else '.json'),
            spec.expected_payload_schema, ArtifactProfile.MATRIX_ARRAY_NPZ if array else ArtifactProfile.CANONICAL_JSON,
            spec.expected_media_type, 'software.parameter-response.fixture', 'inputs', raw,
            VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
        manifest = decode_artifact_manifest(plane.root.resolve(published.manifest_materialization.relative_path, for_write=False).read_bytes())
        inputs.append(VerifiedArtifactInput(manifest.logical, manifest.materialization))
    runners = RunnerRegistry(tuple(sorted((f.runner_factory() for f in factories), key=lambda r: r.manifest.registry_id)),
        registry_sha256=compiled.registry.fingerprint())
    index = DevelopmentRunRecoveryIndex.from_execution_plan(plan, run_id=run.run_plan_id,
        wave_id='wave.software.response', authority_identities=())
    recovery = ExternalRunRecoveryStore(plane)
    recovery.freeze(index)
    receipts = ExternalTaskReceiptStore(plane)
    contacts = ExternalNativeEffectContactStore(plane=plane, execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    engine = create_catalog_engine('sqlite+pysqlite:///:memory:')
    upgrade_catalog(engine)
    repository = SQLiteOperationalRepository(engine)
    scheduler = LocalScheduler(operational_repository=repository, artifact_writer=plane, receipt_store=receipts,
        recovery_index=index, recovery_store=recovery, runner_registry=runners, implementation_commit=s.provenance.observed_git_head,
        external_input_resolver=_StaticInputResolver(tuple(inputs)), executor=DirectTaskExecutor(), input_port_factory=plane,
        lane=PlanLane.DEVELOPMENT, authorized_barriers=(), assurance_profile=ExecutionAssuranceProfile.TRUSTED_LOCAL,
        native_effect_contact_store=contacts,
        native_effect_capability_keys=tuple(f.manifest.capability_key for f in factories if f.registration.native_effect))
    try:
        result = scheduler.execute(run.run_plan_id, plan)
        assert result.status is OperationalStatus.SUCCEEDED, tuple((a.task_id, a.disposition, a.reason_code) for a in repository.attempts(run.run_plan_id))
        assert len(result.receipts) == 4
        store = ExternalNativeSubworkStore(plane=plane, parent_contacts=contacts)
        contact = contacts.read(run.run_plan_id, f'{NAMESPACE}.{s.root.root_id}.futures')
        definitions = tuple(store.iter_roster_definitions(contact))
        assert len(definitions) == 24 and all(store.inspect(d).state is NativeSubworkState.COMPLETED for d in definitions)
        raw_records, publications = {}, {}
        for receipt in result.receipts:
            for logical in receipt.output_logical_artifacts:
                material = next(m for m in receipt.output_materializations if m.logical_artifact_id == logical.logical_artifact_id)
                raw = plane.root.resolve(material.relative_path, for_write=False).read_bytes()
                assert sha256(raw).hexdigest() == logical.content_sha256
                publications[logical.logical_artifact_id] = raw
                if logical.payload_schema != MATRIX_ARRAY_SCHEMA:
                    raw_records[logical.payload_schema] = raw
        classes = (MatrixParameterResponseOrigin, MatrixParameterResponseForecast, MatrixParameterNativeResponses, MatrixParameterResponseAssessment)
        o, f, n, assessment = (decode_canonical_bytes(raw_records[c.SCHEMA], c, maximum_bytes=None) for c in classes)
        assert len(assessment.scores) == 5760 and len(n.events) == 24
        assert assessment.native_reference_pass and assessment.numerical_convergence == 'UNASSESSED'
        publications[s.history_arrays.artifact_id] = history_raw
        publications[s.factor_arrays.artifact_id] = retained[2]['factor-raw']
        def blocked(*args, **kwargs):
            raise AssertionError('cold completed receipt recovery entered producer/native/eigensolver/RNG')
        monkeypatch.setattr(science, 'forecast', blocked)
        monkeypatch.setattr(science, 'native_branch', blocked)
        monkeypatch.setattr(np.linalg, 'eigh', blocked)
        monkeypatch.setattr(np.linalg, 'eigvalsh', blocked)
        monkeypatch.setattr(np.random, 'Generator', blocked)
        monkeypatch.setattr(ExternalNativeSubworkStore, 'begin', blocked)
        monkeypatch.setattr(ExternalNativeSubworkStore, 'contact', blocked)
        cold = independent.read_retained(s.canonical_bytes(), *(raw_records[c.SCHEMA] for c in classes),
            lambda a: publications[a.artifact_id], original_records=(parameter, supply, factor_source, factor_product, factor_assessment))
        assert cold == assessment
        past = decode_matrix_arrays(publications[o.arrays.array_artifact.artifact_id], o.arrays)
        frontier = reduce_parameter_frontier(protocol_for_source(s, protocol_id='software.parameter.frontier'),
            s, o, cold, past['receivers'], stratum_id=s.design.coordinate.family_id)
        assert len(frontier.horizon_losses) == 15
        assert all(store.recover(d).state is NativeSubworkState.COMPLETED for d in definitions)
        assert scheduler.execute(run.run_plan_id, plan) == result
        portable_path = tmp_path / 'portable'
        shutil.copytree(tmp_path / 'original', portable_path)
        portable = _plane(portable_path, binary_codecs=MATRIX_STORAGE_CODECS)
        portable_contacts = ExternalNativeEffectContactStore(plane=portable, execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
            visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
        portable_store = ExternalNativeSubworkStore(plane=portable, parent_contacts=portable_contacts)
        assert all(portable_store.recover(d).state is NativeSubworkState.COMPLETED for d in definitions)
        assert {str(p.relative_to(historical)): sha256(p.read_bytes()).hexdigest()
                for p in historical.rglob('*') if p.is_file()} == preserved
    finally:
        engine.dispose()


def _completed_fixture_cold(root, tmp_path, monkeypatch):
    """Authenticate previously completed exposed children without any replay."""
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.adapters.methods.matrix_parameter_response.records import (
        MatrixParameterResponseOrigin, MatrixParameterResponseForecast, MatrixParameterNativeResponses,
        MatrixParameterResponseAssessment,
    )
    from empirical_lawhood.adapters.methods.matrix_parameter_response.frontier import protocol_for_source, reduce_parameter_frontier
    from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
    from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
    from empirical_lawhood.runtime.native_subwork import NativeSubworkState
    from tests.runtime_platform.test_native_subwork import _plane
    import shutil

    def original(cls):
        for path in (root / 'inputs').glob('*.json'):
            if json.loads(path.read_text()).get('schema') == cls.SCHEMA:
                return decode_canonical_bytes(path.read_bytes(), cls, maximum_bytes=None)
        raise ValueError('completed fixture lacks actual typed original input')
    source = original(MatrixParameterResponseSource)
    upstream = tuple(original(c) for c in (MatrixParameterHistorySource, MatrixParameterFactorSupply,
        MatrixParameterFactorSource, MatrixParameterFactorProduct, MatrixParameterFactorAssessment))
    receipts = tuple(decode_canonical_bytes(p.read_bytes(), CanonicalTaskReceipt, maximum_bytes=None)
        for p in (root / 'runs').rglob('*.json') if '/receipts/' in str(p)
        and json.loads(p.read_text()).get('schema') == CanonicalTaskReceipt.SCHEMA)
    assert len(receipts) == 28
    publications, raw_records = {}, {}
    for receipt in receipts:
        for logical in receipt.output_logical_artifacts:
            material = next(m for m in receipt.output_materializations if m.logical_artifact_id == logical.logical_artifact_id)
            raw = (root / material.relative_path).read_bytes()
            assert sha256(raw).hexdigest() == logical.content_sha256 == material.physical_sha256
            publications[logical.logical_artifact_id] = raw
            if receipt.task_id.startswith(NAMESPACE) and logical.media_type == 'application/json':
                raw_records[logical.payload_schema] = raw
    for p in (root / 'inputs').glob('*.npz'):
        raw = p.read_bytes()
        for artifact in (source.history_arrays, source.factor_arrays):
            if sha256(raw).hexdigest() == artifact.sha256:
                publications[artifact.artifact_id] = raw
    def blocked(*args, **kwargs):
        raise AssertionError('completed fixture entered producer/native/eigen/RNG')
    for target, name in ((science, 'forecast'), (science, 'native_branch'), (np.linalg, 'eigh'),
                         (np.linalg, 'eigvalsh'), (np.random, 'Generator'),
                         (ExternalNativeSubworkStore, 'begin'), (ExternalNativeSubworkStore, 'contact')):
        monkeypatch.setattr(target, name, blocked)
    classes = (MatrixParameterResponseOrigin, MatrixParameterResponseForecast, MatrixParameterNativeResponses, MatrixParameterResponseAssessment)
    cold = independent.read_retained(source.canonical_bytes(), *(raw_records[c.SCHEMA] for c in classes),
        lambda a: publications[a.artifact_id], original_records=upstream)
    assert len(cold.scores) == 5760 and cold.native_reference_pass
    o = decode_canonical_bytes(raw_records[classes[0].SCHEMA], classes[0], maximum_bytes=None)
    native = decode_canonical_bytes(raw_records[classes[2].SCHEMA], classes[2], maximum_bytes=None)
    past = decode_matrix_arrays(publications[o.arrays.array_artifact.artifact_id], o.arrays)
    frontier = reduce_parameter_frontier(protocol_for_source(source, protocol_id='software.response.cold-frontier'),
        source, o, cold, past['receivers'], stratum_id=source.design.coordinate.family_id)
    assert len(frontier.horizon_losses) == 15
    portable = tmp_path / 'portable-completed'
    shutil.copytree(root, portable)
    plane = _plane(portable, binary_codecs=MATRIX_STORAGE_CODECS)
    contacts = ExternalNativeEffectContactStore(plane=plane, execution_plan=native.events[0].definition.parent_contact.execution_plan,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    store = ExternalNativeSubworkStore(plane=plane, parent_contacts=contacts)
    assert all(store.recover(e.definition).state is NativeSubworkState.COMPLETED for e in native.events)
