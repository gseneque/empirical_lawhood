# SPDX-License-Identifier: MPL-2.0
"""Local acquisition graph composition beneath one immutable global programme."""
from dataclasses import replace
from hashlib import sha256

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec

from .commitment import ScheduledCommitment
from .compact_records import NAMESPACE as COMPACT_NAMESPACE, ScheduledCompactBank
from .operation_bindings import BUDGET
from .programme_composition import compile_programme_wave, expected_global_commitment, programme_wave_task_ids


def programme_acquisition_draft(*, scope, bank, global_parent_binding,
        proof_owners, operational_budgets, template_bytes, draft_id, calibration_payload=None):
    """Compose complete local data acquisition with exact actual new owners.

    The original parent binding is a custody input, never manufactured here.
    Confirmation calibration bytes are opaque caller-supplied source bytes;
    parent authentication and outcome authority remain the public entry owner.
    """
    from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft
    from .programme_acquisition import (ScheduledProgrammeAcquisitionAdmission,
        ScheduledProgrammeAcquisitionAdmissionConfig, ScheduledProgrammeAcquisitionCollectorConfig, acquisition_root)
    from .programme_acquisition_bindings import operation_registrations
    from .records import _publication

    programme, wave_id = scope.programme, scope.wave.wave_id
    root = acquisition_root(scope, bank)
    global_parent_binding.__post_init__()
    global_parent = global_parent_binding.parent
    global_parent_publication = global_parent_binding.publication
    global_parent_receipt = global_parent_binding.receipt
    global_parent_receipt_publication = global_parent_binding.receipt_publication
    if (global_parent.programme != programme.identity or global_parent.bank != programme.bank
            or global_parent.semantic_commitment != expected_global_commitment(bank)):
        raise ValueError('acquisition wave substitutes its actual mode-specific original global preparation')
    _publication(global_parent_publication, global_parent)
    _publication(global_parent_receipt_publication, global_parent_receipt)
    tasks = programme_wave_task_ids(programme, bank, wave_id)
    plan, operands = compile_programme_wave(programme=programme, bank=bank, wave_id=wave_id,
        proof_owners=tuple((owner, task) for owner, task in proof_owners if task in tasks),
        operational_budgets={task: operational_budgets[task] for task in tasks}, template_bytes=template_bytes)
    registrations = {r.selection.capability_key.rsplit('.', 1)[-1]: r for r in operation_registrations()}
    operations = [replace(o, selection=registrations[o.selection.capability_key.rsplit('.', 1)[-1]].selection)
        for o in plan.operations]
    admission_config = ScheduledProgrammeAcquisitionAdmissionConfig('config.'+wave_id+'.acquisition-open', scope, global_parent_binding)
    admission = ScheduledProgrammeAcquisitionAdmission('admission.acquisition.'+wave_id,
        admission_config.identity, scope, global_parent_binding, global_parent.semantic_commitment)
    collector_config = ScheduledProgrammeAcquisitionCollectorConfig('config.'+wave_id+'.acquisition-collect', programme.identity,
        programme.bank, plan.wave, scope.identity, admission.identity, programme.mode)
    if programme.mode == 'E4_CONFIRMATION':
        publication = bank.forecast_design.calibration_publication
        if (type(calibration_payload) is not bytes or len(calibration_payload) != publication.materialization.size_bytes
                or sha256(calibration_payload).hexdigest() != publication.logical.content_sha256):
            raise ValueError('confirmation acquisition omits exact opaque original calibration source bytes')
        operands[publication.logical.logical_artifact_id] = calibration_payload
    elif calibration_payload is not None:
        raise ValueError('uncalibrated acquisition cannot alias a protected parent payload')
    for task, role, config in ((wave_id+'.open', 'open', admission_config),
            (wave_id+'.collect', collector_config.operation, collector_config)):
        owners = tuple(owner for owner, node in proof_owners if node == task)
        budget = operational_budgets.get(task)
        if not owners or budget is None or not BUDGET.contains(budget):
            raise ValueError('programme wave controls omit explicit owners or contained budgets')
        operations.append(RecursiveOperationSpec.from_config(node_id=task, selection=registrations[role].selection,
            config_id=config.config_id, config=config, obligation_ids=owners, resource_budget=budget))
    links = []
    for link in plan.links:
        if link.consumer_input_id == 'commitment':
            links.append(replace(link, edge_id='edge.'+link.consumer_node_id+'.admission', consumer_input_id='admission',
                producer_node_id=wave_id+'.open', producer_output_id='product', external_input_id=None))
        else:
            links.append(link)
    bank_external = next(e.input_id for e in plan.external_inputs if e.payload_schema == ScheduledCompactBank.SCHEMA)
    global_external = 'external.'+global_parent_publication.logical.logical_artifact_id
    external = [e for e in plan.external_inputs if e.payload_schema != ScheduledCommitment.SCHEMA]
    external.append(RecursiveExternalInput(global_external, global_parent_publication.logical.logical_artifact_id,
        global_parent.SCHEMA, 'application/json', global_parent_publication.materialization.size_bytes,
        OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, global_parent.fingerprint(), 'SOURCE'))
    operands[global_parent_publication.logical.logical_artifact_id] = global_parent
    receipt_external = 'external.'+global_parent_receipt_publication.logical.logical_artifact_id
    external.append(RecursiveExternalInput(receipt_external, global_parent_receipt_publication.logical.logical_artifact_id,
        global_parent_receipt.SCHEMA, 'application/json', global_parent_receipt_publication.materialization.size_bytes,
        OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, global_parent_receipt.fingerprint(), 'SOURCE'))
    operands[global_parent_receipt_publication.logical.logical_artifact_id] = global_parent_receipt
    for task, port, producer, source in ((wave_id+'.open', 'bank', None, bank_external),
            (wave_id+'.open', 'confirmation-global-parent' if programme.mode == 'E4_CONFIRMATION' else 'global-parent', None, global_external),
            (wave_id+'.open', 'global-parent-receipt', None, receipt_external), (wave_id+'.collect', 'bank', None, bank_external),
            (wave_id+'.collect', 'admission', wave_id+'.open', None)):
        links.append(RecursiveInputLink('edge.'+task+'.'+port, task, port, producer_node_id=producer,
            producer_output_id='product' if producer else None, external_input_id=source, scientific_role='SOURCE'))
    for operation in plan.operations:
        role = operation.selection.capability_key.rsplit('.', 1)[-1]
        port = 'products.'+role.removesuffix('-development').replace('forecast-calibrated', 'forecast')+'.'+operation.node_id.removeprefix(COMPACT_NAMESPACE+'.').removesuffix('.'+role)
        links.append(RecursiveInputLink('edge.'+wave_id+'.collect.'+port, wave_id+'.collect', port,
            producer_node_id=operation.node_id, producer_output_id='product', scientific_role='OUTCOME'))
    expected_tasks = {o.node_id for o in operations}
    if set(operational_budgets) != expected_tasks or {node for _, node in proof_owners} != expected_tasks:
        raise ValueError('programme wave actual explicit owner/budget census differs from the admitted graph')
    draft = RecursiveStudyDraft(draft_id, root.question, root.campaign, (), (), (),
        tuple(sorted(operations, key=lambda o: o.node_id)), tuple(sorted(external, key=lambda e: e.input_id)),
        tuple(sorted(links, key=lambda e: e.edge_id)), tuple(sorted(expected_tasks)), prospective_draft=root)
    return draft, operands
