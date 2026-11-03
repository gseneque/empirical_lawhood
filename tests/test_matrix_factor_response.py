"""Exposed mechanical kernels, receipt readback and reusable worker ports."""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
import io
import shutil
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import FactorEventSpec
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.science import causal_observations, measure_sector
from empirical_lawhood.adapters.methods.matrix_factor_response import independent, science
from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import BUDGET
from empirical_lawhood.adapters.methods.matrix_factor_response.operation_bindings import _run_native
from empirical_lawhood.adapters.methods.matrix_factor_response.records import (
    PREDICTORS, MatrixFactorAction, MatrixFactorPreparationRecipe, MatrixFactorResponseDesign,
    MatrixFactorResponseModel, MatrixResponseArrays, identity,
)
from empirical_lawhood.adapters.methods.matrix_history_analysis import algebra
from empirical_lawhood.adapters.methods.matrix_prospective.example import example_source
from empirical_lawhood.adapters.simulators.six_matrix_response.factor_response import factor_response_force_step
from empirical_lawhood.adapters.simulators.six_matrix_response import factor_response, simulation
from empirical_lawhood.adapters.simulators.six_matrix_response.factor_bridge import factor_frame_sha256
from empirical_lawhood.adapters.simulators.six_matrix_response.gradients import SixMatrixParameters, reference_action_terms
from empirical_lawhood.adapters.simulators.six_matrix_response.model import SixMatrixState, hermitian_part
from empirical_lawhood.adapters.simulators.six_matrix_response.simulation import baoab_step_with_hermitian_noise
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.native_subwork import NativeSubworkState
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.execution import VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind
from tests.test_matrix_parameter_native import REGIMES, coordinate, corpus


@pytest.mark.parametrize('regime',REGIMES)
@pytest.mark.parametrize('amplitude',(-.2,0.,.2))
def test_factor_response_cache_preserves_every_step_and_gradient_count(regime, amplitude, monkeypatch):
    c = coordinate(regime)
    rng,state,direction,_,_ = corpus()
    noise = np.asarray([simulation.hermitian_noise(rng=rng,q=2) for _ in range(8)],dtype='<c16')
    gradient = simulation.analytic_gradient_terms
    evaluations = []
    def counted(*args, **kwargs):
        evaluations.append(None)
        return gradient(*args, **kwargs)
    monkeypatch.setattr(simulation,'analytic_gradient_terms',counted)
    expected_positions,expected_momenta = [state.positions.copy()],[state.momenta.copy()]
    reference = state
    for tick,innovation in enumerate(noise):
        reference = factor_response_force_step(reference,direction=direction,
            amplitude=amplitude if tick < 3 else 0.,member=c.member,numerical_view=c.primary_view,
            standardized_noise=innovation)
        expected_positions.append(reference.positions.copy());expected_momenta.append(reference.momenta.copy())
    assert len(evaluations) == 2*len(noise)
    evaluations.clear()
    actual = factor_response.native_factor_response_branch(state,direction=direction,
        amplitude=amplitude,pulse_steps=3,member=c.member,numerical_view=c.primary_view,innovations=noise)
    assert len(evaluations) == len(noise)+1
    assert actual['positions'].tobytes() == np.asarray(expected_positions,dtype='<c16').tobytes()
    assert actual['momenta'].tobytes() == np.asarray(expected_momenta,dtype='<c16').tobytes()
    assert actual['noise'].tobytes() == noise.tobytes()

def object_id(name):
    return ObjectIdentity(name,'empirical-lawhood/test/'+name,'1.0.0','a'*64)

def product(arrays,name,producers):
    raw,members = encode_matrix_arrays(arrays)
    artifact = ArtifactIdentity(name,'matrix-arrays',MATRIX_ARRAY_SCHEMA,sha256(raw).hexdigest(),'application/x-npz',len(raw))
    return raw,MatrixResponseArrays(name,artifact,members,tuple(sorted(producers,key=lambda p:p.object_id)))

