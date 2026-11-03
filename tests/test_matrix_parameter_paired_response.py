# SPDX-License-Identifier: MPL-2.0
"""Exposed paired response and declared nine-setting conformance, never qualification."""

from dataclasses import replace
from decimal import Decimal as D
from itertools import product
import os
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS

from empirical_lawhood.adapters.methods.matrix_parameter_response import science as original_science
from empirical_lawhood.adapters.methods.matrix_parameter_response import paired_science as science
from empirical_lawhood.adapters.methods.matrix_parameter_response import paired_independent as independent
from empirical_lawhood.adapters.methods.matrix_parameter_response.paired_records import (
    DISPOSITION_WITHOUT_STANDARD, MatrixPairedNumericalStandard, MatrixParameterPairedDesign,
    MatrixPairedFunctionalDiscrepancy, identity, source_for,
)
from empirical_lawhood.adapters.methods.matrix_parameter_response.paired_grid import declare_grid
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
from tests.test_matrix_parameter_response import retained as original_retained, selected_case, templates
from tests.test_matrix_parameter_factor import absent_case


@pytest.fixture(scope='module')
def paired_case():
    retained = original_retained.__wrapped__()
    original,parameter,supply,factor,fp,fa,model = selected_case(retained)
    root = Path(os.environ['MATRIX_PARAMETER_RESPONSE_RETAINED_HISTORY'])
    history_raw = next((root/'runs/test.e4.run/native-subwork').rglob('outputs/arrays')).read_bytes()
    history = decode_matrix_arrays(history_raw,supply.product.arrays)
    factors = decode_matrix_arrays(retained[2]['factor-raw'],fp.arrays)
    origin_raw,origin = original_science.origin_record(original,history,factors,templates(),fp,
        artifact_id='software.paired.common-origin-arrays')
    d = origin.design
    fine = replace(d.coordinate.fine_view,view_id='software.paired.fine-view',rng_algorithm=d.view.rng_algorithm,
        rng_version=d.view.rng_version,stream_derivation_rule_id=d.view.stream_derivation_rule_id)
    design = MatrixParameterPairedDesign('software.paired.design',origin,fine)
    source = source_for(original,design,source_id='software.paired.source',provenance=original.provenance)
    raw,forecast = science.forecast(design,decode_matrix_arrays(origin_raw,origin.arrays),model,
        artifact_id='software.paired.forecast-arrays')
    return (source,original,parameter,supply,factor,fp,fa,model),history_raw,retained[2]['factor-raw'],origin_raw,raw,forecast


@pytest.mark.held
def test_paired_public_forecast_same_origin_clocks_and_cold_witnesses(paired_case,monkeypatch):
    case,_,_,origin_raw,raw,forecast = paired_case
    source,*_,model = case
    design = source.design
    past = decode_matrix_arrays(origin_raw,design.common_origin.arrays)
    predicted = decode_matrix_arrays(raw,forecast.arrays)
    assert len(predicted) == 23 and all(disposition == 'AVAILABLE' for _,disposition,_ in forecast.dispositions)
    assert design.native_origin_tick('FINE') == 2*design.native_origin_tick('PRIMARY')
    assert tuple(h*design.fine_view.timestep for h in design.horizon_steps('FINE')) == tuple(h*design.primary.view.timestep for h in design.horizon_steps('PRIMARY'))
    def blocked(*args,**kwargs):
        pytest.fail('cold paired reproof entered producer/RNG/eigensolver')
    monkeypatch.setattr(science,'forecast_values',blocked)
    monkeypatch.setattr(np.random,'Generator',blocked)
    monkeypatch.setattr(np.linalg,'eigh',blocked)
    independent.verify_forecast(design,past,predicted,forecast)
    changed = dict(predicted)
    changed['fine_full_coupled'] = changed['fine_full_coupled'].copy()
    changed['fine_full_coupled'][0,0,0] += .01
    with pytest.raises(ValueError):
        independent.verify_forecast(design,past,changed,forecast)
    assert identity(model) == forecast.model


