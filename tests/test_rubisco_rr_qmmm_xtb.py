"""Synthetic CLI outputs only; no ASH/native process or authentic source use."""
from dataclasses import replace
from decimal import Decimal, localcontext
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from empirical_lawhood.adapters.simulators.rubisco_electronic import rr_qmmm_xtb as r

D = Decimal


def original_inputs():
    return dict(current_coords=[[.52917726, 0., 0.], [1.05835452, 0., 0.]],
                current_MM_coords=[[0., 10., 0.], [0., 20., 0.], [0., 30., 0.]],
                MMcharges=[.1, 0., -.2], qm_elems=['H', 'H'], mm_elems=['O']*3,
                Grad=True, PC=True, charge=0, mult=1)


def native_capture(p):
    """Independent quadratic in native x_QM and y_PC with complete gradients."""
    with localcontext() as ctx:
        ctx.prec = 50
        qm = tuple((xyz[0], D(0), D(0)) for xyz in p.coordinates_bohr)
        selected = tuple(row for row in p.field_rows if row.exact_charge)
        pc = tuple((D(0), r.angstrom_to_bohr(row.coordinates_angstrom[1]), D(0)) for row in selected)
        energy = sum((g[0]**2/2 for g in qm), D()) + sum((g[1]**2/2 for g in pc), D())
        total = D(p.native_serialized_field_charge_sum.numerator) / D(p.native_serialized_field_charge_sum.denominator)
        norm = sum((v*v for g in qm for v in g), D()).sqrt()
    text = f'''xtb version 6.7.1 (edcfbbe) compiled on 2024-07-22
 program call : {' '.join(p.program_argv)}
 : # electrons {p.valence_electron_count} :
 : max. iterations 250 :
 : Hamiltonian GFN2-xTB :
 : restarted? false :
 : GBSA solvation false :
 : PC potential {'true' if p.embedded else 'false'} :
 : electronic temp. 300 K :
 : accuracy 0.0500000 :
 : net charge {p.formal_charge} :
 : unpaired electrons {p.unpaired_electrons} :
'''
    if p.embedded:
        text += f' : -> # point charges {len(selected)} :\n : -> sum of PC {total:.7f} e :\n'
    text += f' convergence criteria satisfied after 7 iterations\n | TOTAL ENERGY {energy:.12f} Eh |\n'
    grad = (f'$grad\ncycle = 1 SCF energy = {energy:.12f} |dE/dxyz| = {norm:.6f}\n'
            + ''.join(' '.join(format(v, '.14f') for v in xyz)+' '+atom.element.lower()+'\n'
                      for atom, xyz in zip(p.atoms, p.coordinates_bohr, strict=True))
            + ''.join(' '.join(format(v, '.13E') for v in g)+'\n' for g in qm) + '$end\n').encode()
    pcgrad = (''.join(' '.join(format(v, '.8f') for v in g)+'\n' for g in pc).encode() if p.embedded else None)
    return r.XtbSinglePointCaptureV1(p.identity, p.execution_id, p.output_locator, p.program_argv,
                                   0, text.encode(), b'normal termination of xtb\n', grad, pcgrad)


def theory(*, mutate=lambda p, c: c, maximum_callbacks=120):
    events = []

    def execute(p):
        events.append(('execute', p))
        return mutate(p, native_capture(p))

    def retain(p, c):
        events.append(('retain', p, c))

    t = r.StrictQmmmXtbTheoryV1(executable_path='/selected/bin/xtb',
                              parameter_path='/selected/share/param_gfn2-xtb.txt',
                              output_root='/selected/output', executor=execute,
                              retain_capture=retain, maximum_callbacks=maximum_callbacks)
    return t, events


def test_native_to_ash_chain_rule_on_qm_and_external_coordinate_quadratics():
    t, events = theory()
    inputs = original_inputs()
    _, qm, pc = t.run(**inputs)
    # E is native coordinate squared/2. dE/dx_ASH must be x_native*b_ASH/b_native.
    with localcontext() as ctx:
        ctx.prec = 50
        expected = r.ASH_ANGSTROM_PER_BOHR/r.ANGSTROM_PER_BOHR
    assert qm[0, 0] == pytest.approx(float(expected), abs=2e-14)
    assert np.array_equal(pc[1], [0., 0., 0.])
    for part, atom, axis, gradient in [('current_coords', 1, 0, qm[1, 0]),
                                      ('current_MM_coords', 2, 1, pc[2, 1])]:
        h = 1e-4
        plus, minus = dict(inputs), dict(inputs)
        plus[part] = [row[:] for row in inputs[part]]
        minus[part] = [row[:] for row in inputs[part]]
        plus[part][atom][axis] += h
        minus[part][atom][axis] -= h
        plus['Grad'] = minus['Grad'] = False
        fd = (t.run(**plus)-t.run(**minus))/(2*h)
        assert fd == pytest.approx(gradient/float(r.ASH_ANGSTROM_PER_BOHR), abs=3e-7)
    assert len(events) == 10  # Each invocation has one executor and one retention.