def mechanical_case():
    """Literal numerical inputs; no source wrapper or authority is constructed."""
    condition = example_source().protocol
    model = MatrixFactorResponseModel('test.b.model',object_id('test.b.model-implementation'))
    recipe = MatrixFactorPreparationRecipe('test.b.constant-prefix','CONSTANT_ALPHA_NEW_PREFIX',D(2)/3,D(22)/3,'PCG64:1.0.0')
    rule = FactorEventSpec('test.b.factor-rule',('Y',),(0,1),D('.001'),0,0,
        D('.05'),D('.05'),D('15'),D('15'),D('30'),D('1e-10'),D('1e-20'),D('.5'))
    design = MatrixFactorResponseDesign(design_id='test.b.design',rule=rule,member=condition.member,view=condition.view,
        alpha_x=D(2)/3,alpha_y=D(22)/3,origin_tick=0,
        actions=tuple(MatrixFactorAction('test.action.'+role.lower(),role,D('.1'),1,D(1)) for role in ('COMPLEMENT','FACTOR','GENERIC','TRACE')),
        horizon_steps=(1,),receiver_count=1,hessian_difference_step=D('.0001'),generic_gap_minimum=D('1e-9'),
        spectral_gap_minimum=D('1e-9'),native_reference_tolerance=D('.000001'),weak_response_minimum=D('.0000001'),
        potential_difference_step=D('.000002'),hessian_reference_tolerance=D('.001'),
        model=identity(model),evaluator=object_id('test.b.evaluator'),instrument=object_id('test.b.instrument'),
        receiver=object_id('test.b.receiver'),initial_state_rule=object_id('test.b.initial'),
        preparation_schedule=ObjectIdentity.from_record(recipe.recipe_id,recipe))
    rng = np.random.default_rng(404)
    positions = np.stack((algebra.LEFT,algebra.RIGHT))+.001*hermitian_part(rng.normal(size=(2,3,4,4))+1j*rng.normal(size=(2,3,4,4)))
    initial = {'positions':np.asarray(positions[None],dtype='<c16'),'momenta':np.zeros((1,2,3,4,4),dtype='<c16')}
    coefficients = np.zeros((1,2,2,3,4)); coefficients[:,1,:,:,1] = 1/np.sqrt(6)
    templates = {'force_coefficients':np.ones((2,3,3),dtype='<f8')/np.sqrt(18),
        'generic_basis':np.asarray(algebra.RIGHT,dtype='<c16'),
        'receiver_coefficients':coefficients,'trace_coefficients':np.ones((2,3),dtype='<f8')/np.sqrt(6)}
    return design,initial,templates,model

def mechanical_origin(case):
    """Direct numerical origin, without a canonical source or custody claim."""
    design,initial,templates,_ = case
    sector = ('X','Y').index(design.factor_sector)
    measured = {tick:measure_sector(initial['positions'][tick,sector],design.rule)
        if tick <= design.origin_tick else None for tick in design.rule.lattice}
    observations,frames = causal_observations(design.rule,measured)
    selected = next(row for row in observations if row.tick == design.origin_tick)
    assert selected.status == 'AVAILABLE' and selected.identifiable is True
    assert selected.causal_admitted is True and selected.raw_admitted is True
    assert not selected.alignment_ambiguous
    frame = np.asarray(frames[design.origin_tick],dtype='<c16')
    forces,receivers = science._instrument(design,frame,templates)
    past = dict(initial) | {'frame':frame,'forces':forces,'receivers':receivers}
    return SimpleNamespace(design=design,frame_sha256=factor_frame_sha256(frame)),past