@pytest.mark.held
def test_complete48_paired_branches_weighted_noise_full192_and_pulse(paired_case):
    case,_,_,origin_raw,*_ = paired_case
    source = case[0]
    past = decode_matrix_arrays(origin_raw,source.design.common_origin.arrays)
    census = science.branch_census(source)
    assert len(census) == 48 and {b[0] for b in census} == {'FINE','PRIMARY'}
    panels = science.noise_panels(source)
    for panel in panels.values():
        independent.verify_noise_pair(source.design,panel['PRIMARY'],panel['FINE'],panel['BRIDGE'])
    for view in ('PRIMARY','FINE'):
        branch = next(b for b in census if b[0] == view and b[-1] == 'PLUS')
        values = science.native_branch(source,past,branch,panels[branch[2].panel_id])
        count = source.design.horizon_steps(view)[-1]
        assert values['positions'].shape == values['momenta'].shape == (count+1,2,3,4,4)
        assert np.array_equal(values['positions'][0],past['positions'][-1])
        reference = independent.reference_branch_parameters(member=source.design.primary.member,
            alpha_tilde=(source.design.primary.alpha_x,source.design.primary.alpha_y),view=source.design.view(view),
            positions=past['positions'][-1],momenta=past['momenta'][-1],force=past['forces'][source.design.primary.actions.index(branch[3])],
            amplitude=float(branch[3].amplitude),pulse_steps=branch[3].pulse_steps*source.design.multiplier(view),noise=values['noise'])
        for name in ('positions','momenta'):
            np.testing.assert_allclose(values[name],reference[name],rtol=0,atol=1e-9)
    panel = panels[source.root.streams[0].panel_id]
    wrong = panel['BRIDGE'].copy();wrong[0,0,0,0,0] += 1
    with pytest.raises(ValueError):
        independent.verify_noise_pair(source.design,panel['PRIMARY'],panel['FINE'],wrong)


@pytest.mark.parametrize('kind',('no-standard','positive','negative','weak','failed-reference'))
@pytest.mark.held
def test_numerical_standard_is_required_and_outcomes_remain_distinct(paired_case,kind):
    design = paired_case[0][0].design
    row = MatrixPairedFunctionalDiscrepancy('panel.test','action.test',D('.01'),(D('.001'),)*48,D('.001'),False)
    if kind == 'no-standard':
        assert independent._numerical_disposition(design,(row,),True) == (None,DISPOSITION_WITHOUT_STANDARD)
        return
    standard = MatrixPairedNumericalStandard('software.paired.standard',design.primary.receiver,
        identity(design.common_origin),D('.01'),D('.01'))
    design = replace(design,numerical_standard=standard)
    if kind == 'negative':
        row = replace(row,receiver_absolute_errors=(D('.1'),)*48)
    elif kind == 'weak':
        row = replace(row,relative_curve_error=None,weak_response=True)
    expected = {'positive':'COMPATIBLE_WITH_FROZEN_EMPIRICAL_STANDARD','negative':'VIOLATED_FROZEN_EMPIRICAL_STANDARD',
        'weak':'UNRESOLVED_WEAK_FUNCTIONAL_DENOMINATOR','failed-reference':'UNASSESSED_FAILED_NATIVE_REFERENCE'}[kind]
    assert independent._numerical_disposition(design,(row,),kind != 'failed-reference') == (identity(standard),expected)


@pytest.mark.parametrize('defect',('duplicate-controls','duplicate-discrepancies','duplicate-scores',
    'wrong-control-view','wrong-transition-count','foreign-receiver','inconsistent-panel-role',
    'different-view-horizon','duplicate-score-view','foreign-discrepancy-panel','inconsistent-physical-clock',
    'invalid-control-id','noninteger-state-denominator','nonpositive-physical-horizon'))
