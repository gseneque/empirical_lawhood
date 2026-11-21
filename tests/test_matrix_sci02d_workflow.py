# SPDX-License-Identifier: MPL-2.0
"""Disclosed SCI02-D compiler and custody controls, not study evidence."""
from dataclasses import replace
from decimal import Decimal
from types import SimpleNamespace
import numpy as np
import pytest
from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge import bindings as binding, experiment, science
from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge.records import BridgeDesign, BridgeSelection, BridgeFit, BridgeProduct
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave
from tests.runtime_platform.test_recursive_compiler import fixture as campaign_fixture


def setup(tmp_path):
    from tests.test_matrix_later_programme import metadata
    design = BridgeDesign('test.sci02d.design', 'a'*64)
    selection = BridgeSelection('test.sci02d.selection', design, 'b'*64)
    provenance = metadata.__wrapped__(tmp_path)[1].provenance
    train = tuple(ObjectIdentity('test.training.'+str(i), BridgeProduct.SCHEMA, '1.0.0', str(i%10)*64) for i in range(16))
    fit = BridgeFit('test.fit', design.identity, train, ((Decimal(0),)*4,)*3, (Decimal(1),)*3)
    return design, selection, provenance, fit


def test_complete_compiler_and_strict_causal_ports(tmp_path):
    design, selection, provenance, fitted = setup(tmp_path)
    declarations = binding.operation_declarations()
    registry = CapabilityRegistry('registry.test.sci02d', tuple(d.manifest() for d in declarations))
    kwargs = dict(registry=registry, registrations=tuple(d.registration() for d in declarations), implementation_commit='a'*40,
        output_codecs={s:k for d in declarations for s,k in d.record_codecs.items()})
    for tranche, fit, count in (('TRAINING', None, 34), ('CONFIRMATION', fitted, 145)):
        roots = experiment.roots_for(selection, tranche)
        draft, records = binding.lower(design, selection, roots, provenance, campaign_fixture()[0].campaign,
            draft_id='test.draft.sci02d.'+tranche.lower(), fitted=fit)
        compiled = compile_recursive_wave(draft=draft, **kwargs)
        assert len(compiled.execution_plan.tasks) == count
        assert len([c for c in compiled.execution_plan.tasks if c.capability.capability_key.endswith('.sample')]) == len(roots)
        assert all(record.identity.object_id == key.removeprefix('external.') for key,record in records)
        if tranche == 'TRAINING':
            assert sum(l.consumer_input_id == 'controls-product' for l in draft.links) == 17
        assert sum(l.consumer_input_id == 'sample-positions' for l in draft.links) == len(roots)
        with pytest.raises(ValueError): compile_recursive_wave(draft=replace(draft, links=draft.links[1:]), **kwargs)
        bad = replace(draft, external_inputs=draft.external_inputs[:-1])
        with pytest.raises(ValueError): compile_recursive_wave(draft=bad, **kwargs)


def test_public_preparation_derives_complete_new_allocation(tmp_path):
    from empirical_lawhood.execution.experiment_preparation import ExecutionSelection
    design, selection, provenance, _ = setup(tmp_path)
    campaign = campaign_fixture()[0].campaign
    spec = experiment.BridgeSpecification('test.spec.sci02d', design.identity, selection.identity, provenance.identity,
        ObjectIdentity.from_record(campaign.campaign_id, campaign), 'TRAINING')
    records = dict(design=design, selection=selection, provenance=provenance, campaign=campaign)
    source = ObjectIdentity('test.source', 'empirical-lawhood/testing/source', '1.0.0', 'c'*64)
    bound = experiment.bind_inputs(spec, records)
    result = experiment.prepare(spec, scientific_inputs=bound.scientific_inputs,
        execution=ExecutionSelection(environment_id='environment.test', source_snapshot=source, output_root=str(tmp_path), workers=4),
        method_inputs=bound.method_inputs)
    assert result.executable and result.census.native_effect_count == 16
    assert len(result.draft.operations) == 34 and len(result.allocation.units) == 16
    experiment.validate_instance(specification=spec, allocation=result.allocation, draft=result.draft, source_records=result.design_records)
    with pytest.raises(ValueError): experiment.bind_inputs(spec, {**records, 'selection': replace(selection, seed_sha256='d'*64)})


