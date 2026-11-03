"""Synthetic native-format controls; no authentic context or solver execution."""
from dataclasses import FrozenInstanceError, fields, replace
import json
from types import SimpleNamespace
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
import math
from pathlib import Path
import subprocess
import sys

import pytest

from empirical_lawhood.adapters.simulators.rubisco_electronic import rr_xtb_repair as r

D = Decimal


def contract():
    return r.NativeCoordinateContractV1(
        (r.NativeAtomV1('fixed-h', 'H', (D('0.52917726'), D(0), D(0))),
         r.NativeAtomV1('free-h', 'H', (D('1.05835452'), D(0), D(0)))),
        (r.NativeFieldRowV1('field-positive', (D(10), D(0), D(0)), Fraction(1, 3)),
         r.NativeFieldRowV1('zero-ca', (D(20), D(0), D(0)), Fraction()),
         r.NativeFieldRowV1('field-negative', (D(30), D(0), D(0)), Fraction(-1, 7))),
        ('fixed-h',), 0)


def plan(stage='fixed-optimization', previous=0):
    c = contract()
    return r.XtbStagePlanV1(c, stage, ((D(1), D(0), D(0)), (D(2), D(0), D(0))), previous)


def setup(p):
    total = D(p.native_serialized_field_charge_sum.numerator) / D(p.native_serialized_field_charge_sum.denominator)
    return f'''xtb version 6.7.1 (edcfbbe) compiled on 2024-07-22
 : # electrons 2 :
 : max. iterations 250 :
 : Hamiltonian GFN2-xTB :
 : restarted? false :
 : GBSA solvation false :
 : PC potential true :
 : -> # point charges 2 :
 : -> sum of PC {total:.7f} e :
 : electronic temp. 300 K :
 : accuracy 0.0500000 :
 : net charge 0 :
 : unpaired electrons 0 :
 convergence criteria satisfied after 7 iterations
'''


def opt_stdout(p, cycles=2, energy='-1.000000000000'):
    return (setup(p) + ''' : optimization level verytight :
 : max. optcycles 60 :
 : ANC micro-cycles 20 :
 * 1 fixed atom positions, i.e. in gradient

     #   Z                                   position/Å
     1   1 H     0.5291773     0.0000000     0.0000000

''' + ''.join(f'.............................. CYCLE {i} ....................\n' for i in range(1, cycles + 1))
        + f'''GEOMETRY OPTIMIZATION CONVERGED AFTER {cycles} ITERATIONS
 convergence criteria satisfied after 5 iterations
 | TOTAL ENERGY {energy} Eh |
''').encode()


def gradient_bytes(energy='-1.000000000000', gradients=((D('.03'), D('.04'), D(0)), (D('.12'), D(0), D(0)))):
    norm = math.sqrt(sum(float(v) ** 2 for row in gradients for v in row))
    return (f'$grad\ncycle = 1 SCF energy = {energy} |dE/dxyz| = {norm:.6f}\n'
            + '1.00000000000000 0.00000000000000 0.00000000000000 h\n'
            + '2.00000000000000 0.00000000000000 0.00000000000000 h\n'
            + ''.join(' '.join(format(v, '.13E') for v in row) + '\n' for row in gradients)
            + '$end\n').encode()


def opt_result(p=None, stdout=None, coordinates=None, **kwargs):
    p = plan() if p is None else p
    return r.XtbStageResultV1(p, 0, opt_stdout(p) if stdout is None else stdout, b'normal termination of xtb\n',
                             p.coordinate_bytes if coordinates is None else coordinates, None, '6.7.1', **kwargs)


def grad_result(p=None, energy='-1.000000000000', raw=None):
    p = plan('final-unfixed-gradient', 4) if p is None else p
    stdout = (setup(p) + f' | TOTAL ENERGY {energy} Eh |\n').encode()
    return r.XtbStageResultV1(p, 0, stdout, b'normal termination of xtb\n', p.coordinate_bytes,
                             gradient_bytes(energy) if raw is None else raw, '6.7.1')