@pytest.mark.held
def test_retained_paired_assessment_refuses_census_substitution_without_native(defect):
    """Admission changes only: re-use an immutable completed exposed assessment."""
    import json
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.adapters.methods.matrix_parameter_response.paired_records import MatrixParameterPairedAssessment
    selected = os.environ.get('MATRIX_PARAMETER_PAIRED_COMPLETED_FIXTURE')
    if not selected:
        pytest.skip('exact completed paired fixture required; this test never acquires one')
    path = next(p for p in Path(selected).rglob('product.json')
        if json.loads(p.read_bytes()).get('schema') == MatrixParameterPairedAssessment.SCHEMA)
    original = path.read_bytes()
    a = decode_canonical_bytes(original,MatrixParameterPairedAssessment,maximum_bytes=None)
    assert a.canonical_bytes() == original
    with pytest.raises(ValueError):
        if defect == 'duplicate-controls':
            replace(a,controls=(a.controls[0],)*48)
        elif defect == 'duplicate-discrepancies':
            replace(a,functional_discrepancies=(a.functional_discrepancies[0],)*len(a.functional_discrepancies))
        elif defect == 'duplicate-scores':
            replace(a,scores=(a.scores[0],)*len(a.scores))
        elif defect == 'wrong-control-view':
            c = a.controls[0]
            replace(a,controls=(replace(c,view='PRIMARY' if c.view == 'FINE' else 'FINE'),*a.controls[1:]))
        elif defect == 'wrong-transition-count':
            replace(a,controls=(replace(a.controls[0],denominator_steps=a.controls[0].denominator_steps+1),*a.controls[1:]))
        elif defect in ('foreign-receiver','inconsistent-panel-role','different-view-horizon'):
            view,score = a.scores[0]
            changes = {'foreign-receiver':{'receiver_index':48},
                'inconsistent-panel-role':{'panel_role':'INDEPENDENT_FUTURE' if score.panel_role == 'COMMON_NOISE_PANEL' else 'COMMON_NOISE_PANEL'},
                'different-view-horizon':{'horizon_step':score.horizon_step+1}}[defect]
            replace(a,scores=((view,replace(score,**changes)),*a.scores[1:]))
        elif defect == 'duplicate-score-view':
            view,score = a.scores[0]
            replace(a,scores=(('PRIMARY' if view == 'FINE' else 'FINE',score),*a.scores[1:]))
        elif defect in ('foreign-discrepancy-panel','inconsistent-physical-clock'):
            row = a.functional_discrepancies[0]
            changes = {'panel_id':'panel.foreign'} if defect == 'foreign-discrepancy-panel' else {'physical_horizon':row.physical_horizon+D('.0001')}
            replace(a,functional_discrepancies=(replace(row,**changes),*a.functional_discrepancies[1:]))
        elif defect == 'invalid-control-id':
            replace(a.controls[0],control_id='control.foreign')
        elif defect == 'noninteger-state-denominator':
            replace(a.controls[0],denominator_real_coordinates=D(192))
        else:
            replace(a.functional_discrepancies[0],physical_horizon=D(0))
    assert path.read_bytes() == original


def grid_allocation(groups):
    _,parameter,*_ = absent_case()
    base = parameter.coordinate
    levels = ((D('.4'),D('.5'),D('.6')),(D('1'),D('1.5'),D('2')),(D('.1'),D('.2'),D('.3')))
    settings = tuple(product(*((lo,hi) for lo,_,hi in levels))) + (tuple(center for _,center,_ in levels),)
    coordinates = []
    for i,(bath,friction,coupling) in enumerate(settings):
        member = replace(base.member,member_id=f'software.grid.member.{i}',cross_coupling_gamma=coupling)
        p = replace(base.primary_view,view_id=f'software.grid.primary.{i}',bath_temperature=bath,friction_gamma=friction)
        f = replace(base.fine_view,view_id=f'software.grid.fine.{i}',bath_temperature=bath,friction_gamma=friction)
        coordinates.append(replace(base,coordinate_id=f'software.grid.coordinate.{i}',member=member,primary_view=p,fine_view=f))
    roots = []
    for group in range(groups):
        streams = tuple(replace(s,digest_sha256=f'{100000+group*16+i:032x}'+'0'*32) for i,s in enumerate(parameter.root.streams))
        for c in coordinates:
            r = replace(parameter.root.root,root_id=f'software.grid.root.{group:03d}.{c.coordinate_id.rsplit(".",1)[1]}',
                independent_group_id=f'software.grid.group.{group:03d}',coordinate_id=c.coordinate_id,regime_id='regime.'+c.coordinate_id)
            roots.append(replace(parameter.root,root=r,coordinate=coordinate_identity(c),streams=streams))
    return replace(parameter.allocation,allocation_id=f'software.grid.allocation.{groups}',coordinates=tuple(coordinates),roots=tuple(roots)),levels


