# SPDX-License-Identifier: MPL-2.0
"""Deployment supervision through explicit observation and lifecycle ports.

The application binds provider adapters. This owner retains monetary decisions,
operational evidence, uncertain-action handling and recovery restrictions.
"""

from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import time
from typing import Callable, Protocol

from empirical_lawhood.storage.transfer_files import normalized_absolute_path as _absolute, encode_document as _encode
from empirical_lawhood.storage.artifact_replication import _durable_bytes
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.execution.progress import progress_step, report_progress
from empirical_lawhood.execution.deployment_budget import account_deployment
from empirical_lawhood.execution.remote.deployment_supervision_selection import SupervisionSelection


class DeploymentObservationPort(Protocol):
    def observe(self, output: Path) -> dict: ...


class DeploymentActionPort(Protocol):
    def act(self, action: str, output: Path) -> dict | None: ...


def supervise_deployment(selection_path, *, output_directory,
                         observer: DeploymentObservationPort | None = None,
                         actions: DeploymentActionPort | None = None,
                         observer_factory: Callable[[SupervisionSelection], DeploymentObservationPort] | None = None,
                         action_factory: Callable[[SupervisionSelection, Path], DeploymentActionPort] | None = None,
                         sleep=time.sleep, emit=lambda value: print(json.dumps(value), flush=True)):
    """Run one fresh supervision lifetime; no restart, dispatch or volume deletion.

Ports permit offline conformance tests. A real invocation requires original
owner authorization and independently checked allocation identities.
"""
    path = Path(selection_path)
    original = read_bounded_bytes(path, maximum_bytes=128*1024)
    selected = SupervisionSelection.from_document(json.loads(original))
    authorization = selected.require_authorization()
    output = Path(output_directory)
    _absolute(str(output))
    # Use the original read-only selection, not a copy on the failing journal
    # filesystem. The action process independently checks its exact bytes.
    if actions is None:
        if action_factory is None:
            raise TypeError('deployment supervision requires an application-bound action port')
        actions = action_factory(selected, path)

    def require_current():
        if read_bounded_bytes(path, maximum_bytes=128*1024) != original:
            raise ValueError('supervision selection changed during its lifetime')
        selected.require_authorization()

    def record(value, *, best_effort=False):
        value = {**value, 'recorded_utc': datetime.now(timezone.utc).isoformat(),
            'native_work_dispatched': False, 'automatic_replay': False, 'keep_volume_id': selected.allocation.volume_id}
        try:
            with (output/'events.jsonl').open('ab') as stream:
                stream.write(_encode(value))
                stream.flush()
                os.fsync(stream.fileno())
            temporary = output/'latest.pending.json'
            _durable_bytes(temporary, _encode(value))
            temporary.replace(output/'latest.json')
        except Exception as error:
            if not best_effort:
                raise
            value.update(evidence_publication='UNAVAILABLE', evidence_error_type=type(error).__name__,
                         evidence_error=str(error))
        try:
            emit(value)
        except Exception:
            if not best_effort:
                raise
            # A broken event consumer must not replace the original unresolved
            # outcome or prevent an authorized emergency lifecycle action.
            try:
                print(json.dumps(value), file=sys.stderr, flush=True)
            except Exception:
                pass
        return value

    def observe(attempt):
        nonlocal observer
        if observer is None:
            if observer_factory is None:
                raise TypeError('deployment supervision requires an application-bound observation port')
            observer = observer_factory(selected)
        with progress_step("deployment.observe", total=1, unit="provider-observations") as progress:
            result = observer.observe(attempt)
            progress.advance()
            return result

    def retire(attempt, index, cause=None):
        # Attempt retirement before any further failure-report writes. Authority
        # and allocation checks still apply even when evidence storage is lost.
        try:
            require_current()
            with progress_step('deployment.retire', total=1, unit='provider-actions') as progress:
                action = actions.act('retire', attempt/'retire.log')
                progress.advance()
            if cause is not None:
                record({'status': 'SUPERVISION_REFUSED', 'error_type': type(cause).__name__,
                        'error': str(cause), 'retirement_action': action}, best_effort=True)
            confirmation = output/f'retirement-{index:06d}'
            confirmation.mkdir(mode=0o700)
            confirmed = observe(confirmation)
            if confirmed['status'] != 'COMPUTE_ABSENT_VOLUME_RETAINED':
                raise RuntimeError('selected compute remains present after the retirement command')
            require_current()
            return record({**confirmed, 'retirement_action': action})
        except Exception as error:
            record({'status': 'RETIREMENT_UNRESOLVED', 'error_type': type(error).__name__,
                    'error': str(error)}, best_effort=True)
            raise RuntimeError('retirement is unresolved; inspect original actions and resolve the selected allocation') from error

    try:
        if output.resolve(strict=False) != output:
            raise ValueError('select an ordinary explicit supervision destination')
        output.mkdir(mode=0o700)
        _durable_bytes(output/'selection.json', original)
        _durable_bytes(output/'original-authorization.json', authorization)
    except Exception as error:
        return retire(output/'observation-000000', 0, error)

    stopped, accounted, index = False, '0', 0
    while True:
        index += 1
        attempt = output/f'observation-{index:06d}'
        try:
            require_current()
            attempt.mkdir(mode=0o700)
            observed = observe(attempt)
            if observed['status'] == 'COMPUTE_ABSENT_VOLUME_RETAINED':
                require_current()
                return record(observed)
            result = account_deployment(selected.allocation, observed_utc=observed['observed_utc'],
                pod_billed_usd=observed['pod_billed_usd'], volume_billed_usd=observed['volume_billed_usd'],
                previous_accounted_usd=accounted, science_stopped=stopped)
            accounted = result['accounted_usd']
            record({**result, 'observation': str(attempt)})
            if result['status'] == 'STOP_SCIENCE_RETURN_ONLY' and not stopped:
                require_current()
                with progress_step('deployment.cancel', total=1, unit='provider-actions') as progress:
                    action = actions.act('cancel', attempt/'cancel.log')
                    progress.advance()
                stopped = True
                record({'status': 'FINANCIAL_CANCELLATION_RETURNED', 'native_completion': 'NOT_INFERRED',
                        'cancellation_action': action})
                if action is not None and action.get('action_log') != 'PUBLISHED':
                    raise RuntimeError('controller action evidence is unavailable')
        except Exception as error:
            return retire(attempt, index, error)
        if result['status'] == 'RETIRE_COMPUTE':
            return retire(attempt, index)
        report_progress(phase="deployment.await-next-observation", done=index, unit="observations",
            detail=f"Next provider poll after {selected.allocation.budget.poll_seconds}s; remote advance unknown")
        sleep(selected.allocation.budget.poll_seconds)


def observe_deployment_budget(selection_path, *, output_directory,
                              observer_factory: Callable[[SupervisionSelection], DeploymentObservationPort]):
    raw = read_bounded_bytes(Path(selection_path), maximum_bytes=128*1024)
    selected = SupervisionSelection.from_document(json.loads(raw))
    output = Path(output_directory)
    _absolute(str(output))
    if output.resolve(strict=False) != output or not output.parent.is_dir():
        raise ValueError('select an ordinary explicit observation destination')
    output.mkdir(mode=0o700)
    _durable_bytes(output/'selection.json', raw)
    observed = observer_factory(selected).observe(output)
    if observed['status'] == 'OBSERVED':
        observed = account_deployment(selected.allocation, **{k: v for k, v in observed.items() if k != 'status'})
    if read_bounded_bytes(Path(selection_path), maximum_bytes=128*1024) != raw:
        raise ValueError('allocation selection changed during observation')
    observed['selection_sha256'] = sha256(raw).hexdigest()
    _durable_bytes(output/'readout.json', _encode(observed))
    return observed