def test_legacy_bohr_conversion_is_context_independent_and_fd_chain_rule():
    with localcontext() as ctx:
        ctx.prec = 6
        assert r.angstrom_to_bohr(D('.52917726')) == 1
        assert r.bohr_to_angstrom(D(3)) == D('1.58753178')
        observed = r.gradient_hartree_per_angstrom(D('2'))
    with localcontext() as ctx:
        ctx.prec = 50
        assert observed == D(2) / D('.52917726')
        step = D('.000001')
        # E(x_A)=(x_A / a0)^2/2, x_A=2*a0; symmetric derivative is2/a0.
        x = 2 * D('.52917726')
        fd = (((x+step)/D('.52917726'))**2 - ((x-step)/D('.52917726'))**2) / (4*step)
        assert abs(fd-observed) < D('1e-40')
    with pytest.raises(ValueError):
        r.angstrom_to_bohr(D('NaN'))


def test_selected_gfn2_kernel_uses_arithmetic_hardness_not_singular_point_charge():
    assert r.gfn2_damped_coulomb_kernel(0, 1) == 50
    assert r.gfn2_damped_coulomb_kernel(2, 1) == pytest.approx(1/math.sqrt(4+1/2500))
    assert r.gfn2_damped_coulomb_kernel(2, 1) != .5
    for operands in ((-1, 1), (1, 0), (1, float('nan')), (1, 1, 98)):
        with pytest.raises(ValueError):
            r.gfn2_damped_coulomb_kernel(*operands)


def test_complete_field_is_retained_and_only_exact_zero_rows_omitted():
    p = plan()
    assert len(p.contract.field_rows) == 3
    assert p.native_field_ids == ('field-positive', 'field-negative')
    assert p.excluded_exact_zero_field_ids == ('zero-ca',)
    rows = p.pcem_bytes.decode().splitlines()
    assert rows[0] == '2'
    assert all(row.split()[-1] == '99' for row in rows[1:])
    serialized = sum((Fraction(row.split()[0]) for row in rows[1:]), Fraction())
    assert p.native_serialized_field_charge_sum == serialized
    assert p.native_field_rounding_delta == serialized - Fraction(4, 21)
    assert p.native_field_rounding_delta != 0
    assert D(rows[1].split()[1]) == D(format(r.angstrom_to_bohr(D(10)), '.17E'))


def test_immutable_contract_identity_and_source_boundary():
    c = contract()
    assert c.all_electron_count == c.valence_electron_count == 2
    with pytest.raises(FrozenInstanceError):
        c.formal_charge = -2
    with pytest.raises(ValueError):
        replace(c, atoms=list(c.atoms))
    with pytest.raises(ValueError):
        replace(c, fixed_atom_ids=('fixed-h', 'free-h'))
    with pytest.raises(ValueError):
        replace(c, atoms=(c.atoms[0], c.atoms[0]))
    with pytest.raises(ValueError):
        replace(c, formal_charge=1)
    assert replace(c, atoms=tuple(reversed(c.atoms))).identity != c.identity
    assert tuple(f.name for f in fields(r.XtbRepairSettingsV1) if f.init) == ('optimizer_engine',)
    with pytest.raises(TypeError):
        r.XtbRepairSettingsV1(accuracy=D(1))
    with pytest.raises(ValueError, match='source-bound'):
        r.plan_fixed_optimization(c)
    with pytest.raises(ValueError, match='admitted source'):
        r.RrXtbRepairInputV1(c, b'{}\n')
    with pytest.raises(ValueError, match='coincident'):
        replace(c, field_rows=(r.NativeFieldRowV1('pc', c.atoms[0].coordinates_angstrom, Fraction(1)),))


def lbfgs_plan(stage='fixed-optimization', previous=0):
    return replace(plan(stage, previous), settings=r.XtbRepairSettingsV1(optimizer_engine='lbfgs'))


