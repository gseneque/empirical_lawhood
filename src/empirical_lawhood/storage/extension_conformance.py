# SPDX-License-Identifier: MPL-2.0
"""Instrument existing contact boundaries during disclosed conformance checks.

This is a development check, not a sandbox for hostile Python. The public
command runs it in its own bounded process, separate from scientific workers.
"""

from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
import os
from pathlib import Path
import subprocess
from unittest.mock import patch


class ConformanceContactRefused(PermissionError):
    pass


_mount_diagnostic = ContextVar("conformance_mount_diagnostic", default=None)


class ConformanceContacts(list):
    def __init__(self):
        super().__init__()
        self.storage_diagnostics = []


@contextmanager
def forbid_conformance_contact(*, source_access=None, effect_ports=()):
    from empirical_lawhood.execution.recursive_provider import RecursiveOperationProvider
    from empirical_lawhood.execution.continuing_source import ContinuingSourceOwner
    from empirical_lawhood.execution.local.execution import LocalScheduler
    from empirical_lawhood.execution.local import isolated_native_subwork
    from empirical_lawhood.storage.artifacts import LocalFilesystemInspector

    attempts = ConformanceContacts()
    def refuse(boundary):
        def guard(*_args, **_kwargs):
            attempts.append(boundary)
            raise ConformanceContactRefused(f"conformance refuses contact at {boundary}")
        return guard

    original_inspect, original_process = LocalFilesystemInspector.inspect, subprocess.Popen

    def inspect_mount(inspector, contract):
        # Reuse the actual current-volume owner, including its unchanged
        # five-second and output bounds. No cached or synthetic state is supplied.
        target = str(Path(contract.required_mount_path).resolve(strict=True))
        command = ("findmnt", "--json", "--target", target, "--output", "SOURCE,FSTYPE,UUID,TARGET")
        token = _mount_diagnostic.set(command)
        try:
            return original_inspect(inspector, contract)
        finally:
            _mount_diagnostic.reset(token)

    def selected_process(command, *args, **kwargs):
        expected = _mount_diagnostic.get()
        options = dict(cwd=None, env=None, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, bufsize=0, start_new_session=os.name == "posix")
        if (expected is not None and type(command) is tuple and command == expected
                and not args and kwargs == options):
            attempts.storage_diagnostics.append({"owner": "LocalFilesystemInspector.inspect",
                "mount_target": expected[3], "timeout_seconds": 5,
                "maximum_stdout_bytes": 64 * 1024, "maximum_stderr_bytes": 16 * 1024})
            return original_process(command, **kwargs)
        return refuse("subprocess.Popen")(command, *args, **kwargs)

    with ExitStack() as stack:
        for owner, name in ((RecursiveOperationProvider, "runners"),
                            (RecursiveOperationProvider, "external_inputs"),
                            (LocalScheduler, "_execute_runner"),
                            (ContinuingSourceOwner, "start"),
                            (ContinuingSourceOwner, "ingest"),
                            (ContinuingSourceOwner, "execute"),
                            (isolated_native_subwork, "run_isolated_native_entry"),
                            (isolated_native_subwork, "preflight_isolated_native_entry")):
            stack.enter_context(patch.object(owner, name, refuse(owner.__name__ + "." + name)))
        # The shared contract checks never need these actual source ports. A
        # caught attempt still fails its case. Loading a trusted Python fixture
        # retains the existing process/network guards; this is not a sandbox.
        selected_ports = [(port, ("submit", "observe")) for key, port in effect_ports]
        if source_access is not None:
            selected_ports.append((source_access, ("require_owner", "require_actor")))
        patched = set()
        for port, names in selected_ports:
            for name in names:
                owner = port if name in getattr(port, '__dict__', {}) else type(port)
                key = id(owner), name
                if key not in patched:
                    stack.enter_context(patch.object(owner, name, refuse(type(port).__name__ + "." + name)))
                    patched.add(key)
        stack.enter_context(patch("socket.socket.connect", refuse("socket.connect")))
        stack.enter_context(patch("socket.socket.connect_ex", refuse("socket.connect_ex")))
        stack.enter_context(patch.object(LocalFilesystemInspector, "inspect", inspect_mount))
        stack.enter_context(patch("subprocess.Popen", selected_process))
        yield attempts
