# SPDX-License-Identifier: MPL-2.0
"""Exposed complete pilot cost controls and actual retained-custody joins."""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from fractions import Fraction as F

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import pilot_allocation as owner
from empirical_lawhood.domains.rubisco.rubisco_response import pilot_allocation_read as retained
from empirical_lawhood.storage.artifacts import ArtifactIdentityConflict
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.inquiry.recursive_inquiry import InquiryCost
from tests import test_rubisco_physical_first_passage as passage


pin = passage.pin
fixture = passage.fixture


def selected(**changes):
    case = owner.PilotCalibrationCase('calibration.one', pin('config.one'), 'class.force')
    profile = owner.PilotCostClass('class.force', 'COMPLETE_COUPLED_FORCE_RETURN', 1, D('1.25'),
        pin('scope.force'), 'Explicit exposed extrapolation from the complete selected operator task.')
    work = owner.PilotWorkEstimate('work.all', pin('selection.all'), profile.class_id, 12,
        owner.COMPLETE_COVERAGE, 2**20, 2**16, 4096)
    first = owner.PilotCandidate('candidate.a', (work,), D('.01'), (pin('criteria.all'),))
    second = owner.PilotCandidate('candidate.b', (replace(work, units=6),), D('.01'), (pin('criteria.all'),))
    return replace(owner.PilotAllocationRule('rule.exposed.pilot', (case,), (profile,), (first, second),
        ('candidate.a', 'candidate.b'), 'USD', D('.001'), pin('quote.exposed'), D('.05'),
        2**21, 2**17, 8192, pin('design.exposed')), **changes)


def measured(rule=None, **changes):
    rule = rule or selected()
    case = rule.calibrations[0]
    return replace(owner.PilotCostMeasurement(case.calibration_id, case.configuration, pin('original.one'),
        'COMPLETE', InquiryCost(D(13), D(10), D(2000)), 3, 2**19, ()), **changes)


def test_exact_serial_projection_selects_the_first_affordable_complete_candidate():
    rule = selected()
    report = owner.allocate_pilot(rule, (measured(rule),))
    # Independently derived: max whole-task cost 10/3 per force, multiplied
    # by 5/4; twelve units cost $0.06, six cost $0.035 including overhead.
    first, second = (report['candidates'][key] for key in rule.priority)
    assert first['serial_seconds'] == owner.rational(50)
    assert first['additional_charge'] == owner.rational(F(6, 100))
    assert second['additional_charge'] == owner.rational(F(35, 1000))
    assert report['selected_candidate'] == 'candidate.b'
    assert first['reason_codes'] == ['ADDITIONAL_PROJECTED_CHARGE_EXCEEDED']
    assert second['complete_material_role_cells'] == 44
    assert report['scientific_acquisition_authority'] == 'NONE'
    with localcontext() as context:
        context.prec = 2
        assert owner.allocate_pilot(rule, (measured(rule),)) == report
    assert decode_canonical_bytes(rule.canonical_bytes(), owner.PilotAllocationRule,
        maximum_bytes=2**20) == rule


def test_priority_is_prospective_and_shared_work_is_charged_once():
    rule = selected(maximum_additional_projected_charge=D(1), priority=('candidate.b', 'candidate.a'))
    report = owner.allocate_pilot(rule, (measured(rule),))
    assert report['selected_candidate'] == 'candidate.b'
    assert report['candidates']['candidate.b']['scientific_work_items'] == 1
    duplicate = replace(rule.candidates[0].work[0], work_id='work.duplicate')
    with pytest.raises(ValueError, match='repeats one scientific selection'):
        replace(rule.candidates[0], work=(*rule.candidates[0].work, duplicate))
    with pytest.raises(ValueError, match='priority'):
        replace(rule, priority=('candidate.b', 'candidate.b'))


@pytest.mark.parametrize('omitted', ('material', 'role'))
def test_no_candidate_can_spend_its_tranche_on_an_incomplete_paired_roster(omitted):
    candidate = selected().candidates[0]
    work = candidate.work[0]
    coverage = tuple(cell for cell in work.coverage if (
        cell[0] != 'v1-wt' if omitted == 'material' else cell[1] != 'oxygen-charge-transfer'))
    with pytest.raises(ValueError, match='omits a consequential role'):
        replace(candidate, work=(replace(work, coverage=coverage),))


@pytest.mark.parametrize('change,reason', (
    ({'quoted_charge_per_second': None, 'quote_source': None}, 'CURRENT_QUOTE_UNAVAILABLE'),
    ({'maximum_additional_projected_charge': None}, 'PROJECTED_CHARGE_ENVELOPE_UNSELECTED'),
    ({'available_device_memory_bytes': 1}, 'SELECTED_RESOURCE_CAPACITY_INSUFFICIENT'),
    ({'available_host_memory_bytes': 1}, 'SELECTED_RESOURCE_CAPACITY_INSUFFICIENT'),
    ({'available_retained_bytes': 1}, 'SELECTED_RESOURCE_CAPACITY_INSUFFICIENT'),
))
def test_missing_quote_charge_selection_or_actual_capacity_cannot_select_work(change, reason):
    rule = selected(**change)
    report = owner.allocate_pilot(rule, (measured(rule),))
    assert report['selected_candidate'] is None
    assert all(reason in row['reason_codes'] for row in report['candidates'].values())