@pytest.mark.parametrize(('phase','groups'),(('EXPOSED_SOFTWARE',2),('DEVELOPMENT',32),('REVISION_CALIBRATION',64),('CONFIRMATION',64)))
def test_declared_nine_setting_complete_grid_group_and_unentered_denominator(phase,groups):
    allocation,levels = grid_allocation(groups)
    grid = declare_grid(allocation,grid_id='software.grid.'+phase.lower(),phase=phase,levels=levels,axis_scales=('LINEAR',)*3)
    assert grid.requested_independent_groups == groups
    assert grid.requested_coordinate_cases == 9*groups
    census = grid.unentered_census(allocation)
    assert len(census.cells) == 18*groups and not census.complete_independent_groups
    assert all(c.disposition == 'UNENTERED' for c in census.cells)
    assert census.requested_independent_groups == groups


@pytest.mark.parametrize('defect',('duplicate-root-view','false-complete-group','different-view-coordinate',
    'different-view-group','wrong-root-count','wrong-group-count','foreign-assessment-schema'))
def test_canonical_grid_census_refuses_substitution(defect):
    allocation,levels = grid_allocation(2)
    grid = declare_grid(allocation,grid_id='software.grid.canonical',phase='EXPOSED_SOFTWARE',levels=levels,axis_scales=('LINEAR',)*3)
    census = grid.unentered_census(allocation)
    with pytest.raises(ValueError):
        if defect == 'duplicate-root-view':
            changed = replace(census.cells[0],root_id=census.cells[2].root_id,coordinate=census.cells[2].coordinate)
            replace(census,cells=(changed,*census.cells[1:]))
        elif defect == 'false-complete-group':
            replace(census,complete_independent_groups=(grid.matched_groups[0][0],))
        elif defect == 'different-view-coordinate':
            changed = replace(census.cells[0],coordinate=census.cells[2].coordinate)
            replace(census,cells=(changed,*census.cells[1:]))
        elif defect == 'different-view-group':
            changed = replace(census.cells[0],independent_group_id=grid.matched_groups[1][0])
            replace(census,cells=(changed,*census.cells[1:]))
        elif defect == 'wrong-root-count':
            replace(census,requested_roots=True)
        elif defect == 'wrong-group-count':
            replace(census,requested_independent_groups=1)
        else:
            replace(census.cells[0],disposition='COMPLETED',assessment=census.allocation)


@pytest.mark.parametrize('defect',('false-center','missing-coordinate','missing-root','changed-preparation','unmatched-noise','wrong-stage-count'))
def test_nine_setting_grid_refuses_design_or_matching_substitution(defect):
    allocation,levels = grid_allocation(2)
    grid = declare_grid(allocation,grid_id='software.grid.refusals',phase='EXPOSED_SOFTWARE',levels=levels,axis_scales=('LINEAR',)*3)
    with pytest.raises(ValueError):
        if defect == 'false-center':
            replace(grid,levels=((D('.4'),D('.51'),D('.6')),*levels[1:]))
        elif defect == 'missing-coordinate':
            replace(grid,coordinates=grid.coordinates[:-1])
        elif defect == 'missing-root':
            changed = replace(allocation,roots=allocation.roots[:-1])
            declare_grid(changed,grid_id='software.grid.missing',phase='EXPOSED_SOFTWARE',levels=levels,axis_scales=('LINEAR',)*3)
        elif defect == 'changed-preparation':
            c = replace(allocation.coordinates[0],target_x=allocation.coordinates[0].target_x+D('.1'))
            root = replace(allocation.roots[0],coordinate=coordinate_identity(c))
            changed = replace(allocation,coordinates=(c,*allocation.coordinates[1:]),roots=(root,*allocation.roots[1:]))
            declare_grid(changed,grid_id='software.grid.changed',phase='EXPOSED_SOFTWARE',levels=levels,axis_scales=('LINEAR',)*3)
        elif defect == 'unmatched-noise':
            r = allocation.roots[0]
            stream = replace(r.streams[0],digest_sha256=f'{r.streams[0].effective_seed+9999:032x}'+'0'*32)
            changed = replace(allocation,roots=(replace(r,streams=(stream,*r.streams[1:])),*allocation.roots[1:]))
            declare_grid(changed,grid_id='software.grid.noise',phase='EXPOSED_SOFTWARE',levels=levels,axis_scales=('LINEAR',)*3)
        else:
            replace(grid,phase='CONFIRMATION')