def test_historical_v1_instance_accepts_only_the_exact_original_output_allowance(tmp_path):
    design, selection, provenance, _ = setup(tmp_path)
    design = replace(design, protocol_document_sha256='cb2bb1a3be6fcf05be70d74cce7e7ef25edf34249b8333530ef7bfeb7d89587b')
    selection = replace(selection, design=design)
    campaign = campaign_fixture()[0].campaign
    def operands(design, selection):
        spec = experiment.BridgeSpecification('test.historical.sci02d',design.identity,selection.identity,provenance.identity,
            ObjectIdentity.from_record(campaign.campaign_id,campaign),'TRAINING')
        records = dict(design=design,selection=selection,provenance=provenance,campaign=campaign)
        current, _ = experiment.lower(spec,records)
        sources = tuple((pin.object_id,records[key]) for key,(_,pin) in experiment.expected_records(spec).items())
        return current, dict(specification=spec,allocation=experiment.allocation_for(selection,'TRAINING'),source_records=sources)
    current, kwargs = operands(design,selection)
    historical = replace(current, operations=tuple(replace(op, resource_budget=replace(op.resource_budget,output_bytes=192*1024**2)) for op in current.operations))
    experiment.validate_instance(draft=current,**kwargs)
    experiment.validate_instance(draft=historical,**kwargs)
    assert all(op.resource_budget.output_bytes==384*1024**2 for op in experiment.lower(kwargs['specification'],
        dict(design=design,selection=selection,provenance=provenance,campaign=campaign))[0].operations)
    for changed in (replace(historical,operations=(current.operations[0],*historical.operations[1:])),
        replace(historical,operations=tuple(replace(op,resource_budget=replace(op.resource_budget,output_bytes=192*1024**2+1)) for op in historical.operations)),
        replace(historical,operations=(replace(historical.operations[0],resource_budget=replace(historical.operations[0].resource_budget,memory_bytes=1024)),*historical.operations[1:]))):
        with pytest.raises(ValueError,match='complete tranche'):
            experiment.validate_instance(draft=changed,**kwargs)
    other_design=replace(design,protocol_document_sha256='f'*64)
    other, other_kwargs=operands(other_design,replace(selection,design=other_design))
    other=replace(other,operations=tuple(replace(op,resource_budget=replace(op.resource_budget,output_bytes=192*1024**2)) for op in other.operations))
    with pytest.raises(ValueError,match='complete tranche'):
        experiment.validate_instance(draft=other,**other_kwargs)


def test_frozen_fit_matches_independent_covariance_and_never_uses_reference(tmp_path):
    design, selection, provenance, _ = setup(tmp_path)
    roots = experiment.roots_for(selection, 'TRAINING')
    config = binding.make_config(design, selection.identity, roots, 'fit', provenance.identity)
    rng = np.random.default_rng(871)
    parents, arrays, blocks = {}, {}, []
    for root in roots:
        c = binding.make_config(design, selection.identity, (root,), 'assess', provenance.identity)
        identity = ObjectIdentity('test.assess.'+str(root.ordinal), BridgeProduct.SCHEMA, '1.0.0', 'e'*64)
        parents[c.node_id] = SimpleNamespace(config=c, identity=identity, disposition='AVAILABLE')
        z = rng.normal(size=(2,2,256,5)); z[..., 0] += 1.7*z[...,1]-.9*z[...,3]
        arrays[c.node_id] = {'series': z}
        b = z[0].reshape(2,8,32,5).mean(axis=2)
        blocks.extend(b-b.mean(axis=1,keepdims=True))
    expected = np.vstack(blocks).T@np.vstack(blocks)/(16*2*7)
    result, frozen = science.fit(config, parents, arrays)
    np.testing.assert_allclose(result.arrays['covariance'], expected, atol=1e-14)
    np.testing.assert_allclose(np.array(frozen.coefficients[2], dtype=float), np.linalg.solve(
        expected[1:,1:]+.01*np.max(np.diag(expected)[1:])*np.eye(4),expected[1:,0]), atol=1e-14)
    assert frozen.sampling_fractions[0] == 1 and frozen.coefficients[0] == (Decimal(0),)*4
    with pytest.raises(ValueError): science.fit(config, dict(list(parents.items())[:-1]), arrays)