def test_all_original_calibrations_are_required_and_none_can_be_counted_twice():
    rule = selected()
    second = replace(rule.calibrations[0], calibration_id='calibration.two', configuration=pin('config.two'))
    rule = replace(rule, calibrations=(*rule.calibrations, second))
    with pytest.raises(ValueError, match='every selected calibration'):
        owner.allocate_pilot(rule, (measured(rule),))
    duplicate = replace(measured(rule), calibration_id=second.calibration_id, configuration=second.configuration)
    with pytest.raises(ValueError, match='repeats one original'):
        owner.allocate_pilot(rule, (measured(rule), duplicate))
    wrong = replace(duplicate, original=pin('original.two'), configuration=pin('config.wrong'))
    with pytest.raises(ValueError, match='substitutes'):
        owner.allocate_pilot(rule, (measured(rule), wrong))


@pytest.mark.parametrize('disposition', ('FAILED', 'UNASSESSED', 'MISSING_ORIGINAL'))
def test_failures_and_unknowns_preserve_cost_and_prevent_success_only_calibration(disposition):
    rule = selected()
    row = measured(rule, disposition='UNASSESSED', completed_units=0, reason_codes=('ORIGINAL_UNAVAILABLE',))
    # Missing work has no invented zero cost or recovered original.
    if disposition == 'MISSING_ORIGINAL':
        row = owner.PilotCostMeasurement(row.calibration_id, row.configuration, None, disposition,
            InquiryCost(None, None, None), 0, None, row.reason_codes)
    else:
        row = replace(row, disposition=disposition)
    report = owner.allocate_pilot(rule, (row,))
    assert report['selected_candidate'] is None
    assert report['original_calibrations'] == (row.to_document(),)
    assert report['total_original_calibration_cost']['wall_seconds'] == (
        None if disposition == 'MISSING_ORIGINAL' else owner.rational(10))


def test_cost_memory_and_success_census_cannot_be_invented():
    rule = selected()
    for row in (measured(rule, cost=InquiryCost(None, None, D(100))),
                measured(rule, peak_rss_bytes=None), measured(rule, peak_rss_bytes=2**22)):
        assert owner.allocate_pilot(rule, (row,))['selected_candidate'] is None
    sparse = replace(rule, cost_classes=(replace(rule.cost_classes[0], minimum_successful_calibrations=2),))
    assert owner.allocate_pilot(sparse, (measured(rule),))['selected_candidate'] is None
    with pytest.raises(ValueError, match='invents completed units'):
        measured(rule, disposition='FAILED', reason_codes=('NATIVE_FAILED',))
    with pytest.raises(ValueError, match='invents completed units'):
        measured(rule, disposition='UNASSESSED', completed_units=0, original=None, reason_codes=('UNASSESSED',))


def native_rule(source):
    rule = selected()
    case = replace(rule.calibrations[0], configuration=source.config.identity)
    profile = replace(rule.cost_classes[0], scope=retained.pilot_force_scope(source.config).identity)
    # These are exposed task-cost projections, not native molecular recipes.
    work = replace(rule.candidates[0].work[0], host_memory_bytes=2**40)
    candidate = replace(rule.candidates[0], work=(work,))
    return replace(rule, calibrations=(case,), cost_classes=(profile,), candidates=(candidate,),
        priority=(candidate.candidate_id,), maximum_additional_projected_charge=D(1000),
        available_host_memory_bytes=2**41)


def pilot_source(source):
    return retained.RetainedPilotCalibration('calibration.one', source.config, source.representation,
        source.phase_bytes, source.original_result, source.native_subwork)


def test_original_trajectory_cost_and_export_reconstruct_without_new_native_calls(fixture, monkeypatch):
    from empirical_lawhood.api import numerical_provenance, recursive_authoring
    from empirical_lawhood.api.domain_composition.rubisco_response import pilot as public
    from tests.test_recursive_public_service import _plane
    _, path, _, observed = passage.run_original(fixture, monkeypatch)
    source = pilot_source(path)
    rule = native_rule(source)
    plane = _plane(fixture.tmp_path/'pilot-custody')
    monkeypatch.setattr(recursive_authoring, 'implementation_binding', lambda _: fixture.config.implementation)
    monkeypatch.setattr(numerical_provenance, 'capture_numerical_provenance', lambda **k: fixture.config.provenance)
    before = len(observed)
    exported = public.export_pilot_allocation(selection=rule, sources=(source,), project_root=fixture.tmp_path,
        artifact_writer=plane, output_relative_path='selected/pilot')
    reread = public.read_pilot_allocation_export(directory_relative_path='selected/pilot', sources=(source,), artifact_writer=plane)
    assert reread['report'] == exported['report'] and len(observed) == before
    measurement = reread['report']['original_calibrations'][0]['value']
    assert measurement['completed_units'] == 5
    assert measurement['disposition'] == 'COMPLETE'
    assert measurement['cost'] == source.original_result.completion.cost.to_document()
    assert reread['report']['selected_candidate'] == 'candidate.a'
    target = plane.root.resolve('selected/pilot/report.txt', for_write=False)
    target.write_bytes(target.read_bytes()+b'changed\n')
    with pytest.raises(ArtifactIdentityConflict):
        public.read_pilot_allocation_export(directory_relative_path='selected/pilot', sources=(source,), artifact_writer=plane)


