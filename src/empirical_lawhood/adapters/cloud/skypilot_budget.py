# SPDX-License-Identifier: MPL-2.0
"""Pinned SkyPilot lifecycle actions behind the deployment action port."""

from hashlib import sha256
import json
import os
from pathlib import Path

from empirical_lawhood.execution.local.bounded_process import run_bounded_command
from empirical_lawhood.execution.remote.deployment_supervision_selection import SupervisionSelection
from empirical_lawhood.storage.artifact_replication import _durable_bytes
from empirical_lawhood.storage.bounded_io import read_bounded_bytes


class SkyPilotBudgetActions:
    def __init__(self, selection, selection_path):
        self.selection, self.selection_path = selection, Path(selection_path)
        self.original = read_bounded_bytes(self.selection_path, maximum_bytes=128*1024)
        if SupervisionSelection.from_document(json.loads(self.original)) != selection:
            raise ValueError('controller action changes its original supervision selection')

    def act(self, action, output):
        if action not in ('cancel', 'retire'):
            raise ValueError('budget supervision can only cancel jobs or retire selected compute')
        if read_bounded_bytes(self.selection_path, maximum_bytes=128*1024) != self.original:
            raise ValueError('supervision selection changed before its controller action')
        self.selection.require_authorization()
        environment = os.environ.copy()
        environment.update(PYTHONPATH=os.pathsep.join(self.selection.controller_source_paths),
            SKYPILOT_GLOBAL_CONFIG=self.selection.controller_config, PYTHONDONTWRITEBYTECODE='1')
        command = [self.selection.controller_python, '-m',
            'empirical_lawhood.adapters.cloud.skypilot_controller_action',
            '--selection', str(self.selection_path), '--action', action,
            '--expected-selection-sha256', sha256(self.original).hexdigest()]
        # The lifecycle action must not depend on opening, writing or flushing
        # its normal evidence destination. The existing process owner bounds
        # both in-memory channels and the action lifetime before publication.
        result = run_bounded_command(command, environment=environment,
            timeout_seconds=self.selection.allocation.budget.action_timeout_seconds,
            maximum_stdout_bytes=2**20, maximum_stderr_bytes=2**20)
        evidence = {'action': action, 'action_returncode': result.returncode, 'action_log': 'PUBLISHED'}
        try:
            _durable_bytes(Path(output), result.stdout + b'\n--- controller stderr ---\n' + result.stderr)
        except OSError as error:
            evidence.update(action_log='UNAVAILABLE', action_log_error_type=type(error).__name__,
                            action_log_error=str(error))
        if result.returncode:
            raise RuntimeError(f'upstream {action} failed with exit {result.returncode}; '
                               f'action log is {evidence["action_log"]}')
        return evidence