def lbfgs_stdout(p, cycles=2, energy='-1.000000000000'):
    argv = ('/selected/native/bin/xtb', *p.argv('/selected/native/param_gfn2-xtb.txt'))
    text = opt_stdout(p, cycles, energy).decode()
    text = text.replace(' : optimization level verytight :\n : max. optcycles 60 :\n : ANC micro-cycles 20 :\n',
        ' | L-ANC optimizer |\n : energy convergence 1.0000000E-07 Eh\n'
        ' : grad. convergence 2.0000000E-04 Eh/a0\n : Hessian reset 20 steps\n : LBFGS images 20\n')
    text = text.replace(f'CONVERGED AFTER {cycles} ITERATIONS', f'CONVERGED AFTER {cycles} CYCLES')
    return (' program call : ' + ' '.join(argv) + '\n' + text).encode(), argv


def test_additive_lbfgs_selection_preserves_historical_rf_input_and_identity():
    rf = plan();new = lbfgs_plan()
    assert r.XtbRepairSettingsV1().optimizer_engine == 'rf'
    assert rf.settings.model_id == r.MODEL_ID and new.settings.model_id == r.LBFGS_MODEL_ID
    assert replace(new, settings=r.XtbRepairSettingsV1()) == rf
    assert new.contract == rf.contract
    assert new.coordinate_bytes == rf.coordinate_bytes and new.pcem_bytes == rf.pcem_bytes
    assert new.control_bytes == rf.control_bytes.replace(b' engine=rf\n', b' engine=lbfgs\n')
    assert new.identity != rf.identity
    # Frozen 4b486d... pre-addition owner, evaluated on this synthetic input.
    assert rf.identity == '0191ac5bb9ccbc938c9ffc390304105274537a6f47d03bb0d8993c446b6dd1cf'
    assert plan('final-unfixed-gradient', 4).identity == '40b1d79e28a68662b9674eec23f406d00a99b730d5556445948486b9a3e899f0'
    assert sha256(rf.control_bytes).hexdigest() == 'cd50cc76500264e2b46de15290cc1bc7f5b0ac7bc8aa2b1ace31946e1926d9c0'
    # Selected engine provenance also distinguishes the physically
    # engine-agnostic fresh-gradient plans from the historical RF plans.
    assert lbfgs_plan('final-unfixed-gradient', 4).identity != plan('final-unfixed-gradient', 4).identity
    for value in ('fire', '', True, [], None):
        with pytest.raises(ValueError):r.XtbRepairSettingsV1(optimizer_engine=value)


def test_lbfgs_requires_native_cycles_engine_setup_and_exact_selected_program_call():
    p=lbfgs_plan();stdout,argv=lbfgs_stdout(p)
    admitted=opt_result(p=p,stdout=stdout,expected_program_argv=argv)
    assert admitted.status == 'NATIVE_STAGE_PASSED'
    assert admitted.realized_optimizer_engine == 'lbfgs' and admitted.observed_native_program_call == argv
    assert admitted.native_objective_evaluations == 4 and admitted.realized_anc_cycles == 2
    for bad in (stdout.replace(b'L-ANC optimizer',b'ANC optimizer'),
                stdout.replace(b'AFTER 2 CYCLES',b'AFTER 2 ITERATIONS'),
                stdout.replace(b'Hessian reset 20',b'Hessian reset 10'),
                stdout.replace(b'LBFGS images 20',b'LBFGS images 10'),
                stdout.replace(b'1.0000000E-07',b'5.0000000E-07'),
                stdout.replace(b'--cycles 60',b'--cycles 50')):
        refused=opt_result(p=p,stdout=bad,expected_program_argv=argv)
        assert refused.status == 'NATIVE_STAGE_REFUSED' and refused.native_objective_evaluations is None
    assert opt_result(p=p,stdout=stdout).status == 'NATIVE_STAGE_REFUSED'
    refused=opt_result(p=p,stdout=stdout,expected_program_argv=argv[:-1]+('50',))
    assert refused.status == 'NATIVE_STAGE_REFUSED'
    assert opt_result(stdout=stdout).status == 'NATIVE_STAGE_REFUSED'


