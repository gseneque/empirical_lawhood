# SPDX-License-Identifier: MPL-2.0
"""Expose coherent wrong bias geometry while original trace and custody still pass."""

from dataclasses import replace
import math
import zlib

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import periodic_bias as producer
from empirical_lawhood.adapters.rubisco.rubisco_response import periodic_equilibrium_native as native
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_equilibrium_operation as owner
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_equilibrium_read as retained
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium_recorded import assess_recorded_equilibrium, selected_equilibrium_member
from empirical_lawhood.api.domain_composition.rubisco_response.periodic_equilibrium import read_reference_equilibrium
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from tests import test_rubisco_periodic_equilibrium_acquisition as base
from tests.test_rubisco_periodic_bias_assessment import criteria


fixture = base.fixture


def corrupt_bias(monkeypatch):
    original = native.selected_bias
    def wrong(*args, **kwargs):
        result = original(*args, **kwargs)
        window = args[0].window
        values = tuple(value+.07 for value in result['cv_values'])
        displacements = tuple(math.atan2(math.sin(value-float(center)), math.cos(value-float(center)))
            if kind == 'IMPROPER_DIHEDRAL' else value-float(center)
            for value, center, kind in zip(values, window.centers, window.cv_kinds, strict=True))
        energies = tuple(.5*float(k)*d*d for k, d in zip(window.force_constants, displacements, strict=True))
        gradient = np.zeros_like(result['gradient_kj_mol_per_angstrom'])
        for rows, k, d, derivative in zip(result['cv_atom_indices'], window.force_constants, displacements,
                result['cv_cartesian_derivatives'], strict=True):
            gradient[list(rows)] += float(k)*d*derivative
        return dict(result, cv_values=values, cv_displacements=displacements, term_energies_kj_mol=energies,
            energy_kj_mol=math.fsum(energies), gradient_kj_mol_per_angstrom=gradient)
    monkeypatch.setattr(native, 'selected_bias', wrong)


@pytest.mark.parametrize('wrong', (False, True))
def test_public_original_read_checks_geometry_separately_from_authentic_stochastic_trace(fixture, monkeypatch, wrong):
    config, raw = base.trajectory(fixture)
    limits = criteria(config.selection.convention, 3)
    base.stub_native(fixture, monkeypatch)
    if wrong:corrupt_bias(monkeypatch)
    c = base.custody(fixture, config, raw)
    output = owner.ReferenceEquilibriumRunner().execute_with_native_subwork(c.context, c.store)
    result = decode_canonical_bytes(output.outputs[0].payload, owner.ReferenceEquilibriumResult, maximum_bytes=owner.MAX_RETURN)
    def refuse(*args, **kwargs):pytest.fail('read called the native or bias producer')
    monkeypatch.setattr(native, 'execute_reference_equilibrium', refuse)
    monkeypatch.setattr(native, 'selected_bias', refuse)
    monkeypatch.setattr(producer, 'evaluate_reference_umbrella_bias', refuse)
    inputs = dict(config=config, representation=fixture.model, phase_bytes=raw, original_result=result,
        native_subwork=c.store, assessor_source=fixture.model.material.sources[0])
    unselected = read_reference_equilibrium(**inputs)
    assert unselected['assessment_error'] is None
    assert unselected['assessment']['selected_trace_criteria'] == 'SATISFIED'
    assert unselected['assessment']['bias_geometry_assessment']['selected_bias_geometry_criteria'] == 'UNEVALUABLE'
    readout = read_reference_equilibrium(**inputs, bias_geometry_criteria=limits)
    assert readout['assessment_error'] is None
    assert readout['bias_geometry_criteria'] == limits.to_document()
    assert readout['authenticated_file_count'] == len(result.returned.files.files)
    assert readout['assessment']['selected_trace_criteria'] == 'SATISFIED'
    geometry = readout['assessment']['bias_geometry_assessment']
    assert geometry['selected_bias_geometry_criteria'] == ('FALSIFIED' if wrong else 'SATISFIED')
    assert geometry['assessed_frames'] == geometry['expected_frames'] == 4
    assert geometry['falsified_frames'] == (4 if wrong else 0)
    assert geometry['first_falsified_evaluation'] == (1 if wrong else None)
    assert geometry['satisfied_frames'] == (0 if wrong else 4)
    assert readout['new_operator_evaluations'] == 0


