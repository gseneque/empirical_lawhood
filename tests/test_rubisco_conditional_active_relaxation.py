# SPDX-License-Identifier: MPL-2.0
"""Prospective subset custody controls; no measured enzyme or mutation response."""
from empirical_lawhood.storage.artifact_sidecars import resolve_artifact_sidecar_bytes

from dataclasses import fields, replace
from hashlib import sha256
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import zlib

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import active_relaxation_native as native
from empirical_lawhood.domains.rubisco.rubisco_response import active_relaxation_operation as owner
from empirical_lawhood.domains.rubisco.rubisco_response import active_relaxation_read as retained
from empirical_lawhood.domains.rubisco.rubisco_response import active_relaxation_translation as graph
from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_selection import MODEL_NAMES, prepare_conditional_relaxation_selection
from empirical_lawhood.adapters.rubisco.rubisco_response.fixed_coordinate_mm import COULOMB_KJ_NM_PER_MOL_E2
from empirical_lawhood.api.domain_composition.rubisco_response import active_relaxation as public

from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.execution.native_subwork import NativeSubworkState
from tests.runtime_platform.test_native_subwork import _plane
from tests import test_rubisco_active_relaxation_operation as controls

compile_selected = controls.compile_selected
custody = controls.custody
fixture = controls.fixture
matched = controls.matched


@pytest.fixture
def conditional(fixture):
    selection = public.prepare_conditional_active_relaxation(plan=fixture.plan,
        state_census=fixture.plan.members[0].state_census[:2],
        assumptions=('Exposed software fixture with two declared starts and no physical population claim.',))
    values = {field.name:getattr(fixture.config, field.name) for field in fields(owner.ActiveRelaxationConfig)}
    fixture.config = owner.ConditionalActiveRelaxationConfig(**values, selection=selection)
    return fixture


@pytest.mark.parametrize('change', ('empty', 'duplicate', 'unknown-site', 'unknown-water', 'assumptions', 'plan'))
def test_selection_refuses_missing_or_unmatched_scenarios_before_native(fixture, change):
    census = fixture.plan.members[0].state_census[:1]
    assumptions = ('Explicit exposed chemical scenario.',)
    if change == 'empty':
        census = ()
    elif change == 'duplicate':
        census = census+census
    elif change == 'unknown-site':
        census = (('unselected.site', *census[0][1:]),)
    elif change == 'unknown-water':
        census = ((*census[0][:2], 'INVENTED'),)
    elif change == 'assumptions':
        assumptions = ()
    if change == 'plan':
        selection = prepare_conditional_relaxation_selection(plan=fixture.plan, state_census=census, assumptions=assumptions)
        changed_plan = replace(fixture.plan, plan_id=fixture.plan.plan_id+'.changed')
        with pytest.raises(ValueError, match='original plan'):
            values = {field.name:getattr(fixture.config, field.name) for field in fields(owner.ActiveRelaxationConfig)}
            owner.ConditionalActiveRelaxationConfig(**{**values, 'plan':changed_plan}, selection=selection)
    else:
        with pytest.raises(ValueError):
            prepare_conditional_relaxation_selection(plan=fixture.plan, state_census=census, assumptions=assumptions)
    assert not Path(fixture.config.work_directory).exists()


def test_shared_plan_and_all_direct_seeds_survive_selected_native_census(conditional):
    f = conditional
    c = custody(f)
    assert owner._decode(c.context, conditional=True) == (f.config, f.model, f.prepared, f.sources)
    assert len(f.config.seeds) == len(f.prepared.seeds) == 96
    assert len(f.config.plan.members) == 4 and all(len(m.state_census) == 96 for m in f.plan.members)
    assert len(c.context.input_ports) == 105 and len(c.work.definitions) == 2
    assert {d.configuration for d in c.work.definitions} == {s.identity for s in owner.selected_seeds(f.config, f.prepared)}
    assert all(f.config.selection.identity in d.sources for d in c.work.definitions)
    draft = graph.active_relaxation_draft(f.config)
    assert len(draft.development_study.numerical_view_ids) == 2
    assert draft.development_study.assigned_unit_ids == (owner.UNIT,)
    compiled = compile_selected(f)
    assert compiled.proof is not None and len(compiled.execution_plan.tasks) == 1
    task = compiled.execution_plan.tasks[0]
    assert task.maximum_attempts == 1 and task.capability.requested_resources == owner.BUDGET
    assert task.outputs[0].payload_schema == owner.ConditionalActiveRelaxationResult.SCHEMA
    assert owner.BUDGET.wall_time_seconds is None
    assert owner.operation_declaration().manifest().fingerprint() == '90bf3365043ec8ad87064d6b22e23c88a15b323b987bdfac2d9b6fc83c660676'
    assert decode_canonical_bytes(f.config.canonical_bytes(), owner.ConditionalActiveRelaxationConfig,
        maximum_bytes=owner.MAX_CONFIG) == f.config


