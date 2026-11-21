# SPDX-License-Identifier: MPL-2.0
"""Public SCI02-D input construction, authenticated continuation and readback."""
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge import bindings as binding, experiment
from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge.records import BridgeDesign, BridgeSelection, BridgeProduct, BridgeCheckpoint, PROTOCOL_ID
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity


def _write_inputs(*, design, selection, campaign, frozen, protocol, project_root, output_directory, audit):
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.storage.numerical_provenance import capture_numerical_provenance
    from empirical_lawhood.design.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding
    destination = Path(output_directory).absolute()
    if destination.exists(): raise FileExistsError('SCI02-D inputs need a new explicit destination')
    provenance, implementation = capture_numerical_provenance(project_root=project_root), implementation_binding(project_root)
    tranche = 'TRAINING' if frozen is None else 'CONFIRMATION'
    spec = experiment.BridgeSpecification('specification.sci02d.'+tranche.lower()+'.'+selection.fingerprint()+'.'+provenance.fingerprint()[:16],
        design.identity, selection.identity, provenance.identity, ObjectIdentity.from_record(campaign.campaign_id, campaign), tranche,
        None if frozen is None else frozen.identity)
    records = dict(design=design, selection=selection, provenance=provenance, campaign=campaign,
        **({} if frozen is None else {'frozen': frozen}))
    experiment.bind_inputs(spec, records)
    sources = ExperimentFileInputSelection('inputs.sci02d.'+spec.fingerprint(), PROTOCOL_ID,
        tuple(ExperimentInputBinding(key, ObjectIdentity.from_record(campaign.campaign_id, value) if key == 'campaign' else value.identity,
            key+'.json', len(value.canonical_bytes())) for key,value in sorted(records.items())), ())
    payloads = {key+'.json': value.canonical_bytes() for key,value in records.items()}
    payloads.update({'specification.json': spec.canonical_bytes(), 'sources.json': sources.canonical_bytes(),
        'source-snapshot.json': implementation.canonical_bytes(), 'protocol.original.md': protocol,
        'input-custody-audit.json': json.dumps(audit, sort_keys=True, indent=2).encode()})
    destination.mkdir(parents=True)
    for name,raw in sorted(payloads.items()):
        with (destination/name).open('xb') as stream: stream.write(raw)
    return {'directory': str(destination), 'specification': str(destination/'specification.json'), 'sources': str(destination/'sources.json'),
        'source_snapshot': str(destination/'source-snapshot.json'), 'tranche': tranche, 'independent_roots': 16 if frozen is None else 72,
        'operations': 34 if frozen is None else 145, 'new_native_contact_cap': 16 if frozen is None else 72,
        'selection': selection.identity.to_document(), 'protocol_sha256': design.protocol_document_sha256}


def create_training_inputs(*, campaign_path, protocol_path, project_root, output_directory):
    """Commit a newly generated stream bank before any native outcome contact."""
    from secrets import token_hex
    from empirical_lawhood.storage.bounded_io import read_bounded_bytes
    from empirical_lawhood.design.campaigns import CampaignSpec
    protocol = read_bounded_bytes(Path(protocol_path), maximum_bytes=1024**2)
    digest = sha256(protocol).hexdigest()
    design = BridgeDesign('design.sci02d.'+digest, digest)
    seed = token_hex(32)
    selection = BridgeSelection('selection.sci02d.'+seed, design, seed)
    campaign = decode_canonical_bytes(read_bounded_bytes(Path(campaign_path), maximum_bytes=4*1024**2), CampaignSpec, maximum_bytes=4*1024**2)
    return _write_inputs(design=design, selection=selection, campaign=campaign, frozen=None, protocol=protocol,
        project_root=project_root, output_directory=output_directory,
        audit={'new_native_contacts': 0, 'new_independent_allocation': {'training': 16, 'confirmation': 64, 'reference': 8},
            'previous_sci02_reservation_reused': False, 'scope': design.scope})


