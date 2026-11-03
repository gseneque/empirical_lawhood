# SPDX-License-Identifier: MPL-2.0
"""Spawn the explicitly selected frozen interpreter without parent import paths.

Only the parent uses these transport classes. The child receives the ordinary
stdlib SpawnProcess and existing engine arguments, so an unchanged installed
worker needs no controller modules or entry script. Its normal preflight still
authenticates actual code, environment, inputs and native-entry permission.
"""
from copy import copy
import io
import multiprocessing
from multiprocessing import context, popen_spawn_posix, resource_tracker, spawn, util
import os


class _SelectedWorkerPopen(popen_spawn_posix.Popen):
    def _launch(self, process_obj):
        environment = process_obj._selected_worker_environment
        worker = copy(process_obj)
        worker.__class__ = context.SpawnProcess
        del worker._selected_worker_environment
        tracker_fd = resource_tracker.getfd()
        self._fds.append(tracker_fd)
        prepared = spawn.get_preparation_data(process_obj._name)
        # Keep the selected interpreter's isolated import path and avoid
        # executing the controller's command-line entry point in the worker.
        for name in ('sys_path', 'init_main_from_path', 'init_main_from_name'):
            prepared.pop(name, None)
        payload = io.BytesIO()
        context.set_spawning_popen(self)
        try:
            context.reduction.dump(prepared, payload)
            context.reduction.dump(worker, payload)
        finally:
            context.set_spawning_popen(None)
        parent_r = child_w = child_r = parent_w = None
        try:
            parent_r, child_w = os.pipe()
            child_r, parent_w = os.pipe()
            program = ('from multiprocessing.spawn import spawn_main; '
                f'spawn_main(tracker_fd={tracker_fd}, pipe_handle={child_r})')
            command = [environment.interpreter_path, '-I', '-B', '-c', program, '--multiprocessing-fork']
            self._fds.extend((child_r, child_w))
            self.pid = util.spawnv_passfds(os.fsencode(environment.interpreter_path), command, self._fds)
            self.sentinel = parent_r
            with open(parent_w, 'wb', closefd=False) as stream:
                stream.write(payload.getbuffer())
        finally:
            descriptors = [fd for fd in (parent_r, parent_w) if fd is not None]
            self.finalizer = util.Finalize(self, util.close_fds, descriptors)
            for fd in (child_r, child_w):
                if fd is not None:
                    os.close(fd)


class _SelectedWorkerProcess(context.SpawnProcess):
    def __init__(self, *args, selected_worker_environment, **kwargs):
        super().__init__(*args, **kwargs)
        self._selected_worker_environment = selected_worker_environment

    @staticmethod
    def _Popen(process_obj):
        return _SelectedWorkerPopen(process_obj)


class SelectedWorkerSpawnContext:
    """A per-executor selection; no global multiprocessing state is changed."""
    def __init__(self, environment):
        from empirical_lawhood.runtime.prepared_native_invocation import PreparedWorkerEnvironment
        if type(environment) is not PreparedWorkerEnvironment:
            raise TypeError('selected worker transport requires its exact frozen environment')
        environment.__post_init__()
        self.environment = environment
        self.base = multiprocessing.get_context('spawn')

    def Pipe(self, *args, **kwargs):
        return self.base.Pipe(*args, **kwargs)

    def Process(self, *args, **kwargs):
        return _SelectedWorkerProcess(*args, selected_worker_environment=self.environment, **kwargs)
