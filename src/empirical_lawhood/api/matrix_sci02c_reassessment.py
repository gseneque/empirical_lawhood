# SPDX-License-Identifier: MPL-2.0
"""Authenticated additive PURE readback of the failed SCI02-C calibration checks."""
from hashlib import sha256
import json
from pathlib import Path

from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02c_bindings as owner
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02c_reassessment as binding
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_records import Sci02CDesign, Sci02CProduct, NATIVE_PHASES
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_experiment import Sci02CSpecification
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import Sci02Selection
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.api.matrix_sci02 import _source_record, _values
from empirical_lawhood.api.recursive_execution import _read_recursive_wave_with_retained_roots


def _pin(record, field): return ObjectIdentity.from_record(getattr(record, field), record)


def authenticate_original(*, directory, artifact_writer):
    """Require the settled 200 successes, 24 PURE KeyErrors and nine blocked tasks."""
    from empirical_lawhood.api.matrix_sci02c import _native_custody
    from empirical_lawhood.adapters.matrix_storage.matrix_array_io import decode_matrix_arrays, NPZMemberSelection
    from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
    from empirical_lawhood.design.campaigns import CampaignSpec
    from empirical_lawhood.storage.recovery import ExternalRunRecoveryStore
    from empirical_lawhood.execution.recovery import DevelopmentRunRecoveryIndex, TaskRecoveryDisposition
    from empirical_lawhood.execution.execution import OperationalFailureClass
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_read
    captured = {}

    def consume(**kwargs):
        payloads, products, plan = kwargs['payloads'], kwargs['products'], kwargs['plan']
        spec = decode_canonical_bytes(payloads['experiment-specification.json'], Sci02CSpecification, maximum_bytes=4 * 1024**2)
        if spec.tranche != 'CALIBRATION': raise ValueError('SCI02-C reassessment requires the original calibration tranche')
        study = _source_record(payloads, spec.study, Sci02CDesign)
        selection = _source_record(payloads, spec.selection, Sci02Selection)
        provenance = _source_record(payloads, spec.provenance, NumericalProducingProvenance)
        frozen = _source_record(payloads, spec.frozen, Sci02CProduct)
        roots = tuple(selection.root('DEV', i) for i in range(8, 16))
        configs = owner.configs(study, roots, provenance.identity, model=frozen.frozen_description)
        tasks = {t.task_id: t for t in plan.tasks}
        failed = tuple(c.node_id for c in configs if c.phase == 'assess')
        blocked = tuple(c.node_id for c in configs if c.phase in ('reduce', 'calibrate'))
        succeeded = tuple(c.node_id for c in configs if c.phase not in ('assess', 'reduce', 'calibrate'))
        terminal = products['terminal']
        if (set(tasks) != {c.node_id for c in configs} or terminal is None
                or terminal.operational_status != 'FAILED'
                or terminal.failed_task_ids != failed or terminal.blocked_task_ids != blocked
                or terminal.completed_task_ids != succeeded):
            raise ValueError('SCI02-C reassessment refuses changed, incomplete or differently failed original execution')
        writer = kwargs['artifact_writer']
        index_path = f'runs/{terminal.run_id}/recovery/wave.development/run-recovery-index.json'
        from empirical_lawhood.storage.recursive_custody import read_exposed_recursive_payload
        manifest = writer.read_manifest(index_path)
        index = decode_canonical_bytes(read_exposed_recursive_payload(writer, manifest, maximum_bytes=64 * 1024**2),
            DevelopmentRunRecoveryIndex, maximum_bytes=64 * 1024**2)
        recovery = ExternalRunRecoveryStore(writer)
        for task_id in failed:
            attempt, = index.task(task_id).attempts
            event = recovery.read_event(index, attempt.event_relative_path)
            if (event is None or event.disposition is not TaskRecoveryDisposition.FAILED or event.failure is None
                    or event.failure.failure_class is not OperationalFailureClass.RETRY_EXHAUSTION
                    or event.failure.sanitized_exception_type != 'KeyError'):
                raise ValueError('SCI02-C reassessment refuses a different original failure')
        records = {}
        for c in configs:
            if c.node_id not in succeeded: continue
            receipt = products['receipts'].get(c.node_id)
            candidates = products['records'].get(c.node_id, {})
            if receipt is None or receipt.operational_status is not OperationalStatus.SUCCEEDED or len(candidates) != 1:
                raise ValueError('SCI02-C reassessment lacks an exact successful original receipt')
            p, = candidates.values()
            if type(p) is not Sci02CProduct or p.config != c or p.disposition != 'AVAILABLE':
                raise ValueError('SCI02-C reassessment changes original completed operands')
            records[c.node_id] = p
            if c.phase in NATIVE_PHASES: _native_custody(writer, products, tasks, plan, c, provenance, p)
        for p in records.values():
            expected = tuple(sorted((records[c.node_id].identity for c in owner.parents_for(p.config).values()), key=lambda v: v.object_id))
            if p.predecessors != expected: raise ValueError('SCI02-C reassessment changes original sealed causality')
        artifact = study.physical.assay.template_artifact
        name = 'external-' + sha256(('external.templates.' + artifact.sha256).encode()).hexdigest()[:24] + '.npz'
        templates = dict(decode_matrix_arrays(payloads[name], NPZMemberSelection(artifact, study.physical.assay.template_members)))
        cases, paths = [], {}
        for root in roots:
            selected = tuple(p for p in records.values() if p.config.roots == (root,))
            by_phase = {p.config.phase: p for p in selected if p.config.recipe == 'COMMON'}
            sci02_read.instrument_checks(study.physical, _values(writer, products, tasks, by_phase['source-state']),
                _values(writer, products, tasks, by_phase['instrument']), templates)
            current = owner.make_config(study, (root,), 'reduce', 'COMMON', provenance.identity, model=frozen.frozen_description)
            cases.append(binding.RetainedCalibrationRoot('retained.calibration.' + current.node_id, current,
                _pin(plan, 'execution_plan_id'), _pin(terminal, 'terminal_event_id'), tuple(sorted(selected, key=lambda p: p.config.node_id)),
                tuple(sorted((_pin(products['receipts'][p.config.node_id], 'receipt_id') for p in selected), key=lambda p: p.object_id))))
            for p in selected:
                a = products['outputs'][p.arrays.array_artifact.artifact_id]
                paths['external.' + p.arrays.array_artifact.artifact_id] = writer.root.resolve(a.materialization.relative_path, for_write=False)
        captured.update(cases=tuple(cases), paths=paths, study=study, selection=selection, frozen=frozen,
            campaign=_source_record(payloads, spec.campaign, CampaignSpec),
            original_directory=str(Path(directory).absolute()), original_plan=_pin(plan, 'execution_plan_id').to_document(),
            original_terminal=_pin(terminal, 'terminal_event_id').to_document(), original_status='FAILED', original_native_contacts=80)
        return {'state': 'ORIGINAL_CALIBRATION_NATIVE_AND_CAUSAL_CUSTODY_AUTHENTICATED', 'native_contacts': 80,
            'failed_pure_checks': 24, 'blocked_pure_reductions': 9, 'new_native_contacts': 0}

    _read_recursive_wave_with_retained_roots(directory=directory, artifact_writer=artifact_writer,
        terminal_product_format='references', _scientific_consumer=consume)
    return captured