def test_actual_failed_and_missing_originals_keep_cost_without_calibration_units(fixture, monkeypatch):
    _, path, _, observed = passage.run_original(fixture, monkeypatch, failure='native')
    source = pilot_source(path)
    rule = native_rule(source)
    before = len(observed)
    report, arrays = retained.read_pilot_allocation(selection=rule, sources=(source,), assessor_source=fixture.model.material.sources[0])
    row = report['original_calibrations'][0]['value']
    assert row['disposition'] == 'FAILED' and row['completed_units'] == 0
    assert row['cost'] == source.original_result.completion.cost.to_document()
    assert report['selected_candidate'] is None and arrays['pilot.completed-units'].tolist() == [0]
    missing = replace(source, original_result=None, native_subwork=None)
    report, _ = retained.read_pilot_allocation(selection=rule, sources=(missing,), assessor_source=fixture.model.material.sources[0])
    assert report['original_calibrations'][0]['value']['disposition'] == 'MISSING_ORIGINAL'
    assert report['total_original_calibration_cost']['wall_seconds'] is None
    assert len(observed) == before


def test_changed_operator_scope_and_omitted_source_refuse_before_original_contact(fixture):
    config, phase, _ = passage.native_selection(fixture)
    source = retained.RetainedPilotCalibration('calibration.one', config, fixture.model, phase, None, None)
    rule = native_rule(source)
    with pytest.raises(ValueError, match='every selected original'):
        retained.validate_pilot_sources(rule, ())
    wrong = replace(rule, cost_classes=(replace(rule.cost_classes[0], scope=pin('scope.wrong')),))
    with pytest.raises(ValueError, match='operator or environment'):
        retained.validate_pilot_sources(wrong, (source,))


def test_original_byte_change_during_allocation_refuses_the_return(fixture, monkeypatch):
    _, path, _, _ = passage.run_original(fixture, monkeypatch)
    source = pilot_source(path)
    rule = native_rule(source)
    original_allocate = retained.allocate_pilot
    original_stream = source.native_subwork.iter_completed_output
    def changed_stream(definition, output_id, **kwargs):
        first = True
        for block in original_stream(definition, output_id, **kwargs):
            if first and output_id == 'files.raw' and block:
                block = bytes((block[0] ^ 1,))+block[1:]
                first = False
            yield block
    def allocate_then_change(*args):
        report = original_allocate(*args)
        monkeypatch.setattr(source.native_subwork, 'iter_completed_output', changed_stream)
        return report
    monkeypatch.setattr(retained, 'allocate_pilot', allocate_then_change)
    with pytest.raises((ValueError, ArtifactIdentityConflict), match='original output|digest|physical'):
        retained.read_pilot_allocation(selection=rule, sources=(source,), assessor_source=fixture.model.material.sources[0])


@pytest.mark.parametrize('failed', (False, True))
def test_complete_force_probe_calibration_uses_actual_receipted_cost(fixture, monkeypatch, failed):
    import numpy as np
    from tests import test_rubisco_periodic_probe_operation as probe
    from tests.rubisco_exposed_geometry_fixture import install_exposed_geometry, retain_exposed_source_coordinates
    install_exposed_geometry(monkeypatch)
    custody = probe.custody(fixture)
    calls = []
    monkeypatch.setattr(probe.owner, 'authenticate_periodic_engine', lambda *a, **k: ())
    def invoke(**kwargs):
        calls.append('EXPOSED_FORCE')
        retain_exposed_source_coordinates(kwargs)
        (kwargs['directory']/'exposed.txt').write_bytes(b'Exposed software control only.\n')
        if failed:
            raise RuntimeError('exposed calibration failure')
        return dict(energy_hartree=-1.0, gradient_hartree_per_bohr=np.zeros((83, 3)))
    monkeypatch.setattr(probe.native, 'execute_periodic_probe', invoke)
    output = probe.owner.PeriodicProbeRunner().execute_with_native_subwork(custody.context, custody.store)
    result = decode_canonical_bytes(output.outputs[0].payload, probe.owner.PeriodicProbeResult,
        maximum_bytes=probe.owner.MAX_RETURN)
    source = retained.RetainedPilotCalibration('calibration.one', fixture.config, fixture.model, None, result, custody.store)
    rule = native_rule(source)
    report, _ = retained.read_pilot_allocation(selection=rule, sources=(source,), assessor_source=fixture.model.material.sources[0])
    row = report['original_calibrations'][0]['value']
    assert row['disposition'] == ('FAILED' if failed else 'COMPLETE')
    assert row['completed_units'] == (0 if failed else 1)
    assert row['cost'] == result.completion.cost.to_document()
    assert calls == ['EXPOSED_FORCE']