def test_lbfgs_fresh_gradient_preserves_exact_selected_settings_without_optimization():
    p=lbfgs_plan();stdout,argv=lbfgs_stdout(p)
    optimization=opt_result(p=p,stdout=stdout,expected_program_argv=argv)
    final=lbfgs_plan('final-unfixed-gradient',optimization.native_objective_evaluations)
    final_argv=('/selected/native/bin/xtb',*final.argv('/selected/native/param_gfn2-xtb.txt'))
    text=(' program call : '+' '.join(final_argv)+'\n'+setup(final)+' | TOTAL ENERGY -1.000000000000 Eh |\n').encode()
    diagnostic=r.XtbStageResultV1(final,0,text,b'normal termination of xtb\n',final.coordinate_bytes,
        gradient_bytes(),'6.7.1',expected_program_argv=final_argv)
    assert diagnostic.status == 'NATIVE_STAGE_PASSED' and diagnostic.realized_optimizer_engine is None
    assert b'$fix' not in final.control_bytes and b'$opt' not in final.control_bytes
    pair=r.XtbRepairPairAssessmentV1(optimization,diagnostic)
    assert pair.status == 'FRESH_SCC_ENERGY_CONSISTENT' and pair.native_objective_evaluations == 5


def test_fixed_roles_keep_both_physical_protons_free_including_unchanged_hb():
    def atom(identity, component, name, element='H'):
        return r.PreparedAtomV1(identity, 'A', 191, component, name, element, (D(0), D(0), D(0)), None, 'synthetic-role-control')
    atoms = (atom('mg', 'MG', 'MG', 'Mg'), atom('cb', 'KCX', 'CB', 'C'), atom('hb', 'KCX', 'HB2'),
             atom('cap', 'CAP', 'HCAP'), atom('p1', 'RUB', 'P1', 'P'), atom('o1', 'RUB', 'O1', 'O'),
             atom('o2', 'RUB', 'O2', 'O'), atom('amber:6901', 'KCX', 'HOQ1'), atom('amber:6900', 'RUB', 'HO3'))
    selected = r.select_fixed_atom_ids(atoms, (('cb', 'hb'), ('o2', 'amber:6901')))
    assert selected == ('mg', 'cb', 'hb', 'cap', 'p1', 'o1')
    assert not {'amber:6900', 'amber:6901'} & set(selected)


def test_stage_inputs_bind_bohr_identity_and_fresh_unfixed_command():
    p = plan()
    assert r.parse_coord(p.coordinate_bytes, p.contract.atoms) == p.coordinates_bohr
    assert p.fixed_atom_indices == (1,)
    assert b'$fix\n atoms: 1\n' in p.control_bytes
    args = p.argv('/selected/share/xtb/param_gfn2-xtb.txt')
    assert args[args.index('--vparam')+1] == '/selected/share/xtb/param_gfn2-xtb.txt'
    assert '--norestart' in args and '--grad' not in args
    g = plan('final-unfixed-gradient', 4)
    assert g.fixed_atom_indices == () and b'$fix' not in g.control_bytes
    assert g.argv('/selected/params')[-1] == '--grad'
    assert '--opt' not in g.argv('/selected/params')
    for path in ('relative/params', '/bad\npath', '/bad\x00path'):
        with pytest.raises(ValueError):
            p.argv(path)


def test_native_coord_and_gradient_require_complete_order_and_finite_tokens():
    p = plan()
    for raw in (p.coordinate_bytes.replace(b'$coord', b'$coord angs'),
                p.coordinate_bytes.replace(b' h\n', b' c\n', 1),
                p.coordinate_bytes.replace(b'1.00000000000000000E+0', b'NaN'),
                b'$coord\n1 0 0 h\n$end\n'):
        with pytest.raises(ValueError):
            r.parse_coord(raw, p.contract.atoms)
    energy, xyz, grads, norm = r.parse_gradient(gradient_bytes(), p.contract.atoms)
    assert energy == -1 and xyz == p.coordinates_bohr
    assert grads == ((D('.03'), D('.04'), D(0)), (D('.12'), D(0), D(0))) and norm == D('.13')
    for raw in (gradient_bytes().replace(b'cycle = 1', b'cycle = 2'),
                gradient_bytes().replace(b'3.0000000000000E-2', b'NaN'),
                gradient_bytes().replace(b'$end', b'0 0 0\n$end')):
        with pytest.raises(ValueError):
            r.parse_gradient(raw, p.contract.atoms)