def test_exact_input_floats_original_rows_and_zero_charge_join_preserved():
    t, _ = theory()
    inputs = original_inputs()
    inputs['current_coords'][0][0] = .1
    before = [row[:] for row in inputs['current_coords']]
    t.run(**inputs)
    p = t.last_observation.plan
    assert p.atoms[0].coordinates_angstrom[0] == D.from_float(.1)
    assert p.atoms[0].coordinates_angstrom[0] != D('.1')
    assert inputs['current_coords'] == before
    assert p.native_field_ids == ('pc-00001', 'pc-00003')
    assert p.excluded_exact_zero_field_ids == ('pc-00002',)
    assert t.last_observation.pc_gradient_native[1] == (D(0),)*3
    assert len(t.last_observation.pc_gradient_ash) == 3
    assert p.program_argv[-1] == '--grad'
    assert '--opt' not in p.program_argv and '--norestart' in p.program_argv
    assert p.binary_sha256 == r.BINARY_SHA256 and p.parameter_sha256 == r.PARAMETER_SHA256
    assert tuple(name for name, _ in p.input_files) == ('input.coord', 'xcontrol.inp', 'pointcharges')
    assert all(line.split()[-1] == '99' for line in p.pcem_bytes.decode().splitlines()[1:])


@pytest.mark.parametrize('change', [
    lambda c: replace(c, pcgrad_bytes=b'0 0 0\n'),
    lambda c: replace(c, pcgrad_bytes=c.pcgrad_bytes+b'0 0 0\n'),
    lambda c: replace(c, pcgrad_bytes=b'0 NaN 0\n0 0 0\n'),
    lambda c: replace(c, gradient_bytes=None),
    lambda c: replace(c, gradient_bytes=c.gradient_bytes.replace(b'|dE/dxyz| = 2.236068', b'|dE/dxyz| = 9.000000')),
    lambda c: replace(c, stdout=c.stdout+b'FAILED TO CONVERGE\n'),
    lambda c: replace(c, stdout=c.stdout.replace(b'unpaired electrons 0', b'unpaired electrons 2')),
    lambda c: replace(c, stdout=c.stdout.replace(b'convergence criteria satisfied after 7', b'convergence criteria satisfied after 251')),
    lambda c: replace(c, native_failure_files=('.sccnotconverged',)),
    lambda c: replace(c, operational_refusal='CPU budget exceeded'),
    lambda c: replace(c, returncode=None, operational_refusal='pre-exec spawn refused'),
    lambda c: replace(c, returncode=128),
    lambda c: replace(c, plan_identity='0'*64),
    lambda c: replace(c, program_argv=c.program_argv[:-1]+('--sp',)),
])
def test_raw_refusal_is_retained_before_parsing_and_never_retried(change):
    t, events = theory(mutate=lambda p, c: change(c))
    with pytest.raises(ValueError):
        t.run(**original_inputs())
    assert [event[0] for event in events] == ['execute', 'retain']
    assert t.callback_reservations == 1 and t.last_observation is None


def test_exact_request_binding_and_native_geometry_witness_refusals():
    t, _ = theory()
    t.run(**original_inputs())
    o = t.last_observation
    with pytest.raises(ValueError, match='locator'):
        r.XtbSinglePointObservationV1(o.plan, replace(o.capture, output_locator='/elsewhere/call-0001'))
    with pytest.raises(ValueError, match='coordinates'):
        r.XtbSinglePointObservationV1(o.plan, replace(o.capture, gradient_bytes=o.capture.gradient_bytes.replace(
            b'1.00000000000000 0.00000000000000 0.00000000000000 h',
            b'1.10000000000000 0.00000000000000 0.00000000000000 h')))
    with pytest.raises(ValueError, match='argv'):
        r.XtbSinglePointObservationV1(o.plan, replace(o.capture, stdout=o.capture.stdout.replace(b'--grad', b'--sp')))


