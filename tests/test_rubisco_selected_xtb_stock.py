# SPDX-License-Identifier: MPL-2.0
"""Exposed stock-selection controls; no native engine or qualification."""
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
import ast

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.contracts import SourceMember
from empirical_lawhood.adapters.methods.rubisco_insilico_free_energy import prospective_xtb as x
from empirical_lawhood.infrastructure.isolated_native_subwork import _file_sha256
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from tests.test_rubisco_rr_qmmm_xtb import native_capture

D = Decimal
COMMIT = '1' * 40


def member(name, path, raw):
    return SourceMember(name, str(path), sha256(raw.encode()).hexdigest(), raw)


def row(path, raw, *, digest=None):
    return {'path': str(path), 'size_bytes': len(raw.encode()),
            'sha256': sha256(raw.encode()).hexdigest() if digest is None else digest}


def stock(tmp_path, *, change=lambda proof, terminal: None, version=None, unit=None):
    """Declared fixture metadata, never an independently admitted native stock."""
    binary = tmp_path / '000-xtb'
    binary.write_text('DISCLOSED_EXPOSED_BYTES_NOT_A_NATIVE_ENGINE')
    version = version or f'xtb version 6.7.1 ({COMMIT}) compiled for exposed source control\n'
    unit = unit or 'real(wp), parameter :: autoaa = 0.52917726_wp\n'
    terminal = {'exit_code': 0, 'tool_authoritatively_terminal': True, 'selected_source_commit': COMMIT}
    paths = {name: tmp_path / name for name in ('stock.json', 'version.txt', 'unit.f90', 'terminal.json')}
    proof = {'schema': 'el.xtb.official-upstream-native-stock.v1', 'source_commit': COMMIT,
             'stock_root': str(tmp_path / 'native-stock'),
             'qualification_operands': {
                 'executable': row(binary, binary.read_text()),
                 'parameter': row(tmp_path / 'param', 'DECLARED_ONLY', digest=x.PARAMETER_SHA256),
                 'unit_source': row(paths['unit.f90'], unit),
                 'native_unit_angstrom_per_bohr': '0.52917726',
                 'library_closure': {key: row(tmp_path / (key + '.txt'), 'DECLARED_ONLY')
                                     for key in ('elf_dynamic', 'elf_header', 'elf_program_headers', 'ldd')}},
             'metadata_processes': [{'argv': [str(binary), '--version'], 'return_code': 0,
                                     'stdout': row(paths['version.txt'], version)}],
             'runtime_external_members': [{'selected_path': str(tmp_path / 'lib.so'),
                                          'resolved_path': str(tmp_path / 'lib.so'),
                                          'size_bytes': 1, 'sha256': 'a' * 64}]}
    change(proof, terminal)
    terminal_text = json.dumps(terminal, sort_keys=True)
    proof['known_build_terminal'] = row(paths['terminal.json'], terminal_text)
    documents = {'stock.json': json.dumps(proof, sort_keys=True), 'version.txt': version,
                 'unit.f90': unit, 'terminal.json': terminal_text}
    for name, raw in documents.items():
        paths[name].write_text(raw)
    return x.SelectedXtbStockV1('stock.exposed.source-built',
                               *(member('source.exposed.' + name, paths[name], documents[name])
                                 for name in documents))


def operands(selected, *, embedded=True):
    executable, parameter, _, _, _ = x._stock_projection(selected)
    atoms = (x.NativeAtomV1('qm.h', 'H', (D('0'), D('-0'), D('0'))),)
    fields = (x.NativeFieldRowV1('pc.nonzero', (D('1'), D('2'), D('3')), Fraction(1, 10)),
              x.NativeFieldRowV1('pc.zero', (D('0'), D('0'), D('0')), Fraction())) if embedded else ()
    return ('call-0001', '/selected/output/call-0001', executable[0], parameter[0], atoms, fields, 0, 1, embedded)


def test_selected_stock_roundtrip_has_exact_source_bytes_and_complete_file_bindings(tmp_path):
    selected = stock(tmp_path)
    raw = selected.canonical_bytes()
    assert decode_canonical_bytes(raw, x.SelectedXtbStockV1, maximum_bytes=len(raw)) == selected
    assert selected.identity.object_fingerprint == sha256(raw).hexdigest()
    assert len(selected.file_bindings) == 11  # four sources, binary/parameter, one runtime, four closure rows
    assert len({r[0] for r in selected.file_bindings}) == 11
    assert selected.stock_proof.raw_utf8 == (tmp_path / 'stock.json').read_text()