def author_reassessment(*, directory, artifact_writer, project_root, output_directory, input_directory):
    from empirical_lawhood.api.recursive_authoring import author_recursive_wave
    from empirical_lawhood.storage.numerical_provenance import capture_numerical_provenance
    source = authenticate_original(directory=directory, artifact_writer=artifact_writer)
    provenance = capture_numerical_provenance(project_root=project_root)
    digest = sha256((''.join(c.fingerprint() for c in source['cases']) + provenance.fingerprint()).encode()).hexdigest()
    draft = binding.lower(source['cases'], provenance, source['campaign'], draft_id='draft.sci02c.readback.' + digest)
    inputs = Path(input_directory).absolute()
    inputs.mkdir(parents=True, exist_ok=False)
    for c in source['cases']: (inputs / f'root-{c.original.root.ordinal:02d}.json').write_bytes(c.canonical_bytes())
    (inputs / 'provenance.json').write_bytes(provenance.canonical_bytes())
    audit = {k: v for k, v in source.items() if k.startswith('original_')}
    audit.update(current_provenance=provenance.identity.to_document(), source_cases=[c.identity.to_document() for c in source['cases']],
        operations=9, new_native_contact_count=0, frozen_account_changed=False)
    (inputs / 'source-audit.json').write_text(json.dumps(audit, indent=2, sort_keys=True) + '\n')
    result = author_recursive_wave(draft=draft, project_root=project_root, artifact_writer=artifact_writer,
        output_dir=output_directory, input_bindings=tuple(sorted(source['paths'].items())))
    return {'authoring': result, 'directory': str(Path(output_directory).absolute()), 'source_audit': str(inputs / 'source-audit.json')}