def test_energy_projection_still_requires_complete_gradient_and_one_objective():
    t, events = theory()
    inputs = dict(original_inputs(), Grad=False)
    energy = t.run(**inputs)
    assert isinstance(energy, float) and t.last_observation is not None
    assert events[0][1].program_argv[-1] == '--grad'
    broken, events = theory(mutate=lambda p, c: replace(c, gradient_bytes=None))
    with pytest.raises(ValueError, match='gradient'):
        broken.run(**inputs)
    assert len(events) == 2


def test_spin_ledger_and_nonembedded_gradient_supported_without_ignoring_field():
    t, _ = theory()
    energy, grad = t.run(current_coords=[[0., 0., 0.]], elems=['H'], charge=0, mult=2, Grad=True)
    assert energy == 0 and grad.shape == (1, 3)
    p = t.last_observation.plan
    assert p.unpaired_electrons == p.all_electron_count == p.valence_electron_count == 1
    assert p.pcem_bytes is None and p.native_field_ids == ()
    with pytest.raises(ValueError, match='electron ledger'):
        t.run(current_coords=[[0., 0., 0.]], elems=['H'], charge=0, mult=1)
    with pytest.raises(ValueError, match='ignore'):
        t.run(current_coords=[[0., 0., 0.]], elems=['H'], charge=0, mult=2, MMcharges=[.1])


def test_executor_exception_consumes_reservation_without_retry_or_new_locator():
    t, events = theory(maximum_callbacks=1)

    def refused(p):
        events.append(('execute', p))
        raise RuntimeError('caller retained its operational failure sidecar')

    t.executor = refused
    with pytest.raises(RuntimeError):
        t.run(**original_inputs())
    assert t.callback_reservations == 1 and len(events) == 1
    with pytest.raises(ValueError, match='ceiling'):
        t.run(**original_inputs())
    assert len(events) == 1 and events[0][1].execution_id == 'call-0001'


@pytest.mark.parametrize('changes', [
    {'numcores': 2}, {'numcores': True}, {'mult': True}, {'charge': .0},
    {'MMcharges': [.1, 0.]}, {'qm_elems': ['H']},
    {'current_coords': [[float('nan'), 0., 0.], [1., 0., 0.]]},
    {'current_coords': [[np.complex128(1+1j), 0., 0.], [1., 0., 0.]]},
    {'MMcharges': [np.bool_(True), 0., -.1]},
    {'current_coords': [[1., 0., 0., 4.], [1., 0., 0.]]},
    {'current_MM_coords': [[.52917726, 0., 0.], [0., 20., 0.], [0., 30., 0.]]},
])
def test_invalid_inputs_refuse_before_any_executor_reservation(changes):
    t, events = theory()
    with pytest.raises(ValueError):
        t.run(**dict(original_inputs(), **changes))
    assert events == [] and t.callback_reservations == 0


def test_conversion_is_decimal_context_independent_and_locators_are_explicit():
    with localcontext() as ctx:
        ctx.prec = 6
        actual = r.native_gradient_to_ash(D(2))
    with localcontext() as ctx:
        ctx.prec = 50
        assert actual == D(2)*r.ASH_ANGSTROM_PER_BOHR/r.ANGSTROM_PER_BOHR
    with pytest.raises(ValueError):
        r.native_gradient_to_ash(D('Infinity'))
    with pytest.raises(ValueError):
        r.StrictQmmmXtbTheoryV1(executable_path='/x/../bin/xtb', parameter_path='/p', output_root='/o',
                              executor=lambda p: None, retain_capture=lambda p, c: None)
    t, events = theory()
    t.run(**original_inputs());t.run(**original_inputs())
    assert [row[1].output_locator for row in events if row[0] == 'execute'] == ['/selected/output/call-0001', '/selected/output/call-0002']
    assert sha256(t.last_observation.plan.coordinate_bytes).hexdigest()


def test_fresh_process_import_needs_no_native_or_numpy_and_has_no_io_lookup():
    source_root = Path(__file__).resolve().parents[1]/'src'
    code = f'''import sys, importlib.abc
sys.path.insert(0, {str(source_root)!r})
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self, fullname, path=None, target=None):
  if fullname.split('.')[0] in ('numpy','ash','openmm','xtb','geometric','pyscf'):
   raise AssertionError('native/numerical import: '+fullname)
sys.meta_path.insert(0, Guard())
from empirical_lawhood.adapters.simulators.rubisco_electronic import rr_qmmm_xtb
assert rr_qmmm_xtb.MAXIMUM_CALLBACKS == 120
'''
    result = subprocess.run([sys.executable, '-c', code], check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
