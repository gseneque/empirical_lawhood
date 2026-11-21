# SPDX-License-Identifier: MPL-2.0
"""Bounded original metadata for preparation and selected response effects."""

from pathlib import Path

from empirical_lawhood.api.experiment_execution_read import load_development_execution_controls, read_execution_records
from empirical_lawhood.api.operational_observation import native_progress_record
from empirical_lawhood.storage.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.storage.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.storage.recursive_custody import read_exposed_recursive_payload
from empirical_lawhood.storage.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.execution.operational_observation import DOMAIN_SCHEMA, VERSION, document_bytes, validate_domain
from empirical_lawhood.api.domain_composition.rubisco_response.preparation_presentation import load_selected

MAX_READOUT = 4 * 2**20


def identity(pin):
    return dict(schema=pin.object_schema, version=pin.object_version,
        object_id=pin.object_id, fingerprint=pin.object_fingerprint)


def published_readout(*, writer, run_id, task, attempts, kind):
    """Read the original published independent record, never reconstruct its arrays."""
    store = ExternalTaskReceiptStore(writer)
    values = []
    for row in attempts:
        if row['task_id'] != task or row.get('receipt_id') is None:
            continue
        receipt = store.read_by_receipt_id(run_id, task, row['receipt_id'])
        if receipt is None or receipt.operational_status is not OperationalStatus.SUCCEEDED:
            continue
        for logical, material in zip(receipt.output_logical_artifacts, receipt.output_materializations, strict=True):
            if logical.payload_schema != kind.SCHEMA:
                continue
            manifest = writer.read_manifest(material.relative_path)
            if manifest.logical != logical or manifest.materialization != material:
                raise PermissionError('preparation observation substitutes its original receipted readout')
            raw = read_exposed_recursive_payload(writer, manifest, maximum_bytes=MAX_READOUT)
            value = decode_canonical_bytes(raw, kind, maximum_bytes=MAX_READOUT)
            if value.fingerprint() != logical.content_sha256:
                raise PermissionError('preparation observation changes original readout identity')
            values.append(value)
    if len(values) > 1:
        raise ValueError('preparation observation refuses ambiguous successful independent readouts')
    return values[0] if values else None