@pytest.mark.parametrize('embedded', (False, True))
def test_v2_identity_and_all_original_native_bytes_remain_exact(tmp_path, embedded):
    selected = stock(tmp_path)
    args = operands(selected, embedded=embedded)
    args = (*args[:2], '/selected/bin/xtb', '/selected/param', *args[4:])
    # Load the exact immutable original owner where retained locally; portable
    # assertions below also freeze the original identity construction explicitly.
    current = x.XtbSinglePointPlanV2(*args)
    payload = {'model_id': x.MODEL_ID, 'execution_id': current.execution_id,
               'output_locator': current.output_locator, 'argv': current.program_argv,
               'binary': 'debf27a9e0fa4bfb5ca75aafe4b90d8211f08ec2f4a482f375a4987212eaa12a',
               'parameters': x.PARAMETER_SHA256,
               'qm': [(a.atom_id, a.element, tuple(str(v) for v in a.coordinates_angstrom)) for a in current.atoms],
               'field': [(r.atom_id, tuple(str(v) for v in r.coordinates_angstrom),
                          r.exact_charge.numerator, r.exact_charge.denominator) for r in current.field_rows],
               'files': [(n, sha256(raw).hexdigest()) for n, raw in current.input_files]}
    assert current.identity == sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    assert (current.release_tag, current.runtime_build) == ('6.7.1', 'edcfbbe')
    original = Path('/tmp/el-domain-entry-audit-20261011/selected-prefix-source02/src/empirical_lawhood/adapters/methods/rubisco_insilico_free_energy/prospective_xtb.py')
    if original.is_file():
        assert sha256(original.read_bytes()).hexdigest() == '641f8a0138223d84081c07d787813fedde0554ac07165277ec02672ad882766c'
        name = 'tests._immutable_original_prospective_xtb'
        spec = importlib.util.spec_from_file_location(name, original)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
            old = module.XtbSinglePointPlanV2(*args)
            assert {n: getattr(old, n) for n in old.__dataclass_fields__} == {
                n: getattr(current, n) for n in current.__dataclass_fields__}
        finally:
            sys.modules.pop(name, None)


@pytest.mark.parametrize('change,match', (
    (lambda p, t: p.update(schema='UNSUPPORTED'), 'source/build proof'),
    (lambda p, t: p['qualification_operands']['parameter'].update(sha256='b' * 64), 'parameter bytes'),
    (lambda p, t: p['metadata_processes'][0].update(return_code=1), 'version observation'),
    (lambda p, t: p.update(runtime_external_members=[]), 'runtime file census'),
    (lambda p, t: p['qualification_operands']['library_closure'].pop('ldd'), 'loader closure'),
    (lambda p, t: t.update(exit_code=1), 'build terminal'),
    (lambda p, t: t.update(exit_code=False), 'build terminal'),
    (lambda p, t: t.update(selected_source_commit='2' * 40), 'build terminal'),
))
def test_selected_stock_cannot_override_or_omit_original_evidence(tmp_path, change, match):
    with pytest.raises(ValueError, match=match):
        stock(tmp_path, change=change)


def test_source_version_and_unit_must_follow_actual_stock_sources(tmp_path):
    with pytest.raises(ValueError, match='source/build'):
        stock(tmp_path, version='xtb version 6.7.1 (edcfbbe)\n')
    with pytest.raises(ValueError, match='native gradient/coordinate unit'):
        stock(tmp_path, unit='real(wp), parameter :: autoaa = 0.5_wp\n')


def capture(plan):
    old = native_capture(plan)
    fields = {name: getattr(old, name) for name in old.__dataclass_fields__}
    fields['stdout'] = old.stdout.replace(b'(edcfbbe)', ('(' + plan.runtime_build + ')').encode())
    return x.XtbSinglePointCaptureV2(**fields)


def test_new_stock_binds_exact_plan_capture_and_old_banner_refuses(tmp_path):
    selected = stock(tmp_path)
    plan = x.XtbSinglePointPlanV3(*operands(selected), selected_stock=selected)
    old = x.XtbSinglePointPlanV2(*operands(selected))
    assert plan.input_files == old.input_files and plan.program_argv == old.program_argv
    assert plan.identity != old.identity and plan.binary_sha256 != old.binary_sha256
    assert (plan.release_tag, plan.runtime_build) == ('6.7.1', COMMIT)
    observed = x.XtbSinglePointObservationV2(plan, capture(plan))
    assert len(observed.pc_gradient_native) == 2 and observed.pc_gradient_native[1] == (D(0),) * 3
    wrong = replace(capture(plan), stdout=capture(plan).stdout.replace(COMMIT.encode(), b'edcfbbe'))
    with pytest.raises(ValueError, match='native release'):
        x.XtbSinglePointObservationV2(plan, wrong)
    with pytest.raises(ValueError, match='selected executable/parameter path'):
        replace(plan, executable_path='/wrong/bin/xtb')