def test_grid_protected_actual_transfer_regime_requires_separate_settings():
    allocation,levels = grid_allocation(2)
    grid = declare_grid(allocation,grid_id='software.grid.reserve',phase='EXPOSED_SOFTWARE',levels=levels,axis_scales=('LINEAR',)*3)
    c = allocation.coordinates[0];m,p = c.member,c.primary_view
    physical = (m.mass_x,m.mass_y,m.cross_coupling_gamma,m.beta_rule,p.bath_temperature,p.friction_gamma,c.target_x,c.target_y)
    with pytest.raises(ValueError,match='protected'):
        grid.validate_transfer_reserve(allocation,SimpleNamespace(regimes=(SimpleNamespace(physical_parameters=physical),)))


@pytest.mark.held
def test_paired_factories_compiler_committed_roles_and_sourcefree_config(paired_case):
    from empirical_lawhood.adapters.methods.matrix_parameter_response import paired_operation_bindings as binding
    from empirical_lawhood.runtime.capabilities import CapabilityRegistry
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
    case = paired_case[0];source = case[0]
    factories = binding.operation_factories()
    assert len(factories) == 4 and sum(f.registration.native_effect for f in factories) == 1
    cfg = binding.MatrixParameterPairedForecastConfig(f'config.{binding.NAMESPACE}.{source.root.root_id}.forecast',
        source.design,source.root.root_id,source.root.independent_group_id,source.root.clock_id)
    assert b'"seed"' not in cfg.canonical_bytes() and b'"streams"' not in cfg.canonical_bytes()
    assert not hasattr(binding.MatrixParameterPairedRunner('forecast'),'execute_with_native_subwork')
    registry = CapabilityRegistry('registry.software.paired',tuple(sorted((f.manifest for f in factories),key=lambda m:m.registry_id)))
    draft = binding.development_draft((case,),draft_id='software.paired.compile')
    compiled = compile_recursive_wave(draft=draft,registrations=binding.operation_registrations(),registry=registry,
        implementation_commit=source.provenance.observed_git_head,output_codecs=binding.output_codecs())
    assert len(compiled.execution_plan.tasks) == 4
    future_config = next(c.record for c in compiled.config_inputs if getattr(c.record,'operation',None) == 'futures')
    future_registration = next(r for r in binding.operation_registrations() if r.native_effect)
    assert len(set(future_registration.native_effect_slot_ids(future_config))) == 48
    for defect in ('system','views','forecast-role','incomplete-roster'):
        with pytest.raises(ValueError):
            if defect == 'system':
                changed = replace(draft,development_study=replace(draft.development_study,system=identity(source.design)))
            elif defect == 'views':
                changed = replace(draft,development_study=replace(draft.development_study,numerical_view_ids=()))
            elif defect == 'forecast-role':
                link = next(l for l in draft.links if l.consumer_input_id == 'forecast' and l.consumer_node_id.endswith('.futures'))
                changed = replace(draft,links=tuple(replace(l,scientific_role='SOURCE') if l == link else l for l in draft.links))
            else:
                invalid = replace(source,requested_roots=2)
                binding.development_root((invalid,),study_id='study.software.incomplete')
                continue
            compile_recursive_wave(draft=changed,registrations=binding.operation_registrations(),registry=registry,
                implementation_commit=source.provenance.observed_git_head,output_codecs=binding.output_codecs())