def test_full_coupled_force_both_kicks_and_zero_force_baseline():
    case = mechanical_case()
    design,_,_,_ = case
    _,past = mechanical_origin(case)
    state = SixMatrixState(2,past['positions'][-1],past['momenta'][-1],0,float(design.alpha_x),float(design.alpha_y))
    noise = independent.noise_panel(SimpleNamespace(seed=992),1)[0]
    force = past['forces'][1]
    actual = factor_response_force_step(state,amplitude=.1,direction=force,member=design.member,numerical_view=design.view,standardized_noise=noise)
    reference = independent.reference_branch(design,past,force,.1,1,noise[None])
    np.testing.assert_allclose(actual.positions,reference['positions'][1],atol=1e-8)
    np.testing.assert_allclose(actual.momenta,reference['momenta'][1],atol=1e-8)
    native = baoab_step_with_hermitian_noise(state,member=design.member,numerical_view=design.view,
        next_alpha_tilde_x=state.alpha_tilde_x,next_alpha_tilde_y=state.alpha_tilde_y,standardized_noise=noise)
    unforced = factor_response_force_step(state,amplitude=0.,direction=force,member=design.member,numerical_view=design.view,standardized_noise=noise)
    np.testing.assert_array_equal(unforced.positions,native.positions)
    np.testing.assert_array_equal(unforced.momenta,native.momenta)
    assert np.linalg.norm(actual.momenta[0]-native.momenta[0]) > 0
    assert np.linalg.norm(actual.momenta[1]-native.momenta[1]) > 0

def test_additive_potential_matches_literal_owner_at_changed_physics():
    case = mechanical_case()
    design,_,_,_ = case
    _,past = mechanical_origin(case)
    design = replace(design,member=replace(design.member,mass_x=D('.7'),mass_y=D('.7'),cross_coupling_gamma=D('1.2')),
        alpha_x=D('.5'),alpha_y=D('3.4'))
    parameters = SixMatrixParameters(2,.7,.7,1.2,.5,3.4)
    np.testing.assert_allclose(independent.potential(past['positions'][-1],design),
        reference_action_terms(past['positions'][-1],parameters).total,atol=1e-12)

def test_full_coupled_response_keeps_requested_amplitude():
    case = mechanical_case()
    design,_,_,model = case
    origin,past = mechanical_origin(case)
    predicted,_,_ = science.forecast_values(origin,past,model)
    hessian = predicted['origin_hessian']
    modes = science.reduction_modes(origin,past,hessian)[0]['FULL_COUPLED']
    action = design.actions[1]
    doubled = science._linear_response(design,modes,hessian,past['forces'][1],past['receivers'],
        replace(action,amplitude=2*action.amplitude))
    np.testing.assert_allclose(doubled,2*predicted['full_coupled'][1],atol=1e-12)


def test_unidentified_factor_retains_unadmitted_observation():
    design,initial,_,_ = mechanical_case()
    sector = ('X','Y').index(design.factor_sector)
    measured = {tick:measure_sector(np.zeros_like(initial['positions'][tick,sector]),design.rule)
        if tick <= design.origin_tick else None for tick in design.rule.lattice}
    observations,frames = causal_observations(design.rule,measured)
    selected = next(row for row in observations if row.tick == design.origin_tick)
    assert selected.status == 'UNIDENTIFIABLE' and selected.identifiable is False
    assert selected.raw_admitted is None and selected.causal_admitted is None
    assert design.origin_tick not in frames


def test_degenerate_comparator_retains_unresolved_complete_payload():
    design,initial,templates,model = mechanical_case()
    initial['positions'][0] = np.stack((algebra.LEFT,algebra.RIGHT))
    origin,past = mechanical_origin((design,initial,templates,model))
    values,dispositions,nonfinite = science.forecast_values(origin,past,model)
    assert dict((name,state) for name,state,_ in dispositions)['SPECTRA'] == 'UNRESOLVED'
    assert np.isnan(values['spectra']).all() and 'spectra' in nonfinite
    assert set(values) == {*(name.lower() for name in PREDICTORS),'origin_hessian'}


def test_actual_mechanistic_estimators_covariant_on_complete_origin_instrument():
    case = mechanical_case()
    _,_,_,model = case
    origin,past = mechanical_origin(case)
    expected,dispositions,_ = science.forecast_values(origin,past,model)
    rng = np.random.default_rng(723)
    unitary,_ = np.linalg.qr(rng.normal(size=(4,4))+1j*rng.normal(size=(4,4)))
    transformed = {name:np.asarray(unitary@values@unitary.conj().T,dtype='<c16') for name,values in past.items()}
    conjugate_origin = SimpleNamespace(design=origin.design,frame_sha256=factor_frame_sha256(transformed['frame']))
    observed,actual_dispositions,_ = science.forecast_values(conjugate_origin,transformed,model)
    assert dispositions == actual_dispositions
    for name in PREDICTORS:
        np.testing.assert_allclose(observed[name.lower()],expected[name.lower()],atol=1e-10,rtol=1e-6)


