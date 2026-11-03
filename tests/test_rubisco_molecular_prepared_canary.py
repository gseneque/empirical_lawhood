# SPDX-License-Identifier: MPL-2.0
"""Two exposed executable doubles reach actual scientific interfaces and custody.

Neither Amber nor xTB is executed by these tests. Actual canary entry is a
separate root-owned development control; no Gp/backend qualification is claimed.
"""

from dataclasses import replace
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys

import pytest

from empirical_lawhood.adapters.methods import isolated_native_conformance
from empirical_lawhood.adapters.methods.isolated_native_conformance import ExposedIsolatedNativeRunner
from empirical_lawhood.adapters.methods.rubisco_insilico_free_energy import prospective_xtb as xtb, raw_coupled_return as raw
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor, TaskProcessError
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.native_subwork import NativeSubworkState
from empirical_lawhood.runtime.isolated_native_subwork import IsolatedNativeEntryReturn, IsolatedNativeEntrySelection
from tests.fixtures.rubisco import molecular_prepared_canary as child, molecular_prepared_canary_readback as independent, molecular_prepared_canary_control as control
from tests.runtime_platform.test_native_subwork import _plane, _store, _process_context


VISIBILITY = VisibilityCeiling.DEVELOPMENT_ONLY
ACCESS = OutcomeAccess.DEVELOPMENT_VISIBLE
LARGE_BYTES = 16 * 1024 * 1024