def test_native_receipt_recovery_and_compiler_shards(tmp_path, monkeypatch):
    from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge import native, sampling
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_science import Computation
    from empirical_lawhood.domains.matrix.matrix_storage_codecs import MATRIX_STORAGE_CODECS
    from empirical_lawhood.science.records.decoding import decode_canonical_bytes
    from empirical_lawhood.execution.execution import WorkerInputBinding, WorkerInputKind, WorkerOutputPort
    from tests.test_matrix_parameter_history import publish, object_id
    from tests.runtime_platform.test_native_subwork import _plane
    from tests.matrix_native_invocation_support import prepared_native_store
    design, selection, provenance, fitted = setup(tmp_path)
    root = selection.root('CONFIRMATION', 0)
    config = binding.make_config(design, selection.identity, (root,), 'sample', provenance.identity, fitted)
    declaration = next(d for d in binding.operation_declarations() if d.capability_key.endswith('.sample'))
    plane = _plane(tmp_path/'native', binary_codecs=MATRIX_STORAGE_CODECS)
    source = (config, design, root, provenance, *selection.streams(root.bank, root.ordinal))
    records = tuple((config.config_id if value is config else value.identity.object_id, value) for value in source)
    manifests = tuple(publish(plane, name, record.SCHEMA, record.canonical_bytes()) for name,record in records)
    def context():
        ports = tuple(plane.open(m,binding=WorkerInputBinding(m.logical.logical_artifact_id, m.materialization.materialization_id,
            m.logical.payload_schema,m.logical.media_type,m.materialization.size_bytes,binding.VISIBILITY,binding.ACCESS,WorkerInputKind.EXTERNAL),
            maximum_bytes=m.materialization.size_bytes) for m in manifests)
        outputs = tuple(WorkerOutputPort(config.node_id+'.'+p.output_id,p.payload_schema,p.profile,p.media_type,config.node_id+'.'+p.output_id)
            for p in declaration.outputs)
        return SimpleNamespace(input_ports=ports,output_ports=outputs,task_id=config.node_id,
            config=SimpleNamespace(config_id=config.config_id,content_sha256=config.fingerprint()),resource_budget=binding.BUDGET,
            permissions=binding.PERMISSIONS,outcome_access=binding.ACCESS)
    calls = []
    def disclosed_fixture(*args,**kwargs):
        calls.append(1)
        return Computation({'positions': np.zeros((2,3),dtype='<f8'), 'gradients':np.ones((2,3),dtype='<f8'), 'test':np.zeros(1,dtype='<f8')})
    monkeypatch.setattr(sampling,'acquire',disclosed_fixture)
    runner = declaration.provider_factory().runner_factory()
    store,ctx,_ = prepared_native_store(plane,runner=runner,context=context(),manifests=manifests,provenance=provenance,
        execution_plan=object_id('test.sci02d.plan'),native_work_preparer=native.prepare_native_work,
        run_id='test.sci02d.run',attempt_id='test.sci02d.run.sample.attempt-001',visibility=binding.VISIBILITY,access=binding.ACCESS)
    first = runner.execute_with_native_subwork(ctx,store)
    product = decode_canonical_bytes(next(o.payload for o in first.outputs if o.output_id.endswith('.product')),BridgeProduct,maximum_bytes=None)
    assert product.native[0].completion.output_ids == ('arrays','checkpoint','gradients','positions')
    assert len(product.shards) == 2 and calls == [1]
    def forbidden(*args,**kwargs): pytest.fail('completed receipt recovery entered native acquisition')
    monkeypatch.setattr(sampling,'acquire',forbidden)
    recovered = runner.execute_with_native_subwork(context(),store)
    assert [(o.output_id,o.payload) for o in first.outputs] == [(o.output_id,o.payload) for o in recovered.outputs]


def test_reference_outputs_fit_existing_bounded_array_contracts(tmp_path):
    from empirical_lawhood.adapters.matrix_storage.matrix_array_io import decode_matrix_arrays
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_science import Computation
    design, selection, provenance, fitted = setup(tmp_path)
    config = binding.make_config(design,selection.identity,(selection.root('REFERENCE',0),),'sample',provenance.identity,fitted)
    n, nodes = design.production_steps*4//design.sample_stride,9
    # Full dimensions, disclosed zero values: this checks storage, not science.
    data = {'positions':np.zeros((2,2,2,nodes,n,96),dtype='<f8'), 'gradients':np.zeros((2,2,2,nodes,n,96),dtype='<f8'),
        'witnesses':np.zeros((96,7,2,2,nodes,96),dtype='<f8'), 'observables':np.zeros((2,2,2,nodes,n,5),dtype='<f8')}
    ids = {key:'test.reference.'+key for key in ('arrays','positions','gradients')}
    payloads,operands = binding.pack(config,Computation(data),ids)
    assert sum(map(len,payloads.values())) <= binding.BUDGET.output_bytes
    for key,raw in payloads.items():
        assert len(raw) <= binding.MAXIMUM_MATRIX_ARRAY_BYTES
        decoded = dict(decode_matrix_arrays(raw,operands[key]))
        assert all(np.array_equal(value,data[name]) for name,value in decoded.items())


