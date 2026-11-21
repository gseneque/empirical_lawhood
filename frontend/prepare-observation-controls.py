# SPDX-License-Identifier: MPL-2.0
"""Prepare disclosed no-cloud controls through the production observation adapter.

Only the absent scientific metadata and provider ports are replaced. Collection
registration, accounting, supervision records, seals, import and browser reads
use their production owners. These controls supply no scientific qualification.
"""

import argparse
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

from empirical_lawhood.api import operational_observation as observation
from empirical_lawhood.api.application import execute_application
from empirical_lawhood.api.application_collection import SELECTION_SCHEMA as RUN_SELECTION
from empirical_lawhood.api.application_contracts import ApplicationContext, ApplicationRequest, response_bytes
from empirical_lawhood.api.application_state import operational_state_store
from empirical_lawhood.execution.remote.deployment_supervision import supervise_deployment
from empirical_lawhood.execution.deployment_budget import DeploymentAllocation, DeploymentBudget
from empirical_lawhood.execution.operational_observation import DOMAIN_SCHEMA, SELECTION_SCHEMA, document, document_bytes, unavailable_domain


class _PauseControl(BaseException):
    pass


class _ProviderControl:
    def __init__(self, observed, retired=False):
        self.observed, self.retired, self.calls = observed, retired, 0

    def observe(self, _output):
        self.calls += 1
        return {"status": "COMPUTE_ABSENT_VOLUME_RETAINED"} if self.retired and self.calls > 1 else self.observed


class _ActionControl:
    def __init__(self):
        self.calls = []

    def act(self, action, output):
        self.calls.append(action)
        output.write_text("EXPOSED SOFTWARE CONTROL; NO CLOUD ACTION\n")


def _pause(_seconds):
    raise _PauseControl()


def _pin(path):
    return {"path": str(path), "sha256": sha256(path.read_bytes()).hexdigest()}


def _write(path, value):
    with path.open('xb') as stream:
        stream.write(document_bytes(value))
    return _pin(path)


def _request(context, name, operation, **parameters):
    request = ApplicationRequest(name, context.context_id, operation, tuple(parameters.items()))
    result = execute_application(context, request)
    if not result.succeeded:
        raise RuntimeError(f'{operation}: {result.reason_codes}')
    return result


def domain_control(binding, kind):
    if kind == "unavailable-reader":
        return unavailable_domain(binding)
    source = {"schema": "empirical-lawhood/testing/operational-control", "version": "1.0.0",
        "object_id": "exposed.control", "fingerprint": sha256(kind.encode()).hexdigest()}
    positions = []
    for genotype in ("WT", "I95M"):
        for checkpoint in ("initial", "later"):
            accepted = checkpoint == "initial"
            positions.append({"id": f'{genotype}.{checkpoint}', "label": f'{genotype} / {checkpoint}',
                "genotype": genotype, "checkpoint": checkpoint, "trial": "ADVISORY_TRIAL_OBSERVED",
                "safe_state": "ACCEPTED" if accepted else "NOT_ACCEPTED",
                "publication": "PUBLISHED" if accepted else "FAILED" if kind == "partial-publication" else "NOT_PUBLISHED",
                "independent_reading": "READABLE_CONTROL" if accepted else "UNAVAILABLE",
                "continuation": "COORDINATE_RESTART_ONLY" if accepted else "UNAVAILABLE", "source": source})
    unknown = kind == "unknown-contact"
    effects = [{"id": f'exposed.effect.{index}', "stage": "diagnostic", "position": positions[index]["id"],
        "direction": "primary" if index < 2 else "additional", "scale": "0.01" if index % 2 else "0.02",
        "side": "plus" if index % 2 else "minus", "entry": "UNKNOWN" if unknown else "OBSERVED",
        "raw_return": "UNKNOWN" if unknown else "OBSERVED", "publication": "UNAVAILABLE" if unknown else "FAILED",
        "completion_receipt": "NOT_OBSERVED", "complete_force_return": "NOT_ESTABLISHED", "source": source}
        for index in range(4)]
    # Complete returns deliberately differ from both the task-receipt and raw
    # return counts. The browser must not derive its own scientific counter.
    allowances = [{"stage": stage, "allowance": allowance, "complete_returns": 0,
        "state": "DECLINED" if stage == "adaptive" else "PARTIAL" if stage == "preparation" else "UNENTERED",
        "depends_on": dependencies, "source": source} for stage, allowance, dependencies in (
            ("preparation", 10, []), ("diagnostic", 20, ["preparation"]),
            ("challenge", 4, ["adaptive"]), ("adaptive", 4, ["diagnostic"]))]
    return {"schema": DOMAIN_SCHEMA, "version": "1.0.0", "status": "SUPPORTED",
        "binding": {name: binding[name] for name in ("run_id", "packet_sha256")},
        "positions": positions, "effects": effects, "allowances": allowances, "complete_return_count": 0,
        "return_count_scope": "DISCLOSED_CONTROL_READER; RAW_RETURNS_AND_RECEIPTS_ARE_NOT_COMPLETE_FORCE_RETURNS",
        "pending_bindings": ["Original scientific readouts are not supplied by this exposed observation control."]}