def read_reassessment(*, directory, original_directory, artifact_writer, _capture=None):
    from empirical_lawhood.api.matrix_sci02c import _check_result
    from empirical_lawhood.api.matrix_native_read_custody import _record
    original = authenticate_original(directory=original_directory, artifact_writer=artifact_writer)
    captured = {} if _capture is None else _capture

    def consume(**kwargs):
        draft, plan, products = kwargs['draft'], kwargs['plan'], kwargs['products']
        payloads = kwargs['payloads']
        configs = []
        for op in draft.operations:
            name = 'config-' + sha256(op.node_id.encode()).hexdigest()[:24] + '.json'
            configs.append(decode_canonical_bytes(payloads[name], binding.ReassessmentConfig, maximum_bytes=binding.MAX_RECORD))
        configs = tuple(sorted(configs, key=lambda c: c.node_id))
        pooled, = (c for c in configs if c.phase == 'calibrate')
        if configs != binding.selected_for(pooled) or pooled.retained != original['cases']:
            raise ValueError('SCI02-C readback substitutes its authenticated original calibration')
        tasks = {t.task_id: t for t in plan.tasks}
        if set(tasks) != {c.node_id for c in configs}: raise ValueError('SCI02-C readback changes its complete PURE graph')
        root_products, root_arrays, rows, costs = {}, {}, [], []
        for c in configs:
            if c.phase != 'reduce': continue
            receipt = products['receipts'].get(c.node_id)
            if receipt is None or receipt.operational_status is not OperationalStatus.SUCCEEDED:
                raise ValueError('SCI02-C readback lacks a completed PURE reduction')
            p = _record(products, tasks, plan.source_plan.object_id, c.node_id, Sci02CProduct)
            if p.config != c.operation or p.predecessors != tuple(sorted((v.identity for v in c.retained[0].products), key=lambda v: v.object_id)):
                raise ValueError('SCI02-C readback substitutes original product ancestry')
            arrays = {}
            for v in c.retained[0].products:
                name = 'external-' + sha256(('external.' + v.arrays.array_artifact.artifact_id).encode()).hexdigest()[:24] + '.npz'
                from empirical_lawhood.adapters.matrix_storage.matrix_array_io import decode_matrix_arrays
                arrays[v.config.node_id] = dict(decode_matrix_arrays(payloads[name], v.arrays))
            actual = _values(kwargs['artifact_writer'], products, tasks, p)
            _check_result(p, actual, binding.reassess(c, arrays))
            root_products[c.node_id], root_arrays[c.node_id] = p, actual
            row = {'root': c.operation.root.record_id, 'ordinal': c.operation.root.ordinal, 'state': 'ASSESSED',
                'disposition': p.disposition, 'measurements': {k: None if v is None else str(v) for k, v in p.measurements}}
            for key in ('model_q', 'frozen_q', 'native_q', 'native_endpoints', 'predictions', 'widths', 'selected_route', 'request_history'):
                if key in actual: row[key] = actual[key].tolist()
            rows.append(row)
            costs.append({'node': c.node_id, 'phase': 'retained-reduce', 'root_ordinal': c.operation.root.ordinal,
                'components': {k: str(v) for k, v in p.measurements if k.startswith('runtime.')}})
        p = _record(products, tasks, plan.source_plan.object_id, pooled.node_id, Sci02CProduct)
        expected, calibration = binding.science.calibrate(pooled.operation, root_products, root_arrays)
        actual = _values(kwargs['artifact_writer'], products, tasks, p)
        _check_result(p, actual, expected)
        if p.config != pooled.operation or p.calibration_result != calibration or p.predecessors != tuple(sorted((v.identity for v in root_products.values()), key=lambda v: v.object_id)):
            raise ValueError('SCI02-C readback changes its original fixed calibration rule')
        captured.update(original=original, calibrated=p, receipt=products['receipts'][pooled.node_id])
        return {'scientific_completion': 'COMPLETE_SCI02C_ASSESSMENT', 'state': 'RECEIPT_BOUND_CALIBRATION_REASSESSED',
            'tranche': 'CALIBRATION', 'assigned_roots': 8, 'assigned_response_packages': 24,
            'root_findings': rows, 'operation_costs': costs, 'calibration': calibration.to_document(),
            'pooled_product': p.identity.to_document(), 'pooled_measurements': {k: None if v is None else str(v) for k,v in p.measurements},
            'original_terminal': original['original_terminal'], 'original_status': 'FAILED',
            'original_completed_native_contacts': 80, 'new_native_contact_count': 0,
            'qualification': 'NOT_ESTABLISHED', 'molecular_requirement': {'status': 'OPEN'}}

    report, _ = _read_recursive_wave_with_retained_roots(directory=directory, artifact_writer=artifact_writer,
        terminal_product_format='references', _scientific_consumer=consume)
    return report