def selected_native(*, writer, plan, index, source, config, task, prefix):
    """Join only the exact authored task and its original frozen subwork roster."""
    contacts = ExternalNativeEffectContactStore(plane=writer,
        execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    parent = contacts.read(index.run_id, task.task_id)
    if parent is None:
        return None, dict(entry='NOT_OBSERVED', raw_return='NOT_OBSERVED', publication='NOT_OBSERVED',
            completion_receipt='NOT_OBSERVED', state='ENTRY_NOT_OBSERVED')
    if (parent.execution_task != ObjectIdentity.from_record(task.task_id, task)
            or parent.implementation_commit != plan.implementation_commit
            or parent.attempt_id not in {a.attempt_id for a in index.task(task.task_id).attempts}):
        raise PermissionError('preparation observation changes the original task or attempt')
    store = ExternalNativeSubworkStore(plane=writer, parent_contacts=contacts, parent_contact=parent, completed_only=True)
    definitions = [store.read_definition(pin) for roster in store.iter_rosters(parent) for pin in roster.subworks]
    if not definitions:
        return None, dict(entry='UNKNOWN', raw_return='UNKNOWN', publication='UNAVAILABLE',
            completion_receipt='UNAVAILABLE', state='PARENT_CONTACT_WITHOUT_SUBWORK_ROSTER')
    if len(definitions) != 1:
        raise PermissionError('preparation observation changes its selected one-effect task')
    definition, = definitions
    if (definition.code_sources_sha256, definition.dependency_lock_sha256) != (
            source.code_sources_sha256, source.dependency_lock_sha256):
        raise PermissionError('preparation observation changes its original worker source')
    if prefix:
        from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_operation import CAPABILITY, operands
        if (definition.subwork_id != 'active-prefix.' + config.original.model_name or definition.operation_id != CAPABILITY
                or definition.sources != operands(config)
                or definition.configuration not in {s.identity for s in config.original.seeds}):
            raise PermissionError('preparation observation changes the original prefix definition')
    else:
        from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_operation import definition_for
        if definition != definition_for(config, parent=parent, materialization_ids=definition.input_materialization_ids):
            raise PermissionError('preparation observation changes the selected response effect')
    return definition, native_progress_record(store, definition)


def checkpoint_seals(config, definition):
    """Observe bounded canonical seals, leaving array and geometry checks pending."""
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_checkpoint import ActivePreparationCheckpoint
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_evaluation import CompletePreparationEvaluation
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_continuation import original_configuration
    from empirical_lawhood.storage.bounded_io import read_bounded_bytes
    root = Path(config.original.work_directory) / definition.subwork_id
    if any(p.is_symlink() for p in (root, *root.parents)):
        raise PermissionError('checkpoint observation refuses redirected native custody')
    if not root.exists():
        return (), ()
    if not root.is_dir():
        raise PermissionError('checkpoint observation requires an original native directory')
    allowance = dict(config.prefix.model_allowances)[config.original.model_name]
    checkpoints, evaluations = [], []
    # The finite purchase bounds both rosters. No unbounded directory scan or array read.
    for number in range(allowance + 1):
        for stem, kind, target in (('accepted', ActivePreparationCheckpoint, checkpoints),
                                   ('evaluation', CompletePreparationEvaluation, evaluations)):
            if stem == 'evaluation' and number == 0:
                continue
            path = root / (stem + '-' + f'{number:08d}' + '.json')
            if not path.exists() and not path.is_symlink():
                continue
            if path.is_symlink():
                raise PermissionError('checkpoint seal is not an original regular file')
            record = decode_canonical_bytes(read_bounded_bytes(path, maximum_bytes=64 * 1024), kind, maximum_bytes=64 * 1024)
            if (record.configuration, record.seed, record.prototype) != (original_configuration(config), definition.configuration,
                    config.original.prototype.identity):
                raise PermissionError('checkpoint seal changes original configuration, seed or operator')
            if (record.iterations if stem == 'accepted' else record.ordinal) != number:
                raise PermissionError('checkpoint seal changes its declared native order')
            target.append(record)
    return tuple(checkpoints), tuple(evaluations)


def prefix_positions(config, definition, progress, readout):
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_continuation import original_configuration
    inherited = (readout is None and hasattr(config, 'continuation') and progress['state'] == 'ENTRY_NOT_OBSERVED')
    if inherited:
        readout = config.continuation.readout
    seals, evaluations = ((), ()) if definition is None else checkpoint_seals(config, definition)
    assessment = None if readout is None else readout.assessment
    if readout is not None and readout.original_result.configuration != original_configuration(config):
        raise PermissionError('checkpoint observation substitutes an independent readout')
    source = config.identity if definition is None else definition.identity
    rows = []
    for name, seal in (('initial', seals[0] if seals else None), ('later', seals[-1] if len(seals) > 1 else None)):
        position = None if assessment is None else next(p for p in assessment.positions if p.position == name)
        rows.append(dict(id=config.original.model_name + '.' + name, label=config.original.model_name + ' ' + name,
            genotype='I95M' if config.original.model_name == 'm1-i95m' else 'WT',
            checkpoint=name, trial=('COMPLETE_RETURN_SEALS_' + str(len(evaluations)) if evaluations else progress['state']),
            safe_state=('PUBLISHED_ASSESSED_' + position.disposition if position is not None else
                'ACCEPTED_SEAL_PENDING_ARRAY_AND_GEOMETRY_READ' if seal is not None else 'UNAVAILABLE'),
            publication=progress['publication'],
            independent_reading=('ORIGINAL_CONTINUATION_INPUT_ASSESSED' if inherited else
                'PUBLISHED_READOUT_CURRENT_ARRAY_RECHECK_DEFERRED' if assessment is not None else
                'REFUSED_' + type(readout).__name__ if readout is not None else 'NOT_YET_PUBLISHED'),
            continuation=assessment.continuation if assessment is not None else 'UNAVAILABLE_PENDING_INDEPENDENT_READ',
            source=identity(position.checkpoint if position is not None and position.checkpoint is not None else
                seal.identity if seal is not None else source)))
    count = (len(assessment.evaluations) if assessment is not None and assessment.complete_native_return_ledger else
        0 if progress['state'] == 'ENTRY_NOT_OBSERVED' else None)
    return rows, count


def observe(context, directory, artifact_writer, selection):
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_operation import config_types, node_id as prefix_node
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_read import ActivePreparationPrefixReadout
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_operation import node_id as point_node
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_read import PreparationResponsePointReadout
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_analysis_operation import config_types as analysis_config_types
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_supply_operation import PreparationSupplyConfig
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_supply_policy import supply_owners
    packet, draft, source, _ = load_selected(context=context, directory=directory, artifact_writer=artifact_writer)
    control_packet, _, plan, index, control_source, access = load_development_execution_controls(directory=directory, artifact_writer=artifact_writer)
    if (access is not None or control_packet != packet or control_source != source
            or (packet.fingerprint(), index.run_id, source.code_sources_sha256) !=
            (selection['binding']['packet_sha256'], selection['binding']['run_id'], selection['binding']['worker_source_sha256'])):
        raise PermissionError('preparation observation changes original packet, run, source or access')
    report = read_execution_records(writer=artifact_writer, plan=plan, index=index)
    configs, _, _, _ = supply_owners(draft)
    prefix = type(configs[0]) in config_types()
    analysis = type(configs[0]) in (*analysis_config_types(), PreparationSupplyConfig)
    positions, effects, counts = [], [], []
    if not analysis:
        tasks = {t.task_id: t for t in plan.tasks}
        for config in configs:
            task = prefix_node(config) if prefix else point_node(config)
            definition, progress = selected_native(writer=artifact_writer, plan=plan, index=index, source=source,
                config=config, task=tasks[task], prefix=prefix)
            readout = published_readout(writer=artifact_writer, run_id=index.run_id, task=task,
                attempts=report['operational_census'], kind=ActivePreparationPrefixReadout if prefix else PreparationResponsePointReadout)
            if prefix:
                rows, count = prefix_positions(config, definition, progress, readout)
                positions.extend(rows)
            else:
                effect = config.point.effect
                if readout is not None and (readout.configuration != config.identity or readout.point != config.point):
                    raise PermissionError('response observation substitutes its selected independent readout')
                result = None if readout is None else readout.original.original_result
                returned = None if result is None else result.returned.returned
                complete = (result is not None and result.returned.error is None and returned is not None
                    and returned.energy is not None and returned.gradient is not None)
                count = 1 if complete else 0 if readout is not None or progress['state'] == 'ENTRY_NOT_OBSERVED' else None
                effects.append(dict(id=effect.effect_id, stage=effect.stage,
                    position=effect.model_name + '.' + effect.position, direction=effect.direction,
                    scale=str(effect.signed_step_bohr.copy_abs()), side='plus' if effect.signed_step_bohr > 0 else 'minus',
                    **{key: progress[key] for key in ('entry', 'raw_return', 'publication', 'completion_receipt')},
                    complete_force_return='PUBLISHED_INDEPENDENT_COMPLETE_RETURN' if complete else
                        'NOT_AVAILABLE' if count == 0 else 'UNKNOWN_PENDING_INDEPENDENT_READ',
                    source=identity(effect.identity)))
            counts.append(count)
    stage = 'assessment' if analysis else 'preparation' if prefix else configs[0].point.effect.stage
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import is_environmental
    environmental = not prefix and not analysis and is_environmental(configs[0].protocol)
    dependencies = ([] if prefix else ['preparation'] if stage in ('diagnostic', 'initial-primary') else
        ['initial-primary-assessment'] if stage == 'environment-diagnostic' else
        ['environment-diagnostic-assessment'] if environmental else ['diagnostic'])
    allowance = 0 if analysis else sum(n for _, n in configs[0].prefix.model_allowances) if prefix else len(configs)
    total = None if any(c is None for c in counts) else sum(counts)
    value = dict(schema=DOMAIN_SCHEMA, version=VERSION, status='SUPPORTED',
        binding={key: selection['binding'][key] for key in ('run_id', 'packet_sha256')}, positions=positions,
        effects=effects, allowances=[dict(stage=stage, allowance=allowance, complete_returns=total,
            state=report['status'], depends_on=dependencies,
            source=identity(configs[0].identity))], complete_return_count=total,
        return_count_scope=('Original prefix allowance and cumulative independently published return ledger, including retained continuation inputs.'
            if prefix else 'Selected wave only, from its published independent complete-return ledger.')
            + ' Live seals and receipts alone do not count.',
        pending_bindings=[])
    validate_domain(value)
    if len(document_bytes(value)) > 1024**2:
        raise ValueError('preparation observation exceeds its complete bounded metadata contract')
    return value