def test_actual_callback_selects_v3_and_retains_complete_capture_before_new_banner_guard(tmp_path):
    selected = stock(tmp_path)
    args = operands(selected)
    events = []
    def execute(plan):
        events.append(('execute', plan))
        return capture(plan)
    def retain(plan, returned):
        events.append(('retain', returned))
    callback = x.StrictQmmmXtbTheoryV1(executable_path=args[2], parameter_path=args[3],
        output_root='/selected/output', executor=execute, retain_capture=retain, selected_stock=selected)
    supplied = dict(current_coords=((0.0, -0.0, 0.0),), qm_elems=('H',),
                    current_MM_coords=((1.0, 2.0, 3.0), (0.0, 0.0, 0.0)),
                    MMcharges=(0.1, 0.0), Grad=True, PC=True, charge=0, mult=2)
    callback.run(**supplied)
    assert [row[0] for row in events] == ['execute', 'retain']
    assert type(callback.last_observation.plan) is x.XtbSinglePointPlanV3
    assert callback.last_observation.plan.selected_stock == selected
    assert callback.last_observation.plan.runtime_build == COMMIT
    events.clear()
    def adverse(plan):
        returned = execute(plan)
        return replace(returned, stdout=returned.stdout.replace(COMMIT.encode(), b'edcfbbe'))
    callback.executor = adverse
    with pytest.raises(ValueError, match='native release'):
        callback.run(**supplied)
    assert [row[0] for row in events] == ['execute', 'retain']
    assert callback.callback_reservations == 2 and callback.last_observation is None


def test_real_precontact_source_locator_and_mutation_refuse_before_exposed_executor(tmp_path):
    selected = stock(tmp_path)
    args = operands(selected)
    calls = []
    path, resolved, evidence = next(r for r in selected.file_bindings if r[0] == args[2])
    assert str(Path(path).resolve()) == resolved
    assert _file_sha256(path) == evidence.sha256
    callback = x.StrictQmmmXtbTheoryV1(executable_path=args[2], parameter_path=args[3],
                                      output_root='/selected/output', executor=calls.append,
                                      retain_capture=lambda p, c: None, selected_stock=selected)
    assert callback.callback_reservations == 0 and calls == []
    with pytest.raises(ValueError, match='selected executable/parameter path'):
        x.StrictQmmmXtbTheoryV1(executable_path='/wrong/bin/xtb', parameter_path=args[3],
                                output_root='/selected/output', executor=calls.append,
                                retain_capture=lambda p, c: None, selected_stock=selected)
    Path(path).write_text('MUTATED_EXPOSED_SOURCE')
    assert _file_sha256(path) != evidence.sha256
    # Execute the real prospective caller's effect-free source guard, not a
    # sentinel or a mocked digest. No bootstrap, native method or factory runs.
    caller = Path('/tmp/el-domain-entry-audit-20261011/run-local-ethane-derivatives04.py')
    if caller.is_file():
        tree = ast.parse(caller.read_bytes())
        functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                     and n.name in {'binding', 'authenticate', 'selected_stock_authentication'}]
        assert len(functions) == 3
        namespace = {'Path': Path, 'sha256': sha256}
        exec(compile(ast.Module(body=functions, type_ignores=[]), str(caller), 'exec'), namespace)
        with pytest.raises(ValueError, match='Selected original/frozen bytes changed'):
            namespace['selected_stock_authentication'](selected)
    assert calls == [] and callback.callback_reservations == 0


def test_actual_caller_support_search_refuses_override_and_undeclared_rc(tmp_path):
    selected = stock(tmp_path)
    caller = Path('/tmp/el-domain-entry-audit-20261011/run-local-ethane-derivatives04.py')
    if not caller.is_file():
        return  # Private caller checks supplement the portable domain contract.
    tree = ast.parse(caller.read_bytes())
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'selected_stock_search')
    home = tmp_path / 'native-stock/native'
    namespace = {'Path': Path, 'json': json,
                 'ENTRY_SELECTION': {'xtb_home': str(home), 'xtb_path': str(home / 'share/xtb')}}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(caller), 'exec'), namespace)
    assert namespace['selected_stock_search'](selected) == (str(home), str(home / 'share/xtb'))
    namespace['ENTRY_SELECTION']['xtb_path'] = '/wrong/parameter-search'
    with pytest.raises(ValueError, match='support search'):
        namespace['selected_stock_search'](selected)
    namespace['ENTRY_SELECTION']['xtb_path'] = str(home / 'share/xtb')
    home.mkdir(parents=True)
    (home / '.xtbrc').write_text('UNDECLARED_EXPOSED_RC')
    with pytest.raises(ValueError, match='rc file'):
        namespace['selected_stock_search'](selected)