def test_model_budget_and_design_normalization_substitution_refuse():
    design,_,_,model = mechanical_case()
    recipe = MatrixFactorPreparationRecipe('test.b.constant-prefix','CONSTANT_ALPHA_NEW_PREFIX',
        D(2)/3,D(22)/3,'PCG64:1.0.0')
    with pytest.raises(ValueError,match='historical ramp'):
        replace(recipe,rng_revision='ORIGINAL_PCG64DXSM_RETAINED_NOT_REGENERATED')
    with pytest.raises(ValueError,match='budget'):
        replace(model,fitting_budget=1)
    with pytest.raises(ValueError,match='normalization'):
        replace(design,normalization='DERIVATIVE_DIVIDE_BY_AMPLITUDE')

def test_completed_native_child_recovers_receipt_bytes_without_producer_or_begin():
    values = {'positions':np.arange(96,dtype='<c16').reshape(1,2,3,4,4),
        'momenta':np.zeros((1,2,3,4,4),dtype='<c16')}
    raw,_ = encode_matrix_arrays(values)
    inspection = SimpleNamespace(completion=SimpleNamespace(operational_status=OperationalStatus.SUCCEEDED),receipt=object(),
        outputs=(SimpleNamespace(logical=SimpleNamespace(payload_schema=MATRIX_ARRAY_SCHEMA,profile=ArtifactProfile.MATRIX_ARRAY_NPZ),
            materialization=SimpleNamespace(size_bytes=len(raw))),))
    class Completed:
        def recover(self,definition):
            return inspection
        def iter_completed_output(self,definition,output_id):
            assert output_id == 'arrays'
            yield raw
        def begin(self,*args):
            pytest.fail('completed scientific child cannot begin again')
    def forbidden():
        pytest.fail('completed scientific child producer cannot execute again')
    expected = {name:('<c16',value.shape) for name,value in values.items()}
    recovered = _run_native(Completed(),object(),forbidden,expected)
    for name in values:
        np.testing.assert_array_equal(recovered[name],values[name])
        assert not recovered[name].flags.writeable
    with pytest.raises(ValueError,match='Matrix NPY axes, dtype or layout differ from the manifest'):
        _run_native(Completed(),object(),forbidden,expected|{'positions':('<c16',(2,2,3,4,4))})

@pytest.mark.parametrize('state',(NativeSubworkState.BEGUN,NativeSubworkState.UNKNOWN_COMPLETION))
def test_uncertain_or_begun_native_child_cannot_be_replayed(state):
    class Unknown:
        def recover(self,definition):
            return None
        def inspect(self,definition):
            return SimpleNamespace(state=state)
        def begin(self,*args):
            pytest.fail('uncertain child cannot begin again')
    with pytest.raises(ValueError,match='retained or uncertain'):
        _run_native(Unknown(),object(),lambda:pytest.fail('native replay'),{})