def create_confirmation_inputs(*, directory, original_directory, artifact_writer, templates_path, protocol_path, project_root, output_directory):
    from empirical_lawhood.api.matrix_sci02c import _write_inputs
    from empirical_lawhood.storage.bounded_io import read_bounded_bytes
    captured = {}
    report = read_reassessment(directory=directory, original_directory=original_directory, artifact_writer=artifact_writer, _capture=captured)
    source, calibrated = captured['original'], captured['calibrated']
    protocol = read_bounded_bytes(Path(protocol_path), maximum_bytes=1024**2)
    if sha256(protocol).hexdigest() != source['study'].protocol_document_sha256:
        raise ValueError('SCI02-C reassessment continuation changes the frozen scientific protocol')
    artifact = source['selection'].design.assay.template_artifact
    templates = read_bounded_bytes(Path(templates_path), maximum_bytes=artifact.size_bytes)
    if len(templates) != artifact.size_bytes or sha256(templates).hexdigest() != artifact.sha256:
        raise ValueError('SCI02-C reassessment continuation changes the original fixed instrument')
    audit = {'predecessor_directory': str(Path(directory).absolute()), 'original_failed_directory': str(Path(original_directory).absolute()),
        'predecessor_product': calibrated.identity.to_document(), 'predecessor_receipt': captured['receipt'].to_document(),
        'readout_sha256': sha256(json.dumps(report, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest(),
        'original_terminal': source['original_terminal'], 'original_status': 'FAILED', 'new_native_contacts_during_derivation': 0}
    return _write_inputs(study=source['study'], selection=source['selection'], campaign=source['campaign'], cases=(),
        frozen=source['frozen'], calibrated=calibrated, files=(('templates', artifact, 'templates.npz', templates),),
        protocol=protocol, project_root=project_root, output_directory=output_directory, audit=audit)