def metadata_control(selection, kind):
    binding = selection["binding"]
    terminal = kind in ("financial-stop", "retirement-unresolved", "retired-volume", "return-failed")
    status = "SUCCEEDED" if terminal else "INTERRUPTED" if kind == "unknown-contact" else "RUNNING"
    source = {"schema": "empirical-lawhood/testing/operational-control", "version": "1.0.0",
        "object_id": "exposed.metadata", "fingerprint": sha256(kind.encode()).hexdigest()}
    execution = {"status": status, "run_id": binding["run_id"], "task_count": 3, "attempt_count": 3,
        "offset": 0, "rows": [{"task_id": f'exposed.task.{i}', "attempt_id": f'exposed.attempt.{i}', "ordinal": 1,
            "operational_status": s, "receipt_id": f'exposed.receipt.{i}' if s == "SUCCEEDED" else None}
            for i, s in enumerate(("SUCCEEDED", "FAILED", "NOT_ATTEMPTED"))], "source": source,
        "producing_code_sha256": binding["worker_source_sha256"], "dependency_lock_sha256": "d" * 64,
        "producing_commit": "e" * 40}
    unknown = kind == "unknown-contact"
    native = {"total": 1, "offset": 0, "rows": [{"task_id": "exposed.task.1", "attempt_id": "exposed.attempt.1",
        "subwork_id": "exposed.subwork", "state": "UNKNOWN_CONTACT" if unknown else "CONTACT_UNRESOLVED",
        "entry": "UNKNOWN" if unknown else "OBSERVED", "raw_return": "UNKNOWN" if unknown else "OBSERVED",
        "publication": "UNAVAILABLE" if unknown else "PARTIAL", "completion_receipt": "NOT_OBSERVED",
        "declared_outputs": 2, "published_outputs": 0 if unknown else 1, "source": source}],
        "coverage": "COMPLETE_METADATA_WINDOW", "body_validation": "DEFERRED_TO_ORIGINAL_READER"}
    return execution, native, domain_control(binding, kind)