def test_anc_overshoot_complete_trace_and_source_inferred_inner_convergence():
    p = plan()
    observed = opt_result(p, opt_stdout(p, cycles=99))
    assert observed.status == 'NATIVE_STAGE_PASSED'
    assert observed.realized_anc_cycles == observed.source_inferred_converged_inner_scc_solves == 99
    assert observed.explicit_scc_iterations == (7, 5)
    assert observed.native_objective_evaluations == 101
    assert observed.unmasked_gradient_hartree_per_bohr == ()
    assert observed.energy_hartree == -1
    assert not observed.scientific_geometry_admitted
    for stdout in (opt_stdout(p, 100), opt_stdout(p).replace(b'CYCLE 1', b'CYCLE 2'),
                   opt_stdout(p).replace(b'after 5 iterations', b'after 251 iterations'),
                   opt_stdout(p).replace(b'GEOMETRY OPTIMIZATION CONVERGED AFTER 2 ITERATIONS', b'')):
        assert opt_result(p, stdout).status == 'NATIVE_STAGE_REFUSED'


def test_fixed_table_scope_and_coordinate_preservation_are_independent():
    p = plan()
    # An unrelated numeric table after the completed fixed table is permissible.
    stdout = opt_stdout(p) + b' 7 8 O 1.0 2.0 3.0\n'
    assert opt_result(p, stdout).status == 'NATIVE_STAGE_PASSED'
    assert opt_result(p, stdout.replace(b'1   1 H', b'2   1 H')).status == 'NATIVE_STAGE_REFUSED'
    moved = ((D('1.000000001'), D(0), D(0)), p.coordinates_bohr[1])
    assert opt_result(p, coordinates=r.encode_coord(p.contract.atoms, moved)).status == 'NATIVE_STAGE_REFUSED'
    small_rounding = ((D('1.00000000001'), D(0), D(0)), p.coordinates_bohr[1])
    assert opt_result(p, coordinates=r.encode_coord(p.contract.atoms, small_rounding)).status == 'NATIVE_STAGE_PASSED'


def test_raw_refusals_retain_failures_and_strict_profile_setup():
    p = plan()
    refusal = r.XtbStageResultV1(p, 9, b'partial stdout', b'SCC failed', b'', None, '6.7.1')
    assert refusal.status == 'NATIVE_STAGE_REFUSED' and refusal.stdout == b'partial stdout' and refusal.stderr == b'SCC failed'
    assert refusal.native_objective_evaluations is None
    assert refusal.realized_anc_cycles is None and refusal.source_inferred_converged_inner_scc_solves is None
    marker = opt_result(p, native_failure_files=(('.sccnotconverged', b'original-marker'),))
    assert marker.status == 'NATIVE_STAGE_REFUSED' and marker.native_failure_files[0][1] == b'original-marker'
    for changed in (b'6.7.0 (edcfbbe)', b'6.7.1 (26b2801)'):
        assert opt_result(p, opt_stdout(p).replace(b'6.7.1 (edcfbbe)', changed)).status == 'NATIVE_STAGE_REFUSED'
    for original, changed in ((b'net charge 0', b'net charge -2'), (b'# electrons 2', b'# electrons 14'),
                              (b'GFN2-xTB', b'GFN1-xTB'), (b'PC potential true', b'PC potential false'),
                              (b'restarted? false', b'restarted? true'), (b'GBSA solvation false', b'GBSA solvation true'),
                              (b'0.1904762 e', b'0.2904762 e')):
        assert opt_result(p, opt_stdout(p).replace(original, changed)).status == 'NATIVE_STAGE_REFUSED'


