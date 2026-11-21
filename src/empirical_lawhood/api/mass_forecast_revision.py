# SPDX-License-Identifier: MPL-2.0
"""Authenticate a retained source before preparing its explicit derivative workflow."""

from hashlib import sha256
import json
from pathlib import Path
import sys

from empirical_lawhood.methods.mass_balance_starter.records import MassAssessment, MassForecast
from empirical_lawhood.methods.mass_balance_revision import design, experiment
from empirical_lawhood.methods.mass_balance_revision.records import MAX_BYTES, MAX_SOURCE_BYTES, PROTOCOL_ID, ForecastUpgradeSource, ForecastUpgradeSpecification, MassForecastV2
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.design.experiment_inputs import ExperimentInputBinding, ExperimentInputSelection


def create_inputs(*, authoring_directory, project_root, operator_profile, output_directory, source_operator_profile=None):
    """Derive the complete original custody through its existing authenticated reader."""
    from empirical_lawhood.api.application_context import application_storage
    from empirical_lawhood.api.application_contracts import ApplicationContext
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.api.recursive_execution import _read_recursive_wave_with_retained_roots

    root = Path(project_root).resolve(strict=True)
    _, _, destination_plane = application_storage(ApplicationContext('mass-balance.upgrade.inputs',
        'Mass forecast derivative inputs', Path(sys.executable), project_root=root,
        operator_profile=Path(operator_profile)), for_write=True)
    destination = Path(output_directory)
    if not destination.is_absolute():
        raise ValueError('forecast upgrade requires a new explicit absolute input destination')
    destination = destination_plane.root.resolve(
        destination.relative_to(destination_plane.root.contract.canonical_path).as_posix(), for_write=True)
    if destination.exists():
        raise FileExistsError('forecast upgrade input destination already exists')
    _, _, original_plane = application_storage(ApplicationContext('mass-balance.upgrade.original',
        'Original retained mass forecast', Path(sys.executable),
        operator_profile=Path(operator_profile if source_operator_profile is None else source_operator_profile)))
    (report, products, _, plan), roots = _read_recursive_wave_with_retained_roots(
        directory=Path(authoring_directory), artifact_writer=original_plane, include_products=True)
    packet = roots[0]
    if (report.get('scientific_result', {}).get('namespace') != 'mass-balance'
            or report['scientific_result'].get('scientific_completion') != 'COMPLETED'
            or report['scientific_result'].get('evidence_scope') != 'EXPOSED_DEVELOPMENT'):
        raise ValueError('forecast upgrade requires a complete original exposed mass-balance study')
    forecasts = tuple(record for values in products['records'].values() for record in values.values() if type(record) is MassForecast)
    assessments = tuple(record for values in products['records'].values() for record in values.values() if type(record) is MassAssessment)
    if len(forecasts) != 1 or len(assessments) != 1 or len(products['receipts']) != 2:
        raise ValueError('forecast upgrade requires the exact complete original two-operation result')
    forecast, assessment = forecasts[0], assessments[0]
    receipts = tuple(sorted(products['receipts'].values(), key=lambda value:value.receipt_id))
    packet_pin = ObjectIdentity.from_record(packet.packet_id, packet)
    plan_pin = ObjectIdentity.from_record(plan.execution_plan_id, plan)
    name = sha256(canonical_json_bytes((packet_pin, plan_pin, tuple(
        ObjectIdentity.from_record(receipt.receipt_id, receipt) for receipt in receipts)))).hexdigest()
    source = ForecastUpgradeSource('mass-balance.upgrade-source.' + name, forecast, assessment, receipts,
        packet_pin, plan_pin, packet.implementation)
    specification = ForecastUpgradeSpecification('specification.mass-balance.upgrade.' + source.fingerprint(),
        source.identity, forecast.config.scope, forecast.config.independent_unit_ids)
    experiment.bind_inputs(specification, {'original':source})
    selection = ExperimentInputSelection('inputs.mass-balance.upgrade.' + specification.fingerprint(), PROTOCOL_ID,
        (ExperimentInputBinding('original', source.identity, 'original.json', source.canonical_size_bytes()),))
    implementation = implementation_binding(root)
    payloads = {'original.json':source.canonical_bytes(), 'specification.json':specification.canonical_bytes(),
        'sources.json':selection.canonical_bytes(), 'source-snapshot.json':implementation.canonical_bytes(),
        'original-read-report.json':(json.dumps(report, indent=2, sort_keys=True) + '\n').encode()}
    if (len(payloads['original.json']) > MAX_SOURCE_BYTES
            or any(len(raw) > 2 * 1024**2 for raw in payloads.values())):
        raise ValueError('forecast upgrade input package exceeds its declared source or metadata bound')
    destination_plane.root.verify(for_write=True)
    destination.mkdir(parents=True, exist_ok=False)
    for filename, raw in sorted(payloads.items()):
        with (destination / filename).open('xb') as stream:
            stream.write(raw)
    return {'specification':str(destination / 'specification.json'), 'sources':str(destination / 'sources.json'),
        'source_snapshot':str(destination / 'source-snapshot.json'), 'original':source.identity.to_document(),
        'original_read_report':str(destination / 'original-read-report.json'),
        'original_claim_disposition':report['scientific_result']['claim_disposition'],
        'qualification':'NOT_ESTABLISHED', 'new_measurements':0, 'native_contact_count':0}