@pytest.mark.parametrize('change', ('selection-port', 'unselected-seed', 'question', 'budget'))
def test_shared_compiler_refuses_trimmed_context_or_changed_question(conditional, change):
    f = conditional
    draft = graph.active_relaxation_draft(f.config)
    if change in ('selection-port', 'unselected-seed'):
        key = ('external.active-relaxation.native-conditional-selection' if change == 'selection-port'
            else 'external.active-relaxation.native-seed.095')
        draft = replace(draft, external_inputs=tuple(row for row in draft.external_inputs if row.input_id != key),
            links=tuple(row for row in draft.links if row.external_input_id != key))
    elif change == 'question':
        draft = replace(draft, development_study=replace(draft.development_study, question='All active states are populated.'))
    else:
        draft = replace(draft, operations=(replace(draft.operations[0], resource_budget=replace(owner.BUDGET, cpu_cores=9)),))
    with pytest.raises(ValueError):
        compile_selected(f, draft)
    assert not Path(f.config.work_directory).exists()


def install_exposed_operator(monkeypatch, *, fail_first=False):
    from tests.rubisco_exposed_geometry_fixture import install_exposed_geometry
    install_exposed_geometry(monkeypatch)
    import empirical_lawhood.domains.rubisco.rubisco_response as package
    import empirical_lawhood.adapters.rubisco.rubisco_response as native_package
    from empirical_lawhood.adapters.rubisco.rubisco_response import periodic_qmmm as qmmm
    calls, builds = [], []
    monkeypatch.setattr(owner, 'authenticate_periodic_engine', lambda *a, **k:None)
    for short in ('periodic_mm_remainder', 'periodic_images', 'pyscf_periodic_electronic'):
        owner_package = native_package if short == 'pyscf_periodic_electronic' else package
        stub = ModuleType(owner_package.__name__+'.'+short)
        monkeypatch.setitem(sys.modules, stub.__name__, stub)
        monkeypatch.setattr(owner_package, short, stub, raising=False)

    def build(**kwargs):
        builds.append('EXPOSED_MM_ASSIGNMENT_STUB')
        if fail_first and len(builds) == 1:
            raise RuntimeError('exposed conditional failure')
        (kwargs['output_directory']/'mm-assignment.json').write_text('{"scope":"EXPOSED_SOFTWARE_STUB"}\n')
        return object(), {}, dict(scope='EXPOSED_SOFTWARE_STUB')

    class StationaryOperator:
        def __init__(self, **kwargs):
            self.observe = kwargs['observe']
            self.evaluations = 0
            self.remainder_audit = self.embedding_audit = dict(scope='EXPOSED_SOFTWARE_STUB')

        def evaluate(self, coordinates):
            self.evaluations += 1
            calls.append('EXPOSED_ZERO_GRADIENT_CALLBACK')
            for event in ('entry', 'electronic-return', 'return'):
                self.observe(dict(event=event, evaluation=self.evaluations, physical_atoms=len(coordinates),
                    converged=True, orbital_gradient_norm=0., energy_hartree=-1.))
            return dict(energy_hartree=-1., gradient_hartree_per_bohr=np.zeros_like(coordinates),
                gradient_unit=native.GRADIENT_UNIT, bohr_angstrom=.52917721092,
                hartree_kj_mol=COULOMB_KJ_NM_PER_MOL_E2/(.52917721092/10))

    monkeypatch.setattr(qmmm, 'build_periodic_amber_system', build)
    monkeypatch.setattr(qmmm, 'PeriodicCoupledOperator', StationaryOperator)
    return builds, calls