def test_reference_output_allowance_covers_native_and_parent_publication(tmp_path):
    from empirical_lawhood.execution.local.native_subwork_ipc import NativeSubworkPipeService
    design, _, _, _ = setup(tmp_path)
    # Bound full, uncompressed selected data; compressed zero fixtures hide
    # the cost of retaining both the native and ordinary parent copies.
    samples = design.production_steps * design.reference_multiplier // design.sample_stride
    warmup = design.burn_steps * design.reference_multiplier // design.sample_stride
    witnesses = (design.burn_steps + design.production_steps) * design.reference_multiplier // 1024
    chains = 2 * 2 * 2 * 9
    array_bytes = 8 * (2 * chains * samples * 96 + chains * samples * 6
        + chains * warmup + witnesses * 7 * 2 * 2 * 9 * 96 + samples + witnesses + 9)
    # Canonical records, archive/member headers and exact RNG custody have
    # an additional conservative allowance in each publication.
    copy_bound = array_bytes + 2 * binding.MAX_RECORD
    declaration = next(d for d in binding.operation_declarations() if d.capability_key.endswith('.sample'))
    meter = object.__new__(NativeSubworkPipeService)
    meter._output_budget = declaration.manifest().resource_ceiling.output_bytes
    meter.output_bytes = copy_bound
    meter.ordinary_output_bytes = 0
    assert meter.account_ordinary_output_bytes(copy_bound)
    remaining = meter._output_budget - meter.output_bytes - meter.ordinary_output_bytes
    assert not meter.account_ordinary_output_bytes(remaining + 1)


def test_original_array_custody_joins_the_named_shard_and_refuses_cross_wiring(tmp_path):
    from empirical_lawhood.api.matrix_native_read_custody import _array
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import Sci02Arrays
    from empirical_lawhood.adapters.matrix_storage.matrix_array_io import encode_matrix_arrays
    from empirical_lawhood.science.identity.references import ArtifactIdentity
    from empirical_lawhood.domains.matrix.matrix_storage_codecs import MATRIX_STORAGE_CODECS
    from tests.runtime_platform.test_native_subwork import _plane
    from tests.test_matrix_parameter_history import publish
    plane = _plane(tmp_path/'shards',binary_codecs=MATRIX_STORAGE_CODECS)
    from hashlib import sha256
    operands,manifests = {},{}
    for label,value in (('arrays',0.),('positions',1.),('gradients',2.)):
        raw,members = encode_matrix_arrays({label:np.array([value],dtype='<f8')})
        manifest = publish(plane,'test.shard.'+label,binding.MATRIX_ARRAY_SCHEMA,raw)
        artifact = ArtifactIdentity(manifest.logical.logical_artifact_id,'scientific-product',binding.MATRIX_ARRAY_SCHEMA,
            sha256(raw).hexdigest(),'application/x-npz',len(raw))
        operands[label] = Sci02Arrays('test.'+label,artifact,members)
        manifests[label] = manifest
    receipt = SimpleNamespace(output_logical_artifacts=tuple(m.logical for m in manifests.values()),
        output_materializations=tuple(m.materialization for m in manifests.values()))
    products = {'receipts':{'test.task':receipt},'outputs':{m.logical.logical_artifact_id:m for m in manifests.values()}}
    tasks = {'test.task':SimpleNamespace(outputs=tuple(SimpleNamespace(output_id='test.task.'+label,
        logical_artifact_id=m.logical.logical_artifact_id) for label,m in manifests.items()))}
    for label,operand in operands.items(): _array(products,tasks,'test.task',operand,label=label)
    with pytest.raises(PermissionError): _array(products,tasks,'test.task',operands['positions'],label='gradients')
    with pytest.raises(PermissionError): _array(products,tasks,'test.task',operands['positions'])