def read_result(*, directory, artifact_writer, specification, instance, payloads, report, products, draft, plan, allow_partial=False):
    """Present the retained derivative and the unchanged original scientific findings."""
    if type(specification) is not ForecastUpgradeSpecification or instance.specification != specification.identity:
        raise PermissionError('forecast upgrade read substitutes its exact original specification')
    config = design.config_for(specification)
    base = {'namespace':'mass-balance', 'record_revision':'2.0.0', 'conversion':specification.conversion,
        'assigned_units':len(specification.independent_unit_ids), 'independent_unit_ids':specification.independent_unit_ids,
        'evidence_scope':'EXPOSED_DEVELOPMENT', 'qualification':'NOT_ESTABLISHED', 'new_measurements':0,
        'scientific_reconstruction_performed':False, 'native_acquisition_performed':False}
    if allow_partial or report.get('typed_product_validation') == 'DEFERRED':
        return {**base, 'scientific_completion':'DEFERRED'}
    name = 'experiment-source-' + sha256(specification.source.object_id.encode()).hexdigest() + '.json'
    source = decode_canonical_bytes(payloads[name], ForecastUpgradeSource, maximum_bytes=MAX_SOURCE_BYTES)
    experiment.bind_inputs(specification, {'original':source})
    if ({task.task_id for task in plan.tasks} != {config.node_id}
            or report.get('run_id') != plan.source_plan.object_id):
        raise PermissionError('forecast upgrade read changes its complete original operation census')
    receipt = products['receipts'].get(config.node_id)
    if receipt is None or receipt.operational_status is not OperationalStatus.SUCCEEDED:
        return {**base, 'scientific_completion':'INCOMPLETE'}
    product = products['records'].get(config.node_id, {}).get(config.node_id + '.product')
    if type(product) is not MassForecastV2 or product.config != config or product.original_source != source:
        raise PermissionError('forecast upgrade read substitutes its original derivative source or revision')
    product.__post_init__()
    if product.canonical_size_bytes() > MAX_BYTES:
        raise PermissionError('forecast upgrade result exceeds its original output contract')
    counts = {key:sum(row.disposition == key for row in source.assessment.rows)
        for key in ('SATISFIED', 'FALSIFIED', 'UNEVALUABLE')}
    return {**base, 'scientific_completion':'COMPLETED', 'representation_disposition':'SATISFIED',
        'original_claim_disposition':'FALSIFIED' if counts['FALSIFIED'] else 'UNEVALUABLE' if counts['UNEVALUABLE'] else 'SATISFIED',
        'original_counts':counts, 'original_forecast':source.forecast.identity.to_document(),
        'original_assessment':source.assessment.identity.to_document(),
        'original_receipts':tuple(ObjectIdentity.from_record(row.receipt_id, row).to_document() for row in source.producing_receipts),
        'original_implementation':source.original_implementation.to_document(), 'derivative':product.identity.to_document(),
        'findings':tuple({'unit_id':row.unit_id, 'original_kg':str(row.original_kg), 'final_g':str(row.final_g),
            'units':row.units, 'original_disposition':old.disposition, 'original_reason_codes':old.reason_codes}
            for row, old in zip(product.rows, source.assessment.rows, strict=True))}