def execute_and_read(f, c):
    runner = owner.ActiveRelaxationRunner(conditional=True)
    result = runner.execute_with_native_subwork(c.context, c.store)
    original = decode_canonical_bytes(result.outputs[0].payload,
        owner.ConditionalActiveRelaxationResult, maximum_bytes=64*2**20)
    report = retained.read_relaxation(config=f.config, representation=f.model, prepared=f.prepared,
        coordinate_bytes=f.coordinates, original_result=original, native_subwork=c.store,
        assessor_source=f.model.material.sources[0], readout_id='readout.exposed.conditional.'+f.config.model_name)
    return result, original, report


def test_selected_original_failures_and_endpoints_survive_read_and_recovery(conditional, monkeypatch):
    f = conditional
    builds, calls = install_exposed_operator(monkeypatch, fail_first=True)
    c = custody(f)
    raw, original, report = execute_and_read(f, c)
    assert len(builds) == 2 and len(calls) == 2
    assert len(original.units) == len(report.endpoints) == 2 and len(report.state_census) == 96
    assert sum(row.native_error is not None for row in report.endpoints) == 1
    assert sum(row.assessment is not None for row in report.endpoints) == 1
    assert report.endpoints[1].assessment.complete_reference_evaluations == 2
    assert decode_canonical_bytes(report.canonical_bytes(), retained.ConditionalActiveRelaxationReadout,
        maximum_bytes=64*2**20) == report

    def refuse(**kwargs):
        pytest.fail('completed conditional attempt was replayed')

    monkeypatch.setattr(native, 'execute_active_relaxation', refuse)
    recovered = owner.ActiveRelaxationRunner(conditional=True).execute_with_native_subwork(c.fresh(), c.store)
    assert recovered.outputs[0].payload == raw.outputs[0].payload
    with pytest.raises(ValueError, match='selected denominator'):
        replace(original, units=original.units[:-1])
    with pytest.raises(ValueError, match='complete denominator'):
        replace(report, state_census=report.state_census[:2])
    with pytest.raises(TypeError, match='exact ActiveRelaxationReadout'):
        retained.assess_matched_readouts(plan=f.plan, readouts=(report,)*4)
    original_read = c.store.iter_completed_output
    monkeypatch.setattr(c.store, 'iter_completed_output', lambda definition, key, **kwargs:
        iter((b'CORRUPT ORIGINAL ARCHIVE',)) if key == 'files.raw' else original_read(definition, key, **kwargs))
    with pytest.raises((ValueError, zlib.error)):
        retained.read_relaxation(config=f.config, representation=f.model, prepared=f.prepared,
            coordinate_bytes=f.coordinates, original_result=original, native_subwork=c.store,
            assessor_source=f.model.material.sources[0], readout_id='readout.exposed.conditional.corrupt')
    assert len(calls) == 2


def test_unknown_selected_contact_cannot_be_repeated(conditional, monkeypatch):
    f = conditional
    c = custody(f)
    monkeypatch.setattr(owner, 'authenticate_periodic_engine', lambda *a, **k:None)
    monkeypatch.setattr(native, 'execute_active_relaxation', lambda **k:pytest.fail('unknown attempt repeated'))
    c.store.freeze_roster(c.work.rosters[0], definitions=c.work.definitions)
    entry = c.store.begin(c.work.definitions[0])
    c.store.contact(entry)
    with pytest.raises(ValueError, match='no automatic retry'):
        owner.ActiveRelaxationRunner(conditional=True).execute_with_native_subwork(c.context, c.store)
    assert c.store.inspect(c.work.definitions[0]).state is NativeSubworkState.UNKNOWN_COMPLETION
    assert c.store.inspect(c.work.definitions[1]).state is NativeSubworkState.NOT_ENTERED


