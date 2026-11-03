# SPDX-License-Identifier: MPL-2.0
"""One complete global calibration and its separate reveal operation.

Original whole-wave plans are checked here and authenticated sequentially by
the public entry owner. Only their bounded custody summaries enter this graph.
Composition supplies no scientific qualification, issue or reveal authority.
"""

from hashlib import sha256

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.recursive_authoring import (
    RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft,
)
from empirical_lawhood.planning.study_authoring import StudyDraft

from .compact_records import ScheduledCompactBank, compact_identity
from .operation_bindings import BUDGET
from .programme_calibration import (
    CALIBRATE_TASK_ID, MAXIMUM_CALIBRATION_BYTES, QUALIFY_TASK_ID,
    ScheduledProgrammeCalibrationConfig, ScheduledProgrammeWaveCustody, validate_wave_custody,
)
from .programme_calibration_bindings import calibration_registrations
from .programme_acquisition_custody import ScheduledProgrammeAcquisitionWaveCustody, validate_acquisition_plan
from .programme_records import NAMESPACE, ScheduledProgramme, validate_programme_bank
from .programme_reduction import ScheduledProgrammeWaveResult
from .programme_tail_freeze import (
    CONFIG_ID as TAIL_FREEZE_CONFIG_ID, TASK_ID as TAIL_FREEZE_TASK_ID,
    ScheduledProgrammeTailFreezeConfig, operation_factories as tail_freeze_factories,
)

BLIND, SEALED = OutcomeAccess.OUTCOME_BLIND, OutcomeAccess.EVALUATION_SEALED
PROSPECTIVE = VisibilityCeiling.PROSPECTIVE


def programme_tail_task_ids():
    return tuple(sorted((TAIL_FREEZE_TASK_ID, CALIBRATE_TASK_ID, QUALIFY_TASK_ID)))