def _cold_completed_paired(root,tmp_path,monkeypatch):
    """Actual ordinary+48 child receipt/physical bytes before independent reproof."""
    import json
    import shutil
    from hashlib import sha256
    from empirical_lawhood.adapters.methods.matrix_parameter_response import paired_operation_bindings as binding
    from empirical_lawhood.adapters.methods.matrix_parameter_response.paired_records import (
        MatrixParameterPairedSource,MatrixParameterPairedForecast,MatrixParameterPairedNative,MatrixParameterPairedAssessment,
    )
    from empirical_lawhood.adapters.methods.matrix_parameter_response.records import MatrixParameterResponseSource
    from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterHistorySource
    from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import (
        MatrixParameterFactorSupply,MatrixParameterFactorSource,MatrixParameterFactorProduct,MatrixParameterFactorAssessment,
    )
    from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
    from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.evidence import OutcomeAccess,VisibilityCeiling
    from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
    from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
    from empirical_lawhood.runtime.native_subwork import NativeSubworkState
    from tests.runtime_platform.test_native_subwork import _plane
    def input_record(cls):
        for path in (root/'inputs').glob('*.json'):
            if json.loads(path.read_text()).get('schema') == cls.SCHEMA:
                return decode_canonical_bytes(path.read_bytes(),cls,maximum_bytes=None)
        raise ValueError('completed paired fixture lacks actual typed input')
    source = input_record(MatrixParameterPairedSource)
    original = input_record(MatrixParameterResponseSource)
    original_records = tuple(input_record(cls) for cls in (MatrixParameterHistorySource,MatrixParameterFactorSupply,
        MatrixParameterFactorSource,MatrixParameterFactorProduct,MatrixParameterFactorAssessment))
    receipts = tuple(decode_canonical_bytes(p.read_bytes(),CanonicalTaskReceipt,maximum_bytes=None)
        for p in (root/'runs').rglob('*.json') if '/receipts/' in str(p) and json.loads(p.read_text()).get('schema') == CanonicalTaskReceipt.SCHEMA)
    ordinary = tuple(r for r in receipts if r.task_id.startswith(binding.NAMESPACE))
    assert len(receipts) == 52 and len(ordinary) == 4
    records,publications = {},{}
    for r in receipts:
        for logical in r.output_logical_artifacts:
            material = next(m for m in r.output_materializations if m.logical_artifact_id == logical.logical_artifact_id)
            raw = (root/material.relative_path).read_bytes()
            assert len(raw) == material.size_bytes and sha256(raw).hexdigest() == logical.content_sha256 == material.physical_sha256
            publications[logical.logical_artifact_id] = raw
            if r in ordinary and logical.payload_schema != MATRIX_ARRAY_SCHEMA:
                records[logical.payload_schema] = raw
    for path in (root/'inputs').glob('*.npz'):
        raw = path.read_bytes()
        for a in (original.history_arrays,original.factor_arrays,source.design.common_origin.arrays.array_artifact):
            if sha256(raw).hexdigest() == a.sha256:
                publications[a.artifact_id] = raw
    supply,product = original_records[1],original_records[3]
    history = decode_matrix_arrays(publications[original.history_arrays.artifact_id],supply.product.arrays)
    factors = decode_matrix_arrays(publications[original.factor_arrays.artifact_id],product.arrays)
    def blocked(*args,**kwargs):
        pytest.fail('completed paired fixture entered producer/RNG/eigensolver/native contact')
    for target,name in ((science,'forecast'),(science,'native_branch'),(science,'noise_panel'),(np.random,'Generator'),
            (np.linalg,'eigh'),(np.linalg,'eigvalsh'),(ExternalNativeSubworkStore,'begin'),(ExternalNativeSubworkStore,'contact')):
        monkeypatch.setattr(target,name,blocked)
    classes = (MatrixParameterPairedSource,MatrixParameterPairedForecast,MatrixParameterPairedNative,MatrixParameterPairedAssessment)
    retained_native = decode_canonical_bytes(records[MatrixParameterPairedNative.SCHEMA],MatrixParameterPairedNative,maximum_bytes=None)
    last_byte = bytearray(publications[retained_native.arrays.array_artifact.artifact_id]);last_byte[-1] ^= 1
    def corrupt_last_byte(artifact):
        return bytes(last_byte) if artifact == retained_native.arrays.array_artifact else publications[artifact.artifact_id]
    with pytest.raises(ValueError):
        independent.read_retained(*(records[c.SCHEMA] for c in classes),corrupt_last_byte,
            original_inputs=(original,*original_records,history,factors))
    cold = independent.read_retained(*(records[c.SCHEMA] for c in classes),lambda a:publications[a.artifact_id],
        original_inputs=(original,*original_records,history,factors))
    assert len(cold.controls) == 48 and len(cold.functional_discrepancies) == 24 and len(cold.scores) == 11520
    assert cold.native_reference_pass and cold.numerical_disposition == DISPOSITION_WITHOUT_STANDARD
    assert cold.unchanged_e3_transfer == 'UNENTERED_FROZEN_MODEL_CALIBRATION_CALLER_REQUIRED'
    native = decode_canonical_bytes(records[MatrixParameterPairedNative.SCHEMA],MatrixParameterPairedNative,maximum_bytes=None)
    portable_path = tmp_path/'portable-paired'
    shutil.copytree(root,portable_path)
    plane = _plane(portable_path, binary_codecs=MATRIX_STORAGE_CODECS)
    contacts = ExternalNativeEffectContactStore(plane=plane,execution_plan=native.events[0].definition.parent_contact.execution_plan,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    store = ExternalNativeSubworkStore(plane=plane,parent_contacts=contacts)
    assert all(store.recover(e.definition).state is NativeSubworkState.COMPLETED for e in native.events)
    predicted = decode_matrix_arrays(publications[native.arrays.array_artifact.artifact_id],native.arrays)
    wrong = dict(predicted)
    name = source.root.streams[0].panel_id+'.bridge'
    wrong[name] = wrong[name].copy();wrong[name][0,0,0,0,0] += .1
    commitment = decode_canonical_bytes(records[MatrixParameterPairedForecast.SCHEMA],MatrixParameterPairedForecast,maximum_bytes=None)
    past = decode_matrix_arrays(publications[source.design.common_origin.arrays.array_artifact.artifact_id],source.design.common_origin.arrays)
    with pytest.raises(ValueError):
        independent.assess(source,commitment,native,past,decode_matrix_arrays(publications[commitment.arrays.array_artifact.artifact_id],commitment.arrays),
            wrong,original_inputs=(original,*original_records,history,factors))
    return cold


@pytest.mark.held
def test_actual_four_phase48_child_receipts_independent_and_portable(paired_case,tmp_path,monkeypatch):
    if selected := os.environ.get('MATRIX_PARAMETER_PAIRED_COMPLETED_FIXTURE'):
        _cold_completed_paired(Path(selected),tmp_path,monkeypatch)
        return
    import resource
    import time
    from hashlib import sha256
    from empirical_lawhood.adapters.methods.matrix_parameter_response import paired_operation_bindings as binding
    from empirical_lawhood.api.execution import _StaticInputResolver
    from empirical_lawhood.infrastructure.execution import DirectTaskExecutor,LocalScheduler
    from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
    from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
    from empirical_lawhood.infrastructure.sql import SQLiteOperationalRepository,create_catalog_engine,upgrade_catalog
    from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore,decode_artifact_manifest
    from empirical_lawhood.kernel.evidence import OutcomeAccess,VisibilityCeiling
    from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.kernel.status import OperationalStatus
    from empirical_lawhood.runtime.artifacts import ArtifactProfile,ArtifactWriteRequest
    from empirical_lawhood.runtime.capabilities import CapabilityRegistry
    from empirical_lawhood.runtime.execution import ExecutionAssuranceProfile,RunnerRegistry,VerifiedArtifactInput
    from empirical_lawhood.runtime.plans import PlanLane
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
    from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryIndex
    from tests.runtime_platform.test_native_subwork import _plane
    case,history_raw,factor_raw,origin_raw,*_ = paired_case
    source = case[0]
    records = binding.operands(*case) | {'streams.'+s.purpose_id:s for s in source.root.streams}
    by_sha = {r.fingerprint():r.canonical_bytes() for r in records.values()}
    by_sha.update({sha256(raw).hexdigest():raw for raw in (history_raw,factor_raw,origin_raw)})
    draft = binding.development_draft((case,),draft_id='software.paired.actual')
    factories = binding.operation_factories()
    registry = CapabilityRegistry('registry.software.paired.actual',tuple(sorted((f.manifest for f in factories),key=lambda m:m.registry_id)))
    compiled = compile_recursive_wave(draft=draft,registrations=binding.operation_registrations(),registry=registry,
        implementation_commit=source.provenance.observed_git_head,output_codecs=binding.output_codecs())
    by_sha.update({c.record.fingerprint():c.payload for c in compiled.config_inputs})
    plan,run = compiled.execution_plan,compiled.run_plan
    plane = _plane(tmp_path/'original', binary_codecs=MATRIX_STORAGE_CODECS)
    inputs = []
    specs = {v.logical_artifact_id:v for task in plan.tasks for v in task.external_inputs}
    for i,(aid,spec) in enumerate(sorted(specs.items())):
        raw = by_sha[spec.expected_content_sha256]
        array = spec.expected_payload_schema == MATRIX_ARRAY_SCHEMA
        published = plane.write(ArtifactWriteRequest(aid,f'inputs/input-{i:03d}'+('.npz' if array else '.json'),
            spec.expected_payload_schema,ArtifactProfile.MATRIX_ARRAY_NPZ if array else ArtifactProfile.CANONICAL_JSON,
            spec.expected_media_type,'software.parameter-paired.fixture','inputs',raw,
            VisibilityCeiling.DEVELOPMENT_ONLY,(),OutcomeAccess.DEVELOPMENT_VISIBLE))
        manifest = decode_artifact_manifest(plane.root.resolve(published.manifest_materialization.relative_path,for_write=False).read_bytes())
        inputs.append(VerifiedArtifactInput(manifest.logical,manifest.materialization))
    runners = RunnerRegistry(tuple(sorted((f.runner_factory() for f in factories),key=lambda r:r.manifest.registry_id)),
        registry_sha256=compiled.registry.fingerprint())
    index = DevelopmentRunRecoveryIndex.from_execution_plan(plan,run_id=run.run_plan_id,wave_id='wave.software.paired',authority_identities=())
    recovery = ExternalRunRecoveryStore(plane);recovery.freeze(index)
    contacts = ExternalNativeEffectContactStore(plane=plane,execution_plan=ObjectIdentity.from_record(plan.execution_plan_id,plan),
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    engine = create_catalog_engine('sqlite+pysqlite:///:memory:');upgrade_catalog(engine)
    repository = SQLiteOperationalRepository(engine)
    scheduler = LocalScheduler(operational_repository=repository,artifact_writer=plane,receipt_store=ExternalTaskReceiptStore(plane),
        recovery_index=index,recovery_store=recovery,runner_registry=runners,implementation_commit=source.provenance.observed_git_head,
        external_input_resolver=_StaticInputResolver(tuple(inputs)),executor=DirectTaskExecutor(),input_port_factory=plane,lane=PlanLane.DEVELOPMENT,
        authorized_barriers=(),assurance_profile=ExecutionAssuranceProfile.TRUSTED_LOCAL,native_effect_contact_store=contacts,
        native_effect_capability_keys=tuple(f.manifest.capability_key for f in factories if f.registration.native_effect))
    cpu,wall = time.process_time(),time.monotonic()
    try:
        result = scheduler.execute(run.run_plan_id,plan)
        assert result.status is OperationalStatus.SUCCEEDED,tuple((a.task_id,a.disposition,a.reason_code) for a in repository.attempts(run.run_plan_id))
        print('paired_installed_cost',{'new_exposed_native_children':48,'wall_seconds':time.monotonic()-wall,
            'cpu_seconds':time.process_time()-cpu,'process_peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024})
        _cold_completed_paired(tmp_path/'original',tmp_path,monkeypatch)
        assert scheduler.execute(run.run_plan_id,plan) == result
    finally:
        engine.dispose()