def test_unfixed_gradient_preserves_nonzero_fixed_forces_and_independent_statistics():
    result = grad_result()
    assert result.status == 'NATIVE_STAGE_PASSED'
    assert result.unmasked_gradient_hartree_per_bohr[0] == (D('.03'), D('.04'), D(0))
    assert result.full_gradient_norm_hartree_per_bohr == pytest.approx(.13)
    assert result.fixed_gradient_norm_hartree_per_bohr == pytest.approx(.05)
    assert result.free_gradient_norm_hartree_per_bohr == pytest.approx(.12)
    assert result.free_gradient_rms_hartree_per_bohr == pytest.approx(.12/math.sqrt(3))
    assert result.free_gradient_maximum_component_hartree_per_bohr == .12
    assert result.parser_native_executions == 0 and not result.scientific_geometry_admitted
    raw = gradient_bytes().replace(b'|dE/dxyz| = 0.130000', b'|dE/dxyz| = 0.120000')
    assert grad_result(raw=raw).status == 'NATIVE_STAGE_REFUSED'
    assert grad_result(raw=gradient_bytes().replace(b'1.00000000000000', b'1.00000000100000')).status == 'NATIVE_STAGE_REFUSED'
    p = plan('final-unfixed-gradient', 119)
    assert grad_result(p).status == 'NATIVE_STAGE_PASSED'
    p = plan('fixed-optimization', 119)
    assert opt_result(p).status == 'NATIVE_STAGE_REFUSED'


def test_fresh_recalculation_requires_same_join_and_energy_agreement():
    opt = opt_result()
    diag = grad_result()
    pair = r.XtbRepairPairAssessmentV1(opt, diag)
    assert pair.status == 'FRESH_SCC_ENERGY_CONSISTENT' and pair.native_objective_evaluations == 5
    assert pair.energy_difference_hartree == 0 and not pair.scientific_geometry_admitted
    disagreed = r.XtbRepairPairAssessmentV1(opt, grad_result(energy='-0.999998000000'))
    assert disagreed.status == 'RECALC_DISAGREEMENT' and disagreed.energy_difference_hartree == D('.000002')
    with pytest.raises(ValueError):
        r.XtbRepairPairAssessmentV1(opt, grad_result(plan('final-unfixed-gradient', 3)))
    refused = grad_result(raw=b'partial raw gradient')
    pair = r.XtbRepairPairAssessmentV1(opt, refused)
    assert pair.status == 'NATIVE_STAGE_REFUSED' and pair.native_objective_evaluations is None
    missing_term = r.XtbStageResultV1(diag.plan, 0, diag.stdout, b'', diag.coordinate_bytes, diag.gradient_bytes, '6.7.1')
    assert missing_term.status == 'NATIVE_STAGE_REFUSED' and missing_term.native_objective_evaluations is None


def test_cold_import_refuses_optional_native_and_execution_imports():
    owner = str(Path(r.__file__).resolve())
    script = '''import importlib.abc, importlib.util, sys
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self, fullname, path=None, target=None):
  if fullname.split('.')[0] in {'numpy','pyscf','openmm','simtk','parmed','pdbfixer','Bio','rapidfuzz','subprocess'}:
   raise AssertionError('cold native/effect import: '+fullname)
sys.meta_path.insert(0,Guard())
spec=importlib.util.spec_from_file_location('cold_xtb_repair',sys.argv[1])
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
assert module.XtbRepairSettingsV1().native_effects == 0
'''
    checked = subprocess.run([sys.executable, '-c', script, owner], check=False, capture_output=True, text=True)
    assert checked.returncode == 0, checked.stderr