def programme_tail_draft(*, root, programme, bank, wave_custody, execution_plans,
        proof_owners, operational_budgets, calibration_id, draft_id, wave_results=None, wave_payloads=None):
    """Keep every original wave once beneath the complete scientific root.

    The caller supplies explicit proof owners and resource budgets. Published
    results, collector configurations and receipts retain their original pins.
    Typed ``wave_results`` must already be exposed software-fixture data.
    Production uses opaque ``wave_payloads`` and defers semantic decoding to
    the issued sealed calibrator. This function never opens a protected store.
    The unchanged generic authoring API consumes the returned source records;
    its programme wrapper must authenticate the original custody before entry.
    """
    if (type(root) is not StudyDraft or root.experiment is None or root.campaign is None
            or type(programme) is not ScheduledProgramme or programme.mode != 'E4_REVISION_CALIBRATION'
            or type(bank) is not ScheduledCompactBank):
        raise ValueError('programme tail requires its complete original revision-calibration scientific root')
    validate_programme_bank(programme, bank)
    if (tuple(sorted((*root.development_unit_ids, *root.evaluation_unit_ids))) != programme.group_ids
            or root.development_unit_ids or root.experiment.information_cutoffs !=
                tuple(case.information_cutoff for case in programme.cases)):
        raise ValueError('programme tail changes its complete original global group/cutoff census')
    # Typed outcomes are an explicitly exposed software-test path. Production
    # callers supply opaque source payloads; no sealed outcome is decoded here.
    results = None if wave_results is None else tuple(wave_results)
    custody, plans = tuple(wave_custody), tuple(execution_plans)
    waves = tuple(wave.wave_id for wave in programme.waves)
    if (len(waves) != 16 or (results is not None and (any(type(value) is not ScheduledProgrammeWaveResult for value in results)
                or tuple(value.wave_id for value in results) != waves))
            or any(type(value) not in (ScheduledProgrammeWaveCustody, ScheduledProgrammeAcquisitionWaveCustody) for value in custody)
            or len({type(value) for value in custody}) != 1
            or tuple(value.wave_id for value in custody) != waves or len(plans) != len(waves)):
        raise ValueError('programme tail omits, duplicates or reorders an original whole-group wave')
    if (results is None) == (wave_payloads is None):
        raise ValueError('programme tail requires exactly one opaque-source or exposed-software-outcome path')
    from .programme_bindings import operation_manifests
    from .compact_records import NAMESPACE as COMPACT_NAMESPACE
    manifests = {value.capability_key: value for value in operation_manifests()}
    for index, (binding, plan) in enumerate(zip(custody, plans, strict=True)):
        if type(binding) is ScheduledProgrammeAcquisitionWaveCustody:
            validate_acquisition_plan(programme, binding, plan)
        if (binding.configuration.programme != programme.identity or binding.configuration.bank != programme.bank
                or binding.configuration.wave != programme.waves[index]
                or ObjectIdentity.from_record(plan.execution_plan_id, plan) != binding.execution_plan
                or tuple(task for task in plan.tasks if task.task_id == binding.producer_task.task_id) != (binding.producer_task,)
                or plan.implementation_commit != binding.receipt.implementation_commit):
            raise ValueError('programme tail substitutes its actual original full plan/configuration/custody scope')
        expected = {COMPACT_NAMESPACE+'.'+root_id+'.'+role for root_id in binding.configuration.wave.root_ids
            for role in ('prefix', 'numerical', 'measure', 'check', 'project', 'forecast', 'continue',
                'full-numerical', 'physical-forecast', 'responses', 'response-score')}
        if {task.task_id for task in plan.tasks} != expected | {binding.wave_id+'.open', binding.wave_id+'.collect'}:
            raise ValueError('programme tail thins the complete original whole-wave task census')
        if type(binding) is ScheduledProgrammeWaveCustody:
            for task in plan.tasks:
                role = task.task_id.rsplit('.', 1)[-1]
                owner = manifests[NAMESPACE+'.'+role]
                if (task.capability.capability_key != owner.capability_key or task.capability.capability_version != owner.capability_version
                        or task.capability_implementation_sha256 != owner.implementation_sha256
                        or task.capability.config.config_schema != owner.config_schema
                        or task.capability.config.config_schema_sha256 != owner.config_schema_sha256):
                    raise ValueError('programme tail substitutes an actual installed whole-wave provider contract')
        if results is not None:
            validate_wave_custody(programme, results[index], binding, plan)
    if results is None and set(wave_payloads) != {binding.publication.logical.logical_artifact_id for binding in custody}:
        raise ValueError('programme tail changes its exact opaque original wave source census')

    tasks = programme_tail_task_ids()
    if (set(operational_budgets) != set(tasks) or {task for _, task in proof_owners} != set(tasks)
            or len(set(proof_owners)) != len(proof_owners)
            or len({owner for owner, _ in proof_owners}) != len(proof_owners)):
        raise ValueError('programme tail changes its explicit exact proof-owner or resource census')
    registrations = {row.selection.capability_key.rsplit('.', 1)[-1]: row for row in calibration_registrations()}
    operations, external, links, records = [], {}, [], {}

    def add(record, *, key=None, publication=None, access=BLIND, role='SOURCE'):
        raw = record.canonical_bytes()
        if len(raw) > MAXIMUM_CALIBRATION_BYTES:
            raise ValueError('programme tail source exceeds its unchanged closed16MiB record contract')
        if publication is not None:
            logical, physical = publication.logical, publication.materialization
            if (logical.payload_schema != record.SCHEMA or logical.content_sha256 != record.fingerprint()
                    or physical.physical_sha256 != logical.content_sha256 or physical.size_bytes != len(raw)
                    or logical.media_type != 'application/json' or logical.outcome_access is not access
                    or logical.visibility_ceiling is not PROSPECTIVE):
                raise ValueError('programme tail substitutes original publication bytes or source/outcome boundary')
            key = logical.logical_artifact_id
        if key is None:
            raise ValueError('programme tail source omits its actual stable artifact identity')
        name = 'external.'+key
        value = RecursiveExternalInput(name, key, record.SCHEMA, 'application/json', len(raw),
            access, PROSPECTIVE, record.fingerprint(), role)
        if external.setdefault(name, value) != value or records.setdefault(key, record) != record:
            raise ValueError('programme tail aliases different original source bytes')
        return name

    def source(task, port, name, *, role='SOURCE'):
        links.append(RecursiveInputLink('edge.'+task+'.'+port, task, port,
            external_input_id=name, scientific_role=role))

    bank_source = add(bank, key=bank.bank_id)
    pins = tuple(value.identity for value in custody)
    freeze_factory, = tail_freeze_factories()
    freeze_config = ScheduledProgrammeTailFreezeConfig(TAIL_FREEZE_CONFIG_ID, programme, programme.bank, pins)
    freeze_budget = operational_budgets[TAIL_FREEZE_TASK_ID]
    if (not BUDGET.contains(freeze_budget) or freeze_budget.output_bytes is None
            or freeze_budget.output_bytes > MAXIMUM_CALIBRATION_BYTES):
        raise ValueError('programme tail metadata freeze exceeds its closed downstream record contract')
    operations.append(RecursiveOperationSpec.from_config(node_id=TAIL_FREEZE_TASK_ID,
        selection=freeze_factory.registration.selection, config_id=freeze_config.config_id, config=freeze_config,
        obligation_ids=tuple(sorted(owner for owner, task in proof_owners if task == TAIL_FREEZE_TASK_ID)),
        resource_budget=freeze_budget))
    source(TAIL_FREEZE_TASK_ID, 'bank', bank_source)
    for role, task in (('calibrate', CALIBRATE_TASK_ID), ('calibration-qualify', QUALIFY_TASK_ID)):
        budget = operational_budgets[task]
        if (not BUDGET.contains(budget) or budget.output_bytes is None
                or budget.output_bytes > MAXIMUM_CALIBRATION_BYTES):
            raise ValueError('programme tail output budget exceeds its closed downstream record contract')
        config = ScheduledProgrammeCalibrationConfig('config.'+NAMESPACE+'.'+role, role,
            programme, compact_identity(bank), calibration_id, pins)
        operations.append(RecursiveOperationSpec.from_config(node_id=task,
            selection=registrations[role].selection, config_id=config.config_id, config=config,
            obligation_ids=tuple(sorted(owner for owner, node in proof_owners if node == task)), resource_budget=budget))
        source(task, 'bank', bank_source)
    links.append(RecursiveInputLink('edge.'+CALIBRATE_TASK_ID+'.tail-freeze', CALIBRATE_TASK_ID, 'tail-freeze',
        producer_node_id=TAIL_FREEZE_TASK_ID, producer_output_id='product', scientific_role='SOURCE'))
    for index, binding in enumerate(custody):
        suffix = '.'+binding.wave_id
        if results is not None:
            result_source = add(results[index], publication=binding.publication, access=SEALED, role='HISTORY')
        else:
            publication = binding.publication
            key, raw = publication.logical.logical_artifact_id, wave_payloads[publication.logical.logical_artifact_id]
            if (type(raw) is not bytes or len(raw) != publication.materialization.size_bytes
                    or len(raw) > MAXIMUM_CALIBRATION_BYTES or sha256(raw).hexdigest() != binding.result.object_fingerprint
                    or publication.logical.outcome_access is not SEALED or publication.logical.visibility_ceiling is not PROSPECTIVE):
                raise ValueError('programme tail changes exact opaque sealed source bytes or boundary')
            result_source = 'external.'+key
            external[result_source] = RecursiveExternalInput(result_source, key, ScheduledProgrammeWaveResult.SCHEMA,
                'application/json', len(raw), SEALED, PROSPECTIVE, binding.result.object_fingerprint, 'HISTORY')
            records[key] = raw
        source(CALIBRATE_TASK_ID, 'waves'+suffix, result_source, role='HISTORY')
        acquisition = type(binding) is ScheduledProgrammeAcquisitionWaveCustody
        custody_source = add(binding, key=binding.binding_id)
        custody_port = ('acquisition-wave-custody' if acquisition else 'wave-custody')+suffix
        source(CALIBRATE_TASK_ID, custody_port, custody_source)
        source(TAIL_FREEZE_TASK_ID, custody_port, custody_source)
        source(CALIBRATE_TASK_ID, 'wave-receipts'+suffix,
            add(binding.receipt, publication=binding.receipt_publication))
        source(CALIBRATE_TASK_ID, ('acquisition-wave-configurations' if acquisition else 'wave-configurations')+suffix,
            add(binding.configuration, publication=binding.configuration_publication))
    for port, output in (('calibration', 'product'), ('evidence', 'evidence')):
        links.append(RecursiveInputLink('edge.'+QUALIFY_TASK_ID+'.'+port, QUALIFY_TASK_ID, port,
            producer_node_id=CALIBRATE_TASK_ID, producer_output_id=output, scientific_role='OUTCOME'))
    return RecursiveStudyDraft(draft_id, root.question, root.campaign, (), (), (),
        tuple(sorted(operations, key=lambda value: value.node_id)),
        tuple(sorted(external.values(), key=lambda value: value.input_id)),
        tuple(sorted(links, key=lambda value: value.edge_id)), tasks, prospective_draft=root), records