def prepare(args):
    context = ApplicationContext.from_document(document(args.context.read_bytes()))
    if not os.path.ismount(args.required_mount):
        raise ValueError('the selected external mount is unavailable')
    for path in (args.output_dir, args.observation_root):
        path.relative_to(args.required_mount)
        if path.exists():
            raise ValueError('select fresh control destinations')
    context = replace(context, context_id="exposed.observation.controls", label="Exposed software observations · no cloud",
        project_root=None, input_root=args.output_dir, observation_root=args.observation_root,
        collection_path=args.observation_root / 'collection.json', invocation_root=args.output_dir / 'invocations',
        progress_root=args.output_dir / 'progress', python_executable=Path(sys.executable).absolute())
    store = operational_state_store(context)
    store.root.resolve(args.observation_root.relative_to(store.root.contract.canonical_path).as_posix(), for_write=True)
    args.output_dir.mkdir(mode=0o700)
    args.observation_root.mkdir(mode=0o700)
    context.invocation_root.mkdir()
    context.progress_root.mkdir()
    _write(args.output_dir / 'context.json', context.to_document())
    _write(args.output_dir / 'contexts.json', {"schema": "empirical-lawhood/application/contexts", "version": "1.0.0",
        "contexts": [context.to_document()]})
    source = _write(args.output_dir / 'control-source.json', {"scope": "EXPOSED_SOFTWARE_CONTROLS_ONLY",
        "native_calls": 0, "provider_calls": 0, "scientific_qualification": "NONE"})
    now = datetime.now(timezone.utc).replace(microsecond=0)
    selection_digest, rows = None, []
    original_reader = observation._observe_execution
    try:
        for kind in ('active', 'partial-publication', 'unknown-contact', 'stale-transfer', 'collector-restart', 'financial-stop',
                     'retirement-unresolved', 'retired-volume', 'return-failed', 'unavailable-reader'):
            selected_id = 'control.' + kind
            deployment_id = 'exposed-' + kind
            case = args.output_dir / kind
            case.mkdir()
            target = args.observation_root / kind
            target.mkdir()
            allocation = DeploymentAllocation(deployment_id, 'exposed-cluster', 'exposed-generation', 'exposed-pod',
                'exposed-head', 'exposed-volume', '/exposed/persistent', 'EXPOSED-1',
                (now - timedelta(hours=1)).isoformat(), (now - timedelta(minutes=30)).isoformat(),
                DeploymentBudget('50', '10', '1', '0', '3.99', '0.01', '0.03'))
            allocation_pin = _write(case / 'allocation.json', allocation.to_document())
            authority = _write(case / 'exposed-authority.json', {"status": "OWNER_AUTHORIZED", "deployment_id": deployment_id,
                "budget_total_usd": "50", "return_reserve_usd": "10", "retirement_margin_usd": "1",
                "maximum_compute_hourly_usd": "3.99", "keep_volume_id": allocation.volume_id, "zone": allocation.zone,
                "financial_actions": ["CANCEL_SELECTED_JOBS", "RETIRE_SELECTED_COMPUTE_KEEP_VOLUME"],
                "evidence_role": "EXPOSED_SOFTWARE_CONTROL_ONLY; NOT_REAL_AUTHORIZATION"})
            supervisor = _write(case / 'supervisor-selection.json', {"version": "1.0.0", "allocation": allocation.to_document(),
                "authorization_path": authority['path'], "authorization_sha256": authority['sha256'],
                "controller_python": '/nonexecuting/python', "controller_source_paths": ['/nonexecuting/source'],
                "controller_config": '/nonexecuting/config'})
            billing = '52' if kind in ('retirement-unresolved', 'retired-volume') else '40.47' if kind == 'financial-stop' else '2.25'
            observed = {"status": "OBSERVED", "observed_utc": now.isoformat(), "pod_billed_usd": billing, "volume_billed_usd": '0'}
            provider, actions = _ProviderControl(observed, retired=kind == 'retired-volume'), _ActionControl()
            try:
                supervise_deployment(Path(supervisor['path']), output_directory=case / 'supervisor',
                    observer=provider, actions=actions, sleep=_pause, emit=lambda _: None)
            except _PauseControl:
                pass
            except RuntimeError:
                if kind != 'retirement-unresolved':
                    raise
            job = _write(case / 'job-card.json', {"evidence_role": "EXPOSED_SOFTWARE_CONTROL_ONLY", "observation": {
                "cadence_seconds": 30, "stale_after_seconds": 120, "controller_source_sha256": 'c' * 64,
                "worker_source_sha256": 'd' * 64, "selected_gpu": "EXPOSED GPU CONTROL"}})
            binding = {"deployment_id": deployment_id, "investigation_id": "exposed.investigation", "selection_id": selected_id,
                "run_id": selected_id + '.run', "packet_sha256": sha256(selected_id.encode()).hexdigest(),
                "allocation_sha256": allocation_pin['sha256'], "job_card_sha256": job['sha256'],
                "controller_source_sha256": 'c' * 64, "worker_source_sha256": 'd' * 64}
            selected = {"schema": SELECTION_SCHEMA, "version": "1.0.0", "binding": binding,
                "directory": str(case / 'absent-scientific-result'), "allocation": allocation_pin, "job_card": job,
                "supervisors": [{"directory": str(case / 'supervisor'), "selection_sha256": _pin(case / 'supervisor/selection.json')['sha256']}],
                "cadence_seconds": 30, "stale_after_seconds": 120, "task_offset": 0, "native_offset": 0,
                "row_limit": 200, "domain_panel": None}
            selected_pin = _write(case / 'observer-selection.json', selected)
            stages = [{"id": f'm50.{i:02}', "label": label, "revision": 1, "state": state,
                "depends_on": deps, "source": source, "decision": None, "intent": None} for i, label, state, deps in (
                    (6, 'Paired preparation · exposed control', 'AUTHORED', []),
                    (7, 'Mixed-scale diagnostic · exposed control', 'SELECTED', ['m50.06']),
                    (9, 'Adaptive refinement before challenge · exposed control', 'DECLINED', ['m50.07']),
                    (8, 'Withheld challenge · exposed control', 'PLANNED', ['m50.09']))]
            entry = {"schema": RUN_SELECTION, "version": "1.0.0", "value": {"selection_id": selected_id,
                "investigation_id": binding['investigation_id'], "context_id": context.context_id,
                "label": 'Exposed control · ' + kind, "question": 'Software observation control: ' + kind,
                "identity": None, "readers": [{"operation": 'recursive.execution', "directory": selected['directory']}],
                "classification": {"programmes": [{"id": 'software', "label": 'Disclosed software controls'}],
                    "disciplines": [], "source": source}, "companions": [], "stages": stages, "links": [],
                "deployment": {name: binding[name] for name in ('deployment_id', 'run_id', 'packet_sha256',
                    'controller_source_sha256', 'worker_source_sha256')}}}
            entry['value']['deployment'].update(allocation=allocation_pin, job_card=job,
                observation_path=str(target / 'current.json'), return_path=str(target / 'return.json'))
            parameters = {'text': document_bytes(entry).decode()}
            if selection_digest:
                parameters['expected_collection_sha256'] = selection_digest
            registered = _request(context, selected_id, 'collection.register', **parameters)
            selection_digest = registered.payload['collection_sha256']
            _write(case / 'registration.json', json.loads(response_bytes(registered)))
            observation._observe_execution = lambda _context, selected, kind=kind: metadata_control(selected, kind)
            exported = observation.collect_observation(context, selected_pin, collector_id=selected_id + '.collector', sequence=1,
                output_directory=target / 'export-01', now=(now - timedelta(minutes=10) if kind == 'stale-transfer' else now).isoformat())
            # Incoming packages belong to the explicitly selected input root.
            # A copied closed directory simulates upstream byte transport only.
            import shutil
            incoming = case / 'incoming-01'
            shutil.copytree(exported['directory'], incoming)
            imported = _request(context, selected_id + '.import', 'observation.import', selection_id=selected_id,
                directory=str(incoming), expected_manifest_sha256=exported['manifest_sha256'])
            if kind == 'collector-restart':
                prior = exported['snapshot_sha256']
                exported = observation.collect_observation(context, selected_pin, collector_id=selected_id + '.restarted', sequence=1,
                    previous_snapshot_sha256=prior, output_directory=target / 'export-02', now=now.isoformat())
                incoming = case / 'incoming-02'
                shutil.copytree(exported['directory'], incoming)
                imported = _request(context, selected_id + '.restart', 'observation.import', selection_id=selected_id,
                    directory=str(incoming), expected_manifest_sha256=exported['manifest_sha256'],
                    expected_current_sha256=imported.payload['state_sha256'], restart_from_snapshot_sha256=prior)
            if kind == 'return-failed':
                _request(context, selected_id + '.return', 'observation.record-return', selection_id=selected_id,
                    text=document_bytes({'stage': 'TRANSFER', 'action': 'FAILED', 'source': source, 'close': False}).decode())
            read = _request(context, selected_id + '.read', 'observation.read', selection_id=selected_id)
            (case / 'read.json').write_bytes(response_bytes(read))
            rows.append({'id': selected_id, 'kind': kind, 'export': exported,
                'import_state_sha256': imported.payload['state_sha256'], 'fake_action_calls': actions.calls,
                'provider_calls': 0, 'native_calls': 0, 'lifecycle_actions': 0,
                'accounting': read.payload['snapshot']['financial']['accounting']['accounted_usd'],
                'remaining': read.payload['snapshot']['financial']['accounting']['remaining_usd']})
    finally:
        observation._observe_execution = original_reader
    report = {"scope": "EXPOSED_SOFTWARE_CONTROLS_ONLY", "status": "PASS", "rows": rows,
        "contexts": str(args.output_dir / 'contexts.json'), "context": str(args.output_dir / 'context.json'),
        "collection": str(context.collection_path), "real_provider_calls": 0, "new_native_calls": 0,
        "scientific_readers": "NOT SUPPLIED BY THESE EXPOSED OBSERVATION CONTROLS"}
    _write(args.output_dir / 'controls.json', report)
    print(json.dumps({'status': 'PASS', 'controls': len(rows), 'report': str(args.output_dir / 'controls.json')}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--context', required=True, type=Path)
    parser.add_argument('--required-mount', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--observation-root', required=True, type=Path)
    args = parser.parse_args()
    prepare(args)


if __name__ == '__main__':
    main()