def test_completed_child_real_receipt_relocation_and_corruption_refusal(tmp_path,monkeypatch):
    from empirical_lawhood.infrastructure.artifact_validation import ArtifactIdentityConflict, ArtifactProfileValidatorRegistry
    from empirical_lawhood.runtime.native_subwork import NativeSubworkOutput, NativeSubworkRoster
    from tests.runtime_platform.test_native_subwork import _selected, _complete, _plane, _store

    values = {'positions':np.arange(96,dtype='<c16').reshape(1,2,3,4,4),
        'momenta':np.zeros((1,2,3,4,4),dtype='<c16')}
    expected = {name:('<c16',value.shape) for name,value in values.items()}
    raw,_ = encode_matrix_arrays(values)
    # Existing exposed runtime metadata supplies real retained inputs and a
    # declared output; no scientific source, acquisition or authority is claimed.
    store,definition,inputs = _selected(tmp_path,freeze=False)
    store.plane.validators = ArtifactProfileValidatorRegistry(binary_codecs=MATRIX_STORAGE_CODECS)
    definition = replace(definition,outputs=(NativeSubworkOutput('arrays',MATRIX_ARRAY_SCHEMA,
        ArtifactProfile.MATRIX_ARRAY_NPZ,'application/x-npz'),))
    store.freeze_roster(NativeSubworkRoster('selected.native-subwork',definition.parent_contact,
        (definition.identity,)),definitions=(definition,))
    entry = store.begin(definition,inputs)
    store.contact(entry)
    store.publish_output(entry,'arrays',(raw,),maximum_bytes=len(raw),maximum_chunk_bytes=len(raw),
        expected_size_bytes=len(raw),expected_physical_sha256=sha256(raw).hexdigest())
    _complete(store,entry)
    before = store.recover(definition)
    target = tmp_path/'relocated'
    shutil.copytree(store.plane.root.contract.canonical_path,target)
    reader = _store(_plane(target,binary_codecs=MATRIX_STORAGE_CODECS),definition.parent_contact)
    def forbidden(*args,**kwargs):
        pytest.fail('receipt-only recovery cannot create a native effect or call its producer')
    for method in ('begin','contact','publish_output','complete'):
        monkeypatch.setattr(reader,method,forbidden)
    recovered = _run_native(reader,definition,forbidden,expected)
    for name in values:
        np.testing.assert_array_equal(recovered[name],values[name])
    assert reader.recover(definition) == before
    output = before.outputs[0].materialization
    path = reader.plane.root.resolve(output.relative_path,for_write=False)
    raw = path.read_bytes()
    path.write_bytes(raw[:-1]+bytes((raw[-1]^1,)))
    with pytest.raises(ArtifactIdentityConflict,match='bytes differ|changed during its verification scope'):
        _run_native(reader,definition,forbidden,expected)

def native_fixture_context(plane, *, runner, config, manifests, run_id, attempt_id,
                           output_ports, access, task_record=None, receipts=()):
    """Expose this fixture's actual ports and explicit original task edges."""
    from empirical_lawhood.runtime.execution import DependencyReceiptBinding

    dependencies = set() if task_record is None else {
        row.operational_logical_artifact_id for row in task_record.scientific_inputs if row.producer_task_id is not None}
    ports = []
    for manifest in manifests:
        logical, material = manifest.logical, manifest.materialization
        kind = WorkerInputKind.DEPENDENCY if logical.logical_artifact_id in dependencies else WorkerInputKind.EXTERNAL
        binding = WorkerInputBinding(logical.logical_artifact_id, material.materialization_id,
            logical.payload_schema, logical.media_type, material.size_bytes,
            logical.visibility_ceiling, logical.outcome_access, kind)
        ports.append(plane.open(VerifiedArtifactInput(manifest.logical,manifest.materialization), binding=binding, maximum_bytes=material.size_bytes))
    dependent_materials = {row.materialization_id for row in ports if row.binding.kind is WorkerInputKind.DEPENDENCY}
    receipt_bindings = tuple(sorted((DependencyReceiptBinding(receipt.receipt_id, receipt.task_id,
        tuple(sorted(row.materialization_id for row in receipt.output_materializations
            if row.materialization_id in dependent_materials))) for receipt in receipts
        if any(row.materialization_id in dependent_materials for row in receipt.output_materializations)), key=lambda row: row.receipt_id))
    return SimpleNamespace(run_id=run_id, attempt_id=attempt_id,
        task_id=config.config_id.removeprefix('config.'), input_ports=tuple(ports), output_ports=output_ports,
        config=SimpleNamespace(content_sha256=config.fingerprint()), dependency_receipts=receipt_bindings,
        resource_budget=BUDGET if task_record is None else task_record.capability.requested_resources,
        permissions=runner.manifest.permissions if task_record is None else task_record.capability.required_permissions,
        outcome_access=access)

class Reader:
    def __init__(self,raw):
        self.stream=io.BytesIO(raw)
    @property
    def bytes_read(self):
        return self.stream.tell()
    def read(self,size=-1):
        return self.stream.read(size)
    def close(self):
        self.stream.close()