def test_confirmation_keeps_error_and_uncertainty_failures_in_complete_denominator(tmp_path):
    design,selection,provenance,fitted = setup(tmp_path)
    roots = experiment.roots_for(selection,'CONFIRMATION')
    config = binding.make_config(design,selection.identity,roots,'confirm',provenance.identity,fitted)
    parents,arrays = {},{}
    for root in roots:
        c = binding.make_config(design,selection.identity,(root,),'assess',provenance.identity,fitted)
        parents[c.node_id] = SimpleNamespace(config=c,disposition='AVAILABLE')
        if root.bank == 'CONFIRMATION':
            e = (root.ordinal-31.5)/1000
            point = np.array([.2+e,.2+.5*e,.23+.1*e])
            estimate = np.broadcast_to(point,(2,2,3)).copy()
            estimate[1] -= .003
            estimate[:,0] += .005; estimate[:,1] -= .005
        else:
            estimate = np.full((2,2,3),.2+(root.ordinal-3.5)*.00001)
        arrays[c.node_id] = {'estimates':estimate,'prefix_estimates':estimate,'five_node_estimates':estimate,
            'prefix_half_widths':np.ones((2,3)), 'doubled_block_half_widths':np.ones((2,3))*1.1,
            'chronological_half_estimates':np.stack((estimate+.001,estimate-.001)),
            'correlation_diagnostics':np.broadcast_to(np.array([1.,256.,1.]),(2,2,3,2,3)).copy()}
    result = science.confirm(config,parents,arrays)
    np.testing.assert_allclose(result.arrays['variance_ratios'],[1,.25,.01],atol=1e-12)
    np.testing.assert_allclose(result.arrays['bias_half'][0],[0,0,.03],atol=1e-12)
    assert np.array_equal(result.arrays['coverage_counts'],[64,64,64])
    assert np.array_equal(result.arrays['individual_sampling_precision_counts'],[0,0,0])
    assert 'PAIRED_TARGET_ACCURACY_UNRESOLVED' in result.reasons
    assert 'NUMERICAL_ALLOWANCE_UNRESOLVED_OR_EXCEEDED' in result.reasons
    assert 'PREPARATION_ALLOWANCE_UNRESOLVED_OR_EXCEEDED' in result.reasons
    assert result.disposition == 'PARTIAL' and dict(result.measurements)['confirmation.complete_roots'] == 64
    with pytest.raises(ValueError,match='full original banks'):
        science.confirm(config,dict(list(parents.items())[:-1]),arrays)


def test_public_input_constructor_commits_new_bank_without_native_contact(tmp_path, monkeypatch):
    import secrets
    from empirical_lawhood.api import matrix_sci02d as api, recursive_authoring
    from empirical_lawhood.storage import numerical_provenance
    from empirical_lawhood.science.records.decoding import decode_canonical_bytes
    from empirical_lawhood.design.experiment_inputs import ExperimentFileInputSelection
    from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge import sampling
    design,selection,provenance,_ = setup(tmp_path)
    monkeypatch.setattr(secrets,'token_hex',lambda size:'c'*64)
    monkeypatch.setattr(numerical_provenance,'capture_numerical_provenance',lambda **kwargs:provenance)
    # Disclosed canonical source placeholder, confined to the constructor test.
    monkeypatch.setattr(recursive_authoring,'implementation_binding',lambda path:selection)
    def forbidden(*args,**kwargs): pytest.fail('input construction entered native science')
    monkeypatch.setattr(sampling,'acquire',forbidden)
    protocol = tmp_path/'test-protocol.md'; protocol.write_bytes(b'EXPOSED SOFTWARE CONTROL ONLY\n')
    campaign = tmp_path/'campaign.json'; campaign.write_bytes(campaign_fixture()[0].campaign.canonical_bytes())
    result = api.create_training_inputs(campaign_path=campaign,protocol_path=protocol,project_root=tmp_path,output_directory=tmp_path/'inputs')
    sources = decode_canonical_bytes((tmp_path/'inputs/sources.json').read_bytes(),ExperimentFileInputSelection,maximum_bytes=None)
    assert sources.files == () and {b.key for b in sources.bindings} == {'design','selection','provenance','campaign'}
    assert result['new_native_contact_cap'] == 16 and result['operations'] == 34
    with pytest.raises(FileExistsError):
        api.create_training_inputs(campaign_path=campaign,protocol_path=protocol,project_root=tmp_path,output_directory=tmp_path/'inputs')
