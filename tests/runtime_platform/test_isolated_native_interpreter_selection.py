# SPDX-License-Identifier: MPL-2.0
"""Main controller and a bare selected child share the existing custody bridge."""

from hashlib import sha256
import json
from pathlib import Path
import venv

import pytest

from empirical_lawhood.adapters.methods.isolated_native_conformance import ExposedIsolatedNativeRunner
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor, TaskProcessError
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.isolated_native_subwork import IsolatedNativeEntrySelection
from empirical_lawhood.runtime.native_subwork import NativeSubworkState
from tests.runtime_platform.test_isolated_native_subwork import fixture_case


SOURCE_ROOT = Path(__file__).resolve().parents[2] / 'src'


@pytest.mark.parametrize('phase,code', [('success', 0), ('after-completion', 95)])
def test_frozen_controller_uses_authenticated_bare_venv_child(tmp_path, phase, code):
    child_env = tmp_path / 'science-only-child'
    venv.EnvBuilder(with_pip=False, symlinks=True, system_site_packages=False).create(child_env)
    interpreter = child_env / 'bin/python'
    store, definitions, context, root, invocation, payload = fixture_case(tmp_path, phase)
    source = root / 'selected_bare_environment.py'
    source.write_text('import json, sys\nfrom pathlib import Path\n'
        'from empirical_lawhood.adapters.methods.isolated_native_conformance import exposed_child as original\n'
        'def exposed_child(progress, invocation):\n'
        '    Path("observed-child-runtime.json").write_text(json.dumps({"executable":sys.executable,"prefix":sys.prefix,"base_prefix":sys.base_prefix}))\n'
        '    original(progress, invocation)\n')
    runner = ExposedIsolatedNativeRunner(str(invocation), str(root), selected_entry_source=str(source),
        selected_import_root=str(SOURCE_ROOT), selected_interpreter_path=str(interpreter),
        selected_interpreter_sha256=sha256(interpreter.read_bytes()).hexdigest())
    try:
        executor = LocalProcessExecutor(scratch_root=store.plane.root)
        if code:
            with pytest.raises(TaskProcessError):
                executor.execute(runner, context, timeout_seconds=None, native_subwork=store)
        else:
            assert executor.execute(runner, context, timeout_seconds=None, native_subwork=store).checks[0].passed
    finally:
        for port in context.input_ports:
            port.close()
    observed = json.loads((root / 'observed-child-runtime.json').read_bytes())
    assert observed['executable'] == str(interpreter)
    assert observed['prefix'] == str(child_env)
    assert store.inspect(definitions[0]).state is NativeSubworkState.COMPLETED
    completed = store.recover(definitions[0])
    assert b''.join(store.iter_completed_output(definitions[0], definitions[0].outputs[0].output_id)) == payload
    assert store.recover(definitions[0]) == completed
    raw = b''.join(store.iter_completed_output(next(row for row in store.iter_roster_definitions(
        definitions[0].parent_contact, 'selected.native-subwork') if row.subwork_id == 'engine.metadata'), 'process.selection'))
    selected = decode_canonical_bytes(raw, IsolatedNativeEntrySelection, maximum_bytes=len(raw))
    assert selected.interpreter_path == str(interpreter)
    assert selected.interpreter_sha256 == sha256(interpreter.read_bytes()).hexdigest()
    assert all(store.inspect(row).state is NativeSubworkState.NOT_ENTERED for row in definitions[1:])


@pytest.mark.parametrize('wrong', ['digest', 'missing-digest'])
def test_explicit_interpreter_refuses_without_child_contact(tmp_path, wrong):
    child_env = tmp_path / 'science-only-child'
    venv.EnvBuilder(with_pip=False, symlinks=True, system_site_packages=False).create(child_env)
    interpreter = child_env / 'bin/python'
    store, definitions, context, root, invocation, _ = fixture_case(tmp_path, 'success')
    runner = ExposedIsolatedNativeRunner(str(invocation), str(root), selected_interpreter_path=str(interpreter),
        selected_interpreter_sha256='9' * 64 if wrong == 'digest' else None)
    try:
        with pytest.raises(TaskProcessError) as failure:
            LocalProcessExecutor(scratch_root=store.plane.root).execute(runner, context,
                timeout_seconds=None, native_subwork=store)
        assert failure.value.sanitized_exception_type == 'ValueError'
    finally:
        for port in context.input_ports:
            port.close()
    assert all(store.inspect(row).state is NativeSubworkState.NOT_ENTERED for row in definitions)
    assert not (root / 'child-return.json').exists()
    assert not (root / 'observed-child-runtime.json').exists()