def test_four_original_members_retain_all_384_starts_and_unmeasured_alternatives(conditional, monkeypatch):
    f = conditional
    builds, calls = install_exposed_operator(monkeypatch)
    reports = []
    for name, (model, prototype, prepared, raw_top, raw_xyz, coordinates) in zip(MODEL_NAMES, f.models, strict=True):
        directory = f.tmp_path/name
        directory.mkdir()
        sources = owner.prepare_raw_sources(prototype, raw_top, raw_xyz)
        config = replace(f.config, config_id=f.config.config_id+'.'+name, model_name=name,
            prototype=prototype, preparation=prepared.identity, preparation_size_bytes=prepared.canonical_size_bytes(),
            seeds=prepared.seeds, representation_size_bytes=model.canonical_size_bytes(),
            raw_sources=sources.identity, raw_source_size_bytes=sources.canonical_size_bytes(),
            work_directory=str(directory/'working'))
        member = SimpleNamespace(**{**vars(f), 'model':model, 'prototype':prototype, 'prepared':prepared,
            'raw_top':raw_top, 'raw_xyz':raw_xyz, 'coordinates':coordinates, 'sources':sources,
            'config':config, 'tmp_path':directory})
        _, _, report = execute_and_read(member, custody(member))
        reports.append(report)
    result = public.assess_matched_active_relaxation(plan=f.plan, readouts=tuple(reports),
        conditional_selection=f.config.selection)
    assert len(builds) == 8 and len(calls) == 16
    assert all(member.states_not_selected == 94 for member in result.members)
    assert sum(member.states_not_selected for member in result.members) == 376
    assert sum(len(report.endpoints) for report in reports) == 8
    assert result.original_biological_units == 1
    assert result.equilibrium_populations == result.turnover_contrast == result.specificity_contrast == 'UNEVALUABLE'
    assert decode_canonical_bytes(result.canonical_bytes(), retained.ConditionalMatchedActiveRelaxationReadout,
        maximum_bytes=64*2**20) == result
    with pytest.raises(ValueError, match='all four'):
        public.assess_matched_active_relaxation(plan=f.plan, readouts=tuple(reports[:-1]), conditional_selection=f.config.selection)
    changed = replace(f.config.selection, assumptions=('Different exposed chemical assumption.',))
    with pytest.raises(ValueError, match='shared original selection'):
        public.assess_matched_active_relaxation(plan=f.plan, readouts=tuple(reports), conditional_selection=changed)


def test_public_author_authenticates_full_inputs_and_explicit_selection(conditional, monkeypatch):
    from empirical_lawhood.api import numerical_provenance, recursive_authoring
    f = conditional
    plane = _plane(f.tmp_path/'public-custody')
    project = f.tmp_path/'project'
    project.mkdir()
    output = Path(plane.root.contract.canonical_path)/'authored'
    calls = []
    monkeypatch.setattr(recursive_authoring, 'implementation_binding', lambda root:f.config.implementation)
    monkeypatch.setattr(numerical_provenance, 'capture_numerical_provenance', lambda **k:f.config.provenance)

    def author(**kwargs):
        calls.append(kwargs)
        assert len(kwargs['input_bindings']) == len(kwargs['draft'].external_inputs) == 104
        for key, path in kwargs['input_bindings']:
            selected = next(row for row in kwargs['draft'].external_inputs if row.input_id == key)
            manifest = resolve_artifact_sidecar_bytes(plane, path.with_name(path.name + '.manifest.json').read_bytes())
            plane.verify_manifest(manifest)
            assert path.stat().st_size == selected.maximum_size_bytes
            assert sha256(path.read_bytes()).hexdigest() == selected.expected_content_sha256 == manifest.logical.content_sha256
        return {'authored_directory':str(output), 'scope':'EXPOSED_FINAL_AUTHOR_STUB'}

    monkeypatch.setattr(recursive_authoring, 'author_recursive_wave', author)
    result = public.author_active_relaxation(plan=f.plan, model_name=f.config.model_name,
        prepared=f.prepared, prototype=f.prototype, representation=f.model, raw_topology=f.raw_top,
        raw_coordinates=f.raw_xyz, project_root=project, work_directory=Path(f.config.work_directory),
        artifact_writer=plane, output_dir=output, conditional_selection=f.config.selection)
    assert len(calls) == 1 and len(result['native_input_paths']) == 104
    assert not output.exists() and not Path(f.config.work_directory).exists()