def test_closed_projection_uses_context_source_api_and_exact_native_token_bytes():
    """Independent synthetic layout, with no authentic context construction."""
    from empirical_lawhood.adapters.physical.rubisco_kinetics import rr_coupled_preparation as p
    atom = p.PreparedAtomV1('synthetic-H', 'A', 1, 'RUB', 'H', 'H',
                            (D('1.0000'), D('-0E-7'), D('2.50')), 1, 'synthetic-coordinate')
    cap = p.PreparedAtomV1('synthetic-cap', 'A', 1, 'CAP', 'HL', 'H',
                           (D('3.000'), D('0'), D('4.00')), None, 'synthetic-link')
    transfer = p.ProtonTransferV1('synthetic-transfer', 'synthetic-H', 'old', 'new', 'old',
        (D('0.000'), D('1.0'), D('2.00')), atom.coordinates)
    geometry = p.EnolateGeometryV1(1.6, (('a', 120.0),), (('b', .5),), 50.0, .7, ('synthetic-unready',))
    c = SimpleNamespace(source=SimpleNamespace(source_bindings=(('synthetic-source', 7, '0'*64),)),
        variant='synthetic-layout', proton_view='V2', protocol_sha256='1'*64, physical_atoms=(atom,),
        quantum_atoms=(atom, cap), environment_atoms=(), candidate_bonds=(('synthetic-H', 'synthetic-cap'),),
        candidate_qm_lewis_bonds=(('synthetic-H', 'synthetic-cap', 1),),
        candidate_qm_formal_charges=(('synthetic-H', 0), ('synthetic-cap', 0)),
        removed_parent_atom_indices=(9,), changed_atom_ids=('synthetic-H',), mutation_audits=(),
        proton_transfers=(transfer,), caps=(), formula=(('H', 2),), formal_quantum_charge=0, electron_count=2,
        enolate_geometry=geometry, changed_atom_contacts=(),
        nearest_quantum_environment_pair=('synthetic-H', 'synthetic-env', 1.0), status='GEOMETRY_UNREADY',
        failures=('synthetic-unready',), inventory_passed=True, executable_mm_hamiltonian=False,
        exact_assay_parent_admitted=False, ground_state_certified=False, selected_singlet_hypothesis=True, native_effects=0)
    assert not hasattr(c, 'source_bindings')
    expected = {
        'role': 'unrelaxed-initial-coupled-inventory-not-a-ready-QM-job', 'variant': 'synthetic-layout',
        'proton_view': 'V2', 'protocol_sha256': '1'*64, 'source_bindings': [['synthetic-source', 7, '0'*64]],
        'atom_columns': ['atom_id', 'author_chain', 'author_position', 'component', 'atom_name', 'element',
            'current_x_decimal', 'current_y_decimal', 'current_z_decimal', 'parent_atom_index',
            'coordinate_and_recipe_origin', 'donor_atom_index'],
        'atom_rows': [['synthetic-H', 'A', 1, 'RUB', 'H', 'H', '1.0000', '-0E-7', '2.50', 1, 'synthetic-coordinate', None],
            ['synthetic-cap', 'A', 1, 'CAP', 'HL', 'H', '3.000', '0', '4.00', None, 'synthetic-link', None]],
        'physical_atom_ids': ['synthetic-H'], 'quantum_atom_ids': ['synthetic-H', 'synthetic-cap'],
        'environment_atom_ids': [], 'candidate_bonds': [['synthetic-H', 'synthetic-cap']],
        'candidate_qm_lewis_bonds': [['synthetic-H', 'synthetic-cap', 1]],
        'candidate_qm_formal_charges': [['synthetic-H', 0], ['synthetic-cap', 0]],
        'removed_parent_atom_indices': [9], 'changed_atom_ids': ['synthetic-H'], 'mutation_audits': [],
        'proton_transfers': [{'identity': 'synthetic-transfer', 'atom_id': 'synthetic-H', 'previous_donor_id': 'old',
            'new_acceptor_id': 'new', 'placement_direction_previous_donor_id': 'old',
            'original_coordinates': ['0.000', '1.0', '2.00'], 'new_coordinates': ['1.0000', '-0E-7', '2.50']}],
        'caps': [], 'formula': [['H', 2]], 'formal_quantum_charge': 0, 'electron_count': 2,
        'enolate_geometry': {'c2_c3_angstrom': 1.6, 'trigonal_angles_degrees': [['a', 120.0]],
            'plane_displacements_angstrom': [['b', .5]], 'signed_o2_c2_c3_o3_dihedral_degrees': 50.0,
            'cis_projected_dot_angstrom_squared': .7, 'failures': ['synthetic-unready']},
        'changed_atom_contacts': [], 'nearest_quantum_environment_pair': ['synthetic-H', 'synthetic-env', 1.0],
        'status': 'GEOMETRY_UNREADY', 'failures': ['synthetic-unready'], 'inventory_passed': True,
        'executable_mm_hamiltonian': False, 'exact_assay_parent_admitted': False, 'ground_state_certified': False,
        'selected_singlet_hypothesis': True, 'native_effects': 0}
    independent_bytes = (json.dumps(expected, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()
    assert r._rawjson(r._closed_context_document(c)) == independent_bytes
    assert r._rawjson(r._closed_context_document(c)) != independent_bytes.replace(b'1.0000', b'1.0')