def _selected_source():
    """Retain actual checkout bytes; do not create an executable source copy."""
    root = Path(__file__).resolve().parents[1]
    package = root / 'src/empirical_lawhood'
    paths = {path for path in package.rglob('*')
        if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc'}
    paths.update(Path(module.__file__).resolve() for module in (child, independent, control))
    census = tuple((path.relative_to(root).as_posix(), sha256(path.read_bytes()).hexdigest())
        for path in sorted(paths))
    return root, census


def _stock(tmp_path, known_failure=None):
    root = tmp_path / 'exposed-engine'
    tleap = root / 'ambertools24-tleap/bin/teLeap'
    tleap.parent.mkdir(parents=True)
    # All returned atom/residue/parameter text is explicitly a software double.
    tleap.write_text('#!' + sys.executable + '\n' + '''
from pathlib import Path
import sys
assert sys.argv[-2:]==['-f','tleap.in']
assert len(sys.argv)==7 and all(v.startswith('-I') for v in sys.argv[1:5])
assert Path('tleap.in').read_text().endswith('quit\\n')
tables={'POINTERS':[0]*31,'ATOM_NAME':['C','CA','N','C','N','O'],
    'AMBER_ATOM_TYPE':['CT']*6,'CHARGE':[0.0]*6,'MASS':[12.0]*6,'ATOM_TYPE_INDEX':[1]*6,
    'NUMBER_EXCLUDED_ATOMS':[0]*6,'RESIDUE_LABEL':['ACE','ALA','GLY','ALA','NME','WAT'],
    'RESIDUE_POINTER':[1,2,3,4,5,6],'BOND_FORCE_CONSTANT':[0.0]}
tables['POINTERS'][0]=6;tables['POINTERS'][11]=6;tables['POINTERS'][27]=1
rows=['%VERSION EXPOSED_EXECUTABLE_DOUBLE NEVER_QUALIFICATION\\n']
for name,values in tables.items():
    kind='A' if isinstance(values[0],str) else 'E' if isinstance(values[0],float) else 'I'
    repeat,width=(20,4) if kind=='A' else (5,16) if kind=='E' else (10,8)
    rows+=['%FLAG '+name+'\\n',f'%FORMAT({repeat}{kind}{width}'+('.8' if kind=='E' else '')+')\\n']
    fields=[f'{v:<4}' if kind=='A' else f'{v:16.8E}' if kind=='E' else f'{v:8d}' for v in values]
    rows+=[''.join(fields[i:i+repeat])+'\\n' for i in range(0,len(fields),repeat)]
Path('model.prmtop').write_text(''.join(rows))
xyz=[v for i in range(6) for v in (float(i),0.0,0.0)]+[20.,20.,20.,90.,90.,90.]
Path('model.inpcrd').write_text('EXPOSED_EXECUTABLE_DOUBLE\\n6\\n'+''.join(''.join(f'{v:12.7f}' for v in xyz[i:i+6])+'\\n' for i in range(0,len(xyz),6)))
Path('model.pdb').write_text(''.join(f'ATOM  {i+1:5d} {name:^4s} {res:>3s} A{i+1:4d}    {float(i):8.3f}{0.:8.3f}{0.:8.3f}  1.00  0.00           C  \\n' for i,(name,res) in enumerate(zip(tables['ATOM_NAME'],tables['RESIDUE_LABEL']))))
with Path('exposed-large-native-return.bin').open('xb') as stream:
    block=bytes(range(256))*4096
    for _ in range(16):stream.write(block)
print('EXPOSED_EXECUTABLE_DOUBLE Amber-shaped return, not molecular qualification')
''')
    tleap.chmod(0o700)
    files = [tleap]
    for kind in ('prep', 'lib', 'parm', 'cmd'):
        path = root / 'ambertools24-tleap/dat/leap' / kind / 'exposed-selected-stock.dat'
        path.parent.mkdir(parents=True)
        path.write_text('EXPOSED DOUBLE ' + kind)
        files.append(path)
    for name in ('leaprc.protein.ff14SB', 'leaprc.water.tip3p', 'leaprc.gaff2'):
        path = root / 'ambertools24-tleap/dat/leap/cmd' / name
        path.write_text('EXPOSED DOUBLE ' + name)
        files.append(path)
    native = root / 'xtb'
    native.write_text('#!' + sys.executable + '\n' + '''
from pathlib import Path
from decimal import Decimal
import sys
assert sys.argv[1]=='input.coord' and '--grad' in sys.argv and '--norestart' in sys.argv
coords=Path('input.coord').read_text().splitlines()[1:-1]
assert len(coords)==8
rows=['$grad','cycle = 1 SCF energy = -7.00000000000000 |dE/dxyz| = 0.00000000000000']
for row in coords:
    x,y,z,element=row.split()
    rows.append(' '.join(f'{Decimal(v):.14f}' for v in (x,y,z))+' '+element)
for i in range(8):rows.append(' '.join(f'{Decimal(i*3+axis+1)/Decimal(1000):.14E}' for axis in range(3)))
rows.append('$end')
Path('gradient').write_text('\\n'.join(rows)+'\\n')
print('EXPOSED_EXECUTABLE_DOUBLE xTB-shaped single E/G return, not derivative qualification')
''')
    native.chmod(0o700)
    failed_program = tleap if known_failure == 'preparation' else native if known_failure == 'energy-gradient' else None
    if failed_program is not None:
        with failed_program.open('a') as stream:
            stream.write('\nraise SystemExit(77)\n')
    parameter = root / 'param_gfn2-xtb.txt'
    parameter.write_text('EXPOSED DOUBLE PARAMETER STOCK')
    files += [native, parameter]
    inventory = {'selected_engine_root': str(root), 'entries': [dict(kind='file', actual_path=str(path),
        path=path.relative_to(root).as_posix(), size=path.stat().st_size, sha256=sha256(path.read_bytes()).hexdigest()) for path in files]}
    inventory_path = root / 'engine-inventory.json'
    inventory_path.write_text(json.dumps(inventory, sort_keys=True))
    origin = root / 'original-coordinate-input.json'
    coordinates = tuple(tuple(float(v).hex() for v in row) for row in ((-.77,0,0),(.77,0,0),(-1.1,1,0),
        (-1.1,-.5,.9),(-1.1,-.5,-.9),(1.1,1,0),(1.1,-.5,.9),(1.1,-.5,-.9)))
    origin.write_text(json.dumps({'claim': 'EXPOSED_COORDINATE_INPUT_ONLY', 'coordinates_angstrom_hex': coordinates}, sort_keys=True))
    return tleap, native, parameter, inventory_path, origin, coordinates


def _selected(tmp_path, phase, known_failure=None):
    plane = _plane(tmp_path / 'custody')
    source_root, sources = _selected_source()
    tleap, native, parameter, inventory, origin, coordinates = _stock(tmp_path, known_failure)
    selected = child.MolecularPreparedCanarySelection('molecular.canary.selected', str(tmp_path / 'native-work'),
        'EXPOSED_EXECUTABLE_DOUBLE', str(tleap), sha256(tleap.read_bytes()).hexdigest(), str(native), sha256(native.read_bytes()).hexdigest(),
        str(parameter), sha256(parameter.read_bytes()).hexdigest(), str(inventory), sha256(inventory.read_bytes()).hexdigest(),
        coordinates, str(origin), sha256(origin.read_bytes()).hexdigest(), str(source_root), sources,
        sha256((source_root / 'uv.lock').read_bytes()).hexdigest())
    provenance = NumericalProducingProvenance('{"python":"exposed","numpy":"exposed","scipy":"exposed","system":"Linux","machine":"exposed","threadpools":[]}',
        selected.dependency_lock_sha256, sources, sha256(canonical_json_bytes(sources)).hexdigest(), '3' * 40, False)
    bundle, parent, definitions, request, payload = control.prepare_control(plane, selected, provenance,
        run_id='synthetic.molecular.canary', task_id='native.parent', contact_id='synthetic.molecular.canary.attempt-001',
        execution_plan=ObjectIdentity('plan.selected', 'empirical-lawhood/runtime/development-execution-plan', '1.0.0', '1' * 64),
        task_identity=ObjectIdentity('native.parent', 'empirical-lawhood/runtime/execution-task', '1.0.0', '2' * 64),
        visibility=VISIBILITY, access=ACCESS, phase=phase)
    invocation_dir = tmp_path / 'frozen-invocation'
    invocation_dir.mkdir()
    invocation = invocation_dir / 'invocation.json'
    invocation.write_bytes(payload)
    store = _store(plane, parent, bundle.manifests)
    assert store.parent_contacts.read(parent.run_id, parent.task_id) is None
    return plane, bundle, store, selected, request, definitions, invocation_dir, invocation


@pytest.mark.parametrize('phase', ['success', 'after-completion'])
def test_frozen_molecular_interface_full_publication_and_independent_recovery(tmp_path, phase):
    plane, bundle, store, selected, request, definitions, directory, invocation = _selected(tmp_path, phase)
    try:
        store.parent_contacts.begin(definitions[0].parent_contact)
        context = _process_context(store, definitions[0], bundle.manifests)
        for port in context.input_ports:
            port.close()
        context = replace(context, input_bindings=bundle.input_bindings, input_ports=bundle.input_ports)
        runner = ExposedIsolatedNativeRunner(str(invocation), str(directory),
            selected_entry_source=str(Path(child.__file__).resolve()),
            selected_import_root=str(Path(selected.source_root) / 'src'))
        if phase == 'after-completion':
            with pytest.raises(TaskProcessError):
                LocalProcessExecutor(scratch_root=plane.root).execute(runner, context, timeout_seconds=None, native_subwork=store)
        else:
            LocalProcessExecutor(scratch_root=plane.root).execute(runner, context, timeout_seconds=None, native_subwork=store)
        returned_raw = (directory / 'child-return.json').read_bytes()
        returned = decode_canonical_bytes(returned_raw, IsolatedNativeEntryReturn, maximum_bytes=len(returned_raw))
        assert returned.handshake_completed and returned.returncode == (95 if phase == 'after-completion' else 0)
        metadata = isolated_native_conformance.exposed_metadata_definition(definitions[0])
        entry_raw = b''.join(store.iter_completed_output(metadata, 'process.selection'))
        entry = decode_canonical_bytes(entry_raw, IsolatedNativeEntrySelection, maximum_bytes=len(entry_raw))
        assert entry.entry_source_sha256 == dict(selected.code_sources)[Path(child.__file__).resolve().relative_to(Path(selected.source_root)).as_posix()]
        assert entry.invocation_sha256 == sha256(invocation.read_bytes()).hexdigest()
        assert all(sha256((Path(selected.source_root) / path).read_bytes()).hexdigest() == digest for path, digest in selected.code_sources)
        destination = tmp_path / 'relocated-custody'
        shutil.copytree(plane.root.contract.canonical_path, destination)
        reader = _store(_plane(destination), definitions[0].parent_contact)
        before = tuple(reader.recover(row) for row in definitions)
        contact_files = tuple(sorted(destination.rglob('contact')))
        reports = []
        for definition in definitions:
            assert reader.inspect(definition).state is NativeSubworkState.COMPLETED
            census = b''.join(reader.iter_completed_output(definition, 'files.census'))
            names = ('input.coord', 'gradient', 'selected-command.json', 'subprocess-return.json') if definition.subwork_id.endswith('energy-gradient') else ('model.prmtop', 'model.inpcrd', 'model.pdb', 'selected-command.json', 'subprocess-return.json')
            archive = independent.authenticate_archive(reader.iter_completed_output(definition, 'files.raw', maximum_chunk_bytes=65536), census, definition.subwork_id, names)
            files = archive['files']
            command, result = json.loads(files['selected-command.json']), json.loads(files['subprocess-return.json'])
            assert command['argv'] == result['argv'] and result['returncode'] == 0
            if definition.subwork_id.endswith('energy-gradient'):
                independent.authenticate_coordinate_input(files['input.coord'], selected.coordinates_angstrom_hex)
                energy, gradient = independent.read_gradient(files['input.coord'], files['gradient'])
                capture = json.loads(b''.join(reader.iter_completed_output(definition, 'raw.return')))['value']
                assert capture['request'] == json.loads(request.identity.canonical_bytes())
                assert capture['capture_failures'] == []
                energy_capture = independent.record_value(capture['energy'], raw.RawArrayCapture.SCHEMA)
                gradient_capture = independent.record_value(capture['gradient'], raw.RawArrayCapture.SCHEMA)
                independent.authenticate_array(reader.iter_completed_output(definition, 'raw.energy'), energy_capture, (), (energy,))
                converted = tuple(value * Fraction('0.5291772109303') / Fraction('0.52917726') for row in gradient for value in row)
                independent.authenticate_array(reader.iter_completed_output(definition, 'raw.gradient'), gradient_capture, (8, 3), converted)
                assert len(gradient) == 8 and sum(map(len, gradient)) == 24
                assert command['argv'][0] == selected.xtb_path
                assert '--grad' in command['argv'] and '--norestart' in command['argv']
                assert command['environment'] == dict(PATH='/usr/bin:/bin', LC_ALL='C', LANG='C', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
            else:
                report = independent.read_amber(files['model.prmtop'], files['model.inpcrd'], files['model.pdb'])
                assert report['atom_count'] == 6 and report['coordinate_components'] == 18
                assert 'exposed-large-native-return.bin' in archive['names'] and archive['byte_count'] > LARGE_BYTES
                assert command['argv'][0] == selected.tleap_path and command['argv'][-2:] == ['-f', 'tleap.in']
                assert [Path(value[2:]).name for value in command['argv'][1:5]] == ['prep', 'lib', 'parm', 'cmd']
            unit = json.loads(b''.join(reader.iter_completed_output(definition, 'unit.return')))['value']
            assert unit['known_return'] and unit['preparation_succeeded'] and len(unit['native_calls']) == 1
            reports.append(dict(unit=definition.subwork_id, members=archive['member_count'], bytes=archive['byte_count']))
        assert tuple(reader.recover(row) for row in definitions) == before
        full_report = independent.read_completed_control(reader, definitions, selected, request)
        assert full_report['full_native_definition_count'] == 8 and full_report['actual_native_calls'] == 2
        assert full_report['complete_gradient_components'] == 24 and full_report['actual_scientific_admission'] == 'NOT_ATTEMPTED'
        assert tuple(sorted(destination.rglob('contact'))) == contact_files
        with pytest.raises(ValueError, match='already completed'):
            reader.begin(definitions[0], bundle.manifests)
        (tmp_path / 'independent-readback.json').write_text(json.dumps(dict(claim='EXPOSED_INTERFACE_ACCEPTANCE_ONLY', phase=phase,
            full_gradient_components=24, whole_physical_atoms=8, prepared_units=2, native_calls=2, readback=reports), sort_keys=True))
    finally:
        bundle.close()


@pytest.mark.parametrize('fault', ['missing-row', 'extra-row', 'nonfinite', 'element', 'coordinate'])
def test_independent_literal_reader_refuses_incomplete_or_changed_whole8_return(fault):
    coords = '$coord\n' + ''.join(f'{index} 0 0 ' + ('c' if index < 2 else 'h') + '\n' for index in range(8)) + '$end\n'
    gradient = '$grad\ncycle = 1 SCF energy = -7 |dE/dxyz| = 0\n' + ''.join(f'{index} 0 0 ' + ('c' if index < 2 else 'h') + '\n' for index in range(8)) + '0 0 0\n' * 8 + '$end\n'
    if fault == 'missing-row': gradient = gradient.replace('0 0 0\n', '', 1)
    elif fault == 'extra-row': gradient = gradient.replace('$end', '0 0 0\n$end')
    elif fault == 'nonfinite': gradient = gradient.replace('energy = -7', 'energy = NaN')
    elif fault == 'element': gradient = gradient.replace('0 0 0 c', '0 0 0 h')
    else: gradient = gradient.replace('0 0 0 c', '0.1 0 0 c')
    with pytest.raises(ValueError): independent.read_gradient(coords.encode(), gradient.encode())


@pytest.mark.parametrize('fault', ['coordinates', 'component-count', 'point-charge', 'claim', 'source-root'])
def test_tiny_selected_protocol_refuses_false_scientific_scope(tmp_path, fault):
    _, bundle, _, selected, _, _, _, _ = _selected(tmp_path, 'success')
    try:
        change = {'coordinates': dict(coordinates_angstrom_hex=selected.coordinates_angstrom_hex[:-1]),
            'component-count': dict(gradient_component_denominator=21), 'point-charge': dict(point_charge_count=2),
            'claim': dict(scientific_claim='GP_QUALIFICATION'), 'source-root': dict(source_root='../outside')}[fault]
        with pytest.raises(ValueError): replace(selected, **change)
    finally: bundle.close()


def test_reader_source_is_independent_of_native_or_producer_imports():
    source = Path(independent.__file__).read_text()
    import ast
    for row in ast.walk(ast.parse(source)):
        if isinstance(row, ast.Import):
            assert all(name.name.split('.')[0] in sys.stdlib_module_names for name in row.names)
        elif isinstance(row, ast.ImportFrom):
            assert row.module.split('.')[0] in sys.stdlib_module_names
    assert independent.NATIVE_ANGSTROM_PER_BOHR == Fraction(xtb.ANGSTROM_PER_BOHR)
    assert independent.ASH_ANGSTROM_PER_BOHR == Fraction(xtb.ASH_ANGSTROM_PER_BOHR)


@pytest.mark.parametrize('fault', ['code', 'lock', 'executable', 'parameter', 'extra-search-stock', 'source-origin', 'self-consistent-changed-origin'])
def test_selected_child_refuses_real_source_or_stock_change_before_any_native_begin(tmp_path, monkeypatch, fault):
    _, bundle, _, selected, _, _, _, invocation = _selected(tmp_path, 'success')
    data = json.loads(invocation.read_bytes())
    substituted_reads = []
    original_source_sha256 = None
    try:
        if fault in ('code', 'lock'):
            path = Path(selected.source_root) / (selected.code_sources[0][0] if fault == 'code' else 'uv.lock')
            original_source_sha256 = sha256(path.read_bytes()).hexdigest()
            original_chunks = child.file_chunks

            def changed_source_chunks(candidate, *args, **kwargs):
                yield from original_chunks(candidate, *args, **kwargs)
                if Path(candidate).resolve() == path.resolve():
                    substituted_reads.append(path)
                    yield b'\n# SUBSTITUTED READ STREAM; ACTUAL CHECKOUT UNCHANGED\n'

            monkeypatch.setattr(child, 'file_chunks', changed_source_chunks)
        elif fault == 'executable':
            Path(selected.tleap_path).write_bytes(b'EXPOSED CHANGED EXECUTABLE')
        elif fault == 'parameter':
            Path(selected.parameter_path).write_bytes(b'EXPOSED CHANGED PARAMETERS')
        elif fault == 'extra-search-stock':
            (Path(selected.tleap_path).parent.parent / 'dat/leap/cmd/unselected-command').write_bytes(b'EXPOSED EXTRA')
        else:
            path = Path(selected.input_origin_path)
            changed = json.loads(path.read_bytes())
            changed['coordinates_angstrom_hex'][0][0] = float(9).hex()
            path.write_text(json.dumps(changed, sort_keys=True))
            if fault == 'self-consistent-changed-origin':
                selected = replace(selected, input_origin_sha256=sha256(path.read_bytes()).hexdigest())
                # Complete request/definition/provenance identities remain old;
                # self-consistent operand substitution is still not admitted.
                data['selection'] = selected.canonical_bytes().decode()
        class NoNativeProgress:
            def begin(self, *args):
                pytest.fail('a changed actual operand reached native BEGIN')
        class Invocation:
            def read(self): return json.dumps(data).encode()
        with pytest.raises(ValueError): child.exposed_child(NoNativeProgress(), Invocation())
        if fault in ('code', 'lock'):
            assert substituted_reads == [path]
            assert sha256(path.read_bytes()).hexdigest() == original_source_sha256
        assert not Path(selected.workdir).exists()
    finally: bundle.close()


def test_independent_array_reader_refuses_full_shape_bits_and_appended_member():
    import zlib
    import struct
    header = b"{'descr': '<f8', 'fortran_order': False, 'shape': (8, 3), }\n"
    raw_bytes = b'\x93NUMPY\x02\x00' + len(header).to_bytes(4, 'little') + header + struct.pack('<24d', *range(24))
    encoder = zlib.compressobj(wbits=31)
    encoded = encoder.compress(raw_bytes) + encoder.flush()
    capture = dict(uncompressed_bytes=len(raw_bytes), uncompressed_sha256=sha256(raw_bytes).hexdigest(),
        shape=[8, 3], npy_header_bytes=12 + len(header))
    assert independent.authenticate_array((encoded,), capture, (8, 3), tuple(range(24)))['elements'] == 24
    for actual, changed, shape, expected in ((encoded, capture, (7, 3), tuple(range(24))),
            (encoded, capture, (8, 3), (99, *range(1, 24))), (encoded + encoded, capture, (8, 3), tuple(range(24))),
            (encoded[:-3], capture, (8, 3), tuple(range(24)))):
        with pytest.raises(ValueError): independent.authenticate_array((actual,), changed, shape, expected)


@pytest.mark.parametrize('failed_unit', ['preparation', 'energy-gradient'])
def test_known_command_failure_closes_actual_unit_and_preserves_unentered_dependent_denominator(tmp_path, failed_unit):
    plane, bundle, store, selected, request, definitions, directory, invocation = _selected(tmp_path, 'success', failed_unit)
    try:
        store.parent_contacts.begin(definitions[0].parent_contact)
        context = _process_context(store, definitions[0], bundle.manifests)
        for port in context.input_ports: port.close()
        context = replace(context, input_bindings=bundle.input_bindings, input_ports=bundle.input_ports)
        runner = ExposedIsolatedNativeRunner(str(invocation), str(directory),
            selected_entry_source=str(Path(child.__file__).resolve()),
            selected_import_root=str(Path(selected.source_root) / 'src'))
        with pytest.raises(TaskProcessError):
            LocalProcessExecutor(scratch_root=plane.root).execute(runner, context, timeout_seconds=None, native_subwork=store)
        failed = next(row for row in definitions if row.subwork_id.endswith(failed_unit))
        retained = store.recover(failed)
        assert retained is not None and retained.completion.operational_status.value == 'FAILED'
        unit = json.loads(b''.join(store.iter_completed_output(failed, 'unit.return')))['value']
        assert unit['known_return'] and not unit['preparation_succeeded'] and unit['error_text']
        archive = independent.authenticate_archive(store.iter_completed_output(failed, 'files.raw'),
            b''.join(store.iter_completed_output(failed, 'files.census')), failed.subwork_id, ('subprocess-return.json',))
        assert json.loads(archive['files']['subprocess-return.json'])['returncode'] == 77
        other = next(row for row in definitions if row != failed)
        assert store.inspect(other).state is (NativeSubworkState.NOT_ENTERED if failed_unit == 'preparation' else NativeSubworkState.COMPLETED)
        with pytest.raises(ValueError): independent.read_completed_control(store, definitions, selected, request)
        with pytest.raises(ValueError, match='already completed'): store.begin(failed, bundle.manifests)
    finally: bundle.close()