@pytest.mark.parametrize('wrong', (False, True))
def test_prefix_preserves_finite_bias_negative_and_cannot_acquire_full_admission(fixture, monkeypatch, wrong):
    config, raw = base.trajectory(fixture)
    base.stub_native(fixture, monkeypatch, failure='native')
    if wrong:corrupt_bias(monkeypatch)
    directory = fixture.tmp_path/'native'
    with pytest.raises(RuntimeError):base.run_body(fixture, config, raw, directory)
    report = assess_recorded_equilibrium(selection=config.selection, prototype=fixture.selection,
        representation=fixture.model, phase_bytes=raw, native_succeeded=False,
        bias_geometry_criteria=criteria(config.selection.convention, 3),
        files=((p.name,p.read_bytes() if selected_equilibrium_member(p.name) else None) for p in sorted(directory.iterdir())))
    geometry = report['bias_geometry_assessment']
    assert geometry['assessed_frames'] == 1 and geometry['expected_frames'] == 4
    assert geometry['selected_bias_geometry_criteria'] == ('FALSIFIED' if wrong else 'UNEVALUABLE')
    assert report['selected_trace_criteria'] == 'UNEVALUABLE'


def test_unresolved_stencils_count_all_frames_and_local_terms(fixture, monkeypatch):
    config, raw = base.trajectory(fixture)
    base.stub_native(fixture, monkeypatch)
    directory = fixture.tmp_path/'native'
    base.run_body(fixture, config, raw, directory)
    from decimal import Decimal
    limits = criteria(config.selection.convention, 3, derivative_step_angstrom=Decimal('1e-30'))
    report = assess_recorded_equilibrium(selection=config.selection, prototype=fixture.selection,
        representation=fixture.model, phase_bytes=raw, native_succeeded=True, bias_geometry_criteria=limits,
        files=((p.name,p.read_bytes() if selected_equilibrium_member(p.name) else None) for p in sorted(directory.iterdir())))
    geometry = report['bias_geometry_assessment']
    assert geometry['selected_bias_geometry_criteria'] == 'UNEVALUABLE'
    assert geometry['assessed_frames'] == geometry['unevaluable_frames'] == 4
    assert geometry['first_unevaluable_evaluation'] == 1
    assert all(term['unresolved_frames'] == 4 for term in geometry['terms'])
    assert all(term['first_unresolved_reason'] == 'unresolved_displacement' for term in geometry['terms'])


def test_bias_assessment_error_cannot_hide_later_corrupt_archived_bytes(fixture, monkeypatch):
    config, raw = base.trajectory(fixture)
    base.stub_native(fixture, monkeypatch)
    original = native.execute_reference_equilibrium
    def add_tail(**kwargs):
        result = original(**kwargs)
        (kwargs['directory']/'zz-tail.txt').write_bytes(b'original-tail')
        return result
    monkeypatch.setattr(native, 'execute_reference_equilibrium', add_tail)
    c = base.custody(fixture, config, raw)
    output = owner.ReferenceEquilibriumRunner().execute_with_native_subwork(c.context, c.store)
    result = decode_canonical_bytes(output.outputs[0].payload, owner.ReferenceEquilibriumResult, maximum_bytes=owner.MAX_RETURN)
    limits = criteria(config.selection.convention, 3)
    limits = replace(limits, convention=replace(limits.convention, object_fingerprint='0'*64))
    inputs = dict(config=config, representation=fixture.model, phase_bytes=raw, original_result=result,
        native_subwork=c.store, assessor_source=fixture.model.material.sources[0], bias_geometry_criteria=limits)
    report = read_reference_equilibrium(**inputs)
    assert 'substitutes' in report['assessment_error'] and report['assessment'] is None
    assert report['authenticated_file_count'] == len(result.returned.files.files)
    original_iter = c.store.iter_completed_output
    expanded = zlib.decompress(b''.join(original_iter(result.definition, 'files.raw')), wbits=31)
    assert expanded.endswith(b'original-tail')
    compressor = zlib.compressobj(wbits=31)
    bad = compressor.compress(expanded[:-1]+b'X')+compressor.flush()
    def iter_bad(definition, output_id, **kwargs):
        if output_id == 'files.raw':yield bad
        else:yield from original_iter(definition, output_id, **kwargs)
    monkeypatch.setattr(c.store, 'iter_completed_output', iter_bad)
    with pytest.raises(retained.TrajectoryCustodyError, match='original complete file'):
        read_reference_equilibrium(**inputs)