def create_continuation_inputs(*, directory, artifact_writer, protocol_path, project_root, output_directory):
    """Authenticate the complete original training read before freezing its fit."""
    from empirical_lawhood.api.experiment_scientific_read import read_prepared_development_science
    from empirical_lawhood.api.recursive_execution import _read_recursive_wave_with_retained_roots
    from empirical_lawhood.api.matrix_sci02 import _source_record
    from empirical_lawhood.storage.bounded_io import read_bounded_bytes
    from empirical_lawhood.design.campaigns import CampaignSpec
    captured = {}
    def consume(**kwargs):
        summary = read_prepared_development_science(**kwargs)
        if summary is None or summary.get('scientific_completion') != 'COMPLETE_SCI02D_ASSESSMENT':
            raise ValueError('SCI02-D continuation requires its complete independently read predecessor')
        payloads = kwargs['payloads']
        spec = decode_canonical_bytes(payloads['experiment-specification.json'], experiment.BridgeSpecification, maximum_bytes=4*1024**2)
        if spec.tranche != 'TRAINING': raise ValueError('SCI02-D has no further native successor after its finite confirmation')
        fitted = [v for values in kwargs['products']['records'].values() for v in values.values() if type(v) is BridgeProduct and v.config.phase == 'fit']
        if len(fitted) != 1 or fitted[0].fit is None: raise ValueError('SCI02-D training lacks its original frozen estimator')
        frozen = fitted[0]
        captured.update(design=_source_record(payloads, spec.design, BridgeDesign), selection=_source_record(payloads, spec.selection, BridgeSelection),
            campaign=_source_record(payloads, spec.campaign, CampaignSpec), frozen=frozen,
            audit={'predecessor_directory': str(Path(directory).absolute()), 'predecessor_product': frozen.identity.to_document(),
                'predecessor_receipt': kwargs['products']['receipts'][frozen.config.node_id].to_document(),
                'independent_read_sha256': sha256(json.dumps(summary, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest(),
                'new_native_contacts_during_derivation': 0})
        return summary
    _read_recursive_wave_with_retained_roots(directory=directory, artifact_writer=artifact_writer,
        terminal_product_format='references', _scientific_consumer=consume)
    protocol = read_bounded_bytes(Path(protocol_path), maximum_bytes=1024**2)
    if sha256(protocol).hexdigest() != captured['design'].protocol_document_sha256:
        raise ValueError('SCI02-D continuation changes its original frozen scientific protocol')
    return _write_inputs(**captured, protocol=protocol, project_root=project_root, output_directory=output_directory)


def _native_custody(writer, products, tasks, plan, config, provenance, product):
    from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge.native import native_work
    from empirical_lawhood.api.matrix_native_read_custody import _expected_contact
    from empirical_lawhood.api.matrix_native_acquisition_replay import inspect_native
    from empirical_lawhood.storage.native_effect_custody import ExternalNativeEffectContactStore
    from empirical_lawhood.storage.native_subwork import ExternalNativeSubworkStore
    contacts = ExternalNativeEffectContactStore(plane=writer, execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
        visibility_ceiling=binding.VISIBILITY, outcome_access=binding.ACCESS)
    store = ExternalNativeSubworkStore(plane=writer, parent_contacts=contacts)
    receipt = products['receipts'][config.node_id]
    parent = _expected_contact(task=tasks[config.node_id], plan=plan, run_id=receipt.run_id, attempt_id=receipt.attempt_id, products=products)
    if contacts.read(receipt.run_id, config.node_id) != parent: raise PermissionError('SCI02-D parent contact changes actual consumed operands')
    context = SimpleNamespace(input_ports=tuple(SimpleNamespace(materialization_id=v) for v in parent.input_materialization_ids))
    definition, = native_work(context, config, provenance, parent).definitions
    if len(product.native) != 1 or product.native[0].definition != definition:
        raise PermissionError('SCI02-D native event changes original source, streams or parent custody')
    observed = inspect_native(store=store, definition=definition, event=product.native[0], require_nonentry=False)
    checkpoint = decode_canonical_bytes(b''.join(store.iter_completed_output(definition, 'checkpoint')), BridgeCheckpoint, maximum_bytes=binding.MAX_RECORD)
    if (checkpoint.config, checkpoint.arrays, checkpoint.shards, checkpoint.measurements) != (config.identity, product.arrays, product.shards, product.measurements):
        raise PermissionError('SCI02-D product changes its original completed native checkpoint')
    return observed


def values(writer, products, tasks, product):
    from empirical_lawhood.api.matrix_sci02 import _values
    result = {}
    labels = ('arrays', *(('positions', 'gradients') if product.shards else ()))
    for label, operand in zip(labels, (product.arrays, *product.shards), strict=True):
        part = _values(writer, products, tasks, SimpleNamespace(config=product.config, arrays=operand), label=label)
        if set(result)&set(part): raise PermissionError('SCI02-D repeats a retained shard member')
        result.update(part)
    return result


def _check_result(product, actual, expected):
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_read import same
    if set(actual) != set(expected.arrays): raise PermissionError('SCI02-D read changes the complete output member census')
    for key,value in expected.arrays.items(): same(actual[key], value, 'SCI02-D independently read '+key)
    measurements = tuple((k,v) for k,v in product.measurements if not k.startswith('runtime.'))
    if (product.disposition, product.reasons, measurements) != (expected.disposition, expected.reasons, expected.measurements):
        raise PermissionError('SCI02-D read changes original scientific findings')


def read_result(*, directory, artifact_writer, specification, instance, payloads, report, products, draft, plan, allow_partial=False):
    """Validate one complete original tranche without acquiring any trajectory."""
    return _read_result(directory=directory, artifact_writer=artifact_writer, specification=specification,
        instance=instance, payloads=payloads, report=report, products=products, draft=draft, plan=plan,
        allow_partial=allow_partial, reconstruct=True)


def read_recorded_result(*, directory, artifact_writer, specification, instance, payloads, report, products, draft, plan, allow_partial=False):
    """Authenticate recorded products and arrays without independent reconstruction.

    This is historical presentation, not scientific validation. Original source,
    producer, receipt, predecessor, array and completed-native joins stay active.
    The ordinary full scientific reader remains the explicit reconstruction.
    """
    return _read_result(directory=directory, artifact_writer=artifact_writer, specification=specification,
        instance=instance, payloads=payloads, report=report, products=products, draft=draft, plan=plan,
        allow_partial=allow_partial, reconstruct=False)


def _read_result(*, directory, artifact_writer, specification, instance, payloads, report, products, draft, plan,
                 allow_partial, reconstruct):
    from decimal import Decimal
    import time
    if reconstruct:
        from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge import assessment, science, read as reader
    from empirical_lawhood.api.matrix_native_read_custody import _record
    from empirical_lawhood.api.matrix_sci02 import _source_record
    from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
    from empirical_lawhood.science.records.status import OperationalStatus
    cpu, wall = time.process_time(), time.monotonic()
    if type(specification) is not experiment.BridgeSpecification or instance.specification != specification.identity:
        raise PermissionError('SCI02-D read substitutes its exact public instance')
    count = 16 if specification.tranche == 'TRAINING' else 72
    if allow_partial or report.get('typed_product_validation') == 'DEFERRED':
        return {'scientific_completion': 'DEFERRED', 'assigned_roots': count, 'qualification': 'NOT_ESTABLISHED'}
    design = _source_record(payloads, specification.design, BridgeDesign)
    selection = _source_record(payloads, specification.selection, BridgeSelection)
    provenance = _source_record(payloads, specification.provenance, NumericalProducingProvenance)
    frozen = None if specification.frozen is None else _source_record(payloads, specification.frozen, BridgeProduct)
    roots = experiment.roots_for(selection, specification.tranche)
    configs = binding.configs(design, selection.identity, roots, provenance.identity, None if frozen is None else frozen.fit)
    tasks = {t.task_id:t for t in plan.tasks}
    if set(tasks) != {c.node_id for c in configs} or draft.selected_operation_ids != tuple(c.node_id for c in configs):
        raise PermissionError('SCI02-D read changes the original complete operation census')
    run_id = plan.source_plan.object_id
    if report.get('run_id') != run_id: raise PermissionError('SCI02-D read changes the actual execution identity')
    records, costs, operation_costs = {}, {}, []
    for config in configs:
        receipt = products['receipts'].get(config.node_id)
        if receipt is None or receipt.operational_status is not OperationalStatus.SUCCEEDED: continue
        product = _record(products, tasks, run_id, config.node_id, BridgeProduct)
        if product.config != config: raise PermissionError('SCI02-D changes the producing configuration')
        records[config.node_id] = product
        own_cost = {}
        for key,value in product.measurements:
            if value is not None and key.startswith(('runtime.', 'native.')):
                label = config.phase+'.'+key
                costs[label] = costs.get(label, Decimal(0))+value
                own_cost[key] = str(value)
        if product.native:
            child = product.native[0].completion.cost
            own_cost.update({f'native_child.{k}': None if getattr(child,k) is None else str(getattr(child,k)) for k in ('cpu_seconds','wall_seconds')})
        operation_costs.append({'node': config.node_id, 'phase': config.phase, 'bank': None if len(config.roots) != 1 else config.root.bank,
            'ordinal': None if len(config.roots) != 1 else config.root.ordinal, 'components': own_cost})
    for config in configs:
        product = records.get(config.node_id)
        if product is None: continue
        parents = binding.parents_for(config)
        if any(c.node_id not in records for c in parents.values()): raise PermissionError('SCI02-D completed product lacks original predecessor receipts')
        if product.predecessors != tuple(sorted((records[c.node_id].identity for c in parents.values()), key=lambda p:p.object_id)):
            raise PermissionError('SCI02-D substitutes original sealed predecessor custody')
    pooled_inputs, pooled_arrays, rows = {}, {}, []
    for config in configs:
        if config.phase != 'controls' or config.node_id not in records: continue
        product = records[config.node_id]
        actual = values(artifact_writer, products, tasks, product)
        if reconstruct:
            _check_result(product, actual, science.controls())
        pooled_inputs[config.node_id], pooled_arrays[config.node_id] = product, actual
    for root in roots:
        selected = {c.phase:c for c in configs if c.roots == (root,)}
        if any(c.node_id not in records for c in selected.values()):
            rows.append({'root': root.record_id, 'bank': root.bank, 'ordinal': root.ordinal, 'state': 'UNKNOWN',
                'missing_operations': sum(c.node_id not in records for c in selected.values())})
            continue
        sample, assessed = (records[selected[p].node_id] for p in ('sample','assess'))
        native = _native_custody(artifact_writer, products, tasks, plan, sample.config, provenance, sample)
        actual = values(artifact_writer, products, tasks, assessed)
        if reconstruct:
            raw = values(artifact_writer, products, tasks, sample)
            expected = assessment.assess(assessed.config, raw)
            _check_result(assessed, actual, expected)
            del raw, expected
        pooled_inputs[assessed.config.node_id], pooled_arrays[assessed.config.node_id] = assessed, actual
        rows.append({'root': root.record_id, 'bank': root.bank, 'ordinal': root.ordinal,
            'state': 'ASSESSED' if reconstruct else 'RECORDED',
            'disposition': assessed.disposition, 'reasons': list(assessed.reasons), 'product': assessed.identity.to_document(),
            'measurements': {k:None if v is None else str(v) for k,v in assessed.measurements},
            **{key:actual[key].tolist() for key in ('estimates','prefix_estimates','prefix_half_widths','doubled_block_half_widths',
                'five_node_estimates','kinetic_means','reconstruction_residuals')}})
        if not reconstruct:
            rows[-1]['native_custody'] = {'definition': native.definition.identity.to_document(),
                'completion': native.completion.to_document(), 'receipt': native.receipt.to_document(),
                'parent_receipt': products['receipts'][sample.config.node_id].to_document(),
                'historical_publication_failures': 'NOT_SUPPLIED_BY_COMPLETED_RECEIPTS'}
    pooled, = (c for c in configs if c.phase in ('fit','confirm'))
    result = records.get(pooled.node_id)
    complete = result is not None and len(records) == len(configs) and sum(r['state'] != 'UNKNOWN' for r in rows) == count
    summary = {}
    if complete:
        actual = values(artifact_writer, products, tasks, result)
        if reconstruct and pooled.phase == 'fit':
            expected, fitted = science.fit(pooled, pooled_inputs, pooled_arrays)
            _check_result(result, actual, expected)
            reader.check_fit(pooled, pooled_inputs, pooled_arrays, result, actual)
            if result.fit != fitted: raise PermissionError('SCI02-D read substitutes the frozen exact estimator')
        elif reconstruct:
            _check_result(result, actual, science.confirm(pooled, pooled_inputs, pooled_arrays))
        summary.update(pooled_product=result.identity.to_document(), pooled_disposition=result.disposition, pooled_reasons=list(result.reasons),
            pooled_measurements={k:None if v is None else str(v) for k,v in result.measurements},
            pooled_arrays={k:v.tolist() for k,v in actual.items()})
        if result.fit is not None: summary['frozen_fit'] = result.fit.to_document()
    output = {'scientific_completion': 'COMPLETE_SCI02D_ASSESSMENT' if complete else 'INCOMPLETE_SCI02D_ASSESSMENT',
        'state': 'FROZEN_ESTIMATOR_AVAILABLE' if complete and result.fit is not None else 'FINITE_COHORT_ASSESSED' if complete else 'INCOMPLETE',
        'scope': design.scope, 'tranche': specification.tranche, 'assigned_roots': count, 'root_findings': rows,
        'cost_components': {k:str(v) for k,v in sorted(costs.items())}, 'operation_costs': operation_costs,
        'cost_scope': 'Native child includes sampling; do not sum overlapping windows. Complete CLI costs are external execution observations.',
        'new_native_contact_count': 0, 'original_completed_native_contacts': sum(len(p.native) for p in records.values()),
        'read_cpu_seconds': time.process_time()-cpu, 'read_wall_seconds': time.monotonic()-wall,
        'molecular_requirement': {'status': 'OPEN', 'requirement': 'Actual paired M1 WT/I95M restrained canonical suppliers'},
        'qualification': 'NOT_ESTABLISHED', 'equilibrium_state_coverage': 'NOT_ESTABLISHED', **summary}
    if not reconstruct:
        output.update(scientific_completion='NOT_RECONSTRUCTED_BY_RECORDED_VIEW',
            state='RECORDED_PRODUCTS_COMPLETE' if complete else 'RECORDED_PRODUCTS_INCOMPLETE',
            read_scope='AUTHENTICATED_HISTORICAL_SCI02D_FINDINGS', independent_reconstruction='NOT_PERFORMED',
            design=design.to_document(), selection=selection.identity.to_document())
    return output
